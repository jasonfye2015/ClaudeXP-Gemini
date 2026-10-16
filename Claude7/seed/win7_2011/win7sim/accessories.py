"""Small, self-contained Windows-style accessory applications."""

from __future__ import annotations

from decimal import Decimal, DecimalException
from pathlib import Path

from PySide6.QtCore import QPoint, QRect, QSize, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QKeySequence,
    QPainter,
    QPen,
    QPixmap,
    QShortcut,
    QTextCharFormat,
)
from PySide6.QtWidgets import (
    QColorDialog,
    QComboBox,
    QFontComboBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .config import STORAGE_ROOT


def _documents_folder() -> Path:
    folder = STORAGE_ROOT / "UserData" / "Documents"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def _pictures_folder() -> Path:
    folder = STORAGE_ROOT / "UserData" / "Pictures"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


class CalculatorApp(QWidget):
    """A four-function desktop calculator with keyboard and button input."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._stored_value: Decimal | None = None
        self._pending_operator: str | None = None
        self._replace_input = True
        self._error = False
        self.display = QLineEdit("0")
        self.display.setObjectName("calculator-display")
        self.display.setAccessibleName("Calculator display")
        self.display.setReadOnly(True)
        self.display.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.display.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.display.setMaxLength(22)
        self.display.setMinimumHeight(48)
        self.display.setStyleSheet("font-size: 22pt; padding: 3px 8px;")

        layout = QVBoxLayout(self)
        layout.addWidget(self.display)
        grid = QGridLayout()
        grid.setSpacing(4)
        layout.addLayout(grid)
        keys = (
            ("CE", "C", "⌫", "÷"),
            ("7", "8", "9", "×"),
            ("4", "5", "6", "−"),
            ("1", "2", "3", "+"),
            ("±", "0", ".", "="),
        )
        self.buttons: dict[str, QPushButton] = {}
        for row, tokens in enumerate(keys):
            for column, token in enumerate(tokens):
                button = QPushButton(token)
                button.setObjectName(
                    "calculator-" + {
                        "⌫": "backspace",
                        "÷": "divide",
                        "×": "multiply",
                        "−": "subtract",
                        "±": "sign",
                    }.get(token, token.casefold())
                )
                button.setMinimumSize(54, 42)
                button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                button.clicked.connect(
                    lambda _checked=False, value=token: self.press(value)
                )
                grid.addWidget(button, row, column)
                self.buttons[token] = button
        self.setMinimumWidth(254)

        shortcuts = {
            **{str(number): str(number) for number in range(10)},
            ".": ".",
            "+": "+",
            "-": "−",
            "*": "×",
            "/": "÷",
            "=": "=",
            "Return": "=",
            "Enter": "=",
            "Backspace": "⌫",
            "Delete": "C",
            "Escape": "C",
            "%": "%",
        }
        for sequence, token in shortcuts.items():
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.activated.connect(lambda value=token: self.press(value))
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    @staticmethod
    def _format(value: Decimal) -> str:
        if value == 0:
            return "0"
        text = format(value.normalize(), "f")
        return text if len(text) <= 20 else format(value, ".12g")

    def _current_value(self) -> Decimal:
        return Decimal(self.display.text())

    def _show_value(self, value: Decimal) -> None:
        self.display.setText(self._format(value))

    def _clear_error(self) -> None:
        if self._error:
            self.display.setText("0")
            self._stored_value = None
            self._pending_operator = None
            self._replace_input = True
            self._error = False

    def _calculate(self, left: Decimal, operator: str, right: Decimal) -> Decimal:
        if operator == "+":
            return left + right
        if operator == "−":
            return left - right
        if operator == "×":
            return left * right
        if operator == "÷":
            if right == 0:
                raise ZeroDivisionError("Divide by zero")
            return left / right
        raise ValueError(f"Unsupported calculator operator: {operator}")

    def _show_error(self, message: str) -> None:
        self.display.setText(message)
        self._stored_value = None
        self._pending_operator = None
        self._replace_input = True
        self._error = True

    def press(self, key: str) -> None:
        self._clear_error()
        if key.isdigit() and len(key) == 1:
            current = "0" if self._replace_input else self.display.text()
            if current == "0":
                current = key
            elif len(current.lstrip("-").replace(".", "")) < 16:
                current += key
            self.display.setText(current)
            self._replace_input = False
            return

        if key == ".":
            current = "0" if self._replace_input else self.display.text()
            if "." not in current:
                self.display.setText(current + ".")
            self._replace_input = False
            return

        if key in ("C", "CE"):
            self.display.setText("0")
            if key == "C":
                self._stored_value = None
                self._pending_operator = None
            self._replace_input = True
            return

        if key == "⌫":
            if not self._replace_input:
                text = self.display.text()
                text = text[:-1] if len(text) > 1 else "0"
                if text in ("", "-"):
                    text = "0"
                self.display.setText(text)
            return

        if key == "±":
            value = self._current_value()
            self._show_value(-value)
            self._replace_input = True
            return

        if key == "%":
            value = self._current_value()
            if self._stored_value is not None and self._pending_operator:
                value = self._stored_value * value / Decimal(100)
            else:
                value /= Decimal(100)
            self._show_value(value)
            self._replace_input = True
            return

        if key in ("+", "−", "×", "÷"):
            value = self._current_value()
            if self._stored_value is not None and self._pending_operator:
                if not self._replace_input:
                    try:
                        value = self._calculate(
                            self._stored_value, self._pending_operator, value
                        )
                    except ZeroDivisionError as exc:
                        self._show_error(str(exc))
                        return
                else:
                    value = self._stored_value
            self._stored_value = value
            self._pending_operator = key
            self._show_value(value)
            self._replace_input = True
            return

        if key == "=" and self._stored_value is not None and self._pending_operator:
            try:
                result = self._calculate(
                    self._stored_value, self._pending_operator, self._current_value()
                )
            except ZeroDivisionError as exc:
                self._show_error(str(exc))
                return
            except DecimalException:
                self._show_error("Error")
                return
            self._show_value(result)
            self._stored_value = None
            self._pending_operator = None
            self._replace_input = True


class PaintCanvas(QWidget):
    """A simple white bitmap canvas with continuous mouse drawing."""

    contentChanged = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.image = QPixmap(QSize(800, 500))
        self.image.fill(Qt.GlobalColor.white)
        self.pen_color = QColor("#202020")
        self.pen_width = 3
        self._last_point: QPoint | None = None
        self._dirty = False
        self.setMinimumSize(self.image.size())
        self.setMouseTracking(False)

    def paintEvent(self, _event) -> None:  # noqa: N802 - Qt event name
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.GlobalColor.white)
        painter.drawPixmap(0, 0, self.image)

    def mousePressEvent(self, event) -> None:  # noqa: N802 - Qt event name
        if event.button() == Qt.MouseButton.LeftButton:
            self._last_point = event.position().toPoint()
            self.draw_segment(self._last_point, self._last_point)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802 - Qt event name
        if (
            self._last_point is not None
            and event.buttons() & Qt.MouseButton.LeftButton
        ):
            point = event.position().toPoint()
            self.draw_segment(self._last_point, point)
            self._last_point = point

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802 - Qt event name
        if event.button() == Qt.MouseButton.LeftButton:
            self._last_point = None

    def draw_segment(self, start: QPoint, end: QPoint) -> None:
        painter = QPainter(self.image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(
            QPen(
                self.pen_color,
                self.pen_width,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            )
        )
        painter.drawLine(start, end)
        painter.end()
        radius = self.pen_width + 2
        self.update(QRect(start, end).normalized().adjusted(-radius, -radius, radius, radius))
        self._dirty = True
        self.contentChanged.emit()

    def clear(self) -> None:
        self.image.fill(Qt.GlobalColor.white)
        self.update()
        self._dirty = True
        self.contentChanged.emit()

    def load(self, path: Path) -> bool:
        image = QPixmap(str(path))
        if image.isNull():
            return False
        self.image = image
        self.setMinimumSize(image.size())
        self.update()
        self._dirty = False
        return True

    def save(self, path: Path) -> bool:
        success = self.image.save(str(path))
        if success:
            self._dirty = False
        return success


class PaintApp(QWidget):
    """A bitmap drawing program that saves and opens standard image files."""

    documentAccessed = Signal(str)
    _FORMATS = "PNG image (*.png);;JPEG image (*.jpg *.jpeg);;BMP image (*.bmp)"

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.current_path: Path | None = None
        root = QVBoxLayout(self)
        toolbar = QHBoxLayout()
        self.new_button = QPushButton("New")
        self.open_button = QPushButton("Open…")
        self.save_button = QPushButton("Save")
        self.color_button = QPushButton("Color…")
        self.width_box = QSpinBox()
        self.width_box.setRange(1, 36)
        self.width_box.setValue(3)
        self.width_box.setPrefix("Brush ")
        for button in (self.new_button, self.open_button, self.save_button):
            toolbar.addWidget(button)
        toolbar.addSpacing(12)
        toolbar.addWidget(self.color_button)
        toolbar.addWidget(self.width_box)
        toolbar.addStretch(1)
        root.addLayout(toolbar)
        self.canvas = PaintCanvas()
        self._update_color_swatch()
        self.scroll = QScrollArea()
        self.scroll.setWidget(self.canvas)
        self.scroll.setWidgetResizable(False)
        root.addWidget(self.scroll, 1)
        self.new_button.clicked.connect(self.new_picture)
        self.open_button.clicked.connect(self._open_dialog)
        self.save_button.clicked.connect(self._save_dialog)
        self.color_button.clicked.connect(self._choose_color)
        self.width_box.valueChanged.connect(self._set_brush_width)
        self.canvas.contentChanged.connect(self._update_title)
        self._update_title()

    def _update_title(self) -> None:
        title = self.current_path.name if self.current_path else "Untitled"
        self.setWindowTitle("Paint — " + title + (" *" if self.canvas._dirty else ""))

    def _confirm_discard(self) -> bool:
        if not self.canvas._dirty:
            return True
        answer = QMessageBox.question(
            self,
            "Paint",
            "Discard unsaved changes?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return answer == QMessageBox.StandardButton.Yes

    def new_picture(self) -> None:
        if not self._confirm_discard():
            return
        self.canvas.image = QPixmap(QSize(800, 500))
        self.canvas.image.fill(Qt.GlobalColor.white)
        self.canvas.setMinimumSize(self.canvas.image.size())
        self.canvas._dirty = False
        self.canvas.update()
        self.current_path = None
        self._update_title()

    def open_picture(self, path: Path) -> bool:
        if not self._confirm_discard():
            return False
        if not self.canvas.load(path):
            QMessageBox.warning(self, "Paint", f"Could not open this image:\n{path}")
            return False
        self.current_path = path
        self._update_title()
        self.documentAccessed.emit(str(path))
        return True

    def save_picture(self, path: Path) -> bool:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            success = self.canvas.save(path)
        except OSError as exc:
            QMessageBox.warning(self, "Paint", f"Could not save this image:\n{exc}")
            return False
        if not success:
            QMessageBox.warning(self, "Paint", f"Could not save this image:\n{path}")
            return False
        self.current_path = path
        self._update_title()
        self.documentAccessed.emit(str(path))
        return True

    def _open_dialog(self) -> None:
        path, _filter = QFileDialog.getOpenFileName(
            self, "Open picture", str(_pictures_folder()), self._FORMATS
        )
        if path:
            self.open_picture(Path(path))

    def _save_dialog(self) -> None:
        initial = self.current_path or (_pictures_folder() / "Untitled.png")
        path, _filter = QFileDialog.getSaveFileName(
            self, "Save picture", str(initial), self._FORMATS
        )
        if path:
            target = Path(path)
            if not target.suffix:
                target = target.with_suffix(".png")
            self.save_picture(target)

    def _choose_color(self) -> None:
        color = QColorDialog.getColor(self.canvas.pen_color, self, "Brush color")
        if color.isValid():
            self.canvas.pen_color = color
            self._update_color_swatch()

    def _set_brush_width(self, width: int) -> None:
        self.canvas.pen_width = width

    def _update_color_swatch(self) -> None:
        color = self.canvas.pen_color.name()
        self.color_button.setStyleSheet(
            f"QPushButton {{ background-color: {color}; color: "
            f"{'#ffffff' if self.canvas.pen_color.lightness() < 128 else '#111111'}; "
            "border: 1px solid #667788; padding: 4px 10px; }"
        )

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt event name
        if self._confirm_discard():
            event.accept()
        else:
            event.ignore()


class WordPadApp(QWidget):
    """A small rich-text editor with HTML, Markdown, and plain-text files."""

    documentAccessed = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.current_path: Path | None = None
        root = QVBoxLayout(self)
        toolbar = QHBoxLayout()
        self.new_button = QPushButton("New")
        self.open_button = QPushButton("Open…")
        self.save_button = QPushButton("Save")
        for button in (self.new_button, self.open_button, self.save_button):
            toolbar.addWidget(button)
        toolbar.addSpacing(8)
        self.font_box = QFontComboBox()
        self.font_box.setMaximumWidth(190)
        self.font_size = QComboBox()
        self.font_size.setEditable(True)
        self.font_size.addItems(["8", "9", "10", "11", "12", "14", "16", "18", "20", "24", "36"])
        self.font_size.setCurrentText("11")
        self.font_size.setMaximumWidth(62)
        toolbar.addWidget(self.font_box)
        toolbar.addWidget(self.font_size)
        self.bold_button = QPushButton("B")
        self.bold_button.setObjectName("wordpad-bold")
        self.bold_button.setCheckable(True)
        self.bold_button.setToolTip("Bold (Ctrl+B)")
        self.italic_button = QPushButton("I")
        self.italic_button.setObjectName("wordpad-italic")
        self.italic_button.setCheckable(True)
        self.italic_button.setToolTip("Italic (Ctrl+I)")
        self.underline_button = QPushButton("U")
        self.underline_button.setObjectName("wordpad-underline")
        self.underline_button.setCheckable(True)
        self.underline_button.setToolTip("Underline (Ctrl+U)")
        for button in (self.bold_button, self.italic_button, self.underline_button):
            toolbar.addWidget(button)
        self.alignment = QComboBox()
        self.alignment.addItems(["Left", "Center", "Right", "Justify"])
        self.alignment.setToolTip("Paragraph alignment")
        toolbar.addWidget(self.alignment)
        toolbar.addStretch(1)
        root.addLayout(toolbar)
        self.editor = QTextEdit()
        self.editor.setAcceptRichText(True)
        self.editor.setFontFamily("Calibri")
        self.editor.setFontPointSize(11)
        self.editor.setPlaceholderText("Start typing…")
        root.addWidget(self.editor, 1)
        self.new_button.clicked.connect(self.new_document)
        self.open_button.clicked.connect(self._open_dialog)
        self.save_button.clicked.connect(self._save_dialog)
        self.font_box.currentFontChanged.connect(self._set_font)
        self.font_size.currentTextChanged.connect(self._set_font_size)
        self.bold_button.toggled.connect(self._set_bold)
        self.italic_button.toggled.connect(self._set_italic)
        self.underline_button.toggled.connect(self._set_underline)
        self.alignment.currentTextChanged.connect(self._set_alignment)
        self.editor.currentCharFormatChanged.connect(self._reflect_format)
        self.editor.document().modificationChanged.connect(self._update_title)
        self._update_title()

    def _update_title(self, _modified: bool | None = None) -> None:
        title = self.current_path.name if self.current_path else "Untitled"
        dirty = self.editor.document().isModified()
        self.setWindowTitle("WordPad — " + title + (" *" if dirty else ""))

    def _merge_format(self, char_format: QTextCharFormat) -> None:
        cursor = self.editor.textCursor()
        cursor.mergeCharFormat(char_format)
        self.editor.mergeCurrentCharFormat(char_format)

    def _set_font(self, font: QFont) -> None:
        char_format = QTextCharFormat()
        char_format.setFontFamily(font.family())
        self._merge_format(char_format)

    def _set_font_size(self, value: str) -> None:
        try:
            size = float(value)
        except ValueError:
            return
        if 1 <= size <= 200:
            char_format = QTextCharFormat()
            char_format.setFontPointSize(size)
            self._merge_format(char_format)

    def _set_bold(self, enabled: bool) -> None:
        char_format = QTextCharFormat()
        char_format.setFontWeight(
            QFont.Weight.Bold if enabled else QFont.Weight.Normal
        )
        self._merge_format(char_format)

    def _set_italic(self, enabled: bool) -> None:
        char_format = QTextCharFormat()
        char_format.setFontItalic(enabled)
        self._merge_format(char_format)

    def _set_underline(self, enabled: bool) -> None:
        char_format = QTextCharFormat()
        char_format.setFontUnderline(enabled)
        self._merge_format(char_format)

    def _set_alignment(self, value: str) -> None:
        alignment = {
            "Left": Qt.AlignmentFlag.AlignLeft,
            "Center": Qt.AlignmentFlag.AlignHCenter,
            "Right": Qt.AlignmentFlag.AlignRight,
            "Justify": Qt.AlignmentFlag.AlignJustify,
        }.get(value, Qt.AlignmentFlag.AlignLeft)
        self.editor.setAlignment(alignment)

    def _reflect_format(self, char_format: QTextCharFormat) -> None:
        controls = (
            (self.bold_button, char_format.fontWeight() >= QFont.Weight.Bold),
            (self.italic_button, char_format.fontItalic()),
            (self.underline_button, char_format.fontUnderline()),
        )
        for button, checked in controls:
            button.blockSignals(True)
            button.setChecked(checked)
            button.blockSignals(False)
        self.font_box.blockSignals(True)
        self.font_box.setCurrentFont(char_format.font())
        self.font_box.blockSignals(False)
        size = char_format.fontPointSize() or 11
        self.font_size.blockSignals(True)
        self.font_size.setCurrentText(str(round(size)))
        self.font_size.blockSignals(False)

    def _confirm_replace(self) -> bool:
        if not self.editor.document().isModified():
            return True
        answer = QMessageBox.question(
            self,
            "WordPad",
            "Discard unsaved changes?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return answer == QMessageBox.StandardButton.Yes

    def new_document(self) -> None:
        if not self._confirm_replace():
            return
        self.editor.clear()
        self.editor.document().setModified(False)
        self.current_path = None
        self._update_title()

    def load_document(self, path: Path) -> bool:
        if not self._confirm_replace():
            return False
        try:
            content = path.read_text(encoding="utf-8")
            suffix = path.suffix.casefold()
            if suffix in (".html", ".htm"):
                self.editor.setHtml(content)
            elif suffix == ".md":
                self.editor.setMarkdown(content)
            else:
                self.editor.setPlainText(content)
        except (OSError, UnicodeError) as exc:
            QMessageBox.warning(self, "WordPad", f"Could not open this document:\n{exc}")
            return False
        self.editor.document().setModified(False)
        self.current_path = path
        self._update_title()
        self.documentAccessed.emit(str(path))
        return True

    def save_document(self, path: Path) -> bool:
        suffix = path.suffix.casefold()
        if not suffix:
            path = path.with_suffix(".html")
            suffix = ".html"
        if suffix not in (".html", ".htm", ".md", ".txt"):
            QMessageBox.warning(
                self,
                "WordPad",
                "Choose an HTML, Markdown, or plain-text filename. "
                "RTF and Word documents are not supported.",
            )
            return False
        content = (
            self.editor.toHtml()
            if suffix in (".html", ".htm")
            else self.editor.toMarkdown()
            if suffix == ".md"
            else self.editor.toPlainText()
        )
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        except OSError as exc:
            QMessageBox.warning(self, "WordPad", f"Could not save this document:\n{exc}")
            return False
        self.current_path = path
        self.editor.document().setModified(False)
        self._update_title()
        self.documentAccessed.emit(str(path))
        return True

    def _open_dialog(self) -> None:
        path, _filter = QFileDialog.getOpenFileName(
            self,
            "Open document",
            str(_documents_folder()),
            "Documents (*.html *.htm *.md *.txt);;All files (*.*)",
        )
        if path:
            self.load_document(Path(path))

    def _save_dialog(self) -> None:
        initial = self.current_path or (_documents_folder() / "Untitled.html")
        path, _filter = QFileDialog.getSaveFileName(
            self,
            "Save document",
            str(initial),
            "Web document (*.html);;Markdown (*.md);;Text document (*.txt)",
        )
        if path:
            self.save_document(Path(path))

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt event name
        if self._confirm_replace():
            event.accept()
        else:
            event.ignore()
