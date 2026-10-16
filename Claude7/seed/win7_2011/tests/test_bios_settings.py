import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from win7_2011.win7sim import config


class BiosSettingsRecoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.primary = Path(self.directory.name) / "bios.json"
        self.backup = self.primary.with_name("bios.backup.json")
        patcher = patch.object(config, "BIOS_SETTINGS_FILE", self.primary)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.settings = {"advanced": [0, 0, 0, 1, 0], "colors": [2]}

    def test_successful_saves_refresh_backup_from_valid_choices(self) -> None:
        config.save_bios_settings(self.settings)
        self.assertEqual(config.load_bios_settings_backup(), self.settings)
        self.assertEqual(self.primary.read_bytes(), self.backup.read_bytes())
        config.save_bios_settings({"colors": [1]})
        self.assertEqual(config.load_bios_settings_backup(), {"colors": [1]})
        self.assertFalse(list(self.primary.parent.glob("*.tmp")))

    def test_invalid_save_leaves_both_files_unchanged(self) -> None:
        config.save_bios_settings(self.settings)
        original = self.primary.read_bytes()
        for invalid in ([], {"colors": [True]}, {"colors": [-1]}):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                config.save_bios_settings(invalid)
            self.assertEqual(self.primary.read_bytes(), original)
            self.assertEqual(self.backup.read_bytes(), original)

    def test_primary_write_failure_keeps_known_good_copy(self) -> None:
        config.save_bios_settings(self.settings)
        original = self.backup.read_bytes()
        with (
            patch.object(Path, "replace", side_effect=PermissionError("denied")),
            self.assertRaises(PermissionError),
        ):
            config.save_bios_settings({"colors": [1]})
        self.assertEqual(self.primary.read_bytes(), original)
        self.assertEqual(self.backup.read_bytes(), original)
        self.assertFalse(list(self.primary.parent.glob("*.tmp")))

    def test_backup_write_failure_is_explicit_and_keeps_old_backup(self) -> None:
        config.save_bios_settings(self.settings)
        original = self.backup.read_bytes()
        write = config._atomic_write_private_json

        def fail_backup(path, serialized):
            if path == self.backup:
                raise PermissionError("backup denied")
            write(path, serialized)

        with (
            patch.object(config, "_atomic_write_private_json", side_effect=fail_backup),
            self.assertRaises(PermissionError),
        ):
            config.save_bios_settings({"colors": [1]})
        self.assertEqual(config.load_bios_settings(), {"colors": [1]})
        self.assertEqual(self.backup.read_bytes(), original)

    def test_loading_damaged_primary_never_uses_backup_automatically(self) -> None:
        config.save_bios_settings(self.settings)
        damaged = b"\xff{broken"
        self.primary.write_bytes(damaged)
        with self.assertRaises(ValueError):
            config.load_bios_settings()
        self.assertEqual(self.primary.read_bytes(), damaged)
        self.assertEqual(config.load_bios_settings_backup(), self.settings)
        self.assertFalse(list(self.primary.parent.glob("bios.damaged-*")))

    def test_restore_preserves_exact_bytes_and_keeps_backup(self) -> None:
        config.save_bios_settings(self.settings)
        backup_bytes = self.backup.read_bytes()
        archives = []
        for damaged in (b"\xff{broken", b"another damaged file"):
            self.primary.write_bytes(damaged)
            archive = config.restore_bios_settings(self.settings)
            archives.append(archive)
            self.assertEqual(archive.read_bytes(), damaged)
            self.assertEqual(config.load_bios_settings(), self.settings)
            self.assertEqual(self.backup.read_bytes(), backup_bytes)
        self.assertNotEqual(*archives)
        self.assertEqual(archives[0].read_bytes(), b"\xff{broken")

    def test_missing_corrupt_or_changed_backup_never_touches_original(self) -> None:
        damaged = b"{broken"
        self.primary.write_bytes(damaged)
        for contents in (None, "{broken", "[]", '{"colors": [true]}', "{}"):
            with self.subTest(contents=contents):
                if contents is not None:
                    self.backup.write_text(contents, encoding="utf-8")
                with self.assertRaises((OSError, ValueError)):
                    config.restore_bios_settings(self.settings)
                self.assertEqual(self.primary.read_bytes(), damaged)
                self.assertFalse(list(self.primary.parent.glob("bios.damaged-*")))

    def test_archive_failure_leaves_original_and_backup_unchanged(self) -> None:
        config.save_bios_settings(self.settings)
        self.primary.write_bytes(b"{broken")
        backup = self.backup.read_bytes()
        with (
            patch.object(config.tempfile, "mkstemp", side_effect=PermissionError("denied")),
            self.assertRaises(PermissionError),
        ):
            config.restore_bios_settings(self.settings)
        self.assertEqual(self.primary.read_bytes(), b"{broken")
        self.assertEqual(self.backup.read_bytes(), backup)

    def test_restore_write_failure_keeps_damaged_original_and_archive(self) -> None:
        config.save_bios_settings(self.settings)
        self.primary.write_bytes(b"{broken")
        with (
            patch.object(Path, "replace", side_effect=PermissionError("denied")),
            self.assertRaises(PermissionError),
        ):
            config.restore_bios_settings(self.settings)
        self.assertEqual(self.primary.read_bytes(), b"{broken")
        archives = list(self.primary.parent.glob("bios.damaged-*"))
        self.assertEqual(len(archives), 1)
        self.assertEqual(archives[0].read_bytes(), b"{broken")
        self.assertEqual(config.load_bios_settings_backup(), self.settings)

    def test_confirmed_manual_save_also_preserves_damaged_file(self) -> None:
        self.primary.write_bytes(b"{broken")
        config.save_bios_settings(self.settings, preserve_original=True)
        archive, = self.primary.parent.glob("bios.damaged-*")
        self.assertEqual(archive.read_bytes(), b"{broken")
        self.assertEqual(json.loads(self.backup.read_text()), self.settings)
