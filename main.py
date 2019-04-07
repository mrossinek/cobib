#!/usr/bin/python3
import argparse
import pdftotext
import json
import re
import requests
import sqlite3

API_URL = "https://api.crossref.org/works/"
DOI_REGEX = r'(10\.[0-9a-zA-Z]+\/(?:(?!["&\'])\S)+)\b'
HEADER = {'user-agent': 'CReMa (https://github.com/mrossinek/crema)/0.1'}
KEYS = ['author', 'title', 'volume', 'issue', 'page', 'published-print', 'DOI', 'publisher', 'ISSN', 'URL']


def init(args):
    conn = sqlite3.connect("test.db")
    conn.execute('''create table literature
                (doi    varchar(255) primary key not null,
                 author text                     not null,
                 title  text                     not null);''')
    conn.commit()


def list(args):
    conn = sqlite3.connect("test.db")
    cursor = conn.execute("SELECT rowid, doi, author, title from literature")
    for row in cursor:
        print(row)


def add(args):
    dois = []
    if args.pdf is not None:
        def most_common(lst: list): return max(set(matches), key=matches.count)
        for pdf in args.pdf:
            pdf = pdftotext.PDF(pdf)
            text = "".join(pdf)
            matches = re.findall(DOI_REGEX, text)
            dois.append(most_common(matches))
    if args.doi is not None:
        dois.extend(args.dois)
    for doi in dois:
        assert(re.match(DOI_REGEX, doi))
        page = requests.get(API_URL+doi, headers=HEADER).json()
        for key in KEYS:
            print(dict(page)['message'][key])


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

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
