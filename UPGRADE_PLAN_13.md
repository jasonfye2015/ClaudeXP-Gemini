# The nineteenth big update: the island through the Neather Gate, made a place worth going

v11.9 brought Claudecraft's island in as a tech demo: walk, break, place, and the island remembers. This plan makes
it part of the game: what the party digs, fells, finds and fights there turns into gold, experience and things that
work at home, and what the party brings from home (picks, lanterns, potions, weapons) matters there. Nine phases,
each one shippable and committed on its own (v12.0 to v12.8).

Principles, kept throughout:
- **The game's own systems are the currency.** Island ore becomes the main game's ore chunks (copper, iron, silver,
  gold, star-iron: 23c-ore.js), so they are smelted at the Smith's forge into the same bars and alloys. Charcoal is
  the same charcoal. Gear found is real gear (CM.makeItem). Experience goes to the heroes by the usual share.
- **What the party brings matters there.** A pick from home sets what can be mined and how fast; its points wear as
  they do in the shaft's caves. A lantern widens the light at night and underground. The heroes' weapons and spells
  are what they fight with. Potions on the belt work.
- **Same rules of risk as the other places.** Carried things are lost if the party falls (left in a bundle where they
  fell, to be fetched); things stored in an island chest are safe; experience is always kept.
- **Original creatures and pictures.** The island's creatures are the game's own monsters (in their own pictures);
  nothing is copied from any other game.
- **Tests and a bot for every phase**, as for the Mage Tower and the Fortress, and the island's save stays small
  (edits only, capped).

---

## Phase 0 (v12.0): the party on the island, and a satchel
- **Who walks.** The whole party goes through; the front hero is the one who walks and acts (Tab changes who leads).
  Hits land on the leader first, then spread to the front row, as in the dungeon.
- **The HUD** gains the leader's health and magic bars, the party's four portraits (click to lead), and a clock.
- **The satchel.** Breaking a block puts it in the satchel (a 27-slot store of stacks, up to 64 each), shown with I.
  The hotbar's nine slots now hold what is in the satchel; placing uses it up. Creative placement of any block ends.
- **Breaking takes time.** Each block has a hardness (leaves fast, dirt quick, stone slower, ore slower still); hold
  the button and a crack grows over the block. Bare hands are slow on stone and cannot break ore.
- Tests: breaking yields the block, placing spends it; hardness timings; the leader takes the hits.

## Phase 1 (v12.1): ore, caves, and the pick from home
- **Caves.** A 3D noise carves winding caves and a few large caverns under the hills (never through the sea floor),
  lit only by what the party carries.
- **Ore in the stone, by depth** (the deeper, the rarer): copper near the surface, iron below, silver deeper, gold in
  the deep caverns, and star-iron in a few seams just above the bedrock. Coal-like **charstone** too, near the top.
- **The pick from home.** Ore can only be broken with a pick from the bag that mines it (CM.PICKS: copper, iron,
  steel...), and each ore block mined wears the pick a point, as a swing does in the shaft's caves. A better pick
  breaks stone faster too. With no pick, stone and dirt still break, slowly.
- **Ore drops as the game's own ore chunks** (CM.oreChunk), and charstone as **charcoal** (CM.charcoal). Both are
  heavy, as at home: the party's carrying limit applies to the satchel's ore.
- Tests: ore depths by seed; a copper pick cannot take silver; points worn; chunks are the main game's.

## Phase 2 (v12.2): crafting on the island
- **A workbench** (from planks) and a **kiln** (from cobblestone) the party can build and place.
- **Recipes** (the satchel's materials, nothing from home): planks and poles from wood; **torches** (pole and
  charcoal) that light their blocks and can be placed on walls; **island tools** - stone pick, stone axe, stone
  sword, then copper and iron ones from bars smelted in the kiln - that speed breaking and add to a weapon's damage
  there; **chests** that keep things safe on the island; **ladders**; **glass** (sand in the kiln).
- **The kiln smelts** ore chunks with charcoal into **bars** - the same bars as the Smith's smelter makes (three
  chunks and a charcoal), so a party can bring home bars instead of heavy ore.
- Island tools stay on the island (a rack by the gate); bars, ore and charcoal can go home.
- The crafting window: the satchel on one side, the recipes the party can make lit on the other, one click to make.
- Tests: every recipe's inputs and outputs; the kiln's bars equal the forge's; tools break faster by tier.

## Phase 3 (v12.3): day, night, and the island's creatures
- **The island keeps the game's clock**: day and night, the sky's colours, the sun and moon, and dark at night.
- **Creatures**, the game's own monsters seen in their own pictures (billboards in the 3D view): by day, harmless
  wildlife to hunt for meat (the cook's ingredients, 69d-cook.js); at night and in the caves, monsters by depth -
  Giant Rats and Kobolds near the surface, Skeletons and Goblins underground, Wraiths and Gargoyles in the deep
  caverns. They spawn in the dark, away from torches and from the party's light.
- **Fighting** in real time, as in the Mage Tower: the leader's weapon (blade, bow or spell, with the main game's
  damage sums and the leader's level) or an island sword. Monsters chase by the shortest walk over blocks, strike
  when close, some shoot.
- **Experience** for every kill, a third of the rules' amount (as the tower's xpShare); **gold** dropped by the
  monsters that carry it (Kobolds, Goblins); now and then a monster drops a thing (a real item, by depth).
- **Falling:** the party is put back at the gate on the island with the leader at a tenth of their health; the
  satchel's contents are left in a bundle where they fell (a glowing chest, there until fetched); experience kept.
- Tests: spawning only in the dark and away from light; the clock's night; kills pay the share; the bundle.

## Phase 4 (v12.4): the way home, and what comes with it
- **Out through the gate**, everything in the satchel that has a meaning at home comes home:
  - ore chunks, bars and charcoal → the bag (the Smith smelts and forges them: picks, alloys, his work);
  - meat → the cook's ingredients;
  - gems (see phase 5) → sellable gems; things dropped by monsters → the bag, as gear;
  - island gold → the party's gold.
- **What stays**: blocks, island tools, torches - kept in the satchel for the next visit (the island's own).
- **The merchant buys timber and stone** by the stack (a little gold), and the **Guildhall's builders take blocks
  towards the village's upgrades** (a hundred planks or stone count as gold off the next build) - so building
  materials have a use at home too.
- **Into the island**, the party carries its bag: picks and lanterns are used there; potions on the belt work; food
  eaten there mends a little.
- Tests: each kind carried home lands as the main game's own thing; the builders' credit; a pick worn there is worn
  at home.

## Phase 5 (v12.5): finds and places to go
- **Buried and hidden finds**: gem blocks in the deep caverns (garnet, sapphire, emerald) - sellable at home, and
  three of a kind make a ring or an amulet at the Smith (CM.makeItem of that slot); **sunken chests** in the sea and
  **ruins** on the hills, each a small built structure with a chest (gold, a thing by depth, a map fragment).
- **Map fragments**: four make a map that marks the island's vault (phase 7) on the HUD's compass.
- **Lairs** in the deepest caverns, as the Fortress has: they send monsters until broken, and leave a chest.
- Tests: the finds are the seed's; chests pay by depth; four fragments make the map.

## Phase 6 (v12.6): a home on the island
- **A bedroll** (from wool-less island fibre: leaves and poles) placed in a room the party has walled and roofed
  makes it a **camp**: sleeping there passes the night, mends the party as resting does at home, and moves the
  party's return point there. A camp with a chest, a workbench and a kiln within reach is a **homestead**: the town's
  folk notice (renown), and its chest can be reached from the island's gate.
- **Signposts** to place and name; the HUD's compass shows them.
- Tests: the camp needs walls and a roof; sleeping skips the night and heals; the homestead's renown.

## Phase 7 (v12.7): the vault under the island, and errands
- **The vault**: under the island's highest hill, a sealed chamber of basalt reached by digging (the map shows it),
  three rooms of traps, lairs and a guardian - an original one, the Hollow Mason, a golem of the island's own blocks
  that pulls stone from the walls to mend itself. Its fall leaves a relic-grade thing and a title.
- **Errands from town** (64b-people.js): the Smith wants iron ore or bars; the cook wants meat; the Library wants a
  rune from the vault's walls; the Guildhall wants stone for the wall. Each pays as errands do.
- Achievements: the first star-iron, the vault's guardian, a homestead.
- Tests: the vault's place by seed; the guardian's mending; each errand's turn-in.

## Phase 8 (v12.8): measure, tune, and tell
- **A bot** (tools/craftbot.js) that goes in with a given party and pick, mines, crafts, fights at night and comes
  home: the gold, experience and ore an hour of play brings, against an hour in the shaft at the same level - the
  island should pay about as well as the dungeon, a little less in gold and more in ore.
- **Performance**: only changed chunks re-meshed, creatures culled by distance, the save capped (edits only).
- **Docs**: README, LORE (the island's history), Help and the Manual's chapter; screenshots.

---

## The numbers to start from (tuned in phase 8)
| | |
|---|---|
| Ore per block | 1 chunk (2 for star-iron seams) |
| Pick wear | 1 point per ore block |
| Kiln | 3 chunks + 1 charcoal = 1 bar (as the Smith) |
| Kill experience | a third of the rules' (as the Mage Tower) |
| Monster level | 1 + the night's count, + depth bands underground (surface 1-5, caves 5-15, deep 15-30) |
| Falling | leader at a tenth of their health, satchel left in a bundle, experience kept |
| Timber / stone at the merchant | 1 gold a stack of 16 |
| Builders' credit | 100 blocks = 50 gold off the next village build |
| Gems | garnet 40, sapphire 80, emerald 120 gold |

## Open questions for you
1. Should the **whole party** fight (four heroes taking turns as leader), or should one hero go in as in the other
   places? The plan keeps the whole party, with a leader.
2. Should **falling** keep the satchel in a bundle to fetch (as planned), or lose it outright like the Fortress?
3. Is **building a homestead** (phase 6) wanted, or should the island stay a place to mine and fight?
