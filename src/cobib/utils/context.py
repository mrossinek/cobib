"""coBib's context manager."""

from __future__ import annotations

from contextvars import copy_context

from textual.app import App


def get_active_app() -> App[None] | None:
    """Gets the active textual App (if any).

    Returns:
        The active textual App (or None) based on the current context.
    """
    ctx = copy_context()
    app = [var for var in ctx.values() if isinstance(var, App)]
    if len(app):
        return app[0]
    return None
