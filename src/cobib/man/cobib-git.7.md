cobib-git(7) -- git integration
===============================

## SYNOPSIS

```bash
cobib init --git
```
```python
config.database.git = True
```

## DESCRIPTION

coBib supports automatic version control of its plain-text database (see also *cobib-database(7)*).
To use this, the database must be initialized correctly, as shown above.

  1. The *cobib-init(1)* command must be given the `--git` argument.
  2. The `config.database.git` setting must be set to `True`.

When all of the above is done correctly, commands which affect the database will automatically generate commits to track their changes.
The following commands can then leverage this as follows:

  * *cobib-note(1)* will track changes to notes in addition to changes to the database
  * *cobib-review(1)* can continue a previously started review process
  * *cobib-undo(1)* can be used to undo a previous auto-generated commit
  * *cobib-redo(1)* can be used to undo a previous *cobib-undo(1)* command
  * *cobib-git(1)* transparently passes through to _git(1)_

## SEE ALSO

*cobib(1)*, *cobib-init(1)*, *cobib-note(1)*, *cobib-redo(1)*, *cobib-review(1)*, cobib-undo(1)_, cobib-database(7)_

[//]: # ( vim: set ft=markdown tw=0: )
