"""coBib's subscribable events.

### Available Events

There are various kinds of event types:
    - Pre*Command: these fire before a command gets executed. Hooks subscribing to these events
      are passed the argument dictionary which they can modify to their desire.
    - Post*Command: these fire after a command got executed but (generally) **before** the
      Database gets written to file, allowing final touch-ups and modifications to take place.
      The inputs to these hooks depend on the specific command firing the event (see below).
    - Pre*Parse: just like the Pre-Command events, these fire before a parser runs. As an input
      they generally get the driver input.
    - Post*Parse: these fire after a parser ran. They again allow final touch-ups of the
      generated dictionary of new entries.
    - Pre*Dump: these fire before an entry gets dumped. The hook can pre-process the entry to
      its desire. Changes will not become persistent in the Database.
    - Post*Dump: these fire after an entry got formatted as a string. The string can be
      post-processed with some final touch-ups.

All events are listed below.

### Usage

You can register a function to be executed when a certain event gets triggered as shown in the
following example:
```python
from pathlib import Path
from os import system
from cobib.config import Event

@Event.PostInitCommand.subscribe
def add_remote(root: Path, file: Path) -> None:
    system(f"git -C {root} remote add origin https://github.com/user/repo")
```
The above example gets run after the `init` command has finished. It adds a remote to the git
repository. This can be useful in combination with automatic pushing to the remote like done here:
```python
@Event.PostGitCommit.subscribe
def push_to_remote(root: Path, file: Path) -> None:
    system(f"git -C {root} push origin master")
```

It is important that you include the type hints as part of the function definition because these are
used during the config validation.

You can also subscribe the same function to multiple events at once as shown in the following
(rather non-sensible) example:
```python
from typing import Dict
from cobib.database import Entry

@Event.PostArxivParse.subscribe
@Event.PostDOIParse.subscribe
@Event.PostISBNParse.subscribe
def print_new_entries(bib: Dict[str, Entry) -> None:
    print("New entries being added: ", list(bib.keys()))
```
"""

from __future__ import annotations

import logging
from argparse import Namespace
from enum import Enum
from itertools import zip_longest
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    ForwardRef,
    List,
    Optional,
    Set,
    Tuple,
    get_type_hints,
)

from cobib.utils.rel_path import RelPath

from .config import config

_FORWARD_REFS: Dict[str, str] = {}
if TYPE_CHECKING:
    from cobib.database import Entry
else:
    _FORWARD_REFS = {
        "ForwardRef('Entry')": "Entry",
    }

LOGGER = logging.getLogger(__name__)


class Event(Enum):
    # pylint: disable=invalid-name
    """Subscribable events triggered at runtime.

    The following sections list all events available in coBib. The heading of each section includes
    the name of the event, the type (always `Event`) and its unique identifier which is a tuple made
    up of a unique integer ID plus the `Callable` type hint required for the hooks subscribing to
    this particular event.
    """

    _annotation_: Any

    def __new__(cls, annotation: Any) -> Event:
        """Enum constructor.

        We overwrite the default constructor to handle the "overloaded" use of the Enum values in
        which we store the non-unique Callable type hints. The actual values of the Enum are simply
        integers.

        Args:
            annotation: the expected Callable type hint for the hooks registering to this event.

        Returns:
            The new Event instance.
        """
        value = len(cls.__members__) + 1
        obj = object.__new__(cls)
        obj._value_ = (value, annotation)
        obj._annotation_ = annotation
        return obj  # type: ignore[no-any-return]

    PreAddCommand: Event = Callable[[Namespace], None]  # type: ignore[assignment]
    """
    Fires:
        Before starting the `cobib.commands.add.AddCommand`.

    Arguments:
        - `largs`: the `Namespace` dictionary of of command arguments.

    Returns:
        Nothing. But the `Namespace` can be modified, affecting the command execution.
    """
    PostAddCommand: Event = Callable[[Dict[str, "Entry"]], None]  # type: ignore[assignment]
    """
    Fires:
        Before finishing the `cobib.commands.add.AddCommand`.

    Arguments:
        - `new_entries`: the dictionary of new entries to be added to the database.

    Returns:
        Nothing. But the dictionary of new entries can be modified before the changes are made
        persistent in the database.

    Note:
        This event fires *before* starting the `cobib.commands.edit.EditCommand` which starts if
        manual entry addition is requested.
    """

    PreDeleteCommand: Event = Callable[[Namespace], None]  # type: ignore[assignment]
    """
    Fires:
        Before starting the `cobib.commands.delete.DeleteCommand`.

    Arguments:
        - `largs`: the `Namespace` dictionary of of command arguments.

    Returns:
        Nothing. But the `Namespace` can be modified, affecting the command execution.
    """
    PostDeleteCommand: Event = Callable[[Set[str]], None]  # type: ignore[assignment]
    """Gets fired before finishing the `cobib.commands.DeleteCommand`. The deleted entry labels are
    provided as input. Modifying them has no effect."""

    PreEditCommand: Event = Callable[[Namespace], None]  # type: ignore[assignment]
    """
    Fires:
        Before starting the `cobib.commands.edit.EditCommand`.

    Arguments:
        - `largs`: the `Namespace` dictionary of of command arguments.

    Returns:
        Nothing. But the `Namespace` can be modified, affecting the command execution.
    """
    PostEditCommand: Event = Callable[["Entry"], None]  # type: ignore[assignment]
    """Gets fired before finishing the `cobib.commands.EditCommand`. The new entry gets provided as
    input and it may be modified. However, renaming the label will no longer be possible."""

    PreExportCommand: Event = Callable[[Namespace], None]  # type: ignore[assignment]
    """
    Fires:
        Before starting the `cobib.commands.export.ExportCommand`.

    Arguments:
        - `largs`: the `Namespace` dictionary of of command arguments.

    Returns:
        Nothing. But the `Namespace` can be modified, affecting the command execution.
    """
    PostExportCommand: Event = Callable[[List[str], Namespace], None]  # type: ignore[assignment]
    """
    Fires:
        Before finishing the `cobib.commands.export.ExportCommand`.

    Arguments:
        - `labels`: the list of exported labels.
        - `largs`: the `Namespace` dictionary of command arguments.

    Returns:
        Nothing.

    Note:
        If exporting to a zip file, it will only be closed *after* this event got fired.
    """

    PreInitCommand: Event = Callable[[Namespace], None]  # type: ignore[assignment]
    """
    Fires:
        Before starting the `cobib.commands.init.InitCommand`.

    Arguments:
        - `largs`: the `Namespace` dictionary of of command arguments.

    Returns:
        Nothing. But the `Namespace` can be modified, affecting the command execution.
    """
    PostInitCommand: Event = Callable[[Path, Path], None]  # type: ignore[assignment]
    """
    Fires:
        Before finishing the `cobib.commands.init.InitCommand`.

    Arguments:
        - `root`: the `Path` to the root directory where the database file resides.
        - `file`: the `Path` to the database file.

    Returns:
        Nothing.
    """

    PreListCommand: Event = Callable[[Namespace], None]  # type: ignore[assignment]
    """
    Fires:
        Before starting the `cobib.commands.list.ListCommand`.

    Arguments:
        - `largs`: the `Namespace` dictionary of of command arguments.

    Returns:
        Nothing. But the `Namespace` can be modified, affecting the command execution.
    """
    PostListCommand: Event = Callable[[List[str]], None]  # type: ignore[assignment]
    """
    Fires:
        Before finishing the `cobib.commands.list.ListCommand`.

    Arguments:
        - `labels`: the list of labels.

    Returns:
        Nothing.
    """

    PreModifyCommand: Event = Callable[[Namespace], None]  # type: ignore[assignment]
    """
    Fires:
        Before starting the `cobib.commands.modify.ModifyCommand`.

    Arguments:
        - `largs`: the `Namespace` dictionary of of command arguments.

    Returns:
        Nothing. But the `Namespace` can be modified, affecting the command execution.
    """
    PostModifyCommand: Event = Callable[[List[str], bool], None]  # type: ignore[assignment]
    """
    Fires:
        Before finishing the `cobib.commands.modify.ModifyCommand`.

    Arguments:
        - `labels`: the list of modified labels.
        - `dry`: whether the command was run in dry-mode.

    Returns:
        Nothing.
    """

    PreOpenCommand: Event = Callable[[Namespace], None]  # type: ignore[assignment]
    """
    Fires:
        Before starting the `cobib.commands.open.OpenCommand`.

    Arguments:
        - `largs`: the `Namespace` dictionary of of command arguments.

    Returns:
        Nothing. But the `Namespace` can be modified, affecting the command execution.
    """
    PostOpenCommand: Event = Callable[[List[str]], None]  # type: ignore[assignment]
    """
    Fires:
        Before finishing the `cobib.commands.open.OpenCommand`.

    Arguments:
        - `labels`: the list of opened labels.

    Returns:
        Nothing.
    """

    PreRedoCommand: Event = Callable[[Namespace], None]  # type: ignore[assignment]
    """
    Fires:
        Before starting the `cobib.commands.redo.RedoCommand`.

    Arguments:
        - `largs`: the `Namespace` dictionary of of command arguments.

    Returns:
        Nothing. But the `Namespace` can be modified, affecting the command execution.

    Note:
        As of right now, the `redo` command does not take any arguments, so there is nothing to
        modify here.
    """
    PostRedoCommand: Event = Callable[[Path, str], None]  # type: ignore[assignment]
    """
    Fires:
        Before finishing the `cobib.commands.redo.RedoCommand`.

    Arguments:
        - `root`: the `Path` to the root directory where the database file resides.
        - `sha`: the SHA of the redone git-commit.

    Returns:
        Nothing.
    """

    PreSearchCommand: Event = Callable[[Namespace], None]  # type: ignore[assignment]
    """
    Fires:
        Before starting the `cobib.commands.search.SearchCommand`.

    Arguments:
        - `largs`: the `Namespace` dictionary of of command arguments.

    Returns:
        Nothing. But the `Namespace` can be modified, affecting the command execution.
    """
    PostSearchCommand: Event = Callable[[int, List[str]], None]  # type: ignore[assignment]
    """
    Fires:
        Before finishing the `cobib.commands.search.SearchCommand`.

    Arguments:
        - `hits`: the number of matches found in the database.
        - `labels`: the list of matching labels.

    Returns:
        Nothing.
    """

    PreShowCommand: Event = Callable[[Namespace], None]  # type: ignore[assignment]
    """
    Fires:
        Before starting the `cobib.commands.show.ShowCommand`.

    Arguments:
        - `largs`: the `Namespace` dictionary of of command arguments.

    Returns:
        Nothing. But the `Namespace` can be modified, affecting the command execution.
    """
    PostShowCommand: Event = Callable[[str], Optional[str]]  # type: ignore[assignment]
    """
    Fires:
        Before finishing the `cobib.commands.show.ShowCommand`.

    Arguments:
        - `entry_str`: the formatted string-representation of the shown `Entry`.

    Returns:
        Optionally a new (or updated) string to represent the shown `Entry`.

    Note:
        If a registered hook returns a new string, no subsequent hooks will be run!
    """

    PreUndoCommand: Event = Callable[[Namespace], None]  # type: ignore[assignment]
    """
    Fires:
        Before starting the `cobib.commands.undo.UndoCommand`.

    Arguments:
        - `largs`: the `Namespace` dictionary of of command arguments.

    Returns:
        Nothing. But the `Namespace` can be modified, affecting the command execution.
    """
    PostUndoCommand: Event = Callable[[Path, str], None]  # type: ignore[assignment]
    """
    Fires:
        Before finishing the `cobib.commands.undo.UndoCommand`.

    Arguments:
        - `root`: the `Path` to the root directory where the database file resides.
        - `sha`: the SHA of the undone git-commit.

    Returns:
        Nothing.
    """

    PreBibtexParse: Event = Callable[[str], Optional[str]]  # type: ignore[assignment]
    """
    Fires:
        Before starting `cobib.parsers.bibtex.BibtexParser.parse`.

    Arguments:
        - `string`: the string to be parsed as BibTeX.

    Returns:
        Optionally a new (or updated) string to be parsed as BibTeX.

    Note:
        If a registered hook returns a new string, no subsequent hooks will be run!
    """
    PostBibtexParse: Event = Callable[[Dict[str, "Entry"]], None]  # type: ignore[assignment]
    """
    Fires:
        Before finishing `cobib.parsers.bibtex.BibtexParser.parse`.

    Arguments:
        - `bib`: a dictionary of the new `Entry` instances stored under their `label` as keys.

    Returns:
        Nothing. But the dictionary can be modified in-place such that the changes will be
        propagated to the database.
    """
    PreBibtexDump: Event = Callable[["Entry"], None]  # type: ignore[assignment]
    """
    Fires:
        Before starting `cobib.parsers.bibtex.BibtexParser.dump`.

    Arguments:
        - `Entry`: the `Entry` object to be dumped in BibTeX format.

    Returns:
        Nothing. But the object can be modified in-place. Changes will *not* become persistent in
        the database.
    """
    PostBibtexDump: Event = Callable[[str], Optional[str]]  # type: ignore[assignment]
    """
    Fires:
        Before finishing `cobib.parsers.bibtex.BibtexParser.dump`.

    Arguments:
        - `string`: the string-representation of the `Entry` to be dumped as BibTeX.

    Returns:
        Optionally a new (or updated) string to be dumped.

    Note:
        If a registered hook returns a new string, no subsequent hooks will be run!
    """

    PreYAMLParse: Event = Callable[[str], Optional[str]]  # type: ignore[assignment]
    """
    Fires:
        Before starting `cobib.parsers.yaml.YAMLParser.parse`.

    Arguments:
        - `string`: the string to be parsed as YAML.

    Returns:
        Optionally a new (or updated) string to be parsed as YAML.

    Note:
        If a registered hook returns a new string, no subsequent hooks will be run!
    """
    PostYAMLParse: Event = Callable[[Dict[str, "Entry"]], None]  # type: ignore[assignment]
    """
    Fires:
        Before finishing `cobib.parsers.yaml.YAMLParser.parse`.

    Arguments:
        - `bib`: a dictionary of the new `Entry` instances stored under their `label` as keys.

    Returns:
        Nothing. But the dictionary can be modified in-place such that the changes will be
        propagated to the database.
    """
    PreYAMLDump: Event = Callable[["Entry"], None]  # type: ignore[assignment]
    """
    Fires:
        Before starting `cobib.parsers.yaml.YAMLParser.dump`.

    Arguments:
        - `Entry`: the `Entry` object to be dumped in YAML format.

    Returns:
        Nothing. But the object can be modified in-place. Changes will *not* become persistent in
        the database.
    """
    PostYAMLDump: Event = Callable[[str], Optional[str]]  # type: ignore[assignment]
    """
    Fires:
        Before finishing `cobib.parsers.yaml.YAMLParser.dump`.

    Arguments:
        - `string`: the string-representation of the `Entry` to be dumped as YAML.

    Returns:
        Optionally a new (or updated) string to be dumped.

    Note:
        If a registered hook returns a new string, no subsequent hooks will be run!
    """

    PreArxivParse: Event = Callable[[str], Optional[str]]  # type: ignore[assignment]
    """
    Fires:
        Before starting `cobib.parsers.arxiv.ArxivParser.parse`.

    Arguments:
        - `string`: the string to be parsed as an arXiv ID.

    Returns:
        Optionally a new (or updated) string to be parsed as an arXiv ID.

    Note:
        If a registered hook returns a new string, no subsequent hooks will be run!
    """
    PostArxivParse: Event = Callable[[Dict[str, "Entry"]], None]  # type: ignore[assignment]
    """
    Fires:
        Before finishing `cobib.parsers.arxiv.ArxivParser.parse`.

    Arguments:
        - `bib`: a dictionary of the new `Entry` instances stored under their `label` as keys.

    Returns:
        Nothing. But the dictionary can be modified in-place such that the changes will be
        propagated to the database.
    """

    PreDOIParse: Event = Callable[[str], Optional[str]]  # type: ignore[assignment]
    """
    Fires:
        Before starting `cobib.parsers.doi.DOIParser.parse`.

    Arguments:
        - `string`: the string to be parsed as a DOI.

    Returns:
        Optionally a new (or updated) string to be parsed as a DOI.

    Note:
        If a registered hook returns a new string, no subsequent hooks will be run!
    """
    PostDOIParse: Event = Callable[[Dict[str, "Entry"]], None]  # type: ignore[assignment]
    """
    Fires:
        Before finishing `cobib.parsers.doi.DOIParser.parse`.

    Arguments:
        - `bib`: a dictionary of the new `Entry` instances stored under their `label` as keys.

    Returns:
        Nothing. But the dictionary can be modified in-place such that the changes will be
        propagated to the database.
    """

    PreISBNParse: Event = Callable[[str], Optional[str]]  # type: ignore[assignment]
    """
    Fires:
        Before starting `cobib.parsers.isbn.ISBNParser.parse`.

    Arguments:
        - `string`: the string to be parsed as an ISBN.

    Returns:
        Optionally a new (or updated) string to be parsed as an ISBN.

    Note:
        If a registered hook returns a new string, no subsequent hooks will be run!
    """
    PostISBNParse: Event = Callable[[Dict[str, "Entry"]], None]  # type: ignore[assignment]
    """
    Fires:
        Before finishing `cobib.parsers.isbn.ISBNParser.parse`.

    Arguments:
        - `bib`: a dictionary of the new `Entry` instances stored under their `label` as keys.

    Returns:
        Nothing. But the dictionary can be modified in-place such that the changes will be
        propagated to the database.
    """

    PreURLParse: Event = Callable[[str], Optional[str]]  # type: ignore[assignment]
    """
    Fires:
        Before starting `cobib.parsers.url.URLParser.parse`.

    Arguments:
        - `string`: the string to be parsed as a URL.

    Returns:
        Optionally a new (or updated) string to be parsed as a URL.

    Note:
        If a registered hook returns a new string, no subsequent hooks will be run!
    """
    PostURLParse: Event = Callable[[Dict[str, "Entry"]], None]  # type: ignore[assignment]
    """
    Fires:
        Before finishing `cobib.parsers.url.URLParser.parse`.

    Arguments:
        - `bib`: a dictionary of the new `Entry` instances stored under their `label` as keys.

    Returns:
        Nothing. But the dictionary can be modified in-place such that the changes will be
        propagated to the database.
    """

    PreFileDownload: Event = Callable[  # type: ignore[assignment]
        [str, str, Optional[str]], Optional[Tuple[str, str, Optional[str]]]
    ]
    """
    Fires:
        Before starting `cobib.utils.file_downloader.FileDownloader.download`.

    Arguments:
        - `url`: the URL from which to download a file.
        - `label`: the label of the `Entry` to which the file belongs.
        - `folder`: an optional folder where the file will be stored.

    Returns:
        This can optionally return a tuple overwriting the input arguments.

    Note:
        If a registered hook returns a new tuple of arguments, no subsequent hooks will be run!
    """
    PostFileDownload: Event = Callable[[RelPath], Optional[RelPath]]  # type: ignore[assignment]
    """
    Fires:
        Before finishing `cobib.utils.file_downloader.FileDownloader.download` if and only if the
        download was successful.

    Arguments:
        - `path`: the `RelPath` to the freshly downloaded file.

    Returns:
        An optional new `RelPath`.

    Note:
        If a registered hook returns a new path, no subsequent hooks will be run!
    """

    PreGitCommit: Event = Callable[  # type: ignore[assignment]
        [str, Optional[Dict[str, Any]]], Optional[str]
    ]
    """
    Fires:
        Before starting `cobib.commands.base_command.Command.git` (i.e. whenever an automatic
        git-commit occurs).

    Arguments:
        - `msg`: the commit message.
        - `args`: an optional dictionary of keyword arguments provided to the command which
                  triggered this commit.

    Returns:
        Optionally a new commit message.

    Note:
        If a registered hook returns a new commit message, no subsequent hooks will be run!
    """
    PostGitCommit: Event = Callable[[Path, Path], None]  # type: ignore[assignment]
    """
    Fires:
        Before finishing `cobib.commands.base_command.Command.git` (i.e. whenever an automatic
        git-commit occurs).

    Arguments:
        - `root`: the `Path` to the root git directory where the database file resides.
        - `file`: the `Path` to the database file.

    Returns:
        Nothing.
    """

    def subscribe(self, function: Callable) -> Callable:  # type: ignore[type-arg]
        """Subscribes the provided function to this Event.

        Usage:
            ```python
            @Event.PostGitCommit.subscribe
            def push_to_remote(root: Path, file: Path) -> None:
                os.system(f"git -C {root} push")
            ```

        Args:
            function: the callable to execute when this Event fires.

        Returns:
            The same callable which ensures that we can chain multiple subscription decorators to
            subscribe the same function to multiple events.
        """
        if self not in config.events.keys():
            config.events[self] = []
        LOGGER.debug("Subscribing new hook to %s.", str(self))
        config.events[self].append(function)
        return function

    def fire(self, *args: Any, **kwargs: Any) -> Any:
        """Fires the Event by executing all subscribed hooks.

        Note, that if a hook has a non-None return value this method will return prematurely
        regardless of whether more hooks are subscribed.
        The exact signature of the hooks depends on the Event as indicated above.

        Args:
            args: positional hook arguments.
            kwargs: keyword hook arguments.

        Returns:
            Whatever a hook returns or `None` as a default.
        """
        LOGGER.debug("Firing %s.", str(self))
        if self not in config.events.keys():
            return None
        for hook in config.events[self]:
            res = hook(*args, **kwargs)
            if res is not None:
                return res
        return None

    def validate(self) -> bool:
        """Validates the type hints of all subscribed functions against the expected one.

        Returns:
            Whether or not all subscribers have the correct type hint.
        """
        if self not in config.events.keys():
            return True

        def _compare_types(expected: Any, provided: Any) -> List[bool]:
            result = []
            for exp, pro in zip_longest(expected, provided):
                try:
                    result.extend(_compare_types(exp.__args__, pro.__args__))
                except AttributeError:
                    if isinstance(exp, ForwardRef):
                        result.append(_FORWARD_REFS[str(exp)] in str(pro))
                    elif pro == "None":
                        result.append(exp == type(None))
                    else:
                        result.append(exp == pro)
            return result

        LOGGER.debug("Validating hooks subscribed to %s.", str(self))
        annotation = self._annotation_.__args__
        for idx, sub in enumerate(config.events[self]):
            sub_ann = get_type_hints(sub).values()
            if not all(_compare_types(annotation, sub_ann)):
                LOGGER.debug(
                    "Hook #%s has a mismatching annotation: %s instead of %s",
                    idx,
                    annotation,
                    sub_ann,
                )
                return False
        return True
