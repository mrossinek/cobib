"""coBib's terminal user interface.

This class implements a beautiful TUI for coBib, leveraging
[`textual`](https://github.com/textualize/textual).

.. warning::

   This module makes no API stability guarantees! With it being based on
   [`textual`](https://textual.textualize.io/) which is still in very early stages of its
   development, breaking API changes in this module might be released as part of coBib's feature
   releases. You have been warned.
"""

from __future__ import annotations

import asyncio
import io
import logging
import shlex
import sys
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from typing import Any, Iterator

from rich.console import RenderableType
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.coordinate import Coordinate
from textual.css.query import NoMatches
from textual.widget import AwaitMount, Widget
from textual.widgets import DataTable, Footer, Header, Tree
from typing_extensions import override

from cobib import commands
from cobib.ui.components import (
    EntryView,
    HelpPopup,
    Input,
    MainView,
    Popup,
    PopupLoggingHandler,
    PopupPanel,
    Progress,
    Prompt,
    SelectionFilter,
)
from cobib.ui.ui import UI
from cobib.utils.file_downloader import FileDownloader


# NOTE: pylint and mypy are unable to understand that the `App` interface actually implements `run`
# pylint: disable=abstract-method
class TUI(UI, App[None]):  # type: ignore[misc]
    """The TUI class.

    This class does not support any extra command-line arguments compared to the base class.
    However, it also extends the `textual.app.App` interface. It can be used with the debugging
    tools of textual but starting it requires a little bit of care because it depends on some setup
    being done during `cobib.ui.cli.CLI.run` (which is the method from which the TUI gets started
    during normal operation).

    In short, here is how you can start the TUI using textual:
    ```
    textual run "src/cobib/__main__.py"
    ```
    This assumes that you are at the root of the cobib development folder. You can include
    additional command-line arguments within the quotes as you desire.

    Adding the `--dev` argument to `textual run` will connect it to the debugging console which you
    can start in a separate shell via `textual console`.
    """

    DEFAULT_CSS = """
    Screen {
        layers: default popup overlay;
        align-vertical: bottom;
    }
    """

    # TODO: extract key bindings to widgets where appropriate
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("question_mark", "toggle_help", "Help"),
        ("underscore", "toggle_layout", "Layout"),
        ("space", "toggle_fold", "Fold"),
        ("colon", "prompt(':')", "Prompt"),
        ("v", "select", "Select"),
        ("slash", "prompt('/')", "Search"),
        ("a", "prompt('add ')", "Add"),
        ("d", "delete", "Delete"),
        ("e", "edit", "Edit"),
        ("f", "filter", "Filter"),
        ("i", "prompt('import ')", "Import"),
        ("m", "prompt('modify ', False, True)", "Modify"),
        ("o", "open", "Open"),
        ("r", "prompt('redo', True)", "Redo"),
        ("s", "sort", "Sort"),
        ("u", "prompt('undo', True)", "Undo"),
        ("x", "prompt('export ', False, True)", "Export"),
        Binding("j", "arrow_key('down')", "Down", show=False),
        Binding("k", "arrow_key('up')", "Up", show=False),
        Binding("h", "arrow_key('left')", "Left", show=False),
        Binding("l", "arrow_key('right')", "Right", show=False),
        Binding("down", "arrow_key('down')", "Down", show=False),
        Binding("up", "arrow_key('up')", "Up", show=False),
        Binding("left", "arrow_key('left')", "Left", show=False),
        Binding("right", "arrow_key('right')", "Right", show=False),
    ]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initializes the TUI.

        Args:
            *args: any positional arguments for textual's underlying `App` class.
            **kwargs: any keyword arguments for textual's underlying `App` class.
        """
        super().__init__(*args, **kwargs)
        self.title = "coBib"
        self.sub_title = "The Console Bibliography Manager"
        self._list_args = ["-r"]
        self._filter: SelectionFilter = SelectionFilter()
        self._background_tasks: set[asyncio.Task] = set()  # type: ignore[type-arg]
        PopupLoggingHandler(self, level=logging.INFO)
        Progress.console = self
        FileDownloader.progress = Progress

    @override
    def compose(self) -> ComposeResult:
        yield HelpPopup(classes="-hidden")

        main = MainView()
        yield main

        entry = EntryView()
        yield entry

        yield PopupPanel()

        yield Header()
        yield Footer()

        command = commands.ListCommand(*self._list_args)
        command.execute()
        table = command.render_textual()
        main.mount(table)

    # TODO: remove once https://github.com/Textualize/textual/pull/1541 is merged into Textual
    @contextmanager
    def suspend(self) -> Iterator[None]:
        """Temporarily suspends the application.

        .. warning::

           This method will be removed once support for this has been merged directly into textual.
           Refer to [this pull request](https://github.com/Textualize/textual/pull/1541) for more
           details.
        """
        driver = self._driver
        if driver is not None:
            driver.stop_application_mode()
            with redirect_stdout(sys.__stdout__), redirect_stderr(sys.__stderr__):
                yield
            driver.start_application_mode()

    def print(self, renderable: RenderableType | Widget) -> tuple[Widget, AwaitMount]:
        """A utility method for "printing" to the screen.

        Args:
            renderable: the object to be printed. If this is a `Widget`, it will be mounted in the
                `PopupPanel` as is. Otherwise, the renderable object will be wrapped in a `Popup`
                before mounting without any styling or timer applied.

        Returns:
            The pair of the widget mounted to the `PopupPanel` and the awaitable of its `mount`
            action.
        """
        if isinstance(renderable, Widget):
            popup = renderable
        else:
            popup = Popup(renderable, level=0, timer=None)

        await_mount = self.query_one(PopupPanel).mount(popup)

        return popup, await_mount

    # Event reaction methods

    def on_mount(self) -> None:
        """Triggers on the [`Mount`][1] event.

        This method takes care of initializing the desired layout and seeds the `EntryView` widget.

        [1]: https://textual.textualize.io/api/events/#textual.events.Mount
        """
        self.screen.styles.layout = "horizontal"
        self._show_entry()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Triggers on the `cobib.ui.components.input.Input.Submitted` event.

        This method parses the input value and extracts the command to be triggered as well as all
        its arguments.

        Args:
            event: the triggering event.
        """
        event.input.remove()
        if event.value[0] == "/":
            event.value = "search " + event.value[1:]
        elif event.value[0] == ":":
            event.value = event.value[1:]

        command = shlex.split(event.value)

        if self._filter.active:
            command += ["--"]
            command.extend(list(self._filter.selection))
            self._filter.active = False

        if command and command[0]:
            if command[0].lower() == "list":
                self._list_args = command[1:]
                self._update_table()
            elif command[0].lower() == "search":
                main = self.query_one(MainView)
                main.clear()
                subcmd = commands.SearchCommand(*command[1:])
                subcmd.execute()
                tree = subcmd.render_textual()
                main.mount(tree)
                self.refresh(layout=True)
            else:
                with redirect_stdout(io.StringIO()) as stdout:
                    with redirect_stderr(io.StringIO()) as stderr:
                        try:
                            subcmd = getattr(commands, command[0].title() + "Command")(
                                *command[1:], prompt=Prompt, console=self
                            )

                            task = asyncio.create_task(  # type: ignore[var-annotated]
                                subcmd.execute()  # type: ignore[arg-type]
                            )
                            self._background_tasks.add(task)
                            task.add_done_callback(self._background_tasks.discard)
                            task.add_done_callback(lambda _: self._update_table)
                        except SystemExit:
                            pass
                stdout_val = stdout.getvalue().strip()
                if stdout_val:
                    self.print(Popup(stdout_val, level=logging.INFO))
                stderr_val = stderr.getvalue().strip()
                if stderr_val:
                    self.print(Popup(stderr_val, level=logging.CRITICAL))
                self._update_table()

    # Action methods

    def action_arrow_key(self, key_name: str) -> None:
        """The movement action.

        This method currently redirects to the widget mounted in the `MainView`.
        The movement keys `h`, `j`, `k`, and `l` also redirect here.

        .. warning::

           This method is pending a refactoring during which the layouting will be redesigned in
           favor of screens. Once that happens, the movement key bindings will be handled by the
           widgets directly.

           For more information refer to [this issue](https://gitlab.com/cobib/cobib/-/issues/111).

        Args:
            key_name: the name of the key triggering this action.
        """
        # TODO: handle scroll offset
        main = self.query_one(MainView).children[0]
        cursor_func = getattr(main, f"action_cursor_{key_name}", None)
        if cursor_func is None:
            return
        cursor_func()
        self._show_entry()

    def action_toggle_layout(self) -> None:
        """The layout toggling action.

        This action will toggle between a horizontal and vertical layout.
        """
        # TODO: refactor how layout is done
        layout = self.screen.styles.layout
        if layout is None:
            return
        if layout.name.lower().startswith("horizontal"):
            self.screen.styles.layout = "vertical"
            main = self.query_one(MainView)
            main.styles.height = "2fr"
            main.styles.width = "1fr"
            entry = self.query_one(EntryView)
            entry.styles.height = "1fr"
            entry.styles.width = "1fr"
        elif layout.name.lower().startswith("vertical"):
            self.screen.styles.layout = "horizontal"
            main = self.query_one(MainView)
            main.styles.width = "2fr"
            main.styles.height = "1fr"
            entry = self.query_one(EntryView)
            entry.styles.width = "1fr"
            entry.styles.height = "1fr"
        self.refresh(layout=True)

    async def action_prompt(
        self, value: str, submit: bool = False, check_selection: bool = False
    ) -> None:
        """The prompt action.

        This action triggers an interactive user input via which an arbitrary coBib command can be
        executed as if it were run via the CLI.

        All commands which do not have an explicit action associated with them will go through this
        prompt action.

        Args:
            value: the string with which to pre-populate the input field.
            submit: if set, the user will not be prompted and the input will be submitted
                immediately (i.e. `value` gets parsed directly).
            check_selection: whether or not to check for a visual selection.
        """
        if check_selection and self._filter.selection:
            self._filter.active = True
            value += "-s "

        prompt = Input(value=value)
        prompt.styles.layer = "overlay"
        prompt.styles.dock = "bottom"  # type: ignore[arg-type]
        prompt.styles.border = (None, None)
        prompt.styles.padding = (0, 0)

        await self.mount(prompt)
        if submit:
            await prompt.action_submit()
        else:
            prompt.focus()

    def action_toggle_help(self) -> None:
        """The help action.

        This action toggles a help popup. Once opened, the same keybind needs to be pressed to close
        it.
        """
        help_sidebar = self.query_one(HelpPopup)
        self.set_focus(None)
        if help_sidebar.has_class("-hidden"):
            help_sidebar.remove_class("-hidden")
        else:
            help_sidebar.add_class("-hidden")

    async def action_select(self) -> None:
        """The selection action.

        This action adds the entry currently under the cursor to the visual selection.
        """
        self._select_entry()

    def action_toggle_fold(self) -> None:
        """The folding action.

        This action toggles the display of a node in the results tree of the
        `cobib.commands.search.SearchCommand.render_textual`.

        .. warning::

           This method is pending a refactoring during which the layouting will be redesigned in
           favor of screens. Once that happens, this action will be moved to the widget returned by
            `cobib.commands.search.SearchCommand.render_textual`.

           For more information refer to [this issue](https://gitlab.com/cobib/cobib/-/issues/111).
        """
        # TODO: provide more ways to fold (e.g. recursively)
        try:
            main = self.query_one(MainView).query_one(Tree)
            main.action_toggle_node()
        except NoMatches:
            pass

    async def action_delete(self) -> None:
        """The delete action.

        This action triggers the `cobib.commands.delete.DeleteCommand`.
        """
        labels: list[str]
        if self._filter.selection:
            labels = list(self._filter.selection)
            self._filter.selection.clear()
        else:
            labels = [self._get_current_label()]

        commands.DeleteCommand(*labels).execute()
        self._update_table()

    async def action_edit(self) -> None:
        """The edit action.

        This action triggers the `cobib.commands.edit.EditCommand`.
        """
        self._edit_entry()

    async def action_open(self) -> None:
        """The open action.

        This action triggers the `cobib.commands.open.OpenCommand`.
        """
        labels: list[str]
        if self._filter.selection:
            labels = list(self._filter.selection)
            self._filter.selection.clear()
        else:
            labels = [self._get_current_label()]

        open_cmd = commands.OpenCommand(*labels, prompt=Prompt, console=self)
        task = asyncio.create_task(open_cmd.execute())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

    async def action_filter(self) -> None:
        """The filter action.

        This action triggers the `cobib.commands.list.ListCommand` via the `action_prompt` and
        allows the user to provide additional filters.
        """
        await self.action_prompt("list " + " ".join(self._list_args) + " ")

    async def action_sort(self) -> None:
        """The sort action.

        This action triggers the `cobib.commands.list.ListCommand` via the `action_prompt` and
        allows the user to provide a field to be sorted by. This command is handled specially
        because it ensures that only a single sort argument can be given at a time.
        """
        try:
            # first, remove any previously used sort argument
            sort_arg_idx = self._list_args.index("-s")
            self._list_args.pop(sort_arg_idx)
        except ValueError:
            pass

        # add the sort option to the arguments
        self._list_args += ["-s"]

        await self.action_prompt("list " + " ".join(self._list_args) + " ")

    # Utility methods

    def _edit_entry(self) -> None:
        """Edits the current entry.

        This method takes care of suspending the application in favor of the editor.
        """
        label = self._get_current_label()
        with self.suspend():
            commands.EditCommand(label).execute()
        self.refresh(layout=True)

    def _get_current_label(self) -> str:
        """Gets the label of the entry currently under the cursor.

        .. warning::

           This method is pending a refactoring during which the layouting will be redesigned in
           favor of screens. Once that happens, the responsibility of detecting the current label
           will be delegated to the widget subclasses to be mounted on the respective screens.

           For more information refer to [this issue](https://gitlab.com/cobib/cobib/-/issues/111).

        Returns:
            The label of the entry currently under the cursor.
        """
        label: str
        try:
            table = self.query_one(MainView).query_one(DataTable)
            label = table.get_cell_at(Coordinate(table.cursor_row, 0)).plain
        except NoMatches:
            try:
                tree = self.query_one(MainView).query_one(Tree)
                previous_node, current_node = tree.cursor_node, tree.cursor_node
                if current_node is None:
                    raise NoMatches  # pylint: disable=raise-missing-from
                while current_node.parent is not None:
                    previous_node, current_node = current_node, current_node.parent
                if previous_node is None:
                    raise NoMatches  # pylint: disable=raise-missing-from
                label = str(previous_node.label).split(" - ", maxsplit=1)[0]
            except NoMatches as exc:
                raise NoMatches from exc
        return label

    def _select_entry(self) -> None:
        """Adds the entry currently under the cursor to the visual selection."""
        try:
            table = self.query_one(MainView).query_one(DataTable)
            label = table.get_cell_at(Coordinate(table.cursor_row, 0)).plain
            if label in self._filter.selection:
                self._filter.selection.remove(label)
            else:
                self._filter.selection.add(label)
            table.notify_style_update()
            table.refresh()
            self.query_one(EntryView).refresh()

        except NoMatches:
            try:
                tree = self.query_one(MainView).query_one(Tree)
                previous_node, current_node = tree.cursor_node, tree.cursor_node
                if current_node is None:
                    raise NoMatches  # pylint: disable=raise-missing-from
                while current_node.parent is not None:
                    previous_node, current_node = current_node, current_node.parent
                if previous_node is None:
                    raise NoMatches  # pylint: disable=raise-missing-from

                label = str(previous_node.label).split(" - ", maxsplit=1)[0]

                if label in self._filter.selection:
                    self._filter.selection.remove(label)
                else:
                    self._filter.selection.add(label)

                tree.notify_style_update()
                tree.refresh()
                self.query_one(EntryView).refresh()

            except NoMatches as exc:
                raise NoMatches from exc

    def _show_entry(self) -> None:
        """Renders the entry currently under the cursor in the `EntryView` widget."""
        label = self._get_current_label()
        show_cmd = commands.ShowCommand(label)
        show_cmd.execute()
        entry = self.query_one(EntryView)
        entry.string = show_cmd.render_rich(
            background_color=entry.background_colors[1].rich_color.name,
        )

    def _update_table(self) -> None:
        """Updates the list of entries displayed in the `MainView`."""
        # TODO: retain scroll position
        main = self.query_one(MainView)
        main.clear()
        command = commands.ListCommand(*self._list_args)
        command.execute()
        table = command.render_textual()
        main.mount(table)
        main.focus()
        self.refresh(layout=True)
