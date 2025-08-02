cobib-yaml(7) -- YAML parser backend
====================================

## SYNOPSIS

`cobib add --yaml` _FILE_

## DESCRIPTION

Adds the entries from a YAML file.
The contents of the YAML file are expected to be as described in _cobib-database(7)_.
The parsing is done using the [`ruamel.yaml`](https://pypi.org/project/ruamel.yaml/) library.

By default, coBib attempts to use the C-based implementation to ensure good performance.
If this causes problems, it can be disabled by setting `config.parsers.yaml.use_c_lib_yaml = False`.

Obviously, this parser does not support any automatic file downloads.

## EXAMPLES

```bash
$ cobib add --yaml file.yaml
```

## SEE ALSO

_cobib(1)_, _cobib-add(1)_, _cobib-database(7)_, _cobib-parsers(7)_

[//]: # ( vim: set ft=markdown tw=0: )
