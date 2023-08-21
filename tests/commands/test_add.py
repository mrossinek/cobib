"""Tests for coBib's AddCommand."""
# pylint: disable=unused-argument

from __future__ import annotations

import logging
import os
import tempfile
from datetime import datetime
from itertools import zip_longest
from typing import TYPE_CHECKING, Any, Dict, Generator, List, Optional, Type

import pytest
from typing_extensions import override

from cobib.commands import AddCommand
from cobib.config import Event, config
from cobib.database import Database
from cobib.utils.rel_path import RelPath

from .. import MockStdin, get_resource
from .command_test import CommandTest

EXAMPLE_LITERATURE = get_resource("example_literature.yaml")
EXAMPLE_DUPLICATE_ENTRY_BIB = get_resource("example_duplicate_entry.bib", "commands")
EXAMPLE_DUPLICATE_ENTRY_YAML = get_resource("example_duplicate_entry.yaml", "commands")
EXAMPLE_MULTI_FILE_ENTRY_BIB = get_resource("example_multi_file_entry.bib", "commands")
EXAMPLE_MULTI_FILE_ENTRY_YAML = get_resource("example_multi_file_entry.yaml", "commands")

if TYPE_CHECKING:
    import _pytest.fixtures

    import cobib.commands


class TestAddCommand(CommandTest):
    """Tests for coBib's AddCommand."""

    @override
    def get_command(self) -> Type[cobib.commands.base_command.Command]:
        return AddCommand

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
            request.param = {"stdin_list": None}

        monkeypatch.setattr("sys.stdin", MockStdin(request.param.get("stdin_list", None)))

        yield request.param

    def _assert(self, extra_filename: str) -> None:
        """Common assertion utility method.

        Args:
            extra_filename: path to an additional filename whose contents are to be added to the
                expected lines.
        """
        # compare with reference file
        with open(EXAMPLE_LITERATURE, "r", encoding="utf-8") as expected:
            true_lines = expected.readlines()
        with open(extra_filename, "r", encoding="utf-8") as extra:
            true_lines += extra.readlines()
        with open(config.database.file, "r", encoding="utf-8") as file:
            # we use zip_longest to ensure that we don't have more than we expect
            for line, truth in zip_longest(file, true_lines):
                assert line == truth

    def _assert_entry(self, label: str, **kwargs) -> None:  # type: ignore
        """An additional assertion utility to check specific entry fields.

        Args:
            label: the label of the entry.
            kwargs: additional keyword arguments whose contents are checked against the Entry's
                `data contents.
        """
        entry = Database()[label]
        for key, value in kwargs.items():
            assert entry.data.get(key, None) == value

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["setup"],
        [
            [{"git": False}],
            [{"git": True}],
        ],
        indirect=["setup"],
    )
    @pytest.mark.parametrize(
        ["more_args", "entry_kwargs"],
        [
            [[], {}],
            [
                ["-f", "test/debug.py"],
                {"file": [str(RelPath("test/debug.py"))]},
            ],
            [["-l", "dummy_label"], {}],
            [["tag"], {"tags": ["tag"]}],
            [["tag", "tag2"], {"tags": ["tag", "tag2"]}],
        ],
    )
    async def test_command(
        self, setup: Any, more_args: List[str], entry_kwargs: Dict[str, Any]
    ) -> None:
        # pylint: disable=invalid-overridden-method
        """Test the command itself.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            more_args: additional arguments to be passed to the command.
            entry_kwargs: the expected contents of the resulting `Entry`.
        """
        git = setup.get("git", False)

        try:
            label = more_args[more_args.index("-l") + 1]
        except ValueError:
            label = "example_multi_file_entry"
        args = ["-b", EXAMPLE_MULTI_FILE_ENTRY_BIB] + more_args

        await AddCommand(*args).execute()

        assert Database()[label]

        if entry_kwargs or label != "example_multi_file_entry":
            self._assert_entry(label, **entry_kwargs)
        else:
            # only when we don't use extra arguments the files will match
            self._assert(EXAMPLE_MULTI_FILE_ENTRY_YAML)

        if git:
            # assert the git commit message
            # Note: we do not assert the arguments, because they depend on the available parsers
            self.assert_git_commit_message("add", None)

    @pytest.mark.asyncio
    async def test_add_new_entry(self, setup: Any, caplog: pytest.LogCaptureFixture) -> None:
        """Test adding a new plain entry.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            caplog: the built-in pytest fixture.
        """
        await AddCommand("-l", "dummy").execute()
        assert (
            "cobib.commands.add",
            30,
            "No input to parse. Creating new entry 'dummy' manually.",
        ) in caplog.record_tuples

        with open(config.database.file, "r", encoding="utf-8") as file:
            lines = file.readlines()
            dummy_start = lines.index("dummy:\n")
            assert dummy_start > 0
            assert lines[dummy_start - 1] == "---\n"
            assert lines[dummy_start + 1] == "  ENTRYTYPE: article\n"
            assert lines[dummy_start + 2] == "...\n"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("folder", [None, "."])
    @pytest.mark.parametrize("skip_download", [None, True, False])
    @pytest.mark.parametrize("config_overwrite", [True, False])
    async def test_add_with_download(
        self,
        setup: Any,
        folder: Optional[str],
        skip_download: Optional[bool],
        config_overwrite: bool,
        capsys: pytest.CaptureFixture[str],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test adding a new entry with possibly an associated file automatically downloaded.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            folder: the folder for the downloaded file.
            skip_download: argument to `AddCommand`.
            config_overwrite: what to overwrite `config.commands.add.skip_download` with.
            capsys: the built-in pytest fixture.
            caplog: the built-in pytest fixture.
        """
        config.commands.add.skip_download = config_overwrite

        should_download = not config_overwrite
        if skip_download is not None:
            should_download = not skip_download

        path = RelPath(f"{'/tmp' if folder is None else folder}/Cao2018.pdf")
        try:
            # ensure file does not exist yet
            os.remove(path.path)
        except FileNotFoundError:
            pass
        try:
            args = ["-a", "1812.09976"]
            if folder:
                args += ["-p", folder]
            if skip_download is not None:
                args.append(f"--{'skip' if skip_download else 'force'}-download")

            await AddCommand(*args).execute()

            if (
                "cobib.parsers.arxiv",
                logging.ERROR,
                "An Exception occurred while trying to query the arXiv ID: 1812.09976.",
            ) in caplog.record_tuples:
                pytest.skip("The requests API encountered an error. Skipping test.")

            entry = Database()["Cao2018"]
            assert entry.label == "Cao2018"
            assert entry.data["archivePrefix"] == "arXiv"
            assert entry.data["arxivid"].startswith("1812.09976")
            assert "_download" not in entry.data.keys()

            if should_download:
                assert f"Successfully downloaded {path}" in capsys.readouterr().out
                assert os.path.exists(path.path)
            else:
                assert not os.path.exists(path.path)
        finally:
            try:
                os.remove(path.path)
            except FileNotFoundError:
                pass

    @pytest.mark.asyncio
    @pytest.mark.parametrize("deprecated", (True, False))
    @pytest.mark.parametrize(
        ["setup"],
        [
            [{"git": False}],
            [{"git": True}],
        ],
        indirect=["setup"],
    )
    async def test_add_with_update(
        self, setup: Any, deprecated: bool, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test update option of AddCommand.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            deprecated: whether to test the deprecated or new means.
            caplog: the built-in pytest fixture.
        """
        git = setup.get("git", False)
        await AddCommand("-a", "1812.09976", "--skip-download").execute()

        if (
            "cobib.parsers.arxiv",
            logging.ERROR,
            "An Exception occurred while trying to query the arXiv ID: 1812.09976.",
        ) in caplog.record_tuples:
            pytest.skip("The requests API encountered an error. Skipping test.")

        # assert initial state
        entry = Database()["Cao2018"]

        assert entry.data["author"].startswith("Yudong Cao")
        assert entry.data["title"].startswith("Quantum Chemistry in the Age of Quantum Computing")
        assert entry.data["arxivid"].startswith("1812.09976")
        assert entry.data["doi"] == "10.1021/acs.chemrev.8b00803"
        assert entry.data["primaryClass"] == "quant-ph"
        assert entry.data["archivePrefix"] == "arXiv"
        assert entry.data["abstract"] != ""
        assert entry.data["year"] == 2018

        assert "journal" not in entry.data.keys()
        assert "month" not in entry.data.keys()
        assert "number" not in entry.data.keys()
        assert "pages" not in entry.data.keys()
        assert "volume" not in entry.data.keys()

        args = [
            "-d",
            "10.1021/acs.chemrev.8b00803",
            "-l",
            "Cao2018",
            "--skip-download",
        ]
        if deprecated:
            args += ["--update"]
        else:
            args += ["--disambiguation", "update"]
        await AddCommand(*args).execute()

        if (
            "cobib.parsers.doi",
            logging.ERROR,
            "An Exception occurred while trying to query the DOI: 10.1021/acs.chemrev.8b00803.",
        ) in caplog.record_tuples:
            pytest.skip("The requests API encountered an error. Skipping test.")

        if deprecated:
            assert (
                "cobib.commands.add",
                logging.WARNING,
                "The '--update' argument of the 'add' command is deprecated! "
                "Instead you should use '--disambiguation update'.",
            ) in caplog.record_tuples

        # assert final state
        entry = Database()["Cao2018"]

        assert entry.data["author"].startswith("Yudong Cao")
        assert entry.data["title"].startswith("Quantum Chemistry in the Age of Quantum Computing")
        assert entry.data["arxivid"].startswith("1812.09976")
        assert entry.data["primaryClass"] == "quant-ph"
        assert entry.data["archivePrefix"] == "arXiv"
        assert entry.data["abstract"] != ""

        assert entry.data["journal"] == "Chemical Reviews"
        assert entry.data["doi"] == "10.1021/acs.chemrev.8b00803"
        assert entry.data["month"] == "aug"
        assert entry.data["number"] == 19
        assert entry.data["pages"] == "10856--10915"
        assert entry.data["volume"] == 119
        assert entry.data["year"] == 2019

        if git:
            # assert the git commit message
            # Note: we do not assert the arguments, because they depend on the available parsers
            self.assert_git_commit_message("add", None)

    @pytest.mark.asyncio
    async def test_skip_manual_add_if_exists(
        self, setup: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test manual addition is skipped if the label exists already.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            caplog: the built-in pytest fixture.
        """
        await AddCommand("-l", "einstein").execute()
        assert (
            "cobib.commands.add",
            30,
            (
                "You tried to add the 'einstein' entry manually, but it already exists, "
                "please use `cobib edit einstein` instead!"
            ),
        ) in caplog.record_tuples

    @pytest.mark.asyncio
    @pytest.mark.parametrize("deprecated", (True, False))
    async def test_continue_after_skip_exists(
        self, setup: Any, deprecated: bool, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test entry addition continues after skipping over existing entry.

        Regression test against #83

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            deprecated: whether to test the deprecated or new means.
            caplog: the built-in pytest fixture.
        """
        with tempfile.NamedTemporaryFile("w") as file:
            with open(EXAMPLE_DUPLICATE_ENTRY_BIB, "r", encoding="utf-8") as existing:
                file.writelines(existing.readlines())
            file.writelines(["@article{dummy,\nauthor = {Dummy},\n}"])
            file.flush()
            args = ["-b", file.name]
            if deprecated:
                args += ["--skip-existing"]
            else:
                args += ["--disambiguation", "keep"]
            await AddCommand(*args).execute()
        assert (
            "cobib.commands.add",
            20,
            "Skipping addition of the already existing entry 'einstein'.",
        ) in caplog.record_tuples
        assert (
            "cobib.database.database",
            10,
            "Updating entry dummy",
        ) in caplog.record_tuples

        if deprecated:
            assert (
                "cobib.commands.add",
                logging.WARNING,
                "The '--skip-existing' argument of the 'add' command is deprecated! "
                "Instead you should use '--disambiguation keep'.",
            ) in caplog.record_tuples

    @pytest.mark.asyncio
    async def test_warning_missing_label(
        self, setup: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test warning for missing label and any other input.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            caplog: the built-in pytest fixture.
        """
        await AddCommand().execute()
        assert (
            "cobib.commands.add",
            40,
            "Neither an input to parse nor a label for manual creation specified!",
        ) in caplog.record_tuples

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["setup"],
        [
            [{"git": False}],
            [{"git": True}],
        ],
        indirect=["setup"],
    )
    async def test_overwrite_label(self, setup: Any) -> None:
        """Test add command while specifying a label manually.

        Regression test against #4.

        The duplicate entry has been adapted to also assert the elongation of Journal names.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
        """
        config.utils.journal_abbreviations = [("Annalen der Physik", "Ann. Phys.")]
        git = setup.get("git", False)
        # add potentially duplicate entry
        await AddCommand(
            "-b", EXAMPLE_DUPLICATE_ENTRY_BIB, "--label", "duplicate_resolver"
        ).execute()

        assert Database()["duplicate_resolver"]

        self._assert(EXAMPLE_DUPLICATE_ENTRY_YAML)

        if git:
            # assert the git commit message
            self.assert_git_commit_message("add", None)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["setup"],
        [
            [{"git": False}],
            [{"git": True}],
        ],
        indirect=["setup"],
    )
    async def test_configured_label_default(self, setup: Any) -> None:
        """Test add command when a `label_default` is pre-configured.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
        """
        config.database.format.label_default = "{author.split()[1]}{year}"
        git = setup.get("git", False)

        await AddCommand("-b", EXAMPLE_DUPLICATE_ENTRY_BIB).execute()

        assert Database()["Einstein1905"]

        if git:
            # assert the git commit message
            self.assert_git_commit_message("add", None)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["setup", "post_setup", "args"],
        [
            [{"git": False}, {"stdin_list": ["disambiguate"]}, []],
            [{"git": True}, {"stdin_list": ["disambiguate"]}, []],
            [{"git": False}, {}, ["--disambiguation", "disambiguate"]],
            [{"git": True}, {}, ["--disambiguation", "disambiguate"]],
        ],
        indirect=["setup", "post_setup"],
    )
    async def test_disambiguate_label(
        self, setup: Any, post_setup: Any, args: list[str], caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test label disambiguation if the provided one already exists.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            post_setup: an additional setup fixture.
            args: additional arguments for the AddCommand.
            caplog: the built-in pytest fixture.
        """
        git = setup.get("git", False)

        await AddCommand("-b", EXAMPLE_DUPLICATE_ENTRY_BIB, *args).execute()

        assert (
            "cobib.commands.add",
            30,
            "You tried to add a new entry 'einstein' which already exists!",
        ) in caplog.record_tuples
        assert (
            "cobib.commands.add",
            30,
            "The label will be disambiguated based on the configuration option: "
            "config.database.format.label_suffix",
        ) in caplog.record_tuples

        assert Database()["einstein_a"]

        if git:
            # assert the git commit message
            self.assert_git_commit_message("add", None)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["post_setup"],
        [
            [{"stdin_list": ["disambiguate"]}],
        ],
        indirect=["post_setup"],
    )
    async def test_disambiguate_download(
        self,
        setup: Any,
        post_setup: Any,
        capsys: pytest.CaptureFixture[str],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test label disambiguation is propagated to downloaded files.

        This is a regression test against https://gitlab.com/cobib/cobib/-/issues/96.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            post_setup: an additional setup fixture.
            capsys: the built-in pytest fixture.
            caplog: the built-in pytest fixture.
        """
        database = Database()

        for label in ("Cao2018", "Cao2018_a"):
            try:
                path = RelPath(f"/tmp/{label}.pdf")
                try:
                    # ensure file does not exist yet
                    os.remove(path.path)
                except FileNotFoundError:
                    pass

                # by repeatedly calling the same add command, we trigger the label disambiguation
                await AddCommand("-a", "1812.09976").execute()

                if (
                    "cobib.parsers.arxiv",
                    logging.ERROR,
                    "An Exception occurred while trying to query the arXiv ID: 1812.09976.",
                ) in caplog.record_tuples:
                    pytest.skip("The requests API encountered an error. Skipping test.")

                entry = database[label]
                assert entry.data["author"].startswith("Yudong Cao")
                assert entry.data["title"].startswith(
                    "Quantum Chemistry in the Age of Quantum Computing"
                )
                assert entry.data["arxivid"].startswith("1812.09976")
                assert entry.data["doi"] == "10.1021/acs.chemrev.8b00803"
                assert entry.data["primaryClass"] == "quant-ph"
                assert entry.data["archivePrefix"] == "arXiv"
                assert entry.data["abstract"] != ""
                assert entry.data["year"] == 2018
                assert os.path.exists(path.path)

            finally:
                try:
                    os.remove(path.path)
                except FileNotFoundError:
                    pass

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["setup"],
        [
            [{"git": False}],
        ],
        indirect=["setup"],
    )
    # other variants are already covered by test_command
    async def test_cmdline(self, setup: Any, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test the command-line access of the command.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            monkeypatch: the built-in pytest fixture.
        """
        await self.run_module(
            monkeypatch, "main", ["cobib", "add", "-b", EXAMPLE_MULTI_FILE_ENTRY_BIB]
        )
        self._assert(EXAMPLE_MULTI_FILE_ENTRY_YAML)

    @pytest.mark.asyncio
    async def test_event_pre_add_command(self, setup: Any) -> None:
        """Tests the PreAddCommand event."""

        @Event.PreAddCommand.subscribe
        def hook(command: AddCommand) -> None:
            command.largs.label = "dummy"

        assert Event.PreAddCommand.validate()

        await AddCommand("-b", EXAMPLE_DUPLICATE_ENTRY_BIB).execute()

        assert "dummy" in Database().keys()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["post_setup"],
        [
            [{"stdin_list": ["disambiguate"]}],
        ],
        indirect=["post_setup"],
    )
    async def test_event_post_add_command(self, setup: Any, post_setup: Any) -> None:
        """Tests the PostAddCommand event."""

        @Event.PostAddCommand.subscribe
        def hook(command: AddCommand) -> None:
            command.new_entries["dummy"] = command.new_entries.pop("einstein_a")

        assert Event.PostAddCommand.validate()

        await AddCommand("-b", EXAMPLE_DUPLICATE_ENTRY_BIB).execute()

        assert "dummy" in Database().keys()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        [
            "args",
            "msg_string",
        ],
        [
            [
                ["--skip-existing"],
                "The '--skip-existing' argument of the 'add' command is deprecated! "
                "Instead you should use '--disambiguation keep'.",
            ],
            [
                ["--update"],
                "The '--update' argument of the 'add' command is deprecated! "
                "Instead you should use '--disambiguation update'.",
            ],
        ],
    )
    async def test_warn_deprecated_args(
        self, setup: Any, args: list[str], msg_string: str, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test the warning upon usage of deprecated arguments.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            args: arguments for the AddCommand.
            msg_string: the string which the warning message must match.
            caplog: the built-in pytest fixture.
        """
        args = ["-b", EXAMPLE_MULTI_FILE_ENTRY_BIB] + args

        await AddCommand(*args).execute()

        for source, level, msg in caplog.record_tuples:
            if source == "cobib.commands.add" and level == 30:
                if msg == msg_string:
                    break
        else:
            pytest.fail("No Warning logged from AddCommand.")

    @pytest.mark.asyncio
    async def test_hook_datetime_added(self, setup: Any) -> None:
        """Tests the hook to keep track of the time an entry was added.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
        """

        @Event.PostAddCommand.subscribe
        def date_added(command: AddCommand) -> None:
            for entry in command.new_entries.values():
                entry.data["datetime_added"] = str(datetime.now())

        assert Event.PostModifyCommand.validate()

        await AddCommand("-b", EXAMPLE_DUPLICATE_ENTRY_BIB, "-l", "dummy").execute()

        assert "datetime_added" in Database()["dummy"].data
