"""Bounded-history policy and Messenger integration against local HTTP fixtures."""
import unittest
from pathlib import Path
from unittest.mock import patch

from win7_2011.tests import test_ai_failures as failures
from win7_2011.tests.test_messaging import sample_account
from win7_2011.win7sim import config
from win7_2011.win7sim.apps import MessengerApp
from win7_2011.win7sim.contacts import CONTACTS
from win7_2011.win7sim.messenger_context import bounded_messages, input_size
from win7_2011.win7sim.local_ai import FailureCategory
from win7_2011.win7sim.service import ConnectionSimulator


class ContextPolicyTests(unittest.TestCase):
    def test_unicode_whole_messages_and_prompt_are_bounded_without_mutation(self):
        history = [
            {"role": "user", "content": "Old " + "🦊" * 400},
            {"role": "assistant", "content": "Old reply"},
            {"role": "user", "content": "Newest " + "🦊" * 100},
        ]
        original = [dict(message) for message in history]
        messages, omitted = bounded_messages("Persona", history, 600)
        self.assertEqual(omitted, 2)
        self.assertEqual(messages[0], {"role": "system", "content": "Persona"})
        self.assertEqual(messages[-1], history[-1])
        self.assertLessEqual(input_size(messages), 600)
        self.assertEqual(history, original)
        messages[-1]["content"] = "Changed request copy"
        self.assertEqual(history, original)

    def test_prompt_or_newest_message_is_never_silently_shortened(self):
        with self.assertRaisesRegex(ValueError, "instructions exceed"):
            bounded_messages("x" * 600, [], 512)
        with self.assertRaisesRegex(ValueError, "newest message"):
            bounded_messages("Persona", [{"role": "user", "content": "x" * 600}], 512)


# Reuse HTTP fixture helpers, not the unrelated inherited test cases.
class MessengerContextTests(unittest.TestCase):
    setUpClass = classmethod(failures.FailureTests.setUpClass.__func__)
    setUp = failures.FailureTests.setUp
    tearDown = failures.FailureTests.tearDown
    wait = failures.FailureTests.wait
    server = failures.FailureTests.server
    service = failures.FailureTests.service

    def messenger(self, ai, history):
        root = Path(self.directory.name) / "Messenger"
        storage = patch.object(config, "MESSENGER_HISTORY", root)
        storage.start()
        self.addCleanup(storage.stop)
        config.save_messenger_history(CONTACTS[0].contact_id, history, "rook")
        internet = ConnectionSimulator()
        self.objects.append(internet)
        messenger = MessengerApp(sample_account(), internet, ai_service=ai)
        self.objects.append(messenger)
        return messenger

    def send(self, messenger, text):
        messenger.message_edit.setText(text)
        messenger.send_button.click()
        self.wait(lambda: not messenger.client.is_busy and not messenger.ai.is_busy)

    def test_repeated_long_sends_work_without_summary_model_and_preserve_export(self):
        for backend in ("llama_cpp",):
            with self.subTest(backend=backend):
                server, url = self.server()
                ai = self.service(backend, url)
                ai.settings.models["summary"] = "not-installed"
                original = [
                    {"role": role, "content": f"Older {index} " + "🦊" * 500}
                    for index in range(40)
                    for role in ("user", "assistant")
                ]
                messenger = self.messenger(ai, original)
                contact_id = messenger.selected_contact.contact_id
                self.assertFalse(ai.is_available("summary"))
                self.assertTrue(messenger.send_button.isEnabled())
                for index in range(5):
                    newest = f"New send {index}"
                    self.send(messenger, newest)
                    payload = server.posts[-1]["messages"]
                    self.assertEqual(payload[0]["role"], "system")
                    self.assertEqual(payload[1]["role"], "user")
                    self.assertEqual(payload[-1], {"role": "user", "content": newest})
                    self.assertLessEqual(input_size(payload), messenger.context_budget.value())
                    self.assertLess(len(payload), len(original))
                    self.assertIn("older messages omitted", messenger.context_status.text())
                self.assertEqual(len(server.posts), 5, "No summary jobs or automatic retries")
                full = messenger.contact_histories[contact_id]
                self.assertEqual(full[:len(original)], original)
                self.assertEqual(len(full), len(original) + 10)
                self.assertEqual(config.load_messenger_history(contact_id, "rook"), full)
                export = Path(self.directory.name) / f"export-{backend}.json"
                config.export_messenger_histories(export, contact_id, "rook")
                self.assertIn("Older 0", export.read_text(encoding="utf-8"))
                reopened = MessengerApp(sample_account(), messenger.service, ai_service=ai)
                self.objects.append(reopened)
                self.assertEqual(reopened.contact_histories[contact_id], full)
                self.assertIn("Older 0", reopened.transcript.toPlainText())

    def test_context_rejection_is_visible_no_retry_and_manual_recovery_is_bounded(self):
        for backend in ("llama_cpp",):
            with self.subTest(backend=backend):
                server, url = self.server()
                ai = self.service(backend, url)
                history = [
                    {"role": role, "content": f"Turn {index} " + "x" * 500}
                    for index in range(30)
                    for role in ("user", "assistant")
                ]
                messenger = self.messenger(ai, history)
                server.status = 400
                server.body = {"error": {"code": "context_length_exceeded", "message": "Too long"}}
                self.send(messenger, "Failed send is still saved")
                self.assertEqual(ai.backend.last_failure, FailureCategory.CONTEXT_LIMIT)
                self.assertTrue(ai.is_available("direct"))
                self.assertTrue(messenger.send_button.isEnabled())
                self.assertEqual(len(server.posts), 1)
                self.assertIn("Reduce the AI input budget", messenger.context_status.text())
                self.assertIn("not automatically retried", messenger.context_status.text())
                failed_history = config.load_messenger_history(messenger.selected_contact.contact_id, "rook")
                self.assertEqual(failed_history, history + [
                    {"role": "user", "content": "Failed send is still saved"},
                ])
                first_size = input_size(server.posts[0]["messages"])
                messenger.context_budget.setValue(4096)
                self.app.processEvents()
                self.assertEqual(len(server.posts), 1)
                self.assertIn("model rejected", messenger.context_status.text())
                server.status = 200
                server.body = {"message": {"content": "Reply"},
                               "choices": [{"message": {"content": "Reply"}}]}
                self.send(messenger, "Explicit next send")
                self.assertEqual(len(server.posts), 2)
                self.assertLess(input_size(server.posts[-1]["messages"]), first_size)
                self.assertNotIn("model rejected", messenger.context_status.text())
                self.assertEqual(
                    config.load_messenger_history(messenger.selected_contact.contact_id, "rook"),
                    failed_history + [
                        {"role": "user", "content": "Explicit next send"},
                        {"role": "assistant", "content": "Reply"},
                    ],
                )

    def test_oversized_draft_stays_in_composer_and_never_reaches_server(self):
        server, url = self.server()
        ai = self.service("llama_cpp", url)
        history = [{"role": "user", "content": "Keep saved message"}]
        messenger = self.messenger(ai, history)
        draft = "🦊" * 4000
        self.send(messenger, draft)
        self.assertEqual(server.posts, [])
        self.assertEqual(messenger.message_edit.text(), draft)
        self.assertEqual(config.load_messenger_history(messenger.selected_contact.contact_id, "rook"), history)
        self.assertIn("Message not sent", messenger.provider_status.text())
        self.assertIn("newest message", messenger.provider_status.text())


if __name__ == "__main__":
    unittest.main()
