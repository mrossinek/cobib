cobib-edit(1) -- edit an entry
==============================

## SYNOPSIS

`cobib edit` [`-a|--add`] [`--preserve-files|--no-preserve-files`] _LABEL_

## DESCRIPTION

Edits an entry of the database.
The entry is specified by its _LABEL_.
Its contents are dumped in the easily readable YAML format and opened in the `config.commands.edit.editor` program.
Upon saving and closing that program, any changes to the entry (including a renaming if the _LABEL_ has been edited) are saved to the database.

Depending on the value of `config.commands.edit.preserve_files`, associated files of an entry will be renamed, too.
The value of this setting can be overwritten at runtime using the options below.

It is possible to _add_ entirely new entries (i.e. if _LABEL_ does not exist yet) by specifying the `--add` option.

## OPTIONS

  * `-a`, `--add`:
    Combined with a _LABEL_ that does **not** yet exist in the database, this opens an empty entry in the editor.

  * `--preserve-files`:
    If the entry's label has been edited, this ensures that the associated files are _preserved_, i.e. **NOT** renamed to match.

  * `--no-preserve-files`:
    If the entry's label has been edited, this enforces the renaming of associated files.

## ENVIRONMENT

  * _$EDITOR_:
    Specifies the editor program.
    Hard-coding the `config.commands.edit.editor` setting can overwrite this behavior.

## EXAMPLES

```bash
$ cobib edit Label
$ cobib edit --add NewLabel
$ cobib edit --preserve-files Label
$ cobib edit --no-preserve-files Label
```

## SEE ALSO

*cobib(1)*, *cobib-commands(7)*

[//]: # ( vim: set ft=markdown tw=0: )
