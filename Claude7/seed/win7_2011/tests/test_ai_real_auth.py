"""Separate opt-in Windows/native credential + authenticated server check.

No secret configuration is accepted from environment variables. See REAL_AI_TESTS.md.
"""
import os
import sys
import time
import unittest
import uuid
from urllib.parse import urlsplit

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from win7_2011.tests.real_ai_support import required
from win7_2011.win7sim.ai_credentials import WindowsCredentialStore
from win7_2011.win7sim.ai_service import AIChannel, AIService, BACKENDS
from win7_2011.win7sim.ai_settings import AISettings, ROLE_LABELS, normalize_endpoint
from win7_2011.win7sim.local_ai import FailureCategory


def configuration():
    """Validate all non-secret configuration before accessing credentials/network."""
    if required("WIN7_REAL_AUTH_TEST_OWNED") != "YES":
        raise ValueError("Explicit ownership of both test endpoints must be YES.")
    backend = required("WIN7_REAL_AUTH_BACKEND")
    if backend not in BACKENDS:
        raise ValueError("WIN7_REAL_AUTH_BACKEND must be llama_cpp.")
    def endpoint(name):
        value = required(name)
        parsed = urlsplit(value)
        if parsed.query or parsed.fragment:
            raise ValueError("Test endpoint URLs must not contain queries or fragments.")
        return normalize_endpoint(backend, value)
    primary = endpoint("WIN7_REAL_AUTH_URL")
    healthy = endpoint("WIN7_REAL_AUTH_HEALTHY_URL")
    if primary == healthy:
        raise ValueError("Use two distinct test endpoints for endpoint isolation.")
    models = dict.fromkeys(ROLE_LABELS, required("WIN7_REAL_AUTH_MODEL"))
    models["background"] = required("WIN7_REAL_AUTH_HEALTHY_MODEL")
    return AISettings(backend, primary, models, {"background": healthy}).validated()


def observing_client(client_class):
    class ObservingClient(client_class):
        def __init__(self, parent):
            super().__init__(parent)
            # Never record headers, credentials, URLs, responses, or server metadata.
            self.calls = []

        def _request(self, kind, method, url, payload=None):
            messages = (payload or {}).get("messages", [])
            self.calls.append((kind, [dict(row) for row in messages]))
            super()._request(kind, method, url, payload)

    return ObservingClient


class RealAuthenticationTests(unittest.TestCase):
    def wait(self, condition):
        deadline = time.monotonic() + 180
        while not condition() and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(.01)
        self.assertTrue(condition(), "Authenticated-server operation timed out.")

    def test_saved_key_change_and_explicit_reconnect(self):
        if os.environ.get("WIN7_REAL_AUTH") != "1":
            self.skipTest("Set WIN7_REAL_AUTH=1; see REAL_AI_TESTS.md")
        if sys.platform != "win32":
            self.fail("The enabled authenticated check requires Windows Credential Manager on Windows.")
        settings = configuration()
        self.exercise(settings, WindowsCredentialStore())

    def exercise(self, settings, store):
        """Also exercised by offline fixtures, never treated as a live Windows result."""
        backend, primary = settings.backend, settings.url
        healthy = settings.endpoint_for("background")
        original = store.get(backend, primary)
        healthy_key = store.get(backend, healthy)
        self.assertTrue(bool(original) and bool(healthy_key),
                        "Save keys for both test endpoints in Windows Credential Manager first.")
        # Register restoration before the first mutation, including partial-write failures.
        def restore():
            try:
                store.set(backend, primary, original)
            except Exception:
                raise AssertionError(
                    "Could not restore the primary test credential; replace it in Options."
                ) from None
        self.addCleanup(restore)
        self.app = QApplication.instance() or QApplication([])
        ai = AIService(settings=settings, credential_store=store,
                       backend_factory=observing_client(BACKENDS[backend]))
        def stop():
            ai.stop()
            ai.deleteLater()
            self.app.processEvents()
        self.addCleanup(stop)
        channel = AIChannel(ai)
        channel.setParent(ai)
        completions, responses, failures = [], [], []
        # Keep only IDs/booleans/categories, never server response text.
        ai.jobFinished.connect(lambda job, ok, _text: completions.append((job, ok)))
        ai.jobFinished.connect(lambda *_args: failures.append(ai.backend.last_failure))
        channel.responseFinished.connect(lambda ok, _text: responses.append(ok))

        def discover():
            ai.reconnect()
            self.wait(lambda: not ai.is_busy)

        def chats():
            return [row for row in ai.backend.calls if row[0] == "chat"]

        def send(role, text="Reply with only OK."):
            count = len(completions)
            job = ai.submit(role, [{"role": "user", "content": text}])
            self.wait(lambda: not ai.is_busy)
            self.assertEqual(completions[count:], [(job, True)],
                             "A fresh message must generate successfully.")

        # Warm both real endpoints, then leave the primary connection cached.
        discover()
        self.assertTrue(ai.is_available("direct"), "Primary discovery failed.")
        self.assertTrue(ai.is_available("background"), "Healthy discovery failed.")
        send("background")
        send("direct")
        # Writing through the real native store (not update_api_key) models an
        # invalid/revoked cached credential without proactively clearing discovery.
        invalid = "win7-rejected-" + uuid.uuid4().hex
        store.set(backend, primary, invalid)
        before = len(chats())
        count = len(completions)
        rejected = [{"role": "user", "content": "Do not replay this rejected message."}]
        channel.send_chat(rejected)
        queued = ai.submit("summary", [{"role": "user", "content": "Do not replay queued work."}])
        # Healthy work was already queued when primary authentication failed.
        healthy_job = ai.submit("background", [{"role": "user", "content": "Reply with only OK."}])
        self.wait(lambda: not ai.is_busy)
        outcomes = completions[count:]
        self.assertEqual(len(outcomes), 3)
        self.assertFalse(outcomes[0][1], "The invalid key must reject generation.")
        self.assertIn((queued, False), outcomes)
        self.assertIn((healthy_job, True), outcomes)
        self.assertEqual(failures[count], FailureCategory.AUTHENTICATION,
                         "The real endpoint must reject the key with HTTP 401 or 403.")
        self.assertEqual(responses, [False])
        self.assertFalse(channel.is_busy)
        self.assertEqual(len(chats()), before + 2,
                         "Only rejected primary and healthy queued chat may reach transport.")
        self.assertTrue(set(ai._endpoint_errors) == {primary},
                        "Only the affected endpoint may be invalidated.")
        self.assertFalse(ai._model_errors, "An auth failure is not a missing model.")
        self.assertNotIn(primary, ai.models_by_url)
        self.assertIn(healthy, ai.models_by_url)
        self.assertTrue(ai.connected)
        self.assertFalse(ai.is_available("direct"))
        self.assertFalse(ai.is_available("summary"))
        self.assertTrue(ai.is_available("background"))
        with self.assertRaises(RuntimeError):
            channel.send_chat(rejected)
        send("background")

        # Prove discovery is protected too, not just the chat route.
        completed_count = len(completions)
        before_discovery = len(chats())
        discover()
        self.assertFalse(ai.is_available("direct"),
                         "Model discovery must reject the saved invalid key.")
        self.assertTrue(ai.is_available("background"))
        self.assertTrue(any("Authentication failed" in text for text in ai._discovery_errors),
                        "Discovery must report an authentication failure.")
        self.assertEqual(responses, [False], "Discovery must never replay a rejected message.")
        self.assertEqual(len(chats()), before_discovery, "Discovery must not transmit chat.")
        self.assertEqual(len(completions), completed_count, "Discovery must not complete old jobs.")

        ai.update_api_key(backend, primary, original)
        self.assertTrue(store.get(backend, primary) == original, "Replacement key was not saved.")
        self.assertTrue(store.get(backend, healthy) == healthy_key, "Healthy credential changed.")
        self.assertFalse(ai.is_available("direct"), "Saving alone must not restore availability.")
        self.assertTrue(ai.is_available("background"))
        before = len(chats())
        request_count = len(ai.backend.calls)
        self.assertTrue(ai.can_reconnect)
        discover()
        self.assertTrue(channel.is_connected, "Explicit reconnect did not restore availability.")
        self.assertTrue(ai.is_available("summary"))
        self.assertTrue(ai.is_available("background"))
        self.assertFalse(ai._endpoint_errors)
        self.assertEqual(ai.queue_count, 0)
        self.assertEqual(len(chats()), before, "Reconnect must not replay chat.")
        self.assertEqual(responses, [False], "Reconnect must not emit a replacement reply.")
        self.assertEqual(len(completions), completed_count, "Reconnect must not complete old jobs.")
        self.assertTrue(all(row[0] in ("models", "context")
                            for row in ai.backend.calls[request_count:]),
                        "Reconnect may only perform discovery.")
        fresh = "This is a new message. Reply with only OK."
        send("direct", fresh)
        self.assertEqual(len(chats()), before + 1)
        self.assertEqual(chats()[-1][1], [{"role": "user", "content": fresh}])
        self.assertEqual(responses, [False], "A service send must not replay the failed channel job.")
        self.assertEqual(sum(row[1] == rejected for row in chats()), 1,
                         "The rejected message must be sent exactly once across the whole scenario.")
        self.assertFalse(any(
            message.get("content") == "Do not replay queued work."
            for _kind, messages in chats() for message in messages
        ), "Rejected queued work must never be transmitted.")
