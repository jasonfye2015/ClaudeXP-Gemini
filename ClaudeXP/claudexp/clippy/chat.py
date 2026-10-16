"""Chat with Clippy: a proper window (tray icon > Chat with Clippy, or the Chat... button in his balloon).
The history is kept in data/clippy_chat.json. '/remind 10 call mom' sets a reminder."""
import html
import json
import re

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QComboBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextBrowser, QVBoxLayout,
                               QWidget)
from shiboken6 import isValid

from ..paths import DATA
from ..wm import XPWindow
from . import art, brain, moods

HISTORY = DATA / "clippy_chat.json"
KEEP = 60
_open = {}


def load():
    try:
        data = json.loads(HISTORY.read_text(encoding="utf-8"))
        return [m for m in data if m.get("role") in ("user", "assistant") and m.get("content")][-KEEP:]
    except (OSError, ValueError, AttributeError):
        return []


def save(messages):
    try:
        HISTORY.parent.mkdir(parents=True, exist_ok=True)
        HISTORY.write_text(json.dumps(messages[-KEEP:], indent=1), encoding="utf-8")
    except OSError:
        pass


class ChatBody(QWidget):
    def __init__(self, desktop, clippy):
        super().__init__()
        self.desktop = desktop
        self.clippy = clippy
        self.messages = load()
        self.job = None
        self.streaming = ""
        v = QVBoxLayout(self)
        v.setContentsMargins(8, 8, 8, 8)
        top = QHBoxLayout()
        self.portrait = QLabel()
        top.addWidget(self.portrait)
        self.title = QLabel()
        top.addWidget(self.title, 1)
        top.addWidget(QLabel("Mood:"))
        self.mood = QComboBox()
        for key in moods.MOOD_ORDER:
            self.mood.addItem(f"{moods.MOODS[key]['emoji']} {moods.MOODS[key]['label']}", key)
        self.mood.addItem("🎲 Moody (changes by itself)", moods.MOODY)
        self.mood.setCurrentIndex(max(0, self.mood.findData(clippy.cfg.get("mood", "happy"))))
        self.mood.activated.connect(self._mood_picked)
        top.addWidget(self.mood)
        clear = QPushButton("Clear")
        clear.clicked.connect(self.clear)
        top.addWidget(clear)
        v.addLayout(top)
        self.view = QTextBrowser()
        self.view.setOpenExternalLinks(False)
        v.addWidget(self.view, 1)
        row = QHBoxLayout()
        self.edit = QLineEdit()
        self.edit.setPlaceholderText("Say something to Clippy...   (/remind 10 stretch  sets a reminder)")
        self.edit.returnPressed.connect(self.send)
        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self._send_or_stop)
        row.addWidget(self.edit, 1)
        row.addWidget(self.send_btn)
        v.addLayout(row)
        self.refresh_header()
        self.render()
        self.edit.setFocus()

    # ---- header --------------------------------------------------------------------------------------------
    def refresh_header(self):
        c = self.clippy
        mood = c.mood
        info = moods.mood_info(mood)
        self.portrait.setPixmap(art.icon_pixmap(40, art.still_pose(mood, c.cfg.get("wire", "silver"),
                                                                    c.cfg.get("accessory", "none"))))
        self.title.setText(f"<b>Clippy</b><br><span style='color:#555'>feeling {info['label'].lower()}</span>")
        idx = self.mood.findData(c.cfg.get("mood", "happy"))
        if idx >= 0 and idx != self.mood.currentIndex():
            self.mood.setCurrentIndex(idx)

    def _mood_picked(self, _i):
        self.clippy.set_mood(self.mood.currentData())
        self.refresh_header()

    # ---- the transcript ------------------------------------------------------------------------------------
    def render(self):
        fill, border, text, link = moods.mood_info(self.clippy.mood)["balloon"]
        parts = []
        for m in self.messages:
            parts.append(self._bubble(m["role"], m["content"], fill, text))
        if self.streaming:
            parts.append(self._bubble("assistant", self.streaming, fill, text))
        elif self.job is not None:
            parts.append(self._bubble("assistant", "...", fill, text))
        if not parts:
            parts.append("<p style='color:#777'>Say hello! Clippy has been waiting. A long time. Quietly.</p>")
        self.view.setHtml("<body style='font-family:Tahoma;font-size:11px'>" + "".join(parts) + "</body>")
        bar = self.view.verticalScrollBar()
        bar.setValue(bar.maximum())

    @staticmethod
    def _bubble(role, content, fill, text):
        body = html.escape(content).replace("\n", "<br>")
        if role == "user":
            return (f"<table width='100%'><tr><td align='right'><table><tr><td bgcolor='#D6E4FF' style='padding:5px'>"
                    f"<b>You</b><br>{body}</td></tr></table></td></tr></table>")
        return (f"<table width='100%'><tr><td align='left'><table><tr><td bgcolor='{fill}' style='padding:5px;"
                f" color:{text}'><b>Clippy</b><br>{body}</td></tr></table></td></tr></table>")

    def note(self, text):
        """A line from Clippy that didn't come from the model (reminders, errors)."""
        self.messages.append({"role": "assistant", "content": text})
        save(self.messages)
        self.render()

    # ---- talking -------------------------------------------------------------------------------------------
    def _send_or_stop(self):
        if self.job is not None:
            self.stop()
        else:
            self.send()

    def stop(self):
        job, self.job = self.job, None
        if job is not None:
            try:
                job.stop()
            except Exception:
                pass
        if self.streaming:
            self.messages.append({"role": "assistant", "content": self.streaming})
            save(self.messages)
        self.streaming = ""
        self.send_btn.setText("Send")
        self.render()

    def send(self):
        text = self.edit.text().strip()
        if not text or self.job is not None:
            return
        self.edit.clear()
        m = re.match(r"/remind\s+(\d+)\s*(?:m|min|minutes?)?\s+(.+)", text, re.I)
        if m:
            minutes, what = int(m.group(1)), m.group(2).strip()
            self.clippy.add_reminder(minutes, what)
            self.messages.append({"role": "user", "content": text})
            self.messages.append({"role": "assistant", "content": f"Got it! I'll remind you in {minutes} minute"
                                                                  f"{'s' if minutes != 1 else ''}: {what}"})
            save(self.messages)
            self.render()
            return
        self.messages.append({"role": "user", "content": text})
        self.streaming = ""
        self.send_btn.setText("Stop")
        job = brain.chat(self.messages[-24:], self._chunk, self._done, mood=self.clippy.mood,
                         aware=self.clippy.aware())
        if job is None:                                             # _done already ran
            return
        self.job = job
        self.clippy.widget.play("think")
        self.render()

    def _chunk(self, so_far):
        if self.job is None and not self.streaming and not so_far:
            return
        self.streaming = brain.clean_chat(so_far)
        self.render()

    def _done(self, text, err):
        self.job = None
        self.send_btn.setText("Send")
        reply = brain.clean_chat(text or self.streaming)
        self.streaming = ""
        if err or not reply:
            reply = "(Clippy's language model isn't available right now. Try the Local Storage models, or " \
                    "come back later!)" if err == "no model" else (reply or "Hmm. I lost my train of thought.")
            if err and err != "no model":
                reply = f"{reply}\n({err})" if reply else f"({err})"
        self.messages.append({"role": "assistant", "content": reply})
        brain.remember(reply)
        save(self.messages)
        self.render()
        self.clippy.widget.play("eyebrows")

    def clear(self):
        self.stop()
        self.messages = []
        save(self.messages)
        self.render()

    def closeEvent(self, event):
        self.stop()
        event.accept()


def open_chat(desktop, clippy):
    win = _open.get("win")
    if win is None or not isValid(win):
        body = ChatBody(desktop, clippy)
        win = XPWindow(desktop, "Chat with Clippy", body, QIcon(art.icon_pixmap(16)), (440, 520))
        body.frame = win
        _open["win"] = win
        _open["body"] = body
    desktop.open_window(win)
    return win


def current():
    """The open chat body, or None."""
    win, body = _open.get("win"), _open.get("body")
    return body if win is not None and isValid(win) and body is not None else None
