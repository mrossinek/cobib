"""Tests for CoBib's TUI."""
# pylint: disable=unused-argument, redefined-outer-name

import curses
import fcntl
import os
import select
import termios
from array import array
from pathlib import Path

import pyte
import pytest
from cobib import __version__ as version
from cobib.commands import AddCommand, DeleteCommand
from cobib.config import CONFIG
from cobib.database import read_database
from cobib.tui import TextBuffer, TUI


@pytest.fixture
def setup():
    """Setup."""
    # ensure configuration is empty
    CONFIG.config = {}
    root = os.path.abspath(os.path.dirname(__file__))
    CONFIG.set_config(Path(root + '/../cobib/docs/debug.ini'))
    # NOTE: normally you would never trigger an Add command before reading the database but in this
    # controlled testing scenario we can be certain that this is fine
    AddCommand().execute(['-b', './test/dummy_scrolling_entry.bib'])
    read_database()
    yield setup
    DeleteCommand().execute(['dummy_entry_for_scroll_testing'])


def assert_list_view(screen, current, expected):
    """Asserts the list view of the TUI."""
    term_width = len(screen.buffer[0])
    # assert default colors
    assert [c.bg for c in screen.buffer[0].values()] == ['brown'] * term_width
    assert [c.bg for c in screen.buffer[len(screen.buffer)-2].values()] == ['brown'] * term_width
    # the top statusline contains the version info and number of entries
    assert f"CoBib v{version} - {len(expected)} Entries" in screen.display[0]
    # check current line
    if current >= 0:
        assert [c.fg for c in screen.buffer[current].values()] == ['white'] * term_width
        assert [c.bg for c in screen.buffer[current].values()] == ['cyan'] * term_width
    # the entries per line
    for idx, label in enumerate(expected):
        # offset of 1 due to top statusline
        assert label in screen.display[idx+1]
    # the bottom statusline should contain at least parts of the information string
    assert screen.display[-2].strip() in TUI.infoline()
    # the prompt line should be empty
    assert screen.display[-1].strip() == ""


def assert_help_screen(screen, offset=6, only_title=False):
    """Asserts the contents of the Help screen."""
    assert "CoBib TUI Help" in screen.display[offset]
    if not only_title:
        for cmd, desc in TUI.HELP_DICT.items():
            assert any("{:<8} {}".format(cmd+':', desc) in line for line in
                       screen.display[2+offset:19+offset])


def assert_no_help_window_artefacts(screen):
    """Asserts issue #20 remains fixed."""
    assert_list_view(screen, 1, [
        'dummy_entry_for_scroll_testing', 'knuthwebsite', 'latexcompanion', 'einstein'
    ])
    for line in range(5, 22):
        assert screen.display[line].strip() == ''


def assert_scroll(screen, update, direction):
    """Asserts cursor-line position after scrolling.

    Attention: The values of update *strongly* depend on the contents of the dummy scrolling entry.
    """
    term_width = len(screen.buffer[0])
    if direction == 'y' or update == 0:
        assert [c.fg for c in screen.buffer[1 + update].values()] == ['white'] * term_width
        assert [c.bg for c in screen.buffer[1 + update].values()] == ['cyan'] * term_width
    elif direction == 'x':
        # TODO actually use the update information
        assert [c.fg for c in screen.buffer[1].values()] == ['white'] * term_width
        assert [c.bg for c in screen.buffer[1].values()] == ['cyan'] * term_width


def assert_wrap(screen, state):
    """Asserts the viewport buffer is wrapped."""
    if state:
        assert screen.display[2][:2] == TextBuffer.INDENT + ' '
    else:
        assert screen.display[2][:2] == 'kn'


def assert_show(screen):
    """Asserts the show menu."""
    with open('./test/dummy_scrolling_entry.bib', 'r') as source:
        for screen_line, source_line in zip(screen.display[1:5], source.readlines()):
            assert screen_line.strip() in source_line.strip()


def assert_add(screen):
    """Asserts the add prompt."""
    try:
        assert f"CoBib v{version} - 5 Entries" in screen.display[0]
        assert "Cao_2019" in screen.display[1]
        assert "dummy_entry_for_scroll_testing" in screen.display[2]
        assert "knuthwebsite" in screen.display[3]
        assert "latexcompanion" in screen.display[4]
        assert "einstein" in screen.display[5]
    finally:
        DeleteCommand().execute(['Cao_2019'])


def assert_delete(screen):
    """Asserts entry is deleted.

    This also ensures it is added again after successful deletion.
    """
    try:
        assert f"CoBib v{version} - 3 Entries" in screen.display[0]
        assert not any("dummy_entry_for_scroll_testing" in line for line in screen.display[4:21])
    finally:
        AddCommand().execute(['-b', './test/dummy_scrolling_entry.bib'])


def assert_editor(screen):
    """Asserts the editor opens."""
    start = 0
    while '---' not in screen.display[start]:
        start += 1
    end = start+1
    while '...' not in screen.display[end]:
        end += 1
    with open('./test/example_literature.yaml', 'r') as source:
        for screen_line, source_line in zip(screen.display[start:end], source.readlines()):
            if screen_line.strip() == '~':
                # vim populates lines after the end of the file with single '~' characters
                break
            # assert the source line is fully part of the line visible in the editor window
            assert source_line.strip() in screen_line.strip()


def assert_export(screen, contents):
    """Asserts the export prompt."""
    assert screen.display[-1].strip() == contents
    # actual command execution is tested by the test_commands.test_export unittest


def assert_search_view(screen, label, search, selected):
    """Asserts the search screen contents."""
    term_width = len(screen.buffer[0])
    if selected:
        assert [c.bg for c in screen.buffer[1].values()] == \
            ['magenta'] * len(label) + \
            ['default'] * (term_width - len(label))
    else:
        assert [c.fg for c in screen.buffer[1].values()] == \
            ['blue'] * len(label) + \
            ['default'] * (term_width - len(label))
    offset = screen.display[2].index(search)
    assert [c.fg for c in screen.buffer[2].values()] == \
        ['default'] * offset + \
        ['red'] * len(search) + \
        ['default'] * (term_width - len(search) - offset)


def assert_select_list_view(screen, current, selected, labels):
    """Asserts the selection in the list view of the TUI."""
    term_width = len(screen.buffer[0])
    for sel, lab in zip(selected, labels):
        assert [c.bg for c in screen.buffer[sel].values()] == ['magenta'] * len(lab) + \
                ['cyan' if sel == current else 'default'] * (term_width - len(lab))


def assert_select_show_view(screen, current):
    """Asserts the selection in the show view."""
    label_len = len('dummy_entry_for_scroll_testing')
    with open('./test/dummy_scrolling_entry.bib', 'r') as source:
        for idx, (screen_line, source_line) in enumerate(zip(screen.display[1:5],
                                                             source.readlines())):
            if idx == 0:
                assert [c.bg for c in screen.buffer[1].values()] == \
                    ['cyan' if current else 'default'] * 6 + \
                    ['magenta'] * label_len + \
                    ['cyan' if current else 'default'] * (len(screen.buffer[0]) - label_len - 6)
            assert screen_line.strip() in source_line.strip()


@pytest.mark.parametrize(['keys', 'assertion', 'assertion_kwargs'], [
        ['', assert_list_view, {
            'current': 1, 'expected': [
                'dummy_entry_for_scroll_testing', 'knuthwebsite', 'latexcompanion', 'einstein'
            ]}],
        ['?q', assert_no_help_window_artefacts, {}],
        ['?', assert_help_screen, {}],
        ['w', assert_wrap, {'state': True}],
        ['ww', assert_wrap, {'state': False}],
        ['\n', assert_show, {}],
        ['a-b ./test/example_entry.bib\n', assert_add, {}],
        ['d', assert_delete, {}],
        ['Ge', assert_editor, {}],
        ['x', assert_export, {'contents': ":export"}],
        ['x' + 100 * 'j', assert_export, {'contents': 'j' * 79}],  # regression-test on #48
        ['f++ID einstein\n', assert_list_view, {
            'current': 1, 'expected': ['einstein']}],
        ['f--ID einstein\n', assert_list_view, {
            'current': 1, 'expected': [
                'dummy_entry_for_scroll_testing', 'knuthwebsite', 'latexcompanion'
            ]}],
        ['f++ID einstein ++ID knuthwebsite\n', assert_list_view, {
            'current': -1, 'expected': []}],
        ['f++ID einstein ++ID knuthwebsite -x\n', assert_list_view, {
            'current': 1, 'expected': ['knuthwebsite', 'einstein']}],
        ['syear\n', assert_list_view, {
            'current': 1, 'expected': [
                'latexcompanion', 'knuthwebsite', 'einstein', 'dummy_entry_for_scroll_testing'
            ]}],
        ['/einstein\njj', assert_search_view, {
            'label': 'einstein',
            'search': 'einstein',
            'selected': False
        }],
        ['/einstein\njjv', assert_search_view, {
            'label': 'einstein',
            'search': 'einstein',
            'selected': True
        }],
        ['Gv/einstein\njj', assert_search_view, {
            'label': 'einstein',
            'search': 'einstein',
            'selected': True
        }],
        ['/einstein\nvq', assert_select_list_view, {'current': 1, 'selected': [4],
                                                    'labels': ['einstein']}],
        ['v', assert_select_list_view, {'current': 1, 'selected': [1],
                                        'labels': ['dummy_entry_for_scroll_testing']}],
        ['vj', assert_select_list_view, {'current': 2, 'selected': [1],
                                         'labels': ['dummy_entry_for_scroll_testing']}],
        ['jvjv', assert_select_list_view, {'current': 3, 'selected': [2, 3],
                                           'labels': ['knuthwebsite', 'latexcompanion']}],
        ['vv', assert_list_view, {  # assert that re-selection toggles
            'current': 1, 'expected': [
                'dummy_entry_for_scroll_testing', 'knuthwebsite', 'latexcompanion', 'einstein'
            ]}],
        ['v\n', assert_select_show_view, {'current': True}],
        ['\nv', assert_select_show_view, {'current': True}],
        ['\nvj', assert_select_show_view, {'current': False}],
        ['\nvq', assert_select_list_view, {'current': 1, 'selected': [1],
                                           'labels': ['dummy_entry_for_scroll_testing']}],
    ])
def test_tui(setup, keys, assertion, assertion_kwargs):
    """Test TUI.

    Args:
        setup: runs pytest fixture.
        keys (str): keys to be send to the CoBib TUI.
        assertion (Callable): function to run the assertions for the key to be tested.
        assertion_kwargs (dict): additional keyword arguments for assertion function.
    """
    # create pseudo-terminal
    pid, f_d = os.forkpty()
    if pid == 0:
        # child process spawns TUI
        curses.wrapper(TUI)
    else:
        # parent process sets up virtual screen of identical size
        screen = pyte.Screen(80, 24)
        stream = pyte.ByteStream(screen)
        # send keys char-wise to TUI
        for key in keys:
            os.write(f_d, str.encode(key))
        # scrape pseudo-terminal's screen
        while True:
            try:
                [f_d], _, _ = select.select([f_d], [], [], 1)
            except (KeyboardInterrupt, ValueError):
                # either test was interrupted or file descriptor of child process provides nothing
                # to be read
                break
            else:
                try:
                    # scrape screen of child process
                    data = os.read(f_d, 1024)
                    stream.feed(data)
                except OSError:
                    # reading empty
                    break
        for line in screen.display:
            print(line)
        assertion(screen, **assertion_kwargs)


def assert_config_color(screen, colors):
    """Assert configured colors."""
    term_width = len(screen.buffer[0])
    assert [c.bg for c in screen.buffer[0].values()] == [colors['top_statusbar_bg']] * term_width
    assert [c.fg for c in screen.buffer[0].values()] == [colors['top_statusbar_fg']] * term_width
    assert [c.bg for c in screen.buffer[len(screen.buffer)-2].values()] == \
        [colors['bottom_statusbar_bg']] * term_width
    assert [c.fg for c in screen.buffer[len(screen.buffer)-2].values()] == \
        [colors['bottom_statusbar_fg']] * term_width
    assert [c.bg for c in screen.buffer[1].values()] == [colors['cursor_line_bg']] * term_width
    assert [c.fg for c in screen.buffer[1].values()] == [colors['cursor_line_fg']] * term_width


def test_tui_config_color():
    """Test TUI color configuration."""
    # ensure configuration is empty
    CONFIG.config = {}
    root = os.path.abspath(os.path.dirname(__file__))
    CONFIG.set_config(Path(root + '/../cobib/docs/debug.ini'))
    # overwrite color configuration
    CONFIG.config['COLORS']['top_statusbar_bg'] = 'red'
    CONFIG.config['COLORS']['top_statusbar_fg'] = 'blue'
    CONFIG.config['COLORS']['bottom_statusbar_bg'] = 'green'
    CONFIG.config['COLORS']['bottom_statusbar_fg'] = 'magenta'
    CONFIG.config['COLORS']['cursor_line_bg'] = 'white'
    CONFIG.config['COLORS']['cursor_line_fg'] = 'black'
    read_database()
    test_tui(None, '', assert_config_color, {'colors': CONFIG.config['COLORS']})


@pytest.mark.parametrize(['command', 'key'], [
        ['Show', 'p'],  # previously unused key
        ['Show', 'o'],  # should overwrite previously used key with other command
    ])
def test_tui_config_keys(command, key):
    """Test TUI key binding configuration."""
    # ensure configuration is empty
    CONFIG.config = {}
    root = os.path.abspath(os.path.dirname(__file__))
    CONFIG.set_config(Path(root + '/../cobib/docs/debug.ini'))
    # overwrite key binding configuration
    CONFIG.config['KEY_BINDINGS'][command] = key
    # NOTE: normally you would never trigger an Add command before reading the database but in this
    # controlled testing scenario we can be certain that this is fine
    AddCommand().execute(['-b', './test/dummy_scrolling_entry.bib'])
    read_database()
    try:
        test_tui(None, key, assert_show, {})
    finally:
        DeleteCommand().execute(['dummy_entry_for_scroll_testing'])


def assert_quit(screen, prompt):
    """Asserts the quit prompt."""
    if prompt == 'True':
        assert screen.display[-1].strip() == 'Do you really want to quit CoBib? [y/n]'
    elif prompt == 'False':
        assert screen.display[-1].strip() == ''
    else:
        assert not 'Unexpected prompt setting!'


@pytest.mark.parametrize(['setting', 'keys'], [
        ['True', 'q'],
        ['False', 'q'],
    ])
def test_tui_quit_prompt(setting, keys):
    """Test the prompt_before_quit setting of the TUI."""
    # ensure configuration is empty
    CONFIG.config = {}
    root = os.path.abspath(os.path.dirname(__file__))
    CONFIG.set_config(Path(root + '/../cobib/docs/debug.ini'))
    # set prompt_before_quit setting
    CONFIG.config['TUI']['prompt_before_quit'] = setting
    read_database()
    test_tui(None, keys, assert_quit, {'prompt': setting})


def assert_open(screen):
    """Asserts the open menu."""
    assert '1: [file] /tmp/a.txt' in screen.display[16]
    assert '2: [file] /tmp/b.txt' in screen.display[17]
    assert '3: [url] https://www.duckduckgo.com' in screen.display[18]
    assert '4: [url] https://www.google.com' in screen.display[19]
    assert "Entry to open [Type 'help' for more info]:" in screen.display[20]


def test_tui_open_menu():
    """Test the open prompt menu for multiple associated files."""
    # ensure configuration is empty
    CONFIG.config = {}
    root = os.path.abspath(os.path.dirname(__file__))
    CONFIG.set_config(Path(root + '/../cobib/docs/debug.ini'))
    # NOTE: normally you would never trigger an Add command before reading the database but in this
    # controlled testing scenario we can be certain that this is fine
    AddCommand().execute(['-b', './test/dummy_multi_file_entry.bib'])
    read_database()
    try:
        test_tui(None, 'o', assert_open, {})
    finally:
        DeleteCommand().execute(['dummy_multi_file_entry'])


@pytest.mark.parametrize(['keys', 'assertion', 'assertion_kwargs'], [
        ['', assert_list_view, {
            'current': 1, 'expected': [
                'dummy_entry_for_scroll_testing', 'knuthwebsite', 'latexcompanion', 'einstein'
            ]}],
        ['?', assert_help_screen, {'offset': 1, 'only_title': True}],
    ])
def test_tui_resize(setup, keys, assertion, assertion_kwargs):
    """Test TUI resize handling.

    Includes a regression test against #58 by opening the help popup.

    Args:
        setup: runs pytest fixture.
        keys (str): keys to be send to the CoBib TUI.
        assertion (Callable): function to run the assertions for the key to be tested.
        assertion_kwargs (dict): additional keyword arguments for assertion function.
    """
    # create pseudo-terminal
    pid, f_d = os.forkpty()
    if pid == 0:
        # child process spawns TUI
        curses.wrapper(TUI)
    else:
        # resize pseudo terminal
        fcntl.ioctl(f_d, termios.TIOCSWINSZ, array('h', [10, 45, 1200, 220]))
        # parent process sets up virtual screen of identical size
        screen = pyte.Screen(45, 10)
        stream = pyte.ByteStream(screen)
        # send keys char-wise to TUI
        for key in keys:
            os.write(f_d, str.encode(key))
        # scrape pseudo-terminal's screen
        while True:
            try:
                [f_d], _, _ = select.select([f_d], [], [], 1)
            except (KeyboardInterrupt, ValueError):
                # either test was interrupted or file descriptor of child process provides nothing
                # to be read
                break
            else:
                try:
                    # scrape screen of child process
                    data = os.read(f_d, 1024)
                    stream.feed(data)
                except OSError:
                    # reading empty
                    break
        for line in screen.display:
            print(line)
        assertion(screen, **assertion_kwargs)


@pytest.mark.parametrize(['keys', 'assertion', 'assertion_kwargs'], [
        # vertical scrolling
        ['G', assert_scroll, {'update': 20, 'direction': 'y'}],
        ['Gg', assert_scroll, {'update': 0, 'direction': 'y'}],
        ['j', assert_scroll, {'update': 1, 'direction': 'y'}],
        ['jjk', assert_scroll, {'update': 1, 'direction': 'y'}],
        # assert scrolloff value of `3` is respected
        [''.join(['j'] * 20), assert_scroll, {'update': 17, 'direction': 'y'}],
        [''.join(['j'] * 21), assert_scroll, {'update': 18, 'direction': 'y'}],
        [''.join(['j'] * 22), assert_scroll, {'update': 19, 'direction': 'y'}],
        ['G' + ''.join(['k'] * 20), assert_scroll, {'update': 3, 'direction': 'y'}],
        ['G' + ''.join(['k'] * 21), assert_scroll, {'update': 2, 'direction': 'y'}],
        ['G' + ''.join(['k'] * 22), assert_scroll, {'update': 1, 'direction': 'y'}],
        # horizontal scrolling
        ['l', assert_scroll, {'update': 1, 'direction': 'x'}],
        ['llh', assert_scroll, {'update': 1, 'direction': 'x'}],
        ['$', assert_scroll, {'update': 23, 'direction': 'x'}],
        ['$0', assert_scroll, {'update': 0, 'direction': 'x'}],
    ])
def test_tui_scrolling(keys, assertion, assertion_kwargs):
    """Test TUI scrolling behavior."""
    # ensure configuration is empty
    CONFIG.config = {}
    root = os.path.abspath(os.path.dirname(__file__))
    CONFIG.set_config(Path(root + '/../cobib/docs/debug.ini'))
    # overwrite database file
    CONFIG.config['DATABASE']['file'] = './test/scrolling_database.yaml'
    read_database()
    test_tui(None, keys, assertion, assertion_kwargs)
