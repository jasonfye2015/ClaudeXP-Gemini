"""Pictures made here from Claude and Magic's own (assets/cm): the cold brazier - its lit brazier with the fire taken
out and a few dark coals left in the bowl - for the brazier trial (game/features.py).

    python tools/make_art.py"""
from pathlib import Path

from PIL import Image

CM = Path(__file__).resolve().parents[1] / "assets" / "cm"


def cold_brazier():
    im = Image.open(CM / "brazier.png").convert("RGBA")
    px = im.load()
    w, h = im.size
    rim = None
    for y in range(h):                                     # (the bowl's rim: the first dark row under the fire)
        for x in range(w):
            r, g, b, a = px[x, y]
            if a > 100 and r < 90 and g < 90 and b < 90 and rim is None:
                rim = y
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            fire = r > 150 and g > 60 and b < 120 and r > b + 60
            if a and (fire or (rim is not None and y < rim)):
                px[x, y] = (0, 0, 0, 0)
    import random
    rng = random.Random(3)
    if rim is not None:                                    # (coals, cold)
        for _ in range(int(w * 0.6)):
            x = rng.randint(int(w * 0.25), int(w * 0.75))
            y = rim + rng.randint(-2, 2)
            if 0 <= y < h:
                c = rng.randint(28, 52)
                px[x, y] = (c, c - 6, c - 10, 255)
    im.save(CM / "nx.brazier_cold.png")


if __name__ == "__main__":
    cold_brazier()
    print("made", CM / "nx.brazier_cold.png")
