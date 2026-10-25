"""MSN Hotmail in the notification area: a little envelope that turns yellow, with a count, while new mail is
waiting. Click it to open Hotmail in Internet Explorer; right-click for Outlook Express too. New mail pops a
balloon here ('You've got mail!' is still the dial-up's voice). Also the art for the desktop's MSN Hotmail link."""
from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

HOTMAIL_URL = "http://www.hotmail.com/"
POLL_MS = 4000          # reading mail in Hotmail happens on the web server's thread: look now and then


def hotmail_pixmap(size=32, new=False, count=0):
    """An envelope on Hotmail's blue square; yellow with a red count when mail is waiting."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 32
    if not new:
        g = QLinearGradient(0, 0, 0, size)
        g.setColorAt(0, QColor("#4C7FD8"))
        g.setColorAt(1, QColor("#0B3A99"))
        p.setPen(QPen(QColor("#082A70"), max(1.0, s)))
        p.setBrush(g)
        p.drawRoundedRect(QRectF(1.5 * s, 1.5 * s, 29 * s, 29 * s), 5 * s, 5 * s)
    env = QRectF(5 * s, 9 * s, 22 * s, 15 * s) if not new else QRectF(2 * s, 7 * s, 27 * s, 19 * s)
    p.setPen(QPen(QColor("#7A5A10") if new else QColor("#2A3A60"), max(1.0, 1.2 * s)))
    p.setBrush(QColor("#FFE36A") if new else QColor("#FFFFFF"))
    p.drawRect(env)
    p.drawPolyline(QPolygonF([env.topLeft(), QPointF(env.center().x(), env.top() + env.height() * 0.6),
                              env.topRight()]))
    if not new:                                       # the orange dot of 'msn.'
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#FF9900"))
        p.drawEllipse(QRectF(22 * s, 21 * s, 6 * s, 6 * s))
    elif count:
        text = str(count) if count < 100 else "99+"
        r = QRectF(size - 17 * s, size - 17 * s, 16 * s, 16 * s)
        p.setPen(QPen(QColor("white"), max(1.0, s)))
        p.setBrush(QColor("#D42020"))
        p.drawEllipse(r)
        f = QFont("Tahoma")
        f.setBold(True)
        f.setPixelSize(max(6, int((9 if len(text) == 1 else 7) * s)))
        p.setFont(f)
        p.setPen(QColor("white"))
        p.drawText(r, Qt.AlignCenter, text)
    p.end()
    return pm


def hotmail_icon(size=32):
    icon = QIcon()
    for sz in (16, 32, 48):
        icon.addPixmap(hotmail_pixmap(sz))
    return icon


def open_hotmail(desktop):
    from .programs import navigator
    navigator.open_url(desktop, HOTMAIL_URL)


MAIL_NAME = "MSN Hotmail"           # the later computers set their own (Windows Live Hotmail, Outlook.com)


class MailTray:
    def __init__(self, desktop):
        from .tray import TrayIcon
        self.desktop = desktop
        self.count = -1
        self.tray = TrayIcon(desktop, QIcon(hotmail_pixmap(16)), desktop)
        self.tray.activated.connect(self._activated)
        self.tray.messageClicked.connect(lambda: open_hotmail(desktop))
        menu = QMenu(desktop)
        menu.addAction("Open MSN &Hotmail", lambda: open_hotmail(desktop))
        menu.addAction("Open &Outlook Express", self._outlook)
        menu.addSeparator()
        menu.addAction("Hide this icon until new mail arrives", self._hide)
        self.tray.setContextMenu(menu)
        self.hidden_until_new = False
        self.timer = QTimer(desktop)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(POLL_MS)
        from . import life
        sim = life.get()
        if sim is not None:
            sim.mail_arrived.connect(self.refresh)
        QTimer.singleShot(0, self.refresh)

    def _unread(self):
        from . import life
        sim = life.get()
        return len(sim.mailbox.unread()) if sim is not None else 0

    def refresh(self):
        n = self._unread()
        if n == self.count:
            return
        grew = n > self.count >= 0
        self.count = n
        if n:
            self.tray.setIcon(QIcon(hotmail_pixmap(16, new=True, count=n)))
            self.tray.setToolTip(f"{MAIL_NAME}\nYou have {n} new e-mail message{'s' if n != 1 else ''}")
            if grew:
                self.hidden_until_new = False
        else:
            self.tray.setIcon(QIcon(hotmail_pixmap(16)))
            self.tray.setToolTip(f"{MAIL_NAME}\nNo new e-mail")
        self.tray.setVisible(not self.hidden_until_new)

    def notify(self, title, text):
        """A new-mail balloon from this icon."""
        self.refresh()
        if not self.tray.isVisible():
            self.hidden_until_new = False
            self.tray.show()
        self.tray.showMessage(title, text, None, 8000)

    def _activated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            open_hotmail(self.desktop)

    def _outlook(self):
        from .programs import launch
        launch(self.desktop, "outlook")

    def _hide(self):
        self.hidden_until_new = True
        self.tray.hide()


_tray = None


def install(desktop):
    global _tray
    _tray = MailTray(desktop)
    return _tray


def get():
    return _tray
