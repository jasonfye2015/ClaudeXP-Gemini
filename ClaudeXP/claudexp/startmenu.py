"""The Start menu, drawn over startmenu.jpg."""
from functools import partial

from PySide6.QtCore import QPoint, QRect, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import QMenu, QStyle, QWidget

from . import programs, sound, theme
from .paths import pixmap
from .user import draw_user_picture, user_name

MENU_STYLE = """
QMenu { background: white; border: 1px solid #7A96DF; font-family: Tahoma; font-size: 11px; }
QMenu::item { padding: 5px 24px 5px 8px; }
QMenu::item:selected { background: #316AC5; color: white; }
QMenu::item:disabled { color: #ACA899; }
QMenu::separator { height: 1px; background: #ACA899; margin: 3px 2px; }
"""

PIC_RECT = QRect(6, 8, 52, 52)
PINNED_TOP = 70
MFU_TOP = 124
ALL_PROGRAMS = QRect(4, 528, 182, 26)
LOG_OFF = QRect(140, 563, 90, 30)
TURN_OFF = QRect(234, 563, 140, 30)
BAKED_HIGHLIGHT = QRect(193, 231, 180, 28)  # Control Panel highlight baked into the image

# (label, rect) of the right-hand column items already drawn in the image.
RIGHT_ITEMS = [
    ("My Documents", QRect(192, 72, 180, 28)),
    ("My Recent Documents", QRect(192, 102, 180, 28)),
    ("My Pictures", QRect(192, 132, 180, 28)),
    ("My Music", QRect(192, 162, 180, 28)),
    ("My Computer", QRect(192, 192, 180, 28)),
    ("Control Panel", QRect(192, 231, 180, 28)),
    ("Set Program Access and Defaults", QRect(192, 260, 180, 30)),
    ("Printers and Faxes", QRect(192, 291, 180, 28)),
    ("Search", QRect(192, 329, 180, 28)),
    ("Run...", QRect(192, 359, 180, 28)),
    ("Help and Support", QRect(192, 389, 180, 28)),     # not in the artwork; drawn by _draw_help_item
    ("Thanks!", QRect(192, 419, 180, 28)),              # the credits window (also drawn by _draw_help_item)
]


class StartMenu(QWidget):
    def __init__(self, desktop):
        super().__init__(desktop)
        self.desktop = desktop
        self.bg = pixmap("startmenu.jpg")
        self.setFixedSize(self.bg.size())
        self.setMouseTracking(True)
        from .user import account
        account().changed.connect(self.update)
        self.pinned = list(programs.PINNED)   # XP's pinned 'Internet' spot
        self.hover = None
        self.hide()

    # ---- layout -------------------------------------------------------------
    def _items(self):
        """Every clickable region as (id, rect)."""
        items = []
        for key in self.pinned:
            items.append((("prog", key), QRect(4, PINNED_TOP, 182, 42)))
        y = MFU_TOP
        from .programs import installed
        gone = installed.removed()
        for key in [k for k in programs.recent if k not in gone]:
            items.append((("prog", key), QRect(4, y, 182, 38)))
            y += 38
        items.append((("all", None), ALL_PROGRAMS))
        for label, rect in RIGHT_ITEMS:
            items.append((("right", label), rect))
        items.append((("logoff", None), LOG_OFF))
        items.append((("turnoff", None), TURN_OFF))
        return items

    def _item_at(self, pos):
        for item_id, rect in self._items():
            if rect.contains(pos):
                return item_id
        return None

    # ---- events -------------------------------------------------------------
    def hideEvent(self, event):
        self.hover = None

    def mouseMoveEvent(self, event):
        item = self._item_at(event.position().toPoint())
        if item != self.hover:
            self.hover = item
            self.update()

    def leaveEvent(self, event):
        self.hover = None
        self.update()

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        if PIC_RECT.contains(event.position().toPoint()):
            # Clicking your picture: XP's 'Pick a new picture for your account'.
            from .controlpanel import user_accounts
            self.desktop.hide_start_menu()
            user_accounts(self.desktop, page=1)
            return
        item = self._item_at(event.position().toPoint())
        if item is None:
            return
        kind, value = item
        if kind == "all":
            self._show_all_programs()
            return
        self.desktop.hide_start_menu()
        if kind in ("prog", "right"):
            sound.play("menu")
        if kind == "prog":
            programs.launch(self.desktop, value)
        elif kind == "right":
            from . import explorer
            from .explorer import vfs
            folders = {"My Documents": vfs.my_documents, "My Pictures": vfs.my_pictures, "My Music": vfs.my_music}
            if value == "My Computer":
                programs.launch(self.desktop, "mycomputer")
            elif value == "Printers and Faxes":
                from .printing import printers_and_faxes
                printers_and_faxes(self.desktop)
            elif value == "Search":
                from .programs.search import open_search
                open_search(self.desktop)
            elif value == "Help and Support":
                from .programs.helpctr import open_help
                open_help(self.desktop)
            elif value == "Thanks!":
                from . import credits
                credits.show(self.desktop)
            elif value == "Run...":
                from .programs.run import open_run
                open_run(self.desktop)
            elif value == "Control Panel":
                from .controlpanel import control_panel
                control_panel(self.desktop)
            elif value in folders:
                vfs.setup_c()
                explorer.launch(self.desktop, folders[value]())
            else:
                from .programs.placeholder import open_placeholder
                icon = self.style().standardIcon(QStyle.SP_DirIcon)
                open_placeholder(self.desktop, value, icon)
        elif kind == "logoff":
            self.desktop.log_off()
        elif kind == "turnoff":
            self.desktop.turn_off()

    def _show_all_programs(self):
        menu = QMenu(self)
        css = theme.current().menu_css()
        menu.setStyleSheet(css)
        folder = self.style().standardIcon(QStyle.SP_DirIcon)
        submenus = {"": menu}

        def submenu(path):
            # Folders first, alphabetically, like XP's All Programs.
            if path not in submenus:
                parent_path, _, name = path.rpartition("/")
                parent = submenu(parent_path)
                sub = QMenu(name, parent)
                sub.setIcon(folder)
                sub.setStyleSheet(css)
                folders = [a for a in parent.actions() if a.menu()]
                after = next((a for a in folders if a.text() > name), None)
                if after is None:
                    after = next((a for a in parent.actions() if not a.menu()), None)
                parent.insertMenu(after, sub)
                submenus[path] = sub
            return submenus[path]

        from .programs import installed
        gone = installed.removed()
        listed = [p for p in programs.PROGRAMS if p.listed and p.key not in gone
                  and (p.key not in programs.FOLDER_SHORTCUTS or programs.archive_folder(p.key))]
        for group in sorted({p.group for p in listed if p.group}):
            submenu(group)
        for prog in listed:
            submenu(prog.group).addAction(prog.icon(), prog.name, partial(self._launch_from_menu, prog.key))
        for sub in submenus.values():
            if sub is not menu:
                items = [a for a in sub.actions() if not a.menu()]
                for a in sorted(items, key=lambda a: a.text()):
                    sub.removeAction(a)
                    sub.addAction(a)
        menu.popup(self.mapToGlobal(QPoint(ALL_PROGRAMS.right() + 2, ALL_PROGRAMS.top())))

    def _launch_from_menu(self, key):
        self.desktop.hide_start_menu()
        sound.play("menu")
        programs.launch(self.desktop, key)

    # ---- painting -----------------------------------------------------------
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        self.st = theme.current()
        self.st.paint_start_menu(p, self)
        p.setRenderHint(QPainter.Antialiasing)
        self._draw_header(p)
        self._draw_programs(p)
        self._draw_right_hover(p)
        self._draw_footer(p)

    def _draw_help_item(self, p):
        r = dict(RIGHT_ITEMS)["Help and Support"]
        icon = QRectF(r.x() + 6, r.center().y() - 10, 20, 20)
        grad = QLinearGradient(icon.topLeft(), icon.bottomRight())
        grad.setColorAt(0, QColor("#6FA3F7"))
        grad.setColorAt(1, QColor("#1D4FC4"))
        p.setPen(QPen(QColor("#163A8F"), 1))
        p.setBrush(grad)
        p.drawEllipse(icon)
        f = QFont("Tahoma", 9)
        f.setBold(True)
        p.setFont(f)
        p.setPen(QColor("white"))
        p.drawText(icon, Qt.AlignCenter, "?")
        p.setFont(QFont("Tahoma", 8))
        p.setPen(QColor("black"))
        p.drawText(r.adjusted(32, 0, 0, 0), Qt.AlignVCenter | Qt.AlignLeft, "Help and Support")
        from .credits import credits_icon
        r = dict(RIGHT_ITEMS)["Thanks!"]
        p.drawPixmap(r.x() + 6, r.center().y() - 11, credits_icon().pixmap(22, 22))
        p.drawText(r.adjusted(32, 0, 0, 0), Qt.AlignVCenter | Qt.AlignLeft, "Thanks!")

    def _draw_control_panel_item(self, p):
        # The image only has Control Panel highlighted; repaint it un-highlighted.
        icon = self.style().standardIcon(QStyle.SP_DesktopIcon)
        r = BAKED_HIGHLIGHT
        p.drawPixmap(r.x() + 4, r.center().y() - 12, icon.pixmap(24, 24))
        p.setFont(QFont("Tahoma", 8))
        p.setPen(QColor("black"))
        p.drawText(r.adjusted(32, 0, 0, 0), Qt.AlignVCenter | Qt.AlignLeft, "Control Panel")

    def _draw_header(self, p):
        draw_user_picture(p, PIC_RECT)
        p.setPen(QPen(QColor("white"), 2))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(QRectF(PIC_RECT).adjusted(-1, -1, 1, 1), 3, 3)

        font = QFont("Trebuchet MS", 11)
        font.setBold(True)
        p.setFont(font)
        name_rect = QRect(68, 8, 300, 52)
        if self.st.sm_name_shadow:
            p.setPen(QColor(self.st.sm_name_shadow))
            p.drawText(name_rect.translated(1, 1), Qt.AlignVCenter | Qt.AlignLeft, user_name())
        p.setPen(QColor(self.st.sm_name))
        p.drawText(name_rect, Qt.AlignVCenter | Qt.AlignLeft, user_name())

    def _draw_programs(self, p):
        for item_id, rect in self._items():
            kind, key = item_id
            if kind != "prog":
                continue
            prog = programs.get(key)
            hovered = self.hover == item_id
            if hovered:
                p.fillRect(rect, QColor(self.st.sm_hover))
            pinned = key in self.pinned and rect.top() == PINNED_TOP
            p.drawPixmap(rect.x() + 6, rect.center().y() - 16, prog.icon().pixmap(32, 32))
            text_rect = rect.adjusted(46, 0, -4, 0)
            name_font = QFont("Tahoma", 8)
            name_font.setBold(pinned)
            p.setFont(name_font)
            p.setPen(QColor(self.st.sm_hover_text) if hovered else QColor(self.st.sm_text))
            if pinned and prog.blurb:
                p.drawText(text_rect.adjusted(0, 4, 0, -rect.height() // 2), Qt.AlignBottom | Qt.AlignLeft, prog.name)
                p.setFont(QFont("Tahoma", 8))
                p.setPen(QColor(self.st.sm_hover_text) if hovered else QColor(self.st.sm_sub))
                p.drawText(text_rect.adjusted(0, rect.height() // 2, 0, -4), Qt.AlignTop | Qt.AlignLeft, prog.blurb)
            else:
                p.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, prog.name)
        if self.hover == ("all", None):
            c = QColor(self.st.sm_hover)
            c.setAlpha(70)
            p.fillRect(ALL_PROGRAMS, c)

    def _draw_right_hover(self, p):
        if self.hover and self.hover[0] == "right":
            rect = dict(RIGHT_ITEMS)[self.hover[1]]
            c = QColor(self.st.sm_hover)
            c.setAlpha(80)
            p.fillRect(rect, c)

    def _draw_footer(self, p):
        p.setFont(QFont("Tahoma", 8))
        for item_id, rect, color, label in (
            (("logoff", None), LOG_OFF, "#F0B43C", "Log Off"),
            (("turnoff", None), TURN_OFF, "#E0582F", "Turn Off Computer"),
        ):
            if self.hover == item_id:
                p.fillRect(rect, QColor(255, 255, 255, 40))
            box = QRectF(rect.x() + 4, rect.center().y() - 10, 21, 21)
            grad = QLinearGradient(0, box.top(), 0, box.bottom())
            grad.setColorAt(0, QColor(color).lighter(130))
            grad.setColorAt(1, QColor(color))
            p.setPen(QPen(QColor("white"), 1))
            p.setBrush(grad)
            p.drawRoundedRect(box, 3, 3)
            p.setPen(QPen(QColor("white"), 2))
            p.setBrush(Qt.NoBrush)
            c = box.center()
            if item_id[0] == "turnoff":
                p.drawArc(QRectF(c.x() - 5, c.y() - 4, 10, 10), 120 * 16, 300 * 16)
                p.drawLine(c.x(), c.y() - 6, c.x(), c.y())
            else:
                p.drawLine(c.x() - 5, c.y(), c.x() + 4, c.y())
                p.drawLine(c.x() + 1, c.y() - 3, c.x() + 4, c.y())
                p.drawLine(c.x() + 1, c.y() + 3, c.x() + 4, c.y())
            p.setPen(QColor(self.st.sm_footer_text))
            p.drawText(rect.adjusted(30, 0, 0, 0), Qt.AlignVCenter | Qt.AlignLeft, label)
