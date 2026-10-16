import json
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEvent, Qt  # noqa: E402
from PySide6.QtGui import QKeyEvent  # noqa: E402
from PySide6.QtWidgets import QApplication, QMessageBox  # noqa: E402

from win7_2011.win7sim import config  # noqa: E402
from win7_2011.win7sim.application import SimulationWindow  # noqa: E402
from win7_2011.win7sim.screens import BiosScreen  # noqa: E402
from win7_2011.win7sim.screens import WindowsStartScreen  # noqa: E402


class BiosPasswordTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.qt_app = QApplication.instance() or QApplication([])

    def test_password_hashes_are_salted_private_and_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            password_file = Path(directory) / "System" / "bios-passwords.json"
            with (
                patch.object(config, "BIOS_PASSWORDS_FILE", password_file),
                patch.object(config, "BIOS_PASSWORD_HASH_ITERATIONS", 100),
            ):
                first_hash = config.hash_bios_password("private-passphrase")
                second_hash = config.hash_bios_password("private-passphrase")
                self.assertNotEqual(first_hash, second_hash)
                self.assertTrue(
                    config.verify_bios_password("private-passphrase", first_hash)
                )
                self.assertFalse(config.verify_bios_password("wrong", first_hash))

                config.save_bios_password_hashes({"user": first_hash})
                stored_text = password_file.read_text(encoding="utf-8")
                backup_file = password_file.with_name("bios-passwords.backup.json")
                backup_text = backup_file.read_text(encoding="utf-8")
                self.assertNotIn("private-passphrase", stored_text)
                self.assertNotIn("private-passphrase", backup_text)
                self.assertEqual(
                    config.load_bios_password_hashes(),
                    {"user": first_hash},
                )
                self.assertEqual(
                    stat.S_IMODE(password_file.stat().st_mode),
                    0o600,
                )
                self.assertEqual(
                    stat.S_IMODE(backup_file.stat().st_mode),
                    0o600,
                )

    def test_password_page_sets_and_clears_user_password(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            password_file = Path(directory) / "System" / "bios-passwords.json"
            screen = BiosScreen(auto_start=False)
            screen._setup_page = "password"

            with (
                patch.object(config, "BIOS_PASSWORDS_FILE", password_file),
                patch.object(config, "BIOS_PASSWORD_HASH_ITERATIONS", 100),
                patch(
                    "win7_2011.win7sim.screens.QInputDialog.getText",
                    side_effect=[
                        ("supervisor-secret", True),
                        ("supervisor-secret", True),
                        ("user-secret", True),
                        ("user-secret", True),
                    ],
                ),
            ):
                screen._setup_page_item = 0
                screen._set_bios_password("supervisor")
                saved = config.load_bios_password_hashes()
                self.assertTrue(
                    config.verify_bios_password(
                        "supervisor-secret", saved["supervisor"]
                    )
                )

                screen._setup_page_item = 1
                screen._set_bios_password("user")
                saved = config.load_bios_password_hashes()
                self.assertIn("user", saved)
                self.assertTrue(
                    config.verify_bios_password("user-secret", saved["user"])
                )
                self.assertEqual(screen._setup_values["password"], [1, 1])

                with patch(
                    "win7_2011.win7sim.screens.QMessageBox.question",
                    side_effect=[
                        QMessageBox.StandardButton.Yes,
                        QMessageBox.StandardButton.Yes,
                    ],
                ):
                    screen._clear_bios_password("user")
                    self.assertIn("supervisor", config.load_bios_password_hashes())
                    self.assertEqual(screen._setup_values["password"], [1, 0])
                    screen._clear_bios_password("supervisor")

                self.assertEqual(config.load_bios_password_hashes(), {})
                self.assertEqual(screen._setup_values["password"], [0, 0])
            screen.close()
            screen.deleteLater()

    def test_supervisor_setup_and_user_startup_require_their_passwords(self) -> None:
        with patch.object(config, "BIOS_PASSWORD_HASH_ITERATIONS", 100):
            supervisor_hash = config.hash_bios_password("supervisor-secret")
            user_hash = config.hash_bios_password("user-secret")
        screen = BiosScreen(
            auto_start=False,
            password_hashes={
                "supervisor": supervisor_hash,
                "user": user_hash,
            },
        )

        with (
            patch.object(config, "BIOS_PASSWORD_HASH_ITERATIONS", 100),
            patch(
                "win7_2011.win7sim.screens.QInputDialog.getText",
                side_effect=[
                    ("wrong", True),
                    ("supervisor-secret", True),
                    ("wrong", True),
                    ("user-secret", True),
                ],
            ) as prompt,
        ):
            wrong_setup = QKeyEvent(
                QEvent.Type.KeyPress,
                Qt.Key.Key_Delete,
                Qt.KeyboardModifier.NoModifier,
            )
            screen.keyPressEvent(wrong_setup)
            self.assertFalse(screen.setup_open)
            self.assertIn("supervisor password", screen._setup_status.lower())

            correct_setup = QKeyEvent(
                QEvent.Type.KeyPress,
                Qt.Key.Key_Delete,
                Qt.KeyboardModifier.NoModifier,
            )
            screen.keyPressEvent(correct_setup)
            self.assertTrue(screen.setup_open)

            self.assertFalse(screen.authorize_startup())
            self.assertTrue(screen.authorize_startup())

        self.assertEqual(prompt.call_count, 4)
        screen.close()
        screen.deleteLater()

    def test_password_hash_file_rejects_unknown_roles_and_bad_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            password_file = Path(directory) / "bios-passwords.json"
            with patch.object(config, "BIOS_PASSWORDS_FILE", password_file):
                password_file.write_text(
                    json.dumps({"administrator": "not-a-hash"}),
                    encoding="utf-8",
                )
                with self.assertRaises(ValueError):
                    config.load_bios_password_hashes()

                password_file.write_text(
                    json.dumps({"user": "pbkdf2_sha256$999999999$00$00"}),
                    encoding="utf-8",
                )
                with self.assertRaises(ValueError):
                    config.load_bios_password_hashes()

    def test_corrupt_primary_uses_validated_backup_for_normal_password_checks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            password_file = Path(directory) / "bios-passwords.json"
            backup_file = password_file.with_name("bios-passwords.backup.json")
            with (
                patch.object(config, "BIOS_PASSWORDS_FILE", password_file),
                patch.object(config, "BIOS_PASSWORD_HASH_ITERATIONS", 100),
            ):
                hashes = {
                    "supervisor": config.hash_bios_password("supervisor-secret"),
                    "user": config.hash_bios_password("user-secret"),
                }
                config.save_bios_password_hashes(hashes)
                password_file.write_text("{ damaged", encoding="utf-8")

                loaded, recovery_status = (
                    config.load_bios_password_hashes_with_status()
                )
                self.assertEqual(loaded, hashes)
                self.assertEqual(
                    recovery_status,
                    "BIOS password backup recovery used; main file repaired.",
                )
                self.assertEqual(
                    json.loads(password_file.read_text(encoding="utf-8")),
                    hashes,
                )
                self.assertEqual(config.load_bios_password_hashes(), hashes)
                screen = BiosScreen(
                    auto_start=False,
                    password_hashes=loaded,
                    recovery_status=recovery_status,
                )
                self.assertIn("backup recovery used", screen._setup_status.lower())
                screen._setup_page = "password"
                with (
                    patch.object(config, "BIOS_PASSWORD_HASH_ITERATIONS", 100),
                    patch(
                        "win7_2011.win7sim.screens.QInputDialog.getText",
                        side_effect=[
                            ("supervisor-secret", True),
                            ("user-secret", True),
                        ],
                    ),
                ):
                    self.assertTrue(screen._request_setup_password(hashes["supervisor"]))
                    self.assertTrue(screen.authorize_startup())
                screen.close()
                screen.deleteLater()
                self.assertTrue(backup_file.exists())

    def test_backup_remains_usable_when_primary_repair_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            password_file = Path(directory) / "bios-passwords.json"
            backup_file = password_file.with_name("bios-passwords.backup.json")
            with (
                patch.object(config, "BIOS_PASSWORDS_FILE", password_file),
                patch.object(config, "BIOS_PASSWORD_HASH_ITERATIONS", 100),
            ):
                hashes = {
                    "supervisor": config.hash_bios_password("supervisor-secret"),
                    "user": config.hash_bios_password("user-secret"),
                }
                config.save_bios_password_hashes(hashes)
                password_file.write_text("{ damaged", encoding="utf-8")

                with patch.object(
                    config,
                    "_atomic_write_private_json",
                    side_effect=OSError("storage is read-only"),
                ):
                    loaded, recovery_status = (
                        config.load_bios_password_hashes_with_status()
                    )

                self.assertEqual(loaded, hashes)
                self.assertIn("backup recovery used", recovery_status)
                self.assertIn("repair failed", recovery_status)
                self.assertEqual(
                    password_file.read_text(encoding="utf-8"),
                    "{ damaged",
                )
                self.assertEqual(
                    json.loads(backup_file.read_text(encoding="utf-8")),
                    hashes,
                )

                screen = BiosScreen(
                    auto_start=False,
                    password_hashes=loaded,
                    recovery_status=recovery_status,
                )
                screen._setup_page = "password"
                with patch(
                    "win7_2011.win7sim.screens.QInputDialog.getText",
                    side_effect=[
                        ("supervisor-secret", True),
                        ("user-secret", True),
                    ],
                ):
                    self.assertTrue(
                        screen._request_setup_password(hashes["supervisor"])
                    )
                    self.assertTrue(screen.authorize_startup())
                screen.close()
                screen.deleteLater()

    def test_password_save_failures_around_each_replacement_keep_a_valid_copy(self) -> None:
        class SimulatedPowerLoss(BaseException):
            pass

        original_replace = Path.replace
        replacement_cases = (
            ("before", "bios-passwords.backup.json", "old", OSError),
            ("after", "bios-passwords.backup.json", "old", OSError),
            ("before", "bios-passwords.json", "old", OSError),
            ("after", "bios-passwords.json", "new", OSError),
            (
                "after",
                "bios-passwords.backup.json",
                "old",
                SimulatedPowerLoss,
            ),
        )

        for timing, target_name, expected, exception_type in replacement_cases:
            with self.subTest(timing=timing, target=target_name):
                with tempfile.TemporaryDirectory() as directory:
                    password_file = Path(directory) / "bios-passwords.json"
                    backup_file = password_file.with_name(
                        "bios-passwords.backup.json"
                    )
                    old_plaintext = "previous-private-password"
                    new_plaintext = "replacement-private-password"
                    with (
                        patch.object(config, "BIOS_PASSWORDS_FILE", password_file),
                        patch.object(config, "BIOS_PASSWORD_HASH_ITERATIONS", 100),
                    ):
                        old_hashes = {
                            "user": config.hash_bios_password(old_plaintext)
                        }
                        new_hashes = {
                            "user": config.hash_bios_password(new_plaintext)
                        }
                        config.save_bios_password_hashes(old_hashes)

                        def fail_at_replacement(source: Path, target: Path) -> Path:
                            if target.name == target_name:
                                if timing == "before":
                                    raise exception_type("injected save interruption")
                                original_replace(source, target)
                                raise exception_type("injected save interruption")
                            return original_replace(source, target)

                        with patch.object(Path, "replace", fail_at_replacement):
                            with self.assertRaises(exception_type):
                                config.save_bios_password_hashes(new_hashes)

                        self.assertEqual(
                            config.load_bios_password_hashes(),
                            old_hashes if expected == "old" else new_hashes,
                        )
                        self.assertEqual(
                            json.loads(password_file.read_text(encoding="utf-8")),
                            old_hashes if expected == "old" else new_hashes,
                        )
                        backup_contents = json.loads(
                            backup_file.read_text(encoding="utf-8")
                        )
                        self.assertEqual(
                            backup_contents,
                            old_hashes
                            if timing == "before"
                            and target_name == "bios-passwords.backup.json"
                            else new_hashes,
                        )
                        for credential_file in (password_file, backup_file):
                            stored_text = credential_file.read_text(encoding="utf-8")
                            self.assertNotIn(old_plaintext, stored_text)
                            self.assertNotIn(new_plaintext, stored_text)

    def test_missing_or_invalid_password_copies_remain_locked_with_clear_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            password_file = Path(directory) / "bios-passwords.json"
            backup_file = password_file.with_name("bios-passwords.backup.json")
            with patch.object(config, "BIOS_PASSWORDS_FILE", password_file):
                password_file.write_text("{ damaged", encoding="utf-8")
                backup_file.write_text(
                    json.dumps({"user": "not-a-valid-hash"}),
                    encoding="utf-8",
                )
                with self.assertRaisesRegex(ValueError, "Neither.*backup"):
                    config.load_bios_password_hashes()

                screen = BiosScreen(auto_start=False, passwords_available=False)
                event = QKeyEvent(
                    QEvent.Type.KeyPress,
                    Qt.Key.Key_F8,
                    Qt.KeyboardModifier.NoModifier,
                )
                screen.keyPressEvent(event)
                self.assertIn("restore a valid password file", screen._setup_status.lower())
                self.assertIn("remain locked", screen._setup_status.lower())
                screen.close()
                screen.deleteLater()

    def test_unreadable_password_settings_fail_closed(self) -> None:
        screen = BiosScreen(auto_start=False, passwords_available=False)
        event = QKeyEvent(
            QEvent.Type.KeyPress,
            Qt.Key.Key_Delete,
            Qt.KeyboardModifier.NoModifier,
        )
        screen.keyPressEvent(event)
        self.assertFalse(screen.setup_open)
        self.assertIn("could be verified", screen._setup_status.lower())
        self.assertFalse(screen.authorize_startup())
        with (
            patch(
                "win7_2011.win7sim.screens.QInputDialog.getItem"
            ) as recovery_selection,
            patch(
                "win7_2011.win7sim.screens.QMessageBox.question"
            ) as recovery_confirmation,
        ):
            event = QKeyEvent(
                QEvent.Type.KeyPress,
                Qt.Key.Key_F8,
                Qt.KeyboardModifier.NoModifier,
            )
            screen.keyPressEvent(event)
        recovery_selection.assert_not_called()
        recovery_confirmation.assert_not_called()
        self.assertIn("recovery unavailable", screen._setup_status.lower())
        screen.close()
        screen.deleteLater()

    def test_post_recovery_removes_only_selected_password_and_resets_settings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            storage = Path(directory) / "System"
            password_file = storage / "bios-passwords.json"
            settings_file = storage / "bios.json"
            settings = {
                "standard": [1, 1, 0, 0, 0, 0, 0],
                "advanced": [0, 0, 0, 1, 0],
            }
            with (
                patch.object(config, "BIOS_PASSWORDS_FILE", password_file),
                patch.object(config, "BIOS_SETTINGS_FILE", settings_file),
                patch.object(config, "BIOS_PASSWORD_HASH_ITERATIONS", 100),
            ):
                hashes = {
                    "supervisor": config.hash_bios_password("supervisor-secret"),
                    "user": config.hash_bios_password("user-secret"),
                }
                config.save_bios_password_hashes(hashes)
                config.save_bios_settings(settings)
                screen = BiosScreen(
                    auto_start=False,
                    settings=settings,
                    password_hashes=hashes,
                )
                screen._post_complete = True
                screen._boot_drive_detected = True
                screen._bootable_dvd_detected = True
                screen._selected_boot_source = "DVD-ROM"

                with (
                    patch(
                        "win7_2011.win7sim.screens.QInputDialog.getItem",
                        return_value=("Supervisor Password", True),
                    ),
                    patch(
                        "win7_2011.win7sim.screens.QMessageBox.question",
                        return_value=QMessageBox.StandardButton.Yes,
                    ) as confirmation,
                ):
                    event = QKeyEvent(
                        QEvent.Type.KeyPress,
                        Qt.Key.Key_F8,
                        Qt.KeyboardModifier.NoModifier,
                    )
                    screen.keyPressEvent(event)

                self.assertIn("setup choices", confirmation.call_args.args[2])
                self.assertIn("boot order", confirmation.call_args.args[2])
                remaining_hashes = config.load_bios_password_hashes()
                self.assertNotIn("supervisor", remaining_hashes)
                self.assertTrue(
                    config.verify_bios_password("user-secret", remaining_hashes["user"])
                )
                self.assertEqual(config.load_bios_settings(), {})
                self.assertEqual(screen._setup_values["advanced"], [0] * 5)
                self.assertEqual(screen._setup_values["standard"], [0] * 7)
                self.assertEqual(screen._setup_values["password"], [0, 1])
                self.assertEqual(screen._selected_boot_source, "Hard Disk")
                self.assertFalse(screen.setup_open)

                # The recovered supervisor credential no longer blocks setup,
                # while the separate user credential remains stored for startup.
                event = QKeyEvent(
                    QEvent.Type.KeyPress,
                    Qt.Key.Key_Delete,
                    Qt.KeyboardModifier.NoModifier,
                )
                screen.keyPressEvent(event)
                self.assertTrue(screen.setup_open)
                screen.close()
                screen.deleteLater()

    def test_post_recovery_decline_and_failed_save_leave_password_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            storage = Path(directory) / "System"
            password_file = storage / "bios-passwords.json"
            settings_file = storage / "bios.json"
            settings = {"advanced": [0, 0, 0, 1, 0]}
            with (
                patch.object(config, "BIOS_PASSWORDS_FILE", password_file),
                patch.object(config, "BIOS_SETTINGS_FILE", settings_file),
                patch.object(config, "BIOS_PASSWORD_HASH_ITERATIONS", 100),
            ):
                hashes = {"user": config.hash_bios_password("user-secret")}
                config.save_bios_password_hashes(hashes)
                config.save_bios_settings(settings)
                screen = BiosScreen(
                    auto_start=False,
                    settings=settings,
                    password_hashes=hashes,
                )

                with (
                    patch(
                        "win7_2011.win7sim.screens.QInputDialog.getItem",
                        return_value=("User Password", True),
                    ),
                    patch(
                        "win7_2011.win7sim.screens.QMessageBox.question",
                        return_value=QMessageBox.StandardButton.No,
                    ),
                ):
                    event = QKeyEvent(
                        QEvent.Type.KeyPress,
                        Qt.Key.Key_F8,
                        Qt.KeyboardModifier.NoModifier,
                    )
                    screen.keyPressEvent(event)
                self.assertEqual(config.load_bios_password_hashes(), hashes)
                self.assertEqual(config.load_bios_settings(), settings)

                with patch.object(
                    config,
                    "save_bios_password_hashes",
                    side_effect=OSError("simulated password-file failure"),
                ):
                    with self.assertRaises(OSError):
                        config.recover_bios_password("user")
                self.assertEqual(config.load_bios_settings(), settings)
                self.assertEqual(config.load_bios_password_hashes(), hashes)
                screen.close()
                screen.deleteLater()

    def test_interrupted_recovery_restores_previous_state_on_next_launch(self) -> None:
        class SimulatedPowerLoss(BaseException):
            pass

        with tempfile.TemporaryDirectory() as directory:
            storage = Path(directory) / "System"
            password_file = storage / "bios-passwords.json"
            settings_file = storage / "bios.json"
            journal_file = storage / "bios-password-recovery.json"
            settings = {"standard": [1, 0, 1], "advanced": [0, 1]}
            with (
                patch.object(config, "BIOS_PASSWORDS_FILE", password_file),
                patch.object(config, "BIOS_SETTINGS_FILE", settings_file),
                patch.object(config, "BIOS_PASSWORD_HASH_ITERATIONS", 100),
            ):
                hashes = {
                    "supervisor": config.hash_bios_password("supervisor-secret"),
                    "user": config.hash_bios_password("user-secret"),
                }
                config.save_bios_password_hashes(hashes)
                config.save_bios_settings(settings)

                # Simulate abrupt process loss after the settings write but
                # before the password file update; normal rollback must not run.
                with patch.object(
                    config,
                    "save_bios_password_hashes",
                    side_effect=SimulatedPowerLoss(),
                ):
                    with self.assertRaises(SimulatedPowerLoss):
                        config.recover_bios_password("supervisor")

                self.assertEqual(config.load_bios_settings(), {})
                self.assertTrue(journal_file.exists())
                self.assertNotIn(
                    "supervisor-secret",
                    journal_file.read_text(encoding="utf-8"),
                )

                status = config.recover_interrupted_bios_password_recovery()

                self.assertIn("interrupted", status.lower())
                self.assertIn("restored", status.lower())
                self.assertNotIn("supervisor-secret", status)
                self.assertEqual(config.load_bios_settings(), settings)
                self.assertEqual(config.load_bios_password_hashes(), hashes)
                self.assertFalse(journal_file.exists())

    def test_application_stays_on_bios_until_user_password_is_accepted(self) -> None:
        with (
            patch("win7_2011.win7sim.application.ensure_storage_folders"),
            patch(
                "win7_2011.win7sim.application.recover_interrupted_bios_password_recovery",
                return_value=(
                    "Interrupted BIOS recovery: previous password and BIOS "
                    "settings restored."
                ),
            ),
            patch("win7_2011.win7sim.application.load_account", return_value=None),
            patch("win7_2011.win7sim.application.load_bios_settings", return_value={}),
            patch(
                "win7_2011.win7sim.application.load_bios_password_hashes_with_status",
                return_value=(
                    {"user": "validated-test-hash"},
                    "BIOS password backup recovery used; main file repaired.",
                ),
            ),
            patch.dict(os.environ, {"WIN7_SIM_FAST_BOOT": "1"}),
        ):
            window = SimulationWindow()
            bios_screen = window.stack.currentWidget()
            self.assertIsInstance(bios_screen, BiosScreen)
            assert isinstance(bios_screen, BiosScreen)
            self.assertIn("BIOS password backup recovery used", bios_screen._setup_status)
            self.assertIn("Interrupted BIOS recovery", bios_screen._setup_status)
            for timer in bios_screen._post_timers:
                timer.stop()
            bios_screen._post_complete = True
            bios_screen._boot_drive_detected = True
            bios_screen._selected_boot_source = "Hard Disk"

            with patch.object(BiosScreen, "authorize_startup", side_effect=[False, True]):
                window._show_windows_start()
                self.assertIs(window.stack.currentWidget(), bios_screen)
                self.assertEqual(window._stage, "bios")

                window._show_windows_start()
                self.assertIsInstance(window.stack.currentWidget(), WindowsStartScreen)
                self.assertEqual(window._stage, "windows-start")

            start_screen = window.stack.currentWidget()
            if isinstance(start_screen, WindowsStartScreen):
                start_screen._timer.stop()
            window.close()
            window.deleteLater()


if __name__ == "__main__":
    unittest.main()
