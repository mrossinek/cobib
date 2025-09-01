"""coBib's global console instance.

See the suggestion in rich's documentation: https://rich.readthedocs.io/en/stable/console.html.
"""

from rich.console import Console

from cobib.config import config

console = Console(theme=config.theme.build())
