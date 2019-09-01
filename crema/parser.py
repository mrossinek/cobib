from ruamel.yaml import YAML
from ruamel.yaml.compat import StringIO
from collections import OrderedDict
import bibtexparser


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
    def from_bibtex(file):
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
