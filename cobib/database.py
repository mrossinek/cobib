"""Database handler module."""

from collections import OrderedDict
from pathlib import Path
import os
import sys

from cobib.config import CONFIG
from cobib.parser import Entry


def read_database(fresh=False):
    """Reads the database file.

    The YAML database file pointed to by the configuration file is read in and parsed. The data is
    stored as an OrderedDict in the global configuration object.

    Args:
        fresh (bool, optional): Forcefully reloads the bibliographic data.
    """
    if fresh:
        # delete data currently in memory
        del CONFIG.config['BIB_DATA']
    conf_database = CONFIG.config['DATABASE']
    file = os.path.expanduser(conf_database['file'])
    try:
        CONFIG.config['BIB_DATA'] = Entry.from_yaml(Path(file))
    except AttributeError:
        CONFIG.config['BIB_DATA'] = OrderedDict()
    except FileNotFoundError:
        print(f"The database file {file} does not exist! Please run `cobib init`!", file=sys.stderr)
        sys.exit(1)


def write_database(entries):
    """Writes to the database file.

    Appends the bibliographic data of the provided entries to the database file. If a label already
    exists in the database, the corresponding entry is skipped.

    Args:
        entries (list[Entry]): list of new bibliography entries
    """
    if 'BIB_DATA' not in CONFIG.config.keys():
        # if no data in memory, read the database file (the case when using the CLI)
        read_database()
    new_lines = []
    for label, entry in entries.items():
        if label in CONFIG.config['BIB_DATA'].keys():
            print("Error: label '{}' already exists!".format(label))
            continue
        string = entry.to_yaml()
        reduced = '\n'.join(string.splitlines())
        new_lines.append(reduced)

    if new_lines:
        conf_database = CONFIG.config['DATABASE']
        file = os.path.expanduser(conf_database['file'])
        # append new lines to the database file
        with open(file, 'a') as bib:
            for line in new_lines:
                bib.write(line+'\n')
        # update bibliography data
        read_database(fresh=True)
