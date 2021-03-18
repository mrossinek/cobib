"""Tests for CoBib's logging helper functions."""

import logging
from cobib.logging import log_to_stream, log_to_file


def test_log_to_stream():
    """Test stream logging configuration."""
    log_to_stream()
    logger = logging.getLogger()
    assert logger.level == 30
    assert isinstance(logger.handlers[0], logging.StreamHandler)


def test_log_to_file():
    """Test file logging configuration."""
    log_to_file()
    logger = logging.getLogger()
    assert logger.level == 20
    assert isinstance(logger.handlers[0], logging.FileHandler)
