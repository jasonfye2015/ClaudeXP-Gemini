"""Every program in the Timeline, read from the three computers' registries, written as Manual/15-programs.md.

    python -m manual.catalog [--out PATH]

The registries are read as source (Python's ast), not imported, so this needs no Qt and touches no computer's data:
ClaudeXP's Program(...) list and its static tables (the emulators, the id shooters, the folder shortcuts, the
Projects), Claude7's and Claude11's DROPPED / RENAMED / REGROUPED and their own programs. The one-line descriptions
come from XP's Help and Support catalog (helpctr_guide.CATALOG) where it has one, else from the Start menu blurb.
Rerun it when programs are added or renamed; the self-check reads the same lines, so a name it rejects won't get in."""
import argparse
import ast
import time
from pathlib import Path

TIMELINE = Path(__file__).resolve().parents[2]
XP = TIMELINE / "ClaudeXP" / "claudexp" / "programs" / "__init__.py"
GUIDE = TIMELINE / "ClaudeXP" / "claudexp" / "programs" / "helpctr_guide.py"
W7 = TIMELINE / "Claude7" / "claude7" / "programs" / "__init__.py"
W11 = TIMELINE / "Claude11" / "claude11" / "programs" / "__init__.py"
PROJECTS = TIMELINE / "ClaudeApps" / "projects" / "__init__.py"
OUT = TIMELINE / "Manual" / "15-programs.md"

# a Start menu group -> a section of the catalog, for programs the Help catalog doesn't place
GROUP_SECTION = {"Social Programs": "talk", "Furry Stuff": "furry", "Projects": "projects", "Games": "games",
                 "Games/Windows Games": "games", "Games/Game Emulation": "emu", "Gemini Office": "office",
                 "GeminiAdobe": "office", "Accessories/Entertainment": "media", "Accessories/System Tools": "system",
                 "Accessories": "system", "ClaudeAmp": "media", "Real": "media", "QuickTime": "media",
                 "Kiwix": "web", "ClaudeTorrent": "web", "Nero": "system", "Alcohol 120%": "system", "WinRAR": "system",
                 "WinZip": "system", "Lavasoft Ad-aware 5.6": "system", "StyleXP": "system"}
KEY_SECTION = {"claudeai": "ai", "kithylinai": "ai", "copilotai": "ai", "copilotvoice": "ai", "imagecreator": "ai",
               "pystudio": "ai", "copilotwidgets": "ai", "neko": "ai", "clippy": "ai", "manual": "other",
               "backup": "system", "tv": "media", "tvguide": "media", "wmp": "media", "moviemaker": "office",
               "flash": "media", "paint": "office", "notepad": "office", "wordpad": "office", "calc": "system",
               "mycomputer": "system", "winupdate": "system", "antivirus": "system", "defrag": "system",
               "connect": "web", "dsl": "web", "activate": "system", "tour": "system", "search": "system",
               "helpctr": "system", "arp": "system", "taskmgr": "system", "sndvol": "media", "sndrec": "media",
               "firefox": "web", "settings": "system", "controlpanel": "system", "gadgets": "system",
               "widgets": "system", "stickynotes": "office", "snipping": "office", "chess": "games"}
EMPTY = {"games": "One of Windows' own games", "system": "A Windows tool", "office": "A Windows accessory"}


def _assign(tree, name):
    """The value of a top-level `name = <literal>` in the module."""
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            try:
                return ast.literal_eval(node.value)
            except ValueError:
                return None
    return None


def _str(node, names):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name):
        return names.get(node.id, "")
    return ""


def _programs(tree, names):
    """[(key, name, blurb, group, listed)] from every Program("key", "name", "blurb", ..., group=..) call with
    literal arguments."""
    out = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "Program"):
            continue
        if len(node.args) < 3 or not all(isinstance(a, ast.Constant) for a in node.args[:2]):
            continue
        key, name = node.args[0].value, node.args[1].value
        blurb = _str(node.args[2], names)
        group = ""
        listed = True
        for kw in node.keywords:
            if kw.arg == "group":
                group = _str(kw.value, names)
            elif kw.arg == "listed" and isinstance(kw.value, ast.Constant):
                listed = bool(kw.value.value)
        out.append((key, name, blurb, group, listed))
    return out


def xp_programs():
    tree = ast.parse(XP.read_text(encoding="utf-8"))
    furry = _assign(tree, "FURRY") or "Furry Stuff"
    names = {"FURRY": furry}
    progs = _programs(tree, names)
    for key, name, blurb in _assign(tree, "DOOM_GAMES") or []:
        progs.append((key, name, blurb, "Games", True))
    for key, name, blurb in _assign(tree, "EMULATORS") or []:
        progs.append((key, name, blurb, "Games/Game Emulation", True))
    groups = _assign(tree, "SHORTCUT_GROUPS") or {}
    for key, (label, _prefix) in (_assign(tree, "FOLDER_SHORTCUTS") or {}).items():
        progs.append((key, label, "A shortcut to that folder on drive E:", groups.get(key, furry), True))
    ptree = ast.parse(PROJECTS.read_text(encoding="utf-8"))
    for key, (name, blurb, *_rest) in (_assign(ptree, "PROJECTS") or {}).items():
        progs.append((key, name, blurb, "Projects", True))
    return progs


def era_programs(path, xp):
    """That computer's registry: XP's with its DROPPED / RENAMED / REGROUPED applied, plus its own programs."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    dropped = _assign(tree, "DROPPED") or set()
    renamed = _assign(tree, "RENAMED") or {}
    regrouped = _assign(tree, "REGROUPED") or {}
    out = {}
    for key, name, blurb, group, listed in xp:
        if key in dropped:
            continue
        name, blurb = renamed.get(key, (name, blurb))
        out[key] = (name, blurb, regrouped.get(key, group), listed)
    for key, name, blurb, group, listed in _programs(tree, {}):
        out[key] = (name, blurb, group, listed)
    return out


def guide():
    tree = ast.parse(GUIDE.read_text(encoding="utf-8"))
    return _assign(tree, "SECTIONS") or [], _assign(tree, "CATALOG") or {}


def write(out):
    xp = xp_programs()
    w7 = era_programs(W7, xp)
    w11 = era_programs(W11, xp)
    sections, catalog = guide()
    ids = [s[0] for s in sections]
    rows = {sid: [] for sid in ids}
    seen = set()

    def place(key, name, blurb, group):
        sid = catalog.get(key, (None,))[0] or KEY_SECTION.get(key) or GROUP_SECTION.get(group) or "other"
        if sid not in rows:
            sid = "other"
        what = catalog.get(key, (None, ""))[1] or blurb
        rows[sid].append((name, what, key))

    for key, name, blurb, group, listed in xp:
        if not listed or key in seen:
            continue
        seen.add(key)
        place(key, name, blurb, group)
    for era in (w7, w11):                        # programs only a later computer has
        for key, (name, blurb, group, listed) in era.items():
            if listed and key not in seen:
                seen.add(key)
                place(key, name, blurb, group)
    xp_by = {k: n for k, n, _b, _g, _l in xp}

    def cell(era, key, xp_name):
        if key not in era:
            return "-"
        name = era[key][0]
        return "yes" if name == xp_name else f"as *{name}*"

    total = len(seen)
    lines = ["# 15. Every program", "",
             f"Read from the three computers' registries on {time.strftime('%d %B %Y')}: {total} programs in all, "
             f"{sum(1 for k, _n, _b, _g, l in xp if l)} on EPOCH-2001, {sum(1 for v in w7.values() if v[3])} on "
             f"SYSTEM-2011 and {sum(1 for v in w11.values() if v[3])} on WORKSTATION-2025. A program is on every "
             "computer unless an era dropped it (a service that closed) or renamed it (the same program in that year's "
             "clothes). The sections are the ones XP's Help and Support uses. Regenerate with "
             "`python -m manual.catalog` from `ClaudeApps` after adding or renaming a program.", ""]
    for sid, title, intro in sections:
        if not rows[sid]:
            continue
        lines += [f"## {title}", ""]
        if intro:
            lines += [intro, ""]
        lines += ["| Program | What it is | 2001 | 2011 | 2025 |", "|---|---|:-:|:-:|:-:|"]
        for name, what, key in sorted(rows[sid], key=lambda r: r[0].lower()):
            on_xp = "yes" if key in xp_by else "-"
            if key not in xp_by:                 # a later computer's own program
                name = w7.get(key, w11.get(key))[0]
            what = (what or EMPTY.get(sid, "")).replace("|", "/").replace("\n", " ")
            lines.append(f"| **{name}** | {what} | {on_xp} | {cell(w7, key, name)} | {cell(w11, key, name)} |")
        lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")
    return total


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args(argv)
    n = write(args.out)
    print(f"{n} programs -> {args.out}")


if __name__ == "__main__":
    main()
