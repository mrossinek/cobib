"""Tests for coBib's main executable."""
# pylint: disable=unused-argument

import logging
import os
import tempfile
from pathlib import Path
from typing import Any, List

import pytest

from cobib.config import config

from . import get_resource
from .cmdline_test import CmdLineTest


class TestMainExecutable(CmdLineTest):
    """Tests for coBib's main executable.

    Note: all commands are tested separately in their respective test files.
    Therefore, the tests here mainly deal with testing the global parser arguments.
    """

    @staticmethod
    @pytest.fixture
    def setup() -> None:
        """Load testing config."""
        config.load(get_resource("debug.py"))

    def test_version(
        self, setup: Any, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Tests the version parser argument."""
        with pytest.raises(SystemExit):
            self.run_module(monkeypatch, "main", ["cobib", "--version"])
        # pylint: disable=import-outside-toplevel
        from cobib import __version__

        assert capsys.readouterr().out.strip() == f"coBib v{__version__}"

    @pytest.mark.parametrize(
        ["main", "args"],
        [
            ["main", ["open", "einstein"]],
            ["helper_main", ["_example_config"]],
        ],
    )
    @pytest.mark.parametrize(
        ["verbosity_arg", "level"],
        [
            ["-v", logging.INFO],
            ["-vv", logging.DEBUG],
        ],
    )
    def test_verbosity(
        self,
        setup: Any,
        monkeypatch: pytest.MonkeyPatch,
        main: str,
        args: List[str],
        verbosity_arg: str,
        level: int,
    ) -> None:
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
            ["helper_main", ["_example_config"]],
        ],
    )
    def test_logfile(
        self, setup: Any, monkeypatch: pytest.MonkeyPatch, main: str, args: List[str]
    ) -> None:
        """Tests the logfile parser argument."""
        logfile = str(Path(tempfile.gettempdir()) / "cobib_test_logging.log")
        # we choose the open command as an arbitrary choice which has minimal side effects
        self.run_module(monkeypatch, main, ["cobib", "-l", logfile] + args)
        try:
            assert isinstance(logging.getLogger().handlers[0], logging.FileHandler)
            assert logging.getLogger().handlers[0].baseFilename == logfile  # type: ignore
        finally:
            os.remove(logfile)

    @pytest.mark.parametrize(
        ["main", "args"],
        [
            ["main", ["open", "einstein"]],
            ["helper_main", ["_example_config"]],
        ],
    )
    def test_configfile(self, monkeypatch: pytest.MonkeyPatch, main: str, args: List[str]) -> None:
        """Tests the configfile parser argument."""
        # we choose the open command as an arbitrary choice which has minimal side effects
        self.run_module(monkeypatch, main, ["cobib", "-c", get_resource("debug.py")] + args)
        assert config.database.file == get_resource("example_literature.yaml")
