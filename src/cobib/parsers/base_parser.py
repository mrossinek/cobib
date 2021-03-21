"""coBib Parser interface."""

import logging
from abc import ABC, abstractmethod

LOGGER = logging.getLogger(__name__)


class Parser(ABC):
    """The Parser interface."""

    name = "base"

    @abstractmethod
    def parse(self, string):
        """Creates a new Entry from the given string."""

    @abstractmethod
    def dump(self, entry):
        """Dumps an entry in the parsers format."""
