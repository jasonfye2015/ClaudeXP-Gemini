"""The TV archive on the external drive (E:): finds 'Movies...', 'TV Series.../<Show>' and '...Commercials...'
folders anywhere under Local Storage, reads each video's running time from its header (cached in data/, nothing is
written into the archive), and matches files to TV Guide details (assets/tvguide/shows.txt, plus a show's own
episode-guide .txt when the archive has one)."""
import json
import os
import re
import struct
import unicodedata
from pathlib import Path

from ...paths import DATA, ROOT

VIDEO_EXTS = {".avi", ".mp4", ".mkv", ".mov", ".m4v", ".mpg", ".mpeg"}
INDEX_FILE = DATA / "tv_index.json"
GUIDE_FILE = ROOT / "assets" / "tvguide" / "shows.txt"
PROMO_MAX_SECS = 180            # extras shorter than this air as promos between shows
SKIP = re.compile(r"kablam", re.I)          # release-group adverts that came with some files


class Media:
    __slots__ = ("path", "kind", "show", "show_key", "season", "episode", "title", "secs", "desc", "aired",
                 "year", "rating")

    def __init__(self, path, kind, secs, **kw):
        self.path, self.kind, self.secs = path, kind, secs
        for k in self.__slots__:
            if k not in ("path", "kind", "secs"):
                setattr(self, k, kw.get(k, ""))

    def label(self):
        """The guide title: 'Show: Episode' or the movie title."""
        if self.kind in ("episode", "special") and self.show:
            if not self.title:
                return self.show
            return self.title if norm(self.title).startswith(norm(self.show)) else f"{self.show}: {self.title}"
        return self.title


def norm(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()      # Svën Höek -> Sven Hoek
    return re.sub(r"[^a-z0-9]+", " ", text.lower().replace("&", " and ")).strip()


# ---- running times from headers ---------------------------------------------------------------------------

def _avi(f):
    d = f.read(4096)
    i = d.find(b"avih")
    if i < 0:
        return None
    usec, _a, _b, _c, frames = struct.unpack("<5I", d[i + 8:i + 28])
    j = d.find(b"dmlh")                     # OpenDML (over 1 GB): avih only counts the first RIFF chunk
    if j >= 0:
        frames = max(frames, struct.unpack("<I", d[j + 8:j + 12])[0])
    return usec * frames / 1e6 if usec and frames else None


def _mvhd(f, size):
    pos = 0
    while pos < size:
        f.seek(pos)
        hdr = f.read(16)
        if len(hdr) < 8:
            return None
        n, kind = struct.unpack(">I4s", hdr[:8])
        if n == 1:
            n = struct.unpack(">Q", hdr[8:16])[0]
        if n == 0:
            n = size - pos
        if n < 8:
            return None
        if kind == b"moov":
            f.seek(pos)
            data = f.read(min(n, 4 * 2 ** 20))
            j = data.find(b"mvhd")
            if j < 0:
                return None
            if data[j + 4] == 1:
                scale, dur = struct.unpack(">IQ", data[j + 24:j + 36])
            else:
                scale, dur = struct.unpack(">II", data[j + 16:j + 24])
            return dur / scale if scale else None
        pos += n
    return None


def _mkv(f):
    d = f.read(2 * 2 ** 20)
    scale = 1_000_000
    m = re.search(rb"\x2a\xd7\xb1(.)", d, re.S)
    if m:
        ln = m.group(1)[0] & 0x7F
        scale = int.from_bytes(d[m.end():m.end() + ln], "big") or scale
    m = re.search(rb"\x44\x89\x88(.{8})|\x44\x89\x84(.{4})", d, re.S)
    if not m:
        return None
    val = struct.unpack(">d", m.group(1))[0] if m.group(1) else struct.unpack(">f", m.group(2))[0]
    return val * scale / 1e9


def running_time(path):
    ext = path.suffix.lower()
    try:
        with open(path, "rb") as f:
            if ext == ".avi":
                return _avi(f)
            if ext == ".mkv":
                return _mkv(f)
            if ext in (".mp4", ".mov", ".m4v"):
                return _mvhd(f, path.stat().st_size)
    except (OSError, struct.error, ValueError):
        pass
    return None


# ---- guide data -------------------------------------------------------------------------------------------------

def load_guide():
    """{'MOVIE': [...], 'SHOW': {key: (title, desc)}, 'EP': {(key, 'S1E2'): (...)}, 'TITLE': {(key, norm): (...)}}"""
    g = {"MOVIE": [], "SHOW": {}, "EP": {}, "TITLE": {}}
    try:
        lines = GUIDE_FILE.read_text(encoding="utf-8").splitlines()
    except OSError:
        return g
    for line in lines:
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split("|")
        key = parts[0]
        if key == "MOVIE" and len(parts) >= 5:
            g["MOVIE"].append({"title": parts[1], "year": parts[2], "rating": parts[3], "desc": parts[4]})
        elif len(parts) >= 5 and parts[1] == "SHOW":
            g["SHOW"][key] = (parts[2], parts[4])
        elif len(parts) >= 5:
            entry = {"title": parts[2], "aired": parts[3], "desc": parts[4]}
            if re.fullmatch(r"S\d+E\d+", parts[1]):
                g["EP"][(key, parts[1])] = entry
            g["TITLE"][(key, norm(parts[2]))] = entry
    return g


def read_episode_guide(folder):
    """A show's own episode guide .txt ('1. Title [1]' / 'First aired: ...' / description) -> {norm title: entry}."""
    out = {}
    for txt in Path(folder).glob("*Episode Guide*.txt"):
        try:
            lines = txt.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        current = None
        for line in lines:
            m = re.match(r"\s*\d+\.\s+(.+?)\s*\[\d+\]\s*$", line)
            if m:
                current = {"title": m.group(1), "aired": "", "desc": ""}
                out[norm(m.group(1))] = current
            elif current is not None:
                if line.startswith("First aired:"):
                    current["aired"] = line.split(":", 1)[1].strip()
                elif line.startswith(("Writer", "Director", "Guest", "*")):
                    continue
                elif line.strip() and not current["desc"]:
                    current["desc"] = line.strip()
    return out


SHOW_KEYS = [("aqua teen", "ATHF"), ("ren and stimpy", "REN"), ("ren stimpy", "REN"), ("mongrels", "MONGRELS")]


def show_key(name):
    n = norm(name)
    return next((k for kw, k in SHOW_KEYS if kw in n), n.upper()[:20])


def _clean_title(stem):
    t = re.sub(r"[\[(][^\])]*[\])]", " ", stem)                       # [2001], (Nick Version)
    t = re.sub(r"\b(xvid|divx|dvdrip|hdtv|pdtv|ws|x264|yify|bluray|720p|1080p|axxo|riv|mot)\b.*", " ", t, flags=re.I)
    return re.sub(r"[._]+", " ", t).strip(" -")


def _episode_info(stem):
    """(season, episode, title) from 'S03E05 - eDork', '1e01a-Stimpy's Big Day', 'Mongrels.s01e02...Title'."""
    m = re.search(r"[sS](\d+)[eE](\d+)(?:\s*-\s*(.+))?", stem)
    if m:
        title = m.group(3) or ""
        if not title:
            rest = stem[m.end():]
            rest = re.sub(r"^[._]*(?:ws[._])?(?:pdtv[._]|hdtv[._])?xvid-[a-z0-9]+[._]", "", rest, flags=re.I)
            title = rest
        return int(m.group(1)), int(m.group(2)), re.sub(r"[._]+", " ", title).strip(" -")
    m = re.match(r"(\d+)e(\d+)([ab]?)-(.+)", stem)
    if m:
        return int(m.group(1)), int(m.group(2)), re.sub(r"\s*\(.*?\)\s*", " ", m.group(4)).strip()
    return None, None, _clean_title(stem)


def _match_title(title, titles):
    """The guide entry whose title is closest to a file's ({norm title: entry}); None if nothing is close."""
    import difflib
    t = re.sub(r"^(a|the)\s+|\s+part\s+\d+$", "", norm(re.sub(r"^[ab]\s*-\s*", "", title)))
    if not t:
        return None
    if t in titles:
        return titles[t]
    best, score = None, 0.0
    for tt, v in titles.items():
        u = re.sub(r"^(a|the)\s+", "", tt)
        s = 1.0 if (u.startswith(t) or t.startswith(u)) and min(len(t), len(u)) >= 6 else             difflib.SequenceMatcher(None, t, u).ratio()
        if s > score:
            best, score = v, s
    return best if score >= 0.8 else None


def _match_movie(stem, movies):
    words = set(norm(_clean_title(stem)).split())
    year = re.search(r"(19|20)\d\d", stem)
    best, score = None, 0.0
    for m in movies:
        t = [w for w in norm(m["title"].replace("(RiffTrax)", "")).split() if w not in ("the", "of")]
        if not t:
            continue
        s = sum(w in words for w in t) / len(t) + (0.3 if year and year.group(0) == m["year"] else 0)
        if s > score:
            best, score = m, s
    return best if score >= 0.75 else None


# ---- scanning -------------------------------------------------------------------------------------------------

def find_roots(base):
    """{'movies': [...], 'tv': [...], 'ads': [...]} folders under base (up to 3 levels deep)."""
    roots = {"movies": [], "tv": [], "ads": []}
    base = Path(base)
    if not base.exists():
        return roots
    for folder, dirs, _files in os.walk(base):
        depth = Path(folder).relative_to(base).parts
        if len(depth) > 3:
            dirs[:] = []
            continue
        for d in list(dirs):
            n = d.lower()
            path = Path(folder) / d
            if n.startswith("movies"):
                roots["movies"].append(path)
                dirs.remove(d)
            elif n.startswith(("tv series", "tv shows")):
                roots["tv"].append(path)
                dirs.remove(d)
            elif "commercial" in n or n.startswith(("ads", "adverts")):
                roots["ads"].append(path)
                dirs.remove(d)
    return roots


def scan(base, progress=None):
    """Every playable video in the archive as Media, with running times (cached) and guide details."""
    cache = {}
    try:
        cache = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    fresh = {}
    guide = load_guide()
    roots = find_roots(base)
    out = []

    def secs_for(p):
        st = p.stat()
        key = str(p)
        hit = cache.get(key)
        if hit and hit[0] == st.st_size and hit[1] == int(st.st_mtime):
            fresh[key] = hit
            return hit[2]
        secs = running_time(p)
        fresh[key] = [st.st_size, int(st.st_mtime), secs]
        if progress:
            progress(p.name)
        return secs

    def videos(folder):
        for dirpath, _d, files in os.walk(folder):
            for name in sorted(files):
                p = Path(dirpath) / name
                if p.suffix.lower() in VIDEO_EXTS and not SKIP.search(name):
                    yield p

    for root in roots["movies"]:
        for p in videos(root):
            secs = secs_for(p)
            if not secs:
                continue
            m = _match_movie(p.stem, guide["MOVIE"])
            if m:
                out.append(Media(p, "movie", secs, title=m["title"], year=m["year"], rating=m["rating"], desc=m["desc"]))
            else:
                out.append(Media(p, "movie", secs, title=_clean_title(p.stem)))
    for root in roots["tv"]:
        for show_dir in sorted(d for d in root.iterdir() if d.is_dir()):
            key = show_key(show_dir.name)
            show_title = guide["SHOW"].get(key, (re.sub(r"\s*[-(].*$", "", show_dir.name).strip(), ""))[0]
            own = read_episode_guide(show_dir)
            for p in videos(show_dir):
                secs = secs_for(p)
                if not secs:
                    continue
                season, episode, title = _episode_info(p.stem)
                extra = "extra" in norm(str(p.relative_to(show_dir))) or "deleted scene" in norm(p.stem) \
                    or "promo" in norm(p.stem)
                if extra and secs < PROMO_MAX_SECS:
                    title = re.sub(r"^.*?(extras|deleted scene)\s*-\s*", "", title, flags=re.I)
                    out.append(Media(p, "promo", secs, show=show_title, show_key=key, title=title))
                    continue
                info = None
                if season and episode:
                    info = guide["EP"].get((key, f"S{season}E{episode}"))
                if info is None:
                    titles = dict(own)
                    titles.update((tt, v) for (k, tt), v in guide["TITLE"].items() if k == key)
                    info = _match_title(title, titles)
                if extra:
                    title = re.sub(r"^.*?(extras|deleted scene)\s*-\s*", "", title, flags=re.I)
                out.append(Media(p, "special" if extra else "episode", secs, show=show_title, show_key=key,
                                 season=season or "", episode=episode or "",
                                 title=(info or {}).get("title") or title, desc=(info or {}).get("desc", ""),
                                 aired=(info or {}).get("aired", "")))
    for root in roots["ads"]:
        for p in videos(root):
            secs = secs_for(p)
            if not secs:
                continue
            m = re.match(r"((?:19|20)\d\d)\s+(.+)", p.stem)
            title = m.group(2) if m else p.stem
            title = re.sub(r"\s*(full\s+)?(commercial|ad|promo)\s*$", "", title, flags=re.I).strip() or title
            out.append(Media(p, "ad", secs, title=title, year=m.group(1) if m else ""))
    try:
        INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
        INDEX_FILE.write_text(json.dumps(fresh), encoding="utf-8")
    except OSError:
        pass
    return out
