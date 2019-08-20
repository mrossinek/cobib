#!/usr/bin/python3
# IMPORTS
from bs4 import BeautifulSoup
from subprocess import Popen
from zipfile import ZipFile
import argparse
import configparser
import inspect
import os
import pdftotext
import pybtex.database
import re
import requests
import sys
import tabulate
import tempfile


# GLOBAL VARIABLES
# API and HEADER settings according to this resource
# https://crosscite.org/docs.html
DOI_URL = "https://doi.org/"
DOI_HEADER = {'Accept': "application/x-bibtex"}
# arXiv url according to docs from here https://arxiv.org/help/oa
ARXIV_URL = "https://export.arxiv.org/oai2?verb=GetRecord&metadataPrefix=arXiv&identifier=oai:arXiv.org:"
# DOI regex used for matching DOIs
DOI_REGEX = r'(10\.[0-9a-zA-Z]+\/(?:(?!["&\'])\S)+)\b'
# biblatex default types and required values taken from their docs
# https://ctan.org/pkg/biblatex
BIBTEX_TYPES = {
    'article': ['author', 'title', 'journal', 'year'],
    'book': ['author', 'title', 'year'],
    'collection': ['editor', 'title', 'year'],
    'proceedings': ['title', 'year'],
    'report': ['author', 'title', 'type', 'institution', 'year'],
    'thesis': ['author', 'title', 'type', 'institution', 'year'],
    'unpublished': ['author', 'title', 'year']
    }
# global config
# the default configuration file will be loaded from ~/.config/crema/config.ini
CONFIG = configparser.ConfigParser()


# ARGUMENT FUNCTIONS
def init_(args):
    """
    Initializes the yaml database file at the configured location.
    """
    conf_database = dict(CONFIG['DATABASE'])
    file = os.path.expanduser(conf_database['file'])
    with open(file, 'w') as f:
        f.write('entries:')
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
    # for row in cursor:
    #     parser.add_argument('++'+row[1], type=str, action='append',
    #                         help="include elements with matching "+row[1])
    #     parser.add_argument('--'+row[1], type=str, action='append',
    #                         help="exclude elements with matching "+row[1])
    largs = parser.parse_args(args)
    labels = []
    table = []
    for key, entry in bib_data.entries.items():
        labels.append(key)
        table.append([key, entry.fields['title']])
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
        entry = bib_data.entries[largs.label]
        entry_str = pybtex.database.BibliographyData(entries={largs.label: entry}).to_string(bib_format='bibtex')
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
        entry = bib_data.entries[largs.label]
        if 'file' not in entry.fields.keys() or entry.fields['file'] is None:
            print("Error: There is no file associated with this entry.")
            sys.exit(1)
        Popen(["xdg-open", entry.fields['file']], stdin=None, stdout=None, stderr=None, close_fds=True, shell=False)
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
    # group_add.add_argument("-a", "--arxiv", type=str,
    #                        help="arXiv ID of the new references")
    group_add.add_argument("-b", "--bibtex", type=argparse.FileType('r'),
                           help="BibTeX bibliographic data")
    # group_add.add_argument("-d", "--doi", type=str,
    #                        help="DOI of the new references")
    # group_add.add_argument("-p", "--pdf", type=argparse.FileType('rb'),
    #                        help="PDFs files to be added")
    parser.add_argument("tags", nargs=argparse.REMAINDER)
    if (len(args) == 0):
        parser.print_usage(sys.stderr)
        sys.exit(1)
    largs = parser.parse_args(args)

    bib_data = _read_database()

    if largs.bibtex is not None:
        new_data = pybtex.database.parse_file(largs.bibtex)
        new_entries = []
        for key, entry in new_data.entries.items():
            if key in bib_data.entries.keys():
                print("Error: key '{}' already exists!".format(key))
                continue
            string = pybtex.database.BibliographyData(entries={key: entry}).to_string(bib_format='yaml')
            reduced = '\n'.join(string.splitlines()[1:])
            new_entries.append(reduced)
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
    indent_level_threshold = -1
    with open(file, 'w') as bib:
        for line in lines:
            if largs.label in line:
                indent_level_threshold = len(line) - len(line.strip())
                entry_to_be_removed = True
                continue
            indent_level = len(line) - len(line.strip())
            if indent_level <= indent_level_threshold:
                entry_to_be_removed = False
            if not entry_to_be_removed:
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
        entry = bib_data.entries[largs.label]
        prev = pybtex.database.BibliographyData(entries={largs.label: entry}).to_string(bib_format='yaml')
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
    indent_level_threshold = -1
    with open(file, 'w') as bib:
        for line in lines:
            if largs.label in line:
                indent_level_threshold = len(line) - len(line.strip())
                entry_to_be_replaced = True
                continue
            indent_level = len(line) - len(line.strip())
            if indent_level <= indent_level_threshold:
                entry_to_be_replaced = False
                bib.writelines(next)
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
            entry = bib_data.entries[label]
            if largs.bibtex is not None:
                entry_str = pybtex.database.BibliographyData(entries={label: entry}).to_string(bib_format='bibtex')
                largs.bibtex.write(entry_str)
            if largs.zip is not None:
                if 'file' in entry.fields.keys() and entry.fields['file'] is not None:
                    largs.zip.write(entry.fields['file'], label+'.pdf')
    except KeyError:
        print("Error: No entry with the label '{}' could be found.".format(largs.label))
    return


# HELPER FUNCTIONS
def _read_database():
    conf_database = dict(CONFIG['DATABASE'])
    file = os.path.expanduser(conf_database['file'])
    try:
        bib_data = pybtex.database.parse_file(file, bib_format='yaml')
    except AttributeError:
        bib_data = pybtex.database.BibliographyData()
    return bib_data


def _write_database(entries):
    conf_database = dict(CONFIG['DATABASE'])
    file = os.path.expanduser(conf_database['file'])
    with open(file, 'a') as bib:
        for entry in entries:
            bib.write('\n'+entry)
    return


# MAIN
def main():
    subcommands = []
    for key, value in globals().items():
        if inspect.isfunction(value) and 'args' in inspect.signature(value).parameters:
            subcommands.append(value.__name__[:-1])
    parser = argparse.ArgumentParser(description="Process input arguments.")
    parser.add_argument("-c", "--config", type=argparse.FileType('r'),
                        help="Alternative config file")
    parser.add_argument('command', help="subcommand to be called",
                        choices=subcommands)
    parser.add_argument('args', nargs=argparse.REMAINDER)

    if (len(sys.argv) == 1):
        parser.print_usage(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    if args.config is not None:
        CONFIG.read(args.config.name)
    else:
        CONFIG.read(os.path.expanduser('~/.config/crema/config.ini'))

    globals()[args.command+'_'](args.args)


if __name__ == '__main__':
    main()
