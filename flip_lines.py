#!/usr/bin/env python3

import argparse
import sys
import unicodedata

try:
    import regex as re
except ImportError:
    # this is for the people who somehow don't have pip
    sys.stderr.write("Missing dependency: pip install regex\n")
    sys.exit(1)

# defines so stuff will be easier
GRAPHEME_RE = re.compile(r'\X')
# \p{Nd} is digits from every script, arabic numbers read left to right too
TOKEN_RE    = re.compile(r'[A-Za-z\p{Nd}._%+\-]+')
LATIN_RE    = re.compile(r'[A-Za-z]')
SPACE_RE    = re.compile(r'\p{Z}')

# Arabic letters change shape depending on their neighbours, and software without
# RTL support usually can't do that either. So every letter gets swapped for its
# ready-made presentation form before the flip.
# SHAPES: letter -> {'<isolated>' / '<final>' / '<initial>' / '<medial>': form}
SHAPES = {}
for _cp in [*range(0xFB50, 0xFC00), *range(0xFE70, 0xFF00)]:
    _d = unicodedata.decomposition(chr(_cp)).split()
    if _d and _d[0] in ('<isolated>', '<final>', '<initial>', '<medial>'):
        SHAPES.setdefault(unicodedata.normalize('NFKC', chr(_cp)), {})[_d[0]] = chr(_cp)

LAM, TATWEEL, ZWNJ = chr(0x644), chr(0x640), chr(0x200C)

def shape_arabic(run):
    # run is a list of graphemes in reading order, marks ride along on their letter

    def joins_next(x):
        return ZWNJ not in x and (x[0] == TATWEEL or '<initial>' in SHAPES.get(x[0], ()))

    def joins_prev(x):
        return x[0] == TATWEEL or '<final>' in SHAPES.get(x[0], ())

    out = []
    k = 0
    while k < len(run):
        x = run[k]
        prev = k > 0 and joins_next(run[k - 1]) and joins_prev(x)
        nxt = k + 1 < len(run) and joins_next(x) and joins_prev(run[k + 1])

        # lam + alef is always written as one ligature
        pair = SHAPES.get(x[0] + run[k + 1][0]) if nxt and x[0] == LAM else None
        if pair:
            out.append(pair['<final>' if prev else '<isolated>'] + x[1:] + run[k + 1][1:])
            k += 2
            continue

        if prev:
            form = '<medial>' if nxt else '<final>'
        else:
            form = '<initial>' if nxt else '<isolated>'
        out.append(SHAPES.get(x[0], {}).get(form, x[0]) + x[1:])
        k += 1
    return out

def reverse_graphemes(s: str, english: bool = False) -> str:
    g = GRAPHEME_RE.findall(s)
    n = len(g)
    ignored = [False] * n
    whole = ''.join(g)

    def span_to_idx(a, b):
        # this is the slow, stupid, but absolutely bulletproof way.
        # DO NOT CHANGE unless you're like Linus or smthin
        pos = 0
        i = 0
        while i < n and pos < a:
            pos += len(g[i])
            i += 1
        start = i
        while i < n and pos < b:
            pos += len(g[i])
            i += 1
        return start, i

    pairs = {'(': ')', '[': ']', '{': '}'}
    inv = {v: k for k, v in pairs.items()}

    stack = []
    for i, ch in enumerate(g):
        if ch in pairs:
            stack.append((i, ch))
        elif ch in inv:
            # bracket matcher. it's O(n²). No, I don't care.
            # It works. Touch it and everything WILL fall apart.
            for j in range(len(stack) - 1, -1, -1):
                if stack[j][1] == inv[ch]:
                    open_i, _ = stack.pop(j)
                    for k in range(open_i, i + 1):
                        ignored[k] = True
                    break

    for m in TOKEN_RE.finditer(whole):
        # --english: words get flipped like everything else, plain numbers still stay
        if english and LATIN_RE.search(m.group()):
            continue
        si, ei = span_to_idx(*m.span())
        for k in range(si, ei):
            ignored[k] = True

    is_space = SPACE_RE
    i = 0
    while i < n:
        if ignored[i]:
            j = i
            while j < n and ignored[j]:
                j += 1

            a = i - 1
            while a >= 0 and is_space.fullmatch(g[a]):
                ignored[a] = True
                a -= 1

            i = j
        else:
            i += 1

    out = []
    i = 0
    while i < n:
        if ignored[i]:
            out.append(g[i])
            i += 1
        else:
            j = i
            while j < n and not ignored[j]:
                j += 1
            out.extend(reversed(shape_arabic(g[i:j])))
            i = j

    return "".join(out)


def process_stream(fin, fout, english=False):
    for line in fin:
        nl = line.endswith("\n")
        # Windows CRLF backwards compatibility
        line = line.rstrip("\n\r")
        fout.write(reverse_graphemes(line, english))
        if nl:
            fout.write("\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Reverses RTL text while keeping brackets, numbers and English readable.")
    ap.add_argument("input", nargs="?", help="input file, stdin if left out")
    ap.add_argument("output", nargs="?", help="output file, stdout if left out")
    ap.add_argument("-e", "--english", action="store_true", help="flip English too (numbers still stay)")
    args = ap.parse_args()
    in_path, out_path = args.input, args.output

    sys.stdout.reconfigure(encoding="utf-8")

    if in_path:
        try:
            fin = open(in_path, "r", encoding="utf-8", newline="")
        except OSError as e:
            sys.stderr.write(f"Failed to open {in_path}: {e}\n")
            sys.exit(1)
    else:
        fin = sys.stdin

    if out_path:
        # some win stuff breaks without this so don't touch
        with open(out_path, "w", encoding="utf-8-sig", newline="") as fout:
            process_stream(fin, fout, args.english)
    else:
        process_stream(fin, sys.stdout, args.english)

    if in_path:
        fin.close()
