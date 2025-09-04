cobib-import(1) -- import entries
=================================

## SYNOPSIS

`cobib import` [`--skip-download|--force-download`] `--<IMPORTER>` [`--`] _ARGS_ ...

## DESCRIPTION

Imports entries from another bibliography.
This can be seen as a migration utility and, thus, this command is used only once (or very rarely).
To ease the interface (and implementation), this process of adding new entries is separated from the *cobib-add(1)* command.

To support various other bibliography managers as sources for this command, the specific implementation of each one is split out (see *cobib-importers(7)*).
All available backends are then registered (at runtime) in a **mutually exclusive** group of keyword arguments (indicated by `--<IMPORTER>` above).
coBib ships with a single builtin backend to import from a BibTeX file (`--bibtex`), which is used like so:
```bash
$ cobib import --bibtex path/to/file.bib
```

> NOTE: in v5.5.0 of coBib there still exists a builtin `--zotero` backend, but it is deprecated and will be replaced by the `cobib-zotero` plugin in v6.0.0

Plugins can implement other importers for other sources.
The full list of available backends can be seen in the output of:
```bash
$ cobib import --help
```

### Notes on the configuration dependence

Since this command adds new entries to the database, its outcome can be affected by some configuration settings.
In particular, the values of _config.database.stringify_ (see *cobib-config(5)*) affect how certain fields are converted to/from strings.
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
$ cobib import --bibtex path/to/file.bib
```

While the `--bibtex` backend does not provide any download features, other backends provided by plugins should respect the corresponding options and setting:
```bash
$ cobib import --skip-download --<IMPORTER>
```


## SEE ALSO

*cobib(1)*, *cobib-commands(7)*, *cobib-importers(7)*

[//]: # ( vim: set ft=markdown tw=0: )
