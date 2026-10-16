import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from win7_2011.win7sim.identity import (
    AccountStoreError,
    FursonaProfile,
    UserAccount,
    age_on_january_first,
    load_account,
    save_account,
    validate_account,
)


class IdentityTests(unittest.TestCase):
    def test_adult_rule_applies_for_the_entire_simulated_year(self) -> None:
        self.assertEqual(age_on_january_first(date(1989, 12, 31)), 21)
        self.assertEqual(age_on_january_first(date(1990, 1, 2)), 20)

    def test_validation_rejects_a_profile_under_21_in_2011(self) -> None:
        account = UserAccount(
            desktop_name="Sam",
            fursonas=[
                FursonaProfile(
                    fursona_name="Rook",
                    species="fox",
                    pronouns="they/them",
                    date_of_birth="1990-01-02",
                )
            ],
        )
        self.assertTrue(any("at least 21" in error for error in validate_account(account)))

    def test_shared_name_resolves_to_the_desktop_account(self) -> None:
        account = UserAccount(
            desktop_name="Sam",
            online_name="ignored while shared",
            use_desktop_name_online=True,
        )
        self.assertEqual(account.resolved_online_name, "Sam")

    def test_account_save_load_round_trip(self) -> None:
        account = UserAccount(
            desktop_name="Sam",
            online_name="sam_online",
            use_desktop_name_online=False,
            fursonas=[
                FursonaProfile(
                    fursona_name="Rook",
                    species="fox",
                    pronouns="they/them",
                    date_of_birth="1989-12-31",
                    bio="A test profile.",
                )
            ],
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "System" / "account.json"
            save_account(account, file_path)
            loaded = load_account(file_path)

        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertEqual(loaded.desktop_name, "Sam")
        self.assertEqual(loaded.resolved_online_name, "sam_online")
        self.assertEqual(loaded.fursonas[0].fursona_name, "Rook")
        self.assertEqual(loaded.fursonas[0].date_of_birth, "1989-12-31")

    def test_unknown_schema_is_not_silently_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "account.json"
            file_path.write_text(json.dumps({"schema_version": 999}), encoding="utf-8")
            with self.assertRaises(AccountStoreError):
                load_account(file_path)
            self.assertEqual(json.loads(file_path.read_text())["schema_version"], 999)


if __name__ == "__main__":
    unittest.main()
