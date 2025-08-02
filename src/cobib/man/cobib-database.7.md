cobib-database(7) -- database format
====================================

## SYNOPSIS

`$HOME/.local/share/cobib/literature.yaml`

## DESCRIPTION

coBib's bibliography data is stored in a single plain-text YAML file.
The default location is stated above, but it may be configured via the `config.database.file` setting (see also _cobib-config(5)_).

A few considerations went into the choice for this database format:

  * the plain-text format ensures that the data is human readable and is easily recovered, even if coBib were to not be available in the future
  * the centralization of all the bibliographic data allows an easy version control integration (see also _cobib-git(7)_)
  * the use of linking to externally associated files still allows flexibility in PDF management

### Contents

The contents of the YAML file are expected to be of the following form:
```yaml
---
Label1:
  ENTRYTYPE: article
  field: value
  listfield:
  - value 1
  - value 2
...
---
Label2:
  ENTRYTYPE: misc
  field: 10
  author:
  - first: Name
    last: Surname
...
```

The following details are important:

  * every entry is stored as its own YAML document with an explicit start (`---`) and end (`...`) marker
  * every entry should have _exactly one_ root node which represents its `label` in the database
  * it contains a dictionary-like structure matching _field_ names to their _values_
  * values can be strings, numbers, or lists
  * the `author` field can be a sequence of mappings.
    Refer to the documentation of `cobib.database.author.Author` for more details.

### Performance

Parsing large databases can become a performance bottleneck.
There are multiple tricks to improve performance:

  * Caching:
    coBib will cache parsed databases at the location specified by the `config.database.cache` setting.
    This is **enabled** by default but can be disabled by changing the above setting to `None`.

  * C-based parser:
    The YAML parser (see also _cobib-yaml(7)_) has a C-based implementation which is significantly faster than the Python-based one.
    This is **enabled** by default but can be disabled by setting `config.parsers.yaml.use_c_lib_yaml = False`.

  * Linting:
    If the database format is not entirely up-to-date with the latest defaults, some processes can slow the parsing down.
    The _cobib-lint(1)_ command can be used to identify and fix problems to improve parsing speed.

## SEE ALSO

_cobib(1)_, _cobib-config(5)_

[//]: # ( vim: set ft=markdown tw=0: )
