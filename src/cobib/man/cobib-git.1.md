cobib-git(1) -- pass through to the database's git tracking
===========================================================

## SYNOPSIS

`cobib git` ...

## DESCRIPTION

If changes of the database are tracked using cobib-git(7), then this command passes through to git(1) at the database's location.
This makes it essentially equivalent to

```bash
$ git -C <path/to/cobib/database> ...
```

Benefits over the above include:
- not having to remember the database path
- access to cobib(1)'s base-level CLI arguments like `--config` or `--logfile`
- customization via the `PreGitCommand` and `PostGitCommand` cobib-event(7) hooks

## EXAMPLES

Show the latest change:
```bash
$ cobib git show HEAD
```

Check for uncommitted changes:
```bash
$ cobib git status
```

Browse the database's history:
```bash
$ cobib git log
```

## SEE ALSO

*cobib(1)*, *cobib-commands(7)*, *cobib-git(7)*

[//]: # ( vim: set ft=markdown tw=0: )
