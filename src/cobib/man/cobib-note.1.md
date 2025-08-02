cobib-note(1) -- take notes for an entry
========================================

## SYNOPSIS

`cobib note` _LABEL_ [_ACTION_]

## DESCRIPTION

Interact with the note associated with an entry.
Every entry can have a note file associated with it, the location of which is stored in the `note` field.
This command provides the means to interact with this note.

Notes are handled specially during a _cobib-search(1)_, because their content is searched directly by cobib rather than relying on an external `config.commands.search.grep` program as is done for associated files.
At the same time, the actual database is kept clean from possibly long text passages and editing of notes can be done outside of cobib-edit(1) commands.

The following options exist for _ACTION_:

  * `edit`:
    Opens the note using `config.commands.edit.editor` for editing.
    This is the default value.

  * `show`:
    Dumps the contents of the note.

  * `delete`:
    Deletes the associated note.

The default location for notes is in the same folder as the `config.database.file` using the entry's _LABEL_ as the filename and `config.commands.note.default_filetype` as the filetype.
Of course, a custom path can be stored in the `note` field, too, but if it is outside the database's folder, the _cobib-git(7)_ integration will not track the note file.

## EXAMPLES

```bash
$ cobib note Label1 edit
$ cobib note Label1 show
$ cobib note Label1 delete
```

## SEE ALSO

_cobib(1)_, _cobib-edit(1)_, _cobib-search(1)_, _cobib-commands(7)_, _cobib-git(7)_

[//]: # ( vim: set ft=markdown tw=0: )
