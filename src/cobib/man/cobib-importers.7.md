cobib-importers(7) -- importer backends
=======================================

## SYNOPSIS

```bash
$ cobib import --help
```

## DESCRIPTION

coBib has the builtin importer backends listed below.
Additionally, _cobib-plugins(7)_ may implement and register their own importer backends.
Thus, the actual list of available backends can be found using the `--help` of the _cobib-import(1)_ command:
```bash
$ cobib import --help
```

All available import backends are registered as options of the _cobib-import(1)_ command using their `name` attribute, like so: `--NAME`.

  * _cobib-zotero(7)_:
    Imports entries from a Zotero bibliography.

## SEE ALSO

_cobib(1)_, _cobib-import(1)_, _cobib-plugins(7)_

[//]: # ( vim: set ft=markdown tw=0: )
