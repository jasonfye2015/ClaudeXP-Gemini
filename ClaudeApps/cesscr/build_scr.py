"""Builds dist\\Claude Entertainment System.scr - one file, the games and their sprite sheets inside it.

    1. build\\pkg\\claudexp: ClaudeXP's NES clock games and the Claude Entertainment System, copied as they are, with
       the shim folder's stand-ins for ClaudeXP's drive, settings, sound and dialogs, and a screensaver.py made of
       ClaudeXP's own Saver (its timing included) and just these games.
    2. build\\sprites: only the sheets and maps the games read, from Local Storage.
    3. an icon from Mario's sprite, then PyInstaller (one file, no console) and .exe -> .scr.

Run it with build_scr.bat (it makes its own Python with PySide6 and PyInstaller, apart from ClaudeXP's)."""
import ast
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TIMELINE = HERE.parents[1]
XP = TIMELINE / "ClaudeXP" / "claudexp"
STORAGE = TIMELINE / "Local Storage"
BUILD, DIST = HERE / "build", HERE / "dist"
PKG = BUILD / "pkg" / "claudexp"
SPRITES = BUILD / "sprites"
NAME = "Claude Entertainment System"
GAMES = ["supercb", "smb3cb", "zeldacb", "zelda2cb", "metroidcb", "ces"]
SAVERS = [("Super Claude Bros", "supercb"), ("Super Claude Bros. 3", "smb3cb"), ("The Legend of Claude", "zeldacb"),
          ("Zelda II: The Adventure of Claude", "zelda2cb"), ("Metroid: Claude's Mission", "metroidcb")]


def make_package():
    if PKG.parent.exists():
        shutil.rmtree(PKG.parent)
    (PKG / "explorer").mkdir(parents=True)
    for name in GAMES:
        shutil.copy2(XP / f"{name}.py", PKG / f"{name}.py")
    (PKG / "__init__.py").write_text('"""ClaudeXP\'s NES clock games, for the .scr."""\n', encoding="utf-8")
    (PKG / "explorer" / "__init__.py").write_text("", encoding="utf-8")
    shutil.copy2(HERE / "shim" / "vfs.py", PKG / "explorer" / "vfs.py")
    for name in ("display", "sound", "network"):
        shutil.copy2(HERE / "shim" / f"{name}.py", PKG / f"{name}.py")
    # ClaudeXP's Saver, word for word, and the games
    source = (XP / "screensaver.py").read_text(encoding="utf-8")
    saver = next(n for n in ast.parse(source).body if isinstance(n, ast.ClassDef) and n.name == "Saver")
    lines = ['"""The screen savers in the .scr: ClaudeXP\'s Saver and the NES clock games."""',
             "import time", "", "from PySide6.QtCore import Qt, QTimer", "from PySide6.QtWidgets import QWidget", "",
             f"from . import {', '.join(GAMES)}", "", "",
             ast.get_source_segment(source, saver), "", "",
             "SAVERS = {"]
    lines += [f"    {title!r}: {mod}.make_saver_class(Saver)," for title, mod in SAVERS]
    lines += ["}", f"SAVERS[{NAME!r}] = ces.make_saver_class(Saver, SAVERS)", ""]
    (PKG / "screensaver.py").write_text("\n".join(lines), encoding="utf-8")


def gather_sprites():
    """Each game's sheets (and Metroid's maps), from Local Storage into build\\sprites under the same folder names."""
    if SPRITES.exists():
        shutil.rmtree(SPRITES)
    sys.path.insert(0, str(PKG.parent))
    import importlib
    wanted = []
    for mod in ("supercb", "smb3cb", "zeldacb", "zelda2cb", "metroidcb"):
        m = importlib.import_module(f"claudexp.{mod}")
        folders = getattr(m, "FOLDERS", None) or (m.FOLDER,)
        folder = next((f for f in folders if (STORAGE / f).is_dir()), folders[0])
        files = list(m.SHEETS.values())
        if hasattr(m, "MAP"):
            files += [m.MAP.format(a) for a in m.AREAS.values()]
        wanted += [(folder, f) for f in files]
    missing = []
    for folder, f in wanted:
        src = STORAGE / folder / f
        if not src.exists():
            missing.append(f"{folder}\\{f}")
            continue
        (SPRITES / folder).mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, SPRITES / folder / f)
    size = sum(p.stat().st_size for p in SPRITES.rglob("*") if p.is_file())
    print(f"sprites: {len(wanted) - len(missing)} files, {size / 2**20:.1f} MB")
    for m in missing:
        print("  missing (that game will be skipped):", m)


def make_icon():
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QGuiApplication
    QGuiApplication.instance() or QGuiApplication([])
    from claudexp import supercb
    mario = supercb.cut("chars", supercb.FRAME_X[0], 8, 16, 16)
    icon = BUILD / "ces.ico"
    mario.scaled(256, 256, Qt.IgnoreAspectRatio, Qt.FastTransformation).save(str(icon))
    return icon


def pyinstall(icon):
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--onefile", "--windowed", "--name", NAME,
           "--distpath", str(DIST), "--workpath", str(BUILD / "work"), "--specpath", str(BUILD),
           "--paths", str(PKG.parent), "--add-data", f"{SPRITES};sprites", "--icon", str(icon),
           "--hidden-import", "claudexp.screensaver"]
    for heavy in ("PySide6.QtMultimedia", "PySide6.QtNetwork", "PySide6.QtQml", "PySide6.QtQuick", "PySide6.QtPdf",
                  "PySide6.QtWebEngineCore", "PySide6.QtOpenGL", "PySide6.QtSvg", "tkinter"):
        cmd += ["--exclude-module", heavy]
    cmd.append(str(HERE / "scr_main.py"))
    subprocess.run(cmd, check=True)
    exe, scr = DIST / f"{NAME}.exe", DIST / f"{NAME}.scr"
    if scr.exists():
        scr.unlink()
    exe.rename(scr)
    print(f"built {scr} ({scr.stat().st_size / 2**20:.1f} MB)")


if __name__ == "__main__":
    make_package()
    gather_sprites()
    icon = make_icon()
    if "--no-exe" not in sys.argv:
        pyinstall(icon)
