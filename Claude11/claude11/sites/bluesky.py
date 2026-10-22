"""Bluesky, autumn 2025: http://bsky.app/ in Microsoft Edge or Firefox. The residents' lives as a timeline - their
diary notes are their posts (the same ones LiveJournal and Facebook show), with likes and reposts from their friends
and the replies the life simulation writes - profiles with the Fur Directory's details, a media tab from their
pictures, follows, and your own posts: write one and a few friends reply, through the same queue LiveJournal uses.
The data helpers are Facebook's (sites/facebook.py); only the store of likes and reposts is Bluesky's own."""
import hashlib
import html
import json
import random
import threading
from urllib.parse import parse_qs, quote, unquote

from claudexp.programs.navigator.sites import Response, Site, file_response, redirect

from .. import clock
from ..paths import DATA
from .facebook import (_birthday, _card, _default_pic, _friends, _known, _likers, _lj, _me, _people, _photos,
                       _picture_path, _posts)

HOST = "bsky.app"
STORE = DATA / "bluesky.json"
FEED_SIZE = 40
_lock = threading.RLock()
e = html.escape
LOGO = ('<svg xmlns="http://www.w3.org/2000/svg" width="30" height="27" viewBox="0 0 568 501" fill="#1185FE">'
        '<path d="M123.121 33.664C188.241 82.553 258.281 181.68 284 234.873c25.719-53.192 95.759-152.32 160.879-201.21'
        'C491.866-1.611 568-28.906 568 57.947c0 17.346-9.945 145.713-15.778 166.555-20.275 72.453-94.155 90.933-159.875 '
        '79.748C507.222 323.8 536.444 388.56 473.333 453.32c-119.86 122.992-172.272-30.859-185.702-70.281-2.462-7.227-3.614-'
        '10.608-3.631-7.733-.017-2.875-1.169.506-3.631 7.733-13.43 39.422-65.842 193.273-185.702 70.281-63.111-64.76-33.889-'
        '129.52 80.986-149.071-65.72 11.185-139.6-7.295-159.875-79.748C9.945 203.659 0 75.291 0 57.946 0-28.906 76.135-1.612 '
        '123.121 33.664Z"/></svg>')
CSS = """
body { margin: 0; background: #FFFFFF; font-family: 'Segoe UI Variable Text', 'Segoe UI', -apple-system, Helvetica, Arial,
       sans-serif; font-size: 15px; color: #0B0F14; }
td, div, p, li, input, textarea, select { font-family: 'Segoe UI Variable Text', 'Segoe UI', Helvetica, Arial, sans-serif;
                                          font-size: 15px; }
a { color: #0B0F14; text-decoration: none; } a:hover { text-decoration: underline; }
a.blue, .blue a { color: #1083FE; }
.nav a { display: block; padding: 10px 14px; font-size: 18px; border-radius: 24px; color: #0B0F14; }
.nav a.on { font-weight: 700; }
.nav a:hover { background: #F1F3F5; text-decoration: none; }
.newpost { display: block; background: #1083FE; color: #FFFFFF; text-align: center; border-radius: 24px; padding: 11px;
           font-weight: 700; margin: 10px 14px; }
.newpost:hover { background: #0070E0; text-decoration: none; }
#center { border-left: 1px solid #E4E9EE; border-right: 1px solid #E4E9EE; min-height: 600px; }
.tabs { border-bottom: 1px solid #E4E9EE; }
.tabs a { display: inline-block; padding: 12px 18px; color: #42576C; font-weight: 600; }
.tabs a.on { color: #0B0F14; border-bottom: 3px solid #1083FE; }
.post { border-bottom: 1px solid #E4E9EE; padding: 12px 14px; }
.post:hover { background: #FAFBFC; }
.post .who { font-weight: 700; } .post .handle, .post .time, .sub, .muted { color: #42576C; }
.post .text { margin: 4px 0 8px 0; font-size: 15px; line-height: 20px; white-space: pre-wrap; }
.actions { color: #42576C; font-size: 14px; }
.actions a { color: #42576C; margin-right: 28px; }
.actions a.liked { color: #EC4899; font-weight: 700; } .actions a.reposted { color: #20BC07; font-weight: 700; }
.avatar { border-radius: 50%; object-fit: cover; }
.compose { border-bottom: 1px solid #E4E9EE; padding: 12px 14px; }
textarea.compose { width: 97%; border: none; font-size: 17px; resize: none; outline: none; padding: 6px 0; }
.btn { background: #1083FE; color: #FFFFFF; border: none; border-radius: 20px; padding: 7px 16px; font-weight: 700;
       font-size: 14px; cursor: pointer; }
.btn.ghost { background: #F1F3F5; color: #0B0F14; }
input.text { border: 1px solid #D4DBE2; border-radius: 20px; padding: 7px 14px; font-size: 14px; width: 92%;
             background: #F1F3F5; }
.card { border: 1px solid #E4E9EE; border-radius: 10px; padding: 12px 14px; margin: 12px 0; }
.card h3 { margin: 0 0 8px 0; font-size: 16px; }
.banner { height: 150px; background: linear-gradient(135deg, #1083FE, #7C3AED); }
.profile-head { padding: 0 14px 12px 14px; border-bottom: 1px solid #E4E9EE; }
.profile-head img.avatar { border: 3px solid #FFFFFF; margin-top: -45px; }
h1 { font-size: 24px; margin: 6px 0 0 0; font-weight: 800; }
.stats b { color: #0B0F14; } .stats { color: #42576C; margin: 8px 0; }
.bio { margin: 8px 0; line-height: 20px; }
.grid td { padding: 2px; } .grid img { border-radius: 4px; }
.reply { border-bottom: 1px solid #E4E9EE; padding: 10px 14px 10px 44px; }
.foot { color: #42576C; font-size: 13px; padding: 12px 14px; }
.foot a { color: #42576C; }
"""
TRENDING = ["#FurryArt", "#Fursuit", "#FursuitFriday", "#MFF2025", "#Claudecadia", "#FurNet", "#ThrowbackThursday"]


# ---- data ----------------------------------------------------------------------------------------------------------
def _store():
    try:
        data = json.loads(STORE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    data.setdefault("likes", {})
    data.setdefault("reposts", {})
    return data


def _save(data):
    with _lock:
        STORE.parent.mkdir(parents=True, exist_ok=True)
        tmp = STORE.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=1), encoding="utf-8")
        tmp.replace(STORE)


def _handle(name):
    slug = "".join(ch for ch in name.lower() if ch.isalnum())
    return f"{slug or 'someone'}.bsky.social"


def _by_handle(handle):
    """The resident (or you) behind a handle, or None."""
    handle = handle.lower().removeprefix("@")
    for name in [_me()] + _people():
        if _handle(name) == handle or name.lower() == handle:
            return name
    return None


def _u(name):
    return f"/profile/{quote(_handle(name))}"


def _pic_tag(name, size=42):
    return f'<img src="/img/{quote(name)}.jpg" width="{size}" height="{size}" class="avatar" alt="">'


def _counts(owner, item):
    """Reposts and a few extra likes from the wider fandom: the same every time for a post."""
    rnd = random.Random(f"bsky/{owner}/{item}")
    return rnd.randint(0, 4), rnd.randint(0, 9)


def _reposted(owner, item, data):
    return _me() in data["reposts"].get(f"{owner}/{item}", [])


# ---- pages ---------------------------------------------------------------------------------------------------------
def _page(title, inner, active="home", right=None):
    me = _me()
    items = (("home", "/", "Home"), ("search", "/search", "Search"), ("notifications", "/notifications", "Notifications"),
             ("chat", "/chat", "Chat"), ("feeds", "/feeds", "Feeds"), ("lists", "/lists", "Lists"),
             ("profile", _u(me), "Profile"), ("settings", "/settings", "Settings"))
    nav = "".join(f'<a href="{href}"{" class=\"on\"" if key == active else ""}>{label}</a>' for key, href, label in items)
    right_col = right if right is not None else _right_column()
    return f"""<html><head><title>{e(title)} - Bluesky</title><style>{CSS}</style></head><body>
<table width="100%" cellspacing="0" cellpadding="0" style="max-width:1200px;margin:0 auto"><tr valign="top">
<td width="230" style="padding:14px 0"><div style="padding:6px 14px 10px 14px">{LOGO}</div><div class="nav">{nav}</div>
<a class="newpost" href="/#compose">New Post</a>
<div style="padding:16px 14px" class="muted">{_pic_tag(me, 36)} <b>{e(me)}</b><br>@{e(_handle(me))}</div></td>
<td id="center" width="600">{inner}</td>
<td style="padding:14px 18px">{right_col}</td></tr></table>
</body></html>"""


def _right_column():
    me = _me()
    friends = set(_friends(me))
    others = [n for n in _people() if n not in friends and n != me]
    rnd = random.Random(clock.now().strftime("%Y%m%d") + "bsky")
    suggest = rnd.sample(others, k=min(3, len(others))) if others else []
    sugg = "".join(f'<div style="margin:8px 0">{_pic_tag(n, 36)} <a href="{_u(n)}"><b>{e(n)}</b></a> '
                   f'<span class="muted">@{e(_handle(n))}</span><br><span class="muted" style="font-size:13px">'
                   f'{e((_card(n).get("summary") or "")[:90])}</span></div>' for n in suggest) or \
        "<span class='muted'>You follow everyone already.</span>"
    trends = "".join(f'<div style="margin:6px 0"><a class="blue" href="/hashtag/{quote(t[1:])}">{e(t)}</a> '
                     f'<span class="muted" style="font-size:13px">{rnd.randint(40, 900)} posts</span></div>'
                     for t in rnd.sample(TRENDING, k=5))
    return (f'<form action="/search" method="get" style="margin:0 0 12px 0"><input class="text" name="q" value="" '
            f'placeholder="Search"></form>'
            f'<div class="card"><h3>Trending</h3>{trends}</div>'
            f'<div class="card"><h3>Suggested follows</h3>{sugg}</div>'
            f'<div class="foot"><a href="/feeds">Feedback</a> &middot; <a href="/settings">Privacy</a> &middot; '
            f'<a href="/settings">Terms</a> &middot; <a href="/help">Help</a><br>Bluesky Social, PBC &copy; 2025</div>')


def _post_html(owner, p, data, thread=False):
    lj = _lj()
    item = p["id"]
    me = _me()
    likers = _likers(owner, item, data)
    liked = me in likers
    reposted = _reposted(owner, item, data)
    base_reposts, base_likes = _counts(owner, item)
    comments = lj.comments(lj.load(), owner, item)
    when = f'{e(p.get("date", ""))}' + (f' &middot; {e(p.get("time", ""))}' if p.get("time") else "")
    text = e(p.get("text", ""))
    body = (f'<div class="post"><table cellpadding="0" cellspacing="0" width="100%"><tr valign="top"><td width="54">'
            f'{_pic_tag(owner, 42)}</td><td><span class="who"><a href="{_u(owner)}">{e(owner)}</a></span> '
            f'<span class="handle">@{e(_handle(owner))}</span> <span class="time">&middot; {when}</span>'
            f'<div class="text">{text}</div>'
            f'<div class="actions"><a href="{_u(owner)}/post/{item}">&#128172; {len(comments)}</a>'
            f'<a href="/repost?owner={quote(owner)}&item={item}"{" class=\"reposted\"" if reposted else ""}>'
            f'&#128257; {base_reposts + (1 if reposted else 0)}</a>'
            f'<a href="/like?owner={quote(owner)}&item={item}"{" class=\"liked\"" if liked else ""}>'
            f'{"&#9829;" if liked else "&#9825;"} {base_likes + len(likers)}</a>'
            f'<a href="{_u(owner)}/post/{item}">Share</a></div></td></tr></table></div>')
    if not thread:
        return body
    replies = "".join(f'<div class="reply">{_pic_tag(c["who"], 32)} <span class="who"><a href="{_u(c["who"])}">'
                      f'{e(c["who"])}</a></span> <span class="handle">@{e(_handle(c["who"]))}</span> '
                      f'<span class="time">&middot; {e(c.get("date", ""))}</span>'
                      f'<div class="text">{e(c["text"])}</div></div>' for c in comments)
    form = (f'<form class="compose" method="post" action="/reply" style="margin:0"><input type="hidden" name="owner" '
            f'value="{e(owner)}"><input type="hidden" name="item" value="{item}">'
            f'<table width="100%"><tr valign="top"><td width="54">{_pic_tag(me, 42)}</td><td>'
            f'<textarea class="compose" name="text" rows="2" placeholder="Write your reply"></textarea>'
            f'<div style="text-align:right"><input class="btn" type="submit" value="Reply"></div></td></tr></table></form>')
    return body + form + replies


class Bluesky(Site):
    host = HOST
    aliases = ("bsky.social", "www.bsky.app", "blueskyweb.xyz")
    title = "Bluesky"
    blurb = "Where the fandom went"

    def installed(self):
        return True

    # ---- GET ----
    def handle(self, path, query):
        q = {k: v[0] for k, v in parse_qs(query, keep_blank_values=True).items()}
        if path in ("/", "/home", "/index.html"):
            return self._home(q.get("feed", "following"))
        if path.startswith("/img/"):
            return self._img(unquote(path[5:]).removesuffix(".jpg"))
        if path.startswith("/media/"):
            return self._media_file(path[7:])
        if path == "/like":
            return self._toggle("likes", q.get("owner", ""), q.get("item", ""))
        if path == "/repost":
            return self._toggle("reposts", q.get("owner", ""), q.get("item", ""))
        if path == "/search":
            return self._search(q.get("q", ""))
        if path.startswith("/hashtag/"):
            return self._search("#" + unquote(path[9:]))
        if path in ("/notifications", "/chat", "/feeds", "/lists", "/settings", "/help"):
            return self._simple(path.strip("/"))
        if path.startswith("/profile/"):
            handle, _, rest = path[9:].strip("/").partition("/")
            name = _by_handle(unquote(handle))
            if name is None:
                return None
            if rest == "":
                return self._profile(name, "posts")
            if rest in ("replies", "media", "likes"):
                return self._profile(name, rest)
            if rest in ("follows", "followers"):
                return self._follows(name, rest)
            if rest.startswith("post/"):
                return self._thread(name, rest[5:])
        return None

    # ---- POST ----
    def handle_post(self, path, query, form):
        f = {k: v[-1] for k, v in form.items()}
        if path == "/post":
            return self._do_post(f.get("text", "").strip())
        if path == "/reply":
            return self._do_reply(f.get("owner", ""), f.get("item", ""), f.get("text", "").strip())
        return None

    # ---- the timeline ----
    def _feed_items(self, feed):
        me = _me()
        names = [me] + (list(_friends(me)) if feed == "following" else _people())
        items = []
        for name in dict.fromkeys(names):
            if not _known(name):
                continue
            for p in _posts(name)[:8]:
                items.append((p["id"], name, p))
        items.sort(key=lambda t: t[0], reverse=True)
        return items

    def _home(self, feed):
        data = _store()
        items = self._feed_items(feed)
        posts = "".join(_post_html(owner, p, data) for _id, owner, p in items[:FEED_SIZE]) or \
            "<div class='post muted'>Nothing here yet. Your friends' posts show up as they write them.</div>"
        tabs = "".join(f'<a href="/?feed={key}"{" class=\"on\"" if key == feed else ""}>{label}</a>'
                       for key, label in (("following", "Following"), ("discover", "Discover"), ("fandom", "Furry Fandom")))
        compose = (f'<form class="compose" method="post" action="/post" style="margin:0" id="compose"><table width="100%">'
                   f'<tr valign="top"><td width="54">{_pic_tag(_me(), 42)}</td><td>'
                   f'<textarea class="compose" name="text" rows="2" placeholder="What\'s up?"></textarea>'
                   f'<div style="text-align:right"><span class="muted" style="font-size:13px;margin-right:12px">300</span>'
                   f'<input class="btn" type="submit" value="Post"></div></td></tr></table></form>')
        return _page("Home", f'<div class="tabs">{tabs}</div>{compose}{posts}', active="home")

    # ---- profiles ----
    def _head(self, name, active):
        me = _me()
        card = _card(name)
        personal = card.get("personal") or {}
        bio_bits = [card.get("summary", "")]
        if personal.get("location"):
            bio_bits.append(f"&#128205; {e(personal['location'])}")
        bd = _birthday(name)
        if bd:
            import datetime
            bio_bits.append("&#127874; " + datetime.date(2000, bd[0], bd[1]).strftime("%B %d").replace(" 0", " "))
        friends = _friends(name)
        rnd = random.Random("bsky-stats/" + name)
        followers = len(friends) + rnd.randint(20, 400)
        posts = len(_posts(name))
        tabs = "".join(f'<a href="{_u(name)}{href}"{" class=\"on\"" if key == active else ""}>{label}</a>'
                       for key, href, label in (("posts", "", "Posts"), ("replies", "/replies", "Replies"),
                                                ("media", "/media", "Media"), ("likes", "/likes", "Likes")))
        button = ('<span class="btn ghost">Edit Profile</span>' if name == me else
                  f'<a href="/chat"><span class="btn ghost">&#128172; Message</span></a> <span class="btn">Following</span>')
        return (f'<div class="banner"></div><div class="profile-head"><table width="100%"><tr valign="bottom">'
                f'<td>{_pic_tag(name, 90)}</td><td align="right" style="padding-top:12px">{button}</td></tr></table>'
                f'<h1>{e(name)}</h1><div class="muted">@{e(_handle(name))}</div>'
                f'<div class="stats"><a href="{_u(name)}/followers"><b>{followers}</b> followers</a> &nbsp; '
                f'<a href="{_u(name)}/follows"><b>{len(friends)}</b> following</a> &nbsp; <b>{posts}</b> posts</div>'
                f'<div class="bio">{" &middot; ".join(b if b.startswith("&#") else e(b) for b in bio_bits if b)}</div></div>'
                f'<div class="tabs">{tabs}</div>')

    def _profile(self, name, tab):
        data = _store()
        if tab == "media":
            pics = _photos(name)
            cells = "".join(f'<td><a href="/media/{quote(name)}/{quote(p.name)}"><img src="/media/{quote(name)}/{quote(p.name)}" '
                            f'width="190" height="190" style="object-fit:cover" alt=""></a></td>' for p, _c in pics[:30])
            rows = "".join(f"<tr>{r}</tr>" for r in _rows(cells.split("</td>"), 3))
            body = f'<table class="grid">{rows}</table>' if pics else "<div class='post muted'>No media yet.</div>"
        elif tab == "likes":
            liked = [key for key, names in data["likes"].items() if _me() in names] if name == _me() else []
            items = []
            for key in liked:
                owner, _, item = key.partition("/")
                post = next((p for p in _posts(owner) if str(p["id"]) == item), None) if _known(owner) else None
                if post is not None:
                    items.append((post["id"], owner, post))
            items.sort(key=lambda t: t[0], reverse=True)
            body = "".join(_post_html(o, p, data) for _i, o, p in items) or \
                "<div class='post muted'>Likes are private on Bluesky.</div>"
        elif tab == "replies":
            lj = _lj()
            store = lj.load()
            mine = []
            for other in [_me()] + _people():
                for p in _posts(other)[:10]:
                    for c in lj.comments(store, other, p["id"]):
                        if c.get("who") == name:
                            mine.append((p["id"], other, p, c))
            mine.sort(key=lambda t: t[0], reverse=True)
            body = "".join(f'<div class="post"><div class="muted" style="font-size:13px">Replying to '
                           f'<a class="blue" href="{_u(o)}/post/{p["id"]}">@{e(_handle(o))}</a></div>'
                           f'<div class="text">{e(c["text"])}</div><div class="time">{e(c.get("date", ""))}</div></div>'
                           for _i, o, p, c in mine[:30]) or "<div class='post muted'>No replies yet.</div>"
        else:
            body = "".join(_post_html(name, p, data) for p in _posts(name)[:30]) or \
                "<div class='post muted'>No posts yet.</div>"
        return _page(name, self._head(name, tab) + body, active="profile" if name == _me() else "")

    def _follows(self, name, which):
        people = _friends(name)
        if which == "followers":
            rnd = random.Random("bsky-followers/" + name)
            extra = [n for n in _people() if n not in people and n != name]
            people = people + rnd.sample(extra, k=min(5, len(extra)))
        rows = "".join(f'<div class="post">{_pic_tag(n, 42)} <a href="{_u(n)}"><b>{e(n)}</b></a> '
                       f'<span class="muted">@{e(_handle(n))}</span><br><span class="muted" style="font-size:13px">'
                       f'{e((_card(n).get("summary") or "")[:120])}</span></div>' for n in people) or \
            "<div class='post muted'>Nobody yet.</div>"
        label = "Followers" if which == "followers" else "Following"
        return _page(f"{name} - {label}", f'<div class="post"><a href="{_u(name)}">&larr;</a> <b>{e(name)}</b> '
                     f'<span class="muted">{label}</span></div>{rows}', active="")

    def _thread(self, name, item):
        if not item.isdigit():
            return redirect(_u(name))
        post = next((p for p in _posts(name) if str(p["id"]) == item), None)
        if post is None:
            return redirect(_u(name))
        return _page("Post", f'<div class="post"><a href="/">&larr;</a> <b>Post</b></div>'
                     + _post_html(name, post, _store(), thread=True), active="")

    # ---- files ----
    def _img(self, name):
        path = _picture_path(name)
        if path is not None:
            return file_response(path)
        return Response(_default_pic(name), "image/svg+xml")

    def _media_file(self, rest):
        name, _, filename = rest.partition("/")
        name, filename = unquote(name), unquote(filename)
        for p, _cap in _photos(name):
            if p.name == filename:
                return file_response(p)
        return None

    # ---- search and the simple pages ----
    def _search(self, q):
        q = q.strip()
        ql = q.lower()
        people = [n for n in [_me()] + _people() if ql and (ql.lstrip("@") in n.lower() or ql.lstrip("@") in _handle(n))]
        data = _store()
        posts = []
        if ql and not ql.startswith("@"):
            for name in [_me()] + _people():
                for p in _posts(name)[:10]:
                    if ql.lstrip("#") in p.get("text", "").lower():
                        posts.append((p["id"], name, p))
        posts.sort(key=lambda t: t[0], reverse=True)
        who = "".join(f'<div class="post">{_pic_tag(n, 42)} <a href="{_u(n)}"><b>{e(n)}</b></a> '
                      f'<span class="muted">@{e(_handle(n))}</span></div>' for n in people)
        found = "".join(_post_html(o, p, data) for _i, o, p in posts[:20])
        body = (f'<div class="compose"><form action="/search" method="get" style="margin:0"><input class="text" name="q" '
                f'value="{e(q)}" placeholder="Search for people, posts or tags"></form></div>'
                + (f'<div class="post"><b>People</b></div>{who}' if who else "")
                + (f'<div class="post"><b>Posts</b></div>{found}' if found else "")
                + ("" if (who or found or not q) else "<div class='post muted'>No results.</div>"))
        return _page("Search", body, active="search")

    def _simple(self, what):
        me = _me()
        texts = {
            "notifications": [("Notifications", "When your friends like or reply to a post, it shows up here. Nothing new "
                                                "right now.")],
            "chat": [("Chat", "Direct messages live in Telegram and Discord on this computer; Bluesky's chat is for "
                              "people you don't have anywhere else.")],
            "feeds": [("Feeds", "Following, Discover, Furry Fandom, Fursuit Friday, FurNet Regulars - custom feeds built by "
                                "the community.")],
            "lists": [("Lists", "FurNet Regulars, PawPrints MUCK, Con Buddies. Add people to a list from their profile.")],
            "settings": [("Settings", f"Account: @{_handle(me)}. Appearance: light. Moderation, Privacy and security, "
                                      f"Accessibility, Languages, About. (This is a Claude11 page: nothing to set.)")],
            "help": [("Help", "Bluesky is an open social network. Posts are 300 characters; the timeline is just your "
                              "follows, in order.")],
        }
        title, text = texts.get(what, [(what.capitalize(), "")])[0]
        return _page(title, f'<div class="post"><b>{e(title)}</b></div><div class="post">{e(text)}</div>',
                     active=what)

    # ---- actions ----
    def _toggle(self, kind, owner, item):
        if not (_known(owner) and item.isdigit()):
            return redirect("/")
        key = f"{owner}/{item}"
        me = _me()
        with _lock:
            data = _store()
            names = data[kind].setdefault(key, [])
            if me in names:
                names.remove(me)
            else:
                names.append(me)
            _save(data)
        return redirect("/")

    def _do_post(self, text):
        if not text:
            return redirect("/")
        lj = _lj()
        friends = _friends(_me())

        def change(data):
            entry = lj.new_entry(data, "", text[:300], "", "", "public")
            entry["date"] = entry["date"].replace("2001", str(clock.YEAR))
            lj.queue_comments_on(data, entry, friends)
        lj.update(change)
        return redirect("/")

    def _do_reply(self, owner, item, text):
        if not (_known(owner) and item.isdigit() and text):
            return redirect("/")
        lj = _lj()
        me = _me()

        def change(data):
            lj.add_comment(data, owner, int(item), me, text[:300])
            if owner != me:
                lj.queue_reply(data, owner, int(item), text[:300])
        lj.update(change)
        return redirect(f"{_u(owner)}/post/{item}")


def _rows(cells, n):
    cells = [c + "</td>" for c in cells if c.strip()]
    return ["".join(cells[i:i + n]) for i in range(0, len(cells), n)]
