"""System Restore, like Windows XP's: restore points hold Windows' *settings* (display, desktop layout, account,
network, game statistics, program preferences), never your documents, e-mail or the buddies' memories.
A 'System Checkpoint' is made automatically once a day; you can make your own; restoring first makes an 'Undo'
point, then really restarts ClaudeXP and says 'Restoration Complete'. Formatting C: erases them, as on XP."""
import json
import shutil
from datetime import datetime, timedelta

from PySide6.QtCore import QDate, QPointF, QRectF, Qt
from PySide6.QtGui import (QColor, QFont, QIcon, QLinearGradient, QPainter, QPen, QPixmap, QPolygonF,
                           QTextCharFormat)
from PySide6.QtWidgets import (QButtonGroup, QCalendarWidget, QHBoxLayout, QLabel, QLineEdit, QListWidget,
                               QListWidgetItem, QPushButton, QRadioButton, QStackedWidget, QVBoxLayout, QWidget)

from .. import clock, sound
from ..paths import DATA
from ..wm import XPWindow

RESTORE_DIR = DATA / "System Volume Information" / "_restore"
DONE_FILE = DATA / "restore_done.json"
SETTINGS = ["display.json", "desktop.json", "user.json", "network.json", "updates.json", "antivirus.json",
            "games.json", "run.json", "calc.json", "wmp.json"]
KINDS = {"checkpoint": "System Checkpoint", "manual": "", "undo": "Restore Operation", "update": "Windows Update"}


def restore_icon(size=32):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.scale(size / 32, size / 32)
    p.setPen(QPen(QColor("#304070"), 1))
    p.setBrush(QColor("white"))
    p.drawEllipse(QRectF(4, 4, 24, 24))
    p.setPen(QPen(QColor("#202020"), 2))
    p.drawLine(16, 16, 16, 9)
    p.drawLine(16, 16, 21, 18)
    p.setPen(QPen(QColor("#2A9A2A"), 3))
    p.drawArc(QRectF(1, 1, 30, 30), 100 * 16, 120 * 16)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#2A9A2A"))
    p.drawPolygon(QPolygonF([QPointF(2, 18), QPointF(-1, 10), QPointF(7, 12)]))
    p.end()
    return QIcon(pm)


# ---- restore points ------------------------------------------------------------------------------------------

def points():
    out = []
    if RESTORE_DIR.exists():
        for d in RESTORE_DIR.iterdir():
            try:
                out.append(json.loads((d / "manifest.json").read_text(encoding="utf-8")) | {"dir": d})
            except (OSError, ValueError):
                continue
    return sorted(out, key=lambda p: p["id"])


def label(point):
    kind = KINDS.get(point["kind"], "")
    desc = point.get("desc") or kind
    if point["kind"] == "undo":
        return f"Undo: {desc}"
    return desc if not kind or desc == kind else f"{kind}: {desc}"


def create_point(desc, kind="manual"):
    existing = points()
    n = (existing[-1]["id"] + 1) if existing else 1
    folder = RESTORE_DIR / f"RP{n}"
    folder.mkdir(parents=True, exist_ok=True)
    saved = []
    for name in SETTINGS:
        if (DATA / name).exists():
            shutil.copy2(DATA / name, folder / name)
            saved.append(name)
    now = clock.now()
    manifest = {"id": n, "desc": desc, "kind": kind, "files": saved,
                "real": datetime.now().astimezone().isoformat(timespec="seconds"),
                "date": now.strftime("%Y-%m-%d"), "time": clock.time_text(now)}
    (folder / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    # XP keeps a limited amount; keep the newest 30
    for old in existing[:-29]:
        shutil.rmtree(old["dir"], ignore_errors=True)
    return manifest


def auto_checkpoint():
    """A daily 'System Checkpoint', like XP's."""
    pts = [p for p in points() if p["kind"] == "checkpoint"]
    if pts:
        last = datetime.fromisoformat(pts[-1]["real"])
        if datetime.now().astimezone() - last < timedelta(hours=24):
            return None
    return create_point("System Checkpoint", "checkpoint")


def put_back(point):
    """Copy the point's settings back (run while ClaudeXP is stopped). A setting that didn't exist yet at that
    time goes back to its default (the 'Undo' point made just before keeps a copy)."""
    for name in SETTINGS:
        src = point["dir"] / name
        if name in point["files"] and src.exists():
            shutil.copy2(src, DATA / name)
        elif (DATA / name).exists():
            (DATA / name).unlink()
    DONE_FILE.write_text(json.dumps({"desc": label(point), "date": point["date"], "time": point["time"]}),
                         encoding="utf-8")


def restore(desktop, point):
    """Make an Undo point, then restart ClaudeXP and put the settings back while nothing is running."""
    from .. import programs, setup
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication
    create_point(f"Restore to {point['date']} {point['time']}", "undo")
    app = desktop.window()
    programs.shutdown_all()
    for win in list(desktop.windows):
        desktop.close_window(win)
    app.shutdown_screen.text = "System Restore is restoring your computer..."
    app.stack.setCurrentWidget(app.shutdown_screen)
    sound.play("shutdown", lambda: QTimer.singleShot(1500, lambda: setup.reboot(QApplication.instance(),
                                                                               lambda: put_back(point))))


def check_completed(desktop):
    """After logging on: 'Restoration Complete' (once)."""
    try:
        done = json.loads(DONE_FILE.read_text(encoding="utf-8"))
        DONE_FILE.unlink()
    except (OSError, ValueError):
        return
    open_wizard(desktop, completed=done)


# ---- the wizard -------------------------------------------------------------------------------------------------

class Side(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(150)

    def paintEvent(self, event):
        p = QPainter(self)
        g = QLinearGradient(0, 0, 0, self.height())
        g.setColorAt(0, QColor("#7AA1E6"))
        g.setColorAt(1, QColor("#3A6BC5"))
        p.fillRect(self.rect(), g)
        p.drawPixmap(35, 40, restore_icon(80).pixmap(80, 80))
        f = QFont("Trebuchet MS")
        f.setPixelSize(13)
        f.setBold(True)
        p.setFont(f)
        p.setPen(QColor("white"))
        p.drawText(QRectF(10, 140, 130, 60), Qt.AlignCenter | Qt.TextWordWrap, "System Restore")


class Wizard(QWidget):
    def __init__(self, desktop, completed=None):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.setObjectName("sr")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("QWidget#sr { background: white; } QLabel, QRadioButton, QPushButton, QListWidget, "
                           "QLineEdit { font-family: Tahoma; font-size: 11px; } QLabel#title { font-family: "
                           "'Trebuchet MS'; font-size: 20px; color: #1C3D91; font-weight: bold; }"
                           "QWidget#buttons { background: #ECE9D8; border-top: 1px solid #ACA899; }")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        top = QHBoxLayout()
        top.setSpacing(0)
        top.addWidget(Side())
        self.pages = QStackedWidget()
        top.addWidget(self.pages, 1)
        root.addLayout(top, 1)
        bar = QWidget()
        bar.setObjectName("buttons")
        bar.setAttribute(Qt.WA_StyledBackground, True)
        bh = QHBoxLayout(bar)
        bh.setContentsMargins(10, 8, 10, 8)
        bh.addStretch()
        self.back = QPushButton("< Back")
        self.next = QPushButton("Next >")
        self.cancel = QPushButton("Cancel")
        for b in (self.back, self.next, self.cancel):
            b.setFixedSize(80, 23)
            bh.addWidget(b)
        root.addWidget(bar)
        self.back.clicked.connect(lambda: self.go(self.prev_page.get(self.pages.currentIndex(), 0)))
        self.next.clicked.connect(self._next)
        self.cancel.clicked.connect(lambda: self.frame.request_close())
        self.prev_page = {}
        self._build()
        if completed:
            self.done_text.setText(f"Your computer has been successfully restored to:\n\n{completed['desc']}\n"
                                   f"{completed['date']} {completed['time']}\n\nYour documents, e-mail and other "
                                   "personal files were not changed.")
            self.go(5)
        else:
            self.go(0)

    def _page(self, title):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(24, 18, 24, 12)
        t = QLabel(title)
        t.setObjectName("title")
        t.setWordWrap(True)
        v.addWidget(t)
        v.addSpacing(8)
        self.pages.addWidget(w)
        return v

    def _text(self, v, text):
        lab = QLabel(text)
        lab.setWordWrap(True)
        v.addWidget(lab)
        return lab

    def _build(self):
        v = self._page("Welcome to System Restore")
        self._text(v, "You can use System Restore to undo harmful changes to your computer and restore its settings "
                      "and performance. System Restore returns your computer to an earlier time (called a restore "
                      "point) without causing you to lose recent work, such as saved documents, e-mail, or history "
                      "and favorites lists.\n\nYour computer automatically creates restore points (called system "
                      "checkpoints), but you can also create your own.")
        v.addSpacing(10)
        self._text(v, "To begin, select the task that you want to perform:")
        self.choice = QButtonGroup(self)
        self.opt_restore = QRadioButton("Restore my computer to an earlier time")
        self.opt_create = QRadioButton("Create a restore point")
        self.opt_restore.setChecked(True)
        for r in (self.opt_restore, self.opt_create):
            self.choice.addButton(r)
            v.addWidget(r)
        v.addStretch()

        v = self._page("Select a Restore Point")
        self._text(v, "The following calendar displays in bold all of the dates that have restore points available. "
                      "The list displays the restore points that are available for the selected date.")
        row = QHBoxLayout()
        self.calendar = QCalendarWidget()
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.calendar.setFixedSize(230, 170)
        self.calendar.selectionChanged.connect(self._fill_day)
        row.addWidget(self.calendar)
        self.day_list = QListWidget()
        row.addWidget(self.day_list, 1)
        v.addLayout(row)
        v.addStretch()

        v = self._page("Confirm Restore Point Selection")
        self.confirm_text = self._text(v, "")
        v.addStretch()

        v = self._page("Create a Restore Point")
        self._text(v, "Your computer automatically creates restore points at regularly scheduled times. However, you "
                      "can use System Restore to create your own restore points. This is useful if you are about to "
                      "make changes to your computer, such as installing a program or changing settings.")
        v.addSpacing(8)
        self._text(v, "Restore point description:")
        self.desc = QLineEdit()
        self.desc.setMaxLength(64)
        self.desc.textChanged.connect(lambda t: self.pages.currentIndex() == 3 and self.next.setEnabled(bool(t.strip())))
        v.addWidget(self.desc)
        v.addStretch()

        v = self._page("Restore Point Created")
        self.created_text = self._text(v, "")
        v.addStretch()

        v = self._page("Restoration Complete")
        self.done_text = self._text(v, "")
        v.addStretch()

    def go(self, index):
        self.pages.setCurrentIndex(index)
        self.back.setEnabled(index in (1, 2, 3))
        self.next.setText({2: "Next >", 3: "Create", 4: "Close", 5: "OK"}.get(index, "Next >"))
        self.cancel.setVisible(index not in (4, 5))
        if index == 1:
            self._mark_calendar()
        if index == 3:
            self.desc.setFocus()
            self.next.setEnabled(bool(self.desc.text().strip()))
        else:
            self.next.setEnabled(index != 1 or self.day_list.currentItem() is not None)

    def _mark_calendar(self):
        bold = QTextCharFormat()
        f = QFont()
        f.setBold(True)
        bold.setFont(f)
        bold.setForeground(QColor("#000080"))
        last = None
        for p in points():
            d = QDate.fromString(p["date"], "yyyy-MM-dd")
            self.calendar.setDateTextFormat(d, bold)
            last = d
        self.calendar.setSelectedDate(last or QDate(clock.now().year, clock.now().month, clock.now().day))
        self._fill_day()

    def _fill_day(self):
        day = self.calendar.selectedDate().toString("yyyy-MM-dd")
        self.day_list.clear()
        for p in reversed(points()):
            if p["date"] == day:
                item = QListWidgetItem(f"{p['time']}   {label(p)}")
                item.setData(Qt.UserRole, p)
                self.day_list.addItem(item)
        if self.day_list.count():
            self.day_list.setCurrentRow(0)
        self.next.setEnabled(self.day_list.count() > 0)

    def _next(self):
        i = self.pages.currentIndex()
        if i == 0:
            target = 1 if self.opt_restore.isChecked() else 3
            self.prev_page[target] = 0
            self.go(target)
        elif i == 1:
            item = self.day_list.currentItem()
            if item is None:
                return
            self.chosen = item.data(Qt.UserRole)
            p = self.chosen
            self.confirm_text.setText(
                f"Selected restore point:\n\n    {p['date']}  {p['time']}\n    {label(p)}\n\n"
                "This process does not cause you to lose recent work, such as saved documents or e-mail, and is "
                "completely reversible.\n\nDuring the restoration, System Restore shuts down Windows. After the "
                "restoration is complete, Windows restarts using the settings from the date and time listed above."
                "\n\nIMPORTANT: Before continuing, save your changes and close any open programs.\n\n"
                "To restore your computer to this date and time, click Next.")
            self.prev_page[2] = 1
            self.go(2)
        elif i == 2:
            self.frame.request_close()
            restore(self.desktop, self.chosen)
        elif i == 3:
            p = create_point(self.desc.text().strip())
            self.created_text.setText(f"New restore point:\n\n    {p['date']}  {p['time']}\n    {p['desc']}\n\n"
                                      "To restore your computer to this state, or any other restore point, start "
                                      "System Restore again and select 'Restore my computer to an earlier time'.")
            self.go(4)
        else:
            self.frame.request_close()


def open_wizard(desktop, completed=None):
    body = Wizard(desktop, completed)
    win = XPWindow(desktop, "System Restore", body, restore_icon(), (660, 470))
    body.frame = win
    desktop.open_window(win)
    return win
