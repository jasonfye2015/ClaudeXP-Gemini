"""The crop pictures for the South Fields (UPGRADE_PLAN_14.md), carried inside the one file like the other packs.

    python tools/cropsheet.py --gather   cut the chosen cells from the kept sets in Local Storage into src/art/crops.png
                                         (+ src/art/crops.json, the frame index)
    python tools/cropsheet.py            write src/js/35b-croppack.js from src/art/crops.png and crops.json
    python tools/cropsheet.py --check    say whether src/js/35b-croppack.js matches src/art/ (exit 1 if not)

The sets (each kept whole, with its licence, in Local Storage\\Farm - Sprites):
  [LPC] Crops v2.1 - bluecarrot16, Daniel Eddeland, Joshua Taylor, Richard Kettering; commissioned by castelonia.
    CC-BY-SA 3.0+ or GPL 3.0+. https://opengameart.org/content/lpc-crops (32x64 cells: rows 0-3 the growth, row 4
    after the picking; three blocks of five rows, a crop a column)
  Farming Crops 16x16 - josehzz. CC0. https://opengameart.org/content/farming-crops-16x16 (two crops a row, six
    columns each: a portrait, then ripe to seed)
Every frame here is a 32x64 cell, the plant standing on its foot at the bottom; josehzz's are doubled to 32x32.
"""
import base64
import io
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
ART = HERE / "src" / "art"
PNG = ART / "crops.png"
INDEX = ART / "crops.json"
OUT = HERE / "src" / "js" / "35b-croppack.js"
TIMELINE = next((p for p in [Path(os.environ.get("CLAUDE_TIMELINE", "")), HERE.parent.parent, HERE.parent / "Claude Timeline"] if (p / "Local Storage").is_dir()), HERE.parent.parent)
SETS = TIMELINE / "Local Storage" / "Farm - Sprites"
LPC = SETS / "LPC Crops v2.1" / "crops-v2" / "crops.png"
JOSE = SETS / "josehzz Farming Crops 16x16" / "Crop_Spritesheet.png"
CW, CH, COLS = 32, 64, 16

# crop id -> ("lpc", block, column) or ("jose", row, side 0|1)
CHOSEN = {
    "potato": ("lpc", 0, 0), "sweetpotato": ("lpc", 0, 3), "carrot": ("lpc", 0, 6), "parsnip": ("lpc", 0, 7), "radish": ("lpc", 0, 8),
    "beet": ("lpc", 0, 9), "turnip": ("lpc", 0, 10), "garlic": ("lpc", 0, 12), "onion": ("lpc", 0, 13), "pepper": ("lpc", 0, 19),
    "chili": ("lpc", 0, 22), "watermelon": ("lpc", 0, 23), "melon": ("lpc", 0, 25), "pumpkin": ("lpc", 0, 27), "squash": ("lpc", 0, 29),
    "corn": ("lpc", 0, 30),
    "asparagus": ("lpc", 1, 0), "rhubarb": ("lpc", 1, 1), "lettuce": ("lpc", 1, 2), "kale": ("lpc", 1, 4), "redcabbage": ("lpc", 1, 5),
    "cabbage": ("lpc", 1, 6), "celery": ("lpc", 1, 7), "cauliflower": ("lpc", 1, 11), "broccoli": ("lpc", 1, 12), "artichoke": ("lpc", 1, 13),
    "leek": ("lpc", 1, 14), "eggplant": ("lpc", 1, 16), "zucchini": ("lpc", 1, 17), "cucumber": ("lpc", 1, 19), "strawberry": ("lpc", 1, 20),
    "blackberry": ("lpc", 1, 21), "raspberry": ("lpc", 1, 22), "blueberry": ("lpc", 1, 23), "grapes": ("lpc", 1, 24), "tomato": ("lpc", 1, 27),
    "peas": ("lpc", 1, 29), "hops": ("lpc", 1, 30), "beans": ("lpc", 1, 31),
    "coffee": ("lpc", 2, 29), "pineapple": ("lpc", 2, 30), "kiwi": ("lpc", 2, 31),
    "rose": ("jose", 0, 1), "tulip": ("jose", 1, 1), "barley": ("jose", 4, 1), "wheat": ("jose", 5, 0), "sunflower": ("jose", 9, 1),
}
CREDITS = ('"[LPC] Crops" by bluecarrot16, Daniel Eddeland (daneeklu), Joshua Taylor, Richard Kettering (Jetrel); commissioned by castelonia. '
           'CC-BY-SA 3.0+ or GPL 3.0+. https://opengameart.org/content/lpc-crops  |  "Farming Crops 16x16" by josehzz, CC0, '
           'https://opengameart.org/content/farming-crops-16x16')


def gather():
    from PIL import Image
    lpc, jose = Image.open(LPC).convert("RGBA"), Image.open(JOSE).convert("RGBA")
    frames, index = [], {}

    def cell_lpc(block, col, row):
        return lpc.crop((col * CW, (block * 5 + row) * CH, col * CW + CW, (block * 5 + row) * CH + CH))

    def cell_jose(row, side, col):                                         # col 1 is ripe, 5 the seed
        small = jose.crop(((side * 6 + col) * 16, row * 16, (side * 6 + col) * 16 + 16, row * 16 + 16)).resize((32, 32), Image.NEAREST)
        out = Image.new("RGBA", (CW, CH), (0, 0, 0, 0)); out.alpha_composite(small, (0, CH - 32)); return out

    def put(im):
        frames.append(im); return len(frames) - 1
    index["sown"] = put(cell_lpc(0, 0, 4))                               # (a mound of turned earth: every crop, the day it's sown)
    for crop, (kind, a, b) in CHOSEN.items():
        if kind == "lpc":
            index[crop] = {"s": [put(cell_lpc(a, b, r)) for r in range(4)], "after": put(cell_lpc(a, b, 4))}
        else:
            s = [put(cell_jose(a, b, c)) for c in (4, 3, 2, 1)]
            index[crop] = {"s": s, "after": s[1]}
    rows = (len(frames) + COLS - 1) // COLS
    sheet = Image.new("RGBA", (COLS * CW, rows * CH), (0, 0, 0, 0))
    for i, im in enumerate(frames):
        sheet.alpha_composite(im, ((i % COLS) * CW, (i // COLS) * CH))
    ART.mkdir(parents=True, exist_ok=True)
    sheet.save(PNG, optimize=True)
    INDEX.write_text(json.dumps({"cell": [CW, CH], "cols": COLS, "frames": index}, indent=1, sort_keys=True), encoding="utf-8")
    print(f"gathered {len(frames)} frames, {len(CHOSEN)} crops -> {PNG.name} ({PNG.stat().st_size // 1024} KB)")


def build_text():
    data = json.loads(INDEX.read_text(encoding="utf-8"))
    atlas = "data:image/png;base64," + base64.b64encode(PNG.read_bytes()).decode("ascii")
    return ('"use strict";\n// GENERATED by tools/cropsheet.py from src/art/crops.png and crops.json - do not edit. The South Fields\' crops\n'
            '// (UPGRADE_PLAN_14.md): every frame a 32x64 cell; frames.<crop>.s the four stages, .after the plant once picked, sown the\n'
            '// turned earth. 36c-cropart.js decodes the atlas and lays the frames into the looks.\n'
            f"CM.cropPack = {{ credits: {json.dumps(CREDITS)}, cell: {json.dumps(data['cell'])}, cols: {data['cols']}, frames: {json.dumps(data['frames'], sort_keys=True)},\n"
            f"  atlas: {json.dumps(atlas)} }};\n")


def main(argv):
    if "--gather" in argv:
        gather()
    text = build_text()
    if "--check" in argv:
        ok = OUT.exists() and OUT.read_text(encoding="utf-8") == text
        print("35b-croppack.js is up to date" if ok else "35b-croppack.js is out of date: run python tools/cropsheet.py")
        return 0 if ok else 1
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT.name} ({len(text) // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
