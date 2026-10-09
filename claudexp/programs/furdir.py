"""The Fur Directory: a read-only card for every furry the system's AI plays - the ClaudeAIM buddies (who are also
on FurNet IRC and the MUCK), the IRC and MUCK regulars, and the background lurkers in the IRC channels.

The details come from hand-written records, one JSON file per resident in
Program Files/The Fur Directory/residents/ (see README.txt there). Nothing here is generated, and nothing can be
edited inside ClaudeXP. Facts the system already keeps - screen names, AIM icon and profile, persona text, hours,
the MUCK description, photos a buddy can send, their life journal and e-mail - are read live from where the
programs keep them, so a card can never disagree with how its resident behaves. Blank fields are left blank.

Gallery: every resident's icon and name (filter by where they live), with the 'not real people' disclaimer.
Card: header, screen names, personal details, favourites, fursona, personality, relationships and friends,
files and pictures, web pages, recent journal - with Back / Gallery / Forward at the bottom."""
import html
import json
import re
from pathlib import Path

from PySide6.QtCore import QRectF, QSize, Qt, QUrl
from PySide6.QtGui import QColor, QFont, QIcon, QImage, QLinearGradient, QPainter, QPen, QPixmap, QTextDocument
from PySide6.QtWidgets import (QComboBox, QHBoxLayout, QLabel, QListView, QListWidget, QListWidgetItem, QPushButton,
                               QStackedWidget, QStyledItemDelegate, QTextBrowser, QVBoxLayout, QWidget)
from shiboken6 import isValid

from ..paths import ROOT
from ..wm import XPWindow

DIR = ROOT / "Program Files" / "The Fur Directory"
RECORDS = DIR / "residents"
AIM_DIR = ROOT / "Program Files" / "ClaudeAIM"
IRC_DIR = ROOT / "Program Files" / "ClaudeIRC"
MUCK_DIR = ROOT / "Program Files" / "ClaudeMUCK" / "world"
JOURNALS = ROOT / "data" / "journals"
TITLE = "The Fur Directory"
DISCLAIMER = ("All residents of The Fur Directory are fictional characters played by ClaudeXP's AI. They are not real "
              "people, and any resemblance to real persons, living or dead, is coincidental.")
GROUPS = [("all", "Everyone"), ("aim", "AIM buddies"), ("irc", "FurNet IRC regulars"),
          ("muck", "MUCK regulars"), ("background", "Background characters")]
# The gallery's sections. A record's "tier" decides; otherwise: an AIM account = main; a regular who chats (or is on
# more than one system) = support; staff, bots, idlers and lurkers who rarely talk to you = background.
TIERS = [("user", "User Fursonas", "The fursonas offered when Windows is set up. Yours is marked."),
         ("main", "Main Furs", "They have their own instant-messenger accounts and talk to you directly."),
         ("support", "Support Furs", "Regulars you meet around FurNet IRC and the MUCK."),
         ("background", "Background Furs", "Admins, bots and the crowd in the background - they rarely talk to you.")]
TIER_NAMES = {k: label for k, label, _d in TIERS}
HEADER = Qt.UserRole + 1
PICTURE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp"}


def dir_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    for i, col in enumerate(("#C8B890", "#E8DCC0", "#FFF8E8")):            # a little stack of index cards
        r = QRectF(3 + i * 2, 5 + i * 3, 24, 17)
        p.setPen(QPen(QColor("#806A40"), 1))
        p.setBrush(QColor(col))
        p.drawRoundedRect(r, 2, 2)
    p.setPen(QPen(QColor("#B0A080"), 1))
    for y in (17, 20, 23):
        p.drawLine(19, y, 30, y)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#C8501C"))                                           # a paw on the front card
    for x, y, r in ((13, 20, 3), (9.5, 16, 1.4), (12, 14.4, 1.4), (14.8, 14.4, 1.4), (17.3, 16, 1.4)):
        p.drawEllipse(QRectF(x - r, y - r, 2 * r, 2 * r))
    p.end()
    return QIcon(pm)


def _load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def base_nick(nick):
    """'Kodiak|zzz' -> 'Kodiak', 'Raptor_' -> 'Raptor', 'Mittens^work' -> 'Mittens'."""
    return re.split(r"[|^]", nick)[0].strip("_") or nick


def slug(name):
    return re.sub(r"[^A-Za-z0-9_-]+", "_", name).strip("_") or "resident"


# ---- who lives here ------------------------------------------------------------------------------------------------

class Resident:
    def __init__(self, rid, name, group):
        self.id, self.name, self.group = rid, name, group
        self.aim = None             # the AIM contact file's dict
        self.aim_dir = None
        self.irc = None             # {"nick", "realname", "channels", "hours", "persona", "bot"}
        self.muck = None            # {"name", "species", "desc", "doing", "hours", "persona", "haunts"}
        self.record = {}
        self.preset = None          # a Setup fursona (fursonas.Preset)
        self.is_you = False

    @property
    def systems(self):
        """Where they have an account: 'aim', 'irc', 'muck' (plus any the record lists)."""
        out = {k for k, v in (("aim", self.aim), ("irc", self.irc), ("muck", self.muck)) if v}
        out |= {k for k, v in self.record.get("screen_names", {}).items() if v and k != "email"}
        return out

    @property
    def tier(self):
        if self.preset is not None:
            return "user"
        by_hand = str(self.record.get("tier", "")).lower()
        if by_hand in TIER_NAMES:
            return by_hand
        if self.aim:
            return "main"
        irc, muck = self.irc or {}, self.muck or {}
        if irc.get("lurker") or irc.get("bot") or muck.get("wizard") or muck.get("idle"):
            return "background"
        if len(self.systems) > 1 or irc.get("persona") or muck.get("persona"):
            return "support"
        return "background"

    @property
    def icon_path(self):
        if self.preset is not None:
            return self.preset.account_picture
        if self.aim and self.aim.get("icon"):
            p = AIM_DIR / "assets" / "icons" / self.aim["icon"]
            if p.exists():
                return p
        pic = self.record.get("icon")
        if pic and (DIR / pic).exists():
            return DIR / pic
        return None


def residents():
    """Everyone the AI plays, in gallery order: AIM buddies, IRC regulars, MUCK regulars, background."""
    out, seen = [], {}

    def add(name, group):
        key = name.lower()
        if key not in seen:
            seen[key] = Resident(slug(name), name, group)
            out.append(seen[key])
        return seen[key]

    for f in sorted((AIM_DIR / "contacts").glob("*.json")):
        c = _load(f, {})
        if not c.get("screen_name"):
            continue
        r = add(c["screen_name"], "aim")
        r.aim = c
        r.aim_dir = f.with_suffix("")
        irc = c.get("irc") or {}
        r.irc = {"nick": irc.get("nick", c["screen_name"]), "realname": irc.get("realname", ""),
                 "channels": irc.get("channels", []), "hours": None, "persona": "", "bot": False}
        muck = c.get("muck") or {}
        r.muck = {"name": muck.get("name", c["screen_name"]), "species": muck.get("species", ""),
                  "desc": muck.get("desc", ""), "doing": muck.get("doing", ""), "hours": None, "persona": "",
                  "haunts": muck.get("haunts", [])}
    for reg in _load(IRC_DIR / "regulars.json", {}).get("regulars", []):
        r = add(reg["nick"], "irc")
        r.irc = {"nick": reg["nick"], "realname": reg.get("realname", ""), "channels": reg.get("channels", []),
                 "hours": reg.get("hours"), "persona": reg.get("persona", ""), "bot": bool(reg.get("bot"))}
    for reg in _load(MUCK_DIR / "regulars.json", {}).get("regulars", []):
        r = add(reg["name"], "muck")
        r.muck = {"name": reg["name"], "species": reg.get("species", ""), "desc": reg.get("desc", ""),
                  "doing": reg.get("doing", ""), "hours": reg.get("hours"), "persona": reg.get("persona", ""),
                  "haunts": reg.get("haunts", []), "wizard": bool(reg.get("wizard")),
                  "idle": bool(reg.get("idle_only"))}
    lurk = {}
    for chan, c in _load(IRC_DIR / "network.json", {}).get("channels", {}).items():
        for nick in c.get("lurkers", []):
            lurk.setdefault(base_nick(nick), []).append((nick, chan))
    for name in sorted(lurk, key=str.lower):
        if name.lower() in seen:
            continue
        r = add(name, "background")
        r.irc = {"nick": lurk[name][0][0], "realname": "", "channels": [c for _n, c in lurk[name]],
                 "hours": None, "persona": "", "bot": "bot" in name.lower(), "lurker": True}
    for r in out:
        r.record = _load(RECORDS / f"{r.id}.json", {})
        if r.record.get("fur_name"):
            r.name = r.record["fur_name"]
    from .. import fursonas
    mine = fursonas.chosen()
    for pr in fursonas.presets():                               # the Setup fursonas, at the top
        r = Resident(slug("user-" + pr.id), pr.name, "user")
        r.preset, r.record, r.is_you = pr, pr.data, mine is not None and mine.id == pr.id
        out.append(r)
    order = [k for k, _l, _d in TIERS]
    out.sort(key=lambda r: order.index(r.tier))                 # stable: keeps the order within each tier
    return out


# ---- pictures --------------------------------------------------------------------------------------------------------

def avatar(r, size=64):
    """The AIM buddy icon, the record's own picture, or a drawn initial."""
    if r.preset is not None:                                    # the same tile Setup shows
        from ..fursonas import preset_pixmap
        return preset_pixmap(r.preset, size).toImage()
    p_ = r.icon_path
    if p_ is not None:
        img = QImage(str(p_))
        if not img.isNull():
            return img.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    img = QImage(size, size, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    hue = sum(map(ord, r.name)) * 37 % 360
    g = QLinearGradient(0, 0, size, size)
    g.setColorAt(0, QColor.fromHsv(hue, 90, 245))
    g.setColorAt(1, QColor.fromHsv(hue, 170, 170))
    p.setPen(QPen(QColor.fromHsv(hue, 170, 110), 1.5))
    p.setBrush(g)
    p.drawRoundedRect(QRectF(2, 2, size - 4, size - 4), 8, 8)
    p.setPen(QColor("white"))
    f = QFont("Trebuchet MS")
    f.setPixelSize(int(size * 0.5))
    f.setBold(True)
    p.setFont(f)
    p.drawText(QRectF(0, 0, size, size), Qt.AlignCenter, r.name[:1].upper())
    p.end()
    return img


def pictures(r):
    """(path, caption) for every picture the system ties to this resident."""
    out = []
    if r.aim_dir is not None and r.aim_dir.is_dir():
        caps = {}
        cap_file = r.aim_dir / "captions.txt"
        if cap_file.exists():
            for line in cap_file.read_text(encoding="utf-8", errors="replace").splitlines():
                name, _, text = line.partition(":")
                caps[name.strip()] = text.strip()
        for f in sorted(r.aim_dir.iterdir()):
            if f.suffix.lower() in PICTURE_EXTS:
                out.append((f, caps.get(f.name, "")))
    if r.preset is not None:
        out += [(path, cap or album) for album, path, cap in r.preset.photos()]
    for item in r.record.get("files", []):
        path = Path(item.get("path", "")) if isinstance(item, dict) else Path(item)
        if not path.is_absolute():
            path = ROOT / path
        if path.exists():
            out.append((path, item.get("caption", "") if isinstance(item, dict) else ""))
    return out


# ---- the card ----------------------------------------------------------------------------------------------------------

def _e(text):
    return html.escape(str(text)).replace("\n", "<br>")


def _hours(h):
    if not h:
        return ""
    def minutes(t):
        hh, _, mm = str(t).partition(":")
        return int(hh) * 60 + int(mm or 0)

    def fix(t):
        m = minutes(t) % 1440
        return f"{m // 60:02d}:{m % 60:02d}"
    if minutes(h[1]) - minutes(h[0]) >= 1440 - 1:
        return "All day"
    return f"{fix(h[0])} - {fix(h[1])}"


def _age(pers):
    """Worked out from a "dob" on ClaudeXP's 2001 calendar, when no age is written down."""
    from ..fursonas import age_from
    return age_from({"dob": pers.get("dob", "")}) if pers.get("dob") else ""


def _email(name):
    try:
        from ..life import email_address
        return email_address(name)
    except Exception:
        return ""


def _schedule(aim):
    """Sleep hours from an AIM buddy's presence schedule."""
    sched = ((aim or {}).get("presence") or {}).get("schedule") or {}
    bits = []
    for label, key in (("weekdays", "weekday"), ("weekends", "weekend")):
        d = sched.get(key)
        if d and d.get("sleep") and d.get("wake"):
            bits.append(f"{_hours((d['sleep'][0], d['wake'][1]))} {label}")
    return ", ".join(bits)


class Card:
    """Builds one resident's card as HTML for a QTextBrowser (images are added as document resources)."""
    CSS = """
    body { font-family: Tahoma; font-size: 11px; color: #2A2418; }
    h1 { font-family: 'Trebuchet MS'; font-size: 22px; color: #5A2A08; margin: 0; }
    h2 { font-family: 'Trebuchet MS'; font-size: 13px; color: #FFFFFF; background: #8A5A28; padding: 3px 6px;
         margin-top: 14px; margin-bottom: 4px; }
    td.k { color: #6A5A3A; font-weight: bold; padding-right: 10px; white-space: nowrap; }
    .blank { color: #B0A488; font-style: italic; }
    .sys { color: #8A7A5A; font-size: 10px; }
    a { color: #1A4AB0; }
    """

    def __init__(self, doc, everyone):
        self.doc = doc
        self.by_id = {r.id: r for r in everyone}
        self.by_name = {r.name.lower(): r for r in everyone}

    def _img(self, key, img):
        self.doc.addResource(QTextDocument.ImageResource, QUrl(key), img)
        return key

    def _row(self, label, value, system=""):
        if value in (None, "", [], {}):
            if system:
                return (f"<tr><td class=k>{label}</td><td>{_e(system)} "
                        f"<span class=sys>(from the system)</span></td></tr>")
            return f"<tr><td class=k>{label}</td><td class=blank>-</td></tr>"
        if isinstance(value, list):
            value = ", ".join(str(v) for v in value)
        return f"<tr><td class=k>{label}</td><td>{_e(value)}</td></tr>"

    def _section(self, title, rows):
        return f"<h2>{title}</h2><table cellspacing=2>{''.join(rows)}</table>"

    def _text(self, title, text, system=""):
        if text:
            return f"<h2>{title}</h2><p>{_e(text)}</p>"
        if system:
            return f"<h2>{title}</h2><p>{_e(system)}</p><p class=sys>(from the system)</p>"
        return f"<h2>{title}</h2><p class=blank>Nothing written yet.</p>"

    def _link(self, name):
        r = self.by_id.get(slug(name)) or self.by_name.get(str(name).lower())
        return f'<a href="card:{r.id}">{_e(r.name)}</a>' if r else _e(name)

    def build(self, r):
        rec = r.record
        pers, fav, sona = rec.get("personal", {}), rec.get("favorites", {}), rec.get("fursona", {})
        rel = rec.get("relationship", {})
        aim, irc, muck = r.aim or {}, r.irc or {}, r.muck or {}
        icon = self._img(f"avatar:{r.id}", avatar(r, 96))
        where = {"aim": "AIM buddy - also on FurNet IRC and the MUCK", "irc": "FurNet IRC regular",
                 "muck": "MUCK regular", "background": "Background character on FurNet IRC",
                 "user": "A fursona you can choose when Windows is set up"}[r.group]
        if irc.get("bot"):
            where += " (a bot)"
        if muck.get("wizard"):
            where += " (MUCK wizard)"
        where = f"{TIER_NAMES[r.tier][:-1]}  -  {where}"
        you = ('<div style="margin-top:4px"><span style="background:#C8501C; color:white; font-weight:bold;'
               ' padding:2px 6px;">&nbsp;THIS IS YOU&nbsp;</span></div>') if r.is_you else ""
        out = [f"<html><head><style>{self.CSS}</style></head><body>",
               f'<table cellspacing=0 cellpadding=0><tr><td><img src="{icon}" width=96 height=96></td>'
               f'<td style="padding-left:14px; vertical-align:middle"><h1>{_e(r.name)}</h1>'
               f'<div>{_e(where)}</div>{you}'
               + (f'<div style="margin-top:6px"><i>"{_e(aim["profile"])}"</i></div>' if aim.get("profile") else "")
               + "</td></tr></table>"]
        # screen names
        names = dict(rec.get("screen_names", {}))
        if r.preset is not None:                                 # a fursona's accounts follow its handle
            from ..user import aim_name, email_address, irc_nick, muck_name
            h = r.preset.handle
            aim = {"screen_name": aim_name(h), "profile": r.preset.get("summary")}
            irc = {"nick": irc_nick(h)}
            muck = {"name": muck_name(h), "desc": r.preset.get("online", "muck_desc")}
            names["email"] = names.get("email") or email_address(h)
        out.append(self._section("Screen names", [
            self._row("AIM", names.get("aim"), aim.get("screen_name", "")),
            self._row("FurNet IRC", names.get("irc"),
                      (irc.get("nick", "") + (f"  on {', '.join(irc['channels'])}" if irc.get("channels") else ""))
                      if irc else ""),
            self._row("MUCK", names.get("muck"), muck.get("name", "")),
            self._row("E-mail", names.get("email"), _email(r.name) if r.group == "aim" else ""),
            *[self._row(k.title(), v) for k, v in names.items() if k not in ("aim", "irc", "muck", "email")]]))
        # personal
        tz = aim.get("timezone", "")
        out.append(self._section("Personal details", [
            self._row("Real name", pers.get("real_name"), irc.get("realname", "") if irc.get("realname") not in
                      ("...", r.name) else ""),
            self._row("Location", pers.get("location"), tz.replace("_", " ").split("/")[-1] if tz else ""),
            self._row("Sex", pers.get("sex")),
            self._row("Age", pers.get("age"), str(_age(pers))),
            self._row("Date of birth", pers.get("dob")),
            self._row("Job", pers.get("job")),
            self._row("Work hours", pers.get("work_hours")),
            self._row("Sleep hours", pers.get("sleep_hours"), _schedule(aim)),
            self._row("Online hours", pers.get("online_hours"), _hours(irc.get("hours") or muck.get("hours"))),
            *[self._row(k.replace("_", " ").title(), v) for k, v in pers.items()
              if k not in ("real_name", "location", "sex", "age", "dob", "job", "work_hours", "sleep_hours",
                           "online_hours")]]))
        # favourites
        out.append(self._section("Favourites", [
            self._row("Movies", fav.get("movies")), self._row("Music", fav.get("music")),
            self._row("Food", fav.get("food")),
            *[self._row(k.replace("_", " ").title(), v) for k, v in fav.items() if k not in ("movies", "music",
                                                                                            "food")]]))
        # fursona
        out.append(self._section("Fursona", [
            self._row("Species", sona.get("species"), muck.get("species", "")),
            self._row("Colours", sona.get("colors")), self._row("Markings", sona.get("markings")),
            self._row("Clothing", sona.get("clothing")),
            *[self._row(k.replace("_", " ").title(), v) for k, v in sona.items()
              if k not in ("species", "colors", "markings", "clothing", "description")]]))
        for key, label in (("fursuit", "Fursuit"), ("conventions", "Conventions")):
            if rec.get(key):
                out.append(self._text(label, rec[key]))
        if sona.get("description") or muck.get("desc"):
            out.append(self._text("Description", sona.get("description"), muck.get("desc", "")))
        # personality
        out.append(self._text("Personality", rec.get("personality"), ""))
        persona = aim.get("persona") or irc.get("persona") or muck.get("persona")
        if persona:
            out.append(f"<h2>How the system plays them</h2><p>{_e(persona)}</p>")
        # relationships
        friends = rec.get("friends", [])
        partner = rel.get("partner")
        rows = [f"<tr><td class=k>Status</td><td>{_e(rel['status'])}</td></tr>" if rel.get("status")
                else "<tr><td class=k>Status</td><td class=blank>-</td></tr>"]
        if partner:
            rows.append(f"<tr><td class=k>Partner</td><td>{self._link(partner)}</td></tr>")
        rows.append("<tr><td class=k>Friends</td><td>" + (", ".join(self._link(f) for f in friends)
                                                          if friends else "<span class=blank>-</span>") + "</td></tr>")
        for other in rec.get("relationships", []):
            if isinstance(other, dict):
                rows.append(f"<tr><td class=k>{_e(other.get('type', 'Knows'))}</td>"
                            f"<td>{self._link(other.get('name', ''))} {_e(other.get('note', ''))}</td></tr>")
        out.append(f"<h2>Relationships</h2><table cellspacing=2>{''.join(rows)}</table>")
        # files and pictures
        pics = pictures(r)
        out.append("<h2>Pictures and files</h2>")
        if pics:
            cells = []
            for i, (path, cap) in enumerate(pics):
                thumb = QImage(str(path))
                if thumb.isNull():
                    cells.append(f'<td width=120 align=center><a href="open:{_e(path)}">{_e(path.name)}</a></td>')
                    continue
                key = self._img(f"thumb:{r.id}:{i}", thumb.scaled(110, 84, Qt.KeepAspectRatio,
                                                                  Qt.SmoothTransformation))
                cells.append(f'<td width=120 align=center valign=top><a href="open:{_e(path)}">'
                             f'<img src="{key}"></a><br><span class=sys>{_e(cap or path.name)}</span></td>')
            rows = ["<tr>" + "".join(cells[i:i + 5]) + "</tr>" for i in range(0, len(cells), 5)]
            out.append(f"<table cellspacing=6>{''.join(rows)}</table>")
        else:
            out.append("<p class=blank>No pictures or files yet.</p>")
        # web pages
        pages = rec.get("webpages", [])
        out.append("<h2>Web pages</h2>")
        if pages:
            out.append("<ul>" + "".join(
                f'<li><a href="web:{_e(p.get("url", ""))}">{_e(p.get("title") or p.get("url", ""))}</a> '
                f'<span class=sys>{_e(p.get("url", ""))}</span></li>' for p in pages if isinstance(p, dict)) + "</ul>")
        else:
            out.append("<p class=blank>No web pages yet.</p>")
        # life journal (the system's)
        journal = _load(JOURNALS / f"{r.id}.json", []) if r.group == "aim" else []
        if journal:
            out.append("<h2>Recent life events</h2><table cellspacing=2>" + "".join(
                f"<tr><td class=k>{_e(e.get('date', ''))}</td><td>{_e(e.get('text', ''))}</td></tr>"
                for e in reversed(journal[-6:])) + "</table><p class=sys>(from their journal)</p>")
        if rec.get("notes"):
            out.append(self._text("Notes", rec["notes"]))
        for key, value in rec.items():                           # anything we add later gets shown too
            if key in ("id", "fur_name", "tier", "icon", "screen_names", "personal", "favorites", "fursona",
                       "personality", "relationship", "friends", "relationships", "files", "webpages", "notes",
                       "handle", "summary", "online", "knows", "fursuit", "conventions"):
                continue
            if isinstance(value, dict):
                out.append(self._section(key.replace("_", " ").title(),
                                         [self._row(k.replace("_", " ").title(), v) for k, v in value.items()]))
            elif value not in (None, "", []):
                out.append(self._text(key.replace("_", " ").title(),
                                      ", ".join(map(str, value)) if isinstance(value, list) else value))
        out.append("</body></html>")
        return "".join(out)


# ---- the window --------------------------------------------------------------------------------------------------

class _GalleryList(QListWidget):
    """Icon view whose section headers stretch across the whole row."""

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fit_headers()

    def fit_headers(self):
        w = max(200, self.viewport().width() - 12)
        for i in range(self.count()):
            item = self.item(i)
            if item.data(HEADER):
                item.setSizeHint(QSize(w, 46))
        self.doItemsLayout()


class _GalleryDelegate(QStyledItemDelegate):
    def paint(self, p, option, index):
        head = index.data(HEADER)
        if not head:
            return super().paint(p, option, index)
        title, blurb, n = head
        r = QRectF(option.rect).adjusted(2, 8, -2, -2)
        p.save()
        p.setRenderHint(QPainter.Antialiasing)
        g = QLinearGradient(r.topLeft(), r.topRight())
        g.setColorAt(0, QColor("#8A5A28"))
        g.setColorAt(1, QColor("#E8D4A8"))
        p.setPen(Qt.NoPen)
        p.setBrush(g)
        p.drawRoundedRect(r, 4, 4)
        f = QFont("Trebuchet MS", 11)
        f.setBold(True)
        p.setFont(f)
        p.setPen(QColor("#FFF8E8"))
        p.drawText(r.adjusted(10, 0, 0, 0), Qt.AlignVCenter | Qt.AlignLeft, f"{title}  ({n})")
        p.setFont(QFont("Tahoma", 8))
        p.setPen(QColor("#4A3418"))
        p.drawText(r.adjusted(0, 0, -10, 0), Qt.AlignVCenter | Qt.AlignRight, blurb)
        p.restore()


class FurDirectory(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.everyone = residents()
        self.shown = list(self.everyone)
        self.index = 0
        self.setObjectName("fd")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("QWidget#fd { background: #F4ECD8; } QLabel { font: 11px Tahoma; }"
                           "QListWidget { background: #FFFBF0; border: 1px solid #C8B890; font: 11px Tahoma; }"
                           "QListWidget::item:selected { background: #E8D4A8; color: black; }"
                           "QTextBrowser { background: #FFFBF0; border: 1px solid #C8B890; }"
                           "QPushButton { font: 11px Tahoma; min-width: 80px; padding: 3px 8px; }")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        banner = QLabel()
        banner.setPixmap(self._banner())
        lay.addWidget(banner)
        self.stack = QStackedWidget()
        lay.addWidget(self.stack, 1)
        # gallery
        g = QWidget()
        gv = QVBoxLayout(g)
        gv.setContentsMargins(0, 6, 0, 0)
        top = QHBoxLayout()
        top.addWidget(QLabel("Show:"))
        self.filter = QComboBox()
        self.filter.addItem("Everyone", "all")
        for key, label, _d in TIERS:
            self.filter.addItem(label, f"tier:{key}")
        for key, label in (("aim", "On AIM"), ("irc", "On FurNet IRC"), ("muck", "On the MUCK")):
            self.filter.addItem(label, f"on:{key}")
        self.filter.currentIndexChanged.connect(self.fill)
        top.addWidget(self.filter)
        top.addStretch()
        self.count = QLabel()
        top.addWidget(self.count)
        gv.addLayout(top)
        self.grid = _GalleryList()
        self.grid.setViewMode(QListView.IconMode)
        self.grid.setIconSize(QSize(64, 64))
        self.grid.setResizeMode(QListView.Adjust)
        self.grid.setMovement(QListView.Static)
        self.grid.setWordWrap(True)
        self.grid.setSpacing(2)
        self.grid.setItemDelegate(_GalleryDelegate(self.grid))
        self.grid.itemActivated.connect(self._activated)
        gv.addWidget(self.grid, 1)
        note = QLabel(DISCLAIMER)
        note.setWordWrap(True)
        note.setAlignment(Qt.AlignCenter)
        note.setStyleSheet("color: #6A5A3A; font-style: italic; padding: 6px; border-top: 1px solid #C8B890;")
        gv.addWidget(note)
        self.stack.addWidget(g)
        # card
        c = QWidget()
        cv = QVBoxLayout(c)
        cv.setContentsMargins(0, 6, 0, 0)
        self.page = QTextBrowser()
        self.page.setOpenLinks(False)
        self.page.anchorClicked.connect(self._link)
        cv.addWidget(self.page, 1)
        row = QHBoxLayout()
        self.back = QPushButton("◄ Back")
        self.home = QPushButton("Gallery")
        self.fwd = QPushButton("Forward ►")
        self.back.clicked.connect(lambda: self.show_card(self.index - 1))
        self.home.clicked.connect(self.show_gallery)
        self.fwd.clicked.connect(lambda: self.show_card(self.index + 1))
        self.where = QLabel()
        row.addWidget(self.back)
        row.addStretch()
        row.addWidget(self.where)
        row.addStretch()
        row.addWidget(self.home)
        row.addStretch()
        row.addWidget(self.fwd)
        cv.addLayout(row)
        self.stack.addWidget(c)
        self.fill()

    @staticmethod
    def _banner():
        pm = QPixmap(700, 46)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        g = QLinearGradient(0, 0, 700, 0)
        g.setColorAt(0, QColor("#6A3A10"))
        g.setColorAt(1, QColor("#C8964A"))
        p.setPen(Qt.NoPen)
        p.setBrush(g)
        p.drawRoundedRect(QRectF(0, 0, 700, 46), 6, 6)
        p.drawPixmap(10, 7, dir_icon().pixmap(32, 32))
        f = QFont("Trebuchet MS", 17)
        f.setBold(True)
        p.setFont(f)
        p.setPen(QColor("#FFF4DC"))
        p.drawText(QRectF(52, 0, 500, 46), Qt.AlignVCenter | Qt.AlignLeft, "The Fur Directory")
        p.setFont(QFont("Tahoma", 8))
        p.setPen(QColor("#F8E4C0"))
        p.drawText(QRectF(300, 0, 390, 46), Qt.AlignVCenter | Qt.AlignRight, "Who's who among the residents")
        p.end()
        return pm

    def fill(self, *_):
        what = self.filter.currentData() or "all"
        kind, _, value = what.partition(":")
        self.shown = [r for r in self.everyone if kind == "all" or (kind == "tier" and r.tier == value)
                      or (kind == "on" and value in r.systems)]
        self.grid.clear()
        self.rows = []                                   # grid row -> index in self.shown (None for headers)
        for key, label, blurb in TIERS:
            members = [(i, r) for i, r in enumerate(self.shown) if r.tier == key]
            if not members:
                continue
            head = QListWidgetItem()
            head.setFlags(Qt.NoItemFlags)
            head.setData(HEADER, (label, blurb, len(members)))
            self.grid.addItem(head)
            self.rows.append(None)
            for i, r in members:
                item = QListWidgetItem(QIcon(QPixmap.fromImage(avatar(r, 64))), r.name)
                item.setSizeHint(QSize(100, 96))
                item.setToolTip(f"{label[:-1]} - {dict(GROUPS).get(r.group, 'a Setup fursona')}")
                self.grid.addItem(item)
                self.rows.append(i)
        self.grid.fit_headers()
        self.count.setText(f"{len(self.shown)} resident{'s' if len(self.shown) != 1 else ''}")
        self.index = 0
        self.show_gallery()

    def _activated(self, item):
        i = self.rows[self.grid.row(item)]
        if i is not None:
            self.show_card(i)

    def show_gallery(self):
        self.stack.setCurrentIndex(0)
        if self.index in self.rows:
            self.grid.setCurrentRow(self.rows.index(self.index))
        if self.frame is not None:
            self.frame.set_title(TITLE)

    def show_card(self, i):
        if not self.shown:
            return
        self.index = i % len(self.shown)
        r = self.shown[self.index]
        doc = self.page.document()
        doc.clear()
        self.page.setHtml(Card(doc, self.everyone).build(r))
        self.page.verticalScrollBar().setValue(0)
        self.where.setText(f"{self.index + 1} of {len(self.shown)}")
        self.stack.setCurrentIndex(1)
        if self.frame is not None:
            self.frame.set_title(f"{r.name} - {TITLE}")

    def _link(self, url):
        text = url.toString()
        kind, _, value = text.partition(":")
        if kind == "card":
            for i, r in enumerate(self.shown):
                if r.id == value:
                    self.show_card(i)
                    return
            self.filter.setCurrentIndex(0)                       # not in this filter: show everyone
            for i, r in enumerate(self.shown):
                if r.id == value:
                    self.show_card(i)
        elif kind == "open":
            from ..explorer import viewers
            viewers.open_file(self.desktop, Path(html.unescape(value)))
        elif kind == "web":
            from . import navigator
            navigator.launch(self.desktop, url=html.unescape(value))

    def keyPressEvent(self, event):
        if self.stack.currentIndex() == 1:
            if event.key() in (Qt.Key_Left, Qt.Key_PageUp):
                self.show_card(self.index - 1)
                return
            if event.key() in (Qt.Key_Right, Qt.Key_PageDown):
                self.show_card(self.index + 1)
                return
            if event.key() in (Qt.Key_Escape, Qt.Key_Backspace):
                self.show_gallery()
                return
        super().keyPressEvent(event)


_open = {}


def open_furdir(desktop, show_me=False):
    win = _open.get("win")
    if win is None or not isValid(win):
        body = FurDirectory(desktop)
        win = XPWindow(desktop, TITLE, body, dir_icon(), (760, 600))
        body.frame = win
        _open["win"] = win
    desktop.open_window(win)
    if show_me:                                                  # User Accounts' 'View my fursona's card'
        body = win.content
        body.filter.setCurrentIndex(0)
        for i, r in enumerate(body.shown):
            if r.is_you:
                body.show_card(i)
    return win
