"""The four regions ("sims"): the Furry Bazaar (a free shop), the Neon Paws Club, Pawprint Estates (land you can
own) and Sandbox Isle (rez and build anything). Each is scenery (prims), its sky, and the things that matter to
the world: where you land, walls, seats, vendor booths, dance balls, land parcels and the build area.

A region is 6400 x 6400 cm (64 m square); x runs east, z runs south, y is up."""
import math

from .catalog import OBJECTS, P

SIZE = 6400
C = SIZE / 2
PARCEL = 1300
ROAD = 200


def _rot(x, z, yaw):
    a = math.radians(yaw)
    return x * math.cos(a) + z * math.sin(a), -x * math.sin(a) + z * math.cos(a)


def place(prims, x, z, yaw=0.0, y=0.0, scale=1.0):
    """An object's prims moved to (x, y, z), turned by yaw degrees and scaled."""
    out = []
    for shape, pos, size, colour, o in prims:
        px, pz = _rot(pos[0] * scale, pos[2] * scale, yaw)
        o = dict(o)
        r = o.get("rot", (0, 0, 0))
        o["rot"] = (r[0], r[1] + yaw, r[2])
        if shape == "t":
            o.pop("rot")
            out.append((shape, (x + px, y + pos[1] * scale, z + pz), size, colour, o))
        else:
            out.append((shape, (x + px, y + pos[1] * scale, z + pz), tuple(v * scale for v in size), colour, o))
    return out


def box(x, y, z, w, h, d, colour, **o):
    """A box standing on y."""
    return P("c", (x, y + h / 2, z), (w, h, d), colour, **o)


def text(x, y, z, s, colour="#FFFFFF", size=1.6):
    return P("t", (x, y, z), (size, size, size), colour, text=s)


class Sim:
    def __init__(self, key, name, desc, env):
        self.key, self.name, self.desc, self.env = key, name, desc, env
        self.prims = []
        self.tags = {}               # prim index -> tag (what clicking it means)
        self.extra = ""              # raw QML (lights)
        self.landing = (C, C, 0.0)
        self.walls = []              # (x0, z0, x1, z1): you can't walk through these
        self.seats = {}              # tag -> (x, y, z, yaw)
        self.spots = {}              # what residents do where: name -> [(x, z, yaw)]
        self.booths = {}             # tag -> booth name
        self.mannequins = []         # (item key, x, y, z, yaw)
        self.dance = {}              # tag -> dance style
        self.parcels = []            # {"n", "x0", "z0", "x1", "z1", "sign": (x, z)}
        self.build_area = None       # (x0, z0, x1, z1)
        self.teleports = {}          # tag -> sim key

    def add(self, prims, tag=None):
        for p in prims if isinstance(prims, list) else [prims]:
            if tag:
                self.tags[len(self.prims)] = tag
            self.prims.append(p)

    def obj(self, key, x, z, yaw=0.0, y=0.0, scale=1.0, tag=None):
        name, prims, info = OBJECTS[key]
        self.add(place(prims, x, z, yaw, y, scale), tag)
        return info

    def seat(self, key, x, z, yaw=0.0, n=None):
        n = n if n is not None else len(self.seats)
        tag = f"seat:{self.key}:{n}"
        info = self.obj(key, x, z, yaw, tag=tag)
        sx, sy, sz, syaw = info["sit"]
        ox, oz = _rot(sx, sz, yaw)
        self.seats[tag] = (x + ox, sy, z + oz, yaw + syaw)
        self.spots.setdefault("sit", []).append(tag)
        if "sit2" in info:
            tag2 = f"seat:{self.key}:{n}b"
            sx, sy, sz, syaw = info["sit2"]
            ox, oz = _rot(sx, sz, yaw)
            self.seats[tag2] = (x + ox, sy, z + oz, yaw + syaw)
            self.spots["sit"].append(tag2)
        return tag

    def teleport_board(self, x, z, yaw):
        """A board of the other regions; click one to go."""
        self.add(box(x, 0, z, 16, 240, 16, "#4A4A52"))
        self.add(place([box(0, 120, 0, 380, 200, 10, "#1E2A3A"),
                        text(0, 300, 8, "TELEPORT HUB", "#7FD8FF", 1.4)], x, z, yaw))
        k = 0
        for key, label, col in (("bazaar", "Furry Bazaar", "#E8A040"), ("club", "Neon Paws Club", "#E85AD8"),
                                ("estates", "Pawprint Estates", "#6AC86A"), ("sandbox", "Sandbox Isle", "#4AB8E8")):
            if key == self.key:
                continue
            bx = -120 + k * 120
            tag = f"tp:{key}"
            self.add(place([box(bx, 150, 7, 100, 110, 6, col, glow=True)], x, z, yaw), tag)
            self.add(place([text(bx, 246, 12, label, "#FFFFFF", 0.8)], x, z, yaw))
            self.teleports[tag] = key
            k += 1


def _sky(sky, fog, near, far, sun, bright, ambient, pitch, yaw, fill):
    return {"sky": sky, "fog": fog, "fogNear": near, "fogFar": far, "sun": sun, "sunBright": bright,
            "ambient": ambient, "sunPitch": pitch, "sunYaw": yaw, "fill": fill}


def _ground(s, colour, far_colour=None):
    s.add(P("c", (C, -5, C), (SIZE, 10, SIZE), colour, surface="fur"), "ground")
    s.add(P("c", (C, -12, C), (40000, 10, 40000), far_colour or colour, surface="fur"))


def _tree(s, x, z, kind="pine", scale=1.0):
    s.obj(kind, x, z, yaw=(x * 7 + z * 3) % 360, scale=scale)


def _lamp_post(s, x, z, colour="#FFE8B0"):
    s.add([P("y", (x, 150, z), (10, 300, 10), "#2A2A30"), P("s", (x, 305, z), (34, 34, 34), colour, glow=True)])


# ---- the Furry Bazaar -------------------------------------------------------------------------------------------
BOOTHS = [("Tops", "#C83A34"), ("Bottoms & Shoes", "#3A5AA8"), ("Hats", "#E8A040"), ("Eyes & Necks", "#7A4FA8"),
          ("Wings & Backs", "#3AA0A0"), ("Home & Garden", "#4A9A4A"), ("Build Basics", "#8A8A8A")]
BOOTH_SLOTS = {"Tops": ("torso",), "Bottoms & Shoes": ("legs", "feet"), "Hats": ("head",),
               "Eyes & Necks": ("eyes", "neck"), "Wings & Backs": ("back", "wrist")}


def bazaar():
    from .avatar import BODY_ORDER
    s = Sim("bazaar", "Furry Bazaar", "A sunny open-air market where everything is free: furry bodies on pedestals "
            "around the fountain, and stalls of clothes, accessories and things to rez.",
            _sky("#9CCBF2", "#CFE2F4", 3000, 11000, "#FFF4E0", 1.05, "#5A626C", -50, -35, 0.38))
    _ground(s, "#6E9A5A")
    s.add(P("y", (C, 1, C), (5000, 2, 5000), "#D8CBB0", surface="fur"))
    s.add(P("y", (C, 2, C), (2700, 2, 2700), "#C8B898", surface="fur"))
    # the fountain
    s.add([P("y", (C, 30, C), (620, 60, 620), "#B8B0A0", surface="fur"),
           P("y", (C, 50, C), (560, 22, 560), "#5AAAE0", surface="glass", opacity=0.75),
           P("y", (C, 110, C), (60, 160, 60), "#B8B0A0"), P("y", (C, 190, C), (220, 18, 220), "#B8B0A0"),
           P("y", (C, 200, C), (190, 8, 190), "#5AAAE0", surface="glass", opacity=0.8),
           P("s", (C, 240, C), (40, 70, 40), "#BFE6FF", surface="glass", opacity=0.55, anim="pulse")])
    s.walls.append((C - 320, C - 320, C + 320, C + 320))
    # bodies on pedestals around the fountain
    n = len(BODY_ORDER)
    for i, name in enumerate(BODY_ORDER):
        a = i / n * 2 * math.pi
        x, z = C + math.sin(a) * 1150, C + math.cos(a) * 1150
        yaw = math.degrees(a) + 180
        s.add(P("y", (x, 20, z), (130, 40, 130), "#E8E4DC", surface="shiny"))
        s.mannequins.append((f"body:{name}", x, 40.0, z, yaw))
        s.spots.setdefault("browse", []).append((x + math.sin(a + math.pi) * -190, z + math.cos(a + math.pi) * -190,
                                                 yaw + 180))
    # the stalls
    for i, (booth, colour) in enumerate(BOOTHS):
        a = (i + 0.5) / len(BOOTHS) * 2 * math.pi
        x, z = C + math.sin(a) * 2050, C + math.cos(a) * 2050
        yaw = math.degrees(a) + 180
        tag = f"booth:{booth}"
        stall = [box(0, 0, 0, 420, 100, 120, "#A8824E"),
                 box(0, 100, -10, 430, 8, 140, "#8A6A3E")]
        stall += [P("y", (dx, 150, dz), (12, 300, 12), "#6A4A2A") for dx in (-200, 200) for dz in (-60, 60)]
        stall += [P("c", (-150 + k * 60, 310, 0), (60, 14, 170), colour if k % 2 == 0 else "#F4F0E8",
                    surface="cloth", rot=(10, 0, 0)) for k in range(6)]
        stall += [box(-120 + k * 80, 108, 0, 50, 40, 50, ("#E8C870", colour, "#D8D8D8", "#7AB8E8")[k % 4])
                  for k in range(4)]
        s.add(place(stall, x, z, yaw), tag)
        s.add(place([box(0, 200, 70, 300, 70, 6, "#1E2A3A"), text(0, 262, 76, booth, "#FFE9A0", 1.3),
                     text(0, 230, 76, "FREE - click to shop", "#FFFFFF", 0.7)], x, z, yaw), tag)
        s.booths[tag] = booth
        bx, bz = x + math.sin(a) * -230, z + math.cos(a) * -230
        s.spots.setdefault("browse", []).append((bx, bz, yaw + 180))
    # benches, trees, lamps, the welcome sign
    for k in range(8):
        a = (k + 0.25) / 8 * 2 * math.pi
        x, z = C + math.sin(a) * 1650, C + math.cos(a) * 1650
        s.seat("sofa", x, z, math.degrees(a) + 180)
        _lamp_post(s, C + math.sin(a + 0.2) * 1650, C + math.cos(a + 0.2) * 1650)
    for k in range(1, 16):                             # (none in the way of the landing point)
        a = k / 16 * 2 * math.pi
        _tree(s, C + math.sin(a) * 2750, C + math.cos(a) * 2750, "pine" if k % 2 else "palm", 1.1)
    s.landing = (C, C + 2500, 180.0)
    wx = C - 1000
    s.add([box(wx - 260, 0, C + 2350, 20, 220, 20, "#4A4A52"), box(wx + 260, 0, C + 2350, 20, 220, 20, "#4A4A52"),
           box(wx, 160, C + 2350, 600, 150, 14, "#2E4E8A"),
           text(wx, 300, C + 2359, "Welcome to the FURRY BAZAAR", "#FFE9A0", 1.6),
           text(wx, 250, C + 2359, "Everything here is free! Click a body or a stall.", "#FFFFFF", 0.9)])
    s.teleport_board(C + 1100, C + 2400, 200)
    return s


# ---- the Neon Paws Club -----------------------------------------------------------------------------------------
def club():
    s = Sim("club", "Neon Paws Club", "A dance club after dark: a glowing dance floor, a DJ booth, a bar and couches. "
            "Click a dance ball to dance.",
            _sky("#0C0A20", "#1A1430", 2200, 9500, "#B0B8FF", 0.5, "#4A4868", -55, 20, 0.28))
    _ground(s, "#26262C", "#1A1A20")
    w, h = 2600, 420
    x0, z0, x1, z1 = C - w / 2, C - w / 2, C + w / 2, C + w / 2
    s.add(box(C, 0, C, w, 4, w, "#2E2420"))
    wall = "#3A2A4A"
    for x, z, ww, dd in ((C, z0, w, 40), (x0, C, 40, w), (x1, C, 40, w)):
        s.add(box(x, 0, z, ww, h, dd, wall))
    gap = 500
    for x in (x0 + (w - gap) / 4, x1 - (w - gap) / 4):
        s.add(box(x, 0, z1, (w - gap) / 2, h, 40, wall))
    s.walls += [(x0 - 20, z0 - 20, x1 + 20, z0 + 20), (x0 - 20, z0, x0 + 20, z1), (x1 - 20, z0, x1 + 20, z1),
                (x0, z1 - 20, C - gap / 2, z1 + 20), (C + gap / 2, z1 - 20, x1, z1 + 20)]
    for x, z, ww, dd, col in ((C, z0 + 22, w, 6, "#4AE8F0"), (x0 + 22, C, 6, w, "#F05AD8"),
                              (x1 - 22, C, 6, w, "#F05AD8")):
        s.add(box(x, h - 30, z, ww, 10, dd, col, glow=True))
    # the dance floor
    fx, fz = C, C - 150
    tile = 150
    for i in range(8):
        for j in range(8):
            s.add(box(fx - 4 * tile + tile / 2 + i * tile, 4, fz - 4 * tile + tile / 2 + j * tile, tile - 6, 3,
                      tile - 6, "#FF00FF", glow=True, anim="rainbow", phase=(i * 3 + j * 5) % 11))
    s.spots["dance"] = [(fx - 520 + (k % 6) * 210, fz - 480 + (k // 6) * 240, (k * 47) % 360) for k in range(24)]
    s.add([P("y", (fx, 400, fz), (8, 60, 8), "#888888"),
           P("s", (fx, 350, fz), (90, 90, 90), "#E8E8F0", surface="gold", anim="spin")])
    # dance balls
    for k, (dx, dz) in enumerate(((-520, -520), (520, -520), (-520, 520), (520, 520))):
        tag = f"dance:{k + 1}"
        s.add([P("s", (fx + dx, 240, fz + dz), (40, 40, 40), "#FF00FF", glow=True, anim="rainbow", phase=k * 3)], tag)
        s.add(text(fx + dx, 300, fz + dz, f"Dance {k + 1} ♪", "#FFE9A0", 0.9))
        s.dance[tag] = k + 1
    # the DJ booth
    s.add([box(C, 0, z0 + 260, 700, 110, 160, "#1E1E24"), box(C, 110, z0 + 260, 720, 8, 170, "#4AE8F0", glow=True),
           P("y", (C - 160, 124, z0 + 260), (90, 10, 90), "#2A2A2A", anim="spin"),
           P("y", (C + 160, 124, z0 + 260), (90, 10, 90), "#2A2A2A", anim="spin"),
           box(C, 120, z0 + 120, 900, 260, 20, "#101018"),
           box(C, 140, z0 + 132, 860, 220, 4, "#FF00FF", glow=True, anim="rainbow", phase=4),
           text(C, 300, z0 + 140, "NEON PAWS", "#FFFFFF", 2.2)])
    s.walls.append((C - 360, z0 + 170, C + 360, z0 + 350))
    s.spots["dj"] = [(C, z0 + 200, 180.0)]
    # the bar
    bx = x0 + 260
    s.add([box(bx, 0, C, 120, 110, 1000, "#5A3424"), box(bx, 110, C, 140, 8, 1020, "#C8A060", surface="shiny"),
           box(x0 + 60, 0, C, 40, 300, 1000, "#2A1E1A")]
          + [box(x0 + 70, 120 + r * 60, C - 400 + k * 90, 20, 40, 14, ("#5AD85A", "#E8C040", "#E85A5A", "#5A9AE8")[
              (k + r) % 4], glow=True) for k in range(10) for r in range(2)])
    s.walls.append((x0 + 190, C - 520, x0 + 330, C + 520))
    for k in range(5):
        s.seat("beanbag", bx + 230, C - 400 + k * 200, 270)
    # couches
    for k in range(3):
        s.seat("sofa", x1 - 180, C - 600 + k * 600, 270)
    s.add([P("y", (x1 - 420, 40, C - 300 + k * 600), (90, 80, 90), "#2A2A30") for k in range(2)])
    # lights that dance
    lights = []
    for k, (dx, dz, col) in enumerate(((-700, -700, "#FF3AD8"), (700, -700, "#3AD8FF"), (-700, 700, "#FFD83A"),
                                       (700, 700, "#7A3AFF"))):
        lights.append(f"PointLight {{ position: Qt.vector3d({fx + dx}, 330, {fz + dz}); color: \"{col}\"; "
                      f"brightness: 6 + 4 * Math.sin(root.t * 3 + {k * 1.6}); "
                      "constantFade: 1; linearFade: 0.0; quadraticFade: 2.2 }")
    s.extra = "\n".join(lights)
    # outside: the street
    s.add(box(C, 0, z1 + 900, SIZE, 2, 900, "#3A3A40"))
    for k in range(-2, 3):
        _lamp_post(s, C + k * 900, z1 + 480, "#FFD0F0")
    s.add([box(C, h, z1 + 30, 900, 140, 20, "#14101E"), text(C, h + 112, z1 + 44, "NEON PAWS CLUB", "#FF5AD8", 2.0),
           text(C, h + 44, z1 + 44, "dance - chat - be fluffy", "#7FE8FF", 1.0)])
    s.landing = (C, z1 - 300, 180.0)
    s.teleport_board(C + 1100, z1 + 350, 200)
    s.spots["mingle"] = [(C - 900 + k * 360, C + 750, 180.0) for k in range(6)]
    return s


# ---- Pawprint Estates -----------------------------------------------------------------------------------------
def parcel_rect(n):
    i, j = n % 4, n // 4
    x0 = ROAD + i * (PARCEL + ROAD)
    z0 = ROAD + j * (PARCEL + ROAD)
    return x0, z0, x0 + PARCEL, z0 + PARCEL


def house_prims(colour, roof):
    """A little house (front to +z), centred on its floor."""
    out = [box(0, 0, 0, 640, 300, 480, colour), box(0, 0, 241, 110, 210, 6, "#5A3A24")]
    for dx in (-200, 200):
        out.append(box(dx, 120, 242, 110, 90, 4, "#FFE9A8", glow=True))
    out.append(P("c", (0, 300, 0), (452, 452, 470), colour, rot=(0, 0, 45)))          # the gable ends
    for side in (-1, 1):                                                               # the roof itself
        out.append(P("c", (side * 168, 466, 0), (420, 18, 560), roof, rot=(0, 0, -side * 45)))
    out.append(box(0, 0, 330, 700, 12, 180, "#9A7A54"))
    out.append(box(240, 300, -120, 60, 160, 60, "#8A5A44"))
    return out


def estates(owners):
    s = Sim("estates", "Pawprint Estates", "Leafy lots of land with little houses. Residents live here - and any "
            "free lot can be yours: click its sign to claim it, then build on it.",
            _sky("#F0C890", "#F4D8B0", 2500, 10000, "#FFD8A8", 0.95, "#6A5A50", -28, -60, 0.32))
    _ground(s, "#6E9A4A")
    for k in range(5):                                 # roads
        v = k * (PARCEL + ROAD) + ROAD / 2
        s.add(box(v, 0, C, ROAD, 3, SIZE, "#5A5A5E"))
        s.add(box(C, 0, v, SIZE, 3, ROAD, "#5A5A5E"))
    for n in range(16):
        x0, z0, x1, z1 = parcel_rect(n)
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        owner = owners.get(n)
        s.add([P("y", (x, 40, z), (10, 80, 10), "#F4F0E8") for x in (x0 + 20, x1 - 20) for z in (z0 + 20, z1 - 20)])
        sign_tag = f"parcel:{n}"
        label = f"{owner}'s place" if owner else "FREE LAND\nclick to claim"
        s.add([P("y", (x1 - 120, 60, z1 - 40), (8, 120, 8), "#6A4424"),
               box(x1 - 120, 100, z1 - 40, 180, 70, 8, "#8A5A34" if owner else "#3A8A3A")], sign_tag)
        s.add(text(x1 - 120, 180, z1 - 34, label, "#FFFFFF", 0.75))
        s.parcels.append({"n": n, "x0": x0, "z0": z0, "x1": x1, "z1": z1, "sign": (x1 - 120, z1 - 120)})
        if owner and owner != "@player":
            h = sum(map(ord, owner))
            colour = ("#E8D8B8", "#C8D8E8", "#E8C8C8", "#D8E8C8", "#E8E0A8", "#D0C8E8")[h % 6]
            roof = ("#8A3A2A", "#3A4A6A", "#4A6A3A", "#6A4A3A")[h % 4]
            s.add(place(house_prims(colour, roof), cx, cz - 180))
            s.walls.append((cx - 330, cz - 180 - 250, cx + 330, cz - 180 + 250))
            seat = s.seat("sofa", cx - 120, cz + 280, 180, n=f"porch{n}")
            s.spots.setdefault("home", []).append((n, seat, cx + 200, cz + 400))
            _tree(s, x0 + 160, z1 - 200, "pine", 0.8)
            s.obj("flowerpot", cx + 280, cz + 260)
        else:
            _tree(s, x0 + 200, z0 + 200, "pine", 0.6)
    s.landing = (2 * (PARCEL + ROAD) + ROAD / 2, SIZE - 300, 180.0)
    s.add([box(s.landing[0] + 300, 0, s.landing[1] - 200, 400, 120, 20, "#2E4E8A"),
           text(s.landing[0] + 300, 150, s.landing[1] - 188, "PAWPRINT ESTATES", "#FFE9A0", 1.1)])
    s.teleport_board(s.landing[0] - 900, s.landing[1] - 150, 160)
    return s


# ---- Sandbox Isle -----------------------------------------------------------------------------------------------
def sandbox():
    s = Sim("sandbox", "Sandbox Isle", "A public sandbox on a little island: rez anything and build. Objects left "
            "here go home to their owners after two hours.",
            _sky("#8ED0F4", "#C8E8F8", 3500, 14000, "#FFFAF0", 1.1, "#5A6870", -55, 30, 0.4))
    s.add(P("c", (C, -30, C), (60000, 10, 60000), "#2A8AB8", surface="shiny"))
    s.add(P("y", (C, -10, C), (5600, 20, 5600), "#E8D8A8", surface="fur"), "ground")
    s.add(P("y", (C, 1, C), (4200, 2, 4200), "#8AB86A", surface="fur"), "ground")
    deck = 2600
    s.add(box(C, 0, C, deck, 10, deck, "#B8925A"), "ground")
    for k in range(1, 13):
        v = C - deck / 2 + k * deck / 13
        s.add(box(v, 10, C, 4, 1, deck, "#8A6A3A"))
        s.add(box(C, 10, v, deck, 1, 4, "#8A6A3A"))
    s.build_area = (C - deck / 2, C - deck / 2, C + deck / 2, C + deck / 2)
    for k in range(14):
        a = k / 14 * 2 * math.pi
        _tree(s, C + math.sin(a) * 2350, C + math.cos(a) * 2350, "palm", 1.0)
    s.add([box(C, 0, C + 1500, 20, 200, 20, "#4A4A52"), box(C, 140, C + 1500, 700, 140, 12, "#F2C230"),
           text(C, 262, C + 1508, "SANDBOX - BUILD ANYTHING", "#1A1A1A", 1.4),
           text(C, 200, C + 1508, "Objects go home after 2 hours", "#1A1A1A", 0.8)])
    s.landing = (C - 600, C + 1600, 180.0)
    s.teleport_board(C - 1700, C + 1650, 150)
    s.spots["build"] = [(C - 900 + (k % 4) * 600, C - 900 + (k // 4) * 600, (k * 70) % 360) for k in range(12)]
    s.seat("beanbag", C + 1700, C + 900, 220)
    s.seat("beanbag", C + 1900, C + 700, 230)
    return s


def all_sims(owners):
    return {"bazaar": bazaar(), "club": club(), "estates": estates(owners), "sandbox": sandbox()}


SIM_ORDER = ["bazaar", "club", "estates", "sandbox"]
