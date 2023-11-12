"""coBib's database module.

coBib uses a plain-test YAML file to store the bibliographic database.
This module contains the components which represent this database at runtime.
"""

from .author import Author as Author
from .database import Database as Database
from .entry import Entry as Entry
