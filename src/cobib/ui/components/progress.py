"""coBib's progress widget.

This widget is a simple wrapper around textual's
[`ProgressBar`](https://textual.textualize.io/widgets/progress_bar/) widget to ensure a more unified
handling alongside rich's
[`Progress`](https://rich.readthedocs.io/en/stable/reference/progress.html) interface.

.. warning::

   This widget (used by the `cobib.utils.file_downloader.FileDownloader`) is not on par with the
   progress display of the CLI. Future improvements are imminent.

   For more information refer to [this issue](https://gitlab.com/cobib/cobib/-/issues/112).

.. warning::

   This module makes no API stability guarantees! Refer to `cobib.ui.components` for more details.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.widgets import ProgressBar

if TYPE_CHECKING:
    from ..tui import TUI


class Progress(ProgressBar, can_focus=False, can_focus_children=False):
    """coBib's progress widget."""

    console: TUI
    """The running TUI instance."""

    # TODO: add proper styling and figure out why this does not refresh properly
