"""Discord: your friends, a server of your own, stickers, and what you're playing.

The same buddies as every other messenger (core.py), in Discord's dark look: a server rail (Home and The Den), the
Friends page with Active Now, direct messages, The Den's text channels with a member list, and your panel in the
corner.

Stickers work as on Telegram (each buddy's favourite pack, from the Sticker Manager): a reply that starts or ends with
one of their sticker emojis arrives as the sticker, and you can send them from the composer.

What you're playing is broadcast: while a game from the Games menu is open, your panel and the member list show
"Playing <game>", your friends know it when they talk to you, and a friend may message you about it. For the Internet
games (Checkers, Reversi, Backgammon, Hearts, Spades) a friend may offer to be your player 2; accept and they sit down
at your table on the Zone. Friends play the games here too, now and then (Active Now).

The Den's channels are group chats: post and one or two friends who are on answer (an @mention picks who), and they
chat there on their own once in a while. Channel histories live in data/messengers/discord/channels/."""
import html
import json
import random
import time
from datetime import datetime, timedelta

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QImageReader, QMovie, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (QAbstractItemView, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget,
                               QListWidgetItem, QMenu, QPushButton, QScrollArea, QStackedWidget, QStyle,
                               QStyledItemDelegate, QToolButton, QVBoxLayout, QWidget)
from shiboken6 import isValid

from ... import sound
from ...paths import DATA
from .core import AWAY, BUSY, OFFLINE, ONLINE, clean_reply, timefmt
from .telegram import EMOJI_FONT, EmojiStickers, TelegramNetwork, _clock, _when, avatar, emoji_picture

SETTINGS = DATA / "discord.json"
CHANNEL_DIR = DATA / "messengers" / "discord" / "channels"
NOTIFY_SOUND = "discord_notification.mp3"             # assets/sounds: Discord's own message sound
LOGO = "Discord Details/discord_icon.png"               # in Local Storage, the user's own copy of the logo
SERVER = "The Den"
CHANNELS = (("general", "Chat about anything."),
            ("gaming", "What everyone's playing. Looking for a player 2? Ask here."),
            ("art-and-pics", "Art, pictures, fursuits and cute things."))
ZONE_GAMES = {"ibackgammon", "icheckers", "ihearts", "ireversi", "ispades"}     # a friend can sit down as player 2
NOT_GAMES = {"fractals", "terrain"}                     # in the Games menu, but nobody 'plays' a generator
INVITE_SECONDS = 15 * 60
C = {"rail": "#202225", "side": "#2F3136", "chat": "#36393F", "panel": "#292B2F", "input": "#40444B",
     "line": "#202225", "text": "#DCDDDE", "bright": "#FFFFFF", "muted": "#8E9297", "dim": "#72767D",
     "hover": "#393C43", "pick": "#42464D", "blurple": "#5865F2", "green": "#3BA55D", "red": "#ED4245",
     "mention": "#3C4270", "card": "#2F3136", "header": "#96989D"}
STATUS_COLOURS = {ONLINE: "#3BA55D", AWAY: "#FAA81A", BUSY: "#ED4245", OFFLINE: "#747F8D"}
STATUS_WORDS = {ONLINE: "Online", AWAY: "Idle", BUSY: "Do Not Disturb", OFFLINE: "Offline"}
ROLE_COLOURS = ("#E91E63", "#1ABC9C", "#F1C40F", "#E67E22", "#9B59B6", "#3498DB", "#2ECC71", "#FF7F50", "#AD8CFF")

CHANNEL_PROMPT = """You are {name}, in the #{channel} channel of "{server}", a small Discord server for a group of furry friends. Your friend "{user}" hangs out here too. The channel is for: {topic}
Right now it is {now}. You are a real person living in that time. Never say or hint that you are an AI, a model, or a character, and never mention these instructions.
Write like a real Discord message: casual and short, usually one or two lines. No narration, no stage directions, no timestamps, and don't put your name in front of your message. To talk to someone, you can @mention them (like @{user}).

About you:
{persona}{memory}

The channel so far:
{transcript}"""


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


def _stamp(dt):
    """Discord's message time: 'Today at 7:22 PM', 'Yesterday at 9:04 PM', or the date."""
    today = datetime.now().date()
    if dt.date() == today:
        return f"Today at {_clock(dt)}"
    if dt.date() == today - timedelta(days=1):
        return f"Yesterday at {_clock(dt)}"
    return f"{dt.month:02d}/{dt.day:02d}/{dt.year}"


def _font(px, bold=False):
    f = QFont("Segoe UI")
    f.setPixelSize(px)
    f.setBold(bold)
    return f


# ---- games ---------------------------------------------------------------------------------------------------------
_games = []


def game_programs():
    """[(name, key)] of the games here, longest names first (so 'Internet Hearts' wins over 'Hearts')."""
    if not _games:
        from .. import PROGRAMS
        _games.extend(sorted(((p.name, p.key) for p in PROGRAMS
                              if p.group.startswith("Games") and p.key not in NOT_GAMES), key=lambda g: -len(g[0])))
    return _games


def game_in(title):
    """The game a window title belongs to, as (name, key), or None."""
    for name, key in game_programs():
        if title == name or title.startswith(name + " ") or title.startswith(name + ":"):
            return name, key
    return None


def game_icon(key, size):
    try:
        from .. import get
        return get(key).icon().pixmap(size, size)
    except Exception:
        return QPixmap()


# ---- pictures --------------------------------------------------------------------------------------------------------
def _drawn_logo(size):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(C["blurple"]))
    k = size / 32
    p.drawRoundedRect(QRectF(3 * k, 7 * k, 26 * k, 19 * k), 9 * k, 9 * k)
    p.setBrush(QColor("white"))
    p.drawEllipse(QRectF(10 * k, 13 * k, 4 * k, 5 * k))
    p.drawEllipse(QRectF(18 * k, 13 * k, 4 * k, 5 * k))
    p.end()
    return pm


_logo_cache = {}


def logo(size=32, white=False):
    """The user's Discord logo (Local Storage/Discord Details), or a drawn one; white=True for the Home button."""
    if (size, white) not in _logo_cache:
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
        if pm.isNull():
            pm = _drawn_logo(size)
        if white:
            p = QPainter(pm)
            p.setCompositionMode(QPainter.CompositionMode_SourceIn)
            p.fillRect(pm.rect(), QColor("white"))
            p.end()
        _logo_cache[(size, white)] = pm
    return _logo_cache[(size, white)]


def discord_icon():
    icon = QIcon()
    for size in (16, 32, 48):
        icon.addPixmap(logo(size))
    return icon


def tray_picture(count, size=16):
    """Discord's logo for the notification area, with a red badge when messages are waiting."""
    pm = QPixmap(logo(size))
    if count:
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        text = str(count) if count < 100 else "99+"
        w = max(size * 0.62, size * (0.36 + 0.2 * len(text)))
        badge = QRectF(size - w, size * 0.42, w, size * 0.58)
        p.setPen(QPen(QColor("white"), 1))
        p.setBrush(QColor(C["red"]))
        p.drawRoundedRect(badge, badge.height() / 2, badge.height() / 2)
        p.setPen(QColor("white"))
        f = QFont("Tahoma")
        f.setPixelSize(max(6, int(size * 0.46)))
        f.setBold(True)
        p.setFont(f)
        p.drawText(badge, Qt.AlignCenter, text)
        p.end()
    return pm


def my_avatar(size):
    """Your account picture in a circle (or Discord's default: the logo on blurple)."""
    from ... import user
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    pic = None
    try:
        pic = user.picture_pixmap()
    except Exception:
        pic = None
    clip = QPainterPath()
    clip.addEllipse(QRectF(0, 0, size, size))
    if pic:
        img = pic.toImage()
        side = min(img.width(), img.height())
        img = img.copy((img.width() - side) // 2, (img.height() - side) // 2, side, side)
        p.setClipPath(clip)
        p.drawImage(QRectF(0, 0, size, size), img)
    else:
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(C["blurple"]))
        p.drawEllipse(QRectF(0, 0, size, size))
        inner = int(size * 0.6)
        p.drawPixmap((size - inner) // 2, (size - inner) // 2, logo(inner, white=True))
    p.end()
    return pm


def draw_status(p, cx, cy, r, presence, ring):
    """Discord's status dot: green, an idle moon, a do-not-disturb bar, or an empty grey ring."""
    p.save()
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(ring))
    p.drawEllipse(QPointF(cx, cy), r + 2.5, r + 2.5)
    p.setBrush(QColor(STATUS_COLOURS.get(presence, STATUS_COLOURS[OFFLINE])))
    p.drawEllipse(QPointF(cx, cy), r, r)
    p.setBrush(QColor(ring))
    if presence == AWAY:
        p.drawEllipse(QPointF(cx - r * 0.45, cy - r * 0.45), r * 0.65, r * 0.65)
    elif presence == BUSY:
        p.drawRoundedRect(QRectF(cx - r * 0.6, cy - r * 0.18, r * 1.2, r * 0.36), r * 0.18, r * 0.18)
    elif presence not in (ONLINE,):
        p.drawEllipse(QPointF(cx, cy), r * 0.5, r * 0.5)
    p.restore()


def role_colour(bid):
    return ROLE_COLOURS[sum(map(ord, bid)) % len(ROLE_COLOURS)]


def sticker_glyph(size, colour):
    """The composer's sticker button: a square with a peeled corner."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    k = size / 24
    path = QPainterPath()
    path.moveTo(4 * k, 6 * k)
    path.quadTo(4 * k, 4 * k, 6 * k, 4 * k)
    path.lineTo(18 * k, 4 * k)
    path.quadTo(20 * k, 4 * k, 20 * k, 6 * k)
    path.lineTo(20 * k, 13 * k)
    path.lineTo(13 * k, 20 * k)
    path.lineTo(6 * k, 20 * k)
    path.quadTo(4 * k, 20 * k, 4 * k, 18 * k)
    path.closeSubpath()
    p.setPen(QPen(QColor(colour), 2 * k))
    p.setBrush(Qt.NoBrush)
    p.drawPath(path)
    p.drawLine(QPointF(13 * k, 20 * k), QPointF(13 * k, 15 * k))
    p.drawLine(QPointF(13 * k, 15 * k), QPointF(20 * k, 13 * k))
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(colour))
    p.drawEllipse(QRectF(8.5 * k, 8.5 * k, 2.4 * k, 2.4 * k))
    p.drawEllipse(QRectF(13.5 * k, 8.5 * k, 2.4 * k, 2.4 * k))
    p.end()
    return pm


# ---- the network ------------------------------------------------------------------------------------------------
class Channel:
    """One of The Den's text channels: a group chat, kept like a buddy's history."""

    def __init__(self, name, topic):
        self.name = name
        self.topic = topic
        self.path = CHANNEL_DIR / f"{name}.json"
        try:
            self.history = json.loads(self.path.read_text(encoding="utf-8")).get("messages", [])
        except (OSError, ValueError):
            self.history = []

    def add(self, kind, text, **extra):
        entry = {"kind": kind, "text": text, "ts": datetime.now().astimezone().isoformat(timespec="seconds"), **extra}
        self.history.append(entry)
        del self.history[:-400]
        self.save()
        return entry

    def save(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps({"messages": self.history}, indent=1), encoding="utf-8")
        except OSError:
            pass


class DiscordNetwork(TelegramNetwork):
    """Telegram's stickers, plus channels and the game you're playing."""
    key = "discord"
    title = "Discord"
    channel_added = Signal(str, dict)       # channel name, entry
    channel_typing = Signal(str)            # channel name
    activity_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.channels = {name: Channel(name, topic) for name, topic in CHANNELS}
        self.typing_in = {name: set() for name in self.channels}
        self.activity = None                # {"name", "key", "since"} while you're playing something
        self.show_activity = True
        self.pending_invite = {}            # buddy id -> game key: their next message comes with an invitation
        self.chatter = QTimer(self, interval=4 * 60 * 1000, timeout=self._chatter)

    def handle_for(self, contact):
        return contact.screen_name

    def sign_in(self):
        super().sign_in()
        self.chatter.start()

    def sign_out(self):
        self.chatter.stop()
        super().sign_out()

    # ---- what people are playing -------------------------------------------------------------------------------
    def friend_activity(self, b):
        """(game name, key) a friend is playing right now, or None: a few of them, now and then (per half hour)."""
        if b.presence not in (ONLINE, BUSY):
            return None
        rng = random.Random(f"{b.contact.id}:{int(time.time() // 1800)}:discord")
        if rng.random() < 0.28:
            return rng.choice(game_programs())
        return None

    def set_activity(self, game):
        """game: (name, key) of what you're playing, or None."""
        cur = self.activity
        if game is None:
            if cur is not None:
                self.activity = None
                self.pending_invite.clear()
                self.activity_changed.emit()
            return
        name, key = game
        if cur is not None and cur["key"] == key:
            return
        self.activity = {"name": name, "key": key, "since": time.time()}
        self.activity_changed.emit()
        token = self.activity
        QTimer.singleShot(random.randint(15, 60) * 1000, lambda: self._game_started(token))

    def _game_started(self, token):
        """You've been playing a little while: maybe a friend who's on says something (or offers to play)."""
        if self.activity is not token or not self.show_activity or not self.signed_in:
            return
        online = [b for b in self.buddies.values() if b.presence == ONLINE and not b.busy]
        if not online:
            return
        talked = [b for b in online if b.history] or online
        b = random.choice(talked)
        user, name, key = self.my_handle(), token["name"], token["key"]
        if key in ZONE_GAMES:
            if random.random() < 0.85:
                self.pending_invite[b.contact.id] = key
                self.reach_out(b, f"Discord shows that {user} just started playing {name} on the Zone. Send them a "
                                  "short message offering to be their player 2 - you'd hop on the Zone and join their "
                                  "game.")
        elif random.random() < 0.45:
            if random.random() < 0.55:
                self.reach_out(b, f"Discord shows that {user} just started playing {name}. Send them a short "
                                  "message about it.")
            else:
                self._channel_reply(self.channels["gaming"], b,
                                    f"Discord shows that {user} just started playing {name}. Say something about it "
                                    f"to them here in #gaming (you can @mention them as @{user}).")

    def _memory(self, b):
        extra = ""
        if self.activity is not None and self.show_activity:
            mins = int((time.time() - self.activity["since"]) // 60)
            extra += (f"\n\nDiscord shows that {self.my_handle()} is playing {self.activity['name']} right now "
                      f"(for {mins} minute{'s' if mins != 1 else ''} so far).")
        mine = self.friend_activity(b)
        if mine is not None:
            extra += f"\nDiscord shows you as playing {mine[0]} right now."
        return super()._memory(b) + extra

    def _deliver(self, b, text):
        super()._deliver(b, text)
        key = self.pending_invite.pop(b.contact.id, None)
        if key is not None and self.activity is not None and self.activity["key"] == key:
            e = b.add("invite", f"{b.name} wants to join you in {self.activity['name']}.", game=self.activity["name"],
                      key=key)
            self.message_added.emit(b.contact.id, e)

    # ---- channels ------------------------------------------------------------------------------------------------
    def post(self, name, text, **extra):
        ch = self.channels[name]
        e = ch.add("user", text, **extra)
        self.channel_added.emit(name, e)
        self._plan_replies(ch, text)

    def post_sticker(self, name, path):
        from stickers import library
        self.post(name, library.describe(path), sticker=str(path))

    def _plan_replies(self, ch, text):
        """One or two friends who are on answer; someone @mentioned (or named) answers first."""
        from ... import llm_server
        if not llm_server.ready():
            return
        online = [b for b in self.buddies.values() if b.presence == ONLINE]
        if not online:
            return
        low = text.lower()
        named = [b for b in online if b.name.lower() in low]
        others = [b for b in online if b not in named]
        random.shuffle(others)
        who = named[:2] or others[:1 if random.random() < 0.6 else 2]
        for b in who:
            self._heard(b, self.my_handle(), text)

        def go(i):
            if i < len(who):
                self._channel_reply(ch, who[i], then=lambda: go(i + 1))
        QTimer.singleShot(random.randint(1500, 5000), lambda: go(0))

    def _chatter(self):
        """Once in a while, someone says something in a channel on their own (and maybe someone answers)."""
        from ... import llm_server
        if not self.signed_in or not llm_server.ready() or random.random() > 0.35:
            return
        online = [b for b in self.buddies.values() if b.presence == ONLINE and not b.busy]
        if not online:
            return
        ch = self.channels[random.choice(("general", "general", "gaming", "art-and-pics"))]
        first = random.choice(online)
        rest = [b for b in online if b is not first]

        def answer():
            if rest and random.random() < 0.5:
                self._channel_reply(ch, random.choice(rest))
        self._channel_reply(ch, first, f"Say something new in #{ch.name}: start a topic that fits you and the "
                                       "channel, or pick up on what's been said.", then=answer)

    def _channel_reply(self, ch, b, instruction=None, then=None):
        def finish():
            if then is not None:
                QTimer.singleShot(random.randint(1500, 6000), then)
        from ... import ai_models, broker, llm_server
        if b.busy or not llm_server.available():
            finish()
            return
        b.busy = True
        self.typing_in[ch.name].add(b.contact.id)
        self.channel_typing.emit(ch.name)
        user = self.my_handle()
        lines = []
        for e in ch.history[-20:]:
            if e["kind"] == "user":
                lines.append(f"{user}: {e['text']}")
            elif e["kind"] == "contact":
                other = self.buddies.get(e.get("who", ""))
                lines.append(f"{other.name if other else e.get('name', 'someone')}: {e['text']}")
        system = CHANNEL_PROMPT.format(name=b.name, channel=ch.name, server=SERVER, user=user, topic=ch.topic,
                                       now=timefmt.now_text(b.contact.timezone), persona=b.contact.persona.strip(),
                                       memory=self._memory(b), transcript="\n".join(lines) or "(nothing yet)")
        ask = instruction or f"Write your next message in #{ch.name}."
        msgs = [{"role": "system", "content": system},
                {"role": "user", "content": f"[{ask} If you have nothing to add, reply with just SKIP.]"}]
        model = ai_models.model_for("conversation", resident=b.name)

        def stop():
            b.busy = False
            self.typing_in[ch.name].discard(b.contact.id)
            self.channel_typing.emit(ch.name)

        def done(text, err):
            reply = clean_reply(text or "", b.name) if not err else ""
            if not reply or reply.strip().upper().startswith("SKIP"):
                stop()
                finish()
                return

            def deliver():
                stop()
                self._channel_deliver(ch, b, reply)
                finish()
            QTimer.singleShot(int(min(8.0, 0.8 + len(reply) / 18) * 1000), deliver)

        broker.get().chat(model, msgs, {"num_ctx": int(ai_models.config()["context"]),
                                        "temperature": b.contact.temperature}, done, broker.AIM, think=False)

    def _channel_deliver(self, ch, b, text):
        mention = self.my_handle().lower() in text.lower()
        try:
            from stickers import library
            hit = library.sticker_in(b.name, text)
        except Exception:
            hit = None
        if hit is not None:
            path, emoji, meaning = hit
            rest = text.strip()
            rest = (rest[len(emoji):] if rest.startswith(emoji) else rest[:-len(emoji)]).strip()
            if rest:
                self.channel_added.emit(ch.name, ch.add("contact", rest, who=b.contact.id, mention=mention))
            self.channel_added.emit(ch.name, ch.add("contact", emoji, who=b.contact.id, sticker=str(path),
                                                    meaning=meaning, mention=mention and not rest))
            self._heard(b, b.name, f"{rest} [sticker: {emoji} {meaning}]".strip())
        else:
            self.channel_added.emit(ch.name, ch.add("contact", text, who=b.contact.id, mention=mention))
            self._heard(b, b.name, text)


# ---- the server rail -------------------------------------------------------------------------------------------------
class Rail(QWidget):
    """Home (direct messages and friends) and The Den, down the far left."""
    SPOTS = ("home", "sep", "den")

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setFixedWidth(72)
        self.setMouseTracking(True)
        self.hover = None

    def _rect(self, i):
        y = 12 + sum(16 if s == "sep" else 56 for s in self.SPOTS[:i])
        return QRectF(12, y, 48, 48)

    def _at(self, pos):
        for i, spot in enumerate(self.SPOTS):
            if spot != "sep" and self._rect(i).contains(pos):
                return spot
        return None

    def mouseMoveEvent(self, event):
        spot = self._at(event.position())
        if spot != self.hover:
            self.hover = spot
            self.setToolTip({"home": "Home", "den": SERVER}.get(spot, ""))
            self.update()

    def leaveEvent(self, event):
        self.hover = None
        self.update()

    def mousePressEvent(self, event):
        spot = self._at(event.position())
        if spot == "home":
            self.app.show_home()
        elif spot == "den":
            self.app.show_server()

    def paintEvent(self, event):
        app = self.app
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(C["rail"]))
        for i, spot in enumerate(self.SPOTS):
            r = self._rect(i)
            if spot == "sep":
                p.fillRect(QRectF(24, r.top() - 4, 24, 2), QColor(C["chat"]))
                continue
            picked = app.server == spot
            lit = picked or self.hover == spot
            rad = 16 if lit else 24
            unread = app.channel_unread_total() if spot == "den" else 0
            if picked or unread or self.hover == spot:      # the white pill on the left edge
                h = 40 if picked else 20 if self.hover == spot else 8
                p.setPen(Qt.NoPen)
                p.setBrush(QColor("white"))
                p.drawRoundedRect(QRectF(-4, r.center().y() - h / 2, 8, h), 4, 4)
            p.setPen(Qt.NoPen)
            if spot == "home":
                p.setBrush(QColor(C["blurple"] if lit else C["chat"]))
                p.drawRoundedRect(r, rad, rad)
                p.drawPixmap(int(r.left() + 10), int(r.top() + 10), logo(28, white=True) if lit else logo(28))
                count = sum(app.unread.values())
                if count:
                    badge = QRectF(r.right() - 16, r.bottom() - 16, 20 if count < 10 else 26, 20)
                    p.setPen(QPen(QColor(C["rail"]), 3))
                    p.setBrush(QColor(C["red"]))
                    p.drawRoundedRect(badge, 10, 10)
                    p.setPen(QColor("white"))
                    p.setFont(_font(11, True))
                    p.drawText(badge, Qt.AlignCenter, str(count) if count < 100 else "99+")
            else:
                p.setBrush(QColor("#E67E22" if lit else C["chat"]))
                p.drawRoundedRect(r, rad, rad)
                p.setPen(QColor("white" if lit else C["text"]))
                p.setFont(_font(15, True))
                p.drawText(r, Qt.AlignCenter, "TD")


# ---- the sidebar, member list and friends list -----------------------------------------------------------------------
class SideRows(QStyledItemDelegate):
    HEIGHTS = {"friends": 44, "header": 40, "dm": 44, "category": 36, "channel": 34}

    def __init__(self, app):
        super().__init__(app)
        self.app = app

    def sizeHint(self, option, index):
        row = index.data(Qt.UserRole)
        return QSize(option.rect.width(), self.HEIGHTS.get(row[0], 34))

    def paint(self, p, option, index):
        app = self.app
        row = index.data(Qt.UserRole)
        kind = row[0]
        r = QRectF(option.rect)
        p.save()
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(r, QColor(C["side"]))
        here = app.where == (kind,) + tuple(row[1:2]) if kind in ("friends", "dm", "channel") else False
        hover = bool(option.state & QStyle.State_MouseOver)
        box = QRectF(r.left() + 8, r.top() + 1, r.width() - 16, r.height() - 2)
        if kind in ("friends", "dm", "channel") and (here or hover):
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(C["pick"] if here else C["hover"]))
            p.drawRoundedRect(box, 4, 4)
        if kind == "friends":
            p.drawPixmap(int(box.left() + 10), int(box.top() + 9), emoji_picture("👥", 22))
            p.setPen(QColor(C["bright"] if here else C["muted"]))
            p.setFont(_font(15, True))
            p.drawText(QRectF(box.left() + 44, box.top(), box.width() - 50, box.height()),
                       Qt.AlignLeft | Qt.AlignVCenter, "Friends")
        elif kind == "header" or kind == "category":
            p.setPen(QColor(C["muted"]))
            p.setFont(_font(11, True))
            text = row[1].upper()
            if kind == "category":
                text = "⌄  " + text
            p.drawText(QRectF(r.left() + 16, r.top() + 12, r.width() - 24, r.height() - 12),
                       Qt.AlignLeft | Qt.AlignVCenter, text)
        elif kind == "dm":
            b = app.network.buddies.get(row[1])
            if b is not None:
                p.drawPixmap(int(box.left() + 8), int(box.top() + 5), avatar(b, 32))
                draw_status(p, box.left() + 36, box.top() + 33, 4.5, b.presence,
                            C["pick"] if here else C["hover"] if hover else C["side"])
                unread = app.unread.get(b.contact.id, 0)
                p.setPen(QColor(C["bright"] if here or unread else C["muted"]))
                p.setFont(_font(14, bool(unread)))
                game = app.network.friend_activity(b)
                top = box.top() + (4 if game else 0)
                h = 22 if game else box.height()
                name_r = QRectF(box.left() + 50, top, box.width() - (86 if unread else 56), h)
                p.drawText(name_r, Qt.AlignLeft | Qt.AlignVCenter,
                           p.fontMetrics().elidedText(b.name, Qt.ElideRight, int(name_r.width())))
                if game:
                    p.setPen(QColor(C["muted"]))
                    p.setFont(_font(11))
                    sub = QRectF(box.left() + 50, top + 18, box.width() - 56, 16)
                    p.drawText(sub, Qt.AlignLeft | Qt.AlignVCenter,
                               p.fontMetrics().elidedText(f"Playing {game[0]}", Qt.ElideRight, int(sub.width())))
                if unread:
                    badge = QRectF(box.right() - 28, box.center().y() - 8, 20, 16)
                    p.setPen(Qt.NoPen)
                    p.setBrush(QColor(C["red"]))
                    p.drawRoundedRect(badge, 8, 8)
                    p.setPen(QColor("white"))
                    p.setFont(_font(11, True))
                    p.drawText(badge, Qt.AlignCenter, str(unread))
        elif kind == "channel":
            name = row[1]
            unread = app.channel_unread.get(name, 0)
            if unread and not here:
                p.setPen(Qt.NoPen)
                p.setBrush(QColor("white"))
                p.drawRoundedRect(QRectF(-4, box.center().y() - 4, 8, 8), 4, 4)
            bright = here or unread
            p.setPen(QColor(C["bright"] if bright else C["dim"]))
            p.setFont(_font(20))
            p.drawText(QRectF(box.left() + 8, box.top(), 20, box.height()), Qt.AlignCenter, "#")
            p.setPen(QColor(C["bright"] if bright else C["muted"]))
            p.setFont(_font(15, bool(unread) and not here))
            p.drawText(QRectF(box.left() + 34, box.top(), box.width() - 40, box.height()),
                       Qt.AlignLeft | Qt.AlignVCenter, name)
            mentions = app.mentions.get(name, 0)
            if mentions and not here:
                badge = QRectF(box.right() - 28, box.center().y() - 8, 20, 16)
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(C["red"]))
                p.drawRoundedRect(badge, 8, 8)
                p.setPen(QColor("white"))
                p.setFont(_font(11, True))
                p.drawText(badge, Qt.AlignCenter, str(mentions))
        p.restore()


class PersonRows(QStyledItemDelegate):
    """The member list (compact) and the Friends page (with a status line and a message button)."""

    def __init__(self, app, friends=False):
        super().__init__(app)
        self.app = app
        self.friends = friends

    def sizeHint(self, option, index):
        row = index.data(Qt.UserRole)
        if row[0] == "header":
            return QSize(option.rect.width(), 40 if self.friends else 36)
        return QSize(option.rect.width(), 62 if self.friends else 44)

    def paint(self, p, option, index):
        app = self.app
        row = index.data(Qt.UserRole)
        r = QRectF(option.rect)
        bg = C["chat"] if self.friends else C["side"]
        p.save()
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(r, QColor(bg))
        if row[0] == "header":
            p.setPen(QColor(C["header"]))
            p.setFont(_font(11, True))
            p.drawText(QRectF(r.left() + (20 if self.friends else 16), r.top() + 14, r.width() - 30, r.height() - 14),
                       Qt.AlignLeft | Qt.AlignVCenter, row[1])
            p.restore()
            return
        bid = row[1]
        if bid == "":
            name, pic, presence = app.my_name(), my_avatar(32), ONLINE
            game = (app.network.activity["name"], app.network.activity["key"]) \
                if app.network.activity and app.network.show_activity else None
        else:
            b = app.network.buddies.get(bid)
            if b is None:
                p.restore()
                return
            name, pic, presence, game = b.name, avatar(b, 32), b.presence, app.network.friend_activity(b)
        hover = bool(option.state & QStyle.State_MouseOver)
        if self.friends:
            box = QRectF(r.left() + 20, r.top(), r.width() - 40, r.height())
            if hover:
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(C["hover"]))
                p.drawRoundedRect(QRectF(box.left() - 10, box.top() + 1, box.width() + 20, box.height() - 2), 8, 8)
            p.fillRect(QRectF(box.left(), box.top(), box.width(), 1), QColor("#42454A"))
            ring = C["hover"] if hover else bg
            p.drawPixmap(int(box.left()), int(box.top() + 15), pic)
            draw_status(p, box.left() + 28, box.top() + 43, 5, presence, ring)
            p.setPen(QColor(C["bright"]))
            p.setFont(_font(15, True))
            p.drawText(QRectF(box.left() + 44, box.top() + 11, box.width() - 110, 20), Qt.AlignLeft | Qt.AlignVCenter,
                       name)
            p.setPen(QColor(C["muted"]))
            p.setFont(_font(12))
            status = f"Playing {game[0]}" if game else STATUS_WORDS.get(presence, "Offline")
            p.drawText(QRectF(box.left() + 44, box.top() + 31, box.width() - 110, 18), Qt.AlignLeft | Qt.AlignVCenter,
                       status)
            button = QRectF(box.right() - 36, box.center().y() - 18, 36, 36)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(C["side"] if not hover else C["rail"]))
            p.drawEllipse(button)
            p.setPen(QPen(QColor(C["muted"]), 2))
            p.setBrush(Qt.NoBrush)
            bubble = QRectF(button.left() + 10, button.top() + 11, 16, 12)
            p.drawRoundedRect(bubble, 4, 4)
            p.drawLine(QPointF(bubble.left() + 4, bubble.bottom()), QPointF(bubble.left() + 2, bubble.bottom() + 4))
        else:
            box = QRectF(r.left() + 8, r.top() + 1, r.width() - 16, r.height() - 2)
            if hover:
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(C["hover"]))
                p.drawRoundedRect(box, 4, 4)
            faded = presence == OFFLINE
            if faded:
                p.setOpacity(0.35)
            p.drawPixmap(int(box.left() + 8), int(box.top() + 5), pic)
            if not faded:
                draw_status(p, box.left() + 36, box.top() + 33, 4.5, presence, C["hover"] if hover else bg)
            colour = C["bright"] if bid == "" else role_colour(bid)
            p.setPen(QColor(colour))
            p.setFont(_font(14, True))
            top = box.top() + (4 if game else 0)
            name_r = QRectF(box.left() + 50, top, box.width() - 56, 22 if game else box.height())
            p.drawText(name_r, Qt.AlignLeft | Qt.AlignVCenter,
                       p.fontMetrics().elidedText(name, Qt.ElideRight, int(name_r.width())))
            if game:
                p.setPen(QColor(C["muted"]))
                f = _font(11)
                p.setFont(f)
                sub = QRectF(box.left() + 50, top + 18, box.width() - 56, 16)
                p.drawText(sub, Qt.AlignLeft | Qt.AlignVCenter,
                           p.fontMetrics().elidedText(f"Playing {game[0]}", Qt.ElideRight, int(sub.width())))
        p.restore()


class ActiveNow(QWidget):
    """The Friends page's right column: who's playing what."""

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setFixedWidth(340)

    def paintEvent(self, event):
        app = self.app
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(C["chat"]))
        p.fillRect(QRectF(0, 0, 1, self.height()), QColor("#42454A"))
        p.setPen(QColor(C["bright"]))
        p.setFont(_font(20, True))
        p.drawText(QRectF(16, 16, self.width() - 32, 30), Qt.AlignLeft | Qt.AlignVCenter, "Active Now")
        playing = [(b, g) for b in app.network.buddies.values() if (g := app.network.friend_activity(b))]
        y = 60
        if not playing:
            p.setFont(_font(16, True))
            p.drawText(QRectF(16, y + 20, self.width() - 32, 24), Qt.AlignCenter, "It's quiet for now...")
            p.setPen(QColor(C["muted"]))
            p.setFont(_font(13))
            p.drawText(QRectF(24, y + 48, self.width() - 48, 60), Qt.AlignHCenter | Qt.AlignTop | Qt.TextWordWrap,
                       "When a friend starts an activity - like playing a game - we'll show it here!")
            return
        for b, (game, key) in playing:
            card = QRectF(16, y, self.width() - 32, 84)
            if card.bottom() > self.height() - 8:
                break
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(C["side"]))
            p.drawRoundedRect(card, 8, 8)
            p.drawPixmap(int(card.left() + 14), int(card.top() + 12), avatar(b, 32))
            draw_status(p, card.left() + 42, card.top() + 40, 5, b.presence, C["side"])
            p.setPen(QColor(C["bright"]))
            p.setFont(_font(14, True))
            p.drawText(QRectF(card.left() + 58, card.top() + 10, card.width() - 70, 18),
                       Qt.AlignLeft | Qt.AlignVCenter, b.name)
            p.setPen(QColor(C["muted"]))
            p.setFont(_font(12))
            p.drawText(QRectF(card.left() + 58, card.top() + 28, card.width() - 70, 16),
                       Qt.AlignLeft | Qt.AlignVCenter, p.fontMetrics().elidedText(game, Qt.ElideRight, 210))
            icon = game_icon(key, 24)
            if not icon.isNull():
                p.drawPixmap(int(card.left() + 14), int(card.top() + 52), icon)
            p.setPen(QColor(C["text"]))
            p.drawText(QRectF(card.left() + 46, card.top() + 52, card.width() - 60, 24), Qt.AlignLeft | Qt.AlignVCenter,
                       f"Playing {game}")
            y += 96


class UserPanel(QWidget):
    """You, at the bottom of the sidebar: your picture, name and tag (or what you're playing), mute, deafen, settings."""

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setFixedHeight(52)
        self.setMouseTracking(True)
        self.hover = None

    def _buttons(self):
        w = self.width()
        return {"mic": QRectF(w - 104, 10, 32, 32), "deafen": QRectF(w - 70, 10, 32, 32),
                "gear": QRectF(w - 38, 10, 32, 32)}

    def mouseMoveEvent(self, event):
        hit = next((k for k, r in self._buttons().items() if r.contains(event.position())), None)
        if hit != self.hover:
            self.hover = hit
            self.setToolTip({"mic": "Mute", "deafen": "Deafen (no sounds)", "gear": "User Settings"}.get(hit, ""))
            self.update()

    def leaveEvent(self, event):
        self.hover = None
        self.update()

    def mousePressEvent(self, event):
        hit = next((k for k, r in self._buttons().items() if r.contains(event.position())), None)
        if hit == "mic":
            self.app.toggle_setting("mic_muted")
        elif hit == "deafen":
            self.app.toggle_setting("deafened")
        elif hit == "gear":
            self.app.settings_menu(self.mapToGlobal(self._buttons()["gear"].topLeft().toPoint()))
        self.update()

    def paintEvent(self, event):
        app = self.app
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(C["panel"]))
        p.drawPixmap(8, 10, my_avatar(32))
        draw_status(p, 36, 38, 4.5, ONLINE, C["panel"])
        p.setPen(QColor(C["bright"]))
        p.setFont(_font(14, True))
        text_w = self.width() - 160
        p.drawText(QRectF(48, 9, text_w, 18), Qt.AlignLeft | Qt.AlignVCenter,
                   p.fontMetrics().elidedText(app.my_name(), Qt.ElideRight, text_w))
        act = app.network.activity if app.network.show_activity else None
        p.setPen(QColor(C["muted"]))
        p.setFont(_font(12))
        p.drawText(QRectF(48, 27, text_w, 16), Qt.AlignLeft | Qt.AlignVCenter,
                   p.fontMetrics().elidedText(f"Playing {act['name']}" if act else f"#{app.tag()}",
                                              Qt.ElideRight, text_w))
        for kind, r in self._buttons().items():
            if self.hover == kind:
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(C["hover"]))
                p.drawRoundedRect(r, 4, 4)
            p.setPen(QPen(QColor(C["text"] if self.hover == kind else "#B9BBBE"), 2))
            p.setBrush(Qt.NoBrush)
            cx, cy = r.center().x(), r.center().y()
            if kind == "mic":
                p.drawRoundedRect(QRectF(cx - 3.5, cy - 9, 7, 12), 3.5, 3.5)
                p.drawArc(QRectF(cx - 7, cy - 6, 14, 12), 180 * 16, 180 * 16)
                p.drawLine(QPointF(cx, cy + 6), QPointF(cx, cy + 9))
            elif kind == "deafen":
                p.drawArc(QRectF(cx - 8, cy - 8, 16, 16), 0, 180 * 16)
                p.drawLine(QPointF(cx - 8, cy), QPointF(cx - 8, cy + 5))
                p.drawLine(QPointF(cx + 8, cy), QPointF(cx + 8, cy + 5))
                p.setBrush(QColor(C["text"] if self.hover == kind else "#B9BBBE"))
                p.drawRoundedRect(QRectF(cx - 9, cy + 1, 4, 7), 1.5, 1.5)
                p.drawRoundedRect(QRectF(cx + 5, cy + 1, 4, 7), 1.5, 1.5)
            else:
                f = QFont("Segoe UI Symbol")
                f.setPixelSize(19)
                p.setFont(f)
                p.drawText(r, Qt.AlignCenter, "⚙")
            off = kind == "mic" and app.settings.get("mic_muted") or kind == "deafen" and app.settings.get("deafened")
            if off:
                p.setPen(QPen(QColor(C["red"]), 2.4))
                p.drawLine(QPointF(cx - 9, cy - 9), QPointF(cx + 9, cy + 9))


# ---- the messages ------------------------------------------------------------------------------------------------------
class MessageView(QScrollArea):
    """Discord's messages: avatar, coloured name and time, then that person's lines grouped under them."""

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.inner = QWidget()
        self.inner.setObjectName("messages")
        self.col = QVBoxLayout(self.inner)
        self.col.setContentsMargins(0, 10, 0, 14)
        self.col.setSpacing(0)
        self.col.addStretch(1)
        self.setWidget(self.inner)
        self.movies = []
        self.last = None            # (author key, time, the layout new lines go in)
        self.last_day = None
        self.verticalScrollBar().rangeChanged.connect(lambda _lo, hi: self.verticalScrollBar().setValue(hi))

    def clear(self):
        for movie in self.movies:
            movie.stop()
        self.movies = []
        while self.col.count() > 1:
            item = self.col.takeAt(1)
            w = item.widget()
            if w is not None:
                w.hide()
                w.deleteLater()
        self.last = None
        self.last_day = None

    def show_entries(self, entries, intro):
        self.clear()
        self.col.addWidget(intro)
        for e in entries:
            self.add(e)

    def _rich(self, text):
        out = html.escape(text)
        for name in sorted(self.app.known_names(), key=len, reverse=True):
            tag = "@" + html.escape(name)
            out = out.replace(tag, f"<span style='background:{C['mention']}; color:#DEE0FC;'>{tag}</span>")
        return out.replace("\n", "<br>")

    def _divider(self, day):
        holder = QWidget()
        row = QHBoxLayout(holder)
        row.setContentsMargins(16, 14, 16, 6)
        for side in (0, 1):
            line = QFrame()
            line.setFixedHeight(1)
            line.setStyleSheet("QFrame { background: #42454A; }")
            row.addWidget(line, 1)
            if side == 0:
                label = QLabel(f"{day:%B} {day.day}, {day.year}")
                label.setStyleSheet(f"QLabel {{ color: {C['dim']}; font: bold 9pt 'Segoe UI'; padding: 0 6px; }}")
                row.addWidget(label)
        self.col.addWidget(holder)

    def add(self, e):
        app = self.app
        dt = _when(e)
        if dt.date() != self.last_day:
            self.last_day = dt.date()
            self._divider(dt)
            self.last = None
        kind = e["kind"]
        if kind == "system":
            note = QLabel(f"<span style='color:{C['green']}'>→</span>&nbsp;&nbsp;{html.escape(e['text'])}"
                          f"&nbsp;&nbsp;<span style='color:{C['dim']}; font-size:8pt'>{_stamp(dt)}</span>")
            note.setWordWrap(True)
            note.setStyleSheet(f"QLabel {{ color: {C['muted']}; font: 10pt 'Segoe UI'; padding: 6px 16px 6px 34px; }}")
            self.col.addWidget(note)
            self.last = None
            return
        if kind == "invite":
            self.col.addWidget(self._invite(e))
            self.last = None
            return
        key, name, pic, colour = app.author(e)
        if self.last is not None and self.last[0] == key and dt - self.last[1] < timedelta(minutes=7):
            lines = self.last[2]
            self.last = (key, dt, lines)
        else:
            group = QWidget()
            row = QHBoxLayout(group)
            row.setContentsMargins(16, 14, 16, 0)
            row.setSpacing(16)
            face = QLabel()
            face.setPixmap(pic)
            face.setFixedSize(40, 40)
            row.addWidget(face, 0, Qt.AlignTop)
            lines = QVBoxLayout()
            lines.setSpacing(2)
            head = QLabel(f"<span style='color:{colour}; font-weight:600; font-size:11pt'>{html.escape(name)}</span>"
                          f"&nbsp;&nbsp;<span style='color:{C['dim']}; font-size:8pt'>{_stamp(dt)}</span>")
            lines.addWidget(head)
            row.addLayout(lines, 1)
            self.col.addWidget(group)
            self.last = (key, dt, lines)
        if e.get("sticker"):
            from pathlib import Path
            if Path(e["sticker"]).exists():
                pic_label = QLabel()
                movie = QMovie(e["sticker"])
                size = QImageReader(e["sticker"]).size()
                if size.isValid():
                    movie.setScaledSize(size.scaled(160, 160, Qt.KeepAspectRatio))
                pic_label.setMovie(movie)
                movie.start()
                self.movies.append(movie)
                pic_label.setToolTip(f"{e.get('text', '')}  {e.get('meaning', '')}".strip())
                lines.addWidget(pic_label, 0, Qt.AlignLeft)
                return
        words = QLabel(self._rich(e["text"]))
        words.setTextFormat(Qt.RichText)
        words.setWordWrap(True)
        words.setTextInteractionFlags(Qt.TextSelectableByMouse)
        mention = e.get("mention")
        words.setStyleSheet(f"QLabel {{ color: {C['text']}; font: 11pt 'Segoe UI', '{EMOJI_FONT}';"
                            + (" background: rgba(250, 168, 26, 25); border-left: 2px solid #FAA81A;"
                               " padding-left: 4px;" if mention else "") + " }")
        lines.addWidget(words)

    def _invite(self, e):
        """A friend's offer to be your player 2: Accept seats them at your Zone table."""
        app = self.app
        holder = QWidget()
        row = QHBoxLayout(holder)
        row.setContentsMargins(72, 6, 16, 6)
        card = QFrame()
        card.setObjectName("invite")
        card.setFixedWidth(420)
        card.setStyleSheet(f"QFrame#invite {{ background: {C['card']}; border: 1px solid #202225; border-radius: 6px; }}")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(6)
        title = QLabel("YOU'VE BEEN INVITED TO PLAY")
        title.setStyleSheet(f"QLabel {{ color: {C['muted']}; font: bold 8pt 'Segoe UI'; background: transparent; }}")
        lay.addWidget(title)
        mid = QHBoxLayout()
        icon = QLabel()
        icon.setPixmap(game_icon(e.get("key", ""), 40))
        icon.setStyleSheet("QLabel { background: transparent; }")
        mid.addWidget(icon)
        words = QLabel(f"<b style='color:white; font-size:11pt'>{html.escape(e.get('game', ''))}</b><br>"
                       f"<span style='color:{C['muted']}'>{html.escape(e['text'])}</span>")
        words.setWordWrap(True)
        words.setStyleSheet("QLabel { background: transparent; font: 10pt 'Segoe UI'; }")
        mid.addWidget(words, 1)
        button = QPushButton()
        button.setFixedSize(96, 34)
        expired = (datetime.now() - _when(e)).total_seconds() > INVITE_SECONDS
        if e.get("accepted"):
            button.setText("Accepted")
            button.setEnabled(False)
        elif expired:
            button.setText("Expired")
            button.setEnabled(False)
        else:
            button.setText("Accept")
            button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(lambda: app.accept_invite(e))
        button.setStyleSheet(f"QPushButton {{ background: {C['green']}; color: white; border: none; border-radius: 3px;"
                             " font: bold 10pt 'Segoe UI'; } QPushButton:hover { background: #2D7D46; }"
                             f" QPushButton:disabled {{ background: {C['input']}; color: {C['muted']}; }}")
        mid.addWidget(button)
        lay.addLayout(mid)
        row.addWidget(card)
        row.addStretch(1)
        return holder


# ---- the program -----------------------------------------------------------------------------------------------------
class Discord(QWidget):
    def __init__(self, desktop, network):
        super().__init__()
        self.desktop = desktop
        self.network = network
        self.frame = None
        self.settings = _settings()
        network.show_activity = self.settings.get("activity", True)
        self.server = "home"
        self.where = ("friends",)
        self.friends_tab = "online"
        self.unread = {}                    # buddy id -> new direct messages
        self.channel_unread = {}            # channel -> new messages
        self.mentions = {}                  # channel -> messages that @mention you
        self.tray = None
        self.setObjectName("discord")
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        self.rail = Rail(self)
        row.addWidget(self.rail)
        row.addWidget(self._sidebar())
        row.addWidget(self._main(), 1)
        self._style()
        network.message_added.connect(self._message)
        network.channel_added.connect(self._channel_message)
        network.presence_changed.connect(lambda _bid: self._refresh_people())
        network.typing_changed.connect(lambda _bid, _on: self._update_typing())
        network.channel_typing.connect(lambda _name: self._update_typing())
        network.activity_changed.connect(self._refresh_people)
        self.watch = QTimer(self, interval=4000, timeout=self._watch_games)
        self.watch.start()
        if not network.signed_in:
            network.sign_in()
        self._watch_games()
        self._tray_on()
        last = self.settings.get("last", ["friends"])
        if last and last[0] == "channel" and last[1] in network.channels:
            self.show_server(last[1])
        elif last and last[0] == "dm" and last[1] in network.buddies:
            self.open_target(("dm", last[1]))
        else:
            self.show_home()

    # ---- building ------------------------------------------------------------------------------------------
    def _sidebar(self):
        side = QWidget()
        side.setObjectName("side")
        side.setFixedWidth(240)
        col = QVBoxLayout(side)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(0)
        self.side_top = QStackedWidget()
        self.side_top.setFixedHeight(48)
        find_holder = QWidget()
        fh = QHBoxLayout(find_holder)
        fh.setContentsMargins(10, 10, 10, 10)
        self.find = QLineEdit()
        self.find.setObjectName("find")
        self.find.setPlaceholderText("Find or start a conversation")
        self.find.textChanged.connect(self._refresh_sidebar)
        fh.addWidget(self.find)
        self.side_top.addWidget(find_holder)
        self.server_name = QPushButton(f"{SERVER}")
        self.server_name.setObjectName("servername")
        self.server_name.clicked.connect(self._server_menu)
        self.side_top.addWidget(self.server_name)
        col.addWidget(self.side_top)
        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet(f"QFrame {{ background: {C['line']}; }}")
        col.addWidget(line)
        self.side_list = QListWidget()
        self.side_list.setObjectName("sidelist")
        self.side_list.setItemDelegate(SideRows(self))
        self.side_list.setMouseTracking(True)
        self.side_list.setFrameShape(QFrame.NoFrame)
        self.side_list.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.side_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.side_list.itemClicked.connect(lambda item: self._side_clicked(item.data(Qt.UserRole)))
        col.addWidget(self.side_list, 1)
        self.me = UserPanel(self)
        col.addWidget(self.me)
        return side

    def _main(self):
        main = QWidget()
        col = QVBoxLayout(main)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(0)
        self.header = QWidget()
        self.header.setObjectName("header")
        self.header.setFixedHeight(48)
        hl = QHBoxLayout(self.header)
        hl.setContentsMargins(16, 0, 12, 0)
        hl.setSpacing(8)
        self.head_icon = QLabel()
        hl.addWidget(self.head_icon)
        self.head_title = QLabel()
        self.head_title.setObjectName("headtitle")
        hl.addWidget(self.head_title)
        self.head_bar = QFrame()
        self.head_bar.setFixedSize(1, 24)
        self.head_bar.setStyleSheet("QFrame { background: #4F545C; }")
        hl.addWidget(self.head_bar)
        self.head_topic = QLabel()
        self.head_topic.setObjectName("topic")
        hl.addWidget(self.head_topic, 1)
        self.tabs = QWidget()
        tl = QHBoxLayout(self.tabs)
        tl.setContentsMargins(0, 0, 0, 0)
        tl.setSpacing(6)
        self.tab_buttons = {}
        for key, label in (("online", "Online"), ("all", "All")):
            b = QPushButton(label)
            b.setObjectName("tab")
            b.setCheckable(True)
            b.clicked.connect(lambda _c=False, k=key: self._friends_tab(k))
            tl.addWidget(b)
            self.tab_buttons[key] = b
        add = QPushButton("Add Friend")
        add.setObjectName("addfriend")
        add.clicked.connect(self._add_friend)
        tl.addWidget(add)
        hl.addWidget(self.tabs)
        self.members_btn = QToolButton()
        self.members_btn.setIcon(QIcon(emoji_picture("👥", 22)))
        self.members_btn.setToolTip("Member List")
        self.members_btn.setCheckable(True)
        self.members_btn.setChecked(self.settings.get("members", True))
        self.members_btn.clicked.connect(self._toggle_members)
        hl.addWidget(self.members_btn)
        col.addWidget(self.header)
        self.pages = QStackedWidget()
        col.addWidget(self.pages, 1)
        # the Friends page
        friends = QWidget()
        fr = QHBoxLayout(friends)
        fr.setContentsMargins(0, 0, 0, 0)
        fr.setSpacing(0)
        self.friend_list = QListWidget()
        self.friend_list.setObjectName("friendlist")
        self.friend_list.setItemDelegate(PersonRows(self, friends=True))
        self.friend_list.setMouseTracking(True)
        self.friend_list.setFrameShape(QFrame.NoFrame)
        self.friend_list.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.friend_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.friend_list.itemClicked.connect(self._friend_clicked)
        fr.addWidget(self.friend_list, 1)
        self.active_now = ActiveNow(self)
        fr.addWidget(self.active_now)
        self.pages.addWidget(friends)
        # a conversation: messages, the composer, and (in a channel) the member list
        chat = QWidget()
        cr = QHBoxLayout(chat)
        cr.setContentsMargins(0, 0, 0, 0)
        cr.setSpacing(0)
        self.chat_col = QWidget()
        cc = QVBoxLayout(self.chat_col)
        cc.setContentsMargins(0, 0, 0, 0)
        cc.setSpacing(0)
        self.view = MessageView(self)
        cc.addWidget(self.view, 1)
        composer_holder = QWidget()
        ch = QVBoxLayout(composer_holder)
        ch.setContentsMargins(16, 0, 16, 0)
        ch.setSpacing(0)
        self.composer = QFrame()
        self.composer.setObjectName("composer")
        self.composer.setFixedHeight(44)
        cl = QHBoxLayout(self.composer)
        cl.setContentsMargins(10, 0, 8, 0)
        cl.setSpacing(4)
        plus = QToolButton()
        plus.setObjectName("plus")
        plus.setText("+")
        plus.setToolTip("Stickers")
        plus.clicked.connect(lambda: self.toggle_picker(1))
        cl.addWidget(plus)
        self.entry = QLineEdit()
        self.entry.setObjectName("entry")
        self.entry.returnPressed.connect(self.send)
        cl.addWidget(self.entry, 1)
        sticker = QToolButton()
        sticker.setIcon(QIcon(sticker_glyph(24, "#B9BBBE")))
        sticker.setIconSize(QSize(24, 24))
        sticker.setToolTip("Stickers")
        sticker.clicked.connect(lambda: self.toggle_picker(1))
        cl.addWidget(sticker)
        smile = QToolButton()
        smile.setIcon(QIcon(emoji_picture("🙂", 24)))
        smile.setIconSize(QSize(24, 24))
        smile.setToolTip("Emoji")
        smile.clicked.connect(lambda: self.toggle_picker(0))
        cl.addWidget(smile)
        ch.addWidget(self.composer)
        self.typing = QLabel()
        self.typing.setObjectName("typing")
        self.typing.setFixedHeight(24)
        ch.addWidget(self.typing)
        cc.addWidget(composer_holder)
        cr.addWidget(self.chat_col, 1)
        self.member_list = QListWidget()
        self.member_list.setObjectName("memberlist")
        self.member_list.setFixedWidth(240)
        self.member_list.setItemDelegate(PersonRows(self))
        self.member_list.setMouseTracking(True)
        self.member_list.setFrameShape(QFrame.NoFrame)
        self.member_list.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.member_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.member_list.itemClicked.connect(self._member_clicked)
        cr.addWidget(self.member_list)
        self.pages.addWidget(chat)
        # the emoji / sticker picker floats over the messages, above the composer
        self.picker = QFrame(self.chat_col)
        self.picker.setObjectName("picker")
        self.picker.resize(380, 380)
        pl = QVBoxLayout(self.picker)
        pl.setContentsMargins(0, 0, 0, 0)
        self.emoji_panel = EmojiStickers(self)
        pl.addWidget(self.emoji_panel)
        self.picker.hide()
        return main

    def _style(self):
        self.setStyleSheet(
            f"QWidget {{ font-family: 'Segoe UI', '{EMOJI_FONT}'; color: {C['text']}; }}"
            f"QWidget#discord, QWidget#header, QScrollArea, QWidget#messages {{ background: {C['chat']}; }}"
            f"QWidget#side, QListWidget#sidelist, QListWidget#memberlist {{ background: {C['side']}; border: none; }}"
            f"QListWidget {{ outline: 0; }} QListWidget#friendlist {{ background: {C['chat']}; border: none; }}"
            f"QListWidget::item:selected, QListWidget::item:hover {{ background: transparent; }}"
            f"QLineEdit#find {{ background: {C['rail']}; border: none; border-radius: 4px; padding: 5px 7px;"
            f" color: {C['text']}; font-size: 9pt; }}"
            f"QPushButton#servername {{ background: {C['side']}; border: none; color: {C['bright']}; text-align: left;"
            f" padding: 0 16px; font: bold 11pt 'Segoe UI'; }} QPushButton#servername:hover {{ background: {C['hover']}; }}"
            f"QLabel#headtitle {{ color: {C['bright']}; font: bold 11pt 'Segoe UI'; }}"
            f"QLabel#topic {{ color: {C['header']}; font: 9pt 'Segoe UI'; }}"
            f"QPushButton#tab {{ background: transparent; border: none; border-radius: 4px; padding: 3px 10px;"
            f" color: {C['header']}; font: 10pt 'Segoe UI'; }} QPushButton#tab:hover {{ background: {C['hover']};"
            f" color: {C['text']}; }} QPushButton#tab:checked {{ background: {C['pick']}; color: {C['bright']}; }}"
            f"QPushButton#addfriend {{ background: {C['green']}; border: none; border-radius: 4px; padding: 3px 10px;"
            f" color: white; font: 10pt 'Segoe UI'; }}"
            f"QToolButton {{ background: transparent; border: none; padding: 2px; color: #B9BBBE; }}"
            f"QToolButton:checked {{ background: transparent; }}"
            f"QToolButton#plus {{ background: #B9BBBE; color: {C['input']}; border-radius: 11px; font: bold 14pt;"
            f" min-width: 22px; max-width: 22px; min-height: 22px; max-height: 22px; padding: 0; }}"
            f"QFrame#composer {{ background: {C['input']}; border-radius: 8px; }}"
            f"QLineEdit#entry {{ background: transparent; border: none; color: {C['text']}; font-size: 11pt;"
            f" padding: 4px 6px; }}"
            f"QLabel#typing {{ color: {C['text']}; font: 9pt 'Segoe UI'; padding-left: 4px; }}"
            f"QFrame#picker {{ background: {C['side']}; border: 1px solid {C['rail']}; border-radius: 8px; }}"
            f"QFrame#picker QListWidget {{ background: {C['side']}; border: none; }}"
            f"QFrame#picker QLabel {{ color: {C['muted']}; font: bold 8pt 'Segoe UI'; padding: 4px; }}"
            f"QPushButton#panel {{ background: transparent; color: {C['muted']}; border: none; padding: 8px;"
            f" font: bold 9pt; }} QPushButton#panel:checked {{ color: {C['bright']};"
            f" border-bottom: 2px solid {C['blurple']}; }}"
            f"QScrollBar:vertical {{ background: {C['side']}; width: 8px; margin: 0; border: none; }}"
            f"QScrollBar::handle:vertical {{ background: {C['rail']}; border-radius: 4px; min-height: 30px; }}"
            f"QScrollBar:horizontal {{ background: {C['side']}; height: 8px; margin: 0; border: none; }}"
            f"QScrollBar::handle:horizontal {{ background: {C['rail']}; border-radius: 4px; min-width: 30px; }}"
            f"QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}"
            f"QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}")

    # ---- who's who -------------------------------------------------------------------------------------------
    def my_name(self):
        return self.network.my_handle()

    def tag(self):
        """Your four-digit Discord tag (made up once, then kept)."""
        if not self.settings.get("tag"):
            self.settings["tag"] = f"{random.randint(1, 9999):04d}"
            _save_settings(self.settings)
        return self.settings["tag"]

    def known_names(self):
        return [self.my_name()] + [b.name for b in self.network.buddies.values()]

    def author(self, e):
        """(key, name, picture, name colour) of whoever wrote a line in the conversation that's open."""
        if e["kind"] == "user":
            return "me", self.my_name(), my_avatar(40), C["bright"]
        if self.where[0] == "dm":
            b = self.network.buddies.get(self.where[1])
        else:
            b = self.network.buddies.get(e.get("who", ""))
        if b is None:
            return "?", e.get("name", "someone"), logo(40), C["bright"]
        colour = C["bright"] if self.where[0] == "dm" else role_colour(b.contact.id)
        return b.contact.id, b.name, avatar(b, 40), colour

    # ---- going places ----------------------------------------------------------------------------------------
    def show_home(self):
        self.server = "home"
        self.side_top.setCurrentIndex(0)
        target = self.where if self.where[0] in ("friends", "dm") else ("friends",)
        self.open_target(target)

    def show_server(self, channel=None):
        self.server = "den"
        self.side_top.setCurrentIndex(1)
        name = channel or (self.where[1] if self.where[0] == "channel" else self.settings.get("channel", "general"))
        self.open_target(("channel", name if name in self.network.channels else "general"))

    def _side_clicked(self, row):
        if row[0] == "friends":
            self.open_target(("friends",))
        elif row[0] in ("dm", "channel"):
            self.open_target((row[0], row[1]))

    def open_target(self, target):
        self.where = target
        self.picker.hide()
        kind = target[0]
        if kind == "channel":
            self.server = "den"
            self.side_top.setCurrentIndex(1)
            self.settings["channel"] = target[1]
        elif self.server != "home":
            self.server = "home"
            self.side_top.setCurrentIndex(0)
        self.settings["last"] = list(target)
        _save_settings(self.settings)
        self.tabs.setVisible(kind == "friends")
        self.members_btn.setVisible(kind == "channel")
        self.head_bar.setVisible(kind != "dm")
        if kind == "friends":
            self.head_icon.setPixmap(emoji_picture("👥", 22))
            self.head_title.setText("Friends")
            self.head_topic.setText("")
            self.pages.setCurrentIndex(0)
            self._friends_tab(self.friends_tab)
        elif kind == "dm":
            b = self.network.buddies[target[1]]
            self.unread.pop(b.contact.id, None)
            b.unread = False
            self.head_icon.setText("<span style='color:#72767D; font: 20pt \"Segoe UI\"'>@</span>")
            self.head_title.setText(b.name)
            self._update_dm_topic(b)
            self.entry.setPlaceholderText(f"Message @{b.name}")
            self.member_list.hide()
            self.pages.setCurrentIndex(1)
            self.view.show_entries(b.history[-150:], self._intro_dm(b))
        else:
            ch = self.network.channels[target[1]]
            self.channel_unread.pop(ch.name, None)
            self.mentions.pop(ch.name, None)
            self.head_icon.setText("<span style='color:#72767D; font: 20pt \"Segoe UI\"'>#</span>")
            self.head_title.setText(ch.name)
            self.head_topic.setText(ch.topic)
            self.entry.setPlaceholderText(f"Message #{ch.name}")
            self.member_list.setVisible(self.members_btn.isChecked())
            self.pages.setCurrentIndex(1)
            self.view.show_entries(ch.history[-150:], self._intro_channel(ch))
            self._refresh_members()
        self._update_typing()
        self._refresh_sidebar()
        self._update_tray()
        self.rail.update()
        if kind != "friends":
            self.entry.setFocus()

    def _update_dm_topic(self, b):
        game = self.network.friend_activity(b)
        status = STATUS_WORDS.get(b.presence, "Offline")
        colour = STATUS_COLOURS.get(b.presence, STATUS_COLOURS[OFFLINE])
        self.head_topic.setText(f"<span style='color:{colour}'>●</span> " + (f"Playing {html.escape(game[0])}" if game
                                                                             else status))

    def _intro_dm(self, b):
        w = QWidget()
        col = QVBoxLayout(w)
        col.setContentsMargins(16, 16, 16, 8)
        pic = QLabel()
        pic.setPixmap(avatar(b, 80))
        col.addWidget(pic)
        name = QLabel(b.name)
        name.setStyleSheet("QLabel { color: white; font: bold 20pt 'Segoe UI'; }")
        name.setWordWrap(True)
        col.addWidget(name)
        blurb = QLabel(f"This is the beginning of your direct message history with <b>@{html.escape(b.name)}</b>.")
        blurb.setStyleSheet(f"QLabel {{ color: {C['header']}; font: 10pt 'Segoe UI'; }}")
        blurb.setWordWrap(True)
        col.addWidget(blurb)
        return w

    def _intro_channel(self, ch):
        w = QWidget()
        col = QVBoxLayout(w)
        col.setContentsMargins(16, 16, 16, 8)
        badge = QLabel("#")
        badge.setFixedSize(68, 68)
        badge.setAlignment(Qt.AlignCenter)
        badge.setStyleSheet(f"QLabel {{ background: {C['input']}; color: white; border-radius: 34px;"
                            " font: 30pt 'Segoe UI'; }")
        col.addWidget(badge)
        title = QLabel(f"Welcome to #{ch.name}!")
        title.setStyleSheet("QLabel { color: white; font: bold 20pt 'Segoe UI'; }")
        title.setWordWrap(True)
        col.addWidget(title)
        blurb = QLabel(f"This is the start of the #{ch.name} channel. {ch.topic}")
        blurb.setStyleSheet(f"QLabel {{ color: {C['header']}; font: 10pt 'Segoe UI'; }}")
        blurb.setWordWrap(True)
        col.addWidget(blurb)
        return w

    # ---- lists -----------------------------------------------------------------------------------------------
    def _sorted_buddies(self):
        def order(b):
            here = {ONLINE: 0, BUSY: 0, AWAY: 1}.get(b.presence, 2)
            last = next((e for e in reversed(b.history) if e["kind"] in ("user", "contact")), None)
            return (here, 0, -_when(last).timestamp(), "") if last is not None else (here, 1, 0, b.name.lower())
        return sorted(self.network.buddies.values(), key=order)

    @staticmethod
    def _row(lst, data, pick=False):
        item = QListWidgetItem()
        item.setData(Qt.UserRole, data)
        if data[0] in ("header", "category"):
            item.setFlags(Qt.NoItemFlags)
        lst.addItem(item)
        if pick:
            lst.setCurrentItem(item)

    def _refresh_sidebar(self, *_):
        lst = self.side_list
        bar = lst.verticalScrollBar().value()
        lst.blockSignals(True)
        lst.clear()
        if self.server == "home":
            self._row(lst, ("friends",), self.where == ("friends",))
            self._row(lst, ("header", "Direct Messages"))
            wanted = self.find.text().strip().lower()
            for b in self._sorted_buddies():
                if not wanted or wanted in b.name.lower():
                    self._row(lst, ("dm", b.contact.id), self.where == ("dm", b.contact.id))
        else:
            self._row(lst, ("category", "Text Channels"))
            for name in self.network.channels:
                self._row(lst, ("channel", name), self.where == ("channel", name))
        lst.blockSignals(False)
        lst.verticalScrollBar().setValue(bar)

    def _refresh_members(self):
        lst = self.member_list
        lst.clear()
        people = self._sorted_buddies()
        on = [b for b in people if b.presence != OFFLINE]
        off = [b for b in people if b.presence == OFFLINE]
        self._row(lst, ("header", f"ONLINE — {len(on) + 1}"))
        self._row(lst, ("member", ""))
        for b in on:
            self._row(lst, ("member", b.contact.id))
        if off:
            self._row(lst, ("header", f"OFFLINE — {len(off)}"))
            for b in off:
                self._row(lst, ("member", b.contact.id))

    def _friends_tab(self, key):
        self.friends_tab = key
        for k, b in self.tab_buttons.items():
            b.setChecked(k == key)
        lst = self.friend_list
        lst.clear()
        people = self._sorted_buddies()
        if key == "online":
            people = [b for b in people if b.presence != OFFLINE]
            self._row(lst, ("header", f"ONLINE — {len(people)}"))
        else:
            self._row(lst, ("header", f"ALL FRIENDS — {len(people)}"))
        for b in people:
            self._row(lst, ("friend", b.contact.id))
        self.active_now.update()

    def _refresh_people(self, *_):
        self._refresh_sidebar()
        if self.where[0] == "channel":
            self._refresh_members()
        elif self.where[0] == "friends":
            self._friends_tab(self.friends_tab)
        elif self.where[0] == "dm" and self.where[1] in self.network.buddies:
            self._update_dm_topic(self.network.buddies[self.where[1]])
        self.me.update()

    def _friend_clicked(self, item):
        row = item.data(Qt.UserRole)
        if row[0] == "friend":
            self.open_target(("dm", row[1]))

    def _member_clicked(self, item):
        row = item.data(Qt.UserRole)
        if row[0] == "member" and row[1]:
            menu = QMenu(self)
            menu.addAction("Message", lambda: self.open_target(("dm", row[1])))
            b = self.network.buddies.get(row[1])
            if b is not None:
                menu.addAction(f"Mention @{b.name}", lambda: self.insert_emoji(f"@{b.name} "))
            menu.exec(self.cursor().pos())

    def channel_unread_total(self):
        return sum(self.channel_unread.values())

    # ---- talking -----------------------------------------------------------------------------------------------
    def send(self):
        text = self.entry.text().strip()
        if not text:
            return
        self.entry.clear()
        if self.where[0] == "dm":
            self.network.send(self.network.buddies[self.where[1]], text)
        elif self.where[0] == "channel":
            self.network.post(self.where[1], text)

    def send_sticker(self, path):
        if not path:
            return
        self.picker.hide()
        if self.where[0] == "dm":
            self.network.send_sticker(self.network.buddies[self.where[1]], path)
        elif self.where[0] == "channel":
            self.network.post_sticker(self.where[1], path)

    def insert_emoji(self, emoji):
        self.entry.insert(emoji)
        self.entry.setFocus()

    def toggle_picker(self, tab):
        if self.picker.isVisible() and self.emoji_panel.pages.currentIndex() == tab:
            self.picker.hide()
            return
        self.emoji_panel.show_tab(tab)
        self._place_picker()
        self.picker.show()
        self.picker.raise_()

    def _place_picker(self):
        col = self.chat_col
        self.picker.move(max(0, col.width() - self.picker.width() - 16), max(0, col.height() - self.picker.height() - 76))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.picker.isVisible():
            self._place_picker()

    def _looking_at(self, target):
        return self.where == target and self.frame is not None and self.desktop.active is self.frame

    def _notify(self, muted_key=None):
        if self.settings.get("deafened") or muted_key in self.settings.get("muted", []):
            return
        if sound.play_file(NOTIFY_SOUND) is None and not sound.is_muted():
            sound.play("notify")                        # (the sound file is missing: Windows' own)
        if self.frame is not None:
            self.frame.flash()

    def _message(self, bid, e):
        if self.where == ("dm", bid):
            self.view.add(e)
        if e["kind"] in ("contact", "invite") and not self._looking_at(("dm", bid)):
            if e["kind"] == "contact" or not self.unread.get(bid):
                self.unread[bid] = self.unread.get(bid, 0) + 1
            self._notify(bid)
        self._update_tray()
        self._refresh_sidebar()
        self.rail.update()

    def _channel_message(self, name, e):
        if self.where == ("channel", name):
            self.view.add(e)
        if e["kind"] == "contact" and not self._looking_at(("channel", name)):
            if self.where != ("channel", name):
                self.channel_unread[name] = self.channel_unread.get(name, 0) + 1
                if e.get("mention"):
                    self.mentions[name] = self.mentions.get(name, 0) + 1
            if e.get("mention"):
                self._notify()
        self._update_tray()
        self._refresh_sidebar()
        self.rail.update()

    def _update_typing(self):
        names = []
        if self.where[0] == "dm":
            b = self.network.buddies.get(self.where[1])
            if b is not None and b.busy:
                names = [b.name]
        elif self.where[0] == "channel":
            names = [self.network.buddies[bid].name for bid in self.network.typing_in.get(self.where[1], ())
                     if bid in self.network.buddies]
        if not names:
            self.typing.setText("")
        elif len(names) == 1:
            self.typing.setText(f"<b>•••</b>&nbsp; <b>{html.escape(names[0])}</b> is typing...")
        else:
            self.typing.setText(f"<b>•••</b>&nbsp; <b>{html.escape(names[0])}</b> and <b>{html.escape(names[1])}</b>"
                                " are typing...")

    # ---- playing -----------------------------------------------------------------------------------------------
    def _watch_games(self):
        """What you're playing: the newest game window that's open (Discord's game detection)."""
        playing = None
        for win in reversed(getattr(self.desktop, "windows", [])):
            if not isValid(win):
                continue
            hit = game_in(getattr(win, "title", "") or "")
            if hit is not None:
                playing = hit
                break
        self.network.set_activity(playing)
        self.me.update()

    def accept_invite(self, e):
        if self.where[0] != "dm":
            return
        b = self.network.buddies.get(self.where[1])
        if b is None or e.get("accepted"):
            return
        e["accepted"] = True
        try:
            b.path.write_text(json.dumps({"messages": b.history}, indent=1), encoding="utf-8")
        except OSError:
            pass
        from ...games import zone
        zone.invite(b.name)
        b.add("system", f"You accepted. {b.name} is joining you in {e.get('game', 'the game')} on the Zone.")
        self.view.show_entries(b.history[-150:], self._intro_dm(b))       # (the card now says Accepted)
        open_game = any(isValid(w) and game_in(getattr(w, "title", "") or "") == (e.get("game"), e.get("key"))
                        for w in getattr(self.desktop, "windows", []))
        if not open_game and e.get("key"):
            try:
                from .. import launch
                launch(self.desktop, e["key"])
            except Exception:
                pass

    # ---- menus and settings ------------------------------------------------------------------------------------
    def toggle_setting(self, key):
        self.settings[key] = not self.settings.get(key)
        _save_settings(self.settings)
        self.me.update()

    def settings_menu(self, where):
        menu = QMenu(self)
        act = menu.addAction("Display current activity as a status message", self._toggle_activity)
        act.setCheckable(True)
        act.setChecked(self.network.show_activity)
        deaf = menu.addAction("Deafen (no notification sounds)", lambda: self.toggle_setting("deafened"))
        deaf.setCheckable(True)
        deaf.setChecked(bool(self.settings.get("deafened")))
        if self.where[0] == "dm":
            muted = self.where[1] in self.settings.get("muted", [])
            menu.addAction("Unmute this conversation" if muted else "Mute this conversation", self._toggle_mute)
        menu.addSeparator()
        menu.addAction("Sticker Manager...", self._open_sticker_manager)
        menu.addAction("About Discord", self._about)
        menu.exec(where)

    def _toggle_activity(self):
        self.network.show_activity = not self.network.show_activity
        self.settings["activity"] = self.network.show_activity
        _save_settings(self.settings)
        self._refresh_people()

    def _toggle_mute(self):
        muted = self.settings.setdefault("muted", [])
        bid = self.where[1]
        if bid in muted:
            muted.remove(bid)
        else:
            muted.append(bid)
        _save_settings(self.settings)

    def _toggle_members(self):
        self.settings["members"] = self.members_btn.isChecked()
        _save_settings(self.settings)
        if self.where[0] == "channel":
            self.member_list.setVisible(self.members_btn.isChecked())

    def _server_menu(self):
        menu = QMenu(self)
        menu.addAction("Mark As Read", self._mark_read)
        menu.exec(self.server_name.mapToGlobal(self.server_name.rect().bottomLeft()))

    def _mark_read(self):
        self.channel_unread.clear()
        self.mentions.clear()
        self._refresh_sidebar()
        self._update_tray()
        self.rail.update()

    def _add_friend(self):
        from claudecore import host
        host.message(self.desktop, "Add Friend", "Your Discord friends are your buddies: add someone to your "
                     "ClaudeAIM Buddy List and they're your friend here too.", "info")

    def _open_sticker_manager(self):
        try:
            from stickers.manager import open_stickers
            open_stickers(self.desktop)
        except Exception:
            pass

    def _about(self):
        from claudecore import host
        host.message(self.desktop, "About Discord", "Discord\n\nChat with your friends, hang out in The Den, send "
                     "stickers (give them meanings in the Sticker Manager), and let your friends see what you're "
                     "playing - for the Internet games, one of them may offer to be your player 2.", "info")

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
        menu.addAction("Open Discord", self._bring_forward)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(lambda *_a: self._bring_forward())
        self._update_tray()
        self.tray.show()

    def _update_tray(self):
        if self.tray is None:
            return
        count = sum(self.unread.values()) + sum(self.mentions.values())
        self.tray.setIcon(QIcon(tray_picture(count)))
        self.tray.setToolTip(f"Discord - {count} unread message{'s' if count != 1 else ''}" if count else "Discord")

    def _bring_forward(self):
        if self.frame is not None and isValid(self.frame):
            self.desktop.open_window(self.frame)
            waiting = next(iter(self.unread), None)
            if waiting is not None and self.where != ("dm", waiting):
                self.open_target(("dm", waiting))
            elif not self.unread:
                waiting = next(iter(self.mentions), None)
                if waiting is not None:
                    self.open_target(("channel", waiting))

    def _tray_off(self):
        if self.tray is not None:
            self.tray.hide()
            self.tray.deleteLater()
            self.tray = None

    def closeEvent(self, event):
        self.watch.stop()
        self._tray_off()
        self.view.clear()
        self.network.set_activity(None)
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
        _holder["net"] = DiscordNetwork()
    body = Discord(desktop, _holder["net"])
    win = XPWindow(desktop, "Discord", body, discord_icon(), size=(1080, 680))
    body.frame = win
    _holder["win"] = win
    desktop.open_window(win)
    return win


def shutdown():
    win = _holder.get("win")
    if win is not None and isValid(win):
        win.content._tray_off()
        win.content.network.sign_out()
