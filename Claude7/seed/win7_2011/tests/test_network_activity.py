"""Tests for the taskbar's simulated 2011 DSL traffic indicator."""

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from win7_2011.win7sim.network_activity import DSLNetworkTrayButton


class DSLNetworkActivityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.icon = DSLNetworkTrayButton()
        self.addCleanup(self.icon.deleteLater)

    def tearDown(self):
        self.app.processEvents()

    def test_transfer_time_uses_representative_2011_dsl_upload_and_download_rates(self):
        self.assertEqual(
            self.icon.estimated_transfer_seconds("incoming", 375_000), 1.0
        )
        self.assertEqual(
            self.icon.estimated_transfer_seconds("outgoing", 64_000), 1.0
        )

    def test_chat_transfers_blink_in_the_correct_direction_without_throttling(self):
        outgoing_duration = self.icon.report_transfer(
            "outgoing", 1_024, "MSN chat message"
        )
        self.assertAlmostEqual(outgoing_duration, 1_024 * 8 / 512_000)
        self.assertEqual(self.icon._events[-1]["direction"], "outgoing")
        self.assertTrue(self.icon.activity_timer.isActive())
        self.assertIn("Green = sending · Red = receiving", self.icon.toolTip())
        self.assertIn("MSN chat message", self.icon.toolTip())

        incoming_duration = self.icon.report_transfer(
            "incoming", 3_000, "MSN chat reply"
        )
        self.assertAlmostEqual(incoming_duration, 3_000 * 8 / 3_000_000)
        self.assertEqual(self.icon._events[-1]["direction"], "incoming")
        self.assertIn("Also: Receiving 2.9 KiB", self.icon.toolTip())
        self.assertIn("do not delay the app", self.icon.toolTip())

    def test_service_slowdown_reduces_simulated_rate_and_outages_stop_activity(self):
        normal = self.icon.estimated_transfer_seconds("incoming", 50_000)
        self.icon.set_connection_state("slowdown")
        slow = self.icon.estimated_transfer_seconds("incoming", 50_000)
        self.assertEqual(slow, normal * 2)
        self.assertIn("reduced simulated speed", self.icon.toolTip())

        self.icon.report_transfer("outgoing", 2_000, "Queued message")
        self.assertTrue(self.icon.activity_timer.isActive())
        self.icon.set_connection_state("disconnected")
        self.assertFalse(self.icon.connected)
        self.assertFalse(self.icon.activity_timer.isActive())
        self.assertEqual(self.icon._events, [])
        self.assertIn("Disconnected", self.icon.toolTip())
        self.assertAlmostEqual(
            self.icon.report_transfer("incoming", 100, "Offline"),
            100 * 8 / self.icon.DOWNLOAD_BITS_PER_SECOND,
        )

    def test_invalid_direction_and_negative_transfer_size_are_rejected(self):
        with self.assertRaises(ValueError):
            self.icon.estimated_transfer_seconds("sideways", 10)
        with self.assertRaises(ValueError):
            self.icon.estimated_transfer_seconds("incoming", -1)


if __name__ == "__main__":
    unittest.main()
