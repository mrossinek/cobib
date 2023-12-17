"""coBib's file downloader utility."""

from __future__ import annotations

import asyncio
import logging
import re
import tempfile
from pathlib import Path

import requests
from rich.progress import DownloadColumn, SpinnerColumn, TimeElapsedColumn
from rich.progress import Progress as RichProgress

from cobib.config import Event, config

from .progress import Progress
from .rel_path import RelPath

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


class FileDownloader:
    """The file downloader singleton.

    This utility centralizes the downloading of associated files.
    """

    _instance: FileDownloader | None = None
    """The singleton instance of this class."""

    def __new__(cls) -> FileDownloader:
        """Singleton constructor.

        This method gets called when accessing `FileDownloader` and enforces the singleton pattern
        implemented by this class.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    _PDF_MARKER = bytes("%PDF", "utf-8")
    """A marker which the downloaded file's beginning is checked against, to determine that it is
    indeed a PDF file."""

    @staticmethod
    def _assert_pdf(content: bytes) -> bool:
        """Asserts that the `content` starts with the `_PDF_MARKER`.

        Args:
            content: the string of bytes to check.

        Returns:
            Whether the `content` matches.
        """
        if not content.startswith(FileDownloader._PDF_MARKER):
            LOGGER.warning("The URL did not provide a PDF file. Aborting download!")
            return False
        return True

    @staticmethod
    def _unlink(path: RelPath) -> None:
        """Remove a file and ignore any error.

        Args:
            path: the file to remove.
        """
        path.path.unlink(missing_ok=True)

    @staticmethod
    async def download(
        url: str,
        label: str,
        folder: str | None = None,
        overwrite: bool = False,
        headers: dict[str, str] | None = None,
    ) -> RelPath | None:
        """Downloads a file.

        The path of the downloaded file is `folder/label.pdf`. The path can be configured via
        `cobib.config.config.FileDownloaderConfig.default_location`.

        Args:
            url: the link to the file to be downloaded.
            label: the name of the entry.
            folder: an optional folder where the downloaded file will be stored.
            overwrite: whether or not to overwrite an existing file.
            headers: optional headers for the download `GET` request.

        Returns:
            The `RelPath` to the downloaded file. If downloading was not successful, `None` is
            returned.
        """
        if folder is None:
            folder = config.utils.file_downloader.default_location

        hook_result = Event.PreFileDownload.fire(url, label, folder, headers)
        if hook_result is not None:
            url, label, folder, headers = hook_result

        path = RelPath(Path(f"{folder}/{label}").with_suffix(".pdf"))

        backup = None
        if path.path.exists():
            if not overwrite:
                LOGGER.warning(
                    "A file at '%s' already exists! Using that rather than downloading.", path
                )
                return path
            backup = FileDownloader._backup_file(path)

        url = FileDownloader._map_url(url)

        with open(path.path, "wb") as file:
            LOGGER.info("Downloading %s to %s", url, path)

            try:
                response = requests.get(url, timeout=10, stream=True, headers=headers)
                total_length = response.headers.get("content-length", None)
                total_length = int(total_length) if total_length is not None else None
            except requests.exceptions.RequestException as err:
                msg = f"An Exception occurred while downloading the file located at {url}"
                LOGGER.warning(msg)
                LOGGER.error(err)
                FileDownloader._recover(path, backup)
                return None

            progress_bar = Progress.initialize(
                SpinnerColumn(),
                *RichProgress.get_default_columns(),
                TimeElapsedColumn(),
                DownloadColumn(),
            )
            optional_awaitable = progress_bar.start()  # type: ignore[func-returns-value]
            if optional_awaitable is not None:
                await optional_awaitable

            task = progress_bar.add_task("Downloading...", total=total_length)

            accumulated_length = 0

            if total_length is None:
                if not FileDownloader._assert_pdf(response.content):
                    FileDownloader._recover(path, backup)
                    progress_bar.stop()
                    return None
                file.write(response.content)
            else:
                for data in response.iter_content(chunk_size=4096):
                    if accumulated_length == 0 and not FileDownloader._assert_pdf(data):
                        FileDownloader._recover(path, backup)
                        progress_bar.stop()
                        return None
                    accumulated_length += len(data)
                    progress_bar.advance(task, len(data))
                    await asyncio.sleep(0)
                    file.write(data)

            progress_bar.stop()

            msg = f"Successfully downloaded {path}"
            print(msg)
            LOGGER.info(msg)

            path = Event.PostFileDownload.fire(path) or path

            return path

    @staticmethod
    def _map_url(url: str) -> str:
        """Maps a URL according to `cobib.config.config.FileDownloaderConfig.url_map`.

        Args:
            url: the URL to be mapped.

        Returns:
            The mapped URL.
        """
        for pattern_url, repl_url in config.utils.file_downloader.url_map.items():
            if re.match(pattern_url, url):
                new_url: str = re.sub(pattern_url, repl_url, url)
                LOGGER.info(
                    "Matched the file's URL to your pattern URL %s and replaced it to become %s",
                    pattern_url,
                    new_url,
                )
                return new_url
        return url

    @staticmethod
    def _backup_file(path: RelPath) -> tempfile._TemporaryFileWrapper[bytes]:
        """Create a backup of an existing file.

        Args:
            path: the path to the file to be backed up.

        Returns:
            The temporary backup file.
        """
        # we make a copy of the existing file in case downloading a new one fails
        backup = tempfile.NamedTemporaryFile(delete=False)
        backup.write(path.path.read_bytes())
        backup.seek(0)
        return backup

    @staticmethod
    def _recover(path: RelPath, backup: tempfile._TemporaryFileWrapper[bytes] | None) -> None:
        """Recovers from a backup file.

        If not `backup` exists, the file location which was supposed to be recovered is properly
        removed.

        Args:
            path: the path to the file to be recovered.
            backup: the temporary backup file.
        """
        FileDownloader._unlink(path)
        if backup is not None:
            path.path.write_bytes(backup.read())
            backup.close()
            Path(backup.name).unlink()
