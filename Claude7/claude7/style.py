"""App-wide look for the programs running inside Claude7: Windows 7's controls (the host's Windows style where there
is one, else Fusion), Segoe UI, and no dark mode (2011 had none)."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QStyleFactory

FACE = "#F0F0F0"


def apply(app):
    app.styleHints().setColorScheme(Qt.ColorScheme.Light)
    keys = QStyleFactory.keys()
    for name in ("windowsvista", "Windows", "Fusion"):
        if name in keys:
            app.setStyle(name)
            break
    pal = QPalette()
    for role, color in [
        (QPalette.Window, FACE), (QPalette.Button, FACE), (QPalette.Base, "#FFFFFF"),
        (QPalette.AlternateBase, "#F7F7F7"), (QPalette.WindowText, "#000000"), (QPalette.Text, "#000000"),
        (QPalette.ButtonText, "#000000"), (QPalette.Highlight, "#3399FF"), (QPalette.HighlightedText, "#FFFFFF"),
        (QPalette.ToolTipBase, "#FFFFFF"), (QPalette.ToolTipText, "#575757"), (QPalette.Link, "#0066CC"),
    ]:
        pal.setColor(role, QColor(color))
    app.setPalette(pal)
    app.setFont(QFont("Segoe UI", 9))
