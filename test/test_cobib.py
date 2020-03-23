"""Tests for CoBib's actual commands"""
# pylint: disable=unused-argument, redefined-outer-name

import os
from datetime import datetime
from io import StringIO
from pathlib import Path
from shutil import copyfile

import pytest
from cobib import cobib


@pytest.fixture
def setup():
    """Setup"""
    root = os.path.abspath(os.path.dirname(__file__))
    cobib.set_config(Path(root + '/../cobib/docs/debug.ini'))


def test_set_config(setup):
    """Test config setting"""
    # from setup
    assert cobib.CONFIG['DATABASE']['file'] == './test/example_literature.yaml'
    # change back to default
    cobib.set_config()
    assert cobib.CONFIG['DATABASE']['file'] == '~/.local/share/cobib/literature.yaml'


def test_init():
    """Test init command"""
    # use temporary config
    tmp_config = "[DATABASE]\nfile=/tmp/cobib_test_database.yaml\n"
    with open('/tmp/cobib_test_config.ini', 'w') as file:
        file.write(tmp_config)
    cobib.set_config(Path('/tmp/cobib_test_config.ini'))
    # store current time
    now = float(datetime.now().timestamp())
    cobib.init_({})
    # check creation time of temporary database file
    ctime = os.stat('/tmp/cobib_test_database.yaml').st_ctime
    # assert these times are close
    assert ctime - now < 0.1 or now - ctime < 0.1
    # clean up file system
    os.remove('/tmp/cobib_test_database.yaml')
    os.remove('/tmp/cobib_test_config.ini')


def test_list(setup):
    """Test list command"""
    # redirect output of list to string
    file = StringIO()
    tags = cobib.list_([], out=file)
    expected = ['einstein', 'latexcompanion', 'knuthwebsite']
    assert tags == expected
    for line in file.getvalue().split('\n'):
        if line.startswith('ID') or all([c in '- ' for c in line]):
            # skip table header
            continue
        assert line.split()[0] in expected


def test_list_with_missing_keys(setup):
    """Asserts issue #1 is fixed.

    When a key is queried which is not present in all entries, the list command should return
    normally.
    """
    # redirect output of list to string
    file = StringIO()
    tags = cobib.list_(['++year', '1905'], out=file)
    expected = ['einstein']
    assert tags == expected
    for line in file.getvalue().split('\n'):
        if line.startswith('ID') or all([c in '- ' for c in line]):
            # skip table header
            continue
        assert line.split()[0] in expected


def test_show(setup):
    """Test show command"""
    file = StringIO()
    cobib.show_(['einstein'], out=file)
    with open('./test/example_literature.bib', 'r') as expected:
        for line, truth in zip(file.getvalue().split('\n'), expected):
            if not line:
                continue
            assert line == truth.strip('\n')


def test_open():
    """Test open command"""
    pytest.skip("There is currently no meaningful way of testing this.")


def test_add():
    """Test add command"""
    # use temporary config
    tmp_config = "[DATABASE]\nfile=/tmp/cobib_test_database.yaml\n"
    with open('/tmp/cobib_test_config.ini', 'w') as file:
        file.write(tmp_config)
    cobib.set_config(Path('/tmp/cobib_test_config.ini'))
    # ensure database file exists and is empty
    open('/tmp/cobib_test_database.yaml', 'w').close()
    # add some data
    cobib.add_(['-b', './test/example_literature.bib'])
    # compare with reference file
    with open('/tmp/cobib_test_database.yaml', 'r') as file:
        with open('./test/example_literature.yaml', 'r') as expected:
            for line, truth in zip(file, expected):
                assert line == truth
    # clean up file system
    os.remove('/tmp/cobib_test_database.yaml')
    os.remove('/tmp/cobib_test_config.ini')


def test_remove():
    """Test remove command"""
    # use temporary config
    tmp_config = "[DATABASE]\nfile=/tmp/cobib_test_database.yaml\n"
    with open('/tmp/cobib_test_config.ini', 'w') as file:
        file.write(tmp_config)
    cobib.set_config(Path('/tmp/cobib_test_config.ini'))
    # copy example database to configured location
    copyfile(Path('./test/example_literature.yaml'), Path('/tmp/cobib_test_database.yaml'))
    # remove some data
    # NOTE: for testing simplicity we remove the last entry
    cobib.remove_(['knuthwebsite'])
    with open('/tmp/cobib_test_database.yaml', 'r') as file:
        with open('./test/example_literature.yaml', 'r') as expected:
            for line, truth in zip(file, expected):
                assert line == truth
            with pytest.raises(StopIteration):
                file.__next__()
    # clean up file system
    os.remove('/tmp/cobib_test_database.yaml')
    os.remove('/tmp/cobib_test_config.ini')


def test_edit():
    """Test edit command"""
    pytest.skip("There is currently no meaningful way of testing this.")


def test_export(setup):
    """Test export command"""
    cobib.export_(['-b', '/tmp/cobib_test_export.bib'])
    with open('/tmp/cobib_test_export.bib', 'r') as file:
        with open('./test/example_literature.bib', 'r') as expected:
            for line, truth in zip(file, expected):
                assert line == truth
    # clean up file system
    os.remove('/tmp/cobib_test_export.bib')
