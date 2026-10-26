"""The autopilot panel's Day, Threads and Interests tabs: the finer control over Kithylin's day (claudecore.autopilot.day).

Day: the week on the real clock, painted in half-hour cells (free time, work, lunch, asleep, out); what each block
means for him - the scene in his prompt, the away message, how quickly he answers, which legs suit it; today's
override and day off; and Right now - what he's doing, what's happened, and what he has told people, all editable.

Threads: the stories he brings up - life arcs with a beat a day, daily openers, recurring bits, roleplay seeds - with
who has heard each one; the suggestions mined from his Telegram logs, used once ticked; and his style card.

Interests: his buddies in three columns - love interests, close acquaintances, friends - which set how quickly he
answers each, how long he chats, who he IMs first and who he roleplays with."""
import os
import subprocess
import sys

from PySide6.QtCore import QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (QAbstractItemView, QButtonGroup, QCheckBox, QComboBox, QFormLayout, QGroupBox,
                               QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListView, QListWidget, QListWidgetItem,
                               QPlainTextEdit, QPushButton, QRadioButton, QScrollArea, QSplitter, QTableWidget,
                               QTableWidgetItem, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

from claudecore.autopilot import day as dayc

BLOCK_ORDER = ["free", "work", "lunch", "sleep", "out"]
WEIGHTS = [("Never", 0.0), ("Less", 0.4), ("Normal", 1.0), ("More", 1.6)]
PACES = [("Quickly", 0.7), ("Normally", 1.0), ("A bit slower", 1.5), ("Slowly", 2.2), ("Very slowly", 3.5)]


def _nearest(options, value):
    return min(range(len(options)), key=lambda i: abs(options[i][1] - float(value)))


# ---- the week -----------------------------------------------------------------------------------------------------
class ScheduleGrid(QWidget):
    """Seven rows of 48 half-hour cells. Click or drag to paint with the chosen block; a red line marks now."""
    changed = Signal()
    LEFT, TOP = 36, 16

    def __init__(self, day):
        super().__init__()
        self.day = day
        self.brush = "w"
        self.setMinimumHeight(7 * 17 + self.TOP + 2)
        self.setMinimumWidth(48 * 8 + self.LEFT)
        self.setToolTip("Click or drag to paint the week with the block chosen below")
        self._painting = False

    def _geom(self):
        cw = (self.width() - self.LEFT - 1) / dayc.CELLS
        ch = (self.height() - self.TOP - 1) / 7
        return cw, ch

    def _cell(self, pos):
        cw, ch = self._geom()
        col = int((pos.x() - self.LEFT) / cw)
        row = int((pos.y() - self.TOP) / ch)
        if 0 <= col < dayc.CELLS and 0 <= row < 7:
            return row, col
        return None

    def _paint_at(self, pos):
        rc = self._cell(pos)
        if rc is None:
            return
        row, col = rc
        key = dayc.DAYS[row]
        cells = self.day.data["schedule"][key]
        if cells[col] != self.brush:
            self.day.data["schedule"][key] = cells[:col] + self.brush + cells[col + 1:]
            self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._painting = True
            self._paint_at(e.position().toPoint())

    def mouseMoveEvent(self, e):
        if self._painting:
            self._paint_at(e.position().toPoint())

    def mouseReleaseEvent(self, e):
        if self._painting:
            self._painting = False
            self.day.save()
            self.changed.emit()

    def paintEvent(self, _e):
        p = QPainter(self)
        cw, ch = self._geom()
        blocks = self.day.data["blocks"]
        p.setPen(self.palette().text().color())
        f = p.font()
        f.setPointSizeF(max(6.5, f.pointSizeF() - 1.5))
        p.setFont(f)
        for h in range(0, 24, 3):
            x = self.LEFT + h * 2 * cw
            p.drawText(QRectF(x - 2, 0, 40, self.TOP), Qt.AlignLeft | Qt.AlignVCenter,
                       f"{h % 12 or 12}{'a' if h < 12 else 'p'}")
        for r, d in enumerate(dayc.DAYS):
            y = self.TOP + r * ch
            p.setPen(self.palette().text().color())
            p.drawText(QRectF(0, y, self.LEFT - 4, ch), Qt.AlignRight | Qt.AlignVCenter, d.title())
            cells = self.day.data["schedule"][d]
            for c in range(dayc.CELLS):
                key = dayc.CODES.get(cells[c], "free")
                p.fillRect(QRectF(self.LEFT + c * cw, y, cw + 0.5, ch), QColor(blocks[key].get("colour", "#DDD")))
        p.setPen(QPen(QColor(0, 0, 0, 40), 1))
        for c in range(0, dayc.CELLS + 1, 2):
            x = self.LEFT + c * cw
            p.drawLine(int(x), self.TOP, int(x), int(self.TOP + 7 * ch))
        for r in range(8):
            y = self.TOP + r * ch
            p.drawLine(self.LEFT, int(y), int(self.LEFT + dayc.CELLS * cw), int(y))
        now = self.day.now()
        x = self.LEFT + (now.hour * 60 + now.minute) / 30 * cw
        y = self.TOP + now.weekday() * ch
        p.setPen(QPen(QColor("#D02020"), 2))
        p.drawLine(int(x), int(y), int(x), int(y + ch))
        p.end()


class DayTab(QScrollArea):
    """The week, the blocks, today, and right now."""

    def __init__(self, day, legs, pilot):
        super().__init__()
        self.day, self.legs, self.pilot = day, legs, pilot
        self.setWidgetResizable(True)
        page = QWidget()
        col = QVBoxLayout(page)
        top = QHBoxLayout()
        self.follow = QCheckBox("Follow his schedule (on the real clock)")
        self.follow.setChecked(bool(day.data.get("follow_schedule", True)))
        self.follow.toggled.connect(self._set_follow)
        top.addWidget(self.follow)
        top.addStretch(1)
        self.now_label = QLabel()
        top.addWidget(self.now_label)
        col.addLayout(top)

        self.grid = ScheduleGrid(day)
        self.grid.changed.connect(self._refresh_now)
        col.addWidget(self.grid)
        brushes = QHBoxLayout()
        brushes.addWidget(QLabel("Paint:"))
        self.brush_group = QButtonGroup(self)
        for key in BLOCK_ORDER:
            rb = QRadioButton(day.data["blocks"][key]["title"])
            rb.setStyleSheet(f"QRadioButton {{ background: {day.data['blocks'][key]['colour']}; padding: 1px 5px; "
                             "border-radius: 3px; }")
            rb.setChecked(key == "work")
            rb.toggled.connect(lambda on, k=key: on and setattr(self.grid, "brush", dayc.CODE_OF[k]))
            self.brush_group.addButton(rb)
            brushes.addWidget(rb)
        brushes.addStretch(1)
        reset = QPushButton("Default week")
        reset.setToolTip("The standard week: Mon-Fri work 9:30 am - 6:30 pm, lunch 2:30 - 3:30 pm; asleep 11 pm - 7 am")
        reset.clicked.connect(self._reset_week)
        brushes.addWidget(reset)
        col.addLayout(brushes)

        # the blocks
        blocks = QGroupBox("What each block means for him")
        bl = QHBoxLayout(blocks)
        form = QFormLayout()
        self.block_pick = QComboBox()
        for key in BLOCK_ORDER:
            self.block_pick.addItem(day.data["blocks"][key]["title"], key)
        self.block_pick.setCurrentIndex(max(0, self.block_pick.findData(day.block())))    # the one he's in now
        self.block_pick.currentIndexChanged.connect(self._show_block)
        form.addRow("Block:", self.block_pick)
        self.scene = QLineEdit()
        self.scene.setToolTip("A line for his prompt: where he is and how he's chatting")
        self.scene.textEdited.connect(lambda t: self._set_block("scene", t))
        form.addRow("Scene:", self.scene)
        self.away = QLineEdit()
        self.away.setToolTip("His AIM away message while he's in this block (if he's away from the computer)")
        self.away.textEdited.connect(lambda t: self._set_block("away", t))
        form.addRow("Away message:", self.away)
        self.asleep = QCheckBox("Away from the computer (the legs stop, the away message answers)")
        self.asleep.toggled.connect(lambda on: self._set_block("asleep", on))
        form.addRow("", self.asleep)
        self.reply_pace = QComboBox()
        for label, v in PACES:
            self.reply_pace.addItem(label, v)
        self.reply_pace.currentIndexChanged.connect(lambda _i: self._set_block("reply_pace",
                                                                              self.reply_pace.currentData()))
        form.addRow("He answers IMs:", self.reply_pace)
        bl.addLayout(form, 3)
        self.weights = QTableWidget(len(legs), 2)
        self.weights.setHorizontalHeaderLabels(["Leg", "In this block"])
        self.weights.verticalHeader().hide()
        self.weights.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.weights.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.weight_boxes = {}
        for r, cls in enumerate(legs):
            item = QTableWidgetItem(cls.title)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            item.setToolTip(cls.blurb or cls.title)
            self.weights.setItem(r, 0, item)
            box = QComboBox()
            for label, v in WEIGHTS:
                box.addItem(label, v)
            box.currentIndexChanged.connect(lambda _i, k=cls.key, b=box: self._set_weight(k, b.currentData()))
            self.weights.setCellWidget(r, 1, box)
            self.weight_boxes[cls.key] = box
        self.weights.setMinimumHeight(170)
        bl.addWidget(self.weights, 2)
        col.addWidget(blocks)

        # today
        today = QGroupBox("Today")
        tl = QFormLayout(today)
        self.override = QLineEdit()
        self.override.setPlaceholderText("e.g. home sick with a cold / Red's birthday dinner tonight / snowed in")
        self.override.textEdited.connect(self._set_override)
        tl.addRow("Today:", self.override)
        self.day_off = QCheckBox("A day off - no work today")
        self.day_off.toggled.connect(self._set_day_off)
        tl.addRow("", self.day_off)
        self.check = QCheckBox("Check each reply against today's story (and rewrite it once if it doesn't fit)")
        self.check.setChecked(bool(day.data.get("check_replies", True)))
        self.check.toggled.connect(lambda on: (day.data.__setitem__("check_replies", on), day.save()))
        tl.addRow("", self.check)
        col.addWidget(today)

        # right now
        now = QGroupBox("Right now")
        nl = QVBoxLayout(now)
        self.facts = QLabel()
        self.facts.setWordWrap(True)
        self.facts.setTextInteractionFlags(Qt.TextSelectableByMouse)
        nl.addWidget(self.facts)
        lists = QHBoxLayout()
        self.claims = self._editable_list("What he's told people today (double-click to edit)",
                                          ["Time", "To", "What he said"], self._claim_changed, self._add_claim,
                                          self._remove_claim, lists)
        self.events = self._editable_list("What's happened today", ["Time", "What"], self._event_changed,
                                          self._add_event, self._remove_event, lists)
        nl.addLayout(lists)
        col.addWidget(now)
        col.addStretch(1)
        self.setWidget(page)
        self._sig = None
        self._show_block()
        self._load_today()
        self.timer = QTimer(self, interval=1500, timeout=self.refresh)
        self.timer.start()
        self.refresh()

    # ---- building ------------------------------------------------------------------------------------------------
    def _editable_list(self, title, headers, changed, add, remove, into):
        box = QGroupBox(title)
        v = QVBoxLayout(box)
        tree = QTreeWidget()
        tree.setHeaderLabels(headers)
        tree.setRootIsDecorated(False)
        tree.setMinimumHeight(130)
        tree.setColumnWidth(0, 44)
        if len(headers) == 3:
            tree.setColumnWidth(1, 80)
        tree.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        tree.itemChanged.connect(changed)
        v.addWidget(tree)
        row = QHBoxLayout()
        row.addStretch(1)
        a = QPushButton("Add")
        a.clicked.connect(add)
        r = QPushButton("Remove")
        r.clicked.connect(remove)
        row.addWidget(a)
        row.addWidget(r)
        v.addLayout(row)
        into.addWidget(box)
        return tree

    # ---- the week and the blocks -----------------------------------------------------------------------------------
    def _set_follow(self, on):
        self.day.data["follow_schedule"] = on
        self.day.save()
        self._refresh_now()

    def _reset_week(self):
        self.day.data["schedule"] = self.day.standard_schedule()
        self.day.save()
        self.grid.update()
        self._refresh_now()

    def _block(self):
        return self.day.data["blocks"][self.block_pick.currentData()]

    def _show_block(self, *_):
        b = self._block()
        self._loading = True
        self.scene.setText(b.get("scene", ""))
        self.away.setText(b.get("away", ""))
        self.scene.setCursorPosition(0)
        self.away.setCursorPosition(0)
        self.asleep.setChecked(bool(b.get("asleep")))
        self.away.setEnabled(bool(b.get("asleep")))
        self.reply_pace.setCurrentIndex(_nearest(PACES, b.get("reply_pace", 1.0)))
        for key, box in self.weight_boxes.items():
            box.setCurrentIndex(_nearest(WEIGHTS, b.get("legs", {}).get(key, 1.0)))
        self._loading = False

    def _set_block(self, field, value):
        if getattr(self, "_loading", False):
            return
        self._block()[field] = value
        if field == "asleep":
            self.away.setEnabled(bool(value))
        self.day.save()

    def _set_weight(self, key, value):
        if getattr(self, "_loading", False):
            return
        legs = self._block().setdefault("legs", {})
        if abs(float(value) - 1.0) < 1e-6:
            legs.pop(key, None)
        else:
            legs[key] = value
        self.day.save()

    # ---- today ---------------------------------------------------------------------------------------------------------
    def _load_today(self):
        t = self.day.today
        self._loading = True
        self.override.setText(t.get("override", ""))
        self.day_off.setChecked(bool(t.get("day_off")))
        self._loading = False

    def _set_override(self, text):
        self.day.today["override"] = text.strip()
        self.day.save()

    def _set_day_off(self, on):
        if getattr(self, "_loading", False):
            return
        self.day.today["day_off"] = on
        self.day.save()
        self._refresh_now()

    # ---- right now -----------------------------------------------------------------------------------------------------
    def _claim_changed(self, item, column):
        if getattr(self, "_filling", False):
            return
        i = item.data(0, Qt.UserRole)
        cl = self.day.today["claims"]
        if 0 <= i < len(cl):
            cl[i]["who" if column == 1 else "text" if column == 2 else "t"] = item.text(column).strip()
            self.day.save()

    def _event_changed(self, item, column):
        if getattr(self, "_filling", False):
            return
        i = item.data(0, Qt.UserRole)
        ev = self.day.today["events"]
        if 0 <= i < len(ev):
            ev[i]["text" if column == 1 else "t"] = item.text(column).strip()
            self.day.save()

    def _add_claim(self):
        self.day.today["claims"].append({"t": self.day.now().strftime("%H:%M"), "who": "", "text": "something he said"})
        self.day.save()
        self.refresh(force=True)
        item = self.claims.topLevelItem(self.claims.topLevelItemCount() - 1)
        if item is not None:
            self.claims.editItem(item, 2)

    def _add_event(self):
        self.day.today["events"].append({"t": self.day.now().strftime("%H:%M"), "text": "something that happened"})
        self.day.save()
        self.refresh(force=True)
        item = self.events.topLevelItem(self.events.topLevelItemCount() - 1)
        if item is not None:
            self.events.editItem(item, 1)

    def _remove_claim(self):
        item = self.claims.currentItem()
        if item is not None:
            i = item.data(0, Qt.UserRole)
            if 0 <= i < len(self.day.today["claims"]):
                del self.day.today["claims"][i]
                self.day.save()
                self.refresh(force=True)

    def _remove_event(self):
        item = self.events.currentItem()
        if item is not None:
            i = item.data(0, Qt.UserRole)
            if 0 <= i < len(self.day.today["events"]):
                del self.day.today["events"][i]
                self.day.save()
                self.refresh(force=True)

    def _refresh_now(self):
        info = self.day.block_info()
        ends = self.day.block_ends()
        self.now_label.setText(f"Now: <b>{info.get('title')}</b> until {dayc.time_text(ends.time())}")
        self.facts.setText("\n".join(self.day.facts()))
        self.grid.update()

    def refresh(self, force=False):
        if not self.isVisible() and not force:
            return
        self._refresh_now()
        t = self.day.today
        sig = (t.get("date"), len(t["claims"]), len(t["events"]),
               t["claims"][-1]["text"] if t["claims"] else "", t["events"][-1]["text"] if t["events"] else "")
        editing = self.claims.state() == QAbstractItemView.EditingState or \
            self.events.state() == QAbstractItemView.EditingState
        if (sig == self._sig and not force) or (editing and not force):
            return
        if sig[0] != (self._sig or (None,))[0]:
            self._load_today()
        self._sig = sig
        self._filling = True
        for tree, rows, cols in ((self.claims, t["claims"], ("t", "who", "text")),
                                 (self.events, t["events"], ("t", "text"))):
            tree.clear()
            for i, row in enumerate(rows):
                item = QTreeWidgetItem([row.get(c, "") for c in cols])
                item.setFlags(item.flags() | Qt.ItemIsEditable)
                item.setData(0, Qt.UserRole, i)
                item.setToolTip(len(cols) - 1, row.get(cols[-1], ""))
                tree.addTopLevelItem(item)
            tree.scrollToBottom()
        self._filling = False


# ---- threads ------------------------------------------------------------------------------------------------------
class ThreadsTab(QWidget):
    """The threads list, one thread's editor, the mined suggestions and the style card."""

    def __init__(self, day, legs, pilot):
        super().__init__()
        self.day, self.legs, self.pilot = day, legs, pilot
        self.miner = None
        added = day.merge_mined()
        col = QVBoxLayout(self)
        intro = QLabel("The stories and bits of his life he brings up: at most one per conversation, and a follow-up "
                       "with someone who's already heard it. Suggestions found in your Telegram logs are listed but "
                       "not used until you set them Active.")
        intro.setWordWrap(True)
        col.addWidget(intro)
        split = QSplitter(Qt.Vertical)
        top = QWidget()
        tv = QVBoxLayout(top)
        tv.setContentsMargins(0, 0, 0, 0)
        filt = QHBoxLayout()
        self.show_suggested = QCheckBox("Show suggestions from my logs")
        self.show_suggested.setChecked(True)
        self.show_suggested.toggled.connect(self.fill)
        filt.addWidget(self.show_suggested)
        filt.addStretch(1)
        self.count = QLabel()
        filt.addWidget(self.count)
        tv.addLayout(filt)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Thread", "Kind", "Status", "Heard it", "From"])
        self.tree.setRootIsDecorated(False)
        self.tree.setAlternatingRowColors(True)
        for c, w in enumerate((230, 100, 70, 60)):
            self.tree.setColumnWidth(c, w)
        self.tree.currentItemChanged.connect(self._show)
        tv.addWidget(self.tree, 1)
        buttons = QHBoxLayout()
        for label, fn in (("New thread", self._new), ("Use it (Active)", self._activate), ("Pause", self._pause),
                          ("Delete", self._delete)):
            b = QPushButton(label)
            b.clicked.connect(fn)
            buttons.addWidget(b)
        buttons.addStretch(1)
        tv.addLayout(buttons)
        split.addWidget(top)

        edit = QGroupBox("This thread")
        form = QFormLayout(edit)
        self.title = QLineEdit()
        self.title.textEdited.connect(lambda t: self._set("title", t))
        form.addRow("Title:", self.title)
        kinds = QHBoxLayout()
        self.kind = QComboBox()
        for k, label in dayc.THREAD_KINDS.items():
            self.kind.addItem(label, k)
        self.kind.currentIndexChanged.connect(lambda _i: self._set("kind", self.kind.currentData()))
        kinds.addWidget(self.kind)
        self.status = QComboBox()
        for st in dayc.THREAD_STATUS:
            self.status.addItem(st.title(), st)
        self.status.currentIndexChanged.connect(lambda _i: self._set("status", self.status.currentData()))
        kinds.addWidget(QLabel("Status:"))
        kinds.addWidget(self.status)
        kinds.addStretch(1)
        form.addRow("Kind:", kinds)
        self.facts = QPlainTextEdit()
        self.facts.setPlaceholderText("What's true about it: who, what, where, how he feels. For an opener, the line "
                                      "itself; for a roleplay seed, the scene.")
        self.facts.setFixedHeight(58)
        self.facts.textChanged.connect(lambda: self._set("facts", self.facts.toPlainText()))
        form.addRow("Facts:", self.facts)
        self.beats = QPlainTextEdit()
        self.beats.setPlaceholderText("One line per day, for a life arc: day 1 - found a flat; day 2 - packing; "
                                      "day 3 - moving day...")
        self.beats.setFixedHeight(58)
        self.beats.textChanged.connect(lambda: self._set("beats", [b for b in self.beats.toPlainText().splitlines()
                                                                   if b.strip()]))
        form.addRow("Beats:", self.beats)
        self.leg_list = QListWidget()
        self.leg_list.setFlow(QListView.LeftToRight)
        self.leg_list.setWrapping(True)
        self.leg_list.setResizeMode(QListView.Adjust)
        self.leg_list.setFixedHeight(74)
        self.leg_list.setToolTip("While this thread is active, these legs come up more often")
        for cls in legs:
            it = QListWidgetItem(cls.title)
            it.setData(Qt.UserRole, cls.key)
            it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
            it.setCheckState(Qt.Unchecked)
            self.leg_list.addItem(it)
        self.leg_list.itemChanged.connect(self._legs_changed)
        form.addRow("Makes likelier:", self.leg_list)
        told = QHBoxLayout()
        self.told = QLabel()
        self.told.setWordWrap(True)
        told.addWidget(self.told, 1)
        forget = QPushButton("Forget who's heard it")
        forget.clicked.connect(self._forget)
        told.addWidget(forget)
        form.addRow("Heard it:", told)
        self.editor = edit
        split.addWidget(edit)

        style = QGroupBox("His style card (from your recent Telegram chats)")
        sl = QVBoxLayout(style)
        self.style_text = QLabel()
        self.style_text.setWordWrap(True)
        self.style_text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        sl.addWidget(self.style_text)
        row = QHBoxLayout()
        self.use_style = QCheckBox("Use my style card in his prompt")
        self.use_style.setChecked(bool(day.data.get("use_style")))
        self.use_style.toggled.connect(lambda on: (day.data.__setitem__("use_style", on), day.save()))
        row.addWidget(self.use_style)
        row.addStretch(1)
        self.mine_btn = QPushButton("Look through my Telegram logs again...")
        self.mine_btn.setToolTip("Runs selfmodel.threads: reads the recent Telegram export, summarises conversations "
                                 "with a model on the graphics card and groups them into suggested threads and a "
                                 "style card. Takes a while; Kithylin shouldn't be at the computer meanwhile.")
        self.mine_btn.clicked.connect(self._mine)
        row.addWidget(self.mine_btn)
        sl.addLayout(row)
        self.mine_status = QLabel()
        sl.addWidget(self.mine_status)
        split.addWidget(style)
        split.setSizes([260, 260, 120])
        col.addWidget(split, 1)
        self._current = None
        self.fill()
        self._show_style()
        if added:
            self.mine_status.setText(f"{added} new suggestion{'s' if added != 1 else ''} from your logs.")
        self.timer = QTimer(self, interval=3000, timeout=self._poll)
        self.timer.start()

    # ---- the list ---------------------------------------------------------------------------------------------------
    def fill(self, *_):
        keep = self._current
        self.tree.blockSignals(True)
        self.tree.clear()
        show_sugg = self.show_suggested.isChecked()
        order = {"active": 0, "paused": 1, "suggested": 2, "done": 3}
        threads = sorted(self.day.data["threads"], key=lambda t: (order.get(t.get("status"), 9),
                                                                  -int(t.get("support") or 0)))
        pick = None
        shown = 0
        for t in threads:
            if t.get("status") == "suggested" and not show_sugg:
                continue
            src = {"you": "You", "mined": "Your logs", "auto": "His day"}.get(t.get("source"), t.get("source", ""))
            if t.get("source") == "mined" and t.get("support"):
                src += f" ({t['support']})"
            item = QTreeWidgetItem([t.get("title", ""), dayc.THREAD_KINDS.get(t.get("kind"), t.get("kind", "")),
                                    t.get("status", "").title(), str(len(t.get("told", {}))), src])
            item.setData(0, Qt.UserRole, t["id"])
            item.setToolTip(0, t.get("facts", ""))
            if t.get("status") == "active":
                f = item.font(0)
                f.setBold(True)
                item.setFont(0, f)
            self.tree.addTopLevelItem(item)
            shown += 1
            if t["id"] == keep:
                pick = item
        self.tree.blockSignals(False)
        active = len(self.day.active_threads())
        self.count.setText(f"{active} active, {shown} shown")
        if pick is not None:
            self.tree.setCurrentItem(pick)
        elif self.tree.topLevelItemCount():
            self.tree.setCurrentItem(self.tree.topLevelItem(0))
        else:
            self._show(None)

    def _thread(self):
        return self.day.thread(self._current) if self._current else None

    def _show(self, item, *_):
        self._current = item.data(0, Qt.UserRole) if item is not None else None
        t = self._thread()
        self.editor.setEnabled(t is not None)
        self._loading = True
        t = t or {}
        self.title.setText(t.get("title", ""))
        self.kind.setCurrentIndex(max(0, self.kind.findData(t.get("kind", "life"))))
        self.status.setCurrentIndex(max(0, self.status.findData(t.get("status", "active"))))
        self.facts.setPlainText(t.get("facts", ""))
        self.beats.setPlainText("\n".join(t.get("beats", [])))
        for i in range(self.leg_list.count()):
            it = self.leg_list.item(i)
            it.setCheckState(Qt.Checked if it.data(Qt.UserRole) in t.get("legs", []) else Qt.Unchecked)
        told = t.get("told", {})
        self.told.setText(", ".join(f"{who} ({when[5:]})" for who, when in sorted(told.items(), key=lambda x: x[1]))
                          or "nobody yet")
        self._loading = False

    def _set(self, field, value):
        if getattr(self, "_loading", False):
            return
        t = self._thread()
        if t is None:
            return
        t[field] = value
        if field == "status" and value == "active" and not t.get("started"):
            t["started"] = self.day.today_key()
        self.day.save()
        item = self.tree.currentItem()
        if item is not None and field in ("title", "kind", "status"):
            item.setText({"title": 0, "kind": 1, "status": 2}[field],
                         dayc.THREAD_KINDS.get(value, value) if field == "kind" else
                         str(value).title() if field == "status" else value)

    def _legs_changed(self, _item):
        if getattr(self, "_loading", False):
            return
        self._set("legs", [self.leg_list.item(i).data(Qt.UserRole) for i in range(self.leg_list.count())
                           if self.leg_list.item(i).checkState() == Qt.Checked])

    def _new(self):
        t = dayc.new_thread("A new thread", "life", status="active", started=self.day.today_key())
        self.day.data["threads"].append(t)
        self.day.save()
        self._current = t["id"]
        self.fill()
        self.title.setFocus()
        self.title.selectAll()

    def _activate(self):
        t = self._thread()
        if t is not None:
            t["status"] = "active"
            t["started"] = t.get("started") or self.day.today_key()
            self.day.save()
            self.fill()

    def _pause(self):
        t = self._thread()
        if t is not None:
            t["status"] = "paused"
            self.day.save()
            self.fill()

    def _delete(self):
        if self._current:
            self.day.remove_thread(self._current)
            self._current = None
            self.fill()

    def _forget(self):
        t = self._thread()
        if t is not None:
            t["told"] = {}
            self.day.save()
            self._show(self.tree.currentItem())
            self.fill()

    # ---- the style card and the miner ------------------------------------------------------------------------------
    def _show_style(self):
        s = self.day.data.get("style") or {}
        if not s:
            self.style_text.setText("No style card yet: look through your Telegram logs to make one.")
            return
        lines = []
        if s.get("openers"):
            lines.append("Openers: " + ", ".join(f"“{o}”" for o in s["openers"][:8]))
        if s.get("closers"):
            lines.append("Closers: " + ", ".join(f"“{c}”" for c in s["closers"][:8]))
        wb = s.get("words_by_block") or {}
        if wb:
            lines.append("Words per message: " + ", ".join(f"{k} {round(v)}" for k, v in wb.items()))
        if s.get("habits"):
            lines.append("Habits: " + ", ".join(s["habits"][:12]))
        if s.get("sessions"):
            lines.append(f"From {s['sessions']} conversations since {s.get('since', '?')}"
                         + (f" (built {self.day.data.get('style_built')})" if self.day.data.get("style_built") else ""))
        self.style_text.setText("\n".join(lines))

    def _mine(self):
        p = self.pilot()
        if p is not None and p.running:
            self.mine_status.setText("Stop Kithylin first: the look-through needs the graphics card to itself.")
            return
        if self.miner is not None and self.miner.poll() is None:
            return
        apps = dayc.TIMELINE / "ClaudeApps"
        log = dayc.MINED_FILE.with_name("threads.log")
        exe = sys.executable
        if exe.lower().endswith("pythonw.exe"):
            exe = exe[:-len("pythonw.exe")] + "python.exe"
        try:
            log.parent.mkdir(parents=True, exist_ok=True)
            with open(log, "w", encoding="utf-8") as out:
                self.miner = subprocess.Popen([exe, "-m", "selfmodel.threads"], cwd=str(apps), stdout=out,
                                              stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                              creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        except OSError as e:
            self.mine_status.setText(f"Couldn't start it: {e}")
            return
        self.mine_btn.setEnabled(False)
        self.mine_status.setText("Looking through your Telegram logs (this takes a while)...")

    def _poll(self):
        if self.miner is None:
            return
        log = dayc.MINED_FILE.with_name("threads.log")
        try:
            last = [ln for ln in log.read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip()][-1:]
        except OSError:
            last = []
        if self.miner.poll() is None:
            if last:
                self.mine_status.setText(last[0][:140])
            return
        code, self.miner = self.miner.returncode, None
        self.mine_btn.setEnabled(True)
        if code != 0:
            self.mine_status.setText("It stopped: " + (last[0][:120] if last else f"exit code {code}")
                                     + f" (see {log.name})")
            return
        added = self.day.merge_mined()
        self.fill()
        self._show_style()
        self.mine_status.setText(f"Done: {added} new suggestion{'s' if added != 1 else ''}.")


# ---- interests ----------------------------------------------------------------------------------------------------
class _TierList(QListWidget):
    """One column of contacts; contacts are dragged between columns."""

    def __init__(self, tier, on_change):
        super().__init__()
        self.tier = tier
        self.on_change = on_change
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setIconSize(QSize(32, 32))
        self.setSpacing(1)
        self.setSortingEnabled(True)

    def dropEvent(self, e):
        super().dropEvent(e)
        self.on_change(self)                       # (the column it came from removes it by itself)


class InterestsTab(QWidget):
    """Who matters to him: his contacts in three columns - love interests, close acquaintances, friends."""

    def __init__(self, day, contacts):
        super().__init__()
        self.day = day
        self.contacts = contacts                    # [(id, screen name, icon path or "")]
        col = QVBoxLayout(self)
        intro = QLabel("Who he talks to most. Drag a buddy to another column (or pick one and use the buttons). "
                       "It sets how quickly he answers them, how long he chats, who he IMs first and who he "
                       "roleplays with, and his prompt says who they are to him.")
        intro.setWordWrap(True)
        col.addWidget(intro)
        row = QHBoxLayout()
        self.lists, self.counts = {}, {}
        for tier in dayc.TIER_ORDER:
            info = dayc.TIERS[tier]
            box = QGroupBox(info["title"] + ("s" if not info["title"].endswith("s") else ""))
            v = QVBoxLayout(box)
            blurb = QLabel(info["blurb"][:1].upper() + info["blurb"][1:] + ".")
            blurb.setWordWrap(True)
            blurb.setMinimumHeight(34)
            v.addWidget(blurb)
            lst = _TierList(tier, self._sync)
            lst.itemSelectionChanged.connect(lambda t=tier: self._selected(t))
            v.addWidget(lst, 1)
            self.counts[tier] = QLabel()
            v.addWidget(self.counts[tier])
            self.lists[tier] = lst
            row.addWidget(box, 1)
        col.addLayout(row, 1)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        closer = QPushButton("▲ Closer")
        closer.clicked.connect(lambda: self._move(-1))
        further = QPushButton("▼ Less close")
        further.clicked.connect(lambda: self._move(1))
        buttons.addWidget(closer)
        buttons.addWidget(further)
        col.addLayout(buttons)
        self.fill()

    def fill(self):
        from PySide6.QtGui import QIcon
        for lst in self.lists.values():
            lst.clear()
        for cid, name, icon in self.contacts:
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, cid)
            if icon:
                item.setIcon(QIcon(icon))
            self.lists[self.day.tier(cid)].addItem(item)
        self._counts()

    def _counts(self):
        for tier, lst in self.lists.items():
            n = lst.count()
            self.counts[tier].setText(f"{n} {'buddy' if n == 1 else 'buddies'}")

    def _sync(self, lst):
        """Buddies dropped into a column take its tier."""
        interests = self.day.data.setdefault("interests", {})
        for i in range(lst.count()):
            interests[lst.item(i).data(Qt.UserRole)] = lst.tier
        self.day.save()
        QTimer.singleShot(0, self._counts)

    def _selected(self, tier):
        if self.lists[tier].selectedItems():
            for other, lst in self.lists.items():
                if other != tier:
                    lst.blockSignals(True)
                    lst.clearSelection()
                    lst.blockSignals(False)

    def _move(self, step):
        for i, tier in enumerate(dayc.TIER_ORDER):
            items = self.lists[tier].selectedItems()
            if not items:
                continue
            j = i + step
            if not 0 <= j < len(dayc.TIER_ORDER):
                return
            cid = items[0].data(Qt.UserRole)
            self.day.set_tier(cid, dayc.TIER_ORDER[j])
            self.fill()
            target = self.lists[dayc.TIER_ORDER[j]]
            for k in range(target.count()):
                if target.item(k).data(Qt.UserRole) == cid:
                    target.setCurrentRow(k)
            return
