"""ClaudeXP shortcuts (.lnk): tiny text files that point at a ClaudeXP program or a file/folder on the virtual PC.

    [ClaudeXP Shortcut]
    Program=comix

Explorer and the desktop show them without the .lnk, with the program's own icon, and opening one launches it.
A real (binary) Windows .lnk that ends up on the drive just shows a plain icon."""
from pathlib import Path

HEADER = "[ClaudeXP Shortcut]"


def _program(key):
    from .. import programs
    return next((p for p in programs.PROGRAMS if p.key == key), None)


def read(path):
    """{'program': key} or {'target': path}, or {} if it isn't one of ours."""
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    if not text.lstrip().startswith(HEADER):
        return {}
    out = {}
    for line in text.splitlines()[1:]:
        if "=" in line:
            k, v = line.split("=", 1)
            out[k.strip().lower()] = v.strip()
    return out


def make(path, program=None, target=None):
    lines = [HEADER]
    if program:
        lines.append(f"Program={program}")
    if target:
        lines.append(f"Target={target}")
    Path(path).write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")


def is_shortcut(path):
    return Path(path).suffix.lower() == ".lnk"


def icon(path):
    """The icon of what the shortcut points at (None if unknown)."""
    info = read(path)
    if info.get("program"):
        prog = _program(info["program"])
        if prog is not None:
            try:
                return prog.icon()
            except Exception:
                return None
    if info.get("target"):
        from PySide6.QtCore import QFileInfo
        from .fileicons import XPIconProvider
        target = Path(info["target"])
        if target.exists():
            return XPIconProvider().icon(QFileInfo(str(target)))
    return None


def open_shortcut(desktop, path):
    info = read(path)
    if info.get("program"):
        from .. import programs
        if _program(info["program"]) is not None:
            programs.launch(desktop, info["program"])
            return True
    if info.get("target"):
        target = Path(info["target"])
        if target.is_dir():
            from . import launch
            launch(desktop, target)
            return True
        if target.exists():
            from .viewers import open_file
            open_file(desktop, target)
            return True
    from .dialogs import msgbox
    msgbox(desktop, "Problem with Shortcut", f"The item '{Path(path).stem}' that this shortcut refers to has been "
                                            "changed or moved, so this shortcut will no longer work properly.", "error")
    return False
