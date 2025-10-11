[![coBib](https://gitlab.com/cobib/cobib/-/raw/master/docs/logo/cobib_logo.svg)](https://cobib.gitlab.io/cobib/cobib.html)

# coBib

[![pipeline](https://gitlab.com/cobib/cobib/badges/master/pipeline.svg)](https://gitlab.com/cobib/cobib/-/pipelines)
[![coverage](https://gitlab.com/cobib/cobib/badges/master/coverage.svg)](https://gitlab.com/cobib/cobib/-/graphs/master/charts)
[![Release](https://img.shields.io/gitlab/v/release/cobib/cobib?label=Release&logo=gitlab)](https://gitlab.com/cobib/cobib/-/releases/)
[![AUR](https://img.shields.io/aur/version/cobib?label=AUR&logo=archlinux)](https://aur.archlinux.org/packages/cobib)
[![PyPI](https://img.shields.io/pypi/v/cobib?label=PyPI&logo=pypi)](https://pypi.org/project/cobib/)
[![Python](https://img.shields.io/python/required-version-toml?tomlFilePath=https://gitlab.com/cobib/cobib/-/raw/master/pyproject.toml?ref_type=heads?label=Python&label=Python&logo=python)](https://gitlab.com/cobib/cobib/-/blob/master/pyproject.toml)
[![License](https://img.shields.io/gitlab/license/cobib/cobib?label=License)](https://gitlab.com/cobib/cobib/-/blob/master/LICENSE.txt)

coBib is a simple, console-based bibliography management tool.
It is the result of the need for an easy-to-use alternative to full-blown reference managers like Mendeley or Zotero.
As such it follows some basic design goals:

* **plain-text database**: which means you get full access and control over the database.
* **git-integration**: as a benefit of the above, you can keep track of your database through version control.
* **centralized database, location-independent library**: this means, that coBib *only* manages the
  database file in a centralized fashion but allows you to spread the actual contents of your
  library across the entire file system (this is the major different to
  [papis](https://papis.readthedocs.io/en/latest/library_structure.html)).
* **command-line and TUI support**: all features are available through the command-line as well as a
  [textual](https://textual.textualize.io/)-based TUI

Here is an example screenshot of the TUI when listing the entries in your database:

![coBib TUI List](https://gitlab.com/cobib/cobib/-/raw/master/docs/screenshots/cobib_tui_list.svg)

And here is an example screenshot for listing search results:

![coBib TUI Search](https://gitlab.com/cobib/cobib/-/raw/master/docs/screenshots/cobib_tui_search.svg)


## Installation

For all common purposes you can install coBib via `pip`:

```
pip install cobib
```

If you would also like to install the man-page, you need to download the source
code and do the following:

```
git clone https://gitlab.com/cobib/cobib
cd cobib
make install_man_pages
```

### Arch Linux

coBib is packaged in the AUR.
* [cobib](https://aur.archlinux.org/packages/cobib/)
* [cobib-git](https://aur.archlinux.org/packages/cobib-git/)

### Windows

coBib _might_ work on Windows as is, but it is not being tested so no guarantees are given.
If you are using Windows 10 or later and are running into issues, you should be able to install and
use coBib's full functionality within the Linux subsystem.


## Getting Started

To get started with coBib, you check out:
- the `cobib-getting-started.7` man-page:
  ```bash
  cobib man getting-started
  ```
- the interactive tutorial:
  ```bash
  cobib tutorial
  ```


## Configuration

You can overwrite the default configuration by placing a `config.py` file in `~/.config/cobib/`.
The easiest way to get started with this file is by copying [`example.py`](https://gitlab.com/cobib/cobib/-/blob/master/src/cobib/config/example.py)
or by using:

```
cobib _example_config > ~/.config/cobib/config.py
```

You can then modify it to your liking.

You may also specify a different config file at runtime by using the `-c` or `--config` command line argument or by specifying a custom path in the `COBIB_CONFIG` environment variable.
You can also disable loading of _any_ configuration file by setting this environment variable to one of the following values: `"", 0, "f", "false", "nil", "none"`.

Finally, be sure to take a look at the man page (`man 5 cobib-config`) and/or the online documentation for more information.


## Plugins

coBib supports the implementation of plugins!
You can find an example plugin in [this folder](./plugin) or read the docs of
`cobib_dummy` (when viewing the hosted documentation online).

Below is a list of known plugins. If you wrote your own, feel free to add it here!
- [`cobib-zotero`](https://gitlab.com/cobib/cobib-zotero): an importer backend for [Zotero](https://github.com/zotero/zotero)


## Documentation

coBib's documentation is hosted [here](https://cobib.gitlab.io/cobib/cobib.html).
That page also contains a **getting started** guide!

If you would like to generate a local version during development, you need to clone the source code, and install [`pdoc`](https://github.com/mitmproxy/pdoc) in order to generate it:

```
git clone https://gitlab.com/cobib/cobib.git
cd cobib
pip install pdoc
pdoc -d google -e cobib=https://gitlab.com/cobib/cobib/-/blob/master/src/cobib/ -t docs/jinja -o build/html src/cobib plugin/src/cobib_dummy tests
```

You can then browse the documentation from `build/html/cobib.html`.


## History

I have started this project when I was looking into alternatives to popular reference managers such as Mendeley,
which has more features than I use on a regular basis and does not allow me to work from the command line which is where I spend most of the time that I spend on the computer.

Hence, I have decided to make it my own task of implementing a simple, yet fast, reference manager.
coBib is written in Python and uses a YAML file to store its bibliography in a plain text format.

### Alternatives

Besides coBib there are many other tools for managing your bibliography.
Below is a selection (alphabetical) of open source tools that I am aware of:

- [bibiman](https://codeberg.org/lukeflo/bibiman): CLI, TUI
- [bibman](https://codeberg.org/KMIJPH/bibman): CLI, TUI
- [jabref](https://github.com/JabRef/jabref): GUI
- [papis](https://github.com/papis/papis): CLI, TUI, local web app
- [pubs](https://github.com/pubs/pubs): CLI
- [xapers](https://finestructure.net/xapers): CLI, TUI
- [zotero](https://github.com/zotero/zotero): GUI, remote web app

### Changelog

You can find the detailed changes throughout coBib's history in [the Changelog](https://gitlab.com/cobib/cobib/-/blob/master/CHANGELOG.md).


## License

coBib is licensed under the [MIT License](https://gitlab.com/cobib/cobib/-/blob/master/LICENSE.txt).

[^1]: References like this one get interpreted by the documentation generator. If you are reading this as the README page, you may find the [online documentation](https://cobib.gitlab.io/cobib/cobib.html) more enjoyable.

[//]: # ( vim: set ft=markdown tw=0: )
