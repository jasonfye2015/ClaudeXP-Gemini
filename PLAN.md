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

## Phase 4 - the NPCs speak (llama.cpp)

- The vendors, Mother Wren and the townsfolk talk through llama-server (the Timeline's llama.cpp, a model from
  Local Storage/LLM Models), in character, knowing what Claude has done (his depth, his kills, his deaths).
- A canned line for each when no model is there; nothing waits on the model to play.

## Phase 5 - the forest, and the story

- The forest round Thornwick to walk in: paths, glades, a few of the forest's own creatures and places.
- Claude's back story, told through the floors, the guardians and the townsfolk - fitting Claude and Magic's canon.
