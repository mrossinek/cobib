"""coBib's input widget.

This widget is a simple wrapper around textual's
[`Input`](https://textual.textualize.io/widgets/input/) widget to ensure two aspects:

- that the `Escape` key can be used to quit/abort the input
- the widget can be automatically unmounted upon submission of the input (`Enter`)

.. warning::

   This module makes no API stability guarantees! Refer to `cobib.ui.components` for more details.
"""

from __future__ import annotations

from textual.widgets import Input as _Input


class Input(_Input):
    """coBib's input widget."""

    catch: bool = False
    """If set, this widget will automatically unmount itself upon the `Submitted` event."""

    BINDINGS = [("escape", "escape", "Quit the prompt")]

    async def action_escape(self) -> None:
        """The action to perform when hitting `Escape`.

        In this case, unmount the widget itself and refresh the parent's layout.
        """
        if self.parent is not None:
            self.parent.refresh(layout=True)
        await self.remove()

    def on_input_submitted(self, event: _Input.Submitted) -> None:
        """The action to perform when receiving the `Submitted` event.

        In this case, unmount the widget itself if `catch` is set. Otherwise the event gets
        [bubbled up](https://textual.textualize.io/guide/events/#bubbling).
        """
        if self.catch:
            event.input.remove()
            event.stop()
