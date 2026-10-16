"""The Setup tab of Control Panel > AI Models: the AI Model Setup Assistant.

It shows what ClaudeXP needs (llm_setup.MANIFEST), what's installed, and downloads and installs the rest. When the
essentials are missing it starts downloading them by itself after a short countdown. If a download fails it offers to
retry, to use files you already have (a file, or a whole folder to search), or to download from another address.
Any other .gguf can be added from a web address too.
"""
import os

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (QFileDialog, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QProgressBar, QPushButton,
                               QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)
from shiboken6 import isValid

from . import llm_setup as ls

COUNTDOWN = 10
_installer = {}


def installer(desktop):
    """One downloader for the whole session: it keeps going if the AI Models window is closed, and when it finishes
    the models are picked up straight away."""
    if "i" not in _installer:
        inst = ls.Installer()
        from . import llm_server
        inst.all_done.connect(lambda: llm_server.recheck(desktop))
        _installer["i"] = inst
    return _installer["i"]


class SetupTab(QWidget):
    def __init__(self, desktop, on_installed=None, auto=False):
        super().__init__()
        self.desktop = desktop
        self.on_installed = on_installed
        self.inst = installer(desktop)
        self.pending = []                      # (key, files) still to bring in from a searched folder
        self.inst.status.connect(self._status)
        self.inst.progress.connect(self._progress)
        self.inst.item_done.connect(self._item_done)
        self.inst.all_done.connect(self._all_done)
        self.failed = []
        v = QVBoxLayout(self)
        v.setContentsMargins(8, 8, 8, 8)
        self.banner = QLabel()
        self.banner.setWordWrap(True)
        self.banner.setStyleSheet("QLabel { font-family: Tahoma; font-size: 11px; padding: 6px; border: 1px solid "
                                  "#99B4E5; background: #EEF3FD; }")
        v.addWidget(self.banner)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Model", "Size", "Status"])
        self.tree.setRootIsDecorated(True)
        self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tree.setStyleSheet("QTreeWidget { background: white; font-family: Tahoma; font-size: 11px; }")
        self.tree.setMinimumHeight(190)
        self.tree.itemChanged.connect(lambda *_: self._totals())
        v.addWidget(self.tree, 1)
        self.totals = QLabel()
        v.addWidget(self.totals)
        self.bar = QProgressBar()
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(14)
        v.addWidget(self.bar)
        self.line = QLabel(" ")
        self.line.setStyleSheet("font-family: Tahoma; font-size: 11px; color: #333;")
        v.addWidget(self.line)
        row = QHBoxLayout()
        self.go = QPushButton("Download and Install")
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        row.addWidget(self.go)
        row.addWidget(self.stop_btn)
        row.addStretch()
        v.addLayout(row)
        row2 = QHBoxLayout()
        self.have = QPushButton("Use Files I Have...")
        self.folder = QPushButton("Search a Folder...")
        self.address = QPushButton("Other Address...")
        self.custom = QPushButton("Add From Web Address...")
        for b in (self.have, self.folder, self.address, self.custom):
            row2.addWidget(b)
        v.addLayout(row2)
        for b in (self.go, self.stop_btn, self.have, self.folder, self.address, self.custom):
            b.setStyleSheet("font-family: Tahoma; font-size: 11px;")
        self.go.clicked.connect(self.start)
        self.stop_btn.clicked.connect(self.stop)
        self.have.clicked.connect(lambda: self.use_files())
        self.folder.clicked.connect(self.search_folder)
        self.address.clicked.connect(lambda: self.other_address())
        self.custom.clicked.connect(self.add_custom)
        self.countdown = None
        self.fill()
        if auto and ls.essentials_missing():
            self._start_countdown()

    # ---- the list ------------------------------------------------------------------------------------------
    def fill(self):
        self.tree.blockSignals(True)
        self.tree.clear()
        self.rows = {}
        for gkey, gname, gdesc in ls.GROUPS:
            top = QTreeWidgetItem([gname, "", gdesc])
            f = top.font(0)
            f.setBold(True)
            top.setFont(0, f)
            self.tree.addTopLevelItem(top)
            for it in [i for i in ls.MANIFEST if i["group"] == gkey]:
                done = ls.installed(it)
                row = QTreeWidgetItem([it["title"], ls.fmt(ls.size(it)), self._state_text(it)])
                row.setToolTip(0, it["what"])
                row.setFlags(row.flags() | Qt.ItemIsUserCheckable)
                row.setCheckState(0, Qt.Unchecked if done else (Qt.Checked if gkey == "essential" else
                                                                Qt.Unchecked))
                if done:
                    row.setFlags(row.flags() & ~Qt.ItemIsEnabled)
                row.setData(0, Qt.UserRole, it["key"])
                top.addChild(row)
                self.rows[it["key"]] = row
            top.setExpanded(True)
        self.tree.blockSignals(False)
        self._banner()
        self._totals()

    def _state_text(self, it):
        if ls.installed(it):
            return "Installed"
        got = ls.partial(it)
        if got:
            return f"Partly downloaded ({got * 100 // max(1, ls.size(it))}%)"
        return "Missing"

    def _banner(self, text=None):
        if text:
            self.banner.setText(text)
            return
        missing = ls.essentials_missing()
        if missing:
            self.banner.setText("<b>ClaudeXP's language models are missing.</b> Without them your buddies, IRC, the "
                                "MUCK, the made-up Web and the AI helpers can't talk. Tick what you want and click "
                                "<b>Download and Install</b> - or use files you've already downloaded.")
        else:
            self.banner.setText("<b>Everything ClaudeXP needs is installed.</b> You can add the recommended and "
                                "optional models here too.")

    def selected(self):
        return [k for k, row in self.rows.items()
                if row.checkState(0) == Qt.Checked and row.flags() & Qt.ItemIsEnabled]

    def _totals(self):
        keys = self.selected()
        need = sum(ls.size(ls.item(k)) - ls.partial(ls.item(k)) for k in keys)
        free = ls.free_space()
        warn = "  <font color='#C02010'><b>Not enough free space!</b></font>" if need > free else ""
        self.totals.setText(f"Selected: {len(keys)} item(s), {ls.fmt(need)} to download.   Free space on drive E: "
                            f"{ls.fmt(free)}{warn}")
        self.go.setEnabled(bool(keys) and not self.inst.busy())

    # ---- downloading ---------------------------------------------------------------------------------------
    def _start_countdown(self):
        left = {"n": COUNTDOWN}
        need = sum(ls.size(i) - ls.partial(i) for i in ls.essentials_missing())
        self.countdown = QTimer(self)

        def tick():
            if left["n"] <= 0:
                self.countdown.stop()
                self.countdown = None
                self.start()
                return
            self._banner(f"<b>ClaudeXP's language models are missing.</b> Downloading the essentials ({ls.fmt(need)}) "
                         f"starts in <b>{left['n']}</b> seconds. Click <b>Stop</b> to choose something else, such as "
                         "files you already have.")
            left["n"] -= 1
        self.countdown.timeout.connect(tick)
        tick()
        self.countdown.start(1000)
        self.stop_btn.setEnabled(True)

    def start(self, keys=None, urls=None):
        if self.countdown is not None:
            self.countdown.stop()
            self.countdown = None
        keys = keys or self.selected()
        if not keys:
            return
        need = sum(ls.size(ls.item(k)) - ls.partial(ls.item(k)) for k in keys)
        if need > ls.free_space():
            self._msg(f"There isn't enough free space on E: ({ls.fmt(ls.free_space())} free, {ls.fmt(need)} needed). "
                      "Free some space, or untick some models.", "warning")
            return
        self.failed = []
        self._busy(True)
        self._banner("Downloading... You can keep using ClaudeXP; this window can stay open in the background.")
        self.inst.download(keys, urls)

    def stop(self):
        if self.countdown is not None:
            self.countdown.stop()
            self.countdown = None
            self._banner()
            self.stop_btn.setEnabled(False)
            return
        self.inst.stop()
        self.line.setText("Stopping... (what's downloaded so far is kept, and resumes next time)")

    def _busy(self, on):
        self.go.setEnabled(not on)
        self.stop_btn.setEnabled(on)
        for b in (self.have, self.folder, self.address, self.custom):
            b.setEnabled(not on)

    def _status(self, key, text):
        if isValid(self):
            self.line.setText(text)
            row = self.rows.get(key)
            if row is not None:
                row.setText(2, "Working...")

    def _progress(self, key, done, total):
        if isValid(self) and total:
            self.bar.setValue(int(done * 100 / total))

    def _item_done(self, key, ok, error):
        if not isValid(self):
            return
        row = self.rows.get(key)
        if row is not None:
            it = ls.item(key)
            row.setText(2, "Installed" if ok else f"Failed - {self._state_text(it)}")
            if ok:
                row.setCheckState(0, Qt.Unchecked)
                row.setFlags(row.flags() & ~Qt.ItemIsEnabled)
        if not ok and error != "Cancelled.":
            self.failed.append((key, error))

    def _all_done(self):
        if not isValid(self):
            return
        if self.pending:
            k, files = self.pending.pop(0)
            QTimer.singleShot(0, lambda: self.inst.use_files(k, files))
            return
        self._busy(False)
        self.bar.setValue(0)
        from . import llm_server
        if self.on_installed:
            self.on_installed()
        self.fill()
        if self.failed:
            key, error = self.failed[0]
            self.line.setText(f"{ls.item(key)['title'] if not key.startswith('custom:') else key}: {error}")
            self._offer_options(key, error)
        elif not ls.essentials_missing():
            self.line.setText("Done. Your buddies can talk.")

    def _offer_options(self, key, error):
        if key.startswith("custom:"):
            self._msg(f"The download didn't work:\n\n{error}", "warning")
            return
        from .explorer.dialogs import msgbox
        title = ls.item(key)["title"]

        def answer(b):
            if b == "Try Again":
                self.start([key])
            elif b == "Use My Files":
                self.use_files(key)
            elif b == "Other Address":
                self.other_address(key)
        msgbox(self.desktop, "AI Model Setup", f"{title} couldn't be downloaded:\n\n{error}\n\nYou can try again, "
               "point ClaudeXP at a copy you've already downloaded, or give another web address to download it from.",
               "warning", ("Try Again", "Use My Files", "Other Address", "Cancel"), answer)

    # ---- the other ways in ------------------------------------------------------------------------------------
    def _which(self, key=None):
        if key:
            return key
        current = self.tree.currentItem()
        k = current.data(0, Qt.UserRole) if current is not None else None
        if k:
            return k
        sel = self.selected()
        return sel[0] if sel else None

    def use_files(self, key=None):
        key = self._which(key)
        if key is None:
            self._msg("Click a model in the list first.", "info")
            return
        it = ls.item(key)
        chosen = {}
        for f in it["files"]:
            if ls.target(it, f).is_file() and ls.target(it, f).stat().st_size == f["size"]:
                continue
            kind = "Zip files (*.zip)" if f["name"].endswith(".zip") else "Model files (*.gguf)"
            path, _ = QFileDialog.getOpenFileName(self, f"Find {f['name']} ({ls.fmt(f['size'])})", os.path.expanduser(
                "~"), f"{kind};;All files (*.*)")
            if not path:
                return
            chosen[f["name"]] = path
        if not chosen:
            return
        self._busy(True)
        self.failed = []
        self.inst.use_files(key, chosen)

    def search_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Find models you've already downloaded", os.path.expanduser("~"))
        if not path:
            return
        self.line.setText("Looking for model files...")
        found = self.inst.find_in_folder(path)
        if not found:
            self._msg("None of ClaudeXP's model files were found in that folder (they're matched by name and size).",
                      "info")
            self.line.setText(" ")
            return
        names = ", ".join(ls.item(k)["title"] for k in found)
        self.line.setText(f"Found: {names}")
        self._busy(True)
        self.failed = []
        self.pending = [(k, found[k]) for k in found][1:]
        first = next(iter(found))
        self.inst.use_files(first, found[first])

    def other_address(self, key=None):
        key = self._which(key)
        if key is None:
            self._msg("Click a model in the list first.", "info")
            return
        it = ls.item(key)
        from .network import DialogBody, _fixed_window
        body = DialogBody()
        v = QVBoxLayout(body)
        v.setContentsMargins(14, 12, 14, 12)
        v.addWidget(QLabel(f"<b>Download {it['title']} from another address</b><br>Paste a web address for each file "
                           "(a mirror, or a direct link). The file is still checked before it's installed."))
        edits = {}
        for f in it["files"]:
            v.addWidget(QLabel(f"{f['name']} ({ls.fmt(f['size'])}):"))
            e = QLineEdit(f["url"])
            e.setMinimumWidth(460)
            v.addWidget(e)
            edits[f["name"]] = e
        row = QHBoxLayout()
        row.addStretch()
        ok, cancel = QPushButton("Download"), QPushButton("Cancel")
        for b in (ok, cancel):
            b.setFixedSize(80, 23)
            row.addWidget(b)
        v.addLayout(row)
        holder = {}

        def close():
            if holder.get("win") is not None and isValid(holder["win"]):
                self.desktop.close_window(holder.pop("win"))

        def go():
            urls = {n: e.text().strip() for n, e in edits.items() if e.text().strip()}
            close()
            self.start([key], urls)
        ok.clicked.connect(go)
        cancel.clicked.connect(close)
        holder["win"] = _fixed_window(self.desktop, "Other Address", body, close)
        self.desktop.open_window(holder["win"])

    def add_custom(self):
        from .network import DialogBody, _fixed_window
        body = DialogBody()
        v = QVBoxLayout(body)
        v.setContentsMargins(14, 12, 14, 12)
        v.addWidget(QLabel("<b>Add a model from a web address</b><br>The address of any .gguf file (for example a "
                           "'resolve' link from Hugging Face). It's saved as a new model you can assign in AI Models."))
        e = QLineEdit()
        e.setMinimumWidth(460)
        e.setPlaceholderText("https://huggingface.co/.../resolve/main/model-Q4_K_M.gguf")
        v.addWidget(e)
        row = QHBoxLayout()
        row.addStretch()
        ok, cancel = QPushButton("Download"), QPushButton("Cancel")
        for b in (ok, cancel):
            b.setFixedSize(80, 23)
            row.addWidget(b)
        v.addLayout(row)
        holder = {}

        def close():
            if holder.get("win") is not None and isValid(holder["win"]):
                self.desktop.close_window(holder.pop("win"))

        def go():
            url = e.text().strip()
            if not url.lower().startswith(("http://", "https://")):
                return
            close()
            self._busy(True)
            self.failed = []
            self.inst.custom(url)
        ok.clicked.connect(go)
        cancel.clicked.connect(close)
        holder["win"] = _fixed_window(self.desktop, "Add From Web Address", body, close)
        self.desktop.open_window(holder["win"])

    def _msg(self, text, icon="info"):
        from .explorer.dialogs import msgbox
        msgbox(self.desktop, "AI Model Setup", text, icon)

    def shutdown(self):
        """The window is closing: a countdown is called off; a download carries on in the background."""
        if self.countdown is not None:
            self.countdown.stop()
            self.countdown = None
