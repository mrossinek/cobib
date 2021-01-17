"""CoBib's TUI viewport."""

import copy
import curses
import logging
import re

from cobib import __version__
from cobib.commands import ListCommand
from cobib.config import config
from .buffer import TextBuffer
from .state import Mode, STATE

LOGGER = logging.getLogger(__name__)


class Frame:
    """Frame class used to integrate a `TextBuffer` and `curses.pad` tightly with each other.

    This helper class is mainly used to implement the main 'viewport' of the TUI. It is a stateful
    object which handles a session-persistent history of the viewport to enable seamless level
    navigation.
    """

    def __init__(self, tui, max_height, max_width):
        """Initializes the Frame object."""
        LOGGER.debug("Initializing frame's buffer")
        self.buffer = TextBuffer()
        LOGGER.debug("Initializing frame's pad")
        self.pad = curses.newpad(1, 1)
        # Also store a history of buffer contents and state (such as the current line, etc.)
        self.history = []

        # store TUI reference
        self.tui = tui
        self.height = max_height
        self.width = max_width

    def clear(self):
        """Wrapper for buffer.clear to intercept for history storage."""
        self.history.append((copy.deepcopy(self.buffer), copy.deepcopy(STATE)))
        # almost 100 entries should be much more than enough
        self.history = self.history[:99]
        self.buffer.clear()

    def revert(self):
        """Reverts the frame to the previous state."""
        self.buffer, state = self.history.pop()
        STATE.update(state)
        self.buffer.replace(range(self.buffer.height), re.escape(config.get_ansi_color('selection'))
                            + r'(.+)' + re.escape('\x1b[0m'), r'\1')
        # highlight current selection
        for label in self.tui.selection:
            # Note: this step may become a performance bottleneck because we replace inside the
            # whole buffer for each selected label!
            if STATE.mode == Mode.SEARCH.value:
                # Note: the inclusion of the search label is explained in the `SearchCommand`.
                self.buffer.replace(range(self.buffer.height),
                                    re.escape(config.get_ansi_color('search_label')) + label
                                    + re.escape('\x1b[0m'),
                                    config.get_ansi_color('search_label') +
                                    config.get_ansi_color('selection') + label + '\x1b[0m\x1b[0m')
            else:
                # Note: the two spaces are explained in the `select()` method.
                self.buffer.replace(range(self.buffer.height), label + '  ',
                                    config.get_ansi_color('selection') + label + '\x1b[0m  ')
        self.view(ansi_map=self.tui.ANSI_MAP)
        self.tui.statusbar(self.tui.topbar, STATE.topstatus)

    def resize(self, new_height, new_width):
        """Resizes the Frame to the new dimensions.

        Args:
            new_height (int): the new height.
            new_width (int): the new width.
        """
        self.height = new_height
        self.width = new_width
        self.refresh()

    def refresh(self):
        """Utility function to quickly refresh the Frame's pad."""
        self.pad.refresh(STATE.top_line, STATE.left_edge, 1, 0, self.height, self.width-1)

    def view(self, ansi_map=None):
        """Utility function to quickly view the Frame's buffer.

        Args:
            ansi_map (dict): optional, dictionary mapping ANSI codes to curses color pairs.
        """
        self.buffer.view(self.pad, self.height, self.width-1, ansi_map=ansi_map)

    def scroll_y(self, update):
        """Scroll vertically.

        Args:
            update (int or str): the offset specifying the scrolling height.
        """
        scrolloff = config.tui.scroll_offset
        overlap = scrolloff >= self.height - scrolloff
        scroll_lock = overlap and STATE.current_line - STATE.top_line == self.height // 2
        # jump to top
        if update == 'g':
            LOGGER.debug('Jump to top of viewport.')
            STATE.top_line = 0
            STATE.current_line = 0
        # jump to bottom
        elif update == 'G':
            LOGGER.debug('Jump to bottom of viewport.')
            STATE.top_line = max(self.buffer.height - self.height, 0)
            STATE.current_line = self.buffer.height-1
        # scroll up
        elif update < 0:
            LOGGER.debug('Scroll viewport up by %d lines.', update)
            next_line = STATE.current_line + update
            if STATE.top_line > 0 and next_line < STATE.top_line + scrolloff:
                if scroll_lock or not overlap:
                    STATE.top_line += update
                elif overlap and \
                        STATE.current_line - STATE.top_line > self.height // 2 and \
                        next_line - STATE.top_line < self.height // 2:
                    STATE.top_line = next_line - self.height // 2
            STATE.current_line = max(next_line, 0)
        # scroll down
        elif update > 0:
            LOGGER.debug('Scroll viewport down by %d lines.', update)
            next_line = STATE.current_line + update
            if next_line >= STATE.top_line + self.height - scrolloff and \
                    self.buffer.height > STATE.top_line + self.height:
                if scroll_lock or not overlap:
                    STATE.top_line += update
                elif overlap and \
                        STATE.current_line - STATE.top_line < self.height // 2 and \
                        next_line - STATE.top_line > self.height // 2:
                    STATE.top_line = next_line - self.height // 2
            if next_line < self.buffer.height:
                STATE.current_line = next_line
            else:
                STATE.top_line = self.buffer.height - self.height
                STATE.current_line = self.buffer.height - 1

    def scroll_x(self, update):
        """Scroll horizontally.

        Args:
            update (int or str): the offset specifying the scrolling width.
        """
        # jump to beginning
        if update == 0:
            LOGGER.debug('Jump to first column of viewport.')
            STATE.left_edge = 0
        # jump to end
        elif update == '$':
            LOGGER.debug('Jump to end of viewport.')
            STATE.left_edge = self.buffer.width - self.width
        else:
            LOGGER.debug('Scroll viewport horizontally by %d columns.', update)
            next_col = STATE.left_edge + update
            # limit column such that no empty columns can appear on left or right
            if 0 <= next_col <= self.buffer.width - self.width:
                STATE.left_edge = next_col

    def wrap(self):
        """Toggles wrapping of the text currently displayed."""
        LOGGER.debug('Wrap command triggered.')
        # first, ensure left_edge is set to 0
        STATE.left_edge = 0
        # then, wrap the buffer
        self.buffer.wrap(self.width)
        self.view()
        # if cursor line is below buffer height, move it one line back up
        if self.buffer.height and STATE.current_line >= self.buffer.height:
            STATE.current_line -= 1

    def get_current_label(self):
        """Returns the label and y position of the currently selected entry."""
        LOGGER.debug('Obtaining current label "under" cursor.')
        cur_y, _ = self.pad.getyx()
        # Two cases are possible: the list and the show mode
        if STATE.mode == Mode.LIST.value:
            # In the list mode, the label can be found in the current line
            # or in one of the previous lines if we are on a wrapped line
            while chr(self.pad.inch(cur_y, 0)) == TextBuffer.INDENT[0]:
                cur_y -= 1
            label = self.pad.instr(cur_y, 0).decode('utf-8').split(' ')[0]
        elif STATE.mode == Mode.SEARCH.value:
            # In the search mode, the same holds but we need to slightly change the label detection.
            while chr(self.pad.inch(cur_y, 0)) in ('[', TextBuffer.INDENT[0]):
                cur_y -= 1
            label = self.pad.instr(cur_y, 0).decode('utf-8').split(' ')[0]
        else:
            # In any other mode, the label can be found in the top statusbar
            label = '-'.join(STATE.topstatus.split('-')[1:]).strip()
            # We also set cur_y to 0 for the select command to find it
            cur_y = 0
        LOGGER.debug('Current label at "%s" is "%s".', str(cur_y), label)
        return label, cur_y

    def update_list(self):
        """Updates the default list view."""
        LOGGER.debug('Re-populating the viewport with the list command.')
        self.buffer.clear()
        labels = ListCommand().execute(STATE.list_args, out=self.buffer)
        labels = labels or []  # convert to empty list if labels is None
        # populate buffer with the list
        if STATE.mode != Mode.LIST.value:
            STATE.current_line = STATE.previous_line
            STATE.mode = Mode.LIST.value
        # reset viewport
        STATE.top_line = 0
        STATE.left_edge = 0
        STATE.inactive_commands = []
        # highlight current selection
        for label in self.tui.selection:
            # Note: the two spaces are explained in the `select()` method.
            # Also: this step may become a performance bottleneck because we replace inside the
            # whole buffer for each selected label!
            self.buffer.replace(range(self.buffer.height), label + '  ',
                                config.get_ansi_color('selection') + label + '\x1b[0m  ')
        # display buffer in viewport
        self.view(ansi_map=self.tui.ANSI_MAP)
        # update top statusbar
        STATE.topstatus = "CoBib v{} - {} Entries".format(__version__, len(labels))
        self.tui.statusbar(self.tui.topbar, STATE.topstatus)
        # if cursor position is out-of-view (due to e.g. top-line reset in Show command), reset the
        # top-line such that the current line becomes height again
        if STATE.current_line > STATE.top_line + self.height:
            STATE.top_line = min(STATE.current_line, self.buffer.height - self.height)
