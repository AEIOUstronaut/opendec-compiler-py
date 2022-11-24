"""node.py

Parser node definitions and classes.
"""


from typing import Union

from components.position import Position


class Node(object):
    """Generic node class. A common base for parser node classes.

    Attributes:
        pos     Position of the parsed node
    """
    def __init__(self, pos: Position) -> None:
        self.pos = pos

    def __eq__(self, __o: object) -> bool:
        raise NotImplementedError

    def __repr__(self) -> str:
        raise NotImplementedError


class CommandNode(Node):
    """CommandNode is a node representing an OpenDec command, which is
    one of the basic components in OpenDec. A command is used to provide
    additional functionality to the text-to-speech engine outside of
    reading sounds and phonemes, which includes modifying the engine's
    internal state. A command is defined as:

        COMMAND := [ :STRING (INT | FLOAT | STRING)* ] ({ (PHONEME | COMMAND)* })?

    Attributes:
        pos         Position of the command
        command     Command name
        parameters  Command parameters (optional)
        context     Command context (optional)
    """
    def __init__(
            self,
            pos: Position,
            command: str,
            parameters: list[Union[str, int, float]],
            context: list[Union["CommandNode", "PhonemeNode"]]
    ) -> None:
        super().__init__(pos)
        self.command = command
        self.parameters = parameters
        self.context = context

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, CommandNode) \
            and self.command == __o.command \
            and self.parameters == __o.parameters \
            and self.context == __o.context

    def __repr__(self) -> str:
        build = f"[:{self.command}"
        for p in self.parameters:
            build += f" {str(p)}"
        build += "]"

        if len(self.context) > 0:
            build += " {"
            for c in self.context:
                build += f" {str(c)}"
            build += " }"

        return build


class EofNode(Node):
    """EofNode represents the end of the file. Used as a marker when
    processing parsed nodes to indicate when we've processed all parsed
    nodes.

    Attributes:
        pos     Position of end-of-file token.
    """
    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, EofNode)

    def __repr__(self) -> str:
        return "<EOF>"

class PhonemeNode(Node):
    """PhonemeNode is a node representing an OpenDec phoneme, which is
    one of the basic components in OpenDec. A phoneme is a basic unit of
    sound that is recognized and processed by the text-to-speech engine.
    In the OpenDec specification, a phoneme can also be used to call a
    user-define object (e.g. phrase or sound). A phoneme is defined as:

        PHONEME := STRING (< (INT | FLOAT)? ,? INT? >)?

    Attributes:
        pos         Position of the phoneme
        phoneme     Sounded, unsounded, or defined phonemes
        pitch       Pitch of the phoneme
        length      Length of the phoneme
    """
    def __init__(
            self,
            pos: Position,
            phoneme: str,
            length: Union[int, float],
            pitch: int
    ) -> None:
        super().__init__(pos)
        self.phoneme = phoneme
        self.length = length
        self.pitch = pitch

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, PhonemeNode) \
            and self.phoneme == __o.phoneme \
            and self.length == __o.length \
            and self.pitch == __o.pitch

    def __repr__(self) -> str:
        build = f"{self.phoneme}"
        if self.pitch + self.length > 0:
            build += "<"
            if self.length > 0: build += f"{self.length}"
            if self.pitch > 0:  build += f",{self.pitch}"
            build += ">"
        return f"[{build}]"


class VoiceNode(Node):
    """VoiceNode is a node representing an OpenDec voice definition,
    which is an abstraction used in OpenDec. The text-to-speech engine
    allows users to modify voice characteristics, and this abstraction
    allows for complex voice definitions in a simplified abstraction. A
    voice is defined as:

        VOICE := [ :voice STRING ] ({ STRING : INT (,? STRING : INT)* })?

    Attributes:
        pos         Position of the voice definition
        name        Voice name
        parameters  Voice parameters
    """
    def __init__(
            self,
            pos: Position,
            name: str,
            parameters: dict[str: int]
    ) -> None:
        super().__init__(pos)
        self.command = "voice"
        self.name = name
        self.parameters = parameters

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, VoiceNode) \
            and self.name == __o.name \
            and self.parameters == __o.parameters

    def __repr__(self) -> str:
        build = "[:voice "
        build += self.name
        build += "] {"
        build += ", ".join([f"{p}: {self.parameters[p]}" for p in self.parameters])
        build += "}"
        return build
