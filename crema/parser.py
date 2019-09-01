from ruamel.yaml import YAML
from ruamel.yaml.compat import StringIO
from bs4 import BeautifulSoup
from collections import OrderedDict
import bibtexparser
import pdftotext
import re
import requests

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


class Entry():
    class YamlDumper(YAML):
        def dump(self, data, stream=None, **kw):
            inefficient = False
            if stream is None:
                inefficient = True
                stream = StringIO()
            YAML.dump(self, data, stream, **kw)
            if inefficient:
                return stream.getvalue()

    def __init__(self, label, data):
        self.label = label
        self.data = data

    def __repr__(self):
        return self.to_bibtex()

    def matches(self, filter, OR):
        match_list = []
        for key, values in filter.items():
            if key[0] not in self.data.keys():
                match_list.append(not key[1])
            for val in values:
                if val not in self.data[key[0]]:
                    match_list.append(not key[1])
                else:
                    match_list.append(key[1])
        if OR:
            return any(m for m in match_list)
        else:
            return all(m for m in match_list)

    def to_bibtex(self):
        database = bibtexparser.bibdatabase.BibDatabase()
        database.entries = [self.data]
        return bibtexparser.dumps(database)

    def to_yaml(self):
        yaml = Entry.YamlDumper()
        yaml.explicit_start = True
        yaml.explicit_end = True
        return yaml.dump({self.label: self.data})

    @staticmethod
    def from_bibtex(file, string=False):
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
        yaml = YAML()
        bib = OrderedDict()
        for entry in yaml.load_all(file):
            for label, data in entry.items():
                bib[label] = Entry(label, data)
        return bib

    @staticmethod
    def from_doi(doi):
        assert(re.match(DOI_REGEX, doi))
        page = requests.get(DOI_URL+doi, headers=DOI_HEADER)
        return Entry.from_bibtex(page.text, string=True)

    @staticmethod
    def from_arxiv(arxiv):
        page = requests.get(ARXIV_URL+arxiv)
        xml = BeautifulSoup(page.text, features='xml')
        entry = {}
        entry['archivePrefix'] = 'arXiv'
        for key in xml.metadata.arXiv.findChildren(recursive=False):
            if key.name == 'doi':
                entry['doi'] = str(key.contents[0])
            elif key.name == 'id':
                entry['arxivid'] = str(key.contents[0])
                entry['eprint'] = str(key.contents[0])
            elif key.name == 'categories':
                entry['primaryClass'] = key.contents[0].split(' ')[0]
            elif key.name == 'created':
                entry['year'] = key.contents[0].split('-')[0]
                if 'ID' in entry.keys():
                    entry['ID'] = entry['ID'] + entry['year']
                else:
                    entry['ID'] = entry['year']
            elif key.name == 'title':
                entry['title'] = re.sub(r'\s+', ' ', key.contents[0].strip().replace('\n', ' '))
            elif key.name == 'authors':
                entry['author'] = ''
                first = True
                for author in key.findChildren(recursive=False):
                    if first:
                        if 'ID' in entry.keys():
                            entry['ID'] = author.keyname.contents[0] + entry['ID']
                        else:
                            entry['ID'] = author.keyname.contents[0]
                        first = False
                    entry['author'] += author.forenames.contents[0] + ' ' + author.keyname.contents[0] + ' and '
                entry['author'] = entry['author'][:-5]
            elif key.name == 'abstract':
                entry['abstract'] = re.sub(r'\s+', ' ', key.contents[0].strip().replace('\n', ' '))
            else:
                print("The key '{}' of this arXiv entry is not being processed!".format(key.name))
        if 'doi' in entry.keys():
            entry['ENTRYTYPE'] = 'article'
        else:
            entry['ENTRYTYPE'] = 'unpublished'
        bib = OrderedDict()
        bib[entry['ID']] = Entry(entry['ID'], entry)
        return bib

    @staticmethod
    def from_pdf(pdf):
        def most_common(lst: list): return max(set(lst), key=lst.count)
        pdf_obj = pdftotext.PDF(pdf)
        text = "".join(pdf_obj)
        matches = re.findall(DOI_REGEX, text)
        return Entry.from_doi(most_common(matches))
