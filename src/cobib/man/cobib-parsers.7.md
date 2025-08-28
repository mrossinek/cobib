cobib-parsers(7) -- parser backends
===================================

## SYNOPSIS

```bash
$ cobib add --help
```

## DESCRIPTION

coBib has the builtin parser backends listed below.
Additionally, *cobib-plugins(7)* may implement and register their own parser backends.
Thus, the actual list of available backends can be found using the `--help` of the *cobib-add(1)* command:
```bash
$ cobib add --help
```

All available parser backends are registered as options of the *cobib-add(1)* command using their `name` attribute, like so: `--NAME`.
If the short-hand option corresponding to the name's first letter is not already used, that alias is also enabled, like so: `-N`.

  * *cobib-arxiv(7)*:
    Adds the entry from an arXiv ID.

  * *cobib-bibtex(7)*:
    Adds entries from a BibLaTeX file.

  * *cobib-doi(7)*:
    Adds the entry from a DOI.

  * *cobib-isbn(7)*:
    Adds the entry from an ISBN.

  * *cobib-url(7)*:
    Adds the entry from a URL.

  * *cobib-yaml(7)*:
    Adds entries from a YAML file in coBib's database format (see also *cobib-database(7)*).

## SEE ALSO

*cobib(1)*, *cobib-add(1)*, *cobib-plugins(7)*

[//]: # ( vim: set ft=markdown tw=0: )
