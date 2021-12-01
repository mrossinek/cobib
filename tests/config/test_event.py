"""Tests for coBib's Event validation."""

from typing import Any, Generator

import pytest

from cobib.config import Event, config

from .. import get_resource


@pytest.fixture(autouse=True)
def setup() -> Generator[Any, None, None]:
    """Setup debugging configuration.

    Yields:
        Access to the local fixture variables.
    """
    config.load(get_resource("debug.py"))
    yield setup
    config.clear()
    config.defaults()


@pytest.mark.parametrize(
    "event",
    [
        Event.PreAddCommand,
        Event.PostAddCommand,
        Event.PreDeleteCommand,
        Event.PostDeleteCommand,
        Event.PreEditCommand,
        Event.PostEditCommand,
        Event.PreExportCommand,
        Event.PostExportCommand,
        Event.PreImportCommand,
        Event.PostImportCommand,
        Event.PreInitCommand,
        Event.PostInitCommand,
        Event.PreListCommand,
        Event.PostListCommand,
        Event.PreModifyCommand,
        Event.PostModifyCommand,
        Event.PreOpenCommand,
        Event.PostOpenCommand,
        Event.PreRedoCommand,
        Event.PostRedoCommand,
        Event.PreSearchCommand,
        Event.PostSearchCommand,
        Event.PreShowCommand,
        Event.PostShowCommand,
        Event.PreUndoCommand,
        Event.PostUndoCommand,
        Event.PreBibtexParse,
        Event.PostBibtexParse,
        Event.PreBibtexDump,
        Event.PostBibtexDump,
        Event.PreYAMLParse,
        Event.PostYAMLParse,
        Event.PreYAMLDump,
        Event.PostYAMLDump,
        Event.PreArxivParse,
        Event.PostArxivParse,
        Event.PreDOIParse,
        Event.PostDOIParse,
        Event.PreISBNParse,
        Event.PostISBNParse,
        Event.PreURLParse,
        Event.PostURLParse,
        Event.PreZoteroImport,
        Event.PostZoteroImport,
        Event.PreFileDownload,
        Event.PostFileDownload,
        Event.PreGitCommit,
        Event.PostGitCommit,
    ],
)
def test_config_validation(event: Event) -> None:
    """Test the config validation of faulty hook subscription functions.

    Args:
        event: the coBib Event which to subscribe to.
    """

    @event.subscribe
    def faulty_hook() -> None:
        return

    with pytest.raises(RuntimeError) as exc_info:
        config.validate()

    assert (
        str(exc_info.value)
        == f"config.events.Event.{event.name} did not pass its validation check."
    )
