"""A messenger built from a description: ICQ, Skype, Trillian and KIK are each a Theme (colours, words, icons,
how lines and screen names look) handed to ThemedSkin + ThemedMain. MSN and Yahoo! have their own hand-made
windows (msn.py, yim.py); everything else about them is the same Client and Network."""
import hashlib
import html
from dataclasses import dataclass, field

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter
from PySide6.QtWidgets import (QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMenu, QMenuBar, QPushButton,
                               QStackedWidget, QToolButton, QVBoxLayout, QWidget)

from . import art
from .client import Client
from .core import AWAY, BUSY, OFFLINE, Network
from .ui import BuddyTree

e = html.escape


def number(text, digits):
    """A stable made-up number for a name (ICQ UINs)."""
    n = int(hashlib.md5(text.encode()).hexdigest(), 16)
    return str(10 ** (digits - 1) + n % (9 * 10 ** (digits - 1)))


@dataclass
class Theme:
    key: str                         # 'icq'
    title: str                       # 'ICQ'
    version: str                     # for About
    icon: str                        # art name for the program icon
    status_icons: dict               # presence -> art name
    handle: object                   # (contact, sections) -> screen name
    my_handle: object                # (my name) -> my screen name
    statuses: list                   # [(word, presence)]
    groups: list                     # [(title, test)]
    head_top: str = "#FFFFFF"        # header gradient
    head_bottom: str = "#DDDDDD"
    head_text: str = "#000000"
    accent: str = "#316AC5"          # buttons, selection
    page: str = "#FFFFFF"            # window background
    font: str = "Tahoma"
    subtitle: str = ""
    signin_title: str = "Sign In"
    signin_field: str = "Screen name:"
    signin_button: str = "Sign In"
    buttons: list = field(default_factory=list)      # decorative toolbar words in the conversation window
    footer: list = field(default_factory=list)       # decorative buttons along the bottom of the main window
    me_color: str = "#0000CC"
    them_color: str = "#CC0000"
    line_style: str = "name"         # 'name' (name: text), 'stamp' (name (time): text), 'bubble' (chat bubbles)
    main_size: tuple = (240, 470)
    convo_size: tuple = (460, 400)
    message_sound: str = "notify"      # a file in assets/sounds, or a Windows sound event
    signin_sound: str = "ding"
    signoff_sound: str = ""
    login_sound: str = ""            # when you sign in yourself
    button_sounds: dict = field(default_factory=dict)    # toolbar word -> sound (Skype's Call rings)
    toast: tuple = ("#FFFFFF", "#DDDDDD", "#808080", "#000000")
    label: object = None             # (buddy) -> list text; default: screen name
    tag: object = None               # (buddy) -> text shown after the name, e.g. the network on Trillian


class ThemedNetwork(Network):
    def __init__(self, theme, parent=None):
        self.theme = theme
        self.key, self.title = theme.key, theme.title
        super().__init__(parent)

    def handle_for(self, contact):
        return self.theme.handle(contact, self.sections.get(contact.id, {}))


class ThemedSkin:
    send_sound = False

    def __init__(self, network):
        self.network = network
        self.t = t = network.theme
        self.title = t.title
        self.main_size, self.convo_size = t.main_size, t.convo_size
        self.message_sound, self.signin_sound = t.message_sound, t.signin_sound
        self.signoff_sound, self.login_sound = t.signoff_sound, t.login_sound
        self.toast_colors = t.toast
        self.send_label = "Send"
        self.send_size = QSize(64, 28)
        f = f"font-family: {t.font}; font-size: 11px;"
        self.window_style = f"QWidget#convo {{ background: {t.page}; }}"
        bubble = t.line_style == "bubble"
        self.transcript_style = (f"QTextBrowser {{ background: {'#EDEDED' if bubble else 'white'}; border: 1px solid "
                                 f"#A0A0A0; font-family: {t.font}; font-size: 12px; padding: 4px; }}")
        self.input_style = (f"QTextEdit {{ background: white; border: 1px solid #A0A0A0; font-family: {t.font}; "
                            "font-size: 12px; }")
        self.send_style = (f"QPushButton {{ {f} font-weight: bold; color: white; background: {t.accent}; "
                           f"border: 1px solid {QColor(t.accent).darker(140).name()}; border-radius: 3px; }}"
                           f"QPushButton:pressed {{ background: {QColor(t.accent).darker(130).name()}; }}")
        self.status_style = f"QLabel {{ background: {t.page}; color: #444; padding: 2px 6px; {f} }}"

    def app_icon(self):
        return art.icon(self.t.icon, 32)

    def toast_logo(self):
        return art.pixmap(self.t.icon, 22)

    def display(self, b):
        return b.handle if self.t.label is None else self.t.label(b)

    def convo_title(self, b):
        return f"{self.display(b)} - {self.t.title}"

    def toolbar(self, conv):
        bar = _Band(self.t, self.t.title, small=True)
        row = QHBoxLayout(bar)
        row.setContentsMargins(46, 2, 8, 2)
        for text in self.t.buttons:
            b = QToolButton()
            b.setText(text)
            b.setStyleSheet(f"QToolButton {{ border: none; background: transparent; color: {self.t.head_text}; "
                            f"font-family: {self.t.font}; font-size: 11px; }} QToolButton:hover {{ text-decoration: "
                            "underline; }")
            b.clicked.connect(lambda _c=False, w=text: self._button(conv, w))
            row.addWidget(b)
        row.addStretch()
        return bar

    def _button(self, conv, word):
        ring = self.t.button_sounds.get(word)
        if ring:
            from .client import play
            play(ring)
            conv.status.setText(f"{word}: no answer.")
        else:
            conv.status.setText(f"{word} isn't available right now.")

    def header(self, conv, b):
        tag = f" &nbsp;<span style='color:#808080'>({e(self.t.tag(b))})</span>" if self.t.tag else ""
        lab = QLabel(f"&nbsp;<b>{e(self.display(b))}</b>{tag}")
        lab.setStyleSheet(f"QLabel {{ background: {self.t.page}; padding: 5px 4px; font-family: {self.t.font}; "
                          "font-size: 11px; }")
        return lab

    def format_bar(self, conv):
        return None

    def line(self, entry, me, b):
        kind, text = entry["kind"], e(entry["text"]).replace("\n", "<br>")
        if kind == "system":
            return f'<span style="color:#808080;"><i>{text}</i></span>'
        mine = kind == "user"
        who = self.t.my_handle(me) if mine else self.display(b)
        color = self.t.me_color if mine else self.t.them_color
        if self.t.line_style == "bubble":
            align, bg, fg = ("right", self.t.me_color, "#FFFFFF") if mine else ("left", "#FFFFFF", "#222222")
            return (f'<table width="100%" cellspacing="0" cellpadding="0"><tr><td align="{align}">'
                    f'<table cellpadding="7" style="background:{bg};"><tr><td style="color:{fg};">{text}</td></tr>'
                    "</table></td></tr></table>")
        if self.t.line_style == "stamp":
            from datetime import datetime
            try:
                ts = datetime.fromisoformat(entry["ts"]).strftime("%I:%M %p").lstrip("0")
            except (ValueError, KeyError):
                ts = ""
            return f'<b style="color:{color};">{e(who)}</b> <span style="color:#808080;">({ts})</span>:<br>{text}'
        return f'<b style="color:{color};">{e(who)}</b>: {text}'

    def typing_text(self, b):
        return f"{self.display(b)} is typing..."

    def received_text(self, t):
        return f"Last message received at {t:%I:%M %p}".replace(" 0", " ")

    def main_window(self, client):
        return ThemedMain(client, self.t)


class _Band(QWidget):
    """The coloured header band with the program's logo and name."""

    def __init__(self, theme, title, subtitle="", small=False):
        super().__init__()
        self.t, self.title, self.subtitle, self.small = theme, title, subtitle, small
        self.setFixedHeight(34 if small else 52)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        g = QLinearGradient(0, 0, 0, self.height())
        g.setColorAt(0, QColor(self.t.head_top))
        g.setColorAt(1, QColor(self.t.head_bottom))
        p.fillRect(self.rect(), g)
        size = self.height() - 8
        p.drawPixmap(6, 4, art.pixmap(self.t.icon, size))
        if self.small:
            return
        p.setPen(QColor(self.t.head_text))
        f = QFont(self.t.font, 14)
        f.setBold(True)
        p.setFont(f)
        p.drawText(self.rect().adjusted(size + 14, 4, -6, -18), Qt.AlignLeft | Qt.AlignVCenter, self.title)
        p.setFont(QFont(self.t.font, 8))
        p.drawText(self.rect().adjusted(size + 14, 26, -6, -4), Qt.AlignLeft | Qt.AlignVCenter, self.subtitle)


class ThemedMain(QWidget):
    def __init__(self, client, theme):
        super().__init__()
        self.client, self.network, self.t = client, client.network, theme
        self.frame = None
        self.process_image = f"{theme.key}.exe"
        self.setObjectName("themedmain")
        self.setAttribute(Qt.WA_StyledBackground, True)
        f = f"font-family: {theme.font}; font-size: 11px;"
        self.f = f
        self.setStyleSheet(f"QWidget#themedmain {{ background: {theme.page}; }}")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        bar = QMenuBar()
        bar.setStyleSheet(f"QMenuBar {{ background: #ECE9D8; {f} }}")
        m = bar.addMenu(f"&{theme.title.split()[0]}")
        self.sign_act = m.addAction("Sign &In", self.toggle_sign)
        m.addSeparator()
        m.addAction("&Close", lambda: self.frame.request_close() if self.frame else None)
        h = bar.addMenu("&Help")
        h.addAction(f"&About {theme.title}", self.about)
        lay.addWidget(bar)
        lay.addWidget(_Band(theme, theme.title, theme.subtitle))
        self.stack = QStackedWidget()
        lay.addWidget(self.stack, 1)
        self.stack.addWidget(self._signin_page())
        self.stack.addWidget(self._list_page())
        if theme.footer:
            foot = QWidget()
            foot.setStyleSheet(f"QWidget {{ background: {theme.head_bottom}; }}")
            row = QHBoxLayout(foot)
            row.setContentsMargins(4, 3, 4, 3)
            for word in theme.footer:
                b = QPushButton(word)
                b.setStyleSheet(f"QPushButton {{ {f} color: {theme.head_text}; background: transparent; border: 1px "
                                f"solid {QColor(theme.head_bottom).darker(130).name()}; padding: 2px 6px; }}")
                b.clicked.connect(lambda _c=False, w=word: self._note(f"{w} isn't available in this version."))
                row.addWidget(b)
            lay.addWidget(foot)

    def _signin_page(self):
        page = QWidget()
        page.setStyleSheet(f"QLabel {{ {self.f} }} QLineEdit {{ background: white; border: 1px solid #A0A0A0; "
                           "padding: 2px; }")
        v = QVBoxLayout(page)
        v.setContentsMargins(16, 20, 16, 16)
        logo = QLabel()
        logo.setPixmap(art.pixmap(self.t.icon, 72))
        logo.setAlignment(Qt.AlignCenter)
        v.addWidget(logo)
        v.addWidget(QLabel(f"<b style='font-size:13px'>{e(self.t.signin_title)}</b>"))
        form = QFormLayout()
        form.addRow(self.t.signin_field, QLineEdit(self.t.my_handle(self.network.my_handle())))
        pw = QLineEdit("********")
        pw.setEchoMode(QLineEdit.Password)
        form.addRow("Password:", pw)
        v.addLayout(form)
        go = QPushButton(self.t.signin_button)
        go.setFixedHeight(28)
        go.setStyleSheet(ThemedSkin(self.network).send_style)
        go.clicked.connect(self.toggle_sign)
        v.addWidget(go)
        v.addStretch()
        return page

    def _list_page(self):
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        head = QWidget()
        head.setStyleSheet(f"QWidget {{ background: {self.t.page}; border-bottom: 1px solid #C0C0C0; }}")
        h = QHBoxLayout(head)
        h.setContentsMargins(6, 4, 6, 4)
        self.me = QLabel()
        h.addWidget(self.me)
        self.status_btn = QPushButton()
        self.status_btn.setFlat(True)
        self.status_btn.setStyleSheet(f"QPushButton {{ text-align: left; border: none; {self.f} }}")
        self.status_btn.clicked.connect(self._status_menu)
        h.addWidget(self.status_btn, 1)
        v.addWidget(head)
        t = self.t
        label = (lambda b: (t.label(b) if t.label else b.handle) + (f"  ({t.tag(b)})" if t.tag else "") +
                 ("  (Away)" if b.presence == AWAY else "  (Busy)" if b.presence == BUSY else ""))
        sel = QColor(t.accent).name()
        self.tree = BuddyTree(self.network, t.groups, t.status_icons,
                              f"QTreeWidget {{ border: none; background: white; {self.f} font-size: 12px; }}"
                              f"QTreeWidget::item {{ padding: 2px; }} QTreeWidget::item:selected {{ background: {sel};"
                              " color: white; }", label=label,
                              order=lambda b: (b.presence == OFFLINE, label(b).lower()))
        self.tree.open_buddy.connect(lambda bid: self.client.open_convo(bid))
        v.addWidget(self.tree, 1)
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
            self._status_label(self.t.statuses[0][0])

    def _status_label(self, word):
        self.status_btn.setText(f"{self.t.my_handle(self.network.my_handle())}:  {word}  ▾")
        self.me.setPixmap(art.pixmap(self.t.status_icons[self.network.my_status if self.network.my_status != BUSY
                                                         else AWAY], 20))

    def _status_menu(self):
        m = QMenu(self)
        for word, status in self.t.statuses:
            m.addAction(word, lambda w=word, s=status: (setattr(self.network, "my_status", s), self._status_label(w)))
        m.addSeparator()
        m.addAction("Sign Out", self.toggle_sign)
        m.exec(self.status_btn.mapToGlobal(self.status_btn.rect().bottomLeft()))

    def about(self):
        self._note(f"{self.t.title}\nVersion {self.t.version}")

    def _note(self, text):
        from ...explorer.dialogs import msgbox
        msgbox(self.client.desktop, self.t.title, text, "info", window_icon=art.icon(self.t.icon, 16))


def make(theme):
    """-> (launch, shutdown, icon) for a themed messenger."""
    holder = {}

    def client(desktop):
        if "c" not in holder:
            net = ThemedNetwork(theme, desktop)
            holder["c"] = Client(desktop, net, ThemedSkin(net))
        return holder["c"]

    def launch(desktop):
        client(desktop).show()

    def shutdown():
        if "c" in holder:
            holder["c"].shutdown()

    def icon():
        return art.icon(theme.icon, 32)
    return launch, shutdown, icon, client
