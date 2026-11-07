# Claudenites 3-D - the plan

The outline: a Wolfenstein-style first-person game, much larger; Claude alone, a mage with a wand; Claude and Magic's
textures, meshes, monsters, dressings and unique rooms; wands built from parts; armour found as he levels; health,
mana and potions; loot straight into the pack; a forest town to come home to (between floors, or by Scroll of
Return); a roguelike, procedurally made, at least 100 floors with a new theme every 10; three save slots; three skill
trees that outlive death; death costs the run, not the man; vendors; NPCs who speak through llama.cpp; Python; its
own GitHub repo; in the launcher's Apps. The main goal: the guardian on floor 100. It's Claude's back story.

## Phase 1 - the foundation (v0.1) - done

- Python package (PySide6 + PyOpenGL 3.3 core + numpy); runs in the Timeline's computers and on its own (Apps).
- Claude and Magic's figures and plants imported as they are (tools/import_cm.py) and read with numpy; skinned on
  the card, with their clips (idle, walk, attack, cast, hit, die); its ambientCG stone.
- Floors made from a seed: rooms (plain, pillared, dais, pit, high hall, cross) and corridors, steps and lintels,
  torches; ten bands of ten floors (textures, tint, fog, light, monsters); a guardian's hall on every tenth floor,
  the stairs sealed until it falls.
- Thornwick: a clearing in the forest (Claude and Magic's trees), houses with roofs, four vendors, the Deep's mouth.
- The wand: bodies and parts (core/element, lens, splitter, focus, quickener, seeker, rebound, piercer); bolts with
  light; Fire burns, Frost slows, Storm chains, Venom stacks; the wand in his hand.
- Monsters: melee, ranged, swarm, brute, flyer; they notice, chase (a flow field), strike and cast.
- Loot straight into the pack; gold; potions; scrolls; levels; gear (six slots, four rarities, affixes).
- The three skill trees (Evocation, Warding, Arcana) with Mother Wren, kept through death; unlearning for gold.
- Death: home with everything, the run back to floor 1. The stairs: deeper, or home. Three save slots.
- HUD: life and mana orbs, the wands, potions, experience, the map (M for the big one), floating damage and loot,
  the guardian's bar. Sounds made at start.

## Phase 2 - Claude and Magic's Deep, dressed (v0.2) - done

- Its painted art exported from the running game (tools/export_cm_art.py into assets/cm): the dressings by band -
  pipe mouths that drip into puddles, barred grates, drain ports, webs, moss, roots, vines, chains, sconces, niches,
  banners, soot; beams, ribs, stalactites and hanging roots overhead; its stone cones; each band's floor things
  (glowcaps, crystals, braziers, crucibles, sarcophagi, skulls, candles) with their light; wall torches.
- Its sixty set pieces, laid into rooms made to their size by their letters, with their lines (said once, on the
  first step in), their chests and guards, their monsters, water, raised and sunken squares, trees and lights.
- Chests (F), guarded or not; wading water; floors of coin; things that stand in the way.

## Phase 2b - more of the Deep

- Doors, secret walls, traps (the Gauntlet's vents, the Pendulum Hall's blades), breakable barrels.
- The set pieces' own workings (the Hourglass, the Weighing Room, the Puzzle of Lamps...).
- Each band's own music (synthesized) and ambient sounds (drips, wind, the forge).

## Phase 3 - the deep end

- Guardians with phases and patterns (summons, rings of bolts, charges); the Unmade King on floor 100.
- Elites and champions (named, with an affix: fast, warded, splitting...), and a band's rarer monsters.
- More wand bodies and parts (chain, nova, beam, orbiting motes), legendary parts, item sets.

## Phase 4 - the NPCs speak (llama.cpp) (v0.3) - done

- The vendors and Mother Wren talk through the Timeline's llama.cpp engine (claudecore.ai.llm_server: llama-server
  from Local Storage/LLM Models; Qwen3 4B Instruct when it's there), in character (game/people.py), knowing what
  Claude has done (his deepest floor, the run, his falls, his kills, the guardians, his wand); greeting him, and
  answering what he types at their stalls. Warmed as the game starts; asked in a thread; never waited on.
- Their own lines when no model is there (or it's switched off in the menu).
- Later: townsfolk beyond the four, who talk about the forest and the story (phase 5).

## Phase 5 - the forest (v0.4) - done

- The wood round Thornwick (game/forest.py): the town 176 squares across, trails from the clearing's four ways to
  eight glades with their lines (the Mossy Pond, the Old Shrine, the Woodcutter's Camp with Rook - who talks - the
  Fairy Ring, the Hollow Oak, the Wolf Hollow, the Bandits' Camp, the Stream and its bridge), ~3400 trees you walk
  between, undergrowth; creatures at Claude's own strength that keep to the wood; falling there costs nothing.
- Also: the dead flip over; nothing in the Deep stands in a corridor or a narrow way (tests walk every floor at
  Claude's size); the trees drawn by chunks near him, 60 frames a second.

## v0.5 - breaking things, ClaudeRPG's music, the title - done

- Barrels, crates, racks, shelves, tables, benches, egg sacs, cocoons and fungus break under bolts (splinters,
  a sound, sometimes gold or a potion); where they stood is clear.
- ClaudeRPG's music engine and its worlds' styles in Python (engine/music.py), streamed through a QAudioSink
  (ui/audio.py), following the town, the forest, the band and a guardian's fight; music/sound options.
- The title (ui/title.py): a title card over Thornwick, then Play / Records / Options / Keys / Credits.

## v0.6 - Claude and Magic's sky and weather - done

- Its clock, seasons, daylight and moon; its weather as live events (its odds, ramps, day leaning, aurora,
  tornado), carried over into game/sky.py; its look (engine/atmosphere.py: sky colours by the hour, sun, moon in its
  phase, clouds, stars, aurora, rainbow, lightning, fog; snow and frost on the ground); the falling weather and the
  below (engine/weatherfx.py); its dial and Calendar (ui/dial.py); rain and wind heard, thunder after lightning.
- The weather in play, outdoors and in the first floors (its flood: floors 1-3, a day to drain).

## v0.7 - running, and floors twice the size - done

- Shift runs (x1.65), and a running jump goes higher (x1.3) and carries further.
- Floors twice the area (64 to 108 squares across), 16 to 36 rooms; rooms at their own heights along the tree that
  joins them, corridors relaxed between them in steps of a tenth; L, ring, split and stepped rooms; winding
  corridors; more loops; dead-end alcoves with caches; floors made again gentler, then level, should the heights
  ever cut anything off (a whole-floor walk at Claude's size decides).
- Pickups (gold, potions, scrolls, finds) lying about; two to five chests; more breakables.

## v0.8-v0.11 - item pictures, drops seen, 3-D chests, the pack and the look - done

## v0.12 - home: the cabin, the farm, food - done

- The cabin in Thornwick (levels.cabin, entered at its door): bed (sleep to six, full life/mana, the farm grows
  through the night), hearth (cooking), chest (the stash: items and food, kept through death).
- The farm (game/farm.py): 8-20 plots, watering (by hand, rain, the sprinkler), four growth stages over 1.5-5 days,
  harvests with seed back; the sign's panel; the Sprinkler, Farmhand (basket, replanting from the chest's seeds) and
  More plots. Crops drawn on the plots (LPC Crops).
- Food (game/food.py): 14 crops, meat/fish/mushroom/honey from monsters, 24 recipes of one to three things, buffs of
  1-5 real hours (three at once); the hearth's experiments and the cookbook. Seeds from monsters, chests, Hesper.
- The pack's tabs: Armor, Wands, Seeds, Raw, Cooked, Misc.

## v0.13 - the ground blends (Claude and Magic's polish) - done

- engine/groundmap.py: a texel a square (ground kind, cover, water, wear), and the level shader's ground(): noisy
  edge blends between grounds, anti-tiling patches, wear by traffic, the forest floor under the trees (moss, litter),
  muddy banks, dappled light, autumn leaves at the walls, mud after rain - as C&M's 76zzzzzzzzzz0-groundblend,
  26c-wear, 26d-forestfloor and 40-render's uGBlend. An option to turn it off.

## v0.14 - the Deep's detail, and rarity - done

- game/detail.py: corridor light map (L.amb, in every program's lighting), corridor torches, brighter torches;
  timber (corridor frames, skirting, beams as boxes); stains, wall streaks and grime, puddles with a sheen (the
  dungeon's float map, engine/groundmap.deep, and WORLD_FS's deep()); bones, empty bottles (7Soul1), vines; grates
  in the ceilings with light shafts (glow mode 7), a pool of light and motes.
- Five rarities for gear, wands and parts (data.RARITIES, WAND_POWER, WAND_HASTE, PART_POWER); old saves migrated
  (items.migrate); the colours and effects in the tiles, tooltips, HUD, drops, toasts and a Legendary banner.

## v0.15 - strange floors, locked doors, puzzles - done

- game/features.py, after a floor is made whole: specials (dream/hoard/den/drowned, about 1 in 5, seeded), coloured
  doors on one-way-in rooms with their keys reachable with every door shut (features.reach), the lever-sealed rune
  door, the brazier trial. Level.door_at/can_stand(doors=) - walkable_reach ignores doors. Game: ghosts (their own
  list: nothing touches them), keys, open_door, pull_lever, _trial, _light_brazier. Renderer: door slabs
  (levelmesh.door, tinted), runes, lever lights, pouring pipes, ghosts, the Dreaming's lights/tint/FOV; HUD keys,
  the trial's countdown, the Dreaming's colour wash.

## v0.16 - the Gauntlet, traps, secrets - done

- features: "rush" special (depth > 11): L.rush, L.arena, waves in world._gauntlet/_champion, the guardian flag
  carried through _kill; a Legendary chest. Traps (L.traps: spikes, darts, fire; world._traps; art by
  tools/make_art.py). Hidden rooms behind cracked walls (L.secret_walls; world._crack; L.mesh_version makes the
  renderer build the floor again). game/eggs.py: the secrets (see it, not the README).

## v0.17 - auto-play, and the endless Deep - done

- game/autoplay.py: Autopilot.drive (fight / puzzles at hand / Dijkstra over squares his body fits through - traps
  dear, doors shut without their keys - to pickups, chests, doors, levers, the trial, cracked walls, monsters, the
  unseen, the stairs; stuck: jump, strafe, shoot ahead, give the goal up a while) and housekeeping (shopping, the
  best wands by greedy dps, gear by weighted stats, skills, farm, cooking and eating, selling, potions). The HUD's
  button over the life orb, and P. Endless: data.band_of cycles; world.endless() once the hundredth floor's
  guardian falls (stats["won"]).

## v0.18-v0.19 - auto-play's speed, hotkeys and stats - done

- F9/P on-off, F10 speed (x1-x8: the game stepped several times a frame), the mouse let go while it plays; F11 the
  stats panel (autoplay.Tally: the session's count and player.stats["autoplay"], read from the game's events after
  every step).

## Phase 6 - the story

- Claude becomes the Lich King later (Claude and Magic's canon): the floors, the guardians, Mother Wren and the
  Unmade King tell how it begins - what he finds at the bottom, and what it costs him.
