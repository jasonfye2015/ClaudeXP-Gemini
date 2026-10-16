"""Per-model sizing over real Qt HTTP transport, without a tokenizer or model."""
import json
import unittest
from pathlib import Path
from win7_2011.tests.test_ai_failures import FailureHandler
from win7_2011.tests import test_messenger_context as contexts
from win7_2011.tests import test_ai_real_servers as live_tests
from win7_2011.tests.real_ai_support import RealHTTP
from win7_2011.win7sim import config
from win7_2011.win7sim.ai_settings import AISettings, ROLE_LABELS, load_ai_settings, save_ai_settings
from win7_2011.win7sim.messenger_context import (
    bounded_messages, input_size, model_input_budget, reply_reserve, valid_context_window,
)


class TokenizingHandler(FailureHandler):
    """A local server that formats whole conversations before tokenizing."""

    def do_POST(self):
        if self.path not in ("/apply-template", "/tokenize"):
            return super().do_POST()
        payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        self.server.measurements.append((self.path, payload))
        mode = self.server.token_mode
        if mode == "unsupported":
            self.respond(404, {})
        elif self.path == "/apply-template":
            if mode == "bad-template":
                self.respond(200, {"prompt": 123})
            else:
                # Template includes system, framing and a generation prefix.
                prompt = "<start>" + "".join(
                    f"<{item['role']}>{item['content']}</{item['role']}>"
                    for item in payload["messages"]
                ) + "<assistant>"
                self.respond(200, {"prompt": prompt})
        elif mode == "bad-tokens":
            self.respond(200, {"tokens": [1, True, 3]})
        else:
            # Fake tokenizer groups Unicode foxes into one token and treats
            # template delimiters as normal tokens, unlike UTF-8 bytes.
            prompt = payload["content"]
            count = len(prompt.replace("🦊", "x"))
            self.respond(200, {"tokens": list(range(count))})


class ModelSizingTests(unittest.TestCase):
    def test_estimate_reserves_reply_and_counts_persona_framing_unicode(self):
        history = [{"role": "user", "content": "🦊" * 100}]
        self.assertEqual(input_size(history), 464)
        for window in (256, 2048, 32768):
            with self.subTest(window=window):
                allowance = model_input_budget(window, 131072)
                self.assertEqual(allowance + reply_reserve(window), window)
                if window >= 2048:
                    messages, _ = bounded_messages("Persona " * 20, history, allowance)
                    self.assertLessEqual(input_size(messages) + reply_reserve(window), window)
        self.assertEqual(model_input_budget(None, 8192), 8192)

    def test_invalid_metadata_is_not_a_window(self):
        for value in (None, True, False, "4096", 4096.0, 0, -1, 255, 16_777_217):
            self.assertIsNone(valid_context_window(value))


class ModelContextIntegrationTests(unittest.TestCase):
    # Reuse fixture helpers, not another test class's actual test cases.
    setUpClass = contexts.MessengerContextTests.__dict__["setUpClass"]
    setUp = contexts.MessengerContextTests.setUp
    tearDown = contexts.MessengerContextTests.tearDown
    wait = contexts.MessengerContextTests.wait
    server = contexts.MessengerContextTests.server
    service = contexts.MessengerContextTests.service
    messenger = contexts.MessengerContextTests.messenger
    send = contexts.MessengerContextTests.send

    def test_windows_live_limit_harness_over_offline_transport(self):
        """Validate the runner itself; this is not a live/native certification."""
        small_server, small_url = self.server()
        large_server, large_url = self.server()
        small_server.models, large_server.models = ["chat"], ["large"]
        small_server.context_props = (200, {"default_generation_settings": {"n_ctx": 4096}})
        large_server.context_props = (200, {"default_generation_settings": {"n_ctx": 8192}})
        for server in (small_server, large_server):
            server.body = {
                "message": {"content": "Reply"}, "eval_count": 4,
                "choices": [{"message": {"content": "Reply"}}],
                "usage": {"completion_tokens": 4},
            }
        live_tests.RealModelLimitTests().exercise_limits(
            "llama_cpp", RealHTTP("llama_cpp", small_url), "chat",
            RealHTTP("llama_cpp", large_url), "large",
        )

    def test_llama_exact_unicode_and_template_overhead_preserve_full_history(self):
        server, url = self.server(TokenizingHandler)
        server.token_mode, server.measurements = "exact", []
        server.context_props = (200, {"default_generation_settings": {"n_ctx": 4096}})
        ai = self.service("llama_cpp", url)
        history = [
            {"role": role, "content": f"Turn {i} " + "🦊" * 80}
            for i in range(12) for role in ("user", "assistant")
        ]
        messenger = self.messenger(ai, history)
        self.assertEqual(messenger.context_budget.value(), 3584)
        self.send(messenger, "new 🦊🦊")
        self.assertTrue(server.posts, (messenger.provider_status.text(), server.measurements))
        selected = server.posts[-1]["messages"]
        self.assertEqual(len(server.posts), 1)
        self.assertGreater(len(server.measurements), 2)
        self.assertEqual(server.measurements[0][0], "/apply-template")
        self.assertEqual(server.measurements[0][1]["messages"][0], selected[0])
        self.assertEqual(server.measurements[0][1]["max_tokens"], 512)
        token_calls = [body for path, body in server.measurements if path == "/tokenize"]
        self.assertTrue(all(body["add_special"] and body["parse_special"] for body in token_calls))
        self.assertIn("<assistant>", token_calls[-1]["content"])
        count = len(token_calls[-1]["content"].replace("🦊", "x"))
        self.assertLessEqual(count + 512, 4096)
        self.assertGreater(input_size(selected), 3584, "Exact input fits more than byte estimate")
        self.assertIn(f"Exact server-formatted input: {count} tokens", messenger.context_status.text())
        self.assertEqual(
            config.load_messenger_history(messenger.selected_contact.contact_id, "rook")[:len(history)],
            history,
        )

    def test_invalid_or_unsupported_tokenization_uses_byte_fallback_without_retry(self):
        for mode in ("unsupported", "bad-template", "bad-tokens"):
            with self.subTest(mode=mode):
                server, url = self.server(TokenizingHandler)
                server.token_mode, server.measurements = mode, []
                server.context_props = (200, {"default_generation_settings": {"n_ctx": 4096}})
                ai = self.service("llama_cpp", url)
                messenger = self.messenger(ai, [
                    {"role": "user", "content": "🦊" * 300},
                    {"role": "assistant", "content": "old response"},
                ])
                self.send(messenger, "manual send")
                self.assertEqual(len(server.posts), 1, messenger.provider_status.text())
                self.assertLessEqual(input_size(server.posts[0]["messages"]), 3584)
                self.assertIn("exact tokenization unavailable", messenger.context_status.text())
                self.assertEqual(server.posts[0]["messages"][-1]["content"], "manual send")

    def test_exact_rejects_oversized_newest_before_sending_or_saving(self):
        server, url = self.server(TokenizingHandler)
        server.token_mode, server.measurements = "exact", []
        server.context_props = (200, {"default_generation_settings": {"n_ctx": 256}})
        ai = self.service("llama_cpp", url)
        messenger = self.messenger(ai, [])
        draft = "🦊" * 250
        self.send(messenger, draft)
        self.assertEqual(server.posts, [])
        self.assertEqual(messenger.message_edit.text(), draft)
        self.assertEqual(config.load_messenger_history(messenger.selected_contact.contact_id, "rook"), [])
        self.assertIn("Message not sent", messenger.provider_status.text())

    def test_exact_preflight_does_not_retry_rejected_generation(self):
        server, url = self.server(TokenizingHandler)
        server.token_mode, server.measurements = "exact", []
        server.context_props = (200, {"default_generation_settings": {"n_ctx": 4096}})
        ai = self.service("llama_cpp", url)
        messenger = self.messenger(ai, [])
        server.status = 400
        server.body = {"error": {"code": "context_length_exceeded", "message": "Too long"}}
        self.send(messenger, "Save this even on server rejection")
        self.assertEqual(len(server.posts), 1)
        self.assertTrue(server.measurements)
        self.assertIn("not automatically retried", messenger.context_status.text())
        self.assertEqual(
            config.load_messenger_history(messenger.selected_contact.contact_id, "rook")[-1],
            {"role": "user", "content": "Save this even on server rejection"},
        )

    def test_models_with_different_windows_bound_input_and_reply_on_switch(self):
        server, url = self.server()
        server.models = ["chat"]
        server.context_props = (200, {"default_generation_settings": {"n_ctx": 4096}})
        ai = self.service("llama_cpp", url)
        history = [
            {"role": role, "content": "Old turn " + "🦊" * 150}
            for _ in range(25) for role in ("user", "assistant")
        ]
        messenger = self.messenger(ai, history)
        self.assertEqual(messenger.context_budget.value(), 3584)
        self.send(messenger, "First explicit send")
        small = server.posts[-1]
        self.assertLessEqual(input_size(small["messages"]) + 512, 4096)
        self.assertEqual(small["messages"][0]["role"], "system")
        self.assertIn("512 tokens reserved", messenger.context_status.text())
        self.assertEqual(small["max_tokens"], 512)
        server.context_props = (200, {"default_generation_settings": {"n_ctx": 16384}})
        server.models = ["large"]
        roles = dict.fromkeys(ROLE_LABELS, "large")
        ai.apply(AISettings("llama_cpp", url, roles))
        self.wait(lambda: not ai.is_busy)
        self.assertEqual(len(server.posts), 1, "Changing models never sends messages")
        self.assertEqual(messenger.context_budget.value(), 15872)
        self.send(messenger, "Second explicit send")
        large = server.posts[-1]
        self.assertGreater(len(large["messages"]), len(small["messages"]))
        self.assertLessEqual(input_size(large["messages"]) + 512, 16384)
        saved = config.load_messenger_history(messenger.selected_contact.contact_id, "rook")
        self.assertEqual(saved[:len(history)], history)
        self.assertEqual(len(server.posts), 2)

    def test_llama_uses_runtime_not_training_window_or_router_global_props(self):
        server, url = self.server()
        ai = self.service("llama_cpp", url)
        for value in (None, True, "4096", -1, 4096.5, 16_777_217, 8192):
            server.context_props = (200, {
                "default_generation_settings": {"n_ctx": value},
                "n_ctx_train": 131072,
            })
            ai.test_connection()
            self.wait(lambda: not ai.is_busy)
            self.assertEqual(ai.context_for_role()[0], 8192 if value == 8192 else None)
            self.assertTrue(ai.is_available("direct"))
        server.models = ["chat", "other"]
        ai.test_connection()
        self.wait(lambda: not ai.is_busy)
        self.assertIsNone(ai.context_for_role()[0])

    def test_manual_limit_persists_scoped_to_model_endpoint_and_backend(self):
        server, url = self.server()
        other_server, other_url = self.server()
        ai = self.service("llama_cpp", url)
        messenger = self.messenger(ai, [])
        messenger.model_context_limit.setValue(4096)
        messenger.model_context_limit.editingFinished.emit()
        self.assertEqual(load_ai_settings().context_limits[url]["chat"], 4096)
        self.assertEqual(messenger.context_budget.value(), 3584)
        self.assertIn("manual limit", messenger.context_status.text())
        self.assertFalse(server.posts)
        ai.apply(AISettings("llama_cpp", url, dict.fromkeys(ROLE_LABELS, "chat")))
        self.wait(lambda: not ai.is_busy)
        self.assertEqual(ai.context_for_role()[0], 4096, "Options Apply retains saved limits")
        ai.apply(AISettings("llama_cpp", other_url, dict.fromkeys(ROLE_LABELS, "chat")))
        self.wait(lambda: not ai.is_busy)
        self.assertIsNone(ai.context_for_role()[0])
        ai.set_context_limit(8192)
        ai.apply(AISettings("llama_cpp", url, dict.fromkeys(ROLE_LABELS, "chat")))
        self.wait(lambda: not ai.is_busy)
        self.assertEqual(ai.context_for_role()[0], 4096)
        self.assertEqual(ai.settings.context_limits[other_url]["chat"], 8192)
        server.models.append("other")
        ai.settings.models["direct"] = "other"
        ai.changed.emit()
        self.assertIsNone(ai.context_for_role()[0])
        self.assertEqual(messenger.model_context_limit.value(), 0)
        ai.settings.models["direct"] = "chat"
        ai.changed.emit()
        messenger.model_context_limit.setValue(0)
        messenger.model_context_limit.editingFinished.emit()
        self.assertIsNone(ai.context_for_role()[0])
        self.assertNotIn("chat", load_ai_settings().context_limits[url])

    def test_manual_limit_cannot_exceed_metadata_or_drop_oversized_draft(self):
        server, url = self.server()
        server.context_props = (200, {"default_generation_settings": {"n_ctx": 4096}})
        ai = self.service("llama_cpp", url)
        ai.set_context_limit(8192)
        self.assertEqual(ai.context_for_role()[0], 4096)
        self.assertIn("capped by provider", ai.context_for_role()[1])
        history = [{"role": "user", "content": "Keep this"}]
        messenger = self.messenger(ai, history)
        draft = "🦊" * 1000
        self.send(messenger, draft)
        self.assertEqual(messenger.message_edit.text(), draft)
        self.assertFalse(server.posts)
        self.assertEqual(config.load_messenger_history(messenger.selected_contact.contact_id, "rook"), history)
        messenger.model_context_limit.setValue(1)
        messenger.model_context_limit.editingFinished.emit()
        self.assertIn("not saved", messenger.provider_status.text())
        self.assertEqual(load_ai_settings().context_limits[url]["chat"], 8192)
        self.assertEqual(messenger.model_context_limit.value(), 8192)

    def test_old_settings_load_and_invalid_manual_limits_are_rejected(self):
        root = Path(self.directory.name)
        for version in (1, 2):
            (root / "ai.json").write_text(json.dumps({
                "version": version, "backend": "ollama", "url": "http://localhost:11434",
                "roles": dict.fromkeys(ROLE_LABELS, "chat"),
            }))
            self.assertEqual(load_ai_settings().context_limits, {})
        for value in (True, "4096", -1, 255, 4096.5):
            with self.assertRaises(ValueError):
                save_ai_settings(AISettings(context_limits={"http://localhost:11434": {"chat": value}}))


if __name__ == "__main__":
    unittest.main()
