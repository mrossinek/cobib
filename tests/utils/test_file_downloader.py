"""Tests for coBib's file downloader utility."""

import tempfile

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
        with open(get_resource("__init__.py", "utils"), "r") as expected:
            with open(tmpdirname + "/dummy.pdf", "r") as truth:
                assert expected.read() == truth.read()
