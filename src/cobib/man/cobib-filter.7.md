cobib-filter(7) -- filter mechanism
===================================

## SYNOPSIS

```
++title WORD
--title WORD
```

## DESCRIPTION

The *cobib-list(1)* command provides a filtering mechanism to narrow down the entries in a database.
While the *cobib-list(1)* will simply list the narrowed down list, other commands which act on one or more entries can leverage this filtering mechanism to specify the list of entries to act upon.
Examples of commands supporting this are *cobib-export(1)*, *cobib-modify(1)*, *cobib-review(1)*, and *cobib-search(1)*.

The basic syntax of a filter argument is as follows:
```
++title WORD
```
This filter will match only those entries whose `title` field contains the string `WORD`.
Therefore, this is a positively matching filter (indicated by the `++` prefix).
Negative match filtering are possible, too, using the `--` prefix:
```
--title WORD
```
I.e. this filter matches those entries whose `title` field does **not** contain the string `WORD`.

The filter arguments are registered at runtime.
Therefore, filter arguments exist for _all_ fields appearing in _any_ entry of the database.

Because no assertions are made on the content of the fields, all filter matching is done on strings.
Therefore, to list all entries from the year 2024, simply do the following:
```
++year 2024
```
As a consequence to string-based matching, the following filter will match any entry from a year containing `20` (e.g. `20XX`, `X20X`, or `XX20`).
```
++year 20
```

Multiple filter arguments combine using logical _AND_ operations.
Thus, the following matches only entries from the year `2024` containing `Quantum` in the title:
```
++year 2024 ++title Quantum
```
However, the *cobib-list(1)* command provides the `--or` (or `-x`) argument which switches to logical _OR_ operations for combining multiple filters.

It is also possible to filter on the mere existence or lack of a specific field by matching against an empty string:
```
++journal ""
--journal ""
```

Last but not least, the filter mechanism interprets the strings as a _regex(7)_ pattern.
This means, that the following will match all entries whose labels are of the form `"<non-digit chars>_<digits>"`:
```
++label "\D+_\d+"
```

Finally, the additional arguments of the *cobib-list(1)* can be used to further modify the filtering mechanism.
This includes case insensitivity, LaTeX and Unicode decoding, and fuzzy matching.

## SEE ALSO

*cobib(1)*, *cobib-list(1)*

[//]: # ( vim: set ft=markdown tw=0: )
