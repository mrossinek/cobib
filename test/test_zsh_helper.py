"""Tests for CoBib's zsh helper functions"""

import os
from pathlib import Path
from cobib import zsh_helper
import cobib


def test_list_commands():
    """Test listing commands"""
    cmds = zsh_helper.list_commands()
    cmds = [c.split(':')[0] for c in cmds]
    expected = [cmd.replace('Command', '').lower() for cmd in cobib.commands.__all__]
    assert sorted(cmds) == sorted(expected)


def test_list_tags():
    """Test listing tags"""
    root = os.path.abspath(os.path.dirname(__file__))
    tags = zsh_helper.list_tags({'config': Path(root + '/../cobib/docs/debug.ini')})
    assert tags == ['einstein', 'latexcompanion', 'knuthwebsite']


def test_list_filters():
    """Test listing filters"""
    root = os.path.abspath(os.path.dirname(__file__))
    filters = zsh_helper.list_filters({'config': Path(root + '/../cobib/docs/debug.ini')})
    assert filters == {'publisher', 'ENTRYTYPE', 'address', 'ID', 'journal', 'doi', 'year', 'title',
                       'author', 'pages', 'number', 'volume', 'url'}
