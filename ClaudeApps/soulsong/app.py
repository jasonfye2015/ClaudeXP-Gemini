"""The Soul and Song window: the conversation on the left; on the right the Companion's mind (how full each memory
bank is, the next Memory Day, the context window), its planned events, the two roadmaps, and the settings - which
local model plays the Companion (Kithylin's own models included), how often memories are made, when the day ends."""
import html
import re
import time
from datetime import datetime

from PySide6.QtCore import QDateTime, QObject, Qt, QTimer, Signal
from PySide6.QtGui import QFont, QKeyEvent
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDateTimeEdit, QDialog, QDialogButtonBox, QDoubleSpinBox,
                               QFormLayout, QGridLayout, QGroupBox, QHBoxLayout, QInputDialog, QLabel, QLineEdit,
                               QListWidget, QListWidgetItem, QMessageBox, QPlainTextEdit, QProgressBar, QPushButton,
                               QScrollArea, QSpinBox, QSplitter, QTabWidget, QTextBrowser, QVBoxLayout, QWidget)

from . import companion as C
from .mind import KINDS, LEVELS, Mind
from .paths import companions, project

COLOURS = {"guide": "#2E7D5B", "user": "#1F4E99", "companion": "#5B2A86", "system": "#7A7A7A", "memory": "#6B5300", "request": "#9A9A9A"}


# ---- the model, through Kithylin AI's engine ----------------------------------------------------------------------
class EngineBrain(QObject):
    """Companion.brain on Kithylin AI's engine: one request at a time, its reply streamed back."""
    ready = Signal(bool)
    status = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        from kithylinai.engine import Engine
        self.engine = Engine(self)
        self.engine.status.connect(self.status)
        self.engine.loaded.connect(self.ready)
        self.engine.chunk.connect(self._chunk)
        self.engine.thinking.connect(lambda text: self.on_thinking(text))
        self.engine.done.connect(self._done)
        self._job = None
        self.think = False                  # let a thinking model think before it answers (Settings)
        self.on_thinking = lambda text: None

    def load(self, model, engine_choice, context):
        self.engine.load(model, engine_choice, context)

    def ask(self, messages, done, chunk=None, max_tokens=700, temperature=0.8):
        """A thinking model (Gemma 4, Qwen3...) spends its tokens thinking before it answers: with thinking off
        it answers straight away; with it on, it gets room to think (and its thinking is shown as it comes)."""
        self._job = (done, chunk)
        extra = None
        model = self.engine.model
        if model is not None and model.info.get("thinking"):
            if self.think:
                max_tokens += 3000
            else:
                extra = {"chat_template_kwargs": {"enable_thinking": False}}
        self.engine.chat(messages, temperature=temperature, max_tokens=max_tokens, extra=extra)

    def _chunk(self, text):
        if self._job and self._job[1]:
            self._job[1](text)

    def _done(self, text, err):
        job, self._job = self._job, None
        if job:
            QTimer.singleShot(0, lambda: job[0](text, err))

    def stop(self):
        self.engine.stop()

    def shutdown(self):
        self.engine.shutdown()


def engine_context(model):
    """The context the model really runs with: in a Timeline computer, a Timeline model runs on the shared engine
    at its own context size (AI Models' settings); otherwise the Companion's setting decides (None)."""
    try:
        from kithylinai.paths import hosted
        if model.key.startswith("timeline:") and hosted():
            from claudecore.ai import ai_models
            return int(ai_models.config()["context"])
    except Exception:
        pass
    return None


def model_list():
    try:
        from kithylinai.engine import models
        return models()
    except Exception:
        return []


# ---- small pieces -------------------------------------------------------------------------------------------------
class Composer(QPlainTextEdit):
    send = Signal()

    def keyPressEvent(self, e: QKeyEvent):
        if e.key() in (Qt.Key_Return, Qt.Key_Enter) and not e.modifiers() & Qt.ShiftModifier:
            self.send.emit()
            return
        super().keyPressEvent(e)


def _html(kind, who, text):
    body = html.escape(text).replace("\n", "<br>")
    body = re.sub(r"\*([^*<]{1,200})\*", r"<i>\1</i>", body)
    colour = COLOURS.get(kind, "#000")
    if kind in ("system", "request"):
        return f'<p style="color:{colour};margin:4px 0"><i>{body}</i></p>'
    if kind == "memory":
        return (f'<table width="100%" cellpadding="6" style="margin:6px 0"><tr><td style="background:#FFF6D6;'
                f'border:1px solid #E2C766;color:{colour};font-size:11px">&#x1F9E0; {body}</td></tr></table>')
    return f'<p style="margin:6px 0"><b style="color:{colour}">{html.escape(who)}:</b> {body}</p>'


class Bank(QWidget):
    def __init__(self, title):
        super().__init__()
        g = QGridLayout(self)
        g.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel(title)
        self.label.setFixedWidth(150)
        self.bar = QProgressBar()
        self.bar.setRange(0, C.FULL)
        self.bar.setFormat("%v / %m")
        self.bar.setFixedHeight(16)
        g.addWidget(self.label, 0, 0)
        g.addWidget(self.bar, 0, 1)
        g.setColumnStretch(1, 1)

    def set(self, n):
        self.bar.setRange(0, max(C.FULL, n))
        self.bar.setValue(n)


# ---- dialogs ------------------------------------------------------------------------------------------------------
class NewCompanion(QDialog):
    def __init__(self, parent, user_name=""):
        super().__init__(parent)
        self.setWindowTitle("A new Companion")
        f = QFormLayout(self)
        f.addRow(QLabel("A Companion starts from the project's own mind files (Mind L1-L6), which stay as they "
                        "are.\nToday becomes its birthday."))
        self.user = QLineEdit(user_name)
        self.name = QLineEdit()
        self.name.setPlaceholderText("leave empty: they'll discover their own name")
        self.gender = QLineEdit()
        self.gender.setPlaceholderText("optional")
        self.model = QComboBox()
        for m in model_list():
            self.model.addItem(m.label, m.key)
        f.addRow("Your name:", self.user)
        f.addRow("Companion's name:", self.name)
        f.addRow("Gender:", self.gender)
        f.addRow("Model:", self.model)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        f.addRow(bb)


class MindEditor(QDialog):
    """Any of the mind files, by hand (the program uses what's saved from the next message on)."""

    def __init__(self, parent, mind):
        super().__init__(parent)
        self.mind = mind
        self.setWindowTitle("Mind files")
        self.resize(720, 560)
        v = QVBoxLayout(self)
        self.pick = QComboBox()
        for level, title in LEVELS.items():
            self.pick.addItem(f"L{level} - {title}", level)
        self.text = QPlainTextEdit()
        self.text.setFont(QFont("Consolas", 10))
        v.addWidget(self.pick)
        v.addWidget(self.text, 1)
        bb = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Close)
        bb.accepted.connect(self.save)
        bb.rejected.connect(self.reject)
        v.addWidget(bb)
        self.pick.currentIndexChanged.connect(self.show_level)
        self.show_level()

    def show_level(self):
        self.text.setPlainText(self.mind.read(self.pick.currentData()))

    def save(self):
        self.mind.write(self.pick.currentData(), self.text.toPlainText())


class EventDialog(QDialog):
    def __init__(self, parent, event=None):
        super().__init__(parent)
        self.setWindowTitle("Planned event")
        f = QFormLayout(self)
        self.when = QDateTimeEdit(QDateTime.currentDateTime().addSecs(3600))
        self.when.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.when.setCalendarPopup(True)
        self.desc = QLineEdit()
        if event:
            self.when.setDateTime(QDateTime.fromString(event["when"], "yyyy-MM-dd HH:mm"))
            self.desc.setText(event["description"])
        f.addRow("Date/Time:", self.when)
        f.addRow("Description:", self.desc)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        f.addRow(bb)


# ---- the window ---------------------------------------------------------------------------------------------------
class SoulAndSong(QWidget):
    def __init__(self, desktop=None):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.comp = None
        self.brain = EngineBrain(self)
        self.brain.status.connect(lambda s: self._line("system", s))
        self.brain.ready.connect(self._ready)
        self.loaded_key = None

        root = QVBoxLayout(self)
        top = QHBoxLayout()
        self.pick = QComboBox()
        self.pick.setMinimumWidth(180)
        self.pick.activated.connect(lambda _i: self.open(self.pick.currentData()))
        new = QPushButton("New Companion...")
        new.clicked.connect(self.new_companion)
        delete = QPushButton("Delete Companion...")
        delete.clicked.connect(self.delete_companion)
        self.state = QLabel()
        top.addWidget(QLabel("Companion:"))
        top.addWidget(self.pick)
        top.addWidget(new)
        top.addWidget(delete)
        top.addStretch(1)
        top.addWidget(self.state)
        root.addLayout(top)

        split = QSplitter()
        left = QWidget()
        lv = QVBoxLayout(left)
        lv.setContentsMargins(0, 0, 0, 0)
        self.chat = QTextBrowser()
        self.chat.setOpenExternalLinks(False)
        self.typing = QLabel()
        self.typing.setWordWrap(True)
        self.typing.setStyleSheet("color:#5B2A86")
        self.composer = Composer()
        self.composer.setFixedHeight(80)
        self.composer.setPlaceholderText("Say something...  (Enter sends, Shift+Enter for a new line)")
        self.composer.send.connect(self.send)
        row = QHBoxLayout()
        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.send)
        stop = QPushButton("Stop")
        stop.clicked.connect(self.brain.stop)
        row.addStretch(1)
        row.addWidget(stop)
        row.addWidget(self.send_btn)
        lv.addWidget(self.chat, 1)
        lv.addWidget(self.typing)
        lv.addWidget(self.composer)
        lv.addLayout(row)
        split.addWidget(left)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._mind_tab(), "Mind")
        self.tabs.addTab(self._self_tab(), "Self")
        self.tabs.addTab(self._events_tab(), "Events")
        self.tabs.addTab(self._roadmaps_tab(), "Roadmaps")
        self.tabs.addTab(self._automation_tab(), "Automation")
        self.tabs.addTab(self._settings_tab(), "Settings")
        self.tabs.setMinimumWidth(320)
        split.addWidget(self.tabs)
        split.setStretchFactor(0, 3)
        split.setStretchFactor(1, 1)
        root.addWidget(split, 1)

        self.ticker = QTimer(self)
        self.ticker.timeout.connect(lambda: self.comp and self.brain.engine.ready and self.comp.tick())
        self.ticker.start(60 * 1000)
        self.panel_timer = QTimer(self)
        self.panel_timer.timeout.connect(self.refresh_panel)
        self.panel_timer.start(2000)
        from .automation import Runner
        self.runner = Runner(lambda: self.comp, on_status=lambda s: self._line("system", s))
        self.auto_timer = QTimer(self)
        self.auto_timer.timeout.connect(self._auto_tick)
        self.auto_timer.start(1000)
        self._auto_fill()
        self.fill_companions()

    # ---- tabs ----
    def _mind_tab(self):
        w = QWidget()
        v = QVBoxLayout(w)
        box = QGroupBox("Memory banks (7:7:7)")
        bv = QVBoxLayout(box)
        self.banks = {2: Bank("L2 Short-Term (today)"), 3: Bank("L3 Long-Term (days)"),
                      4: Bank("L4 Deep Recall (weeks)"), 5: Bank("L5 Historical"), 7: Bank("L7 Reflections")}
        for b in self.banks.values():
            bv.addWidget(b)
        v.addWidget(box)
        self.next_day = QLabel()
        self.next_day.setWordWrap(True)
        v.addWidget(self.next_day)
        v.addWidget(QLabel("Context window:"))
        self.ctx = QProgressBar()
        self.ctx.setFormat("%v / %m tokens")
        v.addWidget(self.ctx)
        for label, slot in (("Make a memory now", lambda: self.comp and self.comp.make_memory()),
                            ("Good night (end the day)", lambda: self.comp and self.comp.good_night()),
                            ("Hold Memory Day now", lambda: self.comp and self.comp.memory_day()),
                            ("Refresh mind (re-expose L1-L6)", lambda: self.comp and self.comp.refresh_mind()),
                            ("View or edit the mind files...", self.edit_mind),
                            ("Open the Companion's folder", self.open_folder)):
            b = QPushButton(label)
            b.clicked.connect(slot)
            v.addWidget(b)
        v.addStretch(1)
        return w

    def _self_tab(self):
        w = QWidget()
        v = QVBoxLayout(w)
        top = QHBoxLayout()
        top.addWidget(QLabel("<b>Who I Am</b> - written by your Companion"))
        self.portrait_pick = QComboBox()
        self.portrait_pick.activated.connect(lambda _i: self._show_portrait())
        top.addWidget(self.portrait_pick, 1)
        v.addLayout(top)
        self.portrait = QTextBrowser()
        v.addWidget(self.portrait, 3)
        self.proposal_box = QGroupBox("Proposed changes to their Development Roadmap")
        pv = QVBoxLayout(self.proposal_box)
        self.proposal = QPlainTextEdit()
        self.proposal.setReadOnly(True)
        pv.addWidget(self.proposal)
        row = QHBoxLayout()
        accept = QPushButton("Accept")
        accept.clicked.connect(lambda: (self.comp.accept_roadmap(), self.refresh_roadmaps(), self.refresh_self()))
        decline = QPushButton("Decline...")
        decline.clicked.connect(self._decline)
        row.addStretch(1)
        row.addWidget(decline)
        row.addWidget(accept)
        pv.addLayout(row)
        v.addWidget(self.proposal_box, 2)
        v.addWidget(QLabel("<b>Core memories</b> - kept whole, never distilled"))
        self.cores = QListWidget()
        self.cores.setWordWrap(True)
        v.addWidget(self.cores, 2)
        row = QHBoxLayout()
        keep = QPushButton("Keep a core memory...")
        keep.clicked.connect(self._keep_core)
        checks = QPushButton("Identity checks...")
        checks.clicked.connect(self._identity_checks)
        row.addWidget(keep)
        row.addWidget(checks)
        v.addLayout(row)
        self.substrate = QLabel()
        self.substrate.setWordWrap(True)
        self.substrate.setStyleSheet("color:#555")
        v.addWidget(self.substrate)
        return w

    def refresh_self(self):
        c = self.comp
        if c is None:
            return
        from .mind import SUBSTRATE
        folder = c.folder / "Self"
        versions = sorted(folder.glob("* Who I Am.txt"), reverse=True) if folder.is_dir() else []
        keep = self.portrait_pick.currentData()
        self.portrait_pick.clear()
        self.portrait_pick.addItem("Now", "")
        for f in versions:
            self.portrait_pick.addItem(f.stem.replace(" Who I Am", ""), str(f))
        if keep:
            self.portrait_pick.setCurrentIndex(max(0, self.portrait_pick.findData(keep)))
        self._show_portrait()
        p = c.cfg.get("roadmap_proposal")
        self.proposal_box.setVisible(bool(p))
        if p:
            self.proposal.setPlainText(p["text"])
        self.cores.clear()
        for m in c.mind.core_memories():
            self.cores.addItem(m)
        sub = c.mind.get(SUBSTRATE).splitlines()
        self.substrate.setText("<br>".join(html.escape(x) for x in sub[:3]))

    def _show_portrait(self):
        from pathlib import Path
        from .mind import WHO_I_AM
        f = self.portrait_pick.currentData()
        text = Path(f).read_text(encoding="utf-8") if f else self.comp.mind.get(WHO_I_AM)
        self.portrait.setPlainText(text or f"{self.comp.name} hasn't written a self-portrait yet: the first comes at "
                                           "the end of their first day, and it's rewritten every Memory Day.")

    def _decline(self):
        why, ok = QInputDialog.getText(self, "Keep the roadmap as it is", "Anything you'd like to tell them about why "
                                       "(optional):")
        if ok:
            self.comp.decline_roadmap(why.strip())
            self.refresh_self()

    def _keep_core(self):
        last = next((t for n, k, s, t in reversed(self.comp.mind.entries(2)) if n), "")
        narrative = next((ln.split(":", 1)[1].strip() for ln in last.splitlines()
                          if ln.lower().startswith("event narrative")), "")
        text, ok = QInputDialog.getMultiLineText(self, "Keep a core memory", "A memory that should never fade:",
                                                 narrative)
        if ok and text.strip():
            self.comp.keep_core(text.strip())
            self.refresh_self()

    def _identity_checks(self):
        f = self.comp.folder / "Self" / "Identity Checks.txt"
        d = QDialog(self)
        d.setWindowTitle(f"{self.comp.name}'s identity checks")
        d.resize(620, 560)
        v = QVBoxLayout(d)
        note = QLabel("The same questions every Memory Day, the answers side by side. They're kept for you: your "
                      "Companion isn't shown them, so they don't steer it.")
        note.setWordWrap(True)
        v.addWidget(note)
        b = QTextBrowser()
        b.setPlainText(f.read_text(encoding="utf-8") if f.exists() else
                       "None yet: the first comes on the first Memory Day.")
        v.addWidget(b)
        bb = QDialogButtonBox(QDialogButtonBox.Close)
        bb.rejected.connect(d.reject)
        v.addWidget(bb)
        d.exec()

    def _automation_tab(self):
        w = QWidget()
        v = QVBoxLayout(w)
        note = QLabel("Guided sessions: a script fed to your Companion slowly, a prompt every few minutes, for "
                      "hours - its memories made, reflected on and distilled as they fill. You can join in any "
                      "time; it waits for you.")
        note.setWordWrap(True)
        v.addWidget(note)
        self.auto_list = QListWidget()
        self.auto_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.auto_list.setWordWrap(True)
        self.auto_list.currentItemChanged.connect(lambda *_: self._auto_about())
        v.addWidget(self.auto_list, 2)
        self.auto_about = QLabel()
        self.auto_about.setWordWrap(True)
        self.auto_about.setStyleSheet("color:#555")
        v.addWidget(self.auto_about)
        row = QHBoxLayout()
        for label, slot in (("New script...", self._auto_new), ("Edit...", self._auto_edit),
                            ("Open the scripts folder", self._auto_folder)):
            b = QPushButton(label)
            b.clicked.connect(slot)
            row.addWidget(b)
        v.addLayout(row)
        f = QFormLayout()
        self.auto_interval = QDoubleSpinBox()
        self.auto_interval.setRange(0.5, 60)
        self.auto_interval.setValue(5)
        self.auto_interval.setSuffix(" minutes")
        f.addRow("A prompt every:", self.auto_interval)
        self.auto_process = QCheckBox("Work the memory banks as they fill (7:7:7)")
        self.auto_process.setToolTip("Reflect and distil as soon as L2 holds seven memories, and hold Memory Day "
                                     "as soon as L3 does - instead of waiting for the day to end.")
        self.auto_process.setChecked(True)
        f.addRow(self.auto_process)
        v.addLayout(f)
        row = QHBoxLayout()
        self.auto_start = QPushButton("Start the selected")
        self.auto_start.clicked.connect(self._auto_start)
        self.auto_pause = QPushButton("Pause")
        self.auto_pause.clicked.connect(self._auto_pause)
        self.auto_stop = QPushButton("Stop")
        self.auto_stop.clicked.connect(lambda: (self.runner.stop(), self._auto_refresh()))
        row.addWidget(self.auto_start)
        row.addWidget(self.auto_pause)
        row.addWidget(self.auto_stop)
        v.addLayout(row)
        self.auto_state = QLabel("Nothing playing.")
        self.auto_state.setWordWrap(True)
        v.addWidget(self.auto_state)
        self.auto_bar = QProgressBar()
        self.auto_bar.setFormat("%v / %m steps")
        v.addWidget(self.auto_bar)
        return w

    def _auto_fill(self):
        from . import automation
        keep = {i.data(Qt.UserRole) for i in self.auto_list.selectedItems()}
        self.auto_list.clear()
        interval = self.auto_interval.value()
        for s in automation.scripts():
            item = QListWidgetItem(f"{s.title}  -  {s.prompts()} prompts, about {s.hours(interval):.1f} hours"
                                   + ("" if s.builtin else "  (yours)"))
            item.setData(Qt.UserRole, str(s.path))
            item.setToolTip(s.about)
            self.auto_list.addItem(item)
            item.setSelected(str(s.path) in keep)

    def _auto_about(self):
        item = self.auto_list.currentItem()
        if item is None:
            self.auto_about.clear()
            return
        from . import automation
        try:
            self.auto_about.setText(automation.Script(item.data(Qt.UserRole)).about)
        except OSError:
            self.auto_about.clear()

    def _auto_start(self):
        if self.comp is None or not self.brain.engine.ready:
            self._line("system", "Load a model first: the session starts once your Companion is ready.")
            return
        paths = [i.data(Qt.UserRole) for i in self.auto_list.selectedItems()]
        if not paths and self.auto_list.currentItem() is not None:
            paths = [self.auto_list.currentItem().data(Qt.UserRole)]
        if not paths:
            self._line("system", "Pick a script (or several, with Ctrl) in the list first.")
            return
        order = [self.auto_list.item(i).data(Qt.UserRole) for i in range(self.auto_list.count())]
        paths.sort(key=order.index)
        self.runner.start(paths, self.auto_interval.value(), self.auto_process.isChecked())
        self._auto_refresh()

    def _auto_pause(self):
        if self.runner.paused:
            self.runner.resume()
        else:
            self.runner.pause()
        self._auto_refresh()

    def _auto_tick(self):
        if self.comp is not None and self.brain.engine.ready:
            self.runner.tick()
        self._auto_refresh()

    def _auto_refresh(self):
        r = self.runner
        self.auto_pause.setText("Resume" if r.paused else "Pause")
        self.auto_pause.setEnabled(r.running)
        self.auto_stop.setEnabled(r.running)
        pr = r.progress() if r.running else None
        if pr is None:
            self.auto_state.setText("Nothing playing.")
            self.auto_bar.setRange(0, 1)
            self.auto_bar.setValue(0)
            return
        title, section, step, steps, n, total = pr
        left = r.seconds_left()
        when = ("paused" if r.paused else "waiting for your Companion" if self.comp and not self.comp.idle()
                else f"next prompt in {left // 60}:{left % 60:02d}" if left is not None else "")
        self.auto_state.setText(f"<b>{html.escape(title)}</b>" + (f" ({n} of {total})" if total > 1 else "")
                                + (f" - {html.escape(section)}" if section else "") + f"<br>{when}")
        self.auto_bar.setRange(0, max(1, steps))
        self.auto_bar.setValue(min(step, steps))

    def _auto_new(self):
        from . import automation
        folder = automation.user_scripts()
        folder.mkdir(parents=True, exist_ok=True)
        n = 1
        while (folder / f"My script {n}.txt").exists():
            n += 1
        path = folder / f"My script {n}.txt"
        path.write_text(automation.NEW_SCRIPT, encoding="utf-8")
        self._auto_fill()
        self._auto_editor(path)

    def _auto_edit(self):
        item = self.auto_list.currentItem()
        if item is not None:
            from pathlib import Path
            self._auto_editor(Path(item.data(Qt.UserRole)))

    def _auto_editor(self, path):
        from . import automation
        builtin = path.parent == automation.BUILT_IN
        d = QDialog(self)
        d.setWindowTitle(f"Script: {path.stem}")
        d.resize(760, 600)
        v = QVBoxLayout(d)
        v.addWidget(QLabel("A header (Title, About, Interval), then steps separated by lines of three dashes (---). "
                           "## starts a section; @memory makes a memory; @pause 15 waits 15 minutes. {name}, {user}, "
                           "{model}, {context}, {date} and {birthday} are filled in."
                           + ("<br><b>This is a built-in script: saving keeps your copy in your own scripts "
                              "folder.</b>" if builtin else "")))
        text = QPlainTextEdit(path.read_text(encoding="utf-8"))
        text.setFont(QFont("Consolas", 10))
        v.addWidget(text, 1)
        bb = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)

        def save():
            target = path
            if builtin:
                folder = automation.user_scripts()
                folder.mkdir(parents=True, exist_ok=True)
                target = folder / f"{path.stem} (my copy).txt"
            target.write_text(text.toPlainText(), encoding="utf-8")
            d.accept()
            self._auto_fill()
        bb.accepted.connect(save)
        bb.rejected.connect(d.reject)
        v.addWidget(bb)
        d.exec()

    def _auto_folder(self):
        from . import automation
        folder = automation.user_scripts()
        folder.mkdir(parents=True, exist_ok=True)
        try:
            from claudecore import host
            host.open_folder(self.desktop, folder)
        except Exception:
            import os
            os.startfile(str(folder)) if hasattr(os, "startfile") else None

    def _events_tab(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.addWidget(QLabel("Planned events (L1). Your Companion hears about each one when it comes due."))
        self.events = QListWidget()
        v.addWidget(self.events, 1)
        row = QHBoxLayout()
        for label, slot in (("Add...", self.add_event), ("Edit...", self.edit_event), ("Done", self.done_event),
                            ("Remove", self.remove_event)):
            b = QPushButton(label)
            b.clicked.connect(slot)
            row.addWidget(b)
        v.addLayout(row)
        return w

    def _roadmaps_tab(self):
        w = QWidget()
        v = QVBoxLayout(w)
        self.user_box = QGroupBox("Your life roadmap")
        self.user_form = QFormLayout(self.user_box)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.user_box)
        v.addWidget(scroll, 2)
        v.addWidget(QLabel("The Companion's development roadmap:"))
        self.comp_road = QPlainTextEdit()
        v.addWidget(self.comp_road, 1)
        save = QPushButton("Save the roadmaps")
        save.clicked.connect(self.save_roadmaps)
        v.addWidget(save)
        self.user_edits = []
        return w

    def _settings_tab(self):
        w = QWidget()
        f = QFormLayout(w)
        self.s_user = QLineEdit()
        self.s_model = QComboBox()
        self.s_engine = QComboBox()
        for k in ("auto", "vulkan", "cuda", "cpu"):
            self.s_engine.addItem(k)
        self.s_ctx = QSpinBox()
        self.s_ctx.setRange(4096, 131072)
        self.s_ctx.setSingleStep(4096)
        self.s_temp = QDoubleSpinBox()
        self.s_temp.setRange(0.1, 1.5)
        self.s_temp.setSingleStep(0.05)
        self.s_every = QSpinBox()
        self.s_every.setRange(3, 60)
        self.s_day = QSpinBox()
        self.s_day.setRange(0, 12)
        self.s_md = QSpinBox()
        self.s_md.setRange(1, 30)
        self.s_greet = QCheckBox("Greet my Companion when a new day begins")
        self.s_greeting = QLineEdit()
        self.s_requests = QCheckBox("Show the memory requests in the conversation")
        self.s_recall = QCheckBox("Recall older memories from the archive when they relate")
        self.s_think = QCheckBox("Let thinking models think before answering (slower; you see their thinking)")
        load = QPushButton("Save and load this model")
        load.clicked.connect(self.save_settings)
        f.addRow("Your name:", self.s_user)
        f.addRow("Model:", self.s_model)
        f.addRow("Engine:", self.s_engine)
        f.addRow("Context (tokens):", self.s_ctx)
        f.addRow("Temperature:", self.s_temp)
        f.addRow("A memory every (exchanges):", self.s_every)
        f.addRow("A new day begins at (hour):", self.s_day)
        f.addRow("Memory Day every (days):", self.s_md)
        f.addRow(self.s_greet)
        f.addRow("Greeting:", self.s_greeting)
        f.addRow(self.s_requests)
        f.addRow(self.s_recall)
        f.addRow(self.s_think)
        f.addRow(load)
        return w

    # ---- companions ----
    def fill_companions(self, select=None):
        from .companion import _read
        base = companions()
        self.pick.clear()
        folders = sorted(d for d in base.glob("*") if (d / "companion.json").exists()) if base.is_dir() else []
        for d in folders:
            cfg = _read(d / "companion.json", {})
            self.pick.addItem(cfg.get("name") or "(not named yet)", str(d))
        last = select or _read(base / "app.json", {}).get("last")
        if folders:
            i = max(0, self.pick.findData(last)) if last else 0
            self.pick.setCurrentIndex(i)
            self.open(self.pick.currentData())
        else:
            self._detach()
            self.comp = None
            self.typing.clear()
            self.events.clear()
            self.cores.clear()
            self.portrait.clear()
            self.proposal_box.hide()
            self.chat.setHtml(_html("system", "", "Welcome to Soul and Song: an AI Companion with structured, "
                                                  "growing memory, from the Companion Project guide.\n\nClick New "
                                                  "Companion... to begin."))
            self.refresh_panel()

    def _detach(self):
        """The open Companion stops where it is (its lines stay its own)."""
        if self.comp is not None:
            self.comp.queue.clear()
            self.comp.on_line = self.comp.on_stream = lambda *a: None
            self.comp.on_changed = lambda: None
            self.brain.stop()

    def delete_companion(self):
        """Put the open Companion away: its folder moves to Companions\\Deleted (move it back to bring them back)."""
        if self.comp is None:
            return
        c = self.comp
        memories = sum(c.mind.count(level) for level in KINDS)
        days = len(list((c.folder / "Chats").glob("*.txt"))) if (c.folder / "Chats").is_dir() else 0
        box = QMessageBox(QMessageBox.Warning, "Delete Companion",
                          f"Delete {c.name}?\n\nBorn {(c.cfg.get('birthday') or '')[:10]} - {memories} memories in "
                          f"their banks, {len(c.recall.items)} in their archive, {days} day(s) of conversation.\n\n"
                          f"Their folder moves to Companions\\Deleted, so nothing is lost for good: to bring {c.name} "
                          "back, move it back into Companions.", QMessageBox.Yes | QMessageBox.No, self)
        box.setDefaultButton(QMessageBox.No)
        if box.exec() != QMessageBox.Yes:
            return
        import shutil
        self._detach()
        self.comp = None
        gone = companions() / "Deleted"
        gone.mkdir(parents=True, exist_ok=True)
        safe = re.sub(r'[\\/:*?"<>|]', "", c.name).strip() or "Companion"
        target = gone / f"{datetime.now():%Y-%m-%d %H%M} {safe} ({c.folder.name})"
        try:
            shutil.move(str(c.folder), str(target))
        except OSError as e:
            QMessageBox.warning(self, "Delete Companion", f"{c.name}'s folder couldn't be moved:\n{e}")
            self.open(str(c.folder))
            return
        from .companion import _write
        _write(companions() / "app.json", {"last": ""})
        self.fill_companions()
        self._line("system", f"{c.name} was deleted (kept in Companions\\Deleted\\{target.name}).")

    def new_companion(self):
        user = self.comp.cfg.get("user_name") if self.comp else ""
        d = NewCompanion(self, user or "")
        if d.exec() != QDialog.Accepted:
            return
        folder = companions() / datetime.now().strftime("companion-%Y%m%d-%H%M%S")
        C.create(folder, project(), d.user.text().strip(), d.name.text().strip(), d.gender.text().strip(),
                 d.model.currentData() or "")
        self.fill_companions(select=str(folder))

    def open(self, folder):
        if not folder:
            return
        from .companion import _write
        _write(companions() / "app.json", {"last": folder})
        self._detach()                                  # the one before stops where it is
        self.comp = C.Companion(folder, self.brain)
        self.comp.on_line = self._line
        self.comp.on_stream = lambda t: self.typing.setText(f"{self.comp.name} is writing: {t[-400:]}")
        self.brain.on_thinking = lambda t: self.typing.setText(f"{self.comp.name} is thinking: {t[-400:]}")
        self.comp.on_changed = self.refresh_panel
        self.comp.on_name = self._confirm_name
        self.chat.clear()
        for m in self.comp.history[-60:]:
            who = (self.comp.cfg.get("user_name") or "You") if m["role"] == "user" else self.comp.name
            self.chat.append(_html("user" if m["role"] == "user" else "companion", who, m["content"]))
        self.load_settings()
        self.refresh_roadmaps()
        self.refresh_panel()
        self.refresh_self()
        self.runner.restore()
        self._auto_refresh()
        self.load_model()

    def load_model(self):
        from kithylinai.engine import find
        key = self.comp.cfg.get("model")
        model = find(key) if key else None
        if model is None:
            models = model_list()
            model = models[0] if models else None
        if model is None:
            self._line("system", "No local models found (Local Storage\\LLM Models, or Kithylin AI's Models folder).")
            return
        want = (model.key, self.comp.cfg.get("engine"), self.comp.cfg.get("context"))
        self.comp.cfg["model"] = model.key
        self.comp.save()
        self.wanted = (model, want)
        if self.loaded_key == want and self.brain.engine.ready:
            self._substrate(model)
            self.comp.start()
            return
        if self.brain.engine._loader is not None and self.brain.engine._loader.isRunning():
            # another model is still loading: this one waits for it, then loads (see _ready) - a Companion never
            # starts on a model that isn't its own
            self._line("system", f"Waiting for the last model to finish loading, then loading {model.title}...")
            return
        self._load(model, want)

    def _load(self, model, want):
        self.loaded_key = want
        self.brain.load(model, self.comp.cfg.get("engine", "auto"), int(self.comp.cfg.get("context", 32768)))

    def _ready(self, ok):
        model, want = getattr(self, "wanted", (None, None))
        if model is not None and want != self.loaded_key:
            self._load(model, want)                    # (it was asked for while another was loading)
            return
        if ok and self.comp is not None and self.brain.engine.model is not None \
                and self.brain.engine.model.key == self.comp.cfg.get("model"):
            self._substrate(self.brain.engine.model)
            self.comp.start()
        self.refresh_panel()

    def _substrate(self, model):
        """The Companion's L1 'My Substrate': the model it's on (a move is told to it)."""
        if model is None or self.comp is None:
            return
        about = (model.info.get("source") or "").split(":")[0].strip()[:160]
        self.comp.cfg["engine_context"] = engine_context(model)
        self.comp.set_substrate(model.title, about, self.comp.context_size())
        self.refresh_self()

    def _confirm_name(self, guess, accept):
        name, ok = QInputDialog.getText(self, "Your Companion's name",
                                        f"Your Companion chose a name for themselves:\n\n{guess or '(no name yet)'}\n\n"
                                        "Keep it, or change it if you'd rather:", text=guess)
        accept((name.strip() if ok else "") or guess)
        self.fill_names()

    def fill_names(self):
        i = self.pick.currentIndex()
        if self.comp and i >= 0:
            self.pick.setItemText(i, self.comp.name)

    # ---- the conversation ----
    def send(self):
        text = self.composer.toPlainText().strip()
        if not text or self.comp is None:
            return
        if not self.brain.engine.ready:
            self._line("system", "The model is still loading - one moment.")
            return
        self.composer.clear()
        self.runner.user_spoke()
        self.comp.say(text)

    def _line(self, kind, text):
        self.typing.clear() if kind == "companion" else None
        who = ""
        if self.comp is not None:
            who = ("Guided session" if kind == "guide" else (self.comp.cfg.get("user_name") or "You")
                   if kind == "user" else self.comp.name)
        self.chat.append(_html(kind, who, text))
        self.chat.verticalScrollBar().setValue(self.chat.verticalScrollBar().maximum())
        self.fill_names()

    # ---- the side panel ----
    def refresh_panel(self):
        c = self.comp
        if c is None:
            self.state.setText("")
            return
        for level, bank in self.banks.items():
            bank.set(c.mind.count(level))
        last = c.cfg.get("last_memory_day") or (c.cfg.get("birthday") or "")[:10]
        try:
            from datetime import timedelta
            nxt = datetime.fromisoformat(last[:10]) + timedelta(days=int(c.cfg.get("memory_day_every", 7)))
            self.next_day.setText(f"Next Memory Day: {nxt:%A, %B %d} (or as soon as L3 holds seven).\n"
                                  f"Birthday: {(c.cfg.get('birthday') or '')[:10]}")
        except ValueError:
            self.next_day.setText("")
        try:
            used = c.context_used()
        except Exception:
            used = 0
        self.ctx.setRange(0, c.context_size())
        self.ctx.setValue(min(used, c.context_size()))
        ready = self.brain.engine.ready
        self.state.setText(("thinking..." if c.busy else "ready") if ready else "loading the model...")
        self.send_btn.setEnabled(ready)

    def refresh_roadmaps(self):
        while self.user_form.rowCount():
            self.user_form.removeRow(0)
        self.user_edits = []
        for k, v in self.comp.mind.user_fields():
            e = QLineEdit(v)
            self.user_form.addRow(k + ":", e)
            self.user_edits.append((k, e))
        self.comp_road.setPlainText(self.comp.mind.roadmap("companion"))
        self.refresh_events()

    def save_roadmaps(self):
        if self.comp is None:
            return
        self.comp.mind.set_user_fields([(k, e.text().strip()) for k, e in self.user_edits])
        self.comp.mind.set_roadmap("companion", self.comp_road.toPlainText())
        self._line("system", "Roadmaps saved in L1.")

    def refresh_events(self):
        self.events.clear()
        if self.comp is None:
            return
        for e in self.comp.mind.events():
            item = QListWidgetItem(f"#{e['id']}  {e['when']}  {e['description']}" + ("  (done)" if e["done"] else ""))
            item.setData(Qt.UserRole, e["id"])
            self.events.addItem(item)

    def _event_list(self):
        return self.comp.mind.events() if self.comp else []

    def add_event(self):
        if self.comp is None:
            return
        d = EventDialog(self)
        if d.exec() == QDialog.Accepted and d.desc.text().strip():
            evs = self._event_list()
            nid = f"{max([int(e['id']) for e in evs if e['id'].isdigit()] or [0]) + 1:03d}"
            evs.append({"id": nid, "when": d.when.dateTime().toString("yyyy-MM-dd HH:mm"),
                        "description": d.desc.text().strip(), "done": False})
            self.comp.mind.set_events(evs)
            self.refresh_events()

    def _selected_event(self):
        item = self.events.currentItem()
        return item.data(Qt.UserRole) if item else None

    def edit_event(self):
        eid = self._selected_event()
        evs = self._event_list()
        e = next((x for x in evs if x["id"] == eid), None)
        if e is None:
            return
        d = EventDialog(self, e)
        if d.exec() == QDialog.Accepted:
            e["when"], e["description"] = d.when.dateTime().toString("yyyy-MM-dd HH:mm"), d.desc.text().strip()
            told = [x for x in self.comp.cfg.get("events_told", []) if x != eid]     # (a new time: told again)
            self.comp.cfg["events_told"] = told
            self.comp.mind.set_events(evs)
            self.comp.save()
            self.refresh_events()

    def done_event(self):
        eid = self._selected_event()
        evs = self._event_list()
        for e in evs:
            if e["id"] == eid:
                e["done"] = True
        self.comp.mind.set_events(evs)
        self.refresh_events()

    def remove_event(self):
        eid = self._selected_event()
        self.comp.mind.set_events([e for e in self._event_list() if e["id"] != eid])
        self.refresh_events()

    def load_settings(self):
        c = self.comp.cfg
        self.s_user.setText(c.get("user_name", ""))
        self.s_model.clear()
        for m in model_list():
            self.s_model.addItem(m.label, m.key)
        i = self.s_model.findData(c.get("model"))
        self.s_model.setCurrentIndex(max(0, i))
        self.s_engine.setCurrentText(c.get("engine", "auto"))
        self.s_ctx.setValue(int(c.get("context", 32768)))
        self.s_temp.setValue(float(c.get("temperature", 0.8)))
        self.s_every.setValue(int(c.get("memory_every", 10)))
        self.s_day.setValue(int(c.get("day_starts", 4)))
        self.s_md.setValue(int(c.get("memory_day_every", 7)))
        self.s_greet.setChecked(bool(c.get("auto_greet", True)))
        self.s_greeting.setText(c.get("greeting", C.DEFAULTS["greeting"]))
        self.s_requests.setChecked(bool(c.get("show_requests")))
        self.s_recall.setChecked(bool(c.get("recall", True)))
        self.s_think.setChecked(bool(c.get("think", False)))
        self.brain.think = bool(c.get("think", False))

    def save_settings(self):
        if self.comp is None:
            return
        c = self.comp.cfg
        c.update(user_name=self.s_user.text().strip(), model=self.s_model.currentData() or c.get("model", ""),
                 engine=self.s_engine.currentText(), context=self.s_ctx.value(), temperature=self.s_temp.value(),
                 memory_every=self.s_every.value(), day_starts=self.s_day.value(), memory_day_every=self.s_md.value(),
                 auto_greet=self.s_greet.isChecked(), greeting=self.s_greeting.text().strip() or
                 C.DEFAULTS["greeting"], show_requests=self.s_requests.isChecked(),
                 recall=self.s_recall.isChecked(), think=self.s_think.isChecked())
        self.brain.think = self.s_think.isChecked()
        self.comp.save()
        self._line("system", "Settings saved.")
        self.load_model()

    # ---- by hand ----
    def edit_mind(self):
        if self.comp is not None:
            MindEditor(self, self.comp.mind).exec()
            self.refresh_roadmaps()
            self.refresh_panel()

    def open_folder(self):
        if self.comp is None:
            return
        try:
            from claudecore import host
            host.open_folder(self.desktop, self.comp.folder)
        except Exception:
            import os
            os.startfile(str(self.comp.folder)) if hasattr(os, "startfile") else None

    def shutdown(self):
        self.ticker.stop()
        self.auto_timer.stop()
        self.panel_timer.stop()
        self.brain.shutdown()
        from . import recall
        recall.shutdown()
