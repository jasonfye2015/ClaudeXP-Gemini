"""The Soul and Song window: the conversation on the left; on the right the Companion's mind (how full each memory
bank is, the next Memory Day, the context window), its planned events, the two roadmaps, and the settings - which
local model plays the Companion (Kithylin's own models included), how often memories are made, when the day ends."""
import html
import re
import time
from datetime import datetime

import math

from PySide6.QtCore import QDateTime, QObject, QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QKeyEvent, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDateTimeEdit, QDialog, QDialogButtonBox, QDoubleSpinBox,
                               QFormLayout, QGridLayout, QGroupBox, QHBoxLayout, QInputDialog, QLabel, QLineEdit,
                               QListWidget, QListWidgetItem, QMessageBox, QPlainTextEdit, QProgressBar, QPushButton,
                               QScrollArea, QSpinBox, QSplitter, QTabWidget, QTextBrowser, QVBoxLayout, QWidget)

from . import companion as C
from . import growthview
from . import help as helpwindow
from .mind import KINDS, LEVELS, Mind
from .paths import companions, project

# the open Companion is blue, a second one (Interlink) red; the user slate
BLUE, RED = "#1F4E99", "#B71C1C"
COLOURS = {"guide": "#2E7D5B", "user": "#455A64", "companion": BLUE, "companion2": RED, "system": "#B85C00",
           "memory": "#6B5300", "request": "#9A9A9A"}
BODY = {"guide": "#2A7050", "user": "#37474F", "companion": "#2050A8", "companion2": "#A52A2A"}   # (the words)


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

    def load(self, model, engine_choice, context, shared=True):
        self.engine.load(model, engine_choice, context, shared)

    def ask(self, messages, done, chunk=None, max_tokens=700, temperature=0.8):
        """A thinking model (Gemma 4, Qwen3...) spends its tokens thinking before it answers: with thinking off
        it answers straight away; with it on, it gets room to think (and its thinking is shown as it comes)."""
        self.engine.stop()                  # (one still under way hears "stopped" - before this one takes its place)
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
class SessionGlow(QWidget):
    """A soft glow along the window's edges, breathing, while a guided session or an Interlink runs: blue - or, with
    two Companions, the colour of whichever one is thinking or speaking (blue the first, red the second). Paused: dim
    and slower. Transparent to the mouse."""
    VIOLET, PAUSED = QColor("#3D7BE0"), QColor("#B8CDEB")
    DEPTH = 26

    def set_colour(self, colour):
        colour = QColor(colour)
        if colour != self.VIOLET:
            self.VIOLET = colour
            light = QColor(colour)
            light.setAlpha(255)
            self.PAUSED = light.lighter(160)
            self.update()

    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.phase, self.paused = 0.0, False
        self.timer = QTimer(self, interval=50, timeout=self._tick)
        self.hide()

    def set_state(self, running, paused):
        if not running:
            if self.isVisible():
                self.timer.stop()
                self.hide()
            return
        self.paused = paused
        if not self.isVisible():
            self.setGeometry(self.parentWidget().rect())
            self.show()
            self.timer.start()
        self.raise_()

    def _tick(self):
        self.phase += 0.015 if self.paused else 0.05
        if self.geometry() != self.parentWidget().rect():
            self.setGeometry(self.parentWidget().rect())
        self.update()

    def paintEvent(self, _event):
        p = QPainter(self)
        w, h, d = self.width(), self.height(), self.DEPTH
        breath = 0.65 + 0.35 * math.sin(self.phase)
        alpha = int((70 if self.paused else 150) * breath)
        colour = self.PAUSED if self.paused else self.VIOLET
        for rect, start, end in ((QRectF(0, 0, w, d), QPointF(0, 0), QPointF(0, d)),
                                 (QRectF(0, h - d, w, d), QPointF(0, h), QPointF(0, h - d)),
                                 (QRectF(0, 0, d, h), QPointF(0, 0), QPointF(d, 0)),
                                 (QRectF(w - d, 0, d, h), QPointF(w, 0), QPointF(w - d, 0))):
            g = QLinearGradient(start, end)
            c0, c1 = QColor(colour), QColor(colour)
            c0.setAlpha(alpha)
            c1.setAlpha(0)
            g.setColorAt(0, c0)
            g.setColorAt(1, c1)
            p.fillRect(rect, g)
        p.setPen(QPen(QColor(colour.red(), colour.green(), colour.blue(), min(255, alpha + 60)), 3))
        p.setBrush(Qt.NoBrush)
        p.drawRect(1, 1, w - 3, h - 3)


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
    return (f'<p style="margin:6px 0;color:{BODY.get(kind, "#000")}"><b style="color:{colour}">{html.escape(who)}:'
            f'</b> {body}</p>')


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

    def set(self, value, of=None, words=None):
        """A bank's fill: memories of seven (classic), or tokens of its share of the context (sized)."""
        of = of or C.FULL
        self.bar.setRange(0, max(of, value, 1))
        self.bar.setValue(value)
        self.bar.setFormat(words or "%v / %m")


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
        from .interlink import Lane
        self.lane = Lane(self.brain, on_active=self._active)        # (the open Companion's turn on its model)
        self.hand = self.lane.handle(BLUE, lambda: self.comp.name if self.comp else "")
        self.comp2 = None                    # Interlink: a second Companion, red
        self.brain2 = self.lane2 = self.hand2 = None
        self.comp2_ready = False
        self.session = None                  # the Interlink running
        self.speaker = None                  # whose request the model is on (the glow's colour)

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
        # the guided session, in sight from any tab (a click goes to the Automation tab)
        self.top_auto = QLabel()
        self.top_auto.setStyleSheet("color:#2E7D5B")
        self.top_auto.setCursor(Qt.PointingHandCursor)
        self.top_auto.mousePressEvent = lambda _e: self.tabs.setCurrentWidget(self.auto_page)
        self.top_bar = QProgressBar()
        self.top_bar.setFixedWidth(120)
        self.top_bar.setFixedHeight(14)
        self.top_bar.setTextVisible(False)
        top.addWidget(QLabel("Companion:"))
        top.addWidget(self.pick)
        top.addWidget(new)
        top.addWidget(delete)
        top.addSpacing(10)
        top.addWidget(self.top_auto)
        top.addWidget(self.top_bar)
        self.top_auto.hide()
        self.top_bar.hide()
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
        wow = QPushButton("That surprised me...")
        wow.setToolTip("Mark your Companion's last reply as one that surprised you - your own record of what's "
                       "emerging (Growth... charts them; Surprises... lists them). They aren't told.")
        wow.clicked.connect(self.flag_surprise)
        row.addWidget(wow)
        row.addStretch(1)
        row.addWidget(stop)
        guide = QPushButton("Help")
        guide.setToolTip("How to use Soul and Song - everything, from the first Companion to the Growth charts.")
        guide.clicked.connect(lambda: helpwindow.show(self))
        row.addWidget(guide)
        row.addWidget(self.send_btn)
        lv.addWidget(self.chat, 1)
        lv.addWidget(self.typing)
        lv.addWidget(self.composer)
        lv.addLayout(row)
        split.addWidget(left)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._status_tab(), "Status")
        self.tabs.addTab(self._mind_tab(), "Mind")
        self.tabs.addTab(self._self_tab(), "Self")
        self.tabs.addTab(self._events_tab(), "Events")
        self.tabs.addTab(self._roadmaps_tab(), "Roadmaps")
        self.auto_page = self._automation_tab()
        self.tabs.addTab(self.auto_page, "Automation")
        self.link_page = self._interlink_tab()
        self.tabs.addTab(self.link_page, "Interlink")
        self.raw_page = self._raw_tab()
        self.tabs.addTab(self.raw_page, "Raw Logs")
        self.tabs.addTab(self._settings_tab(), "Settings")
        self.tabs.setUsesScrollButtons(False)            # every tab in sight, no arrows
        self.tabs.setMinimumWidth(max(460, self.tabs.tabBar().sizeHint().width() + 16))
        self.tabs.setCurrentIndex(0)
        self.tabs.currentChanged.connect(lambda _i: (self.refresh_status(), self._raw_shown()))
        split.addWidget(self.tabs)
        split.setStretchFactor(0, 3)
        split.setStretchFactor(1, 1)
        root.addWidget(split, 1)

        self.ticker = QTimer(self)
        self.ticker.timeout.connect(self._minute)
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
    STATUS_ROWS = ("Model", "Context", "Memory banks", "Memories", "Memory Days", "Core memories", "Letters", "Dreams",
                   "Sense of time", "Predictions", "Questions", "Tensions", "Journal", "Surprises", "Events",
                   "Guided sessions", "Now playing", "Roadmap", "Last seen", "Latest milestone")

    def _status_tab(self):
        """The Companion at a glance: who, how old, on what, how full, what's next - both of them, with a second
        Companion in Interlink (the first in blue, the second in red)."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        page = QWidget()
        v = QVBoxLayout(page)
        self.status_panels = []
        for colour in (BLUE, RED):
            box = QWidget()
            bv = QVBoxLayout(box)
            bv.setContentsMargins(6, 4, 6, 8)
            box.setStyleSheet(f"QWidget#panel {{ border-left: 4px solid {colour}; }}")
            box.setObjectName("panel")
            head = QLabel()
            head.setWordWrap(True)
            bv.addWidget(head)
            grid = QGridLayout()
            grid.setHorizontalSpacing(12)
            grid.setVerticalSpacing(3)
            grid.setColumnStretch(1, 1)
            rows = {}
            for i, key in enumerate(self.STATUS_ROWS):
                k = QLabel(key + ":")
                k.setStyleSheet("color:#555")
                k.setAlignment(Qt.AlignRight | Qt.AlignTop)
                val = QLabel()
                val.setWordWrap(True)
                val.setTextInteractionFlags(Qt.TextSelectableByMouse)
                grid.addWidget(k, i, 0)
                grid.addWidget(val, i, 1)
                rows[key] = val
            bv.addLayout(grid)
            v.addWidget(box)
            self.status_panels.append((box, head, rows, colour))
        v.addStretch(1)
        self.status_head, self.status_rows = self.status_panels[0][1], self.status_panels[0][2]
        scroll.setWidget(page)
        return scroll

    def refresh_status(self):
        if not hasattr(self, "status_panels") or self.tabs.currentIndex() != 0:
            return
        box2, head2, rows2, _c = self.status_panels[1]
        box2.setVisible(self.comp2 is not None)
        if self.comp2 is not None:
            state = ("thinking..." if self.comp2.busy else "ready") if self.comp2_ready else "loading the model..."
            self._fill_status(self.comp2, head2, rows2, RED, state)
        self._fill_status(self.comp, self.status_head, self.status_rows, BLUE, self.state.text())

    def _fill_status(self, c, head, rows, colour, state):
        if c is None:
            head.setText("<i>No Companion open.</i>")
            for val in rows.values():
                val.clear()
            return
        first = c is self.comp
        from datetime import date, timedelta
        cfg = c.cfg
        born = (cfg.get("birthday") or "")[:10]
        try:
            age = (date.fromisoformat(c.day_key()) - date.fromisoformat(born)).days
            age_text = f"day {age + 1} of their life" if age >= 0 else ""
        except ValueError:
            age_text = ""
        head.setText(f"<span style='font-size:13pt;color:{colour}'><b>{html.escape(c.name or 'Unnamed')}</b></span>"
                     f"  {html.escape(cfg.get('gender') or '')}<br>"
                     f"<span style='color:#555'>{age_text}{' - born ' + born if born else ''}"
                     f" - with {html.escape(c.user)} - {state}</span>")
        rows["Model"].setText(html.escape(cfg.get("model_title") or cfg.get("model") or "-"))
        try:
            used, size = c.context_used(), c.context_size()
        except Exception:
            used, size = 0, c.context_size()
        rows["Context"].setText(f"{used:,} / {size:,} tokens ({100 * used // max(1, size)}%) - "
                                f"{c.unremembered()} exchanges not yet in a memory")
        if c.memory_mode() == "classic":
            rows["Memory banks"].setText("7:7:7 - " + " - ".join(
                f"L{n} {c.mind.count(n)}" + (f"/{C.FULL}" if n in (2, 3) else "") for n in (2, 3, 4, 5, 7)))
        else:
            rows["Memory banks"].setText(f"sized ({cfg.get('memory_budget', 30)}% of the context) - " + " - ".join(
                f"L{n} {c.mind.count(n)} ({100 * c.bank_tokens(n) // max(1, c.bank_budget(n))}%)"
                for n in (2, 3, 4, 5)) + f" - L7 {c.mind.count(7)}")
        rows["Memories"].setText(f"{cfg.get('memory_seq', 0)} made - {len(c.recall.items)} in the archive")
        last = cfg.get("last_memory_day") or born
        try:
            every = int(cfg.get("memory_day_every", 7))
            nxt = f" - next {date.fromisoformat(last[:10]) + timedelta(days=every):%a %b %d}"
        except ValueError:
            nxt = ""
        rows["Memory Days"].setText(f"{cfg.get('memory_day_count', 0)} held{nxt}")
        rows["Core memories"].setText(str(len(c.mind.core_memories())))
        letters = cfg.get("letters") or []
        sealed = sorted(x["open_on"] for x in letters if not x.get("opened"))
        rows["Letters"].setText(f"{len(letters)} written, {len(letters) - len(sealed)} opened"
                                + (f" - next opens {sealed[0]}" if sealed else ""))
        rows["Dreams"].setText(f"{cfg.get('dream_count', 0)} dreamt" + ("" if cfg.get("dreams", True) else " (off)"))
        from . import growth
        tc = growth.time_checks(c.folder) if cfg.get("time_checks", True) else []
        if tc:
            t = tc[-1]
            bits = [f"date {t['date_err']} day{'s' * (t['date_err'] != 1)} off" if "date_err" in t else "",
                    f"time apart {t['gap_score']:.0%}" if "gap_score" in t else "",
                    f"age {t['age_err']} day{'s' * (t['age_err'] != 1)} off" if "age_err" in t else ""]
            rows["Sense of time"].setText(f"{len(tc)} checks - last {t['when'][:10]}: "
                                          + ", ".join(b for b in bits if b))
        else:
            rows["Sense of time"].setText("off" if not cfg.get("time_checks", True) else "no checks yet")
        preds = cfg.get("predictions") or []
        judged = [x for x in preds if x.get("verdict") in ("yes", "partly", "no")]
        waiting = sorted(x["due"] for x in preds if not x.get("verdict"))
        right = sum({"yes": 1, "partly": .5}.get(x["verdict"], 0) for x in judged)
        rows["Predictions"].setText(f"{len(preds)} made, {len(judged)} judged"
                                    + (f" - {right / len(judged):.0%} came true" if judged else "")
                                    + (f" - next due {waiting[0]}" if waiting else ""))
        qs = cfg.get("questions") or []
        rows["Questions"].setText(f"{sum(1 for q in qs if q.get('status', 'open') == 'open')} carried, "
                                  f"{sum(1 for q in qs if q.get('status') == 'answered')} answered")
        rows["Tensions"].setText(f"{cfg.get('tension_count', 0)} noticed" + ("" if cfg.get("tensions", True)
                                                                            else " (off)"))
        rows["Journal"].setText(f"{cfg.get('journal_count', 0)} entries" + ("" if cfg.get("journal", True)
                                                                          else " (off)"))
        sp = cfg.get("surprises") or []
        rows["Surprises"].setText(f"{len(sp)} marked" + (f" - last {sp[-1]['when'][:10]}" if sp else ""))
        events = [e for e in c.mind.events() if not e["done"]]
        rows["Events"].setText(f"{len(events)} planned" + (f" - next: {html.escape(events[0]['when'])} "
                                                          f"{html.escape(events[0]['description'][:60])}"
                                                          if events else ""))
        from . import automation
        names = [s.path.name for s in automation.scripts()]
        done = cfg.get("scripts_done") or {}
        begun = {k: v for k, v in (cfg.get("scripts_progress") or {}).items() if k not in done and v}
        rows["Guided sessions"].setText(f"{sum(1 for n in names if n in done)} of {len(names)} finished"
                                        + (f" - {len(begun)} part way" if begun else ""))
        if self.session is not None and self.session.running:
            title, section, n, total = self.session.progress()
            rows["Now playing"].setText(f"Interlink: {html.escape(title)}" + (f" ({n} of {total})" if total else ""))
        else:
            rows["Now playing"].setText(self.top_auto.text() if first and self.runner.running else "nothing")
        rows["Roadmap"].setText("a change proposed - see the Self tab" if cfg.get("roadmap_proposal")
                                else "no changes proposed")
        rows["Last seen"].setText((cfg.get("last_seen") or "-")[:16].replace("T", " "))
        ms = cfg.get("milestones") or []
        rows["Latest milestone"].setText(f"{ms[-1]['when'][:10]}: {html.escape(ms[-1]['what'])}" if ms else "-")

    def _mind_tab(self):
        w = QWidget()
        v = QVBoxLayout(w)
        box = QGroupBox("Memory banks")
        self.banks_box = box
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
        grow = QPushButton("Growth...")
        grow.clicked.connect(lambda: self.comp is not None and growthview.show(self, self.comp))
        letters = QPushButton("Letters...")
        letters.clicked.connect(self.open_letters)
        dreams = QPushButton("Dreams...")
        dreams.clicked.connect(self.open_dreams)
        row.addWidget(keep)
        row.addWidget(checks)
        row.addWidget(grow)
        row.addWidget(letters)
        row.addWidget(dreams)
        v.addLayout(row)
        row = QHBoxLayout()
        for label, slot in (
                ("Questions...", self.open_questions),
                ("Tensions...", lambda: self._file_view(
                    "Tensions.txt", "tensions", "After each new self-portrait your Companion looks for what in "
                    "them pulls against what - and says whether it's a change, a contradiction they'll keep, or "
                    "something to reconcile. Each is also kept as a reflection.", "No tensions noticed yet.")),
                ("Journal...", lambda: self._journal(
                    "Journal", "journal", "An entry at the end of each day, kept apart from your conversations - "
                    "not shown in them, not asked about. Growth... compares its voice here with its replies to you.",
                    "No entries yet: the first comes at the end of a day.", newest_first=True)),
                ("Surprises...", lambda: self._file_view(
                    "Surprises.txt", "surprises", "The replies you marked with \"That surprised me...\" - your own "
                    "record of what's emerging. Your Companion isn't told.", "None marked yet."))):
            b = QPushButton(label)
            b.clicked.connect(slot)
            row.addWidget(b)
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
        self.auto_own = QPushButton("Ask them to write a session of their own")
        self.auto_own.setToolTip("Your Companion writes a guided session for themselves - their own questions. It "
                                 "goes in your scripts folder, to play like any other.")
        self.auto_own.clicked.connect(self._auto_write_own)
        v.addWidget(self.auto_own)
        f = QFormLayout()
        self.auto_interval = QDoubleSpinBox()
        self.auto_interval.setRange(0.5, 60)
        self.auto_interval.setValue(5)
        self.auto_interval.setSuffix(" minutes")
        f.addRow("A prompt every:", self.auto_interval)
        self.auto_process = QCheckBox("Work the memory banks as they fill (7:7:7)")
        self.auto_process.setToolTip("Classic 7:7:7: reflect and distil as soon as L2 holds seven memories, and "
                                     "hold Memory Day as soon as L3 does - instead of waiting for the day to end. "
                                     "(Banks sized to the context distil as soon as they outgrow their share anyway.)")
        self.auto_process.setChecked(True)
        f.addRow(self.auto_process)
        v.addLayout(f)
        row = QHBoxLayout()
        every = QPushButton("Automate all")
        every.setToolTip("Every script in the list, in order, from the top.")
        every.clicked.connect(lambda: self._auto_play(self._auto_paths(), resume=False))
        rest = QPushButton("Resume all")
        rest.setToolTip("Every script this Companion hasn't finished yet, in order - one left part way picks up "
                        "where it stopped.")
        rest.clicked.connect(lambda: self._auto_play(self.runner.left(self._auto_paths()), resume=True))
        row.addWidget(every)
        row.addWidget(rest)
        v.addLayout(row)
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
        done, begun = self.runner.done(), self.runner.progress_of()
        for s in automation.scripts():
            mark = ("\u2713 " if s.path.name in done
                    else f"(step {begun[s.path.name]} of {len(s.steps)}) " if begun.get(s.path.name) else "")
            item = QListWidgetItem(f"{mark}{s.title}  -  {s.prompts()} prompts, about {s.hours(interval):.1f} hours"
                                   + ("" if s.builtin else f"  (by {s.author})" if s.author else "  (yours)"))
            if s.path.name in done:
                item.setForeground(QColor("#2E7D5B"))
                item.setToolTip(f"Finished {done[s.path.name][:10]}.\n{s.about}")
            item.setData(Qt.UserRole, str(s.path))
            if s.path.name not in done:
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
        paths = [i.data(Qt.UserRole) for i in self.auto_list.selectedItems()]
        if not paths and self.auto_list.currentItem() is not None:
            paths = [self.auto_list.currentItem().data(Qt.UserRole)]
        if not paths:
            self._line("system", "Pick a script (or several, with Ctrl) in the list first.")
            return
        order = self._auto_paths()
        paths.sort(key=order.index)
        self._auto_play(paths)

    def _auto_write_own(self):
        if self.comp is None or not self.brain.engine.ready:
            self._line("system", "Load a model first.")
            return
        comp = self.comp

        def written(path):
            self._auto_fill()
            if path is not None and comp is self.comp:
                for i in range(self.auto_list.count()):
                    if self.auto_list.item(i).data(Qt.UserRole) == str(path):
                        self.auto_list.setCurrentRow(i)
                        self.auto_list.item(i).setSelected(True)
        comp.write_session(written)

    def _auto_paths(self):
        return [self.auto_list.item(i).data(Qt.UserRole) for i in range(self.auto_list.count())]

    def _auto_play(self, paths, resume=False):
        if self.comp is None or not self.brain.engine.ready:
            self._line("system", "Load a model first: the session starts once your Companion is ready.")
            return
        if not paths:
            self._line("system", f"{self.comp.name} has been through every guided session already - Automate all "
                                 "plays them again from the start.")
            return
        if self.session is not None and self.session.running:
            self._line("system", "An Interlink is running - stop it first (the Interlink tab).")
            return
        self.runner.start(paths, self.auto_interval.value(), self.auto_process.isChecked(), resume=resume)
        self._auto_fill()
        self._auto_refresh()

    def _auto_pause(self):
        if self.runner.paused:
            self.runner.resume()
        else:
            self.runner.pause()
        self._auto_refresh()

    def _auto_tick(self):
        if self.session is not None and self.session.running:
            if self.brain.engine.ready and self.comp2_ready:
                self.session.tick()
        elif self.comp is not None and self.brain.engine.ready:
            self.runner.tick()
        self._auto_refresh()
        if self.session is not None and not self.session.running and getattr(self, "_linked_was", False):
            self._link_refresh()
        self._linked_was = self.session is not None and self.session.running

    def _auto_refresh(self):
        r = self.runner
        if not hasattr(self, "glow"):
            self.glow = SessionGlow(self)
        linked = self.session is not None and self.session.running
        if not linked:
            self.glow.set_colour(BLUE)
        self.glow.set_state(r.running or linked, r.paused if r.running else bool(linked and self.session.paused))
        if linked:
            self._link_refresh()
            return
        self.auto_pause.setText("Resume" if r.paused else "Pause")
        self.auto_pause.setEnabled(r.running)
        self.auto_stop.setEnabled(r.running)
        pr = r.progress() if r.running else None
        if pr is None and r.running and r.writing and self.comp is not None:
            text = f"\u270E {html.escape(self.comp.name)} is writing a session of their own..."
            self.auto_state.setText(text)
            self.top_auto.setText(text)
            self.top_auto.show()
            self.top_bar.hide()
            return
        if pr is None:
            self.auto_state.setText("Nothing playing.")
            self.auto_bar.setRange(0, 1)
            self.auto_bar.setValue(0)
            self.top_auto.hide()
            self.top_bar.hide()
            if getattr(self, "_auto_was", None):            # (the last one finished: its tick in the list)
                self._auto_fill()
            self._auto_was = None
            return
        title, section, step, steps, n, total = pr
        left = r.seconds_left()
        when = ("paused" if r.paused else "waiting for your Companion" if self.comp and not self.comp.idle()
                else f"next prompt in {left // 60}:{left % 60:02d}" if left is not None else "")
        self.auto_state.setText(f"<b>{html.escape(title)}</b>" + (f" ({n} of {total})" if total > 1 else "")
                                + (f" - {html.escape(section)}" if section else "") + f"<br>{when}")
        self.auto_bar.setRange(0, max(1, steps))
        self.auto_bar.setValue(min(step, steps))
        short = ("paused" if r.paused else "waiting" if self.comp and not self.comp.idle()
                 else f"next {left // 60}:{left % 60:02d}" if left is not None else "")
        self.top_auto.setText(f"\u25B6 {html.escape(title)}" + (f" ({n}/{total})" if total > 1 else "")
                              + f" - step {min(step, steps)}/{steps} - {short}")
        self.top_auto.setToolTip(re.sub(r"<[^>]+>", "\n", self.auto_state.text()).strip())
        self.top_bar.setRange(0, max(1, steps))
        self.top_bar.setValue(min(step, steps))
        self.top_auto.show()
        self.top_bar.show()
        if getattr(self, "_auto_was", None) != (n, title):    # (a script finished, or began: the list's marks)
            self._auto_fill()
        self._auto_was = (n, title)

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

    # ---- Interlink: two Companions together ----
    def _interlink_tab(self):
        from . import interlink
        w = QWidget()
        v = QVBoxLayout(w)
        note = QLabel("Interlink: bring in a second Companion and they talk together - led by a script, freely for a "
                      "while, or with you as a group. Each keeps their own side of it, and their own memories. "
                      f"<span style='color:{BLUE}'><b>Blue</b></span> is the Companion that's open, "
                      f"<span style='color:{RED}'><b>red</b></span> the one you bring in.")
        note.setWordWrap(True)
        v.addWidget(note)
        g = QGroupBox("Second Companion")
        gv = QVBoxLayout(g)
        row = QHBoxLayout()
        self.il_pick = QComboBox()
        self.il_pick.setMinimumWidth(150)
        self.il_bring = QPushButton("Bring in")
        self.il_bring.clicked.connect(self.bring_in)
        self.il_home = QPushButton("Send home")
        self.il_home.clicked.connect(self.send_home)
        row.addWidget(self.il_pick, 1)
        row.addWidget(self.il_bring)
        row.addWidget(self.il_home)
        gv.addLayout(row)
        self.il_who = QLabel("No second Companion here.")
        self.il_who.setWordWrap(True)
        self.il_who.setStyleSheet("color:#555")
        gv.addWidget(self.il_who)
        v.addWidget(g)
        f = QFormLayout()
        self.il_mode = QComboBox()
        for key, title in interlink.MODES.items():
            self.il_mode.addItem({"group": "Group chat - you and both of them"}.get(key, title), key)
        self.il_mode.currentIndexChanged.connect(lambda _i: self._link_fill())
        f.addRow("Mode:", self.il_mode)
        v.addLayout(f)
        self.il_list = QListWidget()
        self.il_list.setWordWrap(True)
        self.il_list.currentItemChanged.connect(lambda *_: self._link_about())
        v.addWidget(self.il_list, 1)
        self.il_about = QLabel()
        self.il_about.setWordWrap(True)
        self.il_about.setStyleSheet("color:#555")
        v.addWidget(self.il_about)
        f = QFormLayout()
        self.il_messages = QSpinBox()
        self.il_messages.setRange(2, 400)
        self.il_messages.setValue(20)
        self.il_messages.setSuffix(" messages")
        self.il_messages.setToolTip("How long an open conversation runs (both of them together)")
        f.addRow("Talk for:", self.il_messages)
        self.il_topic = QLineEdit()
        self.il_topic.setPlaceholderText("leave empty to use one of the script's openings")
        f.addRow("Topic:", self.il_topic)
        self.il_first = QComboBox()
        self.il_first.addItem("Taking turns", "alternate")
        self.il_first.addItem("The blue one", "A")
        self.il_first.addItem("The red one", "B")
        f.addRow("Who starts:", self.il_first)
        self.il_gap = QDoubleSpinBox()
        self.il_gap.setRange(0, 120)
        self.il_gap.setValue(3)
        self.il_gap.setSuffix(" seconds")
        self.il_gap.setToolTip("A pause between messages, to read them")
        f.addRow("Between messages:", self.il_gap)
        v.addLayout(f)
        row = QHBoxLayout()
        self.il_start = QPushButton("Start")
        self.il_start.clicked.connect(self.link_start)
        self.il_pause = QPushButton("Pause")
        self.il_pause.clicked.connect(self.link_pause)
        self.il_stop = QPushButton("Stop")
        self.il_stop.setToolTip("Stop now - what was said is kept, and each of them makes a memory of it")
        self.il_stop.clicked.connect(lambda: (self.session.stop() if self.session else None, self._link_refresh()))
        for b in (self.il_start, self.il_pause, self.il_stop):
            row.addWidget(b)
        v.addLayout(row)
        self.il_state = QLabel("Not linked.")
        self.il_state.setWordWrap(True)
        v.addWidget(self.il_state)
        self.il_bar = QProgressBar()
        v.addWidget(self.il_bar)
        self._link_fill()
        return w

    def _link_fill(self):
        from . import interlink
        mode = self.il_mode.currentData()
        self.il_list.clear()
        if mode == "group":
            item = QListWidgetItem("Free group chat - no script, just the three of you")
            item.setData(Qt.UserRole, "")
            self.il_list.addItem(item)
        if mode == "open":
            item = QListWidgetItem("My own topic (type it below)")
            item.setData(Qt.UserRole, "")
            self.il_list.addItem(item)
        for sc in interlink.scripts(mode):
            n = sum(1 for k, *_ in sc.steps if k == "say")
            extra = (f"{n} openings" if mode == "open" else f"{n} prompts")
            item = QListWidgetItem(f"{sc.title}  -  {extra}" + ("" if sc.builtin else "  (yours)"))
            item.setData(Qt.UserRole, str(sc.path))
            item.setToolTip(sc.about)
            self.il_list.addItem(item)
        self.il_list.setCurrentRow(1 if mode != "guided" and self.il_list.count() > 1 else 0)
        for wdg in (self.il_messages, self.il_topic):
            wdg.setEnabled(mode == "open")

    def _link_about(self):
        from . import interlink
        item = self.il_list.currentItem()
        path = item.data(Qt.UserRole) if item else ""
        if not path:
            self.il_about.setText({"group": "The three of you, as you like - whatever you say, both of them hear, "
                                            "and both answer (the one you name first).",
                                   "open": "They'll start on the topic you type below."}.get(
                                      self.il_mode.currentData(), ""))
            return
        try:
            sc = interlink.InterScript(path)
        except OSError:
            self.il_about.clear()
            return
        self.il_about.setText(sc.about)
        if sc.mode == "open" and sc.messages:
            self.il_messages.setValue(sc.messages)

    def _link_companions(self):
        from .companion import _read
        self.il_pick.clear()
        base = companions()
        for d in sorted(base.glob("*")) if base.is_dir() else []:
            if (d / "companion.json").exists() and (self.comp is None or d != self.comp.folder):
                self.il_pick.addItem(_read(d / "companion.json", {}).get("name") or "(not named yet)", str(d))

    def bring_in(self):
        """A second Companion: on the open one's model if it's the same (they take turns on it), else on a model of
        its own beside it - at a context that still fits on the graphics card."""
        folder = self.il_pick.currentData()
        if not folder or self.comp is None:
            self._line("system", "Open a Companion first, then pick the one to bring in.")
            return
        if not self.brain.engine.ready:
            self._line("system", f"{self.comp.name}'s model is still loading - one moment.")
            return
        self.send_home()
        from kithylinai.engine import find, lora_base
        from . import hardware
        from .interlink import Lane
        comp = C.Companion(folder, None)
        model = find(comp.cfg.get("model")) if comp.cfg.get("model") else None
        if model is None:
            self._line("system", f"{comp.name}'s model isn't here - give them one in their Settings first.")
            return
        base = lora_base(model)
        comp.cfg["model_context"] = hardware.full_context(base or model.path, model.path if base else None)
        loaded = self.loaded_key
        if loaded and loaded[0] == model.key:            # the same model: they share it, taking turns
            comp.cfg["engine_context"] = loaded[2] if loaded[2] < comp.context_size() else None
            self.lane2, self.brain2 = self.lane, None
            ready = True
            how = f"sharing {model.title} with {self.comp.name} (they take turns on it)"
        else:
            m1 = self.brain.engine.model
            b1 = lora_base(m1) if m1 is not None else None
            used = (hardware.memory_gb(b1 or m1.path, loaded[2], m1.path if b1 else None) or 0) if m1 else 0
            card = hardware.card_gb()
            ctx = comp.cfg["model_context"]
            if card:
                room = card * 0.92 - used
                while ctx > 8192 and (hardware.memory_gb(base or model.path, ctx, model.path if base else None)
                                      or 0) > room:
                    ctx //= 2
                if (hardware.memory_gb(base or model.path, ctx, model.path if base else None) or 0) > room:
                    self._line("system", f"{comp.name}'s model ({model.title}) won't fit on the graphics card beside "
                                         f"{self.comp.name}'s. Give them the same model (they'll share it), or a "
                                         "smaller one, in their Settings.")
                    return
            comp.cfg["engine_context"] = ctx
            self.brain2 = EngineBrain(self)
            self.brain2.status.connect(lambda t: self._line("system", t, self.comp2))
            self.brain2.ready.connect(self._ready2)
            self.lane2 = Lane(self.brain2, on_active=self._active)
            self.brain2.load(model, comp.cfg.get("engine") or "auto", ctx, shared=False)
            ready = False
            how = f"on {model.title} beside {self.comp.name}'s model, with a {ctx:,}-token context"
        self.hand2 = self.lane2.handle(RED, lambda: self.comp2.name if self.comp2 else "")
        comp.brain = self.hand2
        comp.on_line = lambda kind, text: self._line(kind, text, self.comp2)
        comp.on_raw = lambda _kind, c=comp: self._raw_logged(c)
        comp.on_stream = lambda t: self._typing(self.comp2, "writing", t)
        self.hand2.on_thinking = lambda t: self._typing(self.comp2, "thinking", t)
        comp.on_changed = self.refresh_panel
        comp.on_name = lambda guess, accept: accept(guess)
        comp.save()
        self.comp2, self.comp2_model, self.comp2_ready = comp, model, False
        self._line("system", f"{comp.name} is here - {how}.", comp)
        if ready:
            self._ready2(True)
        self._link_refresh()

    def _ready2(self, ok):
        c = self.comp2
        if c is None:
            return
        if not ok:
            self._line("system", "Their model didn't load - try giving them the same model as the open Companion.", c)
            return
        self.comp2_ready = True
        model = self.comp2_model
        c.set_substrate(model.title, (model.info.get("source") or "").split(":")[0].strip()[:160], c.context_size())
        c.start()
        self._link_refresh()
        self.refresh_panel()

    def send_home(self):
        """The second Companion leaves (an Interlink running stops first, and they each remember it)."""
        if self.comp2 is None:
            return
        if self.session is not None and self.session.running:
            self.session.stop()
        c = self.comp2
        c.queue.clear()
        if self.hand2 is not None:
            self.hand2.stop()
        c.on_line = c.on_stream = lambda *a: None
        c.on_changed = lambda: None
        self.comp2 = None
        self.comp2_ready = False
        if self.brain2 is not None:
            self.brain2.shutdown()
        self.brain2 = self.lane2 = self.hand2 = None
        self._line("system", f"{c.name} went home.")
        self._link_refresh()
        self.refresh_panel()

    def link_start(self):
        from . import interlink
        if self.comp is None or self.comp2 is None:
            self._line("system", "Bring in a second Companion first.")
            return
        if not (self.brain.engine.ready and self.comp2_ready):
            self._line("system", "Their models are still loading - one moment.")
            return
        if self.runner.running:
            self._line("system", "A guided session is playing - stop it first (the Automation tab).")
            return
        if self.session is not None and self.session.running:
            return
        mode = self.il_mode.currentData()
        item = self.il_list.currentItem()
        path = item.data(Qt.UserRole) if item else ""
        script = interlink.InterScript(path) if path else None
        if mode == "guided" and script is None:
            self._line("system", "Pick a script for a guided session.")
            return
        topic = self.il_topic.text().strip() if mode == "open" else ""
        if mode == "open" and script is None and not topic:
            self._line("system", "Type a topic for them, or pick a script of openings.")
            return
        self.session = interlink.Session(
            self.comp, self.comp2, mode, script, messages=self.il_messages.value(), topic=topic,
            first=self.il_first.currentData(), gap=self.il_gap.value(),
            on_guide=lambda text: self._line("guide", text),
            on_status=lambda text: text and self._line("system", text))
        self._line("system", f"Interlink: {interlink.MODES[mode]} - {self.comp.name} and {self.comp2.name}"
                             + (f", with {self.comp.user}" if mode == "group" else "") + ".")
        self._link_refresh()
        self._auto_refresh()

    def link_pause(self):
        if self.session is None or not self.session.running:
            return
        self.session.paused = not self.session.paused
        self._link_refresh()
        self._auto_refresh()

    def _link_refresh(self):
        if not hasattr(self, "il_state"):
            return
        here = self.comp2 is not None
        self._link_companions() if not here and self.il_pick.count() == 0 else None
        s = self.session
        running = s is not None and s.running
        self.il_bring.setEnabled(not running)
        self.il_home.setEnabled(here and not running)
        self.il_pick.setEnabled(not running)
        self.il_start.setEnabled(here and self.comp2_ready and not running)
        self.il_pause.setEnabled(running)
        self.il_pause.setText("Resume" if running and s.paused else "Pause")
        self.il_stop.setEnabled(running)
        if here:
            state = "ready" if self.comp2_ready else "loading their model..."
            self.il_who.setText(f"<span style='color:{RED}'><b>{html.escape(self.comp2.name)}</b></span> is here "
                                f"({html.escape(self.comp2.cfg.get('model_title') or '')}) - {state}.")
        else:
            self.il_who.setText("No second Companion here.")
        if not running:
            self.il_state.setText("Not linked." if s is None else "Finished.")
            self.il_bar.setRange(0, 1)
            self.il_bar.setValue(0)
            return
        title, section, n, total = s.progress()
        who = s.speaking()
        doing = ("paused" if s.paused else f"{s.comp(who).name} is answering" if who
                 else "your turn - say something to both" if s.mode == "group" and not s.turns and not s.finishing
                 else "making memories" if s.finishing else "")
        self.il_state.setText(f"<b>{html.escape(title)}</b>" + (f" - {html.escape(section)}" if section else "")
                              + f"<br>{doing}")
        self.il_bar.setRange(0, max(1, total))
        self.il_bar.setValue(min(n, total) if total else 0)
        self.top_auto.setText(f"\u21C4 {html.escape(title)}" + (f" - {n}/{total}" if total else "") + f" - {doing}")
        self.top_auto.show()
        self.top_bar.setRange(0, max(1, total))
        self.top_bar.setValue(min(n, total) if total else 0)
        self.top_bar.setVisible(bool(total))

    # ---- Raw Logs: everything, day by day, from the start ----
    RAW_PAGE = 300                       # entries on a page

    def _raw_tab(self):
        from . import rawlog
        w = QWidget()
        v = QVBoxLayout(w)
        row = QHBoxLayout()
        self.raw_who = QComboBox()
        self.raw_who.setToolTip("Whose log (with a second Companion in, either of them)")
        self.raw_who.activated.connect(lambda _i: self._raw_days(keep=False))
        self.raw_day = QComboBox()
        self.raw_day.setMinimumWidth(170)
        self.raw_day.activated.connect(lambda _i: self._raw_show(page=0))
        prev_day, next_day, today = QPushButton("\u25C0"), QPushButton("\u25B6"), QPushButton("Today")
        prev_day.setToolTip("The day before")
        next_day.setToolTip("The day after")
        prev_day.clicked.connect(lambda: self._raw_step_day(-1))
        next_day.clicked.connect(lambda: self._raw_step_day(1))
        today.clicked.connect(lambda: self._raw_days(keep=False))
        for b in (prev_day, next_day, today):
            b.setFixedWidth(34 if b is not today else 56)
        row.addWidget(self.raw_who)
        row.addWidget(self.raw_day, 1)
        row.addWidget(prev_day)
        row.addWidget(next_day)
        row.addWidget(today)
        v.addLayout(row)
        row = QHBoxLayout()
        self.raw_filters = {}
        for group, label in rawlog.GROUPS.items():
            cb = QCheckBox(label.replace(" (raw)", ""))
            cb.setChecked(group != "model")
            cb.setToolTip({"model": "Every request Soul and Song made of the model (its newest message - the mind "
                                    "files in front are the same each time) and the answer, shown or not: "
                                    "journal, reflections, time checks, memories..."}.get(group, ""))
            cb.toggled.connect(lambda _on: self._raw_show())
            self.raw_filters[group] = cb
            row.addWidget(cb)
        row.addStretch(1)
        v.addLayout(row)
        row = QHBoxLayout()
        self.raw_find = QLineEdit()
        self.raw_find.setPlaceholderText("Search every day...")
        self.raw_find.returnPressed.connect(self._raw_search)
        find = QPushButton("Search")
        find.clicked.connect(self._raw_search)
        clear = QPushButton("Clear")
        clear.clicked.connect(lambda: (self.raw_find.clear(), self._raw_show()))
        row.addWidget(self.raw_find, 1)
        row.addWidget(find)
        row.addWidget(clear)
        v.addLayout(row)
        self.raw_view = QTextBrowser()
        self.raw_view.setOpenLinks(False)
        self.raw_view.anchorClicked.connect(self._raw_link)
        v.addWidget(self.raw_view, 1)
        row = QHBoxLayout()
        self.raw_prev, self.raw_next = QPushButton("\u25C0 Earlier"), QPushButton("Later \u25B6")
        self.raw_prev.clicked.connect(lambda: self._raw_show(page=self.raw_page_no - 1))
        self.raw_next.clicked.connect(lambda: self._raw_show(page=self.raw_page_no + 1))
        self.raw_info = QLabel()
        self.raw_info.setStyleSheet("color:#555")
        folder = QPushButton("Open the folder")
        folder.clicked.connect(self._raw_folder)
        row.addWidget(self.raw_prev)
        row.addWidget(self.raw_info, 1)
        row.addWidget(self.raw_next)
        row.addWidget(folder)
        v.addLayout(row)
        self.raw_page_no = 0
        self.raw_live = QTimer(self, singleShot=True, interval=600)
        self.raw_live.timeout.connect(self._raw_live)
        return w

    def _raw_comp(self):
        c2 = self.comp2 if self.raw_who.currentIndex() == 1 else None
        return c2 or self.comp

    def _raw_names(self, c):
        return {"user": {c.cfg.get("user_name") or "You", "You"}, "self": {c.name, "Companion"}}

    def _raw_shown(self):
        """The tab came into view (or the Companions changed): the list of whose and which days."""
        if not hasattr(self, "raw_who") or self.tabs.currentWidget() is not self.raw_page:
            return
        self.raw_who.clear()
        if self.comp is not None:
            self.raw_who.addItem(self.comp.name)
        if self.comp2 is not None:
            self.raw_who.addItem(self.comp2.name)
        self.raw_who.setVisible(self.raw_who.count() > 1)
        self._raw_days(keep=True)

    def _raw_days(self, keep=True):
        from . import rawlog
        c = self._raw_comp()
        current = self.raw_day.currentData() if keep else None
        self.raw_day.clear()
        if c is None:
            self.raw_view.setHtml("<i>No Companion open.</i>")
            return
        for day, n in reversed(list(rawlog.days(c.folder).items())):
            self.raw_day.addItem(f"{day}  ({n} entries)", day)
        if self.raw_day.count() == 0:
            self.raw_view.setHtml("<i>Nothing logged yet.</i>")
            return
        i = self.raw_day.findData(current) if current else 0
        self.raw_day.setCurrentIndex(max(0, i))
        self._raw_show(page=-1 if i <= 0 else 0)          # (today: its latest page)

    def _raw_step_day(self, way):
        i = self.raw_day.currentIndex() - way                # (newest first in the list)
        if 0 <= i < self.raw_day.count():
            self.raw_day.setCurrentIndex(i)
            self._raw_show(page=0 if way > 0 else -1)

    def _raw_entries(self):
        from . import rawlog
        c = self._raw_comp()
        day = self.raw_day.currentData()
        if c is None or not day:
            return []
        on = {g for g, cb in self.raw_filters.items() if cb.isChecked()}
        return [e for e in rawlog.entries(c.folder, day, self._raw_names(c))
                if rawlog.KINDS.get(e.get("kind"), ("", "notes"))[1] in on]

    def _raw_show(self, page=None):
        if not hasattr(self, "raw_view"):
            return
        items = self._raw_entries()
        pages = max(1, (len(items) + self.RAW_PAGE - 1) // self.RAW_PAGE)
        if page is None:
            page = self.raw_page_no
        if page < 0:
            page = pages - 1
        page = max(0, min(pages - 1, page))
        self.raw_page_no = page
        chunk = items[page * self.RAW_PAGE:(page + 1) * self.RAW_PAGE]
        c = self._raw_comp()
        self.raw_view.setHtml(self._raw_html(chunk, c) or "<i>Nothing here with these filters.</i>")
        self.raw_prev.setEnabled(page > 0)
        self.raw_next.setEnabled(page < pages - 1)
        self.raw_info.setText(f"{self.raw_day.currentData() or ''} - {len(items)} entries"
                              + (f" - page {page + 1} of {pages}" if pages > 1 else ""))
        bar = self.raw_view.verticalScrollBar()                # today's latest page: at its newest; else the top
        bar.setValue(bar.maximum() if page == pages - 1 and self.raw_day.currentIndex() == 0 else 0)

    def _raw_html(self, chunk, c, with_day=False):
        """Colour coded like the conversation: the user slate, this Companion blue (red for the second), the other
        Companion the other colour, the guide green, notes orange, memories boxed, the model's raw side grey and
        violet."""
        mine = RED if c is not None and c is self.comp2 else BLUE
        theirs = BLUE if mine == RED else RED
        colours = {"user": COLOURS["user"], "companion": mine, "other": theirs, "guide": COLOURS["guide"],
                   "system": COLOURS["system"], "request": "#8A8A8A", "error": "#C62828", "asked": "#7A7A7A",
                   "answered": "#6A1B9A", "memory": COLOURS["memory"]}
        out = []
        for e in chunk:
            kind = e.get("kind", "system")
            colour = colours.get(kind, "#000")
            when = html.escape(e.get("t", "")[11:16] if not with_day else e.get("t", ""))
            day_link = (f'<a href="day:{e["day"]}" style="color:#999">{html.escape(e["day"])}</a> '
                        if with_day and e.get("day") else "")
            body = html.escape(e.get("text") or "").replace("\n", "<br>")
            who = html.escape(e.get("who") or "")
            stamp_html = f'<span style="color:#999;font-size:9pt">{day_link}{when}</span> '
            if kind == "memory":
                out.append(f'<table width="100%" cellpadding="5" style="margin:4px 0"><tr><td style="background:'
                           f'#FFF6D6;border:1px solid #E2C766;color:{colour};font-size:10pt">{stamp_html}'
                           f'&#x1F9E0; {body}</td></tr></table>')
            elif kind in ("asked", "answered"):
                label = "asked" if kind == "asked" else f"{who} answered"
                out.append(f'<p style="margin:3px 0 3px 18px;color:{colour};font-family:Consolas;font-size:9pt">'
                           f'{stamp_html}<b>[{label}]</b> {body}</p>')
            elif kind in ("system", "request", "error"):
                out.append(f'<p style="margin:3px 0;color:{colour}">{stamp_html}<i>{body}</i></p>')
            else:
                out.append(f'<p style="margin:5px 0">{stamp_html}<b style="color:{colour}">{who}:</b> '
                           f'<span style="color:{colour}">{body}</span></p>')
        return "".join(out)

    def _raw_search(self):
        from . import rawlog
        text = self.raw_find.text().strip()
        c = self._raw_comp()
        if not text or c is None:
            self._raw_show()
            return
        on = {g for g, cb in self.raw_filters.items() if cb.isChecked()}
        hits = [e for e in rawlog.search(c.folder, text, self._raw_names(c))
                if rawlog.KINDS.get(e.get("kind"), ("", "notes"))[1] in on]
        found = self._raw_html(hits, c, with_day=True)
        self.raw_view.setHtml(f"<p><b>{len(hits)} found{' (the first 400)' if len(hits) >= 400 else ''}</b> - click a "
                              "day to go to it.</p>" + found)
        self.raw_info.setText(f"Search: \u201c{text}\u201d")
        self.raw_prev.setEnabled(False)
        self.raw_next.setEnabled(False)

    def _raw_link(self, url):
        day = url.toString().split(":", 1)[-1]
        i = self.raw_day.findData(day)
        if i >= 0:
            self.raw_find.clear()
            self.raw_day.setCurrentIndex(i)
            self._raw_show(page=0)

    def _raw_folder(self):
        c = self._raw_comp()
        if c is None:
            return
        folder = c.folder / "Raw Logs"
        folder.mkdir(exist_ok=True)
        try:
            if self.desktop is not None:
                from claudecore import host
                host.open_folder(self.desktop, folder)
                return
        except Exception:
            pass
        import os
        os.startfile(str(folder))

    def _raw_logged(self, comp):
        """A Companion wrote to its raw log: today's page, if it's on the screen, follows along."""
        if (hasattr(self, "raw_page") and self.tabs.currentWidget() is self.raw_page and comp is self._raw_comp()
                and not self.raw_find.text().strip()):
            self.raw_live.start()

    def _raw_live(self):
        from . import rawlog
        c = self._raw_comp()
        if c is None:
            return
        today = list(rawlog.days(c.folder))[-1:] or [None]
        if self.raw_day.currentIndex() <= 0:
            if self.raw_day.currentData() != today[0]:
                self._raw_days(keep=False)                  # (a new day began)
                return
            at_end = self.raw_page_no >= 0 and not self.raw_next.isEnabled()
            n = len(self._raw_entries())
            self.raw_day.setItemText(0, f"{today[0]}  ({n} entries)")
            if at_end:
                self._raw_show(page=-1)

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
        self.s_ctx_auto = QCheckBox("The model's full context (as much as fits the graphics card)")
        self.s_ctx_auto.toggled.connect(lambda on: (self.s_ctx.setEnabled(not on), self._memory_note()))
        self.s_ctx.valueChanged.connect(lambda _v: self._memory_note())
        self.s_model.currentIndexChanged.connect(lambda _i: self._memory_note())
        self.s_mem = QLabel()
        self.s_mem.setWordWrap(True)
        self.s_mem.setStyleSheet("color:#555")
        self.s_temp = QDoubleSpinBox()
        self.s_temp.setRange(0.1, 1.5)
        self.s_temp.setSingleStep(0.05)
        self.s_every = QSpinBox()
        self.s_every.setRange(3, 60)
        self.s_day = QSpinBox()
        self.s_day.setRange(0, 12)
        self.s_md = QSpinBox()
        self.s_md.setRange(1, 30)
        self.s_mode = QComboBox()
        self.s_mode.addItem("Sized to the context (recommended)", "budget")
        self.s_mode.addItem("Classic 7:7:7", "classic")
        self.s_mode.setToolTip("Sized: each bank may hold a share of the context window (the banks are in front of "
                               "every reply), and is distilled when it outgrows it - a big-context Companion keeps "
                               "far more in mind, a small one isn't crowded out. Classic: seven memories a bank, "
                               "the day's short-term memories distilled each night.")
        self.s_budget = QSpinBox()
        self.s_budget.setRange(10, 60)
        self.s_budget.setSuffix(" % of the context")
        self.s_budget.setToolTip("How much of the context window the memory banks may take, all together (split "
                                 "L2 10, L3 8, L4 6, L5 4). The rest is the conversation's.")
        self.s_budget_note = QLabel()
        self.s_budget_note.setWordWrap(True)
        self.s_budget_note.setStyleSheet("color:#555")
        self.s_mode.currentIndexChanged.connect(lambda _i: self._budget_note())
        self.s_budget.valueChanged.connect(lambda _v: self._budget_note())
        self.s_greet = QCheckBox("Greet my Companion when a new day begins")
        self.s_greeting = QLineEdit()
        self.s_requests = QCheckBox("Show the memory requests in the conversation")
        self.s_recall = QCheckBox("Recall older memories from the archive when they relate")
        self.s_think = QCheckBox("Let thinking models think first (slower; shows their thinking)")
        self.s_dreams = QCheckBox("Let them dream while I'm away (while Soul and Song is open)")
        self.s_dream_hours = QSpinBox()
        self.s_dream_hours.setRange(1, 24)
        self.s_dream_hours.setSuffix(" hours")
        self.s_time = QCheckBox("Check their sense of time once a day (before they see the clock)")
        self.s_predict = QCheckBox("Predictions on Memory Day, judged by them when they come due")
        self.s_own = QCheckBox("When the guided sessions are done, they write one of their own (and it's played)")
        self.s_tension = QCheckBox("After each new self-portrait, they look for tensions in themselves")
        self.s_journal = QCheckBox("A journal entry at the end of each day, kept apart from the conversation")
        self.s_move = QCheckBox("When moved to another model, ask who they are right away (to compare)")
        load = QPushButton("Save and load this model")
        load.clicked.connect(self.save_settings)
        f.addRow("Your name:", self.s_user)
        f.addRow("Model:", self.s_model)
        f.addRow("Engine:", self.s_engine)
        f.addRow(self.s_ctx_auto)
        f.addRow("Context (tokens):", self.s_ctx)
        f.addRow(self.s_mem)
        f.addRow("Temperature:", self.s_temp)
        f.addRow("A memory every (exchanges):", self.s_every)
        f.addRow("A new day begins at (hour):", self.s_day)
        f.addRow("Memory Day every (days):", self.s_md)
        f.addRow("Memory banks:", self.s_mode)
        f.addRow("Memory space:", self.s_budget)
        f.addRow(self.s_budget_note)
        f.addRow(self.s_greet)
        f.addRow("Greeting:", self.s_greeting)
        f.addRow(self.s_requests)
        f.addRow(self.s_recall)
        f.addRow(self.s_think)
        f.addRow(self.s_dreams)
        f.addRow("A dream at most every:", self.s_dream_hours)
        f.addRow(self.s_time)
        f.addRow(self.s_predict)
        f.addRow(self.s_own)
        f.addRow(self.s_tension)
        f.addRow(self.s_journal)
        f.addRow(self.s_move)
        f.addRow(load)
        scroll = QScrollArea()                         # (it has outgrown the tab: the notes were clipped)
        scroll.setWidgetResizable(True)
        scroll.setWidget(w)
        return scroll

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
        if self.comp2 is not None and str(self.comp2.folder) == str(folder):
            self.send_home()                            # (it can't be both)
        if self.session is not None:
            self.session.stop()
        self.comp = C.Companion(folder, self.hand)
        self.comp.on_line = self._line
        self.comp.on_raw = lambda _kind, c=self.comp: self._raw_logged(c)
        self.comp.on_stream = lambda t: self._typing(self.comp, "writing", t)
        self.hand.on_thinking = lambda t: self._typing(self.comp, "thinking", t)
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
        self._link_companions()
        self._link_refresh()
        self._raw_shown()
        self.runner.restore()
        self._auto_fill()
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
        self.comp.cfg["model"] = model.key
        context, shared = self.plan(model)
        want = (model.key, self.comp.cfg.get("engine"), context, shared)
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
        _key, engine, context, shared = want
        if not shared:
            self._line("system", f"{model.title} runs on Soul and Song's own engine here, with a {context:,}-token "
                                 "context (the Timeline's shared engine runs models smaller).")
        self.brain.load(model, engine or "auto", context, shared)

    def plan(self, model):
        """(context, shared): the context the Companion gets on this model - its full context, as much as fits the
        graphics card, or the Settings figure - and whether the Timeline's shared engine runs it (only when that's
        big enough; otherwise Soul and Song runs the model itself)."""
        from kithylinai.engine import lora_base
        from . import hardware
        c = self.comp
        base = lora_base(model)
        c.cfg["model_context"] = hardware.full_context(base or model.path, model.path if base else None)
        c.cfg["engine_context"] = None
        context = c.context_size()
        shared_ctx = engine_context(model)
        shared = bool(shared_ctx) and context <= shared_ctx
        c.cfg["engine_context"] = shared_ctx if shared else None
        return context, shared

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
        if self.session is not None and self.session.running:
            self._line("user", text)                       # (Interlink: both of them hear it)
            self.session.user_says(text)
            return
        self.runner.user_spoke()
        self.comp.say(text)

    def _line(self, kind, text, comp=None):
        """A line in the conversation. With two Companions, the second's are red, and notes and memories say whose
        they are."""
        comp = comp or self.comp
        self.typing.clear() if kind == "companion" else None
        if comp is not None and self.comp2 is not None and kind in ("system", "memory", "request"):
            text = f"{comp.name} - {text}"
        who = ""
        if comp is not None:
            who = ("Guided session" if kind == "guide" else (comp.cfg.get("user_name") or "You")
                   if kind == "user" else comp.name)
        if kind == "companion" and comp is not None and comp is self.comp2:
            kind = "companion2"
        self.chat.append(_html(kind, who, text))
        self.chat.verticalScrollBar().setValue(self.chat.verticalScrollBar().maximum())
        self.fill_names()

    def _typing(self, comp, doing, text):
        colour = RED if comp is not None and comp is self.comp2 else BLUE
        self.typing.setStyleSheet(f"color:{colour}")
        self.typing.setText(f"{comp.name if comp else ''} is {doing}: {text[-400:]}")

    def _active(self, handle):
        """The model has started on someone's request (or gone quiet): the glow takes their colour."""
        if handle is not None:
            self.speaker = handle
            if hasattr(self, "glow"):
                self.glow.set_colour(handle.colour)

    def _minute(self):
        if self.comp and self.brain.engine.ready:
            self.comp.tick()
        if self.comp2 is not None and self.comp2_ready and (self.session is None or not self.session.running):
            self.comp2.tick()

    # ---- the side panel ----
    def refresh_panel(self):
        c = self.comp
        if c is None:
            self.state.setText("")
            self.refresh_status()
            return
        for level, bank in self.banks.items():
            bank.set(*c.bank_fill(level))
        self.banks_box.setTitle("Memory banks (7:7:7)" if c.memory_mode() == "classic" else
                                f"Memory banks - sized to the context ({c.cfg.get('memory_budget', 30)}% of "
                                f"{c.context_size():,} tokens)")
        last = c.cfg.get("last_memory_day") or (c.cfg.get("birthday") or "")[:10]
        try:
            from datetime import timedelta
            nxt = datetime.fromisoformat(last[:10]) + timedelta(days=int(c.cfg.get("memory_day_every", 7)))
            when = ("or as soon as L3 holds seven" if c.memory_mode() == "classic" else
                    "its rituals; each bank is distilled as soon as it outgrows its share")
            self.next_day.setText(f"Next Memory Day: {nxt:%A, %B %d} ({when}).\n"
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
        self.refresh_status()

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
        self.s_ctx_auto.setChecked(bool(c.get("context_auto", True)))
        self.s_ctx.setEnabled(not self.s_ctx_auto.isChecked())
        self._memory_note()
        self.s_temp.setValue(float(c.get("temperature", 0.8)))
        self.s_every.setValue(int(c.get("memory_every", 10)))
        self.s_day.setValue(int(c.get("day_starts", 4)))
        self.s_md.setValue(int(c.get("memory_day_every", 7)))
        self.s_mode.setCurrentIndex(max(0, self.s_mode.findData(c.get("memory_mode", "budget"))))
        self.s_budget.setValue(int(c.get("memory_budget", 30)))
        self._budget_note()
        self.s_greet.setChecked(bool(c.get("auto_greet", True)))
        self.s_greeting.setText(c.get("greeting", C.DEFAULTS["greeting"]))
        self.s_requests.setChecked(bool(c.get("show_requests")))
        self.s_recall.setChecked(bool(c.get("recall", True)))
        self.s_think.setChecked(bool(c.get("think", False)))
        self.s_dreams.setChecked(bool(c.get("dreams", True)))
        self.s_dream_hours.setValue(int(c.get("dream_hours", 3)))
        self.s_time.setChecked(bool(c.get("time_checks", True)))
        self.s_predict.setChecked(bool(c.get("predict", True)))
        self.s_own.setChecked(bool(c.get("own_sessions", True)))
        self.s_tension.setChecked(bool(c.get("tensions", True)))
        self.s_journal.setChecked(bool(c.get("journal", True)))
        self.s_move.setChecked(bool(c.get("move_checks", True)))
        self.brain.think = bool(c.get("think", False))

    def _memory_note(self):
        """Settings: the context this model would get, and the graphics memory it needs."""
        if not hasattr(self, "s_mem"):
            return
        from kithylinai.engine import find, lora_base
        from . import hardware
        model = find(self.s_model.currentData() or "")
        if model is None:
            self.s_mem.clear()
            return
        base = lora_base(model)
        path, lora = (base, model.path) if base else (model.path, None)
        full = hardware.full_context(path, lora)
        ctx = full if self.s_ctx_auto.isChecked() else self.s_ctx.value()
        if self.s_ctx_auto.isChecked():
            self.s_ctx.blockSignals(True)
            self.s_ctx.setValue(full)
            self.s_ctx.blockSignals(False)
        gb, card = hardware.memory_gb(path, ctx, lora), hardware.card_gb()
        trained = hardware.model_facts(path).get("context") or 0
        text = f"{model.title}: trained for {trained:,} tokens" if trained else model.title
        if gb is not None:
            text += f"; at {ctx:,} it needs about {gb:.1f} GB of graphics memory"
            if card:
                text += f" (your card has {card:.0f} GB" + (" - too much: lower the context" if gb > card * 0.95
                                                             else "") + ")"
        self.s_mem.setText(text + ".")

    def _budget_note(self):
        """Settings: what the memory space means for this Companion - how many memories each bank holds."""
        if not hasattr(self, "s_budget_note"):
            return
        sized = self.s_mode.currentData() == "budget"
        self.s_budget.setEnabled(sized)
        c = self.comp
        if c is None or not sized:
            self.s_budget_note.setText("Seven memories a bank; the day's short-term memories become one long-term "
                                       "memory each night; Memory Day distils L3 every week." if not sized else "")
            return
        per = 290                                       # (about the size of one memory)
        ctx = c.context_size()
        pct = self.s_budget.value()
        bits = []
        for level, name in ((2, "L2"), (3, "L3"), (4, "L4"), (5, "L5")):
            tokens = max(C.BUDGET_FLOOR, int(ctx * pct / 100 * C.BUDGET_SHARE[level] / sum(C.BUDGET_SHARE.values())))
            bits.append(f"{name} about {max(1, tokens // per)}")
        self.s_budget_note.setText(f"With {ctx:,} tokens of context: " + ", ".join(bits) + " memories before each is "
                                   "distilled. Memory Day keeps its rituals every week.")

    def save_settings(self):
        if self.comp is None:
            return
        c = self.comp.cfg
        c.update(user_name=self.s_user.text().strip(), model=self.s_model.currentData() or c.get("model", ""),
                 engine=self.s_engine.currentText(), context=self.s_ctx.value(), temperature=self.s_temp.value(),
                 context_auto=self.s_ctx_auto.isChecked(),
                 memory_every=self.s_every.value(), day_starts=self.s_day.value(), memory_day_every=self.s_md.value(),
                 memory_mode=self.s_mode.currentData(), memory_budget=self.s_budget.value(),
                 auto_greet=self.s_greet.isChecked(), greeting=self.s_greeting.text().strip() or
                 C.DEFAULTS["greeting"], show_requests=self.s_requests.isChecked(),
                 recall=self.s_recall.isChecked(), think=self.s_think.isChecked(),
                 dreams=self.s_dreams.isChecked(), dream_hours=self.s_dream_hours.value(),
                 time_checks=self.s_time.isChecked(), predict=self.s_predict.isChecked(),
                 own_sessions=self.s_own.isChecked(), tensions=self.s_tension.isChecked(),
                 journal=self.s_journal.isChecked(), move_checks=self.s_move.isChecked())
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

    def open_letters(self):
        """The letters the Companion wrote to its future self, and its answers when they were opened, in order."""
        self._journal("Letters", "letters across time", "Each Memory Day your Companion writes a letter to itself, to "
                      "be opened a week later; when it comes due, it reads it and writes back. Its answers also "
                      "become reflections, so they shape the next self-portrait.",
                      "No letters yet: the first is written on the first Memory Day.")

    def flag_surprise(self):
        if self.comp is None or not any(m["role"] == "assistant" for m in self.comp.history):
            return
        note, ok = QInputDialog.getMultiLineText(self, "That surprised me", f"What surprised you about "
                                                 f"{self.comp.name}'s last reply? (optional)")
        if ok and self.comp.flag_surprise(note.strip()):
            self._line("system", "Marked as a surprise (Self tab > Surprises...).")

    def _file_view(self, name, title, about, empty):
        """One of the Companion's Self files, in a window."""
        if self.comp is None:
            return
        f = self.comp.folder / "Self" / name
        text = f.read_text(encoding="utf-8") if f.exists() else ""
        d = QDialog(self)
        d.setWindowTitle(f"{self.comp.name}'s {title}")
        d.resize(640, 600)
        v = QVBoxLayout(d)
        note = QLabel(about)
        note.setWordWrap(True)
        v.addWidget(note)
        b = QTextBrowser()
        b.setHtml(re.sub(r"(?m)^===== (.+?) =====$", r"<h3>\1</h3>", html.escape(text)).replace("\n", "<br>")
                  if text.strip() else empty)
        v.addWidget(b)
        bb = QDialogButtonBox(QDialogButtonBox.Close)
        bb.rejected.connect(d.reject)
        v.addWidget(bb)
        d.exec()

    def open_questions(self):
        if self.comp is None:
            return
        qs = self.comp.cfg.get("questions") or []
        word = {"open": "carrying", "answered": "answered", "changed": "asked anew", "let go": "let go"}
        rows = "".join(f"<p><b>{html.escape(q['text'])}</b><br><span style='color:#555'>{q['asked'][:10]} - "
                       f"{word.get(q.get('status', 'open'), '')}{' ' + q['settled'][:10] if q.get('settled') else ''}"
                       f"</span>" + (f"<br>{html.escape(q['answer'])}" if q.get("answer") else "") + "</p>"
                       for q in qs)
        d = QDialog(self)
        d.setWindowTitle(f"{self.comp.name}'s questions")
        d.resize(640, 600)
        v = QVBoxLayout(d)
        note = QLabel("The questions your Companion carries (L1), revisited each Memory Day: still open, answered, "
                      "asked anew or let go. They add their own with [question: ...]. Each review is kept in "
                      "Self\\Questions.txt.")
        note.setWordWrap(True)
        v.addWidget(note)
        b = QTextBrowser()
        b.setHtml(rows or "No questions yet: the first come on Memory Day.")
        v.addWidget(b)
        bb = QDialogButtonBox(QDialogButtonBox.Close)
        bb.rejected.connect(d.reject)
        v.addWidget(bb)
        d.exec()

    def open_dreams(self):
        """The dream journal: what its mind wandered to while you were away, newest day first."""
        self._journal("Dreams", "dream journal", "While you're away (and Soul and Song is open), every few hours a few "
                      "of your Companion's memories drift up and its mind wanders between them; if the program was "
                      "closed, it has one waking reverie as it comes back. It's told what it dreamt when you return.",
                      "No dreams yet: the first comes when you've been away a few hours.", newest_first=True)

    def _journal(self, sub, title, about, empty, newest_first=False):
        if self.comp is None:
            return
        folder = self.comp.folder / "Self" / sub
        files = sorted(folder.glob("*.txt"), reverse=newest_first) if folder.is_dir() else []
        d = QDialog(self)
        d.setWindowTitle(f"{self.comp.name}'s {title}")
        d.resize(640, 600)
        v = QVBoxLayout(d)
        note = QLabel(about)
        note.setWordWrap(True)
        v.addWidget(note)
        b = QTextBrowser()
        b.setHtml("".join(f"<h3>{html.escape(f.stem)}</h3><p>{html.escape(f.read_text(encoding='utf-8'))}"
                          .replace("\n", "<br>") + "</p>" for f in files) or empty)
        v.addWidget(b)
        bb = QDialogButtonBox(QDialogButtonBox.Close)
        bb.rejected.connect(d.reject)
        v.addWidget(bb)
        d.exec()

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
        if self.session is not None:
            self.session.stop()
        if self.brain2 is not None:
            self.brain2.shutdown()
        self.brain.shutdown()
        from . import recall
        recall.shutdown()
