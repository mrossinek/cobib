"""Tests for coBib's OpenCommand."""
# pylint: disable=unused-argument

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Generator, List, Optional, Tuple, Type

import pytest
from typing_extensions import override

from cobib.commands import ModifyCommand, OpenCommand
from cobib.config import Event, config
from cobib.database import Database

from .. import MockStdin, get_resource
from .command_test import CommandTest

if TYPE_CHECKING:
    import _pytest.fixtures

    import cobib.commands


class TestOpenCommand(CommandTest):
    """Tests for coBib's OpenCommand."""

    # Note: we can hard-code the `/tmp` path here, because we never really create these files.
    # We just need some absolute paths to test against.
    TMP_FILE_A = "/tmp/a.txt"
    TMP_FILE_B = "/tmp/b.txt"

    @override
    def get_command(self) -> Type[cobib.commands.base_command.Command]:
        return OpenCommand

    @pytest.fixture(autouse=True)
    def auto_setup(self) -> Generator[None, None, None]:
        """Additional setup instructions which will be run automatically for this class of tests."""
        path_a = Path(self.TMP_FILE_A)
        path_b = Path(self.TMP_FILE_B)

        path_a.touch()
        path_b.touch()

        yield

        path_a.unlink(missing_ok=True)
        path_b.unlink(missing_ok=True)

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
                "[all,help,cancel]: ",
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
            if "help" in stdin_list:
                expected_out += expected_out.copy()
                expected_out[4] += "Multiple targets were found. You may select the following:"
                extra_out = [
                    "  1. an individual URL number",
                    "  2. a target type (provided in '[...]')",
                    "  3. 'all'",
                    "  4. or 'cancel' to abort the command",
                ]
                for line in reversed(extra_out):
                    expected_out.insert(5, line)

                expected_log.append(("cobib.commands.open", 10, "User requested help."))
                expected_log.append(("cobib.commands.open", 30, "User aborted open command."))
            elif "cancel" in stdin_list:
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

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["args", "post_setup"],
        [
            [["knuthwebsite"], {"multi_file": False}],
            [["example_multi_file_entry"], {"multi_file": True, "stdin_list": ["cancel"]}],
            [["example_multi_file_entry"], {"multi_file": True, "stdin_list": ["help", "cancel"]}],
            [["example_multi_file_entry"], {"multi_file": True, "stdin_list": ["all"]}],
            [["example_multi_file_entry"], {"multi_file": True, "stdin_list": ["url"]}],
            [["example_multi_file_entry"], {"multi_file": True, "stdin_list": ["1"]}],
        ],
        indirect=["post_setup"],
    )
    async def test_command(  # pylint: disable=invalid-overridden-method
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
        await OpenCommand(*args).execute()

        true_log = [rec for rec in caplog.record_tuples if rec[0] == "cobib.commands.open"]
        true_out = capsys.readouterr().out.split("\n")

        self._assert(true_out, true_log, **post_setup)

    @pytest.mark.asyncio
    async def test_warning_missing_label(
        self, setup: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test warning for missing label.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            caplog: the built-in pytest fixture.
        """
        await OpenCommand("dummy").execute()
        assert (
            "cobib.commands.open",
            30,
            "No entry with the label 'dummy' could be found.",
        ) in caplog.record_tuples

    @pytest.mark.asyncio
    async def test_warning_nothing_to_open(
        self, setup: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test warning for label with nothing to open.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            caplog: the built-in pytest fixture.
        """
        await OpenCommand("einstein").execute()
        assert (
            "cobib.commands.open",
            30,
            "The entry 'einstein' has no actionable field associated with it.",
        ) in caplog.record_tuples

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["args", "post_setup"],
        [
            [["example_multi_file_entry"], {"multi_file": True, "stdin_list": ["1"]}],
        ],
        indirect=["post_setup"],
    )
    async def test_warning_missing_file(
        self,
        setup: Any,
        post_setup: Any,
        caplog: pytest.LogCaptureFixture,
        args: List[str],
    ) -> None:
        """Test warning for non-existent files.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            post_setup: an additional setup fixture.
            caplog: the built-in pytest fixture.
            args: the arguments to pass to the command.
        """
        path_a = Path(self.TMP_FILE_A)
        path_a.unlink(missing_ok=True)

        await OpenCommand(*args).execute()

        assert (
            "cobib.commands.open",
            40,
            f"Could not find the file at '{path_a}'!",
        ) in caplog.record_tuples

    @pytest.mark.asyncio
    async def test_config_openable_fields(
        self,
        setup: Any,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test the `config.commands.open.fields` setting.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            monkeypatch: the built-in pytest fixture.
            capsys: the built-in pytest fixture.
        """
        config.commands.open.fields = ["note"]

        with open(
            get_resource("example_multi_file_entry.yaml", "commands"), "r", encoding="utf-8"
        ) as multi_file_entry:
            with open(config.database.file, "a", encoding="utf-8") as database:
                for line in multi_file_entry.readlines():
                    if line == "  file:\n":
                        database.write("  note:\n")
                    else:
                        database.write(line)

        Database().read()

        monkeypatch.setattr("sys.stdin", MockStdin(["cancel"]))

        await OpenCommand("example_multi_file_entry").execute()

        true_out = capsys.readouterr().out.split("\n")

        expected_out = [
            "  1: [note] " + self.TMP_FILE_A,
            "  2: [note] " + self.TMP_FILE_B,
            "[all,help,cancel]: ",
        ]

        for line, truth in zip(true_out, expected_out):
            assert line == truth

    @pytest.mark.asyncio
    async def test_open_non_list_field(
        self,
        setup: Any,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test opening of non-list type fields.

        This is a regression test against https://gitlab.com/cobib/cobib/-/issues/100

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            monkeypatch: the built-in pytest fixture.
            caplog: the built-in pytest fixture.
        """
        config.commands.open.fields = ["note"]

        with open(
            get_resource("example_multi_file_entry.yaml", "commands"), "r", encoding="utf-8"
        ) as multi_file_entry:
            with open(config.database.file, "a", encoding="utf-8") as database:
                for line in multi_file_entry.readlines():
                    if line == "  file:\n":
                        database.write("  note: /tmp/a.txt\n")
                        database.write("...\n")
                        break
                    database.write(line)

        Database().read()

        monkeypatch.setattr("sys.stdin", MockStdin())

        await OpenCommand("example_multi_file_entry").execute()

        true_log = [rec for rec in caplog.record_tuples if rec[0] == "cobib.commands.open"]

        expected_log = [
            ("cobib.commands.open", 10, "Starting Open command."),
            (
                "cobib.commands.open",
                10,
                'Parsing "/tmp/a.txt" for URLs.',
            ),
            (
                "cobib.commands.open",
                10,
                'Opening "/tmp/a.txt" with cat.',
            ),
        ]
        assert true_log == expected_log

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["field", "post_setup"],
        [
            ["all", {"multi_file": True}],
            ["file", {"multi_file": True}],
            ["url", {"multi_file": True}],
        ],
        indirect=["post_setup"],
    )
    async def test_field_cmdline_switch(
        self,
        setup: Any,
        post_setup: Any,
        caplog: pytest.LogCaptureFixture,
        capsys: pytest.CaptureFixture[str],
        field: str,
    ) -> None:
        """Test the command itself.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            post_setup: an additional setup fixture.
            caplog: the built-in pytest fixture.
            capsys: the built-in pytest fixture.
            field: the field to open via the command-line switch.
        """
        expected_log = [
            ("cobib.commands.open", 10, "Starting Open command."),
            ("cobib.commands.open", 10, 'Parsing "/tmp/a.txt" for URLs.'),
            ("cobib.commands.open", 10, 'Parsing "/tmp/b.txt" for URLs.'),
            ("cobib.commands.open", 10, 'Parsing "https://www.duckduckgo.com" for URLs.'),
            ("cobib.commands.open", 10, 'Parsing "https://www.google.com" for URLs.'),
            ("cobib.commands.open", 10, f"User selected the {field} set of urls from the CLI."),
        ]
        if field in ("all", "file"):
            expected_log += [
                ("cobib.commands.open", 10, 'Opening "/tmp/a.txt" with cat.'),
                ("cobib.commands.open", 10, 'Opening "/tmp/b.txt" with cat.'),
            ]
        if field in ("all", "url"):
            expected_log += [
                ("cobib.commands.open", 10, 'Opening "https://www.duckduckgo.com" with cat.'),
                ("cobib.commands.open", 10, 'Opening "https://www.google.com" with cat.'),
            ]

        await OpenCommand("example_multi_file_entry", "--field", field).execute()

        true_log = [rec for rec in caplog.record_tuples if rec[0] == "cobib.commands.open"]
        assert true_log == expected_log

        true_out = capsys.readouterr().out.split("\n")
        assert true_out == [""]

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["post_setup"],
        [
            [{"multi_file": False}],
        ],
        indirect=["post_setup"],
    )
    async def test_cmdline(
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
        await self.run_module(monkeypatch, "main", ["cobib", "open", "knuthwebsite"])

        true_out = capsys.readouterr().out.split("\n")

        self._assert(true_out, logs=None, **post_setup)

    @pytest.mark.asyncio
    async def test_event_pre_open_command(
        self,
        setup: Any,
        post_setup: Any,
        caplog: pytest.LogCaptureFixture,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Tests the PreOpenCommand event."""

        @Event.PreOpenCommand.subscribe
        def hook(command: OpenCommand) -> None:
            command.largs.labels = ["knuthwebsite"]

        assert Event.PreOpenCommand.validate()

        await OpenCommand("einstein").execute()

        true_log = [rec for rec in caplog.record_tuples if rec[0] == "cobib.commands.open"]
        true_out = capsys.readouterr().out.split("\n")

        self._assert(true_out, true_log, multi_file=False)

    @pytest.mark.asyncio
    async def test_event_post_open_command(
        self,
        setup: Any,
        post_setup: Any,
        caplog: pytest.LogCaptureFixture,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Tests the PostOpenCommand event."""

        @Event.PostOpenCommand.subscribe
        def hook(command: OpenCommand) -> None:
            print(command.largs.labels, file=sys.stderr)

        assert Event.PostOpenCommand.validate()

        await OpenCommand("knuthwebsite").execute()

        true_log = [rec for rec in caplog.record_tuples if rec[0] == "cobib.commands.open"]
        outerr = capsys.readouterr()
        true_out = outerr.out.split("\n")

        self._assert(true_out, true_log, multi_file=False)

        assert outerr.err == "['knuthwebsite']\n"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["args", "post_setup"],
        [
            [["example_multi_file_entry"], {"multi_file": True, "stdin_list": ["1"]}],
        ],
        indirect=["post_setup"],
    )
    async def test_hook_last_opened(self, setup: Any, post_setup: Any, args: List[str]) -> None:
        """Tests the hook to keep track of the last time an entry was opened.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            post_setup: an additional setup fixture.
            args: the arguments to pass to the command.
        """
        assert "last_opened" not in Database()["example_multi_file_entry"].data

        @Event.PostOpenCommand.subscribe
        def hook(command: OpenCommand) -> None:
            ModifyCommand(
                f"last_opened:{datetime.now()}",
                "-s",
                "--",
                *command.opened_entries,
            ).execute()

        assert Event.PostOpenCommand.validate()

        await OpenCommand(*args).execute()

        assert "last_opened" in Database()["example_multi_file_entry"].data
