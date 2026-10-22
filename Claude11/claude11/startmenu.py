"""The Windows 11 Start menu: a rounded panel floating above the centre of the taskbar - the search box, the Pinned
grid with 'All >', the Recommended list, and along the bottom your picture and name with the power button. 'All'
replaces the pinned grid with the alphabetical list of every program (folders for the groups); typing in the search
box shows the matches."""
import json

from PySide6.QtCore import QPoint, QPointF, QRect, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QLineEdit, QMenu, QStyle, QTreeWidget, QTreeWidgetItem, QWidget

from . import sound
from .paths import DATA
from .user import draw_user_picture, user_name

WIDTH, HEIGHT = 640, 690
MARGIN = 32
COLS, ROWS = 6, 3
CELL_W, CELL_H = 96, 84
REC_COLS, REC_ROWS = 2, 3
REC_W, REC_H = 288, 56
FOOT_H = 64
START_FILE = DATA / "start.json"
DEFAULT_PINNED = ["iexplore", "outlook", "mycomputer", "wmp", "photos", "settings",
                  "claudeai", "copilotai", "calc", "notepad", "paint", "snipping",
                  "stickynotes", "moviemaker", "solitaire", "telegram", "discord", "tv"]
TREE_CSS = """
QTreeWidget { background: transparent; border: none; font-family: 'Segoe UI Variable Text', 'Segoe UI';
              font-size: 12px; outline: none; color: #1A1A1A; }
QTreeWidget::item { height: 36px; padding-left: 4px; border-radius: 4px; }
QTreeWidget::item:hover { background: rgba(0, 0, 0, 14); }
QTreeWidget::item:selected { background: rgba(0, 0, 0, 24); color: #1A1A1A; }
QTreeWidget::item:disabled { color: #1A1A1A; }
QTreeWidget::branch { background: transparent; image: none; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: rgba(0, 0, 0, 60); border-radius: 3px; min-height: 24px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""
SEARCH_CSS = """
QLineEdit { background: rgba(255, 255, 255, 220); border: 1px solid rgba(0, 0, 0, 30); border-bottom: 2px solid %s;
            border-radius: 18px; padding: 6px 16px 6px 40px; font-family: 'Segoe UI Variable Text', 'Segoe UI';
            font-size: 13px; color: #1A1A1A; }
"""


def _settings():
    try:
        return json.loads(START_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def start_pinned():
    return list(_settings().get("pinned", DEFAULT_PINNED))


def set_start_pinned(keys):
    data = _settings()
    data["pinned"] = list(keys)
    START_FILE.parent.mkdir(parents=True, exist_ok=True)
    START_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _font(size=12, bold=False):
    from .style import font
    return font(size, QFont.DemiBold if bold else QFont.Normal)


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
        self.search.setPlaceholderText("Search for apps, settings, and documents")
        self.search.textChanged.connect(self._search_changed)
        self.tree = QTreeWidget(self)
        self.tree.setHeaderHidden(True)
        self.tree.setStyleSheet(TREE_CSS)
        self.tree.setIndentation(28)
        self.tree.setIconSize(QSize(24, 24))
        self.tree.setRootIsDecorated(False)
        self.tree.itemClicked.connect(self._tree_clicked)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._tree_menu)
        self.tree.hide()
        self.hide()

    # ---- placing ----
    def place(self):
        from .taskbar import TASKBAR_H
        avail = self.desktop.height() - TASKBAR_H - 12
        h = max(420, min(HEIGHT, avail))
        if h != self.height():
            self.setFixedSize(WIDTH, h)
        self.move((self.desktop.width() - WIDTH) // 2, self.desktop.height() - TASKBAR_H - self.height() - 12)
        self._layout()

    def _rows(self):
        """How many pinned rows fit at this height."""
        return max(1, min(ROWS, (self.height() - 420) // CELL_H + 1))

    def _layout(self):
        from . import display
        accent = display.get().accent().name()
        self.search.setStyleSheet(SEARCH_CSS % accent)
        self.search.setGeometry(MARGIN, 20, WIDTH - 2 * MARGIN, 38)
        self.tree.setGeometry(MARGIN, 112, WIDTH - 2 * MARGIN, self.height() - 112 - FOOT_H - 12)

    def focus_search(self):
        QTimer.singleShot(0, self.search.setFocus)

    # ---- geometry ----
    def _pinned_rect(self):
        return QRect(MARGIN, 112, COLS * CELL_W, self._rows() * CELL_H)

    def _all_rect(self):
        return QRect(WIDTH - MARGIN - 70, 76, 70, 28)

    def _rec_header_y(self):
        return self._pinned_rect().bottom() + 20

    def _rec_rect(self):
        y = self._rec_header_y() + 36
        rows = max(1, min(REC_ROWS, (self.height() - FOOT_H - 12 - y) // REC_H))
        return QRect(MARGIN, y, REC_COLS * REC_W, rows * REC_H)

    def _more_rect(self):
        return QRect(WIDTH - MARGIN - 80, self._rec_header_y() - 4, 80, 28)

    def _footer_rect(self):
        return QRect(0, self.height() - FOOT_H, WIDTH, FOOT_H)

    def _user_rect(self):
        f = self._footer_rect()
        return QRect(MARGIN + 8, f.y() + 12, 200, 40)

    def _power_rect(self):
        f = self._footer_rect()
        return QRect(WIDTH - MARGIN - 48, f.y() + 12, 40, 40)

    def _back_rect(self):
        return QRect(WIDTH - MARGIN - 80, 76, 80, 28)

    def _pinned_keys(self):
        from claudexp import programs
        from claudexp.programs import installed
        gone = installed.removed()
        keys = []
        for key in start_pinned():
            if key in gone:
                continue
            try:
                programs.get(key)
            except StopIteration:
                continue
            keys.append(key)
        return keys

    def _pinned_cells(self):
        pr = self._pinned_rect()
        out = []
        for i, key in enumerate(self._pinned_keys()[:COLS * self._rows()]):
            col, row = i % COLS, i // COLS
            out.append((key, QRect(pr.x() + col * CELL_W, pr.y() + row * CELL_H, CELL_W, CELL_H)))
        return out

    def _recommended(self):
        from claudexp import programs
        from claudexp.programs import installed
        gone = installed.removed()
        rr = self._rec_rect()
        n = REC_COLS * (rr.height() // REC_H)
        keys = [k for k in programs.recent if k not in gone][:n]
        out = []
        for i, key in enumerate(keys):
            try:
                programs.get(key)
            except StopIteration:
                continue
            col, row = i % REC_COLS, i // REC_COLS
            out.append((key, QRect(rr.x() + col * REC_W, rr.y() + row * REC_H, REC_W, REC_H)))
        return out

    def _items(self):
        items = []
        if self.mode == "main":
            items += [(("pin", key), r) for key, r in self._pinned_cells()]
            items += [(("rec", key), r) for key, r in self._recommended()]
            items.append((("all", None), self._all_rect()))
            items.append((("more", None), self._more_rect()))
        else:
            items.append((("back", None), self._back_rect()))
        items.append((("user", None), self._user_rect()))
        items.append((("power", None), self._power_rect()))
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
        self.focus_search()

    def hideEvent(self, event):
        self.hover = None
        self.search.clear()

    def _set_mode(self, mode):
        self.mode = mode
        self.tree.setVisible(mode != "main")
        if mode == "all":
            self._fill_tree()
        self.update()

    # ---- the All apps list and search results ----
    def _listed(self):
        from claudexp import programs
        from claudexp.programs import installed
        gone = installed.removed()
        return [p for p in programs.PROGRAMS if p.listed and p.key not in gone
                and (p.key not in programs.FOLDER_SHORTCUTS or programs.archive_folder(p.key))]

    def _header(self, text):
        head = QTreeWidgetItem([text])
        head.setFlags(Qt.ItemIsEnabled)
        f = _font(12, bold=True)
        head.setFont(0, f)
        head.setForeground(0, QColor("#1A1A1A"))
        return head

    def _fill_tree(self, query=""):
        self.tree.clear()
        listed = self._listed()
        folder_icon = self.style().standardIcon(QStyle.SP_DirIcon)
        if query:
            q = query.lower()
            hits = sorted([p for p in listed if q in p.name.lower() or q in p.blurb.lower()], key=lambda p: p.name)
            if hits:
                head = self._header("Best match")
                self.tree.addTopLevelItem(head)
                for prog in hits[:30]:
                    item = QTreeWidgetItem([prog.name])
                    item.setIcon(0, prog.icon())
                    item.setData(0, Qt.UserRole, prog.key)
                    self.tree.addTopLevelItem(item)
            else:
                self.tree.addTopLevelItem(self._header("No results for \"" + query + "\""))
            return
        # top level: loose programs and the group folders, in one alphabet with letter headers
        entries = []
        groups = {}
        for prog in listed:
            if prog.group:
                top = prog.group.split("/")[0]
                groups.setdefault(top, []).append(prog)
            else:
                entries.append((prog.name, "prog", prog))
        for name, progs in groups.items():
            entries.append((name, "group", progs))
        entries.sort(key=lambda e: e[0].lower())
        letter = None
        for name, kind, payload in entries:
            first = name[0].upper()
            if not first.isalpha():
                first = "#"
            if first != letter:
                letter = first
                self.tree.addTopLevelItem(self._header(letter))
            if kind == "prog":
                item = QTreeWidgetItem([payload.name])
                item.setIcon(0, payload.icon())
                item.setData(0, Qt.UserRole, payload.key)
                self.tree.addTopLevelItem(item)
            else:
                folder = QTreeWidgetItem([name])
                folder.setIcon(0, folder_icon)
                folder.setData(0, Qt.UserRole, None)
                self.tree.addTopLevelItem(folder)
                subs = {}
                for prog in sorted(payload, key=lambda p: p.name.lower()):
                    parts = prog.group.split("/")
                    parent = folder
                    for part in parts[1:]:
                        path = "/".join(parts[:parts.index(part) + 1])
                        if path not in subs:
                            sub = QTreeWidgetItem([part])
                            sub.setIcon(0, folder_icon)
                            sub.setData(0, Qt.UserRole, None)
                            parent.addChild(sub)
                            subs[path] = sub
                        parent = subs[path]
                    item = QTreeWidgetItem([prog.name])
                    item.setIcon(0, prog.icon())
                    item.setData(0, Qt.UserRole, prog.key)
                    parent.addChild(item)

    def _tree_clicked(self, item, _col):
        key = item.data(0, Qt.UserRole)
        if key is None:
            if item.flags() & Qt.ItemIsSelectable:
                item.setExpanded(not item.isExpanded())
            return
        self._launch(key)

    def _tree_menu(self, pos):
        item = self.tree.itemAt(pos)
        if item is None or not item.data(0, Qt.UserRole):
            return
        key = item.data(0, Qt.UserRole)
        self._program_menu(key, self.tree.viewport().mapToGlobal(pos), pinned_here=key in start_pinned())

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
        pos = event.position().toPoint()
        item = self._item_at(pos)
        if event.button() == Qt.RightButton:
            if item and item[0] in ("pin", "rec"):
                self._program_menu(item[1], event.globalPosition().toPoint(), pinned_here=item[0] == "pin")
            return
        if event.button() != Qt.LeftButton or item is None:
            return
        kind, value = item
        if kind == "all":
            self._set_mode("all")
        elif kind == "back":
            self._set_mode("main")
        elif kind == "more":
            self._set_mode("all")
        elif kind == "user":
            self._user_menu()
        elif kind == "power":
            self._power_menu()
        elif kind in ("pin", "rec"):
            self._launch(value)

    def _launch(self, key):
        from claudexp import programs
        self.desktop.hide_start_menu()
        sound.play("menu")
        programs.launch(self.desktop, key)

    def _menu(self):
        from .shims import MENU_CSS
        menu = QMenu(self)
        menu.setStyleSheet(MENU_CSS)
        return menu

    def _program_menu(self, key, gp, pinned_here):
        from claudexp import programs
        from .taskbar import pinned as tb_pinned, set_pinned as set_tb_pinned
        menu = self._menu()
        try:
            prog = programs.get(key)
        except StopIteration:
            return
        menu.addAction(prog.icon(), "Open", lambda: self._launch(key))
        menu.addSeparator()
        if pinned_here or key in start_pinned():
            menu.addAction("Unpin from Start", lambda: self._pin_start(key, False))
        else:
            menu.addAction("Pin to Start", lambda: self._pin_start(key, True))
        if key in tb_pinned():
            menu.addAction("Unpin from taskbar", lambda: self._pin_taskbar(key, False, tb_pinned, set_tb_pinned))
        else:
            menu.addAction("Pin to taskbar", lambda: self._pin_taskbar(key, True, tb_pinned, set_tb_pinned))
        menu.popup(gp)

    def _pin_start(self, key, on):
        keys = start_pinned()
        if on and key not in keys:
            keys.append(key)
        elif not on and key in keys:
            keys.remove(key)
        set_start_pinned(keys)
        self.update()

    def _pin_taskbar(self, key, on, get, put):
        keys = get()
        if on and key not in keys:
            keys.append(key)
        elif not on and key in keys:
            keys.remove(key)
        put(keys)
        self.desktop.taskbar.update()

    def _user_menu(self):
        menu = self._menu()
        menu.addAction("Change account settings", lambda: self._account_settings())
        menu.addAction("Lock", lambda: self._power("lock"))
        menu.addAction("Sign out", lambda: self._power("logoff"))
        r = self._user_rect()
        menu.popup(self.mapToGlobal(QPoint(r.x(), r.y() - 110)))

    def _account_settings(self):
        self.desktop.hide_start_menu()
        try:
            from .settings import open_settings
            open_settings(self.desktop, "accounts")
        except Exception:
            from .controlpanel import user_accounts
            user_accounts(self.desktop, page=1)

    def _power_menu(self):
        menu = self._menu()
        menu.addAction("Sleep", lambda: self._power("sleep"))
        menu.addAction("Shut down", lambda: self._power("shutdown"))
        menu.addAction("Restart", lambda: self._power("restart"))
        r = self._power_rect()
        menu.popup(self.mapToGlobal(QPoint(r.x() - 60, r.y() - 110)))

    def _power(self, what):
        self.desktop.hide_start_menu()
        sound.play("menu")
        d = self.desktop
        {"logoff": d.log_off, "lock": d.lock, "restart": d.restart, "sleep": d.sleep, "shutdown": d.turn_off}[what]()

    # ---- painting ----
    def paintEvent(self, event):
        from claudexp import programs
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        from .taskbar import draw_panel
        draw_panel(p, self.rect(), radius=8, alpha=248)
        # the search box's magnifier
        sr = self.search.geometry()
        c = QPointF(sr.x() + 20, sr.center().y())
        p.setPen(QPen(QColor("#5C5C5C"), 1.5))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPointF(c.x() - 1, c.y() - 1), 5.5, 5.5)
        p.drawLine(QPointF(c.x() + 3, c.y() + 3), QPointF(c.x() + 7, c.y() + 7))
        if self.mode == "main":
            self._draw_main(p, programs)
        else:
            p.setFont(_font(13, bold=True))
            p.setPen(QColor("#1A1A1A"))
            p.drawText(QRect(MARGIN + 4, 76, 300, 28), Qt.AlignVCenter | Qt.AlignLeft,
                       "All" if self.mode == "all" else "Search results")
            self._small_button(p, self._back_rect(), "‹  Back", self.hover == ("back", None))
        self._draw_footer(p)

    def _small_button(self, p, rect, text, hot):
        r = QRectF(rect).adjusted(0.5, 0.5, -0.5, -0.5)
        p.setPen(QPen(QColor(0, 0, 0, 30), 1))
        p.setBrush(QColor(255, 255, 255, 200 if hot else 140))
        p.drawRoundedRect(r, 4, 4)
        p.setFont(_font(11))
        p.setPen(QColor("#1A1A1A"))
        p.drawText(rect, Qt.AlignCenter, text)

    def _draw_main(self, p, programs):
        p.setFont(_font(13, bold=True))
        p.setPen(QColor("#1A1A1A"))
        p.drawText(QRect(MARGIN + 4, 76, 300, 28), Qt.AlignVCenter | Qt.AlignLeft, "Pinned")
        self._small_button(p, self._all_rect(), "All  ›", self.hover == ("all", None))
        for key, rect in self._pinned_cells():
            try:
                prog = programs.get(key)
            except StopIteration:
                continue
            if self.hover == ("pin", key):
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(0, 0, 0, 14))
                p.drawRoundedRect(QRectF(rect).adjusted(2, 2, -2, -2), 6, 6)
            pm = prog.icon().pixmap(32, 32)
            p.drawPixmap(rect.x() + (rect.width() - pm.width()) // 2, rect.y() + 12 + (32 - pm.height()) // 2, pm)
            p.setFont(_font(11))
            p.setPen(QColor("#1A1A1A"))
            tr = QRect(rect.x() + 4, rect.y() + 50, rect.width() - 8, 30)
            text = prog.name
            fm = p.fontMetrics()
            if fm.boundingRect(tr, Qt.AlignHCenter | Qt.TextWordWrap, text).height() > tr.height():
                text = fm.elidedText(text, Qt.ElideRight, tr.width() * 2 - 10)
            p.drawText(tr, Qt.AlignHCenter | Qt.AlignTop | Qt.TextWordWrap, text)
        hy = self._rec_header_y()
        p.setFont(_font(13, bold=True))
        p.setPen(QColor("#1A1A1A"))
        p.drawText(QRect(MARGIN + 4, hy - 4, 300, 28), Qt.AlignVCenter | Qt.AlignLeft, "Recommended")
        self._small_button(p, self._more_rect(), "More  ›", self.hover == ("more", None))
        recs = self._recommended()
        if not recs:
            p.setFont(_font(12))
            p.setPen(QColor("#5C5C5C"))
            p.drawText(self._rec_rect().adjusted(8, 0, 0, 0), Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap,
                       "The programs and files you open show up here, so you can get back to them quickly.")
        for i, (key, rect) in enumerate(recs):
            try:
                prog = programs.get(key)
            except StopIteration:
                continue
            if self.hover == ("rec", key):
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(0, 0, 0, 14))
                p.drawRoundedRect(QRectF(rect).adjusted(0, 2, -8, -2), 6, 6)
            pm = prog.icon().pixmap(28, 28)
            p.drawPixmap(rect.x() + 12, rect.y() + (rect.height() - pm.height()) // 2, pm)
            p.setFont(_font(12))
            p.setPen(QColor("#1A1A1A"))
            p.drawText(QRect(rect.x() + 52, rect.y() + 10, rect.width() - 64, 18), Qt.AlignVCenter | Qt.AlignLeft,
                       p.fontMetrics().elidedText(prog.name, Qt.ElideRight, rect.width() - 70))
            p.setFont(_font(11))
            p.setPen(QColor("#5C5C5C"))
            p.drawText(QRect(rect.x() + 52, rect.y() + 29, rect.width() - 64, 16), Qt.AlignVCenter | Qt.AlignLeft,
                       "Recently used" if i else "Just now")

    def _draw_footer(self, p):
        fr = self._footer_rect()
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 10))
        from PySide6.QtGui import QPainterPath
        path = QPainterPath()
        path.addRoundedRect(QRectF(fr).adjusted(0.5, 0, -0.5, -0.5), 8, 8)
        path.addRect(QRectF(fr.x() + 0.5, fr.y(), fr.width() - 1, 10))
        p.drawPath(path.simplified())
        p.setPen(QPen(QColor(0, 0, 0, 16), 1))
        p.drawLine(fr.x() + 1, fr.y(), fr.right(), fr.y())
        ur = self._user_rect()
        if self.hover == ("user", None):
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(0, 0, 0, 14))
            p.drawRoundedRect(QRectF(ur).adjusted(-8, 0, 8, 0), 6, 6)
        draw_user_picture(p, QRect(ur.x(), ur.y() + 4, 32, 32), circle=True)
        p.setFont(_font(12))
        p.setPen(QColor("#1A1A1A"))
        p.drawText(QRect(ur.x() + 44, ur.y(), ur.width() - 44, ur.height()), Qt.AlignVCenter | Qt.AlignLeft, user_name())
        pr = self._power_rect()
        if self.hover == ("power", None):
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(0, 0, 0, 14))
            p.drawRoundedRect(QRectF(pr), 6, 6)
        c = pr.center()
        pen = QPen(QColor("#1A1A1A"), 1.6)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        p.drawArc(QRectF(c.x() - 7, c.y() - 6, 14, 14), 60 * 16, 300 * 16)
        p.drawLine(QPointF(c.x(), c.y() - 9), QPointF(c.x(), c.y() - 1))
