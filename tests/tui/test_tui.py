"""Tests for coBib's TUI."""
# pylint: disable=no-self-use,unused-argument,too-many-public-methods

import copy
import tempfile
from itertools import zip_longest
from pathlib import PurePath
from signal import SIGWINCH
from typing import Any, Dict, Generator, List, Set, Union

import pytest

from cobib.config import config
from cobib.database import Database
from cobib.tui import TUI, Frame, TextBuffer
from cobib.tui.state import STATE, Mode

from .. import get_resource
from ..cmdline_test import CmdLineTest
from .mock_curses import MockCursesPad
from .tui_test import TUITest


class TestTUI(CmdLineTest, TUITest):
    """Tests for coBib's TUI.

    This class derives the `tests.tui.tui_test.TUITest` as well as the
    `tests.cmdline_test.CmdLineTest` because it also ensures that the TUI can be started from the
    command-line interface.
    """

    @staticmethod
    @pytest.fixture(autouse=True)
    def setup() -> Generator[Any, None, None]:
        """Setup.

        This fixture is automatically enabled for all tests in this class.

        Yields:
            This method yields control to the actual test after which it will tear down the setup.
        """
        # pylint: disable=attribute-defined-outside-init
        config.load(get_resource("debug.py"))
        original_keydict = copy.deepcopy(TUI.KEYDICT)
        yield
        # clean up config
        config.defaults()
        STATE.reset()
        TUI.KEYDICT = copy.deepcopy(original_keydict)

    def test_colors(self, patch_curses: Any, caplog: pytest.LogCaptureFixture) -> None:
        """Test `cobib.tui.tui.TUI.colors`.

        Args:
            patch_curses: the `tests.tui.tui_test.TUITest.patch_curses` fixture.
            caplog: the built-in pytest fixture.
        """
        TUI.colors()
        assert TUI.ANSI_MAP == {
            "\x1b[30;43m": 2,
            "\x1b[34;40m": 3,
            "\x1b[31;40m": 4,
            "\x1b[37;46m": 5,
            "\x1b[37;42m": 6,
            "\x1b[37;44m": 7,
            "\x1b[37;41m": 8,
            "\x1b[37;45m": 9,
        }
        expected_log = [
            ("TUITest", 10, "start_color"),
            ("cobib.tui.tui", 10, "Initiliazing color pair 1 for top_statusbar"),
            ("TUITest", 10, "init_pair: (1, 0, 3)"),
            ("cobib.tui.tui", 10, "Adding ANSI color code for top_statusbar"),
            ("cobib.tui.tui", 10, "Initiliazing color pair 2 for bottom_statusbar"),
            ("TUITest", 10, "init_pair: (2, 0, 3)"),
            ("cobib.tui.tui", 10, "Adding ANSI color code for bottom_statusbar"),
            ("cobib.tui.tui", 10, "Initiliazing color pair 3 for search_label"),
            ("TUITest", 10, "init_pair: (3, 4, 0)"),
            ("cobib.tui.tui", 10, "Adding ANSI color code for search_label"),
            ("cobib.tui.tui", 10, "Initiliazing color pair 4 for search_query"),
            ("TUITest", 10, "init_pair: (4, 1, 0)"),
            ("cobib.tui.tui", 10, "Adding ANSI color code for search_query"),
            ("cobib.tui.tui", 10, "Initiliazing color pair 5 for cursor_line"),
            ("TUITest", 10, "init_pair: (5, 7, 6)"),
            ("cobib.tui.tui", 10, "Adding ANSI color code for cursor_line"),
            ("cobib.tui.tui", 10, "Initiliazing color pair 6 for popup_help"),
            ("TUITest", 10, "init_pair: (6, 7, 2)"),
            ("cobib.tui.tui", 10, "Adding ANSI color code for popup_help"),
            ("cobib.tui.tui", 10, "Initiliazing color pair 7 for popup_stdout"),
            ("TUITest", 10, "init_pair: (7, 7, 4)"),
            ("cobib.tui.tui", 10, "Adding ANSI color code for popup_stdout"),
            ("cobib.tui.tui", 10, "Initiliazing color pair 8 for popup_stderr"),
            ("TUITest", 10, "init_pair: (8, 7, 1)"),
            ("cobib.tui.tui", 10, "Adding ANSI color code for popup_stderr"),
            ("cobib.tui.tui", 10, "Initiliazing color pair 9 for selection"),
            ("TUITest", 10, "init_pair: (9, 7, 5)"),
            ("cobib.tui.tui", 10, "Adding ANSI color code for selection"),
        ]
        assert caplog.record_tuples == expected_log

    def test_config_color(self, patch_curses: Any, caplog: pytest.LogCaptureFixture) -> None:
        """Test `cobib.tui.tui.TUI.colors` when setting a non-default color value.

        Args:
            patch_curses: the `tests.tui.tui_test.TUITest.patch_curses` fixture.
            caplog: the built-in pytest fixture.
        """
        config.tui.colors.selection_fg = "red"
        TUI.colors()
        assert ("TUITest", 10, "init_pair: (9, 1, 5)") in caplog.record_tuples
        assert ("cobib.tui.tui", 10, "Adding ANSI color code for selection") in caplog.record_tuples

    @pytest.mark.parametrize(
        ["can_change_color"],
        [
            [False],
            [True],
        ],
    )
    def test_config_rgb_color(
        self,
        patch_curses: Any,
        caplog: pytest.LogCaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
        can_change_color: bool,
    ) -> None:
        """Test overwriting the RGB color value.

        Args:
            patch_curses: the `tests.tui.tui_test.TUITest.patch_curses` fixture.
            caplog: the built-in pytest fixture.
            monkeypatch: the built-in pytest fixture.
            can_change_color: whether `curses.can_change_color` is enabled.
        """
        monkeypatch.setattr("curses.can_change_color", lambda: can_change_color)
        config.tui.colors.white = "#AA0000"
        TUI.colors()
        if not can_change_color:
            assert (
                "cobib.tui.tui",
                30,
                "Curses cannot change the default colors. Skipping color setup.",
            ) in caplog.record_tuples
        else:
            assert ("TUITest", 10, "init_color: (7, 666, 0, 0)") in caplog.record_tuples

    def test_config_unknown_color(
        self, patch_curses: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that setting an unknown color logs a warning.

        Args:
            patch_curses: the `tests.tui.tui_test.TUITest.patch_curses` fixture.
            caplog: the built-in pytest fixture.
        """
        config.tui.colors.dummy_fg = "white"
        TUI.colors()
        assert (
            "cobib.tui.tui",
            30,
            "Detected unknown TUI color name specification: dummy",
        ) in caplog.record_tuples

    def test_bind_keys(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test `cobib.tui.tui.TUI.bind_keys`.

        Args:
            caplog: the built-in pytest fixture.
        """
        TUI.bind_keys()
        assert TUI.KEYDICT == {
            258: ("y", 1),
            259: ("y", -1),
            338: ("y", 20),
            339: ("y", -20),
            106: ("y", 1),
            107: ("y", -1),
            103: ("y", "g"),
            71: ("y", "G"),
            2: ("y", -20),
            4: ("y", 10),
            6: ("y", 20),
            21: ("y", -10),
            260: ("x", -1),
            261: ("x", 1),
            104: ("x", -1),
            108: ("x", 1),
            48: ("x", 0),
            36: ("x", "$"),
            58: "Prompt",
            47: "Search",
            63: "Help",
            97: "Add",
            100: "Delete",
            101: "Edit",
            102: "Filter",
            109: "Modify",
            111: "Open",
            113: "Quit",
            114: "Redo",
            115: "Sort",
            117: "Undo",
            118: "Select",
            119: "Wrap",
            120: "Export",
            10: "Show",
            13: "Show",
        }
        expected_log = [
            ("cobib.tui.tui", 20, "Binding key : to the Prompt command."),
            ("cobib.tui.tui", 20, "Binding key / to the Search command."),
            ("cobib.tui.tui", 20, "Binding key ? to the Help command."),
            ("cobib.tui.tui", 20, "Binding key a to the Add command."),
            ("cobib.tui.tui", 20, "Binding key d to the Delete command."),
            ("cobib.tui.tui", 20, "Binding key e to the Edit command."),
            ("cobib.tui.tui", 20, "Binding key f to the Filter command."),
            ("cobib.tui.tui", 20, "Binding key m to the Modify command."),
            ("cobib.tui.tui", 20, "Binding key o to the Open command."),
            ("cobib.tui.tui", 20, "Binding key q to the Quit command."),
            ("cobib.tui.tui", 20, "Binding key r to the Redo command."),
            ("cobib.tui.tui", 20, "Binding key s to the Sort command."),
            ("cobib.tui.tui", 20, "Binding key u to the Undo command."),
            ("cobib.tui.tui", 20, "Binding key v to the Select command."),
            ("cobib.tui.tui", 20, "Binding key w to the Wrap command."),
            ("cobib.tui.tui", 20, "Binding key x to the Export command."),
            ("cobib.tui.tui", 20, "Binding key ENTER to the Show command."),
        ]
        assert caplog.record_tuples == expected_log

    def test_config_bind_key(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test `cobib.tui.tui.TUI.bind_keys` when binding a non-default key.

        Args:
            caplog: the built-in pytest fixture.
        """
        config.tui.key_bindings.prompt = "p"
        TUI.bind_keys()
        assert ord(":") not in TUI.KEYDICT.keys()
        assert ord("p") in TUI.KEYDICT and TUI.KEYDICT[ord("p")] == "Prompt"
        assert ("cobib.tui.tui", 20, "Binding key p to the Prompt command.") in caplog.record_tuples

    def test_config_unknown_command(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test that binding an unknown command logs a warning.

        Args:
            caplog: the built-in pytest fixture.
        """
        config.tui.key_bindings.dummy = "p"
        TUI.bind_keys()
        assert (
            "cobib.tui.tui",
            30,
            'Unknown command "Dummy". Ignoring key binding.',
        ) in caplog.record_tuples

    def test_infoline(self) -> None:
        """Test `cobib.tui.tui.TUI.infoline`."""
        infoline = TUI.infoline()
        assert (
            infoline
            == "a:Add d:Delete e:Edit x:Export f:Filter ?:Help m:Modify o:Open ::Prompt q:Quit "
            "r:Redo /:Search v:Select ENTER:Show s:Sort u:Undo w:Wrap"
        )

    @pytest.mark.parametrize(
        ["attr"],
        [
            [0],
            [1],
        ],
    )
    def test_statusbar(self, attr: int, caplog: pytest.LogCaptureFixture) -> None:
        """Test `cobib.tui.tui.TUI.statusbar`.

        Args:
            attr: the attribute number to use for the printed text.
            caplog: the built-in pytest fixture.
        """
        pad = MockCursesPad()
        text = "Test statusbar text"
        TUI.statusbar(pad, text, attr)
        assert pad.lines == [text]
        expected_log = [
            ("MockCursesPad", 10, "erase"),
            ("MockCursesPad", 10, "getmaxyx"),
            ("MockCursesPad", 10, f"addnstr: 0 0 Test statusbar text -1 {attr}"),
            ("MockCursesPad", 10, "refresh: None None None None None None"),
        ]
        assert caplog.record_tuples == expected_log

    def test_init(self, patch_curses: Any, caplog: pytest.LogCaptureFixture) -> None:
        """Test `cobib.tui.tui.TUI.__init__`.

        Args:
            patch_curses: the `tests.tui.tui_test.TUITest.patch_curses` fixture.
            caplog: the built-in pytest fixture.
        """
        stdscr = MockCursesPad()
        stdscr.size = (24, 80)
        tui = TUI(stdscr, debug=True)
        assert tui.stdscr == stdscr
        assert tui.width == 80
        assert tui.height == 24
        assert tui.STATE == STATE
        assert tui.prompt_before_quit is True
        assert tui.selection == set()
        assert isinstance(tui.topbar, MockCursesPad)
        assert tui.topbar.lines[0].startswith("coBib")
        assert tui.topbar.lines[0].endswith("3 Entries")
        assert isinstance(tui.botbar, MockCursesPad)
        assert (
            tui.botbar.lines[0]
            == "a:Add d:Delete e:Edit x:Export f:Filter ?:Help m:Modify o:Open ::Prompt q:Quit "
            "r:Redo /:Search v:Select ENTER:Show s:Sort u:Undo w:Wrap"
        )
        assert isinstance(tui.prompt, MockCursesPad)
        assert isinstance(tui.viewport, Frame)
        assert tui.viewport.width == 80
        assert tui.viewport.height == 21
        expected_lines = [
            "knuthwebsite    Knuth: Computers and Typesetting",
            "latexcompanion  The \\LaTeX\\ Companion",
            'einstein        Zur Elektrodynamik bewegter K{\\"o}rper',
        ]
        for line, truth in zip_longest(expected_lines, tui.viewport.buffer.lines):
            assert line == truth.strip()
        expected_log = [
            ("cobib.tui.tui", 20, "Initializing TUI."),
            ("TUITest", 10, "curs_set: (0,)"),
            ("cobib.tui.tui", 10, "stdscr size determined to be 80x24"),
            ("cobib.tui.tui", 10, "Initializing colors."),
            ("TUITest", 10, "use_default_colors"),
            ("TUITest", 10, "start_color"),
            ("cobib.tui.tui", 10, "Initiliazing color pair 1 for top_statusbar"),
            ("TUITest", 10, "init_pair: (1, 0, 3)"),
            ("cobib.tui.tui", 10, "Adding ANSI color code for top_statusbar"),
            ("cobib.tui.tui", 10, "Initiliazing color pair 2 for bottom_statusbar"),
            ("TUITest", 10, "init_pair: (2, 0, 3)"),
            ("cobib.tui.tui", 10, "Adding ANSI color code for bottom_statusbar"),
            ("cobib.tui.tui", 10, "Initiliazing color pair 3 for search_label"),
            ("TUITest", 10, "init_pair: (3, 4, 0)"),
            ("cobib.tui.tui", 10, "Adding ANSI color code for search_label"),
            ("cobib.tui.tui", 10, "Initiliazing color pair 4 for search_query"),
            ("TUITest", 10, "init_pair: (4, 1, 0)"),
            ("cobib.tui.tui", 10, "Adding ANSI color code for search_query"),
            ("cobib.tui.tui", 10, "Initiliazing color pair 5 for cursor_line"),
            ("TUITest", 10, "init_pair: (5, 7, 6)"),
            ("cobib.tui.tui", 10, "Adding ANSI color code for cursor_line"),
            ("cobib.tui.tui", 10, "Initiliazing color pair 6 for popup_help"),
            ("TUITest", 10, "init_pair: (6, 7, 2)"),
            ("cobib.tui.tui", 10, "Adding ANSI color code for popup_help"),
            ("cobib.tui.tui", 10, "Initiliazing color pair 7 for popup_stdout"),
            ("TUITest", 10, "init_pair: (7, 7, 4)"),
            ("cobib.tui.tui", 10, "Adding ANSI color code for popup_stdout"),
            ("cobib.tui.tui", 10, "Initiliazing color pair 8 for popup_stderr"),
            ("TUITest", 10, "init_pair: (8, 7, 1)"),
            ("cobib.tui.tui", 10, "Adding ANSI color code for popup_stderr"),
            ("cobib.tui.tui", 10, "Initiliazing color pair 9 for selection"),
            ("TUITest", 10, "init_pair: (9, 7, 5)"),
            ("cobib.tui.tui", 10, "Adding ANSI color code for selection"),
            ("cobib.tui.tui", 10, "Initializing key bindings."),
            ("cobib.tui.tui", 20, "Binding key : to the Prompt command."),
            ("cobib.tui.tui", 20, "Binding key / to the Search command."),
            ("cobib.tui.tui", 20, "Binding key ? to the Help command."),
            ("cobib.tui.tui", 20, "Binding key a to the Add command."),
            ("cobib.tui.tui", 20, "Binding key d to the Delete command."),
            ("cobib.tui.tui", 20, "Binding key e to the Edit command."),
            ("cobib.tui.tui", 20, "Binding key f to the Filter command."),
            ("cobib.tui.tui", 20, "Binding key m to the Modify command."),
            ("cobib.tui.tui", 20, "Binding key o to the Open command."),
            ("cobib.tui.tui", 20, "Binding key q to the Quit command."),
            ("cobib.tui.tui", 20, "Binding key r to the Redo command."),
            ("cobib.tui.tui", 20, "Binding key s to the Sort command."),
            ("cobib.tui.tui", 20, "Binding key u to the Undo command."),
            ("cobib.tui.tui", 20, "Binding key v to the Select command."),
            ("cobib.tui.tui", 20, "Binding key w to the Wrap command."),
            ("cobib.tui.tui", 20, "Binding key x to the Export command."),
            ("cobib.tui.tui", 20, "Binding key ENTER to the Show command."),
            ("cobib.tui.tui", 10, "Initializing global State"),
            ("cobib.tui.tui", 10, "Populating top status bar."),
            ("cobib.tui.tui", 10, "Populating bottom status bar."),
            ("cobib.tui.tui", 10, "Initializing viewport with Frame"),
            ("cobib.tui.tui", 10, "Populating viewport buffer."),
        ]
        assert [
            record for record in caplog.record_tuples if record[0] in ("cobib.tui.tui", "TUITest")
        ] == expected_log

    def test_resize(self, patch_curses: Any, caplog: pytest.LogCaptureFixture) -> None:
        """Test `cobib.tui.tui.TUI.resize_handler`.

        Args:
            patch_curses: the `tests.tui.tui_test.TUITest.patch_curses` fixture.
            caplog: the built-in pytest fixture.
        """
        stdscr = MockCursesPad()
        stdscr.size = (24, 80)
        tui = TUI(stdscr, debug=True)
        caplog.clear()

        tui.height, tui.width = (12, 70)
        tui.resize_handler(None, None)
        assert tui.width == 70
        assert tui.height == 12
        assert tui.topbar.size[1] == 70  # type: ignore
        assert tui.botbar.size[1] == 70  # type: ignore
        assert tui.prompt.size[1] == 70  # type: ignore
        expected_log = [
            ("TUITest", 10, "resize_term"),
            ("MockCursesPad", 10, "clear"),
            ("MockCursesPad", 10, "refresh: None None None None None None"),
            ("MockCursesPad", 10, "resize: 1 70"),
            ("MockCursesPad", 10, "erase"),
            ("MockCursesPad", 10, "getmaxyx"),
            ("MockCursesPad", 10, "addnstr: 0 0 coBib VERSION - 3 Entries 69 0"),  # will be skipped
            ("MockCursesPad", 10, "refresh: None None None None None None"),
            ("MockCursesPad", 10, "refresh: None None None None None None"),
            ("MockCursesPad", 10, "resize: 1 70"),
            ("MockCursesPad", 10, "mvwin: 10 0"),
            ("MockCursesPad", 10, "erase"),
            ("MockCursesPad", 10, "getmaxyx"),
            (
                "MockCursesPad",
                10,
                "addnstr: 0 0 a:Add d:Delete e:Edit x:Export f:Filter ?:Help m:Modify o:Open "
                "::Prompt q:Quit r:Redo /:Search v:Select ENTER:Show s:Sort u:Undo w:Wrap 69 0",
            ),
            ("MockCursesPad", 10, "refresh: None None None None None None"),
            ("MockCursesPad", 10, "refresh: None None None None None None"),
            ("MockCursesPad", 10, "resize: 1 70"),
            ("MockCursesPad", 10, "refresh: 0 0 11 0 12 69"),
            ("MockCursesPad", 10, "refresh: 0 0 1 0 9 69"),
        ]
        for log, truth in zip(
            expected_log,
            [
                record
                for record in caplog.record_tuples
                if record[0] in ("MockCursesPad", "TUITest")
            ],
        ):
            assert log[0] == truth[0]
            assert log[1] == truth[1]
            if truth[2].startswith("addnstr: 0 0 coBib v"):
                # skip version-containing log
                continue
            assert log[2] == truth[2]

    def test_resize_live(self) -> None:
        """Test `cobib.tui.tui.TUI.resize_handler` while the TUI is actually running."""

        def assertion(screen, logs, **kwargs):  # type: ignore
            expected_screen = [
                "knuthwebsite    Knuth: Computers and Typesett",
                r"latexcompanion  The \LaTeX\ Companion",
                "einstein        Zur Elektrodynamik bewegter K",
                "",
                "",
                "",
                "",
                "a:Add d:Delete e:Edit x:Export f:Filter ?:He",
            ]
            for line, truth in zip(expected_screen, screen.display[1:]):
                assert line == truth.strip()

            expected_log = [
                ("cobib.tui.tui", 10, "Handling resize event."),
                ("cobib.tui.tui", 10, "New stdscr dimension determined to be 45x10"),
            ]
            assert all(log in logs for log in expected_log)

        self.run_tui([SIGWINCH], assertion, {})

    def test_help(self, patch_curses: Any, caplog: pytest.LogCaptureFixture) -> None:
        # pylint: disable=consider-using-f-string
        """Test `cobib.tui.tui.TUI.help`.

        Args:
            patch_curses: the `tests.tui.tui_test.TUITest.patch_curses` fixture.
            caplog: the built-in pytest fixture.
        """
        stdscr = MockCursesPad()
        stdscr.size = (24, 80)
        tui = TUI(stdscr, debug=True)
        caplog.clear()

        tui.help()
        expected_log = [
            ("cobib.tui.tui", 10, "Help command triggered."),
            ("cobib.tui.tui", 10, "Generating help text."),
            ("MockCursesPad", 10, "erase"),
            ("MockCursesPad", 10, "refresh: 0 0 1 0 22 80"),
            ("MockCursesPad", 10, "resize: 21 80"),
            ("MockCursesPad", 10, "addstr: 1 1                              coBib TUI Help"),
            ("MockCursesPad", 10, "addstr: 2 1   Key    Command  Description"),
            ("MockCursesPad", 10, "bkgd:   (6,)"),
            ("MockCursesPad", 10, "box"),
            ("MockCursesPad", 10, "refresh: 0 0 1 0 22 80"),
            ("MockCursesPad", 10, "getch"),
            ("MockCursesPad", 10, "clear"),
            ("cobib.tui.tui", 10, "Handling resize event."),
        ]
        inv_keys = {}
        for key, cmd in TUI.KEYDICT.items():
            if cmd in TUI.HELP_DICT:
                inv_keys[cmd] = "ENTER" if key in (10, 13) else chr(key)
        for idx, (cmd, desc) in enumerate(TUI.HELP_DICT.items()):
            expected_log.insert(
                -6,
                (
                    "MockCursesPad",
                    10,
                    f"addstr: {3+idx} 1 "
                    + "{:^8} {:<8} {}".format(
                        "[" + config.tui.key_bindings[cmd.lower()] + "]", cmd + ":", desc
                    ),
                ),
            )
        for log, truth in zip(
            expected_log,
            [
                record
                for record in caplog.record_tuples
                if record[0] in ("MockCursesPad", "cobib.tui.tui")
            ],
        ):
            assert log == truth

    def test_help_live(self) -> None:
        """Test `cobib.tui.tui.TUI.help` while the TUI is actually running."""

        def assertion(screen, logs, **kwargs):  # type: ignore
            # pylint: disable=consider-using-f-string
            header_check = ["coBib TUI Help" in line for line in screen.display]
            assert any(header_check)
            offset = header_check.index(True)
            for cmd, desc in TUI.HELP_DICT.items():
                assert any(
                    "{:<8} {}".format(cmd + ":", desc) in line
                    for line in screen.display[2 + offset : 19 + offset]
                )

        self.run_tui("?", assertion, {})

    def test_help_no_artifacts(self) -> None:
        """Test that the help popup leaves no rendering artifacts behind."""

        def assertion(screen, logs, **kwargs):  # type: ignore
            expected_lines = [
                "knuthwebsite    Knuth: Computers and Typesetting",
                "latexcompanion  The \\LaTeX\\ Companion",
                'einstein        Zur Elektrodynamik bewegter K{\\"o}rper',
            ]
            for line, truth in zip_longest(expected_lines, screen.display[1:4]):
                assert line == truth.strip()
            for line in range(5, 22):
                assert screen.display[line].strip() == ""

        self.run_tui("?q", assertion, {})

    @pytest.mark.parametrize(
        ["selection"],
        [
            [set()],
            [{"knuthwebsite"}],
        ],
    )
    def test_select(
        self, patch_curses: Any, caplog: pytest.LogCaptureFixture, selection: Set[str]
    ) -> None:
        """Test `cobib.tui.tui.TUI.select`.

        Args:
            patch_curses: the `tests.tui.tui_test.TUITest.patch_curses` fixture.
            caplog: the built-in pytest fixture.
            selection: the set of selected labels.
        """
        stdscr = MockCursesPad()
        stdscr.size = (24, 80)
        tui = TUI(stdscr, debug=True)
        tui.selection = copy.deepcopy(selection)
        caplog.clear()

        tui.select()
        assert tui.selection == (set() if selection else {"knuthwebsite"})
        expected_log = [
            ("cobib.tui.tui", 10, "Select command triggered."),
            ("cobib.tui.frame", 10, 'Obtaining current label "under" cursor.'),
            ("cobib.tui.frame", 10, 'Current label at "0" is "knuthwebsite".'),
        ]
        if selection:
            expected_log.append(
                ("cobib.tui.tui", 20, "Removing 'knuthwebsite' from the selection.")
            )
        else:
            expected_log.append(("cobib.tui.tui", 20, "Adding 'knuthwebsite' to the selection."))
        assert [
            record
            for record in caplog.record_tuples
            if record[0] in ("cobib.tui.frame", "cobib.tui.tui")
        ] == expected_log

    @pytest.mark.parametrize(
        ["keys", "assertion_kwargs"],
        [
            ["v", {"current": 1, "selected": [1], "labels": ["knuthwebsite"]}],
            ["vj", {"current": 2, "selected": [1], "labels": ["knuthwebsite"]}],
            ["jvjv", {"current": 3, "selected": [2, 3], "labels": ["latexcompanion", "einstein"]}],
            ["vv", {"current": 1, "selected": [], "labels": []}],
            # ['v\n', assert_select_show_view, {'current': True}],
        ],
    )
    def test_select_list_live(self, keys: str, assertion_kwargs: Dict[str, Any]) -> None:
        """Tests the select method in the list view while the TUI is actually running.

        Args:
            keys: the string of keys to send to the running TUI.
            assertion_kwargs: additional keyword arguments to pass to the assertion method.
        """

        def assertion(screen, logs, **kwargs):  # type: ignore
            term_width = len(screen.buffer[0])
            current = kwargs["current"]
            labels = kwargs["labels"]
            selected = kwargs["selected"]
            for sel, lab in zip(selected, labels):
                assert [c.bg for c in screen.buffer[sel].values()] == ["magenta"] * len(lab) + [
                    "cyan" if sel == current else "default"
                ] * (term_width - len(lab))
            if not selected and not labels:
                for idx in range(1, 4):
                    assert [c.bg for c in screen.buffer[idx].values()] == [
                        "cyan" if idx == current else "default"
                    ] * term_width

        self.run_tui(keys, assertion, assertion_kwargs)

    def test_select_show_live(self) -> None:
        """Tests the select method in the show view while the TUI is actually running."""

        def assertion(screen, logs, **kwargs):  # type: ignore
            expected_screen = [
                "@misc{knuthwebsite,",
                " author = {Donald Knuth},",
                " title = {Knuth: Computers and Typesetting},",
                r" url = {http://www-cs-faculty.stanford.edu/\~{}uno/abcde.html}",
                "}",
            ]
            term_width = len(screen.buffer[0])
            label_len = len("knuthwebsite")
            for idx, (line, truth) in enumerate(zip(screen.display[1:6], expected_screen)):
                if idx == 0:
                    assert [c.bg for c in screen.buffer[1].values()] == ["cyan"] * 6 + [
                        "magenta"
                    ] * label_len + ["cyan"] * (term_width - label_len - 6)
                assert line.strip() in truth.strip()

        self.run_tui("v\n", assertion, {})

    def test_select_search_live(self) -> None:
        """Tests the select method in the search view while the TUI is actually running."""

        def assertion(screen, logs, **kwargs):  # type: ignore
            expected_screen = [
                "knuthwebsite - 1 match",
                "[1]     @misc{knuthwebsite,",
                "[1]      author = {Donald Knuth},",
            ]
            term_width = len(screen.buffer[0])
            label_len = len("knuthwebsite")
            for idx, (line, truth) in enumerate(zip(screen.display[1:6], expected_screen)):
                if idx == 0:
                    assert [c.bg for c in screen.buffer[1].values()] == ["magenta"] * label_len + [
                        "cyan"
                    ] * (term_width - label_len)
                assert line.strip() in truth.strip()

        self.run_tui("v/knuth\n", assertion, {})

    @pytest.mark.parametrize(
        ["text"],
        [
            [["Some single-line dummy text."]],
            [["Some multi-line dummy text.", "This is the second line."]],
        ],
    )
    def test_prompt_print(
        self, patch_curses: Any, caplog: pytest.LogCaptureFixture, text: List[str]
    ) -> None:
        """Test `cobib.tui.tui.TUI.prompt_print`.

        Args:
            patch_curses: the `tests.tui.tui_test.TUITest.patch_curses` fixture.
            caplog: the built-in pytest fixture.
            text: the text to print to the prompt.
        """
        stdscr = MockCursesPad()
        stdscr.size = (24, 80)
        tui = TUI(stdscr, debug=True)
        caplog.clear()

        tui.prompt_print("\n".join(text))
        assert tui.prompt.lines == [text[0]]  # type: ignore
        if len(text) > 1:
            # assert popup on multi-line text messages
            assert (
                "cobib.tui.buffer",
                10,
                "Appending string to text buffer: " + "\n".join(text),
            ) in caplog.record_tuples
            assert ("cobib.tui.buffer", 10, "Create popup window.") in caplog.record_tuples

    @pytest.mark.parametrize(
        ["prompt_quit", "returned_char", "mode"],
        [
            [False, 27, Mode.LIST.value],
            [False, 27, Mode.SHOW.value],
            [False, 27, Mode.SEARCH.value],
            [True, ord("y"), Mode.LIST.value],
            [True, ord("n"), Mode.LIST.value],
        ],
    )
    def test_quit(
        self,
        patch_curses: Any,
        caplog: pytest.LogCaptureFixture,
        prompt_quit: bool,
        returned_char: int,
        mode: str,
    ) -> None:
        """Test `cobib.tui.tui.TUI.quit`.

        Args:
            patch_curses: the `tests.tui.tui_test.TUITest.patch_curses` fixture.
            caplog: the built-in pytest fixture.
            prompt_quit: whether to prompt before actually quitting.
            returned_char: the value for `tests.tui.mock_curses.MockCursesPad.returned_chars`.
            mode: the `cobib.tui.state.Mode` value.
        """
        stdscr = MockCursesPad()
        stdscr.size = (24, 80)
        config.tui.prompt_before_quit = prompt_quit
        tui = TUI(stdscr, debug=True)
        STATE.mode = mode
        caplog.clear()

        tui.prompt.returned_chars = [returned_char]  # type: ignore

        expected_log = []
        if mode == Mode.LIST.value:
            expected_log.append(("cobib.tui.tui", 10, "Quitting from lowest level."))
        else:
            expected_log.append(
                ("cobib.tui.tui", 10, "Quitting higher menu level. Falling back to list view.")
            )
        if prompt_quit:
            expected_log.append(("TUITest", 10, "curs_set: (1,)"))

        if returned_char == ord("n"):
            expected_log.append(("cobib.tui.tui", 20, "User aborted quitting."))
            expected_log.append(("TUITest", 10, "curs_set: (0,)"))

        if mode == Mode.LIST.value and returned_char != ord("n"):
            with pytest.raises(StopIteration):
                tui.quit()
        else:
            tui.quit()
        assert [
            record for record in caplog.record_tuples if record[0] in ("cobib.tui.tui", "TUITest")
        ] == expected_log

    # Most keys are difficult to test here and we assume that the breadth of this function is tested
    # by the unittests of the triggered commands. Nonetheless, we test a few special keys to ensure
    # that the method itself works roughly as intended.
    @pytest.mark.parametrize(
        ["keys"],
        [[[ord("q")]], [[ord("q"), 410]]],  # curses.KEY_RESIZE
    )
    def test_loop(
        self,
        patch_curses: Any,
        caplog: pytest.LogCaptureFixture,
        keys: Union[str, List[List[int]]],
    ) -> None:
        """Test `cobib.tui.tui.TUI.loop`.

        Args:
            patch_curses: the `tests.tui.tui_test.TUITest.patch_curses` fixture.
            caplog: the built-in pytest fixture.
            keys: the keys to send to the TUI.
        """
        stdscr = MockCursesPad()
        stdscr.size = (24, 80)
        stdscr.returned_chars = keys  # type: ignore
        config.tui.prompt_before_quit = False
        tui = TUI(stdscr, debug=True)
        # we expect normal execution
        tui.loop(debug=True)
        # minimal assertions
        for key in keys:
            assert ("cobib.tui.tui", 10, f"Key press registered: {key}") in caplog.record_tuples
        assert caplog.record_tuples[-2] == ("cobib.tui.tui", 10, "Quitting from lowest level.")
        assert caplog.record_tuples[-1] == ("cobib.tui.tui", 10, "Stopping key event loop.")

    def test_loop_inactive_commands(
        self, patch_curses: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that inactive commands are not triggered during the TUI loop.

        Args:
            patch_curses: the `tests.tui.tui_test.TUITest.patch_curses` fixture.
            caplog: the built-in pytest fixture.
        """
        stdscr = MockCursesPad()
        stdscr.size = (24, 80)
        stdscr.returned_chars = [ord("q"), ord("\n")]
        config.tui.prompt_before_quit = False
        tui = TUI(stdscr, debug=True)
        tui.STATE.inactive_commands = ["Show"]
        # we expect normal execution
        tui.loop(debug=True)
        # minimal assertions
        assert (
            "cobib.commands.show",
            10,
            "Show command triggered from TUI.",
        ) not in caplog.record_tuples
        for key in stdscr.returned_chars:
            assert ("cobib.tui.tui", 10, f"Key press registered: {key}") in caplog.record_tuples
        assert caplog.record_tuples[-2] == ("cobib.tui.tui", 10, "Quitting from lowest level.")
        assert caplog.record_tuples[-1] == ("cobib.tui.tui", 10, "Stopping key event loop.")

    @pytest.mark.parametrize(
        ["keys", "expected"],
        [
            [["t", "e", "s", "t", "\n"], "test"],  # normal Enter
            [["t", "e", "s", "t", 27, None, -1], ""],  # Escape
            [["t", "e", 27, None, 68, "s", "t", "\n"], "tst"],  # left arrow
            [
                ["t", "e", 27, None, 68, 27, None, 67, "s", "t", "\n"],
                "test",
            ],  # left and right arrow
            [["t", "e", 127, "s", "t", "\n"], "tst"],  # internal Backspace
            [[127, 127], ""],  # Backspace until prompt is empty
        ],
    )
    def test_prompt_handler(
        self, patch_curses: Any, keys: List[Union[int, str]], expected: str
    ) -> None:
        """Test `cobib.tui.tui.TUI.prompt_handler`.

        Args:
            patch_curses: the `tests.tui.tui_test.TUITest.patch_curses` fixture.
            keys: the keys to send to the prompt handler.
            expected: the expected string to be returned from the prompt handler.
        """
        stdscr = MockCursesPad()
        stdscr.size = (24, 80)
        config.tui.prompt_before_quit = False
        tui = TUI(stdscr, debug=True)
        tui.prompt.returned_chars = [  # type: ignore
            ord(k) if isinstance(k, str) else k for k in reversed(keys)
        ]
        command = tui.prompt_handler("")
        assert command == expected

    @pytest.mark.parametrize(
        ["keys", "assertion_kwargs"],
        [
            ["x", {"contents": ":export"}],
            [":", {"contents": ":"}],
            [":" + 100 * "j", {"contents": "j" * 79}],  # regression-test against #48
        ],
    )
    def test_prompt_live(self, keys: str, assertion_kwargs: Dict[str, str]) -> None:
        """Test `cobib.tui.tui.TUI.prompt_handler` while the TUI is actually running.

        Args:
            keys: the string of keys to send to the running TUI.
            assertion_kwargs: additional keyword arguments to pass to the assertion method.
        """

        def assertion(screen, logs, **kwargs):  # type: ignore
            assert screen.display[-1].strip() == kwargs["contents"]

        self.run_tui(keys, assertion, assertion_kwargs)

    def test_execute_command(self) -> None:
        """Test `cobib.tui.tui.TUI.execute_command`."""
        pytest.skip("This method is tested implicitly by the test.commands.*.test_tui methods.")

    @pytest.mark.parametrize(
        ["keys", "assertion_kwargs"],
        [
            # vertical scrolling
            ["G", {"update": 20, "direction": "y"}],
            ["Gg", {"update": 0, "direction": "y"}],
            ["j", {"update": 1, "direction": "y"}],
            ["jjk", {"update": 1, "direction": "y"}],
            # assert scrolloff value of `3` is respected
            ["".join(["j"] * 20), {"update": 17, "direction": "y"}],
            ["".join(["j"] * 21), {"update": 18, "direction": "y"}],
            ["".join(["j"] * 22), {"update": 19, "direction": "y"}],
            ["G" + "".join(["k"] * 20), {"update": 3, "direction": "y"}],
            ["G" + "".join(["k"] * 21), {"update": 2, "direction": "y"}],
            ["G" + "".join(["k"] * 22), {"update": 1, "direction": "y"}],
            # horizontal scrolling
            ["l", {"update": 1, "direction": "x"}],
            ["llh", {"update": 1, "direction": "x"}],
            ["$", {"update": 23, "direction": "x"}],
            ["$0", {"update": 0, "direction": "x"}],
        ],
    )
    def test_scroll_live(self, keys: str, assertion_kwargs: Dict[str, Union[int, str]]) -> None:
        """Test scrolling while the TUI is actually running.

        Args:
            keys: the string of keys to send to the running TUI.
            assertion_kwargs: additional keyword arguments to pass to the assertion method.
        """

        def assertion(screen, logs, **kwargs):  # type: ignore
            direction = kwargs["direction"]
            update = kwargs["update"]
            term_width = len(screen.buffer[0])

            if direction == "y" or update == 0:
                assert [c.fg for c in screen.buffer[1 + update].values()] == ["white"] * term_width
                assert [c.bg for c in screen.buffer[1 + update].values()] == ["cyan"] * term_width
            elif direction == "x":
                # TODO: figure out how (or if) to actually use the update information
                assert [c.fg for c in screen.buffer[1].values()] == ["white"] * term_width
                assert [c.bg for c in screen.buffer[1].values()] == ["cyan"] * term_width

        # overwrite database
        config.database.file = get_resource("scrolling_database.yaml", "tui")
        try:
            Database().read()
            self.run_tui(keys, assertion, assertion_kwargs)
        finally:
            Database().clear()

    @pytest.mark.parametrize(
        ["keys", "assertion_kwargs"],
        [
            ["w", {"state": True}],
            ["ww", {"state": False}],
        ],
    )
    def test_wrap_live(self, keys: str, assertion_kwargs: Dict[str, bool]) -> None:
        """Test wrapping while the TUI is actually running.

        Args:
            keys: the string of keys to send to the running TUI.
            assertion_kwargs: additional keyword arguments to pass to the assertion method.
        """

        def assertion(screen, logs, **kwargs):  # type: ignore
            state = kwargs["state"]
            if state:
                assert screen.display[2][:2] == TextBuffer.INDENT + " "
            else:
                assert screen.display[1][:2] == "kn"

        self.run_tui([SIGWINCH] + list(keys), assertion, assertion_kwargs)  # type: ignore

    @pytest.mark.parametrize(
        ["kwargs"],
        [
            [[]],
            [["-l", str(PurePath(tempfile.gettempdir()) / "cobib_test.log")]],
        ],
    )
    def test_cmdline(self, monkeypatch: pytest.MonkeyPatch, kwargs: List[str]) -> None:
        """Test the command-line access of the TUI.

        Args:
            monkeypatch: the built-in pytest fixture.
            kwargs: the additional arguments to pass to the command line call.
        """
        monkeypatch.setattr("cobib.tui.tui", lambda: None)
        self.run_module(monkeypatch, "main", ["cobib"] + kwargs)
