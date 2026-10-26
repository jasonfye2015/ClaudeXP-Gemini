"""Bluesky, as the user's own profile: http://bsky.app/profile/<handle>, built from the copy the Bluesky watcher keeps
in Local Storage/Bsky-Kithy (claudexp/bsky.py). Read-only: there's no signing in, replying or liking here - it's
their posts, pictures and videos, kept.

    /                                   -> their profile
    /profile/<handle>[?tab=&page=]      posts, replies, media, reposts
    /profile/<handle>/post/<rkey>       one post (with what it replied to)
    /media/<file>                       a picture or video from the copy

Videos are H.264, which this browser engine can't play: a video's picture links to the .mp4, which the browser opens
in the system's video player (see webview.py)."""
import html
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, quote

from . import Response, Site, file_response, redirect

PER_PAGE = 20
TABS = [("posts", "Posts"), ("replies", "Replies"), ("media", "Media"), ("reposts", "Reposts")]

CSS = """
*{box-sizing:border-box} body{margin:0;background:#f1f3f5;font:15px/1.45 -apple-system,"Segoe UI",Arial,sans-serif;
color:#0b0f14} a{color:#1083fe;text-decoration:none} a:hover{text-decoration:underline}
.top{background:#fff;border-bottom:1px solid #e3e8ec;padding:10px 16px;display:flex;align-items:center;gap:10px}
.top .logo{color:#1083fe;font-weight:700;font-size:20px} .top .note{color:#6f869f;font-size:13px;margin-left:auto}
.wrap{max-width:640px;margin:0 auto;background:#fff;border-left:1px solid #e3e8ec;border-right:1px solid #e3e8ec;
min-height:100vh} .banner{height:160px;background:#1083fe;overflow:hidden} .banner img{width:100%;height:100%;
object-fit:cover;display:block}
.head{padding:0 16px 12px;position:relative} .avatar{width:92px;height:92px;border-radius:50%;border:4px solid #fff;
margin-top:-46px;background:#cfd9e2;object-fit:cover} .name{font-size:26px;font-weight:700;margin:6px 0 0}
.handle{color:#6f869f} .counts{margin:8px 0;color:#42576c} .counts b{color:#0b0f14} .bio{white-space:pre-wrap}
.tabs{display:flex;border-bottom:1px solid #e3e8ec} .tabs a{flex:1;text-align:center;padding:12px 0;color:#6f869f;
font-weight:600} .tabs a.on{color:#0b0f14;border-bottom:3px solid #1083fe} .tabs a:hover{text-decoration:none;
background:#f6f8fa} .post{display:flex;gap:10px;padding:12px 16px;border-bottom:1px solid #e3e8ec}
.post .pic{width:44px;height:44px;border-radius:50%;object-fit:cover;flex:none;background:#cfd9e2}
.post .body{flex:1;min-width:0} .meta{color:#6f869f;font-size:14px} .meta b{color:#0b0f14}
.text{white-space:pre-wrap;word-wrap:break-word;margin:2px 0 6px} .ctx{color:#6f869f;font-size:13px;margin-bottom:2px}
.imgs{display:grid;gap:4px;border-radius:12px;overflow:hidden;margin:6px 0} .imgs.n1{grid-template-columns:1fr}
.imgs.n2,.imgs.n4{grid-template-columns:1fr 1fr} .imgs.n3{grid-template-columns:1fr 1fr 1fr}
.imgs.many{grid-template-columns:1fr 1fr 1fr} .imgs img{width:100%;height:100%;object-fit:cover;display:block;
max-height:420px} .imgs.n1 img{max-height:520px;object-fit:contain;background:#000}
.video{position:relative;display:block;border-radius:12px;overflow:hidden;background:#000;margin:6px 0}
.video{max-height:420px} .video img{width:100%;height:100%;display:block;object-fit:contain;opacity:.92} .video .play{position:absolute;
left:50%;top:50%;width:64px;height:64px;margin:-32px 0 0 -32px;border-radius:50%;background:rgba(0,0,0,.6);
color:#fff;font-size:30px;line-height:64px;text-align:center} .video .tag{position:absolute;left:8px;bottom:8px;
background:rgba(0,0,0,.6);color:#fff;font-size:12px;padding:2px 6px;border-radius:4px}
.quote,.card{border:1px solid #e3e8ec;border-radius:12px;padding:10px;margin:6px 0;display:block;color:inherit}
.card img{width:100%;max-height:260px;object-fit:cover;border-radius:8px} .card .t{font-weight:600}
.card .d,.card .u{color:#6f869f;font-size:13px} .stats{color:#6f869f;font-size:13px;display:flex;gap:18px}
.alt{color:#6f869f;font-size:12px} .pager{display:flex;justify-content:space-between;padding:14px 16px}
.mediagrid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:3px;padding:3px} .mediagrid a{display:block;
aspect-ratio:1/1;overflow:hidden;position:relative;background:#000} .mediagrid img{width:100%;height:100%;
object-fit:cover} .mediagrid .v{position:absolute;right:6px;bottom:6px;color:#fff;font-size:13px;
background:rgba(0,0,0,.6);padding:1px 5px;border-radius:4px} .empty{padding:40px 16px;color:#6f869f;
text-align:center} .parent{opacity:.85}
"""


def _root():
    from .... import bsky
    return bsky.folder()


def _load(sub):
    out = []
    d = _root() / sub
    for p in d.glob("*.json") if d.is_dir() else ():
        try:
            out.append(json.loads(p.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            pass
    out.sort(key=lambda r: _created(r["item"]["post"]), reverse=True)
    return out


def _created(post):
    return (post.get("record") or {}).get("createdAt") or post.get("indexedAt") or ""


def _when(iso, long=False):
    try:
        t = datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone()
    except ValueError:
        return ""
    if long:
        return f"{t:%B} {t.day}, {t.year} at {t:%I:%M %p}".replace(" 0", " ")
    return f"{t:%b} {t.day}, {t.year}"


def _rich(record):
    """A post's text with its links, mentions and hashtags (facets index UTF-8 bytes)."""
    text = record.get("text") or ""
    raw = text.encode("utf-8")
    spans = []
    for f in record.get("facets") or []:
        idx = f.get("index") or {}
        a, b = idx.get("byteStart"), idx.get("byteEnd")
        feat = (f.get("features") or [{}])[0]
        if a is None or b is None or not (0 <= a < b <= len(raw)):
            continue
        spans.append((a, b, feat))
    spans.sort(key=lambda s: s[0])
    out, pos = [], 0
    for a, b, feat in spans:
        if a < pos:
            continue
        out.append(html.escape(raw[pos:a].decode("utf-8", "replace")))
        inner = html.escape(raw[a:b].decode("utf-8", "replace"))
        kind = feat.get("$type", "")
        if kind.endswith("#link"):
            out.append(f'<a href="{html.escape(feat.get("uri", ""))}">{inner}</a>')
        elif kind.endswith("#mention"):
            out.append(f'<a href="/profile/{quote(feat.get("did", ""))}">{inner}</a>')
        else:
            out.append(f"<b>{inner}</b>")
        pos = b
    out.append(html.escape(raw[pos:].decode("utf-8", "replace")))
    return "".join(out)


class Bluesky(Site):
    host = "bsky.app"
    aliases = ("www.bsky.app", "bsky.social", "kithy.bsky.social")
    title = "Kithy on Bluesky"
    blurb = "your Bluesky posts, pictures and videos, kept on this computer"

    def installed(self):
        return True

    # ---- the copy ----
    def profile(self):
        try:
            return json.loads((_root() / "profile.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None

    def _media_url(self, rec, key):
        """A local address for a cid or CDN url this post kept, else the original address."""
        name = (rec.get("files") or {}).get(key)
        return f"/media/{quote(name)}" if name else key

    def _is_me(self, who, prof):
        return who in (prof.get("handle"), prof.get("did"))

    # ---- GET ----
    def handle(self, path, query):
        q = {k: v[0] for k, v in parse_qs(query).items()}
        prof = self.profile()
        if path.startswith("/media/"):
            target = (_root() / "media" / Path(path[7:]).name)
            return file_response(target)
        if prof is None:
            return self._page("Bluesky", '<div class="empty">Your Bluesky posts haven\'t been copied yet. The '
                                         'Bluesky watcher fetches them in the background: come back in a few '
                                         'minutes.</div>')
        me = f"/profile/{prof['handle']}"
        if path in ("/", "", "/profile", "/profile/"):
            return redirect(me)
        parts = [p for p in path.split("/") if p]
        if len(parts) >= 2 and parts[0] == "profile":
            if not self._is_me(parts[1], prof):
                return self._page("Bluesky", f'<div class="empty">Only {html.escape(prof.get("displayName") or prof["handle"])}\'s '
                                             f'own posts are kept on this computer.<br><br><a href="{me}">Back to '
                                             'the profile</a></div>', prof)
            if len(parts) == 2:
                return self._profile(prof, q.get("tab", "posts"), int(q.get("page", "1") or 1))
            if len(parts) == 4 and parts[2] == "post":
                return self._thread(prof, parts[3])
        return None

    # ---- pages ----
    def _page(self, title, body, prof=None):
        top = ('<div class="top"><span class="logo">&#x1F98B; Bluesky</span>'
               '<span class="note">A copy kept on this computer - read only</span></div>')
        return Response(f'<!DOCTYPE html><html><head><meta charset="utf-8"><title>{html.escape(title)}</title>'
                        f'<style>{CSS}</style></head><body>{top}<div class="wrap">{body}</div></body></html>')

    def _profile(self, prof, tab, page):
        if tab not in dict(TABS):
            tab = "posts"
        me = f"/profile/{prof['handle']}"
        avatar = f'/media/{quote(prof["local_avatar"])}' if prof.get("local_avatar") else ""
        banner = f'/media/{quote(prof["local_banner"])}' if prof.get("local_banner") else ""
        head = (f'<div class="banner">{f"<img src={chr(34)}{banner}{chr(34)} alt={chr(34)}{chr(34)}>" if banner else ""}</div>'
                f'<div class="head"><img class="avatar" src="{avatar}" alt="">'
                f'<div class="name">{html.escape(prof.get("displayName") or prof["handle"])}</div>'
                f'<div class="handle">@{html.escape(prof["handle"])}</div>'
                f'<div class="counts"><b>{prof.get("followersCount", 0)}</b> followers &nbsp; '
                f'<b>{prof.get("followsCount", 0)}</b> following &nbsp; <b>{prof.get("postsCount", 0)}</b> posts</div>'
                f'<div class="bio">{html.escape(prof.get("description") or "")}</div></div>')
        tabs = '<div class="tabs">' + "".join(
            f'<a href="{me}?tab={k}"{" class=on" if k == tab else ""}>{t}</a>' for k, t in TABS) + "</div>"
        if tab == "reposts":
            recs = _load("reposts")
        else:
            recs = _load("posts")
            if tab == "posts":
                recs = [r for r in recs if r.get("kind") != "reply"]
            elif tab == "replies":
                recs = [r for r in recs if r.get("kind") == "reply"]
        if tab == "media":
            return self._page(f"{prof.get('displayName') or prof['handle']} - Media", head + tabs
                              + self._media_grid(prof, recs), prof)
        total = len(recs)
        page = max(1, min(page, max(1, -(-total // PER_PAGE))))
        shown = recs[(page - 1) * PER_PAGE:page * PER_PAGE]
        body = "".join(self._post(prof, r) for r in shown) or '<div class="empty">Nothing here yet.</div>'
        pager = '<div class="pager">'
        pager += f'<a href="{me}?tab={tab}&page={page - 1}">&larr; Newer</a>' if page > 1 else "<span></span>"
        pager += (f'<a href="{me}?tab={tab}&page={page + 1}">Older &rarr;</a>' if page * PER_PAGE < total
                  else "<span></span>")
        pager += "</div>"
        return self._page(f"{prof.get('displayName') or prof['handle']} (@{prof['handle']}) - Bluesky",
                          head + tabs + body + pager, prof)

    def _media_grid(self, prof, recs):
        cells = []
        for r in recs:
            post = r["item"]["post"]
            link = f"/profile/{prof['handle']}/post/{post['uri'].rsplit('/', 1)[-1]}"
            for kind, src, _full in self._pictures(r, post.get("embed") or {}):
                cells.append(f'<a href="{link}"><img src="{src}" alt="" loading="lazy">'
                             + ('<span class="v">&#9654; video</span>' if kind == "video" else "") + "</a>")
        return ('<div class="mediagrid">' + "".join(cells) + "</div>") if cells else \
            '<div class="empty">No pictures yet.</div>'

    def _pictures(self, rec, view):
        """[(kind, picture src, full-size / video src)] for an embed view (images, gallery, video, with media)."""
        t = view.get("$type", "")
        if t.endswith("recordWithMedia#view"):
            return self._pictures(rec, view.get("media") or {})
        out = []
        if t.endswith("images#view") or t.endswith("gallery#view"):
            for im in view.get("images") or view.get("items") or []:
                full = im.get("fullsize") or ""
                cid = full.rstrip("/").split("/")[-1].split("@")[0]
                big = self._media_url(rec, cid) if cid in (rec.get("files") or {}) else self._media_url(rec, full)
                small = self._media_url(rec, im.get("thumb") or im.get("thumbnail") or full)
                out.append(("image", small if small.startswith("/media/") else big, big))
        elif t.endswith("video#view"):
            cid = view.get("cid", "")
            out.append(("video", self._media_url(rec, view.get("thumbnail", "")), self._media_url(rec, cid)))
        return out

    def _embed(self, rec, view):
        t = view.get("$type", "")
        out = []
        pics = self._pictures(rec, view)
        imgs = [(s, f) for k, s, f in pics if k == "image"]
        if imgs:
            n = len(imgs)
            cls = f"n{n}" if n <= 4 else "many"
            out.append(f'<div class="imgs {cls}">' + "".join(
                f'<a href="{f}"><img src="{s}" alt="" loading="lazy"></a>' for s, f in imgs) + "</div>")
            alts = [im.get("alt") for im in (view.get("images") or view.get("items") or
                                              (view.get("media") or {}).get("images") or []) if im.get("alt")]
            if alts:
                out.append('<div class="alt">' + " / ".join(html.escape(a) for a in alts) + "</div>")
        ratio = (view.get("aspectRatio") or (view.get("media") or {}).get("aspectRatio") or {})
        shape = f' style="aspect-ratio:{ratio["width"]}/{ratio["height"]}"' if ratio.get("width") else ""
        for k, s, f in pics:
            if k == "video":
                out.append(f'<a class="video" href="{f}"{shape}><img src="{s}" alt=""><span class="play">&#9654;</span>'
                           '<span class="tag">Opens in your video player</span></a>')
        ext = view.get("external") or (view.get("media") or {}).get("external")
        if ext:
            thumb = self._media_url(rec, ext["thumb"]) if ext.get("thumb") else ""
            out.append(f'<a class="card" href="{html.escape(ext.get("uri", ""))}">'
                       + (f'<img src="{thumb}" alt="">' if thumb else "")
                       + f'<div class="t">{html.escape(ext.get("title") or "")}</div>'
                       f'<div class="d">{html.escape(ext.get("description") or "")}</div>'
                       f'<div class="u">{html.escape(ext.get("uri") or "")}</div></a>')
        quoted = view.get("record") if t.endswith("record#view") else (view.get("record") or {}).get("record") \
            if t.endswith("recordWithMedia#view") else None
        if isinstance(quoted, dict) and quoted.get("value"):
            a = quoted.get("author") or {}
            inner = "".join(self._embed(rec, e) for e in quoted.get("embeds") or [])
            out.append(f'<div class="quote"><div class="meta"><b>{html.escape(a.get("displayName") or a.get("handle", ""))}</b> '
                       f'@{html.escape(a.get("handle", ""))} &middot; {_when(quoted["value"].get("createdAt", ""))}</div>'
                       f'<div class="text">{_rich(quoted["value"])}</div>{inner}</div>')
        return "".join(out)

    def _post(self, prof, rec, link=True, big=False, post=None, ctx=True):
        post = post or rec["item"]["post"]
        a = post.get("author") or {}
        record = post.get("record") or {}
        rkey = post["uri"].rsplit("/", 1)[-1]
        mine = a.get("did") == prof.get("did")
        url = f"/profile/{prof['handle']}/post/{rkey}" if mine else ""
        pic = self._media_url(rec, a.get("avatar", "")) if a.get("avatar") else ""
        note = ""
        if ctx and rec.get("kind") == "repost" and post is rec["item"]["post"]:
            note = f'<div class="ctx">&#x1F501; Reposted by {html.escape(prof.get("displayName") or prof["handle"])}</div>'
        elif ctx and "reply" in record:
            parent = ((rec["item"].get("reply") or {}).get("parent") or {}).get("author") or {}
            if parent.get("handle"):
                note = f'<div class="ctx">&#x21AA; Replying to @{html.escape(parent["handle"])}</div>'
        when = _when(_created(post), long=big)
        stamp = f'<a href="{url}">{when}</a>' if url and link else when
        stats = (f'<div class="stats"><span>&#x1F4AC; {post.get("replyCount", 0)}</span>'
                 f'<span>&#x1F501; {post.get("repostCount", 0) + post.get("quoteCount", 0)}</span>'
                 f'<span>&#x2661; {post.get("likeCount", 0)}</span></div>')
        return (f'<div class="post{" big" if big else ""}"><img class="pic" src="{pic}" alt="">'
                f'<div class="body">{note}<div class="meta"><b>{html.escape(a.get("displayName") or a.get("handle", ""))}</b> '
                f'@{html.escape(a.get("handle", ""))} &middot; {stamp}</div>'
                f'<div class="text"{" style=font-size:18px" if big else ""}>{_rich(record)}</div>'
                f'{self._embed(rec, post.get("embed") or {})}{stats}</div></div>')

    def _thread(self, prof, rkey):
        path = _root() / "posts" / f"{Path(rkey).name}.json"
        try:
            rec = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return self._page("Bluesky", '<div class="empty">That post isn\'t in the copy kept here.<br><br>'
                                         f'<a href="/profile/{prof["handle"]}">Back to the profile</a></div>', prof)
        above = ""
        reply = rec["item"].get("reply") or {}
        for key in ("root", "parent"):
            p = reply.get(key)
            if p and p.get("uri") and p.get("record") is not None and (key == "parent" or
                                                                       p["uri"] != (reply.get("parent") or {}).get("uri")):
                above += '<div class="parent">' + self._post(prof, rec, post=p, ctx=False) + "</div>"
        body = (f'<div class="pager"><a href="/profile/{prof["handle"]}">&larr; {html.escape(prof.get("displayName") or prof["handle"])}</a>'
                "<span></span></div>" + above + self._post(prof, rec, link=False, big=True))
        text = (rec["item"]["post"].get("record") or {}).get("text") or "Post"
        return self._page(f"{prof.get('displayName') or prof['handle']}: \"{text[:60]}\" - Bluesky", body, prof)
