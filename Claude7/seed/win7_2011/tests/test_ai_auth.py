import ctypes
import json
import os
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLineEdit

from win7_2011.win7sim import ai_credentials, config
from win7_2011.win7sim.ai_credentials import WindowsCredentialStore, credential_target
from win7_2011.win7sim.ai_service import AIService, BACKENDS
from win7_2011.win7sim.ai_settings import AISettings, ROLE_LABELS, load_ai_settings, save_ai_settings
from win7_2011.win7sim.options import APIKeyDialog, OptionsWindow


class MemoryCredentials:
    """Test double only; never used by the application."""
    def __init__(self):
        self.values = {}

    def get(self, backend, endpoint):
        return self.values.get(credential_target(backend, endpoint))

    def set(self, backend, endpoint, value):
        self.values[credential_target(backend, endpoint)] = value

    def delete(self, backend, endpoint):
        self.values.pop(credential_target(backend, endpoint), None)


class ProtectedHandler(BaseHTTPRequestHandler):
    def respond(self, status, body):
        raw = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        if self.server.redirect:
            self.send_header("Location", self.server.redirect)
        self.end_headers()
        self.wfile.write(raw)

    def handle_request(self, chat=False):
        authorization = self.headers.get("Authorization")
        self.server.seen.append((self.path, authorization))
        if chat:
            self.rfile.read(int(self.headers["Content-Length"]))
        expected = f"Bearer {self.server.key}" if self.server.key else None
        if authorization != expected or self.server.failure:
            # Deliberately echo a synthetic key to verify it cannot reach UI.
            self.respond(self.server.failure or 401, {
                "error": {"message": f"Rejected {authorization}"}
            })
        elif self.server.redirect:
            self.respond(302, {})
        elif chat:
            content = self.server.reply_text
            self.respond(200, {
                "message": {"content": content},
                "choices": [{"message": {"content": content}}],
            })
        else:
            self.respond(200, {"models": [{"name": "chat"}], "data": [{"id": "chat"}]})

    def do_GET(self):
        self.handle_request()

    def do_POST(self):
        self.handle_request(True)

    def log_message(self, *_args):
        pass


class AuthenticationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.storage = patch.object(config, "SYSTEM_ROOT", self.root)
        self.storage.start()
        self.store = MemoryCredentials()
        self.servers, self.objects = [], []

    def tearDown(self):
        for obj in self.objects:
            if isinstance(obj, AIService):
                obj.stop()
            elif hasattr(obj, "cancel"):
                obj.cancel()
            elif hasattr(obj, "close"):
                obj.close()
            obj.deleteLater()
        self.app.processEvents()
        for server, thread in self.servers:
            server.shutdown()
            server.server_close()
            thread.join(2)
        self.storage.stop()
        self.directory.cleanup()

    def server(self, key="fixture-key"):
        server = ThreadingHTTPServer(("127.0.0.1", 0), ProtectedHandler)
        server.key, server.failure = key, 0
        server.redirect = ""
        server.reply_text = "Protected reply"
        server.seen = []
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

    def client(self, backend):
        client = BACKENDS[backend]()
        client.credential_resolver = lambda url: self.store.get(backend, url)
        self.objects.append(client)
        return client

    def service(self, backend, url, role_urls=None, store=None):
        ai = AIService(
            settings=AISettings(backend, url, dict.fromkeys(ROLE_LABELS, "chat"), role_urls or {}),
            credential_store=store if store is not None else self.store,
        )
        self.objects.append(ai)
        return ai

    def test_protected_discovery_connection_and_chat_for_llama_server(self):
        for backend in BACKENDS:
            with self.subTest(backend=backend):
                server, url = self.server()
                self.store.set(backend, url, server.key)
                client = self.client(backend)
                listed, connected, replies = [], [], []
                client.modelsListed.connect(lambda *args: listed.append(args))
                client.connectionFinished.connect(lambda *args: connected.append(args))
                client.responseFinished.connect(lambda *args: replies.append(args))
                client.list_models(url + "/v1/")
                self.wait(lambda: bool(listed))
                self.assertEqual(listed[0][:2], (True, ["chat"]))
                client.connect_to_server(url, "chat")
                self.wait(lambda: bool(connected))
                self.assertTrue(connected[0][0])
                client.send_chat([{"role": "user", "content": "Hello"}])
                self.wait(lambda: bool(replies))
                self.assertEqual(replies, [(True, "Protected reply")])
                self.assertEqual(len(server.seen), 4)  # discovery, optional metadata, connect, chat
                self.assertIn("/props", [path for path, _ in server.seen])
                self.assertTrue(all(header == "Bearer fixture-key" for _, header in server.seen))
                self.assertEqual(client._request_key, "")

    def test_real_auth_scenario_with_offline_fixtures(self):
        # Exercise every live-scenario assertion cheaply with the llama client.
        # This is not a Windows Credential Manager or real-model certification.
        from win7_2011.tests.test_ai_real_auth import RealAuthenticationTests
        for backend in BACKENDS:
            with self.subTest(backend=backend):
                primary, url = self.server("primary-fixture")
                healthy, other = self.server("healthy-fixture")
                self.store.set(backend, url, primary.key)
                self.store.set(backend, other, healthy.key)
                settings = AISettings(
                    backend, url, dict.fromkeys(ROLE_LABELS, "chat"),
                    {"background": other},
                ).validated()
                case = RealAuthenticationTests()
                try:
                    case.exercise(settings, self.store)
                finally:
                    self.assertTrue(case.doCleanups(), "Scenario cleanup failed.")
                self.assertEqual(self.store.get(backend, url), primary.key)
                self.assertEqual(self.store.get(backend, other), healthy.key)

    def test_real_auth_scenario_restores_key_after_partial_write_failure(self):
        from win7_2011.tests.test_ai_real_auth import RealAuthenticationTests
        primary, url = self.server("primary-fixture")
        healthy, other = self.server("healthy-fixture")
        self.store.set("llama_cpp", url, primary.key)
        self.store.set("llama_cpp", other, healthy.key)
        settings = AISettings("llama_cpp", url, dict.fromkeys(ROLE_LABELS, "chat"),
                              {"background": other}).validated()
        case = RealAuthenticationTests()
        native_set = self.store.set

        def partial_write(backend, endpoint, value):
            native_set(backend, endpoint, value)
            if value.startswith("win7-rejected-"):
                raise RuntimeError("Synthetic write failure")

        with patch.object(self.store, "set", side_effect=partial_write):
            try:
                with self.assertRaisesRegex(RuntimeError, "Synthetic write failure"):
                    case.exercise(settings, self.store)
            finally:
                self.assertTrue(case.doCleanups(), "Scenario cleanup failed.")
        self.assertEqual(self.store.get("llama_cpp", url), primary.key)
        self.assertEqual(self.store.get("llama_cpp", other), healthy.key)

    def test_missing_wrong_and_forbidden_keys_are_explicit_and_never_echoed(self):
        for backend in BACKENDS:
            for key, status in ((None, 401), ("wrong-fixture-key", 401), ("fixture-key", 403)):
                with self.subTest(backend=backend, key=key, status=status):
                    server, url = self.server()
                    if key:
                        self.store.set(backend, url, key)
                    if status == 403:
                        server.failure = status
                    client = self.client(backend)
                    results = []
                    client.modelsListed.connect(lambda *args: results.append(args))
                    client.list_models(url)
                    self.wait(lambda: bool(results))
                    self.assertEqual(results[0][:2], (False, []))
                    self.assertIn(f"Authentication failed (HTTP {status})", results[0][2])
                    self.assertIn("Options", results[0][2])
                    if key:
                        self.assertNotIn(key, results[0][2])

    def test_chat_auth_failure_is_explicit_and_disconnects_adapter(self):
        for backend in BACKENDS:
            with self.subTest(backend=backend):
                server, url = self.server()
                self.store.set(backend, url, server.key)
                client = self.client(backend)
                connected, replies = [], []
                client.connectionFinished.connect(lambda *args: connected.append(args))
                client.responseFinished.connect(lambda *args: replies.append(args))
                client.connect_to_server(url, "chat")
                self.wait(lambda: bool(connected))
                server.failure = 401
                client.send_chat([])
                self.wait(lambda: bool(replies))
                self.assertFalse(replies[0][0])
                self.assertIn("Authentication failed", replies[0][1])
                self.assertNotIn(server.key, replies[0][1])
                self.assertFalse(client.is_connected)

    def test_json_escaped_key_echoes_are_redacted(self):
        for backend in BACKENDS:
            with self.subTest(backend=backend):
                server, url = self.server('fixture"key\\escaped')
                self.store.set(backend, url, server.key)
                server.reply_text = f"Echo: {server.key}"
                client = self.client(backend)
                connected, replies = [], []
                client.connectionFinished.connect(lambda *args: connected.append(args))
                client.responseFinished.connect(lambda *args: replies.append(args))
                client.connect_to_server(url, "chat")
                self.wait(lambda: bool(connected))
                client.send_chat([])
                self.wait(lambda: bool(replies))
                self.assertEqual(replies, [(True, "Echo: [redacted]")])

    def test_redirect_does_not_forward_key_or_make_second_request(self):
        for backend in BACKENDS:
            with self.subTest(backend=backend):
                server, url = self.server()
                destination, other = self.server()
                server.redirect = other + "/collect"
                self.store.set(backend, url, server.key)
                client = self.client(backend)
                results = []
                client.modelsListed.connect(lambda *args: results.append(args))
                client.list_models(url)
                self.wait(lambda: bool(results))
                self.assertFalse(results[0][0])
                self.assertIn("redirects are not followed", results[0][2])
                self.assertFalse(destination.seen)

    def test_role_specific_keys_survive_service_restart(self):
        for backend in BACKENDS:
            with self.subTest(backend=backend):
                primary, url = self.server("direct-fixture")
                secondary, other = self.server("summary-fixture")
                self.store.set(backend, url, primary.key)
                self.store.set(backend, other, secondary.key)
                ai = self.service(backend, url, {"summary": other})
                save_ai_settings(ai.settings)
                self.assertNotIn(primary.key, (self.root / "ai.json").read_text())
                self.assertNotIn(secondary.key, (self.root / "ai.json").read_text())
                ai = AIService(settings=load_ai_settings(), credential_store=self.store)
                self.objects.append(ai)
                ai.test_connection()
                self.wait(lambda: not ai.is_busy)
                self.assertTrue(ai.is_available("summary"))
                results = []
                ai.jobFinished.connect(lambda *args: results.append(args))
                for role in ("direct", "summary", "background"):
                    ai.submit(role, [])
                self.wait(lambda: len(results) == 3)
                self.assertTrue(all(result[1] for result in results))
                self.assertTrue(all(header == "Bearer direct-fixture" for _, header in primary.seen))
                self.assertTrue(all(header == "Bearer summary-fixture" for _, header in secondary.seen))

    def test_key_replace_remove_busy_guard_and_dialog_never_reveals_saved_key(self):
        server, url = self.server()
        ai = self.service("llama_cpp", url)
        options = OptionsWindow(ai)
        self.objects.append(options)
        options.url_edit.setText(url)
        dialog = APIKeyDialog(ai, "llama_cpp", url)
        self.objects.append(dialog)
        self.assertEqual(dialog.key_edit.echoMode(), QLineEdit.EchoMode.Password)
        self.assertEqual(dialog.key_edit.text(), "")
        dialog.key_edit.setText(server.key)
        dialog.save_button.click()
        self.assertEqual(dialog.key_edit.text(), "")
        self.assertEqual(self.store.get("llama_cpp", url), server.key)
        ai.test_connection()
        self.assertTrue(all(not button.isEnabled() for button in options.key_buttons))
        with self.assertRaises(RuntimeError):
            ai.update_api_key("llama_cpp", url, "replacement")
        self.wait(lambda: not ai.is_busy)
        reopened = APIKeyDialog(ai, "llama_cpp", url)
        self.objects.append(reopened)
        self.assertEqual(reopened.key_edit.text(), "")
        reopened.key_edit.setText("replacement")
        reopened.reject()
        self.assertEqual(reopened.key_edit.text(), "")
        self.assertEqual(self.store.get("llama_cpp", url), server.key)
        ai.update_api_key("llama_cpp", url, "replacement")
        self.assertFalse(ai.is_available("direct"))
        server.key = "replacement"
        ai.test_connection()
        self.wait(lambda: not ai.is_busy)
        self.assertTrue(ai.is_available("direct"))
        reopened.remove_button.click()
        self.assertIsNone(self.store.get("llama_cpp", url))
        self.assertFalse(ai.is_available("direct"))
        server.key = None
        ai.test_connection()
        self.wait(lambda: not ai.is_busy)
        ai.submit("direct", [])
        self.wait(lambda: not ai.is_busy)
        self.assertEqual(server.seen[-1][1], None)

    def test_options_key_buttons_route_main_inherited_and_overridden_endpoints(self):
        ai = self.service("llama_cpp", "http://localhost:9931")
        options = OptionsWindow(ai)
        self.objects.append(options)
        options.role_url_edits["summary"].setText("http://localhost:9999/v1/")
        with patch("win7_2011.win7sim.options.APIKeyDialog") as dialog:
            options._edit_api_key()
            self.assertEqual(dialog.call_args.args[1:3], ("llama_cpp", "http://localhost:9931"))
            options._edit_api_key("direct")
            self.assertEqual(dialog.call_args.args[1:3], ("llama_cpp", "http://localhost:9931"))
            options._edit_api_key("summary")
            self.assertEqual(dialog.call_args.args[1:3], ("llama_cpp", "http://localhost:9999"))
            options._edit_api_key()
            self.assertEqual(dialog.call_args.args[1:3], ("llama_cpp", "http://localhost:9931"))

    def test_store_failure_does_not_send_request_or_leak_exception(self):
        server, url = self.server()
        with patch.object(self.store, "get", side_effect=RuntimeError("private-fixture-value")):
            ai = self.service("llama_cpp", url)
            ai.test_connection()
            self.assertFalse(ai.is_busy)
            self.assertFalse(ai.connected)
            self.assertNotIn("private-fixture-value", ai.status)
            self.assertIn("Credential Manager", ai.status)
            self.assertFalse(server.seen)
        dialog = APIKeyDialog(ai, "llama_cpp", url)
        self.objects.append(dialog)
        dialog.key_edit.setText("private-fixture-value")
        with patch.object(self.store, "set", side_effect=RuntimeError("private-fixture-value")):
            dialog.save_button.click()
        self.assertNotIn("private-fixture-value", dialog.status.text())
        self.assertEqual(dialog.result(), 0)
        self.assertFalse(self.store.values)
        self.assertFalse((self.root / "ai.json").exists())

    def test_unauthenticated_settings_versions_migrate_without_secrets(self):
        for version in (1, 2):
            for backend in BACKENDS:
                with self.subTest(version=version, backend=backend):
                    server, url = self.server(None)
                    raw = {"version": version, "backend": backend, "url": url,
                           "roles": dict.fromkeys(ROLE_LABELS, "chat")}
                    if version == 2:
                        raw.update(role_urls={"summary": url}, profiles={
                            backend: {"url": url, "roles": raw["roles"], "role_urls": {}}
                        })
                    (self.root / "ai.json").write_text(json.dumps(raw))
                    settings = load_ai_settings()
                    ai = AIService(settings=settings, credential_store=self.store)
                    self.objects.append(ai)
                    ai.test_connection()
                    self.wait(lambda: not ai.is_busy)
                    ai.submit("direct", [])
                    self.wait(lambda: not ai.is_busy)
                    save_ai_settings(ai.settings)
                    self.assertEqual(load_ai_settings().models, raw["roles"])
                    self.assertFalse(self.store.values)
                    self.assertTrue(all(header is None for _, header in server.seen))


class NativeCredentialTests(unittest.TestCase):
    def test_target_normalizes_llama_v1_and_rejects_invalid_endpoints_and_backends(self):
        self.assertEqual(credential_target("llama_cpp", "http://localhost:9931/v1/"),
                         credential_target("llama_cpp", "http://localhost:9931"))
        for url in ("https://example.com", "http://user:secret@localhost"):
            with self.assertRaises(ValueError):
                credential_target("llama_cpp", url)
        with self.assertRaises(ValueError):
            credential_target("ollama", "http://localhost:11434")

    def test_non_windows_has_no_plaintext_fallback(self):
        store = WindowsCredentialStore()
        with patch.object(ai_credentials.sys, "platform", "linux"):
            self.assertIsNone(store.get("llama_cpp", "http://localhost:9931"))
            with self.assertRaisesRegex(RuntimeError, "Credential Manager"):
                store.set("llama_cpp", "http://localhost:9931", "fixture-key")
            with self.assertRaisesRegex(RuntimeError, "Credential Manager"):
                store.delete("llama_cpp", "http://localhost:9931")

    def test_native_read_write_delete_free_and_error_handling(self):
        # Exercise ctypes ABI marshalling without depending on a Windows login.
        class FakeAPI:
            def __init__(self):
                self.blob = "fixture-key".encode("utf-16-le")
                self.buffer = (ctypes.c_ubyte * len(self.blob)).from_buffer_copy(self.blob)
                self.credential = ai_credentials._Credential()
                self.credential.CredentialBlobSize = len(self.blob)
                self.credential.CredentialBlob = self.buffer
                self.freed = 0
                self.ok = True

            def CredReadW(self, target, kind, flags, out):
                self.target = target
                ctypes.cast(out, ctypes.POINTER(ctypes.POINTER(ai_credentials._Credential)))[0] = (
                    ctypes.pointer(self.credential)
                )
                return self.ok

            def CredFree(self, pointer):
                self.freed += 1

            def CredWriteW(self, pointer, flags):
                value = ctypes.cast(pointer, ctypes.POINTER(ai_credentials._Credential)).contents
                self.written = ctypes.string_at(value.CredentialBlob, value.CredentialBlobSize)
                self.persist, self.kind = value.Persist, value.Type
                return self.ok

            def CredDeleteW(self, target, kind, flags):
                return self.ok

        api, store = FakeAPI(), WindowsCredentialStore()
        with patch.object(ai_credentials.sys, "platform", "win32"), patch.object(
            store, "_api", return_value=api
        ), patch.object(ctypes, "get_last_error", return_value=1168, create=True) as last_error:
            self.assertEqual(store.get("llama_cpp", "http://localhost:9931"), "fixture-key")
            self.assertEqual(api.freed, 1)
            store.set("llama_cpp", "http://localhost:9931", "replacement")
            self.assertEqual(api.written.decode("utf-16-le"), "replacement")
            self.assertEqual((api.persist, api.kind), (2, 1))
            store.delete("llama_cpp", "http://localhost:9931")
            api.ok = False
            self.assertIsNone(store.get("llama_cpp", "http://localhost:9931"))
            store.delete("llama_cpp", "http://localhost:9931")  # Missing key is idempotent.
            last_error.return_value = 5
            for call in (lambda: store.get("llama_cpp", "http://localhost:9931"),
                         lambda: store.set("llama_cpp", "http://localhost:9931", "fixture-key"),
                         lambda: store.delete("llama_cpp", "http://localhost:9931")):
                with self.assertRaisesRegex(RuntimeError, "Credential Manager"):
                    call()

    def test_header_injection_and_empty_keys_are_rejected_without_echo(self):
        for value in ("", "has spaces", "fixture\r\nInjected: yes", "non-ascii-ü"):
            with self.assertRaises(ValueError) as error:
                ai_credentials.validate_api_key(value)
            if value:
                self.assertNotIn(value, str(error.exception))
