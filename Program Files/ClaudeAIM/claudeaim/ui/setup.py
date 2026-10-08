"""Setup window: models, context size, log-on options and Reset All."""
import shutil

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog, QFormLayout, QGroupBox,
                               QHBoxLayout, QLabel, QMessageBox, QPushButton, QScrollArea,
                               QSpinBox, QVBoxLayout, QWidget)

from .. import host, llm, paths
from .common import tiled_background

DEFAULT_CHOICE = "(default)"


class SetupWindow(host.HostedWindow, QDialog):
    reset_requested = Signal()

    def __init__(self, settings, contacts, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Setup")
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.settings = settings
        self.contacts = contacts
        tiled_background(self)
        self.resize(420, 520)

        try:
            self.models = [m for m in llm.list_models() if "embed" not in m]
            self.ollama_error = ""
        except Exception as e:
            self.models, self.ollama_error = [], str(e) or e.__class__.__name__

        root = QVBoxLayout(self)

        # Model -------------------------------------------------------------
        model_box = QGroupBox("Ollama")
        form = QFormLayout(model_box)
        self.default_model = QComboBox()
        self.default_model.setEditable(True)
        self.default_model.addItems(self.models)
        self.default_model.setCurrentText(settings["default_model"])
        form.addRow("Default model:", self.default_model)

        self.context_size = QSpinBox()
        self.context_size.setRange(1024, 262144)
        self.context_size.setSingleStep(1024)
        self.context_size.setValue(int(settings["context_size"]))
        self.context_size.setSuffix(" tokens")
        form.addRow("Context size:", self.context_size)

        self.model_info = QLabel()
        self.model_info.setWordWrap(True)
        form.addRow(self.model_info)
        self.default_model.currentTextChanged.connect(self._show_model_info)
        self._show_model_info(self.default_model.currentText())
        root.addWidget(model_box)

        # Per-buddy models --------------------------------------------------------
        buddy_box = QGroupBox("Buddy models")
        buddy_layout = QVBoxLayout(buddy_box)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QWidget()
        buddy_form = QFormLayout(inner)
        self.overrides = {}
        current = settings["model_overrides"]
        for c in contacts:
            combo = QComboBox()
            combo.addItem(DEFAULT_CHOICE)
            combo.addItems(self.models)
            combo.setCurrentText(current.get(c.id) or DEFAULT_CHOICE)
            buddy_form.addRow(c.screen_name + ":", combo)
            self.overrides[c.id] = combo
        if not contacts:
            buddy_form.addRow(QLabel("No buddies yet. Add some to the contacts folder."))
        scroll.setWidget(inner)
        buddy_layout.addWidget(scroll)
        root.addWidget(buddy_box, 1)

        # Options ----------------------------------------------------------------
        opts_box = QGroupBox("Options")
        opts = QVBoxLayout(opts_box)
        self.skip_dialup = QCheckBox("Skip the dial-up screen during log on")
        self.skip_dialup.setChecked(bool(settings["skip_dialup"]))
        self.auto_login = QCheckBox("Auto-login (skip the Sign On window)")
        self.auto_login.setChecked(bool(settings["auto_login"]))
        self.sounds = QCheckBox("Play sounds")
        self.sounds.setChecked(bool(settings["sounds"]))
        for box in (self.skip_dialup, self.auto_login, self.sounds):
            opts.addWidget(box)
        root.addWidget(opts_box)

        # Buttons --------------------------------------------------------------------
        buttons = QHBoxLayout()
        reset = QPushButton("Reset All...")
        reset.clicked.connect(self._reset_all)
        buttons.addWidget(reset)
        buttons.addStretch()
        ok = QPushButton("OK")
        ok.setDefault(True)
        ok.clicked.connect(self._ok)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        buttons.addWidget(ok)
        buttons.addWidget(cancel)
        root.addLayout(buttons)

    def _show_model_info(self, model):
        if self.ollama_error:
            self.model_info.setText(f"Couldn't reach Ollama: {self.ollama_error}")
            return
        try:
            max_ctx = llm.context_length(model) if model else None
        except Exception:
            max_ctx = None
        if max_ctx:
            self.context_size.setMaximum(max_ctx)
            self.model_info.setText(f"{model} supports up to {max_ctx:,} tokens. "
                                    "Bigger context sizes use more memory.")
        else:
            self.model_info.setText("")

    def _ok(self):
        overrides = {cid: combo.currentText() for cid, combo in self.overrides.items()
                     if combo.currentText() != DEFAULT_CHOICE}
        self.settings.update(
            default_model=self.default_model.currentText().strip() or "gemma3:4b",
            context_size=self.context_size.value(),
            model_overrides=overrides,
            skip_dialup=self.skip_dialup.isChecked(),
            auto_login=self.auto_login.isChecked(),
            sounds=self.sounds.isChecked(),
        )
        self.accept()

    def _reset_all(self):
        answer = host.warning(
            self, "Reset All",
            "This erases your screen name, settings, away message, buddy icon and every "
            "conversation. ClaudeAIM will restart.\n\nAre you sure?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer != QMessageBox.Yes:
            return
        shutil.rmtree(paths.DATA, ignore_errors=True)
        self.reject()
        self.reset_requested.emit()
