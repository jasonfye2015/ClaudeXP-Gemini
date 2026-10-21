"""Telegram Desktop: the one messenger with stickers.

The same buddies as every other messenger (core.py: their presence, their memory of you across the networks, their
replies from the language model), in Telegram's own look: a chat list with round avatars and previews, a wallpapered
conversation with green and white bubbles, ticks and date pills, a typing indicator, an Emoji | Stickers panel, a User
Info panel and Night Mode.

Stickers (Local Storage/Sticker Packs, given meanings in the Sticker Manager): each buddy has a favourite pack, and
their prompt lists its emojis. A reply that starts or ends with one arrives as one of that emoji's stickers (picked at
random). A sticker you send reaches them as '[sticker: 😊 happy tail wag]'. The other messengers stay sticker-free."""
import html
import json
import random
import re
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import (QColor, QFont, QIcon, QImage, QImageReader, QLinearGradient, QMovie, QPainter,
                           QPainterPath, QPen, QPixmap, QPolygonF)
from PySide6.QtWidgets import (QAbstractItemView, QFrame, QHBoxLayout, QLabel, QLineEdit, QListView, QListWidget,
                               QListWidgetItem, QMenu, QPushButton, QScrollArea, QSizePolicy, QStackedWidget,
                               QStyle, QStyledItemDelegate, QToolButton, QVBoxLayout, QWidget)
from shiboken6 import isValid

from ... import sound
from ...paths import DATA
from .core import AWAY, BUSY, OFFLINE, ONLINE, Network, codes_for, decode_in_furcoder

SETTINGS = DATA / "telegram.json"
NOTIFY_SOUND = "telegram_notification.mp3"            # assets/sounds: Telegram's own incoming-message sound
LOGO = "Telegram Details/Telegram Logo.png"            # in Local Storage, the user's own copy of the logo
EMOJI_FONT = "Segoe UI Emoji"
EMOJIS = ("😂 😘 ❤️ 😍 😊 😁 👍 ☺️ 😔 😄 😭 💋 😒 😳 😜 🙈 😉 😃 😢 😝 😱 😡 😏 😞 😅 😚 🙊 😌 😀 😋 😆 👌 😐 😕 "
          "🤣 😇 🙂 🙃 🥰 😗 😙 😛 🤪 🤨 🧐 🤓 😎 🤩 🥳 😟 🙁 😣 😖 😫 😩 🥺 😤 😠 🤬 🤯 😓 🤗 🤔 🤭 🤫 😶 😬 "
          "🙄 😯 😦 😧 😮 😲 🥱 😴 🤤 😪 😵 🤐 🥴 🤢 🤮 🤧 😷 🤒 🤕 🤑 🤠 😈 👿 👻 💀 🐾 🐺 🦊 🐶 🐱 🐰 "
          "🦁 🐯 🐻 🐼 🐲 🦄 🐴 🐮 🐷 🐸 🐵 🦝 💕 💖 💔 🔥 ✨ 🎉 💤 💦 🍕 ☕ 🍺 🎁 👋 👏 🙏 💪 🤝 ✌️ 🤞 🤘").split()
LIGHT = {"bg": "#FFFFFF", "side": "#FFFFFF", "line": "#E7E7E7", "text": "#000000", "dim": "#8E9AA6",
         "accent": "#419FD9", "pick": "#419FD9", "pick_text": "#FFFFFF", "mine": "#EFFDDE", "theirs": "#FFFFFF",
         "mine_time": "#6CB86A", "theirs_time": "#A0ACB6", "search": "#F1F1F1", "wall1": "#A9C7A1",
         "wall2": "#6F9E79", "pill": "rgba(40, 70, 40, 140)", "panel": "#FFFFFF", "badge": "#4FAE4E"}
DARK = {"bg": "#17212B", "side": "#17212B", "line": "#0E1621", "text": "#F5F5F5", "dim": "#6D7F8F",
        "accent": "#5288C1", "pick": "#2B5278", "pick_text": "#FFFFFF", "mine": "#2B5278", "theirs": "#182533",
        "mine_time": "#7DA8D3", "theirs_time": "#6D7F8F", "search": "#242F3D", "wall1": "#0E1621",
        "wall2": "#16222F", "pill": "rgba(30, 44, 58, 200)", "panel": "#17212B", "badge": "#3E6A99"}
AVATAR_COLOURS = ("#E17076", "#7BC862", "#65AADD", "#A695E7", "#EE7AAE", "#6EC9CB", "#FAA774")


def _settings():
    try:
        data = json.loads(SETTINGS.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _save_settings(data):
    try:
        SETTINGS.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS.write_text(json.dumps(data, indent=1), encoding="utf-8")
    except OSError:
        pass


def _plain(name):
    return re.sub(r"[^a-z0-9_]+", "", name.lower().replace(" ", "_")) or "user"


def _when(entry):
    try:
        return datetime.fromisoformat(entry["ts"]).astimezone().replace(tzinfo=None)
    except (KeyError, ValueError):
        return datetime.now()


def _clock(dt):
    return f"{dt.hour % 12 or 12}:{dt.minute:02d} {'AM' if dt.hour < 12 else 'PM'}"


# ---- icons ------------------------------------------------------------------------------------------------------
def _drawn_logo(size):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#2AABEE"))
    p.drawEllipse(QRectF(1, 1, size - 2, size - 2))
    k = size / 32
    p.setBrush(QColor("white"))
    p.drawPolygon(QPolygonF([QPointF(7 * k, 15.5 * k), QPointF(23.5 * k, 9 * k), QPointF(20.5 * k, 23.5 * k),
                             QPointF(15 * k, 19.5 * k), QPointF(12.5 * k, 22 * k), QPointF(12.2 * k, 18 * k)]))
    p.setBrush(QColor("#C8DAEA"))
    p.drawPolygon(QPolygonF([QPointF(12.2 * k, 18 * k), QPointF(21 * k, 11.5 * k), QPointF(15 * k, 19.5 * k),
                             QPointF(12.5 * k, 22 * k)]))
    p.end()
    return pm


_logo_cache = {}


def logo(size=32):
    """The user's Telegram logo (Local Storage/Telegram Details), or a drawn one if it isn't there."""
    if size not in _logo_cache:
        pm = QPixmap()
        try:
            from ...explorer.vfs import local_storage
            path = local_storage() / LOGO
            if path.exists():
                reader = QImageReader(str(path))
                reader.setScaledSize(QSize(size * 2, size * 2))
                img = reader.read()
                if not img.isNull():
                    pm = QPixmap.fromImage(img.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        except Exception:
            pm = QPixmap()
        _logo_cache[size] = pm if not pm.isNull() else _drawn_logo(size)
    return _logo_cache[size]


def telegram_icon():
    icon = QIcon()
    for size in (16, 32, 48):
        icon.addPixmap(logo(size))
    return icon


def emoji_picture(emoji, size):
    """An emoji drawn in colour (Segoe UI Emoji), as a picture."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.TextAntialiasing)
    f = QFont(EMOJI_FONT)
    f.setPixelSize(int(size * 0.82))
    p.setFont(f)
    p.drawText(QRectF(0, 0, size, size), Qt.AlignCenter, emoji)
    p.end()
    return pm


def tray_picture(count, size=16):
    """Telegram's logo for the notification area, with a red badge and the number of unread messages."""
    pm = QPixmap(logo(size))
    if count:
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        text = str(count) if count < 100 else "99+"
        w = max(size * 0.62, size * (0.36 + 0.2 * len(text)))
        badge = QRectF(size - w, size * 0.42, w, size * 0.58)
        p.setPen(QPen(QColor("white"), 1))
        p.setBrush(QColor("#E53935"))
        p.drawRoundedRect(badge, badge.height() / 2, badge.height() / 2)
        p.setPen(QColor("white"))
        f = QFont("Tahoma")
        f.setPixelSize(max(6, int(size * 0.46)))
        f.setBold(True)
        p.setFont(f)
        p.drawText(badge, Qt.AlignCenter, text)
        p.end()
    return pm


_avatar_cache = {}


def avatar(b, size):
    """A buddy's picture in a circle (their buddy icon), or their initials on a colour."""
    key = (b.contact.id, size)
    if key in _avatar_cache:
        return _avatar_cache[key]
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    clip = QPainterPath()
    clip.addEllipse(QRectF(0, 0, size, size))
    img = QImage()
    try:
        from claudeaim import paths as aim_paths
        icon_path = aim_paths.resolve_icon(b.contact.icon) if b.contact.icon else None
        if icon_path:
            img = QImage(str(icon_path))
    except Exception:
        img = QImage()
    if not img.isNull():
        side = min(img.width(), img.height())
        img = img.copy((img.width() - side) // 2, (img.height() - side) // 2, side, side)
        p.setClipPath(clip)
        p.drawImage(QRectF(0, 0, size, size), img)
    else:
        colour = AVATAR_COLOURS[sum(map(ord, b.contact.id)) % len(AVATAR_COLOURS)]
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(colour))
        p.drawEllipse(QRectF(0, 0, size, size))
        words = re.findall(r"[A-Za-z0-9]+", b.name) or ["?"]
        initials = (words[0][0] + (words[1][0] if len(words) > 1 else "")).upper()
        p.setPen(QColor("white"))
        f = QFont("Segoe UI", max(7, int(size * 0.32)))
        f.setBold(True)
        p.setFont(f)
        p.drawText(QRectF(0, 0, size, size), Qt.AlignCenter, initials)
    p.end()
    _avatar_cache[key] = pm
    return pm


# ---- the network ------------------------------------------------------------------------------------------------
class TelegramNetwork(Network):
    key = "telegram"
    title = "Telegram"

    def handle_for(self, contact):
        return "@" + _plain(contact.screen_name)

    def _memory(self, b):
        """What every messenger tells them, plus the stickers they can send (their favourite pack's emojis)."""
        extra = ""
        try:
            from stickers import library
            lines = library.prompt_lines(b.name)
            if lines:
                extra = "\n\n" + lines
        except Exception:
            pass
        return super()._memory(b) + extra

    def send_sticker(self, b, path):
        from stickers import library
        self.send(b, library.describe(path), sticker=str(path))

    def _deliver(self, b, text):
        """A reply that starts or ends with one of their sticker emojis: the words (if any), then the sticker."""
        try:
            from stickers import library
            hit = library.sticker_in(b.name, text)
        except Exception:
            hit = None
        if hit is None:
            super()._deliver(b, text)
            return
        path, emoji, meaning = hit
        rest = text.strip()
        rest = (rest[len(emoji):] if rest.startswith(emoji) else rest[:-len(emoji)]).strip()
        b.busy = False
        self.typing_changed.emit(b.contact.id, False)
        if rest:
            e = b.add("contact", rest)
            self.message_added.emit(b.contact.id, e)
            self._heard(b, b.name, rest)
        e = b.add("contact", emoji, sticker=str(path), meaning=meaning)
        b.unread = True
        self.message_added.emit(b.contact.id, e)
        self._heard(b, b.name, f"[sticker: {emoji} {meaning}]")


# ---- the chat list ---------------------------------------------------------------------------------------------
class ChatRows(QStyledItemDelegate):
    def __init__(self, app):
        super().__init__(app)
        self.app = app

    def sizeHint(self, option, index):
        return QSize(option.rect.width(), 62)

    def paint(self, p, option, index):
        app = self.app
        c = app.colours
        b = app.network.buddies.get(index.data(Qt.UserRole))
        if b is None:
            return
        r = QRectF(option.rect)
        picked = bool(option.state & QStyle.State_Selected)
        p.save()
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(r, QColor(c["pick"]) if picked else QColor(c["side"]))
        p.drawPixmap(int(r.left() + 10), int(r.top() + 7), avatar(b, 48))
        if b.presence == ONLINE:
            p.setPen(QPen(QColor(c["side"] if not picked else c["pick"]), 2))
            p.setBrush(QColor("#4FCE5D"))
            p.drawEllipse(QRectF(r.left() + 46, r.top() + 41, 12, 12))
        text = QColor(c["pick_text"] if picked else c["text"])
        dim = QColor(c["pick_text"] if picked else c["dim"])
        last = app.last_entry(b)
        p.setPen(text)
        f = QFont("Segoe UI", 10)
        f.setBold(True)
        p.setFont(f)
        when = ""
        if last is not None:
            dt = _when(last)
            when = _clock(dt) if dt.date() == datetime.now().date() else f"{dt:%a}" if (datetime.now() - dt).days < 7 \
                else f"{dt.month}/{dt.day}"
        name_rect = QRectF(r.left() + 68, r.top() + 9, r.width() - 140, 20)
        p.drawText(name_rect, Qt.AlignLeft | Qt.AlignVCenter, p.fontMetrics().elidedText(b.name, Qt.ElideRight,
                                                                                         int(name_rect.width())))
        p.setFont(QFont("Segoe UI", 8))
        p.setPen(dim)
        p.drawText(QRectF(r.right() - 74, r.top() + 9, 64, 20), Qt.AlignRight | Qt.AlignVCenter, when)
        preview, accent = app.preview(b)
        if b.busy:
            preview, accent = "typing...", True
        p.setFont(QFont(f"Segoe UI, {EMOJI_FONT}", 9))
        p.setPen(QColor(c["pick_text"]) if picked else QColor(c["accent"]) if accent else dim)
        unread = app.unread.get(b.contact.id, 0)
        prev_rect = QRectF(r.left() + 68, r.top() + 32, r.width() - (110 if unread else 80), 20)
        p.drawText(prev_rect, Qt.AlignLeft | Qt.AlignVCenter,
                   p.fontMetrics().elidedText(preview, Qt.ElideRight, int(prev_rect.width())))
        if unread and not picked:
            badge = QRectF(r.right() - 36, r.top() + 33, 26, 18)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(c["badge"]))
            p.drawRoundedRect(badge, 9, 9)
            p.setPen(QColor("white"))
            fb = QFont("Segoe UI", 8)
            fb.setBold(True)
            p.setFont(fb)
            p.drawText(badge, Qt.AlignCenter, str(unread))
        p.restore()


# ---- the conversation --------------------------------------------------------------------------------------------
class Wallpaper(QWidget):
    """Telegram's wallpaper: a soft gradient with a faint scatter of paw prints."""

    def __init__(self, app):
        super().__init__()
        self.app = app

    def paintEvent(self, event):
        c = self.app.colours
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        g = QLinearGradient(0, 0, self.width(), self.height())
        g.setColorAt(0, QColor(c["wall1"]))
        g.setColorAt(1, QColor(c["wall2"]))
        p.fillRect(self.rect(), g)
        rng = random.Random(7)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 26))
        step = 70
        for y in range(-20, self.height() + 40, step):
            for x in range(-20, self.width() + 40, step):
                cx, cy = x + rng.uniform(0, 40), y + rng.uniform(0, 40)
                s = rng.uniform(0.7, 1.2)
                p.drawEllipse(QRectF(cx - 6 * s, cy - 4 * s, 12 * s, 9 * s))
                for dx, dy in ((-7, -9), (-2.5, -12), (2.5, -12), (7, -9)):
                    p.drawEllipse(QRectF(cx + dx * s - 2.4 * s, cy + dy * s - 2.6 * s, 4.8 * s, 5.2 * s))


class ChatView(QScrollArea):
    """The messages: bubbles (yours green on the right, theirs white on the left), stickers, and date pills."""

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setStyleSheet("QScrollArea { background: transparent; } QScrollArea > QWidget > QWidget "
                           "{ background: transparent; }")
        self.viewport().setAutoFillBackground(False)
        self.inner = QWidget()
        self.inner.setAttribute(Qt.WA_TranslucentBackground)
        self.col = QVBoxLayout(self.inner)
        self.col.setContentsMargins(14, 10, 14, 10)
        self.col.setSpacing(4)
        self.col.addStretch(1)
        self.setWidget(self.inner)
        self.movies = []
        self.last_day = None
        self.verticalScrollBar().rangeChanged.connect(self._stick_to_bottom)
        self._follow = True

    def _stick_to_bottom(self, _lo, hi):
        if self._follow:
            self.verticalScrollBar().setValue(hi)

    def clear(self):
        for movie in self.movies:
            movie.stop()
        self.movies = []
        while self.col.count() > 1:
            w = self.col.takeAt(1).widget()
            if w is not None:
                w.hide()
                w.deleteLater()
        self.last_day = None

    def show_entries(self, entries, read_upto):
        self.clear()
        self._follow = True
        for i, e in enumerate(entries):
            self.add(e, read=i < read_upto)

    def add(self, e, read=True):
        c = self.app.colours
        day = _when(e).date()
        if day != self.last_day:
            self.last_day = day
            pill = QLabel(f"{_when(e):%B} {_when(e).day}")
            pill.setStyleSheet(f"QLabel {{ background: {c['pill']}; color: white; border-radius: 10px; "
                               "padding: 3px 10px; font: bold 9pt 'Segoe UI'; }}")
            row = QHBoxLayout()
            holder = QWidget()
            holder.setLayout(row)
            row.setContentsMargins(0, 6, 0, 6)
            row.addStretch(1)
            row.addWidget(pill)
            row.addStretch(1)
            self.col.addWidget(holder)
        if e["kind"] == "system":
            note = QLabel(e["text"])
            note.setWordWrap(True)
            note.setAlignment(Qt.AlignCenter)
            note.setStyleSheet(f"QLabel {{ color: white; background: {c['pill']}; border-radius: 9px; padding: 3px 10px;"
                               " font: 9pt 'Segoe UI'; }}")
            self.col.addWidget(note)
            return
        mine = e["kind"] == "user"
        holder = QWidget()
        row = QHBoxLayout(holder)
        row.setContentsMargins(0, 0, 0, 0)
        stamp = _clock(_when(e)) + ("  ✓✓" if mine and read else "  ✓" if mine else "")
        if e.get("sticker") and Path(e["sticker"]).exists():
            box = QVBoxLayout()
            pic = QLabel()
            movie = QMovie(e["sticker"])
            size = QImageReader(e["sticker"]).size()
            if size.isValid():
                movie.setScaledSize(size.scaled(170, 170, Qt.KeepAspectRatio))
            pic.setMovie(movie)
            movie.start()
            self.movies.append(movie)
            pic.setToolTip(f"{e.get('text', '')}  {e.get('meaning', '')}".strip())
            tag = QLabel(stamp)
            tag.setStyleSheet(f"QLabel {{ color: white; background: {c['pill']}; border-radius: 8px; padding: 1px 7px;"
                              " font: 8pt 'Segoe UI'; }}")
            box.addWidget(pic)
            box.addWidget(tag, 0, Qt.AlignRight if mine else Qt.AlignLeft)
            if mine:
                row.addStretch(1)
                row.addLayout(box)
            else:
                row.addLayout(box)
                row.addStretch(1)
            self.col.addWidget(holder)
            return
        bubble = QFrame()
        bubble.setObjectName("bubble")
        bubble.setStyleSheet(f"QFrame#bubble {{ background: {c['mine'] if mine else c['theirs']}; border-radius: 12px; }}")
        inner = QVBoxLayout(bubble)
        inner.setContentsMargins(11, 6, 11, 5)
        inner.setSpacing(1)
        words = QLabel(e["text"])
        words.setWordWrap(True)
        words.setTextInteractionFlags(Qt.TextSelectableByMouse)
        words.setMaximumWidth(max(240, int(self.viewport().width() * 0.62)))
        words.setStyleSheet(f"QLabel {{ color: {c['text']}; font: 10pt 'Segoe UI', '{EMOJI_FONT}'; background: transparent; }}")
        time_label = QLabel(stamp)
        time_label.setStyleSheet(f"QLabel {{ color: {c['mine_time'] if mine else c['theirs_time']}; font: 8pt 'Segoe UI';"
                                 " background: transparent; }}")
        inner.addWidget(words)
        inner.addWidget(time_label, 0, Qt.AlignRight)
        if mine:
            row.addStretch(1)
            row.addWidget(bubble)
        else:
            row.addWidget(bubble)
            row.addStretch(1)
        self.col.addWidget(holder)


# ---- the Emoji | Stickers panel and User Info ----------------------------------------------------------------------
class EmojiStickers(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        tabs = QHBoxLayout()
        tabs.setContentsMargins(0, 0, 0, 0)
        self.tab_buttons = []
        for i, name in enumerate(("EMOJI", "STICKERS")):
            b = QPushButton(name)
            b.setObjectName("panel")
            b.setCheckable(True)
            b.clicked.connect(lambda _c=False, n=i: self.show_tab(n))
            tabs.addWidget(b)
            self.tab_buttons.append(b)
        lay.addLayout(tabs)
        self.pages = QStackedWidget()
        lay.addWidget(self.pages, 1)
        self.emoji = QListWidget()
        self.emoji.setViewMode(QListView.IconMode)
        self.emoji.setIconSize(QSize(28, 28))
        self.emoji.setGridSize(QSize(40, 40))
        self.emoji.setResizeMode(QListView.Adjust)
        self.emoji.setMovement(QListView.Static)
        for e in EMOJIS:                       # drawn as pictures: as item text, icon view squeezes them to '...'
            item = QListWidgetItem(QIcon(emoji_picture(e, 28)), "")
            item.setData(Qt.UserRole, e)
            item.setToolTip(e)
            self.emoji.addItem(item)
        self.emoji.itemClicked.connect(lambda item: app.insert_emoji(item.data(Qt.UserRole)))
        self.pages.addWidget(self.emoji)
        stickers = QWidget()
        sl = QVBoxLayout(stickers)
        sl.setContentsMargins(0, 0, 0, 0)
        sl.setSpacing(0)
        self.packs = QListWidget()
        self.packs.setFlow(QListView.LeftToRight)
        self.packs.setFixedHeight(52)
        self.packs.setIconSize(QSize(40, 40))
        self.packs.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.packs.currentRowChanged.connect(self.show_pack)
        sl.addWidget(self.packs)
        self.pack_name = QLabel()
        sl.addWidget(self.pack_name)
        self.grid = QListWidget()
        self.grid.setViewMode(QListView.IconMode)
        self.grid.setIconSize(QSize(76, 76))
        self.grid.setGridSize(QSize(86, 86))
        self.grid.setResizeMode(QListView.Adjust)
        self.grid.setMovement(QListView.Static)
        self.grid.itemClicked.connect(lambda item: app.send_sticker(item.data(Qt.UserRole)))
        sl.addWidget(self.grid, 1)
        self.pages.addWidget(stickers)
        self.loaded = False
        self.show_tab(0)

    def show_tab(self, n):
        for i, b in enumerate(self.tab_buttons):
            b.setChecked(i == n)
        self.pages.setCurrentIndex(n)
        if n == 1 and not self.loaded:
            self.load_packs()

    def load_packs(self):
        self.loaded = True
        from stickers import library
        self.packs.clear()
        data = library.load()
        for folder in library.packs():
            files = library.stickers(folder)
            if not files:
                continue
            item = QListWidgetItem(QIcon(self._thumb(files[0], 40)), "")
            item.setData(Qt.UserRole, str(folder))
            done = len(library.assigned(data, folder.name))
            item.setToolTip(f"{folder.name}\n{done} of {len(files)} stickers have an emoji")
            self.packs.addItem(item)
        if self.packs.count():
            self.packs.setCurrentRow(0)

    @staticmethod
    def _thumb(path, size):
        reader = QImageReader(str(path))
        full = reader.size()
        if full.isValid():
            reader.setScaledSize(full.scaled(size, size, Qt.KeepAspectRatio))
        img = reader.read()
        return QPixmap.fromImage(img) if not img.isNull() else QPixmap(size, size)

    def show_pack(self, row):
        item = self.packs.item(row)
        if item is None:
            return
        from stickers import library
        folder = Path(item.data(Qt.UserRole))
        data = library.load()
        meanings = data["packs"].get(folder.name, {})
        self.pack_name.setText(f"  {folder.name.upper()}")
        self.grid.clear()
        for f in library.stickers(folder):
            info = meanings.get(f.name, {})
            it = QListWidgetItem(QIcon(self._thumb(f, 76)), "")
            it.setData(Qt.UserRole, str(f))
            it.setToolTip(f"{info.get('emoji', '')}  {info.get('meaning', '')}".strip() or "No emoji yet")
            self.grid.addItem(it)


class UserInfo(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(8)
        head = QHBoxLayout()
        self.title = QLabel("User Info")
        head.addWidget(self.title, 1)
        close = QToolButton()
        close.setText("✕")
        close.setAutoRaise(True)
        close.clicked.connect(app.close_side)
        head.addWidget(close)
        lay.addLayout(head)
        top = QHBoxLayout()
        self.pic = QLabel()
        top.addWidget(self.pic)
        names = QVBoxLayout()
        self.name = QLabel()
        self.status = QLabel()
        names.addWidget(self.name)
        names.addWidget(self.status)
        top.addLayout(names, 1)
        lay.addLayout(top)
        self.details = QLabel()
        self.details.setWordWrap(True)
        self.details.setTextFormat(Qt.RichText)
        self.buddy = None
        self.details.linkActivated.connect(lambda _l: self.buddy is not None and
                                           decode_in_furcoder(app.desktop, self.buddy.contact.id))
        lay.addWidget(self.details)
        self.notify = QPushButton()
        self.notify.setObjectName("panel")
        self.notify.clicked.connect(app.toggle_notifications)
        lay.addWidget(self.notify)
        clear = QPushButton("Clear history")
        clear.setObjectName("panel")
        clear.clicked.connect(app.clear_history)
        lay.addWidget(clear)
        lay.addStretch(1)

    def show_buddy(self, b):
        c = self.app.colours
        self.pic.setPixmap(avatar(b, 72))
        self.name.setText(b.name)
        self.status.setText(self.app.status_text(b))
        try:
            from stickers import library
            pack = library.favorite_pack(b.name) or "(none yet)"
        except Exception:
            pack = "(none)"
        codes = codes_for(b)
        extra = ""
        for key, title in (("furcode", "Furry Code"), ("yiffcode", "YIFF Code")):
            if codes.get(key):
                extra += (f"<br><br><span style='color:{c['dim']}'>{title}</span><br>"
                          f"<span style='font-family:Consolas'>{html.escape(codes[key])}</span>")
        if extra:
            extra += f"<br><a href='decode' style='color:{c['accent']}'>Decode in FurCoder</a>"
        self.details.setText(f"<span style='color:{c['dim']}'>Username</span><br>{self.app.network.handle_for(b.contact)}"
                             f"<br><br><span style='color:{c['dim']}'>Favourite stickers</span><br>{pack}{extra}")
        self.buddy = b
        muted = b.contact.id in self.app.settings.get("muted", [])
        self.notify.setText("Notifications: Off (turn on)" if muted else "Notifications: On (turn off)")


# ---- the program ---------------------------------------------------------------------------------------------------
class Telegram(QWidget):
    def __init__(self, desktop, network):
        super().__init__()
        self.desktop = desktop
        self.network = network
        self.frame = None
        self.settings = _settings()
        self.colours = DARK if self.settings.get("night") else LIGHT
        self.current = None
        self.unread = {}
        self.tray = None
        self.pages = QStackedWidget()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.pages)
        self.pages.addWidget(self._welcome())
        self.pages.addWidget(self._main())
        network.message_added.connect(self._message)
        network.presence_changed.connect(lambda _bid: self._refresh_list())
        network.typing_changed.connect(self._typing)
        self.restyle()
        if self.settings.get("started"):
            self.start_messaging()

    # ---- building ------------------------------------------------------------------------------------------
    def _welcome(self):
        page = QWidget()
        page.setObjectName("welcome")
        col = QVBoxLayout(page)
        col.setContentsMargins(0, 0, 0, 40)
        banner = QLabel()
        banner.setFixedHeight(190)
        banner.setAlignment(Qt.AlignCenter)
        banner.setPixmap(logo(96))
        banner.setStyleSheet("QLabel { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #1E8FD8, stop:1 #4DB6F0); }")
        col.addWidget(banner)
        col.addSpacing(26)
        title = QLabel("Telegram Desktop")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("QLabel { font: bold 16pt 'Segoe UI'; color: #222222; }")
        col.addWidget(title)
        blurb = QLabel("Welcome to the official Telegram Desktop app.\nIt's fast and secure.")
        blurb.setAlignment(Qt.AlignCenter)
        blurb.setStyleSheet("QLabel { font: 10pt 'Segoe UI'; color: #888888; }")
        col.addWidget(blurb)
        col.addSpacing(30)
        go = QPushButton("START MESSAGING")
        go.setFixedSize(300, 50)
        go.setCursor(Qt.PointingHandCursor)
        go.setStyleSheet("QPushButton { background: #40A7E3; color: white; border: none; border-radius: 4px; "
                         "font: bold 10pt 'Segoe UI'; } QPushButton:hover { background: #3A9AD3; }")
        go.clicked.connect(self.start_messaging)
        col.addWidget(go, 0, Qt.AlignCenter)
        col.addStretch(1)
        page.setStyleSheet("QWidget#welcome { background: white; }")
        return page

    def _main(self):
        page = QWidget()
        row = QHBoxLayout(page)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        # left: the chat list
        self.left = QWidget()
        self.left.setFixedWidth(300)
        lc = QVBoxLayout(self.left)
        lc.setContentsMargins(0, 0, 0, 0)
        lc.setSpacing(0)
        top = QHBoxLayout()
        top.setContentsMargins(10, 10, 10, 10)
        self.menu_btn = QToolButton()
        self.menu_btn.setText("☰")
        self.menu_btn.setAutoRaise(True)
        self.menu_btn.clicked.connect(self._main_menu)
        top.addWidget(self.menu_btn)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search")
        self.search.textChanged.connect(self._refresh_list)
        top.addWidget(self.search, 1)
        lc.addLayout(top)
        self.chats = QListWidget()
        self.chats.setItemDelegate(ChatRows(self))
        self.chats.setFrameShape(QFrame.NoFrame)
        self.chats.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.chats.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chats.currentItemChanged.connect(lambda item, _old: self.open_chat(item.data(Qt.UserRole)) if item else None)
        lc.addWidget(self.chats, 1)
        row.addWidget(self.left)
        # middle: the conversation
        self.middle = QWidget()
        mc = QVBoxLayout(self.middle)
        mc.setContentsMargins(0, 0, 0, 0)
        mc.setSpacing(0)
        self.header = QWidget()
        self.header.setFixedHeight(56)
        hl = QHBoxLayout(self.header)
        hl.setContentsMargins(16, 6, 10, 6)
        names = QVBoxLayout()
        names.setSpacing(0)
        self.chat_name = QLabel()
        self.chat_status = QLabel()
        names.addWidget(self.chat_name)
        names.addWidget(self.chat_status)
        hl.addLayout(names, 1)
        self.info_btn = QToolButton()
        self.info_btn.setText("ⓘ")
        self.info_btn.setToolTip("User Info")
        self.info_btn.setAutoRaise(True)
        self.info_btn.clicked.connect(self.toggle_info)
        hl.addWidget(self.info_btn)
        self.more_btn = QToolButton()
        self.more_btn.setText("⋮")
        self.more_btn.setAutoRaise(True)
        self.more_btn.clicked.connect(self._chat_menu)
        hl.addWidget(self.more_btn)
        mc.addWidget(self.header)
        self.wall = Wallpaper(self)
        wl = QVBoxLayout(self.wall)
        wl.setContentsMargins(0, 0, 0, 0)
        self.view = ChatView(self)
        wl.addWidget(self.view)
        self.empty = QLabel("Select a chat to start messaging")
        self.empty.setAlignment(Qt.AlignCenter)
        wl.addWidget(self.empty)
        mc.addWidget(self.wall, 1)
        self.composer = QWidget()
        self.composer.setFixedHeight(52)
        cl = QHBoxLayout(self.composer)
        cl.setContentsMargins(12, 6, 10, 6)
        self.entry = QLineEdit()
        self.entry.setPlaceholderText("Write a message...")
        self.entry.returnPressed.connect(self.send)
        cl.addWidget(self.entry, 1)
        self.smile = QToolButton()
        self.smile.setText("☺")
        self.smile.setToolTip("Emoji and stickers")
        self.smile.setAutoRaise(True)
        self.smile.clicked.connect(self.toggle_emoji)
        cl.addWidget(self.smile)
        self.send_btn = QToolButton()
        self.send_btn.setText("➤")
        self.send_btn.setToolTip("Send")
        self.send_btn.setAutoRaise(True)
        self.send_btn.clicked.connect(self.send)
        cl.addWidget(self.send_btn)
        mc.addWidget(self.composer)
        row.addWidget(self.middle, 1)
        # right: emoji and stickers, or user info
        self.side = QStackedWidget()
        self.side.setFixedWidth(340)
        self.emoji_panel = EmojiStickers(self)
        self.info_panel = UserInfo(self)
        self.side.addWidget(self.emoji_panel)
        self.side.addWidget(self.info_panel)
        self.side.hide()
        row.addWidget(self.side)
        self._show_empty(True)
        return page

    def restyle(self):
        c = self.colours
        self.setStyleSheet(
            f"QWidget {{ font-family: 'Segoe UI', '{EMOJI_FONT}'; }}"
            f"QListWidget {{ background: {c['side']}; border: none; color: {c['text']}; outline: 0; }}"
            f"QLineEdit {{ background: {c['search']}; border: none; border-radius: 5px; padding: 6px 10px;"
            f" color: {c['text']}; font-size: 10pt; }}"
            f"QToolButton {{ color: {c['dim']}; font-size: 16pt; border: none; padding: 2px 6px; }}"
            f"QToolButton:hover {{ color: {c['accent']}; }}"
            f"QPushButton#panel {{ background: transparent; color: {c['accent']}; border: none; padding: 7px; "
            f"font: bold 9pt; text-align: left; }} QPushButton#panel:checked {{ border-bottom: 2px solid {c['accent']}; }}"
            f"QLabel {{ color: {c['text']}; }}")
        for w in (self.left, self.middle, self.header, self.composer, self.side, self.emoji_panel, self.info_panel):
            w.setAutoFillBackground(True)
            pal = w.palette()
            pal.setColor(w.backgroundRole(), QColor(c["panel"] if w in (self.side, self.emoji_panel, self.info_panel)
                                                    else c["bg"]))
            w.setPalette(pal)
        self.chat_name.setStyleSheet(f"QLabel {{ font: bold 10pt 'Segoe UI'; color: {c['text']}; }}")
        self.empty.setStyleSheet(f"QLabel {{ color: white; font: bold 10pt 'Segoe UI'; background: {c['pill']};"
                                 " border-radius: 10px; padding: 4px 12px; }}")
        self.info_panel.title.setStyleSheet(f"QLabel {{ font: bold 11pt 'Segoe UI'; color: {c['text']}; }}")
        self.info_panel.name.setStyleSheet(f"QLabel {{ font: 11pt 'Segoe UI'; color: {c['text']}; }}")
        self.emoji_panel.pack_name.setStyleSheet(f"QLabel {{ color: {c['dim']}; font: bold 8pt 'Segoe UI'; padding: 4px; }}")
        self.wall.update()
        self.chats.viewport().update()
        if self.current:
            self.open_chat(self.current)

    # ---- signing in -----------------------------------------------------------------------------------------
    def start_messaging(self):
        if not self.settings.get("started"):
            self.settings["started"] = True
            _save_settings(self.settings)
        self.pages.setCurrentIndex(1)
        if not self.network.signed_in:
            self.network.sign_in()
        self._tray_on()
        self._refresh_list()

    # ---- the list ------------------------------------------------------------------------------------------
    def last_entry(self, b):
        return next((e for e in reversed(b.history) if e["kind"] in ("user", "contact")), None)

    def preview(self, b):
        """(the chat list's second line, whether it's in the accent colour)."""
        e = self.last_entry(b)
        if e is None:
            return self.status_text(b), b.presence == ONLINE
        if e.get("sticker"):
            return (f"You: {e['text'] if not e['text'].startswith('[') else ''} Sticker" if e["kind"] == "user"
                    else f"{e['text']} Sticker"), True
        return (f"You: {e['text']}" if e["kind"] == "user" else e["text"]).replace("\n", " "), False

    def status_text(self, b):
        if b.busy:
            return "typing..."
        return {ONLINE: "online", BUSY: "online", AWAY: "last seen just now"}.get(b.presence, "last seen recently")

    def _refresh_list(self, *_):
        if not hasattr(self, "chats"):
            return
        wanted = self.search.text().strip().lower()
        buddies = [b for b in self.network.buddies.values() if not wanted or wanted in b.name.lower()]

        def order(b):
            """Who'll answer first: online, then away, then offline; most recent chats first within each."""
            here = {ONLINE: 0, BUSY: 0, AWAY: 1}.get(b.presence, 2)
            e = self.last_entry(b)
            return (here, 0, -_when(e).timestamp(), "") if e is not None else (here, 1, 0, b.name.lower())
        buddies.sort(key=order)
        self.chats.blockSignals(True)
        self.chats.clear()
        for b in buddies:
            item = QListWidgetItem()
            item.setData(Qt.UserRole, b.contact.id)
            self.chats.addItem(item)
            if b.contact.id == self.current:
                self.chats.setCurrentItem(item)
        self.chats.blockSignals(False)

    # ---- a chat --------------------------------------------------------------------------------------------
    def _show_empty(self, empty):
        self.view.setVisible(not empty)
        self.empty.setVisible(empty)
        self.header.setVisible(not empty)
        self.composer.setVisible(not empty)

    def open_chat(self, bid):
        b = self.network.buddies.get(bid)
        if b is None:
            return
        self.current = bid
        self.unread.pop(bid, None)
        b.unread = False
        self._update_tray()
        self._show_empty(False)
        self.chat_name.setText(b.name)
        self._update_status(b)
        entries = b.history[-200:]
        last_reply = max((i for i, e in enumerate(entries) if e["kind"] == "contact"), default=-1)
        self.view.show_entries(entries, read_upto=last_reply)
        if self.side.isVisible() and self.side.currentWidget() is self.info_panel:
            self.info_panel.show_buddy(b)
        self.chats.viewport().update()
        self.entry.setFocus()

    def _update_status(self, b):
        c = self.colours
        text = self.status_text(b)
        live = b.busy or b.presence in (ONLINE, BUSY)
        self.chat_status.setText(text)
        self.chat_status.setStyleSheet(f"QLabel {{ font: 9pt 'Segoe UI'; color: {c['accent'] if live else c['dim']}; }}")

    def send(self):
        text = self.entry.text().strip()
        b = self.network.buddies.get(self.current)
        if not text or b is None:
            return
        self.entry.clear()
        self.network.send(b, text)

    def send_sticker(self, path):
        b = self.network.buddies.get(self.current)
        if b is None or not path:
            return
        self.network.send_sticker(b, path)

    def insert_emoji(self, emoji):
        self.entry.insert(emoji)
        self.entry.setFocus()

    def _message(self, bid, e):
        b = self.network.buddies.get(bid)
        if b is None:
            return
        if bid == self.current:
            if e["kind"] == "contact":
                self.open_chat(bid)                        # (your messages so far now show as read)
            else:
                self.view.add(e, read=False)
        incoming = e["kind"] == "contact"
        if incoming:
            looking = bid == self.current and self.frame is not None and self.desktop.active is self.frame
            if not looking:
                self.unread[bid] = self.unread.get(bid, 0) + 1
                self._update_tray()
                if bid not in self.settings.get("muted", []):
                    if sound.play_file(NOTIFY_SOUND) is None and not sound.is_muted():
                        sound.play("notify")                  # (the sound file is missing: Windows' own)
                    if self.frame is not None:
                        self.frame.flash()
        self._refresh_list()

    def _typing(self, bid, _on):
        b = self.network.buddies.get(bid)
        if b is not None and bid == self.current:
            self._update_status(b)
        self.chats.viewport().update()

    # ---- panels and menus ------------------------------------------------------------------------------------
    def toggle_emoji(self):
        if self.side.isVisible() and self.side.currentWidget() is self.emoji_panel:
            self.side.hide()
        else:
            self.side.setCurrentWidget(self.emoji_panel)
            self.side.show()

    def toggle_info(self):
        b = self.network.buddies.get(self.current)
        if b is None:
            return
        if self.side.isVisible() and self.side.currentWidget() is self.info_panel:
            self.side.hide()
        else:
            self.info_panel.show_buddy(b)
            self.side.setCurrentWidget(self.info_panel)
            self.side.show()

    def close_side(self):
        self.side.hide()

    def toggle_notifications(self):
        muted = self.settings.setdefault("muted", [])
        if self.current in muted:
            muted.remove(self.current)
        elif self.current:
            muted.append(self.current)
        _save_settings(self.settings)
        b = self.network.buddies.get(self.current)
        if b is not None:
            self.info_panel.show_buddy(b)

    def clear_history(self):
        b = self.network.buddies.get(self.current)
        if b is None:
            return
        b.history = []
        try:
            b.path.write_text(json.dumps({"messages": []}, indent=1), encoding="utf-8")
        except OSError:
            pass
        self.open_chat(b.contact.id)
        self._refresh_list()

    def _chat_menu(self):
        menu = QMenu(self)
        menu.addAction("View profile", self.toggle_info)
        muted = self.current in self.settings.get("muted", [])
        menu.addAction("Enable notifications" if muted else "Disable notifications", self.toggle_notifications)
        menu.addAction("Clear history", self.clear_history)
        menu.exec(self.more_btn.mapToGlobal(self.more_btn.rect().bottomLeft()))

    def _main_menu(self):
        menu = QMenu(self)
        night = menu.addAction("Night Mode", self.toggle_night)
        night.setCheckable(True)
        night.setChecked(bool(self.settings.get("night")))
        menu.addAction("Sticker Manager...", self._open_sticker_manager)
        menu.addSeparator()
        menu.addAction("About Telegram", self._about)
        menu.exec(self.menu_btn.mapToGlobal(self.menu_btn.rect().bottomLeft()))

    def toggle_night(self):
        self.settings["night"] = not self.settings.get("night")
        _save_settings(self.settings)
        self.colours = DARK if self.settings["night"] else LIGHT
        self.restyle()

    def _open_sticker_manager(self):
        try:
            from stickers.manager import open_stickers
            open_stickers(self.desktop)
        except Exception:
            pass

    def _about(self):
        from claudecore import host
        host.message(self.desktop, "About Telegram", "Telegram Desktop\n\nA fast and secure messaging app, with "
                     "stickers. Your stickers come from E:\\Sticker Packs; give them meanings in the Sticker Manager.",
                     "info")

    # ---- the notification area ---------------------------------------------------------------------------------
    def _tray_on(self):
        if self.tray is not None:
            return
        try:
            from ...tray import TrayIcon
            self.tray = TrayIcon(self.desktop, QIcon(tray_picture(0)), self.desktop)
        except Exception:
            self.tray = None                               # (no notification area to put it in)
            return
        menu = QMenu()
        menu.addAction("Open Telegram", self._bring_forward)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(lambda *_a: self._bring_forward())
        self._update_tray()
        self.tray.show()

    def _update_tray(self):
        if self.tray is None:
            return
        count = sum(self.unread.values())
        self.tray.setIcon(QIcon(tray_picture(count)))
        self.tray.setToolTip(f"Telegram - {count} unread message{'s' if count != 1 else ''}" if count else "Telegram")

    def _bring_forward(self):
        if self.frame is not None and isValid(self.frame):
            self.desktop.open_window(self.frame)
            waiting = next(iter(self.unread), None)           # straight to a chat with something new
            if waiting is not None and waiting != self.current:
                self.open_chat(waiting)
                self._refresh_list()

    def _tray_off(self):
        if self.tray is not None:
            self.tray.hide()
            self.tray.deleteLater()
            self.tray = None

    def closeEvent(self, event):
        self._tray_off()
        for movie in self.view.movies:
            movie.stop()
        self.network.sign_out()
        event.accept()


_holder = {}


def launch(desktop):
    from ...wm import XPWindow
    win = _holder.get("win")
    if win is not None and isValid(win):
        desktop.open_window(win)
        return win
    if "net" not in _holder:
        _holder["net"] = TelegramNetwork()
    body = Telegram(desktop, _holder["net"])
    win = XPWindow(desktop, "Telegram", body, telegram_icon(), size=(980, 640))
    body.frame = win
    _holder["win"] = win
    desktop.open_window(win)
    return win


def shutdown():
    win = _holder.get("win")
    if win is not None and isValid(win):
        win.content._tray_off()
        win.content.network.sign_out()
