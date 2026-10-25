"""Kithylin AI's window: Chat (over Kithylin's art), Gallery, Codes and Settings."""
import time

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog, QDoubleSpinBox, QFileDialog, QFormLayout, QGroupBox, QHBoxLayout,
                               QInputDialog, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMessageBox,
                               QPlainTextEdit, QPushButton, QScrollArea, QSpinBox, QTabWidget, QVBoxLayout, QWidget)

from . import defaults, engine as engine_mod, store
from .chat import Backdrop, ChatView, Composer, FormatBar, Slideshow
from .codes import CodesPage
from .details import ModelDetails
from .gallery import Gallery, load_index
from .paths import ART, ICON, hosted

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
        form.addRow("", self.bg_adult)
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

    # ---- chatting ----------------------------------------------------------------------------------------------------
    def send(self):
        text = self.composer.toPlainText().strip()
        if not text or self.engine.busy():
            return
        if not self.engine.ready:
            self.system("No model is loaded yet - press Load.")
            return
        self.composer.clear()
        self.chat.add("user", text)
        system_prompt = self.settings.system_prompt()
        budget = int(self.settings["context"]) * 3 - len(system_prompt) - int(self.settings["max_tokens"]) * 3
        kept, used = [], 0
        for m in reversed(self.chat.spoken()):
            used += len(m["content"])
            if used > budget and kept:
                break
            kept.insert(0, {"role": m["role"], "content": m["content"]})
        messages = ([{"role": "system", "content": system_prompt}] if system_prompt else []) + kept
        self.reply = self.chat.add("assistant", "", streaming=True)
        self.view.render(self.visible_messages(), streaming=True)
        self.send_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.engine.chat(messages, float(self.settings["temperature"]), int(self.settings["max_tokens"]))

    def _chunk(self, text):
        if self.reply is not None:
            self.reply["content"] = text
            if not self._render_timer.isActive():
                self._render_timer.start(60)

    def _done(self, text, err):
        self._render_timer.stop()
        self.stop_btn.setEnabled(False)
        self.send_btn.setEnabled(self.engine.ready)
        if self.reply is None:
            return
        self.reply.pop("streaming", None)
        if err == "stopped":
            self.reply["content"] = text
            self.reply["stopped"] = True
        elif err:
            self.reply["content"] = text
            self.chat.add("system", f"The model didn't answer: {err}")
        else:
            self.reply["content"] = text.strip()
        if not self.reply["content"]:
            self.chat.messages.remove(self.reply)
        self.reply = None
        self.chat.save()
        self.view.render(self.visible_messages())
        self.composer.setFocus()

    def stop(self):
        self.engine.stop()

    # ---- history -------------------------------------------------------------------------------------------------------
    def new_chat(self):
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
        self.chat.save()
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
