"""Functionality testing for the import function."""


import os.path
import pytest
import sys

# Required for local imports.
ROOTDIR = os.path.abspath(os.path.join(__file__, "..", ".."))
if ROOTDIR not in sys.path:
    sys.path.insert(0, ROOTDIR)

# Local imports should go under this comment.
from components.lexer import Lexer
from components.node import CommandNode, PhonemeNode, VoiceNode
from components.parser import Parser
from components.processor import Processor
from components.state import State
from constants import VOICE_DEFAULTS
from utils.exceptions import StateException


DIR_TEST_FILES = os.path.abspath(os.path.join("tests", "test_files"))


class Buffer(object):
    def __init__(self) -> None:
        self.filename = "<BufferObject>"
        self.reset()

    def reset(self) -> None:
        self.buffer = ""

    def write(self, buffer: str) -> None:
        self.buffer += buffer


class TestFunctionalityImport:
    def __setup(self, source: str) -> tuple[Buffer, Processor]:
        buffer = Buffer()
        state = State("", [DIR_TEST_FILES])

        tokens = Lexer(source).get_tokens()
        nodes = Parser(tokens).get_nodes()
        processor = Processor(nodes, state, writer=buffer)

        return (buffer, processor)

    @pytest.mark.parametrize("count", range(1, 6))
    def test_import_command(self, count: int) -> None:
        source = "[:import import_command.opendec]" * count
        buffer, processor = self.__setup(source)
        processor.process()

        assert buffer.buffer == "[:comma 50]" * count

    @pytest.mark.parametrize("count", range(1, 6))
    def test_import_phoneme(self, count: int) -> None:
        source = "[:import import_phoneme.opendec]" * count
        buffer, processor = self.__setup(source)
        processor.process()

        assert buffer.buffer == "[_<500>][aa<500,10>][b<15>]" * count

    @pytest.mark.parametrize("count", range(1, 6))
    def test_import_phrase(self, count: int) -> None:
        source = "[:import import_phrase.opendec]" * count
        buffer, processor = self.__setup(source)
        processor.process()

        assert buffer.buffer == ""

        assert "name" in processor.state.phrases
        assert "name" not in processor.state.sounds
        assert "name" not in processor.state.voices

        assert len(processor.state.phrases) == 1
        assert len(processor.state.sounds) == 0
        assert len(processor.state.voices) == 0

        assert processor.state.phrases["name"] == [
            PhonemeNode(None, "aa", 500, 0),
            CommandNode(None, "bpm", [60], []),
            PhonemeNode(None, "aa", 0.5, 0),
        ]

    def test_import_registration_conflict(self) -> None:
        source = "[:import import_phrase.opendec][:import import_sound.opendec]"
        _, processor = self.__setup(source)

        with pytest.raises(StateException):
            processor.process()

        source = "[:import import_sound.opendec][:import import_phrase.opendec]"
        _, processor = self.__setup(source)

        with pytest.raises(StateException):
            processor.process()

    @pytest.mark.parametrize("count", range(1, 6))
    def test_import_sound(self, count: int) -> None:
        source = "[:import import_sound.opendec]" * count
        buffer, processor = self.__setup(source)
        processor.process()

        assert buffer.buffer == ""

        assert "name" not in processor.state.phrases
        assert "name" in processor.state.sounds
        assert "name" not in processor.state.voices

        assert len(processor.state.phrases) == 0
        assert len(processor.state.sounds) == 1
        assert len(processor.state.voices) == 0

        assert processor.state.sounds["name"] == [
            PhonemeNode(None, "b", 0, 0),
            PhonemeNode(None, "aa", 0, 0),
            PhonemeNode(None, "b", 0, 0),
        ]

    @pytest.mark.parametrize("count", range(1, 6))
    def test_import_voice(self, count: int) -> None:
        source = "[:import import_voice.opendec]" * count
        buffer, processor = self.__setup(source)
        processor.process()

        assert buffer.buffer == ""

        assert "name" not in processor.state.phrases
        assert "name" not in processor.state.sounds
        assert "name" in processor.state.voices

        assert len(processor.state.phrases) == 0
        assert len(processor.state.sounds) == 0
        assert len(processor.state.voices) == 1

        expected = VOICE_DEFAULTS.copy()
        expected["sx"] = 0
        assert processor.state.voices["name"] == expected
