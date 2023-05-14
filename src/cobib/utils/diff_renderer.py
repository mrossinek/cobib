"""coBib's diff renderer utility."""

from __future__ import annotations

import difflib
import re
from collections import namedtuple
from dataclasses import dataclass, field

from rich.style import Style
from rich.syntax import Syntax
from rich.table import Table

Coordinate = namedtuple("Coordinate", ["row", "col"])


@dataclass
class Side:
    """A simple dataclass for configuring the different sides of a diff view."""

    name: str
    """The name of the side."""
    background: str
    """What background color to use for highlighted differences on this side."""
    foreground: str
    """What foreground color to use for highlighted differences on this side."""


LEFT = Side("a", "#300000", "red")
"""The configured left side of a diff view."""
RIGHT = Side("b", "#002000", "green")
"""The configured right side of a diff view."""


@dataclass
class DiffData:
    """A simple dataclass for holding the difference data."""

    lines: list[str]
    """The total lines being compared."""

    highlight_lines: set[int] = field(default_factory=set)
    """The indices of the lines to be highlighted because they differ."""

    style_ranges: list[tuple[Style, Coordinate, Coordinate]] = field(default_factory=list)
    """A list of stylized ranges to further highlight differences. This is a list of tuples, each of
    which contains three elements:

    1. the style to be applied to this range
    2. the initial `(row, col)` coordinate
    3. the final `(row, col)` coordinate
    """

    current_block: list[str] = field(default_factory=list)
    """The current list of lines being compared."""

    current_offset: int = 0
    """The current index offset of the lines being compared."""

    def _get_cumulative_count(self) -> int:
        """Returns the cumulative number of characters up to the current offset."""
        return sum(len(line) for line in self.lines[: self.current_offset - 1])

    def get_row_col_from_pos(self, position: int) -> Coordinate:
        """Converts a character position into a `(row, col)` coordinate.

        Args:
            position: the absolute character position.

        Returns:
            The `(row, col)` coordinate.
        """
        position += self._get_cumulative_count()
        col, row = -1, 0
        cumulative_count = 0
        for line in self.lines:
            cumulative_count += len(line)
            if cumulative_count > position:
                col = position - (cumulative_count - len(line))
                break
            row += 1
        return Coordinate(row + 1, col)

    def stylize_matches(self, matches: list[difflib.Match], side: Side) -> None:
        """Processes the provided matches and registers the styles in `self`.

        Args:
            matches: the list of difference matches to be highlighted.
            side: the styling data for a specific side.
        """
        pos = 0
        for match in matches:
            row1, col1 = self.get_row_col_from_pos(pos)
            row2, col2 = self.get_row_col_from_pos(getattr(match, side.name))
            pos = getattr(match, side.name) + match.size

            for row in range(row1, row2 + 1 * (match.size > 0)):
                self.highlight_lines.add(row)

                self.style_ranges.insert(
                    0, (Style(bgcolor=side.background), Coordinate(row, 0), Coordinate(row + 1, 0))
                )

            self.style_ranges.append(
                (Style(bgcolor=side.foreground), Coordinate(row1, col1), Coordinate(row2, col2))
            )

    def render(self, lexer: str = "text") -> Syntax:
        """Renders the difference data as a `rich` renderable.

        Args:
            lexer: the syntax lexing to apply.

        Returns:
            A `rich` renderable.
        """
        syntax = Syntax(
            "".join(self.lines),
            lexer,
            background_color="default",
            highlight_lines=self.highlight_lines,
            line_numbers=True,
            word_wrap=True,
        )

        for style in self.style_ranges:
            syntax.stylize_range(*style)

        return syntax


class Differ:
    """A utility class to compare two strings."""

    _unified_diff_header = re.compile(r"@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@")
    """A regex to detect the headers of a `unified_diff` output."""

    def __init__(self, left: str, right: str) -> None:
        """Initializes a `Differ` instance.

        Args:
            left: the left string.
            right: the right string.
        """
        self.left = DiffData(left.splitlines(keepends=True))
        self.right = DiffData(right.splitlines(keepends=True))

    def _sequence_matcher(self) -> None:
        """A utility method to process the `difflib.SequenceMatcher` results."""
        matches = difflib.SequenceMatcher(
            a="".join(self.left.current_block),
            b="".join(self.right.current_block),
        ).get_matching_blocks()

        self.left.stylize_matches(matches, LEFT)
        self.right.stylize_matches(matches, RIGHT)

        self.left.current_block = []
        self.right.current_block = []

    def _parse_unified_diff_header(self, line: str) -> None:
        """A utility to process a `difflib.unified_diff` header."""
        result = Differ._unified_diff_header.search(line)

        if result is not None:
            offset_left, _, offset_right, _ = result.groups()

            self.left.current_offset = int(offset_left)
            self.right.current_offset = int(offset_right)

    def compute(self) -> None:
        """Computes the difference between the two strings.

        This combines the information gathered from `difflib.unified_diff` and additionally compares
        each block with a `difflib.SequenceMatcher`.
        """
        udiff = difflib.unified_diff(
            self.left.lines,
            self.right.lines,
            n=0,
            lineterm="",
        )

        for line in udiff:
            if line[:2] == "@@":
                self._sequence_matcher()
                self._parse_unified_diff_header(line)

            elif line[:1] == "-" and line != "--- ":
                self.left.current_block.append(line[1:])

            elif line[:1] == "+" and line != "+++ ":
                self.right.current_block.append(line[1:])

        self._sequence_matcher()

    def render(self, lexer: str = "text") -> Table:
        """Renders the compared strings in a side-by-side view.

        Args:
            lexer: the syntax lexing to apply.

        Returns:
            A `rich` renderable.
        """
        table = Table(box=None, show_header=False)
        table.add_row(self.left.render(lexer), self.right.render(lexer))
        return table
