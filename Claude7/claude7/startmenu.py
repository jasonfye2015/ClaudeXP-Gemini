"""The Windows 7 Start menu: pinned and recent programs on the left, All Programs opening in place as a folder
tree, 'Search programs and files' at the bottom, your picture and the places on the right, and the Shut down
button with its arrow (Switch user, Log off, Lock, Restart, Sleep)."""
from functools import partial

from PySide6.QtCore import QPoint, QPointF, QRect, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen, QPolygonF
from PySide6.QtWidgets import QLineEdit, QMenu, QStyle, QTreeWidget, QTreeWidgetItem, QWidget

from . import sound
from .paths import pixmap
from .user import draw_user_picture, user_name

WIDTH, HEIGHT = 420, 580
LEFT_W = 250
ROW_H = 34
PIC = 48
RIGHT_ITEMS = ["@user", "Documents", "Pictures", "Music", "Games", "-", "Computer", "Control Panel",
               "Devices and Printers", "Default Programs", "Help and Support"]
TREE_CSS = """
QTreeWidget { background: white; border: none; font-family: 'Segoe UI'; font-size: 12px; outline: none; }
QTreeWidget::item { height: 24px; padding-left: 2px; }
QTreeWidget::item:hover { background: #E5F3FB; }
QTreeWidget::item:selected { background: #CCE8FF; color: black; border: 1px solid #99D1FF; }
QTreeWidget::branch { background: white; }
QScrollBar:vertical { background: #F0F0F0; width: 14px; }
QScrollBar::handle:vertical { background: #CDCDCD; border-radius: 3px; min-height: 24px; margin: 2px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""
SEARCH_CSS = """
QLineEdit { background: white; border: 1px solid #9BB3CC; border-radius: 3px; padding: 3px 22px 3px 6px;
            font-family: 'Segoe UI'; font-size: 12px; font-style: italic; color: #6D6D6D; }
QLineEdit:focus { font-style: normal; color: black; }
"""


class StartMenu(QWidget):
    def __init__(self, desktop):
        super().__init__(desktop)
        self.desktop = desktop
        self.setFixedSize(WIDTH, HEIGHT)
        self.setMouseTracking(True)
        from .user import account
        account().changed.connect(self.update)
        self.hover = None
        self.mode = "main"
        self.search = QLineEdit(self)
        self.search.setPlaceholderText("Search programs and files")
        self.search.setStyleSheet(SEARCH_CSS)
        self.search.setGeometry(10, HEIGHT - 40, LEFT_W - 14, 26)
        self.search.textChanged.connect(self._search_changed)
        self.tree = QTreeWidget(self)
        self.tree.setHeaderHidden(True)
        self.tree.setStyleSheet(TREE_CSS)
        self.tree.setIndentation(16)
        self.tree.setGeometry(10, 10, LEFT_W - 14, HEIGHT - 94)
        self.tree.itemClicked.connect(self._tree_clicked)
        self.tree.hide()
        self.hide()

    # ---- layout ----
    def _left_items(self):
        """(id, rect) of the pinned and recent programs in the main view."""
        from claudexp import programs
        from claudexp.programs import installed
        gone = installed.removed()
        items = []
        y = 12
        for key in [k for k in programs.PINNED if k not in gone]:
            items.append((("prog", key), QRect(10, y, LEFT_W - 14, ROW_H)))
            y += ROW_H
        if items:
            y += 8
        for key in [k for k in programs.recent if k not in gone and k not in programs.PINNED][:10]:
            if y + ROW_H > HEIGHT - 94:
                break
            items.append((("prog", key), QRect(10, y, LEFT_W - 14, ROW_H)))
            y += ROW_H
        return items

    def _all_programs_rect(self):
        return QRect(10, HEIGHT - 76, LEFT_W - 14, 28)

    def _right_items(self):
        items = []
        y = 22 + PIC + 14
        for label in RIGHT_ITEMS:
            if label == "-":
                y += 10
                continue
            items.append((("right", label), QRect(LEFT_W + 14, y, WIDTH - LEFT_W - 28, 26)))
            y += 28
        return items

    def _shutdown_rect(self):
        return QRect(LEFT_W + 20, HEIGHT - 42, 100, 26)

    def _arrow_rect(self):
        return QRect(LEFT_W + 120, HEIGHT - 42, 22, 26)

    def _items(self):
        items = []
        if self.mode == "main":
            items += self._left_items()
        items.append((("all", None), self._all_programs_rect()))
        items += self._right_items()
        items.append((("shutdown", None), self._shutdown_rect()))
        items.append((("arrow", None), self._arrow_rect()))
        return items

    def _item_at(self, pos):
        for item_id, rect in self._items():
            if rect.contains(pos):
                return item_id
        return None

    # ---- showing ----
    def showEvent(self, event):
        super().showEvent(event)
        self.search.clear()
        self._set_mode("main")
        QTimer.singleShot(0, self.search.setFocus)

    def hideEvent(self, event):
        self.hover = None
        self.search.clear()

    def _set_mode(self, mode):
        self.mode = mode
        self.tree.setVisible(mode != "main")
        if mode == "all":
            self._fill_tree()
        self.update()

    # ---- the All Programs tree and search results ----
    def _fill_tree(self, query=""):
        from claudexp import programs
        from claudexp.programs import installed
        self.tree.clear()
        gone = installed.removed()
        listed = [p for p in programs.PROGRAMS if p.listed and p.key not in gone
                  and (p.key not in programs.FOLDER_SHORTCUTS or programs.archive_folder(p.key))]
        folder_icon = self.style().standardIcon(QStyle.SP_DirIcon)
        if query:
            head = QTreeWidgetItem(["Programs"])
            head.setFlags(Qt.ItemIsEnabled)
            f = head.font(0)
            f.setBold(True)
            head.setFont(0, f)
            self.tree.addTopLevelItem(head)
            q = query.lower()
            hits = sorted([p for p in listed if q in p.name.lower() or q in p.blurb.lower()], key=lambda p: p.name)
            for prog in hits[:30]:
                item = QTreeWidgetItem([prog.name])
                item.setIcon(0, prog.icon())
                item.setData(0, Qt.UserRole, prog.key)
                self.tree.addTopLevelItem(item)
            self.tree.expandAll()
            return
        folders = {}

        def folder(path):
            if path in folders:
                return folders[path]
            parent_path, _, name = path.rpartition("/")
            parent = folder(parent_path) if parent_path else None
            item = QTreeWidgetItem([name])
            item.setIcon(0, folder_icon)
            item.setData(0, Qt.UserRole, None)
            if parent is None:
                self.tree.addTopLevelItem(item)
            else:
                parent.addChild(item)
            folders[path] = item
            return item

        for group in sorted({p.group for p in listed if p.group}):
            folder(group)
        loose = []
        for prog in sorted(listed, key=lambda p: p.name.lower()):
            item = QTreeWidgetItem([prog.name])
            item.setIcon(0, prog.icon())
            item.setData(0, Qt.UserRole, prog.key)
            if prog.group:
                folders[prog.group].addChild(item)
            else:
                loose.append(item)
        for item in loose:
            self.tree.addTopLevelItem(item)
        self.tree.sortItems(0, Qt.AscendingOrder)
        # folders first, like Windows 7's All Programs
        tops = [self.tree.takeTopLevelItem(0) for _ in range(self.tree.topLevelItemCount())]
        tops.sort(key=lambda it: (it.data(0, Qt.UserRole) is not None, it.text(0).lower()))
        for it in tops:
            self.tree.addTopLevelItem(it)

    def _tree_clicked(self, item, _col):
        key = item.data(0, Qt.UserRole)
        if key is None:
            item.setExpanded(not item.isExpanded())
            return
        self._launch(key)

    def _search_changed(self, text):
        if text.strip():
            self._set_mode("search")
            self._fill_tree(text.strip())
        elif self.mode == "search":
            self._set_mode("main")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.desktop.hide_start_menu()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter) and self.mode == "search":
            for i in range(self.tree.topLevelItemCount()):
                key = self.tree.topLevelItem(i).data(0, Qt.UserRole)
                if key:
                    self._launch(key)
                    return
        else:
            super().keyPressEvent(event)

    # ---- events ----
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
        pos = event.position().toPoint()
        if self._pic_rect().contains(pos):
            self.desktop.hide_start_menu()
            from .controlpanel import user_accounts
            user_accounts(self.desktop, page=1)
            return
        item = self._item_at(pos)
        if item is None:
            return
        kind, value = item
        if kind == "all":
            self._set_mode("main" if self.mode != "main" else "all")
            return
        if kind == "arrow":
            self._power_menu()
            return
        if kind == "shutdown":
            self.desktop.hide_start_menu()
            self.desktop.turn_off()
            return
        self.desktop.hide_start_menu()
        sound.play("menu")
        if kind == "prog":
            self._launch(value)
        elif kind == "right":
            self._open_right(value)

    def _launch(self, key):
        from claudexp import programs
        self.desktop.hide_start_menu()
        sound.play("menu")
        programs.launch(self.desktop, key)

    def _open_right(self, value):
        from claudexp import explorer, programs
        from . import vfs
        vfs.setup_c()
        folders = {"Documents": vfs.my_documents, "Pictures": vfs.my_pictures, "Music": vfs.my_music,
                   "@user": vfs.user_home, "Games": lambda: vfs.user_home() / "Desktop" / "Games"}
        if value == "Computer":
            programs.launch(self.desktop, "mycomputer")
        elif value == "Control Panel":
            from .controlpanel import control_panel
            control_panel(self.desktop)
        elif value == "Devices and Printers":
            from claudexp.printing import printers_and_faxes
            printers_and_faxes(self.desktop)
        elif value == "Default Programs":
            from .controlpanel import default_programs
            default_programs(self.desktop)
        elif value == "Help and Support":
            from .programs.helpctr import open_help
            open_help(self.desktop)
        elif value in folders:
            explorer.launch(self.desktop, folders[value]())

    def _power_menu(self):
        from .shims import MENU_CSS
        menu = QMenu(self)
        menu.setStyleSheet(MENU_CSS)
        menu.addAction("Switch user", lambda: self._power("switch"))
        menu.addAction("Log off", lambda: self._power("logoff"))
        menu.addAction("Lock", lambda: self._power("lock"))
        menu.addAction("Restart", lambda: self._power("restart"))
        menu.addAction("Sleep", lambda: self._power("sleep"))
        r = self._arrow_rect()
        menu.popup(self.mapToGlobal(QPoint(r.right() + 2, r.top() - 120)))

    def _power(self, what):
        self.desktop.hide_start_menu()
        sound.play("menu")
        d = self.desktop
        {"switch": d.switch_user, "logoff": d.log_off, "lock": d.lock, "restart": d.restart, "sleep": d.sleep}[what]()

    # ---- painting ----
    def _pic_rect(self):
        return QRect(WIDTH - 28 - PIC - 24, 12, PIC, PIC)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        from . import display
        aero = display.get().aero_color()
        w, h = self.width(), self.height()
        # the glass frame
        frame = QRectF(0.5, 0.5, w - 1, h - 1)
        tint = QColor(aero).darker(150)
        tint.setAlpha(235)
        p.setPen(QPen(QColor(0, 0, 0, 170), 1))
        p.setBrush(tint)
        p.drawRoundedRect(frame, 7, 7)
        sheen = QLinearGradient(0, 0, 0, h)
        sheen.setColorAt(0, QColor(255, 255, 255, 90))
        sheen.setColorAt(0.35, QColor(255, 255, 255, 20))
        sheen.setColorAt(1, QColor(255, 255, 255, 40))
        p.setBrush(sheen)
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(frame, 7, 7)
        p.setPen(QPen(QColor(255, 255, 255, 110), 1))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(frame.adjusted(1, 1, -1, -1), 6, 6)
        # the left pane
        left = QRect(8, 8, LEFT_W - 10, HEIGHT - 16)
        p.setPen(QPen(QColor(0, 0, 0, 90), 1))
        p.setBrush(QColor("white"))
        p.drawRoundedRect(QRectF(left).adjusted(0.5, 0.5, -0.5, -0.5), 3, 3)
        if self.mode == "main":
            self._draw_programs(p)
        # the bar with All Programs
        bar = self._all_programs_rect()
        p.setPen(QPen(QColor("#D9DFE7"), 1))
        p.drawLine(bar.left(), bar.top() - 4, bar.right(), bar.top() - 4)
        f = QFont("Segoe UI")
        f.setPixelSize(12)
        p.setFont(f)
        if self.hover == ("all", None):
            self._highlight(p, bar)
        tri = QPolygonF([QPointF(bar.left() + 12, bar.center().y() - 5), QPointF(bar.left() + 18, bar.center().y()),
                         QPointF(bar.left() + 12, bar.center().y() + 5)])
        if self.mode != "main":
            tri = QPolygonF([QPointF(bar.left() + 18, bar.center().y() - 5), QPointF(bar.left() + 12, bar.center().y()),
                             QPointF(bar.left() + 18, bar.center().y() + 5)])
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#3C3C3C"))
        p.drawPolygon(tri)
        p.setPen(QColor("#1E1E1E"))
        p.drawText(bar.adjusted(32, 0, 0, 0), Qt.AlignVCenter | Qt.AlignLeft,
                   "Back" if self.mode != "main" else "All Programs")
        # the right pane
        self._draw_right(p)

    def _highlight(self, p, rect, dark=False):
        r = QRectF(rect).adjusted(0.5, 0.5, -0.5, -0.5)
        if dark:
            p.setPen(QPen(QColor(255, 255, 255, 120), 1))
            p.setBrush(QColor(255, 255, 255, 60))
        else:
            g = QLinearGradient(r.topLeft(), r.bottomLeft())
            g.setColorAt(0, QColor("#EAF3FC"))
            g.setColorAt(1, QColor("#D5E7F7"))
            p.setPen(QPen(QColor("#7DA2CE"), 1))
            p.setBrush(g)
        p.drawRoundedRect(r, 3, 3)

    def _draw_programs(self, p):
        from claudexp import programs
        f = QFont("Segoe UI")
        f.setPixelSize(12)
        p.setFont(f)
        sep_drawn = False
        for item_id, rect in self._left_items():
            kind, key = item_id
            try:
                prog = programs.get(key)
            except StopIteration:
                continue
            if key not in programs.PINNED and not sep_drawn:
                p.setPen(QPen(QColor("#D9DFE7"), 1))
                p.drawLine(rect.left() + 4, rect.top() - 5, rect.right() - 4, rect.top() - 5)
                sep_drawn = True
            if self.hover == item_id:
                self._highlight(p, rect)
            p.drawPixmap(rect.x() + 6, rect.center().y() - 16, prog.icon().pixmap(32, 32))
            p.setPen(QColor("#1E1E1E"))
            p.drawText(rect.adjusted(46, 0, -4, 0), Qt.AlignVCenter | Qt.AlignLeft,
                       p.fontMetrics().elidedText(prog.name, Qt.ElideRight, rect.width() - 52))

    def _draw_right(self, p):
        pic = self._pic_rect()
        # the user tile, framed
        p.setPen(QPen(QColor(255, 255, 255, 200), 2))
        p.setBrush(QColor(255, 255, 255, 60))
        p.drawRoundedRect(QRectF(pic).adjusted(-4, -4, 4, 4), 4, 4)
        draw_user_picture(p, pic)
        f = QFont("Segoe UI")
        f.setPixelSize(12)
        p.setFont(f)
        for item_id, rect in self._right_items():
            label = item_id[1]
            text = user_name() if label == "@user" else label
            if self.hover == item_id:
                self._highlight(p, rect, dark=True)
            p.setPen(QColor(0, 0, 0, 120))
            p.drawText(rect.adjusted(7, 1, 0, 1), Qt.AlignVCenter | Qt.AlignLeft, text)
            p.setPen(QColor("white"))
            p.drawText(rect.adjusted(6, 0, 0, 0), Qt.AlignVCenter | Qt.AlignLeft, text)
        # Shut down and its arrow
        for rect, label in ((self._shutdown_rect(), "Shut down"), (self._arrow_rect(), "")):
            r = QRectF(rect).adjusted(0.5, 0.5, -0.5, -0.5)
            hot = self.hover in (("shutdown", None), ("arrow", None))
            g = QLinearGradient(r.topLeft(), r.bottomLeft())
            g.setColorAt(0, QColor(255, 255, 255, 150 if hot else 110))
            g.setColorAt(0.5, QColor(255, 255, 255, 60 if hot else 30))
            g.setColorAt(1, QColor(255, 255, 255, 90 if hot else 50))
            p.setPen(QPen(QColor(0, 0, 0, 150), 1))
            p.setBrush(g)
            p.drawRoundedRect(r, 3, 3)
            p.setPen(QPen(QColor(255, 255, 255, 120), 1))
            p.setBrush(Qt.NoBrush)
            p.drawRoundedRect(r.adjusted(1, 1, -1, -1), 2, 2)
            if label:
                p.setPen(QColor("white"))
                p.drawText(rect, Qt.AlignCenter, label)
            else:
                c = rect.center()
                p.setPen(Qt.NoPen)
                p.setBrush(QColor("white"))
                p.drawPolygon(QPolygonF([QPointF(c.x() - 3, c.y() - 5), QPointF(c.x() + 3, c.y()),
                                         QPointF(c.x() - 3, c.y() + 5)]))
