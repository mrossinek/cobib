cobib-zotero(7) -- zotero importer backend
==========================================

## SYNOPSIS

`cobib import --zotero` [`--`] [`--no-cache`] [`--user-id` _USERID_] [`--api-key` _APIKEY_]

## DESCRIPTION

Imports the bibliography from [Zotero](https://www.zotero.org).
This importer is registered inside the _cobib-import(1)_ command.
In its simplest form, it is executed like so:
```bash
$ cobib import --zotero
```


Normally, this command will only need to be executed once, but for convenience, the OAuth authentication tokens provided by the Zotero API are cached (at `config.logging.cache`).

## OPTIONS

  * `--no-cache`:
    Disables the cache of the OAuth authentication tokens.

  * `--user-id`=_USERID_:
    Provides the user ID of the Zotero bibliography to import.
    If this user ID points to a publicly accessible library, no OAuth authentication will be required.
    Otherwise, the `--api-key` argument is also required.

  * `--api-key`=_APIKEY_:
    Provides the Zotero API key to use instead of a new OAuth authentication process.

## EXAMPLES

The following example imports a publicly accessible library with 2 entries:
```bash
cobib import --zotero -- --user-id 8608002
```

## SEE ALSO

_cobib(1)_, _cobib-import(1)_, _cobib-importers(7)_, [Zotero](https://www.zotero.org)

[//]: # ( vim: set ft=markdown tw=0: )
