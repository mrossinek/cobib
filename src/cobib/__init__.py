"""coBib."""
import os
import subprocess

__version__ = "3.0.0a1"

if os.path.exists(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/../.git"):
    # if installed from source, append HEAD commit SHA to version info as metadata
    proc = subprocess.Popen(["git", "rev-parse", "HEAD"], stdout=subprocess.PIPE)
    git_revision, _ = proc.communicate()
    __version__ += "+" + git_revision.decode("utf-8")[:7]
