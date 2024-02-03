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
from collections.abc import Awaitable, Callable, Coroutine
from contextlib import redirect_stderr, redirect_stdout
from inspect import iscoroutinefunction
from typing import Any, ClassVar, cast

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.keys import Keys
from textual.logging import TextualHandler
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, Static
from typing_extensions import override

from cobib import commands
from cobib.config import config
from cobib.database import Database
from cobib.ui.components import (
    EntryView,
    HelpScreen,
    InputScreen,
    ListView,
    LoggingHandler,
    LogScreen,
    MainContent,
    MotionKey,
    PresetFilterScreen,
    SearchView,
    SelectionFilter,
)
from cobib.ui.ui import UI
from cobib.utils.prompt import Confirm

LOGGER = logging.getLogger(__name__)


# NOTE: pylint and mypy are unable to understand that the `App` interface actually implements `run`


class TUI(UI, App[None]):  # type: ignore[misc]
    """The TUI class.

    This class does not support any extra command-line arguments compared to the base class.
    However, it also extends the `textual.app.App` interface. It can be used with the debugging
    tools of textual but starting it requires you to use the `-c` (a.k.a. `--command`) argument of
    `textual run` since `cobib` is installed as a command-line script.

    In short, here is how you can start the TUI using textual:
    ```
    textual run -c cobib
    ```
    This assumes that you are at the root of the cobib development folder. You can include
    additional command-line arguments after `cobib`, but when doing so you will need to put the
    entire command in quotes, like this:
    ```
    textual run -c "cobib -v"
    ```

    Adding the `--dev` argument to `textual run` will connect it to the debugging console which you
    can start in a separate shell via `textual console`.

    For more information on how to debug a textual app, please refer to
    [their documentation](https://textual.textualize.io/guide/devtools/).
    """

    DEFAULT_CSS = """
        Screen {
            layers: default;
            align-vertical: bottom;
        }
    """

    _PRESET_FILTER_BINDINGS: ClassVar[list[tuple[str, str, str]]] = [
        (f"{i}", f"preset_filter({i})", f"Preset #{i}") for i in range(10)
    ]
    BINDINGS: ClassVar[list[Binding | tuple[str, str] | tuple[str, str, str]]] = [
        ("q", "quit", "Quit"),
        ("question_mark", "push_screen('help')", "Help"),
        ("underscore", "toggle_layout", "Layout"),
        ("colon", "prompt(':')", "Prompt"),
        ("v", "select", "Select"),
        ("slash", "prompt('/')", "Search"),
        ("a", "prompt('add ')", "Add"),
        ("c", "prompt('review ', False, True)", "Review"),
        ("d", "delete", "Delete"),
        ("e", "edit", "Edit"),
        ("f", "filter", "Filter"),
        ("i", "prompt('import ')", "Import"),
        ("m", "prompt('modify ', False, True)", "Modify"),
        ("o", "open", "Open"),
        ("p", "preset_filter()", "Preset"),
        ("r", "prompt('redo', True)", "Redo"),
        ("s", "sort", "Sort"),
        ("u", "prompt('undo', True)", "Undo"),
        ("x", "prompt('export ', False, True)", "Export"),
        ("z", "push_screen('log')", "Log"),
        *_PRESET_FILTER_BINDINGS,
    ]
    """
    | Key(s) | Description |
    | :- | :- |
    | q | Quit's coBib. |
    | ? | Toggles the help screen. |
    | _ | Toggles between the horizontal and vertical layout. |
    | : | Starts the prompt for an arbitrary coBib command. |
    | v | Selects the current entry. |
    | / | Searches the database for the provided string. |
    | digit | Immediately selects the preset filter given by that digit (0 = reset). |
    | a | Prompts for a new entry to be added to the database. |
    | d | Deletes the current (or selected) entries. |
    | e | Edits the current entry. |
    | f | Allows filtering the table using `++/--` keywords. |
    | i | Imports entries from another source. |
    | m | Prompts for a modification (respects selection). |
    | o | Opens the current (or selected) entries. |
    | p | Allows selecting a preset filter (see `config.tui.preset_filters`). |
    | r | Redoes the last undone change. Requires git-tracking! |
    | s | Prompts for the field to sort by (use -r to list in reverse). |
    | u | Undes the last change. Requires git-tracking! |
    | x | Exports the current (or selected) entries. |
    | z | Toggles the log screen. |
    """

    SCREENS: ClassVar[dict[str, Screen[Any] | Callable[[], Screen[Any]]]] = {
        "help": HelpScreen,
        "log": LogScreen,
        "input": InputScreen,
        "preset_filter": PresetFilterScreen,
    }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initializes the TUI.

        Args:
            *args: any positional arguments for textual's underlying `App` class.
            **kwargs: any keyword arguments for textual's underlying `App` class.
        """
        super().__init__(*args, **kwargs)
        self.console.push_theme(config.theme.build())
        self.root_logger.addHandler(TextualHandler())
        self.title = "coBib"
        self.sub_title = "The Console Bibliography Manager"
        self._list_args = ["-r"]
        self._filter: SelectionFilter = SelectionFilter()
        self._filters.append(self._filter)
        self._background_tasks: set[asyncio.Task] = set()  # type: ignore[type-arg]
        LoggingHandler(self, level=logging.INFO)

    @override
    def compose(self) -> ComposeResult:
        with MainContent(initial=ListView.id):
            yield ListView()
            yield SearchView(".")

        yield EntryView()

        yield Header()
        yield Footer()

    # Event reaction methods

    def on_motion_key(self, event: MotionKey) -> None:
        """Triggers on the custom `cobib.ui.components.motion_key.MotionKey` event.

        This function will update the entry shown in the `cobib.ui.components.entry_view.EntryView`
        widget. It only triggers on vertical motion keys.

        Args:
            event: the motion event.
        """
        if event.key in {Keys.Down, Keys.Up, Keys.PageDown, Keys.PageUp, Keys.Home, Keys.End}:
            self._show_entry()

    async def on_mount(self) -> None:
        """Triggers on the [`Mount`][1] event.

        This method takes care of initializing the desired layout and seeds the `EntryView` widget.

        [1]: https://textual.textualize.io/api/events/#textual.events.Mount
        """
        self.screen.styles.layout = "horizontal"
        await self._update_table()
        self._show_entry()

    # Action methods

    async def action_quit(self) -> None:
        """Action to display the quit dialog."""

        async def _prompt_quit() -> None:
            res = await Confirm.ask("Are you sure you want to quit?", default=True)
            if res:
                self.exit()

        task = asyncio.create_task(_prompt_quit())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

    def action_toggle_layout(self) -> None:
        """The layout toggling action.

        This action will toggle between a horizontal and vertical layout.
        """
        layout = self.screen.styles.layout
        if layout is None:
            return
        main = self.query_one(MainContent)
        if layout.name.lower().startswith("horizontal"):
            self.screen.styles.layout = "vertical"
            main.styles.height = "2fr"
            main.styles.width = "1fr"
        elif layout.name.lower().startswith("vertical"):
            self.screen.styles.layout = "horizontal"
            main.styles.width = "2fr"
            main.styles.height = "1fr"
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

        if submit:
            await self._process_input(value)
        else:
            await_mount = self.push_screen("input", self._process_input)
            inp_screen = cast(InputScreen, self.get_screen("input"))
            await await_mount
            inp = inp_screen.query_one(Input)
            inp.value = value
            inp.action_end()

    async def action_select(self) -> None:
        """The selection action.

        This action adds the entry currently under the cursor to the visual selection.
        """
        main = self.query_one(MainContent)
        label = main.get_current_label()

        if label in self._filter.selection:
            self._filter.selection.remove(label)
        else:
            self._filter.selection.add(label)

        main.notify_style_update()
        main.refresh()
        self.query_one(EntryView).query_one(Static).refresh()

    def action_delete(self) -> None:
        """The delete action.

        This action triggers the `cobib.commands.delete.DeleteCommand`.
        """
        main = self.query_one(MainContent)
        labels: list[str]
        if self._filter.selection:
            labels = list(self._filter.selection)
            self._filter.selection.clear()
        else:
            labels = [main.get_current_label()]

        self._run_command(["delete", *labels])

    async def action_edit(self) -> None:
        """The edit action.

        This action triggers the `cobib.commands.edit.EditCommand`.
        """
        self._edit_entry()
        await self._update_table()

    def action_open(self) -> None:
        """The open action.

        This action triggers the `cobib.commands.open.OpenCommand`.
        """
        main = self.query_one(MainContent)
        labels: list[str]
        if self._filter.selection:
            labels = list(self._filter.selection)
            self._filter.selection.clear()
        else:
            labels = [main.get_current_label()]

        self._run_command(["open", *labels])

    async def action_preset_filter(self, idx: int | None = None) -> None:
        """The preset filter selection action.

        This action selects (or prompts for) a preset filter from `config.tui.preset_filters`.

        Args:
            idx: the index of which preset filter to select. When this is `None`, the user will be
                prompted interactively. When `0`, all filters will be reset.
        """
        if idx is None:
            await_mount = self.push_screen("preset_filter", self._process_input)
            await await_mount
        else:
            idx = int(idx)
            if idx == 0:
                await self._process_input("list -r")
            elif idx <= len(config.tui.preset_filters):
                await self._process_input(f"list {config.tui.preset_filters[idx-1]}")

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
            # NOTE: we need to pop twice in order to remove both: the `-s` option and the key which
            # was sorted by
            self._list_args.pop(sort_arg_idx)
            self._list_args.pop(sort_arg_idx)
        except ValueError:
            pass

        # add the sort option to the arguments
        self._list_args += ["-s"]

        await self.action_prompt("list " + " ".join(self._list_args) + " ")

    # Utility methods

    def _edit_entry(self) -> None:
        """Edits the current entry.

        Suspension of the App is handled directly by the edit command using
        `cobib.utils.context.get_active_app`.
        """
        main = self.query_one(MainContent)
        label = main.get_current_label()
        commands.EditCommand(label).execute()

    def _show_entry(self, command: commands.ShowCommand | None = None) -> None:
        """Renders the entry currently under the cursor in the `EntryView` widget.

        Args:
            command: the `cobib.commands.show.ShowCommand` to execute. If this is `None`, a new
                instance will be constructed to show the entry at the current cursor location.
        """
        if command is None:
            main = self.query_one(MainContent)
            label = main.get_current_label()
            command = commands.ShowCommand(label)
        command.execute()
        entry = self.query_one(EntryView)
        static = entry.query_one(Static)
        static.update(
            command.render_rich(
                background_color=entry.background_colors[1].rich_color.name,
            )
        )

    def _jump_to_entry(self, command: list[str]) -> None:
        """Jumps the cursor in the current view to the entry provided by the command arguments.

        Args:
            command: the list of command arguments to be passed to the
                `cobib.commands.show.ShowCommand`.
        """
        show_cmd = commands.ShowCommand(*command)
        label = show_cmd.largs.label
        main = self.query_one(MainContent)
        try:
            main.jump_to_label(label)
        except KeyError:
            if label in Database():
                msg = (
                    f"The entry with label '{label}' exists in the database but not in the current "
                    "view. Displaying it only in the side panel."
                )
                LOGGER.info(msg)
        self._show_entry(show_cmd)

    async def _update_table(self) -> None:
        """Updates the list of entries displayed in the `MainContent`."""
        main = self.screen_stack[0].query_one(MainContent)
        old_table = main.query_one(ListView)
        command = commands.ListCommand(*self._list_args)
        command.execute()
        table = command.render_textual()
        await main.replace_widget(table)
        table.focus()
        if old_table is not None:
            table.cursor_coordinate = old_table.cursor_coordinate
            table.scroll_x = old_table.scroll_x
            table.scroll_y = old_table.scroll_y
            del old_table
        self.refresh(layout=True)

    async def _update_tree(self, command: list[str]) -> None:
        """Updates the tree of search results displayed in the `MainContent`.

        Args:
            command: the list of command arguments to be passed to the
                `cobib.commands.search.SearchCommand`.
        """
        subcmd = commands.SearchCommand(*command)
        await subcmd.execute()
        tree = subcmd.render_textual()
        main = self.query_one(MainContent)
        await main.replace_widget(tree)
        tree.focus()
        self.refresh(layout=True)

    async def _process_input(self, value: str) -> None:
        """Processes the input returned from the `cobib.ui.components.input_screen.InputScreen`.

        Args:
            value: the value put into the `Input` widget by the user.
        """
        if not value:
            return

        if value[0] == "/":
            value = "search " + value[1:]
        elif value[0] == ":":
            value = value[1:]

        command = shlex.split(value)

        if self._filter.active:
            command += ["--"]
            command.extend(list(self._filter.selection))
            self._filter.active = False

        if command and command[0]:
            if command[0].lower() == "init":
                LOGGER.error(
                    "You cannot run the 'init' command from within the TUI!\n"
                    "Please run this command outside the TUI."
                )
                return
            if command[0].lower() == "git":
                LOGGER.error(
                    "You cannot run the 'git' command from within the TUI because it is impossible "
                    "to foresee what the command might output or need for input etc.\n"
                    "Please run this command outside the TUI."
                )
                return
            if command[0].lower() == "show":
                self._jump_to_entry(command[1:])
            if command[0].lower() == "list":
                self._list_args = command[1:]
                await self._update_table()
            elif command[0].lower() == "search":
                await self._update_tree(command[1:])
            elif command[0].lower() == "edit":
                with self.suspend():
                    commands.EditCommand(*command[1:]).execute()
            else:
                self._run_command(command)

    @staticmethod
    async def _async_done_callback(
        task: Awaitable[None], async_callback: Callable[[], Coroutine[Any, Any, None]]
    ) -> None:
        """Adds an asynchronous callback for when the provided task is done.

        Args:
            task: the Task to await before running the next coroutine.
            async_callback: the asynchronous callback to run after the `task` has completed.
        """
        await task
        await async_callback()

    def _run_command(self, command: list[str]) -> None:
        """Parses and executes a cobib command with its arguments.

        This method also redirects `stdout` and `stderr` and captures their contents to be displayed
        as popups in the TUI.

        Args:
            command: a list of strings consisting of the command keyword and its arguments.
        """
        with redirect_stdout(io.StringIO()) as stdout:
            with redirect_stderr(io.StringIO()) as stderr:
                try:
                    subcmd = getattr(commands, command[0].title() + "Command")(*command[1:])

                    if not iscoroutinefunction(subcmd.execute):
                        subcmd.execute()
                    else:
                        # FIXME: in these cases, stdout and stderr cannot be captured

                        # 1. create subcommand execution task
                        task1 = asyncio.create_task(subcmd.execute())

                        # 2. create another task which chains an asynchronous callback after the
                        #    previous one
                        task2 = asyncio.create_task(
                            TUI._async_done_callback(task1, self._update_table)
                        )

                        # 3. ensure proper clean-up of all created tasks
                        self._background_tasks.add(task1)
                        task1.add_done_callback(self._background_tasks.discard)
                        self._background_tasks.add(task2)
                        task2.add_done_callback(self._background_tasks.discard)

                except SystemExit:
                    pass

        stdout_val = stdout.getvalue().strip()
        if stdout_val:
            self.notify(stdout_val, title="Output", severity="information", timeout=5)

        stderr_val = stderr.getvalue().strip()
        if stderr_val:
            self.notify(stderr_val, title="Error", severity="error", timeout=10)
