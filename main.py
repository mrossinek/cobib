#!/usr/bin/python3
import argparse
import configparser
import pdftotext
import json
import re
import requests
import sqlite3
import sys

API_URL = "https://api.crossref.org/works/"
DOI_REGEX = r'(10\.[0-9a-zA-Z]+\/(?:(?!["&\'])\S)+)\b'
KEYS = {
        'doi':          "varchar(255) primary key not null",
        'type':         "varchar(255) not null",
        'author':       "text",
        'editor':       "text",
        'title':        "text",
        'journaltitle': "varchar(255)",
        'issue':        "integer",
        'volume':       "integer",
        'number':       "integer",
        'edition':      "integer",
        'month':        "integer",
        'year':         "integer",
        'date':         "date",
        'url':          "varchar(255)",
        'isbn':         "integer",
        'institution':  "varchar(255)",
        'pages':        "varchar(31)",
        'file':         "varchar(255)",
        'abstract':     "text"
        }
SYNONYMS = {
        'doi':          ["DOI"],
        'title':        ["main-title", "maintitle"],
        'journaltitle': ["journal", "journaltitle", "publisher"],
        'date':         ["published-print"],
        'url':          ["URL"],
        'isbn':         ["ISBN"],
        'pages':        ["page"]
        }

config = configparser.ConfigParser()
config.read('config.ini')


def init(args):
    conn = sqlite3.connect("test.db")
    cmd = "create table literature(\n"
    for key, value in KEYS.items():
        cmd += key+' '+value+',\n'
    cmd = cmd[:-2]+'\n)'
    conn.execute(cmd)
    conn.commit()


def list(args):
    conn = sqlite3.connect("test.db")
    cursor = conn.execute("SELECT rowid, doi, author, title from literature")
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
        dois.extend(args.dois)
    for doi in dois:
        assert(re.match(DOI_REGEX, doi))
        page = requests.get(API_URL+doi, headers=dict(config['HEADER'])).json()
        payload = {}
        message = dict(page)['message']
        for key in message.keys():
            if key in KEYS.keys():
                _update_payload(payload, key, message[key])
            elif key in flatten([v for k, v in SYNONYMS.items()]):
                _update_payload(payload, key, message[key])
        print(json.dumps(payload, indent=2))


def _update_payload(payload, key, value):
    if key == 'title':  # array of strings
        payload[key] = value[0]
    elif key in ['author', 'editor']:  # array of contributors
        people = ''
        for person in value:
            people += person['given'] + ' ' + person['family'] + ', '
        payload['author'] = people[:-2]
    elif key in ['date', 'published-print']:  # partial date format
        payload['year'] = value['date-parts'][0][0]
        if len(value['date-parts'][0]) > 1:
            payload['month'] = value['date-parts'][0][1]
    else:
        payload[key] = value


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
