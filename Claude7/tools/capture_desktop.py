"""Capture SYSTEM-2011's desktop as it is now - the icons (where each sits, which shortcuts are loose on the desktop,
the view options), the gadgets (which, and where) and the background (Personalization) - into
assets/desktop_layout.json, the desktop a new install or a format starts with.

    python tools/capture_desktop.py          (from the Claude7 folder; Claude7 needn't be running)"""
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "assets" / "desktop_layout.json"


def read(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def main():
    users = DATA / "Drive C" / "Users"
    desks = [d / "Desktop" for d in users.iterdir() if (d / "Desktop").is_dir()] if users.is_dir() else []
    if not desks:
        sys.exit("No desktop to capture (Claude7 hasn't been set up).")
    desk = max(desks, key=lambda d: d.stat().st_mtime)
    shortcuts, folders = [], []
    for path in sorted(desk.iterdir(), key=lambda p: p.name.lower()):
        if path.is_dir():
            folders.append(path.name)
        elif path.suffix.lower() == ".lnk":
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                if line.startswith("Program="):
                    shortcuts.append({"file": path.name, "program": line.split("=", 1)[1].strip()})
    names = {f"file:{s['file']}" for s in shortcuts} | {f"file:{f}" for f in folders}
    state = read(DATA / "desktop.json", {})
    positions = {k: v for k, v in (state.get("positions") or {}).items()
                 if k.startswith("sys:") or k in names}                  # (no stale entries)
    display = read(DATA / "display.json", {})
    if display.get("wallpaper"):
        wp = Path(display["wallpaper"])
        try:
            display["wallpaper"] = wp.relative_to(ROOT).as_posix()          # (kept relative to Claude7)
        except ValueError:
            pass
    gadgets = [{k: v for k, v in g.items() if not k.startswith("_")}
               for g in read(DATA / "gadgets.json", {}).get("gadgets", [])]
    layout = {
        "_help": "The desktop a new install (or a format) of SYSTEM-2011 starts with: icon grid positions (column, "
                 "row), the view options, the loose shortcuts and the program folders on the desktop, the gadgets "
                 "and where they sit (pixels), and the background (Personalization). Taken from the user's desktop, "
                 f"{date.today().isoformat()}, by tools/capture_desktop.py.",
        "positions": positions,
        "hidden": state.get("hidden", []),
        "auto_arrange": state.get("auto_arrange", False),
        "align_grid": state.get("align_grid", True),
        "show_icons": state.get("show_icons", True),
        "size": state.get("size", "Medium icons"),
        "shortcuts": shortcuts,
        "folders": folders,
        "gadgets": gadgets,
        "display": display,
    }
    OUT.write_text(json.dumps(layout, indent=1), encoding="utf-8")
    print(f"{len(positions)} icon positions, {len(shortcuts)} shortcuts, {len(folders)} folders, {len(gadgets)} "
          f"gadgets, background {display.get('wallpaper')} -> {OUT}")


if __name__ == "__main__":
    main()
