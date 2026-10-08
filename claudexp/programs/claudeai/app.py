"""ClaudeAI: a Claude Desktop-style chat app for the local model.

Collapsible sidebar (New chat, search, Starred and Recents with a menu per chat), streaming
Markdown replies with Copy / Retry, Extended thinking, a model picker, and Settings.
"""
import html
import math
import time

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QTimer, QUrl
from PySide6.QtGui import (QColor, QFont, QIcon, QImage, QKeySequence, QPainter, QPainterPath, QPen, QPixmap,
                           QShortcut, QTextDocument)
from PySide6.QtWidgets import (QApplication, QComboBox, QDoubleSpinBox, QFrame, QGridLayout, QHBoxLayout, QLabel,
                               QLineEdit, QListWidget, QListWidgetItem, QMenu, QPlainTextEdit, QPushButton,
                               QSizePolicy, QTextBrowser, QToolButton, QVBoxLayout, QWidget)
from shiboken6 import isValid

from ... import broker, clock
from ...user import user_name
from .store import DEFAULT_INSTRUCTIONS, Chats, Settings

BG, SIDEBAR, BORDER = "#FAF9F5", "#F0EEE6", "#E3DFD3"
TEXT, MUTED, ACCENT, USER_BUBBLE = "#3D3929", "#8B877C", "#D97757", "#EDEAE0"
UI_FONT, SERIF = "Segoe UI", "Georgia"

STYLE = f"""
QWidget#claudeai {{ background: {BG}; }}
QWidget#sidebar {{ background: {SIDEBAR}; border-right: 1px solid {BORDER}; }}
QLabel {{ color: {TEXT}; font-family: '{UI_FONT}'; }}
QLabel#brand {{ font-family: '{SERIF}'; font-size: 17px; font-weight: bold; }}
QLabel#section {{ color: {MUTED}; font-size: 11px; font-weight: bold; padding: 8px 6px 2px 6px; }}
QLabel#chattitle {{ font-size: 13px; font-weight: 600; padding: 4px 8px; border-radius: 6px; }}
QLabel#chattitle:hover {{ background: #EFECE3; }}
QPushButton#newchat {{ color: {TEXT}; font-family: '{UI_FONT}'; font-size: 13px; font-weight: 600; text-align: left;
                       padding: 7px 8px; border: none; border-radius: 8px; background: transparent; }}
QPushButton#newchat:hover {{ background: #E6E2D7; }}
QToolButton {{ border: none; border-radius: 6px; padding: 4px; color: {TEXT}; font-family: '{UI_FONT}'; }}
QToolButton:hover {{ background: #E6E2D7; }}
QToolButton:checked {{ background: #F3DED4; color: #B85A3B; }}
QLineEdit#search {{ background: #F7F5EF; border: 1px solid {BORDER}; border-radius: 8px; padding: 5px 8px;
                    font-family: '{UI_FONT}'; font-size: 12px; color: {TEXT}; }}
QListWidget#chats {{ background: transparent; border: none; outline: none; font-family: '{UI_FONT}'; font-size: 12px; }}
QListWidget#chats::item {{ border-radius: 7px; padding: 0px; color: {TEXT}; }}
QListWidget#chats::item:hover {{ background: #E8E4D9; }}
QListWidget#chats::item:selected {{ background: #E3DED1; color: {TEXT}; }}
QFrame#composer {{ background: white; border: 1px solid #DAD5C8; border-radius: 16px; }}
QPlainTextEdit#prompt {{ background: transparent; border: none; font-family: '{UI_FONT}'; font-size: 14px; color: {TEXT}; }}
QComboBox#model {{ border: none; background: transparent; color: {MUTED}; font-family: '{UI_FONT}'; font-size: 12px; padding: 2px 6px; }}
QComboBox#model:hover {{ background: #F1EEE6; border-radius: 6px; }}
QTextBrowser#conversation {{ background: {BG}; border: none; }}
QMenu {{ background: white; border: 1px solid {BORDER}; border-radius: 8px; padding: 4px;
         font-family: '{UI_FONT}'; font-size: 12px; }}
QMenu::item {{ padding: 6px 22px 6px 12px; border-radius: 5px; color: {TEXT}; }}
QMenu::item:selected {{ background: #F0EDE4; color: {TEXT}; }}
"""


def spark_pixmap(size=32, color=ACCENT):
    """An orange spark/asterisk mark."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(color))
    c = size / 2
    rays = 11
    for i in range(rays):
        a = i * 2 * math.pi / rays + (0.12 if i % 2 else 0)
        length = c * (0.95 if i % 3 else 0.78)
        w = size * 0.07
        path = QPainterPath()
        tip = QPointF(c + math.cos(a) * length, c + math.sin(a) * length)
        side = QPointF(math.cos(a + math.pi / 2) * w, math.sin(a + math.pi / 2) * w)
        base = QPointF(c, c)
        path.moveTo(base + side)
        path.lineTo(tip)
        path.lineTo(base - side)
        path.closeSubpath()
        p.drawPath(path)
    p.drawEllipse(QPointF(c, c), size * 0.11, size * 0.11)
    p.end()
    return pm


def app_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#F4E9DF"))
    p.drawRoundedRect(QRectF(1, 1, 30, 30), 7, 7)
    p.drawPixmap(4, 4, spark_pixmap(24))
    p.end()
    return QIcon(pm)


def _sidebar_icon(collapsed):
    pm = QPixmap(18, 18)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor(TEXT), 1.4))
    p.setBrush(Qt.NoBrush)
    p.drawRoundedRect(QRectF(1.5, 2.5, 15, 13), 2.5, 2.5)
    p.drawLine(QPointF(6.5, 2.5), QPointF(6.5, 15.5))
    p.end()
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
    """A chat in the sidebar: its title, plus a ⋯ button that shows on hover."""

    def __init__(self, app, chat):
        super().__init__()
        self.app, self.chat = app, chat
        row = QHBoxLayout(self)
        row.setContentsMargins(8, 3, 2, 3)
        self.label = QLabel()
        self.label.setStyleSheet("font-size: 12px; background: transparent;")
        row.addWidget(self.label, 1)
        self.more = QToolButton()
        self.more.setText("⋯")
        self.more.setFixedSize(24, 22)
        self.more.setVisible(False)
        self.more.clicked.connect(lambda: app.chat_menu(chat, self.more.mapToGlobal(self.more.rect().bottomLeft())))
        row.addWidget(self.more)
        self._set_text()

    def _set_text(self):
        fm = self.label.fontMetrics()
        self.label.setText(fm.elidedText(self.chat["title"], Qt.ElideRight, 190))

    def enterEvent(self, event):
        self.more.setVisible(True)

    def leaveEvent(self, event):
        self.more.setVisible(False)


class ClaudeAI(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.settings = Settings()
        self.chats = Chats()
        self.current = None
        self.job = None
        self.expanded_thoughts = set()
        self.setObjectName("claudeai")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(STYLE)
        self.models = self._list_models()
        if not self.settings["model"] or self.settings["model"] not in self.models:
            self.settings.values["model"] = self.models[0] if self.models else ""

        # ---- sidebar ----
        self.sidebar = QWidget()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setAttribute(Qt.WA_StyledBackground, True)
        sv = QVBoxLayout(self.sidebar)
        sv.setContentsMargins(8, 8, 8, 8)
        sv.setSpacing(4)
        top = QHBoxLayout()
        self.toggle = QToolButton()
        self.toggle.setIcon(_sidebar_icon(False))
        self.toggle.setToolTip("Toggle sidebar")
        self.toggle.clicked.connect(self.toggle_sidebar)
        top.addWidget(self.toggle)
        self.brand = QLabel("ClaudeAI")
        self.brand.setObjectName("brand")
        top.addWidget(self.brand, 1)
        sv.addLayout(top)
        self.new_btn = QPushButton("  New chat")
        self.new_btn.setObjectName("newchat")
        plus = QPixmap(20, 20)
        plus.fill(Qt.transparent)
        pp = QPainter(plus)
        pp.setRenderHint(QPainter.Antialiasing)
        pp.setPen(Qt.NoPen)
        pp.setBrush(QColor(ACCENT))
        pp.drawEllipse(QRectF(0, 0, 20, 20))
        pp.setPen(QPen(QColor("white"), 2))
        pp.drawLine(10, 5, 10, 15)
        pp.drawLine(5, 10, 15, 10)
        pp.end()
        self.new_btn.setIcon(QIcon(plus))
        self.new_btn.clicked.connect(self.new_chat)
        sv.addWidget(self.new_btn)
        self.search = QLineEdit()
        self.search.setObjectName("search")
        self.search.setPlaceholderText("Search your chats...")
        self.search.textChanged.connect(lambda _t: self.refresh_sidebar())
        sv.addWidget(self.search)
        self.list = QListWidget()
        self.list.setObjectName("chats")
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list.itemClicked.connect(self._list_clicked)
        self.list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self._list_menu)
        sv.addWidget(self.list, 1)
        bottom = QHBoxLayout()
        avatar = QLabel(user_name()[:1].upper())
        avatar.setFixedSize(28, 28)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet(f"background: #3D3929; color: #FAF9F5; border-radius: 14px; font-weight: bold;")
        self.avatar = avatar
        bottom.addWidget(avatar)
        self.user_label = QLabel(user_name())
        self.user_label.setStyleSheet("font-size: 12px; font-weight: 600;")
        bottom.addWidget(self.user_label, 1)
        self.gear = QToolButton()
        self.gear.setText("⚙")
        self.gear.setStyleSheet("font-size: 18px; padding: 0px 4px;")
        self.gear.setToolTip("Settings")
        self.gear.clicked.connect(self.open_settings)
        bottom.addWidget(self.gear)
        sv.addLayout(bottom)

        # ---- main column ----
        main = QWidget()
        mv = QVBoxLayout(main)
        mv.setContentsMargins(0, 0, 0, 12)
        mv.setSpacing(6)
        header = QHBoxLayout()
        header.setContentsMargins(12, 8, 12, 0)
        self.open_sidebar = QToolButton()
        self.open_sidebar.setIcon(_sidebar_icon(True))
        self.open_sidebar.setToolTip("Open sidebar")
        self.open_sidebar.clicked.connect(self.toggle_sidebar)
        header.addWidget(self.open_sidebar)
        self.title = QLabel("")
        self.title.setObjectName("chattitle")
        self.title.setCursor(Qt.PointingHandCursor)
        self.title.mousePressEvent = lambda _e: self.current and self.chat_menu(
            self.current, self.title.mapToGlobal(self.title.rect().bottomLeft()))
        header.addWidget(self.title)
        header.addStretch()
        self.star_btn = QToolButton()
        self.star_btn.setToolTip("Star chat")
        self.star_btn.clicked.connect(lambda: self.current and self.toggle_pin(self.current))
        header.addWidget(self.star_btn)
        mv.addLayout(header)

        self.view = QTextBrowser()
        self.view.setObjectName("conversation")
        self.view.setOpenLinks(False)
        self.view.anchorClicked.connect(self._link)
        self.view.document().addResource(QTextDocument.ImageResource, QUrl("spark:big"),
                                         spark_pixmap(40).toImage())
        self.view.document().addResource(QTextDocument.ImageResource, QUrl("spark:small"),
                                         spark_pixmap(20).toImage())
        mv.addWidget(self.view, 1)

        self.composer = QFrame()
        self.composer.setObjectName("composer")
        cv = QVBoxLayout(self.composer)
        cv.setContentsMargins(14, 10, 10, 8)
        self.prompt = QPlainTextEdit()
        self.prompt.setObjectName("prompt")
        self.prompt.setPlaceholderText("How can I help you today?")
        self.prompt.setFixedHeight(48)
        self.prompt.textChanged.connect(self._grow)
        self.prompt.installEventFilter(self)
        cv.addWidget(self.prompt)
        crow = QHBoxLayout()
        self.think_btn = QToolButton()
        self.think_btn.setText("✻ Extended thinking")
        self.think_btn.setCheckable(True)
        self.think_btn.setChecked(bool(self.settings["think"]))
        self.think_btn.toggled.connect(lambda on: self.settings.set("think", on))
        self.think_btn.setStyleSheet("font-size: 12px;")
        crow.addWidget(self.think_btn)
        crow.addStretch()
        self.model_box = QComboBox()
        self.model_box.setObjectName("model")
        self.model_box.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.model_box.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.model_box.addItems(self.models or ["(no models found)"])
        if self.settings["model"]:
            self.model_box.setCurrentText(self.settings["model"])
        self.model_box.currentTextChanged.connect(lambda m: self.settings.set("model", m))
        crow.addWidget(self.model_box)
        self.send_btn = QToolButton()
        self.send_btn.setFixedSize(32, 32)
        self.send_btn.clicked.connect(self._send_or_stop)
        crow.addWidget(self.send_btn)
        cv.addLayout(crow)
        wrap = QHBoxLayout()
        wrap.setContentsMargins(40, 0, 40, 0)
        wrap.addWidget(self.composer)
        mv.addLayout(wrap)
        note = QLabel("ClaudeAI runs on your local model and can make mistakes. Please double-check responses.")
        note.setAlignment(Qt.AlignCenter)
        note.setStyleSheet(f"color: {MUTED}; font-size: 11px;")
        mv.addWidget(note)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self.sidebar)
        root.addWidget(main, 1)

        QShortcut(QKeySequence("Ctrl+Shift+O"), self, self.new_chat)
        QShortcut(QKeySequence("Ctrl+B"), self, self.toggle_sidebar)
        self.render_timer = QTimer(self)
        self.render_timer.setSingleShot(True)
        self.render_timer.timeout.connect(self.render)
        self._apply_sidebar(self.settings["sidebar"])
        self._update_send()
        self.refresh_sidebar()
        self.render()

    # ---- models -----------------------------------------------------------------------------
    def _list_models(self):
        try:
            import ollama
            models = []
            for m in ollama.list().models:
                name = m.model
                bare = name.split(":")[-1]
                if "embed" in name or name in models or (len(bare) >= 32 and all(c in "0123456789abcdef" for c in bare)):
                    continue   # skip embedding models, duplicates and raw hash-named imports
                models.append(name)
        except Exception:
            models = []
        try:
            from claudeaim.storage import Settings as AimSettings
            default = AimSettings()["default_model"]
            if default in models:
                models.remove(default)
                models.insert(0, default)
            elif not models:
                models = [default]
        except Exception:
            pass
        return models

    # ---- sidebar -------------------------------------------------------------------------------
    def toggle_sidebar(self):
        self._apply_sidebar(not self.sidebar.isVisible())

    def _apply_sidebar(self, shown):
        self.sidebar.setVisible(shown)
        self.sidebar.setFixedWidth(250)
        self.open_sidebar.setVisible(not shown)
        self.settings.set("sidebar", shown)

    def refresh_sidebar(self):
        self.list.clear()
        pinned, recents = self.chats.listed(self.search.text())
        for title, group in (("Starred", pinned), ("Recents", recents)):
            if not group:
                continue
            head = QListWidgetItem()
            head.setFlags(Qt.NoItemFlags)
            self.list.addItem(head)
            label = QLabel(title)
            label.setObjectName("section")
            head.setSizeHint(QSize(200, 26))
            self.list.setItemWidget(head, label)
            for chat in group:
                item = QListWidgetItem()
                item.setData(Qt.UserRole, chat["id"])
                item.setSizeHint(QSize(200, 30))
                self.list.addItem(item)
                self.list.setItemWidget(item, ChatRow(self, chat))
                if self.current is not None and chat["id"] == self.current["id"]:
                    item.setSelected(True)
        if not pinned and not recents:
            empty = QListWidgetItem("No chats yet" if not self.search.text() else "No matching chats")
            empty.setFlags(Qt.NoItemFlags)
            empty.setForeground(QColor(MUTED))
            self.list.addItem(empty)

    def _list_clicked(self, item):
        chat = self.chats.get(item.data(Qt.UserRole)) if item.data(Qt.UserRole) else None
        if chat is not None:
            self.open_chat(chat)

    def _list_menu(self, pos):
        item = self.list.itemAt(pos)
        chat = self.chats.get(item.data(Qt.UserRole)) if item and item.data(Qt.UserRole) else None
        if chat is not None:
            self.chat_menu(chat, self.list.viewport().mapToGlobal(pos))

    def chat_menu(self, chat, pos):
        menu = QMenu(self)
        menu.addAction("☆  Unstar" if chat["pinned"] else "★  Star", lambda: self.toggle_pin(chat))
        menu.addAction("✎  Rename", lambda: self.rename(chat))
        menu.addSeparator()
        menu.addAction("🗑  Delete", lambda: self.delete(chat))
        menu.exec(pos)

    def toggle_pin(self, chat):
        chat["pinned"] = not chat["pinned"]
        self.chats.save()
        self.refresh_sidebar()
        self._update_header()

    def rename(self, chat):
        ask_text(self.desktop, "Rename chat", "Chat name:", chat["title"],
                 lambda text: self._renamed(chat, text))

    def _renamed(self, chat, text):
        if text.strip():
            chat["title"] = text.strip()
            chat["titled"] = True
            self.chats.save()
            self.refresh_sidebar()
            self._update_header()

    def delete(self, chat):
        from ...explorer.dialogs import msgbox

        def answer(button):
            if button == "Delete":
                if self.current is chat:
                    self.stop()
                    self.current = None
                self.chats.delete(chat["id"])
                self.refresh_sidebar()
                self.render()

        msgbox(self.desktop, "Delete chat", f"Are you sure you want to delete \"{chat['title']}\"?\n\n"
                                            "This can't be undone.", "warning", ("Delete", "Cancel"), answer)

    # ---- chats -------------------------------------------------------------------------------------
    def new_chat(self):
        self.stop()
        self.current = None
        self.expanded_thoughts.clear()
        self.refresh_sidebar()
        self.render()
        self.prompt.setFocus()

    def open_chat(self, chat):
        if self.current is chat:
            return
        self.stop()
        self.current = chat
        self.expanded_thoughts.clear()
        if chat.get("model") in self.models:
            self.model_box.setCurrentText(chat["model"])
        self.refresh_sidebar()
        self.render()
        self.prompt.setFocus()

    def _update_header(self):
        chat = self.current
        self.title.setText(f"{chat['title']}  ⌄" if chat and chat["messages"] else "")
        self.star_btn.setVisible(bool(chat and chat["messages"]))
        if chat:
            self.star_btn.setText("★" if chat["pinned"] else "☆")
            self.star_btn.setStyleSheet(f"color: {ACCENT if chat['pinned'] else MUTED}; font-size: 16px;")
        if self.frame is not None:
            self.frame.set_title(f"{chat['title']} - ClaudeAI" if chat and chat["messages"] else "ClaudeAI")

    # ---- rendering ---------------------------------------------------------------------------------
    def schedule_render(self):
        if not self.render_timer.isActive():
            self.render_timer.start(120)

    def render(self):
        self._update_header()
        chat = self.current
        if chat is None or not chat["messages"]:
            self.prompt.setPlaceholderText("How can I help you today?")
            hour = clock.now().hour
            part = "morning" if 5 <= hour < 12 else "afternoon" if hour < 17 else "evening"
            self.view.setHtml(f"""<table width="100%" height="100%"><tr><td align="center" valign="middle">
                <br><br><br><br><br><img src="spark:big" width="40" height="40"><br><br>
                <span style="font-family:'{SERIF}'; font-size:28px; color:{TEXT};">Good {part}, {html.escape(user_name())}</span>
                </td></tr></table>""")
            return
        self.prompt.setPlaceholderText("Reply to ClaudeAI...")
        bar = self.view.verticalScrollBar()
        at_bottom = bar.value() >= bar.maximum() - 30
        parts = []
        last_assistant = max((i for i, m in enumerate(chat["messages"]) if m["role"] == "assistant"), default=-1)
        for i, m in enumerate(chat["messages"]):
            if m["role"] == "user":
                text = html.escape(m["content"]).replace("\n", "<br>")
                parts.append(f"""<table width="100%" cellspacing="0" cellpadding="0" style="margin-top:14px;"><tr>
                    <td width="34" valign="top"><table cellpadding="5" bgcolor="#3D3929"><tr><td>
                    <span style="color:#FAF9F5; font-weight:bold; font-family:'{UI_FONT}';">{html.escape(user_name()[:1].upper())}</span>
                    </td></tr></table></td>
                    <td><table width="100%" cellpadding="10" bgcolor="{USER_BUBBLE}"><tr><td>
                    <span style="font-family:'{UI_FONT}'; font-size:14px; color:{TEXT};">{text}</span>
                    </td></tr></table></td></tr></table>""")
            else:
                block = ""
                if m.get("thinking"):
                    open_ = i in self.expanded_thoughts
                    block += (f'<p style="margin-top:12px;"><a href="think:{i}" style="color:{MUTED}; text-decoration:none;'
                              f' font-family:\'{UI_FONT}\'; font-size:12px;">{"▾" if open_ else "▸"} Thought process</a></p>')
                    if open_:
                        thought = html.escape(m["thinking"]).replace("\n", "<br>")
                        block += (f'<table width="100%" cellpadding="8" style="border-left: 2px solid {BORDER};"><tr><td>'
                                  f'<span style="color:{MUTED}; font-family:\'{UI_FONT}\'; font-size:12px;">{thought}</span>'
                                  "</td></tr></table>")
                content = m["content"]
                if m.get("streaming"):
                    if not content:
                        status = "Thinking..." if m.get("thinking") else "..."
                        body = f'<img src="spark:small" width="20" height="20"> <span style="color:{MUTED};">{status}</span>'
                    else:
                        body = _markdown_html(content + " ▍")
                else:
                    body = _markdown_html(content) if content else f'<i style="color:{MUTED};">(no response)</i>'
                parts.append(f"""<table width="100%" cellpadding="0" style="margin-top:10px;"><tr><td>{block}
                    <div style="font-family:'{SERIF}'; font-size:15px; color:{TEXT};">{body}</div></td></tr></table>""")
                if not m.get("streaming"):
                    actions = f'<a href="copy:{i}" style="color:{MUTED}; text-decoration:none;">⧉ Copy</a>'
                    if i == last_assistant:
                        actions += f' &nbsp; <a href="retry:{i}" style="color:{MUTED}; text-decoration:none;">↻ Retry</a>'
                    if m.get("stopped"):
                        actions = f'<span style="color:{MUTED};">Stopped</span> &nbsp; ' + actions
                    parts.append(f'<p style="font-family:\'{UI_FONT}\'; font-size:12px;">{actions}</p>')
        self.view.setHtml(f"""<table width="100%"><tr><td width="6%"></td><td>{''.join(parts)}<br></td>
            <td width="6%"></td></tr></table>""")
        if at_bottom or (self.job is not None):
            bar.setValue(bar.maximum())

    def _link(self, url):
        kind, _, index = url.toString().partition(":")
        if self.current is None or not index.isdigit():
            return
        i = int(index)
        msgs = self.current["messages"]
        if i >= len(msgs):
            return
        if kind == "copy":
            QApplication.clipboard().setText(msgs[i]["content"])
        elif kind == "retry":
            self.retry()
        elif kind == "think":
            self.expanded_thoughts ^= {i}
            self.render()

    # ---- sending --------------------------------------------------------------------------------------
    def eventFilter(self, obj, event):
        if obj is self.prompt and event.type() == event.Type.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter) and not event.modifiers() & Qt.ShiftModifier:
                self._send_or_stop(from_enter=True)
                return True
        return False

    def _grow(self):
        lines = self.prompt.document().size().height()
        fm_h = self.prompt.fontMetrics().lineSpacing()
        self.prompt.setFixedHeight(int(min(180, max(48, lines * fm_h + 14))))
        self._update_send()

    def _update_send(self):
        busy = self.job is not None
        pm = QPixmap(32, 32)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        ready = busy or bool(self.prompt.toPlainText().strip())
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(ACCENT if ready else "#E8C5B6"))
        p.drawRoundedRect(QRectF(2, 2, 28, 28), 9, 9)
        if busy:
            p.setBrush(QColor("white"))
            p.drawRoundedRect(QRectF(11, 11, 10, 10), 2, 2)
        else:
            p.setPen(QPen(QColor("white"), 2.2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            p.drawLine(QPointF(16, 23), QPointF(16, 9))
            p.drawLine(QPointF(10.5, 14.5), QPointF(16, 9))
            p.drawLine(QPointF(21.5, 14.5), QPointF(16, 9))
        p.end()
        self.send_btn.setIcon(QIcon(pm))
        self.send_btn.setIconSize(QSize(32, 32))
        self.send_btn.setToolTip("Stop response" if busy else "Send message")

    def _send_or_stop(self, from_enter=False):
        if self.job is not None:
            if not from_enter:
                self.stop()
            return
        text = self.prompt.toPlainText().strip()
        if not text:
            return
        self.prompt.clear()
        if self.current is None:
            self.current = self.chats.new(self.model_box.currentText())
        self.current["messages"].append({"role": "user", "content": text})
        self.chats.touch(self.current)
        self.refresh_sidebar()
        self._generate()

    def retry(self):
        chat = self.current
        if chat is None or self.job is not None:
            return
        while chat["messages"] and chat["messages"][-1]["role"] == "assistant":
            chat["messages"].pop()
        if chat["messages"]:
            self._generate()

    def _generate(self):
        chat = self.current
        model = self.model_box.currentText()
        chat["model"] = model
        history = [{"role": m["role"], "content": m["content"]} for m in chat["messages"]]
        budget = int(self._ctx() * 3)                  # rough characters that fit in the context
        kept, used = [], len(self.settings["instructions"])
        for m in reversed(history):
            used += len(m["content"])
            if used > budget and kept:
                break
            kept.insert(0, m)
        messages = [{"role": "system", "content": self.settings["instructions"] or DEFAULT_INSTRUCTIONS}] + kept
        reply = {"role": "assistant", "content": "", "streaming": True}
        chat["messages"].append(reply)
        think = self.think_btn.isChecked()
        self.render()

        def on_chunk(text):
            reply["content"] = text
            self.schedule_render()

        def on_thinking(text):
            reply["thinking"] = text
            self.schedule_render()

        def on_done(text, err):
            if self.job is not job:
                return
            self.job = None
            reply.pop("streaming", None)
            if err == "stopped":
                reply["stopped"] = True
            elif err:
                reply["content"] = f"*Something went wrong talking to the model: {err}*"
            else:
                reply["content"] = text
            self.chats.touch(chat)
            self._update_send()
            self.render()
            self.refresh_sidebar()
            if not chat.get("titled") and not err:
                self._name_chat(chat)

        job = broker.get().stream(model, messages, {"num_ctx": self._ctx(),
                                                    "temperature": float(self.settings["temperature"])},
                                  on_chunk, on_done, broker.FOREGROUND, think=think, on_thinking=on_thinking)
        self.job = job
        self._update_send()

    def _ctx(self):
        try:
            from claudeaim.storage import Settings as AimSettings
            return int(AimSettings()["context_size"])
        except Exception:
            return 8192

    def stop(self):
        if self.job is not None:
            self.job.stop()

    def _name_chat(self, chat):
        """Give a new chat a short title in the background."""
        chat["titled"] = True
        first = chat["messages"][0]["content"][:500]
        prompt = (f"Write a short title (at most 6 words) for a chat that begins with this message:\n\n{first}\n\n"
                  "Reply with only the title, no quotes or punctuation at the end.")

        def done(text, err):
            title = (text or "").strip().strip('"').splitlines()[0].strip() if text and not err else ""
            if title:
                chat["title"] = title[:60]
                self.chats.save()
                if isValid(self):
                    self.refresh_sidebar()
                    self._update_header()

        broker.get().chat(chat["model"], [{"role": "user", "content": prompt}],
                          {"num_ctx": self._ctx(), "temperature": 0.3}, done, broker.REPLY, think=False)

    # ---- settings ---------------------------------------------------------------------------------------
    def open_settings(self):
        from ...network import DialogBody, _fixed_window
        body = DialogBody()
        grid = QGridLayout(body)
        grid.setContentsMargins(14, 12, 14, 12)
        grid.addWidget(QLabel("<b>Settings</b>"), 0, 0, 1, 2)
        grid.addWidget(QLabel("Default model:"), 1, 0)
        model = QComboBox()
        model.addItems(self.models or [self.settings["model"]])
        model.setCurrentText(self.settings["model"])
        grid.addWidget(model, 1, 1)
        grid.addWidget(QLabel("Temperature:"), 2, 0)
        temp = QDoubleSpinBox()
        temp.setRange(0.0, 2.0)
        temp.setSingleStep(0.1)
        temp.setValue(float(self.settings["temperature"]))
        grid.addWidget(temp, 2, 1)
        grid.addWidget(QLabel("Custom instructions (how ClaudeAI should respond):"), 3, 0, 1, 2)
        instr = QPlainTextEdit(self.settings["instructions"])
        instr.setFixedHeight(110)
        grid.addWidget(instr, 4, 0, 1, 2)
        reset = QPushButton("Reset instructions")
        reset.clicked.connect(lambda: instr.setPlainText(DEFAULT_INSTRUCTIONS))
        grid.addWidget(reset, 5, 0)
        row = QHBoxLayout()
        row.addStretch()
        save, cancel = QPushButton("Save"), QPushButton("Cancel")
        for b in (save, cancel):
            b.setFixedSize(75, 23)
            row.addWidget(b)
        grid.addLayout(row, 6, 0, 1, 2)
        body.setFixedWidth(420)
        holder = {}

        def close():
            if holder.get("win") is not None:
                self.desktop.close_window(holder.pop("win"))

        def apply():
            self.settings.set("model", model.currentText())
            self.settings.set("temperature", temp.value())
            self.settings.set("instructions", instr.toPlainText().strip() or DEFAULT_INSTRUCTIONS)
            self.model_box.setCurrentText(model.currentText())
            close()

        save.clicked.connect(apply)
        cancel.clicked.connect(close)
        holder["win"] = _fixed_window(self.desktop, "ClaudeAI Settings", body, close)
        holder["win"].icon = app_icon()
        self.desktop.open_window(holder["win"])

    def shutdown(self):
        self.stop()

    def closeEvent(self, event):
        self.shutdown()
        event.accept()


def ask_text(desktop, title, label, default, on_ok):
    """A small 'type a name' dialog."""
    from ...network import DialogBody, _fixed_window
    body = DialogBody()
    v = QVBoxLayout(body)
    v.setContentsMargins(14, 12, 14, 12)
    v.addWidget(QLabel(label))
    edit = QLineEdit(default)
    v.addWidget(edit)
    row = QHBoxLayout()
    row.addStretch()
    ok, cancel = QPushButton("OK"), QPushButton("Cancel")
    for b in (ok, cancel):
        b.setFixedSize(75, 23)
        row.addWidget(b)
    v.addLayout(row)
    body.setFixedWidth(320)
    holder = {}

    def close():
        if holder.get("win") is not None:
            desktop.close_window(holder.pop("win"))

    def accept():
        text = edit.text()
        close()
        on_ok(text)

    ok.clicked.connect(accept)
    edit.returnPressed.connect(accept)
    cancel.clicked.connect(close)
    holder["win"] = _fixed_window(desktop, title, body, close)
    desktop.open_window(holder["win"])
    edit.setFocus()
    edit.selectAll()
