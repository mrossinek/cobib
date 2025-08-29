"""coBib's subscribable events.

.. include:: ../man/cobib-event.7.html_fragment
"""

from __future__ import annotations

import logging
from enum import Enum
from itertools import zip_longest
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    ForwardRef,
    Optional,
    Tuple,
    cast,
    get_type_hints,
)

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
        "ForwardRef('commands.ManCommand')": "cobib.commands.man.ManCommand",
        "ForwardRef('commands.ModifyCommand')": "cobib.commands.modify.ModifyCommand",
        "ForwardRef('commands.NoteCommand')": "cobib.commands.note.NoteCommand",
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

    .. warning::
       The unique integer identifying a particular event is **not** guaranteed to be stable between
       multiple releases of coBib! Thus, it should not be relied upon in any way!
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

    PreAddCommand = cast("Event", Callable[["commands.AddCommand"], None])
    """
    Fires:
        Before starting the `cobib.commands.add.AddCommand`.

    Arguments:
        `cobib.commands.add.AddCommand`: the command instance that is about to run.

    Returns:
        Nothing. But the command attributes can be modified, affecting the execution.
    """
    PostAddCommand = cast("Event", Callable[["commands.AddCommand"], None])
    """
    Fires:
        Before finishing the `cobib.commands.add.AddCommand`.

    Arguments:
        `cobib.commands.add.AddCommand`: the command instance that just ran.

    Returns:
        Nothing. But the command attributes can be modified, affecting the execution.

    Note:
        This event fires **before** starting the `cobib.commands.edit.EditCommand` which starts if
        manual entry addition is requested.
    """

    PreDeleteCommand = cast("Event", Callable[["commands.DeleteCommand"], None])
    """
    Fires:
        Before starting the `cobib.commands.delete.DeleteCommand`.

    Arguments:
        `cobib.commands.delete.DeleteCommand`: the command instance that is about to run.

    Returns:
        Nothing. But the command attributes can be modified, affecting the execution.
    """
    PostDeleteCommand = cast("Event", Callable[["commands.DeleteCommand"], None])
    """
    Fires:
        Before finishing the `cobib.commands.delete.DeleteCommand`.

    Arguments:
        `cobib.commands.delete.DeleteCommand`: the command instance that just ran.

    Returns:
        Nothing. While the deleted entry labels are accessible, modifying them has no effect.
    """

    PreEditCommand = cast("Event", Callable[["commands.EditCommand"], None])
    """
    Fires:
        Before starting the `cobib.commands.edit.EditCommand`.

    Arguments:
        `cobib.commands.edit.EditCommand`: the command instance that is about to run.

    Returns:
        Nothing. But the command attributes can be modified, affecting the execution.
    """
    PostEditCommand = cast("Event", Callable[["commands.EditCommand"], None])
    """
    Fires:
        Before finishing the `cobib.commands.edit.EditCommand`.

    Arguments:
        `cobib.commands.edit.EditCommand`: the command instance that just ran.

    Returns:
        Nothing. While the edited entry is accessible, modifying it has no effect.
    """

    PreExportCommand = cast("Event", Callable[["commands.ExportCommand"], None])
    """
    Fires:
        Before starting the `cobib.commands.export.ExportCommand`.

    Arguments:
        `cobib.commands.export.ExportCommand`: the command instance that is about to run.

    Returns:
        Nothing. But the command attributes can be modified, affecting the execution.
    """
    PostExportCommand = cast("Event", Callable[["commands.ExportCommand"], None])
    """
    Fires:
        Before finishing the `cobib.commands.export.ExportCommand`.

    Arguments:
        `cobib.commands.export.ExportCommand`: the command instance that just ran.

    Returns:
        Nothing. The files to which has been exported are still accessible and open.
    """

    PreGitCommand = cast("Event", Callable[["commands.GitCommand"], None])
    """
    Fires:
        Before starting the `cobib.commands.git.GitCommand`.

    Arguments:
        `cobib.commands.git.GitCommand`: the command instance that is about to run.

    Returns:
        Nothing. But the command attributes can be modified, affecting the execution.
    """
    PostGitCommand = cast("Event", Callable[["commands.GitCommand"], None])
    """
    Fires:
        Before finishing the `cobib.commands.git.GitCommand`.

    Arguments:
        `cobib.commands.git.GitCommand`: the command instance that just ran.

    Returns:
        Nothing.
    """

    PreImportCommand = cast("Event", Callable[["commands.ImportCommand"], None])
    """
    Fires:
        Before starting the `cobib.commands.import_.ImportCommand`.

    Arguments:
        `cobib.commands.import_.ImportCommand`: the command instance that is about to run.

    Returns:
        Nothing. But the command attributes can be modified, affecting the execution.
    """
    PostImportCommand = cast("Event", Callable[["commands.ImportCommand"], None])
    """
    Fires:
        Before finishing the `cobib.commands.import_.ImportCommand`.

    Arguments:
        `cobib.commands.import_.ImportCommand`: the command instance that just ran.

    Returns:
        Nothing. But the dictionary of new entries can be modified before the changes are made
        persistent in the database.
    """

    PreInitCommand = cast("Event", Callable[["commands.InitCommand"], None])
    """
    Fires:
        Before starting the `cobib.commands.init.InitCommand`.

    Arguments:
        `cobib.commands.init.InitCommand`: the command instance that is about to run.

    Returns:
        Nothing. But the command attributes can be modified, affecting the execution.
    """
    PostInitCommand = cast("Event", Callable[["commands.InitCommand"], None])
    """
    Fires:
        Before finishing the `cobib.commands.init.InitCommand`.

    Arguments:
        `cobib.commands.init.InitCommand`: the command instance that just ran.

    Returns:
        Nothing.
    """

    PreListCommand = cast("Event", Callable[["commands.ListCommand"], None])
    """
    Fires:
        Before starting the `cobib.commands.list_.ListCommand`.

    Arguments:
        `cobib.commands.list_.ListCommand`: the command instance that is about to run.

    Returns:
        Nothing. But the command attributes can be modified, affecting the execution.
    """
    PostListCommand = cast("Event", Callable[["commands.ListCommand"], None])
    """
    Fires:
        Before finishing the `cobib.commands.list_.ListCommand`.

    Arguments:
        `cobib.commands.list_.ListCommand`: the command instance that just ran.

    Returns:
        Nothing. But the to-be-listed entries are still accessible before being rendered.
    """

    PreManCommand = cast("Event", Callable[["commands.ManCommand"], None])
    """
    Fires:
        Before starting the `cobib.commands.man.ManCommand`.

    Arguments:
        `cobib.commands.man.ManCommand`: the command instance that is about to run.

    Returns:
        Nothing. But the command attributes can be modified, affecting the execution.
    """
    PostManCommand = cast("Event", Callable[["commands.ManCommand"], None])
    """
    Fires:
        Before finishing the `cobib.commands.man.ManCommand`.

    Arguments:
        `cobib.commands.man.ManCommand`: the command instance that just ran.

    Returns:
        Nothing.
    """

    PreModifyCommand = cast("Event", Callable[["commands.ModifyCommand"], None])
    """
    Fires:
        Before starting the `cobib.commands.modify.ModifyCommand`.

    Arguments:
        `cobib.commands.modify.ModifyCommand`: the command instance that is about to run.

    Returns:
        Nothing. But the command attributes can be modified, affecting the execution.
    """
    PostModifyCommand = cast("Event", Callable[["commands.ModifyCommand"], None])
    """
    Fires:
        Before finishing the `cobib.commands.modify.ModifyCommand`.

    Arguments:
        `cobib.commands.modify.ModifyCommand`: the command instance that just ran.

    Returns:
        Nothing. But the modified entries are still accessible before written to the database.
    """

    PreNoteCommand = cast("Event", Callable[["commands.NoteCommand"], None])
    """
    Fires:
        Before starting the `cobib.commands.note.NoteCommand`.

    Arguments:
        `cobib.commands.note.NoteCommand`: the command instance that is about to run.

    Returns:
        Nothing. But the command attributes can be modified, affecting the execution.
    """
    PostNoteCommand = cast("Event", Callable[["commands.NoteCommand"], None])
    """
    Fires:
        Before finishing the `cobib.commands.note.NoteCommand`.

    Arguments:
        `cobib.commands.note.NoteCommand`: the command instance that just ran.

    Returns:
        Nothing. While the entry whose note was edited is accessible, modifying it has no effect.
    """

    PreOpenCommand = cast("Event", Callable[["commands.OpenCommand"], None])
    """
    Fires:
        Before starting the `cobib.commands.open.OpenCommand`.

    Arguments:
        `cobib.commands.open.OpenCommand`: the command instance that is about to run.

    Returns:
        Nothing. But the command attributes can be modified, affecting the execution.
    """
    PostOpenCommand = cast("Event", Callable[["commands.OpenCommand"], None])
    """
    Fires:
        Before finishing the `cobib.commands.open.OpenCommand`.

    Arguments:
        `cobib.commands.open.OpenCommand`: the command instance that just ran.

    Returns:
        Nothing.
    """

    PreRedoCommand = cast("Event", Callable[["commands.RedoCommand"], None])
    """
    Fires:
        Before starting the `cobib.commands.redo.RedoCommand`.

    Arguments:
        `cobib.commands.redo.RedoCommand`: the command instance that is about to run.

    Returns:
        Nothing. But the command attributes can be modified, affecting the execution.
    """
    PostRedoCommand = cast("Event", Callable[["commands.RedoCommand"], None])
    """
    Fires:
        Before finishing the `cobib.commands.redo.RedoCommand`.

    Arguments:
        `cobib.commands.redo.RedoCommand`: the command instance that just ran.

    Returns:
        Nothing.
    """

    PreReviewCommand = cast("Event", Callable[["commands.ReviewCommand"], None])
    """
    Fires:
        Before starting the `cobib.commands.review.ReviewCommand`.
        The only logic which is done prior to this event is the retrieval of the command arguments
        from a previous review process when the `--resume` option has been specified.

    Arguments:
        `cobib.commands.review.ReviewCommand`: the command instance that is about to run.

    Returns:
        Nothing. But the command attributes can be modified, affecting the execution.
    """
    PostReviewCommand = cast("Event", Callable[["commands.ReviewCommand"], None])
    """
    Fires:
        Before finishing the `cobib.commands.review.ReviewCommand`.

    Arguments:
        `cobib.commands.review.ReviewCommand`: the command instance that just ran.

    Returns:
        Nothing.
    """

    PreSearchCommand = cast("Event", Callable[["commands.SearchCommand"], None])
    """
    Fires:
        Before starting the `cobib.commands.search.SearchCommand`.

    Arguments:
        `cobib.commands.search.SearchCommand`: the command instance that is about to run.

    Returns:
        Nothing. But the command attributes can be modified, affecting the execution.
    """
    PostSearchCommand = cast("Event", Callable[["commands.SearchCommand"], None])
    """
    Fires:
        Before finishing the `cobib.commands.search.SearchCommand`.

    Arguments:
        `cobib.commands.search.SearchCommand`: the command instance that just ran.

    Returns:
        Nothing. But the search results are still accessible before being rendered.
    """

    PreShowCommand = cast("Event", Callable[["commands.ShowCommand"], None])
    """
    Fires:
        Before starting the `cobib.commands.show.ShowCommand`.

    Arguments:
        `cobib.commands.show.ShowCommand`: the command instance that is about to run.

    Returns:
        Nothing. But the command attributes can be modified, affecting the execution.
    """
    PostShowCommand = cast("Event", Callable[["commands.ShowCommand"], None])
    """
    Fires:
        Before finishing the `cobib.commands.show.ShowCommand`.

    Arguments:
        `cobib.commands.show.ShowCommand`: the command instance that just ran.

    Returns:
        Nothing. But the string-represented entry is still accessible before being rendered.
    """

    PreUndoCommand = cast("Event", Callable[["commands.UndoCommand"], None])
    """
    Fires:
        Before starting the `cobib.commands.undo.UndoCommand`.

    Arguments:
        `cobib.commands.undo.UndoCommand`: the command instance that is about to run.

    Returns:
        Nothing. But the command attributes can be modified, affecting the execution.
    """
    PostUndoCommand = cast("Event", Callable[["commands.UndoCommand"], None])
    """
    Fires:
        Before finishing the `cobib.commands.undo.UndoCommand`.

    Arguments:
        `cobib.commands.undo.UndoCommand`: the command instance that just ran.

    Returns:
        Nothing.
    """

    PreZoteroImport = cast("Event", Callable[["importers.ZoteroImporter"], None])
    """
    Fires:
        Before starting `cobib.importers.zotero.ZoteroImporter.fetch`.

    Arguments:
        `cobib.importers.zotero.ZoteroImporter`: the importer instance that is about to run.

    Returns:
        Nothing. But the importer attributes can be modified, affecting the execution.
    """
    PostZoteroImport = cast("Event", Callable[["importers.ZoteroImporter"], None])
    """
    Fires:
        Before finishing `cobib.importers.zotero.ZoteroImporter.fetch`.

    Arguments:
        `cobib.importers.zotero.ZoteroImporter`: the importer instance that just ran.

    Returns:
        Nothing. But the importer attributes can be modified, affecting the execution.

    Note:
        - The entry labels will not have been mapped or disambiguated at this point.
    """

    PreBibtexParse = cast("Event", Callable[[str], Optional[str]])
    """
    Fires:
        Before starting `cobib.parsers.bibtex.BibtexParser.parse`.

    Arguments:
        `string`: the string to be parsed as BibTeX.

    Returns:
        Optionally a new (or updated) string to be parsed as BibTeX.

    Note:
        If a registered hook returns a new string, no subsequent hooks will be run!
    """
    PostBibtexParse = cast("Event", Callable[[Dict[str, "Entry"]], None])
    """
    Fires:
        Before finishing `cobib.parsers.bibtex.BibtexParser.parse`.

    Arguments:
        `bib`: a dictionary of new entries mapping from their labels to the actual data.

    Returns:
        Nothing. But the dictionary can be modified in-place such that the changes will be
        propagated to the database.
    """
    PreBibtexDump = cast("Event", Callable[["Entry"], None])
    """
    Fires:
        Before starting `cobib.parsers.bibtex.BibtexParser.dump`.

    Arguments:
        `entry`: the entry which is to be dumped in BibTeX format.

    Returns:
        Nothing. But the object can be modified in-place. Changes will **not** become persistent in
        the database.
    """
    PostBibtexDump = cast("Event", Callable[[str], Optional[str]])
    """
    Fires:
        Before finishing `cobib.parsers.bibtex.BibtexParser.dump`.

    Arguments:
        `string`: the string-representation of the `Entry` to be dumped as BibTeX.

    Returns:
        Optionally a new (or updated) string to be dumped.

    Note:
        If a registered hook returns a new string, no subsequent hooks will be run!
    """

    PreYAMLParse = cast("Event", Callable[[str], Optional[str]])
    """
    Fires:
        Before starting `cobib.parsers.yaml.YAMLParser.parse`.

    Arguments:
        `string`: the string to be parsed as YAML.

    Returns:
        Optionally a new (or updated) string to be parsed as YAML.

    Note:
        If a registered hook returns a new string, no subsequent hooks will be run!
    """
    PostYAMLParse = cast("Event", Callable[[Dict[str, "Entry"]], None])
    """
    Fires:
        Before finishing `cobib.parsers.yaml.YAMLParser.parse`.

    Arguments:
        `bib`: a dictionary of the new `Entry` instances stored under their `label` as keys.

    Returns:
        Nothing. But the dictionary can be modified in-place such that the changes will be
        propagated to the database.
    """
    PreYAMLDump = cast("Event", Callable[["Entry"], None])
    """
    Fires:
        Before starting `cobib.parsers.yaml.YAMLParser.dump`.

    Arguments:
        `entry`: the `Entry` object to be dumped in YAML format.

    Returns:
        Nothing. But the object can be modified in-place. Changes will **not** become persistent in
        the database.
    """
    PostYAMLDump = cast("Event", Callable[[str], Optional[str]])
    """
    Fires:
        Before finishing `cobib.parsers.yaml.YAMLParser.dump`.

    Arguments:
        `string`: the string-representation of the `Entry` to be dumped as YAML.

    Returns:
        Optionally a new (or updated) string to be dumped.

    Note:
        If a registered hook returns a new string, no subsequent hooks will be run!
    """

    PreArxivParse = cast("Event", Callable[[str], Optional[str]])
    """
    Fires:
        Before starting `cobib.parsers.arxiv.ArxivParser.parse`.

    Arguments:
        `string`: the string to be parsed as an arXiv ID.

    Returns:
        Optionally a new (or updated) string to be parsed as an arXiv ID.

    Note:
        If a registered hook returns a new string, no subsequent hooks will be run!
    """
    PostArxivParse = cast("Event", Callable[[Dict[str, "Entry"]], None])
    """
    Fires:
        Before finishing `cobib.parsers.arxiv.ArxivParser.parse`.

    Arguments:
        `bib`: a dictionary of the new `Entry` instances stored under their `label` as keys.

    Returns:
        Nothing. But the dictionary can be modified in-place such that the changes will be
        propagated to the database.
    """

    PreDOIParse = cast("Event", Callable[[str], Optional[str]])
    """
    Fires:
        Before starting `cobib.parsers.doi.DOIParser.parse`.

    Arguments:
        `string`: the string to be parsed as a DOI.

    Returns:
        Optionally a new (or updated) string to be parsed as a DOI.

    Note:
        If a registered hook returns a new string, no subsequent hooks will be run!
    """
    PostDOIParse = cast("Event", Callable[[Dict[str, "Entry"]], None])
    """
    Fires:
        Before finishing `cobib.parsers.doi.DOIParser.parse`.

    Arguments:
        `bib`: a dictionary of the new `Entry` instances stored under their `label` as keys.

    Returns:
        Nothing. But the dictionary can be modified in-place such that the changes will be
        propagated to the database.
    """

    PreISBNParse = cast("Event", Callable[[str], Optional[str]])
    """
    Fires:
        Before starting `cobib.parsers.isbn.ISBNParser.parse`.

    Arguments:
        `string`: the string to be parsed as an ISBN.

    Returns:
        Optionally a new (or updated) string to be parsed as an ISBN.

    Note:
        If a registered hook returns a new string, no subsequent hooks will be run!
    """
    PostISBNParse = cast("Event", Callable[[Dict[str, "Entry"]], None])
    """
    Fires:
        Before finishing `cobib.parsers.isbn.ISBNParser.parse`.

    Arguments:
        `bib`: a dictionary of the new `Entry` instances stored under their `label` as keys.

    Returns:
        Nothing. But the dictionary can be modified in-place such that the changes will be
        propagated to the database.
    """

    PreURLParse = cast("Event", Callable[[str], Optional[str]])
    """
    Fires:
        Before starting `cobib.parsers.url.URLParser.parse`.

    Arguments:
        `string`: the string to be parsed as a URL.

    Returns:
        Optionally a new (or updated) string to be parsed as a URL.

    Note:
        If a registered hook returns a new string, no subsequent hooks will be run!
    """
    PostURLParse = cast("Event", Callable[[Dict[str, "Entry"]], None])
    """
    Fires:
        Before finishing `cobib.parsers.url.URLParser.parse`.

    Arguments:
        `bib`: a dictionary of the new `Entry` instances stored under their `label` as keys.

    Returns:
        Nothing. But the dictionary can be modified in-place such that the changes will be
        propagated to the database.
    """

    PreFileDownload = cast(
        "Event",
        Callable[
            [str, str, Optional[str], Optional[Dict[str, str]]],
            Optional[Tuple[str, str, Optional[str], Optional[Dict[str, str]]]],
        ],
    )
    """
    Fires:
        Before starting `cobib.utils.file_downloader.FileDownloader.download`.

    Arguments:
        `url`: the URL from which to download a file.
        `label`: the label of the `Entry` to which the file belongs.
        `folder`: an optional folder where the file will be stored.
        `headers`: an optional headers dictionary for the download `GET` request.

    Returns:
        This can optionally return a tuple overwriting all of the provided input arguments.

    Note:
        If a registered hook returns a new tuple of arguments, no subsequent hooks will be run!
    """
    PostFileDownload = cast("Event", Callable[[RelPath], Optional[RelPath]])
    """
    Fires:
        Before finishing `cobib.utils.file_downloader.FileDownloader.download` if and only if the
        download was successful.

    Arguments:
        `path`: the `RelPath` to the freshly downloaded file.

    Returns:
        An optional new `RelPath`.

    Note:
        If a registered hook returns a new path, no subsequent hooks will be run!
    """

    PreGitCommit = cast("Event", Callable[[str, Optional[Dict[str, Any]]], Optional[str]])
    """
    Fires:
        Before starting `cobib.commands.base_command.Command.git` (i.e. whenever an automatic
        git-commit occurs).

    Arguments:
        `msg`: the commit message.
        `args`: an optional dictionary of keyword arguments provided to the command that triggered
                this commit.

    Returns:
        Optionally a new commit message.

    Note:
        If a registered hook returns a new commit message, no subsequent hooks will be run!
    """
    PostGitCommit = cast("Event", Callable[[Path, Path], None])
    """
    Fires:
        Before finishing `cobib.commands.base_command.Command.git` (i.e. whenever an automatic
        git-commit occurs).

    Arguments:
        `root`: the `Path` to the root git directory where the database file resides.
        `file`: the `Path` to the database file.

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
                        result.append(exp is type(None))
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
