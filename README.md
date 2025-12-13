# RTL-Flipper

Reverses text while keeping the important bits readable. Because sometimes you need backwards text that doesn't look like complete gibberish.
Personally mainly made this for translating games and software, where it just doesn't work with RTL.
**THIS UNFORTUNATELY DOES NOT WORK WELL WITH ARABIC AND DOESN'T FLIP ENGLISH!** Just wanted to let you know.

## What does this thing do?

Takes text and flips it around, but intelligently. It won't destroy your:
- Brackets and what's inside them `(like this)` or `[this]` or `{this}`
- Email addresses, URLs, and other token-y things
- The general structure of your text

So instead of turning `hello (world) test` into complete chaos, it actually keeps things somewhat readable.

## Why though?

¯\\\_(ツ)\_/¯ 

As said above, personally mainly made this for translating games and software, where it just doesn't work with RTL.

## Installation

You need Python 3 and the `regex` library:

```bash
pip install regex
```

That's it. No framework hell, no dependency nightmares.

## Usage

```bash
# Flip a file
python flip_lines.py input.txt output.txt

# Flip stdin to stdout
echo "hello world" | python flip_lines.py

# Or just
python flip_lines.py input.txt
```

Windows users: there's a `RUN.ps1` if you're into that. Just put whatever you want into input.txt.

## Technical stuff (for the nerds)

- Handles **grapheme clusters** properly - emojis, combining characters, all that Unicode nonsense
- O(n²) bracket matching because it works and I'm not rewriting it
- Preserves whitespace around preserved tokens
- Won't explode on weird Unicode edge cases (probably)

## License

AGPL-3.0 - Use it, modify it, have fun. Just don't turn it into proprietary software. 
And yes, that includes running it as a web service. If you do, you gotta share the source.

## Contributing

If you find a bug, cool. If you want to add features, also cool. Just don't make the code worse please.
