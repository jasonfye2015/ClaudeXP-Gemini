"""Where Claude11 keeps things, and cached image loading.

  ROOT            Claude11/                this computer
  DATA            Claude11/data            everything that changes: the account, drive C:, journals, mail, settings
  PROGRAM_FILES   Claude11/Program Files   the period programs' own data on this computer (the IRC and MUCK regulars,
                                           the Fur Directory's residents, the browsers' favourites...)
  ASSETS          Claude11/assets          Claude11's own artwork (the ASUS splash) and anything you add
  XP_ROOT         ClaudeXP/                the period programs' code and artwork, run here through xpcompat.py

Windows 11's wallpapers and sounds are not part of the project. They come, in this order, from assets/backgrounds and
assets/sounds (anything you put there), from Local Storage/Windows 11 Media/Wallpapers and /sounds (the user's own
collection on the shared drive), and from the real PC's C:\\Windows\\Web and C:\\Windows\\Media when this is a Windows
machine. Without any of them, Claude11 draws its own.
"""
import os
import re
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
HOST_WINDOWS = Path(os.environ.get("SystemRoot") or r"C:\Windows")
HOST_WEB = HOST_WINDOWS / "Web"
HOST_MEDIA = HOST_WINDOWS / "Media"
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}
MEDIA_FOLDER = "Windows 11 Media"              # inside Local Storage: Wallpapers/ and sounds/
# the folders under C:\Windows\Web\Wallpaper and what Windows 11 calls those themes
HOST_THEMES = {"Windows": "Windows", "ThemeA": "Glow", "ThemeB": "Captured Motion", "ThemeC": "Sunrise",
               "ThemeD": "Flow", "Theme1": "Windows (light)", "Theme2": "Windows (dark)"}
_RES_RE = re.compile(r"[-_ ]\d{3,5}x\d{3,5}([-_ ]\d+)?$")


@lru_cache(maxsize=None)
def pixmap(name):
    """An image from assets/images (a sub-folder path is fine: 'boot/asus_splash.png'). Null if missing."""
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


# ---- the user's Windows 11 media on the shared drive ----------------------------------------------------------------
def media_root():
    """Local Storage/Windows 11 Media (any capitalisation), or None when there isn't one."""
    try:
        from . import vfs
        storage = vfs.local_storage()
    except Exception:
        storage = TIMELINE / "Local Storage"
    if not storage.is_dir():
        return None
    wanted = MEDIA_FOLDER.lower()
    try:
        for d in storage.iterdir():
            if d.is_dir() and d.name.lower() == wanted:
                return d
    except OSError:
        pass
    return None


def _media_sub(name):
    root = media_root()
    if root is None:
        return None
    try:
        for d in root.iterdir():
            if d.is_dir() and d.name.lower() == name.lower():
                return d
    except OSError:
        pass
    return None


def pretty_label(stem):
    """'windows-11-stock-official-colorful-3840x2160-5658' -> 'Windows 11 Stock Official Colorful'."""
    s = _RES_RE.sub("", stem)
    words = [w for w in re.split(r"[-_ ]+", s) if w]
    out = []
    for w in words:
        if w.lower() in ("windows", "win") and out == []:
            out.append("Windows")
        elif w.isdigit() or w.lower() in ("4k", "5k", "8k", "amoled", "hd"):
            out.append(w.upper() if not w.isdigit() else w)
        else:
            out.append(w[:1].upper() + w[1:].lower())
    return " ".join(out) or stem


def media_wallpapers():
    """[(label, path)] of the pictures in Local Storage/Windows 11 Media/Wallpapers, the Bloom first."""
    folder = _media_sub("Wallpapers")
    if folder is None:
        return []
    files = sorted((p for p in folder.iterdir() if p.suffix.lower() in IMAGE_EXTS),
                   key=lambda p: (0 if "bloom" in p.stem.lower() else 1, p.stat().st_size if p.suffix.lower() == ".png"
                                  else 0, p.name.lower()))
    out, seen = [], {}
    for p in files:
        label = pretty_label(p.stem)
        n = seen.get(label, 0) + 1
        seen[label] = n
        out.append((label if n == 1 else f"{label} {n}", p))
    return out


def media_sounds():
    """Local Storage/Windows 11 Media/sounds, or None."""
    return _media_sub("sounds")


def host_wallpapers():
    """[(label, path)] of the wallpapers Windows 11 itself ships, when this is a Windows PC (the Bloom first)."""
    out = []
    base = HOST_WEB / "Wallpaper"
    if not base.is_dir():
        return out
    for folder, theme in HOST_THEMES.items():
        d = base / folder
        if not d.is_dir():
            continue
        files = sorted(p for p in d.iterdir() if p.suffix.lower() in IMAGE_EXTS)
        for i, p in enumerate(files):
            if folder == "Windows":
                label = "Windows 11" if p.stem == "img0" else "Windows 11 (dark)" if p.stem == "img19" else p.stem
            else:
                label = theme if len(files) == 1 else f"{theme} {i + 1}"
            out.append((label, p))
    return out


def lock_images():
    """The lock screen pictures: assets/images/lock/* first, then the landscapes and skies of Local Storage's
    Windows 11 Media, then Windows 11's own (C:\\Windows\\Web\\Screen)."""
    out = sorted(p for p in (IMAGES / "lock").glob("*") if p.suffix.lower() in IMAGE_EXTS) \
        if (IMAGES / "lock").is_dir() else []
    media = [p for _label, p in media_wallpapers()]
    scenic = [p for p in media if any(k in p.stem.lower() for k in ("landscape", "sunrise", "sunset", "forest", "desert",
                                                                     "solar", "scenery", "waves", "layers", "floating"))]
    out += scenic + [p for p in media if p not in scenic]
    screen = HOST_WEB / "Screen"
    if screen.is_dir():
        out += sorted(p for p in screen.iterdir() if p.suffix.lower() in IMAGE_EXTS)
    return out
