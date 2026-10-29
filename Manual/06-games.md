# 6. Games

Every game is the same on all three computers; only the window around it changes. They're in the **Games** folder on
the desktop and under **Games** in the Start menu. Progress and high scores go to `ClaudeGames\Saves`, shared by all
three, so a city built on the XP machine is there on the Windows 11 one.

## The Claude games

| Game | What it is |
|---|---|
| **Claudemmings** | Lemmings: the twelve Fun levels with the original music (from `Local Storage\Lemmings`). Levels give 15 of the skill they're named for plus 3 of each other, because the maps can't always tell decoration from ground |
| **Claudualties Unknown** | Casualties: Unknown: descend the caves for the cargo and keep the Expie alive (art from `Local Storage\casualties unknown`, sound synthesised) |
| **Claudeggle** | Peggle: aim, shoot, clear the orange pegs |
| **ClaudeCraft** | Minecraft: build anything, block by block |
| **ClaudeQuest** | The pack is calling |
| **ClaudeRPG** | A cosy, endless dungeon adventure |
| **Claudeablo** | Diablo: fifty levels down, the Lord of Terror waits |
| **Claude and Magic** | Twenty floors down, the Lich King waits: a first-person dungeon crawler for a party of four, in 3D. Name your four, choose their callings from eight (Knight, Paladin, Rogue, Ranger, Cleric, Mage, Druid, Bard), roll their stats and set their rows, with advice on the party's balance. Rooms and corridors with doors and keys, secret walls, pits and trapdoors, teleporters and spinners, fountains, altars, levers and gates, carvings that tell the story, torches that burn down, stairs back up to floors kept as you left them, monsters that come for you and leave ailments behind (cured at the camp's temple), and a boon to choose at every level. One HTML file (`ClaudeGames\claudemagic\game`) that plays in a browser too; a seed on the title screen lays out the same dungeon again. On the desktop of all three computers and in the launcher's APPS |
| **ClaudeCity** | SimCity: from dust to Megalopolis |
| **Scorched Claude** | Scorched Earth: tanks, nukes and very angry physics |
| **Claudejeweled** | Bejeweled: swap gems, line up three |
| **Claudeanoid** | Arkanoid: break all the blocks, 40 rounds |
| **Claude Shelter** | Fallout Shelter: an underground vault, dwellers, raiders, the wasteland |
| **Claudeout 4** | Fallout 4: out of Vault 111 and into the old neighbourhood, in 3D |
| **ClaudePit** | A slot machine, a debt, and a trapdoor |
| **Claudeatro** | Balatro: poker hands, chips times mult, jokers that break the rules |
| **Claudescryption** | Inscryption: Leshy deals, in a cabin in the woods |
| **Claudeita** | Noita: wands, spells and a world that falls apart |
| **Claude Life** | Conway's Game of Life |
| **Claude Incremental** | From answering questions to converting the galaxy |
| **Claude Aquarium** | A living fish tank: windowed, full screen or a desktop pet |
| **Claude Fractal Generator** | Mandelbrot, Julia and friends, Fractint style |
| **Claude Terrain Generator** | Fractal landscapes, VistaPro style |
| **Claudecadia** | Furcadia: a furry graphical chat world, with the residents in it |

Real-time games run on a precise timer with catch-up, so they run at speed even when the computer's window is busy.

## Emulation

**Games > Emulation** has the console emulators, one window driven by a libretro core:

| System | Core |
|---|---|
| NES | FCEUmm |
| SNES | Snes9x |
| Game Boy / Game Boy Color | Gambatte |
| Game Boy Advance | mGBA |
| Genesis (and 32X) | PicoDrive |
| Master System, Game Gear | Genesis Plus GX, Gearsystem |
| N64 | Mupen64Plus-Next (software renderer, so it needs no 3D set-up) |
| Apple ][ | AppleWin |

ROMs come from the matching folder under `Local Storage\Emulation` (e.g. `SNES (33 Roms)`). Picking one runs it at
2x with sound. Battery saves and save states (ten slots) are each computer's own.

| Key | What |
|---|---|
| Arrows | D-pad |
| Enter | Start |
| Space or Shift | Select |
| F5 / F7 | Save / load state |
| 0-9 | Pick a slot |
| P or Pause | Pause |
| F1 | Reset |
| Esc | Back to the game list |

The face buttons differ per system and are shown on each system's page.

**Doom, Doom II and Wolfenstein 3D** run on the PrBoom core; **Heretic** and **Hexen** on Chocolate Doom. All of them
find their WADs in `Local Storage\WADs`.

## Each era's own Windows games

- **2001:** Solitaire, Spider Solitaire, FreeCell, Hearts, Minesweeper, Pinball, the Internet games (Backgammon,
  Checkers, Hearts, Reversi, Spades), and the Entertainment Pack: Rodent's Revenge, SkiFree, JezzBall, Taipei, Golf,
  TriPeaks, Blockfall. In **Games > Windows Games**.
- **2011:** the same, plus Chess Titans.
- **2025:** the Microsoft Solitaire Collection (Solitaire, Spider, FreeCell, TriPeaks, Minesweeper), the classic
  games, 3D Pinball Space Cadet. The Internet games are gone.

## The screen savers

**Display Properties > Screen Saver** (Control Panel > Personalization on 7 and 11) has each era's classics - 3D
Pipes, Mystify, Starfield, Flying Toasters, Marquee, My Pictures Slideshow and the rest - and five NES clock games
built from the sprite sheets in `Local Storage`. Each plays itself, and its clock tells the real time:

| Screen saver | Sprites from |
|---|---|
| **Super Claude Bros** (Settings: character and world) | `SMB Clock` |
| **Super Claude Bros. 3** | `SMB3 - Sprites` |
| **The Legend of Claude** | `LOZ Sprites` |
| **Zelda II: The Adventure of Claude** | `Zelda2 - Sprites` |
| **Metroid: Claude's Mission** | `Mertoid - Sprites` |

The **Claude Entertainment System**, the default on all three computers (a format keeps it), plays them all in turn,
with a title card between cartridges. **Settings** picks which games are in, how long each plays (5 minutes by
default) and whether they go in order or shuffled. A game whose sprite sheets aren't there is skipped.

It's also a real Windows screen saver: `Local Storage\Windows Screen saver\Claude Entertainment System.scr` (one
38 MB file with the sprites inside). Right-click it and choose **Install**. It's built from the same games by
`ClaudeApps\cesscr\build_scr.bat`, so after changing a game, build it again; its README says how.

## Adding a game

A game is a Python package in `ClaudeGames` that asks the computer for a window through the host
(`host.window(desktop, title, body, icon, size)`) and never imports an OS's own modules. Register it once in
ClaudeXP's program registry with `group="Games"` and it appears on all three computers, in the Start menu and in the
desktop Games folder, in each era's window style. See [under the hood](13-under-the-hood.md). New games don't get a
loose desktop icon; the Games folder is enough.
