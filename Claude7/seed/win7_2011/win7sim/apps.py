from __future__ import annotations

from datetime import date
from html import escape
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .config import (
    assign_legacy_messenger_history,
    legacy_messenger_history_available,
    preview_legacy_messenger_history,
    STORAGE_FOLDERS,
    STORAGE_ROOT,
    clear_messenger_history,
    export_messenger_histories,
    import_messenger_histories,
    load_messenger_history,
    read_messenger_export,
    save_messenger_history,
)
from .ai_service import AIChannel, AIService
from .contacts import CONTACTS, ContactIdentity, messenger_system_prompt, relationship_for
from .identity import FursonaProfile, UserAccount, age_on_january_first
from .messenger_context import (
    DEFAULT_INPUT_BUDGET, additional_context, bounded_messages, input_size,
    model_input_budget, reply_reserve, summary_messages,
)
from .messenger_memory import ConversationContextDialog, load_context, save_context
from .messenger_import import MessengerImportDialog
from .messenger_legacy import LegacyChatPreviewDialog
from .local_ai import FailureCategory
from .service import ConnectionSimulator, ServiceState


class ProfileDirectoryApp(QWidget):
    """Browse the canonical adult community identities shared with Messenger."""

    def __init__(self, account: UserAccount, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.account = account
        root = QVBoxLayout(self)

        heading = QLabel("Furry Directory")
        heading.setStyleSheet("font-size: 17pt; font-weight: 600; color: #274f70;")
        root.addWidget(heading)
        subheading = QLabel(
            "Browse the shared community roster. These are the same profiles "
            "and stable identities used by Windows Live Messenger."
        )
        subheading.setWordWrap(True)
        subheading.setStyleSheet("color: #5b7285;")
        root.addWidget(subheading)

        filters = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search display or online name…")
        self.search_input.setAccessibleName("Search display or online name")
        self.search_input.setClearButtonEnabled(True)
        self.species_filter = QComboBox()
        self.species_filter.setAccessibleName("Species filter")
        self.species_filter.addItem("All species", None)
        for species in sorted({contact.species for contact in CONTACTS}, key=str.casefold):
            self.species_filter.addItem(species, species)
        self.location_filter = QComboBox()
        self.location_filter.setAccessibleName("Location filter")
        self.location_filter.addItem("All locations", None)
        for location in sorted({contact.location for contact in CONTACTS}, key=str.casefold):
            self.location_filter.addItem(location, location)
        self.reset_filters_button = QPushButton("Reset")
        filters.addWidget(self.search_input, 1)
        filters.addWidget(QLabel("Species:"))
        filters.addWidget(self.species_filter)
        filters.addWidget(QLabel("Location:"))
        filters.addWidget(self.location_filter)
        filters.addWidget(self.reset_filters_button)
        root.addLayout(filters)
        self.results_label = QLabel()
        root.addWidget(self.results_label)
        self._contacts_by_id = {contact.contact_id: contact for contact in CONTACTS}

        body = QHBoxLayout()
        self.profile_list = QListWidget()
        self.profile_list.setMinimumWidth(210)
        self.detail_panel = QWidget()
        self.detail_layout = QVBoxLayout(self.detail_panel)
        self.detail_layout.setContentsMargins(16, 8, 8, 8)
        self.avatar = QLabel()
        self.avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar.setFixedSize(180, 180)
        self.avatar.setStyleSheet(
            "background: #eef3f7; border: 1px solid #cbd8e2; border-radius: 4px;"
        )
        self.name = QLabel()
        self.name.setStyleSheet("font-size: 18pt; font-weight: 600;")
        self.species = QLabel()
        self.location = QLabel()
        self.pronouns = QLabel()
        self.birth_date = QLabel()
        self.bio = QLabel()
        self.bio.setWordWrap(True)
        self.online_name = QLabel()
        self.online_name.setStyleSheet("color: #526e83;")

        self.detail_layout.addWidget(self.avatar, 0, Qt.AlignmentFlag.AlignLeft)
        self.detail_layout.addWidget(self.name)
        form = QFormLayout()
        form.addRow("Species", self.species)
        form.addRow("Location", self.location)
        form.addRow("Pronouns", self.pronouns)
        form.addRow("Date of birth", self.birth_date)
        self.detail_layout.addLayout(form)
        self.detail_layout.addWidget(self.bio)
        self.full_profile_button = QPushButton("Full character profile / pictures…")
        self.full_profile_button.clicked.connect(self._show_full_profile)
        self.detail_layout.addWidget(self.full_profile_button)
        self.detail_layout.addStretch(1)
        self.detail_layout.addWidget(self.online_name)

        body.addWidget(self.profile_list)
        body.addWidget(self.detail_panel, 1)
        root.addLayout(body, 1)

        self.profile_list.currentRowChanged.connect(self._show_profile)
        self.search_input.textChanged.connect(self._filter_profiles)
        self.species_filter.currentIndexChanged.connect(self._filter_profiles)
        self.location_filter.currentIndexChanged.connect(self._filter_profiles)
        self.reset_filters_button.clicked.connect(self._reset_filters)
        self._filter_profiles()

    def _reset_filters(self) -> None:
        controls = (self.search_input, self.species_filter, self.location_filter)
        for control in controls:
            control.blockSignals(True)
        self.search_input.clear()
        self.species_filter.setCurrentIndex(0)
        self.location_filter.setCurrentIndex(0)
        for control in controls:
            control.blockSignals(False)
        self._filter_profiles()

    def _filter_profiles(self) -> None:
        query = self.search_input.text().strip().casefold()
        species = self.species_filter.currentData()
        location = self.location_filter.currentData()
        selected = self.profile_list.currentItem()
        selected_id = selected.data(Qt.ItemDataRole.UserRole) if selected else None
        self.profile_list.blockSignals(True)
        self.profile_list.clear()
        selected_row = 0
        for contact in CONTACTS:
            if query and not (
                query in contact.display_name.casefold()
                or query in contact.online_name.casefold()
            ):
                continue
            if species is not None and contact.species != species:
                continue
            if location is not None and contact.location != location:
                continue
            item = QListWidgetItem(f"{contact.display_name}\n{contact.online_name}")
            item.setData(Qt.ItemDataRole.UserRole, contact.contact_id)
            self.profile_list.addItem(item)
            if contact.contact_id == selected_id:
                selected_row = self.profile_list.count() - 1
        count = self.profile_list.count()
        self.results_label.setText(
            f"{count} of {len(CONTACTS)} profiles"
            if count else "No matching profiles. Try another search or reset the filters."
        )
        self.profile_list.setCurrentRow(selected_row if count else -1)
        self.profile_list.blockSignals(False)
        self._show_profile(self.profile_list.currentRow())

    def _show_profile(self, index: int) -> None:
        item = self.profile_list.item(index) if index >= 0 else None
        profile = self._contacts_by_id.get(item.data(Qt.ItemDataRole.UserRole)) if item else None
        self.detail_panel.setVisible(profile is not None)
        if profile is None:
            for label in (
                self.avatar, self.name, self.species, self.location, self.pronouns,
                self.birth_date, self.bio, self.online_name,
            ):
                label.clear()
            return
        self.name.setText(profile.display_name)
        self.full_profile_button.setEnabled(bool(profile.source_profile or profile.gallery))
        self.species.setText(profile.species)
        self.location.setText(profile.location)
        self.pronouns.setText(profile.pronouns)
        self.birth_date.setText(profile.age_label)
        self.bio.setText(
            f"{profile.bio}\n\nInterests: {', '.join(profile.interests)}\n"
            f"Preferences: {profile.preferences}\n"
            f"Relationship history: {profile.relationship_history}"
        )
        self.avatar.clear()
        self.avatar.setToolTip(f"@{profile.online_name} · {profile.circle.title()} circle")
        if profile.icon_path:
            from .contacts import MSN_ASSETS
            from PySide6.QtGui import QPixmap
            self.avatar.setPixmap(QPixmap(str(MSN_ASSETS / profile.icon_path)).scaled(
                self.avatar.size(), Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            ))
        else:
            self.avatar.setText(f"@{profile.online_name}\n{profile.circle.title()} circle")
        self.online_name.setText(f"Stable community ID: {profile.contact_id}")

    def _show_full_profile(self) -> None:
        item = self.profile_list.currentItem()
        contact = self._contacts_by_id.get(item.data(Qt.ItemDataRole.UserRole)) if item else None
        if not contact:
            return
        from PySide6.QtWidgets import QDialog, QTextBrowser
        from .msn_widgets import show_gallery
        dialog = QDialog(self)
        dialog.setWindowTitle(f"{contact.online_name} — supplied character profile")
        dialog.resize(640, 560)
        root = QVBoxLayout(dialog)
        text = QTextBrowser()
        text.setPlainText(contact.source_profile or contact.bio)
        root.addWidget(text)
        gallery = QPushButton("View supplied pictures…")
        gallery.setEnabled(bool(contact.gallery))
        gallery.clicked.connect(lambda: show_gallery(contact, dialog))
        root.addWidget(gallery)
        dialog.exec()


class NotepadApp(QWidget):
    documentAccessed = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.current_path: Path | None = None

        root = QVBoxLayout(self)
        toolbar = QHBoxLayout()
        self.open_button = QPushButton("Open")
        self.save_button = QPushButton("Save")
        self.path_label = QLabel("Untitled")
        self.path_label.setStyleSheet("color: #60778a;")
        self.open_button.clicked.connect(self._open_file)
        self.save_button.clicked.connect(self._save_file)
        toolbar.addWidget(self.open_button)
        toolbar.addWidget(self.save_button)
        toolbar.addSpacing(8)
        toolbar.addWidget(self.path_label, 1)
        root.addLayout(toolbar)

        self.editor = QTextEdit()
        self.editor.setAcceptRichText(False)
        self.editor.setFontFamily("Consolas")
        self.editor.setPlaceholderText("Type a note…")
        root.addWidget(self.editor, 1)

    def _open_file(self) -> None:
        documents = STORAGE_ROOT / "UserData" / "Documents"
        documents.mkdir(parents=True, exist_ok=True)
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open text file",
            str(documents),
            "Text files (*.txt *.log *.ini);;All files (*.*)",
        )
        if not file_path:
            return
        self.load_file(Path(file_path))

    def load_file(self, path: Path) -> bool:
        if self.editor.document().isModified():
            answer = QMessageBox.question(
                self, "Notepad", "Discard unsaved changes and open this document?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return False
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            QMessageBox.warning(self, "Notepad", f"Could not open this file:\n{exc}")
            return False
        self.editor.setPlainText(text)
        self.editor.document().setModified(False)
        self.current_path = path
        self.path_label.setText(path.name)
        self.documentAccessed.emit(str(path))
        return True

    def _save_file(self) -> None:
        documents = STORAGE_ROOT / "UserData" / "Documents"
        documents.mkdir(parents=True, exist_ok=True)
        initial_path = str(self.current_path or (documents / "Untitled.txt"))
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save text file",
            initial_path,
            "Text files (*.txt);;All files (*.*)",
        )
        if not file_path:
            return
        path = Path(file_path)
        try:
            path.write_text(self.editor.toPlainText(), encoding="utf-8")
        except OSError as exc:
            QMessageBox.warning(self, "Notepad", f"Could not save this file:\n{exc}")
            return
        self.current_path = path
        self.path_label.setText(path.name)
        self.editor.document().setModified(False)
        self.documentAccessed.emit(str(path))


class MyComputerApp(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        heading = QLabel("Computer")
        heading.setStyleSheet("font-size: 17pt; font-weight: 600; color: #274f70;")
        root.addWidget(heading)
        root.addWidget(
            QLabel(
                "Local folders are available without a network connection or an LLM. "
                "The program creates missing folders and leaves existing files alone."
            )
        )
        self.folder_list = QListWidget()
        for folder in STORAGE_FOLDERS:
            relative = folder.relative_to(STORAGE_ROOT)
            item = QListWidgetItem(f"{relative}    —    {folder}")
            self.folder_list.addItem(item)
        root.addWidget(self.folder_list, 1)


class MessengerApp(QWidget):
    """Messenger uses a conversation channel on the desktop's shared AI service."""

    aiSettingsRequested = Signal()
    networkTransferRequested = Signal(str, int, str)

    def __init__(
        self,
        account: UserAccount,
        service: ConnectionSimulator,
        parent: QWidget | None = None,
        ai_service: AIService | None = None,
    ) -> None:
        super().__init__(parent)
        self.account = account
        self.service = service
        self.ai = ai_service or AIService(self)
        self.client = AIChannel(self.ai, parent=self)
        self.client.inputPrepared.connect(self._input_prepared)
        self._pending_draft = None
        self._last_input_measurement = None
        self._histories_by_profile: dict[str, dict[str, list[dict[str, str]]]] = {}
        self._errors_by_profile: dict[str, dict[str, str]] = {}
        self._blocked_saves_by_profile: dict[str, set[str]] = {}
        self._unsaved_conversations: set[tuple[str, str]] = set()
        self._close_preapproved = False
        self._context_by_profile: dict[str, dict[str, str]] = {}
        self._additional_context = {}
        self._additional_context_errors = {}
        self._profile_id: str | None = None
        self._pending_profile_id: str | None = None
        self._sync_profile()
        self.selected_contact: ContactIdentity | None = None

        root = QVBoxLayout(self)
        heading = QLabel("Windows Live Messenger")
        heading.setStyleSheet("font-size: 17pt; font-weight: 600; color: #274f70;")
        root.addWidget(heading)
        description = QLabel(
            "Chats use the shared local AI service. Replies are never "
            "generated from scripts; if the provider is unavailable, this app says so."
        )
        description.setWordWrap(True)
        root.addWidget(description)

        settings = QHBoxLayout()
        self.ai_settings_button = QPushButton("Open AI Settings")
        self.ai_settings_button.setObjectName("openAiSettings")
        self.ai_settings_button.clicked.connect(self.aiSettingsRequested.emit)
        settings.addWidget(self.ai_settings_button)
        self.export_all_button = QPushButton("Export all saved chats…")
        self.export_all_button.setObjectName("messengerExportAll")
        self.export_all_button.clicked.connect(lambda: self._export_history(all_contacts=True))
        settings.addWidget(self.export_all_button)
        self.import_button = QPushButton("Import saved chats…")
        self.import_button.setObjectName("messengerImport")
        self.import_button.clicked.connect(self._import_history)
        settings.addWidget(self.import_button)
        settings.addStretch()
        root.addLayout(settings)

        self.provider_status = QLabel(self.ai.status)
        self.provider_status.setObjectName("providerStatus")
        self.provider_status.setWordWrap(True)
        self.provider_status.setStyleSheet("color: #7a4b12;")
        root.addWidget(self.provider_status)

        body = QSplitter(Qt.Orientation.Horizontal)
        contacts_panel = QWidget()
        contacts_layout = QVBoxLayout(contacts_panel)
        contacts_layout.setContentsMargins(0, 0, 0, 0)
        text_size_row = QHBoxLayout()
        text_size_label = QLabel("Contact text size:")
        self.contact_text_size = QComboBox()
        self.contact_text_size.setObjectName("messengerContactTextSize")
        self.contact_text_size.setAccessibleName("Messenger contact text size")
        for label, points in (("Normal", 10), ("Large", 12), ("Extra large", 14)):
            self.contact_text_size.addItem(label, points)
        text_size_label.setBuddy(self.contact_text_size)
        text_size_row.addWidget(text_size_label)
        text_size_row.addWidget(self.contact_text_size)
        contacts_layout.addLayout(text_size_row)
        self.search_input = QLineEdit()
        self.search_input.setObjectName("messengerContactSearch")
        self.search_input.setPlaceholderText("Search display or online name…")
        self.search_input.setAccessibleName("Search Messenger contacts by display or online name")
        self.search_input.setClearButtonEnabled(True)
        contacts_layout.addWidget(self.search_input)
        self.search_results = QLabel()
        self.search_results.setObjectName("messengerContactResults")
        contacts_layout.addWidget(self.search_results)
        self.contact_list = QListWidget()
        self.contact_list.setObjectName("messengerContacts")
        self.contact_list.setMinimumWidth(175)
        self._contacts_by_id = {contact.contact_id: contact for contact in CONTACTS}
        for contact in CONTACTS:
            item = QListWidgetItem(f"{contact.display_name}\n{contact.online_name}")
            item.setData(Qt.ItemDataRole.UserRole, contact.contact_id)
            self.contact_list.addItem(item)
        contacts_layout.addWidget(self.contact_list, 1)
        self.search_results.setText(f"{len(CONTACTS)} contacts")
        self.contact_text_size.currentIndexChanged.connect(self._resize_contact_text)

        conversation = QWidget()
        conversation_layout = QVBoxLayout(conversation)
        self.contact_heading = QLabel("Select a contact")
        self.contact_heading.setStyleSheet("font-size: 13pt; font-weight: 600;")
        conversation_layout.addWidget(self.contact_heading)
        self.contact_details = QLabel(
            "Select a community member to view their shared profile."
        )
        self.contact_details.setWordWrap(True)
        self.contact_details.setStyleSheet("color: #526e83;")
        conversation_layout.addWidget(self.contact_details)
        self.relationship_details = QLabel()
        self.relationship_details.setObjectName("messengerRelationshipContext")
        self.relationship_details.setTextFormat(Qt.TextFormat.PlainText)
        self.relationship_details.setWordWrap(True)
        conversation_layout.addWidget(self.relationship_details)
        self.transcript = QTextEdit()
        self.transcript.setObjectName("messengerTranscript")
        self.transcript.setReadOnly(True)
        conversation_layout.addWidget(self.transcript, 1)
        self.history_status = QLabel()
        self.history_status.setObjectName("messengerHistoryStatus")
        self.history_status.setWordWrap(True)
        conversation_layout.addWidget(self.history_status)
        self.retry_save_button = QPushButton("Retry saving")
        self.retry_save_button.setObjectName("messengerRetrySave")
        self.retry_save_button.clicked.connect(self._retry_save_history)
        conversation_layout.addWidget(self.retry_save_button)
        self.assign_legacy_button = QPushButton("Preview older chat (read-only)…")
        self.assign_legacy_button.setObjectName("messengerAssignLegacy")
        self.assign_legacy_button.clicked.connect(self._assign_legacy_history)
        conversation_layout.addWidget(self.assign_legacy_button)
        context_controls = QHBoxLayout()
        context_controls.addWidget(QLabel("AI input budget (bytes / exact tokens):"))
        self.context_budget = QSpinBox()
        self.context_budget.setObjectName("messengerContextBudget")
        self.context_budget.setRange(512, 131072)
        self.context_budget.setSingleStep(512)
        self.context_budget.setValue(DEFAULT_INPUT_BUDGET)
        self.context_budget.setToolTip(
            "With a supported single-model llama-server and known/manual window, "
            "bounds exact server-formatted input tokens. Otherwise bounds UTF-8 "
            "input plus estimated message framing, not exact tokens. "
            "Model limits reserve reply space automatically. Lower this if the server reports "
            "a context limit. Applies to this Messenger window; no automatic retries."
        )
        context_controls.addWidget(self.context_budget)
        conversation_layout.addLayout(context_controls)
        self._context_identity = None
        model_controls = QHBoxLayout()
        model_controls.addWidget(QLabel("Manual model window (tokens):"))
        self.model_context_limit = QSpinBox()
        self.model_context_limit.setObjectName("messengerModelContextLimit")
        self.model_context_limit.setRange(0, 16_777_216)
        self.model_context_limit.setSpecialValueText("Automatic / unknown")
        self.model_context_limit.setSingleStep(256)
        self.model_context_limit.setToolTip(
            "Enter the server's actual context window (at least 256 tokens) when metadata is "
            "missing, or a lower limit. Saved separately for each backend, server and model. "
            "Zero clears the manual override. Without template-aware tokenization, "
            "input bytes remain an estimate, not exact tokens."
        )
        self.model_context_limit.editingFinished.connect(self._save_model_context_limit)
        model_controls.addWidget(self.model_context_limit)
        conversation_layout.addLayout(model_controls)
        self.context_status = QLabel()
        self.context_status.setObjectName("messengerContextStatus")
        self.context_status.setTextFormat(Qt.TextFormat.PlainText)
        self.context_status.setWordWrap(True)
        conversation_layout.addWidget(self.context_status)
        self.additional_context_button = QPushButton("Pinned details / optional summary…")
        self.additional_context_button.clicked.connect(self._edit_additional_context)
        conversation_layout.addWidget(self.additional_context_button)
        self.additional_context_preview = QTextEdit()
        self.additional_context_preview.setReadOnly(True)
        self.additional_context_preview.setMaximumHeight(85)
        self.additional_context_preview.setAccessibleName("Exact additional AI context in use")
        conversation_layout.addWidget(self.additional_context_preview)
        self.context_budget.valueChanged.connect(self._update_context_status)
        self.export_history_button = QPushButton("Export saved conversation…")
        self.export_history_button.setObjectName("messengerExportHistory")
        self.export_history_button.clicked.connect(lambda: self._export_history())
        conversation_layout.addWidget(self.export_history_button)
        self.clear_history_button = QPushButton("Clear conversation…")
        self.clear_history_button.setObjectName("messengerClearHistory")
        self.clear_history_button.clicked.connect(self._clear_history)
        conversation_layout.addWidget(self.clear_history_button)
        composer = QHBoxLayout()
        self.message_edit = QLineEdit()
        self.message_edit.setObjectName("messengerMessage")
        self.message_edit.setPlaceholderText("Write a message…")
        self.send_button = QPushButton("Send")
        self.send_button.setObjectName("messengerSend")
        composer.addWidget(self.message_edit, 1)
        composer.addWidget(self.send_button)
        conversation_layout.addLayout(composer)
        body.addWidget(contacts_panel)
        body.addWidget(conversation)
        body.setStretchFactor(1, 1)
        root.addWidget(body, 1)

        self.send_button.clicked.connect(self._send_message)
        self.message_edit.returnPressed.connect(self._send_message)
        self.contact_list.currentRowChanged.connect(self._select_contact)
        self.search_input.textChanged.connect(self._filter_contacts)
        self.client.connectionFinished.connect(self._connection_finished)
        self.client.responseFinished.connect(self._response_finished)
        self.client.busyChanged.connect(self._busy_changed)
        self.service.stateChanged.connect(self._service_state_changed)
        self._service_state_changed(self.service.state, self.service.status_text)
        self.contact_list.setCurrentRow(0)
        self._refresh_controls()

    def _connection_finished(self, success: bool, message: str) -> None:
        if not self.service.chat_available:
            message = f"{self.service.status_text}. Messaging is paused. Engine: {message}"
        self._set_provider_status(
            message, error=not success or self.ai.error or not self.service.chat_available
        )
        self._refresh_controls()

    def _sync_profile(self) -> None:
        profile = self.account.active_profile
        profile_id = profile.profile_id if profile else ""
        if self._profile_id == profile_id:
            return
        self._profile_id = profile_id
        if profile_id not in self._histories_by_profile:
            histories = {contact.contact_id: [] for contact in CONTACTS}
            errors: dict[str, str] = {}
            if profile_id:
                for contact in CONTACTS:
                    try:
                        histories[contact.contact_id] = load_messenger_history(
                            contact.contact_id, profile_id
                        )
                    except (OSError, UnicodeError, ValueError) as exc:
                        errors[contact.contact_id] = str(exc)
            self._histories_by_profile[profile_id] = histories
            self._errors_by_profile[profile_id] = errors
            # A failed load means the in-memory history may be incomplete.
            # Never overwrite that file with a new or partial conversation.
            self._blocked_saves_by_profile[profile_id] = set(errors)
            self._context_by_profile[profile_id] = {}
        self.contact_histories = self._histories_by_profile[profile_id]
        self.history_errors = self._errors_by_profile[profile_id]
        self.blocked_history_saves = self._blocked_saves_by_profile[profile_id]
        self.context_failures = self._context_by_profile[profile_id]
        if hasattr(self, "message_edit"):
            self.message_edit.clear()
            self._select_contact(self.contact_list.currentRow())

    def _resize_contact_text(self) -> None:
        """Adjust readability without rebuilding the roster or conversation."""
        points = self.contact_text_size.currentData()
        for widget in (self.search_input, self.contact_list, self.search_results):
            widget.setStyleSheet(f"font-size: {points}pt;")
        self.search_input.setMinimumHeight(self.search_input.fontMetrics().height() + 14)

    def _filter_contacts(self) -> None:
        query = self.search_input.text().strip().casefold()
        selected_id = self.selected_contact.contact_id if self.selected_contact else None
        self.contact_list.blockSignals(True)
        self.contact_list.clear()
        selected_row = 0
        for contact in CONTACTS:
            if query and not (
                query in contact.display_name.casefold()
                or query in contact.online_name.casefold()
            ):
                continue
            item = QListWidgetItem(f"{contact.display_name}\n{contact.online_name}")
            item.setData(Qt.ItemDataRole.UserRole, contact.contact_id)
            self.contact_list.addItem(item)
            if contact.contact_id == selected_id:
                selected_row = self.contact_list.count() - 1
        self.contact_list.setCurrentRow(selected_row if self.contact_list.count() else -1)
        self.contact_list.blockSignals(False)
        count = self.contact_list.count()
        self.search_results.setText(
            f"{count} of {len(CONTACTS)} contacts" if count else "No matching contacts"
        )
        self._select_contact(self.contact_list.currentRow())

    def _select_contact(self, index: int) -> None:
        self._sync_profile()
        item = self.contact_list.item(index)
        contact = self._contacts_by_id.get(
            item.data(Qt.ItemDataRole.UserRole)
        ) if item else None
        if contact is None:
            self.selected_contact = None
            self.contact_heading.setText("Select a contact")
            self.contact_details.setText("Select a community member to view their shared profile.")
            self.relationship_details.clear()
            self._render_history()
            self._update_history_status()
            self._refresh_controls()
            return
        self.selected_contact = contact
        self.contact_heading.setText(contact.display_name)
        self.contact_details.setText(
            f"{contact.species} · {contact.pronouns} · {contact.online_name}\n"
            f"{contact.age_label} · {contact.bio}"
        )
        relationship = relationship_for(contact, self.account.active_profile)
        self.relationship_details.setText(
            relationship.as_text() if relationship else
            "Use the friendship and relationship details in the supplied character "
            "profile; no additional player-specific backstory has been invented."
            if contact.source_profile else
            "No established friendship history for the active fursona."
        )
        self._render_history()
        self._update_history_status()
        self._refresh_controls()

    def _render_history(self) -> None:
        self.transcript.clear()
        self._update_context_status()
        if self.selected_contact is None:
            return
        for message in self.contact_histories[self.selected_contact.contact_id]:
            speaker = "You" if message["role"] == "user" else self.selected_contact.display_name
            self.transcript.append(
                f"<b>{escape(speaker)}:</b> {escape(message['content'])}"
            )

    def _export_history(self, all_contacts: bool = False) -> None:
        self._sync_profile()
        if not self._profile_id:
            return
        profile_id = self._profile_id
        contact = self.selected_contact
        if not all_contacts and contact is None:
            return
        filename = "messenger-chats.json" if all_contacts else f"{contact.contact_id}-chat.json"
        destination, _ = QFileDialog.getSaveFileName(
            self, "Export saved Messenger chats outside Storage",
            str(Path.home() / filename), "Readable JSON (*.json)",
        )
        if not destination:
            return
        try:
            count = export_messenger_histories(
                Path(destination), None if all_contacts else contact.contact_id,
                profile_id,
            )
        except (OSError, UnicodeError, ValueError) as exc:
            QMessageBox.warning(
                self, "Chats not exported",
                f"Could not export saved chats: {exc}\n\n"
                "Your local conversations have not been changed or deleted.",
            )
            return
        QMessageBox.information(
            self, "Chats exported",
            f"Exported {count} saved conversation(s) to:\n{destination}\n\n"
            "Only messages already saved on disk are included. Keep this file "
            "on another drive before formatting the computer.",
        )

    def _import_history(self) -> None:
        self._sync_profile()
        profile = self.account.active_profile
        if profile is None or self.client.is_busy:
            return
        source, _ = QFileDialog.getOpenFileName(
            self, "Choose exported Messenger chats", str(Path.home()), "Readable JSON (*.json)",
        )
        if not source:
            return
        try:
            exported = read_messenger_export(Path(source))
            preview = MessengerImportDialog(exported, profile.fursona_name, self)
            if preview.exec() != QDialog.DialogCode.Accepted:
                return
            if self.client.is_busy or self.account.active_profile_id != profile.profile_id:
                raise ValueError("The active fursona or chat changed. Please start the import again.")
            policy = preview.policy.currentData()
            for chat in exported["conversations"]:
                contact_id = chat["contact_id"]
                saved = load_messenger_history(contact_id, profile.profile_id)
                if self.contact_histories[contact_id] != saved:
                    raise ValueError(
                        "There are unsaved messages in a matching chat. Retry saving "
                        "them before importing; no chats have been changed."
                    )
            updates = import_messenger_histories(exported, profile.profile_id, policy)
        except (OSError, UnicodeError, ValueError) as exc:
            QMessageBox.warning(
                self, "Chats not imported", f"Could not import chats: {exc}\n\n"
                "Existing messages have not been overwritten.",
            )
            return
        for contact_id, messages in updates.items():
            self.contact_histories[contact_id] = messages
            self._unsaved_conversations.discard((profile.profile_id, contact_id))
            self.history_errors.pop(contact_id, None)
            self.blocked_history_saves.discard(contact_id)
            self.context_failures.pop(contact_id, None)
        self._render_history()
        self._refresh_controls()
        QMessageBox.information(
            self, "Chats imported",
            f"Restored {len(updates)} conversation(s) for {profile.fursona_name}. "
            "Matching chats were handled using your selected option.",
        )

    def _clear_history(self) -> None:
        self._sync_profile()
        profile_id = self._profile_id
        contact = self.selected_contact
        if contact is None or not profile_id or self.client.is_busy:
            return
        answer = QMessageBox.question(
            self,
            "Clear conversation",
            f"Permanently delete the saved conversation with {contact.display_name} "
            "and its pinned details / approved summary from this computer? "
            "This cannot be undone.\n\n"
            "Your account, documents, other fursonas' chats, and other contacts' conversations will not "
            "be affected.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if (
            answer != QMessageBox.StandardButton.Yes or self.client.is_busy
            or self.account.active_profile_id != profile_id
        ):
            return
        try:
            save_context(contact.contact_id, profile_id, {"pins": "", "summary": ""})
            self._additional_context[(profile_id, contact.contact_id)] = {"pins": "", "summary": ""}
            self._additional_context_errors.pop((profile_id, contact.contact_id), None)
            clear_messenger_history(contact.contact_id, profile_id)
        except (OSError, ValueError) as exc:
            QMessageBox.warning(
                self,
                "Conversation not cleared",
                f"Could not delete the saved conversation: {exc}\n"
                "The conversation has been kept.",
            )
            return
        self.contact_histories[contact.contact_id] = []
        self._unsaved_conversations.discard((profile_id, contact.contact_id))
        self.history_errors.pop(contact.contact_id, None)
        self.blocked_history_saves.discard(contact.contact_id)
        self.context_failures.pop(contact.contact_id, None)
        self._render_history()
        self._update_history_status()
        self._refresh_controls()

    def _send_message(self) -> None:
        self._sync_profile()
        contact = self.selected_contact
        text = self.message_edit.text().strip()
        if not text or contact is None or not self._can_chat():
            return
        history = self.contact_histories[contact.contact_id]
        proposed = [*history, {"role": "user", "content": text}]
        extra = self._extra_context()
        messages = [{
            "role": "system", "content": messenger_system_prompt(contact, self.account)
            + ("\n\n" + extra if extra else ""),
        }, *proposed]
        self._pending_draft = text
        self._pending_contact_id = contact.contact_id
        self._pending_profile_id = self._profile_id
        try:
            self.client.send_chat(messages, self._input_budget())
        except (ValueError, RuntimeError) as exc:
            self._pending_draft = None
            self._pending_contact_id = None
            self._pending_profile_id = None
            self._set_provider_status(str(exc), error=True)
            self._refresh_controls()
            return
        self.networkTransferRequested.emit(
            "outgoing", len(text.encode("utf-8")) + 128, "MSN chat message"
        )
        self._set_provider_status("Measuring input, then waiting for the shared local AI service…")
        self._refresh_controls()

    def _input_prepared(self, measurement):
        """Commit only once a complete, measured input is ready for generation."""
        contact_id, profile_id = self._pending_contact_id, self._pending_profile_id
        if self._pending_draft is None or not contact_id or not profile_id:
            return
        history = self._histories_by_profile[profile_id][contact_id]
        history.append({"role": "user", "content": self._pending_draft})
        self._context_by_profile[profile_id].pop(contact_id, None)
        self._save_history(contact_id, profile_id)
        if self._profile_id == profile_id:
            if self.message_edit.text().strip() == self._pending_draft:
                self.message_edit.clear()
            self._render_history()
        self._last_input_measurement = (profile_id, contact_id, measurement)
        if self._profile_id == profile_id and self.selected_contact.contact_id == contact_id:
            self._show_context_status(measurement["omitted"], len(history))
            self._append_measurement()
        self._pending_draft = None

    def _response_finished(self, success: bool, message: str) -> None:
        self._sync_profile()
        contact_id = getattr(self, "_pending_contact_id", None)
        profile_id = self._pending_profile_id
        contact = next((item for item in CONTACTS if item.contact_id == contact_id), None)
        if success and contact is not None and profile_id:
            self._histories_by_profile[profile_id][contact.contact_id].append(
                {"role": "assistant", "content": message}
            )
            self._save_history(contact.contact_id, profile_id)
            if self.selected_contact == contact and self._profile_id == profile_id:
                self._render_history()
        elif not success:
            if self._pending_draft is not None:
                self._set_provider_status(message, error=True)
            elif self.ai.backend.last_failure == FailureCategory.CONTEXT_LIMIT:
                guidance = (
                    "The model rejected the context. Reduce the AI input budget "
                    "to include fewer recent messages, "
                    "shorten your next message, or choose a model with a larger "
                    "context window. The complete transcript is kept; this message "
                    "was not automatically retried. Send a message yourself when ready."
                )
                message += " " + guidance
                if contact is not None and profile_id:
                    self._context_by_profile[profile_id][contact.contact_id] = guidance
                    self._update_context_status()
            if self._pending_draft is None:
                self._set_provider_status(
                    f"Chat unavailable: {message}", error=True
                )
        self._pending_draft = None
        self._pending_contact_id = None
        self._pending_profile_id = None
        self._refresh_controls()

    def _service_state_changed(self, state: ServiceState, status: str) -> None:
        if state in (ServiceState.DISCONNECTED, ServiceState.MAINTENANCE):
            self.client.cancel_chat()
            self._set_provider_status(
                f"{status}. Messaging is paused; local programs remain available.",
                error=True,
            )
        elif state is ServiceState.SLOWDOWN:
            self._set_provider_status(
                f"{status}. Background activity is paused; direct chats remain available."
            )
        elif not self.client.is_connected:
            self._set_provider_status(
                f"Internet: Connected. Open AI Settings to connect a local model. {self.ai.status}"
            )
        else:
            self._set_provider_status(
                f"{status}. Direct-conversation model: {self.client.model_name}."
            )
        self._refresh_controls()

    def _busy_changed(self, _busy: bool) -> None:
        self._refresh_controls()

    def _can_chat(self) -> bool:
        return (
            self.client.is_connected
            and not self.client.is_busy
            and self.service.chat_available
            and self.selected_contact is not None
            and self.account.active_profile is not None
        )

    def _refresh_controls(self) -> None:
        self._sync_profile()
        self.send_button.setEnabled(self._can_chat())
        self.export_history_button.setEnabled(self.selected_contact is not None and bool(self._profile_id))
        self.export_all_button.setEnabled(bool(self._profile_id))
        self.import_button.setEnabled(bool(self._profile_id) and not self.client.is_busy)
        self.contact_list.setEnabled(not self.client.is_busy)
        self.search_input.setEnabled(not self.client.is_busy)
        self.clear_history_button.setEnabled(
            self.selected_contact is not None and bool(self._profile_id) and not self.client.is_busy
        )
        self.context_budget.setEnabled(not self.client.is_busy)
        self.additional_context_button.setEnabled(
            bool(self._profile_id) and self.selected_contact is not None and not self.client.is_busy
        )
        self.model_context_limit.setEnabled(not self.ai.is_busy and bool(self.client.model_name))
        self._sync_model_context()
        self._update_history_status()

    def _sync_model_context(self):
        window, source = self.ai.context_for_role()
        endpoint, model = self.ai.settings.endpoint_for("direct"), self.client.model_name
        identity = (self.ai.settings.backend, endpoint, model, window, source)
        if identity == self._context_identity:
            return
        self._context_identity = identity
        manual = self.ai.settings.context_limits.get(endpoint, {}).get(model, 0)
        self.model_context_limit.setValue(manual)
        self.context_budget.setMinimum(1 if window else 512)
        self.context_budget.setMaximum(model_input_budget(window, 131072))
        self.context_budget.setValue(model_input_budget(window, 131072) if window else DEFAULT_INPUT_BUDGET)
        self._update_context_status()

    def _save_model_context_limit(self):
        try:
            self.ai.set_context_limit(self.model_context_limit.value())
        except (ValueError, RuntimeError, OSError) as exc:
            self._set_provider_status(f"Context limit not saved: {exc}", error=True)
            self._context_identity = None
            self._sync_model_context()

    def _input_budget(self):
        window, _ = self.ai.context_for_role()
        return model_input_budget(window, self.context_budget.value())

    def _show_context_status(self, omitted: int, total: int) -> None:
        failure = self.context_failures.get(
            self.selected_contact.contact_id, ""
        ) if self.selected_contact else ""
        window, source = self.ai.context_for_role()
        extra = self._extra_context()
        extra_bytes = len(extra.encode("utf-8")) + (2 if extra else 0)
        key = (self._profile_id, self.selected_contact.contact_id) if self.selected_contact else None
        context_error = self._additional_context_errors.get(key, "")
        sizing = (
            f"{self.client.model_name}: {window} tokens ({source}); "
            f"{reply_reserve(window)} tokens reserved for the reply. "
            if window else
            f"{self.client.model_name}: context metadata missing or invalid. "
            "Set a manual model window; using the adjustable byte estimate meanwhile. "
            f"Reply capped at {reply_reserve(window)} tokens, but total fit is unknown. "
        )
        self.context_status.setText(
            f"AI context: {total - omitted} of {total} messages included; "
            f"{omitted} older messages omitted from model input. "
            "The full transcript is kept for viewing, saving and export. "
            "No summary model is needed. "
            + sizing
            + f"Input allowance: {self._input_budget()} estimated UTF-8 bytes including persona "
            "instructions, pinned details, approved summary and chat framing, "
            "not an exact token count or a fit guarantee."
            + (f" Additional context: {extra_bytes} bytes "
               "(shown below, including separator; included in allowance)." if extra else "")
            + (f"\nAdditional context not loaded: {context_error}. "
               "No extra context is used; bounded direct chat remains available."
               if context_error else "")
            + (f"\n{failure}" if failure else "")
        )

    def _append_measurement(self):
        last = self._last_input_measurement
        if not last or not self.selected_contact or (
            self._profile_id, self.selected_contact.contact_id
        ) != last[:2]:
            return
        measurement = last[2]
        if measurement["exact"]:
            detail = (
                f" Last submitted input: Exact server-formatted input: "
                f"{measurement['count']} tokens (persona, additional context, "
                "chat template and special tokens included); "
                f"{reply_reserve(self.ai.context_for_role()[0])} tokens reserved for reply. "
                "A changed server/model may still reject input; no automatic retry."
            )
        else:
            detail = (
                f" Last submitted input: {measurement['count']} estimated bytes; "
                "exact tokenization unavailable."
            )
        self.context_status.setText(self.context_status.text() + detail)

    def _update_context_status(self) -> None:
        if self.selected_contact is None:
            self.context_status.clear()
            self.additional_context_preview.clear()
            self.additional_context_preview.hide()
            return
        history = self.contact_histories[self.selected_contact.contact_id]
        extra = self._extra_context()
        self.additional_context_preview.setPlainText(extra)
        self.additional_context_preview.setVisible(bool(extra))
        try:
            _, omitted = bounded_messages(
                messenger_system_prompt(self.selected_contact, self.account),
                history, self._input_budget(),
                extra,
            )
        except ValueError as exc:
            self.context_status.setText(
                f"Byte-estimate preview: {exc} The full transcript is kept. "
                "A supported single-model llama-server with a known/manual window "
                "will measure exact formatted tokens when you send; this preview "
                "does not prevent that measurement."
            )
            self._append_measurement()
            return
        self._show_context_status(omitted, len(history))
        self.context_status.setText(
            self.context_status.text()
            + " This is a byte-estimate preview; supported single-model llama-server "
            "input is measured with its template and tokenizer when you send."
        )
        self._append_measurement()

    def _extra_context(self):
        if not self._profile_id or self.selected_contact is None:
            return ""
        key = (self._profile_id, self.selected_contact.contact_id)
        if key not in self._additional_context:
            try:
                self._additional_context[key] = load_context(key[1], key[0])
            except (OSError, UnicodeError, ValueError) as exc:
                self._additional_context_errors[key] = str(exc)
                self._additional_context[key] = {"pins": "", "summary": ""}
        return additional_context(**self._additional_context[key])

    def _apply_additional_context(self, contact, profile_id, context):
        if self.account.active_profile_id != profile_id or self.client.is_busy:
            raise RuntimeError("The active fursona changed or a reply is pending. Reopen context.")
        bounded_messages(
            messenger_system_prompt(contact, self.account),
            [], self._input_budget(),
            additional_context(**context),
        )
        save_context(contact.contact_id, profile_id, context)
        key = (profile_id, contact.contact_id)
        self._additional_context[key] = dict(context)
        self._additional_context_errors.pop(key, None)
        self._update_context_status()

    def _edit_additional_context(self):
        self._sync_profile()
        contact = self.selected_contact
        if contact is None or not self._profile_id or self.client.is_busy:
            return
        self._extra_context()
        key = (self._profile_id, contact.contact_id)
        # Never overwrite an unreadable context file with an empty fallback.
        if key in self._additional_context_errors:
            QMessageBox.warning(self, "Additional context could not be read",
                                self._additional_context_errors[key])
            return
        history = self.contact_histories[contact.contact_id]
        try:
            _, omitted = bounded_messages(
                messenger_system_prompt(contact, self.account), history,
                self._input_budget(), self._extra_context(),
            )
            window, _ = self.ai.context_for_role("summary")
            budget = model_input_budget(window, self.context_budget.value())
            request = (*summary_messages(history, omitted, budget), budget)
        except ValueError as exc:
            request = str(exc)
        dialog = ConversationContextDialog(
            self, contact, self._profile_id, self._additional_context[key], request,
        )
        dialog.exec()
        dialog.deleteLater()

    def _set_provider_status(self, text: str, error: bool = False) -> None:
        self.provider_status.setText(text)
        color = "#a12b24" if error else "#416c35"
        self.provider_status.setStyleSheet(f"color: {color};")

    def _save_history(self, contact_id: str, profile_id: str | None = None) -> None:
        profile_id = profile_id or self._profile_id
        if not profile_id:
            return
        self._unsaved_conversations.add((profile_id, contact_id))
        errors = self._errors_by_profile[profile_id]
        if contact_id in self._blocked_saves_by_profile[profile_id]:
            self._update_history_status()
            return
        try:
            save_messenger_history(
                contact_id, self._histories_by_profile[profile_id][contact_id], profile_id
            )
        except (OSError, UnicodeError, ValueError) as exc:
            errors[contact_id] = str(exc)
        else:
            errors.pop(contact_id, None)
            self._unsaved_conversations.discard((profile_id, contact_id))
        self._update_history_status()

    def _retry_save_history(self) -> None:
        self._sync_profile()
        contact = self.selected_contact
        if contact is None or not self._profile_id or self.client.is_busy:
            return
        if contact.contact_id not in self.history_errors:
            return
        self._save_history(contact.contact_id)

    def _update_history_status(self) -> None:
        self.assign_legacy_button.hide()
        self.retry_save_button.hide()
        self.retry_save_button.setEnabled(False)
        if self.selected_contact is None:
            self.history_status.clear()
            return
        contact_id = self.selected_contact.contact_id
        if not self._profile_id:
            self.history_status.setText("Select a saved fursona before using Messenger.")
            return
        error = self.history_errors.get(contact_id)
        if error:
            if contact_id in self.blocked_history_saves:
                self.history_status.setText(
                    f"Saved conversation unavailable: {error} "
                    "The existing file was left unchanged; new messages for this "
                    "contact will not be saved."
                )
            else:
                self.history_status.setText(
                    f"Could not save conversation: {error} "
                    "The current conversation is still in this window, but its latest "
                    "messages are not saved. Fix the storage problem and choose Retry "
                    "saving, or send another message to try saving again."
                )
                self.retry_save_button.show()
                self.retry_save_button.setEnabled(not self.client.is_busy)
            self.history_status.setStyleSheet("color: #a12b24;")
        else:
            self.history_status.setText(
                "Conversation history is saved on this computer."
            )
            self.history_status.setStyleSheet("color: #416c35;")
        try:
            available = legacy_messenger_history_available(contact_id, self._profile_id)
        except (OSError, UnicodeError, ValueError) as exc:
            self.history_status.setText(
                self.history_status.text() + f"\nOlder chat ownership could not be read: {exc}. "
                "Its files were left unchanged."
            )
            return
        if available:
            self.history_status.setText(
                self.history_status.text() + "\nAn older chat has not been loaded into "
                "this conversation or sent to AI. Preview it read-only before confirming its owner; "
                "the original is preserved."
            )
            self.assign_legacy_button.show()
            self.assign_legacy_button.setEnabled(not self.client.is_busy)

    def _assign_legacy_history(self) -> None:
        self._sync_profile()
        contact = self.selected_contact
        profile = self.account.active_profile
        if contact is None or profile is None or self.client.is_busy:
            return
        try:
            messages = preview_legacy_messenger_history(contact.contact_id, profile.profile_id)
        except (OSError, UnicodeError, ValueError) as exc:
            QMessageBox.warning(
                self, "Older chat preview unavailable",
                f"{exc}\nIts files were left unchanged; ownership was not assigned.",
            )
            return
        preview = LegacyChatPreviewDialog(
            messages, contact.display_name, profile.fursona_name, self,
        )
        result = preview.exec()
        preview.deleteLater()
        if (
            result != QDialog.DialogCode.Accepted or self.client.is_busy
            or self.account.active_profile_id != profile.profile_id
        ):
            return
        answer = QMessageBox.question(
            self, "Assign older conversation",
            f"Assign the older conversation with {contact.display_name} to "
            f"{profile.fursona_name}? Only this fursona will be able to load it. "
            "The original file will be preserved, and existing chats will not be replaced.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if (
            answer != QMessageBox.StandardButton.Yes or self.client.is_busy
            or self.account.active_profile_id != profile.profile_id
        ):
            return
        try:
            if self.contact_histories[contact.contact_id]:
                raise ValueError("This fursona already has messages; they were not replaced.")
            assign_legacy_messenger_history(contact.contact_id, profile.profile_id)
            self.contact_histories[contact.contact_id] = load_messenger_history(
                contact.contact_id, profile.profile_id
            )
            self.history_errors.pop(contact.contact_id, None)
            self.blocked_history_saves.discard(contact.contact_id)
        except (OSError, UnicodeError, ValueError) as exc:
            QMessageBox.warning(self, "Older chat not assigned", str(exc))
        self._render_history()
        self._update_history_status()

    def confirm_close(self, action: str = "close Messenger") -> bool:
        """Preflight a close without cancelling work or discarding any history."""
        if self._close_preapproved:
            self._close_preapproved = False
            return True
        if not self._unsaved_conversations:
            return True
        profiles = {profile.profile_id: profile.fursona_name for profile in self.account.fursonas}
        contacts = {contact.contact_id: contact.display_name for contact in CONTACTS}
        chats = "\n".join(
            f"• {profiles.get(profile_id, profile_id)} — {contacts.get(contact_id, contact_id)}"
            for profile_id, contact_id in sorted(self._unsaved_conversations)
        )
        retryable = {
            key for key in self._unsaved_conversations
            if key[1] not in self._blocked_saves_by_profile[key[0]]
        }
        buttons = QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Discard
        can_retry = bool(retryable) and not self.client.is_busy
        if can_retry:
            buttons |= QMessageBox.StandardButton.Retry
        answer = QMessageBox.question(
            self,
            "Messenger has unsaved messages",
            f"These conversations have messages that are only in memory:\n{chats}\n\n"
            f"If you {action}, these unsaved messages will be lost. "
            "Cancel returns to Messenger; Discard continues without saving."
            + ("\nRetry saves all writable chats, including other fursonas' chats."
               if can_retry else "")
            + ("\nUnreadable transcripts will not be overwritten. Return to Messenger "
               "to review those chats."
               if len(retryable) != len(self._unsaved_conversations) else "")
            + ("\nA reply is still running. Return to Messenger and wait before retrying."
               if self.client.is_busy else ""),
            buttons,
            QMessageBox.StandardButton.Cancel,
        )
        if answer == QMessageBox.StandardButton.Discard:
            return True
        if answer == QMessageBox.StandardButton.Retry and can_retry:
            for profile_id, contact_id in sorted(retryable):
                self._save_history(contact_id, profile_id)
            if not self._unsaved_conversations:
                return True
            QMessageBox.warning(
                self, "Messages are still unsaved",
                "Some conversations could not be saved. Messenger has been kept open "
                "with all messages in memory. Fix the save problem and retry, or "
                "explicitly choose Discard when leaving.",
            )
        return False

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt event name
        if not self.confirm_close():
            event.ignore()
            return
        self.client.cancel()
        super().closeEvent(event)
