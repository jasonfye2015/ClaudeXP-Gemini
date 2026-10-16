"""Pieces shared by Setup ('Who will use this computer?') and Control Panel > User Accounts: the account-picture
picker, the online-name form (use your Windows name or a separate handle, for every account, with automatic
sign-in) and the optional-password form."""
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QButtonGroup, QCheckBox, QGridLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
                               QRadioButton, QVBoxLayout, QWidget)

from . import user

PRETEND_NOTE = ("These are pretend accounts that never leave this computer. Don't use a password you use for "
                "anything real.")


class PicturePicker(QListWidget):
    def __init__(self, icon_size=48):
        super().__init__()
        self.setViewMode(QListWidget.IconMode)
        self.setIconSize(QSize(icon_size, icon_size))
        self.setGridSize(QSize(icon_size + 14, icon_size + 14))
        self.setMovement(QListWidget.Static)
        self.setResizeMode(QListWidget.Adjust)
        self.setFlow(QListWidget.LeftToRight)
        for pic_id, label, pm in user.pictures():
            item = QListWidgetItem(QIcon(pm), "")
            item.setToolTip(label)
            item.setData(Qt.UserRole, pic_id)
            self.addItem(item)

    def select(self, pic_id):
        for i in range(self.count()):
            if self.item(i).data(Qt.UserRole) == pic_id:
                self.setCurrentRow(i)
                return

    def selected(self):
        item = self.currentItem()
        return item.data(Qt.UserRole) if item else None


class OnlineNameForm(QWidget):
    """'Your online name': the same as your Windows name, or a separate handle; used everywhere or not."""
    changed = Signal()

    def __init__(self, windows_name=lambda: ""):
        super().__init__()
        self.windows_name = windows_name
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        group = QButtonGroup(self)
        self.same = QRadioButton("Use my Windows name online")
        self.other = QRadioButton("Use a different online name (a screen name):")
        self.same.setChecked(True)
        for r in (self.same, self.other):
            group.addButton(r)
            v.addWidget(r)
        self.handle = QLineEdit()
        self.handle.setMaxLength(20)
        self.handle.setFixedWidth(260)
        self.handle.setContentsMargins(22, 0, 0, 0)
        v.addWidget(self.handle)
        v.addSpacing(6)
        self.link = QCheckBox("Use this name for all my online accounts (America Online, AIM, IRC, the MUCK,\n"
                              "e-mail and the Zone) and sign me in automatically")
        self.link.setChecked(True)
        v.addWidget(self.link)
        self.preview = QLabel()
        self.preview.setWordWrap(True)
        self.preview.setContentsMargins(22, 2, 0, 0)
        v.addWidget(self.preview)
        v.addStretch()
        for sig in (self.same.toggled, self.link.toggled):
            sig.connect(self._refresh)
        self.handle.textChanged.connect(self._refresh)
        self._refresh()

    def set_values(self, handle, linked, same=None):
        if same is None:
            same = handle.strip() == self.windows_name().strip()
        (self.same if same else self.other).setChecked(True)
        self.handle.setText("" if same else handle)
        self.link.setChecked(linked)
        self._refresh()

    def value(self):
        return self.windows_name().strip() if self.same.isChecked() else self.handle.text().strip()

    def linked(self):
        return self.link.isChecked()

    def is_same(self):
        return self.same.isChecked()

    def valid(self):
        return bool(self.value())

    def _refresh(self, *_):
        self.handle.setEnabled(self.other.isChecked())
        h = self.value()
        if not h:
            self.preview.setText("")
        elif self.link.isChecked():
            self.preview.setText(f"You'll be <b>{user.aim_name(h)}</b> on AIM and America Online, "
                                 f"<b>{user.irc_nick(h)}</b> on IRC, <b>{user.muck_name(h)}</b> on the MUCK, "
                                 f"and <b>{user.email_address(h)}</b> for e-mail.")
        else:
            self.preview.setText("Each program will ask for its own name and password, as it does now.")
        self.changed.emit()


class PasswordForm(QWidget):
    """An optional password: 'Don't use a ... password', or a password typed twice."""
    changed = Signal()

    def __init__(self, title, none_text, has_password=False):
        super().__init__()
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        head = QLabel(f"<b>{title}</b>")
        v.addWidget(head)
        self.none = QCheckBox(none_text)
        self.none.setChecked(not has_password)
        v.addWidget(self.none)
        grid = QGridLayout()
        grid.setContentsMargins(22, 0, 0, 0)
        self.pw = QLineEdit()
        self.confirm = QLineEdit()
        for row, (label, edit) in enumerate((("Password:", self.pw), ("Confirm:", self.confirm))):
            edit.setEchoMode(QLineEdit.Password)
            edit.setFixedWidth(200)
            edit.textChanged.connect(self._refresh)
            grid.addWidget(QLabel(label), row, 0)
            grid.addWidget(edit, row, 1)
        self.mismatch = QLabel("")
        grid.addWidget(self.mismatch, 2, 1)
        grid.setColumnStretch(2, 1)
        v.addLayout(grid)
        self.none.toggled.connect(self._refresh)
        self._refresh()

    def value(self):
        """None for no password."""
        return None if self.none.isChecked() else self.pw.text()

    def valid(self):
        return self.none.isChecked() or (bool(self.pw.text()) and self.pw.text() == self.confirm.text())

    def _refresh(self, *_):
        on = not self.none.isChecked()
        self.pw.setEnabled(on)
        self.confirm.setEnabled(on)
        if on and self.confirm.text() and self.pw.text() != self.confirm.text():
            self.mismatch.setText("The passwords don't match.")
        else:
            self.mismatch.setText("")
        self.changed.emit()
