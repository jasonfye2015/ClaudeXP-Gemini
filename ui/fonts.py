"""The two hands words are written in: hers - Italianno (the user's pick: fancy, elegant, readable; SIL Open Font
Licence, assets/fonts) - and his, a plain serif. Hers larger. Both sized from Options (her_size, his_size, in percent).

    fonts.her(records, base)   a QFont for her words, base points at 100%
    fonts.his(records, base)   for his
"""
from pathlib import Path

from PySide6.QtGui import QFont, QFontDatabase

ASSETS = Path(__file__).resolve().parents[1] / "assets" / "fonts"
HER_FILE = "Italianno-Regular.ttf"
SERIF = "Georgia"
_family = {}


def her_family():
    """Italianno, loaded once into the application's fonts (a serif italic if it can't be)."""
    if "her" not in _family:
        fid = QFontDatabase.addApplicationFont(str(ASSETS / HER_FILE))
        fams = QFontDatabase.applicationFontFamilies(fid) if fid >= 0 else []
        _family["her"] = fams[0] if fams else None
    return _family["her"]


def _scale(records, key):
    try:
        return max(0.5, min(2.0, float(records.options.get(key, 100)) / 100.0))
    except (AttributeError, TypeError, ValueError):
        return 1.0


def her(records, base=30):
    fam = her_family()
    f = QFont(fam or SERIF, max(8, int(round(base * _scale(records, "her_size")))))
    if fam is None:
        f.setItalic(True)
        f.setPointSize(max(8, int(round(base * 0.6 * _scale(records, "her_size")))))
    return f


def his(records, base=13):
    return QFont(SERIF, max(7, int(round(base * _scale(records, "his_size")))))
