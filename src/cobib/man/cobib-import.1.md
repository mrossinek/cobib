cobib-import(1) -- import entries
=================================

## SYNOPSIS

`cobib import` [`--skip-download|--force-download`] `--<IMPORTER>` [`--`] _ARGS_ ...

## DESCRIPTION

Imports entries from another bibliography.
This can be seen as a migration utility and, thus, this command is used only once (or very rarely).
To ease the interface (and implementation), this process of adding new entries is separated from the _cobib-add(1)_ command.

To support various other bibliography managers as sources for this command, the specific implementation of each one is split out (see _cobib-importers(7)_).
All available backends are then registered (at runtime) in a **mutually exclusive** group of keyword arguments (indicated by `--<IMPORTER>` above).
coBib ships with a single backend for Zotero, which is used like so:
```bash
$ cobib import --zotero
```

Plugins can implement other importers for other sources.
The full list of available backends can be seen in the output of:
```bash
$ cobib import --help
```

### Notes on the configuration dependence

Since this command adds new entries to the database, its outcome can be affected by some configuration settings.
In particular, the values of _config.database.stringify_ (see _cobib-config(5)_) affect how certain fields are converted to/from strings.
For example, _config.database.stringify.list_separator.file_ defaults to comma-separated values.
But you should update this setting **before** importing if you use another separator (for example a semicolon) like so:
```python
from cobib import config

config.database.stringify.list_separator.file = "; "
```

## OPTIONS

  * `--skip-download`:
    Skips the automatic download of attached files (like PDFs).
    This takes precedence over the _config.commands.import\_.skip_download_ setting.

  * `--force-download`:
    Forces the automatic download of attached files (like PDFs).
    This takes precedence over the _config.commands.import\_.skip_download_ setting.

  * `--<IMPORTER>`:
    Specifies the importer to use.
    All positional arguments (_ARGS_) will be forwarded to this backend.

## EXAMPLES

```bash
$ cobib import --skip-download --zotero
```


## SEE ALSO

_cobib(1)_, _cobib-commands(7)_, _cobib-importers(7)_

[//]: # ( vim: set ft=markdown tw=0: )
