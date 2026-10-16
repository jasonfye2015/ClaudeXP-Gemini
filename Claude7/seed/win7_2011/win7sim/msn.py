"""Authentic supplied MSN artwork wrapped around the existing chat engine."""

from html import escape
from pathlib import Path
import re

from PySide6.QtCore import Qt, QSize, Signal, QTimer
from PySide6.QtGui import QIcon, QPixmap, QPainter, QFont
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QMenuBar, QMenu, QTreeWidget, QTreeWidgetItem,
    QHBoxLayout, QVBoxLayout, QDialog, QFormLayout, QInputDialog, QMessageBox,
    QTextBrowser, QColorDialog, QFontDialog, QFileDialog, QLineEdit,
)

from .apps import MessengerApp
from .contacts import CONTACTS, MSN_CONTACTS, MSN_ASSETS, SUPPLIED_PROFILES
from .clock import format_locked_date, format_locked_time
from .msn_presence import MSNPresence
from .msn_history import MSNHistoryParticipant
from .msn_widgets import TemplateCanvas, Avatar, MessageComposer, player_avatar, stash_legacy_ui, show_gallery


STATUS_FILES = {
    "Online": "Online", "Away": "Away", "Do not disturb": "DND",
    "Blocked": "Blocked", "Offline": "Away",  # Specifically requested by the supplied README.
}


def status_icon(state):
    return QIcon(str(MSN_ASSETS / f"MSN_Contact_List_{STATUS_FILES[state]}_Icon_Inddicator.jpg"))


class MSNContactListApp(MSNHistoryParticipant, MessengerApp):
    conversationRequested = Signal(object)
    browserRequested = Signal(str)
    closeMessengerRequested = Signal()
    trayVisibilityRequested = Signal(bool)

    def __init__(self, account, service, parent=None, ai_service=None, presence=None, history_session=None):
        super().__init__(account, service, parent, ai_service)
        root = stash_legacy_ui(self)
        self.presence = presence or MSNPresence(self)
        self._owns_presence = presence is None
        self._show_background = True
        self._show_legacy = False
        self._unread_mail = 0
        self._mail_lit = False
        self._advertisements = [(MSN_ASSETS / "MSN_Contact_List_AD_Default.jpg", None)]
        self._ad_index = 0
        self.setMinimumSize(290, 480)
        self.menus = QMenuBar()
        root.addWidget(self.menus)
        self._build_menus()
        # Reuse the existing search and readability controls.
        search_row = QHBoxLayout()
        search_row.addWidget(self.search_input, 1)
        search_row.addWidget(self.contact_text_size)
        root.addLayout(search_row)
        self.search_input.show()
        self.contact_text_size.show()
        self.search_input.textChanged.connect(self.rebuild_tree)
        self.contact_text_size.currentIndexChanged.connect(self._resize_roster)
        self.canvas = TemplateCanvas("MSN_Contact_List_Template.jpg")
        root.addWidget(self.canvas, 1)
        self.user_icon = Avatar(player_avatar(account))
        self.user_name = QLabel(account.resolved_online_name)
        self.user_name.setStyleSheet("font-weight: bold; font-size: 12pt; background: transparent;")
        self.user_status = QPushButton()
        self.user_status.setStyleSheet("text-align: left; border: 0; background: transparent;")
        self.user_status.clicked.connect(self._choose_status)
        self.activity = QLabel("Welcome to MSN Messenger")
        self.activity.setWordWrap(True)
        self.mail_button = QPushButton("Inbox")
        self.mail_button.setStyleSheet("border: 0; background: transparent; text-align: left;")
        self.mail_button.clicked.connect(self._open_mail)
        self.mail_icon = QPushButton()
        self.mail_icon.setAccessibleName("Open inbox")
        self.mail_icon.setStyleSheet("border: 0; background: transparent;")
        self.mail_icon.clicked.connect(self._open_mail)
        self.mail_icon.setToolTip("Open inbox")
        self._mail_indicator = QIcon(str(MSN_ASSETS / "MSN_Contact_List_Mail_Indicator.jpg"))
        self.mail_icon.setIcon(self._mail_indicator)
        self.mail_icon.setIconSize(QSize(29, 27))
        self.add_button = QPushButton()
        self.add_button.setAccessibleName("Add a contact")
        self.add_button.setToolTip("Add a Contact")
        self.add_button.setStyleSheet("border: 0; background: transparent;")
        self.add_button.clicked.connect(self._add_contact_dialog)
        self.tree = QTreeWidget()
        self.tree.setObjectName("msnContactTree")
        self.tree.setHeaderHidden(True)
        self.tree.setRootIsDecorated(True)
        self.tree.setIndentation(12)
        self.tree.setStyleSheet("QTreeWidget {border: 0; background: white;} QTreeWidget::item {padding: 2px;}")
        self.tree.itemDoubleClicked.connect(self._open_item)
        self.tree.itemClicked.connect(self._select_item)
        self.tree.currentItemChanged.connect(
            lambda current, _previous: self._select_item(current) if current else None
        )
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._context_menu)
        self.ad_button = QPushButton()
        self.ad_button.setObjectName("msnAdvertisement")
        self.ad_button.setStyleSheet("border: 0; background: white;")
        self.ad_button.clicked.connect(self._click_ad)
        for widget, rect in (
            (self.user_icon, (28, 80, 140, 137)),
            (self.user_name, (203, 85, 612, 57)),
            (self.user_status, (203, 147, 375, 45)),
            (self.mail_icon, (582, 150, 30, 35)),
            (self.mail_button, (615, 147, 193, 42)),
            (self.activity, (120, 292, 708, 76)),
            (self.add_button, (112, 382, 440, 49)),
            (self.tree, (113, 444, 717, 832)),
            (self.ad_button, (121, 1306, 706, 178)),
        ):
            self.canvas.place(widget, *rect)
        self.provider_status.setMaximumHeight(50)
        root.addWidget(self.provider_status)
        self.provider_status.show()
        self.preference_status = QLabel()
        self.preference_status.setWordWrap(True)
        root.addWidget(self.preference_status)
        self.presence.changed.connect(self._presence_changed)
        self.presence.userChanged.connect(self._update_user)
        self._ad_timer = QTimer(self)
        self._ad_timer.timeout.connect(self._rotate_ad)
        self._ad_timer.start(7 * 60_000)
        self._mail_timer = QTimer(self)
        self._mail_timer.timeout.connect(self._flash_mail)
        self._mail_timer.start(700)
        self.rebuild_tree()
        self._update_user()
        self._rotate_ad(advance=False)
        if history_session:
            history_session.attach(self)

    def sizeHint(self):
        return QSize(350, 650)

    def _build_menus(self):
        file = self.menus.addMenu("&File")
        file.addAction("My status…", self._choose_status)
        file.addAction("Sign out", lambda: self.presence.set_user_status("Offline"))
        file.addAction("Sign in", lambda: self.presence.set_user_status("Online"))
        file.addSeparator()
        self.close_action = file.addAction("Close MSN Messenger")
        self.close_action.triggered.connect(
            lambda _checked=False: self.closeMessengerRequested.emit()
        )
        contacts = self.menus.addMenu("&Contacts")
        contacts.addAction("Add a contact…", self._add_contact_dialog)
        contacts.addAction("Find a contact", lambda: self.search_input.setFocus())
        background = contacts.addAction("Show background community")
        background.setCheckable(True)
        background.setChecked(True)
        background.toggled.connect(self._toggle_background)
        legacy = contacts.addAction("Show previous starter contacts")
        legacy.setCheckable(True)
        legacy.toggled.connect(self._toggle_legacy)
        actions = self.menus.addMenu("&Actions")
        actions.addAction("Send an instant message", self._open_selected)
        actions.addAction("Block / Unblock selected contact", self._block_selected)
        actions.addAction("View selected contact's pictures", self._gallery_selected)
        tools = self.menus.addMenu("&Tools")
        self.tray_visibility_action = tools.addAction("Show Messenger icon in system tray")
        self.tray_visibility_action.setCheckable(True)
        self.tray_visibility_action.setChecked(
            self.presence.preferences.data.get("show_tray_icon", True)
            if self.presence.preferences else True
        )
        self.tray_visibility_action.toggled.connect(self.trayVisibilityRequested)
        tools.addAction("AI / Local Models…", self.aiSettingsRequested.emit)
        tools.addAction("Export all saved chats…", lambda: self._export_history(True))
        tools.addAction("Import saved chats…", self._import_history)
        tools.addAction("Chat history / recovery tools…", self._history_tools)
        self.menus.addMenu("&Help").addAction("About MSN Messenger", self._about)

    def _about(self):
        QMessageBox.information(self, "MSN Messenger",
            "Private 2011 slice-of-life simulator.\nSupplied MSN artwork and character profiles.\n"
            "Chat replies use your local model; online presence is simulated.")

    def _toggle_background(self, checked):
        self._show_background = checked
        self.rebuild_tree()

    def _toggle_legacy(self, checked):
        self._show_legacy = checked
        self.rebuild_tree()

    def _resize_roster(self):
        self.tree.setFont(QFont("Segoe UI", self.contact_text_size.currentData()))

    def rebuild_tree(self):
        selected = self.tree.currentItem()
        selected_id = selected.data(0, Qt.ItemDataRole.UserRole) if selected else None
        expanded = {
            self.tree.topLevelItem(i).data(0, Qt.ItemDataRole.UserRole):
            self.tree.topLevelItem(i).isExpanded()
            for i in range(self.tree.topLevelItemCount())
        }
        self.tree.clear()
        query = self.search_input.text().strip().casefold()
        candidates = list(MSN_CONTACTS)
        if not self._show_background:
            candidates = [c for c in candidates if c.contact_id in SUPPLIED_PROFILES]
        if self._show_legacy:
            candidates += [c for c in CONTACTS if c not in MSN_CONTACTS]
        matches = [c for c in candidates if query in c.online_name.casefold() or query in c.display_name.casefold()]
        online = [c for c in matches if self.presence.states.get(c.contact_id, "Offline") != "Offline"]
        offline = [c for c in matches if self.presence.states.get(c.contact_id, "Offline") == "Offline"]
        for label, contacts in (("Online", online), ("Offline", offline)):
            group = QTreeWidgetItem(self.tree, [f"{label} ({len(contacts)}/{len(candidates)})"])
            group.setData(0, Qt.ItemDataRole.UserRole, label)
            group.setExpanded(expanded.get(label, True))
            for contact in contacts:
                state = self.presence.state(contact.contact_id)
                item = QTreeWidgetItem(group, [contact.online_name])
                item.setData(0, Qt.ItemDataRole.UserRole, contact.contact_id)
                combined = QPixmap(48, 24)
                combined.fill(Qt.GlobalColor.transparent)
                painter = QPainter(combined)
                painter.drawPixmap(0, 3, status_icon(state).pixmap(18, 18))
                if contact.icon_path:
                    painter.drawPixmap(23, 0, QPixmap(str(MSN_ASSETS / contact.icon_path)).scaled(
                        24, 24, Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    ))
                painter.end()
                item.setIcon(0, QIcon(combined))
                item.setToolTip(0, f"{state} · {contact.species} · {contact.age_label}")
                if contact.contact_id == selected_id:
                    self.tree.setCurrentItem(item)
        self.tree.setIconSize(QSize(48, 24))
        self._resize_roster()

    def _selected(self, item=None):
        item = item or self.tree.currentItem()
        contact_id = item.data(0, Qt.ItemDataRole.UserRole) if item else None
        return self._contacts_by_id.get(contact_id)

    def _select_item(self, item, _column=0):
        contact = self._selected(item)
        if contact:
            for row in range(self.contact_list.count()):
                if self.contact_list.item(row).data(Qt.ItemDataRole.UserRole) == contact.contact_id:
                    self.contact_list.setCurrentRow(row)
                    break

    def _open_item(self, item, _column=0):
        contact = self._selected(item)
        if contact:
            self.conversationRequested.emit(contact)

    def _open_selected(self):
        item = self.tree.currentItem()
        if item:
            self._open_item(item)

    def _block_selected(self):
        contact = self._selected()
        if contact:
            self.presence.toggle_block(contact.contact_id)

    def _gallery_selected(self):
        contact = self._selected()
        if contact:
            self._gallery_dialog = show_gallery(contact, self)

    def _context_menu(self, point):
        item = self.tree.itemAt(point)
        if item is None or not self._selected(item):
            return
        self.tree.setCurrentItem(item)
        menu = QMenu(self)
        menu.addAction("Send an instant message", self._open_selected)
        menu.addAction("View pictures", self._gallery_selected)
        menu.addAction("Block / Unblock", self._block_selected)
        menu.exec(self.tree.viewport().mapToGlobal(point))

    def _choose_status(self):
        statuses = ["Online", "Away", "Do not disturb", "Offline"]
        state, accepted = QInputDialog.getItem(self, "My status", "Status:", statuses,
                                               statuses.index(self.presence.user_status), False)
        if not accepted:
            return
        message = ""
        if state == "Away":
            message, accepted = QInputDialog.getText(self, "Away message", "Message:")
            if not accepted:
                return
        self.presence.set_user_status(state, message)

    def _update_user(self):
        status = self.presence.user_status
        message = self.presence.away_message
        self.user_status.setText(f"{status} — {message}" if message else status)
        self.user_status.setIcon(status_icon(status))
        if hasattr(self, "preference_status"):
            self.preference_status.setText(self.presence.preferences.error if self.presence.preferences else "")
            self.preference_status.setVisible(bool(self.preference_status.text()))

    def _presence_changed(self, contact_id, state):
        contact = self._contacts_by_id.get(contact_id)
        if contact:
            self.activity.setText(f"{contact.online_name} is now {state.lower()}.")
        self.rebuild_tree()
        self._update_user()

    def _add_contact_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add a Contact")
        root = QVBoxLayout(dialog)
        root.addWidget(QLabel("Contact address or screen name:"))
        field = QLineEdit()
        root.addWidget(field)
        note = QLabel("Creating additional contacts will be available in a later update.\n"
                      "Your supplied community is already installed.")
        note.setWordWrap(True)
        root.addWidget(note)
        close = QPushButton("Close")
        close.clicked.connect(dialog.accept)
        root.addWidget(close)
        dialog.exec()

    def set_unread_mail(self, count):
        self._unread_mail = max(0, int(count))
        self._flash_mail()

    def _flash_mail(self):
        self._mail_lit = not self._mail_lit if self._unread_mail else False
        self.mail_button.setText(f"Inbox ({self._unread_mail})" if self._unread_mail else "Inbox")
        self.mail_icon.setIcon(
            QIcon() if self._unread_mail and self._mail_lit else self._mail_indicator
        )
        self.mail_button.setStyleSheet(
            "border: 0; background: transparent; text-align: left; color: "
            + ("#d17c00;" if self._mail_lit else "#305476;")
        )

    def _open_mail(self):
        QMessageBox.information(self, "Inbox", "The email program is not connected to MSN yet.")

    def set_advertisements(self, advertisements):
        checked = []
        for image, target in advertisements:
            path = Path(image)
            if QPixmap(str(path)).isNull():
                raise ValueError(f"Cannot load advertisement: {path}")
            if target and not target.startswith(("http://", "https://")):
                raise ValueError("Advertisement targets must be web addresses.")
            checked.append((path, target))
        if not checked:
            raise ValueError("At least one advertisement is required.")
        self._advertisements, self._ad_index = checked, 0
        self._rotate_ad(False)

    def _rotate_ad(self, advance=True):
        if advance:
            self._ad_index = (self._ad_index + 1) % len(self._advertisements)
        image, target = self._advertisements[self._ad_index]
        self.ad_button.setIcon(QIcon(str(image)))
        self.ad_button.setIconSize(self.ad_button.size())
        self.ad_button.setToolTip(target or "MSN Messenger")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "ad_button"):
            QTimer.singleShot(0, lambda: self.ad_button.setIconSize(self.ad_button.size()))

    def _click_ad(self):
        target = self._advertisements[self._ad_index][1]
        if target:
            self.browserRequested.emit(target)

    def _history_tools(self):
        if not self._selected():
            QMessageBox.information(self, "Select a contact", "Select a contact before opening history tools.")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Messenger history tools")
        root = QVBoxLayout(dialog)
        note = QLabel("Applies to the contact selected in the list and the active fursona.")
        root.addWidget(note)
        for text, callback in (
            ("Export selected chat…", lambda: self._export_history()),
            ("Clear selected chat…", self._clear_history),
            ("Preview / assign older chat…", self._assign_legacy_history),
            ("Retry saving", self._retry_save_history),
        ):
            button = QPushButton(text)
            button.clicked.connect(callback)
            root.addWidget(button)
        self.history_status.setParent(dialog)
        root.addWidget(self.history_status)
        dialog.exec()
        self.history_status.setParent(self._legacy_stash)
        self.history_status.hide()

    def closeEvent(self, event):
        if not self.confirm_close():
            event.ignore()
            return
        self._ad_timer.stop()
        self._mail_timer.stop()
        if self._owns_presence:
            self.presence.stop()
        self.client.cancel()
        QWidget.closeEvent(self, event)


class MSNConversationApp(MSNHistoryParticipant, MessengerApp):
    messageArrived = Signal(str)

    def __init__(self, account, service, contact, parent=None, ai_service=None, presence=None, history_session=None):
        self.presence = presence
        self._chat_contact = contact
        super().__init__(account, service, parent, ai_service)
        root = stash_legacy_ui(self)
        self.setMinimumSize(500, 390)
        self._font = QFont("Segoe UI", 10)
        self._color = "#000000"
        self._background = None
        self._last_received = ""
        self._dialogs = []
        old_composer = self.message_edit
        self.message_edit = MessageComposer()
        self.message_edit.setObjectName("messengerMessage")
        self.message_edit.returnPressed.connect(self._send_message)
        old_composer.deleteLater()
        self.menus = QMenuBar()
        root.addWidget(self.menus)
        self._build_chat_menus()
        self.canvas = TemplateCanvas("MSN_IM_Window_Template.jpg")
        root.addWidget(self.canvas, 1)
        old_transcript = self.transcript
        self.transcript = QTextBrowser()
        self.transcript.setObjectName("messengerTranscript")
        self.transcript.setOpenLinks(False)
        self.transcript.setOpenExternalLinks(False)
        self.transcript.anchorClicked.connect(self._open_picture)
        old_transcript.deleteLater()
        self.transcript.setStyleSheet("border: 0; background: white;")
        self.to_label = QLabel(f"To: {contact.online_name}")
        self.to_label.setStyleSheet("background: #e9f1f9;")
        self.recipient_avatar = Avatar(
            str(MSN_ASSETS / contact.icon_path) if contact.icon_path else "",
            stretch_to_frame=True,
        )
        self.my_avatar = Avatar(player_avatar(account), stretch_to_frame=True)
        self.last_received = QLabel("Last message received on: —")
        self.last_received.setStyleSheet("background: #e2eaf5; font-size: 8pt;")
        self.message_edit.setStyleSheet("background: white; border: 0;")
        self.message_edit.setPlaceholderText("Type a message…")
        self.send_button.setStyleSheet("background: #f5f9fd; border: 1px solid #aab9ca;")
        self.message_edit.setAcceptRichText(False)
        self.message_edit.setFont(self._font)
        for widget, rect in (
            (self.to_label, (13, 55, 240, 16)),
            (self.transcript, (13, 74, 242, 95)),
            (self.recipient_avatar, (267, 60, 71, 71)),
            (self.my_avatar, (267, 187, 71, 71)),
            (self.message_edit, (13, 201, 203, 49)),
            (self.send_button, (220, 209, 32, 31)),
            (self.last_received, (13, 255, 243, 12)),
        ):
            self.canvas.place(widget, *rect)
        # Transparent hit targets use the labels already printed in the template.
        for label, rect, callback in (
            ("Font", (14, 180, 41, 14), self._choose_font),
            ("Emoticons", (58, 180, 20, 14), self._emoji_menu),
            ("Winks", (87, 180, 45, 14), self._wink),
            ("Backgrounds", (140, 180, 74, 14), self._choose_background),
            ("Animated message", (224, 180, 18, 14), self._wink),
        ):
            button = QPushButton()
            button.setAccessibleName(label)
            button.setToolTip(label)
            button.setStyleSheet("border: 0; background: transparent;")
            button.clicked.connect(callback)
            self.canvas.place(button, *rect)
        for label, rect in (
            ("Invite", (10, 6, 43, 38)), ("Send Files", (54, 6, 39, 38)),
            ("Webcam", (94, 6, 41, 38)), ("Audio", (137, 6, 31, 38)),
            ("Activities", (172, 6, 36, 38)), ("Games", (210, 6, 30, 38)),
        ):
            button = QPushButton()
            button.setAccessibleName(label)
            button.setToolTip(f"{label} — planned for a later update")
            button.setStyleSheet("border: 0; background: transparent;")
            button.clicked.connect(lambda _checked=False, name=label: QMessageBox.information(
                self, name, f"{name} will be implemented in a later update, as noted in your template instructions."))
            self.canvas.place(button, *rect)
        root.addWidget(self.provider_status)
        self.provider_status.show()
        root.addWidget(self.history_status)
        self.history_status.show()
        # Recoverable save failures remain visible without opening a hidden tools window.
        root.addWidget(self.retry_save_button)
        self.retry_save_button.show()
        self.preference_status = QLabel()
        self.preference_status.setWordWrap(True)
        root.addWidget(self.preference_status)
        if self.presence and self.presence.preferences:
            prefs = self.presence.preferences
            self.last_received.setText(
                "Last message received on: " + prefs.data["last_received"].get(contact.contact_id, "—")
            )
            self.preference_status.setText(prefs.error)
        self.preference_status.setVisible(bool(self.preference_status.text()))
        self._typing = False
        self._idle_received_text = self.last_received.text()
        self.client.busyChanged.connect(self._typing_busy_changed)
        self._wink_timer = QTimer(self)
        self._wink_timer.setSingleShot(True)
        self._wink_timer.timeout.connect(lambda: self.my_avatar.setStyleSheet(
            "background: transparent; border: 0;"))
        self.advanced = QDialog(self)
        self.advanced.setWindowTitle("Conversation details / AI context")
        self.advanced.resize(660, 620)
        controls = QVBoxLayout(self.advanced)
        for widget in (
            self.contact_details, self.relationship_details, self.context_status,
            self.additional_context_preview, self.additional_context_button,
            self.context_budget, self.model_context_limit,
            self.export_history_button, self.clear_history_button,
            self.assign_legacy_button,
        ):
            if widget is self.context_budget:
                controls.addWidget(QLabel("AI input budget (bytes / exact tokens):"))
            elif widget is self.model_context_limit:
                controls.addWidget(QLabel("Manual model window (tokens; zero = automatic):"))
            controls.addWidget(widget)
            widget.show()
        for row in range(self.contact_list.count()):
            if self.contact_list.item(row).data(Qt.ItemDataRole.UserRole) == contact.contact_id:
                self.contact_list.setCurrentRow(row)
                break
        if presence:
            presence.changed.connect(self._presence_update)
            presence.userChanged.connect(self._presence_update)
            self.client.busyChanged.connect(self._mark_chatting)
            self._presence_update()
        self._refresh_controls()
        self._render_history()
        if history_session:
            history_session.attach(self)

    def sizeHint(self):
        return QSize(680, 570)

    def _build_chat_menus(self):
        file = self.menus.addMenu("&File")
        file.addAction("Export conversation…", lambda: self._export_history())
        file.addAction("Import chats…", self._import_history)
        file.addAction("Close", self.close)
        edit = self.menus.addMenu("&Edit")
        edit.addAction("Copy transcript selection", lambda: self.transcript.copy())
        edit.addAction("Select all messages", lambda: self.transcript.selectAll())
        edit.addAction("Paste", self.message_edit.paste)
        actions = self.menus.addMenu("&Actions")
        actions.addAction("View contact pictures", self._gallery)
        actions.addAction("Insert emoticon", self._emoji_menu)
        actions.addAction("Send a wink", self._wink)
        actions.addAction("Block / Unblock", self._block)
        tools = self.menus.addMenu("&Tools")
        tools.addAction("AI / Local Models…", self.aiSettingsRequested.emit)
        tools.addAction("Conversation details / AI context…", self._advanced)
        tools.addAction("Font…", self._choose_font)
        tools.addAction("Text color…", self._choose_color)
        tools.addAction("Background…", self._choose_background)
        tools.addAction("Clear conversation…", self._clear_history)
        self.menus.addMenu("&Help").addAction("About this conversation", lambda: QMessageBox.information(
            self, "MSN conversation", "Private local chat. The entire saved transcript is kept; "
            "only bounded, approved context is sent to the model."))

    def _advanced(self):
        self.advanced.show()
        self.advanced.raise_()

    def _can_chat(self):
        ready = super()._can_chat()
        if not self.presence:
            return ready
        return ready and self.presence.user_status != "Offline" and self.presence.state(
            self._chat_contact.contact_id) not in ("Offline", "Blocked")

    def _presence_update(self, *_args):
        if not self.presence:
            return
        state = self.presence.state(self._chat_contact.contact_id)
        self.to_label.setText(f"To: {self._chat_contact.online_name} ({state})")
        metadata = self.presence.metadata(self._chat_contact.contact_id)
        self.to_label.setToolTip(metadata.get("away_message", "") if state == "Away" else state)
        if state in ("Offline", "Blocked") or self.presence.user_status == "Offline":
            self.client.cancel_chat()
            reason = "You are signed out" if self.presence.user_status == "Offline" else f"{self._chat_contact.online_name} is {state.lower()}"
            self._set_provider_status(reason + ". Sending is paused; saved messages remain available.")
        else:
            self._service_state_changed(self.service.state, self.service.status_text)
        self._refresh_controls()

    def _mark_chatting(self, busy):
        if busy:
            self.presence.chatting.add(self._chat_contact.contact_id)
        else:
            self.presence.chatting.discard(self._chat_contact.contact_id)

    def _block(self):
        if self.presence:
            self.presence.toggle_block(self._chat_contact.contact_id)

    def _gallery(self):
        self._dialogs.append(show_gallery(self._chat_contact, self))

    def _choose_font(self):
        accepted, font = QFontDialog.getFont(self._font, self, "Message font")
        if accepted:
            self._font = font
            self.message_edit.setFont(font)
            self.transcript.setFont(font)

    def _choose_color(self):
        color = QColorDialog.getColor(parent=self)
        if color.isValid():
            self._color = color.name()
            self._render_history()

    def _choose_background(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Chat background", "", "Images (*.jpg *.jpeg *.png *.bmp)")
        if not filename:
            return
        pixmap = QPixmap(filename)
        if pixmap.isNull():
            QMessageBox.warning(self, "Chat background", "That image could not be opened.")
            return
        self._background = filename
        # The path comes from the user's local file picker, never from a model response.
        encoded = Path(filename).as_uri() if Path(filename).is_absolute() else filename
        self.transcript.setStyleSheet(f'QTextBrowser {{border: 0; background-image: url("{encoded}");}}')

    def _emoji_menu(self):
        menu = QMenu(self)
        for icon in (":)", ":D", ";)", ":3", "<3", "*wags*", "*purrs*"):
            menu.addAction(icon, lambda value=icon: self.message_edit.insert(value))
        menu.exec(self.message_edit.mapToGlobal(self.message_edit.rect().topLeft()))

    def _wink(self):
        self.message_edit.insert(" *winks!* ")
        if self._can_chat():
            self._send_message()
        self._animate_avatar()

    def _animate_avatar(self):
        # A small, native wink effect; never manufactures a contact reply.
        self.my_avatar.setStyleSheet("background: #fff4bf; border: 2px solid #f2ba39;")
        self._wink_timer.start(700)

    def _render_history(self):
        super()._render_history()
        if not hasattr(self, "_font") or not self.selected_contact:
            return
        self.transcript.clear()
        for message in self.contact_histories[self.selected_contact.contact_id]:
            speaker = "You" if message["role"] == "user" else self.selected_contact.online_name
            body = escape(message["content"])
            if message["role"] == "assistant":
                for filename in self.selected_contact.gallery:
                    short = Path(filename).name
                    token = escape(f"[share:{short}]")
                    body = body.replace(token, f'<a href="msn-picture:{escape(short, quote=True)}">'
                                              f'View shared picture: {escape(short)}</a>')
            self.transcript.append(f'<b>{escape(speaker)}:</b> <span style="color:{self._color}">{body}</span>')
        self.transcript.moveCursor(self.transcript.textCursor().MoveOperation.End)

    def _open_picture(self, url):
        name = url.toString().removeprefix("msn-picture:")
        if url.scheme() == "msn-picture" and name in {
            Path(filename).name for filename in self._chat_contact.gallery
        }:
            self._dialogs.append(show_gallery(self._chat_contact, self, name))

    def _input_prepared(self, measurement):
        super()._input_prepared(measurement)
        if self._pending_contact_id == self._chat_contact.contact_id and self.client.is_busy:
            self._idle_received_text = self.last_received.text()
            self._typing = True
            self.last_received.setText(
                f"{self._chat_contact.online_name} is typing a message..."
            )

    def _typing_busy_changed(self, busy):
        if not busy and self._typing:
            self._typing = False
            self.last_received.setText(self._idle_received_text)

    def _response_finished(self, success, message):
        contact_id = self._pending_contact_id
        profile_id = self._pending_profile_id
        self._typing_busy_changed(False)
        super()._response_finished(success, message)
        if success and contact_id == self._chat_contact.contact_id and profile_id == self._profile_id:
            self.networkTransferRequested.emit(
                "incoming", len(message.encode("utf-8")) + 128,
                "MSN chat reply",
            )
            from datetime import datetime
            now = datetime.now()
            timestamp = f"{format_locked_date(now)} {format_locked_time(now)}"
            self.last_received.setText("Last message received on: " + timestamp)
            if self.presence and self.presence.preferences:
                prefs = self.presence.preferences
                prefs.data["last_received"][self._chat_contact.contact_id] = timestamp
                prefs.save()
                self.preference_status.setText(prefs.error)
                self.preference_status.setVisible(bool(prefs.error))
            if "*winks!*" in message:
                self._animate_avatar()
            self.messageArrived.emit(contact_id)

    def closeEvent(self, event):
        if not self.confirm_close():
            event.ignore()
            return
        if self.presence:
            self.presence.chatting.discard(self._chat_contact.contact_id)
        self._wink_timer.stop()
        self._typing_busy_changed(False)
        self.client.cancel()
        QWidget.closeEvent(self, event)
