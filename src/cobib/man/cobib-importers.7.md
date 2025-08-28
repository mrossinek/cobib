cobib-importers(7) -- importer backends
=======================================

## SYNOPSIS

```bash
$ cobib import --help
```

## DESCRIPTION

coBib has the builtin importer backends listed below.
Additionally, *cobib-plugins(7)* may implement and register their own importer backends.
Thus, the actual list of available backends can be found using the `--help` of the *cobib-import(1)* command:
```bash
$ cobib import --help
```

All available import backends are registered as options of the *cobib-import(1)* command using their `name` attribute, like so: `--NAME`.

  * *cobib-zotero(7)*:
    Imports entries from a Zotero bibliography.

## SEE ALSO

*cobib(1)*, *cobib-import(1)*, *cobib-plugins(7)*

[//]: # ( vim: set ft=markdown tw=0: )
