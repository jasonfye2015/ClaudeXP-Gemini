"""Isolated, read-only preview before claiming an older Messenger transcript."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QLabel, QTextEdit, QVBoxLayout,
)


class LegacyChatPreviewDialog(QDialog):
    def __init__(
        self, messages: list[dict[str, str]], contact_name: str,
        profile_name: str, parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Preview older chat — read-only")
        self.resize(700, 500)
        layout = QVBoxLayout(self)
        self.notice = QLabel(
            f"Older chat with {contact_name} — read-only preview\n"
            "These messages are not loaded into your conversation or sent to AI. "
            "The original file stays unchanged unless you confirm ownership.\n"
            f"Continue only if this chat belongs to {profile_name}. "
            "You will be asked to confirm before assigning it."
        )
        self.notice.setWordWrap(True)
        self.notice.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(self.notice)
        layout.addWidget(QLabel(f"{len(messages)} message(s)"))
        self.transcript = QTextEdit()
        self.transcript.setReadOnly(True)
        self.transcript.setAccessibleName("Read-only older chat preview")
        self.transcript.setPlainText("\n\n".join(
            f"{'Unknown owner' if message['role'] == 'user' else contact_name}:\n"
            f"{message['content']}" for message in messages
        ) if messages else "This older chat has no messages.")
        layout.addWidget(self.transcript, 1)
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        proceed = self.buttons.button(QDialogButtonBox.StandardButton.Ok)
        proceed.setText("Continue to ownership confirmation…")
        proceed.setAutoDefault(False)
        proceed.setDefault(False)
        cancel = self.buttons.button(QDialogButtonBox.StandardButton.Cancel)
        cancel.setDefault(True)
        cancel.setFocus()
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
