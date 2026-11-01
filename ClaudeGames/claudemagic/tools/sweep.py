"""The floor's sweep (v16.4): opens every table of the Gilded Joker in a real browser engine (Qt WebEngine), at a
normal and a narrow window, plays a few rounds with clicks and keys, and reports script errors, animation loops or
timers left running after leaving, and anything that runs off the window's edge. A screenshot of each table is kept.

    python tools/sweep.py              (every table; needs PySide6 with WebEngine)
    ONLY=slots,pond python tools/sweep.py
The report and pictures go to the system's temp folder, cm_sweep/."""
import json
import time
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QApplication
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView

import tempfile
HERE = Path(tempfile.gettempdir())
OUT = HERE / "cm_sweep"
OUT.mkdir(exist_ok=True)
GAME = sorted((Path(__file__).resolve().parent.parent / "game").glob("Claude and Magic v*.html"))[-1]


CONSOLE = []
class Page(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, msg, line, source):
        lv = str(level).split('.')[-1]
        if "Error" in lv or "Warning" in lv: CONSOLE.append(f"{lv}: {msg} (line {line})")


app = QApplication([])
profile = QWebEngineProfile("cm-sweep", app)
store = HERE / "cm_sweep_profile"
store.mkdir(exist_ok=True)
profile.setPersistentStoragePath(str(store / "storage"))
profile.setCachePath(str(store / "cache"))
view = QWebEngineView()
page = Page(profile, view)
page.settings().setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
page.settings().setAttribute(QWebEngineSettings.PlaybackRequiresUserGesture, False)
view.setPage(page)
view.resize(1180, 800)
view.show()
loaded = []
view.loadFinished.connect(lambda ok: loaded.append(ok))
view.load(QUrl.fromLocalFile(str(GAME)))


def pump(seconds):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        app.processEvents()
        time.sleep(0.005)


def js(code, timeout=15):
    box = []
    page.runJavaScript("(function(){ try { return JSON.stringify({v: (" + code + ")}); } catch (e) { return JSON.stringify({error: String(e && e.stack || e)}); } })()",
                       lambda r: box.append(r))
    end = time.monotonic() + timeout
    while not box and time.monotonic() < end:
        app.processEvents()
        time.sleep(0.005)
    got = json.loads(box[0]) if box and box[0] else {"error": "no answer"}
    if "error" in got:
        print("JS ERROR:", got["error"], flush=True)
    return got.get("v")


def run(code):
    return js("(function(){ " + code + "; return true; })()")


def shot(name, wait=0.7):
    pump(wait)
    view.grab().save(str(OUT / f"{name}.png"))
    print("shot", name, flush=True)


def look(name):
    run(f"const s = document.querySelector('#look'); if (s) {{ s.value = '{name}'; s.dispatchEvent(new Event('change')); }}")
    pump(0.5)


def stand(x, y, facing):
    run(f"const g = CM.game; g.floor.pos = [{x}, {y}]; g.floor.facing = {facing}; g.look(); g.emit('floor', g.floor); g.emit('change')")



import sys
SIZES = [(1180, 800), (820, 640)]
while not loaded:
    app.processEvents(); time.sleep(0.01)
pump(1.0)
while not js("CM.art.packs.ready"):
    pump(0.1)
run("const g = CM.game; g.newGame('sweep-55', null, undefined, undefined, undefined, undefined, { town: true }); CM.ui.closeDialogs(); if (CM.ui.leaveSplash) CM.ui.leaveSplash(); g.startCombat = () => {}")
run("""window.__errs = []; window.addEventListener('error', (e) => __errs.push(String(e.message) + ' @' + e.lineno)); window.addEventListener('unhandledrejection', (e) => __errs.push('promise: ' + (e.reason && e.reason.stack || e.reason)));
  const raf = window.requestAnimationFrame.bind(window); window.__raf = 0; window.requestAnimationFrame = (f) => { window.__raf++; return raf(f); };
  const si = window.setInterval.bind(window), ci = window.clearInterval.bind(window); window.__iv = new Set(); window.setInterval = (f, t, ...a) => { const id = si(f, t, ...a); __iv.add(id); return id; }; window.clearInterval = (id) => { __iv.delete(id); ci(id); };""")
run("const g = CM.game; g.gold = 50000; g.tkStore().n = 5000; CM.ui.cgOpenTo = 'gallery'; CM.ui.openCasino()"); pump(1.0)
def rate():
    a = js("window.__raf"); pump(1.0); return js("window.__raf") - a
base = rate(); ivs0 = js("__iv.size")
print("baseline rAF/s", base, "intervals", ivs0, flush=True)
ids = js("CM.CG_TABLES.map(([k, n]) => [k, n])")
import os
ONLY = [x for x in os.environ.get("ONLY", "").split(",") if x]
if ONLY: ids = [r for r in ids if r[0] in ONLY]
report = []
OVER = """(() => { const b = document.querySelector('#casino-body'), R = b.getBoundingClientRect(), out = [];
  for (const e of b.querySelectorAll('*')) { const r = e.getBoundingClientRect(); if (r.width > 0 && r.height > 0 && (r.right > R.right + 3 || r.left < R.left - 3) && getComputedStyle(e).position !== 'fixed') out.push(e.tagName.toLowerCase() + (e.className && typeof e.className === 'string' ? '.' + e.className.split(' ')[0] : '') + ' ' + Math.round(r.right - R.right)); }
  return { sw: b.scrollWidth - b.clientWidth, list: out.slice(0, 4) }; })()"""
PLAY = """(() => { const b = document.querySelector('#casino-body'); const skip = /leave|all games|settle|sell all|cash out|get up|clear|let it go|buy .*pass/i;
  const btn = [...b.querySelectorAll('button')].find((x) => !x.disabled && x.classList.contains('primary') && !skip.test(x.textContent) && !x.closest('.cgnav') && !x.closest('.cgcats'));
  if (btn) { btn.click(); return btn.textContent.trim().slice(0, 40); } return ''; })()"""
POKE = """(() => { const c = document.querySelector('#casino-body canvas:not([data-cgthumb])'); if (!c) return false; const r = c.getBoundingClientRect(), x = r.left + r.width / 2, y = r.top + r.height * 0.6;
  for (const t of ['mousemove', 'mousedown']) c.dispatchEvent(new MouseEvent(t, { clientX: x, clientY: y, bubbles: true })); setTimeout(() => c.dispatchEvent(new MouseEvent('mouseup', { clientX: x, clientY: y, bubbles: true })), 450); c.dispatchEvent(new MouseEvent('click', { clientX: x, clientY: y, bubbles: true }));
  for (const k of ['Space', 'ArrowLeft', 'ArrowRight', 'ArrowUp', 'Enter']) { window.dispatchEvent(new KeyboardEvent('keydown', { code: k, key: k === 'Space' ? ' ' : k, bubbles: true })); window.dispatchEvent(new KeyboardEvent('keyup', { code: k, key: k === 'Space' ? ' ' : k, bubbles: true })); } return true; })()"""
for (tid, name) in ids:
    CONSOLE.clear(); run("__errs.length = 0")
    run(f"CM.ui.cgBusy = false; CM.ui.cgNote = ''; CM.ui.cgView = '{tid}'; CM.ui.renderCasino()"); pump(1.0)
    view.grab().save(str(OUT / f"{tid}.png"))
    over = {}
    for (w, h) in SIZES:
        view.resize(w, h); pump(0.5); over[f"{w}"] = js(OVER)
    view.resize(*SIZES[0]); pump(0.3)
    clicks = []
    for k in range(3):
        c = js(PLAY); clicks.append(c); js(POKE); pump(1.6)
    view.grab().save(str(OUT / f"{tid}-played.png"))
    gold = js("CM.game.gold")
    run("CM.ui.cgBusy = false; CM.ui.cgView = 'gallery'; CM.ui.renderCasino()"); pump(1.2)
    r = rate(); ivs = js("__iv.size")
    errs = js("__errs.slice()") + [c for c in CONSOLE if "Error" in c]
    row = {"id": tid, "name": name, "errors": errs[:5], "raf": r, "intervals": ivs, "over": over, "clicks": clicks, "gold": gold}
    flag = []
    if errs: flag.append("ERR")
    if r > base + 25: flag.append(f"LOOP+{r - base}")
    if ivs > ivs0: flag.append(f"IV+{ivs - ivs0}")
    for w, o in over.items():
        if o and (o["sw"] > 2 or o["list"]): flag.append(f"OVER{w}")
    row["flags"] = flag; report.append(row)
    print(f"{tid:12s} {' '.join(flag) or 'ok':30s} clicks={clicks}", flush=True)
    if r > base + 25: base = r   # (count each leak once)
    ivs0 = max(ivs0, ivs)
(OUT / "report.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
print("done", len(report), flush=True)
app.quit()
