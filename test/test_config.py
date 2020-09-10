"""Tests for CoBib's config validation."""
# pylint: disable=unused-argument, redefined-outer-name

import os
from pathlib import Path

import pytest
from cobib.config import CONFIG


@pytest.fixture
def setup():
    """Setup."""
    # ensure configuration is empty
    CONFIG.config = {}
    root = os.path.abspath(os.path.dirname(__file__))
    CONFIG.set_config(Path(root + '/../cobib/docs/debug.ini'))


def test_base_config(setup):
    """Test the initial configuration passes all validation checks."""
    CONFIG.validate()


@pytest.mark.parametrize(['section'], [
        ['DATABASE'],
        ['FORMAT'],
        ['TUI'],
        ['KEY_BINDINGS'],
        ['COLORS'],
    ])
def test_missing_section(setup, section):
    """Test raised RuntimeError for missing configuration section."""
    with pytest.raises(RuntimeError) as exc_info:
        del CONFIG.config[section]
        CONFIG.validate()
    assert section in str(exc_info.value)


@pytest.mark.parametrize(['section', 'field'], [
        ['DATABASE', 'file'],
        ['DATABASE', 'open'],
        ['DATABASE', 'grep'],
        ['FORMAT', 'month'],
        ['FORMAT', 'ignore_non_standard_types'],
        ['TUI', 'default_list_args'],
        ['TUI', 'prompt_before_quit'],
        ['TUI', 'reverse_order'],
        ['TUI', 'scroll_offset'],
        ['COLORS', 'cursor_line_fg'],
        ['COLORS', 'cursor_line_bg'],
        ['COLORS', 'top_statusbar_fg'],
        ['COLORS', 'top_statusbar_bg'],
        ['COLORS', 'bottom_statusbar_fg'],
        ['COLORS', 'bottom_statusbar_bg'],
        ['COLORS', 'search_label_fg'],
        ['COLORS', 'search_label_bg'],
        ['COLORS', 'search_query_fg'],
        ['COLORS', 'search_query_bg'],
    ])
def test_database_section(setup, section, field):
    """Test raised RuntimeError for missing config fields."""
    with pytest.raises(RuntimeError) as exc_info:
        del CONFIG.config.get(section, {})[field]
        CONFIG.validate()
    assert f'{section}/{field}' in str(exc_info.value)


@pytest.mark.parametrize(['color'], [
        ['cursor_line_fg'],
        ['cursor_line_bg'],
        ['top_statusbar_fg'],
        ['top_statusbar_bg'],
        ['bottom_statusbar_fg'],
        ['bottom_statusbar_bg'],
        ['search_label_fg'],
        ['search_label_bg'],
        ['search_query_fg'],
        ['search_query_bg'],
    ])
def test_valid_tui_colors(setup, color):
    """Test curses color specification validation."""
    with pytest.raises(RuntimeError) as exc_info:
        CONFIG.config.get('COLORS', {})[color] = 'test'
        CONFIG.validate()
    assert str(exc_info.value) == 'Unknown color specification: test'
