"""Gemini Word, the first Gemini Office application."""
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap

from .wordpad import open_wordpad


def gemini_word_icon():
    from .office_icons import office_icon
    icon = office_icon("word")
    if not icon.isNull():
        return icon
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(QColor("#34495E"), 1))
    painter.setBrush(QColor("#FFFFFF"))
    painter.drawRoundedRect(QRectF(5.5, 2.5, 20, 27), 1, 1)
    painter.setPen(QPen(QColor("#BCC9D5"), 1))
    for y, width in ((9, 11), (13, 13), (17, 9)):
        painter.drawLine(10, y, 10 + width, y)
    painter.setPen(QPen(QColor("#1F6AA5"), 1))
    painter.setBrush(QColor("#F5C451"))
    painter.drawEllipse(QRectF(16.5, 18.5, 13, 13))
    painter.setPen(QPen(QColor("#184B78"), 1))
    painter.drawText(QRectF(16, 18, 14, 14), Qt.AlignCenter, "G")
    painter.end()
    return QIcon(pm)


def open_gemini_word(desktop, path=None):
    open_wordpad(desktop, path, "Gemini Word", gemini_word_icon())
