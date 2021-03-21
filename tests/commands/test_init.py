"""Tests for CoBib's InitCommand."""
# pylint: disable=no-self-use,unused-argument

import os
from datetime import datetime
from shutil import rmtree

import pytest

from cobib.commands import InitCommand
from cobib.config import config

from .command_test import CommandTest


class TestInitCommand(CommandTest):
    """Tests for CoBib's InitCommand."""

    def get_command(self):
        """Get the command tested by this class."""
        return InitCommand

    @pytest.mark.parametrize(
        ["setup"],
        [
            [{"git": False, "database": False}],
            [{"git": True, "database": False}],
            [{"git": True, "database": True}],
        ],
        indirect=["setup"],
    )
    @pytest.mark.parametrize(["safe"], [[False], [True]])
    def test_command(self, setup, safe):
        """Test the command itself."""
        if safe:
            # fill database file
            with open(config.database.file, "w") as file:
                file.write("test")
        # store current time
        now = float(datetime.now().timestamp())
        # try running init
        InitCommand().execute(["--git"] if setup["git"] else [])
        if safe:
            # check database file still contains 'test'
            with open(config.database.file, "r") as file:
                assert file.read() == "test"
        else:
            # check creation time of temporary database file
            ctime = os.stat(config.database.file).st_ctime
            # assert these times are close
            assert ctime - now < 0.1 or now - ctime < 0.1
        if setup["git"] and not setup["database"]:
            # check creation time of temporary database git folder
            ctime = os.stat(self.COBIB_TEST_DIR_GIT).st_ctime
            # assert these times are close
            assert ctime - now < 0.1 or now - ctime < 0.1
            # and assert that it is indeed a folder
            assert os.path.isdir(self.COBIB_TEST_DIR_GIT)
            # assert the git commit message
            self.assert_git_commit_message("init", {"git": True})

    @pytest.mark.parametrize(
        ["setup"],
        [
            [{"git": False, "database": False}],
        ],
        indirect=["setup"],
    )
    def test_warn_insufficient_config(self, setup, caplog):
        """Test warning in case of insufficient config."""
        try:
            # store current time
            now = float(datetime.now().timestamp())
            # try running init
            InitCommand().execute(["--git"])

            # assert warning is printed
            assert (
                "cobib.commands.init",
                30,
                "You are about to initialize the git tracking of your database, but this will only "
                "have effect if you also enable the DATABASE/git setting in your configuration "
                "file!",
            ) in caplog.record_tuples
            # now assert that the command did everything as usual though

            # check creation time of temporary database file
            ctime = os.stat(config.database.file).st_ctime
            # assert these times are close
            assert ctime - now < 0.1 or now - ctime < 0.1
            # check creation time of temporary database git folder
            ctime = os.stat(self.COBIB_TEST_DIR_GIT).st_ctime
            # assert these times are close
            assert ctime - now < 0.1 or now - ctime < 0.1
            # and assert that it is indeed a folder
            assert os.path.isdir(self.COBIB_TEST_DIR_GIT)
            # assert the git commit message
            self.assert_git_commit_message("init", {"git": True})
        finally:
            # clean up file system
            rmtree(self.COBIB_TEST_DIR_GIT)

    @pytest.mark.parametrize(
        ["setup"],
        [
            [{"git": False, "database": False}],
        ],
        indirect=["setup"],
    )
    # other variants are already covered by test_command
    def test_cmdline(self, setup, monkeypatch):
        """Test the command-line access of the command."""
        # store current time
        now = float(datetime.now().timestamp())
        # try calling init
        self.run_module(monkeypatch, "main", ["cobib", "init"])
        # try running init
        # check creation time of temporary database file
        ctime = os.stat(config.database.file).st_ctime
        # assert these times are close
        assert ctime - now < 0.1 or now - ctime < 0.1
