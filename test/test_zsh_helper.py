"""Tests for CoBib's zsh helper functions."""

import os
from itertools import zip_longest
from pathlib import Path
from cobib import zsh_helper
from cobib.config import config
import cobib


def test_list_commands():
    """Test listing commands."""
    cmds = zsh_helper.list_commands()
    cmds = [c.split(':')[0] for c in cmds]
    expected = [cmd.replace('Command', '').lower() for cmd in cobib.commands.__all__]
    assert sorted(cmds) == sorted(expected)


def test_list_tags():
    """Test listing tags."""
    root = os.path.abspath(os.path.dirname(__file__))
    config.load(Path(root + '/debug.py'))
    tags = zsh_helper.list_tags()
    assert tags == ['einstein', 'latexcompanion', 'knuthwebsite']


def test_list_filters():
    """Test listing filters."""
    root = os.path.abspath(os.path.dirname(__file__))
    config.load(Path(root + '/debug.py'))
    filters = zsh_helper.list_filters()
    assert filters == {'publisher', 'ENTRYTYPE', 'address', 'ID', 'journal', 'doi', 'year', 'title',
                       'author', 'pages', 'number', 'volume', 'url'}


def test_example_config():
    """Test printing the example config."""
    root = os.path.abspath(os.path.dirname(__file__))
    config.load(Path(root + '/debug.py'))
    example = zsh_helper.example_config()
    with open(root + '/../cobib/config/example.py', 'r') as expected:
        for line, truth in zip_longest(example, expected):
            assert line == truth.strip()
