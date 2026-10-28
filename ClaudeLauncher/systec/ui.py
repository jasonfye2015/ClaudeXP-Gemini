"""SYSTEC Multi-Boot Manager: the Claude Timeline's system selection screen.

A card per computer (EPOCH-2001, SYSTEM-2011, WORKSTATION-2025). Click one for Load This Computer, Load and Format
and Config; double-click to load. The bottom bar has Help, Profile, Backup, Apps (the programs that also run on
their own), the Manual and Power Off, and the real date and time.
While a computer runs, the launcher steps aside, and comes back when it shuts down.
"""
import math
import os
import random
import subprocess
import sys
import time
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import (QBrush, QColor, QFont, QFontMetrics, QIcon, QImage, QLinearGradient, QPainter,
                           QPainterPath, QPen, QPixmap, QPolygonF, QTransform)
from PySide6.QtWidgets import (QComboBox, QDialog, QFileDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
                               QListWidget, QListWidgetItem, QMessageBox, QPushButton, QToolButton, QVBoxLayout,
                               QWidget)

from . import profile as prof
from .systems import PORTABLE_PYTHON, PORTABLE_PYTHONS, SYSTEMS, TIMELINE

if str(TIMELINE / "ClaudeCore") not in sys.path:          # the shared Furry Code / YIFF Code editor
    sys.path.insert(0, str(TIMELINE / "ClaudeCore"))
if str(TIMELINE / "ClaudeApps") not in sys.path:          # the manual's viewer
    sys.path.append(str(TIMELINE / "ClaudeApps"))

VW, VH = 1408, 768
VERSION = "v1.60"
FONT = "Segoe UI"
TEXT = QColor("#E8ECF2")
DIM = QColor("#8A94A6")
BACKUP_CSS = """
QGroupBox { color: #8FB4FF; font-family: 'Segoe UI'; font-size: 12px; font-weight: 600; border: 1px solid #3A4250;
            border-radius: 6px; margin-top: 10px; padding-top: 8px; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
QCheckBox { color: #E8ECF2; font-family: 'Segoe UI'; font-size: 13px; }
QListWidget { background: #0E1116; color: #E8ECF2; border: 1px solid #3A4250; font-family: 'Segoe UI'; font-size: 12px; }
QListWidget::item:selected { background: #2A3A5A; }
QSpinBox { background: #0E1116; color: #E8ECF2; border: 1px solid #3A4250; padding: 2px; }
QProgressBar { background: #0E1116; border: 1px solid #3A4250; border-radius: 3px; height: 10px; }
QProgressBar::chunk { background: #8FB4FF; }
"""
DIALOG_CSS = """
QDialog { background: #15181E; }
QLabel { color: #E8ECF2; font-family: 'Segoe UI'; font-size: 13px; }
QLabel#title { font-size: 20px; font-weight: 600; letter-spacing: 1px; }
QLabel#dim { color: #8A94A6; }
QLineEdit { background: #0C0E12; color: #E8ECF2; border: 1px solid #3A4250; border-radius: 4px; padding: 6px;
            font-family: 'Segoe UI'; font-size: 14px; selection-background-color: #2E6BD6; }
QListWidget { background: #0C0E12; color: #E8ECF2; border: 1px solid #3A4250; border-radius: 4px;
              font-family: 'Segoe UI'; font-size: 13px; outline: none; }
QListWidget::item { padding: 6px; border-radius: 4px; }
QListWidget::item:selected { background: #24324A; border: 1px solid #5A8CFF; }
QPushButton { background: #1E232C; color: #E8ECF2; border: 1px solid #4A5466; border-radius: 4px;
              padding: 7px 18px; font-family: 'Segoe UI'; font-size: 13px; letter-spacing: 1px; }
QPushButton:hover { border-color: #8FB4FF; background: #263042; }
QPushButton:default { border-color: #5A8CFF; }
QMessageBox { background: #15181E; }
"""
CODES_CSS = DIALOG_CSS + """
QTabWidget::pane { border: 1px solid #3A4250; background: #101318; }
QTabBar::tab { background: #1E232C; color: #C8CED8; padding: 7px 16px; border: 1px solid #3A4250;
               font-family: 'Segoe UI'; font-size: 13px; }
QTabBar::tab:selected { background: #24324A; color: #FFFFFF; border-color: #5A8CFF; }
QWidget { color: #E8ECF2; font-family: 'Segoe UI'; font-size: 12px; }
QScrollArea, QScrollArea > QWidget > QWidget { background: #101318; border: none; }
QGroupBox { border: 1px solid #3A4250; border-radius: 4px; margin-top: 14px; padding-top: 6px; }
QGroupBox::title { subcontrol-origin: margin; left: 8px; color: #8FB4FF; letter-spacing: 1px; }
QComboBox { background: #0C0E12; border: 1px solid #3A4250; border-radius: 3px; padding: 3px 6px; }
QComboBox QAbstractItemView { background: #0C0E12; selection-background-color: #24324A; }
QCheckBox { spacing: 5px; }
QTextBrowser { background: #0C0E12; border: 1px solid #3A4250; }
"""
CODES_LABEL_CSS = "QLabel { font-family: Consolas, 'Courier New'; font-size: 12px; color: #C8D8FF; }"


def _font(px, weight=QFont.Normal, spacing=0.0):
    f = QFont(FONT)
    f.setPixelSize(px)
    f.setWeight(weight)
    if spacing:
        f.setLetterSpacing(QFont.AbsoluteSpacing, spacing)
    return f


def _grey(img):
    return QPixmap.fromImage(img.convertToFormat(QImage.Format_Grayscale8))


def logo_icon():
    """The SYSTEC emblem: an S in a hexagon."""
    ic = QIcon()
    for sz in (16, 32, 48, 256):
        pm = QPixmap(sz, sz)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        _emblem(p, QPointF(sz / 2, sz / 2), sz * 0.46, sz >= 48)
        p.end()
        ic.addPixmap(pm)
    return ic


def _emblem(p, c, r, fine=True):
    hexagon = QPolygonF([QPointF(c.x() + math.cos(math.radians(a)) * r, c.y() + math.sin(math.radians(a)) * r)
                         for a in range(-90, 270, 60)])
    g = QLinearGradient(c.x(), c.y() - r, c.x(), c.y() + r)
    g.setColorAt(0, QColor("#2A3140"))
    g.setColorAt(1, QColor("#0E1117"))
    p.setPen(QPen(QColor("#8FB4FF"), max(1.0, r * 0.08)))
    p.setBrush(QBrush(g))
    p.drawPolygon(hexagon)
    s = QPainterPath()
    k = r * 0.42
    s.moveTo(c.x() + k, c.y() - k * 1.05)
    s.lineTo(c.x() - k * 0.55, c.y() - k * 1.05)
    s.lineTo(c.x() - k, c.y() - k * 0.4)
    s.lineTo(c.x() + k, c.y() + k * 0.4)
    s.lineTo(c.x() + k * 0.55, c.y() + k * 1.05)
    s.lineTo(c.x() - k, c.y() + k * 1.05)
    p.setPen(QPen(QColor("#E8ECF2"), max(1.2, r * 0.16), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    p.setBrush(Qt.NoBrush)
    p.drawPath(s)


class Systec(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SYSTEC Multi-Boot Manager")
        self.setWindowIcon(logo_icon())
        self.setMouseTracking(True)
        self.setMinimumSize(VW * 2 // 3, VH * 2 // 3)
        self.mouse = QPointF(-1, -1)
        self.selected = None
        self.hover = None
        self.buttons = []
        self.cards = []
        self.process = None
        self.running = None
        self.apps = {}                     # the standalone apps started from APPS: key -> their process
        self.bg = None
        self.checks = None                 # the self-check's findings, once it has run
        self._start_selfcheck()
        self.art = {}
        self.t = 0.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(33)
        self.watch = QTimer(self)
        self.watch.timeout.connect(self._check_process)
        QTimer.singleShot(400, self._first_run)

    # ---- geometry -----------------------------------------------------------------------------------------
    def _xf(self):
        sc = min(self.width() / VW, self.height() / VH)
        t = QTransform()
        t.translate((self.width() - VW * sc) / 2, (self.height() - VH * sc) / 2)
        t.scale(sc, sc)
        return t

    def _logical(self, pos):
        inv, _ok = self._xf().inverted()
        return inv.map(pos)

    def _tick(self):
        self.t += 0.033
        self.update()

    # ---- input --------------------------------------------------------------------------------------------
    def mouseMoveEvent(self, e):
        self.mouse = self._logical(e.position())
        hover = next((s for r, s in self.cards if r.contains(self.mouse)), None)
        if hover is not self.hover:
            self.hover = hover
        clickable = any(r.contains(self.mouse) for r, _a in self.buttons) or hover is not None
        self.setCursor(Qt.PointingHandCursor if clickable else Qt.ArrowCursor)

    def mousePressEvent(self, e):
        if e.button() != Qt.LeftButton:
            return
        pos = self._logical(e.position())
        for rect, action in reversed(self.buttons):
            if rect.contains(pos):
                action()
                return
        for rect, system in self.cards:
            if rect.contains(pos):
                self.selected = system
                return
        self.selected = None

    def mouseDoubleClickEvent(self, e):
        pos = self._logical(e.position())
        for rect, system in self.cards:
            if rect.contains(pos) and system.installed:
                self.selected = system
                self.load(system)
                return

    def keyPressEvent(self, e):
        k = e.key()
        if k == Qt.Key_Escape:
            if self.selected:
                self.selected = None
            elif self.isFullScreen():
                self.showNormal()
        elif k == Qt.Key_F11:
            self.showNormal() if self.isFullScreen() else self.showFullScreen()
        elif k in (Qt.Key_Left, Qt.Key_Right):
            i = SYSTEMS.index(self.selected) if self.selected in SYSTEMS else -1
            self.selected = SYSTEMS[(i + (1 if k == Qt.Key_Right else -1)) % len(SYSTEMS)]
        elif k in (Qt.Key_Return, Qt.Key_Enter) and self.selected and self.selected.installed:
            self.load(self.selected)

    # ---- painting -----------------------------------------------------------------------------------------
    def _background(self):
        if self.bg is not None:
            return self.bg
        pm = QPixmap(VW, VH)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        rnd = random.Random(2001)
        step = 110
        pts = {}
        for gy in range(-1, VH // step + 3):
            for gx in range(-1, VW // step + 3):
                pts[gx, gy] = QPointF(gx * step + rnd.uniform(-38, 38), gy * step + rnd.uniform(-38, 38))
        p.setPen(QPen(QColor(255, 255, 255, 10), 1))
        for (gx, gy), a in pts.items():
            b, c, d = pts.get((gx + 1, gy)), pts.get((gx, gy + 1)), pts.get((gx + 1, gy + 1))
            if not (b and c and d):
                continue
            for tri in ((a, b, d), (a, d, c)):
                cy = (tri[0].y() + tri[1].y() + tri[2].y()) / 3
                v = int(26 + rnd.uniform(-9, 9) - cy / VH * 10)
                p.setBrush(QColor(v, v + 1, v + 4))
                p.drawPolygon(QPolygonF(list(tri)))
        p.end()
        self.bg = pm
        return pm

    def _image(self, system, kind=""):
        key = (system.key, kind)
        if key not in self.art:
            img = QImage(str(system.image(kind)))
            self.art[key] = (QPixmap.fromImage(img), _grey(img)) if not img.isNull() else (QPixmap(), QPixmap())
        return self.art[key]

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        p.fillRect(self.rect(), QColor("#0B0D10"))
        p.setTransform(self._xf())
        p.drawPixmap(0, 0, self._background())
        self.buttons, self.cards = [], []
        self._header(p)
        x0, w, gap = 52, 416, 28
        for i, system in enumerate(SYSTEMS):
            self._card(p, QRectF(x0 + i * (w + gap), 104, w, 352), system)
        self._details(p, QRectF(52, 476, VW - 104, 196))
        self._footer(p)
        if self.running:
            p.fillRect(QRectF(0, 0, VW, VH), QColor(0, 0, 0, 170))
            p.setFont(_font(26, QFont.DemiBold, 2))
            p.setPen(TEXT)
            p.drawText(QRectF(0, VH / 2 - 40, VW, 40), Qt.AlignCenter, f"{self.running.key} IS RUNNING")
            p.setFont(_font(14))
            p.setPen(DIM)
            p.drawText(QRectF(0, VH / 2 + 6, VW, 24), Qt.AlignCenter,
                       "The launcher comes back when that computer shuts down.")
        p.end()

    def _header(self, p):
        _emblem(p, QPointF(62, 44), 18)
        p.setFont(_font(26, QFont.Bold, 1.5))
        p.setPen(TEXT)
        p.drawText(QRectF(90, 22, 200, 44), Qt.AlignVCenter, "SYSTEC")
        p.setPen(QPen(QColor("#5A6476"), 1.5))
        p.drawLine(QPointF(212, 28), QPointF(212, 60))
        p.setFont(_font(26, QFont.Normal, 1.0))
        p.setPen(TEXT)
        p.drawText(QRectF(226, 22, 420, 44), Qt.AlignVCenter, "SYSTEM SELECTION")
        p.setFont(_font(15, QFont.Normal, 1.0))
        p.setPen(QColor("#C8CED8"))
        p.drawText(QRectF(VW - 560, 22, 508, 44), Qt.AlignRight | Qt.AlignVCenter,
                   f"SYSTEC | MULTI-BOOT MANAGER | {VERSION}")

    def _status_icons(self, p, x, y, colour):
        p.setPen(QPen(colour, 1.8, Qt.SolidLine, Qt.RoundCap))
        p.setBrush(Qt.NoBrush)
        for i, r in enumerate((10, 6.5, 3)):
            p.drawArc(QRectF(x - r, y - r + 8, r * 2, r * 2), 45 * 16, 90 * 16)
        p.drawRoundedRect(QRectF(x + 18, y - 3, 9, 15), 1.5, 1.5)
        p.drawLine(QPointF(x + 20.5, y - 5), QPointF(x + 24.5, y - 5))
        p.drawLine(QPointF(x + 21, y + 3), QPointF(x + 24, y + 7))

    def _card(self, p, r, system):
        self.cards.append((r, system))
        sel = system is self.selected
        hot = system is self.hover
        accent = QColor(system.accent)
        p.setPen(QPen(accent if sel else QColor("#5A6476") if hot else QColor("#3A4250"), 2 if sel else 1.2))
        p.setBrush(QColor(18, 20, 25, 236))
        p.drawRoundedRect(r, 6, 6)
        if sel:
            glow = QColor(accent)
            for i in range(1, 7):
                glow.setAlpha(36 - i * 5)
                p.setPen(QPen(glow, 2))
                p.setBrush(Qt.NoBrush)
                p.drawRoundedRect(r.adjusted(-i, -i, i, i), 6 + i, 6 + i)
        # title bar
        p.setFont(_font(23, QFont.Medium, 1.2))
        p.setPen(QColor("#F2C88A") if sel else TEXT)
        p.drawText(QRectF(r.x() + 14, r.y() + 6, r.width() - 90, 36), Qt.AlignVCenter, system.key)
        self._status_icons(p, r.right() - 56, r.y() + 18, accent if sel else QColor("#A8B0BE"))
        p.setPen(QPen(QColor("#3A4250"), 1))
        p.drawLine(QPointF(r.x() + 1, r.y() + 46), QPointF(r.right() - 1, r.y() + 46))
        # the picture: the desk, or the screen on hover
        art = QRectF(r.x() + 12, r.y() + 56, r.width() - 24, (r.width() - 24) * 559 / 1024)
        colour, grey = self._image(system, "Screenshot" if hot and system.installed and not sel else "")
        pm = colour if system.installed else grey
        if not pm.isNull():
            path = QPainterPath()
            path.addRoundedRect(art, 4, 4)
            p.save()
            p.setClipPath(path)
            p.drawPixmap(art, pm, QRectF(pm.rect()))
            if not system.installed:
                p.fillRect(art, QColor(0, 0, 0, 120))
            p.restore()
        if not system.installed:
            band = QRectF(art.x(), art.center().y() - 26, art.width(), 52)
            p.fillRect(band, QColor(10, 12, 16, 210))
            p.setFont(_font(18, QFont.DemiBold, 3))
            p.setPen(QColor("#C8CED8"))
            p.drawText(band.adjusted(0, 4, 0, -20), Qt.AlignCenter, "NOT INSTALLED")
            p.setFont(_font(12, QFont.Normal, 1))
            p.setPen(DIM)
            p.drawText(band.adjusted(0, 28, 0, -4), Qt.AlignCenter, f"{system.folder} is coming in a future build")
        elif sel and not self.running:
            p.fillRect(art, QColor(8, 10, 14, 120))
            bw, bh = 214, 38
            cx = art.center().x()
            self._button(p, QRectF(cx - bw / 2, art.y() + 30, bw, bh), "LOAD THIS COMPUTER",
                         lambda s=system: self.load(s), accent)
            self._button(p, QRectF(cx - bw / 2, art.y() + 80, bw, bh), "LOAD AND FORMAT",
                         lambda s=system: self.load(s, format_drive=True), accent)
            self._button(p, QRectF(art.x() + 12, art.bottom() - 42, 96, 30), "CONFIG",
                         lambda s=system: self.config(s), accent, small=True)
            self._button(p, QRectF(art.right() - 108, art.bottom() - 42, 96, 30), "BACK",
                         lambda: setattr(self, "selected", None), accent, small=True)
        # specs
        y = art.bottom() + 14
        p.setFont(_font(16, QFont.Medium))
        p.setPen(accent)
        p.drawText(QRectF(r.x() + 14, y, 200, 22), Qt.AlignVCenter, "Specs")
        p.setFont(_font(15))
        line = "  |  ".join(f"{k}: {v}" for k, v in system.short)
        p.drawText(QRectF(r.x() + 14, y + 24, r.width() - 28, 22), Qt.AlignVCenter,
                   QFontMetrics(p.font()).elidedText(line, Qt.ElideRight, int(r.width() - 28)))

    def _button(self, p, r, text, action, accent, small=False, enabled=True):
        hot = r.contains(self.mouse) and enabled
        p.setPen(QPen(QColor(accent).lighter(130) if hot else QColor("#6A7486"), 1.4))
        p.setBrush(QColor(30, 36, 46, 235) if hot else QColor(16, 19, 25, 225))
        p.drawRoundedRect(r, 4, 4)
        p.setFont(_font(13 if small else 15, QFont.Medium, 1.0))
        p.setPen(TEXT if enabled else DIM)
        p.drawText(r, Qt.AlignCenter, text)
        if enabled:
            self.buttons.append((r, action))

    def _details(self, p, r):
        system = self.selected or self.hover or SYSTEMS[0]
        accent = QColor(system.accent)
        p.setPen(QPen(QColor("#3A4250"), 1.2))
        p.setBrush(QColor(14, 16, 20, 225))
        p.drawRoundedRect(r, 6, 6)
        p.setFont(_font(18, QFont.DemiBold, 1.2))
        p.setPen(accent)
        p.drawText(QRectF(r.x() + 18, r.y() + 10, 600, 26), Qt.AlignVCenter,
                   f"{system.key}  •  {system.os_name}")
        p.setFont(_font(13))
        p.setPen(DIM)
        p.drawText(QRectF(r.x() + 18, r.y() + 36, r.width() - 36, 22), Qt.AlignVCenter, system.tagline)
        col_w = (r.width() - 36) / 2
        for i, (part, value, desc) in enumerate(system.specs):
            col, row = i % 2, i // 2
            x = r.x() + 18 + col * col_w
            y = r.y() + 66 + row * 31
            p.setFont(_font(13, QFont.DemiBold))
            p.setPen(QColor("#C8CED8"))
            p.drawText(QRectF(x, y, 90, 16), Qt.AlignVCenter, part)
            p.setFont(_font(13))
            p.setPen(TEXT)
            p.drawText(QRectF(x + 92, y, col_w - 110, 16), Qt.AlignVCenter, value)
            p.setFont(_font(11))
            p.setPen(DIM)
            p.drawText(QRectF(x + 92, y + 15, col_w - 110, 14), Qt.AlignVCenter,
                       QFontMetrics(p.font()).elidedText(desc, Qt.ElideRight, int(col_w - 110)))

    def _footer(self, p):
        # who's signed in
        me = prof.load()
        chip = QRectF(52, VH - 62, 370, 44)
        p.setPen(QPen(QColor("#3A4250"), 1.2))
        p.setBrush(QColor(14, 16, 20, 225))
        p.drawRoundedRect(chip, 6, 6)
        pic = None
        if me and me.get("fursona"):
            pr = prof.preset(me["fursona"])
            path = pr.picture() if pr else None
            pic = QPixmap(str(path)) if path else None
        av = QRectF(chip.x() + 6, chip.y() + 6, 32, 32)
        if pic and not pic.isNull():
            p.drawPixmap(av, pic, QRectF(pic.rect()))
        else:
            p.setBrush(QColor("#263042"))
            p.drawRoundedRect(av, 4, 4)
        p.setFont(_font(15, QFont.DemiBold))
        p.setPen(TEXT)
        p.drawText(QRectF(chip.x() + 48, chip.y() + 3, 260, 20), Qt.AlignVCenter, me["name"] if me else "No profile yet")
        self.buttons.append((chip, self.edit_profile))
        line = QRectF(chip.x() + 48, chip.y() + 22, chip.width() - 126, 16)
        if me:                                      # your Furry Code under your name, and a button for both codes
            code = prof.codes(me).get("furcode") or "No Furry Code yet - click CODES to make one"
            mono = QFont("Consolas")
            mono.setPixelSize(11)
            p.setFont(mono)
            p.setPen(QColor("#C8D8FF"))
            p.drawText(line, Qt.AlignVCenter, QFontMetrics(mono).elidedText(code, Qt.ElideRight, int(line.width())))
            self._button(p, QRectF(chip.right() - 72, chip.y() + 9, 64, 26), "CODES", self.edit_codes, "#8FB4FF",
                         small=True)
        else:
            p.setFont(_font(11, QFont.Normal, 0.5))
            p.setPen(DIM)
            p.drawText(line, Qt.AlignVCenter, "TIMELINE IDENTITY - click to change")
        # the centre buttons, on a trapezoid (a little right of centre: clear of the profile chip)
        cx, w = VW / 2 + 20, 570
        tray = QPolygonF([QPointF(cx - w / 2 - 24, VH), QPointF(cx - w / 2, VH - 52), QPointF(cx + w / 2, VH - 52),
                          QPointF(cx + w / 2 + 24, VH)])
        p.setPen(QPen(QColor("#3A4250"), 1.2))
        p.setBrush(QColor(14, 16, 20, 230))
        p.drawPolygon(tray)
        for i, (text, action) in enumerate((("HELP", self.help), ("PROFILE", self.edit_profile),
                                            ("BACKUP", self.backups), ("APPS", self.apps_window),
                                            ("MANUAL", self.manual), ("POWER OFF", self.close))):
            self._button(p, QRectF(cx - 279 + i * 94, VH - 40, 88, 28), text, action, "#8FB4FF", small=True)
        self._selfcheck_chip(p)
        # date and time
        box = QRectF(VW - 300, VH - 50, 300, 50)
        path = QPainterPath(QPointF(box.x(), box.bottom()))
        path.lineTo(box.x() + 22, box.y())
        path.lineTo(box.right(), box.y())
        path.lineTo(box.right(), box.bottom())
        path.closeSubpath()
        p.drawPath(path)
        now = time.localtime()
        p.setFont(_font(16, QFont.Normal, 1))
        p.setPen(TEXT)
        clock = time.strftime("%I:%M %p", now).lstrip("0")
        p.drawText(box.adjusted(30, 0, -18, 0), Qt.AlignRight | Qt.AlignVCenter,
                   f"{time.strftime('%b', now).upper()} {now.tm_mday}, {now.tm_year}  |  {clock}")

    # ---- actions -------------------------------------------------------------------------------------------
    def _first_run(self):
        if prof.load() is None:
            self.edit_profile(first=True)

    def edit_profile(self, first=False):
        dlg = ProfileDialog(self, prof.load() or prof.suggestion(), first)
        dlg.exec()
        self.update()

    def edit_codes(self):
        me = prof.load()
        if me is None:
            return
        pr = prof.preset(me.get("fursona")) if me.get("fursona") else None
        dlg = CodesDialog(self, prof.codes(me), pr.codes if pr else None)
        if dlg.exec():
            prof.save_codes(dlg.codes())
        self.update()

    def help(self):
        box = QMessageBox(self)
        box.setWindowTitle("SYSTEC Help")
        box.setStyleSheet(DIALOG_CSS)
        box.setText(
            "<b>SYSTEC Multi-Boot Manager</b><br><br>"
            "Pick a computer and choose <b>Load This Computer</b> (or double-click it).<br><br>"
            "<b>Load and Format</b> starts that computer's System Recovery to reinstall Windows. It erases only that "
            "computer's own files - mail, memories, settings. Your Timeline identity and your game saves are kept.<br><br>"
            "<b>Config</b> shows the machine's specs and where its Local Storage (drive E:) is - point it at your "
            "external drive to use the full archive.<br><br>"
            "<b>Profile</b> is who you are in every era: your name and fursona. Each computer's Setup takes it from "
            "here.<br><br><b>Your codes</b> (the Furry / YIFF panel above your name - click it) decide how the "
            "residents get along with you: attraction, roleplay, what you have in common. A fursona comes with "
            "defaults; change them any time.<br><br><b>Backup</b> saves your saves, each computer's data, your profile and "
            "your Kithylin chats into one zip, and restores them. <b>Apps</b> runs Kithylin AI, Soul and Song, ClaudeRPG and "
            "the two code studios on their own, without a computer around them. <b>Manual</b> is the whole guide to "
            "the Timeline.<br><br>"
            "Keys: arrows pick a computer, Enter loads it, F11 full screen, Esc goes back.")
        box.exec()

    def manual(self):
        """The Claude Timeline Manual (the Manual folder's pages) in a window of its own."""
        from manual import ManualView, manual_icon
        win = getattr(self, "_manual", None)
        if win is None or not win.isVisible():
            win = ManualView()
            win.setWindowTitle("Claude Manual")
            win.setWindowIcon(manual_icon())
            win.resize(1120, 740)
            self._manual = win
        win.show()
        win.raise_()
        win.activateWindow()

    def config(self, system):
        ConfigDialog(self, system).exec()

    # ---- the standalone apps ------------------------------------------------------------------------------
    def apps_window(self):
        """APPS: programs that run on their own, without a computer around them."""
        win = getattr(self, "_apps", None)
        if win is None or not win.isVisible():
            win = AppsWindow(self)
            self._apps = win
        win.show()
        win.raise_()
        win.activateWindow()

    def app_running(self, key):
        proc = self.apps.get(key)
        return proc is not None and proc.poll() is None

    def computer_running(self):
        return self.process is not None and self.process.poll() is None

    def start_app(self, key):
        """Start one in a process of its own. Returns what to tell the user ('' when it's starting)."""
        from claudecore import standalone as S
        name = S.APPS[key][0]
        if self.app_running(key):
            return f"{name} is already open."
        if key in S.SHARED_FILES and self.computer_running():
            return (f"Not while {self.running.key} is running: {name} keeps the same files inside it. Shut the "
                    "computer down first.")
        python = SYSTEMS[0].python()                 # (the computers' Python: their packages, on any PC)
        env = dict(os.environ)
        if any(folder in python.parents for folder in PORTABLE_PYTHONS):
            env["PYTHONNOUSERSITE"] = "1"
        if key == "kithylinai":
            args, cwd = [str(python), "-m", "kithylinai"], TIMELINE / "ClaudeApps"
        else:
            args, cwd = [str(python), "-m", "claudecore.standalone", key], TIMELINE / "ClaudeCore"
        try:
            self.apps[key] = subprocess.Popen(args, cwd=str(cwd), env=env)
        except OSError as exc:
            return f"{name} couldn't start: {exc}"
        return ""

    def load(self, system, format_drive=False):
        if self.process is not None or not system.installed:
            return
        from claudecore import standalone as S
        open_alone = [S.APPS[k][0] for k in S.SHARED_FILES if self.app_running(k)]
        if open_alone:
            box = QMessageBox(QMessageBox.Question, "SYSTEC",
                              f"{' and '.join(open_alone)} {'is' if len(open_alone) == 1 else 'are'} open on "
                              f"{'its' if len(open_alone) == 1 else 'their'} own. Inside {system.key} the same "
                              "files are used - close it first, or boot anyway?", parent=self)
            boot = box.addButton("BOOT ANYWAY", QMessageBox.AcceptRole)
            box.addButton("CANCEL", QMessageBox.RejectRole)
            box.setStyleSheet(DIALOG_CSS)
            box.exec()
            if box.clickedButton() is not boot:
                return
        if not self._clear_to_boot(system):
            return
        if prof.load() is None:
            self.edit_profile(first=True)
            if prof.load() is None:
                return
        style = None
        if format_drive:
            box = FormatDialog(self, system)
            if box.exec() != QDialog.Accepted:
                return
            style = box.style()
        env = dict(os.environ, CLAUDE_TIMELINE="1")
        python = system.python()
        if any(folder in python.parents for folder in PORTABLE_PYTHONS):
            env["PYTHONNOUSERSITE"] = "1"          # only the Timeline's own packages, not this PC's
        if format_drive:
            env["CLAUDE_TIMELINE_FORMAT"] = "1"
            if style:
                env["CLAUDE_TIMELINE_PERSONA_STYLE"] = style
        try:
            self.process = subprocess.Popen([str(python), str(system.path / "main.py")],
                                            cwd=str(system.path), env=env)
        except OSError as exc:
            QMessageBox.critical(self, "SYSTEC", f"Could not start {system.key}:\n{exc}")
            return
        self.running = system
        self.watch.start(1000)
        QTimer.singleShot(1500, self.showMinimized)

    # ---- the self-check -----------------------------------------------------------------------------------------
    def _start_selfcheck(self):
        import threading
        from claudecore import selfcheck

        def work():
            try:
                self.checks = selfcheck.run()
            except Exception:
                self.checks = []
        threading.Thread(target=work, daemon=True).start()

    def _selfcheck_chip(self, p):
        r = QRectF(VW - 300, VH - 82, 300, 26)
        if self.checks is None:
            text, colour = "SELF-CHECK  ...", DIM
        else:
            errors = sum(1 for f in self.checks if f.level == "error")
            warnings = sum(1 for f in self.checks if f.level == "warning")
            if errors:
                text, colour = f"SELF-CHECK  {errors} PROBLEM{'S' if errors > 1 else ''}", QColor("#FF6A6A")
            elif warnings:
                text, colour = f"SELF-CHECK  {warnings} WARNING{'S' if warnings > 1 else ''}", QColor("#FFC86A")
            else:
                text, colour = "SELF-CHECK  OK", QColor("#7AE0A0")
        p.setFont(_font(12, QFont.Medium, 1.0))
        p.setPen(QColor(colour) if not isinstance(colour, QColor) else colour)
        p.drawText(r.adjusted(0, 0, -18, 0), Qt.AlignRight | Qt.AlignVCenter, text)
        if self.checks is not None:
            self.buttons.append((r, self.show_selfcheck))

    def show_selfcheck(self, findings=None, ask_for=None):
        """The findings in a dialog. ask_for: a computer about to boot - then it's 'boot anyway?'. Returns True to boot."""
        from claudecore import selfcheck
        findings = self.checks if findings is None else findings
        dlg = QDialog(self)
        dlg.setWindowTitle("Self-check")
        dlg.setStyleSheet(DIALOG_CSS)
        dlg.setMinimumWidth(620)
        lay = QVBoxLayout(dlg)
        title = QLabel("SELF-CHECK" if ask_for is None else f"{ask_for.key} HAS A PROBLEM")
        title.setObjectName("title")
        lay.addWidget(title)
        colours = {"error": "#FF6A6A", "warning": "#FFC86A", "info": "#8FB4FF"}
        rows = "".join(f"<p><b style='color:{colours.get(f.level, '#E8ECF2')}'>{f.level.upper()}</b>&nbsp; {f.message}"
                       + (f"<br><span style='color:#8A94A6'>{f.advice}</span>" if f.advice else "") + "</p>"
                       for f in (findings or []))
        body = QLabel(rows or "<p>Everything checks out.</p>")
        body.setWordWrap(True)
        body.setTextFormat(Qt.RichText)
        lay.addWidget(body)
        row = QHBoxLayout()
        row.addStretch(1)
        go = None
        if ask_for is not None:
            go = QPushButton("BOOT ANYWAY")
            go.clicked.connect(dlg.accept)
            row.addWidget(go)
        again = QPushButton("CHECK AGAIN")
        again.clicked.connect(lambda: (dlg.reject(), self._recheck()))
        row.addWidget(again)
        close = QPushButton("CANCEL" if ask_for is not None else "CLOSE")
        close.clicked.connect(dlg.reject)
        row.addWidget(close)
        lay.addLayout(row)
        return dlg.exec() == QDialog.Accepted and ask_for is not None

    def _recheck(self):
        self.checks = None
        self._start_selfcheck()
        self.update()

    def _clear_to_boot(self, system):
        """Before booting: the quick checks again (things may have changed since start-up) plus the code check's
        result; anything that would stop this computer is shown first."""
        from claudecore import backup as B
        from claudecore import selfcheck
        area = B.ERA_PART.get(system.year)
        if area is None:
            return True
        findings = selfcheck.run(quick=True)
        if self.checks is not None:                      # keep the code errors the full check found
            findings += [f for f in self.checks if f.message.startswith("A code error")]
        else:
            findings += selfcheck.check_code()
        stops = selfcheck.blocking(findings, area)
        if not stops:
            return True
        return self.show_selfcheck(stops, ask_for=system)

    def backups(self):
        from claudecore import backup as B
        from claudecore.backup_ui import BackupPanel
        running = self.running if self.process is not None and self.process.poll() is None else None
        blocked = ({B.ERA_PART.get(running.year)} - {None}) | B.SHARED if running is not None else set()
        dlg = QDialog(self)
        dlg.setWindowTitle("Backup and Restore")
        dlg.setStyleSheet(DIALOG_CSS + BACKUP_CSS)
        dlg.setMinimumSize(640, 720)
        lay = QVBoxLayout(dlg)
        title = QLabel("BACKUP AND RESTORE")
        title.setObjectName("title")
        lay.addWidget(title)
        lay.addWidget(BackupPanel(blocked=blocked), 1)
        close = QPushButton("CLOSE")
        close.clicked.connect(dlg.accept)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(close)
        lay.addLayout(row)
        dlg.exec()

    def _auto_backup(self):
        """After a computer shuts down: a quiet backup of the ticked parts, if that's switched on."""
        from claudecore import backup as B
        cfg = B.settings()
        if not cfg.get("auto") or not cfg.get("parts"):
            return
        import threading

        def work():
            try:
                B.create(cfg["parts"], auto=True)
            except Exception:
                pass                       # a failed automatic backup never gets in the way
        threading.Thread(target=work, daemon=True).start()

    def _check_process(self):
        if self.process is None or self.process.poll() is None:
            return
        self.process = None
        self.running = None
        self.watch.stop()
        self._auto_backup()
        self._recheck()
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, e):
        if self.process is not None and self.process.poll() is None:
            box = QMessageBox(QMessageBox.Question, "Power Off",
                              f"{self.running.key} is still running. Leave it running and close the launcher?",
                              QMessageBox.Yes | QMessageBox.Cancel, self)
            box.setStyleSheet(DIALOG_CSS)
            if box.exec() != QMessageBox.Yes:
                e.ignore()
                return
        e.accept()


# ---- dialogs -----------------------------------------------------------------------------------------------
class ProfileDialog(QDialog):
    """Your Timeline identity: a name, and a ready-made fursona (or 'Be unique')."""
    UNIQUE = "__unique__"

    def __init__(self, parent, current, first=False):
        super().__init__(parent)
        self.setWindowTitle("Timeline Identity")
        self.setStyleSheet(DIALOG_CSS)
        self.setMinimumSize(620, 560)
        current = current or {}
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        title = QLabel("WHO ARE YOU IN THE TIMELINE?" if first else "TIMELINE IDENTITY")
        title.setObjectName("title")
        lay.addWidget(title)
        note = QLabel("This is you in every era. Each computer's Setup uses it, so reinstalling Windows never asks "
                      "again. A fursona comes with its own name, picture, photos and online accounts.")
        note.setObjectName("dim")
        note.setWordWrap(True)
        lay.addWidget(note)
        self.list = QListWidget()
        self.list.setIconSize(QSize(56, 56))
        for pr in prof.presets():
            pm = QPixmap(str(pr.picture())) if pr.picture() else QPixmap()
            text = pr.name + (f"  -  {pr.species}" if pr.species else "")
            item = QListWidgetItem(QIcon(pm), text)
            item.setData(Qt.UserRole, pr.id)
            item.setToolTip(pr.summary)
            self.list.addItem(item)
        unique = QListWidgetItem("Be unique  -  your own name, no ready-made fursona")
        unique.setData(Qt.UserRole, self.UNIQUE)
        self.list.addItem(unique)
        lay.addWidget(self.list, 1)
        row = QHBoxLayout()
        row.addWidget(QLabel("Name"))
        self.name = QLineEdit(current.get("name", ""))
        row.addWidget(self.name, 1)
        row.addWidget(QLabel("Online handle"))
        self.handle = QLineEdit(current.get("handle", ""))
        row.addWidget(self.handle, 1)
        lay.addLayout(row)
        self.codes = prof.codes(current)
        own = current.get("codes") or {}
        self.codes_edited = bool(own.get("furcode") or own.get("yiffcode"))
        codes_row = QHBoxLayout()
        self.codes_label = QLabel(_codes_text(self.codes))
        self.codes_label.setWordWrap(True)
        self.codes_label.setStyleSheet(CODES_LABEL_CSS)
        codes_row.addWidget(self.codes_label, 1)
        edit_codes = QPushButton("CODES...")
        edit_codes.setToolTip("Your Furry Code and YIFF Code: encode, decode, change")
        edit_codes.clicked.connect(self._edit_codes)
        codes_row.addWidget(edit_codes)
        lay.addLayout(codes_row)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        cancel = QPushButton("CANCEL")
        cancel.clicked.connect(self.reject)
        save = QPushButton("SAVE")
        save.setDefault(True)
        save.clicked.connect(self._save)
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        lay.addLayout(buttons)
        want = current.get("fursona") or self.UNIQUE
        for i in range(self.list.count()):
            if self.list.item(i).data(Qt.UserRole) == want:
                self.list.setCurrentRow(i)
                self.list.scrollToItem(self.list.item(i), QListWidget.PositionAtCenter)
                break
        self.list.currentItemChanged.connect(self._picked)      # (after: keep a name you chose yourself)

    def _picked(self, item, _prev=None):
        if item is None:
            return
        pr = prof.preset(item.data(Qt.UserRole))
        if pr is not None:
            self.name.setText(pr.name)
            self.handle.setText(pr.handle)
            if not self.codes_edited:                   # a fursona comes with its own codes
                self.codes = dict(pr.codes)
                self.codes_label.setText(_codes_text(self.codes))

    def _edit_codes(self):
        item = self.list.currentItem()
        pr = prof.preset(item.data(Qt.UserRole)) if item else None
        dlg = CodesDialog(self, self.codes, pr.codes if pr else None)
        if dlg.exec():
            self.codes = dlg.codes()
            self.codes_edited = True
            self.codes_label.setText(_codes_text(self.codes))

    def _save(self):
        name = self.name.text().strip()
        if not name:
            self.name.setFocus()
            return
        item = self.list.currentItem()
        pid = item.data(Qt.UserRole) if item else self.UNIQUE
        prof.save(name, None if pid == self.UNIQUE else pid, self.handle.text().strip() or name,
                  self.codes if self.codes_edited else {})
        self.accept()


class CodesDialog(QDialog):
    """Your Furry Code and YIFF Code: type or paste them, or build them in the encoder; the decoder says them in
    words. They decide how the residents get along with you (see ClaudeCore/claudecore/furcodes/steering.py)."""

    def __init__(self, parent, codes, defaults=None):
        super().__init__(parent)
        from claudecore.furcodes.editor import CodesEditor
        self.setWindowTitle("Furry Code and YIFF Code")
        self.setStyleSheet(CODES_CSS)
        self.resize(1080, 720)
        self.defaults = defaults or {}
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 16, 20, 16)
        title = QLabel("FURRY CODE AND YIFF CODE")
        title.setObjectName("title")
        lay.addWidget(title)
        note = QLabel("These codes are you, as far as the residents are concerned: who's attracted to you and who's "
                      "just a friend, who's up for roleplay (and how far), what you have in common. Change them and "
                      "they treat you differently from the next time a computer starts - whatever your history "
                      "together says.")
        note.setObjectName("dim")
        note.setWordWrap(True)
        lay.addWidget(note)
        self.editor = CodesEditor(codes.get("furcode", ""), codes.get("yiffcode", ""))
        lay.addWidget(self.editor, 1)
        buttons = QHBoxLayout()
        if self.defaults:
            reset = QPushButton("FURSONA DEFAULTS")
            reset.setToolTip("Put back the codes that came with your fursona")
            reset.clicked.connect(lambda: self.editor.set_codes(self.defaults))
            buttons.addWidget(reset)
        buttons.addStretch(1)
        cancel = QPushButton("CANCEL")
        cancel.clicked.connect(self.reject)
        save = QPushButton("SAVE")
        save.setDefault(True)
        save.clicked.connect(self.accept)
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        lay.addLayout(buttons)

    def codes(self):
        return self.editor.codes()


def _codes_text(codes):
    fc, yc = (codes or {}).get("furcode", ""), (codes or {}).get("yiffcode", "")
    return f"{fc or '(no Furry Code)'}\n{yc or '(no YIFF Code)'}"


class FormatDialog(QDialog):
    """Load and Format: are you sure - and, for a computer with styles, which Contact Persona Style to install."""

    def __init__(self, parent, system):
        super().__init__(parent)
        self.setWindowTitle("Load and Format")
        self.setStyleSheet(DIALOG_CSS)
        self.setMinimumWidth(560)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        title = QLabel(f"Start {system.key} in System Recovery?")
        title.setObjectName("title")
        lay.addWidget(title)
        note = QLabel("Reinstalling Windows erases this computer's own files: its mail, the residents' memories of "
                      "you there, and its settings (they're moved to Recovery Backups, not deleted).\n\nYour "
                      "Timeline identity and game saves are kept.")
        note.setWordWrap(True)
        lay.addWidget(note)
        self.combo = None
        styles = persona_styles(system)
        if styles:
            lay.addSpacing(10)
            head = QLabel("CONTACT PERSONA STYLE")
            head.setObjectName("title")
            lay.addWidget(head)
            self.combo = QComboBox()
            current = installed_style(system)
            for s_ in styles:
                label = s_["name"] + ("   (installed now)" if s_["id"] == current else "")
                self.combo.addItem(label, s_["id"])
                if s_["id"] == current:
                    self.combo.setCurrentIndex(self.combo.count() - 1)
            lay.addWidget(self.combo)
            self.about = QLabel()
            self.about.setObjectName("dim")
            self.about.setWordWrap(True)
            lay.addWidget(self.about)
            self.styles = {s_["id"]: s_ for s_ in styles}
            self.combo.currentIndexChanged.connect(self._describe)
            self._describe()
        end = QHBoxLayout()
        end.addStretch(1)
        cancel = QPushButton("CANCEL")
        cancel.clicked.connect(self.reject)
        go = QPushButton("FORMAT")
        go.clicked.connect(self.accept)
        end.addWidget(cancel)
        end.addWidget(go)
        lay.addSpacing(8)
        lay.addLayout(end)

    def _describe(self):
        s_ = self.styles.get(self.combo.currentData(), {})
        text = s_.get("description", "")
        if s_.get("created"):
            text += f"  (made {s_['created']})"
        text += ("\n\nHow the residents are made and prompted stays this way until the next format. Choosing a "
                 "different style than the one installed now also starts the residents' memories afresh.")
        self.about.setText(text)

    def style(self):
        return self.combo.currentData() if self.combo is not None else None


def persona_styles(system):
    """The Contact Persona Styles a computer can be set up with (only ClaudeXP has them so far)."""
    if system.year != 2001:
        return []
    base = TIMELINE / "Persona Styles"
    out = []

    def key(p):
        try:
            return tuple(int(x) for x in p.name[1:].split("."))
        except ValueError:
            return (9999,)
    for d in sorted(base.iterdir(), key=key) if base.is_dir() else []:
        meta = prof._load(d / "style.json")
        if meta.get("id"):
            out.append(meta)
    if not out:
        return []
    out.append({"id": "dev", "name": "Development (latest changes)",
                "description": "Whatever the residents and the prompting are right now - where new work happens."})
    return out


def installed_style(system):
    sid = prof._load(system.path / "data" / "persona_style.json").get("style")
    return sid or "1.0"


class ConfigDialog(QDialog):
    """A computer's specs, and where its Local Storage (drive E:) is."""

    def __init__(self, parent, system):
        super().__init__(parent)
        self.setWindowTitle(f"{system.key} - Config")
        self.setStyleSheet(DIALOG_CSS)
        self.setMinimumWidth(640)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        title = QLabel(f"{system.key}  •  {system.os_name}")
        title.setObjectName("title")
        lay.addWidget(title)
        specs = QLabel("<table cellpadding='3'>" + "".join(
            f"<tr><td style='color:#C8CED8'><b>{part}</b></td><td>{value}<br><span style='color:#8A94A6'>{desc}"
            f"</span></td></tr>" for part, value, desc in system.specs) + "</table>")
        specs.setWordWrap(True)
        lay.addWidget(specs)
        lay.addSpacing(10)
        head = QLabel("LOCAL STORAGE (DRIVE E:)")
        head.setObjectName("title")
        lay.addWidget(head)
        note = QLabel("Shared by every computer: the language models, the media archive, ROMs and website rips. "
                      "Point it at your external drive for the full archive.")
        note.setObjectName("dim")
        note.setWordWrap(True)
        lay.addWidget(note)
        row = QHBoxLayout()
        self.path = QLineEdit(self._current())
        self.path.setReadOnly(True)
        row.addWidget(self.path, 1)
        browse = QPushButton("BROWSE...")
        browse.clicked.connect(self._browse)
        reset = QPushButton("DEFAULT")
        reset.clicked.connect(self._reset)
        row.addWidget(browse)
        row.addWidget(reset)
        lay.addLayout(row)
        close = QPushButton("CLOSE")
        close.clicked.connect(self.accept)
        end = QHBoxLayout()
        end.addStretch(1)
        end.addWidget(close)
        lay.addLayout(end)

    @staticmethod
    def _current():
        chosen = prof.setting("local_storage")
        return str(TIMELINE / chosen) if chosen else str(TIMELINE / "Local Storage")     # (relative: inside the Timeline)

    def _browse(self):
        folder = QFileDialog.getExistingDirectory(self, "Where is Local Storage?", self._current())
        if folder:
            try:                         # inside the Timeline: keep it relative, so it moves with the drive
                stored = str(Path(folder).resolve().relative_to(TIMELINE))
            except ValueError:
                stored = folder
            prof.set_setting("local_storage", stored)
            self.path.setText(self._current())

    def _reset(self):
        prof.set_setting("local_storage", None)
        self.path.setText(self._current())


APPS_CSS = DIALOG_CSS + """
QToolButton { background: #1E232C; color: #E8ECF2; border: 1px solid #4A5466; border-radius: 6px; padding: 10px 4px;
              font-family: 'Segoe UI'; font-size: 12px; }
QToolButton:hover { border-color: #8FB4FF; background: #263042; }
QToolButton:checked { border-color: #7AE0A0; }
QComboBox { background: #0C0E12; color: #E8ECF2; border: 1px solid #3A4250; border-radius: 4px; padding: 5px 8px;
            font-family: 'Segoe UI'; font-size: 13px; min-width: 300px; }
QComboBox QAbstractItemView { background: #0C0E12; color: #E8ECF2; selection-background-color: #24324A; }
"""


class AppsWindow(QDialog):
    """APPS: the programs that also run on their own - straight on this PC, without a computer around them, so they
    start quickly and have the graphics card to themselves. Each starts in a process of its own
    (claudecore.standalone; Kithylin AI with its own python -m kithylinai)."""

    def __init__(self, launcher):
        super().__init__(launcher)
        from claudecore import standalone as S
        self.launcher = launcher
        self.setWindowTitle("Apps")
        self.setStyleSheet(APPS_CSS)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 18)
        title = QLabel("APPS")
        title.setObjectName("title")
        lay.addWidget(title)
        note = QLabel("These run on their own, straight on this PC: no computer around them, so they start quickly "
                      "and have the graphics card to themselves. Your Companions, chats, programs and saves are "
                      "the same ones the computers use.")
        note.setObjectName("dim")
        note.setWordWrap(True)
        lay.addWidget(note)
        lay.addSpacing(6)
        row = QHBoxLayout()
        row.setSpacing(10)
        self.tiles = {}
        for key, (name, _module, _open, _icon, what) in S.APPS.items():
            tile = QToolButton()
            tile.setText(name.replace("Copilot ", "Copilot\n").replace("Claude QBasic ", "Claude QBasic\n"))
            tile.setIcon(S.icon(key, 56))
            tile.setIconSize(QSize(56, 56))
            tile.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            tile.setFixedSize(132, 124)
            tile.setCheckable(True)                    # (checked: it's open)
            tile.setToolTip(what)
            tile.setCursor(Qt.PointingHandCursor)
            tile.clicked.connect(lambda _c=False, k=key: self.start(k))
            tile.installEventFilter(self)
            row.addWidget(tile)
            self.tiles[key] = tile
        lay.addLayout(row)
        self.status = QLabel(" ")
        self.status.setObjectName("dim")
        self.status.setWordWrap(True)
        self.status.setMinimumHeight(36)
        lay.addWidget(self.status)
        end = QHBoxLayout()
        settings = QPushButton("SETTINGS")
        settings.setToolTip("The language model the code studios use, and its engine")
        settings.setAutoDefault(False)
        settings.clicked.connect(lambda: AppsSettingsDialog(self).exec())
        end.addWidget(settings)
        end.addStretch(1)
        close = QPushButton("CLOSE")
        close.setDefault(True)
        close.clicked.connect(self.close)
        end.addWidget(close)
        lay.addLayout(end)
        self.watch = QTimer(self)
        self.watch.timeout.connect(self._refresh)
        self.watch.start(1000)
        self._refresh()

    def eventFilter(self, obj, event):
        from PySide6.QtCore import QEvent
        if event.type() == QEvent.Enter:
            from claudecore import standalone as S
            key = next((k for k, t in self.tiles.items() if t is obj), None)
            if key is not None:
                name, _m, _o, _i, what = S.APPS[key]
                self.status.setText(f"<b>{name}</b> - {what}" + ("  (open)" if self.launcher.app_running(key) else ""))
        return False

    def start(self, key):
        from claudecore import standalone as S
        said = self.launcher.start_app(key)
        self.status.setText(said or f"Starting {S.APPS[key][0]}...")
        self._refresh()

    def _refresh(self):
        for key, tile in self.tiles.items():
            tile.setChecked(self.launcher.app_running(key))


class AppsSettingsDialog(QDialog):
    """APPS > Settings: what the code studios' AI runs on when they run on their own (a computer's own choices are
    in its Control Panel > AI Models). Kept in Profile/Standalone Apps."""
    CONTEXTS = [8192, 16384, 32768, 65536]

    def __init__(self, parent):
        super().__init__(parent)
        from claudecore import standalone as S
        S.install()                                    # (this process's own stand-in, for the model settings)
        from claudecore.ai import ai_models, llm_server
        self.ai_models = ai_models
        self.setWindowTitle("Apps - Settings")
        self.setStyleSheet(APPS_CSS)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 18)
        title = QLabel("APPS - SETTINGS")
        title.setObjectName("title")
        lay.addWidget(title)
        note = QLabel("For Copilot Python Studio's AI Helper and Claude QBasic Studio's Vibe Coder when they run on "
                      "their own. Soul and Song and Kithylin AI choose their models in their own Settings.")
        note.setObjectName("dim")
        note.setWordWrap(True)
        lay.addWidget(note)
        cfg = ai_models.config()
        models = [m for m in ai_models.installed() if not m.embedding]
        form = QFormLayout()
        form.setVerticalSpacing(10)
        self.model = QComboBox()
        auto = ai_models.default_for("coding", models)
        auto_title = next((m.title for m in models if m.id == auto), "none installed")
        self.model.addItem(f"Automatic ({auto_title})", "")
        for m in models:
            self.model.addItem(f"{m.title}  ({m.size / 2**30:.1f} GB)", m.id)
        self.model.setCurrentIndex(max(0, self.model.findData(cfg["assign"].get("coding", ""))))
        form.addRow("Coding model", self.model)
        self.engine = QComboBox()
        self.engine.addItem("Automatic", "")
        names = {"vulkan": "Vulkan (any graphics card)", "cuda": "CUDA (NVIDIA)", "cpu": "Processor only",
                 "macos": "Metal (Mac)"}
        for flavour in llm_server.engines():
            self.engine.addItem(names.get(flavour, flavour), flavour)
        self.engine.setCurrentIndex(max(0, self.engine.findData(cfg.get("engine") or "")))
        form.addRow("Engine", self.engine)
        self.context = QComboBox()
        for n in self.CONTEXTS:
            self.context.addItem(f"{n:,} tokens", n)
        self.context.setCurrentIndex(max(0, self.context.findData(int(cfg.get("context") or 16384))))
        form.addRow("Context", self.context)
        lay.addLayout(form)
        where = QHBoxLayout()
        folder = QLabel(f"Their settings are kept in {S.DATA}")
        folder.setObjectName("dim")
        folder.setWordWrap(True)
        where.addWidget(folder, 1)
        show = QPushButton("OPEN")
        show.clicked.connect(lambda: S.reveal(S.DATA.mkdir(parents=True, exist_ok=True) or S.DATA))
        where.addWidget(show)
        lay.addLayout(where)
        end = QHBoxLayout()
        end.addStretch(1)
        cancel = QPushButton("CANCEL")
        cancel.clicked.connect(self.reject)
        save = QPushButton("SAVE")
        save.setDefault(True)
        save.clicked.connect(self._save)
        end.addWidget(cancel)
        end.addWidget(save)
        lay.addLayout(end)

    def _save(self):
        cfg = self.ai_models.config()
        chosen = self.model.currentData()
        if chosen:
            cfg["assign"]["coding"] = chosen
        else:
            cfg["assign"].pop("coding", None)
        cfg["engine"] = self.engine.currentData() or ""
        cfg["context"] = int(self.context.currentData())
        self.ai_models.save(cfg)
        self.accept()
