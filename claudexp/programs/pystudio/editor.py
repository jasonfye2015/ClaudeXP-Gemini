"""The code editor widget: line numbers, auto-indent, bracket pairing, lint markers and completion popup."""
import re

from PySide6.QtCore import QObject, QPoint, QRect, QSize, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QTextBlockUserData, QTextCursor, QTextFormat
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QPlainTextEdit, QTextEdit, QWidget

from .highlight import PythonHighlighter

PAIRS = {"(": ")", "[": "]", "{": "}", '"': '"', "'": "'"}
CLOSERS = set(PAIRS.values())
INDENT = "    "
WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_]*$")


WARNING_HINTS = ("imported but unused", "assigned to but never used", "unable to detect undefined names",
                 "redefinition of unused", "f-string is missing placeholders")


def is_warning(message):
    return any(h in message for h in WARNING_HINTS)


class _Gutter(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.gutter_width(), 0)

    def paintEvent(self, event):
        self.editor.paint_gutter(event)

    def mousePressEvent(self, event):
        self.gutter.editor.gutter_clicked(event.position().toPoint().y(), event.position().toPoint().x())


class _Mark(QTextBlockUserData):
    def __init__(self):
        super().__init__()
        self.breakpoint = False


class _Completer(QObject):
    """Runs jedi off the UI thread. Only the newest request's answer is delivered."""
    done = Signal(int, list, str)

    def __init__(self):
        super().__init__()
        self.env = None
        self.python = None

    def request(self, serial, code, line, col, path):
        thread = _JediThread(self, serial, code, line, col, path)
        thread.finished.connect(thread.deleteLater)
        self._threads = getattr(self, "_threads", set())
        self._threads.add(thread)
        thread.finished.connect(lambda t=thread: self._threads.discard(t))
        thread.start()


class _JediThread(QThread):
    def __init__(self, owner, serial, code, line, col, path):
        super().__init__()
        self.owner, self.serial, self.code, self.line, self.col, self.path = owner, serial, code, line, col, path

    def run(self):
        items, signature = [], ""
        try:
            import jedi
            owner = self.owner
            if owner.env is None and owner.python:
                owner.env = jedi.create_environment(str(owner.python), safe=False)
            script = jedi.Script(self.code, path=self.path or None, environment=owner.env)
            for c in script.complete(self.line, self.col)[:200]:
                items.append((c.name, c.type, c.name_with_symbols))
            sigs = script.get_signatures(self.line, self.col)
            if sigs:
                signature = sigs[0].to_string()
        except Exception:
            pass
        self.owner.done.emit(self.serial, items, signature)


class CodeEditor(QPlainTextEdit):
    signature_changed = Signal(str)
    cursor_info = Signal(int, int)
    breakpoints_changed = Signal(int, bool)
    ghost_wanted = Signal()

    def __init__(self, python=None):
        super().__init__()
        self.setProperty("nospell", True)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setTabStopDistance(0)
        self.set_font_size(10)
        self.setStyleSheet("QPlainTextEdit { background: white; color: black; border: 1px solid #7F9DB9; }")
        self.highlighter = PythonHighlighter(self.document())
        self.path = None
        self.menu_hook = None              # called with (menu, editor, click position) to add menu items
        self.problems = []                 # [(line, message)]
        self.debug_line = None
        self.ghost, self.ghost_at = "", -1
        self.ghost_enabled = False
        self._ghost_timer = QTimer(self, singleShot=True, interval=800)
        self._ghost_timer.timeout.connect(self._ghost_due)
        self.textChanged.connect(self._text_edited)
        self.gutter = _Gutter(self)
        self.blockCountChanged.connect(self._update_gutter_width)
        self.updateRequest.connect(self._scroll_gutter)
        self.cursorPositionChanged.connect(self._cursor_moved)
        self._update_gutter_width()

        self.popup = QListWidget(self)
        self.popup.setWindowFlags(Qt.ToolTip)
        self.popup.setFocusPolicy(Qt.NoFocus)
        self.popup.setStyleSheet("QListWidget { background: #FFFFE1; border: 1px solid black; font-family: Tahoma; "
                                 "font-size: 11px; } QListWidget::item:selected { background: #316AC5; color: white; }")
        self.popup.itemClicked.connect(lambda _i: self._accept_completion())
        self.completer = _Completer()
        self.completer.python = python
        self.completer.done.connect(self._completions_ready)
        self._serial = 0
        self._want_popup = False
        self._timer = QTimer(self, singleShot=True, interval=350)
        self._timer.timeout.connect(self._ask_completions)
        self._highlight_line()

    # ---- fonts, gutter ---------------------------------------------------------------------------
    def set_font_size(self, points):
        self.font_points = max(7, min(28, points))
        font = QFont("Consolas", self.font_points)
        font.setStyleHint(QFont.Monospace)
        self.setFont(font)
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * 4)
        if hasattr(self, "gutter"):
            self._update_gutter_width()

    def gutter_width(self):
        return 28 + self.fontMetrics().horizontalAdvance("9") * max(3, len(str(self.blockCount())))

    def build_menu(self, pos):
        menu = self.createStandardContextMenu()
        if self.menu_hook is not None:
            menu.addSeparator()
            self.menu_hook(menu, self, pos)
        return menu

    def contextMenuEvent(self, event):
        self.build_menu(event.pos()).exec(event.globalPos())

    def _update_gutter_width(self, *_):
        self.setViewportMargins(self.gutter_width(), 0, 0, 0)

    def _scroll_gutter(self, rect, dy):
        if dy:
            self.gutter.scroll(0, dy)
        else:
            self.gutter.update(0, rect.y(), self.gutter.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_gutter_width()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.gutter.setGeometry(QRect(cr.left(), cr.top(), self.gutter_width(), cr.height()))

    def paint_gutter(self, event):
        painter = QPainter(self.gutter)
        painter.fillRect(event.rect(), QColor("#ECE9D8"))
        painter.setPen(QColor("#808080"))
        errors = {line for line, m in self.problems if not is_warning(m)}
        warnings = {line for line, m in self.problems if is_warning(m)} - errors
        block = self.firstVisibleBlock()
        number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())
        current = self.textCursor().blockNumber()
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                data = block.userData()
                if data is not None and data.breakpoint:
                    painter.setBrush(QColor("#C00000"))
                    painter.setPen(QColor("#600000"))
                    painter.drawEllipse(3, top + (bottom - top) // 2 - 6, 12, 12)
                if number + 1 == self.debug_line:
                    painter.setBrush(QColor("#E8D000"))
                    painter.setPen(QColor("#806000"))
                    mid = top + (bottom - top) // 2
                    painter.drawPolygon([QPoint(3, mid - 5), QPoint(10, mid - 5), QPoint(10, mid - 8),
                                         QPoint(16, mid), QPoint(10, mid + 8), QPoint(10, mid + 5), QPoint(3, mid + 5)])
                if number + 1 in errors or number + 1 in warnings:
                    painter.setBrush(QColor("#D02020") if number + 1 in errors else QColor("#E0A000"))
                    painter.setPen(Qt.NoPen)
                    painter.drawEllipse(18, top + (bottom - top) // 2 - 3, 6, 6)
                painter.setPen(QColor("#000000") if number == current else QColor("#808080"))
                painter.drawText(0, top, self.gutter.width() - 6, self.fontMetrics().height(),
                                 Qt.AlignRight, str(number + 1))
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            number += 1

    def gutter_clicked(self, y, x=0):
        block = self.cursorForPosition(QPoint(0, y)).block()
        if x < 16:
            self.toggle_breakpoint(block.blockNumber() + 1)
        else:
            self.setTextCursor(QTextCursor(block))

    # ---- breakpoints and the debugger's current line ----------------------------------------------------
    def breakpoints(self):
        found, block = [], self.document().firstBlock()
        while block.isValid():
            data = block.userData()
            if data is not None and data.breakpoint:
                found.append(block.blockNumber() + 1)
            block = block.next()
        return found

    def toggle_breakpoint(self, number=None):
        block = self.document().findBlockByNumber((number or self.textCursor().blockNumber() + 1) - 1)
        if not block.isValid():
            return None
        data = block.userData() or _Mark()
        data.breakpoint = not data.breakpoint
        block.setUserData(data)
        self.gutter.update()
        self.breakpoints_changed.emit(block.blockNumber() + 1, data.breakpoint)
        return data.breakpoint

    def set_debug_line(self, number):
        self.debug_line = number
        if number:
            self.goto_line(number)
            self.setFocus(Qt.OtherFocusReason)
        self._highlight_line()
        self.gutter.update()

    # ---- ghost text (AI autocomplete) --------------------------------------------------------------------
    def _text_edited(self):
        self.clear_ghost()
        if self.ghost_enabled and self.hasFocus():
            self._ghost_timer.start()

    def _ghost_due(self):
        cursor = self.textCursor()
        rest = cursor.block().text()[cursor.positionInBlock():]
        if self.ghost_enabled and not cursor.hasSelection() and not self.popup.isVisible() and not rest.strip():
            self.ghost_wanted.emit()

    def show_ghost(self, text, position):
        if text and position == self.textCursor().position() and not self.popup.isVisible():
            self.ghost, self.ghost_at = text, position
            self.viewport().update()

    def clear_ghost(self):
        if self.ghost:
            self.ghost = ""
            self.viewport().update()

    def accept_ghost(self):
        text, self.ghost = self.ghost, ""
        self.textCursor().insertText(text)
        self.viewport().update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.ghost or self.textCursor().position() != self.ghost_at:
            return
        painter = QPainter(self.viewport())
        painter.setFont(self.font())
        painter.setPen(QColor("#A0A0A0"))
        rect = self.cursorRect()
        metrics = self.fontMetrics()
        for i, line in enumerate(self.ghost.split("\n")[:6]):
            x = rect.left() if i == 0 else self.contentOffset().x() + self.document().documentMargin()
            painter.drawText(int(x), rect.top() + i * metrics.lineSpacing() + metrics.ascent(), line)

    def completer_popup_open(self):
        return self.popup.isVisible()

    def text_around_cursor(self, before=3000, after=1000):
        text, pos = self.toPlainText(), self.textCursor().position()
        return text[max(0, pos - before):pos], text[pos:pos + after], pos

    # ---- highlighting current line and lint markers -----------------------------------------------------
    def _cursor_moved(self):
        self._highlight_line()
        self.gutter.update()
        c = self.textCursor()
        self.cursor_info.emit(c.blockNumber() + 1, c.positionInBlock() + 1)

    def set_problems(self, problems):
        self.problems = problems
        self._highlight_line()
        self.gutter.update()

    def _highlight_line(self):
        extra = []
        line = QTextEdit.ExtraSelection()
        line.format.setBackground(QColor("#FFFFE8"))
        line.format.setProperty(QTextFormat.FullWidthSelection, True)
        line.cursor = self.textCursor()
        line.cursor.clearSelection()
        extra.append(line)
        if self.debug_line:
            block = self.document().findBlockByNumber(self.debug_line - 1)
            if block.isValid():
                now = QTextEdit.ExtraSelection()
                now.format.setBackground(QColor("#FFF29A"))
                now.format.setProperty(QTextFormat.FullWidthSelection, True)
                now.cursor = QTextCursor(block)
                extra.append(now)
        for number, message in self.problems:
            block = self.document().findBlockByNumber(number - 1)
            if not block.isValid():
                continue
            sel = QTextEdit.ExtraSelection()
            cur = QTextCursor(block)
            cur.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
            sel.cursor = cur
            sel.format.setUnderlineStyle(sel.format.UnderlineStyle.WaveUnderline)
            sel.format.setUnderlineColor(QColor("#E0A000") if is_warning(message) else QColor("#D02020"))
            extra.append(sel)
        self.setExtraSelections(extra)

    def goto_line(self, number):
        block = self.document().findBlockByNumber(max(0, number - 1))
        if block.isValid():
            self.setTextCursor(QTextCursor(block))
            self.centerCursor()
            self.setFocus()

    # ---- typing helpers ------------------------------------------------------------------------------
    def keyPressEvent(self, event):
        key, mods, text = event.key(), event.modifiers(), event.text()
        if self.ghost:
            if key == Qt.Key_Tab and not mods and self.textCursor().position() == self.ghost_at:
                self.accept_ghost()
                return
            self.clear_ghost()
        if key == Qt.Key_B and mods & Qt.ControlModifier:
            self.toggle_breakpoint()
            return
            if key in (Qt.Key_Down, Qt.Key_Up):
                row = self.popup.currentRow() + (1 if key == Qt.Key_Down else -1)
                self.popup.setCurrentRow(max(0, min(self.popup.count() - 1, row)))
                return
            if key in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Tab):
                self._accept_completion()
                return
            if key == Qt.Key_Escape:
                self.popup.hide()
                return
            if key not in (Qt.Key_Backspace, Qt.Key_Shift) and not (text and (text.isalnum() or text == "_")):
                self.popup.hide()
        if key == Qt.Key_Space and mods & Qt.ControlModifier:
            self._want_popup = True
            self._ask_completions()
            return
        cursor = self.textCursor()
        if key in (Qt.Key_Return, Qt.Key_Enter) and not mods & Qt.ControlModifier:
            self._newline()
            return
        if key == Qt.Key_Tab and not mods:
            if cursor.hasSelection():
                self.indent_selection(True)
            else:
                col = cursor.positionInBlock()
                cursor.insertText(" " * (4 - col % 4))
            return
        if key == Qt.Key_Backtab:
            self.indent_selection(False)
            return
        if key == Qt.Key_Backspace and not cursor.hasSelection():
            before = cursor.block().text()[:cursor.positionInBlock()]
            if before and not before.strip() and len(before) % 4 == 0:
                cursor.movePosition(QTextCursor.Left, QTextCursor.KeepAnchor, 4)
                cursor.removeSelectedText()
                return
            after = cursor.block().text()[cursor.positionInBlock():cursor.positionInBlock() + 1]
            if before and before[-1] in PAIRS and after == PAIRS[before[-1]]:
                cursor.deleteChar()
        if text and text in CLOSERS and not cursor.hasSelection():
            after = cursor.block().text()[cursor.positionInBlock():cursor.positionInBlock() + 1]
            if after == text:
                cursor.movePosition(QTextCursor.Right)
                self.setTextCursor(cursor)
                return
        if text in PAIRS and not mods & Qt.ControlModifier:
            if cursor.hasSelection():
                chosen = cursor.selectedText()
                cursor.insertText(text + chosen + PAIRS[text])
                return
            before = cursor.block().text()[:cursor.positionInBlock()]
            after = cursor.block().text()[cursor.positionInBlock():cursor.positionInBlock() + 1]
            quote = text in "\"'"
            if quote and (before[-1:].isalnum() or before[-1:] == "_" or before.endswith(text * 2)):
                pass
            elif not after or after.isspace() or after in CLOSERS:
                cursor.insertText(text + PAIRS[text])
                cursor.movePosition(QTextCursor.Left)
                self.setTextCursor(cursor)
                self._schedule_popup(text)
                return
        super().keyPressEvent(event)
        self._schedule_popup(text)

    def _schedule_popup(self, text):
        if text == "." or (text and (text.isalnum() or text == "_") and self.popup.isVisible()):
            self._want_popup = True
            self._timer.start()
        elif text == "(" or text == ",":
            self._want_popup = False
            self._timer.start()
        elif text == ")":
            self.signature_changed.emit("")

    def _newline(self):
        cursor = self.textCursor()
        line = cursor.block().text()
        before = line[:cursor.positionInBlock()]
        indent = re.match(r"[ \t]*", line).group(0)
        stripped = before.rstrip()
        extra = INDENT if stripped.endswith(":") else ""
        after = line[cursor.positionInBlock():]
        if stripped and stripped.split()[0] in ("return", "pass", "break", "continue", "raise") and not extra:
            indent = indent[:-4] if len(indent) >= 4 else ""
        cursor.beginEditBlock()
        cursor.insertText("\n" + indent + extra)
        if after[:1] in CLOSERS and before[-1:] in PAIRS and extra:
            pos = cursor.position()
            cursor.insertText("\n" + indent)
            cursor.setPosition(pos)
        cursor.endEditBlock()
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def _selected_blocks(self):
        cursor = self.textCursor()
        start, end = cursor.selectionStart(), cursor.selectionEnd()
        doc = self.document()
        first = doc.findBlock(start)
        last = doc.findBlock(end)
        if end > start and last.position() == end:
            last = last.previous()
        blocks = []
        block = first
        while block.isValid():
            blocks.append(block)
            if block == last:
                break
            block = block.next()
        return blocks

    def indent_selection(self, forward):
        cursor = self.textCursor()
        cursor.beginEditBlock()
        for block in self._selected_blocks():
            c = QTextCursor(block)
            if forward:
                c.insertText(INDENT)
            else:
                text = block.text()
                n = min(4, len(text) - len(text.lstrip(" ")))
                if n:
                    c.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, n)
                    c.removeSelectedText()
        cursor.endEditBlock()

    def toggle_comment(self):
        blocks = [b for b in self._selected_blocks()]
        lines = [b.text() for b in blocks if b.text().strip()]
        uncomment = bool(lines) and all(t.lstrip().startswith("#") for t in lines)
        cursor = self.textCursor()
        cursor.beginEditBlock()
        for block in blocks:
            text = block.text()
            if not text.strip():
                continue
            c = QTextCursor(block)
            lead = len(text) - len(text.lstrip())
            c.setPosition(block.position() + lead)
            if uncomment:
                n = 2 if text.lstrip().startswith("# ") else 1
                c.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, n)
                c.removeSelectedText()
            else:
                c.insertText("# ")
        cursor.endEditBlock()

    # ---- completion --------------------------------------------------------------------------------
    def _ask_completions(self):
        self._serial += 1
        cursor = self.textCursor()
        self.completer.request(self._serial, self.toPlainText(), cursor.blockNumber() + 1,
                               cursor.positionInBlock(), self.path)

    def _completions_ready(self, serial, items, signature):
        if serial != self._serial:
            return
        self.signature_changed.emit(signature)
        if not self._want_popup or not items or not self.hasFocus():
            if not items:
                self.popup.hide()
            return
        self.popup.clear()
        for name, kind, full in items:
            item = QListWidgetItem(f"{name}    {kind}")
            item.setData(Qt.UserRole, name)
            self.popup.addItem(item)
        self.popup.setCurrentRow(0)
        rect = self.cursorRect()
        self.popup.setFixedSize(280, min(180, 18 * len(items) + 6))
        self.popup.move(self.viewport().mapToGlobal(rect.bottomLeft()))
        self.popup.show()

    def _accept_completion(self):
        item = self.popup.currentItem()
        self.popup.hide()
        if item is None:
            return
        cursor = self.textCursor()
        word = WORD.search(cursor.block().text()[:cursor.positionInBlock()])
        if word:
            cursor.movePosition(QTextCursor.Left, QTextCursor.KeepAnchor, len(word.group(0)))
        cursor.insertText(item.data(Qt.UserRole))
        self.setTextCursor(cursor)

    def focusOutEvent(self, event):
        self.popup.hide()
        super().focusOutEvent(event)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            self.set_font_size(self.font_points + (1 if event.angleDelta().y() > 0 else -1))
            return
        super().wheelEvent(event)
