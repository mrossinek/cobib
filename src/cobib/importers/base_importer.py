"""coBib's Importer interface."""

from abc import ABC, abstractmethod
from typing import List

from cobib.database import Entry


class Importer(ABC):
    """The Importer interface.

    This interface should be implemented by all concrete importer implementations.
    """

    name = "base"
    """The importers `name` is used to register itself as an input argument to the
    `cobib.commands.import_.ImportCommand`."""

    @abstractmethod
    def fetch(self, args: List[str], skip_download: bool = False) -> List[Entry]:
        """Fetches a list of entries.

        Args:
            args: a sequence of additional arguments used during execution. The available arguments
                depend on the actual importer in use.
            skip_download: whether or not to skip downloading of additional files such as attached
                PDF files or notes.

        Returns:
            A list of entries.
        """
