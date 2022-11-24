"""Unit tests for the OpenDec Token objects."""


import os.path
import sys

# Required for local imports.
ROOTDIR = os.path.abspath(os.path.join(__file__, "..", ".."))
if ROOTDIR not in sys.path:
    sys.path.insert(0, ROOTDIR)

# Local imports should go under this comment.
from components.token import Token, TokenType


class TestToken:
    def test_init(self):
        for ttype in TokenType:
            token = Token(ttype, "value", None)

            assert token.type == ttype
            assert token.value == "value"
            assert token.pos == None

    def test_equality(self):
        token = Token(TokenType.INT, 1, None)
        same = Token(TokenType.INT, 1, None)
        diff_val = Token(TokenType.INT, 2, None)
        diff_type = Token(TokenType.FLOAT, 1, None)
        diff_both = Token(TokenType.FLOAT, 2, None)

        assert token == same
        assert token != diff_val
        assert token != diff_type
        assert token != diff_both
