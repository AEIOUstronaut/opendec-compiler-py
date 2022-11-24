"""Unit tests for the OpenDec parser Node objects."""


import os.path
import pytest
import sys
from typing import Union

# Required for local imports.
ROOTDIR = os.path.abspath(os.path.join(__file__, "..", ".."))
if ROOTDIR not in sys.path:
    sys.path.insert(0, ROOTDIR)

# Local imports should go under this comment.
from components.node import (
    Node,
    CommandNode,
    EofNode,
    PhonemeNode,
    VoiceNode,
)
from components.position import Position


class TestNode:
    @pytest.fixture(autouse=True)
    def __setup_and_teardown(self) -> None:
        self.position = Position("test_node")

    def test_node(self) -> None:
        node = Node(self.position)

        with pytest.raises(NotImplementedError):
            node == 0
        with pytest.raises(NotImplementedError):
            str(node)

    @pytest.mark.parametrize("command, parameters, context, string", [
        # Empty command.
        ("", [], [],        "[:]"),
        ("command", [], [], "[:command]"),

        # Single parameter.
        ("command", [1], [],        "[:command 1]"),
        ("command", [1.0], [],      "[:command 1.0]"),
        ("command", ["one"], [],    "[:command one]"),

        # Multiple parameters.
        ("command", [1, 1], [],         "[:command 1 1]"),
        ("command", [1, 1.0], [],       "[:command 1 1.0]"),
        ("command", [1, "one"], [],     "[:command 1 one]"),
        ("command", [1.0, 1], [],       "[:command 1.0 1]"),
        ("command", [1.0, 1.0], [],     "[:command 1.0 1.0]"),
        ("command", [1.0, "one"], [],   "[:command 1.0 one]"),
        ("command", ["one", 1], [],     "[:command one 1]"),
        ("command", ["one", 1.0], [],   "[:command one 1.0]"),
        ("command", ["one", "one"], [], "[:command one one]"),

        # Context.
        ("command", [], [CommandNode(None, "", [], [])], "[:command] { [:] }"),
        ("command", [], [PhonemeNode(None, "phoneme", 1, 1)], "[:command] { [phoneme<1,1>] }"),
        ("command", [], [
            CommandNode(None, "", [], []),
            PhonemeNode(None, "phoneme", 1, 1),
        ], "[:command] { [:] [phoneme<1,1>] }"),

        # Parameters and context.
        ("command", [1, 1.0, "one"], [
            CommandNode(None, "", [], []),
            PhonemeNode(None, "phoneme", 1, 1),
        ], "[:command 1 1.0 one] { [:] [phoneme<1,1>] }"),

    ])
    def test_command_node(
            self,
            command: str,
            parameters: list[str],
            context: list[Node],
            string: str
    ) -> None:
        node = CommandNode(self.position, command, parameters, context)
        copy_same = CommandNode(self.position, command, parameters, context)
        copy_diff = CommandNode(self.position, command + "_", parameters, context)

        assert node.command == command
        assert node.parameters == parameters
        assert node.context == context
        assert str(node) == string

        assert node == CommandNode(None, command, parameters, context)
        assert node == copy_same
        assert node != copy_diff

        assert str(node) == str(copy_same)
        assert str(node) == str(CommandNode(None, command, parameters, context))

    def test_eof_node(self) -> None:
        node = EofNode(self.position)

        assert node == EofNode(self.position)
        assert node == EofNode(None)
        assert str(node) == "<EOF>"

    @pytest.mark.parametrize("phoneme, length, pitch, string", [
        ("phoneme", 0, 0,   "[phoneme]"),
        ("phoneme", 0, 1,   "[phoneme<,1>]"),
        ("phoneme", 1, 0,   "[phoneme<1>]"),
        ("phoneme", 1.0, 0, "[phoneme<1.0>]"),
        ("phoneme", 1, 1,   "[phoneme<1,1>]"),
        ("phoneme", 1.0, 1, "[phoneme<1.0,1>]"),
    ])
    def test_phoneme_node(
            self,
            phoneme: str,
            length: Union[int, float],
            pitch: int,
            string: str
    ) -> None:
        node = PhonemeNode(self.position, phoneme, length, pitch)
        copy_same = PhonemeNode(self.position, phoneme, length, pitch)
        copy_diff = PhonemeNode(self.position, phoneme + "_", length, pitch)

        assert node.phoneme == phoneme
        assert node.length == length
        assert node.pitch == pitch
        assert str(node) == string

        assert node == PhonemeNode(None, phoneme, length, pitch)
        assert node == copy_same
        assert node != copy_diff

        assert str(node) == str(copy_same)
        assert str(node) == str(PhonemeNode(None, phoneme, length, pitch))

    @pytest.mark.parametrize("name, parameters, string", [
        ("name", {},                        "[:voice name] {}"),
        ("name", {"a": 1},                  "[:voice name] {a: 1}"),
        ("name", {"a": 1, "b": 2},          "[:voice name] {a: 1, b: 2}"),
        ("name", {"a": 1, "b": 2, "c": 3},  "[:voice name] {a: 1, b: 2, c: 3}"),
    ])
    def test_voice_node(
            self,
            name: str,
            parameters: dict[str: int],
            string: str
    ) -> None:
        node = VoiceNode(self.position, name, parameters)
        copy_same = VoiceNode(self.position, name, parameters)
        copy_diff = VoiceNode(self.position, name + "_", parameters)

        assert node.command == "voice"
        assert node.name == name
        assert node.parameters == parameters
        assert str(node) == string

        assert node == VoiceNode(None, name, parameters)
        assert node == copy_same
        assert node != copy_diff

        assert str(node) == str(copy_same)
        assert str(node) == str(VoiceNode(None, name, parameters))
