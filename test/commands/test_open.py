"""Tests for CoBib's OpenCommand."""
# pylint: disable=no-self-use,unused-argument

from test.commands.command_test import CommandTest
from test.tui.tui_test import TUITest

import pytest

from cobib.commands import OpenCommand
from cobib.database import Database


class MockStdin:
    """A mock object to replace sys.stdin."""
    # pylint: disable=missing-function-docstring

    def __init__(self, string=None):
        # noqa: D107
        if string is None:
            string = []
        self.string = string + ['\n']

    def readline(self):
        # noqa: D102
        return self.string.pop(0)


class TestOpenCommand(CommandTest, TUITest):
    """Tests for CoBib's OpenCommand."""

    def get_command(self):
        """Get the command tested by this class."""
        return OpenCommand

    @pytest.fixture
    def post_setup(self, monkeypatch, request):
        """Setup."""
        if not hasattr(request, 'param'):
            # use default settings
            request.param = {'stdin_list': None, 'multi_file': True}

        if request.param.get('multi_file', True):
            with open('./test/commands/example_multi_file_entry.yaml', 'r') as multi_file_entry:
                with open('/tmp/cobib_test/database.yaml', 'a') as database:
                    database.write(multi_file_entry.read())
            Database().read()

        monkeypatch.setattr('sys.stdin', MockStdin(request.param.get('stdin_list', None)))

        yield request.param

    def _assert(self, output, logs=None, **kwargs):
        """Common assertion utility method."""
        if not kwargs.get('multi_file', True):
            expected_log = [
                ('cobib.commands.open', 10, 'Starting Open command.'),
                ('cobib.commands.open', 10,
                 'Parsing "http://www-cs-faculty.stanford.edu/\\~{}uno/abcde.html" for URLs.'),
                ('cobib.commands.open', 10,
                 'Opening "http://www-cs-faculty.stanford.edu/\\~{}uno/abcde.html" with cat.')
            ]
            if logs is not None:
                assert logs == expected_log
        else:
            expected_out = [
                "  1: [file] /tmp/a.txt",
                "  2: [file] /tmp/b.txt",
                "  3: [url] https://www.duckduckgo.com",
                "  4: [url] https://www.google.com",
                "Entry to open [Type 'help' for more info]: ",
            ]

            expected_log = [
                ('cobib.commands.open', 10, 'Starting Open command.'),
                ('cobib.commands.open', 10, 'Parsing "/tmp/a.txt" for URLs.'),
                ('cobib.commands.open', 10, 'Parsing "/tmp/b.txt" for URLs.'),
                ('cobib.commands.open', 10, 'Parsing "https://www.duckduckgo.com" for URLs.'),
                ('cobib.commands.open', 10, 'Parsing "https://www.google.com" for URLs.'),
            ]

            stdin_list = kwargs.get('stdin_list', [])
            extra_logs = None
            if not stdin_list:
                expected_log.append(('cobib.commands.open', 30, 'User aborted open command.'))
            elif 'help' in stdin_list:
                expected_out += expected_out.copy()
                expected_out[4] += "You can specify one of the following options:"
                extra_out = [
                    "  1. a url number",
                    "  2. a field name provided in '[...]'",
                    "  3. or simply 'all'",
                    "  4. ENTER will abort the command",
                    ""
                ]
                for line in reversed(extra_out):
                    expected_out.insert(5, line)

                expected_log.append(('cobib.commands.open', 10, 'User requested help.'))
                expected_log.append(('cobib.commands.open', 30, 'User aborted open command.'))
            elif 'all' in stdin_list:
                extra_logs = [
                    ('cobib.commands.open', 10, 'User selected all urls.'),
                    ('cobib.commands.open', 10, 'Opening "/tmp/a.txt" with cat.'),
                    ('cobib.commands.open', 10, 'Opening "/tmp/b.txt" with cat.'),
                    ('cobib.commands.open', 10, 'Opening "https://www.duckduckgo.com" with cat.'),
                    ('cobib.commands.open', 10, 'Opening "https://www.google.com" with cat.'),
                ]
            elif 'url' in stdin_list:
                extra_logs = [
                    ('cobib.commands.open', 10, 'User selected the url set of urls.'),
                    ('cobib.commands.open', 10, 'Opening "https://www.duckduckgo.com" with cat.'),
                    ('cobib.commands.open', 10, 'Opening "https://www.google.com" with cat.'),
                ]
            elif '1' in stdin_list:
                extra_logs = [
                    ('cobib.commands.open', 10, 'User selected url 1'),
                    ('cobib.commands.open', 10, 'Opening "/tmp/a.txt" with cat.'),
                ]

            if extra_logs is not None:
                for log in extra_logs:
                    expected_log.append(log)

            for line, truth in zip(output, expected_out):
                assert line == truth
            if logs is not None:
                assert logs == expected_log

    @pytest.mark.parametrize(['args', 'post_setup'], [
        [['knuthwebsite'], {'multi_file': False}],
        [['example_multi_file_entry'], {'multi_file': True}],
        [['example_multi_file_entry'], {'multi_file': True, 'stdin_list': ['help']}],
        [['example_multi_file_entry'], {'multi_file': True, 'stdin_list': ['all']}],
        [['example_multi_file_entry'], {'multi_file': True, 'stdin_list': ['url']}],
        [['example_multi_file_entry'], {'multi_file': True, 'stdin_list': ['1']}],
    ], indirect=['post_setup'])
    def test_command(self, setup, post_setup, caplog, capsys, args):
        """Test the command itself."""
        OpenCommand().execute(args)

        true_log = [rec for rec in caplog.record_tuples if rec[0] == 'cobib.commands.open']
        true_out = capsys.readouterr().out.split('\n')

        self._assert(true_out, true_log, **post_setup)

    def test_warning_missing_label(self, setup, caplog):
        """Test warning for missing label."""
        OpenCommand().execute(['dummy'])
        assert ('cobib.commands.open', 30, "No entry with the label 'dummy' could be found.") \
            in caplog.record_tuples

    def test_warning_nothing_to_open(self, setup, caplog):
        """Test warning for label with nothing to open."""
        OpenCommand().execute(['einstein'])
        assert ('cobib.commands.open', 30,
                "The entry 'einstein' has no actionable field associated with it.") \
            in caplog.record_tuples

    @pytest.mark.parametrize(['post_setup'], [
        [{'multi_file': False}],
    ], indirect=['post_setup'])
    def test_cmdline(self, setup, post_setup, monkeypatch, capsys):
        """Test the command-line access of the command."""
        self.run_module(monkeypatch, 'main', ['cobib', 'open', 'knuthwebsite'])

        true_out = capsys.readouterr().out.split('\n')

        self._assert(true_out, logs=None, **post_setup)

    @pytest.mark.parametrize(['select', 'keys'], [
        [False, 'o'],
        [True, 'Gvo'],
    ])
    def test_tui(self, setup, select, keys):
        """Test the TUI access of the command."""
        def assertion(screen, logs, **kwargs):
            expected_log = [
                ('cobib.commands.open', 10, 'Open command triggered from TUI.'),
                ('cobib.commands.open', 10, 'Starting Open command.'),
            ]
            if kwargs.get('selection', False):
                expected_log.append(
                    ('cobib.commands.open', 30,
                     "The entry 'einstein' has no actionable field associated with it.")
                )
            else:
                expected_log.append(
                    ('cobib.commands.open', 10,
                     'Parsing "http://www-cs-faculty.stanford.edu/\\~{}uno/abcde.html" for URLs.')
                )
                expected_log.append(
                    ('cobib.commands.open', 10,
                     'Opening "http://www-cs-faculty.stanford.edu/\\~{}uno/abcde.html" with cat.')
                )

            assert [log for log in logs if log[0] == 'cobib.commands.open'] == expected_log

        self.run_tui(keys, assertion, {'selection': select})
