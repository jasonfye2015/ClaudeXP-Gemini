"""Generation failure categories and endpoint-scoped availability over real HTTP."""
import json
import os
import socket
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from win7_2011.tests.test_messaging import sample_account
from win7_2011.win7sim import config
from win7_2011.win7sim.ai_service import AIService, AIChannel
from win7_2011.win7sim.ai_settings import AISettings, ROLE_LABELS
from win7_2011.win7sim.apps import MessengerApp
from win7_2011.win7sim.local_ai import FailureCategory
from win7_2011.win7sim.options import OptionsWindow
from win7_2011.win7sim.service import ConnectionSimulator


class FailureHandler(BaseHTTPRequestHandler):
    def respond(self, status, data):
        raw = data if isinstance(data, bytes) else json.dumps(data).encode()
        try:
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_GET(self):
        self.server.gets.append(self.path)
        if self.path == "/props":
            self.respond(*getattr(self.server, "context_props", (404, {})))
            return
        self.respond(self.server.discovery_status, {
            "models": [{"name": name} for name in self.server.models],
            "data": [{"id": name} for name in self.server.models],
        })

    def do_POST(self):
        payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if self.path == "/api/show":
            self.respond(*getattr(self.server, "context_metadata", {}).get(payload["model"], (404, {})))
            return
        if self.path in ("/apply-template", "/tokenize"):
            self.respond(404, {})
            return
        self.server.posts.append(payload)
        self.server.started.set()
        self.server.gate.wait(3)
        if self.server.drop:
            self.connection.shutdown(socket.SHUT_RDWR)
            self.connection.close()
            return
        status, body = self.server.model_responses.get(
            self.server.posts[-1]["model"], (self.server.status, self.server.body)
        )
        self.respond(status, body)

    def log_message(self, *_args):
        pass


class FailureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.storage = patch.object(config, "SYSTEM_ROOT", Path(self.directory.name))
        self.storage.start()
        self.servers, self.objects = [], []

    def tearDown(self):
        for obj in self.objects:
            if isinstance(obj, AIService):
                obj.stop()
            elif hasattr(obj, "close"):
                obj.close()
            obj.deleteLater()
        self.app.processEvents()
        for server, thread in self.servers:
            server.gate.set()
            server.shutdown()
            server.server_close()
            thread.join(2)
        self.storage.stop()
        self.directory.cleanup()

    def wait(self, condition):
        deadline = time.monotonic() + 3
        while not condition() and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(.005)
        self.assertTrue(condition(), "Local HTTP request timed out")

    def server(self, handler=FailureHandler):
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        server.status = server.discovery_status = 200
        server.body = {"message": {"content": "Reply"},
                       "choices": [{"message": {"content": "Reply"}}]}
        server.drop = False
        server.models = ["chat"]
        server.model_responses = {}
        server.gets, server.posts = [], []
        server.gate, server.started = threading.Event(), threading.Event()
        server.gate.set()
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.servers.append((server, thread))
        return server, f"http://127.0.0.1:{server.server_port}"

    def service(self, backend, url, other=None):
        ai = AIService(settings=AISettings(
            backend, url, dict.fromkeys(ROLE_LABELS, "chat"),
            {"background": other} if other else {},
        ))
        self.objects.append(ai)
        ai.test_connection()
        self.wait(lambda: not ai.is_busy)
        return ai

    def test_transport_auth_and_server_failures_invalidate_only_affected_endpoint(self):
        cases = [
            ("drop", 200, {}, FailureCategory.TRANSPORT),
            ("timeout", 200, {}, FailureCategory.TRANSPORT),
            ("auth", 401, {"error": "Invalid key"}, FailureCategory.AUTHENTICATION),
            ("auth", 403, {"error": "Forbidden"}, FailureCategory.AUTHENTICATION),
            ("server", 503, {"error": "Unavailable"}, FailureCategory.TRANSPORT),
        ]
        for backend in ("llama_cpp",):
            for mode, status, body, category in cases:
                with self.subTest(backend=backend, mode=mode, status=status):
                    primary, url = self.server()
                    secondary, other = self.server()
                    ai = self.service(backend, url, other)
                    options = OptionsWindow(ai)
                    self.objects.append(options)
                    internet = ConnectionSimulator()
                    self.objects.append(internet)
                    messenger = MessengerApp(sample_account(), internet, ai_service=ai)
                    self.objects.append(messenger)
                    results = []
                    ai.jobFinished.connect(lambda *args: results.append(args))
                    primary.status, primary.body = status, body
                    primary.drop = mode == "drop"
                    primary.gate.clear()
                    if mode == "timeout":
                        ai.backend.request_timeout_ms = 80
                    first = ai.submit("direct", [{"role": "user", "content": "Fail once"}])
                    self.wait(primary.started.is_set)
                    queued = ai.submit("summary", [{"role": "user", "content": "Do not retry"}])
                    healthy = ai.submit("background", [])
                    # Capture category before the next queued request resets it.
                    observed = []
                    ai.jobFinished.connect(lambda *_args: observed.append(ai.backend.last_failure))
                    if mode != "timeout":
                        primary.gate.set()
                    self.wait(lambda: len(results) == 3)
                    self.assertEqual([row[0] for row in results], [first, queued, healthy])
                    self.assertEqual([row[1] for row in results], [False, False, True])
                    self.assertEqual(observed[0], category)
                    self.assertFalse(ai.is_available("direct"))
                    self.assertFalse(ai.is_available("summary"))
                    self.assertTrue(ai.is_available("background"))
                    self.assertEqual(ai.models_by_url, {other: ["chat"]})
                    self.assertEqual(ai.available_models, ["chat"])
                    self.assertEqual(len(primary.posts), 1)
                    self.assertEqual(len(secondary.posts), 1)
                    self.assertFalse(messenger.send_button.isEnabled())
                    for text in (options.status_label.text(), options.activity_label.text(),
                                 messenger.provider_status.text()):
                        self.assertIn(url, text)
                        self.assertIn("Reconnect saved servers", text)
                    before = (len(primary.gets), len(primary.posts))
                    with self.assertRaises(RuntimeError):
                        ai.submit("direct", [])
                    self.assertEqual(before, (len(primary.gets), len(primary.posts)))
                    primary.gate.set()
                    primary.status, primary.drop = 200, False
                    ai.backend.request_timeout_ms = 120_000
                    ai.reconnect()
                    self.wait(lambda: not ai.is_busy)
                    self.assertTrue(ai.is_available("direct"))
                    self.assertNotIn("Reconnect saved servers", ai.status)
                    self.assertEqual(len(primary.posts), 1, "Reconnect must never replay messages")

    def test_healthy_server_survives_context_empty_protocol_and_request_failures(self):
        cases = [
            (500, {"error": "Context too large"}, FailureCategory.CONTEXT_LIMIT),
            (400, {"error": {"code": "context_length_exceeded", "message": "Too long"}},
             FailureCategory.CONTEXT_LIMIT),
            (200, {"error": {"type": "exceed_context_size_error", "message": "Too long"}},
             FailureCategory.CONTEXT_LIMIT),
            (200, {}, FailureCategory.EMPTY_REPLY),
            (200, {"message": {"content": " "}, "choices": [{"message": {"content": ""}}]},
             FailureCategory.EMPTY_REPLY),
            (200, b"invalid json", FailureCategory.PROTOCOL),
            (400, {"error": "Invalid parameter"}, FailureCategory.REQUEST),
            (404, {"error": "Route not found"}, FailureCategory.REQUEST),
        ]
        for backend in ("llama_cpp",):
            primary, url = self.server()
            ai = self.service(backend, url)
            channel = AIChannel(ai)
            results = []
            channel.responseFinished.connect(lambda *args: results.append(args))
            for status, body, category in cases:
                with self.subTest(backend=backend, category=category, body=body):
                    primary.status, primary.body = status, body
                    channel.send_chat([])
                    self.wait(lambda: not ai.is_busy)
                    self.assertFalse(results[-1][0])
                    self.assertEqual(ai.backend.last_failure, category)
                    self.assertTrue(ai.backend.is_connected)
                    self.assertTrue(channel.is_connected)
                    self.assertEqual(ai.models_by_url, {url: ["chat"]})
                    self.assertNotIn("Reconnect saved servers", ai.status)
            primary.status = 200
            primary.body = {"message": {"content": "Recovered"},
                            "choices": [{"message": {"content": "Recovered"}}]}
            channel.send_chat([])
            self.wait(lambda: not ai.is_busy)
            self.assertEqual(results[-1], (True, "Recovered"))
            self.assertIsNone(ai.backend.last_failure)

    def test_missing_model_after_discovery_keeps_other_models_and_endpoint_usable(self):
        cases = [
            ("llama_cpp", 404, {"error": {"code": "model_not_found", "message": "Unknown model"}}),
            ("llama_cpp", 503, {"error": {"type": "model_not_loaded", "message": "Model is not loaded"}}),
            ("llama_cpp", 200, {"error": {"message": "Model chat does not exist"}}),
        ]
        for backend, status, body in cases:
            with self.subTest(backend=backend, status=status):
                primary, url = self.server()
                secondary, other = self.server()
                primary.models = ["chat", "other"]
                ai = self.service(backend, url, other)
                # Two roles share the affected assignment; another endpoint
                # still advertises the very same model name.
                options = OptionsWindow(ai)
                self.objects.append(options)
                internet = ConnectionSimulator()
                self.objects.append(internet)
                messenger = MessengerApp(sample_account(), internet, ai_service=ai)
                self.objects.append(messenger)
                results, observed = [], []
                ai.jobFinished.connect(lambda *args: results.append(args))
                ai.jobFinished.connect(lambda *_args: observed.append(ai.backend.last_failure))
                ai.set_simulated_availability(True, True)
                primary.model_responses["chat"] = (status, body)
                primary.gate.clear()
                first = ai.submit("direct", [{"role": "user", "content": "Fail once"}])
                self.wait(primary.started.is_set)
                queued = ai.submit("summary", [{"role": "user", "content": "Never replay"}])
                primary.gate.set()
                self.wait(lambda: not ai.is_busy)
                self.assertEqual([row[0] for row in results], [first, queued])
                self.assertTrue(all(not row[1] for row in results))
                self.assertEqual(observed[0], FailureCategory.MODEL_UNAVAILABLE)
                self.assertFalse(ai.backend.is_connected)
                self.assertTrue(ai.connected, "The server is still reachable")
                self.assertFalse(ai.is_available("direct"))
                self.assertFalse(ai.is_available("summary"))
                self.assertTrue(ai.is_available("background"))
                self.assertEqual(ai.models_by_url, {url: ["other"], other: ["chat"]})
                self.assertEqual(ai.available_models, ["chat", "other"])
                self.assertEqual(ai._endpoint_errors, {})
                self.assertFalse(messenger.send_button.isEnabled())
                for text in (options.status_label.text(), options.activity_label.text(),
                             messenger.provider_status.text()):
                    self.assertIn("missing or unloaded", text)
                    self.assertIn(url, text)
                    self.assertIn("Load or reinstall", text)
                    self.assertIn("Reconnect saved servers", text)
                before = (len(primary.gets), len(primary.posts))
                with self.assertRaises(RuntimeError):
                    ai.submit("direct", [])
                self.assertEqual(before, (len(primary.gets), len(primary.posts)))

                # Switch the background assignment to the unaffected model on
                # the same endpoint; no discovery/reconnect action is required.
                ai.settings.models["background"] = "other"
                ai.settings.role_urls["background"] = url
                ai.set_simulated_availability(True, False)
                healthy = ai.submit("background", [])
                self.wait(lambda: not ai.is_busy)
                self.assertEqual(results[-1], (healthy, True, "Reply"))
                self.assertEqual([post["model"] for post in primary.posts], ["chat", "other"])
                self.assertIn("missing or unloaded", ai.status,
                              "A healthy job must not hide the unavailable assignment")
                self.assertIn("missing or unloaded", messenger.provider_status.text())
                self.assertIn("missing or unloaded", options.activity_label.text())

                # Discovery may keep advertising a model which the server has
                # unloaded. Reconnection is explicit and never resends work.
                primary.model_responses.clear()
                options.reconnect_button.click()
                self.wait(lambda: not ai.is_busy)
                self.assertTrue(ai.is_available("direct"))
                self.assertTrue(ai.is_available("summary"))
                self.assertNotIn("missing or unloaded", ai.status)
                self.assertEqual(len(primary.posts), 2)
                self.assertTrue(messenger.send_button.isEnabled())
                sent = ai.submit("direct", [{"role": "user", "content": "New message"}])
                self.wait(lambda: not ai.is_busy)
                self.assertEqual(results[-1], (sent, True, "Reply"))
                self.assertEqual(len(primary.posts), 3)

    def test_model_removed_from_discovery_before_job_invalidates_only_that_model(self):
        for backend in ("llama_cpp",):
            with self.subTest(backend=backend):
                primary, url = self.server()
                primary.models = ["chat", "other"]
                ai = self.service(backend, url)
                primary.models = ["other"]
                results = []
                ai.jobFinished.connect(lambda *args: results.append(args))
                ai.submit("direct", [])
                self.wait(lambda: not ai.is_busy)
                self.assertEqual(ai.backend.last_failure, FailureCategory.MODEL_UNAVAILABLE)
                self.assertFalse(results[-1][1])
                self.assertEqual(ai.models_by_url, {url: ["other"]})
                self.assertTrue(ai.connected)
                self.assertFalse(primary.posts)
                self.assertIn("Load or reinstall", ai.status)
                ai.reconnect()
                self.wait(lambda: not ai.is_busy)
                self.assertFalse(ai.is_available("direct"))
                self.assertIn("Unavailable assignments", ai.status)
                self.assertIn("Reconnect saved servers", ai.status)
                primary.models.append("chat")
                ai.reconnect()
                self.wait(lambda: not ai.is_busy)
                self.assertTrue(ai.is_available("direct"))
                self.assertFalse(primary.posts, "Discovery must never replay failed jobs")

    def test_last_model_unloaded_does_not_mark_healthy_endpoint_down(self):
        for backend in ("llama_cpp",):
            with self.subTest(backend=backend):
                primary, url = self.server()
                ai = self.service(backend, url)
                primary.status, primary.body = 404, {"error": "Model chat not found"}
                ai.submit("direct", [])
                self.wait(lambda: not ai.is_busy)
                self.assertEqual(ai.models_by_url, {url: []})
                self.assertEqual(ai.available_models, [])
                self.assertTrue(ai.connected)
                self.assertFalse(ai.is_available("direct"))
                self.assertEqual(ai._endpoint_errors, {})
                self.assertTrue(ai.can_reconnect)

    def test_explicit_cancellation_does_not_invalidate_endpoint_or_retry_work(self):
        for backend in ("llama_cpp",):
            with self.subTest(backend=backend):
                primary, url = self.server()
                ai = self.service(backend, url)
                primary.gate.clear()
                results = []
                ai.jobFinished.connect(lambda *args: results.append(args))
                active = ai.submit("direct", [])
                queued = ai.submit("direct", [])
                self.wait(primary.started.is_set)
                ai.cancel_all()
                self.wait(lambda: not ai.is_busy)
                self.assertEqual({row[0] for row in results}, {active, queued})
                self.assertTrue(all(row[1:] == (False, "Request cancelled.") for row in results))
                self.assertEqual(ai.backend.last_failure, FailureCategory.CANCELLED)
                self.assertTrue(ai.is_available("direct"))
                self.assertEqual(ai.models_by_url, {url: ["chat"]})
                self.assertEqual(len(primary.posts), 1)
                self.assertNotIn("Reconnect saved servers", ai.status)

    def test_failure_while_connecting_for_a_job_also_invalidates_endpoint(self):
        for backend in ("llama_cpp",):
            with self.subTest(backend=backend):
                primary, url = self.server()
                ai = self.service(backend, url)
                primary.discovery_status = 401
                results = []
                ai.jobFinished.connect(lambda *args: results.append(args))
                ai.submit("direct", [])
                self.wait(lambda: not ai.is_busy)
                self.assertFalse(results[0][1])
                self.assertFalse(ai.connected)
                self.assertFalse(ai.is_available("direct"))
                self.assertEqual(ai.models_by_url, {})
                self.assertFalse(primary.posts)

    def test_paused_jobs_on_failed_endpoint_finish_without_blocking_idle_reconnect(self):
        for backend in ("llama_cpp",):
            for keep_healthy in (False, True):
                with self.subTest(backend=backend, keep_healthy=keep_healthy):
                    primary, url = self.server()
                    secondary, other = self.server()
                    ai = self.service(backend, url, other if keep_healthy else None)
                    discovery_gets = len(primary.gets)
                    options = OptionsWindow(ai)
                    self.objects.append(options)
                    ai.set_simulated_availability(True, True)
                    primary.status, primary.body = 401, {"error": "Invalid key"}
                    primary.gate.clear()
                    results = []
                    ai.jobFinished.connect(lambda *args: results.append(args))
                    active = ai.submit("direct", [])
                    self.wait(primary.started.is_set)
                    summary = ai.submit("summary", [])
                    background = ai.submit("background", [])
                    primary.gate.set()
                    expected = 2 if keep_healthy else 3
                    self.wait(lambda: len(results) == expected)
                    self.assertEqual([row[0] for row in results[:2]], [active, summary])
                    self.assertTrue(all(not row[1] for row in results))
                    self.assertEqual(len(primary.posts), 1)
                    self.assertEqual(len(primary.gets), discovery_gets + 1,
                                     "Only the active job connects; queued failures must not probe")
                    self.assertFalse(secondary.posts)
                    if keep_healthy:
                        self.assertEqual(ai.queue_count, 1)
                        self.assertEqual(ai._queue[0].request_id, background)
                        self.assertTrue(ai.is_available("background"))
                        ai.set_simulated_availability(True, False)
                        self.wait(lambda: not ai.is_busy)
                        self.assertEqual(results[-1], (background, True, "Reply"))
                        self.assertEqual(len(secondary.posts), 1)
                    else:
                        self.assertEqual(results[-1][0], background)
                        self.assertTrue(ai.background_paused)
                    self.assertEqual(ai.queue_count, 0)
                    self.assertTrue(options.reconnect_button.isEnabled())
                    primary.status = 200
                    options.reconnect_button.click()
                    self.wait(lambda: not ai.is_busy)
                    self.assertTrue(ai.is_available("direct"))
                    self.assertEqual(len(primary.posts), 1)
