"""coBib's Rich-Textual progress integration.

The `Progress` utility provided by this module either constructs a `rich.progress.Progress` object
or a custom textual widget to display a rich-progress indicator and update it accordingly. This was
favored over using textual's `textual.widgets.ProgressBar` to re-implement rich's more flexible
`rich.progress.Progress` displaying capabilities.
"""

from __future__ import annotations

import logging
from typing import Any

from rich.progress import Progress as RichProgress
from rich.progress import ProgressColumn, TaskID
from textual.app import ComposeResult
from textual.containers import HorizontalGroup
from textual.widgets import Label, ProgressBar
from typing_extensions import override

from .context import get_active_app

LOGGER = logging.getLogger(__name__)


class Progress:
    """A utility class to construct either a `rich` or `textual` progress indicator."""

    @staticmethod
    def initialize(*columns: str | ProgressColumn, **kwargs: Any) -> RichProgress | TextualProgress:
        """Initializes a new progress indicator.

        When `get_active_app` returns a `textual` App, this will construct a `TextualProgress`
        widget, otherwise it falls back to constructing a `rich.progress.Progress` object.

        Args:
            columns: the columns to include in the progress indicator.
            kwargs: any keyword arguments.

        Returns:
            The new progress indicator.
        """
        app = get_active_app()
        if app is None:
            return RichProgress(*columns, **kwargs)

        if len(columns) > 0:
            LOGGER.warning("Ignoring custom columns for the TextualProgress.")  # pragma: no cover

        return TextualProgress()


class TextualProgress(HorizontalGroup):
    """coBib's Frankenstein Rich-Textual progress widget."""

    DEFAULT_CSS = """
        TextualProgress {
            layout: horizontal;
            width: 100%;
            height: 1;
            dock: bottom;
        }

        #progress-title {
            padding-right: 1;
        }
    """

    TIMEOUT = 1.0

    SHOW_ETA = True

    @override
    def compose(self) -> ComposeResult:
        yield Label(id="progress-title")
        yield ProgressBar(id="progress-bar", show_eta=TextualProgress.SHOW_ETA)

    def add_task(self, label: str, total: float | None = None) -> TaskID:
        """Registers the new task with this progress indicator.

        Args:
            label: the text for the `progress-title` Label.
            total: the total length.

        Returns:
            A task ID. This is always 0 because this widget can only display one task at a time.
        """
        self.query_one(Label).update(label)
        self.query_exactly_one(ProgressBar).total = total
        return TaskID(0)

    def advance(self, task: TaskID, advance: float = 1) -> None:
        """Advances the task.

        Args:
            task: the task ID. This should always be 0 because this widget can only display one task
                at a time.
            advance: the amount by which to advance the progress indicator.
        """
        if task != 0:
            LOGGER.error(  # pragma: no cover
                f"Encountered unexpected TaskID: {task}. "
                "TextualProgress cannot display more than one task at a time."
            )
        assert task == 0
        progress = self.query_exactly_one(ProgressBar)
        progress.advance(advance)

    async def start(self) -> None:
        """Starts the progress indicator by mounting it to the App."""
        app = get_active_app()
        await_mount = app.mount(self)  # type: ignore[union-attr]
        await await_mount

    def stop(self) -> None:
        """Stops the progress indicator by removing it after a fixed timeout."""
        self.set_timer(TextualProgress.TIMEOUT, self.remove)
