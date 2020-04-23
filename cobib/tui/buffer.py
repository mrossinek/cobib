"""CoBib auxiliary TextBuffer"""

import textwrap


class TextBuffer:
    """TextBuffer class used as an auxiliary variable to redirect output into.

    This buffer class implements a `write` method which allows it to be used as a drop-in source
    for the `file` argument of the `print()` method. Thereby, its output can be gathered in this
    buffer for further usage (such as printing it into a curses pad).
    """

    INDENT = "↪ "

    def __init__(self):
        self.lines = []
        self.height = 0
        self.width = 0
        self.wrapped = False

    def write(self, string):
        """Writes a non-empty string into the buffer."""
        if string.strip():
            # only handle non-empty strings
            self.lines.append(string)
            self.height = len(self.lines)
            self.width = max(self.width, len(string))

    def clear(self):
        """Clears the buffer."""
        self.lines = []
        self.height = 0
        self.width = 0
        self.wrapped = False

    def split(self):
        """Split lines at line breaks."""
        copy = self.lines.copy()
        self.lines = []
        self.width = 0
        for line in copy:
            for string in line.split('\n'):
                self.lines.append(string)
                self.width = max(self.width, len(string))
        self.height = len(self.lines)

    def wrap(self, width):
        """Wrap text in buffer to given width."""
        copy = self.lines.copy()
        self.lines = []
        self.width = 0
        for line in copy:
            if self.wrapped:
                # unwrap instead
                if line.startswith(TextBuffer.INDENT):
                    self.lines[-1] += line[1:]
                else:
                    self.lines.append(line)
                self.width = max(self.width, len(self.lines[-1]))
            else:
                for string in textwrap.wrap(line, width=width-1,
                                            subsequent_indent=TextBuffer.INDENT):
                    self.lines.append(string)
                self.width = width
        self.height = len(self.lines)
        self.wrapped = not self.wrapped

    def view(self, pad, visible_height, visible_width):
        """View buffer in provided curses pad."""
        # first clear pad
        pad.erase()
        pad.refresh(0, 0, 1, 0, visible_height, visible_width)
        # then resize
        # NOTE The +1 added onto the height accounts for some weird offset in the curses pad.
        pad.resize(self.height+1, max(self.width, visible_width+1))
        # and populate
        for row, line in enumerate(self.lines):
            pad.addstr(row, 0, line)
        pad.refresh(0, 0, 1, 0, visible_height, visible_width)
