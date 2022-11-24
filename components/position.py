"""position.py

Class, utilities, and constants for the Position object used in the
token scanner and parser.
"""


class Position(object):
    """A class to represent the current Position in the text being read
    by the lexer.

    Attributes:
        filename    Name of the source file being read
        index       Current index in the text
        column      Current column number in the text
        line        Current line number in the text

    Methods:
        advance     Advance the position by a single character
        copy        Create a copy of the current Position object
    """
    def __init__(self, filename: str) -> None:
        """Constructor for the Position object.

        Parameters:
            filename    File name of source code
        """
        self.filename = filename
        self.index = 0
        self.line = 0
        self.column = 0

    def __repr__(self) -> str:
        return f"<Position: file '{self.filename}', line {self.line + 1}, col {self.column}>"

    def advance(self, c) -> None:
        """Advance the position given the current character.

        Parameters:
            c   Most recent character read by the lexer.
        """
        self.index += 1
        self.column += 1

        if c == "\n":
            self.column = 0
            self.line += 1

    def copy(self) -> object:
        """Create a copy of the current Position object.

        Returns:
            A copy of the current Position object.
        """
        copy = Position(self.filename)
        copy.index = self.index
        copy.line = self.line
        copy.column = self.column
        return copy
