"""Tests for CReMa's actual commands"""

import os
from datetime import datetime
from io import StringIO
from pathlib import Path
from shutil import copyfile

import pytest
from crema import crema


@pytest.fixture
def setup():
    """Setup"""
    root = os.path.abspath(os.path.dirname(__file__))
    crema.set_config(Path(root + '/../crema/docs/debug.ini'))


def test_set_config(setup):  # pylint: disable=unused-argument, redefined-outer-name
    """Test config setting"""
    # from setup
    assert crema.CONFIG['DATABASE']['file'] == './test/example_literature.yaml'
    # change back to default
    crema.set_config()
    assert crema.CONFIG['DATABASE']['file'] == '~/.local/share/crema/literature.yaml'


def test_init():
    """Test init command"""
    # use temporary config
    tmp_config = "[DATABASE]\nfile=/tmp/crema_test_database.yaml\n"
    with open('/tmp/crema_test_config.ini', 'w') as file:
        file.write(tmp_config)
    crema.set_config(Path('/tmp/crema_test_config.ini'))
    # store current time
    now = float(datetime.now().timestamp())
    crema.init_({})
    # check creation time of temporary database file
    ctime = os.stat('/tmp/crema_test_database.yaml').st_ctime
    # assert these times are close
    assert ctime - now < 0.1 or now - ctime < 0.1
    # clean up file system
    os.remove('/tmp/crema_test_database.yaml')
    os.remove('/tmp/crema_test_config.ini')


def test_list(setup):  # pylint: disable=unused-argument, redefined-outer-name
    """Test list command"""
    # redirect output of list to string
    file = StringIO()
    tags = crema.list_([], out=file)
    expected = ['einstein', 'latexcompanion', 'knuthwebsite']
    assert tags == expected
    for line in file.getvalue().split('\n'):
        if line.startswith('ID') or all([c in '- ' for c in line]):
            # skip table header
            continue
        assert line.split()[0] in expected


def test_show(setup):  # pylint: disable=unused-argument, redefined-outer-name
    """Test show command"""
    file = StringIO()
    # pylint: disable=unexpected-keyword-arg
    crema.show_(['einstein'], out=file)  # TODO: figure out why the above exception is needed
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
    tmp_config = "[DATABASE]\nfile=/tmp/crema_test_database.yaml\n"
    with open('/tmp/crema_test_config.ini', 'w') as file:
        file.write(tmp_config)
    crema.set_config(Path('/tmp/crema_test_config.ini'))
    # ensure database file exists and is empty
    open('/tmp/crema_test_database.yaml', 'w').close()
    # add some data
    crema.add_(['-b', './test/example_literature.bib'])
    # compare with reference file
    with open('/tmp/crema_test_database.yaml', 'r') as file:
        with open('./test/example_literature.yaml', 'r') as expected:
            for line, truth in zip(file, expected):
                assert line == truth
    # clean up file system
    os.remove('/tmp/crema_test_database.yaml')
    os.remove('/tmp/crema_test_config.ini')


def test_remove():
    """Test remove command"""
    # use temporary config
    tmp_config = "[DATABASE]\nfile=/tmp/crema_test_database.yaml\n"
    with open('/tmp/crema_test_config.ini', 'w') as file:
        file.write(tmp_config)
    crema.set_config(Path('/tmp/crema_test_config.ini'))
    # copy example database to configured location
    copyfile(Path('./test/example_literature.yaml'), Path('/tmp/crema_test_database.yaml'))
    # remove some data
    # NOTE: for testing simplicity we remove the last entry
    crema.remove_(['knuthwebsite'])
    with open('/tmp/crema_test_database.yaml', 'r') as file:
        with open('./test/example_literature.yaml', 'r') as expected:
            for line, truth in zip(file, expected):
                assert line == truth
            with pytest.raises(StopIteration):
                file.__next__()
    # clean up file system
    os.remove('/tmp/crema_test_database.yaml')
    os.remove('/tmp/crema_test_config.ini')


def test_edit():
    """Test edit command"""
    pytest.skip("There is currently no meaningful way of testing this.")


def test_export(setup):  # pylint: disable=unused-argument, redefined-outer-name
    """Test export command"""
    crema.export_(['-b', '/tmp/crema_test_export.bib'])
    with open('/tmp/crema_test_export.bib', 'r') as file:
        with open('./test/example_literature.bib', 'r') as expected:
            for line, truth in zip(file, expected):
                assert line == truth
    # clean up file system
    os.remove('/tmp/crema_test_export.bib')
