cobib-open(1) -- open associated files
======================================

## SYNOPSIS

`cobib open` [`-f|--field=`_FIELD_] _LABEL_ [_LABEL_ ...]

## DESCRIPTION

Opens associated files of one of more entries from the database.
The _fields_ that can be opened are configured via the `config.commands.open.fields` setting.
In addition to those, _FIELD_ can be set to `all` indicating that all associated files should be opened.

If `--field` is not specified and multiple fields could be opened, an interactive prompt is used to determine which field to open.
The following choices can be selected during the prompt:

  * `1|2|...`:
    The respective field from the enumerated list of options.

  * `all|...`:
    The respective group of files specified by that field.
    The groups are shown as `[...]` in the list of options.
    `all` indicates _all_ files.

  * `help`:
    Will print a shortened help at runtime.

  * `cancel`:
    Aborts the command.

As mentioned earlier, `--field` is a short-cut around this interactive prompt.
However, it only supports specifiers of the type `all|...` and not any numeric identifiers.

Any field will be opened using the `config.commands.open.command` command.

## OPTIONS

  * `-f`, `--field=`_FIELD_:
    The field to open.
    Use `all` to open all associated files or any of the field names configured by `config.commands.open.fields`.
    The default value includes `file` and `url`.

## EXAMPLES

```bash
$ cobib open Label1
$ cobib open -f all Label2
$ cobib open -f url Label1 Label2
```

## SEE ALSO

_cobib(1)_, _cobib-commands(7)_

[//]: # ( vim: set ft=markdown tw=0: )
