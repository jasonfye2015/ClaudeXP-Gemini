import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from win7_2011.win7sim import config
from win7_2011.win7sim.apps import MessengerApp, ProfileDirectoryApp
from win7_2011.win7sim.close_histories import CLOSE_HISTORIES
from win7_2011.win7sim.contacts import (
    CONTACTS,
    messenger_system_prompt,
    relationship_for,
    validate_close_histories,
)
from win7_2011.win7sim.identity import FursonaProfile, UserAccount
from win7_2011.win7sim.service import ConnectionSimulator


def account_with_two_fursonas() -> UserAccount:
    profiles = [
        FursonaProfile("Rook", "red fox", "they/them", "1988-06-12", profile_id="rook"),
        FursonaProfile("Moss", "otter", "she/her", "1985-03-09", profile_id="moss"),
    ]
    return UserAccount(
        desktop_name="Desktop Login",
        online_name="shared_handle",
        use_desktop_name_online=False,
        fursonas=profiles,
        active_profile_id="rook",
    )


class RelationshipTests(unittest.TestCase):
    def test_all_fifty_close_contacts_have_distinct_complete_histories(self) -> None:
        account = account_with_two_fursonas()
        close = [contact for contact in CONTACTS if contact.circle == "close" and not contact.source_profile]
        self.assertEqual(len(close), 50)
        self.assertEqual(validate_close_histories(), [])
        self.assertEqual(set(CLOSE_HISTORIES), {contact.contact_id for contact in close})
        contexts = [relationship_for(contact, account.active_profile) for contact in close]
        self.assertEqual(len({context.shared_history for context in contexts}), 50)
        self.assertEqual(len({context.boundaries for context in contexts}), 50)
        for contact, context in zip(close, contexts):
            with self.subTest(contact=contact.contact_id):
                self.assertEqual(context.contact_id, contact.contact_id)
                self.assertEqual(context.profile_id, "rook")
                self.assertTrue(context.shared_history and context.boundaries)
                seed = CLOSE_HISTORIES[contact.contact_id]
                self.assertEqual(len(set(seed.memories)), 2)
                prompt = messenger_system_prompt(contact, account)
                self.assertIn(context.as_text(), prompt)
                self.assertIn("established platonic friends, not strangers", prompt)

    def test_histories_survive_reload_and_are_bound_to_each_active_fursona(self) -> None:
        account = account_with_two_fursonas()
        for contact in CONTACTS[:50]:
            with self.subTest(contact=contact.contact_id):
                original = relationship_for(contact, account.active_profile)
                restored = UserAccount.from_dict(account.to_dict())
                self.assertEqual(original, relationship_for(contact, restored.active_profile))
                restored.active_profile_id = "moss"
                other = relationship_for(contact, restored.active_profile)
                self.assertEqual(other.profile_id, "moss")
                self.assertEqual(other.player_name, "Moss")
                self.assertNotEqual(original, other)
                prompt = messenger_system_prompt(contact, restored)
                self.assertIn("Moss; species: otter; pronouns: she/her", prompt)
                self.assertNotIn("Rook", prompt)
                self.assertNotIn("red fox; pronouns: they/them", prompt)

    def test_community_profiles_do_not_gain_private_friendship_memories(self) -> None:
        account = account_with_two_fursonas()
        for contact in CONTACTS[50:200]:
            with self.subTest(contact=contact.contact_id):
                self.assertIsNone(relationship_for(contact, account.active_profile))
                self.assertNotIn(contact.contact_id, CLOSE_HISTORIES)
                prompt = messenger_system_prompt(contact, account)
                self.assertIn("No established shared history", prompt)
                self.assertNotIn("fictional shared backstory", prompt)
                self.assertIn(contact.relationship_history, prompt)

    def test_missing_active_fursona_never_invents_one_from_login_name(self) -> None:
        account = account_with_two_fursonas()
        account.active_profile_id = "missing"
        self.assertIsNone(account.active_profile)
        self.assertIsNone(relationship_for(CONTACTS[0], account.active_profile))
        prompt = messenger_system_prompt(CONTACTS[0], account)
        self.assertIn("No active player fursona is available", prompt)
        self.assertNotIn("Friendship with Desktop Login", prompt)
        self.assertNotIn("Friendship with Rook", prompt)


class MessengerRelationshipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.qt_app = QApplication.instance() or QApplication([])

    def test_first_and_following_messages_include_active_relationship_context(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(config, "MESSENGER_HISTORY", Path(directory)):
                account = account_with_two_fursonas()
                service = ConnectionSimulator()
                messenger = MessengerApp(account, service)
                directory_app = ProfileDirectoryApp(account)
                try:
                    messenger._can_chat = lambda: True
                    with patch.object(messenger.client, "send_chat") as send:
                        for index in (0, 49, 50):
                            messenger.contact_list.setCurrentRow(index)
                            contact = CONTACTS[index]
                            relationship = relationship_for(contact, account.active_profile)
                            if relationship:
                                self.assertEqual(
                                    messenger.relationship_details.text(), relationship.as_text()
                                )
                                # The public directory remains a biography, not a private memory dump.
                                directory_app.profile_list.setCurrentRow(index)
                                self.assertNotIn(
                                    relationship.shared_history, directory_app.bio.text()
                                )
                            else:
                                self.assertIn(
                                    "No established friendship", messenger.relationship_details.text()
                                )
                            for text in ("Hi, how are you?", "Thanks for listening."):
                                messenger.message_edit.setText(text)
                                messenger._send_message()
                                messages = send.call_args.args[0]
                                self.assertEqual(messages[0], {
                                    "role": "system",
                                    "content": messenger_system_prompt(contact, account),
                                })
                                self.assertEqual(messages[-1], {"role": "user", "content": text})
                    # Reopening with another selected fursona resolves its own context.
                    account.active_profile_id = "moss"
                    messenger._select_contact(0)
                    self.assertIn("Friendship with Moss", messenger.relationship_details.text())
                    self.assertNotIn("Friendship with Rook", messenger.relationship_details.text())
                    with patch.object(messenger.client, "send_chat") as send:
                        messenger.message_edit.setText("Hello again.")
                        messenger._send_message()
                        prompt = send.call_args.args[0][0]["content"]
                        self.assertIn("Friendship with Moss", prompt)
                        self.assertNotIn("Friendship with Rook", prompt)
                        messages = send.call_args.args[0]
                        self.assertEqual(len(messages), 2)
                        self.assertNotIn("Thanks for listening.", str(messages))
                finally:
                    directory_app.close()
                    messenger.close()
                    directory_app.deleteLater()
                    messenger.deleteLater()
                    service.stop()
                    service.deleteLater()
                    self.qt_app.processEvents()


if __name__ == "__main__":
    unittest.main()
