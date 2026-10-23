"""Builds Kithylin AI's gallery: copies "Kithylin's Art" into kithylinai/Art/, makes thumbnails once, and writes
Art/index.json for the gallery to read. The art is finished work that doesn't change, so this is run once (and
again only to pick up a new folder).

    Python\\python.exe ClaudeApps\\kithylinai\\build_art.py [SOURCE]

SOURCE defaults to Local Storage/Misc Personal Image Folders/AI Kithy. Pictures (jpg, png, webp, gif) get a
thumbnail in Art/.thumbs/<folder>/<name>.jpg; videos (mp4) are listed and open in the computer's player.
Any text files kept with the pictures (the prompts they were made from) come along too, unlisted.
"""
import json
import os
import shutil
import sys
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

HERE = Path(__file__).resolve().parent
ART = HERE / "Art"
THUMBS = ART / ".thumbs"
INDEX = ART / "index.json"
DEFAULT_SOURCE = HERE.parents[1] / "Local Storage" / "Misc Personal Image Folders" / "AI Kithy"
PICTURES = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}
VIDEOS = {".mp4", ".webm", ".mov", ".m4v"}
THUMB = 360


def copy_tree(src, dst):
    copied = 0
    for root, dirs, files in os.walk(src):
        dirs[:] = sorted(d for d in dirs if not d.startswith("."))
        rel = Path(root).relative_to(src)
        (dst / rel).mkdir(parents=True, exist_ok=True)
        for name in files:
            s, d = Path(root) / name, dst / rel / name
            if not d.exists() or d.stat().st_size != s.stat().st_size:
                shutil.copy2(s, d)
                copied += 1
    return copied


def main():
    from PySide6.QtCore import QSize, Qt
    from PySide6.QtGui import QGuiApplication, QImageReader
    QGuiApplication(sys.argv)

    src = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SOURCE
    if not src.is_dir():
        sys.exit(f"No art folder at {src}")
    started = time.time()
    print(f"copying {src} -> {ART}", flush=True)
    print(f"  {copy_tree(src, ART)} files copied", flush=True)

    folders, made = [], 0
    for folder in sorted(p for p in ART.iterdir() if p.is_dir() and not p.name.startswith(".")):
        items = []
        for f in sorted(folder.iterdir(), key=lambda p: p.name.lower()):
            ext = f.suffix.lower()
            if ext in PICTURES:
                thumb = THUMBS / folder.name / (f.stem + ".jpg")
                reader = QImageReader(str(f))
                reader.setAutoTransform(True)
                size = reader.size()
                w, h = size.width(), size.height()
                if not thumb.exists():
                    thumb.parent.mkdir(parents=True, exist_ok=True)
                    if w > 0 and h > 0:
                        reader.setScaledSize(QSize(w, h).scaled(THUMB, THUMB, Qt.KeepAspectRatio))
                    img = reader.read()
                    if img.isNull():
                        print(f"  couldn't read {f}", flush=True)
                        continue
                    img.save(str(thumb), "JPEG", 86)
                    made += 1
                items.append({"file": f.name, "kind": "image", "w": w, "h": h})
            elif ext in VIDEOS:
                items.append({"file": f.name, "kind": "video", "size": f.stat().st_size})
        if items:
            cover = next((i["file"] for i in items if i["kind"] == "image"), "")
            folders.append({"name": folder.name, "count": len(items), "cover": cover,
                            "pictures": sum(1 for i in items if i["kind"] == "image"),
                            "videos": sum(1 for i in items if i["kind"] == "video"), "items": items})
        print(f"  {folder.name}: {len(items)} items", flush=True)
    INDEX.write_text(json.dumps({"built": time.strftime("%Y-%m-%d %H:%M"), "thumb": THUMB, "folders": folders},
                                indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{len(folders)} folders, {sum(f['count'] for f in folders)} items, {made} new thumbnails, "
          f"{time.time() - started:.0f}s", flush=True)


if __name__ == "__main__":
    main()
