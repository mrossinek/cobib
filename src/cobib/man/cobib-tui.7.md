cobib-tui(7) -- coBib's text-based (or terminal) user interface
===============================================================

## SYNOPSIS

`cobib`

## DESCRIPTION

When executing `cobib` without specifying one of its subcommands (see *cobib-commands(7)*) its TUI gets started.
It provides an interactive session in which the database can be explored and manipulated using all of coBib's features.
The TUI is built using [textual](https://textual.textualize.io/).

It has multiple panels:

  * The main panel takes up 2/3 of the screen.
    It either views a list of entries (see *cobib-list(1)*) or search results (see *cobib-search(1)*).
  * A static view of the entry that is currently under the cursor.
  * An editable view of the entry's note.

Most subcommands of coBib are directly executable via a keybinding.
If a command requires additional arguments, a prompt will open to query them.
Any such prompt will behave identically to the standard command-line interface (or CLI).
It is even possible to use the `--help` argument for a small popup to provide additional information on that command.

### Keybindings

Below all keybindings are listed in alphabetical order:

  * `a`:
    Triggers the *cobib-add(1)* command.
  * `c`:
    Triggers the *cobib-review(1)* command (mnemonic: _check_).
  * `d`:
    Triggers the *cobib-delete(1)* command for the current (selection) of entries.
  * `e`:
    Triggers the *cobib-edit(1)* command.
  * `f`:
    Triggers the *cobib-list(1)* command to _filter_ the viewed list of entries.
  * `i`:
    Triggers the *cobib-import(1)* command.
  * `m`:
    Triggers the *cobib-modify(1)* command.
  * `n`:
    Triggers the *cobib-note(1)* command for the current entry.
  * `o`:
    Triggers the *cobib-open(1)* command for the current (selection) of entries.
  * `p`:
    Prompts which [preset view][Preset filters] to open.
  * `q`:
    Quits the TUI.
  * `r`:
    Triggers the *cobib-redo(1)* command.
  * `s`:
    Triggers the *cobib-list(1)* command to _sort_ the viewed list of entries.
  * `u`:
    Triggers the *cobib-undo(1)* command.
  * `v`:
    Adds the current entry to the visual selection.
  * `x`:
    Triggers the *cobib-export(1)* command of the current (selection) of entries.
  * `z`:
    Toggles a panel to view the _log_ messages.
  * [0-9]:
    Selects the corresponding [preset view][preset filters].
  * `?`:
    Toggles the help screen.
  * `!`:
    Triggers the *cobib-man(1)* command (mnemonic: more help than `?`).
    When pressed for the first time, this brings up the man-page index to select a man-page from.
    Otherwise, the last viewed man-page will still be in the buffer.
    Use `:man ...` to open a specific man-page directly rather than the index.
  * `_`:
    Toggles between the horizontal and vertical layouts.
  * `:`:
    Opens a prompt for any CLI command.
  * `/`:
    Triggers the *cobib-search(1)* command.
  * `enter`:
    Updates the view of the current entry and loads the contents of its note (if one exists).
  * `Ctrl+p`:
    Opens textual's command palette.


If the main panel is showing the results of a *cobib-search(1)*, the following keybindings exist:

  * `space`:
    Toggles the expanded/collapsed state of the current item.
  * `backspace`:
    Toggles the expanded/collapsed state of the current item, _recursively_ (i.e. affecting all its children, too).


When editing a note, the following keybindings exist:

  * `Escape`:
    Unfocuses the text area.
  * `Ctrl+r`:
    Resets the unsaved changes.
  * `Ctrl+s`:
    Saves the text area contents.
  * `Ctrl+x`:
    Opens the text area content in an external editor.


When viewing a man-page, the following keybindings exist:

  * `q`:
    To quit the man-page view.
  * `t`:
    To open the table of contents of the current man-page.
  * `i`:
    To select a new man-page to view from the man-page index (this is what opens when pressing `!` for the first time).
  * `Enter`:
    To open the selected man-page from the index view.
  * `Escape`:
    To cancel selecting a new man-page from the index view.
  * `mouse`:
    You can left-click on other man-page references to open them.


Finally, vim-like key bindings exist for navigation:

  * `h` | `left arrow`:
    Moves left (if possible).
  * `j` | `down arrow`:
    Moves down (if possible).
  * `k` | `up arrow`:
    Moves up (if possible).
  * `l` | `right arrow`:
    Moves right (if possible).
  * `PageUp`:
    Moves one page up.
  * `PageDown`:
    Moves one page down.
  * `Home`:
    Moves to the top.
  * `End`:
    Moves to the bottom.

### Preset filters

The `config.tui.preset_filters` setting can be used to determine preset views that can be reached quickly.
For example, the following setting:
```python

config.tui.preset_filters = [
    "++tags new",   # filters entries with the `new` tag
    "++year 2023",  # filters entries from the year 2023
]
```
will change the main panel contents to list the results of the first entry when hitting `1` and the second when hitting `2`.
The normal (unfiltered) entries are always reachable via the preset `0`.
If the `config.tui.preset_filters` has more than 9 entries, those presets can still be reached via the popup triggered by the `p` keybinding.

## SEE ALSO

*cobib(1)*

[//]: # ( vim: set ft=markdown tw=0: )
