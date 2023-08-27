"""coBib's Parser interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import cobib.database


class Parser(ABC):
    """The Parser interface.

    This interface should be implemented by all concrete parser implementations.
    If the `dump` functionality does not make sense in a specific context, an error should be logged
    but the function should return normally otherwise.
    """

    name = "base"
    """The parsers `name` is used to register itself as an input argument to the
    `cobib.commands.add.AddCommand`."""

    @abstractmethod
    def parse(self, string: str) -> dict[str, cobib.database.Entry]:
        """Creates a new Entry from the given string.

        This method can add a URL in the special field `_download` of the
        `cobib.database.Entry.data` dictionary pointing to a file which will be downloaded and
        stored as the associated file of the parsed entry.

        Args:
            string: the input of the concrete parser type. Depending on the concrete implementation,
                this can be the actual raw data input or a path to a file containing the raw data.
                It is the responsibility of the concrete implementation to deal with all of these
                scenarios.

        Returns:
            An `OrderedDict` mapping labels to `cobib.database.Entry` instances generated from the
            raw data.
        """

    @abstractmethod
    def dump(self, entry: cobib.database.Entry) -> str | None:
        """Dumps an entry in the parsers format.

        Args:
            entry: the `cobib.database.Entry` to be dumped.

        Returns:
            A `str`-representation of the entry in the concrete parsers format. If the conversion
            does not make sense for a certain concrete implementation, `None` is returned and an
            error should be logged. This function should *not* raise an actual error or exit
            prematurely.
        """
