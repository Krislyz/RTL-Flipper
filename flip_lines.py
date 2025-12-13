#!/usr/bin/env python3

import sys

try:
    import regex as re
except ImportError:
    # this is for the people who somehow don't have pip
    sys.stderr.write("Missing dependency: pip install regex\n")
    sys.exit(1)

# defines so stuff will be easier
GRAPHEME_RE = re.compile(r'\X')
TOKEN_RE    = re.compile(r'[A-Za-z0-9._%+\-]+')
SPACE_RE    = re.compile(r'\p{Z}')

def reverse_graphemes(s: str) -> str:
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
            out.extend(reversed(g[i:j]))
            i = j

    return "".join(out)


def process_stream(fin, fout):
    for line in fin:
        nl = line.endswith("\n")
        # Windows CRLF backwards compatibility
        line = line.rstrip("\n\r")
        fout.write(reverse_graphemes(line))
        if nl:
            fout.write("\n")


if __name__ == "__main__":
    args = sys.argv[1:]
    in_path = args[0] if len(args) else None
    out_path = args[1] if len(args) > 1 else None

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
            process_stream(fin, fout)
    else:
        process_stream(fin, sys.stdout)

    if in_path:
        fin.close()
