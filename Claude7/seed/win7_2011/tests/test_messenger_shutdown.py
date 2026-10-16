import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton

from win7_2011.tests.test_messaging import sample_account
from win7_2011.win7sim import config
from win7_2011.win7sim.application import SimulationWindow
from win7_2011.win7sim.contacts import CONTACTS
from win7_2011.win7sim.desktop import DesktopPage


class MessengerShutdownTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        storage = patch.object(config, "MESSENGER_HISTORY", Path(directory.name))
        storage.start()
        self.addCleanup(storage.stop)
        questions = patch(
            "win7_2011.win7sim.apps.QMessageBox.question",
            return_value=QMessageBox.StandardButton.Cancel,
        )
        questions.start()
        self.addCleanup(questions.stop)
        self.desktop = DesktopPage(sample_account())
        self.desktop.show()
        self.desktop.open_messenger()
        self.messenger = self.desktop._windows["messenger"].widget()
        self.addCleanup(self.cleanup_desktop)
        self.contact = CONTACTS[0].contact_id
        self.messenger.contact_histories[self.contact].append(
            {"role": "user", "content": "Do not lose this"}
        )
        with patch("win7_2011.win7sim.apps.save_messenger_history", side_effect=OSError("disk full")):
            self.messenger._save_history(self.contact)
        self.controller = SimpleNamespace(
            _stage="desktop", _shutting_down=False, _allow_close=False,
            _shutdown_safe_delay=100_000,
            stack=SimpleNamespace(currentWidget=lambda: self.desktop),
            _show_login=Mock(), _set_page=Mock(), _play_shutdown_sound=Mock(),
            _restart_pc=Mock(), _finish_shutdown=Mock(), _enter_recovery_mode=Mock(),
        )
        self.controller._begin_shutdown = lambda: SimulationWindow._begin_shutdown(self.controller)

    def cleanup_desktop(self):
        with patch(
            "win7_2011.win7sim.apps.QMessageBox.question",
            return_value=QMessageBox.StandardButton.Discard,
        ):
            self.desktop.close()
        self.desktop.deleteLater()
        self.app.processEvents()

    def test_cancel_blocks_logoff_shutdown_and_outer_window_close(self):
        for action in ("logoff", "shutdown", "close"):
            with self.subTest(action=action), patch.object(self.desktop, "stop_session") as stop:
                if action == "logoff":
                    SimulationWindow._log_off(self.controller)
                elif action == "shutdown":
                    SimulationWindow._begin_shutdown(self.controller)
                else:
                    event = QCloseEvent()
                    SimulationWindow.closeEvent(self.controller, event)
                    self.assertFalse(event.isAccepted())
                stop.assert_not_called()
                self.controller._show_login.assert_not_called()
                self.controller._set_page.assert_not_called()
                self.assertEqual(self.controller._stage, "desktop")
                self.assertFalse(self.controller._shutting_down)
                self.assertEqual(self.messenger.contact_histories[self.contact][0]["content"],
                                 "Do not lose this")
                self.assertEqual(self.desktop.mdi_area.activeSubWindow(),
                                 self.desktop._windows["messenger"])

    def test_cancel_blocks_desktop_and_mdi_close_without_cancelling_reply(self):
        with patch.object(self.desktop, "stop_session") as stop, patch.object(
            self.messenger.client, "cancel"
        ) as cancel:
            self.assertFalse(self.desktop.close())
            self.assertFalse(self.desktop._windows["messenger"].close())
            stop.assert_not_called()
            cancel.assert_not_called()
            self.assertTrue(self.messenger._unsaved_conversations)

    def test_shutdown_retry_failure_returns_to_live_desktop(self):
        with patch(
            "win7_2011.win7sim.apps.QMessageBox.question",
            return_value=QMessageBox.StandardButton.Retry,
        ), patch("win7_2011.win7sim.apps.QMessageBox.warning"), patch(
            "win7_2011.win7sim.apps.save_messenger_history", side_effect=OSError("still full")
        ), patch.object(self.desktop, "stop_session") as stop:
            SimulationWindow._begin_shutdown(self.controller)
            stop.assert_not_called()
            self.assertEqual(self.controller._stage, "desktop")
            self.assertTrue(self.messenger._unsaved_conversations)

    def test_start_menu_shutdown_cancel_and_failed_retry_do_not_stop_services(self):
        self.desktop.shutdownRequested.connect(self.controller._begin_shutdown)
        shutdown = self.desktop.findChild(QPushButton, "shutdownButton")
        self.assertIsNotNone(shutdown)
        for answer, busy in (
            (QMessageBox.StandardButton.Cancel, True),
            (QMessageBox.StandardButton.Retry, False),
        ):
            with self.subTest(answer=answer), patch(
                "win7_2011.win7sim.apps.QMessageBox.question", return_value=answer,
            ) as prompt, patch(
                "win7_2011.win7sim.apps.QMessageBox.warning"
            ), patch(
                "win7_2011.win7sim.apps.save_messenger_history", side_effect=OSError("still full"),
            ), patch.object(
                type(self.messenger.client), "is_busy", new=property(lambda _: busy),
            ), patch.object(self.desktop.service, "stop") as connection_stop, patch.object(
                self.desktop.ai_service, "stop"
            ) as ai_stop, patch.object(self.messenger.client, "cancel") as cancel:
                self.desktop.start_button.click()
                shutdown.click()
                prompt.assert_called_once()
                self.assertFalse(self.desktop.start_menu.isVisible())
                connection_stop.assert_not_called()
                ai_stop.assert_not_called()
                cancel.assert_not_called()
                self.assertFalse(self.controller._shutting_down)
                self.assertEqual(self.controller._stage, "desktop")
                self.controller._set_page.assert_not_called()
                self.assertEqual(self.messenger.contact_histories[self.contact][0]["content"],
                                 "Do not lose this")

    def test_successful_retry_allows_shutdown_and_removes_warning(self):
        with patch(
            "win7_2011.win7sim.apps.QMessageBox.question",
            return_value=QMessageBox.StandardButton.Retry,
        ), patch.object(self.desktop, "stop_session") as stop:
            SimulationWindow._begin_shutdown(self.controller)
            stop.assert_called_once()
        self.assertEqual(self.controller._stage, "shutdown")
        self.assertTrue(self.controller._shutting_down)
        self.assertEqual(config.load_messenger_history(self.contact, "rook"),
                         self.messenger.contact_histories[self.contact])
        with patch("win7_2011.win7sim.apps.QMessageBox.question") as prompt:
            self.assertTrue(self.desktop.confirm_session_end("log off"))
            prompt.assert_not_called()
        screen = self.controller._set_page.call_args.args[0]
        screen.deleteLater()

    def test_reinstall_cancel_does_not_erase_data_and_discard_does_not_resave_it(self):
        self.controller.account = self.desktop.account
        with patch("win7_2011.win7sim.application.reset_user_data") as reset:
            SimulationWindow._format_and_reinstall(self.controller)
            reset.assert_not_called()
        with patch(
            "win7_2011.win7sim.apps.QMessageBox.question",
            return_value=QMessageBox.StandardButton.Discard,
        ) as prompt, patch(
            "win7_2011.win7sim.application.reset_user_data"
        ) as reset, patch(
            "win7_2011.win7sim.apps.save_messenger_history"
        ) as save:
            self.controller._begin_shutdown = Mock()
            SimulationWindow._format_and_reinstall(self.controller)
            reset.assert_called_once()
            save.assert_not_called()
            prompt.assert_called_once()
            self.controller._begin_shutdown.assert_called_once_with(confirm_unsaved=False)
            self.assertIsNone(self.controller.account)

    def test_explicit_discard_allows_logoff(self):
        with patch(
            "win7_2011.win7sim.apps.QMessageBox.question",
            return_value=QMessageBox.StandardButton.Discard,
        ), patch.object(self.desktop, "stop_session") as stop:
            SimulationWindow._log_off(self.controller)
            stop.assert_called_once()
        self.controller._show_login.assert_called_once()


if __name__ == "__main__":
    unittest.main()
