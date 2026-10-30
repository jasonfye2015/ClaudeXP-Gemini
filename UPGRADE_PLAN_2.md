# Claude and Magic - the fourth big update: new and expanded mechanics

Where the game stands (v2.0, after the third big update): fifty floors in ten bands, eleven callings with three-tier
paths, bonds, affixes and uniques, an alchemist and a smith, choice events and hazards, rivals and peddlers, a
weekly challenge, run codes, a bestiary, a balance simulator and a test suite. ~9,500 lines of JS. Saves keep each
floor as what changed since the seed made it; the dice of every fight are the seed's.

The third update was about depth in what was there. This one is about **new systems**: a generator that can grow
again, a surface between runs, a magic system with more than a list of spells, fights with ground under them,
replays, and a difficulty ladder with rungs. Same shape as before: phases, each shippable, each with tests and a
simulator run. Phase 0 is again the one that pays for the rest.

---

## What v2.0 invites (and what it blocks)

| # | Observation | Where | What it means for this plan |
|---|-------------|-------|-----------------------------|
| 1 | **The generator is frozen.** A seed must make the same floor in every version, so no new rooms, layouts or structure can be added without moving every saved run. Three features were deferred for this reason. | `20-world.js`, `25-saves.js` (`CM.GEN`) | Phase 0: a *generator version* - old runs keep the generator they were made with; new runs get the new one. Unblocks everything structural. |
| 2 | **Every fight is deterministic.** Same seed, same choices, same outcome. | `62-combat.js` (the fight's dice), `60-game.js` (`rng` in the save) | A run is reproducible from its inputs: **replays** are cheap (record choices, replay them), and so are "ghost" runs and share-a-run-as-a-film. |
| 3 | **Between runs there is little to do.** Kits, three earned callings, a vault slot, a memorial. A run's reward is a Hall of Fame row. | `64-meta.js`, the title | A **surface** (a village that grows with what you bring up) gives every run a reason beyond depth. |
| 4 | **Magic is a list.** Spells have a cost and an effect; nothing to decide but which. Tomes add rows to the list. | `CM.ABILITIES`, `doAbility` | Overcasting, combining, reagents: decisions inside the casting. |
| 5 | **The fight has no ground.** Rows and reach, and otherwise an abstract exchange of blows. The dungeon's furniture (water, vents, pillars, the lair's throne) is scenery. | `62-combat.js`, `foePlace` | Terrain in combat, formations, phases for the lesser guardians. |
| 6 | **Difficulty is three rungs and a wall.** Fair crowns half the simulated parties; Grim crowns none (the Lich King ends every run on floors 16-20). Nothing between Fair and Grim, nothing past Grim. | `CM.DIFFICULTIES`, the sim | An **ascension ladder** (win, and the next run carries one more modifier) and a middle rung. |
| 7 | **The bot doesn't play the new systems.** It ignores events, the alchemist, strongboxes, oils, the waystones. Its numbers understate what a player can do. | `tools/bot.js` | Every phase adds the bot's use of its mechanic, or the sim measures nothing. |
| 8 | **The three earned callings borrow their pixel dolls** and have no tomes, no kit lines, no partyAdvice beyond the Monk. The Monk's fists use the "?" icon. | `36-looks.js`, `CM.TOMES`, `CM.KITS` | Finish them in Phase 1. |
| 9 | **`70-ui.js` is 1,550 lines**, and the action bar is a wall of buttons. New systems need screens. | `70-ui.js` | A screen-per-file split like the game's, and a proper combat timeline. |
| 10 | **The Deep's bands are five floors of the same thing.** Hazards and a unique each, but one route down and no reason to go back. | `makeFloor` (band structure) | Branches, wings, a second way down, places worth returning to. |

---

## Phase 0 - A generator that can grow (do first) - DONE (v2.1)

**Goal:** the floors of new runs can change again, and old runs still play out on the floors they had.

1. **Generator versions.** `CM.GEN` becomes a real version. `20-world.js` keeps `makeFloor` as `CM.generators[1]` -
   frozen, never edited again, with a test that its output for a hundred seeds matches a stored fingerprint file
   (`tests/fixtures/gen1.json`). New work goes in `CM.generators[2]` (`21-world-v2.js`), which starts as a copy and
   is free to change. A run records its `gen`; `floorAt` uses the run's generator. Old saves say `gen: 1` by the
   migration. The daily, the weekly and run codes carry the gen, so "the same dungeon for everyone" stays true.
2. **A floor description language.** v2 builds a floor from a *plan* (rooms, their kinds, connections, what they
   hold) before carving it, so set pieces, wings and multi-room vaults are data (`CM.ROOMS`), not special cases, and
   the planner can be tested without the carver.
3. **Bot and sim, extended.** The bot learns the v2.0 systems: it opens strongboxes, answers safe events, brews
   oils and greater potions at camp, rubs oils on before guardians, uses waystones to rest before a shaft, buys from
   peddlers. The sim reports per-calling survival and per-band deaths as before, plus *where gold goes* and *what
   is never used* (a mechanic nobody uses is a mechanic to cut or fix).
4. **A UI split.** `70-ui.js` into `70-ui.js` (the frame, dialogs, helpers), `71-title.js`, `72-create.js`,
   `73-play.js` (party, log, actions, automap), `74-fight.js`, `75-bag.js`, `76-camp.js`. Same `CM.UI` class, methods
   per file, as the game's own split.
5. **Replay recording** (the data side only; the viewer is Phase 7). Every action the player takes - a move, a
   turn, a use, a fight command, a choice, a purchase - goes through one `game.act2(kind, args)` door and into
   `run.log` (a compact array). The save keeps it. A test replays a bot run from its log and gets the same floor,
   gold and party, step for step.

**Done when:** the gen-1 fingerprint test passes, a v2.0 save loads on gen 1 and a new run starts on gen 2, the bot
uses every v2.0 system in the sim's report, and a replayed log reproduces a run exactly.

---

## Phase 1 - Finishing the eleven, and the ground of a fight - DONE (v2.2; the dolls want the full tile set)

**Goal:** the earned callings feel native, and a fight has a place it happens in.

- **The three callings, finished:** pixel dolls of their own (gathered from the Crawl set: a monk's robe, a
  necromancer's hood and skull-topped staff, goggles), a fists icon, a tome for each (Tome of Hexes, of Turrets),
  kit lines, partyAdvice lines ("no one to take the blows but a Monk"), a recruit of each kind at the tavern once
  the calling is earned.
- **Terrain in combat.** The square the fight stands on matters: in water (the Vaults, the Drowned Town, a flooded
  floor) frost holds every foe it touches and fire does half; on a vent the Foundry's heat sears the back row; among
  the lair's pillars one fewer foe can reach you; in a magical dark every blow may miss. Shown as a line under the
  round counter ("Knee-deep in water: frost holds, fire sputters") and in the bestiary's hints.
- **Formations.** Before a fight (and at camp), a formation: Line (as now), Wedge (one hero in front takes the blows,
  +2 defence; the rest hit for full from the second rank), Loose (no one is reached by a breath for full; blows do
  less; spells cost one more). The sheet's row buttons become a formation picker.
- **Phases for the lesser guardians.** The Rat King, the Drowned Knight and the Forge-Warden get a second form at a
  third of their health, as the Deep's do: the Rat King's swarm becomes the fight (the king hides, four rats a round
  until it is found), the Knight's throne floods the hall (every square water), the Warden's hammer breaks and the
  heat doubles.
- **Monster affixes.** The elite leaders get affixes like the party's gear: Shielded (warded every round), Venomous,
  Mirrored (bolts rebound), Hungry (feeds), Spectral (half of every blow misses), with the bestiary learning each.

---

## Phase 2 - Magic with decisions in it - DONE (v2.3)

**Goal:** casting is a choice of *how*, not only *what*.

- **Overcasting.** Hold the spell's key (or a second button) to pour more magic in: double the cost for half again
  the effect, triple for double and a chance of backlash (the caster burns for a tenth of their health). Shown on the
  cast menu as three rows per spell.
- **Weaving.** Two casters in one round make one spell: the first casts and *holds*; if the second casts a matching
  spell before the round ends they weave: Fire Bolt + Frost = Steam (every foe blinded), Fireball + Lightning =
  Firestorm (double, burning), Heal + Bless = Sanctuary, Sleep + Hex = Nightmare (sleeping foes take double). Found
  by doing, like combos; the journal keeps them.
- **Reagents.** The alchemist's ingredients have a second use: a spore cap cast with Sleep lasts the fight; crystal
  dust with Magic Missile splits it; grave salt with Turn Undead routs. One reagent a cast, from the pack.
- **Spell levels for tomes.** A tome of a spell the reader knows isn't refused: it raises the spell a level (+25%,
  -1 cost, to level 3). Tomes become a thing to hunt.
- **Familiars.** The Mage's Familiar (level 6: a cat, an owl or a toad, chosen once): the cat finds hidden doors
  beside you, the owl sees in the dark, the toad eats one ailment a floor. The Necromancer's is a skull that bites.

---

## Phase 3 - The surface - DONE (v2.4)

**Goal:** a place between runs that grows, and a reason to bring things up.

- **Renown.** Every run ends with renown: floors, guardians, the crown, achievements earned, the weekly. Renown is
  the surface's currency; it never buys power directly.
- **The village** (a screen before the title's Expedition card, four buildings, each with levels bought with renown):
  - *The guildhall* - retire a hero who came home: they become a trainer, and every new party of their calling
    starts with one of their boons. Keeps the recruits you've met (the tavern's three come from here).
  - *The merchant's house* - the camp's merchant stocks what the house has unlocked (greater potions from level 2,
    oils from 3, one rare item a camp from 4).
  - *The library* - the bestiary and the journal live here; scholarship: each kind fully learned (met, slain,
    weakness found) is +1% damage against it, for good.
  - *The shrine of the fallen* - the memorial becomes a place: light a candle for a hero laid to rest, and their
    best trinket returns to the vault, once.
- **Contracts.** The guildhall posts three contracts a week (from the week's seed): "Slay the Forge-Warden without a
  healer", "Reach floor 12 on Grim", "Bring up a Spore Cap" - renown and a title each. The bot plays them in the sim
  so none is impossible.
- **The vault, widened** to three slots at guildhall level 2, five at 4.

---

## Phase 4 - The dungeon, branched (needs Phase 0) - DONE (v2.6; the tenth band deferred)

**Goal:** more than one way down, and places worth coming back to.

- **Two stairs.** From floor 3 down, a floor may have two ways down: the ladder, and a *wing stair* into a side wing
  - a short floor of its own (the Sewers under the Catacombs, the Cistern under the Vaults, the Mines beside the
  Halls, the Crypts under the Palace; one per Deep band) with its own hazard, a chest or two, and a way back to the
  main stair a floor below. Optional, known by their smell.
- **Secret floors.** A hidden stair (search the right wall, told by a carving) to a floor between floors - the
  Lich King's wine cellar, the Dwarves' vault - once a band, by the seed.
- **New set pieces,** at last: a great hall with a balcony (two levels: the balcony's archers), a drowned chapel, a
  foundry floor of moving ingots (a plate puzzle), the Ossuary's charnel pit, a crystal maze that spins you. In the
  room language of Phase 0.
- **The dungeon changes behind you.** Floors you have left may be *re-visited by the dungeon*: a closed door on a
  floor two above is open now, a band of monsters has wandered up the stairs, a peddler has set up by the fountain.
  Rare, by the step count, and never on a floor you are on.
- **The Root remembers (New Game+).** After the bottom, the surface offers an Awakened expedition on the same seed:
  every floor is the mirror of itself, the monsters a band deeper, the uniques awake (a second power each), and a
  tenth band under the Root that only an Awakened run can enter.

---

## Phase 5 - The difficulty ladder - DONE (v2.5)

**Goal:** a rung for everyone, and a reason to win again.

- **A middle rung:** Hard (monsters a sixth tougher), between Fair and Grim; Grim softened at the Lich King (the
  cold every third turn, not second) so it is a wall with a door.
- **Ascension.** Winning on Fair or above unlocks Ascension 1 for that seed-kind; each win adds a rung, to 15: the
  fountains are fewer, the camps cost more, the guardians have their second form from the start, affixed elites
  every band, no Greater potions, the Lich King's phylactery moves... each rung one named rule, shown on the
  creation screen, all of them on the Hall of Fame row.
- **Iron.** A toggle: saving only at camps. The Hall of Fame marks it; the achievements for it.
- **The simulator's ladder report:** survival by rung, so each rung is a measured step and not a cliff.

---

## Phase 6 - Expanded systems in play - DONE (v2.7)

- **Morale.** A party value (0-100) the fight reads: high morale, blows land a little more often; low, heroes may
  freeze a turn. Up with victories, bonds, the camp fire, a Bard's song; down with a hero falling, fleeing, a curse,
  hunger. Shown as a word on the party bar ("Steady", "Shaken"), never as a number.
- **Two slots more:** boots (speed, silence, the water walked dry) and cloak (warding, a hood against the dark's
  surprise); the pixel dolls have the parts already.
- **Quirks at creation:** choose one of eight per hero (Nightsighted: sees a step further in the dark, but -1
  Constitution; Greedy: +10% gold, chests may be trapped twice; Pious; Stubborn; Lucky; Sickly...) - small, honest
  trade-offs that make two Knights different.
- **Hunger, lightly:** rations in the pack (the merchant sells them; the alchemist makes trail bread); 300 steps
  without one and morale falls, 600 and the party is Weary (every blow does less). Never death by hunger.
- **Multiclassing at 20:** a hero at 20 may take a second calling's first two spells or skills (a Knight who can
  Heal), at the guildhall, for renown.

---

## Phase 7 - Replays, ghosts and the film of a run - DONE (v2.8)

**Goal:** a run can be watched, shared and raced.

- **The viewer.** Any Hall of Fame row with a log plays back in the real view - the walk, the fights, the choices -
  at 1x, 4x or by fight, with the log scrolling and a scrubber by floor. From the deterministic dice of Phase 0 of
  the third update and the log of Phase 0 of this one.
- **Share a run** as a code that carries the log (compressed; the seed and the inputs are small): paste it and
  watch, or race it.
- **Racing a ghost.** Play the weekly with a ghost: a friend's run (or your own best) walks the same dungeon beside
  you; the automap shows where they were at your step count, the log says when they took the stair.
- **Clips.** The viewer renders a fight or a floor to a short GIF/WebM (the canvas, captured) for the summary card.

---

## Phase 8 - Sound and sight, again

- **Lit stone** (deferred last time): `pack.py --gather` with ambientCG's normal and roughness maps, a second
  texture array, per-pixel torch lighting with specular on wet stone. Budget: the built file under 6 MB.
- **A sprite pass on the Drawn theme:** two frames of idle and one of attack for every monster, painted in code as
  the rest is.
- **Adaptive battle music:** the battle tune in layers by danger - drums alone while the party is whole, the lead
  joins under half, the pad drops out when a hero falls; a guardian's second form changes key.
- **Barks:** a few short synthesised calls per monster kind (a hiss, a laugh, a bell) for strikes and deaths.
- **A camera pass:** a slow push-in when a guardian telegraphs, a tilt when the party falls, a pull-back on the
  crown.

---

## Phase 9 - Around the game, again

- **Install as an app:** a manifest and a service worker in the one file's folder, so a browser offers to install
  it and it opens offline like the Timeline's window does.
- **Cloud of your own:** Export to a URL (the save as a `#fragment`, compressed) that opens the game with the save
  loaded - nothing is stored anywhere but the link.
- **Full gamepad remapping** and Steam Deck layouts (the small screen's rules at the Deck's size).
- **Text as data:** every string the player reads moves to `12-text.js`, keyed, so a translation is one file. No
  translation shipped; the door open.
- **Statistics:** a page of what every run has come to - fights, deaths by band, favourite calling, gold spent
  where - from the logs.

---

## Order, size and dependencies

| Phase | Size | Depends on | Notes |
|-------|------|------------|-------|
| 0 Generator, bot, UI split, log | L | - | Do first. Nothing structural moves without it. |
| 1 The eleven, terrain, formations, phases | M | - | Mostly combat; sim after. |
| 2 Magic | M | 1 (terrain reads elements) | Weaving wants the timeline UI from 0's split. |
| 3 The surface | L | 0 (UI split) | The first new screen; renown touches every run's end. |
| 5 The ladder | S | 1, 2 (the rungs name their rules) | Measured with the sim's ladder report. |
| 4 The dungeon, branched | L | 0 (gen 2, room language) | The biggest content phase. |
| 6 Expanded systems | M | 3 (multiclassing at the guildhall) | Morale touches the bot. |
| 7 Replays | M | 0 (the log) | Pure addition; a joy. |
| 8 Sound and sight | M | - | Needs the art gathered on the machine with the full sets. |
| 9 Around the game | S-M | 7 (share a run) | |

Suggested sequence: **0 -> 1 -> 2 -> 3 -> 5 -> 4 -> 6 -> 7 -> 8 -> 9**, v2.1 after Phase 0, v2.5 after Phase 3, v3.0
when Phase 4 lands.

## Risks

- **Two generators to keep.** Gen 1 is frozen by a fingerprint test; the cost is that any bug in it stays. Fine: it
  is finished. Gen 2 is where bugs go.
- **The surface changes what a run is for.** Renown must never buy power, or the Hall of Fame stops meaning
  anything; the guildhall's trainer boons are the one exception and are capped at one.
- **Scope.** Phases 3, 4 and 6 are each a game's worth. Ship each at its first useful size (one building, one wing,
  morale alone) and let the sim and the Hall of Fame say what wants more.
- **Save size.** The log makes saves grow with the run (an input a step: ~100 KB for a long run, compressed less).
  The 200 KB budget holds; the viewer never needs more than one run's log in memory.
- **The bot.** Every mechanic the bot can't use is unmeasured. Budget a day of bot work per phase and hold to it.
