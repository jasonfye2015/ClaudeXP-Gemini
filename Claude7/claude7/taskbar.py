"""The Windows 7 taskbar: the Start orb, pinned programs and the open windows as big glass buttons with thumbnail
previews, the notification area with its hidden-icons arrow, the clock, and the Show desktop sliver at the end."""
import json
import time

from PySide6.QtCore import QEvent, QPoint, QPointF, QRect, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import QCalendarWidget, QFrame, QGridLayout, QLabel, QMenu, QPushButton, QToolTip, \
    QVBoxLayout, QWidget
from shiboken6 import isValid

from . import clock, sound
from .paths import DATA, pixmap

TASKBAR_H = 40
ORB_W = 54
ITEM_H = 32
ITEM_MAX_W = 162
ITEM_ICON_W = 44
TRAY_SLOT = 24
CLOCK_W = 78
SHOW_DESKTOP_W = 12
CHEVRON_W = 18
FLASHES = 7
PINNED_FILE = DATA / "taskbar.json"
DEFAULT_PINNED = ["iexplore", "mycomputer", "wmp"]


def _settings():
    try:
        return json.loads(PINNED_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _save_settings(data):
    PINNED_FILE.parent.mkdir(parents=True, exist_ok=True)
    PINNED_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def pinned():
    return list(_settings().get("pinned", DEFAULT_PINNED))


def set_pinned(keys):
    data = _settings()
    data["pinned"] = list(keys)
    _save_settings(data)


def flag_pixmap(size=16):
    """Action Center's little white flag."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 16
    p.setPen(QPen(QColor("#FFFFFF"), 1.6 * s))
    p.drawLine(QPointF(3 * s, 1.5 * s), QPointF(3 * s, 14.5 * s))
    p.setPen(QPen(QColor("#E8E8E8"), 0.8 * s))
    p.setBrush(QColor("#FFFFFF"))
    p.drawPolygon(QPolygonF([QPointF(3.6 * s, 2 * s), QPointF(13 * s, 2 * s), QPointF(10.5 * s, 5 * s),
                             QPointF(13 * s, 8 * s), QPointF(3.6 * s, 8 * s)]))
    p.end()
    return pm


class Thumbnail(QWidget):
    """The preview that pops up above a window's button."""

    def __init__(self, desktop):
        super().__init__(desktop)
        self.desktop = desktop
        self.win = None
        self.hide()
        self.setMouseTracking(True)

    def show_for(self, win, button_rect):
        if not isValid(win):
            return
        self.win = win
        self.resize(206, 170)
        bar = self.desktop.taskbar
        x = bar.x() + button_rect.center().x() - self.width() // 2
        x = max(0, min(x, self.desktop.width() - self.width()))
        self.move(x, bar.y() - self.height() - 2)
        self.show()
        self.raise_()
        self.update()

    def mousePressEvent(self, event):
        if self.win is None or not isValid(self.win):
            self.hide()
            return
        if self._close_rect().contains(event.position().toPoint()):
            self.win.request_close()
            self.hide()
            return
        self.hide()
        self.desktop.activate(self.win)

    def leaveEvent(self, event):
        QTimer.singleShot(250, self._maybe_hide)

    def _maybe_hide(self):
        if not self.underMouse() and not self.desktop.taskbar.underMouse():
            self.hide()

    def _close_rect(self):
        return QRect(self.width() - 26, 6, 18, 18)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        from . import display
        tint = QColor(display.get().aero_color()).darker(160)
        tint.setAlpha(220)
        r = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
        p.setPen(QPen(QColor(0, 0, 0, 160), 1))
        p.setBrush(tint)
        p.drawRoundedRect(r, 5, 5)
        p.setPen(QPen(QColor(255, 255, 255, 90), 1))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(r.adjusted(1, 1, -1, -1), 4, 4)
        win = self.win
        if win is None or not isValid(win):
            return
        f = QFont("Segoe UI")
        f.setPixelSize(12)
        p.setFont(f)
        p.setPen(QColor("white"))
        x = 10
        if not win.icon.isNull():
            p.drawPixmap(x, 8, win.icon.pixmap(16, 16))
            x += 20
        p.drawText(QRect(x, 6, self.width() - x - 30, 20), Qt.AlignVCenter | Qt.AlignLeft,
                   p.fontMetrics().elidedText(win.title, Qt.ElideRight, self.width() - x - 34))
        c = self._close_rect()
        p.setPen(QPen(QColor(255, 255, 255, 200), 1.6))
        p.drawLine(c.x() + 5, c.y() + 5, c.right() - 4, c.bottom() - 4)
        p.drawLine(c.right() - 4, c.y() + 5, c.x() + 5, c.bottom() - 4)
        shot = win.grab() if win.isVisible() else QPixmap()
        box = QRect(10, 32, self.width() - 20, self.height() - 42)
        if shot.isNull():
            p.fillRect(box, QColor(0, 0, 0, 80))
            return
        shot = shot.scaled(box.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        p.drawPixmap(box.x() + (box.width() - shot.width()) // 2, box.y() + (box.height() - shot.height()) // 2, shot)


class Taskbar(QWidget):
    def __init__(self, desktop):
        super().__init__(desktop)
        self.desktop = desktop
        self.tray_icons = []
        self.flash_on = False
        self.setFixedHeight(TASKBAR_H)
        self.clock = QTimer(self)
        self.clock.timeout.connect(self.update)
        self.clock.start(1000)
        self.flasher = QTimer(self)
        self.flasher.timeout.connect(self._flash_tick)
        self.expanded = False
        self.hover = None
        self.pressed = None
        self.hover_since = 0.0
        self.thumb = Thumbnail(desktop)
        self.thumb_timer = QTimer(self)
        self.thumb_timer.setSingleShot(True)
        self.thumb_timer.timeout.connect(self._show_thumbnail)
        self.peek_timer = QTimer(self)
        self.peek_timer.setSingleShot(True)
        self.peek_timer.timeout.connect(lambda: self.desktop.peek(True))
        self._cpl_cache = (0.0, {})
        self.orb = pixmap("orb.bmp")
        self.start_down = False
        self.setMouseTracking(True)

    # ---- settings from Taskbar and Start Menu Properties ----
    def _setting(self, key, default):
        stamp, data = self._cpl_cache
        if time.monotonic() - stamp > 2:
            try:
                data = json.loads((DATA / "cpl.json").read_text(encoding="utf-8"))
            except (OSError, ValueError):
                data = {}
            self._cpl_cache = (time.monotonic(), data)
        return data.get(key, default)

    # ---- tray icons ----
    def add_tray_icon(self, icon):
        if icon not in self.tray_icons:
            self.tray_icons.append(icon)
            self.update()

    def remove_tray_icon(self, icon):
        if icon in self.tray_icons:
            self.tray_icons.remove(icon)
            self.update()

    def _live_tray_icons(self):
        return [i for i in self.tray_icons if isValid(i)]

    def _hidden(self, icon, data, now):
        from .tray import INACTIVE_SECONDS, behaviour
        mode = behaviour(icon.key, data) if icon.key else "auto"
        if mode == "show" or (self.desktop.balloon.isVisible() and self.desktop.balloon.owner is icon):
            return False
        if mode == "hide":
            return True
        return now - icon.last_used > INACTIVE_SECONDS

    def _tray_split(self):
        """(icons on show, the hidden ones)."""
        from .tray import tray_settings
        icons = self._live_tray_icons()
        if not icons:
            return [], []
        now = time.monotonic()
        data = tray_settings() if not hasattr(self, "_tray_data") or now - self._tray_data[0] > 2 else \
            self._tray_data[1]
        self._tray_data = (now, data)
        hidden = [i for i in icons if self._hidden(i, data, now)]
        return [i for i in icons if i not in hidden], hidden

    def _shown_tray_icons(self):
        return self._tray_split()[0]

    def tray_icon_rects(self):
        tray = self.tray_rect()
        y = (TASKBAR_H - 16) // 2
        x0 = tray.left() + 6 + (CHEVRON_W if self._tray_split()[1] else 0)
        return [(icon, QRect(x0 + i * TRAY_SLOT, y, 16, 16)) for i, icon in enumerate(self._shown_tray_icons())]

    def chevron_rect(self):
        if not self._tray_split()[1]:
            return QRect()
        tray = self.tray_rect()
        return QRect(tray.left() + 2, (TASKBAR_H - 20) // 2, 16, 20)

    def tray_icon_center(self, icon):
        for ic, rect in self.tray_icon_rects():
            if ic is icon:
                return self.mapToParent(rect.center())
        return self.mapToParent(self.chevron_rect().center()) if self.chevron_rect().isValid() else None

    def _tray_icon_at(self, pos):
        for icon, rect in self.tray_icon_rects():
            if rect.contains(pos):
                return icon
        return None

    # ---- flashing ----
    def start_flashing(self):
        if not self.flasher.isActive():
            self.flash_on = True
            self.flasher.start(500)

    def _flash_tick(self):
        self.flash_on = not self.flash_on
        live = False
        for win in self.desktop.task_order:
            if win.flashing:
                win.flash_ticks += 1
                if win.flash_ticks < FLASHES * 2:
                    live = True
        if not live:
            self.flasher.stop()
            self.flash_on = True
        self.update()

    # ---- geometry ----
    def start_rect(self):
        return QRect(0, 0, ORB_W, TASKBAR_H)

    def _system_tray_w(self):
        return 3 * TRAY_SLOT + 6              # the volume, network and Action Center icons Windows always shows

    def tray_rect(self):
        shown = len(self._shown_tray_icons())
        w = 6 + (CHEVRON_W if self._tray_split()[1] else 0) + shown * TRAY_SLOT + self._system_tray_w()
        right = self.width() - SHOW_DESKTOP_W - CLOCK_W
        return QRect(right - w, 0, w, TASKBAR_H)

    def system_icon_rects(self):
        """The icons Windows draws itself: (name, rect) for 'volume', 'network', 'flag'."""
        tray = self.tray_rect()
        x = tray.right() - self._system_tray_w() + 8
        y = (TASKBAR_H - 16) // 2
        return [("flag", QRect(x, y, 16, 16)), ("network", QRect(x + TRAY_SLOT, y, 16, 16)),
                ("volume", QRect(x + 2 * TRAY_SLOT, y, 16, 16))]

    def clock_rect(self):
        return QRect(self.width() - SHOW_DESKTOP_W - CLOCK_W, 0, CLOCK_W, TASKBAR_H)

    def show_desktop_rect(self):
        return QRect(self.width() - SHOW_DESKTOP_W, 0, SHOW_DESKTOP_W, TASKBAR_H)

    def speaker_rect(self):
        return dict(self.system_icon_rects())["volume"]

    def items(self):
        """What sits between the orb and the tray: ("pinned", key) and ("win", window) in taskbar order."""
        out = []
        wins = [w for w in self.desktop.task_order if isValid(w)]
        used = set()
        for key in pinned():
            mine = [w for w in wins if getattr(w, "program", None) == key]
            if mine:
                for w in mine:
                    out.append(("win", w))
                    used.add(w)
            else:
                out.append(("pinned", key))
        for w in wins:
            if w not in used:
                out.append(("win", w))
        return out

    def button_rects(self):
        """[(rect, kind, payload)] for every item on the taskbar."""
        items = self.items()
        if not items:
            return []
        avail = self.tray_rect().left() - ORB_W - 8
        per = min(ITEM_MAX_W, max(ITEM_ICON_W, avail // len(items)))
        labels = per >= 100
        out = []
        x = ORB_W + 4
        y = (TASKBAR_H - ITEM_H) // 2
        for kind, payload in items:
            w = ITEM_ICON_W if (kind == "pinned" or not labels) else per
            out.append((QRect(x, y, w, ITEM_H), kind, payload))
            x += w + 2
        return out

    def _item_at(self, pos):
        for rect, kind, payload in self.button_rects():
            if rect.contains(pos):
                return rect, kind, payload
        return None

    # ---- events ----
    def event(self, event):
        if event.type() == QEvent.ToolTip:
            pos = event.pos()
            icon = self._tray_icon_at(pos)
            text = ""
            if icon is not None:
                text = icon.toolTip()
            elif self.show_desktop_rect().contains(pos):
                text = "Show desktop"
            elif self.clock_rect().contains(pos):
                text = clock.long_date_text()
            elif self.start_rect().contains(pos):
                text = "Start"
            else:
                for name, rect in self.system_icon_rects():
                    if rect.contains(pos):
                        text = {"flag": "No current issues detected", "network": "Internet access",
                                "volume": "Speakers: " + ("Muted" if sound.is_muted() else
                                                          f"{int(_master() * 100)}%")}[name]
                hit = self._item_at(pos)
                if hit and hit[1] == "pinned":
                    from claudexp import programs
                    text = programs.get(hit[2]).name
            if text:
                QToolTip.showText(event.globalPos(), text, self)
            else:
                QToolTip.hideText()
            return True
        return super().event(event)

    def mousePressEvent(self, event):
        pos = event.position().toPoint()
        self.thumb.hide()
        if self.start_rect().contains(pos):
            if event.button() == Qt.LeftButton:
                self.desktop.toggle_start_menu()
            return
        self.desktop.hide_start_menu()
        if event.button() == Qt.LeftButton:
            if self.show_desktop_rect().contains(pos):
                self._show_desktop()
                return
            if self.clock_rect().contains(pos):
                self._calendar_popup()
                return
            if self.chevron_rect().contains(pos):
                self._hidden_popup()
                return
            for name, rect in self.system_icon_rects():
                if rect.contains(pos):
                    {"flag": self._action_center, "network": self._network_status, "volume": self._volume_popup}[name]()
                    return
            icon = self._tray_icon_at(pos)
            if icon is not None:
                icon.touch()
                from PySide6.QtWidgets import QSystemTrayIcon
                icon.activated.emit(QSystemTrayIcon.Trigger)
                return
            hit = self._item_at(pos)
            if hit:
                rect, kind, payload = hit
                if kind == "pinned":
                    from claudexp import programs
                    sound.play("navigate")
                    programs.launch(self.desktop, payload)
                else:
                    self.desktop.taskbar_clicked(payload)
                self.update()
        elif event.button() == Qt.RightButton:
            gp = event.globalPosition().toPoint()
            icon = self._tray_icon_at(pos)
            if icon is not None and icon.contextMenu() is not None:
                icon.touch()
                icon.contextMenu().popup(gp)
                return
            for name, rect in self.system_icon_rects():
                if rect.contains(pos):
                    self._system_icon_menu(name, gp)
                    return
            hit = self._item_at(pos)
            if hit:
                self._item_menu(hit, gp)
            else:
                self._context_menu(gp, on_clock=self.clock_rect().contains(pos))
        elif event.button() == Qt.MiddleButton:
            hit = self._item_at(pos)
            if hit and hit[1] == "win" and hit[2].program:
                from claudexp import programs
                programs.launch(self.desktop, hit[2].program)

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()
        over_sliver = self.show_desktop_rect().contains(pos)
        if over_sliver and not self.desktop.peeking and not self.peek_timer.isActive():
            self.peek_timer.start(600)
        elif not over_sliver:
            self.peek_timer.stop()
            if self.desktop.peeking:
                self.desktop.peek(False)
        hit = self._item_at(pos)
        key = (hit[1], id(hit[2])) if hit else None
        if key != self.hover:
            self.hover = key
            self.update()
            if hit and hit[1] == "win":
                self._hover_hit = hit
                self.thumb_timer.start(450)
            else:
                self.thumb_timer.stop()
                QTimer.singleShot(200, lambda: self.thumb.hide() if not self.thumb.underMouse() else None)

    def leaveEvent(self, event):
        self.hover = None
        self.thumb_timer.stop()
        self.peek_timer.stop()
        if self.desktop.peeking:
            self.desktop.peek(False)
        QTimer.singleShot(250, lambda: self.thumb.hide() if not self.thumb.underMouse() else None)
        self.update()

    def _show_thumbnail(self):
        hit = getattr(self, "_hover_hit", None)
        if hit and self.hover == (hit[1], id(hit[2])) and isValid(hit[2]):
            self.thumb.show_for(hit[2], hit[0])

    # ---- menus and popups ----
    def _item_menu(self, hit, gp):
        from claudexp import programs
        rect, kind, payload = hit
        menu = QMenu(self)
        menu.setStyleSheet(_menu_css())
        key = payload if kind == "pinned" else getattr(payload, "program", None)
        if key:
            try:
                prog = programs.get(key)
                menu.addAction(prog.icon(), prog.name, lambda: programs.launch(self.desktop, key))
                menu.addSeparator()
                if key in pinned():
                    menu.addAction("Unpin this program from taskbar", lambda: self._pin(key, False))
                else:
                    menu.addAction("Pin this program to taskbar", lambda: self._pin(key, True))
            except StopIteration:
                pass
        if kind == "win":
            menu.addAction("Close window", payload.request_close)
        menu.popup(gp)

    def _pin(self, key, on):
        keys = pinned()
        if on and key not in keys:
            keys.append(key)
        elif not on and key in keys:
            keys.remove(key)
        set_pinned(keys)
        self.update()

    def _system_icon_menu(self, name, gp):
        menu = QMenu(self)
        menu.setStyleSheet(_menu_css())
        if name == "volume":
            from .volume import open_volume_control
            menu.addAction("Open Volume Mixer", lambda: open_volume_control(self.desktop))
            menu.addAction("Playback devices", lambda: open_volume_control(self.desktop))
            menu.addSeparator()
            menu.addAction("Sounds", lambda: self._volume_popup())
        elif name == "network":
            from . import network
            menu.addAction("Open Network and Sharing Center", lambda: network.get(self.desktop)._show_status())
            menu.addAction("Troubleshoot problems", lambda: network.get(self.desktop)._troubleshoot())
        else:
            menu.addAction("Open Action Center", self._action_center)
            menu.addAction("Troubleshoot a problem", self._action_center)
            menu.addAction("Open Windows Update", lambda: __import__("claudexp.programs", fromlist=["launch"])
                           .launch(self.desktop, "winupdate"))
        menu.popup(gp)

    def _volume_popup(self):
        from .volume import VolumePopup
        pop = VolumePopup(self)
        r = self.speaker_rect()
        pop.show_at(self.mapToGlobal(QPoint(r.center().x(), r.top())))
        pop.destroyed.connect(self.update)

    def _network_status(self):
        from . import network
        network.get(self.desktop)._show_status()

    def _action_center(self):
        from .dialogs import msgbox
        msgbox(self.desktop, "Action Center", "No current issues detected.\n\nWindows Update: up to date.\n"
               "Virus protection: ClaudeShield AntiVirus is on.\nBackup: Windows Backup has not been set up.", "info")

    def _calendar_popup(self):
        frame = QFrame(None, Qt.Popup)
        frame.setStyleSheet("QFrame { background: #F0F0F0; border: 1px solid #7E7E7E; } QLabel { border: none; "
                            "font-family: 'Segoe UI'; } QCalendarWidget { border: none; }")
        v = QVBoxLayout(frame)
        v.setContentsMargins(10, 8, 10, 8)
        big = QLabel(clock.time_text())
        big.setStyleSheet("font-size: 22px; color: #1E3B5A;")
        big.setAlignment(Qt.AlignHCenter)
        v.addWidget(big)
        day = QLabel(clock.long_date_text())
        day.setAlignment(Qt.AlignHCenter)
        v.addWidget(day)
        cal = QCalendarWidget()
        cal.setGridVisible(False)
        now = clock.now()
        from PySide6.QtCore import QDate
        cal.setSelectedDate(QDate(now.year, now.month, now.day))
        cal.setFixedSize(270, 190)
        v.addWidget(cal)
        link = QLabel("Change date and time settings...")
        link.setStyleSheet("color: #0066CC; text-decoration: underline;")
        link.setCursor(Qt.PointingHandCursor)

        def settings(_e):
            frame.close()
            try:
                from claudexp.cpl_extra import date_and_time
                date_and_time(self.desktop)
            except Exception:
                pass
        link.mousePressEvent = settings
        v.addWidget(link)
        frame.adjustSize()
        r = self.clock_rect()
        gp = self.mapToGlobal(QPoint(r.center().x(), r.top()))
        frame.move(gp.x() - frame.width() // 2 - 60, gp.y() - frame.height() - 6)
        frame.show()

    def _hidden_popup(self):
        """The hidden icons' panel above the arrow."""
        from PySide6.QtWidgets import QSystemTrayIcon
        shown, hidden = self._tray_split()
        frame = QFrame(None, Qt.Popup)
        frame.setStyleSheet("QFrame { background: #F0F0F0; border: 1px solid #7E7E7E; } QPushButton { border: none; "
                            "background: transparent; } QPushButton:hover { background: #DDE8F5; } "
                            "QLabel { border: none; color: #0066CC; text-decoration: underline; font-family: 'Segoe UI'; }")
        v = QVBoxLayout(frame)
        grid = QGridLayout()
        for i, icon in enumerate(hidden):
            b = QPushButton()
            b.setFixedSize(28, 28)
            b.setIcon(icon.icon())
            b.setToolTip(icon.toolTip())

            def click(_c=False, ic=icon):
                frame.close()
                ic.touch()
                ic.activated.emit(QSystemTrayIcon.Trigger)

            def ctx(pos, ic=icon, b=b):
                if ic.contextMenu() is not None:
                    frame.close()
                    ic.contextMenu().popup(b.mapToGlobal(pos))
            b.clicked.connect(click)
            b.setContextMenuPolicy(Qt.CustomContextMenu)
            b.customContextMenuRequested.connect(ctx)
            grid.addWidget(b, i // 4, i % 4)
        v.addLayout(grid)
        link = QLabel("Customize...")
        link.setCursor(Qt.PointingHandCursor)

        def customize(_e):
            frame.close()
            from .tray import customize_notifications
            customize_notifications(self.desktop)
        link.mousePressEvent = customize
        v.addWidget(link)
        frame.adjustSize()
        r = self.chevron_rect()
        gp = self.mapToGlobal(QPoint(r.center().x(), r.top()))
        frame.move(gp.x() - frame.width() // 2, gp.y() - frame.height() - 8)
        frame.show()

    def _context_menu(self, global_pos, on_clock=False):
        from claudexp import programs
        menu = QMenu(self)
        menu.setStyleSheet(_menu_css())
        if on_clock:
            menu.addAction("Adjust date/time", lambda: __import__("claudexp.cpl_extra", fromlist=["date_and_time"])
                           .date_and_time(self.desktop))
            menu.addSeparator()
        menu.addAction("Cascade windows", lambda: self._arrange("cascade"))
        menu.addAction("Show windows stacked", lambda: self._arrange("stack"))
        menu.addAction("Show windows side by side", lambda: self._arrange("side"))
        menu.addAction("Show the desktop", self._show_desktop)
        menu.addSeparator()
        menu.addAction("Start Task Manager", lambda: programs.launch(self.desktop, "taskmgr"))
        menu.addSeparator()
        menu.addAction("Properties", self._properties)
        menu.popup(global_pos)

    def _properties(self):
        try:
            from claudexp.cpl_extra import taskbar_start
            taskbar_start(self.desktop)
        except Exception:
            from .dialogs import msgbox
            msgbox(self.desktop, "Taskbar and Start Menu Properties", "Taskbar: locked, always on top.", "info")

    def _visible_windows(self):
        return [w for w in self.desktop.windows if w.isVisible() and w.on_taskbar]

    def _show_desktop(self):
        self.peek_timer.stop()
        if self.desktop.peeking:
            self.desktop.peek(False)
        self.desktop.toggle_show_desktop()

    def _arrange(self, how):
        wins = self._visible_windows()
        if not wins:
            return
        area = self.desktop.work_area()
        if how == "cascade":
            for i, w in enumerate(wins):
                w.maximized = False
                w.snapped = None
                w.move(30 + i * 28, 30 + i * 28)
        elif how == "stack":
            h = area.height() // len(wins)
            for i, w in enumerate(wins):
                w.maximized = False
                w.snapped = None
                w.setGeometry(0, i * h, area.width(), h)
        else:
            wd = area.width() // len(wins)
            for i, w in enumerate(wins):
                w.maximized = False
                w.snapped = None
                w.setGeometry(i * wd, 0, wd, area.height())
        sound.play("menu")

    # ---- painting ----
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        from . import display
        aero = display.get().aero_color()
        w, h = self.width(), self.height()
        base = QColor(aero).darker(190)
        base.setAlpha(225)
        p.fillRect(self.rect(), base)
        sheen = QLinearGradient(0, 0, 0, h)
        sheen.setColorAt(0, QColor(255, 255, 255, 70))
        sheen.setColorAt(0.5, QColor(255, 255, 255, 18))
        sheen.setColorAt(0.52, QColor(0, 0, 0, 20))
        sheen.setColorAt(1, QColor(255, 255, 255, 10))
        p.fillRect(self.rect(), sheen)
        p.setPen(QPen(QColor(0, 0, 0, 160), 1))
        p.drawLine(0, 0, w, 0)
        p.setPen(QPen(QColor(255, 255, 255, 60), 1))
        p.drawLine(0, 1, w, 1)
        # the items
        menu_open = self.desktop.start_menu.isVisible()
        for rect, kind, payload in self.button_rects():
            self._paint_item(p, rect, kind, payload)
        # the orb (hover and pressed states live in the one bitmap, stacked)
        if not self.orb.isNull():
            state = 2 if (self.start_down or menu_open) else (1 if self.hover == "start" else 0)
            src = QRect(0, state * 54, 54, 54)
            p.drawPixmap(QRect(0, (TASKBAR_H - 54) // 2, 54, 54), self.orb, src)
        # the tray
        tray = self.tray_rect()
        p.setPen(QPen(QColor(0, 0, 0, 90), 1))
        p.drawLine(tray.left(), 6, tray.left(), h - 6)
        p.setPen(QPen(QColor(255, 255, 255, 40), 1))
        p.drawLine(tray.left() + 1, 6, tray.left() + 1, h - 6)
        chev = self.chevron_rect()
        if chev.isValid():
            p.setPen(QPen(QColor("#FFFFFF"), 1.4))
            cx, cy = chev.center().x(), chev.center().y()
            p.drawPolyline(QPolygonF([QPointF(cx - 3.5, cy + 1.5), QPointF(cx, cy - 2), QPointF(cx + 3.5, cy + 1.5)]))
        for icon, rect in self.tray_icon_rects():
            p.drawPixmap(rect, icon.icon().pixmap(16, 16))
        for name, rect in self.system_icon_rects():
            if name == "flag":
                p.drawPixmap(rect, flag_pixmap(16))
            elif name == "network":
                from .network import network_pixmap
                p.drawPixmap(rect, network_pixmap(16))
            else:
                from .volume import speaker_pixmap
                p.drawPixmap(rect, speaker_pixmap(16, sound.is_muted()))
        # the clock
        cr = self.clock_rect()
        f = QFont("Segoe UI")
        f.setPixelSize(12)
        p.setFont(f)
        p.setPen(QColor("white"))
        p.drawText(QRect(cr.x(), 3, cr.width(), 17), Qt.AlignCenter, clock.time_text())
        p.drawText(QRect(cr.x(), 19, cr.width(), 17), Qt.AlignCenter, clock.date_text())
        # Show desktop
        sd = self.show_desktop_rect()
        p.setPen(QPen(QColor(0, 0, 0, 120), 1))
        p.drawLine(sd.left(), 4, sd.left(), h - 4)
        p.setPen(QPen(QColor(255, 255, 255, 70), 1))
        p.drawLine(sd.left() + 1, 4, sd.left() + 1, h - 4)
        g = QLinearGradient(sd.left(), 0, sd.right(), 0)
        g.setColorAt(0, QColor(255, 255, 255, 30))
        g.setColorAt(1, QColor(255, 255, 255, 70))
        p.fillRect(QRect(sd.left() + 2, 3, sd.width() - 2, h - 6), g)

    def _paint_item(self, p, rect, kind, payload):
        active = kind == "win" and payload is self.desktop.active and payload.isVisible()
        hovered = self.hover == (kind, id(payload))
        flashing = kind == "win" and payload.flashing and self.flash_on
        r = QRectF(rect).adjusted(0.5, 0.5, -0.5, -0.5)
        icon = None
        label = ""
        if kind == "pinned":
            from claudexp import programs
            try:
                icon = programs.get(payload).icon()
            except StopIteration:
                icon = None
        else:
            icon = payload.icon if not payload.icon.isNull() else None
            label = payload.title
        if kind == "win" or hovered:
            g = QLinearGradient(r.topLeft(), r.bottomLeft())
            if flashing:
                g.setColorAt(0, QColor(255, 210, 110, 230))
                g.setColorAt(1, QColor(240, 160, 40, 230))
            elif active:
                g.setColorAt(0, QColor(255, 255, 255, 140))
                g.setColorAt(0.5, QColor(255, 255, 255, 60))
                g.setColorAt(1, QColor(255, 255, 255, 90))
            elif hovered:
                g.setColorAt(0, QColor(255, 255, 255, 95))
                g.setColorAt(1, QColor(255, 255, 255, 35))
            else:
                g.setColorAt(0, QColor(255, 255, 255, 55))
                g.setColorAt(0.5, QColor(255, 255, 255, 15))
                g.setColorAt(1, QColor(255, 255, 255, 30))
            p.setPen(QPen(QColor(0, 0, 0, 150 if (active or hovered) else 90), 1))
            p.setBrush(g)
            p.drawRoundedRect(r, 3, 3)
            p.setPen(QPen(QColor(255, 255, 255, 110 if active else 70), 1))
            p.setBrush(Qt.NoBrush)
            p.drawRoundedRect(r.adjusted(1, 1, -1, -1), 2, 2)
            if kind == "win" and not payload.isVisible():       # minimized: a flatter button
                p.fillRect(r.adjusted(1, 1, -1, -1), QColor(0, 0, 0, 35))
        size = 24
        if icon is not None:
            ix = rect.x() + (rect.width() - size) // 2 if rect.width() <= ITEM_ICON_W else rect.x() + 8
            p.drawPixmap(ix, rect.y() + (rect.height() - size) // 2, icon.pixmap(size, size))
        if label and rect.width() > ITEM_ICON_W:
            f = QFont("Segoe UI")
            f.setPixelSize(12)
            p.setFont(f)
            text = p.fontMetrics().elidedText(label, Qt.ElideRight, rect.width() - 44)
            p.setPen(QColor(0, 0, 0, 120))
            p.drawText(rect.adjusted(39, 1, -4, 1), Qt.AlignVCenter | Qt.AlignLeft, text)
            p.setPen(QColor("white"))
            p.drawText(rect.adjusted(38, 0, -4, 0), Qt.AlignVCenter | Qt.AlignLeft, text)


def _master():
    from .volume import levels
    return levels()["master"]


def _menu_css():
    from .shims import MENU_CSS
    return MENU_CSS
