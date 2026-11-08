"""A plain place to talk with her (F4), for building the game - until her scenes (phase 3d) have their own window, her
own font, the letterbox and the dressing. Her lines large, his smaller; he types (a language model writes her words)
or chooses (the script). The night waits while it's open. Esc, or Done, closes it."""
import queue

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea, QVBoxLayout, QWidget

from . import fonts

STYLE = """
QWidget#talk { background: transparent; }
QLabel { background: transparent; }
QLineEdit { color: #EADCC4; background: rgba(12, 8, 9, 220); border: 1px solid #6A4E36; border-radius: 4px;
    padding: 8px; font-family: Georgia; font-size: 15px; }
QPushButton { color: #E6D8C2; background: rgba(40, 26, 20, 200); border: 1px solid #6A4E36; border-radius: 4px;
    padding: 7px 14px; font-family: Georgia; font-size: 14px; text-align: left; }
QPushButton:hover { background: rgba(80, 46, 30, 220); border-color: #A07A54; }
QScrollArea { background: transparent; border: none; }
"""


class Talk(QWidget):
    def __init__(self, shell, conversation, scene="audience"):
        super().__init__(shell)
        self.shell, self.talk = shell, conversation
        self.setObjectName("talk")
        self.setStyleSheet(STYLE)
        self.replies = queue.Queue()
        self.waiting = False
        lay = QVBoxLayout(self)
        lay.setContentsMargins(120, 40, 120, 30)
        head = QLabel("Talking with her - a plain stand-in for her scenes (phase 3d)  ·  her words: "
                      + ("a language model" if conversation.mode == "model" else "the script"))
        head.setStyleSheet("color: #8E7E6C; font-family: Georgia; font-size: 12px;")
        lay.addWidget(head)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.viewport().setStyleSheet("background: transparent;")
        self.body = QWidget()
        self.body.setStyleSheet("background: transparent;")
        self.lines = QVBoxLayout(self.body)
        self.lines.addStretch(1)
        self.scroll.setWidget(self.body)
        lay.addWidget(self.scroll, 1)
        self.answer = QVBoxLayout()
        lay.addLayout(self.answer)
        row = QHBoxLayout()
        row.addStretch(1)
        done = QPushButton("Done")
        done.clicked.connect(self.close_talk)
        row.addWidget(done)
        lay.addLayout(row)
        self._thinking()
        self.talk.open(scene, lambda text, choices: self.replies.put((text, choices)))
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._poll)
        self.timer.start(60)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(4, 2, 4, 205))
        p.end()

    def _add(self, who, text):
        lab = QLabel(text)
        lab.setWordWrap(True)
        rec = self.shell.records
        if who == "her":
            lab.setFont(fonts.her(rec, 30))                   # (her hand: Italianno, larger)
            lab.setStyleSheet("color: #E9D2C4; padding: 4px 0;")
        else:
            lab.setFont(fonts.his(rec, 13))
            lab.setStyleSheet("color: #A9B8C4; padding: 2px 0 8px 40px;")
        self.lines.addWidget(lab)
        QTimer.singleShot(30, lambda: self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum()))

    def _clear_answer(self):
        while self.answer.count():
            w = self.answer.takeAt(0).widget()
            if w is not None:
                w.deleteLater()

    def _thinking(self):
        self._clear_answer()
        self.waiting = True
        lab = QLabel("...")
        lab.setStyleSheet("color: #8E7E6C; font-family: Georgia; font-size: 18px;")
        self.answer.addWidget(lab)

    def _poll(self):
        try:
            text, choices = self.replies.get_nowait()
        except queue.Empty:
            return
        self.waiting = False
        self._add("her", text)
        audio = self.shell.view.audio
        if audio is not None:
            audio.say(text)
        self._clear_answer()
        if choices is None:                                    # (the scene is over)
            lab = QLabel("(She sends you on.)" if self.talk.ended != "cold" else "(She has finished with you, for now.)")
            lab.setStyleSheet("color: #8E7E6C; font-family: Georgia; font-size: 13px;")
            self.answer.addWidget(lab)
        elif choices:
            for i, c in enumerate(choices):
                b = QPushButton(c)
                b.setCursor(Qt.PointingHandCursor)
                b.clicked.connect(lambda _x=False, i=i, c=c: self._chose(i, c))
                self.answer.addWidget(b)
        else:
            edit = QLineEdit()
            edit.setPlaceholderText("Answer her...")
            edit.returnPressed.connect(lambda: self._typed(edit.text()))
            self.answer.addWidget(edit)
            edit.setFocus()

    def _chose(self, i, text):
        self._add("him", text)
        self._thinking()
        self.talk.choose(i, lambda t, ch: self.replies.put((t, ch)))

    def _typed(self, text):
        if not text.strip() or self.waiting:
            return
        self._add("him", text.strip())
        self._thinking()
        self.talk.say(text, lambda t, ch: self.replies.put((t, ch)))

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.close_talk()
            return
        super().keyPressEvent(e)

    def close_talk(self):
        self.timer.stop()
        self.shell.set_panel(None)
        self.shell.view.setFocus()
