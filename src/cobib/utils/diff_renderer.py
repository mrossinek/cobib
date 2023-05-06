"""coBib's diff renderer utility."""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field

from rich.style import Style
from rich.syntax import Syntax
from rich.table import Table


@dataclass
class Side:
    """TODO."""

    name: str
    background: str
    foreground: str


LEFT = Side("a", "#300000", "red")
RIGHT = Side("b", "#002000", "green")


@dataclass
class DiffData:
    """TODO."""

    lines: list[str]

    highlight_lines: set[int] = field(default_factory=set)

    style_ranges: list[tuple[Style, tuple[int, int], tuple[int, int]]] = field(default_factory=list)

    current_block: list[str] = field(default_factory=list)

    current_offset: int = 0

    def _get_cumulative_count(self) -> int:
        """TODO."""
        return sum(len(line) for line in self.lines[: self.current_offset - 1])

    def get_row_col_from_pos(self, position: int) -> tuple[int, int]:
        """TODO."""
        position += self._get_cumulative_count()
        col, row = -1, 0
        cumulative_count = 0
        for line in self.lines:
            cumulative_count += len(line)
            if cumulative_count > position:
                col = position - (cumulative_count - len(line))
                break
            row += 1
        return row + 1, col

    def stylize_matches(self, matches: list[difflib.Match], side: Side) -> None:
        """TODO."""
        pos = 0
        for match in matches:
            row1, col1 = self.get_row_col_from_pos(pos)
            row2, col2 = self.get_row_col_from_pos(getattr(match, side.name))
            pos = getattr(match, side.name) + match.size

            for row in range(row1, row2 + 1 * (match.size > 0)):
                self.highlight_lines.add(row)

                self.style_ranges.insert(
                    0, (Style(bgcolor=side.background), (row, 0), (row + 1, 0))
                )

            self.style_ranges.append((Style(bgcolor=side.foreground), (row1, col1), (row2, col2)))

    def render(self, lexer: str = "text") -> Syntax:
        """TODO."""
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
    """TODO."""

    _unified_diff_header = re.compile(r"@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@")
    """TODO."""

    def __init__(self, left: str, right: str) -> None:
        """TODO."""
        self.left = DiffData(left.splitlines(keepends=True))
        self.right = DiffData(right.splitlines(keepends=True))

    def render(self, lexer: str = "text") -> Table:
        """TODO."""
        table = Table(box=None, show_header=False)
        table.add_row(self.left.render(lexer), self.right.render(lexer))
        return table

    def compute(self) -> None:
        """TODO."""
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

    def _sequence_matcher(self) -> None:
        """TODO."""
        matches = difflib.SequenceMatcher(
            a="".join(self.left.current_block),
            b="".join(self.right.current_block),
        ).get_matching_blocks()

        self.left.stylize_matches(matches, LEFT)
        self.right.stylize_matches(matches, RIGHT)

        self.left.current_block = []
        self.right.current_block = []

    def _parse_unified_diff_header(self, line: str) -> None:
        """TODO."""
        result = Differ._unified_diff_header.search(line)

        if result is not None:
            offset_left, _, offset_right, _ = result.groups()

            self.left.current_offset = int(offset_left)
            self.right.current_offset = int(offset_right)
