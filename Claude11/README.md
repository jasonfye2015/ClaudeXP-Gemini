# Claude11 - WORKSTATION-2025

A Windows 11 Home computer from October 2025, the third computer of the Claude Timeline (after EPOCH-2001, the
Windows XP machine in `ClaudeXP/`, and SYSTEM-2011, the Windows 7 machine in `Claude7/`). Start it from the SYSTEC
launcher (`Claude Timeline.bat`) or directly:

```bash
python main.py
```

## What it is

- **Power on:** the ASUS UEFI splash (the user's own picture: the Intel badge, the glowing Windows logo, ASUS), then
  Windows 11's spinning dots under the logo while it boots. DEL or F2 during the splash opens the ASUS UEFI BIOS
  Utility; F8 opens the Windows Recovery Environment (Troubleshoot > Reset this PC reinstalls Windows). NVMe and a
  modern board: no hard drive sounds, no POST beep.
- **The lock screen and sign-in:** the lock picture with the big clock, then your account picture, your name and the
  PIN box over the same picture blurred, with network, accessibility and power in the corner.
- **The desktop:** Windows 11's Bloom (read from the real PC's `C:\Windows\Web`, with a drawn stand-in when there is
  none), rounded Mica windows with Snap and Snap layouts, the centered taskbar (Start, Search, Task View, pinned
  programs with their indicator lines), the Widgets weather button at the left corner, the system tray with Quick
  Settings, the clock with the notification center and calendar, toasts bottom right, Alt+Tab and Task View.
- **The Start menu:** the search box, the Pinned grid with All (the alphabetical list, folders for the groups), the
  Recommended programs, your name and the power button.
- **Settings:** System (About, Display, Sound, Notifications, Power, Recovery), Bluetooth & devices, Network &
  internet, Personalization (background, accent colours, lock screen, themes, taskbar), Apps, Accounts, Time &
  language, Gaming, Accessibility, Privacy & security, Windows Update. The Control Panel is still there too.
- **Windows 11's own programs:** File Explorer's 2025 face over XP's file manager, Microsoft Edge and Firefox 144 on
  XP's web engine, the Widgets board (Weather, Calendar, Outlook, TV Guide, Top stories, Photos, Performance,
  Clock), Sticky Notes, the Snipping Tool, Tips.
- **Every program of the Timeline**, through `claude11/xpcompat.py`: the shared games, archive viewers and apps, and
  the period programs of ClaudeXP that still existed in 2025 - Outlook (Outlook Express's window in 2025 clothes),
  Outlook.com, Telegram, Discord, Trillian, Kik, IRC, the MUCK, Second Life, LiveJournal, Facebook and Bluesky on the
  Furry Web (`sites/facebook.py`, `sites/bluesky.py`: the residents' diaries as posts),
  Media Player, Clipchamp, the Ruffle Flash player. The services that closed are gone: AIM (2017), MSN Messenger
  (2013), Yahoo! Messenger (2018), ICQ (2024), Skype (May 2025).

## Layout

| Where | What |
|---|---|
| `main.py`, `claude11/launch.py`, `claude11/app.py` | Start-up (crash log, the compatibility layer, the residents' sync, Qt), the main window and the flow from power on to shut down |
| `claude11/bios.py`, `boot.py` | The ASUS UEFI splash and setup utility, the recovery environment, the boot spinner, the black Shutting down / Restarting / Signing out screens, the powered-off PC |
| `claude11/logon.py` | The lock screen and sign-in |
| `claude11/desktop.py`, `icons.py`, `taskbar.py`, `startmenu.py`, `wm.py` | The desktop, its icons, the centered taskbar and its flyouts (Quick Settings, the notification center, hidden icons, thumbnails), the Start menu, Mica windows with Snap layouts |
| `claude11/tray.py`, `network.py`, `volume.py`, `display.py` | Toasts and tray icons, the always-on Wi-Fi, the volume mixer, Personalization data (the real PC's wallpapers and lock screen pictures, accent colours) |
| `claude11/settings.py`, `controlpanel.py` | The Settings app; the classic Control Panel and its dialogs |
| `claude11/explorer11.py` | File Explorer's 2025 face over XP's file manager |
| `claude11/programs/` | The registry for 2025 (`__init__.py`), Edge and Firefox (`browsers.py`), the Widgets board (`widgets.py`), Sticky Notes, the Snipping Tool, Tips (`helpctr.py`) |
| `claude11/web2025.py`, `xpfaces.py`, `sites/` | MSN and Outlook.com in 2025, the small 2025 faces on XP pieces (Outlook, the AI loading box, LiveJournal), Facebook (2025 look) and Bluesky on the Furry Web |
| `claude11/xpcompat.py`, `shims.py`, `host11.py` | ClaudeXP's modules swapped for Claude11's under the XP names, the import hook that redirects Program Files and swaps 2001 for 2025, the stand-ins (no Clippy, no visual styles), the host every shared program talks to |
| `claude11/setup/` | Windows Setup from the USB drive, the out-of-box experience, the speech check |
| `claude11/screensaver.py`, `alttab.py` | Bubbles, Ribbons and friends; Alt+Tab and Task View |
| `assets/` | The ASUS splash (`images/boot/asus_splash.png`), icons; drop pictures into `backgrounds/`, lock pictures into `images/lock/` and sounds into `sounds/` to override the collection's and the real PC's |
| `data/`, `Program Files/`, `logs/` | This computer's own data, the period programs' data, crash logs (all gitignored) |

## Notes

- Wallpapers, lock screen pictures and sounds come, in this order, from `assets/backgrounds` and `assets/sounds`,
  from the user's collection in `Local Storage/Windows 11 Media/Wallpapers` and `/sounds` (59 wallpapers, the Windows
  11 sound scheme and the real startup chime as an m4a), and from the real Windows installation (`C:\Windows\Web`,
  `C:\Windows\Media`). Nothing of Microsoft's is copied into the project; the 8K pictures are scaled down as they
  load, and only the lighter ones are copied onto the virtual drive C:.
- Clear `data/` (or use the launcher's Load and Format) to go through the out-of-box experience again.
- The residents' 2025 lives are in `Residents/<Name>/eras/2025.json` (drafted by
  `ClaudeCore/tools/draft_2025_eras.py`; the 34 main residents' by hand). Discord and Telegram are ClaudeXP's own
  modern faces; Facebook wears its 2025 look and Bluesky is new. Still to come: the 2025 TV channels.
