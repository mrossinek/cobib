"""coBib's file downloader utility."""

from __future__ import annotations

import logging
import sys
from typing import Callable, Optional

import requests

from cobib.config import config

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

    def download(self, url: str, label: str, folder: Optional[str] = None) -> Optional[RelPath]:
        """Downloads a file.

        The path of the downloaded file is `folder/label.pdf`. The path can be configured via
        `cobib.config.commands.add.download_location`.

        Args:
            url: the link to the file to be downloaded.
            label: the name of the entry.
            folder: an optional folder where the downloaded file will be stored.

        Returns:
            The `RelPath` to the downloaded file. If downloading was not successful, `None` is
            returned.
        """
        if folder is None:
            folder = config.utils.file_downloader.default_location
        path = RelPath(f"{folder}/{label}.pdf")
        with open(path.path, "wb") as file:
            LOGGER.info("Downloading %s", path)
            try:
                response = requests.get(url, timeout=10, stream=True)
                total_length = int(response.headers.get("content-length", -1))
            except requests.exceptions.RequestException as err:
                msg = f"An Exception occurred while downloading the file located at {url}"
                LOGGER.warning(msg)
                LOGGER.error(err)
                print(msg, file=sys.stderr)
                return None
            if total_length < 0:
                file.write(response.content)
            else:
                accumulated_length = 0
                total_size = self._size(total_length)
                for data in response.iter_content(chunk_size=4096):
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
            LOGGER.info(msg)
            print(msg)
            return path
