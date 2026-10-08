"""The current user's name and picture, shared by the Welcome screen and Start menu."""
import getpass
from functools import lru_cache

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPixmap

from .paths import find_image


def user_name():
    return getpass.getuser().capitalize()


@lru_cache(maxsize=None)
def _user_pic():
    path = find_image("userpic")
    pic = QPixmap(str(path)) if path else QPixmap()
    return None if pic.isNull() else pic


def draw_user_picture(p, rect):
    """Draw assets/images/userpic.* into rect, or an orange tile with the user's initial."""
    pic = _user_pic()
    if pic:
        p.drawPixmap(rect, pic)
        return
    grad = QLinearGradient(0, rect.top(), 0, rect.bottom())
    grad.setColorAt(0, QColor("#FFC85A"))
    grad.setColorAt(1, QColor("#F2742B"))
    p.fillRect(QRectF(rect), grad)
    font = QFont("Trebuchet MS")
    font.setPixelSize(max(8, int(rect.height() * 0.55)))
    font.setBold(True)
    p.setFont(font)
    p.setPen(QColor("white"))
    p.drawText(QRectF(rect), Qt.AlignCenter, user_name()[:1])
