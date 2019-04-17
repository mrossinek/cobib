#!/usr/bin/python3
# {{{ IMPORTS
from subprocess import Popen
import argparse
import configparser
import pdftotext
import re
import requests
import sqlite3
import sys
# }}}


# {{{ GLOBAL VARIABLES
# API and HEADER settings according to this resource
# https://crosscite.org/docs.html
API_URL = "https://doi.org/"
HEADER = {'Accept': "application/x-bibtex"}
# DOI regex used for matching DOIs
DOI_REGEX = r'(10\.[0-9a-zA-Z]+\/(?:(?!["&\'])\S)+)\b'
# custom database keys which are not part of the biblatex default keys
# this dict may also hold all those keys that require special parameters
TABLE_KEYS = {
    'doi':      "primary key not null",
    'type':     "not null",
    'label':    "not null",
    'file':     "",
    'tags':     "",
    'abstract': ""
    }
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
# }}}


# {{{ CONFIG
config = configparser.ConfigParser()
config.read('config.ini')
conf_database = dict(config['DATABASE'])
# }}}


# {{{ ARGUMENT FUNCTIONS
def init(args):
    """
    Initializes the sqlite3 database at the configured location.
    A single table is used which is named in the config file.
    The initial columns correspond to all minimally required values of the
    default biblatex types plus the custom keys defined initially.
    All fields are TEXT fields and do not have any special attributes. If an
    entry must not be NULL it should be declared in the TABLE_KEYS dictionary
    with its according parameters.
    """
    conn = sqlite3.connect(conf_database['path'])
    cmd = "create table "+conf_database['table']+"(\n"
    for type, keys in BIBTEX_TYPES.items():
        for key in keys:
            if key not in TABLE_KEYS.keys():
                TABLE_KEYS[key] = ""
    for key, params in TABLE_KEYS.items():
        cmd += key+' text '+params+',\n'
    cmd = cmd[:-2]+'\n)'
    conn.execute(cmd)
    conn.commit()


def list(args):
    """
    Lists all entries in the database.
    """
    conn = sqlite3.connect(conf_database['path'])
    cursor = conn.execute("SELECT rowid, doi, label FROM "+conf_database['table'])
    for row in cursor:
        print(row)


def show(args):
    """
    Prints the details of a selected entry in bibtex format to stdout.
    """
    conn = sqlite3.connect(conf_database['path'])
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("SELECT * FROM "+conf_database['table']+" WHERE rowid = "+str(args.id))
    for row in cursor:
        print(dict_to_bibtex(dict(row)))


def open(args):
    """
    Opens the associated file of an entry with xdg-open.
    """
    conn = sqlite3.connect(conf_database['path'])
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("SELECT * FROM "+conf_database['table']+" WHERE rowid = "+str(args.id))
    for row in cursor:
        entry = dict(row)
        if entry['file'] is None:
            print("Error: There is no file associated with this entry.")
            sys.exit(1)
        Popen(["xdg-open", entry['file']], stdin=None, stdout=None, stderr=None, close_fds=True, shell=False)


def add(args):
    """
    Adds new entries to the database.
    """
    dois = []
    def flatten(l): return [item for sublist in l for item in sublist]
    if args.pdf is not None:
        def most_common(lst: list): return max(set(matches), key=matches.count)
        for pdf in args.pdf:
            pdf_obj = pdftotext.PDF(pdf)
            text = "".join(pdf_obj)
            matches = re.findall(DOI_REGEX, text)
            dois.append((most_common(matches), pdf.name))
    if args.doi is not None:
        dois.extend(args.doi)
    for doi in dois:
        if type(doi) == tuple:
            doi_str = doi[0]
            file = doi[1]
        else:
            doi_str = doi
            file = None
        assert(re.match(DOI_REGEX, doi_str))
        page = requests.get(API_URL+doi_str, headers=HEADER)
        insert_entry(page.text, file)
# }}}


# {{{ HELPER FUNCTIONS
def insert_entry(bibtex: str, pdf: str = None):
    """
    Inserts an entry into the database.
    This function has the following side effects:
    * any missing key columns are inserted into the database
    * if a duplicate entry appears to exist, nothing happens
    """
    # load database info
    conn = sqlite3.connect(conf_database['path'])
    cursor = conn.execute("PRAGMA table_info("+conf_database['table']+")")
    table_keys = [row[1] for row in cursor]

    # extract information from bibtex
    entry = bibtex_to_dict(bibtex)
    if pdf is not None:
        entry['file'] = pdf
    keys = ''
    values = ''
    for key, value in entry.items():
        if key not in table_keys:
            cursor.execute("ALTER TABLE "+conf_database['table']+" ADD COLUMN "+key+" text")
            cursor = conn.execute("PRAGMA table_info("+conf_database['table']+")")
            table_keys = [row[1] for row in cursor]
        keys = "{},{}".format(keys, key)
        values = "{},'{}'".format(values, value)

    keys = keys.strip(',')
    values = values.strip(',')

    # insert into table
    cmd = "INSERT INTO "+conf_database['table']+" ("+keys+") VALUES ("+values+")"
    try:
        cursor.execute(cmd)
        conn.commit()
    except sqlite3.IntegrityError as e:
        print(e)
        print("Error: You already appear to have an identical entry in your database.")
    finally:
        conn.close()


def bibtex_to_dict(bibtex: str):
    """
    Converts a bibtex formatted string into a dictionary of key-value pairs.
    """
    entry = {}
    lines = bibtex.split('\n')
    entry['type'] = re.findall(r'^@([a-zA-Z]*){', lines[0])[0]
    entry['label'] = re.findall(r'{(\w*),$', lines[0])[0]
    for line in lines[1:-1]:
        key, value = line.split('=')
        entry[key.strip()] = value.strip(' ,{}')
    return entry


def dict_to_bibtex(entry: dict):
    """
    Converts a key-value paired dictionary into a bibtex formatted string.
    """
    bibtex = "@"+entry['type']+"{"+entry['label']
    for key in sorted(entry):
        if entry[key] is not None and key not in ['type', 'label']:
            bibtex += "\n\t"+key+" = {"+str(entry[key])+"},"
    bibtex = bibtex.strip(',')+"\n}"
    return bibtex
# }}}


# {{{ MAIN
def main():
    parser = argparse.ArgumentParser(description="Process input arguments.")
    subparsers = parser.add_subparsers(help="sub-command help")
    parser_init = subparsers.add_parser("init", help="initialize the database")
    parser_init.set_defaults(func=init)
    parser_list = subparsers.add_parser("list", help="list entries from the database")
    parser_list.set_defaults(func=list)
    parser_show = subparsers.add_parser("show", help="show an entry from the database")
    parser_show.add_argument("id", type=int, help="row ID of the entry")
    parser_show.set_defaults(func=show)
    parser_open = subparsers.add_parser("open", help="open the file associated with this entry")
    parser_open.add_argument("id", type=int, help="row ID of the entry")
    parser_open.set_defaults(func=open)
    parser_add = subparsers.add_parser("add", help="add help")
    group_add = parser_add.add_mutually_exclusive_group()
    group_add.add_argument("-d", "--doi", type=str, nargs='+',
                           help="DOI of the new references")
    group_add.add_argument("-p", "--pdf", type=argparse.FileType('rb'),
                           nargs='+', help="PDFs files to be added")
    parser_add.set_defaults(func=add)

    if (len(sys.argv) == 1):
        parser.print_usage(sys.stderr)
        sys.exit(1)
    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
# }}}
