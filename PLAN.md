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
- Shared helpers for simulated casts: `claudexp/programs/people.py`.
- Speed: gemma4 is a *thinking* model (~30s of hidden reasoning per reply). MUCK and IRC pass
  think=False (0.5s replies) via AIM's llm.LLM.chat(think=..., priority=...); AIM itself still uses
  the model default. All programs use AIM's context_size so Ollama never reloads the model.
  main.py exits with os._exit so a running generation can't hang shutdown.
- userpic.jpg (Welcome + Start menu) and the 1024x768 Bliss wallpaper are in.

## Next
1. Real XP icons/title-bar buttons as the user finds them (see list in chat 2026-10-07)
2. Shared memory between programs (a buddy remembers what you said on the MUCK when you IM them)
