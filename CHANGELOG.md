# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
- complete rewrite to use a plain-text `yaml` database instead of `sqlite3`

### Removed
- `sqlite3` database

## [0.1] - 2019-04-29

### Added
- initial version with a basic `sqlite3`-based database


[Unreleased]: https://gitlab.com/mrossinek/deuterium/-/compare/v1.0.2...master
[1.0.2]: https://gitlab.com/mrossinek/cobib/-/tags/v1.0.2
[1.0.1]: https://gitlab.com/mrossinek/cobib/-/tags/v1.0.1
[1.0.0]: https://gitlab.com/mrossinek/cobib/-/tags/v1.0.0
[0.2]: https://gitlab.com/mrossinek/cobib/-/tags/v0.2
[0.1]: https://gitlab.com/mrossinek/cobib/-/tags/v0.1
