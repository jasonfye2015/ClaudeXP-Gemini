"""Queued native Qt callbacks must not touch deleted desktop children."""

import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import sys
import unittest
from unittest.mock import patch

from PySide6.QtCore import QEvent
from PySide6.QtWidgets import QApplication

from win7_2011.tests.test_mush import make_account
from win7_2011.win7sim.desktop import DesktopPage


class DesktopTeardownTests(unittest.TestCase):
    def test_disposal_with_queued_tray_and_activation_callbacks_is_clean(self):
        app = QApplication.instance() or QApplication([])
        desktop = DesktopPage(make_account())
        desktop.show()
        desktop.open_irc_client()
        app.processEvents()
        desktop.open_mush_client()
        desktop.stop_session()
        desktop.deleteLater()
        errors = []
        with patch.object(sys, "excepthook", lambda kind, error, tb: errors.append(error)):
            app.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            app.processEvents()
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
