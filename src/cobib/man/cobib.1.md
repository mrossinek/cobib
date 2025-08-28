cobib(1) -- a console-based bibliography management tool
========================================================

## SYNOPSIS

`cobib` [`-p|--porcelain`] [`-v|--verbose`] [`-c|--config`=_PATH_] [`-l|--logfile`=_PATH_] [_SUBCOMMAND_] [_ARGS_ ...]<br>
`cobib` `-h|--help` <br>
`cobib` `--version`

## DESCRIPTION

coBib is a console-based bibliography management tool written in Python.
It maintains a plain-text database of literature references in YAML format and provides various subcommands to work with this database.
It also provides an interactive terminal user interface (see also *cobib-tui(7)*) to complement its command-line interface (see the [SUBCOMMANDS][] section below).

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
    See also *cobib-config(5)* for more details.

  * `-c`, `--config`=_PATH_:
    Run with an alternate configuration file at _PATH_.
    This value takes precedence over any other configuration file.
    See also *cobib-config(5)* for more details.

  * `-l`, `--logfile`=_PATH_:
    Run with an alternate log file at _PATH_.
    The default verbosity level will be _info_ when logging to a file.
    The level can be increased using the `--verbose` option.

## SUBCOMMANDS

The builtin subcommands are documented at *cobib-commands(7)*.
In addition, the *cobib-tui(7)* gets started when **no** subcommand is specified, like so:
```bash
$ cobib
```

Finally, *cobib-plugins(7)* may implement and register their own subcommands.
Thus, the actual list of available commands can be found using the `--help`:
```bash
$ cobib --help
```

## ENVIRONMENT

  * _$COBIB_CONFIG_:
    Specifies the path to a configuration file.
    See *cobib-config(5)* for more details.

  * _$EDITOR_:
    Specifies the editor program to use for the *cobib-edit(1)* command.

## FILES

  * _$HOME/.config/cobib/config.py_:
    The configuration file.
    Refer to *cobib-config(5)* for the documentation of the configuration options.

  * _$HOME/.local/share/cobib/literature.yaml_:
    The default location of the database file.
    This is a plain-text YAML file.
    For more details refer to *cobib-database(7)*.

## EXAMPLES

Before you can use coBib, you have to initialize your database.
You can change the location of the database in the configuration file; see *cobib-config(5)*.
Once you are happy, simply execute the following:

```bash
$ cobib init --git
```

The example above also initializes the git integration.
See *cobib-init(1)* and *cobib-git(7)* for more details.

Now you are ready to *cobib-add(1)* or *cobib-import(1)* entries into your database.
For an interactive experience, you can use the *cobib-tui(7)*:

```bash
$ cobib
```

## SEE ALSO

*cobib-config(5)*, *cobib-commands(7)*, *cobib-database(7)*, *cobib-filter(7)*, *cobib-getting-started(7)*, *cobib-git(7)*, *cobib-plugins(7)*, *cobib-tui(7)*

The quick usage references for each command using `--help` directly from the command-line.

The [online documentation][online-documentation] of the API references including usage examples.

The [repository][repository] for the source code and issue tracker.

[//]: # ( vim: set ft=markdown tw=0: )
