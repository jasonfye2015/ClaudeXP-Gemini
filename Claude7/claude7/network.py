"""The network in 2011: always-on broadband over Wi-Fi. Nothing to dial - the period programs that ask to connect
(ClaudeXP's network.connect(desktop, then=...)) are simply told they're online. The notification area shows the
five-bar wireless icon, and its status window is Windows 7's 'Wireless Network Connection Status'.

Also the Windows 7 dialog body and the fixed-size dialog frame every message box and properties window is built on."""
import random
import time

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QMenu, QPushButton, QVBoxLayout, QWidget

from .wm import AeroWindow

SSID = "HomeNetwork"
SPEED = "54.0 Mbps"
DIALOG_STYLE = """
QWidget#dialog { background: #F0F0F0; }
QWidget { font-family: 'Segoe UI'; font-size: 12px; color: #000000; }
QPushButton { min-height: 22px; padding: 2px 12px; border: 1px solid #707070; border-radius: 3px;
              background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #F2F2F2, stop:0.5 #EBEBEB, stop:0.51 #DDDDDD, stop:1 #CFCFCF); }
QPushButton:hover { border-color: #3C7FB1; background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #EAF6FD, stop:0.5 #D9F0FC, stop:0.51 #BEE6FD, stop:1 #A7D9F5); }
QPushButton:pressed { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #C2E4F6, stop:1 #A9DAF5); }
QPushButton:default { border-color: #3C7FB1; }
QLineEdit, QComboBox, QSpinBox, QPlainTextEdit, QTextEdit, QListWidget, QTreeWidget { border: 1px solid #ABADB3; background: white; padding: 2px; }
QGroupBox { border: 1px solid #DCDCDC; border-radius: 4px; margin-top: 10px; padding-top: 6px; }
QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 3px; }
QCheckBox, QRadioButton { spacing: 6px; }
QTabWidget::pane { border: 1px solid #D9D9D9; background: white; }
QTabBar::tab { padding: 4px 10px; border: 1px solid #D9D9D9; border-bottom: none; background: #F0F0F0; }
QTabBar::tab:selected { background: white; }
QMenuBar { background: #F0F0F0; }
QMenuBar::item:selected { background: #CCE8FF; border: 1px solid #99D1FF; }
QMenu { background: #F0F0F0; border: 1px solid #979797; }
QMenu::item { padding: 4px 24px 4px 28px; }
QMenu::item:selected { background: #CCE8FF; border: 1px solid #99D1FF; }
QMenu::separator { height: 1px; background: #D7D7D7; margin: 3px 2px; }
"""


def network_pixmap(size=16, lit=(False, False)):
    """The Windows 7 wireless signal bars (five, all lit)."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 16
    p.setPen(Qt.NoPen)
    for i in range(5):
        h = (4 + i * 2.4) * s
        p.setBrush(QColor("#FFFFFF") if size <= 20 else QColor("#5A8DC8"))
        p.drawRect(QRectF((1 + i * 3) * s, (14 * s) - h, 2.2 * s, h))
    p.end()
    return pm


def dsl_pixmap(size=32):
    """A router with its lights on (the 'always on' connection icon)."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 32
    g = QLinearGradient(0, 8 * s, 0, 24 * s)
    g.setColorAt(0, QColor("#E8E8E8"))
    g.setColorAt(1, QColor("#A0A0A0"))
    p.setPen(QPen(QColor("#404040"), max(1.0, s)))
    p.setBrush(g)
    p.drawRoundedRect(QRectF(3 * s, 12 * s, 26 * s, 12 * s), 3 * s, 3 * s)
    p.setPen(QPen(QColor("#303030"), max(1.0, 1.5 * s)))
    p.drawLine(QPointF(8 * s, 12 * s), QPointF(8 * s, 3 * s))
    p.drawLine(QPointF(24 * s, 12 * s), QPointF(24 * s, 3 * s))
    p.setPen(Qt.NoPen)
    for i, col in enumerate(("#30D030", "#30D030", "#F0C020", "#30D030")):
        p.setBrush(QColor(col))
        p.drawEllipse(QPointF((9 + i * 5) * s, 18 * s), 1.6 * s, 1.6 * s)
    p.end()
    return pm


def dsl_icon():
    return QIcon(dsl_pixmap(32))


def network_icon():
    icon = QIcon()
    for sz in (16, 32):
        icon.addPixmap(network_pixmap(sz))
    return icon


class DialogBody(QWidget):
    """A Windows 7 dialog's face; on_close runs when the frame's X is clicked."""

    def __init__(self):
        super().__init__()
        self.on_close = None
        self.setObjectName("dialog")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.restyle()

    def restyle(self):
        self.setStyleSheet(DIALOG_STYLE)

    def closeEvent(self, event):
        event.accept()
        if self.on_close:
            self.on_close()


def _dialog_body():
    return DialogBody()


def _fixed_window(desktop, title, body, closer, icon=None):
    """A fixed-size Aero dialog around body, centred on the screen; closer() runs when the X is clicked."""
    body.setFixedSize(body.sizeHint().expandedTo(body.minimumSize()))
    body.on_close = closer
    win = AeroWindow(desktop, title, body, icon or QIcon(), buttons=("close",))
    win.fit_fixed_content()
    area = desktop.work_area()
    win.move(area.center() - win.rect().center())
    win.placed = True
    return win


class Network:
    """Broadband: always connected. The tray icon and status window are the only things to see."""

    def __init__(self, desktop):
        self.desktop = desktop
        self.connected = True
        self.disconnect_listeners = []
        self.kind = "wifi"
        self.since = time.monotonic()
        self.sent = random.randint(2_000_000, 9_000_000)
        self.received = random.randint(40_000_000, 200_000_000)
        self._callbacks = []
        self.tray = None
        self.ticker = QTimer()
        self.ticker.timeout.connect(self._traffic_tick)
        self.ticker.start(2500)
        QTimer.singleShot(0, self._show_tray)

    @property
    def name(self):
        return "Wireless Network Connection"

    @property
    def speed(self):
        return SPEED

    def _show_tray(self):
        from .tray import TrayIcon
        if self.tray is not None:
            return
        self.tray = TrayIcon(self.desktop, network_icon())
        self.tray.setToolTip(f"{SSID}\nInternet access")
        menu = QMenu()
        menu.addAction("Open Network and Sharing Center", self._show_status)
        menu.addAction("Troubleshoot problems", lambda: self._troubleshoot())
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(lambda _r: self._show_status())
        self.tray.show()

    def connect(self, then=None, kind=None):
        self.connected = True
        if then:
            QTimer.singleShot(0, then)

    def disconnect(self, quiet=False):
        pass                                     # broadband doesn't hang up

    def _traffic_tick(self):
        self.sent += random.randint(200, 4000)
        self.received += random.randint(500, 40000)

    def _duration_text(self):
        secs = int(time.monotonic() - self.since)
        return f"{secs // 3600:02d}:{(secs // 60) % 60:02d}:{secs % 60:02d}"

    def _troubleshoot(self):
        from .dialogs import msgbox
        msgbox(self.desktop, "Windows Network Diagnostics", "Troubleshooting couldn't identify the problem.\n\n"
               "You are connected to the Internet.", "info")

    def _show_status(self):
        body = DialogBody()
        v = QVBoxLayout(body)
        v.setContentsMargins(12, 10, 12, 10)
        head = QLabel("Connection")
        head.setStyleSheet("font-weight: bold;")
        v.addWidget(head)
        g = QGridLayout()
        g.setHorizontalSpacing(24)
        rows = [("IPv4 Connectivity:", "Internet"), ("IPv6 Connectivity:", "No Internet access"),
                ("Media State:", "Enabled"), ("SSID:", SSID), ("Duration:", self._duration_text()),
                ("Speed:", SPEED), ("Signal Quality:", "Excellent")]
        labels = {}
        for i, (k, val) in enumerate(rows):
            g.addWidget(QLabel(k), i, 0)
            lab = QLabel(val)
            labels[k] = lab
            g.addWidget(lab, i, 1, Qt.AlignRight)
        v.addLayout(g)
        act = QLabel("Activity")
        act.setStyleSheet("font-weight: bold; margin-top: 8px;")
        v.addWidget(act)
        g2 = QGridLayout()
        g2.addWidget(QLabel("Sent"), 0, 1, Qt.AlignCenter)
        g2.addWidget(QLabel("Received"), 0, 2, Qt.AlignCenter)
        g2.addWidget(QLabel("Bytes:"), 1, 0)
        sent, recv = QLabel(f"{self.sent:,}"), QLabel(f"{self.received:,}")
        g2.addWidget(sent, 1, 1, Qt.AlignRight)
        g2.addWidget(recv, 1, 2, Qt.AlignRight)
        v.addLayout(g2)
        row = QHBoxLayout()
        for text in ("Properties", "Disable", "Diagnose"):
            b = QPushButton(text)
            b.setEnabled(text == "Diagnose")
            b.clicked.connect(self._troubleshoot)
            row.addWidget(b)
        row.addStretch()
        close = QPushButton("Close")
        row.addWidget(close)
        v.addLayout(row)
        body.setMinimumWidth(360)
        holder = {}
        timer = QTimer(body)

        def refresh():
            labels["Duration:"].setText(self._duration_text())
            sent.setText(f"{self.sent:,}")
            recv.setText(f"{self.received:,}")

        timer.timeout.connect(refresh)
        timer.start(1000)

        def done():
            timer.stop()
            if holder.get("win") is not None:
                self.desktop.close_window(holder.pop("win"))

        close.clicked.connect(done)
        holder["win"] = _fixed_window(self.desktop, "Wireless Network Connection Status", body, done, network_icon())
        self.desktop.open_window(holder["win"])


_network = None


def get(desktop):
    global _network
    if _network is None:
        _network = Network(desktop)
    return _network


def connect(desktop, then=None):
    get(desktop).connect(then)


def is_connected():
    return True


def is_broadband():
    return True


def connection_name():
    return "Wireless Network Connection"


def disconnect(quiet=False):
    pass


def on_disconnect(desktop, callback):
    get(desktop)._callbacks.append(callback)
