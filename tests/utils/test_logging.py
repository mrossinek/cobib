"""Tests for coBib's logging helper functions."""

import logging

from cobib.utils.logging import get_file_handler, get_stream_handler


def test_get_stream_handler() -> None:
    """Test stream logging configuration."""
    handler = get_stream_handler()
    assert handler.level == 30
    assert isinstance(handler, logging.StreamHandler)


def test_get_file_handler() -> None:
    """Test file logging configuration."""
    handler = get_file_handler("INFO")
    assert handler.level == 20
    assert isinstance(handler, logging.FileHandler)
