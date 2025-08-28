cobib-arxiv(7) -- arXiv parser backend
======================================

## SYNOPSIS

`cobib add --arxiv` _ARXIVID_

## DESCRIPTION

Adds an entry from the provided [arXiv](https://arxiv.org) ID.
This is done by manually parsing the XML data provided by the arXiv API.

Additionally, the PDF of the article will be downloaded and saved under `config.utils.file_downloader.default_location`.
To disable this feature by default, set `config.commands.add.skip_download = True`.
The `--force-download` and `--skip-download` options of the *cobib-add(1)* command can be used to overwrite the configuration setting at runtime.

## EXAMPLES

```bash
$ cobib add --arxiv 1701.08213
$ cobib add --skip-download -a https://arxiv.org/abs/1701.08213
```

## SEE ALSO

*cobib(1)*, *cobib-add(1)*, *cobib-parsers(7)*

[//]: # ( vim: set ft=markdown tw=0: )
