cobib-exporters(7) -- exporter backends
=======================================

## SYNOPSIS

```bash
$ cobib export --help
```

## DESCRIPTION

coBib has the builtin exporter backends listed below.
Additionally, *cobib-plugins(7)* may implement and register their own exporter backends.
Thus, the actual list of available backends can be found using the `--help` of the *cobib-export(1)* command:
```bash
$ cobib export --help
```

All available export backends are registered as options of the *cobib-export(1)* command using their `name` attribute, like so: `--NAME`.

  * *cobib-bibtex(7)*:
    Exports entries to a BibTeX file.

  * *cobib-yaml(7)*:
    Exports entries to a YAML file.

  * *cobib-zip(7)*:
    Exports the associated files of entries to a Zip archive.

## SEE ALSO

*cobib(1)*, *cobib-export(1)*, *cobib-plugins(7)*

[//]: # ( vim: set ft=markdown tw=0: )
