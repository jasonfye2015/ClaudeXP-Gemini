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
    _save(a.data)
    a.changed.emit()


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
