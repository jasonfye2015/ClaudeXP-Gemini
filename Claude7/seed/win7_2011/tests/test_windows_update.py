import os
import re
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from win7_2011.win7sim import config
from win7_2011.win7sim.windows_update import (
    UPDATE_CATALOG,
    WindowsUpdateApp,
    WindowsUpdateService,
)


class WindowsUpdateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.state_file = Path(self.temp.name) / "windows-update.json"
        self.state_path_patch = patch.object(
            config, "WINDOWS_UPDATE_STATE_FILE", self.state_file
        )
        self.state_path_patch.start()
        self.service = WindowsUpdateService(seed=17)

    def tearDown(self):
        self.service.stop_session()
        self.state_path_patch.stop()
        self.temp.cleanup()
        self.app.processEvents()

    def test_first_run_schedules_rare_updates_instead_of_starting_them(self):
        remaining = self.service.state["next_auto_check_at"] - time.time()
        self.assertTrue(14 * 24 * 60 * 60 <= remaining <= 28 * 24 * 60 * 60)
        self.assertTrue(self.service.automatic_enabled)
        self.assertFalse(self.service.running)
        self.assertTrue(self.service._auto_timer.isActive())

        self.service.set_automatic_enabled(False)
        saved = config.load_windows_update_state()
        self.assertFalse(saved["automatic_enabled"])

    def test_due_automatic_check_starts_one_batch_and_resets_its_cooldown(self):
        self.service.state["next_auto_check_at"] = time.time() - 1

        self.service._automatic_check_due()

        self.assertTrue(self.service.running)
        self.assertTrue(self.service.automatic_run)
        self.assertGreater(self.service.state["next_auto_check_at"], time.time())
        self.assertGreaterEqual(len(self.service.updates), 7)
        self.assertLessEqual(len(self.service.updates), 14)

    def test_catalog_contains_real_windows_7_x64_updates_released_in_2011(self):
        expected_kbs = {
            "2419640", "2425227", "2479943", "2483614", "2491683", "2506212",
            "2446709", "2510531", "2478661", "2478663", "2503665", "2532531",
            "2570947", "2564958", "2579686", "2506014", "2533623",
        }
        catalog_kbs = {
            re.search(r"\(KB(\d{7})\)", title).group(1)
            for title in UPDATE_CATALOG
        }

        self.assertGreater(len(UPDATE_CATALOG), 14)
        self.assertEqual(catalog_kbs, expected_kbs)
        self.assertEqual(len(UPDATE_CATALOG), len(catalog_kbs))
        for title in UPDATE_CATALOG:
            self.assertRegex(title, r" — 2011-\d{2}-\d{2}$")
            self.assertRegex(title, r"\(KB\d{7}\)")
        self.assertIn(
            "Security Update for Windows 7 for x64-based Systems "
            "(KB2503665) — 2011-06-14",
            UPDATE_CATALOG,
        )

    def test_random_batches_vary_within_the_2011_catalog_and_keep_batch_size(self):
        batches = set()
        for seed in range(20):
            service = WindowsUpdateService(seed=seed)
            try:
                self.assertTrue(service.start_updates())
                batch = tuple(service.updates)
                batches.add(frozenset(batch))
                self.assertGreaterEqual(len(batch), 7)
                self.assertLessEqual(len(batch), 14)
                self.assertEqual(len(batch), len(set(batch)))
                self.assertTrue(set(batch).issubset(UPDATE_CATALOG))
            finally:
                service.cancel_updates()
                service.stop_session()
        self.assertGreater(len(batches), 1)

    def test_manual_batch_queues_seven_to_fourteen_updates_and_maintenance(self):
        maintenance = []
        transfers = []
        self.service.maintenanceModeChanged.connect(maintenance.append)
        self.service.networkTransferRequested.connect(
            lambda direction, size, description: transfers.append(
                (direction, size, description)
            )
        )

        self.assertTrue(self.service.start_updates())
        self.assertGreaterEqual(len(self.service.updates), 7)
        self.assertLessEqual(len(self.service.updates), 14)
        self.assertEqual(self.service.stage, "downloading")
        self.assertEqual(maintenance, [True])
        self.assertEqual(transfers[0][0], "incoming")
        self.assertGreaterEqual(transfers[0][1], 512 * 1024)
        self.assertIn("Windows Update", transfers[0][2])
        self.assertEqual(
            self.service.state["pending_updates"],
            self.service.updates,
        )

        self.service.cancel_updates()
        self.assertFalse(self.service.running)
        self.assertIsNone(self.service.state["pending_updates"])
        self.assertEqual(maintenance, [True, False])

    def test_incomplete_batch_resumes_after_a_new_desktop_session(self):
        self.service.start_updates()
        original_updates = list(self.service.updates)
        original_stage = self.service.stage
        self.service.stop_session()

        resumed = WindowsUpdateService(seed=99)
        try:
            resumed._resume_timer.stop()
            self.assertTrue(resumed.has_pending_updates)
            self.assertEqual(resumed.updates, original_updates)
            self.assertEqual(resumed.stage, original_stage)
            self.assertTrue(resumed.start_updates())
            self.assertEqual(resumed.updates, original_updates)
            self.assertTrue(resumed.running)
            resumed.cancel_updates()
        finally:
            resumed.stop_session()

    def test_completed_batch_records_install_history_without_a_restart(self):
        self.service.PHASE_DURATION_MS = (1, 1)
        self.service.start_updates()
        phases = len(self.service.updates) * 2
        for _ in range(phases):
            self.service._phase_started_at -= 1
            self.service._tick()

        self.assertFalse(self.service.running)
        self.assertEqual(self.service.batch_progress, 100)
        self.assertEqual(self.service.state["completed_batches"], 1)
        self.assertEqual(
            self.service.state["last_installed_updates"],
            self.service.updates,
        )
        self.assertIsNone(self.service.state["pending_updates"])
        self.assertIn("No restart is required", self.service.status_message)

    def test_download_waits_for_broadband_without_holding_ai_maintenance_priority(self):
        maintenance = []
        transfers = []
        self.service.maintenanceModeChanged.connect(maintenance.append)
        self.service.networkTransferRequested.connect(
            lambda direction, size, description: transfers.append(direction)
        )
        self.service.set_network_available(False)

        self.service.start_updates()
        self.assertTrue(self.service.running)
        self.assertFalse(self.service._timer.isActive())
        self.assertFalse(self.service._maintenance_active)
        self.assertIn("Waiting for the broadband connection", self.service.status_message)
        self.assertFalse(transfers)

        self.service.set_network_available(True)
        self.assertTrue(self.service._timer.isActive())
        self.assertTrue(self.service._maintenance_active)
        self.assertEqual(transfers, ["incoming"])
        self.assertEqual(maintenance, [True])
        self.service.cancel_updates()

    def test_update_window_shows_selected_updates_and_manual_controls(self):
        window = WindowsUpdateApp(self.service)
        try:
            self.service.start_updates()
            self.app.processEvents()
            self.assertEqual(window.update_list.count(), len(self.service.updates))
            self.assertEqual(window.check_button.text(), "Checking for updates…")
            self.assertTrue(window.cancel_button.isEnabled())
            self.assertTrue(window.automatic_checkbox.isChecked())
            self.service.cancel_updates()
            self.app.processEvents()
            self.assertEqual(window.check_button.text(), "Check for updates")
        finally:
            window.close()
            window.deleteLater()
            self.app.processEvents()


if __name__ == "__main__":
    unittest.main()
