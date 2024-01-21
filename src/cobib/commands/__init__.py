"""coBib's commands.

coBib provides a series of commands, all of which are available both, from the command-line as well
as through the text user interface (see also `cobib.ui.tui`).
The abstract interface which should be implemented is defined by the `cobib.commands.base_command`.
"""

from .add import AddCommand as AddCommand
from .delete import DeleteCommand as DeleteCommand
from .edit import EditCommand as EditCommand
from .export import ExportCommand as ExportCommand
from .git import GitCommand as GitCommand
from .import_ import ImportCommand as ImportCommand
from .init import InitCommand as InitCommand
from .list_ import ListCommand as ListCommand
from .modify import ModifyCommand as ModifyCommand
from .open import OpenCommand as OpenCommand
from .redo import RedoCommand as RedoCommand
from .review import ReviewCommand as ReviewCommand
from .search import SearchCommand as SearchCommand
from .show import ShowCommand as ShowCommand
from .undo import UndoCommand as UndoCommand
