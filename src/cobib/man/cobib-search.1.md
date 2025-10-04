cobib-search(1) -- search in the database
=========================================

## SYNOPSIS

`cobib search` [`-i|--ignore-case | -I|--no-ignore-case`] [`-l|--decode-latex | -L|--no-decode-latex`] [`-u|--decode-unicode | -U|--no-decode-unicode`] [`-z|--fuzziness=`_FUZZINESS_] [`-c|--context=`_CONTEXT_] [`--skip-files|--include-files`] [`--skip-notes|--include-notes`] _QUERY_ [_QUERY_ ...] [`--`] [_FILTER_ ...]

## DESCRIPTION

Searches in the database.
This command takes one or more _QUERY_ strings which are _regex(7)_ patterns matched against the (filtered) entries in the database.
Searches are performed against the *cobib-bibtex(7)* formatted entries rather than the raw database file.
Any matches are printed to the output.

In the most simplistic form, this command simply searches for the provided string in all entries:
```bash
$ cobib search Einstein
```
A more advanced example using a _regex(7)_-pattern could look like this:
```bash
$ cobib search "[Ee]instein"
```
This will match upper- and lower-case spellings of the word `Einstein`.

The example above can be achieved more simply by specifying the `--ignore-case` (or `-i`) option.
Case-insensitivity can even be enabled by default via the `config.commands.search.ignore_case` setting.
If that is done, `--no-ignore-case` (or `-I`) can be used to overwrite it once at runtime.

Note, that `--ignore-case` and `--no-ignore-case` do **not** get forwarded to `config.commands.search.grep`.
This is due to lacking guarantees on the naming of these arguments between different possible tools such as `grep`, `rg`, etc.
Instead, resolve to configure `config.commands.search.grep_args`.

There are even more options to tweak the matching behavior described in the [Approximate Searching] section below.

The search can be narrowed to a subset of the database using the *cobib-filter(7)* mechanism:
```bash
$ cobib search -i quantum -- ++year 2025
```

By default, matches are printed with 1 line of context above and below the actual match (with duplicate lines removed):
```bash
$ cobib search --ignore-case Einstein
einstein - 2 matches
├── 1:
│   └── @article{einstein,
└── 2:
    ├──  author = {Einstein, Albert},
    └──  doi = {http://dx.doi.org/10.1002/andp.19053221004},
```
This can be tweaked via the `config.commands.search.context` setting and the `--context` option at runtime:
```bash
$ cobib search --ignore-case --context 4 Einstein
einstein - 2 matches
├── 1:
│   └── @article{einstein,
└── 2:
    ├──  author = {Einstein, Albert},
    ├──  doi = {http://dx.doi.org/10.1002/andp.19053221004},
    ├──  journal = {Annalen der Physik},
    ├──  number = {10},
    └──  pages = {891--921},
```

### Approximate Searching

Because the search is done on the *cobib-bibtex(7)* output, the possible occurrence of LaTeX typesetting commands can make accurate searches difficult.
While _regex(7)_ patterns can deal with many such cases, writing them becomes increasingly complicated and cumbersome.
Therefore, this command provides a few additional means to make searches easier.

Some simple LaTeX sequences can be converted to Unicode characters when `--decode-latex` (or `-l`) is specified.
For example, this allows the following search to match `K{\"o}rper`:
```bash
$ cobib search --decode-latex Körper
```
This can be enabled by default via the `config.commands.search.decode_latex` setting.
If that is done, `--no-decode-latex` (or `-L`) can be used to overwrite it once at runtime.

Additionally, Unicode characters can be converted to a close ASCII equivalent when `--decode-unicode` (or `-u`) is specified.
This combines well with the `--decode-latex` option allowing for example the following to still match `K{\"o}rper`:
```bash
$ cobib search --decode-latex --decode-unicode Korper
```
This can be enabled by default via the `config.commands.search.decode_unicode` setting.
If that is done, `--no-decode-unicode` (or `-U`) can be used to overwrite it once at runtime.

Finally, one can even account for typos or other inaccuracies in the query or source through `--fuzziness` (or `-z`).
This requires the optional [regex](https://pypi.org/project/regex/) dependency to be installed.
Reusing the same example as above, the following search will still match:
```bash
$ cobib search --decode-latex --decode-unicode --fuzziness 2 Koprer
```
The default value of fuzziness is 0 but can be set via the `config.commands.search.fuzziness` setting.

### Associated files and notes

This command treats the `file` and `notes` data fields of an entry in a special way:
* files listed under `file` will be searched with the `config.commands.search.grep` command.
  Note, that the keyword arguments for the search command to not automatically apply to the external `grep` tool.
  The only argument that _always_ gets forwarded is the `--context`, but any other settings should be configured via `config.commands.search.grep_args`.
* the note file pointed to by `notes` will be read and its contents included in the *cobib-bibtex(7)* output against which _QUERY_ gets matched

This differing behavior also explains the reason for specifically tracking notes separately from files.
See *cobib-note(1)* for more details.

Both of the above behaviors are enabled by default but can be configured via the `config.commands.search.skip_files` and `config.commands.search.skip_notes`, respectively.
If that is done, the `--include_files` or `--skip-files` and `--include-notes` or `--skip-notes` options can be used to overwrite the configuration once at runtime.

## OPTIONS

  * `-c`, `--context=`_CONTEXT_:
    Specifies the number of lines to provide as context around search matches.
    This takes precedence over the value of the `config.commands.search.context` setting.

  * `-l`, `--decode-latex`:
    Enables the decoding of simple LaTeX sequences as Unicode characters.
    This takes precedence over the value of the `config.commands.search.decode_latex` setting.

  * `-L`, `--no-decode-latex`:
    Disables the decoding of simple LaTeX sequences as Unicode characters.
    This takes precedence over the value of the `config.commands.search.decode_latex` setting.

  * `-u`, `--decode-unicode`:
    Enables the decoding of Unicode characters to their closest ASCII equivalents.
    This takes precedence over the value of the `config.commands.search.decode_unicode` setting.

  * `-U`, `--no-decode-unicode`:
    Disables the decoding of Unicode characters to their closest ASCII equivalents.
    This takes precedence over the value of the `config.commands.search.decode_unicode` setting.

  * `-z`, `--fuzziness=`_FUZZINESS_:
    Specifies the number of fuzzy errors to allow while matching search results.
    This takes precedence over the value of the `config.commands.search.fuzziness` setting.
    Using this feature requires the optional [regex](https://pypi.org/project/regex/) dependency to be installed.

  * `-i`, `--ignore-case`:
    Makes the search case-insensitive.
    This takes precedence over the value of the `config.commands.search.ignore_case` setting.

  * `-I`, `--no-ignore-case`:
    Makes the search case-sensitive.
    This takes precedence over the value of the `config.commands.search.ignore_case` setting.

  * `--skip-files`:
    Skips searching of associated files found in the entries `file` field.
    This takes precedence over the value of the `config.commands.search.skip_files` setting.

  * `--include-files`:
    Enforces the inclusion of associated files found in the entries `file` field in the search results.
    This takes precedence over the value of the `config.commands.search.skip_files` setting.

  * `--skip-notes`:
    Skips searching of the associated note found in the entries `note` field.
    This takes precedence over the value of the `config.commands.search.skip_notes` setting.

  * `--include-notes`:
    Enforces the inclusion of the associated note found in the entries `note` field in the search results.
    This takes precedence over the value of the `config.commands.search.skip_notes` setting.

## EXAMPLES

Some basic examples:
```bash
$ cobib search einstein
$ cobib search --ignore-case einstein
```

The following will match results when they contain **at least** `quantum` or `advantage`:
```bash
$ cobib search quantum advantage
```
The following treats the two words as a single phrase:
```bash
$ cobib search "quantum advantage"
```
One can guard against different typesetting using a regex:
```bash
$ cobib search "quantum.?advantage"
```

One can filter the database to reduce the time to search.
Skipping searching of associated files will also speed up the search significantly.
```bash
$ cobib search --skip-files quantum -- --or ++year 2023 ++year 2024 ++year 2025
```

## SEE ALSO

*cobib(1)*, *cobib-note(1)*, *cobib-bibtex(7)*, *cobib-commands(7)*, _regex(7)_, [regex](https://pypi.org/project/regex/)

[//]: # ( vim: set ft=markdown tw=0: )
