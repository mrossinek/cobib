"""coBib - the Console Bibliography.

.. include:: ../../README.md
"""

import subprocess
from pathlib import Path

__version__ = "4.5.0"

if (Path(__file__).parent.parent.parent / ".git").exists():
    # if installed from source, append HEAD commit SHA to version info as metadata
    with subprocess.Popen(["git", "rev-parse", "HEAD"], stdout=subprocess.PIPE) as proc:
        git_revision, _ = proc.communicate()
    __version__ += "+" + git_revision.decode("utf-8")[:7]
