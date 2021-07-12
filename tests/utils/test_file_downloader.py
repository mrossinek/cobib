"""Tests for coBib's file downloader utility."""

import tempfile
from os import remove
from typing import Any

import pytest
import requests

from cobib.config import config
from cobib.utils.file_downloader import FileDownloader

from .. import get_resource


@pytest.fixture
def setup_remove_content_length(monkeypatch: pytest.MonkeyPatch, enable: bool = True) -> None:
    """Setup method to remove the `content-length` from the response header.

    Args:
        monkeypatch: the built-in pytest fixture.
        enable: whether to enable this fixture.
    """
    if not enable:
        return

    def remove_content_length(*args, **kwargs):  # type: ignore
        """Mock function to remove `content-length` from response."""
        response = requests.request("get", *args, **kwargs)
        response.headers.pop("content-length")
        return response

    monkeypatch.setattr(requests, "get", remove_content_length)


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


def test_download(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test the FileDownloader.download method.

    Args:
        monkeypatch: the built-in pytest fixture.
    """
    with tempfile.TemporaryDirectory() as tmpdirname:
        try:
            # ensure file does not exist yet
            remove(tmpdirname + "/dummy.pdf")
        except FileNotFoundError:
            pass
        # disable the PDF assertion method
        monkeypatch.setattr(FileDownloader, "_assert_pdf", lambda _: True)
        path = FileDownloader().download(
            "https://gitlab.com/mrossinek/cobib/-/raw/master/tests/utils/__init__.py",
            "dummy",
            tmpdirname,
        )
        if path is None:
            pytest.skip("Likely, a requests error occured.")
        with open(get_resource("__init__.py", "utils"), "r") as expected:
            with open(tmpdirname + "/dummy.pdf", "r") as truth:
                assert expected.read() == truth.read()


@pytest.mark.parametrize(
    ["setup_remove_content_length"],
    [
        [{"enable": False}],
        [{"enable": True}],
    ],
    indirect=["setup_remove_content_length"],
)
# pylint: disable=unused-argument,redefined-outer-name
def test_skip_download_if_no_pdf(setup_remove_content_length: Any) -> None:
    """Test that download is skipped when file is not a PDF.

    Args:
        setup_remove_content_length: a custom fixture.
    """
    with tempfile.TemporaryDirectory() as tmpdirname:
        assert (
            FileDownloader().download(
                "https://gitlab.com/mrossinek/cobib/-/raw/master/tests/utils/__init__.py",
                "dummy",
                tmpdirname,
            )
            is None
        )


def test_skip_download_if_exists(caplog: pytest.LogCaptureFixture) -> None:
    """Test that download is skipped when file already exists.

    Args:
        caplog: the built-in pytest fixture.
    """
    with tempfile.TemporaryDirectory() as tmpdirname:
        open(tmpdirname + "/dummy.pdf", "w").close()  # pylint: disable=consider-using-with
        FileDownloader().download(
            "https://gitlab.com/mrossinek/cobib/-/raw/master/tests/utils/__init__.py",
            "dummy",
            tmpdirname,
        )
        for mod, lvl, msg in caplog.record_tuples:
            if (
                mod == "cobib.utils.file_downloader"
                and lvl == 30
                and "already exists! Using that rather than downloading." in msg
            ):
                break
        else:
            assert False, "Download not aborted."


@pytest.mark.parametrize(
    ["setup_remove_content_length"],
    [
        [{"enable": False}],
        [{"enable": True}],
    ],
    indirect=["setup_remove_content_length"],
)
# pylint: disable=unused-argument,redefined-outer-name
def test_download_with_url_map(setup_remove_content_length: Any) -> None:
    """Test the `config.utils.file_downloader.url_map` usage.

    We use a Quantum Journal article because they are open-source and, thus, do not require a Proxy
    to get access to.

    Args:
        setup_remove_content_length: a custom fixture.
    """
    try:
        config.load(get_resource("debug.py"))
        with tempfile.TemporaryDirectory() as tmpdirname:
            try:
                # ensure file does not exist yet
                remove(tmpdirname + "/dummy.pdf")
            except FileNotFoundError:
                pass
            path = FileDownloader().download(
                "https://quantum-journal.org/papers/q-2021-06-17-479/",
                "dummy",
                tmpdirname,
            )
            if path is None:
                pytest.skip("Likely, a requests error occured.")
            assert path.path.exists()
            with open(path.path, "rb") as file:
                assert file.read().startswith(bytes("%PDF", "utf-8"))
    finally:
        config.defaults()


def test_gracefully_fail_download(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test gracefully failing downloads.

    Args:
        monkeypatch: the built-in pytest fixture.
    """

    def raise_exception(*args, **kwargs):  # type: ignore
        """Mock function to raise an Exception."""
        raise requests.exceptions.RequestException()

    monkeypatch.setattr(requests, "get", raise_exception)

    with tempfile.TemporaryDirectory() as tmpdirname:
        assert (
            FileDownloader().download(
                "https://quantum-journal.org/papers/q-2021-06-17-479/",
                "dummy",
                tmpdirname,
            )
            is None
        )
