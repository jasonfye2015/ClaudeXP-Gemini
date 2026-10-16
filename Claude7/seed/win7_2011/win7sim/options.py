from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QSpinBox, QTabWidget,
    QScrollArea, QVBoxLayout, QWidget,
)

from .ai_settings import AISettings, ROLE_LABELS, BACKEND_LABELS, normalize_endpoint
from .config import STORAGE_ROOT
from .screensaver import IdleScreenSaverController, ScreenSaverSettingsPage


class APIKeyDialog(QDialog):
    """Never loads the existing key into a widget."""

    def __init__(self, ai, backend, endpoint, parent=None):
        super().__init__(parent)
        self.ai, self.backend, self.endpoint = ai, backend, endpoint
        self.setWindowTitle("Local server API key")
        self.resize(480, 240)
        layout = QVBoxLayout(self)
        info = QLabel(
            f"{BACKEND_LABELS[backend]}\n{endpoint}\n\n"
            "Saved keys are never displayed. Save replaces the key; Remove restores "
            "unauthenticated requests. Changes are immediate, not controlled by Apply. "
            "All roles using this server address share the same key."
        )
        info.setTextFormat(Qt.TextFormat.PlainText)
        info.setWordWrap(True)
        layout.addWidget(info)
        self.key_edit = QLineEdit()
        self.key_edit.setObjectName("aiApiKey")
        self.key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_edit.setMaxLength(2048)
        self.key_edit.setPlaceholderText("Enter a new API key (optional authentication)")
        layout.addWidget(self.key_edit)
        self.status = QLabel()
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        self.save_button = buttons.addButton("Save key", QDialogButtonBox.ButtonRole.ActionRole)
        self.remove_button = buttons.addButton("Remove saved key", QDialogButtonBox.ButtonRole.ActionRole)
        self.save_button.clicked.connect(lambda: self._update(False))
        self.remove_button.clicked.connect(lambda: self._update(True))
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.finished.connect(lambda _result: self.key_edit.clear())

    def _update(self, remove):
        try:
            self.ai.update_api_key(
                self.backend, self.endpoint, None if remove else self.key_edit.text()
            )
        except (ValueError, RuntimeError) as exc:
            self.status.setText(str(exc))
            return
        self.accept()


class OptionsWindow(QDialog):
    formatReinstallRequested = Signal()

    def __init__(
        self,
        ai_service,
        parent=None,
        screen_saver_controller: IdleScreenSaverController | None = None,
    ):
        super().__init__(parent)
        self.ai = ai_service
        self.setWindowTitle("Options")
        self.resize(680, 540)
        self.setMinimumSize(580, 480)
        root = QVBoxLayout(self)
        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)

        general = QWidget()
        layout = QVBoxLayout(general)
        layout.addWidget(QLabel("System recovery"))
        recovery = QLabel(
            "Format and Reinstall resets the user account, documents, and screen-saver preferences. "
            "Installed programs, models, media, and AI engine settings are preserved."
        )
        recovery.setWordWrap(True)
        layout.addWidget(recovery)
        format_button = QPushButton("Format and reinstall…")
        format_button.setObjectName("formatReinstallButton")
        format_button.clicked.connect(self.formatReinstallRequested.emit)
        layout.addWidget(format_button)
        layout.addStretch()
        self.tabs.addTab(general, "General")

        ai_page = QWidget()
        layout = QVBoxLayout(ai_page)
        engine = QGroupBox("Local engine")
        form = QFormLayout(engine)
        self.engine_label = QLabel(BACKEND_LABELS["llama_cpp"])
        self.engine_label.setObjectName("aiEngine")
        form.addRow("Local engine", self.engine_label)
        self.url_edit = QLineEdit(self.ai.settings.url)
        self.url_edit.setObjectName("aiEndpoint")
        self.key_buttons = []
        form.addRow("Server address", self._endpoint_controls(self.url_edit))
        credential_note = QLabel(
            "API keys are optional and saved only in Windows Credential Manager, "
            "never in connection profiles. Private-network HTTP sends keys without "
            "encryption; use HTTPS outside loopback."
        )
        credential_note.setWordWrap(True)
        form.addRow(credential_note)
        future = QLabel(
            "The app can start and stop a local llama-server using the "
            "executable and GGUF file below. It does not download either file. Existing "
            "servers are used as-is, and llama-server lists only models loaded at that endpoint. "
            "For auto-start, Direct conversations becomes the model alias; if blank, the "
            "GGUF filename (without .gguf) is used."
        )
        future.setWordWrap(True)
        form.addRow(future)

        self.llama_executable_edit = QLineEdit(self.ai.settings.llama_server_executable)
        self.llama_executable_edit.setObjectName("llamaServerExecutable")
        self.llama_executable_edit.setPlaceholderText(
            str(STORAGE_ROOT / "Runtime" / "llama.cpp" / "llama-server.exe")
        )
        executable_row = QWidget()
        executable_layout = QHBoxLayout(executable_row)
        executable_layout.setContentsMargins(0, 0, 0, 0)
        executable_layout.addWidget(self.llama_executable_edit, 1)
        self.llama_executable_browse = QPushButton("Browse…")
        self.llama_executable_browse.setObjectName("browseLlamaServer")
        self.llama_executable_browse.clicked.connect(self._browse_llama_executable)
        executable_layout.addWidget(self.llama_executable_browse)
        form.addRow("llama-server executable", executable_row)

        self.llama_model_edit = QLineEdit(self.ai.settings.llama_model_path)
        self.llama_model_edit.setObjectName("llamaModelFile")
        self.llama_model_edit.setPlaceholderText(
            str(STORAGE_ROOT / "Models" / "your-model.gguf")
        )
        model_row = QWidget()
        model_layout = QHBoxLayout(model_row)
        model_layout.setContentsMargins(0, 0, 0, 0)
        model_layout.addWidget(self.llama_model_edit, 1)
        self.llama_model_browse = QPushButton("Browse…")
        self.llama_model_browse.setObjectName("browseLlamaModel")
        self.llama_model_browse.clicked.connect(self._browse_llama_model)
        model_layout.addWidget(self.llama_model_browse)
        form.addRow("GGUF model file", model_row)

        self.llama_gpu_layers = QSpinBox()
        self.llama_gpu_layers.setObjectName("llamaGpuLayers")
        self.llama_gpu_layers.setRange(0, 999)
        self.llama_gpu_layers.setValue(self.ai.settings.llama_gpu_layers)
        self.llama_gpu_layers.setToolTip(
            "Layers to offload to the GPU. Use 0 for CPU-only; lower this if GPU memory is insufficient."
        )
        form.addRow("GPU layers (0 = CPU only)", self.llama_gpu_layers)
        self._llama_widgets = [
            self.llama_executable_edit, self.llama_executable_browse,
            self.llama_model_edit, self.llama_model_browse, self.llama_gpu_layers,
        ]
        layout.addWidget(engine)

        assignments = QGroupBox("Model assignments")
        form = QFormLayout(assignments)
        self.model_combos = {}
        self.role_url_edits = {}
        for role, label in ROLE_LABELS.items():
            combo = QComboBox()
            combo.setEditable(True)
            combo.setObjectName(f"aiModel-{role}")
            combo.lineEdit().setPlaceholderText("Select or enter an installed model name")
            combo.setEditText(self.ai.settings.models[role])
            form.addRow(label, combo)
            self.model_combos[role] = combo
            endpoint = QLineEdit(self.ai.settings.role_urls.get(role, ""))
            endpoint.setObjectName(f"aiEndpoint-{role}")
            endpoint.setPlaceholderText("Use the main server address (optional override)")
            form.addRow("  Server for this role", self._endpoint_controls(endpoint, role))
            self.role_url_edits[role] = endpoint
        note = QLabel(
            "The same model can serve every role. Blank roles stay unavailable. "
            "Only one generation runs at a time; direct chats have queue priority."
        )
        note.setWordWrap(True)
        form.addRow(note)
        layout.addWidget(assignments)
        row = QHBoxLayout()
        self.apply_button = QPushButton("Apply && Connect")
        self.apply_button.setObjectName("aiApply")
        self.test_button = QPushButton("Test saved connection / Refresh models")
        self.test_button.setObjectName("aiTest")
        self.test_button.setToolTip("Tests the saved endpoint, not unsaved edits.")
        row.addWidget(self.apply_button)
        row.addWidget(self.test_button)
        layout.addLayout(row)
        self.status_label = QLabel()
        self.status_label.setTextFormat(Qt.TextFormat.PlainText)
        self.status_label.setObjectName("aiConnectionStatus")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        layout.addStretch()
        ai_scroll = QScrollArea()
        ai_scroll.setWidgetResizable(True)
        ai_scroll.setWidget(ai_page)
        self.ai_tab_index = self.tabs.addTab(ai_scroll, "AI / Local Models")

        activity = QWidget()
        layout = QVBoxLayout(activity)
        self.activity_label = QLabel()
        self.activity_label.setWordWrap(True)
        layout.addWidget(self.activity_label)
        self.cancel_button = QPushButton("Cancel model work")
        self.cancel_button.setObjectName("aiCancel")
        self.cancel_button.clicked.connect(self.ai.cancel_all)
        layout.addWidget(self.cancel_button)
        self.reconnect_button = QPushButton("Reconnect saved servers")
        self.reconnect_button.setObjectName("aiReconnect")
        self.reconnect_button.setToolTip(
            "Refresh models at the saved server addresses after a restart. "
            "Does not apply unsaved edits or resend messages."
        )
        self.reconnect_button.clicked.connect(self._reconnect)
        layout.addWidget(self.reconnect_button)
        info = QLabel(
            "Actual engine errors are shown here, independently of simulated "
            "internet outages. After restarting a local server, reconnect here without "
            "editing settings. Failed or cancelled messages are not resent; send a new "
            "message yourself when ready. Reconnecting does not end simulated outages. "
            "Local games, media, and documents do not need an AI connection."
        )
        info.setWordWrap(True)
        layout.addWidget(info)
        layout.addStretch()
        self.tabs.addTab(activity, "Activity")

        if screen_saver_controller is not None:
            self.screen_saver_page = ScreenSaverSettingsPage(screen_saver_controller)
            self.tabs.addTab(self.screen_saver_page, "Screen Saver")

        close_buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close_buttons.rejected.connect(self.hide)
        root.addWidget(close_buttons)
        self.apply_button.clicked.connect(self._apply)
        self.test_button.clicked.connect(self._test)
        self.url_edit.textChanged.connect(lambda: self._models_changed([]))
        for edit in self.role_url_edits.values():
            edit.textChanged.connect(lambda: self._models_changed([]))
        self.ai.modelsChanged.connect(self._models_changed)
        self.ai.statusChanged.connect(self._status_changed)
        self.ai.changed.connect(self._refresh)
        self._models_changed(self.ai.available_models)
        self._status_changed(self.ai.status, self.ai.error)
        self._refresh()

    def _endpoint_controls(self, edit, role=None):
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(edit, 1)
        button = QPushButton("API key…")
        button.setObjectName(f"aiKey-{role or 'main'}")
        button.setToolTip("Save, replace, or remove a key for the current server address.")
        button.clicked.connect(lambda: self._edit_api_key(role))
        layout.addWidget(button)
        self.key_buttons.append(button)
        return row

    def _edit_api_key(self, role=None):
        try:
            endpoint = (
                self.role_url_edits[role].text().strip() if role is not None else ""
            ) or self.url_edit.text()
            endpoint = normalize_endpoint("llama_cpp", endpoint)
        except ValueError as exc:
            self._status_changed(str(exc), True)
            return
        dialog = APIKeyDialog(self.ai, "llama_cpp", endpoint, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._status_changed(
                "API key updated. Apply & Connect or test the saved connection to verify it.", False
            )
        dialog.deleteLater()

    def open_ai_tab(self):
        self.tabs.setCurrentIndex(self.ai_tab_index)
        self.show()
        self.raise_()
        self.activateWindow()

    def _apply(self):
        try:
            self.ai.apply(AISettings(
                url=self.url_edit.text(),
                models={role: combo.currentText() for role, combo in self.model_combos.items()},
                role_urls={role: edit.text() for role, edit in self.role_url_edits.items()},
                llama_server_executable=self.llama_executable_edit.text(),
                llama_model_path=self.llama_model_edit.text(),
                llama_gpu_layers=self.llama_gpu_layers.value(),
            ))
        except (OSError, ValueError, RuntimeError) as exc:
            self._status_changed(str(exc), True)

    def _test(self):
        try:
            self.ai.test_connection()
        except (ValueError, RuntimeError) as exc:
            self._status_changed(str(exc), True)

    def _reconnect(self):
        try:
            self.ai.reconnect()
        except (ValueError, RuntimeError) as exc:
            self._status_changed(str(exc), True)

    def _browse_llama_executable(self):
        filename, _filter = QFileDialog.getOpenFileName(
            self, "Choose llama-server executable",
            self.llama_executable_edit.text(),
            "llama-server executable (llama-server.exe);;All files (*)",
        )
        if filename:
            self.llama_executable_edit.setText(filename)

    def _browse_llama_model(self):
        filename, _filter = QFileDialog.getOpenFileName(
            self, "Choose a GGUF model file",
            self.llama_model_edit.text() or str(STORAGE_ROOT / "Models"),
            "GGUF models (*.gguf);;All files (*)",
        )
        if filename:
            self.llama_model_edit.setText(filename)

    def _models_changed(self, _models):
        for role, combo in self.model_combos.items():
            current = combo.currentText()
            models = []
            try:
                draft = AISettings(
                    url=self.url_edit.text(),
                    role_urls={role: self.role_url_edits[role].text()},
                ).validated()
                models = self.ai.models_by_url.get(draft.endpoint_for(role), [])
            except ValueError:
                pass
            combo.clear()
            combo.addItem("")
            combo.addItems(models)
            combo.setEditText(current)

    def _status_changed(self, text, error):
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: {'#a12b24' if error else '#416c35'};")

    def _refresh(self):
        busy = self.ai.is_busy
        self.apply_button.setEnabled(not busy)
        self.test_button.setEnabled(not busy)
        self.reconnect_button.setEnabled(self.ai.can_reconnect)
        self.cancel_button.setEnabled(busy)
        self.url_edit.setEnabled(not busy)
        llama_enabled = not busy
        for widget in self._llama_widgets:
            widget.setEnabled(llama_enabled)
        for button in self.key_buttons:
            button.setEnabled(not busy)
        for edit in self.role_url_edits.values():
            edit.setEnabled(not busy)
        for combo in self.model_combos.values():
            combo.setEnabled(not busy)
        assignments = "\n".join(
            f"{label}: {self.ai.settings.models[role] or '(not assigned)'}"
            for role, label in ROLE_LABELS.items()
        )
        self.activity_label.setText(
            f"{self.ai.status}\n\nWaiting jobs: {self.ai.queue_count}\n"
            f"Background work: {'paused' if self.ai.background_paused else 'available'}"
            f"\n\n{assignments}"
        )
