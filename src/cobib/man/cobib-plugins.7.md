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
    See *cobib-commands(7)* for more details.

  * `cobib.importers`:
    An entry point to register additional importer backends available through the *cobib-import(1)* command.
    See *cobib-importers(7)* for more details.

  * `cobib.parsers`:
    An entry point to register additional parser backends available through the *cobib-add(1)* command.
    See *cobib-parsers(7)* for more details.

## EXAMPLES

To see an example for developing a plugin, check out the [`cobib_dummy` plugin](https://gitlab.com/cobib/cobib/-/tree/master/plugin?ref_type=heads).

## SEE ALSO

*cobib(1)*, *cobib-commands(7)*, *cobib-importers(7)*, *cobib-parsers(7)*

[//]: # ( vim: set ft=markdown tw=0: )
