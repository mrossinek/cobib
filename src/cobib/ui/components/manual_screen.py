"""coBib's man-page screen.

This screen renders a Textual-`MarkdownViewer` of one of coBib's man-pages.

.. warning::

   This module makes no API stability guarantees! Refer to `cobib.ui.components` for more details.
"""

from __future__ import annotations

import re
from copy import copy
from typing import Any, ClassVar

from linkify_it import LinkifyIt
from linkify_it.main import Match
from markdown_it import MarkdownIt
from rich.tree import Tree
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Footer, MarkdownViewer, OptionList
from textual.widgets.option_list import Option
from typing_extensions import override

from cobib.man import manual


class ManualScreen(ModalScreen[None]):
    """coBib's man-page screen."""

    BINDINGS: ClassVar[list[Binding | tuple[str, str] | tuple[str, str, str]]] = [
        ("q", "quit", "quit"),
        ("i", "index", "index"),
        Binding("j", "scroll_down", "Down", show=False),
        Binding("k", "scroll_up", "Up", show=False),
        Binding("t", "toggle_toc", "TOC", tooltip="Toggle the ToC Panel."),
    ]
    """
    | Key(s) | Description |
    | :- | :- |
    | t | Toggle the ToC. |
    | i | View index of man-pages. |
    | q | Quits the manual. |
    | j, down | Scrolls down. |
    | k, up | Scrolls up. |
    | PageDown | Moves one page down. |
    | PageUp | Moves one page up. |
    | End | Moves to the bottom. |
    | Home | Moves to the top. |
    """

    DEFAULT_CSS = """
        ManualScreen {
            align: center middle;
            offset-y: -1;
        }

        #manual {
            height: auto;
            max-height: 90%;
            max-width: 90%;
            background: $surface;
        }
    """

    @override
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        def _normalize(_, match: Match) -> None:  # type: ignore[no-untyped-def]
            match.url = str(manual.path_from_name(manual.resolve_name(match.raw)))

        linkify = LinkifyIt()
        linkify.add(
            "cobib",
            {
                "validate": re.compile(r"^[-a-z]*\(\d\)"),
                "normalize": _normalize,
            },
        )
        parser = MarkdownIt("gfm-like")
        parser.linkify = linkify

        self.markdown = MarkdownViewer(
            id="manual",
            # FIXME: enable links once https://github.com/Textualize/textual/issues/6039 is fixed
            open_links=False,
            parser_factory=lambda: parser,
            show_table_of_contents=False,
        )
        """The internal `MarkdownViewer` widget in which the actual man-page gets rendered."""

    @override
    def compose(self) -> ComposeResult:
        yield self.markdown
        yield Footer()

    def action_quit(self) -> None:
        """Quits the manual.

        Since this is the action of the `ManualScreen`, it simply pops the screen.
        """
        assert self.is_current
        self.app.pop_screen()

    def action_toggle_toc(self) -> None:
        """Toggles display of the MarkdownViewer ToC panel."""
        self.markdown.show_table_of_contents = not self.markdown.show_table_of_contents

    def action_scroll_up(self) -> None:
        """Scrolls up inside the MarkdownViewer."""
        self.markdown.scroll_up()

    def action_scroll_down(self) -> None:
        """Scrolls down inside the MarkdownViewer."""
        self.markdown.scroll_down()

    async def action_index(self) -> None:
        """Opens a prompt with the man-page index to open another page."""

        async def load(option: str | None) -> None:
            if option is None or not option:
                return
            # NOTE: no idea how to unittest the link clicking...
            await self.markdown.go(manual.path_from_name(option))

        self.app.push_screen(ManPageIndexScreen(), load)


class ManPageIndexScreen(ModalScreen[str]):
    """coBib's man-page index screen."""

    AUTO_FOCUS = "OptionList"

    BINDINGS: ClassVar[list[Binding | tuple[str, str] | tuple[str, str, str]]] = [
        ("escape", "escape", "escape"),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
    ]
    """
    | Key(s) | Description |
    | :- | :- |
    | escape | Escapes the selection. |
    | enter | Confirms the selection. |
    | j, down | Moves down. |
    | k, up | Moves up. |
    | PageDown | Moves one page down. |
    | PageUp | Moves one page up. |
    | End | Moves to the bottom. |
    | Home | Moves to the top. |
    """

    DEFAULT_CSS = """
        ManPageIndexScreen {
            align: center middle;
            offset-y: -1;
        }

        #pages {
            height: auto;
            max-height: 50%;
            max-width: 50%;
            background: $surface;
        }
    """

    @override
    def compose(self) -> ComposeResult:
        index = manual.render_rich()

        def node_to_option(node: Tree) -> Option:
            if len(node.children) == 0:
                return Option(node, id=str(node.label))

            node_without_children = copy(node)
            node_without_children.children = []
            return Option(node_without_children, disabled=True)

        def flatten(tree: Tree) -> list[Option]:
            nodes = [node_to_option(tree)]
            for node in tree.children:
                nodes.append(node_to_option(node))
                for n in node.children:
                    nodes.extend(flatten(n))
            return nodes

        nodes = flatten(index)

        yield OptionList(*nodes, id="pages")

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Returns the selected man-page link."""
        self.dismiss(str(event.option.id))

    def action_escape(self) -> None:
        """Escapes the prompt without opening a new man-page."""
        self.dismiss("")

    def action_cursor_up(self) -> None:
        """Scrolls up inside the OptionList."""
        self.query_exactly_one(OptionList).action_cursor_up()

    def action_cursor_down(self) -> None:
        """Scrolls down inside the OptionList."""
        self.query_exactly_one(OptionList).action_cursor_down()
