# IMPORTS

from .parser import Entry

from collections import OrderedDict, defaultdict
from pathlib import Path
from subprocess import Popen
from zipfile import ZipFile
import argparse
import inspect
import os
import sys
import tabulate
import tempfile


# ARGUMENT FUNCTIONS
def init_(args):
    """
    Initializes the yaml database file at the configured location.
    """
    conf_database = dict(CONFIG['DATABASE'])
    file = os.path.expanduser(conf_database['file'])
    open(file, 'w').close()
    return


def list_(args):
    """
    By default, all entries of the database are listed.
    This output will be filterable in the future by providing values for any
    set of table keys.
    """
    if '--' in args:
        args.remove('--')
    parser = argparse.ArgumentParser(prog="list", description="List subcommand parser.",
                                     prefix_chars='+-')
    parser.add_argument('-x', '--or', dest='OR', action='store_true',
                        help="concatenate filters with OR instead of AND")
    bib_data = _read_database()
    unique_keys = set()
    for label, entry in bib_data.items():
        unique_keys.update(entry.data.keys())
    for key in sorted(unique_keys):
        parser.add_argument('++'+key, type=str, action='append',
                            help="include elements with matching "+key)
        parser.add_argument('--'+key, type=str, action='append',
                            help="exclude elements with matching "+key)
    largs = parser.parse_args(args)
    filter = defaultdict(list)
    for f in largs._get_kwargs():
        if f[0] == 'OR' or f[1] is None:
            continue
        if not isinstance(f[1], list):
            f[1] = [f[1]]
        for i in f[1]:
            for index, object in enumerate(sys.argv):
                if i == object:
                    if sys.argv[index-1][0] == '-':
                        filter[tuple([f[0], False])].append(i)
                        break
                    else:
                        filter[tuple([f[0], True])].append(i)
                        break
    labels = []
    table = []
    for label, entry in bib_data.items():
        if entry.matches(filter, largs.OR):
            labels.append(label)
            table.append([label, entry.data['title']])
    print(tabulate.tabulate(table, headers=["Label", "Title"]))
    return labels


def show_(args):
    """
    Prints the details of a selected entry in bibtex format to stdout.
    """
    parser = argparse.ArgumentParser(prog="show", description="Show subcommand parser.")
    parser.add_argument("label", type=str, help="label of the entry")
    if (len(args) == 0):
        parser.print_usage(sys.stderr)
        sys.exit(1)
    largs = parser.parse_args(args)
    bib_data = _read_database()
    try:
        entry = bib_data[largs.label]
        entry_str = entry.to_bibtex()
        print(entry_str)
    except KeyError:
        print("Error: No entry with the label '{}' could be found.".format(largs.label))
    return


def open_(args):
    """
    Opens the associated file of an entry with xdg-open.
    """
    parser = argparse.ArgumentParser(prog="open", description="Open subcommand parser.")
    parser.add_argument("label", type=str, help="label of the entry")
    if (len(args) == 0):
        parser.print_usage(sys.stderr)
        sys.exit(1)
    largs = parser.parse_args(args)
    bib_data = _read_database()
    try:
        entry = bib_data[largs.label]
        if 'file' not in entry.data.keys() or entry.data['file'] is None:
            print("Error: There is no file associated with this entry.")
            sys.exit(1)
        Popen(["xdg-open", entry.data['file']], stdin=None, stdout=None, stderr=None, close_fds=True, shell=False)
    except KeyError:
        print("Error: No entry with the label '{}' could be found.".format(largs.label))
    return


def add_(args):
    """
    Adds new entries to the database.
    """
    parser = argparse.ArgumentParser(prog="add", description="Add subcommand parser.")
    parser.add_argument("-l", "--label", type=str,
                        help="the label for the new database entry")
    parser.add_argument("-f", "--file", type=str,
                        help="a file associated with this entry")
    group_add = parser.add_mutually_exclusive_group()
    group_add.add_argument("-a", "--arxiv", type=str,
                           help="arXiv ID of the new references")
    group_add.add_argument("-b", "--bibtex", type=argparse.FileType('r'),
                           help="BibTeX bibliographic data")
    group_add.add_argument("-d", "--doi", type=str,
                           help="DOI of the new references")
    group_add.add_argument("-p", "--pdf", type=argparse.FileType('rb'),
                           help="PDFs files to be added")
    parser.add_argument("tags", nargs=argparse.REMAINDER)
    if (len(args) == 0):
        parser.print_usage(sys.stderr)
        sys.exit(1)
    largs = parser.parse_args(args)

    new_entries = OrderedDict()

    if largs.bibtex is not None:
        new_entries = Entry.from_bibtex(largs.bibtex)
    if largs.arxiv is not None:
        new_entries = Entry.from_arxiv(largs.arxiv)
    if largs.doi is not None:
        new_entries = Entry.from_doi(largs.doi)
    if largs.pdf is not None:
        new_entries = Entry.from_pdf(largs.pdf)

    if largs.file is not None:
        assert(len(new_entries.values()) == 1)
        for key, value in new_entries.items():
            value.set_file(largs.file)

    if largs.label is not None:
        assert(len(new_entries.values()) == 1)
        for key, value in new_entries.items():
            value.set_label(largs.label)

    if largs.tags is not None:
        assert(len(new_entries.values()) == 1)
        for key, value in new_entries.items():
            value.set_tags(largs.tags)

    _write_database(new_entries)
    return


def remove_(args):
    """
    Removes the entry from the database.
    """
    parser = argparse.ArgumentParser(prog="remove", description="Remove subcommand parser.")
    parser.add_argument("label", type=str, help="label of the entry")
    if (len(args) == 0):
        parser.print_usage(sys.stderr)
        sys.exit(1)
    largs = parser.parse_args(args)
    conf_database = dict(CONFIG['DATABASE'])
    file = os.path.expanduser(conf_database['file'])
    with open(file, 'r') as bib:
        lines = bib.readlines()
    entry_to_be_removed = False
    buffer = []
    for line in lines:
        if line.startswith(largs.label):
            entry_to_be_removed = True
            buffer.pop()
            continue
        if entry_to_be_removed and line.startswith('...'):
            entry_to_be_removed = False
            continue
        if not entry_to_be_removed:
            buffer.append(line)
    with open(file, 'w') as bib:
        for line in buffer:
            bib.write(line)
    return


def edit_(args):
    """
    Opens an existing entry for manual editing.
    """
    parser = argparse.ArgumentParser(prog="edit", description="Edit subcommand parser.")
    parser.add_argument("label", type=str, help="label of the entry")
    if (len(args) == 0):
        parser.print_usage(sys.stderr)
        sys.exit(1)
    largs = parser.parse_args(args)
    bib_data = _read_database()
    try:
        entry = bib_data[largs.label]
        prev = entry.to_yaml()
    except KeyError:
        print("Error: No entry with the label '{}' could be found.".format(largs.label))
    tmp_file = tempfile.NamedTemporaryFile(mode='w+', suffix='.yaml')
    tmp_file.write(prev)
    tmp_file.flush()
    status = os.system(os.environ['EDITOR'] + ' ' + tmp_file.name)
    assert status == 0
    tmp_file.seek(0, 0)
    next = ''.join(tmp_file.readlines()[1:])
    tmp_file.close()
    assert not os.path.exists(tmp_file.name)
    if prev == next:
        return
    conf_database = dict(CONFIG['DATABASE'])
    file = os.path.expanduser(conf_database['file'])
    with open(file, 'r') as bib:
        lines = bib.readlines()
    entry_to_be_replaced = False
    with open(file, 'w') as bib:
        for line in lines:
            if line.startswith(largs.label):
                entry_to_be_replaced = True
                continue
            if entry_to_be_replaced and line.startswith('...'):
                entry_to_be_replaced = False
                bib.writelines(next)
                continue
            if not entry_to_be_replaced:
                bib.write(line)
    return


def export_(args):
    """
    Exports all entries matched by the filter queries (see the list docs).
    Currently supported exporting formats are:
    * bibtex databases
    * zip archives
    """
    parser = argparse.ArgumentParser(prog="export", description="Export subcommand parser.")
    parser.add_argument("-b", "--bibtex", type=argparse.FileType('a'),
                        help="BibTeX output file")
    parser.add_argument("-z", "--zip", type=argparse.FileType('a'),
                        help="zip output file")
    parser.add_argument('list_args', nargs=argparse.REMAINDER)
    if (len(args) == 0):
        parser.print_usage(sys.stderr)
        sys.exit(1)
    largs = parser.parse_args(args)
    bib_data = _read_database()

    if largs.bibtex is None and largs.zip is None:
        return
    if largs.zip is not None:
        largs.zip = ZipFile(largs.zip.name, 'w')
    labels = list_(largs.list_args)

    try:
        for label in labels:
            entry = bib_data[label]
            if largs.bibtex is not None:
                entry_str = entry.to_bibtex()
                largs.bibtex.write(entry_str)
            if largs.zip is not None:
                if 'file' in entry.data.keys() and entry.data['file'] is not None:
                    largs.zip.write(entry.data['file'], label+'.pdf')
    except KeyError:
        print("Error: No entry with the label '{}' could be found.".format(largs.label))
    return


# HELPER FUNCTIONS
def _read_database():
    conf_database = dict(CONFIG['DATABASE'])
    file = os.path.expanduser(conf_database['file'])
    try:
        bib_data = Entry.from_yaml(Path(file))
    except AttributeError:
        bib_data = OrderedDict()
    return bib_data


def _write_database(entries):
    bib_data = _read_database()
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
    return


def _load_config(config):
    global CONFIG
    CONFIG = config


def _list_commands():
    subcommands = []
    for key, value in globals().items():
        if inspect.isfunction(value) and 'args' in inspect.signature(value).parameters:
            subcommands.append(value.__name__[:-1])
    return subcommands
