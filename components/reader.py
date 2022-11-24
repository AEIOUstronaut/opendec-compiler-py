"""reader.py

An interface used to read and track read progress for OpenDec source
code.
"""


import logging
import os.path

from components.position import Position
from utils.exceptions import ReaderException


class Reader(object):
    """The reader interface. Reads and track read progress for OpenDec
    source code.

    Attributes (Public):
        char        Source code character at current position
        filename    File name for the source code (empty if plaintext)

    Attributes (Private):
        pos         Current reading position in the source text
        source      Source text being read

    Methods:
        getchar     Get next character from source
        getpos      Get a copy of the current text position
    """
    def __init__(self, source: str) -> None:
        """Reader constructor method.

        Parameters:
            source  Source to read - can be file or plaintext
        """
        # Clean up the input before we start loading it into the reader.
        source = source.strip()

        # Perform some basic validation.
        if len(source) == 0:
            raise ReaderException("Failed to initialize reader - no source provided")

        # Begin reading the source so that we have some text to scan/read.
        if os.path.isfile(source):
            logging.info(f"Initializing Reader for source file '{source}'")
            self.filename = source
            with open(source, "r") as sourcefile:
                self.source = sourcefile.read()
        else:
            logging.info(f"Initializing Reader directly from source text")
            self.filename = ""
            self.source = source

        # Now that we have the source text, we can initialize other important
        # attributes of the Reader object.
        self.char = self.source[0]
        self.pos = Position(self.filename)

    def advance(self) -> None:
        self.pos.advance(self.char)

        if self.pos.index < len(self.source):
            self.char = self.source[self.pos.index]
        else:
            self.char = ""

    def getpos(self) -> Position:
        """Get a copy of the current position in the source text."""
        return self.pos.copy()
