"""Bring Claude and Magic's art across: its figures (the rigged, animated CC0 bodies its tools/models.py bakes) and its
stone textures (ambientCG, CC0), into assets/. Run it again whenever Claude and Magic's figures change.

    python tools/import_cm.py            copy them in
    python tools/import_cm.py --check    say what would change, change nothing

The plants (trees, bushes, rocks, barrels, crates: static vertex-coloured meshes) come the same way from
35d-plants.js, into assets/figures/plants.bin and plants.json.

The figures come from Claude and Magic's src/js/35c-figures.js: the same binary, kept as it is (assets/figures/
figures.bin, raw deflate) with its manifest and its mapping of monsters to models (assets/figures/figures.json), so
engine/figures.py reads exactly what Claude and Magic draws. Nothing here reads the packs in Local Storage."""
import base64
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CM = ROOT.parent / "Claude and Magic"
FIG_JS = CM / "src" / "js" / "35c-figures.js"
PLANT_JS = CM / "src" / "js" / "35d-plants.js"
STONE = CM / "src" / "art" / "stone"
OUT_FIG = ROOT / "assets" / "figures"
OUT_TEX = ROOT / "assets" / "textures"


def figures(src=None, mapping_key="figures"):
    text = (src or FIG_JS).read_text(encoding="utf-8")
    grab = lambda key: re.search(rf"^  {key}: (.*),\n", text, re.M).group(1)   # noqa: E731
    manifest = json.loads(grab("manifest"))
    mapping = json.loads(grab(mapping_key)) if mapping_key else {}
    credits = json.loads(grab("credits"))
    data = base64.b64decode(json.loads(grab("data")))
    meta = {"credits": credits, "manifest": manifest, mapping_key or "figures": mapping,
            "_": "Imported from Claude and Magic by tools/import_cm.py - do not edit; figures.bin is raw deflate."}
    return data, json.dumps(meta, separators=(",", ":"))


def main():
    check = "--check" in sys.argv
    changed = []
    data, meta = figures()
    OUT_FIG.mkdir(parents=True, exist_ok=True)
    pdata, pmeta = figures(PLANT_JS, None)
    for path, blob in ((OUT_FIG / "figures.bin", data), (OUT_FIG / "figures.json", meta.encode()),
                       (OUT_FIG / "plants.bin", pdata), (OUT_FIG / "plants.json", pmeta.encode())):
        if not path.exists() or path.read_bytes() != blob:
            changed.append(path.name)
            if not check:
                path.write_bytes(blob)
    OUT_TEX.mkdir(parents=True, exist_ok=True)
    for f in sorted(STONE.iterdir()):
        if f.suffix.lower() not in (".jpg", ".png"):
            continue
        dest = OUT_TEX / f.name
        if not dest.exists() or dest.read_bytes() != f.read_bytes():
            changed.append(f.name)
            if not check:
                shutil.copyfile(f, dest)
    print(("would change: " if check else "changed: ") + (", ".join(changed) or "nothing"))
    return 1 if (check and changed) else 0


if __name__ == "__main__":
    sys.exit(main())
