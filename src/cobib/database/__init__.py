"""coBib's database module.

coBib uses a plain-test YAML file to store the bibliographic database.
This module contains the components which represent this database at runtime.
"""

from .database import Database
from .entry import Entry

__all__ = [
    "Database",
    "Entry",
]
