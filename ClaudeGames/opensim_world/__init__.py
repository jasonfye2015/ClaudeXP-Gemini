"""The Furry Hollow: a real Second Life-style world on this PC, shared by every computer of the Timeline.

OpenSimulator (the open-source Second Life server) runs a private standalone grid on 127.0.0.1 with one region; a
viewer (Firestorm if the user has put one in Local Storage, else the Cool VL Viewer) logs the user in; and the main residents
walk around in it as NPCs. A scripted object in the region (the Hollow Keeper, loaded from an OAR this package
writes) creates the NPCs, passes what it hears in local chat to the bridge (bridge.py, a small web server inside the
computer that launched the world) and says the residents' replies, which the language model writes in each
resident's own voice - the same people, the same memories, as on the messengers.

Everything lives in Local Storage/SecondLife (nothing is installed on Windows):
    dotnet/       the .NET 8 runtime, unzipped            opensim/      OpenSimulator 0.9.3
    viewer/app/   the viewer, unpacked from its installer  world.json   the avatar and its password (generated)
"""
import json
import os
import secrets
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

# the regions: (name, region UUID, map position, UDP port)
REGIONS = [("Furry Hollow", "8a6b1d2e-4f7c-4c11-9d3e-2b5f7a9c1e01", (1000, 1000), 9000),
           ("Whisker Falls", "8a6b1d2e-4f7c-4c11-9d3e-2b5f7a9c1e02", (1001, 1000), 9001),
           ("Tailwind Beach", "8a6b1d2e-4f7c-4c11-9d3e-2b5f7a9c1e03", (1000, 1001), 9002),
           ("Lantern Market", "8a6b1d2e-4f7c-4c11-9d3e-2b5f7a9c1e04", (1001, 1001), 9003),
           # south of the block, walkable from it
           ("Love Island", "8a6b1d2e-4f7c-4c11-9d3e-2b5f7a9c1e05", (1000, 1002), 9004),
           ("Fantasy Island", "8a6b1d2e-4f7c-4c11-9d3e-2b5f7a9c1e06", (1001, 1002), 9005),
           # the adults' pair, off on their own to the east: reached by teleport, not by walking
           ("Whitewood", "8a6b1d2e-4f7c-4c11-9d3e-2b5f7a9c1e07", (1004, 1000), 9006),
           ("Castle LoveGlo", "8a6b1d2e-4f7c-4c11-9d3e-2b5f7a9c1e08", (1005, 1000), 9007)]
REGION = REGIONS[0][0]                       # where you arrive
GRID_PORT = 9000
BRIDGE_PORT = 9180
GRID_NAME = "Claude Timeline Grid"
HERE = Path(__file__).resolve().parent


def root():
    """Local Storage/SecondLife (the shared drive's copy of the world)."""
    try:
        from claudecore import host
        base = Path(host.local_storage())
    except Exception:
        base = Path(__file__).resolve().parents[2] / "Local Storage"
    return base / "SecondLife"


def dotnet():
    exe = root() / "dotnet" / "dotnet.exe"
    return exe if exe.is_file() else None


def opensim_bin():
    b = root() / "opensim" / "bin"
    return b if (b / "OpenSim.dll").is_file() else None


def viewer_exe():
    """Firestorm if the user dropped one in viewer/, else the Cool VL Viewer (both unpacked, not installed). Alchemy
    is never used: its Windows builds are made with Havok, which compiles out every grid but Second Life's own."""
    app = root() / "viewer"
    if not app.is_dir():
        return None
    found = sorted(app.rglob("*.exe"), key=lambda p: p.name.lower())
    for wanted in ("firestorm", "coolvlviewer"):
        for p in found:
            n = p.name.lower()
            if n.startswith(wanted) and "setup" not in n and "uninst" not in n:
                return p
    return None


def installed():
    return dotnet() is not None and opensim_bin() is not None and viewer_exe() is not None


# ---- the avatar ---------------------------------------------------------------------------------------------------
def world_file():
    return root() / "world.json"


def avatar():
    """{"first", "last", "password", "uuid"}: the user's avatar, made once from the Timeline profile."""
    try:
        data = json.loads(world_file().read_text(encoding="utf-8"))
        if data.get("first") and data.get("password"):
            return data
    except (OSError, ValueError):
        pass
    name = ""
    try:                                     # the Timeline profile: the same name on every computer
        prof = json.loads((Path(__file__).resolve().parents[2] / "Profile" / "profile.json").read_text(encoding="utf-8"))
        name = prof.get("handle") or prof.get("name") or ""
    except (OSError, ValueError):
        pass
    if not name:
        try:
            from claudecore import host
            name = host.user_name() or ""
        except Exception:
            pass
    first = "".join(ch for ch in name if ch.isalnum()) or "Visitor"
    data = {"first": first, "last": "Resident", "password": secrets.token_urlsafe(12), "uuid": str(uuid.uuid4())}
    world_file().parent.mkdir(parents=True, exist_ok=True)
    world_file().write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


# ---- configuring OpenSim ------------------------------------------------------------------------------------------
def _set_ini(path, section, key, value):
    """Set key = value in [section] of an OpenSim ini (uncommenting it if it's there, adding it if it isn't)."""
    lines = path.read_text(encoding="utf-8").splitlines()
    out, current, done = [], None, False
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith("[") and s.endswith("]"):
            if current == section and not done:
                out.append(f"    {key} = {value}")
                done = True
            current = s[1:-1]
        elif current == section and not done:
            bare = s.lstrip(";").strip()
            if bare.split("=")[0].strip() == key and "=" in bare and not bare.startswith("#"):
                out.append(f"    {key} = {value}")
                done = True
                continue
        out.append(line)
    if not done:
        if current == section:
            out.append(f"    {key} = {value}")
        else:
            out += ["", f"[{section}]", f"    {key} = {value}"]
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def configure():
    """Point OpenSim at this PC: standalone, one region, the user as estate owner, NPCs and the bridge allowed."""
    b = opensim_bin()
    me = avatar()
    ini = b / "OpenSim.ini"
    if not ini.exists():
        shutil.copy2(b / "OpenSim.ini.example", ini)
    for section, key, value in (
            ("Const", "BaseHostname", '"127.0.0.1"'), ("Const", "PublicPort", f'"{GRID_PORT}"'),
            ("Estates", "DefaultEstateName", '"Furry Hollow Estate"'),
            ("Estates", "DefaultEstateOwnerName", f'"{me["first"]} {me["last"]}"'),
            ("Estates", "DefaultEstateOwnerUUID", me["uuid"]),
            ("Estates", "DefaultEstateOwnerEMail", '"owner@furryhollow.local"'),
            ("Estates", "DefaultEstateOwnerPassword", f'"{me["password"]}"'),
            ("NPC", "Enabled", "true"), ("NPC", "AllowSenseAsAvatar", "true"),
            ("XEngine", "Enabled", "false"), ("YEngine", "Enabled", "true"),
            ("Startup", "DefaultScriptEngine", '"YEngine"'),
            ("Network", "OutboundDisallowForUserScriptsExcept", f"127.0.0.1:{BRIDGE_PORT}"),
            ("Architecture", "Include-Architecture", '"config-include/Standalone.ini"')):
        _set_ini(ini, section, key, value)
    (b / "config-include" / "osslEnable.ini").write_text(
        "; Written by the Claude Timeline: the Hollow Keeper may create and run the residents' NPCs.\n"
        "[OSSL]\n  osslNPC = true\n  Allow_osIsNpc = true\n  Allow_osAgentSaveAppearance = true\n", encoding="utf-8")
    for key, value in (("PrimRequestsPerSec", "5"), ("PrimRequestsBurst", "10")):
        _set_ini(ini, "ScriptsHttpRequestModule", key, value)
    common = b / "config-include" / "StandaloneCommon.ini"
    if common.exists():
        _set_ini(common, "GridInfoService", "gridname", f'"{GRID_NAME}"')
        _set_ini(common, "GridInfoService", "gridnick", '"claudetimeline"')
        _set_ini(common, "LoginService", "WelcomeMessage", '"Welcome to the Furry Hollow!"')
    regions = b / "Regions" / "Regions.ini"
    regions.parent.mkdir(exist_ok=True)
    regions.write_text("".join(
        f"[{name}]\nRegionUUID = {rid}\nLocation = {x},{y}\nInternalAddress = 0.0.0.0\nInternalPort = {port}\n"
        f"AllowAlternatePorts = False\nExternalHostName = 127.0.0.1\n\n"
        for name, rid, (x, y), port in REGIONS), encoding="utf-8")
    return me


def clear_keepers():
    """Take the Keepers out of the region database before the server starts: loading an OAR gives its objects new
    IDs, so without this every launch would add another Keeper (and another set of residents) to each region."""
    import sqlite3
    db = opensim_bin() / "OpenSim.db"
    if not db.exists():
        return 0
    con = sqlite3.connect(str(db))
    try:
        ids = [r[0] for r in con.execute("SELECT UUID FROM prims WHERE Name IN ('Hollow Keeper', 'Fitting Room')")]
        for table, column in (("primitems", "primID"), ("primshapes", "UUID"), ("prims", "UUID")):
            con.executemany(f"DELETE FROM {table} WHERE {column} = ?", [(i,) for i in ids])
        con.commit()
        return len(ids)
    except sqlite3.Error:
        return 0
    finally:
        con.close()


def _logged_out():
    """Nobody is in the world while the server is down: a server that was stopped hard leaves its avatars marked
    online, and the next login would be refused as 'already logged in'."""
    import sqlite3
    db = opensim_bin() / "griduser.db"
    if not db.exists():
        return
    con = sqlite3.connect(str(db))
    try:
        con.execute("UPDATE GridUser SET Online = 'False' WHERE Online <> 'False'")
        con.commit()
    except sqlite3.Error:
        pass
    finally:
        con.close()


# ---- the server ---------------------------------------------------------------------------------------------------
class Server:
    """OpenSim.dll under the bundled .NET, its console on a pipe and its output in opensim/bin/console.log."""

    def __init__(self):
        self.proc = None
        self.log_path = None

    def start(self):
        if self.running():
            return
        clear_keepers()
        _logged_out()
        b = opensim_bin()
        for compiled in (b / "ScriptEngines").rglob("*.yobj"):   # compiled scripts are cached by their text; a bad
            try:                                                   # compile would otherwise be reused for good
                compiled.unlink()
            except OSError:
                pass
        self.log_path = b / "console.log"
        env = dict(os.environ, DOTNET_ROOT=str(dotnet().parent), DOTNET_MULTILEVEL_LOOKUP="0")
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        self._log = open(self.log_path, "w", encoding="utf-8", errors="replace")
        self.proc = subprocess.Popen([str(dotnet()), "OpenSim.dll", "-console=basic"], cwd=str(b), env=env, stdin=subprocess.PIPE,
                                     stdout=self._log, stderr=subprocess.STDOUT, text=True, creationflags=flags)

    def running(self):
        return self.proc is not None and self.proc.poll() is None

    def log(self):
        try:
            return self.log_path.read_text(encoding="utf-8", errors="replace")
        except (OSError, AttributeError):
            return ""

    def ready(self):
        """Every region is up and taking logins."""
        return self.log().count("LOGINS ENABLED") >= len(REGIONS)

    def command(self, text):
        if self.running():
            try:
                self.proc.stdin.write(text + "\n")
                self.proc.stdin.flush()
            except OSError:
                pass

    def wait_ready(self, seconds=180):
        end = time.time() + seconds
        while time.time() < end and self.running():
            if self.ready():
                return True
            time.sleep(1)
        return self.ready()

    def stop(self, seconds=300):
        """Save every region, then shut down cleanly. A big region takes a while to write out, and killing the
        server before it has would lose what was built or loaded since the last save, so it gets five minutes."""
        if not self.running():
            return
        self.command("backup")
        self.command("shutdown")
        try:
            self.proc.wait(seconds)
        except subprocess.TimeoutExpired:
            self.proc.kill()
        try:
            self._log.close()
        except Exception:
            pass


def account_id(server, first, last, seconds=10):
    """The avatar's UUID, from the server console's `show account`."""
    import re
    mark = len(server.log())
    server.command(f"show account {first} {last}")
    end = time.time() + seconds
    while time.time() < end:
        m = re.search(r"ID:\s+([0-9a-f-]{36})", server.log()[mark:])
        if m:
            return m.group(1)
        time.sleep(0.5)
    return None


def place_keeper(server):
    """Make the user's avatar the estate owner and (re)load a Hollow Keeper into every region."""
    from . import oar
    me = avatar()
    owner = account_id(server, me["first"], me["last"])
    if owner is None:
        return False
    if owner != me.get("uuid"):
        me["uuid"] = owner
        world_file().write_text(json.dumps(me, indent=2), encoding="utf-8")
    server.command(f"estate set owner 101 {me['first']} {me['last']}")
    for name, *_rest in REGIONS:             # a Keeper in every region, each its own object
        path = oar.write(root() / "keepers" / f"{name}.oar", owner, name)
        done = server.log().count("Start scripts done")
        server.command(f"change region {name}")
        server.command(f'load oar --merge "{path}"')
        end = time.time() + 30               # one at a time: the script engine's first start in each region isn't
        while time.time() < end and server.log().count("Start scripts done") <= done:   # safe to run in parallel
            time.sleep(0.25)
        time.sleep(1)
    server.command("change region root")
    return True


GRID_KEY = f"127.0.0.1:{GRID_PORT}"


def register_grid():
    """Add the Timeline's grid to the viewer's own list of grids (what its 'add grid' dialog writes): the viewer
    keeps it in its settings folder, Firestorm_x64."""
    from xml.sax.saxutils import escape
    uri = f"http://127.0.0.1:{GRID_PORT}/"
    entry = (f"<key>{GRID_KEY}</key><map><key>keyname</key><string>{GRID_KEY}</string>"
             f"<key>grid_login_id</key><string>{escape(GRID_NAME)}</string>"
             f"<key>label</key><string>{escape(GRID_NAME)}</string>"
             f"<key>login_uri</key><array><string>{uri}</string></array>"
             f"<key>helper_uri</key><string>{uri}</string><key>login_page</key><string>{uri}</string>"
             f"<key>platform</key><string>OpenSim</string><key>favorite</key><boolean>1</boolean></map>")
    appdata = Path(os.environ.get("APPDATA", ""))
    for name in ["Firestorm_x64"]:
        target = appdata / name / "user_settings" / "grids_user.xml"
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            text = target.read_text(encoding="utf-8")
        except OSError:
            text = ""
        if f"<key>{GRID_KEY}</key>" in text:
            continue
        if "<map>" in text:
            text = text.replace("<map>", "<map>" + entry, 1)
        else:
            text = f"<?xml version=\"1.0\" ?><llsd><map>{entry}</map></llsd>\n"
        target.write_text(text, encoding="utf-8")


def launch_viewer():
    """The viewer, logged straight in to the Furry Hollow."""
    me = avatar()
    exe = viewer_exe()
    login = ["--login", me["first"], me["last"], me["password"], "--multiple"]
    if exe.name.lower().startswith("firestorm"):
        register_grid()
        args = [str(exe), "--grid", GRID_KEY, "--loginuri", f"http://127.0.0.1:{GRID_PORT}/"] + login
    else:                                    # Cool VL ships a "localhost9000" grid (http://127.0.0.1:9000/): ours
        args = [str(exe), "--grid", f"localhost{GRID_PORT}"] + login
    return subprocess.Popen(args, cwd=str(exe.parent))
