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

coBib supports automatic version control of its plain-text database (see also _cobib-database(7)_).
To use this, the database must be initialized correctly, as shown above.

  1. The _cobib-init(1)_ command must be given the `--git` argument.
  2. The `config.database.git` setting must be set to `True`.

When all of the above is done correctly, commands which affect the database will automatically generate commits to track their changes.
The following commands can then leverage this as follows:

  * _cobib-note(1)_ will track changes to notes in addition to changes to the database
  * _cobib-review(1)_ can continue a previously started review process
  * _cobib-undo(1)_ can be used to undo a previous auto-generated commit
  * _cobib-redo(1)_ can be used to undo a previous _cobib-undo(1)_ command
  * _cobib-git(1)_ transparently passes through to _git(1)_

## SEE ALSO

_cobib(1)_, _cobib-init(1)_, _cobib-note(1)_, _cobib-redo(1)_, _cobib-review(1)_, cobib-undo(1)_, cobib-database(7)_

[//]: # ( vim: set ft=markdown tw=0: )
