"""Gemini Distiller: convert text documents and images into PDF files."""
from pathlib import Path

from PySide6.QtCore import QMarginsF, QRectF, Qt
from PySide6.QtGui import QColor, QImageReader, QPageLayout, QPageSize, QPainter, QPdfWriter, QTextDocument
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QPushButton, QStyle, QVBoxLayout,
                               QWidget)

from ..wm import XPWindow
from .office_icons import office_icon
from .notepad import SaveAsDialog, _read

IMAGE_EXTS = {".bmp", ".gif", ".jpg", ".jpeg", ".png"}
TEXT_EXTS = {".txt", ".md", ".csv", ".log", ".nfo", ".ini", ".html", ".htm", ".rtf"}
MAX_SOURCE_BYTES = 20 * 1024 * 1024
MAX_IMAGE_PIXELS = 40_000_000


class GeminiDistiller(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.source = None
        self.setObjectName("geminiDistiller")
        self.setStyleSheet(
            "QWidget#geminiDistiller { background: #ECE9D8; }"
            "QLabel#distillerStatus { border-top: 1px solid #ACA899; padding: 3px 6px; font: 11px Tahoma; }"
        )
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 0)
        root.addWidget(QLabel(
            "Create a PDF from a text document or image. Supported formats: TXT, RTF, HTML, CSV, "
            "Markdown, BMP, GIF, JPEG, and PNG."))
        row = QHBoxLayout()
        self.select_button = QPushButton("Select Source...")
        self.select_button.clicked.connect(self.choose_source)
        row.addWidget(self.select_button)
        self.source_label = QLabel("No source selected")
        self.source_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        row.addWidget(self.source_label, 1)
        root.addLayout(row)
        self.distill_button = QPushButton("Distill to PDF...")
        self.distill_button.setEnabled(False)
        self.distill_button.clicked.connect(self.choose_destination)
        root.addWidget(self.distill_button, alignment=Qt.AlignRight)
        root.addStretch()
        self.status = QLabel("Select a source document or image.")
        self.status.setObjectName("distillerStatus")
        root.addWidget(self.status)

    def name(self):
        return "Gemini Distiller"

    def choose_source(self):
        from .opendialog import open_dialog
        open_dialog(self.desktop, "Select Source Document", IMAGE_EXTS | TEXT_EXTS, self.set_source,
                    icon=gemini_distiller_icon())

    def set_source(self, path):
        self.source = Path(path)
        self.source_label.setText(self.source.name)
        self.source_label.setToolTip(str(self.source))
        self.distill_button.setEnabled(True)
        self.status.setText("Ready to create a PDF.")

    def choose_destination(self):
        if self.source is None:
            return
        suggested = self.source.with_suffix(".pdf").name

        def selected(path):
            target = path if path.suffix.lower() == ".pdf" else path.with_suffix(".pdf")
            self.distill(self.source, target)

        SaveAsDialog(self.desktop, suggested, self.source.parent, selected)

    @staticmethod
    def _image(path):
        reader = QImageReader(str(path))
        reader.setAutoTransform(True)
        size = reader.size()
        if not size.isValid() or size.width() * size.height() > MAX_IMAGE_PIXELS:
            raise ValueError("The source image has invalid or oversized dimensions.")
        image = reader.read()
        if image.isNull():
            raise ValueError("The source image could not be decoded.")
        return image

    @staticmethod
    def _document(path):
        if path.stat().st_size > MAX_SOURCE_BYTES:
            raise ValueError("The source document exceeds the 20 MB limit.")
        suffix = path.suffix.lower()
        doc = QTextDocument()
        if suffix == ".rtf":
            from .wordpad import from_rtf
            from_rtf(_read(path), doc)
        elif suffix in (".html", ".htm"):
            doc.setHtml(_read(path))
        else:
            doc.setPlainText(_read(path))
        return doc

    @classmethod
    def distill_to_pdf(cls, source, target):
        source, target = Path(source), Path(target)
        if source.suffix.lower() not in IMAGE_EXTS | TEXT_EXTS:
            raise ValueError(f"{source.suffix or 'This'} file type is not supported.")
        if not source.is_file():
            raise OSError(f"The source file does not exist: {source}")
        target.parent.mkdir(parents=True, exist_ok=True)
        writer = QPdfWriter(str(target))
        writer.setTitle(source.stem)
        writer.setCreator("Gemini Distiller")
        writer.setPageSize(QPageSize(QPageSize.Letter))
        writer.setPageMargins(QMarginsF(15, 15, 15, 15), QPageLayout.Millimeter)
        if source.suffix.lower() in IMAGE_EXTS:
            image = cls._image(source)
            painter = QPainter(writer)
            if not painter.isActive():
                raise OSError("Could not start the PDF writer.")
            page = QRectF(writer.pageLayout().paintRectPixels(writer.resolution()))
            scale = min(page.width() / image.width(), page.height() / image.height())
            width, height = image.width() * scale, image.height() * scale
            target_rect = QRectF((page.width() - width) / 2, (page.height() - height) / 2, width, height)
            painter.fillRect(page, Qt.white)
            painter.drawImage(target_rect, image)
            painter.end()
        else:
            document = cls._document(source)
            document.setDocumentMargin(24)
            document.print_(writer)
        if not target.is_file() or target.stat().st_size == 0:
            raise OSError("PDF creation did not produce an output file.")
        return target

    def distill(self, source, target):
        self.status.setText("Creating PDF...")
        self.distill_button.setEnabled(False)
        QApplication.processEvents()
        try:
            output = self.distill_to_pdf(source, target)
        except (OSError, UnicodeError, ValueError, RuntimeError) as error:
            self.distill_button.setEnabled(True)
            self.status.setText("PDF creation failed.")
            return self._message("Gemini Distiller", f"Could not create {Path(target).name}.\n{error}", "error")
        self.distill_button.setEnabled(True)
        self.status.setText(f"Created {output.name}.")
        self._message("Gemini Distiller", f"PDF created successfully:\n{output}", "info")
        return output

    def _message(self, title, text, icon="info"):
        from ..explorer.dialogs import msgbox
        return msgbox(self.desktop, title, text, icon)


def gemini_distiller_icon():
    icon = office_icon("distiller")
    if not icon.isNull():
        return icon
    return QApplication.style().standardIcon(QStyle.SP_FileIcon)


def open_gemini_distiller(desktop):
    body = GeminiDistiller(desktop)
    window = XPWindow(desktop, "Gemini Distiller", body, gemini_distiller_icon(), (600, 250))
    body.frame = window
    desktop.open_window(window)
    return window
