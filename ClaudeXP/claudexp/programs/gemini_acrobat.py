"""Gemini Acrobat: a PDF reader built on Qt's PDF engine."""
from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QImage, QPainter, QPixmap
from PySide6.QtPdf import QPdfDocument
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QMenuBar, QPushButton, QScrollArea,
                               QSpinBox, QStyle, QVBoxLayout, QWidget)

from ..wm import XPWindow
from .office_icons import office_icon


class GeminiAcrobat(QWidget):
    def __init__(self, desktop, path=None):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.path = None
        self.page = 0
        self.zoom = 100
        self.document = QPdfDocument(self)
        self.setStyleSheet(
            "QWidget#geminiAcrobat { background: #ECE9D8; }"
            "QLabel#pdfPage { background: #777777; }"
            "QLabel#pdfStatus { border-top: 1px solid #ACA899; padding: 2px 6px; font: 11px Tahoma; }"
        )
        self.setObjectName("geminiAcrobat")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        menu = QMenuBar()
        file_menu = menu.addMenu("&File")
        file_menu.addAction("&Open...", self.open_dialog, "Ctrl+O")
        file_menu.addAction("&Print Current Page...", self.print_page, "Ctrl+P")
        file_menu.addSeparator()
        file_menu.addAction("E&xit", lambda: self.frame.request_close() if self.frame else None)
        view_menu = menu.addMenu("&View")
        view_menu.addAction("&Zoom In", lambda: self.set_zoom(self.zoom + 25), "Ctrl++")
        view_menu.addAction("Zoom &Out", lambda: self.set_zoom(self.zoom - 25), "Ctrl+-")
        view_menu.addAction("&Actual Size", lambda: self.set_zoom(100), "Ctrl+0")
        menu.addMenu("&Help").addAction("&About Gemini Acrobat", self.about)
        root.addWidget(menu)

        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(5, 4, 5, 4)
        self.previous = QPushButton("◀ Previous")
        self.next = QPushButton("Next ▶")
        self.page_number = QSpinBox()
        self.page_number.setRange(1, 1)
        self.page_count = QLabel("of 0")
        self.zoom_spin = QSpinBox()
        self.zoom_spin.setRange(25, 400)
        self.zoom_spin.setSingleStep(25)
        self.zoom_spin.setSuffix("%")
        self.zoom_spin.setValue(self.zoom)
        self.fit_button = QPushButton("Fit Page")
        toolbar.addWidget(self.previous)
        toolbar.addWidget(self.next)
        toolbar.addSpacing(8)
        toolbar.addWidget(QLabel("Page:"))
        toolbar.addWidget(self.page_number)
        toolbar.addWidget(self.page_count)
        toolbar.addStretch()
        toolbar.addWidget(self.fit_button)
        toolbar.addWidget(QLabel("Zoom:"))
        toolbar.addWidget(self.zoom_spin)
        root.addLayout(toolbar)

        self.page_image = QLabel()
        self.page_image.setAlignment(Qt.AlignCenter)
        self.page_image.setObjectName("pdfPage")
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setAlignment(Qt.AlignCenter)
        self.scroll.setWidget(self.page_image)
        root.addWidget(self.scroll, 1)
        self.status = QLabel("Open a PDF document to begin.")
        self.status.setObjectName("pdfStatus")
        root.addWidget(self.status)

        self.previous.clicked.connect(lambda: self.show_page(self.page - 1))
        self.next.clicked.connect(lambda: self.show_page(self.page + 1))
        self.fit_button.clicked.connect(self.fit_page)
        self.page_number.valueChanged.connect(lambda n: self.show_page(n - 1))
        self.zoom_spin.valueChanged.connect(self.set_zoom)
        if path is not None:
            self.open_file(path)

    def name(self):
        return self.path.name if self.path else "No document"

    def update_title(self):
        if self.frame is not None:
            self.frame.set_title(f"{self.name()} - Gemini Acrobat")

    def open_file(self, path):
        path = Path(path)
        candidate = QPdfDocument()
        candidate.load(str(path))
        if candidate.status() != QPdfDocument.Status.Ready:
            error = f"PDF error: {candidate.error().name}"
            candidate.close()
            self._message("Gemini Acrobat", f"Cannot open {path.name}.\n{error}", "error")
            return False
        candidate.setParent(self)
        old_document = self.document
        self.document = candidate
        old_document.close()
        old_document.deleteLater()
        self.path = path
        self.page = 0
        count = self.document.pageCount()
        self.page_number.blockSignals(True)
        self.page_number.setRange(1, max(1, count))
        self.page_number.setValue(1)
        self.page_number.blockSignals(False)
        self.page_count.setText(f"of {count}")
        self.previous.setEnabled(count > 1)
        self.next.setEnabled(count > 1)
        self.update_title()
        self.show_page(0)
        return True

    def show_page(self, index):
        count = self.document.pageCount()
        if not count:
            return
        self.page = max(0, min(index, count - 1))
        if self.page_number.value() != self.page + 1:
            self.page_number.blockSignals(True)
            self.page_number.setValue(self.page + 1)
            self.page_number.blockSignals(False)
        self.previous.setEnabled(self.page > 0)
        self.next.setEnabled(self.page < count - 1)

        points = self.document.pagePointSize(self.page)
        width = max(1, round(points.width() * 96 / 72 * self.zoom / 100))
        height = max(1, round(points.height() * 96 / 72 * self.zoom / 100))
        ratio = min(1.0, 4000 / max(width, height), (20_000_000 / (width * height)) ** 0.5)
        target = QSize(max(1, round(width * ratio)), max(1, round(height * ratio)))
        rendered = self.document.render(self.page, target)
        if rendered.isNull():
            self.page_image.clear()
            self.status.setText(f"Could not render page {self.page + 1}.")
            return
        page = QImage(rendered.size(), QImage.Format_RGB32)
        page.fill(Qt.white)
        painter = QPainter(page)
        painter.drawImage(0, 0, rendered)
        painter.end()
        self.page_image.setPixmap(QPixmap.fromImage(page))
        self.page_image.resize(page.size())
        self.status.setText(f"Page {self.page + 1} of {count}    {self.zoom}%")

    def set_zoom(self, zoom):
        self.zoom = max(25, min(400, int(zoom)))
        if self.zoom_spin.value() != self.zoom:
            self.zoom_spin.blockSignals(True)
            self.zoom_spin.setValue(self.zoom)
            self.zoom_spin.blockSignals(False)
        self.show_page(self.page)

    def fit_page(self):
        if not self.document.pageCount():
            return
        points = self.document.pagePointSize(self.page)
        available = self.scroll.viewport().size()
        if points.width() <= 0 or points.height() <= 0 or available.isEmpty():
            return
        width_zoom = available.width() * 72 / (points.width() * 96) * 100
        height_zoom = available.height() * 72 / (points.height() * 96) * 100
        self.set_zoom(round(min(width_zoom, height_zoom)))

    def open_dialog(self):
        from .opendialog import open_dialog
        open_dialog(self.desktop, "Open PDF", {".pdf"}, self.open_file, icon=gemini_acrobat_icon(),
                    start=self.path.parent if self.path else None)

    def print_page(self):
        if not self.document.pageCount():
            return self._message("Gemini Acrobat", "Open a PDF document first.", "info")
        from ..explorer import vfs
        from ..printing import print_image
        temp = vfs.DRIVE_C / "WINDOWS" / "Temp"
        temp.mkdir(parents=True, exist_ok=True)
        file = temp / f"{self.path.stem if self.path else 'Document'} - page {self.page + 1}.png"
        points = self.document.pagePointSize(self.page)
        scale = min(1500 / max(1, points.width()), 2000 / max(1, points.height()))
        target = QSize(max(1, round(points.width() * scale)), max(1, round(points.height() * scale)))
        rendered = self.document.render(self.page, target)
        if rendered.isNull():
            return self._message("Gemini Acrobat", "Could not render the page for printing.", "error")
        image = QImage(rendered.size(), QImage.Format_RGB32)
        image.fill(Qt.white)
        painter = QPainter(image)
        painter.drawImage(0, 0, rendered)
        painter.end()
        if not image.save(str(file), "PNG"):
            return self._message("Gemini Acrobat", "Could not save the rendered page for printing.", "error")
        print_image(self.desktop, file)

    def closeEvent(self, event):
        self.document.close()
        self.document.deleteLater()
        event.accept()

    def about(self):
        self._message("About Gemini Acrobat", "Gemini Acrobat\nVersion 1.0\n\n"
                      "View and print PDF documents.")

    def _message(self, title, text, icon="info"):
        from ..explorer.dialogs import msgbox
        return msgbox(self.desktop, title, text, icon)


def gemini_acrobat_icon():
    icon = office_icon("acrobat")
    if not icon.isNull():
        return icon
    return QApplication.style().standardIcon(QStyle.SP_FileIcon)


def open_gemini_acrobat(desktop, path=None):
    body = GeminiAcrobat(desktop, path)
    window = XPWindow(desktop, f"{body.name()} - Gemini Acrobat", body, gemini_acrobat_icon(), (960, 720))
    body.frame = window
    desktop.open_window(window)
    return window
