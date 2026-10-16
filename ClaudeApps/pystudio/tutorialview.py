"""Lesson window for Python Studio: pick a lesson, work in the editor, press Check."""
import json
import threading

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QSplitter,
                               QTextBrowser, QVBoxLayout, QWidget)

from . import lessons
from claudecore import host

PROGRESS = host.data("pystudio") / "pystudio_lessons.json"


def load_progress():
    try:
        return set(json.loads(PROGRESS.read_text(encoding="utf-8")).get("done", []))
    except Exception:
        return set()


def save_progress(done):
    try:
        PROGRESS.parent.mkdir(parents=True, exist_ok=True)
        PROGRESS.write_text(json.dumps({"done": sorted(done)}), encoding="utf-8")
    except OSError:
        pass


class _Bridge(QObject):
    finished = Signal(str, bool, str)


class LessonWindow(QWidget):
    """open_code(title, code) puts text in a new editor tab; get_code() returns the current editor's text;
    ask(text) sends a question to the AI Helper; python() is the runtime's path."""

    def __init__(self, open_code, get_code, ask, python):
        super().__init__()
        self.open_code, self.get_code, self.ask, self.python = open_code, get_code, ask, python
        self.done = load_progress()
        self.current = None
        self.hints_shown = 0
        self.bridge = _Bridge()
        self.bridge.finished.connect(self._checked)

        self.list = QListWidget()
        self.list.setMaximumWidth(250)
        self.list.currentRowChanged.connect(self._select)
        self.progress = QLabel()
        left = QWidget()
        lay = QVBoxLayout(left)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.list)
        lay.addWidget(self.progress)

        self.text = QTextBrowser()
        self.result = QLabel("")
        self.result.setWordWrap(True)
        self.start_btn = QPushButton("Open lesson in editor")
        self.check_btn = QPushButton("Check my work")
        self.hint_btn = QPushButton("Hint")
        self.ask_btn = QPushButton("Ask the AI to explain")
        self.solution_btn = QPushButton("Show solution")
        self.start_btn.clicked.connect(self.start)
        self.check_btn.clicked.connect(self.check)
        self.hint_btn.clicked.connect(self.hint)
        self.ask_btn.clicked.connect(self.explain)
        self.solution_btn.clicked.connect(self.solution)
        buttons = QHBoxLayout()
        for b in (self.start_btn, self.check_btn, self.hint_btn, self.ask_btn, self.solution_btn):
            buttons.addWidget(b)
        right = QWidget()
        rlay = QVBoxLayout(right)
        rlay.setContentsMargins(0, 0, 0, 0)
        rlay.addWidget(self.text, 1)
        rlay.addWidget(self.result)
        rlay.addLayout(buttons)

        split = QSplitter()
        split.addWidget(left)
        split.addWidget(right)
        split.setStretchFactor(1, 1)
        outer = QVBoxLayout(self)
        outer.addWidget(split)

        for lesson in lessons.LESSONS:
            self.list.addItem(QListWidgetItem(""))
        self._refresh_list()
        first = next((i for i, x in enumerate(lessons.LESSONS) if x["id"] not in self.done), 0)
        self.list.setCurrentRow(first)

    def _refresh_list(self):
        for i, lesson in enumerate(lessons.LESSONS):
            mark = "\u2714 " if lesson["id"] in self.done else "    "
            self.list.item(i).setText(mark + lesson["title"])
        self.progress.setText(f"{len(self.done & {x['id'] for x in lessons.LESSONS})} of "
                              f"{len(lessons.LESSONS)} lessons finished")

    def _select(self, row):
        if row < 0:
            return
        self.current = lessons.LESSONS[row]
        self.hints_shown = 0
        self.text.setHtml(self.current["text"] + "<p><i>Press \"Open lesson in editor\", write your answer, "
                                                 "then press \"Check my work\".</i></p>")
        self.result.setText("")

    def start(self):
        if self.current:
            self.open_code(self.current["title"], self.current["starter"])
            self._say("Lesson opened in a new tab. Make your changes there, then press Check.")

    def _say(self, message, good=None):
        color = {True: "#1b7a1b", False: "#b03030"}.get(good, "#000000")
        self.result.setStyleSheet(f"color: {color}; font-weight: bold;")
        self.result.setText(message)

    def check(self):
        code = self.get_code()
        if not self.current or not code.strip():
            self._say("Open the lesson in the editor first.", False)
            return
        self.check_btn.setEnabled(False)
        self._say("Checking...")
        lesson = self.current

        def work():
            try:
                ok, message = lessons.check(self.python(), lesson, code)
            except Exception as exc:
                ok, message = False, f"Could not run the check: {exc}"
            self.bridge.finished.emit(lesson["id"], ok, message)
        threading.Thread(target=work, daemon=True).start()

    def _checked(self, lesson_id, ok, message):
        self.check_btn.setEnabled(True)
        if ok:
            self.done.add(lesson_id)
            save_progress(self.done)
            self._refresh_list()
            ids = [x["id"] for x in lessons.LESSONS]
            if len(self.done & set(ids)) == len(ids):
                message += " You finished every lesson!"
            elif lesson_id == self.current["id"]:
                message += " Pick the next lesson when you're ready."
        self._say(message, ok)

    def hint(self):
        hints = self.current["hints"] if self.current else []
        if not hints:
            return
        n = min(self.hints_shown, len(hints) - 1)
        self.hints_shown += 1
        self._say(f"Hint {n + 1} of {len(hints)}: {hints[n]}")

    def explain(self):
        if not self.current:
            return
        code = self.get_code()
        plain = self.text.toPlainText().split("Press \"Open lesson")[0].strip()
        self.ask("I'm a beginner learning Python. Here is my lesson:\n\n" + plain +
                 "\n\nExplain the idea in simple words with one small example. Do not give the full answer. "
                 + ("Here is what I have so far:\n" + code if code.strip() else ""))

    def solution(self):
        if self.current:
            self.open_code(self.current["title"] + " (solution)", self.current["solution"])
            self._say("The solution is open in a new tab. Read it, then try typing it out yourself.")
