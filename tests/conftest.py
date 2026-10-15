"""Shared pytest fixtures."""

import logging
from collections.abc import Generator

import pytest

from cobib.commands.base_command import Command
from cobib.config import config
from cobib.exporters.base_exporter import Exporter
from cobib.importers.base_importer import Importer


def _reset_argparsers() -> None:
    """Drops every cached `argparser` so that it gets rebuilt from the current config."""
    for cls in [Command, Exporter, Importer]:
        if "argparser" in vars(cls):
            delattr(cls, "argparser")
        for scls in cls.__subclasses__():
            if "argparser" in vars(scls):
                delattr(scls, "argparser")


@pytest.fixture(autouse=True)
def _reset_root_logger_handlers() -> Generator[None, None, None]:
    """Removes handlers which tests (e.g. via `run_module`) added to the root logger."""
    _reset_argparsers()
    yield
    # remove all handlers from root logger as to not accumulate them during the test suite
    logging.getLogger().handlers = []
    config.defaults()
