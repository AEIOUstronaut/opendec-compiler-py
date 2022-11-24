"""lexer.py

Implementation of the OpenDec compiler's token lexer, as well as all
required components and exceptions.
"""


import logging
import string

from constants import BREAK_CHARS, SPECIAL_CHARACTERS, WHITESPACE
from components.reader import Reader
from components.token import Token, TokenType
from utils.exceptions import LexerException


TOKENTYPE_SPECIALCHAR_MAP = {
    ",": TokenType.COMMA,
    "{": TokenType.LBRACE,
    "}": TokenType.RBRACE,
    "[": TokenType.LBRACKET,
    "]": TokenType.RBRACKET,
    "<": TokenType.LCHEVRON,
    ">": TokenType.RCHEVRON,
}


class Lexer(object):
    """The OpenDec lexer.

    Attributes:
        reader  Reader object used to scan the source code

    Methods:
        get_tokens      Scan source for all tokens
        read_remaining  Read characters until we run into a BREAK
        scan_comment    Scan for (and ignore) any comments
        scan_number     Scan for a number
        scan_string     Scan for a string
    """
    def __init__(self, source: str) -> None:
        """The Lexer constructor method.

        Parameters:
            source  Source code to scan
        """
        logging.info("Initializing Lexer")
        self.reader = Reader(source)

    def get_tokens(self) -> list[Token]:
        """Scan the source code given to the initialized Lexer object
        and return the list of all valid tokens.

        Parameters:
            None

        Returns:
            A list of tokens found from the source text.
        """
        logging.info("Lexer: reading tokens")
        tokens = []

        while self.reader.char != "":
            # Ignore whitespace.
            if self.reader.char in WHITESPACE:
                self.reader.advance()
                continue

            # Ignore comments.
            elif self.reader.char == "/":
                token = self.scan_comment()
                if token is not None:
                    tokens.append(token)
                continue

            # Get special character tokens.
            elif self.reader.char in SPECIAL_CHARACTERS:
                if self.reader.char not in TOKENTYPE_SPECIALCHAR_MAP:
                    raise LexerException(
                        self.reader.getpos(),
                        "SpecialCharImplementationException",
                        f"Lexer did not recognize special char '{self.reader.char}'"
                    )

                tokens.append(Token(
                    TOKENTYPE_SPECIALCHAR_MAP[self.reader.char],
                    self.reader.char,
                    self.reader.getpos()
                ))
                self.reader.advance()

            # Get any numbers (INT or FLOAT). Floats must have leading zeros.
            elif self.reader.char in string.digits:
                tokens.append(self.scan_number())

            # Read all other character sequences as a string.
            else:
                tokens.append(self.scan_string())

            logging.debug(f"Lexer: read {tokens[-1]}")

        tokens.append(Token(TokenType.EOF, None, self.reader.pos))
        logging.info(f"Lexer: read {len(tokens)} tokens total")
        return tokens

    def read_remaining(self) -> str:
        """Read remaining characters that do not trigger a break.

        Return:
            All subsequent characters that do not trigger a break.
        """
        remaining = ""

        # Keep reading until we hit a special character that requires a break
        # or until there are no more characters to read.
        while self.reader.char != "" and self.reader.char not in BREAK_CHARS:
            remaining += self.reader.char
            self.reader.advance()

        # One of the special characters is '/' which indicates the start of a
        # comment. We need to check if this is actually a comment or if we're
        # processing a string that contains this character (e.g. a file path).
        if self.reader.char == "/":
            token = self.scan_comment()
            if token is not None:
                remaining += token.value

        return remaining

    def scan_comment(self) -> Token:
        """Scan source for comments and ignore them.

        Return:
            Returns None if there is a sequence of characters that is a
            valid comment. If not, return a string starting with the
            comment character.

        Raises:
            LexerException  On unclosed block comments
        """
        pos = self.reader.getpos()
        self.reader.advance()

        # The follow-up character is '/', so we're scanning an inline comment.
        if self.reader.char == "/":
            logging.debug("Lexer: ignoring inline comment...")
            while self.reader.char != "" and self.reader.char != "\n":
                self.reader.advance()

        # The follow-up character is '*', so we're scanning a block comment.
        elif self.reader.char == "*":
            logging.debug("Lexer: ignoring block comment...")
            while self.reader.char != "":
                self.reader.advance()

                if self.reader.char == "*":
                    self.reader.advance()
                    if self.reader.char == "/":
                        self.reader.advance()
                        break
            else:
                # If we get here, we never found the closing "*/".
                raise LexerException(
                    pos, "OpenBlockCommentException"
                    "Found block comment that was not closed."
                )

        # If the follow-up character is not a recognized comment sequence, then
        # we need to treat the characters scanned as a string, as this could be
        # a file path (e.g. /home/user/todo.txt)
        else:
            string = "/" + self.read_remaining()
            return Token(TokenType.STRING, string, pos)

    def scan_number(self) -> Token:
        pos = self.reader.getpos()
        number = ""
        fp = False

        while self.reader.char != "" and self.reader.char not in BREAK_CHARS:
            # Keep readign digits as they com. No special rules applied.
            if self.reader.char in string.digits:
                number += self.reader.char

            # If we've processed mutliple dots, we have an invalid FLOAT.
            elif self.reader.char == "." and fp:
                number += self.read_remaining()

                errmsg = f"Invalid FLOAT '{number}' - can only have single '.'"
                raise LexerException(pos, "ValueError", errmsg)

            # If we encounter a dot, we're processing a FLOAT.
            elif self.reader.char == ".":
                number += self.reader.char
                fp = True

            # Illegal character - we're not processing a valid number.
            else:
                illegal_char = self.reader.char
                number_type = "FLOAT" if fp else "INT"
                number += self.read_remaining()

                errmsg = f"Invalid {number_type} '{number}' - '{illegal_char}' "
                errmsg += f"is not a legal number character"
                raise LexerException(pos, "ValueError", errmsg)

            self.reader.advance()

        if fp:
            return Token(TokenType.FLOAT, float(number), pos)
        else:
            return Token(TokenType.INT, int(number), pos)

    def scan_string(self) -> Token:
        """Scan source for any strings.

        Parameters:
            None

        Return:
            A STRING token scanned from the source text.
        """
        pos = self.reader.getpos()
        string = self.read_remaining()
        return Token(TokenType.STRING, string, pos)
