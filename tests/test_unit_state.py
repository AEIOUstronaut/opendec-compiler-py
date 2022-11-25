"""Unit tests for the OpenDec parser Node objects."""


import os.path
import pytest
import sys

# Required for local imports.
ROOTDIR = os.path.abspath(os.path.join(__file__, "..", ".."))
if ROOTDIR not in sys.path:
    sys.path.insert(0, ROOTDIR)

# Local imports should go under this comment.
from components.lexer import Lexer
from components.node import Node, CommandNode, PhonemeNode, VoiceNode
from components.parser import Parser
from components.state import State
from utils.exceptions import StateException


class TestNode:
    def __parse_nodes(self, source: str) -> list[Node]:
        tokens = Lexer(source).get_tokens()
        nodes = Parser(tokens).get_nodes()

        return nodes

    def test_init(self) -> None:
        source = "./directory/base.ext"
        includes = [f"include{i}" for i in range(5)]

        state = State(source, includes)

        assert state.bpm_to_ms == 1.0
        assert state.cwd == os.path.abspath(".")
        assert state.includes == [os.path.abspath(".")] + includes

        assert state.source == os.path.abspath(source)
        assert state.compiled == os.path.abspath(os.path.join(".", "build", f"base.opendec.compiled"))
        assert state.outfile == os.path.abspath(os.path.join(".", "export", f"base.wav"))

        assert state.phrases == {}
        assert state.sounds == {}
        assert state.voices == {}

    @pytest.mark.parametrize("bpm, multiplier", [
        (30, 2000),
        (60, 1000),
        (90,  666),
        (120, 500),
        (150, 400),
        (200, 300),
        (600, 100),
    ])
    def test_bpm(self, bpm: int, multiplier: int) -> None:
        state = State("", [])
        state.set_bpm(bpm)

        assert int(state.bpm_to_ms) == multiplier

    def test_register_phrase(self):
        source = "[:phrase name] { phoneme<500,04> [:comma 50] }"
        nodes = self.__parse_nodes(source)

        state = State("", [])
        state.register(nodes[0])

        assert len(state.phrases) == 1
        assert len(state.sounds) == 0
        assert len(state.voices) == 0

        assert "name" in state.phrases
        assert state.phrases["name"] == [
            PhonemeNode(None, "phoneme", 500, 4),
            CommandNode(None, "comma", [50], [])
        ]

    def test_register_sound(self):
        source = "[:sound name] {b aa b}"
        nodes = self.__parse_nodes(source)

        state = State("", [])
        state.register(nodes[0])

        assert len(state.phrases) == 0
        assert len(state.sounds) == 1
        assert len(state.voices) == 0

        assert "name" in state.sounds
        assert state.sounds["name"] == [
            PhonemeNode(None, "b", 0, 0),
            PhonemeNode(None, "aa", 0, 0),
            PhonemeNode(None, "b", 0, 0),
        ]

    def test_register_voice(self):
        source = "[:voice name] {sx 0 hs 110 br 10}"
        nodes = self.__parse_nodes(source)

        state = State("", [])
        state.register(nodes[0])

        assert len(state.phrases) == 0
        assert len(state.sounds) == 0
        assert len(state.voices) == 1

        assert "name" in state.voices
        assert state.voices["name"] == {"sx": 0, "hs": 110, "br": 10}

    def test_no_shared_names(self):
        source = "[:sound same] {aa} [:phrase same] {aa}"
        nodes = self.__parse_nodes(source)

        state = State("", [])
        state.register(nodes[0])
        with pytest.raises(StateException):
            state.register(nodes[1])

        state = State("", [])
        state.register(nodes[1])
        with pytest.raises(StateException):
            state.register(nodes[0])

    @pytest.mark.parametrize("source", [
        "[:sound aa] {aa}",     # This is a vowel phoneme
        "[:sound b] {b}",       # This is a consonant phoneme
        "[:sound _] {_}",       # This is a symbol phoneme
        "[:phrase aa] {aa}",    # This is a vowel phoneme
        "[:phrase b] {b}",      # This is a consonant phoneme
        "[:phrase _] {_}",      # This is a symbol phoneme
        "[:voice Paul] {}",     # This is a default voice
        "[:voice Betty] {}",    # This is a default voice
    ])
    def test_invalid_names(self, source):
        nodes = self.__parse_nodes(source)
        state = State("", [])

        with pytest.raises(StateException):
            state.register(nodes[0])
