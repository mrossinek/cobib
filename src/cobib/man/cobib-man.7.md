cobib-man(7) -- manual pages
============================

## SYNOPSIS

```toml
[project.entry-points."cobib.man"]
"cobib.1" = "cobib.man:_commands"
```

## DESCRIPTION

coBib comes with its own builtin man-pages (see *cobib-man(1)* for more details).

All available man-pages are registered via the `cobib.man` [entry-point](https://setuptools.pypa.io/en/latest/pkg_resources.html#entry-points).
This even allows *cobib-plugins(7)* to write and integrate their own man-pages.

The next two sections explain the following:

1. how man-pages are categorized into groups based on their [entry-point](https://setuptools.pypa.io/en/latest/pkg_resources.html#entry-points)
2. how coBib's man-pages are written

### CATEGORIZATION

Just like UNIX's _man(1)_ command, *cobib-man(1)* has a builtin prioritization for resolving what man-page to show.
For example, `cobib man git` will show the *cobib-git(1)* page, but `cobib man git.7` has to be used to access *cobib-git(7)*
because the `.1` section has a higher priority than the `.7` section.

The order of prioritization is apparent from the man-page index (which can be viewed using `cobib man`).
The nested list below indicates the available categories with their prioritization character (later referred to as `PRIO`) and category header (later referred to as _HEADER_).

1. `.1` section: _Commands_
    1. `A`: _Common_
    2. `B`: _Utility_
    3. `P`: _Plugin_ (only shown when *cobib-plugins(7)* are installed)
2. `.5` section: _Config_
3. `.7` section: _Miscellaneous_
    1. `A`: _Overview_
    2. `B`: _Info_
    3. `E`: _Exporters_
    3. `I`: _Importers_
    4. `P`: _Parsers_

Where a man-page fits in, depends on its [entry-point](https://setuptools.pypa.io/en/latest/pkg_resources.html#entry-points) configuration.
The structure should be as follows:
```toml
[project.entry-points."cobib.man"]
"NAME.SECTION" = "MODULE:PRIO_HEADER"
```

  * `NAME`:
    Should be a descriptive name of the man-page, e.g. `cobib-config`.

  * `SECTION`:
    Should be the man-page section (see also _man-pages(7)_. For coBib this will likely be 1, 5, or 7.

  * `MODULE`:
    Should be the Python module which contains the raw Markdown file, e.g. `cobib.man`.

  * `PRIO_HEADER`:
    Should be the prioritization character and all-lowercase header as per the list above.

When writing man-pages for a *cobib-plugins(7)*, consider using the following [entry-points](https://setuptools.pypa.io/en/latest/pkg_resources.html#entry-points):
* `P_plugin` in `.1`: for *cobib-commands(7)*
* `A_overview` in `.7`: for an overview of the plugin
* `E_exporters` in `.7`: for *cobib-exporters(7)*
* `I_importers` in `.7`: for *cobib-importers(7)*
* `P_parsers` in `.7`: for *cobib-parsers(7)*

Concrete examples of these cases are provided in the `cobib_dummy` [plugin](https://gitlab.com/cobib/cobib/-/tree/master/plugin/).

In rare cases, a single man-page might fit into more than one category, in which case multiple `PRIO_HEADER`s can be defined, for example like so:
```toml
[project.entry-points."cobib.man"]
"cobib-bibtex.7" = "cobib.man:I_importers.P_parsers"
```

### WRITING

coBib man-pages should be written in _markdown(7)_ format.
Specifically, coBib uses _ronn(1)_ to convert markdown files to man-pages readable with _man(1)_.
While any plugin is not forced to do the same, writing the man-pages in _markdown(7)_ ensures that they can be viewed with the *cobib-man(1)* command.
Therefore, it is recommended to follow the guidelines set out by the _ronn-format(7)_.

## SEE ALSO

*cobib(1)*, *cobib-man(1)*, *cobib-plugins(7)*

[//]: # ( vim: set ft=markdown tw=0: )
