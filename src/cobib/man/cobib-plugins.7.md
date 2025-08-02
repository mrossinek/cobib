cobib-plugins(7) -- entry points for coBib's plugins
====================================================

## SYNOPSIS

```python
cobib.commands
cobib.importers
cobib.parsers
```

## DESCRIPTION

coBib provides multiple entry points for plugins to register additional functionality.

  * `cobib.commands`:
    An entry point to register additional commands available through the command-line interface.
    See _cobib-commands(7)_ for more details.

  * `cobib.importers`:
    An entry point to register additional importer backends available through the _cobib-import(1)_ command.
    See _cobib-importers(7)_ for more details.

  * `cobib.parsers`:
    An entry point to register additional parser backends available through the _cobib-add(1)_ command.
    See _cobib-parsers(7)_ for more details.

## EXAMPLES

To see an example for developing a plugin, check out the [`cobib_dummy` plugin](https://gitlab.com/cobib/cobib/-/tree/master/plugin?ref_type=heads).

## SEE ALSO

_cobib(1)_, _cobib-commands(7)_, _cobib-importers(7)_, _cobib-parsers(7)_

[//]: # ( vim: set ft=markdown tw=0: )
