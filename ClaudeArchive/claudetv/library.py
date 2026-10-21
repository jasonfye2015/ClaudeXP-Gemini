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
from claudecore import host


VIDEO_EXTS = {".avi", ".mp4", ".mkv", ".mov", ".m4v", ".mpg", ".mpeg"}
INDEX_FILE = host.data("claudetv") / "tv_index.json"     # this computer's scan of the archive
GUIDE_FILE = Path(__file__).resolve().parent / "assets" / "shows.txt"
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
    for m in re.finditer(rb"\x2a\xd7\xb1([\x81-\x88])", d[:256 * 1024]):     # TimecodeScale (1-8 bytes)
        ln = m.group(1)[0] & 0x7F
        value = int.from_bytes(d[m.end():m.end() + ln], "big")
        if 1_000 <= value <= 1_000_000_000:             # a real one; the bytes also occur by chance in video
            scale = value
            break
    for m in re.finditer(rb"\x44\x89\x88(.{8})|\x44\x89\x84(.{4})", d, re.S):
        val = struct.unpack(">d", m.group(1))[0] if m.group(1) else struct.unpack(">f", m.group(2))[0]
        secs = val * scale / 1e9
        if 1 <= secs <= 12 * 3600:          # the same bytes can turn up by chance before the real Duration
            return secs
    return None


def _scr(b):
    """System clock (90 kHz) from the bytes after an MPEG pack start code."""
    if len(b) < 5:
        return None
    if b[0] >> 6 == 1:                                     # MPEG-2
        return ((b[0] >> 3) & 7) << 30 | (b[0] & 3) << 28 | b[1] << 20 | (b[2] >> 3) << 15 | \
            (b[2] & 3) << 13 | b[3] << 5 | b[4] >> 3
    if b[0] >> 4 == 2:                                     # MPEG-1
        return ((b[0] >> 1) & 7) << 30 | b[1] << 22 | (b[2] >> 1) << 15 | b[3] << 7 | b[4] >> 1
    return None


def _mpeg_ps(f, size):
    head = f.read(512 * 1024)
    f.seek(max(0, size - 512 * 1024))
    tail = f.read()
    i, j = head.find(b"\x00\x00\x01\xba"), tail.rfind(b"\x00\x00\x01\xba")
    if i < 0 or j < 0:
        return None
    first, last = _scr(head[i + 4:i + 10]), _scr(tail[j + 4:j + 10])
    if first is None or last is None or last <= first:
        return None
    return (last - first) / 90000


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
            if ext in (".mpg", ".mpeg"):
                return _mpeg_ps(f, path.stat().st_size)
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
            g["MOVIE"].append({"title": parts[1], "year": parts[2], "rating": parts[3], "desc": parts[4],
                               "aliases": [a.strip() for a in parts[5].split(",") if a.strip()] if len(parts) > 5 else []})
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


SHOW_KEYS = [("ramsay s kitchen", "KNUK"), ("kitchen nightmares", "KNUS"), ("hotel hell", "HOTELHELL"),
             ("cookalong", "COOKALONG"), ("top gear", "TOPGEAR"), ("wheeler dealer", "WHEELER"),
             ("localnewsarchive cbs", "NEWSCBS"), ("localnewsarchive abc", "NEWSABC"),
             ("localnewsarchive wnbc", "NEWSWNBC"), ("comedy", "COMEDY"), ("aqua teen", "ATHF"), ("ren and stimpy", "REN"), ("ren stimpy", "REN"), ("mongrels", "MONGRELS"),
             ("father of the pride", "FOTP"), ("wolfs rain", "WOLFSRAIN"), ("wolf s rain", "WOLFSRAIN"),
             ("damekko", "DAMEKKO")]


def show_key(name):
    n = norm(name)
    return next((k for kw, k in SHOW_KEYS if kw in n), n.upper()[:20])


def _clean_title(stem):
    t = re.sub(r"[\[(][^\])]*[\])]", " ", stem)                       # [2001], (Nick Version)
    t = re.sub(r"\b(xvid|divx|dvdrip|hdtv|pdtv|ws|x264|yify|bluray|720p|1080p|axxo|riv|mot)\b.*", " ", t, flags=re.I)
    return re.sub(r"[._]+", " ", t).strip(" -")


def _episode_info(stem):
    """(season, episode, title) from 'S03E05 - eDork', '1e01a-Stimpy's Big Day', 'Mongrels.s01e02...Title'."""
    m = re.search(r"(?:^|[ ._-])(\d{1,2})x(\d{1,2})\s*-\s*(.+)$", stem)      # 'Ramsays Kitchen Nightmares - 01x02 - The Glass House'
    if m:
        return int(m.group(1)), int(m.group(2)), re.sub(r"\s*\[.*?\]\s*", " ", m.group(3)).strip()
    m = re.search(r"[sS](\d+)[eE](\d+)(?:-\d+)?(?:\s*-\s*(.+))?", stem)     # ('S01E01-02': a double episode)
    if m:
        title = m.group(3) or ""
        if not title:
            rest = stem[m.end():]
            rest = re.sub(r"^[._]*(?:ws[._])?(?:pdtv[._]|hdtv[._])?xvid-[a-z0-9]+[._]", "", rest, flags=re.I)
            title = re.sub(r"(?:^|[._ -])(?:ws[._ ])?(?:hdtv|pdtv|dvdrip|xvid|divx|x264|webrip)\b.*$", "", rest,
                           flags=re.I)
        title = RELEASE_JUNK.sub("", re.sub(r"[._]+", " ", title)).strip(" -")
        return int(m.group(1)), int(m.group(2)), title
    m = re.match(r"[a-z.]+\.(\d)(\d\d)\.(?:hdtv|pdtv)", stem, re.I)          # 'hotel.hell.101.hdtv-lol'
    if m:
        return int(m.group(1)), int(m.group(2)), ""
    m = re.match(r"(\d+)e(\d+)([ab]?)-(.+)", stem)
    if m:
        return int(m.group(1)), int(m.group(2)), re.sub(r"\s*\(.*?\)\s*", " ", m.group(4)).strip()
    m = re.search(r"[\s_-](\d{1,3})\s*$", re.sub(r"[\[(][^\])]*[\])]", "", stem).strip(" _"))
    if m:                                                    # '[a4e]Wolf's_Rain_01[divx5]', '..._Doubutsu_-_01[CRC]'
        return 1, int(m.group(1)), ""
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


RELEASE_JUNK = re.compile(r"\b(dvdrip|xvid|divx|mp3|ac3|hdtv|pdtv|x264|webrip|trg|valkyria|kroimpa|subbed|proper|repack|"
                          r"480p|720p|1080p|\d{3,4}x\d{3,4}(-\d)?)\b.*$",
                          re.I)


COMEDY_TITLES = {"louis ck beacon": "Louis C.K.: Live at the Beacon Theater",
                 "jim norton american degenerate": "Jim Norton: American Degenerate",
                 "doug stanhope oslo burning the bridge to nowhere": "Doug Stanhope: Oslo, Burning the Bridge to Nowhere",
                 "lewis black taxed beyond belief": "Lewis Black: Taxed Beyond Belief",
                 "dave chappelle killing them softly": "Dave Chappelle: Killing Them Softly",
                 "dave chappelle for what it s worth": "Dave Chappelle: For What It's Worth",
                 "mitch hedberg": "Mitch Hedberg: Stand-Up"}


def _comedy_info(path, show_dir):
    """(show, title, episode, year) for a file in the Comedy folder."""
    rel = path.relative_to(show_dir)
    stem = re.sub(r"[._]+", " ", path.stem)
    year = ""
    m = re.search(r"\(?((?:19|20)\d\d)\)?", stem)
    if m:
        year = m.group(1)
    title = re.sub(r"\(?(?:19|20)\d\d\)?", " ", stem)
    title = RELEASE_JUNK.sub("", title)
    title = re.sub(r"^\s*comedy\s*-\s*stand-?up\s*-\s*", "", title, flags=re.I)
    title = re.sub(r"\s{2,}", " ", title).strip(" -")
    folder = rel.parts[0] if len(rel.parts) > 1 else ""
    m = re.match(r"(.+?)\s+-\s+(\d+)\s+-\s+(.+)", title)
    if m:                                                      # 'The Maria Bamford Show - 01 - Dropout'
        return m.group(1), m.group(3), int(m.group(2)), year
    m = re.match(r"comedy central presents\s*-?\s*(.+)", title, re.I)
    if m:
        return "Comedy Central Presents", m.group(1).strip(), "", year
    if folder.lower().startswith("comedy central presents") and "presents" not in title.lower():
        return "Comedy Central Presents", title, "", year
    m = re.match(r"(.+?)\s+-\s+(.+)", title)                  # 'George Carlin - You Are All Diseased'
    if m:
        return "", f"{m.group(1)}: {m.group(2)}", "", year
    return "", title, "", year


def _match_movie(stem, movies):
    compact = re.sub(r"[^a-z0-9]", "", stem.lower())
    for m in movies:                                   # 'killbill1.divx.vice': spellings that share no words
        if any(a in compact for a in m.get("aliases", [])):
            return m
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


MONTHS = "january february march april may june july august september october november december".split()


def _air_date(text):
    """The broadcast date in a news clip's name: 'September_25_1993' -> 9/25/1993, '10_12_83' -> 10/12/1983,
    '10_93' -> 10/1993."""
    t = text.replace("_", " ").replace(".", " ")
    m = re.search(r"(" + "|".join(MONTHS) + r")\s+(\d{1,2}),?\s+((?:19|20)\d\d)", t, re.I)
    if m:
        return f"{MONTHS.index(m.group(1).lower()) + 1}/{int(m.group(2))}/{m.group(3)}"
    m = re.search(r"(?<!\d)(\d{1,2})\s(\d{1,2})\s(\d{2})(?!\d)", t)
    if m and 1 <= int(m.group(1)) <= 12 and 1 <= int(m.group(2)) <= 31:
        return f"{int(m.group(1))}/{int(m.group(2))}/{1900 + int(m.group(3)) if int(m.group(3)) > 30 else 2000 + int(m.group(3))}"
    m = re.search(r"(?<!\d)(\d{1,2})\s(\d{2})(?!\d)", t)
    if m and 1 <= int(m.group(1)) <= 12:
        return f"{int(m.group(1))}/{1900 + int(m.group(2)) if int(m.group(2)) > 30 else 2000 + int(m.group(2))}"
    m = re.search(r"(?<!\d)((?:19|20)\d\d)(?!\d)", t)
    return m.group(1) if m else ""


def _news_item(p, secs, key, show_title):
    """A news archive clip, with the title and description from the info file that came with it."""
    info = {}
    try:
        info = json.loads((p.parent / (p.stem + ".info.json")).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    title = (info.get("title") or "").strip() or re.sub(r"[-_]+", " ", re.sub(r"-[A-Za-z0-9_-]{11}$", "", p.stem))
    title = title.replace("_", " ")
    title = re.sub(r"^(?:WNBC|NBC|CBS|ABC)(?:[\s-]+NY)?(?:[\s-]+NEWS)?\s*[-:]\s*", "", title, flags=re.I).strip()
    if sum(c.isupper() for c in title) > 0.6 * max(1, sum(c.isalpha() for c in title)):     # SHOUTING -> Title Case
        keep = {"CBS", "ABC", "NBC", "WNBC", "NY", "NYC", "TV", "US", "USA", "UK", "II", "III", "AM", "PM", "DC", "LA"}
        title = " ".join(w if w.strip("().,:-'") in keep else w.capitalize() for w in title.split())
    title = title or "News"
    desc = " ".join((info.get("description") or "").split())
    if len(desc) > 240:
        desc = desc[:237].rsplit(" ", 1)[0] + "..."
    return Media(p, "episode", secs, show=show_title, show_key=key, title=title, desc=desc,
                 aired=_air_date(p.stem))


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
        if hit and hit[0] == st.st_size and hit[1] == int(st.st_mtime) and (hit[2] or 0) <= 12 * 3600:
            fresh[key] = hit
            return hit[2]
        secs = running_time(p)
        fresh[key] = [st.st_size, int(st.st_mtime), secs]
        if progress:
            progress(p.name)
        return secs

    def videos(folder, deep=True):
        for dirpath, dirs, files in os.walk(folder):
            names = set(files)
            for name in sorted(files):
                p = Path(dirpath) / name
                if p.suffix.lower() not in VIDEO_EXTS or SKIP.search(name):
                    continue
                if p.stem.lower().endswith(".ia") and p.stem[:-3] + p.suffix in names:
                    continue                        # 'X.ia.mp4' is the Internet Archive's copy of 'X.mp4'
                yield p
            if not deep:
                dirs[:] = []

    # A 'Movies...' folder can hold whole series and commercials too ('Movies and TV part 2'): loose files in it
    # are movies, a sub-folder with 'commercial' in its name holds ads, and any other sub-folder is a show.
    # ...and inside one, a folder called 'Movies' holds feature films (the feature movie channels), and one called
    # 'News' holds a news archive per station.
    show_dirs, ad_dirs, feature_dirs = [], list(roots["ads"]), []
    for root in roots["tv"]:
        show_dirs += sorted(d for d in root.iterdir() if d.is_dir())
    for root in roots["movies"]:
        for d in sorted(d for d in root.iterdir() if d.is_dir()):
            low = d.name.lower()
            if "commercial" in low or low.startswith(("ads", "adverts")):
                ad_dirs.append(d)
            elif low == "movies":
                feature_dirs.append(d)
            elif low == "news":
                show_dirs += sorted(x for x in d.iterdir() if x.is_dir())
            else:
                show_dirs.append(d)

    def movie(p, key=""):
        secs = secs_for(p)
        if not secs:
            return
        m = _match_movie(p.stem, guide["MOVIE"])
        if m:
            out.append(Media(p, "movie", secs, title=m["title"], year=m["year"], rating=m["rating"], desc=m["desc"],
                             show_key=key))
        else:
            out.append(Media(p, "movie", secs, title=_clean_title(p.stem), show_key=key))

    for root in roots["movies"]:
        for p in videos(root, deep=False):
            movie(p)
    for root in feature_dirs:
        for p in videos(root, deep=False):
            movie(p, "FEATURE")
    for show_dir in show_dirs:
        base_key = show_key(show_dir.name)
        own = read_episode_guide(show_dir)
        for p in videos(show_dir):
            key = base_key
            if key == "KNUK" and "nightmares us" in norm(p.stem):      # US episodes in a UK season folder
                key = "KNUS"
            show_title = guide["SHOW"].get(key, (re.sub(r"\s*[-(].*$", "", show_dir.name).strip(), ""))[0]
            secs = secs_for(p)
            if not secs:
                continue
            if key.startswith("NEWS"):
                out.append(_news_item(p, secs, key, show_title))
                continue
            if "training video" in norm(str(p.relative_to(show_dir))) and secs < 15 * 60:
                out.append(Media(p, "promo", secs, show=show_title, show_key=key,         # Gordon's how-to clips
                                 title=re.sub(r"^\d+\s*-\s*", "", _clean_title(p.stem))))
                continue
            if key == "COMEDY":
                show, title, episode, year = _comedy_info(p, show_dir)
                info = guide["TITLE"].get((key, norm(title))) or {}
                desc = info.get("desc") or (
                    (f"A half hour of stand-up from {title}, taped for Comedy Central Presents." if secs > 15 * 60
                     else f"A short stand-up set from {title}.")
                    if show == "Comedy Central Presents" else
                    "Maria Bamford plays herself, her family and everyone in her hometown after she moves back in "
                    "with her parents." if "Maria Bamford" in show else "A stand-up comedy special.")
                title = COMEDY_TITLES.get(norm(title), title)
                out.append(Media(p, "episode", secs, show=show, show_key=key, episode=episode or "",
                                 title=title, desc=desc, aired=info.get("aired") or year))
                continue
            season, episode, title = _episode_info(p.stem)
            extra = "extra" in norm(str(p.relative_to(show_dir))) or "deleted scene" in norm(p.stem) \
                or "promo" in norm(p.stem) or (not episode and secs < PROMO_MAX_SECS)     # e.g. an ending theme
            if extra and secs < PROMO_MAX_SECS:
                title = re.sub(r"^.*?(extras|deleted scene)\s*-\s*", "", title, flags=re.I)
                out.append(Media(p, "promo", secs, show=show_title, show_key=key, title=title))
                continue
            info = None
            if season and episode:
                info = guide["EP"].get((key, f"S{season}E{episode}"))
            if info is None and title:
                titles = dict(own)
                titles.update((tt, v) for (k, tt), v in guide["TITLE"].items() if k == key)
                info = _match_title(title, titles)
            if extra:
                title = re.sub(r"^.*?(extras|deleted scene)\s*-\s*", "", title, flags=re.I)
            if key == "COOKALONG" and episode:
                episode = episode % 100                                  # 'Cookalong Live - 104' is episode 4
            if not title and not info and episode:
                title = f"Episode {episode}"
            out.append(Media(p, "special" if extra else "episode", secs, show=show_title, show_key=key,
                             season=season or "", episode=episode or "",
                             title=(info or {}).get("title") or title, desc=(info or {}).get("desc", ""),
                             aired=(info or {}).get("aired", "")))
    for root in ad_dirs:
        # a brand's own folder ('Commercials Orangina') keeps its ads apart: they air on their own channel
        ad_key = "ORANGINA" if "orangina" in root.name.lower() else ""
        for p in videos(root):
            secs = secs_for(p)
            if not secs:
                continue
            m = re.match(r"((?:19|20)\d\d)\s+(.+)", p.stem)
            title = m.group(2) if m else re.sub(r"^\d{1,4}\s*-\s*", "", p.stem)        # ('022 - Pokemon Stadium 2')
            folder_year = next((part for part in p.relative_to(root).parts[:-1]          # 'Commercials/2004/...'
                                if re.fullmatch(r"(?:19|20)\d\d", part)), "")
            title = re.sub(r"_\d{3,4}p$", "", title)                      # 'Orangina Bear_1080p'
            title = re.sub(r"\s*(full\s+)?(commercial|ad|promo)\s*$", "", title, flags=re.I).strip() or title
            out.append(Media(p, "ad", secs, title=title, year=folder_year or (m.group(1) if m else ""), show_key=ad_key))
    try:
        INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
        INDEX_FILE.write_text(json.dumps(fresh), encoding="utf-8")
    except OSError:
        pass
    return out
