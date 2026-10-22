"""Where Claude7 keeps things, and cached image loading.

  ROOT            Claude7/                 this computer
  DATA            Claude7/data             everything that changes: the account, drive C:, journals, mail, settings
  PROGRAM_FILES   Claude7/Program Files    the period programs' own data on this computer (ClaudeAIM's contacts and
                                           chats, the IRC and MUCK regulars, the Fur Directory's residents...)
  ASSETS          Claude7/assets           Windows 7's artwork and sounds
  XP_ROOT         ClaudeXP/                the period programs' code and artwork, run here through xpcompat.py
"""
from functools import lru_cache
from pathlib import Path

from PySide6.QtGui import QIcon, QPixmap

ROOT = Path(__file__).resolve().parent.parent
TIMELINE = ROOT.parent
DATA = ROOT / "data"
PROGRAM_FILES = ROOT / "Program Files"
ASSETS = ROOT / "assets"
IMAGES = ASSETS / "images"
SOUNDS = ASSETS / "sounds"
BACKGROUNDS = ASSETS / "backgrounds"
ICONS = ASSETS / "icons"
USER_PICTURES = ASSETS / "user_pictures"
XP_ROOT = TIMELINE / "ClaudeXP"


@lru_cache(maxsize=None)
def pixmap(name):
    """An image from assets/images (a sub-folder path is fine: 'logon/Logon_Template.png'). Null if missing."""
    return QPixmap(str(IMAGES / name))


@lru_cache(maxsize=None)
def icon(name):
    """An icon file from assets/icons."""
    return QIcon(str(ICONS / name))


def find_image(stem):
    """The first assets/images/<stem>.* file, or None."""
    for path in sorted(IMAGES.glob(stem + ".*")):
        return path
    return None
