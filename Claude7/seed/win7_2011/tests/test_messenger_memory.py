"""Optional, reviewed conversation context over local HTTP and native Qt controls."""
import unittest
from unittest.mock import patch

from win7_2011.tests import test_messenger_context as context_tests
from win7_2011.tests.test_messaging import sample_account
from win7_2011.win7sim import config
from win7_2011.win7sim.apps import MessengerApp
from win7_2011.win7sim.contacts import CONTACTS, messenger_system_prompt
from win7_2011.win7sim.messenger_context import (
    additional_context, bounded_messages, input_size, summary_messages,
)
from PySide6.QtWidgets import QMessageBox
from win7_2011.win7sim.messenger_memory import (
    ConversationContextDialog, load_context,
)


class AdditionalContextPolicyTests(unittest.TestCase):
    def test_exact_addition_is_reserved_before_recent_history(self):
        extra = additional_context("Favorite snack: 🦊", "You promised a visit.")
        history = [{"role": "user", "content": "old" * 300},
                   {"role": "assistant", "content": "old reply"},
                   {"role": "user", "content": "new"}]
        messages, omitted = bounded_messages("Persona", history, 450, extra)
        self.assertEqual(messages[0]["content"], "Persona\n\n" + extra)
        self.assertEqual(omitted, 2)
        self.assertLessEqual(input_size(messages), 450)
        self.assertEqual(history[-1]["content"], "new")
        with self.assertRaisesRegex(ValueError, "pinned details"):
            bounded_messages("Persona", history, 100, extra)

    def test_summary_only_uses_bounded_omitted_source_without_mutation(self):
        history = [{"role": role, "content": f"turn {n} " + "x" * 80}
                   for n in range(10) for role in ("user", "assistant")]
        before = [dict(m) for m in history]
        messages, start, end = summary_messages(history, 16, 1100)
        self.assertGreater(start, 0)
        self.assertEqual(end, 16)
        self.assertEqual(messages[1:], history[start:end])
        self.assertLessEqual(input_size(messages), 1100)
        self.assertEqual(history, before)
        with self.assertRaisesRegex(ValueError, "Nothing to summarize"):
            summary_messages(history, 0, 1100)
        with self.assertRaises(ValueError):
            summary_messages(history, 16, 100)


class AdditionalContextIntegrationTests(unittest.TestCase):
    setUpClass = classmethod(context_tests.MessengerContextTests.setUpClass.__func__)
    setUp = context_tests.MessengerContextTests.setUp
    tearDown = context_tests.MessengerContextTests.tearDown
    wait = context_tests.MessengerContextTests.wait
    server = context_tests.MessengerContextTests.server
    service = context_tests.MessengerContextTests.service
    messenger = context_tests.MessengerContextTests.messenger
    send = context_tests.MessengerContextTests.send

    def long_history(self):
        return [{"role": role, "content": f"Older {index} " + "x" * 400}
                for index in range(30) for role in ("user", "assistant")]

    def editor(self, app):
        history = app.contact_histories[app.selected_contact.contact_id]
        _, omitted = bounded_messages(
            messenger_system_prompt(app.selected_contact, app.account),
            history, app._input_budget(), app._extra_context(),
        )
        request = (*summary_messages(history, omitted, app.context_budget.value()),
                   app.context_budget.value())
        key = (app._profile_id, app.selected_contact.contact_id)
        dialog = ConversationContextDialog(
            app, app.selected_contact, app._profile_id, app._additional_context[key], request,
        )
        self.objects.append(dialog)
        return dialog

    def test_pin_edit_remove_persist_and_budget_guard_without_summary(self):
        server, url = self.server()
        ai = self.service("llama_cpp", url)
        ai.settings.models["summary"] = "not-installed"
        history = self.long_history()
        app = self.messenger(ai, history)
        contact = app.selected_contact
        editor = self.editor(app)
        self.assertFalse(editor.generate.isEnabled())
        self.assertIn("unavailable", editor.status.text())
        pins = "Remember our camping plan. 🦊"
        editor.pins.setPlainText(pins)
        self.assertEqual(editor.preview.toPlainText(), additional_context(pins, ""))
        editor.save.click()
        self.assertEqual(app.additional_context_preview.toPlainText(), additional_context(pins, ""))
        self.send(app, "Latest")
        self.assertIn(additional_context(pins, ""), server.posts[-1]["messages"][0]["content"])
        self.assertLessEqual(input_size(server.posts[-1]["messages"]), app._input_budget())
        self.assertEqual(app.contact_histories[contact.contact_id][:len(history)], history)
        reopened = MessengerApp(sample_account(), app.service, ai_service=ai)
        self.objects.append(reopened)
        self.assertEqual(reopened._extra_context(), additional_context(pins, ""))
        self.assertEqual(load_context(contact.contact_id, "rook")["pins"], pins)
        self.assertEqual(load_context(CONTACTS[1].contact_id, "rook")["pins"], "")
        self.assertEqual(load_context(contact.contact_id, "other-fursona")["pins"], "")
        with self.assertRaises(ValueError):
            app._apply_additional_context(contact, "rook", {"pins": "x" * 20000, "summary": ""})
        self.assertEqual(load_context(contact.contact_id, "rook")["pins"], pins)
        with patch("win7_2011.win7sim.apps.save_context", side_effect=OSError("disk full")):
            editor = self.editor(app)
            editor.pins.setPlainText("Edited")
            editor.save.click()
            self.assertIn("not saved", editor.status.text())
            self.assertEqual(app._extra_context(), additional_context(pins, ""))
        app._apply_additional_context(contact, "rook", {"pins": "", "summary": ""})
        self.send(app, "Without notes")
        self.assertNotIn(pins, server.posts[-1]["messages"][0]["content"])
        self.assertEqual(len(server.posts), 2)

    def test_optional_summary_is_a_reviewed_draft_and_does_not_touch_transcript(self):
        for backend in ("llama_cpp",):
            with self.subTest(backend=backend):
                server, url = self.server()
                server.models.append("summarizer")
                ai = self.service(backend, url)
                ai.settings.models["summary"] = "summarizer"
                server.model_responses["summarizer"] = (
                    200, {"message": {"content": "Summary of old plans."},
                          "choices": [{"message": {"content": "Summary of old plans."}}]},
                )
                app = self.messenger(ai, self.long_history())
                app._apply_additional_context(app.selected_contact, "rook", {"pins": "", "summary": ""})
                before = config.load_messenger_history(app.selected_contact.contact_id, "rook")
                editor = self.editor(app)
                editor.generate.click()
                self.wait(lambda: not editor.channel.is_busy and not ai.is_busy)
                self.assertEqual(server.posts[0]["model"], "summarizer")
                self.assertEqual(server.posts[0]["messages"], editor.summary_request[0])
                self.assertIn("system:", editor.source.toPlainText())
                self.assertIn("Older", editor.source.toPlainText())
                self.assertEqual(editor.summary.toPlainText(), "Summary of old plans.")
                self.assertEqual(app._extra_context(), "")
                self.assertEqual(config.load_messenger_history(app.selected_contact.contact_id, "rook"), before)
                editor.summary.setPlainText("Reviewed: we planned a visit.")
                editor.save.click()
                self.send(app, "Continue")
                self.assertEqual(server.posts[-1]["model"], "chat")
                self.assertIn("Reviewed: we planned a visit.", server.posts[-1]["messages"][0]["content"])
                self.assertNotIn("Summary of old plans.", server.posts[-1]["messages"][0]["content"])
                self.assertEqual(len(server.posts), 2)

    def test_summary_failure_keeps_approved_context_and_failed_direct_job_is_not_resent(self):
        for backend in ("llama_cpp",):
            with self.subTest(backend=backend):
                server, url = self.server()
                server.models.append("summarizer")
                ai = self.service(backend, url)
                ai.settings.models["summary"] = "summarizer"
                app = self.messenger(ai, self.long_history())
                saved = {"pins": "Keep this", "summary": "Previously reviewed summary"}
                app._apply_additional_context(app.selected_contact, "rook", saved)
                server.status = 400
                server.body = {"error": {"code": "context_length_exceeded", "message": "Too long"}}
                self.send(app, "Failed direct request")
                before = config.load_messenger_history(app.selected_contact.contact_id, "rook")
                server.model_responses["summarizer"] = (404, {"error": "model not found"})
                editor = self.editor(app)
                editor.generate.click()
                self.wait(lambda: not editor.channel.is_busy and not ai.is_busy)
                self.assertEqual(len(server.posts), 2)
                self.assertIn("Summary failed", editor.status.text())
                self.assertEqual(editor.summary.toPlainText(), saved["summary"])
                self.assertEqual(load_context(app.selected_contact.contact_id, "rook"), saved)
                self.assertEqual(config.load_messenger_history(app.selected_contact.contact_id, "rook"), before)
                self.assertTrue(app.send_button.isEnabled())
                self.assertFalse(ai.is_available("summary"))
                server.status = 200
                server.body = {"message": {"content": "Reply"},
                               "choices": [{"message": {"content": "Reply"}}]}
                self.send(app, "Explicit recovery")
                self.assertEqual(len(server.posts), 3)
                self.assertEqual(server.posts[-1]["messages"][-1]["content"], "Explicit recovery")

    def test_empty_or_cancelled_summary_cannot_replace_existing_context(self):
        server, url = self.server()
        ai = self.service("llama_cpp", url)
        app = self.messenger(ai, self.long_history())
        saved = {"pins": "Keep pins", "summary": "Keep summary"}
        app._apply_additional_context(app.selected_contact, "rook", saved)
        editor = self.editor(app)
        editor._finished(True, "   ")
        self.assertEqual(editor.summary.toPlainText(), saved["summary"])
        self.assertIn("failed", editor.status.text())
        editor.generate.click()
        editor.reject()
        self.wait(lambda: not ai.is_busy)
        self.assertEqual(load_context(app.selected_contact.contact_id, "rook"), saved)
        self.assertLessEqual(len(server.posts), 1)

    def test_unreadable_context_does_not_overwrite_file_or_block_chat(self):
        server, url = self.server()
        ai = self.service("llama_cpp", url)
        app = self.messenger(ai, self.long_history())
        path = config._messenger_history_path(app.selected_contact.contact_id, "rook").with_suffix(".context.json")
        path.write_text("{bad", encoding="utf-8")
        app._additional_context.clear()
        app._update_context_status()
        self.assertIn("Additional context not loaded", app.context_status.text())
        self.send(app, "Direct path")
        self.assertTrue(app.send_button.isEnabled())
        self.assertEqual(path.read_text(encoding="utf-8"), "{bad")
        self.assertEqual(len(server.posts), 1)

    def test_real_editor_bounds_summary_to_its_own_model_window(self):
        for backend in ("llama_cpp",):
            with self.subTest(backend=backend):
                server, url = self.server()
                server.models.append("summarizer")
                ai = self.service(backend, url)
                ai.settings.models["summary"] = "summarizer"
                ai.context_windows_by_url[url] = {"summarizer": 2048}
                app = self.messenger(ai, self.long_history())
                app._apply_additional_context(app.selected_contact, "rook", {"pins": "", "summary": ""})

                def interact(dialog):
                    self.assertTrue(dialog.generate.isEnabled())
                    request, start, end, budget = dialog.summary_request
                    self.assertEqual(budget, 1536)
                    self.assertLessEqual(input_size(request), budget)
                    self.assertGreater(start, 0)
                    self.assertGreater(end, start)
                    dialog.generate.click()
                    self.wait(lambda: not dialog.channel.is_busy and not ai.is_busy)
                    self.assertEqual(server.posts[0]["model"], "summarizer")
                    self.assertEqual(server.posts[0]["max_tokens"], 512)
                    dialog.reject()
                    return 0

                with patch.object(ConversationContextDialog, "exec", interact):
                    app.additional_context_button.click()
                self.assertEqual(app._extra_context(), "")
                self.send(app, "Direct still usable")
                self.assertEqual(len(server.posts), 2)

    def test_notes_can_be_removed_even_when_newest_history_no_longer_fits(self):
        server, url = self.server()
        ai = self.service("llama_cpp", url)
        app = self.messenger(ai, self.long_history())
        app._apply_additional_context(
            app.selected_contact, "rook", {"pins": "x" * 4000, "summary": "Old summary"},
        )
        app.context_budget.setValue(4096)
        self.assertIn("exceed", app.context_status.text())
        draft = "x" * 2000
        self.send(app, draft)
        self.assertEqual(app.message_edit.text(), draft)
        self.assertEqual(server.posts, [])
        app._apply_additional_context(app.selected_contact, "rook", {"pins": "", "summary": ""})
        self.send(app, "Small new message")
        self.assertEqual(len(server.posts), 1)

    def test_clear_conversation_removes_notes_and_profile_guard_prevents_wrong_owner(self):
        server, url = self.server()
        ai = self.service("llama_cpp", url)
        app = self.messenger(ai, self.long_history())
        contact = app.selected_contact
        saved = {"pins": "Plans", "summary": "Approved"}
        app._apply_additional_context(contact, "rook", saved)
        with self.assertRaises(RuntimeError):
            app._apply_additional_context(contact, "other-fursona", saved)
        self.assertEqual(load_context(contact.contact_id, "rook"), saved)
        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
            app.clear_history_button.click()
        self.assertEqual(load_context(contact.contact_id, "rook"), {"pins": "", "summary": ""})
        self.assertEqual(config.load_messenger_history(contact.contact_id, "rook"), [])
        self.assertEqual(app._extra_context(), "")
        self.assertEqual(server.posts, [])


if __name__ == "__main__":
    unittest.main()
