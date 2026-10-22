"""The user account on this computer (data/user.json): the name, the account picture (a Windows 7 user tile or the
fursona's own picture), the profile folder (C:\\Users\\<folder>), the Windows password and the online handle that
every messenger signs in with. The same interface as ClaudeXP's user module, so the period programs read the
account here the way they always did."""
import base64
import hashlib
import json
import secrets
from functools import lru_cache

from PySide6.QtCore import QObject, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPixmap

from .paths import DATA, USER_PICTURES, find_image

USER_FILE = DATA / "user.json"
PICTURES_DIR = USER_PICTURES
DEFAULT_NAME = "User"
DEFAULT_PICTURE = "Usertile10.png"
DEFAULT_COMPUTER = "SYSTEM-2011"
CUSTOM = "custom:userpic"


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
    """Windows Setup's new account: replaces whatever was there (the profile folder keeps the name it's given)."""
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
    name = name.lstrip("0123456789 ") or "Win7User"
    return (name + "01")[:16] if len(name) < 3 else name[:16]


def irc_nick(handle=None):
    nick = "".join(ch for ch in (handle or online_handle()) if ch.isalnum() or ch in "_-[]\\`^{}|")
    nick = nick.lstrip("0123456789-") or "Win7User"
    return nick[:16]


def muck_name(handle=None):
    name = "".join(ch for ch in (handle or online_handle()) if ch.isalnum())
    return (name or "Guest")[:20]


def email_address(handle=None):
    slug = "".join(ch for ch in (handle or online_handle()).lower() if ch.isalnum())
    return f"{slug or 'me'}@hotmail.com"


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


def pictures():
    """[(id, label, QPixmap)] of every account picture to choose from: Windows 7's user tiles, plus your own."""
    out = []
    custom = find_image("userpic")
    if custom:
        out.append((CUSTOM, "My picture", QPixmap(str(custom))))
    for path in sorted(PICTURES_DIR.glob("*.png")):
        out.append((path.name, path.stem.replace("Usertile", "Tile "), QPixmap(str(path))))
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
    if pic_id == CUSTOM:
        path = find_image("userpic")
    elif pic_id.startswith("fursona:"):
        try:
            from claudexp.fursonas import get, picture_path, preset_pixmap
            path = picture_path(pic_id)
            preset = get(pic_id[len("fursona:"):])
            if path is None and preset is not None:
                return preset_pixmap(preset, 128)
        except Exception:
            path = None
    else:
        path = PICTURES_DIR / pic_id
        if not path.exists():
            path = PICTURES_DIR / DEFAULT_PICTURE
    pic = QPixmap(str(path)) if path else QPixmap()
    return None if pic.isNull() else pic


def picture_pixmap():
    return _picture()


def draw_user_picture(p, rect):
    """The account picture into rect (or a blue tile with the user's initial)."""
    pic = _picture()
    if pic:
        p.setRenderHint(p.RenderHint.SmoothPixmapTransform)
        p.drawPixmap(rect, pic)
        return
    grad = QLinearGradient(0, rect.top(), 0, rect.bottom())
    grad.setColorAt(0, QColor("#7FB6E8"))
    grad.setColorAt(1, QColor("#2B6CB0"))
    p.fillRect(QRectF(rect), grad)
    font = QFont("Segoe UI")
    font.setPixelSize(max(8, int(rect.height() * 0.55)))
    font.setBold(True)
    p.setFont(font)
    p.setPen(QColor("white"))
    p.drawText(QRectF(rect), Qt.AlignCenter, user_name()[:1])
