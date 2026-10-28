# 13. Under the hood

For whoever changes the Timeline next, probably you with a Claude Code session open in the folder. The design notes
it was built from are in `PLAN.md`; each computer has a `README.md` of its own; the shared folders have `README.txt`
files. This is the map.

## One registry, three computers

Every program is registered once, in ClaudeXP's registry, `ClaudeXP\claudexp\programs\__init__.py`:

```python
Program("furcoder", "FurCoder", "Encode and decode Furry Codes and YIFF Codes",
        _shared("furcoder", "furcoder_icon"), _shared("furcoder", "launch"), group=FURRY)
```

A `Program` has a key (used everywhere: shortcuts, settings, the self-check), a name (which must be a valid Windows
file name, because each one becomes a `.lnk`), a blurb, an icon getter and a launcher, an optional shutdown hook, a
`group` (its All Programs submenu: `"Games"`, `"Accessories/System Tools"`, or `""` for the top level) and `listed`.
`_shared(module, func)` imports a program from the shared folders (`ClaudeGames`, `ClaudeArchive`, `ClaudeApps`,
which `claudexp/__init__.py` puts on `sys.path`) the first time it's used; `_lazy` does the same for XP's own
modules.

Claude7 and Claude11 build their registries from XP's: `claude7\programs\__init__.py` drops the 2001-only programs
(`DROPPED`), renames the ones that changed (`RENAMED`: MSN Messenger becomes Windows Live Messenger, Internet Explorer
becomes Microsoft Edge in 2025), regroups some (`REGROUPED`), adds its own (Sticky Notes, the Snipping Tool, Chess
Titans), and installs the result back into `claudexp.programs` so everything that asks the registry sees that era's.

**So: register a program in XP's registry and it is on all three computers**, in each one's own window style, unless
an era drops or renames it.

## How a shared program talks to the computer it's on

Never by importing an OS's modules. Always through the host, `ClaudeCore\claudecore\host.py`:

```python
from claudecore import host
win = host.window(desktop, "Claudeggle", body, icon, (990, 676))   # a window in this OS's style
host.sound("ding")                       # this OS's sound for an event
host.saves("claudeggle")                 # ClaudeGames\Saves\claudeggle, shared by every era
host.data("claudeai")                    # this computer's own data folder for that program
host.local_storage()                     # the shared Local Storage
host.era()                               # 2001, 2011 or 2025
host.message(desktop, title, text, "info", buttons, on_button)
host.open_media(desktop, path), host.open_flash(desktop, path)
```

Each OS registers its host at start-up (`claudexp\xphost.py`, `claude7\host7.py`, `claude11\host11.py`). The window
the host returns is that OS's own window class with `.content` and `request_close()`.

## How Claude7 and Claude11 run XP's programs

Through a compatibility layer, `claude7\xpcompat.py` (and Claude11's): before any XP module loads, `claudexp.paths.DATA`
is pointed at that computer's `data`, the modules that *are* Windows (`wm`, `sound`, `clock`, `user`, `network`,
`tray`, `display`, `volume`, the dialogs, the drive, Setup, the Control Panel, the desktop icons) are aliased in
`sys.modules` to the newer computer's own, the Program Files constants are redirected to that computer's
`Program Files`, and "2001" becomes "2011" or "2025" in the prompts. An XP program that asks for an `XPWindow` gets an
`AeroWindow` or a `MicaWindow` without knowing.

## Desktops and shortcuts

A shortcut is a tiny text file:

```
[ClaudeXP Shortcut]
Program=comix
```

Explorer and the desktop show it without the `.lnk`, with the program's own icon. `explorer\shortcuts.py` makes
them, with `safe_name()` turning forbidden characters into dashes.

- **XP:** `desktop_icons.py` has the built-in desktop icons (`builtins()`, bump `LAYOUT` when their order changes),
  the program folders (`PROGRAM_FOLDERS`: which groups go in Games, Furry Programs, Social Programs...), and
  `FOLDERS` / `FOLDERS_SINCE`, a version number per folder: raising it adds the shortcuts an existing desktop is
  missing, never removes any (a shortcut you deleted stays deleted).
- **7 and 11:** `icons.py` has `DESKTOP_SHORTCUTS` (the loose icons on a fresh desktop) and `PROGRAM_FOLDERS`;
  `ensure_program_folders()` links any program never linked before.

## Adding a game

1. A package in `ClaudeGames\<name>\` with an icon function and a `launch(desktop)` that opens one window through the
   host (copy a small one such as `claudeanoid`). Art in its `assets\`. Saves through `host.saves(name)`.
2. One `Program(...)` line in XP's registry with `group="Games"`. That puts it in Start > Games and the desktop Games
   folder on all three computers (`FOLDERS` goes up one so existing desktops get the shortcut).
3. Real-time games use the shared precise timer with catch-up, or they run in slow motion.
4. Run the self-check (it parses the registry for bad names) and the offscreen smoke test.

## Testing without a screen

```
set QT_QPA_PLATFORM=offscreen
set QT_QPA_FONTDIR=C:\Windows\Fonts
```

With those, a computer or a program can be imported and driven from a script with no window. Claude7 and Claude11
were tested that way (every program launched offscreen). **Never run tests against the real `data` folders** of the
computers, and never against `ClaudeApps\kithylinai\Data`: Kithylin AI honours a `KITHYLINAI_DATA` environment
variable for a scratch folder.

## Background threads

A `QThread` that's thrown away while it's still running doesn't raise an error: it ends the whole computer on the
spot, leaving only `QThread: Destroyed while thread '' is still running` in `logs\crash.log`. That's easy to do by
accident - a window closed mid-reply, a stop that waits a few seconds and then lets go, a "done" signal handled before
the thread has really returned. So threads that talk to a model are kept alive until they've finished, whoever lets
go of them first: `kithylinai.engine._Kept` (Kithylin AI and Soul and Song) and `pystudio.threads.Kept` (both code
studios). Build a new one on those, or on `QThreadPool` and `QRunnable`, which can't be dropped that way.

## The runtimes and the launcher

- **`Python\`** is a portable CPython 3.14 for Windows with every package the Timeline needs; the launcher sets
  `PYTHONNOUSERSITE=1` so the PC's own packages never leak in. On the development PC, ClaudeXP's `.venv` is used when
  its base Python is still installed. **`Python-mac\`** is the Apple silicon twin ([On a Mac](12-mac.md)).
- **`Claude Timeline.exe`** is a tiny C# program (`ClaudeLauncher\exe\ClaudeTimeline.cs`) that runs
  `ClaudeLauncher\main.py` on the portable Python without a console. `build.bat` rebuilds it with the C# compiler
  every Windows has; `make_icon.py` draws the icon.
- **The launcher** (`ClaudeLauncher\systec`) starts a computer as a separate process with `CLAUDE_TIMELINE=1` in its
  environment (and `CLAUDE_TIMELINE_FORMAT=1` for a format), minimises itself, and watches for the process to end.

## Git

One repository at the top. Ignored, on purpose: `Local Storage` (except its README), the Pythons, `Profile`, the
launcher's settings, every `data` and `Program Files` folder, `ClaudeGames\Saves`, Kithylin AI's `Art`, `Models` and
`Data`, the Windows 7 seed library, and macOS droppings. `ClaudeXP\Features to add.txt` is a personal list and is not
committed. Commits are made and pushed when you ask for them.

## Where things are, quickly

| I want to change... | Look in |
|---|---|
| A program's name, group or icon | `ClaudeXP\claudexp\programs\__init__.py`, then `RENAMED` / `REGROUPED` in Claude7 and Claude11 |
| Which desktop icons a fresh computer has | `desktop_icons.py` (XP), `icons.py` (7, 11) |
| A resident | `Residents\<Name>\resident.json` and `eras\<year>.json` |
| How the residents are prompted | `ClaudeXP\claudexp\persona_style.py` and the residents' loaders; freeze a version into `Persona Styles\` |
| The launcher's cards, specs, buttons | `ClaudeLauncher\systec\systems.py`, `ui.py` |
| The backup parts | `PARTS` in `ClaudeCore\claudecore\backup.py` |
| What the self-check checks | `ClaudeCore\claudecore\selfcheck.py` |
| Which model does which job by default | `ClaudeCore\claudecore\ai\ai_models.py` |
| Kithylin AI | `ClaudeApps\kithylinai` (`defaults.py` has the default prompts) |
| Training | `ClaudeApps\selfmodel` |
| ClaudeTV's channels and schedule | `ClaudeArchive\claudetv\lineup.py`, `schedule.py` |
| This manual | `Manual\*.md`; the viewer is `ClaudeApps\manual` |
