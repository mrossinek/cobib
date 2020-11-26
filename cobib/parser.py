"""CoBib parsing module."""

from collections import OrderedDict
import json
import logging
import os
import re
import subprocess
import sys

from bs4 import BeautifulSoup
from pylatexenc.latexencode import UnicodeToLatexEncoder
from ruamel.yaml import YAML
from ruamel.yaml.compat import StringIO
import bibtexparser
import requests

from cobib.config import CONFIG

LOGGER = logging.getLogger(__name__)

# API and HEADER settings according to this resource: https://crosscite.org/docs.html
DOI_URL = "https://doi.org/"
DOI_HEADER = {'Accept': "application/x-bibtex"}
# DOI regex used for matching DOIs
DOI_REGEX = r'(10\.[0-9a-zA-Z]+\/(?:(?!["&\'])\S)+)\b'
# arXiv URL according to docs from here https://arxiv.org/help/oa
ARXIV_URL = "https://export.arxiv.org/api/query?id_list="
# ISBN regex used for matching ISBNs (adapted from https://github.com/xlcnd/isbnlib)
ISBN_REGEX = re.compile(r'97[89]{1}(?:-?\d){10}|\d{9}[0-9X]{1}|'
                        r'[-0-9X]{10,16}', re.I | re.M | re.S)
# ISBN-API: https://openlibrary.org/dev/docs/api/books
ISBN_URL = "https://openlibrary.org/api/books?bibkeys=ISBN:"
# biblatex default types and required values taken from their docs: https://ctan.org/pkg/biblatex
BIBTEX_TYPES = {
    'article': ['author', 'title', 'journal', 'year'],
    'book': ['author', 'title', 'year'],
    'collection': ['editor', 'title', 'year'],
    'proceedings': ['title', 'year'],
    'report': ['author', 'title', 'type', 'institution', 'year'],
    'thesis': ['author', 'title', 'type', 'institution', 'year'],
    'unpublished': ['author', 'title', 'year']
    }


class Entry:
    """Bibliography entry class.

    Handles everything ranging from field manipulation over format conversion to filter matching.
    """
    class YamlDumper(YAML):
        """Wrapper class for YAML dumping."""

        # pylint: disable=arguments-differ,inconsistent-return-statements
        def dump(self, data, stream=None, **kw):
            """See base class."""
            inefficient = False
            if stream is None:
                inefficient = True
                stream = StringIO()
            YAML.dump(self, data, stream, **kw)
            if inefficient:
                return stream.getvalue()

    def __init__(self, label, data, suppress_warnings=True):
        """Initializes the Entry object.

        Args:
            label (str): Database Id used for this entry.
            data (dict): Dictionary of fields specifying this entry.
            suppress_warnings (bool): if True, suppresses warnings.
        """
        label = str(label)
        LOGGER.debug('Initializing entry: %s', label)
        self._label = label
        self.data = data.copy()
        self.escape_special_chars(suppress_warnings)
        month_type = CONFIG.config['FORMAT'].get('month', None)
        if month_type:
            self.convert_month(month_type)
        if self.data['ID'] != self._label:
            # sanity check for matching label and ID
            LOGGER.warning("Mismatching label '%s' and ID '%s'. Overwriting ID with label.",
                           self._label, self.data['ID'])
            self.set_label = self._label

    def __repr__(self):
        """Returns the entry in its bibtex format."""
        return self.to_bibtex()

    @property
    def label(self):
        """Returns the database Id of this entry."""
        return self._label

    @label.setter
    def set_label(self, label):
        """Sets the database Id of this entry."""
        LOGGER.debug("Changing the label '%s' to '%s'.", self.label, label)
        self._label = label
        LOGGER.debug("Changing the ID '%s' to '%s'.", self.data['ID'], label)
        self.data['ID'] = label

    @property
    def tags(self):
        """Returns the tags of this entry."""
        return self.data.get('tags', None)

    @tags.setter
    def set_tags(self, tags):
        """Sets the tags of this entry."""
        self.data['tags'] = ''.join(tag.strip('+')+', ' for tag in tags).strip(', ')
        LOGGER.debug("Adding the tags '%s' to '%s'.", self.data['tags'], self.label)

    @property
    def file(self):
        """Returns the associated file of this entry."""
        return self.data.get('file', None)

    @file.setter
    def set_file(self, file):
        """Sets the associated file of this entry."""
        if isinstance(file, list):
            file = ', '.join([os.path.abspath(f) for f in file])
        else:
            file = os.path.abspath(file)
        self.data['file'] = file
        LOGGER.debug("Adding '%s' as the file to '%s'.", self.data['file'], self.label)

    def convert_month(self, type_):
        """Converts the month into the specified type.

        The month field of an entry may be stored either in string or number format. This function
        is used to convert between the two options.

        Args:
            type_ (str): may be either 'str' or 'int' indicating the format of the month field
        """
        month = self.data.get('month', None)
        if month is None:
            return
        try:
            month = int(month)
        except ValueError:
            pass
        if type(month).__name__ != type_:
            LOGGER.debug('Converting month type for %s', self.label)
            months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
                      'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
            if isinstance(month, str):
                self.data['month'] = str(months.index(month)+1)
            elif isinstance(month, int):
                self.data['month'] = months[month-1]

    def escape_special_chars(self, suppress_warnings=True):
        """Escapes special characters.

        Special characters should be escaped to ensure proper rendering in LaTeX documents. This
        function leverages the existing implementation of the pylatexenc module.

        Args:
            suppress_warnings (bool): if True, suppresses warnings.
        """
        enc = UnicodeToLatexEncoder(non_ascii_only=True,
                                    replacement_latex_protection='braces-all',
                                    unknown_char_policy='keep',
                                    unknown_char_warning=not suppress_warnings or
                                    LOGGER.isEnabledFor(10))  # 10 = DEBUG logging level
        for key, value in self.data.items():
            if key in ('ID', 'file'):
                # do NOT these fields and keep any special characters
                self.data[key] = value
                continue
            if isinstance(value, str):
                self.data[key] = enc.unicode_to_latex(value)

    def matches(self, _filter, _or):
        """Check whether the filter matches.

        CoBib provides an extensive filtering implementation. The filter is specified in the form
        of a dictionary whose keys consist of pairs of (str, bool) entries where the string
        indicates the field to match against and the boolean whether a positive (true) or negative
        (false) match is required. The value obviously refers to what needs to be matched.

        Args:
            _filter (dict): dictionary describing the filter as explained above.
            _or (bool): boolean indicating whether logical OR (true) or AND (false) are used to
                        combine multiple filter items.

        Returns:
            Boolean indicating whether this entry matches the filter.
        """
        LOGGER.debug('Checking whether entry %s matches.', self.label)
        match_list = []
        for key, values in _filter.items():
            if key[0] not in self.data.keys():
                match_list.append(not key[1])
                continue
            for val in values:
                if val not in self.data[key[0]]:
                    match_list.append(not key[1])
                else:
                    match_list.append(key[1])
        if _or:
            return any(m for m in match_list)
        return all(m for m in match_list)

    def search(self, query, context=1, ignore_case=False):
        """Search entry contents for query string.

        The search will try its best to recursively query all the data associated with this entry
        for the given query string.

        Args:
            query (str): text to search for.
            context (int): number of context lines to provide for each match.
            ignore_case (bool): if True, ignore case when searching.

        Returns:
            A list of lists containing the context for each match associated with this entry.
        """
        LOGGER.debug('Searching entry %s for %s.', self.label, query)
        matches = []
        bibtex = str(self).split('\n')
        re_flags = re.IGNORECASE if ignore_case else 0
        for idx, line in enumerate(bibtex):
            if re.search(rf'{query}', line, flags=re_flags):
                # add new match
                matches.append([])
                # upper context
                for string in bibtex[max(idx-context, 0):min(idx+1, len(bibtex))]:
                    if not re.search(rf'{query}', string, flags=re_flags):
                        matches[-1].append(string)
                # matching line itself
                matches[-1].append(line)
                # lower context
                for string in bibtex[max(idx+1, 0):min(idx+context+1, len(bibtex))]:
                    if not re.search(rf'{query}', string, flags=re_flags):
                        matches[-1].append(string)
                    else:
                        break

        if self.file and os.path.exists(self.file):
            grep_prog = CONFIG.config['DATABASE'].get('grep')
            LOGGER.debug('Searching associated file %s with %s', self.file, grep_prog)
            grep = subprocess.Popen([grep_prog, f'-C{context}', query, self.file],
                                    stdout=subprocess.PIPE)
            # extract results
            results = grep.stdout.read().decode().split('--')
            for match in results:
                if match:
                    matches.append([line.strip() for line in match.split('\n') if line.strip()])

        return matches

    def to_bibtex(self):
        """Returns the entry in biblatex format."""
        database = bibtexparser.bibdatabase.BibDatabase()
        database.entries = [self.data]
        LOGGER.debug('Converting entry %s to BibTex format.', self.label)
        return bibtexparser.dumps(database)

    def to_yaml(self):
        """Returns the entry in YAML format."""
        yaml = Entry.YamlDumper()
        yaml.explicit_start = True
        yaml.explicit_end = True
        LOGGER.debug('Converting entry %s to YAML format.', self.label)
        return yaml.dump({self._label: dict(sorted(self.data.items()))})

    @staticmethod
    def from_bibtex(file, string=False):
        """Creates a new bibliography from a BibLaTex source file.

        Args:
            file (str or file): string with BibLaTex data or path to the BibLaTex file.
            string (bool, optional): indicates whether the file argument is of string or file type.

        Returns:
            An OrderedDict containing the bibliography as per the provided BibLaTex data.
        """
        bparser = bibtexparser.bparser.BibTexParser()
        bparser.ignore_nonstandard_types = CONFIG.config['DATABASE'].getboolean(
            'ignore_non_standard_types', False)
        if string:
            LOGGER.debug('Loading BibTex string: %s.', file)
            database = bibtexparser.loads(file, parser=bparser)
        else:
            LOGGER.debug('Loading BibTex data from file: %s.', file)
            database = bibtexparser.load(file, parser=bparser)
        bib = OrderedDict()
        for entry in database.entries:
            bib[entry['ID']] = Entry(entry['ID'], entry, suppress_warnings=False)
        return bib

    @staticmethod
    def from_yaml(file):
        """Creates a new bibliography from a YAML source file.

        Args:
            file (file): path to YAML file from which to load database.

        Returns:
            An OrderedDict containing the bibliography as per the provided YAML file.
        """
        yaml = YAML()
        bib = OrderedDict()
        LOGGER.debug('Loading YAML data from file: %s.', file)
        for entry in yaml.load_all(file):
            for label, data in entry.items():
                bib[label] = Entry(label, data)
        return bib

    @staticmethod
    def from_doi(doi):
        """Queries the bibtex source for a given DOI.

        Args:
            doi (str): DOI for which to obtain the bibtex data.

        Returns:
            An OrderedDict containing the bibliographic data of the provided DOI.
        """
        assert re.match(DOI_REGEX, doi)
        LOGGER.info('Gathering BibTex data for DOI: %s.', doi)
        page = requests.get(DOI_URL+doi, headers=DOI_HEADER, timeout=5)
        return Entry.from_bibtex(page.text, string=True)

    @staticmethod
    def from_arxiv(arxiv):
        """Queries the bibtex source for a given arxiv ID.

        Args:
            arxiv (str): arXiv ID for which to obtain the bibtex data.

        Returns:
            An OrderedDict containing the bibliographic data of the provided arXiv ID.
        """
        LOGGER.info('Gathering BibTex data for arXiv ID: %s.', arxiv)
        page = requests.get(ARXIV_URL+arxiv)
        xml = BeautifulSoup(page.text, features='html.parser')
        entry = {}
        entry['archivePrefix'] = 'arXiv'
        for key in xml.feed.entry.findChildren(recursive=False):
            if key.name == 'arxiv:doi':
                entry['doi'] = str(key.contents[0])
            elif key.name == 'id':
                entry['arxivid'] = str(key.contents[0]).replace('http://arxiv.org/abs/', '')
                entry['eprint'] = str(key.contents[0])
            elif key.name == 'primary_category':
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

    @staticmethod
    def from_isbn(isbn):
        """Queries the bibtex source for a given ISBN.

        Args:
            isbn (str): ISBN for which to obtain the bibtex data.

        Returns:
            An OrderedDict containing the bibliographic data of the provided ISBN.
        """
        assert re.match(ISBN_REGEX, isbn)
        LOGGER.info('Gathering BibTex data for ISBN: %s.', isbn)
        isbn_plain = ''.join([i for i in isbn if i.isdigit()])
        page = requests.get(ISBN_URL+isbn_plain+'&jscmd=data&format=json', timeout=5)
        contents = dict(json.loads(page.content))
        if not contents:
            msg = f'No data was found for ISBN: {isbn}. If you think this is an error and the ' + \
                  'openlibrary API should provide an entry, please file a bug report. Otherwise' + \
                  ' please try adding this entry manually until more APIs are available in CoBib.'
            LOGGER.warning(msg)
            print(msg, file=sys.stderr)
            return {}
        entry = {}
        for key, value in contents[list(contents.keys())[0]].items():
            if key in ['title', 'url']:
                entry[key] = value
            elif key == 'number_of_pages':
                # we explicitly convert to a string to prevent type errors in the bibtexparser
                entry['pages'] = str(value)
            elif key == 'publish_date':
                entry['date'] = value
                try:
                    entry['year'] = re.search(r'\d{4}', value).group()
                    if 'ID' in entry.keys():
                        entry['ID'] += str(entry['year'])
                    else:
                        entry['ID'] = str(entry['year'])
                except AttributeError:
                    pass
            elif key == 'authors':
                if 'ID' in entry.keys():
                    entry['ID'] = value[0]['name'].split()[-1] + entry['ID']
                else:
                    entry['ID'] = value[0]['name'].split()[-1]
                entry['author'] = ' and'.join([a['name'] for a in value])
            elif key == 'publishers':
                entry['publisher'] = ' and'.join([a['name'] for a in value])
        # set entry-type do 'book'
        entry['ENTRYTYPE'] = 'book'
        bib = OrderedDict()
        bib[entry['ID']] = Entry(entry['ID'], entry)
        return bib
