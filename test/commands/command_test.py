"""CoBib command test class."""
# pylint: disable=no-self-use

from abc import abstractmethod

import json
import logging
import os
import shlex
import subprocess

from shutil import copyfile, rmtree

from test.cmdline_test import CmdLineTest

import pytest

from cobib.config import config
from cobib.database import Database
from cobib.logging import log_to_stream


class CommandTest(CmdLineTest):
    """The base class for CoBib's command test classes."""

    @abstractmethod
    def get_command(self):
        """Get the command tested by this class."""

    @abstractmethod
    def test_command(self):
        """Test the command itself."""

    @pytest.fixture
    def setup(self, request):
        """Setup."""
        log_to_stream(logging.DEBUG)

        if not hasattr(request, 'param'):
            # use default settings
            request.param = {'git': False, 'database': True}

        # use temporary config
        config.commands.edit.editor = 'cat'
        config.commands.open.command = 'cat'
        config.database.file = '/tmp/cobib_test/database.yaml'
        config.database.git = request.param.get('git', False)

        # load database
        if request.param.get('database', True):
            os.makedirs('/tmp/cobib_test', exist_ok=True)
            copyfile('./test/example_literature.yaml', '/tmp/cobib_test/database.yaml')
            Database().read()
            if request.param.get('git', True):
                root = '/tmp/cobib_test'
                msg = 'Initial commit'
                commands = [
                    f'cd {root}',
                    'git init',
                    'git add -- database.yaml',
                    f'git commit --no-gpg-sign --quiet --message {shlex.quote(msg)}',
                ]
                os.system('; '.join(commands))

        yield request.param

        # clean up file system
        try:
            os.remove('/tmp/cobib_test/database.yaml')
            if request.param.get('git', False):
                rmtree('/tmp/cobib_test/.git')
        except FileNotFoundError:
            pass

        # clean up database
        if request.param.get('database', True):
            Database().clear()

        # clean up config
        config.defaults()

    @staticmethod
    def assert_git_commit_message(command, args=None):
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

        if args is not None:
            # assert args
            args = json.dumps(args, indent=2, default=str)
            for ref, truth in zip(args.split('\n'), message[2:]):
                assert ref == truth

    def test_handle_argument_error(self, caplog):
        """Test handling of ArgumentError."""
        command_cls = self.get_command()
        command_cls().execute(['--dummy'])
        name = command_cls.name
        for (source, level, message) in caplog.record_tuples:
            if (f'cobib.commands.{name}', logging.ERROR) == (source, level) and \
                    f'Error: {name}: error:' in message:
                break
        else:
            pytest.fail('No Error logged from ArgumentParser.')
