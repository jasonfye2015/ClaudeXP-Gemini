# The thirteenth big update: Claudeita's cave

The Timeline's Claudeita (ClaudeGames/claudeita: a world of falling sand, flowing liquids and fire, five biomes and
five bosses, with wands built from spells) brought whole into Claude and Magic, as the Mage Tower and Leshy's table
were: a place in the Wood, a portal in the yard, one hero, and a game of its own inside.

The rules asked for:
- A cave mouth in the Wood; the party picks one caster to go in (Mage, Necromancer, Druid, Cleric, Bard, Artificer).
- As in Claudeita, a default wand is given (the Apprentice's Wand, and the Miner's Rod for digging).
- A portal to the cave's front from the portal yard in town (the second plinth lights).
- The game inside is Claudeita's: side-on, real time, the world destructible, wands and spells.
- Death: the hero is back with the party at the cave mouth with a tenth of their health, and none of the run's
  gold, things or wands.
- A win: the hero keeps the run's gold and things.
- Experience is always kept.

All three phases were done together and shipped as v11.3 (DONE).

## Phase 1: the cave mouth, the world and the wands (DONE)
- The cave mouth in the Wood, south of the fields: a crag of grey rock three squares deep with a dark mouth, a path
  to it from the fields, a portal home beside it; the second plinth in the portal yard lit for it.
- Who goes in: the casters (with why not for the rest).
- src/js/64i-claudeita.js: the port - the materials (sand, snow, water, lava, acid, fire, ice, gold...), the world
  made a few rows at a time as the hero descends (five biomes, each with its arena and sanctuary), the loose cells
  simulated where something moves; the spells (projectiles, modifiers, multicasts) and wands cast in order; the hero's
  body, walking, jumping, levitating, swimming, burning.
- src/js/76c-cave.js: the window's side - a canvas over the view, the world's pixels, the hero, the shots, the light
  of the deep, the HUD (health, levitation, mana, gold, depth, the wands and the slots).
- The hero's health in the cave follows theirs (more in the cave, the same share); their level and wisdom or
  intellect add to the spells' damage.
- Death and leaving as asked; experience banked always.

## Phase 2: the cave's creatures and bosses (DONE)
- The nine kinds (slime, bat, hiisi, frost, spore, worm, imp, turret, ghost) and the five bosses (Gravelmaw,
  Rimecaller, Mother Spore, the Cinder Colossus, the Unmaker) with Claudeita's own ways.
- The sanctuaries: a fountain, a shop of wands and spells, and (new here) a rope up: out with what you carry,
  counted as a win.
- Pickups: gold, wands, spells, hearts; each boss leaves a thing of the party's own (gear) besides.
- The Unmaker's fall: the cave won.

## Phase 3: the wand editor, the rack, sounds, docs (DONE)
- Tab: the wand editor (Claudeita's: click a spell, then where it goes; right-click to the bag).
- The rack at the cave mouth: wands and spells carried out of a won run are kept, and up to two may be taken in.
- Sounds for casting, blasts, digging, splashes, gold, hurts and bosses.
- Tests (the world's rules, the wands' casts, the death and win rules), README, Help and the Manual.
