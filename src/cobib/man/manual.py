"""coBib's manual interface.

.. include:: cobib-man.7.html_fragment
"""

import re
from collections import defaultdict
from importlib.util import find_spec
from io import StringIO
from pathlib import Path

from rich.console import Console, ConsoleOptions
from rich.tree import Tree

from cobib.utils.entry_points import entry_points


class Manual:
    """coBib's man-page database.

    This object manages all man-pages that are registered via the `cobib.man` entry-point.
    """

    MAN_PAGE_REFERENCE_REGEX = r"(\S+)\((\d)\)"
    """A regex to split the man-page name from its section provided in parentheses."""

    def __init__(self) -> None:
        """Initializes the man-page database.

        This parses the `cobib.man` entry-points and populates the :attr:`index` and
        :attr:`sections` attributes.
        """
        self.index: dict[str, str] = {}
        """Dictionary mapping man-page names to the Python module containing the raw file."""

        self.sections: dict[int, dict[str, dict[str, set[str]]]] = defaultdict(
            lambda: defaultdict(lambda: defaultdict(set))
        )
        """A nested dictionary to sort man-pages into a priority hierarchy.

        The nesting levels of the dictionary have the following keys:
            1. level is a man-page section (e.g. 1, 5, 7)
            2. level is a priority character used to group man-pages within a section (e.g. A, B).
               An empty string is used for lowest level man-pages (e.g. `cobib.1` in section 1).
            3. level should have only a single entry whose key will be the heading in the rendered
               man-page index for the corresponding priority level (or section level when the second
               level is the empty string).

        Here is an example:
        ```python
        sections = {
            1: {
                "": {"Commands": {"cobib.1}},
                "A": {"Common": {"cobib-add.1", ...}},
                "B": {"Utility": {"cobib-git.1", ...}},
            },
            5: {
                "": {"Config": {"cobib-config.5}},
            },
            7: {
                "": {"Miscellaneous": {"cobib-getting-started.7}},
                ...,
            },
        ```
        """

        for entry, _ in entry_points("cobib.man"):
            name = entry.name
            section = int(entry.name.split(".")[-1])
            module, priority = entry.value.split(":")
            self.index[name] = module

            for category in priority.split("."):
                prio, header = category.split("_")
                self.sections[section][prio][header].add(name)

    def path_from_name(self, name: str) -> Path:
        """Maps a man-page name to the path where it is stored.

        Args:
            name: the name of the man-page to get the path for.

        Returns:
            The path to the man-page file.

        Raises:
            KeyError: if the name is not a known man-page (i.e. is not in :attr:`index`).
            ImportError: if the module in which the man-page is located could not be loaded.
        """
        if name not in self.index:
            raise KeyError(
                f"'{name}' does not match a known man-page. Make sure the man-page was registered "
                "correctly via the `cobib.man` entry-point."
            )

        spec = find_spec(self.index[name])

        if spec is None or spec.origin is None:
            # NOTE: no idea how to test this... this would imply a previously registered entry-point
            # magically broke somehow..
            raise ImportError(  # pragma: no cover
                f"Could not load the spec for the module containing the '{name}' man-page."
                " Please report this issue with steps on how to reproduce this bug online: "
                "https://gitlab.com/cobib/cobib/-/issues/new"
            )

        folder = Path(spec.origin).parent

        return folder / f"{name}.md"

    def resolve_name(self, name: str) -> str:
        """Resolves the name of a man-page in a prioritized order according to :attr:`sections`.

        The `name` may be a unique substring. It may also be in link-form, e.g. `cobib(1)` which
        gets resolved to `cobib.1`. If the name could match multiple pages, the order in
        :attr:`sections` determines the priority. For example, `man` could match `cobib-man.1` and
        `cobib-man.7`, but the former will take precedence. Query for `man.7` to get the latter.

        Args:
            name: the name of a man-page.

        Returns:
            The resolved name in sanitized form (e.g. `cobib.1`).

        Raises:
            KeyError: if `name` could not be matched with any man-page.
        """
        name = self._normalize(name)
        for section in sorted(self.sections.keys()):
            for prio in sorted(self.sections[section].keys()):
                for header in sorted(self.sections[section][prio].keys()):
                    for candidate in sorted(self.sections[section][prio][header]):
                        if name in candidate:
                            return candidate

        raise KeyError(f"'{name}' could not be matched to any man-page.")

    def render_rich(self) -> Tree:
        """Renders :attr:`sections` as a `rich.tree.Tree`."""
        tree = Tree(".", hide_root=True)
        for section in sorted(self.sections.keys()):
            section_header = self.sections[section].get("", {"": ()})
            header = next(iter(section_header.keys()))
            section_tree = tree.add(f"{section} - {header.title()}", style="blue bold")
            for prio in sorted(self.sections[section].keys()):
                for header in sorted(self.sections[section][prio].keys()):
                    if prio != "":
                        prio_tree = section_tree.add(
                            f"{prio} - {header.title()}", style="yellow bold"
                        )
                    for name in sorted(self.sections[section][prio][header]):
                        if prio == "":
                            section_tree.add(name, style="white not bold")
                        else:
                            prio_tree.add(name, style="white not bold")

        return tree

    def render_porcelain(self) -> list[str]:
        """Renders :attr:`sections` in a plain-text readable form."""

        class _ASCIIConsole(Console):
            @property
            def options(self) -> ConsoleOptions:
                options = super().options
                options.encoding = "ascii"
                return options

        io = StringIO()
        console = _ASCIIConsole(file=io)
        console.print(self.render_rich())
        return io.getvalue().split("\n")

    @staticmethod
    def _normalize(name: str) -> str:
        """Normalizes a man-page link (e.g. `cobib(1)`) to a man-page name (e.g. `cobib.1`)."""
        if match := re.match(Manual.MAN_PAGE_REFERENCE_REGEX, name):
            name = f"{match[1]}.{match[2]}"
        return name


manual = Manual()
