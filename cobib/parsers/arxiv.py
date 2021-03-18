"""arXiv Parser."""

from collections import OrderedDict
import logging
import re
import sys

from bs4 import BeautifulSoup
import requests

from cobib.database import Entry
from .base_parser import Parser

LOGGER = logging.getLogger(__name__)


class ArxivParser(Parser):
    """The arXiv Parser."""

    name = 'arxiv'

    # arXiv URL according to docs from here https://arxiv.org/help/oa
    ARXIV_URL = "https://export.arxiv.org/api/query?id_list="

    def parse(self, string):
        # pdoc will inherit the docstring from the base class
        # noqa: D102
        LOGGER.info('Gathering BibTex data for arXiv ID: %s.', string)
        try:
            page = requests.get(self.ARXIV_URL+string, timeout=10)
        except requests.exceptions.RequestException as err:
            LOGGER.error('An Exception occurred while trying to query the arXiv ID: %s.', string)
            LOGGER.error(err)
            return {}
        xml = BeautifulSoup(page.text, features='html.parser')
        if xml.feed.entry.title.contents[0] == 'Error':
            msg = 'The arXiv API returned the following error: ' + \
                  xml.feed.entry.summary.contents[0]
            LOGGER.warning(msg)
            print(msg, file=sys.stderr)
            return {}
        entry = {}
        entry['archivePrefix'] = 'arXiv'
        for key in xml.feed.entry.findChildren(recursive=False):
            if key.name == 'arxiv:doi':
                entry['doi'] = str(key.contents[0])
            elif key.name == 'id':
                entry['arxivid'] = str(key.contents[0]).replace('http://arxiv.org/abs/', '')
                entry['eprint'] = str(key.contents[0])
            elif key.name == 'arxiv:primary_category':
                entry['primaryClass'] = str(key.attrs['term'])
            elif key.name == 'published':
                # The year must also be stored as a string for compatibility reasons with
                # bibtexparser. However, we perform a conversion to an integer first, to ensure that
                # the year can actually be represented as such.
                entry['year'] = str(int(key.contents[0].split('-')[0]))
                if 'ID' in entry.keys():
                    entry['ID'] = entry['ID'] + str(entry['year'])
                else:
                    entry['ID'] = str(entry['year'])
            elif key.name == 'title':
                entry['title'] = re.sub(r'\s+', ' ', key.contents[0].strip().replace('\n', ' '))
            elif key.name == 'author':
                if 'author' not in entry.keys():
                    first = True
                    entry['author'] = ''
                name = [n.contents[0] for n in key.findChildren()][0]
                if first:
                    if 'ID' in entry.keys():
                        entry['ID'] = name.split()[-1] + entry['ID']
                    else:
                        entry['ID'] = name.split()[-1]
                    first = False
                entry['author'] += '{} and '.format(name)
            elif key.name == 'summary':
                entry['abstract'] = re.sub(r'\s+', ' ', key.contents[0].strip().replace('\n', ' '))
            else:
                LOGGER.warning("The key '%s' of this arXiv entry is not being processed!", key.name)
        if 'doi' in entry.keys():
            entry['ENTRYTYPE'] = 'article'
        else:
            entry['ENTRYTYPE'] = 'unpublished'
        # strip last 'and' from author field
        entry['author'] = entry['author'][:-5]
        bib = OrderedDict()
        bib[entry['ID']] = Entry(entry['ID'], entry)
        return bib

    def dump(self, entry):
        # pdoc will inherit the docstring from the base class
        # noqa: D102
        LOGGER.error("Cannot dump an entry as an arXiv ID.")
