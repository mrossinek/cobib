"""CoBib command-line test class."""

import runpy


class CmdLineTest:
    """A command-line test runs CoBib's command-line interface."""

    @staticmethod
    def run_module(monkeypatch, main, sys_argv):
        """Gets the CoBib runtime module after monkeypatching sys.argv."""
        monkeypatch.setattr('sys.argv', sys_argv)
        module = runpy.run_module('cobib')
        module.get(main)()
