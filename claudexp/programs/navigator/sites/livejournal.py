"""The Furry LiveJournal, autumn 2001: http://www.livejournal.com/ - everyone's online journal.

Every resident has a journal at /users/<name>/ with their life-journal notes as entries (Current mood, Current
music), a Friends page, a User Info page and comments. You log in as yourself and keep your own journal: Update
Journal posts an entry (public, friends-only or private), Edit Entries changes or deletes one, Edit Info is your
profile. Buddies comment on what you post and answer your comments (life/lj.py). Pages are real HTML with forms,
on the furry web's local server.
"""
import html
from urllib.parse import parse_qs, quote, unquote

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPen, QPixmap, QPolygonF

from . import Response, Site, file_response, redirect

HOST = "www.livejournal.com"
_session = {"signed_in": False}
_userpic = {"png": b""}          # your picture, made on the main thread (QPixmap can't be used from the server's)
RECENT = 20


# ---- the desktop icon --------------------------------------------------------------------------------------------

def lj_pixmap(size=32):
    """A journal with a pencil writing in it, and LiveJournal's blue."""
    from PySide6.QtCore import QPointF
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 32
    g = QLinearGradient(0, 0, size, size)
    g.setColorAt(0, QColor("#5B8FD0"))
    g.setColorAt(1, QColor("#1E4E96"))
    p.setPen(QPen(QColor("#163A70"), max(1.0, s)))
    p.setBrush(g)
    p.drawRoundedRect(QRectF(3 * s, 2.5 * s, 22 * s, 27 * s), 2 * s, 2 * s)      # the cover
    p.setBrush(QColor("#FFFDF4"))
    p.setPen(QPen(QColor("#8A8A80"), max(0.8, 0.8 * s)))
    p.drawRect(QRectF(7 * s, 5 * s, 16 * s, 22 * s))                             # the page
    p.setPen(QPen(QColor("#9DB8E0"), max(0.8, 0.9 * s)))
    for i in range(6):
        y = (9 + i * 3) * s
        p.drawLine(QPointF(9 * s, y), QPointF(21 * s, y))
    p.setPen(QPen(QColor("#163A70"), max(0.8, s)))
    for i in range(5):                                                           # the spiral
        p.drawEllipse(QRectF(4.2 * s, (6 + i * 4.5) * s, 4 * s, 2.6 * s))
    f = QFont("Georgia")
    f.setBold(True)
    f.setItalic(True)
    f.setPixelSize(max(6, int(9 * s)))
    p.setFont(f)
    p.setPen(QColor("#1E4E96"))
    p.drawText(QRectF(9 * s, 6 * s, 13 * s, 10 * s), Qt.AlignCenter, "LJ")
    # the pencil, writing
    p.translate(23 * s, 22 * s)
    p.rotate(-45)
    p.setPen(QPen(QColor("#5A4410"), max(0.8, 0.8 * s)))
    p.setBrush(QColor("#FFC93C"))
    p.drawRect(QRectF(0, -2.2 * s, 13 * s, 4.4 * s))
    p.setBrush(QColor("#F08CA0"))
    p.drawRect(QRectF(13 * s, -2.2 * s, 2.5 * s, 4.4 * s))
    p.setBrush(QColor("#F3D9A8"))
    p.drawPolygon(QPolygonF([QPointF(0, -2.2 * s), QPointF(-4 * s, 0), QPointF(0, 2.2 * s)]))
    p.setBrush(QColor("#303030"))
    p.drawPolygon(QPolygonF([QPointF(-2.6 * s, -0.8 * s), QPointF(-4 * s, 0), QPointF(-2.6 * s, 0.8 * s)]))
    p.end()
    return pm


def lj_icon():
    icon = QIcon()
    for sz in (16, 32, 48):
        icon.addPixmap(lj_pixmap(sz))
    return icon


def open_livejournal(desktop):
    from .. import open_url
    open_url(desktop, "http://www.livejournal.com/")


# ---- helpers -----------------------------------------------------------------------------------------------------

def _sim():
    from ....life import get
    return get()


def _lj():
    from ....life import lj
    return lj


def _me():
    from .... import user
    return user.online_handle()


def _u(name):
    return f"/users/{quote(name)}/"


def _text(t):
    return html.escape(t or "").replace("\n", "<br>\n")


def _refresh_userpic():
    from .... import user
    pm = user.picture_pixmap()
    if pm.isNull():
        return
    pm = pm.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    ba = QByteArray()
    buf = QBuffer(ba)
    buf.open(QIODevice.WriteOnly)
    pm.save(buf, "PNG")
    _userpic["png"] = bytes(ba)


CSS = """
body { margin: 0; background: #FFFFFF; font-family: Verdana, Arial, sans-serif; font-size: 12px; }
td, th, div, p, li, form, input, select, textarea { font-family: Verdana, Arial, sans-serif; font-size: 12px; }
a { color: #003399; }
.head { background: #FFFFFF; border-bottom: 3px solid #336699; }
.logo { font-family: Georgia, serif; font-size: 30px; font-style: italic; font-weight: bold; color: #336699; }
.logo span { color: #F0A020; }
.side { background: #EEF2F8; border-right: 1px solid #B0C0D8; }
.side a { text-decoration: none; display: block; padding: 2px 0; }
.box { border: 1px solid #B0C0D8; background: #F7F9FC; padding: 8px; }
.jhead { background: #336699; color: #FFFFFF; }
.jhead a { color: #FFFFFF; }
.jtitle { font-family: Georgia, serif; font-size: 22px; font-weight: bold; color: #FFFFFF; }
.date { background: #C8D6EA; font-weight: bold; padding: 3px 6px; }
.entry { border: 1px solid #B0C0D8; margin: 0 0 14px 0; }
.etext { padding: 8px; font-size: 13px; line-height: 1.35; }
.meta { padding: 0 8px 6px 8px; color: #555555; font-size: 11px; }
.links { background: #EEF2F8; padding: 3px 8px; font-size: 11px; text-align: right; }
.comment { border-left: 3px solid #B0C0D8; margin: 8px 0 8px 20px; padding: 4px 8px; background: #FAFBFD; }
.foot { color: #777777; font-size: 10px; }
.btn { font-family: Verdana; font-size: 12px; }
input.text, textarea { border: 1px solid #7F9DB9; }
"""


def _page(title, inner):
    me = _me()
    nav = (f'<a href="/update.bml"><b>Update Journal</b></a><a href="{_u(me)}">Your Journal</a>'
           f'<a href="{_u(me)}friends">Friends Page</a><a href="/editjournal.bml">Edit Entries</a>'
           f'<a href="/editinfo.bml">Edit Info</a><a href="/logout.bml">Log Out</a>'
           if _session["signed_in"] else '<a href="/login.bml"><b>Log In</b></a>'
           '<a href="/create.bml">Create a Journal</a>')
    return f"""<html><head><title>{html.escape(title)}</title><style>{CSS}</style></head><body>
<table width="100%" cellpadding="8" cellspacing="0" class="head"><tr>
<td><a href="/" style="text-decoration:none"><span class="logo">LiveJournal<span>.com</span></span></a></td>
<td align="right" valign="bottom" style="color:#666666">{"Logged in as <b>" + html.escape(me) + "</b>" if _session["signed_in"] else "Not logged in"}</td></tr></table>
<table width="100%" cellspacing="0" cellpadding="0"><tr valign="top">
<td width="150" class="side" style="padding:10px">{nav}<br><b>Find</b><a href="/directory.bml">Directory</a>
<a href="/random.bml">Random Journal</a><br><b>About</b><a href="/site/about.bml">What is LiveJournal?</a></td>
<td style="padding:12px">{inner}</td></tr></table>
<center class="foot"><br>LiveJournal.com - run by volunteers and paid accounts. Frank the goat says hi.<br><br></center>
</body></html>"""


def _journal_page(name, title, inner, me_page=False):
    """A journal in the 'Generator' style everyone used."""
    links = (f'<a href="{_u(name)}">Recent Entries</a> &nbsp;|&nbsp; <a href="{_u(name)}friends">Friends</a> '
             f'&nbsp;|&nbsp; <a href="/userinfo.bml?user={quote(name)}">User Info</a> &nbsp;|&nbsp; '
             '<a href="/">LiveJournal.com</a>')
    return f"""<html><head><title>{html.escape(title)}</title><style>{CSS}</style></head><body>
<table width="100%" cellpadding="10" cellspacing="0" class="jhead"><tr>
<td width="110"><img src="/userpic/{quote(name)}.png" width="80" height="80" style="border:2px solid #FFFFFF;
background:#FFFFFF" alt=""></td><td><div class="jtitle">{html.escape(name)}'s Journal</div>
<div style="padding-top:4px">{links}</div></td></tr></table>
<table width="100%" cellpadding="14"><tr><td>{inner}</td></tr></table>
<center class="foot">Powered by LiveJournal.com</center><br></body></html>"""


def _entry_box(owner, e, data, show_comments_link=True):
    lj = _lj()
    count = len(lj.comments(data, owner, e["id"]))
    subject = f'<b>{html.escape(e["subject"])}</b><br>' if e.get("subject") else ""
    lock = " <i>(friends only)</i>" if e.get("security") == "friends" else (
        " <i>(private)</i>" if e.get("security") == "private" else "")
    meta = []
    if e.get("mood"):
        meta.append(f"<b>Current mood:</b> {html.escape(e['mood'])}")
    if e.get("music"):
        meta.append(f"<b>Current music:</b> {html.escape(e['music'])}")
    link = f"{_u(owner)}{e['id']}.html"
    links = (f'<a href="{link}">{count} comment{"s" if count != 1 else ""}</a> | '
             f'<a href="{link}#add">Leave a comment</a>') if show_comments_link else ""
    if owner == _me() and _session["signed_in"]:
        links += f' | <a href="/editjournal.bml?itemid={e["id"]}">Edit</a>'
    return (f'<div class="entry"><div class="date">{html.escape(e.get("date", ""))} &nbsp; '
            f'<span style="font-weight:normal">{html.escape(e.get("time", ""))}</span>{lock}</div>'
            f'<div class="etext">{subject}{_text(e["text"])}</div>'
            f'<div class="meta">{"<br>".join(meta)}</div><div class="links">{links}</div></div>')


def _entries(name, data):
    """name's entries, newest first (yours from data, everyone else's from their life journal)."""
    if name == _me():
        mine = data["entries"][::-1]
        return [e for e in mine if e.get("security") != "private" or _session["signed_in"]]
    return _lj().resident_entries(name)


def _known(name):
    sim = _sim()
    return name == _me() or (sim is not None and name in sim.people)


def _resolve(name):
    """The journal's real name for what was typed ('arcticfox' -> 'ArcticFox'), or None."""
    if _known(name):
        return name
    low = name.lower()
    if low == _me().lower():
        return _me()
    sim = _sim()
    return next((n for n in (sim.people if sim is not None else []) if n.lower() == low), None)


def _journals():
    """Everyone with a journal: you, the AIM buddies, and every regular who has written anything."""
    sim = _sim()
    if sim is None:
        return [_me()]
    names = [n for n, p in sim.people.items() if p.contact is not None or _lj().resident_entries(n)]
    return [_me()] + sorted(names, key=str.lower)


# ---- the site ------------------------------------------------------------------------------------------------------

class LiveJournal(Site):
    host = HOST
    aliases = ("livejournal.com", "livejournal.org")
    title = "LiveJournal"
    blurb = "Everyone's online journal"

    def __init__(self):
        import threading
        if threading.current_thread() is threading.main_thread():
            _refresh_userpic()
            try:
                from .... import user
                user.account().changed.connect(_refresh_userpic)
            except Exception:
                pass

    def installed(self):
        return True

    # ---- GET ----
    def handle(self, path, query):
        q = {k: v[0] for k, v in parse_qs(query, keep_blank_values=True).items()}
        if path in ("/", "/index.bml"):
            return self._home()
        if path.startswith("/~"):
            return redirect(_u(path[2:].strip("/")))
        if path.startswith("/userpic/"):
            return self._userpic(unquote(path[9:]).removesuffix(".png"))
        if path == "/login.bml":
            return self._login()
        if path == "/logout.bml":
            _session["signed_in"] = False
            return redirect("/")
        if path == "/create.bml":
            return _page("Create a Journal", "<h3>Create a Journal</h3><p>You already have a journal: "
                         f'<a href="{_u(_me())}">{html.escape(_me())}</a>. <a href="/login.bml">Log in</a> to update '
                         "it.</p><p>(LiveJournal is invite-only right now - ask a friend for an invite code!)</p>")
        if path == "/directory.bml":
            return self._directory()
        if path == "/random.bml":
            import random
            return redirect(_u(random.choice(_journals())))
        if path == "/site/about.bml":
            return _page("About LiveJournal", "<h3>What is LiveJournal?</h3><p>LiveJournal is a simple-to-use "
                         "communication tool that lets you express yourself, share your life, and connect with "
                         "friends online. Keep a journal, read your friends' journals on your Friends page, and "
                         "leave comments.</p><p>LiveJournal was started in 1999 by Brad Fitzpatrick as a way of "
                         "keeping his high school friends updated on his activities.</p>")
        if path == "/userinfo.bml":
            return self._userinfo(q.get("user", ""))
        if path.startswith("/users/"):
            return self._users(path[7:])
        needs_login = path in ("/update.bml", "/editjournal.bml", "/editinfo.bml")
        if needs_login and not _session["signed_in"]:
            return redirect("/login.bml")
        if path == "/update.bml":
            return self._update_form()
        if path == "/editjournal.bml":
            return self._edit_form(q.get("itemid", ""))
        if path == "/editinfo.bml":
            return self._editinfo_form()
        return None

    # ---- POST ----
    def handle_post(self, path, query, form):
        f = {k: v[-1] for k, v in form.items()}
        if path == "/login.bml":
            return self._do_login(f)
        if path == "/talkpost_do.bml":
            return self._do_comment(f)
        if not _session["signed_in"]:
            return redirect("/login.bml")
        if path == "/update.bml":
            return self._do_update(f)
        if path == "/editjournal.bml":
            return self._do_edit(f)
        if path == "/editinfo.bml":
            return self._do_editinfo(f)
        return None

    # ---- pages ----
    def _home(self):
        lj = _lj()
        rows = []
        latest = []
        for name in _journals()[1:]:
            ents = lj.resident_entries(name)
            if ents:
                latest.append((ents[0]["id"], name, ents[0]))
        latest.sort(reverse=True)
        for _id, name, e in latest[:12]:
            snippet = html.escape(e["text"][:140]) + ("..." if len(e["text"]) > 140 else "")
            rows.append(f'<tr valign="top"><td width="60"><img src="/userpic/{quote(name)}.png" width="50" height="50">'
                        f'</td><td><a href="{_u(name)}"><b>{html.escape(name)}</b></a> &nbsp; '
                        f'<span class="foot">{html.escape(e["date"])} {html.escape(e["time"])}</span><br>{snippet} '
                        f'<a href="{_u(name)}{e["id"]}.html">more&raquo;</a></td></tr>')
        login = ("" if _session["signed_in"] else
                 '<div class="box"><b>Log in</b> to update your journal and read your Friends page.<br><br>'
                 '<a href="/login.bml">Log in &raquo;</a></div><br>')
        me = _me()
        inner = f"""{login}<h3 style="color:#336699">Welcome to LiveJournal</h3>
<p>LiveJournal is a place to keep a journal online, read your friends' journals, and talk about it all.
{f'<a href="{_u(me)}friends"><b>Read your Friends page</b></a> or <a href="/update.bml"><b>post an entry</b></a>.' if _session["signed_in"] else ""}</p>
<div class="box"><b>Recently updated journals</b><table cellpadding="5">{"".join(rows) or "<tr><td>Nobody has posted yet.</td></tr>"}</table></div>
<p class="foot">LiveJournal has {41207 + len(_journals()) * 13:,} journals, {len(_journals())} of them people you know.</p>"""
        return _page("LiveJournal.com", inner)

    def _userpic(self, name):
        if name == _me():
            return Response(_userpic["png"], "image/png") if _userpic["png"] else None
        sim = _sim()
        person = sim.people.get(name) if sim is not None else None
        if person is not None and person.contact is not None and person.contact.icon:
            from claudeaim import paths as aim_paths
            return file_response(aim_paths.resolve_icon(person.contact.icon))
        return Response(_default_pic(name), "image/svg+xml")

    def _login(self, error=""):
        err = f'<p style="color:#CC0000"><b>{html.escape(error)}</b></p>' if error else ""
        inner = f"""<h3>Log in</h3>{err}<form method="post" action="/login.bml"><table cellpadding="4">
<tr><td>Username:</td><td><input class="text" name="user" value="{html.escape(_me())}"></td></tr>
<tr><td>Password:</td><td><input class="text" type="password" name="password" value="********"></td></tr>
<tr><td></td><td><input type="submit" class="btn" value="Log in"></td></tr></table></form>"""
        return _page("Log in", inner)

    def _do_login(self, f):
        _session["signed_in"] = True                   # (the password box is for show: anything logs in)
        return redirect(f"{_u(_me())}friends")

    def _directory(self):
        sim = _sim()
        rows = []
        for name in _journals():
            person = sim.people.get(name) if sim is not None else None
            n = len(_entries(name, _lj().load()))
            bio = html.escape(_lj().about(person.persona)) if person is not None else "That's you!"
            rows.append(f'<tr valign="top"><td><a href="{_u(name)}"><b>{html.escape(name)}</b></a></td>'
                        f'<td>{n}</td><td>{bio}</td></tr>')
        return _page("Directory", f'<h3>Directory</h3><table cellpadding="4" width="100%"><tr><th align="left">'
                                  f'Journal</th><th align="left">Entries</th><th align="left">About</th></tr>'
                                  f'{"".join(rows)}</table>')

    def _userinfo(self, name):
        name = _resolve(name) or name
        if not _known(name):
            return _page("Unknown user", "<h3>Unknown user</h3><p>There is no user by that name.</p>")
        lj = _lj()
        data = lj.load()
        sim = _sim()
        if name == _me():
            prof = data["profile"]
            bio = _text(prof.get("bio", "")) or "<i>(nothing yet - <a href='/editinfo.bml'>Edit Info</a>)</i>"
            interests = prof.get("interests", "")
            location = prof.get("location", "")
            friends = sorted(sim.buddies, key=str.lower) if sim is not None else []
        else:
            person = sim.people[name]
            bio = html.escape(lj.about(person.persona))
            interests = ""
            location = ""
            friends = lj.friends_of(sim, name)
            if person.contact is not None:
                friends = sorted(set(friends) | {_me()}, key=str.lower)
        flinks = ", ".join(f'<a href="/userinfo.bml?user={quote(n)}">{html.escape(n)}</a>' for n in friends)
        n = len(_entries(name, data))
        rows = [("User", f'<a href="{_u(name)}">{html.escape(name)}</a>'), ("About", bio)]
        if location:
            rows.append(("Location", html.escape(location)))
        if interests:
            rows.append(("Interests", html.escape(interests)))
        rows += [("Website", f'<a href="http://www.furrycities.com/{quote(name)}/">My FurryCities homepage</a>'),
                 ("Journal entries", str(n)), ("Friends", flinks or "(none)")]
        table = "".join(f'<tr valign="top"><td width="120"><b>{k}:</b></td><td>{v}</td></tr>' for k, v in rows)
        return _page(f"User Info: {name}",
                     f'<table cellpadding="5"><tr><td><img src="/userpic/{quote(name)}.png" width="100" height="100">'
                     f'</td><td><h3>{html.escape(name)}</h3></td></tr></table><table cellpadding="5">{table}</table>')

    def _users(self, rest):
        name, _, sub = rest.partition("/")
        real = _resolve(unquote(name))
        if real is None:
            return None
        if real != unquote(name):
            return redirect(_u(real) + sub)
        name = real
        lj = _lj()
        data = lj.load()
        if not sub:
            ents = _entries(name, data)[:RECENT]
            if name != _me():
                lj.update(lambda d: lj.request_backfill(d, name, len(ents)))
            inner = "".join(_entry_box(name, e, data) for e in ents) or (
                "<p>This journal has no entries yet." + ("" if name == _me() else
                " Check back in a little while - they may be writing one right now!") + "</p>")
            if name == _me() and _session["signed_in"]:
                inner = '<p><a href="/update.bml"><b>Post a new entry &raquo;</b></a></p>' + inner
            return _journal_page(name, f"{name}'s Journal", inner)
        if sub.rstrip("/") == "friends":
            return self._friends(name, data)
        if sub.endswith(".html") and sub[:-5].isdigit():
            return self._entry(name, int(sub[:-5]), data)
        return None

    def _friends(self, name, data):
        lj = _lj()
        sim = _sim()
        if name == _me():
            friends = sorted(sim.buddies, key=str.lower) if sim is not None else []
        else:
            friends = lj.friends_of(sim, name)
        posts = []
        asked = 0
        for f in friends:
            ents = _entries(f, data)
            if f != _me() and asked < 4 and len(ents) < lj.BACKFILL_ENTRIES and f not in data["backfilled"]:
                asked += 1
                lj.update(lambda d, f=f, n=len(ents): lj.request_backfill(d, f, n))
            for e in ents[:5]:
                posts.append((e.get("ts") or e["id"], f, e))
        posts.sort(key=lambda x: x[0], reverse=True)
        boxes = []
        for _ts, f, e in posts[:30]:
            boxes.append(f'<table width="100%" cellspacing="0"><tr valign="top"><td width="70" align="center">'
                         f'<img src="/userpic/{quote(f)}.png" width="56" height="56"><br><a href="{_u(f)}">'
                         f'<b>{html.escape(f)}</b></a></td><td>{_entry_box(f, e, data)}</td></tr></table>')
        inner = "".join(boxes) or "<p>Nobody on the friends list has posted yet.</p>"
        return _journal_page(name, f"{name}'s Friends", f"<h3>{html.escape(name)}'s Friends</h3>{inner}")

    def _entry(self, name, item, data):
        lj = _lj()
        e = next((x for x in _entries(name, data) if x["id"] == item), None)
        if e is None:
            return None
        cs = lj.comments(data, name, item)
        comments = "".join(
            f'<div class="comment"><table><tr valign="top"><td><img src="/userpic/{quote(c["who"])}.png" width="40" '
            f'height="40"></td><td><a href="{_u(c["who"])}"><b>{html.escape(c["who"])}</b></a> '
            f'<span class="foot">{html.escape(c["date"])}</span><br>{_text(c["text"])}</td></tr></table></div>'
            for c in cs)
        form = (f'<a name="add"></a><div class="box"><b>Leave a comment</b><form method="post" action="/talkpost_do.bml">'
                f'<input type="hidden" name="journal" value="{html.escape(name)}"><input type="hidden" name="itemid" '
                f'value="{item}"><textarea name="body" rows="5" cols="60"></textarea><br>'
                f'<input type="submit" class="btn" value="Post Comment"> &nbsp; <span class="foot">Posting as '
                f'<b>{html.escape(_me())}</b></span></form></div>'
                if _session["signed_in"] else
                '<div class="box"><a href="/login.bml">Log in</a> to leave a comment.</div>')
        inner = (_entry_box(name, e, data, show_comments_link=False)
                 + f"<h4>{len(cs)} comment{'s' if len(cs) != 1 else ''}</h4>{comments}{form}")
        return _journal_page(name, f"{name}: {e.get('subject') or 'entry'}", inner)

    def _do_comment(self, f):
        if not _session["signed_in"]:
            return redirect("/login.bml")
        name, item, body = f.get("journal", ""), f.get("itemid", ""), f.get("body", "").strip()
        if not (_known(name) and item.isdigit() and body):
            return redirect(_u(name) if _known(name) else "/")
        lj = _lj()
        me = _me()

        def change(data):
            lj.add_comment(data, name, int(item), me, body)
            if name != me:
                lj.queue_reply(data, name, int(item), body)
        lj.update(change)
        return redirect(f"{_u(name)}{item}.html")

    # ---- your journal ----
    def _form(self, action, e=None, delete=False):
        e = e or {}
        moods = "".join(f'<option{" selected" if m == e.get("mood") else ""}>{m}</option>' for m in [""] + _lj().MOODS)
        sec = e.get("security", "public")
        secs = "".join(f'<option value="{v}"{" selected" if v == sec else ""}>{label}</option>'
                       for v, label in (("public", "Public"), ("friends", "Friends only"), ("private", "Private")))
        hidden = f'<input type="hidden" name="itemid" value="{e["id"]}">' if e.get("id") else ""
        extra = ('<input type="submit" class="btn" name="action" value="Delete Entry" '
                 'onclick="return confirm(\'Delete this entry?\')">' if delete else "")
        return f"""<form method="post" action="{action}">{hidden}<table cellpadding="4" width="100%">
<tr><td width="90"><b>Subject:</b></td><td><input class="text" name="subject" size="60" value="{html.escape(e.get("subject", ""))}"></td></tr>
<tr><td valign="top"><b>Event:</b></td><td><textarea name="event" rows="14" style="width:100%">{html.escape(e.get("text", ""))}</textarea></td></tr>
<tr><td><b>Current mood:</b></td><td><select name="mood">{moods}</select></td></tr>
<tr><td><b>Current music:</b></td><td><input class="text" name="music" size="40" value="{html.escape(e.get("music", ""))}"></td></tr>
<tr><td><b>Security:</b></td><td><select name="security">{secs}</select></td></tr>
<tr><td></td><td><input type="submit" class="btn" name="action" value="{"Save Changes" if delete else "Update Journal"}"> {extra}</td></tr>
</table></form>"""

    def _update_form(self):
        return _page("Update Journal", "<h3>Update Journal</h3><p>Write about your day. Your friends will see it on "
                     "their Friends pages.</p>" + self._form("/update.bml"))

    def _do_update(self, f):
        if not f.get("event", "").strip():
            return Response(_page("Update Journal", "<h3>Update Journal</h3><p style='color:#CC0000'><b>Your entry "
                                  "is empty.</b></p>" + self._form("/update.bml")))
        lj = _lj()
        sim = _sim()
        friends = sorted(sim.buddies) if sim is not None else []

        def change(data):
            entry = lj.new_entry(data, f.get("subject", ""), f["event"], f.get("mood", ""), f.get("music", ""),
                                 f.get("security", "public"))
            lj.queue_comments_on(data, entry, friends)
        lj.update(change)
        return redirect(_u(_me()))

    def _edit_form(self, itemid):
        data = _lj().load()
        if itemid.isdigit():
            e = next((x for x in data["entries"] if x["id"] == int(itemid)), None)
            if e is not None:
                return _page("Edit Entry", "<h3>Edit Entry</h3>" + self._form("/editjournal.bml", e, delete=True))
        rows = "".join(f'<tr><td>{html.escape(e["date"])}</td><td><a href="/editjournal.bml?itemid={e["id"]}">'
                       f'{html.escape(e.get("subject") or e["text"][:60] or "(no subject)")}</a></td>'
                       f'<td>{e.get("security", "public")}</td></tr>' for e in data["entries"][::-1])
        return _page("Edit Entries", f'<h3>Edit Entries</h3><table cellpadding="4" width="100%"><tr><th align="left">'
                                     f'Date</th><th align="left">Entry</th><th align="left">Security</th></tr>'
                                     f'{rows or "<tr><td colspan=3>You have no entries yet.</td></tr>"}</table>')

    def _do_edit(self, f):
        lj = _lj()
        item = int(f["itemid"]) if f.get("itemid", "").isdigit() else -1

        def change(data):
            for e in data["entries"]:
                if e["id"] == item:
                    if f.get("action") == "Delete Entry":
                        data["entries"].remove(e)
                        data["comments"].pop(f"{_me()}/{item}", None)
                    else:
                        e.update(subject=f.get("subject", "").strip(), text=f.get("event", "").strip(),
                                 mood=f.get("mood", ""), music=f.get("music", "").strip(),
                                 security=f.get("security", "public"))
                    return
        lj.update(change)
        return redirect(_u(_me()))

    def _editinfo_form(self):
        prof = _lj().load()["profile"]
        inner = f"""<h3>Edit Info</h3><form method="post" action="/editinfo.bml"><table cellpadding="4">
<tr><td><b>Location:</b></td><td><input class="text" name="location" size="40" value="{html.escape(prof.get("location", ""))}"></td></tr>
<tr><td valign="top"><b>Bio:</b></td><td><textarea name="bio" rows="6" cols="60">{html.escape(prof.get("bio", ""))}</textarea></td></tr>
<tr><td valign="top"><b>Interests:</b></td><td><input class="text" name="interests" size="60" value="{html.escape(prof.get("interests", ""))}"><br>
<span class="foot">Separate them with commas: furries, anime, drawing, AIM...</span></td></tr>
<tr><td></td><td><input type="submit" class="btn" value="Save Changes"></td></tr></table></form>
<p class="foot">Your picture is your Windows account picture (Control Panel &gt; User Accounts).</p>"""
        return _page("Edit Info", inner)

    def _do_editinfo(self, f):
        def change(data):
            data["profile"].update(location=f.get("location", "").strip(), bio=f.get("bio", "").strip(),
                                   interests=f.get("interests", "").strip())
        _lj().update(change)
        return redirect(f"/userinfo.bml?user={quote(_me())}")


def _default_pic(name):
    """No userpic: a coloured square with their initial (for regulars without an AIM buddy icon)."""
    import hashlib
    hue = int(hashlib.md5(name.encode()).hexdigest()[:2], 16) * 360 // 256
    letter = html.escape((name[:1] or "?").upper())
    return (f"<svg xmlns='http://www.w3.org/2000/svg' width='100' height='100'><rect width='100' height='100' "
            f"fill='hsl({hue},45%,62%)'/><text x='50' y='66' font-size='52' text-anchor='middle' fill='white' "
            f"font-family='Georgia' font-weight='bold'>{letter}</text></svg>").encode()
