# 12. On a Mac

The same SSD runs the Timeline on an Apple silicon Mac (it was built against a MacBook Neo with an A18 Pro and 8 GB).
Nothing is installed on the Mac.

## Starting

Double-click **Claude Timeline.command**. The first time, macOS refuses because it's from an unidentified developer:
right-click, Open, and allow it once. Kithylin AI has its own `Kithylin AI.command` in `ClaudeApps\kithylinai`.

The `.command` runs the launcher on `Python-mac`, the Timeline's Mac Python, and puts Python's compiled-code cache in
`~/Library/Caches/Claude Timeline`, on the Mac's own disk: the SSD's exFAT clusters are 256 KB, so thousands of tiny
cache files would eat gigabytes.

## How it's wired

- **Python-mac** is python-build-standalone 3.14.9 for arm64, with the same packages as the Windows Python installed
  by `pip --platform macosx_14_0_arm64 --target`. Qt's universal binaries were thinned to arm64 only, which brought
  the folder from several gigabytes to 1.8 GB. It isn't in git; if it's ever lost, that's how to make it again.
- **The engine** is llama.cpp's Apple build in `Local Storage\LLM Models\llama.cpp\macos`; the launcher, the computers
  and Kithylin AI pick it on a Mac. Models run on the Mac's GPU through Metal.
- **Memory:** 8 GB is shared between everything. The Timeline limits what it loads on a Mac (`memory_limit()` in the
  model code), and a 12B model is a squeeze; the 4B and 1B models are comfortable. Expect one model at a time.
- **Fonts:** macOS has Tahoma, Arial, Verdana and Courier New but not Segoe UI, Consolas or Lucida Console, so
  `claudecore\macfonts.py` maps each Windows font to the closest Mac one (Segoe UI to the Mac's own UI font, Consolas
  to Menlo) when the program starts. Without it Qt picks any font with the wrong widths.
- **Retina:** icons are drawn at twice the pixels; the code asks for sizes in points, not pixels, after the XP
  desktop icons came out double-sized.
- **Line endings:** `.command` files are kept with Unix line endings by `.gitattributes`, or the Mac won't run them.

## What works and what's different

All three computers boot and run on the Mac, and the archive viewers, games and Kithylin AI with them. Things to know:

- Full screen is F11 as on Windows; the Mac's own Cmd shortcuts belong to macOS.
- Anything that leans on Windows itself isn't there: the launcher's `.exe`, the console emulator cores and Chocolate
  Doom (Windows builds), the Furry Hollow's OpenSimulator (a Windows .NET setup), Copilot Voice and Image Creator's
  engines (installed for Windows). The programs themselves open and say so.
- Loading a 12B on 8 GB is slow and may be refused; pick a smaller model in AI Models, or run Kithylin v1.
- A magenta square where a picture should be means a file wasn't found, usually a path whose case doesn't match the
  file's name.
- The second stage of Mac support (the TV, the heavier programs, proper testing on the machine itself) hasn't been
  done. If something misbehaves on the Mac and not on Windows, that's where to look first.

## Ejecting

Nothing running, then eject the drive in Finder before pulling it. macOS leaves `._*` and `.DS_Store` files on the
drive; git ignores them.
