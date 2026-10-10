"""The Checkpoints window: save, compare and roll back the whole project."""
import difflib
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMessageBox, QPlainTextEdit,
                               QPushButton, QSplitter, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

from . import checkpoints as cp

STATUS = {"changed": ("changed", "#B58900"), "deleted": ("deleted since", "#C00000"), "new": ("new since", "#1B7F1B")}


def unified(old, new, name):
    lines = difflib.unified_diff(old.splitlines(), new.splitlines(), f"checkpoint: {name}", "now", lineterm="", n=2)
    return "\n".join(lines) or "(no differences)"


class CheckpointWindow(QWidget):
    """`studio` supplies root(), save_all(), checkpoint_now(name), files_restored(paths), status(text)."""

    def __init__(self, studio):
        super().__init__()
        self.studio = studio
        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        self.where = QLabel("")
        self.where.setStyleSheet("QLabel { color: #606060; }")
        root.addWidget(self.where)
        split = QSplitter(Qt.Horizontal)
        left = QWidget()
        lbox = QVBoxLayout(left)
        lbox.setContentsMargins(0, 0, 0, 0)
        self.list = QListWidget()
        self.list.currentRowChanged.connect(self._select)
        self.save_button = QPushButton("Save checkpoint...")
        self.save_button.clicked.connect(self.save_new)
        lbox.addWidget(self.list, 1)
        lbox.addWidget(self.save_button)
        split.addWidget(left)
        right = QSplitter(Qt.Vertical)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["File", "Compared with now"])
        self.tree.setRootIsDecorated(False)
        self.tree.setColumnWidth(0, 230)
        self.tree.setSelectionMode(QTreeWidget.ExtendedSelection)
        self.tree.itemSelectionChanged.connect(self._show_diff)
        self.diff = QPlainTextEdit()
        self.diff.setReadOnly(True)
        self.diff.setProperty("nospell", True)
        self.diff.setLineWrapMode(QPlainTextEdit.NoWrap)
        right.addWidget(self.tree)
        right.addWidget(self.diff)
        right.setSizes([160, 230])
        split.addWidget(right)
        split.setSizes([230, 470])
        root.addWidget(split, 1)
        self.note = QLabel("")
        self.note.setWordWrap(True)
        root.addWidget(self.note)
        row = QHBoxLayout()
        self.restore_all = QPushButton("Restore whole project")
        self.restore_all.clicked.connect(lambda: self.restore(False))
        self.restore_some = QPushButton("Restore selected files")
        self.restore_some.clicked.connect(lambda: self.restore(True))
        self.remove = QPushButton("Delete checkpoint")
        self.remove.clicked.connect(self.delete_current)
        row.addWidget(self.restore_all)
        row.addWidget(self.restore_some)
        row.addStretch()
        row.addWidget(self.remove)
        root.addLayout(row)
        self.items = []
        self.refresh()

    def root_dir(self):
        return Path(self.studio.root())

    def refresh(self, select=None):
        self.items = cp.listing(self.root_dir())
        self.where.setText(f"Project folder: {self.root_dir()}")
        self.list.blockSignals(True)
        self.list.clear()
        for c in self.items:
            item = QListWidgetItem(f"{c['name']}\n{c['when']}  -  {len(c['files'])} files" + ("  (automatic)" if c["auto"] else ""))
            item.setData(Qt.UserRole, c["id"])
            self.list.addItem(item)
        self.list.blockSignals(False)
        row = next((i for i, c in enumerate(self.items) if c["id"] == select), 0 if self.items else -1)
        self.list.setCurrentRow(row)
        self._select(row)

    def current(self):
        row = self.list.currentRow()
        return self.items[row] if 0 <= row < len(self.items) else None

    def _select(self, _row=None):
        c = self.current()
        self.tree.clear()
        self.diff.clear()
        have = c is not None
        for b in (self.restore_all, self.restore_some, self.remove):
            b.setEnabled(have)
        if not have:
            self.note.setText("No checkpoints yet. Save one before trying something risky, like a big AI change.")
            return
        diffs = cp.changes(self.root_dir(), c["id"])
        for rel, status in diffs:
            label, color = STATUS[status]
            item = QTreeWidgetItem([rel, label])
            item.setForeground(1, QBrush(QColor(color)))
            item.setData(0, Qt.UserRole, status)
            self.tree.addTopLevelItem(item)
        self.note.setText("The project is identical to this checkpoint." if not diffs else
                          f"{len(diffs)} file(s) differ. Select a file to see what changed.")
        if diffs:
            self.tree.setCurrentItem(self.tree.topLevelItem(0))

    def _show_diff(self):
        c = self.current()
        sel = self.tree.selectedItems()
        if c is None or not sel:
            return
        rel = sel[0].text(0)
        status = sel[0].data(0, Qt.UserRole)
        old = cp.saved_text(self.root_dir(), c["id"], rel)
        new = cp._read(self.root_dir() / rel)
        if status == "new":
            self.diff.setPlainText("This file was created after the checkpoint (restoring the whole project removes it).")
            return
        self.diff.setPlainText(unified(old, new, c["name"]))

    def save_new(self):
        made = self.studio.save_checkpoint()
        if made:
            self.refresh(select=made["id"])

    def restore(self, selected_only):
        c = self.current()
        if c is None:
            return
        only = None
        if selected_only:
            only = {i.text(0) for i in self.tree.selectedItems() if i.data(0, Qt.UserRole) != "new"}
            if not only:
                self.note.setText("Select one or more changed or deleted files first.")
                return
        diffs = cp.changes(self.root_dir(), c["id"])
        extra = [rel for rel, st in diffs if st == "new"] if only is None else []
        if not diffs and only is None:
            self.note.setText("Nothing to restore: the project already matches this checkpoint.")
            return
        message = (f"Roll {'the selected files' if only else 'the whole project'} back to \"{c['name']}\"?\n\n"
                   f"Your current state is saved as an automatic checkpoint first, so you can undo this.")
        if extra:
            message += f"\n\nFiles created after the checkpoint will be removed: {', '.join(extra[:6])}" + (" ..." if len(extra) > 6 else "")
        if QMessageBox.question(self, "Restore checkpoint", message) != QMessageBox.Yes:
            return
        done = self.studio.restore_checkpoint(c["id"], only, remove_new=only is None)
        self.refresh(select=c["id"])
        self.note.setText(f"Restored {len(done)} file(s).")

    def delete_current(self):
        c = self.current()
        if c is not None and QMessageBox.question(self, "Delete checkpoint", f"Delete \"{c['name']}\"?") == QMessageBox.Yes:
            cp.delete(self.root_dir(), c["id"])
            self.refresh()
