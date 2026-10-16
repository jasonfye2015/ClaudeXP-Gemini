"""The HTML rips, served as they were saved: YiffStar, SexyFur and Club Stripes.

Rippers saved 'page.php?x=1' as files like 'page.php¿x=1.html' (YiffStar), 'page.php@x=1' (Club Stripes) or plain
'page.html', and cut long names short; resolve() finds the file a link means, whichever way it was saved."""
import os
from pathlib import Path
from urllib.parse import unquote

from . import Site, file_response

QUERY_MARKS = ("¿", "@", "?", "%3F")


def _entries(folder, cache={}):
    """{lower-case name: real name} for a folder (cached; the rips don't change while ClaudeXP runs)."""
    key = str(folder)
    if key not in cache:
        try:
            cache[key] = {n.lower(): n for n in os.listdir(folder)}
        except OSError:
            cache[key] = {}
    return cache[key]


def resolve(root, path, query, index=("index.html", "index.htm", "index.php", "home.html", "default.htm")):
    """The file in root that 'path?query' means, or None."""
    parts = [p for p in unquote(path).split("/") if p and p not in (".", "..")]
    folder = Path(root)
    for part in parts[:-1]:
        name = _entries(folder).get(part.lower())
        if name is None:
            return None
        folder = folder / name
    last = parts[-1] if parts else ""
    if not last or (folder / last).is_dir() and not query:
        if last:
            folder = folder / _entries(folder).get(last.lower(), last)
        names = _entries(folder)
        for i in index:
            if i in names and (folder / names[i]).is_file():
                return folder / names[i]
        return None
    names = _entries(folder)
    candidates = [last]
    if query:
        q = unquote(query)
        candidates = [last + m + q for m in QUERY_MARKS] + [last]
    for c in candidates:
        for variant in (c, c + ".html", c + ".htm"):
            real = names.get(variant.lower())
            if real and (folder / real).is_file():
                return folder / real
    if query:                                   # the ripper cut long names short: the longest saved prefix
        best = None
        for c in candidates[:-1]:
            low = c.lower()
            for n_low, real in names.items():
                stem = n_low[:-5] if n_low.endswith(".html") else n_low
                if len(stem) >= len(last) + 4 and low.startswith(stem) and (best is None or len(stem) > len(best[0])):
                    best = (stem, real)
        if best:
            return folder / best[1]
    return None


class StaticSite(Site):
    index = ("index.html", "index.htm", "index.php", "home.html", "default.htm")

    def handle(self, path, query):
        root = self.root()
        target = resolve(root, path, query, self.index)
        return file_response(target) if target is not None else None


class YiffStar(StaticSite):
    host, aliases, folder = "www.yiffstar.com", ("yiffstar.net",), "YiffStar"
    title, blurb = "YiffStar", "furry stories and authors"
    index = ("index.php", "index.html")


class SexyFur(StaticSite):
    host, folder = "www.sexyfur.com", "SexyFur"
    title, blurb = "SexyFur", "furry art galleries"


class ClubStripes(StaticSite):
    host, aliases, folder = "www.clubstripes.com", ("clubstripes.net",), "clubstripes"
    title, blurb = "Club Stripes", "Marty's comics, galleries and fiction"
    index = ("home.html", "index.html")
