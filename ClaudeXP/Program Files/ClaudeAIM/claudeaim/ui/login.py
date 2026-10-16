"""Sign On window (Login.jpeg)."""
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QCheckBox, QLineEdit

from .. import host
from .common import ImageButton, ImageWindow

BG = "#b2b2b4"  # the grey of Login.jpeg
FIELD_STYLE = "QLineEdit { border: none; background: white; font: 11pt 'Arial'; padding-left: 3px; }"


class LoginWindow(ImageWindow):
    signed_on = Signal()
    help_requested = Signal()
    setup_requested = Signal()
    quit_requested = Signal()

    def __init__(self, settings):
        super().__init__("Login.jpeg", "Sign On", extra_height=45, bg=BG)
        self.settings = settings
        self.leaving = False

        self.screen_name = QLineEdit(self)
        self.screen_name.setGeometry(165, 360, 238, 40)
        self.screen_name.setStyleSheet(FIELD_STYLE)
        self.screen_name.setMaxLength(16)
        if settings["screen_name"]:
            self.screen_name.setText(settings["screen_name"])
            self.screen_name.setReadOnly(True)  # locked until "Reset All"
            self.screen_name.setToolTip("Your screen name is set. Use Setup > Reset All to start over.")

        self.password = QLineEdit(self)
        self.password.setGeometry(165, 416, 238, 34)
        self.password.setStyleSheet(FIELD_STYLE)
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setText(settings["password"])

        box_style = f"QCheckBox {{ background: {BG}; font: 10pt 'Arial'; }}"
        self.save_password = QCheckBox("Save password", self)
        self.save_password.setGeometry(10, 462, 200, 36)
        self.save_password.setStyleSheet(box_style)
        self.save_password.setChecked(bool(settings["save_password"]))

        self.auto_login = QCheckBox("Auto-login", self)
        self.auto_login.setGeometry(265, 462, 150, 36)
        self.auto_login.setStyleSheet(box_style)
        self.auto_login.setChecked(bool(settings["auto_login"]))

        self.help_btn = ImageButton("button_help.jpg", self, "Help")
        self.help_btn.move(18, 507)
        self.help_btn.clicked.connect(self.help_requested)

        self.setup_btn = ImageButton("button_setup.jpg", self, "Setup")
        self.setup_btn.move(85, 510)
        self.setup_btn.clicked.connect(self.setup_requested)

        self.signon_btn = ImageButton("button_signon.jpg", self, "Sign On")
        self.signon_btn.move(self.width() - 88 - 18, 508)
        self.signon_btn.clicked.connect(self._sign_on)

        self.screen_name.returnPressed.connect(self._sign_on)
        self.password.returnPressed.connect(self._sign_on)
        self.center_on_screen()

    def _sign_on(self):
        name = self.screen_name.text().strip()
        if not name:
            host.information(self, "Sign On", "Please enter a screen name.")
            return
        keep = self.save_password.isChecked()
        self.settings.update(
            screen_name=name,
            save_password=keep,
            password=self.password.text() if keep else "",
            auto_login=self.auto_login.isChecked(),
        )
        self.leaving = True
        self.close()
        self.signed_on.emit()

    def closeEvent(self, event):
        event.accept()
        if not self.leaving:
            self.quit_requested.emit()
