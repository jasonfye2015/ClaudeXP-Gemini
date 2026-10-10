"""Desktop icons, like XP: drag them around (snapping to a grid), rubber-band select, Arrange Icons By,
Auto Arrange, Refresh, a real Desktop folder (C:\\Documents and Settings\\<you>\\Desktop) whose files and
folders show up as icons, rename in place, delete to the Recycle Bin, and drop files in from Windows.

Positions and options are saved in data/desktop.json.
"""
import json
import shutil
import time
from pathlib import Path

from PySide6.QtCore import QFileInfo, QFileSystemWatcher, QObject, QPoint, QRect, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QIcon, QPainter
from PySide6.QtWidgets import QApplication, QFileIconProvider, QLineEdit, QMenu, QRubberBand, QStyle, QWidget
from shiboken6 import isValid

from . import programs, sound
from .paths import DATA, pixmap

STATE_FILE = DATA / "desktop.json"
CELL_W, CELL_H = 80, 78
ORIGIN = QPoint(6, 6)
MENU_STYLE = ("QMenu { background: white; border: 1px solid #ACA899; font-family: Tahoma; font-size: 11px; }"
              " QMenu::item { padding: 4px 24px 4px 20px; } QMenu::item:selected { background: #316AC5; color: white; }"
              " QMenu::item:disabled { color: #ACA899; }")
SORTS = ("Name", "Size", "Type", "Modified")
LAYOUT = 8                  # bump when builtins() changes order
# Desktop folders of program shortcuts, made once (layout 3); they sit right after the E: folder links.
PROGRAM_FOLDERS = {"Furry Programs": ["comix", "folio", "stories", "cdviewer", "furcon", "furvideo", "furdir", "furlog", "furlocator"],
                   "Emulation": ["nes", "snes", "gb", "gbc", "gba", "gen", "sms", "gg", "apple2"],
                   # the desktop Games folder mirrors Start > Programs > Games
                   "Games": [p.key for p in programs.PROGRAMS if p.group == "Games"],
                   "GeminiOffice": [p.key for p in programs.PROGRAMS if p.group == "Gemini Office"],
                   "GeminiAdobe": [p.key for p in programs.PROGRAMS if p.group == "GeminiAdobe"],
                   "Disc Tools": ["nero", "alcohol120"],
                   "Archive Tools": ["winrar", "winzip"]}
# the layout version that last changed each folder (an upgrade adds the shortcuts it's missing; it never removes)
FOLDERS_SINCE = {"Furry Programs": 18, "Emulation": 3, "Games": 10,
                 "GeminiOffice": 11, "GeminiAdobe": 15, "Disc Tools": 16, "Archive Tools": 16}
# Folder contents get their own version, so adding a shortcut doesn't reflow the desktop's icons (LAYOUT does).
FOLDERS = 18


def std(which):
    return QApplication.style().standardIcon(which)


def builtins():
    """The icons Windows puts on the desktop: system icons and program shortcuts. (key, label, icon getter)"""
    folders = [(f"prog:{key}", label, lambda: std(QStyle.SP_DirIcon))
               for key, (label, _prefix) in programs.FOLDER_SHORTCUTS.items() if programs.archive_folder(key)]
    return [
        ("sys:recycle", "Recycle Bin", lambda: std(QStyle.SP_TrashIcon)),
        ("sys:mycomputer", "My Computer", lambda: std(QStyle.SP_ComputerIcon)),
        ("prog:connect", "America Online", lambda: QIcon(pixmap("aol_icon.png"))),
    ] + folders + [
        ("prog:tv", "ClaudeTV", lambda: programs.get("tv").icon()),
        ("prog:claudeamp", "ClaudeAmp", lambda: programs.get("claudeamp").icon()),
        ("prog:flash", "Flash Player", lambda: programs.get("flash").icon()),
        ("prog:torrent", "ClaudeTorrent", lambda: programs.get("torrent").icon()),
        ("prog:rpg", "ClaudeRPG", lambda: programs.get("rpg").icon()),
        ("prog:navigator", "Netscape Navigator", lambda: programs.get("navigator").icon()),
        ("prog:claudeai", "ClaudeAI", lambda: programs.get("claudeai").icon()),
        ("prog:copilotai", "CopilotAI", lambda: programs.get("copilotai").icon()),
        ("prog:imagecreator", "Copilot Image Creator", lambda: programs.get("imagecreator").icon()),
        ("prog:neko", "Copilot Neko", lambda: programs.get("neko").icon()),
        ("prog:copilotwidgets", "Copilot Widgets", lambda: programs.get("copilotwidgets").icon()),
        ("prog:aim", "ClaudeAIM", lambda: programs.get("aim").icon()),
        ("prog:irc", "ClaudeIRC", lambda: programs.get("irc").icon()),
        ("prog:muck", "ClaudeMUCK", lambda: programs.get("muck").icon()),
        ("prog:pystudio", "Copilot Python Studio", lambda: programs.get("pystudio").icon()),
    ]


class DesktopIcon(QWidget):
    W, H = 76, 70

    def __init__(self, manager, key, label, icon, path=None):
        super().__init__(manager.desktop)
        self.manager = manager
        self.key, self.label, self.icon, self.path = key, label, icon, path
        self.selected = False
        self.setFixedSize(self.W, self.H)
        self.setFocusPolicy(Qt.ClickFocus)

    @property
    def kind(self):
        return self.key.split(":", 1)[0]     # sys | prog | file

    def text_rect(self):
        return QRect(2, 38, self.W - 4, self.H - 38)

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
        pm = self.icon.pixmap(32, 32, QIcon.Selected if self.selected else QIcon.Normal)
        p.drawPixmap((self.W - 32) // 2, 2, pm)
        p.setFont(QFont("Tahoma", 8))
        flags = Qt.AlignHCenter | Qt.AlignTop | Qt.TextWordWrap
        rect = self.text_rect()
        if self.selected:
            bounds = p.boundingRect(rect, flags, self.label).adjusted(-2, 0, 2, 0)
            p.fillRect(bounds, QColor("#316AC5"))
        else:
            p.setPen(QColor(0, 0, 0, 200))
            p.drawText(rect.translated(1, 1), flags, self.label)
        p.setPen(QColor("white"))
        p.drawText(rect, flags, self.label)


class IconManager(QObject):
    def __init__(self, desktop):
        super().__init__(desktop)
        self.desktop = desktop
        self.state = {"positions": {}, "labels": {}, "hidden": [], "auto_arrange": False, "align_grid": True,
                      "show_icons": True}
        try:
            with open(STATE_FILE, encoding="utf-8") as f:
                self.state.update(json.load(f))
        except (OSError, ValueError):
            pass
        if self.state.get("layout", 1) < LAYOUT:
            # The built-in shortcuts were reordered: let them flow into the new order once (files keep their spots).
            old = self.state.get("layout", 1)
            self._make_program_folders([n for n, v in FOLDERS_SINCE.items() if old < v])
            if old < 5:                                  # layout 5: the TV left Furry Programs for the desktop
                from .explorer import vfs
                stale = vfs.user_home() / "Desktop" / "Furry Programs" / "FurTV 2000.lnk"
                if stale.exists():
                    stale.unlink()
            self.state["positions"] = {k: v for k, v in self.state["positions"].items()
                                       if not k.startswith(("sys:", "prog:"))
                                       and k[5:] not in PROGRAM_FOLDERS}
            self.state["layout"] = LAYOUT
            self.state["folders"] = FOLDERS
        folders = self.state.get("folders", self.state.get("layout", 1))
        if folders < FOLDERS:
            self._make_program_folders([n for n, v in FOLDERS_SINCE.items() if folders < v])
            self.state["folders"] = FOLDERS
        self.icons = []
        self.press = None          # (global pos, {icon: start pos}) while dragging
        self.dragging = False
        self.band = QRubberBand(QRubberBand.Rectangle, desktop)
        self.band_origin = None
        self.editor = None
        self.icon_provider = QFileIconProvider()
        self.watcher = QFileSystemWatcher(self)
        self.rescan_timer = QTimer(self)
        self.rescan_timer.setSingleShot(True)
        self.rescan_timer.timeout.connect(self.rescan)
        self.watcher.directoryChanged.connect(lambda _p: self.rescan_timer.start(300))
        desktop.setAcceptDrops(True)

    # ---- the Desktop folder -------------------------------------------------------------
    def _make_program_folders(self, names):
        """Desktop folders holding shortcuts to grouped programs."""
        from .explorer import shortcuts, vfs
        from . import programs
        vfs.setup_c()
        desk = vfs.user_home() / "Desktop"
        for name in names:
            keys = PROGRAM_FOLDERS.get(name)
            if keys is None:
                continue
            folder = desk / name
            folder.mkdir(parents=True, exist_ok=True)
            for key in keys:
                prog = next((p for p in programs.PROGRAMS if p.key == key), None)
                if prog is not None and not (folder / f"{prog.name}.lnk").exists():
                    shortcuts.make(folder / f"{prog.name}.lnk", program=key)

    def folder(self):
        from .explorer import vfs
        vfs.setup_c()
        path = vfs.user_home() / "Desktop"
        path.mkdir(parents=True, exist_ok=True)
        if str(path) not in self.watcher.directories():
            self.watcher.addPath(str(path))
        return path

    def rescan(self):
        """Build the icons: built-ins (unless hidden), then whatever is in the Desktop folder."""
        wanted = []
        from .explorer import shortcuts
        desk = self.folder()

        def file_entry(f):
            return (f"file:{f.name}", f.stem if f.is_file() and f.suffix.lower() == ".lnk" else f.name,
                    lambda f=f: std(QStyle.SP_DirIcon) if f.is_dir()
                    else (shortcuts.icon(f) if shortcuts.is_shortcut(f) else None)
                    or self.icon_provider.icon(QFileInfo(str(f))), f)
        folder_links = {f"prog:{k}" for k in programs.FOLDER_SHORTCUTS}
        program_folders = [desk / n for n in PROGRAM_FOLDERS if (desk / n).is_dir()]
        for key, label, icon in builtins():
            if key not in self.state["hidden"]:
                wanted.append((key, self.state["labels"].get(key, label), icon, None))
        # the program folders go right after the last E: folder link (or after America Online)
        keys = [w[0] for w in wanted]
        after = max((keys.index(k) for k in folder_links if k in keys),
                    default=keys.index("prog:connect") if "prog:connect" in keys else len(keys) - 1)
        for i, f in enumerate(program_folders):
            wanted.insert(after + 1 + i, file_entry(f))
        for f in sorted(desk.iterdir(), key=lambda p: p.name.lower()):
            if f.name.startswith(".") or f.name.lower() == "desktop.ini" or f in program_folders:
                continue
            wanted.append(file_entry(f))
        existing = {i.key: i for i in self.icons}
        keep = []
        for key, label, icon, path in wanted:
            item = existing.pop(key, None)
            if item is None:
                item = DesktopIcon(self, key, label, icon(), path)
            else:
                item.label, item.path = label, path
                item.update()
            keep.append(item)
        for gone in existing.values():
            self.state["positions"].pop(gone.key, None)
            gone.deleteLater()
        self.icons = keep
        self.layout()

    # ---- grid and layout --------------------------------------------------------------------
    def rows(self):
        return max(1, (self.desktop.work_area().height() - ORIGIN.y()) // CELL_H)

    def cell_pos(self, col, row):
        return QPoint(ORIGIN.x() + col * CELL_W, ORIGIN.y() + row * CELL_H)

    def cell_of(self, pos):
        col = max(0, round((pos.x() - ORIGIN.x()) / CELL_W))
        row = max(0, min(self.rows() - 1, round((pos.y() - ORIGIN.y()) / CELL_H)))
        return col, row

    def occupied(self, ignore=()):
        return {self.cell_of(i.pos()) for i in self.icons if i not in ignore}

    def free_cell(self, near=None, ignore=()):
        """The free grid cell nearest `near` (or the first free one, column by column)."""
        taken = self.occupied(ignore)
        if near is None:
            col = 0
            while True:
                for row in range(self.rows()):
                    if (col, row) not in taken:
                        return col, row
                col += 1
        c0, r0 = self.cell_of(near)
        for radius in range(0, 60):
            best = None
            for col in range(max(0, c0 - radius), c0 + radius + 1):
                for row in range(max(0, r0 - radius), min(self.rows(), r0 + radius + 1)):
                    if max(abs(col - c0), abs(row - r0)) == radius and (col, row) not in taken:
                        d = (col - c0) ** 2 + (row - r0) ** 2
                        if best is None or d < best[0]:
                            best = (d, col, row)
            if best:
                return best[1], best[2]
        return self.free_cell()

    def layout(self):
        show = self.state["show_icons"]
        if self.state["auto_arrange"]:
            self._place_in_order(sorted(self.icons, key=self._visual_order))
        else:
            placed = []
            for icon in self.icons:
                pos = self.state["positions"].get(icon.key)
                if pos is not None:
                    icon.move(*pos)
                    placed.append(icon)
            for icon in self.icons:
                if icon not in placed:
                    icon.move(self.cell_pos(*self.free_cell(ignore=[i for i in self.icons if i not in placed])))
                    placed.append(icon)
                    self.state["positions"][icon.key] = [icon.x(), icon.y()]
        for icon in self.icons:
            icon.setVisible(show)
        self.stack_below_windows()
        self.save()

    def stack_below_windows(self):
        """Icons sit on the wallpaper, under every open window."""
        for icon in self.icons:
            icon.lower()

    def _visual_order(self, icon):
        pos = self.state["positions"].get(icon.key)
        if pos is None:
            return (10 ** 6, 0)
        col, row = self.cell_of(QPoint(*pos))
        return (col, row)

    def _place_in_order(self, order):
        rows = self.rows()
        for n, icon in enumerate(order):
            icon.move(self.cell_pos(n // rows, n % rows))
            self.state["positions"][icon.key] = [icon.x(), icon.y()]

    def arrange_by(self, how):
        """Arrange Icons By: system icons first, then the rest sorted."""
        def info(icon):
            if icon.path is None:
                return (icon.label.lower(), 0, "Shortcut" if icon.kind == "prog" else "System Folder", 0)
            st = icon.path.stat()
            kind = "File Folder" if icon.path.is_dir() else icon.path.suffix.lower()
            return (icon.label.lower(), st.st_size, kind, st.st_mtime)

        index = SORTS.index(how)
        system = [i for i in self.icons if i.kind == "sys" and i.key != "sys:recycle"]
        rest = [i for i in self.icons if i not in system]
        rest.sort(key=lambda i: (info(i)[index], i.label.lower()), reverse=how in ("Size", "Modified"))
        self._place_in_order(system + rest)
        self.save()

    def toggle(self, option):
        self.state[option] = not self.state[option]
        if option == "auto_arrange" and self.state["auto_arrange"]:
            self.layout()
        elif option == "align_grid" and self.state["align_grid"]:
            for icon in self.icons:
                icon.move(self.cell_pos(*self.free_cell(icon.pos(), ignore=[icon])))
                self.state["positions"][icon.key] = [icon.x(), icon.y()]
        elif option == "show_icons":
            self.layout()
        self.save()

    def refresh(self):
        """Refresh: icons blink off and back, the Desktop folder is re-read."""
        for icon in self.icons:
            icon.hide()
        QTimer.singleShot(150, self.rescan)

    def save(self):
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2)

    # ---- selection ---------------------------------------------------------------------------
    def selected(self):
        return [i for i in self.icons if i.selected]

    def select(self, icons, add=False):
        icons = set(icons)
        for icon in self.icons:
            want = (icon in icons) or (add and icon.selected)
            if icon.selected != want:
                icon.selected = want
                icon.update()

    def clear_selection(self):
        self.select([])

    # ---- pressing and dragging icons -------------------------------------------------------------
    def icon_pressed(self, icon, event):
        self.desktop.setFocus()
        if event.button() == Qt.LeftButton:
            if event.modifiers() & Qt.ControlModifier:
                icon.selected = not icon.selected
                icon.update()
            elif not icon.selected:
                self.select([icon])
            sel = self.selected()
            self.press = (event.globalPosition().toPoint(), {i: QPoint(i.pos()) for i in sel})
            self.dragging = False
            for i in sel:
                i.raise_()
        elif event.button() == Qt.RightButton and not icon.selected:
            self.select([icon])

    def icon_dragged(self, event):
        if self.press is None:
            return
        start, origins = self.press
        delta = event.globalPosition().toPoint() - start
        if not self.dragging and delta.manhattanLength() < 5:
            return
        self.dragging = True
        area = self.desktop.work_area()
        for icon, origin in origins.items():
            p = origin + delta
            icon.move(max(0, min(p.x(), area.width() - icon.width())), max(0, min(p.y(), area.height() - icon.height())))

    def icon_released(self, event):
        if self.press is None:
            return
        start, origins = self.press
        self.press = None
        if not self.dragging:
            if not event.modifiers() & Qt.ControlModifier:
                self.select([i for i in self.icons if i.selected and i.geometry().contains(
                    self.desktop.mapFromGlobal(event.globalPosition().toPoint()))] or self.selected()[:1])
            return
        self.dragging = False
        moved = list(origins)
        drop = self.desktop.mapFromGlobal(event.globalPosition().toPoint())
        target = next((i for i in self.icons if i not in moved and i.geometry().contains(drop)), None)
        if target is not None and target.key == "sys:recycle":
            for icon, origin in origins.items():
                icon.move(origin)
            self.stack_below_windows()
            self.delete(moved)
            return
        if target is not None and target.path is not None and target.path.is_dir():
            files = [i for i in moved if i.path is not None]
            for icon, origin in origins.items():
                icon.move(origin)
            for icon in files:
                try:
                    shutil.move(str(icon.path), str(self._unique(target.path, icon.path.name)))
                except OSError:
                    pass
            self.rescan()
            return
        if self.state["auto_arrange"]:
            # Re-insert the dragged icons where they were dropped, keeping the column order.
            others = sorted((i for i in self.icons if i not in moved), key=lambda i: self.cell_of(i.pos()))
            drop_cell = self.cell_of(drop)
            idx = sum(1 for i in others if self.cell_of(i.pos()) < drop_cell)
            self._place_in_order(others[:idx] + moved + others[idx:])
        elif self.state["align_grid"]:
            # Snap each dragged icon to the nearest free cell.
            for icon in sorted(moved, key=lambda i: (i.x(), i.y())):
                icon.move(self.cell_pos(*self.free_cell(icon.pos(), ignore=[icon] + [m for m in moved if m is not icon])))
        for icon in moved:
            self.state["positions"][icon.key] = [icon.x(), icon.y()]
        self.stack_below_windows()
        self.save()

    # ---- rubber band (dragging on the empty desktop) ---------------------------------------------------
    def ready(self):
        """Called once the desktop has its real size: build the icons."""
        if not self.icons:
            self.rescan()

    def desktop_pressed(self, event):
        self.desktop.setFocus()
        if self.editor is not None:
            self._finish_rename(True)
        if event.button() != Qt.LeftButton:
            return
        if not event.modifiers() & Qt.ControlModifier:
            self.clear_selection()
        self.band_origin = event.position().toPoint()
        self.band.setGeometry(QRect(self.band_origin, QSize()))
        self.band.show()
        self.band.raise_()

    def desktop_dragged(self, event):
        if self.band_origin is None:
            return
        rect = QRect(self.band_origin, event.position().toPoint()).normalized()
        self.band.setGeometry(rect)
        add = bool(event.modifiers() & Qt.ControlModifier)
        self.select([i for i in self.icons if i.isVisible() and rect.intersects(i.geometry())], add=add)

    def desktop_released(self, event):
        if self.band_origin is not None:
            self.band.hide()
            self.band_origin = None

    # ---- opening and file operations -------------------------------------------------------------------
    def open_icons(self, icons):
        from . import explorer
        from .explorer.viewers import open_file
        for icon in icons:
            if icon.key == "sys:mycomputer":
                explorer.launch(self.desktop)
            elif icon.key == "sys:recycle":
                explorer.launch(self.desktop, explorer.RECYCLE_BIN)
            elif icon.kind == "prog":
                programs.launch(self.desktop, icon.key.split(":", 1)[1])
            elif icon.path is not None:
                if icon.path.is_dir():
                    explorer.launch(self.desktop, icon.path)
                else:
                    open_file(self.desktop, icon.path)

    @staticmethod
    def _unique(folder, name):
        target = Path(folder) / name
        stem, suffix = Path(name).stem, Path(name).suffix
        n = 2
        while target.exists():
            target = Path(folder) / f"{stem} ({n}){suffix}"
            n += 1
        return target

    def new_item(self, kind, at=None):
        folder = self.folder()
        if kind == "folder":
            target = self._unique(folder, "New Folder")
            target.mkdir()
        else:
            target = self._unique(folder, "New Text Document.txt")
            target.write_text("", encoding="utf-8")
        key = f"file:{target.name}"
        if at is not None:
            cell = self.cell_pos(*self.free_cell(at))
            self.state["positions"][key] = [cell.x(), cell.y()]
        self.rescan()
        icon = next((i for i in self.icons if i.key == key), None)
        if icon is not None:
            self.select([icon])
            self.rename(icon)

    def paste(self, at=None):
        from .explorer.window import Explorer
        clip = Explorer.clipboard
        if not clip["paths"]:
            return
        self.copy_in(clip["paths"], move=clip["move"], at=at)
        if clip["move"]:
            Explorer.clipboard = {"paths": [], "move": False}

    def copy_in(self, paths, move=False, at=None):
        folder = self.folder()
        for src in paths:
            src = Path(src)
            if not src.exists() or src.parent.resolve() == folder.resolve():
                continue
            target = self._unique(folder, src.name)
            try:
                if move:
                    shutil.move(str(src), str(target))
                elif src.is_dir():
                    shutil.copytree(src, target)
                else:
                    shutil.copy2(src, target)
            except OSError:
                continue
            if at is not None:
                cell = self.cell_pos(*self.free_cell(at))
                self.state["positions"][f"file:{target.name}"] = [cell.x(), cell.y()]
        self.rescan()

    def copy_selected(self, move=False):
        from .explorer.window import Explorer
        paths = [i.path for i in self.selected() if i.path is not None]
        if paths:
            Explorer.clipboard = {"paths": paths, "move": move}

    def delete(self, icons=None):
        from .explorer import vfs
        from .explorer.dialogs import msgbox
        icons = [i for i in (icons or self.selected()) if i.key not in ("sys:mycomputer", "sys:recycle")]
        if not icons:
            return
        files = [i for i in icons if i.path is not None]
        shortcuts = [i for i in icons if i.kind == "prog"]
        if len(icons) == 1:
            what = icons[0]
            text = (f"Are you sure you want to delete the '{what.label}' shortcut?\n\n(You can show it again from "
                    "Display Properties > Desktop > Customize Desktop.)" if what.kind == "prog"
                    else f"Are you sure you want to send '{what.label}' to the Recycle Bin?")
            title = "Confirm Shortcut Delete" if what.kind == "prog" else "Confirm File Delete"
        else:
            text = f"Are you sure you want to send these {len(icons)} items to the Recycle Bin?"
            title = "Confirm Multiple File Delete"

        def answer(button):
            if button != "Yes":
                return
            for icon in files:
                try:
                    vfs.recycle(icon.path)
                except OSError:
                    pass
            for icon in shortcuts:
                if icon.key not in self.state["hidden"]:
                    self.state["hidden"].append(icon.key)
            sound.play("navigate")
            self.rescan()

        msgbox(self.desktop, title, text, "question", ("Yes", "No"), answer, window_icon=std(QStyle.SP_TrashIcon))

    def set_hidden(self, hidden_keys):
        self.state["hidden"] = list(hidden_keys)
        self.rescan()

    # ---- renaming in place -------------------------------------------------------------------------------
    def rename(self, icon=None):
        icon = icon or (self.selected()[0] if self.selected() else None)
        if icon is None:
            return
        if self.editor is not None:
            self._finish_rename(True)
        edit = QLineEdit(icon.label, self.desktop)
        edit.setAlignment(Qt.AlignCenter)
        edit.setStyleSheet("QLineEdit { background: white; color: black; border: 1px solid black;"
                           " font-family: Tahoma; font-size: 11px; }")
        rect = icon.text_rect().translated(icon.pos())
        edit.setGeometry(rect.x() - 4, rect.y(), rect.width() + 8, 20)
        edit.selectAll()
        if icon.path is not None and icon.path.is_file() and icon.path.suffix:
            edit.setSelection(0, len(icon.path.stem))   # XP selects the name, not the extension
        edit.show()
        edit.raise_()
        edit.setFocus()
        edit.returnPressed.connect(lambda: self._finish_rename(True))
        edit.editingFinished.connect(lambda: self._finish_rename(True))
        self.editor = (edit, icon)

    def _finish_rename(self, keep):
        if self.editor is None:
            return
        edit, icon = self.editor
        self.editor = None
        name = edit.text().strip()
        edit.hide()
        edit.deleteLater()
        if not keep or not name or name == icon.label or not isValid(icon):
            return
        if icon.path is None:
            self.state["labels"][icon.key] = name
            icon.label = name
            icon.update()
            self.save()
            return
        if any(c in name for c in '\\/:*?"<>|'):
            from .explorer.dialogs import msgbox
            msgbox(self.desktop, "Rename", 'A file name cannot contain any of the following characters:\n\\ / : * ? " < > |',
                   "error")
            return
        target = icon.path.with_name(name)
        if target.exists():
            from .explorer.dialogs import msgbox
            msgbox(self.desktop, "Error Renaming File or Folder",
                   f"Cannot rename {icon.label}: A file with the name you specified already exists.", "error")
            return
        try:
            icon.path.rename(target)
        except OSError:
            return
        old_key, new_key = icon.key, f"file:{name}"
        if old_key in self.state["positions"]:
            self.state["positions"][new_key] = self.state["positions"].pop(old_key)
        icon.key = new_key
        self.rescan()

    def cancel_rename(self):
        self._finish_rename(False)

    # ---- context menus ------------------------------------------------------------------------------------
    def icon_menu(self, icon, global_pos):
        from . import display
        from .explorer.dialogs import system_info
        if not icon.selected:
            self.select([icon])
        sel = self.selected()
        menu = QMenu(self.desktop)
        menu.setStyleSheet(MENU_STYLE)
        bold = QFont("Tahoma", 8, QFont.Bold)
        menu.addAction("&Open", lambda: self.open_icons(sel)).setFont(bold)
        if icon.key == "sys:mycomputer":
            menu.addAction("&Explore", lambda: self.open_icons([icon]))
            menu.addSeparator()
            menu.addAction("Rena&me", lambda: self.rename(icon))
            menu.addSeparator()
            menu.addAction("P&roperties", lambda: system_info(self.desktop))
        elif icon.key == "sys:recycle":
            menu.addAction("&Explore", lambda: self.open_icons([icon]))
            menu.addAction("Empty Recycle &Bin", self._empty_recycle_bin)
            menu.addSeparator()
            menu.addAction("Rena&me", lambda: self.rename(icon))
        else:
            if icon.path is not None and icon.path.suffix.lower() in display.IMAGE_EXTS:
                menu.addAction("Set as Desktop &Background", lambda: display.get().set_wallpaper(icon.path))
            menu.addSeparator()
            if icon.path is not None:
                menu.addAction("Cu&t", lambda: self.copy_selected(True))
                menu.addAction("&Copy", lambda: self.copy_selected(False))
                menu.addSeparator()
            menu.addAction("&Delete", lambda: self.delete(sel))
            menu.addAction("Rena&me", lambda: self.rename(icon))
            menu.addSeparator()
            menu.addAction("P&roperties", lambda: self.properties(icon))
        menu.exec(global_pos)

    def desktop_menu(self, global_pos):
        from .controlpanel import display_properties
        from .explorer.window import Explorer
        at = self.desktop.mapFromGlobal(global_pos)
        menu = QMenu(self.desktop)
        menu.setStyleSheet(MENU_STYLE)
        arrange = menu.addMenu("Arrange &Icons By")
        for how in SORTS:
            arrange.addAction(how, lambda h=how: self.arrange_by(h))
        arrange.addSeparator()
        for label, option in (("&Auto Arrange", "auto_arrange"), ("A&lign to Grid", "align_grid"),
                              ("&Show Desktop Icons", "show_icons")):
            act = arrange.addAction(label, lambda o=option: self.toggle(o))
            act.setCheckable(True)
            act.setChecked(bool(self.state[option]))
        arrange.addSeparator()
        arrange.addAction("Run Desktop Cleanup Wizard").setEnabled(False)
        menu.addAction("R&efresh", self.refresh)
        menu.addSeparator()
        paste = menu.addAction("&Paste", lambda: self.paste(at))
        paste.setEnabled(bool(Explorer.clipboard["paths"]))
        menu.addAction("Paste &Shortcut").setEnabled(False)
        menu.addSeparator()
        new = menu.addMenu("Ne&w")
        new.addAction(std(QStyle.SP_DirIcon), "&Folder", lambda: self.new_item("folder", at))
        new.addAction(std(QStyle.SP_FileIcon), "Text Document", lambda: self.new_item("text", at))
        menu.addSeparator()
        menu.addAction("P&roperties", lambda: display_properties(self.desktop))
        menu.exec(global_pos)

    def _empty_recycle_bin(self):
        from .explorer import vfs
        from .explorer.dialogs import msgbox
        n = len(vfs.recycled())
        if not n:
            return

        def answer(button):
            if button == "Yes":
                vfs.empty_recycle_bin()
                sound.play("navigate")

        msgbox(self.desktop, "Confirm Multiple File Delete",
               f"Are you sure you want to delete these {n} items?" if n > 1 else
               "Are you sure you want to delete this item?", "question", ("Yes", "No"), answer,
               window_icon=std(QStyle.SP_TrashIcon))

    def properties(self, icon):
        from .explorer import vfs
        from .explorer.dialogs import date_2001, properties, size_text
        from .explorer.window import xp_type
        if icon.key.split(":", 1)[1] in programs.FOLDER_SHORTCUTS:
            folder = programs.archive_folder(icon.key.split(":", 1)[1])
            target = (vfs.to_virtual(folder) or "") if folder else ""
            properties(self.desktop, icon.label, [("Target type:", "File Folder"), ("Target:", target),
                                                  ("-", ""), ("Start in:", str(Path(target).parent))], icon=icon.icon)
            return
        if icon.path is None:
            target = {"notepad": r"C:\WINDOWS\notepad.exe", "connect": r"C:\Program Files\America Online\isignup.exe",
                      "navigator": r"C:\Program Files\Netscape\Navigator\netscape.exe",
                      "claudeai": r"C:\Program Files\ClaudeAI\claudeai.exe",
                      "aim": r"C:\Program Files\ClaudeAIM\ClaudeAIM.exe",
                      "irc": r"C:\Program Files\ClaudeIRC\ClaudeIRC.exe",
                      "muck": r"C:\Program Files\ClaudeMUCK\ClaudeMUCK.exe",
                      "tv": r"C:\Program Files\ClaudeTV\ClaudeTV.exe",
                      "comix": r"C:\Program Files\FurComix Reader\FurComix.exe",
                      "folio": r"C:\Program Files\FurFolio Reader\FurFolio.exe",
                      "stories": r"C:\Program Files\FurFolio Reader\FurStory.exe",
                      "cdviewer": r"C:\Program Files\Fur CD Viewer\FurCD.exe",
                      "furcon": r"C:\Program Files\Furry Con CD Viewer\FurCon.exe",
                      "furvideo": r"C:\Program Files\Furry Video Browser\FurVideo.exe",
                      "flash": r"C:\Program Files\Macromedia\Flash Player\FlashPla.exe",
                      "claudeamp": r"C:\Program Files\ClaudeAmp\ClaudeAmp.exe",
                      "torrent": r"C:\Program Files\ClaudeTorrent\ClaudeTorrent.exe",
                      "rpg": r"C:\Program Files\ClaudeRPG\ClaudeRPG.exe",
                      "nes": r"C:\Program Files\FCE Ultra\fceu.exe",
                      "snes": r"C:\Program Files\Snes9x\snes9x.exe",
                      "gb": r"C:\Program Files\Gambatte\gambatte.exe",
                      "gbc": r"C:\Program Files\Gambatte\gambatte_gbc.exe",
                      "gba": r"C:\Program Files\mGBA\mgba.exe", "gen": r"C:\Program Files\PicoDrive\picodrive.exe",
                      "sms": r"C:\Program Files\Genesis Plus\gpgx.exe",
                      "gg": r"C:\Program Files\Gearsystem\gearsystem.exe",
                      "apple2": r"C:\Program Files\AppleWin\applewin.exe",
                      "doom": r"C:\Program Files\Doom\doom.exe", "doom2": r"C:\Program Files\Doom II\doom2.exe",
                      "wolf3d": r"C:\Program Files\Wolfenstein 3D\wolf3d.exe",
                      "heretic": r"C:\Program Files\Heretic\heretic.exe", "hexen": r"C:\Program Files\Hexen\hexen.exe"}.get(icon.key.split(":", 1)[1], "")
            properties(self.desktop, icon.label, [("Target type:", "Application"), ("Target:", target),
                                                  ("-", ""), ("Start in:", str(Path(target).parent))], icon=icon.icon)
            return
        st = icon.path.stat()
        if icon.path.is_dir():
            files = [f for f in icon.path.rglob("*") if f.is_file()]
            size = sum(f.stat().st_size for f in files)
            rows = [("Type:", "File Folder"), ("Location:", vfs.to_virtual(icon.path.parent) or ""),
                    ("Size:", f"{size_text(size)} ({size:,} bytes)"), ("Contains:", f"{len(files)} Files"),
                    ("-", ""), ("Created:", date_2001(st.st_ctime))]
        else:
            rows = [("Type of file:", xp_type(icon.path, False)), ("Location:", vfs.to_virtual(icon.path.parent) or ""),
                    ("Size:", f"{size_text(st.st_size)} ({st.st_size:,} bytes)"), ("-", ""),
                    ("Created:", date_2001(st.st_ctime)), ("Modified:", date_2001(st.st_mtime))]
        properties(self.desktop, icon.label, rows, icon=icon.icon)

    # ---- keyboard ---------------------------------------------------------------------------------------------
    def key_pressed(self, event):
        key, mods = event.key(), event.modifiers()
        if self.editor is not None:
            if key == Qt.Key_Escape:
                self.cancel_rename()
            return True
        if key == Qt.Key_Delete:
            self.delete()
        elif key == Qt.Key_F2:
            self.rename()
        elif key == Qt.Key_F5:
            self.refresh()
        elif key in (Qt.Key_Return, Qt.Key_Enter):
            self.open_icons(self.selected())
        elif key == Qt.Key_A and mods & Qt.ControlModifier:
            self.select([i for i in self.icons if i.isVisible()])
        elif key == Qt.Key_C and mods & Qt.ControlModifier:
            self.copy_selected(False)
        elif key == Qt.Key_X and mods & Qt.ControlModifier:
            self.copy_selected(True)
        elif key == Qt.Key_V and mods & Qt.ControlModifier:
            self.paste()
        else:
            return False
        return True

    def drop_files(self, paths, at):
        self.copy_in(paths, move=False, at=at)
