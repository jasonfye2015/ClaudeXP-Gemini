# ClaudeXP plan

A virtual Windows XP desktop (one PySide6 window) that will host ClaudeAIM, ClaudeIRC,
ClaudeMUCK and NetscapeNavigator. ClaudeAIM (../ClaudeAIM) stays standalone; code gets
copied over here when AIM moves in.

Run: `ClaudeXP.bat`, or `main.py` with `.venv` in Thonny. F11 = fullscreen, click/key skips boot.

## Done
- Boot screen (winXP_boot.jpg + sliding windowsxp_progress.jpg)
- Desktop: wallpaper, icons (My Computer, Notepad, Recycle Bin)
- Window manager (`claudexp/wm.py`): Luna title bars, drag, resize, min/max/close, focus
- Taskbar: Start button, window buttons, clock tray
- Start menu over startmenu.jpg: pinned/recent programs, All Programs, Log Off, Turn Off
- Notepad; placeholder windows for unbuilt things
- XP sounds (`claudexp/sound.py`, `sound.play("startup")` etc.): startup, shutdown screen,
  navigate click, menu command, error; tray speaker toggles mute
- Welcome screen (`claudexp/welcome.py`): boot -> Welcome -> desktop; Log Off returns here.
  `assets/images/xp_logo.png` was cut out of winXP_boot.jpg. User name/picture live in `claudexp/user.py`
- It's always 2001: `claudexp/clock.py` gives real local month/day/time with year 2001.
  The tray shows time + date (full date tooltip). Programs should use it for timestamps.
- Programs are registered in `claudexp/programs/__init__.py`
- **ClaudeAIM is installed** in `Program Files/ClaudeAIM/` (a copy of ../ClaudeAIM's code, assets,
  contacts and data, taken 2026-10-07; the two now evolve separately). Launched by
  `claudexp/programs/aim.py`. How hosting works:
  - `claudexp/hosting.py` AppHost: adopts the program's top-level windows into XP frames on first
    show, gives it XP tray icons (`claudexp/tray.py`, incl. balloons), flashing taskbar buttons.
  - AIM side: `claudeaim/host.py`. Windows inherit `host.HostedWindow`; window-manager calls go
    through `host.present / available_geometry / is_active / alert / information / warning`.
    Without a host installed it falls back to normal Qt windows.
  - AIM timestamps use year 2001; the XP mute button mutes AIM; Log Off / Turn Off close AIM.
  - App-wide classic grey look is in `claudexp/style.py` (matches AIM's retro style).
- Dial-up (`claudexp/network.py`): "Connect America Online" dialog (AOL banner), modem.mp3 with
  Dialing / Verifying / Registering stages, two-monitors tray icon (blinks, tooltip, Status window,
  Disconnect). Saved in data/network.json. Programs call `network.connect(desktop, then=...)`;
  AIM requires it (and skips its own dial-up when hosted); hanging up signs AIM off.
- **ClaudeMUCK** (`claudexp/programs/muck/`): MUSHclient-style client (client.py) talking to a
  simulated PawPrints MUCK (world.py; prompts in brain.py, reusing ClaudeAIM's Ollama helper and
  model settings). Map and MUCK-only regulars are editable JSON in `Program Files/ClaudeMUCK/world/`
  (rooms have 'popularity'). AIM buddies join too; an optional "muck" section in their AIM contact
  JSON sets name/species/desc/haunts/doing. Player + generated descriptions saved in
  `Program Files/ClaudeMUCK/data/` (gitignored). Needs the dial-up. Presence on the MUCK is
  separate from AIM presence for now (same schedules, independent sessions).
- **ClaudeIRC** (`claudexp/programs/irc/`): mIRC 6-style client (client.py: switchbar, Status /
  channel / query panes, nick list, Options dialog) for the simulated FurNet network (furnet.py:
  server welcome + MOTD, channels with topics, joins/parts/quits, lurkers, FurBot !commands,
  'asl?' guests getting kicked, /whois /list /msg /me /nick /away /ctcp ...). Network, channels and
  IRC-only regulars in `Program Files/ClaudeIRC/` (network.json, regulars.json); AIM buddies join
  (optional "irc" section in their contact file). Settings + private-message history in
  `Program Files/ClaudeIRC/data/` (gitignored).
- **Netscape Navigator** (`claudexp/programs/navigator/`): Netscape 4-style browser (browser.py).
  The model writes each page as 2001 HTML 3.2, streamed in like a dial-up download (web.py:
  prompts, PageLoader thread, cache in `Program Files/Netscape/data/cache`, built-in /img/*
  images drawn by Qt, static Netcenter home page). Buddies (and MUCK/IRC regulars) get personal
  homepages on any URL containing their name (e.g. www.furrycities.com/ArcticFox/); site facts in
  `Program Files/Netscape/sites.json` keep FurNet/PawPrints pages consistent. Plain words in
  Location = search. View > Regenerate Page re-rolls a cached page. ~15 tok/s: a page takes ~1 min.
  Real Netscape art in assets/images: netscape_icon.jpg (program icon), netscape_throbber.gif
  (34-frame meteor throbber), netscape_splash.jpg (launch splash), netscape_about.jpg (about: page).
- **Model broker** (`claudexp/broker.py`): every Ollama request from every program goes through one
  queue on one worker, by priority: FOREGROUND 10 > AIM 8 > REPLY 5 > CHATTER 0 > BACKGROUND -10.
  AIM's llm.LLM delegates to it (llm.install_broker), Netscape streams through it. Tracks the
  background 'batch' for maintenance progress. **HDD light** (`claudexp/hdd.py`) in the tray
  flickers while it works.
- **Maintenance** (`claudexp/maintenance/`): Automatic Updates (tray download, 'Updates are ready',
  install, Restart Now), Disk Defragmenter, ClaudeShield AntiVirus 2002 (tray, scans, LiveUpdate,
  quarantine, rare 2001 worms). CoverClock: a task never finishes while background model work is
  queued. The coordinator starts a task when a background batch of 3+ jobs begins (40 min cooldown;
  defrag only when the user is idle 3+ min).
- **Living world** (`claudexp/life/`): per-buddy journals in data/journals (life notes + summaries
  of conversations from AIM/IRC/MUCK/email) injected into every program's prompts, so buddies
  remember across programs; story ticks every 45-90 min; buddies reach out (AIM IM > IRC query >
  email); Netscape WebMail inbox + 'You've got mail!'; buddy homepages show and auto-refresh with
  life news; catch-up after the PC was off (queued at login, hidden behind maintenance).
- **My Computer / Windows Explorer** (`claudexp/explorer/`): B: floppy ('device is not ready'),
  C: the XP disk (real folder `data/Drive C`, built on first open: Documents and Settings, Program
  Files with .exe files that launch the ClaudeXP programs, WINDOWS with system32/Fonts/Media),
  D: CD drive ('Please insert a disk'), E: External Drive = the real `Local Stoage` folder (or
  `Local Storage`). Task pane, Address bar, Icons/List/Details, XP sizes/types/2001 dates, new folder,
  rename, cut/copy/paste, drag-in copies from real Windows, delete -> Recycle Bin (`data/Recycle Bin`,
  restorable), drive Properties pie chart. Files open in Notepad (now with Save/Save As), the Picture
  and Fax Viewer, a mini Media Player, or Netscape (local .htm).
  Drive sounds (assets/sounds): harddrive_startup*.mp3 at boot, floppydrive_reading*.mp3 when
  opening B:, cdrom_startup*.mp3 when opening D: (sound.play_clip plays the first few seconds),
  externalHD_start*.mp3 when E: is opened after 10+ minutes idle (it 'spins up' first).
- **ClaudeAI** (`claudexp/programs/claudeai/`): Claude Desktop-style chat with the local model.
  Collapsible sidebar (Ctrl+B): New chat (Ctrl+Shift+O), search, Starred + Recents, per-chat menu
  (Star, Rename, Delete). Streaming Markdown replies via the broker (FOREGROUND), Stop, Copy, Retry,
  Extended thinking (broker.stream on_thinking -> collapsible 'Thought process'), model picker,
  auto titles, Settings (default model, temperature, custom instructions). Saved in data/claudeai.
- **Power** (`claudexp/power.py`): power-on runs an AMIBIOS POST (ami_bios_logo.png, memory test,
  POST beep post_beep1/2.wav (generated square waves), floppy seek, drive detection matching My
  Computer, hard drive spin-up sound) before the XP boot screen. Turn Off Computer -> shutdown sound
  -> 'It's now safe to turn off your computer' (safe_shutdown.jpg) with Turn off (quit) / Restart
  computer (back to BIOS). The PC stays 'on' there: life.powered_off keeps story ticks running
  (news arrives as email). Closing the real window still exits (shutdown sound, then quit).
- **Personalizing**: `claudexp/user.py` (data/user.json: account name, default 'Desktop'; picture,
  default Snowflake from assets/user_icons, or the user's own assets/images/userpic.*; the profile
  folder keeps its original name, like XP) and `claudexp/display.py` (data/display.json: wallpaper
  from assets/backgrounds, default the 1024x768 Bliss; Center/Tile/Stretch; color).
  `claudexp/controlpanel.py`: Control Panel, Display Properties (Desktop tab with monitor preview,
  Browse finds pictures in My Pictures/E:), User Accounts (change name / picture). Desktop right-click
  -> Properties; Start menu picture -> pick a picture; Explorer 'Set as Desktop Background'.
- **Screen savers** (`claudexp/screensaver.py`): Windows XP, Starfield, Mystify, Beziers, 3D Pipes,
  Marquee, My Pictures Slideshow, Blank. ScreenSaverManager (on the main window) starts the chosen
  saver after N idle minutes on the desktop or Welcome screen (default Windows XP, 10 min); mouse/key
  wakes it; 'On resume, display Welcome screen' locks to Welcome (app.lock) with programs left open.
  Display Properties' Screen Saver tab has a live preview, Settings (Marquee text), Preview, Wait.
- **Desktop icons** (`claudexp/desktop_icons.py`, IconManager on the desktop): built-in icons plus
  everything in the real Desktop folder (C:\Documents and Settings\<profile>\Desktop, watched for
  changes). Drag (multi-select), rubber band, Ctrl-click, snap to an 80x78 grid; Arrange Icons By
  Name/Size/Type/Modified, Auto Arrange, Align to Grid, Show Desktop Icons; Refresh (F5); New
  Folder/Text Document; Paste; rename in place (F2); Delete -> Recycle Bin (shortcuts are hidden instead;
  Display Properties > Customize Desktop brings them back); drop onto Recycle Bin or a folder; files
  dragged in from Windows are copied. Saved in data/desktop.json.
- **Printing** (`claudexp/printing.py`): one printer, 'Epson LQ-570+ (Dot Matrix)', that prints to PDF in
  E:\Printed (the Local Storage folder). Text prints dot-matrix style (green-bar paper, tractor holes,
  80 columns); web pages/chats/pictures print as normal pages. XP Print dialog (copies), a spooler with
  a tray printer icon, printer_sound1/2.mp3 (longer for more pages), a 'Document Printed' balloon, and a
  print queue window. Print from Notepad (Ctrl+P), Netscape, the Picture Viewer, ClaudeAI (Ctrl+P) and
  Explorer's right-click Print; Printers and Faxes in the Start menu and Control Panel.
- **Games** (`claudexp/games/`, Start > All Programs > Games): cards are drawn in code (`cards.py`, 71x96,
  blue crosshatch back; real XP card images could replace face_pixmap/back_pixmap) with a shared
  drag-and-drop CardTable. Solitaire (Draw One/Three, Standard scoring + timer, double/right-click home,
  bouncing win cascade), FreeCell (the real Microsoft deals 1-32000, Select Game, Restart, supermoves,
  safe auto-play, win/loss streak), Spider (1/2/4 suits, Undo, runs clear, can't deal onto an empty
  column), Minesweeper (Beginner/Intermediate/Expert/Custom, LED counters, smiley, flags/?, chording,
  safe first click, Best Times), Hearts (Pauline, Michele, Ben; pass left/right/across/hold, moon
  shooting, to 100). Stats and settings in data/games.json. All Programs now has submenus
  (Program.group: Accessories, Accessories/System Tools, Games).
- Shared helpers for simulated casts: `claudexp/programs/people.py`.
- Speed: gemma4 is a *thinking* model (~30s of hidden reasoning per reply). MUCK and IRC pass
  think=False (0.5s replies) via AIM's llm.LLM.chat(think=..., priority=...); AIM itself still uses
  the model default. All programs use AIM's context_size so Ollama never reloads the model.
  main.py exits with os._exit so a running generation can't hang shutdown.
- userpic.jpg (Welcome + Start menu) and the 1024x768 Bliss wallpaper are in.

## Next
1. Real XP icons/title-bar buttons as the user finds them (see list in chat 2026-10-07)
2. Ideas: one shared presence per buddy across AIM/IRC/MUCK; IRC MemoServ memos and MUCK mail;
   replying to emails; a 'World activity' setting (Low/Normal/Lively)
