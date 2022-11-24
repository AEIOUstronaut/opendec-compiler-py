"""writer.py

An interface used to write intermediate OpenDec files.
"""


import logging
import os.path

from utils.exceptions import WriterException


class Writer(object):
    """The writer interface. Used for generating the compiled OpenDec
    files.

    Attributes:
        filename    File name to write to

    Methods:
        write               Write buffer to the file.
    """
    def __init__(self, filename: str) -> None:
        """The Writer constructor method.

        Parameters:
            filename    Named intermediate file to use (optional)
        """
        logging.info(f"Initializing Writer with file '{filename}'")

        filepath = os.path.abspath(filename)
        root, _ = os.path.split(filepath)

        if not os.path.isdir(root):
            raise WriterException(f"Cannot create file '{filepath}' - directory '{root}' doesn't exist")

        self.filename = filepath
        self.reset()

        logging.debug(f"Initialized Writer with file '{filename}'")

    def reset(self) -> None:
        """Clear the intermediate file."""
        with open(self.filename, "w") as f:
            pass

    def write(self, buffer: str) -> None:
        """Write a buffer to the intermediate file.

        Parameters:
            buffer  String buffer to write to the intermediate file

        Returns:
            None.
        """
        logging.debug(f"Writer: writing {len(buffer)} bytes -> '{buffer}'")
        with open(self.filename, "a") as writefile:
            writefile.write(buffer)
