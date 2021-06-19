"""Tests for coBib's file downloader utility."""

import tempfile
from shutil import rmtree

import pytest

from cobib.utils.file_downloader import FileDownloader

from .. import get_resource


def test_downloader_singleton() -> None:
    """Test the FileDownloader is a Singleton."""
    f_d = FileDownloader()
    f_d2 = FileDownloader()
    assert f_d is f_d2


def test_set_logger() -> None:
    """Test the FileDownloader.set_logger method."""
    f_d = FileDownloader()
    logger = lambda text: f"test: {text}"
    f_d.set_logger(logger)  # type: ignore
    # pylint: disable=protected-access
    assert FileDownloader._logger("") == "test: "  # type: ignore


def test_download() -> None:
    """Test the FileDownloader.download method."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        FileDownloader().download(
            "https://gitlab.com/mrossinek/cobib/-/raw/master/tests/utils/__init__.py",
            "dummy",
            tmpdirname,
        )
        try:
            with open(get_resource("__init__.py", "utils"), "r") as expected:
                with open(tmpdirname + "/dummy.pdf", "r") as truth:
                    assert expected.read() == truth.read()
        finally:
            rmtree(tmpdirname)


def test_skip_download_if_exists(caplog: pytest.LogCaptureFixture) -> None:
    """Test that download is skipped when file already exists.

    Args:
        caplog: the built-in pytest fixture.
    """
    with tempfile.TemporaryDirectory() as tmpdirname:
        open(tmpdirname + "/dummy.pdf", "w").close()
        FileDownloader().download(
            "https://gitlab.com/mrossinek/cobib/-/raw/master/tests/utils/__init__.py",
            "dummy",
            tmpdirname,
        )
        try:
            for mod, lvl, msg in caplog.record_tuples:
                if (
                    mod == "cobib.utils.file_downloader"
                    and lvl == 30
                    and "already exists! Using that rather than downloading." in msg
                ):
                    break
            else:
                assert False, "Download not aborted."
        finally:
            rmtree(tmpdirname)
