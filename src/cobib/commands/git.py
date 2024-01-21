"""coBib's Git command.

This command is a simple pass through to the `git` executable, running inside the folder of coBib's
database (i.e. it is equivalent to running `git -C <path/to/cobib/database> <whatever arguments>`).
It exists solely for convenience since the above can be cumbersome to type out and specifying a
shell alias only works when coBib is used for a single database location (otherwise one needs one
alias for each database).

.. note::

   This command is not available from within the TUI because the generated output is not dealt with
   very nicely (yet? 🤔)

Below are a few example use cases.

### Checking the latest change
```
cobib git show HEAD
```

### Checking for uncommitted changes
```
cobib git status
```

### Browsing the entire history
```
cobib git log
```

### Pushing or pulling the recent changes
```
cobib git push origin master
cobib git pull origin master
```

### This also works with coBib-level keyword arguments:

```
cobib -c my_other_config.py git show HEAD
cobib -l my_log_file.txt git log
```

<hr/>

Of course, you have the full power of git at your fingertips, so there really are no limits to what
you can do.
"""

from __future__ import annotations

import argparse
import logging
import subprocess

from typing_extensions import override

from cobib.config import Event, config
from cobib.utils.rel_path import RelPath

from .base_command import ArgumentParser, Command

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


class GitCommand(Command):
    """The Git Command.

    This command ignores all arguments passed to it and instead forwards them to the `git`
    executable for further processing.
    """

    name = "git"

    @override
    @classmethod
    def init_argparser(cls) -> None:
        parser = ArgumentParser(prog="git", description="Git subcommand parser.")
        parser.add_argument("git_args", nargs=argparse.REMAINDER, help="the arguments to git")
        cls.argparser = parser

    @override
    @classmethod
    def _parse_args(cls, args: tuple[str, ...]) -> argparse.Namespace:
        largs = super()._parse_args(())
        largs.git_args = args
        return largs

    @override
    def execute(self) -> None:
        git_tracked = config.database.git
        if not git_tracked:
            msg = (
                "You must enable coBib's git-tracking in order to use the `Git` command."
                "\nPlease refer to the documentation for more information on how to do so."
            )
            LOGGER.error(msg)
            return

        file = RelPath(config.database.file).path
        root = file.parent
        if not (root / ".git").exists():
            msg = (
                "You have configured, but not initialized coBib's git-tracking."
                "\nPlease consult `cobib init --help` for more information on how to do so."
            )
            LOGGER.error(msg)
            return

        LOGGER.debug("Starting Git command.")

        Event.PreGitCommand.fire(self)

        subprocess.run(["git", "-C", root, *self.largs.git_args], check=False)

        Event.PostGitCommand.fire(self)
