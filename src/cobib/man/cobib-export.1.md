cobib-export(1) -- export entries
=================================

## SYNOPSIS

`cobib export` [`-a|--abbreviate`] [`--dotless`] [`-b|--bibtex` _BIBFILE_] [`-z|--zip` _ZIPFILE_] [`-s|--selection`] [`--` _FILTER_ ...]

## DESCRIPTION

Exports entries from the database.
Two output formats are available:
- BibLaTeX (here referred to as BibTeX) files (enabled by `-b` or `--bibtex`)
- Zip archives (enabled by `-z` or `--zip`)

Note, that _at least_ one of these output formats has to be enabled!

The use case of the former is obvious, the one of the latter simply collects all associated files into a single zip archive.
This is important, since coBib (by design) permits files to be scattered across the entire file system.

When exporting to BibTeX, journal names can be abbreviated by specifying the `--abbreviate` (and optionally the `--dotless`) options, as explained in more detail below.

It is possible to limit the exported entries in two ways:
1. using the _cobib-filter(7)_ syntax
2. using the `--selection` option explained below

## OPTIONS

  * `-b`, `--bibtex`=_BIBFILE_:
    Specifies the path to the BibTeX output.

  * `-z`, `--zip`=_ZIPFILE_:
    Specifies the path to the zip archive.

  * `-s`, `--selection`:
    Switches from the _cobib-filter(7)_ mechanism to interpreting the _FILTER_ arguments as a list of plain entry labels.
    This is not necessarily super useful for using from the command-line, but integrates well with the visual selection in the _cobib-tui(7)_!

  * `-a`, `--abbreviate`:
    Specifies that journal names in the BibTeX output should be abbreviated as configured by `config.utils.journal_abbreviations`.

  * `--dotless`:
    Removes the punctuation from the abbreviated journal names.
    This option has no effect without `--abbreviate`.

## EXAMPLES

Simple exports with one or more output formats:
```bash
$ cobib export --bibtex output.bib
$ cobib export --zip output.zip
$ cobib export --bibtex output.bib --zip output.zip
```

Exports with abbreviated journal names:
```bash
$ cobib export --abbreviate --bibtex output.bib
$ cobib export -a --dotless --bibtex output.bib
```

Exports with a _cobib-filter(7)_ applied:
```bash
$ cobib export -b output.bib -- --or ++year 2024 ++year 2025
```

Exports with a manual selection:
```bash
$ cobib export -b output.bib -s -- Label1 Label2
```

## SEE ALSO

_cobib(1)_, _cobib-commands(7)_, _cobib-filter(7)_

[//]: # ( vim: set ft=markdown tw=0: )
