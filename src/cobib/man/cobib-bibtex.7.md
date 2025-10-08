cobib-bibtex(7) -- BibTeX parser, importer and exporter backends
================================================================

## SYNOPSIS

```bash
cobib add --bibtex _FILE_
cobib import --bibtex _FILE_
cobib export --bibtex _FILE_ --journal-format _FORMAT_
```

## DESCRIPTION

Adds or imports the entries from a BibTeX file (see *cobib-add(1)* or *cobib-import(1)* for their differences)
or exports the selected entries to a BibTeX file (see *cobib-export(1)*).
This is done using the [bibtexparser](https://github.com/sciunto-org/python-bibtexparser) library.

Non-standard BibTeX types can be configured to be ignored via the `config.parsers.bibtex.ignore_non_standard_types` setting.

Obviously, this parser does not support any automatic file downloads so the download-related options and settings of the *cobib-import(1)* command have no effect.

## OPTIONS

  * `-f`, `--journal-format=`_FORMAT_:
    **Only available with *cobib-export(1)*!**
    Specify the output format of the `journal` field values. The choices are: `full`, `abbrev`, and `dotless`.
    These are full-length, abbreviated and abbreviated without punctuation journal names.
    This takes precedence over the value of the `config.exporters.bibtex.journal_format` setting.

## EXAMPLES

```bash
$ cobib add --bibtex file.bib
$ cobib import --bibtex file.bib
$ cobib export --bibtex file.bib
```

## SEE ALSO

*cobib(1)*, *cobib-add(1)*, *cobib-export(1)*, *cobib-import(1)*, *cobib-exporters(7)*, *cobib-importers(7)*, *cobib-parsers(7)*

[//]: # ( vim: set ft=markdown tw=0: )
