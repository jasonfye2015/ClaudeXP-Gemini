"""The notification area's icons and balloon tips, Windows 7 style.

TrayIcon has QSystemTrayIcon's interface (the parts programs use) but lives in the taskbar's notification area;
Windows 7 hides the inactive ones behind the little arrow (Notification Area Icons in the Control Panel decides
which). Balloon is the grey-and-white notification that slides up from an icon."""
import json
import time

from PySide6.QtCore import QObject, QPoint, QPointF, QRect, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPolygonF
from PySide6.QtWidgets import QSystemTrayIcon, QWidget
from shiboken6 import isValid

from .paths import DATA

SETTINGS_FILE = DATA / "tray.json"
INACTIVE_SECONDS = 60


def tray_settings():
    try:
        with open(SETTINGS_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        data = {}
    data.setdefault("behaviour", {})
    data.setdefault("seen", [])
    return data


def save_tray_settings(data):
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def behaviour(key, data=None):
    """'auto' (hide when inactive), 'show' or 'hide' for a tray icon's name."""
    return (data or tray_settings())["behaviour"].get(key, "auto")


def remember(key):
    data = tray_settings()
    if key not in data["seen"]:
        data["seen"].append(key)
        save_tray_settings(data)


class TrayIcon(QObject):
    activated = Signal(QSystemTrayIcon.ActivationReason)
    messageClicked = Signal()

    def __init__(self, desktop, icon=None, parent=None):
        super().__init__(parent)
        self.desktop = desktop
        self._icon = icon or QIcon()
        self._tooltip = ""
        self._menu = None
        self._visible = False
        self.key = None
        self.last_used = time.monotonic()
        self.destroyed.connect(lambda *_: desktop.taskbar.remove_tray_icon(self)
                               if isValid(desktop.taskbar) else None)

    def setIcon(self, icon):
        self._icon = icon
        self.desktop.taskbar.update()

    def icon(self):
        return self._icon

    def setToolTip(self, text):
        self._tooltip = text

    def toolTip(self):
        return self._tooltip

    def setContextMenu(self, menu):
        self._menu = menu

    def contextMenu(self):
        return self._menu

    def show(self):
        self._visible = True
        if self.key is None:
            self.key = (self._tooltip or "Program").split("\n")[0].split(" - ")[0].split(":")[0].strip()[:60]
            remember(self.key)
        self.last_used = time.monotonic()
        self.desktop.taskbar.add_tray_icon(self)

    def touch(self):
        self.last_used = time.monotonic()
        self.desktop.taskbar.update()

    def hide(self):
        self._visible = False
        self.desktop.taskbar.remove_tray_icon(self)
        self.desktop.balloon.dismiss(self)

    def setVisible(self, visible):
        self.show() if visible else self.hide()

    def isVisible(self):
        return self._visible

    def showMessage(self, title, message, icon=None, msecs=10000):
        if self._visible:
            self.touch()
            self.desktop.balloon.pop(self, title, message, msecs)


class Balloon(QWidget):
    """Windows 7's notification: a rounded grey box with a close button, pointing down at its icon."""
    WIDTH = 300
    TAIL = 14
    PAD = 12

    def __init__(self, desktop):
        super().__init__(desktop)
        self.desktop = desktop
        self.owner = None
        self.title = ""
        self.message = ""
        self.tail_x = 40
        self.title_h = 16
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide)
        self.hide()

    def pop(self, owner, title, message, msecs):
        from . import sound
        sound.play("balloon")
        self.owner, self.title, self.message = owner, title, message
        anchor = self.desktop.taskbar.tray_icon_center(owner)
        if anchor is None:
            anchor = QPoint(self.desktop.width() - 120, self.desktop.taskbar.y())
        title_font, body_font = self._fonts()
        text_w = self.WIDTH - 2 * self.PAD - 18
        title_h = QFontMetrics(title_font).boundingRect(QRect(0, 0, text_w, 1000), Qt.TextWordWrap, title).height()
        body_h = QFontMetrics(body_font).boundingRect(QRect(0, 0, self.WIDTH - 2 * self.PAD - 40, 1000),
                                                      Qt.TextWordWrap, message).height()
        box_h = self.PAD + max(title_h, 20) + 6 + body_h + self.PAD
        x = min(self.desktop.width() - self.WIDTH - 6, anchor.x() - self.WIDTH + 40)
        y = self.desktop.taskbar.y() - box_h - self.TAIL - 2
        self.setGeometry(max(4, x), y, self.WIDTH, box_h + self.TAIL)
        self.tail_x = anchor.x() - self.x()
        self.title_h = max(title_h, 20)
        self.show()
        self.raise_()
        self.update()
        self.timer.start(max(1000, msecs))

    def dismiss(self, owner=None):
        if owner is None or owner is self.owner:
            self.timer.stop()
            self.hide()

    @staticmethod
    def _fonts():
        title = QFont("Segoe UI", 9)
        title.setBold(True)
        return title, QFont("Segoe UI", 9)

    def mousePressEvent(self, event):
        owner = self.owner
        self.dismiss()
        if owner is not None and isValid(owner) and not self._close_rect().contains(event.position().toPoint()):
            owner.messageClicked.emit()

    def _close_rect(self):
        return QRect(self.width() - self.PAD - 14, self.PAD - 2, 16, 16)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        box = QRectF(0.5, 0.5, self.width() - 1, self.height() - self.TAIL - 1)
        path = QPainterPath()
        path.addRoundedRect(box, 6, 6)
        tx = max(24.0, min(float(self.tail_x), self.width() - 10.0))
        tail = QPainterPath()
        tail.addPolygon(QPolygonF([QPointF(tx - 16, box.bottom() - 1), QPointF(tx - 2, box.bottom() - 1),
                                   QPointF(tx - 2, self.height() - 1.0)]))
        path = path.united(tail)
        g = QLinearGradient(0, 0, 0, box.height())
        g.setColorAt(0, QColor("#FFFFFF"))
        g.setColorAt(1, QColor("#E3E7ED"))
        p.setPen(QPen(QColor("#6E7B8B"), 1))
        p.setBrush(g)
        p.drawPath(path)
        title_font, body_font = self._fonts()
        icon = self.owner.icon() if self.owner is not None and isValid(self.owner) else QIcon()
        x = self.PAD
        if not icon.isNull():
            p.drawPixmap(x, self.PAD, icon.pixmap(32, 32))
            x += 40
        p.setPen(QColor("#1E3B5A"))
        p.setFont(title_font)
        p.drawText(QRect(x, self.PAD, self.width() - x - self.PAD - 20, self.title_h), Qt.TextWordWrap, self.title)
        p.setFont(body_font)
        p.setPen(QColor("#202020"))
        body_top = self.PAD + self.title_h + 6
        p.drawText(QRect(x, body_top, self.width() - x - self.PAD, int(box.bottom()) - body_top), Qt.TextWordWrap,
                   self.message)
        c = self._close_rect()
        p.setPen(QPen(QColor("#5A6470"), 1.4))
        p.drawLine(c.x() + 4, c.y() + 4, c.right() - 3, c.bottom() - 3)
        p.drawLine(c.right() - 3, c.y() + 4, c.x() + 4, c.bottom() - 3)


def customize_notifications(desktop):
    """Control Panel > Notification Area Icons: show, hide, or only show notifications, for every icon."""
    from PySide6.QtWidgets import QComboBox, QHBoxLayout, QHeaderView, QLabel, QPushButton, QTreeWidget, \
        QTreeWidgetItem, QVBoxLayout
    from .network import DialogBody, _fixed_window
    data = tray_settings()
    current = []
    for icon in desktop.taskbar._live_tray_icons():
        if icon.key and icon.key not in [k for k, _ in current]:
            current.append((icon.key, icon.icon()))
    past = [k for k in data["seen"] if k not in [c for c, _ in current]]
    body = DialogBody()
    v = QVBoxLayout(body)
    title = QLabel("Select which icons and notifications appear on the taskbar")
    title.setStyleSheet("font-size: 15px; color: #1E3B5A;")
    v.addWidget(title)
    intro = QLabel("If you choose to hide icons and notifications, you won't be notified about changes or updates. "
                   "To view hidden icons at any time, click the arrow next to the notification area on the taskbar.")
    intro.setWordWrap(True)
    v.addWidget(intro)
    tree = QTreeWidget()
    tree.setHeaderLabels(["Icons", "Behaviors"])
    tree.setRootIsDecorated(False)
    tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
    tree.setMinimumSize(520, 260)
    combos = {}
    choices = [("show", "Show icon and notifications"), ("auto", "Only show notifications"),
               ("hide", "Hide icon and notifications")]

    def add_row(key, icon=None):
        item = QTreeWidgetItem([key, ""])
        if icon is not None:
            item.setIcon(0, icon)
        tree.addTopLevelItem(item)
        combo = QComboBox()
        for value, label in choices:
            combo.addItem(label, value)
        combo.setCurrentIndex([c[0] for c in choices].index(behaviour(key, data)))
        tree.setItemWidget(item, 1, combo)
        combos[key] = combo

    for key, icon in current:
        add_row(key, icon)
    for key in past:
        add_row(key)
    v.addWidget(tree)
    row = QHBoxLayout()
    row.addStretch()
    ok, cancel = QPushButton("OK"), QPushButton("Cancel")
    for b in (ok, cancel):
        b.setFixedSize(80, 24)
        row.addWidget(b)
    v.addLayout(row)
    holder = {}

    def close():
        if holder.get("win") is not None:
            desktop.close_window(holder.pop("win"))

    def save():
        data["behaviour"] = {k: c.currentData() for k, c in combos.items()}
        save_tray_settings(data)
        desktop.taskbar.update()
        close()

    ok.clicked.connect(save)
    cancel.clicked.connect(close)
    holder["win"] = _fixed_window(desktop, "Notification Area Icons", body, close)
    desktop.open_window(holder["win"])
    return holder["win"]
