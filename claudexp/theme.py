"""Visual styles and themes, like XP's Display Properties > Themes / Appearance.

A *visual style* draws the window frames, the taskbar and the Start menu:
  luna     - Windows XP style, in Default (blue), Olive Green or Silver (the Luna artwork is recoloured for the
             other two and cached in data/theme_cache)
  classic  - Windows Classic style, with the Windows 2000 colour schemes (Brick, Desert, Rainy Day...)
  watercolor, aquax, chromehex - unsigned third-party styles; Windows only loads them once StyleXP has patched
             uxtheme.dll (see programs/stylexp.py)
A *theme* (themes.py) bundles a visual style with a wallpaper, a sound scheme, pointers and a screen saver.

The choice lives in data/display.json under "theme". Hosted programs (ClaudeAIM) keep their own colours: only
ClaudeXP's own windows get a Classic scheme's palette, their frames are themed like any other window."""
import colorsys
import math

from PySide6.QtCore import QObject, QPoint, QPointF, QRect, QRectF, Qt, Signal
from PySide6.QtGui import (QColor, QFont, QImage, QLinearGradient, QPainter, QPainterPath, QPalette, QPen, QPixmap,
                           QPolygonF)

from .paths import DATA, IMAGES

CACHE = DATA / "theme_cache"
DEFAULT = {"style": "luna", "scheme": "blue", "font": "normal", "name": "Windows XP",
           "sounds": "Windows Default", "cursors": "Windows Default"}
FONT_SIZES = [("normal", "Normal"), ("large", "Large Fonts"), ("xlarge", "Extra Large Fonts")]
FONT_BUMP = {"normal": 0, "large": 3, "xlarge": 6}
HACKED = ("watercolor", "aquax", "chromehex")          # need StyleXP's patched uxtheme.dll


class _Notifier(QObject):
    changed = Signal()


notifier = _Notifier()


def _c(x):
    return x if isinstance(x, QColor) else QColor(x)


def _grad(p0, p1, stops):
    g = QLinearGradient(p0, p1)
    for at, col in stops:
        g.setColorAt(at, _c(col))
    return g


# ---- recolouring the Luna artwork ------------------------------------------------------------------------------

def _shift(r, g, b, scheme):
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    if not (0.50 <= h <= 0.74 and s > 0.08):
        return r, g, b
    if scheme == "olive":
        h, s, v = 0.205, min(1.0, s * 0.62), v * 0.86
    elif v < 0.4:                                                  # silver: dark text stays dark
        h, s = 0.67, s * 0.15
    else:
        h, s, v = 0.67, s * 0.12, min(1.0, 0.40 + v * 0.56)
    rr, gg, bb = colorsys.hsv_to_rgb(h, s, v)
    return round(rr * 255), round(gg * 255), round(bb * 255)


def shift_color(color, scheme):
    c = _c(color)
    if scheme == "blue":
        return c
    return QColor(*_shift(c.red(), c.green(), c.blue(), scheme))


def recolored(name, scheme):
    """assets/images/<name> with its blues turned olive or silver (green Start button and white text stay)."""
    if scheme == "blue":
        return QPixmap(str(IMAGES / name))
    out = CACHE / f"{scheme}2_{name.rsplit('.', 1)[0]}.png"
    if out.exists():
        pm = QPixmap(str(out))
        if not pm.isNull():
            return pm
    img = QImage(str(IMAGES / name)).convertToFormat(QImage.Format_RGB32)
    w, h, bpl = img.width(), img.height(), img.bytesPerLine()
    buf = bytearray(img.constBits().tobytes())
    memo = {}
    for i in range(0, len(buf), 4):
        key = (buf[i], buf[i + 1], buf[i + 2])                     # B, G, R
        val = memo.get(key)
        if val is None:
            r, g, b = _shift(key[2], key[1], key[0], scheme)
            val = memo[key] = (b, g, r)
        buf[i], buf[i + 1], buf[i + 2] = val
    res = QImage(bytes(buf), w, h, bpl, QImage.Format_RGB32).copy()
    try:
        CACHE.mkdir(parents=True, exist_ok=True)
        res.save(str(out))
    except OSError:
        pass
    return QPixmap.fromImage(res)


# ---- shared drawing bits ---------------------------------------------------------------------------------------

def bevel(p, r, raised=True, face=None, light="#FFFFFF", shadow="#808080", dark="#404040"):
    """A Windows Classic 3D edge (two lines each side)."""
    r = QRectF(r)
    if face is not None:
        p.fillRect(r, _c(face))
    tl1, br1 = (light, dark) if raised else (shadow, light)
    tl2, br2 = (None, shadow) if raised else (dark, None)
    p.save()
    p.setRenderHint(QPainter.Antialiasing, False)
    x0, y0, x1, y1 = r.left(), r.top(), r.right() - 1, r.bottom() - 1
    p.setPen(_c(tl1))
    p.drawLine(QPointF(x0, y0), QPointF(x1, y0))
    p.drawLine(QPointF(x0, y0), QPointF(x0, y1))
    p.setPen(_c(br1))
    p.drawLine(QPointF(x0, y1), QPointF(x1, y1))
    p.drawLine(QPointF(x1, y0), QPointF(x1, y1))
    if tl2:
        p.setPen(_c(tl2))
        p.drawLine(QPointF(x0 + 1, y0 + 1), QPointF(x1 - 1, y0 + 1))
        p.drawLine(QPointF(x0 + 1, y0 + 1), QPointF(x0 + 1, y1 - 1))
    if br2:
        p.setPen(_c(br2))
        p.drawLine(QPointF(x0 + 1, y1 - 1), QPointF(x1 - 1, y1 - 1))
        p.drawLine(QPointF(x1 - 1, y0 + 1), QPointF(x1 - 1, y1 - 1))
    p.restore()


def glyph(p, rect, kind, color, maximized=False, weight=1.0):
    """Minimize / maximize / restore / close marks, scaled to the button."""
    r = QRectF(rect)
    s = min(r.width(), r.height())
    cx, cy = r.center().x(), r.center().y()
    col = _c(color)
    p.save()
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(Qt.NoBrush)
    if kind == "min":
        p.fillRect(QRectF(cx - s * 0.22, cy + s * 0.12, s * 0.38, max(2.0, s * 0.13 * weight)), col)
    elif kind == "max":
        if maximized:
            p.setPen(QPen(col, max(1.0, s * 0.06)))
            p.drawRect(QRectF(cx - s * 0.12, cy - s * 0.28, s * 0.38, s * 0.32))
            p.fillRect(QRectF(cx - s * 0.12, cy - s * 0.28, s * 0.38, max(1.5, s * 0.08)), col)
            p.drawRect(QRectF(cx - s * 0.28, cy - s * 0.08, s * 0.38, s * 0.32))
            p.fillRect(QRectF(cx - s * 0.28, cy - s * 0.08, s * 0.38, max(1.5, s * 0.08)), col)
        else:
            p.setPen(QPen(col, max(1.0, s * 0.06)))
            p.drawRect(QRectF(cx - s * 0.25, cy - s * 0.25, s * 0.5, s * 0.48))
            p.fillRect(QRectF(cx - s * 0.25, cy - s * 0.25, s * 0.5, max(2.0, s * 0.1 * weight)), col)
    else:
        p.setPen(QPen(col, max(1.5, s * 0.1 * weight), Qt.SolidLine, Qt.FlatCap))
        d = s * 0.22
        p.drawLine(QPointF(cx - d, cy - d), QPointF(cx + d, cy + d))
        p.drawLine(QPointF(cx + d, cy - d), QPointF(cx - d, cy + d))
    p.restore()


def windows_flag(p, r):
    """The four-colour wavy Windows flag (for Classic's Start button and the like)."""
    p.save()
    p.setRenderHint(QPainter.Antialiasing)
    w, h = r.width() / 2 - 0.5, r.height() / 2 - 0.5
    for (dx, dy), col in (((0, 0), "#F03C1C"), ((1, 0), "#3CB43C"), ((0, 1), "#2A6CF0"), ((1, 1), "#F8C81C")):
        x, y = r.left() + dx * (w + 1), r.top() + dy * (h + 1)
        path = QPainterPath()
        path.moveTo(x, y + 1)
        path.cubicTo(x + w * 0.4, y - 0.5, x + w * 0.6, y + 2, x + w, y + 0.5)
        path.lineTo(x + w, y + h)
        path.cubicTo(x + w * 0.6, y + h + 1.5, x + w * 0.4, y + h - 1, x, y + h + 0.5)
        path.closeSubpath()
        p.fillPath(path, _c(col))
    p.restore()


# ---- the styles --------------------------------------------------------------------------------------------------

class Style:
    """What every visual style provides. Sizes are in desktop pixels."""
    key = ""
    name = ""
    base_title_h = 30
    border = 4
    task_text = "white"
    tray_text = "white"
    sm_text, sm_sub = "#000000", "#7F7F7F"
    sm_hover, sm_hover_text = "#316AC5", "white"
    sm_name, sm_name_shadow = "white", "#0F2C8C"
    sm_footer_text = "white"

    def __init__(self, scheme, font="normal"):
        self.scheme = scheme
        self.font = font

    @property
    def title_h(self):
        return self.base_title_h + FONT_BUMP.get(self.font, 0)

    def title_font(self):
        f = QFont("Trebuchet MS", 10 + FONT_BUMP.get(self.font, 0) // 2)
        f.setBold(True)
        return f

    def palette(self):
        """A QPalette for ClaudeXP's own window contents, or None to keep the app's."""
        return None

    def desktop_color(self):
        return None

    # -- the window frame
    def button_rects(self, w, buttons):
        s = 21 + FONT_BUMP.get(self.font, 0)
        y = (self.title_h - s) // 2 + 1
        x = w - self.border - 2 - s
        rects = {}
        for kind in ("close", "max", "min"):
            if kind in buttons:
                rects[kind] = QRect(x, y, s, s)
                x -= s + 2
        return rects

    def paint_frame(self, p, w, h, title, icon, active, buttons, maximized=False, hover=None, press=None):
        raise NotImplementedError

    def _title_text(self, p, rect, title, color, shadow=None, align=Qt.AlignLeft):
        p.setFont(self.title_font())
        text = p.fontMetrics().elidedText(title, Qt.ElideRight, max(0, rect.width()))
        if shadow is not None:
            p.setPen(_c(shadow))
            p.drawText(rect.translated(1, 1), Qt.AlignVCenter | align, text)
        p.setPen(_c(color))
        p.drawText(rect, Qt.AlignVCenter | align, text)

    # -- the taskbar
    def start_width(self):
        return 97

    def task_text_color(self, pressed):
        return self.task_text

    def paint_taskbar(self, p, rect, start, menu_open):
        raise NotImplementedError

    def paint_task_button(self, p, rect, pressed):
        raise NotImplementedError

    def paint_tray(self, p, rect):
        raise NotImplementedError

    # -- the Start menu
    def paint_start_menu(self, p, menu):
        raise NotImplementedError

    def menu_css(self):
        return ("QMenu { background: white; border: 1px solid #7A96DF; font-family: Tahoma; font-size: 11px; }"
                " QMenu::item { padding: 5px 24px 5px 8px; }"
                " QMenu::item:selected { background: #316AC5; color: white; }"
                " QMenu::item:disabled { color: #ACA899; }"
                " QMenu::separator { height: 1px; background: #ACA899; margin: 3px 2px; }")


# ---- Windows XP style (Luna) ---------------------------------------------------------------------------------

LUNA = {
    "blue": dict(frame=("#0831D9", "#7B97E0"),
                 title=([(0, "#3D95FF"), (0.1, "#0A62F4"), (0.5, "#0055E5"), (0.9, "#0047D7"), (1, "#003DB6")],
                        [(0, "#B9CEF6"), (0.15, "#9DB9EB"), (0.6, "#94AFE8"), (1, "#7B97E0")]),
                 text=("white", "#E2EAFA"), shadow="#0A1F7A",
                 btn=("#4C8DFF", "#1E5EE6"), btn_hover=("#6FA6FF", "#2C6CF0"), btn_inactive=("#C4D3F5", "#9DB2E8"),
                 glyph="white", edge="white",
                 tray=("#1C98EB", "#0F8CE8", "#0F82DE"), tray_edge=("#0A5BC5", "#3BB6FF"),
                 task_text="white", tray_text="white", task_down=(0, 20, 100, 90),
                 sm_hover="#316AC5", sm_hover_text="white", sm_name="white", sm_name_shadow="#0F2C8C",
                 sm_footer_text="white", menu=("#316AC5", "white", "#7A96DF")),
    "olive": dict(frame=("#7A9254", "#C2CCA4"),
                  title=([(0, "#D2DDAB"), (0.1, "#A9BC7C"), (0.5, "#97AC69"), (0.9, "#8CA25C"), (1, "#7A9254")],
                         [(0, "#EEF2DF"), (0.15, "#E2E9CC"), (0.6, "#DCE4C2"), (1, "#C6D2A2")]),
                  text=("white", "#F6F8EE"), shadow="#4A5A2C",
                  btn=("#B4C88A", "#7F9A50"), btn_hover=("#C8DAA0", "#8EAA5E"), btn_inactive=("#E2E9CC", "#CBD6AC"),
                  glyph="white", edge="white",
                  tray=("#DCE5BC", "#CEDAA8", "#C2D096"), tray_edge=("#94A86A", "#EEF3DC"),
                  task_text="white", tray_text="black", task_down=(50, 70, 10, 90),
                  sm_hover="#93A070", sm_hover_text="white", sm_name="white", sm_name_shadow="#4A5A2C",
                  sm_footer_text="white", menu=("#93A070", "white", "#A3B47C")),
    "silver": dict(frame=("#A8A8BC", "#DADAE4"),
                   title=([(0, "#FFFFFF"), (0.1, "#EDEDF3"), (0.5, "#DCDCE7"), (0.9, "#CBCBDA"), (1, "#ACACC0")],
                          [(0, "#FDFDFE"), (0.15, "#F6F6F9"), (0.6, "#F0F0F4"), (1, "#E4E4EC")]),
                   text=("#1A1A2E", "#9A9AAE"), shadow="#FFFFFF",
                   btn=("#FFFFFF", "#C6C6D6"), btn_hover=("#FFFFFF", "#DCDCEA"), btn_inactive=("#FAFAFC", "#E8E8EE"),
                   glyph="#303050", edge="#8A8AA0",
                   tray=("#F8F8FB", "#E6E6EE", "#D6D6E2"), tray_edge=("#9A9AAE", "#FFFFFF"),
                   task_text="black", tray_text="black", task_down=(0, 0, 40, 45),
                   sm_hover="#8A90AC", sm_hover_text="white", sm_name="#1A1A2E", sm_name_shadow="#FFFFFF",
                   sm_footer_text="#1A1A2E", menu=("#8A90AC", "white", "#9A9AAE")),
}
LUNA_NAMES = [("blue", "Default (blue)"), ("olive", "Olive Green"), ("silver", "Silver")]


class LunaStyle(Style):
    key, name = "luna", "Windows XP style"

    def __init__(self, scheme="blue", font="normal"):
        super().__init__(scheme if scheme in LUNA else "blue", font)
        self.c = LUNA[self.scheme]
        for attr in ("task_text", "tray_text", "sm_hover", "sm_hover_text", "sm_name", "sm_name_shadow",
                     "sm_footer_text"):
            setattr(self, attr, self.c[attr])
        self._pm = {}

    def pm(self, name):
        if name not in self._pm:
            self._pm[name] = recolored(name, self.scheme)
        return self._pm[name]

    def paint_frame(self, p, w, h, title, icon, active, buttons, maximized=False, hover=None, press=None):
        c, th, b = self.c, self.title_h, self.border
        p.setRenderHint(QPainter.Antialiasing)
        rad = 0 if maximized else 8
        path = QPainterPath()
        path.moveTo(0, h)
        path.lineTo(0, rad)
        path.quadTo(0, 0, rad, 0)
        path.lineTo(w - rad, 0)
        path.quadTo(w, 0, w, rad)
        path.lineTo(w, h)
        path.closeSubpath()
        p.fillPath(path, _c(c["frame"][0 if active else 1]))
        p.save()
        p.setClipPath(path)
        p.fillRect(0, 0, w, th, _grad(QPointF(0, 0), QPointF(0, th), c["title"][0 if active else 1]))
        p.restore()
        x = b + 4
        if icon is not None and not icon.isNull():
            p.drawPixmap(x, (th - 16) // 2, icon.pixmap(16, 16))
            x += 21
        rects = self.button_rects(w, buttons)
        text_w = (min(r.left() for r in rects.values()) if rects else w - b) - x - 4
        self._title_text(p, QRect(x, 0, text_w, th), title, c["text"][0 if active else 1],
                         c["shadow"] if active else None)
        for kind, rect in rects.items():
            self._button(p, rect, kind, active, hover == kind, press == kind and hover == kind, maximized)

    def _button(self, p, rect, kind, active, hot, down, maximized):
        c = self.c
        if kind == "close":
            top, bot = ("#F09A7C", "#D2502E") if hot else ("#E8795A", "#C5371A")
            if not active:
                top, bot = "#E7A894", "#D07A63"
            ink, edge = "white", "white"
        else:
            top, bot = c["btn_hover"] if hot else c["btn"]
            if not active:
                top, bot = c["btn_inactive"]
            ink, edge = c["glyph"], c["edge"]
        if down:
            top, bot = bot, top
        p.setPen(QPen(_c(edge), 1))
        p.setBrush(_grad(QPointF(0, rect.top()), QPointF(0, rect.bottom()), [(0, top), (1, bot)]))
        p.drawRoundedRect(QRectF(rect).adjusted(0.5, 0.5, -0.5, -0.5), 3, 3)
        glyph(p, rect, kind, ink, maximized, weight=1.3)

    # taskbar: the Luna artwork, recoloured
    def start_width(self):
        return self.pm("startbutton.jpg").scaledToHeight(30).width()

    def paint_taskbar(self, p, rect, start, menu_open):
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        tile = self.pm("taskbar_empty.jpg").scaledToHeight(rect.height(), Qt.SmoothTransformation)
        p.drawTiledPixmap(rect, tile)
        p.drawPixmap(start.topLeft(), self.pm("startbutton.jpg").scaledToHeight(rect.height(),
                                                                              Qt.SmoothTransformation))
        if menu_open:
            p.fillRect(start, QColor(0, 40, 0, 70))

    def paint_task_button(self, p, rect, pressed):
        p.drawPixmap(rect, self.pm("taskbar_window.jpg"))
        if pressed:
            p.fillRect(rect.adjusted(1, 1, -1, -1), QColor(*self.c["task_down"]))

    def paint_tray(self, p, rect):
        t = self.c["tray"]
        p.fillRect(rect, _grad(QPointF(0, 0), QPointF(0, rect.height()), [(0, t[0]), (0.5, t[1]), (1, t[2])]))
        p.setPen(_c(self.c["tray_edge"][0]))
        p.drawLine(rect.left(), 0, rect.left(), rect.height())
        p.setPen(_c(self.c["tray_edge"][1]))
        p.drawLine(rect.left() + 1, 0, rect.left() + 1, rect.height())

    def paint_start_menu(self, p, menu):
        from .startmenu import BAKED_HIGHLIGHT
        p.drawPixmap(0, 0, self.pm("startmenu.jpg"))
        p.fillRect(BAKED_HIGHLIGHT, shift_color("#D3E5FA", self.scheme))
        menu._draw_control_panel_item(p)
        menu._draw_help_item(p)

    def menu_css(self):
        sel, sel_text, border = self.c["menu"]
        return (f"QMenu {{ background: white; border: 1px solid {border}; font-family: Tahoma; font-size: 11px; }}"
                " QMenu::item { padding: 5px 24px 5px 8px; }"
                f" QMenu::item:selected {{ background: {sel}; color: {sel_text}; }}"
                " QMenu::item:disabled { color: #ACA899; }"
                " QMenu::separator { height: 1px; background: #ACA899; margin: 3px 2px; }")


# ---- the procedural Start menu (Classic and the third-party styles) -------------------------------------------

RIGHT_ICONS = {"My Documents": "docs", "My Recent Documents": "recent", "My Pictures": "pics", "My Music": "music",
               "My Computer": "computer", "Control Panel": "panel", "Set Program Access and Defaults": "access",
               "Printers and Faxes": "printer", "Search": "search", "Run...": "run", "Help and Support": "help"}
BOLD_RIGHT = {"My Documents", "My Pictures", "My Music", "My Computer"}


def _right_icon(p, kind, r):
    """Small drawn icons for the Start menu's right column."""
    from PySide6.QtWidgets import QApplication, QStyle
    st = QApplication.style()
    which = {"docs": QStyle.SP_DirIcon, "recent": QStyle.SP_DirIcon, "pics": QStyle.SP_DirIcon,
             "music": QStyle.SP_DirIcon, "computer": QStyle.SP_ComputerIcon, "panel": QStyle.SP_DesktopIcon,
             "access": QStyle.SP_ComputerIcon, "printer": QStyle.SP_DriveNetIcon,
             "search": QStyle.SP_FileDialogContentsView, "run": QStyle.SP_DialogOkButton,
             "help": QStyle.SP_MessageBoxQuestion}[kind]
    p.drawPixmap(r, st.standardIcon(which).pixmap(r.size()))


def paint_drawn_start_menu(p, menu, c):
    """The XP two-column Start menu drawn from colours: c has header, left, right, footer, border, sep, text,
    right_text, header_pinstripe (optional)."""
    from .startmenu import RIGHT_ITEMS
    w, h = menu.width(), menu.height()
    p.setRenderHint(QPainter.Antialiasing, False)
    head, foot = QRectF(0, 0, w, 66), QRectF(0, 558, w, h - 558)
    p.fillRect(head, c["header"](head) if callable(c["header"]) else _c(c["header"]))
    if c.get("pinstripe"):
        p.setPen(QColor(255, 255, 255, 70))
        for y in range(0, 66, 2):
            p.drawLine(0, y, w, y)
    p.fillRect(QRectF(0, 66, 190, 492), _c(c["left"]))
    p.fillRect(QRectF(190, 66, w - 190, 492), _c(c["right"]))
    p.fillRect(foot, c["footer"](foot) if callable(c["footer"]) else _c(c["footer"]))
    p.setPen(_c(c["sep"]))
    p.drawLine(190, 66, 190, 557)
    p.drawLine(8, 119, 182, 119)
    p.drawLine(8, 522, 182, 522)
    p.drawLine(198, 226, w - 10, 226)
    p.drawLine(198, 324, w - 10, 324)
    p.drawLine(0, 66, w, 66)
    p.drawLine(0, 557, w, 557)
    # All Programs and its green arrow
    from .startmenu import ALL_PROGRAMS
    f = QFont("Tahoma", 8)
    f.setBold(True)
    p.setFont(f)
    p.setPen(_c(c["text"]))
    p.drawText(QRect(ALL_PROGRAMS.left() + 50, ALL_PROGRAMS.top(), 100, ALL_PROGRAMS.height()),
               Qt.AlignVCenter | Qt.AlignLeft, "All Programs")
    p.setRenderHint(QPainter.Antialiasing)
    ar = QRectF(ALL_PROGRAMS.left() + 152, ALL_PROGRAMS.center().y() - 8, 16, 16)
    p.setPen(QPen(QColor("#2C7A20"), 1))
    p.setBrush(_grad(ar.topLeft(), ar.bottomLeft(), [(0, "#7EE06A"), (1, "#2E9A22")]))
    p.drawRoundedRect(ar, 3, 3)
    p.setBrush(QColor("white"))
    p.setPen(Qt.NoPen)
    p.drawPolygon(QPolygonF([QPointF(ar.left() + 5, ar.top() + 4), QPointF(ar.right() - 4, ar.center().y()),
                             QPointF(ar.left() + 5, ar.bottom() - 4)]))
    # the right column
    for label, rect in RIGHT_ITEMS:
        _right_icon(p, RIGHT_ICONS[label], QRect(rect.x() + 6, rect.center().y() - 11, 22, 22))
        f = QFont("Tahoma", 8)
        f.setBold(label in BOLD_RIGHT)
        p.setFont(f)
        p.setPen(_c(c["right_text"]))
        p.drawText(rect.adjusted(34, 0, -4, 0), Qt.AlignVCenter | Qt.AlignLeft | Qt.TextWordWrap, label)
    p.setBrush(Qt.NoBrush)
    p.setPen(QPen(_c(c["border"]), 1))
    p.setRenderHint(QPainter.Antialiasing, False)
    p.drawRect(QRectF(0, 0, w - 1, h - 1))


# ---- Windows Classic style ---------------------------------------------------------------------------------------

# face, active title (left, right), inactive title (left, right), active text, inactive text, highlight, desktop,
# window text
CLASSIC = {
    "Windows Classic": ("#D4D0C8", "#0A246A", "#A6CAF0", "#808080", "#C0C0C0", "#FFFFFF", "#D4D0C8", "#0A246A",
                        "#3A6EA5", "#000000"),
    "Windows Standard": ("#C0C0C0", "#000080", "#1084D0", "#808080", "#B5B5B5", "#FFFFFF", "#C0C0C0", "#000080",
                         "#008080", "#000000"),
    "Brick": ("#C2BFA5", "#800000", "#C08050", "#887E6E", "#C2BFA5", "#FFFFFF", "#E8E4D0", "#800000", "#400000",
              "#000000"),
    "Desert": ("#D5CCBB", "#008080", "#7EC4C0", "#A28D68", "#D5CCBB", "#FFFFFF", "#F2EEE6", "#008080", "#A28D68",
               "#000000"),
    "Eggplant": ("#90B0A8", "#582858", "#A870A0", "#588078", "#90B0A8", "#FFFFFF", "#D8E8E4", "#582858", "#405050",
                 "#000000"),
    "Lilac": ("#AEA8D9", "#5A4E8C", "#B4AEE0", "#8E87BF", "#C8C4E6", "#FFFFFF", "#ECEAF8", "#5A4E8C", "#5A4E8C",
              "#000000"),
    "Marine": ("#88C0B8", "#000080", "#5A8EC8", "#609890", "#A8D0C8", "#FFFFFF", "#E0F0EC", "#000080", "#004040",
               "#000000"),
    "Plum": ("#A89890", "#483048", "#9A7898", "#887870", "#B8A8A0", "#FFFFFF", "#E8E0DC", "#483048", "#402840",
             "#000000"),
    "Rainy Day": ("#8099B3", "#4F657D", "#A0B4C8", "#708090", "#A0B0C0", "#FFFFFF", "#D8E0E8", "#4F657D", "#000000",
                  "#000000"),
    "Rose": ("#CFAFB7", "#800040", "#D08098", "#A08088", "#D8C0C8", "#FFFFFF", "#F2E8EC", "#800040", "#804060",
             "#000000"),
    "Slate": ("#A0B0C0", "#3C5070", "#8AA0BC", "#80909C", "#B8C4D0", "#FFFFFF", "#E4EAF0", "#3C5070", "#3A5A78",
              "#000000"),
    "Spruce": ("#A2C8A9", "#2E5E3A", "#80B890", "#7A9A80", "#BCD8C0", "#FFFFFF", "#E4F0E6", "#2E5E3A", "#1E3E24",
               "#000000"),
    "Wheat": ("#D7D3A8", "#808000", "#D0C870", "#A8A480", "#E0DCC0", "#FFFFFF", "#F4F2E4", "#808000", "#A0A040",
              "#000000"),
    "High Contrast Black": ("#000000", "#800080", "#800080", "#008000", "#008000", "#FFFFFF", "#FFFFFF", "#800080",
                            "#000000", "#FFFFFF"),
}


class ClassicStyle(Style):
    key, name = "classic", "Windows Classic style"
    base_title_h = 22

    def __init__(self, scheme="Windows Classic", font="normal"):
        super().__init__(scheme if scheme in CLASSIC else "Windows Classic", font)
        (self.face, self.a1, self.a2, self.i1, self.i2, self.atext, self.itext, self.hilite, self.desk,
         self.text) = CLASSIC[self.scheme]
        dark = _c(self.face).value() < 60
        self.light = "#FFFFFF"
        self.shadow = "#808080"
        self.dark = "#404040" if not dark else "#C0C0C0"
        self.task_text = self.tray_text = self.text
        self.sm_text = self.text
        self.sm_sub = "#606060" if not dark else "#C0C0C0"
        self.sm_hover, self.sm_hover_text = self.hilite, "#FFFFFF"
        self.sm_name, self.sm_name_shadow = self.atext, None
        self.sm_footer_text = self.atext

    def title_font(self):
        f = QFont("Tahoma", 8 + FONT_BUMP.get(self.font, 0) // 2)
        f.setBold(True)
        return f

    def palette(self):
        pal = QPalette()
        dark = _c(self.face).value() < 60
        base, text = ("#000000", "#FFFFFF") if dark else ("#FFFFFF", "#000000")
        for role, col in ((QPalette.Window, self.face), (QPalette.Button, self.face), (QPalette.Base, base),
                          (QPalette.AlternateBase, base), (QPalette.WindowText, self.text),
                          (QPalette.ButtonText, self.text), (QPalette.Text, text), (QPalette.Highlight, self.hilite),
                          (QPalette.HighlightedText, "#FFFFFF"), (QPalette.Light, "#FFFFFF"),
                          (QPalette.Midlight, _c(self.face).lighter(110)), (QPalette.Mid, _c(self.face).darker(130)),
                          (QPalette.Dark, "#808080"), (QPalette.Shadow, "#404040"),
                          (QPalette.ToolTipBase, "#FFFFE1"), (QPalette.ToolTipText, "#000000")):
            pal.setColor(role, _c(col))
        return pal

    def desktop_color(self):
        return self.desk

    def button_rects(self, w, buttons):
        bw, bh = 16 + FONT_BUMP.get(self.font, 0), 14 + FONT_BUMP.get(self.font, 0)
        y = 4 + (self.title_h - 4 - bh) // 2
        x = w - self.border - 2 - bw
        rects = {}
        if "close" in buttons:
            rects["close"] = QRect(x, y, bw, bh)
            x -= bw + 2
        for kind in ("max", "min"):
            if kind in buttons:
                rects[kind] = QRect(x, y, bw, bh)
                x -= bw
        return rects

    def paint_frame(self, p, w, h, title, icon, active, buttons, maximized=False, hover=None, press=None):
        p.setRenderHint(QPainter.Antialiasing, False)
        bevel(p, QRect(0, 0, w, h), True, self.face, self.light, self.shadow, self.dark)
        cap = QRectF(4, 4, w - 8, self.title_h - 4)
        a, b = (self.a1, self.a2) if active else (self.i1, self.i2)
        p.fillRect(cap, _grad(cap.topLeft(), cap.topRight(), [(0, a), (1, b)]))
        x = 6
        if icon is not None and not icon.isNull():
            p.drawPixmap(x, int(cap.center().y()) - 8, icon.pixmap(16, 16))
            x += 19
        rects = self.button_rects(w, buttons)
        text_w = (min(r.left() for r in rects.values()) if rects else w - 6) - x - 4
        self._title_text(p, QRect(x, int(cap.top()), text_w, int(cap.height())), title,
                         self.atext if active else self.itext)
        for kind, rect in rects.items():
            down = press == kind and hover == kind
            bevel(p, rect, not down, self.face, self.light, self.shadow, self.dark)
            ink = self.text if (active or kind == "close") else "#808080"
            glyph(p, rect.translated(1, 1) if down else rect, kind, ink, maximized, weight=1.1)

    def start_width(self):
        return 58

    def paint_taskbar(self, p, rect, start, menu_open):
        p.fillRect(rect, _c(self.face))
        p.setPen(_c(self.face))
        p.drawLine(rect.left(), rect.top(), rect.right(), rect.top())
        p.setPen(_c(self.light))
        p.drawLine(rect.left(), rect.top() + 1, rect.right(), rect.top() + 1)
        b = start.adjusted(2, 3, -1, -2)
        bevel(p, b, not menu_open, self.face, self.light, self.shadow, self.dark)
        off = 1 if menu_open else 0
        windows_flag(p, QRectF(b.left() + 4 + off, b.center().y() - 6 + off, 14, 12))
        f = QFont("Tahoma", 8)
        f.setBold(True)
        p.setFont(f)
        p.setPen(_c(self.text))
        p.drawText(b.adjusted(21 + off, off, 0, off), Qt.AlignVCenter | Qt.AlignLeft, "Start")

    def paint_task_button(self, p, rect, pressed):
        if pressed:
            bevel(p, rect, False, self.face, self.light, self.shadow, self.dark)
            inner = QRectF(rect).adjusted(2, 2, -2, -2)
            p.fillRect(inner, _c(self.face).lighter(112))
        else:
            bevel(p, rect, True, self.face, self.light, self.shadow, self.dark)

    def paint_tray(self, p, rect):
        r = rect.adjusted(2, 3, -2, -2)
        p.save()
        p.setRenderHint(QPainter.Antialiasing, False)
        p.setPen(_c(self.shadow))
        p.drawLine(r.left(), r.top(), r.right(), r.top())
        p.drawLine(r.left(), r.top(), r.left(), r.bottom())
        p.setPen(_c(self.light))
        p.drawLine(r.left(), r.bottom(), r.right(), r.bottom())
        p.drawLine(r.right(), r.top(), r.right(), r.bottom())
        p.restore()

    def paint_start_menu(self, p, menu):
        a1, a2 = self.a1, self.a2
        paint_drawn_start_menu(p, menu, {
            "header": lambda r: _grad(r.topLeft(), r.topRight(), [(0, a1), (1, a2)]),
            "footer": lambda r: _grad(r.topLeft(), r.topRight(), [(0, a1), (1, a2)]),
            "left": "#FFFFFF" if _c(self.face).value() > 60 else "#000000", "right": self.face,
            "border": self.dark, "sep": self.shadow, "text": self.text,
            "right_text": self.text})

    def menu_css(self):
        return (f"QMenu {{ background: {self.face}; color: {self.text}; border: 2px outset {self.face};"
                " font-family: Tahoma; font-size: 11px; }"
                " QMenu::item { padding: 4px 24px 4px 8px; }"
                f" QMenu::item:selected {{ background: {self.hilite}; color: white; }}"
                " QMenu::item:disabled { color: #808080; }"
                " QMenu::separator { height: 2px; background: #808080; margin: 3px 2px; }")


# ---- the third-party styles (StyleXP) ----------------------------------------------------------------------------

GLOSS = {
    "watercolor": dict(
        name="Watercolor", title_h=27, align=Qt.AlignLeft, font=("Trebuchet MS", 10), shape="round",
        buttons_left=False, pinstripe=False,
        frame=("#A9C0E2", "#D2DDEC"), title_a=[(0, "#FFFFFF"), (0.45, "#F0F5FC"), (1, "#CFDFF4")],
        title_i=[(0, "#FFFFFF"), (1, "#EEF2F8")], text=("#1E3F7A", "#9AAAC4"), shadow=None,
        btn=("#FFFFFF", "#D6E4F6"), btn_hover=("#FFFFFF", "#E8F0FB"), btn_inactive=("#FFFFFF", "#F0F4F9"),
        edge="#8EA8CC", glyph="#2E5288", close=("#FFF0EC", "#F2B0A0"), close_hover=("#FFF8F6", "#F7C8BC"),
        close_glyph="#A03020",
        taskbar=[(0, "#FFFFFF"), (1, "#D2E2F5")], taskbar_edge="#9DB6DC",
        start=("#A6E0A8", "#3E9E58"), start_text="#FFFFFF", start_shape="pill", start_label="start", start_w=92,
        task=("#FFFFFF", "#E2ECF8"), task_down=("#C3D7F0", "#DCE8F7"), task_edge="#9DB6DC", task_text="#1E3F7A",
        tray=[(0, "#F3F7FD"), (1, "#DCE7F5")], tray_text="#1E3F7A",
        sm_header=[(0, "#FFFFFF"), (1, "#D2E2F5")], sm_name="#1E3F7A", sm_name_shadow=None, sm_left="#FFFFFF",
        sm_right="#EEF4FC", sm_footer=[(0, "#D2E2F5"), (1, "#FFFFFF")], sm_footer_text="#1E3F7A",
        sm_hover="#C3D7F0", sm_hover_text="#000000", sm_text="#000000", sm_sub="#7F7F7F", sm_border="#9DB6DC",
        menu=("#FFFFFF", "#000000", "#C3D7F0", "#000000", "#9DB6DC")),
    "aquax": dict(
        name="Aqua X", title_h=24, align=Qt.AlignHCenter, font=("Tahoma", 9), shape="circle",
        buttons_left=True, pinstripe=True,
        frame=("#8C8C8C", "#B4B4B4"), title_a=[(0, "#F4F4F4"), (1, "#C6C6C6")],
        title_i=[(0, "#FAFAFA"), (1, "#E2E2E2")], text=("#202020", "#A0A0A0"), shadow="#FFFFFF",
        gels={"close": ("#FF9A8A", "#D8281C"), "min": ("#FFE58A", "#E0A010"), "max": ("#A6F08A", "#2EA41C")},
        btn_inactive=("#F0F0F0", "#B8B8B8"), edge="#6A6A6A", glyph="#5A1A10",
        taskbar=[(0, "#F2F2F2"), (0.5, "#DADADA"), (1, "#B6B6B6")], taskbar_edge="#8C8C8C",
        start=("#A8D4FF", "#1E6FD9"), start_text="#FFFFFF", start_shape="pill", start_label="start", start_w=86,
        task=("#FFFFFF", "#D0D0D0"), task_down=("#8CC2FF", "#2F7FE0"), task_edge="#8C8C8C", task_text="#202020",
        task_text_down="#FFFFFF",
        tray=[(0, "#E8E8E8"), (1, "#C2C2C2")], tray_text="#202020",
        sm_header=[(0, "#F4F4F4"), (1, "#C6C6C6")], sm_name="#202020", sm_name_shadow="#FFFFFF",
        sm_left="#FFFFFF", sm_right="#EDEDED", sm_footer=[(0, "#C6C6C6"), (1, "#F4F4F4")],
        sm_footer_text="#202020", sm_hover="#3875D7", sm_hover_text="#FFFFFF", sm_text="#000000", sm_sub="#7F7F7F",
        sm_border="#8C8C8C", menu=("#FFFFFF", "#000000", "#3875D7", "#FFFFFF", "#8C8C8C")),
    "chromehex": dict(
        name="Chrome Hex", title_h=28, align=Qt.AlignLeft, font=("Arial", 10), shape="hex",
        buttons_left=False, pinstripe=False,
        frame=("#2E3138", "#5A5E68"), title_a=[(0, "#8A8E98"), (0.08, "#5C606A"), (0.5, "#34373E"), (1, "#1C1E22")],
        title_i=[(0, "#9A9EA6"), (1, "#5A5E66")], text=("#F0F4FA", "#B8BCC4"), shadow="#000000",
        btn=("#9AA0AC", "#3E424C"), btn_hover=("#C8CEDA", "#5A606C"), btn_inactive=("#7A7E88", "#5A5E66"),
        edge="#D8DCE4", glyph="#FFFFFF", close=("#FF9A5A", "#C03A10"), close_hover=("#FFB27A", "#D85020"),
        close_glyph="#FFFFFF",
        taskbar=[(0, "#5A5E68"), (0.1, "#3A3D44"), (1, "#16181C")], taskbar_edge="#8A8E98",
        start=("#FFB060", "#E0600A"), start_text="#1A1A1A", start_shape="hex", start_label="START", start_w=88,
        task=("#4A4E58", "#2A2D33"), task_down=("#6A707C", "#454952"), task_edge="#7A7E88", task_text="#E8ECF4",
        tray=[(0, "#2A2D33"), (1, "#121316")], tray_text="#FFB060",
        sm_header=[(0, "#5A5E68"), (1, "#1C1E22")], sm_name="#F0F4FA", sm_name_shadow="#000000",
        sm_left="#2A2C32", sm_right="#383B42", sm_footer=[(0, "#1C1E22"), (1, "#4A4E58")],
        sm_footer_text="#F0F4FA", sm_hover="#FF8A1A", sm_hover_text="#000000", sm_text="#E0E4EC",
        sm_sub="#A0A4AC", sm_border="#8A8E98", menu=("#2A2C32", "#E0E4EC", "#FF8A1A", "#000000", "#8A8E98")),
}


def _hexagon(r):
    r = QRectF(r)
    dx = r.width() * 0.22
    return QPolygonF([QPointF(r.left() + dx, r.top()), QPointF(r.right() - dx, r.top()),
                      QPointF(r.right(), r.center().y()), QPointF(r.right() - dx, r.bottom()),
                      QPointF(r.left() + dx, r.bottom()), QPointF(r.left(), r.center().y())])


class GlossStyle(Style):
    """Watercolor, Aqua X and Chrome Hex: smooth gradients, shaped buttons."""

    def __init__(self, key, font="normal"):
        super().__init__("Default", font)
        self.key = key
        self.c = GLOSS[key]
        self.name = self.c["name"]
        self.base_title_h = self.c["title_h"]
        for attr in ("task_text", "tray_text", "sm_hover", "sm_hover_text", "sm_name", "sm_name_shadow",
                     "sm_footer_text", "sm_text", "sm_sub"):
            setattr(self, attr, self.c[attr])

    def title_font(self):
        fam, size = self.c["font"]
        f = QFont(fam, size + FONT_BUMP.get(self.font, 0) // 2)
        f.setBold(True)
        return f

    def button_rects(self, w, buttons):
        if self.c["shape"] == "circle":
            s = 14 + FONT_BUMP.get(self.font, 0)
            y = (self.title_h - s) // 2
            x = self.border + 6
            rects = {}
            for kind in ("close", "min", "max"):
                if kind in buttons:
                    rects[kind] = QRect(x, y, s, s)
                    x += s + 6
            return rects
        s = (19 if self.c["shape"] == "round" else 22) + FONT_BUMP.get(self.font, 0)
        sw = s + (6 if self.c["shape"] == "hex" else 0)
        y = (self.title_h - s) // 2 + 1
        x = w - self.border - 3 - sw
        rects = {}
        for kind in ("close", "max", "min"):
            if kind in buttons:
                rects[kind] = QRect(x, y, sw, s)
                x -= sw + 2
        return rects

    def paint_frame(self, p, w, h, title, icon, active, buttons, maximized=False, hover=None, press=None):
        c, th = self.c, self.title_h
        p.setRenderHint(QPainter.Antialiasing)
        rad = 0 if maximized else (7 if c["shape"] != "hex" else 3)
        path = QPainterPath()
        path.moveTo(0, h)
        path.lineTo(0, rad)
        path.quadTo(0, 0, rad, 0)
        path.lineTo(w - rad, 0)
        path.quadTo(w, 0, w, rad)
        path.lineTo(w, h)
        path.closeSubpath()
        p.fillPath(path, _c(c["frame"][0 if active else 1]))
        p.save()
        p.setClipPath(path)
        p.fillRect(QRectF(0, 0, w, th), _grad(QPointF(0, 0), QPointF(0, th), c["title_a" if active else "title_i"]))
        if c["pinstripe"]:
            p.setPen(QColor(255, 255, 255, 90))
            for y in range(1, th, 2):
                p.drawLine(0, y, w, y)
        if c["shape"] == "hex":
            p.setPen(QColor(255, 255, 255, 90))
            p.drawLine(0, 1, w, 1)
        p.restore()
        rects = self.button_rects(w, buttons)
        if c["buttons_left"]:
            left = (max(r.right() for r in rects.values()) + 8) if rects else self.border + 6
            trect = QRect(left, 0, w - 2 * left, th)
        else:
            x = self.border + 5
            if icon is not None and not icon.isNull():
                p.drawPixmap(x, (th - 16) // 2, icon.pixmap(16, 16))
                x += 21
            trect = QRect(x, 0, (min(r.left() for r in rects.values()) if rects else w) - x - 4, th)
        self._title_text(p, trect, title, c["text"][0 if active else 1], c["shadow"] if active else None,
                         c["align"])
        for kind, rect in rects.items():
            self._button(p, rect, kind, active, hover == kind, press == kind and hover == kind, maximized)

    def _button(self, p, rect, kind, active, hot, down, maximized):
        c = self.c
        r = QRectF(rect).adjusted(0.5, 0.5, -0.5, -0.5)
        if c["shape"] == "circle":
            top, bot = c["gels"][kind] if active else c["btn_inactive"]
            if down:
                top, bot = bot, top
            p.setPen(QPen(_c(c["edge"]), 0.8))
            p.setBrush(_grad(r.topLeft(), r.bottomLeft(), [(0, top), (1, bot)]))
            p.drawEllipse(r)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(255, 255, 255, 150))
            p.drawEllipse(QRectF(r.left() + r.width() * 0.22, r.top() + 1.5, r.width() * 0.56, r.height() * 0.38))
            if hot:
                glyph(p, rect.adjusted(2, 2, -2, -2), kind, c["glyph"], maximized)
            return
        if kind == "close":
            top, bot = c["close_hover"] if hot else c["close"]
            ink = c["close_glyph"]
        else:
            top, bot = c["btn_hover"] if hot else c["btn"]
            ink = c["glyph"]
        if not active:
            top, bot = c["btn_inactive"]
        if down:
            top, bot = bot, top
        p.setPen(QPen(_c(c["edge"]), 1))
        p.setBrush(_grad(r.topLeft(), r.bottomLeft(), [(0, top), (1, bot)]))
        if c["shape"] == "hex":
            p.drawPolygon(_hexagon(r))
        else:
            p.drawRoundedRect(r, 5, 5)
        glyph(p, rect, kind, ink, maximized)

    def start_width(self):
        return self.c["start_w"]

    def paint_taskbar(self, p, rect, start, menu_open):
        c = self.c
        p.fillRect(rect, _grad(QPointF(0, 0), QPointF(0, rect.height()), c["taskbar"]))
        p.setPen(_c(c["taskbar_edge"]))
        p.drawLine(rect.left(), rect.top(), rect.right(), rect.top())
        p.setRenderHint(QPainter.Antialiasing)
        b = QRectF(start).adjusted(0, 1, -4, -1)
        top, bot = c["start"]
        if menu_open:
            top, bot = bot, top
        p.setPen(QPen(_c(bot).darker(140), 1))
        p.setBrush(_grad(b.topLeft(), b.bottomLeft(), [(0, top), (0.5, bot), (1, _c(bot).darker(115))]))
        if c["start_shape"] == "hex":
            p.drawPolygon(_hexagon(b.adjusted(2, 1, 0, -1)))
        else:
            path = QPainterPath()
            path.moveTo(b.left(), b.top())
            path.lineTo(b.right() - b.height() / 2, b.top())
            path.arcTo(QRectF(b.right() - b.height(), b.top(), b.height(), b.height()), 90, -180)
            path.lineTo(b.left(), b.bottom())
            path.closeSubpath()
            p.drawPath(path)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(255, 255, 255, 90))
            p.drawRoundedRect(QRectF(b.left() + 3, b.top() + 2, b.width() - b.height() / 2 - 4, b.height() * 0.38),
                              4, 4)
        windows_flag(p, QRectF(b.left() + 9, b.center().y() - 7, 15, 14))
        f = QFont("Trebuchet MS", 11)
        f.setBold(True)
        f.setItalic(c["start_shape"] != "hex")
        p.setFont(f)
        p.setPen(QColor(0, 0, 0, 90))
        p.drawText(b.adjusted(29, 1, 0, 1), Qt.AlignVCenter | Qt.AlignLeft, c["start_label"])
        p.setPen(_c(c["start_text"]))
        p.drawText(b.adjusted(28, 0, 0, 0), Qt.AlignVCenter | Qt.AlignLeft, c["start_label"])

    def paint_task_button(self, p, rect, pressed):
        c = self.c
        p.save()
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(rect).adjusted(0.5, 0.5, -0.5, -0.5)
        top, bot = c["task_down"] if pressed else c["task"]
        p.setPen(QPen(_c(c["task_edge"]), 1))
        p.setBrush(_grad(r.topLeft(), r.bottomLeft(), [(0, top), (1, bot)]))
        if c["shape"] == "hex":
            p.drawPolygon(_hexagon(r))
        else:
            p.drawRoundedRect(r, r.height() / 2 if c["shape"] == "circle" else 4, r.height() / 2
                              if c["shape"] == "circle" else 4)
        p.restore()

    def task_text_color(self, pressed):
        return self.c.get("task_text_down", self.c["task_text"]) if pressed else self.c["task_text"]

    def paint_tray(self, p, rect):
        c = self.c
        p.fillRect(rect, _grad(QPointF(0, 0), QPointF(0, rect.height()), c["tray"]))
        p.setPen(_c(c["taskbar_edge"]))
        p.drawLine(rect.left(), 0, rect.left(), rect.height())

    def paint_start_menu(self, p, menu):
        c = self.c
        paint_drawn_start_menu(p, menu, {
            "header": lambda r: _grad(r.topLeft(), r.bottomLeft(), c["sm_header"]),
            "footer": lambda r: _grad(r.topLeft(), r.bottomLeft(), c["sm_footer"]),
            "left": c["sm_left"], "right": c["sm_right"], "border": c["sm_border"], "sep": c["sm_border"],
            "text": c["sm_text"], "right_text": c["sm_text"], "pinstripe": c["pinstripe"]})

    def menu_css(self):
        bg, fg, sel, sel_text, border = self.c["menu"]
        return (f"QMenu {{ background: {bg}; color: {fg}; border: 1px solid {border}; font-family: Tahoma;"
                " font-size: 11px; } QMenu::item { padding: 5px 24px 5px 8px; }"
                f" QMenu::item:selected {{ background: {sel}; color: {sel_text}; }}"
                " QMenu::item:disabled { color: #8A8A8A; }"
                f" QMenu::separator {{ height: 1px; background: {border}; margin: 3px 2px; }}")


# ---- the current choice ------------------------------------------------------------------------------------------

def make_style(style, scheme, font="normal"):
    if style == "classic":
        return ClassicStyle(scheme, font)
    if style in GLOSS:
        return GlossStyle(style, font)
    return LunaStyle(scheme, font)


def all_styles():
    """[(key, label)] for 'Windows and buttons' (the third-party ones only once StyleXP has patched Windows)."""
    out = [("luna", "Windows XP style"), ("classic", "Windows Classic style")]
    if hacked_allowed():
        out += [(k, GLOSS[k]["name"]) for k in HACKED]
    return out


def schemes(style):
    if style == "luna":
        return LUNA_NAMES
    if style == "classic":
        return [(k, k) for k in CLASSIC]
    return [("Default", "Default")]


def default_scheme(style):
    return schemes(style)[0][0]


def hacked_allowed():
    try:
        from .programs import stylexp
        return stylexp.patched()
    except Exception:
        return False


_state = None
_style = None
reverted = False          # True once a lapsed StyleXP trial has put the Windows XP style back


def state():
    global _state
    if _state is None:
        from . import display
        _state = dict(DEFAULT)
        _state.update(display.get().data.get("theme") or {})
    return _state


def current():
    global _style, reverted
    if _style is None:
        s = state()
        style = s["style"]
        if style in HACKED and not hacked_allowed():          # the StyleXP trial ran out: back to Luna
            s.update(style="luna", scheme="blue")
            style = "luna"
            reverted = True
        _style = make_style(style, s["scheme"], s["font"])
    return _style


def title_h():
    return current().title_h


def border():
    return current().border


def set_state(**changes):
    """Change the theme settings (style, scheme, font, name, sounds, cursors) and tell everything to redraw."""
    global _style
    from . import display
    s = state()
    s.update(changes)
    _style = None
    disp = display.get()
    disp.data["theme"] = dict(s)
    disp._save()
    notifier.changed.emit()


def refresh_window(win):
    """Re-fit a window to the current frame metrics and palette (keeping its content the same size)."""
    if getattr(win, "skinned", False):
        return
    st = current()
    lay = win.layout()
    if lay is None:
        return
    old = lay.contentsMargins()
    lay.setContentsMargins(st.border, st.title_h, st.border, st.border)
    dh = st.title_h - old.top()
    dw = 2 * (st.border - old.left())
    if (dh or dw) and not win.maximized:
        fixed = win.minimumSize() == win.maximumSize()
        size = win.size()
        if fixed:
            win.setFixedSize(size.width() + dw, size.height() + dh)
        else:
            win.resize(size.width() + dw, size.height() + dh)
    if not win.adopted:
        pal = st.palette()
        win.setPalette(pal if pal is not None else QPalette())
        from .network import DialogBody
        for body in ([win.content] if isinstance(win.content, DialogBody) else []) +                 win.content.findChildren(DialogBody):
            body.restyle()
    win.update()
