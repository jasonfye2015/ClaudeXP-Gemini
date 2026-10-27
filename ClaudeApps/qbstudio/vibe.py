"""Vibe coding: describe a program and the AI writes it in QBasic, the studio checks that it compiles and runs it, and
anything that goes wrong (a syntax error, a crash, with its line and what was on the screen) goes straight back to the
AI to fix - again and again until it works or the tries run out. Then keep talking: "make the ball faster", "add a
high score" - each request changes the program you have.

It uses the Timeline's own models (the llama.cpp server in ClaudeCore), the same way Copilot Python Studio's AI Helper
does."""
import re

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtWidgets import (QCheckBox, QComboBox, QHBoxLayout, QLabel, QMessageBox, QPlainTextEdit, QPushButton,
                               QSpinBox, QTextBrowser, QToolButton, QVBoxLayout, QWidget)

SYSTEM = """You write programs in QBasic (Microsoft QBasic 1.1) for Claude QBasic Studio, which runs them in its own
QBasic interpreter on Windows. Always answer with the COMPLETE program in ONE ```qbasic code block, then one or two
short sentences about it. Never leave parts out ("..." or "rest unchanged").

What the interpreter supports:
- PRINT (; , TAB SPC USING), INPUT, LINE INPUT, INKEY$ (arrows are CHR$(0)+"H"/"P"/"K"/"M", Esc CHR$(27)), CLS,
  LOCATE, COLOR, SLEEP, BEEP, SOUND, PLAY, RANDOMIZE TIMER, RND, TIMER, DATE$, TIME$
- IF/ELSEIF/ELSE/END IF (block and one-line), SELECT CASE (CASE IS, TO, lists), FOR/NEXT, DO/LOOP WHILE/UNTIL,
  WHILE/WEND, EXIT FOR/DO/SUB/FUNCTION, GOTO, GOSUB/RETURN, labels and line numbers, ON ... GOTO/GOSUB,
  ON ERROR GOTO / RESUME NEXT, END
- SUB and FUNCTION (arguments by reference), CALL, DECLARE, DIM SHARED, SHARED, STATIC, CONST, DEFINT A-Z,
  DIM arrays (any dimensions, a TO b), REDIM, TYPE ... END TYPE records, DATA/READ/RESTORE, SWAP
- String and maths functions: LEN LEFT$ RIGHT$ MID$ INSTR UCASE$ LCASE$ LTRIM$ RTRIM$ STR$ VAL CHR$ ASC STRING$
  SPACE$ HEX$ INT FIX CINT ABS SGN SQR SIN COS TAN ATN EXP LOG, MOD, \\ (integer divide), ^
- Graphics: SCREEN 0 (text 80x25), 1, 2, 7 (320x200, 16 colours, pages), 8, 9, 12 (640x480, 16 colours),
  13 (320x200, 256 colours); PSET, PRESET, LINE (B, BF), CIRCLE, PAINT, DRAW, POINT, GET/PUT sprites, PALETTE,
  PCOPY with SCREEN 7,0,1,0 for flicker-free animation, WAIT &H3DA, 8 to pace to the screen's refresh
- Files next to the program: OPEN FOR INPUT/OUTPUT/APPEND AS #1, PRINT #, WRITE #, INPUT #, LINE INPUT #, EOF, CLOSE
NOT supported: DEF FN (use FUNCTION), random-access files (GET #/PUT #), CHAIN, SHELL, CALL ABSOLUTE, mouse, $INCLUDE.

VERY IMPORTANT: a SUB or FUNCTION can't see the main program's variables. Anything the SUBs and the main program both
use (positions, scores, arrays) must be declared at the top with DIM SHARED, e.g. DIM SHARED paddleX, score - or be
passed in as arguments. Otherwise inside the SUB it's a different variable that is always 0.
Write it so it runs: no reserved words as variable names (NAME, KEY, TIMER, COLOR, SCREEN, LINE, STRING ...),
give string variables a $, end a block IF with END IF, use a SUB/FUNCTION's name exactly, and for games read the keys
with INKEY$ inside a DO ... LOOP and pace it with TIMER or WAIT &H3DA, 8 so it doesn't run too fast. Prefer clear,
commented, well-structured code with SUBs."""

QUICK = [("Explain", "Explain what this program does, step by step, in plain language. Don't rewrite it."),
         ("Fix it", "Find and fix the bugs in this program."),
         ("Comment", "Add short, helpful comments to this program."),
         ("Polish", "Make this program nicer: better colours, layout and sound, a title screen and clearer messages, "
                    "without changing what it does.")]
CODE = re.compile(r"```[\w+-]*[ \t]*\r?\n(.*?)```", re.S)
HISTORY_TURNS = 6
SCREEN_LIMIT = 1500


def code_blocks(text):
    return [m.group(1).rstrip("\n") + "\n" for m in CODE.finditer(text)]


class VibePanel(QWidget):
    """studio: the QBasicStudio (current editor, compiling, running and its outcome)."""
    status = Signal(str)

    def __init__(self, studio):
        super().__init__()
        self.studio = studio
        self.history = []               # [(role, text)]
        self.worker = None
        self.reply = ""
        self.job = None                 # the vibe loop in progress: {"tries": n, "phase": ...}
        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(4)
        head = QHBoxLayout()
        title = QLabel("<b>✨ Vibe Coder</b>")
        self.models = QComboBox()
        self.models.setMinimumContentsLength(12)
        self.models.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.models.setToolTip("Which model writes the code (more can be added in Control Panel > AI Models)")
        new = QToolButton()
        new.setText("New chat")
        new.setToolTip("Forget the conversation (the program stays)")
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
            b.clicked.connect(lambda _c=False, p=prompt, lab=label: self.quick(lab, p))
            quick.addWidget(b)
        quick.addStretch()
        root.addLayout(quick)
        opts = QHBoxLayout()
        self.target = QComboBox()
        self.target.addItems(["Change this program", "Write a new program"])
        self.target.setToolTip("Build on the program in the editor, or start a new one in a new tab")
        self.autorun = QCheckBox("Run it")
        self.autorun.setChecked(True)
        self.autorun.setToolTip("Run the program as soon as it's written, and fix it if it crashes")
        self.tries = QSpinBox()
        self.tries.setRange(0, 8)
        self.tries.setValue(4)
        self.tries.setPrefix("fix tries ")
        self.tries.setToolTip("How many times the AI may fix its own mistakes before it stops and asks you")
        opts.addWidget(self.target, 1)
        opts.addWidget(self.autorun)
        opts.addWidget(self.tries)
        root.addLayout(opts)
        self.input = QPlainTextEdit()
        self.input.setFixedHeight(70)
        self.input.setPlaceholderText('Describe what you want, e.g. "a snake game with a high score" or "make the '
                                      'stars twinkle"  (Ctrl+Enter)')
        self.input.installEventFilter(self)
        root.addWidget(self.input)
        row = QHBoxLayout()
        self.go = QPushButton("✨ Vibe it")
        self.go.setToolTip("Write (or change) the program, check it, run it and fix it until it works")
        self.go.clicked.connect(self._go_clicked)
        self.ask_btn = QPushButton("Just ask")
        self.ask_btn.setToolTip("A question about QBasic or the program - nothing is changed")
        self.ask_btn.clicked.connect(self._ask_clicked)
        self.apply_btn = QPushButton("Use code")
        self.apply_btn.setToolTip("Put the code from the last answer into the editor")
        self.apply_btn.clicked.connect(self.apply_last)
        for b in (self.go, self.ask_btn, self.apply_btn):
            row.addWidget(b)
        root.addLayout(row)
        self.note = QLabel("")
        self.note.setWordWrap(True)
        self.note.setStyleSheet("QLabel { color: #606060; }")
        root.addWidget(self.note)
        self.repaint_timer = QTimer(self, singleShot=True, interval=120)
        self.repaint_timer.timeout.connect(self._render)
        self._fill_models()
        self._render()
        self._update_buttons()

    # ---- models ----
    def _fill_models(self):
        self.models.clear()
        try:
            from claudecore.ai import ai_models, llm_server
            installed = ai_models.installed()
            if not llm_server.available() or not installed:
                self.note.setText(llm_server.status() if hasattr(llm_server, "status") else
                                  "No language models found - add one in Control Panel > AI Models.")
                return
            for m in installed:
                self.models.addItem(f"{m.title}  ({m.size / 1e9:.1f} GB)", m.id)
            want = ai_models.model_for("coding")
            i = self.models.findData(want)
            self.models.setCurrentIndex(max(0, i))
        except Exception as exc:
            self.note.setText(f"AI models unavailable: {exc}")

    # ---- the transcript ----
    def eventFilter(self, obj, event):
        if obj is self.input and event.type() == event.Type.KeyPress and event.key() in (Qt.Key_Return, Qt.Key_Enter) \
                and event.modifiers() & Qt.ControlModifier:
            self._go_clicked()
            return True
        return super().eventFilter(obj, event)

    def _render(self):
        parts = []
        for role, text in self.history:
            if role == "user":
                parts.append("\n".join("> " + ln for ln in text.splitlines() or [""]))
            elif role == "system":
                parts.append(f"*{text}*")
            else:
                parts.append(_shorten_code(text))
        if self.worker is not None:
            parts.append(_shorten_code(self.reply) if self.reply else "*writing...*")
        if not parts:
            parts = ["**Describe a program and press ✨ Vibe it.** The AI writes it in QBasic, the studio runs it, "
                     "and if anything goes wrong the AI is shown the error and fixes it - by itself - until it works.",
                     "Then keep going: *\"make it two players\"*, *\"add sound\"*, *\"slow the ball down\"*. Each "
                     "request changes the program in the editor (Ctrl+Z undoes a change).",
                     "The code comes from a model on this PC: smaller ones are quicker but simpler."]
        self.view.setMarkdown("\n\n".join(parts))
        bar = self.view.verticalScrollBar()
        bar.setValue(bar.maximum())

    def new_chat(self):
        if self.worker is not None:
            return
        self.history.clear()
        self.job = None
        self.note.setText("")
        self._render()
        self._update_buttons()

    def _update_buttons(self):
        busy = self.worker is not None or self.job is not None
        self.go.setText("Stop" if busy else "✨ Vibe it")
        self.ask_btn.setEnabled(not busy)
        self.apply_btn.setEnabled(not busy and self._last_code() is not None)

    def _last_code(self):
        for role, text in reversed(self.history):
            if role == "assistant":
                blocks = code_blocks(text)
                return blocks[-1] if blocks else None
        return None

    # ---- asking ----
    def _go_clicked(self):
        if self.worker is not None or self.job is not None:
            self.stop()
            return
        text = self.input.toPlainText().strip()
        if not text:
            self.input.setFocus()
            return
        self.input.clear()
        self.vibe(text)

    def _ask_clicked(self):
        text = self.input.toPlainText().strip()
        if not text:
            return
        self.input.clear()
        self._send(text, with_code=True, then=None)

    def quick(self, label, prompt):
        if self.worker is not None or self.job is not None:
            return
        ed = self.studio.editor()
        if ed is None or not ed.toPlainText().strip():
            self.note.setText("Open or write a program first.")
            return
        if label == "Explain":
            self._send(prompt, with_code=True, then=None)
        else:
            self.target.setCurrentIndex(0)
            self.vibe(prompt, shown=label)

    def stop(self):
        if self.worker is not None:
            self.worker.stop()
        if self.job is not None:
            self.job = None
            self.studio.stop_program()
        self.note.setText("Stopped.")
        self._update_buttons()

    def _send(self, text, with_code, then, shown=None, quiet=False):
        """One question to the model; then(full answer) when it's done."""
        model = self.models.currentData()
        if not model:
            QMessageBox.information(self, "Vibe Coder", self.note.text() or "No language model is available.")
            self.job = None
            self._update_buttons()
            return
        ed = self.studio.editor()
        sent = text
        if with_code and ed is not None and ed.toPlainText().strip():
            sent += "\n\nThe program now:\n```qbasic\n" + ed.toPlainText() + "\n```"
        messages = [{"role": "system", "content": SYSTEM}]
        for role, body in self.history[-HISTORY_TURNS:]:
            if role in ("user", "assistant"):
                messages.append({"role": role, "content": body})
        messages.append({"role": "user", "content": sent})
        if not quiet:
            self.history.append(("user", shown or text))
        else:
            self.history.append(("user", text))
        self.reply = ""
        self.note.setText("Writing... (the first answer can take a while if the model has to load)")
        from pystudio.assistant import _Stream
        self.worker = _Stream(model, messages)
        self.worker.chunk.connect(self._chunk)
        self.worker.failed.connect(lambda m: self.note.setText(f"The AI could not answer: {m}"))
        self.worker.finished.connect(lambda: self._done(then))
        self.worker.start()
        self._update_buttons()
        self._render()

    def _chunk(self, text):
        self.reply += text
        if not self.repaint_timer.isActive():
            self.repaint_timer.start()

    def _done(self, then):
        worker, self.worker = self.worker, None
        full, self.reply = self.reply, ""
        answered = False
        if worker is not None:
            if full.strip():
                self.history.append(("assistant", full))
                answered = not worker.cancelled
                speed = f"  ({worker.tps:.0f} tokens/s)" if worker.tps else ""
                self.note.setText(("Stopped." if worker.cancelled else "Done.") + speed)
            else:
                if self.history and self.history[-1][0] == "user":
                    self.history.pop()
                if not self.note.text().startswith("The AI could not"):
                    self.note.setText("No answer came back.")
            worker.deleteLater()
        self._render()
        if then is not None and answered:
            then(full)
        elif then is not None:
            self.job = None
        self._update_buttons()

    def apply_last(self):
        code = self._last_code()
        if code:
            self.studio.put_code(code, new_tab=False)

    # ---- the vibe loop: write, check, run, fix ----
    def vibe(self, text, shown=None):
        new = self.target.currentIndex() == 1 or self.studio.editor() is None or \
            not self.studio.editor().toPlainText().strip()
        self.job = {"tries": 0, "new": new, "request": text}
        self.status.emit("Vibe coding...")
        prompt = text if not new else text + "\n\nWrite it as a new, complete program."
        self._send(prompt, with_code=not new, then=self._written, shown=shown or text)

    def _written(self, answer):
        job = self.job
        if job is None:
            return
        blocks = code_blocks(answer)
        if not blocks:
            self.history.append(("system", "No program came back - try saying it another way."))
            self.job = None
            self._render()
            return
        code = blocks[-1]
        self.studio.put_code(code, new_tab=job["new"], title=_title_for(job["request"]) if job["new"] else None)
        job["new"] = False
        self._check()

    def _check(self):
        job = self.job
        if job is None:
            return
        errors = self.studio.compile_errors()
        if errors:
            lines = "\n".join(f"line {e.line}: {e.message}   <- {self.studio.source_line(e.line).strip()}"
                              for e in errors[:8])
            self._fix("The program doesn't compile in Claude QBasic Studio's QBasic. These lines are wrong:\n"
                      f"{lines}\nChange those lines so they compile (don't just say it's correct - it isn't, here) "
                      "and give the whole program.",
                      f"It didn't compile ({len(errors)} problem{'s' if len(errors) != 1 else ''}) - fixing...")
            return
        if not self.autorun.isChecked():
            self._finish("Written and checked - press F5 to run it.")
            return
        self.history.append(("system", "Running it..."))
        self._render()
        self.studio.run_program(on_settled=self._ran, settle_secs=4)

    def _ran(self, outcome, error, screen_text):
        """The run settled: outcome "ended", "running" (still going, or waiting for keys) or "error"."""
        job = self.job
        if job is None:
            return
        if outcome != "error":
            self._finish("It runs! " + ("It finished." if outcome == "ended" else
                                        "It's running now - click the screen to play or type."))
            return
        shown = "\n".join(line for line in screen_text.splitlines() if line.strip())[-SCREEN_LIMIT:]
        msg = (f"When it ran it stopped with: {error.message} in line {error.line}"
               + (f" (that line is: {self.studio.source_line(error.line, running=True).strip()})" if error.line else "")
               + (f"\nThe screen showed:\n```\n{shown}\n```" if shown else "")
               + "\nFix it and give the whole program.")
        self._fix(msg, f"It crashed: {error.message} in line {error.line} - fixing...")

    def _fix(self, message, note):
        job = self.job
        if job is None:
            return
        job["tries"] += 1
        if job["tries"] > self.tries.value():
            self._finish(f"Stopped after {self.tries.value()} tries - the last problem is in the editor's Problems "
                         f"list. Tell me more, or press Fix it.", ok=False)
            return
        self.history.append(("system", f"{note} (try {job['tries']} of {self.tries.value()})"))
        self._render()
        self._send(message, with_code=True, then=self._written, quiet=True)

    def _finish(self, message, ok=True):
        self.job = None
        self.history.append(("system", ("✔ " if ok else "⚠ ") + message))
        self.note.setText(message)
        self.status.emit(message[:80])
        self._render()
        self._update_buttons()


def _shorten_code(text):
    """In the transcript, a long program shows as its first lines (the whole of it is in the editor)."""
    def cut(m):
        body = m.group(1)
        lines = body.splitlines()
        if len(lines) <= 14:
            return m.group(0)
        return "```qbasic\n" + "\n".join(lines[:10]) + f"\n' ... ({len(lines) - 10} more lines, in the editor)\n```"
    return CODE.sub(cut, text)


def _title_for(request):
    words = re.findall(r"[A-Za-z0-9]+", request)[:4]
    return ("".join(w.capitalize() for w in words) or "Vibe") + ".bas"
