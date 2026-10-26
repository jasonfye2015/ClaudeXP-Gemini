"""Locations of assets, contacts and saved data."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
IMAGES = ASSETS / "images"
SOUNDS = ASSETS / "sounds"
ICONS = ASSETS / "icons"
CONTACTS = ROOT / "contacts"
DATA = ROOT / "data"
HISTORY = DATA / "history"

ICON_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp"}


def image(name: str) -> str:
    return str(IMAGES / name)


def sound(name: str) -> str:
    return str(SOUNDS / name)


def natural_key(text: str):
    return [int(p) if p.isdigit() else p.lower() for p in re.split(r"(\d+)", text)]


def buddy_icons() -> list[Path]:
    """All selectable buddy icons, in natural order (Icon2 before Icon10)."""
    if not ICONS.exists():
        return []
    files = [p for p in ICONS.iterdir() if p.suffix.lower() in ICON_EXTS]
    return sorted(files, key=lambda p: natural_key(p.name))


def resolve_icon(name: str | None) -> str:
    """Find an icon by filename in assets/icons, then contacts/, else the default."""
    if name:
        for folder in (ICONS, CONTACTS, IMAGES):
            candidate = folder / name
            if candidate.exists():
                return str(candidate)
        moved = Path(name)
        if moved.is_absolute() and "Program Files" in moved.parts:   # a full path from before the computer moved
            i = len(moved.parts) - 1 - moved.parts[::-1].index("Program Files")
            candidate = ROOT.parent.joinpath(*moved.parts[i + 1:])
            if candidate.exists():
                return str(candidate)
    icons = buddy_icons()
    return str(icons[0]) if icons else image("buddyicon.jpg")
