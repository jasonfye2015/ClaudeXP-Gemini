"""Furry Chat Logs: years of chat logs from many clients, browsed by service, account and contact.

Reads the index chatlogs.index builds (Text Logs/_Index/chatlogs.sqlite): home is a shelf of services (AIM, Yahoo!,
MSN, ICQ, IRC, Second Life...), a service opens as the user's accounts on it, and an account as everyone they talked
to and every room they were in. A conversation opens as one transcript collated from every backup and client, in the
classic colours (you in blue, them in red) with a divider for each day: one-to-one chats a year at a time (a month at
a time for very busy years), rooms a day at a time. 'Search all logs' finds words anywhere and opens the transcript
at the line."""
import html
import sqlite3
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (QComboBox, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QTextBrowser,
                               QToolButton, QVBoxLayout, QWidget)
from shiboken6 import isValid

from folio.cdviewer import CDViewer
from folio.gallery import Node
from claudecore import host

from .index import db_path

TILE = 150
BUSY_YEAR = 6000                              # a one-to-one chat year with more lines than this goes month by month
COLOURS = {"AIM": ("#FFD200", "#202020"), "ICQ": ("#3BB54A", "white"), "Yahoo! Messenger": ("#6A1B9A", "white"),
           "MSN Messenger": ("#1E8AD8", "white"), "IRC": ("#505860", "white"), "Second Life": ("#00A0A0", "white"),
           "Jabber": ("#C04020", "white"), "Google Talk": ("#4285F4", "white"), "Skype": ("#00AFF0", "white")}


def chat_icon():
    """Two speech bubbles with a red paw in the front one."""
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor("#20408A"), 1))
    p.setBrush(QColor("#9CC0F4"))
    p.drawRoundedRect(QRectF(12.5, 3.5, 17, 12), 4, 4)
    p.setBrush(QColor("#FFFFFF"))
    bubble = QPainterPath()
    bubble.addRoundedRect(QRectF(2.5, 10.5, 19, 14), 4, 4)
    bubble.moveTo(6, 24)
    bubble.lineTo(4, 29.5)
    bubble.lineTo(11, 24)
    p.setPen(QPen(QColor("#5A5A5A"), 1))
    p.drawPath(bubble.simplified())
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#D8261C"))
    for x, y, r in ((12, 19.4, 2.3), (8.8, 16.2, 1.1), (10.9, 14.8, 1.1), (13.1, 14.8, 1.1), (15.2, 16.2, 1.1)):
        p.drawEllipse(QRectF(x - r, y - r, 2 * r, 2 * r))
    p.end()
    return QIcon(pm)


def logs_root():
    root = host.local_storage() / "Text Logs"
    return root if root.is_dir() else None


def _years(first, last):
    a, b = datetime.fromtimestamp(first).year, datetime.fromtimestamp(last).year
    return str(a) if a == b else f"{a}-{b}"


def _n(count, word, plural=None):
    return f"{count:,} {word if count == 1 else plural or word + 's'}"


def _nice_account(service, account):
    names = {"?": "Unknown account", "irc": "IRC logs", "mirc": "mIRC", "virc": "vIRC",
             "second life": "Unknown account"}
    if account in names:
        return names[account]
    return account.title() if service == "Second Life" else account


# ---- tiles ------------------------------------------------------------------------------------------------------
def _card(title, lines, colour, ink, kind):
    """A service badge, an account card or a contact card."""
    t = TILE + 20
    pm = QPixmap(t, t)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    if kind == "service":
        r = QRectF(22, 14, t - 44, t - 44)
        g = QLinearGradient(r.topLeft(), r.bottomLeft())
        g.setColorAt(0, QColor(colour).lighter(125))
        g.setColorAt(1, QColor(colour))
        p.fillRect(r.translated(3, 4), QColor(0, 0, 0, 70))
        p.setPen(QPen(QColor(colour).darker(150), 1))
        p.setBrush(g)
        p.drawRoundedRect(r, 18, 18)
        p.setPen(QColor(ink))
        p.setFont(QFont("Arial", 13 if len(title) > 8 else 20, QFont.Bold))
        p.drawText(r.adjusted(6, 0, -6, 0), Qt.AlignCenter | Qt.TextWordWrap, title)
    else:
        r = QRectF(14, 20, t - 28, t - 52)
        p.fillRect(r.translated(3, 4), QColor(0, 0, 0, 55))
        p.setPen(QPen(QColor("#9098A8"), 1))
        p.setBrush(QColor("#FFFFFF"))
        p.drawRoundedRect(r, 6, 6)
        head = QRectF(r.left(), r.top(), r.width(), 26)
        path = QPainterPath()
        path.addRoundedRect(head, 6, 6)
        path.addRect(QRectF(head.left(), head.top() + 10, head.width(), 16))
        p.fillPath(path.simplified(), QColor(colour))
        p.setPen(QColor(ink))
        p.setFont(QFont("Tahoma", 8, QFont.Bold))
        p.drawText(head.adjusted(8, 0, -8, 0), Qt.AlignVCenter | Qt.AlignLeft,
                   "ROOM" if kind == "room" else "ACCOUNT" if kind == "account" else "BUDDY")
        p.setPen(QColor("#202020"))
        p.setFont(QFont("Tahoma", 10, QFont.Bold))
        body = QRectF(r.left() + 8, head.bottom() + 6, r.width() - 16, r.height() - 36)
        p.drawText(body, Qt.AlignHCenter | Qt.AlignTop | Qt.TextWordWrap, title)
        p.setPen(QColor("#606870"))
        p.setFont(QFont("Tahoma", 8))
        p.drawText(body, Qt.AlignHCenter | Qt.AlignBottom | Qt.TextWordWrap, lines)
    p.end()
    return pm


# ---- the transcript ---------------------------------------------------------------------------------------------
class Transcript(QWidget):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        self.conv = None
        self.periods = []
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        bar = QWidget()
        bar.setObjectName("tbar")
        bar.setAttribute(Qt.WA_StyledBackground)
        bar.setStyleSheet("QWidget#tbar { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #FDFDFB,"
                          " stop:1 #E3E0D2); border-bottom: 1px solid #A0A0A0; }"
                          "QToolButton { font: 11px Tahoma; padding: 3px 8px; border: 1px solid transparent;"
                          " border-radius: 3px; } QToolButton:hover { border-color: #C0BCA8; background: white; }"
                          "QLabel { font: bold 11px Tahoma; color: #303030; } QComboBox { font: 11px Tahoma; }")
        row = QHBoxLayout(bar)
        row.setContentsMargins(4, 3, 6, 3)
        back = QToolButton()
        back.setText("◄ Back")
        back.clicked.connect(owner.close_transcript)
        row.addWidget(back)
        row.addSpacing(8)
        self.title = QLabel()
        row.addWidget(self.title, 1)
        self.prev = QToolButton()
        self.prev.setText("◄")
        self.prev.clicked.connect(lambda: self.periods_box.setCurrentIndex(max(0, self.periods_box.currentIndex() - 1)))
        row.addWidget(self.prev)
        self.periods_box = QComboBox()
        self.periods_box.setMinimumWidth(200)
        self.periods_box.currentIndexChanged.connect(self._show_period)
        row.addWidget(self.periods_box)
        self.next = QToolButton()
        self.next.setText("►")
        self.next.clicked.connect(lambda: self.periods_box.setCurrentIndex(
            min(self.periods_box.count() - 1, self.periods_box.currentIndex() + 1)))
        row.addWidget(self.next)
        lay.addWidget(bar)
        self.view = QTextBrowser()
        self.view.setOpenExternalLinks(False)
        self.view.setOpenLinks(False)
        self.view.setStyleSheet("QTextBrowser { background: white; border: none; padding: 8px; }")
        lay.addWidget(self.view, 1)
        self.anchor = None

    def open(self, conv, at_id=None):
        """conv = (service, account, contact, room, display name)."""
        self.conv = conv
        service, account, contact, room, name = conv
        self.title.setText(f"{name}  -  {service}, {_nice_account(service, account)}")
        db = self.owner.db
        if room:
            rows = db.execute("SELECT strftime('%Y-%m-%d', ts, 'unixepoch', 'localtime') d, COUNT(*), MIN(ts), MAX(ts)"
                              " FROM messages WHERE service=? AND account=? AND contact=? GROUP BY d ORDER BY d",
                              (service, account, contact)).fetchall()
            self.periods = [(datetime.strptime(d, "%Y-%m-%d").strftime("%a %b %d, %Y"), lo, hi, n)
                            for d, n, lo, hi in rows]
        else:
            years = db.execute("SELECT strftime('%Y', ts, 'unixepoch', 'localtime') y, COUNT(*), MIN(ts), MAX(ts)"
                               " FROM messages WHERE service=? AND account=? AND contact=? GROUP BY y ORDER BY y",
                               (service, account, contact)).fetchall()
            self.periods = []
            for y, n, lo, hi in years:
                if n > BUSY_YEAR:
                    for m, mn, mlo, mhi in db.execute(
                            "SELECT strftime('%m', ts, 'unixepoch', 'localtime') m, COUNT(*), MIN(ts), MAX(ts) FROM messages"
                            " WHERE service=? AND account=? AND contact=? AND ts BETWEEN ? AND ? GROUP BY m ORDER BY m",
                            (service, account, contact, lo, hi)):
                        self.periods.append((datetime(int(y), int(m), 1).strftime("%B %Y"), mlo, mhi, mn))
                else:
                    self.periods.append((y, lo, hi, n))
        self.anchor = at_id
        index = len(self.periods) - 1 if room else 0
        if at_id is not None:
            ts = db.execute("SELECT ts FROM messages WHERE id=?", (at_id,)).fetchone()[0]
            index = next((i for i, (_l, lo, hi, _n) in enumerate(self.periods) if lo <= ts <= hi), 0)
        self.periods_box.blockSignals(True)
        self.periods_box.clear()
        for label, _lo, _hi, n in self.periods:
            self.periods_box.addItem(f"{label}  ({n:,} lines)")
        self.periods_box.blockSignals(False)
        self.periods_box.setCurrentIndex(index)
        self._show_period(index)

    def _show_period(self, index):
        if not (0 <= index < len(self.periods)) or self.conv is None:
            return
        service, account, contact, _room, _name = self.conv
        _label, lo, hi, _n = self.periods[index]
        self.prev.setEnabled(index > 0)
        self.next.setEnabled(index < len(self.periods) - 1)
        rows = self.owner.db.execute(
            "SELECT id, ts, approx, outgoing, speaker, text FROM messages WHERE service=? AND account=? AND contact=?"
            " AND ts BETWEEN ? AND ? ORDER BY ts, id", (service, account, contact, lo, hi)).fetchall()
        out, day = ["<div style='font-family: Arial; font-size: 10pt'>"], None
        for mid, ts, approx, outgoing, who, text in rows:
            when = datetime.fromtimestamp(ts)
            if when.date() != day:
                day = when.date()
                note = " <span style='color:#A08060; font-weight:normal'>(date approximate)</span>" if approx else ""
                out.append(f"<p style='margin:14px 0 4px 0; color:#506080; font-weight:bold; "
                           f"border-bottom:1px solid #C8D0E0'>{when.strftime('%A, %B %d, %Y')}{note}</p>")
            colour = "#16569E" if outgoing else "#A82F2F"
            body = html.escape(text).replace("\n", "<br>")
            if mid == self.anchor:
                body = f"<span style='background:#FFF2A0'>{body}</span>"
            out.append(f"<a name='m{mid}'></a><div style='margin:1px 0'><span style='color:#909090; font-size:8pt'>"
                       f"({when.strftime('%I:%M %p').lstrip('0')})</span> <b style='color:{colour}'>"
                       f"{html.escape(who)}:</b> {body}</div>")
        out.append("</div>")
        self.view.setHtml("".join(out))
        if self.anchor is not None:
            QTimer.singleShot(0, lambda a=self.anchor: self.view.scrollToAnchor(f"m{a}"))
        else:
            self.view.verticalScrollBar().setValue(0)


# ---- search results ---------------------------------------------------------------------------------------------
class Results(QListWidget):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        self.setStyleSheet("QListWidget { background: white; border: none; font: 11px Tahoma; }"
                           "QListWidget::item { padding: 4px 6px; border-bottom: 1px solid #ECE9D8; }"
                           "QListWidget::item:selected { background: #316AC5; color: white; }")
        self.itemActivated.connect(lambda item: owner.open_result(item.data(Qt.UserRole)))


# ---- the program --------------------------------------------------------------------------------------------------
class ChatLogs(CDViewer):
    TITLE = "Furry Chat Logs"
    PLACE = "Chat Logs"
    RACK = "All Services"

    def find_root(self):
        root = logs_root()
        return root if root is not None and db_path(root).exists() else None

    def __init__(self, desktop):
        self.db = None
        self.level = ("home",)
        self.levels = []
        root = self.find_root()
        if root is not None:
            self.db = sqlite3.connect(f"file:{db_path(root).as_posix()}?mode=ro", uri=True)
        super().__init__(desktop)
        self.wall.setIconSize(QSize(TILE + 20, TILE + 20))
        self.wall.setGridSize(QSize(TILE + 36, TILE + 46))
        self.transcript = Transcript(self)
        self.stack.addWidget(self.transcript)
        self.results = Results(self)
        self.stack.addWidget(self.results)
        if self.root is None:
            self.status.setText("The chat logs haven't been indexed yet: put them in 'Text Logs' on drive E: (Local "
                                "Storage) and build the index.")

    def _bar(self):
        bar = super()._bar()
        row = bar.layout()
        self.find.setPlaceholderText("Name")
        row.addSpacing(8)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search all logs...")
        self.search.setFixedWidth(170)
        self.search.returnPressed.connect(self.run_search)
        row.addWidget(self.search)
        return bar

    # ---- browsing ---------------------------------------------------------------------------------------------
    def show_rack(self):
        self.levels.clear()
        self.show_level(("home",), remember=False)

    def show_level(self, level, remember=True):
        if self.db is None:
            return
        if remember and level != self.level:
            self.levels.append(self.level)
        self.level = level
        self._reset()
        self.here = None
        self.stack.setCurrentIndex(0)
        self.back_btn.setEnabled(bool(self.levels))
        q = self.db.execute
        if level[0] == "home":
            rows = q("SELECT service, COUNT(DISTINCT account), SUM(lines), MIN(first), MAX(last) FROM contacts"
                     " GROUP BY service ORDER BY SUM(lines) DESC").fetchall()
            nodes = []
            for service, accounts, lines, first, last in rows:
                n = Node(f"service/{service}", "service", service,
                         f"{lines:,} lines, {_years(first, last)}")
                nodes.append(n)
            crumbs, words = [], _n(len(nodes), "service")
            self._set_wall_look(True)
        elif level[0] == "service":
            service = level[1]
            rows = q("SELECT account, COUNT(*), SUM(lines), MIN(first), MAX(last) FROM contacts WHERE service=?"
                     " GROUP BY account ORDER BY SUM(lines) DESC", (service,)).fetchall()
            nodes = [Node(f"account/{service}/{a}", "account", _nice_account(service, a),
                          f"{_n(c, 'buddy or room', 'buddies and rooms')}\n{_n(lines, 'line')}, {_years(lo, hi)}")
                     for a, c, lines, lo, hi in rows]
            for n, (a, *_rest) in zip(nodes, rows):
                n.artist = n.artist + "\0" + a
            crumbs, words = [service], _n(len(nodes), "account")
            self._set_wall_look(True)
        else:
            service, account = level[1], level[2]
            aliases = {}
            for contact, who, n in q("SELECT contact, speaker, COUNT(*) FROM messages WHERE service=? AND account=?"
                                     " AND outgoing=0 GROUP BY contact, speaker", (service, account)):
                if n > aliases.get(contact, ("", 0))[1]:
                    aliases[contact] = (who, n)
            rows = q("SELECT contact, room, lines, first, last FROM contacts WHERE service=? AND account=?"
                     " ORDER BY room, contact COLLATE NOCASE", (service, account)).fetchall()
            nodes = []
            for contact, room, lines, lo, hi in rows:
                alias = aliases.get(contact, ("", 0))[0]
                name = contact if room or not alias or alias.lower().replace(" ", "") == contact else \
                    f"{alias}\n({contact})"
                node = Node(f"contact/{service}/{account}/{contact}", "room" if room else "buddy", name,
                            f"{lines:,} lines, {_years(lo, hi)}\0{contact}")
                nodes.append(node)
            crumbs = [service, _nice_account(service, account)]
            rooms = sum(1 for r in rows if r[1])
            words = ", ".join(_n(n, w, pl) for n, w, pl in ((len(rows) - rooms, "buddy", "buddies"), (rooms, "room", None))
                              if n)
            self._set_wall_look(False)
        self.wall.fill(nodes)
        self.where.setText("  ›  ".join([self.PLACE] + crumbs))
        self.status.setText(words)
        if self.frame is not None:
            self.frame.set_title(f"{crumbs[-1]} - {self.TITLE}" if crumbs else self.TITLE)

    def go_back(self):
        if self.stack.currentIndex() != 0:
            self.close_transcript()
            return
        if self.levels:
            self.show_level(self.levels.pop(), remember=False)

    def open_node(self, node):
        if node.kind == "service":
            self.show_level(("service", node.name))
        elif node.kind == "account":
            self.show_level(("account", self.level[1], node.artist.split("\0")[1]))
        elif node.kind in ("buddy", "room"):
            contact = node.artist.split("\0")[1]
            self.open_conversation((self.level[1], self.level[2], contact, node.kind == "room",
                                    node.name.replace("\n", " ")))

    def open_conversation(self, conv, at_id=None):
        self.transcript.open(conv, at_id)
        self.stack.setCurrentWidget(self.transcript)
        if self.frame is not None:
            self.frame.set_title(f"{conv[4]} - {self.TITLE}")

    def close_transcript(self):
        self.stack.setCurrentIndex(0)
        if self.frame is not None:
            self.frame.set_title(self.TITLE)

    # ---- search -----------------------------------------------------------------------------------------------
    def run_search(self):
        words = self.search.text().strip()
        if not words or self.db is None:
            return
        query = " ".join(f'"{w}"' for w in words.replace('"', " ").split())
        try:
            rows = self.db.execute(
                "SELECT m.id, m.service, m.account, m.contact, m.room, m.ts, m.speaker, m.text FROM search s"
                " JOIN messages m ON m.id = s.rowid WHERE search MATCH ? ORDER BY m.ts LIMIT 1000", (query,)).fetchall()
        except sqlite3.Error:
            rows = []
        self.results.clear()
        for mid, service, account, contact, room, ts, who, text in rows:
            when = datetime.fromtimestamp(ts).strftime("%b %d, %Y")
            item = QListWidgetItem(f"{when}   {service} / {_nice_account(service, account)} / {contact}\n"
                                   f"      {who}: {text[:160]}")
            item.setData(Qt.UserRole, (mid, service, account, contact, room))
            self.results.addItem(item)
        self.stack.setCurrentWidget(self.results)
        self.status.setText(f"{len(rows):,} lines found" + (" (the first 1,000)" if len(rows) == 1000 else "")
                            + f" for '{words}'")

    def open_result(self, data):
        mid, service, account, contact, room = data
        self.open_conversation((service, account, contact, bool(room), contact), at_id=mid)

    # ---- tiles ------------------------------------------------------------------------------------------------
    def want_thumb(self, node, callback=None):
        pass

    def paint_tile(self, item):
        node = item.data(Qt.UserRole)
        caption = node.artist.split("\0")[0]
        if node.kind == "service":
            colour, ink = COLOURS.get(node.name, ("#707888", "white"))
            pm = _card(node.name, caption, colour, ink, "service")
        else:
            service = self.level[1] if len(self.level) > 1 else ""
            colour, ink = COLOURS.get(service, ("#707888", "white"))
            pm = _card(node.name, caption.split("\n")[-1] if node.kind != "account" else caption.split("\n")[0],
                       colour, ink, node.kind)
        item.setIcon(QIcon(pm))
        item.setText(caption.split("\n")[-1] if node.kind != "service" else caption)
        item.setToolTip(f"{node.name}\n{caption}")

    def closeEvent(self, event):
        if self.db is not None:
            self.db.close()
            self.db = None
        super().closeEvent(event)


_open = {}


def open_chatlogs(desktop):
    win = _open.get("win")
    if win is None or not isValid(win):
        body = ChatLogs(desktop)
        win = host.window(desktop, ChatLogs.TITLE, body, chat_icon(), (920, 660))
        body.frame = win
        _open["win"] = win
        if body.root is not None:
            body.show_rack()
    desktop.open_window(win)
    return win


def shutdown():
    win = _open.get("win")
    if win is not None and isValid(win):
        win.content.video.stop()
