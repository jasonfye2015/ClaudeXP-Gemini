"""The Bluesky watcher: keeps a copy of the user's Bluesky account on this computer, for every system.

Started at boot by each desktop (XP, 7 and 11), it syncs once and then every SYNC_MINUTES while the system is on:
the profile, every post and reply (and what was reposted), and their pictures and videos - the originals, from the
account's own data server. Everything lands in Local Storage/Bsky-Kithy, which the Furry Web's Bluesky site
(programs/navigator/sites/bluesky.py) shows at http://bsky.app/profile/<handle>, read-only.

    profile.json, avatar.*, banner.*    the profile as of the last sync
    posts/<rkey>.json                   each post or reply of theirs: the feed item as Bluesky gave it, and "files"
    reposts/<rkey>.json                 posts by others that they reposted
    media/<cid>.*                       their own pictures and videos, as uploaded
    media/u-<hash>.*                    other pictures the pages need (thumbnails, others' avatars and pictures)
    state.json                          the account's DID and data server, whether the back catalogue is in, the
                                        last sync

Only Bluesky's public API is used (no sign-in): what anyone can see on the profile is what gets kept. Posts deleted
on Bluesky stay here."""
import hashlib
import json
import mimetypes
import os
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HANDLE = "kithy.bsky.social"
FOLDER_NAME = "Bsky-Kithy"
API = "https://public.api.bsky.app/xrpc/"
SYNC_MINUTES = 15
PAGE = 100
MEDIA_VERSION = 2               # what's kept for a post (2: thumbnails as well as originals)
URL_KEYS = ("thumb", "fullsize", "thumbnail", "avatar", "banner")
EXT = {"image/jpeg": ".jpg", "image/png": ".png", "image/gif": ".gif", "image/webp": ".webp", "video/mp4": ".mp4",
       "video/quicktime": ".mov", "video/webm": ".webm"}

MINUTES_CHOICES = (5, 15, 30, 60, 180)
SETTINGS = {"minutes": SYNC_MINUTES, "paused": False, "popup": True}     # watcher.json in the folder

_lock = threading.Lock()                # one sync at a time in this process
_thread = None
_wake = threading.Event()               # set: sync now (the tray's Sync now, a changed setting)
# how it's going, read by the tray (on the UI thread) while the watcher's thread writes it
_status = {"state": "not started", "last": None, "new": 0, "error": "", "phase": "", "done": 0, "total": 0,
           "files": 0, "bytes": 0, "recent": [], "kept": 0, "manual": False, "next": None}


def folder():
    from claudecore import host
    try:
        base = host.local_storage()
    except Exception:
        base = Path(__file__).resolve().parents[2] / "Local Storage"
    return Path(base) / FOLDER_NAME


def status():
    """How the watcher is doing: state ("syncing", "watching", "waiting", "paused"), last (time of the last good
    sync), new, error; while syncing: phase, done of total posts gone through, files and bytes downloaded, recent (the
    last downloads' sizes, for the tray's chart); kept (posts on this computer); next (time of the next sync)."""
    out = dict(_status)
    out["recent"] = list(_status["recent"])
    return out


def settings():
    return {**SETTINGS, **(_read_json(folder() / "watcher.json", {}) or {})}


def set_setting(key, value):
    s = settings()
    s[key] = value
    _write_json(folder() / "watcher.json", s)
    _wake.set()                                         # (the loop picks up a new interval or a pause at once)


def sync_now():
    """Sync as soon as the watcher can (the tray's Sync now)."""
    _status["manual"] = True
    set_setting("paused", False) if settings().get("paused") else _wake.set()


def kept():
    d = folder() / "posts"
    return sum(1 for _ in d.glob("*.json")) if d.is_dir() else 0


def _downloaded(size):
    _status["files"] += 1
    _status["bytes"] += size
    _status["recent"] = (_status["recent"] + [size])[-40:]


# ---- files --------------------------------------------------------------------------------------------------------
def _read_json(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _part(path):
    """A temporary name of this process's own: XP, 7 and 11 may all be syncing at once."""
    return path.with_name(f"{path.name}.{os.getpid()}.part")


def _write_json(path, data):
    """Written whole or not at all (another system may be reading it)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, ensure_ascii=False, indent=1)
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return False
    tmp = _part(path)
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)
    return True


def _get(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": "ClaudeTimeline-BskyWatcher/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(), r.headers.get("Content-Type", "")


def _api(method, **params):
    data, _ctype = _get(API + method + "?" + urllib.parse.urlencode(params))
    return json.loads(data)


def _save_file(path, url):
    """Download url to path (once). Returns the file name, or None if it couldn't be fetched."""
    path = Path(path)
    if path.exists():
        return path.name
    try:
        data, _ctype = _get(url, timeout=180)
    except (urllib.error.URLError, OSError, ValueError):
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = _part(path)
    tmp.write_bytes(data)
    tmp.replace(path)
    _downloaded(len(data))
    return path.name


def sniff(data, ctype=""):
    """A file ending for downloaded bytes: from the bytes themselves (video thumbnails come as octet-stream)."""
    head = data[:16]
    if head.startswith(b"\xff\xd8"):
        return ".jpg"
    if head.startswith(b"\x89PNG"):
        return ".png"
    if head.startswith(b"GIF8"):
        return ".gif"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return ".webp"
    ctype = ctype.split(";")[0].strip()
    return EXT.get(ctype) or mimetypes.guess_extension(ctype) or ".bin"


def _save_url(media, url):
    """A picture from Bluesky's CDN, named by its address."""
    name = "u-" + hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]
    existing = next(iter(media.glob(name + ".*")), None)
    if existing is not None:
        return existing.name
    try:
        data, ctype = _get(url, timeout=120)
    except (urllib.error.URLError, OSError, ValueError):
        return None
    ext = sniff(data, ctype)
    path = media / (name + ext)
    media.mkdir(parents=True, exist_ok=True)
    tmp = _part(path)
    tmp.write_bytes(data)
    tmp.replace(path)
    _downloaded(len(data))
    return path.name


# ---- what a post needs ----------------------------------------------------------------------------------------------
def _blobs(value, out):
    """Every blob (picture, video) a record refers to: [(cid, mime type)]."""
    if isinstance(value, dict):
        if value.get("$type") == "blob" and isinstance(value.get("ref"), dict):
            out.append((value["ref"].get("$link"), value.get("mimeType", "")))
        for v in value.values():
            _blobs(v, out)
    elif isinstance(value, list):
        for v in value:
            _blobs(v, out)
    return out


def _urls(value, out):
    """Every picture address in a view (thumbnails, full sizes, avatars)."""
    if isinstance(value, dict):
        for k, v in value.items():
            if k in URL_KEYS and isinstance(v, str) and v.startswith("http"):
                out.append(v)
            else:
                _urls(v, out)
    elif isinstance(value, list):
        for v in value:
            _urls(v, out)
    return out


def _fetch_media(item, did, pds, media):
    """Download what a feed item shows. Returns {cid or url: local file name}."""
    files = {}
    post = item["post"]
    own = post.get("author", {}).get("did") == did
    if own:
        for cid, mime in _blobs(post.get("record", {}), []):
            if not cid or cid in files:
                continue
            ext = EXT.get(mime) or mimetypes.guess_extension(mime or "") or ".bin"
            q = urllib.parse.urlencode({"did": did, "cid": cid})
            name = _save_file(media / (cid + ext), f"{pds}/xrpc/com.atproto.sync.getBlob?{q}")
            if name:
                files[cid] = name
    for url in _urls({"embed": post.get("embed"), "reply": item.get("reply"), "author": post.get("author")}, []):
        if url in files:
            continue
        mine = next((c for c in files if c and url.rstrip("/").split("/")[-1].split("@")[0] == c), None)
        if mine and "/feed_fullsize/" in url:       # our own picture: the original is already here (the small
                                                    # thumbnail is kept too: pages load fast with it)
            files[url] = files[mine]
            continue
        name = _save_url(media, url)
        if name:
            files[url] = name
    return files


def _rkey(uri):
    return uri.rstrip("/").split("/")[-1]


# ---- the sync -------------------------------------------------------------------------------------------------------
def sync(log=print):
    """Bring Local Storage/Bsky-Kithy up to date. Returns how many new posts came in."""
    if not _lock.acquire(blocking=False):
        return 0
    try:
        return _sync(log)
    finally:
        _lock.release()


def _sync(log):
    root = folder()
    media = root / "media"
    state = _read_json(root / "state.json", {}) or {}
    _status.update(phase="Checking the profile", done=0, total=0, files=0, bytes=0, recent=[])
    profile = _api("app.bsky.actor.getProfile", actor=HANDLE)
    _status["total"] = int(profile.get("postsCount") or 0)
    did = profile["did"]
    if state.get("did") != did or not state.get("pds"):
        doc, _c = _get("https://plc.directory/" + urllib.parse.quote(did) if did.startswith("did:plc:")
                       else f"https://{did.split(':', 2)[2]}/.well-known/did.json")
        doc = json.loads(doc)
        pds = next(s["serviceEndpoint"] for s in doc.get("service", []) if s.get("id", "").endswith("atproto_pds"))
        state.update(did=did, pds=pds.rstrip("/"))
    pds = state["pds"]
    if state.get("media_version") != MEDIA_VERSION:
        state["backfilled"] = False                 # what's kept for each post changed: go through them all again
    for key in ("avatar", "banner"):
        if profile.get(key):
            name = _save_url(media, profile[key])
            if name:
                profile[f"local_{key}"] = name
    _write_json(root / "profile.json", profile)

    new, cursor, pages = 0, None, 0
    while True:
        params = {"actor": did, "limit": PAGE, "filter": "posts_with_replies"}
        if cursor:
            params["cursor"] = cursor
        page = _api("app.bsky.feed.getAuthorFeed", **params)
        items = page.get("feed", [])
        pages += 1
        known_here = 0
        for item in items:
            post = item["post"]
            repost = (item.get("reason") or {}).get("$type", "").endswith("reasonRepost")
            target = root / ("reposts" if repost else "posts") / (_rkey(post["uri"]) + ".json")
            old = _read_json(target)
            if old is not None and old.get("complete"):
                known_here += 1
            _status["phase"] = "Downloading new posts" if old is None else "Going through the posts"
            files = _fetch_media(item, did, pds, media)
            _status["done"] += 1
            _status["total"] = max(_status["total"], _status["done"])
            record = {"item": item, "files": files, "complete": True,
                      "saved": (old or {}).get("saved") or datetime.now(timezone.utc).isoformat(timespec="seconds"),
                      "kind": "repost" if repost else ("reply" if "reply" in post.get("record", {}) else "post")}
            _write_json(target, record)
            if old is None and not repost:
                new += 1
                log(f"Bluesky: saved a new post from {post.get('record', {}).get('createdAt', '')[:10]}: "
                    f"{post.get('record', {}).get('text', '')[:60]}")
        cursor = page.get("cursor")
        if not items or not cursor:
            state["backfilled"] = True
            state["media_version"] = MEDIA_VERSION
            break
        if state.get("backfilled") and known_here == len(items):
            break                                   # caught up with what's already here
    state["last_sync"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    _write_json(root / "state.json", state)
    _status.update(phase="Up to date", done=max(_status["total"], _status["done"]),
                   total=max(_status["total"], _status["done"]))
    return new


# ---- the watcher ----------------------------------------------------------------------------------------------------
def _log(text):
    try:
        from claudecore.ai import llmlog
        llmlog.event("BLUESKY", text)
    except Exception:
        pass


def _loop():
    _status["kept"] = kept()
    while True:
        s = settings()
        if s.get("paused"):
            _status.update(state="paused", next=None)
        else:
            _status["state"] = "syncing"
            try:
                n = sync(_log)
                _status.update(state="watching", last=time.time(), new=n, error="")
                if n:
                    _log(f"Bluesky sync: {n} new post(s) in {folder()}")
            except Exception as exc:                   # offline, Bluesky down: try again next time
                _status.update(state="waiting", error=str(exc)[:200], phase="")
            _status.update(kept=kept(), manual=False)
        minutes = int(settings().get("minutes") or SYNC_MINUTES)
        _status["next"] = None if settings().get("paused") else time.time() + minutes * 60
        _wake.wait(minutes * 60)                       # (or until Sync now, or a setting changes)
        _wake.clear()


def install(desktop=None):
    """Start the watcher (once per running system)."""
    global _thread
    if _thread is None or not _thread.is_alive():
        _thread = threading.Thread(target=_loop, name="bsky-watcher", daemon=True)
        _thread.start()
    return _thread


if __name__ == "__main__":                              # a sync by hand: python -m claudexp.bsky
    print(f"{sync()} new post(s); everything is in {folder()}")
