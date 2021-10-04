"""Tests for coBib's OpenCommand."""
# pylint: disable=no-self-use,unused-argument

from __future__ import annotations

import sys
from argparse import Namespace
from typing import TYPE_CHECKING, Any, Dict, Generator, List, Optional, Tuple, Type

import pytest

from cobib.commands import OpenCommand
from cobib.config import Event, config
from cobib.database import Database

from .. import MockStdin, get_resource
from ..tui.tui_test import TUITest
from .command_test import CommandTest

if TYPE_CHECKING:
    import _pytest.fixtures

    import cobib.commands


class TestOpenCommand(CommandTest, TUITest):
    """Tests for coBib's OpenCommand."""

    # Note: we can hard-code the `/tmp` path here, because we never really create these files.
    # We just need some absolute paths to test against.
    TMP_FILE_A = "/tmp/a.txt"
    TMP_FILE_B = "/tmp/b.txt"

    def get_command(self) -> Type[cobib.commands.base_command.Command]:
        # noqa: D102
        return OpenCommand

    @pytest.fixture
    def post_setup(
        self, monkeypatch: pytest.MonkeyPatch, request: _pytest.fixtures.SubRequest
    ) -> Generator[Dict[str, Any], None, None]:
        """Additional setup instructions.

        Args:
            monkeypatch: the built-in pytest fixture.
            request: a pytest sub-request providing access to nested parameters.

        Yields:
            The internally used parameters for potential later re-use during the actual test.
        """
        if not hasattr(request, "param"):
            # use default settings
            request.param = {"stdin_list": None, "multi_file": True}

        if request.param.get("multi_file", True):
            with open(
                get_resource("example_multi_file_entry.yaml", "commands"), "r", encoding="utf-8"
            ) as multi_file_entry:
                with open(config.database.file, "a", encoding="utf-8") as database:
                    database.write(multi_file_entry.read())
            Database().read()

        monkeypatch.setattr("sys.stdin", MockStdin(request.param.get("stdin_list", None)))

        yield request.param

    def _assert(  # type: ignore
        self, output: List[str], logs: Optional[List[Tuple[str, int, str]]] = None, **kwargs
    ) -> None:
        """Common assertion utility method.

        Args:
            output: the list of lines printed to `sys.stdout`.
            logs: the list of logged messages.
            kwargs: additional test-specific keyword arguments.
        """
        if not kwargs.get("multi_file", True):
            expected_log = [
                ("cobib.commands.open", 10, "Starting Open command."),
                (
                    "cobib.commands.open",
                    10,
                    'Parsing "http://www-cs-faculty.stanford.edu/\\~{}uno/abcde.html" for URLs.',
                ),
                (
                    "cobib.commands.open",
                    10,
                    'Opening "http://www-cs-faculty.stanford.edu/\\~{}uno/abcde.html" with cat.',
                ),
            ]
            if logs is not None:
                assert logs == expected_log
        else:
            expected_out = [
                "  1: [file] " + self.TMP_FILE_A,
                "  2: [file] " + self.TMP_FILE_B,
                "  3: [url] https://www.duckduckgo.com",
                "  4: [url] https://www.google.com",
                "Entry to open [Type 'help' for more info]: ",
            ]

            expected_log = [
                ("cobib.commands.open", 10, "Starting Open command."),
                ("cobib.commands.open", 10, 'Parsing "' + self.TMP_FILE_A + '" for URLs.'),
                ("cobib.commands.open", 10, 'Parsing "' + self.TMP_FILE_B + '" for URLs.'),
                ("cobib.commands.open", 10, 'Parsing "https://www.duckduckgo.com" for URLs.'),
                ("cobib.commands.open", 10, 'Parsing "https://www.google.com" for URLs.'),
            ]

            stdin_list = kwargs.get("stdin_list", [])
            extra_logs = None
            if not stdin_list:
                expected_log.append(("cobib.commands.open", 30, "User aborted open command."))
            elif "help" in stdin_list:
                expected_out += expected_out.copy()
                expected_out[4] += "You can specify one of the following options:"
                extra_out = [
                    "  1. a url number",
                    "  2. a field name provided in '[...]'",
                    "  3. or simply 'all'",
                    "  4. ENTER will abort the command",
                    "",
                ]
                for line in reversed(extra_out):
                    expected_out.insert(5, line)

                expected_log.append(("cobib.commands.open", 10, "User requested help."))
                expected_log.append(("cobib.commands.open", 30, "User aborted open command."))
            elif "all" in stdin_list:
                extra_logs = [
                    ("cobib.commands.open", 10, "User selected all urls."),
                    ("cobib.commands.open", 10, 'Opening "' + self.TMP_FILE_A + '" with cat.'),
                    ("cobib.commands.open", 10, 'Opening "' + self.TMP_FILE_B + '" with cat.'),
                    ("cobib.commands.open", 10, 'Opening "https://www.duckduckgo.com" with cat.'),
                    ("cobib.commands.open", 10, 'Opening "https://www.google.com" with cat.'),
                ]
            elif "url" in stdin_list:
                extra_logs = [
                    ("cobib.commands.open", 10, "User selected the url set of urls."),
                    ("cobib.commands.open", 10, 'Opening "https://www.duckduckgo.com" with cat.'),
                    ("cobib.commands.open", 10, 'Opening "https://www.google.com" with cat.'),
                ]
            elif "1" in stdin_list:
                extra_logs = [
                    ("cobib.commands.open", 10, "User selected url 1"),
                    ("cobib.commands.open", 10, 'Opening "' + self.TMP_FILE_A + '" with cat.'),
                ]

            if extra_logs is not None:
                expected_log.extend(extra_logs)

            for line, truth in zip(output, expected_out):
                assert line == truth
            if logs is not None:
                assert logs == expected_log

    @pytest.mark.parametrize(
        ["args", "post_setup"],
        [
            [["knuthwebsite"], {"multi_file": False}],
            [["example_multi_file_entry"], {"multi_file": True}],
            [["example_multi_file_entry"], {"multi_file": True, "stdin_list": ["help"]}],
            [["example_multi_file_entry"], {"multi_file": True, "stdin_list": ["all"]}],
            [["example_multi_file_entry"], {"multi_file": True, "stdin_list": ["url"]}],
            [["example_multi_file_entry"], {"multi_file": True, "stdin_list": ["1"]}],
        ],
        indirect=["post_setup"],
    )
    def test_command(
        self,
        setup: Any,
        post_setup: Any,
        caplog: pytest.LogCaptureFixture,
        capsys: pytest.CaptureFixture[str],
        args: List[str],
    ) -> None:
        """Test the command itself.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            post_setup: an additional setup fixture.
            caplog: the built-in pytest fixture.
            capsys: the built-in pytest fixture.
            args: the arguments to pass to the command.
        """
        OpenCommand().execute(args)

        true_log = [rec for rec in caplog.record_tuples if rec[0] == "cobib.commands.open"]
        true_out = capsys.readouterr().out.split("\n")

        self._assert(true_out, true_log, **post_setup)

    def test_warning_missing_label(self, setup: Any, caplog: pytest.LogCaptureFixture) -> None:
        """Test warning for missing label.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            caplog: the built-in pytest fixture.
        """
        OpenCommand().execute(["dummy"])
        assert (
            "cobib.commands.open",
            30,
            "No entry with the label 'dummy' could be found.",
        ) in caplog.record_tuples

    def test_warning_nothing_to_open(self, setup: Any, caplog: pytest.LogCaptureFixture) -> None:
        """Test warning for label with nothing to open.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            caplog: the built-in pytest fixture.
        """
        OpenCommand().execute(["einstein"])
        assert (
            "cobib.commands.open",
            30,
            "The entry 'einstein' has no actionable field associated with it.",
        ) in caplog.record_tuples

    @pytest.mark.parametrize(
        ["post_setup"],
        [
            [{"multi_file": False}],
        ],
        indirect=["post_setup"],
    )
    def test_cmdline(
        self,
        setup: Any,
        post_setup: Any,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test the command-line access of the command.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            post_setup: an additional setup fixture.
            monkeypatch: the built-in pytest fixture.
            capsys: the built-in pytest fixture.
        """
        self.run_module(monkeypatch, "main", ["cobib", "open", "knuthwebsite"])

        true_out = capsys.readouterr().out.split("\n")

        self._assert(true_out, logs=None, **post_setup)

    @pytest.mark.parametrize(
        ["select", "keys"],
        [
            [False, "o"],
            [True, "Gvo"],
        ],
    )
    def test_tui(self, setup: Any, select: bool, keys: str) -> None:
        """Test the TUI access of the command.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            select: whether to use the TUI selection.
            keys: the string of keys to pass to the TUI.
        """

        def assertion(screen, logs, **kwargs):  # type: ignore
            expected_log = [
                ("cobib.commands.open", 10, "Open command triggered from TUI."),
                ("cobib.commands.open", 10, "Starting Open command."),
            ]
            if kwargs.get("selection", False):
                expected_log.append(
                    (
                        "cobib.commands.open",
                        30,
                        "The entry 'einstein' has no actionable field associated with it.",
                    )
                )
            else:
                expected_log.append(
                    (
                        "cobib.commands.open",
                        10,
                        # fmt: off
                        'Parsing "http://www-cs-faculty.stanford.edu/\\~{}uno/abcde.html" for '
                        'URLs.',
                        # fmt: on
                    )
                )
                expected_log.append(
                    (
                        "cobib.commands.open",
                        10,
                        # fmt: off
                        'Opening "http://www-cs-faculty.stanford.edu/\\~{}uno/abcde.html" with '
                        'cat.',
                        # fmt: on
                    )
                )

            assert [log for log in logs if log[0] == "cobib.commands.open"] == expected_log

        self.run_tui(keys, assertion, {"selection": select})

    def test_event_pre_open_command(
        self,
        setup: Any,
        post_setup: Any,
        caplog: pytest.LogCaptureFixture,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Tests the PreOpenCommand event."""

        @Event.PreOpenCommand.subscribe
        def hook(largs: Namespace) -> None:
            largs.labels = ["knuthwebsite"]

        assert Event.PreOpenCommand.validate()

        OpenCommand().execute(["einstein"])

        true_log = [rec for rec in caplog.record_tuples if rec[0] == "cobib.commands.open"]
        true_out = capsys.readouterr().out.split("\n")

        self._assert(true_out, true_log, multi_file=False)

    def test_event_post_open_command(
        self,
        setup: Any,
        post_setup: Any,
        caplog: pytest.LogCaptureFixture,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Tests the PostOpenCommand event."""

        @Event.PostOpenCommand.subscribe
        def hook(labels: List[str]) -> None:
            print(labels, file=sys.stderr)

        assert Event.PostOpenCommand.validate()

        OpenCommand().execute(["knuthwebsite"])

        true_log = [rec for rec in caplog.record_tuples if rec[0] == "cobib.commands.open"]
        outerr = capsys.readouterr()
        true_out = outerr.out.split("\n")

        self._assert(true_out, true_log, multi_file=False)

        assert outerr.err == "['knuthwebsite']\n"
