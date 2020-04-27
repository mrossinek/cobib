# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]


## [2.0.0a2] - 2020-04-27

Pypi: https://pypi.org/project/cobib/2.0.0a2/

### Added
- user configuration options for:
    - TUI colors
    - TUI key bindings
    - TUI default list arguments
- help window highlighting

### Changed
- sorting and filtering commands remain persistent when updating the list view


## [2.0.0a1] - 2020-04-23

Pypi: https://pypi.org/project/cobib/2.0.0a1/

### Added
- Added a basic curses-based TUI (#5,!7)

### Changed
- _internal_: refactored commands into separate module


## [1.1.0] - 2020-03-28

Pypi: https://pypi.org/project/cobib/1.1.0/

### Added
- add `FORMAT.month` configuration option to configure the default type for
    month fields (defaults to `int`) (#3,!4)
- escape special LaTeX characters (#2,!5)

### Fixed
- `list` no longer breaks with a `KeyError` when a queried field does not exist
    in any bibliography entry (!2)
- `--label` can now correctly overwrite the ID (#4,!3)

### Changed
- `set_config()` and global `CONFIG` exported to separate module


## [1.0.2] - 2020-01-12

Pypi: https://pypi.org/project/cobib/1.0.2/

Note: this removal is not seen as a MINOR version bump because this is
      essentially a long out-standing bug fix

### Removed/Fixed
- doi extraction from pdf files (476efc4f)
  - also removes the ability to add entries directly via pdf files


## [1.0.1] - 2020-01-12

Pypi: https://pypi.org/project/cobib/1.0.1/

### Changed
- metadata for pypi


## [1.0.0] - 2020-01-12

First MAJOR release. Also available via Pypi: https://pypi.org/project/cobib/1.0.0/
The project was renamed from `CReMa` to `CoBib`

### Added
- allow sorting the list output (2a5a94f1)
- crude and slow (!!!) zsh completion (9f28f441)
- support Darwin's `open` command

### Changed
- suppress list output when exporting
- add used tags to columns when listing
- sort YAML database entries by keys (d2af42d2)

### Fixed
- fixed arxiv parser (7ce3726f)


## [0.2] - 2019-09-02

Note: this release was not marked MAJOR because this is still a WIP and early
      alpha release.

### Added
- complete rewrite to use a plain-text `yaml` database instead of `sqlite3` !1

### Removed
- `sqlite3` database


## [0.1] - 2019-04-29

### Added
- initial version with a basic `sqlite3`-based database


[Unreleased]: https://gitlab.com/mrossinek/cobib/-/compare/v2.0.0a2...master
[2.0.0a2]: https://gitlab.com/mrossinek/cobib/-/tags/v2.0.0a2
[2.0.0a1]: https://gitlab.com/mrossinek/cobib/-/tags/v2.0.0a1
[1.1.0]: https://gitlab.com/mrossinek/cobib/-/tags/v1.1.0
[1.0.2]: https://gitlab.com/mrossinek/cobib/-/tags/v1.0.2
[1.0.1]: https://gitlab.com/mrossinek/cobib/-/tags/v1.0.1
[1.0.0]: https://gitlab.com/mrossinek/cobib/-/tags/v1.0.0
[0.2]: https://gitlab.com/mrossinek/cobib/-/tags/v0.2
[0.1]: https://gitlab.com/mrossinek/cobib/-/tags/v0.1
