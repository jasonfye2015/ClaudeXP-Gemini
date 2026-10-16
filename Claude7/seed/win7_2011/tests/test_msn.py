"""Native offscreen coverage for supplied MSN skins, identities and multi-window chat."""

import json
import os
import random
import tempfile
import threading
import time
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEvent, Qt, QUrl
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication

from win7_2011.tests.test_messaging import sample_account, LlamaServerHandler
from win7_2011.tests.test_ai import ControlledBackend
from win7_2011.win7sim import config
from win7_2011.win7sim.ai_service import AIService
from win7_2011.win7sim.ai_settings import AISettings
from win7_2011.win7sim.contacts import (
    CONTACTS, MSN_CONTACTS, MSN_ASSETS, SUPPLIED_CONTACTS, SUPPLIED_PROFILES,
    messenger_system_prompt, validate_community_contacts,
)
from win7_2011.win7sim.desktop import DesktopPage
from win7_2011.win7sim.msn import MSNContactListApp, MSNConversationApp
from win7_2011.win7sim.msn_browser import MSNBrowser
from win7_2011.win7sim.msn_history import MSNHistorySession
from win7_2011.win7sim.msn_presence import MSNPresence
from win7_2011.win7sim.msn_state import MSNState
from win7_2011.win7sim.msn_tray import MSNTrayButton
from win7_2011.win7sim.msn_widgets import player_avatar
from win7_2011.win7sim.service import ConnectionSimulator, ServiceState


class MSNTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name, path in (
            ("USER_PROFILES", self.root / "Profiles"),
            ("MESSENGER_HISTORY", self.root / "Chats"),
            ("SYSTEM_ROOT", self.root / "System"),
            ("STORAGE_ROOT", self.root),
        ):
            patcher = patch.object(config, name, path)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.account = sample_account()
        self.service = ConnectionSimulator()
        self.service.stop()
        self.preferences = MSNState("rook")
        self.presence = MSNPresence(rng=random.Random(42), preferences=self.preferences, service=self.service)
        self.presence.timer.stop()
        self.ai = AIService(settings=AISettings())
        self.history = MSNHistorySession()
        self.widgets = []
        self.addCleanup(self.cleanup_widgets)

    def cleanup_widgets(self):
        self.ai.stop()
        self.service.stop()
        self.presence.stop()
        for widget in reversed(self.widgets):
            widget.close()
            widget.deleteLater()
        self.app.processEvents()

    def roster(self):
        widget = MSNContactListApp(self.account, self.service, ai_service=self.ai,
            presence=self.presence, history_session=self.history)
        self.widgets.append(widget)
        return widget

    def chat(self, contact=None):
        if self.presence.user_status == "Offline":
            self.presence.set_user_status("Online")
        contact = contact or SUPPLIED_CONTACTS[0]
        self.presence.set_state(contact.contact_id, "Online")
        widget = MSNConversationApp(self.account, self.service, contact,
            ai_service=self.ai, presence=self.presence, history_session=self.history)
        self.widgets.append(widget)
        return widget

    def wait(self, predicate):
        end = time.monotonic() + 5
        while time.monotonic() < end:
            self.app.processEvents()
            if predicate():
                return
            time.sleep(.005)
        self.fail("Timed out waiting for the local test server.")

    def controlled_ai(self):
        self.ai.stop()
        self.ai = AIService(
            backend_factory=ControlledBackend,
            settings=AISettings(models={"direct": "chat", "background": "", "summary": ""}),
        )
        self.ai.test_connection()

    def test_tray_status_flash_counts_and_read_acknowledgement(self):
        tray = MSNTrayButton(self.presence)
        self.widgets.append(tray)
        for state, label in tray.LABELS.items():
            self.presence.set_user_status(state)
            self.assertIn(label, tray.toolTip())
            self.assertFalse(tray.icon().isNull())
        tray.notify_message("a", "First contact")
        tray.notify_message("a", "First contact")
        tray.notify_message("b", "Second contact")
        self.assertEqual(tray.unread_count, 3)
        self.assertTrue(tray.flash_timer.isActive())
        style = tray.styleSheet()
        tray._flash()
        self.assertNotEqual(tray.styleSheet(), style)
        self.assertIn("Offline", tray.toolTip())
        opened = []
        tray.activated.connect(opened.append)
        tray.click()
        self.assertEqual(opened, ["a"])
        tray.mark_read("a")
        self.assertEqual(tray.unread_count, 1)
        tray.mark_read("b")
        self.assertFalse(tray.flash_timer.isActive())
        tray.click()
        self.assertEqual(opened[-1], "")
        tray.notify_message("c", "Third")
        tray.stop()
        self.assertFalse(tray.flash_timer.isActive())
        tray.set_enabled(False)
        self.assertTrue(tray.isHidden())
        self.assertFalse(MSNState("rook").data["show_tray_icon"])
        tray.set_enabled(True)
        self.assertFalse(tray.isHidden())
        self.assertTrue(MSNState("rook").data["show_tray_icon"])

    def test_messenger_always_starts_offline_and_migrates_tray_preference(self):
        self.assertEqual(self.presence.user_status, "Offline")
        self.assertTrue(self.preferences.data["show_tray_icon"])
        self.presence.set_user_status("Online")
        self.preferences.data["show_tray_icon"] = False
        self.preferences.save()
        next_state = MSNState("rook")
        next_presence = MSNPresence(
            rng=random.Random(1), preferences=next_state, service=self.service
        )
        self.addCleanup(next_presence.stop)
        self.assertEqual(next_presence.user_status, "Offline")
        self.assertEqual(next_state.data["user_status"], "Offline")
        self.assertFalse(next_state.data["show_tray_icon"])

    def test_close_messenger_menu_removes_mdi_windows_and_tray_but_keeps_desktop(self):
        self.controlled_ai()
        with patch("win7_2011.win7sim.desktop.AIService", return_value=self.ai):
            desktop = DesktopPage(self.account)
        self.widgets.append(desktop)
        desktop.resize(1100, 780)
        desktop.show()
        desktop.open_messenger()
        roster = desktop._windows["messenger"].widget()
        desktop.open_msn_conversation(SUPPLIED_CONTACTS[0])
        desktop.open_notepad()
        self.assertEqual(
            set(desktop._windows), {"messenger", "msn-chat-" + SUPPLIED_CONTACTS[0].contact_id, "notepad"}
        )
        roster.tray_visibility_action.trigger()
        self.assertTrue(desktop.msn_tray.isHidden())
        self.assertFalse(desktop.msn_tray.presence.preferences.data["show_tray_icon"])
        roster.tray_visibility_action.trigger()
        self.assertFalse(desktop.msn_tray.isHidden())
        self.assertTrue(desktop.msn_tray.presence.preferences.data["show_tray_icon"])

        tray_menu = desktop.msn_tray.build_status_menu()
        tray_menu_items = [action.text() for action in tray_menu.actions()]
        self.assertIn("Close MSN Messenger", tray_menu_items)
        tray_menu.actions()[-1].trigger()
        tray_menu.close()
        tray_menu.deleteLater()
        self.app.processEvents()
        self.app.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.assertNotIn("messenger", desktop._windows)
        self.assertNotIn("msn-chat-" + SUPPLIED_CONTACTS[0].contact_id, desktop._windows)
        self.assertIn("notepad", desktop._windows)
        self.assertFalse(desktop.msn_tray.isVisible())
        self.assertEqual(desktop.msn_presence.user_status, "Offline")
        self.assertEqual(
            [window.widget().__class__.__name__ for window in desktop.mdi_area.subWindowList()],
            ["NotepadApp"],
        )
        self.assertTrue(desktop.isVisible())
        desktop.open_messenger()
        self.assertIn("messenger", desktop._windows)
        self.assertTrue(desktop.msn_tray.isVisible())
        self.assertEqual(desktop.msn_presence.user_status, "Offline")
        desktop._windows["messenger"].widget().close_action.trigger()
        self.app.processEvents()
        self.app.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.assertNotIn("messenger", desktop._windows)
        self.assertFalse(desktop.msn_tray.isVisible())

    def test_llm_taskbar_monitor_opens_log_and_receives_full_activity(self):
        self.controlled_ai()
        with patch("win7_2011.win7sim.desktop.AIService", return_value=self.ai):
            desktop = DesktopPage(self.account)
        self.widgets.append(desktop)
        desktop.llm_monitor.click()
        self.app.processEvents()
        self.assertIn("llm-activity", desktop._windows)
        window = desktop._windows["llm-activity"].widget()

        self.ai.llmPhaseChanged.emit(77, "direct", "generating")
        self.assertEqual(desktop.llm_monitor.phase, "generating")
        self.assertTrue(desktop.llm_monitor.blink_timer.isActive())
        self.ai.llmRequestSent.emit(
            77, "direct", "NemoMix-12B",
            [{"role": "user", "content": "Exact diagnostic prompt"}],
        )
        self.ai.llmResponseCaptured.emit(
            77, "direct", True, "Complete unfiltered model response",
        )
        self.assertIn("Exact diagnostic prompt", window.text.toPlainText())
        self.assertIn("Complete unfiltered model response", window.text.toPlainText())
        self.assertTrue(desktop.llm_activity_log.path.exists())

    def test_network_tray_simulates_msn_sign_in_and_chat_transfers(self):
        self.controlled_ai()
        with patch("win7_2011.win7sim.desktop.AIService", return_value=self.ai):
            desktop = DesktopPage(self.account)
        self.widgets.append(desktop)
        desktop.msn_presence.set_user_status("Online")
        self.assertEqual(
            [event["direction"] for event in desktop.network_tray._events[:2]],
            ["outgoing", "incoming"],
        )
        self.assertIn("Also: Receiving", desktop.network_tray.toolTip())
        self.assertIn("MSN contact and presence list", desktop.network_tray.toolTip())

        contact = SUPPLIED_CONTACTS[0]
        desktop.msn_presence.set_state(contact.contact_id, "Online")
        desktop.open_msn_conversation(contact)
        chat = desktop._windows["msn-chat-" + contact.contact_id].widget()
        chat.message_edit.setText("Hello through MSN")
        chat._send_message()
        self.assertEqual(desktop.network_tray._events[-1]["direction"], "outgoing")
        self.assertIn("MSN chat message", desktop.network_tray._events[-1]["description"])

        self.app.processEvents()
        self.ai.backend.finish(text="A simulated incoming reply")
        self.app.processEvents()
        self.assertEqual(desktop.network_tray._events[-1]["direction"], "incoming")
        self.assertIn("MSN chat reply", desktop.network_tray._events[-1]["description"])

    def test_typing_belongs_to_generating_chat_not_queued_chat_and_clears_on_failure(self):
        self.controlled_ai()
        first, second = self.chat(SUPPLIED_CONTACTS[0]), self.chat(SUPPLIED_CONTACTS[1])
        arrivals = []
        first.messageArrived.connect(arrivals.append)
        second.messageArrived.connect(arrivals.append)
        first.message_edit.setText("First")
        first._send_message()
        second.message_edit.setText("Second")
        second._send_message()
        self.assertFalse(first._typing)
        self.assertFalse(second._typing)
        self.app.processEvents()
        self.assertTrue(first._typing)
        self.assertIn("is typing a message...", first.last_received.text())
        self.assertFalse(second._typing)
        self.ai.backend.finish(text="Hello!")
        self.assertFalse(first._typing)
        self.assertIn("2011", first.last_received.text())
        self.app.processEvents()
        self.assertTrue(second._typing)
        self.ai.backend.finish(False, "Generation failed")
        self.assertFalse(second._typing)
        self.assertNotIn("typing", second.last_received.text())
        self.assertEqual(arrivals, [SUPPLIED_CONTACTS[0].contact_id])
        second.message_edit.setText("Another message")
        second._send_message()
        self.app.processEvents()
        self.assertTrue(second._typing)
        self.presence.set_user_status("Offline")
        self.app.processEvents()
        self.assertFalse(second._typing)
        self.assertEqual(arrivals, [SUPPLIED_CONTACTS[0].contact_id])

    def test_background_replies_flash_tray_and_click_restores_each_unread_chat(self):
        self.controlled_ai()
        with patch("win7_2011.win7sim.desktop.AIService", return_value=self.ai):
            desktop = DesktopPage(self.account)
        self.widgets.append(desktop)
        desktop.resize(1100, 780)
        desktop.show()
        desktop.msn_presence.set_user_status("Online")
        a, b = SUPPLIED_CONTACTS[:2]
        for contact in (a, b):
            desktop.msn_presence.set_state(contact.contact_id, "Online")
            desktop.open_msn_conversation(contact)
        wa = desktop._windows["msn-chat-" + a.contact_id]
        wb = desktop._windows["msn-chat-" + b.contact_id]
        wa.widget().message_edit.setText("Hello A")
        wa.widget()._send_message()
        wa.showMinimized()
        self.app.processEvents()
        self.ai.backend.finish(text="Reply A")
        self.assertEqual(desktop.msn_tray.unread_contacts, (a.contact_id,))
        wb.widget().message_edit.setText("Hello B")
        wb.widget()._send_message()
        desktop.open_messenger()
        self.app.processEvents()
        self.ai.backend.finish(text="Reply B")
        self.assertEqual(desktop.msn_tray.unread_count, 2)
        desktop.msn_tray.click()
        self.assertIs(desktop.mdi_area.activeSubWindow(), wa)
        self.assertFalse(wa.isMinimized())
        self.assertEqual(desktop.msn_tray.unread_contacts, (b.contact_id,))
        desktop.msn_tray.click()
        self.assertIs(desktop.mdi_area.activeSubWindow(), wb)
        self.assertEqual(desktop.msn_tray.unread_count, 0)
        self.assertFalse(desktop.msn_tray.flash_timer.isActive())

    def test_visible_active_chat_reply_does_not_flash_and_activation_marks_read(self):
        desktop = DesktopPage(self.account)
        self.widgets.append(desktop)
        desktop.resize(1100, 780)
        desktop.show()
        contact = SUPPLIED_CONTACTS[0]
        desktop.open_msn_conversation(contact)
        with patch.object(desktop, "_msn_chat_is_readable", return_value=True):
            desktop._msn_message_arrived(contact.contact_id)
            self.assertEqual(desktop.msn_tray.unread_count, 0)
            desktop.msn_tray.notify_message(contact.contact_id, contact.online_name)
            desktop._acknowledge_msn_window()
            self.assertEqual(desktop.msn_tray.unread_count, 0)
        desktop.msn_tray.notify_message(contact.contact_id, contact.online_name)
        desktop.stop_session()
        self.assertFalse(desktop.msn_tray.flash_timer.isActive())

    def test_all_supplied_profiles_and_assets_are_loaded_without_invented_birthdays(self):
        self.assertEqual(len(SUPPLIED_CONTACTS), 34)
        self.assertEqual(len(CONTACTS), 234)
        self.assertEqual(len(MSN_CONTACTS), 184)
        self.assertEqual(validate_community_contacts(), [])
        for contact in SUPPLIED_CONTACTS:
            self.assertEqual(contact.online_name, contact.display_name)
            self.assertTrue(contact.source_profile)
            self.assertFalse(QPixmap(str(MSN_ASSETS / contact.icon_path)).isNull())
            for name in contact.gallery:
                self.assertTrue((MSN_ASSETS / name).is_file())
            prompt = messenger_system_prompt(contact, self.account)
            self.assertIn(contact.source_profile, prompt)
            self.assertIn("2011", prompt)
        fox = next(c for c in SUPPLIED_CONTACTS if c.online_name == "ArcticFox")
        self.assertEqual(fox.date_of_birth, "")
        self.assertEqual(fox.declared_age, 26)
        husky = next(c for c in SUPPLIED_CONTACTS if c.online_name == "CyberianHusky")
        self.assertIsNone(husky.age_in_2011)
        self.assertIn("21+", husky.age_label)

    def test_group_counts_two_icons_search_and_double_click(self):
        roster = self.roster()
        self.assertEqual(roster.tree.topLevelItemCount(), 2)
        self.assertEqual(sum(roster.tree.topLevelItem(i).childCount() for i in range(2)), 184)
        roster.search_input.setText("arctic")
        item = next(roster.tree.topLevelItem(i).child(0) for i in range(2)
                    if roster.tree.topLevelItem(i).childCount())
        self.assertEqual(item.text(0), "ArcticFox")
        self.assertEqual(item.icon(0).pixmap(48, 24).size().width(), 48)
        opened = []
        roster.conversationRequested.connect(opened.append)
        roster._open_item(item)
        self.assertEqual(opened[0].online_name, "ArcticFox")
        roster.search_input.clear()
        roster._toggle_legacy(True)
        self.assertEqual(sum(roster.tree.topLevelItem(i).childCount() for i in range(2)), 234)

    def test_presence_changes_blocking_and_user_status_persist_separately(self):
        contact = SUPPLIED_CONTACTS[0]
        roster = self.roster()
        self.presence.set_state(contact.contact_id, "Offline")
        self.assertIn("offline", roster.activity.text())
        self.presence.toggle_block(contact.contact_id)
        self.presence.set_user_status("Away", "Making tea")
        restored = MSNState("rook")
        self.assertIn(contact.contact_id, restored.data["blocked"])
        self.assertEqual(restored.data["away_message"], "Making tea")
        self.assertEqual(MSNState("moss").data["blocked"], [])
        self.assertIn("Making tea", roster.user_status.text())
        roster.set_unread_mail(1)
        first = roster.mail_icon.icon().isNull()
        roster._flash_mail()
        self.assertNotEqual(first, roster.mail_icon.icon().isNull())
        self.assertGreater(roster.mail_icon.geometry().left(), roster.user_status.geometry().left())
        self.assertGreater(roster.mail_button.geometry().left(), roster.mail_icon.geometry().right())

    def test_damaged_preferences_are_reported_and_preserved(self):
        self.preferences.path.parent.mkdir(parents=True)
        self.preferences.path.write_bytes(b"broken")
        restored = MSNState("rook")
        self.assertTrue(restored.error)
        self.assertFalse(restored.save())
        self.assertEqual(restored.path.read_bytes(), b"broken")

    def test_background_presence_pauses_and_active_chat_is_not_dropped(self):
        contact = SUPPLIED_CONTACTS[0]
        self.presence.set_state(contact.contact_id, "Online")
        self.presence.remaining[contact.contact_id] = 0
        self.service.state = ServiceState.SLOWDOWN
        self.presence.advance()
        self.assertEqual(self.presence.remaining[contact.contact_id], 0)
        self.service.state = ServiceState.CONNECTED
        self.presence.chatting.add(contact.contact_id)
        self.presence.advance()
        self.assertEqual(self.presence.state(contact.contact_id), "Online")
        self.presence.stop()
        self.assertFalse(self.presence.timer.isActive())

    def test_default_ad_does_nothing_and_other_ad_navigates_inside_simulator(self):
        roster = self.roster()
        navigation = []
        roster.browserRequested.connect(navigation.append)
        roster._click_ad()
        self.assertEqual(navigation, [])
        roster.set_advertisements([(MSN_ASSETS / "MSN_Contact_List_AD_Default.jpg", "http://fur.example/")])
        roster._click_ad()
        self.assertEqual(navigation, ["http://fur.example/"])
        self.assertGreaterEqual(roster._ad_timer.interval(), 5 * 60_000)
        self.assertLessEqual(roster._ad_timer.interval(), 10 * 60_000)

    def test_chat_layout_matches_windows_user_icon_and_fills_both_frames(self):
        roster = self.roster()
        chat = self.chat()
        chat.resize(680, 570)
        chat.show()
        self.app.processEvents()
        self.assertTrue(chat.canvas.rect().contains(chat.recipient_avatar.geometry()))
        self.assertTrue(chat.canvas.rect().contains(chat.my_avatar.geometry()))
        self.assertEqual(
            chat.my_avatar.original.toImage(), player_avatar(self.account).toImage()
        )
        self.assertTrue(chat.my_avatar.stretch_to_frame)
        self.assertTrue(chat.recipient_avatar.stretch_to_frame)
        self.assertEqual(chat.my_avatar.pixmap().size(), chat.my_avatar.size())
        self.assertEqual(chat.recipient_avatar.pixmap().size(), chat.recipient_avatar.size())
        sx = chat.canvas.width() / chat.canvas.image.width()
        sy = chat.canvas.height() / chat.canvas.image.height()
        for avatar, rect in (
            (chat.recipient_avatar, (267, 60, 71, 71)),
            (chat.my_avatar, (267, 187, 71, 71)),
        ):
            self.assertEqual(avatar.geometry().getRect(), tuple(
                round(value * scale)
                for value, scale in zip(rect, (sx, sy, sx, sy), strict=True)
            ))
        self.assertIs(chat._histories_by_profile, roster._histories_by_profile)
        self.assertIsNot(chat.client, roster.client)
        self.assertIs(chat.ai, roster.ai)
        chat.message_edit.setText("First line\nSecond line")
        self.assertEqual(chat.message_edit.text(), "First line\nSecond line")
        self.assertTrue(chat.advanced.findChildren(type(chat.context_budget)))

    def test_local_reply_saved_once_and_picture_link_is_allowlisted(self):
        class Handler(LlamaServerHandler):
            requests = []
            reply_text = "Here is a con photo! [share:arc_con1.jpg]"
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        self.ai.apply(AISettings(url=f"http://127.0.0.1:{server.server_port}",
            models={"direct": "test-model:3b", "background": "", "summary": ""}))
        self.wait(lambda: self.ai.is_available("direct"))
        roster = self.roster()
        contact = next(c for c in SUPPLIED_CONTACTS if c.online_name == "ArcticFox")
        chat = self.chat(contact)
        chat.message_edit.setText("Hello there")
        chat._send_message()
        self.wait(lambda: len(chat.contact_histories[contact.contact_id]) == 2)
        messages = config.load_messenger_history(contact.contact_id, "rook")
        self.assertEqual(len(messages), 2)
        self.assertIn("msn-picture:arc_con1.jpg", chat.transcript.toHtml())
        self.assertIn("2011", chat.last_received.text())
        self.assertIn(contact.contact_id, MSNState("rook").data["last_received"])
        self.assertEqual(config.load_messenger_history(contact.contact_id, "moss"), [])
        self.assertEqual(roster.contact_histories[contact.contact_id], messages)
        with patch("win7_2011.win7sim.msn.show_gallery") as gallery:
            chat._open_picture(QUrl("msn-picture:../secret.jpg"))
            gallery.assert_not_called()
            chat._open_picture(QUrl("msn-picture:arc_con1.jpg"))
            gallery.assert_called_once()
        self.presence.toggle_block(contact.contact_id)
        self.assertFalse(chat.send_button.isEnabled())
        self.presence.toggle_block(contact.contact_id)
        self.assertTrue(chat.send_button.isEnabled())
        self.presence.set_user_status("Offline")
        self.assertFalse(chat.send_button.isEnabled())
        self.assertEqual(len(Handler.requests), 1)

    def test_desktop_opens_distinct_chat_windows_and_reuses_the_same_contact(self):
        desktop = DesktopPage(self.account)
        self.widgets.append(desktop)
        desktop.resize(1100, 780)
        desktop.show()
        desktop.open_messenger()
        a, b = SUPPLIED_CONTACTS[:2]
        desktop.open_msn_conversation(a)
        desktop.open_msn_conversation(b)
        first = desktop._windows["msn-chat-" + a.contact_id]
        desktop.open_msn_conversation(a)
        self.assertIs(desktop._windows["msn-chat-" + a.contact_id], first)
        self.assertEqual(len(desktop._windows), 3)
        self.assertIsInstance(desktop._windows["messenger"].widget(), MSNContactListApp)
        self.assertEqual(len(desktop._taskbar_buttons), 3)

    def test_local_browser_renders_installed_page_and_blocks_outside_resources(self):
        folder = self.root / "Web" / "fur.example"
        folder.mkdir(parents=True)
        (folder / "index.html").write_text("<h1>A furry homepage</h1><p>Welcome in 2011.</p>")
        browser = MSNBrowser("http://fur.example/")
        self.widgets.append(browser)
        transfers = []
        browser.networkTransferRequested.connect(lambda *event: transfers.append(event))
        browser.navigate("http://fur.example/")
        self.assertEqual(
            [event[0] for event in transfers],
            ["outgoing", "incoming"],
        )
        self.assertGreater(transfers[1][1], 128)
        self.assertIn("A furry homepage", browser.page.toPlainText())
        self.assertEqual(browser.page.loadResource(2, QUrl("https://real.example/pixel.png")).size(), 0)
        self.assertEqual(browser.page.loadResource(2, QUrl.fromLocalFile("/etc/passwd")).size(), 0)
        browser.navigate("http://missing.example/")
        self.assertIn("not installed", browser.page.toPlainText())
        browser._step(-1)
        self.assertIn("A furry homepage", browser.page.toPlainText())


if __name__ == "__main__":
    unittest.main()
