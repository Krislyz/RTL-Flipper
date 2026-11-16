#!/usr/bin/env python3
# run with: python test_flip.py   (or pytest)

import subprocess
import sys

from flip_lines import reverse_graphemes as flip


def u(*codepoints):
    # arabic is written as code points here so the shapes are easy to check
    return "".join(map(chr, codepoints))


def test_hebrew_keeps_brackets_and_tokens():
    assert flip("שלום (עולם) בדיקה user@mail.com") == "םולש (עולם)הקידב  user@mail.com"


def test_arabic_letters_get_their_joined_shapes():
    # marhaba: initial meem, final reh, initial hah, medial beh, final alef, then reversed
    assert flip(u(0x645, 0x631, 0x62D, 0x628, 0x627)) == u(0xFE8E, 0xFE92, 0xFEA3, 0xFEAE, 0xFEE3)


def test_arabic_lam_alef_becomes_one_ligature():
    assert flip(u(0x644, 0x627)) == u(0xFEFB)
    # salam: initial seen, final lam-alef, isolated meem
    assert flip(u(0x633, 0x644, 0x627, 0x645)) == u(0xFEE1, 0xFEFC, 0xFEB3)


def test_arabic_marks_stay_on_their_letter():
    # meem+fatha, reh+sukun
    assert flip(u(0x645, 0x64E, 0x631, 0x652)) == u(0xFEAE, 0x652, 0xFEE3, 0x64E)


def test_zwnj_stops_the_join():
    # Persian mi-khaham, the yeh must not join the kheh after the ZWNJ (0x200C)
    assert flip(u(0x645, 0x6CC, 0x200C, 0x62E, 0x648, 0x627, 0x647, 0x645)) == \
        u(0xFEE2, 0xFEEB, 0xFE8D, 0xFEEE, 0xFEA7, 0xFBFD, 0x200C, 0xFEE3)


def test_arabic_digits_are_not_reversed():
    # "aam 123" with arabic-indic digits
    assert flip(u(0x639, 0x627, 0x645, 0x20, 0x661, 0x662, 0x663)) == \
        u(0xFEE1, 0xFE8E, 0xFECB, 0x20, 0x661, 0x662, 0x663)


def test_arabic_inside_brackets_is_left_alone():
    assert flip("{" + u(0x627, 0x633, 0x645) + "}") == "{" + u(0x627, 0x633, 0x645) + "}"


def test_english_is_kept_by_default():
    assert flip("hello world") == "hello world"


def test_english_flag_flips_english():
    assert flip("hello world", english=True) == "dlrow olleh"
    assert flip("שלום hello", english=True) == "olleh םולש"


def test_english_flag_still_keeps_numbers():
    assert flip("abc 123", english=True) == "cba 123"


def test_cli_english_argument():
    for flag in ("-e", "--english"):
        out = subprocess.run([sys.executable, "flip_lines.py", flag], input="hello\n",
                             capture_output=True, text=True, encoding="utf-8")
        assert out.stdout == "olleh\n", (flag, out.stdout, out.stderr)


if __name__ == "__main__":
    failed = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            try:
                fn()
                print("ok  ", name)
            except Exception as e:
                failed += 1
                print("FAIL", name, type(e).__name__, e)
    sys.exit(1 if failed else 0)
