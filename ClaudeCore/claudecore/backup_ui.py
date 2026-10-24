"""The backup panel: what to back up, where, automatic backups, and the list of backups to restore from. The same
panel is the SYSTEC launcher's Backup dialog and each computer's backup program (in its own window style).

    BackupPanel(blocked={"xp"}, in_computer=True)   # parts that can't be restored right now, and why it's asked
"""
import os
import threading
import time
from pathlib import Path

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import (QCheckBox, QFileDialog, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QListWidget,
                               QListWidgetItem, QMessageBox, QProgressBar, QPushButton, QSpinBox, QVBoxLayout, QWidget)

from . import backup as B


class _Signals(QObject):
    progress = Signal(int, int, str)
    done = Signal(str, str)             # result, error


class BackupPanel(QWidget):
    def __init__(self, blocked=(), in_computer=False, parent=None):
        super().__init__(parent)
        self.blocked = set(blocked)
        self.in_computer = in_computer
        self.cfg = B.settings()
        self.busy = False
        self.sig = _Signals()
        self.sig.progress.connect(self._progress)
        self.sig.done.connect(self._done)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(8)

        what = QGroupBox("What to back up")
        wl = QVBoxLayout(what)
        self.boxes = {}
        for key in B.ORDER:
            label, _paths, _default, desc = B.PARTS[key]
            cb = QCheckBox(f"{label}")
            cb.setToolTip(desc)
            cb.setChecked(key in self.cfg["parts"])
            cb.toggled.connect(self._save)
            self.boxes[key] = cb
            wl.addWidget(cb)
        self.sizes = QLabel("")
        self.sizes.setWordWrap(True)
        wl.addWidget(self.sizes)
        lay.addWidget(what)

        where = QGroupBox("Where")
        gl = QVBoxLayout(where)
        row = QHBoxLayout()
        self.path = QLineEdit(str(B.folder()))
        self.path.setReadOnly(True)
        browse = QPushButton("Browse...")
        browse.clicked.connect(self._browse)
        row.addWidget(self.path, 1)
        row.addWidget(browse)
        gl.addLayout(row)
        self.warn = QLabel("")
        self.warn.setWordWrap(True)
        gl.addWidget(self.warn)
        arow = QHBoxLayout()
        self.auto = QCheckBox("Back up automatically when a computer shuts down, keeping the last")
        self.auto.setChecked(bool(self.cfg["auto"]))
        self.auto.toggled.connect(self._save)
        self.keep = QSpinBox()
        self.keep.setRange(1, 50)
        self.keep.setValue(int(self.cfg["keep"]))
        self.keep.valueChanged.connect(self._save)
        arow.addWidget(self.auto)
        arow.addWidget(self.keep)
        arow.addStretch(1)
        gl.addLayout(arow)
        lay.addWidget(where)

        brow = QHBoxLayout()
        self.go = QPushButton("Back up now")
        self.go.clicked.connect(self.backup_now)
        brow.addWidget(self.go)
        self.bar = QProgressBar()
        self.bar.setRange(0, 1000)
        self.bar.setValue(0)
        self.bar.setTextVisible(False)
        brow.addWidget(self.bar, 1)
        lay.addLayout(brow)
        self.status = QLabel("")
        self.status.setWordWrap(True)
        lay.addWidget(self.status)

        restore = QGroupBox("Backups")
        rl = QVBoxLayout(restore)
        self.list = QListWidget()
        self.list.setMinimumHeight(120)
        self.list.currentItemChanged.connect(lambda *_: self._chosen())
        rl.addWidget(self.list, 1)
        self.contents = QLabel("")
        self.contents.setWordWrap(True)
        rl.addWidget(self.contents)
        rrow = QHBoxLayout()
        self.restore_btn = QPushButton("Restore the ticked parts from this backup...")
        self.restore_btn.clicked.connect(self.restore_chosen)
        self.delete_btn = QPushButton("Delete this backup")
        self.delete_btn.clicked.connect(self.delete_chosen)
        rrow.addWidget(self.restore_btn)
        rrow.addStretch(1)
        rrow.addWidget(self.delete_btn)
        rl.addLayout(rrow)
        lay.addWidget(restore, 1)
        if self.blocked:
            note = QLabel("This computer's own data can't be restored while it's running: restore it from the "
                          "SYSTEC launcher, or from another computer." if in_computer else
                          "A computer is running: its data can't be restored until it shuts down.")
            note.setWordWrap(True)
            lay.addWidget(note)
        self._update_warning()
        self._measure()
        self.refresh()

    # ---- settings ------------------------------------------------------------------------------------------------
    def _parts(self):
        return [k for k, cb in self.boxes.items() if cb.isChecked()]

    def _save(self, *_):
        self.cfg.update(parts=self._parts(), auto=self.auto.isChecked(), keep=self.keep.value())
        B.save_settings(self.cfg)
        self._show_sizes()

    def _browse(self):
        chosen = QFileDialog.getExistingDirectory(self, "Where should backups go?", str(B.folder()))
        if chosen:
            self.cfg["folder"] = chosen
            B.save_settings(self.cfg)
            self.path.setText(chosen)
            self._update_warning()
            self.refresh()

    def _update_warning(self):
        if B.same_drive(B.folder()):
            self.warn.setText("These backups are on the same drive as the Timeline. They protect against mistakes, "
                              "not against the drive failing: for that, choose a folder on another drive.")
        else:
            self.warn.setText("On a different drive from the Timeline: safe even if the Timeline's drive fails.")

    def _measure(self):
        self.part_sizes = {}

        def work():
            for k in B.ORDER:
                self.part_sizes[k] = B.size(k)
            self.sig.progress.emit(-1, -1, "")
        threading.Thread(target=work, daemon=True).start()

    def _show_sizes(self):
        if not getattr(self, "part_sizes", None) or len(self.part_sizes) < len(B.ORDER):
            self.sizes.setText("Measuring...")
            return
        total = sum(self.part_sizes[k] for k in self._parts())
        self.sizes.setText(f"Ticked: {B.human(total)} before compression.")
        for k, cb in self.boxes.items():
            cb.setText(f"{B.PARTS[k][0]}  ({B.human(self.part_sizes[k])})")

    # ---- backing up --------------------------------------------------------------------------------------------
    def backup_now(self, auto=False):
        parts = self._parts()
        if not parts or self.busy:
            return
        self.busy = True
        self.go.setEnabled(False)
        self.restore_btn.setEnabled(False)
        self.status.setText("Backing up...")
        self.bar.setValue(0)

        def work():
            try:
                path = B.create(parts, auto=auto, progress=lambda d, t, n: self.sig.progress.emit(d, t, n))
                self.sig.done.emit(f"Backed up to {Path(path).name}.", "")
            except Exception as exc:
                self.sig.done.emit("", str(exc) or exc.__class__.__name__)
        threading.Thread(target=work, daemon=True).start()

    def _progress(self, done, total, name):
        if done < 0:
            self._show_sizes()
            return
        self.bar.setValue(int(1000 * done / max(1, total)))
        self.status.setText(f"{'Restoring' if self.restoring else 'Backing up'}... {name}")

    restoring = False

    def _done(self, result, error):
        self.busy = False
        self.restoring = False
        self.go.setEnabled(True)
        self.restore_btn.setEnabled(True)
        self.bar.setValue(1000 if not error else 0)
        self.status.setText(result if not error else f"That didn't work: {error}")
        self.refresh()

    # ---- the list ------------------------------------------------------------------------------------------------
    def refresh(self):
        self.list.clear()
        for path, m in B.listing():
            kind = "auto" if m.get("auto") else ("before a restore" if m.get("label") == "pre-restore" else "")
            parts = ", ".join(B.PARTS[p][0].split(" (")[0] for p in m.get("parts", []) if p in B.PARTS)
            try:
                size = B.human(path.stat().st_size)
            except OSError:
                size = "?"
            item = QListWidgetItem(f"{m.get('made', '?')}   {size}   {('[' + kind + ']  ') if kind else ''}{parts}")
            item.setData(Qt.UserRole, str(path))
            self.list.addItem(item)
        if not self.list.count():
            self.contents.setText("No backups here yet.")
        self._chosen()

    def _chosen(self):
        item = self.list.currentItem()
        has = item is not None
        self.restore_btn.setEnabled(has and not self.busy)
        self.delete_btn.setEnabled(has and not self.busy)
        if not has:
            return
        m = B.manifest(item.data(Qt.UserRole)) or {}
        self.contents.setText("In this backup: " + ", ".join(B.PARTS[p][0] for p in m.get("parts", []) if p in B.PARTS)
                              + f".  {m.get('files', 0)} files.")

    def restore_chosen(self):
        item = self.list.currentItem()
        if item is None or self.busy:
            return
        path = item.data(Qt.UserRole)
        m = B.manifest(path) or {}
        wanted = [p for p in self._parts() if p in m.get("parts", [])]
        stopped = [p for p in wanted if p in self.blocked]
        wanted = [p for p in wanted if p not in self.blocked]
        if not wanted:
            self.status.setText("Nothing to restore: tick the parts you want back (and this backup must contain them)"
                                + (", and a running computer's data can't be restored." if stopped else "."))
            return
        names = "\n".join("  - " + B.PARTS[p][0] for p in wanted)
        box = QMessageBox(QMessageBox.Warning, "Restore",
                          f"Replace these with the copies from {m.get('made', 'the backup')}?\n\n{names}\n\n"
                          "What's there now is backed up first, so you can undo this from the list."
                          + ("\n\nSkipped (running now): " + ", ".join(B.PARTS[p][0] for p in stopped) if stopped else ""),
                          QMessageBox.Yes | QMessageBox.Cancel, self)
        if box.exec() != QMessageBox.Yes:
            return
        self.busy = True
        self.restoring = True
        self.go.setEnabled(False)
        self.restore_btn.setEnabled(False)
        self.status.setText("Making a safety backup of what's there now...")

        def work():
            try:
                safe = B.restore(path, wanted, progress=lambda d, t, n: self.sig.progress.emit(d, t, n))
                self.sig.done.emit("Restored. The previous copy is saved as " + (Path(safe).name if safe else "-")
                                   + ". Start the computer again to see it.", "")
            except Exception as exc:
                self.sig.done.emit("", str(exc) or exc.__class__.__name__)
        threading.Thread(target=work, daemon=True).start()

    def delete_chosen(self):
        item = self.list.currentItem()
        if item is None or self.busy:
            return
        path = Path(item.data(Qt.UserRole))
        box = QMessageBox(QMessageBox.Question, "Delete backup", f"Delete {path.name}? This can't be undone.",
                          QMessageBox.Yes | QMessageBox.Cancel, self)
        if box.exec() == QMessageBox.Yes:
            try:
                path.unlink()
            except OSError as exc:
                self.status.setText(f"Couldn't delete it: {exc}")
            self.refresh()


# ---- inside a computer: a program of its own ---------------------------------------------------------------------
_open = {}


def backup_icon():
    from PySide6.QtCore import QRectF
    from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
    ic = QIcon()
    for sz in (16, 32, 48):
        pm = QPixmap(sz, sz)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        s = sz / 32
        p.setPen(QPen(QColor("#2A3A5A"), max(1.0, s)))
        p.setBrush(QColor("#5A7AB0"))
        p.drawRoundedRect(QRectF(4 * s, 6 * s, 24 * s, 22 * s), 3 * s, 3 * s)
        p.setBrush(QColor("#E8E8F0"))
        p.drawRect(QRectF(9 * s, 6 * s, 14 * s, 8 * s))
        p.setBrush(QColor("#2A3A5A"))
        p.drawRect(QRectF(18 * s, 7 * s, 3 * s, 6 * s))
        p.setBrush(QColor("#40C060"))
        p.drawEllipse(QRectF(17 * s, 17 * s, 9 * s, 9 * s))
        p.end()
        ic.addPixmap(pm)
    return ic


def launch(desktop):
    from shiboken6 import isValid
    from . import host
    win = _open.get("win")
    if win is not None and isValid(win):
        desktop.open_window(win)
        return win
    era = host.era()
    blocked = {B.ERA_PART.get(era)} - {None}
    body = BackupPanel(blocked=blocked, in_computer=True)
    title = {2001: "Backup Utility", 2011: "Backup and Restore", 2025: "Backup"}.get(era, "Backup")
    win = host.window(desktop, title, body, backup_icon(), (620, 700))
    _open["win"] = win
    desktop.open_window(win)
    return win
