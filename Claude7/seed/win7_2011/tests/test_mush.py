"""PawPrints MUCK data, UI, identity, and local-AI behavior."""

from __future__ import annotations

from datetime import datetime
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEvent, QObject, Signal
from PySide6.QtWidgets import QApplication

from win7_2011.win7sim.contacts import SUPPLIED_CONTACTS
from win7_2011.win7sim.identity import FursonaProfile, UserAccount
from win7_2011.win7sim.mush import MushClientApp
from win7_2011.win7sim.mush_tray import MushTrayButton
from win7_2011.win7sim.mush_world import MUSH_ASSETS, MushWorld


def make_account():
    first = FursonaProfile(
        fursona_name="Rook",
        species="red fox",
        pronouns="they/them",
        date_of_birth="1985-04-10",
        bio="A red fox who enjoys late-night walks and old computer games.",
        profile_id="profile-rook",
    )
    second = FursonaProfile(
        fursona_name="Moss",
        species="gray wolf",
        pronouns="she/her",
        date_of_birth="1982-09-21",
        bio="A gray wolf who likes quiet cafes and maps.",
        profile_id="profile-moss",
    )
    return UserAccount(
        desktop_name="Rook",
        fursonas=[first, second],
        active_profile_id=first.profile_id,
    )


class FakeConnection(QObject):
    stateChanged = Signal(str, str)

    def __init__(self):
        super().__init__()
        self.chat_available = True


class FakeAIService(QObject):
    changed = Signal()
    jobFinished = Signal(int, bool, str)
    jobInputPrepared = Signal(int, object)

    def __init__(self):
        super().__init__()
        self.status = "Ready"
        self.requests = []
        self.output_limits = {}
        self.next_id = 0
        self.available = True
        self.background_available = False

    def is_available(self, role):
        return self.available and (
            role == "direct" or (role == "background" and self.background_available)
        )

    def context_for_role(self, role="direct"):
        return 4096, "test window"

    def submit(self, role, messages, input_budget=None, output_limit=None):
        self.next_id += 1
        self.requests.append((self.next_id, role, messages, input_budget))
        self.output_limits[self.next_id] = output_limit
        return self.next_id

    def cancel(self, request_id):
        self.jobFinished.emit(request_id, False, "Cancelled")

    def reply(self, text, success=True):
        request_id = self.requests[-1][0]
        self.jobFinished.emit(request_id, success, text)


class MushTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt_app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.account = make_account()
        self.connection = FakeConnection()
        self.ai = FakeAIService()

    def test_supplied_world_merges_profiles_filters_underage_and_uses_public_rooms(self):
        world = MushWorld(
            self.account,
            now_provider=lambda: datetime(2011, 10, 12, 20, 0),
        )
        names = [resident.name.casefold() for resident in world.residents]
        self.assertEqual(len(names), len(set(names)))
        self.assertIn("red", names)
        red = world.find_resident("Red")
        self.assertEqual(red.source, "PawPrints regular")
        self.assertIn("Full Character Name", red.profile_text)
        self.assertEqual(red.species, "red fox")

        self.assertTrue({"Bubbles", "Pixel", "Gill"}.issubset(world.excluded_minor_names))
        for name in ("Bubbles", "Pixel", "Gill"):
            self.assertIsNone(world.find_resident(name))
        self.assertIn("SleepyStripes", world.excluded_unverified_names)
        self.assertIsNone(world.find_resident("SleepyStripes"))

        self.assertGreater(sum(r.source == "PawPrints regular" for r in world.residents), 50)
        self.assertGreater(
            sum(r.source == "PawPrints community profile" for r in world.residents),
            40,
        )
        self.assertGreater(sum(r.source == "MSN contact" for r in world.residents), 100)

        world.connect("Rook")
        self.assertEqual(world.current_room, "welcome")
        self.assertEqual(world.player_description, self.account.active_profile.bio)
        self.assertTrue(world.move("out"))
        self.assertEqual(world.current_room, "square")
        world.current_room = world.home_room
        self.assertIn("Rook", world.room_name())
        self.assertFalse(world.rooms[world.home_room].get("public", True))
        self.assertTrue(all(
            world.rooms[resident.room_id].get("public", True)
            for resident in world.online_residents.values()
        ))

    def test_passwordless_login_uses_only_the_selected_profile_and_desc_is_temporary(self):
        app = MushClientApp(self.account, self.connection, self.ai)
        self.addCleanup(app.close)
        app._execute_command("connect Moss")
        self.assertFalse(app.connected)
        self.assertIn("Only the selected Windows fursona", app.output.toPlainText())

        app._execute_command("connect Rook")
        self.assertTrue(app.connected)
        self.assertEqual(app.world.player_name, "Rook")
        self.assertEqual(app.world.player_description, self.account.fursonas[0].bio)
        self.assertIn(self.account.fursonas[0].bio, app.output.toPlainText())
        self.assertIn("no password required", app.output.toPlainText())

        original_bio = self.account.fursonas[0].bio
        app._execute_command("@desc A temporary MUSH description.")
        self.assertEqual(app.world.player_description, "A temporary MUSH description.")
        self.assertEqual(self.account.fursonas[0].bio, original_bio)
        app.disconnect_player()
        app._execute_command("connect Rook")
        self.assertEqual(app.world.player_description, original_bio)

        app._execute_command("home")
        self.assertEqual(app.world.current_room, app.world.home_room)
        self.assertIn("Rook's Den", app.output.toPlainText())
        app._execute_command("out")
        self.assertEqual(app.world.current_room, "square")
        app._execute_command("help")
        self.assertIn("page <resident>=<message>", app.output.toPlainText())

    def test_resident_ai_context_and_short_history_are_isolated_per_fursona(self):
        app = MushClientApp(self.account, self.connection, self.ai)
        self.addCleanup(app.close)
        app._execute_command("connect Rook")
        contact = SUPPLIED_CONTACTS[0]
        resident = app.world._resident_by_contact_id[contact.contact_id]
        resident.online = True
        resident.room_id = app.world.current_room
        app.world.online_residents[resident.resident_id] = resident

        app._request_resident_reply(resident, "Do you remember the arcade?", public=False)
        first_messages = self.ai.requests[-1][2]
        first_prompt = first_messages[0]["content"]
        self.assertIn("Rook", first_prompt)
        self.assertIn(self.account.fursonas[0].bio, first_prompt)
        self.assertNotIn("Moss", first_prompt)
        self.assertIn("Do not invent shared history", first_prompt)
        self.assertIn(contact.source_profile, first_prompt)
        self.ai.reply("I was just thinking about that place!")
        self.assertIn(f"{resident.name} pages you: I was just thinking", app.output.toPlainText())

        app.disconnect_player()
        self.account.active_profile_id = self.account.fursonas[1].profile_id
        app._execute_command("connect Moss")
        resident.online = True
        resident.room_id = app.world.current_room
        app.world.online_residents[resident.resident_id] = resident
        app._request_resident_reply(resident, "What have you been doing?", public=False)
        second_messages = self.ai.requests[-1][2]
        second_prompt = second_messages[0]["content"]
        self.assertIn("Moss", second_prompt)
        self.assertNotIn("Rook", second_prompt)
        self.assertEqual(len(second_messages), 2)
        self.assertNotIn("Do you remember the arcade?", repr(second_messages))

    def test_mush_tray_has_menu_and_blinks_its_supplied_icon(self):
        tray = MushTrayButton()
        self.addCleanup(tray.deleteLater)
        self.assertFalse(tray.icon().isNull())
        self.assertTrue((MUSH_ASSETS / "mush_icon.png").is_file())
        action_names = [action.text() for action in tray._menu.actions()]
        self.assertIn("Open MushClient", action_names)
        self.assertIn("Connect to PawPrints MUCK", action_names)
        self.assertIn("Disconnect from PawPrints MUCK", action_names)
        self.assertIn("Exit MushClient", action_names)

        self.assertTrue(tray.isHidden())
        tray.activate()
        tray.set_connected(True)
        self.assertFalse(tray.connect_action.isEnabled())
        self.assertTrue(tray.disconnect_action.isEnabled())
        tray.mark_activity()
        self.assertTrue(tray._flash_timer.isActive())
        lit_state = tray._lit
        tray._toggle_led()
        self.assertNotEqual(tray._lit, lit_state)
        tray._stop_activity()
        self.assertFalse(tray._flash_timer.isActive())
        self.assertFalse(tray._lit)

    def test_private_pages_are_not_replayed_in_public_and_cancelled_sends_are_removed(self):
        app = MushClientApp(self.account, self.connection, self.ai)
        self.addCleanup(app.close)
        app.connect_current()
        resident = app.world._resident_by_contact_id[SUPPLIED_CONTACTS[0].contact_id]
        resident.room_id = app.world.current_room
        app._request_resident_reply(resident, "This is a private page.", public=False)
        self.ai.reply("Private reply.")
        app._request_resident_reply(resident, "A public greeting.", public=True)
        self.assertNotIn("This is a private page.", repr(self.ai.requests[-1][2]))
        key = app._pending["history_key"]
        app.disconnect_player()
        self.assertEqual(app._chat_histories[key], [])
        self.assertFalse(app.world_timer.isActive())

    def test_navigation_does_not_require_a_model_and_idle_residents_never_chat(self):
        app = MushClientApp(self.account, self.connection, self.ai)
        self.addCleanup(app.close)
        app._execute_command("help")
        self.assertIn("Commands:", app.output.toPlainText())
        app.connect_current()
        self.ai.available = False
        app._execute_command("out")
        self.assertEqual(app.world.current_room, "square")
        resident = app.world._resident_by_contact_id[SUPPLIED_CONTACTS[0].contact_id]
        app._request_resident_reply(resident, "Hello", public=False)
        self.assertIn("direct local model is unavailable", app.output.toPlainText())
        self.assertEqual(self.ai.requests, [])
        self.ai.available = True
        resident.idle_only = True
        app._request_resident_reply(resident, "Hello", public=False)
        self.assertEqual(self.ai.requests, [])
        self.assertIn("idle and does not answer", app.output.toPlainText())

    def test_world_ticks_pause_during_outages_and_close(self):
        app = MushClientApp(self.account, self.connection, self.ai)
        self.addCleanup(app.close)
        app.connect_current()
        self.assertTrue(app.world_timer.isActive())
        with patch.object(app.world, "advance", return_value=[]) as advance:
            self.connection.chat_available = False
            app._advance_world()
            advance.assert_not_called()
            self.connection.chat_available = True
            app._advance_world()
            advance.assert_called_once()
        self.assertTrue(MushWorld._in_hours(("19:00", "25:30"), datetime(2011, 1, 1, 1)))
        self.assertFalse(MushWorld._in_hours(("19:00", "25:30"), datetime(2011, 1, 1, 10)))
        app.close()
        self.assertFalse(app.world_timer.isActive())
        self.assertFalse(app.connected)

    def test_desktop_launch_tray_network_and_file_close_remove_the_whole_window(self):
        from win7_2011.win7sim.desktop import DesktopPage

        desktop = DesktopPage(self.account)
        self.addCleanup(desktop.deleteLater)
        self.addCleanup(desktop.close)
        self.addCleanup(desktop.stop_session)
        desktop.resize(1100, 780)
        desktop.show()
        self.qt_app.processEvents()
        self.assertTrue(desktop.mush_tray.isHidden())
        self.assertNotIn("mush-client", desktop._windows)
        desktop.open_mush_client()
        self.assertFalse(desktop.mush_tray.isHidden())
        desktop.mush_tray.connect_action.trigger()
        self.qt_app.processEvents()
        app = desktop._windows["mush-client"].widget()
        self.assertTrue(app.connected)
        self.assertTrue(desktop.mush_tray.connected)
        self.assertTrue(desktop.mush_tray._flash_timer.isActive())
        self.assertIn("mush-client", desktop._taskbar_buttons)
        desktop._windows["mush-client"].showMinimized()
        self.qt_app.processEvents()
        self.assertFalse(desktop.mush_tray.isHidden())
        self.assertTrue(any(
            "PawPrints" in event["description"]
            for event in desktop.network_tray._events
        ))

        file_menu = app.menu_bar.actions()[0].menu()
        close_action = next(
            action for action in file_menu.actions()
            if action.text() == "Close MushClient"
        )
        close_action.trigger()
        self.qt_app.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.qt_app.processEvents()
        self.assertNotIn("mush-client", desktop._windows)
        self.assertNotIn("mush-client", desktop._taskbar_buttons)
        self.assertFalse(desktop.mush_tray.connected)
        self.assertTrue(desktop.mush_tray.isHidden())
        desktop.open_mush_client()
        self.assertFalse(desktop.mush_tray.isHidden())
        desktop.mush_tray.exit_action.trigger()
        self.qt_app.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.qt_app.processEvents()
        self.assertNotIn("mush-client", desktop._windows)
        self.assertTrue(desktop.mush_tray.isHidden())


if __name__ == "__main__":
    unittest.main()
