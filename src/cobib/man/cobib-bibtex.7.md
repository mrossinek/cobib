cobib-bibtex(7) -- BibTeX parser and importer backends
======================================================

## SYNOPSIS

```bash
cobib add --bibtex _FILE_
cobib import --bibtex _FILE_
```

## DESCRIPTION

Adds or imports the entries from a BibTeX file (see *cobib-add(1)* or *cobib-import(1)* for their differences).
This is done using the [bibtexparser](https://github.com/sciunto-org/python-bibtexparser) library.

Non-standard BibTeX types can be configured to be ignored via the `config.parsers.bibtex.ignore_non_standard_types` setting.

Obviously, this parser does not support any automatic file downloads so the download-related options and settings of the *cobib-import(1)* command have no effect.

## EXAMPLES

```bash
$ cobib add --bibtex file.bib
$ cobib import --bibtex file.bib
```

## SEE ALSO

*cobib(1)*, *cobib-add(1)*, *cobib-import(1)*, *cobib-importers(7)*, *cobib-parsers(7)*

[//]: # ( vim: set ft=markdown tw=0: )
