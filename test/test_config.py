"""Tests for CoBib's config validation."""
# pylint: disable=unused-argument, redefined-outer-name

import os
from pathlib import Path

import pytest
from cobib.config import config


def test_load_config():
    """Test loading another config file."""
    root = os.path.abspath(os.path.dirname(__file__))
    config.load(Path(root + '/debug.py'))
    assert config.database.file == './test/example_literature.yaml'


# TODO: remove legacy configuration support on 1.1.2022
def test_load_legacy_config():
    """Test loading a legacy config file."""
    root = os.path.abspath(os.path.dirname(__file__))
    print(root)
    config.load_legacy_config(Path(root + '/legacy_config.ini'))
    # first, it must pass the validation test
    config.validate()
    # then we also check that all settings have been changed somehow
    assert config.commands.edit.default_entry_type == 'string'
    assert config.commands.open.command == 'string'
    assert config.commands.search.grep == 'string'
    assert config.commands.search.ignore_case is True
    assert config.database.file == 'string'
    assert config.database.git is True
    assert config.database.format.month == str
    assert config.parsers.bibtex.ignore_non_standard_types is True
    assert config.tui.default_list_args == ['string']
    assert config.tui.prompt_before_quit is False
    assert config.tui.reverse_order is False
    assert config.tui.scroll_offset == 5
    assert config.tui.colors.cursor_line_fg == 'black'
    assert config.tui.key_bindings.prompt == 'p'


@pytest.fixture
def setup():
    """Setup."""
    root = os.path.abspath(os.path.dirname(__file__))
    config.load(Path(root + '/debug.py'))
    yield setup
    config.defaults()


def test_base_config(setup):
    """Test the initial configuration passes all validation checks."""
    config.validate()


@pytest.mark.parametrize(['sections', 'field'], [
        [['commands', 'edit'], 'default_entry_type'],
        [['commands', 'open'], 'command'],
        [['commands', 'search'], 'grep'],
        [['commands', 'search'], 'ignore_case'],
        [['database'], 'file'],
        [['database'], 'git'],
        [['database', 'format'], 'month'],
        [['parsers', 'bibtex'], 'ignore_non_standard_types'],
        [['tui'], 'default_list_args'],
        [['tui'], 'prompt_before_quit'],
        [['tui'], 'reverse_order'],
        [['tui'], 'scroll_offset'],
        [['tui', 'colors'], 'cursor_line_fg'],
        [['tui', 'colors'], 'cursor_line_bg'],
        [['tui', 'colors'], 'top_statusbar_fg'],
        [['tui', 'colors'], 'top_statusbar_bg'],
        [['tui', 'colors'], 'bottom_statusbar_fg'],
        [['tui', 'colors'], 'bottom_statusbar_bg'],
        [['tui', 'colors'], 'search_label_fg'],
        [['tui', 'colors'], 'search_label_bg'],
        [['tui', 'colors'], 'search_query_fg'],
        [['tui', 'colors'], 'search_query_bg'],
        [['tui', 'colors'], 'popup_help_fg'],
        [['tui', 'colors'], 'popup_help_bg'],
        [['tui', 'colors'], 'popup_stdout_fg'],
        [['tui', 'colors'], 'popup_stdout_bg'],
        [['tui', 'colors'], 'popup_stderr_fg'],
        [['tui', 'colors'], 'popup_stderr_bg'],
        [['tui', 'colors'], 'selection_fg'],
        [['tui', 'colors'], 'selection_bg'],
        [['tui', 'key_bindings'], 'prompt'],
        [['tui', 'key_bindings'], 'search'],
        [['tui', 'key_bindings'], 'help'],
        [['tui', 'key_bindings'], 'add'],
        [['tui', 'key_bindings'], 'delete'],
        [['tui', 'key_bindings'], 'edit'],
        [['tui', 'key_bindings'], 'filter'],
        [['tui', 'key_bindings'], 'modify'],
        [['tui', 'key_bindings'], 'open'],
        [['tui', 'key_bindings'], 'quit'],
        [['tui', 'key_bindings'], 'redo'],
        [['tui', 'key_bindings'], 'sort'],
        [['tui', 'key_bindings'], 'undo'],
        [['tui', 'key_bindings'], 'select'],
        [['tui', 'key_bindings'], 'wrap'],
        [['tui', 'key_bindings'], 'export'],
        [['tui', 'key_bindings'], 'show'],
    ])
def test_missing_config_fields(setup, sections, field):
    """Test raised RuntimeError for missing config fields."""
    with pytest.raises(RuntimeError) as exc_info:
        section = config
        for sec in sections[:-1]:
            section = config[sec]
        del section[sections[-1]][field]
        config.validate()
    assert f"config.{'.'.join(sections)}.{field}" in str(exc_info.value)


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
        ['popup_help_fg'],
        ['popup_help_bg'],
        ['popup_stdout_fg'],
        ['popup_stdout_bg'],
        ['popup_stderr_fg'],
        ['popup_stderr_bg'],
        ['selection_fg'],
        ['selection_bg'],
    ])
def test_valid_tui_colors(setup, color):
    """Test curses color specification validation."""
    with pytest.raises(RuntimeError) as exc_info:
        config.tui.colors[color] = 'test'
        config.validate()
    assert str(exc_info.value) == 'Unknown color specification: test'
