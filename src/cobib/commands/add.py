"""coBib's Add command.

.. include:: ../man/cobib-add.1.html_fragment
"""

from __future__ import annotations

import argparse
import asyncio
import logging
from collections import OrderedDict
from collections.abc import Callable
from functools import wraps
from typing import ClassVar

from rich.prompt import InvalidResponse, PromptBase, PromptType
from typing_extensions import override

from cobib.config import Event, LabelSuffix, config
from cobib.database import Database, Entry
from cobib.parsers import BibtexParser
from cobib.parsers.base_parser import Parser
from cobib.utils.diff_renderer import Differ
from cobib.utils.entry_points import entry_points
from cobib.utils.file_downloader import FileDownloader
from cobib.utils.journal_abbreviations import JournalAbbreviations
from cobib.utils.prompt import Prompt

from .base_command import Command
from .edit import EditCommand
from .modify import evaluate_as_f_string

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


class AddCommand(Command):
    """The Add Command.

    This command can parse the following arguments:

        * `-l`, `--label`: the label to give to the new entry.
        * `--disambiguation`: hard-codes the reply to be used if a disambiguation prompt would
          occur.
        * `-f`, `--file`: one or multiple files to associate with this entry. This data will be
          stored in the `cobib.database.Entry.file` property.
        * `-p`, `--path`: the path to store the downloaded associated file in. This can be used to
          overwrite the `cobib.config.config.FileDownloaderConfig.default_location`.
        * `--skip-download`: skips the automatic download of an associated file.
        * `--force-download`: forces the automatic download of an associated file.
        * in addition to the options above, a *mutually exclusive group* of keyword arguments for
          all available `cobib.parsers` are registered at runtime. Please check the output of
          `cobib add --help` for the exact list.
        * any *positional* arguments (i.e. those, not preceded by a keyword) are interpreted as tags
          and will be stored in the `cobib.database.Entry.tags` property.
    """

    name = "add"

    _avail_parsers: ClassVar[dict[str, tuple[Callable[[], Parser], bool]]] = {
        cls.name: (cls.load(), builtin) for (cls, builtin) in entry_points("cobib.parsers")
    }
    """The available parsers. The values are a tuple of the parser `entry_point` and a boolean
    indicating whether it is built-in (`True`) or from an external source (`False`). In the former
    case, the parser will attempt to provide a short-hand argument option, for example `-b` for
    `--bibtex`."""

    @override
    def __init__(self, *args: str) -> None:
        super().__init__(*args)

        self.new_entries: dict[str, Entry] = OrderedDict()
        """An `OrderedDict` mapping labels to `cobib.database.Entry` instances which were added by
        this command."""

    @override
    @classmethod
    def init_argparser(cls) -> None:
        parser = argparse.ArgumentParser(
            prog="add",
            description="Add subcommand parser.",
            epilog="Read cobib-add.1 and cobib-parsers.7 for more help.",
        )
        parser.add_argument("-l", "--label", type=str, help="the label for the new database entry")
        parser.add_argument(
            "-f",
            "--file",
            type=str,
            nargs="+",
            action="extend",
            help="files associated with this entry",
        )
        parser.add_argument("-p", "--path", type=str, help="the path for the downloaded file")
        parser.add_argument(
            "--disambiguation",
            type=str,
            choices=["keep", "replace", "update", "disambiguate"],
            help="the reply in case of a disambiguation prompt",
        )
        skip_download_group = parser.add_mutually_exclusive_group()
        skip_download_group.add_argument(
            "--skip-download",
            action="store_true",
            default=None,
            help="skip the automatic download of an associated file",
        )
        skip_download_group.add_argument(
            "--force-download",
            dest="skip_download",
            action="store_false",
            default=None,
            help="force the automatic download of an associated file",
        )
        group_add = parser.add_mutually_exclusive_group()
        for name, (_, short_hand) in cls._avail_parsers.items():
            help_text = f"{name} object identifier"
            if short_hand:
                try:
                    group_add.add_argument(f"-{name[0]}", f"--{name}", type=str, help=help_text)
                    continue
                except argparse.ArgumentError:  # pragma: no cover
                    pass  # pragma: no cover
            # NOTE: we ignore coverage for the special handling around here because this is tested
            # via the dummy plugin unittests in the CI.
            try:  # pragma: no cover
                group_add.add_argument(f"--{name}", type=str, help=help_text)  # pragma: no cover
            except argparse.ArgumentError:  # pragma: no cover
                LOGGER.error(  # pragma: no cover
                    f"Could not setup the {name} parser argument for the add command."
                )

        # NOTE: argparse.REMAINDER is undocumented since Python 3.9 and considered a legacy feature.
        # See also https://bugs.python.org/issue17050
        parser.add_argument(
            "tags",
            nargs=argparse.REMAINDER,
            help="A list of space-separated tags to associate with this entry."
            "\nYou can use quotes to specify tags with spaces in them.",
        )

        cls.argparser = parser

    @override
    async def execute(self) -> None:  # type: ignore[override]  # noqa: PLR0912,PLR0915
        LOGGER.debug("Starting Add command.")

        Event.PreAddCommand.fire(self)

        edit_entries = False
        for name, (cls, _) in AddCommand._avail_parsers.items():
            string = getattr(self.largs, name, None)
            if string is None:
                continue
            LOGGER.debug("Adding entries from %s: '%s'.", name, string)
            self.new_entries = cls().parse(string)
            break
        else:
            if self.largs.label is not None:
                LOGGER.warning(
                    "No input to parse. Creating new entry '%s' manually.", self.largs.label
                )
                self.new_entries = {
                    self.largs.label: Entry(
                        self.largs.label,
                        {"ENTRYTYPE": config.commands.edit.default_entry_type},
                    )
                }
                edit_entries = True
            else:
                msg = "Neither an input to parse nor a label for manual creation specified!"
                LOGGER.error(msg)
                return

        if self.largs.label is not None:
            assert len(self.new_entries.values()) == 1
            for value in self.new_entries.copy().values():
                # logging done by cobib/database/entry.py
                value.label = self.largs.label
            self.new_entries = OrderedDict(
                (self.largs.label, value) for value in self.new_entries.values()
            )
        else:
            formatted_entries = OrderedDict()
            for label, value in self.new_entries.items():
                formatted_label = evaluate_as_f_string(
                    config.database.format.label_default, {"label": label, **value.data.copy()}
                )
                value.label = formatted_label
                formatted_entries[formatted_label] = value
            self.new_entries = formatted_entries

        if self.largs.file is not None:
            assert len(self.new_entries.values()) == 1
            for value in self.new_entries.values():
                # logging done by cobib/database/entry.py
                value.file = self.largs.file

        if self.largs.tags != []:
            assert len(self.new_entries.values()) == 1
            for value in self.new_entries.values():
                # logging done by cobib/database/entry.py
                value.tags = self.largs.tags

        skip_download = config.commands.add.skip_download
        if self.largs.skip_download is not None:
            skip_download = self.largs.skip_download
        LOGGER.info("Automatic file download will%s be attempted.", " not" if skip_download else "")

        bib = Database()
        existing_labels = set(bib.keys())

        for lbl, entry in self.new_entries.copy().items():
            overwrite_file = False
            # check if label already exists
            if lbl in existing_labels:
                # if it does, we have multiple cases to differentiate:
                if edit_entries:
                    # the user tried to manually add an entry which already exists, point them to
                    # the edit command instead
                    msg = (
                        f"You tried to add the '{lbl}' entry manually, but it already exists, "
                        f"please use `cobib edit {lbl}` instead!"
                    )
                    LOGGER.warning(msg)
                    continue
                # in all other cases, we enter an interactive prompt to let the user decide how
                # to proceed
                msg = f"You tried to add a new entry '{lbl}' which already exists!"
                LOGGER.warning(msg)

                # finding related entries in the database
                direct, indirect = bib.find_related_labels(lbl)
                if len(indirect) > 0:
                    separator, enumerator = config.database.format.label_suffix
                    trimmed_lbl, _ = LabelSuffix.trim_label(lbl, separator, enumerator)
                    msg = (
                        f"Found some indirectly related entries to '{lbl}': {indirect}.\n"
                        "You can use the review command to inspect these like so:\n"
                        f"cobib review -- ++label {trimmed_lbl}"
                    )
                    LOGGER.warning(msg)

                # get the --disambiguation argument (which will be `None` by default)
                res = self.largs.disambiguation

                parser = BibtexParser()

                # the first label that we would like to check is the current one
                direct_lbl = lbl
                direct.remove(lbl)
                # the remaining ones will be iterated later
                direct_iter = iter(direct)

                # we loop until we reach the `disambiguate` answer (which implies the end) or we
                # break out manually below
                while res != "disambiguate":
                    if res is None:
                        # if the user did not provide an answer via the input arguments, this
                        # renders an interactive prompt for them
                        left = parser.dump(bib[direct_lbl])
                        right = parser.dump(entry)
                        diff = Differ(left, right)
                        diff.compute()
                        table = diff.render("bibtex")

                        prompt_text = "How would you like to handle this conflict?"
                        choices = ["keep", "replace", "update", "cancel", "disambiguate", "help"]
                        default = "keep"

                        res = await Prompt.ask(
                            prompt_text,
                            choices=choices,
                            default=default,
                            pre_prompt_message=table,
                            process_response_wrapper=self._wrap_prompt_process_response,
                        )

                    if res == "update":
                        msg = (
                            f"Updating the already existing entry '{direct_lbl}' with the new data."
                        )
                        LOGGER.info(msg)
                        entry.merge(bib[direct_lbl], ours=True)
                        self._rename_added_entry(entry, direct_lbl)
                        overwrite_file = True
                        break

                    elif res == "replace":
                        msg = (
                            f"Overwriting the already existing entry '{direct_lbl}' with the new "
                            "data."
                        )
                        LOGGER.info(msg)
                        self._rename_added_entry(entry, direct_lbl)
                        overwrite_file = True
                        break

                    elif res == "disambiguate":
                        msg = "Skipping all other related entries and disambiguating the new one."
                        LOGGER.info(msg)
                        break

                    elif res == "keep":
                        res = None
                        msg = f"Keeping the already existing entry '{direct_lbl}'."
                        LOGGER.info(msg)

                    elif res == "cancel":  # pragma: no branch
                        msg = f"Cancelling the addition of the new entry '{lbl}'."
                        LOGGER.warning(msg)
                        return

                    try:
                        direct_lbl = next(direct_iter)
                    except StopIteration:
                        res = "disambiguate"
                        msg = "No more related entries, triggering label disambiguation."
                        LOGGER.info(msg)
                        break

                if res == "disambiguate":
                    msg = (
                        "The label will be disambiguated based on the configuration option: "
                        "config.database.format.label_suffix"
                    )
                    LOGGER.warning(msg)
                    new_label = bib.disambiguate_label(lbl, entry)
                    self._rename_added_entry(entry, new_label)

            # download associated file (if requested)
            if "_download" in entry.data.keys():
                if skip_download:
                    entry.data.pop("_download")
                else:
                    task = asyncio.create_task(
                        FileDownloader().download(
                            entry.data.pop("_download"),
                            entry.label,
                            folder=self.largs.path,
                            overwrite=overwrite_file,
                        )
                    )
                    path = await task
                    if path is not None:  # pragma: no branch
                        entry.file = str(path)
            # check journal abbreviation
            if "journal" in entry.data.keys():
                entry.data["journal"] = JournalAbbreviations.elongate(entry.data["journal"])

        Event.PostAddCommand.fire(self)

        bib.update(self.new_entries)
        if edit_entries:
            EditCommand(self.largs.label).execute()

        bib.save()

        self.git()

        for label in self.new_entries:
            msg = f"'{label}' was added to the database."
            LOGGER.log(35, msg)

    def _rename_added_entry(self, entry: Entry, new_label: str) -> None:
        """Renames the provided entry to the new provided label.

        Args:
            entry: the entry to be renamed.
            new_label: its new label.
        """
        old_label = entry.label
        if old_label != new_label:
            entry.label = new_label
            self.new_entries[new_label] = entry
            self.new_entries.pop(old_label)

    @staticmethod
    def _wrap_prompt_process_response(
        func: Callable[[PromptBase[PromptType], str], PromptType],
    ) -> Callable[[PromptBase[PromptType], str], PromptType]:
        """A method to wrap a `PromptBase.process_response` method.

        This method wraps a `PromptBase.process_response` method in order to handle a user's request
        for additional help.

        Args:
            func: the `PromptBase.process_response` method to be wrapped.

        Returns:
            The wrapped `PromptBase.process_response` method.
        """

        @override  # type: ignore[misc]
        @wraps(func)
        def process_response(prompt: PromptBase[PromptType], value: str) -> PromptType:
            return_value: PromptType = func(prompt, value)

            if return_value == "help":
                LOGGER.debug("User requested help.")
                raise InvalidResponse(
                    "[yellow]A conflict between an existing (left) and newly added entry (right) "
                    "occurred. These are your options:\n"
                    "  'keep' the existing entry and discard the new addition (default)\n"
                    "  'replace' the existing entry with the new one\n"
                    "  'update' the existing entry with the new data\n"
                    "  'cancel' the addition of this new entry\n"
                    "  'disambiguate' the new entry from the existing one by adding a label suffix"
                )

            return return_value

        return process_response
