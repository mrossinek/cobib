cobib-parsers(7) -- parser backends
===================================

## SYNOPSIS

```bash
$ cobib add --help
```

## DESCRIPTION

coBib has the builtin parser backends listed below.
Additionally, _cobib-plugins(7)_ may implement and register their own parser backends.
Thus, the actual list of available backends can be found using the `--help` of the _cobib-add(1)_ command:
```bash
$ cobib add --help
```

All available parser backends are registered as options of the _cobib-add(1)_ command using their `name` attribute, like so: `--NAME`.
If the short-hand option corresponding to the name's first letter is not already used, that alias is also enabled, like so: `-N`.

  * _cobib-arxiv(7)_:
    Adds the entry from an arXiv ID.

  * _cobib-bibtex(7)_:
    Adds entries from a BibLaTeX file.

  * _cobib-doi(7)_:
    Adds the entry from a DOI.

  * _cobib-isbn(7)_:
    Adds the entry from an ISBN.

  * _cobib-url(7)_:
    Adds the entry from a URL.

  * _cobib-yaml(7)_:
    Adds entries from a YAML file in coBib's database format (see also _cobib-database(7)_).

## SEE ALSO

_cobib(1)_, _cobib-add(1)_, _cobib-plugins(7)_

[//]: # ( vim: set ft=markdown tw=0: )
