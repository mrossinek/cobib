"""coBib's Author class."""

from __future__ import annotations

from typing import NamedTuple

from ruamel import yaml


class Author(NamedTuple):
    """A named tuple storing detailed author information.

    Whenever this object gets converted to a string (for printing/dumping/etc.) the following four
    possible cases may be the outcome:

    1. particle Last, suffix, First
    2. Last, suffix, First
    3. particle Last, First
    4. Last, First
    """

    first: str
    """The author's first name."""
    last: str
    """The author's last name."""
    particle: str | None = None
    """The author's name article."""
    suffix: str | None = None
    """The author's name suffix."""

    def __str__(self) -> str:
        """Formats this Author as a string."""
        if self.suffix is not None:
            if self.particle is not None:
                return f"{self.particle} {self.last}, {self.suffix}, {self.first}"
            return f"{self.last}, {self.suffix}, {self.first}"
        if self.particle is not None:
            return f"{self.particle} {self.last}, {self.first}"
        return f"{self.last}, {self.first}"

    @classmethod
    def to_yaml(
        cls, representer: yaml.representer.Representer, node: Author
    ) -> yaml.nodes.MappingNode:
        """Dumps the object for storage in YAML format.

        Args:
            representer: the YAML formatter object.
            node: the current author object to be formatted.

        Returns:
            A YAML-interpretable encoding of this author object.
        """
        return representer.represent_dict(
            {k: v for k, v in node._asdict().items() if v is not None}
        )

    @classmethod
    def parse(cls, author: str) -> str | Author:
        """Parses a string and extracts the author information.

        If the string is fully enclosed by curly braces, it will not be processed further. This can
        be used to prevent the splitting of (for example) the names of non-individuals (such as
        companies).

        Otherwise, the following forms are understood:

        1. First von Last
        2. von Last, First
        3. von Last, Jr, First

        The cases above are distinguished based on the number of commas that are found in the
        string.

        Args:
            author: the string to be parsed.

        Returns:
            The parsed author information (or the verbatim author string).

        Raises:
            ValueError: when more then 2 commas are encountered in the input string.
        """
        if author[0] == "{" and author[-1] == "}":
            return author

        num_commas = author.count(",")

        if num_commas == 0:
            parts = author.split()
            if len(parts) == 1:
                return author

            last = parts[-1]
            first = parts[0]
            particle = None
            for part in parts[1:-1]:
                if part[0].islower():
                    if particle:
                        particle += " " + part
                    else:
                        particle = part
                else:
                    first += " " + part

            return Author(first, last, particle=particle)

        if num_commas == 1:
            prefixed_last, first = author.split(",")
            suffix = None
        elif num_commas == 2:  # noqa: PLR2004
            prefixed_last, suffix, first = author.split(",")
            suffix = suffix.strip()
        else:
            raise ValueError(f"Expected less than 3 commas in the input string, not {num_commas}.")

        split_last = prefixed_last.split()
        if len(split_last) == 1:
            last = split_last[0]
            particle = None
        else:
            last_ = []
            particle_ = []
            for part in split_last:
                if part[0].islower():
                    particle_.append(part)
                else:
                    last_.append(part)
            last = " ".join(last_)
            particle = " ".join(particle_) or None

        return Author(first.strip(), last, particle=particle, suffix=suffix)
