"""Conversation context storage and explicit review UI, separate from transcripts."""
from __future__ import annotations

import json

from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QPushButton, QTextEdit, QVBoxLayout,
)

from . import config
from .ai_service import AIChannel
from .messenger_context import additional_context, input_size


def _path(contact_id, profile_id):
    return config._messenger_history_path(contact_id, profile_id).with_suffix(".context.json")


def load_context(contact_id, profile_id):
    try:
        raw = json.loads(_path(contact_id, profile_id).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"pins": "", "summary": ""}
    if (
        not isinstance(raw, dict) or raw.get("version") != 1
        or raw.get("contact_id") != contact_id or raw.get("profile_id") != profile_id
        or not isinstance(raw.get("pins"), str) or not isinstance(raw.get("summary"), str)
    ):
        raise ValueError("Saved additional context has an invalid format.")
    return {key: raw[key] for key in ("pins", "summary")}


def save_context(contact_id, profile_id, context):
    if set(context) != {"pins", "summary"} or any(
        not isinstance(value, str) for value in context.values()
    ):
        raise ValueError("Additional context must contain plain-text pins and summary.")
    path = _path(contact_id, profile_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    config._atomic_write_private_json(path, json.dumps({
        "version": 1, "profile_id": profile_id, "contact_id": contact_id, **context,
    }, ensure_ascii=False, indent=2) + "\n")


class ConversationContextDialog(QDialog):
    """Generated summaries are drafts until the user explicitly saves them."""

    def __init__(self, messenger, contact, profile_id, context, summary_request):
        super().__init__(messenger)
        self.messenger = messenger
        self.contact = contact
        self.profile_id = profile_id
        self.summary_request = summary_request
        self.channel = AIChannel(messenger.ai, role="summary", parent=self)
        self.channel.responseFinished.connect(self._finished)
        self.setWindowTitle(f"Additional AI context — {contact.display_name}")
        self.resize(650, 650)
        layout = QVBoxLayout(self)
        note = QLabel(
            "Pins and approved summaries are saved for this fursona and contact, separately "
            "from the full transcript. They use the same direct-chat input budget. "
            "Edit or remove them below; nothing is applied until Save context. "
            "Transcript exports do not include these separate notes."
        )
        note.setWordWrap(True)
        layout.addWidget(note)
        layout.addWidget(QLabel("Pinned details (paste important details or older messages):"))
        self.pins = QTextEdit()
        self.pins.setPlainText(context["pins"])
        self.pins.setAccessibleName("Pinned conversation details")
        layout.addWidget(self.pins)
        layout.addWidget(QLabel("Summary draft — review for accuracy before saving:"))
        self.summary = QTextEdit()
        self.summary.setPlainText(context["summary"])
        self.summary.setAccessibleName("Reviewed conversation summary")
        layout.addWidget(self.summary)
        self.generate = QPushButton("Request optional summary")
        self.generate.clicked.connect(self._generate)
        self.generate.setEnabled(
            isinstance(summary_request, tuple) and messenger.ai.is_available("summary")
        )
        layout.addWidget(self.generate)
        self.status = QLabel()
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        layout.addWidget(QLabel("Exact additional text used in direct AI input after saving:"))
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        layout.addWidget(self.preview)
        if isinstance(summary_request, tuple):
            messages, first, end, budget = summary_request
            self.source = QTextEdit()
            self.source.setReadOnly(True)
            self.source.setPlainText("\n\n".join(
                f'{message["role"]}: {message["content"]}' for message in messages
            ))
            layout.addWidget(QLabel(
                f"Summary source: older messages {first + 1}–{end}; "
                f"{first} earlier messages excluded. "
                f"Input estimate {input_size(messages)} / {budget} bytes, including instructions. "
                "Source snapshot (not the whole transcript):"
            ))
            layout.addWidget(self.source)
        else:
            self.status.setText(str(summary_request))
        if not messenger.ai.is_available("summary"):
            self.status.setText(
                "Summary model unavailable. Pins and bounded direct chat remain usable."
            )
        buttons = QHBoxLayout()
        self.save = QPushButton("Save context")
        self.save.clicked.connect(self._save)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        buttons.addWidget(self.save)
        buttons.addWidget(cancel)
        layout.addLayout(buttons)
        self.pins.textChanged.connect(self._preview)
        self.summary.textChanged.connect(self._preview)
        self._preview()

    def context(self):
        return {"pins": self.pins.toPlainText(), "summary": self.summary.toPlainText()}

    def _preview(self):
        self.preview.setPlainText(additional_context(**self.context()))

    def _generate(self):
        if self.channel.is_busy or not isinstance(self.summary_request, tuple):
            return
        try:
            self.channel.send_chat(self.summary_request[0])
        except (ValueError, RuntimeError) as exc:
            self.status.setText(f"Summary not requested: {exc}. Direct chat remains usable.")
            return
        self.generate.setEnabled(False)
        self.save.setEnabled(False)
        self.status.setText("Requesting summary; existing pins, summary and transcript are unchanged.")

    def _finished(self, success, message):
        self.save.setEnabled(True)
        self.generate.setEnabled(self.messenger.ai.is_available("summary"))
        if success and message.strip():
            self.summary.setPlainText(message)
            self.status.setText("Summary draft received. Review and edit it, then Save context to use it.")
        else:
            self.status.setText(
                f"Summary failed: {message or 'Empty response'}. Existing context is unchanged. "
                "Direct chat remains usable; no message was resent."
            )

    def _save(self):
        if self.channel.is_busy:
            return
        try:
            self.messenger._apply_additional_context(
                self.contact, self.profile_id, self.context()
            )
        except (OSError, UnicodeError, ValueError, RuntimeError) as exc:
            self.status.setText(f"Context not saved: {exc}")
            return
        self.accept()

    def done(self, result):
        self.channel.cancel_chat()
        super().done(result)
