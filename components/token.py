"""token.py

Lexer token definitions and classes.
"""


import enum

from components.position import Position


@enum.unique
class TokenType(enum.Enum):
    # Literals.
    FLOAT = enum.auto()     # Floating point numbers
    INT = enum.auto()       # Unsigned integers
    STRING = enum.auto()    # Standard string (double quotations ignored)

    # Special characters.
    COMMA = enum.auto()     # ,
    LBRACE = enum.auto()    # {
    RBRACE = enum.auto()    # }
    LBRACKET = enum.auto()  # [
    RBRACKET = enum.auto()  # ]
    LCHEVRON = enum.auto()  # <
    RCHEVRON = enum.auto()  # >

    EOF = enum.auto()


class Token(object):
    def __init__(self, type_: TokenType, value: object, pos: Position) -> None:
        self.type = type_
        self.value = value
        self.pos = pos

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, Token) \
            and self.type == __o.type \
            and self.value == __o.value

    def __repr__(self) -> str:
        return f"Token<{self.type.name},'{self.value}'>"
