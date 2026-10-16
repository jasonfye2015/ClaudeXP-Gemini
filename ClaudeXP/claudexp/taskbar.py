"""The taskbar: Start button, a button per open window, and the tray (program icons, volume, clock)."""
from PySide6.QtCore import QEvent, QPoint, QPointF, QRect, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QSystemTrayIcon, QToolTip, QWidget
from shiboken6 import isValid

from . import clock, sound, theme

TASKBAR_H = 30
BUTTON_W = 160
BUTTON_H = 26
TRAY_SLOT = 22     # width per tray icon (16px icon + gap)
CLOCK_W = 70
CHEVRON_W = 16     # the 'show hidden icons' button at the left of the tray
COLLAPSE_SECONDS = 6
FLASHES = 8        # taskbar button blinks this many times, then stays orange


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
        self.expanded = False          # hidden tray icons shown (the chevron was clicked)
        self.expanded_until = 0.0
        self._cpl_cache = (0.0, {})
        self._hinted = False
        self.setMouseTracking(True)

    # ---- settings from Taskbar and Start Menu Properties (re-read every couple of seconds) ----
    def _setting(self, key, default):
        import time
        stamp, data = self._cpl_cache
        if time.monotonic() - stamp > 2:
            from .cpl_extra import SETTINGS
            from .programs.people import load_json
            data = load_json(SETTINGS, {})
            self._cpl_cache = (time.monotonic(), data)
        return data.get(key, default)

    # ---- tray icons -----------------------------------------------------------
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
        if mode == "show" or self.desktop.balloon.isVisible() and self.desktop.balloon.owner is icon:
            return False
        if mode == "hide":
            return True
        return self._setting("tb_hideinactive", True) and now - icon.last_used > INACTIVE_SECONDS

    def _tray_split(self):
        """(icons on show, number hidden behind the chevron)."""
        import time
        from .tray import tray_settings
        icons = self._live_tray_icons()
        if not icons:
            return [], 0
        now = time.monotonic()
        if self.expanded and now > self.expanded_until and not self.underMouse():
            self.expanded = False
        data = tray_settings() if not hasattr(self, "_tray_data") or now - self._tray_data[0] > 2 else \
            self._tray_data[1]
        self._tray_data = (now, data)
        hidden = [i for i in icons if self._hidden(i, data, now)]
        if hidden and not self._hinted:
            self._hint_hidden()
        if self.expanded:
            return icons, len(hidden)
        return [i for i in icons if i not in hidden], len(hidden)

    def _shown_tray_icons(self):
        return self._tray_split()[0]

    def chevron_rect(self):
        if not self._tray_split()[1]:
            return QRect()
        tray = self.tray_rect()
        return QRect(tray.left() + 4, (TASKBAR_H - 16) // 2, 14, 16)

    def _chevron_w(self):
        return CHEVRON_W if self._tray_split()[1] else 0

    def tray_icon_rects(self):
        tray = self.tray_rect()
        y = (TASKBAR_H - 16) // 2
        x0 = tray.left() + 8 + self._chevron_w()
        return [(icon, QRect(x0 + i * TRAY_SLOT, y, 16, 16)) for i, icon in enumerate(self._shown_tray_icons())]

    def _hint_hidden(self):
        """The first time icons go behind the chevron, a balloon says so (once, ever)."""
        from .tray import save_tray_settings, tray_settings, TrayIcon
        self._hinted = True
        data = tray_settings()
        if data.get("hint_shown"):
            return
        data["hint_shown"] = True
        save_tray_settings(data)
        from PySide6.QtWidgets import QApplication, QStyle
        owner = self._chevron_owner = TrayIcon(self.desktop, QApplication.style().standardIcon(
            QStyle.SP_MessageBoxInformation), self)
        owner._visible = True

        def pop():
            if self.chevron_rect().isNull():
                return
            self.desktop.balloon.pop(owner, "Inactive icons hidden",
                                     "To keep the notification area tidy, icons you haven't clicked in a while are "
                                     "hidden. Click the arrow to see them, or right-click the taskbar and choose "
                                     "Properties to change this.", 12000)
        QTimer.singleShot(500, pop)

    def tray_icon_center(self, icon):
        if icon is getattr(self, "_chevron_owner", None):
            r = self.chevron_rect()
            return self.mapToParent(r.center()) if not r.isNull() else None
        for i, rect in self.tray_icon_rects():
            if i is icon:
                return self.mapToParent(rect.center())
        return None

    def _tray_icon_at(self, pos):
        for icon, rect in self.tray_icon_rects():
            if rect.adjusted(-3, -7, 3, 7).contains(pos):
                return icon
        return None

    # ---- flashing buttons -----------------------------------------------------
    def start_flashing(self):
        if not self.flasher.isActive():
            self.flash_on = True
            self.flasher.start(500)
        self.update()

    def _flash_tick(self):
        flashing = [w for w in self.desktop.task_order if w.flashing]
        if not flashing:
            self.flasher.stop()
            return
        self.flash_on = not self.flash_on
        for w in flashing:
            w.flash_ticks += 1
        self.update()

    # ---- layout ----------------------------------------------------------------
    def start_rect(self):
        return QRect(0, 0, theme.current().start_width(), TASKBAR_H)

    def _clock_w(self):
        return CLOCK_W if self._setting("tb_clock", True) else 6

    def tray_rect(self):
        shown, hidden = self._tray_split()
        width = 10 + (CHEVRON_W if hidden else 0) + TRAY_SLOT * (len(shown) + 1) + self._clock_w()
        return QRect(self.width() - width, 0, width, TASKBAR_H)

    def speaker_rect(self):
        tray = self.tray_rect()
        return QRect(tray.left() + 8 + self._chevron_w() + TRAY_SLOT * len(self._shown_tray_icons()),
                     (TASKBAR_H - 16) // 2, 16, 16)

    def clock_rect(self):
        tray = self.tray_rect()
        if not self._setting("tb_clock", True):
            return QRect()
        return QRect(tray.right() - CLOCK_W + 1, 0, CLOCK_W, TASKBAR_H)

    def button_rects(self):
        wins = self.desktop.task_order
        if not wins:
            return []
        x0 = self.start_rect().right() + 8
        avail = self.tray_rect().left() - 4 - x0
        bw = max(40, min(BUTTON_W, (avail + 2) // len(wins) - 2))
        y = (TASKBAR_H - BUTTON_H) // 2
        return [(win, QRect(x0 + i * (bw + 2), y, bw, BUTTON_H)) for i, win in enumerate(wins)]

    # ---- events ------------------------------------------------------------------
    def event(self, event):
        if event.type() == QEvent.ToolTip:
            icon = self._tray_icon_at(event.pos())
            if icon is not None and icon.toolTip():
                QToolTip.showText(event.globalPos(), icon.toolTip(), self)
            elif not self.clock_rect().isNull() and self.clock_rect().contains(event.pos()):
                QToolTip.showText(event.globalPos(), clock.long_date_text(), self)
            elif self.speaker_rect().contains(event.pos()):
                QToolTip.showText(event.globalPos(), "Volume" + (" (muted)" if sound.is_muted() else ""), self)
            elif not self.chevron_rect().isNull() and self.chevron_rect().contains(event.pos()):
                QToolTip.showText(event.globalPos(), "Hide" if self.expanded else "Show hidden icons", self)
            else:
                QToolTip.hideText()
            return True
        return super().event(event)

    def mousePressEvent(self, event):
        pos = event.position().toPoint()
        icon = self._tray_icon_at(pos)
        if icon is not None:
            icon.touch()
            if event.button() == Qt.RightButton:
                icon.activated.emit(QSystemTrayIcon.Context)
                menu = icon.contextMenu()
                if menu is not None:
                    menu.popup(event.globalPosition().toPoint() - QPoint(0, menu.sizeHint().height()))
            elif event.button() == Qt.LeftButton:
                icon.activated.emit(QSystemTrayIcon.Trigger)
            return
        if event.button() == Qt.RightButton and self.speaker_rect().contains(pos):
            self._speaker_menu(event.globalPosition().toPoint())
            return
        if event.button() == Qt.RightButton and not self.start_rect().contains(pos):
            self._context_menu(event.globalPosition().toPoint(), on_clock=self.clock_rect().contains(pos))
            return
        if event.button() != Qt.LeftButton:
            return
        if self.start_rect().contains(pos):
            self.desktop.toggle_start_menu()
            return
        if not self.chevron_rect().isNull() and self.chevron_rect().contains(pos):
            import time
            self.expanded = not self.expanded
            self.expanded_until = time.monotonic() + COLLAPSE_SECONDS
            self.desktop.balloon.dismiss(getattr(self, "_chevron_owner", None))
            self.update()
            return
        if self.speaker_rect().contains(pos):
            # a single click: the Volume slider (a double click opens Volume Control, below)
            self._speaker_click = QTimer.singleShot(260, self._volume_popup) if not getattr(
                self, "_double", False) else None
            return
        for win, rect in self.button_rects():
            if rect.contains(pos):
                self.desktop.taskbar_clicked(win)
                return

    def _volume_popup(self):
        if getattr(self, "_double", False):
            self._double = False
            return
        from .volume import VolumePopup
        self._vol = VolumePopup(self)
        self._vol.show_at(self.mapToGlobal(self.speaker_rect().center()))

    def _speaker_menu(self, global_pos):
        from PySide6.QtWidgets import QMenu
        from .volume import open_volume_control
        menu = QMenu(self)
        menu.setStyleSheet(theme.current().menu_css())
        menu.addAction("&Open Volume Control", lambda: open_volume_control(self.desktop))
        menu.addAction("&Adjust Audio Properties", lambda: __import__(
            "claudexp.controlpanel", fromlist=["sound_properties"]).sound_properties(self.desktop))
        menu.popup(global_pos - QPoint(0, menu.sizeHint().height()))

    def _context_menu(self, global_pos, on_clock=False):
        """XP's taskbar menu: arrange windows, Show the Desktop, Task Manager."""
        from PySide6.QtWidgets import QMenu
        from . import programs
        d = self.desktop
        menu = QMenu(self)
        menu.setStyleSheet(theme.current().menu_css())
        from . import cpl_extra
        if on_clock:
            menu.addAction("&Adjust Date/Time", lambda: cpl_extra.date_and_time(d))
            menu.addAction("&Customize Notifications...", lambda: __import__(
                "claudexp.tray", fromlist=["customize_notifications"]).customize_notifications(d))
            menu.addSeparator()
        menu.addAction("&Toolbars").setEnabled(False)
        menu.addSeparator()
        menu.addAction("Ca&scade Windows", lambda: self._arrange("cascade"))
        menu.addAction("Tile Windows Hori&zontally", lambda: self._arrange("rows"))
        menu.addAction("Tile Windows V&ertically", lambda: self._arrange("columns"))
        menu.addAction("&Show the Desktop", self._show_desktop)
        menu.addSeparator()
        menu.addAction("Tas&k Manager", lambda: programs.launch(d, "taskmgr"))
        menu.addSeparator()
        lock = menu.addAction("&Lock the Taskbar")
        lock.setCheckable(True)
        lock.setChecked(True)
        lock.setEnabled(False)
        menu.addAction("P&roperties", lambda: cpl_extra.taskbar_start(d))
        menu.popup(global_pos - QPoint(0, menu.sizeHint().height()))

    def _visible_windows(self):
        return [w for w in self.desktop.windows if w.isVisible() and w.on_taskbar]

    def _show_desktop(self):
        for w in self._visible_windows():
            self.desktop.minimize(w)

    def _arrange(self, how):
        wins = self._visible_windows()
        if not wins:
            return
        area = self.desktop.work_area()
        for i, w in enumerate(wins):
            if w.maximized:
                w.toggle_maximize()
            if how == "cascade":
                w.move(area.x() + 10 + i * 26, area.y() + 10 + i * 26)
                continue
            n = len(wins)
            if w.resizable:
                if how == "rows":
                    w.setGeometry(area.x(), area.y() + i * area.height() // n, area.width(), area.height() // n)
                else:
                    w.setGeometry(area.x() + i * area.width() // n, area.y(), area.width() // n, area.height())
            else:
                w.move(area.x() + (0 if how == "rows" else i * area.width() // n),
                       area.y() + (i * area.height() // n if how == "rows" else 0))
        for w in wins:
            w.raise_()
        self.raise_()

    def mouseDoubleClickEvent(self, event):
        pos = event.position().toPoint()
        icon = self._tray_icon_at(pos)
        if icon is not None and event.button() == Qt.LeftButton:
            icon.touch()
            icon.activated.emit(QSystemTrayIcon.DoubleClick)
            return
        if event.button() == Qt.LeftButton and self.speaker_rect().contains(pos):
            self._double = True                      # cancels the pending single-click slider
            from .volume import open_volume_control
            open_volume_control(self.desktop)
            return
        if event.button() == Qt.LeftButton and not self.clock_rect().isNull() and self.clock_rect().contains(pos):
            from . import cpl_extra
            cpl_extra.date_and_time(self.desktop)
            return
        self.mousePressEvent(event)

    # ---- painting ----------------------------------------------------------------
    def paintEvent(self, event):
        st = theme.current()
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        st.paint_taskbar(p, self.rect(), self.start_rect(), self.desktop.start_menu.isVisible())

        font = QFont("Tahoma", 8)
        for win, rect in self.button_rects():
            pressed = win is self.desktop.active and win.isVisible()
            st.paint_task_button(p, rect, pressed)
            if win.flashing and (self.flash_on or win.flash_ticks >= FLASHES):
                grad = QLinearGradient(0, rect.top(), 0, rect.bottom())
                grad.setColorAt(0, QColor("#F9B868"))
                grad.setColorAt(1, QColor("#E2791B"))
                p.fillRect(rect.adjusted(1, 1, -1, -1), grad)
            shift = 1 if pressed else 0
            if not win.icon.isNull():
                p.drawPixmap(rect.x() + 7 + shift, rect.center().y() - 7 + shift, win.icon.pixmap(16, 16))
            trect = QRect(rect.x() + 28 + shift, rect.y() + shift, rect.width() - 34, rect.height())
            font.setBold(pressed and st.key == "classic")
            p.setFont(font)
            text = p.fontMetrics().elidedText(win.title, Qt.ElideRight, trect.width())
            p.setPen(QColor(st.task_text_color(pressed)))
            p.drawText(trect, Qt.AlignVCenter | Qt.AlignLeft, text)

        tray = self.tray_rect()
        st.paint_tray(p, tray)

        for icon, rect in self.tray_icon_rects():
            p.drawPixmap(rect, icon.icon().pixmap(16, 16))
        self._draw_speaker(p, self.speaker_rect())
        self._draw_chevron(p, st)
        if self.clock_rect().isNull():
            return

        p.setPen(QColor(st.tray_text))
        now = clock.now()
        small = QFont("Tahoma")
        small.setPixelSize(11)
        p.setFont(small)
        text = self.clock_rect().adjusted(0, 2, 0, -2)
        p.drawText(text.adjusted(0, 0, 0, -text.height() // 2), Qt.AlignHCenter | Qt.AlignBottom, clock.time_text(now))
        p.drawText(text.adjusted(0, text.height() // 2, 0, 0), Qt.AlignHCenter | Qt.AlignTop, clock.date_text(now))

    def _draw_chevron(self, p, st):
        r = self.chevron_rect()
        if r.isNull():
            return
        p.save()
        p.setRenderHint(QPainter.Antialiasing)
        hover = self.underMouse() and r.contains(self.mapFromGlobal(__import__(
            "PySide6.QtGui", fromlist=["QCursor"]).QCursor.pos()))
        p.setPen(QPen(QColor(255, 255, 255, 150 if hover else 90), 1))
        p.setBrush(QColor(255, 255, 255, 70 if hover else 30))
        p.drawEllipse(QRectF(r.x() + 0.5, r.y() + 1.5, 13, 13))
        p.setPen(QPen(QColor(st.tray_text), 1.6, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        cx, cy = r.x() + 7, r.y() + 8
        d = -1 if self.expanded else 1               # '<<' to show, '>>' to hide again
        for off in (-2, 2):
            p.drawPolyline(QPolygonF([QPointF(cx + off + 1.5 * d, cy - 3), QPointF(cx + off - 1.5 * d, cy),
                                      QPointF(cx + off + 1.5 * d, cy + 3)]))
        p.restore()

    def mouseMoveEvent(self, event):
        if not self.chevron_rect().isNull():
            self.update(self.chevron_rect().adjusted(-2, -2, 2, 2))
        if self.expanded:
            import time
            self.expanded_until = time.monotonic() + COLLAPSE_SECONDS

    def _draw_speaker(self, p, r):
        p.save()
        p.setRenderHint(QPainter.Antialiasing)
        x, y = r.x(), r.y()
        body = QPolygonF([QPointF(x + 1, y + 5), QPointF(x + 4, y + 5), QPointF(x + 8, y + 1),
                          QPointF(x + 8, y + 15), QPointF(x + 4, y + 11), QPointF(x + 1, y + 11)])
        p.setPen(QPen(QColor("#1A3E7A"), 1))
        p.setBrush(QColor("#E8EEF8"))
        p.drawPolygon(body)
        p.setBrush(Qt.NoBrush)
        if sound.is_muted():
            p.setPen(QPen(QColor("#E0302A"), 2))
            p.drawEllipse(QRectF(x + 8, y + 7, 8, 8))
            p.drawLine(QPointF(x + 9.5, y + 13.5), QPointF(x + 14.5, y + 8.5))
        else:
            p.setPen(QPen(QColor("white"), 1.2))
            p.drawArc(QRectF(x + 6, y + 5, 5, 6), -60 * 16, 120 * 16)
            p.drawArc(QRectF(x + 5, y + 2, 9, 12), -60 * 16, 120 * 16)
        p.restore()
