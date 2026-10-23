"""More furry bodies, out of Linda Kellie's Avatar Center (CC0): that build is a hall of mannequins, each holding a
complete avatar in its contents (shape, skin, eyes, the prim parts). This picks out the furry ones the furry avatars
pack doesn't already have and writes them as an inventory archive, Local Storage/SecondLife/downloads/commons/
furry-commons.iar, one folder per avatar, which the Tailor can try on (pack "commons") and the catalogue lists.

    python -m opensim_world.boxes
"""
import collections
import html
import io
import re
import tarfile
import time
import uuid

from . import avatar, root

SOURCE = root() / "downloads" / "outworldz" / "OAR-Avatar Center(1X1).tgz"
OUT = root() / "downloads" / "commons" / "furry-commons.iar"
NS = uuid.UUID("5a7c2e41-3b9d-4f80-8c16-7d2e9a4b1c33")
FURRY = re.compile(r"\b(wolf|wolfie|fox|pupp?y|pup|dog|husky|bunny|rabbit|dragon|kitty|kitten|cat|bear|mouse|rat|deer|"
                   r"horse|otter|raccoon|furry|anthro|bird|lizard|skunk|tiger|lion|coyote|neko|fur|paw|tail|whiskers)\b", re.I)
PARTS = re.compile(r"\((left|right|l|r)\)|\b(head|tail|paws?|hands?|foot|feet|fore?arms?|legs?|lower|upper|piece|skin|shape|"
                   r"eyes?|whiskers|ears?|hair|base|alpha|avatar|avi|right|left|male|female|version|prim|sign|nipples|"
                   r"with|without|no|and|the|complete|mouth|closed|open|tongue|basic)\b|[-_#*]|\d+", re.I)


def _name_of(items):
    """The avatar's name, from what its parts are called: 'Black Wolf Head', 'Black Wolf Tail' -> 'Black Wolf'."""
    counts = collections.Counter()
    for name, *_ in items:
        cleaned = re.sub(r"\s+", " ", PARTS.sub(" ", re.sub(r"\(.*?\)", " ", name))).strip(" ,.-")
        if len(cleaned) >= 3:
            counts[cleaned.title()] += 1
    if not counts:
        return None
    best = max(counts.items(), key=lambda kv: (kv[1], len(kv[0])))
    return best[0]


def scan(path=SOURCE):
    """[(name, items)] for every mannequin holding a furry avatar; items are (name, asset id, asset type, inv type,
    flags, creator, description)."""
    found = []
    with tarfile.open(path) as t:
        for m in t:
            if not m.name.startswith("objects/"):
                continue
            x = t.extractfile(m).read().decode("utf-8", "replace")
            items = []
            for it in re.findall(r"<TaskInventoryItem>(.*?)</TaskInventoryItem>", x, re.S):
                g = lambda tag: (re.search(f"<{tag}>(.*?)</{tag}>", it, re.S) or [0, ""])[1]
                aid = (re.search(r"<AssetID><UUID>(.*?)</UUID>", it) or [0, ""])[1]
                creator = (re.search(r"<CreatorID><UUID>(.*?)</UUID>", it) or [0, ""])[1]
                items.append((html.unescape(g("Name")), aid, int(g("Type") or -1), int(g("InvType") or -1),
                              int(g("Flags") or 0), creator, html.unescape(g("Description"))))
            kinds = {i[4] & 255 for i in items if i[2] == 13}
            if not ({0, 1} <= kinds):                       # a whole avatar has a shape and a skin
                continue
            names = " ".join(i[0] for i in items)
            if not FURRY.search(names):
                continue
            name = _name_of([i for i in items if i[2] in (5, 6, 13)])
            if name:
                found.append((name, items))
    return found


def _slug(name):
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def build(progress=print):
    from . import catalog
    have = {b["slug"] for b in catalog.load().get("bodies", [])}

    def known(s):
        """Already in the furry pack under a longer name ('fox' is there as 'male_fox'; a she-wolf isn't a wolf)."""
        words = set(s.split("_"))
        for h in have:
            hw = set(h.split("_"))
            if words <= hw and not (({"she", "female"} & hw) and not ({"she", "female"} & words)):
                return True
        return False

    boxes = {}
    for name, items in scan():
        s = _slug(name)
        if known(s) or not FURRY.search(name):
            continue
        if s not in boxes or len(items) > len(boxes[s][1]):
            boxes[s] = (name, items)
    if not boxes:
        progress("No new furry avatars found.")
        return []
    owner = avatar().get("uuid", "00000000-0000-0000-0000-000000000000")
    now = int(time.time())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(SOURCE) as t:
        members = {m.name: m for m in t.getmembers()}
        by_asset = {}
        for n in members:
            if n.startswith("assets/"):
                by_asset[n[7:43]] = n
        with tarfile.open(OUT, "w:gz", format=tarfile.GNU_FORMAT) as out:
            def add(name, data):
                info = tarfile.TarInfo(name)
                info.size = len(data)
                info.mtime = now
                out.addfile(info, io.BytesIO(data))
            add("archive.xml", b'<?xml version="1.0" encoding="utf-16"?>\n<archive major_version="0" minor_version="3">\n'
                               b'  <assets_included>True</assets_included>\n</archive>')
            top = f"inventory/commons__{uuid.uuid5(NS, 'commons')}"
            needed = set()
            for s, (name, items) in sorted(boxes.items()):
                folder = f"{top}/{name}__{uuid.uuid5(NS, s)}"
                for iname, aid, atype, itype, flags, creator, desc in items:
                    if aid not in by_asset:
                        continue
                    needed.add(aid)
                    if atype in (13, 5):                     # a wearable: its textures too
                        text = t.extractfile(members[by_asset[aid]]).read().decode("utf-8", "replace")
                        needed.update(re.findall(r"^\d+ ([0-9a-f-]{36})$", text, re.M))
                    item_id = uuid.uuid5(NS, f"{s}/{iname}/{aid}")
                    xml = (f'<?xml version="1.0" encoding="utf-16"?>\n<InventoryItem>\n  <Name>{html.escape(iname)}</Name>\n'
                           f'  <ID>{item_id}</ID>\n  <InvType>{itype}</InvType>\n  <CreatorUUID>{creator}</CreatorUUID>\n'
                           f'  <CreationDate>{now}</CreationDate>\n  <Owner>{owner}</Owner>\n'
                           f'  <Description>{html.escape(desc)}</Description>\n  <AssetType>{atype}</AssetType>\n'
                           f'  <AssetID>{aid}</AssetID>\n  <SaleType>0</SaleType>\n  <SalePrice>0</SalePrice>\n'
                           f'  <BasePermissions>2147483647</BasePermissions>\n  <CurrentPermissions>2147483647</CurrentPermissions>\n'
                           f'  <EveryOnePermissions>0</EveryOnePermissions>\n  <NextPermissions>2147483647</NextPermissions>\n'
                           f'  <Flags>{flags}</Flags>\n  <GroupID>00000000-0000-0000-0000-000000000000</GroupID>\n'
                           f'  <GroupOwned>False</GroupOwned>\n</InventoryItem>')
                    add(f"{folder}/{iname}__{item_id}.xml", xml.encode("utf-8"))
                progress(f"{name}: {len(items)} items")
            # the prim parts' textures are inside their binary texture entries: take every texture along
            for aid, n in by_asset.items():
                if aid in needed or n.endswith("_texture.jp2"):
                    add(n, t.extractfile(members[n]).read())
    progress(f"{len(boxes)} avatars -> {OUT}")
    return sorted(boxes)


if __name__ == "__main__":
    build()
