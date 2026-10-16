"""Icons supplied for the Gemini-branded application suite."""
from functools import lru_cache

from PySide6.QtGui import QIcon

from ..paths import ROOT

_FILES = {
    "word": "Rokey-Smooth-Metal-Software-Pack-Microsoft-office-2003-word.128.png",
    "excel": "Rokey-Smooth-Metal-Software-Pack-Microsoft-office-2003-excel.128.png",
    "powerpoint": "Rokey-Smooth-Metal-Software-Pack-Microsoft-office-2003-powerpoint.128.png",
    "outlook": "Rokey-Smooth-Metal-Software-Pack-Microsoft-office-2003-outlook.128.png",
    "access": "Rokey-Smooth-Metal-Software-Pack-Microsoft-office-2003-access.128.png",
    "publisher": "Rokey-Smooth-Metal-Software-Pack-Microsoft-office-2003-publisher.128.png",
    "photo": "Rokey-Smooth-Metal-Software-Pack-Adobe-photoshop-cs.128.png",
    "draw": "Rokey-Smooth-Metal-Software-Pack-Adobe-illustrator-cs.128.png",
    "acrobat": "Rokey-Smooth-Metal-Software-Pack-Adobe-acrobat-professional.128.png",
    "distiller": "Rokey-Smooth-Metal-Software-Pack-Adobe-acrobat-distiller.128.png",
}


@lru_cache(maxsize=None)
def office_icon(product):
    filename = _FILES.get(product)
    if filename is None:
        return QIcon()
    icon = QIcon(str(ROOT / "Addon Icons" / filename))
    return icon if not icon.isNull() else QIcon()
