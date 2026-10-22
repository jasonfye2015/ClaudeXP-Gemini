"""Furnishing the world: the first time the server starts with these files in place, each region gets a ready-made
build and the avatar's inventory gets the packs below. What's been loaded is remembered in world.json, so it happens
once (and a region whose build was loaded keeps everything built in it since).

Most of it is Linda Kellie's collection as kept by Zadaroo (https://www.zadaroo.com), released CC0 - free for any
use. The newer regions come from the Outworldz free library (https://outworldz.com/cgi/freesculpts.plx?q=OAR):
Love Island by Avia Bonne (CC BY-NC: personal use, credit her), Fantasy Island by Linda Kellie (CC0), and WhiteWood
and Castle LoveGlo by PcTek CyberStar (CC-BY: credit them). Files go in Local Storage/SecondLife/downloads/<source>
(download_all() fetches them)."""
import json
import time
import urllib.request
import zipfile

from . import REGIONS, avatar, root, world_file

SOURCES = {"zadaroo": "https://files.zadaroo.com/", "outworldz": "https://outworldz.com/Sculpts/cgi/files/"}
REGION_BUILDS = {"Furry Hollow": "oars/LK-MountainRetreat.tgz",      # a forest village in the hills
                 "Whisker Falls": "oars/LakeHouse.tgz",               # a lake with a house on it
                 "Tailwind Beach": "oars/LK-TikiSummer.tgz",          # tiki huts and sand
                 "Lantern Market": "oars/FreebieMall.tgz",            # shops full of things to take
                 "Love Island": "outworldz:OAR-Love_Island(1X1).tgz",          # a romantic fantasy island
                 "Fantasy Island": "outworldz:OAR-Fantasy_Island(1X1).tgz",    # castles and fairy lights
                 "Whitewood": "outworldz:OAR-ADULT-WhiteWood(1X1).tgz",        # adults: a castle in the woods
                 "Castle LoveGlo": "outworldz:OAR-Castle_LoveGlo(1X1).tgz"}    # adults: a castle by the sea
PACKS = ["iars/furry-avatars.iar", "iars/FULLAVATARS.zip", "iars/AVATARHAIR.zip", "iars/LK-ANIMALS.zip",
         "iars/LK-ANIMATIONS.zip", "iars/LK-FURNITURE.zip", "iars/LK-HOUSES.zip"]


def folder(source="zadaroo"):
    return root() / "downloads" / source


def _split(rel):
    """(source, path at the source): "oars/x.tgz" is Zadaroo's, "outworldz:OAR-x.tgz" Outworldz's."""
    return tuple(rel.split(":", 1)) if ":" in rel else ("zadaroo", rel)


def local(rel):
    source, path = _split(rel)
    return folder(source) / path.split("/")[-1]


def download_all(progress=print):
    from urllib.parse import quote
    for rel in list(REGION_BUILDS.values()) + PACKS:
        if not local(rel).exists():
            source, path = _split(rel)
            progress(f"Downloading {path}...")
            local(rel).parent.mkdir(parents=True, exist_ok=True)
            tmp = local(rel).with_suffix(".part")
            urllib.request.urlretrieve(SOURCES[source] + quote(path), tmp)
            tmp.replace(local(rel))


def _done():
    try:
        return json.loads(world_file().read_text(encoding="utf-8")).get("furnished", [])
    except (OSError, ValueError):
        return []


def _mark(item):
    data = json.loads(world_file().read_text(encoding="utf-8"))
    data.setdefault("furnished", []).append(item)
    world_file().write_text(json.dumps(data, indent=2), encoding="utf-8")


def to_do():
    """(kind, name, file) still to load, for the files that are here."""
    done = set(_done())
    names = [r[0] for r in REGIONS]
    out = [("region", region, local(rel)) for region, rel in REGION_BUILDS.items()
           if region in names and f"region:{region}" not in done and local(rel).exists()]
    out += [("pack", rel.split("/")[-1], local(rel)) for rel in PACKS
            if f"pack:{rel.split('/')[-1]}" not in done and local(rel).exists()]
    return out


def _whole(path):
    """The archive itself if it's intact; if the download ends early (Outworldz's WhiteWood is cut short at the
    source), a repacked copy of everything readable, minus the half-written last file - the region loads without a
    few of its textures rather than not at all."""
    import gzip
    import tarfile
    try:
        with gzip.open(path) as g:
            while g.read(1 << 24):
                pass
        return path
    except (EOFError, OSError):
        pass
    fixed = path.with_name(path.name.replace(".tgz", "") + ".repacked.tgz")
    if fixed.exists():
        return fixed
    members = []
    with tarfile.open(path) as t, tarfile.open(fixed.with_suffix(".part"), "w:gz", format=tarfile.GNU_FORMAT) as out:
        try:
            for m in t:
                data = t.extractfile(m).read() if m.isfile() else None
                if m.isfile() and len(data) != m.size:
                    break
                members.append(m.name)
                out.addfile(m, __import__("io").BytesIO(data) if data is not None else None)
        except (EOFError, OSError, tarfile.TarError):
            pass
    fixed.with_suffix(".part").replace(fixed)
    return fixed


def _iar(path):
    """The .iar itself (zipped packs are unpacked next to it the first time)."""
    if path.suffix.lower() == ".iar":
        return path
    out = folder() / "iars"
    with zipfile.ZipFile(path) as z:
        names = [n for n in z.namelist() if n.lower().endswith(".iar")]
        for n in names:
            target = out / n.split("/")[-1]
            if not target.exists():
                out.mkdir(parents=True, exist_ok=True)
                target.write_bytes(z.read(n))
        return out / names[0].split("/")[-1] if names else None


def _wait(server, mark, ok, bad, seconds):
    """Wait for the server to say `ok` (True) or one of `bad` (False) after log position `mark`; yields while waiting."""
    end = time.time() + seconds
    while time.time() < end and server.running():
        log = server.log()[mark:]
        if ok in log:
            return True
        if any(b in log for b in bad):
            return False
        yield
    return False


def _stored(region_name):
    """How many objects of a region are in the region database (read alongside the running server)."""
    import sqlite3
    from . import REGIONS, opensim_bin
    rid = next((r[1] for r in REGIONS if r[0] == region_name), None)
    try:
        con = sqlite3.connect(f"file:{opensim_bin() / 'OpenSim.db'}?mode=ro", uri=True, timeout=5)
        try:
            return con.execute("SELECT COUNT(DISTINCT SceneGroupID) FROM prims WHERE RegionUUID = ?",
                               (rid,)).fetchone()[0]
        finally:
            con.close()
    except Exception:
        return -1


def _saved(region_name, want, seconds):
    """Wait for a loaded build to be saved: the server writes new objects out in the background, a big region over
    a minute or two, and a world stopped before then loses the rest. Done when the count reaches what was loaded
    (less the odd object the server drops as empty) or stops growing for two minutes."""
    end = time.time() + seconds
    last, changed, told = -1, time.time(), 0
    while time.time() < end:
        n = _stored(region_name)
        if want and n >= want * 0.98:
            return True
        if n != last:
            last, changed = n, time.time()
        elif n > 0 and time.time() - changed > 120:
            return True
        if time.time() - told > 20:
            told = time.time()
            yield f"  Saving {region_name}: {max(n, 0)} of {want} objects..."
        else:
            yield None                          # the caller paces this (the program's timer, once a second)
    return last > 0


def furnish(server):
    """A generator the program steps once a second: loads what's still to load, yielding a line of news as it goes.
    Its value (StopIteration.value) is how many things were loaded."""
    me = avatar()
    loaded = 0
    for kind, name, path in to_do():
        if kind == "region":
            yield f"Building {name} (first time only; the market takes a few minutes)..."
            mark = len(server.log())
            server.command(f"change region {name}")
            server.command(f'load oar "{_whole(path)}"')
            waiting = _wait(server, mark, "Successfully loaded archive", ("Aborting load", "Error loading"), 1800)
        else:
            iar = _iar(path)
            if iar is None:
                _mark(f"pack:{name}")
                continue
            yield f"Putting {name.rsplit('.', 1)[0]} in your inventory..."
            mark = len(server.log())
            server.command(f'load iar {me["first"]} {me["last"]} / "{me["password"]}" "{iar}"')
            waiting = _wait(server, mark, "items from archive", ("Load failed", "Aborting"), 900)   # "Loaded 293 items from archive"
        while True:
            try:
                next(waiting)
                yield None
            except StopIteration as stop:
                ok = stop.value
                break
        if ok and kind == "region":                 # wait until it's all written to the region database
            import re
            m = re.search(r"Loaded (\d+) scene objects", server.log()[mark:])
            want = int(m.group(1)) if m else 0
            server.command("backup")
            saving = _saved(name, want, 2400)            # a big build saves at a few objects a second
            while True:
                try:
                    note = next(saving)
                    yield note
                except StopIteration as stop:
                    ok = stop.value
                    break
        if ok:
            _mark(f"{kind}:{name}")
            loaded += 1
        else:
            yield f"Couldn't load {name}; it'll be tried again next time."
    server.command("change region root")
    return loaded
