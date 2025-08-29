cobib-man(1) -- read coBib's manual
===================================

## SYNOPSIS

`cobib man` [_PAGE_]

## DESCRIPTION

Read coBib's builtin manual pages.
This command mimics UNIX's _man(1)_ command but displays the man-page in Markdown format.
It is available on all installations of coBib even when the man-pages have not been compiled and installed separately.

When _PAGE_ is omitted, an index of all registered man-pages gets rendered.
They are printed in order of prioritization and categorization (for more details see *cobib-man(7)*).

Otherwise, _PAGE_ gets resolved to one of coBib's man-pages (you cannot view man-pages that are not part of coBib).
Partial man-page names can be used and will be resolved in prioritization order according to the index (see above).

## EXAMPLES

To view the index of man-pages:
```bash
$ cobib man
```

All of the following resolve to the *cobib(1)* man-page:
```bash
$ cobib man "cobib(1)"
$ cobib man cobib.1
$ cobib man cobib
```

A unique substring of a man-page name can be used, too.
Thus, the following will resolve to *cobib-getting-started(7)*:
```bash
$ cobib man start
```

To disambiguate man-pages with identical names in different sections, specify the suffix:
```bash
$ cobib man git    # resolves to *cobib-git(1)*
$ cobib man git.7  # resolves to *cobib-git(7)*
$ cobib man man    # resolves to *cobib-man(1)*
$ cobib man man.7  # resolves to *cobib-man(7)*
```

## SEE ALSO

*cobib(1)*, *cobib-commands(7)*, *cobib-man(7)*

[//]: # ( vim: set ft=markdown tw=0: )
