"""Read-only import preview and explicit ownership/conflict confirmation."""

from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QLabel, QListWidget,
    QSplitter, QTextEdit, QVBoxLayout,
)


class MessengerImportDialog(QDialog):
    def __init__(self, exported: dict, profile_name: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Preview Messenger import")
        self.resize(760, 540)
        self.exported = exported
        layout = QVBoxLayout(self)
        source_owner = exported.get("profile_id", "unknown (older export)")
        notice = QLabel(
            f"Export owner ID: {source_owner}\n"
            f"Import into: {profile_name}\n"
            "Confirm that these chats belong to this fursona. Other fursonas will not be changed."
        )
        notice.setWordWrap(True)
        layout.addWidget(notice)
        count = sum(len(chat["messages"]) for chat in exported["conversations"])
        layout.addWidget(QLabel(
            f"{len(exported['conversations'])} contact(s), {count} message(s). "
            "Select each contact to read its messages before importing."
        ))
        body = QSplitter()
        self.contacts = QListWidget()
        self.messages = QTextEdit()
        self.messages.setReadOnly(True)
        for chat in exported["conversations"]:
            self.contacts.addItem(
                f"{chat['display_name']} ({chat['contact_id']}) — {len(chat['messages'])} messages"
            )
        self.contacts.currentRowChanged.connect(self._show_messages)
        body.addWidget(self.contacts)
        body.addWidget(self.messages)
        layout.addWidget(body, 1)
        layout.addWidget(QLabel("If a matching conversation already exists:"))
        self.policy = QComboBox()
        self.policy.addItem("Keep existing chats; import only missing chats", "skip")
        self.policy.addItem("Append imported messages after existing messages (may duplicate chats)", "append")
        self.policy.addItem("Replace matching chats with the export (deletes their current messages)", "replace")
        layout.addWidget(self.policy)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Confirm owner and import")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.contacts.setCurrentRow(0)

    def _show_messages(self, row: int) -> None:
        if row < 0:
            self.messages.clear()
            return
        chat = self.exported["conversations"][row]
        self.messages.setPlainText("\n\n".join(
            f"{message['role']}:\n{message['content']}" for message in chat["messages"]
        ))
