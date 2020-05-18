"""Database handler module"""

from collections import OrderedDict
from pathlib import Path
import os
import sys

from cobib.config import CONFIG
from cobib.parser import Entry


def read_database(fresh=False):
    """Read database file"""
    if fresh:
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
    """Write database file"""
    if 'BIB_DATA' not in CONFIG.config.keys():
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
        with open(file, 'a') as bib:
            for line in new_lines:
                bib.write(line+'\n')
        # update bibliography data
        read_database(fresh=True)
