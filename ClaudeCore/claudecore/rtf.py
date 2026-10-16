"""RTF: WordPad's reader and writer, shared - ClaudeXP's WordPad and Gemini Distiller, and the Timeline's story reader.

to_rtf(doc) writes a QTextDocument as RTF; from_rtf(text, doc) reads RTF into one (fonts, sizes, colours,
bold/italic/underline/strike, alignment, paragraphs).
"""
import re

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QTextBlockFormat, QTextCharFormat, QTextCursor


def _rtf_escape(text):
    out = []
    for ch in text:
        if ch in "\\{}":
            out.append("\\" + ch)
        elif ch == "\t":
            out.append("\\tab ")
        elif ord(ch) > 127:
            code = ord(ch)
            out.append(f"\\u{code if code < 32768 else code - 65536}?")
        else:
            out.append(ch)
    return "".join(out)


def to_rtf(doc, generator="ClaudeXP WordPad 5.1.2600"):
    fonts, colors = [], ["#000000"]
    parts = []
    block = doc.begin()
    while block.isValid():
        bf = block.blockFormat()
        align = {Qt.AlignHCenter: "\\qc", Qt.AlignCenter: "\\qc", Qt.AlignRight: "\\qr"}.get(
            bf.alignment() & Qt.AlignHorizontal_Mask, "\\ql")
        parts.append("\\pard" + align + " ")
        if block.textList() is not None:
            parts.append("{\\pntext\\f0\\'B7\\tab}")
        it = block.begin()
        while not it.atEnd():
            frag = it.fragment()
            if frag.isValid():
                cf = frag.charFormat()
                fam = cf.fontFamilies()[0] if cf.fontFamilies() else (cf.fontFamily() or "Arial")
                if fam not in fonts:
                    fonts.append(fam)
                color = cf.foreground().color().name() if cf.foreground().style() != Qt.NoBrush else "#000000"
                if color not in colors:
                    colors.append(color)
                size = cf.fontPointSize() or 10
                codes = [f"\\f{fonts.index(fam)}", f"\\fs{round(size * 2)}", f"\\cf{colors.index(color) + 1}"]
                codes.append("\\b" if cf.fontWeight() >= QFont.Bold else "\\b0")
                codes.append("\\i" if cf.fontItalic() else "\\i0")
                codes.append("\\ul" if cf.fontUnderline() else "\\ulnone")
                codes.append("\\strike" if cf.fontStrikeOut() else "\\strike0")
                parts.append("".join(codes) + " " + _rtf_escape(frag.text().replace("\u2028", "\n")))
            it += 1
        parts.append("\\par\n")
        block = block.next()
    font_table = "".join(f"{{\\f{i}\\fnil\\fcharset0 {name};}}" for i, name in enumerate(fonts or ["Arial"]))
    color_table = "".join(f"\\red{int(c[1:3], 16)}\\green{int(c[3:5], 16)}\\blue{int(c[5:7], 16)};" for c in colors)
    return ("{\\rtf1\\ansi\\ansicpg1252\\deff0\\deflang1033{\\fonttbl" + font_table + "}\n{\\colortbl ;"
            + color_table + f"}}\n{{\\*\\generator {generator};}}\\viewkind4\\uc1\n" + "".join(parts) + "}\n")


def from_rtf(text, doc):
    """Read RTF into the document: fonts, sizes, colours, bold/italic/underline/strike, alignment, paragraphs."""
    doc.clear()
    cursor = QTextCursor(doc)
    fonts, colors = {}, [QColor("black")]
    state = {"f": 0, "fs": 20, "cf": 0, "b": False, "i": False, "ul": False, "strike": False, "align": "ql"}
    stack = []
    skip_depth = None
    pending_font = {"num": None, "name": ""}
    in_fonttbl = in_colortbl = False
    color_acc = {}
    first_block = True
    i, n = 0, len(text)

    def fmt():
        cf = QTextCharFormat()
        cf.setFontFamilies([fonts.get(state["f"], "Arial")])
        cf.setFontPointSize(state["fs"] / 2)
        cf.setFontWeight(QFont.Bold if state["b"] else QFont.Normal)
        cf.setFontItalic(state["i"])
        cf.setFontUnderline(state["ul"])
        cf.setFontStrikeOut(state["strike"])
        cf.setForeground(colors[state["cf"]] if state["cf"] < len(colors) else QColor("black"))
        return cf

    def emit(chars):
        nonlocal first_block
        if skip_depth is not None or in_fonttbl or in_colortbl:
            if in_fonttbl:
                pending_font["name"] += chars
            return
        if first_block:
            bf = QTextBlockFormat()
            bf.setAlignment({"qc": Qt.AlignHCenter, "qr": Qt.AlignRight}.get(state["align"], Qt.AlignLeft))
            cursor.setBlockFormat(bf)
            first_block = False
        cursor.insertText(chars, fmt())

    def new_paragraph():
        bf = QTextBlockFormat()
        bf.setAlignment({"qc": Qt.AlignHCenter, "qr": Qt.AlignRight}.get(state["align"], Qt.AlignLeft))
        cursor.insertBlock(bf, fmt())

    while i < n:
        ch = text[i]
        if ch == "{":
            stack.append((dict(state), skip_depth, in_fonttbl, in_colortbl))
            i += 1
            if text.startswith("\\*", i) and skip_depth is None:
                skip_depth = len(stack)
            continue
        if ch == "}":
            if in_fonttbl and pending_font["num"] is not None:
                fonts[pending_font["num"]] = pending_font["name"].strip().rstrip(";")
                pending_font.update(num=None, name="")
            saved = stack.pop() if stack else (state, None, False, False)
            state.clear()
            state.update(saved[0])
            skip_depth, in_fonttbl, in_colortbl = saved[1], saved[2], saved[3]
            i += 1
            continue
        if ch == "\\":
            m = re.match(r"\\([a-zA-Z]+)(-?\d+)? ?", text[i:])
            if m:
                word, arg = m.group(1), m.group(2)
                i += m.end()
                num = int(arg) if arg is not None else None
                if word in ("fonttbl",):
                    in_fonttbl = True
                elif word == "colortbl":
                    in_colortbl = True
                    colors = []                      # entry 0 is 'auto' (the bare ';')
                elif word in ("pict", "info", "stylesheet", "header", "footer", "object") and skip_depth is None:
                    skip_depth = len(stack)
                elif in_colortbl and word in ("red", "green", "blue"):
                    color_acc[word] = num or 0
                elif in_fonttbl and word == "f":
                    pending_font.update(num=num, name="")
                elif word == "par" or word == "line":
                    if skip_depth is None and not in_fonttbl and not in_colortbl:
                        new_paragraph()
                        first_block = False
                elif word == "pard":
                    state["align"] = "ql"
                elif word in ("qc", "qr", "ql", "qj"):
                    state["align"] = word if word != "qj" else "ql"
                    if skip_depth is None:
                        bf = cursor.blockFormat()
                        bf.setAlignment({"qc": Qt.AlignHCenter, "qr": Qt.AlignRight}.get(state["align"], Qt.AlignLeft))
                        cursor.setBlockFormat(bf)
                elif word in ("b", "i", "strike"):
                    state[word] = num != 0
                elif word == "ul":
                    state["ul"] = num != 0
                elif word == "ulnone":
                    state["ul"] = False
                elif word == "plain":
                    state.update(b=False, i=False, ul=False, strike=False, fs=20)
                elif word == "f" and not in_fonttbl:
                    state["f"] = num or 0
                elif word == "fs":
                    state["fs"] = num or 20
                elif word == "cf":
                    state["cf"] = num or 0
                elif word == "tab":
                    emit("\t")
                elif word == "u" and num is not None:
                    emit(chr(num if num >= 0 else num + 65536))
                    if i < n and text[i] == "?":
                        i += 1
                elif word in ("bullet",):
                    emit("\u2022")
                continue
            if text.startswith("\\'", i):
                emit(bytes([int(text[i + 2:i + 4], 16)]).decode("cp1252", "replace"))
                i += 4
                continue
            if i + 1 < n and text[i + 1] in "\\{}":
                emit(text[i + 1])
                i += 2
                continue
            i += 2
            continue
        if ch == ";" and in_colortbl:
            colors.append(QColor(color_acc.get("red", 0), color_acc.get("green", 0), color_acc.get("blue", 0)))
            color_acc = {}
            i += 1
            continue
        if ch in "\r\n":
            i += 1
            continue
        j = i
        while j < n and text[j] not in "\\{}\r\n" and not (text[j] == ";" and in_colortbl):
            j += 1
        emit(text[i:j])
        i = j
    # the closing \par leaves an empty paragraph behind; drop it
    last = doc.lastBlock()
    if last.length() <= 1 and last.previous().isValid():
        end = QTextCursor(doc)
        end.movePosition(QTextCursor.End)
        end.deletePreviousChar()


# ---- the window -------------------------------------------------------------------------------------------------------
