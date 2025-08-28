cobib-commands(7) -- subcommands
================================

## SYNOPSIS

```bash
$ cobib --help
```

## DESCRIPTION

coBib has a number of builtin subcommands listed below.
Additionally, *cobib-plugins(7)* may implement and register their own subcommands.
Thus, the actual list of available commands can be found using the `--help`:
```bash
$ cobib --help
```

We divide the commands into [COMMON][COMMON COMMANDS] and [UTILITY][UTILITY COMMANDS] commands.

### COMMON COMMANDS

  * *cobib-add(1)*:
    Adds entries to the database.

  * *cobib-delete(1)*:
    Deletes entries from the database.

  * *cobib-edit(1)*:
    Edits an entry in the database.

  * *cobib-export(1)*:
    Exports the database.

  * *cobib-import(1)*:
    Imports entries into the database.

  * *cobib-list(1)*:
    Lists the entries in the database.

  * *cobib-modify(1)*:
    Modifies multiple filtered entries in the database in bulk.

  * *cobib-note(1)*:
    Interacts with the note attached to an entry in the database.

  * *cobib-open(1)*:
    Opens an attachment of an entry in the database.

  * *cobib-review(1)*:
    Reviews multiple filtered (partial) entries interactively.

  * *cobib-search(1)*:
    Searches the database.

  * *cobib-show(1)*:
    Shows an entry in the database.

### UTILITY COMMANDS

  * *cobib-git(1)*:
    Passes through to the _git(1)_ repository of the database.
    This requires *cobib-git(7)* integration to set up.

  * *cobib-init(1)*:
    Initializes a new database.

  * *cobib-lint(1)*:
    Checks the database format.

  * *cobib-redo(1)*:
    Re-applies a previously undone change to the database.
    This requires *cobib-git(7)* integration to set up.

  * *cobib-undo(1)*:
    Undoes the latest change to the database.
    This requires *cobib-git(7)* integration to set up.

  * *cobib-unify-labels(1)*:
    Unifies the labels of all entries in the database.

## SEE ALSO

*cobib(1)*, *cobib-plugins(7)*

[//]: # ( vim: set ft=markdown tw=0: )
