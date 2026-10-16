import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPoint, QSize, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QToolButton

from win7_2011.tests.test_ui import sample_account
from win7_2011.win7sim.desktop import DesktopPage


class StartShellTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.desktop = DesktopPage(sample_account())
        self.desktop.resize(960, 600)
        self.desktop.show()
        self.app.processEvents()

    def tearDown(self):
        self.desktop.stop_session()
        self.desktop.close()
        self.desktop.deleteLater()
        self.app.processEvents()

    def test_tray_grows_left_and_keeps_icons_clear_of_full_clock_text(self):
        desktop = self.desktop
        desktop.open_mush_client()
        self.app.processEvents()
        first_visible = next(
            desktop.tray_icon_layout.itemAt(i).widget()
            for i in range(desktop.tray_icon_layout.count())
            if not desktop.tray_icon_layout.itemAt(i).widget().isHidden()
        )
        self.assertIs(first_visible, desktop.defender_tray)
        for width in (28, 32, 36):
            icon = QToolButton(desktop.tray_icons)
            icon.setFixedSize(width, 30)
            desktop._add_tray_icon(icon)
            icon.show()
        self.app.processEvents()
        self.assertIs(desktop.tray_icon_layout.itemAt(0).widget(), icon)
        clock_x = desktop.clock_panel.mapTo(desktop.system_tray, QPoint(0, 0)).x()
        for button in desktop._tray_buttons:
            if button.isHidden():
                continue
            right = button.mapTo(desktop.system_tray, QPoint(button.width(), 0)).x()
            self.assertLessEqual(right + 14, clock_x)
        for label in (desktop.time_label, desktop.date_label):
            self.assertGreaterEqual(
                label.width(), label.fontMetrics().horizontalAdvance(label.text())
            )
        expanded_width = desktop.system_tray.width()
        icon.hide()
        self.app.processEvents()
        self.assertLess(desktop.system_tray.width(), expanded_width)
        self.assertEqual(
            desktop.system_tray.mapTo(desktop.taskbar, QPoint(desktop.system_tray.width(), 0)).x(),
            desktop.taskbar.width(),
        )

    def test_taskbar_template_toggles_minimize_restore(self):
        self.desktop.open_notepad()
        window = self.desktop._windows["notepad"]
        button = self.desktop._taskbar_buttons["notepad"]
        self.assertEqual(button.size(), QSize(60, 40))
        self.assertEqual(button.toolTip(), "Notepad")
        with patch.object(self.desktop, "_play_menu_sound") as sound:
            button.click()
            self.assertTrue(window.isMinimized())
            sound.assert_called_with("Windows Minimize.wav")
            button.click()
            self.assertFalse(window.isMinimized())
            sound.assert_called_with("Windows Restore.wav")

    def test_outside_click_dismisses_menu(self):
        self.desktop.start_button.click()
        self.assertTrue(self.desktop.start_menu.isVisible())
        QTest.mouseClick(
            self.desktop.mdi_area.viewport(), Qt.MouseButton.LeftButton,
            pos=QPoint(600, 100),
        )
        self.assertFalse(self.desktop.start_menu.isVisible())

    def test_logoff_command_emits_signal(self):
        logoffs = []
        self.desktop.logOffRequested.connect(lambda: logoffs.append(True))
        self.desktop.start_button.click()
        self.desktop.start_menu_buttons["Log Off"].click()
        self.assertEqual(logoffs, [True])
