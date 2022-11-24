"""processor.py

Implementation of the OpenDec processor that writes parser node
information into an intermediate file.
"""


import logging
import os
import os.path

from components.lexer import Lexer
from components.parser import Parser
from components.node import *
from components.state import State
from components.writer import Writer
from constants import (
    DIR_BIN,
    PHONEMES,
    PHONEMES_CONSONANTS,
    VOICE_DEFAULT_NAMES
)
from utils.exceptions import ProcessorException
from utils.validation import validate


class Processor(object):
    """The OpenDec processor.

    Attributes:
        index   Current processor position in the node list
        node    Current parser node being processed
        nodes   List of parser nodes to process
        state   Compiler state
        writer  Intermediate file writer

    Methods (Public):
        advance     Advance the Processor by a single node
        export      Export compiled file as a .WAV file
        process     Write compiled file

    Methods (Private):
        __process_command           Command processing
        __process_phoneme           Phoneme/phrase/sound processing

        __bypass                    Directly pass node to TTS engine
        __ignore                    Ignore a node
        __register                  Register user-defined objects

        __process_bpm_command        Specialized processing for [:bpm]
        __process_import_command     Specialized processing for [:import]
        __process_loop_command       Specialized processing for [:loop]
        __process_name_command       Specialized processing for [:name]
    """
    def __init__(self, nodes: list[Node], state: State, writer: Writer = None) -> None:
        """The Processor constructor method.

        Parameters:
            nodes   Parser nodes to process
            state   Current compiler state
            writer  Pre-existing writer to use (optional)
        """
        logging.info("Initializing Processor")
        self.state = state
        self.nodes = nodes

        self.index = 0
        self.node = self.nodes[0]

        if writer is not None:
            self.writer = writer
        else:
            self.writer = Writer(state.compiled)

    def advance(self) -> None:
        """Advance the processor by one parser node."""
        self.index += 1

        if self.index < len(self.nodes):
            self.node = self.nodes[self.index]
        else:
            self.node = self.nodes[-1]

    def export(self, engine: str) -> None:
        """Export the compiled file into a .wav file."""
        cwd = os.getcwd()
        os.chdir(DIR_BIN)
        os.system(f"type {self.state.compiled} | {engine} -pre \"[:phoneme arpabet on]\" -w {self.state.outfile}")
        os.chdir(cwd)

    def process(self) -> None:
        """Process the parser nodes into the intermediate file."""
        # Now we can start processing the nodes.
        logging.info(f"Processor: processing {len(self.nodes)} nodes")
        while not isinstance(self.node, EofNode):
            logging.debug(f"Processing node {self.node}")

            if isinstance(self.node, (CommandNode, VoiceNode)):
                validate(self.node)
                buffer = self.__process_command(self.node)
            elif isinstance(self.node, PhonemeNode):
                # NOTE: No validation commands for PhonemeNode types. Validation
                #       is done in the `process_phoneme` function as phoneme
                #       validation requires access to the compiler state, while
                #       CommandNode and VoiceNode validation does not.
                self.node.length = int(self.node.length * self.state.bpm_to_ms)
                buffer = self.__process_phoneme(self.node)
            else:
                raise ProcessorException(
                    self.node.pos, "TypeError",
                    f"Unexpected parser node type processed - {self.node.__class__}"
                )

            self.writer.write(buffer)
            self.advance()

    # Below we define the generic parser node processing functions.
    #
    # NOTE: When adding a generic parser node processing function, make sure
    #       that the function takes one parameter (the node to be processed)
    #       and returns a string which is the processed node data that will be
    #       passed directly to the text-to-speech engine. We need to pass a node
    #       as a parameter instead of directly accessing `self.node` because
    #       some processing needs to be done on command context nodes.
    def __process_command(self, node: Union[CommandNode, VoiceNode]) -> str:
        """Process a command node into the intermediate file."""
        # Validate, get the buffer, then write.
        processor = {
            # Base commands.
            "mode":         self.__ignore,
            "name":         self.__process_name_command,
            "play":         self.__process_play_command,
            "phoneme":      self.__ignore,
            "pitch":        self.__ignore,
            "pronounce":    self.__ignore,

            # Extended commands.
            "bpm":          self.__process_bpm_command,
            "import":       self.__process_import_command,

            # Commands with context.
            "loop":         self.__process_loop_command,
            "phrase":       self.__register,
            "sound":        self.__register,
            "voice":        self.__register,
        }.get(node.command, self.__bypass)
        return processor(node)

    def __process_context(self, context: list[Node]) -> str:
        """Process a generic command context."""
        build = ""
        for n in context:
            if isinstance(n, (CommandNode, VoiceNode)):
                build += self.__process_command(n)
            else:
                # When processing phonemes in a context, we need to keep track
                # of their original states. This is done predonimantly to
                # maintain accurate phoneme lengths when calling a phrase
                # repeatedly.
                original_length = n.length

                n.length = int(n.length * self.state.bpm_to_ms)
                build += self.__process_phoneme(n)
                n.length = original_length

        return build

    def __process_phoneme(self, node: PhonemeNode) -> str:
        """Process a phoneme node into the intermediate file."""
        # Process a phoneme. Nothing special needs to be done in this case.
        if node.phoneme in PHONEMES:
            buffer = str(node)

        # Process a phrase. Nothing special needs to be done in this case other
        # than joining all components of the phrase together.
        elif node.phoneme in self.state.phrases:
            phrase = self.state.phrases[node.phoneme]
            buffer = self.__process_context(phrase[:])

        # Process a sound. Special processing needs to be done here. Because a
        # sound can have variable length, we need to calculate vowel phoneme
        # length in milliseconds. Consonant vowel phonemes are always constant,
        # as they alway produce the same sound regardless of phoneme length.
        elif node.phoneme in self.state.sounds:
            buffer = self.__process_sound(node)

        # This neither a phoneme nor registered sound/phrase. Raise an error.
        else:
            raise ProcessorException(
                self.node.pos, "NameError",
                f"Unrecognized phoneme, sound, or phrase '{node.phoneme}'"
            )

        return buffer

    # Below we define more specialized processing commands. This includes
    # registering user-defined functions, expanding loops, and performing more
    # generalized, re-usable processing actions.
    #
    # NOTE: When adding a generic parser node processing function, make sure
    #       that the function takes one parameter (the node to be processed)
    #       and returns a string which is the processed node data that will be
    #       passed directly to the text-to-speech engine. We need to pass a node
    #       as a parameter instead of directly accessing `self.node` because
    #       some processing needs to be done on command context nodes.

    # Here we have the generalized, re-usable processing actions.
    def __bypass(self, node: Node) -> str:
        """The bypass function. This is used for default commands that
        can be directly passed to the text-to-speech engine.
        """
        return str(node)

    def __ignore(self, node: Node) -> str:
        """The ignore function. This is used to ignore any default
        commands that could impact the text-to-speech engine state in
        ways that would cause unexpected or unwanted behaviour.
        """
        return ""

    def __register(self, node: Node) -> str:
        """The register function. This is used to register user-defined
        objects to the compiler state.
        """
        self.state.register(node)
        return ""

    # Here, we have the more specific processing actions.
    def __process_bpm_command(self, node: CommandNode) -> str:
        """Adjust the compiler state's BPM (beats-per-minute). This will
        adjust the multiplier used in converting from BPM to
        milliseconds - the only measure the text-to-speech engine
        actually understands.
        """
        self.state.set_bpm(node.parameters[0])
        return ""

    def __process_import_command(self, node: CommandNode) -> str:
        """Import another file's content into the current file. This
        requires another compilation stack to process the new file's
        content.
        """
        # First we need to find the file before we can compile it. This includes
        # us checking all include directories to see if the file exists there.
        filename = node.parameters[0]
        filepath = None

        if os.path.isfile(filename):
            filepath = os.path.abspath(filename)
        else:
            for include in self.state.includes:
                checkfile = os.path.join(include, filename)
                if os.path.isfile(checkfile):
                    filepath = os.path.abspath(checkfile)

        if filepath is None:
            raise ProcessorException(
                node.pos, "FileNotFoundError",
                f"Could not import file '{filename}' - file not found"
            )

        # If we're here, then we've found a file to import. To import a file,
        # we'll need to go through the whole compilation process again in order
        # to understand what information to insert into this current file.
        #
        # NOTE: Importing can be used to reuse pre-defined objects such as
        #       sounds and phrases, which is why the state is shared between
        #       the current and any imported files.
        #       TODO: Do we need to share everything? (e.g. BPM)
        #
        # NOTE: Importing can be used to reuse pre-written phoneme sequences,
        #       which is why the writer is shared between the current file and
        #       any imported files.
        logging.info(f"Importing file '{filepath}'")

        tokens = Lexer(filepath).get_tokens()
        nodes = Parser(tokens).get_nodes()
        processor = Processor(nodes, self.state, writer=self.writer)
        processor.process()

        logging.info(f"Completed importing file '{filepath}'")
        return ""

    def __process_loop_command(self, node: CommandNode) -> str:
        """Unravel a loop."""
        logging.info(f"Expanding loop ({node.parameters[0]}) at {node.pos}")

        # First we need to process the loop content.
        build = self.__process_context(node.context[:])
        build = build * node.parameters[0]
        return build

    def __process_name_command(self, node: CommandNode) -> str:
        """Modify the text-to-speech engine's voice to a default voice
        or to a user-defined voice. In the case of user-deined voices,
        we need to manually adjust voice parameters.
        """
        name = node.parameters[0]

        if name in VOICE_DEFAULT_NAMES:
            return str(node)
        if name not in self.state.voices:
            raise ProcessorException(node.pos, "NameError", f"Name '{name}' is not defined")

        parameters = self.state.voices[name]
        return "".join([f"[:dv {p} {parameters[p]}]" for p in parameters])

    def __process_play_command(self, node: CommandNode) -> str:
        """Play a sound file. Before passing the command directly to the
        text-to-speech engine, we need to ensure that the file exists or
        can be found in the include directories.
        """
        filename = node.parameters[0]
        filepath = None

        if os.path.isfile(filename):
            filepath = os.path.abspath(filename)
        else:
            for include in self.state.includes:
                checkfile = os.path.join(include, filename)
                if os.path.isfile(checkfile):
                    filepath = os.path.abspath(checkfile)

        if filepath is None:
            raise ProcessorException(
                node.pos, "FileNotFoundError",
                f"Could not import file '{filename}' - file not found"
            )

        node.parameters[0] = filepath
        return str(node)

    def __process_sound(self, node: PhonemeNode) -> str:
        """Expand a sound into its component phonemes."""
        sound = self.state.sounds[node.phoneme]

        head = ""   # Leading consonants (if any) as a string.
        vowels = "" # Vowel consonants as a string.
        tail = ""   # Trailing consonants (if any) as a string.

        # A sound consists of (optional) leading consonants, at least one vowel,
        # then (optional) trailing consonants. We assume that the sound has been
        # validated to meet this criteria before being passed to this method.
        # This means that reading the sound content forwards and backwards will
        # not have any consonant overlap, as there will always be at least one
        # vowel separating the leading and trailing phonemes (if they exist).
        vowel_start = 0
        vowel_end = len(sound) - 1

        while vowel_start < len(sound):
            if sound[vowel_start].phoneme not in PHONEMES_CONSONANTS:
                break

            head += f"[{sound[vowel_start].phoneme}<15>]"
            vowel_start += 1

        while vowel_end >= 0:
            if sound[vowel_end].phoneme not in PHONEMES_CONSONANTS:
                break

            tail = f"[{sound[vowel_end].phoneme}<15>]" + tail
            vowel_end -= 1
        vowel_end += 1

        # Now that we've got the consonants, we need to determine how long the
        # vowels should be played. Each consonant length is constant (15ms), so we
        # can determine this value from the net sound length and the number of
        # consonant and vowel phonemes.
        vcount = vowel_end - vowel_start
        ccount = len(sound) - vcount
        vlength = (node.length - 15 * ccount) // vcount

        if node.length < 15 * ccount:
            raise ProcessorException(
                node.pos, "RuntimeError",
                f"Sound '{node.phoneme}' must have minimum length {15 * ccount}ms" \
                    + f" - got {node.length}"
            )

        # Now that we've got everything sorted for the vowels, construct the vowel
        # string, the return the fully constructed sound string.
        for phoneme in sound[vowel_start:vowel_end]:
            phoneme.length = vlength
            phoneme.pitch = node.pitch
            vowels += str(phoneme)

        return head + vowels + tail
