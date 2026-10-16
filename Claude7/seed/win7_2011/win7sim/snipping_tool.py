"""Snipping Tool preview and a selection overlay for the simulated desktop."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from . import config


class SnippingToolApp(QWidget):
    captureRequested = Signal(str)
    documentAccessed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.capture_image: QImage | None = None
        self.mode_box = QComboBox()
        self.mode_box.setObjectName("snipping-mode")
        self.mode_box.addItems(("Rectangular Snip", "Full-screen Snip"))
        self.new_button = QPushButton("New")
        self.copy_button = QPushButton("Copy")
        self.save_button = QPushButton("Save Snip…")
        self.copy_button.setEnabled(False)
        self.save_button.setEnabled(False)
        toolbar = QHBoxLayout()
        toolbar.addWidget(self.new_button)
        toolbar.addWidget(self.mode_box)
        toolbar.addStretch(1)
        toolbar.addWidget(self.copy_button)
        toolbar.addWidget(self.save_button)

        self.preview = QLabel("Click New, then select an area of the desktop.")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumSize(420, 280)
        self.preview.setStyleSheet(
            "QLabel { background: #e9eef2; border: 1px solid #8496a5; color: #36495a; }"
        )
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.preview)
        self.status = QLabel("Snips capture only the simulated Windows desktop.")

        layout = QVBoxLayout(self)
        layout.addLayout(toolbar)
        layout.addWidget(self.scroll_area, 1)
        layout.addWidget(self.status)

        self.new_button.clicked.connect(self.request_capture)
        self.copy_button.clicked.connect(self.copy_image)
        self.save_button.clicked.connect(self.save_image)

    def request_capture(self) -> None:
        self.captureRequested.emit(self.mode_box.currentText())

    def set_capture(self, image: QImage) -> None:
        if image.isNull():
            self.status.setText("The selected area was empty. Try another snip.")
            return
        self.capture_image = image.copy()
        self._show_preview()
        self.copy_button.setEnabled(True)
        self.save_button.setEnabled(True)
        self.status.setText(
            f"Captured {image.width()} × {image.height()} pixels."
        )

    def _show_preview(self) -> None:
        if self.capture_image is None:
            return
        pixmap = QPixmap.fromImage(self.capture_image)
        viewport = self.scroll_area.viewport().size()
        if pixmap.width() > viewport.width() or pixmap.height() > viewport.height():
            pixmap = pixmap.scaled(
                viewport,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        self.preview.setPixmap(pixmap)
        self.preview.setFixedSize(pixmap.size())

    def copy_image(self) -> None:
        if self.capture_image is None:
            return
        QApplication.clipboard().setImage(self.capture_image)
        self.status.setText("Snip copied to the clipboard.")

    def save_image(self) -> None:
        if self.capture_image is None:
            return
        pictures = config.STORAGE_ROOT / "UserData" / "Pictures"
        pictures.mkdir(parents=True, exist_ok=True)
        path, _selected_filter = QFileDialog.getSaveFileName(
            self,
            "Save snip",
            str(pictures / "Snip.png"),
            "PNG image (*.png)",
        )
        if not path:
            return
        target = Path(path)
        if target.suffix.casefold() != ".png":
            target = target.with_suffix(".png")
        if not self.capture_image.save(str(target), "PNG"):
            QMessageBox.warning(
                self, "Snipping Tool", f"Could not save the snip to:\n{target}"
            )
            return
        self.documentAccessed.emit(str(target))
        self.status.setText(f"Saved: {target}")


class SnipOverlay(QWidget):
    """Mouse-drag overlay that selects a rectangle within the simulated desktop."""

    finished = Signal(QRect)
    cancelled = Signal()

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self._start: QPoint | None = None
        self._selection = QRect()
        self.setGeometry(parent.rect())
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setStyleSheet("background: transparent;")

    @property
    def selection(self) -> QRect:
        return QRect(self._selection)

    def mousePressEvent(self, event) -> None:  # noqa: N802 - Qt event name
        if event.button() != Qt.MouseButton.LeftButton:
            return
        self._start = event.position().toPoint()
        self._selection = QRect(self._start, self._start)
        self.update()

    def mouseMoveEvent(self, event) -> None:  # noqa: N802 - Qt event name
        if self._start is None:
            return
        self._selection = QRect(self._start, event.position().toPoint()).normalized()
        self.update()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802 - Qt event name
        if event.button() != Qt.MouseButton.LeftButton or self._start is None:
            return
        self._selection = QRect(
            self._start, event.position().toPoint()
        ).normalized()
        self._start = None
        self.hide()
        if self._selection.width() < 4 or self._selection.height() < 4:
            self.cancelled.emit()
        else:
            self.finished.emit(QRect(self._selection))

    def keyPressEvent(self, event) -> None:  # noqa: N802 - Qt event name
        if event.key() == Qt.Key.Key_Escape:
            self._start = None
            self.hide()
            self.cancelled.emit()
            event.accept()
            return
        super().keyPressEvent(event)

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt event name
        painter = QPainter(self)
        selection = self._selection.normalized().intersected(self.rect())
        shade = QColor(0, 0, 0, 110)
        if selection.isEmpty():
            painter.fillRect(self.rect(), shade)
            return
        outside = (
            QRect(0, 0, self.width(), selection.top()),
            QRect(
                0,
                selection.bottom() + 1,
                self.width(),
                self.height() - selection.bottom() - 1,
            ),
            QRect(0, selection.top(), selection.left(), selection.height()),
            QRect(
                selection.right() + 1,
                selection.top(),
                self.width() - selection.right() - 1,
                selection.height(),
            ),
        )
        for area in outside:
            if not area.isEmpty():
                painter.fillRect(area, shade)
        painter.setPen(QPen(QColor("#ffffff"), 2, Qt.PenStyle.DashLine))
        painter.drawRect(selection.adjusted(0, 0, -1, -1))
