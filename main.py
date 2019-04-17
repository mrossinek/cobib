#!/usr/bin/python3
import argparse
import configparser
import pdftotext
import re
import requests
import sqlite3
import sys

HEADER = {'Accept': "application/x-bibtex"}
API_URL = "https://doi.org/"
DOI_REGEX = r'(10\.[0-9a-zA-Z]+\/(?:(?!["&\'])\S)+)\b'
TYPES = {
        'article': ['author', 'title', 'journal', 'year'],
        'book': ['author', 'title', 'year'],
        'collection': ['editor', 'title', 'year'],
        'proceedings': ['title', 'year'],
        'report': ['author', 'title', 'type', 'institution', 'year'],
        'thesis': ['author', 'title', 'type', 'institution', 'year'],
        'unpublished': ['author', 'title', 'year']
        }
KEYS = {
        'doi':      "primary key not null",
        'type':     "not null",
        'label':    "not null",
        'file':     "",
        'tags':     "",
        'abstract': ""
        }

config = configparser.ConfigParser()
config.read('config.ini')


def init(args):
    conn = sqlite3.connect("test.db")
    cmd = "create table literature(\n"
    for type, keys in TYPES.items():
        for key in keys:
            if key not in KEYS.keys():
                KEYS[key] = ""
    for key, params in KEYS.items():
        cmd += key+' text '+params+',\n'
    cmd = cmd[:-2]+'\n)'
    conn.execute(cmd)
    conn.commit()


def list(args):
    conn = sqlite3.connect("test.db")
    cursor = conn.execute("SELECT rowid, doi, label from literature")
    for row in cursor:
        print(row)


def add(args):
    dois = []
    def flatten(l): return [item for sublist in l for item in sublist]
    if args.pdf is not None:
        def most_common(lst: list): return max(set(matches), key=matches.count)
        for pdf in args.pdf:
            pdf = pdftotext.PDF(pdf)
            text = "".join(pdf)
            matches = re.findall(DOI_REGEX, text)
            dois.append(most_common(matches))
    if args.doi is not None:
        dois.extend(args.doi)
    for doi in dois:
        assert(re.match(DOI_REGEX, doi))
        page = requests.get(API_URL+doi, headers=HEADER)
        parse_bibtex(page.text)


def parse_bibtex(str):
    # load database info
    conn = sqlite3.connect("test.db")
    cursor = conn.execute("PRAGMA table_info(literature)")
    table_keys = [row[1] for row in cursor]

    # extract information from bibtex
    lines = str.split('\n')
    type = re.findall(r'^@([a-zA-Z]*){', lines[0])[0]
    label = re.findall(r'{(\w*),$', lines[0])[0]
    keys = 'type,label'
    values = "'{}','{}'".format(type, label)
    for line in lines[1:-1]:
        key, value = line.split('=')
        key = key.strip()
        if key not in table_keys:
            cursor.execute("ALTER TABLE literature ADD COLUMN "+key+" text")
            cursor = conn.execute("PRAGMA table_info(literature)")
            table_keys = [row[1] for row in cursor]
        value = value.strip(' ,{}')
        keys = keys+','+key
        values = "{},'{}'".format(values, value)
    cmd = "INSERT INTO literature ("+keys+") VALUES ("+values+")"
    cursor.execute(cmd)
    conn.commit()
    conn.close()


def main():
    parser = argparse.ArgumentParser(description="Process input arguments.")
    subparsers = parser.add_subparsers(help="sub-command help")
    parser_init = subparsers.add_parser("init", help="initialize the database")
    parser_init.set_defaults(func=init)
    parser_list = subparsers.add_parser("list", help="list entries from the database")
    parser_list.set_defaults(func=list)
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
