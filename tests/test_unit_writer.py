"""Unit test for Writer OpenDec object."""


import os
import os.path
import pytest
import sys

# Required for local imports.
ROOTDIR = os.path.abspath(os.path.join(__file__, "..", ".."))
if ROOTDIR not in sys.path:
    sys.path.insert(0, ROOTDIR)

# Local import should go under this comment.
from components.writer import Writer


WRITE_FILE = os.path.abspath("test_unit_reader_source.opendec")


class TestWriter:
    @pytest.fixture(autouse=True)
    def __create_clean_writefile(self) -> None:
        with open(WRITE_FILE, "w") as f:
            f.write(WRITE_FILE)

        yield

        os.remove(WRITE_FILE)

    def __check_file_content(self, content: str) -> None:
        with open(WRITE_FILE, "r") as f:
            assert f.read() == content

    def test_init(self) -> None:
        try:
            Writer(WRITE_FILE)
        except:
            assert False, f"Failed to initialize Writer with '{WRITE_FILE}'"

    def test_reset(self) -> None:
        writer = Writer(WRITE_FILE)

        for _ in range(2):
            writer.write("Hello, world!")
            with open(WRITE_FILE, "r") as f:
                assert f.read() == "Hello, world!"

            writer.reset()
            self.__check_file_content("")

    def test_write(self) -> None:
        writer = Writer(WRITE_FILE)

        writer.write("Hello")
        self.__check_file_content("Hello")

        writer.write(", world!")
        self.__check_file_content("Hello, world!")