"""FurAffinity, built from the image rip: every artist folder is an artist's gallery, every picture a submission.

FA saves files as '<unix time>.<artist>_<title>.<ext>'; the times (Dec 2005 - Jun 2010) are spread over
Jan 1999 - Oct 2001 in the same order, so the site fits ClaudeXP's 2001 and nothing is 'from the future'.
The residents have accounts too (from The Fur Directory): their favourites, shouts, journals and comments live in
data/furaffinity.json (social.py keeps it), and you can favourite art yourself as your own online name."""
import hashlib
import os
import random
import re
import threading
import time
from datetime import datetime
from urllib.parse import quote, unquote

from . import Site, file_response, redirect
from .builder import IMAGE_EXTS, e, page_number, pager, shell, thumbnail

SRC_START, SRC_END = datetime(2005, 12, 1).timestamp(), datetime(2010, 6, 30).timestamp()
DST_START, DST_END = datetime(1999, 1, 1).timestamp(), datetime(2001, 10, 1).timestamp()
PER_PAGE = 48
FA_CSS = """body { background: #2D3B42; color: #CFD8DC; font-family: Verdana, Arial, sans-serif; font-size: 11px; margin: 0; }
a { color: #FFAA44; text-decoration: none; } a:hover { text-decoration: underline; }
#header { background: #1C262B; border-bottom: 3px solid #FF8A00; padding: 8px 16px; }
#logo { font-family: 'Trebuchet MS', Verdana; font-size: 28px; font-weight: bold; color: #FFFFFF; letter-spacing: 1px; }
#logo span { color: #FF8A00; } #tag { color: #8FA3AD; font-size: 10px; }
#nav { background: #3C4D55; padding: 5px 16px; border-bottom: 1px solid #1C262B; }
#nav a { color: #FFFFFF; font-weight: bold; margin-right: 16px; } #nav .me { float: right; color: #FFCC88; }
#main { padding: 12px 16px; } h2 { font-family: 'Trebuchet MS', Verdana; font-size: 15px; color: #FFFFFF;
background: #3C4D55; padding: 4px 8px; margin: 14px 0 6px; border-left: 4px solid #FF8A00; }
.box { background: #36464E; border: 1px solid #22303A; padding: 8px; margin-bottom: 10px; }
.grid td.cell { background: #36464E; border: 1px solid #22303A; width: 170px; height: 190px; font-size: 10px; }
.grid img { border: 1px solid #1C262B; } .grid .by { color: #8FA3AD; }
.pager { text-align: center; margin: 10px; font-size: 12px; } .pager b { color: #FFFFFF; }
.sub img.full { max-width: 100%; max-height: 640px; border: 2px solid #1C262B; } .meta td { padding: 2px 10px 2px 0; }
.meta .k { color: #8FA3AD; } .shout, .comment { background: #3A4A52; border: 1px solid #22303A; padding: 6px; margin: 6px 0; }
.shout .who, .comment .who { color: #FFAA44; font-weight: bold; } .when { color: #8FA3AD; font-size: 9px; }
.avatar { border: 1px solid #1C262B; width: 100px; height: 100px; object-fit: cover; }
.button { background: #FF8A00; color: #1C262B; padding: 3px 10px; font-weight: bold; border: 1px solid #A85A00; }
#footer { text-align: center; color: #6F848E; font-size: 9px; padding: 14px; border-top: 1px solid #22303A; }
table.members td { padding: 2px 12px 2px 0; }"""


def fa_date(ts):
    """A real FA upload time -> its 1999-2001 date."""
    f = (min(max(ts, SRC_START), SRC_END) - SRC_START) / (SRC_END - SRC_START)
    return datetime.fromtimestamp(DST_START + f * (DST_END - DST_START))


def _title(stem, artist):
    t = re.sub(r"^\d{9,}\.", "", stem)
    low = artist.lower().strip("-_")
    t = re.sub(rf"^[-_]*{re.escape(low)}[-_]*_", "", t, flags=re.I) if low else t
    t = re.sub(r"^\d{9,}\.[^_]+_", "", t)                 # re-posts carry the original poster's prefix too
    t = re.sub(r"[_]+", " ", t).strip(" .-")
    t = re.sub(r"\b(copy|small|smallwm|wm|fin|final)\b", "", t, flags=re.I).strip(" .-") or "Untitled"
    return t[:1].upper() + t[1:]


class Submission:
    __slots__ = ("id", "artist", "title", "path", "rel", "date", "ts")


class Index:
    """Everything in the rip, read once (in the server thread, the first time the site is visited)."""

    def __init__(self, root):
        self.root = root
        self.subs = {}                 # id -> Submission
        self.by_artist = {}            # artist lower -> [Submission], oldest first
        self.artist_names = {}         # artist lower -> display name
        for dirpath, _dirs, files in os.walk(root):
            folder = os.path.relpath(dirpath, root)
            for name in files:
                ext = os.path.splitext(name)[1].lower()
                if ext not in IMAGE_EXTS:
                    continue
                rel = name if folder == "." else f"{folder}/{name}".replace("\\", "/")
                stem = os.path.splitext(name)[0]
                m = re.match(r"(\d{10})\.(.+)$", stem)
                artist = folder.split(os.sep)[0] if folder != "." else ""
                if not artist:
                    am = re.match(r"\d{10}\.([^_]+)_", stem)
                    artist = am.group(1) if am else "FurAffinity"
                path = os.path.join(dirpath, name)
                ts = int(m.group(1)) if m else int(os.path.getmtime(path))
                s = Submission()
                s.id = int(hashlib.sha1(rel.lower().encode()).hexdigest()[:7], 16)
                s.artist, s.rel, s.path, s.ts = artist, rel, path, ts
                s.title = _title(stem, artist)
                s.date = fa_date(ts)
                self.subs[s.id] = s
                key = artist.lower()
                self.artist_names.setdefault(key, artist)
                self.by_artist.setdefault(key, []).append(s)
        for subs in self.by_artist.values():
            subs.sort(key=lambda s: (s.ts, s.rel))
        self.newest = sorted(self.subs.values(), key=lambda s: (s.ts, s.rel), reverse=True)


class FurAffinity(Site):
    host, aliases, folder = "www.furaffinity.net", ("furaffinity.com", "fa.net"), "FurAffinity"
    title, blurb = "FurAffinity", "art, journals and friends: the residents are on here too"

    def __init__(self):
        self._index = None
        self._lock = threading.Lock()

    def index(self):
        with self._lock:
            if self._index is None or self._index.root != self.root():
                self._index = Index(self.root())
            return self._index

    # ---- who's who ---------------------------------------------------------------------------------------
    def residents(self):
        """{lower name: (display name, Resident)} for everyone in The Fur Directory, cached for a minute."""
        now = time.monotonic()
        cached = getattr(self, "_res", None)
        if cached and now - cached[0] < 60:
            return cached[1]
        from ...furdir import residents
        out = {}
        for r in residents():
            if r.tier == "user" and not r.is_you:
                continue
            out[r.name.lower()] = (r.name, r)
        self._res = (now, out)
        return out

    def me(self):
        from .... import user
        return user.online_handle() or user.user_name() or "Guest"

    def social(self):
        from . import social
        return social.get(self)

    # ---- the page shell ----------------------------------------------------------------------------------
    def _page(self, title, body):
        me = self.me()
        nav = (f'<div id="nav"><a href="/">Home</a><a href="/browse/">Browse</a><a href="/search/">Search</a>'
               f'<a href="/members/">Members</a><a href="/journals/">Journals</a>'
               f'<span class="me">Logged in as <a href="/user/{quote(me)}/">{e(me)}</a> &middot; '
               f'<a href="/favorites/{quote(me)}/">My Favorites</a></span></div>')
        return shell(f"{title} -- Fur Affinity [dot] net",
                     '<div id="header"><div id="logo">Fur<span>Affinity</span></div><div id="tag">Fur Affinity '
                     '[dot] net &mdash; the furry art community</div></div>' + nav + f'<div id="main">{body}</div>'
                     '<div id="footer">Fur Affinity [dot] net &copy; 2001. All artwork is &copy; its artists. '
                     'Server time: ' + datetime.now().strftime("%H:%M") + "</div>", FA_CSS)

    def _thumbs(self, subs, cols=6):
        cells = [f'<td class="cell" align="center" valign="top"><a href="/view/{s.id}/"><img src="/thumb/{s.id}/" '
                 f'style="max-width:150px;max-height:150px"></a><br><b>{e(s.title[:28])}</b><br>'
                 f'<span class="by">by <a href="/user/{quote(s.artist)}/">{e(s.artist)}</a></span></td>' for s in subs]
        rows = ["<tr>" + "".join(cells[i:i + cols]) + "</tr>" for i in range(0, len(cells), cols)]
        return '<table class="grid" cellspacing="4">' + "".join(rows) + "</table>"

    def _visible(self, subs):
        """Submissions already posted by ClaudeXP's clock."""
        from .... import clock
        now = clock.now()
        return [s for s in subs if s.date <= now]

    # ---- requests -----------------------------------------------------------------------------------------
    def handle(self, path, query):
        idx = self.index()
        m = re.match(r"/(thumb|full)/(\d+)/?$", path)
        if m:
            s = idx.subs.get(int(m.group(2)))
            if s is None:
                return None
            return thumbnail(s.path, 150) if m.group(1) == "thumb" else file_response(s.path)
        m = re.match(r"/avatar/([^/]+)/?$", path)
        if m:
            return self._avatar(unquote(m.group(1)))
        if path in ("/", "/index.html"):
            return self._front()
        if path.rstrip("/") == "/browse":
            return self._browse(query)
        m = re.match(r"/view/(\d+)/?$", path)
        if m:
            return self._view(int(m.group(1)))
        m = re.match(r"/fav/(\d+)/?$", path)
        if m:
            self.social().toggle_fave(self.me(), int(m.group(1)))
            return redirect(f"/view/{m.group(1)}/")
        m = re.match(r"/(user|gallery|favorites|journal)/([^/]+)/?(\d*)/?$", path)
        if m:
            return getattr(self, "_" + m.group(1))(unquote(m.group(2)), query, m.group(3))
        if path.rstrip("/") == "/members":
            return self._members(query)
        if path.rstrip("/") == "/journals":
            return self._journals()
        if path.rstrip("/") == "/search":
            return self._search(query)
        return None

    def _front(self):
        idx = self.index()
        recent = self._visible(idx.newest)[:16]
        soc = self.social()
        active = soc.recently_active(8)
        journals = soc.latest_journals(6)
        side = "".join(f'<div class="shout"><a class="who" href="/journal/{quote(j["user"])}/{j["n"]}/">'
                       f'{e(j["title"])}</a><br><span class="when">by {e(j["user"])} &middot; {e(j["when"])}</span></div>'
                       for j in journals) or "<p>No journals yet.</p>"
        people = " &middot; ".join(f'<a href="/user/{quote(n)}/">{e(n)}</a>' for n in active) or "&nbsp;"
        return self._page("Home", f'<table width="100%"><tr valign="top"><td><h2>Recent Submissions</h2>'
                          f'{self._thumbs(recent, cols=4)}<p align="right"><a href="/browse/">Browse everything &raquo;</a></p>'
                          f'</td><td style="width:270px;min-width:270px"><h2>Welcome!</h2><div class="box">Fur Affinity is home to '
                          f'{len(idx.subs):,} pieces of art by {len(idx.by_artist):,} artists. Watch your favourite '
                          f'artists, leave shouts and keep a journal.</div><h2>Recently Active</h2><div class="box">'
                          f'{people}</div><h2>Latest Journals</h2>{side}</td></tr></table>')

    def _browse(self, query):
        subs = self._visible(self.index().newest)
        page = page_number(query)
        pages = max(1, -(-len(subs) // PER_PAGE))
        shown = subs[(page - 1) * PER_PAGE: page * PER_PAGE]
        return self._page("Browse", f"<h2>Browse &mdash; newest first</h2>{pager('/browse/', page, pages)}"
                          f"{self._thumbs(shown)}{pager('/browse/', page, pages)}")

    def _view(self, sid):
        s = self.index().subs.get(sid)
        if s is None or not self._visible([s]):
            return None
        soc = self.social()
        me = self.me()
        faved = sid in soc.faves(me)
        rng = random.Random(sid)
        views = rng.randint(40, 2400) + len(soc.favers(sid)) * 37
        favers = soc.favers(sid)
        fav_n = rng.randint(0, 60) + len(favers)
        comments = "".join(f'<div class="comment"><a class="who" href="/user/{quote(c["from"])}/">{e(c["from"])}</a> '
                           f'<span class="when">{e(c["when"])}</span><br>{e(c["text"])}</div>'
                           for c in soc.comments(sid)) or "<p>No comments yet.</p>"
        who_faved = ", ".join(f'<a href="/user/{quote(n)}/">{e(n)}</a>' for n in favers[:12])
        siblings = self.index().by_artist.get(s.artist.lower(), [])
        i = siblings.index(s)
        prev_l = f'<a href="/view/{siblings[i - 1].id}/">&laquo; Older</a>' if i > 0 else ""
        next_l = f'<a href="/view/{siblings[i + 1].id}/">Newer &raquo;</a>' if i + 1 < len(siblings) and \
            self._visible([siblings[i + 1]]) else ""
        return self._page(s.title, f'<div class="sub"><h2>{e(s.title)}</h2><center><a href="/full/{s.id}/">'
                          f'<img class="full" src="/full/{s.id}/"></a><br>{prev_l} &nbsp; {next_l}</center>'
                          f'<table width="100%"><tr valign="top"><td><table class="meta">'
                          f'<tr><td class="k">Artist</td><td><a href="/user/{quote(s.artist)}/">{e(s.artist)}</a></td></tr>'
                          f'<tr><td class="k">Posted</td><td>{s.date:%B %d, %Y %I:%M %p}</td></tr>'
                          f'<tr><td class="k">Category</td><td>Artwork (Digital) / General Furry Art</td></tr>'
                          f'<tr><td class="k">Views</td><td>{views:,}</td></tr>'
                          f'<tr><td class="k">Favorites</td><td>{fav_n}</td></tr></table>'
                          f'<p><a class="button" href="/fav/{s.id}/">{"-Remove from" if faved else "+Add to"} '
                          f'Favorites</a></p>' + (f"<p>Faved by: {who_faved}</p>" if who_faved else "") +
                          f'</td></tr></table><h2>Comments</h2>{comments}</div>')

    def _avatar(self, name):
        res = self.residents().get(name.lower())
        if res is not None and res[1].icon_path is not None:
            return thumbnail(res[1].icon_path, 100)
        subs = self.index().by_artist.get(name.lower())
        if subs:
            return thumbnail(subs[0].path, 100)
        return None

    def _user(self, name, query, _n):
        idx = self.index()
        key = name.lower()
        res = self.residents().get(key)
        subs = self._visible(idx.by_artist.get(key, []))
        soc = self.social()
        if res is None and not subs and key != self.me().lower():
            return None
        display = res[0] if res else idx.artist_names.get(key, name)
        about = ""
        if res is not None:
            rec = res[1].record or {}
            sona = rec.get("fursona", {}) if isinstance(rec.get("fursona"), dict) else {}
            species = sona.get("species") or (res[1].muck or {}).get("species", "")
            summary = rec.get("summary") or ((res[1].aim or {}).get("profile") or "")
            about = (f'<b>Species:</b> {e(species) or "&mdash;"}<br><br>{e(summary)}' if species or summary else "")
        elif subs:
            about = f"Artist. {len(subs)} submissions in the gallery."
        links = soc.links(display)
        link_html = "".join(f'<li><a href="{e(u)}">{e(t)}</a></li>' for u, t in links)
        shouts = "".join(f'<div class="shout"><a class="who" href="/user/{quote(sh["from"])}/">{e(sh["from"])}</a> '
                         f'<span class="when">{e(sh["when"])}</span><br>{e(sh["text"])}</div>'
                         for sh in soc.shouts(display)[-12:][::-1]) or "<p>No shouts yet.</p>"
        journal = soc.journals(display)
        jhtml = (f'<div class="box"><a href="/journal/{quote(display)}/{len(journal)}/"><b>{e(journal[-1]["title"])}'
                 f'</b></a> <span class="when">{e(journal[-1]["when"])}</span><br>{e(journal[-1]["text"][:400])}</div>'
                 if journal else "<p>No journals yet.</p>")
        faves = [idx.subs[i] for i in soc.faves(display)[-6:][::-1] if i in idx.subs]
        gallery = (f'<h2>Gallery <a href="/gallery/{quote(display)}/" style="font-size:11px">(view all '
                   f'{len(subs)})</a></h2>{self._thumbs(subs[::-1][:6])}' if subs else "")
        return self._page(f"Userpage of {display}",
                          f'<h2>~{e(display)}</h2><table width="100%"><tr valign="top"><td width="120">'
                          f'<img class="avatar" src="/avatar/{quote(display)}/"></td><td><div class="box">'
                          f'{about or "This user hasn&#39;t written a profile yet."}</div>'
                          + (f'<b>Sites I like:</b><ul>{link_html}</ul>' if link_html else "") +
                          f'</td></tr></table>{gallery}<h2>Latest Journal</h2>{jhtml}'
                          f'<h2>Favorites <a href="/favorites/{quote(display)}/" style="font-size:11px">(view all)</a></h2>'
                          f'{self._thumbs(faves) if faves else "<p>No favorites yet.</p>"}<h2>Shouts</h2>{shouts}')

    def _gallery(self, name, query, _n):
        subs = self._visible(self.index().by_artist.get(name.lower(), []))[::-1]
        if not subs:
            return None
        page = page_number(query)
        pages = max(1, -(-len(subs) // PER_PAGE))
        shown = subs[(page - 1) * PER_PAGE: page * PER_PAGE]
        base = f"/gallery/{quote(name)}/"
        return self._page(f"Gallery of {name}", f"<h2>Gallery of {e(name)}</h2>{pager(base, page, pages)}"
                          f"{self._thumbs(shown)}{pager(base, page, pages)}")

    def _favorites(self, name, query, _n):
        idx = self.index()
        subs = [idx.subs[i] for i in self.social().faves(name)[::-1] if i in idx.subs]
        page = page_number(query)
        pages = max(1, -(-len(subs) // PER_PAGE))
        base = f"/favorites/{quote(name)}/"
        body = self._thumbs(subs[(page - 1) * PER_PAGE: page * PER_PAGE]) if subs else "<p>No favorites yet.</p>"
        return self._page(f"Favorites of {name}", f"<h2>{e(name)}'s Favorites</h2>{pager(base, page, pages)}{body}")

    def _journal(self, name, query, n):
        js = self.social().journals(name)
        if not js:
            return self._page(f"Journals of {name}", f"<h2>{e(name)}'s Journal</h2><p>No journals yet.</p>")
        if n and n.isdigit() and 1 <= int(n) <= len(js):
            j = js[int(n) - 1]
            return self._page(j["title"], f'<h2>{e(j["title"])}</h2><div class="box"><span class="when">by '
                              f'<a href="/user/{quote(name)}/">{e(name)}</a> &middot; {e(j["when"])}</span><br><br>'
                              + e(j["text"]).replace("\n", "<br>") + "</div>")
        rows = "".join(f'<div class="shout"><a class="who" href="/journal/{quote(name)}/{i}/">{e(j["title"])}</a>'
                       f' <span class="when">{e(j["when"])}</span></div>' for i, j in reversed(list(enumerate(js, 1))))
        return self._page(f"Journals of {name}", f"<h2>{e(name)}'s Journal</h2>{rows}")

    def _journals(self):
        rows = "".join(f'<div class="shout"><a class="who" href="/journal/{quote(j["user"])}/{j["n"]}/">'
                       f'{e(j["title"])}</a> <span class="when">by {e(j["user"])} &middot; {e(j["when"])}</span></div>'
                       for j in self.social().latest_journals(40))
        return self._page("Journals", f"<h2>Latest Journals</h2>{rows or '<p>No journals yet.</p>'}")

    def _members(self, query):
        idx = self.index()
        names = {n.lower(): n for n, _r in self.residents().values()}
        names.update({k: v for k, v in idx.artist_names.items() if k not in names})
        everyone = sorted(names.values(), key=lambda n: n.lower())
        page = page_number(query)
        per = 150
        pages = max(1, -(-len(everyone) // per))
        shown = everyone[(page - 1) * per: page * per]
        cols = [shown[i::3] for i in range(3)]
        rows = "".join("<tr>" + "".join(f'<td><a href="/user/{quote(c[r])}/">{e(c[r])}</a></td>' if r < len(c)
                                        else "<td></td>" for c in cols) + "</tr>" for r in range(len(cols[0])))
        return self._page("Members", f"<h2>Members ({len(everyone):,})</h2>{pager('/members/', page, pages)}"
                          f'<table class="members">{rows}</table>{pager("/members/", page, pages)}')

    def _search(self, query):
        m = re.search(r"(?:^|&)q=([^&]*)", query or "")
        q = unquote(m.group(1).replace("+", " ")).strip() if m else ""
        form = (f'<form action="/search/" method="get"><input name="q" value="{e(q)}" size="40"> '
                f'<input type="submit" value="Search"></form>')
        if not q:
            return self._page("Search", f"<h2>Search</h2>{form}")
        words = q.lower().split()
        idx = self.index()
        hits = [s for s in self._visible(idx.newest)
                if all(w in s.title.lower() or w in s.artist.lower() for w in words)]
        page = page_number(query)
        pages = max(1, -(-len(hits) // PER_PAGE))
        base = f"/search/?q={quote(q)}"
        return self._page(f"Search: {q}", f"<h2>Search</h2>{form}<p>{len(hits):,} results for <b>{e(q)}</b></p>"
                          f"{pager(base, page, pages)}{self._thumbs(hits[(page - 1) * PER_PAGE: page * PER_PAGE])}")
