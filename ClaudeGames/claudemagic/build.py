"""Build the one-file game: src/index.html with style.css and the js files (in name order) set inside it, written as
game/Claude and Magic v<VERSION>.html - the file the Timeline opens and the one to double-click in a browser. Beside it
go the three small files that make it installable where a server serves the folder (manifest.webmanifest, sw.js,
icon.svg); opened from disk, the game never asks for them.

    python build.py            write it (an older version's file in game/ is removed)
    python build.py --check    say whether the file in game/ matches the source (the tests ask)

Change the source in src/, not the built file; bump VERSION here when a new version is worth a new file name."""
import json
import re
import sys
from urllib.parse import quote
from pathlib import Path

VERSION = "7.3"
HERE = Path(__file__).resolve().parent
SRC = HERE / "src"
GAME = HERE / "game"
NAME = "Claude and Magic v{}.html"


def build_text():
    html = (SRC / "index.html").read_text(encoding="utf-8")
    css = (SRC / "style.css").read_text(encoding="utf-8")
    scripts = []
    for p in sorted((SRC / "js").glob("*.js")):
        scripts.append(f"// ---- {p.name} ----\n" + p.read_text(encoding="utf-8").strip() + "\n")
    html = html.replace("<!-- @css -->", "<style>\n" + css.strip() + "\n</style>")
    html = html.replace("<!-- @js -->", "<script>\n" + "\n".join(scripts) + "</script>")
    return html.replace("__VERSION__", VERSION).replace("__BUILT__", built_stamp())


# the app's papers: a manifest, a service worker that keeps the file for offline, and an icon (an SVG, so no image
# library is needed to write it)
def side_files():
    name = NAME.format(VERSION)
    manifest = json.dumps({
        "name": "Claude and Magic", "short_name": "Claude & Magic", "description": "A first-person dungeon crawler for a party of four, in one file.",
        "start_url": "./" + quote(name), "scope": "./", "display": "standalone", "orientation": "any",
        "background_color": "#18120C", "theme_color": "#1E160E",
        "icons": [{"src": "icon.svg", "sizes": "any", "type": "image/svg+xml", "purpose": "any"}],
    }, indent=2) + "\n"
    sw = f"""// Claude and Magic v{VERSION}: the service worker keeps the game's file so it opens without the network.
const CACHE = "claudemagic-v{VERSION}";
const FILES = ["./{quote(name)}", "./manifest.webmanifest", "./icon.svg"];
self.addEventListener("install", (e) => {{ e.waitUntil(caches.open(CACHE).then((c) => c.addAll(FILES)).then(() => self.skipWaiting())); }});
self.addEventListener("activate", (e) => {{ e.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim())); }});
self.addEventListener("fetch", (e) => {{
  if (e.request.method !== "GET" || new URL(e.request.url).origin !== location.origin) return;
  e.respondWith(caches.match(e.request, {{ ignoreSearch: true }}).then((hit) => hit || fetch(e.request).then((res) => {{
    if (res.ok) caches.open(CACHE).then((c) => c.put(e.request, res.clone()));
    return res;
  }})));
}});
"""
    icon = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<rect width="64" height="64" rx="12" fill="#1E160E"/><rect x="3" y="3" width="58" height="58" rx="10" fill="none" stroke="#8A6A3A" stroke-width="2"/>
<path d="M14 50 L14 18 L22 18 L32 36 L42 18 L50 18 L50 50 L43 50 L43 30 L34 46 L30 46 L21 30 L21 50 Z" fill="#E8C870"/>
<circle cx="32" cy="13" r="3.5" fill="#F0E0B0"/><path d="M32 4 Q35 9 32 12 Q29 9 32 4 Z" fill="#E03030"/>
</svg>
"""
    return {"manifest.webmanifest": manifest, "sw.js": sw, "icon.svg": icon}


def built_stamp():
    """The day the file was built (CM.built: the F3 overlay, Export and bug reports say which build they came from)."""
    import datetime
    return datetime.date.today().isoformat()


def same_but_stamp(a, b):
    """Two builds are the same if they differ only in the day they were built."""
    return re.sub(r'built: "\d{4}-\d\d-\d\d"', 'built: ""', a) == re.sub(r'built: "\d{4}-\d\d-\d\d"', 'built: ""', b)


def built_file():
    """The newest Claude and Magic v*.html in game/ (None if there isn't one)."""
    best = None
    for f in GAME.glob("Claude and Magic v*.html"):
        m = re.search(r"v(\d+(?:\.\d+)*)", f.stem)
        key = tuple(int(x) for x in m.group(1).split(".")) if m else (0,)
        if best is None or key > best[0]:
            best = (key, f)
    return best[1] if best else None


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    text = build_text()
    out = GAME / NAME.format(VERSION)
    if "--check" in argv:
        have = built_file()
        same = have is not None and have.name == out.name and same_but_stamp(have.read_text(encoding="utf-8"), text)
        for fname, body in side_files().items():
            f = GAME / fname
            same = same and f.exists() and f.read_text(encoding="utf-8") == body
        print("up to date" if same else "out of date: run  python build.py  in ClaudeGames/claudemagic")
        return 0 if same else 1
    GAME.mkdir(exist_ok=True)
    for f in GAME.glob("Claude and Magic v*.html"):
        if f.name != out.name:
            f.unlink()
    out.write_text(text, encoding="utf-8")
    for fname, body in side_files().items():
        (GAME / fname).write_text(body, encoding="utf-8")
    print(f"built {out.name} ({out.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
