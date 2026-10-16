"""Coverage for the private, full-fidelity local-model activity log."""

import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEvent, QObject, Signal
from PySide6.QtWidgets import QApplication

from win7_2011.win7sim import config
from win7_2011.win7sim.ai_service import AIService
from win7_2011.win7sim.ai_settings import AISettings
from win7_2011.win7sim.desktop import DesktopPage
from win7_2011.win7sim.llm_activity import (
    LLMActivityApp, LLMActivityLog, LLMActivityMonitor,
)
from win7_2011.tests.test_mush import make_account


class DesktopActivityBackend(QObject):
    """Controlled transport for exercising the desktop's real AIService."""

    modelsListed = Signal(bool, object, str)
    connectionFinished = Signal(bool, str)
    responseFinished = Signal(bool, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_busy = False
        self.is_connected = False
        self.model_name = ""
        self.calls = []

    def list_models(self, _url):
        self.modelsListed.emit(
            True, ["test-direct", "test-background", "test-summary"], "Available."
        )

    def connect_to_server(self, _url, model):
        self.model_name = model
        self.is_connected = True
        self.connectionFinished.emit(True, "Connected.")

    def send_chat(self, messages):
        self.is_busy = True
        self.calls.append((self.model_name, messages))

    def finish(self, success, text):
        self.is_busy = False
        self.responseFinished.emit(success, text)

    def cancel(self):
        self.finish(False, "Cancelled.")


class LLMActivityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.profiles = self.root / "Profiles"
        patcher = patch.object(config, "USER_PROFILES", self.profiles)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.log = LLMActivityLog("test-fursona")

    def _dispose_widget(self, widget):
        widget.close()
        widget.deleteLater()
        self.app.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()

    def test_full_prompts_and_outputs_are_timestamped_exportable_and_clearable(self):
        messages = [
            {"role": "system", "content": "PRIVATE, COMPLETE system context\nSecond line"},
            {"role": "user", "content": "Exact user prompt"},
            {"role": "assistant", "content": "Prior conversation retained in the request"},
        ]
        output = "Unfiltered model output:\nfirst line\nsecond line"
        self.log.record_request(19, "direct", "NemoMix-12B", messages)
        self.log.record_response(19, "direct", True, output)
        text = self.log.read_recent_text()
        self.assertIn("PRIVATE, COMPLETE system context", text)
        self.assertIn("Exact user prompt", text)
        self.assertIn("Prior conversation retained in the request", text)
        self.assertIn(output, text)
        records = [json.loads(line) for line in text.splitlines() if line.startswith('{"time":')]
        self.assertEqual([record["event"] for record in records], ["PROMPT SENT", "MODEL OUTPUT"])
        self.assertTrue(all("T" in record["time"] and record["model"] == "NemoMix-12B"
                            for record in records))

        exported = self.root / "exported-llm-activity.txt"
        self.assertTrue(self.log.export(exported))
        self.assertEqual(exported.read_text(encoding="utf-8"), text)
        self.assertTrue(self.log.clear())
        self.assertEqual(self.log.read_recent_text(), "")
        self.assertEqual(exported.read_text(encoding="utf-8"), text)

    def test_log_window_updates_as_activity_arrives_and_monitor_tracks_each_phase(self):
        window = LLMActivityApp(self.log)
        self.addCleanup(self._dispose_widget, window)
        self.assertEqual(window.text.toPlainText(), "")
        self.log.record_request(
            2, "background", "Small local model",
            [{"role": "user", "content": "Update the local page."}],
        )
        self.assertIn("Update the local page.", window.text.toPlainText())

        monitor = LLMActivityMonitor()
        self.addCleanup(monitor.deleteLater)
        for phase, label in (
            ("sending", "Sending prompt"),
            ("generating", "Calculating model output"),
            ("output", "Delivering model output"),
        ):
            monitor.set_phase(2, "background", phase)
            self.assertEqual(monitor.phase, phase)
            self.assertIn(label, monitor.toolTip())
            self.assertTrue(monitor.blink_timer.isActive())
        monitor.set_phase(2, "background", "idle")
        self.assertEqual(monitor.phase, "output")
        monitor._clear_phase()
        self.assertEqual(monitor.phase, "idle")
        self.assertFalse(monitor.blink_timer.isActive())

        self.assertTrue(self.log.clear())
        self.assertEqual(window.text.toPlainText(), "")

    def test_failed_requests_are_logged_and_linked_to_their_model(self):
        self.log.record_request(
            23, "summary", "Summary-Model",
            [{"role": "user", "content": "Summarize this."}],
        )
        self.log.record_response(23, "summary", False, "Connection failed")
        text = self.log.read_recent_text()
        headers = [json.loads(line) for line in text.splitlines() if line.startswith('{"time":')]
        self.assertEqual(headers[-1]["event"], "REQUEST ERROR")
        self.assertEqual(headers[-1]["model"], "Summary-Model")
        self.assertIn("Connection failed", text)

    def test_search_finds_prompt_output_and_error_outside_the_recent_view(self):
        entries = [
            ({"time": "2026-10-12T10:00:00+00:00", "event": "PROMPT SENT",
              "request_id": 1, "role": "Direct", "model": "Local A"},
             "old-user-prompt"),
            ({"time": "2026-10-12T10:01:00+00:00", "event": "MODEL OUTPUT",
              "request_id": 1, "role": "Direct", "model": "Local A"},
             "old-model-output"),
            ({"time": "2026-10-12T10:02:00+00:00", "event": "REQUEST ERROR",
              "request_id": 2, "role": "Summary", "model": "Local B"},
             "old-request-error"),
        ]
        content = "".join(
            f"{json.dumps(header)}\n{body}\n\n" for header, body in entries
        )
        content += (
            json.dumps({
                "time": "2026-10-12T10:03:00+00:00", "event": "MODEL OUTPUT",
                "request_id": 3, "role": "Direct", "model": "Local A",
            })
            + "\n"
            + ("x" * (64 * 1024 - 4))
            + "boundary-query"
            + (" unrelated" * 240_000)
        )
        self.log.path.parent.mkdir(parents=True)
        self.log.path.write_text(content, encoding="utf-8")
        self.assertGreater(self.log.path.stat().st_size, self.log.VIEW_MAX_BYTES)
        self.assertNotIn("old-user-prompt", self.log.read_recent_text())

        matches = self.log.search("old-")
        self.assertEqual(
            [match["event"] for match in matches],
            ["PROMPT SENT", "MODEL OUTPUT", "REQUEST ERROR"],
        )
        self.assertEqual(
            [match["snippet"] for match in matches],
            ["old-user-prompt", "old-model-output", "old-request-error"],
        )
        boundary_match = self.log.search("BOUNDARY-QUERY")
        self.assertEqual(len(boundary_match), 1)
        self.assertEqual(boundary_match[0]["event"], "MODEL OUTPUT")

    def test_activity_window_search_results_navigate_without_loading_the_full_log(self):
        for index, (event, body) in enumerate((
            ("PROMPT SENT", "find-this-prompt"),
            ("MODEL OUTPUT", "find-this-output"),
            ("REQUEST ERROR", "find-this-error"),
        )):
            self.log.path.parent.mkdir(parents=True, exist_ok=True)
            with self.log.path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps({
                    "time": f"2026-10-12T10:0{index}:00+00:00",
                    "event": event,
                    "request_id": index,
                    "role": "Direct",
                    "model": "Local model",
                }) + f"\n{body}\n\n")
        with self.log.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({
                "time": "2026-10-12T10:03:00+00:00", "event": "MODEL OUTPUT",
                "request_id": 4, "role": "Direct", "model": "Local model",
            }) + "\n" + ("unrelated " * 240_000))

        window = LLMActivityApp(self.log)
        self.addCleanup(self._dispose_widget, window)
        window.search_input.setText("find-this")
        window.search_button.click()

        self.assertEqual(window.matches.count(), 3)
        self.assertIn("PROMPT SENT", window.text.toPlainText())
        self.assertIn("find-this-prompt", window.text.toPlainText())
        self.assertLess(len(window.text.toPlainText()), 1_000)
        window.next_button.click()
        self.assertIn("MODEL OUTPUT", window.text.toPlainText())
        self.assertIn("find-this-output", window.text.toPlainText())
        window.next_button.click()
        self.assertIn("REQUEST ERROR", window.text.toPlainText())
        self.assertIn("find-this-error", window.text.toPlainText())
        window.previous_button.click()
        self.assertIn("MODEL OUTPUT", window.text.toPlainText())
        self.assertTrue(self.log.clear())
        self.assertEqual(window.matches.count(), 0)
        self.assertEqual(window.text.toPlainText(), "")


class DesktopLLMActivityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_desktop_irc_activity_uses_selected_profile_log_and_viewer(self):
        with tempfile.TemporaryDirectory() as directory:
            profiles = Path(directory) / "Profiles"
            settings = AISettings(models={
                "direct": "test-direct",
                "background": "test-background",
                "summary": "test-summary",
            })
            with (
                patch.object(config, "USER_PROFILES", profiles),
                patch(
                    "win7_2011.win7sim.desktop.AIService",
                    side_effect=lambda parent: AIService(
                        parent,
                        backend_factory=DesktopActivityBackend,
                        settings=settings,
                    ),
                ),
            ):
                desktop = DesktopPage(make_account())
                try:
                    other_log = LLMActivityLog("profile-moss")
                    other_log.record_request(
                        901, "direct", "Moss-only model",
                        [{"role": "user", "content": "Moss-only activity"}],
                    )
                    other_log.record_response(901, "direct", True, "Moss-only result")
                    other_profile_before = other_log.path.read_bytes()

                    client = desktop.open_irc_client()
                    self.app.processEvents()
                    self.assertIs(client.ai_service, desktop.ai_service)
                    service = desktop.ai_service
                    self.assertIsInstance(service, AIService)
                    endpoint = service.settings.endpoint_for("background")
                    service.models_by_url[endpoint] = [
                        "test-direct", "test-background", "test-summary",
                    ]
                    service.connected = True

                    for actor in client.world.actors.values():
                        actor.online = False
                        actor.memberships.clear()
                    actor = client.world.actors["shadowpaw"]
                    actor.online = True
                    actor.memberships = {"#furnet", "#help"}
                    client._autonomous_remaining = 0
                    self.assertTrue(client._maybe_start_autonomous())
                    self.app.processEvents()
                    self.assertEqual(len(service.backend.calls), 1)
                    self.assertEqual(service.backend.calls[0][0], "test-background")
                    request_id = service._active.request_id

                    service.backend.finish(True, "A spontaneous public greeting.")
                    self.app.processEvents()

                    expected_path = profiles / "profile-rook" / "llm-activity.txt"
                    self.assertEqual(desktop.llm_activity_log.path, expected_path)
                    desktop.open_llm_activity()
                    activity_window = desktop._windows["llm-activity"].widget()
                    self.assertIsInstance(activity_window, LLMActivityApp)
                    self.assertEqual(activity_window.status.toolTip(), str(expected_path))
                    viewer_text = activity_window.text.toPlainText()
                    self.assertIn("Write one friendly, natural IRC opening message now.", viewer_text)
                    self.assertIn("A spontaneous public greeting.", viewer_text)
                    self.assertIn(f'"request_id": {request_id}', viewer_text)
                    records = [
                        json.loads(line)
                        for line in viewer_text.splitlines()
                        if line.startswith('{"time":')
                    ]
                    self.assertEqual(
                        [record["event"] for record in records],
                        ["PROMPT SENT", "MODEL OUTPUT"],
                    )
                    self.assertTrue(all(
                        record["role"] == "Background community activity"
                        and record["model"] == "test-background"
                        for record in records
                    ))
                    self.assertEqual(other_log.path.read_bytes(), other_profile_before)
                finally:
                    desktop.stop_session()
                    desktop.close()
                    desktop.deleteLater()
                    self.app.sendPostedEvents(None, QEvent.Type.DeferredDelete)
                    self.app.processEvents()


if __name__ == "__main__":
    unittest.main()
