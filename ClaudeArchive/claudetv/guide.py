"""The TV Guide: a grid of what's on, styled after the 2001 TV Guide Channel. Three hours at a time, up to a week
ahead; click a show for its details, double-click one that's on now to watch it."""
from datetime import timedelta

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget
from shiboken6 import isValid

from . import lineup, schedule
from .tuner import _not_future, _time, describe, now_secs, tv_icon
from claudecore import host

SPAN = 3 * 3600
COL = 1800
ROW_H = 44
HEAD_W = 92
HEAD_H = 24
BLUE = QColor("#14277A")
CELL = QColor("#2846B4")
CELL_ON = QColor("#3A5ED8")
SELECTED = QColor("#E8C020")
DEAD = QColor("#30364E")


def _short(m):
    """Cartoon-length episodes and extras, which share one label per run in the grid."""
    return m.kind in ("episode", "special") and bool(m.show) and m.secs < 20 * 60


class Grid(QWidget):
    selected = Signal(object, object)          # channel, slot
    activated = Signal(object, object)

    def __init__(self):
        super().__init__()
        self.channels = []
        self.start = 0
        self.pick = None                       # (channel, slot)
        self.cells = []                        # (QRectF, channel, slot)
        self.setMinimumHeight(HEAD_H + 5 * ROW_H)
        self.setMouseTracking(True)

    def set_view(self, channels, start):
        self.channels, self.start = channels, start
        self.setMinimumHeight(HEAD_H + max(5, len(channels)) * ROW_H + 2)      # every channel gets its row
        self.update()

    def _x(self, t):
        w = self.width() - HEAD_W
        return HEAD_W + (t - self.start) / SPAN * w

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), BLUE)
        w = self.width()
        # time header
        g = QLinearGradient(0, 0, 0, HEAD_H)
        g.setColorAt(0, QColor("#F0D040"))
        g.setColorAt(1, QColor("#C09010"))
        p.fillRect(QRectF(0, 0, w, HEAD_H), g)
        p.setPen(QColor("#202020"))
        p.setFont(QFont("Arial", 9, QFont.Bold))
        day = schedule.EPOCH + timedelta(seconds=self.start)
        p.drawText(QRectF(4, 0, HEAD_W - 8, HEAD_H), Qt.AlignVCenter | Qt.AlignLeft, f"{day:%a %b} {day.day}")
        for i in range(SPAN // COL):
            t = self.start + i * COL
            x = self._x(t)
            p.drawText(QRectF(x + 4, 0, 90, HEAD_H), Qt.AlignVCenter | Qt.AlignLeft,
                       _time(schedule.EPOCH + timedelta(seconds=t)))
            p.setPen(QPen(QColor("#806010"), 1))
            p.drawLine(int(x), 2, int(x), HEAD_H - 2)
            p.setPen(QColor("#202020"))
        self.cells = []
        y = HEAD_H
        for ch in self.channels:
            row = QRectF(0, y, w, ROW_H)
            p.fillRect(QRectF(0, y + 1, HEAD_W - 2, ROW_H - 2), QColor("#0A1650"))
            p.setPen(QColor("#FFD43A"))
            p.setFont(QFont("Arial Black", 12))
            p.drawText(QRectF(6, y, 30, ROW_H), Qt.AlignVCenter | Qt.AlignLeft, str(ch.number))
            p.setPen(Qt.white)
            p.setFont(QFont("Arial", 9, QFont.Bold))
            p.drawText(QRectF(36, y, HEAD_W - 40, ROW_H), Qt.AlignVCenter | Qt.AlignLeft, ch.call or "")
            if ch.dead:
                r = QRectF(HEAD_W, y + 1, w - HEAD_W - 1, ROW_H - 2)
                p.fillRect(r, DEAD)
                p.setPen(QColor("#9098B8"))
                f = QFont("Arial", 9)
                f.setItalic(True)
                p.setFont(f)
                p.drawText(r.adjusted(8, 0, 0, 0), Qt.AlignVCenter | Qt.AlignLeft, "No Signal")
            else:
                now = now_secs()
                progs = ch.programs(self.start, self.start + SPAN + 3600)
                # a listing runs until the next one starts (the ads and Up Next cards belong to it)
                runs = []                         # [[slot, ...]] runs of short episodes of one show share a label
                for i, slot in enumerate(progs):
                    end = progs[i + 1].start if i + 1 < len(progs) else slot.end
                    if slot.start >= self.start + SPAN:
                        break
                    x0, x1 = max(self._x(slot.start), HEAD_W), min(self._x(end), w - 1)
                    r = QRectF(x0 + 1, y + 1, x1 - x0 - 2, ROW_H - 2)
                    picked = self.pick is not None and self.pick[1] is slot
                    p.fillRect(r, SELECTED if picked else (CELL_ON if slot.start <= now < end else CELL))
                    self.cells.append((r, ch, slot))
                    m = slot.media
                    prev = runs[-1][-1][0] if runs else None
                    if _short(m) and prev is not None and _short(prev.media) and prev.media.show_key == m.show_key:
                        runs[-1].append((slot, r, picked))
                    else:
                        runs.append([(slot, r, picked)])
                for run in runs:
                    slot, r, picked = run[0]
                    m = slot.media
                    if len(run) > 1:
                        r = r.united(run[-1][1])
                        picked = False
                        top, bottom = m.show, f"{slot.text}" if slot.text else f"{len(run)} episodes"
                    elif m.kind in ("episode", "special") and m.show:
                        top, bottom = m.show, m.title
                    else:
                        top, bottom = m.title, m.year if _not_future(m.year) else m.rating
                    if r.width() < 14:
                        continue
                    if slot.start < self.start:
                        top = "◄ " + (top or "")
                    p.setPen(QColor("#101010") if picked else Qt.white)
                    p.setFont(QFont("Arial", 8, QFont.Bold))
                    fm = p.fontMetrics()
                    p.drawText(r.adjusted(4, 3, -3, 0), Qt.AlignTop | Qt.AlignLeft,
                               fm.elidedText(top or "", Qt.ElideRight, int(r.width() - 7)))
                    p.setFont(QFont("Arial", 8))
                    fm = p.fontMetrics()
                    p.setPen(QColor("#303030") if picked else QColor("#C8D4FF"))
                    p.drawText(r.adjusted(4, 0, -3, -4), Qt.AlignBottom | Qt.AlignLeft,
                               fm.elidedText(str(bottom or ""), Qt.ElideRight, int(r.width() - 7)))
            y += ROW_H
        # the 'now' line
        now = now_secs()
        if self.start <= now < self.start + SPAN:
            x = self._x(now)
            p.setPen(QPen(QColor("#FF4040"), 2))
            p.drawLine(int(x), HEAD_H, int(x), y)

    def _hit(self, pos):
        for r, ch, slot in self.cells:
            if r.contains(pos):
                return ch, slot
        return None

    def mousePressEvent(self, event):
        hit = self._hit(event.position())
        if hit:
            self.pick = hit
            self.update()
            self.selected.emit(*hit)

    def mouseDoubleClickEvent(self, event):
        hit = self._hit(event.position())
        if hit:
            self.activated.emit(*hit)

    def mouseMoveEvent(self, event):
        self.setCursor(Qt.PointingHandCursor if self._hit(event.position()) else Qt.ArrowCursor)


class Guide(QWidget):
    def __init__(self, desktop, tuner=None):
        super().__init__()
        self.desktop = desktop
        self.tuner = tuner
        self.frame = None
        self.channels = []
        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(self.backgroundRole(), BLUE)
        self.setPalette(pal)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setSpacing(6)

        self.detail = QLabel()
        self.detail.setWordWrap(True)
        self.detail.setTextFormat(Qt.RichText)
        self.detail.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.detail.setMinimumHeight(110)
        self.detail.setStyleSheet("QLabel { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #0A1650,"
                                  " stop:1 #050A30); color: white; border: 2px solid #F0D040; padding: 6px;"
                                  " font: 12px Arial; }")
        lay.addWidget(self.detail)

        nav = QHBoxLayout()
        style = ("QPushButton { background:#F0D040; color:#202020; border:1px solid #806010; border-radius:3px;"
                 " padding:2px 10px; font: bold 11px Arial; } QPushButton:pressed { background:#C09010; }")

        def button(text, slot):
            b = QPushButton(text)
            b.setStyleSheet(style)
            b.clicked.connect(slot)
            nav.addWidget(b)
            return b
        button("◄ Earlier", lambda: self.move_by(-COL * 3))
        button("Now", self.go_now)
        button("Later ►", lambda: self.move_by(COL * 3))
        nav.addStretch(1)
        self.day = QComboBox()
        self.day.setStyleSheet("QComboBox { font: 11px Arial; padding: 1px 6px; }")
        self.day.activated.connect(self._pick_day)
        nav.addWidget(self.day)
        self.watch = button("Watch", self.watch_selected)
        self.watch.setEnabled(False)
        lay.addLayout(nav)

        self.grid = Grid()
        self.grid.selected.connect(self.show_detail)
        self.grid.activated.connect(self.tune)
        lay.addWidget(self.grid, 1)

        self.start = 0
        self.picked = None
        self.detail.setText("<b style='color:#FFD43A; font-size:15px'>TV Guide</b><br>Loading listings...")
        lineup.get(self._ready)

    def _ready(self, channels):
        if not isValid(self):
            return
        self.channels = channels
        self._fill_days()
        self.go_now()
        live = [c for c in channels if not c.dead]
        if not any(c.decks for c in live):
            self.detail.setText("<b style='color:#FFD43A; font-size:15px'>No listings</b><br>ClaudeTV didn't find "
                                "any programs. Copy the TV archive to drive E: (Local Storage) and choose "
                                "<i>Rescan Channels</i> in ClaudeTV.")
        else:
            on = [c.at(now_secs()) for c in live]
            first = next((s for s in on if s is not None and s.kind == "program"), None)
            if first is not None:
                ch = live[on.index(first)]
                self.grid.pick = (ch, first)
                self.show_detail(ch, first)

    def _fill_days(self):
        self.day.clear()
        today = host.now().replace(hour=0, minute=0, second=0, microsecond=0)
        for i in range(7):
            d = today + timedelta(days=i)
            self.day.addItem("Today" if i == 0 else ("Tomorrow" if i == 1 else f"{d:%A}, {d:%b} {d.day}"), i)

    def _pick_day(self, index):
        today = host.now().replace(hour=0, minute=0, second=0, microsecond=0)
        hour = (schedule.EPOCH + timedelta(seconds=self.start)).hour if self.start else 18
        target = today + timedelta(days=index, hours=max(hour, 6) if index else hour)
        self.set_start(schedule.seconds(target))

    def go_now(self):
        t = int(now_secs())
        self.set_start(t - t % COL)

    def move_by(self, secs):
        self.set_start(self.start + secs)

    def set_start(self, start):
        now = int(now_secs())
        start = max(now - now % COL - 6 * 3600, min(start, now + 7 * 86400))
        self.start = start - start % COL
        self.grid.set_view(self.channels, self.start)
        days = (schedule.EPOCH + timedelta(seconds=self.start)).date() - host.now().date()
        if 0 <= days.days < self.day.count():
            self.day.setCurrentIndex(days.days)

    def show_detail(self, ch, slot):
        self.picked = (ch, slot)
        title, sub, desc = describe(slot)
        esc = lambda s: (s or "").replace("&", "&amp;").replace("<", "&lt;")
        day = slot.when()
        self.detail.setText(
            f"<span style='color:#FFD43A; font-size:16px; font-weight:bold'>{esc(title)}</span><br>"
            f"<span style='color:#9CF0A8'>Channel {ch.number} {ch.call} &nbsp;·&nbsp; {day:%A}, {day:%b} {day.day}"
            f" &nbsp;·&nbsp; {esc(sub)}</span><br><br>{esc(desc)}")
        on_now = slot.start <= now_secs() < slot.end
        self.watch.setEnabled(on_now)
        self.watch.setText("Watch" if on_now else "Not on yet")

    def watch_selected(self):
        if self.picked:
            self.tune(*self.picked)

    def tune(self, ch, slot):
        if not (slot.start <= now_secs() < slot.end):
            return
        from .tuner import current, open_tv
        tuner = current()
        if tuner is None:
            tuner = open_tv(self.desktop).content
        else:
            self.desktop.activate(tuner.frame)
        if tuner.channels:
            tuner.tune(next(c for c in tuner.channels if c.number == ch.number))
        else:
            tuner.state["channel"] = ch.number


_open = {}


def open_guide(desktop, tuner=None):
    win = _open.get("win")
    if win is None or not isValid(win):
        body = Guide(desktop, tuner)
        win = host.window(desktop, "TV Guide - ClaudeTV", body, tv_icon(), (720, 520))
        body.frame = win
        _open["win"] = win
    desktop.open_window(win)
    return win
