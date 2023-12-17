"""coBib's `PresetFilter` selection screen.

This screen renders a Textual-`OptionList` with all the preset filters configured via
`config.tui.preset_filters` for the user to choose from.

.. warning::

   This module makes no API stability guarantees! Refer to `cobib.ui.components` for more details.
"""

from __future__ import annotations

from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import OptionList, Static
from typing_extensions import override

from cobib.config import config


class PresetFilter(OptionList):
    """coBib's custom `OptionList` which can be navigated with Vi-like bindings."""

    BINDINGS: ClassVar[list[Binding | tuple[str, str] | tuple[str, str, str]]] = [
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
    ]
    """
    | Key(s) | Description |
    | :- | :- |
    | j | Moves the cursor down. |
    | k | Moves the cursor up. |
    """


class PresetFilterScreen(ModalScreen[str]):
    """coBib's `PresetFilter` selection screen."""

    BINDINGS: ClassVar[list[Binding | tuple[str, str] | tuple[str, str, str]]] = [
        ("q", "abort", "Close"),
    ]
    """
    | Key(s) | Description |
    | :- | :- |
    | q | Aborts the selection. |
    """

    DEFAULT_CSS = """
        PresetFilterScreen {
            align: center middle;
        }

        #presets {
            width: 80%;
            max-height: 80%;
            background: $surface;
        }

        #help {
            color: $text-disabled;
            width: 80%;
            padding: 1 2;
            background: $surface;
        }
    """

    @override
    def compose(self) -> ComposeResult:
        yield Static(
            (
                "Select one of the preset filters configured via "
                "[yellow]config.tui.preset_filters[/yellow]. "
                "You can restore the default view by selecting the [yellow]NONE[/yellow] filter. "
                "You can abort the selection by pressing [yellow]q[/yellow]."
            ),
            id="help",
        )
        yield PresetFilter("NONE", *config.tui.preset_filters, id="presets")

    def action_abort(self) -> None:
        """Aborts the `PresetFilter` selection."""
        self.dismiss("")

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handles the `OptionList.OptionSelected` event.

        Args:
            event: the triggered event.
        """
        if event.option.prompt == "NONE":
            self.dismiss("list -r")
        else:
            self.dismiss(f"list {event.option.prompt}")
