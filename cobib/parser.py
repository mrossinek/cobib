"""CoBib parsing module."""

from collections import OrderedDict
import os
import re
import requests

from bs4 import BeautifulSoup
from pylatexenc.latexencode import UnicodeToLatexEncoder
from ruamel.yaml import YAML
from ruamel.yaml.compat import StringIO
import bibtexparser

from cobib.config import CONFIG

# API and HEADER settings according to this resource: https://crosscite.org/docs.html
DOI_URL = "https://doi.org/"
DOI_HEADER = {'Accept': "application/x-bibtex"}
# arXiv URL according to docs from here https://arxiv.org/help/oa
ARXIV_URL = "https://export.arxiv.org/api/query?id_list="
# DOI regex used for matching DOIs
DOI_REGEX = r'(10\.[0-9a-zA-Z]+\/(?:(?!["&\'])\S)+)\b'
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

    def __init__(self, label, data):
        """Initializes the Entry object.

        Args:
            label (str): Database Id used for this entry.
            data (dict): Dictionary of fields specifying this entry.
        """
        self._label = label
        self.data = data.copy()
        self.escape_special_chars()
        if 'FORMAT' in CONFIG.config.keys():
            month_type = CONFIG.config['FORMAT'].get('month', None)
        if month_type:
            self.convert_month(month_type)

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
        self._label = label
        self.data['ID'] = label

    @property
    def tags(self):
        """Returns the tags of this entry."""
        return self.data.get('tags', None)

    @tags.setter
    def set_tags(self, tags):
        """Sets the tags of this entry."""
        self.data['tags'] = ''.join(tag.strip('+')+', ' for tag in tags).strip(', ')

    @property
    def file(self):
        """Returns the associated file of this entry."""
        return self.data.get('file', None)

    @file.setter
    def set_file(self, file):
        """Sets the associated file of this entry."""
        self.data['file'] = os.path.abspath(file)

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
            months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
                      'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
            if isinstance(month, str):
                self.data['month'] = str(months.index(month)+1)
            elif isinstance(month, int):
                self.data['month'] = months[month-1]

    def escape_special_chars(self):
        """Escapes special characters.

        Special characters should be escaped to ensure proper rendering in LaTeX documents. This
        function leverages the existing implementation of the pylatexenc module.
        """
        enc = UnicodeToLatexEncoder(non_ascii_only=True,
                                    replacement_latex_protection='braces-all',
                                    unknown_char_policy='keep')
        for key, value in self.data.items():
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

    def to_bibtex(self):
        """Returns the entry in bibtex format."""
        database = bibtexparser.bibdatabase.BibDatabase()
        database.entries = [self.data]
        return bibtexparser.dumps(database)

    def to_yaml(self):
        """Returns the entry in YAML format."""
        yaml = Entry.YamlDumper()
        yaml.explicit_start = True
        yaml.explicit_end = True
        return yaml.dump({self._label: dict(sorted(self.data.items()))})

    @staticmethod
    def from_bibtex(file, string=False):
        """Creates a new bibliography from a bibtex source file.

        Args:
            file (str or file): string with bibtex data or path to the bibtex file.
            string (bool, optional): indicates whether the file argument is of string or file type.

        Returns:
            An OrderedDict containing the bibliography as per the provided bibtex data.
        """
        if string:
            database = bibtexparser.loads(file)
        else:
            database = bibtexparser.load(file)
        bib = OrderedDict()
        for entry in database.entries:
            bib[entry['ID']] = Entry(entry['ID'], entry)
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
        page = requests.get(DOI_URL+doi, headers=DOI_HEADER)
        return Entry.from_bibtex(page.text, string=True)

    @staticmethod
    def from_arxiv(arxiv):
        """Queries the bibtex source for a given arxiv ID.

        Args:
            arxiv (str): arXiv ID for which to obtain the bibtex data.

        Returns:
            An OrderedDict containing the bibliographic data of the provided arXiv ID.
        """
        page = requests.get(ARXIV_URL+arxiv)
        xml = BeautifulSoup(page.text, features='html.parser')
        # TODO rewrite this to use a defaultdict(str)
        entry = {}
        entry['archivePrefix'] = 'arXiv'
        for key in xml.feed.entry.findChildren(recursive=False):
            # TODO key.name == 'category'
            # TODO key.name == 'link'
            # TODO key.name == 'updated'
            if key.name == 'arxiv:doi':
                entry['doi'] = str(key.contents[0])
            elif key.name == 'id':
                entry['arxivid'] = str(key.contents[0]).replace('http://arxiv.org/abs/', '')
                entry['eprint'] = str(key.contents[0])
            elif key.name == 'primary_category':
                entry['primaryClass'] = str(key.attrs['term'])
            elif key.name == 'published':
                entry['year'] = key.contents[0].split('-')[0]
                if 'ID' in entry.keys():
                    entry['ID'] = entry['ID'] + entry['year']
                else:
                    entry['ID'] = entry['year']
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
                print("The key '{}' of this arXiv entry is not being processed!".format(key.name))
        if 'doi' in entry.keys():
            entry['ENTRYTYPE'] = 'article'
        else:
            entry['ENTRYTYPE'] = 'unpublished'
        # strip last 'and' from author field
        entry['author'] = entry['author'][:-5]
        bib = OrderedDict()
        bib[entry['ID']] = Entry(entry['ID'], entry)
        return bib
