"""Tests for CoBib's main executable."""
# pylint: disable=unused-argument

import logging
import os
import tempfile

import pytest

from cobib.config import config

from . import get_resource
from .cmdline_test import CmdLineTest


class TestMainExecutable(CmdLineTest):
    """Tests for CoBib's main executable.

    Note: all commands are tested separately in their respective test files.
    Therefore, the tests here mainly deal with testing the global parser arguments.
    """

    @staticmethod
    @pytest.fixture
    def setup():
        """Load testing config."""
        config.load(get_resource("debug.py"))

    def test_version(self, setup, monkeypatch, capsys):
        """Tests the version parser argument."""
        with pytest.raises(SystemExit):
            self.run_module(monkeypatch, "main", ["cobib", "--version"])
        # pylint: disable=import-outside-toplevel
        from cobib import __version__

        assert capsys.readouterr().out.strip() == f"CoBib v{__version__}"

    @pytest.mark.parametrize(
        ["main", "args"],
        [
            ["main", ["open", "einstein"]],
            ["zsh_main", ["_example_config"]],
        ],
    )
    @pytest.mark.parametrize(
        ["verbosity_arg", "level"],
        [
            ["-v", logging.INFO],
            ["-vv", logging.DEBUG],
        ],
    )
    def test_verbosity(self, setup, monkeypatch, main, args, verbosity_arg, level):
        """Tests the verbosity parser argument."""
        # we choose the open command as an arbitrary choice which has minimal side effects
        args = ["cobib"] + args
        if verbosity_arg:
            args.insert(1, verbosity_arg)
        self.run_module(monkeypatch, main, args)
        assert logging.getLogger().getEffectiveLevel() == level

    @pytest.mark.parametrize(
        ["main", "args"],
        [
            ["main", ["open", "einstein"]],
            ["zsh_main", ["_example_config"]],
        ],
    )
    def test_logfile(self, setup, monkeypatch, main, args):
        """Tests the logfile parser argument."""
        logfile = os.path.join(tempfile.gettempdir(), "cobib_test_logging.log")
        # we choose the open command as an arbitrary choice which has minimal side effects
        self.run_module(monkeypatch, main, ["cobib", "-l", logfile] + args)
        try:
            assert isinstance(logging.getLogger().handlers[0], logging.FileHandler)
            assert logging.getLogger().handlers[0].baseFilename == logfile
        finally:
            os.remove(logfile)

    @pytest.mark.parametrize(
        ["main", "args"],
        [
            ["main", ["open", "einstein"]],
            ["zsh_main", ["_example_config"]],
        ],
    )
    def test_configfile(self, monkeypatch, main, args):
        """Tests the configfile parser argument."""
        # we choose the open command as an arbitrary choice which has minimal side effects
        self.run_module(monkeypatch, main, ["cobib", "-c", get_resource("debug.py")] + args)
        assert config.database.file == get_resource("example_literature.yaml")
