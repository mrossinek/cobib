cobib-doi(7) -- DOI parser backend
==================================

## SYNOPSIS

`cobib add --doi` _DOI_

## DESCRIPTION

Adds an entry from the provided [DOI](https://www.doi.org/).
This is done by parsing the BibTeX data provided by the DOI API (see also _cobib-bibtex(7)_).

Additionally, an attempt is made at downloading the PDF of the article and saving it under `config.utils.file_downloader.default_location`.
To disable this feature by default, set `config.commands.add.skip_download = True`.
The `--force-download` and `--skip-download` options of the _cobib-add(1)_ command can be used to overwrite the configuration setting at runtime.

However, for an arbitrary DOI the PDF may not be available freely, so the success of this can vary greatly.
Being connected to a VPN of an institution that grants access will improve the success rate.

Furthermore, not all DOIs will resolve to a URL from which the PDF location can be determined automatically.
A manual aid can be provided via the `config.utils.file_downloader.url_map` setting.
This dictionary can map journal landing page URL patterns to PDF URL patterns.
See _cobib-config(5)_ for more details.

## EXAMPLES

```bash
$ cobib add --doi 10.1021/acs.jpclett.3c00330
$ cobib add --skip-download -d https://doi.org/10.1021/acs.jpclett.3c00330
```

## SEE ALSO

_cobib(1)_, _cobib-add(1)_, _cobib-parsers(7)_

[//]: # ( vim: set ft=markdown tw=0: )
