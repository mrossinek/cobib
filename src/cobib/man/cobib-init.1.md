cobib-init(1) -- initialize a database
======================================

## SYNOPSIS

`cobib init` [`-g|--git`]

## DESCRIPTION

Initializes a new database.
This command must be run before cobib(1) can be used normally.
It ensures that the database file gets created at the location configured by the `config.database.file` setting.

Additionally, if the cobib-git(7) integration is supposed to be used, the `--git` option must be specified.
This latter option can also be enabled **after** a previously initialized database file already exists.

## OPTIONS

  * `-g`, `--git`:
    Initializes the cobib-git(7) integration.

## EXAMPLES

```bash
$ cobib init
$ cobib init --git
$ cobib -c path/to/another_config.py init
```

## SEE ALSO

*cobib(1)*, *cobib-commands(7)*

[//]: # ( vim: set ft=markdown tw=0: )
