"""Tests for coBib's TUI Frame."""

import re
from typing import Any, Generator, List, Optional, Set, Tuple, Union

import pytest

from cobib.config import config
from cobib.tui import TUI, Frame, Mode, State
from cobib.tui.buffer import TextBuffer
from cobib.tui.state import STATE

from .. import get_resource
from .mock_curses import MockCursesPad
from .mock_tui import MockTUI


class TestTextFrame:
    """Tests for coBib's Frame."""

    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch: pytest.MonkeyPatch) -> Generator[Any, None, None]:
        """Setup.

        This fixture is automatically enabled for all tests in this class.

        Args:
            monkeypatch: the built-in pytest fixture.
        """
        # pylint: disable=attribute-defined-outside-init
        monkeypatch.setattr("curses.newpad", lambda *args: MockCursesPad())
        self.frame = Frame(MockTUI(), 10, 20)  # type: ignore
        yield
        STATE.reset()

    def test_clear(self) -> None:
        """Test `cobib.tui.frame.Frame.clear`."""
        self.frame.buffer.lines = ["test"]
        self.frame.clear()
        assert self.frame.buffer.lines == []
        assert self.frame.buffer.height == 0
        assert self.frame.buffer.width == 0
        assert self.frame.buffer.wrapped is False
        old_buffer, old_state = self.frame.history[0]
        assert old_buffer.lines == ["test"]
        assert isinstance(old_state, State)

    @pytest.mark.parametrize(
        ["lines", "selection", "mode"],
        [
            [["Label0  Title0 by Author0"], set(), Mode.LIST.value],
            [["\x1b[37;45mLabel0\x1b[0m  Title0 by Author0"], set(), Mode.LIST.value],
            [["\x1b[37;45mLabel0\x1b[0m  Title0 by Author0"], {"Label0"}, Mode.LIST.value],
            [
                ["\x1b[34;40mLabel0\x1b[0m - 1 match", "[1]    Some matched text."],
                set(),
                Mode.SEARCH.value,
            ],
            [
                [
                    "\x1b[37;45m\x1b[34;40mLabel0\x1b[0m\x1b[0m - 1 match",
                    "[1]    Some matched text.",
                ],
                set(),
                Mode.SEARCH.value,
            ],
            [
                [
                    "\x1b[37;45m\x1b[34;40mLabel0\x1b[0m\x1b[0m - 1 match",
                    "[1]    Some matched text.",
                ],
                {"Label0"},
                Mode.SEARCH.value,
            ],
            [["@misc{Label0,", "author = {Nobody.}}"], set(), Mode.SHOW.value],
            [["@misc{\x1b[37;45mLabel0\x1b[0m,", "author = {Nobody.}}"], set(), Mode.SHOW.value],
            [
                ["@misc{\x1b[37;45mLabel0\x1b[0m,", "author = {Nobody.}}"],
                {"Label0"},
                Mode.SHOW.value,
            ],
        ],
    )
    def test_revert(
        self, caplog: pytest.LogCaptureFixture, lines: List[str], selection: Set[str], mode: str
    ) -> None:
        """Test `cobib.tui.frame.Frame.revert`.

        Args:
            caplog: the built-in pytest fixture.
            lines: a list of strings to place into the frame's buffer.
            selection: the set of selected labels.
            mode: the `cobib.tui.state.Mode` value.
        """
        buffer = TextBuffer()
        buffer.lines = lines
        buffer.height = len(lines)
        state = State()
        state.mode = mode
        self.frame.tui.selection = selection
        self.frame.history = [(buffer, state)]
        self.frame.revert()
        # assert buffer contents
        text = "\n".join(self.frame.buffer.lines)
        for label in selection:
            assert f"\x1b[37;45m{label}\x1b[0m" in text
        highlighted = re.findall(re.escape("\x1b[37;45m") + r"(.+)" + re.escape("\x1b[0m"), text)
        assert set(re.sub(re.escape("\x1b[0m"), "", h) for h in highlighted) == selection
        # assert log contents
        expected_log = [
            ("MockCursesPad", 10, "erase"),
            ("MockCursesPad", 10, "refresh: 0 0 1 0 10 19"),
            ("MockCursesPad", 10, f"resize: {len(lines)+1} 20"),
            ("MockCursesPad", 10, "refresh: 0 0 1 0 10 19"),
        ]
        for idx, line in enumerate(lines):
            expected_log.insert(-1, ("MockCursesPad", 10, f"addstr: {idx} 0 {line}"))
        assert [
            record
            for record in caplog.record_tuples
            if record[0] in ("MockCursesPad", "cobib.tui.frame")
        ] == expected_log

    def test_revert_empty_history(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test revert with empty history method.

        Args:
            caplog: the built-in pytest fixture.
        """
        self.frame.revert()
        expected_log = [("cobib.tui.frame", 10, "Empty frame history, nothing to revert")]
        assert [
            record for record in caplog.record_tuples if record[0] == "cobib.tui.frame"
        ] == expected_log

    def test_resize(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test `cobib.tui.frame.Frame.resize`.

        Args:
            caplog: the built-in pytest fixture.
        """
        self.frame.resize(10, 10)
        expected_log = [
            ("MockCursesPad", 10, "refresh: 0 0 1 0 10 9"),
        ]
        assert [
            record for record in caplog.record_tuples if record[0] == "MockCursesPad"
        ] == expected_log

    def test_refresh(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test `cobib.tui.frame.Frame.refresh`.

        Args:
            caplog: the built-in pytest fixture.
        """
        self.frame.height = 10
        self.frame.width = 10
        self.frame.refresh()
        expected_log = [
            ("MockCursesPad", 10, "refresh: 0 0 1 0 10 9"),
        ]
        assert [
            record for record in caplog.record_tuples if record[0] == "MockCursesPad"
        ] == expected_log

    def test_view(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test `cobib.tui.frame.Frame.view`.

        Args:
            caplog: the built-in pytest fixture.
        """
        self.frame.buffer.lines = [
            "Label0  Title0 by Author0",
            "Label1  Title1 by Author1",
            "Label2  Title2 by Author2",
            "Label3  Title3 by Author3",
            "Label4  Title4 by Author4",
        ]
        self.frame.view()
        expected_log = [
            ("MockCursesPad", 10, "erase"),
            ("MockCursesPad", 10, "refresh: 0 0 1 0 10 19"),
            ("MockCursesPad", 10, "resize: 1 20"),
            ("MockCursesPad", 10, "addstr: 0 0 Label0  Title0 by Author0"),
            ("MockCursesPad", 10, "addstr: 1 0 Label1  Title1 by Author1"),
            ("MockCursesPad", 10, "addstr: 2 0 Label2  Title2 by Author2"),
            ("MockCursesPad", 10, "addstr: 3 0 Label3  Title3 by Author3"),
            ("MockCursesPad", 10, "addstr: 4 0 Label4  Title4 by Author4"),
            ("MockCursesPad", 10, "refresh: 0 0 1 0 10 19"),
        ]
        assert [
            record for record in caplog.record_tuples if record[0] == "MockCursesPad"
        ] == expected_log

    def test_view_with_ansi_map(
        self, caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test view method with ANSI color map.

        Args:
            caplog: the built-in pytest fixture.
            monkeypatch: the built-in pytest fixture.
        """
        monkeypatch.setattr("curses.color_pair", lambda *args: args)
        # create ANSI color map for testing purposes
        config.defaults()
        ansi_map = {}
        for attr in TUI.COLOR_NAMES:
            ansi_map[config.get_ansi_color(attr)] = TUI.COLOR_NAMES.index(attr) + 1
        # populate buffer
        self.frame.buffer.lines = [
            "\x1b[31;40mLabel0\x1b[0m  Title0 by Author0",
            "\x1b[31;40mLabel1\x1b[0m  Title1 by Author1",
            "\x1b[31;40mLabel2\x1b[0m  Title2 by Author2",
            "\x1b[31;40mLabel3\x1b[0m  Title3 by Author3",
            "\x1b[31;40mLabel4\x1b[0m  Title4 by Author4",
        ]
        self.frame.view(ansi_map=ansi_map)
        expected_log = [
            ("MockCursesPad", 10, "erase"),
            ("MockCursesPad", 10, "refresh: 0 0 1 0 10 19"),
            ("MockCursesPad", 10, "resize: 1 20"),
            ("MockCursesPad", 10, "addstr: 0 0 Label0  Title0 by Author0"),
            ("MockCursesPad", 10, "chgat: 0 0 6 (4,)"),
            ("MockCursesPad", 10, "addstr: 1 0 Label1  Title1 by Author1"),
            ("MockCursesPad", 10, "chgat: 1 0 6 (4,)"),
            ("MockCursesPad", 10, "addstr: 2 0 Label2  Title2 by Author2"),
            ("MockCursesPad", 10, "chgat: 2 0 6 (4,)"),
            ("MockCursesPad", 10, "addstr: 3 0 Label3  Title3 by Author3"),
            ("MockCursesPad", 10, "chgat: 3 0 6 (4,)"),
            ("MockCursesPad", 10, "addstr: 4 0 Label4  Title4 by Author4"),
            ("MockCursesPad", 10, "chgat: 4 0 6 (4,)"),
            ("MockCursesPad", 10, "refresh: 0 0 1 0 10 19"),
        ]
        assert [
            record for record in caplog.record_tuples if record[0] == "MockCursesPad"
        ] == expected_log
        for message in ["Interpreting ANSI color codes on the fly.", "Applying ANSI color map."]:
            assert ("cobib.tui.buffer", 10, message) in caplog.record_tuples

    @pytest.mark.parametrize(
        ["initialize", "update", "repeat", "top", "cur", "msg", "scrolloff"],
        [
            [(0, 0), "g", 1, 0, 0, "Jump to top of viewport.", None],
            [(0, 0), "G", 1, 10, 19, "Jump to bottom of viewport.", None],
            [(0, 0), 1, 1, 0, 1, "Scroll viewport down by 1 lines.", None],
            [(0, 0), 1, 10, 4, 10, "Scroll viewport down by 1 lines.", None],
            [(0, 0), 10, 1, 10, 10, "Scroll viewport down by 10 lines.", None],
            [(0, 0), 20, 1, 10, 19, "Scroll viewport down by 20 lines.", None],
            [(0, 0), 1, 10, 5, 10, "Scroll viewport down by 1 lines.", 10],
            [(0, 0), 10, 1, 5, 10, "Scroll viewport down by 10 lines.", 10],
            [(0, 5), -1, 1, 0, 4, "Scroll viewport up by -1 lines.", None],
            [(0, 5), -1, 10, 0, 0, "Scroll viewport up by -1 lines.", None],
            [(0, 5), -10, 1, 0, 0, "Scroll viewport up by -10 lines.", None],
            [(10, 19), -1, 10, 6, 9, "Scroll viewport up by -1 lines.", None],
            [(10, 19), -10, 1, 0, 9, "Scroll viewport up by -10 lines.", None],
            [(10, 19), -20, 1, 0, 0, "Scroll viewport up by -20 lines.", None],
            [(10, 19), -1, 10, 4, 9, "Scroll viewport up by -1 lines.", 10],
            [(10, 19), -10, 1, 4, 9, "Scroll viewport up by -10 lines.", 10],
            [(10, 19), -20, 1, 0, 0, "Scroll viewport up by -20 lines.", 10],
        ],
    )
    # when `scrolloff` is None, the default will be used
    def test_scroll_y(
        self,
        caplog: pytest.LogCaptureFixture,
        initialize: Tuple[int, int],
        update: Union[int, str],
        repeat: int,
        top: int,
        cur: int,
        msg: str,
        scrolloff: Optional[int],
    ) -> None:
        """Test `cobib.tui.frame.Frame.scroll_y`.

        Args:
            caplog: the built-in pytest fixture.
            initialize: the initial values for `cobib.tui.state.State.top_line` and
                `cobib.tui.state.State.current_line`.
            update: the argument to send to `cobib.tui.frame.Frame.scroll_y`.
            repeat: the number of times to repeat the update.
            top: the expected value for `cobib.tui.state.State.top_line`.
            cur: the expected value for `cobib.tui.state.State.current_line`.
            msg: the expected message to be logged.
            scrolloff: the configuration value for `config.tui.scroll_offset`.
        """
        config.defaults()
        if scrolloff:
            config.tui.scroll_offset = scrolloff

        self.frame.buffer.height = 20
        self.frame.buffer.lines = ["Many lines" for _ in range(20)]

        STATE.reset()
        STATE.top_line = initialize[0]
        STATE.current_line = initialize[1]

        for _ in range(repeat):
            self.frame.scroll_y(update)
            assert ("cobib.tui.frame", 10, msg) in caplog.record_tuples
        assert STATE.top_line == top
        assert STATE.current_line == cur

    @pytest.mark.parametrize(
        ["initialize", "update", "repeat", "left", "msg"],
        [
            [0, 0, 1, 0, "Jump to first column of viewport."],
            [0, "$", 1, 70, "Jump to end of viewport."],
            [0, 1, 1, 1, "Scroll viewport horizontally by 1 columns."],
            [0, 1, 69, 69, "Scroll viewport horizontally by 1 columns."],
            [0, 1, 70, 70, "Scroll viewport horizontally by 1 columns."],
            [0, 1, 71, 70, "Scroll viewport horizontally by 1 columns."],
            [0, 10, 1, 10, "Scroll viewport horizontally by 10 columns."],
            [0, 70, 1, 70, "Scroll viewport horizontally by 70 columns."],
            [10, -1, 1, 9, "Scroll viewport horizontally by -1 columns."],
            [10, -1, 10, 0, "Scroll viewport horizontally by -1 columns."],
            [70, -1, 69, 1, "Scroll viewport horizontally by -1 columns."],
            [70, -1, 70, 0, "Scroll viewport horizontally by -1 columns."],
            [70, -1, 71, 0, "Scroll viewport horizontally by -1 columns."],
            [20, -10, 1, 10, "Scroll viewport horizontally by -10 columns."],
            [70, -70, 1, 0, "Scroll viewport horizontally by -70 columns."],
        ],
    )
    def test_scroll_x(
        self,
        caplog: pytest.LogCaptureFixture,
        initialize: int,
        update: Union[int, str],
        repeat: int,
        left: int,
        msg: str,
    ) -> None:
        """Test `cobib.tui.frame.Frame.scroll_x`.

        Args:
            caplog: the built-in pytest fixture.
            initialize: the initial value for `cobib.tui.state.State.left_edge`.
            update: the argument to send to `cobib.tui.frame.Frame.scroll_x`.
            repeat: the number of times to repeat the update.
            left: the expected value for `cobib.tui.state.State.left_edge`.
            msg: the expected message to be logged.
        """
        text = "A very long line. " * 5
        self.frame.buffer.lines = [text]
        self.frame.buffer.width = len(text)

        STATE.reset()
        STATE.left_edge = initialize

        for _ in range(repeat):
            self.frame.scroll_x(update)
            assert ("cobib.tui.frame", 10, msg) in caplog.record_tuples
        assert STATE.left_edge == left

    def test_wrap(self) -> None:
        """Test `cobib.tui.frame.Frame.wrap`."""
        self.frame.buffer.lines = ["Long line with some text" for _ in range(10)]
        self.frame.wrap()
        assert STATE.left_edge == 0
        STATE.current_line = 20
        self.frame.wrap()
        assert STATE.current_line == 9

    @pytest.mark.parametrize(
        ["lines", "cur_y", "mode"],
        [
            [["Label0  Title0 by Author0", "Label1  Title1 by Author1"], 0, Mode.LIST.value],
            [["Label0  Title0 by", "↪ Author0", "Label1  Title1 by Author1"], 1, Mode.LIST.value],
            [
                ["\x1b[34;40mLabel0\x1b[0m - 1 match", "[1]    Some matched text."],
                0,
                Mode.SEARCH.value,
            ],
            [
                ["\x1b[34;40mLabel0\x1b[0m - 1 match", "[1]    Some matched text."],
                1,
                Mode.SEARCH.value,
            ],
            [
                ["\x1b[34;40mLabel0\x1b[0m - 1 match", "[1]    Some matched", "↪ text."],
                2,
                Mode.SEARCH.value,
            ],
        ],
    )
    def test_get_current_label(
        self,
        caplog: pytest.LogCaptureFixture,
        lines: List[str],
        cur_y: int,
        mode: str,
    ) -> None:
        """Test `cobib.tui.frame.Frame.get_current_label`.

        Args:
            caplog: the built-in pytest fixture.
            lines: a list of strings to place into the frame's buffer.
            cur_y: the value for `cobib.tui.state.State.current_line`.
            mode: the `cobib.tui.state.Mode` value.
        """
        self.frame.pad.lines = lines  # type: ignore
        self.frame.pad.current_pos[0] = cur_y  # type: ignore
        STATE.mode = mode
        cur_label, label_y = self.frame.get_current_label()
        assert cur_label == "Label0"
        assert label_y == 0
        expected_log = [
            ("cobib.tui.frame", 10, 'Obtaining current label "under" cursor.'),
            ("MockCursesPad", 10, "getyx"),
            ("MockCursesPad", 10, "instr: 0, 0"),
            ("cobib.tui.frame", 10, 'Current label at "0" is "Label0".'),
        ]
        for i in range(cur_y + 1):
            expected_log.insert(2, ("MockCursesPad", 10, f"inch: {i}, 0"))
        assert [
            record
            for record in caplog.record_tuples
            if record[0] in ("MockCursesPad", "cobib.tui.frame")
        ] == expected_log

    @pytest.mark.parametrize(
        ["lines", "cur_y", "topstatus"],
        [
            [["@misc{Label0,", "author = {Nobody.}}"], 0, "coBib version - Label0"],
            [["@misc{Label0,", "author = {Nobody.}}"], 1, "coBib version - Label0"],
        ],
    )
    def test_get_current_label_show(
        self,
        caplog: pytest.LogCaptureFixture,
        lines: List[str],
        cur_y: int,
        topstatus: str,
    ) -> None:
        """Test `cobib.tui.frame.Frame.get_current_label` for `cobib.tui.state.Mode.SHOW`.

        This is separate from `test_get_current_label` because the assertions are fundamentally
        different.

        Args:
            caplog: the built-in pytest fixture.
            lines: a list of strings to place into the frame's buffer.
            cur_y: the value for `cobib.tui.state.State.current_line`.
            topstatus: the value for `cobib.tui.state.State.topstatus`.
        """
        self.frame.pad.lines = lines  # type: ignore
        self.frame.pad.current_pos[0] = cur_y  # type: ignore
        STATE.topstatus = topstatus
        STATE.mode = Mode.SHOW.value
        cur_label, label_y = self.frame.get_current_label()
        assert cur_label == "Label0"
        assert label_y == 0
        expected_log = [
            ("cobib.tui.frame", 10, 'Obtaining current label "under" cursor.'),
            ("MockCursesPad", 10, "getyx"),
            ("cobib.tui.frame", 10, 'Current label at "0" is "Label0".'),
        ]
        assert [
            record
            for record in caplog.record_tuples
            if record[0] in ("MockCursesPad", "cobib.tui.frame")
        ] == expected_log

    @pytest.mark.parametrize(
        ["selection", "mode"],
        [
            [set(), Mode.LIST.value],
            [{"knuthwebsite"}, Mode.LIST.value],
            [{"knuthwebsite", "latexcompanion"}, Mode.LIST.value],
            [set(), Mode.SEARCH.value],
            [{"knuthwebsite"}, Mode.SEARCH.value],
            [{"knuthwebsite", "latexcompanion"}, Mode.SEARCH.value],
            [set(), Mode.SHOW.value],
            [{"knuthwebsite"}, Mode.SHOW.value],
            [{"knuthwebsite", "latexcompanion"}, Mode.SHOW.value],
        ],
    )
    def test_update_list(
        self, caplog: pytest.LogCaptureFixture, selection: Set[str], mode: str
    ) -> None:
        """Test `cobib.tui.frame.Frame.update_list`.

        Args:
            caplog: the built-in pytest fixture.
            selection: the set of selected labels.
            mode: the `cobib.tui.state.Mode` value.
        """
        # load testing config
        config.load(get_resource("debug.py"))
        # trigger list update
        STATE.mode = mode
        self.frame.tui.selection = selection
        self.frame.update_list()
        # assert state
        assert STATE.mode == Mode.LIST.value
        assert STATE.current_line == 0
        assert STATE.top_line == 0
        assert STATE.left_edge == 0
        assert STATE.inactive_commands == []
        # assert buffer contents
        text = "\n".join(self.frame.buffer.lines)
        for label in selection:
            assert f"\x1b[37;45m{label}\x1b[0m" in text
        highlighted = re.findall(re.escape("\x1b[37;45m") + r"(.+)" + re.escape("\x1b[0m"), text)
        assert set(re.sub(re.escape("\x1b[0m"), "", h) for h in highlighted) == selection
        # assert log contents
        expected_log = [
            ("cobib.tui.frame", 10, "Re-populating the viewport with the list command."),
            ("MockCursesPad", 10, "erase"),
            ("MockCursesPad", 10, "refresh: 0 0 1 0 10 19"),
            ("MockCursesPad", 10, "resize: 4 54"),
            (
                "MockCursesPad",
                10,
                "addstr: 0 0 "
                + (
                    "\x1b[37;45mknuthwebsite\x1b[0m"
                    if "knuthwebsite" in selection
                    else "knuthwebsite"
                )
                + "    Knuth: Computers and Typesetting      ",
            ),
            (
                "MockCursesPad",
                10,
                "addstr: 1 0 "
                + (
                    "\x1b[37;45mlatexcompanion\x1b[0m"
                    if "latexcompanion" in selection
                    else "latexcompanion"
                )
                + r"  The \LaTeX\ Companion                 ",
            ),
            (
                "MockCursesPad",
                10,
                r"addstr: 2 0 "
                + ("\x1b[37;45meinstein\x1b[0m" if "einstein" in selection else "einstein")
                + r"        Zur Elektrodynamik bewegter K{\"o}rper",
            ),
            ("MockCursesPad", 10, "refresh: 0 0 1 0 10 19"),
        ]
        assert [
            record
            for record in caplog.record_tuples
            if record[0] in ("MockCursesPad", "cobib.tui.frame")
        ] == expected_log

    def test_update_list_out_of_view(self) -> None:
        """Test `cobib.tui.frame.Frame.update_list` when the current line is out of view."""
        # load testing config
        config.load(get_resource("debug.py"))
        # make current line be out-of-view
        self.frame.height = 2
        STATE.current_line = 3
        # trigger list update
        self.frame.update_list()
        # assert state
        assert STATE.mode == Mode.LIST.value
        assert STATE.current_line == 3
        assert STATE.top_line == 1
        assert STATE.left_edge == 0
        assert STATE.inactive_commands == []
