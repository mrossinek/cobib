"""CoBib Command interface"""

import argparse
import os
import sys
from abc import ABC, abstractmethod
from collections import OrderedDict
from pathlib import Path

from cobib.config import CONFIG
from cobib.parser import Entry


class Command(ABC):
    """
    The Command interface declares a method for command execution and some helper methods.
    """

    @abstractmethod
    def execute(self, args, out=sys.stdout):
        """Command execution"""

    @staticmethod
    def tui(tui):
        """TUI command interface"""

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


class ArgumentParser(argparse.ArgumentParser):
    """
    Overwrite ArgumentParser to allow catching any error messages thrown by parse_args.

    Source: https://stackoverflow.com/a/5943381
    """
    def _get_action_from_name(self, name):
        """Given a name, get the Action instance registered with this parser.
        If only it were made available in the ArgumentError object. It is
        passed as it's first argument...
        """
        container = self._actions
        if name is None:
            return None
        for action in container:
            if '/'.join(action.option_strings) == name:
                return action
            if action.metavar == name:
                return action
            if action.dest == name:
                return action
        return None

    def error(self, message):
        exc = sys.exc_info()[1]
        if exc:
            raise exc
        super(ArgumentParser, self).error(message)
