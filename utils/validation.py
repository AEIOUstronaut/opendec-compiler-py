"""validate.py

Validation utilities.
"""


import re

from components.node import *
from constants import (
    PHONEMES_CONSONANTS,
    PHONEMES_VOWELS,
    RE_SOUND,
    RE_VARIABLE,
    VOICE_MINMAX,
    VOICE_PARAMETERS
)
from utils.exceptions import ValidationException


# Common validation utilities.
def _validate_context_length(node: CommandNode) -> None:
    if len(node.context) == 0:
        raise ValidationException(
            node.pos, "SyntaxError",
            f"{node.command} '{node.parameters[0]}' missing context"
        )


def _validate_context_type(node: CommandNode, *types: tuple[object]) -> None:
    for i in range(len(node.context)):
        if not isinstance(node.context[i], types):
            typestr = "|".join([t.__name__ for t in types])
            raise ValidationException(
                node.pos, "CommandContextTypeException",
                f"Command '{node.command}' takes only {typestr} types - " \
                    + f"got {type(node.context[i])}"
            )


def _validate_parameter_count(node: CommandNode, count: int) -> None:
    if len(node.parameters) != count:
        raise ValidationException(
            node.pos, "CommandParameterCountException",
            f"Command '{node.command}' takes only {count} parameters - " \
                + f"got {len(node.parameters)}"
        )


def _validate_parameter_types(node: CommandNode, types: list[object]) -> None:
    assert len(node.parameters) == len(types)

    for i in range(len(node.parameters)):
        if not isinstance(node.parameters[i], types[i]):
            raise ValidationException(
                node.pos, "CommandParameterTypeException",
                f"Command '{node.command}' parameter {i+1} must be type " \
                    + f"{types[i]} - got {type(node.parameters[i])}"
            )


def _validate_parameter_keywords(
        node: CommandNode,
        parameter: str,
        keywords: list[str]
) -> None:
    if parameter not in keywords:
        keywordstring = "|".join([kw for kw in keywords])
        raise ValidationException(
            node.pos, "CommandParameterKeywordException",
            f"Command '{node.command}' parameter '{parameter}' not a valid " \
                + f"keyword - expected one of {keywordstring}"
        )


def _validate_parameter_is_variable(node: CommandNode, parameter: str) -> None:
    if not re.match(RE_VARIABLE, parameter):
        raise ValidationException(
            node.pos, "CommandParameterVariableException",
            f"Command '{node.command}' parameter '{parameter}' does not " \
                + "match the variable regex"
        )


def _validate_parameter_value_range(
        node: CommandNode,
        parameter: int,
        min: int,
        max: int
) -> None:
    if parameter < min or parameter > max:
        raise ValidationException(
            node.pos, "CommandParameterValueException",
            f"Command '{node.command}' parameter value {parameter} must be " \
                + f"between {min} and {max}"
        )


# Validate base commands.
def _autovalidate(node: CommandNode) -> None:
    """Used for commands that don't need additional validation."""
    pass


def _validate_comma_command(node: CommandNode) -> None:
    """[:comma LENGTH] or [:cp LENGTH]

    Command parameters:
        LENGTH (int)
    """
    _validate_parameter_count(node, 1)
    _validate_parameter_types(node, [int])


def _validate_define_voice_command(node: CommandNode) -> None:
    """[:dv OPTION VALUE]

    Options:
        ap|as|b4|b5|bf|br|f4|f5|hr|hs|la|lx|nf|pr|qu|ri|sm|sr|sx

    Parameters:
        VALUE (int)     The value for the given voice option
    """
    _validate_parameter_count(node, 2)
    _validate_parameter_types(node, [str, int])
    _validate_parameter_keywords(node, node.parameters[0], VOICE_PARAMETERS)

    minval, maxval = VOICE_MINMAX[node.parameters[0]]
    _validate_parameter_value_range(node, node.parameters[1], minval, maxval)


def _validate_error_command(node: CommandNode) -> None:
    """[:error OPTION]

    Options:
        ignore|speak|tone
    """
    _validate_parameter_count(node, 1)
    _validate_parameter_types(node, [str])

    keywords = ["ignore", "speak", "tone"]
    _validate_parameter_keywords(node, node.parameters[0], keywords)


def _validate_processing_mode_command(node: CommandNode) -> None:
    """[:mode OPTION MODE]

    Options:
        math|europe|spell|name|citation|latin|table

    Parameters:
        MODE (keyword)     on, off, or set (to disable all other modes)
    """
    _validate_parameter_count(node, 2)
    _validate_parameter_types(node, [str, str])

    options = ["math", "europe", "spell", "name", "citation", "latin", "table"]
    modes = ["on", "off", "set"]

    _validate_parameter_keywords(node, node.parameters[0], options)
    _validate_parameter_keywords(node, node.parameters[1], modes)


def _validate_name_command(node: CommandNode) -> None:
    """[:name OPTION] or [:nOPT]

    Options:
        OPTION  Betty|Dennis|Frank|Harry|Kit|Paul|Rita|Ursula|Wendy
        OPT     b|d|f|h|k|p|r|u|w
    """
    _validate_parameter_count(node, 1)
    _validate_parameter_types(node, [str])
    _validate_parameter_is_variable(node, node.parameters[0])


def _validate_period_pause_command(node: CommandNode) -> None:
    """[:period LENGTH] or [:pp LENGTH]

    Parameters:
        LENGTH (int)    Pause length in milliseconds
    """
    _validate_parameter_count(node, 1)
    _validate_parameter_types(node, [int])


def _validate_phoneme_command(node: CommandNode) -> None:
    """[:phoneme OPTION on|off]

    Options:
        arpabet
    """
    _validate_parameter_count(node, 2)
    _validate_parameter_types(node, [str, str])

    _validate_parameter_keywords(node, node.parameters[0], ["arpabet"])
    _validate_parameter_keywords(node, node.parameters[1], ["on", "off"])


def _validate_pitch_command(node: CommandNode) -> None:
    """[:pitch FREQUENCY]

    Parameters:
        FREQUENCY (int)     Frequency difference in hertz
    """
    _validate_parameter_count(node, 1)
    _validate_parameter_types(node, [int])


def _validate_play_command(node: CommandNode) -> None:
    """[:play FILE]

    Parameters:
        FILE (string)   Path to WAV file to open and play
    """
    _validate_parameter_count(node, 1)
    _validate_parameter_types(node, [str])


def _validate_pronounce_command(node: CommandNode) -> None:
    """[:pronounce OPTION]

    Options:
        alternate|primary|name|noun|adjective|verb
    """
    _validate_parameter_count(node, 1)
    _validate_parameter_types(node, [str])

    options = ["alternate", "primary", "name", "noun", "adjective", "verb"]
    _validate_parameter_keywords(node, node.parameters[0], options)


def _validate_punct_command(node: CommandNode) -> None:
    """[:punct OPTION]

    Options:
        none|some|all|pass
    """
    _validate_parameter_count(node, 1)
    _validate_parameter_types(node, [str])

    options = ["none", "some", "all", "pass"]
    _validate_parameter_keywords(node, node.parameters[0], options)


def _validate_rate_command(node: CommandNode) -> None:
    """[:rate WPM]

    Parameters:
        WPM (int)   Rate of speech in words per minute
    """
    _validate_parameter_count(node, 1)
    _validate_parameter_types(node, [int])
    _validate_parameter_value_range(node, node.parameters[0], 75, 600)


def _validate_say_command(node: CommandNode) -> None:
    """[:say OPTION]

    Options:
        clause|word|letter|filtered|line
    """
    _validate_parameter_count(node, 1)
    _validate_parameter_types(node, [str])

    options = ["clause", "word", "letter", "filtered", "line"]
    _validate_parameter_keywords(node, node.parameters[0], options)


def _validate_skip_command(node: CommandNode) -> None:
    """[:skip OPTION]

    Options:
        punct|rule|all|off|cpg|none
    """
    _validate_parameter_count(node, 1)
    _validate_parameter_types(node, [str])

    options = ["punct", "rule", "all", "off", "cpg", "none"]
    _validate_parameter_keywords(node, node.parameters[0], options)


def _validate_tone_command(node: CommandNode) -> None:
    """[:tone FREQUENCY LENGTH]

    Parameters:
        FREQUENCY (int)     Frequency of the tone to play in hertz
        LENGTH (int)        Length of the tone in milliseconds
    """
    _validate_parameter_count(node, 2)
    _validate_parameter_types(node, [int, int])


def _validate_volume_command(node: CommandNode) -> None:
    """[:volume OPTION VALUE] or [:volume sset LCHANNEL RCHANNEL].

    Options:
        up|lup|rup|down|ldown|rdown|set|lset|rset

    Parameters:
        VALUE (int)     Volume adjustment
        LCHANNEL (int)  Left channel volume adjustment
        RCHANNEL (int)  Right channel volume adjustment
    """
    options = ["up", "lup", "rup", "down", "ldown", "rdown", "set", "lset", "rset"]

    # Handle the "sset" option differently.
    if len(node.parameters) == 2:
        _validate_parameter_types(node, [str, int])
        _validate_parameter_keywords(node, node.parameters[0], options)
        _validate_parameter_value_range(node, node.parameters[1], 0, 100)
    elif len(node.parameters) == 3:
        _validate_parameter_types(node, [str, int, int])
        _validate_parameter_keywords(node, node.parameters[0], ["sset"])
        _validate_parameter_value_range(node, node.parameters[1], 0, 100)
        _validate_parameter_value_range(node, node.parameters[2], 0, 100)
    else:
        _validate_parameter_count(node, 2)


# Validate extended commands.
def _validate_bpm_command(node: CommandNode) -> None:
    """[:bpm TEMPO]

    Parameters:
        TEMPO (int)     Tempo at which to convert timings
    """
    _validate_parameter_count(node, 1)
    _validate_parameter_types(node, [int])
    _validate_parameter_value_range(node, node.parameters[0], 0, 60000)


def _validate_import_command(node: CommandNode) -> None:
    """[:import PATH]

    Parameters:
        PATH (str)      Path to OpenDec script to import
    """
    _validate_parameter_count(node, 1)
    _validate_parameter_types(node, [str])


# Validate commands with context.
def _validate_loop_command(node: CommandNode) -> None:
    """[:loop REPEAT] { Node* }"""
    _validate_parameter_count(node, 1)
    _validate_parameter_types(node, [int])
    _validate_context_type(node, (Node))


def _validate_phrase_command(node: CommandNode) -> None:
    """[:phrase NAME] { Node* }"""
    _validate_parameter_count(node, 1)
    _validate_parameter_types(node, [str])
    _validate_parameter_is_variable(node, node.parameters[0])
    _validate_context_length(node)
    _validate_context_type(node, (Node))


def _validate_sound_command(node: CommandNode) -> None:
    """[:sound NAME] { [consonant]* vowel+ [consonant]* }"""
    _validate_parameter_count(node, 1)
    _validate_parameter_types(node, [str])
    _validate_parameter_is_variable(node, node.parameters[0])
    _validate_context_length(node)
    _validate_context_type(node, (PhonemeNode))

    phonemes = ""
    for context in node.context:
        if context.phoneme in PHONEMES_CONSONANTS:
            phonemes += "c"
        elif context.phoneme in PHONEMES_VOWELS:
            phonemes += "v"
        else:
            raise ValidationException(
                node.pos,
                "SoundPhonemeTypeException",
                f"Sound '{node.parameters[0]}' can only accept vowel or " \
                    + f"consonant phonemes - got '{context}'"
            )
    if not re.match(RE_SOUND, phonemes):
        raise ValidationException(
            node.pos,
            "SyntaxError",
            f"Sound '{node.parameters[0]}' does not follow consonant-vowel-" \
                + "consonant pattern"
        )


def _validate_voice_command(node: VoiceNode) -> None:
    """[:voice NAME] { option1: value1, ... optionN: valueN }"""
    _validate_parameter_is_variable(node, node.name)

    for parameter in node.parameters:
        if parameter not in VOICE_PARAMETERS:
            raise ValidationException(
                node.pos,
                "VoiceParameterNameException",
                f"Voice '{node.name}' contains unrecognized parameter '{parameter}'"
            )

        value = node.parameters[parameter]
        minval, maxval = VOICE_MINMAX[parameter]
        if value < minval or value > maxval:
            raise ValidationException(
                node.pos,
                "VoiceParameterValueException",
                f"Voice '{node.name}' parameter '{parameter}' value {value} " \
                    + f"is not within a valid range ({minval} - {maxval})"
            )


_VALIDATION_MAP = {
    # Base commands.
    "comma":        _validate_comma_command,
    "cp":           _validate_comma_command,
    "dv":           _validate_define_voice_command,
    "error":        _validate_error_command,
    "mode":         _validate_processing_mode_command,
    "name":         _validate_name_command,
    "nb":           _autovalidate,
    "nd":           _autovalidate,
    "nf":           _autovalidate,
    "nh":           _autovalidate,
    "nk":           _autovalidate,
    "np":           _autovalidate,
    "nr":           _autovalidate,
    "nu":           _autovalidate,
    "nw":           _autovalidate,
    "period":       _validate_period_pause_command,
    "pp":           _validate_period_pause_command,
    "phoneme":      _validate_phoneme_command,
    "pitch":        _validate_pitch_command,
    "play":         _validate_play_command,
    "pronounce":    _validate_pronounce_command,
    "punct":        _validate_punct_command,
    "rate":         _validate_rate_command,
    "say":          _validate_say_command,
    "skip":         _validate_skip_command,
    "tone":         _validate_tone_command,
    "volume":       _validate_volume_command,

    # Extended commands.
    "bpm":          _validate_bpm_command,
    "import":       _validate_import_command,

    # Commands with context.
    "loop":         _validate_loop_command,
    "phrase":       _validate_phrase_command,
    "sound":        _validate_sound_command,
    "voice":        _validate_voice_command,
}


def validate(node: CommandNode) -> None:
    """Validate a command node.

    Parameters:
        node    Command node to validate
    """
    if node.command not in _VALIDATION_MAP:
        raise ValidationException(
            node.pos, "NameError", f"Unrecognized command '{node.command}'"
        )

    _VALIDATION_MAP[node.command](node)
