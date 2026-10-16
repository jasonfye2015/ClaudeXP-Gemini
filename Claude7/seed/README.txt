Claude7 seed
============

A head start for SYSTEM-2011 (Windows 7, October 2011): the user's earlier Windows 7 simulator, built with another
LLM, copied here on 2026-10-17 from Desktop\new stuff\projects\ClaudeTimeline\PCWindows7 (the original is untouched).
It's reference material to build the real Claude7 from - not Claude7 itself. The launcher shows SYSTEM-2011 as
installed only once Claude7\main.py exists.

  win7_2011\           the PySide6 simulator (win7sim\ about 20,000 lines, tests\, research\, README.md):
                       Windows 7 shell, Start menu and taskbar, BIOS/boot/logon screens, MSN Messenger with 34 close
                       contacts and their art, mIRC (FurNet), MushClient (PawPrints MUCK), Furry Directory, Windows
                       Update, Media Player, defragmenter, screen saver, Sticky Notes, Snipping Tool, torrent client
    assets\            its images, MSN contacts' icons, photos and captions (45 MB)
    Storage\           its runtime data. Left out: Models (7 GB NemoMix, already in Local Storage) and Runtime
                       (llama.cpp, also in Local Storage)
  Windows 7 Parts\     the art and sound library: wallpapers, boot animations, Start orbs, MSN styling, icons,
                       sounds, logon and setup screens (223 MB, kept out of git)
  Screen Shots\        how it looked
  main.py              its own launcher (runs win7_2011.main)

Not copied: the Replit/Node scaffolding (pnpm, TypeScript, the API server), which the Python app doesn't use.
