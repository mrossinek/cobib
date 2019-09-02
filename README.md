# CReMa

Welcome to CReMa - the Console Reference Manager!
I have started this project when I was looking into alternatives to popular
reference managers such as Mendeley, which has more features than I use on a
regular basis and does not allow me to work from the command line which is
where I spent most of the time that I spent on the computer.

Hence, I have decided to make it my own task of implementing a simple, yet
fast, reference manager. CReMa is written in Python and uses a YAML file to
store all references in a plain text format.

Currently CReMa provides the following functionality:
* adding new references from a bibtex source or via DOI, arXiv ID or PDF
* querying the database by in- and exclusion filters
* printing detailed information about a reference ID
* exporting a list of references to the biblatex format
* opening associated files using an external program
* manually editing entries using the $EDITOR

Future features may include:
* previewing abstracts directly inside the terminal
* extracting abstracts from PDFs


## Installation
```
git clone https://gitlab.com/mrossinek/crema
cd crema
python setup.py install
```

This will install the `crema` package. By default, `crema` will store your
database at `~/.local/share/crema/literature.yaml`

To see how you can change this, see [Config](#Config).


## Usage
Start by initializing the database with
```
crema init
```
Afterwards you can `add`, `list`, `edit`, `remove`, `show`, `open` and `export`
database entries. Type `crema --help` for further information or
`crema <subcommand> --help` for more detailed information on the specific
subcommands.


## Config
You can overwrite the default configuration by placing a `config.ini` file at
`~/.config/crema/`. Take a look at the [default config](https://gitlab.com/mrossinek/crema/blob/master/crema/docs/default.ini) to see what possible
configuration options exist.

You may also specify a different config file at runtime by using the `-c` or
`--config` command line argument.
