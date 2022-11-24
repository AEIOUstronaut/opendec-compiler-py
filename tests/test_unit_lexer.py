"""Unit tests for the OpenDec Lexer."""


import os.path
import pytest
import sys

# Required for local imports.
ROOTDIR = os.path.abspath(os.path.join(__file__, "..", ".."))
if ROOTDIR not in sys.path:
    sys.path.insert(0, ROOTDIR)

# Local imports should go under this comment.
from constants import (
    SPECIAL_CHARACTERS,
    WHITESPACE,
)
from components.lexer import Lexer, Token, TokenType
from components.position import Position
from utils.exceptions import LexerException


class TestLexing:
    def __confirm_eof(self, tokens: list[Token]) -> None:
        assert tokens[-1].type == TokenType.EOF
        assert tokens[-1].value is None

    def test_init(self) -> None:
        source = "source"

        try:
            lexer = Lexer(source)
        except:
            assert False, f"Could not initialize Lexer"

        for char in source:
            lexer.reader.char == char
            lexer.reader.advance()

        assert lexer.reader.char == ""

    def test_command(self) -> None:
        source = "[:command option 1] { 1 1.0 one }"
        expected = [
            Token(TokenType.LBRACKET, "[", None),
            Token(TokenType.STRING, ":command", None),
            Token(TokenType.STRING, "option", None),
            Token(TokenType.INT, 1, None),
            Token(TokenType.RBRACKET, "]", None),
            Token(TokenType.LBRACE, "{", None),
            Token(TokenType.INT, 1, None),
            Token(TokenType.FLOAT, 1.0, None),
            Token(TokenType.STRING, "one", None),
            Token(TokenType.RBRACE, "}", None),
        ]

        tokens = Lexer(source).get_tokens()

        assert len(tokens) == len(expected) + 1
        for i in range(len(expected)):
            assert tokens[i] == expected[i]

        self.__confirm_eof(tokens)

    @pytest.mark.parametrize("source, expected", [
        # Comments only.
        ("// Single in-line comment",           []),
        ("// Multiple\n// Inline\n// Comments", []),
        ("/* Block Comment */",                 []),
        ("/* Complex * Block /* Comment */",    []),

        # Tokens with inline comments.
        ("one two //",          ["one", "two"]),
        ("one two // three",    ["one", "two"]),
        ("one two //three",     ["one", "two"]),
        ("one two// three",     ["one", "two"]),
        ("one two//three",      ["one", "two"]),

        # Tokens with block comments.
        ("one two /* three */", ["one", "two"]),
        ("one two/* three */",  ["one", "two"]),
        ("one two /*three*/",   ["one", "two"]),
        ("one two/*three*/",    ["one", "two"]),
        ("one /* two */ three", ["one", "three"]),
        ("one/* two */three",   ["one", "three"]),
        ("one/*two*/three",     ["one", "three"]),
    ])
    def test_comments(self, source: str, expected: list[str]) -> None:
        tokens = Lexer(source).get_tokens()

        assert len(tokens) == len(expected) + 1

        for i in range(len(expected)):
            assert tokens[i].type == TokenType.STRING
            assert tokens[i].value == expected[i]

        self.__confirm_eof(tokens)

    @pytest.mark.parametrize("source, expected", [
        ("0.0 0.00 0.000 0.0000 0.00000",   [0.0, 0.0, 0.0, 0.0, 0.0]),
        ("0.0 00.0 000.0 0000.0 00000.0",   [0.0, 0.0, 0.0, 0.0, 0.0]),
        ("1.0 1.00 1.000 1.0000 1.00000",   [1.0, 1.0, 1.0, 1.0, 1.0]),
        ("1.0 01.0 001.0 0001.0 00001.0",   [1.0, 1.0, 1.0, 1.0, 1.0]),
        ("0.1 0.01 0.001 0.0001 0.00001",   [0.1, 0.01, 0.001, 0.0001, 0.00001]),
        ("1.1 10.1 100.1 1000.1 10000.1",   [1.1, 10.1, 100.1, 1000.1, 10000.1]),
        ("0.1 0.2 0.3 0.4 0.5",             [0.1, 0.2, 0.3, 0.4, 0.5]),
        ("1.0 2.0 3.0 4.0 5.0",             [1.0, 2.0, 3.0, 4.0, 5.0]),
        ("1. 2. 3. 4. 5.",                  [1.0, 2.0, 3.0, 4.0, 5.0]),
    ])
    def test_float(self, source: str, expected: list[float]) -> None:
        tokens = Lexer(source).get_tokens()

        assert len(tokens) == len(expected) + 1

        for i in range(len(expected)):
            assert tokens[i].type == TokenType.FLOAT
            assert tokens[i].value == expected[i]

        self.__confirm_eof(tokens)

    @pytest.mark.parametrize("source, expected", [
        ("0 00 000 0000 00000", [0, 0, 0, 0, 0]),
        ("1 01 001 0001 00001", [1, 1, 1, 1, 1]),
        ("1 10 100 1000 10000", [1, 10, 100, 1000, 10000]),
        ("1 2 3 4 5",           [1, 2, 3, 4, 5]),
    ])
    def test_int(self, source: str, expected: list[int]) -> None:
        tokens = Lexer(source).get_tokens()

        assert len(tokens) == len(expected) + 1

        for i in range(len(expected)):
            assert tokens[i].type == TokenType.INT
            assert tokens[i].value == expected[i]

        self.__confirm_eof(tokens)

    @pytest.mark.parametrize("source", [
        # Invalid floats.
        "0..",
        "0...",
        "0.0.",
        "0.0.0",
        "0.0.0.0",
        "0.1a",
        "0.1A",
        "1.a",
        "1.A",
        "1.-",

        # Invalid ints.
        "0a",
        "0A",
        "0xa",
        "0xA",
        "0x0",
        "0-",
        "0-0",
    ])
    def test_invalid(self, source: str) -> None:
        with pytest.raises(LexerException):
            Lexer(source).get_tokens()

    def test_phoneme(self) -> None:
        source = "phoneme<1.0,01>"
        expected = [
            Token(TokenType.STRING, "phoneme", None),
            Token(TokenType.LCHEVRON, "<", None),
            Token(TokenType.FLOAT, 1.0, None),
            Token(TokenType.COMMA, ",", None),
            Token(TokenType.INT, 1, None),
            Token(TokenType.RCHEVRON, ">", None),
        ]

        tokens = Lexer(source).get_tokens()

        assert len(tokens) == len(expected) + 1
        for i in range(len(expected)):
            assert tokens[i] == expected[i]

        self.__confirm_eof(tokens)

    @pytest.mark.parametrize("source, type_", [
        (",", TokenType.COMMA),
        ("{", TokenType.LBRACE),
        ("}", TokenType.RBRACE),
        ("[", TokenType.LBRACKET),
        ("]", TokenType.RBRACKET),
        ("<", TokenType.LCHEVRON),
        (">", TokenType.RCHEVRON),
    ])
    def test_special_tokens(self, source: str, type_: TokenType) -> None:
        tokens = Lexer(source).get_tokens()

        assert len(tokens) == 2
        assert tokens[0].type == type_
        assert tokens[0].value == source

        self.__confirm_eof(tokens)

    @pytest.mark.parametrize("source, expected", [
        # Simple strings.
        ("one",     ["one"]),
        ("two",     ["two"]),
        ("three",   ["three"]),

        # Strings with whitespace separation.
        ("one two",         ["one", "two"]),
        ("one\ttwo",        ["one", "two"]),
        ("one\ntwo",        ["one", "two"]),
        ("one\rtwo",        ["one", "two"]),
        ("one\r\ntwo",      ["one", "two"]),
        ("one      two",    ["one", "two"]),
        ("  one  two  ",    ["one", "two"]),
        ("\none\ntwo\n",    ["one", "two"]),
        ("\rone\rtwo\r",    ["one", "two"]),
        ("\tone\ttwo\t",    ["one", "two"]),

        # Strings with quotations.
        ("'one' 'two'",     ["'one'", "'two'"]),
        ("\"one\" \"two\"", ["\"one\"", "\"two\""]),

        # File paths - Windows style.
        ("C:\\path\\to\\file.ext",  ["C:\\path\\to\\file.ext"]),
        ("..\\path\\to\\file.ext",  ["..\\path\\to\\file.ext"]),
        (".\\path\\to\\file.ext",   [".\\path\\to\\file.ext"]),

        # File paths - Unix style.
        ("/home/path/to/file.ext",  ["/home/path/to/file.ext"]),
        ("../path.to.file.ext",     ["../path.to.file.ext"]),
        ("./path.to.file.ext",      ["./path.to.file.ext"]),

        # Special characters.
        *[(s, [s]) for s in "!\"#$%&'()*+-./;=?@\\^_`|~"],

        # Other interesting cases.
        (".123",    [".123"]),
        ("-123",    ["-123"]),
        ("-123.0",  ["-123.0"]),
    ])
    def test_string(self, source: str, expected: list[str]) -> None:
        tokens = Lexer(source).get_tokens()

        assert len(tokens) == len(expected) + 1

        for i in range(len(expected)):
            assert tokens[i].type == TokenType.STRING
            assert tokens[i].value == expected[i]

        self.__confirm_eof(tokens)
