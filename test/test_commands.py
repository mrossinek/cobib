"""Tests for CoBib's commands."""
# pylint: disable=unused-argument, redefined-outer-name

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from io import StringIO
from itertools import zip_longest
from pathlib import Path
from shutil import rmtree

import pytest
from cobib import commands
from cobib.config import CONFIG
from cobib.database import read_database


def assert_git_commit_message(command, args):
    """Assert the last auto-generated git commit message."""
    # get last commit message
    proc = subprocess.Popen(['git', '-C', '/tmp/cobib_test', 'show',
                             '--format=format:%B', '--no-patch', 'HEAD'],
                            stdout=subprocess.PIPE)
    message, _ = proc.communicate()
    # decode it
    message = message.decode('utf-8').split('\n')
    # assert subject line
    assert f'Auto-commit: {command.title()}Command' in message[0]
    # assert args
    args = json.dumps(args, indent=2, default=str)
    for ref, truth in zip(args.split('\n'), message[2:]):
        assert ref == truth


@pytest.fixture
def setup():
    """Setup."""
    root = os.path.abspath(os.path.dirname(__file__))
    CONFIG.set_config(Path(root + '/../cobib/docs/debug.ini'))
    CONFIG.validate()
    read_database()


def test_set_config(setup):
    """Test config setting.

    Args:
        setup: runs pytest fixture.
    """
    # from setup
    assert CONFIG.config['DATABASE']['file'] == './test/example_literature.yaml'
    # change back to default
    CONFIG.set_config()
    CONFIG.validate()
    assert CONFIG.config['DATABASE']['file'] == \
        os.path.expanduser('~/.local/share/cobib/literature.yaml')


@pytest.fixture(params=[False, True])
def init_setup(request):
    """Setup for InitCommand testing."""
    # use temporary config
    tmp_config = "[DATABASE]\nfile=/tmp/cobib_test/database.yaml\n"
    if request.param:
        tmp_config += 'git=True\n'
    with open('/tmp/cobib_test_config.ini', 'w') as file:
        file.write(tmp_config)
    # ensure configuration is empty
    CONFIG.config = {}
    # load config
    CONFIG.set_config(Path('/tmp/cobib_test_config.ini'))
    CONFIG.validate()
    # yielding the arguments allows re-using them inside of the actual test function
    yield request.param
    # clean up file system
    os.remove('/tmp/cobib_test_config.ini')
    if request.param:
        rmtree('/tmp/cobib_test/.git')


@pytest.mark.parametrize(['safe'], [
        [False],
        [True],
    ])
def test_init(init_setup, safe):
    """Test init command."""
    git = init_setup
    if safe:
        # fill database file
        with open('/tmp/cobib_test/database.yaml', 'w') as file:
            file.write('test')
    # store current time
    now = float(datetime.now().timestamp())
    # try running init
    commands.InitCommand().execute(['--git'] if git else [])
    if safe:
        # check database file still contains 'test'
        with open('/tmp/cobib_test/database.yaml', 'r') as file:
            assert file.read() == 'test'
    else:
        # check creation time of temporary database file
        ctime = os.stat('/tmp/cobib_test/database.yaml').st_ctime
        # assert these times are close
        assert ctime - now < 0.1 or now - ctime < 0.1
    if git:
        # check creation time of temporary database git folder
        ctime = os.stat('/tmp/cobib_test/.git').st_ctime
        # assert these times are close
        assert ctime - now < 0.1 or now - ctime < 0.1
        # and assert that it is indeed a folder
        assert os.path.isdir('/tmp/cobib_test/.git')
        # assert the git commit message
        assert_git_commit_message('init', {'git': True, 'force': False})
    # clean up file system
    os.remove('/tmp/cobib_test/database.yaml')


@pytest.mark.parametrize(['args', 'expected'], [
        [[], ['einstein', 'latexcompanion', 'knuthwebsite']],
        [['-r'], ['knuthwebsite', 'latexcompanion', 'einstein']],
        [['-s', 'year'], ['einstein', 'knuthwebsite', 'latexcompanion']],
        [['-r', '-s', 'year'], ['latexcompanion', 'knuthwebsite', 'einstein']],
    ])
def test_list(setup, args, expected):
    """Test list command.

    Args:
        setup: runs pytest fixture.
        args: arguments for the list command call.
        expected: expected result.
    """
    # redirect output of list to string
    file = StringIO()
    tags = commands.ListCommand().execute(args, out=file)
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

    Args:
        setup: runs pytest fixture.
    """
    # redirect output of list to string
    file = StringIO()
    tags = commands.ListCommand().execute(['++year', '1905'], out=file)
    expected = ['einstein']
    assert tags == expected
    for line in file.getvalue().split('\n'):
        if line.startswith('ID') or all([c in '- ' for c in line]):
            # skip table header
            continue
        assert line.split()[0] in expected


def test_show(setup):
    """Test show command.

    Args:
        setup: runs pytest fixture.
    """
    file = StringIO()
    commands.ShowCommand().execute(['einstein'], out=file)
    with open('./test/example_literature.bib', 'r') as expected:
        for line, truth in zip_longest(file.getvalue().split('\n'), expected):
            if not line:
                continue
            assert line == truth.strip('\n')


@pytest.fixture
def open_setup():
    """Setup for OpenCommand testing."""
    # ensure configuration is empty
    CONFIG.config = {}
    root = os.path.abspath(os.path.dirname(__file__))
    CONFIG.set_config(Path(root + '/../cobib/docs/debug.ini'))
    CONFIG.validate()
    # NOTE: normally you would never trigger an Add command before reading the database but in this
    # controlled testing scenario we can be certain that this is fine
    commands.AddCommand().execute(['-b', './test/dummy_multi_file_entry.bib'])
    read_database()
    yield setup
    # clean up
    commands.DeleteCommand().execute(['dummy_multi_file_entry'])


def test_open(open_setup):
    """Test open command.

    Args:
        open_setup: runs pytest fixture.
    """
    # pylint: disable=missing-class-docstring
    class DummyStdin:
        # pylint: disable=missing-function-docstring
        def readline(self):
            # pylint: disable=no-self-use
            return '\n'
    # replace sys.stdout and sys.stdin
    original_stdout = sys.stdout
    original_stdin = sys.stdin
    sys.stdout = StringIO()
    sys.stdin = DummyStdin()
    commands.OpenCommand().execute(['dummy_multi_file_entry'])
    expected = [
        "  1: [file] /tmp/a.txt",
        "  2: [file] /tmp/b.txt",
        "  3: [url] https://www.duckduckgo.com",
        "  4: [url] https://www.google.com",
        "Entry to open [Type 'help' for more info]: ",
    ]
    for line, truth in zip_longest(sys.stdout.getvalue().split('\n'), expected):
        assert line == truth
    # clean up
    sys.stdout = original_stdout
    sys.stdin = original_stdin


@pytest.fixture
def database_setup(init_setup):
    """Initialize a database on top of the init_setup fixture."""
    git = init_setup
    # initialize database
    # NOTE: if the InitCommand fails, all tests depending on this will fail, too
    commands.InitCommand().execute(['--git'] if git else [])
    # freshly read in database to overwrite anything that was read in during setup()
    read_database(fresh=True)
    # yield the parameter to allow re-use in actual test function
    yield git
    # clean up file system
    os.remove('/tmp/cobib_test/database.yaml')


def test_add(database_setup):
    """Test add command."""
    git = database_setup
    # add some data
    commands.AddCommand().execute(['-b', './test/example_literature.bib'])
    # compare with reference file
    with open('/tmp/cobib_test/database.yaml', 'r') as file:
        with open('./test/example_literature.yaml', 'r') as expected:
            for line, truth in zip_longest(file, expected):
                assert line == truth
    if git:
        # assert the git commit message
        with open('./test/example_literature.bib', 'r') as bibtex:
            assert_git_commit_message('add', {
                'label': None,
                'file': None,
                'arxiv': None,
                'bibtex': bibtex,
                'doi': None,
                'isbn': None,
                'tags': [],
            })


def test_add_overwrite_label(database_setup):
    """Test add command while specifying a label manually.

    Regression test against #4.
    """
    # add some data
    commands.AddCommand().execute(['-b', './test/example_literature.bib'])
    # add potentially duplicate entry
    commands.AddCommand().execute(['-b', './test/example_duplicate_entry.bib',
                                   '--label', 'duplicate_resolver'])
    # compare with reference file
    with open('./test/example_literature.yaml', 'r') as expected:
        true_lines = expected.readlines()
    with open('./test/example_duplicate_entry.yaml', 'r') as extra:
        true_lines += extra.readlines()
    with open('/tmp/cobib_test/database.yaml', 'r') as file:
        for line, truth in zip_longest(file, true_lines):
            assert line == truth


@pytest.mark.parametrize(['labels'], [
        [['knuthwebsite']],
        [['knuthwebsite', 'latexcompanion']],
    ])
def test_delete(database_setup, labels):
    """Test delete command."""
    git = database_setup
    # NOTE: DeleteCommand depends on AddCommand to work. While this is not so nice for the
    # unittests, it is the easiest method of testing all git and non-git scenarios.
    commands.AddCommand().execute(['-b', './test/example_literature.bib'])
    # delete some data
    # NOTE: for testing simplicity we delete the last entry
    commands.DeleteCommand().execute(labels)
    with open('/tmp/cobib_test/database.yaml', 'r') as file:
        with open('./test/example_literature.yaml', 'r') as expected:
            # NOTE: do NOT use zip_longest to omit last entry (thus, we deleted the last one)
            for line, truth in zip(file, expected):
                assert line == truth
            with pytest.raises(StopIteration):
                file.__next__()
    if git:
        # assert the git commit message
        assert_git_commit_message('delete', {'labels': labels})


# TODO: figure out some very crude and basic way of testing this
def test_edit():
    """Test edit command."""
    pytest.skip("There is currently no meaningful way of testing this.")


def test_export(setup):
    """Test export command.

    Args:
        setup: runs pytest fixture.
    """
    commands.ExportCommand().execute(['-b', '/tmp/cobib_test_export.bib'])
    with open('/tmp/cobib_test_export.bib', 'r') as file:
        with open('./test/example_literature.bib', 'r') as expected:
            for line, truth in zip_longest(file, expected):
                if truth[0] == '%':
                    # ignore comments
                    continue
                assert line == truth
    # clean up file system
    os.remove('/tmp/cobib_test_export.bib')


def test_export_selection(setup):
    """Test the `selection` interface of the export command.

    Args:
        setup: runs pytest fixture.
    """
    commands.ExportCommand().execute(['-b', '/tmp/cobib_test_export_s.bib', '-s', '--', 'einstein'])
    with open('/tmp/cobib_test_export_s.bib', 'r') as file:
        with open('./test/example_literature.bib', 'r') as expected:
            for line, truth in zip_longest(file, expected):
                print(line, truth)
                if truth[0] == '%':
                    # ignore comments
                    continue
                if truth.strip() == '@book{latexcompanion,':
                    # reached next entry
                    break
                assert line == truth
    # clean up file system
    os.remove('/tmp/cobib_test_export_s.bib')


@pytest.mark.parametrize(['args', 'expected', 'config_overwrite'], [
        [['einstein'], ['einstein - 1 match', '@article{einstein,', 'author = {Albert Einstein},'],
         'False'],
        [['einstein', '-i'], [
            'einstein - 2 matches', '@article{einstein,', 'author = {Albert Einstein},',
            'doi = {http://dx.doi.org/10.1002/andp.19053221004},'
        ], 'False'],
        [['einstein', '-i', '-c', '0'], [
            'einstein - 2 matches', '@article{einstein,', 'author = {Albert Einstein},'
        ], 'False'],
        [['einstein', '-i', '-c', '2'], [
            'einstein - 2 matches', '@article{einstein,', 'author = {Albert Einstein},',
            'doi = {http://dx.doi.org/10.1002/andp.19053221004},', 'journal = {Annalen der Physik},'
        ], 'False'],
        [['einstein'], [
            'einstein - 2 matches', '@article{einstein,', 'author = {Albert Einstein},',
            'doi = {http://dx.doi.org/10.1002/andp.19053221004},'
        ], 'True'],
        [['einstein', '-i'], [
            'einstein - 2 matches', '@article{einstein,', 'author = {Albert Einstein},',
            'doi = {http://dx.doi.org/10.1002/andp.19053221004},'
        ], 'True'],
    ])
def test_search(setup, args, expected, config_overwrite):
    """Test search command.

    Args:
        setup: runs pytest fixture.
        args: arguments for the list command call.
        expected: expected result.
        config_overwrite: with what to overwrite the DATABASE/ignore_search_case config option.
    """
    CONFIG.config['DATABASE']['search_ignore_case'] = config_overwrite
    file = StringIO()
    commands.SearchCommand().execute(args, out=file)
    for line, exp in zip_longest(file.getvalue().split('\n'), expected):
        line = line.replace('\x1b', '')
        line = re.sub(r'\[[0-9;]+m', '', line)
        if exp:
            assert exp in line
        if line and not (line.endswith('match') or line.endswith('matches')):
            assert re.match(r'\[[0-9]+\]', line)
