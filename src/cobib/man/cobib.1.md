cobib(1) -- a console-based bibliography management tool
========================================================

## SYNOPSIS

`cobib` [`-p|--porcelain`] [`-v|--verbose`] [`-c|--config`=_PATH_] [`-l|--logfile`=_PATH_] [_SUBCOMMAND_] [_ARGS_ ...]<br>
`cobib` `-h|--help` <br>
`cobib` `--version`

## DESCRIPTION

coBib is a console-based bibliography management tool written in Python.
It maintains a plain-text database of literature references in YAML format and provides various subcommands to work with this database.
It also provides an interactive terminal user interface (see also _cobib-tui(7)_) to complement its command-line interface (see the [SUBCOMMANDS][] section below).

## OPTIONS

  * `--version`:
    Prints the version information and exits.

  * `-h`, `--help`:
    Prints a help message and exits.

  * `-p`, `--porcelain`:
    Switches the output that will be printed to the terminal to "porcelain" mode.
    This is meant to be useful for parsing for example during scripting or testing.

  * `-v`, `--verbose`:
    Increases the verbosity level of the logging.
    This option may be provided up to two times (increasing the logging to _info_ and _debug_, respectively).
    By default, the verbosity of coBib's CLI is set to _warning_ but if the TUI is started, logging will be increased to _info_ and redirected to `config.logging.logfile`.
    See also _cobib-config(5)_ for more details.

  * `-c`, `--config`=_PATH_:
    Run with an alternate configuration file at _PATH_.
    This value takes precedence over any other configuration file.
    See also _cobib-config(5)_ for more details.

  * `-l`, `--logfile`=_PATH_:
    Run with an alternate log file at _PATH_.
    The default verbosity level will be _info_ when logging to a file.
    The level can be increased using the `--verbose` option.

## SUBCOMMANDS

The builtin subcommands are documented at _cobib-commands(7)_.
In addition, the _cobib-tui(7)_ gets started when **no** subcommand is specified, like so:
```bash
$ cobib
```

Finally, _cobib-plugins(7)_ may implement and register their own subcommands.
Thus, the actual list of available commands can be found using the `--help`:
```bash
$ cobib --help
```

## ENVIRONMENT

  * _$COBIB_CONFIG_:
    Specifies the path to a configuration file.
    See _cobib-config(5)_ for more details.

  * _$EDITOR_:
    Specifies the editor program to use for the _cobib-edit(1)_ command.

## FILES

  * _$HOME/.config/cobib/config.py_:
    The configuration file.
    Refer to _cobib-config(5)_ for the documentation of the configuration options.

  * _$HOME/.local/share/cobib/literature.yaml_:
    The default location of the database file.
    This is a plain-text YAML file.
    For more details refer to _cobib-database(7)_.

## EXAMPLES

Before you can use coBib, you have to initialize your database.
You can change the location of the database in the configuration file; see _cobib-config(5)_.
Once you are happy, simply execute the following:

```bash
$ cobib init --git
```

The example above also initializes the git integration.
See _cobib-init(1)_ and _cobib-git(7)_ for more details.

Now you are ready to _cobib-add(1)_ or _cobib-import(1)_ entries into your database.
For an interactive experience, you can use the _cobib-tui(7)_:

```bash
$ cobib
```

## SEE ALSO

_cobib-commands(7)_, _cobib-config(5)_, _cobib-database(7)_, _cobib-filter(7)_, _cobib-git(7)_, _cobib-plugins(7)_, _cobib-tui(7)_

The quick usage references for each command using `--help` directly from the command-line.

The [online documentation][online-documentation] of the API references including usage examples.

The [repository][repository] for the source code and issue tracker.

[//]: # ( vim: set ft=markdown tw=0: )
