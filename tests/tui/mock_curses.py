"""Mocking utilities for a `curses.window`."""
# pylint: disable=missing-function-docstring

import logging


class MockCursesPad:
    """This class mocks a `curses.window`.

    When testing the `cobib.tui` modules, we need full control over the `curses` objects. Thus,
    this class removes all of the non-essential aspects and logs all method calls.
    """

    def __init__(self, lines=None) -> None:  # type: ignore
        # noqa: D107
        self.logger = logging.getLogger("MockCursesPad")
        self.lines = lines or []
        self.current_pos = [0, 0]
        self.size = (0, 0)
        self.returned_chars = [27]  # Escape

    def erase(self):  # type: ignore
        # noqa: D102
        self.logger.debug("erase")

    def refresh(  # type: ignore
        self, pminrow=None, pmincol=None, sminrow=None, smincol=None, smaxrow=None, smaxcol=None
    ):
        # noqa: D102
        self.logger.debug(
            "refresh: %s %s %s %s %s %s", pminrow, pmincol, sminrow, smincol, smaxrow, smaxcol
        )

    def resize(self, nlines, ncols):  # type: ignore
        # noqa: D102
        self.logger.debug("resize: %s %s", nlines, ncols)
        self.size = (nlines, ncols)

    def mvwin(self, new_y, new_x):  # type: ignore
        # noqa: D102
        self.logger.debug("mvwin: %s %s", new_y, new_x)

    def insstr(self, row, col, string):  # type: ignore
        # noqa: D102
        self.logger.debug("insstr: %s %s %s", row, col, string)
        try:
            self.lines[row] = string
        except IndexError:
            self.lines.insert(row, string)

    def addstr(self, row, col, string):  # type: ignore
        # noqa: D102
        self.logger.debug("addstr: %s %s %s", row, col, string)
        try:
            old_string = self.lines[row]
        except IndexError:
            while len(self.lines) <= row:
                self.lines.append("")
            old_string = ""
        new_string = old_string[:col] + string + old_string[col + len(string) :]
        self.lines[row] = new_string
        print(self.lines)

    def addnstr(self, row, col, string, num, attr):  # type: ignore
        # noqa: D102
        self.logger.debug("addnstr: %s %s %s %s %s", row, col, string, num, attr)
        try:
            old_string = self.lines[row]
        except IndexError:
            while len(self.lines) <= row:
                self.lines.append([])
            old_string = ""
        new_string = old_string[:col] + string + old_string[col + len(string) :]
        self.lines[row] = new_string

    def chgat(self, row, col, num, attr):  # type: ignore
        # noqa: D102
        self.logger.debug("chgat: %s %s %s %s", row, col, num, attr)

    def bkgd(self, char, attr):  # type: ignore
        # noqa: D102
        self.logger.debug("bkgd: %s %s", char, attr)

    def box(self):  # type: ignore
        # noqa: D102
        self.logger.debug("box")

    def clear(self):  # type: ignore
        # noqa: D102
        self.logger.debug("clear")

    def getch(self):  # type: ignore
        # noqa: D102
        self.logger.debug("getch")
        return self.returned_chars.pop()

    def inch(self, cur_y, cur_x):  # type: ignore
        # noqa: D102
        self.logger.debug("inch: %s, %s", cur_y, cur_x)
        try:
            return ord(self.lines[cur_y][cur_x])
        except IndexError:
            return -1

    def instr(self, cur_y, cur_x):  # type: ignore
        # noqa: D102
        self.logger.debug("instr: %s, %s", cur_y, cur_x)
        return self.lines[cur_y][cur_x:].encode()

    def getyx(self):  # type: ignore
        # noqa: D102
        self.logger.debug("getyx")
        return tuple(self.current_pos)

    def getmaxyx(self):  # type: ignore
        # noqa: D102
        self.logger.debug("getmaxyx")
        return self.size

    def move(self, new_y, new_x):  # type: ignore
        # noqa: D102
        self.logger.debug("move: %s, %s", new_y, new_x)
        self.current_pos = [new_y, new_x]

    def nodelay(self, flag):  # type: ignore
        # noqa: D102
        self.logger.debug("nodelay: %s", flag)

    def delch(self, row, col):  # type: ignore
        # noqa: D102
        self.logger.debug("delch: %s, %s", row, col)
        line = self.lines[row]
        self.lines[row] = line[:col] + line[col + 1 :]
        self.current_pos[1] -= 1
