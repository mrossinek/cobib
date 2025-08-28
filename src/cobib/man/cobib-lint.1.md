cobib-lint(1) -- lint the database
==================================

## SYNOPSIS

`cobib lint` [`-f|--format`]

## DESCRIPTION

Lints the database.
This loads the database file with a special logging formatter to redirect all warnings and stylistic formatting errors to the output.
Without any options, this is a simple tool to analyze the database format to stay up-to-date with changes across coBib versions.
Specifying the `--format` option will try to resolve all lint messages that can be fixed automatically.

## OPTIONS

  * `-f`, `--format`:
    When specified, those messages that are automatically resolvable will be applied to the database.

## EXAMPLES

```bash
$ cobib lint
$ cobib lint --format
```

## SEE ALSO

*cobib(1)*, *cobib-unify-labels(1)*, *cobib-commands(7)*, [Linting](https://en.wikipedia.org/wiki/Lint_(software))

[//]: # ( vim: set ft=markdown tw=0: )
