cobib-redo(1) -- reapply an undone change to the database
=========================================================

## SYNOPSIS

`cobib redo`

## DESCRIPTION

Reapplies a change to the database that was previously undone with _cobib-undo(1)_.
This command can only be used when the _cobib-git(7)_ integration is enabled.

If the previous change to the database is **not** the result of cobib-undo(1)_, then this command has no effect.

## EXAMPLES

```bash
cobib redo
```

## SEE ALSO

_cobib(1)_, _cobib-undo(1)_, _cobib-commands(7)_, _cobib-git(7)_

[//]: # ( vim: set ft=markdown tw=0: )
