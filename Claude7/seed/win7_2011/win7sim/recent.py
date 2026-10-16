from __future__ import annotations

import json
from pathlib import Path


class RecentDocuments:
    """Remember explicit document accesses, newest first, within resettable user data."""

    def __init__(self, history_file: Path) -> None:
        self.history_file = history_file

    def entries(self) -> list[Path]:
        if not self.history_file.exists():
            return []
        raw = json.loads(self.history_file.read_text(encoding="utf-8"))
        if not isinstance(raw, list) or any(not isinstance(item, str) for item in raw):
            raise ValueError("Recent document history must be a list of file paths.")
        return [Path(item) for item in raw[:8] if Path(item).is_file()]

    def record(self, path: Path) -> None:
        path = path.resolve()
        entries = [path, *(item for item in self.entries() if item != path)][:8]
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.history_file.with_suffix(".tmp")
        try:
            temporary.write_text(
                json.dumps([str(item) for item in entries], indent=2) + "\n",
                encoding="utf-8",
            )
            temporary.replace(self.history_file)
        finally:
            temporary.unlink(missing_ok=True)
