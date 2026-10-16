"""The user account: display name, account picture, and profile folder (data/user.json).

Like real XP, renaming the account changes the name shown everywhere, but the profile folder
(C:\\Documents and Settings\\<folder>) keeps the name it was created with.
"""
from functools import lru_cache

from PySide6.QtCore import QObject, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPixmap

from .paths import DATA, ROOT, find_image

USER_FILE = DATA / "user.json"
PICTURES_DIR = ROOT / "assets" / "user_icons"
DEFAULT_NAME = "Desktop"
DEFAULT_PICTURE = "Snowflake_(Windows_XP).png"
CUSTOM = "custom:userpic"      # the user's own assets/images/userpic.* picture


def _load():
    import json
    try:
        with open(USER_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        data = {}
    data.setdefault("name", DEFAULT_NAME)
    data.setdefault("picture", DEFAULT_PICTURE)
    if "profile" not in data:
        # Keep an existing profile folder (from before accounts existed), else use the name.
        docs = DATA / "Drive C" / "Documents and Settings"
        existing = [p.name for p in docs.iterdir() if p.is_dir() and p.name not in ("All Users", "Default User")] \
            if docs.exists() else []
        data["profile"] = existing[0] if existing else data["name"]
        _save(data)
    return data


def _save(data):
    import json
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


def user_name():
    return account().data["name"]


def profile_name():
    """The profile folder name (doesn't change when the account is renamed)."""
    return account().data["profile"]


def set_name(name):
    a = account()
    a.data["name"] = name.strip() or DEFAULT_NAME
    online = _online()
    if online.get("same"):
        online["handle"] = a.data["name"]          # 'Use my Windows name online' follows the rename
    _save(a.data)
    a.changed.emit()


def new_account(name, owner="", organization="", computer="", picture=None, handle=None, linked_=True,
                windows_password=None, online_password_=None):
    """A fresh install's first account (from Setup's 'Who will use this computer?' pages). The profile folder
    takes the new name; one already made under the default name during Setup is renamed to match."""
    import random
    a = account()
    name = name.strip() or DEFAULT_NAME
    docs = DATA / "Drive C" / "Documents and Settings"
    old, new = docs / a.data.get("profile", ""), docs / _folder_name(name)
    if a.data.get("profile") and old.exists() and old != new and not new.exists():
        old.rename(new)
    picks = [path.name for path in sorted(PICTURES_DIR.glob("*.png"))]
    a.data.update(name=name, profile=new.name, owner=owner or name, organization=organization,
                  computer=computer,
                  picture=picture or (random.choice(picks) if picks else DEFAULT_PICTURE),
                  online={"handle": (handle or name).strip(), "linked": bool(linked_),
                          "same": (handle or name).strip() == name})
    _save(a.data)
    set_windows_password(windows_password)
    set_online_password(online_password_)
    _picture.cache_clear()
    a.changed.emit()


# ---- the online identity ----------------------------------------------------------------------------------------
# One online handle shared by AOL, ClaudeAIM, ClaudeIRC, ClaudeMUCK, e-mail and the Zone (when 'linked'), and
# optional passwords. These are pretend accounts: the Windows password is only kept as a salted hash; the online
# password is kept (lightly encoded) so it can be filled in for you, like AIM's 'Save password'.

def _online():
    a = account()
    online = a.data.get("online")
    if not isinstance(online, dict):
        # Upgrading an older install: start from the AIM screen name, and keep programs asking separately.
        handle = ""
        try:
            from .programs.people import aim_screen_name
            handle = aim_screen_name()
        except Exception:
            pass
        online = {"handle": handle or a.data["name"], "linked": False}
        a.data["online"] = online
        _save(a.data)
    return online


def online_handle():
    return _online()["handle"]


def linked():
    """Use the online handle for every account and sign in automatically?"""
    return bool(_online().get("linked"))


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
    """AIM screen names: 3-16 letters, digits and spaces, starting with a letter."""
    name = "".join(ch for ch in (handle or online_handle()) if ch.isalnum() or ch == " ").strip()
    name = name.lstrip("0123456789 ") or "XPUser"
    return (name + "01")[:16] if len(name) < 3 else name[:16]


def irc_nick(handle=None):
    """IRC nicknames: no spaces; letters, digits and a few symbols; not starting with a digit."""
    nick = "".join(ch for ch in (handle or online_handle()) if ch.isalnum() or ch in "_-[]\\`^{}|")
    nick = nick.lstrip("0123456789-") or "XPUser"
    return nick[:16]


def muck_name(handle=None):
    """MUCK characters: letters and digits only."""
    name = "".join(ch for ch in (handle or online_handle()) if ch.isalnum())
    return (name or "Guest")[:20]


def email_address(handle=None):
    slug = "".join(ch for ch in (handle or online_handle()).lower() if ch.isalnum())
    return f"{slug or 'me'}@hotmail.com"


def known_as():
    """What the buddies call you: the shared handle, or (if programs ask separately) the AIM screen name."""
    if linked():
        return online_handle()
    try:
        from .programs.people import aim_screen_name
        return aim_screen_name() or online_handle()
    except Exception:
        return online_handle()


def _hash(password, salt):
    import hashlib
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def set_windows_password(password):
    """None or '' removes it (the Welcome screen then logs on with one click)."""
    import secrets
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


def set_online_password(password):
    import base64
    a = account()
    if password:
        a.data["online_password"] = base64.b64encode(password.encode("utf-8")).decode("ascii")
    else:
        a.data.pop("online_password", None)
    _save(a.data)
    a.changed.emit()


def online_password():
    import base64
    raw = account().data.get("online_password")
    try:
        return base64.b64decode(raw).decode("utf-8") if raw else ""
    except ValueError:
        return ""


def _folder_name(name):
    bad = '<>:"/\\|?*'
    return "".join("_" if ch in bad else ch for ch in name).strip(" .") or DEFAULT_NAME


def registered_owner():
    """'Registered to:' in System Properties (the name typed during Setup)."""
    data = account().data
    return data.get("owner") or data["name"], data.get("organization", "")


def pictures():
    """[(id, label, QPixmap)] of every account picture to choose from."""
    out = []
    custom = find_image("userpic")
    if custom:
        out.append((CUSTOM, "My picture", QPixmap(str(custom))))
    for path in sorted(PICTURES_DIR.glob("*.png")):
        label = path.stem.replace("_(Windows_XP)", "").replace("_", " ")
        out.append((path.name, label, QPixmap(str(path))))
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
    elif pic_id.startswith("fursona:"):                 # a Setup fursona's own picture
        from .fursonas import get, picture_path, preset_pixmap
        path = picture_path(pic_id)
        preset = get(pic_id[len("fursona:"):])
        if path is None and preset is not None:
            return preset_pixmap(preset, 96)           # its stand-in tile until a picture is added
    else:
        path = PICTURES_DIR / pic_id
        if not path.exists():
            path = PICTURES_DIR / DEFAULT_PICTURE
    pic = QPixmap(str(path)) if path else QPixmap()
    return None if pic.isNull() else pic


def picture_pixmap():
    return _picture()


def draw_user_picture(p, rect):
    """Draw the account picture into rect (or an orange tile with the user's initial)."""
    pic = _picture()
    if pic:
        p.drawPixmap(rect, pic)
        return
    grad = QLinearGradient(0, rect.top(), 0, rect.bottom())
    grad.setColorAt(0, QColor("#FFC85A"))
    grad.setColorAt(1, QColor("#F2742B"))
    p.fillRect(QRectF(rect), grad)
    font = QFont("Trebuchet MS")
    font.setPixelSize(max(8, int(rect.height() * 0.55)))
    font.setBold(True)
    p.setFont(font)
    p.setPen(QColor("white"))
    p.drawText(QRectF(rect), Qt.AlignCenter, user_name()[:1])
