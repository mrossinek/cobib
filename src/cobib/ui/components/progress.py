"""coBib's Rich-Textual progress widget.

This widget is a bit of a Frankenstein project as it wraps rich's `rich.progress.Progress` object
and makes sure that upon advancing a task, the `textual.widgets.Static` widget used to display it in
the TUI gets updated. This was favored over using textual's `textual.widgets.ProgressBar` to
re-implement rich's more flexible `rich.progress.Progress` displaying capabilities.

.. warning::

   This module makes no API stability guarantees! Refer to `cobib.ui.components` for more details.
"""

from __future__ import annotations

from threading import RLock
from time import monotonic

from rich.progress import Progress as RichProgress
from rich.progress import ProgressColumn, Task, TaskID
from textual.widgets import Static
from typing_extensions import override


class Progress(  # type: ignore[misc]
    Static, RichProgress, can_focus=False, can_focus_children=False
):
    """coBib's Frankenstein Rich-Textual progress widget."""

    DEFAULT_CSS = """
        Progress {
            layout: horizontal;
            width: 100%;
            height: 1;
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
        super().__init__(id="live")

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
    def start(self) -> None:
        return

    @override
    def stop(self) -> None:
        return
