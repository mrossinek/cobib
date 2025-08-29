cobib-getting-started(7) -- how to get started with cobib(1)
============================================================

## DESCRIPTION

This is a guide how to get started with coBib.
This guide does not cover coBib's configuration, refer to *cobib-config(5)* for that.

### Initializing the database

The first thing to do, is to initialize the *cobib-database(7)*.
This is done using the *cobib-init(1)* command.
The location for the database is configured via the `config.database.file` location.
The default location is `~/.local/share/cobib/literature.yaml`.
To initialize it (and the optional git integration, see *cobib-git(7)*), run the following:
```bash
$ cobib init --git
```
The optional git-integration also needs to be enabled by setting `config.database.git = True`.

### Importing a bibliography

The *cobib-import(1)* command can import a bibliography from another reference manager.
The only builtin backend currently is Zotero, see *cobib-importers(7)* for more details.
To import a bibliography from there, simply run:
```bash
$ cobib import --zotero
```

Alternatively, one can always use *cobib-add(1)* to add a bibliography from a `.bib` file:
```bash
$ cobib add --bibtex database.bib
```

### Modifying the database

New entries are added via the *cobib-add(1)* command.
coBib has multiple builtin parser backends, see *cobib-parsers(7)* for more details.
Here are some common examples:
```bash
$ cobib add --arxiv 1701.08213
$ cobib add --doi 10.1021/acs.jpclett.3c00330
$ cobib add --isbn 978-1-449-35573-9
```

Entries can be deleted using *cobib-delete(1)*, edited manually using *cobib-edit(1)* or in bulk using *cobib-modify(1)*.

coBib can associate a _note_ file with each entry which can be managed using the *cobib-note(1)* command.

Finally, an interactive review of the database can be performed using *cobib-review(1)*.

### Viewing the database

Besides reviewing, the database can be inspected using various commands.

The simplest way is to *cobib-list(1)* the entries:
```bash
$ cobib list
```
This command also boast a powerful filtering mechanism which is described in detail in *cobib-filter(7)*.

Individual entries can be shown using *cobib-show(1)*:
```bash
$ cobib show MyLabel
```

Finally, the database can be searched using *cobib-search(1)*.

### Exporting entries

When it is time to write a paper or consume your references in some other form, they can be exported to a `.bib` file using *cobib-export(1)*:
```bash
$ cobib export -b out.bib

```

### Learning more

coBib comes with a builtin manual that can be read using *cobib-man(1)*.
Additionally, all *cobib-commands(7)* support the `--help` argument for a quick reference of their supported arguments.

## SEE ALSO

*cobib(1)*, *cobib-config(5)*, *cobib-commands(7)*

The [online documentation](https://cobib.gitlab.io/cobib/cobib.html) of the API references including usage examples.

The [repository](https://gitlab.com/cobib/cobib) for the source code and issue tracker.

[//]: # ( vim: set ft=markdown tw=0: )
