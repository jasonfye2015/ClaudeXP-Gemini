"""MSN Messenger 4.6: the sign-in screen, 'My Status', the Online / Not Online groups, 'I want to...', and
conversation windows where '<name> says:' sits above each message. Buddies are on Hotmail (or MSN) addresses."""
import hashlib
import html

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter
from PySide6.QtWidgets import (QCheckBox, QHBoxLayout, QLabel, QMenu, QMenuBar, QPushButton, QStackedWidget,
                               QStyle, QToolButton, QVBoxLayout, QWidget)

from . import art
from .client import Client
from .core import AWAY, BUSY, OFFLINE, ONLINE, Network, _slug
from .ui import BuddyTree

e = html.escape
TAHOMA = "font-family: Tahoma, Verdana; font-size: 11px;"
STATUSES = [("Online", ONLINE), ("Busy", BUSY), ("Be Right Back", AWAY), ("Away", AWAY), ("On The Phone", BUSY),
            ("Out To Lunch", AWAY)]


class MSNNetwork(Network):
    key, title = "msn", "MSN Messenger"

    def handle_for(self, contact):
        own = self.sections.get(contact.id, {}).get("email")
        if own:
            return own
        domain = "msn.com" if int(hashlib.md5(contact.id.encode()).hexdigest(), 16) % 5 == 0 else "hotmail.com"
        return f"{_slug(contact.screen_name)}@{domain}"

    def my_email(self):
        return f"{_slug(self.my_handle())}@hotmail.com"


class Skin:
    title = "MSN Messenger"
    main_size = (250, 470)
    convo_size = (470, 400)
    send_label, send_size, send_sound = "Send", QSize(64, 64), False
    message_sound = signin_sound = "MSN_Messenger_Notification_Sound.mp3"
    login_sound = None
    toast_colors = ("#FFFFFF", "#C9DCF7", "#5A7EC0", "#0A246A")
    window_style = "QWidget#convo { background: #EEF3FB; }"
    transcript_style = ("QTextBrowser { background: white; border: 1px solid #7F9DB9; " + TAHOMA +
                        " font-size: 12px; padding: 4px; }")
    input_style = "QTextEdit { background: white; border: 1px solid #7F9DB9; font-family: Tahoma; font-size: 12px; }"
    send_style = ("QPushButton { font-family: Tahoma; font-size: 11px; font-weight: bold; background: qlineargradient("
                  "x1:0, y1:0, x2:0, y2:1, stop:0 #FFFFFF, stop:1 #C9DCF7); border: 1px solid #5A7EC0; }"
                  "QPushButton:pressed { background: #A9C4EE; }")
    status_style = "QLabel { background: #EEF3FB; color: #444; padding: 2px 6px; " + TAHOMA + " }"

    def __init__(self, network):
        self.network = network

    def app_icon(self):
        return art.icon("msn_logo", 32)

    def toast_logo(self):
        return art.pixmap("msn_logo", 22)

    def display(self, b):
        return b.name

    def convo_title(self, b):
        return f"{b.name} - Conversation"

    def toolbar(self, conv):
        bar = QWidget()
        bar.setStyleSheet("QWidget { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFFFFF, "
                          "stop:1 #D7E4F7); border-bottom: 1px solid #A9BEDF; }")
        row = QHBoxLayout(bar)
        row.setContentsMargins(6, 2, 6, 2)
        st = conv.style()
        for text, icon in (("Invite", QStyle.SP_FileDialogNewFolder), ("Send Files", QStyle.SP_DialogSaveButton),
                           ("Voice", QStyle.SP_MediaVolume), ("Video", QStyle.SP_ComputerIcon),
                           ("Block", QStyle.SP_DialogCancelButton)):
            b = QToolButton()
            b.setText(text)
            b.setIcon(st.standardIcon(icon))
            b.setIconSize(QSize(22, 22))
            b.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            b.setStyleSheet("QToolButton { border: none; background: transparent; " + TAHOMA + " }"
                            "QToolButton:hover { border: 1px solid #7F9DB9; background: #FFF7D6; }")
            b.clicked.connect(lambda _c=False, t=text: conv.status.setText(
                f"{t} isn't available in this version of MSN Messenger."))
            row.addWidget(b)
        row.addStretch()
        logo = QLabel()
        logo.setPixmap(art.pixmap("msn_logo", 34))
        row.addWidget(logo)
        return bar

    def header(self, conv, b):
        lab = QLabel(f"&nbsp;To: <b>{e(b.name)}</b> &lt;{e(b.handle)}&gt;")
        lab.setStyleSheet("QLabel { background: #EEF3FB; color: #0A246A; padding: 5px 4px; " + TAHOMA + " }")
        return lab

    def format_bar(self, conv):
        lab = QLabel("&nbsp;Never give out your password or credit card number in an instant message conversation.")
        lab.setStyleSheet("QLabel { background: #EEF3FB; color: #7A7A7A; padding: 2px 4px; font-family: Tahoma; "
                          "font-size: 10px; }")
        return lab

    def line(self, entry, me, b):
        kind, text = entry["kind"], e(entry["text"]).replace("\n", "<br>")
        if kind == "system":
            return f'<span style="color:#808080;">{text}</span>'
        who = me if kind == "user" else b.name
        return (f'<div style="margin-top:6px;"><span style="color:#808080;">{e(who)} says:</span><br>'
                f'&nbsp;&nbsp;&nbsp;&nbsp;<span style="color:#000000;">{text}</span></div>')

    def typing_text(self, b):
        return f"{b.name} is typing a message."

    def received_text(self, t):
        return f"Last message received at {t:%I:%M %p} on {t.month}/{t.day}/2001.".replace(" 0", " ")

    def main_window(self, client):
        return MSNMain(client)


class MSNMain(QWidget):
    def __init__(self, client):
        super().__init__()
        self.client, self.network = client, client.network
        self.frame = None
        self.process_image = "msnmsgr.exe"             # for Task Manager
        self.setObjectName("msnmain")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("QWidget#msnmain { background: white; }")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        bar = QMenuBar()
        bar.setStyleSheet("QMenuBar { background: #ECE9D8; " + TAHOMA + " }")
        f = bar.addMenu("&File")
        self.sign_act = f.addAction("Sign &In", self.toggle_sign)
        f.addSeparator()
        f.addAction("&Close", lambda: self.frame.request_close() if self.frame else None)
        a = bar.addMenu("&Actions")
        a.addAction("Send an &Instant Message...", self.send_im)
        a.addAction("&Add a Contact...", self.add_contact)
        t = bar.addMenu("&Tools")
        t.addAction("&Options...", lambda: self._note("Options aren't available in this version."))
        h = bar.addMenu("&Help")
        h.addAction("&About MSN Messenger", self.about)
        lay.addWidget(bar)
        self.stack = QStackedWidget()
        lay.addWidget(self.stack, 1)
        self.stack.addWidget(self._signin_page())
        self.stack.addWidget(self._list_page())
        lay.addWidget(_Banner())

    # ---- sign in -------------------------------------------------------------------------------------------
    def _signin_page(self):
        page = QWidget()
        v = QVBoxLayout(page)
        v.addStretch()
        logo = QLabel()
        logo.setPixmap(art.pixmap("msn_logo", 110))
        logo.setAlignment(Qt.AlignCenter)
        v.addWidget(logo)
        title = QLabel("<span style='font-size:15px; color:#0A246A;'><b>MSN</b> Messenger</span>")
        title.setAlignment(Qt.AlignCenter)
        v.addWidget(title)
        link = QLabel("<a href='#' style='color:#0033CC;'>Click here to sign in</a>")
        link.setAlignment(Qt.AlignCenter)
        link.setStyleSheet(TAHOMA + " font-size: 12px;")
        link.linkActivated.connect(lambda _l: self.toggle_sign())
        v.addSpacing(10)
        v.addWidget(link)
        self.signin_info = QLabel(f"{e(self.network.my_email())}")
        self.signin_info.setAlignment(Qt.AlignCenter)
        self.signin_info.setStyleSheet(TAHOMA + " color: #555;")
        v.addWidget(self.signin_info)
        auto = QCheckBox("Sign me in automatically")
        auto.setStyleSheet(TAHOMA)
        v.addWidget(auto, 0, Qt.AlignCenter)
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
            self._status_label()

    # ---- the list --------------------------------------------------------------------------------------------
    def _list_page(self):
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        head = QWidget()
        head.setStyleSheet("QWidget { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFFFFF, "
                           "stop:1 #D7E4F7); }")
        h = QHBoxLayout(head)
        h.setContentsMargins(6, 6, 6, 6)
        me = QLabel()
        me.setPixmap(art.pixmap("msn_online", 28))
        self.me_icon = me
        h.addWidget(me)
        self.status_btn = QPushButton()
        self.status_btn.setFlat(True)
        self.status_btn.setStyleSheet("QPushButton { text-align: left; border: none; " + TAHOMA + " color: #0A246A; }"
                                      "QPushButton:hover { text-decoration: underline; }")
        self.status_btn.clicked.connect(self._status_menu)
        h.addWidget(self.status_btn, 1)
        v.addWidget(head)
        self.tree = BuddyTree(self.network, [("Online ({n})", lambda b: b.presence != OFFLINE),
                                             ("Not Online ({n})", lambda b: b.presence == OFFLINE)],
                              {ONLINE: "msn_online", AWAY: "msn_away", BUSY: "msn_away", OFFLINE: "msn_offline"},
                              "QTreeWidget { border: none; background: white; " + TAHOMA + " font-size: 12px; }"
                              "QTreeWidget::item { padding: 2px; } QTreeWidget::item:selected { background: #316AC5;"
                              " color: white; }",
                              label=lambda b: b.name + ("  (Away)" if b.presence == AWAY else ""))
        self.tree.open_buddy.connect(lambda bid: self.client.open_convo(bid))
        v.addWidget(self.tree, 1)
        tasks = QLabel("<b style='color:#0A246A'>I want to...</b><br>"
                       "&nbsp;<a href='im' style='color:#0033CC'>Send an Instant Message</a><br>"
                       "&nbsp;<a href='add' style='color:#0033CC'>Add a Contact</a><br>"
                       "&nbsp;<a href='mail' style='color:#0033CC'>Go to my e-mail inbox</a>")
        tasks.setStyleSheet("QLabel { background: #EEF3FB; border-top: 1px solid #A9BEDF; padding: 6px; " + TAHOMA + " }")
        tasks.linkActivated.connect(self._task)
        v.addWidget(tasks)
        return page

    def _status_label(self):
        word = next((w for w, s in STATUSES if s == self.network.my_status), "Online")
        word = getattr(self, "_status_word", word)
        self.status_btn.setText(f"My Status:  {self.network.my_handle()} ({word})  ▾")
        self.me_icon.setPixmap(art.pixmap("msn_online" if self.network.my_status == ONLINE else "msn_away", 28))

    def _status_menu(self):
        m = QMenu(self)
        for word, status in STATUSES:
            m.addAction(word, lambda w=word, s=status: self._set_status(w, s))
        m.addSeparator()
        m.addAction("Sign Out", self.toggle_sign)
        m.exec(self.status_btn.mapToGlobal(self.status_btn.rect().bottomLeft()))

    def _set_status(self, word, status):
        self.network.my_status = status
        self._status_word = word
        self._status_label()

    def _task(self, which):
        if which == "im":
            self.send_im()
        elif which == "add":
            self.add_contact()
        else:
            from .. import navigator
            navigator.open_url(self.client.desktop, "http://home.netscape.com/webmail/")

    def send_im(self):
        item = self.tree.currentItem() if self.network.signed_in else None
        bid = item.data(0, Qt.UserRole) if item is not None else None
        if bid:
            self.client.open_convo(bid)
        else:
            self._note("Pick someone in your contact list first, then choose Send an Instant Message.")

    def add_contact(self):
        self._note("Your contacts come from your buddy list. New buddies show up here by themselves.")

    def about(self):
        self._note("MSN Messenger Service\nVersion 4.6 (4.6.0083)\n\nCopyright © 1999-2001 Microsoft "
                   "Corporation. All rights reserved.")

    def _note(self, text):
        from ...explorer.dialogs import msgbox
        msgbox(self.client.desktop, "MSN Messenger", text, "info", window_icon=art.icon("msn_logo", 16))


class _Banner(QWidget):
    """The ad strip along the bottom of the window."""

    def __init__(self):
        super().__init__()
        self.setFixedHeight(46)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        g = QLinearGradient(0, 0, self.width(), 0)
        g.setColorAt(0, QColor("#0A246A"))
        g.setColorAt(1, QColor("#3A6FD8"))
        p.fillRect(self.rect(), g)
        p.drawPixmap(6, 7, art.pixmap("msn_logo", 32))
        p.setPen(QColor("#FFFFFF"))
        f = QFont("Tahoma", 9)
        f.setBold(True)
        p.setFont(f)
        p.drawText(self.rect().adjusted(44, 4, -4, -22), Qt.AlignLeft | Qt.AlignVCenter, "Get your FREE e-mail")
        p.setFont(QFont("Tahoma", 8))
        p.setPen(QColor("#FFD24A"))
        p.drawText(self.rect().adjusted(44, 22, -4, -4), Qt.AlignLeft | Qt.AlignVCenter, "at Hotmail.com - Sign up now!")


_client = None


def client(desktop):
    global _client
    if _client is None:
        net = MSNNetwork(desktop)
        _client = Client(desktop, net, Skin(net))
    return _client


def launch(desktop):
    client(desktop).show()


def shutdown():
    if _client is not None:
        _client.shutdown()


def msn_icon():
    return art.icon("msn_logo", 32)
