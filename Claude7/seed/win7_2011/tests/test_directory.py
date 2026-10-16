"""Offscreen coverage of directory discovery and canonical profile selection."""

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from win7_2011.win7sim.apps import ProfileDirectoryApp
from win7_2011.win7sim.contacts import CONTACTS
from win7_2011.win7sim.identity import FursonaProfile, UserAccount


class DirectoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.qt_app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        profile = FursonaProfile("Rook", "red fox", "they/them", "1988-06-12")
        account = UserAccount(
            desktop_name="Test User",
            online_name="test_user",
            use_desktop_name_online=False,
            fursonas=[profile],
            active_profile_id=profile.profile_id,
        )
        self.directory = ProfileDirectoryApp(account)

    def tearDown(self) -> None:
        self.directory.close()
        self.directory.deleteLater()
        self.qt_app.processEvents()

    def result_ids(self) -> list[str]:
        return [
            self.directory.profile_list.item(row).data(Qt.ItemDataRole.UserRole)
            for row in range(self.directory.profile_list.count())
        ]

    def test_search_matches_both_names_case_insensitively(self) -> None:
        for query in ("  MORGAN  ", "NORTHBOUND", "draws", "river", "a"):
            with self.subTest(query=query):
                self.directory.search_input.setText(query)
                normalized = query.strip().casefold()
                self.assertEqual(self.result_ids(), [
                    contact.contact_id for contact in CONTACTS
                    if normalized in contact.display_name.casefold()
                    or normalized in contact.online_name.casefold()
                ])

    def test_filters_cover_canonical_values_and_combine_with_search(self) -> None:
        species_filter = self.directory.species_filter
        location_filter = self.directory.location_filter
        for combo, field in ((species_filter, "species"), (location_filter, "location")):
            expected_values = sorted({getattr(c, field) for c in CONTACTS}, key=str.casefold)
            self.assertEqual(
                [combo.itemData(i) for i in range(1, combo.count())], expected_values
            )
            for value in expected_values:
                combo.setCurrentIndex(combo.findData(value))
                self.assertEqual(self.result_ids(), [
                    c.contact_id for c in CONTACTS if getattr(c, field) == value
                ])
            combo.setCurrentIndex(0)
        contact = CONTACTS[-1]
        species_filter.setCurrentIndex(species_filter.findData(contact.species))
        location_filter.setCurrentIndex(location_filter.findData(contact.location))
        self.directory.search_input.setText(contact.display_name.split()[0])
        self.assertEqual(self.result_ids(), [
            c.contact_id for c in CONTACTS
            if c.species == contact.species and c.location == contact.location
            and contact.display_name.split()[0].casefold() in c.display_name.casefold()
        ])

    def test_filtered_row_displays_complete_canonical_profile(self) -> None:
        contact = CONTACTS[-1]
        self.directory.search_input.setText(contact.online_name)
        row = self.result_ids().index(contact.contact_id)
        self.directory.profile_list.setCurrentRow(row)
        self.assertEqual(self.directory.name.text(), contact.display_name)
        self.assertEqual(self.directory.species.text(), contact.species)
        self.assertEqual(self.directory.location.text(), contact.location)
        self.assertEqual(self.directory.pronouns.text(), contact.pronouns)
        self.assertIn(contact.date_of_birth, self.directory.birth_date.text())
        for text in (
            contact.bio, ", ".join(contact.interests), contact.preferences,
            contact.relationship_history,
        ):
            self.assertIn(text, self.directory.bio.text())
        self.assertIn(contact.online_name, self.directory.avatar.toolTip())
        self.assertIn(contact.circle.title(), self.directory.avatar.toolTip())
        if contact.icon_path:
            self.assertFalse(self.directory.avatar.pixmap().isNull())
        self.assertEqual(
            self.directory.online_name.text(), f"Stable community ID: {contact.contact_id}"
        )
        self.directory.search_input.clear()
        self.assertEqual(
            self.directory.profile_list.currentItem().data(Qt.ItemDataRole.UserRole),
            contact.contact_id,
        )

    def test_empty_results_clear_details_and_reset_restores_roster(self) -> None:
        original_ids = [c.contact_id for c in CONTACTS]
        contact = CONTACTS[-1]
        self.directory.species_filter.setCurrentIndex(
            self.directory.species_filter.findData(contact.species)
        )
        self.directory.location_filter.setCurrentIndex(
            self.directory.location_filter.findData(contact.location)
        )
        self.directory.search_input.setText("no-such-community-member")
        self.assertEqual(self.result_ids(), [])
        self.assertIn("No matching profiles", self.directory.results_label.text())
        self.assertTrue(self.directory.detail_panel.isHidden())
        self.assertEqual(self.directory.name.text(), "")
        self.assertEqual(self.directory.bio.text(), "")
        self.directory.reset_filters_button.click()
        self.assertEqual(self.result_ids(), original_ids)
        self.assertFalse(self.directory.detail_panel.isHidden())
        self.assertEqual(self.directory.name.text(), CONTACTS[0].display_name)
        self.assertEqual(self.directory.results_label.text(), f"{len(CONTACTS)} of {len(CONTACTS)} profiles")


if __name__ == "__main__":
    unittest.main()
