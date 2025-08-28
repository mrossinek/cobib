cobib-yaml(7) -- YAML parser backend
====================================

## SYNOPSIS

`cobib add --yaml` _FILE_

## DESCRIPTION

Adds the entries from a YAML file.
The contents of the YAML file are expected to be as described in *cobib-database(7)*.
The parsing is done using the [`ruamel.yaml`](https://pypi.org/project/ruamel.yaml/) library.

By default, coBib attempts to use the C-based implementation to ensure good performance.
If this causes problems, it can be disabled by setting `config.parsers.yaml.use_c_lib_yaml = False`.

Obviously, this parser does not support any automatic file downloads.

## EXAMPLES

```bash
$ cobib add --yaml file.yaml
```

## SEE ALSO

*cobib(1)*, *cobib-add(1)*, *cobib-database(7)*, *cobib-parsers(7)*

[//]: # ( vim: set ft=markdown tw=0: )
