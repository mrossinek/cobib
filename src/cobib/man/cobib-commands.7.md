cobib-commands(7) -- subcommands
================================

## SYNOPSIS

```bash
$ cobib --help
```

## DESCRIPTION

coBib has a number of builtin subcommands listed below.
Additionally, _cobib-plugins(7)_ may implement and register their own subcommands.
Thus, the actual list of available commands can be found using the `--help`:
```bash
$ cobib --help
```

We divide the commands into [COMMON][COMMON COMMANDS] and [UTILITY][UTILITY COMMANDS] commands.

### COMMON COMMANDS

  * _cobib-add(1)_:
    Adds entries to the database.

  * _cobib-delete(1)_:
    Deletes entries from the database.

  * _cobib-edit(1)_:
    Edits an entry in the database.

  * _cobib-export(1)_:
    Exports the database.

  * _cobib-import(1)_:
    Imports entries into the database.

  * _cobib-list(1)_:
    Lists the entries in the database.

  * _cobib-modify(1)_:
    Modifies multiple filtered entries in the database in bulk.

  * _cobib-note(1)_:
    Interacts with the note attached to an entry in the database.

  * _cobib-open(1)_:
    Opens an attachment of an entry in the database.

  * _cobib-review(1)_:
    Reviews multiple filtered (partial) entries interactively.

  * _cobib-search(1)_:
    Searches the database.

  * _cobib-show(1)_:
    Shows an entry in the database.

### UTILITY COMMANDS

  * _cobib-git(1)_:
    Passes through to the _git(1)_ repository of the database.
    This requires _cobib-git(7)_ integration to set up.

  * _cobib-init(1)_:
    Initializes a new database.

  * _cobib-lint(1)_:
    Checks the database format.

  * _cobib-redo(1)_:
    Re-applies a previously undone change to the database.
    This requires _cobib-git(7)_ integration to set up.

  * _cobib-undo(1)_:
    Undoes the latest change to the database.
    This requires _cobib-git(7)_ integration to set up.

  * _cobib-unify-labels(1)_:
    Unifies the labels of all entries in the database.

## SEE ALSO

_cobib(1)_, _cobib-plugins(7)_

[//]: # ( vim: set ft=markdown tw=0: )
