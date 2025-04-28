"""coBib command test class."""

from __future__ import annotations

import json
import logging
import os
import shlex
import subprocess
import tempfile
from abc import abstractmethod
from collections.abc import Generator
from pathlib import Path
from shutil import copyfile, rmtree
from typing import TYPE_CHECKING, Any

import pytest

from cobib.config import config
from cobib.database import Database

from .. import get_resource
from ..cmdline_test import CmdLineTest

TMPDIR = Path(tempfile.gettempdir()).resolve()

if TYPE_CHECKING:
    import _pytest.fixtures

    import cobib.commands


class CommandTest(CmdLineTest):
    """The base class for coBib's command test classes."""

    COBIB_TEST_DIR = TMPDIR / "cobib_test"
    """Path to the temporary coBib test directory."""

    COBIB_TEST_DIR_GIT = COBIB_TEST_DIR / ".git"
    """Path to the temporary coBib test git directory."""

    @abstractmethod
    def get_command(self) -> type[cobib.commands.base_command.Command]:
        """Get the command tested by this class.

        Returns:
            The command to be tested by this class.
        """

    @abstractmethod
    def test_command(self) -> None:
        """Test the command itself."""

    @pytest.fixture
    def setup(self, request: _pytest.fixtures.SubRequest) -> Generator[dict[str, Any], None, None]:
        """Setup testing environment.

        This method takes care of setting up the testing configuration. This involves:
            - using `cat` for `config.commands.edit.editor` and `config.commands.open.command`
            - setting up a testing database based (if requested by `request.param["database"]`)
            - initializing git tracking (if requested by `request.param["git"]`)

        After yielding to the actual test, this setup also gets torn down.

        Args:
            request: a pytest sub-request providing access to nested parameters.

        Yields:
            The internally used parameters for potential later re-use during the actual test.
        """
        if not hasattr(request, "param"):
            # use default settings
            request.param = {"git": False, "database": True}

        # use temporary config
        config.commands.delete.confirm = False
        config.commands.edit.editor = "cat"
        config.commands.open.command = "cat"
        config.database.cache = None
        config.database.file = self.COBIB_TEST_DIR / "database.yaml"
        config.database.git = request.param.get("git", False)
        config.utils.file_downloader.default_location = "/tmp"
        config.logging.version = None

        # load database
        if request.param.get("database", True):
            self.COBIB_TEST_DIR.mkdir(parents=True, exist_ok=True)
            copyfile(
                get_resource(
                    request.param.get("database_filename", "example_literature.yaml"),
                    request.param.get("database_location", None),
                ),
                config.database.file,
            )
            Database().read()
            if request.param.get("git", True):
                root = self.COBIB_TEST_DIR
                msg = "Initial commit"
                commands = [
                    f"cd {root}",
                    "git init",
                    "git add -- database.yaml",
                    f"git commit --no-gpg-sign --quiet --message {shlex.quote(msg)}",
                ]
                os.system("; ".join(commands))

        yield request.param

        # clean up file system
        Path(config.database.file).unlink(missing_ok=True)
        if request.param.get("git", False):
            rmtree(self.COBIB_TEST_DIR_GIT, ignore_errors=True)
        # remove all handlers from root logger as to not accumulate them during the test suite
        logging.getLogger().handlers = []

        # clean up database
        if request.param.get("database", True):
            Database.reset()

        # clean up config
        config.defaults()

    def assert_git_commit_message(
        self, command: str, args: dict[str, Any] | None = None, msg: str | None = None
    ) -> None:
        """Assert the last auto-generated git commit message.

        Args:
            command: the last command type which ran.
            args: the arguments which were passed to the command.
            msg: an optional commit message which overrules the auto-generated message from the
                 previous arguments.
        """
        # get last commit message
        with subprocess.Popen(
            ["git", "-C", self.COBIB_TEST_DIR, "show", "--format=format:%B", "--no-patch", "HEAD"],
            stdout=subprocess.PIPE,
        ) as proc:
            message, _ = proc.communicate()
            # decode it
            split_msg = message.decode("utf-8").split("\n")

            if msg is not None:
                assert msg == "\n".join(split_msg)
                return

            # assert subject line
            assert f"Auto-commit: {command.title()}Command" in split_msg[0]

            if args is not None:
                # assert args
                args_str = json.dumps(args, indent=2, default=str)
                for ref, truth in zip(args_str.split("\n"), split_msg[2:]):
                    assert ref == truth
