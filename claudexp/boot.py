"""The black Windows XP boot screen with the sliding progress chunk."""
from PySide6.QtCore import QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter
from PySide6.QtWidgets import QWidget

from .paths import pixmap

# Inside of the empty progress bar, in winXP_boot.jpg pixel coordinates.
BAR = QRectF(88, 539, 364, 26)


class BootScreen(QWidget):
    finished = Signal()

    def __init__(self, duration_ms=5000, parent=None):
        super().__init__(parent)
        self.logo = pixmap("winXP_boot.jpg")
        self.chunk = pixmap("windowsxp_progress.jpg")
        self.duration_ms = duration_ms
        self.chunk_h = BAR.height() - 4
        self.chunk_w = self.chunk.width() * self.chunk_h / max(1, self.chunk.height())
        self.offset = -self.chunk_w
        self._done = False
        self.noguiboot = False     # BOOT.INI /NOGUIBOOT: a black screen, no logo
        self.sos = False           # BOOT.INI /SOS: the drivers listed as they load
        self.ticks = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)

    def start(self):
        self._done = False
        self.offset = -self.chunk_w
        self.ticks = 0
        from . import startup
        self.noguiboot, self.sos = startup.boot_flag("NOGUIBOOT"), startup.boot_flag("SOS")
        self.timer.start(30)
        QTimer.singleShot(self.duration_ms, self._finish)

    def _tick(self):
        self.ticks += 1
        self.offset += 4
        if self.offset > BAR.width():
            self.offset = -self.chunk_w
        self.update()

    def _finish(self):
        if self._done:
            return
        self._done = True
        self.timer.stop()
        self.finished.emit()

    def mousePressEvent(self, event):
        self._finish()  # click to skip

    def keyPressEvent(self, event):
        self._finish()

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("black"))
        if self.sos:
            self._draw_sos(p)
            return
        if self.noguiboot or self.logo.isNull():
            return
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        s = min(self.width() / self.logo.width(), self.height() / self.logo.height()) * 0.85
        w, h = self.logo.width() * s, self.logo.height() * s
        x, y = (self.width() - w) / 2, (self.height() - h) / 2
        p.drawPixmap(QRectF(x, y, w, h), self.logo, QRectF(self.logo.rect()))

        bar = QRectF(x + BAR.x() * s, y + BAR.y() * s, BAR.width() * s, BAR.height() * s)
        p.setClipRect(bar)
        chunk = QRectF(bar.x() + self.offset * s, bar.y() + 2 * s,
                       self.chunk_w * s, self.chunk_h * s)
        p.drawPixmap(chunk, self.chunk, QRectF(self.chunk.rect()))


    def _draw_sos(self, p):
        """/SOS: XP's boot screen lists each driver's ARC path as it loads."""
        p.setPen(QColor("#C0C0C0"))
        p.setFont(QFont("Lucida Console", 9))
        lines = ["Microsoft (R) Windows XP (TM) (Build 2600)", "1 System Processor [511 MB Memory]  MultiProcessor"
                 " Kernel", ""] + [f"multi(0)disk(0)rdisk(0)partition(1)\\WINDOWS\\{d}" for d in SOS_DRIVERS]
        shown = min(len(lines), 3 + self.ticks // 3)
        y = 30
        for line in lines[:shown]:
            p.drawText(20, y, line)
            y += 15
            if y > self.height() - 20:
                break


SOS_DRIVERS = ["system32\\ntoskrnl.exe", "system32\\hal.dll", "system32\\KDCOM.DLL", "system32\\BOOTVID.dll",
               "system32\\DRIVERS\\ACPI.sys", "system32\\DRIVERS\\WMILIB.SYS", "system32\\DRIVERS\\pci.sys",
               "system32\\DRIVERS\\isapnp.sys", "system32\\DRIVERS\\intelide.sys",
               "system32\\DRIVERS\\PCIIDEX.SYS", "System32\\Drivers\\MountMgr.sys",
               "system32\\DRIVERS\\ftdisk.sys", "System32\\drivers\\dmload.sys", "System32\\drivers\\dmio.sys",
               "System32\\Drivers\\PartMgr.sys", "System32\\Drivers\\VolSnap.sys",
               "system32\\DRIVERS\\atapi.sys", "system32\\DRIVERS\\disk.sys", "system32\\DRIVERS\\CLASSPNP.SYS",
               "System32\\Drivers\\Fs_Rec.SYS", "System32\\Drivers\\KSecDD.sys", "System32\\Drivers\\Ntfs.sys",
               "System32\\Drivers\\NDIS.sys", "System32\\Drivers\\Mup.sys", "system32\\DRIVERS\\agp440.sys",
               "System32\\Drivers\\vga.sys", "System32\\Drivers\\Beep.SYS", "System32\\Drivers\\Null.SYS",
               "system32\\DRIVERS\\audstub.sys", "system32\\DRIVERS\\rasl2tp.sys", "system32\\DRIVERS\\usbuhci.sys",
               "system32\\DRIVERS\\ati2mtag.sys", "system32\\DRIVERS\\smwdm.sys", "system32\\DRIVERS\\e100b325.sys"]


class ShutdownScreen(QWidget):
    """The plain blue 'Windows is shutting down...' screen."""
    text = "Windows is shutting down..."

    def paintEvent(self, event):
        p = QPainter(self)
        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0, QColor("#5A7EDC"))
        grad.setColorAt(1, QColor("#3557C4"))
        p.fillRect(self.rect(), grad)
        font = QFont("Trebuchet MS", 16)
        font.setBold(True)
        p.setFont(font)
        p.setPen(QColor("#1E3A8A"))
        p.drawText(self.rect().translated(1, 1), Qt.AlignCenter, self.text)
        p.setPen(QColor("white"))
        p.drawText(self.rect(), Qt.AlignCenter, self.text)
