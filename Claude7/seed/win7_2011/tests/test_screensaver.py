from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from win7_2011.win7sim import config
from win7_2011.win7sim.screensaver import (
    IdleScreenSaverController,
    ScreenSaverOverlay,
    ScreenSaverSettingsPage,
)


class ScreenSaverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        root = Path(self.temporary.name)
        self.settings_dir = root / "UserData" / "Screen Saver"
        self.settings_file = self.settings_dir / "settings.json"
        self.settings_file_patch = patch.object(
            config, "SCREEN_SAVER_SETTINGS_FILE", self.settings_file
        )
        self.settings_dir_patch = patch.object(
            config, "SCREEN_SAVER_SETTINGS_DIR", self.settings_dir
        )
        self.settings_file_patch.start()
        self.settings_dir_patch.start()
        self.addCleanup(self.settings_file_patch.stop)
        self.addCleanup(self.settings_dir_patch.stop)
        self.controllers = []
        self.pages = []

    def make_controller(self):
        controller = IdleScreenSaverController()
        self.controllers.append(controller)
        self.addCleanup(controller.deleteLater)
        self.addCleanup(controller.stop_session)
        return controller

    def test_settings_default_save_reload_and_validation(self):
        self.assertEqual(
            config.load_screen_saver_settings(),
            {"saver": "bubbles", "timeout_seconds": 300},
        )
        controller = self.make_controller()
        page = ScreenSaverSettingsPage(controller)
        self.pages.append(page)
        self.addCleanup(page.deleteLater)

        page.saver_combo.setCurrentIndex(page.saver_combo.findData("mystify"))
        page.wait_combo.setCurrentIndex(page.wait_combo.findData(600))
        page.apply_button.click()

        self.assertEqual(
            config.load_screen_saver_settings(),
            {"saver": "mystify", "timeout_seconds": 600},
        )
        self.assertTrue(controller.idle_timer.isActive())
        with self.assertRaises(ValueError):
            config.save_screen_saver_settings(
                {"saver": "unknown", "timeout_seconds": 60}
            )

    def test_idle_timer_launches_saver_and_a_key_returns_to_desktop(self):
        controller = self.make_controller()
        controller.idle_timer.start(25)
        QTest.qWait(70)
        self.app.processEvents()
        self.assertTrue(controller.active)
        self.assertIsNotNone(controller._overlay)

        QTest.keyClick(controller._overlay, Qt.Key.Key_Escape)
        self.app.processEvents()
        self.assertFalse(controller.active)
        self.assertTrue(controller.idle_timer.isActive())

    def test_bubbles_and_mystify_render_as_full_screen_savers(self):
        for saver in ("bubbles", "mystify"):
            overlay = ScreenSaverOverlay(saver)
            overlay.resize(720, 405)
            overlay.show()
            QTest.qWait(50)
            image = overlay.grab().toImage()
            self.assertFalse(image.isNull())
            self.assertEqual(overlay.windowTitle(), f"{saver.title()} Screen Saver")
            overlay.stop_animation()
            overlay.close()
            overlay.deleteLater()
            self.app.processEvents()

    def test_format_reinstall_clears_saved_screen_saver_choice(self):
        config.save_screen_saver_settings(
            {"saver": "mystify", "timeout_seconds": 900}
        )
        root = Path(self.temporary.name) / "format-storage"
        replacements = {
            "STORAGE_ROOT": root,
            "ACCOUNT_FILE": root / "System" / "account.json",
            "USER_PROFILES": root / "Profiles",
            "USER_DOCUMENTS": root / "UserData" / "Documents",
            "MESSENGER_HISTORY": root / "UserData" / "Messenger",
            "STICKY_NOTES": root / "UserData" / "Sticky Notes",
            "MEDIA_PLAYLISTS": root / "UserData" / "Media Player Playlists",
            "SCREEN_SAVER_SETTINGS_DIR": root / "UserData" / "Screen Saver",
            "SCREEN_SAVER_SETTINGS_FILE": (
                root / "UserData" / "Screen Saver" / "settings.json"
            ),
        }
        with patch.multiple(config, **replacements):
            config.save_screen_saver_settings(
                {"saver": "mystify", "timeout_seconds": 900}
            )
            config.reset_user_data()
            self.assertFalse(config.SCREEN_SAVER_SETTINGS_FILE.exists())
            self.assertEqual(
                config.load_screen_saver_settings(),
                {"saver": "bubbles", "timeout_seconds": 300},
            )


if __name__ == "__main__":
    unittest.main()
