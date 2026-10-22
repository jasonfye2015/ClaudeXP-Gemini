"""The notification area's icons and the toast notifications, Windows 11 style.

TrayIcon has QSystemTrayIcon's interface (the parts programs use) but lives in the taskbar's notification area;
Windows 11 hides the inactive ones behind the little chevron (Settings > Taskbar decides which). Balloon keeps the
period programs' name for the notification itself: on Windows 11 it is a toast, a rounded card that slides in at
the bottom right, and it is kept in the notification center afterwards."""
import json
import time

from PySide6.QtCore import QObject, QPoint, QRect, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QIcon, QPainter, QPen
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
    """A Windows 11 toast: app name on top, the title and message, a close button; it slides in bottom right."""
    WIDTH = 364
    PAD = 16

    def __init__(self, desktop):
        super().__init__(desktop)
        self.desktop = desktop
        self.owner = None
        self.title = ""
        self.message = ""
        self.app_name = ""
        self.title_h = 18
        self.hover_close = False
        self.setMouseTracking(True)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide)
        self.slide = QTimer(self)
        self.slide.timeout.connect(self._slide_tick)
        self._target_x = 0
        self.hide()

    def pop(self, owner, title, message, msecs):
        from . import clock, sound
        sound.play("notify")
        self.owner, self.title, self.message = owner, title, message
        self.app_name = (getattr(owner, "key", None) or "Windows") if owner is not None else "Windows"
        title_font, body_font = self._fonts()
        text_w = self.WIDTH - 2 * self.PAD - 44
        title_h = QFontMetrics(title_font).boundingRect(QRect(0, 0, text_w, 1000), Qt.TextWordWrap, title).height()
        body_h = QFontMetrics(body_font).boundingRect(QRect(0, 0, text_w, 1000), Qt.TextWordWrap, message).height()
        self.title_h = max(title_h, 18)
        box_h = self.PAD + 22 + 8 + self.title_h + 4 + body_h + self.PAD
        y = self.desktop.taskbar.y() - box_h - 12
        self._target_x = self.desktop.width() - self.WIDTH - 12
        self.setGeometry(self.desktop.width(), y, self.WIDTH, box_h)
        self.show()
        self.raise_()
        self.slide.start(16)
        self.timer.start(max(1500, msecs))
        try:
            icon = owner.icon() if owner is not None and isValid(owner) else QIcon()
            self.desktop.notifications.insert(0, {"app": self.app_name, "title": title, "message": message,
                                                  "icon": icon, "time": clock.time_text()})
            del self.desktop.notifications[20:]
        except Exception:
            pass

    def _slide_tick(self):
        x = self.x() + max(8, int((self._target_x - self.x()) * 0.35))
        if x >= self._target_x - 1:
            x = self._target_x
            self.slide.stop()
        self.move(x, self.y())

    def dismiss(self, owner=None):
        if owner is None or owner is self.owner:
            self.timer.stop()
            self.slide.stop()
            self.hide()

    @staticmethod
    def _fonts():
        from .style import font
        return font(13, QFont.DemiBold), font(12)

    def _close_rect(self):
        return QRect(self.width() - self.PAD - 20, self.PAD - 2, 22, 22)

    def mouseMoveEvent(self, event):
        hot = self._close_rect().contains(event.position().toPoint())
        if hot != self.hover_close:
            self.hover_close = hot
            self.update()

    def mousePressEvent(self, event):
        owner = self.owner
        on_close = self._close_rect().contains(event.position().toPoint())
        self.dismiss()
        if owner is not None and isValid(owner) and not on_close:
            owner.messageClicked.emit()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        box = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
        p.setPen(QPen(QColor(0, 0, 0, 40), 1))
        p.setBrush(QColor(249, 249, 249, 248))
        p.drawRoundedRect(box, 8, 8)
        title_font, body_font = self._fonts()
        icon = self.owner.icon() if self.owner is not None and isValid(self.owner) else QIcon()
        from .style import font
        p.setFont(font(12))
        x = self.PAD
        if not icon.isNull():
            p.drawPixmap(x, self.PAD, icon.pixmap(16, 16))
            x += 24
        p.setPen(QColor("#5C5C5C"))
        p.drawText(QRect(x, self.PAD - 2, self.width() - x - 60, 20), Qt.AlignVCenter | Qt.AlignLeft, self.app_name)
        c = self._close_rect()
        if self.hover_close:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(0, 0, 0, 18))
            p.drawRoundedRect(QRectF(c), 4, 4)
        p.setPen(QPen(QColor("#1A1A1A"), 1.2))
        p.drawLine(c.x() + 7, c.y() + 7, c.right() - 6, c.bottom() - 6)
        p.drawLine(c.right() - 6, c.y() + 7, c.x() + 7, c.bottom() - 6)
        y = self.PAD + 22 + 8
        x = self.PAD
        if not icon.isNull():
            p.drawPixmap(x, y + 2, icon.pixmap(32, 32))
            x += 44
        text_w = self.width() - x - self.PAD
        p.setFont(title_font)
        p.setPen(QColor("#1A1A1A"))
        p.drawText(QRect(x, y, text_w, self.title_h), Qt.TextWordWrap, self.title)
        p.setFont(body_font)
        p.setPen(QColor("#5C5C5C"))
        p.drawText(QRect(x, y + self.title_h + 4, text_w, self.height() - y - self.title_h - 4 - self.PAD),
                   Qt.TextWordWrap, self.message)


def customize_notifications(desktop):
    """Settings > Personalization > Taskbar > Other system tray icons: which icons stay on the taskbar."""
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
    title = QLabel("Other system tray icons")
    title.setStyleSheet("font-size: 20px; font-weight: 600;")
    v.addWidget(title)
    intro = QLabel("Choose which icons appear on the taskbar. The rest stay in the hidden icon menu, behind the "
                   "little arrow next to the system tray.")
    intro.setWordWrap(True)
    v.addWidget(intro)
    tree = QTreeWidget()
    tree.setHeaderLabels(["Icons", "Behavior"])
    tree.setRootIsDecorated(False)
    tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
    tree.setMinimumSize(520, 260)
    combos = {}
    choices = [("show", "Always show"), ("auto", "Show when active"), ("hide", "Hide icon and notifications")]

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
    ok, cancel = QPushButton("Save"), QPushButton("Cancel")
    for b in (ok, cancel):
        b.setFixedSize(90, 30)
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
    holder["win"] = _fixed_window(desktop, "System tray icons", body, close)
    desktop.open_window(holder["win"])
    return holder["win"]
