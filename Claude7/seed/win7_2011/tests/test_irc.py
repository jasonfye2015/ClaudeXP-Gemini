import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import json
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from PySide6.QtCore import QEvent, QPoint, Signal
from PySide6.QtWidgets import QApplication

from win7_2011.tests.test_mush import make_account, FakeAIService, FakeConnection
from win7_2011.win7sim.irc import IRCClientApp
from win7_2011.win7sim.irc_tray import IRCTrayButton
from win7_2011.win7sim.irc_world import IRCWorld, IRCWorldError, nick_key
from win7_2011.win7sim.llm_activity import LLMActivityLog


class ActivityRecordingFakeAIService(FakeAIService):
    """Fake service that emits the same activity signals as a dispatched AI job."""

    llmRequestSent = Signal(int, str, str, object)
    llmResponseCaptured = Signal(int, str, bool, str)

    def submit(self, role, messages, input_budget=None, output_limit=None):
        request_id = super().submit(role, messages, input_budget, output_limit)
        self.llmRequestSent.emit(
            request_id,
            role,
            self.settings.models[role],
            [dict(message) for message in messages],
        )
        return request_id

    def reply(self, text, success=True):
        request_id, role, *_ = self.requests[-1]
        self.llmResponseCaptured.emit(request_id, role, success, text)
        super().reply(text, success)


class IRCTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.account = make_account()
        self.service = FakeConnection()
        self.ai = FakeAIService()
        self.profile_storage = tempfile.TemporaryDirectory()
        self.addCleanup(self.profile_storage.cleanup)
        self.profile_storage_patch = patch(
            "win7_2011.win7sim.irc.config.USER_PROFILES",
            Path(self.profile_storage.name),
        )
        self.profile_storage_patch.start()
        self.addCleanup(self.profile_storage_patch.stop)

    def client(self):
        world = IRCWorld(self.account, now=lambda: datetime(2011, 10, 12, 20))
        client = IRCClientApp(self.account, self.service, self.ai, world=world)
        self.addCleanup(client.deleteLater)
        self.addCleanup(client.close)
        client.show()
        self.app.processEvents()
        return client

    def resident(self, client):
        actor = client.world.actors[nick_key("Shadowpaw")]
        actor.online = True
        actor.memberships = {"#furnet", "#help"}
        return actor

    def background_model(self, client, *, available=True):
        self.ai.settings = SimpleNamespace(
            models={"background": "test-background"}
        )
        self.ai.background_available = available
        self.ai.changed.emit()
        return client

    def only_resident_online(self, client):
        for actor in client.world.actors.values():
            actor.online = False
            actor.memberships.clear()
        return self.resident(client)

    def test_supplied_network_regulars_adult_filter_and_identity_normalization(self):
        world = IRCWorld(self.account)
        self.assertEqual(world.network["server"], "FurNet.IRC")
        self.assertEqual(world.network["port"], 6667)
        self.assertEqual(len(world.channels), 5)
        self.assertEqual(sum(not a.bot and not a.idle for a in world.actors.values()), 62)
        self.assertEqual(world.excluded_minor_names, {"Zeph", "Gill"})
        self.assertNotIn(nick_key("Zeph"), world.actors)
        self.assertNotIn(nick_key("Gill"), world.actors)
        self.assertTrue(world.actors[nick_key("FurBot")].bot)
        self.assertEqual(nick_key("Fox[away]"), nick_key("fox{away}"))
        self.assertTrue(world.excluded_unverified_names)
        with tempfile.TemporaryDirectory() as root:
            Path(root, "network.json").write_text("{broken")
            with self.assertRaises(IRCWorldError):
                IRCWorld(self.account, root=root)

    def test_autonomous_candidates_exclude_bots_idle_and_nonregular_actors(self):
        world = IRCWorld(self.account)
        world.connect()
        world.joined = {"#furnet"}
        for actor in world.actors.values():
            actor.online = False
            actor.memberships.clear()
        regular = world.actors[nick_key("Shadowpaw")]
        regular.online = True
        regular.memberships = {"#furnet"}
        bot = world.actors[nick_key("FurBot")]
        bot.online = True
        bot.memberships = {"#furnet"}
        idle = next(actor for actor in world.actors.values() if actor.idle)
        idle.online = True
        idle.memberships = {"#furnet"}
        candidates = world.conversation_candidates()
        self.assertEqual(candidates, [(regular, "#furnet")])
        self.assertFalse(bot.age_verified)
        self.assertFalse(idle.supplied_regular)

    def test_auto_login_motd_and_join_use_selected_fursona_not_shared_desktop_name(self):
        client = self.client()
        self.assertTrue(client.world.connected)
        self.assertEqual(client.world.nick, "Rook")
        self.assertEqual(client.world.profile_id, "profile-rook")
        self.assertEqual(client.world.joined, {"#furnet"})
        self.assertEqual(client.current_target(), "#furnet")
        self.assertIn("Unreal3.1.1-Darkshades", client._outputs["Status"].toPlainText())
        self.assertIn("Message of the Day", client._outputs["Status"].toPlainText())
        self.assertTrue(client.timer.isActive())
        client.connect_current()
        self.assertEqual(client._outputs["Status"].toPlainText().count("001 Rook"), 1)

    def test_irc_commands_nicks_away_channels_and_local_services_need_no_model(self):
        client = self.client()
        self.ai.available = False
        client.execute("/join #GAMING")
        self.assertIn("#gaming", client.world.joined)
        client.execute("/nick Rook_2011")
        self.assertEqual(client.world.nick, "Rook_2011")
        client.execute("/nick invalid nick")
        self.assertEqual(client.world.nick, "Rook_2011")
        client.execute("/away Back later")
        self.assertEqual(client.world.away, "Back later")
        client.execute("/away")
        self.assertFalse(client.world.away)
        client.execute("/msg NickServ HELP")
        self.assertIn("no password", client._outputs["NickServ"].toPlainText())
        client.execute("/join #furnet")
        client.execute("!time")
        self.assertIn("year 2011", client._outputs["#furnet"].toPlainText())
        client.execute("/part")
        self.assertNotIn("#furnet", client.world.joined)
        client.execute("Not actually sent")
        self.assertIn("Join this channel", client._outputs["#furnet"].toPlainText())
        self.assertEqual(self.ai.requests, [])
        self.resident(client)
        client.execute("/whois Shadowpaw")
        self.assertIn("shadow@users.FurNet.IRC", client.tabs.currentWidget().toPlainText())
        client.execute("/list")
        self.assertIn("#furry-artists", client._outputs["Status"].toPlainText())

    def test_private_messages_are_bounded_profile_scoped_and_never_enter_public_context(self):
        client = self.client()
        actor = self.resident(client)
        client.execute("/msg shadowpaw private-note")
        self.assertIn("is typing", client.typing_label.text())
        _, role, messages, budget = self.ai.requests[-1]
        self.assertEqual(role, "direct")
        self.assertGreater(budget, 0)
        self.assertIn("Current player: Rook", messages[0]["content"])
        self.assertIn(self.account.active_profile.bio, messages[0]["content"])
        self.assertNotIn("Moss", messages[0]["content"])
        self.ai.reply("A private answer.")
        self.assertIn("<Shadowpaw> A private answer.", client._outputs["Shadowpaw"].toPlainText())
        # Hold this one actor in the channel to make the public reply deterministic.
        for other in client.world.members("#furnet"):
            if other is not actor and not other.bot:
                other.memberships.discard("#furnet")
        client.execute("/join #furnet")
        client.execute("public-note")
        self.assertNotIn("private-note", repr(self.ai.requests[-1][2]))
        self.ai.reply("A public answer.")
        self.assertIn("A public answer.", client._outputs["#furnet"].toPlainText())
        client.disconnect_server()
        self.account.active_profile_id = "profile-moss"
        client.connect_current()
        self.resident(client)
        client.execute("/msg Shadowpaw Moss-message")
        messages = self.ai.requests[-1][2]
        self.assertEqual(len(messages), 2)
        self.assertIn("Current player: Moss", messages[0]["content"])
        self.assertNotIn("private-note", repr(messages))
        self.ai.reply("Hello Moss.")

    def test_outage_cancels_request_without_retry_and_reconnects_on_recovery(self):
        client = self.client()
        self.resident(client)
        client.execute("/msg Shadowpaw pending-note")
        key = client._pending["key"]
        count = len(self.ai.requests)
        self.service.chat_available = False
        self.service.stateChanged.emit("offline", "Service interrupted")
        self.assertFalse(client.world.connected)
        self.assertFalse(client.timer.isActive())
        self.assertEqual(client._histories[key], [])
        self.service.chat_available = True
        self.service.stateChanged.emit("online", "Service restored")
        self.assertTrue(client.world.connected)
        self.assertEqual(len(self.ai.requests), count)
        client.disconnect_server()
        self.service.stateChanged.emit("online", "Service restored")
        self.assertFalse(client.world.connected)

    def test_rejected_reply_and_idle_nick_do_not_create_fake_chat(self):
        client = self.client()
        actor = self.resident(client)
        client.execute("/msg Shadowpaw rejected-turn")
        key = client._pending["key"]
        self.ai.reply("Model error", success=False)
        self.assertEqual(client._histories[key], [])
        self.assertIn("Model error", client._outputs["Shadowpaw"].toPlainText())
        actor.idle = True
        client.execute("/msg Shadowpaw Another message")
        self.assertEqual(len(self.ai.requests), 1)
        self.assertIn("idle and does not answer", client._outputs["Shadowpaw"].toPlainText())
        with patch.object(client.world, "tick", return_value=[]) as tick:
            client._tick()
            tick.assert_called_once()
        self.account.active_profile_id = "profile-moss"
        client._tick()
        self.assertFalse(client.world.connected)

    def test_autonomous_regulars_are_throttled_and_missing_model_disables_controls(self):
        client = self.client()
        actor = self.only_resident_online(client)
        self.assertFalse(client.autonomous_enabled_action.isEnabled())
        self.assertFalse(client.frequency_actions[20].isEnabled())
        self.assertIn("no background model", client.status_label.toolTip().lower())
        self.assertFalse(client._maybe_start_autonomous())
        self.assertEqual(self.ai.requests, [])

        self.background_model(client)
        self.assertTrue(client.autonomous_enabled_action.isEnabled())
        self.assertTrue(client.autonomous_enabled_action.isChecked())
        client._autonomous_remaining = 1
        self.assertFalse(client._maybe_start_autonomous())
        client._autonomous_remaining = 0
        self.assertTrue(client._maybe_start_autonomous())
        self.assertEqual(self.ai.requests[-1][1], "background")
        self.assertEqual(
            self.ai.output_limits[self.ai.requests[-1][0]], 128
        )
        self.assertEqual(client._pending_autonomous["nick"], actor.nick)
        self.assertEqual(client._autonomous_remaining, 20 * 60)
        self.assertFalse(client._maybe_start_autonomous())
        self.assertEqual(
            sum(request[1] == "background" for request in self.ai.requests), 1
        )
        self.ai.reply("Hey, how's the art project going?")
        self.assertIn(
            "<Shadowpaw> Hey, how's the art project going?",
            client._outputs["#furnet"].toPlainText(),
        )

    def test_autonomous_prompts_and_results_are_logged_only_for_active_fursona(self):
        self.ai = ActivityRecordingFakeAIService()
        client = self.client()
        active_log = LLMActivityLog(self.account.active_profile_id)
        active_log.connect_service(self.ai)
        other_log = LLMActivityLog("profile-moss")
        other_log.record_request(
            901,
            "direct",
            "Moss-only model",
            [{"role": "user", "content": "Moss-only activity"}],
        )
        other_log.record_response(901, "direct", True, "Moss-only response")
        other_profile_text = other_log.read_recent_text()

        self.only_resident_online(client)
        self.background_model(client)
        client._autonomous_remaining = 0
        self.assertTrue(client._maybe_start_autonomous())
        success_request_id = self.ai.requests[-1][0]
        self.ai.reply("A spontaneous public greeting.", success=True)

        client._autonomous_remaining = 0
        self.assertTrue(client._maybe_start_autonomous())
        failure_request_id = self.ai.requests[-1][0]
        self.ai.reply("Local model unavailable.", success=False)

        self.assertEqual(
            active_log.path,
            Path(self.profile_storage.name) / "profile-rook" / "llm-activity.txt",
        )
        active_text = active_log.read_recent_text()
        entries = [
            json.loads(line)
            for line in active_text.splitlines()
            if line.startswith('{"time":')
        ]
        self.assertEqual(
            [(entry["request_id"], entry["event"]) for entry in entries],
            [
                (success_request_id, "PROMPT SENT"),
                (success_request_id, "MODEL OUTPUT"),
                (failure_request_id, "PROMPT SENT"),
                (failure_request_id, "REQUEST ERROR"),
            ],
        )
        self.assertTrue(
            all(
                entry["role"] == "Background community activity"
                and entry["model"] == "test-background"
                for entry in entries
            )
        )
        self.assertIn("Write one friendly, natural IRC opening message now.", active_text)
        self.assertIn("A spontaneous public greeting.", active_text)
        self.assertIn("Local model unavailable.", active_text)
        self.assertNotIn("Moss-only activity", active_text)
        self.assertNotIn("Moss-only response", active_text)
        self.assertEqual(other_log.read_recent_text(), other_profile_text)

    def test_autonomous_public_context_excludes_player_private_details_and_routes_traffic(self):
        client = self.client()
        actor = self.only_resident_online(client)
        self.background_model(client)
        # Add a private manual transcript that autonomous public messages must not see.
        client.execute("/msg Shadowpaw private-note-that-must-not-leak")
        self.ai.reply("A private reply.")
        transfer_events = []
        client.networkTransferRequested.connect(
            lambda direction, size, desc: transfer_events.append(
                (direction, size, desc)
            )
        )
        client._autonomous_remaining = 0
        self.assertTrue(client._maybe_start_autonomous())
        request = self.ai.requests[-1]
        self.assertEqual(request[1], "background")
        prompt = request[2][0]["content"]
        self.assertIn("public channel #furnet", prompt)
        self.assertNotIn("private-note-that-must-not-leak", repr(request[2]))
        self.assertNotIn(self.account.active_profile.bio, prompt)
        self.assertNotIn("Friendship with", prompt)
        self.ai.reply("A harmless public opener.")
        self.assertIn(
            "<Shadowpaw> A harmless public opener.",
            client._outputs["#furnet"].toPlainText(),
        )
        self.assertTrue(any(event[0] == "incoming" for event in transfer_events))
        self.assertNotIn(
            "A harmless public opener.",
            client._outputs["Shadowpaw"].toPlainText(),
        )
        self.assertTrue(actor.age_verified)
        client.tabs.setCurrentWidget(client._tab("#furnet"))
        client.execute("I saw your note.")
        continuation = self.ai.requests[-1]
        self.assertEqual(continuation[1], "direct")
        self.assertIn(
            "Your last spontaneous public message in this channel was",
            continuation[2][0]["content"],
        )
        self.assertIn("A harmless public opener.", continuation[2][0]["content"])
        self.assertNotIn("private-note-that-must-not-leak", repr(continuation[2]))

    def test_unsolicited_private_messages_are_opt_in_and_isolated(self):
        client = self.client()
        self.only_resident_online(client)
        self.background_model(client)
        client._autonomous_remaining = 0
        self.assertTrue(client._maybe_start_autonomous())
        self.assertFalse(client._pending_autonomous["private"])
        self.ai.reply("Public only.")

        self.assertTrue(
            client.preferences.update("unsolicited_private", True)
        )
        client._refresh_autonomous_controls()
        client._autonomous_remaining = 0
        with patch.object(client, "_choose_autonomous_private", return_value=True):
            self.assertTrue(client._maybe_start_autonomous())
        self.assertTrue(client._pending_autonomous["private"])
        private_request = self.ai.requests[-1]
        private_prompt = private_request[2][0]["content"]
        self.assertIn("Send this only as a private message", private_prompt)
        self.assertNotIn(self.account.active_profile.bio, private_prompt)
        self.ai.reply("A quiet private hello.")
        self.assertIn(
            "<Shadowpaw> A quiet private hello.",
            client._outputs["Shadowpaw"].toPlainText(),
        )
        self.assertNotIn(
            "A quiet private hello.",
            client._outputs["#furnet"].toPlainText(),
        )

    def test_autonomous_requests_cancel_on_profile_change_and_close(self):
        client = self.client()
        self.only_resident_online(client)
        self.background_model(client)
        client._autonomous_remaining = 0
        self.assertTrue(client._maybe_start_autonomous())
        self.account.active_profile_id = "profile-moss"
        client._check_identity()
        self.assertFalse(client.world.connected)
        self.assertIsNone(client._pending_autonomous)
        self.assertFalse(client.autonomous_client.is_busy)

    def test_autonomous_preferences_stay_with_the_selected_fursona(self):
        client = self.client()
        self.assertTrue(client.preferences.update("autonomous_enabled", False))
        self.assertTrue(client.preferences.update("frequency_minutes", 10))
        self.assertTrue(client.preferences.update("unsolicited_private", True))

        self.account.active_profile_id = "profile-moss"
        client._check_identity()
        self.assertTrue(client.preferences.enabled)
        self.assertEqual(client.preferences.frequency_minutes, 20)
        self.assertFalse(client.preferences.unsolicited_private)

        client.connect_current()
        self.account.active_profile_id = "profile-rook"
        client._check_identity()
        self.assertFalse(client.preferences.enabled)
        self.assertEqual(client.preferences.frequency_minutes, 10)
        self.assertTrue(client.preferences.unsolicited_private)

    def test_autonomous_clock_pauses_for_maintenance_and_resets_after_outage(self):
        client = self.client()
        self.only_resident_online(client)
        self.background_model(client)
        client._autonomous_remaining = 100
        client._autonomous_last_tick = 100
        self.ai.background_paused = True
        with patch("win7_2011.win7sim.irc.time.monotonic", return_value=1000):
            client._advance_autonomous_clock()
        self.assertEqual(client._autonomous_remaining, 100)
        self.assertFalse(client._maybe_start_autonomous())

        self.ai.background_paused = False
        with patch("win7_2011.win7sim.irc.time.monotonic", return_value=1030):
            client._advance_autonomous_clock()
        self.assertEqual(client._autonomous_remaining, 70)
        client._autonomous_remaining = 0
        self.assertTrue(client._maybe_start_autonomous())
        request_count = len(self.ai.requests)
        self.service.chat_available = False
        self.service.stateChanged.emit("offline", "Service interrupted")
        self.assertFalse(client.world.connected)
        self.assertIsNone(client._pending_autonomous)
        self.service.chat_available = True
        self.service.stateChanged.emit("online", "Service restored")
        self.assertTrue(client.world.connected)
        self.assertEqual(len(self.ai.requests), request_count)
        self.assertEqual(client._autonomous_remaining, 20 * 60)

        self.account.active_profile_id = "profile-rook"
        client.connect_current()
        self.only_resident_online(client)
        client._autonomous_remaining = 0
        self.assertTrue(client._maybe_start_autonomous())
        client.stop()
        self.assertIsNone(client._pending_autonomous)
        self.assertFalse(client.autonomous_client.is_busy)

    def test_tray_independent_green_send_red_receive_and_lifecycle(self):
        tray = IRCTrayButton()
        self.addCleanup(tray.deleteLater)
        self.assertTrue(tray.isHidden())
        self.assertFalse(tray.icon().isNull())
        tray.activate()
        tray.set_state(True, "Rook", True)
        self.assertEqual(tray.away_action.text(), "Set Available")
        self.assertFalse(tray.connect_action.isEnabled())
        self.assertTrue(tray.disconnect_action.isEnabled())
        events = []
        tray.closeRequested.connect(lambda: events.append("close"))
        tray.close_action.trigger()
        self.assertEqual(events, ["close"])
        tray.mark_transfer("outgoing", 100, "send")
        self.assertTrue(tray._lit["outgoing"])
        self.assertFalse(tray._lit["incoming"])
        tray.mark_transfer("incoming", 100, "receive")
        self.assertTrue(tray._lit["incoming"])
        self.assertIn("Green = sending · Red = receiving", tray.toolTip())
        for _ in range(6):
            tray._blink()
        self.assertFalse(tray.timer.isActive())
        self.assertFalse(any(tray._lit.values()))
        tray.deactivate()
        self.assertTrue(tray.isHidden())

    def test_desktop_auto_connect_tray_menu_window_close_and_leftward_placement(self):
        from win7_2011.win7sim.desktop import DesktopPage
        desktop = DesktopPage(self.account)
        self.addCleanup(desktop.deleteLater)
        self.addCleanup(desktop.close)
        self.addCleanup(desktop.stop_session)
        desktop.resize(960, 640)
        desktop.show()
        self.app.processEvents()
        self.assertTrue(desktop.irc_tray.isHidden())
        self.assertNotIn("irc-client", desktop._windows)
        client = desktop.open_irc_client()
        self.app.processEvents()
        self.assertTrue(client.world.connected)
        self.assertFalse(desktop.irc_tray.isHidden())
        self.assertEqual(desktop.irc_tray.nick, "Rook")
        self.assertIs(
            desktop.tray_icon_layout.itemAt(0).widget(), desktop.defender_tray
        )
        self.assertIs(desktop.tray_icon_layout.itemAt(1).widget(), desktop.irc_tray)
        icon_right = desktop.irc_tray.mapTo(desktop.system_tray, QPoint(desktop.irc_tray.width(), 0)).x()
        clock_left = desktop.clock_panel.mapTo(desktop.system_tray, QPoint(0, 0)).x()
        self.assertLess(icon_right, clock_left)
        self.assertTrue(any("FurNet" in e["description"] for e in desktop.network_tray._events))
        desktop.irc_tray.away_action.trigger()
        self.assertTrue(client.world.away)
        desktop._windows["irc-client"].showMinimized()
        self.app.processEvents()
        self.assertFalse(desktop.irc_tray.isHidden())
        desktop.irc_tray.open_action.trigger()
        self.assertFalse(desktop._windows["irc-client"].isMinimized())
        # File Exit closes the MDI window, not just the client child.
        client.request_close()
        self.app.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()
        self.assertNotIn("irc-client", desktop._windows)
        self.assertNotIn("irc-client", desktop._taskbar_buttons)
        self.assertTrue(desktop.irc_tray.isHidden())
        client = desktop.open_irc_client()
        self.app.processEvents()
        self.assertTrue(client.world.connected)
        desktop.irc_tray.exit_action.trigger()
        self.app.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()
        self.assertTrue(desktop.irc_tray.isHidden())
        final_client = desktop.open_irc_client()
        self.app.processEvents()
        desktop.stop_session()
        self.assertFalse(final_client.world.connected)
        self.assertFalse(final_client.timer.isActive())
        self.assertFalse(desktop.irc_tray.timer.isActive())


if __name__ == "__main__":
    unittest.main()
