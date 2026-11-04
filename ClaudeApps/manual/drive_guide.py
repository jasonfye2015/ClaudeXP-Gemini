"""The drive's guide: writes Claude.MD at the top of the SSD (beside the Claude Timeline folder) - what the drive is,
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
OUT = TIMELINE.parent / "Claude.MD"

GUIDE = r"""# Claude.MD - the Claude Timeline SSD

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
| `Claude.MD` | This file, written by `python -m manual.drive_guide` |
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

## 4. What lives where

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

## 5. Rebuilding the drive from nothing

Work in this order. Part A comes from GitHub and the web. Part B only exists in your backups.

### A. What can be downloaded again

**1. The code.** Both repositories are private on GitHub under `jasonfye2015`:
- `ClaudeXP-Gemini` - the whole Timeline. Branch `ClaudXP+Gemini`, mirrored to `main`. Clone it as
  `{drive}Claude Timeline`.
- `claude-and-magic` - Claude and Magic's source. Clone it as `Claude Timeline\ClaudeGames\Claude and Magic`. The
  Timeline already carries the built game in `ClaudeGames\claudemagic` (a git subtree, remote `magic`).

You'll need git and the GitHub CLI (`gh auth login`). This drive doesn't record file owners, so mark both folders safe:

```bash
git config --global --add safe.directory "F:/Claude Timeline"
git config --global --add safe.directory "F:/Claude Timeline/ClaudeGames/Claude and Magic"
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

## 6. Where to put things

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

**Models:** see 5.A.4. **Kiwix:** `.zim` files in `Local Storage\Kiwix`. **Lemmings** and **Casualties: Unknown**
read their media from `Local Storage\Lemmings` and `Local Storage\casualties unknown`.

## 7. Checking it works

1. Run `Claude Timeline\Tests\Run All Tests.bat`, or `Python\python.exe Tests\run.py` from the Timeline folder. Add
   `--slow` to boot each computer. Every test should pass.
2. Start the launcher and click **SELF-CHECK**. It should say OK.
3. Boot EPOCH-2001 and open ClaudeAIM. A buddy who answers means the engine and models are working.

## 8. Keeping this file current

Regenerate it after big changes with:

```bash
cd "F:/Claude Timeline/ClaudeApps"
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
"""


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
    text = GUIDE.format(date=time.strftime("%d %B %Y"), drive=drive, folders=folders_table(), programs=programs,
                        inventory=inv_text)
    out = Path(args.out)
    out.write_text(text, encoding="utf-8")
    print(f"{len(text.splitlines()):,} lines -> {out}")


if __name__ == "__main__":
    main()
