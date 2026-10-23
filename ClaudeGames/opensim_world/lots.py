"""Cutting the homes regions into lots. The builds come as one region-sized parcel; before the server starts, each
homes region that still has only that one parcel is divided into a grid of lots (COLS x ROWS), written straight
into the region database's land table, so every resident can have a place of their own (personas.py hands them out,
and the Studio's Home parcel list shows them). The lots belong to the user's avatar, as the estate owner."""
import uuid

from . import REGIONS, avatar, opensim_bin
from .personas import HOME_REGIONS

COLS, ROWS = 5, 4                      # 20 lots a region, about 51 x 64 m each
CELL = 4                               # parcel cells are 4 m; a region is 64 x 64 of them
LANDFLAGS = 671129691                  # what the builds' parcels carry (build, fly, scripts, show in search...)


def _bitmap(c0, c1, r0, r1):
    """A land bitmap (64x64 bits, row-major, one bit per 4 m cell) covering cells c0..c1 x r0..r1."""
    bits = bytearray(512)
    for r in range(r0, r1):
        for c in range(c0, c1):
            i = r * 64 + c
            bits[i // 8] |= 1 << (i % 8)
    return bytes(bits)


def cut(region_name, rows=None):
    """Divide a region into lots if it still has just the one parcel. Returns how many lots it now has."""
    import sqlite3
    rid = next((r[1] for r in REGIONS if r[0] == region_name), None)
    db = opensim_bin() / "OpenSim.db" if opensim_bin() else None
    if not rid or db is None or not db.exists():
        return 0
    owner = avatar().get("uuid", "00000000-0000-0000-0000-000000000000")
    con = sqlite3.connect(str(db), timeout=10)
    try:
        have = con.execute("SELECT COUNT(*) FROM land WHERE RegionUUID = ?", (rid,)).fetchone()[0]
        if have > 1:
            return have
        old = con.execute("SELECT UUID FROM land WHERE RegionUUID = ?", (rid,)).fetchall()
        for (u,) in old:
            con.execute("DELETE FROM landaccesslist WHERE LandUUID = ?", (u,))
        con.execute("DELETE FROM land WHERE RegionUUID = ?", (rid,))
        n = 0
        xs = [round(i * 64 / COLS) for i in range(COLS + 1)]
        ys = [round(i * 64 / ROWS) for i in range(ROWS + 1)]
        for r in range(ROWS):
            for c in range(COLS):
                n += 1
                cells = (xs[c + 1] - xs[c]) * (ys[r + 1] - ys[r])
                con.execute(
                    "INSERT INTO land (UUID, RegionUUID, LocalLandID, Bitmap, Name, Desc, OwnerUUID, IsGroupOwned, Area, "
                    "AuctionID, Category, ClaimDate, ClaimPrice, GroupUUID, SalePrice, LandStatus, LandFlags, LandingType, "
                    "MediaAutoScale, MediaTextureUUID, MediaURL, MusicURL, PassHours, PassPrice, SnapshotUUID, "
                    "UserLocationX, UserLocationY, UserLocationZ, UserLookAtX, UserLookAtY, UserLookAtZ, AuthbuyerID, "
                    "OtherCleanTime, Dwell, MediaType, MediaDescription, MediaSize, MediaLoop, ObscureMusic, ObscureMedia, "
                    "SeeAVs, AnyAVSounds, GroupAVSounds, environment) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,"
                    "?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (str(uuid.uuid4()), rid, n, _bitmap(xs[c], xs[c + 1], ys[r], ys[r + 1]),
                     f"{region_name} lot {n}", "A resident's own place in the Furry Hollow.", owner, "False",
                     cells * CELL * CELL, 0, 0, 0, 0, "00000000-0000-0000-0000-000000000000", 0, 0, LANDFLAGS, 0,
                     0, "00000000-0000-0000-0000-000000000000", "", "", 0.0, 0, "00000000-0000-0000-0000-000000000000",
                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, "00000000-0000-0000-0000-000000000000", 0, 0, "none/none", "",
                     "0,0", 0, 0, 0, 1, 1, 1, ""))
        con.commit()
        return n
    finally:
        con.close()


def cut_homes():
    """Every homes region that's been built but not yet cut up (called before the server starts)."""
    import json
    from . import world_file
    try:
        furnished = json.loads(world_file().read_text(encoding="utf-8")).get("furnished", [])
    except (OSError, ValueError):
        furnished = []
    done = {}
    for region in HOME_REGIONS:
        if f"region:{region}" in furnished:
            done[region] = cut(region)
    return done
