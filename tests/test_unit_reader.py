import itertools
import os
import os.path
import pytest
import sys

# Required for local imports.
ROOTDIR = os.path.abspath(os.path.join(__file__, "..", ".."))
if ROOTDIR not in sys.path:
    sys.path.insert(0, ROOTDIR)

# Local import should go under this comment.
from components.position import Position
from components.reader import Reader
from constants import WHITESPACE
from utils.exceptions import ReaderException


SOURCE_FILE = os.path.abspath("test_unit_reader_source.opendec")
SOURCE_TEXT = "one\ntwo\nthree"

SOURCES = [SOURCE_TEXT, SOURCE_FILE]
WHITESPACE_COMBOS = []
for r in range(len(WHITESPACE)):
    combos = itertools.combinations(WHITESPACE, r)
    WHITESPACE_COMBOS += ["".join(combo) for combo in combos]


class TestReader:
    @pytest.fixture(autouse=True)
    def __create_clean_readfile(self) -> None:
        with open(SOURCE_FILE, "w") as f:
            f.write(SOURCE_TEXT)

        yield

        os.remove(SOURCE_FILE)

    def __position_assert(self, pos: Position, index: int, line: int, col: int) -> None:
        assert pos.index == index
        assert pos.line == line
        assert pos.column == col

    @pytest.mark.parametrize("source", SOURCES)
    def test_init(self, source: str) -> None:
        try:
            Reader(source)
        except:
            assert False, f"Failed to initialize Reader with '{source}'"

    @pytest.mark.parametrize("source", WHITESPACE_COMBOS)
    def test_init_invalid(self, source: str) -> None:
        with pytest.raises(ReaderException):
            Reader(source)

    @pytest.mark.parametrize("source", SOURCES)
    def test_advance(self, source: str):
        reader = Reader(source)

        for i in range(len(SOURCE_TEXT)):
            assert reader.char == SOURCE_TEXT[i]
            reader.advance()

        # Test end-of-file functionality.
        for _ in range(10):
            assert reader.char == ""
            reader.advance()

    @pytest.mark.parametrize("source", SOURCES)
    def test_getpos(self, source: str) -> None:
        reader = Reader(source)

        # Initial position.
        pos = reader.getpos()
        self.__position_assert(pos, 0, 0, 0)

        # Advance a single character.
        reader.advance()
        pos = reader.getpos()
        self.__position_assert(pos, 1, 0, 1)

        # Advance until we reach a new-line character.
        for _ in range(3):
            reader.advance()

        pos = reader.getpos()
        self.__position_assert(pos, 4, 1, 0)

        # Advance until the next new-list character (and then some).
        for _ in range(5):
            reader.advance()

        pos = reader.getpos()
        self.__position_assert(pos, 9, 2, 1)
