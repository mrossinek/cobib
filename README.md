# CoBib

[![pipeline](https://gitlab.com/mrossinek/cobib/badges/master/pipeline.svg)](https://gitlab.com/mrossinek/cobib/-/pipelines)
[![coverage](https://gitlab.com/mrossinek/cobib/badges/master/coverage.svg)](https://gitlab.com/mrossinek/cobib/-/graphs/master/charts)
[![PyPI](https://img.shields.io/pypi/v/cobib)](https://pypi.org/project/cobib/)

[Quickstart](https://mrossinek.gitlab.io/programming/introducing-cobib/)

Welcome to CoBib - the Console Bibliography!
I have started this project when I was looking into alternatives to popular
reference managers such as Mendeley, which has more features than I use on a
regular basis and does not allow me to work from the command line which is
where I spent most of the time that I spent on the computer.

Hence, I have decided to make it my own task of implementing a simple, yet
fast, reference manager. CoBib is written in Python and uses a YAML file to
store its bibliography in a plain text format.

Currently CoBib provides the following functionality:
* adding new references from a bibtex source or via DOI or arXiv ID
* querying the database by in- and exclusion filters
* printing detailed information about a reference ID
* exporting a list of references to the biblatex format
* opening associated files using an external program
* manually editing entries using the `$EDITOR`
* and general database inspection/modification via a curses-based TUI

## Installation
You can either install CoBib via pip: `pip3 install cobib`.

If you would also like to install the man-page and (crude!) Zsh completion,
you need to download the source code and do the following:
```
git clone https://gitlab.com/mrossinek/cobib
cd cobib
make install_extras
```

This will install the `cobib` package. By default, `cobib` will store your
database at `~/.local/share/cobib/literature.yaml`

To see how you can change this, see [Config](#Config).

### Windows
Please note that Windows is *not* supported!
This is due to the fact that [Python under Windows does not ship with the `curses` module][1].

However, if you are using Windows 10 you should be able to install and use CoBib
within the Linux subsystem.

[1]: https://docs.python.org/3/howto/curses.html#what-is-curses

## Usage
Start by initializing the database with
```
cobib init
```
If you would like CoBib to track your database with git, you should use
```
cobib init --git
```
and enable the `DATABASE/git` option (see also [Config](#Config)).
Afterwards you can simply run `cobib` to start the TUI.
If you prefer full control from the command line you can also run all commands
directly via the CLI. Available commands are `add`, `list`, `edit`, `remove`,
`show`, `open` and `export`. Type `cobib --help` for further information or
`cobib <subcommand> --help` for more detailed information on the specific
subcommands.

**Note**: when adding data from a `.bib` file, make sure that it is in the Bib**La**Tex format!

You can also find more information in the man page.


## Config
You can overwrite the default configuration by placing a `config.py` file in `~/.config/cobib/`.
The easiest way to get started with this file is by copying [`example.py`](https://gitlab.com/mrossinek/cobib/-/blob/master/src/cobib/config/example.py)
or by using `cobib _example_config > ~/.config/cobib/config.py`.

You may also specify a different config file at runtime by using the `-c` or `--config` command line argument.

You can also find more information in the man page.

## Documentation
CoBib's documentation is hosted at https://mrossinek.gitlab.io/cobib/

If you would like to generate a local version, you need to clone the source code, and install
[`pdoc`](https://github.com/mitmproxy/pdoc) in order to generate it:
```
git clone https://gitlab.com/mrossinek/cobib.git
cd cobib
pip install pdoc
pdoc -d google -o docs src/cobib
```
You can then browse the documentation from `docs/index.html`.

[//]: # ( vim: set ft=markdown: )
