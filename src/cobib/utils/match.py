"""coBib's search result match object.

This simple data container combines the text from a search result with span(s) indicating the
matching position(s).
"""

from typing import NamedTuple

from rich.text import Text

from cobib.config import config


class Span(NamedTuple):
    """A span to indicate a substring positionally within a larger one."""

    start: int
    """The start of the spanned substring."""

    end: int
    """The end of the spanned substring."""


class Match(NamedTuple):
    """A match object combining a text and matching substring(s)."""

    text: str
    """The text of a search result."""

    spans: list[Span]
    """The spans where a matching substring was found."""

    source: str
    """The source of this match."""

    def stylize(self) -> Text:
        """Return a stylized `rich.Text` of this match."""
        text = Text(self.text)
        for span in self.spans:
            text.stylize(
                config.theme.search.query,
                span.start,
                span.end,
            )
        return text
