"""Claude7's drives: C: the Windows 7 hard disk (data/Drive C, laid out the Windows 7 way: Users, Program Files,
Windows), D: the DVD drive, E: the external drive holding the shared Local Storage. Converts between real paths and
C:\\... style paths, builds C: the first time, and keeps the Recycle Bin. The same interface as ClaudeXP's
explorer.vfs, which the period programs (Windows Explorer among them) use here."""
import json
import os
import random
import shutil
import time
from dataclasses import dataclass
from pathlib import Path

from .paths import BACKGROUNDS, DATA, SOUNDS, USER_PICTURES

DRIVE_C = DATA / "Drive C"
RECYCLE_DIR = DATA / "Recycle Bin"
RECYCLE_INDEX = RECYCLE_DIR / "INFO.json"
C_TOTAL, C_FREE = int(931.51 * 2**30), int(812.26 * 2**30)


def local_storage():
    """The real folder behind E:: the Timeline's shared Local Storage (the launcher's Config can point elsewhere)."""
    from . import timeline as tl
    chosen = tl.setting("local_storage")
    if chosen and (tl.TIMELINE / chosen).is_dir():
        return tl.TIMELINE / chosen
    for name in ("Local Storage", "Local Stoage"):
        if (tl.TIMELINE / name).is_dir():
            return tl.TIMELINE / name
    path = tl.TIMELINE / "Local Storage"
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
        Drive("C", "Local Disk", "hdd", DRIVE_C),
        Drive("D", "DVD RW Drive", "cd", cd_root),
        Drive("E", "External Drive", "external", local_storage()),
    ]
    try:
        from claudexp.programs.alcohol import virtual_drive
        vd = virtual_drive()
        if vd:
            drvs.append(vd)
    except Exception:
        pass
    return drvs


def drive(letter):
    return next((d for d in drives() if d.letter == letter.upper()), None)


# ---- path mapping ------------------------------------------------------------------------------------------------

def to_virtual(path):
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
    vpath = vpath.strip().replace("/", "\\")
    if len(vpath) >= 2 and vpath[1] == ":":
        d = drive(vpath[0])
        if d is None or d.root is None:
            return None
        rest = vpath[2:].strip("\\")
        return d.root / rest if rest else d.root
    return None


# ---- special folders ---------------------------------------------------------------------------------------------

def user_home():
    from .user import profile_name
    return DRIVE_C / "Users" / profile_name()


def my_documents():
    return user_home() / "Documents"


def my_pictures():
    return user_home() / "Pictures"


def my_music():
    return user_home() / "Music"


def my_videos():
    return user_home() / "Videos"


def downloads():
    return user_home() / "Downloads"


def shared_documents():
    return DRIVE_C / "Users" / "Public" / "Documents"


# ---- building C: -------------------------------------------------------------------------------------------------

EXECUTABLES = {   # file name -> program it launches
    "claudeaim.exe": "aim", "claudeirc.exe": "irc", "claudemuck.exe": "muck", "iexplore.exe": "iexplore",
    "notepad.exe": "notepad", "explorer.exe": "mycomputer", "claudeshield.exe": "antivirus", "realplay.exe": "realplayer",
    "kiwix-desktop.exe": "kiwix", "claudecraft.exe": "claudecraft", "msconfig.exe": "msconfig",
    "claudecadia.exe": "furcadia", "claudequest.exe": "claudequest", "claudeablo.exe": "claudeablo",
    "claudecity.exe": "claudecity", "scorch.exe": "scorched", "claudejeweled.exe": "claudejeweled",
    "claudeggle.exe": "claudeggle", "quicktimeplayer.exe": "quicktime", "moviemk.exe": "moviemaker",
    "ad-aware.exe": "adaware", "mspaint.exe": "paint", "calc.exe": "calc", "cmd.exe": "cmd", "taskmgr.exe": "taskmgr",
    "dfrgui.exe": "defrag", "wuapp.exe": "winupdate", "wmplayer.exe": "wmp", "wordpad.exe": "wordpad",
    "wlmail.exe": "outlook", "wab.exe": "wab", "charmap.exe": "charmap",
    "geminiword.exe": "gemini_word", "geminiexcel.exe": "gemini_excel", "geminipowerpoint.exe": "gemini_powerpoint",
    "geminioutlook.exe": "gemini_outlook", "geminiaccess.exe": "gemini_access", "geminipublisher.exe": "gemini_publisher",
    "geminiphoto.exe": "gemini_photo", "geminidraw.exe": "gemini_draw", "geminiacrobat.exe": "gemini_acrobat",
    "geminidistiller.exe": "gemini_distiller", "cleanmgr.exe": "cleanmgr", "soundrecorder.exe": "sndrec",
    "sndvol.exe": "sndvol", "pinball.exe": "pinball", "claudetv.exe": "tv", "furcomix.exe": "comix",
    "furfolio.exe": "folio", "furstory.exe": "stories", "furcd.exe": "cdviewer", "furcon.exe": "furcon",
    "fceu.exe": "nes", "snes9x.exe": "snes", "gambatte.exe": "gb", "gambatte_gbc.exe": "gbc", "mgba.exe": "gba",
    "picodrive.exe": "gen", "gpgx.exe": "sms", "gearsystem.exe": "gg", "applewin.exe": "apple2",
    "mupen64plus.exe": "n64", "msnmsgr.exe": "msn", "ypager.exe": "yim", "icq.exe": "icq", "trillian.exe": "trillian",
    "skype.exe": "skype", "kik.exe": "kik", "doom.exe": "doom", "doom2.exe": "doom2", "wolf3d.exe": "wolf3d",
    "heretic.exe": "heretic", "hexen.exe": "hexen", "ski.exe": "skifree", "jezzball.exe": "jezzball",
    "taipei.exe": "taipei", "rodent.exe": "rodent", "blockfall.exe": "blockfall", "tripeaks.exe": "tripeaks",
    "golf.exe": "golf", "flashplayer.exe": "flash", "claudeamp.exe": "claudeamp", "winamp.exe": "claudeamp",
    "furvideo.exe": "furvideo", "claudetorrent.exe": "torrent", "furdir.exe": "furdir", "clauderpg.exe": "rpg",
    "nero.exe": "nero", "alcohol.exe": "alcohol120", "alcohol120.exe": "alcohol120", "winrar.exe": "winrar",
    "winzip.exe": "winzip", "winzip32.exe": "winzip", "stikynot.exe": "stickynotes", "snippingtool.exe": "snipping",
    "sidebar.exe": "gadgets", "chess.exe": "chess", "control.exe": "controlpanel", "helppane.exe": "helpctr",
    "secondlife.exe": "secondlife",
}
SYSTEM32 = ["advapi32.dll", "comctl32.dll", "comdlg32.dll", "gdi32.dll", "kernel32.dll", "mshtml.dll",
            "msvcrt.dll", "ole32.dll", "oleaut32.dll", "rpcrt4.dll", "shell32.dll", "shlwapi.dll", "user32.dll",
            "wininet.dll", "winmm.dll", "ws2_32.dll", "ntdll.dll", "urlmon.dll", "dwmapi.dll", "uxtheme.dll",
            "svchost.exe", "winlogon.exe", "services.exe", "lsass.exe", "dwm.exe", "csrss.exe", "msiexec.exe",
            "calc.exe", "mspaint.exe", "SoundRecorder.exe", "SndVol.exe", "wuapp.exe", "dfrgui.exe", "taskmgr.exe",
            "cmd.exe", "regedt32.exe", "control.exe", "SnippingTool.exe", "StikyNot.exe", "charmap.exe", "cleanmgr.exe",
            "msconfig.exe", "rstrui.exe", "msinfo32.exe", "notepad.exe", "HelpPane.exe"]
FONTS = ["segoeui.ttf", "segoeuib.ttf", "segoeuii.ttf", "tahoma.ttf", "tahomabd.ttf", "arial.ttf", "arialbd.ttf",
         "times.ttf", "cour.ttf", "verdana.ttf", "trebuc.ttf", "georgia.ttf", "comic.ttf", "impact.ttf",
         "consola.ttf", "calibri.ttf", "cambria.ttc", "lucon.ttf", "marlett.ttf", "webdings.ttf"]
README = """Welcome to your new computer!

This is your Documents library. Save your files here so you can find them later.

Tip: your external drive (E:) is a great place to back up important files.
"""
MARKER = ".claude7-drive"


def _fake(path, lo_kb=8, hi_kb=96, text=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if text is not None:
        path.write_text(text, encoding="utf-8", newline="\r\n")
    else:
        path.write_bytes(os.urandom(random.randint(lo_kb, hi_kb) * 1024))
    old = time.time() - random.uniform(60, 400) * 86400
    os.utime(path, (old, old))


def _ensure_wallpapers():
    """C:\\Windows\\Web\\Wallpaper\\Windows holds the Windows 7 wallpapers, and the account pictures sit under
    ProgramData."""
    walls = DRIVE_C / "Windows" / "Web" / "Wallpaper" / "Windows"
    if not walls.exists():
        walls.mkdir(parents=True)
        for f in BACKGROUNDS.glob("*"):
            if f.is_file():
                shutil.copy2(f, walls / f.name)
    pics = DRIVE_C / "ProgramData" / "Microsoft" / "User Account Pictures" / "Default Pictures"
    if not pics.exists():
        pics.mkdir(parents=True)
        for f in USER_PICTURES.glob("*.png"):
            shutil.copy2(f, pics / f.name)


def _ensure_themes():
    pass


def setup_c():
    """Create the Windows 7 hard drive the first time (and keep adding anything missing)."""
    DRIVE_C.mkdir(parents=True, exist_ok=True)
    pf = DRIVE_C / "Program Files"
    pf86 = DRIVE_C / "Program Files (x86)"
    office = pf86 / "Gemini Office"
    for name in ("GeminiWord.exe", "GeminiExcel.exe", "GeminiPowerPoint.exe", "GeminiOutlook.exe",
                 "GeminiAccess.exe", "GeminiPublisher.exe"):
        if not (office / name).exists():
            _fake(office / name, 200, 900)
    adobe = pf86 / "GeminiAdobe"
    for name in ("GeminiPhoto.exe", "GeminiDraw.exe", "GeminiAcrobat.exe", "GeminiDistiller.exe"):
        if not (adobe / name).exists():
            _fake(adobe / name, 200, 900)
    for extra_exe in (pf86 / "Nero" / "nero.exe", pf86 / "Alcohol Soft" / "Alcohol 120" / "Alcohol.exe",
                      pf / "WinRAR" / "WinRAR.exe", pf86 / "WinZip" / "winzip32.exe",
                      pf / "Internet Explorer" / "iexplore.exe", pf86 / "Windows Live" / "Messenger" / "msnmsgr.exe",
                      pf86 / "Windows Live" / "Mail" / "wlmail.exe", pf86 / "Windows Live" / "Movie Maker" / "MovieMaker.exe",
                      pf86 / "Real" / "RealPlayer" / "realplay.exe", pf / "Kiwix" / "kiwix-desktop.exe",
                      pf / "ClaudeCraft" / "ClaudeCraft.exe", pf / "Claudecadia" / "Claudecadia.exe",
                      pf / "ClaudeQuest" / "ClaudeQuest.exe", pf / "Claudeablo" / "Claudeablo.exe",
                      pf / "ClaudeCity" / "ClaudeCity.exe", pf / "Scorched Claude" / "scorch.exe",
                      pf / "Claudejeweled" / "Claudejeweled.exe", pf / "Claudeggle" / "Claudeggle.exe",
                      pf86 / "QuickTime" / "QuickTimePlayer.exe", pf86 / "Lavasoft" / "Ad-aware" / "Ad-aware.exe",
                      pf / "Windows Sidebar" / "sidebar.exe", pf / "Second Life" / "SecondLife.exe",
                      pf / "Windows Media Player" / "wmplayer.exe", pf / "Windows Mail" / "WinMail.exe"):
        if not extra_exe.exists():
            _fake(extra_exe, 200, 900)
    if (DRIVE_C / MARKER).exists():
        _ensure_wallpapers()
        return
    from .user import profile_name
    home = DRIVE_C / "Users" / profile_name()
    for sub in ("Desktop", "Documents", "Pictures", "Music", "Videos", "Downloads", "Favorites", "Links",
                "Saved Games", "Searches", "Contacts", "AppData/Local/Temp", "AppData/Roaming/Microsoft"):
        (home / sub).mkdir(parents=True, exist_ok=True)
    _fake(home / "Documents" / "Read Me.txt", text=README)
    for sub in ("Documents", "Pictures", "Music", "Videos", "Downloads"):
        (DRIVE_C / "Users" / "Public" / sub).mkdir(parents=True, exist_ok=True)
    (DRIVE_C / "Users" / "Default").mkdir(parents=True, exist_ok=True)
    for rel in ("ClaudeAIM/ClaudeAIM.exe", "ClaudeIRC/ClaudeIRC.exe", "ClaudeMUCK/ClaudeMUCK.exe",
                "ClaudeShield AntiVirus/ClaudeShield.exe", "ClaudeTV/ClaudeTV.exe", "FurComix Reader/FurComix.exe",
                "FurFolio Reader/FurFolio.exe", "FurFolio Reader/FurStory.exe", "Fur CD Viewer/FurCD.exe",
                "Furry Con CD Viewer/FurCon.exe", "Furry Video Browser/FurVideo.exe", "ClaudeAmp/ClaudeAmp.exe",
                "ClaudeTorrent/ClaudeTorrent.exe", "The Fur Directory/FurDir.exe", "ClaudeRPG/ClaudeRPG.exe",
                "FCE Ultra/fceu.exe", "Snes9x/snes9x.exe", "Gambatte/gambatte.exe", "Gambatte/gambatte_gbc.exe",
                "mGBA/mgba.exe", "PicoDrive/picodrive.exe", "Genesis Plus/gpgx.exe", "Gearsystem/gearsystem.exe",
                "AppleWin/applewin.exe", "Mupen64Plus/mupen64plus.exe", "Yahoo!/Messenger/YPager.exe", "ICQ/ICQ.exe",
                "Trillian/trillian.exe", "Skype/Skype.exe", "Kik/kik.exe", "Doom/doom.exe", "Doom II/doom2.exe",
                "Wolfenstein 3D/wolf3d.exe", "Heretic/heretic.exe", "Hexen/hexen.exe",
                "Entertainment Pack/ski.exe", "Entertainment Pack/jezzball.exe", "Entertainment Pack/taipei.exe",
                "Entertainment Pack/rodent.exe", "Entertainment Pack/blockfall.exe", "Entertainment Pack/tripeaks.exe",
                "Entertainment Pack/golf.exe", "Adobe/Flash Player/FlashPlayer.exe", "Microsoft Games/Chess/Chess.exe",
                "Microsoft Games/Solitaire/Solitaire.exe", "Microsoft Games/Minesweeper/MineSweeper.exe"):
        _fake(pf / rel, 200, 900)
    (pf / "Common Files").mkdir(parents=True, exist_ok=True)
    (pf86 / "Common Files").mkdir(parents=True, exist_ok=True)
    win = DRIVE_C / "Windows"
    for name in SYSTEM32:
        _fake(win / "System32" / name)
    for name in FONTS:
        _fake(win / "Fonts" / name, 40, 300)
    media = win / "Media"
    media.mkdir(parents=True, exist_ok=True)
    for wav in SOUNDS.glob("*.wav"):
        shutil.copy2(wav, media / wav.name)
    for name in ("explorer.exe", "regedit.exe", "notepad.exe", "HelpPane.exe", "write.exe"):
        _fake(win / name, 60, 1000)
    _fake(win / "win.ini", text="; for 16-bit app support\n[fonts]\n[extensions]\n[mci extensions]\n[files]\n[Mail]\nMAPI=1\n")
    _fake(win / "system.ini", text="; for 16-bit app support\n[386Enh]\nwoafont=dosapp.fon\n[drivers]\nwave=mmdrv.dll\ntimer=timer.drv\n")
    (win / "Temp").mkdir(exist_ok=True)
    (win / "Resources" / "Themes").mkdir(parents=True, exist_ok=True)
    (DRIVE_C / "PerfLogs").mkdir(exist_ok=True)
    (DRIVE_C / "ProgramData").mkdir(exist_ok=True)
    _fake(DRIVE_C / "bootmgr", 300, 400)
    (DRIVE_C / "Boot").mkdir(exist_ok=True)
    _fake(DRIVE_C / "Boot" / "BCD", 20, 30)
    _ensure_wallpapers()
    (DRIVE_C / MARKER).write_text("Claude7 drive C")


def hidden(path):
    return Path(path).name in (MARKER, "INFO.json", "bootmgr", "BCD", "ProgramData", "Boot", "PerfLogs")


def protected(path):
    path = Path(path).resolve()
    keep = [DRIVE_C, DRIVE_C / "Windows", DRIVE_C / "Program Files", DRIVE_C / "Program Files (x86)",
            DRIVE_C / "Users", user_home(), my_documents(), local_storage()]
    return path in [k.resolve() for k in keep] or (DRIVE_C / "Windows").resolve() in path.parents


# ---- Recycle Bin ---------------------------------------------------------------------------------------------------

def _index():
    try:
        return json.loads(RECYCLE_INDEX.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _save_index(index):
    RECYCLE_DIR.mkdir(parents=True, exist_ok=True)
    RECYCLE_INDEX.write_text(json.dumps(index, indent=2), encoding="utf-8")


def recycle(path):
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
        target = target.with_name(f"{target.stem} - Copy{target.suffix}")
    shutil.move(str(stored), str(target))
    _save_index(index)
    return True


def empty_recycle_bin():
    from . import sound
    if recycled():
        sound.play("recycle")
    for stored, _orig, _when in recycled():
        if stored.is_dir():
            shutil.rmtree(stored, ignore_errors=True)
        else:
            stored.unlink(missing_ok=True)
    _save_index({})
