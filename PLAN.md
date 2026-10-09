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
- **System Recovery** (`claudexp/setup/`): press SPACE during the BIOS test (or 'Start recovery/format' on
  the 'safe to turn off' screen) -> recovery menu -> 'Press any
  key to boot from CD...' -> blue text-mode Setup (Welcome, licence F8/Y, partitions, file system: Quick
  format / full format / leave intact, with [X] Program history (P) and [X] Buddies' memories (M), F to
  format, copying files, 15 s reboot) -> a real process restart (main.py relaunches ClaudeXP and waits) ->
  GUI Setup (steps, minutes countdown, slides, wizard: name/organization, computer name, date, network)
  -> OOBE with assets/sounds/oobe_music.mp3 (Welcome, register, Who will use this computer?, Thank you)
  -> Welcome screen. Format wipes all of data/ (minus unchecked groups); leave-intact resets only Windows
  settings. Program history = Program Files/*/data + data/claudeai; memories = data/journals, mail.json,
  life.json. Nothing is deleted: it's moved to 'Recovery Backups/<date time>/' (gitignored). E: is never
  touched. data/setup.json tracks the stage (gui/oobe) so a reboot mid-Setup resumes it.
  CLAUDEXP_SETUP_SPEED=20 speeds Setup up for tests. ~3-4 minutes at normal speed.
- **Accessories & tools** (`claudexp/programs/`): Calculator (calc.py, Standard view, XP's '0.' display,
  memory, keyboard), Run... (run.py, Start menu; history in data/run.json), Command Prompt (cmd.py: dir, cd,
  type, md, rd, del -> Recycle Bin, copy, ren, tree, color, title, ipconfig, ping over the dial-up, hostname,
  shutdown -s/-r/-l, format c: -> restart into System Recovery, start, program names), Task Manager
  (taskmgr.py: Applications, Processes, Performance, Networking; the model's work shows as svchost.exe CPU;
  ending explorer.exe hides the taskbar/icons until 'explorer' is run). Open it from the taskbar's right-click
  menu (also Cascade/Tile/Show the Desktop) or Ctrl+Alt+End (the host OS keeps Ctrl+Alt+Del and
  Ctrl+Shift+Esc). commands.py resolves names for Run and cmd. Program.listed=False keeps Task Manager out
  of All Programs.
- **Paint** (`programs/paint.py`): all 16 XP tools with their option boxes (brush shapes, line widths, fill
  styles, eraser sizes, zoom), 28-colour palette (left = foreground, right = background, double-click = Edit
  Colors), 3 undo levels like XP, move/Ctrl-copy/cut/paste selections (rect and free-form, opaque/transparent),
  text with a Fonts bar, curves (drag, then two bends), polygons, Shift for 45deg/squares/circles, canvas resize
  handles, zoom + grid, Image menu (Flip/Rotate, Stretch, Invert, Attributes, Clear), Set As Background,
  Print. Saves .bmp/.png/.jpg/.gif (My Pictures). Explorer's right-click 'Edit' on pictures opens it.
- **Windows Media Player 8** (`programs/wmp.py`, replaces the old mini player): Features taskbar, Now Playing
  with visualizations driven by the real audio (QAudioBufferOutput + Goertzel bands: Bars, Scope, Ambience),
  playlist, Media Library (My Music, Shared Music incl. a once-only 'Sample Music' copy of the OOBE music,
  C:\WINDOWS\Media, E:) with ID3 tags, Radio Tuner (online only; stations are always 'too busy'), Copy
  from CD / to Device messages, Skin Chooser (4 colour skins), shuffle/repeat; settings in data/wmp.json.
- **Internet games** (`games/zone.py` + icheckers.py, ireversi.py): need the dial-up (offers to connect),
  'Looking for opponents...', then an awake buddy (85%) or a Zone stranger; XP's canned-phrase chat with
  replies and in-game reactions; Beginner/Intermediate/Expert (alpha-beta: checkers depth 1/4/8, reversi
  1/3/4); Play again?; disconnect ends the game. Finished (or abandoned) games go into the buddy's journal
  and 30% of the time they reach out about it. Process names chkrzm.exe / rvsezm.exe in Task Manager.
  Also Internet Backgammon (ibackgammon.py: dice, bar, bearing off, use-both-dice rule, gammons; evaluator =
  race + blots + points + hits), Internet Hearts (ihearts.py, the offline table with buddies in the seats;
  hearts.py now has per-table names and choose/trick_taken/game_over hooks) and Internet Spades (ispades.py:
  partner across, bids incl. Nil, spades broken, bags, 500 to win). The Zone takes a list of opponents;
  card tables are SELF_DRIVEN with SEATS = 3 and report finished(result); each buddy's diary entry is written
  from their seat (outcome_for).
- **WordPad** (`programs/wordpad.py`): toolbar, format bar (font, size, B/I/U, colour, align, bullets), ruler,
  Find/Replace, Date/Time, Font dialog, Print, New (Rich Text / Text). Its own RTF writer + reader (fonts,
  sizes, colours, bold/italic/underline/strike, alignment, unicode); .rtf/.wri open in WordPad from Explorer.
- **Outlook Express 6 + Address Book** (`programs/outlook.py`): Inbox = the life mailbox (shared with Netscape
  WebMail; deleted mail gets folder='deleted'), Outbox/Sent/Drafts in data/outlook.json, preview pane,
  Contacts pane, Reply/Forward with quoting, Send/Recv (dials up), offline mail waits in the Outbox.
  Sending calls life.receive_email(): the buddy's journal notes it and a REPLY_PROMPT answer arrives 2-9 min
  later (deferred while they sleep; queue in life.json survives restarts); unknown addresses bounce from the
  Mail Delivery Subsystem. Address Book (wab) lists every buddy's address.
- **3D Pinball - Space Cadet** (`games/pinball.py`): a 2D tribute with real physics (8 substeps per frame:
  gravity, segment/circle collisions, flippers as swinging capsules that pass on their surface speed), plunger
  lane with a one-way gate, top arc, pop bumpers, slingshots, drop targets -> 'Hyperspace lit' -> Hyperspace
  hole = mission (rank Cadet..Fleet Admiral), rollover lanes -> bonus multiplier, end-of-ball bonus, nudge/TILT,
  'ball search' for a still ball, 3 balls, top-5 high scores. Keys Z, /, Space, X/., F2, F3. Tested headless
  with a flipper-tapping bot: no escapes, no stuck spots.
- **Calculator Scientific view** (calc.py rewritten around an operand/operator stack: Standard is strictly
  left-to-right, Scientific has precedence + brackets; Hex/Dec/Oct/Bin as 64-bit two's complement,
  Degrees/Radians/Grads, Inv/Hyp, trig/log/powers/roots/n!/dms/Exp/F-E/pi, Mod/And/Or/Xor/Lsh/Not/Int,
  digit grouping; view + grouping saved in data/calc.json).
- **System Tools / Entertainment**: Character Map (charmap.py), Disk Cleanup (cleanmgr.py: real sizes; empties
  the Recycle Bin, C:\\WINDOWS\\Temp and Netscape's page cache after "Are you sure?"), System Information
  (msinfo.py, the 2001 PC's hardware/software), Sound Recorder (sndrec.py: QAudioSource/QAudioSink PCM at
  22.05 kHz mono, 60 s max, waveform, .wav open/save, Delete Before/After, Effects).
- **System Restore** (`programs/sysrestore.py`): restore points = copies of Windows' settings files (SETTINGS)
  in data/System Volume Information/_restore/RP<n>; daily System Checkpoint at logon, one before Windows
  Update installs, manual points; restoring makes an Undo point, then setup.reboot(app, action) restarts the
  process and puts the files back while nothing runs (settings absent at that time go back to defaults);
  'Restoration Complete' at the next logon. Never touches documents, mail or journals.
- **Search Companion** (`programs/search.py`): Rover drawn and animated (wag, blink, sniff while searching);
  pictures/music/video, documents, all files (name with wildcards, a phrase inside text files, where to look),
  computers or people, Help, the Internet (Netscape); results stream in via a QTimer-driven os.walk.
- **Help and Support Center** (`programs/helpctr.py`): XP home page, topics, Index, Search, Back/Forward;
  articles are a real guide to ClaudeXP (incl. 'My buddies don't answer' -> Ollama). Links launch programs.
  The Start menu artwork lacks the item, so startmenu.py paints 'Help and Support' below Run.
- **Tour Windows XP** (`programs/tour.py`): animated slides with the OOBE music; after Setup, a tray icon pops
  the 'Take a tour of Windows XP' balloon on the first logon.
- **One identity** (user.py 'online' section + accounts.py widgets): a Windows name plus an online handle
  (or 'Use my Windows name online', which then follows Windows renames), optional Windows password (salted
  hash; Welcome screen asks, XP's 'Did you forget your password?' hint) and optional online password (kept
  lightly encoded so it can be auto-filled). With 'linked' on: AOL dial-up user/password come from it
  (network._load), AIM gets screen name + saved password + Auto-login before it starts (aim.apply_identity),
  IRC nick/alt follow it with no Options dialog, the MUCK character is created/renamed to it, e-mail is
  <handle>@aol.com, and life.user (what buddies call you) is user.known_as(). Renames are silent to the buddies.
  Setup's OOBE has name + picture, online name, and passwords pages; User Accounts can change all of it.
  Older installs migrate with handle = AIM screen name and linked off (switch it on in User Accounts).
- **FurTV 2000** (`programs/tv/`): an over-the-air tuner card viewer for the user's own TV archive (not in
  git; dropped into Local Storage = E:). library.py finds 'Movies…', 'TV Series…/<Show>' and '…Commercials…'
  folders, reads running times from AVI/MP4/MKV headers (cached in data/tv_index.json, ~1s rescans) and matches
  files to assets/tvguide/shows.txt (episode/movie details from Wikipedia) plus a show's own '*Episode Guide*.txt'.
  schedule.py: a live wall-clock schedule from 6am Jan 1 2001, deterministic (seeded decks: every item once per
  cycle, then reshuffled). WAGG 4: Ren & Stimpy 6am-7pm, Mongrels 7-11pm (on the half hour), Aqua Teen 11pm-6am
  with the DVD extras as promos. KPAW 9: movies all day on 5-minute starts (plus the ATHF movie). 2-3 commercials
  only between programs, then an Up Next card. Channels 2/7/11 are static (assets/video/static*.mp4, also used for
  missing files). tuner.py: QVideoSink-painted picture, snow on channel change, green OSD, info band, CC
  (subtitle tracks), SAP (audio tracks; RiffTrax riff track chosen automatically), keys, right-click menu.
  guide.py: TV Guide Channel-style grid, 3 hours at a time, up to a week ahead, details + Watch.
  Dates after 2001 (air dates, movie years) are hidden.
  KHAH 13 'Ha-Ha 13' (added 2026-10-09): everything in TV Series/Comedy (stand-up specials, Comedy Central
  Presents, The Maria Bamford Show; ~23 h) all day on 5-minute starts with ads between programs. library._comedy_info
  cleans the messy names (COMEDY_TITLES for the specials); MPEG-1/2 .mpg running times come from the first/last
  pack clock (_mpeg_ps). The guide grows a row per channel.
- **FurComix Reader** (`programs/comix/`): reads E:\Furry Media Archive…\Comic Scans… (user's archive, not in
  git). Never indexes: each shelf is one os.scandir; covers are decoded (scaled while decoding) on a thread pool
  only when their tile scrolls into view, cached in data/comix_thumbs. A comic = folder of images or
  .cbz/.zip (zipfile), .cbr/.rar/.cb7/.7z (7-Zip if installed, else a friendly message) or .pdf (QtPdf, UI thread
  only); single-folder wrappers are looked through; an archive next to a same-named folder is hidden (already
  extracted). The user's own RAR/CBR/ZIP comics were extracted beside their archives with 7-Zip (2026-10-08;
  originals kept; AOI's zips are password-protected site downloads, its comix/ folder already has the pages).
  Library grid (series draw as stacks, read-progress bars, Continue Reading row, filter), CDisplay-style viewer
  (Fit Page/Fit Width/two-page spreads, filmstrip, preloads 3 pages, wheel/Space scroll tall pages then turn),
  progress in data/comix.json.
  An archive is also hidden when its pages already lie loose beside it (a packaged copy, e.g. Hit The Showers).
- **FurFolio Reader** (`programs/folio/gallery.py`): E:\Furry Media Archive…\Portfolios… as an art gallery
  (artists -> folios -> pieces; ~6,500 images, never indexed). Artists hang as matted prints, folios as portfolio
  cases, a folio is a wall of thumbnails of every piece (lazy, cached in data/folio_thumbs; a cover skips damaged
  files, e.g. Brain O'Connell's Cover.jpg is really MPEG data). One-folio artists open straight into it; folio names
  lose the artist prefix; a folio's Info.txt shows under its heading. Viewer: piece matted + framed on a charcoal
  wall with a brass caption plate, slideshow, Actual Size with drag-to-pan, filmstrip, My Favorites (data/folio.json).
  Reuses FurComix's Loader and name helpers. Start menu: Programs > FurFolio Reader (both readers).
- **FurStory Reader** (`programs/folio/stories.py`, installed with FurFolio): E:\…\Authors and Stories… as a
  bookshelf (217 leather spines on wooden shelves, from names only). Opening a book walks that folder: every
  readable file is a chapter, grouped by sub-folder (index/contents files first). Reads HTML (pictures kept,
  colours/fonts/scripts stripped, links between its own pages turn chapters), TXT (hard-wrapped lines reflowed,
  scene breaks kept), RTF (WordPad's from_rtf), PDF text (QtPdf), Word .doc/.wri (best-effort text runs),
  WordPerfect (.wpd document-pointer parser, ~22/29), and anything inside .zip/.gz; .cbr chapters open in FurComix.
  ~5,300 chapters, ~100% open. Reading: centred serif column, Paper/Sepia/Night, text size, chapter nav, place
  remembered (data/stories.json), Continue button on the shelf, red ribbon on books in progress.
- **Fur CD Viewer** (`programs/folio/cdviewer.py`): E:\…\Art CDs and DVDs… (64 artist discs, ~30k images).
  Rack of jewel cases / DVD keep cases with the disc's own cover art (cover/front/info/large… names first);
  inside, folders as manila tiles with their first picture peeking out, pictures as thumbnails, videos as film
  tiles. Skips the discs' own thumbnail folders and tn_/_t images, exe/dll/html/swf, AUDIO_TS and small DVD menu
  VOBs. Pictures open in FurFolio's framed Viewer (reused via duck-typed owner methods); AVI/MPEG/VOB play in a
  built-in VideoPane (QVideoSink painted). Desktop shortcut. Video tiles show a real still from FrameGrabber
  (one QMediaPlayer on the UI thread, a still ~4s in, retried at the middle if the frame is nearly black, cached
  in data/folio_thumbs; seeking must be deferred out of the player's own status signal or it stalls).
- **Furry Con CD Viewer** (`programs/folio/furcon.py`, a CDViewer subclass): E:\…\FurCon CDs… (11 convention
  recap discs, ~375 photos, ~105 videos). Lobby of con badges on lanyards in each con's colours (Anthrocon,
  Eurofurence, Further Confusion, Midwest FurFest; names/editions normalised from folder names), sorted by con and
  year, on hotel-carpet red. Opening a con shows the whole weekend on one page: all photos, then all videos,
  gathered from its sub-folders. Video-only cons (5 of 11) get a video still on their badge. Desktop shortcut.
- **Desktop / Start menu layout (2026-10-08)**: desktop order Recycle Bin, My Computer, America Online, the E:
  folder links, then the rest; no Notepad icon. desktop_icons.LAYOUT=2 makes existing desktops reflow the built-in
  shortcuts once (user files keep their spots); bump it whenever builtins() is reordered. Start > Programs >
  Furry Stuff holds FurTV, FurComix, FurFolio, FurStory, Fur CD Viewer, Furry Con CD Viewer and copies of the
  folder links (only listed when that folder exists on E:).
- **ClaudeAI tray** (`programs/claudeai/__init__.py`): spark icon in the notification area while it runs
  (double-click opens; right-click Open / New Chat / Load at Startup / Exit). Load at Startup (settings
  'startup', default on; also a checkbox in ClaudeAI Settings) puts it in the tray at logon without a window
  (app.show_desktop -> claudeai.start_at_logon). X tucks the window into the tray (one-time balloon); Exit quits.
  store.Settings.set now merges with the file so the tray and the window don't overwrite each other.
- **Console emulators** (`programs/nes/emulator.py`: one window class + a SYSTEMS table of core, ROM folder
  regex, extensions, icon, size and face-button keys; NES = FCE Ultra, SNES = Snes9x 1.63 with S=X, A=Y, Q=L,
  W=R; data/<system>/; Task Manager reads content.process_image). Also GB (Gambatte), GBC (a renamed copy of
  Gambatte so both run at once), GBA (mGBA), Genesis+32X (PicoDrive), Master System (Genesis Plus GX); SameBoy
  (2 MHz audio rate) and SMS Plus GX (crashed on load) were tried and dropped. Each system is its own program with
  the user's icon, on the desktop and in Start > Programs > Game Emulation. Entry points <key>_icon/open_<key>/
  shutdown_<key> are generated from SYSTEMS; programs.EMULATORS lists names.
  Later: Game Gear (Gearsystem) and Apple ][ (AppleWin, 560x384). Computers set System.keyboard: libretro.py
  answers SET_KEYBOARD_CALLBACK and polls RETRO_DEVICE_KEYBOARD; every key goes to the machine as RETROK codes
  (capitals only, like the real Apple ][+; only F-keys/Pause stay as shortcuts). ROM folders are now named
  'NES (Roms)' etc.; icons are the user's per-folder PNGs copied to assets/images/<key>_icon.png.
- **NES Emulator** (`programs/nes/`, shown as FCE Ultra): libretro.py is our own ctypes libretro front end
  (environment/video/audio/input callbacks, SRAM, serialize); fceu.py is the window. Core:
  assets/emulators/fceumm_libretro.dll (GPL-2, see README there; runs ~2,800 fps headless). ROMs are the user's,
  from E:\Emulation\NES… (not in git). Game list with cleaned titles, 1x/2x/3x (steps down to fit the screen),
  pixel-sharp or 4:3 TV aspect, QAudioSink sound at the core's rate, battery saves (data/nes/saves), 10 save
  state slots (data/nes/states), pause when inactive, recent games. Keys: arrows, X=A, Z=B, Enter=Start,
  Space/Shift=Select, F5/F7 states, 0-9 slot, P pause, F1 reset, Esc list. Start > Games and the desktop.
  Note: grabbing the XPWindow alone renders the screen white; grab the main window for screenshots.
- **Flying Toasters screen saver** (screensaver.FlyingToasters): the user's 4.4 s clip
  (assets/video/flying_toasters.mp4, 1280x718, no audio) looped silently via QVideoSink, fitted to the screen with
  the bars filled in the clip's own background colour; listed in Display Properties > Screen Saver.
- **Doom-engine games** (Start > Programs > Games + desktop): Doom, Doom II, Wolfenstein 3D are emulator.py SYSTEMS
  on PrBoom (one DLL copy each so they can run together), reading E:\WADs (System.top / System.games pick and name
  the WADs; Wolfenstein 3D.wad is a Doom II TC, PrBoom finds DOOM2 beside it). Classic keys: arrows, Ctrl fire,
  Space use, Shift run, , . strafe, PgUp/PgDn weapons, Tab map, Esc menu (A=use/confirm, X=fire, Y=run, L/R strafe,
  L2/R2 weapons, Select map on the RetroPad). libretro.py fix: cores keep the system/save dir pointers (now stable
  buffers) and need a real log interface (PrBoom wrote through a NULL one -> 'access violation writing 0x0').
- **Heretic / Hexen** (`programs/doom/native.py`): no libretro core, so Chocolate Heretic/Hexen 3.1.1
  (assets/engines/chocolate) run as their own processes; the SDL window is restyled WS_CHILD and adopted with
  QWindow.fromWinId + createWindowContainer. A native child paints over ClaudeXP windows, so when the game window
  isn't in front (or a menu/Start menu is open) it's swapped for a PrintWindow still. Config/saves in data/<game>/
  (-config, -extraconfig, -savedir); graphical_startup 0. The user's HEXEN.WAD is the 4-level demo, which lacks
  FONTAY (yellow font) that Chocolate Hexen needs: a small PWAD is generated from its own FONTA lumps at launch.
- **ClaudeTV** (was FurTV 2000; renamed 2026-10-09 - it's plain TV, not furry): on the desktop after the folders and
  directly in All Programs; LAYOUT=5 removes the old FurTV shortcut from the Furry Programs folder.
- **Shortcuts + desktop folders (2026-10-09)**: explorer/shortcuts.py adds ClaudeXP .lnk files ('[ClaudeXP
  Shortcut]' + Program=key or Target=path); Explorer hides '.lnk', shows the target's icon, type 'Shortcut'; opening
  one launches it. desktop_icons LAYOUT=3 makes 'Furry Programs' (the six furry programs) and 'Emulation' (the nine
  emulators) desktop folders once and drops those loose icons; the folders sit right after the E: folder links.
  LAYOUT=4 adds a 'Games' folder (Doom, Doom II, Wolfenstein 3D, Heretic, Hexen); FOLDERS_SINCE says which layout
  version introduced each folder so upgrades only create the new ones.
  The archive folders lost their '(xx.xgb)' size suffixes; programs already matched by name prefix, and saved paths
  in data/comix.json, stories.json and tv_index.json were rewritten to the new names.
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
