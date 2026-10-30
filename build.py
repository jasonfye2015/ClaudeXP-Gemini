"""Build the one-file game: src/index.html with style.css and the js files (in name order) set inside it, written as
game/Claude and Magic v<VERSION>.html - the file the Timeline opens and the one to double-click in a browser.

    python build.py            write it (an older version's file in game/ is removed)
    python build.py --check    say whether the file in game/ matches the source (the tests ask)

Change the source in src/, not the built file; bump VERSION here when a new version is worth a new file name."""
import re
import sys
from pathlib import Path

VERSION = "2.6"
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
        print("up to date" if same else "out of date: run  python build.py  in ClaudeGames/claudemagic")
        return 0 if same else 1
    GAME.mkdir(exist_ok=True)
    for f in GAME.glob("Claude and Magic v*.html"):
        if f.name != out.name:
            f.unlink()
    out.write_text(text, encoding="utf-8")
    print(f"built {out.name} ({out.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
