import os
import unittest
import wave
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


from PySide6.QtCore import QEvent, QPoint, QPointF, QSize, Qt  # noqa: E402
from PySide6.QtGui import QEnterEvent, QKeyEvent, QPixmap  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import (  # noqa: E402
    QApplication,
    QComboBox,
    QFrame,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QWidget,
)

from win7_2011.win7sim.application import SimulationWindow  # noqa: E402
from win7_2011.win7sim.apps import MessengerApp, ProfileDirectoryApp  # noqa: E402
from win7_2011.win7sim.config import load_bios_settings  # noqa: E402
from win7_2011.win7sim.contacts import CONTACTS  # noqa: E402
from win7_2011.win7sim.desktop import DesktopPage  # noqa: E402
from win7_2011.win7sim.identity import FursonaProfile, UserAccount  # noqa: E402
from win7_2011.win7sim.service import ConnectionSimulator  # noqa: E402
from win7_2011.win7sim.screens import (  # noqa: E402
    BiosScreen,
    LoginScreen,
    ShutdownScreen,
    SetupWizard,
    UserSelectionScreen,
    WindowsStartScreen,
)


def sample_account() -> UserAccount:
    profile = FursonaProfile(
        fursona_name="Rook",
        species="red fox",
        pronouns="they/them",
        date_of_birth="1988-06-12",
        bio="An example profile used only in tests.",
    )
    return UserAccount(
        desktop_name="Test User",
        online_name="test_user",
        use_desktop_name_online=False,
        fursonas=[profile],
        active_profile_id=profile.profile_id,
    )


class QtUiSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.qt_app = QApplication.instance() or QApplication([])

    def send_key(self, widget: QWidget, key: Qt.Key) -> None:
        event = QKeyEvent(
            QEvent.Type.KeyPress,
            key,
            Qt.KeyboardModifier.NoModifier,
        )
        self.qt_app.sendEvent(widget, event)

    def test_startup_screen_paints_offscreen(self) -> None:
        screen = WindowsStartScreen()
        screen.resize(1024, 768)
        screen.show()
        self.qt_app.processEvents()
        image = screen.grab()
        self.assertFalse(image.isNull())
        self.assertEqual(image.size().width(), 1024)
        self.assertEqual(screen._timer.interval(), 50)
        self.assertEqual(len(screen._sequence), 105 + 3 * 88)
        screen.close()
        screen.deleteLater()

    def test_bios_screen_reveals_hardware_checks_and_memory_with_post_sound(self) -> None:
        screen = BiosScreen()
        screen.resize(960, 600)
        screen.show()
        self.qt_app.processEvents()

        self.assertFalse(screen._ami_logo.isNull())
        self.assertFalse(screen._energy_star_logo.isNull())
        self.assertFalse(screen._gemma_logo.isNull())
        self.assertFalse(screen._gemini_logo.isNull())
        self.assertEqual(screen._gemma_logo.size(), QSize(542, 132))
        self.assertEqual(screen._gemini_logo.size(), QSize(53, 56))
        self.assertFalse(screen.memory_test_complete)
        self.assertFalse(screen.cpu_check_complete)
        self.assertFalse(screen.usb_check_complete)
        self.assertFalse(screen.sata_port_1_check_complete)
        self.assertFalse(screen.sata_port_2_check_complete)
        self.assertFalse(screen.post_complete)
        self.assertFalse(screen.grab().isNull())

        screen._complete_cpu_check()
        self.assertTrue(screen.cpu_check_complete)
        self.assertFalse(screen.usb_check_complete)
        screen._complete_usb_check()
        self.assertTrue(screen.usb_check_complete)
        self.assertFalse(screen.sata_port_1_check_complete)
        screen._complete_sata_port_1_check()
        self.assertTrue(screen.sata_port_1_check_complete)
        self.assertFalse(screen.sata_port_2_check_complete)
        screen._complete_sata_port_2_check()
        self.assertTrue(screen.sata_port_2_check_complete)
        self.assertFalse(screen.post_complete)

        post_completed = []
        screen.postComplete.connect(lambda: post_completed.append(True))
        screen._complete_memory_test()
        self.assertTrue(screen.memory_test_complete)
        self.assertTrue(screen.post_complete)
        self.assertEqual(post_completed, [True])

        sound_path = (
            Path(__file__).resolve().parents[1]
            / "assets"
            / "bios"
            / "boot-post.wav"
        )
        with wave.open(str(sound_path), "rb") as sound:
            sound_duration_ms = round(
                sound.getnframes() * 1000 / sound.getframerate()
            )
        self.assertEqual(screen.MEMORY_CHECK_DELAY_MS, sound_duration_ms)
        self.assertEqual(
            [timer.interval() for timer in screen._post_timers],
            [
                screen.CPU_CHECK_DELAY_MS,
                screen.USB_CHECK_DELAY_MS,
                screen.SATA_PORT_1_CHECK_DELAY_MS,
                screen.SATA_PORT_2_CHECK_DELAY_MS,
                screen.MEMORY_CHECK_DELAY_MS,
            ],
        )

        for timer in screen._post_timers:
            timer.stop()

        screen.close()
        screen.deleteLater()

    def test_shutdown_screen_transitions_to_safe_image_and_emits_choices(self) -> None:
        screen = ShutdownScreen(safe_delay_ms=60_000)
        screen.resize(1024, 768)
        screen.show()
        self.qt_app.processEvents()
        self.assertTrue(screen._message.isVisible())
        self.assertFalse(screen._safe_image_label.isVisible())

        screen._show_safe_screen()
        self.qt_app.processEvents()
        self.assertTrue(screen._safe_image_label.isVisible())
        self.assertEqual(screen.grab().toImage().pixelColor(10, 10).name(), "#000000")
        self.assertTrue(screen.restart_button.isVisible())
        self.assertTrue(screen.end_button.isVisible())
        self.assertTrue(screen.recovery_button.isVisible())

        actions = []
        screen.restartRequested.connect(lambda: actions.append("restart"))
        screen.endProgramRequested.connect(lambda: actions.append("end"))
        screen.recoveryRequested.connect(lambda: actions.append("recovery"))
        screen.restart_button.click()
        screen.end_button.click()
        screen.recovery_button.click()
        self.assertEqual(actions, ["restart", "end", "recovery"])
        screen.close()
        screen.deleteLater()

    def test_recovery_mode_requires_confirmation_before_reset(self) -> None:
        with (
            patch("win7_2011.win7sim.application.ensure_storage_folders"),
            patch("win7_2011.win7sim.application.load_account", return_value=None),
            patch("win7_2011.win7sim.application.reset_user_data") as reset,
            patch(
                "win7_2011.win7sim.application.QMessageBox.question",
                return_value=QMessageBox.StandardButton.No,
            ),
        ):
            window = SimulationWindow()
            window.account = sample_account()
            window._stage = "shutdown"
            window._enter_recovery_mode()
            reset.assert_not_called()
            self.assertIsNotNone(window.account)

            with patch(
                "win7_2011.win7sim.application.QMessageBox.question",
                return_value=QMessageBox.StandardButton.Yes,
            ):
                window._enter_recovery_mode()

            reset.assert_called_once_with()
            self.assertIsNone(window.account)
            self.assertEqual(window._stage, "bios")
            window._stage = "login"
            window.close()
            window.deleteLater()

    def test_delete_opens_navigable_setup_and_escape_returns_to_post(self) -> None:
        screen = BiosScreen(auto_start=False)
        screen.start_post()
        screen.resize(960, 600)
        screen.show()
        self.qt_app.processEvents()

        self.send_key(screen, Qt.Key.Key_Delete)
        self.assertTrue(screen.setup_open)
        self.assertTrue(all(not timer.isActive() for timer in screen._post_timers))
        self.assertFalse(screen.grab().isNull())

        self.send_key(screen, Qt.Key.Key_Right)
        self.assertEqual(screen._setup_group, 1)
        self.send_key(screen, Qt.Key.Key_Down)
        self.send_key(screen, Qt.Key.Key_Down)
        self.send_key(screen, Qt.Key.Key_Return)
        self.assertEqual(screen._setup_page, "colors")
        self.send_key(screen, Qt.Key.Key_Right)
        self.assertEqual(screen._setup_values["colors"], [1])

        self.send_key(screen, Qt.Key.Key_Escape)
        self.assertIsNone(screen._setup_page)
        self.send_key(screen, Qt.Key.Key_Left)
        self.send_key(screen, Qt.Key.Key_Down)
        self.send_key(screen, Qt.Key.Key_Return)
        self.assertEqual(screen._setup_page, "advanced")
        self.send_key(screen, Qt.Key.Key_Down)
        self.send_key(screen, Qt.Key.Key_Right)
        self.assertEqual(screen._setup_values["advanced"][1], 1)
        self.send_key(screen, Qt.Key.Key_Escape)
        self.send_key(screen, Qt.Key.Key_Escape)
        self.assertFalse(screen.setup_open)
        self.assertTrue(all(timer.isActive() for timer in screen._post_timers))

        advanced = []
        screen.advanceRequested.connect(lambda: advanced.append(True))
        screen._complete_sata_port_1_check()
        screen._complete_memory_test()
        self.send_key(screen, Qt.Key.Key_Space)
        self.assertEqual(advanced, [True])

        for timer in screen._post_timers:
            timer.stop()
        screen.close()
        screen.deleteLater()

    def test_bios_f10_persists_settings_and_escape_discards_later_edits(self) -> None:
        from tempfile import TemporaryDirectory

        from win7_2011.win7sim import config

        with TemporaryDirectory() as directory:
            settings_file = Path(directory) / "System" / "bios.json"
            with patch.object(config, "BIOS_SETTINGS_FILE", settings_file):
                screen = BiosScreen(auto_start=False)
                screen.show()
                self.qt_app.processEvents()
                self.send_key(screen, Qt.Key.Key_Delete)
                self.send_key(screen, Qt.Key.Key_Down)
                self.send_key(screen, Qt.Key.Key_Return)
                self.assertEqual(screen._setup_page, "advanced")
                self.send_key(screen, Qt.Key.Key_Down)
                self.send_key(screen, Qt.Key.Key_Right)
                self.assertEqual(screen._setup_values["advanced"][1], 1)
                self.send_key(screen, Qt.Key.Key_F10)

                self.assertFalse(screen.setup_open)
                saved = load_bios_settings()
                self.assertEqual(saved["advanced"][1], 1)

                reopened = BiosScreen(auto_start=False, settings=saved)
                self.assertEqual(reopened._setup_values["advanced"][1], 1)
                reopened.show()
                self.qt_app.processEvents()
                self.send_key(reopened, Qt.Key.Key_Delete)
                self.send_key(reopened, Qt.Key.Key_Down)
                self.send_key(reopened, Qt.Key.Key_Return)
                self.send_key(reopened, Qt.Key.Key_Down)
                self.send_key(reopened, Qt.Key.Key_Right)
                self.assertEqual(reopened._setup_values["advanced"][1], 0)
                self.send_key(reopened, Qt.Key.Key_Escape)
                self.send_key(reopened, Qt.Key.Key_Escape)
                self.assertFalse(reopened.setup_open)
                self.assertEqual(load_bios_settings(), saved)

                with (
                    patch(
                        "win7_2011.win7sim.application.ensure_storage_folders"
                    ),
                    patch(
                        "win7_2011.win7sim.application.load_account",
                        return_value=None,
                    ),
                    patch.dict(os.environ, {"WIN7_SIM_FAST_BOOT": "1"}),
                ):
                    window = SimulationWindow()
                    boot_screen = window.stack.currentWidget()
                    self.assertIsInstance(boot_screen, BiosScreen)
                    assert isinstance(boot_screen, BiosScreen)
                    self.assertEqual(boot_screen._setup_values["advanced"][1], 1)
                    window.close()
                    window.deleteLater()

                screen.close()
                reopened.close()
                screen.deleteLater()
                reopened.deleteLater()

    def test_post_boot_selection_updates_on_save_but_not_on_escape(self) -> None:
        from tempfile import TemporaryDirectory

        from win7_2011.win7sim import config

        with TemporaryDirectory() as directory:
            settings_file = Path(directory) / "System" / "bios.json"
            with patch.object(config, "BIOS_SETTINGS_FILE", settings_file):
                original_settings = {
                    "advanced": [0, 0, 0, 0, 0],
                }
                config.save_bios_settings(original_settings)

                discarded = BiosScreen(
                    auto_start=False,
                    bootable_dvd_present=True,
                    bootable_usb_present=True,
                    settings=load_bios_settings(),
                )
                discarded._complete_usb_check()
                discarded._complete_sata_port_1_check()
                discarded._complete_sata_port_2_check()
                discarded._complete_memory_test()
                self.assertEqual(discarded.selected_boot_source, "Hard Disk")

                self.send_key(discarded, Qt.Key.Key_Delete)
                self.send_key(discarded, Qt.Key.Key_Down)
                self.send_key(discarded, Qt.Key.Key_Return)
                for _ in range(3):
                    self.send_key(discarded, Qt.Key.Key_Down)
                self.send_key(discarded, Qt.Key.Key_Right)
                self.assertEqual(discarded._setup_values["advanced"][3], 1)
                self.send_key(discarded, Qt.Key.Key_Escape)
                self.send_key(discarded, Qt.Key.Key_Escape)

                self.assertFalse(discarded.setup_open)
                self.assertEqual(discarded.selected_boot_source, "Hard Disk")
                self.assertEqual(load_bios_settings(), original_settings)

                saved = BiosScreen(
                    auto_start=False,
                    bootable_dvd_present=True,
                    bootable_usb_present=True,
                    settings=load_bios_settings(),
                )
                saved._complete_usb_check()
                saved._complete_sata_port_1_check()
                saved._complete_sata_port_2_check()
                saved._complete_memory_test()
                self.assertEqual(saved.selected_boot_source, "Hard Disk")

                self.send_key(saved, Qt.Key.Key_Delete)
                self.send_key(saved, Qt.Key.Key_Down)
                self.send_key(saved, Qt.Key.Key_Return)
                for _ in range(3):
                    self.send_key(saved, Qt.Key.Key_Down)
                self.send_key(saved, Qt.Key.Key_Right)
                self.assertEqual(saved._setup_values["advanced"][3], 1)
                self.send_key(saved, Qt.Key.Key_F10)

                self.assertFalse(saved.setup_open)
                self.assertEqual(saved.selected_boot_source, "DVD-ROM")
                self.assertEqual(load_bios_settings()["advanced"][3], 1)

                discarded.close()
                saved.close()
                discarded.deleteLater()
                saved.deleteLater()

    def test_invalid_bios_settings_use_defaults_without_blocking_startup(self) -> None:
        from tempfile import TemporaryDirectory

        from win7_2011.win7sim import config

        invalid_files = {
            "malformed JSON": "{ not valid JSON",
            "invalid choice index": (
                '{"advanced": [0, 0, 0, 99, 0], "colors": [2]}'
            ),
        }
        with TemporaryDirectory() as directory:
            for case, contents in invalid_files.items():
                with self.subTest(case=case):
                    settings_file = Path(directory) / case.replace(" ", "-") / "bios.json"
                    settings_file.parent.mkdir(parents=True)
                    settings_file.write_text(contents, encoding="utf-8")
                    original_contents = settings_file.read_bytes()
                    with (
                        patch.object(config, "BIOS_SETTINGS_FILE", settings_file),
                        patch(
                            "win7_2011.win7sim.application.ensure_storage_folders"
                        ),
                        patch(
                            "win7_2011.win7sim.application.recover_interrupted_bios_password_recovery",
                            return_value=None,
                        ),
                        patch(
                            "win7_2011.win7sim.application.load_account",
                            return_value=None,
                        ),
                        patch(
                            "win7_2011.win7sim.application.load_bios_password_hashes_with_status",
                            return_value=({}, None),
                        ),
                        patch.dict(os.environ, {"WIN7_SIM_FAST_BOOT": "1"}),
                    ):
                        window = SimulationWindow()
                        screen = window.stack.currentWidget()
                        self.assertIsInstance(screen, BiosScreen)
                        assert isinstance(screen, BiosScreen)
                        self.assertIsNone(window._load_error)
                        self.assertIn("defaults are being used", screen._settings_warning)
                        self.assertTrue(
                            all(
                                value == 0
                                for page, values in screen._setup_values.items()
                                for value in values
                            )
                        )
                        self.assertEqual(settings_file.read_bytes(), original_contents)

                        screen._complete_cpu_check()
                        screen._complete_usb_check()
                        screen._complete_sata_port_1_check()
                        screen._complete_sata_port_2_check()
                        screen._complete_memory_test()
                        self.assertEqual(window._stage, "windows-start")
                        window._continue_startup()
                        self.assertEqual(window._stage, "setup")
                        self.assertEqual(settings_file.read_bytes(), original_contents)

                        window.close()
                        window.deleteLater()

    def test_bios_read_errors_use_defaults_without_rewriting_saved_settings(self) -> None:
        from tempfile import TemporaryDirectory

        from win7_2011.win7sim import config

        for error in (PermissionError("Access denied"), OSError("Storage unavailable")):
            with self.subTest(error=type(error).__name__), TemporaryDirectory() as directory:
                settings_file = Path(directory) / "System" / "bios.json"
                settings_file.parent.mkdir(parents=True)
                settings_file.write_text(
                    '{"advanced": [0, 0, 0, 1, 0], "colors": [2]}\n',
                    encoding="utf-8",
                )
                original_contents = settings_file.read_bytes()
                original_mtime = settings_file.stat().st_mtime_ns
                with (
                    patch.object(config, "BIOS_SETTINGS_FILE", settings_file),
                    patch("win7_2011.win7sim.application.ensure_storage_folders"),
                    patch(
                        "win7_2011.win7sim.application.recover_interrupted_bios_password_recovery",
                        return_value=None,
                    ),
                    patch(
                        "win7_2011.win7sim.application.load_account",
                        return_value=None,
                    ),
                    patch(
                        "win7_2011.win7sim.application.load_bios_password_hashes_with_status",
                        return_value=({}, None),
                    ),
                    patch(
                        "win7_2011.win7sim.application.load_bios_settings",
                        side_effect=error,
                    ) as load_settings,
                    patch.dict(os.environ, {"WIN7_SIM_FAST_BOOT": "1"}),
                ):
                    window = SimulationWindow()
                    try:
                        load_settings.assert_called_once_with()
                        self.assertIsNone(window._load_error)
                        self.assertEqual(window._bios_settings, {})
                        screen = window.stack.currentWidget()
                        self.assertIsInstance(screen, BiosScreen)
                        assert isinstance(screen, BiosScreen)
                        self.assertEqual(
                            screen._settings_warning,
                            "Saved BIOS settings could not be loaded; defaults are being used.",
                        )
                        self.assertEqual(screen._setup_status, screen._settings_warning)
                        self.assertTrue(
                            all(
                                value == 0
                                for values in screen._setup_values.values()
                                for value in values
                            )
                        )
                        window.show()
                        self.qt_app.processEvents()
                        self.assertFalse(screen.grab().isNull())
                        self.assertEqual(settings_file.read_bytes(), original_contents)
                        self.assertEqual(settings_file.stat().st_mtime_ns, original_mtime)

                        screen._complete_cpu_check()
                        screen._complete_usb_check()
                        screen._complete_sata_port_1_check()
                        screen._complete_sata_port_2_check()
                        screen._complete_memory_test()
                        self.assertEqual(window._stage, "windows-start")
                        window._continue_startup()
                        self.assertEqual(window._stage, "setup")
                        self.assertIsInstance(window.stack.currentWidget(), SetupWizard)
                        self.assertEqual(settings_file.read_bytes(), original_contents)
                        self.assertEqual(settings_file.stat().st_mtime_ns, original_mtime)
                    finally:
                        window.close()
                        window.deleteLater()

    def test_bios_default_presets_apply_and_save_supported_choices(self) -> None:
        from tempfile import TemporaryDirectory

        from win7_2011.win7sim import config

        initial_settings = {
            "standard": [1, 1, 0, 1, 0, 0, 1],
            "advanced": [0, 0, 0, 0, 0],
            "chipset": [0, 0, 0, 0],
            "power": [0, 0, 0, 0],
            "colors": [2],
            "antivirus": [1],
        }

        with TemporaryDirectory() as directory:
            settings_file = Path(directory) / "System" / "bios.json"
            with patch.object(config, "BIOS_SETTINGS_FILE", settings_file):
                for preset_index, preset in enumerate(
                    ("original", "optimal", "fail_safe")
                ):
                    with self.subTest(preset=preset):
                        screen = BiosScreen(
                            auto_start=False,
                            settings=initial_settings,
                        )
                        screen.show()
                        self.qt_app.processEvents()
                        self.send_key(screen, Qt.Key.Key_Delete)
                        for _ in range(3):
                            self.send_key(screen, Qt.Key.Key_Right)
                        for _ in range(preset_index):
                            self.send_key(screen, Qt.Key.Key_Down)
                        self.send_key(screen, Qt.Key.Key_Return)

                        expected = screen.SETUP_PRESETS[preset]
                        for page, values in expected.items():
                            for value, (_label, choices) in zip(
                                values,
                                screen.SETUP_PAGES[page][1],
                                strict=True,
                            ):
                                self.assertGreaterEqual(value, 0)
                                self.assertLess(value, len(choices))
                        self.assertEqual(
                            {
                                page: tuple(values)
                                for page, values in expected.items()
                            },
                            {
                                page: tuple(screen._setup_values[page])
                                for page in expected
                            },
                        )

                        # The values are available to setup pages before saving.
                        for _ in range(3):
                            self.send_key(screen, Qt.Key.Key_Left)
                        self.send_key(screen, Qt.Key.Key_Down)
                        self.send_key(screen, Qt.Key.Key_Return)
                        self.assertEqual(screen._setup_page, "advanced")
                        self.assertEqual(
                            tuple(screen._setup_values["advanced"]),
                            expected["advanced"],
                        )
                        self.assertFalse(screen.grab().isNull())

                        self.send_key(screen, Qt.Key.Key_F10)
                        self.assertFalse(screen.setup_open)
                        self.assertEqual(
                            load_bios_settings(),
                            {
                                page: list(values)
                                for page, values in expected.items()
                            },
                        )
                        screen.close()
                        screen.deleteLater()

    def test_bios_escape_discards_applied_preset(self) -> None:
        from tempfile import TemporaryDirectory

        from win7_2011.win7sim import config

        initial_settings = {
            "standard": [1, 1, 0, 1, 0, 0, 1],
            "advanced": [0, 0, 0, 0, 0],
            "chipset": [0, 0, 0, 0],
            "power": [0, 0, 0, 0],
            "colors": [2],
            "antivirus": [1],
        }

        with TemporaryDirectory() as directory:
            settings_file = Path(directory) / "System" / "bios.json"
            with patch.object(config, "BIOS_SETTINGS_FILE", settings_file):
                config.save_bios_settings(initial_settings)
                screen = BiosScreen(
                    auto_start=False,
                    settings=initial_settings,
                )
                self.send_key(screen, Qt.Key.Key_Delete)
                for _ in range(3):
                    self.send_key(screen, Qt.Key.Key_Right)
                self.send_key(screen, Qt.Key.Key_Down)
                self.send_key(screen, Qt.Key.Key_Return)

                self.assertEqual(
                    tuple(screen._setup_values["chipset"]),
                    screen.SETUP_PRESETS["optimal"]["chipset"],
                )
                self.assertNotEqual(
                    screen._setup_values["chipset"],
                    initial_settings["chipset"],
                )
                self.send_key(screen, Qt.Key.Key_Escape)
                self.assertFalse(screen.setup_open)
                self.assertEqual(load_bios_settings(), initial_settings)
                screen.close()
                screen.deleteLater()

    def test_bios_stays_open_when_f10_cannot_save_settings(self) -> None:
        screen = BiosScreen(auto_start=False)
        self.send_key(screen, Qt.Key.Key_Delete)

        with patch(
            "win7_2011.win7sim.screens.save_bios_settings",
            side_effect=OSError("storage is unavailable"),
        ):
            self.send_key(screen, Qt.Key.Key_F10)

        self.assertTrue(screen.setup_open)
        self.assertIn("Settings not saved", screen._setup_status)
        self.assertIn("storage is unavailable", screen._setup_status)
        screen.close()
        screen.deleteLater()

    def test_bios_f9_explicitly_restores_backup_and_keeps_passwords(self) -> None:
        from tempfile import TemporaryDirectory

        from win7_2011.win7sim import config

        with TemporaryDirectory() as directory:
            primary = Path(directory) / "bios.json"
            with patch.object(config, "BIOS_SETTINGS_FILE", primary):
                settings = {"colors": [2], "advanced": [0, 0, 0, 1, 0]}
                config.save_bios_settings(settings)
                primary.write_bytes(b"\xff{damaged")
                screen = BiosScreen(
                    auto_start=False,
                    settings_warning="Saved BIOS settings could not be loaded.",
                    password_hashes={"user": "unchanged"},
                )
                self.send_key(screen, Qt.Key.Key_Delete)
                self.assertIn("F9", screen._setup_status)
                self.assertFalse(screen.grab().isNull())
                with patch(
                    "win7_2011.win7sim.screens.QMessageBox.question",
                    return_value=QMessageBox.StandardButton.No,
                ):
                    self.send_key(screen, Qt.Key.Key_F9)
                self.assertEqual(primary.read_bytes(), b"\xff{damaged")
                self.assertEqual(screen._setup_values["colors"], [0])
                self.assertFalse(list(primary.parent.glob("bios.damaged-*")))
                with patch(
                    "win7_2011.win7sim.screens.QMessageBox.question",
                    return_value=QMessageBox.StandardButton.Yes,
                ) as confirmation:
                    self.send_key(screen, Qt.Key.Key_F9)
                self.assertEqual(
                    confirmation.call_args.args[-1], QMessageBox.StandardButton.No,
                )
                self.assertTrue(screen.setup_open)
                self.assertIsNone(screen._settings_warning)
                self.assertEqual(screen._setup_values["colors"], [2])
                self.assertEqual(screen._setup_values["advanced"], settings["advanced"])
                self.assertEqual(screen._password_hashes, {"user": "unchanged"})
                self.assertEqual(screen._setup_values["password"], [0, 1])
                self.assertEqual(config.load_bios_settings(), settings)
                archive, = primary.parent.glob("bios.damaged-*")
                self.assertEqual(archive.read_bytes(), b"\xff{damaged")
                self.assertIn(archive.name, screen._setup_status)
                screen.close()
                screen.deleteLater()

    def test_bios_f9_bad_backups_or_storage_errors_leave_choices_unchanged(self) -> None:
        from tempfile import TemporaryDirectory

        from win7_2011.win7sim import config

        for backup in (None, "{broken", '{"colors": [999]}', '{"advanced": [1]}'):
            with self.subTest(backup=backup), TemporaryDirectory() as directory:
                primary = Path(directory) / "bios.json"
                primary.write_bytes(b"{damaged")
                if backup is not None:
                    primary.with_name("bios.backup.json").write_text(backup)
                screen = BiosScreen(
                    auto_start=False, settings_warning="Saved settings are damaged.",
                )
                self.send_key(screen, Qt.Key.Key_Delete)
                with (
                    patch.object(config, "BIOS_SETTINGS_FILE", primary),
                    patch(
                        "win7_2011.win7sim.screens.QMessageBox.question",
                        return_value=QMessageBox.StandardButton.Yes,
                    ),
                ):
                    self.send_key(screen, Qt.Key.Key_F9)
                self.assertIn("Settings not restored", screen._setup_status)
                self.assertEqual(screen._setup_values["colors"], [0])
                self.assertIsNotNone(screen._settings_warning)
                self.assertEqual(primary.read_bytes(), b"{damaged")
                self.assertFalse(list(primary.parent.glob("bios.damaged-*")))
                screen.close()
                screen.deleteLater()

        screen = BiosScreen(
            auto_start=False, settings_warning="Saved settings are damaged.",
        )
        self.send_key(screen, Qt.Key.Key_Delete)
        with (
            patch(
                "win7_2011.win7sim.screens.QMessageBox.question",
                return_value=QMessageBox.StandardButton.Yes,
            ),
            patch(
                "win7_2011.win7sim.screens.load_bios_settings_backup",
                return_value={"colors": [2]},
            ),
            patch(
                "win7_2011.win7sim.screens.restore_bios_settings",
                side_effect=PermissionError("Access denied"),
            ),
        ):
            self.send_key(screen, Qt.Key.Key_F9)
        self.assertEqual(screen._setup_values["colors"], [0])
        self.assertIn("Access denied", screen._setup_status)
        self.assertIsNotNone(screen._settings_warning)
        screen.close()
        screen.deleteLater()

    def test_bios_f10_requires_confirmation_when_settings_are_damaged(self) -> None:
        screen = BiosScreen(
            auto_start=False, settings_warning="Saved settings are damaged.",
        )
        self.send_key(screen, Qt.Key.Key_Delete)
        with (
            patch("win7_2011.win7sim.screens.save_bios_settings") as save,
            patch(
                "win7_2011.win7sim.screens.QMessageBox.question",
                return_value=QMessageBox.StandardButton.No,
            ),
        ):
            self.send_key(screen, Qt.Key.Key_F10)
            save.assert_not_called()
        self.assertTrue(screen.setup_open)
        with (
            patch("win7_2011.win7sim.screens.save_bios_settings") as save,
            patch(
                "win7_2011.win7sim.screens.QMessageBox.question",
                return_value=QMessageBox.StandardButton.Yes,
            ),
        ):
            self.send_key(screen, Qt.Key.Key_F10)
            self.assertTrue(save.call_args.kwargs["preserve_original"])
        self.assertFalse(screen.setup_open)
        self.assertIsNone(screen._settings_warning)
        screen.close()
        screen.deleteLater()

    def test_restored_bios_choices_survive_in_process_restart(self) -> None:
        from tempfile import TemporaryDirectory

        from win7_2011.win7sim import config

        for restart_stage in ("login", "user-selection", "shutdown"):
            with self.subTest(stage=restart_stage), TemporaryDirectory() as directory:
                primary = Path(directory) / "bios.json"
                settings = {"colors": [2], "advanced": [0, 0, 0, 1, 0]}
                with (
                    patch.object(config, "BIOS_SETTINGS_FILE", primary),
                    patch("win7_2011.win7sim.application.ensure_storage_folders"),
                    patch(
                        "win7_2011.win7sim.application.recover_interrupted_bios_password_recovery",
                        return_value=None,
                    ),
                    patch(
                        "win7_2011.win7sim.application.load_account",
                        return_value=sample_account(),
                    ),
                    patch(
                        "win7_2011.win7sim.application.load_bios_password_hashes_with_status",
                        return_value=({}, None),
                    ),
                    patch(
                        "win7_2011.win7sim.screens.QMessageBox.question",
                        return_value=QMessageBox.StandardButton.Yes,
                    ),
                ):
                    config.save_bios_settings(settings)
                    primary.write_bytes(b"{damaged")
                    window = SimulationWindow()
                    screen = window.stack.currentWidget()
                    self.assertIsInstance(screen, BiosScreen)
                    self.assertIsNotNone(screen._settings_warning)
                    self.send_key(screen, Qt.Key.Key_Delete)
                    self.send_key(screen, Qt.Key.Key_F9)
                    self.assertEqual(screen._setup_values["colors"], [2])
                    self.send_key(screen, Qt.Key.Key_Escape)
                    screen._complete_cpu_check()
                    screen._complete_usb_check()
                    screen._complete_sata_port_1_check()
                    screen._complete_sata_port_2_check()
                    screen._complete_memory_test()
                    window._continue_startup()
                    self.assertEqual(window._stage, "login")
                    if restart_stage == "user-selection":
                        window._show_user_selection()
                    elif restart_stage == "shutdown":
                        window._begin_shutdown()
                    if restart_stage == "shutdown":
                        window._restart_pc()
                    else:
                        window._restart_from_login()
                    restored = window.stack.currentWidget()
                    self.assertIsInstance(restored, BiosScreen)
                    self.assertEqual(window._stage, "bios")
                    self.assertIsNone(window._bios_settings_warning)
                    self.assertIsNone(restored._settings_warning)
                    self.assertEqual(window._bios_settings, settings)
                    self.assertEqual(restored._setup_values["colors"], [2])
                    self.assertEqual(
                        restored._setup_values["advanced"], settings["advanced"],
                    )
                    archive, = primary.parent.glob("bios.damaged-*")
                    self.assertEqual(archive.read_bytes(), b"{damaged")
                    window.close()
                    window.deleteLater()

    def test_windows_boot_waits_for_post_completion(self) -> None:
        with (
            patch("win7_2011.win7sim.application.ensure_storage_folders"),
            patch("win7_2011.win7sim.application.load_account", return_value=None),
        ):
            window = SimulationWindow()
            window.show()
            self.qt_app.processEvents()
            screen = window.stack.currentWidget()
            self.assertIsInstance(screen, BiosScreen)
            assert isinstance(screen, BiosScreen)
            self.assertTrue(screen.hasFocus())

            event = QKeyEvent(
                QEvent.Type.KeyPress,
                Qt.Key.Key_Space,
                Qt.KeyboardModifier.NoModifier,
            )
            self.qt_app.sendEvent(screen, event)
            self.qt_app.processEvents()

            self.assertEqual(window._stage, "bios")
            window._show_windows_start()
            self.assertEqual(window._stage, "bios")
            screen._complete_cpu_check()
            screen._complete_usb_check()
            screen._complete_sata_port_1_check()
            screen._complete_sata_port_2_check()
            self.assertEqual(window._stage, "bios")
            self.assertIsInstance(window.stack.currentWidget(), BiosScreen)

            screen._complete_memory_test()
            self.qt_app.processEvents()
            self.assertEqual(screen.selected_boot_source, "Hard Disk")
            self.assertEqual(window._stage, "windows-start")
            self.assertIsInstance(window.stack.currentWidget(), WindowsStartScreen)
            window._stage = "login"
            window.close()
            window.deleteLater()

    def test_boot_priority_selects_the_first_detected_bootable_source(self) -> None:
        cases = (
            (True, False, False, 0, "Hard Disk"),
            (False, True, False, 0, "DVD-ROM"),
            (False, False, True, 0, "USB"),
            (True, True, True, 1, "DVD-ROM"),
        )
        for hard_disk, dvd, usb, priority, expected_source in cases:
            with self.subTest(
                hard_disk=hard_disk,
                dvd=dvd,
                usb=usb,
                priority=priority,
            ):
                screen = BiosScreen(
                    auto_start=False,
                    boot_drive_present=hard_disk,
                    bootable_dvd_present=dvd,
                    bootable_usb_present=usb,
                    settings={"advanced": [0, 0, 0, priority, 0]},
                )
                screen._complete_usb_check()
                screen._complete_sata_port_1_check()
                screen._complete_sata_port_2_check()
                screen._complete_memory_test()

                self.assertEqual(screen.boot_drive_detected, hard_disk)
                self.assertEqual(screen.bootable_dvd_detected, dvd)
                self.assertEqual(screen.bootable_usb_detected, usb)
                self.assertEqual(screen.selected_boot_source, expected_source)
                screen.close()
                screen.deleteLater()

    def test_post_device_detection_respects_cmos_drive_configuration(self) -> None:
        cases = (
            (
                "default configured drives",
                [0, 0, 0, 0, 0, 0, 0],
                True,
                "Hard Disk",
                True,
                True,
            ),
            (
                "hard disk not installed",
                [0, 0, 0, 1, 0, 0, 0],
                False,
                "DVD-ROM",
                True,
                True,
            ),
            (
                "hard disk configured as primary slave",
                [0, 0, 0, 1, 1, 0, 0],
                True,
                "Hard Disk",
                True,
                True,
            ),
            (
                "DVD drive configured as secondary slave",
                [0, 0, 0, 0, 0, 1, 1],
                True,
                "Hard Disk",
                True,
                True,
            ),
            (
                "DVD drive not installed",
                [0, 0, 0, 0, 0, 1, 0],
                True,
                "Hard Disk",
                False,
                False,
            ),
        )
        for (
            case,
            standard_settings,
            expected_hard_disk,
            expected_boot_source,
            expected_dvd_drive,
            expected_dvd_media,
        ) in cases:
            with self.subTest(case=case):
                screen = BiosScreen(
                    auto_start=False,
                    boot_drive_present=True,
                    bootable_dvd_present=True,
                    settings={"standard": standard_settings},
                )
                screen._complete_sata_port_1_check()
                screen._complete_sata_port_2_check()
                screen._complete_memory_test()

                self.assertEqual(screen.boot_drive_detected, expected_hard_disk)
                self.assertEqual(screen._dvd_drive_detected, expected_dvd_drive)
                self.assertEqual(
                    screen.bootable_dvd_detected,
                    expected_dvd_media,
                )
                self.assertEqual(screen.selected_boot_source, expected_boot_source)
                screen.close()
                screen.deleteLater()

    def test_uninstalled_dvd_cannot_be_selected_as_the_only_boot_source(self) -> None:
        screen = BiosScreen(
            auto_start=False,
            boot_drive_present=False,
            bootable_dvd_present=True,
            settings={"standard": [0, 0, 0, 1, 0, 1, 0]},
        )
        screen._complete_sata_port_1_check()
        screen._complete_sata_port_2_check()
        screen._complete_memory_test()

        self.assertFalse(screen.boot_drive_detected)
        self.assertFalse(screen._dvd_drive_detected)
        self.assertFalse(screen.bootable_dvd_detected)
        self.assertIsNone(screen.selected_boot_source)
        screen.close()
        screen.deleteLater()

    def test_windows_boots_from_dvd_when_hard_drive_is_missing(self) -> None:
        with (
            patch("win7_2011.win7sim.application.ensure_storage_folders"),
            patch("win7_2011.win7sim.application.load_account", return_value=None),
            patch.dict(os.environ, {"WIN7_SIM_FAST_BOOT": "1"}),
        ):
            window = SimulationWindow(
                boot_drive_present=False,
                bootable_dvd_present=True,
            )
            screen = window.stack.currentWidget()
            self.assertIsInstance(screen, BiosScreen)
            assert isinstance(screen, BiosScreen)
            for timer in screen._post_timers:
                timer.stop()
            screen._complete_usb_check()
            screen._complete_sata_port_1_check()
            screen._complete_sata_port_2_check()
            screen._complete_memory_test()

            self.assertFalse(screen.boot_drive_detected)
            self.assertEqual(screen.selected_boot_source, "DVD-ROM")
            self.assertEqual(window._stage, "windows-start")
            self.assertIsInstance(window.stack.currentWidget(), WindowsStartScreen)
            window.close()
            window.deleteLater()

    def test_missing_boot_drive_shows_bios_error_and_blocks_windows_start(self) -> None:
        with (
            patch("win7_2011.win7sim.application.ensure_storage_folders"),
            patch("win7_2011.win7sim.application.load_account", return_value=None),
        ):
            window = SimulationWindow(boot_drive_present=False)
            screen = window.stack.currentWidget()
            self.assertIsInstance(screen, BiosScreen)
            assert isinstance(screen, BiosScreen)

            screen._complete_cpu_check()
            screen._complete_usb_check()
            screen._complete_sata_port_1_check()
            screen._complete_sata_port_2_check()
            self.assertFalse(screen.boot_drive_detected)
            screen._complete_memory_test()
            self.qt_app.processEvents()

            self.assertTrue(screen.post_complete)
            self.assertIsNone(screen.selected_boot_source)
            self.assertEqual(window._stage, "bios")
            self.assertIs(window.stack.currentWidget(), screen)
            self.assertEqual(
                screen.BOOT_FAILURE_MESSAGE,
                "ERROR: No bootable device found",
            )
            window.close()
            window.deleteLater()

    def test_boot_frames_follow_the_supplied_three_cycle_sequence(self) -> None:
        sequence = WindowsStartScreen.make_sequence(loop_count=3)
        first_cycle = list(range(103, 59, -1)) + list(range(61, 105))
        self.assertEqual(sequence[:105], list(range(105)))
        self.assertEqual(sequence[105:193], first_cycle)
        self.assertEqual(len(sequence), 105 + 3 * 88)

    def test_space_skips_boot_animation_to_login(self) -> None:
        with (
            patch("win7_2011.win7sim.application.ensure_storage_folders"),
            patch("win7_2011.win7sim.application.load_account", return_value=None),
        ):
            window = SimulationWindow()
            window.account = sample_account()
            bios = window.stack.currentWidget()
            self.assertIsInstance(bios, BiosScreen)
            assert isinstance(bios, BiosScreen)
            bios._complete_sata_port_1_check()
            bios._complete_memory_test()
            window.show()
            screen = window.stack.currentWidget()
            self.assertIsInstance(screen, WindowsStartScreen)
            assert isinstance(screen, WindowsStartScreen)
            self.qt_app.processEvents()
            self.assertTrue(screen.hasFocus())
            finished = []
            screen.finished.connect(lambda: finished.append(True))

            event = QKeyEvent(
                QEvent.Type.KeyPress,
                Qt.Key.Key_Space,
                Qt.KeyboardModifier.NoModifier,
            )
            self.qt_app.sendEvent(screen, event)
            self.qt_app.processEvents()

            self.assertEqual(window._stage, "login")
            self.assertIsInstance(window.stack.currentWidget(), LoginScreen)
            self.assertEqual(finished, [True])
            window._stage = "login"
            window.close()
            window.deleteLater()

    def test_setup_accepts_multiple_adult_profiles(self) -> None:
        wizard = SetupWizard()
        wizard.desktop_name.setText("Test User")
        account = wizard.collect_account()
        self.assertEqual(
            [profile.fursona_name for profile in account.fursonas],
            ["Kithylin", "Beep", "Foxy", "Sheppie", "Snowmew", "Quake"],
        )
        self.assertEqual(
            [profile.date_of_birth for profile in account.fursonas],
            [
                "1964-04-25",
                "1988-05-12",
                "1989-01-02",
                "1986-08-10",
                "1983-05-12",
                "1985-03-27",
            ],
        )
        self.assertEqual(account.fursonas[0].location, "Buffalo NY")
        self.assertEqual(account.fursonas[4].gender, "Female")
        self.assertEqual(len(account.fursonas), 6)
        self.assertEqual(wizard.error_label.text(), "")
        wizard.deleteLater()

    def test_login_uses_supplied_art_and_accepts_any_or_empty_password(self) -> None:
        screen = LoginScreen(sample_account())
        screen.resize(1280, 720)
        screen.show()
        self.qt_app.processEvents()
        self.assertEqual(screen.username_label.text(), "Test User")
        self.assertFalse(screen.profile_icon.pixmap().isNull())
        supplied_icon = QPixmap(
            str(
                Path(__file__).resolve().parents[1]
                / "assets"
                / "login"
                / "Kithylin_Profile_Icon.jpg"
            )
        )
        self.assertEqual(
            screen.profile_icon.pixmap().toImage(),
            supplied_icon.toImage(),
        )
        self.assertEqual(screen.profile_icon.size(), QSize(83, 83))
        self.assertEqual(screen.profile_icon.pixmap().size(), QSize(83, 83))
        self.assertFalse(screen.profile_icon.hasScaledContents())
        self.assertEqual(screen.password_entry.echoMode(), QLineEdit.EchoMode.Password)
        self.assertIsNone(screen.findChild(QComboBox))
        login_ids = []
        screen.loginRequested.connect(login_ids.append)
        screen.password_entry.setText("this is not checked")
        screen.password_entry.returnPressed.emit()
        screen.password_entry.clear()
        screen.login_button.click()
        self.assertEqual(login_ids, [screen._profile_id, screen._profile_id])
        screen._restart_timer.stop()
        screen.deleteLater()

    def test_user_selection_displays_profiles_and_emits_hover_and_select_sounds(
        self,
    ) -> None:
        account = sample_account()
        second_profile = FursonaProfile(
            fursona_name="Beep",
            species="raccoon",
            pronouns="they/them",
            date_of_birth="1988-06-12",
            bio="Another test profile.",
        )
        account.fursonas.append(second_profile)
        screen = UserSelectionScreen(account)
        screen.resize(960, 600)
        screen.show()
        self.qt_app.processEvents()
        self.assertEqual(len(screen.profile_buttons), 2)
        self.assertEqual(
            [button.profile_name for button in screen.profile_buttons],
            ["Rook", "Beep"],
        )

        sounds = []
        selected = []
        screen.soundRequested.connect(sounds.append)
        screen.profileSelected.connect(selected.append)
        button = screen.profile_buttons[1]
        center = button.rect().center()
        button.enterEvent(
            QEnterEvent(QPointF(0, 0), QPointF(0, 0), QPointF(0, 0))
        )
        self.assertTrue(button._hovered)
        QTest.mouseClick(button, Qt.MouseButton.LeftButton, pos=center)
        self.assertEqual(sounds, ["User_Highlight.wav", "User_Select.wav"])
        self.assertEqual(selected, [second_profile.profile_id])
        screen._restart_timer.stop()
        screen.deleteLater()

    def test_user_selection_only_switches_to_saved_profiles(self) -> None:
        account = sample_account()
        controller = SimpleNamespace(
            _stage="user-selection",
            account=account,
            _show_login=Mock(),
            _show_error=Mock(),
        )

        with patch("win7_2011.win7sim.application.save_account") as save_account:
            SimulationWindow._select_user_profile(
                controller,
                account.fursonas[0].profile_id,
            )

        self.assertEqual(account.active_profile_id, account.fursonas[0].profile_id)
        self.assertEqual(len(account.fursonas), 1)
        save_account.assert_called_once_with(account)
        controller._show_login.assert_called_once_with()
        controller._show_error.assert_not_called()

        save_account.reset_mock()
        SimulationWindow._select_user_profile(controller, "not-a-saved-profile")
        save_account.assert_not_called()
        controller._show_error.assert_called_once()

    def test_user_selection_sleep_wakes_and_restart_uses_three_second_screen(
        self,
    ) -> None:
        screen = UserSelectionScreen(sample_account())
        screen.resize(960, 600)
        screen.show()
        self.qt_app.processEvents()

        screen._choose_power_action("sleep")
        self.assertTrue(screen._sleeping)
        event = QKeyEvent(
            QEvent.Type.KeyPress,
            Qt.Key.Key_A,
            Qt.KeyboardModifier.NoModifier,
        )
        self.qt_app.sendEvent(screen, event)
        self.assertFalse(screen._sleeping)
        self.assertTrue(screen._controls.isVisible())

        screen._choose_power_action("restart")
        self.assertTrue(screen._restarting)
        self.assertEqual(screen._restart_timer.interval(), 3000)
        screen._restart_timer.stop()
        screen.deleteLater()

    def test_login_power_menu_highlights_and_runs_restart(self) -> None:
        screen = LoginScreen(sample_account())
        screen.resize(960, 600)
        screen.show()
        self.qt_app.processEvents()
        screen.power_button.click()
        self.assertTrue(screen.power_menu.isVisible())

        QTest.mouseMove(screen.power_menu, QPoint(22, 10))
        self.assertEqual(screen.power_menu._hovered_choice, "restart")
        QTest.mouseClick(
            screen.power_menu,
            Qt.MouseButton.LeftButton,
            pos=QPoint(22, 10),
        )
        self.assertTrue(screen._restarting)
        self.assertEqual(screen._restart_timer.interval(), 3000)
        screen._restart_timer.stop()
        screen.deleteLater()

    def test_login_sleep_wakes_on_keyboard_and_shutdown_emits(self) -> None:
        screen = LoginScreen(sample_account())
        screen.show()
        self.qt_app.processEvents()
        shutdowns = []
        screen.shutdownRequested.connect(lambda: shutdowns.append(True))

        screen._choose_power_action("sleep")
        self.assertTrue(screen._sleeping)
        self.assertFalse(screen._controls.isVisible())
        event = QKeyEvent(
            QEvent.Type.KeyPress,
            Qt.Key.Key_A,
            Qt.KeyboardModifier.NoModifier,
        )
        self.qt_app.sendEvent(screen, event)
        self.assertFalse(screen._sleeping)
        self.assertTrue(screen._controls.isVisible())
        screen._choose_power_action("shutdown")
        self.assertEqual(shutdowns, [True])
        screen.deleteLater()
        screen.deleteLater()

    def test_desktop_start_menu_opens_local_notepad(self) -> None:
        desktop = DesktopPage(sample_account())
        desktop.resize(1280, 800)
        desktop.show()
        self.qt_app.processEvents()
        self.assertEqual(
            (desktop._source_wallpaper.width(), desktop._source_wallpaper.height()),
            (1920, 1200),
        )
        texture = desktop.mdi_area.background().texture()
        self.assertFalse(texture.isNull())
        self.assertEqual(
            (texture.width(), texture.height()),
            (
                desktop.mdi_area.viewport().width(),
                desktop.mdi_area.viewport().height(),
            ),
        )
        desktop.start_button.click()
        self.assertTrue(desktop.start_menu.isVisible())
        desktop.findChild(QPushButton, "start-programs").click()
        self.qt_app.processEvents()
        accessories_action = next(
            action
            for action in desktop._active_submenu.actions()
            if action.text() == "Accessories"
        )
        notepad_action = next(
            action
            for action in accessories_action.menu().actions()
            if action.text() == "Notepad"
        )
        notepad_action.trigger()
        self.qt_app.processEvents()
        self.assertIn("notepad", desktop._windows)
        self.assertFalse(desktop.start_menu.isVisible())
        desktop.close()
        desktop.deleteLater()

    def test_start_menu_uses_supplied_template_and_eight_commands(self) -> None:
        desktop = DesktopPage(sample_account())
        desktop.resize(960, 600)
        desktop.show()
        self.qt_app.processEvents()
        desktop.start_button.click()
        self.qt_app.processEvents()

        menu = desktop.start_menu
        self.assertTrue(menu.isVisible())
        self.assertEqual((menu.width(), menu.height()), (270, 267))
        self.assertEqual(len(desktop.start_menu_buttons), 8)
        self.assertEqual(desktop.start_button.icon().pixmap(60, 40).size(), QSize(60, 40))
        self.assertEqual(desktop.bar_transition.pixmap().size(), QSize(37, 40))
        for name in (
            "start-programs",
            "start-recent-items",
            "start-search",
            "start-options",
            "start-help-and-support",
            "start-run",
            "start-log-off",
            "shutdownButton",
        ):
            with self.subTest(button=name):
                self.assertIsNotNone(desktop.findChild(QPushButton, name))
        desktop.close()
        desktop.deleteLater()

    def test_start_menu_shutdown_button_emits_shutdown_request(self) -> None:
        desktop = DesktopPage(sample_account())
        requested = []
        desktop.shutdownRequested.connect(lambda: requested.append(True))
        shutdown = desktop.findChild(QPushButton, "shutdownButton")
        self.assertIsNotNone(shutdown)
        assert shutdown is not None
        shutdown.click()
        self.assertEqual(requested, [True])
        self.assertFalse(desktop.start_menu.isVisible())
        desktop.close()
        desktop.deleteLater()

    def test_start_menu_app_shortcuts_open_their_programs(self) -> None:
        desktop = DesktopPage(sample_account())
        desktop.resize(960, 600)
        desktop.show()
        self.qt_app.processEvents()

        for key, label in (
            ("directory", "Furry Directory"),
            ("messenger", "Windows Live Messenger"),
            ("computer", "Computer"),
        ):
            if not desktop.start_menu.isVisible():
                desktop.start_button.click()
            button = desktop.findChild(QPushButton, "start-programs")
            self.assertIsNotNone(button)
            assert button is not None
            button.click()
            self.qt_app.processEvents()
            action = next(
                action
                for action in desktop._active_submenu.actions()
                if action.text() == label
            )
            action.trigger()
            self.qt_app.processEvents()
            with self.subTest(app=key):
                self.assertIn(key, desktop._windows)
                self.assertFalse(desktop.start_menu.isVisible())

        for key, label in (
            ("notepad", "Notepad"),
            ("calculator", "Calculator"),
            ("paint", "Paint"),
            ("wordpad", "WordPad"),
        ):
            if not desktop.start_menu.isVisible():
                desktop.start_button.click()
            programs = desktop.findChild(QPushButton, "start-programs")
            assert programs is not None
            programs.click()
            self.qt_app.processEvents()
            accessories_action = next(
                action
                for action in desktop._active_submenu.actions()
                if action.text() == "Accessories"
            )
            accessory_menu = accessories_action.menu()
            action = next(
                action
                for action in accessory_menu.actions()
                if action.text() == label
            )
            action.trigger()
            self.qt_app.processEvents()
            with self.subTest(app=key):
                self.assertIn(key, desktop._windows)
                self.assertFalse(desktop.start_menu.isVisible())

        desktop.stop_session()
        desktop.close()
        desktop.deleteLater()

    def test_directory_and_messenger_browse_the_same_canonical_contacts(self) -> None:
        account = sample_account()
        service = ConnectionSimulator()
        directory = ProfileDirectoryApp(account)
        messenger = MessengerApp(account, service)

        directory_ids = [
            directory.profile_list.item(index).data(Qt.ItemDataRole.UserRole)
            for index in range(directory.profile_list.count())
        ]
        messenger_ids = [
            messenger.contact_list.item(index).data(Qt.ItemDataRole.UserRole)
            for index in range(messenger.contact_list.count())
        ]
        self.assertEqual(directory_ids, [contact.contact_id for contact in CONTACTS])
        self.assertEqual(messenger_ids, directory_ids)

        directory.profile_list.setCurrentRow(len(CONTACTS) - 1)
        messenger.contact_list.setCurrentRow(len(CONTACTS) - 1)
        self.assertEqual(directory.name.text(), CONTACTS[-1].display_name)
        self.assertEqual(
            directory.online_name.text(),
            f"Stable community ID: {CONTACTS[-1].contact_id}",
        )
        self.assertIs(messenger.selected_contact, CONTACTS[-1])

        directory.close()
        messenger.close()
        service.stop()
        service.deleteLater()

    def test_messenger_reports_outages_without_blocking_local_notepad(self) -> None:
        from win7_2011.win7sim.service import ServiceState

        desktop = DesktopPage(sample_account())
        desktop.resize(1280, 800)
        desktop.show()
        desktop.open_messenger()
        self.qt_app.processEvents()
        messenger = desktop._windows["messenger"].widget()
        self.assertIn("open ai settings", messenger.provider_status.text().lower())

        desktop.service.begin_interruption(ServiceState.MAINTENANCE, 60_000)
        self.qt_app.processEvents()
        self.assertIn("messaging is paused", messenger.provider_status.text().lower())
        self.assertFalse(messenger.send_button.isEnabled())

        desktop.open_notepad()
        self.qt_app.processEvents()
        self.assertIn("notepad", desktop._windows)
        desktop.stop_session()
        desktop.close()
        desktop.deleteLater()

    def test_first_run_routes_to_setup_without_touching_storage(self) -> None:
        with (
            patch("win7_2011.win7sim.application.ensure_storage_folders"),
            patch("win7_2011.win7sim.application.load_account", return_value=None),
        ):
            window = SimulationWindow()
            window._stage = "windows-start"
            window._continue_startup()
            self.assertIsInstance(window.stack.currentWidget(), SetupWizard)
            window.close()
            window.deleteLater()

    def test_desktop_login_refreshes_saved_ai_servers_once(self) -> None:
        account = sample_account()
        with (
            patch("win7_2011.win7sim.application.ensure_storage_folders"),
            patch("win7_2011.win7sim.application.load_account", return_value=None),
            patch("win7_2011.win7sim.application.save_account"),
            patch("win7_2011.win7sim.ai_service.AIService.reconnect") as reconnect,
        ):
            window = SimulationWindow()
            window.account = account
            window._start_desktop(account.active_profile_id)
            desktop = window.stack.currentWidget()
            self.qt_app.processEvents()

            reconnect.assert_called_once_with()
            self.assertIs(desktop.ai_service.parent(), desktop)
            desktop.stop_session()
            window._stage = "login"
            window._allow_close = True
            window.close()
            window.deleteLater()

    def test_startup_sound_is_queued_after_desktop_entry(self) -> None:
        account = sample_account()
        fake_winsound = SimpleNamespace(
            PlaySound=Mock(),
            SND_FILENAME=1,
            SND_ASYNC=2,
        )
        with (
            patch("win7_2011.win7sim.application.ensure_storage_folders"),
            patch("win7_2011.win7sim.application.load_account", return_value=None),
            patch("win7_2011.win7sim.application.save_account"),
            patch("win7_2011.win7sim.application.sys.platform", "win32"),
            patch.dict("sys.modules", {"winsound": fake_winsound}),
        ):
            window = SimulationWindow()
            bios_sound_path = (
                Path(__file__).resolve().parents[1]
                / "assets"
                / "bios"
                / "boot-post.wav"
            )
            fake_winsound.PlaySound.assert_called_once_with(
                str(bios_sound_path),
                fake_winsound.SND_FILENAME | fake_winsound.SND_ASYNC,
            )
            fake_winsound.PlaySound.reset_mock()
            window.account = account
            window._start_desktop(account.active_profile_id)
            self.qt_app.processEvents()

            sound_path = (
                Path(__file__).resolve().parents[1]
                / "assets"
                / "boot"
                / "windows-7-startup.wav"
            )
            startup_calls = [
                call
                for call in fake_winsound.PlaySound.call_args_list
                if call.args and call.args[0] == str(sound_path)
            ]
            self.assertEqual(len(startup_calls), 1)
            self.assertEqual(
                startup_calls[0].args,
                (
                    str(sound_path),
                    fake_winsound.SND_FILENAME | fake_winsound.SND_ASYNC,
                ),
            )
            fake_winsound.PlaySound.reset_mock()
            window._begin_shutdown()
            shutdown_sound_path = (
                Path(__file__).resolve().parents[1]
                / "assets"
                / "shutdown"
                / "windows-shutdown.wav"
            )
            fake_winsound.PlaySound.assert_called_once_with(
                str(shutdown_sound_path),
                fake_winsound.SND_FILENAME | fake_winsound.SND_ASYNC,
            )
            window._stage = "login"
            window.close()
            window.deleteLater()


if __name__ == "__main__":
    unittest.main()
