cobib-bibtex(7) -- BibTeX parser backend
========================================

## SYNOPSIS

`cobib add --bibtex` _FILE_

## DESCRIPTION

Adds the entries from a BibTeX file.
This is done using the [bibtexparser](https://github.com/sciunto-org/python-bibtexparser) library.

Non-standard BibTeX types can be configured to be ignored via the `config.parsers.bibtex.ignore_non_standard_types` setting.

Obviously, this parser does not support any automatic file downloads.

## EXAMPLES

```bash
$ cobib add --bibtex file.bib
```

## SEE ALSO

_cobib(1)_, _cobib-add(1)_, _cobib-parsers(7)_

[//]: # ( vim: set ft=markdown tw=0: )
