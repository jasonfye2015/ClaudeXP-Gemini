"""App-wide look for programs running inside ClaudeXP: classic Windows controls.

Matches ClaudeAIM's own retro style so hosted programs look the way they do standalone.
"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPalette

GREY = "#c0c0c0"


def apply(app):
    app.styleHints().setColorScheme(Qt.ColorScheme.Light)  # XP had no dark mode
    app.setStyle("Windows")
    pal = QPalette()
    for role, color in [
        (QPalette.Window, GREY), (QPalette.Button, GREY), (QPalette.Base, "#ffffff"),
        (QPalette.AlternateBase, "#ffffff"), (QPalette.WindowText, "#000000"),
        (QPalette.Text, "#000000"), (QPalette.ButtonText, "#000000"),
        (QPalette.Highlight, "#316AC5"), (QPalette.HighlightedText, "#ffffff"),
        (QPalette.ToolTipBase, "#ffffe1"), (QPalette.ToolTipText, "#000000"),
    ]:
        pal.setColor(role, QColor(color))
    app.setPalette(pal)
    app.setFont(QFont("Tahoma", 8))
