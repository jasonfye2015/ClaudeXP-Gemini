import tempfile
import unittest
from pathlib import Path

from win7_2011.win7sim.recent import RecentDocuments


class RecentDocumentsTests(unittest.TestCase):
    def test_access_order_is_persistent_deduplicated_and_limited_to_eight(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            history = root / ".recent-items.json"
            recent = RecentDocuments(history)
            files = [root / f"document-{index}.txt" for index in range(10)]
            for path in files:
                path.write_text("A document", encoding="utf-8")
                recent.record(path)
            recent.record(files[5])
            restored = RecentDocuments(history)
            self.assertEqual(restored.entries()[0], files[5])
            self.assertEqual(len(restored.entries()), 8)
            self.assertEqual(len(set(restored.entries())), 8)
            files[5].unlink()
            self.assertNotIn(files[5], restored.entries())

    def test_invalid_history_reports_an_error_without_overwriting_it(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "recent.json"
            path.write_text('{"invalid": true}', encoding="utf-8")
            recent = RecentDocuments(path)
            with self.assertRaises(ValueError):
                recent.entries()
            self.assertEqual(path.read_text(encoding="utf-8"), '{"invalid": true}')
