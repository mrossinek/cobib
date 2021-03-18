"""Tests for CoBib's SearchCommand."""
# pylint: disable=no-self-use,unused-argument

import re

from io import StringIO
from itertools import zip_longest

from test.commands.command_test import CommandTest
from test.tui.tui_test import TUITest

import pytest

from cobib.commands import SearchCommand
from cobib.config import config


class TestSearchCommand(CommandTest, TUITest):
    """Tests for CoBib's SearchCommand."""

    def get_command(self):
        """Get the command tested by this class."""
        return SearchCommand

    def _assert(self, output, expected):
        """Common assertion utility method."""
        # we use zip_longest to ensure that we don't have more than we expect
        for line, exp in zip_longest(output, expected):
            line = line.replace('\x1b', '')
            line = re.sub(r'\[[0-9;]+m', '', line)
            if exp:
                assert exp in line
            if line and not (line.endswith('match') or line.endswith('matches')):
                assert re.match(r'\[[0-9]+\]', line)

    @pytest.mark.parametrize(['args', 'expected', 'config_overwrite'], [
        [['einstein'], ['einstein - 1 match', '@article{einstein,', 'author = {Albert Einstein},'],
         False],
        [['einstein', '-i'], [
            'einstein - 2 matches', '@article{einstein,', 'author = {Albert Einstein},',
            'doi = {http://dx.doi.org/10.1002/andp.19053221004},'
        ], False],
        [['einstein', '-i', '-c', '0'], [
            'einstein - 2 matches', '@article{einstein,', 'author = {Albert Einstein},'
        ], False],
        [['einstein', '-i', '-c', '2'], [
            'einstein - 2 matches', '@article{einstein,', 'author = {Albert Einstein},',
            'doi = {http://dx.doi.org/10.1002/andp.19053221004},', 'journal = {Annalen der Physik},'
        ], False],
        [['einstein'], [
            'einstein - 2 matches', '@article{einstein,', 'author = {Albert Einstein},',
            'doi = {http://dx.doi.org/10.1002/andp.19053221004},'
        ], True],
        [['einstein', '-i'], [
            'einstein - 2 matches', '@article{einstein,', 'author = {Albert Einstein},',
            'doi = {http://dx.doi.org/10.1002/andp.19053221004},'
        ], True],
    ])
    def test_command(self, setup, args, expected, config_overwrite):
        """Test the command itself."""
        config.commands.search.ignore_case = config_overwrite
        file = StringIO()

        SearchCommand().execute(args, out=file)
        self._assert(file.getvalue().split('\n'), expected)

    @pytest.mark.parametrize(['expected'], [
        [['einstein - 1 match', '@article{einstein,', 'author = {Albert Einstein},']],
    ])
    # other variants are already covered by test_command
    def test_cmdline(self, setup, monkeypatch, capsys, expected):
        """Test the command-line access of the command."""
        self.run_module(monkeypatch, 'main', ['cobib', 'search', 'einstein'])
        self._assert(capsys.readouterr().out.strip().split('\n'), expected)

    @pytest.mark.parametrize(['select', 'keys'], [
        [False, '/einstein\n'],
        [True, 'Gv/einstein\n'],
    ])
    def test_tui(self, setup, select, keys):
        """Test the TUI access of the command."""
        def assertion(screen, logs, **kwargs):
            expected_screen = [
                'einstein - 1 match',
                '[1]     @article{einstein,',
                '[1]      author = {Albert Einstein},'
            ]
            for line, truth in zip(expected_screen, screen.display[1:]):
                assert line == truth.strip()

            expected_log = [
                ('cobib.commands.search', 10, 'Search command triggered from TUI.'),
                ('cobib.commands.search', 10, 'Starting Search command.'),
                ('cobib.commands.search', 10,
                 "Available entries to search: ['einstein', 'latexcompanion', 'knuthwebsite']"),
                ('cobib.commands.search', 10, 'The search will be performed case sensitive'),
                ('cobib.commands.search', 10, 'Entry "einstein" includes 1 hits.'),
                ('cobib.commands.search', 10, 'Applying selection highlighting in search results.'),
                ('cobib.commands.search', 10, 'Populating viewport with search results.'),
                ('cobib.commands.search', 10, 'Resetting cursor position to top.'),

            ]
            assert [log for log in logs if log[0] == 'cobib.commands.search'] == expected_log

            colors = []
            for _ in range(3):
                # color matrix is initialized with default values for three lines
                colors.append([('default', 'default')] * 80)

            # selection must be visible
            if select:
                colors[0][0:8] = [('white', 'magenta')] * 8
            else:
                colors[0][0:8] = [('blue', 'black')] * 8
            # the current line highlighting is only visible from here onward
            colors[0][8:] = [('white', 'cyan')] * 72
            # the search keyword highlighting
            colors[1][17:25] = [('red', 'black')] * 8
            for idx, line in enumerate(colors):
                assert [(c.fg, c.bg) for c in screen.buffer[idx+1].values()] == line

        self.run_tui(keys, assertion, {'selection': select})

    def test_tui_no_hits(self, setup):
        """Test how the TUI handles no search results."""
        def assertion(screen, logs, **kwargs):
            expected_screen = [
                'knuthwebsite    Knuth: Computers and Typesetting',
                r'latexcompanion  The \LaTeX\ Companion',
                r'einstein        Zur Elektrodynamik bewegter K{\"o}rper'
            ]
            for line, truth in zip(expected_screen, screen.display[1:]):
                assert line == truth.strip()

            assert "No search hits for 'dummy'!" in screen.display[-1]

            expected_log = [
                ('cobib.commands.search', 10, 'Search command triggered from TUI.'),
                ('cobib.commands.search', 10, 'Starting Search command.'),
                ('cobib.commands.search', 10,
                 "Available entries to search: ['einstein', 'latexcompanion', 'knuthwebsite']"),
                ('cobib.commands.search', 10, 'The search will be performed case sensitive'),
                ('cobib.commands.search', 20, "No search hits for 'dummy'!"),

            ]
            assert [log for log in logs if log[0] == 'cobib.commands.search'] == expected_log

        self.run_tui('/dummy\n', assertion, {})
