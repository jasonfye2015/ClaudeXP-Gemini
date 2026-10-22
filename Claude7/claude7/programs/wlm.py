"""Windows Live Messenger 2011 - MSN Messenger's window with the 2011 face: your display picture and status at the
top, 'Share something new...', Segoe UI on white and light blue, Available / Busy / Away / Appear offline, and the
Windows Live strip along the bottom. The conversations, the contacts and their replies are ClaudeXP's MSN."""
import html

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMenuBar, QPushButton, QStyle, QToolButton, QVBoxLayout, QWidget

e = html.escape
SEGOE = "font-family: 'Segoe UI'; font-size: 12px;"
STATUSES_2011 = None            # filled by install() from the messenger's presence constants


def install(msn):
    """Dress claudexp.programs.messengers.msn as Windows Live Messenger 2011."""
    global STATUSES_2011
    from claudexp.programs.messengers import art
    from claudexp.programs.messengers.core import AWAY, BUSY, OFFLINE, ONLINE
    from claudexp.programs.messengers.ui import BuddyTree

    STATUSES_2011 = [("Available", ONLINE), ("Busy", BUSY), ("Away", AWAY), ("Appear offline", AWAY)]
    msn.STATUSES[:] = STATUSES_2011
    msn.MSNNetwork.title = "Windows Live Messenger"

    class Skin(msn.Skin):
        title = "Windows Live Messenger"
        main_size = (280, 560)
        convo_size = (520, 440)
        toast_colors = ("#FFFFFF", "#DCEBFA", "#7DA2CE", "#1E395B")
        window_style = "QWidget#convo { background: #F3F8FD; }"
        transcript_style = ("QTextBrowser { background: white; border: 1px solid #A9BEDF; " + SEGOE +
                            " padding: 6px; }")
        input_style = "QTextEdit { background: white; border: 1px solid #A9BEDF; " + SEGOE + " }"
        send_style = ("QPushButton { " + SEGOE + " font-weight: bold; color: #1E395B; background: qlineargradient("
                      "x1:0, y1:0, x2:0, y2:1, stop:0 #FFFFFF, stop:1 #DCEBFA); border: 1px solid #7DA2CE;"
                      " border-radius: 3px; } QPushButton:pressed { background: #C4DCF5; }")
        status_style = "QLabel { background: #F3F8FD; color: #555; padding: 2px 6px; " + SEGOE + " }"

        def convo_title(self, b):
            return f"{b.name}"

        def toolbar(self, conv):
            bar = QWidget()
            bar.setStyleSheet("QWidget { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFFFFF, "
                              "stop:1 #E3EEF9); border-bottom: 1px solid #A9BEDF; }")
            row = QHBoxLayout(bar)
            row.setContentsMargins(8, 3, 8, 3)
            st = conv.style()
            for text, icon in (("Photos", QStyle.SP_DirIcon), ("Files", QStyle.SP_DialogSaveButton),
                               ("Video", QStyle.SP_ComputerIcon), ("Call", QStyle.SP_MediaVolume),
                               ("Games", QStyle.SP_MediaPlay), ("Activities", QStyle.SP_FileDialogContentsView)):
                b = QToolButton()
                b.setText(text)
                b.setIcon(st.standardIcon(icon))
                b.setIconSize(QSize(20, 20))
                b.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
                b.setStyleSheet("QToolButton { border: 1px solid transparent; border-radius: 3px; background: transparent; "
                                + SEGOE + " padding: 2px 6px; } QToolButton:hover { border: 1px solid #7DA2CE; "
                                "background: #E8F0FA; }")
                b.clicked.connect(lambda _c=False, t=text: conv.status.setText(
                    f"{t} isn't available on this computer."))
                row.addWidget(b)
            row.addStretch()
            return bar

        def header(self, conv, b):
            lab = QLabel(f'<table cellspacing="0"><tr><td><b style="font-size:13px; color:#1E395B">{e(b.name)}</b>'
                         f'<br><span style="color:#6D6D6D">{e(b.handle)}</span></td></tr></table>')
            lab.setStyleSheet("QLabel { background: #F3F8FD; padding: 6px 8px; " + SEGOE + " }")
            return lab

        def format_bar(self, conv):
            lab = QLabel(" Never give out your password or credit card number in an instant message conversation.")
            lab.setStyleSheet("QLabel { background: #F3F8FD; color: #8A8A8A; padding: 2px 6px; font-family: 'Segoe UI';"
                              " font-size: 10px; }")
            return lab

        def line(self, entry, me, b):
            kind, text = entry["kind"], e(entry["text"]).replace("\n", "<br>")
            if kind == "system":
                return f'<span style="color:#808080;">{text}</span>'
            who = me if kind == "user" else b.name
            return (f'<div style="margin-top:7px;"><span style="color:#1E395B; font-weight:bold;">{e(who)}</span>'
                    f'<span style="color:#808080;"> said:</span><br>'
                    f'&nbsp;&nbsp;&nbsp;<span style="color:#1E1E1E;">{text}</span></div>')

        def received_text(self, t):
            from .. import clock
            return f"Last message received at {t:%I:%M %p} on {t.month}/{t.day}/{clock.YEAR}.".replace(" 0", " ")

        def main_window(self, client):
            return Main(client)

    class Strip(QWidget):
        """The Windows Live strip along the bottom."""

        def __init__(self):
            super().__init__()
            self.setFixedHeight(40)

        def paintEvent(self, event):
            p = QPainter(self)
            p.setRenderHint(QPainter.Antialiasing)
            g = QLinearGradient(0, 0, 0, self.height())
            g.setColorAt(0, QColor("#E8F1FA"))
            g.setColorAt(1, QColor("#C9DCF0"))
            p.fillRect(self.rect(), g)
            p.setPen(QColor("#A9BEDF"))
            p.drawLine(0, 0, self.width(), 0)
            p.drawPixmap(8, 6, art.pixmap("msn_logo", 28))
            p.setPen(QColor("#1E395B"))
            f = QFont("Segoe UI", 10)
            f.setBold(True)
            p.setFont(f)
            p.drawText(self.rect().adjusted(44, 2, -4, -18), Qt.AlignLeft | Qt.AlignVCenter, "Windows Live")
            p.setFont(QFont("Segoe UI", 8))
            p.setPen(QColor("#4C607A"))
            p.drawText(self.rect().adjusted(44, 18, -4, -2), Qt.AlignLeft | Qt.AlignVCenter,
                       "Hotmail  ·  SkyDrive  ·  Photos  ·  Profile")

    class Main(msn.MSNMain):
        def __init__(self, client):
            super().__init__(client)
            self.setStyleSheet("QWidget#msnmain { background: white; }")
            bar = self.findChild(QMenuBar)
            if bar is not None:
                bar.setStyleSheet("QMenuBar { background: #FFFFFF; " + SEGOE + " } QMenuBar::item:selected "
                                  "{ background: #CCE8FF; }")

        def _signin_page(self):
            page = QWidget()
            page.setStyleSheet("QLabel { " + SEGOE + " }")
            v = QVBoxLayout(page)
            v.addStretch()
            logo = QLabel()
            logo.setPixmap(art.pixmap("msn_logo", 96))
            logo.setAlignment(Qt.AlignCenter)
            v.addWidget(logo)
            title = QLabel("<span style='font-size:18px; color:#1E395B;'>Windows Live<sup>™</sup> Messenger</span>")
            title.setAlignment(Qt.AlignCenter)
            v.addWidget(title)
            v.addSpacing(12)
            self.signin_info = QLabel(e(self.network.my_email()))
            self.signin_info.setAlignment(Qt.AlignCenter)
            self.signin_info.setStyleSheet(SEGOE + " color: #555;")
            v.addWidget(self.signin_info)
            go = QPushButton("Sign in")
            go.setFixedSize(120, 30)
            go.setStyleSheet("QPushButton { " + SEGOE + " background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 "
                             "#FFFFFF, stop:1 #DCEBFA); border: 1px solid #7DA2CE; border-radius: 3px; color: #1E395B; }"
                             "QPushButton:hover { background: #E8F0FA; }")
            go.clicked.connect(self.toggle_sign)
            v.addSpacing(10)
            v.addWidget(go, 0, Qt.AlignCenter)
            remember = QLabel("<span style='color:#6D6D6D'>Remember me &nbsp;✓ &nbsp; Remember my password &nbsp;✓ "
                              "&nbsp; Sign me in automatically &nbsp;✓</span>")
            remember.setAlignment(Qt.AlignCenter)
            v.addWidget(remember)
            v.addStretch()
            return page

        def _list_page(self):
            page = QWidget()
            v = QVBoxLayout(page)
            v.setContentsMargins(0, 0, 0, 0)
            v.setSpacing(0)
            head = QWidget()
            head.setStyleSheet("QWidget { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFFFFF, "
                               "stop:1 #E3EEF9); border-bottom: 1px solid #A9BEDF; }")
            h = QHBoxLayout(head)
            h.setContentsMargins(8, 8, 8, 8)
            h.setSpacing(8)
            self.me_icon = QLabel()
            self.me_icon.setFixedSize(48, 48)
            self.me_icon.setStyleSheet("QLabel { background: white; border: 1px solid #A9BEDF; }")
            h.addWidget(self.me_icon)
            col = QVBoxLayout()
            col.setSpacing(2)
            self.status_btn = QPushButton()
            self.status_btn.setFlat(True)
            self.status_btn.setStyleSheet("QPushButton { text-align: left; border: none; " + SEGOE +
                                          " font-size: 13px; color: #1E395B; } QPushButton:hover { text-decoration: underline; }")
            self.status_btn.clicked.connect(self._status_menu)
            col.addWidget(self.status_btn)
            self.share = QLabel("<span style='color:#8A8A8A'>Share something new...</span>")
            self.share.setStyleSheet(SEGOE)
            col.addWidget(self.share)
            h.addLayout(col, 1)
            v.addWidget(head)
            self.tree = BuddyTree(self.network, [("Favorites ({n})", lambda b: b.presence != OFFLINE),
                                                 ("Other Contacts ({n})", lambda b: b.presence == OFFLINE)],
                                  {ONLINE: "msn_online", AWAY: "msn_away", BUSY: "msn_away", OFFLINE: "msn_offline"},
                                  "QTreeWidget { border: none; background: white; " + SEGOE + " }"
                                  "QTreeWidget::item { padding: 3px; } QTreeWidget::item:selected { background: #CCE8FF;"
                                  " color: black; }",
                                  label=lambda b: b.name + ("  (Away)" if b.presence == AWAY else
                                                            "  (Busy)" if b.presence == BUSY else ""))
            self.tree.open_buddy.connect(lambda bid: self.client.open_convo(bid))
            v.addWidget(self.tree, 1)
            foot = QLabel("<a href='im' style='color:#1E395B'>Send an instant message</a> &nbsp;·&nbsp; "
                          "<a href='mail' style='color:#1E395B'>Hotmail</a> &nbsp;·&nbsp; "
                          "<a href='fb' style='color:#1E395B'>Facebook</a>")
            foot.setStyleSheet("QLabel { background: #F3F8FD; border-top: 1px solid #A9BEDF; padding: 6px; " + SEGOE + " }")
            foot.linkActivated.connect(self._task)
            v.addWidget(foot)
            return page

        def _status_label(self):
            word = next((w for w, s in STATUSES_2011 if s == self.network.my_status), "Available")
            word = getattr(self, "_status_word", word)
            self.status_btn.setText(f"{self.network.my_handle()}  ({word}) ▾")
            self.me_icon.setPixmap(self._my_picture())

        def _my_picture(self):
            from .. import user
            from PySide6.QtGui import QPixmap
            pm = QPixmap(46, 46)
            pm.fill(QColor("white"))
            p = QPainter(pm)
            user.draw_user_picture(p, pm.rect())
            p.end()
            return pm

        def _task(self, which):
            if which == "fb":
                from claudexp.programs import navigator
                navigator.open_url(self.client.desktop, "http://www.facebook.com/")
            else:
                super()._task(which)

        def about(self):
            self._note("Windows Live Messenger\nVersion 2011 (Build 15.4.3555.0308)\n\n© 2011 Microsoft "
                       "Corporation. All rights reserved.")

        def _note(self, text):
            from ..dialogs import msgbox
            msgbox(self.client.desktop, "Windows Live Messenger", text, "info",
                   window_icon=art.icon("msn_logo", 16))

    msn.Skin = Skin
    msn.MSNMain = Main
    msn._Banner = Strip
