# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]


## [3.3.0] - 2021-10-04

Pypi: https://pypi.org/project/cobib/3.3.0/

### Added
- print Changelog since the last run version (cached in `config.logging.version`) (#82)
- the `AddCommand` now has a new `--update` option (#79,!41)
- the `_lint_database` utility now takes the `--format` argument, which automatically resolves all lint messages (#81,!42)
- the new `URLParser` (available via `cobib add --url <URL>` (#84,!44)
    - it attempts importing from a plain URL
    - simultaneously the arXiv, DOI, and ISBN parsers now also support URL containing a matching identifier directly
- the `--dry` argument of the `ModifyCommand` to prevent errors during large bulk modifications
* the `config.database.format.label_default` and `config.database.format.label_suffix` options (#85,!45)
    - labels will automatically be formatted according to the default option
    - if labels conflict with existing ones, the suffix option will be used for disambiguation
    - the `AddCommand` has a new `--skip-existing` option which disables automatic label disambiguation
    - use `cobib _unify_labels --apply` to unify all labels in your database
- subscribable events (#71,!46)
    - allows registering of hooks to be executed in certain situation
    - more information is provided at the [online documentation](https://mrossinek.gitlab.io/cobib/cobib/config/event.html)

### Changed
- when an unknown variable is encountered in the modification of the `modify` command it falls back to an empty string rather than the name of the attempted variable

### Removed
- the `-s` option of the `AddCommand` is no longer available. You need to write out `--skip-download`
- the `ID` filter argument on the `list` command (deprecated in v3.2.0 in favor of the `label` filter)


## [3.2.1] - 2021-07-15

Pypi: https://pypi.org/project/cobib/3.2.1/

### Fixed
- when adding multiple entries at once, continue adding after encountering a single duplicate (#83)


## [3.2.0] - 2021-06-26

Pypi: https://pypi.org/project/cobib/3.2.0/

### Added
- basic auto-downloading of PDF files for arXiv IDs and configured DOIs (#25,!35,!39):
    - the default download location can be configured via `config.utils.file_downloader.default_location`
    - on a per addition basis, this default can be overwritten via the `--path` keyword option of the `AddCommand`
    - if a file already exists in this location of the file system, the download will be skipped
    - download for DOI entries must configure URL patterns in `config.utils.file_downloader.url_map`
    - on a per addition basis, the entire automatic download can be skipped with `--skip-download`
- automatic journal abbreviations (#62,!36):
    - users can configure a list of journal abbreviations via `config.utils.journal_abbreviations`
    - if present, coBib will store the journal in its elongated form
    - a user can then automatically convert to abbreviated forms during exporting (see the new `--abbreviate` and `--dotless` arguments)
- Tentative Windows support by disabling the TUI
- a `--preserve-files` argument was added to the following commands. Unless it is given, these will delete/rename associated files of affected entries:
    - `DeleteCommand`
    - `EditCommand`
    - `ModifyCommand`

### Changed
- the `modifications` of a `ModifyCommand` get interpreted as f-strings (#77,!37):
    - available variables are the entry's label and data fields
- any `ListCommand` filter gets interpreted as a regex pattern (#76)

### Deprecated
- the `ID` filter argument was fully replaced by `label`, unifying the CLI API. Support will be dropped in v3.3.0

### Fixed
- Removed (most) duplication of log messages


## [3.1.1] - 2021-05-25

Pypi: https://pypi.org/project/cobib/3.1.1/

### Fixed
- Pypi package metadata


## [3.1.0] - 2021-05-24

Pypi: https://pypi.org/project/cobib/3.1.0/

### Added
- the YAML format of the database has been extended to support the following: (#55)
    - numbers can be stored as integers
    - the `ID` field is no longer required and will be properly inferred from the label
    - the following fields can be stored as lists: `file`, `tags`, `url`
- three new configuration options were added to complement the above list format options:
    - `config.database.stringify.list_separator.file`
    - `config.database.stringify.list_separator.tags`
    - `config.database.stringify.list_separator.url`
- the `_lint_database` shell utility has been added which can be used to detect possible improvements for the database
- the append-mode of the `ModifyCommand` was implemented (#60):
    - specifying `-a`/`--add` will add the modification value to the field of the entries rather than overwrite it
    - this can be used for string or list concatenation and even number addition on numeric fields

### Changed
- use file paths relative to user-home (achieved by replacing `os.path` with `pathlib`) (#69)
- the shell helper `_list_tags` has been renamed to `_list_labels`
- (DEV): the `logging` and `zsh_helper` modules have been relocated to the `cobib.utils` package
- `+` symbols will no longer be stripped from tags (this was a left-over artifact from pre-v1.0.0)

### Deprecated
- the `config.database.format.month` setting is deprecated in favor of proper three-letter code encoding to support common citation style macros (!34)

### Fixed
- renaming the label during the `edit` command does not leave the previous label entry behind:
    - a followup also ensured that renaming entries happens in-place (#75)
- the sorting of the `list` command


## [3.0.0] - 2021-04-10

Pypi: https://pypi.org/project/cobib/3.0.0/

- From now on, `coBib` is the official way of spelling!

### Added
- coBib's documentation is now generated by [`pdoc`](https://pdoc.dev/) and hosted at https://mrossinek.gitlab.io/cobib/cobib.html
- (DEV): the `cobib.database.Database`-Singleton has been added to centrally manage the bibliographic runtime data (!28)
- the new option `config.database.format.suppress_latex_warnings`
- the new option `config.commands.edit.editor` which takes precedence over the `$EDITOR` variable

### Changed
- the `INI`-style configuration is replaced with a `Python`-based configuration (#54,!25)
    - for guidance on how to migrate an existing configuration please read https://mrossinek.gitlab.io/programming/cobibs-new-configuration/
- (DEV): `cobib.parser.Entry` has been moved to `cobib.database.Entry`
- the `cobib.parsers` module has been extracted (prep for #49, !28)
- the filenames of the associated files are preserved when exporting to a Zip file
- when trying to add an entry with an existing label, the database is not written to and a warning is raised early
- month conversion and special character escaping are only done upon saving entries to the database
- the path to the default logfile can now be configured via `config.logging.logfile` and defaults to `~/.cache/cobib/cobib.log`

### Deprecated
- the `INI`-style configuration is deprecated
    - new configuration options will not be added to this style
    - only bugs which fully break usability will be fixed with regards to this configuration style
    - legacy-support will be fully removed on 1.1.2022

### Fixed
- the ZSH helper utilities now respect the `-c`, `-l`, and `-v` command line options
- the `RedoCommand` should only revert a previously `UndoCommand` operation (#65)
- the `SearchCommand` got some contexts improvements and correctly splits grep results
- unwrapping does not crash the TUI if the cursor was multiple lines below the new buffer height
- line continuation guides are not swallowed by current line highlighting
- ensure the TUI's top line does not become negative
- the TUI's handler for resizing events
- `JSONDecodeError`s thrown by the `ISBNParser` are caught and handled gracefully

### Removed
- the functions `read_database()` and `write_database()` are no longer available (!28)


## [2.6.1] - 2021-02-05

Pypi: https://pypi.org/project/cobib/2.6.1/

Note: [2.6.1] was not released from the `master`-branch, which resulted in a non-linear development.

### Changed
- `init --git` will not initialize a repository unless git has configured both, `name` and `email`

### Fixed
- TUI no longer crashes when aborting to quit (#64)


## [2.6.0] - 2020-12-31

Pypi: https://pypi.org/project/cobib/2.6.0/

### Added
- Git integration (#44, !20):
    - will automatically track any changes done to the database file with git
    - must be enabled by setting the `DATABASE/git` option to `True` **and** running `cobib init --git`
    - Note, that you must have at least set a `name` and `email` in the git config!
- Undo/Redo commands to operate on git history of the database (#59,!23)
    - for obvious reasons these commands require the Git integration (see above) to be enabled
- the `Prompt` command inside of the TUI:
    - allows executing arbitrary CoBib CLI commands
    - the default key binding is `:`
- the `Modify` command: (#60,!24)
    - allows bulk modification of multiple entries in a `<field>:<value>` format
    - for now, this will **always** overwrite the field with the new value!
    - an extension to appending values is planned for a later release
    - the set of entries to be modified can be specified just like with the `export` command through `list`-command filters or manual selection (by setting the `--selection` flag)

### Changed
- the viewport history is preserved correctly (#21,!22)
    - this allows performing a search while showing an entry and reverts back to the correct view after quitting the search
    - the changes mainly involved refactoring of the `cobib/tui` module
- the **positional** argument of the `modify` and `search` has been renamed internally from `list_arg` to `filter`
    - this should not have any visible effect to an end-user but may be relevant to developers

### Fixed
- gracefully handle multiple terminal sizing issues with regards to popups (#58)
- catch messages on `stdout` during deletion from TUI
- added missing help strings to the TUI help menu

### Removed
- The `--force` argument to the `init` command has now been removed (after being deprecated in v2.5.0).


## [2.5.0] - 2020-12-08

Pypi: https://pypi.org/project/cobib/2.5.0/

### Added
- support for multiple associated files (#42,!19)
- interactive menu when opening an entry with multiple associated files (!19)

### Deprecated
- The `--force` argument to the `init` command has been deprecated. I don't think there is any
  benefit to providing the user the option to nuke their database file from the CLI. Instead,
  they can simply edit the file manually.

### Fixed
- always store years as strings to be compatible with bibtexparser
- handle invalid arXiv or DOI IDs gracefully (#57)


## [2.4.1] - 2020-11-01

Pypi: https://pypi.org/project/cobib/2.4.1/

### Fixed
- ISBN parser was missing the ENTRYTYPE and did not use strings for number fields
- the ISBN parser can now handle empty entries (#53)
- the TUI will not crash on stdout/stderr messages exceeding the window width
- the TUI respects quoted strings in the prompt handler (#52)


## [2.4.0] - 2020-10-14

Pypi: https://pypi.org/project/cobib/2.4.0/

### Added
- the `FORMAT/default_entry_type` option used for manual entry addition
- a **manual** insertion mode available through `edit -a new_label` and `add -l new_label`
- a ISBN-based parser for adding new entries (#45)
- the TUI-based `select` command (and corresponding settings) (#8,!18)
- the `--selection` argument for the `export` command (!18)

### Changed
- TUI color highlighting is now prioritized (!17)

### Fixed
- support URLs in file field during `open` command (#47)
- the TUI no longer crashes when encountering long prompt inputs (#48)
- the `edit` command can handle labels which start with common substrings (#46)
- support multiple ANSI colors on a single line (#50)


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
- remove window artifacts after `help` menu is closed (#20)
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
- centralized the database handling to improve performance (#12,!9)

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


[Unreleased]: https://gitlab.com/mrossinek/cobib/-/compare/v3.3.0...master
[3.3.0]: https://gitlab.com/mrossinek/cobib/-/compare/v3.3.0
[3.2.1]: https://gitlab.com/mrossinek/cobib/-/compare/v3.2.1
[3.2.0]: https://gitlab.com/mrossinek/cobib/-/compare/v3.2.0
[3.1.1]: https://gitlab.com/mrossinek/cobib/-/compare/v3.1.1
[3.1.0]: https://gitlab.com/mrossinek/cobib/-/compare/v3.1.0
[3.0.0]: https://gitlab.com/mrossinek/cobib/-/compare/v3.0.0
[2.6.1]: https://gitlab.com/mrossinek/cobib/-/compare/v2.6.1
[2.6.0]: https://gitlab.com/mrossinek/cobib/-/tags/v2.6.0
[2.5.0]: https://gitlab.com/mrossinek/cobib/-/tags/v2.5.0
[2.4.1]: https://gitlab.com/mrossinek/cobib/-/tags/v2.4.1
[2.4.0]: https://gitlab.com/mrossinek/cobib/-/tags/v2.4.0
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
