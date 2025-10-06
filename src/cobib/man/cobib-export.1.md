cobib-export(1) -- export entries
=================================

## SYNOPSIS

`cobib export` [`-s|--selection`] `--<EXPORTER>` [`--` _EXPORTER ARGS_ ...] [`--` _FILTER_ ...]

## DESCRIPTION

Exports entries from the database.
Two exporter backends are built into coBib:
- BibLaTeX (here referred to as BibTeX) files (enabled by `-b` or `--bibtex`) (see also *cobib-bibtex(7)*)
- Zip archives (enabled by `-z` or `--zip`) (see also *cobib-zip(7)*)

Note, that you can only export to one of these formats at a time!

The use case of the former is obvious, the one of the latter simply collects all associated files into a single zip archive.
This is important, since coBib (by design) permits files to be scattered across the entire file system.

Plugins can implement other exporters for other formats.
The full list of available backends can be seen in the output of:
```bash
$ cobib export --help
```

It is possible to limit the exported entries in two ways:
1. using the *cobib-filter(7)* syntax
2. using the `--selection` option explained below

Note, that providing the arguments correctly can be a bit nuanced, since both the `EXPORTER_ARGS` and `FILTER` can take positional and keyword arguments.
To help disambiguate this, you must use the dummy argument `--` as a separator.
Refer to the [EXAMPLES][] below for more details.

## OPTIONS

  * `-s`, `--selection`:
    Switches from the *cobib-filter(7)* mechanism to interpreting the _FILTER_ arguments as a list of plain entry labels.
    This is not necessarily super useful for using from the command-line, but integrates well with the visual selection in the *cobib-tui(7)*!

## EXAMPLES

Simple exports of the whole database to a given format:
```bash
$ cobib export --bibtex output.bib
$ cobib export --zip output.zip
```

Exports with abbreviated journal names:
```bash
$ cobib export --abbreviate --bibtex output.bib
$ cobib export -a --dotless --bibtex output.bib
```

Exports with a *cobib-filter(7)* applied:
```bash
$ cobib export -b output.bib -- --or ++year 2024 ++year 2025
```

Exports with a manual selection:
```bash
$ cobib export -s -b output.bib -- Label1 Label2
```

An export with `--bibtex` arguments and *cobib-filter(7)* arguments:
```bash
$ cobib export -b -- output.bib --abbreviate -- --or ++year 2024 ++year 2025
```

## SEE ALSO

*cobib(1)*, *cobib-commands(7)*, *cobib-exporters(7)*, *cobib-filter(7)*

[//]: # ( vim: set ft=markdown tw=0: )
