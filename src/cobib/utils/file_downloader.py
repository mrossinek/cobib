"""coBib's file downloader utility."""

from __future__ import annotations

import logging
import re
import sys
import tempfile
from typing import Callable, Optional

import requests

from cobib.config import Event, config

from .rel_path import RelPath

LOGGER = logging.getLogger(__name__)


class FileDownloader:
    """The file downloader singleton.

    This utility centralizes the downloading of associated files. It implements the singleton
    pattern to allow simple log method replacement (via `set_logger`).
    """

    _instance: Optional[FileDownloader] = None
    """The singleton instance of this class."""

    _logger: Callable[[str], None] = lambda text: print(text, end="", flush=True, file=sys.stdout)
    """The logging method used to display the downloading progress bar."""

    def __new__(cls) -> FileDownloader:
        """Singleton constructor.

        This method gets called when accessing `FileDownloader` and enforces the singleton pattern
        implemented by this class.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @staticmethod
    def set_logger(log_method: Callable[[str], None]) -> None:
        """Sets the class-wide logging method (see also `FileDownloader._logger`).

        This method is used to display the progress bar of the file downloading.

        Args:
            log_method: the logging method.
        """
        FileDownloader._logger = log_method

    # bytes pretty-printing
    _UNITS_MAPPING = [
        (1 << 50, " PB"),
        (1 << 40, " TB"),
        (1 << 30, " GB"),
        (1 << 20, " MB"),
        (1 << 10, " KB"),
        (1, " B"),
    ]
    """Maps byte sizes to units."""

    @staticmethod
    def _size(bytes_: int) -> str:
        """Human-readable file size.

        Args:
            bytes_: the size in bytes.

        Returns:
            The size formatted for easy human readability.

        Reference:
            https://stackoverflow.com/a/12912296
        """
        for factor, suffix in FileDownloader._UNITS_MAPPING:
            if bytes_ >= factor:
                break
        amount = int(bytes_ / factor)
        return str(amount) + suffix

    _PDF_MARKER = bytes("%PDF", "utf-8")
    """A marker which the downloaded file's beginning is checked against, to determine that it is
    indeed a PDF file."""

    @staticmethod
    def _assert_pdf(content: bytes) -> bool:
        """Asserts that the `content` starts with the `_PDF_MARKER`.

        Args:
            content: the string of bytes to check.

        Returns:
            Whether the`content` matches.
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
        try:
            # TODO: once Python 3.7 is dropped, leverage `missing_ok` argument
            path.path.unlink()
        except FileNotFoundError:
            pass

    def download(
        self, url: str, label: str, folder: Optional[str] = None, overwrite: bool = False
    ) -> Optional[RelPath]:
        """Downloads a file.

        The path of the downloaded file is `folder/label.pdf`. The path can be configured via
        `cobib.config.commands.add.download_location`.

        Args:
            url: the link to the file to be downloaded.
            label: the name of the entry.
            folder: an optional folder where the downloaded file will be stored.
            overwrite: whether or not to overwrite an existing file.

        Returns:
            The `RelPath` to the downloaded file. If downloading was not successful, `None` is
            returned.
        """
        if folder is None:
            folder = config.utils.file_downloader.default_location

        hook_result = Event.PreFileDownload.fire(url, label, folder)
        if hook_result is not None:
            url, label, folder = hook_result

        path = RelPath(f"{folder}/{label}.pdf")

        backup = None
        if path.path.exists():
            if not overwrite:
                LOGGER.warning(
                    "A file at '%s' already exists! Using that rather than downloading.", path
                )
                return path
            # we make a copy of the existing file in case downloading a new one fails
            backup = tempfile.NamedTemporaryFile()  # pylint: disable=consider-using-with
            backup.write(path.path.read_bytes())
            backup.seek(0)

        for pattern_url, repl_url in config.utils.file_downloader.url_map.items():
            if re.match(pattern_url, url):
                new_url = re.sub(pattern_url, repl_url, url)
                LOGGER.info(
                    "Matched the file's URL to your pattern URL %s and replaced it to become %s",
                    pattern_url,
                    new_url,
                )
                url = new_url
                break

        with open(path.path, "wb") as file:
            LOGGER.info("Downloading %s to %s", url, path)
            try:
                response = requests.get(url, timeout=10, stream=True)
                total_length = int(response.headers.get("content-length", -1))
            except requests.exceptions.RequestException as err:
                msg = f"An Exception occurred while downloading the file located at {url}"
                LOGGER.warning(msg)
                LOGGER.error(err)
                FileDownloader._unlink(path)
                if backup is not None:
                    path.path.write_bytes(backup.read())
                    backup.close()
                return None
            if total_length < 0:
                if not FileDownloader._assert_pdf(response.content):
                    FileDownloader._unlink(path)
                    if backup is not None:
                        path.path.write_bytes(backup.read())
                        backup.close()
                    return None
                file.write(response.content)
            else:
                accumulated_length = 0
                total_size = self._size(total_length)
                for data in response.iter_content(chunk_size=4096):
                    if accumulated_length == 0 and not FileDownloader._assert_pdf(data):
                        FileDownloader._unlink(path)
                        if backup is not None:
                            path.path.write_bytes(backup.read())
                            backup.close()
                        return None
                    accumulated_length += len(data)
                    file.write(data)
                    percentage = accumulated_length / total_length
                    progress = int(40 * percentage)
                    FileDownloader._logger(
                        "\rDownloading:"
                        f" [{'=' * progress}{' ' * (40 - progress)}] "
                        f"{100*percentage:6.1f}%"
                        f"{self._size(accumulated_length): >7} / {total_size: <7}",
                    )
                FileDownloader._logger("\n")
            msg = f"Successfully downloaded {path}"
            print(msg)
            LOGGER.info(msg)

            path = Event.PostFileDownload.fire(path) or path

            return path
