"""The AI Helper: a chat panel in Copilot Python Studio that writes, explains and fixes code with a local model."""
import json
import re
import time

from PySide6.QtCore import QThread, QTimer, Signal, Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (QCheckBox, QComboBox, QHBoxLayout, QLabel, QMessageBox, QPlainTextEdit, QPushButton,
                               QTextBrowser, QToolButton, QVBoxLayout, QWidget)

SYSTEM = ("You are the AI Helper inside Copilot Python Studio, an offline Python editor on a Windows PC with no "
          "internet. Programs run on Python 3.12. Installed packages include numpy, Pillow, pygame, pymunk, pytmx, "
          "pygame-menu, pyglet, opensimplex, pathfinding, networkx, imageio, soundfile, sounddevice, pydub, mido, "
          "matplotlib, requests, rich, flask, sympy and tkinter. Never suggest installing anything. "
          "Be concise. When you write code, give the complete working program or function in ONE ```python block, "
          "with a one or two sentence explanation outside it.")
QUICK = [("Explain", "Explain what this code does, step by step, in plain language."),
         ("Fix errors", "Find and fix the bugs or errors in this code. Show the corrected code."),
         ("Improve", "Improve this code: make it cleaner and faster without changing what it does."),
         ("Add comments", "Add short, helpful comments to this code. Show the full commented code.")]
FILE_LIMIT = 12000
CONSOLE_LIMIT = 3000
HISTORY_TURNS = 8
CODE = re.compile(r"```[\w+-]*[ \t]*\r?\n(.*?)```", re.S)


def code_blocks(text):
    return [m.group(1).rstrip("\n") + "\n" for m in CODE.finditer(text)]


class _Stream(QThread):
    chunk = Signal(str)
    failed = Signal(str)

    def __init__(self, model, messages):
        super().__init__()
        self.model, self.messages = model, messages
        self.cancelled = False
        self.tokens, self.tps = 0, 0.0
        self._resp = None

    def stop(self):
        self.cancelled = True
        try:
            if self._resp is not None:
                self._resp.close()
        except Exception:
            pass

    def run(self):
        try:
            from ... import ai_models, llm_server
            body = {"model": self.model, "messages": self.messages, "stream": True, "temperature": 0.3,
                    "cache_prompt": True, "max_tokens": 3000, "chat_template_kwargs": {"enable_thinking": False}}
            begun = time.time()
            self._resp = llm_server.post("/v1/chat/completions", body, stream=True)
            for raw in self._resp:
                if self.cancelled:
                    break
                line = raw.decode("utf-8", "replace").strip()
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    obj = json.loads(data)
                except ValueError:
                    continue
                timings = obj.get("timings") or {}
                if timings:
                    self.tokens = int(timings.get("predicted_n") or 0)
                    self.tps = float(timings.get("predicted_per_second") or 0)
                for choice in obj.get("choices") or []:
                    text = (choice.get("delta") or {}).get("content")
                    if text:
                        self.chunk.emit(text)
            if self.tokens:
                ai_models.record(self.model, self.tokens, self.tps, time.time() - begun, "coding")
        except Exception as exc:
            if not self.cancelled:
                self.failed.emit(str(exc) or exc.__class__.__name__)
        finally:
            try:
                if self._resp is not None:
                    self._resp.close()
            except Exception:
                pass


class AssistantPanel(QWidget):
    """studio: the PythonStudio window (for the current editor and the console)."""

    def __init__(self, studio):
        super().__init__()
        self.studio = studio
        self.history = []                      # [(role, text)] as typed, without the attached file
        self.worker = None
        self.reply = ""
        self.setObjectName("aihelper")

        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)
        root.setSpacing(4)
        head = QHBoxLayout()
        title = QLabel("<b>AI Helper</b>")
        self.models = QComboBox()
        self.models.setMinimumContentsLength(14)
        self.models.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.models.setToolTip("Which model answers (more can be added in Control Panel > AI Models)")
        new = QToolButton()
        new.setText("New chat")
        new.clicked.connect(self.new_chat)
        head.addWidget(title)
        head.addWidget(self.models, 1)
        head.addWidget(new)
        root.addLayout(head)

        self.view = QTextBrowser()
        self.view.setOpenLinks(False)
        root.addWidget(self.view, 1)

        quick = QHBoxLayout()
        quick.setSpacing(2)
        for label, prompt in QUICK:
            b = QToolButton()
            b.setText(label)
            b.clicked.connect(lambda _c=False, p=prompt: self.ask(p, force_file=True))
            quick.addWidget(b)
        quick.addStretch()
        root.addLayout(quick)

        opts = QHBoxLayout()
        self.with_file = QCheckBox("Send current file")
        self.with_file.setChecked(True)
        self.with_console = QCheckBox("Send console output")
        self.with_all = QCheckBox("All open files")
        self.with_all.setToolTip("Also send the other open tabs so the answer fits your whole project")
        opts.addWidget(self.with_file)
        opts.addWidget(self.with_console)
        opts.addWidget(self.with_all)
        opts.addStretch()
        root.addLayout(opts)

        self.input = QPlainTextEdit()
        self.input.setProperty("nospell", False)
        self.input.setFixedHeight(62)
        self.input.setPlaceholderText("Describe what you want, e.g. \"make a snake game with pygame\"  (Ctrl+Enter sends)")
        self.input.installEventFilter(self)
        root.addWidget(self.input)

        row = QHBoxLayout()
        self.send = QPushButton("Send")
        self.send.clicked.connect(self._send_clicked)
        self.insert = QPushButton("Insert code")
        self.insert.setToolTip("Put the code from the last answer at the cursor (or over the selection)")
        self.insert.clicked.connect(self.insert_code)
        self.replace = QPushButton("Replace file")
        self.replace.setToolTip("Replace the whole current file with the code from the last answer (undo with Ctrl+Z)")
        self.replace.clicked.connect(self.replace_file)
        self.copy = QPushButton("Copy code")
        self.copy.clicked.connect(self.copy_code)
        for b in (self.send, self.insert, self.replace, self.copy):
            row.addWidget(b)
        root.addLayout(row)
        self.note = QLabel("")
        self.note.setStyleSheet("QLabel { color: #606060; }")
        self.note.setWordWrap(True)
        root.addWidget(self.note)

        self.repaint_timer = QTimer(self, singleShot=True, interval=120)
        self.repaint_timer.timeout.connect(self._render)
        self._fill_models()
        self._render()
        self._update_buttons()

    # ---- models -----------------------------------------------------------------------------------
    def _fill_models(self):
        self.models.clear()
        try:
            from ... import ai_models, llm_server
            installed = ai_models.installed()
            if not llm_server.available() or not installed:
                self.note.setText(llm_server.status() if hasattr(llm_server, "status") else "No language models found.")
                return
            for m in installed:
                self.models.addItem(f"{m.title}  ({m.size / 1e9:.1f} GB)", m.id)
            want = ai_models.model_for("coding")
            i = self.models.findData(want)
            self.models.setCurrentIndex(max(0, i))
        except Exception as exc:
            self.note.setText(f"AI models unavailable: {exc}")

    def refresh_models(self):
        if self.worker is None:
            self._fill_models()

    # ---- transcript -------------------------------------------------------------------------------
    def eventFilter(self, obj, event):
        if obj is self.input and event.type() == event.Type.KeyPress and event.key() in (Qt.Key_Return, Qt.Key_Enter) \
                and event.modifiers() & Qt.ControlModifier:
            self._send_clicked()
            return True
        return super().eventFilter(obj, event)

    def _render(self):
        parts = []
        for role, text in self.history:
            if role == "user":
                parts.append("\n".join("> " + ln for ln in text.splitlines() or [""]))
            else:
                parts.append(text)
        if self.worker is not None:
            parts.append(self.reply or "*thinking...*")
        if not parts:
            parts = ["Ask for a program, or use the buttons below to explain, fix or improve the open file.\n\n"
                     "The answers come from a model running on this PC, so smaller models are quick but simpler. "
                     "Always read code before you run it."]
        self.view.setMarkdown("\n\n".join(parts))
        bar = self.view.verticalScrollBar()
        bar.setValue(bar.maximum())

    def new_chat(self):
        if self.worker is not None:
            return
        self.history.clear()
        self.reply = ""
        self.note.setText("")
        self._render()
        self._update_buttons()

    def _last_code(self):
        for role, text in reversed(self.history):
            if role == "assistant":
                blocks = code_blocks(text)
                return blocks[-1] if blocks else None
        return None

    def _update_buttons(self):
        have = self._last_code() is not None
        for b in (self.insert, self.replace, self.copy):
            b.setEnabled(have and self.worker is None)
        self.send.setText("Stop" if self.worker is not None else "Send")

    # ---- asking -----------------------------------------------------------------------------------
    def _send_clicked(self):
        if self.worker is not None:
            self.worker.stop()
            return
        text = self.input.toPlainText().strip()
        if text:
            self.input.clear()
            self.ask(text)

    def _context(self, force_file, text=""):
        out = []
        ed = self.studio.editor()
        selected = ""
        if ed is not None:
            selected = ed.textCursor().selectedText().replace("\u2029", "\n").strip()
        if selected:
            out.append("Selected code (the request is about this part):\n```python\n" + selected[:FILE_LIMIT] + "\n```")
        if ed is not None and (force_file or self.with_file.isChecked()):
            code = ed.toPlainText()
            if code.strip():
                if len(code) > FILE_LIMIT:
                    code = code[:FILE_LIMIT] + "\n# ... (file cut here)\n"
                name = ed.path.rsplit("\\", 1)[-1] if ed.path else "untitled.py"
                label = "Whole file for reference" if selected else "Current file"
                out.append(f"{label} ({name}):\n```python\n{code}\n```")
        if self.with_all.isChecked():
            budget = FILE_LIMIT
            for other in self.studio.open_editors():
                if other is ed or budget <= 0:
                    continue
                code = other.toPlainText()[:budget]
                budget -= len(code)
                name = other.path.rsplit("\\", 1)[-1] if other.path else "untitled.py"
                out.append(f"Other open file ({name}):\n```python\n{code}\n```")
        if self.with_console.isChecked():
            console = self.studio.console.toPlainText().strip()
            if console:
                out.append("Console output:\n```\n" + console[-CONSOLE_LIMIT:] + "\n```")
        if ed is not None:
            try:
                from . import apiref
                imports = re.findall(r"^\s*(?:import|from)\s+([\w.]+)", ed.toPlainText(), re.M)
                sheet = apiref.lookup(text + "\n" + selected, imports)
                if sheet:
                    out.append("Exact signatures from the installed packages (trust these over memory):\n" + sheet)
            except Exception:
                pass
        return "\n\n".join(out)

    def ask(self, text, force_file=False):
        if self.worker is not None:
            return
        model = self.models.currentData()
        if not model:
            QMessageBox.information(self, "AI Helper", self.note.text() or "No language model is available.")
            return
        context = self._context(force_file, text)
        sent = f"{text}\n\n{context}" if context else text
        messages = [{"role": "system", "content": SYSTEM}]
        for role, body in self.history[-HISTORY_TURNS:]:
            messages.append({"role": role, "content": body})
        messages.append({"role": "user", "content": sent})
        self.history.append(("user", text))
        self.reply = ""
        self.note.setText("Working... the first answer can take a while if the model has to load.")
        self.worker = _Stream(model, messages)
        self.worker.chunk.connect(self._chunk)
        self.worker.failed.connect(self._failed)
        self.worker.finished.connect(self._done)
        self.worker.start()
        self._update_buttons()
        self._render()

    def _chunk(self, text):
        if not self.reply:
            self.note.setText("Writing...")
        self.reply += text
        if not self.repaint_timer.isActive():
            self.repaint_timer.start()

    def _failed(self, message):
        self.note.setText(f"The AI Helper could not answer: {message}")

    def _done(self):
        worker, self.worker = self.worker, None
        if worker is not None:
            if self.reply.strip():
                self.history.append(("assistant", self.reply))
                speed = f"  ({worker.tps:.0f} tokens/s)" if worker.tps else ""
                self.note.setText(("Stopped." if worker.cancelled else "Done.") + speed)
            elif not self.note.text().startswith("The AI Helper"):
                self.history.pop()                   # nothing came back: drop the question so it can be asked again
                self.note.setText("No answer came back.")
            else:
                self.history.pop()
            worker.deleteLater()
        self.reply = ""
        self._render()
        self._update_buttons()

    # ---- using the answer -------------------------------------------------------------------------
    def fix_error(self, traceback_text):
        """Called by the studio's 'Fix this error' button after a failed run."""
        if self.worker is not None:
            return
        self.studio.show_helper()
        self.ask("My program crashed with this error. Explain the cause briefly and show the corrected code.\n\n"
                 "Error:\n```\n" + traceback_text[-CONSOLE_LIMIT:] + "\n```", force_file=True)

    def _lint(self, code):
        from .app import lint
        return lint(code)

    def insert_code(self):
        code, ed = self._last_code(), self.studio.editor()
        if code is None or ed is None:
            return
        from . import backups
        from .diffview import DiffDialog
        text, cur = ed.toPlainText(), ed.textCursor()
        start, end = cur.selectionStart(), cur.selectionEnd()
        new = text[:start] + code + text[end:]
        if not DiffDialog.ask(self, "Insert code", text, new, self._lint(new), "Insert",
                              "This is what the file will look like:"):
            return
        backups.snapshot(ed.path or "untitled", text, "ai")
        cur.beginEditBlock()
        cur.insertText(code)
        cur.endEditBlock()
        ed.setTextCursor(cur)
        ed.setFocus()
        self.note.setText("Inserted. Press F5 to run it, Ctrl+Z to undo (the old file is also in File > Restore Previous Version).")

    def replace_file(self):
        code, ed = self._last_code(), self.studio.editor()
        if code is None or ed is None:
            return
        from . import backups
        from .diffview import DiffDialog
        old = ed.toPlainText()
        if not DiffDialog.ask(self, "Replace file", old, code, self._lint(code), "Replace file",
                              "Replace everything in this file with the answer?"):
            return
        backups.snapshot(ed.path or "untitled", old, "ai")
        cur = QTextCursor(ed.document())
        cur.beginEditBlock()
        cur.select(QTextCursor.Document)
        cur.insertText(code)
        cur.endEditBlock()
        ed.setFocus()
        self.note.setText("File replaced. Press F5 to run it, Ctrl+Z to undo (the old file is also in File > Restore Previous Version).")

    def copy_code(self):
        from PySide6.QtWidgets import QApplication
        code = self._last_code()
        if code:
            QApplication.clipboard().setText(code)
            self.note.setText("Code copied.")

    def shutdown(self):
        if self.worker is not None:
            self.worker.stop()
            self.worker.wait(2000)
