"""On a Mac: the closest Mac fonts for the Windows fonts the Timeline asks for by name. macOS already has Tahoma, Arial,
Verdana, Trebuchet MS, Georgia and Courier New; Segoe UI (Windows 7 and 11's face), Consolas, Lucida Console and the
rest are Microsoft's and aren't there, so without this Qt picks whatever it finds, with the wrong widths.

    from claudecore import macfonts
    macfonts.apply()        # once, right after the QApplication is made; does nothing off a Mac
"""
import sys

SUBSTITUTES = {
    "Segoe UI": None, "Segoe UI Variable": None, "Segoe UI Variable Text": None, "Segoe UI Variable Display": None,
    "Segoe UI Light": None, "Segoe UI Semibold": None, "Segoe UI Semilight": None,     # None: the Mac's own UI font
    "Segoe UI Symbol": "Apple Symbols", "Segoe UI Emoji": "Apple Color Emoji",
    "Consolas": "Menlo", "Lucida Console": "Monaco", "Cascadia Mono": "Menlo", "Cascadia Code": "Menlo",
    "Franklin Gothic Medium": "Avenir Next Condensed", "Calibri": "Helvetica Neue", "Lucida Sans Unicode": "Lucida Grande",
}


def apply():
    if sys.platform != "darwin":
        return
    try:
        from PySide6.QtGui import QFont, QFontDatabase
        ui = QFontDatabase.systemFont(QFontDatabase.GeneralFont).family() or "Helvetica Neue"
        for windows, mac in SUBSTITUTES.items():
            QFont.insertSubstitution(windows, mac or ui)
    except Exception:
        pass
