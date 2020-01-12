"""Tests for CReMa's zsh helper functions"""

import os
from pathlib import Path
from crema import zsh_helper
import crema


def test_list_commands():
    """Test listing commands"""
    cmds = zsh_helper.list_commands()
    cmds = [c.split(':')[0] for c in cmds]
    expected = [cmd[:-1] for cmd in crema.__all__]
    assert sorted(cmds) == sorted(expected)


def test_list_tags():
    """Test listing tags"""
    root = os.path.abspath(os.path.dirname(__file__))
    tags = zsh_helper.list_tags({'config': Path(root + '/../crema/docs/debug.ini')})
    assert tags == ['einstein', 'latexcompanion', 'knuthwebsite']


def test_list_filters():
    """Test listing filters"""
    root = os.path.abspath(os.path.dirname(__file__))
    filters = zsh_helper.list_filters({'config': Path(root + '/../crema/docs/debug.ini')})
    assert filters == {'publisher', 'ENTRYTYPE', 'address', 'ID', 'journal', 'doi', 'year', 'title',
                       'author', 'pages', 'number', 'volume', 'url'}
