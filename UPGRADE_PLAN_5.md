# Claude and Magic - the seventh big update: the town of Caer Duin above

A plan for v5.2 to v6.0. The surface becomes a place: a town the party stands in, walks through and comes home
to, with a home of its own, a tavern, a merchant, a library, a temple, a guildhall, a smith, an alchemist's
garden and the chronicler's house - built on what the village already is (`65-village.js`: four buildings raised
with renown, villagers, contracts, the vault, the memorial), and on what the camps already do (`63-camp.js`:
trade, the temple, the tavern, the smith, the alchemist, the waystone). Nothing the village or the camps do is
lost; it moves indoors.

The shape in one line: **a run begins at home, walks down the lane to the shaft, and the town grows behind the
party with every run it brings back.**

---

## What is there now, and what each phase turns it into

| Now | After |
|-----|-------|
| The village is a dialog on the title screen: four buildings, renown spent on levels, villagers' lines, contracts | The village is floor 0, drawn by the 3D renderer: a square, lanes, doors that open into the buildings |
| A run starts on floor 1 at the top of the stair | A run starts at the party's door; the shaft is at the end of the lane (a short walk, or one press to skip) |
| The vault is at the camps, one to five things | The vault stays at the camps; the home has a stash of its own that grows with the house |
| The tavern, merchant, smith, alchemist are at the camps every five floors | Each has its house in town as well, with more to offer than the camp's bench; the camps keep their benches |
| Trophies and named weapons are lines in the compendium | They hang on the home's wall, and the memorial's names are on its door |
| Renown buys four buildings' levels | Renown raises the whole town, building by building, and the map fills in |

## Phase 0 - The ground of the town - v5.2 - DONE

- **Floor 0 exists.** `CM.makeTown(seed, village)` builds a hand-laid floor (a template in `20-world.js`, not a
  generator: the generators and their fixtures do not move): a square with a well, four lanes, the shaft's
  mouth at the east end with the stair down, and building plots on the lanes. A plot is a feature of type
  `"building"` with an `id` (home, tavern, merchant, library, temple, guildhall, smith, garden, chronicler); a
  plot not yet raised is a foundation (drawn as low stones, walkable, "Build me a roof").
- **The town is a floor to the engine.** `floorPrint`, `snapshot`, `floorDelta` and `restoreFloor` treat 0 like
  any floor (number 0 restored by `makeTown`); the automap draws it; `look`, `move`, `travelTo`, `explore` work;
  no monsters wander it, no torch burns on it (daylight: `lightFactor` 1 above ground), no hunger counts.
- **In and out.** `newGame` enters floor 0 at the home plot facing the lane; the stair at the shaft's mouth is
  the `ladder` thing, and `use` on it goes to floor 1 as today. From a camp, "Back to town" (the waystone's
  first stone, free) returns to floor 0 at the shaft; from floor 0 the shaft goes to the deepest camp reached
  (the run's `trail`), so the town is never a trap. The title's "Continue" lands wherever the party was,
  including town. A setting, *Skip the walk*, puts the party at the shaft on a new run.
- **The walls say what they are.** Walking up to a plot's door says its name and level; Space opens the
  building's screen (Phase 1 onward); the foundation opens the village's build dialog for that building.
- **The bot and Automatic** know floor 0: from home they walk to the shaft and go down; from a camp they never
  go back up unless told. `tools/sim.js` starts runs at the shaft (`--town` to start at home and measure the
  walk).
- **Tests**: the town is the same for a seed and a village state; a new run starts at home and reaches floor 1
  by walking; save and load on floor 0; the deltas of floor 0 are small; the bot's runs are unchanged in length.

Size: M. Risk: every "floor.number" comparison in the rules that assumes 1 or more (`themeIndex(0)`,
`guardianFor(0)`, hazards, light) is audited and tested here first.

## Phase 1 - The home - v5.3 - DONE

- **A house of the party's own**, at the west end of the square, raised like a building (renown: 50, 150, 400,
  800, 1500; five levels). Inside, one screen with rooms that appear as it grows:
  - **The hearth** (level 1): the party rests for nothing before a run (full health and magic, the small
    ailments cured); a *rested* buff (+5% to hit on floors 1 to 5) for a run begun from home.
  - **The stash** (level 1: 6 things; 2: 12; 3: 20; 5: 40): the party's own storage between runs, apart from
    the camps' vault - anything may be left; nothing is lost when a party falls. Taking a thing from the stash
    into a run is free; a thing in the stash is never insured, never bumped.
  - **The trophy wall** (level 2): the guardians' trophies, the named weapons and the unique things found hang
    here as the item cards they are; the Hall of Fame's crowns are a shelf.
  - **The kitchen** (level 3): meat brought home is cooked here for a meal that lasts the first *two* floors;
    the Bag of Holding's cousin, a *larder*, keeps three rations from run to run.
  - **The door-plate** (level 4): the memorial's names on the door; lighting a candle at home costs what the
    shrine charges, and the candle's gift goes to the stash instead of the vault.
  - **The study** (level 5): a hero may *retire home* (as the guildhall's trainers do) and, retired, writes a
    *will*: one thing from the stash starts every later run in the pack.
- **Tests**: the stash survives a fallen party and a reload; the rested buff is on and off at floor 6; a will
  arrives in the pack of a new run.

Size: M.

## Phase 2 - The tavern, the merchant and the smith - v5.4 - DONE

- **The Hanged Lantern (tavern)**, in town: the recruits (three, plus the rescued and the remembered), the
  fence, the rumours, the bounty board (the week's three contracts and the camps' bounties on one board), and
  the villagers at their tables (Dunmore, the trainers who came home, a *regular* who sells the week's seed's
  gossip: which band the rare ingredient is in, where the Bag of Holding lies). A drink (5 gold) gives the
  party morale 90 to set out with. The camps' tavern keeps the recruits only.
- **The Merchant's House**, in town: the full stock (no rotation at home), orders placed here delivered to the
  first camp, insurance, and at level 3 a *commission*: a weapon or armour of a chosen base at the party's level,
  made by the next camp. The camps' merchant keeps the rotating bench.
- **The Smith's forge**, in town: everything the camps' smith does, and two things only the forge can:
  *reforging a base* (a Long Sword into a Bastard Sword of the same affixes, for gold and essence) and *setting
  a second gem* in a relic. The smith's apprentice buys scrap at a better price.
- **Tests**: a commission arrives at the first camp; a base reforged keeps its affixes and marks; the fence is
  in the tavern and not at the camp's bench twice.

Size: M.

## Phase 3 - The library, the temple and the guildhall - v5.5

- **The Library**: the codex, the compendium, the bestiary, the combos and the item cards at a reading desk
  (one screen with tabs, the journal's boards moved here; the journal in the dungeon keeps only what the run has
  read). Wren the chronicler copies chapters fair as now. New: *tomes to borrow* - one tome a run, returned when
  the party comes home (a spell for the run); the *Lost Page* scroll's three lines are shelved here when found;
  and at level 4 the *gazetteer*: the seed's floors 1 to 5 mapped before the run (the automap's walls, not the
  things).
- **The Temple**: Father Osric's shrine of the fallen (candles, the Patriarch's history as it grows), the
  temple's services at town prices (a tenth cheaper), the tithe, and a *vigil*: a fallen hero's wounds and
  scars reviewed - a scar may be kept or let fade, once.
- **The Guildhall**: the trainers, the second calling, the contracts, and a *roster*: the parties this browser
  has made, kept as presets to set out with again (names, callings, origins), and a *muster* button that makes
  the next run's party from the last one that came home.
- **Tests**: a borrowed tome is in the pack for a run and back on the shelf after; the gazetteer marks floor 1's
  walls on a new run; a roster preset makes the same party.

Size: M.

## Phase 4 - The garden, the chronicler and the square - v5.6

- **The alchemist's garden**: ingredients planted between runs (a bed holds three; each run that ends, a bed
  grows one more of what was planted, up to five), the brewing bench with every recipe at town prices, and the
  alchemist's request from the camps posted here too. The rarer ingredients can be planted only once found.
- **The chronicler's house**: the films (watched at a table), the statistics, the ledger, the Hall of Fame and
  the memorial's book - everything that was a title-screen dialog, under a roof; the title keeps *Continue*,
  *New run*, *Town* and *Settings*.
- **The square**: the well (a drink: the party's morale word said back, and a *wish* - a coin thrown is 1 gold
  to the town's renown), the notice board (the week's seed and party, the daily's name), a *market day* on the
  week's seed with a peddler's cloth in the square, and the townsfolk: three villagers who walk the lanes by
  the time of day (the browser's clock), each with a line a day from `13-lore.js`'s village chapter.
- **The town at night**: after a run ends past the daily's hour the lanterns are lit; nothing changes but the
  light and the lines.
- **Tests**: a planted bed grows by one a run; a film opens from the chronicler's table; market day falls on the
  week's seed.

Size: M.

## Phase 5 - Growth, and the town as a thing that remembers - v5.7

- **The town grows on the map.** Each building's level draws it: a foundation, a frame, a roofed house, a house
  with a sign, a house with a lit window. Raising a building is done at its own door, not in a dialog from the
  title. The square's well is dry until the first crown, running after.
- **Renown rebalanced** for nine buildings: the costs in `CM.VILLAGE` re-tuned so a careful player raises the
  town over twenty to thirty runs, with the home first and the chronicler's house last; `CM.renownFor` gains a
  little for every building visited in a run (the town rewards being used).
- **What the party brought back** shows: trophies on the home's wall, the smith's sign bears the first named
  weapon, the library's shelf fills chapter by chapter, the memorial's door-plate grows, and the tavern's wall
  has the Hall of Fame's best run painted on it.
- **The town's own chapter** (the hill before the shaft, told as renown is spent) moves to the carved stones of
  the square's well, read like the dungeon's walls.
- **Tests**: a building's drawn level matches its data; renown over a thirty-run sim raises the town; the well's
  stones read in order.

Size: S-M.

## Phase 6 - Around the town - v6.0

- **Automatic in town**: the toggle walks the party through its errands (home: rest and stash; merchant: buy;
  temple: heal; tavern: bounties; then the shaft) in a sensible order, and `tools/sim.js --town` measures it.
- **Gamepad and touch** in town: the lanes walk with the stick; buildings open with Use; the building screens
  take the pad's list focus.
- **Films** begin at home when the run did; a film of a run that walked the town shows the walk.
- **Words as data**: every building's lines through `12-text.js`; `tools/words.js` counts the town's words.
- **A balance pass** with the sim (the rested buff, the gazetteer, the will, the commission: none of them may
  move the crown rate on Fair more than five points).
- README, plan status, the version.

Size: S.

---

## Order, size and dependencies

| Phase | Version | Size | Depends on | Notes |
|-------|---------|------|------------|-------|
| 0 The ground of the town | 5.2 | M | - | Floor 0, the walk, in and out, saves, the bot. Do first; everything stands on it. |
| 1 The home | 5.3 | M | 0 | The hearth, the stash, the trophy wall, the kitchen, the door-plate, the study. |
| 2 The tavern, the merchant, the smith | 5.4 | M | 0 | The camps' benches moved under roofs, with more to offer in town. |
| 3 The library, the temple, the guildhall | 5.5 | M | 0, 2 (the roster uses the tavern's recruits) | Reading, candles, trainers, the roster. |
| 4 The garden, the chronicler, the square | 5.6 | M | 0 | The last of the title's dialogs under a roof; the square's life. |
| 5 Growth | 5.7 | S-M | 1-4 | Buildings drawn by level; renown re-tuned for nine. |
| 6 Around the town | 6.0 | S | all | Automatic, pad, films, words, balance, docs. |

Suggested sequence: **0 -> 1 -> 2 -> 3 -> 4 -> 5 -> 6**. Phases 1 to 4 do not depend on one another and could
go in any order; the home first because it is what the player asked for.

## Risks

- **Floor 0 in the rules.** Fifty places compare `floor.number` to bands, guardians, hazards, light and hunger.
  Phase 0 audits them with a test that walks every rule's entry point on floor 0 (nothing wanders, nothing
  burns, nothing is hungry, no hazard, no gathering, no encounter) before any building is built.
- **Two places for one service.** The camps keep their benches so a run deep down is not starved; the town has
  more. The rule: nothing is *only* in town that a run needs mid-run (potions, the temple's raise, the vault).
- **The home's stash and the vault together** could make every run the last run's shopping trip (the earlier
  plan's reason to refuse a stash). The guard: the stash takes nothing *from* a run except by walking it home
  (the party must come back up to leave things), and a fallen party's pack is not sent home - only the insured
  things go to the vault, as now.
- **Saves.** Floor 0's delta is in the run's save like any floor's; the town's state (levels, stash, beds,
  trophies) is in the village store, migrated from the present `village` object (schema 4, tested against a
  v5.1 export).
- **The renderer.** The town is drawn with the dungeon's renderer and a tenth theme (daylight, timber, thatch);
  no new renderer. Buildings are wall tiles with a door and a sign; interiors are screens, not rooms.
- **The bot.** Phase 0 teaches it the walk; nothing later may make a run begin anywhere the bot cannot start.

## Not in this plan, and why

- **Interiors you walk through.** A building is a screen; the lanes are the walk. Rooms inside rooms would want
  a second map scale the game does not have.
- **Town quests with their own chapters.** The town's story is the hill's, told at the well; the dungeon keeps
  the chapters. One new chapter would want the lore bible's table extended first.
- **Money changing between town and dungeon rates.** Gold is gold; renown is renown. No exchange.
- **Townsfolk with schedules and relationships.** Three walkers with a line a day is the whole of it.
- **A siege, a raid, the dungeon coming up.** The Awakened mode is the dungeon remembering you; the town does
  not fight.
