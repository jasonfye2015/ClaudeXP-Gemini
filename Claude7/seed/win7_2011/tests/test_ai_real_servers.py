"""Opt-in integration checks against actual llama-server processes.

See REAL_AI_TESTS.md. Normal unittest discovery skips live checks without
touching a socket or looking for an executable.
Authenticated Windows recovery is separate in test_ai_real_auth.py; this
unloaded-model suite must continue to inject NoCredentials.
"""
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from win7_2011.tests.real_ai_support import LlamaRouter, RealHTTP, required
from win7_2011.win7sim.ai_service import AIChannel, AIService
from win7_2011.win7sim.ai_settings import AISettings, ROLE_LABELS, load_ai_settings, save_ai_settings
from win7_2011.win7sim import config
from win7_2011.win7sim.apps import MessengerApp
from win7_2011.win7sim.contacts import CONTACTS
from win7_2011.win7sim.messenger_context import input_size, model_input_budget, reply_reserve
from win7_2011.win7sim.service import ConnectionSimulator
from win7_2011.tests.test_messaging import sample_account
from win7_2011.win7sim.llama_cpp import LlamaCppClient
from win7_2011.win7sim.local_ai import FailureCategory


class NoCredentials:
    def get(self, *_args):
        return None


def recording_client(client_class, requests=None, responses=None):
    class RecordingClient(client_class):
        """Observe real transport calls; never replace server responses."""

        def __init__(self, parent):
            super().__init__(parent)
            self.requests = requests if requests is not None else []

        def _request(self, kind, method, url, payload=None):
            self.requests.append((kind, method, url, payload))
            super()._request(kind, method, url, payload)

        def _decode_response(self, raw):
            data = super()._decode_response(raw)
            if responses is not None and self._request_kind == "chat":
                responses.append(data)
            return data

    return RecordingClient


class RealServerTests(unittest.TestCase):
    def setUp(self):
        self.app = QApplication.instance() or QApplication([])
        self.ai = None

    def tearDown(self):
        if self.ai:
            self.ai.stop()
            self.ai.deleteLater()
            self.app.processEvents()

    def wait(self, condition, description="operation"):
        deadline = time.monotonic() + 180
        while not condition() and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(.01)
        self.assertTrue(condition(), f"Real-server timeout: {description}")

    def service(self, backend, http, primary, healthy=""):
        roles = dict.fromkeys(ROLE_LABELS, primary)
        if healthy:
            roles["background"] = healthy
        self.ai = AIService(
            settings=AISettings(backend=backend, url=http.url, models=roles),
            backend_factory=recording_client(LlamaCppClient),
            credential_store=NoCredentials(),
        )
        self.ai.test_connection()
        self.wait(lambda: not self.ai.is_busy, "initial discovery")
        self.assertTrue(self.ai.is_available("direct"), self.ai.status)
        self.assertIn(primary, self.ai.models_by_url[http.url])
        if healthy:
            self.assertTrue(self.ai.is_available("background"), self.ai.status)
            self.assertIn(healthy, self.ai.models_by_url[http.url])
        channel = AIChannel(self.ai)
        channel.setParent(self.ai)
        return channel

    def send(self, role="direct", text="Reply with only OK."):
        results = []
        slot = lambda *args: results.append(args)
        self.ai.jobFinished.connect(slot)
        try:
            job = self.ai.submit(role, [{"role": "user", "content": text}])
            self.wait(lambda: not self.ai.is_busy, "generation")
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0][0], job)
            self.assertTrue(results[0][1], results[0][2])
            self.assertTrue(results[0][2].strip())
        finally:
            self.ai.jobFinished.disconnect(slot)

    def chat_requests(self):
        return [row for row in self.ai.backend.requests if row[0] == "chat"]

    def recovery(self, channel, http, primary, healthy, remove, restore):
        # The last successful call must use primary: this exercises the actual
        # server's chat error shape, not just client-side discovery rejection.
        if healthy:
            self.send("background")
        self.send()
        remove()
        before = len(self.chat_requests())
        results = []
        channel.responseFinished.connect(lambda *args: results.append(args))
        failures = []
        categories = []

        def slot(*args):
            failures.append(args)
            categories.append(self.ai.backend.last_failure)
        self.ai.jobFinished.connect(slot)
        try:
            channel.send_chat([{"role": "user", "content": "Do not replay this failed message."}])
            # Queue another job for the same model before Qt delivers failure.
            queued = self.ai.submit("summary", [{"role": "user", "content": "Do not replay queued work."}])
            self.wait(lambda: not self.ai.is_busy, "missing/unloaded-model failure")
            self.assertEqual(len(results), 1)
            self.assertFalse(results[0][0])
            self.assertFalse(channel.is_busy)
            self.assertEqual(len(failures), 2)
            self.assertTrue(all(not row[1] for row in failures))
            self.assertEqual(categories[0], FailureCategory.MODEL_UNAVAILABLE,
                             "Real server error must be model-specific, not an endpoint outage")
            self.assertIn(queued, [row[0] for row in failures])
            self.assertEqual(len(self.chat_requests()), before + 1, "Queued work must not hit the server")
            # The queued service rejection resets last_failure after the first
            # signal, so inspect both its captured category and persisted state.
            self.assertIn((http.url, primary), self.ai._model_errors)
            self.assertFalse(self.ai.is_available("direct"))
            self.assertTrue(self.ai.connected, self.ai.status)
            self.assertIn(http.url, self.ai.models_by_url)
            self.assertNotIn(primary, self.ai.models_by_url[http.url])
            self.assertFalse(self.ai._endpoint_errors)
            self.assertIn("Messages are not resent", self.ai.status)
            with self.assertRaises(RuntimeError):
                channel.send_chat([])
            if healthy:
                self.assertTrue(self.ai.is_available("background"))
                self.send("background")
                self.assertFalse(self.ai.is_available("direct"))
            restore()
            # Restoration alone must not silently clear the service's failure.
            self.assertFalse(self.ai.is_available("direct"))
            before = len(self.chat_requests())
            request_count = len(self.ai.backend.requests)
            self.assertTrue(self.ai.can_reconnect)
            self.ai.reconnect()
            self.wait(lambda: not self.ai.is_busy, "explicit reconnect")
            self.assertTrue(channel.is_connected, self.ai.status)
            self.assertFalse(self.ai._model_errors)
            self.assertEqual(len(results), 1, "Reconnect must not replay channel responses")
            self.assertEqual(len(self.chat_requests()), before, "Reconnect must only discover models")
            self.assertTrue(all(row[0] == "models"
                                for row in self.ai.backend.requests[request_count:]))
            self.assertEqual(self.ai.queue_count, 0)
            self.send(text="This is a new message. Reply with only OK.")
            self.assertEqual(len(self.chat_requests()), before + 1)
            self.assertEqual(self.chat_requests()[-1][3]["messages"], [{
                "role": "user", "content": "This is a new message. Reply with only OK.",
            }])
        finally:
            self.ai.jobFinished.disconnect(slot)

    def test_llama_router_unload_and_reconnect(self):
        if os.environ.get("WIN7_REAL_LLAMA") != "1":
            self.skipTest("Set WIN7_REAL_LLAMA=1; see REAL_AI_TESTS.md")
        if required("WIN7_REAL_LLAMA_TEST_OWNED") != "YES":
            raise ValueError("Explicit test-owned router acknowledgement must be YES.")
        http = RealHTTP("llama_cpp", required("WIN7_REAL_LLAMA_URL"))
        primary = required("WIN7_REAL_LLAMA_PRIMARY")
        healthy = os.environ.get("WIN7_REAL_LLAMA_HEALTHY", "").strip()
        router = LlamaRouter(http, primary, healthy)
        router.prepare()
        props = http.request("GET", "/props")
        print(f"\nReal llama-server build: {props.get('build_info', 'not reported')}", flush=True)
        if not healthy:
            print("Same-endpoint healthy-model check NOT RUN: only one test preset supplied.", flush=True)
        self.addCleanup(router.restore)
        router.load(primary)
        if healthy:
            router.load(healthy)
        self.wait(lambda: all(router.models()[name] == "loaded"
                              for name in router.initial), "llama router model loads")
        channel = self.service("llama_cpp", http, primary, healthy)

        def remove():
            router.unload(primary)
            self.wait(lambda: router.models()[primary] == "unloaded", "llama router unload")

        def restore():
            router.load(primary)
            self.wait(lambda: router.models()[primary] == "loaded", "llama router reload")

        self.recovery(channel, http, primary, healthy, remove, restore)


class RealModelLimitTests(unittest.TestCase):
    """Independent Windows sizing checks; no unload/reconnect/auth scenarios."""

    wait = RealServerTests.wait

    def require_windows(self, flag):
        if os.environ.get(flag) != "1":
            self.skipTest(f"Set {flag}=1; see REAL_AI_TESTS.md")
        self.assertEqual(sys.platform, "win32", "Live model-limit certification requires Windows")
        self.assertEqual(required("WIN7_REAL_LIMIT_TEST_OWNED"), "YES",
                         "Reserve unauthenticated test endpoints and source models for this run")
        # This remains import-safe/offline by default. On Windows let Qt use its
        # native platform plugin rather than inheriting the suite's offscreen default.
        self.assertEqual(os.environ.get("QT_QPA_PLATFORM"), "windows",
                         "Set QT_QPA_PLATFORM=windows for native Windows controls")

    def exercise_limits(self, backend, small_http, small, large_http, large,
                        small_window=4096, large_window=8192):
        """Drive production widgets/transport; fixtures may also check this harness."""
        self.app = QApplication.instance() or QApplication([])
        requests, responses = [], []
        factory = recording_client(LlamaCppClient, requests, responses)
        original = [
            {"role": role, "content": f"Disposable turn {index}: " + "x" * 180}
            for index in range(30) for role in ("user", "assistant")
        ]
        # Never read/write the user's real AI settings or Messenger transcripts.
        with tempfile.TemporaryDirectory(prefix="win7-model-limits-") as directory:
            root = Path(directory)
            with patch.object(config, "SYSTEM_ROOT", root / "System"), \
                    patch.object(config, "MESSENGER_HISTORY", root / "Messenger"):
                save_ai_settings(AISettings(
                    backend, small_http.url, dict.fromkeys(ROLE_LABELS, small),
                ))
                config.save_messenger_history(CONTACTS[0].contact_id, original, "rook")
                internet = ConnectionSimulator()
                ai = messenger = None

                def start():
                    service = AIService(settings=load_ai_settings(), backend_factory=factory,
                                        credential_store=NoCredentials())
                    # Own the service before discovery so assertion failures also clean it up.
                    services.append(service)
                    service.test_connection()
                    self.wait(lambda: not service.is_busy, "model metadata")
                    self.assertTrue(service.is_available("direct"), service.status)
                    widget = MessengerApp(sample_account(), internet, ai_service=service)
                    widgets.append(widget)
                    return service, widget

                def chat_count():
                    return sum(row[0] == "chat" for row in requests)

                def send(text, http, model, window):
                    before = chat_count()
                    messenger.message_edit.setText(text)
                    self.assertTrue(messenger.send_button.isEnabled())
                    messenger.send_button.click()
                    self.wait(lambda: not ai.is_busy and not messenger.client.is_busy, "explicit send")
                    self.assertEqual(chat_count(), before + 1,
                                     f"One click must produce exactly one chat: {messenger.provider_status.text()}")
                    payload = [row for row in requests if row[0] == "chat"][-1][3]
                    reserve = reply_reserve(window)
                    self.assertEqual(payload["model"], model)
                    self.assertEqual(
                        [row for row in requests if row[0] == "chat"][-1][2],
                        http.url + "/v1/chat/completions",
                    )
                    self.assertEqual(payload["messages"][0]["role"], "system")
                    self.assertEqual(payload["messages"][1]["role"], "user")
                    self.assertEqual(payload["messages"][-1], {"role": "user", "content": text})
                    self.assertLessEqual(input_size(payload["messages"]) + reserve, window)
                    self.assertEqual(payload["max_tokens"], reserve)
                    generated = responses[-1].get("usage", {}).get("completion_tokens")
                    self.assertIs(type(generated), int, "Real generation must report output usage")
                    self.assertGreater(generated, 0)
                    self.assertLessEqual(generated, reserve, "Server must honor the reply cap")
                    saved = config.load_messenger_history(CONTACTS[0].contact_id, "rook")
                    self.assertEqual(saved[:len(original)], original)
                    self.assertEqual(len(saved), len(original) + 2 * chat_count())
                    self.assertEqual(saved[-2], {"role": "user", "content": text})
                    self.assertEqual(saved[-1]["role"], "assistant")
                    self.assertTrue(saved[-1]["content"].strip(), messenger.provider_status.text())
                    return payload

                services, widgets = [], []
                try:
                    ai, messenger = start()
                    self.assertEqual(ai.context_windows_by_url[small_http.url][small], small_window)
                    self.assertEqual(ai.context_for_role()[0], small_window)
                    self.assertEqual(messenger.context_budget.value(),
                                     model_input_budget(small_window, 131072))
                    metadata = [row for row in requests if row[0] == "context"]
                    self.assertTrue(metadata, "Production discovery must query live metadata")
                    self.assertEqual(metadata[0][2], small_http.url + "/props")
                    small_payload = send("First explicit send. Reply briefly.", small_http, small, small_window)
                    self.assertIn("older messages omitted", messenger.context_status.text())

                    # Native spinbox path, disk save, a fresh Python interpreter,
                    # and a newly constructed service/widget all see the same override.
                    manual = 3072
                    messenger.model_context_limit.setValue(manual)
                    messenger.model_context_limit.editingFinished.emit()
                    self.assertEqual(ai.context_for_role()[0], manual)
                    self.assertEqual(load_ai_settings().context_limits[small_http.url][small], manual)
                    self.assertEqual(chat_count(), 1, "Editing limits cannot generate")
                    subprocess.run([sys.executable, "-c", (
                        "import sys; from pathlib import Path; "
                        "from win7_2011.win7sim import config; "
                        "from win7_2011.win7sim.ai_settings import load_ai_settings; "
                        "config.SYSTEM_ROOT=Path(sys.argv[1]); "
                        "s=load_ai_settings(); "
                        "assert s.context_limits[s.url][s.models['direct']]==3072"
                    ), str(config.SYSTEM_ROOT)], check=True, timeout=30)
                    messenger.close()
                    ai.stop()
                    ai, messenger = start()
                    self.assertEqual(ai.context_for_role()[0], manual)
                    self.assertEqual(messenger.model_context_limit.value(), manual)
                    self.assertEqual(messenger.context_budget.value(), model_input_budget(manual, 131072))
                    self.assertEqual(chat_count(), 1, "Restart must not replay the saved transcript")
                    self.assertEqual(config.load_messenger_history(CONTACTS[0].contact_id, "rook"),
                                     messenger.contact_histories[CONTACTS[0].contact_id])
                    send("Explicit send after restart. Reply briefly.", small_http, small, manual)

                    ai.apply(AISettings(backend, large_http.url, dict.fromkeys(ROLE_LABELS, large)))
                    self.wait(lambda: not ai.is_busy, "large-model discovery")
                    self.assertEqual(chat_count(), 2, "Model switching is discovery only")
                    self.assertEqual(ai.context_windows_by_url[large_http.url][large], large_window)
                    self.assertEqual(ai.context_for_role()[0], large_window)
                    self.assertEqual(messenger.model_context_limit.value(), 0)
                    self.assertEqual(messenger.context_budget.value(),
                                     model_input_budget(large_window, 131072))
                    large_payload = send("Explicit send after switching. Reply briefly.",
                                         large_http, large, large_window)
                    self.assertGreater(len(large_payload["messages"]), len(small_payload["messages"]))
                    ai.apply(AISettings(backend, small_http.url, dict.fromkeys(ROLE_LABELS, small)))
                    self.wait(lambda: not ai.is_busy, "small-model rediscovery")
                    self.assertEqual(chat_count(), 3)
                    self.assertEqual(ai.context_for_role()[0], manual)
                    self.assertEqual(messenger.model_context_limit.value(), manual)
                    send("Explicit send after switching back. Reply briefly.", small_http, small, manual)
                finally:
                    for service in services:
                        service.stop()
                    for widget in widgets:
                        widget.close()
                        widget.deleteLater()
                    for service in services:
                        service.deleteLater()
                    internet.deleteLater()
                    self.app.processEvents()

    def test_llama_model_limits_windows(self):
        self.require_windows("WIN7_REAL_LIMIT_LLAMA")
        small_http = RealHTTP("llama_cpp", required("WIN7_REAL_LIMIT_LLAMA_SMALL_URL"))
        large_http = RealHTTP("llama_cpp", required("WIN7_REAL_LIMIT_LLAMA_LARGE_URL"))
        self.assertNotEqual(small_http.url, large_http.url, "Use two independent single-model servers")
        small = required("WIN7_REAL_LIMIT_LLAMA_SMALL_MODEL")
        large = required("WIN7_REAL_LIMIT_LLAMA_LARGE_MODEL")
        self.assertNotEqual(small, large, "Use distinct disposable small/large model aliases")
        for http, model, window in ((small_http, small, 4096), (large_http, large, 8192)):
            props = http.request("GET", "/props")
            self.assertEqual(props.get("default_generation_settings", {}).get("n_ctx"), window,
                             "Use --parallel 1 and the documented runtime context size")
            self.assertEqual([row["id"] for row in http.request("GET", "/v1/models")["data"]], [model])
            print(f"\nWindows {sys.getwindowsversion().major}.{sys.getwindowsversion().minor}; "
                  f"llama-server {props.get('build_info', 'build not reported')} n_ctx={window}", flush=True)
        self.exercise_limits("llama_cpp", small_http, small, large_http, large)
