cobib-arxiv(7) -- arXiv parser backend
======================================

## SYNOPSIS

`cobib add --arxiv` _ARXIVID_

## DESCRIPTION

Adds an entry from the provided [arXiv](https://arxiv.org) ID.
This is done by manually parsing the XML data provided by the arXiv API.

Additionally, the PDF of the article will be downloaded and saved under `config.utils.file_downloader.default_location`.
To disable this feature by default, set `config.commands.add.skip_download = True`.
The `--force-download` and `--skip-download` options of the _cobib-add(1)_ command can be used to overwrite the configuration setting at runtime.

## EXAMPLES

```bash
$ cobib add --arxiv 1701.08213
$ cobib add --skip-download -a https://arxiv.org/abs/1701.08213
```

## SEE ALSO

_cobib(1)_, _cobib-add(1)_, _cobib-parsers(7)_

[//]: # ( vim: set ft=markdown tw=0: )
