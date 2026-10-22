"""Furnishing the world: the first time the server starts with these files in place, each region gets a ready-made
build and the avatar's inventory gets the packs below. What's been loaded is remembered in world.json, so it happens
once (and a region whose build was loaded keeps everything built in it since).

All of it is Linda Kellie's collection as kept by Zadaroo (https://www.zadaroo.com), released CC0 - free for any use.
The files go in Local Storage/SecondLife/downloads/zadaroo (download_all() fetches them)."""
import json
import time
import urllib.request
import zipfile

from . import REGIONS, avatar, root, world_file

SOURCE = "https://files.zadaroo.com/"
REGION_BUILDS = {"Furry Hollow": "oars/LK-MountainRetreat.tgz",      # a forest village in the hills
                 "Whisker Falls": "oars/LakeHouse.tgz",               # a lake with a house on it
                 "Tailwind Beach": "oars/LK-TikiSummer.tgz",          # tiki huts and sand
                 "Lantern Market": "oars/FreebieMall.tgz"}            # shops full of things to take
PACKS = ["iars/furry-avatars.iar", "iars/FULLAVATARS.zip", "iars/AVATARHAIR.zip", "iars/LK-ANIMALS.zip",
         "iars/LK-ANIMATIONS.zip", "iars/LK-FURNITURE.zip", "iars/LK-HOUSES.zip"]


def folder():
    return root() / "downloads" / "zadaroo"


def local(rel):
    return folder() / rel.split("/")[-1]


def download_all(progress=print):
    folder().mkdir(parents=True, exist_ok=True)
    for rel in list(REGION_BUILDS.values()) + PACKS:
        if not local(rel).exists():
            progress(f"Downloading {rel}...")
            tmp = local(rel).with_suffix(".part")
            urllib.request.urlretrieve(SOURCE + rel, tmp)
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
            server.command(f'load oar "{path}"')
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
        if ok:
            _mark(f"{kind}:{name}")
            loaded += 1
        else:
            yield f"Couldn't load {name}; it'll be tried again next time."
    server.command("change region root")
    return loaded
