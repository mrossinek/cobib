cobib-yaml(7) -- YAML parser, importer and exporter backends
============================================================

## SYNOPSIS

`cobib add --yaml` _FILE_

`cobib import` `--yaml` _FILE_

`cobib export` `--yaml` `--` _FILE_

## DESCRIPTION

Adds or imports the entries from a YAML file (see *cobib-add(1)* or *cobib-import(1)* for their differences)
or exports the selected entries to a YAML file (see *cobib-export(1)*).
This is done using the [`ruamel.yaml`](https://pypi.org/project/ruamel.yaml/) library.

The contents of the YAML file follow the description from *cobib-database(7)*.

By default, coBib attempts to use the C-based implementation to ensure good performance.
If this causes problems, it can be disabled by setting `config.parsers.yaml.use_c_lib_yaml = False`.

Obviously, this parser does not support any automatic file downloads so the download-related options and settings of the *cobib-import(1)* command have no effect.

## EXAMPLES

```bash
$ cobib add --yaml file.yaml
$ cobib import --yaml file.yaml
$ cobib export --yaml file.yaml
```

## SEE ALSO

*cobib(1)*, *cobib-add(1)*, *cobib-export(1)*, *cobib-import(1)*, *cobib-exporters(7)*, *cobib-importers(7)*, *cobib-parsers(7)*

[//]: # ( vim: set ft=markdown tw=0: )
