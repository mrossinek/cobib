"""CoBib curses interface."""

import curses
import logging
import re
import shlex
import sys
from functools import partial
from signal import signal, SIGWINCH

from cobib import __version__
from cobib import commands
from cobib.config import CONFIG
from .buffer import TextBuffer, InputBuffer

LOGGER = logging.getLogger(__name__)


class TUI:
    """CoBib's curses-based TUI.

    The TUI is implemented as a class to simplify management of different windows/pads and keep a
    synchronized state most consistently.
    """

    COLOR_VALUES = {
        'black': curses.COLOR_BLACK,
        'blue': curses.COLOR_BLUE,
        'cyan': curses.COLOR_CYAN,
        'green': curses.COLOR_GREEN,
        'magenta': curses.COLOR_MAGENTA,
        'red': curses.COLOR_RED,
        'white': curses.COLOR_WHITE,
        'yellow': curses.COLOR_YELLOW,
    }

    COLOR_NAMES = [
        'top_statusbar',
        'bottom_statusbar',
        'search_label',
        'search_query',
        'cursor_line',
        'popup_help',
        'popup_stdout',
        'popup_stderr',
        'selection',
    ]

    ANSI_MAP = {}

    # available command dictionary
    COMMANDS = {
        'Add': commands.AddCommand.tui,
        'Delete': commands.DeleteCommand.tui,
        'Edit': commands.EditCommand.tui,
        'Export': commands.ExportCommand.tui,
        'Filter': partial(commands.ListCommand.tui, sort_mode=False),
        'Help': lambda self: self.help(),
        'Open': commands.OpenCommand.tui,
        'Quit': lambda self: self.quit(),
        'Search': commands.SearchCommand.tui,
        'Select': lambda self: self.select(),
        'Show': commands.ShowCommand.tui,
        'Sort': partial(commands.ListCommand.tui, sort_mode=True),
        'Wrap': lambda self: self.wrap(),
        'x': lambda self, update: self.scroll_x(update),
        'y': lambda self, update: self.scroll_y(update),
    }

    # command help strings
    HELP_DICT = {
        "Add": "Prompts for a new entry to be added to the database.",
        "Delete": "Removes the current entry from the database.",
        "Edit": "Edits the current entry in an external EDITOR.",
        "Export": "Allows exporting the database to .bib or .zip files.",
        "Filter": "Allows filtering the list via `++/--` keywords.",
        "Help": "Displays this help.",
        "Open": "Opens the associated file of an entry.",
        "Quit": "Closes current menu and quit's CoBib.",
        "Search": "**not** implemented yet.",
        "Select": "**not** implemented yet.",
        "Show": "Shows the details of an entry.",
        "Sort": "Prompts for the field to sort against (-r to reverse).",
        "Wrap": "Wraps the text displayed in the window.",
    }

    # standard key bindings
    KEYDICT = {
        10: 'Show',  # line feed = ENTER
        13: 'Show',  # carriage return = ENTER
        curses.KEY_DOWN: ('y', 1),
        curses.KEY_UP: ('y', -1),
        curses.KEY_NPAGE: ('y', 20),
        curses.KEY_PPAGE: ('y', -20),
        ord('j'): ('y', 1),
        ord('k'): ('y', -1),
        ord('g'): ('y', 'g'),
        ord('G'): ('y', 'G'),
        2: ('y', -20),  # CTRL-B
        4: ('y', 10),  # CTRL-D
        6: ('y', 20),  # CTRL-F
        21: ('y', -10),  # CTRL-U
        curses.KEY_LEFT: ('x', -1),
        curses.KEY_RIGHT: ('x', 1),
        ord('h'): ('x', -1),
        ord('l'): ('x', 1),
        ord('0'): ('x', 0),
        ord('$'): ('x', '$'),
        ord('/'): 'Search',
        ord('?'): 'Help',
        ord('a'): 'Add',
        ord('d'): 'Delete',
        ord('e'): 'Edit',
        ord('f'): 'Filter',
        ord('o'): 'Open',
        ord('q'): 'Quit',
        ord('s'): 'Sort',
        ord('v'): 'Select',
        ord('w'): 'Wrap',
        ord('x'): 'Export',
    }

    def __init__(self, stdscr):
        """Initializes the curses-TUI and starts the event loop.

        Args:
            stdscr (curses.window): the curses standard screen as returned by curses.initscr().
        """
        LOGGER.info('Initializing TUI.')
        self.stdscr = stdscr

        # register resize handler
        signal(SIGWINCH, self.resize_handler)

        # Clear and refresh the screen for a blank canvas
        self.stdscr.clear()
        self.stdscr.refresh()
        # Initialize layout
        curses.curs_set(0)
        self.height, self.width = self.stdscr.getmaxyx()
        LOGGER.debug('stdscr size determined to be %dx%d', self.width, self.height)
        self.visible = self.height-3
        # and colors
        LOGGER.debug('Initializing colors.')
        curses.use_default_colors()
        TUI.colors()
        # and user key mappings
        LOGGER.debug('Initializing key bindings.')
        TUI.bind_keys()
        # and inactive commands
        self.inactive_commands = []
        # and default list args
        self.list_args = CONFIG.config['TUI'].get('default_list_args').split(' ')
        # and empty selection
        self.selection = set()

        if CONFIG.config['TUI'].getboolean('reverse_order', True):
            self.list_args += ['-r']

        # load further configuration settings
        self.prompt_before_quit = CONFIG.config['TUI'].getboolean('prompt_before_quit', True)

        # Initialize top status bar
        LOGGER.debug('Populating top status bar.')
        self.topbar = curses.newwin(1, self.width, 0, 0)
        self.topbar.bkgd(' ', curses.color_pair(TUI.COLOR_NAMES.index('top_statusbar') + 1))

        # Initialize bottom status bar
        # NOTE: -2 leaves an additional empty line for the command prompt
        LOGGER.debug('Populating bottom status bar.')
        self.botbar = curses.newwin(1, self.width, self.height-2, 0)
        self.botbar.bkgd(' ', curses.color_pair(TUI.COLOR_NAMES.index('bottom_statusbar') + 1))
        self.statusbar(self.botbar, self.infoline())

        # Initialize command prompt and viewport
        self.viewport = curses.newpad(1, 1)
        # The prompt is a pad to allow command/error prompts to exceed the terminal width.
        self.prompt = curses.newpad(1, self.width)

        # prepare key event loop
        self.list_mode = -1  # -1: list mode active, >=0: previously selected line
        self.current_line = 0
        self.top_line = 0
        self.left_edge = 0

        # populate buffer with list of reference entries
        LOGGER.debug('Populating viewport buffer.')
        self.buffer = TextBuffer()
        self.update_list()

        # start key event loop
        LOGGER.debug('Starting key event loop.')
        self.loop()
        LOGGER.info('Exiting TUI.')

    def resize_handler(self, signum, frame):  # pylint: disable=unused-argument
        """Handles terminal window resize events.

        Args:
            signum (int): signal number.
            frame: unused argument, required by the function template.
        """
        LOGGER.debug('Handling resize event.')
        # stop curses window
        curses.endwin()
        # clear and refresh for a blank canvas
        self.stdscr.clear()
        self.stdscr.refresh()
        # update total dimension data
        self.height, self.width = self.stdscr.getmaxyx()
        LOGGER.debug('New stdscr dimension determined to be %dx%d', self.width, self.height)
        self.visible = self.height-3
        # update top statusbar
        self.topbar.resize(1, self.width)
        self.statusbar(self.topbar, self.topstatus)
        self.topbar.refresh()
        # update bottom statusbar
        self.botbar.resize(1, self.width)
        self.botbar.mvwin(self.height-2, 0)
        self.statusbar(self.botbar, self.infoline())
        self.botbar.refresh()
        # update prompt
        self.prompt.resize(1, self.width)
        self.prompt.refresh(0, 0, self.height-1, 0, self.height, self.width-1)
        # update viewport
        self.viewport.refresh(self.top_line, self.left_edge, 1, 0, self.visible, self.width-1)

    def quit(self):
        """Breaks the key event loop or quits one viewport level."""
        if self.list_mode == -1:
            LOGGER.debug('Quitting from lowest level.')
            if self.prompt_before_quit:
                msg = 'Do you really want to quit CoBib? [y/n] '
                curses.curs_set(1)
                self.prompt.clear()
                if len(msg) >= self.prompt.getmaxyx()[1] - 2:
                    self.prompt.resize(1, len(msg) + 2)
                self.prompt.insstr(0, 0, msg)
                self.prompt.move(0, len(msg))
                self.prompt.refresh(0, 0, self.height-1, 0, self.height, self.width-1)
                key = 0
                while True:
                    if key in (ord('y'), ord('Y')):
                        raise StopIteration
                    if key in (ord('n'), ord('N')):
                        LOGGER.info('User aborted quitting.')
                        curses.curs_set(0)
                        break
                    key = self.prompt.getch()
                self.prompt.clear()
                self.prompt.refresh(0, 0, self.height-1, 0, self.height, self.width-1)
            else:
                raise StopIteration
        LOGGER.debug('Quitting higher menu level. Falling back to list view.')
        self.update_list()

    @staticmethod
    def colors():
        """Initialize the color pairs for the curses TUI."""
        # Start colors in curses
        curses.start_color()
        # parse user color configuration
        color_cfg = CONFIG.config['COLORS']
        colors = {col: {} for col in TUI.COLOR_NAMES}
        for attr, col in color_cfg.items():
            if attr in TUI.COLOR_VALUES.keys():
                if not curses.can_change_color():
                    # cannot change curses default colors
                    LOGGER.warning('Curses cannot change the default colors. Skipping color setup.')
                    continue
                # update curses-internal color with HEX-color
                rgb_color = tuple(int(col.strip('#')[i:i+2], 16) for i in (0, 2, 4))
                # curses colors range from 0 to 1000
                curses_color = tuple(col * 1000 // 255 for col in rgb_color)
                curses.init_color(TUI.COLOR_VALUES[attr], *curses_color)
            else:
                if attr[:-3] not in TUI.COLOR_NAMES:
                    LOGGER.warning('Detected unknown TUI color name specification: %s', attr[:-3])
                    continue
                colors[attr[:-3]][attr[-2:]] = col

        # initialize color pairs for TUI elements
        for idx, attr in enumerate(TUI.COLOR_NAMES):
            foreground = colors[attr].get('fg', 'white')
            background = colors[attr].get('bg', 'black')
            LOGGER.debug('Initiliazing color pair %d for %s', idx + 1, attr)
            curses.init_pair(idx + 1, TUI.COLOR_VALUES[foreground], TUI.COLOR_VALUES[background])
            LOGGER.debug('Adding ANSI color code for %s', attr)
            TUI.ANSI_MAP[CONFIG.get_ansi_color(attr)] = TUI.COLOR_NAMES.index(attr) + 1

    @staticmethod
    def bind_keys():
        """Bind keys according to user configuration."""
        key_bindings = CONFIG.config['KEY_BINDINGS']
        for command, key in key_bindings.items():
            LOGGER.info('Binding key %s to the %s command.', key, command)
            if command not in TUI.COMMANDS.keys():
                LOGGER.warning('Unknown command "%d". Ignoring key binding.', command)
                continue
            if key == 'ENTER':
                TUI.KEYDICT[10] = command  # line feed
                TUI.KEYDICT[13] = command  # carriage return
                continue
            if isinstance(key, str):
                # map key to its ASCII number
                key = ord(key)
            TUI.KEYDICT[key] = command

    @staticmethod
    def statusbar(statusline, text, attr=0):
        """Update the text in the provided status bar and refresh it.

        Args:
            statusline (curses.window): single line height window used as a statusline.
            text (str): text to place in the statusline.
            attr (int, optional): attribute number to use for the printed text.
        """
        statusline.erase()
        _, max_x = statusline.getmaxyx()
        statusline.addnstr(0, 0, text, max_x-1, attr)
        statusline.refresh()

    @staticmethod
    def infoline():
        """Returns a list of the available key bindings."""
        cmds = ["Quit", "Help", "", "Show", "Open", "Wrap", "", "Add", "Edit", "Delete", "",
                "Search", "Filter", "Sort", "Select", "", "Export"]
        infoline = ''
        for cmd in cmds:
            if cmd:
                # get associated key for this command
                for key, command in TUI.KEYDICT.items():
                    if cmd == command:
                        key = 'ENTER' if key in (10, 13) else chr(key)
                        infoline += " {}:{}".format(key, cmd)
                        break
            else:
                infoline += "  "
        return infoline.strip()

    def help(self):
        """Help command.

        Opens a new curses window with more detailed information on the configured key bindings and
        short descriptions of the commands.
        """
        LOGGER.debug('Help command triggered.')
        # sorted commands to place in help window
        cmds = ["Quit", "Help", "Show", "Open", "Wrap", "Add", "Edit", "Delete",
                "Search", "Filter", "Sort", "Select", "Export"]
        # populate text buffer with help text
        help_text = TextBuffer()
        LOGGER.debug('Generating help text.')
        for cmd in cmds:
            key = ' '
            for key, command in TUI.KEYDICT.items():
                if cmd == command:
                    # find mapped key
                    key = 'ENTER' if key in (10, 13) else chr(key)
                    break
            # write: [key] Command: Description
            help_text.write("{:^8} {:<8} {}".format('['+key+']', cmd+':', TUI.HELP_DICT[cmd]))
        # add header section
        help_text.lines.insert(0, "{0:^{1}}".format("CoBib TUI Help", help_text.width))
        help_text.lines.insert(1, "{:^8} {:<8} {}".format('Key', 'Command', 'Description'))
        help_text.height += 2

        # open help popup
        help_text.popup(self, background=TUI.COLOR_NAMES.index('popup_help'))

    def loop(self):
        """The key-handling event loop."""
        key = 0
        # key is the last character pressed
        while True:
            # handle possible keys
            try:
                if key in TUI.KEYDICT.keys():
                    cmd = TUI.KEYDICT[key]
                    if cmd not in self.inactive_commands:
                        if isinstance(cmd, tuple):
                            TUI.COMMANDS[cmd[0]](self, cmd[1])
                        else:
                            TUI.COMMANDS[cmd](self)
                elif key == curses.KEY_RESIZE:
                    self.resize_handler(None, None)
            except StopIteration:
                LOGGER.debug('Stopping key event loop.')
                # raised by quit command
                break

            # highlight current line
            current_colors = []
            for x_pos in range(0, self.viewport.getmaxyx()[1]):
                x_ch = self.viewport.inch(self.current_line, x_pos)
                current_colors.append(x_ch)
                # x_ch is the character at the queried position. The bottom 8 bits are the character
                # proper, and upper bits are the attributes.
                # Source: https://docs.python.org/3/library/curses.html#curses.window.inch
                # Thus, we can find the color attribute by striping the last 8 bits.
                x_attr = x_ch >> 8
                if x_attr <= TUI.COLOR_NAMES.index('cursor_line'):
                    self.viewport.chgat(self.current_line, x_pos, 1,
                                        curses.color_pair(TUI.COLOR_NAMES.index('cursor_line') + 1))

            # Refresh the screen
            self.viewport.refresh(self.top_line, self.left_edge, 1, 0, self.visible, self.width-1)

            # Wait for next input
            key = self.stdscr.getch()
            LOGGER.debug('Key press registered: %s', str(key))

            # reset highlight of current line
            for x_pos in range(0, self.viewport.getmaxyx()[1]):
                self.viewport.chgat(self.current_line, x_pos, 1, current_colors[x_pos])

    def scroll_y(self, update):
        """Scroll viewport vertically.

        Args:
            update (int or str): the offset specifying the scrolling height.
        """
        scrolloff = CONFIG.config['TUI'].getint('scroll_offset', 3)
        overlap = scrolloff >= self.visible - scrolloff
        scroll_lock = overlap and self.current_line - self.top_line == self.visible // 2
        # jump to top
        if update == 'g':
            LOGGER.debug('Jump to top of viewport.')
            self.top_line = 0
            self.current_line = 0
        # jump to bottom
        elif update == 'G':
            LOGGER.debug('Jump to bottom of viewport.')
            self.top_line = max(self.buffer.height - self.visible, 0)
            self.current_line = self.buffer.height-1
        # scroll up
        elif update < 0:
            LOGGER.debug('Scroll viewport up by %d lines.', update)
            next_line = self.current_line + update
            if self.top_line > 0 and next_line < self.top_line + scrolloff:
                if scroll_lock or not overlap:
                    self.top_line += update
                elif overlap and \
                        self.current_line - self.top_line > self.visible // 2 and \
                        next_line - self.top_line < self.visible // 2:
                    self.top_line = next_line - self.visible // 2
            self.current_line = max(next_line, 0)
        # scroll down
        elif update > 0:
            LOGGER.debug('Scroll viewport down by %d lines.', update)
            next_line = self.current_line + update
            if next_line >= self.top_line + self.visible - scrolloff and \
                    self.buffer.height > self.top_line + self.visible:
                if scroll_lock or not overlap:
                    self.top_line += update
                elif overlap and \
                        self.current_line - self.top_line < self.visible // 2 and \
                        next_line - self.top_line > self.visible // 2:
                    self.top_line = next_line - self.visible // 2
            if next_line < self.buffer.height:
                self.current_line = next_line
            else:
                self.top_line = self.buffer.height - self.visible
                self.current_line = self.buffer.height - 1

    def scroll_x(self, update):
        """Scroll viewport horizontally.

        Args:
            update (int or str): the offset specifying the scrolling width.
        """
        # jump to beginning
        if update == 0:
            LOGGER.debug('Jump to first column of viewport.')
            self.left_edge = 0
        # jump to end
        elif update == '$':
            LOGGER.debug('Jump to end of viewport.')
            self.left_edge = self.buffer.width - self.width
        else:
            LOGGER.debug('Scroll viewport horizontally by %d columns.', update)
            next_col = self.left_edge + update
            # limit column such that no empty columns can appear on left or right
            if 0 <= next_col <= self.buffer.width - self.width:
                self.left_edge = next_col

    def wrap(self):
        """Toggles wrapping of the text currently displayed in the viewport."""
        LOGGER.debug('Wrap command triggered.')
        # first, ensure left_edge is set to 0
        self.left_edge = 0
        # then, wrap the buffer
        self.buffer.wrap(self.width)
        self.buffer.view(self.viewport, self.visible, self.width-1)
        # if cursor line is below buffer height, move it one line back up
        if self.buffer.height and self.current_line >= self.buffer.height:
            self.current_line -= 1

    def select(self):
        """Toggles selection of the current label."""
        LOGGER.debug('Select command triggered.')
        # get current label
        label, cur_y = self.get_current_label()
        # toggle selection
        if label not in self.selection:
            LOGGER.info("Adding '%s' to the selection.", label)
            self.selection.add(label)
            # Note, that we use an additional two spaces to attempt to uniquely identify the label
            # in the list mode. Otherwise it might be possible that the same text (as used for the
            # label) can occur elsewhere in the buffer.
            # We do not need this outside of the list view because then the line indexed by `cur_y`
            # will surely only include the one label which we actually want to operate on.
            offset = '  ' if self.list_mode == -1 else ''
            self.buffer.replace(cur_y, label + offset,
                                CONFIG.get_ansi_color('selection') + label + '\x1b[0m' + offset)
        else:
            LOGGER.info("Removing '%s' from the selection.", label)
            self.selection.remove(label)
            self.buffer.replace(cur_y, CONFIG.get_ansi_color('selection') + label + '\x1b[0m',
                                label)
        # update buffer view
        self.buffer.view(self.viewport, self.visible, self.width-1, ansi_map=self.ANSI_MAP)

    def prompt_print(self, text):
        """Handle printing text to the prompt line.

        This function also handles a bug in curses which disallows 'newline'-characters [1].
        Thus, if this is the case, the first line is printed in the prompt and the total text is
        also presented in a popup window. The reason for the duplicate information is too provide a
        little context on the previous message once the popup window has been closed.

        [1] https://docs.python.org/3/library/curses.html#curses.window.addstr

        Args:
            text (str or list): the test to print to the prompt.
        """
        lines = text.strip().split('\n') if isinstance(text, str) else text
        self.prompt.clear()
        self.prompt.resize(1, max(len(lines[0]), self.width))
        self.prompt.addstr(0, 0, lines[0])
        self.prompt.refresh(0, 0, self.height-1, 0, self.height, self.width-1)
        if len(lines) > 1:
            buffer = TextBuffer()
            buffer.write(text)
            buffer.popup(self, background=TUI.COLOR_NAMES.index('popup_stderr'))

    def prompt_handler(self, command, symbol=":"):
        """Handle prompt input.

        Args:
            command (str or None): the command string to populate the prompt with.
            symbol (str, optional): the prompt symbol.

        Returns:
            The final user command.
        """
        LOGGER.debug('Handling input by the user in prompt line.')
        # make cursor visible
        curses.curs_set(1)

        # populate prompt line and place cursor
        prompt_line = symbol if command is None else f"{symbol}{command} "
        self.prompt.clear()
        self.prompt.resize(1, max(len(prompt_line)+2, self.width))
        self.prompt.addstr(0, 0, prompt_line)
        self.prompt.move(0, len(prompt_line))
        self.prompt.refresh(0, 0, self.height-1, 0, self.height, self.width-1)

        key = 0
        command = ''
        while True:
            # get current cursor position
            _, cur_x = self.prompt.getyx()
            # get next key
            self.prompt.nodelay(False)
            key = self.prompt.getch()
            # handle keys
            if key == 27:  # ESC
                self.prompt.nodelay(True)
                # check if it was an arrow escape sequence
                self.prompt.getch()
                arrow = self.prompt.getch()
                if arrow == -1:
                    LOGGER.debug('Prompt input aborted by the user.')
                    # if not, ESC ends the prompt
                    break
                if arrow == 68:  # left arrow key
                    LOGGER.debug('Move cursor left from arrow key input.')
                    self.prompt.move(_, cur_x - 1)
                elif arrow == 67:  # right arrow key
                    LOGGER.debug('Move cursor right from arrow key input.')
                    self.prompt.move(_, cur_x + 1)
            elif key == 127:  # BACKSPACE
                if cur_x > 1:
                    LOGGER.debug('Delete the previous character in the prompt.')
                    self.prompt.delch(_, cur_x - 1)
                else:
                    LOGGER.debug('Prompt input aborted by the user.')
                    command = ''
                    break
            elif key in (10, 13):  # ENTER
                LOGGER.debug('Execute the command as prompted.')
                command = self.prompt.instr(0, 1).decode('utf-8').strip()
                break
            else:
                # any normal key is simply echoed
                self.prompt.resize(1, max(cur_x + 2, self.width))
                self.prompt.addstr(_, cur_x, chr(key))
                self.prompt.move(_, cur_x + 1)
            self.prompt.refresh(0, max(0, cur_x - self.width + 2),
                                self.height-1, 0, self.height, self.width-1)
        # leave echo mode and make cursor invisible
        curses.curs_set(0)

        # clear prompt line
        self.prompt.clear()
        self.prompt.refresh(0, 0, self.height-1, 0, self.height, self.width-1)

        return command

    def execute_command(self, command, out=None, pass_selection=False, skip_prompt=False):
        """Executes a command.

        Args:
            command (str or None): the command to execute.
            out (stream, optional): the output stream to redirect stdout to.
            pass_selection (boolean, optional): whether to the pass the current TUI selection in the
                                                executed command arguments.
            skip_prompt (boolean, optional): whether to skip the user prompt for further commands.

        Returns:
            A pair with the first element being the list with the executed command to allow further
            handling and the second element being whatever is returned by the command.
        """
        if not skip_prompt:
            command = self.prompt_handler(command)
            # split command into separate arguments for cobib
            command = shlex.split(command)

        # process command if it non empty and actually has arguments
        result = None
        if command and command[0]:
            LOGGER.debug('Processing the command: %s', ' '.join(command))
            # temporarily disable prints to stdout, stderr and stdin
            original_stdin = sys.stdin
            original_stdout = sys.stdout
            original_stderr = sys.stderr
            sys.stdout = TextBuffer()
            sys.stderr = TextBuffer()
            sys.stdin = InputBuffer(buffer=sys.stdout, tui=self)
            # run command
            subcmd = getattr(commands, command[0].title()+'Command')()
            try:
                if pass_selection:
                    command += ['--']
                    command.extend(list(self.selection))
                result = subcmd.execute(command[1:], out=out)
            except SystemExit:
                pass
            # if error occurred print info to prompt
            if sys.stderr.lines:
                LOGGER.warning('The command "%s" resulted in an error.', ' '.join(command))
                sys.stderr.split()
                LOGGER.info('sys.stderr contains:\n%s', '\n'.join(sys.stderr.lines))
                # wrap before checking the height:
                sys.stderr.wrap(self.width)
                if sys.stderr.height > 1:
                    sys.stderr.popup(self, background=TUI.COLOR_NAMES.index('popup_stderr'))
                else:
                    self.prompt_print(sys.stderr.lines)
                # command exited with an error
                self.update_list()
            elif sys.stdout.lines:
                LOGGER.info('A message to stdout from "%s" was intercepted.', ' '.join(command))
                sys.stdout.split()
                LOGGER.info('sys.stdout contains:\n%s', '\n'.join(sys.stdout.lines))
                # wrap before checking the height:
                sys.stdout.wrap(self.width)
                if sys.stdout.height > 1:
                    sys.stdout.popup(self, background=TUI.COLOR_NAMES.index('popup_stdout'))
                else:
                    self.prompt_print(sys.stdout.lines)
            # restore stdout, stderr and stdin
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            sys.stdin = original_stdin
        # return command to enable additional handling by function caller
        return (command, result)

    def get_current_label(self):
        """Returns the label and y position of the currently selected entry."""
        LOGGER.debug('Obtaining current label "under" cursor.')
        cur_y, _ = self.viewport.getyx()
        # Two cases are possible: the list and the show mode
        if self.list_mode == -1:
            # In the list mode, the label can be found in the current line
            # or in one of the previous lines if we are on a wrapped line
            while chr(self.viewport.inch(cur_y, 0)) == TextBuffer.INDENT[0]:
                cur_y -= 1
            label = self.viewport.instr(cur_y, 0).decode('utf-8').split(' ')[0]
        elif re.match(r'\d+ hit',
                      '-'.join(self.topbar.instr(0, 0).decode('utf-8').split('-')[1:]).strip()):
            while chr(self.viewport.inch(cur_y, 0)) in ('[', TextBuffer.INDENT[0]):
                cur_y -= 1
            label = self.viewport.instr(cur_y, 0).decode('utf-8').split(' ')[0]
        else:
            # In any other mode, the label can be found in the top statusbar
            label = '-'.join(self.topbar.instr(0, 0).decode('utf-8').split('-')[1:]).strip()
            # We also set cur_y to 0 for the select command to find it
            cur_y = 0
        LOGGER.debug('Current label at "%s" is "%s".', str(cur_y), label)
        return label, cur_y

    def update_list(self):
        """Updates the default list view."""
        LOGGER.debug('Re-populating the viewport with the list command.')
        self.buffer.clear()
        labels = commands.ListCommand().execute(self.list_args, out=self.buffer)
        labels = labels or []  # convert to empty list if labels is None
        # populate buffer with the list
        if self.list_mode >= 0:
            self.current_line = self.list_mode
            self.list_mode = -1
        # reset viewport
        self.top_line = 0
        self.left_edge = 0
        self.inactive_commands = []
        # highlight current selection
        for label in self.selection:
            # Note: the two spaces are explained in the `select()` method.
            # Also: this step may become a performance bottleneck because we replace inside the
            # whole buffer for each selected label!
            self.buffer.replace(range(self.buffer.height), label + '  ',
                                CONFIG.get_ansi_color('selection') + label + '\x1b[0m  ')
        # display buffer in viewport
        self.buffer.view(self.viewport, self.visible, self.width-1, ansi_map=self.ANSI_MAP)
        # update top statusbar
        self.topstatus = "CoBib v{} - {} Entries".format(__version__, len(labels))
        self.statusbar(self.topbar, self.topstatus)
        # if cursor position is out-of-view (due to e.g. top-line reset in Show command), reset the
        # top-line such that the current line becomes visible again
        if self.current_line > self.top_line + self.visible:
            self.top_line = min(self.current_line, self.buffer.height - self.visible)
