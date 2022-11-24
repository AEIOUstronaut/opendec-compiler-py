"""Unit tests for the OpenDec Lexer."""


import os.path
import pytest
import sys

# Required for local imports.
ROOTDIR = os.path.abspath(os.path.join(__file__, "..", ".."))
if ROOTDIR not in sys.path:
    sys.path.insert(0, ROOTDIR)

# Local imports should go under this comment.
from components.lexer import Lexer
from components.node import (
    Node,
    CommandNode,
    EofNode,
    PhonemeNode,
    VoiceNode,
)
from components.parser import Parser
from constants import PHONEMES_NOLENGTH, PHONEMES_NOPITCH
from utils.exceptions import ParserException


class TestParsing:
    def __confirm_eof(self, nodes: list[Node]) -> None:
        assert isinstance(nodes[-1], EofNode)

    def test_init(self) -> None:
        source = "source"
        tokens = Lexer(source).get_tokens()

        try:
            parser = Parser(tokens)
        except:
            assert False, f"Could not initialize Lexer"

        assert parser.index == 0
        assert parser.tokens == tokens
        assert parser.token == tokens[0]

    @pytest.mark.parametrize("source", [
        # Invalid commands.
        "[]",                   # Empty command
        "[:]",                  # Empty command
        "[1]",                  # Invalid command type
        "[1.0]",                # Invalid command type
        "[command]",            # Missing colon in command string
        "[:comma ,]",           # Invalid parameter type
        "[:comma {]",           # Invalid parameter type
        "[:comma }]",           # Invalid parameter type
        "[:comma []",           # Invalid parameter type
        "[:comma ]]",           # Invalid parameter type
        "[:comma <]",           # Invalid parameter type
        "[:comma >]",           # Invalid parameter type
        "[:comma [:comma 1]]",  # No nesting allowed
        "[:comma {}]",          # No nesting allowed
        "[",                    # Command not closed
        "[:comma",              # Command not closed
        "[:comma one",          # Command not closed
        "[:comma one two",      # Command not closed
        "[:comma one two//]",   # Command not closed
        "[:comma one two/*]*/", # Command not closed

        # Invalid phonemes.
        "phoneme<string>",  # Invalid length type
        "phoneme<,0.5>",    # Invalid pitch type
        "phoneme<,string>", # Invalid pitch type
        "phoneme<,,>",      # Invalid tokens
        "phoneme<,:>",      # Invalid tokens
        "phoneme<,{>",      # Invalid tokens
        "phoneme<,}>",      # Invalid tokens
        "phoneme<,[>",      # Invalid tokens
        "phoneme<,]>",      # Invalid tokens
        "phoneme<,<>",      # Invalid tokens
        "phoneme<,/>",      # Invalid tokens
        "phoneme<",         # Unclosed chevrons
        "phoneme<100",      # Unclosed chevrons
        "phoneme<100,",     # Unclosed chevrons
        "phoneme<100,5",    # Unclosed chevrons
        "phoneme<",         # Unclosed chevrons
        "phoneme<0.5",      # Unclosed chevrons
        "phoneme<0.5,",     # Unclosed chevrons
        "phoneme<0.5,5",    # Unclosed chevrons
        "phoneme<,//>",     # Unclosed chevrons
        "phoneme<,/*>*/",   # Unclosed chevrons

        # Invalid voices.
        "[:voice] {sx 1}",                  # Bad command parameters
        "[:voice 1] {sx 1}",                # Bad command parameters
        "[:voice 1.0] {sx 1}",              # Bad command parameters
        "[:voice name unexpected] {sx 1}",  # Bad command parameters
        "[:voice name] {1 1}",              # Invalid parameter types
        "[:voice name] {1 1.0}",            # Invalid parameter types
        "[:voice name] {1 sx}",             # Invalid parameter types
        "[:voice name] {1.0 1}",            # Invalid parameter types
        "[:voice name] {1.0 1.0}",          # Invalid parameter types
        "[:voice name] {1.0 sx}",           # Invalid parameter types
        "[:voice name] {sx 1.0}",           # Invalid parameter types
        "[:voice name] {sx sx}",            # Invalid parameter types
        "[:voice name] {,}",                # Invalid parameters
        "[:voice name] {sx}",               # Invalid parameters
        "[:voice name] {sx,}",              # Invalid parameters
        "[:voice name] {sx}",               # Invalid parameters
        "[:voice name] {sx,}",              # Invalid parameters
        "[:voice name] {sx,hs}",            # Invalid parameters
        "[:voice name] {sx 1,hs}",          # Invalid parameters
        "[:voice name] {sx 1,hs}",          # Invalid parameters
        "[:voice name] {sx 1,hs,}",         # Invalid parameters
        "[:voice 1] {",                     # Unclosed context
        "[:voice 1] {sx 1",                 # Unclosed context
        "[:voice 1] {sx 1 hs 100",          # Unclosed context
    ])
    def test_invalid(self, source: str) -> None:
        tokens = Lexer(source).get_tokens()

        with pytest.raises(ParserException):
            Parser(tokens).get_nodes()

    @pytest.mark.parametrize("source, expected", [
        # Command name only.
        ("[:command]", CommandNode(None, "command", [], [])),

        # Command with parameters only.
        ("[:command 1]",        CommandNode(None, "command", [1], [])),
        ("[:command 1.0]",      CommandNode(None, "command", [1.0], [])),
        ("[:command one]",      CommandNode(None, "command", ["one"], [])),
        ("[:command 1 1]",      CommandNode(None, "command", [1, 1], [])),
        ("[:command 1 1.0]",    CommandNode(None, "command", [1, 1.0], [])),
        ("[:command 1 one]",    CommandNode(None, "command", [1, "one"], [])),
        ("[:command 1.0 1]",    CommandNode(None, "command", [1.0, 1], [])),
        ("[:command 1.0 1.0]",  CommandNode(None, "command", [1.0, 1.0], [])),
        ("[:command 1.0 one]",  CommandNode(None, "command", [1.0, "one"], [])),
        ("[:command one 1]",    CommandNode(None, "command", ["one", 1], [])),
        ("[:command one 1.0]",  CommandNode(None, "command", ["one", 1.0], [])),
        ("[:command one one]",  CommandNode(None, "command", ["one", "one"], [])),

        # Command with context only.
        ("[:command] { phoneme }", CommandNode(None, "command", [], [
            PhonemeNode(None, "phoneme", 0, 0),
        ])),
        ("[:command] { [:command] }", CommandNode(None, "command", [], [
            CommandNode(None, "command", [], []),
        ])),
        ("[:command] { phoneme [:command] }", CommandNode(None, "command", [], [
            PhonemeNode(None, "phoneme", 0, 0),
            CommandNode(None, "command", [], []),
        ])),

        # Command with parameters and context.
        ("[:command option] { phoneme }", CommandNode(None, "command", ["option"], [
            PhonemeNode(None, "phoneme", 0, 0),
        ])),
        ("[:command option] { [:command] }", CommandNode(None, "command", ["option"], [
            CommandNode(None, "command", [], []),
        ])),
        ("[:command option] { phoneme [:command] }", CommandNode(None, "command", ["option"], [
            PhonemeNode(None, "phoneme", 0, 0),
            CommandNode(None, "command", [], []),
        ])),
    ])
    def test_command(self, source: str, expected: CommandNode):
        tokens = Lexer(source).get_tokens()
        nodes = Parser(tokens).get_nodes()

        assert len(nodes) == 2
        assert nodes[0] == expected
        self.__confirm_eof(nodes)

    @pytest.mark.parametrize("source, expected", [
        # Empty phoneme.
        ("phoneme",         PhonemeNode(None, "phoneme", 0, 0)),
        ("phoneme<>",       PhonemeNode(None, "phoneme", 0, 0)),
        ("phoneme<,>",      PhonemeNode(None, "phoneme", 0, 0)),

        # Phoneme length in milliseconds.
        ("phoneme<500>",    PhonemeNode(None, "phoneme", 500, 0)),
        ("phoneme<500,>",   PhonemeNode(None, "phoneme", 500, 0)),
        ("phoneme<500,13>", PhonemeNode(None, "phoneme", 500, 13)),

        # Phoneme length in beats.
        ("phoneme<0.5>",    PhonemeNode(None, "phoneme", 0.5, 0)),
        ("phoneme<0.5,>",   PhonemeNode(None, "phoneme", 0.5, 0)),
        ("phoneme<0.5,13>", PhonemeNode(None, "phoneme", 0.5, 13)),

        # Phoneme pitch only.
        ("phoneme<,13>",    PhonemeNode(None, "phoneme", 0, 13)),

        # Special phonemes - no length.
        *[(f"{c}",          PhonemeNode(None, c, 0, 0)) for c in PHONEMES_NOLENGTH],
        *[(f"{c}<>",        PhonemeNode(None, c, 0, 0)) for c in PHONEMES_NOLENGTH],
        *[(f"{c}<,>",       PhonemeNode(None, c, 0, 0)) for c in PHONEMES_NOLENGTH],
        *[(f"{c}<500>",     PhonemeNode(None, c, 0, 0)) for c in PHONEMES_NOLENGTH],
        *[(f"{c}<0.5>",     PhonemeNode(None, c, 0, 0)) for c in PHONEMES_NOLENGTH],
        *[(f"{c}<500,>",    PhonemeNode(None, c, 0, 0)) for c in PHONEMES_NOLENGTH],
        *[(f"{c}<0.5,>",    PhonemeNode(None, c, 0, 0)) for c in PHONEMES_NOLENGTH],

        # Special phonemes - no pitch.
        *[(f"{c}",          PhonemeNode(None, c, 0, 0)) for c in PHONEMES_NOPITCH],
        *[(f"{c}<>",        PhonemeNode(None, c, 0, 0)) for c in PHONEMES_NOPITCH],
        *[(f"{c}<,>",       PhonemeNode(None, c, 0, 0)) for c in PHONEMES_NOPITCH],
        *[(f"{c}<,13>",     PhonemeNode(None, c, 0, 0)) for c in PHONEMES_NOPITCH],
    ])
    def test_phoneme(self, source: str, expected: PhonemeNode):
        tokens = Lexer(source).get_tokens()
        nodes = Parser(tokens).get_nodes()

        assert len(nodes) == 2
        assert nodes[0] == expected
        self.__confirm_eof(nodes)

    @pytest.mark.parametrize("source, expected", [
        ("[:voice name]",   VoiceNode(None, "name", {})),
        ("[:voice name] {}",   VoiceNode(None, "name", {})),
        ("[:voice name] {sx 1}",   VoiceNode(None, "name", {"sx": 1})),
        ("[:voice name] {sx 1,}",   VoiceNode(None, "name", {"sx": 1})),
        ("[:voice name] {sx 1 hs 2}",   VoiceNode(None, "name", {"sx": 1, "hs": 2})),
        ("[:voice name] {sx 1 hs 2,}",   VoiceNode(None, "name", {"sx": 1, "hs": 2})),
        ("[:voice name] {sx 1, hs 2}",   VoiceNode(None, "name", {"sx": 1, "hs": 2})),
        ("[:voice name] {sx 1, hs 2,}",   VoiceNode(None, "name", {"sx": 1, "hs": 2})),
    ])
    def test_voice(self, source: str, expected: VoiceNode):
        tokens = Lexer(source).get_tokens()
        nodes = Parser(tokens).get_nodes()

        assert len(nodes) == 2
        assert nodes[0] == expected
        self.__confirm_eof(nodes)
