"""Input-event search checks; run alone with QT_QPA_PLATFORM=windows on Windows.

Linux offscreen runs check behavior, not Windows appearance or DPI readability.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "windows" if sys.platform == "win32" else "offscreen")

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QApplication, QToolButton  # noqa: E402

from win7_2011.win7sim import config  # noqa: E402
from win7_2011.win7sim.apps import MessengerApp  # noqa: E402
from win7_2011.win7sim.contacts import CONTACTS  # noqa: E402
from win7_2011.win7sim.identity import FursonaProfile, UserAccount  # noqa: E402
from win7_2011.win7sim.service import ConnectionSimulator  # noqa: E402
from win7_2011.win7sim.theme import APPLICATION_STYLE  # noqa: E402


class MessengerSearchInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])
        print(
            f"\nSearch input test environment: {sys.platform}, "
            f"Qt platform={cls.app.platformName()}, style={cls.app.style().objectName()}, "
            f"scale override={os.environ.get('QT_SCALE_FACTOR', 'none')}",
            flush=True,
        )
        if sys.platform == "win32" and cls.app.platformName() != "windows":
            raise RuntimeError("Windows verification requires QT_QPA_PLATFORM=windows")

    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        history_patch = patch.object(
            config, "MESSENGER_HISTORY", Path(directory.name) / "Messenger"
        )
        history_patch.start()
        self.addCleanup(history_patch.stop)
        old_style = self.app.styleSheet()
        self.app.setStyleSheet(APPLICATION_STYLE)
        self.addCleanup(self.app.setStyleSheet, old_style)
        profile = FursonaProfile(
            fursona_name="Rook", species="red fox", pronouns="they/them",
            date_of_birth="1988-06-12", profile_id="rook",
        )
        account = UserAccount(
            desktop_name="Test User", fursonas=[profile], active_profile_id="rook"
        )
        self.matches = [
            contact for contact in CONTACTS
            if "alex" in contact.display_name.casefold()
            or "alex" in contact.online_name.casefold()
        ]
        self.assertGreater(len(self.matches), 1)
        self.target = self.matches[-1]
        self.history = [{"role": "assistant", "content": "Saved search interaction history."}]
        config.save_messenger_history(self.target.contact_id, self.history, "rook")
        self.saved_bytes = {
            path: path.read_bytes()
            for path in config.MESSENGER_HISTORY.rglob("*") if path.is_file()
        }
        service = ConnectionSimulator()
        service.stop()
        self.messenger = MessengerApp(account, service)
        self.addCleanup(self.messenger.close)
        self.messenger.resize(1000, 700)
        self.messenger.show()
        self.messenger.activateWindow()
        self.app.processEvents()

    def type_search(self, text: str) -> None:
        field = self.messenger.search_input
        QTest.mouseClick(field, Qt.MouseButton.LeftButton)
        QTest.keyClicks(field, text)
        self.app.processEvents()
        self.assertEqual(field.text(), text)

    def clear_button(self) -> QToolButton:
        self.app.processEvents()
        buttons = [
            button for button in self.messenger.search_input.findChildren(QToolButton)
            if button.isVisible()
        ]
        self.assertEqual(len(buttons), 1, "Expected the built-in QLineEdit clear button")
        button = buttons[0]
        self.assertTrue(button.isEnabled())
        self.assertTrue(
            self.messenger.search_input.rect().contains(button.geometry()),
            "Clear button must fit inside the search field",
        )
        return button

    def assert_history_unchanged(self) -> None:
        self.assertEqual(
            {path: path.read_bytes()
             for path in config.MESSENGER_HISTORY.rglob("*") if path.is_file()},
            self.saved_bytes,
        )
        self.assertEqual(
            config.load_messenger_history(self.target.contact_id, "rook"), self.history
        )

    def test_typing_arrows_and_native_clear_preserve_selected_history(self) -> None:
        messenger = self.messenger
        self.assertEqual(messenger.contact_list.count(), len(CONTACTS))
        self.type_search("alex")
        self.assertEqual(
            [messenger.contact_list.item(row).data(Qt.ItemDataRole.UserRole)
             for row in range(messenger.contact_list.count())],
            [contact.contact_id for contact in self.matches],
        )
        QTest.keyClick(messenger.search_input, Qt.Key.Key_Tab)
        self.assertTrue(messenger.contact_list.hasFocus())
        QTest.keyClick(messenger.contact_list, Qt.Key.Key_Home)
        for _ in range(len(self.matches) - 1):
            QTest.keyClick(messenger.contact_list, Qt.Key.Key_Down)
        self.assertIs(messenger.selected_contact, self.target)
        QTest.keyClick(messenger.contact_list, Qt.Key.Key_Up)
        self.assertIs(messenger.selected_contact, self.matches[-2])
        QTest.keyClick(messenger.contact_list, Qt.Key.Key_Down)
        self.assertIs(messenger.selected_contact, self.target)
        before_clear = messenger.transcript.toPlainText()
        self.assertIn(self.history[0]["content"], before_clear)
        QTest.mouseClick(self.clear_button(), Qt.MouseButton.LeftButton)
        self.app.processEvents()
        self.assertEqual(messenger.search_input.text(), "")
        self.assertEqual(messenger.contact_list.count(), len(CONTACTS))
        self.assertIs(messenger.selected_contact, self.target)
        self.assertEqual(
            messenger.contact_list.currentItem().data(Qt.ItemDataRole.UserRole),
            self.target.contact_id,
        )
        self.assertEqual(messenger.transcript.toPlainText(), before_clear)
        self.assertEqual(messenger.contact_histories[self.target.contact_id], self.history)
        self.assert_history_unchanged()

    def test_native_clear_after_no_match_restores_roster_without_changing_history(self) -> None:
        self.type_search("no-such-contact-unique-query")
        self.assertEqual(self.messenger.contact_list.count(), 0)
        self.assertIsNone(self.messenger.selected_contact)
        self.assertEqual(self.messenger.search_results.text(), "No matching contacts")
        QTest.mouseClick(self.clear_button(), Qt.MouseButton.LeftButton)
        self.app.processEvents()
        self.assertEqual(self.messenger.search_input.text(), "")
        self.assertEqual(self.messenger.contact_list.count(), len(CONTACTS))
        self.assert_history_unchanged()

    def test_search_field_has_room_for_text_and_clear_control(self) -> None:
        self.type_search("alex")
        field = self.messenger.search_input
        button = self.clear_button()
        margins = field.textMargins()
        self.assertGreaterEqual(
            field.contentsRect().height() - margins.top() - margins.bottom(),
            field.fontMetrics().height(),
        )
        self.assertGreater(
            field.contentsRect().width() - margins.left() - margins.right()
            - button.width() - 16,
            field.fontMetrics().horizontalAdvance("alex"),
        )

    def test_contact_text_size_can_be_changed_without_losing_search_or_chat(self) -> None:
        messenger = self.messenger
        self.type_search("alex")
        QTest.keyClick(messenger.search_input, Qt.Key.Key_Tab)
        QTest.keyClick(messenger.contact_list, Qt.Key.Key_End)
        self.assertIs(messenger.selected_contact, self.target)
        transcript = messenger.transcript.toPlainText()
        self.assertIn(self.history[0]["content"], transcript)
        size = messenger.contact_text_size
        QTest.mouseClick(size, Qt.MouseButton.LeftButton)
        QTest.keyClick(size, Qt.Key.Key_Escape)
        for key, points in (
            (Qt.Key.Key_Down, 12), (Qt.Key.Key_Down, 14),
            (Qt.Key.Key_Home, 10),
        ):
            QTest.keyClick(size, key)
            self.app.processEvents()
            self.assertEqual(size.currentData(), points)
            self.assertIn(f"{points}pt", messenger.search_input.styleSheet())
            self.assertIn(f"{points}pt", messenger.contact_list.styleSheet())
            self.assertGreaterEqual(
                messenger.search_input.height(),
                messenger.search_input.fontMetrics().height() + 14,
            )
            self.clear_button()
            self.assertEqual(messenger.search_input.text(), "alex")
            self.assertEqual(messenger.contact_list.count(), len(self.matches))
            self.assertIs(messenger.selected_contact, self.target)
            self.assertEqual(messenger.transcript.toPlainText(), transcript)
        QTest.mouseClick(self.clear_button(), Qt.MouseButton.LeftButton)
        self.app.processEvents()
        self.assertEqual(messenger.contact_list.count(), len(CONTACTS))
        self.assertIs(messenger.selected_contact, self.target)
        self.assertEqual(messenger.transcript.toPlainText(), transcript)
        self.assert_history_unchanged()


if __name__ == "__main__":
    unittest.main()
