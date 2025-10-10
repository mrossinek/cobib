cobib-zip(7) -- Zip exporter backend
====================================

## SYNOPSIS

`cobib export` `--zip` `--` _FILE_ [`--include-files|--skip-files`] [`--include-notes|--skip-notes`]

## DESCRIPTION

Exports entries to a Zip file.
More specifically, this gathers up the associated files and external notes of the to-be-exported entries into a single zip archive.

## OPTIONS

  * `--skip-files`:
    Skips file attachments from inclusion in the exported Zip archive.
    This takes precedence over the value of the `config.exporters.zip.skip_files` setting.

  * `--include-files`:
    Enforces the inclusion of file attachments in the exported Zip archive.
    This takes precedence over the value of the `config.exporters.zip.skip_files` setting.

  * `--skip-notes`:
    Skips external notes from inclusion in the exported Zip archive.
    This takes precedence over the value of the `config.exporters.zip.skip_files` setting.

  * `--include-notes`:
    Enforces the inclusion of external notes in the exported Zip archive.
    This takes precedence over the value of the `config.exporters.zip.skip_files` setting.

## EXAMPLES

```bash
$ cobib export --zip -- file.zip --include-files --include-notes
```

## SEE ALSO

*cobib(1)*, *cobib-export(1)*, *cobib-exporters(7)*

[//]: # ( vim: set ft=markdown tw=0: )
