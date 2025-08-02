"""coBib - the Console Bibliography.

[![coBib](https://gitlab.com/cobib/cobib/-/raw/master/docs/logo/cobib_logo.svg)](https://cobib.gitlab.io/cobib/cobib.html)

.. include:: ../../README.md
   :start-after: # coBib

<hr/>

## Getting Started

.. include:: man/cobib-getting-started.7.html_fragment
"""

import subprocess
from pathlib import Path

__version__ = "5.3.0"

if (Path(__file__).parent.parent.parent / ".git").exists():  # pragma: no branch
    # if installed from source, append HEAD commit SHA to version info as metadata
    with subprocess.Popen(["git", "rev-parse", "HEAD"], stdout=subprocess.PIPE) as proc:
        git_revision, _ = proc.communicate()
    __version__ += "+" + git_revision.decode("utf-8")[:7]
