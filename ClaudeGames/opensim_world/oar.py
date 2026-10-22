"""Writing the OpenSim Archive (OAR) that puts the Hollow Keeper into the region: a small stone prim with keeper.lsl
in its contents, owned by the user's avatar so its NPC functions are allowed. OpenSim loads it with `load oar
--merge`, which leaves the rest of the region alone."""
import io
import tarfile
import time
import uuid
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
KEEPER_NS = uuid.UUID("6d1e0c2a-6a4b-4b8e-9f21-3c7d5a1b2e01")


def keeper_ids(region):
    """The region's Keeper object and its script: the same every time (merging replaces it), different per region."""
    return (str(uuid.uuid5(KEEPER_NS, "keeper/" + region)), str(uuid.uuid5(KEEPER_NS, "script/" + region)))
FULL = 2147483647


def _uuid(tag, value):
    return f"<{tag}><UUID>{value}</UUID></{tag}>"


def _vec(tag, x, y, z):
    return f"<{tag}><X>{x}</X><Y>{y}</Y><Z>{z}</Z></{tag}>"


def _item(owner, parent, item_id, asset, name, inv_type, asset_type, description=""):
    """One item in a prim's contents."""
    now = int(time.time())
    return (f"<TaskInventoryItem>{_uuid('AssetID', asset)}<BasePermissions>{FULL}</BasePermissions>"
            f"<CreationDate>{now}</CreationDate>{_uuid('CreatorID', owner)}<Description>{escape(description)}</Description>"
            f"<EveryonePermissions>0</EveryonePermissions><Flags>0</Flags>{_uuid('GroupID', '00000000-0000-0000-0000-000000000000')}"
            f"<GroupPermissions>0</GroupPermissions><InvType>{inv_type}</InvType>{_uuid('ItemID', item_id)}"
            f"{_uuid('OldItemID', item_id)}{_uuid('LastOwnerID', owner)}<Name>{escape(name)}</Name>"
            f"<NextPermissions>{FULL}</NextPermissions>{_uuid('OwnerID', owner)}<CurrentPermissions>{FULL}</CurrentPermissions>"
            f"{_uuid('ParentID', parent)}{_uuid('ParentPartID', parent)}"
            f"{_uuid('PermsGranter', '00000000-0000-0000-0000-000000000000')}<PermsMask>0</PermsMask><Type>{asset_type}</Type>"
            f"<OwnerChanged>false</OwnerChanged></TaskInventoryItem>")


def keeper_xml(owner, script_asset, region, pos=(128.0, 128.0, 22.5), name="Hollow Keeper", animations=()):
    KEEPER_ID, SCRIPT_ITEM = keeper_ids(region)
    now = int(time.time())
    item = _item(owner, KEEPER_ID, SCRIPT_ITEM, script_asset, name, 10, 10, "The residents")
    for anim_name, anim_asset in animations:             # the dances it can play on the residents
        item += _item(owner, KEEPER_ID, str(uuid.uuid5(KEEPER_NS, f"anim/{region}/{anim_name}")), anim_asset,
                      anim_name, 19, 20)
    shape = ("<Shape><ProfileCurve>1</ProfileCurve><PathBegin>0</PathBegin><PathCurve>16</PathCurve><PathEnd>0</PathEnd>"
             "<PathRadiusOffset>0</PathRadiusOffset><PathRevolutions>0</PathRevolutions><PathScaleX>100</PathScaleX>"
             "<PathScaleY>100</PathScaleY><PathShearX>0</PathShearX><PathShearY>0</PathShearY><PathSkew>0</PathSkew>"
             "<PathTaperX>0</PathTaperX><PathTaperY>0</PathTaperY><PathTwist>0</PathTwist><PathTwistBegin>0</PathTwistBegin>"
             "<PCode>9</PCode><ProfileBegin>0</ProfileBegin><ProfileEnd>0</ProfileEnd><ProfileHollow>0</ProfileHollow>"
             "<State>0</State><ProfileShape>Circle</ProfileShape><HollowShape>Same</HollowShape>"
             + _vec("Scale", 0.6, 0.6, 0.9) + "</Shape>")
    part = (f'<SceneObjectPart xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
            f'xmlns:xsd="http://www.w3.org/2001/XMLSchema"><AllowedDrop>false</AllowedDrop>{_uuid("CreatorID", owner)}'
            f'{_uuid("FolderID", KEEPER_ID)}<InventorySerial>{1 + len(animations)}</InventorySerial><TaskInventory>{item}</TaskInventory>'
            f'{_uuid("UUID", KEEPER_ID)}<LocalId>0</LocalId><Name>{escape(name)}</Name><Material>0</Material>'
            f'<PassTouches>false</PassTouches><RegionHandle>0</RegionHandle><ScriptAccessPin>0</ScriptAccessPin>'
            + _vec("GroupPosition", *pos) + _vec("OffsetPosition", 0, 0, 0)
            + "<RotationOffset><X>0</X><Y>0</Y><Z>0</Z><W>1</W></RotationOffset>"
            + _vec("Velocity", 0, 0, 0) + _vec("AngularVelocity", 0, 0, 0) + _vec("Acceleration", 0, 0, 0)
            + f"<Description>{escape('Brings the residents of the Claude Timeline to the Furry Hollow.')}</Description>"
            "<Color><R>0</R><G>0</G><B>0</B><A>255</A></Color><Text /><SitName /><TouchName />"
            "<LinkNum>0</LinkNum><ClickAction>0</ClickAction>" + shape + _vec("Scale", 0.6, 0.6, 0.9)
            + "<ParentID>0</ParentID>" + f"<CreationDate>{now}</CreationDate><Category>0</Category>"
            "<SalePrice>0</SalePrice><ObjectSaleType>0</ObjectSaleType><OwnershipCost>0</OwnershipCost>"
            + _uuid("GroupID", "00000000-0000-0000-0000-000000000000") + _uuid("OwnerID", owner)
            + _uuid("LastOwnerID", owner)
            + f"<BaseMask>{FULL}</BaseMask><OwnerMask>{FULL}</OwnerMask><GroupMask>0</GroupMask>"
            f"<EveryoneMask>0</EveryoneMask><NextOwnerMask>{FULL}</NextOwnerMask><Flags>None</Flags>"
            "</SceneObjectPart>")
    return f"<SceneObjectGroup><RootPart>{part}</RootPart><OtherParts /></SceneObjectGroup>"


# animations from Linda Kellie's animations pack (CC0) that the Keepers carry, to play on the residents
DANCES = ["happydance", "tushpush", "bootscoot", "twril"]


def _animations(names):
    """[(name, asset id, asset file name, data)] for the named animations in LK-ANIMATIONS.iar, if it's here."""
    import html
    import re
    from . import root
    iar = root() / "downloads" / "zadaroo" / "iars" / "LK-ANIMATIONS.iar"
    if not iar.exists():
        return []
    found = {}
    with tarfile.open(iar) as t:
        members = {m.name: m for m in t.getmembers()}
        for n, m in members.items():
            if n.startswith("inventory/") and n.endswith(".xml"):
                x = t.extractfile(m).read().decode("utf-8", "replace")
                if "<AssetType>20</AssetType>" not in x:
                    continue
                anim = html.unescape(re.search(r"<Name>(.*?)</Name>", x).group(1))
                if anim in names and anim not in found:
                    aid = re.search(r"<AssetID>(.*?)</AssetID>", x).group(1)
                    files = [k for k in members if k.startswith("assets/" + aid)]
                    if files:
                        found[anim] = (anim, aid, files[0].split("/", 1)[1], t.extractfile(members[files[0]]).read())
    return [found[n] for n in names if n in found]


def write(path, owner, region, script=None, name="Hollow Keeper", pos=(128.0, 128.0, 22.5), dances=None):
    """The OAR file for one region's Keeper (or another scripted object: `script` text, `name`), owned by `owner`
    (an account UUID). A Keeper also carries the dance animations (DANCES)."""
    if dances is None:
        dances = DANCES if script is None else []
    anims = _animations(dances)
    # each region gets its own copy (its own asset): the script engine compiling one shared asset for four regions at
    # once trips over itself
    script = (HERE / "keeper.lsl").read_text(encoding="utf-8") if script is None else script
    script = (script + f"\n// {region}\n").encode("utf-8")
    import hashlib
    script_asset = str(uuid.uuid5(uuid.NAMESPACE_URL, "claude-timeline/keeper/" + hashlib.md5(script).hexdigest()))
    archive = ('<?xml version="1.0" encoding="utf-16"?><archive major_version="0" minor_version="8">'
               f'<creation_info><datetime>{int(time.time())}</datetime><id>{uuid.uuid4()}</id></creation_info>'
               '<assets_included>True</assets_included></archive>')
    files = {"archive.xml": archive.encode("utf-8"),
             f"objects/{name.replace(' ', '_')}__{keeper_ids(region)[0]}.xml":
                 keeper_xml(owner, script_asset, region, pos, name, [(a[0], a[1]) for a in anims]).encode("utf-8"),
             f"assets/{script_asset}_script.lsl": script}
    for _n, _aid, filename, data in anims:
        files[f"assets/{filename}"] = data
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(path, "w:gz") as tar:
        for name, data in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mtime = int(time.time())
            tar.addfile(info, io.BytesIO(data))
    return path
