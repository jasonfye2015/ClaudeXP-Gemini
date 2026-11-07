"""Pictures made here (assets/cm, nx.*): the cold brazier - Claude and Magic's lit brazier with the fire taken out and
a few dark coals left in the bowl - for the brazier trial; and the traps' own, drawn from nothing: the spike plate
(a worn iron plate pierced with holes), the spikes that spring from it, the dart plate (a flagstone a shade proud of
the floor, a rune on it) and the fire vent (a grate over a red throat) - game/features.py.

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


def _noise(rng, im, amount):
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a:
                k = rng.randint(-amount, amount)
                px[x, y] = (max(0, min(255, r + k)), max(0, min(255, g + k)), max(0, min(255, b + k)), a)


def traps():
    import random
    from PIL import ImageDraw
    rng = random.Random(7)
    S = 128
    # the spike plate: iron, riveted, nine holes
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((6, 6, S - 6, S - 6), 10, fill=(70, 66, 62, 255), outline=(34, 30, 28, 255), width=5)
    d.rounded_rectangle((16, 16, S - 16, S - 16), 6, outline=(92, 86, 80, 255), width=2)
    for i in range(3):
        for j in range(3):
            cx, cy = 34 + i * 30, 34 + j * 30
            d.ellipse((cx - 7, cy - 7, cx + 7, cy + 7), fill=(14, 12, 12, 255))
            d.ellipse((cx - 4, cy - 6, cx + 2, cy - 2), fill=(30, 28, 26, 255))
    for cx, cy in ((12, 12), (S - 12, 12), (12, S - 12), (S - 12, S - 12)):
        d.ellipse((cx - 4, cy - 4, cx + 4, cy + 4), fill=(120, 110, 96, 255))
    _noise(rng, im, 10)
    im.save(CM / "nx.spikeplate.png")
    # the spikes: a row of steel points, standing
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for k in range(7):
        x = 10 + k * 18
        h = rng.randint(80, 116)
        d.polygon([(x - 7, S - 2), (x + 7, S - 2), (x, S - h)], fill=(150, 154, 160, 255))
        d.polygon([(x, S - 2), (x + 7, S - 2), (x, S - h)], fill=(96, 100, 108, 255))
        d.line([(x, S - h), (x - 2, S - h + 18)], fill=(230, 232, 236, 255), width=2)
    im.save(CM / "nx.spikes.png")
    # the dart plate: a flagstone a shade proud, a worn rune on it
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((10, 10, S - 10, S - 10), 8, fill=(104, 98, 90, 255), outline=(52, 48, 44, 255), width=4)
    d.line([(40, 44), (64, 84), (88, 44)], fill=(70, 64, 58, 255), width=4)
    d.line([(64, 30), (64, 98)], fill=(70, 64, 58, 255), width=3)
    _noise(rng, im, 12)
    im.save(CM / "nx.dartplate.png")
    # the fire vent: a grate over a red throat
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((8, 8, S - 8, S - 8), fill=(40, 30, 26, 255), outline=(22, 16, 14, 255), width=5)
    for r, c in ((44, (120, 30, 10, 255)), (32, (190, 60, 14, 255)), (18, (250, 140, 40, 255))):
        d.ellipse((64 - r, 64 - r, 64 + r, 64 + r), fill=c)
    for k in range(-3, 4):
        d.line([(64 + k * 12, 14), (64 + k * 12, S - 14)], fill=(28, 22, 20, 255), width=5)
    d.line([(14, 64), (S - 14, 64)], fill=(28, 22, 20, 255), width=5)
    _noise(rng, im, 8)
    im.save(CM / "nx.vent.png")


if __name__ == "__main__":
    cold_brazier()
    traps()
    print("made the brazier and the traps' pictures in", CM)
