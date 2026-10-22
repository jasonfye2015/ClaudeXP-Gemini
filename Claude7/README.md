# Claude7 - SYSTEM-2011

A Windows 7 Home Premium computer from October 2011, the middle of the Claude Timeline (EPOCH-2001 is ClaudeXP,
WORKSTATION-2025 is Claude11). The same residents live here, ten years older than on the XP machine; the same games,
archive viewers and apps run here in Aero glass; the archive on drive E: (Local Storage) is the same drive.

Run it from the SYSTEC launcher (`Claude Timeline.bat` > SYSTEM-2011 > Load This Computer) or directly:

    cd Claude7
    ..\ClaudeXP\.venv\Scripts\python.exe main.py

F11 toggles full screen (Alt+Tab then switches Claude7's windows). Ctrl+Alt+End opens Task Manager. DEL during the
self test opens the BIOS Setup Utility; F8 opens Advanced Boot Options (Repair Your Computer > Reinstall Windows).

## How it's built

ClaudeXP's period programs (AIM, the messengers, IRC, the MUCK, Internet Explorer, Hotmail, the Furry Web, the
Office suite, Explorer, the Control Panel applets, Windows Update, the antivirus, the games...) are not copied: they
run from `ClaudeXP/` inside Claude7 through the compatibility layer, `claude7/xpcompat.py`:

- `claudexp.paths.DATA` points at `Claude7/data` before any XP module loads, so everything the programs save lands on
  this computer.
- The modules that *are* Windows are Claude7's own, aliased into `sys.modules` under the XP names: `claudexp.wm` is
  `claude7.wm` (so `XPWindow` is an `AeroWindow`), and likewise sound, clock, user, network, tray, display, volume,
  the visual-style shims, the dialogs, the drive (vfs), Setup, the Control Panel and the desktop icons.
- The Program Files constants (where the IRC and MUCK regulars, the Fur Directory cards and the browsers' data live)
  are redirected to `Claude7/Program Files` as each module loads, and "2001" becomes "2011" in the prompts.
- ClaudeAIM (XP's program) reads `Claude7/Program Files/ClaudeAIM` for its contacts and chats, in 2011.

`claude7/programs/__init__.py` builds the registry from ClaudeXP's, drops the 2001-only programs (Netscape, Windows
Messenger, activation, the tour, StyleXP, Clippy, dial-up), renames the Windows Live ones, adds the Windows 7
accessories (Sticky Notes, Snipping Tool, Desktop Gadget Gallery, Help and Support) and installs itself back into
`claudexp.programs`, so every program that asks the registry sees Claude7's.

## Claude7's own pieces

| Module | What |
| --- | --- |
| `bios.py` | AMI self test (Core i5-2500K, 8 GB, SATA), BIOS Setup Utility, Advanced Boot Options |
| `boot.py` | Starting Windows (the 105-frame animation), Shutting down / Logging off, the powered-off PC |
| `logon.py` | The logon screen on the seed's template: user tile, password, Switch User, power menu, Lock |
| `desktop.py`, `icons.py`, `taskbar.py`, `startmenu.py`, `wm.py` | The Aero desktop: Snap, Peek (rest on the Show desktop sliver), thumbnails, the orb, pinned programs, the Start menu with search |
| `tray.py`, `network.py`, `volume.py`, `display.py` | Notifications, the always-on Wi-Fi, the Volume Mixer, Personalization data |
| `controlpanel.py` | Control Panel (categories and icons), Personalization, User Accounts, Default Programs |
| `programs/` | Sticky Notes, Snipping Tool, gadgets (clock, calendar, CPU meter, weather, slide show, feed headlines, e-mail inbox, TV guide), Chess Titans, Help and Support |
| `screensaver.py`, `alttab.py` | Bubbles, Ribbons and friends; Alt+Tab with thumbnails |
| `explorer7.py` | Windows Explorer's 2011 face (navigation pane, breadcrumb, command bar, details pane) over XP's file manager |
| `programs/browsers.py`, `web2011.py` | Internet Explorer 9 and Mozilla Firefox 7 on XP's web engine; MSN.com, Hotmail and the pages' years in 2011 |
| `sites/facebook.py` | Facebook, autumn 2011, on the Furry Web: the residents' diaries as a News Feed, profiles, photos, friends, your wall |
| `programs/wlm.py`, `xpfaces.py` | Windows Live Messenger 2011, Windows Live Mail, Skype 5, Yahoo! Messenger 11, ICQ 7, Trillian 5 faces; the AI loading box in Aero |
| `setup/` | Install Windows from the DVD, Set Up Windows (prefilled from the Timeline's Profile), the speech check |
| `residents_sync.py` | The residents in 2011 (from `Residents/<Name>/eras/2011.json`) into Program Files |

## Folders

    assets/           Windows 7's artwork and sounds (the seed's, curated)
    claude7/          the code
    data/             everything that changes: the account, drive C:, journals, mail, settings (gitignored)
    Program Files/    the period programs' data on this computer, regenerated from Residents/ (gitignored)
    logs/             crash.log (gitignored)
    Recovery Backups/ what a reinstall moved aside (gitignored)
    seed/             the earlier Windows 7 simulator this was built from (reference only)
