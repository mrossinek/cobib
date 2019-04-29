# CReMa

Welcome to CReMa - the Console Reference Manager!
I have started this project when I was looking into alternatives to popular
reference managers such as Mendeley, which has more features than I use on a
regular basis and does not allow me to work from the command line which is
where I spent most of the time that I spent on the computer.

Hence, I have decided to make it my own task of implementing a simple, yet
fast, reference manager. CReMa is written in Python and uses SQLite3 as its
database in the background.

Currently CReMa provides the following functionality:
* adding new references via DOI, arXiv ID and PDF
* querying the database by in- and exclusion filters
* printing detailed information about a reference ID
* exporting a list of references to the biblatex format
* opening associated files using an external program
* manually editing database entries using the EDITOR

Future features may include:
* importing a set of references from a biblatex library file
* previewing abstracts directly inside the terminal
* extracting abstracts from PDFs


## Installation
```
git clone https://github.com/mrossinek/crema
cd crema
make install
```

This will install the Python script to `/usr/local/bin` and create a default
config file at `~/.config/crema`.


## Usage
Start by initializing the database with
```
crema init
```
Afterwards you can `add`, `list`, `edit`, `show`, `open` and `export` database
entries. Type `crema --help` for further information.


## Config
A different config file may be specified using the `-c` or `--config` command
line argument.
