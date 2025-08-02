cobib-undo(1) -- undo the last change to the database
=====================================================

## SYNOPSIS

`cobib undo` [`-f|--force`]

## DESCRIPTION

Undoes the last change to the database.
This command can only be used when the _cobib-git(7)_ integration is enabled.

As a safety measure, this command will only undo the last change to the database, if it was one of coBib's automatic commits.
Specifying the `--force` option bypasses this safety feature.

## OPTIONS

  * `-f`, `--force`:
    When specified, the safety measure to only revert automatic commits gets disabled.

## EXAMPLES

```bash
cobib undo
cobib undo --force
```

## SEE ALSO

_cobib(1)_, _cobib-redo(1)_, _cobib-commands(7)_, _cobib-git(7)_

[//]: # ( vim: set ft=markdown tw=0: )
