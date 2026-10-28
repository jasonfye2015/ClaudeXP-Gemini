# 1. What's in the box

## Three computers, one Timeline

| Computer | Folder | What it is | Snapshot |
|---|---|---|---|
| **EPOCH-2001** | `ClaudeXP` | Windows XP Home Edition on a Pentium III, 256 MB, dial-up | October 2001 |
| **SYSTEM-2011** | `Claude7` | Windows 7 Home Premium on a Core i5-2500K, 8 GB, Aero glass | October 2011 |
| **WORKSTATION-2025** | `Claude11` | Windows 11 Home on a Ryzen 7 7800X3D, 32 GB, Mica | October 2025 |

Each computer is a program of its own that fills the screen and behaves like that PC: the BIOS self test, the boot
screen, the logon, the desktop, the Start menu, the Control Panel, the shutdown. Each keeps its clock on the real
month, day and time, with the year fixed at its era's, so it's always October-ish 2001 on the XP machine while the
date keeps moving.

The project stops at 2025 on purpose and stays grounded in what really existed. The 2040 and 2101 pictures in the
launcher's art folder were a fun exercise, nothing more.

## How it started

It began as one question: what if an old, defunct instant messenger was emulated, with a language model playing the
contacts? That became ClaudeAIM, then a whole Windows XP around it, then the archive drive was pulled in, then games,
then two more computers from later eras, then over-the-air TV from saved shows, and finally your own chat logs, used
to train a model that talks like you. The first commit of the Timeline repository was 7 October 2026; by the end of
that month it held 147 programs on the XP machine alone.

## The folder map

```
Claude Timeline\
├── Claude Timeline.exe       start here on Windows (Claude Timeline.bat does the same with a console)
├── Claude Timeline.command   start here on a Mac
├── Manual\                   this manual
├── PLAN.md                   the design notes the project was built from
├── ClaudeLauncher\           the SYSTEC Multi-Boot Manager (the screen that picks a computer)
├── ClaudeXP\                 EPOCH-2001
├── Claude7\                  SYSTEM-2011
├── Claude11\                 WORKSTATION-2025
├── ClaudeCore\               the shared engine: the language-model router, the host every shared program talks
│                             to, backup, the self-check, the Furry Code tables, Mac fonts
├── ClaudeArchive\            the archive viewers: FurComix, FurFolio, stories, CD viewers, video, ClaudeTV, chat logs
├── ClaudeGames\              every game, the emulators, Doom; Saves\ is your progress (shared by all three)
├── ClaudeApps\               ClaudeAI, Kithylin AI, Soul and Song, the Copilot programs, Python Studio, QBasic
│                             Studio, the Claude Entertainment System .scr, selfmodel (training)
├── Residents\                the cast: one folder per character, with a file for each era they lived in
├── Tests\                    Run All Tests.bat: checks that everything still works (see under the hood)
├── Profile\                  who you are in the Timeline, your codes, the backup and self-check settings
├── Persona Styles\           frozen versions of how the residents are prompted (chosen at Load and Format)
├── Local Storage\            the "external drive": models, media, ROMs, WADs, TV, website rips, your text logs
├── Python\                   the portable Python everything runs on (Windows)
└── Python-mac\               the same for Apple silicon Macs
```

## What's shared and what's each computer's own

**Shared by all three** (change it once, it changes everywhere):

- The programs in `ClaudeArchive`, `ClaudeGames` and `ClaudeApps`. Only the window around them changes: XP's Luna,
  7's Aero, 11's Mica. The program inside is the same.
- Game saves and high scores, in `ClaudeGames\Saves`.
- The residents' timeless facts in `Residents\<Name>\resident.json`.
- Your identity in `Profile`.
- Everything in `Local Storage`.

**Each computer's own**, in its `data` folder (`ClaudeXP\data`, `Claude7\data`, `Claude11\data`):

- Your account and desktop on that computer, its settings and wallpaper.
- Its mail, chat histories, the residents' diaries and memories in that era, the generated web pages.
- Which language model does which job on that computer.

The period programs' data (the IRC regulars, the browsers' caches, the Fur Directory) lives in that computer's
`Program Files` folder and is regenerated from `Residents` when the computer starts.

**Load and Format** in the launcher wipes only that computer's `data`. Nothing shared is touched.

## Where your things live

| What | Where | In git? |
|---|---|---|
| Your name, fursona, codes | `Profile\profile.json` | no |
| Game progress | `ClaudeGames\Saves` | no |
| Each computer's mail, memories, settings | `ClaudeXP\data`, `Claude7\data`, `Claude11\data` | no |
| Kithylin AI chats and settings | `ClaudeApps\kithylinai\Data` | no |
| The models of you | `ClaudeApps\kithylinai\Models` | no |
| Kithylin's art | `ClaudeApps\kithylinai\Art` | no |
| The language models and their engine | `Local Storage\LLM Models` | no |
| The media archive, TV, ROMs, WADs | `Local Storage\...` | no |
| Your chat logs (the training material) | `Local Storage\Text Logs` | no |
| Training data, adapters, logs | `Local Storage\LLM Models\selfmodel` | no |
| The code, the art the computers draw with, the residents | everything else | yes |

"Not in git" means a fresh clone of the repository won't have it. The [backup](10-backup.md) covers the first five
rows and, if you tick them, the models and the training results. `Local Storage` is too big for that (about 746 GB:
TV and Movies 292, Camera Rolls 160, the models and their training files 98, the Furry Media Archive 87, your pictures
61; [chapter 14](14-local-storage.md) has the whole inventory); its safety is the cold copy on the 4 TB drive.

## The drive

The whole Timeline lives on a 1 TB external SSD formatted exFAT, so the same drive runs on a Windows PC and a Mac.
In October 2026 it held 916 GB with 17 GB free: a training run's base weights (24 GB) or a new TV season needs room
made first, and the self-check warns when space gets low.
exFAT with 256 KB clusters means every tiny file takes a quarter of a megabyte, which is why the Mac Python was
slimmed to 1.8 GB and why Python's compiled-code cache goes on the Mac's own disk.

Two things about the drive matter more than anything else in this manual:

1. **Use a USB 3 port.** On a USB 2 port the drive reads at about 25 MB/s and loading a language model takes minutes;
   the first boot looked hung for three minutes before this was found. On a proper port it reads at 370 MB/s.
2. **USB selective suspend must be off** on the PC (Power Options > Change plan settings > Change advanced power
   settings > USB settings). With it on, Windows put the drive to sleep during a long training run and the drive
   was "surprise removed" mid-write. Training now also tells Windows to stay awake while it runs, but the setting is
   the real fix.
