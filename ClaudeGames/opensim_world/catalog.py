"""The catalogue of what the residents can wear, for the Persona Studio's galleries:

    bodies    the furry avatars (Linda Kellie's furry pack) and the human ones (her full avatars), with the Tailor's
              photos of each (Local Storage/SecondLife/outfits) cropped to the figure
    clothes   every garment in the clothing and accessories packs: name, pack, folder, which layer it is (shirt,
              pants, jacket, skirt, shoes...), and a thumbnail made from the garment's own texture
    hair      the hair pack, by style

Written to Local Storage/SecondLife/catalog/index.json with thumbs/ beside it; rebuilt with
    python -m opensim_world.catalog
"""
import html
import io
import json
import re
import tarfile

from . import root

LAYERS = {0: "shape", 1: "skin", 2: "hair", 3: "eyes", 4: "shirt", 5: "pants", 6: "shoes", 7: "socks", 8: "jacket",
          9: "gloves", 10: "undershirt", 11: "underpants", 12: "skirt", 13: "alpha", 14: "tattoo", 15: "physics"}
PACKS = {"furry-avatars.iar": ("bodies", "furry"), "FULLAVATARS.iar": ("bodies", "human"),
         "LK-MENS-CLOTHING.iar": ("clothes", "men"), "LK-WOMENS-CLOTHING.iar": ("clothes", "women"),
         "LK-ACCESSORIES.iar": ("clothes", "accessories"), "AVATARHAIR.iar": ("hair", "hair")}
FEMALE = re.compile(r"\b(she|female|lady|girl|women|candi|celeste|dot|chara|lyra|rana|venus)\b|kitty-prim|pink and black kitty",
                    re.I)
THUMB = 128


def folder():
    return root() / "catalog"


def _plain(part):
    return html.unescape(re.sub(r"__[0-9a-f-]{36}(\.xml)?$", "", part))


def slug(name):
    return re.sub(r"[^a-z0-9]+", "_", html.unescape(name).lower()).strip("_")


def _thumb_from_jp2(data, out):
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(data))
        im.load()
        im = im.convert("RGB")
        im.thumbnail((THUMB, THUMB))
        im.save(out, "PNG")
        return True
    except Exception:
        return False


def _crop_photo(src, out, box=(330, 40, 650, 600), size=(THUMB, int(THUMB * 1.75))):
    """The Tailor's photo cropped to the figure on the platform."""
    try:
        from PIL import Image
        im = Image.open(src).convert("RGB")
        im = im.crop(box)
        im.thumbnail(size)
        im.save(out, "PNG")
        return True
    except Exception:
        return False


def build(progress=print):
    base = root() / "downloads" / "zadaroo"
    thumbs = folder() / "thumbs"
    thumbs.mkdir(parents=True, exist_ok=True)
    index = {"bodies": [], "clothes": [], "hair": []}
    photos = root() / "outfits"
    for iar, (section, kind) in PACKS.items():
        path = base / iar if (base / iar).exists() else base / "iars" / iar
        if not path.exists():
            progress(f"(no {iar})")
            continue
        progress(f"Reading {iar}...")
        with tarfile.open(path) as t:
            members = {m.name: m for m in t.getmembers()}
            groups = {}
            for name, m in members.items():
                p = name.split("/")
                if p[0] != "inventory" or not name.endswith(".xml") or len(p) < 4:
                    continue
                x = t.extractfile(m).read().decode("utf-8", "replace")
                item_name = html.unescape((re.search(r"<Name>(.*?)</Name>", x) or [0, ""])[1])
                asset_type = int((re.search(r"<AssetType>(.*?)</AssetType>", x) or [0, "-1"])[1])
                asset = (re.search(r"<AssetID>(.*?)</AssetID>", x) or [0, ""])[1]
                flags = int((re.search(r"<Flags>(.*?)</Flags>", x) or [0, "0"])[1])
                fpath = [_plain(s) for s in p[2:-1]]
                top = fpath[0] if fpath else ""
                layer = None
                if asset_type in (5, 13):
                    layer = LAYERS.get(flags & 0xFF)
                    afile = next((k for k in members if k.startswith("assets/" + asset)), None)
                    if afile:
                        text = t.extractfile(members[afile]).read().decode("utf-8", "replace")
                        m2 = re.search(r"^type (\d+)", text, re.M)
                        if m2:
                            layer = LAYERS.get(int(m2.group(1)), layer)
                        tex = re.findall(r"^\d+ ([0-9a-f-]{36})$", text, re.M)
                    else:
                        tex = []
                elif asset_type == 6:
                    layer = "attachment"
                    tex = []
                else:
                    continue
                entry = {"id": asset, "name": item_name, "pack": kind, "folder": "/".join(fpath), "layer": layer}
                if section == "bodies":
                    groups.setdefault(top, []).append(entry)
                    continue
                if layer in ("shape", "skin", "eyes", "alpha", "physics") and section == "clothes":
                    continue                        # body parts in a clothing pack: not clothes
                thumb = None
                for tid in tex:
                    if tid.startswith("00000000") or tid in ("c228d1cf-4b5d-4ba8-84f4-899a0796aa97",
                                                             "5748decc-f629-461c-9a36-a35a221fe21f"):
                        continue                    # blank/default textures
                    tf = next((k for k in members if k.startswith("assets/" + tid)), None)
                    if tf:
                        out = thumbs / f"{tid}.png"
                        if out.exists() or _thumb_from_jp2(t.extractfile(members[tf]).read(), out):
                            thumb = out.name
                            break
                entry["thumb"] = thumb
                entry["for"] = "women" if kind == "women" else "men" if kind == "men" else "anyone"
                index[section].append(entry)
            if section == "bodies":
                for top, items in groups.items():
                    s = slug(top)
                    photo = photos / f"{s}.png"
                    thumb = None
                    if photo.exists():
                        out = thumbs / f"body_{s}.png"
                        if out.exists() or _crop_photo(photo, out):
                            thumb = out.name
                    index["bodies"].append({
                        "slug": s, "name": top, "kind": kind,
                        "gender": "female" if FEMALE.search(top) else "male",
                        "parts": [i["name"] for i in items if i["layer"] == "attachment"],
                        "layers": sorted({i["layer"] for i in items if i["layer"] and i["layer"] != "attachment"}),
                        "thumb": thumb})
    index["residents"] = {}                     # the residents' own photos from their fittings
    for photo in sorted(photos.glob("residents_*.png")):
        out = thumbs / f"res_{photo.stem[10:]}.png"
        if out.exists() or _crop_photo(photo, out):
            index["residents"][photo.stem[10:]] = out.name
    index["bodies"].sort(key=lambda b: (b["kind"] != "furry", b["name"].lower()))
    index["clothes"].sort(key=lambda c: (c["pack"], c["folder"].lower(), c["name"].lower()))
    (folder() / "index.json").write_text(json.dumps(index, indent=1, ensure_ascii=False), encoding="utf-8")
    progress(f"{len(index['bodies'])} bodies, {len(index['clothes'])} garments, {len(index['hair'])} hair items")
    return index


def load():
    try:
        return json.loads((folder() / "index.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"bodies": [], "clothes": [], "hair": [], "residents": {}}


if __name__ == "__main__":
    build()
