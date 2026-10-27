"""The program's screen in the studio: the Screen's visible page, scaled to a 4:3 picture the way a CRT showed every
mode, with INPUT's blinking cursor; and the keyboard, turned into what INKEY$ gives (CHR$(0) + a scan code for the
arrows, F-keys and the rest)."""
from PySide6.QtCore import QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtWidgets import QWidget

SPECIAL = {Qt.Key_Up: "\x00H", Qt.Key_Down: "\x00P", Qt.Key_Left: "\x00K", Qt.Key_Right: "\x00M",
           Qt.Key_Home: "\x00G", Qt.Key_End: "\x00O", Qt.Key_PageUp: "\x00I", Qt.Key_PageDown: "\x00Q",
           Qt.Key_Insert: "\x00R", Qt.Key_Delete: "\x00S", Qt.Key_F1: "\x00;", Qt.Key_F2: "\x00<", Qt.Key_F3: "\x00=",
           Qt.Key_F4: "\x00>", Qt.Key_F5: "\x00?", Qt.Key_F6: "\x00@", Qt.Key_F7: "\x00A", Qt.Key_F8: "\x00B",
           Qt.Key_F9: "\x00C", Qt.Key_F10: "\x00D", Qt.Key_F11: "\x00\x85", Qt.Key_F12: "\x00\x86",
           Qt.Key_Return: "\r", Qt.Key_Enter: "\r", Qt.Key_Backspace: "\x08", Qt.Key_Escape: "\x1b",
           Qt.Key_Tab: "\t"}


class ScreenView(QWidget):
    """Shows a screen.Screen; keys typed go to on_key (the running program's key buffer)."""
    stop_requested = Signal()

    def __init__(self, scr=None):
        super().__init__()
        self.scr = scr
        self.on_key = None
        self.image = None
        self.seen = -1
        self.cursor = None
        self.blink = True
        self.message = ""                       # shown under the picture: "Press a key..." and the like
        self.setFocusPolicy(Qt.StrongFocus)
        self.setAttribute(Qt.WA_OpaquePaintEvent)
        self.setMinimumSize(160, 120)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._refresh)
        self.timer.start(16)
        self.blinker = QTimer(self)
        self.blinker.timeout.connect(self._blink)
        self.blinker.start(250)

    def set_screen(self, scr):
        self.scr = scr
        self.seen = -1
        self._refresh()

    def _blink(self):
        self.blink = not self.blink
        if self.cursor:
            self.update()

    def _refresh(self):
        scr = self.scr
        if scr is None:
            return
        cursor_now = scr.cursor_on
        if scr.version == self.seen and (self.cursor is not None) == cursor_now:
            return
        self.seen = scr.version
        w, h, data, pal, cur, _mode = scr.snapshot()
        img = QImage(data, w, h, w, QImage.Format_Indexed8)
        img.setColorTable([0xFF000000 | c for c in pal[:256]])
        self.image = img.copy()
        self.cursor = cur
        self.update()

    def picture_rect(self):
        """Where the picture goes: as big as fits, 4:3."""
        W, H = self.width(), self.height()
        if W * 3 > H * 4:
            ph = H
            pw = H * 4 / 3
        else:
            pw = W
            ph = W * 3 / 4
        return QRectF((W - pw) / 2, (H - ph) / 2, pw, ph)

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#000000"))
        if self.image is None:
            return
        r = self.picture_rect()
        p.drawImage(r, self.image)
        if self.cursor and self.blink:
            x, y, cw, ch, fg = self.cursor
            sx, sy = r.width() / self.image.width(), r.height() / self.image.height()
            p.fillRect(QRectF(r.x() + x * sx, r.y() + (y + ch - max(2, ch // 8)) * sy, cw * sx, max(2, ch // 8) * sy),
                       QColor("#AAAAAA"))
        if self.message:
            p.setPen(QColor("#AAAAAA"))
            p.drawText(self.rect().adjusted(4, 0, -4, -4), Qt.AlignBottom | Qt.AlignHCenter, self.message)
        if self.hasFocus() is False and self.on_key is not None:
            p.setPen(QColor(255, 255, 85, 160))
            p.drawText(self.rect().adjusted(4, 4, -4, -4), Qt.AlignTop | Qt.AlignRight, "click here to type")

    def keyPressEvent(self, event):
        if self.on_key is None:
            return super().keyPressEvent(event)
        key, mods = event.key(), event.modifiers()
        if mods & Qt.ControlModifier and key in (Qt.Key_Pause, Qt.Key_Cancel, Qt.Key_C) and key != Qt.Key_C:
            self.stop_requested.emit()
            return
        if key == Qt.Key_Pause or (mods & Qt.ControlModifier and key == Qt.Key_Break):
            self.stop_requested.emit()
            return
        if key in SPECIAL:
            self.on_key(SPECIAL[key])
            return
        text = event.text()
        if text:
            for ch in text:
                if ord(ch) < 256:
                    self.on_key(ch)
                else:
                    try:
                        self.on_key(ch.encode("cp437").decode("latin-1"))
                    except UnicodeEncodeError:
                        pass

    def focusInEvent(self, event):
        self.update()
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        self.update()
        super().focusOutEvent(event)

    def mousePressEvent(self, event):
        self.setFocus()
