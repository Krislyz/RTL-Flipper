// JavaScript port of flip_lines.py from https://github.com/Krislyz/RTL-Flipper (AGPL-3.0)
(function (root) {
  var seg = typeof Intl !== 'undefined' && Intl.Segmenter ? new Intl.Segmenter(undefined, { granularity: 'grapheme' }) : null;
  // \p{Nd} is digits from every script, arabic numbers read left to right too
  var TOKEN_RE = /[A-Za-z\p{Nd}._%+\-]+/gu;
  var LATIN_RE = /[A-Za-z]/;
  var SPACE_RE = /^\p{Z}$/u;
  var pairs = { '(': ')', '[': ']', '{': '}' };
  var inv = { ')': '(', ']': '[', '}': '{' };

  // Arabic letters change shape depending on their neighbours, and software without
  // RTL support usually can't do that either. So every letter gets swapped for its
  // ready-made presentation form before the flip.
  // SHAPES: letter -> [isolated, final, initial, medial]
  // The python reads the form names from unicodedata. JS has no such thing, but the
  // unicode blocks list each letter's forms in that same order, so count along.
  var SHAPES = {};
  [[0xFB50, 0xFBFF], [0xFE70, 0xFEFF]].forEach(function (range) {
    var last = '', idx = 0;
    for (var cp = range[0]; cp <= range[1]; cp++) {
      var form = String.fromCharCode(cp), letter = form.normalize('NFKC');
      if (letter === form) continue;
      idx = letter === last ? idx + 1 : 0;
      // the one place the order breaks: these two are initial and medial alef maksura
      if (cp === 0xFBE8) idx = 2;
      last = letter;
      (SHAPES[letter] = SHAPES[letter] || [])[idx] = form;
    }
  });
  var LAM = String.fromCharCode(0x644), TATWEEL = String.fromCharCode(0x640), ZWNJ = String.fromCharCode(0x200C);

  function shapeArabic(run) {
    // run is a list of graphemes in reading order, marks ride along on their letter
    function joinsNext(x) {
      return x.indexOf(ZWNJ) < 0 && (x[0] === TATWEEL || !!(SHAPES[x[0]] && SHAPES[x[0]][2]));
    }
    function joinsPrev(x) {
      return x[0] === TATWEEL || !!(SHAPES[x[0]] && SHAPES[x[0]][1]);
    }
    var out = [], k = 0;
    while (k < run.length) {
      var x = run[k];
      var prev = k > 0 && joinsNext(run[k - 1]) && joinsPrev(x);
      var nxt = k + 1 < run.length && joinsNext(x) && joinsPrev(run[k + 1]);

      // lam + alef is always written as one ligature
      var pair = nxt && x[0] === LAM ? SHAPES[x[0] + run[k + 1][0]] : null;
      if (pair) {
        out.push(pair[prev ? 1 : 0] + x.slice(1) + run[k + 1].slice(1));
        k += 2;
        continue;
      }

      var form = prev ? (nxt ? 3 : 1) : (nxt ? 2 : 0);
      out.push(((SHAPES[x[0]] || [])[form] || x[0]) + x.slice(1));
      k++;
    }
    return out;
  }

  function graphemes(s) {
    return seg ? Array.from(seg.segment(s), function (x) { return x.segment; }) : Array.from(s);
  }

  function reverseGraphemes(s, english) {
    var g = graphemes(s), n = g.length, ignored = new Array(n).fill(false), whole = g.join('');

    // character span -> grapheme index range, same slow and bulletproof walk as the python
    function spanToIdx(a, b) {
      var pos = 0, i = 0;
      while (i < n && pos < a) { pos += g[i].length; i++; }
      var start = i;
      while (i < n && pos < b) { pos += g[i].length; i++; }
      return [start, i];
    }

    var stack = [], i, j, k;
    for (i = 0; i < n; i++) {
      var ch = g[i];
      if (pairs[ch]) stack.push([i, ch]);
      else if (inv[ch]) {
        // O(n^2) bracket matching, same as the python
        for (j = stack.length - 1; j >= 0; j--) {
          if (stack[j][1] === inv[ch]) {
            var openI = stack.splice(j, 1)[0][0];
            for (k = openI; k <= i; k++) ignored[k] = true;
            break;
          }
        }
      }
    }

    var m;
    TOKEN_RE.lastIndex = 0;
    while ((m = TOKEN_RE.exec(whole))) {
      // english: words get flipped like everything else, plain numbers still stay
      if (english && LATIN_RE.test(m[0])) continue;
      var r = spanToIdx(m.index, m.index + m[0].length);
      for (k = r[0]; k < r[1]; k++) ignored[k] = true;
    }

    i = 0;
    while (i < n) {
      if (ignored[i]) {
        j = i;
        while (j < n && ignored[j]) j++;
        var a = i - 1;
        while (a >= 0 && SPACE_RE.test(g[a])) { ignored[a] = true; a--; }
        i = j;
      } else i++;
    }

    var out = [];
    i = 0;
    while (i < n) {
      if (ignored[i]) { out.push(g[i]); i++; }
      else {
        j = i;
        while (j < n && !ignored[j]) j++;
        var run = shapeArabic(g.slice(i, j));
        for (k = run.length - 1; k >= 0; k--) out.push(run[k]);
        i = j;
      }
    }
    return out.join('');
  }

  // english = true flips English too, same as the python's --english
  function flipText(text, english) {
    return text.split('\n').map(function (line) {
      return reverseGraphemes(line.replace(/\r$/, ''), english);
    }).join('\n');
  }

  root.rtlFlip = flipText;
  if (typeof module !== 'undefined') module.exports = flipText;
})(typeof window !== 'undefined' ? window : globalThis);
