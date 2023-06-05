"""coBib's motion key event.

This custom event gets send by coBib's widgets and is used to handle cursor motions.

.. warning::

   This module makes no API stability guarantees! Refer to `cobib.ui.components` for more details.
"""

from textual.events import Event


class MotionKey(Event):
    """coBib's motion key event."""

    def __init__(self, key: str) -> None:
        """Initializes a motion key event.

        Args:
            key: the motion key which was pressed to trigger this event.
        """
        super().__init__()
        self.key = key
