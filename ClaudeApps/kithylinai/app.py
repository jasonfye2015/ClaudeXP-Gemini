"""Kithylin AI's window: Chat (over Kithylin's art), Gallery, Codes and Settings."""
import time

import threading

from PySide6.QtCore import QObject, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QIcon, QPixmap
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog, QDoubleSpinBox, QFileDialog, QFormLayout,
                               QGroupBox, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QListWidget, QListWidgetItem,
                               QMenu, QMessageBox, QPlainTextEdit, QPushButton, QScrollArea, QSpinBox,
                               QSystemTrayIcon, QTabWidget, QTextBrowser, QVBoxLayout, QWidget)

from . import defaults, engine as engine_mod, store
from .chat import Backdrop, ChatView, Composer, FormatBar, Slideshow
from .codes import CodesPage
from .details import ModelDetails
from .gallery import Gallery, load_index
from .paths import ART, DATA, ICON, hosted

STYLE = """
QWidget#kithylinai { background: #1b1b28; color: #e8e6f0; font-family: 'Segoe UI'; font-size: 10pt; }
QWidget#kithylinai QLabel { color: #e8e6f0; }
QWidget#kithylinai QLabel#hint { color: #b8b4c4; }
QWidget#kithylinai QLabel#caption { color: #b8b4c4; }
QWidget#kithylinai QLabel#title { color: #CDA4FF; font-size: 15pt; font-weight: bold; }
QWidget#kithylinai QTabWidget::pane { border: 1px solid #33334a; background: #1b1b28; }
QWidget#kithylinai QTabBar::tab { background: #26263a; color: #cfcbe0; padding: 6px 16px; border: 1px solid #33334a;
                                  border-bottom: none; }
QWidget#kithylinai QTabBar::tab:selected { background: #1b1b28; color: #ffffff; }
QWidget#kithylinai QPlainTextEdit#composer { background: rgba(20, 20, 32, 215); color: #ffffff; border: 1px solid #4a4a66;
                                             border-radius: 6px; padding: 6px; font-size: 11pt; }
QWidget#kithylinai QPlainTextEdit, QWidget#kithylinai QLineEdit, QWidget#kithylinai QComboBox,
QWidget#kithylinai QSpinBox, QWidget#kithylinai QDoubleSpinBox, QWidget#kithylinai QListWidget {
    background: #232336; color: #e8e6f0; border: 1px solid #44445e; border-radius: 4px; padding: 3px; selection-background-color: #5a4a8a; }
QWidget#kithylinai QComboBox QAbstractItemView { background: #232336; color: #e8e6f0; selection-background-color: #5a4a8a; }
QWidget#kithylinai QPushButton, QWidget#kithylinai QToolButton { background: #2f2f48; color: #e8e6f0; border: 1px solid #4a4a66;
                                                               border-radius: 5px; padding: 5px 12px; }
QWidget#kithylinai QPushButton:hover, QWidget#kithylinai QToolButton:hover { background: #3c3c5c; }
QWidget#kithylinai QPushButton:disabled { color: #77748a; }
QWidget#kithylinai QPushButton#send { background: #4b3a7a; font-weight: bold; }
QWidget#kithylinai QPushButton#send:hover { background: #5d4a96; }
QWidget#kithylinai QGroupBox { border: 1px solid #33334a; border-radius: 6px; margin-top: 10px; padding-top: 6px; }
QWidget#kithylinai QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; color: #CDA4FF; }
QWidget#kithylinai QGroupBox QLabel, QWidget#kithylinai QScrollArea QLabel { color: #e8e6f0; }
QWidget#kithylinai QCheckBox, QWidget#kithylinai QGroupBox QCheckBox { color: #e8e6f0; }
QWidget#kithylinai QScrollArea { border: none; background: transparent; }
QWidget#kithylinai QScrollArea > QWidget > QWidget { background: #1b1b28; }
QWidget#kithylinai QScrollArea > QWidget > QScrollBar { background: #232336; }
QWidget#kithylinai QListWidget#grid { background: #16161f; }
QWidget#kithylinai QListWidget#grid::item { color: #cfcbe0; }
QWidget#kithylinai QListWidget#grid::item:selected { background: #4b3a7a; }
QWidget#kithylinai QSplitter::handle { background: #33334a; }
"""


def app_icon():
    return QIcon(str(ICON)) if ICON.exists() else QIcon()


def _messengers():
    """Telegram and Discord are there (claudecore.messengers - not when Kithylin AI is lifted out of the Timeline)."""
    try:
        import claudecore.messengers                     # noqa: F401
        return True
    except ImportError:
        return False


class _Later(QObject):
    """later.run(work, then): work() on a thread of its own (the network), then(result) back on the window's thread;
    later.back.emit(fn) runs fn there."""
    back = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.back.connect(lambda fn: fn())

    def run(self, work, then):
        def go():
            try:
                result = work()
            except Exception:
                result = None
            self.back.emit(lambda: then(result))
        threading.Thread(target=go, name="kithylinai-later", daemon=True).start()


class KithylinAI(QWidget):
    def __init__(self, desktop=None):
        super().__init__()
        self.setObjectName("kithylinai")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(STYLE)
        self.desktop = desktop
        self.frame = None
        self.settings = store.Settings()
        self.chat = store.Chat()
        self.engine = engine_mod.Engine(self)
        self.engine.status.connect(self.system)
        self.engine.loaded.connect(self._loaded_changed)
        self.engine.chunk.connect(self._chunk)
        self.engine.done.connect(self._done)
        self.reply = None
        self._job = None                     # the reply under way: {"chat", "reply", "then"} (the window's, or a bot's)
        self.later = _Later(self)
        self.links, self.listeners = {}, {}  # Telegram and Discord: the bots and who's linked; what's listening
        self._msg_queue, self._msg_chats, self._msg_told, self._msg_refresh = [], {}, set(), {}
        self._tray, self._quitting = None, False
        self._render_timer = QTimer(self)
        self._render_timer.setSingleShot(True)
        self._render_timer.timeout.connect(lambda: self.view.render(self.visible_messages()))

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)
        root.addLayout(self._header())
        self.tabs = QTabWidget()
        self.tabs.addTab(self._chat_page(), "Chat")
        self.gallery = Gallery(open_media=self._open_media)
        self.gallery.use_as_background.connect(self._bg_from_gallery)
        self.tabs.addTab(self.gallery, "Kithylin's Art")
        self.codes_page = CodesPage(self.settings["codes"])
        self.codes_page.codes_chosen.connect(self._use_codes)
        self.codes_page.decode_to_chat.connect(self.system)
        self.tabs.addTab(self.codes_page, "Codes")
        self.details = ModelDetails(self.settings)
        self.tabs.addTab(self.details, "Model Details")
        self.tabs.addTab(self._settings_page(), "Settings")
        root.addWidget(self.tabs, 1)

        self.slideshow = Slideshow(self.backdrop, ART, load_index(), self.settings)
        self.slideshow.apply()
        self.refresh_models()
        self.system(f"Kithylin AI. {time.strftime('%A, %d %B %Y, %H:%M')}.")
        if self.settings["echo_prompts"]:
            self.echo_prompts()
        chosen = self.settings["model"]
        if self.settings["autoload"] and chosen and self.model_box.findData(chosen) >= 0:
            QTimer.singleShot(400, self.load_model)
        else:
            self.system("Choose a model at the top and press Load.")
        self.view.render(self.chat.messages)
        if _messengers():
            QTimer.singleShot(400, self._msg_start)

    # ---- layout ---------------------------------------------------------------------------------------------------
    def _header(self):
        row = QHBoxLayout()
        pic = QLabel()
        if ICON.exists():
            pic.setPixmap(QPixmap(str(ICON)).scaled(36, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        title = QLabel("Kithylin AI")
        title.setObjectName("title")
        row.addWidget(pic)
        row.addWidget(title)
        row.addSpacing(12)
        for which, label, tip in (("telegram", "Telegram...", "Talk with Kithylin from your phone, through a Telegram "
                                                              "bot of your own"),
                                  ("discord", "Discord...", "Talk with Kithylin on Discord, through a bot of your own")):
            b = QPushButton(label)
            b.setToolTip(tip)
            b.clicked.connect(lambda _c=False, w=which: self._msg_dialog(w))
            b.setVisible(_messengers())
            row.addWidget(b)
        row.addStretch(1)
        row.addWidget(QLabel("Model:"))
        self.model_box = QComboBox()
        self.model_box.setMinimumWidth(300)
        # (after the list has closed: building the details card while it was still closing left the empty drop-down
        # frame floating on screen on Windows)
        self.model_box.currentIndexChanged.connect(lambda _i: QTimer.singleShot(0, self._show_details))
        row.addWidget(self.model_box)
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.setToolTip("Pick any .gguf model file")
        self.browse_btn.clicked.connect(self.browse_model)
        self.load_btn = QPushButton("Load")
        self.load_btn.clicked.connect(self.load_model)
        self.unload_btn = QPushButton("Unload")
        self.unload_btn.clicked.connect(self.engine.unload)
        self.unload_btn.setEnabled(False)
        for b in (self.browse_btn, self.load_btn, self.unload_btn):
            row.addWidget(b)
        return row

    def _chat_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self.backdrop = Backdrop()
        self.view = ChatView()
        self.view.text_size = int(self.settings["text_size"])
        self.view.user_name = self.settings["user_name"] or "You"
        self.backdrop.lay.addWidget(self.view, 1)
        bottom = QWidget()
        bottom.setAttribute(Qt.WA_TranslucentBackground, True)
        b_lay = QVBoxLayout(bottom)
        b_lay.setContentsMargins(8, 4, 8, 8)
        b_lay.setSpacing(4)
        self.composer = Composer()
        self.composer.send.connect(self.send)
        tools = QHBoxLayout()
        tools.addWidget(FormatBar(self.composer))
        self.new_btn = QPushButton("New chat")
        self.new_btn.clicked.connect(self.new_chat)
        self.save_btn = QPushButton("Save chat...")
        self.save_btn.clicked.connect(self.save_chat)
        self.open_btn = QPushButton("Open chat...")
        self.open_btn.clicked.connect(self.open_chat)
        self.send_btn = QPushButton("Send")
        self.send_btn.setObjectName("send")
        self.send_btn.clicked.connect(self.send)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop)
        self.stop_btn.setEnabled(False)
        for b in (self.new_btn, self.save_btn, self.open_btn):
            tools.addWidget(b)
        tools.addStretch(1)
        tools.addWidget(self.stop_btn)
        tools.addWidget(self.send_btn)
        b_lay.addWidget(self.composer)
        b_lay.addLayout(tools)
        self.backdrop.lay.addWidget(bottom)
        lay.addWidget(self.backdrop, 1)
        return page

    def _settings_page(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        page = QWidget()
        scroll.setWidget(page)
        lay = QVBoxLayout(page)
        lay.setContentsMargins(10, 10, 10, 10)
        s = self.settings

        model_box = QGroupBox("The model")
        form = QFormLayout(model_box)
        self.engine_box = QComboBox()
        for key, label in (("auto", "Automatic (Vulkan if it's there, else CUDA)"), ("vulkan", "Vulkan"),
                           ("cuda", "CUDA"), ("cpu", "CPU only (slow, but leaves the graphics card alone)")):
            self.engine_box.addItem(label, key)
        self.engine_box.setCurrentIndex(max(0, self.engine_box.findData(s["engine"])))
        self.engine_box.currentIndexChanged.connect(lambda _i: s.set("engine", self.engine_box.currentData()))
        form.addRow("Engine:", self.engine_box)
        self.context_spin = QSpinBox()
        self.context_spin.setRange(1024, 131072)
        self.context_spin.setSingleStep(1024)
        self.context_spin.setValue(int(s["context"]))
        self.context_spin.valueChanged.connect(lambda v: s.set("context", int(v)))
        form.addRow("Context (tokens):", self.context_spin)
        self.temp_spin = QDoubleSpinBox()
        self.temp_spin.setRange(0.0, 2.0)
        self.temp_spin.setSingleStep(0.05)
        self.temp_spin.setValue(float(s["temperature"]))
        self.temp_spin.valueChanged.connect(lambda v: s.set("temperature", float(v)))
        form.addRow("Temperature:", self.temp_spin)
        self.max_spin = QSpinBox()
        self.max_spin.setRange(16, 8192)
        self.max_spin.setValue(int(s["max_tokens"]))
        self.max_spin.valueChanged.connect(lambda v: s.set("max_tokens", int(v)))
        form.addRow("Longest reply (tokens):", self.max_spin)
        self.autoload_box = QCheckBox("Load the last model when the program opens")
        self.autoload_box.setChecked(bool(s["autoload"]))
        self.autoload_box.toggled.connect(lambda on: s.set("autoload", bool(on)))
        form.addRow("", self.autoload_box)
        lay.addWidget(model_box)

        look = QGroupBox("The window")
        form = QFormLayout(look)
        self.name_edit = QLineEdit(s["user_name"])
        self.name_edit.editingFinished.connect(self._name_changed)
        form.addRow("Your name in the chat:", self.name_edit)
        self.size_spin = QSpinBox()
        self.size_spin.setRange(8, 24)
        self.size_spin.setValue(int(s["text_size"]))
        self.size_spin.valueChanged.connect(self._size_changed)
        form.addRow("Text size:", self.size_spin)
        self.bg_mode = QComboBox()
        for key, label in (("rotate", "Kithylin's Art, a new picture every few minutes"),
                           ("folder", "Pictures from one folder"), ("picture", "One picture"), ("none", "Plain")):
            self.bg_mode.addItem(label, key)
        self.bg_mode.setCurrentIndex(max(0, self.bg_mode.findData(s["background"]["mode"])))
        self.bg_mode.currentIndexChanged.connect(self._bg_changed)
        form.addRow("Background:", self.bg_mode)
        self.bg_folder = QComboBox()
        for f in load_index().get("folders", []):
            self.bg_folder.addItem(f["name"], f["name"])
        self.bg_folder.setCurrentIndex(max(0, self.bg_folder.findData(s["background"]["folder"])))
        self.bg_folder.currentIndexChanged.connect(self._bg_changed)
        form.addRow("Folder:", self.bg_folder)
        self.bg_minutes = QSpinBox()
        self.bg_minutes.setRange(1, 120)
        self.bg_minutes.setValue(int(s["background"]["minutes"]))
        self.bg_minutes.valueChanged.connect(self._bg_changed)
        form.addRow("Minutes per picture:", self.bg_minutes)
        self.bg_dim = QSpinBox()
        self.bg_dim.setRange(0, 95)
        self.bg_dim.setSuffix(" %")
        self.bg_dim.setValue(int(round(float(s["background"]["dim"]) * 100)))
        self.bg_dim.valueChanged.connect(self._bg_changed)
        form.addRow("Dim the picture:", self.bg_dim)
        self.bg_adult = QCheckBox("Leave the adult folders out of the slideshow")
        self.bg_adult.setChecked(bool(s["background"]["skip_adult"]))
        self.bg_adult.toggled.connect(self._bg_changed)
        adult_row = QHBoxLayout()
        adult_row.addWidget(self.bg_adult)
        pick = QPushButton("Which folders are adult...")
        pick.clicked.connect(self._pick_adult_folders)
        adult_row.addWidget(pick)
        adult_row.addStretch(1)
        form.addRow("", adult_row)
        self.show_sys = QCheckBox("Show system messages (purple) in the chat")
        self.show_sys.setChecked(bool(s["show_system"]))
        self.show_sys.toggled.connect(lambda on: (s.set("show_system", bool(on)), self.view.render(self.visible_messages())))
        form.addRow("", self.show_sys)
        self.echo_box = QCheckBox("Echo the system prompt and codes into the chat when the program opens")
        self.echo_box.setChecked(bool(s["echo_prompts"]))
        self.echo_box.toggled.connect(lambda on: s.set("echo_prompts", bool(on)))
        form.addRow("", self.echo_box)
        lay.addWidget(look)

        who = QGroupBox("Who Kithylin is (the first part of the system prompt)")
        v = QVBoxLayout(who)
        self.character_edit = QPlainTextEdit(s["character"])
        self.character_edit.setMinimumHeight(220)
        v.addWidget(self.character_edit)
        row = QHBoxLayout()
        b = QPushButton("Apply")
        b.clicked.connect(self._apply_character)
        r = QPushButton("Back to the default")
        r.clicked.connect(self._reset_character)
        row.addWidget(b)
        row.addWidget(r)
        row.addStretch(1)
        v.addLayout(row)
        lay.addWidget(who)

        codes = QGroupBox("His codes (the second part of the system prompt)")
        v = QVBoxLayout(codes)
        hint = QLabel("Generated from the codes on the Codes page: the legend, the codes, and what they say. "
                      "Edit it freely; \"Regenerate\" rebuilds it from the current codes.")
        hint.setWordWrap(True)
        hint.setObjectName("hint")
        v.addWidget(hint)
        self.codes_edit = QPlainTextEdit(s["codes_prompt"])
        self.codes_edit.setMinimumHeight(200)
        v.addWidget(self.codes_edit)
        row = QHBoxLayout()
        b = QPushButton("Apply")
        b.clicked.connect(self._apply_codes_prompt)
        r = QPushButton("Regenerate from the codes")
        r.clicked.connect(lambda: self._use_codes(self.settings["codes"]))
        row.addWidget(b)
        row.addWidget(r)
        row.addStretch(1)
        v.addLayout(row)
        lay.addWidget(codes)

        danger = QGroupBox("Reset")
        row = QHBoxLayout(danger)
        b1 = QPushButton("Reset the settings and prompts to the defaults")
        b1.clicked.connect(self.reset_settings)
        b2 = QPushButton("Delete all chat history")
        b2.clicked.connect(self.clear_history)
        row.addWidget(b1)
        row.addWidget(b2)
        row.addStretch(1)
        lay.addWidget(danger)
        lay.addStretch(1)
        return scroll

    # ---- system messages -----------------------------------------------------------------------------------------
    def system(self, text):
        self.chat.add("system", text)
        self.view.render(self.visible_messages())

    def visible_messages(self):
        if self.settings["show_system"]:
            return self.chat.messages
        return [m for m in self.chat.messages if m["role"] != "system"]

    def echo_prompts(self):
        c = self.settings["codes"]
        self.system("System prompt, part 1 (who Kithylin is):\n" + self.settings.filled("character"))
        self.system("System prompt, part 2 (his codes):\n" + self.settings.filled("codes_prompt"))
        self.system(f"Codes supplied: Furry Code {c.get('furcode') or '(none)'}  |  YIFF Code {c.get('yiffcode') or '(none)'}")

    # ---- models ------------------------------------------------------------------------------------------------------
    def refresh_models(self):
        current = self.settings["model"]
        self.model_box.blockSignals(True)
        self.model_box.clear()
        for m in engine_mod.models():
            self.model_box.addItem(m.label, m.key)
        if current and self.model_box.findData(current) < 0 and current.startswith("own:"):
            m = engine_mod.find(current)
            if m:
                self.model_box.addItem(m.label, m.key)
        i = self.model_box.findData(current)
        self.model_box.setCurrentIndex(i if i >= 0 else 0)
        self.model_box.blockSignals(False)
        self._show_details()
        if not self.model_box.count():
            self.system("No models found. Train one with ClaudeApps\\selfmodel (it lands in kithylinai\\Models), or "
                        "Browse... to a .gguf file.")

    def _show_details(self):
        popup = self.model_box.view().window()
        if popup is not self.window() and popup.isVisible():
            popup.hide()                                   # a drop-down frame left behind with nothing in it
        if getattr(self, "details", None) is None:
            return
        key = self.model_box.currentData()
        self.details.show_model(engine_mod.find(key) if key else None)

    def browse_model(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose a model", str(ART.parent / "Models"), "Models (*.gguf)")
        if path:
            key = f"own:{path}"
            if self.model_box.findData(key) < 0:
                m = engine_mod.find(key)
                self.model_box.addItem(m.label, key)
            self.model_box.setCurrentIndex(self.model_box.findData(key))
            self.load_model()

    def load_model(self):
        key = self.model_box.currentData()
        m = engine_mod.find(key) if key else None
        if m is None:
            self.system("Pick a model first.")
            return
        self.settings.set("model", key)
        self.chat.data["model"] = m.title
        self.engine.load(m, self.settings["engine"], int(self.settings["context"]))

    def _loaded_changed(self, ready):
        self.unload_btn.setEnabled(ready)
        self.send_btn.setEnabled(ready and not self.engine.busy())
        if ready:
            QTimer.singleShot(0, self._msg_next)          # (Telegram and Discord messages that waited for it)

    # ---- chatting ----------------------------------------------------------------------------------------------------
    def _for_model(self, chat, system_prompt):
        """The system prompt and as much of the conversation as the context holds, newest kept."""
        budget = int(self.settings["context"]) * 3 - len(system_prompt) - int(self.settings["max_tokens"]) * 3
        kept, used = [], 0
        for m in reversed(chat.spoken()):
            used += len(m["content"])
            if used > budget and kept:
                break
            kept.insert(0, {"role": m["role"], "content": m["content"]})
        return ([{"role": "system", "content": system_prompt}] if system_prompt else []) + kept

    def send(self):
        text = self.composer.toPlainText().strip()
        if not text:
            return
        if self._job is not None or self.engine.busy():
            if self._job is not None and self._job["chat"] is not self.chat:
                self.system("Kithylin is answering on Telegram or Discord - one moment.")
            return
        if not self.engine.ready:
            self.system("No model is loaded yet - press Load.")
            return
        self.composer.clear()
        self.chat.add("user", text)
        messages = self._for_model(self.chat, self.settings.system_prompt())
        self.reply = self.chat.add("assistant", "", streaming=True)
        self._job = {"chat": self.chat, "reply": self.reply, "then": None}
        self.view.render(self.visible_messages(), streaming=True)
        self.send_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.engine.chat(messages, float(self.settings["temperature"]), int(self.settings["max_tokens"]))

    def _chunk(self, text):
        job = self._job
        if job is not None:
            job["reply"]["content"] = text
            if job["chat"] is self.chat and not self._render_timer.isActive():
                self._render_timer.start(60)

    def _done(self, text, err):
        """A reply finished (the window's, or one for Telegram or Discord - sent back there): then the next."""
        self._render_timer.stop()
        self.stop_btn.setEnabled(False)
        self.send_btn.setEnabled(self.engine.ready)
        job, self._job, self.reply = self._job, None, None
        if job is None:
            return
        chat, reply = job["chat"], job["reply"]
        reply.pop("streaming", None)
        if err == "stopped":
            reply["content"] = text
            reply["stopped"] = True
        elif err:
            reply["content"] = text
            chat.add("system", f"The model didn't answer: {err}")
        else:
            reply["content"] = text.strip()
        if not reply["content"]:
            chat.messages.remove(reply)
        chat.save()
        if chat is self.chat:
            self.view.render(self.visible_messages())
            self.composer.setFocus()
        if job["then"] is not None:
            job["then"]("" if err else reply["content"])
        QTimer.singleShot(0, self._msg_next)

    def stop(self):
        self.engine.stop()

    # ---- history -------------------------------------------------------------------------------------------------------
    def new_chat(self):
        if self._job is not None and self._job["chat"] is self.chat:
            self.stop()
        self.chat.save()
        self.chat = store.Chat()
        self.chat.data["model"] = self.engine.model.title if self.engine.model else ""
        self.system("New chat.")
        self.composer.setFocus()

    def save_chat(self):
        if not self.chat.spoken():
            self.system("Nothing to save yet.")
            return
        name, ok = QInputDialog.getText(self, "Save chat", "A name for this chat:", text=self.chat.title())
        if ok and name.strip():
            path = self.chat.save_as(name.strip())
            self.chat.export_text(path.with_suffix(".txt"), self.settings["user_name"] or "You")
            self.system(f"Saved as {path.name} (and a .txt copy) in Data\\saved.")

    def open_chat(self):
        chats = store.list_chats()
        if not chats:
            self.system("No saved chats yet.")
            return
        dlg = _ChatPicker(self, chats)
        if dlg.exec() and dlg.chosen:
            c = store.load_chat(dlg.chosen)
            if c is None:
                return
            c = self._msg_chats.get(c.data.get("id"), c)        # (a Telegram or Discord one: the one in use)
            if self._job is not None and self._job["chat"] is self.chat:
                self.stop()
            self.chat.save()
            self.chat = c
            self.system(f"Opened \"{c.title()}\" ({len(c.spoken())} turns).")

    def clear_history(self):
        if QMessageBox.question(self, "Delete all chat history", "Delete every chat Kithylin AI has saved, including the "
                                "named ones? This can't be undone.") == QMessageBox.Yes:
            n = store.clear_history()
            self.chat = store.Chat()
            self.system(f"Deleted {n} saved chats.")

    # ---- settings -----------------------------------------------------------------------------------------------------
    def _name_changed(self):
        name = self.name_edit.text().strip() or "You"
        self.settings.set("user_name", name)
        self.view.user_name = name
        self.view.render(self.visible_messages())

    def _size_changed(self, v):
        self.settings.set("text_size", int(v))
        self.view.text_size = int(v)
        self.view.render(self.visible_messages())

    def _bg_changed(self, *_):
        bg = dict(self.settings["background"])
        bg.update(mode=self.bg_mode.currentData(), folder=self.bg_folder.currentData() or "",
                  minutes=int(self.bg_minutes.value()), dim=self.bg_dim.value() / 100.0,
                  skip_adult=self.bg_adult.isChecked())
        self.settings.set("background", bg)
        self.slideshow.apply()

    def _pick_adult_folders(self):
        """Tick the art folders the slideshow should leave out (a folder's name doesn't always say)."""
        from PySide6.QtWidgets import QDialogButtonBox, QLabel, QListWidget, QListWidgetItem
        from .chat import adult_folders
        names = [f["name"] for f in load_index().get("folders", [])]
        adult = adult_folders(self.settings, names)
        dlg = QDialog(self)
        dlg.setWindowTitle("Adult folders")
        lay = QVBoxLayout(dlg)
        note = QLabel("Ticked folders are left out of the background slideshow while \"Leave the adult folders out\" "
                      "is on. They stay in Kithylin's Art.")
        note.setWordWrap(True)
        lay.addWidget(note)
        box = QListWidget()
        for n in names:
            it = QListWidgetItem(n)
            it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
            it.setCheckState(Qt.Checked if n in adult else Qt.Unchecked)
            box.addItem(it)
        lay.addWidget(box)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        lay.addWidget(buttons)
        dlg.resize(380, 480)
        if dlg.exec() != QDialog.Accepted:
            return
        bg = dict(self.settings["background"])
        bg["adult_folders"] = [box.item(i).text() for i in range(box.count())
                               if box.item(i).checkState() == Qt.Checked]
        self.settings.set("background", bg)
        self.slideshow.apply()

    def _bg_from_gallery(self, rel):
        bg = dict(self.settings["background"])
        bg.update(mode="picture", picture=rel)
        self.settings.set("background", bg)
        self.bg_mode.blockSignals(True)
        self.bg_mode.setCurrentIndex(self.bg_mode.findData("picture"))
        self.bg_mode.blockSignals(False)
        self.slideshow.apply()
        self.tabs.setCurrentIndex(0)
        self.system(f"Background: {rel}")

    def _apply_character(self):
        self.settings.set("character", self.character_edit.toPlainText())
        self.system("System prompt, part 1 (who Kithylin is), updated:\n" + self.settings.filled("character"))

    def _reset_character(self):
        self.character_edit.setPlainText(defaults.DEFAULT_CHARACTER)
        self._apply_character()

    def _apply_codes_prompt(self):
        self.settings.set("codes_prompt", self.codes_edit.toPlainText())
        self.system("System prompt, part 2 (his codes), updated:\n" + self.settings.filled("codes_prompt"))

    def _use_codes(self, codes):
        codes = {"furcode": codes.get("furcode", ""), "yiffcode": codes.get("yiffcode", "")}
        self.settings.set("codes", codes)
        self.codes_page.set_codes(codes)
        prompt = defaults.codes_prompt(codes["furcode"], codes["yiffcode"])
        self.settings.set("codes_prompt", prompt)
        self.codes_edit.setPlainText(prompt)
        self.system(f"Codes supplied: Furry Code {codes['furcode'] or '(none)'}  |  YIFF Code {codes['yiffcode'] or '(none)'}")
        self.system("System prompt, part 2 (his codes), regenerated:\n" + prompt)

    def reset_settings(self):
        if QMessageBox.question(self, "Reset", "Put every setting and both prompts back to the defaults? Your chats "
                                "are kept.") != QMessageBox.Yes:
            return
        model = self.settings["model"]
        self.settings.reset()
        self.settings.set("model", model)
        s = self.settings
        self.character_edit.setPlainText(s["character"])
        self.codes_edit.setPlainText(s["codes_prompt"])
        self.codes_page.set_codes(s["codes"])
        self.engine_box.setCurrentIndex(max(0, self.engine_box.findData(s["engine"])))
        self.context_spin.setValue(int(s["context"]))
        self.temp_spin.setValue(float(s["temperature"]))
        self.max_spin.setValue(int(s["max_tokens"]))
        self.name_edit.setText(s["user_name"])
        self.size_spin.setValue(int(s["text_size"]))
        self.bg_mode.setCurrentIndex(max(0, self.bg_mode.findData(s["background"]["mode"])))
        self.bg_minutes.setValue(int(s["background"]["minutes"]))
        self.bg_dim.setValue(int(round(s["background"]["dim"] * 100)))
        self.bg_adult.setChecked(bool(s["background"]["skip_adult"]))
        self.show_sys.setChecked(bool(s["show_system"]))
        self.echo_box.setChecked(bool(s["echo_prompts"]))
        self.autoload_box.setChecked(bool(s["autoload"]))
        self.slideshow.apply()
        self.system("Settings and prompts reset to the defaults.")
        self.echo_prompts()

    # ---- Telegram and Discord (claudecore.messengers; what the bots say: bots.py) ------------------------------------
    MESSENGERS = ("telegram", "discord")

    @staticmethod
    def _messenger(which):
        """A messenger's module (claudecore.messengers): its Link and Listener, and its window's words."""
        from claudecore.messengers import discordlink, telegram
        return {"telegram": telegram, "discord": discordlink}[which]

    def _link(self, which):
        if self.links.get(which) is None:
            from .bots import WORDS
            self.links[which] = self._messenger(which).Link(DATA, words=WORDS)
        return self.links[which]

    def _linked(self, which):
        link = self.links.get(which)
        return link is not None and link.ready() and bool(link.owner)

    def _listening(self, which):
        listener = self.listeners.get(which)
        return listener is not None and listener.alive()

    def _msg_start(self, which=None):
        """The bots that are set up, listening - what they hear is passed back to the window's thread."""
        for w in [which] if which else self.MESSENGERS:
            link = self._link(w)
            if link.ready() and not self._listening(w):
                listener = self._messenger(w).Listener(
                    link, lambda raw, w=w: self.later.back.emit(lambda: self._msg_update(w, raw)),
                    on_status=lambda text: self.later.back.emit(lambda: self.system(text)))
                self.listeners[w] = listener
                listener.start()

    def _msg_stop(self, which):
        listener = self.listeners.pop(which, None)
        if listener is not None:
            listener.stop()

    def _msg_send(self, which, chat, text):
        link = self.links[which]
        self.later.run(lambda: link.send(chat, text), lambda _r: None)

    def _msg_update(self, which, raw):
        """One message from Telegram or Discord: who it's from decides what happens."""
        from .bots import WORDS
        mod, link = self._messenger(which), self.links.get(which)
        info = link.classify(raw) if link is not None else None
        if not info:
            return
        kind, chat = info["kind"], info["chat"]
        if kind == "stranger":
            self._msg_send(which, chat, WORDS["private"])
        elif kind == "linked":
            self._msg_send(which, chat, WORDS["linked"])
            self.system(f"{mod.NAME} is linked: {info['name']} can talk with Kithylin there.")
            self._msg_refresh.get(which, lambda: None)()
        elif kind == "invited":
            owner = (link.owner or {}).get("name") or self.settings["user_name"] or "its owner"
            self._msg_send(which, chat, WORDS["welcome"].format(name=info["name"], owner=owner))
            self.system(f"{info['name']} accepted your {mod.NAME} invitation.")
            self._msg_refresh.get(which, lambda: None)()
        elif not info["text"]:                           # (a picture on its own, a voice message...: not yet)
            self._msg_send(which, chat, WORDS["cant"].format(what=info.get("other") or "pictures"))
        else:
            self._msg_queue.append((which, info))
            self._msg_next()

    def _msg_chat(self, which, info):
        """The conversation with this person on Telegram or Discord: a chat of its own in Kithylin AI's history
        (Open chat... shows it), kept from one time to the next."""
        key = f"{which}-{info['user']}"
        if self.chat.data.get("id") == key:
            self._msg_chats[key] = self.chat
        chat = self._msg_chats.get(key)
        if chat is None:
            path = store.CHATS_DIR / f"{key}.json"
            chat = (store.load_chat(path) if path.exists() else None) or store.Chat(
                {"id": key, "title": "", "model": "", "created": time.time(), "updated": time.time(), "messages": []},
                path)
            self._msg_chats[key] = chat
        chat.data["title"] = f"{info['name']} on {self._messenger(which).NAME}"
        return chat

    def _msg_next(self):
        """The next message from Telegram or Discord, answered as soon as the model is free (one reply at a time)."""
        while self._msg_queue and self._job is None and self.engine.ready and not self.engine.busy():
            which, info = self._msg_queue.pop(0)
            link = self.links.get(which)
            if link is None:
                continue
            name = self._messenger(which).NAME
            chat = self._msg_chat(which, info)
            chat.add("user", info["text"] + ("\n(A picture came with this - Kithylin AI can't see pictures yet.)"
                                             if info.get("picture") else ""), via=which)
            guest = info["kind"] == "guest"
            prompt = self.settings.system_prompt(name=info["name"] if guest else None)
            if guest:
                prompt += (f"\n\n(You're talking on {name} with {info['name']}, someone invited to talk with Kithylin "
                           "AI. They know you're an AI.)")
            messages = self._for_model(chat, prompt)
            to = info["chat"]
            self._job = {"chat": chat, "reply": chat.add("assistant", "", streaming=True),
                         "then": lambda text, which=which, to=to: self._msg_send(
                             which, to, text or "(Kithylin AI couldn't answer just now - try again in a moment.)")}
            self.later.run(lambda: link.typing(to), lambda _r: None)
            if chat is self.chat:
                self.view.render(self.visible_messages(), streaming=True)
            elif info["user"] not in self._msg_told:
                self._msg_told.add(info["user"])
                self.system(f"{info['name']} is talking with Kithylin on {name} - Open chat... shows it.")
            self.send_btn.setEnabled(False)
            self.engine.chat(messages, float(self.settings["temperature"]), int(self.settings["max_tokens"]))

    def _show_conversation(self, which, person):
        """A Telegram or Discord conversation, open in the window."""
        chat = self._msg_chat(which, {"user": person["id"], "name": person["name"]})
        if chat is not self.chat:
            if self._job is not None and self._job["chat"] is self.chat:
                self.stop()
            self.chat.save()
            self.chat = chat
        self.view.render(self.visible_messages())

    def _msg_dialog(self, which):
        """Telegram... or Discord...: Kithylin AI's bot there, who's linked, and the people invited."""
        from . import bots
        mod, link = self._messenger(which), self._link(which)
        name = mod.NAME
        d = QDialog(self)
        d.setWindowTitle(f"Kithylin AI on {name}")
        d.setMinimumWidth(560)
        d.setStyleSheet("QDialog, QMessageBox, QInputDialog { background: #1b1b28; color: #e8e6f0; }")
        v = QVBoxLayout(d)
        intro = QLabel(mod.intro(bots.APP, bots.WHO))
        intro.setWordWrap(True)
        v.addWidget(intro)
        row = QHBoxLayout()
        token = QLineEdit()
        token.setEchoMode(QLineEdit.Password)
        token.setPlaceholderText(mod.TOKEN_HINT)
        connect = QPushButton("Link")
        unlink = QPushButton("Unlink")
        row.addWidget(token, 1)
        row.addWidget(connect)
        row.addStretch()
        add = None
        if hasattr(link, "invite_url"):                  # (Discord: a bot is messaged by people it shares a server with)
            add = QPushButton("Add it to a server...")
            add.setToolTip("Discord only lets you message a bot you share a server with: this opens Discord's page "
                           "for adding it to one of yours")
            add.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(link.invite_url())))
            row.addWidget(add)
        row.addWidget(unlink)
        v.addLayout(row)
        state = QLabel()
        state.setWordWrap(True)
        state.setTextInteractionFlags(Qt.TextSelectableByMouse)
        v.addWidget(state)
        talk = QPushButton("Show our conversation")
        talk.setToolTip(f"Open your {name} conversation with Kithylin here, in the window")
        talk.clicked.connect(lambda: (self._show_conversation(which, link.owner), d.accept()))
        v.addWidget(talk, 0, Qt.AlignLeft)
        box = QGroupBox("People you've invited")
        gv = QVBoxLayout(box)
        guests = QListWidget()
        guests.setMaximumHeight(90)
        gv.addWidget(guests)
        grow = QHBoxLayout()
        invite = QPushButton("Invite someone...")
        remove = QPushButton("Remove")
        grow.addWidget(invite)
        grow.addWidget(remove)
        grow.addStretch(1)
        gv.addLayout(grow)
        v.addWidget(box)
        background = QCheckBox("On its own (the launcher's APPS), keep listening when the window is closed")
        background.setToolTip("Closing the window leaves an icon in the notification area: click it (or start Kithylin "
                              "AI again) to open it, or right-click it to stop listening and quit")
        background.setChecked(bool(link.data.get("background", True)))
        v.addWidget(background)
        how = QPushButton("How to connect...")
        how.setToolTip(mod.HOW_HINT)
        how.clicked.connect(lambda: self._msg_how(which, d))
        close = QPushButton("Close")
        bottom = QHBoxLayout()
        bottom.addWidget(how)
        bottom.addStretch(1)
        bottom.addWidget(close)
        v.addLayout(bottom)

        def refresh():
            ready = link.ready()
            token.setVisible(not ready)
            connect.setVisible(not ready)
            unlink.setVisible(ready)
            if add is not None:
                add.setVisible(ready)
            talk.setVisible(ready and bool(link.owner))
            guests.clear()
            for g in link.data["guests"]:
                item = QListWidgetItem(g["name"])
                item.setData(Qt.UserRole, g["id"])
                guests.addItem(item)
            box.setEnabled(ready and bool(link.owner))
            if not ready:
                state.setText("Not linked yet.")
            elif not link.owner:
                code = next((k for k, x in link.data["codes"].items() if x["for"] == "owner"), None) \
                    or link.code("owner")
                state.setText(mod.waiting_text(link, code))
            else:
                state.setText(mod.linked_text(link) + (" Listening." if self._listening(which) else ""))
        self._msg_refresh[which] = refresh

        def do_link():
            try:
                bot = link.connect(token.text())
            except Exception as e:
                QMessageBox.warning(d, name, f"{name} didn't accept that token: {e}")
                return
            token.clear()
            self._msg_start(which)
            self.system(f"Kithylin AI is listening on {name} as {bot}.")
            refresh()

        def do_unlink():
            if QMessageBox.question(d, name, "Unlink the bot? Kithylin AI forgets its token and everyone linked to "
                                             f"it (the bot itself stays yours, in {name}).") != QMessageBox.Yes:
                return
            self._msg_stop(which)
            link.forget()
            refresh()

        def do_invite():
            who, ok = QInputDialog.getText(d, "Invite someone", "Their name (as Kithylin will know them):")
            if ok and who.strip():
                QMessageBox.information(d, "Invite someone",
                                        mod.invite_text(link, who.strip(), link.code("guest", who.strip())))

        def do_remove():
            item = guests.currentItem()
            if item is not None:
                link.remove_guest(item.data(Qt.UserRole))
                refresh()

        def keep():
            link.data["background"] = background.isChecked()
            link.save()
        connect.clicked.connect(do_link)
        unlink.clicked.connect(do_unlink)
        invite.clicked.connect(do_invite)
        remove.clicked.connect(do_remove)
        close.clicked.connect(d.accept)
        d.finished.connect(lambda _r: (keep(), self._msg_refresh.pop(which, None),
                                       getattr(d, "how", None) and d.how.close()))
        refresh()
        d.exec()

    def _msg_how(self, which, parent):
        """The setup, step by step - beside the Telegram or Discord window, to follow along with."""
        from . import bots
        mod = self._messenger(which)
        how = getattr(parent, "how", None)
        if how is None:
            how = parent.how = QDialog(parent)
            how.setWindowTitle(f"How to connect Kithylin AI to {mod.NAME}")
            how.resize(560, 470 if which == "discord" else 410)
            v = QVBoxLayout(how)
            text = QTextBrowser()
            text.setStyleSheet("background: #232336; color: #e8e6f0;")
            text.setHtml(mod.setup(bots.APP, bots.SENDS))
            v.addWidget(text)
            close = QPushButton("Close")
            close.clicked.connect(how.close)
            v.addWidget(close, 0, Qt.AlignRight)
            beside, screen = parent.frameGeometry(), parent.screen().availableGeometry()
            if beside.right() + 8 + how.width() <= screen.right():
                how.move(beside.right() + 8, beside.top())
        how.show()
        how.raise_()
        how.activateWindow()

    # ---- on its own: listening on, from the notification area ----
    def close_to_tray(self):
        """The window closed on its own (the launcher's APPS) while a bot listens: Kithylin AI waits in the
        notification area instead of quitting. True if it did."""
        if self._quitting or hosted() or not QSystemTrayIcon.isSystemTrayAvailable():
            return False
        if not any(self._linked(w) and self.links[w].data.get("background", True) for w in self.MESSENGERS):
            return False
        (self.frame or self).hide()
        self._tray_show()
        return True

    def _tray_show(self):
        if self._tray is None:
            self._tray = QSystemTrayIcon(app_icon(), self)
            menu = QMenu()
            menu.addAction("Open Kithylin AI", self.show_again)
            menu.addSeparator()
            menu.addAction("Stop listening and quit", self._tray_quit)
            self._tray.setContextMenu(menu)
            self._tray._menu = menu
            self._tray.activated.connect(lambda reason: self.show_again()
                                         if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick) else None)
        on = " and ".join(self._messenger(w).NAME for w in self.MESSENGERS if self._linked(w))
        self._tray.setToolTip(f"Kithylin AI - listening on {on}")
        QApplication.instance().setQuitOnLastWindowClosed(False)
        self._tray.show()
        if not getattr(self, "_tray_told", False):
            self._tray_told = True
            self._tray.showMessage("Kithylin AI is still listening",
                                   f"Kithylin keeps answering on {on}. Click this icon - or start Kithylin AI again - to "
                                   "open it; right-click it to stop listening and quit.")

    def show_again(self):
        """Started again, or its icon clicked: the window comes back - out of the notification area, up from
        minimised, in front."""
        frame = self.frame or self
        frame.showNormal() if frame.isMinimized() else frame.show()
        frame.raise_()
        frame.activateWindow()
        if self._tray is not None:
            self._tray.hide()
        QApplication.instance().setQuitOnLastWindowClosed(True)

    def _tray_quit(self):
        self._quitting = True
        if self._tray is not None:
            self._tray.hide()
        QApplication.instance().setQuitOnLastWindowClosed(True)
        (self.frame or self).close()

    # ---- the computer ------------------------------------------------------------------------------------------------
    def _open_media(self, path):
        if hosted() and self.desktop is not None:
            try:
                from claudecore import host
                return host.open_media(self.desktop, path)
            except Exception:
                return False
        return False

    def shutdown(self):
        for which in list(self.listeners):
            self._msg_stop(which)
        if self._tray is not None:
            self._tray.hide()
        self.chat.save()
        for chat in self._msg_chats.values():
            chat.save()
        self.engine.shutdown()


class _ChatPicker(QDialog):
    """A simple list of saved chats to open."""

    def __init__(self, parent, chats):
        super().__init__(parent)
        self.setWindowTitle("Open chat")
        self.resize(520, 380)
        self.chosen = None
        lay = QVBoxLayout(self)
        self.list = QListWidget()
        for path, title, updated, turns, saved in chats:
            stamp = time.strftime("%Y-%m-%d %H:%M", time.localtime(updated))
            item = QListWidgetItem(f"{'★ ' if saved else ''}{title}   —   {turns} turns, {stamp}")
            item.setData(Qt.UserRole, str(path))
            self.list.addItem(item)
        self.list.itemDoubleClicked.connect(lambda _i: self._ok())
        lay.addWidget(self.list, 1)
        row = QHBoxLayout()
        row.addStretch(1)
        ok = QPushButton("Open")
        ok.clicked.connect(self._ok)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        row.addWidget(ok)
        row.addWidget(cancel)
        lay.addLayout(row)
        if self.list.count():
            self.list.setCurrentRow(0)

    def _ok(self):
        item = self.list.currentItem()
        if item:
            self.chosen = item.data(Qt.UserRole)
            self.accept()
