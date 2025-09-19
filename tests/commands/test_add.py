"""Tests for coBib's AddCommand."""

from __future__ import annotations

import logging
import tempfile
from collections.abc import Generator
from datetime import datetime
from itertools import zip_longest
from typing import TYPE_CHECKING, Any

import pytest
from typing_extensions import override

from cobib.commands import AddCommand
from cobib.config import Event, config
from cobib.database import Author, Database
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
    def get_command(self) -> type[cobib.commands.base_command.Command]:
        return AddCommand

    @pytest.fixture
    def post_setup(
        self, monkeypatch: pytest.MonkeyPatch, request: _pytest.fixtures.SubRequest
    ) -> Generator[dict[str, Any], None, None]:
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

    def _assert_entry(self, label: str, **kwargs) -> None:  # type: ignore[no-untyped-def]
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
        self, setup: Any, more_args: list[str], entry_kwargs: dict[str, Any]
    ) -> None:
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
        args = ["-b", EXAMPLE_MULTI_FILE_ENTRY_BIB, *more_args]

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
        folder: str | None,
        skip_download: bool | None,
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

        path = RelPath(f"{'/tmp' if folder is None else folder}/Bravyi2017.pdf")
        path.path.unlink(missing_ok=True)
        try:
            args = ["-a", "1701.08213"]
            if folder:
                args += ["-p", folder]
            if skip_download is not None:
                args.append(f"--{'skip' if skip_download else 'force'}-download")

            await AddCommand(*args).execute()

            if (
                "cobib.parsers.arxiv",
                logging.ERROR,
                "An Exception occurred while trying to query the arXiv ID: 1701.08213.",
            ) in caplog.record_tuples:
                pytest.skip("The requests API encountered an error. Skipping test.")

            entry = Database()["Bravyi2017"]
            assert entry.label == "Bravyi2017"
            assert entry.data["archivePrefix"] == "arXiv"
            assert entry.data["arxivid"].startswith("1701.08213")
            assert "_download" not in entry.data.keys()

            if should_download:
                assert f"Successfully downloaded {path}" in capsys.readouterr().out
                assert path.path.exists()
            else:
                assert not path.path.exists()
        finally:
            path.path.unlink(missing_ok=True)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["setup"],
        [
            [{"git": False}],
            [{"git": True}],
        ],
        indirect=["setup"],
    )
    async def test_add_with_update(self, setup: Any, caplog: pytest.LogCaptureFixture) -> None:
        """Test update option of AddCommand.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            caplog: the built-in pytest fixture.
        """
        git = setup.get("git", False)
        await AddCommand("-a", "2302.03052", "--skip-download").execute()

        if (
            "cobib.parsers.arxiv",
            logging.ERROR,
            "An Exception occurred while trying to query the arXiv ID: 2302.03052.",
        ) in caplog.record_tuples:
            pytest.skip("The requests API encountered an error. Skipping test.")

        # assert initial state
        entry = Database()["Rossmannek2023"]

        assert entry.data["author"][0].first == "Max"
        assert entry.data["author"][0].last == "Rossmannek"
        assert entry.data["title"].startswith(
            "Quantum Embedding Method for the Simulation of Strongly Correlated Systems on Quantum "
            "Computers"
        )
        assert entry.data["arxivid"].startswith("2302.03052")
        assert entry.data["doi"] == "10.1021/acs.jpclett.3c00330"
        assert entry.data["primaryClass"] == "physics.chem-ph"
        assert entry.data["archivePrefix"] == "arXiv"
        assert entry.data["abstract"] != ""
        assert entry.data["year"] == 2023

        assert "journal" not in entry.data.keys()
        assert "month" not in entry.data.keys()
        assert "number" not in entry.data.keys()
        assert "pages" not in entry.data.keys()
        assert "volume" not in entry.data.keys()

        args = [
            "-d",
            "10.1021/acs.jpclett.3c00330",
            "-l",
            "Rossmannek2023",
            "--skip-download",
        ]
        args += ["--disambiguation", "update"]
        await AddCommand(*args).execute()

        if (
            "cobib.parsers.doi",
            logging.ERROR,
            "An Exception occurred while trying to query the DOI: 10.1021/acs.jpclett.3c00330.",
        ) in caplog.record_tuples:
            pytest.skip("The requests API encountered an error. Skipping test.")

        # assert final state
        entry = Database()["Rossmannek2023"]

        assert entry.data["author"][0].first == "Max"
        assert entry.data["author"][0].last == "Rossmannek"
        assert entry.data["title"].startswith(
            "Quantum Embedding Method for the Simulation of Strongly Correlated Systems on Quantum "
            "Computers"
        )
        assert entry.data["arxivid"].startswith("2302.03052")
        assert entry.data["primaryClass"] == "physics.chem-ph"
        assert entry.data["archivePrefix"] == "arXiv"
        assert entry.data["abstract"] != ""

        assert entry.data["issn"] == "1948-7185"
        assert entry.data["journal"] == "The Journal of Physical Chemistry Letters"
        assert entry.data["doi"] == "10.1021/acs.jpclett.3c00330"
        assert entry.data["month"] == "apr"
        assert entry.data["number"] == 14
        assert entry.data["pages"] == "3491–3497"  # noqa: RUF001
        assert entry.data["volume"] == 14
        assert entry.data["year"] == 2023

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
    async def test_continue_after_skip_exists(
        self, setup: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test entry addition continues after skipping over existing entry.

        Regression test against #83

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            caplog: the built-in pytest fixture.
        """
        with tempfile.NamedTemporaryFile("w") as file:
            with open(EXAMPLE_DUPLICATE_ENTRY_BIB, "r", encoding="utf-8") as existing:
                file.writelines(existing.readlines())
            file.writelines(["@article{dummy,\nauthor = {Dummy},\n}"])
            file.flush()
            args = ["-b", file.name]
            args += ["--disambiguation", "keep"]
            await AddCommand(*args).execute()
        assert (
            "cobib.commands.add",
            20,
            "Keeping the already existing entry 'einstein'.",
        ) in caplog.record_tuples
        assert (
            "cobib.database.database",
            10,
            "Updating entry dummy",
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
        config.database.format.label_default = "{author[0].last}{year}"
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
        ["setup", "post_setup"],
        [
            [
                {
                    "database_filename": "disambiguation_database.yaml",
                    "database_location": "database",
                },
                {"stdin_list": ["replace"]},
            ],
        ],
        indirect=["setup", "post_setup"],
    )
    async def test_disambiguate_replace(
        self, setup: Any, post_setup: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test the `replace` prompt of the interactive label disambiguation.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            post_setup: an additional setup fixture.
            caplog: the built-in pytest fixture.
        """
        disambiguation_entry = get_resource("disambiguation_entry.yaml", "commands")
        await AddCommand("-y", disambiguation_entry).execute()

        bib = Database()
        entry = bib["Author2020"]
        assert entry.data["title"] == "Some other entry"
        assert entry.data["author"] == [Author("Some other", "Author")]

        assert (
            "cobib.commands.add",
            20,
            "Overwriting the already existing entry 'Author2020' with the new data.",
        ) in caplog.record_tuples

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["setup", "post_setup"],
        [
            [
                {
                    "database_filename": "disambiguation_database.yaml",
                    "database_location": "database",
                },
                {"stdin_list": ["keep", "keep"]},
            ],
        ],
        indirect=["setup", "post_setup"],
    )
    async def test_disambiguate_keep(
        self, setup: Any, post_setup: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test the `keep` prompt of the interactive label disambiguation.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            post_setup: an additional setup fixture.
            caplog: the built-in pytest fixture.
        """
        bib = Database()
        author_2020 = bib["Author2020"]
        author_2020_a = bib["Author2020_a"]

        disambiguation_entry = get_resource("disambiguation_entry.yaml", "commands")
        await AddCommand("-y", disambiguation_entry).execute()

        assert bib["Author2020"] == author_2020
        assert bib["Author2020_a"] == author_2020_a
        entry = bib["Author2020_b"]
        assert entry.data["title"] == "Some other entry"
        assert entry.data["author"] == [Author("Some other", "Author")]

        assert (
            "cobib.commands.add",
            20,
            "Keeping the already existing entry 'Author2020'.",
        ) in caplog.record_tuples
        assert (
            "cobib.commands.add",
            20,
            "Keeping the already existing entry 'Author2020_a'.",
        ) in caplog.record_tuples

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["setup", "post_setup"],
        [
            [
                {
                    "database_filename": "disambiguation_database.yaml",
                    "database_location": "database",
                },
                {"stdin_list": ["cancel"]},
            ],
        ],
        indirect=["setup", "post_setup"],
    )
    async def test_disambiguate_cancel(
        self, setup: Any, post_setup: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test the `cancel` prompt of the interactive label disambiguation.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            post_setup: an additional setup fixture.
            caplog: the built-in pytest fixture.
        """
        bib = Database()
        original_entry = bib["Author2020"]

        disambiguation_entry = get_resource("disambiguation_entry.yaml", "commands")
        await AddCommand("-y", disambiguation_entry).execute()

        assert bib["Author2020"] == original_entry

        assert (
            "cobib.commands.add",
            30,
            "Cancelling the addition of the new entry 'Author2020'.",
        ) in caplog.record_tuples

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["setup", "post_setup"],
        [
            [
                {
                    "database_filename": "disambiguation_database.yaml",
                    "database_location": "database",
                },
                {"stdin_list": ["help", "cancel"]},
            ],
        ],
        indirect=["setup", "post_setup"],
    )
    async def test_disambiguate_help(
        self,
        setup: Any,
        post_setup: Any,
        caplog: pytest.LogCaptureFixture,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test the `help` prompt of the interactive label disambiguation.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            post_setup: an additional setup fixture.
            caplog: the built-in pytest fixture.
            capsys: the built-in pytest fixture.
        """
        bib = Database()
        original_entry = bib["Author2020"]

        disambiguation_entry = get_resource("disambiguation_entry.yaml", "commands")
        await AddCommand("-y", disambiguation_entry).execute()

        assert bib["Author2020"] == original_entry

        assert (
            "cobib.commands.add",
            10,
            "User requested help.",
        ) in caplog.record_tuples

        assert "These are your options:" in capsys.readouterr().out

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["setup", "post_setup"],
        [
            [
                {
                    "database_filename": "disambiguation_database.yaml",
                    "database_location": "database",
                },
                {"stdin_list": ["cancel"]},
            ],
        ],
        indirect=["setup", "post_setup"],
    )
    async def test_disambiguate_warn_indirect(
        self, setup: Any, post_setup: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test the warning about indirectly related labels.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            post_setup: an additional setup fixture.
            caplog: the built-in pytest fixture.
        """
        disambiguation_entry = get_resource("disambiguation_entry.yaml", "commands")
        await AddCommand("-y", disambiguation_entry, "--label", "Author2020_a").execute()

        assert (
            "cobib.commands.add",
            30,
            (
                "Found some indirectly related entries to 'Author2020_a': {'Author2020_1'}.\n"
                "You can use the review command to inspect these like so:\n"
                "cobib review -- ++label Author2020"
            ),
        ) in caplog.record_tuples

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

        for label in ("Bravyi2017", "Bravyi2017_a"):
            try:
                path = RelPath(f"/tmp/{label}.pdf")
                # ensure file does not exist yet
                path.path.unlink(missing_ok=True)

                # by repeatedly calling the same add command, we trigger the label disambiguation
                await AddCommand("-a", "1701.08213").execute()

                if (
                    "cobib.parsers.arxiv",
                    logging.ERROR,
                    "An Exception occurred while trying to query the arXiv ID: 1701.08213.",
                ) in caplog.record_tuples:
                    pytest.skip("The requests API encountered an error. Skipping test.")

                entry = database[label]
                assert entry.data["author"][0].first == "Sergey"
                assert entry.data["author"][0].last == "Bravyi"
                assert entry.data["title"].startswith(
                    "Tapering off qubits to simulate fermionic Hamiltonians"
                )
                assert entry.data["arxivid"].startswith("1701.08213")
                assert entry.data["primaryClass"] == "quant-ph"
                assert entry.data["archivePrefix"] == "arXiv"
                assert entry.data["abstract"] != ""
                assert entry.data["year"] == 2017
                assert path.path.exists()

            finally:
                path.path.unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_disambiguate_identical(
        self, setup: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test handling of an identical entry being added.

        Args:
            setup: the `tests.commands.command_test.CommandTest.setup` fixture.
            caplog: the built-in pytest fixture.
        """
        cmd = AddCommand("--disambiguation", "keep", "-y", EXAMPLE_LITERATURE)
        await cmd.execute()

        assert len(cmd.new_entries) == 0

        assert (
            "cobib.database.database",
            35,
            (
                "Even though the label 'einstein' already exists in the runtime database, the "
                "entry is identical and, thus, no further disambiguation is necessary."
            ),
        ) in caplog.record_tuples

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
