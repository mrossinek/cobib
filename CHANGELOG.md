# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- the `FORMAT/default_entry_type` option used for manual entry addition
- a **manual** insertion mode available through `edit -a new_label` and `add -l new_label`
- a ISBN-based parser for adding new entries (#45)

### Fixed
- support URLs in file field during `open` command (#47)
- the TUI no longer crashes when encountering long prompt inputs (#48)
- the `edit` command can handle labels which start with common substrings (#46)


## [2.3.4] - 2020-09-14

Pypi: https://pypi.org/project/cobib/2.3.4/

### Fixed
- another AUR package installation error


## [2.3.3] - 2020-09-14

Pypi: https://pypi.org/project/cobib/2.3.3/

### Fixed
- AUR package installation error

## [2.3.2] - 2020-09-10

Pypi: https://pypi.org/project/cobib/2.3.2/

### Added
- option to default to case-insensitive searching (`DATABASE/search_ignore_case`)

### Changed
- clearing the prompt, aborts the command execution

### Fixed
- search command correctly handles missing arguments in TUI (#43)

## [2.3.1] - 2020-09-10

Pypi: https://pypi.org/project/cobib/2.3.1/

### Fixed
- faulty Pypi package

## [2.3.0] - 2020-09-10

Pypi: https://pypi.org/project/cobib/2.3.0/

### Added
- Logging functionality has been added. The verbosity level can be controlled via `-v` (INFO) and `-vv` (DEBUG).
  As soon as the TUI starts, all logging output is redirected to `/tmp/cobib.log`.
- Command line argument `-l` or `--logfile` can be used to specify the output path of the log. This will overwrite the `/tmp/cobib.log` location.
- the `TUI/scroll_offset` setting was added. It defaults to `3` and behaves similar to Vim's `scrolloff` setting.
- Configuration validation has been added. This extends the logging functionality to support more runtime debug information.
- popup window support: stdout and stderr messages are presented in a popup similarly to the help window

### Changed
- `-v` command line argument now refers to `--verbose` rather than `--version`
- Performance of the `add` command has been improved by not refreshing the database when outside of the TUI.

### Fixed
- bug when resizing causes the window width to become greater than the buffer width (#39)
- do not escape special characters in labels (#40)
- avoid special character encoding in file paths

## [2.2.2] - 2020-08-13

Pypi: https://pypi.org/project/cobib/2.2.2/

### Fixed
- current line highlight if viewport is wider than buffer was not correctly reset
- the `ignore_non_standard_types` setting had no effect

## [2.2.1] - 2020-08-10

Pypi: https://pypi.org/project/cobib/2.2.1/

### Changed
- when wrapping the TUI lines, indent until after the label column (#26)
- renamed `default.ini` to `example.ini` in the documentation folder

### Fixed
- current line highlight after viewport width was not correctly reset
- correctly convert boolean configuration options (#34)
- fix crash of TUI in wrap command when viewport is empty (#37)
- default configuration settings are managed centrally and consistently (#35)


## [2.2.0] - 2020-07-12

Pypi: https://pypi.org/project/cobib/2.2.0/

### Added
- allow configuring the program used to `open` associated files
- prompt user before actually quitting CoBib (#33)
- implements the Search command (#7, !12)

### Fixed
- the default value of the `open` command was not set correctly


## [2.1.0] - 2020-06-14

Pypi: https://pypi.org/project/cobib/2.1.0/

### Added
- added half- and full-page scrolling (#22)

### Changed
- importing from `bibtex` data defaults to **not** ignored non-standard entry types (#28)
- suppress LaTex encoding warnings except when adding entries (#29)
- `Search` and `Select` print warnings to the prompt while not implemented

### Fixed
- `init` command ensures directory of database file exists
- remove window artefacts after `help` menu is closed (#20)
- configuration file detection was missing a user home expansion (#31)

## [2.0.0] - 2020-06-06

Pypi: https://pypi.org/project/cobib/2.0.0/

### Fixed
- respect sort order reversing and filter `XOR`ing from the TUI (#18)
- `edit` command on Mac OS (#19)

### Changed
- made `init` command safe against database overwriting
- TUI: list entries in reverse order by default (config: TUI/reverse_order)


## [2.0.0b4] - 2020-05-16

Pypi: https://pypi.org/project/cobib/2.0.0b4/

### Fixed
- reset viewport position when updating buffer


## [2.0.0b3] - 2020-05-16

Pypi: https://pypi.org/project/cobib/2.0.0b3/

### Fixed
- properly assert valid current line number


## [2.0.0b2] - 2020-05-16

Pypi: https://pypi.org/project/cobib/2.0.0b2/

### Fixed
- fixed TUI startup


## [2.0.0b1] - 2020-05-16

**Warning**: do NOT use! The TUI is broken in this release!

Pypi: https://pypi.org/project/cobib/2.0.0b1/

### Fixed
- TUI does not crash when opening an entry with no associated file
- correctly reset current line positions after filtering and editing


## [2.0.0b0] - 2020-04-28

Pypi: https://pypi.org/project/cobib/2.0.0b0/

### Changed
- _internal_: refactored the config into a class
- centralized the database hanlding to improve performance (#12,!9)

### Fixed
- the `Show` command does not break after scrolling the viewport (#13)


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


[Unreleased]: https://gitlab.com/mrossinek/cobib/-/compare/v2.3.4...master
[2.3.4]: https://gitlab.com/mrossinek/cobib/-/tags/v2.3.4
[2.3.3]: https://gitlab.com/mrossinek/cobib/-/tags/v2.3.3
[2.3.2]: https://gitlab.com/mrossinek/cobib/-/tags/v2.3.2
[2.3.1]: https://gitlab.com/mrossinek/cobib/-/tags/v2.3.1
[2.3.0]: https://gitlab.com/mrossinek/cobib/-/tags/v2.3.0
[2.2.2]: https://gitlab.com/mrossinek/cobib/-/tags/v2.2.2
[2.2.1]: https://gitlab.com/mrossinek/cobib/-/tags/v2.2.1
[2.2.0]: https://gitlab.com/mrossinek/cobib/-/tags/v2.2.0
[2.1.0]: https://gitlab.com/mrossinek/cobib/-/tags/v2.1.0
[2.0.0]: https://gitlab.com/mrossinek/cobib/-/tags/v2.0.0
[2.0.0b4]: https://gitlab.com/mrossinek/cobib/-/tags/v2.0.0b4
[2.0.0b3]: https://gitlab.com/mrossinek/cobib/-/tags/v2.0.0b3
[2.0.0b2]: https://gitlab.com/mrossinek/cobib/-/tags/v2.0.0b2
[2.0.0b1]: https://gitlab.com/mrossinek/cobib/-/tags/v2.0.0b1
[2.0.0b0]: https://gitlab.com/mrossinek/cobib/-/tags/v2.0.0b0
[2.0.0a2]: https://gitlab.com/mrossinek/cobib/-/tags/v2.0.0a2
[2.0.0a1]: https://gitlab.com/mrossinek/cobib/-/tags/v2.0.0a1
[1.1.0]: https://gitlab.com/mrossinek/cobib/-/tags/v1.1.0
[1.0.2]: https://gitlab.com/mrossinek/cobib/-/tags/v1.0.2
[1.0.1]: https://gitlab.com/mrossinek/cobib/-/tags/v1.0.1
[1.0.0]: https://gitlab.com/mrossinek/cobib/-/tags/v1.0.0
[0.2]: https://gitlab.com/mrossinek/cobib/-/tags/v0.2
[0.1]: https://gitlab.com/mrossinek/cobib/-/tags/v0.1
