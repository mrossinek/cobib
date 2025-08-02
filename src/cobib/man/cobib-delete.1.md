cobib-delete(1) -- delete entries
=================================

## SYNOPSIS

`cobib delete` [`-y|--yes`] [`--preserve-files|--no-preserve-files`] _LABEL_ [_LABEL_ ...]

## DESCRIPTION

Deletes one or more entries from the database.
The entries to be deleted are specified by their _LABEL_.

A deletion will have to be confirmed in a prompt.
This can be disabled via the `--yes` argument at runtime or by default by changing the value of `config.commands.delete.confirm` (see also _cobib-config(5)_).

Depending on the value of `config.commands.delete.preserve_files`, associated files of an entry will be deleted, too.
The value of this setting can be overwritten at runtime using the options below.

## OPTIONS

  * `-y`, `--yes`:
    Enforces the entry deletion without any confirmation prompt.
    This takes precedence over the _config.commands.delete.confirm_download_ setting.

  * `--preserve-files`:
    Ensures that associated files are _preserved_, i.e. **NOT** deleted.

  * `--no-preserve-files`:
    Enforces the deletion of associated files.

## EXAMPLES

```bash
$ cobib delete Label1 Label2
$ cobib delete --yes Label3
$ cobib delete --preserve-files Label3
$ cobib delete --no-preserve-files Label4 Label5
```

## SEE ALSO

_cobib(1)_, _cobib-commands(7)_

[//]: # ( vim: set ft=markdown tw=0: )
