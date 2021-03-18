"""CoBib database entry module."""

import logging
import os
import re
import subprocess

from pylatexenc.latexencode import UnicodeToLatexEncoder

from cobib.config import config

LOGGER = logging.getLogger(__name__)


class Entry:
    """Bibliography entry class.

    Handles everything ranging from field manipulation over format conversion to filter matching.
    """

    def __init__(self, label, data):
        """Initializes the Entry object.

        Args:
            label (str): Database Id used for this entry.
            data (dict): Dictionary of fields specifying this entry.
        """
        label = str(label)
        LOGGER.debug('Initializing entry: %s', label)
        self._label = label
        self.data = data.copy()
        if self.data['ID'] != self._label:
            # sanity check for matching label and ID
            LOGGER.warning("Mismatching label '%s' and ID '%s'. Overwriting ID with label.",
                           self._label, self.data['ID'])
            self.label = self._label

    def __eq__(self, other):
        """Check equality of two entries."""
        return self.label == other.label and self.data == other.data

    @property
    def label(self):
        """Returns the database Id of this entry."""
        return self._label

    @label.setter
    def label(self, label):
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
    def tags(self, tags):
        """Sets the tags of this entry."""
        self.data['tags'] = ''.join(tag.strip('+')+', ' for tag in tags).strip(', ')
        LOGGER.debug("Adding the tags '%s' to '%s'.", self.data['tags'], self.label)

    @property
    def file(self):
        """Returns the associated file of this entry."""
        return self.data.get('file', None)

    @file.setter
    def file(self, file):
        """Sets the associated file of this entry."""
        if isinstance(file, list):
            file = ', '.join([os.path.abspath(f) for f in file])
        else:
            file = os.path.abspath(file)
        self.data['file'] = file
        LOGGER.debug("Adding '%s' as the file to '%s'.", self.data['file'], self.label)

    def convert_month(self, type_=config.database.format.month):
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
        if not isinstance(month, type_):
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

    def save(self, parser=None):
        """Saves an entry.

        This method mainly wraps the conversion of an entry to its YAML representation as it is
        stored in CoBib's database. However, it also takes care of some final conversions depending
        on the user's configuration. Applying such modifications only before saving ensures a
        consistent state of the database while also providing a fast startup.

        Args:
            parser (YAMLParser, optional): the instance of the YAMLParser to use for dumping.
            Supplying a ready instance can improve efficiency significantly while saving many
            entries after one another.
        """
        self.convert_month(config.database.format.month)
        self.escape_special_chars(config.database.format.suppress_latex_warnings)
        if parser is None:
            # pylint: disable=import-outside-toplevel,cyclic-import
            from cobib.parsers import YAMLParser
            parser = YAMLParser()
        return parser.dump(self)

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
        # pylint: disable=import-outside-toplevel,cyclic-import
        from cobib.parsers import BibtexParser
        bibtex = BibtexParser().dump(self).split('\n')
        re_flags = re.IGNORECASE if ignore_case else 0
        for idx, line in enumerate(bibtex):
            if re.search(rf'{query}', line, flags=re_flags):
                # add new match
                matches.append([])
                # upper context; (we iterate in reverse in order to ensure that we abort on the
                # first previous occurrence of the query pattern)
                for string in reversed(bibtex[max(idx-context, 0):min(idx, len(bibtex))]):
                    if re.search(rf'{query}', string, flags=re_flags):
                        break
                    matches[-1].insert(0, string)
                # matching line itself
                matches[-1].append(line)
                # lower context
                for string in bibtex[max(idx+1, 0):min(idx+context+1, len(bibtex))]:
                    if re.search(rf'{query}', string, flags=re_flags):
                        break
                    matches[-1].append(string)

        if self.file and os.path.exists(self.file):
            grep_prog = config.commands.search.grep
            LOGGER.debug('Searching associated file %s with %s', self.file, grep_prog)
            grep = subprocess.Popen([grep_prog, f'-C{context}', query, self.file],
                                    stdout=subprocess.PIPE)
            # extract results
            results = grep.stdout.read().decode().split('\n--\n')
            for match in results:
                if match:
                    matches.append([line.strip() for line in match.split('\n') if line.strip()])

        return matches
