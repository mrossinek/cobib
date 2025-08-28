cobib-event(7) -- the event hook specification for cobib(1)
===========================================================

## SYNOPSIS

```python
from pathlib import Path
from os import system
from cobib.config import Event

@Event.PostGitCommit.subscribe
def push_to_remote(root: Path, file: Path) -> None:
    system(f"git -C {root} push")
```

## DESCRIPTION

_cobib(1)_ provides various **events** on to which _hooks_ can be registered for execution.
The [SYNOPSIS][] section above shows one such example that can be programmed inside of the _cobib-config(5)_.
In that example, the function `push_to_remote` will be executed every time the `PostGitCommit` event triggers.

When writing event hooks, it is important that you include the full signature type hints, because these are used to validate all registered event hooks.
In the [OPTIONS][] section below, all available events are listed out with their respective hook signature.
The signatures are formatted as Python `Callable` objects which look like so: `Callable[[list, of, argument, types], return type]`.

## OPTIONS

This section lists all available events, separated into topical subsections.

### COMMANDS

Most of the commands provide a **Pre-** and **Post-** execution event which gets triggered before and after the actual command execution, respectively.
All of these events are provided with the Python command object instance, allowing the hooks to modify runtime data of the command.

  * _PreAddCommand_ = `Callable[[cobib.commands.add.AddCommand], None]`:
    Fires:<br>
        Before starting the _cobib-add(1)_ command.

    Arguments:<br>
        - `cobib.commands.add.AddCommand`: the command instance that is about to run.

    Returns:<br>
        Nothing. But the command attributes can be modified, affecting the execution.

  * _PostAddCommand_ = `Callable[[cobib.commands.add.AddCommand], None]`:
    Fires:<br>
        Before finishing the _cobib-add(1)_ command.

    Arguments:<br>
        - `cobib.commands.add.AddCommand`: the command instance that just ran.

    Returns:<br>
        Nothing. But the command attributes can be modified, affecting the execution.

    Note:<br>
        This event fires **before** starting the `cobib.commands.edit.EditCommand` which starts if
        manual entry addition is requested.

  * _PreDeleteCommand_ = `Callable[[cobib.commands.delete.DeleteCommand], None]`:
    Fires:<br>
        Before starting the _cobib-delete(1)_ command.

    Arguments:<br>
        - `cobib.commands.delete.DeleteCommand`: the command instance that is about to run.

    Returns:<br>
        Nothing. But the command attributes can be modified, affecting the execution.

  * _PostDeleteCommand_ = `Callable[[cobib.commands.delete.DeleteCommand], None]`:
    Fires:<br>
        Before finishing the _cobib-delete(1)_ command.

    Arguments:<br>
        - `cobib.commands.delete.DeleteCommand`: the command instance that just ran.

    Returns:<br>
        Nothing. While the deleted entry labels are accessible, modifying them has no effect.

  * _PreEditCommand_ = `Callable[[cobib.commands.edit.EditCommand], None]`:
    Fires:<br>
        Before starting the _cobib-edit(1)_ command.

    Arguments:<br>
        - `cobib.commands.edit.EditCommand`: the command instance that is about to run.

    Returns:<br>
        Nothing. But the command attributes can be modified, affecting the execution.

  * _PostEditCommand_ = `Callable[[cobib.commands.edit.EditCommand], None]`:
    Fires:<br>
        Before finishing the _cobib-edit(1)_ command.

    Arguments:<br>
        - `cobib.commands.edit.EditCommand`: the command instance that just ran.

    Returns:<br>
        Nothing. While the edited entry is accessible, modifying it has no effect.

  * _PreExportCommand_ = `Callable[[cobib.commands.export.ExportCommand], None]`:
    Fires:<br>
        Before starting the _cobib-export(1)_ command.

    Arguments:<br>
        - `cobib.commands.export.ExportCommand`: the command instance that is about to run.

    Returns:<br>
        Nothing. But the command attributes can be modified, affecting the execution.

  * _PostExportCommand_ = `Callable[[cobib.commands.export.ExportCommand], None]`:
    Fires:<br>
        Before finishing the _cobib-export(1)_ command.

    Arguments:<br>
        - `cobib.commands.export.ExportCommand`: the command instance that just ran.

    Returns:<br>
        Nothing. The files to which has been exported are still accessible and open.

  * _PreGitCommand_ = `Callable[[cobib.commands.git.GitCommand], None]`:
    Fires:<br>
        Before starting the _cobib-git(1)_ command.

    Arguments:<br>
        - `cobib.commands.git.GitCommand`: the command instance that is about to run.

    Returns:<br>
        Nothing. But the command attributes can be modified, affecting the execution.

  * _PostGitCommand_ = `Callable[[cobib.commands.git.GitCommand], None]`:
    Fires:<br>
        Before finishing the _cobib-git(1)_ command.

    Arguments:<br>
        - `cobib.commands.git.GitCommand`: the command instance that just ran.

    Returns:<br>
        Nothing.

  * _PreImportCommand_ = `Callable[[cobib.commands.import_.ImportCommand], None]`:
    Fires:<br>
        Before starting the _cobib-import(1)_ command.

    Arguments:<br>
        - `cobib.commands.import_.ImportCommand`: the command instance that is about to run.

    Returns:<br>
        Nothing. But the command attributes can be modified, affecting the execution.

  * _PostImportCommand_ = `Callable[[cobib.commands.import_.ImportCommand], None]`:
    Fires:<br>
        Before finishing the _cobib-import(1)_ command.

    Arguments:<br>
        - `cobib.commands.import_.ImportCommand`: the command instance that just ran.

    Returns:<br>
        Nothing. But the dictionary of new entries can be modified before the changes are made
        persistent in the database.

  * _PreInitCommand_ = `Callable[[cobib.commands.init.InitCommand], None]`:
    Fires:<br>
        Before starting the _cobib-init(1)_ command.

    Arguments:<br>
        - `cobib.commands.init.InitCommand`: the command instance that is about to run.

    Returns:<br>
        Nothing. But the command attributes can be modified, affecting the execution.

  * _PostInitCommand_ = `Callable[[cobib.commands.init.InitCommand], None]`:
    Fires:<br>
        Before finishing the _cobib-init(1)_ command.

    Arguments:<br>
        - `cobib.commands.init.InitCommand`: the command instance that just ran.

    Returns:<br>
        Nothing.

  * _PreListCommand_ = `Callable[[cobib.commands.list_.ListCommand], None]`:
    Fires:<br>
        Before starting the _cobib-list(1)_ command.

    Arguments:<br>
        - `cobib.commands.list_.ListCommand`: the command instance that is about to run.

    Returns:<br>
        Nothing. But the command attributes can be modified, affecting the execution.

  * _PostListCommand_ = `Callable[[cobib.commands.list_.ListCommand], None]`:
    Fires:<br>
        Before finishing the _cobib-list(1)_ command.

    Arguments:<br>
        - `cobib.commands.list_.ListCommand`: the command instance that just ran.

    Returns:<br>
        Nothing. But the to-be-listed entries are still accessible before being rendered.

  * _PreModifyCommand_ = `Callable[[cobib.commands.modify.ModifyCommand], None]`:
    Fires:<br>
        Before starting the _cobib-modify(1)_ command.

    Arguments:<br>
        - `cobib.commands.modify.ModifyCommand`: the command instance that is about to run.

    Returns:<br>
        Nothing. But the command attributes can be modified, affecting the execution.

  * _PostModifyCommand_ = `Callable[[cobib.commands.modify.ModifyCommand], None]`:
    Fires:<br>
        Before finishing the _cobib-modify(1)_ command.

    Arguments:<br>
        - `cobib.commands.modify.ModifyCommand`: the command instance that just ran.

    Returns:<br>
        Nothing. But the modified entries are still accessible before written to the database.

  * _PreNoteCommand_ = `Callable[[cobib.commands.note.NoteCommand], None]`:
    Fires:<br>
        Before starting the _cobib-note(1)_ command.

    Arguments:<br>
        - `cobib.commands.note.NoteCommand`: the command instance that is about to run.

    Returns:<br>
        Nothing. But the command attributes can be modified, affecting the execution.

  * _PostNoteCommand_ = `Callable[[cobib.commands.note.NoteCommand], None]`:
    Fires:<br>
        Before finishing the _cobib-note(1)_ command.

    Arguments:<br>
        - `cobib.commands.note.NoteCommand`: the command instance that just ran.

    Returns:<br>
        Nothing. While the entry whose note was edited is accessible, modifying it has no effect.

  * _PreOpenCommand_ = `Callable[[cobib.commands.open.OpenCommand], None]`:
    Fires:<br>
        Before starting the _cobib-open(1)_ command.

    Arguments:<br>
        - `cobib.commands.open.OpenCommand`: the command instance that is about to run.

    Returns:<br>
        Nothing. But the command attributes can be modified, affecting the execution.

  * _PostOpenCommand_ = `Callable[[cobib.commands.open.OpenCommand], None]`:
    Fires:<br>
        Before finishing the _cobib-open(1)_ command.

    Arguments:<br>
        - `cobib.commands.open.OpenCommand`: the command instance that just ran.

    Returns:<br>
        Nothing.

  * _PreRedoCommand_ = `Callable[[cobib.commands.redo.RedoCommand], None]`:
    Fires:<br>
        Before starting the _cobib-redo(1)_ command.

    Arguments:<br>
        - `cobib.commands.redo.RedoCommand`: the command instance that is about to run.

    Returns:<br>
        Nothing. But the command attributes can be modified, affecting the execution.

  * _PostRedoCommand_ = `Callable[[cobib.commands.redo.RedoCommand], None]`:
    Fires:<br>
        Before finishing the _cobib-redo(1)_ command.

    Arguments:<br>
        - `cobib.commands.redo.RedoCommand`: the command instance that just ran.

    Returns:<br>
        Nothing.

  * _PreReviewCommand_ = `Callable[[cobib.commands.review.ReviewCommand], None]`:
    Fires:<br>
        Before starting the _cobib-review(1)_ command.
        The only logic which is done prior to this event is the retrieval of the command arguments from a previous review process when the `--resume` option has been specified.

    Arguments:<br>
        - `cobib.commands.review.ReviewCommand`: the command instance that is about to run.

    Returns:<br>
        Nothing. But the command attributes can be modified, affecting the execution.

  * _PostReviewCommand_ = `Callable[[cobib.commands.review.ReviewCommand], None]`:
    Fires:<br>
        Before finishing the _cobib-review(1)_ command.

    Arguments:<br>
        - `cobib.commands.review.ReviewCommand`: the command instance that just ran.

    Returns:<br>
        Nothing.

  * _PreSearchCommand_ = `Callable[[cobib.commands.search.SearchCommand], None]`:
    Fires:<br>
        Before starting the _cobib-search(1)_ command.

    Arguments:<br>
        - `cobib.commands.search.SearchCommand`: the command instance that is about to run.

    Returns:<br>
        Nothing. But the command attributes can be modified, affecting the execution.

  * _PostSearchCommand_ = `Callable[[cobib.commands.search.SearchCommand], None]`:
    Fires:<br>
        Before finishing the _cobib-search(1)_ command.

    Arguments:<br>
        - `cobib.commands.search.SearchCommand`: the command instance that just ran.

    Returns:<br>
        Nothing. But the search results are still accessible before being rendered.

  * _PreShowCommand_ = `Callable[[cobib.commands.show.ShowCommand], None]`:
    Fires:<br>
        Before starting the _cobib-show(1)_ command.

    Arguments:<br>
        - `cobib.commands.show.ShowCommand`: the command instance that is about to run.

    Returns:<br>
        Nothing. But the command attributes can be modified, affecting the execution.

  * _PostShowCommand_ = `Callable[[cobib.commands.show.ShowCommand], None]`:
    Fires:<br>
        Before finishing the _cobib-show(1)_ command.

    Arguments:<br>
        - `cobib.commands.show.ShowCommand`: the command instance that just ran.

    Returns:<br>
        Nothing. But the string-represented entry is still accessible before being rendered.

  * _PreUndoCommand_ = `Callable[[cobib.commands.undo.UndoCommand], None]`:
    Fires:<br>
        Before starting the _cobib-undo(1)_ command.

    Arguments:<br>
        - `cobib.commands.undo.UndoCommand`: the command instance that is about to run.

    Returns:<br>
        Nothing. But the command attributes can be modified, affecting the execution.

  * _PostUndoCommand_ = `Callable[[cobib.commands.undo.UndoCommand], None]`:
    Fires:<br>
        Before finishing the _cobib-undo(1)_ command.

    Arguments:<br>
        - `cobib.commands.undo.UndoCommand`: the command instance that just ran.

    Returns:<br>
        Nothing.


### IMPORTERS

Most of the _cobib-importers(7)_ implementatons provide a **Pre-** and **Post-** execution event which gets triggererd before and after the actual import, respectively.
All of these events are provided with the Python importer object instance, allowing the hooks to modify runtime data of the importer.

  * _PreZoteroImport_ = `Callable[[cobib.importers.zotero.ZoteroImporter], None]`:
    Fires:<br>
        Before starting to fetch data using _cobib-zotero(7)_.

    Arguments:<br>
        - `cobib.importers.zotero.ZoteroImporter`: the importer instance that is about to run.

    Returns:<br>
        Nothing. But the importer attributes can be modified, affecting the execution.

  * _PostZoteroImport_ = `Callable[[cobib.importers.zotero.ZoteroImporter], None]`:
    Fires:<br>
        Before finishing to fetch data using _cobib-zotero(7)_.

    Arguments:<br>
        - `cobib.importers.zotero.ZoteroImporter`: the importer instance that just ran.

    Returns:<br>
        Nothing. But the importer attributes can be modified, affecting the execution.

    Note:<br>
        The entry labels will not have been mapped or disambiguated at this point.

### PARSERS

Most of the _cobib-parsers(7)_ implementations provide **Pre-** and **Post-** events for the **-Parse** and **-Dump** actions.
The arguments and return types of these events vary as detailed below.

  * _PreBibtexParse_ = `Callable[[str], Optional[str]]`:
    Fires:<br>
        Before starting to parse data using _cobib-bibtex(7)_.

    Arguments:<br>
        - `string`: the string to be parsed as BibTeX.

    Returns:<br>
        Optionally a new (or updated) string to be parsed as BibTeX.

    Note:<br>
        If a registered hook returns a new string, no subsequent hooks will be run!

  * _PostBibtexParse_ = `Callable[[Dict[str, cobib.database.entry.Entry], None]`:
    Fires:<br>
        Before finishing to parse data using _cobib-bibtex(7)_.

    Arguments:<br>
        - `bib`: a dictionary of new entries mapping from their labels to the actual data.

    Returns:<br>
        Nothing. But the dictionary can be modified in-place such that the changes will be propagated to the database.

  * _PreBibtexDump_ = `Callable[[cobib.database.entry.Entry], None]`:
    Fires:<br>
        Before starting to dump data using _cobib-bibtex(7)_.

    Arguments:<br>
        - `entry`: the entry which is to be dumped in BibTeX format.

    Returns:<br>
        Nothing. But the object can be modified in-place. Changes will **not** become persistent in the database.

  * _PostBibtexDump_ = `Callable[[str], Optional[str]]`:
    Fires:<br>
        Before finishing to dump data using _cobib-bibtex(7)_.

    Arguments:<br>
        - `str`: the string-representation of the dumped entry in BibTeX format.

    Returns:<br>
        Optionally a new (or updated) string to be dumped.

    Note:<br>
        If a registered hook returns a new string, no subsequent hooks will be run!

  * _PreYAMLParse_ = `Callable[[str], Optional[str]]`:
    Fires:<br>
        Before starting to parse data using _cobib-yaml(7)_.

    Arguments:<br>
        - `string`: the string to be parsed as YAML.

    Returns:<br>
        Optionally a new (or updated) string to be parsed as YAML.

    Note:<br>
        If a registered hook returns a new string, no subsequent hooks will be run!

  * _PostYAMLParse_ = `Callable[[Dict[str, cobib.database.entry.Entry], None]`:
    Fires:<br>
        Before finishing to parse data using _cobib-yaml(7)_.

    Arguments:<br>
        - `bib`: a dictionary of new entries mapping from their labels to the actual data.

    Returns:<br>
        Nothing. But the dictionary can be modified in-place such that the changes will be propagated to the database.

  * _PreYAMLDump_ = `Callable[[cobib.database.entry.Entry], None]`:
    Fires:<br>
        Before starting to dump data using _cobib-yaml(7)_.

    Arguments:<br>
        - `entry`: the entry which is to be dumped in YAML format.

    Returns:<br>
        Nothing. But the object can be modified in-place. Changes will **not** become persistent in the database.

  * _PostYAMLDump_ = `Callable[[str], Optional[str]]`:
    Fires:<br>
        Before finishing to dump data using _cobib-yaml(7)_.

    Arguments:<br>
        - `str`: the string-representation of the dumped entry in YAML format.

    Returns:<br>
        Optionally a new (or updated) string to be dumped.

    Note:<br>
        If a registered hook returns a new string, no subsequent hooks will be run!

  * _PreArxivParse_ = `Callable[[str], Optional[str]]`:
    Fires:<br>
        Before starting to parse data using _cobib-arxiv(7)_.

    Arguments:<br>
        - `string`: the string to be parsed as an arXiv ID.

    Returns:<br>
        Optionally a new (or updated) string to be parsed as an arXiv ID.

    Note:<br>
        If a registered hook returns a new string, no subsequent hooks will be run!

  * _PostArxivParse_ = `Callable[[Dict[str, cobib.database.entry.Entry], None]`:
    Fires:<br>
        Before finishing to parse data using _cobib-arxiv(7)_.

    Arguments:<br>
        - `bib`: a dictionary of new entries mapping from their labels to the actual data.

    Returns:<br>
        Nothing. But the dictionary can be modified in-place such that the changes will be propagated to the database.

  * _PreDOIParse_ = `Callable[[str], Optional[str]]`:
    Fires:<br>
        Before starting to parse data using _cobib-doi(7)_.

    Arguments:<br>
        - `string`: the string to be parsed as a DOI.

    Returns:<br>
        Optionally a new (or updated) string to be parsed as a DOI.

    Note:<br>
        If a registered hook returns a new string, no subsequent hooks will be run!

  * _PostDOIParse_ = `Callable[[Dict[str, cobib.database.entry.Entry], None]`:
    Fires:<br>
        Before finishing to parse data using _cobib-doi(7)_.

    Arguments:<br>
        - `bib`: a dictionary of new entries mapping from their labels to the actual data.

    Returns:<br>
        Nothing. But the dictionary can be modified in-place such that the changes will be propagated to the database.

  * _PreISBNParse_ = `Callable[[str], Optional[str]]`:
    Fires:<br>
        Before starting to parse data using _cobib-isbn(7)_.

    Arguments:<br>
        - `string`: the string to be parsed as an ISBN.

    Returns:<br>
        Optionally a new (or updated) string to be parsed as an ISBN.

    Note:<br>
        If a registered hook returns a new string, no subsequent hooks will be run!

  * _PostISBNParse_ = `Callable[[Dict[str, cobib.database.entry.Entry], None]`:
    Fires:<br>
        Before finishing to parse data using _cobib-isbn(7)_.

    Arguments:<br>
        - `bib`: a dictionary of new entries mapping from their labels to the actual data.

    Returns:<br>
        Nothing. But the dictionary can be modified in-place such that the changes will be propagated to the database.

  * _PreURLParse_ = `Callable[[str], Optional[str]]`:
    Fires:<br>
        Before starting to parse data using _cobib-url(7)_.

    Arguments:<br>
        - `string`: the string to be parsed as a URL.

    Returns:<br>
        Optionally a new (or updated) string to be parsed as a URL.

    Note:<br>
        If a registered hook returns a new string, no subsequent hooks will be run!

  * _PostURLParse_ = `Callable[[Dict[str, cobib.database.entry.Entry], None]`:
    Fires:<br>
        Before finishing to parse data using _cobib-url(7)_.

    Arguments:<br>
        - `bib`: a dictionary of new entries mapping from their labels to the actual data.

    Returns:<br>
        Nothing. But the dictionary can be modified in-place such that the changes will be propagated to the database.

### UTILS

  * _PreFileDownload_ = `Callable[[str, str, Optional[str], Optional[Dict[str, str]]], Optional[Tuple[str, str, Optional[str], Optional[Dict[str, str]]]]]`:
    Fires:<br>
        Before starting to download associated files.

    Arguments:<br>
        - `url`: the URL from which to download a file.<br>
        - `label`: the label of the entry to which the file belongs.<br>
        - `folder`: an optional folder where the file will be stored.<br>
        - `headers`: an optional headers dictionary for the download `GET` request.

    Returns:<br>
        This can optionally return a tuple overwriting all of the provided input arguments.

    Note:<br>
        If a registered hook returns a new tuple of arguments, no subsequent hooks will be run!

  * _PostFileDownload_ = `Callable[[cobib.utils.rel_path.RelPath], Optional[cobib.utils.rel_path.RelPath]]`:
    Fires:<br>
        Before finishing to download associated files if and only if the download was successful.

    Arguments:<br>
        - `path`: the path to the freshly downloaded file.

    Returns:<br>
        An optional new path.

    Note:<br>
        If a registered hook returns a new path, no subsequent hooks will be run!

  * _PreGitCommit_ = `Callable[[str, Optional[Dict[str, Any]]], Optional[str]]`:
    Fires:<br>
        Before starting an automatic git commit (see also _cobib-git(7)_).

    Arguments:<br>
        - `msg`: the commit message.<br>
        - `args`: an optional dictionary of keyword arguments provided to the command that triggered this commit.

    Returns:<br>
        Optionally, a new commit message.

    Note:<br>
        If a registered hook returns a new commit message, no subsequent hooks will be run!

  * _PostGitCommit_ = `Callable[[pathlib.Path, pathlib.Path], None]`:
    Fires:<br>
        Before finishing an automatic git commit (see also _cobib-git(7)_).

    Arguments:<br>
        - `root`: the path to the root git directory where the database file resides.<br>
        - `file`: the path to the database file.

    Returns:<br>
        Nothing.


## EXAMPLES

Some useful event hooks can be found in the [wiki](https://gitlab.com/cobib/cobib/-/wikis/Useful-Event-Hooks).

## SEE ALSO

_cobib(1)_, _cobib-config(5)_

[//]: # ( vim: set ft=markdown tw=0: )
