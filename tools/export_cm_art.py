"""Export Claude and Magic's painted art - the pictures it draws in code as it starts (its ten themes' walls, floors,
ceilings and water; the wall dressings: pipe mouths, grates, drain ports, webs, moss, roots, chains, sconces,
banners; the overheads; furniture, landmarks and the set pieces' things) - and its set-piece rooms, from the
Timeline's copy of the game running in Qt WebEngine, into assets/cm/. Run it when Claude and Magic's art changes:

    python tools/export_cm_art.py          (with the Timeline's Python; takes a minute or two)

The game runs on a scratch browser profile: its real saves are never opened."""
import base64
import json
import re
import sys
import tempfile
import time
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QApplication
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
from PySide6.QtWebEngineWidgets import QWebEngineView

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "assets" / "cm"
GAME_DIR = ROOT.parents[0] / "claudemagic" / "game"
PER_THEME = ["wall", "wall2", "wallbones", "floor", "ceiling", "water0", "torch0"]
SHARED_PREFIX = ["decal:", "over:", "clut:", "fu:", "lm:", "ce:", "dl:", "dk:", "mood:", "st:drip"]
SHARED = ["chest", "door", "door_open", "gate", "altar", "fountain", "fountain_dry", "carving", "nest", "throne", "anvil",
          "ember", "fungus", "crystal", "root", "bones", "brazier", "brazier_down", "pit", "trapdoor", "lever", "rope",
          "halo", "lamppool"] + ["sp:" + n for n in (
              "crystal cocoon eggsac cage coffin altar fire coldfire slab mural nest table desk orrery bell hourglass mirror "
              "carving plaque seastone coins ice hook blade lever scale spider meat egg die").split()]
SKIP = ("curio", "claude:", "margin", "redink", "edition")


def newest():
    best = None
    for f in GAME_DIR.glob("Claude and Magic v*.html"):
        key = tuple(int(x) for x in re.search(r"v(\d+(?:\.\d+)*)", f.stem).group(1).split("."))
        if best is None or key > best[0]:
            best = (key, f)
    return best[1]


def main():
    app = QApplication(sys.argv[:1])
    scratch = Path(tempfile.mkdtemp(prefix="nites-cmart-"))
    profile = QWebEngineProfile("nites-export", app)
    profile.setPersistentStoragePath(str(scratch / "storage"))
    profile.setCachePath(str(scratch / "cache"))
    view = QWebEngineView()
    page = QWebEnginePage(profile, view)
    view.setPage(page)
    view.resize(900, 640)
    view.show()
    view.load(QUrl.fromLocalFile(str(newest())))

    def pump(s):
        end = time.monotonic() + s
        while time.monotonic() < end:
            app.processEvents()
            time.sleep(0.005)

    def js(code, timeout=180):
        box = []
        page.runJavaScript(code, lambda r: box.append(r))
        end = time.monotonic() + timeout
        while not box and time.monotonic() < end:
            app.processEvents()
            time.sleep(0.005)
        return box[0] if box else None

    pump(4)
    for _ in range(180):
        if js("typeof CM !== 'undefined' && !!CM.art && !!CM.THEMES && !!CM.game && !!CM.SETPIECES", 10):
            break
        pump(1)
    DEST.mkdir(parents=True, exist_ok=True)
    code = """(function(T, names, prefixes){ const b = CM.art.build(CM.THEMES[T], 'drawn'); const out = {};
      for (const n of Object.keys(b.index)) { if (!(names.includes(n) || prefixes.some(p => n.startsWith(p)))) continue;
        out[n] = b.layers[b.index[n]].toDataURL('image/png'); } return JSON.stringify(out); })(%d, %s, %s)"""
    for T in range(10):
        got = json.loads(js(code % (T, json.dumps(PER_THEME + (SHARED if T == 0 else [])),
                                    json.dumps(SHARED_PREFIX if T == 0 else []))))
        for n, url in got.items():
            if not any(n.startswith(s) for s in SKIP):
                fn = (f"t{T}." if n in PER_THEME else "") + n.replace(":", ".") + ".png"
                (DEST / fn).write_bytes(base64.b64decode(url.split(",", 1)[1]))
        print("theme", T, len(got), flush=True)
    rooms = js("JSON.stringify(CM.SETPIECES.map(s => { const o = {}; for (const k of Object.keys(s)) "
               "if (typeof s[k] !== 'function' && k[0] !== '_') o[k] = s[k]; return o; }))", 60)
    (DEST / "setpieces.json").write_text(rooms, encoding="utf-8")
    print("set pieces", len(json.loads(rooms)))
    app.quit()


if __name__ == "__main__":
    main()
