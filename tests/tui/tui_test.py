"""coBib TUI test class."""

import curses
import fcntl
import logging
import os
import select
import signal
import struct
import tempfile
import termios
from datetime import date
from functools import partial
from pathlib import Path
from time import sleep
from typing import Any, Callable, Dict, List, Tuple, Union

import pyte
import pytest

from cobib.database import Database
from cobib.tui import TUI
from cobib.utils.logging import get_file_handler

from .mock_curses import MockCursesPad

TMP_LOGFILE = Path(tempfile.gettempdir()) / "cobib_tui_test.log"


class TUITest:
    """A TUI test runs coBib's TUI interface.

    The main part of this class is the `run_tui` method. The other methods are mainly setup and tear
    down utilities.
    """

    LOGGER = logging.getLogger("TUITest")
    """"We use a class-level LOGGER for more granular control."""

    @pytest.fixture
    def patch_curses(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Monkeypatch the `curses` module methods.

        Applies required changes to the `curses` module including set up of the `MockCursesPad`s.

        Args:
            monkeypatch: the built-in pytest fixture.
        """
        monkeypatch.setattr(
            "curses.curs_set", lambda *args: self.LOGGER.debug("curs_set: %s", args)
        )
        monkeypatch.setattr("curses.is_term_resized", lambda *args: True)
        monkeypatch.setattr("curses.resize_term", lambda *args: self.LOGGER.debug("resize_term"))
        monkeypatch.setattr(
            "curses.use_default_colors", lambda: self.LOGGER.debug("use_default_colors")
        )
        monkeypatch.setattr("curses.start_color", lambda: self.LOGGER.debug("start_color"))
        monkeypatch.setattr(
            "curses.init_pair", lambda *args: self.LOGGER.debug("init_pair: %s", args)
        )
        monkeypatch.setattr(
            "curses.init_color", lambda *args: self.LOGGER.debug("init_color: %s", args)
        )
        monkeypatch.setattr("curses.color_pair", lambda *args: args)
        monkeypatch.setattr("curses.pair_number", lambda *args: args)
        # pylint: disable=unnecessary-lambda
        monkeypatch.setattr("curses.pair_content", lambda *args: list(*args))
        monkeypatch.setattr("curses.newpad", lambda *args: MockCursesPad())
        monkeypatch.setattr("curses.newwin", lambda *args: MockCursesPad())
        monkeypatch.setattr("curses.endwin", lambda: self.LOGGER.debug("endwin"))

    @staticmethod
    def init_subprocess_coverage() -> Any:
        """Initializes the coverage reporting in a forked subprocess.

        This is required because the TUI itself will run in a forked subprocess. As such, we need to
        manually ensure that the coverage report gets updated accordingly.

        Returns:
            The coverage analyzer.
        """
        try:
            # pylint: disable=import-outside-toplevel
            import coverage
        except ImportError:
            return None
        _coveragerc = Path(__file__).parent.parent.parent / ".coveragerc"
        cov = coverage.Coverage(config_file=_coveragerc)
        cov.start()
        return cov

    @staticmethod
    def end_subprocess_coverage(*_, cov=None) -> None:  # type: ignore
        """Ends the subprocess coverage collection.

        Args:
            cov: the coverage analyzer to stop and save.
        """
        if cov is not None:
            cov.stop()
            cov.save()

    @staticmethod
    def run_tui(
        keys: Union[str, List[Union[str, signal.Signals]]],  # pylint: disable=no-member
        assertion: Callable,  # type: ignore
        assertion_kwargs: Dict,  # type: ignore
    ) -> None:
        """Spawns the coBib TUI in a forked pseudo-terminal.

        This method attaches a pyte object to the forked terminal to allow screen scraping. It also
        allows passing characters to the TUI by writing to the forked processes file descriptor.
        Furthermore, it also takes care of gathering the log, stdout/stderr and coverage information
        produced by the subprocess.

        For more information check out this
        [blog post](https://mrossinek.gitlab.io/programming/testing-tui-applications-in-python/).

        Args:
            keys: a string of characters passed to the TUI process ad verbatim.
            assertion: a callable method to assert the TUI state. This callable must take two
                       arguments: a pyte screen object and the caplog.record_tuples.
            assertion_kwargs: additional keyword arguments propagated to the assertion call.
        """
        # create pseudo-terminal
        pid, f_d = os.forkpty()

        if pid == 0:
            # setup subprocess coverage collection
            cov = TUITest.init_subprocess_coverage()
            signal.signal(signal.SIGTERM, partial(TUITest.end_subprocess_coverage, cov=cov))
            # redirect logging
            file_handler = get_file_handler(logging.DEBUG, TMP_LOGFILE)
            logging.getLogger().addHandler(file_handler)
            # child process initializes curses and spawns the TUI
            try:
                stdscr = curses.initscr()
                stdscr.resize(24, 80)
                if curses.has_colors():
                    curses.start_color()
                curses.cbreak()
                curses.noecho()
                stdscr.keypad(True)
                TUI(stdscr)
            finally:
                stdscr.keypad(False)
                curses.nocbreak()
                curses.echo()
        else:
            # parent process sets up virtual screen of identical size
            screen = pyte.Screen(80, 24)
            stream = pyte.ByteStream(screen)
            # send keys char-wise to TUI
            for key in keys:
                if key == signal.SIGWINCH:
                    sleep(0.25)
                    # resize pseudo terminal
                    buf = struct.pack("HHHH", 10, 45, 0, 0)
                    fcntl.ioctl(f_d, termios.TIOCSWINSZ, buf)
                    # overwrite screen
                    screen = pyte.Screen(45, 10)
                    stream = pyte.ByteStream(screen)
                else:
                    os.write(f_d, str.encode(str(key)))
            # scrape pseudo-terminal's screen
            while True:
                try:
                    [f_d], _, _ = select.select([f_d], [], [], 1)
                except (KeyboardInterrupt, ValueError):
                    # either test was interrupted or file descriptor of child process provides
                    # nothing to be read
                    break
                else:
                    try:
                        # scrape screen of child process
                        data = os.read(f_d, 1024)
                        stream.feed(data)
                    except OSError:
                        # reading empty
                        break
            # send SIGTERM to child process (which is necessary in order for pytest to not show
            # "failed" test cases produced by the forked child processes)
            os.kill(pid, signal.SIGTERM)
            # read the child process log file
            logs: List[Tuple[str, int, str]] = []
            print("### Captured logs from child process ###")
            with open(TMP_LOGFILE, "r", encoding="utf-8") as logfile:
                for line in logfile.readlines():
                    print(line.strip("\n"))
                    if not line.startswith(str(date.today())):
                        logs[-1] = (logs[-1][0], logs[-1][1], logs[-1][2] + line)
                        continue
                    split_line = line.split()
                    logs.append(
                        (
                            split_line[3],  # source
                            getattr(logging, split_line[2].strip("[]")),  # log level
                            " ".join(split_line[5:]),  # message
                        )
                    )
            os.remove(TMP_LOGFILE)
            # dump screen contents for easier debugging
            print("### Captured screen contents from child process ###")
            for line in screen.display:
                print(line)

            # It is necessary to read the database here, since we are in another subprocess
            Database().read()
            assertion(screen, logs, **assertion_kwargs)
