cobib-shell(7) -- coBib's interactive shell
===========================================

## SYNOPSIS

`cobib --shell`

## DESCRIPTION

Sometimes the full *cobib-tui(7)* can be too complex of an interface when wanting to perform a sequence of rather simple tasks.
When this is the case, a simple interactive shell can suffice, which is exactly what this shell-UI provides.

In essence, it is an interactive prompt allowing multiple *cobib-commands(7)* to be executed in sequence using the standard command-line interface (CLI) synopsis.
This is especially useful when combined with additional arguments like a custom *cobib-config(5)* (`--config`) as it avoids having to re-load the config.
It can also speed up certain tasks because the *cobib-database(7)* does not need to be re-parsed either.

### Additional commands

In addition to the *cobib-commands(7)*, the shell provides the following controls:

  * `exit`:
    Quits the interactive shell (the same as `quit`).

  * `help`:
    An alias for `man cobib-shell.7`.

  * `quit`:
    Quits the interactive shell (the same as `exit`).

## EXAMPLES

```bash
$ cobib --shell
$ cobib -s --config path/to/some/config.py
```

## SEE ALSO

*cobib(1)*

[//]: # ( vim: set ft=markdown tw=0: )
