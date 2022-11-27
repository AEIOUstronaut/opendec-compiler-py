"""constants.py

Handy constants.
"""


import os
import os.path


# Handy paths.
DIR_ROOT = os.path.abspath(os.path.join(__file__, ".."))
DIR_BIN = os.path.join(DIR_ROOT, "bin")
DIR_BUILD = os.path.join(os.getcwd(), "build")
DIR_EXPORT = os.path.join(os.getcwd(), "export")
DIR_LIB = os.path.join(os.getcwd(), "lib")
DIR_SRC = os.path.join(os.getcwd(), "src")


# Regexes.
RE_SOUND = "^c*v+c*$"
RE_VARIABLE = "^(([a-zA-Z])|([_a-zA-Z][a-zA-Z0-9_]+))$"


# Command constants.
COMMANDS_BASE = [
    ## Base Commands
    "comma", "cp",      # Comma pause
    "dv",               # Define voice
    "error",            # Error handling functionality
    "mode",             # Text processing mode (NO EFFECT)
    "name",             # Change name
    "nb", "nd", "nf", "nh", "nk", "np", "nr", "nu", "nw",   # Change name alias
    "period", "pp",     # Period pause
    "phoneme",          # Modify phoneme interpretation (NO EFFECT)
    "pitch",            # Frequency difference between upper/lower (NO EFFECT)
    "play",             # Play specified wave (.wav) file
    "pronounce",        # Modify pronounciation rules (NO EFFECT)
    "punct",            # Punctuation processing method
    "rate",             # Rate of standard speech
    "say",              # Specify amount of data to be processed before speech
    "skip",             # Enable/disable speech rules
    "tone",             # Play a sine wave
    "volume",           # Modify the current volume
]
COMMANDS_EXTENDED = [
    ## Extended Commands
    "bpm",              # Convert phoneme length to number of beats, not ms
    "import",           # Import additional OpenDec files
]
COMMANDS_WITH_CONTEXT = [
    "loop",             # Repease segment a given number of times
    "phrase",           # Combine multiple phonemes
    "sound",            # Define a new simple phoneme
    "voice",            # Define a new voice
]
COMMANDS = COMMANDS_BASE + COMMANDS_EXTENDED + COMMANDS_WITH_CONTEXT


# Phoneme constants.
PHONEMES_CONSONANTS = [
    "b",    # _b_in
    "ch",   # _ch_in
    "d",    # _d_ebt
    "dh",   # _th_is
    "dx",   # ri_d_er
    "f",    # _f_in
    "g",    # _g_ive
    "hx",   # _h_ead
    "jh",   # _g_in
    "k",    # _c_at
    "l",    # _l_et
    "lx",   # be_ll_
    "m",    # _m_et
    "n",    # _n_et
    "nx",   # si_ng_
    "p",    # _p_in
    "r",    # _r_ed
    "rx",   # o_r_ation
    "s",    # _s_it
    "sh",   # _sh_in
    "t",    # _t_est
    "th",   # _th_in
    "tx",   # La_t_in
    "v",    # _v_est
    "w",    # _w_est
    "yx",   # _y_et
    "z",    # _z_oo
    "zh",   # mea_s_ure
]
PHONEMES_VOWELS = [
    "aa",   # f_a_rther
    "ae",   # b_a_t
    "ah",   # b_u_t
    "ao",   # b_ou_ght
    "aw",   # ab_ou_t
    "ax",   # _a_bout
    "ay",   # b_i_te
    "eh",   # b_e_t
    "el",   # bott_le_
    "en",   # butt_on_
    "er",   # b_ear"
    "ey",   # b_a_ke
    "ih",   # b_i_t
    "ir",   # b_eer_
    "iy",   # b_ea_t
    "or",   # b_ore_
    "ow",   # b_oa_t
    "oy",   # b_oy_
    "rr",   # b_ir_d
    "uh",   # b_oo_k
    "ur",   # p_oor_
    "uw",   # l_u_te
    "yu",   # c_u_te
]
PHONEMES_SYMBOLS = [
    ",",    # Comma pause
    ".",    # Period pause
    "_",    # Silence
    "'",    # Primary stress
    "`",    # Secondary stress
    "\"",   # Emphatic stress
]
PHONEMES = PHONEMES_CONSONANTS + PHONEMES_VOWELS + PHONEMES_SYMBOLS

PHONEMES_NOLENGTH = [",", ".", "'", "`", "\""]
PHONEMES_NOPITCH = PHONEMES_CONSONANTS + PHONEMES_SYMBOLS


# Text and character constants.
SPECIAL_CHARACTERS = ",{}[]<>"
WHITESPACE = " \n\r\t"

BREAK_CHARS = WHITESPACE + SPECIAL_CHARACTERS + "/"


# Voice constants.
VOICE_DEFAULT_NAMES = [
    "Betty",
    "Dennis",
    "Frank",
    "Harry",
    "Kit",
    "Paul",
    "Rita",
    "Ursula",
    "Wendy",
]
VOICE_MINMAX = {
    # Vocal track parameters.
    "sx": (0, 1),
    "hs": (65, 145),
    "f4": (2000, 4650),
    "f5": (2500, 4950),
    "b4": (100, 2048),
    "b5": (100, 2048),

    # Voicing sound source parameters.
    "br": (0, 72),
    "lx": (0, 100),
    "sm": (0, 100),
    "ri": (0, 100),
    "nf": (0, 100),
    "la": (0, 100),

    # Intonation parameters.
    "bf": (0, 40),
    "hr": (2, 100),
    "sr": (1, 100),
    "as": (0, 100),
    "qu": (0, 100),
    "ap": (50, 350),
    "pr": (0, 250),

    # Gain adjustment parameters.
    "lo": (0, 86),
    "gv": (0, 86),
    "gh": (0, 86),
    "gf": (0, 86),
    "g1": (0, 86),
    "g2": (0, 86),
    "g3": (0, 86),
    "g4": (0, 86),
}
VOICE_PARAMETERS = [parameter for parameter in VOICE_MINMAX]
