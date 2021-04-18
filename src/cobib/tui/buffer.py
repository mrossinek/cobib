"""coBib's auxiliary in-/output buffers.

coBib's TUI manages in- and output through auxiliary buffers.
These take care of everything from simple text buffering to highlighting conversion from ANSI
color codes to `curses` color pairs.
"""

from __future__ import annotations

import curses
import logging
import re
import textwrap
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple, Union

LOGGER = logging.getLogger(__name__)

if TYPE_CHECKING:
    import cobib.tui


class TextBuffer:
    """An auxiliary output-buffer.

    This class implements all necessary methods to make it a suitable argument in a scenario like:
    ```python
    print("some text", file=TextBuffer())
    ```

    This means, it can buffer text which will be subsequently displayed in a `curses.pad`.
    To this extent this class also implements an ANSI color code to `curses` color pair conversion
    as part of its `view` method.

    Finally, the `popup` method can be leveraged by `cobib.tui.tui.TUI` for an easy way to display
    an overlaid frame within the TUI.
    """

    INDENT: str = "↪"
    """The string to be used for line continuation."""

    def __init__(self) -> None:
        """Initializes the TextBuffer object."""
        self.lines: List[str] = []
        """The actual text buffer."""
        self.height: int = 0
        """The height of the buffer contents (i.e. the number of lines)."""
        self.width: int = 0
        """The width of the buffer contents (i.e. the maximum line width)."""
        self.wrapped: bool = False
        """Whether the buffer contents have been wrappped to a certain width."""
        self.ansi_map: Optional[Dict[str, int]] = None
        """An optional dictionary mapping ANSI color codes to `curses` color pair indices."""

    def write(self, string: str) -> None:
        """Writes a non-empty string into the buffer.

        Args:
            string: the string to append to the buffer.
        """
        if string.strip():
            # only handle non-empty strings
            LOGGER.debug("Appending string to text buffer: %s", string)
            self.lines.append(string)
            self.height = len(self.lines)
            self.width = max(self.width, len(string))

    def replace(self, lines: Union[int, range, List[int]], old_str: str, new_str: str) -> None:
        """Replaces the old string with the new in the given lines.

        Args:
            lines: index or indices on which lines to do the replacement.
            old_str: old string to be replaced.
            new_str: new string to be inserted.
        """
        LOGGER.debug('Replacing "%s" with "%s" in lines %s', old_str, new_str, lines)
        if isinstance(lines, int):
            lines = [lines]
        for idx in lines:
            self.lines[idx] = re.sub(old_str, new_str, self.lines[idx])

    def flush(self) -> None:
        """Compatibility method. It has no effect."""

    def close(self) -> None:
        """Compatibility method. It has no effect."""

    def clear(self) -> None:
        """Clears the buffer."""
        LOGGER.debug("Clearing text buffer.")
        self.lines = []
        self.height = 0
        self.width = 0
        self.wrapped = False

    def split(self) -> None:
        """Splits the buffer lines at literal line breaks."""
        copy = self.lines.copy()
        self.lines = []
        self.width = 0
        for line in copy:
            for string in line.split("\n"):
                self.lines.append(string)
                self.width = max(self.width, len(string))
        self.height = len(self.lines)

    def wrap(self, width: int, label_column: bool = True) -> None:
        """Wraps the text in the buffer at a given width.

        If `label_column` is set to `True` (the default), this method will determine the width of
        the column containing the entry labels.
        This is done by attempting to split each line around two consecutive spaces ("␣␣") and
        determining the width of the first field.
        This assumes that the `cobib.commands.list.ListCommand` *always* outputs the entry labels as
        the first column.
        This label column length is then used on indented lines to achieve properly wrapped table
        columns in the output.

        On the other hand, if this value is set to `False`, a default initial column width of `2` is
        used.

        Args:
            width: maximum text width for each line in the buffer.
            label_column: whether to determine a label column width.
        """
        copy = self.lines.copy()
        self.lines = []
        self.width = 0
        if self.wrapped:
            LOGGER.debug("Unwrapping text buffer.")
            for line in copy:
                # unwrap instead
                if line.startswith(TextBuffer.INDENT):
                    # Note: insert single space when joining lines and strip INDENT symbol
                    self.lines[-1] += " " + line[1:].strip()
                else:
                    self.lines.append(line)
                self.width = max(self.width, len(self.lines[-1]))
        else:
            LOGGER.debug("Wrapping text buffer.")
            if label_column:
                # first, determine width of label column
                label_len = 0
                for line in copy:
                    label = line.split("  ")[0]
                    label_len = max(len(label) + 1, label_len)
                    if label_len > width:
                        LOGGER.debug(
                            "Label column width would exceed actual width. Continuing"
                            "without a label column."
                        )
                        label_len = 1
                        break
                LOGGER.debug("Label column width determined to be %d", label_len)
            else:
                label_len = 2
                LOGGER.debug("Usig default label column width %d", label_len)
            for line in copy:
                # then wrap lines with subsequent indents matched to first column width
                for string in textwrap.wrap(
                    line, width=width - 1, subsequent_indent=TextBuffer.INDENT + " " * label_len
                ):
                    self.lines.append(string)
                self.width = width
        self.height = len(self.lines)
        self.wrapped = not self.wrapped

    # pylint: disable=too-many-arguments
    def view(
        self,
        pad: "curses.window",  # type: ignore
        smaxrow: int,
        smaxcol: int,
        pminrow: int = 0,
        pmincol: int = 0,
        sminrow: int = 1,
        smincol: int = 0,
        ansi_map: Optional[Dict[str, int]] = None,
        background: Optional[int] = None,
        box: bool = False,
    ) -> None:
        """Views the buffer contents in the provided `curses.window`.

        Args:
            pad: a re-sizable curses window (aka a pad).
            smaxrow: the available height for the pad.
            smaxcol: the available width for the pad.
            pminrow: the upper display position in the pad.
            pmincol: the left display position in the pad.
            sminrow: the upper display position of the pad.
            smincol: the left display position of the pad.
            ansi_map: optional, dictionary mapping ANSI codes to curses color pairs.
            background: the curses color pair number with which to highlight the window.
            box: whether to print a frame around the window.
        """
        # a regex to detect ANSI color codes
        ansi_regex = re.compile(r"(\x1b\[(\d+)[;]*(\d+)*m)")
        if ansi_map:
            LOGGER.debug("Interpreting ANSI color codes on the fly.")
            self.ansi_map = ansi_map
        # first clear pad
        LOGGER.debug("Clearing curses pad.")
        pad.erase()
        LOGGER.debug("Pad view parameters:")
        LOGGER.debug((pminrow, pmincol, sminrow, smincol, smaxrow, smaxcol))
        pad.refresh(pminrow, pmincol, sminrow, smincol, smaxrow, smaxcol)
        # then resize
        LOGGER.debug("Adjusting pad size.")
        # NOTE The +1 added onto the height accounts for some weird offset in the curses pad.
        pad.resize(self.height + (2 if box else 1), max(self.width, smaxcol + (0 if box else 1)))
        # and populate
        for row, line in enumerate(self.lines):
            start, end, color = -1, -1, -1
            # This list will store the spanned regions for each ANSI color pair.
            # Its entries will be (curses color pair number, start, end).
            color_spans: List[Tuple[int, int, int]] = []
            if self.ansi_map:
                LOGGER.debug("Applying ANSI color map.")
                # The index below is used to keep track of the oldest (i.e. lowest in index) color
                # span which has not been closed yet. This means that we work with the assumption
                # that ANSI color codes always occur in pairs (even though a single \x1b[0m sequence
                # could terminate multiple open spans).
                lowest_incomplete_color_span = 0

                # In order to correctly trim the old line while piecing together the new one we need
                # to keep track of the previously encountered end position.
                prev_end = 0
                new_line = ""

                # iterate over all ANSI color code matches on the current line
                for match in ansi_regex.finditer(line):
                    # add everything preceding the current match to the new line
                    new_line += line[: match.start() - prev_end]
                    # trim the current line from everything in front of the match and itself
                    line = line[match.end() - prev_end :]
                    # store the current end position to use as an offset on the next match
                    prev_end = match.end()

                    # handle ANSI color code
                    if match[0] == "\x1b[0m":
                        # a closing sequence completes the lowest incomplete color span
                        # Note: as mentioned above, we work under the assumption that all ANSI color
                        # codes occur in pairs!
                        color_spans[lowest_incomplete_color_span] = (
                            color_spans[lowest_incomplete_color_span][0],
                            color_spans[lowest_incomplete_color_span][1],
                            len(new_line),
                        )
                        lowest_incomplete_color_span += 1
                    else:
                        # else we create a new color span
                        color_spans.append((self.ansi_map[match[0]], len(new_line), -1))

                # anything left from the original line needs to be added to the new one
                new_line += line
                # and finally the new line replaces the original one
                line = new_line

            pad.addstr(row + (1 if box else 0), (1 if box else 0), line)
            for color, start, end in sorted(color_spans):
                pad.chgat(row, start, end - start, curses.color_pair(color))
        # apply decorations
        if background is not None:
            # setting background color
            pad.bkgd(" ", curses.color_pair(background + 1))
        if box:
            pad.box()
        LOGGER.debug("Viewing curses pad.")
        pad.refresh(pminrow, pmincol, sminrow, smincol, smaxrow, smaxcol)

    def popup(self, tui: cobib.tui.TUI, background: Optional[int] = None) -> None:
        """Displays the buffer in a popup window.

        Args:
            tui: the TUI instance in which the popup is displayed.
            background: the curses color pair number with which to highlight the window.
        """
        LOGGER.debug("Create popup window.")
        popup_win = curses.newpad(self.height + 2, tui.width)
        # computing height offset
        height_offset = tui.height - self.height - 4
        # wrap buffer prior to viewing
        self.wrap(tui.width, label_column=False)
        # view popup window
        self.view(
            popup_win,
            min(height_offset + self.height + 2, tui.height - 1),
            tui.width,
            sminrow=height_offset,
            background=background,
            box=True,
        )

        key = 0
        # loop until quit by user
        while key not in (27, ord("q")):  # exit on ESC
            if key != 0:
                # do not print warning on initial run (key == 0)
                tui.prompt_print('To quit the popup window, press "q".')
            key = tui.prompt.getch()

        # close popup window
        popup_win.clear()
        tui.resize_handler(None, None)


class InputBuffer:
    """An auxiliary output-buffer.

    This class implements all necessary methods to make it a suitable replacement for `sys.stdin`.
    This is used when a command-line implementation of a command queries a user for input on `stdin`
    and allows the TUI to react accordingly.
    """

    def __init__(self, buffer: TextBuffer, tui: cobib.tui.TUI) -> None:
        """Initializes the InputBuffer object.

        Args:
            buffer: the current `sys.stdout` replacement.
            tui: the current TUI instance.
        """
        self.buffer = buffer
        """The `TextBuffer` replaces `sys.stdout`."""
        self.tui = tui
        """The `cobib.tui.tui.TUI` instance whose `cobib.tui.tui.TUI.prompt_handler` to use."""

    def readline(self) -> str:
        """Reads an input from the user mimicking `sys.stdin`."""
        self.buffer.split()
        LOGGER.debug("Create popup window.")
        popup_win = curses.newpad(self.buffer.height + 2, self.tui.width)
        # view popup window
        height_offset = self.tui.height - self.buffer.height - 4
        # wrap buffer prior to viewing
        self.buffer.wrap(self.tui.width, label_column=False)
        # view buffer
        self.buffer.view(
            popup_win,
            height_offset + self.buffer.height + 2,
            self.tui.width,
            sminrow=height_offset,
            box=True,
        )

        user_input: str = self.tui.prompt_handler(None, symbol="> ")

        # close popup window
        popup_win.clear()
        self.buffer.clear()
        self.tui.resize_handler(None, None)

        return user_input
