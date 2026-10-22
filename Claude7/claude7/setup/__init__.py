"""Reinstalling Windows 7 from the installation DVD.

Press F8 during the self test for Advanced Boot Options > Repair Your Computer, or boot from the DVD after a format
request from the launcher. Setup formats C: (or leaves it intact), copies files and restarts; 'Set Up Windows'
(the account, computer name, password, time zone) runs on the next boot.

The restart is a real restart of the Claude7 process, so nothing still in memory (a buddy's open chat, the living
world) can write its old state back after the wipe. The wipe itself happens in main.py once the event loop has
stopped. Nothing is really deleted: everything Setup "erases" is moved to Claude7/Recovery Backups/<date time>/.

This module stands in for claudexp.setup too (the XP programs' System Restore and Task Manager restart through it).
"""
import json
import os
import shutil
from datetime import datetime

from ..paths import DATA, PROGRAM_FILES, ROOT

STATE_FILE = DATA / "setup.json"
BACKUPS = ROOT / "Recovery Backups"
RESTART = 3                    # exit code: main.py starts Claude7 again (Setup's restart)
PROGRAM_DATA = [PROGRAM_FILES / name / "data" for name in ("ClaudeAIM", "ClaudeIRC", "ClaudeMUCK", "Netscape")]
WORLD = ["journals", "mail.json", "life.json"]                 # the residents' lives and memories (in data/)
CHATS = ["messengers", "livejournal.json"]
PROGRAM_HISTORY = ["claudeai"]                                 # in data/, plus PROGRAM_DATA
FILES_ON_C = ["Drive C", "Recycle Bin"]
WINDOWS_SETTINGS = ["user.json", "display.json", "desktop.json", "network.json", "updates.json", "antivirus.json",
                    "games.json", "run.json", "credits.json", "taskbar.json", "tray.json", "volume.json", "cpl.json",
                    "gadgets.json", "stickynotes.json", "speech_license.json", "msconfig.json"]

SPEED = max(0.01, float(os.environ.get("CLAUDE7_SETUP_SPEED") or os.environ.get("CLAUDEXP_SETUP_SPEED") or 1))
_pending_wipe = None
_after_stop = []


def ms(milliseconds):
    return max(1, int(milliseconds / SPEED))


# ---- where Setup is up to -------------------------------------------------------------------------------------
def stage():
    """None normally; 'oobe' while a reinstall is still finishing (Set Up Windows comes after the restart)."""
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f).get("stage")
    except (OSError, ValueError):
        return None


def info():
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def set_stage(name, **extra):
    data = info()
    data.update(extra, stage=name)
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def finished():
    try:
        STATE_FILE.unlink()
    except OSError:
        pass


# ---- the restart in the middle of Setup ------------------------------------------------------------------------
def reboot_into_oobe(app, format_drive, program_history, memories):
    """End of the copying phase: remember what to erase, then quit the event loop with RESTART. main.py calls
    finish_reboot() once Qt has stopped, then starts Claude7 again."""
    global _pending_wipe
    _pending_wipe = {"format": format_drive, "programs": program_history, "memories": memories}
    app.exit(RESTART)


reboot_into_gui_setup = reboot_into_oobe      # (ClaudeXP's name for it)


def reboot(app, action=None):
    """Restart Claude7 for real; action() runs once nothing is running any more."""
    if action is not None:
        _after_stop.append(action)
    app.exit(RESTART)


def finish_reboot():
    """Called by main.py after the event loop stops: pending actions, then the pending wipe."""
    try:
        from claudexp import llm_server
        llm_server.stop()                              # the language model engine keeps files open in data/
    except Exception:
        pass
    while _after_stop:
        _after_stop.pop(0)()
    if _pending_wipe is None:
        return
    w = _pending_wipe
    try:
        wipe(format_drive=w["format"], program_history=w["programs"], memories=w["memories"])
    finally:
        set_stage("oobe", formatted=w["format"])


def wipe(format_drive=True, program_history=True, memories=True, extra=()):
    """Move the chosen data into Recovery Backups/<now>/ (kept outside the virtual PC)."""
    targets = [DATA / name for name in extra]
    if format_drive:
        keep = set()
        if not program_history:
            keep.update(PROGRAM_HISTORY)
        if not memories:
            keep.update(WORLD)
        if DATA.exists():
            targets += [p for p in DATA.iterdir() if p.name not in keep]
    else:
        targets += [DATA / name for name in WINDOWS_SETTINGS]
        if program_history:
            targets += [DATA / name for name in PROGRAM_HISTORY]
        if memories:
            targets += [DATA / name for name in WORLD]
    if program_history:
        targets += PROGRAM_DATA
    targets = [p for p in targets if p.exists()]
    if not targets:
        return None
    backup = BACKUPS / datetime.now().strftime("%Y-%m-%d %H%M%S")
    for path in targets:
        dest = backup / path.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.move(str(path), str(dest))
        except OSError:
            pass
    DATA.mkdir(parents=True, exist_ok=True)
    return backup
