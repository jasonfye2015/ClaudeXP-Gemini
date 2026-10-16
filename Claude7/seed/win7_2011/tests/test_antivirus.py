import unittest

from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from win7_2011.win7sim.antivirus import (
    WindowsDefenderApp,
    WindowsDefenderService,
    WindowsDefenderTrayButton,
)


class SimulatedWindowsDefenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_quick_scan_is_timed_and_reports_only_simulated_items(self):
        service = WindowsDefenderService()
        maintenance_states = []
        completed = []
        service.maintenanceModeChanged.connect(maintenance_states.append)
        service.scanFinished.connect(lambda *args: completed.append(args))
        app = WindowsDefenderApp(service)
        self.assertTrue(app.progress_bar.isHidden())
        service.start_scan("quick", duration_ms=120)
        self.assertTrue(service.scan_running)
        self.assertFalse(app.progress_bar.isHidden())
        self.assertEqual(maintenance_states, [True])
        self.assertIn("no files are read", service.status_message)
        QTest.qWait(240)
        self.app.processEvents()

        self.assertFalse(service.scan_running)
        self.assertEqual(maintenance_states, [True, False])
        self.assertEqual(completed, [("quick", 6_200)])
        self.assertIn("simulated items checked", service.last_result)
        self.assertIn("no threats found (simulation)", service.last_result)
        self.assertEqual(service.progress, 100)
        self.assertIn("6,200 simulated items", app.detail_label.text())
        app.close()
        service.deleteLater()
        app.deleteLater()
        self.app.processEvents()

    def test_cancel_stops_scan_and_releases_ai_maintenance_mode(self):
        service = WindowsDefenderService()
        maintenance_states = []
        service.maintenanceModeChanged.connect(maintenance_states.append)
        service.start_scan("full", duration_ms=2_000)
        service.cancel_scan()

        self.assertFalse(service.scan_running)
        self.assertEqual(maintenance_states, [True, False])
        self.assertIn("canceled", service.status_message)
        service.deleteLater()
        self.app.processEvents()

    def test_tray_menu_exposes_open_scan_update_and_about_actions(self):
        service = WindowsDefenderService()
        tray = WindowsDefenderTrayButton(service)
        opened = []
        about = []
        tray.openRequested.connect(lambda: opened.append(True))
        tray.aboutRequested.connect(lambda: about.append(True))

        self.assertEqual(
            [action.text() for action in tray.context_menu.actions()],
            [
                "Open Windows Defender", "",
                "Quick scan", "Full scan", "Cancel scan", "",
                "Check for updates", "About Windows Defender",
            ],
        )
        tray.open_action.trigger()
        tray.quick_scan_action.trigger()
        self.assertTrue(service.scan_running)
        self.assertTrue(tray.cancel_scan_action.isEnabled())
        tray.cancel_scan_action.trigger()
        tray.update_action.trigger()
        tray.about_action.trigger()

        self.assertEqual(opened, [True])
        self.assertEqual(about, [True])
        self.assertIn("up to date (simulation)", service.status_message)
        self.assertFalse(service.scan_running)
        tray.close()
        tray.deleteLater()
        service.deleteLater()
        self.app.processEvents()


if __name__ == "__main__":
    unittest.main()
