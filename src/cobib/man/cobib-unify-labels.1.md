cobib-unify-labels(1) -- unify the entry labels
===============================================

## SYNOPSIS

`cobib unify_labels` [`-a|--apply`]

## DESCRIPTION

Unifies the labels of all entries in the database.
This command is identical to a cobib-modify(1) command to format the `label` of all entries in the database according to the `config.database.format.label_default` setting.

By default, this command runs with the `--dry` option of cobib-modify(1).
Thus, it does not apply any changes, similar to the behavior of cobib-lint(1).
To actually apply the changes, specify the `--apply` option.

## OPTIONS

  * `-a`, `--apply`:
    When specified, the entries will actually be renamed.

## EXAMPLES

```bash
$ cobib unify_labels
$ cobib unify_labels --apply
```

## SEE ALSO

*cobib(1)*, *cobib-lint(1)*, *cobib-modify(1)*, *cobib-commands(7)*

[//]: # ( vim: set ft=markdown tw=0: )
