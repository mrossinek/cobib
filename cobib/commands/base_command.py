"""CoBib Command interface"""

import os
from abc import ABC, abstractmethod
from collections import OrderedDict
from pathlib import Path

from cobib.config import CONFIG
from cobib.parser import Entry


class Command(ABC):  # pylint: disable=too-few-public-methods
    """
    The Command interface declares a method for command execution and some helper methods.
    """

    @abstractmethod
    def execute(self, args):
        """Command execution"""

    # HELPER FUNCTIONS
    @staticmethod
    def _read_database():
        conf_database = dict(CONFIG['DATABASE'])
        file = os.path.expanduser(conf_database['file'])
        try:
            bib_data = Entry.from_yaml(Path(file))
        except AttributeError:
            bib_data = OrderedDict()
        return bib_data

    @staticmethod
    def _write_database(entries):
        bib_data = Command._read_database()
        new_lines = []
        for label, entry in entries.items():
            if label in bib_data.keys():
                print("Error: label '{}' already exists!".format(label))
                continue
            string = entry.to_yaml()
            reduced = '\n'.join(string.splitlines())
            new_lines.append(reduced)

        conf_database = dict(CONFIG['DATABASE'])
        file = os.path.expanduser(conf_database['file'])
        with open(file, 'a') as bib:
            for line in new_lines:
                bib.write(line+'\n')
