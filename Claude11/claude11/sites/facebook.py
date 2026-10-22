"""Facebook, autumn 2025: http://www.facebook.com/ in Microsoft Edge or Firefox. The residents' lives as a
News Feed - their diary notes are their status updates (the same ones LiveJournal shows), with likes from their
friends and the comments the life simulation writes - profile pages with the Fur Directory's details, photo
albums from their AIM pictures, friends lists, and your own wall: post a status and a few friends come by to
comment, through the same queue LiveJournal uses."""
import hashlib
import html
import json
import random
import threading
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote

from claudexp.programs.navigator.sites import Response, Site, file_response, redirect

from .. import clock
from ..paths import DATA, PROGRAM_FILES

HOST = "www.facebook.com"
STORE = DATA / "facebook.json"
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp"}
FEED_SIZE = 30
_lock = threading.RLock()
CSS = """
body { margin: 0; background: #F0F2F5; font-family: 'Segoe UI Variable Text', 'Segoe UI', Helvetica, Arial, sans-serif;
       font-size: 15px; color: #050505; }
td, div, p, li, input, textarea, select { font-family: 'Segoe UI Variable Text', 'Segoe UI', Helvetica, Arial, sans-serif;
                                          font-size: 15px; }
a { color: #050505; text-decoration: none; } a:hover { text-decoration: underline; }
#bar { background: #FFFFFF; border-bottom: 1px solid #DDDFE2; }
#bar td { color: #050505; padding: 8px 16px; }
#logo { display: inline-block; width: 40px; height: 40px; line-height: 40px; border-radius: 50%; background: #1877F2;
        color: #FFFFFF; text-align: center; font-size: 28px; font-weight: 700; font-family: Helvetica, Arial, sans-serif; }
#bar a { color: #65676B; font-weight: 600; }
#search { width: 240px; border: none; border-radius: 20px; background: #F0F2F5; padding: 9px 16px; font-size: 15px; }
.nav a { display: block; padding: 9px 10px; color: #050505; border-radius: 8px; font-weight: 600; }
.nav a.on { background: #E7F3FF; color: #1877F2; }
.nav a:hover { background: #E4E6EB; text-decoration: none; }
.box { background: #FFFFFF; border-radius: 8px; padding: 12px 14px; margin: 0 0 12px 0; box-shadow: 0 1px 2px rgba(0,0,0,0.12); }
.box h3 { font-size: 17px; color: #65676B; margin: 0 0 8px 0; font-weight: 600; }
.post { background: #FFFFFF; border-radius: 8px; padding: 12px 14px; margin: 0 0 12px 0; box-shadow: 0 1px 2px rgba(0,0,0,0.12); }
.post .who { font-weight: 600; } .post .time { color: #65676B; font-size: 13px; }
.post .text { margin: 6px 0; font-size: 15px; line-height: 20px; }
.actions { color: #65676B; margin-top: 8px; border-top: 1px solid #E4E6EB; padding-top: 6px; font-weight: 600; }
.actions a { color: #65676B; }
.likes { color: #65676B; font-size: 14px; margin-top: 6px; }
.comment { background: #F0F2F5; border-radius: 16px; padding: 8px 12px; margin-top: 6px; display: inline-block; }
.comment .who { font-weight: 600; }
.cform { padding: 8px 0 0 0; }
input.text, textarea { border: none; background: #F0F2F5; border-radius: 18px; padding: 8px 12px; font-size: 15px; }
.btn { background: #1877F2; color: #FFFFFF; border: none; border-radius: 6px; font-weight: 600; padding: 8px 14px;
       font-size: 15px; cursor: pointer; }
.pic { border-radius: 50%; object-fit: cover; }
.info td { padding: 4px 8px 4px 0; vertical-align: top; } .info td.k { color: #65676B; width: 130px; }
.tabs a { padding: 12px 14px; display: inline-block; color: #65676B; font-weight: 600; }
.tabs a.on { color: #1877F2; border-bottom: 3px solid #1877F2; }
h1 { font-size: 28px; font-weight: 700; color: #050505; margin: 0 0 2px 0; }
.sub { color: #65676B; }
.grid td { padding: 4px; text-align: center; vertical-align: top; }
.ad { background: #FFFFFF; border-radius: 8px; padding: 10px; margin-top: 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.12); }
.ad b { color: #050505; }
"""


# ---- data ----------------------------------------------------------------------------------------------------------
def _sim():
    from claudexp.life import get
    return get()


def _lj():
    from claudexp.life import lj
    return lj


def _me():
    from .. import user
    return user.online_handle()


def _store():
    try:
        data = json.loads(STORE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    data.setdefault("likes", {})
    data.setdefault("walls", {})
    return data


def _save(data):
    with _lock:
        STORE.parent.mkdir(parents=True, exist_ok=True)
        tmp = STORE.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=1), encoding="utf-8")
        tmp.replace(STORE)


def _json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _card(name):
    return _json(PROGRAM_FILES / "The Fur Directory" / "residents" / f"{name}.json")


def _contact(name):
    return _json(PROGRAM_FILES / "ClaudeAIM" / "contacts" / f"{name}.json")


def _people():
    sim = _sim()
    return sorted(sim.people) if sim is not None else []


def _known(name):
    sim = _sim()
    return name == _me() or (sim is not None and name in sim.people)


def _friends(name):
    sim = _sim()
    if sim is None:
        return []
    if name == _me():
        return sorted(sim.buddies, key=str.lower)
    return _lj().friends_of(sim, name)


def _posts(name):
    """[{id, text, date, time}] newest first: yours from LiveJournal's store, theirs from their diary."""
    lj = _lj()
    if name == _me():
        mine = [e for e in lj.load()["entries"] if e.get("security") != "private"]
        return [dict(e, text=e.get("text", "")) for e in mine[::-1]]
    return lj.resident_entries(name)


def _likers(owner, item, data=None):
    """Who liked a post: a few of the owner's friends (always the same ones), plus you if you did."""
    rnd = random.Random(f"{owner}/{item}")
    pool = _friends(owner)
    k = rnd.randint(0, min(6, len(pool))) if pool else 0
    names = rnd.sample(pool, k=k) if k else []
    data = data or _store()
    if _me() in data["likes"].get(f"{owner}/{item}", []):
        names = [_me()] + [n for n in names if n != _me()]
    return names


def _photos(name):
    """[(path, caption)] from their AIM pictures (yours from your Pictures library)."""
    if name == _me():
        from .. import vfs
        try:
            files = sorted(p for p in vfs.my_pictures().rglob("*") if p.suffix.lower() in IMAGE_EXTS)[:60]
        except OSError:
            files = []
        return [(p, p.stem.replace("_", " ")) for p in files]
    folder = PROGRAM_FILES / "ClaudeAIM" / "contacts" / name
    if not folder.is_dir():
        return []
    try:
        from claudeaim.pictures import PictureSet
        ps = PictureSet(folder)
        return [(folder / f, cap) for f, cap in ps.captions.items() if (folder / f).is_file()]
    except Exception:
        return [(p, p.stem) for p in sorted(folder.iterdir()) if p.suffix.lower() in IMAGE_EXTS]


def _picture_path(name):
    if name == _me():
        from .. import user
        pic = user.picture_id() or ""
        if pic.startswith("fursona:"):
            try:
                from claudexp import fursonas
                p = fursonas.picture_path(pic)
                if p:
                    return Path(p)
            except Exception:
                pass
        elif pic == user.CUSTOM:
            from ..paths import find_image
            p = find_image("userpic")
            if p:
                return Path(p)
        elif pic:
            p = user.PICTURES_DIR / pic
            if p.is_file():
                return p
        return None
    icon = _contact(name).get("icon")
    if icon:
        try:
            from claudeaim import paths as aim_paths
            p = Path(aim_paths.resolve_icon(icon))
            if p.is_file():
                return p
        except Exception:
            pass
    return None


def _default_pic(name):
    hue = int(hashlib.md5(name.encode()).hexdigest()[:2], 16) * 360 // 256
    letter = html.escape((name[:1] or "?").upper())
    return (f"<svg xmlns='http://www.w3.org/2000/svg' width='100' height='100'><rect width='100' height='100' "
            f"fill='hsl({hue},40%,58%)'/><text x='50' y='66' font-size='52' text-anchor='middle' fill='white' "
            f"font-family='Arial' font-weight='bold'>{letter}</text></svg>").encode()


def _birthday(name):
    dob = (_card(name).get("personal") or {}).get("dob", "")
    try:
        m, d, _y = (int(x) for x in dob.split("/"))
        return m, d
    except ValueError:
        return None


# ---- pages ---------------------------------------------------------------------------------------------------------
e = html.escape


def _u(name):
    return f"/{quote(name)}"


def _pic_tag(name, size=50, cls="pic"):
    return f'<img src="/pic/{quote(name)}.jpg" width="{size}" height="{size}" class="{cls}" alt="">'


def _page(title, inner, left="", right="", active="home"):
    me = _me()
    nav = "".join(f'<a href="{href}"{" class=\"on\"" if key == active else ""}>{label}</a>'
                  for key, href, label in (("home", "/", "News Feed"), ("messages", "/messages", "Messages"),
                                           ("events", "/events", "Events"), ("photos", f"{_u(me)}/photos", "Photos"),
                                           ("friends", f"{_u(me)}/friends", "Friends")))
    left_col = left or (f'<div style="padding:8px 0">{_pic_tag(me, 32)} <a href="{_u(me)}"><b>{e(me)}</b></a>'
                        f'<br><span class="sub">Edit My Profile</span></div><div class="nav">{nav}</div>')
    return f"""<html><head><title>{e(title)}</title><style>{CSS}</style></head><body>
<table id="bar" width="100%" cellspacing="0" cellpadding="0"><tr>
<td width="70"><a href="/" style="text-decoration:none"><span id="logo">f</span></a></td>
<td><form action="/search" method="get" style="margin:0"><input id="search" name="q" value="" placeholder="Search Facebook"></form></td>
<td align="right"><a href="/">Home</a> &nbsp;&nbsp;&nbsp; <a href="{_u(me)}">{_pic_tag(me, 28)}</a> &nbsp;&nbsp;&nbsp;
<a href="/account">Menu &#9662;</a></td></tr></table>
<table width="100%" cellspacing="0" cellpadding="10"><tr valign="top">
<td width="170">{left_col}</td>
<td style="max-width:680px">{inner}</td>
<td width="210">{right}</td></tr></table>
<div style="text-align:center; color:#65676B; padding:10px">Meta &copy; 2025 &middot;
English (US) &middot; <a href="/about">About</a> &middot; <a href="/privacy">Privacy</a> &middot; <a href="/terms">Terms</a>
&middot; <a href="/help">Help</a></div>
</body></html>"""


def _post_html(owner, p, data, with_form=True):
    lj = _lj()
    item = p["id"]
    likers = _likers(owner, item, data)
    me = _me()
    liked = me in likers
    like_text = ""
    if likers:
        shown = [("You" if n == me else n) for n in likers]
        who = ", ".join(e(n) for n in shown[:3]) + (f" and {len(shown) - 3} others" if len(shown) > 3 else "")
        like_text = f'<div class="likes">&#128077; {who} like{"s" if len(shown) == 1 and shown[0] != "You" else ""} this.</div>'
    comments = lj.comments(lj.load(), owner, item)
    chtml = "".join(f'<div class="comment">{_pic_tag(c["who"], 24)} <span class="who"><a href="{_u(c["who"])}">'
                    f'{e(c["who"])}</a></span> {e(c["text"]).replace(chr(10), "<br>")}'
                    f'<br><span class="time">{e(c.get("date", ""))}</span></div>' for c in comments)
    form = (f'<form class="cform" method="post" action="/comment" style="margin:0"><input type="hidden" name="owner" '
            f'value="{e(owner)}"><input type="hidden" name="item" value="{item}"><input class="text" name="text" '
            f'style="width:80%" placeholder="Write a comment..."> <input class="btn" type="submit" value="Comment"></form>'
            if with_form else "")
    when = f'{e(p.get("date", ""))} at {e(p.get("time", ""))}'
    return (f'<div class="post"><table cellpadding="0" cellspacing="0"><tr valign="top"><td width="58">{_pic_tag(owner, 50)}'
            f'</td><td><span class="who"><a href="{_u(owner)}">{e(owner)}</a></span>'
            f'<div class="text">{e(p.get("text", "")).replace(chr(10), "<br>")}</div>'
            f'<div class="actions"><span class="time">{when}</span> &middot; '
            f'<a href="/like?owner={quote(owner)}&item={item}">{"Unlike" if liked else "Like"}</a> &middot; '
            f'<a href="{_u(owner)}/post/{item}">Comment</a> &middot; <a href="/share?owner={quote(owner)}&item={item}">Share</a></div>'
            f'{like_text}{chtml}{form}</td></tr></table></div>')


class Facebook(Site):
    host = HOST
    aliases = ("facebook.com", "m.facebook.com", "fb.com")
    title = "Facebook"
    blurb = "Everyone's on it now"

    def installed(self):
        return True

    # ---- GET ----
    def handle(self, path, query):
        q = {k: v[0] for k, v in parse_qs(query, keep_blank_values=True).items()}
        if path in ("/", "/home.php", "/index.php"):
            return self._home()
        if path.startswith("/pic/"):
            return self._pic(unquote(path[5:]).removesuffix(".jpg"))
        if path.startswith("/photo/"):
            return self._photo_file(path[7:])
        if path == "/like":
            return self._like(q.get("owner", ""), q.get("item", ""))
        if path == "/share":
            return redirect("/")
        if path == "/profile.php":
            return redirect(_u(q.get("id", _me())))
        if path == "/search":
            return self._search(q.get("q", ""))
        if path in ("/messages", "/events", "/account", "/about", "/privacy", "/terms", "/help"):
            return self._simple(path.strip("/").capitalize())
        name, _, rest = path.strip("/").partition("/")
        name = unquote(name)
        if not _known(name):
            return None
        if rest == "" or rest == "wall":
            return self._profile(name)
        if rest == "info":
            return self._info(name)
        if rest == "photos":
            return self._photos(name)
        if rest.startswith("photos/"):
            return self._photo(name, unquote(rest[7:]))
        if rest == "friends":
            return self._friends(name)
        if rest.startswith("post/"):
            return self._post_page(name, rest[5:])
        return None

    # ---- POST ----
    def handle_post(self, path, query, form):
        f = {k: v[-1] for k, v in form.items()}
        if path == "/post":
            return self._do_post(f.get("text", "").strip(), f.get("to", ""))
        if path == "/comment":
            return self._do_comment(f.get("owner", ""), f.get("item", ""), f.get("text", "").strip())
        return None

    # ---- the feed ----
    def _home(self):
        me = _me()
        data = _store()
        items = []
        for name in [me] + _people():
            for p in _posts(name)[:8]:
                items.append((p["id"], name, p))
        items.sort(key=lambda t: t[0], reverse=True)
        feed = "".join(_post_html(owner, p, data) for _id, owner, p in items[:FEED_SIZE]) or \
            "<p class='sub'>Nothing in your News Feed yet. Your friends' updates show up here.</p>"
        status = (f'<form method="post" action="/post" style="margin:0 0 10px 0"><b>Update Status</b> &nbsp; '
                  f'<span class="sub">Add Photo &middot; Ask Question</span><br>'
                  f'<textarea name="text" rows="2" style="width:98%; margin:4px 0" placeholder="What\'s on your mind?"></textarea>'
                  f'<br><input class="btn" type="submit" value="Post"></form>')
        return _page("Facebook", status + feed, right=self._right_column())

    def _right_column(self):
        me = _me()
        friends = set(_friends(me))
        others = [n for n in _people() if n not in friends and n != me]
        rnd = random.Random(clock.now().strftime("%Y%m%d"))
        suggest = rnd.sample(others, k=min(3, len(others))) if others else []
        now = clock.now()
        soon = []
        for name in _people():
            bd = _birthday(name)
            if bd:
                days = (datetime(now.year, bd[0], bd[1]) - now.replace(hour=0, minute=0, second=0, microsecond=0)).days
                if 0 <= days <= 7:
                    soon.append((days, name))
        soon.sort()
        bdays = "".join(f'<div>{_pic_tag(n, 24)} <a href="{_u(n)}">{e(n)}</a> <span class="sub">'
                        f'{"today" if d == 0 else "tomorrow" if d == 1 else f"in {d} days"}</span></div>'
                        for d, n in soon[:4]) or "<span class='sub'>No birthdays this week.</span>"
        sugg = "".join(f'<div>{_pic_tag(n, 32)} <a href="{_u(n)}">{e(n)}</a><br><span class="sub">'
                       f'{len(set(_friends(n)) & friends)} mutual friends</span> &middot; <a href="{_u(n)}">Add Friend</a></div>'
                       for n in suggest) or "<span class='sub'>You know everyone.</span>"
        return (f'<div class="box"><h3>People You May Know</h3>{sugg}</div>'
                f'<div class="box"><h3>Birthdays</h3>{bdays}</div>'
                f'<div class="box"><h3>Sponsored</h3><div class="ad"><b>Furry Con 2026</b><br>Registration is open! Four '
                f'days of art, fursuits and friends. <a href="http://www.furryconventions.com/">Register now</a>.</div>'
                f'<div class="ad"><b>Windows 11</b><br>Your PC, simplified. <a href="http://windows.microsoft.com/">'
                f'Learn more</a>.</div></div>')

    # ---- profiles ----
    def _left(self, name, active):
        card = _card(name)
        personal = card.get("personal") or {}
        sona = card.get("fursona") or {}
        rows = []
        if personal.get("location"):
            rows.append(("Lives in", personal["location"]))
        if personal.get("job"):
            rows.append(("Works at", personal["job"]))
        if sona.get("species"):
            rows.append(("Species", sona["species"]))
        bd = _birthday(name)
        if bd:
            rows.append(("Birthday", datetime(2000, bd[0], bd[1]).strftime("%B %d").replace(" 0", " ")))
        info = "".join(f'<tr><td class="k">{e(k)}</td><td>{e(v)}</td></tr>' for k, v in rows)
        friends = _friends(name)
        grid = "".join(f'<td><a href="{_u(f)}">{_pic_tag(f, 48)}<br>{e(f)}</a></td>' for f in friends[:6])
        tabs = "".join(f'<a href="{_u(name)}{href}"{" class=\"on\"" if key == active else ""}>{label}</a>'
                       for key, href, label in (("wall", "", "Wall"), ("info", "/info", "Info"),
                                                ("photos", "/photos", "Photos"), ("friends", "/friends", "Friends")))
        return (f'<div style="text-align:center">{_pic_tag(name, 150)}</div>'
                f'<div class="box"><table class="info">{info}</table></div>'
                f'<div class="box"><h3>Friends ({len(friends)})</h3><table class="grid"><tr>{grid[:3]}</tr></table>'
                f'<table class="grid" cellpadding="2"><tr>{"".join(f"<td><a href=\"{_u(f)}\">{_pic_tag(f, 44)}</a></td>" for f in friends[:4])}</tr></table>'
                f'<a href="{_u(name)}/friends">See All</a></div>'
                f'<div class="box"><div class="tabs">{tabs}</div></div>')

    def _head(self, name):
        card = _card(name)
        summary = card.get("summary", "")
        me = _me()
        action = ('<span class="sub">This is you.</span>' if name == me else
                  f'<a href="/messages"><span class="btn">Message</span></a> &nbsp; '
                  f'<a href="/poke?who={quote(name)}">Poke</a>')
        return f'<h1>{e(name)}</h1><div class="sub">{e(summary[:160])}</div><div style="margin:6px 0 10px 0">{action}</div>'

    def _profile(self, name):
        me = _me()
        data = _store()
        posts = _posts(name)
        wall = "".join(_post_html(name, p, data) for p in posts[:15])
        notes = data["walls"].get(name, [])
        wall_posts = "".join(f'<div class="post"><table cellpadding="0" cellspacing="0"><tr valign="top"><td width="58">'
                             f'{_pic_tag(w["who"], 50)}</td><td><span class="who"><a href="{_u(w["who"])}">{e(w["who"])}</a>'
                             f'</span> &#9656; <a href="{_u(name)}">{e(name)}</a><div class="text">{e(w["text"])}</div>'
                             f'<div class="actions"><span class="time">{e(w["date"])}</span></div></td></tr></table></div>'
                             for w in notes[::-1][:10])
        if not posts and not notes:
            wall = "<p class='sub'>Nothing on this wall yet.</p>"
        placeholder = "What's on your mind?" if name == me else f"Write something on {name}'s wall..."
        form = (f'<form method="post" action="/post" style="margin:0 0 10px 0"><input type="hidden" name="to" '
                f'value="{e(name)}"><textarea name="text" rows="2" style="width:98%" placeholder="{e(placeholder)}">'
                f'</textarea><br><input class="btn" type="submit" value="{"Post" if name == me else "Share"}"></form>')
        return _page(name, self._head(name) + form + wall_posts + wall, left=self._left(name, "wall"),
                     right=self._right_column(), active="")

    def _info(self, name):
        card = _card(name)
        personal, sona, fav = card.get("personal") or {}, card.get("fursona") or {}, card.get("favorites") or {}
        rel = (card.get("relationship") or {}).get("status", "")
        rows = [("Sex", personal.get("sex", "")), ("Birthday", ""), ("Current City", personal.get("location", "")),
                ("Relationship Status", rel), ("Employer", personal.get("job", "")),
                ("Species", sona.get("species", "")), ("Looks like", sona.get("description", "")[:200]),
                ("Interests", card.get("interests", "")[:300]),
                ("Favorite Movies", ", ".join(fav.get("movies") or [])),
                ("Favorite Music", ", ".join(fav.get("music") or [])),
                ("Favorite Food", ", ".join(fav.get("food") or [])),
                ("About", card.get("personality", "")[:400])]
        bd = _birthday(name)
        if bd:
            rows[1] = ("Birthday", datetime(2000, bd[0], bd[1]).strftime("%B %d").replace(" 0", " "))
        table = "".join(f'<tr><td class="k">{e(k)}</td><td>{e(v)}</td></tr>' for k, v in rows if v)
        return _page(f"{name} - Info", self._head(name) + f'<table class="info">{table}</table>',
                     left=self._left(name, "info"), active="")

    def _photos(self, name):
        pics = _photos(name)
        cells = "".join(f'<td><a href="{_u(name)}/photos/{quote(p.name)}"><img src="/photo/{quote(name)}/{quote(p.name)}" '
                        f'width="130" class="pic" alt=""></a><br><span class="sub">{e(cap[:40])}</span></td>'
                        for p, cap in pics[:40])
        rows = "".join(f"<tr>{cells_row}</tr>" for cells_row in _chunks(cells.split("</td>"), 4))
        body = (f'<table class="grid">{rows}</table>' if pics else
                "<p class='sub'>No photos yet.</p>")
        return _page(f"{name}'s Photos", self._head(name) + f"<h3>{e(name)}'s Photos ({len(pics)})</h3>" + body,
                     left=self._left(name, "photos"), active="")

    def _photo(self, name, filename):
        pics = _photos(name)
        for i, (p, cap) in enumerate(pics):
            if p.name == filename:
                prev_ = pics[i - 1][0].name if i > 0 else None
                next_ = pics[i + 1][0].name if i + 1 < len(pics) else None
                nav = ((f'<a href="{_u(name)}/photos/{quote(prev_)}">&laquo; Previous</a> ' if prev_ else "") +
                       (f'&nbsp; <a href="{_u(name)}/photos/{quote(next_)}">Next &raquo;</a>' if next_ else ""))
                body = (f'<div class="sub">Photo {i + 1} of {len(pics)} &nbsp; {nav}</div>'
                        f'<img src="/photo/{quote(name)}/{quote(p.name)}" width="500" class="pic" alt=""><br>'
                        f'<div class="text" style="margin:6px 0">{e(cap)}</div>'
                        f'<div class="actions"><a href="#">Like</a> &middot; <a href="#">Comment</a> &middot; '
                        f'<a href="#">Tag This Photo</a></div>')
                return _page(f"{name}'s Photos", self._head(name) + body, left=self._left(name, "photos"), active="")
        return None

    def _photo_file(self, rest):
        name, _, filename = rest.partition("/")
        name, filename = unquote(name), unquote(filename)
        for p, _cap in _photos(name):
            if p.name == filename:
                return file_response(p)
        return None

    def _friends(self, name):
        friends = _friends(name)
        cells = "".join(f'<td width="25%"><a href="{_u(f)}">{_pic_tag(f, 48)}</a> <a href="{_u(f)}"><b>{e(f)}</b></a>'
                        f'<br><span class="sub">{len(set(_friends(f)) & set(friends))} mutual friends</span></td>'
                        for f in friends)
        rows = "".join(f"<tr>{r}</tr>" for r in _chunks(cells.split("</td>"), 2))
        return _page(f"{name}'s Friends", self._head(name) + f"<h3>Friends ({len(friends)})</h3>"
                     f'<table class="grid" width="100%">{rows}</table>', left=self._left(name, "friends"), active="")

    def _post_page(self, name, item):
        if not item.isdigit():
            return redirect(_u(name))
        post = next((p for p in _posts(name) if str(p["id"]) == item), None)
        if post is None:
            return redirect(_u(name))
        return _page(f"{name}", self._head(name) + _post_html(name, post, _store()), left=self._left(name, "wall"),
                     active="")

    def _pic(self, name):
        path = _picture_path(name)
        if path is not None:
            return file_response(path)
        return Response(_default_pic(name), "image/svg+xml")

    def _search(self, q):
        q = q.strip().lower()
        hits = [n for n in [_me()] + _people() if q and q in n.lower()]
        body = "".join(f'<div class="post">{_pic_tag(n, 32)} <a href="{_u(n)}"><b>{e(n)}</b></a></div>' for n in hits) \
            or "<p class='sub'>No results.</p>"
        return _page("Search", f"<h3>Search results for \"{e(q)}\"</h3>{body}")

    def _simple(self, what):
        texts = {"Messages": "No new messages. Chat with your friends on Telegram or Discord instead.",
                 "Events": "No upcoming events. Furry Con 2026 registration opens soon.",
                 "Account": "Account Settings, Privacy Settings, Log Out. (This is a Claude11 page: nothing to set.)",
                 "About": "Facebook helps you connect and share with the people in your life.",
                 "Privacy": "Meta's Privacy Policy, 2025 edition: a very long page.",
                 "Terms": "Statement of Rights and Responsibilities.", "Help": "Help Center."}
        return _page(what, f"<h3>{e(what)}</h3><p>{e(texts.get(what, ''))}</p>")

    # ---- actions ----
    def _like(self, owner, item):
        if not (_known(owner) and item.isdigit()):
            return redirect("/")
        key = f"{owner}/{item}"
        me = _me()
        with _lock:
            data = _store()
            names = data["likes"].setdefault(key, [])
            if me in names:
                names.remove(me)
            else:
                names.append(me)
            _save(data)
        return redirect(_u(owner) if owner != me else "/")

    def _do_post(self, text, to):
        me = _me()
        if not text:
            return redirect("/")
        if to and to != me and _known(to):
            now = clock.now()
            with _lock:
                data = _store()
                data["walls"].setdefault(to, []).append({"who": me, "text": text[:2000], "ts": int(now.timestamp()),
                                                          "date": f"{now:%B} {now.day} at {clock.time_text(now)}"})
                _save(data)
            return redirect(_u(to))
        lj = _lj()
        friends = _friends(me)

        def change(data):
            entry = lj.new_entry(data, "", text[:4000], "", "", "public")
            entry["date"] = entry["date"].replace("2001", str(clock.YEAR))
            lj.queue_comments_on(data, entry, friends)
        lj.update(change)
        return redirect("/")

    def _do_comment(self, owner, item, text):
        if not (_known(owner) and item.isdigit() and text):
            return redirect("/")
        lj = _lj()
        me = _me()

        def change(data):
            lj.add_comment(data, owner, int(item), me, text[:1500])
            if owner != me:
                lj.queue_reply(data, owner, int(item), text[:1500])
        lj.update(change)
        return redirect(f"{_u(owner)}/post/{item}" if owner != me else "/")


def _chunks(cells, n):
    cells = [c + "</td>" for c in cells if c.strip()]
    return ["".join(cells[i:i + n]) for i in range(0, len(cells), n)]
