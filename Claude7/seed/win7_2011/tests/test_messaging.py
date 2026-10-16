import json
import os
import tempfile
import threading
import unittest
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEventLoop, QTimer, Qt  # noqa: E402
from PySide6.QtWidgets import QApplication, QDialog, QDialogButtonBox, QMessageBox  # noqa: E402

from win7_2011.win7sim import config  # noqa: E402
from win7_2011.win7sim.apps import MessengerApp  # noqa: E402
from win7_2011.win7sim.messenger_import import MessengerImportDialog  # noqa: E402
from win7_2011.win7sim.messenger_legacy import LegacyChatPreviewDialog  # noqa: E402
from win7_2011.win7sim.contacts import CONTACTS, validate_community_contacts  # noqa: E402
from win7_2011.win7sim.identity import FursonaProfile, UserAccount  # noqa: E402
from win7_2011.win7sim.identity import age_on_january_first  # noqa: E402
from win7_2011.win7sim.llama_cpp import normalize_llama_url  # noqa: E402
from win7_2011.win7sim.service import ConnectionSimulator, ServiceState  # noqa: E402


def sample_account() -> UserAccount:
    profile = FursonaProfile(
        fursona_name="Rook",
        species="red fox",
        pronouns="they/them",
        date_of_birth="1988-06-12",
        profile_id="rook",
    )
    return UserAccount(
        desktop_name="Test User",
        fursonas=[profile],
        active_profile_id=profile.profile_id,
    )


def prepared_send(messenger):
    """A mocked send still needs the channel's input-prepared handshake."""
    def send(messages, *_args):
        messenger._input_prepared({
            "omitted": 0, "count": len(json.dumps(messages).encode()), "exact": False,
        })
    return send


class LlamaServerHandler(BaseHTTPRequestHandler):
    requests: list[dict] = []
    reply_text = "A real model reply."

    def do_GET(self) -> None:
        if self.path == "/props":
            self.send_response(404)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        body = json.dumps({"data": [
            {"id": "test-model:3b"}, {"id": "other-model"},
        ]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        length = int(self.headers["Content-Length"])
        payload = json.loads(self.rfile.read(length))
        self.requests.append(payload)
        body = json.dumps(
            {"choices": [{"message": {
                "role": "assistant", "content": self.reply_text,
            }}]}
        ).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args) -> None:
        pass


class MessagingTests(unittest.TestCase):
    def setUp(self) -> None:
        # Failed-save tests retain messages through cleanup. Never open a real
        # modal close prompt during an offscreen test or its cleanup.
        questions = patch(
            "win7_2011.win7sim.apps.QMessageBox.question",
            return_value=QMessageBox.StandardButton.Cancel,
        )
        questions.start()
        self.addCleanup(questions.stop)

    @classmethod
    def setUpClass(cls) -> None:
        cls.qt_app = QApplication.instance() or QApplication([])
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), LlamaServerHandler)
        cls.server_thread = threading.Thread(
            target=cls.server.serve_forever, daemon=True
        )
        cls.server_thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.server_thread.join(timeout=2)

    def wait_for_signal(self, signal, results: list) -> None:
        loop = QEventLoop()
        signal.connect(lambda *args: (results.append(args), loop.quit()))
        QTimer.singleShot(3000, loop.quit)
        loop.exec()

    def test_contact_search_matches_names_and_clearing_preserves_history(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.object(
            config, "MESSENGER_HISTORY", Path(directory) / "Messenger"
        ):
            roster = tuple(CONTACTS)
            target = CONTACTS[-1]
            history = [{"role": "user", "content": "Saved conversation with the last contact."}]
            config.save_messenger_history(target.contact_id, history, "rook")
            service = ConnectionSimulator()
            service.stop()
            messenger = MessengerApp(sample_account(), service)
            try:
                self.assertEqual(messenger.contact_list.count(), len(CONTACTS))
                for query in (target.display_name, target.online_name):
                    messenger.search_input.setText(f"  {query.upper()}  ")
                    expected = [
                        contact for contact in CONTACTS
                        if query.casefold() in contact.display_name.casefold()
                        or query.casefold() in contact.online_name.casefold()
                    ]
                    self.assertEqual(
                        [messenger.contact_list.item(row).data(Qt.ItemDataRole.UserRole)
                         for row in range(messenger.contact_list.count())],
                        [contact.contact_id for contact in expected],
                    )
                    target_row = expected.index(target)
                    messenger.contact_list.setCurrentRow(target_row)
                    self.assertIs(messenger.selected_contact, target)
                    self.assertIn(history[0]["content"], messenger.transcript.toPlainText())
                messenger.search_input.clear()
                self.assertEqual(messenger.contact_list.count(), len(CONTACTS))
                self.assertIs(messenger.selected_contact, target)
                self.assertEqual(messenger.contact_list.currentRow(), len(CONTACTS) - 1)
                self.assertIn(history[0]["content"], messenger.transcript.toPlainText())
                self.assertEqual(config.load_messenger_history(target.contact_id, "rook"), history)
                self.assertEqual(tuple(CONTACTS), roster)
            finally:
                messenger.close()

    def export_fixture(self, profile_id="rook") -> dict:
        return {
            "version": 2, "profile_id": profile_id,
            "conversations": [
                {
                    "contact_id": contact.contact_id,
                    "display_name": contact.display_name,
                    "online_name": contact.online_name,
                    "messages": [
                        {"role": "user", "content": f"Hello {index} 🦊\nSecond line"},
                        {"role": "assistant", "content": "<b>Literal reply</b>"},
                    ],
                }
                for index, contact in enumerate(CONTACTS[:2])
            ],
        }

    def test_export_import_roundtrip_after_reinstall_preserves_roles_and_order(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.object(
            config, "MESSENGER_HISTORY", Path(directory) / "before"
        ):
            fixture = self.export_fixture()
            for chat in fixture["conversations"]:
                config.save_messenger_history(chat["contact_id"], chat["messages"], "rook")
            source = Path(directory) / "backup.json"
            config.export_messenger_histories(source, profile_id="rook")
            exported = config.read_messenger_export(source)
            with patch.object(config, "MESSENGER_HISTORY", Path(directory) / "after"):
                updates = config.import_messenger_histories(exported, "new-rook", "skip")
                self.assertEqual(list(updates), [c.contact_id for c in CONTACTS[:2]])
                for chat in fixture["conversations"]:
                    self.assertEqual(
                        config.load_messenger_history(chat["contact_id"], "new-rook"),
                        chat["messages"],
                    )
                    self.assertEqual(config.load_messenger_history(chat["contact_id"], "rook"), [])
                legacy = dict(exported)
                legacy["version"] = 1
                del legacy["profile_id"]
                config.import_messenger_histories(legacy, "explicit-owner", "skip")
                self.assertEqual(
                    config.load_messenger_history(CONTACTS[0].contact_id, "explicit-owner"),
                    fixture["conversations"][0]["messages"],
                )

    def test_import_policies_preserve_unrelated_contacts_and_fursonas(self) -> None:
        fixture = self.export_fixture()
        old = [{"role": "assistant", "content": "Keep existing"}]
        for policy in ("skip", "append", "replace"):
            with self.subTest(policy=policy), tempfile.TemporaryDirectory() as directory, patch.object(
                config, "MESSENGER_HISTORY", Path(directory)
            ):
                for contact, owner in ((CONTACTS[0], "rook"), (CONTACTS[2], "rook"), (CONTACTS[0], "moss")):
                    config.save_messenger_history(contact.contact_id, old, owner)
                other = config._messenger_history_path(CONTACTS[2].contact_id, "rook").read_bytes()
                updates = config.import_messenger_histories(fixture, "rook", policy)
                imported = fixture["conversations"][0]["messages"]
                expected = old if policy == "skip" else old + imported if policy == "append" else imported
                self.assertEqual(config.load_messenger_history(CONTACTS[0].contact_id, "rook"), expected)
                self.assertEqual(len(updates), 1 if policy == "skip" else 2)
                self.assertEqual(config.load_messenger_history(CONTACTS[0].contact_id, "moss"), old)
                self.assertEqual(config._messenger_history_path(CONTACTS[2].contact_id, "rook").read_bytes(), other)

    def test_invalid_exports_are_rejected_in_full_before_import(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.object(
            config, "MESSENGER_HISTORY", Path(directory) / "histories"
        ):
            mutations = [
                lambda raw: raw.update(version=True),
                lambda raw: raw.update(version=3),
                lambda raw: raw.update(profile_id="../escape"),
                lambda raw: raw.update(profile_id=None),
                lambda raw: raw.update(conversations=[]),
                lambda raw: raw["conversations"].append(raw["conversations"][0]),
                lambda raw: raw["conversations"][1].update(contact_id="../escape"),
                lambda raw: raw["conversations"][1].update(contact_id="unknown-contact"),
                lambda raw: raw["conversations"][1].update(messages={}),
                lambda raw: raw["conversations"][1]["messages"][0].update(role="system"),
                lambda raw: raw["conversations"][1]["messages"][0].update(content=123),
                lambda raw: raw["conversations"][1]["messages"][0].update(extra="invalid"),
            ]
            old = [{"role": "user", "content": "Original"}]
            config.save_messenger_history(CONTACTS[0].contact_id, old, "rook")
            original = config._messenger_history_path(CONTACTS[0].contact_id, "rook").read_bytes()
            for mutate in mutations:
                raw = self.export_fixture()
                mutate(raw)
                with self.assertRaises(ValueError):
                    config.import_messenger_histories(raw, "rook", "replace")
                self.assertEqual(config._messenger_history_path(CONTACTS[0].contact_id, "rook").read_bytes(), original)
                self.assertFalse(config._messenger_history_path(CONTACTS[1].contact_id, "rook").exists())
            source = Path(directory) / "invalid.json"
            for text in ('{"version": 1, "version": 2}', "{bad", "[]"):
                source.write_text(text, encoding="utf-8")
                with self.assertRaises(ValueError):
                    config.read_messenger_export(source)
            with self.assertRaises(ValueError):
                config.import_messenger_histories(self.export_fixture(), None, "replace")
            with self.assertRaises(ValueError):
                config.import_messenger_histories(self.export_fixture(), "rook", "silent")

    def test_import_write_and_swap_failures_leave_all_original_bytes_intact(self) -> None:
        for failure in ("stage", "backup", "install"):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as directory, patch.object(
                config, "MESSENGER_HISTORY", Path(directory)
            ):
                old = [{"role": "assistant", "content": "Original"}]
                config.save_messenger_history(CONTACTS[0].contact_id, old, "rook")
                path = config._messenger_history_path(CONTACTS[0].contact_id, "rook")
                original = path.read_bytes()
                rename = os.rename
                write = config._atomic_write_private_json
                writes = []

                def fail_write(target, text):
                    writes.append(target)
                    if len(writes) == 2:
                        raise OSError("Disk full")
                    write(target, text)

                def fail_rename(source, target):
                    if (failure == "backup" and Path(source) == path.parent) or (
                        failure == "install" and Path(source).name == "staged"
                    ):
                        raise PermissionError("Access denied")
                    rename(source, target)

                with patch.object(config, "_atomic_write_private_json", side_effect=fail_write if failure == "stage" else write), patch.object(
                    config.os, "rename", side_effect=fail_rename
                ), self.assertRaises(OSError):
                    config.import_messenger_histories(self.export_fixture(), "rook", "replace")
                self.assertEqual(path.read_bytes(), original)
                self.assertFalse(config._messenger_history_path(CONTACTS[1].contact_id, "rook").exists())
                self.assertEqual(list(path.parent.parent.glob(".messenger-import-*")), [])

    def test_import_damaged_existing_chat_is_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.object(
            config, "MESSENGER_HISTORY", Path(directory)
        ):
            path = config._messenger_history_path(CONTACTS[1].contact_id, "rook")
            path.parent.mkdir(parents=True)
            path.write_bytes(b"{ damaged")
            for policy in ("append", "replace"):
                with self.assertRaises(ValueError):
                    config.import_messenger_histories(self.export_fixture(), "rook", policy)
                self.assertEqual(path.read_bytes(), b"{ damaged")
                self.assertFalse(config._messenger_history_path(CONTACTS[0].contact_id, "rook").exists())
            config.import_messenger_histories(self.export_fixture(), "rook", "skip")
            self.assertEqual(path.read_bytes(), b"{ damaged")

    def test_import_preview_displays_all_messages_as_plain_text(self) -> None:
        fixture = self.export_fixture()
        preview = MessengerImportDialog(fixture, "Rook")
        try:
            self.assertEqual(preview.contacts.count(), 2)
            self.assertEqual(preview.policy.currentData(), "skip")
            for row, chat in enumerate(fixture["conversations"]):
                preview.contacts.setCurrentRow(row)
                for message in chat["messages"]:
                    self.assertIn(message["content"], preview.messages.toPlainText())
                    self.assertIn(message["role"], preview.messages.toPlainText())
                self.assertIn(chat["contact_id"], preview.contacts.item(row).text())
        finally:
            preview.close()

    def test_import_ui_cancel_success_failure_and_unsaved_protection(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.object(
            config, "MESSENGER_HISTORY", Path(directory) / "Messenger"
        ):
            source = Path(directory) / "backup.json"
            fixture = self.export_fixture()
            source.write_text(json.dumps(fixture), encoding="utf-8")
            service = ConnectionSimulator()
            service.stop()
            messenger = MessengerApp(sample_account(), service)
            self.addCleanup(messenger.close)
            self.addCleanup(messenger.deleteLater)
            self.addCleanup(service.deleteLater)
            with patch("win7_2011.win7sim.apps.QFileDialog.getOpenFileName", return_value=(str(source), "")), patch.object(
                MessengerImportDialog, "exec", return_value=QDialog.DialogCode.Rejected
            ):
                messenger.import_button.click()
            self.assertFalse(config.MESSENGER_HISTORY.exists())
            with patch("win7_2011.win7sim.apps.QFileDialog.getOpenFileName", return_value=(str(source), "")), patch.object(
                MessengerImportDialog, "exec", return_value=QDialog.DialogCode.Accepted
            ), patch("win7_2011.win7sim.apps.QMessageBox.information"), patch(
                "win7_2011.win7sim.apps.QMessageBox.warning"
            ) as warning:
                with patch.object(config, "_atomic_write_private_json", side_effect=OSError("Disk full")):
                    messenger.import_button.click()
                warning.assert_called_once()
                self.assertEqual(messenger.contact_histories[CONTACTS[0].contact_id], [])
                messenger.import_button.click()
                self.assertIn("Literal reply", messenger.transcript.toPlainText())
                self.assertEqual(messenger.contact_histories[CONTACTS[1].contact_id], fixture["conversations"][1]["messages"])
                warning.reset_mock()
                messenger.contact_histories[CONTACTS[0].contact_id].append({"role": "user", "content": "Unsaved"})
                with patch("win7_2011.win7sim.apps.import_messenger_histories") as importer:
                    messenger.import_button.click()
                    importer.assert_not_called()
                warning.assert_called_once()
            reopened = MessengerApp(sample_account(), service)
            self.addCleanup(reopened.close)
            self.addCleanup(reopened.deleteLater)
            self.assertEqual(reopened.contact_histories[CONTACTS[0].contact_id], fixture["conversations"][0]["messages"])
            with patch.object(type(messenger.client), "is_busy", new=property(lambda _: True)):
                messenger._refresh_controls()
                self.assertFalse(messenger.import_button.isEnabled())

    def test_selecting_second_filtered_contact_uses_stable_id(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.object(
            config, "MESSENGER_HISTORY", Path(directory) / "Messenger"
        ):
            service = ConnectionSimulator()
            service.stop()
            messenger = MessengerApp(sample_account(), service)
            try:
                messenger.search_input.setText("alex")
                matches = [
                    contact for contact in CONTACTS
                    if "alex" in contact.display_name.casefold()
                    or "alex" in contact.online_name.casefold()
                ]
                self.assertGreater(len(matches), 1)
                target = matches[-1]
                self.assertNotEqual(target, CONTACTS[len(matches) - 1])
                history = [{"role": "assistant", "content": "History belonging to this ID."}]
                messenger.contact_histories[target.contact_id] = history
                messenger.contact_list.setCurrentRow(len(matches) - 1)
                self.assertIs(messenger.selected_contact, target)
                self.assertEqual(messenger.contact_heading.text(), target.display_name)
                self.assertIn(history[0]["content"], messenger.transcript.toPlainText())
                self.assertEqual(messenger.contact_histories[CONTACTS[0].contact_id], [])
            finally:
                messenger.close()

    def test_no_search_results_clear_selection_and_search_is_disabled_when_busy(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.object(
            config, "MESSENGER_HISTORY", Path(directory) / "Messenger"
        ):
            service = ConnectionSimulator()
            service.stop()
            messenger = MessengerApp(sample_account(), service)
            try:
                messenger.search_input.setText("no-such-contact-unique-query")
                self.assertEqual(messenger.contact_list.count(), 0)
                self.assertIsNone(messenger.selected_contact)
                self.assertEqual(messenger.contact_heading.text(), "Select a contact")
                self.assertEqual(messenger.transcript.toPlainText(), "")
                self.assertEqual(messenger.search_results.text(), "No matching contacts")
                self.assertFalse(messenger.send_button.isEnabled())
                self.assertFalse(messenger.export_history_button.isEnabled())
                self.assertFalse(messenger.clear_history_button.isEnabled())
                messenger.search_input.clear()
                self.assertEqual(messenger.contact_list.count(), len(CONTACTS))
                self.assertIs(messenger.selected_contact, CONTACTS[0])
                with patch.object(type(messenger.client), "is_busy", new=property(lambda _: True)):
                    messenger._refresh_controls()
                    self.assertFalse(messenger.search_input.isEnabled())
                    self.assertFalse(messenger.contact_list.isEnabled())
                messenger._refresh_controls()
                self.assertTrue(messenger.search_input.isEnabled())
            finally:
                messenger.close()

    def test_provider_url_must_point_to_a_local_host(self) -> None:
        self.assertEqual(
            normalize_llama_url("http://localhost:9931/v1/"),
            "http://localhost:9931",
        )
        with self.assertRaises(ValueError):
            normalize_llama_url("https://example.com")

    def test_messenger_restores_each_contact_history_when_reopened(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            history_root = Path(directory) / "Messenger"
            with patch.object(config, "MESSENGER_HISTORY", history_root):
                service = ConnectionSimulator()
                first = MessengerApp(sample_account(), service)
                contact = first.selected_contact
                assert contact is not None
                first._can_chat = lambda: True
                with patch.object(first.client, "send_chat", side_effect=prepared_send(first)) as send_chat:
                    first.message_edit.setText("Are you going to the art show?")
                    first._send_message()
                    send_chat.assert_called_once()
                first._response_finished(True, "Yes, I will see you there.")

                transcript_path = config._messenger_history_path(contact.contact_id, "rook")
                self.assertTrue(transcript_path.is_file())
                first.close()
                first.deleteLater()
                self.qt_app.processEvents()

                reopened = MessengerApp(sample_account(), service)
                self.assertEqual(
                    reopened.contact_histories[contact.contact_id],
                    [
                        {
                            "role": "user",
                            "content": "Are you going to the art show?",
                        },
                        {
                            "role": "assistant",
                            "content": "Yes, I will see you there.",
                        },
                    ],
                )
                self.assertIn("art show", reopened.transcript.toPlainText())
                reopened.close()
                reopened.deleteLater()
                service.stop()
                service.deleteLater()

    def test_damaged_contact_history_is_reported_and_left_untouched(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            history_root = Path(directory) / "Messenger"
            history_root.mkdir()
            contact = CONTACTS[0]
            damaged_file = history_root / "Profiles" / "rook" / f"{contact.contact_id}.json"
            damaged_file.parent.mkdir(parents=True)
            damaged_contents = "{ this is not valid JSON"
            damaged_file.write_text(damaged_contents, encoding="utf-8")
            with patch.object(config, "MESSENGER_HISTORY", history_root):
                service = ConnectionSimulator()
                messenger = MessengerApp(sample_account(), service)
                messenger.contact_list.setCurrentRow(0)
                self.assertIn("Could not read saved conversation", messenger.history_status.text())
                self.assertIn("will not be saved", messenger.history_status.text())
                self.assertEqual(damaged_file.read_text(encoding="utf-8"), damaged_contents)
                self.assertEqual(messenger.contact_histories[contact.contact_id], [])
                messenger.close()
                messenger.deleteLater()
                service.stop()
                service.deleteLater()

    def test_retry_save_recovers_current_conversation_offline_without_clearing(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.object(
            config, "MESSENGER_HISTORY", Path(directory)
        ):
            contact = CONTACTS[0]
            saved = [{"role": "user", "content": "Already saved"}]
            config.save_messenger_history(contact.contact_id, saved, "rook")
            path = config._messenger_history_path(contact.contact_id, "rook")
            original = path.read_bytes()
            service = ConnectionSimulator()
            messenger = MessengerApp(sample_account(), service)
            self.addCleanup(service.deleteLater)
            self.addCleanup(service.stop)
            self.addCleanup(messenger.deleteLater)
            self.addCleanup(messenger.close)
            history = messenger.contact_histories[contact.contact_id]
            history.append({"role": "user", "content": "Not yet saved"})
            messenger._render_history()
            with patch.object(Path, "replace", side_effect=PermissionError("Access denied")):
                messenger._save_history(contact.contact_id)
                self.assertEqual(path.read_bytes(), original)
                self.assertFalse(path.with_suffix(".json.tmp").exists())
                self.assertIn("Could not save conversation", messenger.history_status.text())
                self.assertFalse(messenger.retry_save_button.isHidden())
                messenger.retry_save_button.click()
                self.assertIn(contact.contact_id, messenger.history_errors)
                self.assertEqual(path.read_bytes(), original)
            history.append({"role": "assistant", "content": "Latest reply"})
            messenger._render_history()
            service.begin_interruption(ServiceState.DISCONNECTED, 60_000)
            self.assertTrue(messenger.retry_save_button.isEnabled())
            with patch.object(type(messenger.client), "is_busy", new=property(lambda _: True)):
                messenger._refresh_controls()
                self.assertFalse(messenger.retry_save_button.isEnabled())
                with patch("win7_2011.win7sim.apps.save_messenger_history") as save:
                    messenger._retry_save_history()
                    save.assert_not_called()
            messenger._refresh_controls()
            messenger.retry_save_button.click()
            self.assertEqual(config.load_messenger_history(contact.contact_id, "rook"), history)
            self.assertNotIn(contact.contact_id, messenger.history_errors)
            self.assertNotIn("Could not save", messenger.history_status.text())
            self.assertTrue(messenger.retry_save_button.isHidden())
            with patch("win7_2011.win7sim.apps.QMessageBox.question") as prompt:
                self.assertTrue(messenger.confirm_close())
                prompt.assert_not_called()
            self.assertIn("Not yet saved", messenger.transcript.toPlainText())
            reopened = MessengerApp(sample_account(), service)
            self.addCleanup(reopened.deleteLater)
            self.addCleanup(reopened.close)
            self.assertEqual(reopened.contact_histories[contact.contact_id], history)
            messenger.contact_list.setCurrentRow(-1)
            with patch("win7_2011.win7sim.apps.save_messenger_history") as save:
                messenger._retry_save_history()
                save.assert_not_called()

    def test_close_cancel_discard_and_retry_preserve_latest_messages(self) -> None:
        from PySide6.QtGui import QCloseEvent

        with tempfile.TemporaryDirectory() as directory, patch.object(
            config, "MESSENGER_HISTORY", Path(directory)
        ):
            service = ConnectionSimulator()
            messenger = MessengerApp(sample_account(), service)
            self.addCleanup(service.deleteLater)
            self.addCleanup(service.stop)
            self.addCleanup(messenger.deleteLater)
            contact_id = CONTACTS[0].contact_id
            messages = messenger.contact_histories[contact_id]
            messages.append({"role": "user", "content": "Keep this message"})
            with patch("win7_2011.win7sim.apps.save_messenger_history", side_effect=OSError("disk full")):
                messenger._save_history(contact_id)
                with patch.object(messenger.client, "cancel") as cancel:
                    event = QCloseEvent()
                    messenger.closeEvent(event)
                    self.assertFalse(event.isAccepted())
                    cancel.assert_not_called()
                with patch(
                    "win7_2011.win7sim.apps.QMessageBox.question",
                    return_value=QMessageBox.StandardButton.Retry,
                ), patch("win7_2011.win7sim.apps.QMessageBox.warning") as warning:
                    self.assertFalse(messenger.confirm_close())
                    warning.assert_called_once()
            self.assertEqual(messages, [{"role": "user", "content": "Keep this message"}])
            with patch(
                "win7_2011.win7sim.apps.QMessageBox.question",
                return_value=QMessageBox.StandardButton.Discard,
            ), patch.object(messenger.client, "cancel") as cancel:
                event = QCloseEvent()
                messenger.closeEvent(event)
                self.assertTrue(event.isAccepted())
                cancel.assert_called_once()
            # The preflight itself does not erase anything; a successful retry
            # saves the latest in-memory history and removes future warnings.
            messages.append({"role": "assistant", "content": "Latest reply"})
            with patch(
                "win7_2011.win7sim.apps.QMessageBox.question",
                return_value=QMessageBox.StandardButton.Retry,
            ) as prompt:
                self.assertTrue(messenger.confirm_close())
                self.assertEqual(prompt.call_args.args[4], QMessageBox.StandardButton.Cancel)
            self.assertEqual(config.load_messenger_history(contact_id, "rook"), messages)
            with patch("win7_2011.win7sim.apps.QMessageBox.question") as prompt:
                self.assertTrue(messenger.confirm_close())
                prompt.assert_not_called()

    def test_close_retry_covers_multiple_contacts_and_inactive_fursonas(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.object(
            config, "MESSENGER_HISTORY", Path(directory)
        ):
            account = sample_account()
            account.fursonas.append(FursonaProfile(
                fursona_name="Moss", species="wolf", pronouns="they/them",
                date_of_birth="1988-06-12", profile_id="moss",
            ))
            service = ConnectionSimulator()
            messenger = MessengerApp(account, service)
            self.addCleanup(service.deleteLater)
            self.addCleanup(service.stop)
            self.addCleanup(messenger.deleteLater)
            expected = {}
            with patch("win7_2011.win7sim.apps.save_messenger_history", side_effect=OSError("disk full")):
                for profile_id, contact in (
                    ("rook", CONTACTS[0]), ("rook", CONTACTS[1]), ("moss", CONTACTS[0]),
                ):
                    account.active_profile_id = profile_id
                    messenger._refresh_controls()
                    history = messenger.contact_histories[contact.contact_id]
                    history.append({"role": "user", "content": f"{profile_id}: {contact.contact_id}"})
                    expected[(profile_id, contact.contact_id)] = list(history)
                    messenger._save_history(contact.contact_id)
            with patch(
                "win7_2011.win7sim.apps.QMessageBox.question",
                return_value=QMessageBox.StandardButton.Cancel,
            ) as prompt:
                self.assertFalse(messenger.confirm_close())
                text = prompt.call_args.args[2]
                for label in ("Rook", "Moss", CONTACTS[0].display_name, CONTACTS[1].display_name):
                    self.assertIn(label, text)
            with patch(
                "win7_2011.win7sim.apps.QMessageBox.question",
                return_value=QMessageBox.StandardButton.Retry,
            ):
                self.assertTrue(messenger.confirm_close())
            self.assertFalse(messenger._unsaved_conversations)
            self.assertEqual(account.active_profile_id, "moss")
            for (profile_id, contact_id), history in expected.items():
                self.assertEqual(config.load_messenger_history(contact_id, profile_id), history)

    def test_close_retry_skips_unreadable_transcript_and_keeps_failed_chats(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.object(
            config, "MESSENGER_HISTORY", Path(directory)
        ):
            damaged, writable, failing = CONTACTS[:3]
            path = config._messenger_history_path(damaged.contact_id, "rook")
            path.parent.mkdir(parents=True)
            path.write_bytes(b"{ damaged transcript")
            service = ConnectionSimulator()
            messenger = MessengerApp(sample_account(), service)
            self.addCleanup(service.deleteLater)
            self.addCleanup(service.stop)
            self.addCleanup(messenger.deleteLater)
            # A load error alone is not a new unsaved message.
            self.assertTrue(messenger.confirm_close())
            with patch("win7_2011.win7sim.apps.save_messenger_history", side_effect=OSError("disk full")):
                for contact in (damaged, writable, failing):
                    messenger.contact_histories[contact.contact_id].append(
                        {"role": "user", "content": contact.display_name}
                    )
                    messenger._save_history(contact.contact_id)
            real_save = config.save_messenger_history
            def save(contact_id, history, profile_id):
                if contact_id == failing.contact_id:
                    raise OSError("Still full")
                real_save(contact_id, history, profile_id)
            with patch(
                "win7_2011.win7sim.apps.QMessageBox.question",
                return_value=QMessageBox.StandardButton.Retry,
            ), patch("win7_2011.win7sim.apps.QMessageBox.warning"), patch(
                "win7_2011.win7sim.apps.save_messenger_history", side_effect=save,
            ) as saves:
                self.assertFalse(messenger.confirm_close())
                self.assertEqual({call.args[0] for call in saves.call_args_list},
                                 {writable.contact_id, failing.contact_id})
            self.assertEqual(messenger._unsaved_conversations,
                             {("rook", damaged.contact_id), ("rook", failing.contact_id)})
            self.assertEqual(path.read_bytes(), b"{ damaged transcript")
            with patch.object(type(messenger.client), "is_busy", new=property(lambda _: True)), patch(
                "win7_2011.win7sim.apps.QMessageBox.question",
                return_value=QMessageBox.StandardButton.Retry,
            ) as prompt, patch("win7_2011.win7sim.apps.save_messenger_history") as saves:
                self.assertFalse(messenger.confirm_close())
                self.assertFalse(prompt.call_args.args[3] & QMessageBox.StandardButton.Retry)
                saves.assert_not_called()

    def test_next_message_retries_failed_save_and_keeps_saving(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.object(
            config, "MESSENGER_HISTORY", Path(directory)
        ):
            service = ConnectionSimulator()
            messenger = MessengerApp(sample_account(), service)
            self.addCleanup(service.deleteLater)
            self.addCleanup(service.stop)
            self.addCleanup(messenger.deleteLater)
            self.addCleanup(messenger.close)
            contact_id = CONTACTS[0].contact_id
            messenger._can_chat = lambda: True
            messenger._refresh_controls()
            with patch.object(messenger.client, "send_chat", side_effect=prepared_send(messenger)):
                with patch.object(Path, "replace", side_effect=OSError("Disk full")):
                    messenger.message_edit.setText("First unsaved message")
                    messenger.send_button.click()
                self.assertIn(contact_id, messenger.history_errors)
                messenger.message_edit.setText("Second message retries saving")
                messenger.send_button.click()
                self.assertNotIn(contact_id, messenger.history_errors)
                messenger._response_finished(True, "Reply is also saved")
                messenger.message_edit.setText("Continued saving")
                messenger.send_button.click()
            self.assertEqual(
                config.load_messenger_history(contact_id, "rook"),
                [
                    {"role": "user", "content": "First unsaved message"},
                    {"role": "user", "content": "Second message retries saving"},
                    {"role": "assistant", "content": "Reply is also saved"},
                    {"role": "user", "content": "Continued saving"},
                ],
            )

    def test_damaged_transcript_stays_protected_from_retry_and_automatic_saves(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.object(
            config, "MESSENGER_HISTORY", Path(directory)
        ):
            contact_id = CONTACTS[0].contact_id
            path = config._messenger_history_path(contact_id, "rook")
            path.parent.mkdir(parents=True)
            original = b"{ damaged transcript"
            path.write_bytes(original)
            service = ConnectionSimulator()
            messenger = MessengerApp(sample_account(), service)
            self.addCleanup(service.deleteLater)
            self.addCleanup(service.stop)
            self.addCleanup(messenger.deleteLater)
            self.addCleanup(messenger.close)
            messenger._can_chat = lambda: True
            messenger._refresh_controls()
            self.assertTrue(messenger.retry_save_button.isHidden())
            self.assertFalse(messenger.retry_save_button.isEnabled())
            with patch("win7_2011.win7sim.apps.save_messenger_history") as save:
                messenger._retry_save_history()
                with patch.object(messenger.client, "send_chat", side_effect=prepared_send(messenger)):
                    messenger.message_edit.setText("Keep this only in memory")
                    messenger.send_button.click()
                    messenger._response_finished(True, "Reply kept in memory")
                save.assert_not_called()
            self.assertEqual(path.read_bytes(), original)
            self.assertIn("will not be saved", messenger.history_status.text())
            self.assertEqual(len(messenger.contact_histories[contact_id]), 2)

    def test_retry_errors_and_load_protection_are_isolated_by_fursona(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.object(
            config, "MESSENGER_HISTORY", Path(directory)
        ):
            contact_id = CONTACTS[0].contact_id
            path = config._messenger_history_path(contact_id, "rook")
            path.parent.mkdir(parents=True)
            path.write_bytes(b"{ damaged")
            account = sample_account()
            account.fursonas.append(FursonaProfile(
                "Moss", "otter", "she/her", "1985-03-09", profile_id="moss"
            ))
            service = ConnectionSimulator()
            messenger = MessengerApp(account, service)
            self.addCleanup(service.deleteLater)
            self.addCleanup(service.stop)
            self.addCleanup(messenger.deleteLater)
            self.addCleanup(messenger.close)
            account.active_profile_id = "moss"
            messenger._refresh_controls()
            messages = [{"role": "user", "content": "Moss's unsaved chat"}]
            messenger.contact_histories[contact_id].extend(messages)
            with patch.object(Path, "replace", side_effect=OSError("Disk full")):
                messenger._save_history(contact_id)
            account.active_profile_id = "rook"
            messenger._refresh_controls()
            self.assertTrue(messenger.retry_save_button.isHidden())
            # A delayed reply for Moss can recover without touching Rook's file.
            messenger._pending_contact_id = contact_id
            messenger._pending_profile_id = "moss"
            messenger._response_finished(True, "Moss's delayed reply")
            self.assertEqual(
                config.load_messenger_history(contact_id, "moss"),
                messages + [{"role": "assistant", "content": "Moss's delayed reply"}],
            )
            self.assertEqual(path.read_bytes(), b"{ damaged")
            self.assertIn(contact_id, messenger.history_errors)
            account.active_profile_id = "moss"
            messenger._refresh_controls()
            self.assertNotIn(contact_id, messenger.history_errors)
            self.assertNotIn(contact_id, messenger.blocked_history_saves)

    def test_clear_selected_history_preserves_other_chats_and_can_start_again(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            history_root = Path(directory) / "Messenger"
            with patch.object(config, "MESSENGER_HISTORY", history_root):
                first, selected = CONTACTS[:2]
                messages = [{"role": "user", "content": "Saved chat"}]
                config.save_messenger_history(first.contact_id, messages, "rook")
                config.save_messenger_history(selected.contact_id, messages, "rook")
                other_path = config._messenger_history_path(first.contact_id, "rook")
                other_bytes = other_path.read_bytes()
                document = Path(directory) / "document.txt"
                document.write_text("Keep this document", encoding="utf-8")
                service = ConnectionSimulator()
                messenger = MessengerApp(sample_account(), service)
                self.addCleanup(service.deleteLater)
                self.addCleanup(service.stop)
                self.addCleanup(messenger.deleteLater)
                self.addCleanup(messenger.close)
                messenger.contact_list.setCurrentRow(1)
                with patch(
                    "win7_2011.win7sim.apps.QMessageBox.question",
                    return_value=QMessageBox.StandardButton.Yes,
                ) as confirm:
                    messenger.clear_history_button.click()
                self.assertIn(selected.display_name, confirm.call_args.args[2])
                self.assertEqual(confirm.call_args.args[4], QMessageBox.StandardButton.No)
                self.assertFalse(config._messenger_history_path(selected.contact_id, "rook").exists())
                self.assertEqual(messenger.contact_histories[selected.contact_id], [])
                self.assertEqual(messenger.transcript.toPlainText(), "")
                self.assertEqual(other_path.read_bytes(), other_bytes)
                self.assertEqual(messenger.contact_histories[first.contact_id], messages)
                self.assertEqual(document.read_text(encoding="utf-8"), "Keep this document")
                reopened = MessengerApp(sample_account(), service)
                self.addCleanup(reopened.deleteLater)
                self.addCleanup(reopened.close)
                self.assertEqual(reopened.contact_histories[selected.contact_id], [])
                self.assertEqual(reopened.contact_histories[first.contact_id], messages)
                messenger._can_chat = lambda: True
                with patch.object(messenger.client, "send_chat", side_effect=prepared_send(messenger)) as send_chat:
                    messenger.message_edit.setText("A new conversation")
                    messenger._send_message()
                self.assertEqual(len(send_chat.call_args.args[0]), 2)
                self.assertEqual(
                    config.load_messenger_history(selected.contact_id, "rook"),
                    [{"role": "user", "content": "A new conversation"}],
                )

    def test_cancel_or_failed_delete_keeps_history_in_memory_and_on_disk(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(config, "MESSENGER_HISTORY", Path(directory)):
                contact = CONTACTS[0]
                messages = [{"role": "user", "content": "Do not lose this"}]
                config.save_messenger_history(contact.contact_id, messages, "rook")
                service = ConnectionSimulator()
                messenger = MessengerApp(sample_account(), service)
                self.addCleanup(service.deleteLater)
                self.addCleanup(service.stop)
                self.addCleanup(messenger.deleteLater)
                self.addCleanup(messenger.close)
                for answer in (QMessageBox.StandardButton.No, QMessageBox.StandardButton.Yes):
                    with patch(
                        "win7_2011.win7sim.apps.QMessageBox.question",
                        return_value=answer,
                    ), patch(
                        "win7_2011.win7sim.apps.clear_messenger_history",
                        side_effect=PermissionError("Access denied"),
                    ) as delete, patch(
                        "win7_2011.win7sim.apps.QMessageBox.warning"
                    ) as warning:
                        messenger.clear_history_button.click()
                    if answer == QMessageBox.StandardButton.No:
                        delete.assert_not_called()
                        warning.assert_not_called()
                    else:
                        delete.assert_called_once_with(contact.contact_id, "rook")
                        warning.assert_called_once()
                    self.assertEqual(config.load_messenger_history(contact.contact_id, "rook"), messages)
                    self.assertEqual(messenger.contact_histories[contact.contact_id], messages)
                    self.assertIn("Do not lose this", messenger.transcript.toPlainText())

    def test_clear_damaged_history_recovers_saving_and_missing_file_is_safe(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(config, "MESSENGER_HISTORY", root):
                contact = CONTACTS[0]
                path = config._messenger_history_path(contact.contact_id, "rook")
                path.parent.mkdir(parents=True)
                path.write_text("{ damaged", encoding="utf-8")
                service = ConnectionSimulator()
                messenger = MessengerApp(sample_account(), service)
                self.addCleanup(service.deleteLater)
                self.addCleanup(service.stop)
                self.addCleanup(messenger.deleteLater)
                self.addCleanup(messenger.close)
                self.assertIn(contact.contact_id, messenger.history_errors)
                with patch(
                    "win7_2011.win7sim.apps.QMessageBox.question",
                    return_value=QMessageBox.StandardButton.Yes,
                ):
                    messenger.clear_history_button.click()
                    messenger.clear_history_button.click()
                self.assertFalse(path.exists())
                self.assertNotIn(contact.contact_id, messenger.history_errors)
                self.assertNotIn("unavailable", messenger.history_status.text())
                messenger.contact_histories[contact.contact_id].append(
                    {"role": "user", "content": "Save again"}
                )
                messenger._save_history(contact.contact_id)
                self.assertEqual(
                    config.load_messenger_history(contact.contact_id, "rook"),
                    messenger.contact_histories[contact.contact_id],
                )

    def test_clear_is_available_offline_but_not_during_reply_or_without_contact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(config, "MESSENGER_HISTORY", Path(directory)):
                service = ConnectionSimulator()
                messenger = MessengerApp(sample_account(), service)
                self.addCleanup(service.deleteLater)
                self.addCleanup(service.stop)
                self.addCleanup(messenger.deleteLater)
                self.addCleanup(messenger.close)
                service.begin_interruption(ServiceState.DISCONNECTED, 60_000)
                self.assertTrue(messenger.clear_history_button.isEnabled())
                with patch.object(type(messenger.client), "is_busy", new=property(lambda _: True)):
                    messenger._refresh_controls()
                    self.assertFalse(messenger.clear_history_button.isEnabled())
                    with patch("win7_2011.win7sim.apps.QMessageBox.question") as confirm:
                        messenger._clear_history()
                        confirm.assert_not_called()
                messenger.contact_list.setCurrentRow(-1)
                self.assertFalse(messenger.clear_history_button.isEnabled())
                with patch("win7_2011.win7sim.apps.QMessageBox.question") as confirm:
                    messenger._clear_history()
                    confirm.assert_not_called()

    def test_history_storage_rejects_unsafe_ids_and_invalid_transcripts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(config, "MESSENGER_HISTORY", Path(directory)):
                with self.assertRaisesRegex(ValueError, "contact ID is invalid"):
                    config.save_messenger_history("../outside", [])
                with self.assertRaisesRegex(ValueError, "contact ID is invalid"):
                    config.clear_messenger_history("../outside")
                with self.assertRaisesRegex(ValueError, "invalid message"):
                    config.save_messenger_history(
                        "morgan-vale",
                        [{"role": ["user"], "content": "unsafe role"}],
                    )

    def test_two_fursonas_share_a_contact_but_not_messages_or_pending_replies(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.object(
            config, "MESSENGER_HISTORY", Path(directory) / "Messenger"
        ):
            account = sample_account()
            account.fursonas.append(FursonaProfile(
                "Moss", "otter", "she/her", "1985-03-09", profile_id="moss"
            ))
            service = ConnectionSimulator()
            messenger = MessengerApp(account, service)
            self.addCleanup(service.deleteLater)
            self.addCleanup(service.stop)
            self.addCleanup(messenger.deleteLater)
            self.addCleanup(messenger.close)
            contact = CONTACTS[0]
            messenger._can_chat = lambda: True
            with patch.object(messenger.client, "send_chat", side_effect=prepared_send(messenger)) as send:
                messenger.message_edit.setText("Rook's private message")
                messenger._send_message()
                account.active_profile_id = "moss"
                messenger._select_contact(0)
                self.assertEqual(messenger.contact_histories[contact.contact_id], [])
                self.assertNotIn("Rook's private", messenger.transcript.toPlainText())
                # A reply arriving after a switch still belongs to its sender.
                messenger._response_finished(True, "Reply only for Rook")
                self.assertEqual(messenger.contact_histories[contact.contact_id], [])
                messenger.message_edit.setText("Moss's private message")
                messenger._send_message()
                request = send.call_args.args[0]
                self.assertEqual(len(request), 2)
                self.assertNotIn("Rook's private", json.dumps(request))
                # Contact selection cannot redirect a reply either.
                messenger._select_contact(1)
                messenger._response_finished(True, "Reply only for Moss")
                self.assertEqual(messenger.contact_histories[CONTACTS[1].contact_id], [])
            for owner, expected in (
                ("rook", ["Rook's private message", "Reply only for Rook"]),
                ("moss", ["Moss's private message", "Reply only for Moss"]),
            ):
                account.active_profile_id = owner
                messenger._select_contact(0)
                self.assertEqual(
                    [item["content"] for item in messenger.contact_histories[contact.contact_id]],
                    expected,
                )
                reopened = MessengerApp(account, service)
                self.addCleanup(reopened.deleteLater)
                self.addCleanup(reopened.close)
                self.assertEqual(reopened.contact_histories, messenger.contact_histories)
                destination = Path(directory) / f"{owner}-export.json"
                config.export_messenger_histories(destination, profile_id=owner)
                exported = json.loads(destination.read_text())
                self.assertEqual(exported["profile_id"], owner)
                self.assertEqual(
                    [item["content"] for item in exported["conversations"][0]["messages"]],
                    expected,
                )
            with patch(
                "win7_2011.win7sim.apps.QMessageBox.question",
                return_value=QMessageBox.StandardButton.Yes,
            ):
                messenger._clear_history()
            self.assertEqual(config.load_messenger_history(contact.contact_id, "moss"), [])
            self.assertEqual(len(config.load_messenger_history(contact.contact_id, "rook")), 2)

    def test_legacy_preview_is_read_only_and_cancellation_keeps_active_chat_isolated(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.object(
            config, "MESSENGER_HISTORY", Path(directory)
        ):
            contact = CONTACTS[0]
            legacy = [
                {"role": "user", "content": "Private older <b>chat</b> 🦊"},
                {"role": "assistant", "content": "Older reply\nSecond line"},
            ]
            active = [{"role": "user", "content": "Current fursona's chat"}]
            config.save_messenger_history(contact.contact_id, legacy)
            config.save_messenger_history(contact.contact_id, active, "rook")
            root = Path(directory)
            originals = {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}
            service = ConnectionSimulator()
            messenger = MessengerApp(sample_account(), service)
            self.addCleanup(service.deleteLater)
            self.addCleanup(service.stop)
            self.addCleanup(messenger.deleteLater)
            self.addCleanup(messenger.close)
            for dismissal in ("cancel", "escape", "close"):
                captured = {}

                def dismiss_preview() -> None:
                    dialog = QApplication.activeModalWidget()
                    captured["dialog_type"] = type(dialog)
                    captured["read_only"] = dialog.transcript.isReadOnly()
                    captured["text"] = dialog.transcript.toPlainText()
                    captured["notice"] = dialog.notice.text()
                    captured["title"] = dialog.windowTitle()
                    if dismissal == "cancel":
                        dialog.buttons.button(QDialogButtonBox.StandardButton.Cancel).click()
                    elif dismissal == "escape":
                        dialog.reject()  # QDialog's Escape behavior.
                    else:
                        dialog.close()

                QTimer.singleShot(0, dismiss_preview)
                with patch("win7_2011.win7sim.apps.QMessageBox.question") as confirm, patch.object(
                    messenger.client, "send_chat"
                ) as send:
                    messenger._assign_legacy_history()
                    confirm.assert_not_called()
                    send.assert_not_called()
                self.assertIs(captured["dialog_type"], LegacyChatPreviewDialog)
                self.assertTrue(captured["read_only"])
                self.assertIn("read-only", captured["title"])
                self.assertIn("not loaded", captured["notice"])
                self.assertIn("sent to AI", captured["notice"])
                self.assertIn("Unknown owner:\n" + legacy[0]["content"], captured["text"])
                self.assertIn(contact.display_name + ":\n" + legacy[1]["content"], captured["text"])
                self.assertEqual(messenger.contact_histories[contact.contact_id], active)
                self.assertNotIn("Private older", messenger.transcript.toPlainText())
                self.assertEqual(
                    {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()},
                    originals,
                )
            # The next outgoing request must use the current fursona's chat, not the preview.
            messenger.message_edit.setText("A new message")
            with patch.object(messenger, "_can_chat", return_value=True), patch.object(
                messenger.client, "send_chat"
            ) as send:
                messenger._send_message()
            outgoing = send.call_args.args[0]
            self.assertIn(active[0], outgoing)
            self.assertFalse(any("Private older" in m["content"] or "Older reply" in m["content"]
                                 for m in outgoing))

    def test_legacy_preview_cannot_confirm_after_switching_fursonas(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.object(
            config, "MESSENGER_HISTORY", Path(directory)
        ):
            contact_id = CONTACTS[0].contact_id
            config.save_messenger_history(contact_id, [])
            source = config._messenger_history_path(contact_id)
            original = source.read_bytes()
            account = sample_account()
            account.fursonas.append(FursonaProfile(
                fursona_name="Moss", species="wolf", pronouns="he/him",
                date_of_birth="1988-01-01", profile_id="moss",
            ))
            service = ConnectionSimulator()
            messenger = MessengerApp(account, service)
            self.addCleanup(service.deleteLater)
            self.addCleanup(service.stop)
            self.addCleanup(messenger.deleteLater)
            self.addCleanup(messenger.close)
            captured = {}

            def switch_and_continue() -> None:
                dialog = QApplication.activeModalWidget()
                captured["text"] = dialog.transcript.toPlainText()
                account.active_profile_id = "moss"
                dialog.buttons.button(QDialogButtonBox.StandardButton.Ok).click()

            QTimer.singleShot(0, switch_and_continue)
            with patch("win7_2011.win7sim.apps.QMessageBox.question") as confirm:
                messenger._assign_legacy_history()
                confirm.assert_not_called()
            self.assertIn("no messages", captured["text"])
            self.assertEqual(source.read_bytes(), original)
            self.assertFalse((Path(directory) / "Legacy").exists())
            self.assertEqual(config.load_messenger_history(contact_id, "rook"), [])
            self.assertEqual(config.load_messenger_history(contact_id, "moss"), [])

    def test_damaged_legacy_preview_fails_without_confirmation_or_file_changes(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.object(
            config, "MESSENGER_HISTORY", Path(directory)
        ):
            contact_id = CONTACTS[0].contact_id
            source = config._messenger_history_path(contact_id)
            service = ConnectionSimulator()
            messenger = MessengerApp(sample_account(), service)
            self.addCleanup(service.deleteLater)
            self.addCleanup(service.stop)
            self.addCleanup(messenger.deleteLater)
            self.addCleanup(messenger.close)
            malformed = (
                b"{ damaged", b"\xff",
                json.dumps({"version": 1, "contact_id": contact_id,
                            "messages": [{"role": "system", "content": "Bad"}]}).encode(),
                json.dumps({"version": 1, "contact_id": "wrong", "messages": []}).encode(),
            )
            for raw in malformed:
                with self.subTest(raw=raw):
                    source.write_bytes(raw)
                    with patch("win7_2011.win7sim.apps.LegacyChatPreviewDialog") as preview, patch(
                        "win7_2011.win7sim.apps.QMessageBox.question"
                    ) as confirm, patch(
                        "win7_2011.win7sim.apps.QMessageBox.warning"
                    ) as warning:
                        messenger._assign_legacy_history()
                        preview.assert_not_called()
                        confirm.assert_not_called()
                        self.assertIn("left unchanged", warning.call_args.args[2])
                    self.assertEqual(source.read_bytes(), raw)
                    self.assertEqual(list(Path(directory).rglob("*.json")), [source])
                    self.assertEqual(messenger.contact_histories[contact_id], [])
            owner_path = Path(directory) / "Legacy" / f"{contact_id}.owner.json"
            owner_path.parent.mkdir()
            owner_path.write_bytes(b"{ damaged ownership")
            with self.assertRaises(ValueError):
                config.preview_legacy_messenger_history(contact_id, "rook")
            self.assertEqual(owner_path.read_bytes(), b"{ damaged ownership")
            self.assertEqual(source.read_bytes(), malformed[-1])
            # A failed assignment may leave a claimed archive; damaged archives
            # remain read-only and must not become previewable by another fursona.
            owner_path.write_text(json.dumps({"profile_id": "rook"}))
            archive = owner_path.with_name(f"{contact_id}.json")
            archive.write_bytes(b"{ damaged archive")
            original_owner = owner_path.read_bytes()
            with self.assertRaises(ValueError):
                config.preview_legacy_messenger_history(contact_id, "rook")
            with self.assertRaisesRegex(ValueError, "available"):
                config.preview_legacy_messenger_history(contact_id, "moss")
            self.assertEqual(archive.read_bytes(), b"{ damaged archive")
            self.assertEqual(owner_path.read_bytes(), original_owner)
            self.assertEqual(source.read_bytes(), malformed[-1])

    def test_legacy_chats_require_explicit_owner_and_preserve_original_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.object(
            config, "MESSENGER_HISTORY", Path(directory)
        ):
            contact = CONTACTS[0]
            messages = [{"role": "user", "content": "Older private chat"}]
            config.save_messenger_history(contact.contact_id, messages)
            source = config._messenger_history_path(contact.contact_id)
            original = source.read_bytes()
            service = ConnectionSimulator()
            messenger = MessengerApp(sample_account(), service)
            self.addCleanup(service.deleteLater)
            self.addCleanup(service.stop)
            self.addCleanup(messenger.deleteLater)
            self.addCleanup(messenger.close)
            self.assertEqual(messenger.contact_histories[contact.contact_id], [])
            self.assertFalse(messenger.assign_legacy_button.isHidden())
            with patch(
                "win7_2011.win7sim.apps.LegacyChatPreviewDialog.exec",
                return_value=QDialog.DialogCode.Accepted,
            ), patch(
                "win7_2011.win7sim.apps.QMessageBox.question",
                return_value=QMessageBox.StandardButton.No,
            ):
                messenger._assign_legacy_history()
            self.assertEqual(source.read_bytes(), original)
            self.assertFalse((Path(directory) / "Legacy").exists())
            self.assertEqual(messenger.contact_histories[contact.contact_id], [])
            with patch(
                "win7_2011.win7sim.apps.LegacyChatPreviewDialog.exec",
                return_value=QDialog.DialogCode.Accepted,
            ), patch(
                "win7_2011.win7sim.apps.QMessageBox.question",
                return_value=QMessageBox.StandardButton.Yes,
            ):
                messenger._assign_legacy_history()
            self.assertEqual(messenger.contact_histories[contact.contact_id], messages)
            archive = Path(directory) / "Legacy" / f"{contact.contact_id}.json"
            self.assertEqual(archive.read_bytes(), original)
            self.assertFalse(source.exists())
            self.assertEqual(config.load_messenger_history(contact.contact_id, "moss"), [])
            for owner in ("rook", "moss"):
                with self.assertRaisesRegex(ValueError, "available"):
                    config.preview_legacy_messenger_history(contact.contact_id, owner)
            with self.assertRaisesRegex(ValueError, "another fursona"):
                config.assign_legacy_messenger_history(contact.contact_id, "moss")
            config.clear_messenger_history(contact.contact_id, "rook")
            self.assertEqual(archive.read_bytes(), original)
            self.assertFalse(config.legacy_messenger_history_available(contact.contact_id, "moss"))

    def test_legacy_assignment_failure_can_only_be_retried_by_its_owner(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.object(
            config, "MESSENGER_HISTORY", Path(directory)
        ):
            contact_id = CONTACTS[0].contact_id
            messages = [{"role": "assistant", "content": "Preserve me"}]
            config.save_messenger_history(contact_id, messages)
            original = config._messenger_history_path(contact_id).read_bytes()
            with patch.object(config, "save_messenger_history", side_effect=OSError("Disk full")):
                with self.assertRaisesRegex(OSError, "Disk full"):
                    config.assign_legacy_messenger_history(contact_id, "rook")
            self.assertTrue(config.legacy_messenger_history_available(contact_id, "rook"))
            self.assertFalse(config.legacy_messenger_history_available(contact_id, "moss"))
            self.assertEqual(config.preview_legacy_messenger_history(contact_id, "rook"), messages)
            with self.assertRaisesRegex(ValueError, "available"):
                config.preview_legacy_messenger_history(contact_id, "moss")
            with self.assertRaisesRegex(ValueError, "another fursona"):
                config.assign_legacy_messenger_history(contact_id, "moss")
            config.assign_legacy_messenger_history(contact_id, "rook")
            self.assertEqual(config.load_messenger_history(contact_id, "rook"), messages)
            archive = Path(directory) / "Legacy" / f"{contact_id}.json"
            self.assertEqual(archive.read_bytes(), original)

    def test_legacy_assignment_never_overwrites_existing_or_damaged_chats(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.object(
            config, "MESSENGER_HISTORY", Path(directory)
        ):
            contact_id = CONTACTS[0].contact_id
            legacy = [{"role": "user", "content": "Old"}]
            scoped = [{"role": "user", "content": "New"}]
            config.save_messenger_history(contact_id, legacy)
            config.save_messenger_history(contact_id, scoped, "rook")
            with self.assertRaisesRegex(ValueError, "not replaced"):
                config.assign_legacy_messenger_history(contact_id, "rook")
            self.assertEqual(config.load_messenger_history(contact_id), legacy)
            self.assertEqual(config.load_messenger_history(contact_id, "rook"), scoped)
            config.clear_messenger_history(contact_id, "rook")
            source = config._messenger_history_path(contact_id)
            for raw in (
                "{ damaged", json.dumps({"version": 1, "contact_id": contact_id,
                                         "messages": [{"role": "system", "content": "Bad"}]}),
                json.dumps({"version": 1, "contact_id": "wrong", "messages": []}),
            ):
                source.write_text(raw)
                with self.assertRaises(ValueError):
                    config.assign_legacy_messenger_history(contact_id, "rook")
                self.assertEqual(source.read_text(), raw)
                self.assertEqual(config.load_messenger_history(contact_id, "rook"), [])
            # Damaged ownership records also fail closed, never granting a second owner.
            owner_path = Path(directory) / "Legacy" / f"{contact_id}.owner.json"
            owner_path.parent.mkdir(parents=True, exist_ok=True)
            owner_path.write_text("{ damaged")
            with self.assertRaises(ValueError):
                config.assign_legacy_messenger_history(contact_id, "moss")
            self.assertEqual(owner_path.read_text(), "{ damaged")

    def test_scoped_files_validate_owner_and_ids_without_loading_legacy(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.object(
            config, "MESSENGER_HISTORY", Path(directory)
        ):
            contact_id = CONTACTS[0].contact_id
            config.save_messenger_history(contact_id, [], "rook")
            path = config._messenger_history_path(contact_id, "rook")
            raw = json.loads(path.read_text())
            raw["profile_id"] = "moss"
            path.write_text(json.dumps(raw))
            with self.assertRaisesRegex(ValueError, "invalid format"):
                config.load_messenger_history(contact_id, "rook")
            for profile_id in ("", "../outside", "a/b", "/absolute", "..", None):
                if profile_id is None:
                    continue  # None is reserved for explicit legacy tooling.
                with self.assertRaisesRegex(ValueError, "fursona ID"):
                    config.save_messenger_history(contact_id, [], profile_id)
            service = ConnectionSimulator()
            messenger = MessengerApp(UserAccount(), service)
            self.addCleanup(service.deleteLater)
            self.addCleanup(service.stop)
            self.addCleanup(messenger.deleteLater)
            self.addCleanup(messenger.close)
            self.assertFalse(messenger.send_button.isEnabled())
            self.assertFalse(messenger.clear_history_button.isEnabled())
            self.assertFalse(messenger.export_all_button.isEnabled())

    def test_export_one_or_all_retains_contacts_roles_order_and_unicode(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(config, "MESSENGER_HISTORY", root / "Messenger"):
                first, second = CONTACTS[:2]
                messages = [
                    {"role": "user", "content": "Hello 🦊\nSecond line"},
                    {"role": "assistant", "content": "Café <hello>"},
                    {"role": "user", "content": "Last message"},
                ]
                for contact in (first, second):
                    config.save_messenger_history(contact.contact_id, messages)
                originals = {path: path.read_bytes() for path in config.MESSENGER_HISTORY.iterdir()}
                destination = root / "chosen-backup.json"
                self.assertEqual(config.export_messenger_histories(destination, second.contact_id), 1)
                exported = json.loads(destination.read_text(encoding="utf-8"))["conversations"]
                self.assertEqual(len(exported), 1)
                self.assertEqual(exported[0]["contact_id"], second.contact_id)
                self.assertEqual(exported[0]["display_name"], second.display_name)
                self.assertEqual(exported[0]["online_name"], second.online_name)
                self.assertEqual(exported[0]["messages"], messages)
                self.assertEqual(config.export_messenger_histories(destination), 2)
                exported = json.loads(destination.read_text(encoding="utf-8"))["conversations"]
                self.assertEqual([chat["contact_id"] for chat in exported], [first.contact_id, second.contact_id])
                self.assertTrue(all(chat["messages"] == messages for chat in exported))
                self.assertEqual({path: path.read_bytes() for path in originals}, originals)

    def test_export_failure_preserves_sources_previous_backup_and_cleans_temporary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(config, "MESSENGER_HISTORY", root / "Messenger"):
                contact = CONTACTS[0]
                config.save_messenger_history(contact.contact_id, [{"role": "user", "content": "Keep"}])
                source = config.MESSENGER_HISTORY / f"{contact.contact_id}.json"
                original = source.read_bytes()
                destination = root / "backup.json"
                destination.write_text("previous backup", encoding="utf-8")
                with patch.object(Path, "replace", side_effect=PermissionError("Access denied")):
                    with self.assertRaises(PermissionError):
                        config.export_messenger_histories(destination)
                self.assertEqual(destination.read_text(), "previous backup")
                self.assertEqual(source.read_bytes(), original)
                self.assertEqual(list(root.glob(".messenger-export-*")), [])
                damaged = config.MESSENGER_HISTORY / f"{CONTACTS[1].contact_id}.json"
                damaged.write_text("{ damaged", encoding="utf-8")
                with self.assertRaisesRegex(ValueError, CONTACTS[1].display_name):
                    config.export_messenger_histories(destination)
                self.assertEqual(destination.read_text(), "previous backup")
                self.assertEqual(damaged.read_text(), "{ damaged")
                self.assertEqual(source.read_bytes(), original)

    def test_export_rejects_storage_destinations_and_empty_chats(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(config, "MESSENGER_HISTORY", root / "Messenger"), patch.object(
                config, "STORAGE_ROOT", root / "Storage"
            ):
                for destination in (config.MESSENGER_HISTORY / "backup.json", config.STORAGE_ROOT / "backup.json"):
                    with self.assertRaisesRegex(ValueError, "outside"):
                        config.export_messenger_histories(destination)
                destination = root / "backup.json"
                with self.assertRaisesRegex(ValueError, "no saved messages"):
                    config.export_messenger_histories(destination)
                self.assertFalse(destination.exists())
                with self.assertRaisesRegex(ValueError, "Unknown"):
                    config.export_messenger_histories(destination, "../bad-id")

    def test_export_buttons_work_offline_cancel_safely_and_report_errors(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(config, "MESSENGER_HISTORY", root / "Messenger"):
                contact = CONTACTS[0]
                messages = [{"role": "assistant", "content": "Saved reply"}]
                config.save_messenger_history(contact.contact_id, messages, "rook")
                service = ConnectionSimulator()
                messenger = MessengerApp(sample_account(), service)
                self.addCleanup(service.deleteLater)
                self.addCleanup(service.stop)
                self.addCleanup(messenger.deleteLater)
                self.addCleanup(messenger.close)
                service.begin_interruption(ServiceState.DISCONNECTED, 60_000)
                self.assertTrue(messenger.export_history_button.isEnabled())
                self.assertTrue(messenger.export_all_button.isEnabled())
                destination = root / "backup.json"
                with patch("win7_2011.win7sim.apps.QFileDialog.getSaveFileName", return_value=("", "")), patch(
                    "win7_2011.win7sim.apps.export_messenger_histories"
                ) as export:
                    messenger.export_history_button.click()
                    export.assert_not_called()
                with patch("win7_2011.win7sim.apps.QFileDialog.getSaveFileName", return_value=(str(destination), "")), patch(
                    "win7_2011.win7sim.apps.QMessageBox.information"
                ) as success:
                    messenger.export_history_button.click()
                    self.assertTrue(destination.is_file())
                    success.assert_called_once()
                    messenger.contact_list.setCurrentRow(-1)
                    self.assertFalse(messenger.export_history_button.isEnabled())
                    messenger.export_all_button.click()
                    self.assertEqual(success.call_count, 2)
                messenger.contact_list.setCurrentRow(0)
                for button in (messenger.export_history_button, messenger.export_all_button):
                    with patch("win7_2011.win7sim.apps.QFileDialog.getSaveFileName", return_value=(str(destination), "")), patch(
                        "win7_2011.win7sim.apps.export_messenger_histories", side_effect=PermissionError("Disk full")
                    ), patch("win7_2011.win7sim.apps.QMessageBox.warning") as warning:
                        button.click()
                        self.assertIn("Disk full", warning.call_args.args[2])
                        self.assertIn("not been changed or deleted", warning.call_args.args[2])
                    self.assertEqual(config.load_messenger_history(contact.contact_id, "rook"), messages)
                    self.assertEqual(messenger.contact_histories[contact.contact_id], messages)

    def test_shared_community_roster_has_200_stable_adult_profiles(self) -> None:
        ids = [contact.contact_id for contact in CONTACTS]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(CONTACTS), 234)
        self.assertEqual(sum(contact.circle == "close" for contact in CONTACTS), 84)
        self.assertEqual(sum(contact.circle == "community" for contact in CONTACTS), 150)
        self.assertTrue(all(contact.online_name for contact in CONTACTS))
        self.assertTrue(all(contact.bio and contact.interests for contact in CONTACTS))
        self.assertEqual(validate_community_contacts(), [])
        self.assertTrue(
            all(
                (contact.age_in_2011 >= 21 if contact.age_in_2011 is not None else contact.adult_confirmed)
                for contact in CONTACTS
            )
        )

    def test_simulated_interruptions_pause_background_work_and_stop_cleanly(self) -> None:
        service = ConnectionSimulator()
        states = []
        service.stateChanged.connect(lambda state, _text: states.append(state))
        self.assertTrue(service.chat_available)
        self.assertFalse(service.background_work_paused)
        service.begin_interruption(ServiceState.DISCONNECTED, 60_000)
        self.assertFalse(service.chat_available)
        self.assertTrue(service.background_work_paused)
        self.assertEqual(states[-1], ServiceState.DISCONNECTED)
        service.begin_interruption(ServiceState.SLOWDOWN, 60_000)
        self.assertTrue(service.chat_available)
        self.assertTrue(service.background_work_paused)
        self.assertEqual(states[-1], ServiceState.SLOWDOWN)
        service.stop()
        self.assertFalse(service._next_event_timer.isActive())
        self.assertFalse(service._restore_timer.isActive())
        service.deleteLater()


if __name__ == "__main__":
    unittest.main()
