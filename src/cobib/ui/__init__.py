"""coBib's UIs.

coBib is designed with two user interfaces in mind:
- a command-line interface (short: CLI)
- a terminal user interface (short: TUI)

Both of these, as well as some other common user-interface utilities, are part of this module.

In addition, coBib also has some shell helpers (see `cobib.utils.shell_helper`) which are exposed
via the separate `ShellHelper` interface (generally speaking those commands need to be prefixed with
an underscore, for example: `cobib _example_config`).
"""

from .cli import CLI as CLI
from .shell_helper import ShellHelper as ShellHelper
from .ui import UI as UI
