import os
import os.path
import pytest
import sys

# Required for local imports.
ROOTDIR = os.path.abspath(os.path.join(__file__, "..", ".."))
if ROOTDIR not in sys.path:
    sys.path.insert(0, ROOTDIR)

# Local import should go under this comment.
from components.lexer import Lexer
from components.node import *
from components.parser import Parser
from components.processor import Processor
from components.state import State
from constants import VOICE_DEFAULTS
from utils.exceptions import ProcessorException


DIR_TEST_FILES = os.path.abspath(os.path.join("tests", "test_files"))


class Buffer(object):
    def __init__(self) -> None:
        self.filename = "<BufferObject>"
        self.reset()

    def reset(self) -> None:
        self.buffer = ""

    def write(self, buffer: str) -> None:
        self.buffer += buffer


class TestProcessor:
    def __setup(self, source: str) -> tuple[Buffer, Processor]:
        buffer = Buffer()
        state = State("", [DIR_TEST_FILES])

        tokens = Lexer(source).get_tokens()
        nodes = Parser(tokens).get_nodes()
        processor = Processor(nodes, state, writer=buffer)

        return (buffer, processor)

    def test_init(self) -> None:
        _, processor = self.__setup("p1 p2<10,10> [:comma 50]")

        assert processor.index == 0
        assert processor.nodes == [
            PhonemeNode(None, "p1", 0, 0),
            PhonemeNode(None, "p2", 10, 10),
            CommandNode(None, "comma", [50], []),
            EofNode(None)
        ]
        assert isinstance(processor.writer, Buffer)

    def test_advance(self) -> None:
        _, processor = self.__setup("p1 p2<10,10> [:comma 50]")

        assert processor.node == PhonemeNode(None, "p1", 0, 0)
        processor.advance()
        assert processor.node == PhonemeNode(None, "p2", 10, 10)
        processor.advance()
        assert processor.node == CommandNode(None, "comma", [50], [])
        processor.advance()
        assert isinstance(processor.node, EofNode)
        processor.advance()
        assert isinstance(processor.node, EofNode)

    @pytest.mark.parametrize("source, expected", [
        # Test un-set BPM.
        # ("_<1>", "[_<1>]"),

        # Test different BPM values.
        ("[:bpm 15] _<1>", "[_<4000>]"),
        ("[:bpm 30] _<1>", "[_<2000>]"),
        ("[:bpm 60] _<1>", "[_<1000>]"),
        ("[:bpm 120] _<1>", "[_<500>]"),
        ("[:bpm 150] _<1>", "[_<400>]"),
        ("[:bpm 200] _<1>", "[_<300>]"),
        ("[:bpm 240] _<1>", "[_<250>]"),

        # Test different pitch lengths.
        ("[:bpm 60] _<0.125>", "[_<125>]"),
        ("[:bpm 60] _<0.33>", "[_<330>]"),
        ("[:bpm 60] _<0.25>", "[_<250>]"),
        ("[:bpm 60] _<0.5>", "[_<500>]"),
        ("[:bpm 60] _<1>", "[_<1000>]"),
        ("[:bpm 60] _<2>", "[_<2000>]"),
        ("[:bpm 60] _<4>", "[_<4000>]"),

        # Test multiple BPM sets.
        ("[:bpm 60] _<1> [:bpm 120] _<2>", "[_<1000>]" * 2),

        # Test BPM reset.
        ("[:bpm 60] _<1> [:bpm 0] _<1000>", "[_<1000>]" * 2),
    ])
    def test_process_bpm(self, source: str, expected: str) -> None:
        buffer, processor = self.__setup(source)
        processor.process()

        assert buffer.buffer == expected

    @pytest.mark.parametrize("source", [
        "[:comma 50]", "[:cp 50]",
        "[:dv sx 0]",
        "[:error ignore]",
        "[:name Paul]",
        *[f"[:n{o}]" for o in "bdfhkpruw"],
        "[:period 50]", "[:pp 50]",
        "[:punct none]",
        "[:rate 200]",
        "[:say clause]",
        "[:skip punct]",
        "[:tone 100 1000]",
        "[:volume up 50]",
        "[:volume sset 50 50]",
    ])
    def test_process_bypass(self, source: str) -> None:
        buffer, processor = self.__setup(source)
        processor.process()

        assert buffer.buffer == source

    @pytest.mark.parametrize("source", [
        "[:mode math on]",
        "[:phoneme arpabet on]",
        "[:pitch 35]",
        "[:pronounce alternate]",
    ])
    def test_process_ignore(self, source: str) -> None:
        buffer, processor = self.__setup(source)
        processor.process()

        assert buffer.buffer == ""

    @pytest.mark.parametrize("filename, exists", [
        (os.path.abspath("./tests/test_files/import_command.opendec"), True),
        (os.path.abspath(".\\tests\\test_files\\import_command.opendec"), True),
        ("./tests/test_files/import_command.opendec", True),
        (".\\tests\\test_files\\import_command.opendec", True),
        ("import_command.opendec", True),

        (os.path.abspath("./tests/test_files/doesnotexist.opendec"), False),
        (os.path.abspath(".\\tests\\test_files\\doesnotexist.opendec"), False),
        ("./tests/test_files/doesnotexist.opendec", False),
        (".\\tests\\test_files\\doesnotexist.opendec", False),
        ("doesnotexist.opendec", False),
    ])
    def test_process_import(self, filename: str, exists: bool) -> None:
        source = f"[:import {filename}]"
        buffer, processor = self.__setup(source)

        if not exists:
            with pytest.raises(ProcessorException):
                processor.process()
        else:
            processor.process()
            assert buffer.buffer == f"[:comma 50]"


    @pytest.mark.parametrize("source, expected", [
        # Looping edge-cases.
        ("[:loop 0] {_}", ""),
        ("[:loop 1] {_}", "[_]"),

        # Looping phonemes only.
        ("[:loop 5] {_}", "[_]" * 5),
        ("[:loop 5] {b}", "[b]" * 5),
        ("[:loop 5] {aa}", "[aa]" * 5),
        ("[:loop 5] {aa<>}", "[aa]" * 5),
        ("[:loop 5] {aa<,>}", "[aa]" * 5),
        ("[:loop 5] {aa<,10>}", "[aa<,10>]" * 5),
        ("[:loop 5] {aa<500>}", "[aa<500>]" * 5),
        ("[:loop 5] {aa<5.0>}", "[aa<5>]" * 5),
        ("[:loop 5] {aa<500,10>}", "[aa<500,10>]" * 5),
        ("[:loop 5] {aa<5.0,10>}", "[aa<5,10>]" * 5),

        # Looping commands.
        ("[:loop 5] {[:pitch 35]}", ""),
        ("[:loop 5] {[:cp 50]}", "[:cp 50]" * 5),

        # Looping phonemes and commands.
        ("[:loop 5] {aa [:pitch 35]}", "[aa]" * 5),
        ("[:loop 5] {aa [:cp 50]}", "[aa][:cp 50]" * 5),
    ])
    def test_process_loop(self, source: str, expected: str) -> None:
        buffer, processor = self.__setup(source)
        processor.process()

        assert buffer.buffer == expected

    @pytest.mark.parametrize("filename, exists", [
        (os.path.abspath("./tests/test_files/blah.wav"), True),
        (os.path.abspath(".\\tests\\test_files\\blah.wav"), True),
        ("./tests/test_files/blah.wav", True),
        (".\\tests\\test_files\\blah.wav", True),
        ("blah.wav", True),

        (os.path.abspath("./tests/test_files/doesnotexist.wav"), False),
        (os.path.abspath(".\\tests\\test_files\\doesnotexist.wav"), False),
        ("./tests/test_files/doesnotexist.wav", False),
        (".\\tests\\test_files\\doesnotexist.wav", False),
        ("test_files.wav", False),
    ])
    def test_process_play(self, filename: str, exists: bool) -> None:
        source = f"[:play {filename}]"
        buffer, processor = self.__setup(source)

        if not exists:
            with pytest.raises(ProcessorException):
                processor.process()
        else:
            processor.process()
            assert buffer.buffer == f"[:play {os.path.join(DIR_TEST_FILES, 'blah.wav')}]"

    def test_process_name(self) -> None:
        source = "[:voice name] { sx 0 hs 110 } [:name name]"
        buffer, processor = self.__setup(source)
        processor.process()

        assert "name" in processor.state.voices
        assert buffer.buffer == "[:np][:dv sx 0][:dv hs 110]"

    @pytest.mark.parametrize("source, expected", [
        # Basic phoneme processing - symbols.
        ("_", "[_]"),
        ("_<>", "[_]"),
        ("_<,>", "[_]"),
        ("_<,10>", "[_]"),
        ("_<500,>", "[_<500>]"),
        ("_<5.0,>", "[_<5>]"),
        ("_<500,10>", "[_<500>]"),
        ("_<5.0,10>", "[_<5>]"),

        # Basic phoneme processing - consonant.
        ("b", "[b]"),
        ("b<>", "[b]"),
        ("b<,>", "[b]"),
        ("b<,10>", "[b]"),
        ("b<500,>", "[b<500>]"),
        ("b<5.0,>", "[b<5>]"),
        ("b<500,10>", "[b<500>]"),
        ("b<5.0,10>", "[b<5>]"),

        # Basic phoneme processing - vowel.
        ("aa", "[aa]"),
        ("aa<>", "[aa]"),
        ("aa<,>", "[aa]"),
        ("aa<,10>", "[aa<,10>]"),
        ("aa<500,>", "[aa<500>]"),
        ("aa<5.0,>", "[aa<5>]"),
        ("aa<500,10>", "[aa<500,10>]"),
        ("aa<5.0,10>", "[aa<5,10>]"),

        # Sound processing.
        ("[:sound ba] {b aa} ba<15>", "[b<15>][aa]"),
        ("[:sound ba] {b aa} ba<30>", "[b<15>][aa<15>]"),
        ("[:sound ba] {b aa} ba<15,10>", "[b<15>][aa<,10>]"),
        ("[:sound ba] {b aa} ba<30,10>", "[b<15>][aa<15,10>]"),
        ("[:sound ba] {b aa} ba<120,10>", "[b<15>][aa<105,10>]"),
        (
            "[:sound ba] {b aa} ba<30> ba<30> ba<30>",
            "[b<15>][aa<15>]" * 3
        ),
        ("[:bpm 60] [:sound ba] {b aa} ba<1>", "[b<15>][aa<985>]"),
        ("[:bpm 60] [:sound ba] {b aa} ba<1> ba<1>", "[b<15>][aa<985>]" * 2),

        # Phrase processing.
        ("[:phrase a] {aa} a", "[aa]"),
        ("[:phrase a] {aa<>} a", "[aa]"),
        ("[:phrase a] {aa<,>} a", "[aa]"),
        ("[:phrase a] {aa<,10>} a", "[aa<,10>]"),
        ("[:phrase a] {aa<500,>} a", "[aa<500>]"),
        ("[:phrase a] {aa<5.0,>} a", "[aa<5>]"),
        ("[:phrase a] {aa<500,10>} a", "[aa<500,10>]"),
        ("[:phrase a] {aa<5.0,10>} a", "[aa<5,10>]"),
        ("[:phrase a] {aa} a a", "[aa]" * 2),
        ("[:phrase a] {aa aa} a", "[aa]" * 2),
        ("[:phrase a] {aa aa} a a", "[aa]" * 4),
        ("[:bpm 60][:phrase a] {aa<1>} a", "[aa<1000>]"),
        ("[:bpm 60][:phrase a] {aa<1>} a a", "[aa<1000>]" * 2),
    ])
    def test_process_phoneme(self, source, expected) -> None:
        buffer, processor = self.__setup(source)
        processor.process()

        assert buffer.buffer == expected

    def test_process_phrase(self) -> None:
        source = "[:phrase name] { b l ax }"
        buffer, processor = self.__setup(source)
        processor.process()

        assert buffer.buffer == ""

        assert len(processor.state.phrases) == 1
        assert len(processor.state.sounds) == 0
        assert len(processor.state.voices) == 0

        assert "name" in processor.state.phrases
        assert "name" not in processor.state.sounds
        assert "name" not in processor.state.voices

        assert processor.state.phrases["name"] == [
            PhonemeNode(None, "b", 0, 0),
            PhonemeNode(None, "l", 0, 0),
            PhonemeNode(None, "ax", 0, 0),
        ]

    def test_process_sound(self) -> None:
        source = "[:sound name] { b l ax }"
        buffer, processor = self.__setup(source)
        processor.process()

        assert buffer.buffer == ""

        assert len(processor.state.phrases) == 0
        assert len(processor.state.sounds) == 1
        assert len(processor.state.voices) == 0

        assert "name" not in processor.state.phrases
        assert "name" in processor.state.sounds
        assert "name" not in processor.state.voices

        assert processor.state.sounds["name"] == [
            PhonemeNode(None, "b", 0, 0),
            PhonemeNode(None, "l", 0, 0),
            PhonemeNode(None, "ax", 0, 0),
        ]

    def test_process_voice(self) -> None:
        source = "[:voice name] { sx 0 hs 110}"
        buffer, processor = self.__setup(source)
        processor.process()

        assert buffer.buffer == ""

        assert len(processor.state.phrases) == 0
        assert len(processor.state.sounds) == 0
        assert len(processor.state.voices) == 1

        assert "name" not in processor.state.phrases
        assert "name" not in processor.state.sounds
        assert "name" in processor.state.voices

        assert processor.state.voices["name"] == {"sx": 0, "hs": 110}

