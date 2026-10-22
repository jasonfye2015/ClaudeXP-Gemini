"""The out-of-box experience of Windows 11: the light pages after the installation's last restart - country, keyboard,
the PC's name, your account, a PIN, privacy choices, speech - and, for a computer outside the Timeline, who you are
online (your fursona or your own name and picture). In the Claude Timeline the launcher's Profile answers the
identity questions, so those pages are skipped."""
from PySide6.QtCore import QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPixmap, QRadialGradient
from PySide6.QtWidgets import (QCheckBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
                               QProgressBar, QPushButton, QStackedWidget, QTextBrowser, QVBoxLayout, QWidget)

from . import ms
from .. import timeline, user

PAGES = ["region", "keyboard", "names", "fursona", "online", "password", "privacy", "speech", "finish"]
TIMELINE_PAGES = ["region", "keyboard", "names", "password", "privacy", "speech", "finish"]
REGIONS = ["United States", "Canada", "United Kingdom", "Australia", "Germany", "France", "Netherlands", "Japan"]
KEYBOARDS = ["US", "United States-International", "United Kingdom", "Canadian Multilingual Standard", "German", "French"]
PRIVACY = [("Location", "Let Microsoft and apps use your location.", False),
           ("Find my device", "Turn on Find my device to help locate this PC if you lose it.", False),
           ("Diagnostic data", "Send required diagnostic data about your device.", True),
           ("Inking & typing", "Help improve language recognition.", False),
           ("Tailored experiences", "Use your diagnostic data for tips and recommendations.", False),
           ("Advertising ID", "Let apps show you personalized ads.", False)]
UNIQUE = "__unique__"
OOBE_CSS = """
QFrame#dlg { background: #FFFFFF; border: 1px solid #E0E0E0; border-radius: 8px; }
QLabel { font-family: 'Segoe UI Variable Text', 'Segoe UI'; font-size: 13px; color: #1A1A1A; background: transparent; }
QLabel#head { font-size: 26px; font-weight: 600; color: #1A1A1A; }
QLabel#sub { font-size: 13px; color: #5C5C5C; }
QLabel#grey { color: #5C5C5C; }
QPushButton { font-family: 'Segoe UI Variable Text', 'Segoe UI'; font-size: 13px; padding: 7px 24px; min-width: 90px;
              background: #FBFBFB; border: 1px solid #D0D0D0; border-radius: 4px; }
QPushButton:hover { background: #F0F0F0; }
QPushButton#next { background: #0067C0; color: white; border-color: #0067C0; }
QPushButton#next:hover { background: #1975C5; }
QPushButton:disabled { color: #9A9A9A; background: #F5F5F5; border-color: #E5E5E5; }
QLineEdit { font-family: 'Segoe UI'; font-size: 14px; padding: 7px 10px; border: 1px solid #E0E0E0;
            border-bottom: 1px solid #8A8A8A; border-radius: 4px; background: #FFFFFF; }
QLineEdit:focus { border-bottom: 2px solid #0067C0; }
QListWidget { font-family: 'Segoe UI'; font-size: 13px; border: 1px solid #E0E0E0; border-radius: 6px;
              background: #FFFFFF; outline: none; }
QListWidget::item { height: 36px; padding-left: 8px; border-radius: 4px; }
QListWidget::item:hover { background: #F0F0F0; }
QListWidget::item:selected { background: #E6F0FB; color: #1A1A1A; }
QCheckBox { font-family: 'Segoe UI'; font-size: 13px; spacing: 10px; }
QTextBrowser { font-family: 'Segoe UI'; font-size: 12px; border: 1px solid #E0E0E0; border-radius: 6px; }
QProgressBar { border: none; background: #E0E0E0; border-radius: 2px; height: 4px; }
QProgressBar::chunk { background: #0067C0; border-radius: 2px; }
"""


class Oobe(QWidget):
    finished = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.identity = None
        self.pages = PAGES
        self.page = 0
        self.preset = None
        self.speech_state = "idle"
        self.speech_task = None
        self.dlg = QFrame(self)
        self.dlg.setObjectName("dlg")
        self.dlg.setStyleSheet(OOBE_CSS)
        self.dlg.setFixedSize(760, 540)
        v = QVBoxLayout(self.dlg)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        self.stack = QStackedWidget()
        v.addWidget(self.stack, 1)
        foot = QWidget()
        foot.setFixedHeight(64)
        fl = QHBoxLayout(foot)
        fl.setContentsMargins(40, 12, 40, 16)
        self.back = QPushButton("Back")
        fl.addWidget(self.back)
        fl.addStretch()
        self.next = QPushButton("Next")
        self.next.setObjectName("next")
        self.back.clicked.connect(lambda: self._go(-1))
        self.next.clicked.connect(lambda: self._go(1))
        fl.addWidget(self.next)
        v.addWidget(foot)
        self.widgets = {}
        self._build()

    # ---- building ----
    def _page(self, key, title, sub, *items):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(40, 36, 40, 8)
        v.setSpacing(12)
        t = QLabel(title)
        t.setObjectName("head")
        t.setWordWrap(True)
        v.addWidget(t)
        if sub:
            s = QLabel(sub)
            s.setObjectName("sub")
            s.setWordWrap(True)
            v.addWidget(s)
        for x in items:
            if isinstance(x, QWidget):
                v.addWidget(x)
            else:
                v.addLayout(x)
        v.addStretch()
        self.widgets[key] = w
        return w

    def _build(self):
        # region
        self.region = QListWidget()
        self.region.addItems(REGIONS)
        self.region.setCurrentRow(0)
        self.region.setFixedHeight(220)
        self._page("region", "Is this the right country or region?", "", self.region)
        # keyboard
        self.keyboard = QListWidget()
        self.keyboard.addItems(KEYBOARDS)
        self.keyboard.setCurrentRow(0)
        self.keyboard.setFixedHeight(220)
        self._page("keyboard", "Is this the right keyboard layout or input method?",
                   "If you also use another keyboard layout, you can add that next.", self.keyboard)
        # names
        self.name = QLineEdit()
        self.computer = QLineEdit(user.DEFAULT_COMPUTER)
        self.name.textChanged.connect(self._refresh)
        self.computer.textChanged.connect(self._refresh)
        self.name_note = QLabel("")
        self.name_note.setObjectName("grey")
        self._page("names", "Let's name your PC", "Make it unique and easy to recognize on your network. Then tell us "
                   "who's going to use this device.", QLabel("PC name"), self.computer, QLabel("Your name"), self.name,
                   self.name_note)
        # fursona (outside the Timeline)
        self.sona_list = QListWidget()
        self.sona_list.setFixedHeight(150)
        self.sona_info = QLabel("")
        self.sona_info.setWordWrap(True)
        self.sona_list.currentItemChanged.connect(self._sona_chosen)
        self._page("fursona", "Choose your fursona", "Pick a ready-made fursona (its own name, picture, profile and "
                   "online accounts), or be unique.", self.sona_list, self.sona_info)
        # online name and picture
        self.handle = QLineEdit()
        self.same = QCheckBox("Use my name online too")
        self.same.setChecked(True)
        self.same.toggled.connect(self._refresh)
        self.pictures = QListWidget()
        self.pictures.setViewMode(QListWidget.IconMode)
        self.pictures.setIconSize(QPixmap(48, 48).size())
        self.pictures.setFixedHeight(120)
        self.pictures.setMovement(QListWidget.Static)
        from PySide6.QtGui import QIcon
        for pic_id, _label, pm in user.pictures():
            it = QListWidgetItem(QIcon(pm), "")
            it.setData(Qt.UserRole, pic_id)
            self.pictures.addItem(it)
        self.pictures.setCurrentRow(0)
        self._page("online", "Your name online, and a picture for your account",
                   "The messengers, IRC and the MUCK sign in with this name.", self.handle, self.same,
                   QLabel("Pick a picture for your account"), self.pictures)
        # PIN
        self.pw = QLineEdit()
        self.pw.setEchoMode(QLineEdit.Password)
        self.pw.setPlaceholderText("New PIN")
        self.pw2 = QLineEdit()
        self.pw2.setEchoMode(QLineEdit.Password)
        self.pw2.setPlaceholderText("Confirm PIN")
        self.hint = QLineEdit()
        self.hint.setPlaceholderText("A hint, in case you forget it")
        for e in (self.pw, self.pw2):
            e.textChanged.connect(self._refresh)
        self._page("password", "Create a PIN", "A PIN is a fast, secure way to sign in. It stays on this device. "
                   "Leave it empty to sign in with a click.", self.pw, self.pw2, self.hint)
        # privacy
        self.privacy = []
        box = QVBoxLayout()
        box.setSpacing(6)
        for name, text, on in PRIVACY:
            c = QCheckBox(f"{name} - {text}")
            c.setChecked(on)
            box.addWidget(c)
            self.privacy.append(c)
        self._page("privacy", "Choose privacy settings for your device",
                   "Microsoft puts you in control of your privacy. Choose your settings, then select Accept.", box)
        # speech
        self.speech_terms = QTextBrowser()
        self.speech_terms.setFixedHeight(110)
        self.speech_agree = QCheckBox("I accept the speech models' licences")
        self.speech_agree.toggled.connect(self._speech_changed)
        self.speech_run = QPushButton("Set up voice access and test it")
        self.speech_run.clicked.connect(self._speech_start)
        self.speech_skip = QCheckBox("Skip this for now (the voice programs will ask again)")
        self.speech_skip.toggled.connect(self._refresh)
        self.speech_status = QLabel("")
        self.speech_status.setWordWrap(True)
        self.speech_bar = QProgressBar()
        self.speech_bar.setRange(0, 0)
        self.speech_bar.hide()
        row = QHBoxLayout()
        row.addWidget(self.speech_run)
        row.addStretch()
        self._page("speech", "Voice access and Narrator", "Windows can talk and listen with a local speech engine.",
                   self.speech_terms, self.speech_agree, row, self.speech_bar, self.speech_status, self.speech_skip)
        # finish
        self.finish_bar = QProgressBar()
        self.finish_bar.setRange(0, 0)
        self._page("finish", "This might take a few minutes", "Don't turn off your PC.", self.finish_bar)
        for key in PAGES:
            self.stack.addWidget(self.widgets[key])

    # ---- flow ----
    def start(self, suggested_name=""):
        self.identity = timeline.profile()
        self.pages = TIMELINE_PAGES if self.identity else PAGES
        self.page = 0
        self.preset = None
        self.speech_state = "idle"
        if self.identity:
            self.name.setText(self.identity["name"])
            self.name.setReadOnly(True)
            self.name_note.setText("Your name comes from the Claude Timeline's profile.")
        else:
            self.name.setText(suggested_name)
            self.name.setReadOnly(False)
            self.name_note.setText("")
            self._fill_fursonas()
        self.computer.setText(user.DEFAULT_COMPUTER)
        self.pw.clear()
        self.pw2.clear()
        self.hint.clear()
        self.handle.clear()
        self.speech_agree.setChecked(False)
        self.speech_skip.setChecked(False)
        self.speech_status.setText("")
        self._show()
        self._place()

    def _fill_fursonas(self):
        self.sona_list.clear()
        it = QListWidgetItem("Be unique (my own name and picture)")
        it.setData(Qt.UserRole, UNIQUE)
        self.sona_list.addItem(it)
        try:
            from claudexp import fursonas
            for pr in fursonas.presets():
                it = QListWidgetItem(fursonas.preset_pixmap(pr, 32), pr.name)
                it.setData(Qt.UserRole, pr.id)
                self.sona_list.addItem(it)
        except Exception:
            pass
        self.sona_list.setCurrentRow(0)

    def _sona_chosen(self, item, _prev=None):
        try:
            from claudexp import fursonas
        except Exception:
            return
        pid = item.data(Qt.UserRole) if item is not None else UNIQUE
        self.preset = fursonas.get(pid) if pid != UNIQUE else None
        pr = self.preset
        if pr is None:
            self.sona_info.setText("Make up your own name and pick your own picture. The residents will get to know "
                                   "you as you chat.")
        else:
            pers = pr.get("personal", default={})
            self.sona_info.setText(f"<b>{pr.name}</b> - {pers.get('location', '')}<br>{pr.get('summary')}")
            self.name.setText(pr.name)
        self._refresh()

    def _show(self):
        key = self.pages[self.page]
        self.stack.setCurrentWidget(self.widgets[key])
        if key == "speech":
            self._speech_show()
        if key == "finish":
            QTimer.singleShot(ms(2500), self._finish)
        self._refresh()

    def _refresh(self, *_):
        key = self.pages[self.page]
        ok = True
        if key == "names":
            ok = bool(self.name.text().strip()) and bool(self.computer.text().strip())
        elif key == "online":
            ok = self.same.isChecked() or bool(self.handle.text().strip())
            self.handle.setEnabled(not self.same.isChecked())
        elif key == "password":
            ok = self.pw.text() == self.pw2.text()
        elif key == "speech":
            ok = self.speech_state == "passed" or (self.speech_skip.isChecked() and self.speech_state != "running")
        self.next.setEnabled(ok)
        self.next.setText({"region": "Yes", "keyboard": "Yes", "privacy": "Accept", "password": "Next" if self.pw.text()
                           else "Skip for now"}.get(key, "Next"))
        self.next.setVisible(key != "finish")
        self.back.setVisible(0 < self.page and key != "finish")

    def _go(self, step):
        if step > 0 and not self.next.isEnabled():
            return
        self.page = max(0, min(len(self.pages) - 1, self.page + step))
        self._show()

    def _finish(self):
        name = self.name.text().strip()
        if self.identity:
            me = self.identity
            fursona = me.get("fursona") or None
            result = {"name": me["name"], "picture": me.get("picture") or (f"fursona:{fursona}" if fursona else None),
                      "handle": me.get("handle") or me["name"], "linked": True, "fursona": fursona}
        else:
            pr = self.preset
            pic = self.pictures.currentItem().data(Qt.UserRole) if self.pictures.currentItem() else None
            result = {"name": name, "picture": f"fursona:{pr.id}" if pr else pic,
                      "handle": pr.handle if pr else (name if self.same.isChecked() else self.handle.text().strip()),
                      "linked": True, "fursona": pr.id if pr else None}
        result.update({"windows_password": self.pw.text(), "hint": self.hint.text().strip(), "online_password": "",
                       "computer": self.computer.text().strip().upper() or user.DEFAULT_COMPUTER,
                       "speech": self.speech_state == "passed"})
        self.finished.emit(result)

    # ---- speech ----
    def _speech_show(self):
        try:
            from . import speechcheck
            self.speech_terms.setHtml(speechcheck.license_html())
            if speechcheck.accepted():
                self.speech_agree.setChecked(True)
        except Exception as exc:
            self.speech_terms.setPlainText(f"The speech engine isn't available on this computer: {exc}")
            self.speech_skip.setChecked(True)
        self._speech_changed()

    def _speech_changed(self, *_):
        running = self.speech_state == "running"
        self.speech_run.setEnabled(self.speech_agree.isChecked() and not running and self.speech_state != "passed")
        self.speech_skip.setEnabled(not running and self.speech_state != "passed")
        self._refresh()

    def _speech_start(self):
        from . import speechcheck
        speechcheck.set_accepted(True)
        self.speech_state = "running"
        self.speech_bar.show()
        self.speech_status.setText("Starting...")
        task = speechcheck.SpeechSetup()
        self.speech_task = task
        task.message.connect(self.speech_status.setText)
        task.passed.connect(self._speech_passed)
        task.failed.connect(self._speech_failed)
        task.finished.connect(self._speech_finished)
        self._speech_changed()
        task.start()

    def _speech_passed(self, heard):
        self.speech_state = "passed"
        self.speech_status.setText(f"Speech works. Windows said a test sentence and heard it back: \"{heard}\"")

    def _speech_failed(self, error):
        self.speech_state = "idle"
        self.speech_status.setText(f"Speech setup did not finish: {error}\nYou can try again, or skip this step.")

    def _speech_finished(self):
        self.speech_bar.hide()
        self.speech_task = None
        self._speech_changed()

    # ---- painting ----
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._go(1)

    def resizeEvent(self, event):
        self._place()

    def _place(self):
        self.dlg.move((self.width() - self.dlg.width()) // 2, (self.height() - self.dlg.height()) // 2)

    def paintEvent(self, event):
        paint_oobe_background(self, QPainter(self))


def paint_oobe_background(widget, p):
    """Windows 11's setup backdrop: near-white with soft blue blooms."""
    p.setRenderHint(QPainter.Antialiasing)
    g = QLinearGradient(0, 0, 0, widget.height())
    g.setColorAt(0, QColor("#F7F9FC"))
    g.setColorAt(1, QColor("#E9EFF8"))
    p.fillRect(widget.rect(), g)
    for cx, cy, rad, colour, alpha in ((0.15, 0.2, 0.45, "#9EC9F5", 150), (0.9, 0.85, 0.5, "#B7D5F7", 130),
                                       (0.8, 0.1, 0.3, "#CFE4FB", 120)):
        rg = QRadialGradient(cx * widget.width(), cy * widget.height(), rad * max(widget.width(), widget.height()))
        c = QColor(colour)
        c.setAlpha(alpha)
        rg.setColorAt(0, c)
        c2 = QColor(colour)
        c2.setAlpha(0)
        rg.setColorAt(1, c2)
        p.fillRect(widget.rect(), rg)
    f = QFont("Segoe UI")
    f.setPixelSize(12)
    p.setFont(f)
    p.setPen(QColor("#5C5C5C"))
    p.drawText(QRectF(0, widget.height() - 30, widget.width(), 20), Qt.AlignCenter, "© 2025 Microsoft")
