"""coBib's Review command.

This command allows you to review the entries of your database to quickly make changes as you go.
This is especially helpful as your knowledge of your database changes and develops with time.

In its simplest form, you can review your entire database in an interactive manner with the
following command:
```
cobib review
```

Since this can be quite a lot all at once, you can also narrow your review down using filters (see
also `cobib.commands.list_`) just like with some of the other commands. For example, the following
command reviews all entries from the year 2023:
```
cobib review -- ++year 2023
```
You can also specify a manual selection of labels (or visually select them in the TUI (see below)):
```
cobib review --selection -- Label1 Label2 ...
```

You can also narrow your review down to one or more fields of all the entries:
```
cobib review tags -- ++year 2023
cobib review ENTRYTYPE year
```
When restricting your review like the above, you will only get a preview of the selected set of
fields. If you require more context, you can either request that interactively (see below) or
provide the `--context` option like so:
```
cobib review --context ENTRYTYPE
```

### How it works

For every label that you review, you will be presented with its contents and asked to select an
action that you would like to take. Your choices are the following:

- `edit`: opens the entry in your `cobib.config.config.EditCommandConfig.editor` and allows you to
          freely modify it.
- `done`: indicates that you are happy with this entry and completes its review.
- `skip`: skips the review of the current entry indicating that you do not want to make any changes
          but also do not mark it as `done` (which means that when resuming a review, it will come
          up again).
- `context`: requests additional context and updates the preview to contain all the information
             stored in the entry. This action is only available when context has not been requested
             yet and when fields are being filtered in the first place.
- `finish`: closes the review process (even if some entries have not been reviewed yet) and saves
            your progress to the database. This allows you to perform reviews in smaller chunks
            because you can resume from the current review state at another time.
- `inline`: allows you to edit a specific field in-line (i.e. without having to open the entry in an
            external editor). When reviewing a single field, you can simply type `inline` to edit
            that one. When reviewing more than one, you need to specify which field you want to edit
            in-line like so: `inline <field>`. This is a highly experimental feature so please be
            aware of bugs and report any issues or suggestions online:
            https://gitlab.com/cobib/cobib/-/issues/new

### Resuming a previously started review

If you finished a review early (see `finish` above) you can easily continue where you left of with
the `--resume` option. This option takes a git commit identifier as its argument so you should
either find the SHA of the auto-commit of the review that you would like to continue (see also
`cobib.commands.git.GitCommand`), or if you know that it is (for example) the last thing that you
did, you can simply use `HEAD` as shown below:
```
cobib review --resume HEAD
```
In this way, you do not need to repeat any filters that you may have used and coBib will
automatically know which entries you have marked as `done` and will not show them to you again.
However, entries which you used `skip` on before, will now show up again.

### Additional options

There are some additional options to the `review` command.

You can indicate which entries of a review you have already completed with the `--done` argument:
```
cobib review --done Author2023 -- ++year 2023
```
The example above will review all entries from the year 2023, except for `Autho2023`. It is unlikely
that you will ever use this option manually if you have `cobib.config.config.DatabaseConfig.git`
enabled, because that will allow you to resume a previously started review more easily.


### TUI

You can also trigger this command from the `cobib.ui.tui.TUI`.
By default, it is bound to the `c` key (as in "check") which will drop you into the prompt where you
can type out a normal command-line command:
```
:review <arguments go here>
```

.. note::
   If you have already selected one or more entries, the `--selection` argument will automatically
   be added.
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
from collections.abc import Callable
from functools import wraps
from typing import cast

from rich.console import Console, Group
from rich.prompt import InvalidResponse, PromptBase, PromptType
from rich.syntax import Syntax
from rich.text import Text
from textual.app import App
from typing_extensions import override

from cobib.config import Event, config
from cobib.database import Database, Entry
from cobib.parsers import YAMLParser
from cobib.utils.prompt import Prompt
from cobib.utils.rel_path import RelPath

from .base_command import ArgumentParser, Command
from .edit import EditCommand
from .list_ import ListCommand

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


class ReviewCommand(Command):
    """The Review Command.

    This command can parse the following arguments:

        * `field`: an optional list of fields to limit the review process to.
        * `-c`, `--context`: when specified, the full entries will be previewed even if selected
          fields have been provided. This disables the interactive `context` action by always
          enabling it.
        * `-r`, `--resume`: specifies a git commit SHA of a previous review command auto-commit from
          which to resume. This requires the git-integration to be enabled.
        * `-d`, `--done`: specifies a list of labels which will not be included in the review even
          if they would seamingly match the filter/selection. This is useful for continuing a
          previously unfinished review process.
        * `-s`, `--selection`: when specified, the positional arguments will *not* be
          interpreted as filters but rather as a direct list of entry labels. This can
          be used on the command-line but is mainly meant for the TUIs visual selection
          interface (hence the name).
        * in addition to the above, you can add `filters` to specify a subset of your
          database for reviewing. For more information refer to `cobib.commands.list_`.
    """

    name = "review"

    @override
    def __init__(
        self,
        *args: str,
        console: Console | App[None] | None = None,
        prompt: type[PromptBase[PromptType]] | None = None,
    ) -> None:
        super().__init__(*args, console=console, prompt=prompt)

        if self.largs.done is None:
            # NOTE: we cannot make the default of the `done` argument an empty list because this
            # would remain the same list across multiple runs of the review command within the same
            # session.
            self.largs.done = []

        self.reviewed_entries: list[Entry] = []
        """A list of `cobib.database.Entry` objects which were marked as `done` by this review."""

    @override
    @classmethod
    def init_argparser(cls) -> None:
        parser = ArgumentParser(prog="review", description="Review subcommand parser.")
        parser.add_argument("field", type=str, nargs="*", help="the field(s) to review")
        parser.add_argument(
            "-c",
            "--context",
            action="store_true",
            help="When specified, the full entries will be previewed even if selected fields have "
            "been provided. This disables the interactive `context` action by always enabling it.",
        )
        parser.add_argument(
            "-r",
            "--resume",
            type=str,
            default=None,
            help="Specifies a git commit SHA of a previous review command auto-commit from which "
            "to resume. This requires the git-integration to be enabled.",
        )
        parser.add_argument(
            "-d",
            "--done",
            type=str,
            nargs="*",
            help="Specifies a list of labels which will not be included in the review even if they "
            "would seamlingly match the filter/selection. This is useful for continuing a "
            "previously unfinished review process.",
        )
        parser.add_argument(
            "-s",
            "--selection",
            action="store_true",
            help="When specified, the `filter` argument will be interpreted as a list of entry "
            "labels rather than arguments for the `list` command.",
        )
        parser.add_argument(
            "filter",
            nargs="*",
            help="You can specify filters as used by the `list` command in order to select a "
            "subset of labels to be reviewed. To ensure this works as expected you should add the "
            "pseudo-argument '--' before the list of filters. See also `list --help` for more "
            "information.",
        )
        cls.argparser = parser

    @override
    @classmethod
    def _parse_args(cls, args: tuple[str, ...]) -> argparse.Namespace:
        review_args = []
        filter_args = []
        found_sep = False
        for arg in args:
            if arg == "--":
                found_sep = True
                continue
            if found_sep:
                filter_args.append(arg)
            else:
                review_args.append(arg)

        largs = super()._parse_args(tuple(review_args))
        largs.filter = filter_args
        return largs

    @override
    async def execute(self) -> None:  # type: ignore[override]  # noqa: PLR0912,PLR0915
        if self.largs.resume is not None:
            LOGGER.info(f"Trying to resume review from {self.largs.resume}.")
            git_tracked = config.database.git
            if not git_tracked:
                msg = (
                    "You must enable coBib's git-tracking in order to use the `--resume` option of "
                    "the `review` command.\nPlease refer to the documentation for more information "
                    "on how to set this up."
                )
                LOGGER.error(msg)
                return

            file = RelPath(config.database.file).path
            root = file.parent
            if not (root / ".git").exists():
                msg = (
                    "You have configured, but not initialized coBib's git-tracking."
                    "\nPlease consult `cobib init --help` for more information on how to do so."
                )
                LOGGER.error(msg)
                return

            try:
                sha_message = subprocess.check_output(
                    ["git", "-C", root, "log", "--format=%B", "-n1", self.largs.resume]
                )
            except subprocess.CalledProcessError:
                LOGGER.error(f"Could not find the requested git commit: '{self.largs.resume}'")
                return

            try:
                decoded_message = sha_message.decode()
                trimmed_message = "".join(decoded_message.splitlines()[1:])
            except KeyError:
                LOGGER.error(f"Could not trim the commit message: '{decoded_message}'")
                return

            try:
                message_args = json.loads(trimmed_message)
            except json.JSONDecodeError:
                LOGGER.error(
                    f"Could not extract arguments from the trimmed message: '{trimmed_message}'"
                )
                return

            LOGGER.info("Found the git-commit from which to resume.")
            for key, val in message_args.items():
                if key == "resume":
                    # we do not overwrite the resume argument
                    continue
                setattr(self.largs, key, val)

        LOGGER.debug("Starting Review command.")

        Event.PreReviewCommand.fire(self)

        if self.largs.selection:
            LOGGER.info("Selection given. Interpreting `filter` as a list of labels")
            labels = [label for label in self.largs.filter if label not in self.largs.done]
        else:
            LOGGER.debug("Gathering filtered list of entries to be reviewed.")
            listed_entries, _ = ListCommand(*self.largs.filter).execute_dull()
            labels = [entry.label for entry in listed_entries if entry.label not in self.largs.done]

        yml = YAMLParser()

        bib = Database()

        for label in labels:
            LOGGER.debug(f"Starting review of entry '{label}'")

            _continue = False
            context = self.largs.context and self.largs.field

            while not _continue:
                entry = bib[label]

                if context:
                    LOGGER.debug("Context has been requested so the fields are not filtered.")
                elif self.largs.field:
                    LOGGER.debug(
                        f"Limiting the review to the requested fields: '{self.largs.field}'"
                    )
                    entry = Entry(
                        label,
                        {key: val for key, val in entry.data.items() if key in self.largs.field},
                    )

                dump = yml.dump(entry)
                if dump is None:
                    LOGGER.error(f"The entry '{label}' could not be dumped as YAML. Skipping it.")
                    continue

                syntax = Syntax(dump, "yaml", background_color="default", word_wrap=True)

                prompt_text = "What action what you like to perform?"
                choices = ["done", "skip", "edit", "inline", "finish", "help"]
                if not context and self.largs.field:
                    choices.insert(0, "context")

                res = await Prompt.ask(
                    prompt_text,
                    choices=choices,
                    pre_prompt_message=syntax,
                    process_response_wrapper=self._wrap_prompt_process_response,
                )
                if res == "context":
                    LOGGER.info("Requesting more context.")
                    context = True
                elif res == "done":
                    LOGGER.info(f"Marking entry '{label}' as done.")
                    self.largs.done.append(label)
                    self.reviewed_entries.append(entry)
                    _continue = True
                elif res == "skip":
                    LOGGER.info(f"Skipping entry '{label}'.")
                    _continue = True
                elif res == "edit":
                    new_text = EditCommand.edit(dump)
                    if dump == new_text:
                        LOGGER.info("No changes detected.")
                    else:
                        parsed = yml.parse(new_text)
                        new_entry = next(iter(parsed.values()))

                        if self.largs.field:
                            new_entry.merge(bib[label], ours=True)

                        if new_entry.label != label:
                            LOGGER.error(
                                "Renaming entries as part of the review process is not supported!"
                            )
                        else:
                            bib.update({label: new_entry})
                elif res.startswith("inline"):
                    try:
                        _, inline = res.split()
                    except ValueError:
                        inline = self.largs.field[0]
                    LOGGER.info(f"Editing field '{inline}' in-line.")

                    prompt_text = f"Please provide the new value for the field '{inline}'"

                    warning = Text.from_markup(
                        "[yellow]WARNING: the inline editing is a highly experimental feature!\n"
                        "Be aware of bugs and proceed with care.\nPlease report any issues or "
                        "suggestions online: https://gitlab.com/cobib/cobib/-/issues/new"
                    )

                    res = await Prompt.ask(
                        prompt_text,
                        input_text=str(entry.data[inline]),
                        pre_prompt_message=Group(warning, syntax),
                    )
                    if res.isnumeric():
                        res = int(res)
                    entry.data[inline] = res
                    entry.merge(bib[label], ours=True)
                    bib.update({label: entry})
                    inline = None

                elif res == "finish":
                    LOGGER.info("Finishing review early.")
                    break

            else:
                # we did NOT break out of the while loop so we continue with the next label
                continue

            # we DID break out of the while loop indicating that we want to finish the review early
            break

        Event.PostReviewCommand.fire(self)

        bib.save()

        self.git(allow_empty=True)

    def _wrap_prompt_process_response(
        self,
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
            return_value: PromptType
            try:
                return_value = func(prompt, value)
            except InvalidResponse as exc:
                if not value.startswith("inline"):
                    raise exc
                return_value = cast(PromptType, value)

            if return_value == "help":
                LOGGER.debug("User requested help.")
                help_text = (
                    "[yellow]You may perform any of the following actions:\n"
                    "    edit: open the current entry for editing\n"
                    "    skip: skip the current entry\n"
                    "    done: mark the current entry as done\n"
                    "  finish: finish the review early\n"
                    "  inline: EXPERIMENTAL edit a field in-line"
                )
                if prompt.choices is not None and "context" in prompt.choices:
                    help_text += "\n context: add additional context to the preview"
                raise InvalidResponse(help_text)

            elif value.startswith("inline"):
                num_args = len(value.split())
                num_fields = len(self.largs.field)
                if num_args > 2 or (num_args == 1 and num_fields > 1):  # noqa: PLR2004
                    help_text = (
                        "[red]You are reviewing more than one field at once.\n"
                        "For editing one of them in-line, please specify which one like so:\n"
                        "  inline <field>"
                    )
                    raise InvalidResponse(help_text)

            return return_value

        return process_response
