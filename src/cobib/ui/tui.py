"""TODO."""

from __future__ import annotations

import asyncio
import io
import logging
import shlex
import sys
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from typing import Any, Iterator, TextIO, cast

from rich.console import RenderableType
from rich.prompt import InvalidResponse, PromptBase
from rich.segment import Segment
from rich.style import Style
from rich.table import Table
from rich.text import Text, TextType
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.color import Color
from textual.containers import Container
from textual.coordinate import Coordinate
from textual.css.query import NoMatches
from textual.filter import LineFilter
from textual.reactive import reactive
from textual.widget import AwaitMount, Widget
from textual.widgets import DataTable, Footer, Header
from textual.widgets import Input as _Input
from textual.widgets import Label, ProgressBar, Static, Tree

from cobib import commands
from cobib.ui.ui import UI
from cobib.utils.file_downloader import FileDownloader


class Input(_Input):
    """TODO."""

    BINDINGS = [("escape", "escape", "Quit the prompt")]

    async def action_escape(self) -> None:
        """TODO."""
        if self.parent is not None:
            self.parent.refresh(layout=True)
        await self.remove()


class PromptInput(Input):
    """TODO."""

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """TODO."""
        event.input.remove()
        event.stop()


# TODO:
class EntryView(Widget, can_focus=False):
    """TODO."""

    DEFAULT_CSS = """
        EntryView {
            width: 1fr;
        }
    """

    # TODO: fix my type!
    string: reactive[RenderableType] = reactive("")

    def render(self) -> RenderableType:
        """TODO."""
        return self.string


class SelectionFilter(LineFilter):
    """TODO."""

    def __init__(self) -> None:
        """TODO."""
        self.active: bool = False
        self.selection: set[str] = set()
        self.selection_style = Style(color="white", bgcolor="magenta")

    def apply(self, segments: list[Segment], background: Color | None = None) -> list[Segment]:
        # pylint: disable=unused-argument
        """TODO."""
        return [
            Segment(
                text,
                self.selection_style
                if any(sel == text.strip() for sel in self.selection)
                else style,
                None,
            )
            for text, style, _ in segments
        ]


# TODO: make custom DataTable and Tree widget subclasses for ListCommand and SearchCommand
# respectively. This will allow handling bindings on a per-widget basis
class MainView(Container):
    """TODO."""

    DEFAULT_CSS = """
        MainView {
            width: 2fr;
        }
    """

    def clear(self) -> None:
        """TODO."""
        self.query("Widget").remove()


class HelpSidebar(Container, can_focus=False):
    """TODO."""

    DEFAULT_CSS = """
        HelpSidebar {
            layer: overlay;
            background: blue 25%;
            height: auto;
            width: 100%;
        }

        HelpSidebar.-hidden {
            offset-y: 100%;
        }
    """

    def compose(self) -> ComposeResult:
        """TODO."""
        help_table = Table(title="coBib TUI Help")
        help_table.add_column("Key")
        help_table.add_column("Description")
        if self.parent is None:
            raise KeyError
        app = cast(App[None], self.parent.parent)
        for _, binding in app.namespace_bindings.values():
            if not binding.show:
                continue
            help_table.add_row(app.get_key_display(binding.key), binding.description)
        static = Static(help_table)
        static.styles.content_align = ("center", "middle")
        yield static


class PopupPanel(Container, can_focus=False):
    """TODO."""

    DEFAULT_CSS = """
        PopupPanel {
            layer: popup;
            layout: vertical;
            align: center bottom;
            width: 100%;
            height: auto;
            offset-y: -1;
        }
    """


class Popup(Label, can_focus=False):
    """TODO."""

    DEFAULT_CSS = """
        Popup {
            text-style: bold;
            min-height: 1;
            width: 100%;
            color: auto;
        }
    """

    def __init__(
        self,
        renderable: RenderableType,
        *args: Any,
        level: int = logging.INFO,
        timer: float | None = 5.0,
        **kwargs: Any,
    ) -> None:
        """TODO."""
        super().__init__(renderable, *args, **kwargs)
        if level >= logging.CRITICAL:
            self.styles.background = "red"
            self.styles.color = "yellow"
        elif level >= logging.ERROR:
            self.styles.background = "red"
        elif level >= logging.WARNING:
            self.styles.background = "yellow"
        elif level >= logging.INFO:
            self.styles.background = "green"
        elif level >= logging.DEBUG:
            self.styles.background = "blue"
        if timer is not None:
            self.set_timer(timer, self.remove)


class PopupLoggingHandler(logging.Handler):
    """TODO."""

    def __init__(self, app: TUI, level: int = logging.INFO) -> None:
        """TODO."""
        super().__init__(level=level)
        self.app = app

        formatter = logging.Formatter(fmt="[%(levelname)s] %(message)s")
        self.setFormatter(formatter)

        for handler in self.app.root_logger.handlers[:]:
            if isinstance(handler, logging.StreamHandler):
                self.app.root_logger.removeHandler(handler)
                handler.close()

        self.app.root_logger.addHandler(self)

    def emit(self, record: logging.LogRecord) -> None:
        """TODO."""
        self.app.print(Popup(self.format(record), level=record.levelno))


class Progress(ProgressBar):
    """TODO."""

    console: TUI

    # TODO: add proper styling and figure out why this does not refresh properly


class TextualPrompt(PromptBase[str]):
    """TODO."""

    console: TUI  # type: ignore[assignment]

    help_popup: Popup | None = None

    async def __call__(  # type: ignore[override]
        self, *, default: Any = ..., stream: TextIO | None = None
    ) -> str:
        # pylint: disable=invalid-overridden-method
        """TODO."""
        popup: Popup
        reply: str
        while True:
            self.pre_prompt()
            prompt = self.make_prompt(default)
            prompt.rstrip()
            popup = Popup(prompt + "\n", level=0, timer=None)
            self.console.print(popup)
            value = await self.get_input(self.console, prompt, self.password, stream=stream)
            await popup.remove()
            if value == "" and default != ...:
                reply = str(default)
                break
            try:
                return_value = self.process_response(value)
            except InvalidResponse as error:
                self.on_validate_error(value, error)
                continue
            else:
                reply = return_value
                break
        if self.help_popup is not None:
            self.help_popup.remove()
        return reply

    @classmethod
    async def get_input(  # type: ignore[override]
        cls, console: App[None], prompt: TextType, password: bool, stream: TextIO | None = None
    ) -> str:
        # pylint: disable=invalid-overridden-method
        """TODO."""
        inp = PromptInput()
        inp.styles.layer = "overlay"
        inp.styles.dock = "bottom"  # type: ignore[arg-type]
        inp.styles.border = (None, None)
        inp.styles.padding = (0, 0)
        await console.mount(inp)

        inp.focus()

        while console.is_mounted(inp):
            await asyncio.sleep(0)

        return str(inp.value)

    def on_validate_error(self, value: str, error: InvalidResponse) -> None:
        """TODO."""
        if value == "help":
            if self.help_popup is not None:
                self.help_popup.remove()
            if isinstance(error.message, Text):
                popup = Popup(error.message + "\n", level=0, timer=None)
            else:
                popup = Popup(Text.from_markup(error.message + "\n"), level=0, timer=None)
            self.console.print(popup)
            self.help_popup = popup
        else:
            super().on_validate_error(value, error)


class TUI(UI, App[None]):
    """TODO."""

    DEFAULT_CSS = """
    Screen {
        layers: default popup overlay;
        align-vertical: bottom;
    }
    """

    # TODO: extract key bindings to widgets where appropriate
    BINDINGS = [
        ("q", "quit", "Quit's coBib"),
        ("v", "select", "Selects the current entry"),
        ("slash", "search", "Searches the database for the provided string"),
        ("s", "sort", "Prompts for the field to sort by (use -r to list in reverse)"),
        ("f", "filter", "Allows filtering the table using `++/--` keywords"),
        ("e", "edit", "Edits the current entry"),
        ("o", "open", "Opens the current (or selected) entries"),
        ("d", "delete", "Delete the current (or selected) entries"),
        ("a", "prompt('add ')", "Prompts for a new entry to be added to the database"),
        ("i", "prompt('import ')", "Imports entries from another source"),
        ("m", "prompt('modify ', False, True)", "Prompts for a modification (respects selection)"),
        ("x", "prompt('export ', False, True)", "Exports the current (or selected) entries"),
        ("r", "prompt('redo', True)", "Redoes the last undone change. Requires git-tracking!"),
        ("u", "prompt('undo', True)", "Undes the last change. Requires git-tracking!"),
        ("j", "arrow_key('down')", "Moves one row down"),
        ("k", "arrow_key('up')", "Moves one row up"),
        ("h", "arrow_key('left')", "Moves to the left"),
        ("l", "arrow_key('right')", "Moves to the right"),
        Binding("down", "arrow_key('down')", "Moves one row down", show=False),
        Binding("up", "arrow_key('up')", "Moves one row up", show=False),
        Binding("left", "arrow_key('left')", "Moves to the left", show=False),
        Binding("right", "arrow_key('right')", "Moves to the right", show=False),
        ("colon", "prompt(':')", "Starts the prompt for an arbitrary coBib command"),
        ("enter", "show_entry", "Shows the current entry in the preview"),
        ("space", "toggle_fold", "Toggles folding of a search result"),
        ("underscore", "toggle_layout", "Toggles between the horizontal and vertical layout"),
        ("question_mark", "toggle_help", "Toggles the help page"),
    ]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """TODO."""
        super().__init__(*args, **kwargs)
        self.title = "coBib"
        self.sub_title = "The Console Bibliography Manager"
        self._list_args = ["-r"]
        self._filter: SelectionFilter = SelectionFilter()
        self._background_tasks: set[asyncio.Task] = set()  # type: ignore[type-arg]
        PopupLoggingHandler(self, level=logging.INFO)
        Progress.console = self
        FileDownloader.progress = Progress

    def compose(self) -> ComposeResult:
        """TODO."""
        yield HelpSidebar(classes="-hidden")

        main = MainView()
        yield main

        entry = EntryView()
        yield entry

        yield PopupPanel()

        yield Header()
        yield Footer()  # TODO: adapt to make more useful with so many key bindings as here

        command = commands.ListCommand(*self._list_args)
        command.execute()
        table = command.render_textual()
        main.mount(table)

    # TODO: remove once https://github.com/Textualize/textual/pull/1541 is merged into Textual
    @contextmanager
    def suspend(self) -> Iterator[None]:
        """TODO."""
        driver = self._driver
        if driver is not None:
            driver.stop_application_mode()
            with redirect_stdout(sys.__stdout__), redirect_stderr(sys.__stderr__):
                yield
            driver.start_application_mode()

    def action_toggle_help(self) -> None:
        """TODO."""
        help_sidebar = self.query_one(HelpSidebar)
        self.set_focus(None)
        if help_sidebar.has_class("-hidden"):
            help_sidebar.remove_class("-hidden")
        else:
            help_sidebar.add_class("-hidden")

    def action_toggle_fold(self) -> None:
        """TODO."""
        # TODO: provide more ways to fold (e.g. recursively)
        try:
            main = self.query_one(MainView).query_one(Tree)
            main.action_toggle_node()
        except NoMatches:
            pass

    def action_arrow_key(self, key_name: str) -> None:
        """TODO."""
        # TODO: handle scroll offset
        main = self.query_one(MainView).children[0]
        cursor_func = getattr(main, f"action_cursor_{key_name}", None)
        if cursor_func is None:
            return
        cursor_func()
        self._show_entry()

    def _get_current_label(self) -> str:
        """TODO."""
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

    def _show_entry(self) -> None:
        """TODO."""
        label = self._get_current_label()
        show_cmd = commands.ShowCommand(label)
        show_cmd.execute()
        entry = self.query_one(EntryView)
        entry.string = show_cmd.render_rich(
            background_color=entry.background_colors[1].rich_color.name,
        )

    def _select_entry(self) -> None:
        """TODO."""
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

    def _edit_entry(self) -> None:
        """TODO."""
        label = self._get_current_label()
        with self.suspend():
            commands.EditCommand(label).execute()
        self.refresh(layout=True)

    async def action_edit(self) -> None:
        """TODO."""
        self._edit_entry()

    async def action_open(self) -> None:
        """TODO."""
        labels: list[str]
        if self._filter.selection:
            labels = list(self._filter.selection)
            self._filter.selection.clear()
        else:
            labels = [self._get_current_label()]

        open_cmd = commands.OpenCommand(*labels, prompt=TextualPrompt, console=self)
        task = asyncio.create_task(open_cmd.execute())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

    async def action_select(self) -> None:
        """TODO."""
        self._select_entry()

    async def action_delete(self) -> None:
        """TODO."""
        labels: list[str]
        if self._filter.selection:
            labels = list(self._filter.selection)
            self._filter.selection.clear()
        else:
            labels = [self._get_current_label()]

        commands.DeleteCommand(*labels).execute()
        self._update_table()

    def on_mount(self) -> None:
        """TODO."""
        self.screen.styles.layout = "horizontal"
        self._show_entry()

    async def action_show_entry(self) -> None:
        """TODO."""
        self._show_entry()

    def action_toggle_layout(self) -> None:
        """TODO."""
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

    def on_input_submitted(self, event: _Input.Submitted) -> None:
        """TODO."""
        event.input.remove()
        if event.value[0] == "/":
            event.value = "search " + event.value[1:]

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
                                *command[1:], prompt=TextualPrompt, console=self
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

    def print(self, renderable: RenderableType | Widget) -> tuple[Widget, AwaitMount]:
        """TODO."""
        if isinstance(renderable, Widget):
            popup = renderable
        else:
            popup = Popup(renderable, level=0, timer=None)

        await_mount = self.query_one(PopupPanel).mount(popup)

        return popup, await_mount

    async def action_search(self) -> None:
        """TODO."""
        await self.action_prompt("/")

    async def action_filter(self) -> None:
        """TODO."""
        await self.action_prompt("list " + " ".join(self._list_args) + " ")

    async def action_sort(self) -> None:
        """TODO."""
        try:
            # first, remove any previously used sort argument
            sort_arg_idx = self._list_args.index("-s")
            self._list_args.pop(sort_arg_idx)
        except ValueError:
            pass

        # add the sort option to the arguments
        self._list_args += ["-s"]

        await self.action_prompt("list " + " ".join(self._list_args) + " ")

    async def action_prompt(
        self, value: str, submit: bool = False, check_selection: bool = False
    ) -> None:
        """TODO."""
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

    def _update_table(self) -> None:
        """TODO."""
        # TODO: retain scroll position
        main = self.query_one(MainView)
        main.clear()
        command = commands.ListCommand(*self._list_args)
        command.execute()
        table = command.render_textual()
        main.mount(table)
        main.focus()
        self.refresh(layout=True)
