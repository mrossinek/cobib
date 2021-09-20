"""coBib's curses-based TUI.

This class implements a curses-based TUI.
As such it provides an interactive front-end to coBib which allows easy navigation and manipulation
of the database.
It also benefits from some performance advantages over the command-line interface when doing many
operations because the parsed database entries remain in memory all the time and do not need to be
re-parsed upon every command invocation.

### Usage

The TUI exposes all commands through single-character key codes as well as some additional
TUI-specific commands:
* `Help` (defaults to the `?` key): opens a help popup.
* `Quit` (defaults to the `q` key): quits the TUI (or one level such as a popup).
* `Prompt` (defaults to the `:` key): starts the command prompt where a used can execute *any* coBib
  command-line command.
* `Select` (defaults to the `v` key): visually selects an entry.
* `Wrap` (defaults to the `w` key): wraps the buffer contents to the terminal width.

Additionally, the following navigation keys are available (these will be familiar to Vim-users):
* *arrow down*, `j`: move one line down
* *arrow up*, `k`: move one line up
* *arrow right*, `l`: move visible area one column to the right (has no effect when wrapped)
* *arrow left*, `h`: move visible area one column to the left (has no effect when wrapped)
* *page down*, `C-F`: move 20 lines down
* *page up*, `C-B`: move 20 lines up
* `C-D`: move 10 lines down
* `C-U`: move 10 lines up
* `G`: jump to the bottom of the buffer
* `g`: jump to the top of the buffer
* `0`: jump to the left end of the buffer
* `$`: jump to the right end of the buffer

In combination with the documentation of the other commands (see `cobib.commands`) the usage of the
TUI should be rather straight forward.

### Configuration

coBib's TUI provides a variety of configuration options.
In order to not duplicate the information here, please refer to the end of `cobib.config.example`
where all settings are listed and commented in detail.
"""

from __future__ import annotations

import curses
import fcntl
import logging
import re
import shlex
import signal
import struct
import sys
from termios import TIOCGWINSZ
from typing import IO, Any, Callable, Dict, List, Optional, Set, Tuple, Union, cast

from cobib import commands
from cobib.config import config
from cobib.utils.file_downloader import FileDownloader

from .buffer import InputBuffer, TextBuffer
from .frame import Frame
from .state import STATE, Mode

LOGGER = logging.getLogger(__name__)


class TUI:
    """coBib's curses-based TUI.

    The TUI is implemented as a class to simplify management of different windows/pads and keep a
    synchronized state most consistently.
    """

    COLOR_VALUES: Dict[str, int] = {
        "black": curses.COLOR_BLACK,
        "blue": curses.COLOR_BLUE,
        "cyan": curses.COLOR_CYAN,
        "green": curses.COLOR_GREEN,
        "magenta": curses.COLOR_MAGENTA,
        "red": curses.COLOR_RED,
        "white": curses.COLOR_WHITE,
        "yellow": curses.COLOR_YELLOW,
    }
    """A dictionary mapping color names to their `curses` values."""

    COLOR_NAMES: List[str] = [
        "top_statusbar",
        "bottom_statusbar",
        "search_label",
        "search_query",
        "cursor_line",
        "popup_help",
        "popup_stdout",
        "popup_stderr",
        "selection",
    ]
    """The list of available TUI colors."""

    ANSI_MAP: Dict[str, int] = {}
    """A dictionary mapping ANSI color codes to `curses` color pairs."""

    COMMANDS: Dict[str, Callable] = {  # type: ignore
        "Add": commands.add.AddCommand.tui,
        "Delete": commands.delete.DeleteCommand.tui,
        "Edit": commands.edit.EditCommand.tui,
        "Export": commands.export.ExportCommand.tui,
        "Filter": commands.list.ListCommand.tui_filter,
        "Help": lambda self: self.help(),
        "Modify": commands.modify.ModifyCommand.tui,
        "Open": commands.open.OpenCommand.tui,
        "Prompt": lambda self: self.execute_command(None),
        "Quit": lambda self: self.quit(),
        "Redo": commands.redo.RedoCommand.tui,
        "Search": commands.search.SearchCommand.tui,
        "Select": lambda self: self.select(),
        "Show": commands.show.ShowCommand.tui,
        "Sort": commands.list.ListCommand.tui_sort,
        "Undo": commands.undo.UndoCommand.tui,
        "Wrap": lambda self: self.viewport.wrap(),
        "x": lambda self, update: self.viewport.scroll_x(update),
        "y": lambda self, update: self.viewport.scroll_y(update),
    }
    """The dictionary of available commands."""

    HELP_DICT: Dict[str, str] = {
        "Add": "Prompts for a new entry to be added to the database.",
        "Delete": "Removes the current entry from the database.",
        "Edit": "Edits the current entry in an external EDITOR.",
        "Export": "Allows exporting the database to .bib or .zip files.",
        "Filter": "Allows filtering the list via `++/--` keywords.",
        "Help": "Displays this help.",
        "Modify": "Allows basic modification of multiple entries at once.",
        "Open": "Opens the associated file of an entry.",
        "Prompt": "Executes arbitrary coBib CLI commands in the prompt.",
        "Quit": "Closes current menu and quit's coBib.",
        "Redo": "Redoes the last undone change. Requires git-tracking!",
        "Search": "Searches the database for a given string.",
        "Select": "Adds the current entry to the interactive selection.",
        "Show": "Shows the details of an entry.",
        "Sort": "Prompts for the field to sort against (-r to reverse).",
        "Undo": "Undoes the last change. Requires git-tracking!",
        "Wrap": "Wraps the text displayed in the window.",
    }
    """The dictionary of help strings associated with their commands."""

    KEYDICT: Dict[int, Any] = {
        curses.KEY_DOWN: ("y", 1),
        curses.KEY_UP: ("y", -1),
        curses.KEY_NPAGE: ("y", 20),
        curses.KEY_PPAGE: ("y", -20),
        ord("j"): ("y", 1),
        ord("k"): ("y", -1),
        ord("g"): ("y", "g"),
        ord("G"): ("y", "G"),
        2: ("y", -20),  # CTRL-B
        4: ("y", 10),  # CTRL-D
        6: ("y", 20),  # CTRL-F
        21: ("y", -10),  # CTRL-U
        curses.KEY_LEFT: ("x", -1),
        curses.KEY_RIGHT: ("x", 1),
        ord("h"): ("x", -1),
        ord("l"): ("x", 1),
        ord("0"): ("x", 0),
        ord("$"): ("x", "$"),
    }
    """The dictionary of standard key-bindings. This will *only* be completed at runtime."""

    def __init__(self, stdscr: "curses.window", debug: bool = False) -> None:  # type: ignore
        """Initializes the curses-TUI and starts the event loop.

        Args:
            stdscr: the curses standard screen as returned by `curses.initscr`.
            debug: if True, the key-event loop is not automatically started.
        """
        LOGGER.info("Initializing TUI.")
        self.stdscr = stdscr

        # redirect stdout and stderr
        self.stdout = sys.stdout = TextBuffer()  # type: ignore
        self.stderr = sys.stderr = TextBuffer()  # type: ignore

        # register resize handler
        signal.signal(signal.SIGWINCH, self.resize_handler)

        # Clear and refresh the screen for a blank canvas
        self.stdscr.clear()
        self.stdscr.refresh()
        # Initialize layout
        curses.curs_set(0)
        self.height, self.width = self.stdscr.getmaxyx()
        LOGGER.debug("stdscr size determined to be %dx%d", self.width, self.height)
        # and colors
        LOGGER.debug("Initializing colors.")
        curses.use_default_colors()
        TUI.colors()
        # and user key mappings
        LOGGER.debug("Initializing key bindings.")
        TUI.bind_keys()

        # Initialize STATE
        LOGGER.debug("Initializing global State")
        self.STATE = STATE  # pylint: disable=invalid-name
        STATE.initialize()
        # load further configuration settings
        self.prompt_before_quit = config.tui.prompt_before_quit

        # the selection needs to be tracked outside of the State in order to persist across
        # different views
        self.selection: Set[str] = set()
        """The labels of the currently visually selected entries."""

        # Initialize top status bar
        LOGGER.debug("Populating top status bar.")
        self.topbar = curses.newwin(1, self.width, 0, 0)
        self.topbar.bkgd(" ", curses.color_pair(TUI.COLOR_NAMES.index("top_statusbar") + 1))

        # Initialize bottom status bar
        # NOTE: -2 leaves an additional empty line for the command prompt
        LOGGER.debug("Populating bottom status bar.")
        self.botbar = curses.newwin(1, self.width, self.height - 2, 0)
        self.botbar.bkgd(" ", curses.color_pair(TUI.COLOR_NAMES.index("bottom_statusbar") + 1))
        self.statusbar(self.botbar, self.infoline())

        # Initialize prompt line
        # The prompt is a pad to allow command/error prompts to exceed the terminal width.
        self.prompt = curses.newpad(1, self.width)

        # set prompt line as output source of the global file downloader
        FileDownloader().set_logger(self.prompt_print)

        # Initialize main viewport
        LOGGER.debug("Initializing viewport with Frame")
        # NOTE: -3 accounts for the top and bottom statusline as well as the command prompt
        self.viewport = Frame(self, self.height - 3, self.width)
        # populate buffer with list of reference entries
        LOGGER.debug("Populating viewport buffer.")
        self.viewport.update_list()

        if not debug:
            # start key event loop
            LOGGER.debug("Starting key event loop.")
            self.loop()
            LOGGER.info("Exiting TUI.")  # pragma: no cover

    def resize_handler(self, signum: Optional[int], frame) -> None:  # type: ignore
        # pylint: disable=unused-argument
        """Handles terminal window resizing events.

        This method gets exploited to trigger a refresh of the entire TUI window.
        In such a case it will be called as `resize_handler(None, None)`.

        Args:
            signum: signal number.
            frame: unused argument, required by the function template.
        """
        LOGGER.debug("Handling resize event.")
        if signum == signal.SIGWINCH:
            # update total dimension data
            buf = struct.pack("HHHH", 0, 0, 0, 0)
            # We use f_d = 0 as this redirects to STDIN under the hood, regardless of whether the
            # application is actually running in the foreground or in a pseudo terminal.
            buf = fcntl.ioctl(0, TIOCGWINSZ, buf)
            self.height, self.width = struct.unpack("HHHH", buf)[0:2]
        if signum is not None and not curses.is_term_resized(self.height, self.width):
            # when no signal number was given, this was a manually triggered event with the purpose
            # of completely refreshing the screen
            LOGGER.debug("Resize event did not have any effect: %dx%d", self.width, self.height)
            return
        LOGGER.debug("New stdscr dimension determined to be %dx%d", self.width, self.height)
        # actually resize the terminal
        curses.resize_term(self.height, self.width)
        # clear and refresh for a blank canvas
        self.stdscr.clear()
        self.stdscr.refresh()
        # update top statusbar
        self.topbar.resize(1, self.width)
        self.statusbar(self.topbar, STATE.topstatus)
        self.topbar.refresh()
        # update bottom statusbar
        self.botbar.resize(1, self.width)
        self.botbar.mvwin(self.height - 2, 0)
        self.statusbar(self.botbar, self.infoline())
        self.botbar.refresh()
        # update prompt
        self.prompt.resize(1, self.width)
        self.prompt.refresh(0, 0, self.height - 1, 0, self.height, self.width - 1)
        # update viewport
        self.viewport.resize(self.height - 3, self.width)

    def quit(self) -> None:
        """Breaks the key event loop or quits one TUI level.

        You can disable the final prompt before coBib quits via `config.tui.prompt_before_quit`.
        """
        if STATE.mode == Mode.LIST.value:
            LOGGER.debug("Quitting from lowest level.")
            if self.prompt_before_quit:
                msg = "Do you really want to quit coBib? [y/n] "
                curses.curs_set(1)
                self.prompt.clear()
                if len(msg) >= self.prompt.getmaxyx()[1] - 2:
                    self.prompt.resize(1, len(msg) + 2)
                self.prompt.insstr(0, 0, msg)
                self.prompt.move(0, len(msg))
                self.prompt.refresh(0, 0, self.height - 1, 0, self.height, self.width - 1)
                key = 0
                while True:
                    if key in (ord("y"), ord("Y")):
                        raise StopIteration
                    if key in (ord("n"), ord("N")):
                        LOGGER.info("User aborted quitting.")
                        curses.curs_set(0)
                        break
                    key = self.prompt.getch()
                self.prompt.clear()
                self.prompt.refresh(0, 0, self.height - 1, 0, self.height, self.width - 1)
            else:
                raise StopIteration
        else:
            LOGGER.debug("Quitting higher menu level. Falling back to list view.")
            self.viewport.revert()

    @staticmethod
    def colors() -> None:
        """Initializes the color pairs for the curses TUI."""
        # Start colors in curses
        curses.start_color()
        # parse user color configuration
        color_cfg = config.tui.colors
        colors: Dict[str, Dict[str, str]] = {col: {} for col in TUI.COLOR_NAMES}
        for attr, col in color_cfg.items():
            if attr in TUI.COLOR_VALUES:
                if not curses.can_change_color():
                    # cannot change curses default colors
                    LOGGER.warning("Curses cannot change the default colors. Skipping color setup.")
                    continue
                # update curses-internal color with HEX-color
                rgb_color = tuple(int(col.strip("#")[i : i + 2], 16) for i in (0, 2, 4))
                # curses colors range from 0 to 1000
                curses_color = tuple(col * 1000 // 255 for col in rgb_color)
                curses.init_color(TUI.COLOR_VALUES[attr], *curses_color)
            else:
                if attr[:-3] not in TUI.COLOR_NAMES:
                    LOGGER.warning("Detected unknown TUI color name specification: %s", attr[:-3])
                    continue
                colors[attr[:-3]][attr[-2:]] = col

        # initialize color pairs for TUI elements
        for idx, attr in enumerate(TUI.COLOR_NAMES):
            foreground = colors[attr].get("fg", "white")
            background = colors[attr].get("bg", "black")
            LOGGER.debug("Initiliazing color pair %d for %s", idx + 1, attr)
            curses.init_pair(idx + 1, TUI.COLOR_VALUES[foreground], TUI.COLOR_VALUES[background])
            LOGGER.debug("Adding ANSI color code for %s", attr)
            TUI.ANSI_MAP[config.get_ansi_color(attr)] = TUI.COLOR_NAMES.index(attr) + 1

    @staticmethod
    def bind_keys() -> None:
        """Binds keys according to the user configuration."""
        for command, key in config.tui.key_bindings.items():
            command = command.title()
            LOGGER.info("Binding key %s to the %s command.", key, command)
            if command not in TUI.COMMANDS.keys():
                LOGGER.warning('Unknown command "%s". Ignoring key binding.', command)
                continue
            if key == "ENTER":
                TUI.KEYDICT[10] = command  # line feed
                TUI.KEYDICT[13] = command  # carriage return
                continue
            if isinstance(key, str):
                # map key to its ASCII number
                key = ord(key)
            TUI.KEYDICT[key] = command

    @staticmethod
    def statusbar(statusline: "curses.window", text: str, attr: int = 0) -> None:  # type: ignore
        """Updates the text in the provided status bar and refreshes it.

        Args:
            statusline: single line height window used as a statusline.
            text: text to place in the statusline.
            attr: attribute number to use for the printed text.
        """
        statusline.erase()
        _, max_x = statusline.getmaxyx()
        statusline.addnstr(0, 0, text, max_x - 1, attr)
        statusline.refresh()

    @staticmethod
    def infoline() -> str:
        """Returns the available key bindings for the bottom status bar."""
        infoline = ""
        for cmd in TUI.HELP_DICT:
            # get associated key for this command
            key = config.tui.key_bindings[cmd.lower()]
            infoline += f" {key}:{cmd}"
        return infoline.strip()

    def help(self) -> None:
        # pylint: disable=consider-using-f-string
        """The Help Command.

        Opens a popup with more detailed information on the configured key bindings and short
        descriptions of the associated commands.
        """
        LOGGER.debug("Help command triggered.")
        # populate text buffer with help text
        help_text = TextBuffer()
        LOGGER.debug("Generating help text.")
        for cmd, desc in TUI.HELP_DICT.items():
            key: Union[int, str]
            for key, command in TUI.KEYDICT.items():
                if cmd == command:
                    # find mapped key
                    key = "ENTER" if key in (10, 13) else chr(key)
                    break
            # write: [key] Command: Description
            help_text.write("{:^8} {:<8} {}".format("[" + str(key) + "]", cmd + ":", desc))
        # add header section
        help_text.lines.insert(0, "{0:^{1}}".format("coBib TUI Help", help_text.width))
        help_text.lines.insert(1, "{:^8} {:<8} {}".format("Key", "Command", "Description"))
        help_text.height += 2

        # open help popup
        help_text.popup(self, background=TUI.COLOR_NAMES.index("popup_help"))

    def loop(self, debug: bool = False) -> None:
        """The key-handling event loop.

        This method takes care of reading the user's key strokes and triggering associated commands.

        Args:
            debug: if True, the key-event loop is not automatically started.
        """
        key = 0
        # key is the last character pressed
        while True:
            # handle possible keys
            try:
                if key in TUI.KEYDICT:
                    cmd = TUI.KEYDICT[key]
                    if cmd not in STATE.inactive_commands:
                        if isinstance(cmd, tuple):
                            TUI.COMMANDS[cmd[0]](self, cmd[1])
                        else:
                            TUI.COMMANDS[cmd](self)
                elif key == curses.KEY_RESIZE:
                    self.resize_handler(None, None)
            except StopIteration:
                LOGGER.debug("Stopping key event loop.")
                # raised by quit command
                sys.stdout = sys.__stdout__
                sys.stderr = sys.__stderr__
                break

            # highlight current line
            current_attributes: List[Optional[int]] = []
            for x_pos in range(0, self.viewport.pad.getmaxyx()[1]):
                x_ch = self.viewport.pad.inch(STATE.current_line, x_pos)
                # store attributes by filtering out the character text
                current_attributes.append(x_ch & curses.A_CHARTEXT)  # type: ignore
                # extract color information
                x_color = x_ch & curses.A_COLOR  # type: ignore
                color_pair_content = curses.pair_content(curses.pair_number(x_color))
                # if the current color attribute is lower in priority than the current line
                # highlighting, use that instead
                if all(col <= 0 for col in color_pair_content):
                    self.viewport.pad.chgat(
                        STATE.current_line,
                        x_pos,
                        1,
                        curses.color_pair(TUI.COLOR_NAMES.index("cursor_line") + 1),
                    )
                else:
                    # otherwise, we remove the stored attributes in order to not reset them later
                    current_attributes[-1] = None

            for stream, name in zip((self.stderr, self.stdout), ("stderr", "stdout")):
                stream.flush()
                if stream.lines:
                    stream.split()
                    LOGGER.info("sys.%s contains:\n%s", name, "\n".join(stream.lines))
                    # wrap before checking the height:
                    stream.wrap(self.width)
                    if stream.height > 1 and not debug:
                        stream.popup(self, background=TUI.COLOR_NAMES.index(f"popup_{name}"))
                    else:
                        self.prompt_print(stream.lines)
                    stream.clear()

            # Refresh the screen
            self.viewport.refresh()

            # Wait for next input
            key = self.stdscr.getch()
            LOGGER.debug("Key press registered: %s", str(key))

            # reset highlight of current line
            for x_pos in range(0, self.viewport.pad.getmaxyx()[1]):
                attr = current_attributes[x_pos]
                if attr is not None:
                    self.viewport.pad.chgat(STATE.current_line, x_pos, 1, attr)

    def select(self) -> None:
        """Toggles selection of the label currently under the cursor."""
        LOGGER.debug("Select command triggered.")
        # get current label
        label, cur_y = self.viewport.get_current_label()
        # toggle selection
        if label not in self.selection:
            LOGGER.info("Adding '%s' to the selection.", label)
            self.selection.add(label)
            # Note, that we use an additional two spaces to attempt to uniquely identify the label
            # in the list mode. Otherwise it might be possible that the same text (as used for the
            # label) can occur elsewhere in the buffer.
            # We do not need this outside of the list view because then the line indexed by `cur_y`
            # will surely only include the one label which we actually want to operate on.
            offset = "  " if STATE.mode == Mode.LIST.value else ""
            self.viewport.buffer.replace(
                cur_y,
                label + offset,
                config.get_ansi_color("selection") + label + "\x1b[0m" + offset,
            )
        else:
            LOGGER.info("Removing '%s' from the selection.", label)
            self.selection.remove(label)
            self.viewport.buffer.replace(
                cur_y,
                re.escape(config.get_ansi_color("selection")) + label + re.escape("\x1b[0m"),
                label,
            )
        # update buffer view
        self.viewport.view(ansi_map=self.ANSI_MAP)

    def prompt_print(self, text: Union[str, List[str]]) -> None:
        """Prints text to the prompt line.

        This function also handles a bug in curses which disallows 'newline'-characters [1].
        Thus, if this is the case, the first line is printed in the prompt and the total text is
        also presented in a popup. The reason for the duplicate information is too provide a little
        context on the left-over message once the popup window has been closed.

        [1] https://docs.python.org/3/library/curses.html#curses.window.addstr

        Args:
            text: the test to print to the prompt.
        """
        lines = text.strip().split("\n") if isinstance(text, str) else text
        self.prompt.clear()
        self.prompt.resize(1, max(len(lines[0]), self.width))
        self.prompt.addstr(0, 0, lines[0])
        self.prompt.refresh(0, 0, self.height - 1, 0, self.height, self.width - 1)
        if len(lines) > 1:
            buffer = TextBuffer()
            buffer.write("\n".join(lines))
            buffer.popup(self, background=TUI.COLOR_NAMES.index("popup_stderr"))

    def prompt_handler(self, command: Optional[str], symbol: str = ":") -> str:
        """Handles prompt input.

        This method starts another loop during which user key strokes are being caught and
        interpreted.

        Args:
            command: the command string to populate the prompt with.
            symbol: the prompt symbol.

        Returns:
            The final user command.
        """
        LOGGER.debug("Handling input by the user in prompt line.")
        # make cursor visible
        curses.curs_set(1)

        # populate prompt line and place cursor
        prompt_line = symbol if command is None else f"{symbol}{command} "
        self.prompt.clear()
        self.prompt.resize(1, max(len(prompt_line) + 2, self.width))
        self.prompt.addstr(0, 0, prompt_line)
        self.prompt.move(0, len(prompt_line))
        self.prompt.refresh(0, 0, self.height - 1, 0, self.height, self.width - 1)

        key = 0
        command = ""
        while True:
            # get current cursor position
            _, cur_x = self.prompt.getyx()
            # get next key
            self.prompt.nodelay(False)
            key = self.prompt.getch()
            LOGGER.debug("Key press registered: %s", str(key))
            # handle keys
            if key == 27:  # ESC
                self.prompt.nodelay(True)
                # check if it was an arrow escape sequence
                self.prompt.getch()
                arrow = self.prompt.getch()
                if arrow == -1:
                    LOGGER.debug("Prompt input aborted by the user.")
                    # if not, ESC ends the prompt
                    break
                if arrow == 68:  # left arrow key
                    LOGGER.debug("Move cursor left from arrow key input.")
                    self.prompt.move(_, cur_x - 1)
                elif arrow == 67:  # right arrow key
                    LOGGER.debug("Move cursor right from arrow key input.")
                    self.prompt.move(_, cur_x + 1)
            elif key in (8, 127):  # BACKSPACE
                if cur_x > 1:
                    LOGGER.debug("Delete the previous character in the prompt.")
                    self.prompt.delch(_, cur_x - 1)
                else:
                    LOGGER.debug("Prompt input aborted by the user.")
                    command = ""
                    break
            elif key in (10, 13):  # ENTER
                LOGGER.debug("Execute the command as prompted.")
                command = cast(bytes, self.prompt.instr(0, 1)).decode("utf-8").strip()
                break
            elif key == -1:  # no input
                break  # pragma: no cover
            else:
                # any normal key is simply echoed
                self.prompt.resize(1, max(cur_x + 2, self.width))
                self.prompt.addstr(_, cur_x, chr(key))
                self.prompt.move(_, cur_x + 1)
            self.prompt.refresh(
                0, max(0, cur_x - self.width + 2), self.height - 1, 0, self.height, self.width - 1
            )
        # leave echo mode and make cursor invisible
        curses.curs_set(0)

        # clear prompt line
        self.prompt.clear()
        self.prompt.refresh(0, 0, self.height - 1, 0, self.height, self.width - 1)

        return command

    def execute_command(
        self,
        command: Union[str, List[str]],
        out: Optional[IO[Any]] = None,
        pass_selection: bool = False,
        skip_prompt: bool = False,
    ) -> Tuple[List[str], Any]:
        """Executes a command.

        Args:
            command: the command to execute.
            out: the output stream to redirect stdout to.
            pass_selection: whether to the pass the current TUI selection in the executed command
                arguments.
            skip_prompt: whether to skip the user prompt for further commands.

        Returns:
            A pair with the first element being the list with the executed command to allow further
            handling and the second element being whatever is returned by the command.
        """
        if not skip_prompt:
            command = self.prompt_handler(cast(str, command))
            # split command into separate arguments for cobib
            try:
                command = shlex.split(command)
            except ValueError:
                LOGGER.error("Invalid command: %s", command)
                return ([""], None)

        command = cast(List[str], command)

        # process command if it is non empty and actually has arguments
        result = None
        if command and command[0]:
            LOGGER.debug("Processing the command: %s", " ".join(command))
            # run command
            sys.stdin = InputBuffer(buffer=self.stdout, tui=self)  # type: ignore
            subcmd = getattr(commands, command[0].title() + "Command")()
            try:
                if pass_selection:
                    command += ["--"]
                    command.extend(list(self.selection))
                result = subcmd.execute(command[1:], out=out)
            except SystemExit:  # pragma: no cover
                pass  # pragma: no cover
            sys.stdin = sys.__stdin__
        # return command to enable additional handling by function caller
        return (command, result)
