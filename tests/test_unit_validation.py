import os.path
import pytest
import sys

# Required for local imports.
ROOTDIR = os.path.abspath(os.path.join(__file__, "..", ".."))
if ROOTDIR not in sys.path:
    sys.path.insert(0, ROOTDIR)

# Local import should go under this comment.
from components.lexer import Lexer
from components.node import Node
from components.parser import Parser
from constants import VOICE_DEFAULT_NAMES, VOICE_MINMAX
from utils.exceptions import ValidationException
from utils.validation import validate


def generate_invalid_voice_parameters() -> list[tuple[str, int]]:
    """Generate a list of source strings for invalid voice parameter
    values. Invalid voice parameters are:

        One below the minimum valid range (if applicable)
        One above the maximum valid range
    """
    pairs = []

    for p in VOICE_MINMAX:
        minval, maxval = VOICE_MINMAX[p]

        if minval > 0:
            pairs.append((p, minval - 1))
        pairs.append((p, maxval + 1))

    return pairs


def generate_valid_voice_parameters() -> list[tuple[str, int]]:
    """Generate a list of source string for valid voice parameter
    values. Valid voice parameters are:

        One at the minimum valid range
        One within the valid range (if applicable)
        One at the maximum valid range
    """
    pairs = []

    for p in VOICE_MINMAX:
        minval, maxval =VOICE_MINMAX[p]
        inrange = minval + ((maxval - minval) // 2)

        pairs.append((p, minval))
        pairs.append((p, inrange))
        pairs.append((p, maxval))

    return pairs


def generate_invalid_dv() -> list[str]:
    pairs = generate_invalid_voice_parameters()
    return [f"[:dv {p} {v}]" for p, v in pairs]


def generate_invalid_voice() -> list[str]:
    pairs = generate_invalid_voice_parameters()
    return [f"[:voice name] {{{p} {v}}}" for p, v in pairs]


def generate_valid_dv() -> list[str]:
    pairs = generate_valid_voice_parameters()
    return [f"[:dv {p} {v}]" for p, v in pairs]


def generate_valid_voice() -> list[str]:
    pairs = generate_valid_voice_parameters()
    return [f"[:voice name] {{{p} {v}}}" for p, v in pairs]


class TestValidation:
    def __parse_node(self, source: str) -> Node:
        tokens = Lexer(source).get_tokens()
        nodes = Parser(tokens).get_nodes()
        return nodes[0]

    @pytest.mark.parametrize("source", [
        # Comma pause command.
        "[:comma]",     "[:cp]",        # Not enough parameters
        "[:comma 0 0]", "[:cp 0 0]",    # Too many parameters
        "[:comma 1.0]", "[:cp 1.0]",    # Wrong parameter type
        "[:comma one]", "[:cp one]",    # Wrong parameter type

        # Design voice command.
        "[:dv]",            # Not enough parameters
        "[:dv sx]",         # Not enough parameters
        "[:dv sx 0 1]",     # Too many parameters
        "[:dv 1 1]",        # Wrong parameter types
        "[:dv 1 1.0]",      # Wrong parameter types
        "[:dv 1 sx]",       # Wrong parameter types
        "[:dv 1.0 1]",      # Wrong parameter types
        "[:dv 1.0 1.0]",    # Wrong parameter types
        "[:dv 1.0 sx]",     # Wrong parameter types
        "[:dv sx 1.0]",     # Wrong parameter types
        "[:dv sx sx]",      # Wrong parameter types
        "[:dv save 1]",     # Invalid option
        *generate_invalid_dv(),

        # Error handling command.
        "[:error]",             # Not enough parameters
        "[:error tone tone]",   # Too many parameters
        "[:error 1]",           # Wrong parameter type
        "[:error 1.0]",         # Wrong parameter type
        "[:error one]",         # Invalid option

        # Text processing mode command.
        "[:mode]",              # Not enough parameters
        "[:mode math]",         # Not enough parameters
        "[:mode math on off]",  # Too many parameters
        "[:mode 1 1]",          # Wrong parameter type
        "[:mode 1 1.0]",        # Wrong parameter type
        "[:mode 1 off]",        # Wrong parameter type
        "[:mode 1.0 1]",        # Wrong parameter type
        "[:mode 1.0 1.0]",      # Wrong parameter type
        "[:mode 1.0 off]",      # Wrong parameter type
        "[:mode math 1]",       # Wrong parameter type
        "[:mode math 1.0]",     # Wrong parameter type
        "[:mode invalid on]",   # Invalid option
        "[:mode math invalid]", # Invalid mode keyword

        # Name command.
        "[:name]",              # Not enough parameters
        "[:name Paul Paul]",    # Too many parameters
        "[:name 1]",            # Wrong parameter type
        "[:name 1.0]",          # Wrong parameter type
        *[f"[:n{o}]" for o in "acegijlmnoqstvxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"],

        # Period pause command.
        "[:period]",        "[:pp]",        # Not enough parameters
        "[:period 0 0]",    "[:pp 0 0]",    # Too many parameters
        "[:period 1.0]",    "[:pp 1.0]",    # Wrong parameter type
        "[:period one]",    "[:pp one]",    # Wrong parameter type

        # Phoneme command.
        "[:phoneme]",                   # Not enough parameters
        "[:phoneme arpabet]",           # Not enough parameters
        "[:phoneme arpabet on off]",    # Too many parameters
        "[:phoneme 1 1]",               # Wrong parameter type
        "[:phoneme 1 1.0]",             # Wrong parameter type
        "[:phoneme 1 on]",              # Wrong parameter type
        "[:phoneme 1.0 1]",             # Wrong parameter type
        "[:phoneme 1.0 1.0]",           # Wrong parameter type
        "[:phoneme 1.0 on]",            # Wrong parameter type
        "[:phoneme arpabet 1]",         # Wrong parameter type
        "[:phoneme arpabet 1.0]",       # Wrong parameter type
        "[:phoneme invalid on]",        # Invalid option
        "[:phoneme arpabet invalid]",   # Invalid keyword

        # Pitch command.
        "[:pitch]",         # Not enough parameters
        "[:pitch 35 35]",   # Too many parameters
        "[:pitch 1.0]",     # Wrong parameter type
        "[:pitch one]",     # Wrong parameter type

        # Play command.
        "[:play]",          # Not enough parameters
        "[:play one one]",  # Too many parameters
        "[:play 1]",        # Wrong parameter type
        "[:play 1.0]",      # Wrong parameter type

        # Pronounce command.
        "[:pronounce]",             # Not enough parameters
        "[:pronounce noun noun]",   # Too many parameters
        "[:pronounce 1]",           # Wrong parameter type
        "[:pronounce 1.0]",         # Wrong parameter type
        "[:pronounce invalid]",     # Invalid option

        # Punct command.
        "[:punct]",         # Not enough parameters
        "[:punct all all]", # Too many parameters
        "[:punct 1]",       # Wrong parameter type
        "[:punct 1.0]",     # Wrong parameter type
        "[:punct invalid]", # Invalid option

        # Rate command.
        "[:rate]",          # Not enough parameters
        "[:rate 100 100]",  # Too many parameters
        "[:rate 1.0]",      # Wrong parameter type
        "[:rate one]",      # Wrong parameter type
        "[:rate 74]",       # Parameter out of range
        "[:rate 601]",      # Parameter out of range

        # Say command.
        "[:say]",           # Not enough parameters
        "[:say word word]", # Too many parameters
        "[:say 1]",         # Wrong parameter type
        "[:say 1.0]",       # Wrong parameter type
        "[:say invalid]",   # Invalid option

        # Skip command.
        "[:skip]",          # Not enough parameters
        "[:skip all all]",  # Too many parameters
        "[:skip 1]",        # Wrong parameter type
        "[:skip 1.0]",      # Wrong parameter type
        "[:skip invalid]",  # Invalid option

        # Tone command.
        "[:tone]",          # Not enough parameters
        "[:tone 1]",        # Not enough parameters
        "[:tone 1 1 1]",    # Too many parameters
        "[:tone 1 1.0]",    # Wrong parameter type
        "[:tone 1 one]",    # Wrong parameter type
        "[:tone 1.0 1]",    # Wrong parameter type
        "[:tone 1.0 1.0]",  # Wrong parameter type
        "[:tone 1.0 one]",  # Wrong parameter type
        "[:tone one 1]",    # Wrong parameter type
        "[:tone one 1.0]",  # Wrong parameter type
        "[:tone one one]",  # Wrong parameter type

        # Volume command.
        "[:volume]",                # Not enough parameters
        "[:volume up]",             # Not enough parameters
        "[:volume sset 10 10 10]",  # Too many parameters
        "[:volume 1 1]",            # Wrong parameter type
        "[:volume 1 1.0]",          # Wrong parameter type
        "[:volume 1 one]",          # Wrong parameter type
        "[:volume 1.0 1]",          # Wrong parameter type
        "[:volume 1.0 1.0]",        # Wrong parameter type
        "[:volume 1.0 one]",        # Wrong parameter type
        "[:volume up 1.0]",         # Wrong parameter type
        "[:volume up one]",         # Wrong parameter type
        "[:volume sset 1 1.0]",     # Wrong parameter type
        "[:volume sset 1 one]",     # Wrong parameter type
        "[:volume sset 1.0 1]",     # Wrong parameter type
        "[:volume sset 1.0 1.0]",   # Wrong parameter type
        "[:volume sset 1.0 one]",   # Wrong parameter type
        "[:volume sset one 1]",     # Wrong parameter type
        "[:volume sset one 1.0]",   # Wrong parameter type
        "[:volume sset one one]",   # Wrong parameter type
        "[:volume invalid 1]",      # Invalid option
        *[f"[:volume {o} 101]" for o in ["up", "lup", "rup", "down", "ldown", "rdown", "set", "lset", "rset"]],
        "[:volume sset 1 101]",     # Invalid parameter value
        "[:volume sset 101 1]",     # Invalid parameter value
        "[:volume sset 101 101]",   # Invalid parameter value

        # Bpm command.
        "[:bpm]",       # Not enough parameters
        "[:bpm 0 0]",   # Too many parameters
        "[:bpm 0.0]",   # Invalid parameter type
        "[:bpm one]",   # Invalid parameter type
        "[:bpm 60001]", # Invalid parameter value

        # Import command.
        "[:import]",            # Not enough parameters
        "[:import one one]",    # Too many parameters
        "[:import 1]",          # Wrong parameter type
        "[:import 1.0]",        # Wrong parameter type

        # Sound command.
        "[:sound]",                         # Not enough parameters
        "[:sound name name]",               # Too many parameters
        "[:sound 1]",                       # Wrong parameter type
        "[:sound 1.0]",                     # Wrong parameter type
        "[:sound name]",                    # No context provided
        "[:sound name] {}",                 # Empty context provided
        "[:sound name] {[:cp 0]}",          # Non-phoneme in context
        "[:sound name] {aa [:cp 0]}",       # Non-phoneme in context
        "[:sound name] {[:cp 0] aa}",       # Non-phoneme in context
        "[:sound name] {aa [:cp 0] aa}",    # Non-phoneme in context
        "[:sound _] {aa}",                  # Sound name not a valid variable
        "[:sound in-valid] {aa}",           # Sound name not a valid variable
        "[:sound name] {_}",                # Non-vowel/consonant phoneme
        "[:sound name] {_ b aa}",           # Non-vowel/consonant phoneme
        "[:sound name] {b _ aa}",           # Non-vowel/consonant phoneme
        "[:sound name] {b aa _}",           # Non-vowel/consonant phoneme
        "[:sound name] {b}",                # Missing vowel phoneme
        "[:sound name] {aa b aa}",          # Wrong phoneme order
        "[:sound name] {b aa b aa}",        # Wrong phoneme order
        "[:sound name] {aa b aa b}",        # Wrong phoneme order

        # Phrase command.
        "[:phrase]",                # Not enough parameters
        "[:phrase name name]",      # Too many parameters
        "[:phrase 1]",              # Wrong parameter type
        "[:phrase 1.0]",            # Wrong parameter type
        "[:phrase name]",           # No context provided
        "[:phrase name] {}",        # Empty context provided
        "[:phrase _] {aa}",         # Phrase name not a valid variable
        "[:phrase in-valid] {aa}",  # Phrase name not a valid variable

        # Voice command.
        "[:voice _]",               # Voice name not a valid variable
        "[:voice in-valid]",        # Voice name not a valid variable
        "[:voice name] {a 1}",      # Invalid parameter name
        "[:voice name] {sx 0 a 1}", # Invalid parameter name
        "[:voice name] {a 1 sx 0}", # Invalid parameter name
        *generate_invalid_voice(),  # invalid parameter values
    ])
    def test_invalid(self, source: str) -> None:
        with pytest.raises(ValidationException):
            validate(self.__parse_node(source))

    @pytest.mark.parametrize("source", [
        # Comma pause command.
        "[:comma 0]",       "[:cp 0]",
        "[:comma 1]",       "[:cp 1]",
        "[:comma 100]",     "[:cp 100]",
        "[:comma 1000]",    "[:cp 1000]",

        # Design voice command.
        *generate_valid_voice(),

        # Error handling command.
        "[:error ignore]",
        "[:error speak]",
        "[:error tone]",

        # Text processing mode command.
        *[f"[:mode math {v}]" for v in ["on", "off", "set"]],
        *[f"[:mode europe {v}]" for v in ["on", "off", "set"]],
        *[f"[:mode spell {v}]" for v in ["on", "off", "set"]],
        *[f"[:mode name {v}]" for v in ["on", "off", "set"]],
        *[f"[:mode citation {v}]" for v in ["on", "off", "set"]],
        *[f"[:mode latin {v}]" for v in ["on", "off", "set"]],
        *[f"[:mode table {v}]" for v in ["on", "off", "set"]],

        # Name command.
        *[f"[:name {o}]" for o in VOICE_DEFAULT_NAMES],
        *[f"[:n{o}]" for o in "bdfhkpruw"],

        # Period pause command.
        "[:period 0]",      "[:pp 0]",
        "[:period 1]",      "[:pp 1]",
        "[:period 100]",    "[:pp 100]",
        "[:period 1000]",   "[:pp 1000]",

        # Phoneme command.
        "[:phoneme arpabet on]",
        "[:phoneme arpabet off]",

        # Pitch command.
        "[:pitch 0]",
        "[:pitch 35]",
        "[:pitch 20000]",

        # Play command.
        "[:play C:\\example\\file.txt]",
        "[:play ..\\example\\file.txt]",
        "[:play .\\example\\file.txt]",
        "[:play /root/example/file.txt]",
        "[:play ../example/file.txt]",
        "[:play ./example/file.txt]",

        # Pronounce command.
        "[:pronounce alternate]",
        "[:pronounce primary]",
        "[:pronounce name]",
        "[:pronounce noun]",
        "[:pronounce adjective]",
        "[:pronounce verb]",

        # Punct command.
        "[:punct none]",
        "[:punct some]",
        "[:punct all]",
        "[:punct pass]",

        # Rate command.
        "[:pitch 75]",
        "[:pitch 200]",
        "[:pitch 600]",

        # Say command.
        "[:say clause]",
        "[:say word]",
        "[:say letter]",
        "[:say filtered]",
        "[:say line]",

        # Skip command.
        "[:skip punct]",
        "[:skip rule]",
        "[:skip all]",
        "[:skip off]",
        "[:skip cpg]",
        "[:skip none]",

        # Tone command.
        "[:tone 0 0]",
        "[:tone 0 100]",
        "[:tone 0 1000]",
        "[:tone 100 0]",
        "[:tone 100 100]",
        "[:tone 100 1000]",
        "[:tone 1000 0]",
        "[:tone 1000 100]",
        "[:tone 1000 1000]",

        # Voice command.
        *[f"[:volume {o} 0]" for o in ["up", "lup", "rup", "down", "ldown", "rdown", "set", "lset", "rset"]],
        *[f"[:volume {o} 50]" for o in ["up", "lup", "rup", "down", "ldown", "rdown", "set", "lset", "rset"]],
        *[f"[:volume {o} 100]" for o in ["up", "lup", "rup", "down", "ldown", "rdown", "set", "lset", "rset"]],
        "[:volume sset 0 0]",
        "[:volume sset 0 50]",
        "[:volume sset 0 100]",
        "[:volume sset 50 0]",
        "[:volume sset 50 50]",
        "[:volume sset 50 100]",
        "[:volume sset 100 0]",
        "[:volume sset 100 50]",
        "[:volume sset 100 100]",

        # Bpm command.
        "[:bpm 0]",
        "[:bpm 120]",
        "[:bpm 60000]",

        # Import command
        "[:import C:\\example\\file.txt]",
        "[:import ..\\example\\file.txt]",
        "[:import .\\example\\file.txt]",
        "[:import /root/example/file.txt]",
        "[:import ../example/file.txt]",
        "[:import ./example/file.txt]",

        # Sound command.
        "[:sound __] {aa}",
        "[:sound n] {aa}",
        "[:sound n0] {aa}",
        "[:sound _n] {aa}",
        "[:sound _n0] {aa}",
        "[:sound name] {aa}",
        "[:sound name0] {aa}",
        "[:sound _name] {aa}",
        "[:sound _name0] {aa}",

        # Phrase command.
        "[:phrase __] {aa [:cp 0]}",
        "[:phrase n] {aa [:cp 0]}",
        "[:phrase n0] {aa [:cp 0]}",
        "[:phrase _n] {aa [:cp 0]}",
        "[:phrase _n0] {aa [:cp 0]}",
        "[:phrase name] {aa [:cp 0]}",
        "[:phrase name0] {aa [:cp 0]}",
        "[:phrase _name] {aa [:cp 0]}",
        "[:phrase _name0] {aa [:cp 0]}",

        # Voice command.
        *generate_valid_voice(),
    ])
    def test_valid(self, source: str) -> None:
        validate(self.__parse_node(source))
