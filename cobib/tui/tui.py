"""CoBib curses interface"""

import curses
import sys
from functools import partial
from signal import signal, SIGWINCH

from cobib import __version__
from cobib import commands
from cobib.config import CONFIG
from .buffer import TextBuffer


class TUI:  # pylint: disable=too-many-instance-attributes
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
        # TODO when implementing select command add a color configuration option
    }

    # available command dictionary
    COMMANDS = {
        'Add': commands.AddCommand.tui,
        'Delete': commands.DeleteCommand.tui,
        'Edit': commands.EditCommand.tui,
        'Export': commands.ExportCommand.tui,
        'Filter': commands.ListCommand.tui,
        'Help': lambda self: self.help(),
        'Open': commands.OpenCommand.tui,
        'Quit': lambda self: self.quit(),
        'Search': lambda _: None,  # TODO search command
        'Select': lambda _: None,  # TODO select command
        'Show': commands.ShowCommand.tui,
        'Sort': partial(commands.ListCommand.tui, args='-s'),
        'Wrap': lambda self: self.wrap(),
        'bottom': lambda self: self.scroll_y('G'),
        'down': lambda self: self.scroll_y(1),
        'end': lambda self: self.scroll_x('$'),
        'home': lambda self: self.scroll_x(0),
        'left': lambda self: self.scroll_x(-1),
        'right': lambda self: self.scroll_x(1),
        'top': lambda self: self.scroll_y(0),
        'up': lambda self: self.scroll_y(-1),
    }
    # standard key bindings
    KEYDICT = {
        10: 'Show',  # line feed = ENTER
        13: 'Show',  # carriage return = ENTER
        curses.KEY_DOWN: 'down',
        curses.KEY_LEFT: 'left',
        curses.KEY_RIGHT: 'right',
        curses.KEY_UP: 'up',
        ord('$'): 'end',
        ord('/'): 'Search',
        ord('0'): 'home',
        ord('?'): 'Help',
        ord('G'): 'bottom',
        ord('a'): 'Add',
        ord('d'): 'Delete',
        ord('e'): 'Edit',
        ord('f'): 'Filter',
        ord('g'): 'top',
        ord('h'): 'left',
        ord('j'): 'down',
        ord('k'): 'up',
        ord('l'): 'right',
        ord('o'): 'Open',
        ord('q'): 'Quit',
        ord('s'): 'Sort',
        ord('v'): 'Select',
        ord('w'): 'Wrap',
        ord('x'): 'Export',
    }

    def __init__(self, stdscr):
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
        TUI.colors()
        # and user key mappings
        TUI.bind_keys()
        # and inactive commands
        self.inactive_commands = []
        # and default list args
        if 'TUI' in CONFIG.sections() and CONFIG['TUI'].get('default_list_args'):
            self.list_args = CONFIG['TUI'].get('default_list_args').split(' ')
        else:
            self.list_args = ['-l']

        # Initialize top status bar
        self.topbar = curses.newwin(1, self.width, 0, 0)
        self.topbar.bkgd(' ', curses.color_pair(TUI.COLOR_PAIRS['top_statusbar'][0]))

        # Initialize bottom status bar
        # NOTE: -2 leaves an additional empty line for the command prompt
        self.botbar = curses.newwin(1, self.width, self.height-2, 0)
        self.botbar.bkgd(' ', curses.color_pair(TUI.COLOR_PAIRS['bottom_statusbar'][0]))
        self.statusbar(self.botbar, self.infoline)

        # Initialize command prompt and viewport
        self.prompt = curses.newwin(1, self.width, self.height-1, 0)
        self.viewport = curses.newpad(1, 1)

        # populate buffer with list of reference entries
        self.buffer = TextBuffer()
        self.update_list()

        # prepare and start key event loop
        self.current_line = 0
        self.list_mode = -1  # -1: list mode active, >=0: previously selected line
        self.top_line = 0
        self.left_edge = 0
        self.loop()

    def resize_handler(self, signum, frame):  # pylint: disable=unused-argument
        """Handles terminal window resize events."""
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
        self.statusbar(self.botbar, self.infoline)
        self.botbar.refresh()
        # update prompt
        self.prompt.resize(1, self.width)
        self.prompt.mvwin(self.height-1, 0)
        # update viewport
        self.viewport.refresh(self.top_line, self.left_edge, 1, 0, self.visible, self.width-1)

    def quit(self):
        """Break the key event loop."""
        if self.list_mode == -1:
            raise StopIteration
        self.current_line = self.list_mode
        self.update_list()

    @staticmethod
    def colors():
        """Initialize the color pairs for the curses TUI."""
        # Start colors in curses
        curses.start_color()
        # parse user color configuration
        if 'COLORS' in CONFIG.sections():
            color_cfg = CONFIG['COLORS']
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
                            # determine whethre foreground or background color are specified
                            ground = 1 if attr[-3:] == '_fg' else 2
                            TUI.COLOR_PAIRS[element][ground] = col

        # initialize color pairs for TUI elements
        for idx, foreground, background in TUI.COLOR_PAIRS.values():
            curses.init_pair(idx, TUI.COLOR_VALUES[foreground], TUI.COLOR_VALUES[background])

    @staticmethod
    def bind_keys():
        """Bind keys according to user configuration."""
        if 'KEY_BINDINGS' in CONFIG.sections():
            key_bindings = CONFIG['KEY_BINDINGS']
            for command, key in key_bindings.items():
                if command not in TUI.COMMANDS.keys():
                    continue
                if key == 'ENTER':
                    TUI.KEYDICT[10] = command  # line feed
                    TUI.KEYDICT[13] = command  # carriage return
                    continue
                if isinstance(key, str):
                    # map key to its ascii number
                    key = ord(key)
                TUI.KEYDICT[key] = command

    @staticmethod
    def statusbar(statusline, text, attr=0):
        """Update the text in the provided status bar and refresh it."""
        statusline.erase()
        _, max_x = statusline.getmaxyx()
        statusline.addnstr(0, 0, text, max_x-1, attr)
        statusline.refresh()

    @property
    def infoline(self):
        """Lists available key bindings."""
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
        """Help command."""
        cmds = ["Quit", "Help", "", "Show", "Open", "Wrap", "", "Add", "Edit", "Delete", "",
                "Search", "Filter", "Sort", "Select", "", "Export"]
        # setup help strings
        help_dict = {
            "Quit": "Closes current menu and quit's CoBib.",
            "Help": "Displays this help.",
            "Show": "Shows the details of an entry.",
            "Open": "Opens the associated file of an entry.",
            "Wrap": "Wraps the text displayed in the window for improved readability.",
            "Add": "Prompts for a new entry to be added to the database.",
            "Edit": "Edits the current entry in an external EDITOR.",
            "Delete": "Removes the current entry from the database.",
            "Search": "**not** implemented yet.",
            "Filter": "Allows filtering the list using CoBib's `list ++/--` filter options.",
            "Sort": "Prompts for the field to sort against (use -r to reverse the order).",
            "Select": "**not** implemented yet.",
            "Export": "Allows exporting the database to .bib or .zip files.",
        }
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
                help_text.write("{:^8} {:<8} {}".format('['+key+']', cmd+':', help_dict[cmd]))
            else:
                # add empty line
                help_text.lines.append('')
                help_text.height += 1
        # add header section
        help_text.lines.insert(0, "{0:^{1}}".format("CoBib TUI Help", help_text.width))
        help_text.lines.insert(1, '')
        help_text.lines.insert(2, "{:^8} {:<8} {}".format('Key', 'Command', 'Description'))
        help_text.height += 3

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
        offset = 4
        help_win.refresh(0, 0, offset, offset, offset+help_h, offset+help_w)

        key = 0
        # loop until quit by user
        while key not in (27, ord('q')):  # exit on ESC
            key = self.prompt.getch()

        # close help window
        help_win.clear()

    def loop(self):
        """The key-handling event loop."""
        key = 0
        # key is the last character pressed
        while True:
            # reset highlight of current line
            self.viewport.chgat(self.current_line, 0, curses.A_NORMAL)

            # handle possible keys
            try:
                if key in TUI.KEYDICT.keys():
                    cmd = TUI.KEYDICT[key]
                    if cmd not in self.inactive_commands:
                        TUI.COMMANDS[cmd](self)
                elif key == curses.KEY_RESIZE:
                    self.resize_handler(None, None)
            except StopIteration:
                # raised by quit command
                break

            # highlight current line
            self.viewport.chgat(self.current_line, 0,
                                curses.color_pair(TUI.COLOR_PAIRS['cursor_line'][0]))

            # Refresh the screen
            self.viewport.refresh(self.top_line, self.left_edge, 1, 0, self.visible, self.width-1)

            # Wait for next input
            key = self.stdscr.getch()

    def scroll_y(self, update):
        """Scroll viewport vertically."""
        # jump to top
        if update == 0:
            self.top_line = 0
            self.current_line = 0
        # jump to bottom
        elif update == 'G':
            self.top_line = max(self.buffer.height - self.visible, 0)
            self.current_line = self.buffer.height-1
        # scroll up
        elif update == -1:
            next_line = self.current_line + update
            if self.top_line > 0 and next_line < self.top_line:
                self.top_line += update
            if next_line >= 0:
                self.current_line = next_line
        # scroll down
        elif update == 1:
            next_line = self.current_line + update
            if next_line - self.top_line == self.visible and \
                    self.top_line + self.visible < self.buffer.height:
                self.top_line += update
            if next_line < self.buffer.height:
                self.current_line = next_line

    def scroll_x(self, update):
        """Scroll viewport horizontally."""
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

    def prompt_handler(self, command, out=None):
        """Handle prompt input."""
        # enter echo mode and make cursor visible
        curses.echo()
        curses.curs_set(1)

        # populate prompt line and place cursor
        prompt_line = ":" if command is None else f":{command} "
        self.prompt.clear()
        self.prompt.addstr(0, 0, prompt_line)
        self.prompt.move(0, len(prompt_line))
        self.prompt.refresh()

        key = 0
        command = ''
        # handle special keys
        while key != 27:  # exit on ESC
            if key == 127:  # BACKSPACE
                cur_y, cur_x = self.prompt.getyx()
                # replace last three characters with spaces (2 characters from BACKSPACE key)
                self.prompt.addstr(cur_y, cur_x - 3, '   ')
                self.prompt.move(cur_y, cur_x - 3)
            elif key in (10, 13):  # ENTER
                command = self.prompt.instr(0, 1).decode('utf-8').strip()
                break
            key = self.prompt.getch()

        # leave echo mode and make cursor invisible
        curses.noecho()
        curses.curs_set(0)

        # clear prompt line
        self.prompt.clear()
        self.prompt.refresh()

        # process command if it non empty and actually has arguments
        if command and command.split(' ')[1:]:
            # temporarily disable prints to stdout
            original_stdout = sys.stderr
            sys.stderr = TextBuffer()
            # run command
            subcmd = getattr(commands, command.split(' ')[0].title()+'Command')()
            subcmd.execute(command.split(' ')[1:], out=out)
            # if error occurred print info to prompt
            if sys.stderr.lines:
                self.prompt.addstr(0, 0, sys.stderr.lines[0])
                self.prompt.refresh()
                # command exited with an error
                self.update_list()
            # restore stdout
            sys.stderr = original_stdout
        else:
            # command was aborted
            self.update_list()

    def get_current_label(self):
        """Obtain label of currently selected entry."""
        # Two cases are possible: the list and the show mode
        if self.list_mode == -1:
            # In the list mode, the label can be found in the current line
            # or in one of the previous lines if we are on a wrapped line
            cur_y, _ = self.viewport.getyx()
            while chr(self.viewport.inch(cur_y, 0)) == TextBuffer.INDENT[0]:
                cur_y -= 1
            label = self.viewport.instr(cur_y, 0).decode('utf-8').split(' ')[0]
            self.list_mode = cur_y
        else:
            # In any other mode, the label can be found in the top statusbar
            label = '-'.join(self.topbar.instr(0, 0).decode('utf-8').split('-')[1:]).strip()
        return label

    def update_list(self):
        """Updates the default list view."""
        self.buffer.clear()
        labels = commands.ListCommand().execute(self.list_args, out=self.buffer)
        # populate buffer with the list
        self.list_mode = -1
        self.inactive_commands = []
        self.buffer.view(self.viewport, self.visible, self.width-1)
        # update top statusbar
        self.topstatus = "CoBib v{} - {} Entries".format(__version__, len(labels))
        self.statusbar(self.topbar, self.topstatus)
