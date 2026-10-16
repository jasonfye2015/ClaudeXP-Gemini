"""WordPad, like Windows XP's: a toolbar, a format bar (font, size, bold/italic/underline, colour, alignment,
bullets), a ruler, Find/Replace, Insert Date and Time, Print, and Rich Text Format files (.rtf, its default; the
RTF reader/writer here covers what WordPad itself can format) as well as plain .txt."""
import re
from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import (QAction, QColor, QFont, QIcon, QKeySequence, QPainter, QPen, QPixmap, QTextBlockFormat,
                           QTextCharFormat, QTextCursor, QTextDocument, QTextListFormat)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFontComboBox, QGridLayout, QHBoxLayout, QLabel,
                               QLineEdit, QMenu, QMenuBar, QPushButton, QRadioButton, QStyle, QTextEdit, QToolButton,
                               QVBoxLayout, QWidget)

from .. import clock, sound
from ..wm import XPWindow
from .notepad import MENU_STYLE, _read

STYLE = MENU_STYLE + """
QWidget#wordpad { background: #ECE9D8; }
QWidget#bar { background: #ECE9D8; border-bottom: 1px solid #ACA899; }
QToolButton { border: 1px solid transparent; padding: 2px; font-family: Tahoma; font-size: 11px; }
QToolButton:hover { border: 1px solid #ACA899; background: #F4F2E8; }
QToolButton:checked { border: 1px solid #808080; background: #FFFFFF; }
QTextEdit { background: white; border: 1px solid #7F9DB9; }
QLabel#status { border-top: 1px solid #ACA899; padding: 2px 6px; font-family: Tahoma; font-size: 11px; }
"""
SIZES = [8, 9, 10, 11, 12, 14, 16, 18, 20, 22, 24, 26, 28, 36, 48, 72]
COLORS = [("Black", "#000000"), ("Maroon", "#800000"), ("Green", "#008000"), ("Olive", "#808000"),
          ("Navy", "#000080"), ("Purple", "#800080"), ("Teal", "#008080"), ("Gray", "#808080"),
          ("Silver", "#C0C0C0"), ("Red", "#FF0000"), ("Lime", "#00FF00"), ("Yellow", "#FFFF00"),
          ("Blue", "#0000FF"), ("Fuchsia", "#FF00FF"), ("Aqua", "#00FFFF"), ("White", "#FFFFFF")]


def wordpad_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor("#606060"), 1))
    p.setBrush(QColor("white"))
    p.drawRect(QRectF(5.5, 2.5, 19, 26))
    p.setPen(QPen(QColor("#2050C0"), 2))
    for i, w in enumerate((14, 12, 14, 9, 13, 10)):
        p.drawLine(8, 7 + i * 3.5, 8 + w, 7 + i * 3.5)
    p.setPen(QPen(QColor("#804000"), 2.5))
    p.drawLine(27, 8, 17, 26)
    p.setPen(QPen(QColor("#202020"), 2))
    p.drawLine(18, 24, 16, 28)
    p.end()
    return QIcon(pm)


# ---- Rich Text Format --------------------------------------------------------------------------------------------

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

class Ruler(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(18)

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#ECE9D8"))
        p.fillRect(QRectF(10, 3, self.width() - 20, 12), QColor("white"))
        p.setPen(QColor("#404040"))
        f = QFont("Tahoma")
        f.setPixelSize(9)
        p.setFont(f)
        inch = 96
        x0 = 12
        i = 0
        while x0 + i * inch / 8 < self.width() - 12:
            x = x0 + i * inch / 8
            if i % 8 == 0 and i:
                p.drawText(QRectF(x - 6, 3, 12, 12), Qt.AlignCenter, str(i // 8))
            elif i % 4 == 0:
                p.drawLine(int(x), 7, int(x), 11)
            else:
                p.drawLine(int(x), 8, int(x), 9)
            i += 1


class WordPad(QWidget):
    def __init__(self, desktop, path=None, product_name="WordPad", app_icon=None):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.path = None
        self.kind = "rtf"
        self.product_name = product_name
        self.app_icon = app_icon or wordpad_icon()
        self.closing = False
        self.setObjectName("wordpad")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(STYLE)
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        self.menu = QMenuBar()
        self.menu.triggered.connect(lambda _a: sound.play("menu"))
        v.addWidget(self.menu)
        self.edit = QTextEdit()
        self.edit.setAcceptRichText(True)
        self.edit.document().setDocumentMargin(12)
        self.edit.setFontFamily("Arial")
        self.edit.setFontPointSize(10)
        self.toolbar = self._toolbar()
        self.formatbar = self._formatbar()
        self.ruler = Ruler()
        v.addWidget(self.toolbar)
        v.addWidget(self.formatbar)
        v.addWidget(self.ruler)
        v.addWidget(self.edit, 1)
        self.status = QLabel("For Help, press F1")
        self.status.setObjectName("status")
        v.addWidget(self.status)
        self._menus()
        self.edit.currentCharFormatChanged.connect(self._sync_format)
        self.edit.cursorPositionChanged.connect(self._sync_align)
        self.edit.document().modificationChanged.connect(lambda _m: self.update_title())
        if path is not None:
            self.load(Path(path))

    # ---- bars ---------------------------------------------------------------------------------------------------
    def _tool(self, text, slot, tip, icon=None, checkable=False):
        b = QToolButton()
        if icon is not None:
            b.setIcon(icon)
        else:
            b.setText(text)
        b.setToolTip(tip)
        b.setCheckable(checkable)
        b.setAutoRaise(True)
        if checkable:
            b.clicked.connect(slot)
        else:
            b.clicked.connect(lambda _checked=False: slot())
        return b

    def _toolbar(self):
        bar = QWidget()
        bar.setObjectName("bar")
        bar.setAttribute(Qt.WA_StyledBackground, True)
        h = QHBoxLayout(bar)
        h.setContentsMargins(4, 2, 4, 2)
        h.setSpacing(1)
        st = QApplication.style()
        items = [(st.standardIcon(QStyle.SP_FileIcon), lambda: self._maybe_save(self.new), "New"),
                 (st.standardIcon(QStyle.SP_DialogOpenButton), lambda: self._maybe_save(self.open_dialog), "Open"),
                 (st.standardIcon(QStyle.SP_DialogSaveButton), self.save, "Save"), None,
                 (None, self.print_, "Print"), (None, self.find_dialog, "Find"), None,
                 (None, self.edit.cut, "Cut"), (None, self.edit.copy, "Copy"), (None, self.edit.paste, "Paste"),
                 (None, self.edit.undo, "Undo"), None, (None, self.insert_date, "Date/Time")]
        for item in items:
            if item is None:
                h.addSpacing(8)
                continue
            icon, slot, tip = item
            h.addWidget(self._tool(tip, slot, tip, icon))
        h.addStretch()
        return bar

    def _formatbar(self):
        bar = QWidget()
        bar.setObjectName("bar")
        bar.setAttribute(Qt.WA_StyledBackground, True)
        h = QHBoxLayout(bar)
        h.setContentsMargins(4, 2, 4, 2)
        h.setSpacing(2)
        self.font_box = QFontComboBox()
        self.font_box.setCurrentFont(QFont("Arial"))
        self.font_box.setFixedWidth(170)
        self.font_box.currentFontChanged.connect(lambda f: self._merge(family=f.family()))
        self.size_box = QComboBox()
        self.size_box.setEditable(True)
        self.size_box.addItems([str(s) for s in SIZES])
        self.size_box.setCurrentText("10")
        self.size_box.setFixedWidth(50)
        self.size_box.textActivated.connect(lambda t: t.replace(".", "").isdigit() and self._merge(size=float(t)))
        self.script_box = QComboBox()
        self.script_box.addItems(["Western"])
        h.addWidget(self.font_box)
        h.addWidget(self.size_box)
        h.addWidget(self.script_box)
        h.addSpacing(6)
        self.bold = self._tool("B", lambda on: self._merge(bold=on), "Bold", checkable=True)
        self.italic = self._tool("I", lambda on: self._merge(italic=on), "Italic", checkable=True)
        self.underline = self._tool("U", lambda on: self._merge(underline=on), "Underline", checkable=True)
        for b, attr in ((self.bold, "setBold"), (self.italic, "setItalic"), (self.underline, "setUnderline")):
            f = QFont("Times New Roman")
            f.setPixelSize(14)
            getattr(f, attr)(True)
            b.setFont(f)
            b.setFixedWidth(24)
            h.addWidget(b)
        color = QToolButton()
        color.setText("A")
        color.setToolTip("Color")
        color.setPopupMode(QToolButton.InstantPopup)
        menu = QMenu(color)
        for name, hexcode in COLORS:
            pm = QPixmap(12, 12)
            pm.fill(QColor(hexcode))
            menu.addAction(QIcon(pm), name, lambda h_=hexcode: self._merge(color=h_))
        color.setMenu(menu)
        h.addWidget(color)
        h.addSpacing(6)
        self.align_buttons = {}
        for key, label, tip in (("left", "\u2261L", "Align Left"), ("center", "\u2261C", "Center"),
                                ("right", "\u2261R", "Align Right")):
            b = self._tool(label, lambda _c=False, k=key: self.set_align(k), tip, checkable=True)
            self.align_buttons[key] = b
            h.addWidget(b)
        h.addWidget(self._tool("\u2022\u2261", self.toggle_bullets, "Bullets"))
        h.addStretch()
        return bar

    def _menus(self):
        m = self.menu
        f = m.addMenu("&File")
        f.addAction("&New...", lambda: self._maybe_save(self.new), QKeySequence("Ctrl+N"))
        f.addAction("&Open...", lambda: self._maybe_save(self.open_dialog), QKeySequence("Ctrl+O"))
        f.addAction("&Save", self.save, QKeySequence("Ctrl+S"))
        f.addAction("Save &As...", self.save_as)
        f.addSeparator()
        f.addAction("&Print...", self.print_, QKeySequence("Ctrl+P"))
        f.addSeparator()
        f.addAction("E&xit", lambda: self.frame.request_close())
        e = m.addMenu("&Edit")
        e.addAction("&Undo", self.edit.undo, QKeySequence("Ctrl+Z"))
        e.addSeparator()
        e.addAction("Cu&t", self.edit.cut, QKeySequence("Ctrl+X"))
        e.addAction("&Copy", self.edit.copy, QKeySequence("Ctrl+C"))
        e.addAction("&Paste", self.edit.paste, QKeySequence("Ctrl+V"))
        e.addAction("Cle&ar", lambda: self.edit.textCursor().removeSelectedText(), QKeySequence("Del"))
        e.addAction("Select A&ll", self.edit.selectAll, QKeySequence("Ctrl+A"))
        e.addSeparator()
        e.addAction("&Find...", self.find_dialog, QKeySequence("Ctrl+F"))
        e.addAction("Find &Next", self.find_next, QKeySequence("F3"))
        e.addAction("R&eplace...", lambda: self.find_dialog(replace=True), QKeySequence("Ctrl+H"))
        v = m.addMenu("&View")
        for label, widget in (("&Toolbar", self.toolbar), ("&Format Bar", self.formatbar), ("&Ruler", self.ruler)):
            act = QAction(label, self, checkable=True, checked=True)
            act.toggled.connect(widget.setVisible)
            v.addAction(act)
        i = m.addMenu("&Insert")
        i.addAction("&Date and Time...", self.insert_date)
        o = m.addMenu("F&ormat")
        o.addAction("&Font...", self.font_dialog)
        o.addAction("Bullet &Style", self.toggle_bullets)
        o.addAction("&Paragraph...", lambda: self.set_align("left"))
        h = m.addMenu("&Help")
        about = ("Windows WordPad\nVersion 5.1 (Build 2600)" if self.product_name == "WordPad"
                 else f"{self.product_name}\nVersion 1.0")
        h.addAction(f"&About {self.product_name}",
                    lambda: self._message(f"About {self.product_name}", about))

    # ---- formatting ------------------------------------------------------------------------------------------------
    def _merge(self, family=None, size=None, bold=None, italic=None, underline=None, color=None):
        cf = QTextCharFormat()
        if family:
            cf.setFontFamilies([family])
        if size:
            cf.setFontPointSize(size)
        if bold is not None:
            cf.setFontWeight(QFont.Bold if bold else QFont.Normal)
        if italic is not None:
            cf.setFontItalic(italic)
        if underline is not None:
            cf.setFontUnderline(underline)
        if color:
            cf.setForeground(QColor(color))
        cursor = self.edit.textCursor()
        cursor.mergeCharFormat(cf)
        self.edit.mergeCurrentCharFormat(cf)
        self.edit.setFocus()

    def _sync_format(self, cf):
        for widget, value in ((self.bold, cf.fontWeight() >= QFont.Bold), (self.italic, cf.fontItalic()),
                              (self.underline, cf.fontUnderline())):
            widget.blockSignals(True)
            widget.setChecked(value)
            widget.blockSignals(False)
        fam = cf.fontFamilies()[0] if cf.fontFamilies() else None
        if fam:
            self.font_box.blockSignals(True)
            self.font_box.setCurrentFont(QFont(fam))
            self.font_box.blockSignals(False)
        if cf.fontPointSize():
            self.size_box.setCurrentText(f"{cf.fontPointSize():g}")

    def _sync_align(self):
        a = self.edit.alignment() & Qt.AlignHorizontal_Mask
        key = "center" if a & Qt.AlignHCenter else "right" if a & Qt.AlignRight else "left"
        for k, b in self.align_buttons.items():
            b.setChecked(k == key)

    def set_align(self, key):
        self.edit.setAlignment({"left": Qt.AlignLeft, "center": Qt.AlignHCenter, "right": Qt.AlignRight}[key])
        self._sync_align()

    def toggle_bullets(self):
        cursor = self.edit.textCursor()
        lst = cursor.currentList()
        if lst is not None:
            bf = QTextBlockFormat()
            bf.setIndent(0)
            for _ in range(lst.count()):
                lst.remove(lst.item(0))
            cursor.setBlockFormat(bf)
        else:
            fmt = QTextListFormat()
            fmt.setStyle(QTextListFormat.ListDisc)
            cursor.createList(fmt)

    def insert_date(self):
        now = clock.now()
        self.edit.insertPlainText(f"{now.month}/{now.day}/{now.year} {clock.time_text(now)}")

    def font_dialog(self):
        from .paint import _dialog
        body = QWidget()
        g = QGridLayout(body)
        fam = QFontComboBox()
        fam.setCurrentFont(QFont(self.font_box.currentFont()))
        size = QComboBox()
        size.addItems([str(s) for s in SIZES])
        size.setCurrentText(self.size_box.currentText())
        bold, italic, under, strike = QCheckBox("&Bold"), QCheckBox("&Italic"), QCheckBox("&Underline"), \
            QCheckBox("Stri&keout")
        g.addWidget(QLabel("&Font:"), 0, 0)
        g.addWidget(fam, 0, 1)
        g.addWidget(QLabel("&Size:"), 1, 0)
        g.addWidget(size, 1, 1)
        for i, box in enumerate((bold, italic, under, strike)):
            g.addWidget(box, 2 + i // 2, i % 2)

        def ok():
            cf = QTextCharFormat()
            cf.setFontFamilies([fam.currentFont().family()])
            cf.setFontPointSize(float(size.currentText()))
            cf.setFontWeight(QFont.Bold if bold.isChecked() else QFont.Normal)
            cf.setFontItalic(italic.isChecked())
            cf.setFontUnderline(under.isChecked())
            cf.setFontStrikeOut(strike.isChecked())
            self.edit.textCursor().mergeCharFormat(cf)
            self.edit.mergeCurrentCharFormat(cf)
        _dialog(self.desktop, "Font", body, ok)

    # ---- find -----------------------------------------------------------------------------------------------------------
    def find_dialog(self, replace=False):
        from .paint import _dialog
        body = QWidget()
        g = QGridLayout(body)
        what = QLineEdit(getattr(self, "last_find", ""))
        g.addWidget(QLabel("Fi&nd what:"), 0, 0)
        g.addWidget(what, 0, 1)
        repl = QLineEdit()
        if replace:
            g.addWidget(QLabel("Re&place with:"), 1, 0)
            g.addWidget(repl, 1, 1)
        case = QCheckBox("Match &case")
        g.addWidget(case, 2, 0, 1, 2)

        def go():
            self.last_find, self.last_case = what.text(), case.isChecked()
            if replace:
                doc_text = self.edit.toPlainText()
                count = doc_text.count(what.text()) if case.isChecked() else doc_text.lower().count(what.text().lower())
                cursor = self.edit.textCursor()
                cursor.movePosition(QTextCursor.Start)
                self.edit.setTextCursor(cursor)
                flags = QTextDocument.FindCaseSensitively if case.isChecked() else QTextDocument.FindFlag(0)
                while self.edit.find(what.text(), flags):
                    self.edit.textCursor().insertText(repl.text())
                self.status.setText(f"Replaced {count} occurrence(s).")
            else:
                self.find_next()
        _dialog(self.desktop, "Replace" if replace else "Find", body, go, what)

    def find_next(self):
        text = getattr(self, "last_find", "")
        if not text:
            return self.find_dialog()
        flags = QTextDocument.FindCaseSensitively if getattr(self, "last_case", False) else QTextDocument.FindFlag(0)
        if not self.edit.find(text, flags):
            self._message(self.product_name, f"{self.product_name} has finished searching the document.", "info")

    # ---- files ------------------------------------------------------------------------------------------------------------
    def name(self):
        return self.path.name if self.path else "Document"

    def update_title(self):
        if self.frame is not None:
            self.frame.set_title(f"{self.name()} - {self.product_name}")

    def new(self):
        from .paint import _dialog
        body = QWidget()
        lay = QVBoxLayout(body)
        lay.addWidget(QLabel("New document type:"))
        rtf, txt = QRadioButton("Rich Text Document"), QRadioButton("Text Document")
        rtf.setChecked(True)
        lay.addWidget(rtf)
        lay.addWidget(txt)

        def ok():
            self.edit.clear()
            self.edit.setFontFamily("Arial")
            self.edit.setFontPointSize(10)
            self.path, self.kind = None, "rtf" if rtf.isChecked() else "txt"
            self.edit.document().setModified(False)
            self.update_title()
        _dialog(self.desktop, "New", body, ok)

    def load(self, path):
        path = Path(path)
        try:
            raw = _read(path)
        except OSError:
            return self._message(self.product_name, f"Cannot open {path.name}.", "error")
        if raw.lstrip().startswith("{\\rtf"):
            from_rtf(raw, self.edit.document())
            self.kind = "rtf"
        else:
            self.edit.setPlainText(raw)
            self.kind = "txt"
        self.path = path
        self.edit.document().setModified(False)
        self.update_title()

    def save(self, then=None):
        if self.path is None:
            return self.save_as(then)
        try:
            if self.path.suffix.lower() == ".rtf":
                self.path.write_text(to_rtf(self.edit.document(), f"ClaudeXP {self.product_name}"),
                                     encoding="cp1252", errors="replace")
            else:
                self.path.write_text(self.edit.toPlainText(), encoding="utf-8")
        except OSError as e:
            return self._message(self.product_name, f"Cannot save {self.path.name}.\n{e.strerror}", "error")
        self.edit.document().setModified(False)
        self.update_title()
        if callable(then):
            then()

    def save_as(self, then=None):
        from ..explorer import vfs
        from .notepad import SaveAsDialog
        ext = ".rtf" if self.kind == "rtf" else ".txt"
        name = self.path.name if self.path else "Document" + ext
        folder = self.path.parent if self.path else vfs.my_documents()

        def saved(path):
            if path.suffix.lower() not in (".rtf", ".txt"):
                path = path.with_suffix(ext)
            self.path = path
            self.kind = "rtf" if path.suffix.lower() == ".rtf" else "txt"
            self.save(then)
        SaveAsDialog(self.desktop, name, folder, saved)

    def open_dialog(self):
        from ..explorer import vfs
        from .paint import _dialog
        from PySide6.QtWidgets import QListWidget, QListWidgetItem
        places = [("My Documents", vfs.my_documents()), ("Desktop", vfs.user_home() / "Desktop"),
                  ("Shared Documents", vfs.shared_documents()), ("External Drive (E:)", vfs.local_storage())]
        body = QWidget()
        g = QGridLayout(body)
        g.addWidget(QLabel("Look in:"), 0, 0)
        where = QComboBox()
        for label, folder in places:
            where.addItem(QApplication.style().standardIcon(QStyle.SP_DirIcon), label, str(folder))
        g.addWidget(where, 0, 1)
        files = QListWidget()
        files.setMinimumSize(360, 200)
        g.addWidget(files, 1, 0, 1, 2)

        def fill():
            files.clear()
            folder = Path(where.currentData())
            if folder.is_dir():
                for p in sorted(folder.iterdir(), key=lambda p: p.name.lower()):
                    if p.suffix.lower() in (".rtf", ".txt", ".ini", ".log"):
                        item = QListWidgetItem(QApplication.style().standardIcon(QStyle.SP_FileIcon), p.name)
                        item.setData(Qt.UserRole, str(p))
                        files.addItem(item)
        where.currentIndexChanged.connect(fill)
        fill()

        def accept():
            item = files.currentItem()
            if item is None:
                return False
            self.load(item.data(Qt.UserRole))
        win = _dialog(self.desktop, "Open", body, accept)
        win.icon = self.app_icon
        files.itemDoubleClicked.connect(lambda _i: accept() is not False and self.desktop.close_window(win))

    def print_(self):
        from ..printing import print_document
        print_document(self.desktop, self.name(), self.edit.document().clone())

    def _maybe_save(self, proceed):
        if not self.edit.document().isModified():
            return proceed()

        def answer(button):
            if button == "Yes":
                self.save(proceed)
            elif button == "No":
                proceed()
        self._message(self.product_name, f"Save changes to {self.name()}?", "warning",
                       ("Yes", "No", "Cancel"), answer)

    def closeEvent(self, event):
        if self.closing or not self.edit.document().isModified():
            event.accept()
            return
        event.ignore()

        def really_close():
            self.closing = True
            if self.frame is not None:
                self.desktop.close_window(self.frame)
        self._maybe_save(really_close)

    def _message(self, title, text, icon="info", buttons=("OK",), on_button=None):
        from ..explorer.dialogs import msgbox
        return msgbox(self.desktop, title, text, icon, buttons, on_button)


def open_wordpad(desktop, path=None, product_name="WordPad", app_icon=None):
    icon = app_icon or wordpad_icon()
    body = WordPad(desktop, path, product_name, icon)
    win = XPWindow(desktop, f"{body.name()} - {product_name}", body, icon, (680, 500))
    body.frame = win
    desktop.open_window(win)
    body.edit.setFocus()
    return win
