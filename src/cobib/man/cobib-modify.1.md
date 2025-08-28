cobib-modify(1) -- modify entries in bulk
=========================================

## SYNOPSIS

`cobib modify` [`--dry`] [`-a|--add | -r|--remove`] [`--preserve-files|--no-preserve-files`] [`-s|--selection`] _MODIFICATION_ [`--`] _FILTER_ [_FILTER_ ...]

## DESCRIPTION

Modifies entries of the database in bulk.
Rather than performing edits manually one at a time, this command applies a modification to a single data field to all entries matching a *cobib-filter(7)*.
This makes bulk modifications much simpler to apply and enables simple scripting.

The _MODIFICATION_ should be provided as a string of the form `<field>:<value>`, that is the name of the entry's data field to be modified and the new value it should take.
The `<value>` gets interpreted as a Python ["f"-string](https://docs.python.org/3/reference/lexical_analysis.html#formatted-string-literals).
This means that the current data of the entry being modified is available through variables taking the name of the respectively fields.
These placeholders can be used inside of `<value>`, for example like so: `"pages:{pages.replace('--', '-')}"`.
This replaces the contents of the `pages` field with the previous content but replacing a double-dash with a single-dash.

When using an undefined placeholder variable as part of `<value>` the resulting error will be handled gracefully by falling back to an empty string.
A warning and error message will be logged.
```bash
$ cobib modify "tags:{undefined}" -- ...
#> [WARNING] You tried to use an undefined variable. Falling back to an empty string.
#> [ERROR] name 'undefined' is not defined
```

Depending on the value of `config.commands.modify.preserve_files`, associated files of an entry will be renamed, too, if the entry's `label` was modified.
The value of this setting can be overwritten at runtime using the options below.

Rather than fully overwriting the existing data of `<field>`, it is possible to **add** or **remove** from it using the respective runtime options listed below.
The exact behavior is determined based on the type of data:
- numerical values are summed (with `--add`) and subtracted (with `--remove`)
- lists are appended to (with `--add`) and removed from (with `--remove`)
- string fields are concatenated with**OUT** any spaces (with `--add`) and can**NOT** be modified with `--remove`
- in combination with `--remove`, an empty `<value>` can be used to remove a data field entirely, for example like so:

```bash
$ cobib modify "tags:" --remove -- ...
```

Finally, specifying the `--dry` option will preview all modifications without actually applying them.

## OPTIONS

  * `--dry`:
    Runs the command in "dry" mode: previews all modifications without actually applying them.

  * `-a`, `--add`:
    Add/append the new `<value>` to the existing data field, rather than overwrite it.
    This is mutually exclusive with the `--remove` option.

  * `-r`, `--remove`:
    Remove/subtract the new `<value>` from the existing data field, rather than overwrite it.
    If `<value>` is _empty_, than the specified `<field>` will be removed entirely.
    This is mutually exclusive with the `--add` option.

  * `--preserve-files`:
    If the entry's label has been modified, this ensures that the associated files are _preserved_, i.e. **NOT** renamed to match.

  * `--no-preserve-files`:
    If the entry's label has been modified, this enforces the renaming of associated files.

  * `-s`, `--selection`:
    Switches from the *cobib-filter(7)* mechanism to interpreting the _FILTER_ arguments as a list of plain entry labels.
    This is not necessarily super useful for using from the command-line, but integrates well with the visual selection in the *cobib-tui(7)*!

## EXAMPLES

Adding or removing a specific tag from entries with matching labels:
```bash
$ cobib modify --add "tags:private" --selection -- Label1 Label2 ...
$ cobib modify --remove "tags:first_author" -- ++author Rossmannek
```

Removing underscores from entry labels:
```bash
$ cobib modify "label:{label.replace('_', '')}" -- ++label "\D+_\d+"
```

## SEE ALSO

*cobib(1)*, *cobib-commands(7)*

[//]: # ( vim: set ft=markdown tw=0: )
