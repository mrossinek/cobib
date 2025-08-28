cobib-redo(1) -- reapply an undone change to the database
=========================================================

## SYNOPSIS

`cobib redo`

## DESCRIPTION

Reapplies a change to the database that was previously undone with *cobib-undo(1)*.
This command can only be used when the *cobib-git(7)* integration is enabled.

If the previous change to the database is **not** the result of cobib-undo(1)_, then this command has no effect.

## EXAMPLES

```bash
cobib redo
```

## SEE ALSO

*cobib(1)*, *cobib-undo(1)*, *cobib-commands(7)*, *cobib-git(7)*

[//]: # ( vim: set ft=markdown tw=0: )
