"""User fursonas: ready-made identities to choose from in Setup ('Choose your fursona'), or 'Be unique'.

Each preset is a folder in Program Files/The Fur Directory/user fursonas/<Name>/:
  profile.json      the same fields as a resident record, plus "handle", "summary", "online" and "knows"
  account.*         the Windows account picture          buddy_icon.*   the AIM buddy icon
  photos/           personal photos; sub-folders become albums in My Pictures; captions.txt as in AIM contacts
(see README.txt there). Choosing one sets the account name, picture and online handle, the AIM buddy icon and away
message, the IRC full name and the MUCK character's description, and copies the photos into My Pictures. The
choice is stored in data/user.json, so only reinstalling Windows (Setup) can change it; until then the name,
picture and online name are locked in User Accounts.

The residents know you: knowledge(name) tells a buddy or regular what they know about you, by how close the
preset says you are (close friends know your life; friends know the basics; anyone else only what they can see).
It goes into AIM (through life.context and the host's extra_context), IRC and MUCK prompts."""
import json
import shutil
from pathlib import Path

from .paths import ROOT

PRESETS = ROOT / "Program Files" / "The Fur Directory" / "user fursonas"
PICTURE_EXTS = (".png", ".jpg", ".jpeg", ".gif", ".bmp")
PREFIX = "fursona:"


def _load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


class Preset:
    def __init__(self, folder):
        self.folder = Path(folder)
        self.id = self.folder.name
        self.data = _load(self.folder / "profile.json", {})
        self.name = self.data.get("fur_name") or self.id
        self.handle = self.data.get("handle") or self.name

    def _file(self, stem):
        for ext in PICTURE_EXTS:
            p = self.folder / f"{stem}{ext}"
            if p.exists():
                return p
        return None

    @property
    def account_picture(self):
        return self._file("account") or self._file("buddy_icon")

    @property
    def buddy_icon(self):
        return self._file("buddy_icon") or self._file("account")

    def photos(self):
        """[(album, path, caption)] from photos/ (files directly in photos/ go in the album 'Photos')."""
        root = self.folder / "photos"
        out = []
        if not root.is_dir():
            return out
        for folder in [root] + sorted(d for d in root.iterdir() if d.is_dir()):
            caps = {}
            cap_file = folder / "captions.txt"
            if cap_file.exists():
                for line in cap_file.read_text(encoding="utf-8", errors="replace").splitlines():
                    name, _, text = line.partition(":")
                    caps[name.strip()] = text.strip()
            for f in sorted(folder.iterdir()):
                if f.is_file() and f.suffix.lower() in PICTURE_EXTS:
                    out.append(("Photos" if folder == root else folder.name, f, caps.get(f.name, "")))
        return out

    def get(self, *keys, default=""):
        d = self.data
        for k in keys:
            if not isinstance(d, dict):
                return default
            d = d.get(k)
        return d if d not in (None, "", [], {}) else default


def presets():
    if not PRESETS.is_dir():
        return []
    return [Preset(d) for d in sorted(PRESETS.iterdir()) if d.is_dir() and (d / "profile.json").exists()]


def get(pid):
    return next((p for p in presets() if p.id == pid), None)


def chosen():
    """The fursona picked in Setup (None for 'Be unique')."""
    from . import user
    pid = user.account().data.get("fursona")
    return get(pid) if pid else None


def locked():
    return chosen() is not None


def preset_pixmap(preset, size=64):
    """The preset's account picture, or a drawn tile with its initial until pictures are added."""
    from PySide6.QtCore import QRectF, Qt
    from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen, QPixmap
    path = preset.account_picture
    if path is not None:
        pm = QPixmap(str(path))
        if not pm.isNull():
            return pm.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    g = QLinearGradient(0, 0, size, size)
    g.setColorAt(0, QColor("#FFE7A8"))
    g.setColorAt(1, QColor("#E89A2A"))
    p.setPen(QPen(QColor("#A0601A"), 1.5))
    p.setBrush(g)
    p.drawRoundedRect(QRectF(2, 2, size - 4, size - 4), 8, 8)
    f = QFont("Trebuchet MS")
    f.setPixelSize(int(size * 0.5))
    f.setBold(True)
    p.setFont(f)
    p.setPen(QColor("white"))
    p.drawText(QRectF(0, 0, size, size), Qt.AlignCenter, preset.name[:1].upper())
    p.end()
    return pm


def unique_pixmap(size=64):
    """'Be unique': a blank card with a question mark."""
    from PySide6.QtCore import QRectF, Qt
    from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPixmap
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor("white"), 2, Qt.DashLine))
    p.setBrush(QColor(255, 255, 255, 40))
    p.drawRoundedRect(QRectF(3, 3, size - 6, size - 6), 8, 8)
    f = QFont("Trebuchet MS")
    f.setPixelSize(int(size * 0.55))
    f.setBold(True)
    p.setFont(f)
    p.drawText(QRectF(0, 0, size, size), Qt.AlignCenter, "?")
    p.end()
    return pm


def picture_path(pic_id):
    """The account picture for a 'fursona:<id>' picture id."""
    p = get(pic_id[len(PREFIX):]) if pic_id.startswith(PREFIX) else None
    return p.account_picture if p else None


# ---- applying it after Setup -------------------------------------------------------------------------------

def apply(preset):
    """Make the new account this fursona (called once, right after Setup's account is created)."""
    from . import user
    a = user.account()
    a.data["fursona"] = preset.id
    user._save(a.data)
    a.changed.emit()
    _copy_photos(preset)
    _aim_settings(preset)


def _copy_photos(preset):
    from .explorer import vfs
    vfs.setup_c()
    for album, path, _cap in preset.photos():
        dest = vfs.my_pictures() / album
        dest.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(path, dest / path.name)
        except OSError:
            pass


def _aim_settings(preset):
    """AIM keeps your buddy icon and away message in its own settings; set them from the fursona."""
    try:
        from .programs.aim import ensure_aim_path
        ensure_aim_path()
        from claudeaim.storage import Settings
        s = Settings()
        changes = {}
        if preset.buddy_icon is not None:
            changes["buddy_icon"] = str(preset.buddy_icon)       # AIM's resolve_icon accepts a full path
        if preset.get("online", "away_message"):
            changes["away_message"] = preset.get("online", "away_message")
        if changes:
            s.update(**changes)
    except Exception:
        pass


def muck_desc():
    p = chosen()
    return p.get("online", "muck_desc") or p.get("fursona", "description") if p else ""


def irc_realname():
    p = chosen()
    return p.get("online", "irc_realname") if p else ""


# ---- what the residents know about you ----------------------------------------------------------------------

CLOSENESS = {"close": "a close friend", "friend": "a friend", "acquaintance": "someone you know a little"}


def closeness(name):
    p = chosen()
    if p is None:
        return None, ""
    for k in p.get("knows", default=[]):
        if isinstance(k, dict) and str(k.get("name", "")).lower() == str(name).lower():
            return k.get("closeness", "friend"), k.get("how_met", "")
    return None, ""


def knowledge(name, called=None):
    """A paragraph for a resident's prompt: what they know about you (empty for 'Be unique')."""
    p = chosen()
    if p is None:
        return ""
    you = called or p.handle
    level, how_met = closeness(name)
    sona, pers = p.get("fursona", default={}), p.get("personal", default={})
    sex = str(pers.get("sex", "")).lower()
    he, his, him = (("he", "his", "him") if sex in ("male", "m") else ("she", "her", "her")
                    if sex in ("female", "f") else ("they", "their", "them"))
    hes = {"he": "he's", "she": "she's"}.get(he, "they're")
    look = ""
    if sona.get("species"):
        look = f"{his} fursona is {_a(sona['species'])}"
    if sona.get("description"):
        look += (". " if look else "") + sona["description"].rstrip(".")
    lines = []
    if level is None:
        if not look:
            return ""
        return (f"\n\nWhat you can tell about {you} just from seeing {him} around (you don't really know {him} "
                f"yet): {look}.")
    lines.append(f"{you} is {CLOSENESS.get(level, 'a friend')} of yours." + (f" {how_met}" if how_met else ""))
    if look:
        lines.append(look[:1].upper() + look[1:] + ".")
    if level == "acquaintance":
        return _about(you, lines)
    basics = []
    if pers.get("age"):
        basics.append(f"{hes} {pers['age']}")
    if sex:
        basics.append(f"{'male' if sex in ('male', 'm') else 'female' if sex in ('female', 'f') else sex}")
    if pers.get("location"):
        basics.append(f"lives in {pers['location']}")
    if basics:
        lines.append("You know " + ", ".join(basics) + ".")
    for key in ("fursuit", "conventions"):
        if p.get(key):
            lines.append(str(p.get(key)).rstrip(".") + ".")
    if level == "close":
        private = []
        for key, label in (("real_name", "real name"), ("job", "job"), ("work_hours", "work hours"),
                           ("sleep_hours", "usually sleeps"), ("online_hours", "online")):
            if pers.get(key):
                private.append(f"{label}: {pers[key]}")
        if private:
            lines.append("As a close friend you also know - " + "; ".join(private) + ".")
        if p.get("personality"):
            lines.append(f"What {hes} like: {p.get('personality')}")
        fav = p.get("favorites", default={})
        likes = [f"{k}: {', '.join(v) if isinstance(v, list) else v}" for k, v in fav.items() if v]
        if likes:
            lines.append(f"{his.title()} favourites - " + "; ".join(likes) + ".")
        rel = p.get("relationship", default={})
        if rel.get("status"):
            lines.append(f"Relationship status: {rel['status']}.")
    return _about(you, lines)


def _about(you, lines):
    return (f"\n\nAbout {you}, who you're talking with (use what you know naturally; don't recite it):\n- "
            + "\n- ".join(lines))


def _a(text):
    return f"an {text}" if text[:1].lower() in "aeiou" else f"a {text}"
