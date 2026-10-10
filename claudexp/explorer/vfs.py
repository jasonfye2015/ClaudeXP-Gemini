"""ClaudeXP's drives: B: floppy, C: the XP hard disk (data/Drive C), D: CD drive, E: an external drive
holding the real 'Local Storage' folder. Converts between real paths and C:\\... style paths, builds C:
the first time, and keeps the Recycle Bin."""
import json
import os
import random
import shutil
import time
from dataclasses import dataclass
from pathlib import Path

from ..paths import DATA, ROOT, SOUNDS

DRIVE_C = DATA / "Drive C"
RECYCLE_DIR = DATA / "Recycle Bin"
RECYCLE_INDEX = RECYCLE_DIR / "INFO.json"
C_TOTAL, C_FREE = int(19.53 * 2**30), int(7.21 * 2**30)


def local_storage():
    """The real folder behind E: (accepts the folder's original 'Local Stoage' spelling too)."""
    for name in ("Local Storage", "Local Stoage"):
        if (ROOT / name).is_dir():
            return ROOT / name
    path = ROOT / "Local Storage"
    path.mkdir(exist_ok=True)
    return path


@dataclass
class Drive:
    letter: str
    label: str
    kind: str            # hdd | external | floppy | cd
    root: Path = None

    @property
    def name(self):
        return f"{self.label} ({self.letter}:)"

    def usage(self):
        """(total, free) bytes, or None for an empty removable drive."""
        if self.kind == "hdd":
            used = sum(f.stat().st_size for f in self.root.rglob("*") if f.is_file()) if self.root.exists() else 0
            return C_TOTAL, max(0, C_FREE - used)
        if self.kind == "external":
            u = shutil.disk_usage(self.root)
            return u.total, u.free
        return None


def drives():
    cd_root = DATA / "virtual_disc_d" if (DATA / "virtual_disc_d").exists() and any((DATA / "virtual_disc_d").iterdir()) else None
    drvs = [
        Drive("B", "3½ Floppy", "floppy"),
        Drive("C", "Local Disk", "hdd", DRIVE_C),
        Drive("D", "CD Drive", "cd", cd_root),
        Drive("E", "External Drive", "external", local_storage()),
    ]
    try:
        from ..programs.alcohol import virtual_drive
        vd = virtual_drive()
        if vd:
            drvs.append(vd)
    except Exception:
        pass
    return drvs


def drive(letter):
    return next((d for d in drives() if d.letter == letter.upper()), None)


# ---- path mapping ------------------------------------------------------------------------------

def to_virtual(path):
    """Real path -> 'C:\\Documents and Settings\\...' (or None if it isn't on a drive)."""
    path = Path(path).resolve()
    for d in drives():
        if d.root is None:
            continue
        root = d.root.resolve()
        if path == root or root in path.parents:
            rel = path.relative_to(root)
            return f"{d.letter}:\\" + "\\".join(rel.parts)
    if path == RECYCLE_DIR.resolve():
        return "Recycle Bin"
    return None


def to_real(vpath):
    """'C:\\WINDOWS' -> real Path (None if it doesn't map to a real drive folder)."""
    vpath = vpath.strip().replace("/", "\\")
    if len(vpath) >= 2 and vpath[1] == ":":
        d = drive(vpath[0])
        if d is None or d.root is None:
            return None
        rest = vpath[2:].strip("\\")
        return d.root / rest if rest else d.root
    return None


# ---- special folders --------------------------------------------------------------------------------

def user_home():
    from ..user import profile_name, user_name
    return DRIVE_C / "Documents and Settings" / profile_name()


def my_documents():
    return user_home() / "My Documents"


def my_pictures():
    return my_documents() / "My Pictures"


def my_music():
    return my_documents() / "My Music"


def shared_documents():
    return DRIVE_C / "Documents and Settings" / "All Users" / "Documents"


# ---- building C: ---------------------------------------------------------------------------------------

EXECUTABLES = {   # file name -> ClaudeXP program it launches
    "claudeaim.exe": "aim", "claudeirc.exe": "irc", "claudemuck.exe": "muck", "netscape.exe": "navigator",
    "notepad.exe": "notepad", "explorer.exe": "mycomputer", "claudeshield.exe": "antivirus",
    "mspaint.exe": "paint", "calc.exe": "calc", "cmd.exe": "cmd", "taskmgr.exe": "taskmgr",
    "dfrgntfs.exe": "defrag", "wupdmgr.exe": "winupdate", "isignup.exe": "connect", "wmplayer.exe": "wmp",
    "wordpad.exe": "wordpad", "msimn.exe": "outlook", "wab.exe": "wab", "charmap.exe": "charmap",
    "geminiword.exe": "gemini_word", "geminiexcel.exe": "gemini_excel",
    "geminipowerpoint.exe": "gemini_powerpoint", "geminioutlook.exe": "gemini_outlook",
    "geminiaccess.exe": "gemini_access", "geminipublisher.exe": "gemini_publisher",
    "geminiphoto.exe": "gemini_photo", "geminidraw.exe": "gemini_draw", "geminiacrobat.exe": "gemini_acrobat",
    "geminidistiller.exe": "gemini_distiller",
    "cleanmgr.exe": "cleanmgr", "sndrec32.exe": "sndrec", "pinball.exe": "pinball",
    "claudetv.exe": "tv", "furtv.exe": "tv", "furcomix.exe": "comix", "furfolio.exe": "folio", "furstory.exe": "stories", "furcd.exe": "cdviewer", "furcon.exe": "furcon", "fceu.exe": "nes", "snes9x.exe": "snes", "gambatte.exe": "gb",
    "gambatte_gbc.exe": "gbc", "mgba.exe": "gba", "picodrive.exe": "gen", "gpgx.exe": "sms", "gearsystem.exe": "gg", "applewin.exe": "apple2",
    "doom.exe": "doom", "doom2.exe": "doom2", "wolf3d.exe": "wolf3d", "heretic.exe": "heretic", "hexen.exe": "hexen",
    "ski.exe": "skifree", "jezzball.exe": "jezzball",
    "taipei.exe": "taipei", "rodent.exe": "rodent", "blockfall.exe": "blockfall", "tripeaks.exe": "tripeaks",
    "golf.exe": "golf", "flashpla.exe": "flash", "claudeamp.exe": "claudeamp", "winamp.exe": "claudeamp",
    "furvideo.exe": "furvideo", "stylexp.exe": "stylexp", "claudetorrent.exe": "torrent", "furdir.exe": "furdir", "clauderpg.exe": "rpg",
    "nero.exe": "nero", "alcohol.exe": "alcohol120", "alcohol120.exe": "alcohol120",
    "winrar.exe": "winrar", "winzip.exe": "winzip", "winzip32.exe": "winzip",
}
SYSTEM32 = ["advapi32.dll", "comctl32.dll", "comdlg32.dll", "gdi32.dll", "kernel32.dll", "mshtml.dll",
            "msvcrt.dll", "ole32.dll", "oleaut32.dll", "rpcrt4.dll", "shell32.dll", "shlwapi.dll", "user32.dll",
            "wininet.dll", "winmm.dll", "ws2_32.dll", "ntdll.dll", "urlmon.dll", "svchost.exe", "winlogon.exe",
            "services.exe", "lsass.exe", "msiexec.exe", "calc.exe", "mspaint.exe", "sndrec32.exe",
            "wupdmgr.exe", "dfrgntfs.exe", "taskmgr.exe", "cmd.exe", "regedt32.exe"]
FONTS = ["tahoma.ttf", "tahomabd.ttf", "arial.ttf", "arialbd.ttf", "times.ttf", "cour.ttf", "verdana.ttf",
         "trebuc.ttf", "georgia.ttf", "comic.ttf", "impact.ttf", "lucon.ttf", "marlett.ttf", "webdings.ttf"]
BOOT_INI = """[boot loader]
timeout=30
default=multi(0)disk(0)rdisk(0)partition(1)\\WINDOWS
[operating systems]
multi(0)disk(0)rdisk(0)partition(1)\\WINDOWS="Microsoft Windows XP Home Edition" /fastdetect
"""
WIN_INI = """; for 16-bit app support
[fonts]
[extensions]
[mci extensions]
[files]
[Mail]
MAPI=1
"""
README = """Welcome to your new computer!

This is your My Documents folder. Save your files here so you can find them later.

Tip: your external drive (E:) is a great place to back up important files.
"""
MARKER = ".claudexp-drive"


def _fake(path, lo_kb=8, hi_kb=96, text=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if text is not None:
        path.write_text(text, encoding="utf-8", newline="\r\n")
    else:
        path.write_bytes(os.urandom(random.randint(lo_kb, hi_kb) * 1024))
    old = time.time() - random.uniform(55, 70) * 86400   # shows as summer 2001 (XP came out in August)
    os.utime(path, (old, old))


def _ensure_wallpapers():
    """C:\\WINDOWS\\Web\\Wallpaper holds the Windows XP wallpapers (and the account pictures, under All Users)."""
    walls = DRIVE_C / "WINDOWS" / "Web" / "Wallpaper"
    if not walls.exists():
        walls.mkdir(parents=True)
        for f in (ROOT / "assets" / "backgrounds").glob("*"):
            shutil.copy2(f, walls / f.name)
    pics = (DRIVE_C / "Documents and Settings" / "All Users" / "Application Data" / "Microsoft" /
            "User Account Pictures" / "Default Pictures")
    if not pics.exists():
        pics.mkdir(parents=True)
        for f in (ROOT / "assets" / "user_icons").glob("*"):
            shutil.copy2(f, pics / f.name)


def _ensure_themes():
    """C:\\WINDOWS\\Resources\\Themes: the built-in .theme files."""
    try:
        from .. import themes
        themes.install_files()
    except Exception:
        pass


def setup_c():
    """Create the XP hard drive the first time (and keep adding anything missing)."""
    DRIVE_C.mkdir(parents=True, exist_ok=True)
    office = DRIVE_C / "Program Files" / "Gemini Office"
    for name in ("GeminiWord.exe", "GeminiExcel.exe", "GeminiPowerPoint.exe", "GeminiOutlook.exe",
                 "GeminiAccess.exe", "GeminiPublisher.exe"):
        executable = office / name
        if not executable.exists():
            _fake(executable, 200, 900)
    adobe = DRIVE_C / "Program Files" / "GeminiAdobe"
    for name in ("GeminiPhoto.exe", "GeminiDraw.exe", "GeminiAcrobat.exe", "GeminiDistiller.exe"):
        executable = adobe / name
        if not executable.exists():
            _fake(executable, 200, 900)
    for extra_exe in (DRIVE_C / "Program Files" / "Ahead" / "Nero" / "nero.exe",
                      DRIVE_C / "Program Files" / "Alcohol Soft" / "Alcohol 120" / "Alcohol.exe",
                      DRIVE_C / "Program Files" / "WinRAR" / "WinRAR.exe",
                      DRIVE_C / "Program Files" / "WinZip" / "winzip32.exe"):
        if not extra_exe.exists():
            _fake(extra_exe, 200, 900)
    if (DRIVE_C / MARKER).exists():
        _ensure_wallpapers()
        _ensure_themes()
        return
    from ..user import profile_name, user_name
    home = DRIVE_C / "Documents and Settings" / profile_name()
    for sub in ("Desktop", "Favorites", "Start Menu", "My Documents/My Pictures", "My Documents/My Music",
                "My Documents/My Received Files", "Local Settings/Temp",
                "Local Settings/Temporary Internet Files"):
        (home / sub).mkdir(parents=True, exist_ok=True)
    _fake(home / "My Documents" / "Read Me.txt", text=README)
    (DRIVE_C / "Documents and Settings" / "All Users" / "Documents" / "Shared Music").mkdir(parents=True, exist_ok=True)
    (DRIVE_C / "Documents and Settings" / "All Users" / "Documents" / "Shared Pictures").mkdir(parents=True, exist_ok=True)
    pf = DRIVE_C / "Program Files"
    for rel in ("ClaudeAIM/ClaudeAIM.exe", "ClaudeIRC/ClaudeIRC.exe", "ClaudeMUCK/ClaudeMUCK.exe",
                "Netscape/Navigator/netscape.exe", "ClaudeShield AntiVirus/ClaudeShield.exe",
                "America Online/isignup.exe", "Windows Media Player/wmplayer.exe", "Outlook Express/msimn.exe",
                "ClaudeTV/ClaudeTV.exe", "FurComix Reader/FurComix.exe",
                "FurFolio Reader/FurFolio.exe", "FurFolio Reader/FurStory.exe",
                "Fur CD Viewer/FurCD.exe", "Furry Con CD Viewer/FurCon.exe", "Furry Video Browser/FurVideo.exe",
                "Macromedia/Flash Player/FlashPla.exe", "ClaudeAmp/ClaudeAmp.exe", "TGTSoft/StyleXP/StyleXP.exe", "ClaudeTorrent/ClaudeTorrent.exe", "The Fur Directory/FurDir.exe", "ClaudeRPG/ClaudeRPG.exe",
                "FCE Ultra/fceu.exe", "Snes9x/snes9x.exe",
                "Gambatte/gambatte.exe", "Gambatte/gambatte_gbc.exe", "mGBA/mgba.exe", "PicoDrive/picodrive.exe",
                "Genesis Plus/gpgx.exe", "Gearsystem/gearsystem.exe", "AppleWin/applewin.exe",
                "Doom/doom.exe", "Doom II/doom2.exe", "Wolfenstein 3D/wolf3d.exe", "Heretic/heretic.exe",
                "Hexen/hexen.exe", "Entertainment Pack/ski.exe", "Entertainment Pack/jezzball.exe",
                "Entertainment Pack/taipei.exe", "Entertainment Pack/rodent.exe", "Entertainment Pack/blockfall.exe",
                "Entertainment Pack/tripeaks.exe", "Entertainment Pack/golf.exe"):
        _fake(pf / rel, 200, 900)
    (pf / "Common Files").mkdir(parents=True, exist_ok=True)
    win = DRIVE_C / "WINDOWS"
    for name in SYSTEM32:
        _fake(win / "system32" / name)
    for name in FONTS:
        _fake(win / "Fonts" / name, 40, 300)
    media = win / "Media"
    media.mkdir(parents=True, exist_ok=True)
    for wav in SOUNDS.glob("*.wav"):
        shutil.copy2(wav, media / wav.name)
    for name in ("notepad.exe", "explorer.exe", "regedit.exe"):
        _fake(win / name, 60, 1000)
    _fake(win / "win.ini", text=WIN_INI)
    _fake(win / "system.ini", text="; for 16-bit app support\n[drivers]\nwave=mmdrv.dll\ntimer=timer.drv\n")
    (win / "Temp").mkdir(exist_ok=True)
    _fake(DRIVE_C / "boot.ini", text=BOOT_INI)
    _fake(DRIVE_C / "AUTOEXEC.BAT", text="")
    _fake(DRIVE_C / "CONFIG.SYS", text="")
    _ensure_wallpapers()
    (DRIVE_C / MARKER).write_text("ClaudeXP drive C")


def hidden(path):
    """Files Explorer doesn't show (like XP's hidden/system files)."""
    return Path(path).name in (MARKER, "INFO.json")


# ---- protected folders -------------------------------------------------------------------------------------

def protected(path):
    """System folders XP wouldn't let you delete or rename."""
    path = Path(path).resolve()
    keep = [DRIVE_C, DRIVE_C / "WINDOWS", DRIVE_C / "Program Files", DRIVE_C / "Documents and Settings",
            user_home(), my_documents(), local_storage()]
    return path in [k.resolve() for k in keep] or (DRIVE_C / "WINDOWS").resolve() in path.parents


# ---- Recycle Bin ----------------------------------------------------------------------------------------------

def _index():
    try:
        return json.loads(RECYCLE_INDEX.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _save_index(index):
    RECYCLE_DIR.mkdir(parents=True, exist_ok=True)
    RECYCLE_INDEX.write_text(json.dumps(index, indent=2), encoding="utf-8")


def recycle(path):
    """Move a file or folder into the Recycle Bin (it can be restored)."""
    path = Path(path)
    RECYCLE_DIR.mkdir(parents=True, exist_ok=True)
    index = _index()
    n = 1
    while (RECYCLE_DIR / f"D{n}{path.suffix}").exists() or f"D{n}{path.suffix}" in index:
        n += 1
    stored = f"D{n}{path.suffix}"
    shutil.move(str(path), str(RECYCLE_DIR / stored))
    index[stored] = {"original": str(path), "deleted": time.time()}
    _save_index(index)


def recycled():
    """[(stored path, original path, deleted time)] for what's in the Recycle Bin."""
    out = []
    for stored, info in _index().items():
        p = RECYCLE_DIR / stored
        if p.exists():
            out.append((p, Path(info["original"]), info["deleted"]))
    return out


def restore(stored):
    index = _index()
    info = index.pop(Path(stored).name, None)
    if info is None:
        return False
    target = Path(info["original"])
    target.parent.mkdir(parents=True, exist_ok=True)
    while target.exists():
        target = target.with_name(f"Copy of {target.name}")
    shutil.move(str(stored), str(target))
    _save_index(index)
    return True


def empty_recycle_bin():
    """Delete everything in the Recycle Bin for good."""
    from .. import clippy, sound
    if recycled():
        sound.play("recycle")
        clippy.notify("recycle", count=len(recycled()))
    for stored, _orig, _when in recycled():
        if stored.is_dir():
            shutil.rmtree(stored, ignore_errors=True)
        else:
            stored.unlink(missing_ok=True)
    _save_index({})
