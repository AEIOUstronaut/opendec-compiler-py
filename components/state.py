"""state.py

Manages the compiler state including meta information and user-defined
object definitions.
"""


import logging
import os
import os.path
from typing import Union

from components.node import CommandNode, VoiceNode
from constants import (
    DIR_BUILD,
    DIR_EXPORT,
    PHONEMES,
    VOICE_DEFAULTS,
    VOICE_DEFAULT_NAMES,
)
from utils.exceptions import StateException


class State(object):
    """An object used to track the OpenDec compiler's state.

    Attributes:
        bpm_to_ms   Multiplier to convert from BPM to milliseconds
        cwd         OpenDec project working directory
        includes    Include directories for file location

    Methods:
        register    Register a user-defined object
        set_bpm     Set current BPM (0 to reset)
    """
    def __init__(self, source: str, includes: list[str]) -> None:
        """The State constructor method."""
        logging.info("Initializing compiler state")

        # Compiler state.
        self.bpm_to_ms = 1.0
        self.cwd = os.getcwd()
        self.includes = [self.cwd] + includes[:]

        basename = os.path.splitext(os.path.split(source)[-1])[0]
        self.source = os.path.abspath(source)
        self.compiled = os.path.join(DIR_BUILD, f"{basename}.opendec.compiled")
        self.outfile = os.path.join(DIR_EXPORT, f"{basename}.wav")

        # User-defined object.
        self.phrases = {}
        self.sounds = {}
        self.voices = {}

        logging.debug(
            "Initialized compiler state:\n" \
            + f"    bpm_to_ms:  {self.bpm_to_ms}\n"
            + f"    cwd:        {self.cwd}\n" \
            + f"    includes:   {self.includes}\n\n" \
            + f"    source file:    {self.source}\n" \
            + f"    compiled file:  {self.compiled}\n" \
            + f"    output file:    {self.outfile}\n"
        )

    def register(self, node: Union[CommandNode, VoiceNode]) -> None:
        """Register a user-defined object.

        Parameters:
            node    User-defined object as a command or voice node
        """
        if not isinstance(node, (CommandNode, VoiceNode)):
            raise StateException(
                node.pos, "RegistrationError",
                f"Cannot register user-defined '{node.__class__.__name__}' type"
            )

        # Register a phrase.
        if node.command == "phrase":
            name = node.parameters[0]

            if name in PHONEMES:
                raise StateException(
                    node.pos, "RegistrationError",
                    f"Cannot register phrase '{name}' - it is a phoneme"
                )
            if name in self.sounds:
                raise StateException(
                    node.pos, "RegistrationError",
                    f"Cannot register phrase '{name}' - it is already a registered sound"
                )

            self.phrases[name] = node.context[:]
            logging.info(f"Registered phrase '{name}'")
            logging.debug(f"Registered phrase '{name}' -> {self.phrases[name]}")

        # Register a sound.
        elif node.command == "sound":
            name = node.parameters[0]

            if name in PHONEMES:
                raise StateException(
                    node.pos, "RegistrationError",
                    f"Cannot register sound '{name}' - it is a phoneme"
                )
            if name in self.phrases:
                raise StateException(
                    node.pos, "RegistrationError",
                    f"Cannot register sound '{name}' - it is already a registered phrase"
                )

            self.sounds[name] = node.context
            logging.info(f"Registered phrase '{name}'")
            logging.debug(f"Registered phrase '{name}' -> {self.sounds[name]}")

        # Register a voice.
        elif node.command == "voice":
            name = node.name

            if name in VOICE_DEFAULT_NAMES:
                raise StateException(
                    node.pos, "RegistrationError",
                    f"Cannot overwrite default voice {name}"
                )

            parameters = VOICE_DEFAULTS.copy()
            for parameter in node.parameters:
                parameters[parameter] = node.parameters[parameter]
            self.voices[name] = parameters

            logging.info(f"Registered voice '{name}'")
            logging.debug(f"Registered voice '{name}' -> {parameters}")

        # Unrecognized command type.
        else:
            raise StateException(
                node.pos, "RegistrationError",
                f"Cannot register command '{node.command}'"
            )

    def set_bpm(self, bpm: int) -> None:
        """Set the beats-per-minute. Setting to BPM disabled the BPM
        feature and all phoneme lengths will be treated as length in
        milliseconds.

        Parameters:
            bpm     Beats per minute
        """
        logging.info(f"Setting BPM to {bpm}")
        if bpm == 0:
            self.bpm_to_ms = 1
        else:
            self.bpm_to_ms = 60000 / bpm
        logging.debug(f"BPM-to-millisecond multiplier: {self.bpm_to_ms:.3f}")
