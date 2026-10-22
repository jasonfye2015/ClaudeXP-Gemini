"""'Set Up Windows': the pages after the installation's last restart - your user name and the computer's name, a
password, the product key, updates, the time zone, the network location, speech - and, for a computer outside the
Timeline, who you are online (your fursona or your own name and picture). In the Claude Timeline the launcher's
Profile answers the identity questions, so those pages are skipped."""
from PySide6.QtCore import QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPixmap
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget,
                               QListWidgetItem, QProgressBar, QPushButton, QRadioButton, QStackedWidget, QTextBrowser,
                               QVBoxLayout, QWidget)

from . import ms
from .. import timeline, user
from ..paths import IMAGES
from .install import DIALOG_CSS

PAGES = ["names", "fursona", "online", "password", "key", "updates", "timezone", "network", "speech", "finish"]
TIMELINE_PAGES = ["names", "password", "key", "updates", "timezone", "network", "speech", "finish"]
ZONES = ["(UTC-08:00) Pacific Time (US & Canada)", "(UTC-07:00) Mountain Time (US & Canada)",
         "(UTC-06:00) Central Time (US & Canada)", "(UTC-05:00) Eastern Time (US & Canada)",
         "(UTC) Dublin, Edinburgh, Lisbon, London", "(UTC+01:00) Amsterdam, Berlin, Rome, Vienna",
         "(UTC+10:00) Canberra, Melbourne, Sydney"]
UNIQUE = "__unique__"


class Oobe(QWidget):
    finished = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.background = QPixmap(str(IMAGES / "shutdown" / "shutdown-screen.jpg"))
        self.identity = None
        self.pages = PAGES
        self.page = 0
        self.preset = None
        self.speech_state = "idle"
        self.speech_task = None
        self.dlg = QFrame(self)
        self.dlg.setObjectName("dlg")
        self.dlg.setStyleSheet(DIALOG_CSS + """
QLineEdit { font-family: 'Segoe UI'; font-size: 12px; padding: 3px; border: 1px solid #ABADB3; }
QListWidget { font-family: 'Segoe UI'; font-size: 12px; border: 1px solid #ABADB3; }
QRadioButton { font-family: 'Segoe UI'; font-size: 12px; }
QTextBrowser { font-family: 'Segoe UI'; font-size: 11px; border: 1px solid #ABADB3; }
""")
        self.dlg.setFixedSize(660, 490)
        v = QVBoxLayout(self.dlg)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        head = QWidget()
        head.setFixedHeight(34)
        head.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFFFFF, stop:1 #E9EFF7);")
        hl = QHBoxLayout(head)
        hl.setContentsMargins(10, 0, 10, 0)
        hl.addWidget(QLabel("Set Up Windows"))
        v.addWidget(head)
        self.stack = QStackedWidget()
        v.addWidget(self.stack, 1)
        foot = QWidget()
        foot.setFixedHeight(48)
        foot.setStyleSheet("background: #F0F0F0; border-top: 1px solid #DFDFDF;")
        fl = QHBoxLayout(foot)
        fl.setContentsMargins(12, 8, 12, 8)
        fl.addStretch()
        self.back = QPushButton("Back")
        self.next = QPushButton("Next")
        self.back.clicked.connect(lambda: self._go(-1))
        self.next.clicked.connect(lambda: self._go(1))
        fl.addWidget(self.back)
        fl.addWidget(self.next)
        v.addWidget(foot)
        self.widgets = {}
        self._build()

    # ---- building ----
    def _page(self, key, title, *items):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(28, 22, 28, 16)
        v.setSpacing(10)
        t = QLabel(title)
        t.setObjectName("head")
        t.setWordWrap(True)
        v.addWidget(t)
        for x in items:
            if isinstance(x, QWidget):
                v.addWidget(x)
            else:
                v.addLayout(x)
        v.addStretch()
        self.widgets[key] = w
        return w

    def _build(self):
        # names
        self.name = QLineEdit()
        self.computer = QLineEdit(user.DEFAULT_COMPUTER)
        self.name.textChanged.connect(self._refresh)
        self.computer.textChanged.connect(self._refresh)
        self.name_note = QLabel("")
        self.name_note.setObjectName("grey")
        self._page("names", "Choose a user name for your account and name your computer to distinguish it on the "
                            "network.", QLabel("Type a user name (for example, John):"), self.name,
                   QLabel("Type a computer name:"), self.computer, self.name_note)
        # fursona (outside the Timeline)
        self.sona_list = QListWidget()
        self.sona_list.setFixedHeight(150)
        self.sona_info = QLabel("")
        self.sona_info.setWordWrap(True)
        self.sona_list.currentItemChanged.connect(self._sona_chosen)
        self._page("fursona", "Choose your fursona", QLabel("Pick a ready-made fursona (its own name, picture, profile "
                                                            "and online accounts), or be unique."),
                   self.sona_list, self.sona_info)
        # online name and picture
        self.handle = QLineEdit()
        self.same = QCheckBox("Use my Windows user name online too")
        self.same.setChecked(True)
        self.same.toggled.connect(self._refresh)
        self.pictures = QListWidget()
        self.pictures.setViewMode(QListWidget.IconMode)
        self.pictures.setIconSize(QPixmap(48, 48).size())
        self.pictures.setFixedHeight(130)
        self.pictures.setMovement(QListWidget.Static)
        from PySide6.QtGui import QIcon
        for pic_id, _label, pm in user.pictures():
            it = QListWidgetItem(QIcon(pm), "")
            it.setData(Qt.UserRole, pic_id)
            self.pictures.addItem(it)
        self.pictures.setCurrentRow(0)
        self._page("online", "Your name online, and a picture for your account",
                   QLabel("The messengers, IRC and the MUCK sign in with this name:"), self.handle, self.same,
                   QLabel("Pick a picture for your user account:"), self.pictures)
        # password
        self.pw = QLineEdit()
        self.pw.setEchoMode(QLineEdit.Password)
        self.pw2 = QLineEdit()
        self.pw2.setEchoMode(QLineEdit.Password)
        self.hint = QLineEdit()
        for e in (self.pw, self.pw2):
            e.textChanged.connect(self._refresh)
        self._page("password", "Set a password for your account",
                   QLabel("Creating a password is a smart security precaution that helps protect your user account "
                          "from unwanted users. Be sure to remember your password or keep it in a safe place."),
                   QLabel("Type a password (recommended):"), self.pw, QLabel("Retype your password:"), self.pw2,
                   QLabel("Type a password hint (required):"), self.hint)
        # product key
        self.key = QLineEdit("XXXXX-XXXXX-XXXXX-XXXXX-XXXXX")
        self.activate = QCheckBox("Automatically activate Windows when I'm online")
        self.activate.setChecked(True)
        self._page("key", "Type your Windows product key",
                   QLabel("You can find your Windows product key on a label included with the package that came "
                          "with your copy of Windows. The label might also be on your computer case."),
                   self.key, self.activate)
        # updates
        self.upd = []
        box = QVBoxLayout()
        for text in ("Use recommended settings\nInstall important and recommended updates, help make Internet "
                     "browsing safer, check online for solutions to problems, and help Microsoft improve Windows.",
                     "Install important updates only\nOnly install security updates and other important updates "
                     "for Windows.", "Ask me later\nUntil you decide, your computer might be vulnerable to security "
                                     "threats."):
            r = QRadioButton(text)
            box.addWidget(r)
            self.upd.append(r)
        self.upd[0].setChecked(True)
        self._page("updates", "Help protect your computer and improve Windows automatically", box)
        # time zone
        self.zone = QComboBox()
        self.zone.addItems(ZONES)
        self.zone.setCurrentIndex(3)
        self.dst = QCheckBox("Automatically adjust clock for Daylight Saving Time")
        self.dst.setChecked(True)
        self.clock_label = QLabel("")
        self._page("timezone", "Review your time and date settings", QLabel("Time zone:"), self.zone, self.dst,
                   self.clock_label)
        # network location
        self.net = []
        box = QVBoxLayout()
        for text in ("Home network\nIf all the computers on this network are at your home, and you recognize them, "
                     "this is a trusted home network.", "Work network\nIf all the computers on this network are at "
                     "your workplace, and you recognize them, this is a trusted work network.", "Public network\n"
                     "If you don't recognize all the computers on the network (for example, you're in a coffee shop "
                     "or airport, or you have mobile broadband), this is a public network and is not trusted."):
            r = QRadioButton(text)
            box.addWidget(r)
            self.net.append(r)
        self.net[0].setChecked(True)
        self._page("network", "Select your computer's current location", box)
        # speech
        self.speech_terms = QTextBrowser()
        self.speech_terms.setFixedHeight(120)
        self.speech_agree = QCheckBox("I accept the speech models' licences")
        self.speech_agree.toggled.connect(self._speech_changed)
        self.speech_run = QPushButton("Set up speech and test it")
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
        self._page("speech", "Speech and voice", QLabel("Windows can talk and listen with a local speech engine."),
                   self.speech_terms, self.speech_agree, row, self.speech_bar, self.speech_status, self.speech_skip)
        # finish
        self.finish_bar = QProgressBar()
        self.finish_bar.setRange(0, 0)
        self._page("finish", "Windows is finalizing your settings", self.finish_bar)
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
        if key == "timezone":
            from .. import clock
            self.clock_label.setText(f"Date: {clock.long_date_text()}      Time: {clock.time_text()}")
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
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        if self.background.isNull():
            g = QLinearGradient(0, 0, 0, self.height())
            g.setColorAt(0, QColor("#1F5FA8"))
            g.setColorAt(1, QColor("#0B2E5C"))
            p.fillRect(self.rect(), g)
        else:
            scale = max(self.width() / self.background.width(), self.height() / self.background.height())
            w, h = self.background.width() * scale, self.background.height() * scale
            p.drawPixmap(QRectF((self.width() - w) / 2, (self.height() - h) / 2, w, h), self.background,
                         QRectF(self.background.rect()))
        f = QFont("Segoe UI")
        f.setPixelSize(12)
        p.setFont(f)
        p.setPen(QColor(255, 255, 255, 200))
        p.drawText(QRectF(0, self.height() - 30, self.width(), 20), Qt.AlignCenter,
                   "© 2009 Microsoft Corporation. All rights reserved.")
