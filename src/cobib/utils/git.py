"""coBib's git manager.

.. include:: ../man/cobib-git.7.html_fragment
"""

from __future__ import annotations

import subprocess
from pathlib import Path


def is_inside_work_tree(path: Path) -> bool:
    """Returns whether the provided path is inside a git worktree and is not being ignored.

    The reason that we also check whether the path is being ignored, is to support the tox-based
    testing environment of coBib which places the temporary testing directories inside coBib's own
    git directory structure (but in an ignored location).

    Args:
        path: the path to check.

    Returns:
        Whether the provided path is inside a git worktree and is not being ignored.
    """
    inside_work_tree = subprocess.run(
        ["git", "-C", path, "rev-parse", "--is-inside-work-tree"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if inside_work_tree.returncode != 0 or inside_work_tree.stdout.decode().strip() != "true":
        return False  # pragma: no cover
    path_ignored = subprocess.run(
        ["git", "-C", path, "check-ignore", "--quiet", path],
        check=False,
    )
    return path_ignored.returncode != 0
