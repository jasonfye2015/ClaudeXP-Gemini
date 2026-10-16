"""Real local HTTP stop/restart coverage for the explicit idle reconnect action."""
import json
import os
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from win7_2011.win7sim.ai_service import AIChannel, AIService
from win7_2011.win7sim.ai_settings import AISettings, ROLE_LABELS
from win7_2011.win7sim.options import OptionsWindow


class RestartHandler(BaseHTTPRequestHandler):
    def respond(self, data):
        body = json.dumps(data).encode()
        try:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_GET(self):
        if self.path == "/props":
            self.respond({})
            return
        self.server.gets.append(self.path)
        self.server.get_started.set()
        self.server.get_gate.wait(3)
        self.respond({"data": [{"id": self.server.model}]})

    def do_POST(self):
        data = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        self.server.posts.append(data)
        self.server.post_started.set()
        self.server.post_gate.wait(3)
        message = {"role": "assistant", "content": "Restart fixture reply"}
        self.respond({"choices": [{"message": message}]})

    def log_message(self, *_args):
        pass


class ReconnectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.servers = {}
        self.objects = []

    def tearDown(self):
        for obj in self.objects:
            if isinstance(obj, AIService):
                obj.stop()
            else:
                obj.close()
            obj.deleteLater()
        self.app.processEvents()
        for server in list(self.servers):
            self.stop_server(server)

    def server(self, backend, model="chat", port=0):
        server = ThreadingHTTPServer(("127.0.0.1", port), RestartHandler)
        server.model = model
        server.gets, server.posts = [], []
        server.get_started, server.post_started = threading.Event(), threading.Event()
        server.get_gate, server.post_gate = threading.Event(), threading.Event()
        server.get_gate.set()
        server.post_gate.set()
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        self.servers[server] = thread
        thread.start()
        return server, f"http://127.0.0.1:{server.server_port}"

    def stop_server(self, server):
        server.get_gate.set()
        server.post_gate.set()
        server.shutdown()
        server.server_close()
        self.servers.pop(server).join(2)

    def wait(self, condition):
        deadline = time.monotonic() + 3
        while not condition() and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(.005)
        self.assertTrue(condition(), "Local fixture request timed out")

    def service(self, backend, url, other=None):
        ai = AIService(settings=AISettings(
            backend=backend, url=url, models=dict.fromkeys(ROLE_LABELS, "chat"),
            role_urls={"background": other} if other else {},
        ))
        self.objects.append(ai)
        ai.test_connection()
        self.wait(lambda: not ai.is_busy)
        options = OptionsWindow(ai)
        self.objects.append(options)
        return ai, options

    def test_stop_restart_recovers_saved_endpoints_without_replaying_failed_message(self):
        for backend in ("llama_cpp",):
            with self.subTest(backend=backend):
                primary, url = self.server(backend)
                secondary, other = self.server(backend)
                ai, options = self.service(backend, url, other)
                channel = AIChannel(ai)
                results = []
                channel.responseFinished.connect(lambda *args: results.append(args))
                channel.send_chat([{"role": "user", "content": "Before restart"}])
                self.wait(lambda: not ai.is_busy)
                self.assertTrue(results[-1][0])
                port = primary.server_port
                self.stop_server(primary)
                channel.send_chat([{"role": "user", "content": "Failed message"}])
                self.wait(lambda: not ai.is_busy)
                self.assertFalse(results[-1][0])
                self.assertFalse(channel.is_busy)
                options.url_edit.setText("http://127.0.0.1:1")
                options.model_combos["direct"].setEditText("unsaved-model")
                # Explicit reconnect while the server is down reports only its
                # endpoints as unavailable; another local engine stays usable.
                options.reconnect_button.click()
                self.wait(lambda: not ai.is_busy)
                self.assertFalse(ai.is_available("direct"))
                self.assertFalse(ai.is_available("summary"))
                self.assertTrue(ai.is_available("background"))
                self.assertIn(url, ai.status)
                restarted, same_url = self.server(backend, port=port)
                self.assertEqual(same_url, url)
                ai.set_simulated_availability(False, True)
                options.reconnect_button.click()
                self.wait(lambda: not ai.is_busy)
                self.assertTrue(channel.is_connected)
                self.assertTrue(ai.is_available("background"))
                self.assertFalse(ai.chat_available)
                self.assertTrue(ai.background_paused)
                self.assertEqual(restarted.posts, [])
                self.assertEqual(len(results), 2)
                self.assertEqual(ai.queue_count, 0)
                self.assertEqual(ai.settings.url, url)
                self.assertEqual(ai.settings.models["direct"], "chat")
                self.assertEqual(options.url_edit.text(), "http://127.0.0.1:1")
                self.assertEqual(options.model_combos["direct"].currentText(), "unsaved-model")
                with self.assertRaises(RuntimeError):
                    channel.send_chat([])
                # Existing test/refresh remains functional after reconnect.
                before = len(restarted.gets)
                options.test_button.click()
                self.wait(lambda: not ai.is_busy)
                self.assertGreater(len(restarted.gets), before)
                self.assertTrue(channel.is_connected)
                ai.set_simulated_availability(True, False)
                channel.send_chat([{"role": "user", "content": "New message"}])
                self.wait(lambda: not ai.is_busy)
                self.assertEqual(results[-1], (True, "Restart fixture reply"))
                self.assertEqual(len(restarted.posts), 1)
                self.assertEqual(restarted.posts[0]["messages"][0]["content"], "New message")

    def test_reconnect_is_idle_only_and_never_replays_cancelled_work(self):
        for backend in ("llama_cpp",):
            with self.subTest(backend=backend):
                server, url = self.server(backend)
                ai, options = self.service(backend, url)
                results = []
                ai.jobFinished.connect(lambda *args: results.append(args))
                server.post_gate.clear()
                running = ai.submit("direct", [{"role": "user", "content": "Cancel running"}])
                queued = ai.submit("direct", [{"role": "user", "content": "Cancel queued"}])
                self.wait(server.post_started.is_set)
                gets = list(server.gets)
                self.assertFalse(options.reconnect_button.isEnabled())
                with self.assertRaises(RuntimeError):
                    ai.reconnect()
                options.reconnect_button.click()
                self.assertEqual(server.gets, gets, "No probes during active generation")
                options.cancel_button.click()
                self.wait(lambda: not ai.is_busy)
                self.assertEqual({row[0] for row in results}, {running, queued})
                self.assertTrue(all(row[1:] == (False, "Request cancelled.") for row in results))
                self.assertTrue(options.reconnect_button.isEnabled())
                port = server.server_port
                self.stop_server(server)
                restarted, _ = self.server(backend, port=port)
                restarted.get_gate.clear()
                options.reconnect_button.click()
                self.wait(restarted.get_started.is_set)
                self.assertFalse(options.reconnect_button.isEnabled())
                with self.assertRaises(RuntimeError):
                    ai.reconnect()
                options.cancel_button.click()
                self.wait(lambda: not ai.is_busy)
                self.assertFalse(ai.connected)
                restarted.get_gate.set()
                options.reconnect_button.click()
                self.wait(lambda: not ai.is_busy)
                self.assertTrue(ai.is_available("direct"))
                self.assertEqual(restarted.posts, [])
                self.assertEqual(len(results), 2)
                ai.stop()
                self.assertFalse(options.reconnect_button.isEnabled())
                with self.assertRaises(RuntimeError):
                    ai.reconnect()
