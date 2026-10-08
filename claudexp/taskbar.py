"""The taskbar: Start button, a button per open window, and the tray (program icons, volume, clock)."""
from PySide6.QtCore import QEvent, QPoint, QPointF, QRect, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QSystemTrayIcon, QToolTip, QWidget
from shiboken6 import isValid

from . import clock, sound
from .paths import pixmap

TASKBAR_H = 30
BUTTON_W = 160
BUTTON_H = 26
TRAY_SLOT = 22     # width per tray icon (16px icon + gap)
CLOCK_W = 70
FLASHES = 8        # taskbar button blinks this many times, then stays orange


class Taskbar(QWidget):
    def __init__(self, desktop):
        super().__init__(desktop)
        self.desktop = desktop
        self.tile = pixmap("taskbar_empty.jpg").scaledToHeight(TASKBAR_H, Qt.SmoothTransformation)
        self.start_pm = pixmap("startbutton.jpg").scaledToHeight(TASKBAR_H, Qt.SmoothTransformation)
        self.button_pm = pixmap("taskbar_window.jpg")
        self.tray_icons = []
        self.flash_on = False
        self.setFixedHeight(TASKBAR_H)
        self.clock = QTimer(self)
        self.clock.timeout.connect(self.update)
        self.clock.start(1000)
        self.flasher = QTimer(self)
        self.flasher.timeout.connect(self._flash_tick)

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

    def tray_icon_rects(self):
        tray = self.tray_rect()
        y = (TASKBAR_H - 16) // 2
        return [(icon, QRect(tray.left() + 8 + i * TRAY_SLOT, y, 16, 16))
                for i, icon in enumerate(self._live_tray_icons())]

    def tray_icon_center(self, icon):
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
        return QRect(0, 0, self.start_pm.width(), TASKBAR_H)

    def tray_rect(self):
        width = 10 + TRAY_SLOT * (len(self._live_tray_icons()) + 1) + CLOCK_W
        return QRect(self.width() - width, 0, width, TASKBAR_H)

    def speaker_rect(self):
        tray = self.tray_rect()
        return QRect(tray.left() + 8 + TRAY_SLOT * len(self._live_tray_icons()), (TASKBAR_H - 16) // 2, 16, 16)

    def clock_rect(self):
        tray = self.tray_rect()
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
            elif self.clock_rect().contains(event.pos()):
                QToolTip.showText(event.globalPos(), clock.long_date_text(), self)
            else:
                QToolTip.hideText()
            return True
        return super().event(event)

    def mousePressEvent(self, event):
        pos = event.position().toPoint()
        icon = self._tray_icon_at(pos)
        if icon is not None:
            if event.button() == Qt.RightButton:
                icon.activated.emit(QSystemTrayIcon.Context)
                menu = icon.contextMenu()
                if menu is not None:
                    menu.popup(event.globalPosition().toPoint() - QPoint(0, menu.sizeHint().height()))
            elif event.button() == Qt.LeftButton:
                icon.activated.emit(QSystemTrayIcon.Trigger)
            return
        if event.button() == Qt.RightButton and not self.start_rect().contains(pos):
            self._context_menu(event.globalPosition().toPoint())
            return
        if event.button() != Qt.LeftButton:
            return
        if self.start_rect().contains(pos):
            self.desktop.toggle_start_menu()
            return
        if self.speaker_rect().contains(pos):
            sound.set_muted(not sound.is_muted())
            sound.play("default")
            self.update()
            return
        for win, rect in self.button_rects():
            if rect.contains(pos):
                self.desktop.taskbar_clicked(win)
                return

    def _context_menu(self, global_pos):
        """XP's taskbar menu: arrange windows, Show the Desktop, Task Manager."""
        from PySide6.QtWidgets import QMenu
        from . import programs
        from .startmenu import MENU_STYLE
        d = self.desktop
        menu = QMenu(self)
        menu.setStyleSheet(MENU_STYLE)
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
        menu.addAction("P&roperties").setEnabled(False)
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
        icon = self._tray_icon_at(event.position().toPoint())
        if icon is not None and event.button() == Qt.LeftButton:
            icon.activated.emit(QSystemTrayIcon.DoubleClick)
            return
        self.mousePressEvent(event)

    # ---- painting ----------------------------------------------------------------
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        p.drawTiledPixmap(self.rect(), self.tile)

        p.drawPixmap(0, 0, self.start_pm)
        if self.desktop.start_menu.isVisible():
            p.fillRect(self.start_rect(), QColor(0, 40, 0, 70))

        font = QFont("Tahoma", 8)
        p.setFont(font)
        for win, rect in self.button_rects():
            p.drawPixmap(rect, self.button_pm)
            pressed = win is self.desktop.active and win.isVisible()
            if win.flashing and (self.flash_on or win.flash_ticks >= FLASHES):
                grad = QLinearGradient(0, rect.top(), 0, rect.bottom())
                grad.setColorAt(0, QColor("#F9B868"))
                grad.setColorAt(1, QColor("#E2791B"))
                p.fillRect(rect.adjusted(1, 1, -1, -1), grad)
            elif pressed:
                p.fillRect(rect.adjusted(1, 1, -1, -1), QColor(0, 20, 100, 90))
            shift = 1 if pressed else 0
            if not win.icon.isNull():
                p.drawPixmap(rect.x() + 7 + shift, rect.center().y() - 7 + shift, win.icon.pixmap(16, 16))
            trect = QRect(rect.x() + 28 + shift, rect.y() + shift, rect.width() - 34, rect.height())
            text = p.fontMetrics().elidedText(win.title, Qt.ElideRight, trect.width())
            p.setPen(QColor("white"))
            p.drawText(trect, Qt.AlignVCenter | Qt.AlignLeft, text)

        tray = self.tray_rect()
        grad = QLinearGradient(0, 0, 0, TASKBAR_H)
        grad.setColorAt(0, QColor("#1C98EB"))
        grad.setColorAt(0.5, QColor("#0F8CE8"))
        grad.setColorAt(1, QColor("#0F82DE"))
        p.fillRect(tray, grad)
        p.setPen(QColor("#0A5BC5"))
        p.drawLine(tray.left(), 0, tray.left(), TASKBAR_H)
        p.setPen(QColor("#3BB6FF"))
        p.drawLine(tray.left() + 1, 0, tray.left() + 1, TASKBAR_H)

        for icon, rect in self.tray_icon_rects():
            p.drawPixmap(rect, icon.icon().pixmap(16, 16))
        self._draw_speaker(p, self.speaker_rect())

        p.setPen(QColor("white"))
        now = clock.now()
        small = QFont("Tahoma")
        small.setPixelSize(11)
        p.setFont(small)
        text = self.clock_rect().adjusted(0, 2, 0, -2)
        p.drawText(text.adjusted(0, 0, 0, -text.height() // 2), Qt.AlignHCenter | Qt.AlignBottom, clock.time_text(now))
        p.drawText(text.adjusted(0, text.height() // 2, 0, 0), Qt.AlignHCenter | Qt.AlignTop, clock.date_text(now))

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
