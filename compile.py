"""compile.py

The Python implementation fo the OpenDec compiler. The compiler takes a
source file written within the OpenDec specification and will compile it
to an intermediate file, then produce an output sound file.
"""


import argparse
import logging
import os
import os.path
import sys

from components.lexer import Lexer
from components.parser import Parser
from components.processor import Processor
from components.state import State
from constants import (
    DIR_BIN,
    DIR_BUILD,
    DIR_EXPORT,
    DIR_LIB,
    DIR_ROOT,
    DIR_SRC,
)


LOG_FILE = os.path.join(os.getcwd(), "build.log")


def clean() -> None:
    """Clean the current working directory of all OpenDec compiler
    artifacts.
    """
    def clean_file(filepath: str) -> None:
        try:    os.remove(filepath)
        except: logging.error(f"Failed to clean up file '{filepath}'")

    logging.info("Cleaning the OpenDec build.")

    # Clean compiled files.
    for compiled in os.listdir(DIR_BUILD):
        if compiled.endswith(".opendec.compiled"):
            compiled = os.path.abspath(os.path.join(DIR_BUILD, compiled))
            logging.debug(f"Deleting compiled file {compiled}")
            clean_file(compiled)

    # Clean any exported .wav files.
    for exported in os.listdir(DIR_EXPORT):
        if exported.endswith(".wav"):
            exported = os.path.abspath(os.path.join(os.getcwd(), exported))
            logging.debug(f"Deleting exported file {exported}")
            clean_file(exported)

    # Clean any log files.
    clean_file(LOG_FILE)


def compile(state: State, cache: bool, engine: str) -> None:
    """Compile an OpenDec source code file and export the output into
    a WAV (.wav) file.

    Parameters:
        state   Compiler state - includes path to source code file
        cache   Cache the intermediate file if True, delete it if not
        engine  Text-to-speech engine used to export .wav files
    """
    tokens = Lexer(state.source).get_tokens()
    nodes = Parser(tokens).get_nodes()
    processor = Processor(nodes, state)

    processor.process()
    processor.export(engine)

    if not cache and os.path.exists(state.compiled):
        os.remove(state.compiled)


def configure_logging(verbosity: int) -> None:
    """Initialize logging for the OpenDec compiler.

    Parameters:
        verbosity   Logging level (larger means more verbose)
    """
    level = {
        0: logging.WARNING,
        1: logging.INFO
    }.get(verbosity, logging.DEBUG)

    logger_fh = logging.FileHandler(LOG_FILE, mode="w")
    logger_fh.setLevel(logging.DEBUG)

    logger_sh = logging.StreamHandler()
    logger_sh.setLevel(level)

    logging.basicConfig(
        level=logging.DEBUG,
        format="[%(asctime)s] [%(levelname)8s] %(message)s",
        handlers=[logger_fh, logger_sh]
    )


def validate_args(args: argparse.Namespace) -> argparse.Namespace:
    """Validate parsed command line arguments.

    Parameters:
        args    Parsed command line arguments to validate

    Returns:
        The parsed command line arguments.
    """
    # Validate that the text-to-speech engine exists.
    engine = os.path.join(DIR_BIN, args.engine)
    if not os.path.exists(engine):
        raise FileNotFoundError(f"Could not find text-to-speech engine binary '{engine}'")

    # Validate the include directories.
    for include in args.include:
        logging.debug(f"Include directory: {include}")
        if not os.path.exists(include):
            raise FileNotFoundError(f"Could not find include directory '{include}'")
        if not os.path.isdir(include):
            raise NotADirectoryError(f"Include directory '{include}' is not a directory")

    # Validate the source files.
    if len(args.sources) == 0:
        for filename in os.listdir(os.getcwd()):
            args.sources.append(os.path.join(os.getcwd(), filename))

        if os.path.isdir(DIR_SRC):
            for filename in os.listdir(DIR_SRC):
                args.sources.append(os.path.join(DIR_SRC, filename))

        args.sources = [f for f in args.sources if f.lower().endswith(".opendec")]

    valid = []
    for source in args.sources:
        if not os.path.exists(source):
            logging.warning(f"Could not find source file '{source}' - skipping")
        elif not os.path.isfile(source):
            logging.warning(f"Source file '{source}' is not a file - skipping")
        else:
            valid.append(os.path.abspath(source))

    return args


if __name__ == "__main__":
    # Required for local imports in the sub-modules.
    if DIR_ROOT not in sys.path:
        sys.path.insert(0, DIR_ROOT)

    # Parse command line arguments.
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c", "--cache", action="store_true",
        help="Save compiled intermediate files in the `build` directory."
    )
    parser.add_argument(
        "-e", "--engine", default="say.exe",
        help="Text-to-speech engine to use. The engine must be in the `bin` " \
            + "directory."
    )
    parser.add_argument(
        "-I", "--include", action="append", default=[DIR_LIB],
        help="Directories where included files may exist. This includes any " \
            + "files that are imported via [:import] or played via [:play]."
    )
    parser.add_argument(
        "-v", "--verbose", action="count", default=0,
        help="Increase the logging verbosity on STDOUT."
    )
    parser.add_argument(
        "--clean", action="store_true",
        help="Clean up compiler artifacts. This includes any intermediate " \
            + "files that have been cached in the `build` directory and file " \
            + "exported to the `export` directory."
    )
    parser.add_argument(
        "sources", nargs="*",
        help="Opendec source files or text to compile."
    )
    args = parser.parse_args()

    configure_logging(args.verbose)
    args = validate_args(parser.parse_args())

    if args.clean:
        clean()
    else:
        # Do some final validations, checks, and setup before compiling.
        if len(args.sources) == 0:
            logging.warning("No source files to compile")
            sys.exit(0)

        # Make sure the artifact directories exist before compilation.
        if not os.path.isdir(DIR_BUILD):
            os.mkdir(DIR_BUILD)
        if not os.path.isdir(DIR_EXPORT):
            os.mkdir(DIR_EXPORT)

        # Ready to compile.
        for source in args.sources:
            state = State(source, args.include)
            compile(state, args.cache, args.engine)
            logging.info(f"Compiled {source}")
