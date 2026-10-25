# 5. The archive and Local Storage

`Local Storage` is the Timeline's external drive: drive **E:** inside every computer. It holds everything that isn't
code and isn't yours-and-small: the language models, the furry media archive, the TV and movies, the ROMs and WADs,
the website rips, the offline Wikipedia, your own pictures and documents, and your chat logs. Git ignores all of it
except its README. About 205 GB.

The computers run fine with it empty; only the talking and the media go quiet.

## The layout

```
Local Storage\
├── LLM Models\                  the language models and their engine (see chapter 7)
│   └── selfmodel\               the training material, adapters and logs of the models of you (chapter 9)
├── Furry Media Archive\         what the archive viewers show:
│   ├── Comic Scans\                 FurComix Reader
│   ├── Portfolios\                  FurFolio Reader
│   ├── Authors and Stories\         FurStory Reader
│   ├── Art CDs and DVDs\            Fur CD Viewer
│   ├── FurCon CDs\                  Furry Con CD Viewer
│   ├── Video\                       Furry Video Browser
│   └── Website Rips\                the Furry Web's real sites (FurAffinity, HousePets, ...), served read-only
├── TV and Movies\               ClaudeTV's channels
├── Emulation\                   ROMs by system ("SNES (33 Roms)" and the like)
├── WADs\                        Doom, Doom II, Wolfenstein 3D, Heretic, Hexen (this name must be exact)
├── Lemmings\                    the original game's music and art, for Claudemmings
├── casualties unknown\          the original game's art, for Claudualties Unknown
├── Kiwix\                       .zim files: Wikipedia and friends, offline
├── SecondLife\                  the Furry Hollow: .NET, OpenSimulator, the viewer, the regions
├── Python Studio\               Copilot Python Studio's own Python 3.12, offline wheels, ffmpeg, docs
├── Text Logs\                   your chat logs, 1999 to now, from every client (and the Telegram export)
├── Camera Rolls\                your photos and videos by year and month (Camera Roll Archive)
├── Misc Personal Image Folders\ your pictures, including AI Kithy (Personal Image Gallery; Kithylin AI's art)
├── Personal Texts and Docs\     your texts (Personal Document Gallery)
├── Others Files Archived\       files people sent you, by name (Other's Files Archive Viewer)
├── Sticker Packs\               Telegram stickers (Sticker Manager gives each an emoji and a meaning)
└── Windows 11 media\            wallpapers and sounds for WORKSTATION-2025
```

Folders are found by how their names begin, so "Furry Media Archive (2001)" works as well as "Furry Media
Archive". `WADs` is the one exception: exactly that.

**Where it is** can be changed per computer from the launcher's **CONFIG** button, if the full archive is on another
drive than the code.

## The viewers

All of these are in **Furry Programs** on the desktop and in the Start menu, on every computer. They never write to
the archive: reading positions, favourites and thumbnail caches are each computer's own.

- **FurComix Reader** - comics: CBR, CBZ and folders of pages. (7-Zip, in `ClaudeArchive\tools`, opens the archives;
  XP's WinRAR and Alcohol 120% use it too.)
- **FurFolio Reader** - artists' portfolios.
- **FurStory Reader** - stories.
- **Fur CD Viewer** - art CDs and DVDs, including disc images.
- **Furry Con CD Viewer** - convention recap discs.
- **Furry Video Browser** - the video archive; files play in that era's own player.
- **Misc Furry Image Viewer** - the numbered albums of assorted pictures.
- **Personal Image Gallery**, **Personal Document Gallery**, **Camera Roll Archive**, **Other's Files Archive
  Viewer** - your own things.
- **Furry Chat Logs** - years of your chat logs by service, account and buddy, collated from every backup and client
  (you in blue, them in red). "Search all logs" finds a word anywhere. This is the same index the training uses.
- **Sticker Manager**, **FurCoder**, **The Fur Directory**, **Furry Log**, **Furry Proximity Locator** - see
  [the residents](04-residents.md).
- **Kiwix Wiki Reader** - offline Wikipedia from the `.zim` files in `Local Storage\Kiwix`; any `.zim` put there shows
  up in its Library.

Flash movies in the archive open in that era's Flash player (Macromedia Flash Player in 2001, Adobe's in 2011, the
Ruffle emulator in 2025).

## ClaudeTV

**ClaudeTV** (TV and Movies) is an over-the-air tuner card's viewer, the kind that came with a Hauppauge card. What's
on is decided by the clock: turning the TV on joins a programme partway through, and changing channel shows a burst
of snow while the tuner locks on. The channels are built from `TV and Movies`; channels 2, 7 and 11 are static, and a
channel whose file has gone missing shows static too. The **TV Guide** (its own program, and a gadget or widget on
the later computers) shows what's on.

| Key | What |
|---|---|
| Up/Down, PgUp/PgDn | Change channel |
| Digits | Enter a channel number |
| + / - | Volume |
| M | Mute |
| I | Info |
| G | Guide |
| C | Captions |
| S | Second audio (the RiffTrax movies have the riff track there) |
| Double-click | Full screen |

## Your chat logs

`Local Storage\Text Logs` is the raw material of both Furry Chat Logs and the models of you: Gaim/Pidgin, Digsby,
Trillian, mIRC and vIRC logs, Second Life chat, Skype, and the Telegram export in `telegram\result.json`. The index
(`Text Logs\_Index\chatlogs.sqlite`) is built from scratch with

```
cd ClaudeArchive
..\Python\python.exe -m chatlogs.index
```

and understands that the same conversation sits in several backups under different names for you. Rebuild it after
adding logs; see [training](09-training.md) for turning them into a model.
