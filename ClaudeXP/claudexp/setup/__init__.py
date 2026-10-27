"""System Recovery: reinstalling Windows XP from the recovery CD.

Press SPACE during the BIOS self test for the recovery menu. Text-mode Setup formats C: (or leaves it
intact), copies files and reboots; GUI Setup and the Welcome to Microsoft Windows (OOBE) pages run on
the next boot.

The reboot is a real restart of the ClaudeXP process, so nothing still in memory (a buddy's open chat,
the living world) can write its old state back after the wipe. The wipe itself happens in main.py after
the old event loop has stopped.

Nothing is really deleted: everything Setup "erases" is moved to ClaudeXP/Recovery Backups/<date time>/,
outside the virtual PC, so a reset can always be undone by hand.
"""
import json
import os
import shutil
from datetime import datetime

from ..paths import DATA, ROOT

STATE_FILE = DATA / "setup.json"
BACKUPS = ROOT / "Recovery Backups"
RESTART = 3                    # exit code: main.py starts ClaudeXP again (Setup's reboot)
PROGRAM_DATA = [ROOT / "Program Files" / name / "data" for name in ("ClaudeAIM", "ClaudeIRC", "ClaudeMUCK", "Netscape")]
WORLD = ["journals", "mail.json", "life.json"]                # the buddies' lives and memories (in data/)
CHATS = ["messengers", "livejournal.json"]                     # chats with them (cleared with a new persona style)
PROGRAM_HISTORY = ["claudeai"]                                 # in data/, plus PROGRAM_DATA
FILES_ON_C = ["Drive C", "Recycle Bin"]
# 'Leave the current file system intact' still puts Windows' own settings back to their defaults:
WINDOWS_SETTINGS = ["user.json", "display.json", "desktop.json", "network.json", "updates.json",
                    "antivirus.json", "games.json", "run.json", "credits.json", "clippy.json", "deskmario.json"]

# Speeds Setup up for scripted tests (CLAUDEXP_SETUP_SPEED=20 runs it 20x faster).
SPEED = max(0.01, float(os.environ.get("CLAUDEXP_SETUP_SPEED", "1") or 1))

_pending_wipe = None


def ms(milliseconds):
    return max(1, int(milliseconds / SPEED))


# ---- where Setup is up to -------------------------------------------------------------------------------

def stage():
    """None normally; 'gui' or 'oobe' while a reinstall is still finishing."""
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


# ---- the reboot in the middle of Setup ---------------------------------------------------------------------

def reboot_into_gui_setup(app, format_drive, program_history, memories):
    """End of text-mode Setup: remember what to erase, then quit the event loop with RESTART.
    main.py calls finish_reboot() once Qt has stopped, then starts ClaudeXP again."""
    global _pending_wipe
    _pending_wipe = {"format": format_drive, "programs": program_history, "memories": memories}
    app.exit(RESTART)


_after_stop = []


def reboot(app, action=None):
    """Restart ClaudeXP for real; action() runs once nothing is running any more (System Restore uses this
    to put old settings back without a program saving over them)."""
    if action is not None:
        _after_stop.append(action)
    app.exit(RESTART)


def finish_reboot():
    """Called by main.py after the event loop stops: run pending actions, do the pending wipe (and mark GUI
    Setup next)."""
    from .. import llm_server
    llm_server.stop()                              # the language model engine keeps files open in data/
    while _after_stop:
        _after_stop.pop(0)()
    if _pending_wipe is None:
        return
    w = _pending_wipe
    from .. import persona_style
    before = persona_style.installed()
    style = persona_style.requested() or before   # (the launcher's Load and Format may choose another)
    changed = style != before
    try:
        # a new Contact Persona Style starts the residents afresh: their memories and chats go with the old one
        wipe(format_drive=w["format"], program_history=w["programs"] or changed, memories=w["memories"] or changed,
             extra=CHATS if changed else ())
    finally:
        persona_style.set_installed(style)          # (after the wipe, which moves data/ away)
        persona_style.consume_request()
        set_stage("gui", formatted=w["format"])   # Setup carries on even if something couldn't be moved


def wipe(format_drive=True, program_history=True, memories=True, extra=()):
    """Move the chosen data into Recovery Backups/<now>/ (kept outside the virtual PC)."""
    targets = [DATA / name for name in extra]
    if format_drive:
        # Formatting erases all of C:, except what the user chose to keep.
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
            pass                                   # in use: keep going, so the rest is still erased
    DATA.mkdir(parents=True, exist_ok=True)
    return backup
