// JavaScript port of flip_lines.py from https://github.com/Krislyz/RTL-Flipper (AGPL-3.0)
(function (root) {
  var seg = typeof Intl !== 'undefined' && Intl.Segmenter ? new Intl.Segmenter(undefined, { granularity: 'grapheme' }) : null;
  var TOKEN_RE = /[A-Za-z0-9._%+\-]+/g;
  var SPACE_RE = /^\p{Z}$/u;
  var pairs = { '(': ')', '[': ']', '{': '}' };
  var inv = { ')': '(', ']': '[', '}': '{' };

  function graphemes(s) {
    return seg ? Array.from(seg.segment(s), function (x) { return x.segment; }) : Array.from(s);
  }

  function reverseGraphemes(s) {
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
        for (k = j - 1; k >= i; k--) out.push(g[k]);
        i = j;
      }
    }
    return out.join('');
  }

  function flipText(text) {
    return text.split('\n').map(function (line) {
      return reverseGraphemes(line.replace(/\r$/, ''));
    }).join('\n');
  }

  root.rtlFlip = flipText;
  if (typeof module !== 'undefined') module.exports = flipText;
})(typeof window !== 'undefined' ? window : globalThis);
