"""Control Panel > AI Models: the language models that play everyone in ClaudeXP, in one place.

  Models       what's installed in E:\\LLM Models\\models (size, pictures, thinking, loaded or not), with Load,
               Unload, Test... and Properties, and a shortcut to the models folder
  Assignments  which model does which job (buddy conversations, background life, ClaudeAI, pictures), plus a
               per-resident model for anyone who talks
  Engine       Vulkan or CUDA, the graphics device, how many models stay loaded, context size, unloading when
               idle, and Start / Stop / Restart / View Log
  Activity     the request queue and recent replies (tokens per second), with a little graph

Settings are saved in data/ai_models.json (see ai_models.py); ClaudeAIM's own model settings follow along."""
import threading
import time

from PySide6.QtCore import QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QGridLayout, QGroupBox, QHBoxLayout, QHeaderView,
                               QLabel, QLineEdit, QPushButton, QRadioButton, QSpinBox, QTabWidget, QTableWidget,
                               QTextEdit, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)
from shiboken6 import isValid

from . import ai_models, llm_server

CONTEXTS = [4096, 8192, 16384, 32768, 65536, 131072]
IDLE = [(0, "Never"), (5, "After 5 minutes"), (15, "After 15 minutes"), (30, "After 30 minutes"),
        (60, "After 1 hour")]
TAB_STYLE = ("QTabWidget::pane { background: #FCFCFE; border: 1px solid #919B9C; }"
             "QTabBar::tab { background: #F0EFE6; border: 1px solid #919B9C; padding: 3px 8px;"
             " font-family: Tahoma; font-size: 11px; }"
             "QTabBar::tab:selected { background: #FCFCFE; border-bottom-color: #FCFCFE; }")


def ai_icon(size=32):
    """A chip with 'AI' on it."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 32
    p.setPen(QPen(QColor("#8A8A8A"), max(1.0, 1.4 * s)))
    for i in range(4):                                            # the pins
        o = (8 + i * 5.3) * s
        p.drawLine(int(o), int(2 * s), int(o), int(6 * s))
        p.drawLine(int(o), int(26 * s), int(o), int(30 * s))
        p.drawLine(int(2 * s), int(o), int(6 * s), int(o))
        p.drawLine(int(26 * s), int(o), int(30 * s), int(o))
    g = QLinearGradient(0, 6 * s, 0, 26 * s)
    g.setColorAt(0, QColor("#4A7FE0"))
    g.setColorAt(1, QColor("#1A3E9A"))
    p.setPen(QPen(QColor("#0F2A70"), max(1.0, s)))
    p.setBrush(g)
    p.drawRoundedRect(QRectF(5.5 * s, 5.5 * s, 21 * s, 21 * s), 3 * s, 3 * s)
    f = QFont("Arial Black")
    f.setPixelSize(max(6, int(10 * s)))
    p.setFont(f)
    p.setPen(QColor("white"))
    p.drawText(QRectF(5 * s, 5 * s, 22 * s, 22 * s), Qt.AlignCenter, "AI")
    p.end()
    return pm


def _size(n):
    return f"{n / 2**30:.1f} GB" if n >= 2**30 else f"{n / 2**20:.0f} MB"


def _model_combo(current, allow_default=False):
    box = QComboBox()
    if allow_default:
        box.addItem("(the usual model)", "")
    for m in ai_models.installed():
        box.addItem(f"{m.title}  ({_size(m.size)}{', sees pictures' if m.vision else ''})", m.id)
    i = box.findData(current)
    box.setCurrentIndex(max(0, i))
    return box


# ---- Activity: a little graph of recent speed -----------------------------------------------------------------

class SpeedGraph(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(90)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        p.fillRect(r, QColor("black"))
        p.setPen(QPen(QColor("#0A4A0A"), 1))
        for i in range(1, 4):
            y = r.top() + r.height() * i / 4
            p.drawLine(int(r.left()), int(y), int(r.right()), int(y))
        acts = [a for a in ai_models.activity() if a["tps"] > 0][-40:]
        if not acts:
            p.setPen(QColor("#3A8A3A"))
            p.setFont(QFont("Tahoma", 8))
            p.drawText(r, Qt.AlignCenter, "No replies yet")
            return
        top = max(20.0, max(a["tps"] for a in acts) * 1.15)
        w = r.width() / 40
        for i, a in enumerate(acts):
            h = (r.height() - 4) * a["tps"] / top
            p.fillRect(QRectF(r.left() + i * w + 1, r.bottom() - h, w - 2, h), QColor("#30E030"))
        p.setPen(QColor("#9AE09A"))
        p.setFont(QFont("Tahoma", 7))
        p.drawText(r.adjusted(4, 2, -4, -2), Qt.AlignTop | Qt.AlignLeft, f"tokens/s (top {top:.0f})")


# ---- the window ---------------------------------------------------------------------------------------------------

class AIModels(QWidget):
    found_devices = Signal(list)

    def __init__(self, desktop, close):
        super().__init__()
        self.desktop = desktop
        self.close_window = close
        self.cfg = ai_models.config()
        v = QVBoxLayout(self)
        v.setContentsMargins(8, 8, 8, 8)
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(TAB_STYLE)
        self.tabs.addTab(self._models_tab(), "Models")
        self.tabs.addTab(self._assign_tab(), "Assignments")
        self.tabs.addTab(self._engine_tab(), "Engine")
        self.tabs.addTab(self._activity_tab(), "Activity")
        v.addWidget(self.tabs)
        row = QHBoxLayout()
        row.addStretch()
        ok, cancel, self.apply_btn = QPushButton("OK"), QPushButton("Cancel"), QPushButton("&Apply")
        for b in (ok, cancel, self.apply_btn):
            b.setFixedSize(75, 23)
            row.addWidget(b)
        v.addLayout(row)
        ok.clicked.connect(lambda: (self.apply(), close()))
        cancel.clicked.connect(close)
        self.apply_btn.clicked.connect(self.apply)
        self.apply_btn.setEnabled(False)
        self.setFixedWidth(500)
        self.timer = QTimer(self, interval=1500, timeout=self.refresh)
        self.timer.start()
        self.found_devices.connect(self._show_devices)
        threading.Thread(target=lambda: self.found_devices.emit(llm_server.devices()), daemon=True).start()
        self.refresh()

    def changed(self, *_):
        self.apply_btn.setEnabled(True)

    # ---- Models ----------------------------------------------------------------------------------------------
    def _models_tab(self):
        page = QWidget()
        v = QVBoxLayout(page)
        intro = QLabel("These language models are installed in E:\\LLM Models\\models. A model loads the first "
                       "time something asks for it.")
        intro.setWordWrap(True)
        v.addWidget(intro)
        self.models = QTreeWidget()
        self.models.setHeaderLabels(["Model", "Size", "Pictures", "Status"])
        self.models.setRootIsDecorated(False)
        self.models.header().setSectionResizeMode(0, QHeaderView.Stretch)
        for col, w in ((1, 60), (2, 56), (3, 74)):
            self.models.setColumnWidth(col, w)
        self.models.setFixedHeight(200)
        v.addWidget(self.models)
        row = QHBoxLayout()
        self.load_btn, self.unload_btn = QPushButton("&Load"), QPushButton("&Unload")
        test, props, folder = QPushButton("&Test..."), QPushButton("P&roperties"), QPushButton("Open Models &Folder")
        for b in (self.load_btn, self.unload_btn, test, props):
            row.addWidget(b)
        row.addStretch()
        v.addLayout(row)
        v.addWidget(folder, 0, Qt.AlignLeft)
        self.note = QLabel()
        self.note.setWordWrap(True)
        v.addWidget(self.note)
        v.addStretch()
        self.load_btn.clicked.connect(lambda: self._load(True))
        self.unload_btn.clicked.connect(lambda: self._load(False))
        test.clicked.connect(self.test)
        props.clicked.connect(self.properties)
        folder.clicked.connect(self._open_folder)
        self.models.itemDoubleClicked.connect(lambda *_: self.properties())
        self._fill_models()
        return page

    def _fill_models(self):
        self.models.clear()
        for m in ai_models.installed():
            item = QTreeWidgetItem([m.title, _size(m.size), "Yes" if m.vision else "No", ""])
            item.setData(0, Qt.UserRole, m.id)
            item.setIcon(0, QIcon(ai_icon(16)))
            self.models.addTopLevelItem(item)
        if self.models.topLevelItemCount():
            self.models.setCurrentItem(self.models.topLevelItem(0))

    def _selected(self):
        item = self.models.currentItem()
        return item.data(0, Qt.UserRole) if item else None

    def _load(self, on):
        mid = self._selected()
        if not mid:
            return
        if on:
            threading.Thread(target=lambda: llm_server._quiet(lambda: llm_server.load(mid)), daemon=True).start()
        else:
            llm_server.unload(mid)
        QTimer.singleShot(500, self.refresh)

    def _open_folder(self):
        from . import explorer
        root = ai_models.models_root()
        root.mkdir(parents=True, exist_ok=True)
        explorer.launch(self.desktop, root)

    def properties(self):
        m = ai_models.get(self._selected() or "")
        if m is None:
            return
        from .explorer.dialogs import msgbox
        info = m.info
        lines = [m.title, "", f"Folder:  {m.id}", f"File:  {m.path.name}  ({_size(m.size)})",
                 f"Sees pictures:  {'yes (' + m.mmproj.name + ')' if m.vision else 'no'}",
                 f"Thinks before answering:  {'yes' if m.thinking else 'no'}"]
        for key, label in (("source", "Source"), ("licence", "Licence"), ("notes", "Notes")):
            if info.get(key):
                lines.append(f"{label}:  {info[key]}")
        msgbox(self.desktop, f"{m.title} Properties", "\n".join(lines), "info")

    def test(self):
        """Ask the selected model something, right here."""
        mid = self._selected()
        if not mid:
            return
        from .network import DialogBody, _fixed_window
        body = DialogBody()
        v = QVBoxLayout(body)
        v.setContentsMargins(10, 10, 10, 10)
        v.addWidget(QLabel(f"Ask {ai_models.get(mid).title} something:"))
        prompt = QLineEdit("Say hello and tell me one fun fact about huskies.")
        v.addWidget(prompt)
        out = QTextEdit()
        out.setReadOnly(True)
        out.setFixedHeight(150)
        v.addWidget(out)
        row = QHBoxLayout()
        row.addStretch()
        send, close = QPushButton("&Send"), QPushButton("Close")
        for b in (send, close):
            b.setFixedSize(75, 23)
            row.addWidget(b)
        v.addLayout(row)
        body.setFixedWidth(420)
        holder = {}

        def done(text, err, t0):
            if isValid(out):
                out.setPlainText((f"(Error: {err})" if err else text) + f"\n\n[{time.time() - t0:.1f} s]")
                send.setEnabled(True)

        def go():
            from . import broker
            send.setEnabled(False)
            out.setPlainText("Thinking... (the model may need a few seconds to load)")
            t0 = time.time()
            broker.get().chat(mid, [{"role": "user", "content": prompt.text()}],
                              {"num_ctx": int(self.cfg["context"]), "temperature": 0.8},
                              lambda text, err: done(text, err, t0), broker.FOREGROUND, think=False)

        def shut():
            w = holder.pop("win", None)
            if w is not None and isValid(w):
                self.desktop.close_window(w)
        send.clicked.connect(go)
        prompt.returnPressed.connect(go)
        close.clicked.connect(shut)
        holder["win"] = _fixed_window(self.desktop, "Test Model", body, shut)
        holder["win"].icon = QIcon(ai_icon(16))
        self.desktop.open_window(holder["win"])

    # ---- Assignments ---------------------------------------------------------------------------------------------
    def _assign_tab(self):
        page = QWidget()
        v = QVBoxLayout(page)
        jobs = QGroupBox("Which model does which job")
        g = QGridLayout(jobs)
        self.role_boxes = {}
        for row, (role, label, blurb) in enumerate(ai_models.ROLES):
            text = QLabel(f"<b>{label}</b><br><span style='color:#606060'>{blurb}</span>")
            text.setWordWrap(True)
            g.addWidget(text, row, 0)
            box = _model_combo(ai_models.model_for(role))
            box.setFixedWidth(190)
            box.currentIndexChanged.connect(self.changed)
            g.addWidget(box, row, 1)
            self.role_boxes[role] = box
        v.addWidget(jobs)
        people = QGroupBox("A model of their own (buddies and regulars who talk to you)")
        pv = QVBoxLayout(people)
        self.overrides = QTableWidget(0, 2)
        self.overrides.setHorizontalHeaderLabels(["Resident", "Model"])
        self.overrides.verticalHeader().hide()
        self.overrides.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.overrides.setColumnWidth(0, 130)
        self.overrides.setSelectionMode(QAbstractItemView.NoSelection)
        self.overrides.setFixedHeight(160)
        try:
            from .programs.furdir import residents
            talkers = [r for r in residents() if r.tier in ("main", "support")]
        except Exception:
            talkers = []
        for r in talkers:
            row = self.overrides.rowCount()
            self.overrides.insertRow(row)
            cell = QLabel(f" {r.name}")
            cell.setProperty("resident", r.name)
            self.overrides.setCellWidget(row, 0, cell)
            box = _model_combo(self.cfg["overrides"].get(r.name, ""), allow_default=True)
            box.currentIndexChanged.connect(self.changed)
            self.overrides.setCellWidget(row, 1, box)
        pv.addWidget(self.overrides)
        v.addWidget(people)
        v.addStretch()
        return page

    # ---- Engine ---------------------------------------------------------------------------------------------------
    def _engine_tab(self):
        page = QWidget()
        v = QVBoxLayout(page)
        eng = QGroupBox("Engine")
        ev = QVBoxLayout(eng)
        have = llm_server.engines()
        current = llm_server.find_engine()
        current = current.parent.name if current else ""
        self.engine_buttons = {}
        for key, label in (("vulkan", "Vulkan - any graphics card (fastest on a GTX 1080 Ti)"),
                           ("cuda", "CUDA - NVIDIA graphics cards only")):
            b = QRadioButton(label + ("" if key in have else "   (not installed)"))
            b.setEnabled(key in have)
            b.setChecked(key == current)
            b.toggled.connect(self.changed)
            ev.addWidget(b)
            self.engine_buttons[key] = b
        self.devices = QLabel("Graphics device: looking...")
        self.devices.setWordWrap(True)
        ev.addWidget(self.devices)
        v.addWidget(eng)
        mem = QGroupBox("Memory")
        g = QGridLayout(mem)
        g.addWidget(QLabel("Models kept loaded at once:"), 0, 0)
        self.max_loaded = QSpinBox()
        self.max_loaded.setRange(1, 4)
        self.max_loaded.setValue(int(self.cfg["max_loaded"]))
        self.max_loaded.valueChanged.connect(self.changed)
        g.addWidget(self.max_loaded, 0, 1)
        g.addWidget(QLabel("Context (how much each model remembers):"), 1, 0)
        self.context = QComboBox()
        for n in CONTEXTS:
            self.context.addItem(f"{n // 1024}K tokens", n)
        self.context.setCurrentIndex(max(0, self.context.findData(int(self.cfg["context"]))))
        self.context.currentIndexChanged.connect(self.changed)
        g.addWidget(self.context, 1, 1)
        g.addWidget(QLabel("Unload models when idle:"), 2, 0)
        self.idle = QComboBox()
        for minutes, label in IDLE:
            self.idle.addItem(label, minutes)
        self.idle.setCurrentIndex(max(0, self.idle.findData(int(self.cfg["idle_minutes"]))))
        self.idle.currentIndexChanged.connect(self.changed)
        g.addWidget(self.idle, 2, 1)
        from PySide6.QtWidgets import QCheckBox
        self.compact = QCheckBox("Lighter context cache (8-bit) - lets a big model and a small one share the card")
        self.compact.setChecked(bool(self.cfg.get("compact_cache", True)))
        self.compact.toggled.connect(self.changed)
        g.addWidget(self.compact, 3, 0, 1, 2)
        v.addWidget(mem)
        st = QGroupBox("Status")
        sv = QVBoxLayout(st)
        self.engine_status = QLabel()
        self.engine_status.setWordWrap(True)
        sv.addWidget(self.engine_status)
        row = QHBoxLayout()
        start, stop, restart, log = (QPushButton("&Start"), QPushButton("Sto&p"), QPushButton("&Restart"),
                                     QPushButton("View &Log"))
        for b in (start, stop, restart, log):
            row.addWidget(b)
        row.addStretch()
        sv.addLayout(row)
        v.addWidget(st)
        v.addStretch()
        start.clicked.connect(lambda: self._background(llm_server.ensure_started))
        stop.clicked.connect(lambda: (llm_server.stop(), self.refresh()))
        restart.clicked.connect(lambda: self._background(llm_server.restart))
        log.clicked.connect(self._log)
        return page

    def _show_devices(self, devices):
        if isValid(self.devices):
            self.devices.setText("Graphics device: " + ("; ".join(devices) if devices else "none found (the CPU "
                                                                                             "will be used)"))

    def _background(self, fn):
        threading.Thread(target=lambda: llm_server._quiet(fn), daemon=True).start()
        QTimer.singleShot(800, self.refresh)

    def _log(self):
        from .paths import DATA
        from .programs.notepad import open_notepad
        log = DATA / "llama-server.log"
        if log.exists():
            open_notepad(self.desktop, log)

    # ---- Activity ----------------------------------------------------------------------------------------------
    def _activity_tab(self):
        page = QWidget()
        v = QVBoxLayout(page)
        self.queue = QLabel()
        v.addWidget(self.queue)
        self.graph = SpeedGraph()
        v.addWidget(self.graph)
        v.addWidget(QLabel("Recent replies:"))
        self.recent = QTreeWidget()
        self.recent.setHeaderLabels(["Time", "Model", "Tokens", "Tokens/s", "Took"])
        self.recent.setRootIsDecorated(False)
        self.recent.header().setSectionResizeMode(1, QHeaderView.Stretch)
        for col, w in ((0, 64), (2, 52), (3, 62), (4, 50)):
            self.recent.setColumnWidth(col, w)
        v.addWidget(self.recent, 1)
        return page

    # ---- keeping it current ---------------------------------------------------------------------------------
    def refresh(self):
        if not isValid(self):
            return
        states = llm_server.model_states()
        for i in range(self.models.topLevelItemCount()):
            item = self.models.topLevelItem(i)
            state = states.get(item.data(0, Qt.UserRole), "")
            item.setText(3, {"loaded": "Loaded", "loading": "Loading..."}.get(state, "Not loaded"))
        missing = llm_server.status()
        self.note.setText(f"<span style='color:#A02020'>{missing}</span>" if missing else
                          "To add a model, put its folder (its .gguf, plus an mmproj-*.gguf if it can see pictures) "
                          "in the models folder, then reopen AI Models.")
        loaded = [k for k, val in states.items() if val == "loaded"]
        if llm_server.running():
            self.engine_status.setText(f"Running ({llm_server.find_engine().parent.name}). Loaded: "
                                       f"{', '.join(loaded) if loaded else 'nothing yet'}.")
        else:
            self.engine_status.setText(missing or "Not running. It starts by itself when something needs a model.")
        try:
            from . import broker
            b = broker.get()
            waiting = max(0, len(b.jobs) - (1 if b.running else 0))
            self.queue.setText(f"Working on a request: {'yes' if b.running else 'no'}    Waiting: {waiting}")
        except Exception:
            self.queue.setText("")
        acts = ai_models.activity()[-30:]
        if self.recent.topLevelItemCount() != len(acts):
            self.recent.clear()
            for a in reversed(acts):
                self.recent.addTopLevelItem(QTreeWidgetItem([
                    time.strftime("%H:%M:%S", time.localtime(a["when"])), a["model"], str(a["tokens"]),
                    f"{a['tps']:.0f}" if a["tps"] else "", f"{a['seconds']:.1f}s"]))
        self.graph.update()

    def apply(self):
        cfg = ai_models.config()
        before = (cfg.get("engine"), cfg.get("max_loaded"), cfg.get("context"), cfg.get("idle_minutes"),
                  cfg.get("compact_cache", True))
        cfg["assign"] = {role: box.currentData() for role, box in self.role_boxes.items() if box.currentData()}
        overrides = {}
        for row in range(self.overrides.rowCount()):
            name = self.overrides.cellWidget(row, 0).property("resident")
            chosen = self.overrides.cellWidget(row, 1).currentData()
            if chosen:
                overrides[name] = chosen
        cfg["overrides"] = overrides
        cfg["engine"] = next((k for k, b in self.engine_buttons.items() if b.isChecked()), cfg.get("engine", ""))
        cfg["max_loaded"] = self.max_loaded.value()
        cfg["context"] = self.context.currentData()
        cfg["idle_minutes"] = self.idle.currentData()
        cfg["compact_cache"] = self.compact.isChecked()
        ai_models.save(cfg)
        self.cfg = cfg
        if before != (cfg["engine"], cfg["max_loaded"], cfg["context"], cfg["idle_minutes"],
                       cfg["compact_cache"]) and llm_server.running():
            self._background(llm_server.restart)                # the router picks the new settings up
        self.apply_btn.setEnabled(False)

    def closeEvent(self, event):
        self.timer.stop()
        event.accept()


_open = {}


def ai_models_properties(desktop):
    win = _open.get("win")
    if win is not None and isValid(win):
        desktop.open_window(win)
        return win
    from .network import DialogBody, _fixed_window
    body = DialogBody()
    lay = QVBoxLayout(body)
    lay.setContentsMargins(0, 0, 0, 0)
    holder = {}

    def close():
        w = holder.pop("win", None)
        if w is not None and isValid(w):
            w.content.findChild(AIModels).timer.stop()
            desktop.close_window(w)
    lay.addWidget(AIModels(desktop, close))
    win = _fixed_window(desktop, "AI Models", body, close)
    win.icon = QIcon(ai_icon(16))
    holder["win"] = win
    _open["win"] = win
    desktop.open_window(win)
    return win
