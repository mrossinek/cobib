"""coBib's subscribable events.

### Available Events

There are various kinds of event types:
    - Pre*Command: these fire before a command gets executed. Hooks subscribing to these events
      are passed an instance of the command which will be populated with the original command-line
      arguments as well as the resulting `argparse.Namespace`.
    - Post*Command: these fire after a command got executed but (generally) **before** the
      Database gets written to file, allowing final touch-ups and modifications to take place.
      Just like the `Pre*Command` events, the input will be an instance of the command through which
      a user can modify the command data at runtime.
    - Pre*Import: these fire before an importer gets executed. Hooks subscribing to these events
      are passed an instance of the importer which will be populated with the original command-line
      arguments as well as the resulting `argparse.Namespace`.
    - Post*Import: these fire after an importer got executed but (generally) **before** the
      Database gets written to file, allowing final touch-ups and modifications to take place.
      Just like the `Pre*Import` events, the input will be an instance of the importer through which
      a user can modify the command data at runtime.
    - Pre*Parse: just like the Pre-Command events, these fire before a parser runs. As an input
      they generally get the driver input.
    - Post*Parse: these fire after a parser ran. They again allow final touch-ups of the
      generated dictionary of new entries.
    - Pre*Dump: these fire before an entry gets dumped. The hook can pre-process the entry to
      its desire. Changes will not become persistent in the Database.
    - Post*Dump: these fire after an entry got formatted as a string. The string can be
      post-processed with some final touch-ups.
    - and finally there a few specific events not belonging to any of the categories mentioned
      above, examples of which are the `PreGitCommit` and `PostGitCommit` events.

All events are listed below.

### Usage

You can register a function to be executed when a certain event gets triggered as shown in the
following example:
```python
from os import system
from cobib.config import Event
from cobib.commands import InitCommand

@Event.PostInitCommand.subscribe
def add_remote(cmd: InitCommand) -> None:
    system(f"git -C {cmd.root} remote add origin https://github.com/user/repo")
```
The above example gets run after the `init` command has finished. It adds a remote to the git
repository. This can be useful in combination with automatic pushing to the remote like done here:
```python
from pathlib import Path
from os import system
from cobib.config import Event

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

You can find some useful examples on
[this wiki page](https://gitlab.com/cobib/cobib/-/wikis/Useful-Event-Hooks).
"""

from __future__ import annotations

import logging
from enum import Enum
from itertools import zip_longest
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, ForwardRef, Optional, Tuple, get_type_hints

from cobib.utils.rel_path import RelPath

from .config import config

_FORWARD_REFS: dict[str, str] = {}
if TYPE_CHECKING:
    from cobib import commands, importers
    from cobib.database import Entry
else:
    _FORWARD_REFS = {
        "ForwardRef('Entry')": "Entry",
        "ForwardRef('commands.AddCommand')": "cobib.commands.add.AddCommand",
        "ForwardRef('commands.DeleteCommand')": "cobib.commands.delete.DeleteCommand",
        "ForwardRef('commands.EditCommand')": "cobib.commands.edit.EditCommand",
        "ForwardRef('commands.ExportCommand')": "cobib.commands.export.ExportCommand",
        "ForwardRef('commands.GitCommand')": "cobib.commands.git.GitCommand",
        "ForwardRef('commands.ImportCommand')": "cobib.commands.import_.ImportCommand",
        "ForwardRef('commands.InitCommand')": "cobib.commands.init.InitCommand",
        "ForwardRef('commands.ListCommand')": "cobib.commands.list_.ListCommand",
        "ForwardRef('commands.ModifyCommand')": "cobib.commands.modify.ModifyCommand",
        "ForwardRef('commands.OpenCommand')": "cobib.commands.open.OpenCommand",
        "ForwardRef('commands.RedoCommand')": "cobib.commands.redo.RedoCommand",
        "ForwardRef('commands.ReviewCommand')": "cobib.commands.review.ReviewCommand",
        "ForwardRef('commands.SearchCommand')": "cobib.commands.search.SearchCommand",
        "ForwardRef('commands.ShowCommand')": "cobib.commands.show.ShowCommand",
        "ForwardRef('commands.UndoCommand')": "cobib.commands.undo.UndoCommand",
        "ForwardRef('importers.ZoteroImporter')": "cobib.importers.zotero.ZoteroImporter",
    }

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


class Event(Enum):
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
        return obj

    PreAddCommand: Event = Callable[["commands.AddCommand"], None]  # type: ignore[assignment]
    """
    Fires:
        Before starting the `cobib.commands.add.AddCommand`.

    Arguments:
        - `cobib.commands.add.AddCommand`: the command instance that is about to run.

    Returns:
        Nothing. But the command attributes can be modified, affecting the execution.
    """
    PostAddCommand: Event = Callable[["commands.AddCommand"], None]  # type: ignore[assignment]
    """
    Fires:
        Before finishing the `cobib.commands.add.AddCommand`.

    Arguments:
        - `cobib.commands.add.AddCommand`: the command instance that just ran.

    Returns:
        Nothing. But the command attributes can be modified, affecting the execution.

    Note:
        This event fires *before* starting the `cobib.commands.edit.EditCommand` which starts if
        manual entry addition is requested.
    """

    PreDeleteCommand: Event = Callable[["commands.DeleteCommand"], None]  # type: ignore[assignment]
    """
    Fires:
        Before starting the `cobib.commands.delete.DeleteCommand`.

    Arguments:
        - `cobib.commands.delete.DeleteCommand`: the command instance that is about to run.

    Returns:
        Nothing. But the command attributes can be modified, affecting the execution.
    """
    PostDeleteCommand: Event = Callable[["commands.DeleteCommand"], None]  # type: ignore[assignment]
    """
    Fires:
        Before finishing the `cobib.commands.delete.DeleteCommand`.

    Arguments:
        - `cobib.commands.delete.DeleteCommand`: the command instance that just ran.

    Returns:
        Nothing. While the deleted entry labels are accessible, modifying them has no effect.
    """

    PreEditCommand: Event = Callable[["commands.EditCommand"], None]  # type: ignore[assignment]
    """
    Fires:
        Before starting the `cobib.commands.edit.EditCommand`.

    Arguments:
        - `cobib.commands.edit.EditCommand`: the command instance that is about to run.

    Returns:
        Nothing. But the command attributes can be modified, affecting the execution.
    """
    PostEditCommand: Event = Callable[["commands.EditCommand"], None]  # type: ignore[assignment]
    """
    Fires:
        Before finishing the `cobib.commands.edit.EditCommand`.

    Arguments:
        - `cobib.commands.edit.EditCommand`: the command instance that just ran.

    Returns:
        Nothing. While the edited entry is accessible, modifying it has no effect.
    """

    PreExportCommand: Event = Callable[["commands.ExportCommand"], None]  # type: ignore[assignment]
    """
    Fires:
        Before starting the `cobib.commands.export.ExportCommand`.

    Arguments:
        - `cobib.commands.export.ExportCommand`: the command instance that is about to run.

    Returns:
        Nothing. But the command attributes can be modified, affecting the execution.
    """
    PostExportCommand: Event = Callable[["commands.ExportCommand"], None]  # type: ignore[assignment]
    """
    Fires:
        Before finishing the `cobib.commands.export.ExportCommand`.

    Arguments:
        - `cobib.commands.export.ExportCommand`: the command instance that just ran.

    Returns:
        Nothing. The files to which has been exported are still accessible and open.
    """

    PreGitCommand: Event = Callable[["commands.GitCommand"], None]  # type: ignore[assignment]
    """
    Fires:
        Before starting the `cobib.commands.git.GitCommand`.

    Arguments:
        - `cobib.commands.git.GitCommand`: the command instance that is about to run.

    Returns:
        Nothing. But the command attributes can be modified, affecting the execution.
    """
    PostGitCommand: Event = Callable[["commands.GitCommand"], None]  # type: ignore[assignment]
    """
    Fires:
        Before finishing the `cobib.commands.git.GitCommand`.

    Arguments:
        - `cobib.commands.git.GitCommand`: the command instance that just ran.

    Returns:
        Nothing.
    """

    PreImportCommand: Event = Callable[["commands.ImportCommand"], None]  # type: ignore[assignment]
    """
    Fires:
        Before starting the `cobib.commands.import_.ImportCommand`.

    Arguments:
        - `cobib.commands.import_.ImportCommand`: the command instance that is about to run.

    Returns:
        Nothing. But the command attributes can be modified, affecting the execution.
    """
    PostImportCommand: Event = Callable[["commands.ImportCommand"], None]  # type: ignore[assignment]
    """
    Fires:
        Before finishing the `cobib.commands.import_.ImportCommand`.

    Arguments:
        - `cobib.commands.import_.ImportCommand`: the command instance that just ran.

    Returns:
        Nothing. But the dictionary of new entries can be modified before the changes are made
        persistent in the database.
    """

    PreInitCommand: Event = Callable[["commands.InitCommand"], None]  # type: ignore[assignment]
    """
    Fires:
        Before starting the `cobib.commands.init.InitCommand`.

    Arguments:
        - `cobib.commands.init.InitCommand`: the command instance that is about to run.

    Returns:
        Nothing. But the command attributes can be modified, affecting the execution.
    """
    PostInitCommand: Event = Callable[["commands.InitCommand"], None]  # type: ignore[assignment]
    """
    Fires:
        Before finishing the `cobib.commands.init.InitCommand`.

    Arguments:
        - `cobib.commands.init.InitCommand`: the command instance that just ran.

    Returns:
        Nothing.
    """

    PreListCommand: Event = Callable[["commands.ListCommand"], None]  # type: ignore[assignment]
    """
    Fires:
        Before starting the `cobib.commands.list_.ListCommand`.

    Arguments:
        - `cobib.commands.list_.ListCommand`: the command instance that is about to run.

    Returns:
        Nothing. But the command attributes can be modified, affecting the execution.
    """
    PostListCommand: Event = Callable[["commands.ListCommand"], None]  # type: ignore[assignment]
    """
    Fires:
        Before finishing the `cobib.commands.list_.ListCommand`.

    Arguments:
        - `cobib.commands.list_.ListCommand`: the command instance that just ran.

    Returns:
        Nothing.
    """

    PreModifyCommand: Event = Callable[["commands.ModifyCommand"], None]  # type: ignore[assignment]
    """
    Fires:
        Before starting the `cobib.commands.modify.ModifyCommand`.

    Arguments:
        - `cobib.commands.modify.ModifyCommand`: the command instance that is about to run.

    Returns:
        Nothing. But the command attributes can be modified, affecting the execution.
    """
    PostModifyCommand: Event = Callable[["commands.ModifyCommand"], None]  # type: ignore[assignment]
    """
    Fires:
        Before finishing the `cobib.commands.modify.ModifyCommand`.

    Arguments:
        - `cobib.commands.modify.ModifyCommand`: the command instance that just ran.

    Returns:
        Nothing. But the modified entries are still accessible before written to the database.
    """

    PreOpenCommand: Event = Callable[["commands.OpenCommand"], None]  # type: ignore[assignment]
    """
    Fires:
        Before starting the `cobib.commands.open.OpenCommand`.

    Arguments:
        - `cobib.commands.open.OpenCommand`: the command instance that is about to run.

    Returns:
        Nothing. But the command attributes can be modified, affecting the execution.
    """
    PostOpenCommand: Event = Callable[["commands.OpenCommand"], None]  # type: ignore[assignment]
    """
    Fires:
        Before finishing the `cobib.commands.open.OpenCommand`.

    Arguments:
        - `cobib.commands.open.OpenCommand`: the command instance that just ran.

    Returns:
        Nothing.
    """

    PreRedoCommand: Event = Callable[["commands.RedoCommand"], None]  # type: ignore[assignment]
    """
    Fires:
        Before starting the `cobib.commands.redo.RedoCommand`.

    Arguments:
        - `cobib.commands.redo.RedoCommand`: the command instance that is about to run.

    Returns:
        Nothing. But the command attributes can be modified, affecting the execution.
    """
    PostRedoCommand: Event = Callable[["commands.RedoCommand"], None]  # type: ignore[assignment]
    """
    Fires:
        Before finishing the `cobib.commands.redo.RedoCommand`.

    Arguments:
        - `cobib.commands.redo.RedoCommand`: the command instance that just ran.

    Returns:
        Nothing.
    """

    PreReviewCommand: Event = Callable[["commands.ReviewCommand"], None]  # type: ignore[assignment]
    """
    Fires:
        Before starting the `cobib.commands.review.ReviewCommand`.
        The only logic which is done prior to this event is the retrieval of the command arguments
        from a previous review process when the `--resume` option has been specified.

    Arguments:
        - `cobib.commands.review.ReviewCommand`: the command instance that is about to run.

    Returns:
        Nothing. But the command attributes can be modified, affecting the execution.
    """
    PostReviewCommand: Event = Callable[["commands.ReviewCommand"], None]  # type: ignore[assignment]
    """
    Fires:
        Before finishing the `cobib.commands.review.ReviewCommand`.

    Arguments:
        - `cobib.commands.review.ReviewCommand`: the command instance that just ran.

    Returns:
        Nothing.
    """

    PreSearchCommand: Event = Callable[["commands.SearchCommand"], None]  # type: ignore[assignment]
    """
    Fires:
        Before starting the `cobib.commands.search.SearchCommand`.

    Arguments:
        - `cobib.commands.search.SearchCommand`: the command instance that is about to run.

    Returns:
        Nothing. But the command attributes can be modified, affecting the execution.
    """
    PostSearchCommand: Event = Callable[["commands.SearchCommand"], None]  # type: ignore[assignment]
    """
    Fires:
        Before finishing the `cobib.commands.search.SearchCommand`.

    Arguments:
        - `cobib.commands.search.SearchCommand`: the command instance that just ran.

    Returns:
        Nothing. But the search results are still accessible before being rendered for the user.
    """

    PreShowCommand: Event = Callable[["commands.ShowCommand"], None]  # type: ignore[assignment]
    """
    Fires:
        Before starting the `cobib.commands.show.ShowCommand`.

    Arguments:
        - `cobib.commands.show.ShowCommand`: the command instance that is about to run.

    Returns:
        Nothing. But the command attributes can be modified, affecting the execution.
    """
    PostShowCommand: Event = Callable[["commands.ShowCommand"], None]  # type: ignore[assignment]
    """
    Fires:
        Before finishing the `cobib.commands.show.ShowCommand`.

    Arguments:
        - `cobib.commands.show.ShowCommand`: the command instance that just ran.

    Returns:
        Nothing. But the string-represented entry is still accessible before being rendered.
    """

    PreUndoCommand: Event = Callable[["commands.UndoCommand"], None]  # type: ignore[assignment]
    """
    Fires:
        Before starting the `cobib.commands.undo.UndoCommand`.

    Arguments:
        - `cobib.commands.undo.UndoCommand`: the command instance that is about to run.

    Returns:
        Nothing. But the command attributes can be modified, affecting the execution.
    """
    PostUndoCommand: Event = Callable[["commands.UndoCommand"], None]  # type: ignore[assignment]
    """
    Fires:
        Before finishing the `cobib.commands.undo.UndoCommand`.

    Arguments:
        - `cobib.commands.undo.UndoCommand`: the command instance that just ran.

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
        - `cobib.database.Entry`: the `Entry` object to be dumped in BibTeX format.

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
        - `cobib.database.Entry`: the `Entry` object to be dumped in YAML format.

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

    PreZoteroImport: Event = Callable[["importers.ZoteroImporter"], None]  # type: ignore[assignment]
    """
    Fires:
        Before starting `cobib.importers.zotero.ZoteroImporter.fetch`.

    Arguments:
        - `cobib.importers.zotero.ZoteroImporter`: the importer instance that is about to run.

    Returns:
        Nothing. But the importer attributes can be modified, affecting the execution.
    """
    PostZoteroImport: Event = Callable[["importers.ZoteroImporter"], None]  # type: ignore[assignment]
    """
    Fires:
        Before finishing `cobib.importers.zotero.ZoteroImporter.fetch`.

    Arguments:
        - `cobib.importers.zotero.ZoteroImporter`: the importer instance that is about to run.

    Returns:
        Nothing. But the importer attributes can be modified, affecting the execution.

    Note:
        - The entry labels will not have been mapped or disambiguated at this point.
    """

    PreFileDownload: Event = Callable[  # type: ignore[assignment]
        [str, str, Optional[str], Optional[Dict[str, str]]],
        Optional[Tuple[str, str, Optional[str], Optional[Dict[str, str]]]],
    ]
    """
    Fires:
        Before starting `cobib.utils.file_downloader.FileDownloader.download`.

    Arguments:
        - `url`: the URL from which to download a file.
        - `label`: the label of the `Entry` to which the file belongs.
        - `folder`: an optional folder where the file will be stored.
        - `headers`: an optional headers dictionary for the download `GET` request.

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

    PreGitCommit: Event = Callable[[str, Optional[Dict[str, Any]]], Optional[str]]  # type: ignore[assignment]
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
        if self not in config.events:
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
        if self not in config.events:
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
        if self not in config.events:
            return True

        def _compare_types(expected: Any, provided: Any) -> list[bool]:
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
