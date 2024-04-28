"""Tests for coBib's file downloader utility."""

from __future__ import annotations

import tempfile
from os import remove
from typing import Any, Dict, Optional, Tuple

import pytest
import requests

from cobib.config import Event, config
from cobib.utils.file_downloader import FileDownloader
from cobib.utils.rel_path import RelPath

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

    def remove_content_length(*args, **kwargs):  # type: ignore[no-untyped-def]
        """Mock function to remove `content-length` from response."""
        response = requests.request("get", *args, timeout=kwargs.pop("timeout", 30), **kwargs)
        response.headers.pop("content-length")
        return response

    monkeypatch.setattr(requests, "get", remove_content_length)


def test_downloader_singleton() -> None:
    """Test the FileDownloader is a Singleton."""
    f_d = FileDownloader()
    f_d2 = FileDownloader()
    assert f_d is f_d2


@pytest.mark.asyncio
async def test_download(monkeypatch: pytest.MonkeyPatch) -> None:
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
        monkeypatch.setattr(FileDownloader, "_assert_pdf", lambda *_: True)
        path = await FileDownloader().download(
            "https://gitlab.com/cobib/cobib/-/raw/master/tests/utils/__init__.py",
            "dummy",
            tmpdirname,
        )
        if path is None:
            pytest.skip("Likely, a requests error occurred.")
        with open(get_resource("__init__.py", "utils"), "r", encoding="utf-8") as expected:
            with open(tmpdirname + "/dummy.pdf", "r", encoding="utf-8") as truth:
                assert expected.read() == truth.read()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["setup_remove_content_length"],
    [
        [{"enable": False}],
        [{"enable": True}],
    ],
    indirect=["setup_remove_content_length"],
)
async def test_skip_download_if_no_pdf(setup_remove_content_length: Any) -> None:
    """Test that download is skipped when file is not a PDF.

    Args:
        setup_remove_content_length: a custom fixture.
    """
    with tempfile.TemporaryDirectory() as tmpdirname:
        assert (
            await FileDownloader().download(
                "https://gitlab.com/cobib/cobib/-/raw/master/tests/utils/__init__.py",
                "dummy",
                tmpdirname,
            )
            is None
        )


@pytest.mark.asyncio
@pytest.mark.parametrize("overwrite", [False, True])
async def test_skip_download_if_exists(caplog: pytest.LogCaptureFixture, overwrite: bool) -> None:
    """Test that download is skipped when file already exists.

    Args:
        caplog: the built-in pytest fixture.
        overwrite: whether or not to overwrite the existing file.
    """
    with tempfile.TemporaryDirectory() as tmpdirname:
        open(tmpdirname + "/dummy.pdf", "w", encoding="utf-8").close()
        await FileDownloader().download(
            "https://gitlab.com/cobib/cobib/-/raw/master/tests/utils/__init__.py",
            "dummy",
            folder=tmpdirname,
            overwrite=overwrite,
        )
        for mod, lvl, msg in caplog.record_tuples:
            if (
                mod == "cobib.utils.file_downloader"
                and lvl == 30
                and "already exists! Using that rather than downloading." in msg
            ):
                break
        else:
            assert overwrite, "This statement should only be reached when overwrite is enabled!"
            return
        assert not overwrite, "This statement should only be reached when overwrite is disabled!"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["setup_remove_content_length"],
    [
        [{"enable": False}],
        [{"enable": True}],
    ],
    indirect=["setup_remove_content_length"],
)
async def test_download_with_url_map(setup_remove_content_length: Any) -> None:
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
            path = await FileDownloader().download(
                "https://quantum-journal.org/papers/q-2021-06-17-479/",
                "dummy",
                tmpdirname,
            )
            if path is None:
                pytest.skip("Likely, a requests error occurred.")
            assert path.path.exists()
            with open(path.path, "rb") as file:
                assert file.read().startswith(bytes("%PDF", "utf-8"))
    finally:
        config.defaults()


@pytest.mark.asyncio
async def test_gracefully_fail_download(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test gracefully failing downloads.

    Args:
        monkeypatch: the built-in pytest fixture.
    """

    def raise_exception(*args, **kwargs):  # type: ignore[no-untyped-def]
        """Mock function to raise an Exception."""
        raise requests.exceptions.RequestException()

    monkeypatch.setattr(requests, "get", raise_exception)

    with tempfile.TemporaryDirectory() as tmpdirname:
        assert (
            await FileDownloader().download(
                "https://quantum-journal.org/papers/q-2021-06-17-479/",
                "dummy",
                tmpdirname,
            )
            is None
        )


@pytest.mark.asyncio
async def test_event_pre_download(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test the PreFileDownload event.

    Args:
        monkeypatch: the built-in pytest fixture.
    """

    @Event.PreFileDownload.subscribe
    def hook(
        url: str, label: str, folder: Optional[str], headers: Optional[Dict[str, str]]
    ) -> Optional[Tuple[str, str, Optional[str], Optional[Dict[str, str]]]]:
        label = "test"
        return (url, label, folder, headers)

    assert Event.PreFileDownload.validate()

    with tempfile.TemporaryDirectory() as tmpdirname:
        try:
            # ensure file does not exist yet
            remove(tmpdirname + "/test.pdf")
        except FileNotFoundError:
            pass
        # disable the PDF assertion method
        monkeypatch.setattr(FileDownloader, "_assert_pdf", lambda *_: True)
        path = await FileDownloader().download(
            "https://gitlab.com/cobib/cobib/-/raw/master/tests/utils/__init__.py",
            "dummy",
            tmpdirname,
        )
        if path is None:
            pytest.skip("Likely, a requests error occurred.")
        with open(get_resource("__init__.py", "utils"), "r", encoding="utf-8") as expected:
            with open(tmpdirname + "/test.pdf", "r", encoding="utf-8") as truth:
                assert expected.read() == truth.read()


@pytest.mark.asyncio
async def test_event_post_download(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test the PostFileDownload event.

    Args:
        monkeypatch: the built-in pytest fixture.
    """

    @Event.PostFileDownload.subscribe
    def hook(path: RelPath) -> Optional[RelPath]:  # type: ignore[return]
        path.path.rename(path.path.parent / "test.pdf")

    assert Event.PostFileDownload.validate()

    with tempfile.TemporaryDirectory() as tmpdirname:
        try:
            # ensure file does not exist yet
            remove(tmpdirname + "/test.pdf")
        except FileNotFoundError:
            pass
        # disable the PDF assertion method
        monkeypatch.setattr(FileDownloader, "_assert_pdf", lambda *_: True)
        path = await FileDownloader().download(
            "https://gitlab.com/cobib/cobib/-/raw/master/tests/utils/__init__.py",
            "dummy",
            tmpdirname,
        )
        if path is None:
            pytest.skip("Likely, a requests error occurred.")
        with open(get_resource("__init__.py", "utils"), "r", encoding="utf-8") as expected:
            with open(tmpdirname + "/test.pdf", "r", encoding="utf-8") as truth:
                assert expected.read() == truth.read()
