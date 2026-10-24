"""Draws the SYSTEC emblem (the launcher's own window icon) into ClaudeLauncher/exe/systec.ico for the .exe.
An .ico is a little directory of images: here PNGs at 16, 24, 32, 48, 64 and 256 pixels."""
import os
import struct
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QPointF, Qt  # noqa: E402
from PySide6.QtGui import QPainter, QPixmap  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

app = QApplication(sys.argv)
from systec.ui import _emblem  # noqa: E402

images = []
for size in (16, 24, 32, 48, 64, 256):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    _emblem(p, QPointF(size / 2, size / 2), size * 0.46, size >= 48)
    p.end()
    data = QByteArray()
    buf = QBuffer(data)
    buf.open(QIODevice.WriteOnly)
    pm.save(buf, "PNG")
    images.append((size, bytes(data)))

out = struct.pack("<HHH", 0, 1, len(images))
offset = 6 + 16 * len(images)
for size, png in images:
    out += struct.pack("<BBBBHHII", size % 256, size % 256, 0, 0, 1, 32, len(png), offset)
    offset += len(png)
out += b"".join(png for _, png in images)
(HERE / "systec.ico").write_bytes(out)
print(f"wrote {HERE / 'systec.ico'} ({len(out)} bytes)")
