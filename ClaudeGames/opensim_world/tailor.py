"""The fitting room: how the residents get their own furry avatars.

An NPC wears a saved appearance (a notecard), and a saved appearance only looks right once a viewer has worn the outfit
and baked its skin. So a helper avatar, Hollow Tailor, does the trying-on: it gets the furry avatars pack in its
#RLV folder (one folder per avatar), logs in with a second Cool VL Viewer with RestrainedLove switched on, and a
Fitting Room object it owns changes it into each avatar in turn with RLV commands, saves the look with
osAgentSaveAppearance and reports the notecard's asset ID here. The residents' Keepers then create each NPC from the
look picked for them (wardrobe.json), by that asset ID, in any region. The user's own avatar is never touched.

    python -m opensim_world.tailor [looks] [seconds]             the 21 looks (with the server not running)
    python -m opensim_world.tailor residents [names] [seconds]   each resident's look, clothes and all
    (after changing wardrobe.json, set "residents_pack" to false in world.json so the residents' folder is rebuilt)
"""
import ctypes
import html
import io
import json
import re
import secrets
import subprocess
import tarfile
import threading
import time
import uuid
from ctypes import wintypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import BRIDGE_PORT, GRID_PORT, REGION, account_id, root, viewer_exe, world_file
from . import oar

TAILOR = ("Hollow", "Tailor")
PACK = "furry-avatars.iar"
SECONDS_PER_LOOK = 35            # long enough for the attachments to rez and the skin to bake
HERE = Path(__file__).resolve().parent


def _world():
    return json.loads(world_file().read_text(encoding="utf-8"))


def _save_world(data):
    world_file().write_text(json.dumps(data, indent=2), encoding="utf-8")


def slug(name):
    return re.sub(r"[^a-z0-9]+", "_", html.unescape(name).lower()).strip("_")


def looks(iar_path):
    """{slug: display name} for each avatar folder in the pack."""
    out = {}
    with tarfile.open(iar_path) as t:
        for n in t.getnames():
            parts = n.split("/")
            if len(parts) >= 3 and parts[0] == "inventory":
                name = html.unescape(re.sub(r"__[0-9a-f-]{36}$", "", parts[2]))
                if name and "." not in parts[2][-5:]:
                    out[slug(name)] = name
    return out


def tailor_iar(src, dst):
    """The pack with its top folder renamed #RLV and each avatar's folder named by its slug, so RLV can wear it."""
    # GNU long names, as OpenSim writes them: it ignores the ustar prefix and PAX headers Python uses otherwise
    with tarfile.open(src) as t, tarfile.open(dst, "w:gz", format=tarfile.GNU_FORMAT) as out:
        for m in t.getmembers():
            data = t.extractfile(m).read() if m.isfile() else None
            parts = m.name.split("/")
            if len(parts) >= 2 and parts[0] == "inventory":
                parts[1] = re.sub(r"^.*?(__[0-9a-f-]{36})$", r"#RLV\1", parts[1])
                if len(parts) >= 3:
                    parts[2] = re.sub(r"^(.*?)(__[0-9a-f-]{36})$",
                                      lambda g: slug(g.group(1)) + g.group(2), parts[2])
            m.name = "/".join(parts)
            out.addfile(m, io.BytesIO(data) if data is not None else None)
    return dst


def fitting_script(slugs, seconds=SECONDS_PER_LOOK):
    names = ", ".join(f'"{s}"' for s in slugs)
    return (HERE / "fitting.lsl").read_text(encoding="utf-8").replace("/*LOOKS*/", names).replace(
        "/*SECONDS*/", f"{seconds}.0")


def ensure_account(server, password):
    """The Tailor's account (made once)."""
    tid = account_id(server, *TAILOR)
    if tid:
        return tid
    tid = str(uuid.uuid4())
    server.command(f"create user {TAILOR[0]} {TAILOR[1]} {password} tailor@furryhollow.local {tid}")
    server.command("")                       # it still asks for a model to copy: none (the default look)
    time.sleep(5)
    return account_id(server, *TAILOR)


# ---- RestrainedLove, on only while the Tailor's viewer runs ----
def _viewer_settings():
    import os
    return Path(os.environ.get("APPDATA", "")) / "SecondLife" / "user_settings" / "settings_coolvlviewer_1324.xml"


# what the Tailor's viewer needs, and Cool VL's own defaults (put back afterwards for the user's viewer)
TAILOR_SETTINGS = {"RestrainedLove": ("Boolean", 1, 0),          # RLV, read only at startup
                   "BackgroundYieldTime": ("U32", 0, 40),       # keep drawing (and baking) behind other windows
                   "AFKTimeout": ("U32", 0, 300),               # never go Away
                   "RestrainedLoveAutomaticRenameItems": ("Boolean", 0, 1)}   # leave the looks' folders as they are


def viewer_settings(values):
    """Set Cool VL Viewer settings ({name: value}) in its settings file, adding any that aren't there."""
    path = _viewer_settings()
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return
    for name, value in values.items():
        kind = TAILOR_SETTINGS[name][0]
        m = re.search(rf"(<key>{name}</key>\s*<map>.*?<key>Value</key>\s*<(?:integer|boolean)>)(\d+)(<)", text, re.S)
        if m is not None:
            text = text[:m.start(2)] + str(int(value)) + text[m.end(2):]
        else:
            entry = (f"<key>{name}</key><map><key>Comment</key><string>Set by the Claude Timeline.</string>"
                     f"<key>Persist</key><integer>1</integer><key>Type</key><string>{kind}</string>"
                     f"<key>Value</key><integer>{int(value)}</integer></map>")
            text = text.replace("<map>", "<map>" + entry, 1)
    path.write_text(text, encoding="utf-8")


# ---- finding and photographing the Tailor's viewer window ----
_user32 = ctypes.windll.user32 if hasattr(ctypes, "windll") else None


def window_of(pid):
    """The process's main window: its biggest visible titled one (not a popup or a notice)."""
    found = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def each(hwnd, _l):
        owner = wintypes.DWORD()
        _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        if owner.value == pid and _user32.IsWindowVisible(hwnd) and _user32.GetWindowTextLengthW(hwnd) > 0:
            r = wintypes.RECT()
            _user32.GetClientRect(hwnd, ctypes.byref(r))
            found.append((r.right * r.bottom, hwnd))
        return True
    _user32.EnumWindows(each, 0)
    return max(found)[1] if found else None


def photograph(pid, path):
    """A picture of the Tailor's viewer window, asked of the window itself (PrintWindow), so whatever else is on the
    screen never ends up in it - even when the viewer is behind other windows."""
    try:
        from PySide6.QtGui import QImage
        hwnd = window_of(pid)
        if hwnd is None:
            return False
        gdi = ctypes.windll.gdi32
        vp = ctypes.c_void_p
        _user32.GetDC.restype = vp
        _user32.GetDC.argtypes = [wintypes.HWND]
        _user32.ReleaseDC.argtypes = [wintypes.HWND, vp]
        _user32.PrintWindow.argtypes = [wintypes.HWND, vp, wintypes.UINT]
        gdi.CreateCompatibleDC.restype = vp
        gdi.CreateCompatibleDC.argtypes = [vp]
        gdi.CreateCompatibleBitmap.restype = vp
        gdi.CreateCompatibleBitmap.argtypes = [vp, ctypes.c_int, ctypes.c_int]
        gdi.SelectObject.restype = vp
        gdi.SelectObject.argtypes = [vp, vp]
        gdi.GetDIBits.argtypes = [vp, vp, wintypes.UINT, wintypes.UINT, vp, vp, wintypes.UINT]
        gdi.DeleteObject.argtypes = [vp]
        gdi.DeleteDC.argtypes = [vp]
        rect = wintypes.RECT()
        _user32.GetClientRect(hwnd, ctypes.byref(rect))
        w, h = rect.right, rect.bottom
        if w <= 0 or h <= 0:
            return False
        hdc = _user32.GetDC(hwnd)
        mem = gdi.CreateCompatibleDC(hdc)
        bmp = gdi.CreateCompatibleBitmap(hdc, w, h)
        gdi.SelectObject(mem, bmp)
        ok = _user32.PrintWindow(hwnd, mem, 3)          # client area only, full content (works for OpenGL)

        class BITMAPINFOHEADER(ctypes.Structure):
            _fields_ = [("biSize", wintypes.DWORD), ("biWidth", wintypes.LONG), ("biHeight", wintypes.LONG),
                        ("biPlanes", wintypes.WORD), ("biBitCount", wintypes.WORD),
                        ("biCompression", wintypes.DWORD), ("biSizeImage", wintypes.DWORD),
                        ("biXPelsPerMeter", wintypes.LONG), ("biYPelsPerMeter", wintypes.LONG),
                        ("biClrUsed", wintypes.DWORD), ("biClrImportant", wintypes.DWORD)]
        info = BITMAPINFOHEADER(ctypes.sizeof(BITMAPINFOHEADER), w, -h, 1, 32, 0, 0, 0, 0, 0, 0)
        buf = ctypes.create_string_buffer(w * h * 4)
        gdi.GetDIBits(mem, bmp, 0, h, buf, ctypes.byref(info), 0)
        gdi.DeleteObject(bmp)
        gdi.DeleteDC(mem)
        _user32.ReleaseDC(hwnd, hdc)
        if not ok or not buf.raw.strip(b"\x00\xff"):     # nothing drawn
            return False
        return QImage(buf.raw, w, h, w * 4, QImage.Format_RGB32).copy().save(str(path))
    except Exception:
        return False


def clear_residents_folder():
    """Remove the Tailor's #RLV/residents folder from the inventory database (server stopped), so a rebuilt
    residents pack - after wardrobe.json changes - replaces it instead of landing beside it."""
    import sqlite3
    from . import opensim_bin
    data = _world()
    tid = data.get("tailor", {}).get("id")
    db = opensim_bin() / "inventory.db"
    if not tid or not db.exists():
        return 0
    con = sqlite3.connect(str(db))
    try:
        folders = {r[0]: (r[1], r[2]) for r in con.execute(
            "SELECT folderID, folderName, parentFolderID FROM inventoryfolders WHERE agentID = ?", (tid,))}
        rlv = {k for k, v in folders.items() if v[0] == "#RLV"}
        doomed = {k for k, v in folders.items() if v[0] == "residents" and v[1] in rlv}
        grew = True
        while grew:
            grew = False
            for k, v in folders.items():
                if k not in doomed and v[1] in doomed:
                    doomed.add(k)
                    grew = True
        for f in doomed:
            con.execute("DELETE FROM inventoryitems WHERE parentFolderID = ?", (f,))
            con.execute("DELETE FROM inventoryfolders WHERE folderID = ?", (f,))
        con.commit()
        return len(doomed)
    finally:
        con.close()


# ---- the fitting ----
def run(server, progress=print, photos=None, only=None, seconds=SECONDS_PER_LOOK, residents=False):
    """Try every look on the Tailor and save each one. The world's server must be running; the bridge must not be
    (this listens on its port). Returns {look: {"name", "notecard"}}.

    residents=True fits each main resident's whole look instead - their furry avatar and their clothes, gathered by
    dress.py into #RLV/residents/<name> - and keeps them in world.json "dressed" by resident name."""
    data = _world()
    pack = root() / "downloads" / "zadaroo" / PACK
    if residents:
        from . import dress
        by_slug = {dress.slug(r): r for r in dress.wardrobe()["picks"]}
        all_looks = {f"{dress.TOP}/{sl}": name for sl, name in by_slug.items()}
        if only:
            all_looks = {k: v for k, v in all_looks.items() if v in only or k.split("/")[-1] in only}
    else:
        all_looks = looks(pack)
        if only:
            all_looks = {k: v for k, v in all_looks.items() if k in only}
    tailor = data.setdefault("tailor", {"password": secrets.token_hex(8)})
    _save_world(data)
    tid = ensure_account(server, tailor["password"])
    if tid is None:
        raise RuntimeError("couldn't make the Tailor's account")
    if tailor.get("id") != tid:
        tailor["id"] = tid
        _save_world(data)
    if not tailor.get("dressed_pack"):
        progress("Giving the Tailor the furry avatars...")
        path = tailor_iar(pack, root() / "keepers" / "tailor.iar")
        mark = len(server.log())
        server.command(f'load iar {TAILOR[0]} {TAILOR[1]} / "{tailor["password"]}" "{path}"')
        end = time.time() + 300
        while "items from archive" not in server.log()[mark:] and time.time() < end:
            time.sleep(1)
        tailor["dressed_pack"] = True
        _save_world(data)
    if residents and not tailor.get("residents_pack"):
        from . import dress
        progress("Giving the Tailor the residents' clothes...")
        path = root() / "keepers" / "residents.iar"
        dress.build(path)
        mark = len(server.log())
        server.command(f'load iar {TAILOR[0]} {TAILOR[1]} #RLV "{tailor["password"]}" "{path}"')
        end = time.time() + 600
        while "items from archive" not in server.log()[mark:] and time.time() < end:
            time.sleep(1)
        tailor["residents_pack"] = True
        _save_world(data)

    saved = {}
    finished = threading.Event()
    viewer = {"proc": None}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            self.send_response(200)
            self.end_headers()

        def do_POST(self):
            body = self.rfile.read(int(self.headers.get("Content-Length") or 0)).decode("utf-8", "replace")
            if self.path == "/outfit":
                look, _, card = body.partition("|")
                if photos is not None and viewer["proc"] is not None:
                    photograph(viewer["proc"].pid, Path(photos) / f"{look.replace('/', '_')}.png")
                saved[look] = {"name": all_looks.get(look, look), "notecard": card}
                progress(f"Saved {all_looks.get(look, look)} ({len(saved)}/{len(all_looks)})")
            elif self.path == "/done":
                finished.set()
            elif self.path == "/say":
                progress("  Fitting Room: " + body)
            self.send_response(200)
            self.end_headers()

    http = ThreadingHTTPServer(("127.0.0.1", BRIDGE_PORT), Handler)
    threading.Thread(target=http.serve_forever, daemon=True).start()
    try:
        room = oar.write(root() / "keepers" / "fitting.oar", tid, "fitting-room", script=fitting_script(list(all_looks), seconds),
                         name="Fitting Room", pos=(128.0, 128.0, 200.0))     # up in the sky, out of the way
        server.command(f"change region {REGION}")
        server.command(f'load oar --merge "{room}"')
        exe = viewer_exe()
        progress("The Tailor is logging in (a second viewer window opens)...")
        viewer_settings({k: v[1] for k, v in TAILOR_SETTINGS.items()})
        viewer["tailoring"] = True
        end = time.time() + 180 + (seconds + 45) * (len(all_looks) + 3)    # each look also takes a picture and a save
        for attempt in range(3):
            viewer["proc"] = subprocess.Popen(
                [str(exe), "--grid", f"localhost{GRID_PORT}", "--login", TAILOR[0], TAILOR[1], tailor["password"],
                 "--multiple"], cwd=str(exe.parent))
            while not finished.is_set() and viewer["proc"].poll() is None and time.time() < end:
                finished.wait(timeout=2)
            if finished.is_set() or time.time() >= end:
                break
            progress("The Tailor's viewer closed; trying again...")
            time.sleep(10)
    finally:
        if viewer["proc"] is not None and viewer["proc"].poll() is None:
            viewer["proc"].terminate()
            try:
                viewer["proc"].wait(20)
            except subprocess.TimeoutExpired:
                pass
        if viewer.get("tailoring"):              # back to the defaults for the user's own viewer
            viewer_settings({k: v[2] for k, v in TAILOR_SETTINGS.items()})
        http.shutdown()
        http.server_close()
    data = _world()
    if residents:
        data.setdefault("dressed", {}).update({v["name"]: v["notecard"] for v in saved.values()})
    else:
        data.setdefault("outfits", {}).update(saved)
    _save_world(data)
    return saved


if __name__ == "__main__":
    import os
    import sys
    os.environ.setdefault("QT_QPA_PLATFORM", "windows")
    from PySide6.QtGui import QGuiApplication
    app = QGuiApplication(sys.argv[:1])
    from . import Server, configure
    configure()
    if "residents" in sys.argv[1:] and not _world().get("tailor", {}).get("residents_pack"):
        clear_residents_folder()                  # a rebuilt pack replaces the old folder
    s = Server()
    s.start()
    while not s.ready() and s.running():
        time.sleep(1)
    shots = root() / "outfits"
    shots.mkdir(exist_ok=True)
    try:
        args = [a for a in sys.argv[1:] if a != "residents"]
        only = [a for a in args if not a.isdigit()] or None
        secs = next((int(a) for a in args if a.isdigit()), SECONDS_PER_LOOK)
        result = run(s, photos=shots, only=only, seconds=secs, residents="residents" in sys.argv[1:])
        print(len(result), "looks saved")
    finally:
        s.stop()
