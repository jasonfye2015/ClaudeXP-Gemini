"""Image-backed native widgets shared by the MSN list and chat windows."""

from pathlib import Path

from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtWidgets import QWidget, QLabel, QDialog, QVBoxLayout, QScrollArea, QTextEdit

from .contacts import MSN_ASSETS, SUPPLIED_PROFILES
from .screens import load_profile_icon


class TemplateCanvas(QWidget):
    def __init__(self, filename, parent=None):
        super().__init__(parent)
        self.image = QPixmap(str(MSN_ASSETS / filename))
        if self.image.isNull():
            raise ValueError(f"Missing MSN template: {filename}")
        self.placements = []

    def place(self, widget, x, y, width, height):
        widget.setParent(self)
        self.placements.append((widget, x, y, width, height))
        widget.show()
        self.arrange()

    def arrange(self):
        sx, sy = self.width() / self.image.width(), self.height() / self.image.height()
        for widget, x, y, width, height in self.placements:
            widget.setGeometry(round(x * sx), round(y * sy), round(width * sx), round(height * sy))

    def resizeEvent(self, event):
        self.arrange()
        super().resizeEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.drawPixmap(self.rect(), self.image)


class Avatar(QLabel):
    def __init__(self, path="", parent=None, stretch_to_frame=False):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("background: transparent; border: 0;")
        self.stretch_to_frame = stretch_to_frame
        self.original = QPixmap()
        self.set_image(path)

    def set_image(self, path):
        self.original = path.copy() if isinstance(path, QPixmap) else QPixmap(str(path)) if path else QPixmap()
        if self.original.isNull():
            self.original = QPixmap(str(MSN_ASSETS / "icons/furry001.jpg"))
        self.refresh()

    def refresh(self):
        mode = (
            Qt.AspectRatioMode.IgnoreAspectRatio
            if self.stretch_to_frame else Qt.AspectRatioMode.KeepAspectRatio
        )
        self.setPixmap(self.original.scaled(self.size(), mode, Qt.TransformationMode.SmoothTransformation))

    def resizeEvent(self, event):
        self.refresh()
        super().resizeEvent(event)


class MessageComposer(QTextEdit):
    """Multiline composer compatible with the existing persistence/chat controller."""
    returnPressed = Signal()

    def text(self):
        return self.toPlainText()

    def setText(self, text):
        self.setPlainText(text)

    def insert(self, text):
        self.insertPlainText(text)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and not (
            event.modifiers() & Qt.KeyboardModifier.ShiftModifier
        ):
            self.returnPressed.emit()
            event.accept()
        else:
            super().keyPressEvent(event)


def player_avatar(account):
    profile = account.active_profile
    if not profile:
        return ""
    return load_profile_icon(profile, MSN_ASSETS.parent / "user-selection")


def stash_legacy_ui(app):
    """Keep the proven persistence/context controls, without the old presentation."""
    stash = QWidget(app)
    stash.hide()
    root = app.layout()

    def remove(layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().setParent(stash)
            elif item.layout():
                remove(item.layout())

    remove(root)
    root.setContentsMargins(0, 0, 0, 0)
    root.setSpacing(0)
    app._legacy_stash = stash
    return root


def show_gallery(contact, parent, selected=None):
    dialog = QDialog(parent)
    dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
    dialog.setWindowTitle(f"{contact.online_name} — shared artwork")
    dialog.resize(640, 620)
    root = QVBoxLayout(dialog)
    description = QLabel("Preinstalled character gallery. A saved picture link never loads an external URL.")
    description.setWordWrap(True)
    root.addWidget(description)
    captions = SUPPLIED_PROFILES.get(contact.contact_id, {}).get("captions", "")
    if captions:
        description.setToolTip(captions)
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    content = QWidget()
    layout = QVBoxLayout(content)
    for filename in contact.gallery:
        if selected and Path(filename).name != selected:
            continue
        image = QPixmap(str(MSN_ASSETS / filename))
        label = QLabel()
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setPixmap(image.scaled(QSize(560, 480), Qt.AspectRatioMode.KeepAspectRatio,
                                     Qt.TransformationMode.SmoothTransformation))
        layout.addWidget(label)
        layout.addWidget(QLabel(Path(filename).name))
    if captions:
        note = QLabel(captions)
        note.setWordWrap(True)
        layout.addWidget(note)
    if not contact.gallery:
        layout.addWidget(QLabel("No pictures were supplied for this contact."))
    scroll.setWidget(content)
    root.addWidget(scroll)
    dialog.show()
    return dialog
