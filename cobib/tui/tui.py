"""CoBib curses interface."""

import curses
import re
import sys
from functools import partial
from signal import signal, SIGWINCH

from cobib import __version__
from cobib import commands
from cobib.config import CONFIG
from .buffer import TextBuffer


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

    COLOR_PAIRS = {
        'cursor_line': [1, 'white', 'cyan'],
        'top_statusbar': [2, 'black', 'yellow'],
        'bottom_statusbar': [3, 'black', 'yellow'],
        'help': [4, 'white', 'red'],
        'search_label': [5, 'blue', 'black'],
        'search_query': [6, 'red', 'black'],
        # TODO when implementing select command add a color configuration option
    }

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
        # TODO select command
        'Select': lambda self: self.prompt_warning('The Select command is not implemented yet!'),
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
        ord('g'): ('y', 0),
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
        self.stdscr = stdscr

        # register resize handler
        signal(SIGWINCH, self.resize_handler)

        # Clear and refresh the screen for a blank canvas
        self.stdscr.clear()
        self.stdscr.refresh()
        # Initialize layout
        curses.curs_set(0)
        self.height, self.width = self.stdscr.getmaxyx()
        self.visible = self.height-3
        # and colors
        curses.use_default_colors()
        TUI.colors()
        # and user key mappings
        TUI.bind_keys()
        # and inactive commands
        self.inactive_commands = []
        # and default list args
        if 'TUI' in CONFIG.config.keys() and CONFIG.config['TUI'].get('default_list_args', ''):
            self.list_args = CONFIG.config['TUI'].get('default_list_args').split(' ')
        else:
            self.list_args = ['-l']

        if 'TUI' in CONFIG.config.keys() and CONFIG.config['TUI'].getboolean('reverse_order', True):
            self.list_args += ['-r']
        else:
            self.list_args += ['-r']

        # load further configuration settings
        if 'TUI' in CONFIG.config.keys():
            self.prompt_before_quit = CONFIG.config['TUI'].getboolean('prompt_before_quit', True)
        else:
            self.prompt_before_quit = True

        # Initialize top status bar
        self.topbar = curses.newwin(1, self.width, 0, 0)
        self.topbar.bkgd(' ', curses.color_pair(TUI.COLOR_PAIRS['top_statusbar'][0]))

        # Initialize bottom status bar
        # NOTE: -2 leaves an additional empty line for the command prompt
        self.botbar = curses.newwin(1, self.width, self.height-2, 0)
        self.botbar.bkgd(' ', curses.color_pair(TUI.COLOR_PAIRS['bottom_statusbar'][0]))
        self.statusbar(self.botbar, self.infoline())

        # Initialize command prompt and viewport
        self.viewport = curses.newpad(1, 1)
        # NOTE being a window and not a pad, the prompt has a limited width. If this ever causes
        # problems, change this here and ensure it is being resized when necessary.
        self.prompt = curses.newwin(1, self.width, self.height-1, 0)

        # prepare key event loop
        self.list_mode = -1  # -1: list mode active, >=0: previously selected line
        self.current_line = 0
        self.top_line = 0
        self.left_edge = 0

        # populate buffer with list of reference entries
        self.buffer = TextBuffer()
        self.update_list()

        # start key event loop
        self.loop()

    def resize_handler(self, signum, frame):  # pylint: disable=unused-argument
        """Handles terminal window resize events.

        Args:
            signum (int): signal number.
            frame: unused argument, required by the function template.
        """
        # stop curses window
        curses.endwin()
        # clear and refresh for a blank canvas
        self.stdscr.clear()
        self.stdscr.refresh()
        # update total dimension data
        self.height, self.width = self.stdscr.getmaxyx()
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
        self.prompt.mvwin(self.height-1, 0)
        # update viewport
        self.viewport.refresh(self.top_line, self.left_edge, 1, 0, self.visible, self.width-1)

    def quit(self):
        """Breaks the key event loop or quits one viewport level."""
        if self.list_mode == -1:
            if self.prompt_before_quit:
                self.prompt.clear()
                self.prompt.insstr(0, 0, 'Do you really want to quit CoBib? [y/n] ')
                self.prompt.refresh()
                key = 0
                while True:
                    if key in (ord('y'), ord('Y')):
                        raise StopIteration
                    if key in (ord('n'), ord('N')):
                        break
                    key = self.prompt.getch()
                self.prompt.clear()
                self.prompt.refresh()
            else:
                raise StopIteration
        self.update_list()

    @staticmethod
    def colors():
        """Initialize the color pairs for the curses TUI."""
        # Start colors in curses
        curses.start_color()
        # parse user color configuration
        if 'COLORS' in CONFIG.config.keys():
            color_cfg = CONFIG.config['COLORS']
            for attr, col in color_cfg.items():
                if attr in TUI.COLOR_VALUES.keys():
                    if not curses.can_change_color():
                        # cannot change curses default colors
                        continue
                    # update curses-internal color with HEX-color
                    rgb_color = tuple(int(col.strip('#')[i:i+2], 16) for i in (0, 2, 4))
                    # curses colors range from 0 to 1000
                    curses_color = tuple(col * 1000 // 255 for col in rgb_color)
                    curses.init_color(TUI.COLOR_VALUES[attr], *curses_color)
                else:
                    # check if the attribute fits a TUI element name
                    for element in TUI.COLOR_PAIRS:
                        if element == attr[:-3] and attr[-3:] in ('_fg', '_bg'):
                            # determine whether foreground or background color are specified
                            ground = 1 if attr[-3:] == '_fg' else 2
                            TUI.COLOR_PAIRS[element][ground] = col

        # initialize color pairs for TUI elements
        for idx, foreground, background in TUI.COLOR_PAIRS.values():
            curses.init_pair(idx, TUI.COLOR_VALUES[foreground], TUI.COLOR_VALUES[background])

    @staticmethod
    def bind_keys():
        """Bind keys according to user configuration."""
        if 'KEY_BINDINGS' in CONFIG.config.keys():
            key_bindings = CONFIG.config['KEY_BINDINGS']
            for command, key in key_bindings.items():
                if command not in TUI.COMMANDS.keys():
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
        # sorted commands to place in help window
        cmds = ["Quit", "Help", "", "Show", "Open", "Wrap", "", "Add", "Edit", "Delete", "",
                "Search", "Filter", "Sort", "Select", "", "Export"]
        # populate text buffer with help text
        help_text = TextBuffer()
        for cmd in cmds:
            if cmd:
                key = ' '
                for key, command in TUI.KEYDICT.items():
                    if cmd == command:
                        # find mapped key
                        key = 'ENTER' if key in (10, 13) else chr(key)
                        break
                # write: [key] Command: Description
                help_text.write("{:^8} {:<8} {}".format('['+key+']', cmd+':', TUI.HELP_DICT[cmd]))
            else:
                # add empty line
                help_text.lines.append('')
                help_text.height += 1
        # add header section
        help_text.lines.insert(0, "{0:^{1}}".format("CoBib TUI Help", help_text.width))
        help_text.lines.insert(1, "{:^8} {:<8} {}".format('Key', 'Command', 'Description'))
        help_text.height += 2

        # populate help window
        help_win = curses.newpad(help_text.height+2, help_text.width+5)  # offsets account for box
        help_win.bkgd(' ', curses.color_pair(TUI.COLOR_PAIRS['help'][0]))
        for row, line in enumerate(help_text.lines):
            attr = 0
            if row < 3:
                attr = curses.A_BOLD
            help_win.addstr(row+1, 2, line, attr)
        # display help window
        help_win.box()
        help_h, help_w = help_win.getmaxyx()
        help_win.refresh(0, 0, 1, 1, 1+help_h, 1+help_w)

        key = 0
        # loop until quit by user
        while key not in (27, ord('q')):  # exit on ESC
            key = self.prompt.getch()

        # close help window
        help_win.clear()
        self.resize_handler(None, None)

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
                # raised by quit command
                break

            # highlight current line
            current_attrs = []
            for x_pos in range(0, self.buffer.width):
                current_attrs.append(self.viewport.inch(self.current_line, x_pos))
            self.viewport.chgat(self.current_line, 0,
                                curses.color_pair(TUI.COLOR_PAIRS['cursor_line'][0]))

            # Refresh the screen
            self.viewport.refresh(self.top_line, self.left_edge, 1, 0, self.visible, self.width-1)

            # Wait for next input
            key = self.stdscr.getch()

            # reset highlight of current line
            for x_pos in range(0, self.buffer.width):
                self.viewport.chgat(self.current_line, x_pos, 1, current_attrs[x_pos])

    def scroll_y(self, update):
        """Scroll viewport vertically.

        Args:
            update (int or str): the offset specifying the scrolling height.
        """
        # jump to top
        if update == 0:
            self.top_line = 0
            self.current_line = 0
        # jump to bottom
        elif update == 'G':
            self.top_line = max(self.buffer.height - self.visible, 0)
            self.current_line = self.buffer.height-1
        # scroll up
        elif update < 0:
            next_line = self.current_line + update
            if self.top_line > 0 and next_line < self.top_line:
                self.top_line += update
            if next_line >= 0:
                self.current_line = next_line
            else:
                self.current_line = 0
        # scroll down
        elif update > 0:
            next_line = self.current_line + update
            if next_line - self.top_line >= self.visible and \
                    self.top_line + self.visible < self.buffer.height:
                self.top_line += update
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
            self.left_edge = 0
        # jump to end
        elif update == '$':
            self.left_edge = self.buffer.width - self.width
        else:
            next_col = self.left_edge + update
            # limit column such that no empty columns can appear on left or right
            if 0 <= next_col <= self.buffer.width - self.width:
                self.left_edge = next_col

    def wrap(self):
        """Toggles wrapping of the text currently displayed in the viewport."""
        # first, ensure left_edge is set to 0
        self.left_edge = 0
        # then, wrap the buffer
        self.buffer.wrap(self.width)
        self.buffer.view(self.viewport, self.visible, self.width-1)
        # if cursor line is below buffer height, move it one line back up
        if self.current_line >= self.buffer.height:
            self.current_line -= 1

    def prompt_handler(self, command, out=None):
        """Handle prompt input.

        Args:
            command (str or None): the command string to populate the prompt with.
            out (stream, optional): the output stream to redirect stdout to.

        Returns:
            A pair with the first element being the list with the executed command to allow further
            handling and the second element being whatever is returned by the command.
        """
        # make cursor visible
        curses.curs_set(1)

        # populate prompt line and place cursor
        prompt_line = ":" if command is None else f":{command} "
        self.prompt.clear()
        self.prompt.addstr(0, 0, prompt_line)
        self.prompt.move(0, len(prompt_line))
        self.prompt.refresh()

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
                    # if not, ESC ends the prompt
                    break
                if arrow == 68:  # left arrow key
                    self.prompt.move(_, cur_x - 1)
                elif arrow == 67:  # right arrow key
                    self.prompt.move(_, cur_x + 1)
            elif key == 127:  # BACKSPACE
                if cur_x > 1:
                    self.prompt.delch(_, cur_x - 1)
            elif key in (10, 13):  # ENTER
                command = self.prompt.instr(0, 1).decode('utf-8').strip()
                break
            else:
                # any normal key is simply echoed
                self.prompt.addstr(_, cur_x, chr(key))
                self.prompt.move(_, cur_x + 1)
        # split command into separate arguments for cobib
        command = command.split(' ')

        # leave echo mode and make cursor invisible
        curses.curs_set(0)

        # clear prompt line
        self.prompt.clear()
        self.prompt.refresh()

        # process command if it non empty and actually has arguments
        result = None
        if command and command[1:]:
            # temporarily disable prints to stdout
            original_stdout = sys.stderr
            sys.stderr = TextBuffer()
            # run command
            subcmd = getattr(commands, command[0].title()+'Command')()
            result = subcmd.execute(command[1:], out=out)
            # if error occurred print info to prompt
            if sys.stderr.lines:
                self.prompt.addstr(0, 0, sys.stderr.lines[0])
                self.prompt.refresh()
                # command exited with an error
                self.update_list()
            # restore stdout
            sys.stderr = original_stdout
        # return command to enable additional handling by function caller
        return (command, result)

    def prompt_warning(self, msg):
        """Prints a warning to the command prompt.

        Args:
            msg (str): message text to print.
        """
        self.prompt.clear()
        self.prompt.insstr(0, 0, f'Warning: {msg}')
        self.prompt.refresh()

    def get_current_label(self):
        """Returns the label and y position of the currently selected entry."""
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
        return label, cur_y

    def update_list(self):
        """Updates the default list view."""
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
        # display buffer in viewport
        self.buffer.view(self.viewport, self.visible, self.width-1)
        # update top statusbar
        self.topstatus = "CoBib v{} - {} Entries".format(__version__, len(labels))
        self.statusbar(self.topbar, self.topstatus)
        # if cursor position is out-of-view (due to e.g. top-line reset in Show command), reset the
        # top-line such that the current line becomes visible again
        if self.current_line > self.top_line + self.visible:
            self.top_line = min(self.current_line, self.buffer.height - self.visible)
