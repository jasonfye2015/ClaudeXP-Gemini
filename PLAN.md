# Claude Timeline - plan

Three computers from three moments in time, sharing one archive and one cast of characters.

| Computer | Folder | Era | Snapshot |
|---|---|---|---|
| EPOCH-2001 | `ClaudeXP/` | Windows XP Home | October 2001 |
| SYSTEM-2011 | `Claude7/` | Windows 7 Home Premium | October 2011 |
| WORKSTATION-2025 | `Claude11/` | Windows 11 Home | October 2025 |

The project stops at 2025 and stays grounded in reality. The 2040 and 2101 concepts in the launcher art were a fun
exercise only. Each computer's clock runs on the real local month, day and time, with the year fixed at its era's.

## Why it exists (in order)

1. **Presenting the archive.** The furry media archive - comics, portfolios, stories, art CDs, convention discs,
   videos, TV and movies, website rips - shown through tools that work the same in every era.
2. **A living community around it.** The residents, the messengers and chat, e-mail and the social web of each era.

## Layout

```
Claude Timeline/
├── PLAN.md
├── ClaudeLauncher/   SYSTEC Multi-Boot Manager (Images/ holds the art and spec sheets)
├── ClaudeCore/       shared engine: llama.cpp engine and request broker, life simulation, the local web server,
│                     resident loader, shared helpers
├── ClaudeArchive/    the archive tools: FurComix, FurFolio, story reader, Fur CD Viewer, FurCon,
│                     Furry Video Browser, ClaudeTV and the TV Guide
├── ClaudeGames/      the user's games, emulators, Doom-style games, Claudecadia; Saves/ is shared by every era
├── ClaudeApps/       ClaudeAI, CopilotAI, Copilot Voice, Image Creator, Python Studio
├── Residents/        the cast (see below)
├── Profile/          the user's identity across the eras
├── Local Storage/    the shared "external drive": LLM Models, media, ROMs, WADs, Kiwix, website rips
├── Python/           one portable Python runtime for everything
├── ClaudeXP/         EPOCH-2001
├── Claude7/          SYSTEM-2011
└── Claude11/         WORKSTATION-2025
```

- **One git repository** at `Claude Timeline/`. ClaudeXP's history comes along under `ClaudeXP/`.
- **Shared programs, era windows.** Shared programs come from ClaudeArchive, ClaudeGames and ClaudeApps. Each OS
  wraps them in its own window style (XP Luna, 7 Aero glass, 11 Mica) and lists them its own way. The program
  inside is the same everywhere.
- **What stays with each OS:**
  - Windows' own games: XP Solitaire and Pinball; 7 Chess Titans; 11 Solitaire Collection.
  - Clippy, on XP only.
  - Each era's shell and its period programs.
- **Each computer has its own `data/`:** user account settings, mail, memories, diaries, the generated web,
  and resident activity. Game saves are the exception: shared, in `ClaudeGames/Saves/`.

## The launcher (SYSTEC Multi-Boot Manager)

From the user's mock-up (`ClaudeLauncher/Images/System_Selection_*.jpg`):
- One card per computer, showing a picture, the specs and the OS.
- On each card: **Load This Computer**, **Load and Format** and **Config**.
- Along the bottom: Help, Reboot and Power Off, plus the real date and time.
- Spec text is drawn live from the spec sheets, so the images are just art. The 2011 card says 4 GB of RAM, but the
  sheet says 8 GB.
- **Load and Format** wipes only that computer's `data/`. The Timeline identity and shared saves survive.
- **Config** holds:
  - Where Local Storage is: the full archive on the USB SSD, or the trimmed development copy.
  - Display options.
- Mobile devices (the real phones and tablets of each era) are a maybe-later.

## The user's identity (Profile/)

- Chosen once, in the launcher: name, fursona, account picture (optionally per era).
- Each computer's Setup and Format take the identity from the launcher, and don't ask for account or fursona details.
- The user's shared history with residents lives in the residents' dated history (below), so it spans the eras too.

## Residents

The same cast in every era, with the same three tiers:
- **Main furs:** IM contacts, with icons, webpages and pictures.
- **Support furs:** the IRC and MUCK regulars who chat.
- **Background furs:** the crowd.

```
Residents/<Name>/
├── resident.json   timeless: fur name, tier, fursona, core personality, mannerisms, how they met the user,
│                   birth date, default friends/relationships
├── eras/2001.json  that era: services and accounts (screen names, icon, profile, away message, e-mail,
│                   webpages), job, location, situation, schedule, time zone, era persona text, tier override
├── eras/2011.json
├── eras/2025.json
└── media/2001/ 2011/ 2025/   icons, photos, art, files they can share (newest folder up to the era)
```

- **Birth dates:** assigned at random once, so every resident is an adult (18-36) in 2001. Their age follows the era:
  a 26-year-old in 2001 is 36 in 2011 and 50 in 2025. Missing details get drafted, consistent with the existing
  persona, for the user to review.
- **No era file means not around then.** For example, they joined the fandom later, or left it.
- **Dated history:**
  ```json
  "history": [
    {"from": 1999, "text": "Met the user on a furry forum"},
    {"from": 2001, "to": 2025, "text": "Met up with the user at conventions several times"},
    {"from": 2017, "to": 2023, "text": "Was in a relationship with the user"}
  ]
  ```
  The loader shows only what has started by the era's year, as it stood then: something ongoing has no end date,
  and something finished is in the past tense. It never reads future era files, so nothing can leak.
- **Past eras appear as "used to":** "used to be on AIM as ...". How long they've known the user is worked out from
  the dates. No logs carry between eras; each era's memories are its own.
- **Memory and the year loop:**
  - Every log, diary note and e-mail stores the real timestamp underneath.
  - The model sees relative dates ("3 days ago").
  - A rolling window of about 11 months is kept, with older entries trimmed or condensed, so a month never repeats.

## Services by era

A service exists in an era only if it really existed in October of that year. XP keeps its current lineup,
anachronisms (Skype, Kik, Copilot) and all.

| Service | Real dates | 2001 | 2011 | 2025 |
|---|---|:-:|:-:|:-:|
| AIM | 1997 - Dec 2017 | yes | yes | - |
| MSN / Windows Live Messenger | 1999 - 2013 | yes | yes | - |
| Yahoo! Messenger | 1998 - 2018 | yes | yes | - |
| ICQ | 1996 - Jun 2024 | yes | yes | - |
| Trillian | 2000 - | yes | yes | yes |
| Skype | 2003 - May 2025 | (XP's) | yes | retired (part of history) |
| Kik | 2010 - | (XP's) | yes | yes |
| IRC (FurNet), MUCK | 1990s - | yes | yes | yes |
| LiveJournal | 1999 - | yes | yes | yes |
| Claudecadia (Furcadia) | 1996 - | yes | yes | yes |
| Facebook, Twitter, YouTube, Steam | 2004 - 2006 | - | yes | yes |
| Discord, Telegram, Bluesky, Teams | 2013 - 2023 | - | - | yes |

## The web

- **Website rips are archive.** Every rip is available, read-only, in every era.
- **Era-local:**
  - What the residents add (favourites, shouts, journals, homepages).
  - Model-written pages.
  - The generated social sites (LiveJournal / Facebook / Discord...).

  These stay in that era's `data/`, so 2001 never sees 2025 posts.

## Storage

- ClaudeXP measured about 205 GB: TV and Movies 75, Furry Media Archive 64, LLM Models 60, Emulation 4.3, code and
  assets about 1.4.
- **The full archive** lives on the 1 TB USB SSD, and the cold backup is on the 4 TB drive.
- **The working drive** keeps a trimmed sample of the media for development, plus all the models in use.
- 14.7 GB of models aren't assigned to any role (mag-mell-12b, qwen25-coder-7b, qwen3-4b-instruct,
  qwen25-coder-1.5b). Check the code before dropping them.

## Build order

1. **Restructure.**
   - Verify the cold backup.
   - Move ClaudeXP into `ClaudeXP/` and Local Storage up a level (same drive, so these are renames).
   - Make `Claude Timeline` the git repo.
   - Recreate the venv, then the portable Python.
   - Update Thonny's interpreter path.
   - ClaudeXP finds the shared Local Storage.
2. **The SYSTEC launcher.**
   - EPOCH-2001 working; the other cards "not installed yet".
   - Profile.
   - Config (with the Local Storage location).
   - XP Setup/Format takes the account from the launcher.
3. **Residents.** The migration script from ClaudeXP's scattered files, birth dates, dated history, drafted details.
4. **Shared code.** ClaudeCore, then ClaudeArchive, ClaudeGames and ClaudeApps, pulled out of ClaudeXP one piece at
   a time, with XP working at every step.
5. **Claude7.**
   - First milestone: the shell plus the whole archive, games and apps. Done 2026-10-22: BIOS, Starting Windows,
     the logon screen, the Aero desktop, Explorer, IE9 and Firefox, Sticky Notes, Snipping Tool, gadgets, Control
     Panel, Help, Setup, and every XP program through claude7/xpcompat.py (see Claude7/README.md).
   - Then the 2011 community: Windows Live Messenger 2011, Skype 5, Yahoo! Messenger 11, Windows Live Hotmail and
     Facebook on the Furry Web (claude7/sites/facebook.py) are in (2026-10-22). The residents' 2011 lives were
     drafted from 2001 by ClaudeCore/tools/draft_2011_eras.py; the 34 main residents have hand-written 2011 lives
     (drafts/main_2011_2026-10-22.json), the rest each carry their own 2011 paragraph (--vary). Chess Titans is in.
6. **Claude11**, the same way.
   - First milestone, started 2026-10-22: the shell and every program. The ASUS UEFI splash (the user's picture)
     with Windows 11's spinning dots, the UEFI BIOS Utility (DEL/F2) and the recovery environment (F8), the lock
     screen and sign-in, the Mica desktop with Snap layouts, the centered taskbar with Quick Settings, the
     notification center and the Widgets board, the Start menu, Settings, File Explorer's 2025 face, Microsoft
     Edge and Firefox 144, Outlook, Tips, and every XP program that still existed in 2025 through
     claude11/xpcompat.py (AIM, MSN, Yahoo!, ICQ and Skype are gone). The wallpapers, lock pictures and sounds
     come from the real PC's Windows 11 (see Claude11/README.md). 144 of 145 programs launch offscreen.
   - The residents' 2025 lives (2026-10-22): ClaudeCore/tools/draft_2025_eras.py drafts eras/2025.json from 2011
     for all 258 (ages +14, Skype gone, Telegram/Discord/Bluesky handles for the mains, a 2025 paragraph each with
     --vary); the 34 main residents have hand-written 2025 lives (drafts/main_2025_2026-10-22.json: retirements,
     marriages, children, businesses, the pandemic years). 2001 and 2011 see none of it.
   - Next: the 2025 community faces (Bluesky and Facebook's 2025 look on the Furry Web, Discord and Telegram),
     the 2025 TV channels. Then maybe mobile devices.

## The Furry Hollow (Second Life on this PC, started 2026-10-22)

- `ClaudeGames/opensim_world`, in every era's Social Programs as "Furry Hollow". Nothing is installed on Windows:
  everything lives in `Local Storage/SecondLife` (gitignored).
  - `dotnet/`: a portable .NET 8 runtime. `opensim/`: OpenSimulator 0.9.3.0 as a standalone grid on
    127.0.0.1:9000 with one region, the Furry Hollow, owned by the user's avatar (named from Profile/).
  - `viewer/coolvl/`: the Cool VL Viewer, unpacked from its InstallJammer installer by `opensim_world/unjammer.py`.
    A Firestorm unpacked into `viewer/` is preferred if the user adds one. Alchemy can't be used: its Windows builds
    are compiled with Havok, which removes every grid but Second Life's.
- The Hollow Keeper (`keeper.lsl`, loaded from an OAR that `oar.py` writes) creates the main residents as NPCs,
  passes local chat to the bridge (`bridge.py`, a small web server on 127.0.0.1:9180 inside the computer that
  launched the world) and says the replies, which the language model writes from each resident's own persona for
  that era.
- Four regions in a 2x2 block (2026-10-22): the Furry Hollow, Whisker Falls, Tailwind Beach and Lantern Market,
  each with its own Keeper and its own crowd of five residents, who appear the first time the user arrives there.
- Furnished once from Linda Kellie's CC0 collection on Zadaroo (`content.py`): Mountain Retreat, Lake House, Tiki
  Summer and the Freebie Mall as the four regions' builds, and the furry avatars, full avatars, hair, animals,
  animations, furniture and houses packs in the avatar's inventory.
- Next: dressing each resident in their own furry avatar (saved appearance notecards), IMs.
