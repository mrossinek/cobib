"""CoBib auxiliary TextBuffer."""

import curses
import logging
import textwrap

LOGGER = logging.getLogger(__name__)


class TextBuffer:
    """TextBuffer class used as an auxiliary variable to redirect output.

    This buffer class implements a `write` method which allows it to be used as a drop-in source
    for the `file` argument of the `print()` method. Thereby, its output can be gathered in this
    buffer for further usage (such as printing it into a curses pad).
    """

    INDENT = "↪"

    def __init__(self):
        """Initializes the TextBuffer object."""
        self.lines = []
        self.height = 0
        self.width = 0
        self.wrapped = False
        self.ansi_map = None

    def write(self, string):
        """Writes a non-empty string into the buffer.

        Args:
            string (str): the string to append to the buffer.
        """
        if string.strip():
            # only handle non-empty strings
            LOGGER.debug('Appending string to text buffer: %s', string)
            self.lines.append(string)
            self.height = len(self.lines)
            self.width = max(self.width, len(string))

    def replace(self, lines, old_str, new_str):
        """Replaces the old string with the new in the given lines.

        Args:
            lines (int or list): index or indices on which lines to do the replacement.
            old_str (str): old string to be replaced.
            new_str (str): new string to be inserted.
        """
        if isinstance(lines, int):
            lines = [lines]
        for idx in lines:
            self.lines[idx] = self.lines[idx].replace(old_str, new_str)

    def flush(self):
        """Compatibility function."""

    def clear(self):
        """Clears the buffer."""
        LOGGER.debug('Clearing text buffer.')
        self.lines = []
        self.height = 0
        self.width = 0
        self.wrapped = False

    def split(self):
        """Split the lines at literal line breaks."""
        copy = self.lines.copy()
        self.lines = []
        self.width = 0
        for line in copy:
            for string in line.split('\n'):
                if string.strip():
                    self.lines.append(string)
                    self.width = max(self.width, len(string))
        self.height = len(self.lines)

    def wrap(self, width):
        """Wrap text in buffer to given width.

        Args:
            width (int): maximum text width for each line in the buffer.
        """
        copy = self.lines.copy()
        self.lines = []
        self.width = 0
        if self.wrapped:
            LOGGER.debug('Unwrapping text buffer.')
            for line in copy:
                # unwrap instead
                if line.startswith(TextBuffer.INDENT):
                    # Note: insert single space when joining lines and strip INDENT symbol
                    self.lines[-1] += ' ' + line[1:].strip()
                else:
                    self.lines.append(line)
                self.width = max(self.width, len(self.lines[-1]))
        else:
            LOGGER.debug('Wrapping text buffer.')
            # first, determine width of label column
            label_len = 0
            for line in copy:
                label = line.split('  ')[0]
                label_len = max(len(label)+1, label_len)
            LOGGER.debug('Label column width determined to be %d', label_len)
            for line in copy:
                # then wrap lines with subsequent indents matched to first column width
                for string in textwrap.wrap(line, width=width-1,
                                            subsequent_indent=TextBuffer.INDENT + ' ' * label_len):
                    self.lines.append(string)
                self.width = width
        self.height = len(self.lines)
        self.wrapped = not self.wrapped

    def view(self, pad, visible_height, visible_width, ansi_map=None):
        """View buffer in provided curses pad.

        Args:
            pad (curses.window): a re-sizable curses window (aka a pad).
            visible_height (int): the available height for the pad.
            visible_width (int): the available width for the pad.
            ansi_map (dict): optional, dictionary mapping ANSI codes to curses color pairs.
        """
        if ansi_map:
            LOGGER.debug('Interpreting ANSI color codes on the fly.')
            self.ansi_map = ansi_map
        # first clear pad
        LOGGER.debug('Clearing curses pad.')
        pad.erase()
        pad.refresh(0, 0, 1, 0, visible_height, visible_width)
        # then resize
        # NOTE The +1 added onto the height accounts for some weird offset in the curses pad.
        LOGGER.debug('Adjusting pad size.')
        pad.resize(self.height+1, max(self.width, visible_width+1))
        # and populate
        for row, line in enumerate(self.lines):
            start, end, color = -1, -1, -1
            if self.ansi_map and line.find('\033[') >= 0:
                LOGGER.debug('Applying ANSI color map.')
                while line.find('\033[0m') >= 0:
                    # remove ANSI color reset codes and update end position
                    end = line.find('\033[0m')
                    line = line.replace('\033[0m', '', 1)
                while line.find('\033[') >= 0:
                    # as long as we can find ANSI color codes, these will be start codes
                    for ansi, col in self.ansi_map.items():
                        if line.find(ansi) >= 0:
                            # by using the maximum of the current color and the found ANSI color we
                            # can ensure that we use the one with the highest priority
                            color = max(col, color)
                            start = line.find(ansi)
                            line = line.replace(ansi, '')
                            end -= len(ansi)
                            break
            pad.addstr(row, 0, line)
            if color >= 0:
                pad.chgat(row, start, end-start, curses.color_pair(color))
        LOGGER.debug('Viewing curses pad.')
        pad.refresh(0, 0, 1, 0, visible_height, visible_width)
