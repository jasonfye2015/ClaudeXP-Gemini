"""Yahoo! Messenger 5.0: the sign-in box, the purple window with 'I'm Available', the Friends group of smileys,
and IM windows with a formatting bar where every line reads 'yahoo_id: message'. Buddies have Yahoo! IDs."""
import html
import re

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter
from PySide6.QtWidgets import (QCheckBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMenu, QMenuBar,
                               QPushButton, QStackedWidget, QToolButton, QVBoxLayout, QWidget)

from . import art
from .client import Client
from .core import AWAY, BUSY, OFFLINE, ONLINE, Network
from .ui import BuddyTree

e = html.escape
TAHOMA = "font-family: Tahoma, Verdana; font-size: 11px;"
PURPLE, DARK, YELLOW = "#7B1FA2", "#4A0D72", "#FFD400"
STATUSES = [("I'm Available", ONLINE), ("Be Right Back", AWAY), ("Busy", BUSY), ("Not at My Desk", AWAY),
            ("On the Phone", BUSY), ("Stepped Out", AWAY), ("Invisible to everyone", AWAY)]


def yahoo_id(name):
    return re.sub(r"[^a-z0-9_]+", "_", name.lower()).strip("_") or "user"


class YIMNetwork(Network):
    key, title = "yim", "Yahoo! Messenger"

    def handle_for(self, contact):
        return self.sections.get(contact.id, {}).get("id") or yahoo_id(contact.screen_name)


class Skin:
    title = "Yahoo! Messenger"
    main_size = (240, 470)
    convo_size = (470, 400)
    send_label, send_size, send_sound = "Send", QSize(60, 26), False
    message_sound = signin_sound = "Yahoo_Messenger_Notification_Sound.mp3"
    login_sound = None
    toast_colors = ("#FFF7C2", "#FFE24A", DARK, "#3A0A5A")
    window_style = "QWidget#convo { background: #EDE6F5; }"
    transcript_style = ("QTextBrowser { background: white; border: 1px solid #9A86B8; font-family: Arial; "
                        "font-size: 12px; padding: 4px; }")
    input_style = "QTextEdit { background: white; border: 1px solid #9A86B8; font-family: Arial; font-size: 12px; }"
    send_style = ("QPushButton { font-family: Tahoma; font-size: 11px; font-weight: bold; color: white; "
                  f"background: {PURPLE}; border: 1px solid {DARK}; }} QPushButton:pressed {{ background: {DARK}; }}")
    status_style = "QLabel { background: #EDE6F5; color: #4A3A5A; padding: 2px 6px; " + TAHOMA + " }"

    def __init__(self, network):
        self.network = network

    def app_icon(self):
        return art.icon("yim_logo", 32)

    def toast_logo(self):
        return art.pixmap("yim_logo", 22)

    def display(self, b):
        return b.handle

    def convo_title(self, b):
        return f"{b.handle} - Instant Message"

    def toolbar(self, conv):
        bar = QWidget()
        bar.setStyleSheet(f"QWidget {{ background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {PURPLE}, "
                          f"stop:1 {DARK}); }}")
        row = QHBoxLayout(bar)
        row.setContentsMargins(6, 3, 6, 3)
        for text in ("Webcam", "Voice", "Send File", "IMVironments", "Address Book"):
            b = QToolButton()
            b.setText(text)
            b.setStyleSheet("QToolButton { border: none; color: white; background: transparent; " + TAHOMA + " }"
                            f"QToolButton:hover {{ color: {YELLOW}; }}")
            b.clicked.connect(lambda _c=False, t=text: conv.status.setText(f"{t} isn't available right now."))
            row.addWidget(b)
        row.addStretch()
        logo = QLabel()
        logo.setPixmap(art.pixmap("yim_logo", 26))
        row.addWidget(logo)
        return bar

    def header(self, conv, b):
        lab = QLabel(f"&nbsp;To: <b>{e(b.handle)}</b>")
        lab.setStyleSheet("QLabel { background: #EDE6F5; color: #3A0A5A; padding: 5px 4px; " + TAHOMA + " }")
        return lab

    def format_bar(self, conv):
        bar = QWidget()
        bar.setStyleSheet("QWidget { background: #EDE6F5; }")
        row = QHBoxLayout(bar)
        row.setContentsMargins(6, 2, 6, 0)
        for text, style in (("B", "font-weight: bold;"), ("I", "font-style: italic;"),
                            ("U", "text-decoration: underline;")):
            b = QToolButton()
            b.setText(text)
            b.setCheckable(True)
            b.setFixedSize(22, 20)
            b.setStyleSheet(f"QToolButton {{ {style} font-family: Arial; border: 1px solid #B9A9D0; background: white; }}"
                            "QToolButton:checked { background: #D9C9F0; }")
            row.addWidget(b)
        smile = QToolButton()
        smile.setIcon(art.icon("yim_online", 16))
        smile.setFixedSize(26, 20)
        smile.setToolTip("Emoticons")
        smile.clicked.connect(lambda: conv.input.insertPlainText(" :) "))
        row.addWidget(smile)
        row.addStretch()
        return bar

    def line(self, entry, me, b):
        kind, text = entry["kind"], e(entry["text"]).replace("\n", "<br>")
        if kind == "system":
            return f'<span style="color:#808080;"><i>{text}</i></span>'
        if kind == "user":
            return f'<span style="color:#0000CC;"><b>{e(yahoo_id(me))}</b></span>: {text}'
        return f'<span style="color:#CC0000;"><b>{e(b.handle)}</b></span>: {text}'

    def typing_text(self, b):
        return f"{b.handle} is typing a message"

    def received_text(self, t):
        return f"Last message received on {t.month}/{t.day}/01 at {t:%I:%M %p}".replace(" 0", " ")

    def main_window(self, client):
        return YIMMain(client)


class YIMMain(QWidget):
    def __init__(self, client):
        super().__init__()
        self.client, self.network = client, client.network
        self.frame = None
        self.process_image = "ypager.exe"             # for Task Manager
        self.setObjectName("yimmain")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("QWidget#yimmain { background: white; }")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        bar = QMenuBar()
        bar.setStyleSheet("QMenuBar { background: #ECE9D8; " + TAHOMA + " }")
        m = bar.addMenu("&Messenger")
        self.sign_act = m.addAction("Sign &In", self.toggle_sign)
        m.addSeparator()
        m.addAction("&Close", lambda: self.frame.request_close() if self.frame else None)
        v = bar.addMenu("&View")
        v.addAction("&Refresh", lambda: self.tree.fill())
        c = bar.addMenu("&Contacts")
        c.addAction("Send an &Instant Message...", self.send_im)
        c.addAction("&Add a Friend...", lambda: self._note("Your friends come from your buddy list. New buddies show "
                                                           "up here by themselves."))
        h = bar.addMenu("&Help")
        h.addAction("&About Yahoo! Messenger", self.about)
        lay.addWidget(bar)
        lay.addWidget(_Header())
        self.stack = QStackedWidget()
        lay.addWidget(self.stack, 1)
        self.stack.addWidget(self._signin_page())
        self.stack.addWidget(self._list_page())
        lay.addWidget(_Tabs())

    def _signin_page(self):
        page = QWidget()
        page.setStyleSheet("QWidget { background: #F4EFFA; } QLabel, QCheckBox { " + TAHOMA + " }"
                           "QLineEdit { background: white; border: 1px solid #9A86B8; padding: 2px; }")
        v = QVBoxLayout(page)
        v.setContentsMargins(16, 16, 16, 16)
        v.addWidget(QLabel("<b style='color:#4A0D72; font-size:13px'>Sign In</b>"))
        form = QFormLayout()
        self.id_edit = QLineEdit(yahoo_id(self.network.my_handle()))
        pw = QLineEdit("password")
        pw.setEchoMode(QLineEdit.Password)
        form.addRow("Yahoo! ID:", self.id_edit)
        form.addRow("Password:", pw)
        v.addLayout(form)
        v.addWidget(QCheckBox("Remember my ID && Password"))
        v.addWidget(QCheckBox("Automatically sign in"))
        go = QPushButton("Sign In")
        go.setStyleSheet(Skin.send_style)
        go.setFixedHeight(26)
        go.clicked.connect(self.toggle_sign)
        v.addWidget(go)
        link = QLabel("<a href='#' style='color:#0033CC'>Get a Yahoo! ID</a>")
        link.linkActivated.connect(lambda _l: self._note("You already have a Yahoo! ID."))
        v.addWidget(link)
        v.addStretch()
        return page

    def toggle_sign(self):
        if self.network.signed_in:
            self.client.sign_out()
            self.stack.setCurrentIndex(0)
            self.sign_act.setText("Sign &In")
        else:
            self.stack.setCurrentIndex(1)
            self.client.signed_in()
            self.sign_act.setText("Sign &Out")
            self.tree.fill()
            self._status_label("I'm Available")

    def _list_page(self):
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        head = QWidget()
        head.setStyleSheet("QWidget { background: #F4EFFA; border-bottom: 1px solid #C9B9E0; }")
        h = QHBoxLayout(head)
        h.setContentsMargins(6, 4, 6, 4)
        self.me = QLabel()
        self.me.setPixmap(art.pixmap("yim_online", 20))
        h.addWidget(self.me)
        self.status_btn = QPushButton()
        self.status_btn.setFlat(True)
        self.status_btn.setStyleSheet("QPushButton { text-align: left; border: none; " + TAHOMA + " color: #3A0A5A; }")
        self.status_btn.clicked.connect(self._status_menu)
        h.addWidget(self.status_btn, 1)
        v.addWidget(head)
        self.tree = BuddyTree(self.network, [("Friends", lambda b: True)],
                              {ONLINE: "yim_online", AWAY: "yim_away", BUSY: "yim_away", OFFLINE: "yim_offline"},
                              "QTreeWidget { border: none; background: white; " + TAHOMA + " font-size: 12px; }"
                              "QTreeWidget::item { padding: 2px; } QTreeWidget::item:selected { background: #7B1FA2;"
                              " color: white; }",
                              label=lambda b: b.handle + ("  (Busy)" if b.presence == BUSY else
                                                          "  (Away)" if b.presence == AWAY else ""),
                              order=lambda b: (b.presence == OFFLINE, b.handle))
        self.tree.open_buddy.connect(lambda bid: self.client.open_convo(bid))
        v.addWidget(self.tree, 1)
        return page

    def _status_label(self, word):
        self.status_btn.setText(f"{yahoo_id(self.network.my_handle())}:  {word}  ▾")
        self.me.setPixmap(art.pixmap("yim_online" if self.network.my_status == ONLINE else "yim_away", 20))

    def _status_menu(self):
        m = QMenu(self)
        for word, status in STATUSES:
            m.addAction(word, lambda w=word, s=status: (setattr(self.network, "my_status", s), self._status_label(w)))
        m.addSeparator()
        m.addAction("Sign Out", self.toggle_sign)
        m.exec(self.status_btn.mapToGlobal(self.status_btn.rect().bottomLeft()))

    def send_im(self):
        item = self.tree.currentItem() if self.network.signed_in else None
        bid = item.data(0, Qt.UserRole) if item is not None else None
        if bid:
            self.client.open_convo(bid)
        else:
            self._note("Pick a friend in your list first, then choose Send an Instant Message.")

    def about(self):
        self._note("Yahoo! Messenger\nVersion 5.0.0.1065\n\nCopyright © 2001 Yahoo! Inc. All rights reserved.")

    def _note(self, text):
        from ...explorer.dialogs import msgbox
        msgbox(self.client.desktop, "Yahoo! Messenger", text, "info", window_icon=art.icon("yim_logo", 16))


class _Header(QWidget):
    """The purple band with the Yahoo! wordmark."""

    def __init__(self):
        super().__init__()
        self.setFixedHeight(48)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        g = QLinearGradient(0, 0, 0, self.height())
        g.setColorAt(0, QColor(PURPLE))
        g.setColorAt(1, QColor(DARK))
        p.fillRect(self.rect(), g)
        mark = art.yahoo_wordmark(30, "#FFFFFF")
        p.drawPixmap(10, 6, mark)
        p.setPen(QColor(YELLOW))
        f = QFont("Arial", 9)
        f.setBold(True)
        p.setFont(f)
        p.drawText(self.rect().adjusted(12, 0, -8, -3), Qt.AlignRight | Qt.AlignBottom, "Messenger")
        p.drawPixmap(self.width() - 38, 6, art.pixmap("yim_online", 26))


class _Tabs(QWidget):
    """The tab strip along the bottom of Yahoo! Messenger 5."""

    def __init__(self):
        super().__init__()
        self.setFixedHeight(24)

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#E2D8EE"))
        p.setFont(QFont("Tahoma", 8))
        x = 4
        for i, text in enumerate(("Messenger", "Stocks", "News", "Calendar")):
            w = 56 if i else 66
            p.setPen(QColor("#9A86B8"))
            p.setBrush(QColor("white") if i == 0 else QColor("#D2C4E4"))
            p.drawRect(x, 2, w, 19)
            p.setPen(QColor("#3A0A5A"))
            p.drawText(x, 2, w, 19, Qt.AlignCenter, text)
            x += w + 2


_client = None


def client(desktop):
    global _client
    if _client is None:
        net = YIMNetwork(desktop)
        _client = Client(desktop, net, Skin(net))
    return _client


def launch(desktop):
    client(desktop).show()


def shutdown():
    if _client is not None:
        _client.shutdown()


def yim_icon():
    return art.icon("yim_logo", 32)
