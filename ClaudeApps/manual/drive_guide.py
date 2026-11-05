"""The drive's guides: writes "Give this to Claude.MD" and "Read Me.MD" at the top of the SSD (beside the Claude Timeline
folder). The first, for Claude: what the drive is,
how to run it, what to download again to rebuild it, where everything goes, and a full inventory: the Timeline's own
folders, every program on the three computers (Manual chapter 15), and everything in Local Storage (chapter 14's scan).

    python -m manual.drive_guide [--out PATH]

It's written to be handed to Claude when the drive needs rebuilding. Run it again whenever things change."""
import argparse
import os
import re
import tempfile
import time
from pathlib import Path

TIMELINE = Path(__file__).resolve().parents[2]
OUT = TIMELINE.parent / "Give this to Claude.MD"
READ_ME = TIMELINE.parent / "Read Me.MD"

GUIDE = r"""# Give this to Claude - the Claude Timeline SSD

Written for Claude (and for you) on {date}. Hand this file to Claude when the drive needs rebuilding or when you want
to know what's on it. Paths below are on this drive, `{drive}`. The drive letter can change from PC to PC; the
Timeline doesn't care.

## 1. What this drive is

The **Claude Timeline**: three recreated computers from three moments in time, sharing one archive and one cast of
characters, all written in Python and Qt by you and Claude.

| Computer | Folder | Era |
|---|---|---|
| EPOCH-2001 | `Claude Timeline\ClaudeXP` | Windows XP Home, October 2001 |
| SYSTEM-2011 | `Claude Timeline\Claude7` | Windows 7 Home Premium, October 2011 |
| WORKSTATION-2025 | `Claude Timeline\Claude11` | Windows 11 Home, October 2025 |

Around them:
- **The archive.** A personal furry media archive (comics, portfolios, stories, art CDs, con discs, videos, website
  rips), TV and movies with commercials, and personal photos and logs. Archive tools show it the same way in every era.
- **The residents.** Around 250 characters with personalities and daily lives, who chat, mail and post through each
  era's programs.
- **Local AI.** Language models run on the PC's graphics card through llama.cpp, with no cloud. They play the
  residents and power ClaudeAI, CopilotAI, Kithylin AI and Soul and Song.
- **Games.** Your own games (Claude and Magic among them), emulators, and Doom-engine games.

The project's own description is `Claude Timeline\PLAN.md`. The user manual is `Claude Timeline\Manual\` (17
chapters, also readable from the launcher's MANUAL button).

## 2. The top of the drive

| Item | What it is |
|---|---|
| `Claude Timeline\` | Everything: the code, the runtimes, and `Local Storage` (the archive and the AI models) |
| `Claude Timeline - Shortcut.lnk` | A shortcut to the folder (personal; never committed) |
| `Give this to Claude.MD` | This file, written by `python -m manual.drive_guide` |
| `Read Me.MD` | The short version for a person: how to start it, and what's in Local Storage |
| `$RECYCLE.BIN`, `System Volume Information`, `.Spotlight-V100`, `.fseventsd` | Windows' and macOS's own housekeeping |

## 3. How to run it

**Windows (10 or 11):** plug the SSD into a USB 3 port and double-click `Claude Timeline\Claude Timeline.exe`. That
opens the SYSTEC Multi-Boot Manager on the drive's own portable Python. Nothing is installed on the PC.
`Claude Timeline.bat` does the same with a console window, so start-up errors show there.

**Mac (Apple silicon):** double-click `Claude Timeline\Claude Timeline.command`. The first time, right-click it, choose
Open and allow it. It uses `Python-mac`. Manual chapter 12 lists what differs on a Mac.

**In the launcher:** pick a computer and press **LOAD THIS COMPUTER**. Other buttons along the bottom:
- **APPS** runs Kithylin AI, Soul and Song, ClaudeRPG, Python Studio and QBasic Studio on their own.
- **BACKUP** makes and restores backups.
- **MANUAL** opens the manual.
- **SELF-CHECK** shows what's wrong, if anything.

**Hardware it was built on:** a GTX 1080 Ti with 11 GB of video memory, using Vulkan. Language models need a graphics
card with Vulkan drivers (NVIDIA, AMD or Intel); a 12B model wants about 8 GB of video memory. Without a capable card
the models run on the CPU, slowly. Everything that doesn't talk works without any model.

**Before unplugging:** shut every computer down from its own Start menu, close Kithylin AI, stop any training, and
eject the drive from the tray.

## 4. A fresh PC: what to do first

Almost everything the Timeline needs is on the drive: Python and Qt with Microsoft's C++ runtime, the llama.cpp
engine, the emulator cores, the Doom engines, 7-Zip, ffmpeg, and the OpenSim world's .NET runtime and viewer. On a
newly installed Windows:

1. **Install the graphics card's driver first** (NVIDIA's, for the GTX 1080 Ti). A fresh Windows often runs on a basic
   display driver without Vulkan. Until the real one is installed the models fall back to the CPU, which is very
   slow, or don't run, and Image Creator won't start.
2. **Smart App Control** is often on after a clean Windows 11 install, and it can block unsigned programs: the
   launcher's `.exe`, the llama.cpp engine, the emulator cores, the Doom engines. If the launcher won't open, start
   `Claude Timeline.bat`, which runs the signed Python instead. Turning Smart App Control off can't be undone
   without reinstalling Windows.
3. **The drive letter doesn't matter.** The launcher, the standalone apps and every computer check where the
   Timeline is at startup, and point any saved paths at the new place (`ClaudeCore\claudecore\relocate.py`).
4. **Permission prompts** may appear the first time: the microphone (Copilot Voice) and possibly the firewall (the
   OpenSim world). Defender also scans files on first use, so the first starts are slower.
5. **What the PC kept, and a format loses:** Claude Code's notes about this project (Appendix E holds a copy from
   when this file was made), the screen saver's settings (reinstall the `.scr` from
   `Local Storage\Windows Screen saver`), and the development tools: git, the GitHub CLI, Node.js, Claude Code and
   Thonny. None of these are needed just to run the Timeline.

## 5. What lives where

| Folder (in `Claude Timeline\`) | What it holds |
|---|---|
| `ClaudeLauncher\` | The SYSTEC Multi-Boot Manager (`main.py`), its art and spec sheets, and `exe\` (the source of `Claude Timeline.exe`) |
| `ClaudeXP\`, `Claude7\`, `Claude11\` | The three computers. Each has its own `data\` (account, mail, chats, desktop, residents' memories) and `Recovery Backups\` |
| `ClaudeCore\` | The shared engine: the llama.cpp engine and request broker, the life simulation, the local web server, the host API |
| `ClaudeArchive\` | The archive tools: FurComix, FurFolio, FurStory, Fur CD Viewer, Furry Con CD Viewer, Furry Video Browser, ClaudeTV and its TV Guide, 7-Zip |
| `ClaudeGames\` | The games and emulators shared by every era. `Saves\` holds every game's progress |
| `ClaudeGames\Claude and Magic\` | Claude and Magic's own development repo, with its own git. The Timeline plays the built copy in `ClaudeGames\claudemagic\` |
| `ClaudeApps\` | ClaudeAI, CopilotAI, Copilot Voice, Image Creator, Python Studio, QBasic Studio, Kithylin AI, Soul and Song, the Manual tools, the screen-saver build, selfmodel (training) |
| `Residents\` | The cast: one folder per character |
| `Persona Styles\` | Frozen versions of how residents are made and prompted (V1.0, V1.1), chosen at Load and Format |
| `Profile\` | You: `profile.json` (name, fursona, Furry Code), backup settings, standalone apps' settings |
| `Manual\` | The user manual (Markdown and screenshots) |
| `Tests\` | The test suite: `Run All Tests.bat`, or `python Tests\run.py` (`--slow` also boots each computer) |
| `Python\`, `Python-mac\` | The portable Python runtimes for Windows and for Apple silicon Macs |
| `Local Storage\` | The "external drive" every computer sees as E: - the archive, the models, ROMs, WADs, Kiwix and backups |
| `.git\` | The Timeline's git history |

## 6. How it works

**Processes.** The launcher (`ClaudeLauncher\main.py`) is one program. Booting a computer starts that computer as a
separate Python process, with `CLAUDE_TIMELINE=1` in its environment; the launcher minimises itself and waits for it
to end. Only one computer runs at a time. The standalone apps (APPS) run as their own processes too, through
`python -m claudecore.standalone <app>`.

**Each computer** is a full desktop drawn with Qt: its own window manager, taskbar, Start menu, Explorer, Control
Panel, Setup and sounds, and a virtual drive C: in its `data\Drive C`. Local Storage appears as drive E:.
EPOCH-2001 (`ClaudeXP`) is the original and holds the master **program registry**
(`ClaudeXP\claudexp\programs\__init__.py`). SYSTEM-2011 and WORKSTATION-2025 build their registries from it,
dropping, renaming and adding programs per era. They run XP's programs through a compatibility layer
(`xpcompat.py`) that swaps XP's window and system modules for their own, so an XP program gets an Aero or Mica
window without knowing.

**Shared programs** (in `ClaudeGames`, `ClaudeArchive`, `ClaudeApps`) never import an OS's modules. They ask the
**host** (`ClaudeCore\claudecore\host.py`) for a window in the current OS's style, sounds, their saves, their data
folder and Local Storage. Register a program once in XP's registry and it appears on all three computers.

**The AI.** `ClaudeCore\claudecore\ai\` runs one `llama-server` from llama.cpp on 127.0.0.1 as a "router": a model
loads onto the graphics card the first time something asks for it, and the least recently used is unloaded when room
is needed. Every program's requests go through one queue, the **broker**, with priorities: what you're waiting for
first, the residents' background life last. `ai_models.py` says which model does which job (conversation,
background, assistant, pictures, coding), changeable in Control Panel > AI Models. An `ollama` stand-in module means
older code that imports `ollama` is answered by this engine.

**The living world.** Each computer keeps the residents' journals in its `data\journals`. About once an hour one
resident's life moves on (a new journal note), and sometimes they tell you by IM, IRC or e-mail. After the PC has been
off, a short catch-up runs at log-on. Every program adds a resident's recent journal entries to the prompt, so what
you said on IRC is remembered on AIM. `residents_sync.py` builds each computer's contact lists, Fur Directory cards
and buddy icons from `Residents\` at startup.

**The period web.** The browsers (Netscape and Internet Explorer in 2001, newer ones later) serve the website rips
from Local Storage read-only at their real addresses, and have the model write everything else as you browse: portal
pages, the residents' home pages and journals, the social sites. Generated pages are cached in that era's `data`,
so 2001 never sees a 2025 post.

**Media.** The archive tools read Local Storage and never write to it. Videos and Flash open in each era's own
players. ClaudeTV builds channels and a schedule from the TV folders (section 13).

The full developer's map, from Manual chapter 13, is Appendix D.

## 7. The residents

About 260 characters live in `Residents\<Name>\`, in three tiers: **main furs** (your IM contacts, with icons, web
pages, pictures and hand-written lives in every era), **support furs** (the IRC and MUCK regulars) and **background
furs** (the crowd).

Each resident's folder holds:
- `resident.json`, the timeless part: fur name, tier, real name, birth date, fursona, personality, mannerisms, how
  they met you, their friends and their Furry and YIFF Codes.
- `eras\2001.json`, `eras\2011.json`, `eras\2025.json`: their accounts on that era's services, job, home, situation,
  schedule and a paragraph about their life then. No era file means they weren't around then.
- `media\` (main furs): pictures and icons. `sources\`: what the character was drawn from.

Birth dates make everyone an adult in 2001, so a resident who is 26 on the XP machine is 36 in 2011 and 50 in 2025,
and their lives follow. Dated history keeps the eras consistent: each computer shows only what had happened by its
year. Memories are per computer: chats on one era's machine never carry to another. **Contact Persona Styles**
(`Persona Styles\V1.0`, `V1.1`, or "Development") are frozen versions of how residents are built and prompted,
chosen when EPOCH-2001 is formatted.

**Kithylin** is not a resident: he's you. Kithylin the Angelic Husky is your fursona, and the name of the models
trained on your own chat logs (Kithylin AI, Kithylin Autopilot).

The main furs:

{main_furs}

## 8. Claude and Magic

Your first-person dungeon crawler ("blobber", after Wizardry and Eye of the Beholder): a party of four goes down
twenty floors to the Lich King, then the Deep to floor 50, then Endless. Around the dungeon there's a town (Caer
Duin) with shops, a house, a casino and festivals, the Deep Wood with a farm and caves, and many games inside the
game: the Mage Tower, Claudecraft, Claudeablo, Super Claude Bros, the Fortress and more. It is one HTML file using
WebGL and Web Audio; it plays in its own Qt WebEngine window in the Timeline, or in any browser.

- **Source:** `ClaudeGames\Claude and Magic\` (its own git repo, `jasonfye2015/claude-and-magic`). The game logic and
  art are JavaScript in `src\js\`, concatenated in file-name order by `build.py` into
  `game\Claude and Magic v<version>.html`.
- **In the Timeline:** `ClaudeGames\claudemagic\` is a git subtree of that repo (remote `magic`). Its `__init__.py`
  opens the newest built HTML on a permanent browser profile in `ClaudeGames\Saves\claudemagic`.
- **Now:** version {cam_version}. `README.txt` describes every system in the game; `LORE.md`, `BALANCE.md` and
  `FIELDS.md` hold the world, the numbers and the save format; `UPGRADE_PLAN_*.md` are the plans it was built from.
- **Tests:** `node tests/run.js` (the rules, about 280 tests, through `tools\headless.js`, which must list every rules
  file) and `python build.py --check`. A visual harness renders scenes offscreen for screenshots.
- **Releasing a version:**
  1. Bump the version in `build.py`, `package.json`, `game\manifest.webmanifest` and `game\sw.js`; delete the old
     HTML and run `python build.py`.
  2. Add a line about the change to the Timeline's Help Center guide
     (`ClaudeXP\claudexp\programs\helpctr_guide.py`) and to Manual chapter 15, then run
     `python -m manual.catalog` from `ClaudeApps`; commit those in the Timeline.
  3. In the game repo: run the tests, commit, push, and wait for GitHub's CI to pass.
  4. In the Timeline: `git subtree pull --prefix=ClaudeGames/claudemagic magic main`, run `Tests\run.py claudemagic`,
     push branch `ClaudXP+Gemini`, then fast-forward `main` to it.

The most recent plans:

{cam_plans}

## 9. Glossary

| Term | Meaning |
|---|---|
| EPOCH-2001, SYSTEM-2011, WORKSTATION-2025 | The three computers: Windows XP (October 2001), Windows 7 (October 2011), Windows 11 (October 2025). Their clocks use the real month, day and time, with the era's year |
| SYSTEC Multi-Boot Manager | The launcher: one card per computer, plus Profile, Backup, Apps, Manual and the self-check |
| Local Storage, drive E: | `Claude Timeline\Local Storage`, the shared "external drive": the archive, models, ROMs, WADs, Kiwix |
| Load and Format | Reinstalls one computer's Windows: its `data` moves to `Recovery Backups\<date time>`, so it can be undone by hand |
| Self-check | The launcher's check for problems that stop a computer starting (bad program names, broken settings, missing Python) |
| Resident, main / support / background fur | The cast, in three tiers (section 7) |
| Era file | A resident's `eras\<year>.json`: their life and accounts in that era |
| Contact Persona Style | A frozen version of how residents are built and prompted (V1.0, V1.1, Development), chosen at Load and Format |
| Furry Code, YIFF Code | Old fandom codes (Furry Code 2.0, YIFF Code 3.0) describing species, interests and openness. Yours are set in the launcher or FurCoder; residents use them for attraction, roleplay and common ground |
| FurCoder | The program that encodes and decodes those codes |
| The Fur Directory | Who's who: every resident's card for the current era |
| The Furry Web | The website rips served at their real addresses, plus the pages the model writes as you browse |
| Furry Log | A diary of everything the language model does |
| Claudecadia | A Furcadia-style graphical chat world where the residents log in as furres |
| ClaudeAIM | The AIM-style buddy list on EPOCH-2001; the heart of the original project |
| ClaudeAI | The Timeline's own chat assistant, on Gemma 4 12B |
| Copilot programs | CopilotAI (assistant), Copilot Voice (speech in and out), Copilot Image Creator (Stable Diffusion) |
| Gemini programs | The Office-style suite on the computers: Gemini Word, Excel, PowerPoint, Outlook, Access, Publisher, Draw, Photo, Acrobat, Distiller |
| Kithylin | Your fursona (the Angelic Husky), and the name of the models trained on your chat logs |
| Kithylin AI | A standalone chat program with a Kithylin model, also on Telegram and Discord |
| Kithylin Autopilot | Kithylin takes over EPOCH-2001: answers IMs, writes e-mail, browses, watches TV, plays, on a real-clock day |
| selfmodel | The training pipeline that makes Kithylin models from your 2004-2011 chat logs (`ClaudeApps\selfmodel`) |
| Soul and Song | A standalone AI Companion with a written-down memory that grows daily (after the Companion Project guide) |
| Companion | One Soul and Song character, in `Local Storage\Projects\AI LLM Txt Files\Companions\` |
| Mind Levels | A Companion's memory banks: L1 who it is, L2 short-term, L3 long-term, L4 deep recall, L5 historical, L6 system instructions, L7 reflections. A full bank is distilled into one memory in the bank below |
| Memory Day | Every seven days, a Companion's weekly review: identity questions, the week's letters, distilling memory |
| Classic 7:7:7 | Soul and Song's original memory rule: seven memories a bank, distilled nightly, with Memory Day weekly |
| Host | `claudecore.host`: how a shared program asks the computer it's on for windows, sounds, saves and data |
| Broker | The one queue every program's model requests go through, by priority |
| xpcompat | How the 2011 and 2025 computers run XP's programs as their own |
| Recovery Backups | Where a format moves a computer's old data, inside that computer's folder |
| Saves | `ClaudeGames\Saves`: every game's progress, shared by all three eras |
| Caer Duin, the Deep Wood, the Lich King | Claude and Magic's town, its land outside the walls, and the boss on floor 20 |

## 10. Working on the project

The Timeline is built in sessions with **Claude Code**, opened in the `Claude Timeline` folder. What a new session
should know:

- **Two repositories.** The Timeline (`jasonfye2015/ClaudeXP-Gemini`): work on branch `ClaudXP+Gemini`, then
  fast-forward `main` to it. Claude and Magic (`jasonfye2015/claude-and-magic`): branch `main`, pulled into the
  Timeline as a subtree (section 8).
- **Commit and push each finished phase without asking**, in both repositories, and keep `main` level with
  `ClaudXP+Gemini`. Never commit `Claude Timeline - Shortcut.lnk`. Bot tokens and other secrets stay local and are
  never committed; scan staged changes for them.
- **Test before calling anything done:** `Tests\run.py` for the Timeline (`--slow` boots the computers), and
  `node tests/run.js` plus `python build.py --check` for Claude and Magic. Tests never touch the real `data` folders,
  saves or Kithylin AI's data.
- **Downloads are allowed** when something is needed. Delete the `package-lock.json` npm leaves behind.
- **Keep content original.** Characters, places and art are made for the project.
- **Processes:** stop a program only by its confirmed process ID. Real-time games need the shared precise timer with
  catch-up, or they run in slow motion.
- **New games** go in Start > Games and the Games folder only, not on the desktop.
- **Claude Code's own notes** about you and the project live on the PC, in
  `C:\Users\<you>\.claude\projects\<drive>--Claude-Timeline\memory\`. Appendix E is a copy of them from when this file
  was written. On a new PC, give them back to Claude, or copy the folder there.

## 11. The Manual

`Claude Timeline\Manual\`, readable in any text editor or from the launcher:

{manual}

## 12. Rebuilding the drive from nothing

Work in this order. Part A comes from GitHub and the web. Part B only exists in your backups.

### A. What can be downloaded again

**1. The code.** Both repositories are private on GitHub under `jasonfye2015`:
- `ClaudeXP-Gemini` - the whole Timeline. Branch `ClaudXP+Gemini`, mirrored to `main`. Clone it as
  `{drive}Claude Timeline`.
- `claude-and-magic` - Claude and Magic's source. Clone it as `Claude Timeline\ClaudeGames\Claude and Magic`. The
  Timeline already carries the built game in `ClaudeGames\claudemagic` (a git subtree, remote `magic`).

You'll need git and the GitHub CLI (`gh auth login`). This drive doesn't record file owners, so mark both folders safe:

```bash
git config --global --add safe.directory "{drive_fwd}Claude Timeline"
git config --global --add safe.directory "{drive_fwd}Claude Timeline/ClaudeGames/Claude and Magic"
```

The emulator cores (`ClaudeGames\emulators\cores`), the Chocolate Doom engines (`ClaudeGames\doom\engines`) and
7-Zip (`ClaudeArchive\tools\7-Zip`) are in git, so they come with the clone.

**2. Python.** Git ignores the runtimes, so rebuild them:
- **`Python\` (Windows):** CPython 3.14 for Windows. Install it from python.org into `Claude Timeline\Python` (or copy
  an installed Python there). Then run:
  `Python\python.exe -m pip install -r ClaudeXP\requirements.txt`. The core packages are PySide6 6.11.2, Pillow,
  pyspellchecker, jedi, pyflakes, httpx and tzdata.
- **`Python-mac\`:** python-build-standalone 3.14 for arm64, with the same packages.
- The launcher sets `PYTHONNOUSERSITE=1`, so the PC's own Python never interferes.

**3. The language engine.** llama.cpp build **b11533**, from https://github.com/ggml-org/llama.cpp/releases. Unzip
into `Local Storage\LLM Models\llama.cpp\`:
- `llama-b11533-bin-win-vulkan-x64.zip` into `vulkan\`. This is the default engine.
- Optionally, `llama-b11533-bin-win-cuda-12.4-x64.zip` plus `cudart-llama-bin-win-cuda-12.4-x64.zip` into `cuda\`.
  Use CUDA 12.4: CUDA 13 dropped GTX 10-series cards.
- Copy Microsoft's Visual C++ runtime DLLs (`msvcp140*.dll`, `vcruntime140*.dll`, `concrt140.dll`) into both folders,
  so they run without the VC++ Redistributable.
- A macOS build goes in `macos\`.

**4. The language models.** Each model gets one folder in `Local Storage\LLM Models\models\<name>\`, holding its
`.gguf` file and an optional `mmproj-*.gguf` (picture projector). The folder name is the model's name everywhere. Each
folder's `info.json` holds its title, licence and jobs; the clone doesn't restore those, but
`Local Storage\LLM Models\README.txt` documents the format and the code reads defaults without them. Download from
Hugging Face:

| Folder | File(s) | Download from | Job |
|---|---|---|---|
| `gemma3-1b` | `gemma-3-1b-it-Q4_K_M.gguf` | huggingface.co/ggml-org/gemma-3-1b-it-GGUF | Background life |
| `gemma3-4b` | `gemma-3-4b-it-Q4_K_M.gguf`, `mmproj-model-f16.gguf` | huggingface.co/ggml-org/gemma-3-4b-it-GGUF | Pictures |
| `gemma4-12b` | `gemma-4-12B-it-Q4_0.gguf`, `mmproj-gemma-4-12B-it-Q8_0.gguf` | huggingface.co/ggml-org/gemma-4-12B-it-GGUF | ClaudeAI |
| `nemomix-unleashed-12b` | `NemoMix-Unleashed-12B-Q4_K_M.gguf` | huggingface.co/bartowski/NemoMix-Unleashed-12B-GGUF | Buddy conversations (ChatML, stop word `<\|im_end\|>`) |
| `mag-mell-12b` | `MN-12B-Mag-Mell-R1-Q4_K_M.gguf` | huggingface.co/bartowski/MN-12B-Mag-Mell-R1-GGUF | Alternative roleplay voice |
| `qwen25-coder-1.5b`, `-7b`, `-14b` | `Qwen2.5-Coder-<size>-Instruct-Q4_K_M.gguf` | huggingface.co/bartowski/Qwen2.5-Coder-<size>-Instruct-GGUF | Python Studio's AI Helper |
| `qwen3-4b-instruct` | `Qwen3-4B-Instruct-2507-Q4_K_M.gguf` | huggingface.co/unsloth/Qwen3-4B-Instruct-2507-GGUF | Small all-rounder |
| `qwen3-coder-30b-a3b` | `Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL.gguf` | huggingface.co/unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF | The code studios' default |
| `nomic-embed-text` | `nomic-embed-text-v1.5.Q8_0.gguf` | huggingface.co/nomic-ai/nomic-embed-text-v1.5-GGUF | Embeddings (memory search) |

`Local Storage\LLM Models\README.txt` gives sizes and SHA-256 checksums for the main ones. After downloading, the
computers' **Control Panel > AI Models** assigns jobs.

**5. Pictures and voice (optional, several GB).** Each program installs these itself, from inside the computers:
- **Image Creator:** Stable Diffusion 1.5 (huggingface.co/stable-diffusion-v1-5/stable-diffusion-v1-5) and SDXL
  (huggingface.co/stabilityai/stable-diffusion-xl-base-1.0), into `LLM Models\image-gen\models\sd15` and `sdxl`.
  Its Python packages are in `ClaudeApps\requirements-imagegen.txt`: torch 2.7.1 for CUDA 12.8, diffusers and
  transformers.
- **Copilot Voice:** faster-whisper `base.en` (huggingface.co/Systran/faster-whisper-base.en) for listening, and
  Piper voices (huggingface.co/rhasspy/piper-voices, 27 English voices) for speaking, into `LLM Models\voice\models`.
  Its Python packages are in `ClaudeApps\requirements-voice.txt`.

**6. Offline Wikipedia.** `wikipedia_en_100_2026-08.zim` from download.kiwix.org goes in `Local Storage\Kiwix\`.
Any `.zim` file there appears in Kiwix's library, up to 15 GB in all.

**7. Free media.**
- **Freedoom** (`FREEDOOM1.WAD`, `FREEDOOM2.WAD`, from freedoom.github.io) goes in `Local Storage\WADs`.
- **ambientCG textures** (CC0, ambientcg.com) go in `Local Storage\ambientCG - Textures`.
- **Dungeon Crawl Stone Soup tiles** (CC0) go in `Local Storage\Dungeon Crawl - Sprites`.

**8. Python Studio's own Python.** Python 3.12 lives at `Local Storage\Python Studio\python312`, with about 60
offline wheels in `wheels\`, ffmpeg in `ffmpeg\` and the offline docs in `docs\`. `Local Storage\README.txt` describes it.

**9. Development tools (only to work on the code).**
- **Node.js** runs Claude and Magic's tests (`node tests/run.js`). Delete the `package-lock.json` npm creates.
- **Playwright** runs its smoke tests.
- **Claude Code** does the building. Its memory for this project is kept on the PC, not the drive, at
  `C:\Users\<you>\.claude\projects\F--Claude-Timeline\memory\`. Copy that folder to the drive if you want it to travel.

### B. What only your backups can restore

None of this is on GitHub or the web. Keep copies on another drive.

- **`Local Storage\`, personal parts:**
  - `Furry Media Archive`, `TV and Movies`, `Camera Rolls`, `Misc Personal Image Folders`
  - `Personal Texts and Docs`, `Text Logs`, `Others Files Archived`, `Projects`, `Project Snapshots`
  - `SecondLife`, `SecondLife Details`, `Second Life Export`, `Sticker Packs`, `Created Files`
  - `Emulation` (your ROMs) and your commercial WADs (Doom, Doom II, Heretic, Hexen, Plutonia, Doom 64, Wolfenstein 3D)
  - `Lemmings` and `casualties unknown` (the games' media), the sprite folders, `SMB Clock`, `Rover`
  - `Windows 11 media` and `Windows Screen saver`
  - `Bsky-Kithy`, which can be re-synced from kithy.bsky.social by the Bluesky watcher
- **The selfmodel's private data:** `LLM Models\selfmodel` holds your chat-log training data and the model trained
  from it. Keep it private.
- **Things the Timeline's own BACKUP button saves** (into `Local Storage\Claude Timeline Backups` by default; another
  drive is safer):
  - game saves (`ClaudeGames\Saves`)
  - each computer's `data\`
  - `Profile\`
  - Kithylin AI's chats (`ClaudeApps\kithylinai\Data`)
  - Soul and Song's Companions (`Local Storage\Projects\AI LLM Txt Files\Companions`)
  - optionally Kithylin's models (`ClaudeApps\kithylinai\Models`, about 2.5 GB) and the training results

Restore a backup from the launcher's **BACKUP** button. Paths inside are relative to the Timeline, so a backup
restores onto any copy on any drive.

## 13. Where to put things

Local Storage folders are found by **how their names begin**. "Furry Media Archive (2001)" works as well as
"Furry Media Archive", and "Emulation Archive" as well as "Emulation". `WADs` is the exception: it must be named
exactly that. The archive is never written to; caches and positions live in each computer's `data\`.

**TV, movies and commercials (ClaudeTV):** these go under `Local Storage\TV and Movies\`, or anywhere in Local Storage
under folders named like this:
- **Movies:** a folder whose name begins `Movies`. Loose video files in it are films; a year in the name, such as
  `Aliens[1986]...`, is read. A `Movies...` folder can also hold whole series and commercials, as
  `Movies and TV part 2` does.
- **TV series:** a folder whose name begins `TV Series`, with one subfolder per show
  (`TV Series\The Ren and Stimpy Show Seasons 1-5\...`). Name episodes with `S01E02`; `S01E01-02` is a double. An
  episode-guide `.txt` in a show's folder adds titles and descriptions.
- **Commercials:** any folder with `Commercials` in its name. They only air between programs. A brand's own folder,
  such as `Commercials Orangina`, gets its own channel. A year comes from a folder (`Commercials\2004\...`) or from
  the file name (`2000 Advil Migraine Commercial.mp4`).
- Extras under 3 minutes air as promos.
- Video types: `.avi .mp4 .mkv .mov .m4v .mpg .mpeg`. Release-group junk in file names is ignored.
- Running times are read from the files and cached. **Rescan** in ClaudeTV picks up new files.

**The Furry Media Archive:** `Local Storage\Furry Media Archive\` holds:
- `Comic Scans` (FurComix: CBR, CBZ or folders)
- `Portfolios` (FurFolio)
- `Authors and Stories` (FurStory)
- `Art CDs and DVDs` (Fur CD Viewer)
- `FurCon CDs` (Furry Con CD Viewer)
- `Video` (Furry Video Browser)
- `Misc Furry Images`
- `Website Rips\<site>`: each site in a folder named exactly `FurAffinity`, `HousePets`, `Hardblush`, `Jay Naylor`,
  `SexyFur`, `YiffStar` or `clubstripes`. Netscape's Furry Web serves them at their own addresses.

**Emulation:** `Local Storage\Emulation\<System> (Roms)`. The folder name must begin with the system's name:
- `NES`, `SNES`, `GB`, `GBC`, `GBA`, `GG`, `SMS`, `Gen` (Genesis), `N64` and `Apple II`
- The count is optional: `SNES (33 Roms)` works.
- File types are each system's usual ones: `.nes`, `.smc`/`.sfc`, `.gb`, `.gbc`, `.gba`, `.gen`, `.z64`/`.n64`,
  `.dsk`, and so on.

**WADs:** `Local Storage\WADs\` holds the Doom, Doom II, Heretic, Hexen, Wolfenstein 3D and Freedoom WADs, by their
usual names. Doom 64 needs `DOOM64.WAD` and its `DOOMSND.DLS`.

**Models:** see 12.A.4. **Kiwix:** `.zim` files in `Local Storage\Kiwix`. **Lemmings** and **Casualties: Unknown**
read their media from `Local Storage\Lemmings` and `Local Storage\casualties unknown`.

## 14. Checking it works

1. Run `Claude Timeline\Tests\Run All Tests.bat`, or `Python\python.exe Tests\run.py` from the Timeline folder. Add
   `--slow` to boot each computer. Every test should pass.
2. Start the launcher and click **SELF-CHECK**. It should say OK.
3. Boot EPOCH-2001 and open ClaudeAIM. A buddy who answers means the engine and models are working.

## 15. Keeping this file current

Regenerate it after big changes with:

```bash
cd "{drive_fwd}Claude Timeline/ClaudeApps"
../Python/python.exe -m manual.drive_guide
```

The inventory below is scanned fresh each time.

---

# Appendix A - The Timeline's own folders

Scanned {date}. Sizes are the files' own. `Local Storage` is in Appendix C.

{folders}

# Appendix B - Every program

{programs}

# Appendix C - Everything in Local Storage

{inventory}

# Appendix D - The developer's map (Manual chapter 13)

{under_the_hood}

# Appendix E - Claude Code's notes about this project

{notes}
"""


READ_ME_TEXT = r"""# Read Me - the Claude Timeline SSD

## Start here

1. Plug the SSD into a **USB 3** port (blue, or marked SS).
2. Open the drive, then the `Claude Timeline` folder, and double-click **Claude Timeline.exe**.
   On a Mac, double-click **Claude Timeline.command** instead.
3. In the launcher, click a computer, then **LOAD THIS COMPUTER**. **F11** switches full screen.
4. To stop, shut the computer down from its own Start menu. The launcher comes back; **POWER OFF** closes it.
5. Before unplugging, make sure no computer is running and Kithylin AI is closed, then eject the drive.

If it won't start, double-click `Claude Timeline.bat` instead to see the error, or click **SELF-CHECK** in the
launcher. On a newly installed PC, install the graphics card's driver first.

## The basics

- **Three computers** from three moments in time: **EPOCH-2001** (Windows XP), **SYSTEM-2011** (Windows 7) and
  **WORKSTATION-2025** (Windows 11). They share one archive, one set of games and one cast of about 260 characters.
- **Launcher buttons:** **APPS** opens Kithylin AI, Soul and Song and the code studios on their own; **BACKUP** saves
  your progress; **MANUAL** opens the full manual.
- **The talking** (the characters, ClaudeAI, Kithylin) runs on AI models stored in `Local Storage\LLM Models`, using
  the graphics card. Everything else works without them.
- **Backups** go to `Local Storage\Claude Timeline Backups`. Copy them to another drive now and then.
- **More help:** the `Manual` folder in `Claude Timeline`. To rebuild the drive, or to ask Claude about it, give
  Claude the file `Give this to Claude.MD`.

{drive_line}

## What's in Local Storage

`Claude Timeline\Local Storage` is the "external drive" (drive E:) inside every computer. Scanned {date}.

{storage}
"""

STORAGE_NOTES = {
    "TV and Movies": "Films, TV series and commercials that ClaudeTV turns into channels",
    "Camera Rolls": "Phone and camera photo backups, 2013 to 2026",
    "LLM Models": "The AI models, the llama.cpp engine, image and voice models, and Kithylin's training",
    "Furry Media Archive": "Comics, portfolios, stories, art CDs, con discs, videos and website rips",
    "Misc Personal Image Folders": "Personal picture collections",
    "Emulation": "Game ROMs for the NES, SNES, Game Boy family, Genesis, Master System, Game Gear, N64 and Apple II",
    "Others Files Archived": "Other people's files you've kept, shown in FurFolio",
    "SecondLife": "The Second Life viewer and OpenSim world (The Furry Hollow)",
    "Projects": "Programming projects, including Soul and Song's Companions",
    "Text Logs": "Your chat logs from 2004 to 2011 (Kithylin's training material)",
    "Personal Texts and Docs": "Personal writing and documents",
    "Bsky-Kithy": "Posts from kithy.bsky.social, kept in sync",
    "Python Studio": "Python 3.12, offline packages, ffmpeg and manuals for Copilot Python Studio",
    "ambientCG - Textures": "Free surface textures used by Claude and Magic",
    "Kiwix": "Offline Wikipedia",
    "Claude Timeline Backups": "Backups made by the launcher's BACKUP button",
    "Windows 11 media": "Wallpapers and sounds for WORKSTATION-2025",
    "WADs": "Doom, Doom II, Heretic, Hexen, Wolfenstein 3D and Freedoom",
    "Lemmings": "Lemmings' music and graphics, for Claudemmings",
    "Second Life Export": "Your own Second Life creations, exported",
    "Project Snapshots": "Screenshots of the project as it was built",
    "Windows Screen saver": "The Claude Entertainment System screen saver",
    "Sticker Packs": "Telegram sticker packs",
    "Dungeon Crawl - Sprites": "Dungeon Crawl tiles used by Claude and Magic",
    "SMB Clock": "Art and sounds for the Super Claude Bros clock",
    "Zelda2 - Sprites": "Sprites for the Zelda II clock screen saver",
    "Mertoid - Sprites": "Sprites for the Metroid clock screen saver",
    "SMB3 - Sprites": "Sprites for the Super Mario Bros. 3 clock screen saver",
    "LOZ Sprites": "Sprites for The Legend of Claude clock screen saver",
    "Rover": "Rover the search dog, EPOCH-2001's helper",
    "casualties unknown": "Casualties: Unknown's graphics, for Claudualties",
    "Farm - Sprites": "Crop sprites for Claude and Magic's farm",
    "SecondLife Details": "Two reference pictures from Second Life",
    "Created Files": "Where programs save what you make (fractals, terrain, Claude Life patterns)",
}


def _gb(size):
    """'291.5 GB', '401.9 MB', '572 KB' -> GB as text."""
    m = re.match(r"([\d.,]+)\s*(B|KB|MB|GB|TB)", size)
    if not m:
        return size
    n = float(m.group(1).replace(",", "")) * {"B": 1 / 1024 ** 3, "KB": 1 / 1024 ** 2, "MB": 1 / 1024, "GB": 1, "TB": 1024}[m.group(2)]
    return f"{n:,.1f} GB" if n >= 0.1 else ("< 0.1 GB" if n > 0 else "0 GB")


def read_me(inv_text, date):
    """The short guide for a person, with Local Storage's folders from the scan."""
    rows = ["| Folder | Size | What it is |", "|---|---:|---|"]
    for m in re.finditer(r"^\| \*\*(.+?)\*\* \| ([\d,]+) \| ([\d,]+) \| ([^|]+) \|", inv_text, re.M):
        name, size = m.group(1), m.group(4).strip()
        rows.append(f"| {name} | {_gb(size)} | {STORAGE_NOTES.get(name, '')} |")
    total = re.search(r"\*\*In all: ([\d,]+) files in [\d,]+ folders, ([\d.]+ \w+)\.\*\*", inv_text)
    if total:
        rows.append(f"| **In all** | **{_gb(total.group(2))}** | {total.group(1)} files |")
    import shutil
    try:
        du = shutil.disk_usage(TIMELINE)
        drive_line = (f"**The drive:** {du.total / 1024 ** 3:,.0f} GB, with {du.free / 1024 ** 3:,.0f} GB free "
                      f"({100 * du.used / du.total:.0f}% full).")
    except OSError:
        drive_line = ""
    return READ_ME_TEXT.format(date=date, storage="\n".join(rows), drive_line=drive_line)


def human(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.0f} {unit}" if unit in ("B", "KB") else f"{n:.1f} {unit}"
        n /= 1024


def walk(p):
    files = size = 0
    for root, dirs, names in os.walk(p):
        for f in names:
            try:
                size += os.path.getsize(os.path.join(root, f))
                files += 1
            except OSError:
                pass
    return files, size


def folders_table():
    rows = ["| Folder | Files | Size |", "|---|---:|---:|"]
    for d in sorted(TIMELINE.iterdir(), key=lambda p: p.name.lower()):
        if not d.is_dir() or d.name in ("Local Storage", "__pycache__") or d.name.startswith("."):
            continue
        n, s = walk(d)
        rows.append(f"| **{d.name}** | {n:,} | {human(s)} |")
        if d.name in ("ClaudeGames", "ClaudeApps", "ClaudeArchive", "ClaudeCore"):
            for sub in sorted(d.iterdir(), key=lambda p: p.name.lower()):
                if sub.is_dir() and sub.name != "__pycache__":
                    n2, s2 = walk(sub)
                    rows.append(f"| &nbsp;&nbsp;&nbsp;&nbsp;{sub.name} | {n2:,} | {human(s2)} |")
    residents = sorted(p.name for p in (TIMELINE / "Residents").iterdir() if p.is_dir())
    return "\n".join(rows) + f"\n\n**The residents ({len(residents)}):** " + ", ".join(residents) + "."


def _json(path):
    import json
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def main_furs():
    """A table of the main furs: name, species, era files and their summary."""
    rows = ["| Resident | Species | Eras | Who they are |", "|---|---|---|---|"]
    for d in sorted((TIMELINE / "Residents").iterdir(), key=lambda p: p.name.lower()):
        r = _json(d / "resident.json")
        if r.get("tier") != "main":
            continue
        eras = ", ".join(sorted(p.stem for p in (d / "eras").glob("*.json"))) if (d / "eras").is_dir() else ""
        species = (r.get("fursona") or {}).get("species", "")
        summary = (r.get("summary") or "").replace("|", "/").replace("\n", " ")
        rows.append(f"| **{r.get('fur_name') or d.name}** | {species} | {eras} | {summary} |")
    tiers = {}
    for d in (TIMELINE / "Residents").iterdir():
        t = _json(d / "resident.json").get("tier")
        if t:
            tiers[t] = tiers.get(t, 0) + 1
    count = ", ".join(f"{n} {t}" for t, n in sorted(tiers.items(), key=lambda kv: -kv[1]))
    return "\n".join(rows) + f"\n\nIn all: {count}."


def cam_details():
    """Claude and Magic's version, and its last few plans with their titles."""
    repo = TIMELINE / "ClaudeGames" / "Claude and Magic"
    version = (_json(repo / "package.json").get("version") or "?").removesuffix(".0")
    plans = []
    for p in repo.glob("UPGRADE_PLAN_*.md"):
        m = re.search(r"_(\d+)\.md$", p.name)
        if m:
            first = p.read_text(encoding="utf-8").splitlines()[0].lstrip("# ").strip()
            plans.append((int(m.group(1)), first))
    lines = [f"- {title}" for _, title in sorted(plans)[-8:]]
    return version, "\n".join(lines) or "- (the repo isn't here)"


def manual_list():
    """The Manual's contents, from its index."""
    text = (TIMELINE / "Manual" / "index.md").read_text(encoding="utf-8")
    m = re.search(r"## Contents\n(.*?)\n## ", text, re.S)
    body = m.group(1).strip() if m else ""
    body = re.sub(r"\[([^\]]+)\]\((\d\d[-\w]*\.md)\)", r"**\1** (`Manual\\\2`)", body)
    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", body)


def notes():
    """Claude Code's memory for this project on this PC, if there is one."""
    projects = Path.home() / ".claude" / "projects"
    slug = re.sub(r"[^A-Za-z0-9]", "-", str(TIMELINE))          # Claude Code names a project's folder after its path
    folders = [projects / slug / "memory"] if (projects / slug / "memory").is_dir() else sorted(
        projects.glob("*Claude-Timeline/memory"), key=lambda p: p.stat().st_mtime, reverse=True) if projects.is_dir() else []
    if not folders:
        return "Not found on this PC when this file was made."
    out = [f"Copied from `{folders[0]}`. Each note is something Claude was told or learned while building the Timeline."]
    for p in sorted(folders[0].glob("*.md")):
        if p.name == "MEMORY.md":
            continue
        text = p.read_text(encoding="utf-8")
        head, _, body = text.partition("\n---\n") if text.startswith("---") else ("", "", text)
        name = re.search(r"^name:\s*(.+)$", head, re.M)
        desc = re.search(r"^description:\s*(.+)$", head, re.M)
        out.append(f"### {name.group(1).strip() if name else p.stem}\n\n" + (f"*{desc.group(1).strip()}*\n\n" if desc else "")
                   + re.sub(r"^(#+) ", r"\1### ", body.strip(), flags=re.M))
    return "\n\n".join(out)


def chapter(path, drop_title=True):
    text = path.read_text(encoding="utf-8")
    if drop_title:
        text = re.sub(r"\A# [^\n]*\n", "", text)
    return re.sub(r"^(#+) ", lambda m: "#" + m.group(1) + " ", text, flags=re.M).strip()   # (one level down)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args(argv)
    from manual import inventory
    with tempfile.TemporaryDirectory() as tmp:
        inv = Path(tmp) / "inventory.md"
        inventory.main(["--out", str(inv)])
        inv_text = chapter(inv)
    programs = chapter(TIMELINE / "Manual" / "15-programs.md")
    drive = TIMELINE.anchor or str(TIMELINE.parent)
    cam_version, cam_plans = cam_details()
    text = GUIDE.format(date=time.strftime("%d %B %Y"), drive=drive, drive_fwd=drive.replace("\\", "/"), folders=folders_table(), programs=programs,
                        inventory=inv_text, main_furs=main_furs(), cam_version=cam_version, cam_plans=cam_plans,
                        manual=manual_list(), under_the_hood=chapter(TIMELINE / "Manual" / "13-under-the-hood.md"),
                        notes=notes())
    out = Path(args.out)
    out.write_text(text, encoding="utf-8")
    print(f"{len(text.splitlines()):,} lines -> {out}")
    short = read_me(inv_text, time.strftime("%d %B %Y"))
    readme = out.parent / READ_ME.name
    readme.write_text(short, encoding="utf-8")
    print(f"{len(short.splitlines()):,} lines -> {readme}")


if __name__ == "__main__":
    main()
