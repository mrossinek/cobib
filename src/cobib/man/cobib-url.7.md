cobib-url(7) -- URL parser backend
==================================

## SYNOPSIS

`cobib add --url` _URL_

## DESCRIPTION

Adds an entry from the provided URL.
This is done by checking the URL for a container identifier in the following order:

  1. arXiv ID (see _cobib-arxiv(7)_)
  2. DOI (see _cobib-doi(7)_)
  3. ISBN (see _cobib-isbn(7)_)

The moment any of the above identifiers are found inside of the URL, the respective parser is used to add an entry.

If no identifier is found as part of the URL string, the contents of the website pointed to by the URL are scanned.
From it, all DOIs are extracted and the most common one (if it occurs more often than once) is assumed to be the DOI of the article to be added.

## EXAMPLES

```bash
$ cobib add --url 978-1-449-35573-9
$ cobib add --url https://arxiv.org/abs/1701.08213
$ cobib add --url https://doi.org/10.1021/acs.jpclett.3c00330
$ cobib add --url https://www.nature.com/articles/s41467-019-10988-2
```

## SEE ALSO

_cobib(1)_, _cobib-add(1)_, _cobib-parsers(7)_

[//]: # ( vim: set ft=markdown tw=0: )
