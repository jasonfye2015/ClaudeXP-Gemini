"""Furry avatars, built from primitives: a body spec (head family, ears, tail, legs, wings, horns, extras, colours,
markings) plus whatever's worn, turned into one Qt Quick 3D node that walks, dances, sits and flies by itself.

Units are centimetres, Y is up, an avatar faces +Z with its feet at the origin. The node's root has the properties
the world drives: walking, dance (0 none, 1-4 styles), sitting, flying, typing, label and title."""
import copy
import math

SHAPES = {"s": "#Sphere", "c": "#Cube", "y": "#Cylinder", "k": "#Cone"}
SURFACES = {"fur": (0.92, 0.0), "scales": (0.42, 0.12), "feathers": (0.85, 0.0), "skin": (0.55, 0.0),
            "metal": (0.35, 0.85), "spirit": (0.3, 0.0), "cloth": (0.95, 0.0), "shiny": (0.25, 0.3),
            "gold": (0.3, 1.0), "glass": (0.08, 0.0)}

DEFAULT = {"species": "Fox", "head": "canine", "snout": 1.0, "ears": "pointed", "ear_size": 1.0, "tail": "fluffy",
           "tail_size": 1.0, "legs": "digi", "wings": None, "horns": None, "extras": [], "fur": "#C8642E",
           "belly": "#F4EDE2", "accent": "#2A2422", "third": "#E8E8E8", "eyes": "#3A7A3A", "nose": "#231C1C",
           "horn": "#E8DCC0", "markings": ["belly", "muzzle", "tailtip"], "height": 1.0, "build": 1.0,
           "head_size": 1.0, "surface": "fur", "frame": "m"}


def spec(**kw):
    s = copy.deepcopy(DEFAULT)
    s.update(copy.deepcopy(kw))
    return s


def _n(v):
    return f"{v:.2f}".rstrip("0").rstrip(".") if isinstance(v, float) else str(v)


def vec(x, y, z):
    return f"Qt.vector3d({_n(float(x))}, {_n(float(y))}, {_n(float(z))})"


def material(colour, surface="fur", opacity=None, glow=False, colour_expr=None):
    rough, metal = SURFACES.get(surface, SURFACES["fur"])
    base = colour_expr or f'"{colour}"'
    if glow:
        s = f"PrincipledMaterial {{ baseColor: {base}; lighting: PrincipledMaterial.NoLighting"
    else:
        s = f"PrincipledMaterial {{ baseColor: {base}; roughness: {rough}; metalness: {metal}"
    if surface == "spirit" and not glow:
        s += "; emissiveFactor: Qt.vector3d(0.25, 0.3, 0.38)"
    if opacity is not None and opacity < 1:
        s += f"; opacity: {opacity}; alphaMode: PrincipledMaterial.Blend"
    return s + " }"


def model(shape, pos, size, colour, rot=None, surface="fur", tag=None, opacity=None, glow=False, extra="",
          colour_expr=None):
    """One primitive. size is in centimetres across (a sphere's diameter, a cube's sides, a cone's base and
    height, a cylinder's diameter and height)."""
    sx, sy, sz = size
    out = f'Model {{ source: "{SHAPES[shape]}"; position: {vec(*pos)}; scale: {vec(sx / 100, sy / 100, sz / 100)}; '
    if rot:
        out += f"eulerRotation: {vec(*rot)}; "
    if tag:
        out += f'objectName: "{tag}"; pickable: true; '
    out += extra
    return out + f"materials: {material(colour, surface, opacity, glow, colour_expr)} }}"


def node(pos=(0, 0, 0), children=(), rot=None, extra="", scale=None):
    out = f"Node {{ position: {vec(*pos)}; "
    if rot:
        out += f"eulerRotation: {rot if isinstance(rot, str) else vec(*rot)}; "
    if scale:
        out += f"scale: {vec(*scale)}; "
    return out + extra + "\n" + "\n".join(children) + "\n}"


# ---- the body --------------------------------------------------------------------------------------------------
class Builder:
    def __init__(self, s, wear, tag):
        self.s = s
        self.wear = wear or []
        self.tag = tag
        self.H = s["height"]
        self.W = s["build"]
        self.mat = s["surface"]

    def m(self, shape, pos, size, colour, rot=None, surface=None, **kw):
        return model(shape, pos, size, colour, rot, surface or self.mat, self.tag, **kw)

    def worn(self, slot):
        return [w for w in self.wear if w.get("slot") == slot]

    def has(self, mark):
        return mark in self.s["markings"]

    def colour(self, part):
        """Which colour a part takes, given the markings."""
        s = self.s
        if part == "muzzle":
            return s["belly"] if self.has("muzzle") else s["fur"]
        if part in ("sock", "glove"):
            return s["accent"] if self.has("socks") else s["fur"]
        return s["fur"]

    # ---- the pieces ----
    def torso(self):
        s, H, W = self.s, self.H, self.W
        f = s["frame"]
        hips = 0.34 if f == "f" else 0.31
        chest = 0.34 if f == "f" else 0.38
        out = [self.m("s", (0, 8 * H, 0), (hips * 100 * W, 26 * H, 24 * W), s["fur"]),
               self.m("s", (0, 33 * H, 0), (31 * W, 50 * H, 22 * W), s["fur"]),
               self.m("s", (0, 52 * H, 0), (chest * 100 * W, 26 * H, 24 * W), s["fur"]),
               self.m("y", (0, 70 * H, 0), (13 * W, 18 * H * (1.6 if "longneck" in s["extras"] else 1), 13 * W),
                      s["fur"])]
        if self.has("belly"):
            out.append(self.m("s", (0, 30 * H, 6 * W), (22 * W, 42 * H, 14 * W), s["belly"]))
        if self.has("saddle"):
            out.append(self.m("s", (0, 40 * H, -6 * W), (29 * W, 40 * H, 18 * W), s["accent"]))
        if self.has("stripes"):
            for k in range(4):
                out.append(self.m("s", (0, (14 + k * 11) * H, 0), (32.6 * W, 3.2, 23 * W), s["accent"]))
        if self.has("spots"):
            for pos, size, col in (((8 * W, 40 * H, 6 * W), (14, 12, 8), s["accent"]),
                                   ((-9 * W, 22 * H, 5 * W), (12, 10, 8), s["third"]),
                                   ((5 * W, 50 * H, -9 * W), (14, 10, 8), s["third"]),
                                   ((-6 * W, 12 * H, -9 * W), (12, 12, 8), s["accent"])):
                out.append(self.m("s", pos, size, col))
        if self.has("speckles"):
            for k in range(14):
                x = ((k * 37) % 23 - 11) * W
                y = (16 + (k * 13) % 40) * H
                z = 10 * W if k % 2 else -10 * W
                out.append(self.m("s", (x, y, z), (2.5, 2.5, 2.5), s["accent"]))
        if "ruff" in s["extras"]:
            out.append(self.m("s", (0, 66 * H, 2), (36 * W, 18, 30 * W), s["belly"]))
        if "quills" in s["extras"]:
            for k in range(12):
                x = ((k % 3) - 1) * 8 * W
                y = (18 + (k // 3) * 12) * H
                out.append(self.m("k", (x, y, -10 * W), (5, 22, 5), s["accent"], rot=(-125, 0, (k % 3 - 1) * 12)))
        if "glowcore" in s["extras"]:
            out.append(self.m("s", (0, 40 * H, 10 * W), (8, 8, 4), s["accent"], glow=True))
        if "plates" in s["extras"]:
            for y in (20, 40):
                out.append(self.m("c", (0, y * H, 9 * W), (28 * W, 8, 6), s["accent"], surface="metal"))
        out += self.clothes_torso()
        return out

    def head(self):
        s = self.s
        fam = s["head"]
        sn = s["snout"]
        e = s["ear_size"]
        out = []
        m = self.m
        # the skull
        if fam == "golem":
            out.append(m("c", (0, 0, 0), (30, 30, 28), s["fur"], surface="metal"))
            out.append(m("c", (0, -10, 6), (26, 10, 22), s["accent"], surface="metal"))
        elif fam == "amphibian":
            out.append(m("s", (0, -2, 2), (38, 24, 32), s["fur"]))
        elif fam == "fish":
            out.append(m("s", (0, 0, 2), (38, 34, 36), s["fur"]))
        elif fam == "insect":
            out.append(m("s", (0, 0, 0), (26, 27, 24), s["fur"]))
        else:
            out.append(m("s", (0, 0, 0), (32, 30, 30), s["fur"]))
        # the face
        eye_x, eye_y, eye_z, eye_r = 6.0, 2.5, 12.5, 7.0
        if fam == "canine":
            length = 10 + 14 * sn
            out.append(m("s", (0, -5, 11 + length * 0.42), (15, 12, length), self.colour("muzzle")))
            out.append(m("s", (0, -1.5, 11 + length * 0.9), (5.5, 4.5, 4.5), s["nose"], surface="shiny"))
        elif fam == "feline":
            for x in (-3.4, 3.4):
                out.append(m("s", (x, -6, 12.5), (9, 8, 8), self.colour("muzzle")))
            out.append(m("s", (0, -3, 15), (4.5, 3.5, 3.5), s["nose"], surface="shiny"))
        elif fam in ("rodent", "ursine"):
            length = 10 + 8 * sn
            out.append(m("s", (0, -5, 11 + length * 0.4), (13 if fam == "rodent" else 17, 11, length),
                         self.colour("muzzle")))
            out.append(m("s", (0, -2.5, 11 + length * 0.85), (4.5, 3.5, 3.5), s["nose"], surface="shiny"))
        elif fam == "bird":
            out.append(m("k", (0, -3, 12), (10, 18 * sn, 7), s["nose"], rot=(90, 0, 0), surface="shiny"))
            eye_x, eye_y, eye_z = 9.5, 3.0, 9.0
        elif fam == "reptile":
            length = 14 + 16 * sn
            out.append(m("s", (0, -6, 11 + length * 0.42), (17, 10, length), self.colour("muzzle")))
            for x in (-3, 3):
                out.append(m("s", (x, -3, 11 + length * 0.88), (2.2, 2.2, 2.2), s["nose"]))
            for x in (-6, 6):
                out.append(m("s", (x, 6, 9), (8, 4, 10), s["fur"]))
        elif fam == "bovine":
            out.append(m("s", (0, -7, 12), (20, 14, 15), self.colour("muzzle")))
            for x in (-4, 4):
                out.append(m("s", (x, -6, 19), (3, 3, 2), s["nose"]))
        elif fam == "deer":
            length = 12 + 10 * sn
            out.append(m("s", (0, -6, 11 + length * 0.42), (13, 11, length), self.colour("muzzle")))
            out.append(m("s", (0, -3.5, 11 + length * 0.88), (5, 4, 4), s["nose"], surface="shiny"))
        elif fam == "amphibian":
            out.append(m("s", (0, -10, 7), (30, 6, 22), s["belly"]))
            eye_x, eye_y, eye_z, eye_r = 9.0, 9.0, 7.0, 11.0
        elif fam == "insect":
            for x in (-10, 10):
                out.append(m("s", (x, 2, 6), (13, 15, 13), s["eyes"], surface="shiny"))
            for x in (-3, 3):
                out.append(m("k", (x, -9, 9), (3, 7, 3), s["accent"], rot=(150, 0, -x * 4)))
            eye_r = 0
        elif fam == "fish":
            out.append(m("s", (0, -9, 13), (22, 6, 8), "#1A1010"))
            for k in range(5):
                out.append(m("k", (-8 + k * 4, -7, 15), (2, 4, 2), "#F0F0E8", rot=(180, 0, 0)))
            eye_x, eye_y, eye_z, eye_r = 9.0, 5.0, 12.0, 6.0
        elif fam == "golem":
            for x in (-6, 6):
                out.append(m("c", (x, 3, 14.5), (6, 3, 2), "#FF9A30", glow=True))
            eye_r = 0
        elif fam == "alpaca":
            out.append(m("s", (0, -5, 13), (14, 12, 16), self.colour("muzzle")))
            out.append(m("s", (0, -4, 20), (5, 3.5, 3), s["nose"]))
        # eyes
        if eye_r:
            for x in (-eye_x, eye_x):
                out.append(m("s", (x, eye_y, eye_z), (eye_r, eye_r, eye_r * 0.7), "#F8F8F0", surface="shiny"))
                out.append(m("s", (x * 1.02, eye_y, eye_z + eye_r * 0.32), (eye_r * 0.62, eye_r * 0.62, 1.5),
                             s["eyes"], surface="shiny"))
                out.append(m("s", (x * 1.03, eye_y, eye_z + eye_r * 0.4), (eye_r * 0.3, eye_r * 0.3, 1),
                             "#101010", surface="shiny"))
        # markings on the head
        if self.has("mask"):
            out.append(m("s", (0, 2.5, 6), (34, 8, 26), s["accent"]))
        if self.has("blaze"):
            out.append(m("s", (0, 9, 6), (6, 7, 30), s["belly"]))
        if self.has("cheeks"):
            for x in (-11, 11):
                out.append(m("s", (x, -3, 8), (5, 5, 3), s["accent"]))
        if self.has("speckles"):
            for x, y in ((-6, 9), (5, 11), (0, 13), (9, 6), (-10, 5)):
                out.append(m("s", (x, y, 9), (2.2, 2.2, 2.2), s["accent"]))
        # ears
        ears = s["ears"]
        for side in (-1, 1):
            if ears in ("pointed", "tufted"):
                inner = [m("k", (0, 0, 0), (8 * e, 17 * e, 3.5), s["fur"])]
                if self.has("eartips"):
                    inner.append(m("k", (0, 10 * e, 0.3), (4 * e, 7 * e, 3.6), s["accent"]))
                if ears == "tufted":
                    inner.append(m("k", (0, 15 * e, 0), (1.8, 9 * e, 1.8), s["accent"]))
                out.append(node((side * 9, 11, -2), inner, rot=(0, 0, -side * 14)))
            elif ears == "round":
                out.append(m("s", (side * 11, 11, -1), (10 * e, 10 * e, 3.5), s["fur"]))
                if self.has("eartips"):
                    out.append(m("s", (side * 11.5, 12, -0.5), (6 * e, 6 * e, 3.6), s["accent"]))
            elif ears == "long":
                inner = [m("s", (0, 14 * e, 0), (6.5 * e, 32 * e, 3), s["fur"])]
                if self.has("eartips"):
                    inner.append(m("s", (0, 26 * e, 0.2), (4.5 * e, 10 * e, 3.1), s["accent"]))
                out.append(node((side * 5, 13, -2), inner, rot=(0, 0, -side * 9)))
            elif ears == "floppy":
                out.append(node((side * 14, 4, -1), [m("s", (0, -8 * e, 0), (7, 20 * e, 4), s["accent"])],
                                rot=(0, 0, side * 22)))
            elif ears == "small":
                out.append(m("s", (side * 16, 5, -1), (10 * e, 5, 4), s["fur"]))
            elif ears == "fin":
                out.append(node((side * 17, 2, 0), [m("k", (0, 0, 0), (12 * e, 14 * e, 2), s["accent"])],
                                rot=(0, 0, -side * 70)))
        # horns and other headgear of nature
        horns = s["horns"]
        for side in (-1, 1):
            if horns == "curved":
                for k in range(5):
                    out.append(m("s", (side * (12 + k * 4.2), 8 + (0, 2.5, 3, 1.5, -1.5)[k], -2 - k),
                                 (8 - k * 1.1, 8 - k * 1.1, 8 - k * 1.1), s["horn"], surface="shiny"))
            elif horns == "antlers":
                parts = [m("y", (0, 14, 0), (2.4, 28, 2.4), s["horn"]),
                         node((0, 10, 0), [m("y", (0, 6, 0), (2, 12, 2), s["horn"])], rot=(0, 0, side * -50)),
                         node((0, 20, 0), [m("y", (0, 6, 0), (2, 12, 2), s["horn"])], rot=(-40, 0, side * -30)),
                         node((0, 27, 0), [m("y", (0, 5, 0), (1.8, 10, 1.8), s["horn"])], rot=(0, 0, side * 40))]
                if "palmate" in s["extras"]:
                    parts.append(m("s", (side * 3, 26, 0), (14, 10, 3), s["horn"]))
                out.append(node((side * 7, 12, -2), parts, rot=(0, 0, side * -25)))
            elif horns == "dragon":
                out.append(node((side * 6, 11, -6), [m("k", (0, 0, 0), (5, 18, 5), s["horn"], surface="shiny")],
                                rot=(-55, 0, side * -10)))
            elif horns == "small":
                out.append(node((side * 6, 12, 0), [m("k", (0, 0, 0), (4, 9, 4), s["horn"])], rot=(-15, 0, 0)))
        extras = s["extras"]
        if "crest" in extras:
            for k in range(4):
                out.append(m("k", (0, 13 - k, -3 - k * 2.5), (3.5, 13 + k * 2, 3.5), s.get("crest", s["accent"]),
                             rot=(-(25 + k * 18), 0, 0)))
        if "antennae" in extras:
            for side in (-1, 1):
                out.append(node((side * 4, 12, 5), [m("y", (0, 12, 0), (1.2, 24, 1.2), s["accent"]),
                                                    m("s", (0, 24, 0), (3.5, 3.5, 3.5), s["accent"])],
                                rot=(-25, 0, side * -22)))
        if "lure" in extras:
            bulb = m("s", (0, 14, 0), (7, 7, 7), "#FFD27A", glow=True)
            out.append(node((0, 15, 6), [m("y", (0, 10, 0), (1.4, 20, 1.4), s["accent"]),
                                         node((0, 20, 0), [m("y", (0, 7, 0), (1.2, 14, 1.2), s["accent"]), bulb],
                                              rot=(70, 0, 0))], rot=(35, 0, 0)))
        if "whiskers" in extras:
            for side in (-1, 1):
                for k in (-8, 0, 8):
                    out.append(node((side * 6, -5, 15), [m("y", (0, 10, 0), (0.6, 20, 0.6), "#E8E8E0")],
                                    rot=(0, 0, -side * (80 + k))))
        if "mane" in extras:
            out.append(m("s", (0, -1, -6), (46, 44, 34), s["accent"]))
        if "hair" in extras:
            out.append(m("s", (0, 12, 2), (20, 9, 18), s["accent"]))
        if "fins" in extras:
            out.append(m("k", (0, 14, -2), (3, 14, 18), s["accent"], rot=(-20, 0, 0)))
        out += self.clothes_head()
        return out

    def arm(self, side):
        s, H, W = self.s, self.H, self.W
        sleeve = next((w for w in self.worn("torso") if w["kind"] in ("longsleeve", "hoodie", "jacket", "tshirt")),
                      None)
        upper = [self.m("s", (0, -14 * H, 0), (10 * W, 32 * H, 10 * W), s["fur"])]
        fore = [self.m("s", (0, -13 * H, 0), (9 * W, 28 * H, 9 * W), self.colour("glove")),
                self.m("s", (0, -28 * H, 1), (10, 10, 10), self.colour("glove"))]
        if sleeve:
            upper.append(model("s", (0, -12 * H, 0), (11.5 * W, 26 * H, 11.5 * W), sleeve["colour"], None, "cloth",
                               self.tag))
            if sleeve["kind"] != "tshirt":
                fore.append(model("s", (0, -10 * H, 0), (10.5 * W, 22 * H, 10.5 * W), sleeve["colour"], None, "cloth",
                                  self.tag))
        for w in self.worn("wrist"):
            fore.append(model("y", (0, -21 * H, 0), (10.5, 3, 10.5), w["colour"], None,
                              "gold" if w["kind"] == "bangle" else "shiny", self.tag))
        x_expr = (f"av.sitting ? -30 : av.flying ? -165 : av.walking ? {-side} * Math.sin(av.phase) * 24 : "
                  f"av.dance === 1 ? -60 - Math.sin(av.phase * 2) * 30 : av.dance === 3 ? -20 + {side} * "
                  f"Math.sin(av.phase) * 25 : 0")
        z_expr = (f"av.dance === 2 ? {side} * (150 + Math.sin(av.phase) * 15) : av.dance === 4 ? {side} * 85 : "
                  f"av.dance === 3 ? {side} * 25 : av.flying ? {side} * 10 : {side} * 6")
        elbow = ("av.walking ? -12 : av.dance === 1 ? -70 : av.dance === 3 ? -45 : av.sitting ? -40 : "
                 "av.flying ? 0 : -6")
        return node((side * 19 * W, 58 * H, 0),
                    upper + [node((0, -28 * H, 0), fore, rot=f"Qt.vector3d({elbow}, 0, 0)")],
                    rot=f"Qt.vector3d({x_expr}, 0, {z_expr})")

    def leg(self, side):
        s, H, W = self.s, self.H, self.W
        pants = next((w for w in self.worn("legs")), None)
        boots = next((w for w in self.worn("feet")), None)
        thigh = [self.m("s", (0, -22 * H, 0), (14 * W, 46 * H, 14 * W), s["fur"])]
        if pants:
            long_ = pants["kind"] in ("pants", "jeans")
            thigh.append(model("s", (0, -20 * H, 0), (15.5 * W, (44 if long_ else 30) * H, 15.5 * W),
                               pants["colour"], None, "cloth", self.tag))
        sock = self.colour("sock")
        kind = s["legs"]
        if kind == "digi":
            shin = [self.m("s", (0, -14 * H, -4), (11 * W, 32 * H, 11 * W), s["fur"], rot=(25, 0, 0)),
                    self.m("s", (0, -32 * H, -6), (9 * W, 24 * H, 9 * W), sock, rot=(-15, 0, 0)),
                    self.m("s", (0, -43 * H, 4), (12 * W, 7, 20), sock)]
        elif kind == "hoof":
            shin = [self.m("s", (0, -20 * H, 0), (10 * W, 42 * H, 10 * W), sock),
                    self.m("y", (0, -41 * H, 0), (11 * W, 8, 11 * W), "#2A2420", surface="shiny")]
        else:
            shin = [self.m("s", (0, -20 * H, 0), (11.5 * W, 44 * H, 11.5 * W), sock),
                    self.m("s", (0, -42 * H, 6), (12 * W, 7, 22), sock)]
        if pants and pants["kind"] in ("pants", "jeans"):
            shin.append(model("s", (0, -18 * H, 0), (13.5 * W, 34 * H, 13.5 * W), pants["colour"], None, "cloth",
                              self.tag))
        if boots:
            shin.append(model("s", (0, -38 * H, 4), (14 * W, 16, 24), boots["colour"], None, "shiny", self.tag))
        hip = (f"av.sitting ? -88 : av.flying ? 18 + Math.sin(av.phase) * 6 : av.walking ? {side} * "
               f"Math.sin(av.phase) * 26 : av.dance === 1 ? -Math.max(0, {side} * Math.sin(av.phase)) * 22 : "
               f"av.dance === 3 ? {side} * Math.sin(av.phase) * 10 : 0")
        knee = (f"av.sitting ? 88 : av.flying ? 30 : av.walking ? Math.max(0, {-side} * Math.sin(av.phase)) * 38 : "
                f"av.dance === 1 ? Math.max(0, {side} * Math.sin(av.phase)) * 40 : 0")
        return node((side * 10 * W, 0, 0), thigh + [node((0, -44 * H, 0), shin, rot=f"Qt.vector3d({knee}, 0, 0)")],
                    rot=f"Qt.vector3d({hip}, 0, 0)")

    def tail(self):
        s, H, W = self.s, self.H, self.W
        kind = s["tail"]
        t = s["tail_size"]
        tip = s["accent"] if self.has("tailtip") and s["accent"] != s["fur"] else s["belly"]
        if not self.has("tailtip"):
            tip = s["fur"]
        parts = []
        if kind == "fluffy":
            sizes = (10, 16, 19, 18, 13)
            for k, d in enumerate(sizes):
                col = tip if k == len(sizes) - 1 else s["fur"]
                parts.append(self.m("s", (0, k * 4.5 * t, -k * 11 * t), (d * t, d * t, d * 1.3 * t), col))
        elif kind == "thin":
            for k in range(7):
                parts.append(self.m("s", (0, k * k * 0.6 * t, -k * 8 * t), (6 * t, 6 * t, 9 * t),
                                    tip if k == 6 else s["fur"]))
        elif kind == "thick":
            for k in range(7):
                d = (17 - k * 2) * t
                parts.append(self.m("s", (0, -k * 5 * t, -k * 11 * t), (d, d, d * 1.4),
                                    s["accent"] if self.has("stripes") and k % 2 else s["fur"]))
        elif kind == "feathers":
            for k in range(5):
                parts.append(node((0, 0, 0), [self.m("s", (0, -4, -16 * t), (6, 2, 30 * t),
                                                     s["accent"] if k % 2 else s["fur"])],
                                  rot=(-30, (k - 2) * 16, 0)))
        elif kind == "puff":
            parts.append(self.m("s", (0, 2, -4), (13 * t, 13 * t, 13 * t), s["belly"]))
        elif kind == "fin":
            parts.append(self.m("s", (0, 0, -10 * t), (16, 8, 22 * t), s["fur"]))
            parts.append(self.m("k", (0, 0, -26 * t), (3, 26 * t, 26 * t), s["accent"], rot=(-90, 0, 0)))
        elif kind == "stub":
            parts.append(self.m("s", (0, 2, -3), (8 * t, 10 * t, 8 * t), s["fur"]))
        elif kind == "ringed":
            for k in range(6):
                parts.append(self.m("s", (0, k * 3.5 * t, -k * 10 * t), (12 * t, 12 * t, 13 * t),
                                    s["accent"] if k % 2 else s["fur"]))
        if not parts:
            return []
        sway = "Math.sin(av.tailT * (av.dance > 0 ? 2.2 : 1)) * 18"
        lift = "av.flying ? 30 : 0"
        return [node((0, 2 * H, -11 * W), parts, rot=f"Qt.vector3d({lift}, {sway}, 0)")]

    def wings(self):
        s, H, W = self.s, self.H, self.W
        kind = s["wings"]
        extra = [w for w in self.worn("back") if w["kind"] in ("angel wings", "fairy wings", "bat wings")]
        out = []
        for kind_, colour, accent in ([(kind, s["fur"], s.get("wingtip", s["accent"]))] if kind else []) + \
                [({"angel wings": "feather", "fairy wings": "insect", "bat wings": "bat"}[w["kind"]], w["colour"],
                  w.get("colour2", w["colour"])) for w in extra]:
            for side in (-1, 1):
                if kind_ == "feather":
                    parts = [model("s", (side * 18, 0, 0), (38, 7, 20), colour, None, "feathers", self.tag),
                             model("s", (side * 36, -5, -2), (34, 6, 18), colour, None, "feathers", self.tag),
                             model("s", (side * 50, -11, -4), (28, 5, 14), accent, None, "feathers", self.tag)]
                elif kind_ == "bat":
                    parts = [model("y", (side * 26, 0, 0), (3, 52, 3), accent, (0, 0, 90), "skin", self.tag),
                             model("s", (side * 28, -10, 0), (56, 3, 34), colour, None, "skin", self.tag)]
                else:
                    parts = [model("s", (side * 26, 4, 0), (50, 1.5, 18), colour, (0, 0, side * 10), "glass", self.tag,
                                   opacity=0.38),
                             model("s", (side * 22, -10, 0), (38, 1.5, 14), colour, (0, 0, side * -15), "glass",
                                   self.tag, opacity=0.38)]
                rot = (f"Qt.vector3d(0, av.flying ? 0 : {side} * -70, av.flying ? {side} * Math.sin(av.phase * 2) "
                       f"* 35 : {side} * -12)")
                out.append(node((side * 8 * W, 54 * H, -12 * W), parts, rot=rot))
        return out

    # ---- clothes ----
    def clothes_torso(self):
        H, W = self.H, self.W
        out = []
        for w in self.worn("torso"):
            k, c = w["kind"], w["colour"]
            c2 = w.get("colour2", c)
            body = [model("s", (0, 30 * H, 0), (33.5 * W, 46 * H, 24.5 * W), c, None, "cloth", self.tag),
                    model("s", (0, 51 * H, 0), (39.5 * W, 25 * H, 25.5 * W), c, None, "cloth", self.tag)]
            if k == "hoodie":
                body.append(model("s", (0, 66 * H, -9 * W), (26 * W, 18, 16), c, None, "cloth", self.tag))
                body.append(model("s", (0, 22 * H, 11.5 * W), (18 * W, 10 * H, 4), c2, None, "cloth", self.tag))
            elif k == "jacket":
                body.append(model("c", (0, 38 * H, 12.2 * W), (6 * W, 38 * H, 2), c2, None, "cloth", self.tag))
                body.append(model("s", (0, 64 * H, -2), (34 * W, 10, 26 * W), c, None, "cloth", self.tag))
            elif k == "vest":
                body = [model("s", (0, 38 * H, -1), (34 * W, 40 * H, 24 * W), c, None, "cloth", self.tag),
                        model("c", (0, 38 * H, 12 * W), (8 * W, 38 * H, 2), "#FFFFFF", None, "cloth", self.tag)]
            elif k == "dress":
                body.append(model("k", (0, -40 * H, 0), (62 * W, 52 * H, 50 * W), c, None, "cloth", self.tag))
            elif k == "tanktop":
                body = body[:1]
            out += body
        for w in self.worn("legs"):
            if w["kind"] == "skirt":
                out.append(model("k", (0, -30 * H, 0), (56 * W, 42 * H, 46 * W), w["colour"], None, "cloth",
                                 self.tag))
            else:
                out.append(model("s", (0, 8 * H, 0), (34 * W, 28 * H, 26 * W), w["colour"], None, "cloth", self.tag))
        for w in self.worn("neck"):
            k, c = w["kind"], w["colour"]
            if k == "collar":
                out.append(model("y", (0, 68 * H, 0), (15.5 * W, 3.5, 15.5 * W), c, None, "shiny", self.tag))
                out.append(model("s", (0, 64 * H, 8 * W), (4, 4, 4), w.get("colour2", "#E8C840"), None, "gold",
                                 self.tag))
            elif k == "scarf":
                out.append(model("y", (0, 68 * H, 0), (18 * W, 7, 18 * W), c, None, "cloth", self.tag))
                out.append(model("c", (5 * W, 56 * H, 9 * W), (6, 20, 2), c, (0, 0, 8), "cloth", self.tag))
            elif k == "bandana":
                out.append(model("k", (0, 66 * H, 7 * W), (20 * W, 14, 3), c, (180, 0, 0), "cloth", self.tag))
            elif k == "bowtie":
                for x in (-3.5, 3.5):
                    out.append(model("s", (x, 66 * H, 8 * W), (7, 5, 3), c, None, "cloth", self.tag))
            elif k == "necklace":
                for j in range(9):
                    a = -1.2 + j * 0.3
                    out.append(model("s", (math.sin(a) * 9 * W, 62 * H - abs(math.sin(a)) * 3, math.cos(a) * 8 * W),
                                     (2.5, 2.5, 2.5), c, None, "gold" if c in ("#E8C840", "#D4AF37") else "shiny",
                                     self.tag))
        for w in self.worn("back"):
            k, c = w["kind"], w["colour"]
            if k == "backpack":
                out.append(model("c", (0, 40 * H, -18 * W), (24 * W, 30 * H, 12), c, None, "cloth", self.tag))
                out.append(model("c", (0, 30 * H, -24 * W), (18 * W, 12 * H, 4), w.get("colour2", c), None, "cloth",
                                 self.tag))
            elif k == "cape":
                out.append(model("c", (0, 24 * H, -14 * W), (34 * W, 80 * H, 2), c, (6, 0, 0), "cloth", self.tag))
        return out

    def clothes_head(self):
        out = []
        for w in self.worn("head"):
            k, c = w["kind"], w["colour"]
            c2 = w.get("colour2", c)
            if k == "cap":
                out += [model("s", (0, 9, 0), (33, 18, 32), c, None, "cloth", self.tag),
                        model("y", (0, 8, 16), (24, 1.5, 18), c2, None, "cloth", self.tag)]
            elif k == "beanie":
                out += [model("s", (0, 9, -1), (34, 22, 33), c, None, "cloth", self.tag),
                        model("s", (0, 20, -1), (7, 7, 7), c2, None, "cloth", self.tag)]
            elif k == "tophat":
                out += [model("y", (0, 15, 0), (40, 1.5, 40), c, None, "cloth", self.tag),
                        model("y", (0, 27, 0), (24, 24, 24), c, None, "cloth", self.tag),
                        model("y", (0, 18, 0), (24.5, 4, 24.5), c2, None, "cloth", self.tag)]
            elif k == "cowboy":
                out += [model("y", (0, 14, 0), (54, 1.5, 48), c, None, "cloth", self.tag),
                        model("s", (0, 18, 0), (26, 18, 24), c, None, "cloth", self.tag),
                        model("y", (0, 15.5, 0), (26.5, 3, 24.5), c2, None, "cloth", self.tag)]
            elif k == "crown":
                out.append(model("y", (0, 14, 0), (26, 5, 26), c, None, "gold", self.tag))
                for j in range(6):
                    a = j * math.pi / 3
                    out.append(model("k", (math.sin(a) * 11, 16, math.cos(a) * 11), (5, 8, 5), c, None, "gold",
                                     self.tag))
            elif k == "witch":
                out += [model("y", (0, 13, 0), (50, 1.5, 50), c, None, "cloth", self.tag),
                        model("k", (0, 13, 0), (26, 34, 26), c, (-12, 0, 0), "cloth", self.tag)]
            elif k == "headphones":
                out += [model("c", (0, 16, -1), (34, 3, 4), c, None, "shiny", self.tag)]
                for x in (-16, 16):
                    out.append(model("y", (x, 1, 0), (10, 5, 10), c2, (0, 0, 90), "shiny", self.tag))
            elif k == "flowers":
                for j in range(8):
                    a = j * math.pi / 4
                    out.append(model("s", (math.sin(a) * 15, 11, math.cos(a) * 14), (6, 5, 6),
                                     (c, c2, "#F8E870")[j % 3], None, "cloth", self.tag))
            elif k == "bow":
                for x in (-5, 5):
                    out.append(model("s", (x + 6, 13, -2), (9, 6, 4), c, (0, 0, x * 3), "cloth", self.tag))
            elif k == "halo":
                for j in range(12):
                    a = j * math.pi / 6
                    out.append(model("s", (math.sin(a) * 12, 28, math.cos(a) * 12), (4, 2, 4), c, None, "cloth",
                                     self.tag, glow=True))
            elif k == "horns":
                for x in (-1, 1):
                    out.append(node((x * 7, 12, 0), [model("k", (0, 0, 0), (5, 12, 5), c, None, "shiny", self.tag)],
                                    rot=(-10, 0, x * -15)))
        for w in self.worn("eyes"):
            k, c = w["kind"], w["colour"]
            lens = "#101418" if k == "shades" else "#C8E8F8"
            for x in (-6.5, 6.5):
                out.append(model("y", (x, 2.5, 16.5), (8.5, 1.2, 8.5), lens, (90, 0, 0), "glass", self.tag,
                                 opacity=0.85 if k == "shades" else 0.35))
                out.append(model("y", (x, 2.5, 16.4), (9.6, 0.8, 9.6), c, (90, 0, 0), "shiny", self.tag))
            out.append(model("c", (0, 3.5, 16.8), (4, 1, 1), c, None, "shiny", self.tag))
        return out

    # ---- all together ----
    def qml(self, label, title, hover=None):
        s = self.s
        H = self.H
        hip = 88 * H
        head_y = 84 * H + (6 * H if "longneck" in s["extras"] else 0)
        hs = s["head_size"]
        rig = self.torso() + self.tail() + self.wings() + [self.arm(-1), self.arm(1), self.leg(-1), self.leg(1)]
        head_rot = "Qt.vector3d(av.dance > 0 ? Math.sin(av.phase * 2) * 8 : 0, 0, 0)"
        rig.append(node((0, head_y, 0), self.head(), rot=head_rot, scale=(hs, hs, hs)))
        bounce = ("av.sitting ? -2 : av.dance === 1 ? Math.abs(Math.sin(av.phase)) * 8 : av.dance > 0 ? "
                  "Math.abs(Math.sin(av.phase * 2)) * 3 : av.walking ? Math.abs(Math.sin(av.phase)) * 2.5 : 0")
        spin = "av.dance === 4 ? av.phase * 57.3 : av.dance === 3 ? Math.sin(av.phase) * 14 : 0"
        sway = "av.dance === 2 ? Math.sin(av.phase) * 5 : 0"
        rig_node = (f"Node {{ y: {_n(hip)} + ({bounce}); eulerRotation: Qt.vector3d(av.flying ? 62 : 0, {spin}, "
                    f"{sway})\n" + "\n".join(rig) + "\n}")
        tag_y = hip + head_y + 30 * hs + 22
        text = hover or ""
        label_qml = ""
        if label or text:
            lines = []
            if title:
                lines.append('Text { anchors.horizontalCenter: parent.horizontalCenter; text: av.typing ? '
                             '"typing..." : av.title; color: "#C8E0FF"; font.pixelSize: 13; font.italic: av.typing }')
            if label:
                lines.append('Text { anchors.horizontalCenter: parent.horizontalCenter; text: av.label; '
                             'color: "white"; font.pixelSize: 18; font.bold: true }')
            if text:
                lines.append(f'Text {{ anchors.horizontalCenter: parent.horizontalCenter; text: "{esc(text)}"; '
                             'color: "#FFE9A0"; font.pixelSize: 15; horizontalAlignment: Text.AlignHCenter }')
            label_qml = (f"Node {{ y: {_n(tag_y)}; visible: av.showTag; eulerRotation.y: root.camYaw - "
                         f"av.eulerRotation.y; scale: {TAG_SCALE}\n"
                         "Rectangle { x: -width / 2; y: -height; width: col.implicitWidth + 14; "
                         "height: col.implicitHeight + 6; radius: 5; color: \"#70101820\"\n"
                         "Column { id: col; anchors.centerIn: parent\n" + "\n".join(lines) + "\n} } }")
        return f"""import QtQuick
import QtQuick3D
Node {{
    id: av
    property real phase: 0
    property real tailT: 0
    property bool walking: false
    property int dance: 0
    property bool sitting: false
    property bool flying: false
    property bool typing: false
    property bool showTag: true
    property string label: "{esc(label or '')}"
    property string title: "{esc(title or '')}"
    NumberAnimation on phase {{ from: 0; to: 6.2832; duration: av.dance > 0 ? 760 : 880; loops: Animation.Infinite;
                               running: av.walking || av.dance > 0 || av.flying }}
    NumberAnimation on tailT {{ from: 0; to: 6.2832; duration: 2600; loops: Animation.Infinite; running: true }}
    {rig_node}
    {label_qml}
}}"""


# name tags keep about the same size on screen, whatever the distance
TAG_SCALE = ("{ var dx = root.camX - av.position.x, dz = root.camZ - av.position.z; "
             "var k = Math.max(0.28, Math.min(3.0, Math.sqrt(dx * dx + dz * dz) / 900)); return Qt.vector3d(k, k, k) }")


def esc(s):
    return str(s).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def avatar_qml(s, wear=(), tag="av", label="", title="", hover=None):
    return Builder(s, list(wear), tag).qml(label, title, hover)


def height_of(s):
    return 88 * s["height"] * 2 + 30 * s["head_size"]


# ---- the bodies on offer -------------------------------------------------------------------------------------------
PRESETS = {
    "Red Fox": spec(species="Red Fox", fur="#C8642E", belly="#F4EDE2", accent="#2A2422", eyes="#C89A2A",
                    markings=["belly", "muzzle", "tailtip", "socks", "eartips"]),
    "Arctic Fox": spec(species="Arctic Fox", fur="#F2F2F2", belly="#FFFFFF", accent="#B8C0C8", eyes="#7AB8E8",
                       markings=["tailtip", "eartips"], ear_size=0.85),
    "Grey Wolf": spec(species="Grey Wolf", fur="#8A8E94", belly="#E0DED8", accent="#3A3A3E", eyes="#D8B040",
                      snout=1.2, markings=["belly", "muzzle", "saddle"], height=1.04, build=1.08),
    "Husky": spec(species="Husky", fur="#5E6672", belly="#F4F4F2", accent="#2A2C30", eyes="#7AC8F0",
                  markings=["belly", "muzzle", "mask", "socks"], build=1.08),
    "German Shepherd": spec(species="German Shepherd", fur="#B87A3A", belly="#D8A86A", accent="#1E1A18",
                            eyes="#6A4A2A", snout=1.2, ear_size=1.15, markings=["saddle", "muzzle"]),
    "Housecat": spec(species="Housecat", head="feline", ears="pointed", ear_size=0.9, tail="thin", fur="#8A8A90",
                     belly="#E8E8E8", accent="#4A4A50", eyes="#7AC850", markings=["belly", "muzzle", "stripes"],
                     extras=["whiskers"]),
    "Calico Cat": spec(species="Calico Cat", head="feline", tail="thin", fur="#F2EEE6", belly="#FFFFFF",
                       accent="#D07A30", third="#2A2420", eyes="#58B848", markings=["spots", "muzzle"],
                       extras=["whiskers"]),
    "Lion": spec(species="Lion", head="feline", ears="round", tail="thin", fur="#D8A050", belly="#F0D8A8",
                 accent="#8A4A20", eyes="#C89A2A", markings=["belly", "muzzle", "tailtip"], extras=["mane", "whiskers"],
                 height=1.06, build=1.12),
    "Tiger": spec(species="Tiger", head="feline", ears="round", tail="ringed", fur="#E07A28", belly="#F6F0E4",
                  accent="#1E1A18", eyes="#D8B040", markings=["belly", "muzzle", "stripes"], extras=["whiskers"],
                  height=1.05, build=1.1),
    "Lynx": spec(species="Lynx", head="feline", ears="tufted", tail="stub", fur="#C8A070", belly="#F0E4D0",
                 accent="#3A2E24", eyes="#A8C850", markings=["belly", "muzzle", "speckles"], extras=["whiskers"]),
    "Bunny": spec(species="Bunny", head="rodent", snout=0.4, ears="long", ear_size=1.1, tail="puff", legs="plant",
                  fur="#C8A888", belly="#F4EEE6", accent="#8A6A50", eyes="#5A3A2A", nose="#E89AA8",
                  markings=["belly", "muzzle"], height=0.94),
    "Dragon": spec(species="Dragon", head="reptile", snout=1.0, ears="fin", tail="thick", tail_size=1.3,
                   wings="bat", horns="dragon", fur="#3A6A4A", belly="#D8C890", accent="#24402E", eyes="#E8B030",
                   horn="#E8DCC0", surface="scales", markings=["belly"], height=1.1, build=1.15),
    "Gryphon": spec(species="Gryphon", head="bird", snout=1.1, ears="pointed", ear_size=0.7, tail="thin",
                    wings="feather", fur="#B8884A", belly="#F4F0E8", accent="#5A3A20", nose="#E8B030",
                    eyes="#D89020", surface="feathers", markings=["belly", "tailtip"]),
    "Songbird": spec(species="Songbird", head="bird", snout=0.7, ears="none", tail="feathers", legs="plant",
                     wings="feather", fur="#4A8AD8", belly="#F0E0C0", accent="#2A4A8A", nose="#3A3A3A",
                     eyes="#202020", surface="feathers", markings=["belly"], extras=["crest"], height=0.92),
    "Deer": spec(species="Deer", head="deer", ears="pointed", ear_size=1.2, tail="puff", legs="hoof", horns="antlers",
                 fur="#A8703A", belly="#F4E8D8", accent="#5A3A20", eyes="#3A2A1A", markings=["belly", "muzzle"],
                 height=1.06),
    "Bear": spec(species="Bear", head="ursine", snout=0.8, ears="round", tail="stub", legs="plant", fur="#6A4A30",
                 belly="#A87A50", accent="#3A2A1A", eyes="#2A1A10", markings=["muzzle"], height=1.12, build=1.35),
    "Otter": spec(species="Otter", head="ursine", snout=0.5, ears="small", tail="thick", tail_size=0.8, legs="plant",
                  fur="#6A4A34", belly="#C8A888", accent="#4A3424", eyes="#1A1410",
                  markings=["belly", "muzzle"], extras=["whiskers"], height=0.95),
    "Raccoon": spec(species="Raccoon", head="canine", snout=0.6, ears="round", tail="ringed", fur="#8A8A8A",
                    belly="#D8D8D0", accent="#2A2A2A", eyes="#2A2A2A", markings=["mask", "muzzle", "socks"]),
    "Skunk": spec(species="Skunk", head="canine", snout=0.7, ears="round", tail="fluffy", tail_size=1.3,
                  fur="#1E1E22", belly="#1E1E22", accent="#F4F4F0", eyes="#2A2A2A", markings=["blaze", "tailtip"]),
    "Kangaroo": spec(species="Kangaroo", head="deer", snout=0.6, ears="long", ear_size=0.8, tail="thick",
                     tail_size=1.2, legs="digi", fur="#B8784A", belly="#E8D0B0", accent="#5A3A20",
                     eyes="#2A1A10", markings=["belly", "muzzle", "eartips"], height=1.05),
    "Frog": spec(species="Frog", head="amphibian", ears="none", tail=None, legs="plant", fur="#4AA86A",
                 belly="#E8E0A0", accent="#2A6A3A", eyes="#E8A020", surface="skin", markings=["belly"],
                 height=0.92),
    "Shark": spec(species="Shark", head="fish", ears="none", tail="fin", legs="plant", fur="#6A7A8A",
                  belly="#F0F0EC", accent="#4A5A6A", eyes="#101010", surface="skin", markings=["belly"],
                  extras=["fins"], height=1.08, build=1.15),
}
BODY_ORDER = list(PRESETS)
