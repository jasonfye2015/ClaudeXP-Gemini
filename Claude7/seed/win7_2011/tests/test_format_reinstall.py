import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton  # noqa: E402

from win7_2011.win7sim import config  # noqa: E402
from win7_2011.win7sim.application import SimulationWindow  # noqa: E402
from win7_2011.win7sim.desktop import DesktopPage  # noqa: E402
from win7_2011.win7sim.identity import FursonaProfile, UserAccount  # noqa: E402


def sample_account() -> UserAccount:
    profile = FursonaProfile(
        fursona_name="Rook",
        species="red fox",
        pronouns="they/them",
        date_of_birth="1988-06-12",
    )
    return UserAccount(
        desktop_name="Test User",
        fursonas=[profile],
        active_profile_id=profile.profile_id,
    )


class FormatReinstallTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.qt_app = QApplication.instance() or QApplication([])

    def test_reset_removes_account_and_documents_but_preserves_installed_data(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "Storage"
            account_file = root / "System" / "account.json"
            personal_note = root / "UserData" / "Documents" / "journal" / "day.txt"
            sticky_note = root / "UserData" / "Sticky Notes" / "rook.json"
            saved_playlists = (
                root / "UserData" / "Media Player Playlists" / "rook.json"
            )
            messenger_history = root / "UserData" / "Messenger" / "morgan-vale.json"
            preserved_files = (
                root / "Media" / "TV" / "guide.json",
                root / "Media" / "Movies" / "film.mp4",
                root / "Media" / "Music" / "song.mp3",
                root / "ROMs" / "game.rom",
                root / "Models" / "local-model.gguf",
                root / "System" / "installed-settings.json",
                root / "UserData" / "keep-this.dat",
            )
            account_file.parent.mkdir(parents=True)
            account_file.write_text("account", encoding="utf-8")
            personal_note.parent.mkdir(parents=True)
            personal_note.write_text("personal history", encoding="utf-8")
            sticky_note.parent.mkdir(parents=True)
            sticky_note.write_text("saved notes", encoding="utf-8")
            saved_playlists.parent.mkdir(parents=True)
            saved_playlists.write_text("saved playlists", encoding="utf-8")
            messenger_history.parent.mkdir(parents=True)
            messenger_history.write_text("saved chat", encoding="utf-8")
            profile_image = root / "Profiles" / "profile-image.png"
            profile_image.parent.mkdir(parents=True)
            profile_image.write_text("user profile file", encoding="utf-8")
            for path in preserved_files:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("preinstalled content", encoding="utf-8")

            with (
                patch.object(config, "STORAGE_ROOT", root),
                patch.object(
                    config, "SCREEN_SAVER_SETTINGS_DIR",
                    root / "UserData" / "Screen Saver",
                ),
                patch.object(config, "USER_PROFILES", root / "Profiles"),
                patch.object(config, "USER_DOCUMENTS", root / "UserData" / "Documents"),
                patch.object(config, "MESSENGER_HISTORY", root / "UserData" / "Messenger"),
                patch.object(config, "STICKY_NOTES", root / "UserData" / "Sticky Notes"),
                patch.object(config, "MEDIA_PLAYLISTS", root / "UserData" / "Media Player Playlists"),
                patch.object(config, "ACCOUNT_FILE", account_file),
            ):
                config.reset_user_data()

            self.assertFalse(account_file.exists())
            self.assertTrue((root / "Profiles").is_dir())
            self.assertEqual(list((root / "Profiles").iterdir()), [])
            self.assertFalse(profile_image.exists())
            self.assertTrue((root / "UserData" / "Documents").is_dir())
            self.assertEqual(list((root / "UserData" / "Documents").iterdir()), [])
            self.assertTrue((root / "UserData" / "Sticky Notes").is_dir())
            self.assertEqual(list((root / "UserData" / "Sticky Notes").iterdir()), [])
            self.assertTrue((root / "UserData" / "Media Player Playlists").is_dir())
            self.assertEqual(
                list((root / "UserData" / "Media Player Playlists").iterdir()), []
            )
            self.assertFalse(messenger_history.exists())
            for path in preserved_files:
                with self.subTest(path=path):
                    self.assertEqual(path.read_text(encoding="utf-8"), "preinstalled content")

    def test_reset_refuses_documents_symlink_and_keeps_account(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "Storage"
            outside = Path(directory) / "outside"
            outside.mkdir()
            protected = outside / "keep.txt"
            protected.write_text("not user data", encoding="utf-8")
            documents = root / "UserData" / "Documents"
            documents.parent.mkdir(parents=True)
            documents.symlink_to(outside, target_is_directory=True)
            account_file = root / "System" / "account.json"
            account_file.parent.mkdir(parents=True)
            account_file.write_text("account", encoding="utf-8")

            with (
                patch.object(config, "STORAGE_ROOT", root),
                patch.object(
                    config, "SCREEN_SAVER_SETTINGS_DIR",
                    root / "UserData" / "Screen Saver",
                ),
                patch.object(config, "USER_PROFILES", root / "Profiles"),
                patch.object(config, "USER_DOCUMENTS", documents),
                patch.object(config, "STICKY_NOTES", root / "UserData" / "Sticky Notes"),
                patch.object(config, "MEDIA_PLAYLISTS", root / "UserData" / "Media Player Playlists"),
                patch.object(config, "ACCOUNT_FILE", account_file),
                self.assertRaises(OSError),
            ):
                config.reset_user_data()

            self.assertEqual(protected.read_text(encoding="utf-8"), "not user data")
            self.assertTrue(account_file.exists())

    def test_start_menu_offers_confirmed_format_action(self):
        desktop = DesktopPage(sample_account())
        button = desktop.findChild(QPushButton, "formatReinstallButton")
        self.assertIsNotNone(button)

        emitted = []
        desktop.formatReinstallRequested.connect(lambda: emitted.append(True))
        with patch(
            "win7_2011.win7sim.desktop.QMessageBox.exec",
            return_value=QMessageBox.StandardButton.Cancel,
        ):
            assert button is not None
            button.click()
        self.assertEqual(emitted, [])

        with patch(
            "win7_2011.win7sim.desktop.QMessageBox.exec",
            return_value=QMessageBox.StandardButton.Yes,
        ):
            button.click()
        self.assertEqual(emitted, [True])
        desktop.deleteLater()

    def test_format_confirmation_says_messenger_conversations_will_be_erased(self):
        desktop = DesktopPage(sample_account())
        captured = []

        def inspect_dialog(dialog):
            captured.append((dialog.text(), dialog.informativeText()))
            self.assertEqual(
                dialog.defaultButton(), dialog.button(QMessageBox.StandardButton.Cancel)
            )
            return QMessageBox.StandardButton.Cancel

        with patch(
            "win7_2011.win7sim.desktop.QMessageBox.exec",
            new=inspect_dialog,
        ):
            desktop._confirm_format_reinstall()

        self.assertTrue(any("Messenger conversations" in text for text, _ in captured))
        self.assertTrue(any("will be erased" in details for _, details in captured))
        details = captured[0][1]
        for instruction in (
            "choose Cancel", "Windows Live Messenger", "Export all saved chats…",
            "for each fursona", "Export saved conversation…", "Sticky Notes",
            "Media Player Playlists",
            "outside Storage",
            "real computer", "another drive",
        ):
            with self.subTest(instruction=instruction):
                self.assertIn(instruction, details)
        desktop.close()
        desktop.deleteLater()

    def test_cancel_preserves_saved_files_and_allows_return_to_messenger(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "Storage"
            account_file = root / "System" / "account.json"
            documents = root / "UserData" / "Documents"
            histories = root / "UserData" / "Messenger"
            sticky_notes = root / "UserData" / "Sticky Notes"
            saved_playlists = root / "UserData" / "Media Player Playlists"
            files = {
                account_file: b"account",
                documents / "note.txt": b"personal note",
                sticky_notes / "rook.json": b"notes",
                saved_playlists / "rook.json": b"playlist",
                histories / "saved-chat.json": b"saved conversation",
            }
            for path, content in files.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)

            with (
                patch.object(config, "STORAGE_ROOT", root),
                patch.object(
                    config, "SCREEN_SAVER_SETTINGS_DIR",
                    root / "UserData" / "Screen Saver",
                ),
                patch.object(config, "ACCOUNT_FILE", account_file),
                patch.object(config, "USER_PROFILES", root / "Profiles"),
                patch.object(config, "USER_DOCUMENTS", documents),
                patch.object(config, "MESSENGER_HISTORY", histories),
                patch.object(config, "STICKY_NOTES", sticky_notes),
                patch.object(config, "MEDIA_PLAYLISTS", saved_playlists),
                patch("win7_2011.win7sim.desktop.USER_DOCUMENTS", documents),
                patch(
                    "win7_2011.win7sim.desktop.QMessageBox.exec",
                    return_value=QMessageBox.StandardButton.Cancel,
                ),
                patch(
                    "win7_2011.win7sim.application.reset_user_data",
                    wraps=config.reset_user_data,
                ) as reset,
            ):
                desktop = DesktopPage(sample_account())
                self.addCleanup(desktop.deleteLater)
                self.addCleanup(desktop.close)
                self.addCleanup(desktop.stop_session)
                controller = SimpleNamespace(
                    account=desktop.account,
                    _begin_shutdown=Mock(),
                    _show_error=Mock(),
                )
                desktop.formatReinstallRequested.connect(
                    lambda: SimulationWindow._format_and_reinstall(controller)
                )
                desktop._confirm_format_reinstall()
                reset.assert_not_called()
                controller._begin_shutdown.assert_not_called()
                self.assertIs(controller.account, desktop.account)
                for path, content in files.items():
                    self.assertEqual(path.read_bytes(), content)

                desktop.open_messenger()
                messenger = desktop._windows["messenger"].widget()
                self.assertTrue(messenger.export_all_button.isEnabled())
                self.assertEqual(messenger.export_all_button.text(), "Export all saved chats…")
                self.assertEqual(
                    messenger.export_history_button.text(), "Export saved conversation…"
                )

    def test_recovery_warning_points_to_exports_without_resetting_on_no(self):
        controller = SimpleNamespace(
            account=sample_account(), _stage="shutdown", _restart_pc=Mock()
        )
        with (
            patch("win7_2011.win7sim.application.reset_user_data") as reset,
            patch(
                "win7_2011.win7sim.application.QMessageBox.question",
                return_value=QMessageBox.StandardButton.No,
            ) as question,
        ):
            SimulationWindow._enter_recovery_mode(controller)
        reset.assert_not_called()
        controller._restart_pc.assert_not_called()
        self.assertIsNotNone(controller.account)
        warning = question.call_args.args[2]
        for instruction in (
            "choose No", "Restart PC", "Windows Live Messenger",
            "Export all saved chats…", "Export saved conversation…",
            "Sticky Notes", "Media Player Playlists", "outside Storage",
            "real computer", "another drive",
        ):
            with self.subTest(instruction=instruction):
                self.assertIn(instruction, warning)


if __name__ == "__main__":
    unittest.main()
