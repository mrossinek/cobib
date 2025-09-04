cobib-add(1) -- add entries
===========================

## SYNOPSIS

`cobib add` [`-l|--label` _LABEL_] [`--disambiguation` _ACTION_] [`-f|--file` _FILE_ ...] [`-p|--path` _PATH_] [`--skip-download|--force-download`] [`--<PARSER>` _SOURCE_] [`--`] [_TAGS_ ...]

## DESCRIPTION

Adds entries to the database.
This is the main command to insert new entries into the database.
For migrating from another bibliography manager, look at *cobib-import(1)* instead,
which is a more simplified entry addition procedure that does not make any modifications other than ensuring unique labels.
In contrast, this *cobib-add(1)* command will parse every entry individually, possibly prompting for user interaction in the process.

Generally speaking, entries can be added in one of two ways:

1. using a _parser_ backend (via the `--<PARSER>` option)
2. manually using coBib's internal YAML format

### Parser-based addition

Multiple parser backends are built into coBib but to support plugins, all of them are registered (at runtime) in a **mutually exclusive** group of keyword arguments.
Thus, entries can only be added from one backend at a time.
Below is a quick overview of the builtin backends:
```bash
$ cobib add --arxiv "some arXiv ID"
$ cobib add --bibtex some_biblatex_file.bib
$ cobib add --doi "some DOI"
$ cobib add --isbn "some ISBN"
$ cobib add --url "some URL"
$ cobib add --yaml some_cobib_yaml_file.yaml
```

The full list of available backends can be seen in the output of:
```bash
$ cobib add --help
```

### Manual addition

Rather than relying on a parser, an entry can be created manually using the `--label` option:
```bash
$ cobib add --label "some_new_label"
```

This will trigger the *cobib-edit(1)* command for a manual addition.
The benefit of using this interface rather than the edit command directly, is the combination with the additional options listed below.

### Notes on the configuration dependence

Since this command adds new entries to the database, its outcome can be affected by some configuration settings.
In particular, the values of _config.database.stringify_ (see *cobib-config(5)*) affect how certain fields are converted to/from strings.
For example, _config.database.stringify.list_separator.file_ defaults to comma-separated values.
But you should update this setting **before** adding entries if you use another separator (for example a semicolon) like so:
```python
from cobib import config

config.database.stringify.list_separator.file = "; "
```


## OPTIONS

  * `-l`, `--label`=_LABEL_:
    Specifies the _label_ of the new entry being added.
    Specifying this option on its own triggers the manual entry addition.
    Combining it with a `--<PARSER>` overwrites the automatically determined _label_.
    Note, that the combined mode only makes sense when a single entry is being added by the parser.
    See also [Label disambiguation][] for more details.

  * `--disambiguation`=_ACTION_:
    Pre-determines the reply to a [Label disambiguation][] process (if one were to start).
    _ACTION_ may be one of the following values: `keep`, `replace`, `update`, `disambiguate`.

  * `-f`, `--file`=_FILE_ ...:
    Specifies one (or more) files to attach to the newly added entry.
    These can be later found in the entry's _file_ field.

  * `-p`, `--path`=_PATH_:
    The path in which to store any automatically downloaded files.
    This takes precedence over the _config.utils.file_downloader.default_location_ setting.

  * `--skip-download`:
    Skips the attempt to automatically download the PDF of the entry (if the chosen backend supports it).
    This takes precedence over the _config.commands.add.skip_download_ setting.

  * `--force-download`:
    Forces the attempt to automatically download the PDF of the entry (if the chosen backend supports it).
    This takes precedence over the _config.commands.import\_.skip_download_ setting.

  * `--<PARSER>`=_SOURCE_:
    Specifies the _parser_ to use and tells it to parse the contents of _SOURCE_.

  * _TAGS_:
    Any positional arguments are interpreted as _tags_ and are added verbatim to the entry's _tags_ field.

## NOTES

The _label_ of an entry is determined automatically based on the `config.database.format.label_default` setting.
By default, this does not change the suggested labels of the backends other than ensuring ASCII characters.
However, its value may be set to automatically infer a label based on the entry's data, e.g.
```python
config.database.format.label_default = "{unidecode(author[0].last).replace('-', '').replace(' ', '')}{year}"
```
The example above will use the surname of the last author and concatenate it with the publication year.

### Label disambiguation

When the _label_ of an entry being added clashes with an already existing entry in the database, an interactive process is triggered to resolve the conflict.
This process is called _label disambiguation_.

When this happens, a side-by-side comparison of the existing and new entry are presented and an interactive prompt asks how to proceed.
The following choices exist as an _ACTION_:

  * `keep`:
    Keeps the existing entry and skips the addition of the new one.
    This is the default action to prevent data loss.
    Selecting this action on the last clashing entry automatically triggers the addition of the new entry under a disambiguated label.

  * `replace`:
    Replaces the existing entry.

  * `update`:
    Takes the existing entry and combine it with all the information found in the new one.
    Existing fields and associated files will be overwritten.
    As an example, this feature is useful when updating a previously added pre-print from _arXiv_ with the peer-reviewed published article.

  * `disambiguate`:
    Keeps all existing entries and adds the new entry under a variant of the _label_ to disambiguate it from any existing ones.
    The disambiguation is done using the `config.database.format.label_suffix`, defaulting to `_a`, `_b`, etc. suffixes.
    Note, that applies the disambiguation **immediately** without showing any possibly remaining entries with related labels.

  * `cancel`:
    Cancels the entire process of entry addition.
    Use this if you realize that you already have the entry in your database and do not wish to add a duplicate entry.

The entire disambiguation process is iterative in the case that multiple disambiguation suffixes have to be tried.

## EXAMPLES

Add tags to the newly added entries:
```bash
$ cobib add --bibtex references_quantum_computing.bib -- new "quantum computing"
```

Associate local files with a newly added entry:
```bash
$ cobib add --doi "some DOI" --file /path/to/my/file.pdf /path/to/another/file.pdf
```

Overwrite the path in which to store the downloaded PDF of an article:
```bash
$ cobib add --arxiv "some arXiv ID" --path /path/to/my/papers/
```

Customize the label to give an entry:
```bash
$ cobib add --isbn "some ISBN" --label Author2025
```

Bypass the [Label disambiguation][] process by providing the action upfront:
```bash
$ cobib add --doi "some DOI" --label MyLabel2023 --disambiguation "update"
```

## SEE ALSO

*cobib(1)*, *cobib-commands(7)*, *cobib-parsers(7)*

[//]: # ( vim: set ft=markdown tw=0: )
