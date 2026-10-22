"""Dressing the residents: each one's furry avatar (wardrobe.json "picks") plus the clothes picked for them
(wardrobe.json "clothes": [pack folder, item name] pairs from Linda Kellie's men's and women's clothing packs, CC0),
gathered into one inventory archive for Hollow Tailor - a folder per resident under #RLV/residents - so the fitting
room (tailor.py) can save each resident's whole look at once.

The clothes are the classic layers (shirt, pants, jacket), painted onto the body under the furry avatar's prim pieces.
"""
import html
import io
import json
import re
import tarfile
import uuid

from . import HERE, root

NS = uuid.UUID("2b1f5a0c-8d3e-4f61-9a27-5c0e1d7b3a01")
PACKS = {"furry": "furry-avatars.iar", "men": "iars/LK-MENS-CLOTHING.iar", "women": "iars/LK-WOMENS-CLOTHING.iar"}
TOP = "residents"


def wardrobe():
    return json.loads((HERE / "wardrobe.json").read_text(encoding="utf-8"))


def slug(name):
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def _plain(part):
    return html.unescape(re.sub(r"__[0-9a-f-]{36}(\.xml)?$", "", part))


def _items(tar):
    """[(folder path, item name, archive member, asset id)] for every item in an IAR."""
    out = []
    for m in tar.getmembers():
        p = m.name.split("/")
        if p[0] == "inventory" and m.name.endswith(".xml") and len(p) >= 3:
            x = tar.extractfile(m).read().decode("utf-8", "replace")
            name = html.unescape((re.search(r"<Name>(.*?)</Name>", x) or [None, ""])[1])
            asset = (re.search(r"<AssetID>(.*?)</AssetID>", x) or [None, ""])[1]
            out.append(("/".join(_plain(s) for s in p[2:-1]), name, m, asset))
    return out


def build(path):
    """Write the archive; returns {resident: slug} for the residents it holds, and a list of clothes not found."""
    base = root() / "downloads" / "zadaroo"
    tars = {k: tarfile.open(base / v) for k, v in PACKS.items()}
    items = {k: _items(t) for k, t in tars.items()}
    ward = wardrobe()
    looks_folder = {}                                   # furry look slug -> its folder name in the pack
    for folder, _n, _m, _a in items["furry"]:
        looks_folder.setdefault(slug(folder.split("/")[0]), folder.split("/")[0])
    top_id = uuid.uuid5(NS, TOP)
    members, missing, residents = {}, [], {}
    for resident, look in ward["picks"].items():
        rslug = slug(resident)
        folder_name = f"{TOP}__{top_id}/{rslug}__{uuid.uuid5(NS, resident)}"
        chosen = [("furry", m) for f, _n, m, _a in items["furry"] if f.split("/")[0] == looks_folder.get(look)]
        for pack_folder, item_name in ward.get("clothes", {}).get(resident, []):
            hit = None
            for key in ("men", "women"):
                for f, n, m, _a in items[key]:
                    if n.strip().lower() == item_name.strip().lower() and f.split("/")[-1].lower() == pack_folder.lower():
                        hit = (key, m)
                        break
                if hit:
                    break
            if hit:
                chosen.append(hit)
            else:
                missing.append(f"{resident}: {pack_folder} / {item_name}")
        for key, m in chosen:
            data = tars[key].extractfile(m).read()
            leaf = m.name.split("/")[-1]
            # each copy its own item ID in the archive (the loader gives new ones anyway)
            leaf = re.sub(r"__[0-9a-f-]{36}\.xml$", f"__{uuid.uuid5(NS, resident + m.name)}.xml", leaf)
            members[f"inventory/{folder_name}/{leaf}"] = data
        residents[resident] = rslug
    with tarfile.open(path, "w:gz", format=tarfile.GNU_FORMAT) as out:
        def add(name, data):
            info = tarfile.TarInfo(name)
            info.size = len(data)
            out.addfile(info, io.BytesIO(data))
        add("archive.xml", tars["furry"].extractfile("archive.xml").read())
        for name, data in members.items():
            add(name, data)
        seen = set()
        for t in tars.values():                         # every asset from the three packs (shared ones once)
            for m in t.getmembers():
                if m.name.startswith("assets/") and m.isfile() and m.name not in seen:
                    seen.add(m.name)
                    add(m.name, t.extractfile(m).read())
    for t in tars.values():
        t.close()
    return residents, missing
