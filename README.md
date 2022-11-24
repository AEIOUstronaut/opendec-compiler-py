# OpenDec Compiler - Python Implementation
The OpenDec compiler takes source code following the OpenDec language
specification, compiles it to text understood by a text-to-speech engine
(current version uses DecTalk as the text-to-speech engine), then exports the
intermetidate file as a WAVE (.wav) file.

To compile a project, run `compile.py` from a directory that contains your
OpenDec source code.

OpenDec source code files should have the `.opendec` extension. It is
recommended that any files meant for importing should have the `.opendeci`
extension - this is to prevent the compiler from accidentally compiling files
that are intended to be used for import only.


# OpenDec Requirements
Before being able to compile any source code, you must have a text-to-speech
engine available and it must be stored in the `bin` directory.

The only other requirement is `pytest` for running the OpenDec tests - this is
not required for running the compiler.


# OpenDec Compiler Usage
```
Usage: compile.py [-h] [-c] [-e ENGINE] [-I INCLUDE] [-v] [--clean] [sources ...]

Positional Arguments:
  sources               Opendec source files or text to compile.

Optional Arguments:
  -h, --help
        Show this help message and exit.

  -c, --cache
        Save the compiled intermediate files in the `build` directory.

  -e ENGINE, --engine ENGINE
        Text-to-speech engine to use. The engine must be in the `bin` directory.

  -I INCLUDE, --include INCLUDE
        Directories where included files may exist. This includes any files that
        are imported via [:import] or played via [:play].

  -v, --verbose
        Increase the logging verbosity on STDOUT.

  --clean
        Clean up compiler artifacts. This includes any intermediate files that
        have been cached in the `build` directory and file exported to the
        `export` directory.
```


## Examples
Assume that the compiler is being run in a directory that looks like this:
```
project/
├─ bin/
│  ├─ say.exe
│  ├─ alternative.exe
├─ build/
├─ export/
├─ imports/
│  ├─ phrases.opendeci
│  ├─ sounds.opendeci
│  ├─ voices.opendeci
├─ bassline.opendec
├─ harmony.opendec
├─ melody.opendec
├─ misc.opendeci
├─ notes.txt
```

To compile all OpenDec files (i.e. all files that end in `.opendec`):
```
python compile.py
```

To compile a specific file:
```
python compile.py bassline.opendec
```

To compile files that rely on `sounds.opendeci`:
```
python compile.py -I imports harmony.opendec melody.opendec
```

If you want to use an alternative text-to-speech engine, make sure that the
binary is in the `bin` directory and run:
```
python compile.py -I import -e alternative.exe harmony.opendec melody.opendec
```
