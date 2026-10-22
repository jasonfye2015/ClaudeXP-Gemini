"""App-wide look for the programs running inside Claude11: Windows 11's controls (Qt's windows11 style where there is
one, else the host's Windows style, else Fusion), Segoe UI Variable, the light theme."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QFontDatabase, QPalette
from PySide6.QtWidgets import QStyleFactory

FACE = "#F3F3F3"
ACCENT = "#0067C0"
_family = None


def font_family():
    """Segoe UI Variable (Windows 11's face) when it's installed, else Segoe UI."""
    global _family
    if _family is None:
        families = set(QFontDatabase.families())
        for name in ("Segoe UI Variable Text", "Segoe UI Variable", "Segoe UI"):
            if name in families:
                _family = name
                break
        else:
            _family = "Segoe UI"
    return _family


def display_family():
    """The display cut for big text (the lock screen's clock, the Start menu's headings)."""
    families = set(QFontDatabase.families())
    for name in ("Segoe UI Variable Display", "Segoe UI Variable", "Segoe UI Light", "Segoe UI"):
        if name in families:
            return name
    return "Segoe UI"


def font(size=12, weight=QFont.Normal, display=False):
    f = QFont(display_family() if display else font_family())
    f.setPixelSize(size)
    if isinstance(weight, int) and not isinstance(weight, QFont.Weight):
        weight = QFont.Weight(max(1, min(1000, weight)))
    f.setWeight(weight)
    return f


def apply(app):
    app.styleHints().setColorScheme(Qt.ColorScheme.Light)
    keys = QStyleFactory.keys()
    for name in ("windows11", "windowsvista", "Windows", "Fusion"):
        if name in keys:
            app.setStyle(name)
            break
    pal = QPalette()
    for role, color in [
        (QPalette.Window, FACE), (QPalette.Button, "#FBFBFB"), (QPalette.Base, "#FFFFFF"),
        (QPalette.AlternateBase, "#F9F9F9"), (QPalette.WindowText, "#1A1A1A"), (QPalette.Text, "#1A1A1A"),
        (QPalette.ButtonText, "#1A1A1A"), (QPalette.Highlight, ACCENT), (QPalette.HighlightedText, "#FFFFFF"),
        (QPalette.ToolTipBase, "#F9F9F9"), (QPalette.ToolTipText, "#1A1A1A"), (QPalette.Link, "#003E92"),
        (QPalette.PlaceholderText, "#767676"),
    ]:
        pal.setColor(role, QColor(color))
    app.setPalette(pal)
    app.setFont(QFont(font_family(), 9))
