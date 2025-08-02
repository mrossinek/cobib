cobib-list(1) -- list entries
=============================

## SYNOPSIS

`cobib list` [`-s|--sort` _SORT_] [`-r|--reverse`] [`-l|--limit` _LIMIT_] [`-i|--ignore-case | -I|--no-ignore-case`] [`-l|--decode-latex | -L|--no-decode-latex`] [`-u|--decode-unicode | -U|--no-decode-unicode`] [`-z|--fuzziness=`_FUZZINESS_]  [`-x|--or`]  [_FILTER_ ...]

## DESCRIPTION

Lists entries from the database.
This command provides the means to view the contents of the database.
It provides the powerful _cobib-filter(7)_ mechanism which many other commands can leverage, too.

In its simplest form, the following list all entries that appear in the database in the order they were added:
```bash
$ cobib list
```

Some basic options exist to manipulate this list which are explained in more detail below.
One example showcasing them all is the following, which sorts the output by the _year_ field, reverses the order (i.e. sorts by year in descending order) and limits the output to 20 entries.
```bash
$ cobib list --sort year --reverse --limit 20
```

The remaining options affect the filter mechanism which is explained in detail in _cobib-filter(7)_.
All to say here is that the `-x|--or` option combines multiple filters using _logical OR_ rather than _logical AND_ operations.
Additionally, it is possible to make the filter matching approximate as explained in the next section.

### Approximate Filtering

Just like the _cobib-search(1)_ command can match search queries approximately, this command can match _cobib-filter(7)_ arguments approximately.

The most straight forward example is a case insensitive match using `--ignore-case` (or `-i`):
```bash
$ cobib list --ignore-case ++title quantum
```
This can be enabled by default via the `config.commands.list_.ignore_case` setting.
If that is done, `--no-ignore-case` (or `-I`) can be used to overwrite it once at runtime.

Similarly, simple LaTeX sequences can be converted to Unicode characters using `--decode-latex` (or `-l`).
For example, this allows the following filter to match `K{\"o}rper`:
```bash
$ cobib list --decode-latex Körper
```
This can be enabled by default via the `config.commands.list_.decode_latex` setting.
If that is done, `--no-decode-latex` (or `-L`) can be used to overwrite it once at runtime.

Additionally, Unicode characters can be converted to a close ASCII equivalent using `--decode-unicode` (or `-u`).
This combines well with the `--decode-latex` option allowing for example the following to still match `K{\"o}rper`:
```bash
$ cobib list --decode-latex --decode-unicode Korper
```
This can be enabled by default via the `config.commands.list_.decode_unicode` setting.
If that is done, `--no-decode-unicode` (or `-U`) can be used to overwrite it once at runtime.

Finally, one can even account for typos or other inaccuracies in the query or source through `--fuzziness` (or `-z`).
This requires the optional [regex](https://pypi.org/project/regex/) dependency to be installed.
Reusing the same example as above, the following filter will still match:
```bash
$ cobib list --decode-latex --decode-unicode --fuzziness 2 Koprer
```
The default value of fuzziness is 0 but can be set via the `config.commands.list_.fuzziness` setting.

## OPTIONS

  * `-s`, `--sort`=_SORT_:
    Sorts the output by field named _SORT_.

  * `-r`, `--reverse`:
    Reverses the order of the output.

  * `-l`, `--limit`=_LIMIT_:
    Limits the number of entries to list to _LIMIT_.

  * `-x`, `--or`:
    Combines multiple filter arguments with _logical OR_ rather than _logical AND_ operations.

  * `-i`, `--ignore-case`:
    Makes the filter matching case-insensitive.
    This takes precedence over the value of the `config.commands.list_.ignore_case` setting.

  * `-I`, `--no-ignore-case`:
    Makes the filter matching case-sensitive.
    This takes precedence over the value of the `config.commands.list_.ignore_case` setting.

  * `-l`, `--decode-latex`:
    Enables the decoding of simple LaTeX sequences as Unicode characters.
    This takes precedence over the value of the `config.commands.list_.decode_latex` setting.

  * `-L`, `--no-decode-latex`:
    Disables the decoding of simple LaTeX sequences as Unicode characters.
    This takes precedence over the value of the `config.commands.list_.decode_latex` setting.

  * `-u`, `--decode-unicode`:
    Enables the decoding of Unicode characters to their closest ASCII equivalents.
    This takes precedence over the value of the `config.commands.list_.decode_unicode` setting.

  * `-U`, `--no-decode-unicode`:
    Disables the decoding of Unicode characters to their closest ASCII equivalents.
    This takes precedence over the value of the `config.commands.list_.decode_unicode` setting.

  * `-z`, `--fuzziness=`_FUZZINESS_:
    Specifies the number of fuzzy errors to allow while matching filter arguments.
    This takes precedence over the value of the `config.commands.list_.fuzziness` setting.
    Using this feature requires the optional [regex](https://pypi.org/project/regex/) dependency to be installed.

## EXAMPLES

List entries containing `Quantum` in the title, sorted by year in descending order, limiting the output to 50 entries:
```bash
$ cobib list -r -s year -l 50 ++title Quantum
```


## SEE ALSO

_cobib(1)_, _cobib-commands(7)_, _cobib-filter(7)_

[//]: # ( vim: set ft=markdown tw=0: )
