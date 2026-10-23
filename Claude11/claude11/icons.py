"""The desktop's icons: Computer, the Recycle Bin, your own folder, and whatever is in C:\\Users\\<you>\\Desktop -
the program folders (Games, Furry Programs, Social Programs...) with their shortcuts, and files you put there.
Positions, selection, dragging, the right-click menus and the desktop's own menu live here (data/desktop.json)."""
import json
import os
import shutil
from pathlib import Path

from PySide6.QtCore import QFileSystemWatcher, QObject, QPoint, QRect, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QFontMetrics, QIcon, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import QApplication, QInputDialog, QMenu, QRubberBand, QStyle, QWidget

from . import sound
from .paths import DATA, icon as asset_icon

STATE_FILE = DATA / "desktop.json"
CELL_W, CELL_H = 90, 94
ICON_SIZES = {"Large icons": 64, "Medium icons": 48, "Small icons": 32}
MARGIN_X, MARGIN_Y = 10, 8
# the program folders on the desktop: folder path -> the Start menu groups that go in it
PROGRAM_FOLDERS = {"Games": ["Games"], "Games/Solitaire & Casual Games": ["Games/Solitaire & Casual Games"],
                   "Games/Classic Games": ["Games/Classic Games"], "Games/Emulation": ["Games/Game Emulation"],
                   "Furry Programs": ["Furry Stuff"], "Social Programs": ["Social Programs"], "Projects": ["Projects"],
                   "Gemini Office": ["Gemini Office"], "GeminiAdobe": ["GeminiAdobe"],
                   "Disc Tools": ["Nero", "Alcohol 120%", "WinRAR", "WinZip"], "Copilot": ["Copilot"],
                   "Windows Tools": ["Windows Tools"]}
# loose shortcuts on a fresh desktop
DESKTOP_SHORTCUTS = ["iexplore", "firefox", "telegram", "discord", "claudeai", "kithylinai", "copilotai", "wmp", "kiwix",
                     "claudecraft", "tv", "secondlife", "furdir", "claudeamp", "torrent", "pystudio"]
# programs that also get a loose desktop icon of their own, besides the one in their folder (added once, even on a
# desktop made before they existed)
LOOSE_TOO = ["hollow"]


def std(which):
    return QApplication.style().standardIcon(which)


def sys_icon(key):
    if key == "sys:recycle":
        from . import vfs
        return asset_icon("Recycle Bin - Full.png" if vfs.recycled() else "Recycle Bin - Empty.png")
    if key == "sys:computer":
        return asset_icon("Internal HD.ico") if not asset_icon("Internal HD.ico").isNull() else std(QStyle.SP_ComputerIcon)
    if key == "sys:network":
        from .network import network_icon
        return network_icon()
    return std(QStyle.SP_DirIcon)


class DesktopIcon(QWidget):
    def __init__(self, manager, key, label, icon, path=None):
        super().__init__(manager.desktop)
        self.manager = manager
        self.key, self.label, self.icon, self.path = key, label, icon, path
        self.selected = False
        self.setFixedSize(CELL_W, CELL_H)
        self.setCursor(Qt.ArrowCursor)

    def kind(self):
        return self.key.split(":")[0]

    def mousePressEvent(self, event):
        self.manager.icon_pressed(self, event)

    def mouseMoveEvent(self, event):
        self.manager.icon_dragged(event)

    def mouseReleaseEvent(self, event):
        self.manager.icon_released(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.manager.open_icons([self])

    def contextMenuEvent(self, event):
        self.manager.icon_menu(self, event.globalPos())

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        size = self.manager.icon_size()
        if self.selected:
            r = QRectF(2, 2, self.width() - 4, self.height() - 4)
            p.setPen(QPen(QColor(255, 255, 255, 120), 1))
            p.setBrush(QColor(255, 255, 255, 70))
            p.drawRoundedRect(r, 4, 4)
        pm = self.icon.pixmap(size, size)
        p.drawPixmap((self.width() - pm.width()) // 2, 6 + (size - pm.height()) // 2, pm)
        f = QFont("Segoe UI")
        f.setPixelSize(12)
        p.setFont(f)
        text_rect = QRect(2, 8 + size, self.width() - 4, self.height() - size - 10)
        flags = Qt.AlignHCenter | Qt.AlignTop | Qt.TextWordWrap
        text = self.label
        fm = QFontMetrics(f)
        if fm.boundingRect(text_rect, flags, text).height() > text_rect.height():
            while text and fm.boundingRect(text_rect, flags, text + "...").height() > text_rect.height():
                text = text[:-1]
            text += "..."
        p.setPen(QColor(0, 0, 0, 170))
        for dx, dy in ((1, 1), (0, 1), (1, 0)):
            p.drawText(text_rect.translated(dx, dy), flags, text)
        p.setPen(QColor("white"))
        p.drawText(text_rect, flags, text)


class IconManager(QObject):
    def __init__(self, desktop):
        super().__init__(desktop)
        self.desktop = desktop
        self.state = {"positions": {}, "hidden": [], "auto_arrange": False, "align_grid": True, "show_icons": True,
                      "size": "Medium icons", "links": [], "folders": 0}
        try:
            with open(STATE_FILE, encoding="utf-8") as f:
                self.state.update(json.load(f))
        except (OSError, ValueError):
            pass
        self.icons = []
        self.press = None
        self.dragging = False
        self.band = QRubberBand(QRubberBand.Rectangle, desktop)
        self.band_origin = None
        self.editor = None
        self.watcher = QFileSystemWatcher(self)
        self.rescan_timer = QTimer(self)
        self.rescan_timer.setSingleShot(True)
        self.rescan_timer.timeout.connect(self.rescan)
        self.watcher.directoryChanged.connect(lambda _p: self.rescan_timer.start(300))
        desktop.setAcceptDrops(True)

    # ---- the Desktop folder and its program shortcuts ----
    def folder(self):
        from . import vfs
        vfs.setup_c()
        d = vfs.user_home() / "Desktop"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def ensure_program_folders(self):
        """Make the program folders and their shortcuts for every program not linked yet (a shortcut you deleted
        stays deleted: only programs never linked before get one)."""
        from claudexp import programs
        from claudexp.explorer import shortcuts
        from claudexp.programs import installed
        desktop = self.folder()
        linked = set(self.state["links"])
        gone = installed.removed()
        groups = {}
        for folder_name, group_names in PROGRAM_FOLDERS.items():
            for g in group_names:
                groups[g] = folder_name
        changed = False
        for prog in programs.PROGRAMS:
            if not prog.listed or prog.key in gone or prog.key in linked:
                continue
            target = groups.get(prog.group)
            if target is None and prog.key not in DESKTOP_SHORTCUTS:
                continue
            if prog.key in programs.FOLDER_SHORTCUTS and not programs.archive_folder(prog.key):
                continue
            where = desktop / target if target else desktop
            where.mkdir(parents=True, exist_ok=True)
            link = where / f"{prog.name}.lnk"
            if not link.exists():
                try:
                    shortcuts.make(link, program=prog.key)
                except Exception:
                    continue
            linked.add(prog.key)
            changed = True
        for key in LOOSE_TOO:
            prog = next((p for p in programs.PROGRAMS if p.key == key), None)
            if prog is None or key in gone or f"{key}@desktop" in linked:
                continue
            link = desktop / f"{prog.name}.lnk"
            if not link.exists():
                try:
                    shortcuts.make(link, program=key)
                except Exception:
                    continue
            linked.add(f"{key}@desktop")
            changed = True
        if changed:
            self.state["links"] = sorted(linked)
            self.save()

    def builtins(self):
        from .user import user_name
        return [("sys:computer", "This PC"), ("sys:recycle", "Recycle Bin"), ("sys:home", user_name()),
                ("sys:network", "Network")]

    def rescan(self):
        """Read the desktop folder and rebuild the icons (keeping their positions)."""
        from claudexp.explorer import shortcuts
        from . import vfs
        for icon in self.icons:
            icon.deleteLater()
        self.icons = []
        folder = self.folder()
        if str(folder) not in self.watcher.directories():
            self.watcher.addPath(str(folder))
        hidden = set(self.state["hidden"])
        entries = []
        for key, label in self.builtins():
            if key not in hidden:
                entries.append((key, label, sys_icon(key), None))
        try:
            files = sorted(folder.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except OSError:
            files = []
        for path in files:
            if vfs.hidden(path) or path.name.startswith("."):
                continue
            key = f"file:{path.name}"
            if key in hidden:
                continue
            if path.is_dir():
                icon = std(QStyle.SP_DirIcon)
                label = path.name
            elif shortcuts.is_shortcut(path):
                icon = shortcuts.icon(path)
                label = path.stem
            else:
                icon = self._file_icon(path)
                label = path.name
            entries.append((key, label, icon, path))
        for key, label, icon, path in entries:
            w = DesktopIcon(self, key, label, icon, path)
            self.icons.append(w)
        self.layout()
        for w in self.icons:
            w.setVisible(self.state["show_icons"])
        self.stack_below_windows()

    def _file_icon(self, path):
        from claudexp.explorer.fileicons import XPIconProvider
        try:
            from PySide6.QtCore import QFileInfo
            return XPIconProvider().icon(QFileInfo(str(path)))
        except Exception:
            return std(QStyle.SP_FileIcon)

    def icon(self, key):
        return next((i for i in self.icons if i.key == key), None)

    def icon_size(self):
        return ICON_SIZES.get(self.state.get("size"), 48)

    # ---- positions ----
    def rows(self):
        return max(1, (self.desktop.work_area().height() - MARGIN_Y) // CELL_H)

    def cell_pos(self, col, row):
        return QPoint(MARGIN_X + col * CELL_W, MARGIN_Y + row * CELL_H)

    def cell_of(self, pos):
        col = max(0, round((pos.x() - MARGIN_X) / CELL_W))
        row = max(0, min(self.rows() - 1, round((pos.y() - MARGIN_Y) / CELL_H)))
        return col, row

    def occupied(self, ignore=()):
        return {self.cell_of(i.pos()) for i in self.icons if i not in ignore}

    def free_cell(self, near=None, ignore=()):
        taken = self.occupied(ignore)
        rows = self.rows()
        if near is not None and near not in taken:
            return near
        for col in range(0, 40):
            for row in range(rows):
                if (col, row) not in taken:
                    return col, row
        return 0, 0

    def layout(self):
        rows = self.rows()
        shown = self.state["show_icons"] and getattr(self.desktop, "explorer_running", True)
        for icon in self.icons:
            icon.setVisible(shown)
        if self.state["auto_arrange"]:
            for i, icon in enumerate(self.icons):
                icon.move(self.cell_pos(i // rows, i % rows))
            return
        placed = set()
        for icon in self.icons:
            saved = self.state["positions"].get(icon.key)
            if saved:
                col, row = saved
                if self.state["align_grid"]:
                    icon.move(self.cell_pos(col, min(row, rows - 1)))
                else:
                    icon.move(QPoint(col, row))
                placed.add(icon)
        for icon in self.icons:
            if icon not in placed:
                col, row = self.free_cell(ignore=[i for i in self.icons if i not in placed])
                icon.move(self.cell_pos(col, row))
                placed.add(icon)
                self.state["positions"][icon.key] = [col, row]
        self.save()

    def stack_below_windows(self):
        for icon in self.icons:
            icon.lower()

    def arrange_by(self, how):
        keys = {"name": lambda i: i.label.lower(), "size": lambda i: (i.path.stat().st_size if i.path and i.path.is_file() else 0),
                "type": lambda i: (i.kind(), i.path.suffix.lower() if i.path else "", i.label.lower()),
                "date": lambda i: (i.path.stat().st_mtime if i.path else 0)}
        self.icons.sort(key=keys.get(how, keys["name"]))
        sysfirst = [i for i in self.icons if i.kind() == "sys"] + [i for i in self.icons if i.kind() != "sys"]
        self.icons = sysfirst
        rows = self.rows()
        self.state["positions"] = {}
        for i, icon in enumerate(self.icons):
            icon.move(self.cell_pos(i // rows, i % rows))
            self.state["positions"][icon.key] = [i // rows, i % rows]
        self.save()

    def toggle(self, option):
        self.state[option] = not self.state[option]
        if option == "show_icons":
            for icon in self.icons:
                icon.setVisible(self.state["show_icons"])
        elif option == "align_grid" and self.state["align_grid"]:
            for icon in self.icons:
                self.state["positions"][icon.key] = list(self.cell_of(icon.pos()))
        self.save()
        self.layout()

    def set_size(self, name):
        self.state["size"] = name
        self.save()
        for icon in self.icons:
            icon.update()

    def refresh(self):
        self.rescan()

    def save(self):
        try:
            STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            STATE_FILE.write_text(json.dumps(self.state, indent=2), encoding="utf-8")
        except OSError:
            pass

    def ready(self):
        self.ensure_program_folders()
        self.rescan()

    # ---- selection and dragging ----
    def selected(self):
        return [i for i in self.icons if i.selected]

    def select(self, icons, add=False):
        for i in self.icons:
            new = i in icons or (add and i.selected)
            if new != i.selected:
                i.selected = new
                i.update()

    def clear_selection(self):
        self.select([])

    clear = clear_selection

    def icon_pressed(self, icon, event):
        self.desktop.hide_start_menu()
        self.desktop.activate(None)
        if event.button() == Qt.RightButton:
            if not icon.selected:
                self.select([icon])
            return
        if event.button() != Qt.LeftButton:
            return
        if event.modifiers() & Qt.ControlModifier:
            icon.selected = not icon.selected
            icon.update()
        elif not icon.selected:
            self.select([icon])
        self.press = (event.globalPosition().toPoint(), {i: i.pos() for i in self.selected()})
        self.dragging = False
        for i in self.selected():
            i.raise_()

    def icon_dragged(self, event):
        if self.press is None:
            return
        start, origins = self.press
        d = event.globalPosition().toPoint() - start
        if not self.dragging and d.manhattanLength() < 6:
            return
        self.dragging = True
        for i, origin in origins.items():
            i.move(origin + d)

    def icon_released(self, event):
        if self.press is None:
            return
        start, origins = self.press
        self.press = None
        if not self.dragging:
            return
        self.dragging = False
        area = self.desktop.work_area()
        moved = list(origins)
        for i in moved:
            pos = i.pos()
            pos.setX(max(0, min(pos.x(), area.width() - CELL_W)))
            pos.setY(max(0, min(pos.y(), area.height() - CELL_H)))
            if self.state["align_grid"] or self.state["auto_arrange"]:
                col, row = self.free_cell(self.cell_of(pos), ignore=moved)
                i.move(self.cell_pos(col, row))
                self.state["positions"][i.key] = [col, row]
            else:
                i.move(pos)
                self.state["positions"][i.key] = [pos.x(), pos.y()]
        if self.state["auto_arrange"]:
            self.layout()
        self.save()
        self.stack_below_windows()

    def desktop_pressed(self, event):
        self.desktop.hide_start_menu()
        if event.button() == Qt.LeftButton:
            if not event.modifiers() & Qt.ControlModifier:
                self.clear_selection()
            self.band_origin = event.position().toPoint()
            self.band.setGeometry(QRect(self.band_origin, self.band_origin))
            self.band.show()

    def desktop_dragged(self, event):
        if self.band_origin is not None and self.band.isVisible():
            r = QRect(self.band_origin, event.position().toPoint()).normalized()
            self.band.setGeometry(r)
            self.select([i for i in self.icons if r.intersects(i.geometry())], add=False)

    def desktop_released(self, event):
        if self.band_origin is not None:
            self.band.hide()
            self.band_origin = None

    def key_pressed(self, event):
        key = event.key()
        if key in (Qt.Key_Return, Qt.Key_Enter) and self.selected():
            self.open_icons(self.selected())
        elif key == Qt.Key_Delete and self.selected():
            self.delete()
        elif key == Qt.Key_F2 and self.selected():
            self.rename()
        elif key == Qt.Key_F5:
            self.rescan()
        elif key == Qt.Key_A and event.modifiers() & Qt.ControlModifier:
            self.select(self.icons)
        else:
            return False
        return True

    # ---- opening ----
    def open_icons(self, icons):
        from claudexp import explorer, programs
        from claudexp.explorer import shortcuts, viewers
        from . import vfs
        for icon in icons:
            sound.play("navigate")
            key = icon.key
            if key == "sys:computer":
                explorer.launch(self.desktop)
            elif key == "sys:recycle":
                explorer.launch(self.desktop, explorer.RECYCLE_BIN)
            elif key == "sys:home":
                explorer.launch(self.desktop, vfs.user_home())
            elif key == "sys:network":
                from . import network
                network.get(self.desktop)._show_status()
            elif icon.path is not None:
                if icon.path.is_dir():
                    explorer.launch(self.desktop, icon.path)
                elif shortcuts.is_shortcut(icon.path):
                    data = shortcuts.read(icon.path)
                    prog = data.get("program") if isinstance(data, dict) else None
                    target = data.get("target") if isinstance(data, dict) else None
                    if prog:
                        programs.launch(self.desktop, prog)
                    elif target and Path(target).is_dir():
                        explorer.launch(self.desktop, Path(target))
                    elif target:
                        viewers.open_file(self.desktop, Path(target))
                else:
                    viewers.open_file(self.desktop, icon.path)

    # ---- changing the desktop ----
    @staticmethod
    def _unique(folder, name):
        path = folder / name
        n = 2
        while path.exists():
            stem, suffix = os.path.splitext(name)
            path = folder / f"{stem} ({n}){suffix}"
            n += 1
        return path

    def new_item(self, kind, at=None):
        folder = self.folder()
        if kind == "folder":
            path = self._unique(folder, "New folder")
            path.mkdir()
        elif kind == "text":
            path = self._unique(folder, "New Text Document.txt")
            path.write_text("", encoding="utf-8")
        else:
            return
        key = f"file:{path.name}"
        if at is not None:
            self.state["positions"][key] = list(self.cell_of(at))
        self.rescan()
        icon = self.icon(key)
        if icon is not None:
            self.select([icon])
            self.rename(icon)

    def paste(self, at=None):
        md = QApplication.clipboard().mimeData()
        if md.hasUrls():
            self.copy_in([Path(u.toLocalFile()) for u in md.urls() if u.isLocalFile()], at=at)

    def copy_in(self, paths, move=False, at=None):
        folder = self.folder()
        for src in paths:
            if not src.exists() or src.parent == folder:
                continue
            dest = self._unique(folder, src.name)
            try:
                if move:
                    shutil.move(str(src), str(dest))
                elif src.is_dir():
                    shutil.copytree(src, dest)
                else:
                    shutil.copy2(src, dest)
            except OSError:
                continue
            if at is not None:
                self.state["positions"][f"file:{dest.name}"] = list(self.cell_of(at))
        self.rescan()

    def drop_files(self, paths, at):
        self.copy_in(paths, at=at)

    def copy_selected(self, move=False):
        from PySide6.QtCore import QMimeData, QUrl
        md = QMimeData()
        md.setUrls([QUrl.fromLocalFile(str(i.path)) for i in self.selected() if i.path])
        QApplication.clipboard().setMimeData(md)

    def delete(self, icons=None):
        from . import vfs
        from .dialogs import msgbox
        icons = [i for i in (icons or self.selected()) if i.path is not None]
        if not icons:
            return
        names = icons[0].label if len(icons) == 1 else f"these {len(icons)} items"

        def go(answer):
            if answer != "Yes":
                return
            for i in icons:
                try:
                    vfs.recycle(i.path)
                except OSError:
                    pass
            sound.play("recycle")
            self.rescan()
        msgbox(self.desktop, "Delete Folder" if icons[0].path.is_dir() else "Delete File",
               f"Are you sure you want to move {names} to the Recycle Bin?", "question", ("Yes", "No"), go)

    def set_hidden(self, hidden_keys):
        self.state["hidden"] = list(hidden_keys)
        self.save()
        self.rescan()

    def rename(self, icon=None):
        icon = icon or (self.selected() or [None])[0]
        if icon is None or icon.path is None:
            return
        old = icon.path
        name, ok = QInputDialog.getText(self.desktop, "Rename", "New name:", text=old.stem if old.is_file() else old.name)
        if not ok or not name.strip():
            return
        new = old.with_name(name.strip() + (old.suffix if old.is_file() else ""))
        try:
            old.rename(new)
        except OSError:
            return
        pos = self.state["positions"].pop(icon.key, None)
        if pos:
            self.state["positions"][f"file:{new.name}"] = pos
        self.rescan()

    # ---- menus ----
    def _menu(self):
        from .shims import MENU_CSS
        menu = QMenu(self.desktop)
        menu.setStyleSheet(MENU_CSS)
        return menu

    def icon_menu(self, icon, global_pos):
        from claudexp import programs
        from claudexp.explorer import shortcuts
        menu = self._menu()
        a = menu.addAction("Open", lambda: self.open_icons(self.selected() or [icon]))
        f = a.font()
        f.setBold(True)
        a.setFont(f)
        if icon.key == "sys:recycle":
            from . import vfs
            menu.addAction("Empty Recycle Bin", self._empty_recycle_bin).setEnabled(bool(vfs.recycled()))
        if icon.path is not None and shortcuts.is_shortcut(icon.path):
            data = shortcuts.read(icon.path)
            prog = data.get("program") if isinstance(data, dict) else None
            if prog:
                from .taskbar import pinned, set_pinned
                if prog in pinned():
                    menu.addAction("Unpin from Taskbar", lambda: (set_pinned([k for k in pinned() if k != prog]),
                                                                   self.desktop.taskbar.update()))
                else:
                    menu.addAction("Pin to Taskbar", lambda: (set_pinned(pinned() + [prog]), self.desktop.taskbar.update()))
                if prog not in programs.PINNED:
                    menu.addAction("Pin to Start Menu", lambda: programs.PINNED.append(prog))
        menu.addSeparator()
        if icon.path is not None:
            menu.addAction("Cut", lambda: (self.copy_selected(True), None))
            menu.addAction("Copy", self.copy_selected)
            menu.addSeparator()
            menu.addAction("Delete", lambda: self.delete(self.selected() or [icon]))
            menu.addAction("Rename", lambda: self.rename(icon))
            menu.addSeparator()
        menu.addAction("Properties", lambda: self.properties(icon))
        menu.popup(global_pos)

    def desktop_menu(self, global_pos):
        menu = self._menu()
        at = self.desktop.mapFromGlobal(global_pos)
        view = menu.addMenu("View")
        for name in ICON_SIZES:
            a = view.addAction(name, lambda n=name: self.set_size(n))
            a.setCheckable(True)
            a.setChecked(self.state.get("size") == name)
        view.addSeparator()
        for label, opt in (("Auto arrange icons", "auto_arrange"), ("Align icons to grid", "align_grid")):
            a = view.addAction(label, lambda o=opt: self.toggle(o))
            a.setCheckable(True)
            a.setChecked(bool(self.state[opt]))
        view.addSeparator()
        a = view.addAction("Show desktop icons", lambda: self.toggle("show_icons"))
        a.setCheckable(True)
        a.setChecked(bool(self.state["show_icons"]))
        sort = menu.addMenu("Sort by")
        for label, how in (("Name", "name"), ("Size", "size"), ("Item type", "type"), ("Date modified", "date")):
            sort.addAction(label, lambda h=how: self.arrange_by(h))
        menu.addAction("Refresh", self.rescan)
        menu.addSeparator()
        paste = menu.addAction("Paste", lambda: self.paste(at))
        paste.setEnabled(QApplication.clipboard().mimeData().hasUrls())
        menu.addSeparator()
        new = menu.addMenu("New")
        new.addAction("Folder", lambda: self.new_item("folder", at))
        new.addAction("Text Document", lambda: self.new_item("text", at))
        menu.addSeparator()
        menu.addAction("Display settings", lambda: self._personalize("display"))
        menu.addAction("Personalize", lambda: self._personalize("background"))
        menu.addSeparator()
        menu.addAction("Widgets", self._gadgets)
        menu.popup(global_pos)

    def _personalize(self, tab):
        from .controlpanel import display_properties
        display_properties(self.desktop, tab=tab)

    def _gadgets(self):
        from .programs import widgets
        widgets.open_gallery(self.desktop)

    def _empty_recycle_bin(self):
        from . import vfs
        from .dialogs import msgbox

        def go(answer):
            if answer == "Yes":
                vfs.empty_recycle_bin()
                self.rescan()
        n = len(vfs.recycled())
        msgbox(self.desktop, "Delete Multiple Items" if n > 1 else "Delete File",
               f"Are you sure you want to permanently delete {'these ' + str(n) + ' items' if n > 1 else 'this item'}?",
               "question", ("Yes", "No"), go)

    def properties(self, icon):
        from .dialogs import properties, size_text, system_info
        from . import vfs
        if icon.key == "sys:computer":
            system_info(self.desktop)
            return
        if icon.key == "sys:recycle":
            items = vfs.recycled()
            total = sum(p.stat().st_size for p, _o, _w in items if p.is_file())
            properties(self.desktop, "Recycle Bin", [("Items:", str(len(items))), ("Size:", size_text(total)),
                                                     ("Location:", "Recycle Bin")], icon=icon.icon)
            return
        path = icon.path or vfs.user_home()
        try:
            st = path.stat()
            size = sum(f.stat().st_size for f in path.rglob("*") if f.is_file()) if path.is_dir() else st.st_size
        except OSError:
            size = 0
        from .dialogs import date_2001
        rows = [("Type:", "File folder" if path.is_dir() else "File"), ("Location:", vfs.to_virtual(path.parent) or ""),
                ("Size:", size_text(size)), ("-", ""), ("Modified:", date_2001(path.stat().st_mtime))]
        properties(self.desktop, icon.label, rows, icon=icon.icon)
