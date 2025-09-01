"""coBib's UIs.

coBib is designed with three user interfaces in mind:
- a command-line interface (short: CLI)
- an interactive shell for executing multiple commands in sequence
- a terminal user interface (short: TUI)
"""

from .cli import CLI as CLI
from .shell import Shell as Shell
from .tui import TUI as TUI
from .ui import UI as UI
