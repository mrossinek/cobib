"""CoBib command test class."""
# pylint: disable=no-self-use

import json
import logging
import os
import shlex
import subprocess
import tempfile
from abc import abstractmethod
from shutil import copyfile, rmtree

import pytest

from cobib.config import config
from cobib.database import Database
from cobib.logging import log_to_stream

from .. import get_resource
from ..cmdline_test import CmdLineTest

TMPDIR = tempfile.gettempdir()


class CommandTest(CmdLineTest):
    """The base class for CoBib's command test classes."""

    COBIB_TEST_DIR = os.path.join(TMPDIR, "cobib_test")
    COBIB_TEST_DIR_GIT = os.path.join(COBIB_TEST_DIR, ".git")

    @abstractmethod
    def get_command(self):
        """Get the command tested by this class."""

    @abstractmethod
    def test_command(self):
        """Test the command itself."""

    @pytest.fixture
    def setup(self, request):
        """Setup."""
        log_to_stream(logging.DEBUG)

        if not hasattr(request, "param"):
            # use default settings
            request.param = {"git": False, "database": True}

        # use temporary config
        config.commands.edit.editor = "cat"
        config.commands.open.command = "cat"
        config.database.file = os.path.join(self.COBIB_TEST_DIR, "database.yaml")
        config.database.git = request.param.get("git", False)

        # load database
        if request.param.get("database", True):
            os.makedirs(self.COBIB_TEST_DIR, exist_ok=True)
            copyfile(get_resource("example_literature.yaml"), config.database.file)
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
        try:
            os.remove(config.database.file)
            if request.param.get("git", False):
                rmtree(self.COBIB_TEST_DIR_GIT)
        except FileNotFoundError:
            pass

        # clean up database
        if request.param.get("database", True):
            Database().clear()

        # clean up config
        config.defaults()

    def assert_git_commit_message(self, command, args=None):
        """Assert the last auto-generated git commit message."""
        # get last commit message
        proc = subprocess.Popen(
            ["git", "-C", self.COBIB_TEST_DIR, "show", "--format=format:%B", "--no-patch", "HEAD"],
            stdout=subprocess.PIPE,
        )
        message, _ = proc.communicate()
        # decode it
        message = message.decode("utf-8").split("\n")
        # assert subject line
        assert f"Auto-commit: {command.title()}Command" in message[0]

        if args is not None:
            # assert args
            args = json.dumps(args, indent=2, default=str)
            for ref, truth in zip(args.split("\n"), message[2:]):
                assert ref == truth

    def test_handle_argument_error(self, caplog):
        """Test handling of ArgumentError."""
        command_cls = self.get_command()
        command_cls().execute(["--dummy"])
        name = command_cls.name
        for (source, level, message) in caplog.record_tuples:
            if (f"cobib.commands.{name}", logging.ERROR) == (
                source,
                level,
            ) and f"Error: {name}: error:" in message:
                break
        else:
            pytest.fail("No Error logged from ArgumentParser.")
