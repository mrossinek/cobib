"""Tests for CoBib's EditCommand."""
# pylint: disable=no-self-use,unused-argument

from test.commands.command_test import CommandTest
from test.tui.tui_test import TUITest

import pytest

from cobib.commands import EditCommand


class TestEditCommand(CommandTest, TUITest):
    """Tests for CoBib's EditCommand.

    Note: in order to be able to test this command to at least a minimal degree, the test
    configuration sets the "editor" to be "cat". Thus, no changes will ever actually be made through
    this "editor".
    Nonetheless, this allows us to test the case where no changes are made (obviously), while also
    being able to test that the EditCommand actually writes to the database when (e.g.) the `--add`
    keyword argument is being used.
    """

    def get_command(self):
        """Get the command tested by this class."""
        return EditCommand

    @staticmethod
    def _assert(changes: bool, logs: list = None, label: str = 'dummy'):
        """Common assertion utility method."""
        if changes:
            if logs is not None:
                assert ('cobib.commands.edit', 20, f"'{label}' was successfully edited.") in logs

            with open('/tmp/cobib_test/database.yaml', 'r') as file:
                lines = file.readlines()
                dummy_start = lines.index('dummy:\n')
                assert dummy_start > 0
                assert lines[dummy_start-1] == '---\n'
                assert lines[dummy_start+1] == '  ENTRYTYPE: article\n'
                assert lines[dummy_start+2] == '  ID: dummy\n'
                assert lines[dummy_start+3] == '...\n'
        else:
            if logs is not None:
                assert ('cobib.commands.edit', 20, 'No changes detected.') in logs

    @pytest.mark.parametrize(['setup'], [
        [{'git': False}],
        [{'git': True}],
    ], indirect=['setup'])
    @pytest.mark.parametrize(['args', 'changes'], [
        [['einstein'], False],
        [['-a', 'dummy'], True],
    ])
    def test_command(self, setup, caplog, args, changes):
        """Test the command itself."""
        git = setup.get('git', False)

        EditCommand().execute(args)

        true_log = [rec for rec in caplog.record_tuples if rec[0] == 'cobib.commands.edit']

        # check common log
        expected_log = [
            ('cobib.commands.edit', 10, 'Starting Edit command.'),
            ('cobib.commands.edit', 10, 'Creating temporary file.'),
            ('cobib.commands.edit', 10, 'Starting editor "cat".'),
            ('cobib.commands.edit', 10, 'Editor finished successfully.'),
        ]

        assert true_log[0:4] == expected_log
        self._assert(changes=changes, logs=true_log)

        if git and changes:
            # assert the git commit message
            self.assert_git_commit_message('edit', {'label': args[-1], 'add': '-a' in args})

    def test_ignore_add_if_label_exists(self, setup, caplog):
        """Test that the `add` argument is ignored if the label already exists."""
        EditCommand().execute(['-a', 'einstein'])
        assert ('cobib.commands.edit', 30,
                "Entry 'einstein' already exists! Ignoring the `--add` argument.") \
            in caplog.record_tuples

    def test_warning_missing_label(self, setup, caplog):
        """Test warning for missing label."""
        EditCommand().execute(['dummy'])
        assert ('cobib.commands.edit', 40,
                "No entry with the label 'dummy' could be found.\n"
                "Use `--add` to add a new entry with this label.") \
            in caplog.record_tuples

    @pytest.mark.parametrize(['setup'], [
        [{'git': False}],
    ], indirect=['setup'])
    def test_cmdline(self, setup, monkeypatch):
        """Test the command-line access of the command."""
        self.run_module(monkeypatch, 'main', ['cobib', 'edit', '-a', 'dummy'])
        self._assert(changes=True, logs=None)

    def test_tui(self, setup):
        """Test the TUI access of the command."""
        def assertion(screen, logs, **kwargs):
            true_log = [log for log in logs if log[0] == 'cobib.commands.edit']
            self._assert(changes=False, logs=true_log)

        self.run_tui('e', assertion, {})
