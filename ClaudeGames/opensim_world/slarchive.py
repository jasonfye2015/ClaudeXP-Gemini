"""Fox Valley: the user's own Second Life creations, brought home. Firestorm's backups (.oxp, in Local Storage/Second
Life Export) are turned into an OpenSim Archive for one region - the builds and signs from the Valley sims set out
on an island, the snapshots and textures hung in galleries, and the boxes of scripts, sounds and notecards on tables
in the archive vault - which content.py loads the first time the world starts with it in place.

An .oxp is zlib-compressed binary LLSD: {"linkset": [[root, child...], ...], "prim": {id: prim}, "asset": {id: asset},
"inventory": {item id: item}}. Only what the user made is in it (Firestorm checks), so a texture someone else made
isn't: faces that used one fall back to the plain white texture, keeping their colour."""
import base64
import io
import math
import struct
import tarfile
import time
import uuid
import zlib
from pathlib import Path
from xml.sax.saxutils import escape

REGION = "Fox Valley"
NS = uuid.UUID("3f6c2b1e-9d4a-4e7b-8c55-1a2b3c4d5e6f")
FULL = 2147483647
ZERO = "00000000-0000-0000-0000-000000000000"
BLANK = "5748decc-f629-461c-9a36-a35a221fe21f"      # in OpenSim's own library, like the next two
PLYWOOD = "89556747-24cb-43ed-920b-47caed15465f"
TRANSPARENT = "8dcd4a48-2d37-4909-9f78-f7a9eb4ef903"
LIBRARY = {BLANK, PLYWOOD, TRANSPARENT}
GROUND = 22.0                                       # the island's height; the water is at 20
WATER = 20.0


def source():
    from . import root
    return root().parent / "Second Life Export"


def target():
    from . import root
    return root() / "downloads" / "archive" / f"{REGION}.tgz"


# ---- reading a backup ---------------------------------------------------------------------------------------------
def _llsd(b, i=0):
    """One value of binary LLSD at b[i:] -> (value, next i)."""
    t = b[i:i + 1]
    i += 1
    if t == b"!":
        return None, i
    if t in (b"1", b"0"):
        return t == b"1", i
    if t == b"i":
        return struct.unpack(">i", b[i:i + 4])[0], i + 4
    if t in (b"r", b"d"):
        return struct.unpack(">d", b[i:i + 8])[0], i + 8
    if t == b"u":
        return str(uuid.UUID(bytes=b[i:i + 16])), i + 16
    if t in (b"b", b"s", b"l"):
        n = struct.unpack(">I", b[i:i + 4])[0]
        v = b[i + 4:i + 4 + n]
        return (v if t == b"b" else v.decode("utf-8", "replace")), i + 4 + n
    if t == b"[":
        n = struct.unpack(">I", b[i:i + 4])[0]
        i += 4
        out = []
        for _ in range(n):
            v, i = _llsd(b, i)
            out.append(v)
        return out, i + 1                           # "]"
    if t == b"{":
        n = struct.unpack(">I", b[i:i + 4])[0]
        i += 4
        out = {}
        for _ in range(n):
            kl = struct.unpack(">I", b[i + 1:i + 5])[0]  # "k" + length + key
            k = b[i + 5:i + 5 + kl].decode()
            v, i = _llsd(b, i + 5 + kl)
            out[k] = v
        return out, i + 1                           # "}"
    raise ValueError(f"unknown LLSD type {t!r} at {i - 1}")


def read(path):
    data, _ = _llsd(zlib.decompress(Path(path).read_bytes()))
    return data


# ---- geometry -----------------------------------------------------------------------------------------------------
def qmul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw, aw * bw - ax * bx - ay * by - az * bz)


def qrot(q, v):
    """v rotated by q."""
    x, y, z, w = q
    vx, vy, vz = v
    tx, ty, tz = 2 * (y * vz - z * vy), 2 * (z * vx - x * vz), 2 * (x * vy - y * vx)
    return (vx + w * tx + (y * tz - z * ty), vy + w * ty + (z * tx - x * tz), vz + w * tz + (x * ty - y * tx))


def zrot(deg):
    a = math.radians(deg) / 2
    return (0.0, 0.0, math.sin(a), math.cos(a))


def bounds(data):
    """(min xyz, max xyz) of every prim, where it was rezzed."""
    prims = data["prim"]
    lo, hi = [1e9] * 3, [-1e9] * 3
    for linkset in data["linkset"]:
        root = prims[linkset[0]]
        rp, rr = root["position"], root["rotation"]
        for pid in linkset:
            p = prims[pid]
            if pid == linkset[0]:
                c, rot = rp, rr
            else:
                off = qrot(rr, p["position"])
                c, rot = [rp[k] + off[k] for k in range(3)], qmul(rr, p["rotation"])
            half = [s / 2 for s in p["scale"]]
            for sx in (-1, 1):
                for sy in (-1, 1):
                    for sz in (-1, 1):
                        d = qrot(rot, (sx * half[0], sy * half[1], sz * half[2]))
                        for k in range(3):
                            lo[k] = min(lo[k], c[k] + d[k])
                            hi[k] = max(hi[k], c[k] + d[k])
    return lo, hi


def _world(data, linkset):
    """[(prim, world position, world rotation)] for one linkset."""
    prims = data["prim"]
    root = prims[linkset[0]]
    rp, rr = root["position"], root["rotation"]
    out = [(root, list(rp), tuple(rr))]
    for pid in linkset[1:]:
        p = prims[pid]
        off = qrot(rr, p["position"])
        out.append((p, [rp[k] + off[k] for k in range(3)], qmul(rr, p["rotation"])))
    return out


def base(data):
    """The height the build stands on: its lowest prims, unless only a stray few (a sunk wall) are far below the rest."""
    bottoms = sorted(pos[2] - sum(abs(qrot(rot, ax)[2]) * p["scale"][i] / 2
                                  for i, ax in enumerate(((1, 0, 0), (0, 1, 0), (0, 0, 1))))
                     for ls in data["linkset"] for p, pos, rot in _world(data, ls))
    stray = max(1, len(bottoms) // 30)
    if len(bottoms) > 10 and bottoms[stray] - bottoms[0] > 2:
        return bottoms[stray]
    return bottoms[0]


SIDES = {1: (0, -1, 0), 2: (1, 0, 0), 3: (0, 1, 0), 4: (-1, 0, 0)}     # a plain box's side faces


def facing(data):
    """Which way a sign's pictures face (degrees, 0 = east, 90 = north), or None for something flat: the side of its
    plain boxes most covered in the user's own textures."""
    own = set(data.get("asset", {}))
    bins, top = [0.0] * 4, 0.0
    for ls in data["linkset"]:
        for p, _pos, rot in _world(data, ls):
            vol = p.get("volume", {})
            if vol.get("profile", {}).get("curve", 1) & 0x0F != 1 or vol.get("path", {}).get("curve", 16) != 16:
                continue
            sx, sy, sz = p["scale"]
            faces = p.get("texture", [])
            for f, n in list(SIDES.items()) + [(0, (0, 0, 1))]:
                if f >= len(faces) or faces[f].get("imageid") not in own:
                    continue
                area = sx * sy if f == 0 else (sx if n[0] == 0 else sy) * sz
                w = qrot(rot, n)
                if abs(w[2]) > 0.7:
                    top += area
                    continue
                a = math.degrees(math.atan2(w[1], w[0])) % 360
                bins[int(((a + 45) % 360) // 90)] += area
    if max(bins) <= 0 or top > 2 * max(bins):
        return None
    return 90.0 * bins.index(max(bins))


def signature(data):
    """Two backups of the same thing (one rezzed twice) have the same shapes and textures."""
    return tuple(sorted((tuple(round(s, 2) for s in p["scale"]), tuple(t.get("imageid") for t in p.get("texture", [])))
                        for p in data["prim"].values()))


def j2c_size(data):
    """(width, height) of a JPEG 2000 codestream, from its SIZ marker."""
    i = data.find(b"\xff\x51")
    if i < 0:
        return None
    w, h, x0, y0 = struct.unpack(">IIII", data[i + 6:i + 22])
    return (w - x0, h - y0) if w > x0 and h > y0 else None


# ---- writing OpenSim's objects ------------------------------------------------------------------------------------
def _face_bits(mask):
    n, m = 0, mask
    while m:
        m >>= 7
        n += 1
    return bytes(((mask >> (7 * (n - i - 1))) & 0x7F) | (0x80 if i < n - 1 else 0) for i in range(n))


def texture_entry(faces):
    """The packed TextureEntry for a list of faces ({imageid, colors, scales, scalet, offsets, offsett, imagerot,
    bump, fullbright, glow, media_flags}), as the viewer sends it: each field's default (face 0's), then the faces
    that differ, by bitfield, then a 0."""
    def fields(f):
        c = f.get("colors", [1, 1, 1, 1])
        rot = math.remainder(f.get("imagerot", 0.0), 2 * math.pi) / (2 * math.pi) * 32768
        return [uuid.UUID(f.get("imageid") or BLANK).bytes,
                bytes(255 - max(0, min(255, round(v * 255))) for v in c),
                struct.pack("<f", f.get("scales", 1.0)), struct.pack("<f", f.get("scalet", 1.0)),
                struct.pack("<h", max(-32767, min(32767, round(f.get("offsets", 0.0) * 32767)))),
                struct.pack("<h", max(-32767, min(32767, round(f.get("offsett", 0.0) * 32767)))),
                struct.pack("<h", max(-32768, min(32767, round(rot)))),
                bytes([(f.get("bump", 0) & 0xDF) | (0x20 if f.get("fullbright") else 0)]),
                bytes([f.get("media_flags", 0) & 0xFF]),
                bytes([max(0, min(255, round(f.get("glow", 0.0) * 255)))]),
                bytes(16)]
    rows = [fields(f) for f in faces] or [fields({})]
    out = bytearray()
    for k in range(len(rows[0])):
        default = rows[0][k]
        out += default
        groups = {}
        for i, r in enumerate(rows[1:], 1):
            if r[k] != default:
                groups[r[k]] = groups.get(r[k], 0) | (1 << i)
        for value, mask in groups.items():
            out += _face_bits(mask) + value
        out += b"\x00"
    return bytes(out)


def _uuid(tag, value):
    return f"<{tag}><UUID>{value}</UUID></{tag}>"


def _vec(tag, v):
    return f"<{tag}><X>{v[0]:.6f}</X><Y>{v[1]:.6f}</Y><Z>{v[2]:.6f}</Z></{tag}>"


def _quat(tag, q):
    return f"<{tag}><X>{q[0]:.7f}</X><Y>{q[1]:.7f}</Y><Z>{q[2]:.7f}</Z><W>{q[3]:.7f}</W></{tag}>"


def _sbyte(v):
    return max(-128, min(127, round(v)))


def _shape(vol, scale, te):
    """The packed shape, from the viewer's volume parameters (what libOpenMetaverse's Pack* functions do)."""
    path, prof = vol.get("path", {}), vol.get("profile", {})
    q = 0.00002
    return ("<Shape>" f"<ProfileCurve>{prof.get('curve', 1)}</ProfileCurve>"
            f"<TextureEntry>{base64.b64encode(te).decode()}</TextureEntry><ExtraParams>AA==</ExtraParams>"
            f"<PathBegin>{round(path.get('begin', 0) / q)}</PathBegin><PathCurve>{path.get('curve', 16)}</PathCurve>"
            f"<PathEnd>{50000 - round(path.get('end', 1) / q)}</PathEnd>"
            f"<PathRadiusOffset>{_sbyte(path.get('radius_offset', 0) / 0.01)}</PathRadiusOffset>"
            f"<PathRevolutions>{max(0, min(255, round((path.get('revolutions', 1) - 1) / 0.015)))}</PathRevolutions>"
            f"<PathScaleX>{max(0, min(255, 200 - round(path.get('scale_x', 1) / 0.01)))}</PathScaleX>"
            f"<PathScaleY>{max(0, min(255, 200 - round(path.get('scale_y', 1) / 0.01)))}</PathScaleY>"
            f"<PathShearX>{_sbyte(path.get('shear_x', 0) / 0.01) & 0xFF}</PathShearX>"
            f"<PathShearY>{_sbyte(path.get('shear_y', 0) / 0.01) & 0xFF}</PathShearY>"
            f"<PathSkew>{_sbyte(path.get('skew', 0) / 0.01)}</PathSkew>"
            f"<PathTaperX>{_sbyte(path.get('taper_x', 0) / 0.01)}</PathTaperX>"
            f"<PathTaperY>{_sbyte(path.get('taper_y', 0) / 0.01)}</PathTaperY>"
            f"<PathTwist>{_sbyte(path.get('twist', 0) / 0.01)}</PathTwist>"
            f"<PathTwistBegin>{_sbyte(path.get('twist_begin', 0) / 0.01)}</PathTwistBegin>"
            f"<PCode>9</PCode><ProfileBegin>{round(prof.get('begin', 0) / q)}</ProfileBegin>"
            f"<ProfileEnd>{50000 - round(prof.get('end', 1) / q)}</ProfileEnd>"
            f"<ProfileHollow>{round(prof.get('hollow', 0) / q)}</ProfileHollow><State>0</State>"
            + _vec("Scale", scale) + "</Shape>")


# asset type, file ending in an OAR
ASSET_TYPES = {"texture": (0, "_texture.jp2"), "sound": (1, "_sound.ogg"), "landmark": (3, "_landmark.txt"),
               "clothing": (5, "_clothing.txt"), "notecard": (7, "_notecard.txt"), "lsltext": (10, "_script.lsl"),
               "bodypart": (13, "_bodypart.txt"), "animatn": (20, "_animation.bvh"), "gesture": (21, "_gesture.txt")}
INV_TYPES = {"texture": 0, "sound": 1, "landmark": 3, "notecard": 7, "script": 10, "snapshot": 15, "wearable": 18,
             "animation": 19, "gesture": 20}


def _item(owner, part_id, item):
    atype = ASSET_TYPES[item["type"]][0]
    inv = INV_TYPES.get(item.get("inv_type"), atype)
    item_id = str(uuid.uuid5(NS, f"item/{part_id}/{item['item_id']}"))
    return (f"<TaskInventoryItem>{_uuid('AssetID', item['asset_id'])}<BasePermissions>{FULL}</BasePermissions>"
            f"<CreationDate>{item.get('created_at') or int(time.time())}</CreationDate>{_uuid('CreatorID', owner)}"
            f"<Description>{escape(item.get('desc', ''))}</Description><EveryonePermissions>0</EveryonePermissions>"
            f"<Flags>{item.get('flags', 0) & 0xFFFFFFFF}</Flags>{_uuid('GroupID', ZERO)}<GroupPermissions>0</GroupPermissions>"
            f"<InvType>{inv}</InvType>{_uuid('ItemID', item_id)}{_uuid('OldItemID', ZERO)}{_uuid('LastOwnerID', owner)}"
            f"<Name>{escape(item['name'])}</Name><NextPermissions>{FULL}</NextPermissions>{_uuid('OwnerID', owner)}"
            f"<CurrentPermissions>{FULL}</CurrentPermissions>{_uuid('ParentID', part_id)}{_uuid('ParentPartID', part_id)}"
            f"{_uuid('PermsGranter', ZERO)}<PermsMask>0</PermsMask><Type>{atype}</Type>"
            f"<OwnerChanged>false</OwnerChanged></TaskInventoryItem>")


def part_xml(owner, part_id, p, group_pos, offset, rot, link, items=(), text="", text_colour=(255, 240, 205),
             phantom=False):
    """One SceneObjectPart. p: {name, description, scale, volume, texture (its faces), material}."""
    inv = "".join(_item(owner, part_id, it) for it in items)
    r, g, b = text_colour
    colour = (f"<Color><R>{r}</R><G>{g}</G><B>{b}</B><A>255</A></Color>" if text
              else "<Color><R>0</R><G>0</G><B>0</B><A>0</A></Color>")
    return (f'<SceneObjectPart xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
            f'xmlns:xsd="http://www.w3.org/2001/XMLSchema"><AllowedDrop>false</AllowedDrop>{_uuid("CreatorID", owner)}'
            f'{_uuid("FolderID", part_id)}<InventorySerial>{len(items)}</InventorySerial>'
            + (f"<TaskInventory>{inv}</TaskInventory>" if items else "")
            + f'{_uuid("UUID", part_id)}<LocalId>0</LocalId><Name>{escape(p.get("name") or "Object")}</Name>'
            f'<Material>{p.get("material", 3)}</Material><PassTouches>false</PassTouches><PassCollisions>false</PassCollisions>'
            f'<RegionHandle>0</RegionHandle><ScriptAccessPin>0</ScriptAccessPin>'
            + _vec("GroupPosition", group_pos) + _vec("OffsetPosition", offset) + _quat("RotationOffset", rot)
            + _vec("Velocity", (0, 0, 0)) + _vec("AngularVelocity", (0, 0, 0)) + _vec("Acceleration", (0, 0, 0))
            + f'<Description>{escape(p.get("description", ""))}</Description>{colour}'
            + (f"<Text>{escape(text)}</Text>" if text else "<Text />")
            + f'<SitName>{escape(p.get("sit_name", ""))}</SitName><TouchName>{escape(p.get("touch_name", ""))}</TouchName>'
            f'<LinkNum>{link}</LinkNum><ClickAction>0</ClickAction>'
            + _shape(p.get("volume", {}), p["scale"], texture_entry(p.get("texture", [])))
            + _vec("Scale", p["scale"])
            + f"<ParentID>0</ParentID><CreationDate>{int(time.time())}</CreationDate><Category>0</Category>"
            "<SalePrice>0</SalePrice><ObjectSaleType>0</ObjectSaleType><OwnershipCost>0</OwnershipCost>"
            + _uuid("GroupID", ZERO) + _uuid("OwnerID", owner) + _uuid("LastOwnerID", owner)
            + f"<BaseMask>{FULL}</BaseMask><OwnerMask>{FULL}</OwnerMask><GroupMask>0</GroupMask>"
            f"<EveryoneMask>0</EveryoneMask><NextOwnerMask>{FULL}</NextOwnerMask>"
            f"<Flags>{'Phantom' if phantom else 'None'}</Flags></SceneObjectPart>")


def group_xml(parts):
    """An object in the OAR's own form: the root part, then the others."""
    return f"<SceneObjectGroup>{parts[0]}<OtherParts>{''.join(parts[1:])}</OtherParts></SceneObjectGroup>"


# ---- what's in the export -----------------------------------------------------------------------------------------
BUILDS = {                    # the big builds, by where their middle goes
    "Fox Valley Tavern": (62, 202), "Kitsune Valley FurPiled HQ Ver 1.1": (116, 204),
    "Kitsune Valley FurPiled HQ Ver 1.0": (172, 204), "Fox Valley Back Deck": (214, 122),
    "Fox Valley Back Bridge": (214, 166)}
WORN = {"FurFree - White Fox": None, "Kithylin's Collar": None, "Kithylin's Halo (partial - no texture)": None,
        "Kithylin's Soul (partial - no textures)": None}
PHOTO_FOLDER = "Kithylin's Snapshots"
HUNG = ["Kithylin's Sim Textures-Maps-Images", "Kithylin's Random Textures",
        "Kithylin's Falstaff AV + Textures + Drawings"]        # boxes of textures also hung in the galleries
PRIVATE = {"Kithylin's Personal RL Pictures-Textures"}     # stays in its box: not hung on a wall
TABLES = [("Fox & Wolf Valley papers", "Fox-Wolf Valley Archive"), ("Avatars", "FurFree Packs"),
          ("Avatars", "Kithylin's Avatars and Parts"), ("Photo albums", PHOTO_FOLDER),
          ("Textures, sounds and scripts", "Kithylin's Textures and Objects")]
SET_TEXT = __import__("re").compile(r'llSetText\(\s*"((?:[^"\\]|\\.)*)"\s*,\s*<\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*>')


def _natural(name):
    import re
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", name)]


class Backup:
    def __init__(self, path):
        self.path = Path(path)
        self.name = self.path.stem
        self.folder = self.path.parent.name
        self.data = read(path)
        self.assets = self.data.get("asset", {})
        self.inventory = self.data.get("inventory", {})

    def items(self, prim):
        """The prim's contents that were exported (their assets are in the backup)."""
        out = []
        for iid in prim.get("content") or []:
            it = self.inventory.get(iid)
            if it and it.get("asset_id") in self.assets and it.get("type") in ASSET_TYPES:
                out.append(it)
        return sorted(out, key=lambda it: _natural(it["name"]))

    def is_box(self):
        return len(self.data["prim"]) == 1

    def pictures(self):
        """[(name, description, asset id)] of the textures in a box, in order."""
        root = self.data["prim"][self.data["linkset"][0][0]]
        return [(it["name"], it.get("desc", ""), it["asset_id"]) for it in self.items(root) if it["type"] == "texture"]


def backups():
    out, seen = [], set()
    for path in sorted(source().glob("*/*.oxp"), key=lambda p: (p.parent.name, _natural(p.stem))):
        b = Backup(path)
        sig = signature(b.data)
        if len(b.data["prim"]) > 1 and sig in seen:       # the same thing exported twice
            continue
        seen.add(sig)
        out.append(b)
    return out


# ---- the region ---------------------------------------------------------------------------------------------------
class Region:
    """Collects objects and assets, then writes the OAR."""

    def __init__(self, owner):
        self.owner = owner
        self.objects = []                                  # (file name, xml)
        self.assets = {}                                   # asset id -> (file ending, data)
        self.count = 0

    def _id(self, *parts):
        return str(uuid.uuid5(NS, "/".join(str(p) for p in parts)))

    def _faces(self, faces, own):
        """The faces, with each texture that isn't here (someone else's) turned into plain white."""
        out = []
        for f in faces:
            f = dict(f)
            tid = f.get("imageid") or BLANK
            if tid in own:
                self.assets[tid] = ("_texture.jp2", own[tid]["data"])
            elif tid not in LIBRARY:
                f["imageid"] = BLANK
            out.append(f)
        return out

    def place(self, b, at, yaw=0.0, label=None, ground=GROUND):
        """Every linkset of backup b, moved so the build's middle is at `at` (x, y) and its base on the ground, turned
        by `yaw` degrees about its middle."""
        lo, hi = bounds(b.data)
        mid = ((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, base(b.data))
        turn = zrot(yaw)
        own = {k: v for k, v in b.assets.items() if v.get("type") == "texture"}
        for n, linkset in enumerate(b.data["linkset"]):
            prims = b.data["prim"]
            root = prims[linkset[0]]
            rel = [root["position"][k] - mid[k] for k in range(3)]
            moved = qrot(turn, rel)
            pos = (at[0] + moved[0], at[1] + moved[1], ground + moved[2])
            rot = qmul(turn, root["rotation"])
            parts = []
            for link, pid in enumerate(linkset):
                p = dict(prims[pid])
                p["texture"] = self._faces(p.get("texture", []), own)
                items = b.items(p)
                for it in items:
                    self.assets[it["asset_id"]] = (ASSET_TYPES[it["type"]][1], b.assets[it["asset_id"]]["data"])
                text, colour = "", (255, 240, 205)
                for it in items:                           # a marker whose script only shows a name: shown as is
                    if it["type"] == "lsltext":
                        m = SET_TEXT.search(b.assets[it["asset_id"]]["data"].decode("utf-8", "replace"))
                        if m:
                            text = m.group(1).replace("\\n", "\n").replace('\\"', '"')
                            colour = tuple(max(0, min(255, round(float(v) * 255))) for v in m.group(2, 3, 4))
                            break
                if link == 0 and label and not text:
                    text = label
                pid_new = self._id(b.folder, b.name, n, pid)
                offset = (0, 0, 0) if link == 0 else p["position"]
                prot = rot if link == 0 else p["rotation"]
                flags = int.from_bytes(p.get("flags", b"\0\0\0\0"), "big") if isinstance(p.get("flags"), bytes) else 0
                parts.append(part_xml(self.owner, pid_new, p, pos, offset, prot,
                                      (link + 1) if len(linkset) > 1 else 0, items, text, colour,
                                      phantom=bool(flags & 0x400)))
            self.add(parts, root.get("name") or b.name)

    def add(self, parts, name):
        self.count += 1
        rid = __import__("re").search(r"<UUID><UUID>([0-9a-f-]{36})</UUID></UUID>", parts[0]).group(1)
        safe = "".join(ch if ch.isalnum() else "_" for ch in name)[:40]
        self.objects.append((f"objects/{safe}__{rid}.xml", group_xml(parts)))

    # -- things made here: plaza, posts, tables, gallery walls --
    def box(self, key, name, pos, scale, colour, rot=(0, 0, 0, 1), text="", texture=BLANK, desc="", shape="box",
            fullbright=False):
        """A plain prim as part xml (root of its own object unless used as a child)."""
        faces = [{"imageid": texture, "colors": list(colour) + [1.0], "fullbright": fullbright}] * 6
        vol = {"profile": {"curve": 1 if shape == "box" else 0}, "path": {"curve": 16}}
        p = {"name": name, "description": desc, "scale": scale, "volume": vol, "texture": faces, "material": 3}
        return self._id("made", key), p

    def solid(self, key, name, pos, scale, colour, text="", **kw):
        pid, p = self.box(key, name, pos, scale, colour, **kw)
        self.add([part_xml(self.owner, pid, p, pos, (0, 0, 0), kw.get("rot", (0, 0, 0, 1)), 0, (), text)], name)

    def wall(self, key, title, at, pictures, photo):
        """A free-standing gallery wall along x at `at`, pictures on both sides, three rows high."""
        rows = 3
        if photo:
            sizes = [(2.0, 1.5)] * len(pictures)
        else:
            sizes = []
            for _n, _d, aid in pictures:
                wh = j2c_size(self.assets[aid][1]) or (1, 1)
                a = wh[0] / wh[1]
                sizes.append((1.8 * min(1, a), 1.8 * min(1, 1 / a)))
        pitch_x, pitch_z = (2.3, 1.8) if photo else (2.1, 2.1)
        per_side = math.ceil(len(pictures) / 2)
        cols = max(2, math.ceil(per_side / rows))
        length, height = cols * pitch_x + 0.4, rows * pitch_z + 0.4
        centre = (at[0], at[1], GROUND + 0.3 + height / 2)
        root_id, root = self.box(key, title, centre, (length, 0.3, height), (0.23, 0.19, 0.16))
        parts = [part_xml(self.owner, root_id, root, centre, (0, 0, 0), (0, 0, 0, 1), 1, (), title)]
        for i, ((name, desc, aid), (w, h)) in enumerate(zip(pictures, sizes)):
            side = -1 if i < per_side else 1                  # south side first, then north
            j = i if side < 0 else i - per_side
            row, col = divmod(j, cols)
            x = -length / 2 + 0.2 + pitch_x * (col + 0.5)
            if side > 0:
                x = -x                                         # the north side reads left to right too
            z = height / 2 - 0.2 - pitch_z * (row + 0.5)
            pid = self._id("made", key, "pic", i)
            dark = {"imageid": BLANK, "colors": [0.1, 0.1, 0.1, 1.0]}
            pic = {"imageid": aid, "colors": [1, 1, 1, 1], "fullbright": True}
            p = {"name": name, "description": desc, "scale": (w, 0.04, h), "material": 3,
                 "volume": {"profile": {"curve": 1}, "path": {"curve": 16}},
                 "texture": [dark, pic, pic, pic, pic, dark]}
            parts.append(part_xml(self.owner, pid, p, centre, (x, side * 0.18, z), (0, 0, 0, 1), len(parts) + 1))
        self.add(parts, title)
        return length

    def write(self, path):
        archive = ('<?xml version="1.0" encoding="utf-16"?><archive major_version="0" minor_version="8">'
                   f'<creation_info><datetime>{int(time.time())}</datetime><id>{uuid.uuid4()}</id></creation_info>'
                   '<region_info><is_megaregion>False</is_megaregion><size_in_meters>256,256</size_in_meters>'
                   '</region_info><assets_included>True</assets_included></archive>')
        files = [("archive.xml", archive.encode("utf-8")),
                 (f"settings/{REGION}.xml", SETTINGS.encode("utf-8")),
                 (f"terrains/{REGION}.r32", terrain())]
        files += [(name, xml.encode("utf-8")) for name, xml in self.objects]
        files += [(f"assets/{aid}{ending}", data) for aid, (ending, data) in self.assets.items()]
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        part = path.with_suffix(".part")
        with tarfile.open(part, "w:gz") as tar:
            for name, data in files:
                info = tarfile.TarInfo(name)
                info.size = len(data)
                info.mtime = int(time.time())
                tar.addfile(info, io.BytesIO(data))
        part.replace(path)
        return path


SETTINGS = f"""<?xml version="1.0" encoding="utf-16"?>
<RegionSettings>
  <General>
    <AllowDamage>False</AllowDamage>
    <AllowLandResell>True</AllowLandResell>
    <AllowLandJoinDivide>True</AllowLandJoinDivide>
    <BlockFly>False</BlockFly>
    <BlockLandShowInSearch>False</BlockLandShowInSearch>
    <BlockTerraform>False</BlockTerraform>
    <DisableCollisions>False</DisableCollisions>
    <DisablePhysics>False</DisablePhysics>
    <DisableScripts>True</DisableScripts>
    <MaturityRating>1</MaturityRating>
    <RestrictPushing>False</RestrictPushing>
    <AgentLimit>40</AgentLimit>
    <ObjectBonus>1</ObjectBonus>
  </General>
  <GroundTextures>
    <Texture1>b8d3965a-ad78-bf43-699b-bff8eca6c975</Texture1>
    <Texture2>abb783e6-3e93-26c0-248a-247666855da3</Texture2>
    <Texture3>179cdabd-398a-9b6b-1391-4dc333ba321f</Texture3>
    <Texture4>beb169c7-11ea-fff2-efe5-0f24dc881df2</Texture4>
    <ElevationLowSW>10</ElevationLowSW>
    <ElevationLowNW>10</ElevationLowNW>
    <ElevationLowSE>10</ElevationLowSE>
    <ElevationLowNE>10</ElevationLowNE>
    <ElevationHighSW>60</ElevationHighSW>
    <ElevationHighNW>60</ElevationHighNW>
    <ElevationHighSE>60</ElevationHighSE>
    <ElevationHighNE>60</ElevationHighNE>
  </GroundTextures>
  <Terrain>
    <WaterHeight>{WATER:g}</WaterHeight>
    <TerrainRaiseLimit>100</TerrainRaiseLimit>
    <TerrainLowerLimit>-100</TerrainLowerLimit>
    <UseEstateSun>True</UseEstateSun>
    <FixedSun>False</FixedSun>
    <SunPosition>0</SunPosition>
  </Terrain>
  <Telehub />
</RegionSettings>"""


def terrain():
    """A rounded-square island: flat at GROUND out to 118 m from the middle, then down to the sea floor."""
    out = bytearray()
    for y in range(256):
        for x in range(256):
            d = (abs(x - 127.5) ** 4 + abs(y - 127.5) ** 4) ** 0.25
            if d <= 118:
                h = GROUND
            else:
                t = min(1.0, (d - 118) / 14)
                h = GROUND - (GROUND - 12) * (3 * t * t - 2 * t * t * t)
            out += struct.pack("<f", h)
    return bytes(out)


def thin_yaw(b):
    """For an upright, flat-sided thing (a board, a sign): the direction (degrees) its flat side faces, else None."""
    pts = []
    for ls in b.data["linkset"]:
        for p, pos, rot in _world(b.data, ls):
            half = [s / 2 for s in p["scale"]]
            for sx in (-1, 1):
                for sy in (-1, 1):
                    for sz in (-1, 1):
                        d = qrot(rot, (sx * half[0], sy * half[1], sz * half[2]))
                        pts.append((pos[0] + d[0], pos[1] + d[1], pos[2] + d[2]))
    zs = [p[2] for p in pts]
    best = None
    for deg in range(0, 180, 5):
        c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
        us = [p[0] * c + p[1] * s for p in pts]
        vs = [-p[0] * s + p[1] * c for p in pts]
        thick, wide = max(us) - min(us), max(vs) - min(vs)
        if best is None or thick < best[0]:
            best = (thick, wide, deg)
    thick, wide, deg = best
    tall = max(zs) - min(zs)
    if thick < 0.35 * wide and tall > 0.6 * wide * 0.5 and tall > 1.5:
        return float(deg)
    return None


def footprint(b, yaw):
    """Width of b along the ring (its widest horizontal extent once turned)."""
    lo, hi = bounds(b.data)
    return max(hi[0] - lo[0], hi[1] - lo[1])


def build(progress=print):
    """Lay out everything in the export and write the OAR. Returns its path (None when there's nothing to load)."""
    from . import avatar
    if not source().is_dir():
        return None
    owner = avatar().get("uuid") or ZERO
    region = Region(owner)
    all_backups = backups()
    progress(f"Fox Valley: {len(all_backups)} backups")
    by_name = {b.name: b for b in all_backups}
    centre = (128.0, 128.0)

    # the arrival plaza
    region.solid("plaza", "Fox Valley plaza", (128, 128, GROUND + 0.05), (34, 34, 0.4), (0.55, 0.52, 0.47),
                 shape="cylinder")
    region.solid("welcome", "Welcome to Fox Valley", (128, 128, GROUND + 1.2), (0.6, 0.6, 2.0), (0.42, 0.3, 0.2),
                 text="Fox Valley\nKithylin Perth's Second Life, brought home\n"
                      "North: the Tavern and the FurPiled HQ  -  East: the back deck and bridge\n"
                      "South: the galleries  -  West: the archive vault  -  Around you: the Valleys' maps and signs")

    # the big builds
    for name, at in BUILDS.items():
        b = by_name.get(name)
        if b:
            region.place(b, at)
            lo, hi = bounds(b.data)
            region.solid(f"label/{name}", name, (at[0], at[1] - (hi[1] - lo[1]) / 2 - 2, GROUND + 0.6),
                         (0.3, 0.3, 1.2), (0.42, 0.3, 0.2), text=name)

    # the signs and maps: upright ones in a ring facing the plaza, flat ones inside it
    rest = [b for b in all_backups if b.folder == "Fox-Wolf Valley Archive" and not b.is_box() and b.name not in BUILDS]
    upright = [(b, thin_yaw(b)) for b in rest]
    ring = [(b, y) for b, y in upright if y is not None]
    flat = [b for b, y in upright if y is None]
    flat_widths = [footprint(b, None) + 2.0 for b in flat]
    flat_radius = max(13.0, sum(flat_widths) / (2 * math.pi))
    widths = [max(4.0, footprint(b, y)) + 2.5 for b, y in ring]
    radius = max(flat_radius + 16, sum(widths) / (2 * math.pi))
    angle = 90.0 + widths[0] / radius * 90 / math.pi if widths else 0
    for (b, yaw), w in zip(ring, widths):
        angle -= w / radius * 180 / math.pi / 2
        a = math.radians(angle)
        at = (centre[0] + radius * math.cos(a), centre[1] + radius * math.sin(a))
        region.place(b, at, yaw=(angle + 180) - yaw, label=b.name)   # its flat side towards the middle
        angle -= w / radius * 180 / math.pi / 2
    angle = 15.0
    for b, w in zip(flat, flat_widths):
        angle += w / flat_radius * 180 / math.pi / 2
        a = math.radians(angle)
        region.place(b, (centre[0] + flat_radius * math.cos(a), centre[1] + flat_radius * math.sin(a)),
                     ground=GROUND + 0.25, label=b.name)
        angle += w / flat_radius * 180 / math.pi / 2

    # the galleries: snapshot albums, then the boxes of textures, on walls in rows to the south
    walls = [(b, True) for b in all_backups if b.folder == PHOTO_FOLDER]
    walls += [(b, False) for b in all_backups if b.name in HUNG]
    x, y = 30.0, 34.0
    for b, photo in walls:
        title, pictures = b.name, b.pictures()
        for chunk_no, start in enumerate(range(0, len(pictures), 72)):
            chunk = pictures[start:start + 72]
            parts = math.ceil(len(pictures) / 72)
            label = title if parts == 1 else f"{title} ({chunk_no + 1} of {parts})"
            for _n, _d, aid in chunk:                        # the pictures' textures go in the archive
                region.assets[aid] = ("_texture.jp2", b.assets[aid]["data"])
            per_side = math.ceil(len(chunk) / 2)
            length = max(2, math.ceil(per_side / 3)) * (2.3 if photo else 2.1) + 0.4
            if x + length > 226:
                x, y = 30.0, y + 22
            region.wall(f"wall/{title}/{chunk_no}", label, (x + length / 2, y), chunk, photo)
            x += length + 5

    # the archive vault: the boxes on tables to the west, a table each
    tables = {}
    for b in all_backups:
        if b.is_box() and any(b.items(p) for p in b.data["prim"].values()):
            topic = next((t for t, folder in TABLES if folder == b.folder), "Other")
            tables.setdefault(topic, []).append(b)
    worn = [b for b in all_backups if not b.is_box() and (b.folder in WORN or b.name in WORN)]
    if worn:
        tables["Worn things (Take one into your inventory to wear it)"] = worn
    ty = 100.0
    for topic, boxes in tables.items():
        rows = [boxes[i:i + 9] for i in range(0, len(boxes), 9)]
        for r, row in enumerate(rows):
            length = len(row) * 2.6 + 1.0
            region.solid(f"table/{topic}/{r}", topic, (24 + length / 2, ty, GROUND + 0.45), (length, 1.6, 0.9),
                         (0.36, 0.25, 0.16), text=topic if r == 0 else "")
            for i, b in enumerate(row):
                lo, hi = bounds(b.data)
                region.place(b, (24 + 1.8 + i * 2.6, ty), ground=GROUND + 0.9, label=b.name)
            ty += 6.5
    progress(f"Fox Valley: {region.count} objects, {len(region.assets)} textures, sounds, scripts and notes")
    return region.write(target())


def ensure(progress=print):
    """The OAR, built the first time (or again when the export has changed)."""
    out = target()
    newest = max((p.stat().st_mtime for p in source().glob("*/*.oxp")), default=0) if source().is_dir() else 0
    if not newest:
        return None
    if out.exists() and out.stat().st_mtime >= newest:
        return out
    return build(progress)
