import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication

from win7_2011.win7sim.torrent_client import (
    TorrentClientApp,
    TorrentClientService,
    TorrentTrayButton,
)


class TorrentClientTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.service = TorrentClientService(seed=17)

    def tearDown(self):
        self.service.stop_session()
        if getattr(self, "window", None) is not None:
            self.window.close()
            self.window.deleteLater()
        if getattr(self, "tray", None) is not None:
            self.tray.deactivate()
            self.tray.deleteLater()
        self.service.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()

    def test_starts_with_twelve_period_plausible_incomplete_items(self):
        self.assertEqual(len(self.service.torrents), 12)
        self.assertEqual(
            len({torrent.progress for torrent in self.service.torrents}), 12
        )
        self.assertTrue(all(0 < torrent.progress < 100 for torrent in self.service.torrents))
        extensions = {
            torrent.name.rsplit(".", 1)[-1].lower()
            for torrent in self.service.torrents
        }
        self.assertTrue(
            {"iso", "zip", "rar", "pdf", "avi", "mp3"}.issubset(extensions)
        )

    def test_transfer_rates_progress_and_network_events_are_simulated(self):
        transfers = []
        activities = []
        self.service.networkTransferRequested.connect(
            lambda direction, byte_count, description: transfers.append(
                (direction, byte_count, description)
            )
        )
        self.service.activityChanged.connect(
            lambda down, up: activities.append((down, up))
        )
        self.service.start()
        initial_progress = [torrent.progress for torrent in self.service.torrents]
        self.service._update_speeds(2.0)

        self.assertEqual(len(self.service.torrents), 12)
        self.assertGreater(
            sum(torrent.download_kib for torrent in self.service.torrents), 0
        )
        self.assertLessEqual(
            sum(torrent.download_kib for torrent in self.service.torrents),
            self.service.DOWNLOAD_LIMIT_KIB,
        )
        self.assertLessEqual(
            sum(torrent.upload_kib for torrent in self.service.torrents),
            self.service.UPLOAD_LIMIT_KIB,
        )
        self.assertTrue(
            any(
                torrent.progress > before
                for torrent, before in zip(
                    self.service.torrents, initial_progress, strict=True
                )
            )
        )
        self.assertEqual({direction for direction, _, _ in transfers}, {
            "incoming",
            "outgoing",
        })
        self.assertTrue(all(size > 0 for _, size, _ in transfers))
        self.assertTrue(all("simulated" in note for _, _, note in transfers))
        self.assertEqual(activities[-1], (True, True))

    def test_pause_resume_and_network_loss_stop_fake_transfer_activity(self):
        self.service.start()
        self.service._update_speeds(1.0)
        self.service.pause_all()
        paused_progress = [torrent.progress for torrent in self.service.torrents]
        self.assertTrue(self.service.paused)
        self.assertTrue(all(
            torrent.download_kib == 0 and torrent.upload_kib == 0
            for torrent in self.service.torrents
        ))
        self.service._update_speeds(10.0)
        self.assertEqual(
            [torrent.progress for torrent in self.service.torrents], paused_progress
        )

        self.service.resume_all()
        self.assertFalse(self.service.paused)
        self.assertTrue(self.service._timer.isActive())
        self.service.set_network_available(False)
        self.assertFalse(self.service._timer.isActive())
        self.assertIn("Waiting", self.service.status_text)
        self.assertTrue(all(
            torrent.download_kib == 0 and torrent.upload_kib == 0
            for torrent in self.service.torrents
        ))
        self.service.set_network_available(True)
        self.assertTrue(self.service._timer.isActive())

    def test_download_completion_changes_to_seeding(self):
        self.service.start()
        torrent = self.service.torrents[0]
        torrent.progress = 99.999
        self.service._update_speeds(120)
        self.assertEqual(torrent.progress, 100)
        self.assertEqual(self.service.seeding_count, 1)

    def test_window_and_taskbar_menu_control_the_same_client(self):
        self.service.start()
        self.window = TorrentClientApp(self.service)
        self.tray = TorrentTrayButton()
        self.tray.bind_service(self.service)
        self.tray.pauseAllRequested.connect(self.service.pause_all)
        self.tray.resumeAllRequested.connect(self.service.resume_all)
        self.tray.activate()
        self.app.processEvents()
        self.assertEqual(self.window.torrent_table.rowCount(), 12)
        self.assertEqual(self.window.torrent_table.columnCount(), 8)
        self.assertTrue(self.tray.isVisible())
        self.assertTrue(self.tray.pause_action.isEnabled())

        self.tray.pause_action.trigger()
        self.assertTrue(self.service.paused)
        self.assertTrue(self.tray.resume_action.isEnabled())
        self.tray.resume_action.trigger()
        self.assertFalse(self.service.paused)

        self.window.close()
        self.tray.deactivate()
        self.assertFalse(self.tray.isVisible())
        self.assertEqual(
            [
                action.text()
                for action in self.tray._menu.actions()
                if not action.isSeparator()
            ],
            [
                "Open Torrent Client",
                "Pause all transfers",
                "Resume all transfers",
                "Close window to tray",
                "Exit Torrent Client",
            ],
        )


if __name__ == "__main__":
    unittest.main()
