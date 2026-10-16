import json
import unittest
from pathlib import Path
import tempfile
from unittest.mock import patch

from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from win7_2011.win7sim import config
from win7_2011.win7sim.defragmenter import (
    DefragmenterService,
    DiskDefragmenterApp,
)


class DiskDefragmenterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self._settings_temp = tempfile.TemporaryDirectory()
        self.settings_dir = Path(self._settings_temp.name) / "Disk Defragmenter"
        self.settings_file = self.settings_dir / "settings.json"
        self._settings_dir_patch = patch.object(
            config, "DEFRAGMENTER_SETTINGS_DIR", self.settings_dir
        )
        self._settings_file_patch = patch.object(
            config, "DEFRAGMENTER_SETTINGS_FILE", self.settings_file
        )
        self._settings_dir_patch.start()
        self._settings_file_patch.start()

    def tearDown(self):
        self._settings_file_patch.stop()
        self._settings_dir_patch.stop()
        self._settings_temp.cleanup()

    def test_timing_choices_are_saved_and_restored(self):
        first = DefragmenterService(seed=18)
        first.set_cycle_duration_ms(65_000)
        first.set_reset_pause_ms(2_700)
        first.deleteLater()

        restarted = DefragmenterService(seed=19)
        try:
            self.assertEqual(restarted.cycle_duration_ms, 65_000)
            self.assertEqual(restarted.reset_pause_ms, 2_700)
        finally:
            restarted.deleteLater()
            self.app.processEvents()

    def test_missing_or_older_settings_use_defaults_for_missing_values(self):
        defaults = {
            "cycle_duration_ms": DefragmenterService.CYCLE_DURATION_MS,
            "reset_pause_ms": DefragmenterService.RESET_PAUSE_MS,
        }
        self.assertEqual(config.load_defragmenter_settings(defaults), defaults)

        self.settings_dir.mkdir(parents=True)
        self.settings_file.write_text(
            json.dumps({"reset_pause_ms": 2_500}), encoding="utf-8"
        )
        self.assertEqual(
            config.load_defragmenter_settings(defaults),
            {"cycle_duration_ms": defaults["cycle_duration_ms"], "reset_pause_ms": 2_500},
        )

    def test_restored_timing_choices_are_clamped_to_supported_limits(self):
        self.settings_dir.mkdir(parents=True)
        self.settings_file.write_text(
            json.dumps({"cycle_duration_ms": 1, "reset_pause_ms": 99_000}),
            encoding="utf-8",
        )
        restored = config.load_defragmenter_settings()
        self.assertEqual(
            restored,
            {
                "cycle_duration_ms": DefragmenterService.MIN_CYCLE_DURATION_MS,
                "reset_pause_ms": DefragmenterService.MAX_RESET_PAUSE_MS,
            },
        )

    def test_full_drive_map_consolidates_then_restarts_messy(self):
        with (
            patch.object(DefragmenterService, "CYCLE_DURATION_MS", 1_000),
            patch.object(DefragmenterService, "RESET_PAUSE_MS", 300),
        ):
            service = DefragmenterService(seed=31)
            original_layout = tuple(service.cells)
            maintenance_states = []
            service.maintenanceModeChanged.connect(maintenance_states.append)
            app = DiskDefragmenterApp(service)

            self.assertEqual(len(original_layout), 80 * 44)
            self.assertEqual(app.disk_map.sizeHint().width(), 790)
            self.assertGreater(service.fragmented_blocks, 0)

            service.start()
            self.assertTrue(service.running)
            self.assertEqual(maintenance_states, [True])
            while service.running and service.progress < 100:
                service._tick()
            self.app.processEvents()

            self.assertEqual(service.progress, 100)
            self.assertEqual(service.completed_passes, 1)
            self.assertEqual(service.fragmented_blocks, 0)
            self.assertEqual(maintenance_states, [True])
            app.reset_pause_control.setValue(0.5)
            self.assertEqual(service.reset_pause_ms, 500)
            self.assertEqual(service._reset_timer.interval(), 500)
            self.assertTrue(service._reset_timer.isActive())
            QTest.qWait(540)
            self.app.processEvents()

            self.assertTrue(service.running)
            self.assertLess(service.progress, 100)
            self.assertGreater(service.fragmented_blocks, 0)
            self.assertNotEqual(tuple(service.cells), original_layout)
            self.assertEqual(maintenance_states, [True])

            service.pause()
            self.assertFalse(service.running)
            self.assertTrue(service.paused)
            self.assertEqual(maintenance_states, [True, False])
            service.stop()
            app.close()
            service.deleteLater()
            self.app.processEvents()

    def test_closing_defragmenter_stops_maintenance_mode(self):
        service = DefragmenterService(seed=8)
        app = DiskDefragmenterApp(service)
        service.start()
        app.show()
        self.app.processEvents()

        app.close()
        self.app.processEvents()
        self.assertFalse(service.running)
        self.assertFalse(service.paused)
        self.assertEqual(service.progress, 0)
        self.assertIn("Stopped", service.status_message)
        service.deleteLater()
        self.app.processEvents()

    def test_timing_controls_enforce_minimum_and_maximum(self):
        service = DefragmenterService(seed=12)
        app = DiskDefragmenterApp(service)
        try:
            service.set_cycle_duration_ms(0)
            service.set_reset_pause_ms(0)
            self.assertEqual(
                service.cycle_duration_ms, service.MIN_CYCLE_DURATION_MS
            )
            self.assertEqual(service.reset_pause_ms, service.MIN_RESET_PAUSE_MS)
            self.assertEqual(
                app.pass_duration_control.value(),
                service.MIN_CYCLE_DURATION_MS / 1000,
            )
            self.assertEqual(
                app.reset_pause_control.value(),
                service.MIN_RESET_PAUSE_MS / 1000,
            )

            service.set_cycle_duration_ms(service.MAX_CYCLE_DURATION_MS + 1)
            service.set_reset_pause_ms(service.MAX_RESET_PAUSE_MS + 1)
            self.assertEqual(
                service.cycle_duration_ms, service.MAX_CYCLE_DURATION_MS
            )
            self.assertEqual(service.reset_pause_ms, service.MAX_RESET_PAUSE_MS)
            self.assertEqual(
                app.pass_duration_control.value(),
                service.MAX_CYCLE_DURATION_MS / 1000,
            )
            self.assertEqual(
                app.reset_pause_control.value(),
                service.MAX_RESET_PAUSE_MS / 1000,
            )
        finally:
            app.close()
            service.deleteLater()
            self.app.processEvents()

    def test_drive_selection_keeps_repeatable_layouts_and_progress_separate(self):
        clock = [100.0]
        with patch(
            "win7_2011.win7sim.defragmenter.time.monotonic",
            side_effect=lambda: clock[0],
        ):
            service = DefragmenterService(seed=71)
            service.set_cycle_duration_ms(40_000)
            app = DiskDefragmenterApp(service)
            try:
                c_layout = tuple(service.cells)
                self.assertEqual(app.drive_selector.count(), 2)
                self.assertEqual(app.drive_selector.currentData(), "C:")
                service.start()
                clock[0] += 10
                service._tick()
                self.assertEqual(service.progress, 25)
                c_progress_layout = tuple(service.cells)

                app.drive_selector.setCurrentIndex(1)
                f_layout = tuple(service.cells)
                self.assertEqual(service.selected_drive, "F:")
                self.assertEqual(service.progress, 0)
                self.assertNotEqual(f_layout, c_layout)

                clock[0] += 20
                service._tick()
                self.assertEqual(service.progress, 50)
                self.assertEqual(app.progress_bar.value(), 50)
                app.drive_selector.setCurrentIndex(0)
                self.assertEqual(service.selected_drive, "C:")
                self.assertEqual(service.progress, 25)
                self.assertEqual(app.progress_bar.value(), 25)
                self.assertEqual(tuple(service.cells), c_progress_layout)

                app.drive_selector.setCurrentIndex(1)
                service.stop()
                self.assertEqual(service.progress, 0)
                self.assertEqual(tuple(service.cells), f_layout)
                app.drive_selector.setCurrentIndex(0)
                self.assertEqual(service.progress, 25)
                self.assertEqual(tuple(service.cells), c_progress_layout)
            finally:
                app.close()
                service.deleteLater()
                self.app.processEvents()

    def test_pass_duration_changes_preserve_progress_running_and_paused(self):
        service = DefragmenterService(seed=13)
        app = DiskDefragmenterApp(service)
        try:
            service.start()
            for _ in range(200):
                service._tick()
            settled_before_change = service._settled_cells
            progress_before_change = service.progress
            interval_before_change = service._timer.interval()

            app.pass_duration_control.setValue(80.0)
            self.assertEqual(service.cycle_duration_ms, 80_000)
            self.assertEqual(service.progress, progress_before_change)
            self.assertEqual(service._settled_cells, settled_before_change)
            self.assertGreater(service._timer.interval(), interval_before_change)

            service._tick()
            self.assertGreater(service._settled_cells, settled_before_change)
            service.pause()
            settled_while_paused = service._settled_cells

            app.pass_duration_control.setValue(20.0)
            self.assertEqual(
                service.cycle_duration_ms, service.MIN_CYCLE_DURATION_MS
            )
            self.assertEqual(service._settled_cells, settled_while_paused)

            service.start()
            service._tick()
            self.assertGreater(service._settled_cells, settled_while_paused)
        finally:
            app.close()
            service.deleteLater()
            self.app.processEvents()

    def test_time_remaining_tracks_progress_duration_and_non_countdown_states(self):
        service = DefragmenterService(seed=23)
        try:
            service.set_cycle_duration_ms(40_000)
            self.assertIsNone(service.estimated_remaining_ms)
            self.assertEqual(service.time_remaining_text, "Ready — no countdown.")

            service.start()
            initial_estimate = service.estimated_remaining_ms
            self.assertEqual(initial_estimate, 40_000)
            self.assertEqual(
                service.time_remaining_text,
                "Estimated time remaining: 40s",
            )

            for _ in range(100):
                service._tick()
            progress_estimate = service.estimated_remaining_ms
            self.assertLess(progress_estimate, initial_estimate)
            self.assertIn(
                "Estimated time remaining:",
                service.time_remaining_text,
            )

            service.set_cycle_duration_ms(80_000)
            duration_estimate = service.estimated_remaining_ms
            self.assertGreater(duration_estimate, progress_estimate)
            self.assertIn(
                "Estimated time remaining:",
                service.time_remaining_text,
            )

            service.pause()
            self.assertIsNone(service.estimated_remaining_ms)
            self.assertEqual(
                service.time_remaining_text,
                "Paused — countdown stopped.",
            )

            service.start()
            service._finish_pass()
            self.assertIsNone(service.estimated_remaining_ms)
            self.assertEqual(
                service.time_remaining_text,
                "Pass complete — preparing the next pass (no countdown).",
            )
            self.assertNotIn(
                "Estimated time remaining:",
                service.time_remaining_text,
            )
        finally:
            service.stop()
            service.deleteLater()
            self.app.processEvents()

    def test_ticks_move_one_to_five_blocks_and_usually_only_one(self):
        service = DefragmenterService(seed=29)
        try:
            service.start()
            moved_per_tick = []
            for _ in range(1_000):
                before = service._settled_cells
                service._tick()
                moved_per_tick.append(service._settled_cells - before)

            self.assertGreaterEqual(min(moved_per_tick), 1)
            self.assertLessEqual(max(moved_per_tick), 5)
            self.assertGreaterEqual(
                moved_per_tick.count(1), 650,
                "A one-block update should be the common case.",
            )
        finally:
            service.stop()
            service.deleteLater()
            self.app.processEvents()


if __name__ == "__main__":
    unittest.main()
