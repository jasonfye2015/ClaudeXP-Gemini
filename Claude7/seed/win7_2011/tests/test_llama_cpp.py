import json
import os
import socket
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from win7_2011.tests.test_ui import sample_account
from win7_2011.win7sim import config
from win7_2011.win7sim.ai_service import AIChannel, AIService
from win7_2011.win7sim.ai_settings import AISettings, ROLE_LABELS, load_ai_settings
from win7_2011.win7sim.desktop import DesktopPage
from win7_2011.win7sim.llama_cpp import LlamaCppClient, normalize_llama_url
from win7_2011.win7sim.llama_server import LlamaServerProcess
from win7_2011.win7sim.local_ai import FailureCategory


class LlamaHandler(BaseHTTPRequestHandler):
    def respond(self, status, data):
        body = data if isinstance(data, bytes) else json.dumps(data).encode()
        try:
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_GET(self):
        if self.path == "/props":
            self.respond(404, {})
            return
        self.server.paths.append(self.path)
        self.server.get_started.set()
        self.server.get_gate.wait(3)
        self.respond(self.server.status, self.server.discovery)

    def do_POST(self):
        payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        self.server.posts.append((self.path, payload))
        self.server.post_started.set()
        self.server.post_gate.wait(3)
        self.respond(self.server.chat_status, self.server.chat)

    def log_message(self, *_args):
        pass


class LlamaTests(unittest.TestCase):
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
            if isinstance(obj, DesktopPage):
                obj.stop_session()
                obj.close()
            elif isinstance(obj, AIService):
                obj.stop()
            elif hasattr(obj, "cancel"):
                obj.cancel()
            obj.deleteLater()
        self.app.processEvents()
        for server, thread in self.servers:
            server.get_gate.set()
            server.post_gate.set()
            server.shutdown()
            server.server_close()
            thread.join(2)
        self.storage.stop()
        self.directory.cleanup()

    def server(self, models=("chat", "small"), handler=LlamaHandler):
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        server.discovery = {"data": [{"id": model} for model in models]}
        server.chat = {"choices": [{"message": {"role": "assistant", "content": "Fixture reply"}}]}
        server.status = server.chat_status = 200
        server.paths, server.posts = [], []
        server.get_started, server.post_started = threading.Event(), threading.Event()
        server.get_gate, server.post_gate = threading.Event(), threading.Event()
        server.get_gate.set()
        server.post_gate.set()
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.servers.append((server, thread))
        return server, f"http://127.0.0.1:{server.server_port}"

    def wait(self, condition):
        deadline = time.monotonic() + 3
        while not condition() and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(.005)
        self.assertTrue(condition(), "HTTP fixture request timed out")

    def client(self):
        client = LlamaCppClient()
        self.objects.append(client)
        return client

    def service(self, url, models=None, role_urls=None):
        ai = AIService(settings=AISettings(
            "llama_cpp", url, models or dict.fromkeys(ROLE_LABELS, "chat"),
            role_urls or {},
        ))
        self.objects.append(ai)
        ai.test_connection()
        self.wait(lambda: not ai.is_busy)
        return ai

    def test_discovery_chat_and_v1_prefix(self):
        server, url = self.server()
        client = self.client()
        connection, replies = [], []
        client.connectionFinished.connect(lambda *args: connection.append(args))
        client.responseFinished.connect(lambda *args: replies.append(args))
        client.connect_to_server(url + "/proxy/v1/", "chat")
        self.wait(lambda: bool(connection))
        self.assertTrue(connection[0][0])
        messages = [{"role": "system", "content": "Keep context"},
                    {"role": "user", "content": "Hello ü"}]
        client.send_chat(messages)
        self.wait(lambda: bool(replies))
        self.assertEqual(replies, [(True, "Fixture reply")])
        self.assertEqual(server.paths, ["/proxy/v1/models"])
        self.assertEqual(server.posts, [("/proxy/v1/chat/completions",
                                        {"model": "chat", "messages": messages, "stream": False})])
        for bad in ("https://example.com", "http://user:pass@localhost", "http://localhost:bad"):
            with self.assertRaises(ValueError):
                normalize_llama_url(bad)

    def test_managed_server_command_uses_localhost_gguf_and_selected_gpu_layers(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = root / "llama-server.exe"
            model = root / "NemoMix.gguf"
            executable.write_bytes(b"test executable")
            model.write_bytes(b"test model")
            server = LlamaServerProcess()
            with patch.object(server.process, "start") as start:
                server.start(
                    str(executable), str(model), "nemomix-12b",
                    "http://127.0.0.1:9931", 37,
                )
                self.assertEqual(server.process.program(), str(executable))
                self.assertEqual(server.process.arguments(), [
                    "--model", str(model), "--alias", "nemomix-12b",
                    "--host", "127.0.0.1", "--port", "9931",
                    "--n-gpu-layers", "37",
                ])
                start.assert_called_once()
            server.mark_ready()
            server.deleteLater()

    def test_nemomix_uses_mistral_template_and_repetition_control_not_alias(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = root / "llama-server.exe"
            executable.write_bytes(b"test executable")
            for filename in (
                "NemoMix-Unleashed-12B-Q4_K_M.gguf",
                "nemomix-unleashed-12b-Q8_0.GGUF",
                "NemoMix-Unleashed-12B.gguf",
            ):
                with self.subTest(filename=filename):
                    model = root / filename
                    model.write_bytes(b"test model")
                    server = LlamaServerProcess()
                    with patch.object(server.process, "start"):
                        server.start(
                            str(executable), str(model), "custom-chat-alias",
                            "http://127.0.0.1:9931", 99,
                        )
                    arguments = server.process.arguments()
                    self.assertEqual(arguments[-4:], [
                        "--chat-template", "mistral-v3-tekken",
                        "--dry-multiplier", "0.8",
                    ])
                    self.assertEqual(
                        arguments[arguments.index("--alias") + 1], "custom-chat-alias"
                    )
                    server.deleteLater()

    def test_unrelated_model_keeps_its_own_template_even_with_nemomix_alias(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = root / "llama-server.exe"
            model = root / "another-model.gguf"
            executable.write_bytes(b"test executable")
            model.write_bytes(b"test model")
            server = LlamaServerProcess()
            with patch.object(server.process, "start"):
                server.start(
                    str(executable), str(model), "NemoMix-Unleashed-12B",
                    "http://127.0.0.1:9931", 99,
                )
            self.assertNotIn("--chat-template", server.process.arguments())
            self.assertNotIn("--dry-multiplier", server.process.arguments())
            server.deleteLater()

    def test_managed_server_rejects_missing_model_or_non_loopback_endpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = root / "llama-server"
            model = root / "model.gguf"
            executable.write_bytes(b"test executable")
            model.write_bytes(b"test model")
            server = LlamaServerProcess()
            with patch.object(server.process, "start"):
                with self.assertRaisesRegex(ValueError, "local-network"):
                    server.start(
                        str(executable), str(model), "model",
                        "https://example.com:9931", 99,
                    )
                with self.assertRaisesRegex(ValueError, "existing .gguf"):
                    server.start(
                        str(executable), str(root / "missing.gguf"), "model",
                        "http://127.0.0.1:9931", 99,
                    )
            server.deleteLater()

    def test_app_managed_llama_server_starts_discovers_model_and_stops_with_session(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            models = root / "Models"
            models.mkdir()
            model = models / "NemoMix-Unleashed-12B-Q4_K_M.gguf"
            model.write_bytes(b"fixture only")
            executable = root / "llama-server"
            executable.write_text(
                f"""#!{sys.executable}
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

port = int(sys.argv[sys.argv.index("--port") + 1])
alias = sys.argv[sys.argv.index("--alias") + 1]

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = (
            {{"data": [{{"id": alias}}]}}
            if self.path == "/v1/models"
            else {{"default_generation_settings": {{"n_ctx": 4096}}}}
        )
        raw = json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)
    def log_message(self, *_args):
        pass

HTTPServer(("127.0.0.1", port), Handler).serve_forever()
""",
                encoding="utf-8",
            )
            executable.chmod(0o755)
            with socket.socket() as sock:
                sock.bind(("127.0.0.1", 0))
                port = sock.getsockname()[1]
            system = root / "System"
            system.mkdir()
            (system / "ai.json").write_text(json.dumps({
                "version": 5,
                "backend": "llama_cpp",
                "url": f"http://127.0.0.1:{port}",
                "roles": dict.fromkeys(ROLE_LABELS, ""),
                "role_urls": {},
                "context_limits": {},
            }), encoding="utf-8")
            with (
                patch.object(config, "SYSTEM_ROOT", system),
                patch.object(config, "MODELS_ROOT", models),
                patch.object(config, "LLAMA_SERVER_EXECUTABLE", executable),
            ):
                ai = AIService()
                self.objects.append(ai)
                self.assertEqual(ai.settings.llama_model_path, str(model))
                self.assertEqual(ai.settings.models["direct"], model.stem)
                ai.test_connection()
                deadline = time.monotonic() + 15
                while time.monotonic() < deadline and not ai.is_available("direct"):
                    self.app.processEvents()
                    time.sleep(.01)
                self.assertTrue(ai.is_available("direct"), ai.status)
                self.assertFalse(ai.llama_server.is_starting)
                self.assertTrue(ai.llama_server.is_running)
                self.assertIn(model.stem, ai.available_models)
                ai.stop()
                deadline = time.monotonic() + 3
                while time.monotonic() < deadline and ai.llama_server.is_running:
                    self.app.processEvents()
                    time.sleep(.01)
                self.assertFalse(ai.llama_server.is_running)

    def test_connection_errors_and_invalid_lists_are_explicit(self):
        server, url = self.server()
        client = self.client()
        results = []
        client.modelsListed.connect(lambda *args: results.append(args))
        cases = [
            (503, {"error": {"message": "Loading model"}}, "Loading model"),
            (401, {"error": {"message": "Invalid API key"}}, "Invalid API key"),
            (404, {"error": {"message": "Not found"}}, "Not found"),
            (200, b"not json", "invalid JSON"),
            (200, {"data": "bad"}, "invalid model list"),
            (200, {"data": [{"id": None}]}, "invalid model list"),
            (200, {"error": {"message": "Backend failed"}}, "Backend failed"),
        ]
        for status, data, detail in cases:
            with self.subTest(detail=detail):
                server.status, server.discovery = status, data
                results.clear()
                client.list_models(url)
                self.wait(lambda: bool(results))
                self.assertFalse(results[0][0])
                self.assertEqual(results[0][1], [])
                self.assertIn(detail, results[0][2])
        server.discovery, server.status = {"data": []}, 200
        results.clear()
        client.list_models(url)
        self.wait(lambda: bool(results))
        self.assertEqual(results[0][:2], (True, []))
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            unused = sock.getsockname()[1]
        results.clear()
        client.list_models(f"http://127.0.0.1:{unused}")
        self.wait(lambda: bool(results))
        self.assertFalse(results[0][0])

    def test_missing_model_empty_chat_and_chat_error(self):
        server, url = self.server()
        client = self.client()
        connection, results = [], []
        client.connectionFinished.connect(lambda *args: connection.append(args))
        client.responseFinished.connect(lambda *args: results.append(args))
        client.connect_to_server(url, "unloaded.gguf")
        self.wait(lambda: bool(connection))
        self.assertFalse(connection[0][0])
        self.assertEqual(client.last_failure, FailureCategory.MODEL_UNAVAILABLE)
        self.assertIn("missing or unloaded", connection[0][1])
        self.assertIn("Reconnect saved servers", connection[0][1])
        self.assertFalse(server.posts)
        connection.clear()
        client.connect_to_server(url, "chat")
        self.wait(lambda: bool(connection))
        for data in ({}, {"choices": []},
                     {"choices": [{"message": {"reasoning_content": "Thinking", "content": ""}}]}):
            server.chat = data
            results.clear()
            client.send_chat([])
            self.wait(lambda: bool(results))
            self.assertFalse(results[0][0])
            self.assertIn("no chat text", results[0][1])
        server.chat_status, server.chat = 500, {"error": {"message": "Context too large"}}
        results.clear()
        client.send_chat([])
        self.wait(lambda: bool(results))
        self.assertEqual(results, [(False, "llama-server: Context too large")])

    def test_role_routing_model_switching_and_single_generation_queue(self):
        primary, url = self.server()
        secondary, other = self.server(("chat", "memory"))
        ai = self.service(url, {"direct": "chat", "background": "small", "summary": "chat"},
                          {"summary": other})
        results = []
        ai.jobFinished.connect(lambda *args: results.append(args))
        primary.post_gate.clear()
        world = ai.submit("background", [])
        direct = ai.submit("direct", [{"role": "user", "content": "First"}])
        summary = ai.submit("summary", [])
        self.wait(primary.post_started.is_set)
        self.assertEqual(primary.posts[0][1]["model"], "chat")
        self.assertFalse(secondary.posts)
        self.assertEqual(ai.queue_count, 2)
        with self.assertRaises(RuntimeError):
            ai.apply(AISettings())
        primary.post_gate.set()
        self.wait(lambda: not ai.is_busy)
        self.assertEqual([item[0] for item in results], [direct, summary, world])
        self.assertEqual(secondary.posts[0][1]["model"], "chat")
        self.assertEqual(primary.posts[-1][1]["model"], "small")
        # Discovery changes the adapter's base URL: next chat must reconnect to
        # its role endpoint even when the model ID has not changed.
        ai.submit("direct", [])
        self.wait(lambda: not ai.is_busy)
        ai.test_connection()
        self.wait(lambda: not ai.is_busy)
        ai.submit("direct", [])
        self.wait(lambda: not ai.is_busy)
        self.assertEqual(len(secondary.posts), 1)
        ai.apply(AISettings("llama_cpp", url, dict.fromkeys(ROLE_LABELS, "small")))
        self.wait(lambda: not ai.is_busy)
        ai.submit("direct", [])
        self.wait(lambda: not ai.is_busy)
        self.assertEqual(primary.posts[-1][1]["model"], "small")

    def test_partial_endpoint_failure_and_models_are_scoped_to_role(self):
        primary, url = self.server(("chat",))
        secondary, other = self.server(("memory",))
        secondary.status, secondary.discovery = 503, {"error": {"message": "Loading model"}}
        ai = self.service(url, {"direct": "chat", "background": "memory", "summary": ""},
                          {"background": other})
        self.assertTrue(ai.is_available("direct"))
        self.assertFalse(ai.is_available("background"))
        self.assertIn(other, ai.status)
        secondary.status, secondary.discovery = 200, {"data": [{"id": "memory"}]}
        ai.test_connection()
        self.wait(lambda: not ai.is_busy)
        self.assertTrue(ai.is_available("background"))
        wrong = AISettings("llama_cpp", url, dict.fromkeys(ROLE_LABELS, "memory"))
        ai.apply(wrong)
        self.wait(lambda: not ai.is_busy)
        self.assertFalse(ai.is_available("direct"))
        self.assertIn("Unavailable assignments", ai.status)

    def test_active_and_queued_cancellation_leave_other_channel_working(self):
        server, url = self.server()
        ai = self.service(url)
        first, queued, last = AIChannel(ai), AIChannel(ai), AIChannel(ai)
        results = [[], [], []]
        for channel, result in zip((first, queued, last), results):
            channel.responseFinished.connect(lambda *args, result=result: result.append(args))
        server.post_gate.clear()
        first.send_chat([{"role": "user", "content": "Cancel running"}])
        queued.send_chat([{"role": "user", "content": "Cancel queued"}])
        last.send_chat([{"role": "user", "content": "Keep"}])
        self.wait(server.post_started.is_set)
        queued.cancel()
        first.cancel()
        self.wait(lambda: bool(results[0]))
        self.assertEqual(results[0], [(False, "Request cancelled.")])
        self.assertEqual(results[1], [(False, "Request cancelled.")])
        server.post_gate.set()
        self.wait(lambda: not ai.is_busy)
        self.assertEqual(results[2], [(True, "Fixture reply")])
        self.assertEqual(len(server.posts), 2)

    def test_cancel_connect_discovery_timeout_and_stop(self):
        server, url = self.server()
        ai = self.service(url)
        results = []
        ai.jobFinished.connect(lambda *args: results.append(args))
        server.get_gate.clear()
        server.get_started.clear()
        ai.submit("direct", [])
        self.wait(server.get_started.is_set)
        ai.cancel_all()
        self.wait(lambda: not ai.is_busy)
        self.assertEqual(results[0][1:], (False, "Request cancelled."))
        self.assertFalse(server.posts)
        server.get_started.clear()
        ai.test_connection()
        self.wait(server.get_started.is_set)
        ai.cancel_all()
        self.wait(lambda: not ai.is_busy)
        self.assertFalse(ai.connected)
        self.assertIn("cancelled", ai.status)
        client = self.client()
        client.request_timeout_ms = 50
        discovery = []
        client.modelsListed.connect(lambda *args: discovery.append(args))
        client.list_models(url)
        self.wait(lambda: bool(discovery))
        self.assertFalse(discovery[0][0])
        server.get_gate.set()
        ai.test_connection()
        self.wait(lambda: not ai.is_busy)
        server.post_gate.clear()
        ai.submit("direct", [])
        self.wait(server.post_started.is_set)
        ai.stop()
        self.wait(lambda: not ai.is_busy)
        with self.assertRaises(RuntimeError):
            ai.submit("direct", [])

    def test_llama_options_preserve_history_when_model_changes(self):
        llama, llama_url = self.server(handler=LlamaHandler)
        llama.discovery = {"data": [
            {"id": "test-model:3b"}, {"id": "other-model"},
        ]}
        desktop = DesktopPage(sample_account())
        self.objects.append(desktop)
        desktop.open_messenger()
        messenger = desktop._windows["messenger"].widget()
        options = desktop.options_window
        options.url_edit.setText(llama_url)
        for combo in options.model_combos.values():
            combo.setEditText("test-model:3b")
        options.apply_button.click()
        self.wait(lambda: not desktop.ai_service.is_busy)
        messenger.message_edit.setText("Keep my conversation")
        messenger.send_button.click()
        self.wait(lambda: not desktop.ai_service.is_busy)
        history = list(messenger.contact_histories[messenger.selected_contact.contact_id])
        options.model_combos["direct"].setEditText("other-model")
        options.apply_button.click()
        self.wait(lambda: not desktop.ai_service.is_busy)
        self.assertIsInstance(desktop.ai_service.backend, LlamaCppClient)
        self.assertEqual(messenger.contact_histories[messenger.selected_contact.contact_id], history)
        messenger.message_edit.setText("Keep using llama.cpp")
        messenger.send_button.click()
        self.wait(lambda: not desktop.ai_service.is_busy)
        self.assertEqual(llama.posts[-1][1]["model"], "other-model")
        self.assertIn("Fixture reply", messenger.transcript.toPlainText())
        saved = load_ai_settings()
        self.assertEqual(saved.backend, "llama_cpp")
        self.assertEqual(saved.url, llama_url)
        self.assertEqual(saved.models["direct"], "other-model")

    def test_version_one_settings_and_role_endpoints_roundtrip(self):
        root = Path(self.directory.name)
        original = {"version": 1, "backend": "ollama", "url": "http://localhost:11434",
                    "roles": dict.fromkeys(ROLE_LABELS, "imported")}
        (root / "ai.json").write_text(json.dumps(original))
        self.assertEqual(load_ai_settings().models, original["roles"])
        server, url = self.server()
        ai = self.service(url)
        ai.apply(AISettings("llama_cpp", url + "/v1", dict.fromkeys(ROLE_LABELS, "chat"),
                            {"background": url + "/v1", "summary": ""}))
        self.wait(lambda: not ai.is_busy)
        loaded = load_ai_settings()
        self.assertEqual(loaded.endpoint_for("background"), url)
        self.assertEqual(loaded.endpoint_for("summary"), url)
        self.assertEqual(loaded.models, ai.settings.models)
        with self.assertRaises(ValueError):
            AISettings(role_urls={"unknown": url}).validated()

    def test_options_role_server_edits_scope_dropdowns_and_test_saved_values(self):
        primary, url = self.server(("chat",))
        secondary, other = self.server(("memory",))
        ai = self.service(url)
        from win7_2011.win7sim.options import OptionsWindow
        options = OptionsWindow(ai)
        self.objects.append(options)
        options.role_url_edits["summary"].setText(other + "/v1")
        options.model_combos["summary"].setEditText("memory")
        options.apply_button.click()
        self.wait(lambda: not ai.is_busy)
        self.assertTrue(ai.is_available("summary"))
        direct = options.model_combos["direct"]
        summary = options.model_combos["summary"]
        self.assertEqual([direct.itemText(i) for i in range(direct.count())], ["", "chat"])
        self.assertEqual([summary.itemText(i) for i in range(summary.count())], ["", "memory"])
        self.assertEqual(load_ai_settings().role_urls["summary"], other)
        options.url_edit.setText("http://127.0.0.1:1")
        options.test_button.click()
        self.wait(lambda: not ai.is_busy)
        self.assertTrue(ai.is_available("direct"), "Test must use saved addresses, not unsaved edits")
        self.assertEqual(options.url_edit.text(), "http://127.0.0.1:1")
        options.url_edit.setText(url)
        primary.post_gate.clear()
        ai.submit("direct", [])
        self.wait(primary.post_started.is_set)
        self.assertFalse(options.role_url_edits["summary"].isEnabled())
        self.assertFalse(options.role_url_edits["summary"].isEnabled())
        options.cancel_button.click()
        self.wait(lambda: not ai.is_busy)
        self.assertTrue(options.role_url_edits["summary"].isEnabled())
