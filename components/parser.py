"""parser.py

Implementation of the OpenDec parser that reads input text and parses it
into different parser nodes.

These nodes are to be passed through to different processors so that the
intermediate file can be writter.
"""


import logging

from constants import PHONEMES_NOLENGTH, PHONEMES_NOPITCH
from components.lexer import Token, TokenType
from components.node import *
from components.position import Position
from utils.exceptions import ParserException


class Parser(object):
    """The OpenDec parser.

    Attributes:
        index   Current parser position in the token list
        token   Current token being processed by the parser
        tokens  List of tokens to parse

    Methods:
        advance     Advance the Parser by a single character
        get_nodes   Scan source for all nodes
    """
    def __init__(self, tokens: list[Token]) -> None:
        """The Parser constructor method.

        Parameters:
            tokens  Tokens to parse
        """
        logging.info("Initializing Parser")
        self.tokens = tokens

        self.index = 0
        self.token = self.tokens[self.index]

    def advance(self) -> None:
        """Advance the parser by one character of the source text."""
        self.index += 1

        if self.index < len(self.tokens):
            self.token = self.tokens[self.index]
        else:
            self.token = self.tokens[-1]

    def get_nodes(self) -> list[Node]:
        """Scan the source text and return the list of all nodes found
        from the source text.

        Returns:
            A list of nodes found from the source text.
        """
        nodes = []

        logging.info("Parser: processing nodes")
        while self.token.type != TokenType.EOF:
            # Parse commands (which includes voice definitions).
            if self.token.type == TokenType.LBRACKET:
                nodes.append(self.parse_command())
                logging.debug(f"Parser: processed node '{nodes[-1]}'")

            # Parse phonemes.
            elif self.token.type in (TokenType.COMMA, TokenType.STRING):
                nodes.append(self.parse_phoneme())
                logging.debug(f"Parser: processed node '{nodes[-1]}'")

            # Unexpected token.
            else:
                raise ParserException(
                    self.token.pos.copy(), "TypeError", f"Illegal {self.token} found"
                )

        nodes.append(EofNode(self.token.pos.copy()))
        logging.info(f"Parser: processed {len(nodes)} nodes")
        return nodes

    def parse_command(self) -> Node:
        """COMMAND := [ :STRING (INT | FLOAT | STRING)* ] ({ (PHONEME | COMMAND)* })?"""
        pos = self.token.pos.copy()
        self.advance()  # Current token is '[', so advance to the next token.

        # Read the command name.
        if self.token.type != TokenType.STRING:
            raise ParserException(
                pos, "SyntaxError",
                f"Expected STRING for command name - got '{self.token}'"
            )
        # And make sure it starts with a colon (:).
        if self.token.value[0] != ":":
            raise ParserException(
                pos, "SyntaxError",
                f"Command '{self.token.value}' must start with ':' - try '{self.token.value}'"
            )
        if self.token.value == ":":
            raise ParserException(
                pos, "SyntaxError",
                "No command provided - only got ':'"
            )
        if self.token.value == ":voice":
            self.advance()
            return self.parse_voice(pos)

        command = CommandNode(pos, self.token.value[1:], [], [])
        self.advance()

        # Read the remaining commands parameters.
        while self.token.type != TokenType.RBRACKET:
            if self.token.type == TokenType.EOF:
                raise ParserException(
                    pos, "SyntaxError",
                    "Unexpected EOF while parsing command"
                )
            elif self.token.type not in (TokenType.FLOAT, TokenType.INT, TokenType.STRING):
                raise ParserException(
                    pos, "SyntaxError",
                    "Command parameter can only be STRING, INT, or FLOAT - " \
                        + f"got '{self.token}'"
                )

            command.parameters.append(self.token.value)
            self.advance()

        # Current token is ']'. Advance and check if we need to process command
        # context.
        self.advance()
        if self.token.type != TokenType.LBRACE:
            # No context to process. Return the command node as it is.
            return command

        # We're currently on a '{' token. Advance to the next token then read
        # the command's context.
        self.advance()

        while self.token.type != TokenType.RBRACE:
            if self.token.type == TokenType.LBRACKET:
                command.context.append(self.parse_command())
            elif self.token.type in (TokenType.COMMA, TokenType.STRING):
                command.context.append(self.parse_phoneme())
            else:
                # Context can only accept other command nodes and phoneme nodes.
                # If we get there, we've hit a token that cannot represent the
                # start of either a command or phoneme.
                raise ParserException(
                    pos, "TypeError", f"Illegal {self.token} in command context"
                )

        self.advance()
        return command

    def parse_phoneme(self) -> Node:
        """PHONEME := STRING (< (INT | FLOAT)? ,? INT? >)?"""
        pos = self.token.pos.copy()
        phoneme = PhonemeNode(pos, self.token.value, 0, 0)
        self.advance()

        if self.token.type == TokenType.LCHEVRON:
            # Phoneme length and/or pitch have been specified.
            self.advance()

            # Get the phoneme length if specified.
            if self.token.type in (TokenType.FLOAT, TokenType.INT):
                phoneme.length = self.token.value
                self.advance()

            # It's possible that pitch isn't specified. If there is a comma,
            # then we need to parse any possible length tokens.
            if self.token.type == TokenType.COMMA:
                self.advance()

                # Get phoneme pitch is specified.
                if self.token.type == TokenType.INT:
                    phoneme.pitch = self.token.value
                    self.advance()

            # Got pitch and length data gathered (if specified), now make sure
            # that the chevrons are closed.
            if self.token.type != TokenType.RCHEVRON:
                raise ParserException(
                    pos, "SyntaxError",
                    f"Missing '>' when parsing phoneme - got '{self.token}'"
                )
            self.advance()

        # Handle any special phoneme cases here.
        if phoneme.phoneme in PHONEMES_NOLENGTH:
            phoneme.length = 0
        if phoneme.phoneme in PHONEMES_NOPITCH:
            phoneme.pitch = 0

        return phoneme

    def parse_voice(self, pos: Position) -> Node:
        """VOICE := [ :voice STRING ] ({ STRING : INT (,? STRING : INT)* })?"""
        # We've already confirmed that the first few tokens ('[:voice') are
        # correct. Now we just need to parse the rest.
        if self.token.type != TokenType.STRING:
            raise ParserException(
                pos, "SyntaxError", f"Voice name must be STRING - got {self.token}"
            )
        voice = VoiceNode(pos, self.token.value, {})
        self.advance()

        if self.token.type != TokenType.RBRACKET:
            raise ParserException(
                pos, "SyntaxError",
                f"Voice command takes only one parameter - got {self.token}"
            )
        self.advance()

        # Voice parameters are optional (will default to Paul's voice settings).
        # If parameters are provided, read and store them.
        if self.token.type != TokenType.LBRACE:
            return voice
        self.advance()

        while self.token.type != TokenType.RBRACE:
            # Get the voice parameter.
            if self.token.type != TokenType.STRING:
                raise ParserException(
                    pos, "SyntaxError",
                    f"Voice parameter must be STRING - got {self.token}"
                )
            parameter = self.token.value
            self.advance()

            # Get the parameter's value.
            if self.token.type != TokenType.INT:
                raise ParserException(
                    pos, "SyntaxError",
                    f"Voice parameter value must be INT - got {self.token}"
                )
            voice.parameters[parameter] = self.token.value
            self.advance()

            # Optionally, a comma can be used to separate parameters.
            if self.token.type == TokenType.COMMA:
                self.advance()

        self.advance()
        return voice
