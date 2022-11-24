"""Unit tests for the OpenDec parser Node objects."""


import os.path
import pytest
import string
import sys

# Required for local imports.
ROOTDIR = os.path.abspath(os.path.join(__file__, "..", ".."))
if ROOTDIR not in sys.path:
    sys.path.insert(0, ROOTDIR)

# Local imports should go under this comment.
from components.position import Position


class TestPosition:
    def __position_assert(self, pos: Position, index: int, line: int, col: int) -> None:
        assert pos.index == index
        assert pos.line == line
        assert pos.column == col

    @pytest.mark.parametrize("filename", [
        "",
        "filename",
        "filename.ext",

        "./filename.ext",
        "../filename.ext",
        "directory/filename.ext",
        "./directory/filename.ext",
        "../directory/filename.ext",
        "/root/directory/filename.ext",

        ".\\filename.ext",
        "..\\filename.ext",
        "directory\\filename.ext",
        ".\\directory\\filename.ext",
        "..\\directory\\filename.ext",
        "C:\\directory\\filename.ext",
    ])
    def test_constructor(self, filename: str) -> None:
        position = Position(filename)

        assert position.filename == filename
        self.__position_assert(position, 0, 0, 0)

    def test_advance(self) -> None:
        position = Position("test_advance")
        nonewline = string.printable.replace("\n", "")

        for line in range(5):
            for i, char in enumerate(nonewline):
                position.advance(char)
                index = line * (len(nonewline) + 1) + i + 1
                self.__position_assert(position, index, line, i + 1)

            position.advance("\n")
            index = line * (len(nonewline) + 1) + i + 2
            self.__position_assert(position, index, line + 1, 0)

    def test_position_copy(self) -> None:
        # Make sure the initial copy is identical to the original.
        position = Position("test_copy")
        copy = position.copy()
        self.__position_assert(position, copy.index, copy.line, copy.column)

        # Advance the original by a non-newline character and make sure the copy
        # doesn't follow suit.
        position.advance("a")

        assert position.index != copy.index
        assert position.line == copy.line
        assert position.column != copy.column

        self.__position_assert(position, 1, 0, 1)
        self.__position_assert(copy, 0, 0, 0)

        # Advance the copy and make sure the original and copy match.
        copy.advance("a")

        assert position.index == copy.index
        assert position.line == copy.line
        assert position.column == copy.column

        self.__position_assert(position, 1, 0, 1)
        self.__position_assert(copy, 1, 0, 1)

        # Advance the original by a newline character and make sure the copy
        # doesn't follow suit.
        position.advance("\n")

        assert position.index != copy.index
        assert position.line != copy.line
        assert position.column == 0

        self.__position_assert(position, 2, 1, 0)
        self.__position_assert(copy, 1, 0, 1)

        # Advance the copy and make sure the original and copy match.
        copy.advance("\n")

        assert position.index == copy.index
        assert position.line == copy.line
        assert position.column == copy.column

        self.__position_assert(position, 2, 1, 0)
        self.__position_assert(copy, 2, 1, 0)
