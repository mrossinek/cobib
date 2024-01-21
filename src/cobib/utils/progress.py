"""coBib's Rich-Textual progress integration.

The `Progress` utility provided by this module either constructs a `rich.progress.Progress` object
or a custom textual widget to display a rich-progress indicator and update it accordingly. This was
favored over using textual's `textual.widgets.ProgressBar` to re-implement rich's more flexible
`rich.progress.Progress` displaying capabilities.
"""

from __future__ import annotations

from threading import RLock
from time import monotonic
from typing import Any

from rich.progress import Progress as RichProgress
from rich.progress import ProgressColumn, Task, TaskID
from textual.widgets import Static
from typing_extensions import override

from .context import get_active_app


class Progress:
    """A utility class to construct either a `rich` or `textual` progress indicator."""

    @staticmethod
    def initialize(*columns: str | ProgressColumn, **kwargs: Any) -> RichProgress:
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
        return TextualProgress(*columns, **kwargs)


class TextualProgress(  # type: ignore[misc]
    Static, RichProgress, can_focus=False, can_focus_children=False
):
    """coBib's Frankenstein Rich-Textual progress widget."""

    DEFAULT_CSS = """
        TextualProgress {
            layout: horizontal;
            width: 100%;
            height: 1;
            offset-y: -1;
            dock: bottom;
        }
    """

    def __init__(
        self,
        *columns: str | ProgressColumn,
    ) -> None:
        """Initializes the Frankenstein Rich-Textual progress widget.

        Args:
            *columns: the columns to be reported. If this is empty, it will fall back to
                `get_default_columns`.
        """
        super().__init__()

        self.columns = columns or self.get_default_columns()

        self._lock = RLock()
        self._tasks: dict[TaskID, Task] = {}
        self._task_index: TaskID = TaskID(0)

        self.speed_estimate_period = 30.0
        self.get_time = monotonic

    @override
    def advance(self, task_id: TaskID, advance: float = 1) -> None:
        super().advance(task_id, advance)
        self.renderable = self.make_tasks_table(self.tasks)
        self.refresh()

    @override
    async def start(self) -> None:  # type: ignore[override]
        app = get_active_app()
        await_mount = app.mount(self)  # type: ignore[union-attr]
        await await_mount

    @override
    def stop(self) -> None:
        self.set_timer(5.0, self.remove)
