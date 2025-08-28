cobib-isbn(7) -- ISBN parser backend
====================================

## SYNOPSIS

`cobib add --isbn` _ISBN_

## DESCRIPTION

Adds an entry from the provided ISBN.
This is done by parsing the BibTeX data provided by the [openlibrary API](https://openlibrary.org/dev/docs/api/books) (see also *cobib-bibtex(7)*).
Note, that the openlibrary API does not contain all ISBNs and potential server errors will be caught by the parser.

This parser does **not** support downloading a PDF version of the entry.

## EXAMPLES

```bash
$ cobib add --isbn 978-1-449-35573-9
```

## SEE ALSO

*cobib(1)*, *cobib-add(1)*, *cobib-parsers(7)*

[//]: # ( vim: set ft=markdown tw=0: )
