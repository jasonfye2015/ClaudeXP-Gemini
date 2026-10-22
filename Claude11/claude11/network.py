"""The network in 2025: always-on gigabit fibre over Wi-Fi 6E. Nothing to dial - the period programs that ask to
connect (ClaudeXP's network.connect(desktop, then=...)) are simply told they're online. The notification area shows
the Wi-Fi arcs, and its status window is Windows 11's Wi-Fi status.

Also the Windows 11 dialog body and the fixed-size dialog frame every message box and properties window is built on."""
import random
import time

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QMenu, QPushButton, QVBoxLayout, QWidget

from .wm import MicaWindow

SSID = "HomeNetwork"
SPEED = "1.2 Gbps"
DIALOG_STYLE = """
QWidget#dialog { background: #F3F3F3; }
QWidget { font-family: 'Segoe UI Variable Text', 'Segoe UI'; font-size: 12px; color: #1A1A1A; }
QPushButton { min-height: 24px; padding: 3px 14px; border: 1px solid #D0D0D0; border-radius: 4px; background: #FBFBFB; }
QPushButton:hover { background: #F6F6F6; }
QPushButton:pressed { background: #F0F0F0; color: #5C5C5C; }
QPushButton:default { background: #0067C0; color: white; border-color: #0067C0; }
QPushButton:default:hover { background: #1975C5; }
QPushButton:disabled { color: #9A9A9A; background: #F5F5F5; border-color: #E5E5E5; }
QLineEdit, QComboBox, QSpinBox, QPlainTextEdit, QTextEdit, QListWidget, QTreeWidget {
    border: 1px solid #E0E0E0; border-radius: 4px; background: white; padding: 3px 6px; }
QLineEdit, QComboBox, QSpinBox { border-bottom: 1px solid #8A8A8A; }
QLineEdit:focus, QComboBox:focus, QSpinBox:focus { border-bottom: 2px solid #0067C0; }
QGroupBox { border: 1px solid #E0E0E0; border-radius: 6px; margin-top: 10px; padding-top: 8px; background: #FBFBFB; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
QCheckBox, QRadioButton { spacing: 8px; }
QTabWidget::pane { border: 1px solid #E0E0E0; border-radius: 6px; background: white; }
QTabBar::tab { padding: 6px 14px; border: none; background: transparent; color: #5C5C5C; }
QTabBar::tab:selected { color: #1A1A1A; border-bottom: 2px solid #0067C0; }
QMenuBar { background: #F3F3F3; }
QMenuBar::item { padding: 4px 8px; border-radius: 4px; }
QMenuBar::item:selected { background: #E5E5E5; }
QMenu { background: #F9F9F9; border: 1px solid #E0E0E0; border-radius: 8px; padding: 4px; }
QMenu::item { padding: 6px 28px 6px 12px; border-radius: 4px; margin: 1px 2px; }
QMenu::item:selected { background: #EAEAEA; }
QMenu::separator { height: 1px; background: #E5E5E5; margin: 4px 8px; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: rgba(0, 0, 0, 60); border-radius: 3px; min-height: 24px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""


def network_pixmap(size=16, lit=(False, False)):
    """Windows 11's Wi-Fi arcs, all lit."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 16
    colour = QColor("#1A1A1A") if size <= 20 else QColor("#0067C0")
    pen = QPen(colour, 1.5 * s)
    pen.setCapStyle(Qt.RoundCap)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    cx, cy = 8 * s, 12 * s
    for rad in (3.5, 6.5, 9.5):
        r = rad * s
        p.drawArc(QRectF(cx - r, cy - r, 2 * r, 2 * r), 45 * 16, 90 * 16)
    p.setPen(Qt.NoPen)
    p.setBrush(colour)
    p.drawEllipse(QPointF(cx, cy + 0.5 * s), 1.5 * s, 1.5 * s)
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
    g.setColorAt(0, QColor("#F4F4F4"))
    g.setColorAt(1, QColor("#C8C8C8"))
    p.setPen(QPen(QColor("#505050"), max(1.0, s)))
    p.setBrush(g)
    p.drawRoundedRect(QRectF(3 * s, 12 * s, 26 * s, 12 * s), 4 * s, 4 * s)
    p.setPen(QPen(QColor("#303030"), max(1.0, 1.5 * s)))
    p.drawLine(QPointF(8 * s, 12 * s), QPointF(8 * s, 3 * s))
    p.drawLine(QPointF(24 * s, 12 * s), QPointF(24 * s, 3 * s))
    p.setPen(Qt.NoPen)
    for i, col in enumerate(("#30D030", "#30D030", "#4CC2FF", "#30D030")):
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
    """A Windows 11 dialog's face; on_close runs when the frame's X is clicked."""

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
    """A fixed-size dialog around body, centred on the screen; closer() runs when the X is clicked."""
    body.setFixedSize(body.sizeHint().expandedTo(body.minimumSize()))
    body.on_close = closer
    win = MicaWindow(desktop, title, body, icon or QIcon(), buttons=("close",))
    win.fit_fixed_content()
    area = desktop.work_area()
    win.move(area.center() - win.rect().center())
    win.placed = True
    return win


class Network:
    """Fibre over Wi-Fi 6E: always connected. The tray icon and status window are the only things to see."""

    def __init__(self, desktop):
        self.desktop = desktop
        self.connected = True
        self.disconnect_listeners = []
        self.kind = "wifi"
        self.since = time.monotonic()
        self.sent = random.randint(40_000_000, 300_000_000)
        self.received = random.randint(2_000_000_000, 9_000_000_000)
        self._callbacks = []
        self.tray = None
        self.ticker = QTimer()
        self.ticker.timeout.connect(self._traffic_tick)
        self.ticker.start(2500)
        QTimer.singleShot(0, self._show_tray)

    @property
    def name(self):
        return "Wi-Fi"

    @property
    def speed(self):
        return SPEED

    def _show_tray(self):
        from .tray import TrayIcon
        if self.tray is not None:
            return
        self.tray = TrayIcon(self.desktop, network_icon())
        self.tray.key = "Network"
        self.tray.setToolTip(f"{SSID}\nInternet access")
        menu = QMenu()
        menu.addAction("Network and Internet settings", self._show_status)
        menu.addAction("Diagnose network problems", lambda: self._troubleshoot())
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(lambda _r: self._show_status())
        from .tray import tray_settings, save_tray_settings
        data = tray_settings()
        if "Network" not in data["behaviour"]:
            data["behaviour"]["Network"] = "hide"            # the taskbar draws its own Wi-Fi icon in the system pill
            save_tray_settings(data)
        self.tray.show()

    def connect(self, then=None, kind=None):
        self.connected = True
        if then:
            QTimer.singleShot(0, then)

    def disconnect(self, quiet=False):
        pass                                     # fibre doesn't hang up

    def _traffic_tick(self):
        self.sent += random.randint(2000, 40000)
        self.received += random.randint(5000, 400000)

    def _duration_text(self):
        secs = int(time.monotonic() - self.since)
        return f"{secs // 3600:02d}:{(secs // 60) % 60:02d}:{secs % 60:02d}"

    def _troubleshoot(self):
        from .dialogs import msgbox
        msgbox(self.desktop, "Get help", "Windows couldn't find a problem with your connection.\n\n"
               "You are connected to the Internet.", "info")

    def _show_status(self):
        body = DialogBody()
        v = QVBoxLayout(body)
        v.setContentsMargins(16, 12, 16, 12)
        head = QLabel(f"{SSID}")
        head.setStyleSheet("font-size: 18px; font-weight: 600;")
        v.addWidget(head)
        sub = QLabel("Connected, secured")
        sub.setStyleSheet("color: #5C5C5C;")
        v.addWidget(sub)
        g = QGridLayout()
        g.setHorizontalSpacing(24)
        rows = [("Protocol:", "Wi-Fi 6E (802.11ax)"), ("Security type:", "WPA3-Personal"), ("Network band:", "6 GHz"),
                ("Network channel:", "37"), ("Link speed (Receive/Transmit):", SPEED), ("IPv4 address:", "192.168.1.24"),
                ("IPv6 connectivity:", "Internet"), ("Duration:", self._duration_text())]
        labels = {}
        for i, (k, val) in enumerate(rows):
            g.addWidget(QLabel(k), i, 0)
            lab = QLabel(val)
            labels[k] = lab
            g.addWidget(lab, i, 1, Qt.AlignRight)
        v.addLayout(g)
        act = QLabel("Data usage")
        act.setStyleSheet("font-weight: 600; margin-top: 8px;")
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
        for text in ("Properties", "Disconnect", "Get help"):
            b = QPushButton(text)
            b.setEnabled(text == "Get help")
            b.clicked.connect(self._troubleshoot)
            row.addWidget(b)
        row.addStretch()
        close = QPushButton("Close")
        row.addWidget(close)
        v.addLayout(row)
        body.setMinimumWidth(420)
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
        holder["win"] = _fixed_window(self.desktop, "Wi-Fi", body, done, network_icon())
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
    return "Wi-Fi"


def disconnect(quiet=False):
    pass


def on_disconnect(desktop, callback):
    get(desktop)._callbacks.append(callback)
