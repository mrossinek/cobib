"""coBib - the Console Bibliography.

# What is coBib?

coBib is a simple, command-line based bibliography management tool.
It is the result of the needs for a easy-to-use alternative to full-blown reference managers like
Mendeley or Zotero.
As such it follows some basic design goals:
* **plain-text database**: which means you get full access and control over the database.
* **git-integration**: as a benefit of the above, you can keep track of your database through
  version control.
* **centralized database, location-independent library**: this means, that coBib *only* manages the
  database file in a centralized fashion but allows you to spread the actual contents of your
  library across the entire file system (this is the major different to
  [papis](https://papis.readthedocs.io/en/latest/library_structure.html)).
* **command-line and TUI support**: all features are available through the command-line as well as a
  curses-based TUI.


# Installation

For all common purposes you can install coBib via `pip`:
```
pip install cobib
```
Note: Use `pip3` if you still have Python 2 installed.

## Arch Linux
coBib is packaged in the AUR.
* [cobib](https://aur.archlinux.org/packages/cobib/)
* [cobib-git](https://aur.archlinux.org/packages/cobib-git/)

## Windows
Windows is **NOT** supported!
This is due to the fact that [Python under Windows does not ship with the `curses` module][1].
However, if you are using Windows 10 you should be able to install and use coBib
within the Linux subsystem.

[1]: https://docs.python.org/3/howto/curses.html#what-is-curses


# Getting started

To get started, you must initialize the database:
```
cobib init
```

If you would like to enable the git-integration, you should run:
```
cobib init --git
```
*and* enable `config.database.git` (see also [configuration](#configuration)).


# Usage

## Adding new entries
You can now add new entries to your database (see also `cobib.commands.add`):
```
cobib add --bibtex some_biblatex_file.bib
cobib add --arxiv <some arXiv ID>
cobib add --doi <some DOI>
cobib add --isbn <some ISBN>
```

## Viewing your database and entries
You can view the contents of your database with (see also `cobib.commands.list`):
```
cobib list
```
You can show a specific entry with (see also `cobib.commands.show`):
```
cobib show <some entry label>
```
You can open an associated file of an entry with (see also `cobib.commands.open`):
```
cobib open <some entry label>
```
You can even search through your database with (see also `cobib.commands.search`):
```
cobib search "some text"
```

## Editing your database
You can delete an entry with (see also `cobib.commands.delete`):
```
cobib delete <some entry label>
```
You can edit an entry manually with (see also `cobib.commands.edit`):
```
cobib edit <some entry label>
```
You can also apply simple modifications to multiple entries at once with (see also
`cobib.commands.modify`):
```
cobib modify tags:private -- <some entry label> <another entry label> ...
```

## Exporting your database
You can export your database with (see also `cobib.commands.export`):
```
cobib export --bibtex my_bibliography.bib
cobib export --zip my_library.zip
```

## Integrated version control
If you have enabled the git-integration, you can undo and re-apply changes to your database with
(see also `cobib.commands.undo` and `cobib.commands.redo`):
```
cobib undo
cobib redo
```

## Getting help
Each subcommand provides additional help via:
```
cobib <subcommand> --help
```
and you can find extensive information in the online documentation (linked above) and the man-page:
```
man cobib
```

## TUI
Finally, you can also use coBib's TUI for a more interactive experience (see also `cobib.tui`), by
simply typing

    cobib


# Configuration

coBib gets configured via a Python object.
To get started you can simply copy the example configuration (`cobib.config.example`) and modify it
to your liking:
```
cobib _example_config > ~/.config/cobib/config.py
```
"""

import os
import subprocess

__version__ = "3.0.0a1"

if os.path.exists(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/../.git"):
    # if installed from source, append HEAD commit SHA to version info as metadata
    proc = subprocess.Popen(["git", "rev-parse", "HEAD"], stdout=subprocess.PIPE)
    git_revision, _ = proc.communicate()
    __version__ += "+" + git_revision.decode("utf-8")[:7]
