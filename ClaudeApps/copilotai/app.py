"""CopilotAI, a persistent local-model chat application with optional offline voice."""
import array
import html
import math
import wave
import random
import time
from collections import deque
from pathlib import Path

from PySide6.QtCore import QPoint, QSize, Qt, QTimer, QUrl
from PySide6.QtGui import QColor, QIcon, QKeySequence, QPainter, QPixmap, QShortcut, QTextDocument
from PySide6.QtMultimedia import (QAudio, QAudioFormat, QAudioOutput, QAudioSource, QMediaDevices,
                                 QMediaPlayer)
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout,
                               QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMenu,
                               QMessageBox, QPlainTextEdit, QPushButton, QSizePolicy, QSlider, QSpinBox,
                               QSplitter, QTextBrowser, QToolButton, QVBoxLayout, QWidget)
from shiboken6 import isValid

from claudecore.ai import ai_models, broker, llm_server
from copilot_voice import (MODELS_ROOT, VoiceTask, _engine_ready, _models_ready,
                             _temporary_audio_path)
from .store import DEFAULT_INSTRUCTIONS, Chats, Settings
from . import imagetool
import voicecatalog
from claudecore import host

BG, SIDEBAR, BORDER = "#FAF9F5", "#F0EEE6", "#E3DFD3"
TEXT, MUTED, ACCENT = "#3D3929", "#8B877C", "#D97757"
VOICES = voicecatalog.VOICES
SAMPLE_RATE = 16000
MAX_RECORD_SECONDS = 90
AUTO_SILENCE_SECONDS = 1.0
AUTO_VAD_THRESHOLD = 650
STYLE = f"""
QWidget#copilotai {{ background: {BG}; }}
QWidget#copilotai QLabel {{ color: {TEXT}; font-family: 'Segoe UI'; }}
QWidget#copilot_sidebar {{ background: {SIDEBAR}; border-right: 1px solid {BORDER}; }}
QLabel#brand {{ font-family: Georgia; font-size: 18px; font-weight: bold; }}
QLabel#section {{ color: {MUTED}; font-size: 11px; font-weight: bold; padding: 7px 5px 2px; }}
QPushButton#newchat {{ text-align: left; padding: 7px 9px; border: 0; border-radius: 7px;
                       font-family: 'Segoe UI'; font-size: 13px; }}
QPushButton#newchat:hover, QToolButton:hover {{ background: #E6E2D7; }}
QLineEdit#search {{ background: #F7F5EF; border: 1px solid {BORDER}; border-radius: 7px;
                    padding: 5px 8px; font-family: 'Segoe UI'; font-size: 12px; }}
QListWidget#chats {{ background: transparent; border: 0; outline: 0; font-family: 'Segoe UI'; font-size: 12px; }}
QListWidget#chats::item {{ border-radius: 6px; padding: 3px; }}
QListWidget#chats::item:hover {{ background: #E8E4D9; }}
QListWidget#chats::item:selected {{ background: #E3DED1; color: {TEXT}; }}
QTextBrowser#conversation {{ background: {BG}; border: 0; font-family: 'Segoe UI'; }}
QPlainTextEdit#prompt {{ background: transparent; border: 0; font-family: 'Segoe UI'; font-size: 14px; }}
QFrame#composer {{ background: white; border: 1px solid #DAD5C8; border-radius: 14px; }}
QToolButton {{ border: 0; border-radius: 6px; padding: 4px; color: {TEXT}; }}
QToolButton:checked {{ background: #F3DED4; color: #B85A3B; }}
QMenu {{ background: white; border: 1px solid {BORDER}; padding: 4px; font-family: 'Segoe UI'; font-size: 12px; }}
QMenu::item {{ padding: 6px 22px 6px 12px; }}
QMenu::item:selected {{ background: #F0EDE4; }}
"""


def app_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor("#F4E9DF"))
    painter.drawRoundedRect(1, 1, 30, 30, 7, 7)
    painter.setBrush(QColor(ACCENT))
    center = QPoint(16, 16)
    for dx, dy in ((0, -8), (7, -4), (6, 5), (0, 8), (-6, 5), (-7, -4)):
        painter.drawEllipse(center + QPoint(dx, dy), 3, 3)
    painter.drawEllipse(center, 4, 4)
    painter.end()
    return QIcon(pm)


def _markdown_html(text):
    doc = QTextDocument()
    doc.setMarkdown(text)
    body = doc.toHtml()
    start = body.find("<body")
    start = body.find(">", start) + 1
    end = body.rfind("</body>")
    return body[start:end]


class ChatRow(QWidget):
    def __init__(self, app, chat):
        super().__init__()
        self.app, self.chat = app, chat
        row = QHBoxLayout(self)
        row.setContentsMargins(8, 3, 2, 3)
        self.label = QLabel()
        self.label.setStyleSheet("font-size: 12px; background: transparent;")
        row.addWidget(self.label, 1)
        self.pin = QLabel("★" if chat.get("pinned") else "")
        self.pin.setStyleSheet(f"color: {ACCENT}; font-size: 12px; background: transparent;")
        row.addWidget(self.pin)
        self.more = QToolButton()
        self.more.setText("⋯")
        self.more.setFixedSize(24, 22)
        self.more.setVisible(False)
        self.more.clicked.connect(lambda: app.chat_menu(chat, self.more.mapToGlobal(self.more.rect().bottomLeft())))
        row.addWidget(self.more)
        self._set_text()

    def _set_text(self):
        self.label.setText(self.label.fontMetrics().elidedText(self.chat["title"], Qt.ElideRight, 180))

    def enterEvent(self, event):
        self.more.setVisible(True)

    def leaveEvent(self, event):
        self.more.setVisible(False)


class CopilotAI(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.settings = Settings()
        self.chats = Chats()
        self.current = None
        self.expanded_thoughts = set()
        self.job = None
        self.image_task = None
        self.voice_task = None
        self.capture = None
        self.capture_io = None
        self.capture_format = None
        self.capture_mode = ""
        self.capture_chunks = []
        self.pre_roll = deque()
        self.pre_roll_duration = 0.0
        self.speech_detected = False
        self.silence_duration = 0.0
        self.speaking = False
        self.closing = False
        self.turn_id = 0
        self._audio_temp = None
        self._reply_audio = None
        self.setObjectName("copilotai")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(STYLE)
        self.models = self._list_models()
        if self.settings["model"] not in self.models:
            self.settings.values["model"] = self.models[0] if self.models else ""
        self.render_timer = QTimer(self)
        self.render_timer.setSingleShot(True)
        self.render_timer.timeout.connect(self.render)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.sidebar = self._make_sidebar()
        root.addWidget(self.sidebar)
        main = self._make_main()
        root.addWidget(main, 1)

        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)
        self.player.mediaStatusChanged.connect(self._playback_end)
        self.player.errorOccurred.connect(self._auto_speak_error)
        QShortcut(QKeySequence("Ctrl+Shift+O"), self, self.new_chat)
        QShortcut(QKeySequence("Ctrl+B"), self, self.toggle_sidebar)
        QShortcut(QKeySequence("Ctrl+P"), self, self.copy_last_reply)
        QShortcut(QKeySequence("Ctrl+L"), self, lambda: (self.search.setFocus(), self.search.selectAll()))
        self._apply_sidebar(self.settings["sidebar"])
        self.refresh_sidebar()
        self.render()
        self._refresh_voice_controls()
        if self.settings["auto_listen"]:
            QTimer.singleShot(0, lambda: self._set_auto_listen(True, announce=False))

    def _make_sidebar(self):
        sidebar = QWidget()
        sidebar.setObjectName("copilot_sidebar")
        sidebar.setAttribute(Qt.WA_StyledBackground, True)
        sidebar.setMinimumWidth(205)
        sidebar.setMaximumWidth(320)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(5)
        top = QHBoxLayout()
        self.sidebar_toggle = QToolButton()
        self.sidebar_toggle.setText("☰")
        self.sidebar_toggle.setToolTip("Collapse sidebar (Ctrl+B)")
        self.sidebar_toggle.clicked.connect(self.toggle_sidebar)
        top.addWidget(self.sidebar_toggle)
        brand = QLabel("CopilotAI")
        brand.setObjectName("brand")
        top.addWidget(brand, 1)
        layout.addLayout(top)

        self.new_button = QPushButton("+  New chat")
        self.new_button.setObjectName("newchat")
        self.new_button.clicked.connect(self.new_chat)
        layout.addWidget(self.new_button)
        self.search = QLineEdit()
        self.search.setObjectName("search")
        self.search.setPlaceholderText("Search chats...")
        self.search.textChanged.connect(lambda _text: self.refresh_sidebar())
        layout.addWidget(self.search)
        self.chat_list = QListWidget()
        self.chat_list.setObjectName("chats")
        self.chat_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chat_list.itemClicked.connect(self._chat_clicked)
        self.chat_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.chat_list.customContextMenuRequested.connect(self._chat_context)
        layout.addWidget(self.chat_list, 1)
        bottom = QHBoxLayout()
        self.user_avatar = QLabel(host.account_name()[:1].upper())
        self.user_avatar.setFixedSize(28, 28)
        self.user_avatar.setAlignment(Qt.AlignCenter)
        self.user_avatar.setStyleSheet("background:#3D3929;color:#FAF9F5;border-radius:14px;font-weight:bold;")
        bottom.addWidget(self.user_avatar)
        bottom.addWidget(QLabel(host.account_name()), 1)
        self.settings_button = QToolButton()
        self.settings_button.setText("⚙")
        self.settings_button.setStyleSheet("font-size:18px;")
        self.settings_button.setToolTip("CopilotAI settings")
        self.settings_button.clicked.connect(self.open_settings)
        bottom.addWidget(self.settings_button)
        layout.addLayout(bottom)
        return sidebar

    def _make_main(self):
        main = QWidget()
        layout = QVBoxLayout(main)
        layout.setContentsMargins(0, 0, 0, 10)
        layout.setSpacing(6)
        header = QHBoxLayout()
        self.show_sidebar = QToolButton()
        self.show_sidebar.setText("☰")
        self.show_sidebar.setToolTip("Open chat history (Ctrl+B)")
        self.show_sidebar.clicked.connect(self.toggle_sidebar)
        header.addWidget(self.show_sidebar)
        self.chat_title = QLabel()
        self.chat_title.setStyleSheet("font-size:13px;font-weight:600;padding:4px 8px;")
        self.chat_title.setCursor(Qt.PointingHandCursor)
        self.chat_title.mousePressEvent = lambda _event: self.current and self.chat_menu(
            self.current, self.chat_title.mapToGlobal(self.chat_title.rect().bottomLeft()))
        header.addWidget(self.chat_title)
        header.addStretch()
        self.pin_button = QToolButton()
        self.pin_button.setToolTip("Pin chat")
        self.pin_button.clicked.connect(lambda: self.current and self.toggle_pin(self.current))
        header.addWidget(self.pin_button)
        layout.addLayout(header)

        self.conversation = QTextBrowser()
        self.conversation.setObjectName("conversation")
        self.conversation.setOpenLinks(False)
        self.conversation.anchorClicked.connect(self._link)
        self.conversation.setContextMenuPolicy(Qt.CustomContextMenu)
        self.conversation.customContextMenuRequested.connect(self._conversation_menu)
        layout.addWidget(self.conversation, 1)

        composer_wrap = QHBoxLayout()
        composer_wrap.setContentsMargins(36, 0, 36, 0)
        self.composer = QWidget()
        self.composer.setObjectName("composer")
        self.composer.setStyleSheet(f"QWidget#composer {{ background:white;border:1px solid {BORDER};border-radius:14px; }}")
        composer_layout = QVBoxLayout(self.composer)
        composer_layout.setContentsMargins(13, 9, 9, 8)
        self.prompt = QPlainTextEdit()
        self.prompt.setObjectName("prompt")
        self.prompt.setPlaceholderText("Message CopilotAI...")
        self.prompt.setFixedHeight(58)
        self.prompt.setMaximumHeight(170)
        self.prompt.textChanged.connect(self._grow_prompt)
        self.prompt.installEventFilter(self)
        composer_layout.addWidget(self.prompt)
        controls = QHBoxLayout()
        self.think_button = QToolButton()
        self.think_button.setText("✻ Think")
        self.think_button.setCheckable(True)
        self.think_button.setChecked(bool(self.settings["think"]))
        self.think_button.setToolTip("Enable extended reasoning for supported local models")
        self.think_button.toggled.connect(lambda value: self.settings.set("think", value))
        controls.addWidget(self.think_button)
        self.image_button = QToolButton()
        self.image_button.setText("🖼 Image")
        self.image_button.setCheckable(True)
        self.image_button.setToolTip("Create a picture from your next message (or start a message with /image)")
        self.image_button.toggled.connect(self._image_mode_changed)
        controls.addWidget(self.image_button)
        self.auto_listen_button = QCheckBox("Auto-listen")
        self.auto_listen_button.setToolTip("Listen locally for speech, then stop after a pause.")
        self.auto_listen_button.setChecked(bool(self.settings["auto_listen"]))
        self.auto_listen_button.toggled.connect(self._set_auto_listen)
        controls.addWidget(self.auto_listen_button)
        self.mic_button = QPushButton("Hold to talk")
        self.mic_button.setToolTip("Push to talk: hold while speaking and release to send.")
        self.mic_button.pressed.connect(self._ptt_pressed)
        self.mic_button.released.connect(self._ptt_released)
        self.mic_button.setContextMenuPolicy(Qt.CustomContextMenu)
        self.mic_button.customContextMenuRequested.connect(lambda pos: self.open_settings())
        controls.addWidget(self.mic_button)
        self.model_box = QComboBox()
        self.model_box.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.model_box.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        self.model_box.addItems(self.models or ["(no local models found)"])
        if self.settings["model"]:
            self.model_box.setCurrentText(self.settings["model"])
        self.model_box.currentTextChanged.connect(self._model_changed)
        controls.addWidget(self.model_box)
        self.send_button = QToolButton()
        self.send_button.setText("Send")
        self.send_button.setStyleSheet(f"background:{ACCENT};color:white;padding:6px 12px;")
        self.send_button.clicked.connect(self.send_or_stop)
        controls.addWidget(self.send_button)
        composer_layout.addLayout(controls)
        composer_wrap.addWidget(self.composer)
        layout.addLayout(composer_wrap)

        self.status = QLabel()
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setStyleSheet(f"color:{MUTED};font-size:11px;")
        layout.addWidget(self.status)
        return main

    @staticmethod
    def _list_models():
        models = []
        try:
            import ollama
            for item in ollama.list().models:
                name = item.model
                bare = name.split(":")[-1]
                if "embed" not in name and not (len(bare) >= 32 and all(c in "0123456789abcdef" for c in bare)):
                    if name not in models:
                        models.append(name)
        except Exception:
            pass
        try:
            default = ai_models.model_for("assistant")
            if default and default not in models:
                models.insert(0, default)
            elif default in models:
                models.remove(default)
                models.insert(0, default)
        except Exception:
            pass
        return models

    def _apply_sidebar(self, visible):
        self.sidebar.setVisible(visible)
        self.show_sidebar.setVisible(not visible)
        self.settings.set("sidebar", visible)

    def toggle_sidebar(self):
        self._apply_sidebar(not self.sidebar.isVisible())

    def refresh_sidebar(self):
        self.chat_list.clear()
        pinned, recent = self.chats.listed(self.search.text())
        for heading, entries in (("Pinned", pinned), ("Recent", recent)):
            if not entries:
                continue
            label_item = QListWidgetItem(heading)
            label_item.setFlags(Qt.NoItemFlags)
            label_item.setSizeHint(QSize(200, 25))
            self.chat_list.addItem(label_item)
            for chat in entries:
                item = QListWidgetItem()
                item.setData(Qt.UserRole, chat["id"])
                item.setSizeHint(QSize(200, 32))
                self.chat_list.addItem(item)
                self.chat_list.setItemWidget(item, ChatRow(self, chat))
                if self.current is chat:
                    item.setSelected(True)
        if not pinned and not recent:
            item = QListWidgetItem("No chats yet" if not self.search.text() else "No matching chats")
            item.setFlags(Qt.NoItemFlags)
            item.setForeground(QColor(MUTED))
            self.chat_list.addItem(item)

    def _chat_clicked(self, item):
        chat_id = item.data(Qt.UserRole)
        chat = self.chats.get(chat_id) if chat_id else None
        if chat is not None:
            self.open_chat(chat)

    def _chat_context(self, pos):
        item = self.chat_list.itemAt(pos)
        chat_id = item.data(Qt.UserRole) if item else None
        chat = self.chats.get(chat_id) if chat_id else None
        if chat is not None:
            self.chat_menu(chat, self.chat_list.viewport().mapToGlobal(pos))

    def chat_menu(self, chat, pos):
        menu = QMenu(self)
        menu.addAction("Unpin chat" if chat.get("pinned") else "Pin chat", lambda: self.toggle_pin(chat))
        menu.addAction("Rename...", lambda: self.rename_chat(chat))
        menu.addAction("Export as Markdown...", lambda: self.export_chat(chat))
        menu.addAction("Copy conversation", lambda: self.copy_chat(chat))
        menu.addSeparator()
        menu.addAction("Delete chat", lambda: self.delete_chat(chat))
        menu.exec(pos)

    def toggle_pin(self, chat):
        chat["pinned"] = not chat.get("pinned", False)
        self.chats.save()
        self.refresh_sidebar()
        self._update_header()

    def rename_chat(self, chat):
        from claudeai.app import ask_text
        ask_text(self.desktop, "Rename chat", "Chat name:", chat["title"],
                 lambda title: self._renamed(chat, title))

    def _renamed(self, chat, title):
        if title.strip():
            chat["title"] = title.strip()[:100]
            chat["titled"] = True
            self.chats.save()
            self.refresh_sidebar()
            self._update_header()

    def delete_chat(self, chat):
        answer = QMessageBox.question(self, "Delete chat",
                                      f'Delete "{chat["title"]}"? This cannot be undone.',
                                      QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer != QMessageBox.Yes:
            return
        if self.current is chat:
            self._stop_job()
            self.current = None
            self.expanded_thoughts.clear()
        self.chats.delete(chat["id"])
        self.refresh_sidebar()
        self.render()

    def new_chat(self):
        self.turn_id += 1
        self._stop_job()
        self.current = None
        self.expanded_thoughts.clear()
        self.refresh_sidebar()
        self.render()
        self.prompt.setFocus()

    def open_chat(self, chat):
        if self.current is chat:
            return
        self.turn_id += 1
        self._stop_job()
        self.current = chat
        self.expanded_thoughts.clear()
        model = chat.get("model", "")
        if model and model in self.models:
            self.model_box.setCurrentText(model)
        self.refresh_sidebar()
        self.render()
        self.prompt.setFocus()

    def _model_changed(self, model):
        self.settings.set("model", model)
        if self.current is not None:
            self.current["model"] = model
            self.chats.save()

    def _update_header(self):
        chat = self.current
        has_messages = bool(chat and chat.get("messages"))
        self.chat_title.setText(chat["title"] if has_messages else "")
        self.pin_button.setVisible(has_messages)
        self.pin_button.setText("★" if has_messages and chat.get("pinned") else "☆")
        self.pin_button.setStyleSheet(f"color:{ACCENT if has_messages and chat.get('pinned') else MUTED};font-size:17px;")
        self.pin_button.setToolTip("Unpin chat" if has_messages and chat.get("pinned") else "Pin chat")
        if self.frame is not None:
            self.frame.set_title(f"{chat['title']} - CopilotAI" if has_messages else "CopilotAI")

    def render(self):
        self._update_header()
        chat = self.current
        if chat is None or not chat.get("messages"):
            hour = host.now().hour
            greeting = "morning" if 5 <= hour < 12 else "afternoon" if hour < 17 else "evening"
            name = html.escape(host.account_name())
            self.conversation.setHtml(
                f"<html><body style='font-family:Segoe UI;color:{TEXT};'><div align='center' "
                f"style='margin-top:100px'><span style='font-size:27px;font-family:Georgia'>"
                f"Good {greeting}, {name}</span><p style='color:{MUTED}'>What would you like to explore?</p>"
                f"</div></body></html>")
            return
        parts = []
        for index, message in enumerate(chat["messages"]):
            role = message.get("role")
            content = message.get("content", "")
            if role == "user":
                parts.append(f"<p style='margin-top:20px'><b>{html.escape(host.account_name())}</b></p>"
                             f"<div style='background:#EDEAE0;padding:10px;border-radius:8px'>"
                             f"{html.escape(content).replace(chr(10), '<br>')}</div>")
            elif role == "assistant":
                thought = ""
                if message.get("thinking"):
                    expanded = index in self.expanded_thoughts
                    thought = (f'<p><a href="think:{index}" style="color:{MUTED};text-decoration:none">'
                               f'{"▾" if expanded else "▸"} Thought process</a></p>')
                    if expanded:
                        content = html.escape(message["thinking"]).replace("\n", "<br>")
                        thought += (f'<div style="border-left:2px solid {BORDER};padding:7px 10px;'
                                    f'color:{MUTED};font-size:12px">{content}</div>')
                content = imagetool.visible(content)
                body = _markdown_html(content) if content else ""
                if not body and not message.get("images") and not message.get("image_note"):
                    body = "<i>(no response)</i>"
                if message.get("streaming") and not content:
                    body = f"<span style='color:#8B877C'>{message.get('image_status') or 'Thinking...'}</span>"
                body += self._images_html(index, message)
                parts.append(f"<p style='margin-top:16px'><b style='color:{ACCENT}'>CopilotAI</b></p>"
                             f"{thought}<div>{body}</div>")
                if not message.get("streaming"):
                    parts.append(f"<p><a href='copy:{index}'>Copy</a>"
                                 f"{' &nbsp; <a href=retry:0>Retry</a>' if index == self._last_assistant_index() else ''}"
                                 f"</p>")
        html_body = "".join(parts)
        self.conversation.setHtml(f"<html><body style='font-family:Segoe UI;color:{TEXT};'>{html_body}</body></html>")
        scrollbar = self.conversation.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _images_html(self, index, message):
        out = []
        for j, item in enumerate(message.get("images") or []):
            path = Path(item.get("path", ""))
            if path.is_file():
                url = QUrl.fromLocalFile(str(path)).toString()
                out.append(f"<p><a href='img:open:{index}:{j}'><img src='{url}' width='{item.get('show', 380)}'></a><br>"
                           f"<span style='color:{MUTED};font-size:11px'>{html.escape(item.get('prompt', ''))}</span><br>"
                           f"<a href='img:open:{index}:{j}'>Open</a> &nbsp; <a href='img:save:{index}:{j}'>Save as...</a>"
                           f" &nbsp; <a href='img:redo:{index}:{j}'>New variation</a></p>")
            else:
                out.append(f"<p style='color:{MUTED}'><i>(image no longer on disk: {html.escape(path.name)})</i></p>")
        if message.get("image_busy"):
            progress = message.get("image_progress")
            step = f" - step {progress[0]} of {progress[1]}" if progress else ""
            out.append(f"<p style='color:{MUTED}'><i>{message.get('image_status') or 'Creating the picture'}"
                       f"{step}...</i></p>")
        if message.get("image_note"):
            out.append(f"<p style='color:{MUTED}'><i>{html.escape(message['image_note'])}</i></p>")
        return "".join(out)

    # ---- the image tool ------------------------------------------------------------------------------
    def _image_engine(self):
        """(model key, '') when pictures can be made, else (None, why not)."""
        import imagegen
        if not imagegen._engine_ready():
            return None, ("The local image engine isn't set up yet. Open Copilot Image Creator, then choose "
                          "Set Up Image Engine.")
        wanted = self.settings["image_model"]
        for key in [wanted] + [k for k in imagegen.MODEL_INFO if k != wanted]:
            if key in imagegen.MODEL_INFO and imagegen._installed(key):
                return key, ""
        return None, "No image model is installed yet. Open Copilot Image Creator and install one."

    def _image_mode_changed(self, on):
        self.prompt.setPlaceholderText("Describe the picture you'd like..." if on else "Message CopilotAI...")
        if on:
            _key, why = self._image_engine()
            if why:
                self.status.setText(why)

    def _image_request(self, request):
        """The Image button or /image: the model only writes the Stable Diffusion prompt."""
        reply = {"role": "assistant", "content": "", "streaming": True, "image_status": "Writing the image prompt..."}
        self.current["messages"].append(reply)
        self.render()
        model = self.model_box.currentText()
        self.status.setText(f"{model} is writing the image prompt...")
        turn = self.turn_id

        def written(text, error):
            if turn != self.turn_id:
                return
            self.job = None
            prompt = "" if error else imagetool.clean_prompt(text)
            reply["content"] = "Here's what I made."
            self._run_image(reply, prompt or request, imagetool.guess_shape(request))

        self.job = broker.get().chat(
            model, [{"role": "system", "content": imagetool.WRITER_SYSTEM}, {"role": "user", "content": request}],
            {"temperature": 0.7, "num_predict": 220}, written, broker.FOREGROUND, think=False)
        self._update_send_button()

    def _run_image(self, reply, prompt, shape):
        """Start the local image engine for this reply (the chat model steps aside to free graphics memory)."""
        from claudecore.ai import llmlog as furlog
        import imagegen
        key, why = self._image_engine()
        if key is None:
            reply.pop("streaming", None)
            reply["image_note"] = why
            self._image_finished(reply)
            return
        if self.settings["image_free_memory"]:
            for model_id, state in llm_server.model_states().items():
                if state == "loaded":
                    llm_server.unload(model_id)
        width, height = imagetool.SIZES[key][shape]
        host.my_pictures().mkdir(parents=True, exist_ok=True)
        output = host.my_pictures() / f"CopilotAI {time.strftime('%Y%m%d-%H%M%S')}.png"
        seed = random.randint(1, 2 ** 31 - 1)
        furlog.event("IMAGE REQUEST (CopilotAI)", prompt, model=key, size=f"{width}x{height}",
                     steps=int(self.settings["image_steps"]), seed=seed, output=output.name)
        reply.pop("streaming", None)
        reply.update(image_busy=True, image_status="Loading the image model", image_progress=None)
        self.status.setText(f"Creating the picture locally with {imagegen.MODEL_INFO[key][0]}...")
        turn = self.turn_id
        task = imagegen.ImageTask(
            "generate", key, prompt=prompt, negative_prompt=imagetool.NEGATIVE, width=width, height=height,
            steps=int(self.settings["image_steps"]), guidance=7.0, seed=seed, output=output)
        self.image_task = task
        self._update_send_button()

        def progress(current, total):
            if turn == self.turn_id:
                reply["image_status"] = "Creating the picture"
                reply["image_progress"] = (current, total)
                if not self.render_timer.isActive():
                    self.render_timer.start(150)

        def completed(result):
            path = Path(result or output)
            reply.setdefault("images", []).append(
                {"path": str(path), "prompt": prompt, "model": key, "shape": shape,
                 "show": 380 if shape != "wide" else 440})
            self.status.setText(f"Saved to My Pictures\\{path.name}")

        def failed(message):
            reply["image_note"] = "The picture couldn't be made: " + (message.strip().splitlines() or ["unknown error"])[-1]

        def cancelled():
            reply["image_note"] = "Picture creation was cancelled."

        def finished():
            reply.pop("image_busy", None)
            reply.pop("image_progress", None)
            self.image_task = None
            if turn == self.turn_id:
                self._image_finished(reply)
            else:
                self.chats.save()
            self._close_when_idle()

        task.progress.connect(progress)
        task.completed.connect(completed)
        task.failed.connect(failed)
        task.cancelled.connect(cancelled)
        task.finished.connect(finished)
        self.render()
        task.start()

    def _image_finished(self, reply):
        self.chats.touch(self.current)
        self.render()
        self.refresh_sidebar()
        self._update_send_button()
        self._finish_turn(reply)

    def _cancel_image(self):
        if self.image_task is not None and self.image_task.isRunning():
            self.image_task.cancel()

    def _image_link(self, value):
        action, _, rest = value.partition(":")
        index, _, j = rest.partition(":")
        try:
            message = self.current["messages"][int(index)]
            item = message["images"][int(j)]
        except (ValueError, IndexError, KeyError):
            return
        path = Path(item["path"])
        if action == "open" and path.is_file():
            host.open_file(self.desktop, path)
        elif action == "save" and path.is_file():
            from PySide6.QtWidgets import QFileDialog
            target, _ = QFileDialog.getSaveFileName(self, "Save picture", path.name, "PNG image (*.png)")
            if target:
                import shutil
                try:
                    shutil.copyfile(path, target)
                except OSError as exc:
                    QMessageBox.critical(self, "Save picture", f"Could not save the picture:\n{exc}")
        elif action == "redo" and self.job is None and self.image_task is None:
            message["streaming"] = True
            self._run_image(message, item["prompt"], item.get("shape", "square"))

    def _last_assistant_index(self):
        if self.current is None:
            return -1
        return max((i for i, message in enumerate(self.current["messages"])
                    if message.get("role") == "assistant"), default=-1)

    def _link(self, url):
        kind, _, value = url.toString().partition(":")
        if self.current is None:
            return
        if kind == "img":
            self._image_link(value)
        elif kind == "retry":
            self.retry()
        elif kind == "copy" and value.isdigit():
            index = int(value)
            messages = self.current["messages"]
            if 0 <= index < len(messages):
                from PySide6.QtWidgets import QApplication
                QApplication.clipboard().setText(messages[index].get("content", ""))
        elif kind == "think" and value.isdigit():
            index = int(value)
            if index in self.expanded_thoughts:
                self.expanded_thoughts.remove(index)
            else:
                self.expanded_thoughts.add(index)
            self.render()

    def _conversation_menu(self, pos):
        menu = QMenu(self)
        menu.addAction("Copy last response", self.copy_last_reply)
        menu.addAction("Copy conversation", lambda: self.current and self.copy_chat(self.current))
        menu.addAction("Export conversation...", lambda: self.current and self.export_chat(self.current))
        menu.exec(self.conversation.mapToGlobal(pos))

    def copy_last_reply(self):
        if self.current is not None:
            answer = next((m["content"] for m in reversed(self.current["messages"])
                           if m.get("role") == "assistant"), "")
            if answer:
                from PySide6.QtWidgets import QApplication
                QApplication.clipboard().setText(answer)

    def copy_chat(self, chat):
        from PySide6.QtWidgets import QApplication
        text = "\n\n".join(f"## {'You' if m['role'] == 'user' else 'CopilotAI'}\n\n{m.get('content', '')}"
                           for m in chat.get("messages", []))
        QApplication.clipboard().setText(text)

    def export_chat(self, chat):
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(self, "Export chat", f"{chat['title']}.md",
                                               "Markdown (*.md);;Text files (*.txt)")
        if not path:
            return
        text = f"# {chat['title']}\n\n" + "\n\n".join(
            f"## {'You' if m['role'] == 'user' else 'CopilotAI'}\n\n{m.get('content', '')}"
            for m in chat.get("messages", []))
        try:
            Path(path).write_text(text, encoding="utf-8")
        except OSError as exc:
            QMessageBox.critical(self, "Export chat", f"Could not write the conversation:\n{exc}")

    def _grow_prompt(self):
        height = self.prompt.document().size().height()
        line_height = self.prompt.fontMetrics().lineSpacing()
        self.prompt.setFixedHeight(int(min(170, max(58, height * line_height + 18))))

    def eventFilter(self, obj, event):
        if obj is self.prompt and event.type() == event.Type.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                if event.modifiers() & Qt.ShiftModifier:
                    return False
                self.send_or_stop()
                return True
        return super().eventFilter(obj, event)

    def send_or_stop(self):
        if self.job is not None:
            self.stop()
            return
        text = self.prompt.toPlainText().strip()
        if text:
            self.prompt.clear()
            self.submit(text)

    def submit(self, text):
        if not self.models:
            QMessageBox.warning(self, "CopilotAI", "No local language model is available. Install one in "
                                "Control Panel > AI Models, then restart CopilotAI.")
            return
        if self.capture is not None and self.capture_mode == "auto":
            self._stop_capture(transcribe=False)
        if self.current is None:
            self.current = self.chats.new(self.model_box.currentText())
        self.current["model"] = self.model_box.currentText()
        self.current["messages"].append({"role": "user", "content": text})
        if len(self.current["messages"]) == 1 and self.settings["auto_title"]:
            self.current["title"] = self._title_from_prompt(text)
            self.current["titled"] = True
        self.chats.touch(self.current)
        self.refresh_sidebar()
        request = text
        if text.lower().startswith("/image ") or text.lower() == "/image":
            request = text[6:].strip()
        if self.image_button.isChecked() or request != text:
            self.image_button.setChecked(False)
            if not request:
                self.status.setText("Tell me what to draw, e.g. /image a lighthouse at sunset")
                return
            if self._image_engine()[0] is None:
                self.current["messages"].append(
                    {"role": "assistant", "content": "", "image_note": self._image_engine()[1]})
                self.render()
                return
            self._image_request(request)
            return
        self._generate()

    @staticmethod
    def _title_from_prompt(text):
        title = " ".join(text.split())
        return title[:57] + ("..." if len(title) > 60 else "")

    def _generate(self):
        chat = self.current
        model = self.model_box.currentText()
        system = self.settings["instructions"] or DEFAULT_INSTRUCTIONS
        image_on = self.settings["image_tool"] and self._image_engine()[0] is not None
        if image_on:
            system += imagetool.ADDENDUM
        messages = [{"role": "system", "content": system}]
        budget = int(self.settings["context"]) * 3
        used = len(messages[0]["content"])
        kept = []
        for item in reversed(chat["messages"]):
            content = item.get("content", "")
            if item.get("images"):
                content = (content + "\n" + imagetool.history_note(item["images"])).strip()
            used += len(content)
            if used > budget and kept:
                break
            kept.insert(0, {"role": item["role"], "content": content})
        messages.extend(kept)
        reply = {"role": "assistant", "content": "", "streaming": True}
        chat["messages"].append(reply)
        self.render()
        self.status.setText(f"Generating with {model} locally...")
        self._update_send_button()
        turn = self.turn_id

        def on_chunk(text):
            if turn == self.turn_id:
                reply["content"] = text
                if not self.render_timer.isActive():
                    self.render_timer.start(100)

        def on_thinking(text):
            if turn == self.turn_id:
                reply["thinking"] = text
                if not self.render_timer.isActive():
                    self.render_timer.start(100)

        def on_done(text, error):
            if turn != self.turn_id:
                return
            self.job = None
            reply.pop("streaming", None)
            if error == "stopped":
                reply["stopped"] = True
            elif error:
                reply["content"] = f"Local model error: {error}"
            else:
                reply["content"] = text
            if not error and image_on:
                clean, picture, shape = imagetool.extract(text)
                if picture:
                    reply["content"] = clean
                    self.chats.touch(chat)
                    self._run_image(reply, picture, shape)
                    return
                reply["content"] = clean
            self.chats.touch(chat)
            self.render()
            self.refresh_sidebar()
            self._update_send_button()
            if error:
                self.status.setText("Response stopped." if error == "stopped" else "The local model request failed.")
                self._resume_auto_listen()
                self._close_when_idle()
                return
            self._finish_turn(reply)
        self.job = broker.get().stream(
            model, messages, {"num_ctx": int(self.settings["context"]),
                              "temperature": float(self.settings["temperature"])},
            on_chunk, on_done, broker.FOREGROUND, think=self.think_button.isChecked(),
            on_thinking=on_thinking)
        self._update_send_button()

    def _finish_turn(self, reply):
        if self.settings["speak_replies"] and self._voice_ready() and reply.get("content"):
            self._speak(reply["content"])
        else:
            if not self.status.text().startswith("Saved to"):
                self.status.setText("Ready.")
            self._resume_auto_listen()
            self._close_when_idle()

    def retry(self):
        if self.current is None or self.job is not None or self.image_task is not None:
            return
        messages = self.current["messages"]
        while messages and messages[-1].get("role") == "assistant":
            messages.pop()
        if messages and messages[-1].get("role") == "user":
            self._generate()

    def stop(self):
        if self.job is not None:
            self.job.stop()
        self._cancel_image()

    def _stop_job(self):
        self._cancel_image()
        if self.job is not None:
            self.job.stop()
            self.job = None
        self._update_send_button()

    def _update_send_button(self):
        busy = self.job is not None or self.image_task is not None
        self.send_button.setText("Stop" if busy else "Send")
        self.send_button.setToolTip("Stop response" if busy else "Send message")

    def open_settings(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("CopilotAI Settings")
        dialog.setMinimumWidth(500)
        dialog.setStyleSheet("QDialog { background:#ECE9D8; } QLabel, QCheckBox { font-family:Tahoma;font-size:11px; }"
                             "QPushButton,QComboBox,QSpinBox,QDoubleSpinBox { font-family:Tahoma;font-size:11px; }")
        outer = QVBoxLayout(dialog)
        form = QFormLayout()
        outer.addLayout(form)

        model = QComboBox()
        model.addItems(self.models or ["(no local models found)"])
        model.setCurrentText(self.settings["model"])
        form.addRow("Default model:", model)
        temperature = QDoubleSpinBox()
        temperature.setRange(0.0, 2.0)
        temperature.setSingleStep(0.1)
        temperature.setValue(float(self.settings["temperature"]))
        form.addRow("Creativity:", temperature)
        context = QSpinBox()
        context.setRange(1024, 131072)
        context.setSingleStep(1024)
        context.setValue(int(self.settings["context"]))
        form.addRow("Context window (tokens):", context)
        instructions = QPlainTextEdit(self.settings["instructions"])
        instructions.setMinimumHeight(95)
        form.addRow("Custom instructions:", instructions)
        think = QCheckBox("Use extended thinking when the selected model supports it")
        think.setChecked(bool(self.settings["think"]))
        form.addRow("Reasoning:", think)
        auto_title = QCheckBox("Automatically title new chats from the opening message")
        auto_title.setChecked(bool(self.settings["auto_title"]))
        form.addRow("Chat history:", auto_title)

        import imagegen
        image_tool = QCheckBox("Let the model create pictures when asked")
        image_tool.setChecked(bool(self.settings["image_tool"]))
        form.addRow("Images:", image_tool)
        image_model = QComboBox()
        for key, info in imagegen.MODEL_INFO.items():
            image_model.addItem(info[0] if isinstance(info, (tuple, list)) else str(key), key)
        image_model.setCurrentIndex(max(0, image_model.findData(self.settings["image_model"])))
        form.addRow("Image model:", image_model)
        image_steps = QSpinBox()
        image_steps.setRange(5, 60)
        image_steps.setValue(int(self.settings["image_steps"]))
        form.addRow("Image steps:", image_steps)
        free_memory = QCheckBox("Unload the chat model while drawing (frees graphics memory)")
        free_memory.setChecked(bool(self.settings["image_free_memory"]))
        form.addRow("", free_memory)
        why = self._image_engine()[1]
        creator = QPushButton("Open Copilot Image Creator...")
        creator.clicked.connect(lambda: imagegen.open_imagegen(self.desktop))
        form.addRow(why or "Image engine ready.", creator)
        form.addRow(QLabel("<b>Voice (offline)</b>"))
        voice = QComboBox()
        voice.setMaxVisibleItems(24)
        installed = self._installed_voices()
        for title, voice_ids in voicecatalog.grouped():
            voice.addItem(f"\u2014 {title} \u2014")
            header = voice.model().item(voice.count() - 1)
            header.setEnabled(False)
            font = header.font()
            font.setBold(True)
            header.setFont(font)
            for voice_id in voice_ids:
                voice.addItem("   " + VOICES[voice_id] + ("" if voice_id in installed else " (download needed)"),
                              voice_id)
        voice.setCurrentIndex(max(1, voice.findData(self.settings["voice_id"])))
        form.addRow("Spoken reply voice:", voice)
        speech_rate = QDoubleSpinBox()
        speech_rate.setRange(0.7, 1.5)
        speech_rate.setSingleStep(0.05)
        speech_rate.setValue(float(self.settings["speech_rate"]))
        speech_rate.setSuffix("× speed")
        form.addRow("Speech rate:", speech_rate)
        speak_replies = QCheckBox("Speak assistant replies aloud")
        speak_replies.setChecked(bool(self.settings["speak_replies"]))
        form.addRow("Text to speech:", speak_replies)
        listen = QCheckBox("Enable automatic listening (microphone stays active while idle)")
        listen.setChecked(bool(self.settings["auto_listen"]))
        form.addRow("Listening mode:", listen)

        self.voice_license_ack = QCheckBox("I reviewed the speech-model and selected voice licenses.")
        outer.addWidget(self.voice_license_ack)
        links = QLabel(
            '<a href="https://huggingface.co/Systran/faster-whisper-base.en">Whisper model (MIT)</a>'
            ' &nbsp;|&nbsp; <a href="https://github.com/OHF-Voice/piper1-gpl">Piper engine (GPL-3.0)</a>'
            ' &nbsp;|&nbsp; '
            '<a href="https://huggingface.co/rhasspy/piper-voices/tree/main/en">Piper voice licenses</a>')
        links.setOpenExternalLinks(True)
        outer.addWidget(links)
        voice_status = QLabel(self._voice_status())
        voice_status.setWordWrap(True)
        outer.addWidget(voice_status)
        voice_buttons = QHBoxLayout()
        setup_voice = QPushButton("Set Up Speech Engine")
        setup_voice.clicked.connect(lambda: self._setup_voice(voice_status))
        voice_buttons.addWidget(setup_voice)
        install_voice = QPushButton("Download Selected Voice")
        install_voice.clicked.connect(lambda: self._install_voice(voice.currentData(), voice_status))
        voice_buttons.addWidget(install_voice)
        test_voice = QPushButton("Test Voice")
        test_voice.clicked.connect(lambda: self._test_voice(voice.currentData(), speech_rate.value()))
        voice_buttons.addWidget(test_voice)
        outer.addLayout(voice_buttons)
        info = QLabel("Speech recognition uses the local English Whisper model. Auto-listen detects speech and "
                      "stops after a pause. You can always use push-to-talk instead.")
        info.setWordWrap(True)
        outer.addWidget(info)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        outer.addWidget(buttons)
        if dialog.exec() != QDialog.Accepted:
            return

        self.settings.set("model", model.currentText())
        self.settings.set("temperature", temperature.value())
        self.settings.set("context", context.value())
        self.settings.set("instructions", instructions.toPlainText().strip() or DEFAULT_INSTRUCTIONS)
        self.settings.set("think", think.isChecked())
        self.settings.set("auto_title", auto_title.isChecked())
        self.settings.set("image_tool", image_tool.isChecked())
        self.settings.set("image_model", image_model.currentData())
        self.settings.set("image_steps", image_steps.value())
        self.settings.set("image_free_memory", free_memory.isChecked())
        self.settings.set("voice_id", voice.currentData())
        self.settings.set("speech_rate", speech_rate.value())
        self.settings.set("speak_replies", speak_replies.isChecked())
        self.model_box.setCurrentText(model.currentText())
        self.think_button.setChecked(think.isChecked())
        self._set_auto_listen(listen.isChecked())

    def _installed_voices(self):
        return {voice_id for voice_id in VOICES
                if (MODELS_ROOT / voice_id / f"{voice_id}.onnx").is_file()
                and (MODELS_ROOT / voice_id / f"{voice_id}.onnx.json").is_file()}

    def _voice_ready(self):
        return _engine_ready() and _models_ready() and self.settings["voice_id"] in self._installed_voices()

    @staticmethod
    def _voice_status():
        if not _engine_ready():
            return "Speech engine not set up. Setup downloads the engine and local Whisper/Piper models."
        if not _models_ready():
            return "Speech models are incomplete. Set up the local speech engine again."
        return "Local speech recognition and synthesis are ready."

    def _setup_voice(self, status):
        if not self.voice_license_ack.isChecked():
            QMessageBox.warning(self, "CopilotAI Voice", "Review the engine and voice licenses before setup.")
            return
        if not _engine_ready() or not _models_ready():
            if QMessageBox.question(
                    self, "Set Up Local Speech",
                    "Setup downloads a private speech runtime, an English Whisper model, and the Lessac Piper "
                    "voice. Additional Piper voices can be installed separately. Download now?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
                return
            self._start_voice_task("setup", status)
        else:
            status.setText(self._voice_status())

    def _install_voice(self, voice_id, status):
        if not self.voice_license_ack.isChecked():
            QMessageBox.warning(self, "CopilotAI Voice", "Review the selected voice license before downloading.")
            return
        if not _engine_ready():
            QMessageBox.warning(self, "CopilotAI Voice", "Set up the local speech engine first.")
            return
        if voice_id in self._installed_voices():
            status.setText(f"{VOICES[voice_id]} is already installed.")
            return
        if QMessageBox.question(self, "Download voice",
                                f"Download {VOICES[voice_id]} from Hugging Face into Local Storage? "
                                f"This voice is about {voicecatalog.size_mb(voice_id)} MB.",
                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
            return
        self._start_voice_task("install-voice", status, voice_id=voice_id)

    def _refresh_voice_controls(self):
        ready = self._voice_ready()
        idle = (self.job is None and self.voice_task is None and not self.speaking
                and self.player.playbackState() != QMediaPlayer.PlaybackState.PlayingState)
        self.mic_button.setEnabled(ready and idle)
        if not ready:
            self.auto_listen_button.blockSignals(True)
            self.auto_listen_button.setChecked(False)
            self.auto_listen_button.blockSignals(False)
            self.auto_listen_button.setEnabled(False)
        else:
            self.auto_listen_button.setEnabled(self.job is None and self.voice_task is None)
            if self.settings["auto_listen"] and not self.auto_listen_button.isChecked():
                self.auto_listen_button.blockSignals(True)
                self.auto_listen_button.setChecked(True)
                self.auto_listen_button.blockSignals(False)

    def _test_voice(self, voice_id, rate):
        if voice_id not in self._installed_voices() or not _engine_ready():
            QMessageBox.information(self, "CopilotAI Voice", "Set up speech and download this voice first.")
            return
        self._speak("Hello! This is a preview of your selected CopilotAI voice.", voice_id=voice_id, rate=rate)

    def _set_auto_listen(self, enabled, announce=True):
        enabled = bool(enabled)
        self.settings.set("auto_listen", enabled)
        if enabled and not self._voice_ready():
            if self.auto_listen_button.isChecked():
                self.auto_listen_button.blockSignals(True)
                self.auto_listen_button.setChecked(False)
                self.auto_listen_button.blockSignals(False)
            if announce:
                QMessageBox.information(self, "CopilotAI Voice", "Set up local speech models before enabling "
                                        "automatic listening.")
            self._refresh_voice_controls()
            return
        if not enabled and self.capture_mode == "auto":
            self._stop_capture(transcribe=False)
        elif enabled and self.job is None and self.voice_task is None:
            self._start_capture("auto")
        self._refresh_voice_controls()

    def _resume_auto_listen(self):
        if (self.settings["auto_listen"] and self.job is None and self.voice_task is None
                and not self.speaking and not self.closing
                and self.player.playbackState() != QMediaPlayer.PlaybackState.PlayingState):
            QTimer.singleShot(500, lambda: self._start_capture("auto")
                              if self.settings["auto_listen"] and self.capture is None else None)

    def _ptt_pressed(self):
        if self.settings["auto_listen"]:
            self.auto_listen_button.setChecked(False)
            return
        self._start_capture("ptt")

    def _ptt_released(self):
        if self.capture_mode == "ptt":
            self._stop_capture(transcribe=True)

    def _start_capture(self, mode):
        if (self.capture is not None or self.job is not None or self.voice_task is not None
                or self.speaking or self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState):
            return
        if not self._voice_ready():
            self.status.setText("Set up the local speech engine before using the microphone.")
            return
        device = QMediaDevices.defaultAudioInput()
        if device.isNull():
            self.status.setText("No microphone found. Connect one and check Windows privacy settings.")
            if mode == "auto":
                self.auto_listen_button.setChecked(False)
            return
        preferred = device.preferredFormat()
        candidates = {SAMPLE_RATE, 22050, 44100, 48000, preferred.sampleRate()}
        channels = {1, 2, preferred.channelCount()}
        audio_format = None
        for rate in sorted((r for r in candidates if r > 0), key=lambda r: abs(r - SAMPLE_RATE)):
            for count in sorted(c for c in channels if c > 0):
                candidate = QAudioFormat()
                candidate.setSampleRate(rate)
                candidate.setChannelCount(count)
                candidate.setSampleFormat(QAudioFormat.Int16)
                if device.isFormatSupported(candidate):
                    audio_format = candidate
                    break
            if audio_format is not None:
                break
        if audio_format is None:
            self.status.setText("The microphone does not support PCM recording.")
            return
        self.capture_format = audio_format
        self.capture = QAudioSource(device, audio_format, self)
        self.capture_io = self.capture.start()
        if self.capture_io is None or self.capture.error() != QAudio.Error.NoError:
            self.status.setText("Could not open the microphone. Check its privacy permissions.")
            self.capture.deleteLater()
            self.capture = self.capture_io = None
            return
        self.capture_mode = mode
        self.capture_chunks = []
        self.pre_roll.clear()
        self.pre_roll_duration = 0.0
        self.speech_detected = False
        self.silence_duration = 0.0
        self.capture_io.readyRead.connect(self._read_capture)
        if mode == "auto":
            self.status.setText("Auto-listening — microphone active. Speech is processed on this PC.")
        else:
            self.status.setText("Listening — release the button when you are done.")
            self.mic_button.setText("Listening...")

    def _read_capture(self):
        if self.capture_io is None:
            return
        data = bytes(self.capture_io.readAll().data())
        if not data:
            return
        if self.capture_mode == "ptt":
            self.capture_chunks.append(data)
            if self._capture_seconds() >= MAX_RECORD_SECONDS:
                self._stop_capture(transcribe=True)
            return
        duration = len(data) / (self.capture_format.sampleRate() * self.capture_format.channelCount() * 2)
        samples = array.array("h")
        samples.frombytes(data[:len(data) // 2 * 2])
        rms = math.sqrt(sum(sample * sample for sample in samples) / max(1, len(samples)))
        if rms >= AUTO_VAD_THRESHOLD:
            if not self.speech_detected:
                self.capture_chunks = [chunk for chunk, _seconds in self.pre_roll]
                self.speech_detected = True
                self.status.setText("Speech detected — listening...")
            self.capture_chunks.append(data)
            self.silence_duration = 0.0
        elif self.speech_detected:
            self.capture_chunks.append(data)
            self.silence_duration += duration
            if self.silence_duration >= AUTO_SILENCE_SECONDS:
                self._stop_capture(transcribe=True)
                return
        else:
            self.pre_roll.append((data, duration))
            self.pre_roll_duration += duration
            while self.pre_roll and self.pre_roll_duration > 0.4:
                _chunk, old_duration = self.pre_roll.popleft()
                self.pre_roll_duration -= old_duration
        if self._capture_seconds() >= MAX_RECORD_SECONDS:
            self._stop_capture(transcribe=self.speech_detected)

    def _capture_seconds(self):
        if self.capture_format is None:
            return 0.0
        size = sum(map(len, self.capture_chunks))
        return size / (self.capture_format.sampleRate() * self.capture_format.channelCount() * 2)

    def _stop_capture(self, transcribe):
        if self.capture is None:
            return
        source, io = self.capture, self.capture_io
        mode = self.capture_mode
        if io is not None and mode == "ptt":
            data = bytes(io.readAll().data())
            if data:
                self.capture_chunks.append(data)
        source.stop()
        source.deleteLater()
        self.capture = self.capture_io = None
        chunks = self.capture_chunks
        self.capture_chunks = []
        self.capture_mode = ""
        if hasattr(self, "mic_button"):
            self.mic_button.setText("Hold to talk")
        if not transcribe or not chunks:
            self._resume_auto_listen()
            return
        raw = b"".join(chunks)
        min_bytes = self.capture_format.sampleRate() * self.capture_format.channelCount() * 2 // 2
        if len(raw) < min_bytes:
            self.status.setText("I didn't catch enough speech. Try speaking a little longer.")
            self._resume_auto_listen()
            return
        self._audio_temp = _temporary_audio_path()
        try:
            with wave.open(str(self._audio_temp), "wb") as wav_file:
                wav_file.setnchannels(self.capture_format.channelCount())
                wav_file.setsampwidth(2)
                wav_file.setframerate(self.capture_format.sampleRate())
                wav_file.writeframes(raw[:len(raw) // 2 * 2])
        except OSError as exc:
            self.status.setText(f"Could not prepare audio for local transcription: {exc}")
            self._delete_temp_audio("_audio_temp")
            return
        self._start_voice_task("transcribe", self.status, audio=self._audio_temp)

    def _voice_task_done(self, operation, result):
        if self.closing:
            self._delete_temp_audio("_audio_temp")
            self._delete_temp_audio("_reply_audio")
            return
        if operation == "transcribe":
            self._delete_temp_audio("_audio_temp")
            if result.strip():
                self.submit(result.strip())
            else:
                self.status.setText("No speech was recognized. Try again.")
                self._resume_auto_listen()
        elif operation == "speak":
            self._reply_audio = Path(result)
            self.audio_output.setVolume(0.0 if host.muted() else 1.0)
            self.player.setSource(QUrl.fromLocalFile(result))
            self.speaking = True
            self.player.play()
            self._refresh_voice_controls()
            self.status.setText("Speaking with the selected local voice...")
        else:
            self._refresh_voice_controls()
            self.status.setText("Local speech model is ready.")

    def _start_voice_task(self, operation, status, **options):
        if self.voice_task is not None:
            self.status.setText("Another local speech operation is already running.")
            return
        task = VoiceTask(operation, **options)
        self.voice_task = task
        def set_status(text):
            self.status.setText(text)
            if status is not self.status and isValid(status):
                status.setText(text)

        task.message.connect(set_status)
        task.completed.connect(lambda result, op=operation: self._voice_task_done(op, result))
        if operation == "setup":
            task.completed.connect(lambda _result: set_status(self._voice_status()))
        elif operation == "install-voice" and options.get("voice_id") in VOICES:
            voice_id = options["voice_id"]
            task.completed.connect(lambda _result: set_status(f"{VOICES[voice_id]} is installed."))
        task.failed.connect(lambda error: self._voice_task_failed(error))
        task.cancelled.connect(self._voice_task_cancelled)
        task.finished.connect(lambda: self._voice_task_finished(task))
        task.start()

    def _voice_task_cancelled(self):
        self._delete_temp_audio("_audio_temp")
        self._delete_temp_audio("_reply_audio")
        if not self.closing:
            self.status.setText("Local speech operation cancelled.")
        self._resume_auto_listen()
        self._close_when_idle()

    def _voice_task_failed(self, error):
        self._delete_temp_audio("_audio_temp")
        self._delete_temp_audio("_reply_audio")
        self.status.setText("The local speech operation failed.")
        if not self.closing:
            QMessageBox.critical(self, "CopilotAI Voice", error)
        self._resume_auto_listen()
        self._close_when_idle()

    def _voice_task_finished(self, task):
        if self.voice_task is task:
            self.voice_task = None
        self._refresh_voice_controls()
        self._resume_auto_listen()
        self._close_when_idle()

    def _speak(self, text, voice_id=None, rate=None):
        voice_id = voice_id or self.settings["voice_id"]
        if voice_id not in self._installed_voices():
            self.status.setText("The selected voice is not installed. Choose a voice in Settings.")
            self._resume_auto_listen()
            return
        self._reply_audio = _temporary_audio_path()
        self._start_voice_task("speak", self.status, text=text, output=self._reply_audio,
                               voice_id=voice_id,
                               length_scale=1.0 / (rate or self.settings["speech_rate"]))

    def _playback_end(self, status):
        from PySide6.QtMultimedia import QMediaPlayer
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.speaking = False
            self.player.setSource(QUrl())
            self._delete_temp_audio("_reply_audio")
            self.status.setText("Ready.")
            self._refresh_voice_controls()
            self._resume_auto_listen()

    def _delete_temp_audio(self, attr):
        path = getattr(self, attr)
        if path is not None:
            try:
                Path(path).unlink(missing_ok=True)
            except OSError as exc:
                self.status.setText(f"Could not remove temporary audio: {exc}")
            setattr(self, attr, None)

    def _auto_speak_error(self, _error, message):
        self.speaking = False
        self._delete_temp_audio("_reply_audio")
        self.status.setText(f"Speech playback failed: {message}")
        self._refresh_voice_controls()
        self._resume_auto_listen()

    def shutdown(self):
        self.turn_id += 1
        self._stop_job()
        if self.capture is not None:
            self._stop_capture(transcribe=False)
        if self.voice_task is not None and self.voice_task.isRunning():
            self.voice_task.cancel()
        if hasattr(self, "player"):
            self.speaking = False
            self.player.stop()
            self.player.setSource(QUrl())
        self._delete_temp_audio("_audio_temp")
        self._delete_temp_audio("_reply_audio")

    def _close_when_idle(self):
        if (self.closing and self.job is None and self.image_task is None and self.voice_task is None
                and self.capture is None and self.frame is not None and isValid(self.frame)):
            QTimer.singleShot(0, self.frame.request_close)

    def closeEvent(self, event):
        if (self.job is not None or self.image_task is not None or self.voice_task is not None
                or self.capture is not None):
            self.closing = True
            event.ignore()
            if self.capture is not None:
                self._stop_capture(transcribe=False)
            if self.job is not None or self.image_task is not None:
                self.stop()
            if self.voice_task is not None:
                self.voice_task.cancel()
            self._close_when_idle()
            return
        self.shutdown()
        event.accept()
