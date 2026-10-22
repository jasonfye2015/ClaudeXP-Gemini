"""The user account on this computer (data/user.json): the name, the account picture (one of Windows 11's coloured
person circles, your fursona's picture, or your own), the profile folder (C:\\Users\\<folder>), the PIN or password
and the online handle every messenger signs in with. The same interface as ClaudeXP's user module, so the period
programs read the account here the way they always did."""
import base64
import hashlib
import json
import secrets
from functools import lru_cache

from PySide6.QtCore import QObject, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPixmap

from .paths import DATA, USER_PICTURES, find_image

USER_FILE = DATA / "user.json"
PICTURES_DIR = USER_PICTURES
DEFAULT_NAME = "User"
DEFAULT_PICTURE = "person:0"
DEFAULT_COMPUTER = "WORKSTATION-2025"
CUSTOM = "custom:userpic"
# Windows 11's default account pictures: a person on a coloured circle
PERSON_COLOURS = [("Gray", "#8E8E8E"), ("Blue", "#0067C0"), ("Teal", "#038387"), ("Green", "#107C10"),
                  ("Purple", "#744DA9"), ("Magenta", "#C30052"), ("Orange", "#CA5010"), ("Red", "#D13438")]


def _load():
    try:
        with open(USER_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        data = {}
    data.setdefault("name", DEFAULT_NAME)
    data.setdefault("picture", DEFAULT_PICTURE)
    data.setdefault("computer", DEFAULT_COMPUTER)
    if "profile" not in data:
        users = DATA / "Drive C" / "Users"
        existing = [p.name for p in users.iterdir() if p.is_dir() and p.name not in ("Public", "Default")] \
            if users.exists() else []
        data["profile"] = existing[0] if existing else _folder_name(data["name"])
        _save(data)
    return data


def _save(data):
    USER_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


class _Account(QObject):
    changed = Signal()

    def __init__(self):
        super().__init__()
        self.data = _load()


_account = None


def account():
    global _account
    if _account is None:
        _account = _Account()
    return _account


def exists():
    return USER_FILE.exists()


def user_name():
    return account().data["name"]


def value(key, default=None):
    return account().data.get(key, default)


def set_user_name(name):
    name = name.strip()
    if not name:
        return
    a = account()
    a.data["name"] = name
    _save(a.data)
    a.changed.emit()


def profile_name():
    return account().data["profile"]


def computer_name():
    return account().data.get("computer") or DEFAULT_COMPUTER


def new_account(name, owner=None, organization="", computer=None, picture=None, handle=None, linked_=True,
                windows_password=None, online_password_=None):
    """Setup's new account: replaces whatever was there (the profile folder keeps the name it's given)."""
    global _account
    name = name.strip() or DEFAULT_NAME
    data = {"name": name, "owner": (owner or name).strip(), "organization": organization.strip(),
            "computer": (computer or DEFAULT_COMPUTER).strip(), "picture": picture or DEFAULT_PICTURE,
            "profile": _folder_name(name), "online": {"handle": (handle or name).strip(), "linked": bool(linked_)}}
    _save(data)
    _account = _Account()
    _picture.cache_clear()
    if windows_password:
        set_windows_password(windows_password)
    if online_password_:
        set_online_password(online_password_)
    return account()


def _online():
    a = account()
    online = a.data.get("online")
    if not online:
        online = {"handle": a.data["name"], "linked": True}
        a.data["online"] = online
        _save(a.data)
    return online


def online_handle():
    return _online()["handle"]


def linked():
    return bool(_online().get("linked", True))


def same_as_windows():
    return bool(_online().get("same"))


def set_online(handle=None, linked_=None, same=None):
    a = account()
    online = _online()
    if handle is not None and handle.strip():
        online["handle"] = handle.strip()
    if linked_ is not None:
        online["linked"] = bool(linked_)
    if same is not None:
        online["same"] = bool(same)
    _save(a.data)
    a.changed.emit()


def aim_name(handle=None):
    name = "".join(ch for ch in (handle or online_handle()) if ch.isalnum() or ch == " ").strip()
    name = name.lstrip("0123456789 ") or "Win11User"
    return (name + "01")[:16] if len(name) < 3 else name[:16]


def irc_nick(handle=None):
    nick = "".join(ch for ch in (handle or online_handle()) if ch.isalnum() or ch in "_-[]\\`^{}|")
    nick = nick.lstrip("0123456789-") or "Win11User"
    return nick[:16]


def muck_name(handle=None):
    name = "".join(ch for ch in (handle or online_handle()) if ch.isalnum())
    return (name or "Guest")[:20]


def email_address(handle=None):
    slug = "".join(ch for ch in (handle or online_handle()).lower() if ch.isalnum())
    return f"{slug or 'me'}@outlook.com"


def known_as():
    return online_handle()


def _hash(password, salt):
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def set_windows_password(password):
    a = account()
    if password:
        salt = secrets.token_hex(8)
        a.data["windows_password"] = {"salt": salt, "hash": _hash(password, salt)}
    else:
        a.data.pop("windows_password", None)
    _save(a.data)
    a.changed.emit()


def has_windows_password():
    return bool(account().data.get("windows_password"))


def check_windows_password(password):
    stored = account().data.get("windows_password")
    return not stored or _hash(password, stored["salt"]) == stored["hash"]


def set_password_hint(hint):
    a = account()
    a.data["password_hint"] = hint.strip()
    _save(a.data)


def password_hint():
    return account().data.get("password_hint", "")


def set_online_password(password):
    a = account()
    if password:
        a.data["online_password"] = base64.b64encode(password.encode("utf-8")).decode("ascii")
    else:
        a.data.pop("online_password", None)
    _save(a.data)
    a.changed.emit()


def online_password():
    raw = account().data.get("online_password")
    try:
        return base64.b64decode(raw).decode("utf-8") if raw else ""
    except ValueError:
        return ""


def _folder_name(name):
    bad = '<>:"/\\|?*'
    return "".join("_" if ch in bad else ch for ch in name).strip(" .") or DEFAULT_NAME


def registered_owner():
    data = account().data
    return data.get("owner") or data["name"], data.get("organization", "")


# ---- pictures ----------------------------------------------------------------------------------------------------
def person_pixmap(colour, size=192):
    """Windows 11's account picture: a white person on a coloured disc."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(colour))
    p.drawEllipse(QRectF(0, 0, size, size))
    p.setBrush(QColor("#FFFFFF"))
    s = size / 100
    p.drawEllipse(QPointF(50 * s, 38 * s), 15 * s, 15 * s)
    body = QPainterPath()
    body.addRoundedRect(QRectF(26 * s, 58 * s, 48 * s, 60 * s), 24 * s, 24 * s)
    clip = QPainterPath()
    clip.addEllipse(QRectF(0, 0, size, size))
    p.drawPath(body.intersected(clip))
    p.end()
    return pm


def pictures():
    """[(id, label, QPixmap)] of every account picture to choose from: your own, Windows 11's person discs, and any
    pictures in assets/user_pictures."""
    out = []
    custom = find_image("userpic")
    if custom:
        out.append((CUSTOM, "My picture", QPixmap(str(custom))))
    for i, (label, colour) in enumerate(PERSON_COLOURS):
        out.append((f"person:{i}", label, person_pixmap(colour, 128)))
    if PICTURES_DIR.is_dir():
        for path in sorted(PICTURES_DIR.glob("*.png")):
            out.append((path.name, path.stem, QPixmap(str(path))))
    return out


def picture_id():
    return account().data["picture"]


def set_picture(pic_id):
    a = account()
    a.data["picture"] = pic_id
    _save(a.data)
    _picture.cache_clear()
    a.changed.emit()


@lru_cache(maxsize=None)
def _picture():
    pic_id = picture_id()
    if pic_id.startswith("person:"):
        try:
            return person_pixmap(PERSON_COLOURS[int(pic_id.split(":")[1]) % len(PERSON_COLOURS)][1])
        except ValueError:
            return person_pixmap(PERSON_COLOURS[0][1])
    if pic_id == CUSTOM:
        path = find_image("userpic")
    elif pic_id.startswith("fursona:"):
        try:
            from claudexp.fursonas import get, picture_path, preset_pixmap
            path = picture_path(pic_id)
            preset = get(pic_id[len("fursona:"):])
            if path is None and preset is not None:
                return preset_pixmap(preset, 192)
        except Exception:
            path = None
    else:
        path = PICTURES_DIR / pic_id
        if not path.exists():
            return person_pixmap(PERSON_COLOURS[0][1])
    pic = QPixmap(str(path)) if path else QPixmap()
    return person_pixmap(PERSON_COLOURS[0][1]) if pic.isNull() else pic


def picture_pixmap():
    return _picture()


def draw_user_picture(p, rect, circle=True):
    """The account picture into rect, as the disc Windows 11 shows (or square, for the period programs)."""
    pic = _picture()
    r = QRectF(rect)
    p.save()
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    if circle:
        clip = QPainterPath()
        clip.addEllipse(r)
        p.setClipPath(clip)
    if pic is not None and not pic.isNull():
        scaled = pic.scaled(int(r.width()), int(r.height()), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        p.drawPixmap(int(r.x() + (r.width() - scaled.width()) / 2), int(r.y() + (r.height() - scaled.height()) / 2),
                     scaled)
    else:
        p.fillRect(r, QColor(PERSON_COLOURS[1][1]))
        font = QFont("Segoe UI")
        font.setPixelSize(max(8, int(r.height() * 0.5)))
        p.setFont(font)
        p.setPen(QColor("white"))
        p.drawText(r, Qt.AlignCenter, user_name()[:1])
    p.restore()
