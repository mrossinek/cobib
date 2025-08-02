cobib-getting-started(7) -- how to get started with coBib
=========================================================

## DESCRIPTION

This is a guide how to get started with coBib.
This guide does not cover coBib's configuration, refer to _cobib-config(5)_ for that.

### Initializing the database

The first thing to do, is to initialize the _cobib-database(7)_.
This is done using the _cobib-init(1)_ command.
The location for the database is configured via the `config.database.file` location.
The default location is `~/.local/share/cobib/literature.yaml`.
To initialize it (and the optional git integration, see _cobib-git(7)_), run the following:
```bash
$ cobib init --git
```
The optional git-integration also needs to be enabled by setting `config.database.git = True`.

### Importing a bibliography

The _cobib-import(1)_ command can import a bibliography from another reference manager.
The only builtin backend currently is Zotero, see _cobib-importers(7)_ for more details.
To import a bibliography from there, simply run:
```bash
$ cobib import --zotero
```

Alternatively, one can always use _cobib-add(1)_ to add a bibliography from a `.bib` file:
```bash
$ cobib add --bibtex database.bib
```

### Modifying the database

New entries are added via the _cobib-add(1)_ command.
coBib has multiple builtin parser backends, see _cobib-parsers(7)_ for more details.
Here are some common examples:
```bash
$ cobib add --arxiv 1701.08213
$ cobib add --doi 10.1021/acs.jpclett.3c00330
$ cobib add --isbn 978-1-449-35573-9
```

Entries can be deleted using _cobib-delete(1)_, edited manually using _cobib-edit(1)_ or in bulk using _cobib-modify(1)_.

coBib can associated a _note_ file with each entry which can be managed using the _cobib-note(1)_ command.

Finally, an interactive review of the database can be performed using _cobib-review(1)_.

### Viewing the database

Besides reviewing, the database can be inspected using various commands.

The simplest way is to _cobib-list(1)_ the entries:
```bash
$ cobib list
```
This command also boast a powerful filtering mechanism which is described in detail in _cobib-filter(7)_.

Individual entries can be shown using _cobib-show(1)_:
```bash
$ cobib show MyLabel
```

Finally, the database can be searched using _cobib-search(1)_.

### Exporting entries

When it is time to write a paper or consume your references in some other form, they can be exported to a `.bib` file using _cobib-export(1)_:
```bash
$ cobib export -b out.bib
```

## SEE ALSO

_cobib(1)_, _cobib-config(5)_, _cobib-commands(7)_

The quick usage references for each command using `--help` directly from the command-line.

The [online documentation][online-documentation] of the API references including usage examples.

The [repository][repository] for the source code and issue tracker.

[//]: # ( vim: set ft=markdown tw=0: )
