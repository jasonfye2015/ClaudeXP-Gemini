"""Everything the Bazaar gives away (it's all free): furry bodies, clothes, accessories and things to rez - and the
QML for objects and scenery, which are lists of prims.

A prim is (shape, (x, y, z), (w, h, d), colour, options): shape "s" sphere, "c" cube, "y" cylinder, "k" cone (base
at y), "t" floating text; sizes in centimetres; options may have rot, surface, glow, opacity, anim ("flicker",
"spin", "bob", "rainbow", "pulse") and phase."""
import math

from .avatar import BODY_ORDER, PRESETS, SHAPES, esc, material, vec

ITEMS = {}          # key -> item


def _add(key, name, kind, **kw):
    ITEMS[key] = dict(key=key, name=name, kind=kind, **kw)


# ---- bodies ----
for _name in BODY_ORDER:
    _add(f"body:{_name}", f"{_name} Body", "body", spec=PRESETS[_name], booth="Bodies")

# ---- clothes: (key, name, slot, kind, colour, colour2) ----
CLOTHES = [
    ("tee-white", "White T-Shirt", "torso", "tshirt", "#F0EEE8", None),
    ("tee-black", "Black Band Tee", "torso", "tshirt", "#26262A", None),
    ("tee-red", "Red T-Shirt", "torso", "tshirt", "#C83A34", None),
    ("tee-sky", "Sky Blue T-Shirt", "torso", "tshirt", "#7AB8E8", None),
    ("hoodie-grey", "Grey Hoodie", "torso", "hoodie", "#8A8E94", "#6A6E74"),
    ("hoodie-blue", "Blue Hoodie", "torso", "hoodie", "#3A5A9A", "#2A3A6A"),
    ("hoodie-purple", "Purple Paw Hoodie", "torso", "hoodie", "#7A4FA8", "#E8C8F0"),
    ("jacket-leather", "Leather Jacket", "torso", "jacket", "#2A2420", "#C8C0B0"),
    ("jacket-denim", "Denim Jacket", "torso", "jacket", "#4A6A9A", "#E8E8E0"),
    ("tank-white", "White Tank Top", "torso", "tanktop", "#F0F0EC", None),
    ("tank-pink", "Pink Tank Top", "torso", "tanktop", "#E88AB0", None),
    ("sweater", "Cozy Sweater", "torso", "longsleeve", "#E8D8B8", None),
    ("flannel", "Red Flannel Shirt", "torso", "longsleeve", "#A83A30", None),
    ("vest", "Formal Vest", "torso", "vest", "#2A2A30", None),
    ("dress-sun", "Sundress", "torso", "dress", "#F2D24A", None),
    ("dress-red", "Evening Dress", "torso", "dress", "#B0203A", None),
    ("jeans-blue", "Blue Jeans", "legs", "jeans", "#3A5A8A", None),
    ("jeans-black", "Black Jeans", "legs", "jeans", "#26262C", None),
    ("shorts-cargo", "Cargo Shorts", "legs", "shorts", "#A8986A", None),
    ("pants-track", "Track Pants", "legs", "pants", "#2A2A3A", None),
    ("skirt-plaid", "Plaid Skirt", "legs", "skirt", "#B03A4A", None),
    ("skirt-pink", "Pink Skirt", "legs", "skirt", "#F0A0C8", None),
    ("sneakers", "Sneakers", "feet", "boots", "#F4F4F4", None),
    ("boots", "Work Boots", "feet", "boots", "#6A4A2A", None),
]
for _k, _n, _slot, _kind, _c, _c2 in CLOTHES:
    _add(f"cloth:{_k}", _n, "clothing", slot=_slot, look=_kind, colour=_c, colour2=_c2 or _c, booth="Clothing")

ACCESSORIES = [
    ("cap-red", "Red Ball Cap", "head", "cap", "#C83A34", "#A82A24"),
    ("cap-blue", "Blue Ball Cap", "head", "cap", "#3A5AA8", "#2A3A7A"),
    ("beanie", "Green Beanie", "head", "beanie", "#4A8A4A", "#F0F0E8"),
    ("tophat", "Top Hat", "head", "tophat", "#1E1E22", "#8A2A2A"),
    ("cowboy", "Cowboy Hat", "head", "cowboy", "#8A6038", "#3A2A1A"),
    ("crown", "Golden Crown", "head", "crown", "#E8C840", None),
    ("witch", "Witch Hat", "head", "witch", "#4A2A6A", None),
    ("headphones", "Headphones", "head", "headphones", "#2A2A2E", "#4AD8E8"),
    ("flowers", "Flower Crown", "head", "flowers", "#F08AB0", "#FFFFFF"),
    ("bow", "Hair Bow", "head", "bow", "#F06AA0", None),
    ("halo", "Halo", "head", "halo", "#FFE68A", None),
    ("devil", "Devil Horns", "head", "horns", "#C02A2A", None),
    ("glasses", "Round Glasses", "eyes", "glasses", "#C8A040", None),
    ("shades", "Sunglasses", "eyes", "shades", "#1A1A1E", None),
    ("nerd", "Nerd Glasses", "eyes", "glasses", "#1A1A1E", None),
    ("collar-red", "Collar with Bell", "neck", "collar", "#C02A2A", "#E8C840"),
    ("collar-blue", "Blue Collar with Tag", "neck", "collar", "#2A5AB0", "#D0D0D8"),
    ("collar-black", "Black Collar", "neck", "collar", "#1A1A1E", "#C0C0C8"),
    ("scarf", "Striped Scarf", "neck", "scarf", "#C83A34", None),
    ("bandana", "Red Bandana", "neck", "bandana", "#C02A2A", None),
    ("bowtie", "Bow Tie", "neck", "bowtie", "#1E1E22", None),
    ("pearls", "Pearl Necklace", "neck", "necklace", "#F4F0E8", None),
    ("chain", "Gold Chain", "neck", "necklace", "#E8C840", None),
    ("backpack", "Backpack", "back", "backpack", "#E8783A", "#3A3A3A"),
    ("angel", "Angel Wings", "back", "angel wings", "#FFFFFF", "#E8E8F0"),
    ("fairy", "Fairy Wings", "back", "fairy wings", "#C8E8FF", None),
    ("batwings", "Bat Wings", "back", "bat wings", "#2A2228", "#4A3A42"),
    ("cape", "Hero Cape", "back", "cape", "#B02A2A", None),
    ("bangles", "Gold Bangles", "wrist", "bangle", "#E8C840", None),
    ("wristband", "Spiked Wristband", "wrist", "band", "#1E1E22", None),
]
for _k, _n, _slot, _kind, _c, _c2 in ACCESSORIES:
    _add(f"acc:{_k}", _n, "accessory", slot=_slot, look=_kind, colour=_c, colour2=_c2 or _c, booth="Accessories")


def worn_piece(item, colour=None):
    """What the avatar builder needs to draw something worn."""
    return {"slot": item["slot"], "kind": item["look"], "colour": colour or item["colour"],
            "colour2": item.get("colour2") or item["colour"]}


# ---- things to rez ----
def P(shape, pos, size, colour, **opts):
    return (shape, pos, size, colour, opts)


OBJECTS = {
    "chair": ("Wooden Chair", [P("c", (0, 44, 0), (48, 6, 46), "#8A5A34"), P("c", (0, 76, -21), (48, 60, 6), "#8A5A34")]
              + [P("c", (x, 22, z), (5, 44, 5), "#6A4424") for x in (-20, 20) for z in (-19, 19)],
              {"sit": (0, 47, 2, 0)}),
    "sofa": ("Comfy Sofa", [P("c", (0, 30, 0), (180, 34, 80), "#7A4A8A", surface="cloth"),
                            P("c", (0, 70, -34), (180, 56, 16), "#6A3A7A", surface="cloth"),
                            P("c", (-86, 50, 0), (16, 40, 80), "#6A3A7A", surface="cloth"),
                            P("c", (86, 50, 0), (16, 40, 80), "#6A3A7A", surface="cloth"),
                            P("c", (-40, 50, 2), (76, 10, 70), "#8A5A9A", surface="cloth"),
                            P("c", (40, 50, 2), (76, 10, 70), "#8A5A9A", surface="cloth")],
             {"sit": (-40, 55, 10, 0), "sit2": (40, 55, 10, 0)}),
    "beanbag": ("Beanbag", [P("s", (0, 26, 0), (90, 52, 90), "#E8783A", surface="cloth")], {"sit": (0, 36, 8, 0)}),
    "table": ("Round Table", [P("y", (0, 74, 0), (110, 5, 110), "#8A5A34"), P("y", (0, 37, 0), (10, 72, 10), "#5A3A1A"),
                              P("y", (0, 2, 0), (60, 4, 60), "#5A3A1A")], {}),
    "lamp": ("Floor Lamp", [P("y", (0, 2, 0), (40, 4, 40), "#2A2A2A"), P("y", (0, 80, 0), (4, 160, 4), "#2A2A2A"),
                            P("k", (0, 150, 0), (50, 36, 50), "#FFE8B0", glow=True, rot=(0, 0, 0))], {}),
    "palm": ("Palm Tree", [P("y", (math.sin(k * 0.25) * 12, 30 + k * 60, 0), (22 - k * 2, 64, 22 - k * 2), "#8A6A44")
                           for k in range(6)]
             + [P("s", (math.sin(a) * 90 + 25, 370, math.cos(a) * 90), (220, 10, 50), "#3A8A3A",
                  rot=(0, math.degrees(a) + 90, -18)) for a in [k * math.pi / 3.5 for k in range(7)]]
             + [P("s", (30 + dx, 348, dz), (18, 18, 18), "#6A4A24") for dx, dz in ((8, 6), (-6, 8), (2, -8))], {}),
    "pine": ("Pine Tree", [P("y", (0, 40, 0), (30, 80, 30), "#5A3A1A")]
             + [P("k", (0, 60 + k * 90, 0), (260 - k * 60, 150, 260 - k * 60), "#2A5A34") for k in range(4)], {}),
    "campfire": ("Campfire", [P("y", (0, 8, 0), (14, 90, 14), "#5A3A1A", rot=(90, k * 60, 0)) for k in range(3)]
                 + [P("k", (math.sin(k * 2.1) * 10, 6, math.cos(k * 2.1) * 10), (30 - k * 6, 50 + k * 10, 30 - k * 6),
                      ("#FF7A1A", "#FFB030", "#FFE070")[k], glow=True, anim="flicker", phase=k) for k in range(3)]
                 + [P("s", (math.sin(a) * 34, 6, math.cos(a) * 34), (16, 12, 16), "#7A7A72")
                    for a in [k * math.pi / 5 for k in range(10)]], {}),
    "plushfox": ("Fox Plushie", [P("s", (0, 18, 0), (30, 32, 26), "#E07A2E", surface="cloth"),
                                 P("s", (0, 18, 8), (18, 22, 14), "#F4EEE6", surface="cloth"),
                                 P("s", (0, 44, 2), (30, 26, 26), "#E07A2E", surface="cloth"),
                                 P("s", (0, 40, 16), (14, 11, 16), "#F4EEE6", surface="cloth"),
                                 P("s", (0, 42, 24), (5, 4, 4), "#1A1A1A"),
                                 P("k", (-9, 52, 0), (9, 14, 4), "#E07A2E", rot=(0, 0, 14)),
                                 P("k", (9, 52, 0), (9, 14, 4), "#E07A2E", rot=(0, 0, -14)),
                                 P("s", (0, 14, -22), (16, 16, 26), "#E07A2E", surface="cloth"),
                                 P("s", (0, 18, -34), (12, 12, 14), "#F4EEE6", surface="cloth"),
                                 P("s", (-6, 47, 13), (4, 4, 3), "#1A1A1A"), P("s", (6, 47, 13), (4, 4, 3), "#1A1A1A")],
                 {}),
    "beachball": ("Beach Ball", [P("s", (0, 40, 0), (80, 80, 80), "#F4F4F0", surface="shiny", anim="spin")]
                  + [P("s", (0, 40, 0), (80.6, 80.6, 18), c, surface="shiny", rot=(0, k * 60, 0), anim="spin")
                     for k, c in enumerate(("#E83A3A", "#3A7AE8", "#F2C230"))], {}),
    "duck": ("Rubber Duck", [P("s", (0, 18, 0), (40, 30, 48), "#F2D23A", surface="shiny"),
                             P("s", (0, 40, 12), (26, 26, 26), "#F2D23A", surface="shiny"),
                             P("s", (0, 37, 27), (16, 6, 14), "#F0782A", surface="shiny"),
                             P("s", (-7, 45, 22), (4, 4, 4), "#1A1A1A"), P("s", (7, 45, 22), (4, 4, 4), "#1A1A1A")], {}),
    "chest": ("Treasure Chest", [P("c", (0, 24, 0), (90, 48, 56), "#8A5A30"), P("y", (0, 50, 0), (56, 90, 56), "#9A6A3A",
                                                                                  rot=(0, 0, 90)),
                                 P("c", (0, 30, 29), (14, 18, 4), "#E8C840", surface="gold")], {}),
    "danceball": ("Dance Ball", [P("s", (0, 0, 0), (34, 34, 34), "#E85AE8", glow=True, anim="rainbow"),
                                 P("t", (0, 34, 0), (1, 1, 1), "#FFE9A0", text="Dance! (click)")],
                  {"dance": 0, "hover": 140}),
    "neon": ("Neon Sign", [P("c", (0, 60, 0), (200, 80, 8), "#1A1A22"),
                           P("t", (0, 84, 6), (2.2, 2.2, 2.2), "#FF5AD8", text="OPEN")], {}),
    "snowman": ("Snowman", [P("s", (0, 36, 0), (72, 70, 72), "#F8F8FA", surface="cloth"),
                            P("s", (0, 92, 0), (54, 52, 54), "#F8F8FA", surface="cloth"),
                            P("s", (0, 136, 0), (40, 38, 40), "#F8F8FA", surface="cloth"),
                            P("k", (0, 136, 18), (8, 22, 8), "#F07A2A", rot=(90, 0, 0)),
                            P("y", (0, 160, 0), (34, 26, 34), "#1A1A1A"), P("y", (0, 148, 0), (52, 2, 52), "#1A1A1A"),
                            P("s", (-7, 142, 17), (5, 5, 5), "#1A1A1A"), P("s", (7, 142, 17), (5, 5, 5), "#1A1A1A")], {}),
    "crate": ("Wooden Crate", [P("c", (0, 30, 0), (60, 60, 60), "#A8824E")], {}),
    "barrel": ("Barrel", [P("y", (0, 45, 0), (60, 90, 60), "#8A5A30"), P("y", (0, 20, 0), (62, 6, 62), "#4A4A4A"),
                          P("y", (0, 70, 0), (62, 6, 62), "#4A4A4A")], {}),
    "rug": ("Round Rug", [P("y", (0, 1, 0), (240, 2, 240), "#A83A4A", surface="cloth"),
                          P("y", (0, 2, 0), (160, 2, 160), "#E8C870", surface="cloth")], {}),
    "bed": ("Double Bed", [P("c", (0, 24, 0), (160, 30, 210), "#6A4424"), P("c", (0, 44, 6), (150, 14, 196), "#F0F0EC",
                                                                             surface="cloth"),
                           P("c", (0, 50, 30), (150, 6, 140), "#4A6EA8", surface="cloth"),
                           P("c", (-40, 54, -80), (60, 14, 34), "#FFFFFF", surface="cloth"),
                           P("c", (40, 54, -80), (60, 14, 34), "#FFFFFF", surface="cloth"),
                           P("c", (0, 70, -104), (160, 90, 8), "#6A4424")], {"sit": (0, 52, 0, 0)}),
    "flowerpot": ("Flower Pot", [P("y", (0, 18, 0), (40, 36, 40), "#B8643A")]
                  + [P("s", (math.sin(k * 1.3) * 12, 46 + (k % 3) * 6, math.cos(k * 1.3) * 12), (14, 14, 14),
                       ("#F08AB0", "#F2D24A", "#E85A5A", "#B08AF0")[k % 4]) for k in range(7)]
                  + [P("y", (0, 34, 0), (3, 24, 3), "#3A7A3A")], {}),
    "lantern": ("Paper Lantern", [P("s", (0, 160, 0), (40, 50, 40), "#FFB060", glow=True, anim="pulse"),
                                  P("y", (0, 80, 0), (3, 160, 3), "#3A3A3A")], {}),
    "sign": ("Sign Post", [P("y", (0, 70, 0), (8, 140, 8), "#6A4424"), P("c", (0, 130, 0), (110, 50, 6), "#8A5A34"),
                           P("t", (0, 146, 4), (1.3, 1.3, 1.3), "#FFFFFF", text="Hello!")], {"text": True}),
    "cube": ("Plywood Cube", [P("c", (0, 50, 0), (100, 100, 100), "#C8B088")], {"basic": True}),
    "sphere": ("Sphere", [P("s", (0, 50, 0), (100, 100, 100), "#C8B088")], {"basic": True}),
    "cylinder": ("Cylinder", [P("y", (0, 50, 0), (100, 100, 100), "#C8B088")], {"basic": True}),
    "cone": ("Cone", [P("k", (0, 0, 0), (100, 100, 100), "#C8B088")], {"basic": True}),
}
for _k, (_n, _prims, _info) in OBJECTS.items():
    _add(f"obj:{_k}", _n, "object", obj=_k, booth="Basics" if _info.get("basic") else "Home & Garden")


def by_booth(booth):
    return [i for i in ITEMS.values() if i.get("booth") == booth]


# ---- QML for prims, objects and scenery ----
def prim_qml(p, tag=None, tint=None, sel=False):
    shape, pos, size, colour, o = p
    if tint:
        colour = tint
    if shape == "t":
        sc = size[0]
        return (f"Node {{ position: {vec(*pos)}; eulerRotation.y: root.camYaw; scale: Qt.vector3d({sc}, {sc}, {sc})\n"
                f'Text {{ x: -width / 2; y: -height; text: "{esc(o.get("text", ""))}"; color: "{colour}"; '
                f'font.pixelSize: 20; font.bold: true; horizontalAlignment: Text.AlignHCenter; style: Text.Outline; '
                f'styleColor: "#000000" }} }}')
    sx, sy, sz = (v / 100 for v in size)
    anim = o.get("anim")
    ph = o.get("phase", 0)
    if anim == "flicker":
        scale = f"Qt.vector3d({sx}, {sy} * (1 + 0.18 * Math.sin(root.t * 11 + {ph * 2.1})), {sz})"
    elif anim == "pulse":
        scale = f"Qt.vector3d({sx} * (1 + 0.04 * Math.sin(root.t * 3)), {sy}, {sz} * (1 + 0.04 * Math.sin(root.t * 3)))"
    else:
        scale = vec(sx, sy, sz)
    rot = o.get("rot")
    if anim == "spin":
        r = rot or (0, 0, 0)
        rot_s = f"eulerRotation: Qt.vector3d({r[0]}, {r[1]} + root.t * 40, {r[2]}); "
    else:
        rot_s = f"eulerRotation: {vec(*rot)}; " if rot else ""
    if anim == "bob":
        pos_s = f"position: Qt.vector3d({pos[0]}, {pos[1]} + Math.sin(root.t * 2) * 8, {pos[2]}); "
    else:
        pos_s = f"position: {vec(*pos)}; "
    colour_expr = None
    if anim == "rainbow":
        colour_expr = f"Qt.hsla((root.t * 0.15 + {ph * 0.13}) % 1, 0.85, 0.55, 1)"
    out = f'Model {{ source: "{SHAPES[shape]}"; {pos_s}scale: {scale}; {rot_s}'
    if tag:
        out += f'objectName: "{tag}"; pickable: true; '
    mat = material(colour, o.get("surface", "fur" if shape == "s" else "cloth"), o.get("opacity"),
                   o.get("glow", False), colour_expr)
    if sel:
        mat = mat[:-2] + "; emissiveFactor: Qt.vector3d(0.25, 0.2, 0.02) }"
    return out + f"materials: {mat} }}"


def object_qml(inst, tag, selected=False):
    """A rezzed object (an instance of an OBJECTS entry), as a Node at the origin; the world places it."""
    name, prims, info = OBJECTS[inst["obj"]]
    tint = inst.get("colour") if info.get("basic") else None
    parts = []
    for p in prims:
        if p[0] == "t" and inst.get("text") is not None:
            p = (p[0], p[1], p[2], p[3], dict(p[4], text=inst["text"]))
        parts.append(prim_qml(p, tag, tint if p[0] != "t" else None, selected))
    hover = inst.get("hover")
    if hover:
        parts.append(prim_qml(P("t", (0, info.get("hover", 120), 0), (1.1, 1.1, 1.1), "#FFE9A0", text=hover)))
    sc = inst.get("scale", 1.0)
    return ("import QtQuick\nimport QtQuick3D\n"
            f"Node {{ scale: Qt.vector3d({sc}, {sc}, {sc})\n" + "\n".join(parts) + "\n}")


def scenery_qml(prims, tagged=()):
    """A whole region's scenery as one Node. tagged: {index: tag} for the prims you can click."""
    tagged = dict(tagged)
    return ("import QtQuick\nimport QtQuick3D\nNode {\n" +
            "\n".join(prim_qml(p, tagged.get(i)) for i, p in enumerate(prims)) + "\n}")
