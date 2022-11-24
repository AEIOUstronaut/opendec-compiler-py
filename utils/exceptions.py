"""exceptions.py

Exceptions that provide some more specificity or extra features. Not all
exceptions will have additional features - they only exist to provide
more specific error names to help debug where an error may occur (e.g.
LexerException for errors in the Lexer).
"""


import logging

from components.position import Position


# Base exceptions.
class LoggingException(Exception):
    def __init__(self, message) -> None:
        logging.error(message)
        super().__init__(message)


class LoggingPositionalException(LoggingException):
    def __init__(self, pos: Position, type_: str, details: str) -> None:
        super().__init__(f"{type_}: {details} {pos}")


# Extended exceptions.
class LexerException(LoggingPositionalException):
    pass


class ReaderException(LoggingException):
    pass


class ParserException(LoggingPositionalException):
    pass


class ProcessorException(LoggingPositionalException):
    pass


class StateException(LoggingPositionalException):
    pass


class ValidationException(LoggingPositionalException):
    pass


class WriterException(LoggingException):
    pass
