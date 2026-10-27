"""The QBasic code editor: line numbers, breakpoints, the debugger's arrow, problems, syntax colours (three themes, the
blue QBasic one among them), auto-indent, keywords capitalised as you leave a line (as QBasic's own editor did),
completion, comment toggling, moving and duplicating lines, and the word under the cursor marked everywhere."""
import re

from PySide6.QtCore import QPoint, QRect, QSize, Qt, QTimer, Signal
from PySide6.QtGui import (QColor, QFont, QPainter, QSyntaxHighlighter, QTextCharFormat, QTextCursor, QTextFormat)
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QPlainTextEdit, QTextEdit, QWidget

from .interp import BUILTINS, KEYWORDS

FUNCTIONS = {name for name in BUILTINS if not name.startswith("_")}
WORDS = sorted(KEYWORDS | FUNCTIONS | {"TAB", "SPC"})
INDENT = "    "
OPENS = re.compile(r"^\s*(?:\d+\s+)?(?:(?:FOR|WHILE|SUB|FUNCTION|TYPE|SELECT\s+CASE|DO)\b|"
                   r"(?:IF|ELSEIF)\b.*\bTHEN\s*(?:'.*)?$|ELSE\s*(?:'.*)?$|CASE\b)", re.I)
CLOSES = re.compile(r"^\s*(?:END\s+(?:IF|SUB|FUNCTION|SELECT|TYPE)|NEXT|WEND|LOOP|ELSE|ELSEIF|CASE)\b", re.I)
TOKEN = re.compile(r'"[^"]*"?|\'.*$|\bREM\b.*$|[A-Za-z][A-Za-z0-9_.]*[$%&!#]?|&H[0-9A-Fa-f]+|\d+\.?\d*(?:[ED][+-]?\d+)?'
                   r'[%&!#]?|\.\d+', re.I)

THEMES = {
    "QBasic Blue": {"bg": "#0000AA", "fg": "#AAAAAA", "kw": "#FFFFFF", "fn": "#55FFFF", "str": "#FFFF55",
                    "num": "#55FF55", "comment": "#A0A0A0", "label": "#FF55FF", "line": "#0000D0",
                    "gutter": "#00007A", "gutter_fg": "#8080C0", "select": "#AAAAAA", "select_fg": "#0000AA",
                    "word": "#2A2AD0", "debug": "#AA5500", "error": "#AA0000", "caret": "#FFFFFF"},
    "Light": {"bg": "#FFFFFF", "fg": "#1E1E1E", "kw": "#0000C0", "fn": "#7A3E9D", "str": "#A31515",
              "num": "#098658", "comment": "#008000", "label": "#AF00DB", "line": "#F3F6FB", "gutter": "#F0F0F0",
              "gutter_fg": "#8A8A8A", "select": "#ADD6FF", "select_fg": "#000000", "word": "#E3E8F5",
              "debug": "#FFF2A8", "error": "#FFD7D7", "caret": "#000000"},
    "Dark": {"bg": "#1E1E1E", "fg": "#D4D4D4", "kw": "#569CD6", "fn": "#DCDCAA", "str": "#CE9178", "num": "#B5CEA8",
             "comment": "#6A9955", "label": "#C586C0", "line": "#2A2D2E", "gutter": "#1E1E1E", "gutter_fg": "#858585",
             "select": "#264F78", "select_fg": "#FFFFFF", "word": "#343A40", "debug": "#4B4515", "error": "#5A1D1D",
             "caret": "#FFFFFF"},
}


class Highlighter(QSyntaxHighlighter):
    def __init__(self, doc, theme):
        super().__init__(doc)
        self.set_theme(theme)

    def set_theme(self, theme):
        def fmt(color, bold=False, italic=False):
            f = QTextCharFormat()
            f.setForeground(QColor(color))
            if bold:
                f.setFontWeight(QFont.Bold)
            f.setFontItalic(italic)
            return f
        t = THEMES[theme]
        self.formats = {"kw": fmt(t["kw"], bold=theme != "QBasic Blue"), "fn": fmt(t["fn"]), "str": fmt(t["str"]),
                        "num": fmt(t["num"]), "comment": fmt(t["comment"], italic=True), "label": fmt(t["label"])}
        self.rehighlight()

    def highlightBlock(self, text):
        m = re.match(r"\s*([A-Za-z][A-Za-z0-9_]*:|\d+\b)", text)
        if m and (m.group(1).endswith(":") or m.group(1).isdigit()):
            self.setFormat(m.start(1), len(m.group(1)), self.formats["label"])
        for m in TOKEN.finditer(text):
            tok = m.group()
            up = tok.upper()
            if tok.startswith('"'):
                kind = "str"
            elif tok.startswith("'") or up.startswith("REM"):
                kind = "comment"
            elif tok[0].isdigit() or tok.startswith(".") or up.startswith("&H"):
                kind = "num"
            elif up in KEYWORDS:
                kind = "kw"
            elif up in FUNCTIONS or up in ("TAB", "SPC"):
                kind = "fn"
            else:
                continue
            self.setFormat(m.start(), len(tok), self.formats[kind])


def capitalize_line(text):
    """Keywords and built-in functions in capitals, outside strings and comments (QBasic's editor did this)."""
    out, last = [], 0
    for m in TOKEN.finditer(text):
        tok = m.group()
        up = tok.upper()
        if tok.startswith('"') or tok.startswith("'"):
            continue
        if up.startswith("REM") and (len(up) == 3 or not up[3].isalnum()):
            out.append(text[last:m.start()] + "REM" + tok[3:])
            last = m.end()
            break
        if up in KEYWORDS or up in FUNCTIONS or up in ("TAB", "SPC"):
            out.append(text[last:m.start()] + up)
            last = m.end()
    out.append(text[last:])
    return "".join(out)


def format_source(source):
    """Format Document: keywords in capitals and the blocks indented."""
    lines = source.replace("\r\n", "\n").split("\n")
    out, depth = [], 0
    for line in lines:
        body = capitalize_line(line.strip())
        if not body:
            out.append("")
            continue
        if CLOSES.match(body):
            depth = max(0, depth - 1)
        out.append(INDENT * depth + body)
        if OPENS.match(body) and not re.match(r"^\s*(?:IF|ELSEIF)\b.*\bTHEN\s+[^'\s]", body, re.I):
            single_if = re.match(r"^\s*IF\b.*\bTHEN\s*\S", body, re.I) and not re.search(r"\bTHEN\s*('.*)?$", body,
                                                                                          re.I)
            if not single_if:
                depth += 1
        if re.match(r"^\s*(?:FOR\b.*\bNEXT\b|DO\b.*\bLOOP\b|WHILE\b.*\bWEND\b)", body, re.I):
            depth = max(0, depth - 1)                          # (a loop on one line)
    return "\n".join(out)


class _Gutter(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        self.setCursor(Qt.PointingHandCursor)

    def sizeHint(self):
        return QSize(self.editor.gutter_width(), 0)

    def paintEvent(self, event):
        self.editor.paint_gutter(event)

    def mousePressEvent(self, event):
        self.editor.gutter_clicked(event.position().toPoint().y())


class CodeEditor(QPlainTextEdit):
    breakpoints_changed = Signal()
    cursor_info = Signal(int, int)
    help_wanted = Signal(str)

    def __init__(self, theme="QBasic Blue", font_points=11):
        super().__init__()
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.path = None
        self.title = "Untitled.bas"
        self.breakpoints = set()
        self.problems = {}                     # line -> message
        self.debug_line = None
        self.theme = theme
        self.words = set()                     # the program's own names, for completion
        self.gutter = _Gutter(self)
        self.highlighter = Highlighter(self.document(), theme)
        self.blockCountChanged.connect(self._update_gutter_width)
        self.updateRequest.connect(self._scroll_gutter)
        self.cursorPositionChanged.connect(self._cursor_moved)
        self._last_block = 0
        self.popup = QListWidget(self)
        self.popup.setWindowFlags(Qt.ToolTip)
        self.popup.setFocusPolicy(Qt.NoFocus)
        self.popup.itemClicked.connect(lambda _i: self._accept_completion())
        self.popup.hide()
        self._complete_timer = QTimer(self, singleShot=True, interval=250)
        self._complete_timer.timeout.connect(self._show_completions)
        self.set_font_size(font_points)
        self.apply_theme(theme)
        self._update_gutter_width()

    # ---- look ----
    def set_font_size(self, points):
        self.font_points = max(7, min(28, points))
        font = QFont("Consolas", self.font_points)
        font.setStyleHint(QFont.Monospace)
        self.setFont(font)
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * 4)
        self._update_gutter_width()

    def apply_theme(self, theme):
        self.theme = theme
        t = THEMES[theme]
        self.setStyleSheet(f"QPlainTextEdit {{ background: {t['bg']}; color: {t['fg']}; border: none; "
                           f"selection-background-color: {t['select']}; selection-color: {t['select_fg']}; }}")
        self.popup.setStyleSheet(f"QListWidget {{ background: {t['gutter']}; color: {t['fg']}; border: 1px solid "
                                 f"{t['gutter_fg']}; font-family: Consolas; font-size: 11px; }} "
                                 f"QListWidget::item:selected {{ background: {t['select']}; color: {t['select_fg']}; }}")
        self.highlighter.set_theme(theme)
        self._decorate()
        self.gutter.update()

    def gutter_width(self):
        digits = len(str(max(1, self.blockCount())))
        return 22 + self.fontMetrics().horizontalAdvance("9") * max(3, digits)

    def _update_gutter_width(self, *_):
        self.setViewportMargins(self.gutter_width(), 0, 0, 0)

    def _scroll_gutter(self, rect, dy):
        if dy:
            self.gutter.scroll(0, dy)
        else:
            self.gutter.update(0, rect.y(), self.gutter.width(), rect.height())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.gutter.setGeometry(QRect(cr.left(), cr.top(), self.gutter_width(), cr.height()))

    def paint_gutter(self, event):
        t = THEMES[self.theme]
        p = QPainter(self.gutter)
        p.fillRect(event.rect(), QColor(t["gutter"]))
        block = self.firstVisibleBlock()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        h = self.fontMetrics().height()
        w = self.gutter.width()
        current = self.textCursor().blockNumber()
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible():
                line = block.blockNumber() + 1
                if line in self.breakpoints:
                    p.setRenderHint(QPainter.Antialiasing)
                    p.setBrush(QColor("#E51400"))
                    p.setPen(Qt.NoPen)
                    p.drawEllipse(3, top + (h - 11) // 2, 11, 11)
                if line == self.debug_line:
                    p.setBrush(QColor("#FFD700"))
                    p.setPen(QColor("#806000"))
                    y = top + h // 2
                    from PySide6.QtGui import QPolygon
                    p.drawPolygon(QPolygon([QPoint(3, y - 5), QPoint(11, y - 5), QPoint(16, y), QPoint(11, y + 5),
                                            QPoint(3, y + 5)]))
                if line in self.problems:
                    p.setPen(QColor("#FF5555"))
                    p.drawText(0, top, 16, h, Qt.AlignCenter, "!")
                p.setPen(QColor(t["fg"] if block.blockNumber() == current else t["gutter_fg"]))
                p.drawText(0, top, w - 5, h, Qt.AlignRight | Qt.AlignVCenter, str(line))
            block = block.next()
            top += int(self.blockBoundingRect(block).height()) if block.isValid() else h

    def gutter_clicked(self, y):
        cursor = self.cursorForPosition(self.viewport().mapFromParent(self.gutter.mapToParent(QPoint(0, y))))
        self.toggle_breakpoint(cursor.blockNumber() + 1)

    def toggle_breakpoint(self, line=None):
        line = line or self.textCursor().blockNumber() + 1
        if line in self.breakpoints:
            self.breakpoints.discard(line)
        else:
            self.breakpoints.add(line)
        self.gutter.update()
        self.breakpoints_changed.emit()

    def set_debug_line(self, line):
        self.debug_line = line
        if line:
            block = self.document().findBlockByNumber(line - 1)
            c = QTextCursor(block)
            self.setTextCursor(c)
            self.centerCursor()
        self._decorate()
        self.gutter.update()

    def set_problems(self, problems):
        self.problems = problems
        self._decorate()
        self.gutter.update()

    # ---- highlights: current line, the debugger's line, problems, the word under the cursor ----
    def _decorate(self):
        t = THEMES[self.theme]
        sels = []

        def line_sel(line, color):
            s = QTextEdit.ExtraSelection()
            s.format.setBackground(QColor(color))
            s.format.setProperty(QTextFormat.FullWidthSelection, True)
            s.cursor = QTextCursor(self.document().findBlockByNumber(line - 1))
            sels.append(s)
        if not self.isReadOnly():
            line_sel(self.textCursor().blockNumber() + 1, t["line"])
        for line in self.problems:
            line_sel(line, t["error"])
        if self.debug_line:
            line_sel(self.debug_line, t["debug"])
        word = self._word_at_cursor()
        if word and len(word) > 1 and not self.textCursor().hasSelection():
            doc = self.document()
            pattern = re.compile(r"\b" + re.escape(word) + r"\b", re.I)
            text = doc.toPlainText()
            for k, m in enumerate(pattern.finditer(text)):
                if k > 200:
                    break
                s = QTextEdit.ExtraSelection()
                s.format.setBackground(QColor(t["word"]))
                c = QTextCursor(doc)
                c.setPosition(m.start())
                c.setPosition(m.end(), QTextCursor.KeepAnchor)
                s.cursor = c
                sels.append(s)
        self.setExtraSelections(sels)

    def _word_at_cursor(self):
        c = self.textCursor()
        block = c.block().text()
        pos = c.positionInBlock()
        m = None
        for m2 in re.finditer(r"[A-Za-z][A-Za-z0-9_.]*[$%&!#]?", block):
            if m2.start() <= pos <= m2.end():
                m = m2
                break
        if m is None:
            return ""
        before = block[:m.start()]
        if before.count('"') % 2 == 1 or "'" in before:
            return ""
        return m.group()

    def word_under_cursor(self):
        return self._word_at_cursor()

    def _cursor_moved(self):
        c = self.textCursor()
        block = c.blockNumber()
        if block != self._last_block:
            self._capitalize_block(self._last_block)
            self._last_block = block
        self.cursor_info.emit(block + 1, c.positionInBlock() + 1)
        self._decorate()
        self.gutter.update()

    def _capitalize_block(self, number):
        block = self.document().findBlockByNumber(number)
        if not block.isValid():
            return
        text = block.text()
        fixed = capitalize_line(text)
        if fixed != text:
            c = QTextCursor(block)
            c.beginEditBlock()
            c.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
            c.insertText(fixed)
            c.endEditBlock()

    # ---- typing ----
    def keyPressEvent(self, event):
        key, mods = event.key(), event.modifiers()
        if self.popup.isVisible():
            if key in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Tab):
                self._accept_completion()
                return
            if key == Qt.Key_Escape:
                self.popup.hide()
                return
            if key in (Qt.Key_Up, Qt.Key_Down, Qt.Key_PageUp, Qt.Key_PageDown):
                row = self.popup.currentRow() + {Qt.Key_Up: -1, Qt.Key_Down: 1, Qt.Key_PageUp: -8,
                                                 Qt.Key_PageDown: 8}[key]
                self.popup.setCurrentRow(max(0, min(self.popup.count() - 1, row)))
                return
        if key == Qt.Key_F1:
            self.help_wanted.emit(self.word_under_cursor())
            return
        if key in (Qt.Key_Return, Qt.Key_Enter) and not mods & Qt.ShiftModifier:
            self._newline()
            return
        if key == Qt.Key_Tab and not mods:
            if self.textCursor().hasSelection():
                self.indent_selection(1)
            else:
                self.insertPlainText(INDENT)
            return
        if key == Qt.Key_Backtab:
            self.indent_selection(-1)
            return
        if key == Qt.Key_Backspace and not self.textCursor().hasSelection():
            c = self.textCursor()
            before = c.block().text()[:c.positionInBlock()]
            if before and not before.strip() and len(before) % len(INDENT) == 0:
                for _ in range(len(INDENT)):
                    c.deletePreviousChar()
                return
        if mods & Qt.AltModifier and key in (Qt.Key_Up, Qt.Key_Down):
            self.move_lines(-1 if key == Qt.Key_Up else 1)
            return
        if mods & Qt.ControlModifier and key == Qt.Key_Space:
            self._show_completions(force=True)
            return
        super().keyPressEvent(event)
        if event.text() and (event.text().isalnum() or event.text() in "$%&!#_"):
            self._complete_timer.start()
        else:
            self.popup.hide()
        if event.text() and event.text().isalpha():
            self._dedent_closer()

    def _newline(self):
        c = self.textCursor()
        line = c.block().text()
        indent = re.match(r"\s*", line).group()
        stripped = line.strip()
        fixed = capitalize_line(line)
        if fixed != line and not c.hasSelection():
            pos = c.positionInBlock()
            c.movePosition(QTextCursor.StartOfBlock)
            c.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
            c.insertText(fixed)
            c.movePosition(QTextCursor.StartOfBlock)
            c.movePosition(QTextCursor.Right, n=min(pos, len(fixed)))
            self.setTextCursor(c)
        if OPENS.match(stripped) and not re.match(r"^\s*IF\b.*\bTHEN\s*[^\s']", stripped, re.I) \
                and not re.match(r"^\s*(?:FOR\b.*\bNEXT\b|DO\b.*\bLOOP\b|WHILE\b.*\bWEND\b)", stripped, re.I):
            indent += INDENT
        self.popup.hide()
        self.textCursor().insertText("\n" + indent)
        self.ensureCursorVisible()

    def _dedent_closer(self):
        """Typing END IF, NEXT, LOOP, WEND, ELSE, CASE ... at the start of an indented line takes a level off."""
        c = self.textCursor()
        text = c.block().text()
        if c.positionInBlock() != len(text):
            return
        word = text.strip().upper()
        if word not in ("NEXT", "LOOP", "WEND", "ELSE", "CASE", "END"):
            return
        prev = c.block().previous()
        if not prev.isValid():
            return
        prev_indent = len(re.match(r"\s*", prev.text()).group())
        cur_indent = len(text) - len(text.lstrip())
        opened = OPENS.match(prev.text().strip()) is not None
        want = max(0, (prev_indent if opened else prev_indent - len(INDENT)))
        if word == "END":
            return
        if cur_indent > want and cur_indent >= len(INDENT):
            c.movePosition(QTextCursor.StartOfBlock)
            c.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, cur_indent - want)
            c.removeSelectedText()

    def indent_selection(self, way):
        c = self.textCursor()
        start, end = sorted((c.selectionStart(), c.selectionEnd()))
        doc = self.document()
        first = doc.findBlock(start).blockNumber()
        last = doc.findBlock(max(start, end - 1)).blockNumber()
        c.beginEditBlock()
        for n in range(first, last + 1):
            b = doc.findBlockByNumber(n)
            bc = QTextCursor(b)
            if way > 0:
                bc.insertText(INDENT)
            else:
                lead = len(b.text()) - len(b.text().lstrip(" "))
                bc.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, min(len(INDENT), lead))
                bc.removeSelectedText()
        c.endEditBlock()

    def toggle_comment(self):
        c = self.textCursor()
        start, end = sorted((c.selectionStart(), c.selectionEnd()))
        doc = self.document()
        first = doc.findBlock(start).blockNumber()
        last = doc.findBlock(max(start, end - 1 if end > start else end)).blockNumber()
        blocks = [doc.findBlockByNumber(n) for n in range(first, last + 1)]
        all_commented = all(b.text().lstrip().startswith("'") or not b.text().strip() for b in blocks)
        c.beginEditBlock()
        for b in blocks:
            text = b.text()
            if not text.strip():
                continue
            lead = len(text) - len(text.lstrip())
            bc = QTextCursor(b)
            bc.movePosition(QTextCursor.Right, n=lead)
            if all_commented:
                bc.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, 2 if text.lstrip().startswith("' ") else 1)
                bc.removeSelectedText()
            else:
                bc.insertText("' ")
        c.endEditBlock()

    def duplicate_line(self):
        c = self.textCursor()
        text = c.block().text()
        c.movePosition(QTextCursor.EndOfBlock)
        c.insertText("\n" + text)
        self.setTextCursor(c)

    def move_lines(self, way):
        c = self.textCursor()
        doc = self.document()
        start, end = sorted((c.selectionStart(), c.selectionEnd()))
        first = doc.findBlock(start).blockNumber()
        last = doc.findBlock(end).blockNumber()
        if (way < 0 and first == 0) or (way > 0 and last >= doc.blockCount() - 1):
            return
        lines = doc.toPlainText().split("\n")
        chunk = lines[first:last + 1]
        del lines[first:last + 1]
        at = first + way
        lines[at:at] = chunk
        c.beginEditBlock()
        c.select(QTextCursor.Document)
        c.insertText("\n".join(lines))
        c.endEditBlock()
        b0 = doc.findBlockByNumber(at)
        b1 = doc.findBlockByNumber(at + len(chunk) - 1)
        nc = QTextCursor(b0)
        nc.setPosition(b1.position() + len(b1.text()), QTextCursor.KeepAnchor)
        self.setTextCursor(nc)

    def go_to_line(self, line, col=1):
        block = self.document().findBlockByNumber(max(0, line - 1))
        c = QTextCursor(block)
        c.movePosition(QTextCursor.Right, n=max(0, min(col - 1, len(block.text()))))
        self.setTextCursor(c)
        self.centerCursor()
        self.setFocus()

    # ---- completion ----
    def _prefix(self):
        c = self.textCursor()
        before = c.block().text()[:c.positionInBlock()]
        if before.count('"') % 2 == 1 or "'" in before:
            return ""
        m = re.search(r"[A-Za-z][A-Za-z0-9_.]*[$%&!#]?$", before)
        return m.group() if m else ""

    def _show_completions(self, force=False):
        prefix = self._prefix()
        if len(prefix) < (1 if force else 2):
            self.popup.hide()
            return
        up = prefix.upper()
        pool = sorted(set(WORDS) | {w.upper() for w in self.words})
        found = [w for w in pool if w.startswith(up) and w != up][:40]
        if not found:
            self.popup.hide()
            return
        self.popup.clear()
        for w in found:
            item = QListWidgetItem(w)
            item.setData(Qt.UserRole, w)
            self.popup.addItem(item)
        self.popup.setCurrentRow(0)
        rect = self.cursorRect()
        pos = self.viewport().mapToGlobal(rect.bottomLeft())
        width = max(140, self.fontMetrics().horizontalAdvance(max(found, key=len)) + 40)
        self.popup.setGeometry(pos.x(), pos.y() + 2, width, min(200, 18 * len(found) + 6))
        self.popup.show()

    def _accept_completion(self):
        item = self.popup.currentItem()
        self.popup.hide()
        if item is None:
            return
        word = item.data(Qt.UserRole)
        prefix = self._prefix()
        c = self.textCursor()
        c.movePosition(QTextCursor.Left, QTextCursor.KeepAnchor, len(prefix))
        c.insertText(word)

    def focusOutEvent(self, event):
        self.popup.hide()
        self._capitalize_block(self.textCursor().blockNumber())
        super().focusOutEvent(event)
