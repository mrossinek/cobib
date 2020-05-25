# CoBib

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
* manually editing entries using the $EDITOR
* and general database inspection/modification via a curses-based TUI

## Installation
You can either install cobib via pip: `pip install cobib` or you can download
the source code and install it manually:
```
git clone https://gitlab.com/mrossinek/cobib
cd cobib
make install
```
The advantage of the latter is that the crude Zsh completion and man page are
installed, too. When installing via pip, you can download these separately from
the source code repository and follow the commands of `make install_extras` to
install them under their respective paths.

This will install the `cobib` package. By default, `cobib` will store your
database at `~/.local/share/cobib/literature.yaml`

To see how you can change this, see [Config](#Config).


## Usage
Start by initializing the database with
```
cobib init
```
Afterwards you can simply run `cobib` to start the TUI.
If you prefer full control from the command line you can also run all commands
directly via the CLI. Available commands are `add`, `list`, `edit`, `remove`,
`show`, `open` and `export`. Type `cobib --help` for further information or
`cobib <subcommand> --help` for more detailed information on the specific
subcommands.

You can also find more information in the man page.


## Config
You can overwrite the default configuration by placing a `config.ini` file at
`~/.config/cobib/`. Take a look at the [default config](https://gitlab.com/mrossinek/cobib/blob/master/cobib/docs/default.ini) to see what possible
configuration options exist.

You may also specify a different config file at runtime by using the `-c` or
`--config` command line argument.

You can also find more information in the man page.
