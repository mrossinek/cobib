"""coBib's debugging config."""

import os

from cobib.config import config

root = os.path.dirname(__file__)
config.database.file = os.path.abspath(os.path.join(root, "example_literature.yaml"))
