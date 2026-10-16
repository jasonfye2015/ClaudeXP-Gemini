import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QCoreApplication, QEvent, QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from win7_2011.tests.test_ui import sample_account
from win7_2011.win7sim.desktop import DesktopPage
from win7_2011.win7sim.shell import (
    RecycleBinError, RecycleBinStore, WindowsComputerApp,
)


class RecycleBinTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.documents = self.root / "Documents"
        self.media = self.root / "Media"
        self.documents.mkdir()
        self.media.mkdir()
        self.store = RecycleBinStore(
            bin_root=self.root / "Recycle Bin",
            allowed_roots=(self.documents, self.media),
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_move_to_bin_updates_full_state_and_restore_never_overwrites(self):
        states = []
        self.store.changed.connect(states.append)
        original = self.documents / "Notes.txt"
        original.write_text("older contents", encoding="utf-8")
        entry = self.store.move_to_bin(original)
        self.assertTrue(states[-1])
        self.assertEqual(self.store.entries()[0]["id"], entry["id"])

        original.write_text("newer contents", encoding="utf-8")
        restored = self.store.restore(entry["id"])
        self.assertEqual(restored.name, "Notes (2).txt")
        self.assertEqual(original.read_text(encoding="utf-8"), "newer contents")
        self.assertEqual(restored.read_text(encoding="utf-8"), "older contents")
        self.assertFalse(self.store.entries())
        self.assertFalse(states[-1])

    def test_empty_permanently_removes_selected_items_only(self):
        first = self.media / "first.txt"
        second = self.media / "second.txt"
        first.write_text("1", encoding="utf-8")
        second.write_text("2", encoding="utf-8")
        first_entry = self.store.move_to_bin(first)
        second_entry = self.store.move_to_bin(second)
        self.store.empty([first_entry["id"]])
        self.assertEqual(len(self.store.entries()), 1)
        self.assertFalse((self.store.items_root / first_entry["id"]).exists())
        self.assertTrue((self.store.items_root / second_entry["id"]).exists())
        self.store.empty()
        self.assertFalse(self.store.entries())

    def test_system_and_out_of_scope_paths_are_protected(self):
        protected = self.root / "Windows" / "settings.ini"
        protected.parent.mkdir()
        protected.write_text("keep", encoding="utf-8")
        with self.assertRaises(RecycleBinError):
            self.store.move_to_bin(protected)


class DesktopShellTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.desktop = DesktopPage(sample_account())
        self.desktop.resize(1000, 680)
        self.desktop.show()
        self.app.processEvents()

    def tearDown(self):
        self.desktop.stop_session()
        self.desktop.close()
        self.desktop.deleteLater()
        self.app.processEvents()

    def test_six_shortcuts_are_arranged_left_and_welcome_note_is_top_right(self):
        self.assertEqual(
            list(self.desktop.desktop_shortcuts),
            ["Recycle Bin", "Desktop", "Firefox", "MSN Messenger", "MushClient", "IRC Client"],
        )
        buttons = list(self.desktop.desktop_shortcuts.values())
        self.assertEqual(len({button.x() for button in buttons}), 1)
        for button in buttons:
            self.assertFalse(button.icon().isNull())
        self.assertGreater(
            self.desktop.welcome_note.x(), self.desktop.mdi_area.viewport().width() // 2
        )
        self.assertGreaterEqual(self.desktop.welcome_note.y(), 0)

    def test_screen_saver_settings_are_in_options(self):
        tab_names = [
            self.desktop.options_window.tabs.tabText(index)
            for index in range(self.desktop.options_window.tabs.count())
        ]
        self.assertIn("Screen Saver", tab_names)
        page = self.desktop.options_window.screen_saver_page
        self.assertEqual(page.saver_combo.currentData(), "bubbles")
        self.assertEqual(page.wait_combo.currentData(), 300)

    def test_mush_desktop_icon_is_upscaled_to_match_the_other_shortcuts(self):
        icon = self.desktop.desktop_shortcuts["MushClient"].icon()
        rendered = icon.pixmap(64, 64)
        self.assertEqual((rendered.width(), rendered.height()), (64, 64))

    def test_maintenance_apps_load_and_share_background_ai_priority(self):
        tray = self.desktop.defender_tray
        self.assertIn(tray, self.desktop._tray_buttons)
        visible_tray_icons = [
            self.desktop.tray_icon_layout.itemAt(index).widget()
            for index in range(self.desktop.tray_icon_layout.count())
            if self.desktop.tray_icon_layout.itemAt(index).widget().isVisible()
        ]
        self.assertIs(visible_tray_icons[0], tray)
        self.assertTrue(tray.isVisible())
        self.assertFalse(self.desktop.defender.scan_running)
        self.assertNotIn("windows-defender", self.desktop._windows)
        actions = [
            action.text()
            for action in self.desktop._build_accessories_menu().actions()
        ]
        self.assertIn("Windows Defender", actions)
        self.assertIn("Disk Defragmenter", actions)
        tray.open_action.trigger()
        self.app.processEvents()
        self.assertIn("windows-defender", self.desktop._windows)

        self.desktop.defender.start_scan("quick", duration_ms=1_000)
        self.assertTrue(self.desktop.ai_service.maintenance_priority_mode)
        self.desktop.open_disk_defragmenter()
        self.app.processEvents()
        self.assertIn("disk-defragmenter", self.desktop._windows)
        self.assertTrue(self.desktop.defragmenter.running)
        self.desktop.open_windows_update()
        self.app.processEvents()
        self.assertIn("windows-update", self.desktop._windows)
        self.desktop.windows_update.start_updates()
        self.assertTrue(self.desktop.ai_service.maintenance_priority_mode)
        self.assertEqual(
            self.desktop.network_tray._last_transfer["direction"],
            "incoming",
        )
        self.desktop.defender.cancel_scan()
        self.assertTrue(self.desktop.ai_service.maintenance_priority_mode)
        self.desktop._windows["disk-defragmenter"].close()
        self.app.processEvents()
        self.assertTrue(self.desktop.ai_service.maintenance_priority_mode)
        self.desktop.windows_update.cancel_updates()
        self.assertFalse(self.desktop.ai_service.maintenance_priority_mode)

    def test_torrent_client_runs_from_taskbar_until_exited(self):
        client = self.desktop.open_torrent_client()
        self.app.processEvents()
        service = self.desktop.torrent_client_service
        self.assertEqual(client.torrent_table.rowCount(), 12)
        self.assertIsNotNone(service)
        self.assertTrue(self.desktop.torrent_tray.isVisible())
        visible_tray_icons = [
            self.desktop.tray_icon_layout.itemAt(index).widget()
            for index in range(self.desktop.tray_icon_layout.count())
            if self.desktop.tray_icon_layout.itemAt(index).widget().isVisible()
        ]
        self.assertIs(visible_tray_icons[0], self.desktop.torrent_tray)
        self.assertTrue(service.started)

        self.desktop.torrent_tray.pause_action.trigger()
        self.assertTrue(service.paused)
        self.desktop.torrent_tray.resume_action.trigger()
        self.assertFalse(service.paused)

        self.desktop.close_torrent_client_window()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()
        self.assertNotIn("torrent-client", self.desktop._windows)
        self.assertFalse(self.desktop.torrent_tray.close_window_action.isEnabled())
        self.assertTrue(self.desktop.torrent_tray.isVisible())
        self.desktop.torrent_tray.open_action.trigger()
        self.app.processEvents()
        self.assertIn("torrent-client", self.desktop._windows)

        self.desktop.torrent_tray.exit_action.trigger()
        self.app.processEvents()
        self.assertFalse(self.desktop.torrent_tray.isVisible())
        self.assertIsNone(self.desktop.torrent_client_service)

    def test_desktop_shortcut_opens_the_five_supplied_drive_icons(self):
        shortcut = self.desktop.desktop_shortcuts["Desktop"]
        QTest.mouseDClick(shortcut, Qt.MouseButton.LeftButton, pos=shortcut.rect().center())
        self.app.processEvents()
        window = self.desktop._windows["desktop-folder"]
        computer = window.widget()
        self.assertIsInstance(computer, WindowsComputerApp)
        self.assertEqual(
            [computer.drive_list.item(i).text() for i in range(computer.drive_list.count())],
            ["CD Rom Drive (D:)", "DVD Drive (E:)", "Floppy Drive (A:)",
             "External HD (F:)", "Internal HD (C:)"],
        )
        self.assertTrue(
            all(
                not computer.drive_list.item(i).icon().isNull()
                for i in range(computer.drive_list.count())
            )
        )

    def test_recycle_bin_right_click_menu_disables_empty_actions_when_empty(self):
        shortcut = self.desktop.desktop_shortcuts["Recycle Bin"]
        self.assertEqual(
            shortcut.contextMenuPolicy(),
            Qt.ContextMenuPolicy.CustomContextMenu,
        )
        menu = self.desktop._build_desktop_shortcut_menu("Recycle Bin", shortcut)
        actions = menu.actions()
        self.assertEqual(
            [action.text() for action in actions if not action.isSeparator()],
            ["Open", "Restore all items", "Empty Recycle Bin", "Properties"],
        )
        self.assertFalse(actions[1].isEnabled())
        self.assertFalse(actions[2].isEnabled())
        menu.close()
        menu.deleteLater()
        self.app.processEvents()

    def test_firefox_shows_the_requested_not_implemented_message(self):
        with patch("win7_2011.win7sim.desktop.QMessageBox.information") as show:
            self.desktop.open_firefox_placeholder()
        show.assert_called_once_with(
            self.desktop, "Firefox", "Feature not implemented yet."
        )

    def test_recycle_bin_shortcut_icon_tracks_file_and_restore_state(self):
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        documents = root / "Documents"
        documents.mkdir()
        test_bin = root / "Bin"
        store = RecycleBinStore(bin_root=test_bin, allowed_roots=(documents,))
        self.desktop.recycle_bin_store = store
        store.changed.connect(self.desktop._update_recycle_bin_icon)
        item = documents / "example.txt"
        item.write_text("safe", encoding="utf-8")
        entry = store.move_to_bin(item)
        button = self.desktop.desktop_shortcuts["Recycle Bin"]
        self.assertIn("contains deleted items", button.toolTip())
        store.restore(entry["id"])
        self.assertEqual(button.toolTip(), "Recycle Bin — empty")


if __name__ == "__main__":
    unittest.main()
