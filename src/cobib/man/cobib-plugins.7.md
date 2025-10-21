cobib-plugins(7) -- entry points for coBib's plugins
====================================================

## SYNOPSIS

```toml
[project.entry-points."cobib.commands"]
[project.entry-points."cobib.exporters"]
[project.entry-points."cobib.importers"]
[project.entry-points."cobib.parsers"]
[project.entry-points."cobib.man"]
```

## DESCRIPTION

coBib provides multiple [entry-points](https://setuptools.pypa.io/en/latest/pkg_resources.html#entry-points) for plugins to register additional functionality.

  * `cobib.commands`:
    An entry-point to register additional commands available through the command-line interface.
    See *cobib-commands(7)* for more details.

  * `cobib.exporters`:
    An entry-point to register additional exporter backends available through the *cobib-export(1)* command.
    See *cobib-exporters(7)* for more details.

  * `cobib.importers`:
    An entry-point to register additional importer backends available through the *cobib-import(1)* command.
    See *cobib-importers(7)* for more details.

  * `cobib.parsers`:
    An entry-point to register additional parser backends available through the *cobib-add(1)* command.
    See *cobib-parsers(7)* for more details.

  * `cobib.man`:
    An entry-point to register additional man-pages available through the *cobib-man(1)* command.
    See *cobib-man(7)* for more details.

## EXAMPLES

To see an example for developing a plugin, check out the [plugin template](https://gitlab.com/cobib/templates/cobib-plugin-template).

## SEE ALSO

*cobib(1)*, *cobib-commands(7)*, *cobib-exporters(7)*, *cobib-importers(7)*, *cobib-parsers(7)*

[//]: # ( vim: set ft=markdown tw=0: )
