"""Python syntax highlighting for Copilot Python Studio."""
import builtins
import keyword
import re

from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat


def _fmt(color, bold=False, italic=False):
    f = QTextCharFormat()
    f.setForeground(QColor(color))
    if bold:
        f.setFontWeight(QFont.Bold)
    f.setFontItalic(italic)
    return f


FORMATS = {
    "keyword": _fmt("#0000CC", bold=True),
    "builtin": _fmt("#7B2D8E"),
    "string": _fmt("#008000"),
    "comment": _fmt("#808080", italic=True),
    "number": _fmt("#B05000"),
    "decorator": _fmt("#A06000"),
    "defname": _fmt("#005A9E", bold=True),
    "self": _fmt("#7B2D8E", italic=True),
}
KEYWORDS = "|".join(sorted(k for k in keyword.kwlist + keyword.softkwlist if k.isidentifier() and k != "_"))
BUILTINS = "|".join(sorted(n for n in dir(builtins) if not n.startswith("_") and n not in keyword.kwlist
                           and n[0].islower()))
RULES = [
    (re.compile(rf"\b(?:{BUILTINS})\b(?=\s*\()"), "builtin"),
    (re.compile(rf"\b(?:{KEYWORDS})\b"), "keyword"),
    (re.compile(r"\b(?:self|cls)\b"), "self"),
    (re.compile(r"\b(?:def|class)\s+(\w+)"), "defname"),
    (re.compile(r"^\s*@[\w.]+"), "decorator"),
    (re.compile(r"\b(?:0[xX][0-9a-fA-F_]+|0[bB][01_]+|0[oO][0-7_]+|\d[\d_]*\.?[\d_]*(?:[eE][+-]?\d+)?j?)\b"), "number"),
]
OPEN_TRIPLE = re.compile(r"""(?i)(?<!\w)(?:[rbuf]|br|rb|fr|rf)?('''|\"\"\")""")
ONE_LINE = re.compile(r"""(?i)(?<!\w)(?:[rbuf]|br|rb|fr|rf)?(?:'(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*")""")
STATE_NONE, STATE_SQ3, STATE_DQ3 = 0, 1, 2


class PythonHighlighter(QSyntaxHighlighter):
    def highlightBlock(self, text):
        state = self.previousBlockState()
        taken = []          # spans already coloured as string or comment
        pos = 0

        if state in (STATE_SQ3, STATE_DQ3):
            end = self._close_triple(text, 0, "'''" if state == STATE_SQ3 else '"""')
            if end < 0:
                self.setFormat(0, len(text), FORMATS["string"])
                self.setCurrentBlockState(state)
                return
            self.setFormat(0, end, FORMATS["string"])
            taken.append((0, end))
            pos = end
        self.setCurrentBlockState(STATE_NONE)

        while pos < len(text):
            found = []
            for kind, rx in (("t", OPEN_TRIPLE), ("s", ONE_LINE)):
                m = rx.search(text, pos)
                if m:
                    found.append((m.start(), 0 if kind == "t" else 1, kind, m))
            hash_at = self._comment_start(text, pos)
            if hash_at >= 0:
                found.append((hash_at, 2, "c", None))
            if not found:
                break
            at, _order, kind, m = min(found, key=lambda c: (c[0], c[1]))
            if kind == "c":
                self.setFormat(at, len(text) - at, FORMATS["comment"])
                taken.append((at, len(text)))
                break
            if kind == "s":
                self.setFormat(at, m.end() - at, FORMATS["string"])
                taken.append((at, m.end()))
                pos = m.end()
                continue
            quote = m.group(1)
            end = self._close_triple(text, m.end(), quote)
            if end < 0:
                self.setFormat(at, len(text) - at, FORMATS["string"])
                taken.append((at, len(text)))
                self.setCurrentBlockState(STATE_SQ3 if quote == "'''" else STATE_DQ3)
                break
            self.setFormat(at, end - at, FORMATS["string"])
            taken.append((at, end))
            pos = end

        def free(a, b):
            return not any(a < e and b > s for s, e in taken)

        for rx, name in RULES:
            for m in rx.finditer(text):
                a, b = (m.start(1), m.end(1)) if name == "defname" else (m.start(), m.end())
                if free(a, b):
                    self.setFormat(a, b - a, FORMATS[name])

    @staticmethod
    def _close_triple(text, start, quote):
        i = start
        while i < len(text):
            if text[i] == "\\":
                i += 2
                continue
            if text.startswith(quote, i):
                return i + 3
            i += 1
        return -1

    @staticmethod
    def _comment_start(text, pos):
        """The first '#' at or after pos that is not inside a one-line string, or -1."""
        quote = None
        i = pos
        while i < len(text):
            c = text[i]
            if quote:
                if c == "\\":
                    i += 2
                    continue
                if c == quote:
                    quote = None
            elif c in "'\"":
                if text.startswith(c * 3, i):
                    return -1      # a triple-quoted string opens here; the string pass deals with it
                quote = c
            elif c == "#":
                return i
            i += 1
        return -1
