# Claude and Magic - the third big update: an upgrade plan

Where the game stands (v1.0, after eight phases): a 3D blobber in one HTML file - eight callings with paths, fifty
floors in ten bands, nine guardians and their echoes, Endless, three themes, generated music, a daily dungeon,
achievements, slots, gamepad and touch. ~8,000 lines of JS in `src/js`, built by `build.py`.

It is a big, finished-feeling game. The plan below is in the same shape as the last two updates: phases, each
shippable on its own, each ending with the build current and the game playable. Phase 0 is not optional - it pays
for everything after it. The rest can be reordered to taste.

---

## What I found looking through it

These are the things the plan is built around. Each was checked against the code or measured in a headless run.

| # | Finding | Where | Why it matters |
|---|---------|-------|----------------|
| 1 | **Saves can fail silently.** `saveRun()` keeps every visited floor whole; `CM.store.set` returns `false` when storage is full, and nothing checks it. | `60-game.js:70-79`, `00-util.js` | Measured: 150 freshly generated floors are ~2.5 MB of JSON before the automap's `seen` fills in. Three slots plus the Hall of Fame share one ~5 MB per-origin quota. A deep Endless run can stop saving with no warning. |
| 2 | **Fights aren't seeded.** The dungeon comes from the seed, but `game.rnd` is `Math.random()`-seeded. | `60-game.js:29` | Today's dungeon is "the same one for everyone" only up to the first fight. And since saves happen only in explore/camp, reloading mid-fight re-rolls it. |
| 3 | **The tests live outside the repo.** README points at `Tests\test_claudemagic.py` (Qt WebEngine); it isn't here, and there is no CI. | README, repo root | Every phase so far was checked on one machine. Nothing stops a regression from reaching `main`. |
| 4 | **`60-game.js` is 2,358 lines, one class, ~130 methods.** Combat, exploring, camp, meta-progression and saving all live together. | `60-game.js` | Each new feature costs more than the one before it. Combat changes (Phase 2) want their own module. |
| 5 | **Save migrations are scattered.** `upgradeHero`, `upgradeFloor`, `upgradeMonster` and `x \|\| default` across `continueRun`; the save has no schema number. | `20-world.js`, `60-game.js` | Fine at eight phases, fragile at sixteen. |
| 6 | **Monster stats are a straight line:** `hp 8+6L, atk 3+2L, df L`. Heroes level on `60*(L-1)^1.6`. | `20-world.js:134` | Kinds differ only by ability and speed, not by shape: a troll is a rat with regen. The curve has never been measured end to end. |
| 7 | **No accessibility settings.** No text size, no reduced motion (despite shakes, flashes and colour washes), one `@media` query. | `style.css`, Settings | Phase 2 of the last update added a lot of screen shake and flash. |
| 8 | Small: `CM.built` is never filled in (`build.py` replaces only `__VERSION__`); `VERSION` is still `1.0` after eight phases. | `00-util.js:4`, `build.py` | Export files and bug reports can't say which build they came from. |
| 9 | The README notes the full Crawl tile set and full ambientCG material sets (normal, roughness, AO maps) are kept "for the updates to come"; only the `_Color` maps are used. | `pack.py` | Lighting upgrades are already paid for. |

---

## Phase 0 - Foundations (do first) - DONE in v1.1

**Goal:** the game can grow for another eight phases without losing saves or regressing.

1. **Saves as seed + changes.** A floor is `CM.makeFloor(number, seed)` - deterministic. Save only what differs:
   things taken, features toggled (doors, levers, plates, fountains), monsters killed/moved, ropes tied, and `seen` as a
   bitset (27x27 = 92 bytes, base64). On load: regenerate, then apply the delta. Expect ~100x smaller saves.
   - Keep reading old whole-floor saves (detect by the presence of `grid`).
   - `CM.store.set` failures surface: a toast ("The save didn't fit - export your runs") and a Settings line showing
     storage used.
2. **Save schema version + one migration chain.** `data.schema = N`; `CM.MIGRATIONS[n](data)` steps an old save up.
   Fold `upgradeHero/Floor/Monster` into it.
3. **Seeded fights.** `game.rnd` comes from `hash(seed, floor, fightIndex)` (or a stream saved with the run). Today's
   dungeon becomes fair; the daily board can be trusted. Optional "Iron" toggle: save at the start of a fight, so
   reloading doesn't re-roll it.
4. **Tests in the repo, and CI.** A Node + Playwright harness (Chromium is the common case anyway) under `tests/`:
   - `build.py --check` and `pack.py --check`
   - `CM.solvable` across 1,000 seeds x 50 floors (and 100 floors Endless)
   - save -> load round trip, including an old-format save fixture per past phase
   - a smoke run: new game, walk, fight, camp, save, continue, no page errors
   - a GitHub Action running all of it on every push.
   Keep the Qt test as the Timeline's own check.
5. **Split `60-game.js`** into `60-game.js` (core, events, saving), `61-explore.js`, `62-combat.js`, `63-camp.js`,
   `64-meta.js` (fame, achievements, trophies, vault). Same `Game` class, methods attached per file
   (`Object.assign(CM.Game.prototype, {...})`), so the build and `CM.game` don't change.
6. **The balance simulator.** `60-game.js` already has "no screen in it". Add `tools/sim.js`: a scripted party
   (sensible default AI: heal under 40%, fight the weakest, cast AoE at 3+ foes) plays N seeds headless and reports
   where parties die, per difficulty, per calling, per band. Every balance change in later phases is checked against it.
7. Small: fill `__BUILT__`, bump to **v1.1**, add the build id to Export and the F3 overlay.

**Done when:** CI is green, a 150-floor Endless save fits in under 200 KB, and the sim prints a death-floor
histogram for Gentle/Fair/Grim.

---

## Phase 1 - Quality of life - DONE in v1.1

**Goal:** less friction on a long run; nothing new to learn.

- **Travel on the automap:** click (or pad-select) a seen square, the party walks there; stops when something is seen.
  `CM.distances` already does the pathing.
- **Auto-explore** (key `X`): to the nearest unseen square; stops at monsters, items, features, low torch.
- **Map notes:** pin a square with a word ("key?", "come back"); kept in the floor delta.
- **Fight faster:** a combat speed setting (animations 1x / 2x / instant), and **Repeat** (last round's orders again)
  for trash fights. Auto-resolve for fights the sim says are trivial (monster level <= party level - 5).
- **Hit chance on the foe** when choosing a target, and expected damage on spells, from `hitChance`/`spellMod`.
- **Item compare** in the bag and the merchant: the stat difference against what that hero wears now, green/red.
  Sort and filter the bag; mark junk; "sell all junk".
- **Waystones:** each camp, once reached, is a waystone; travel between reached camps from any camp (the floors
  between stay as they were). Makes going back up for the temple/smith worth it in the Deep.
- **Hold-to-repeat** movement keys (already there); mouse-look left out - it isn't a grid crawler's way.

---

## Phase 2 - The fight, deeper - DONE in v1.1

**Goal:** fights are decided by choices, not by the numbers. Check every change against the sim.

- **Monsters with shape.** Replace the one formula with per-kind multipliers in `CM.MONSTERS`
  (`hp: 1.4, atk: 0.8, df: 1.2`), and resistances as a table (`resist: { fire: 0.5, holy: 2 }`) - generalising
  `CM.ELEMENTS.weak` and the guardians' "bites deep / does little". Show what's known about a kind on a bestiary page
  in the journal (filled in by fighting them: health, weakness, what it does).
- **Monster rows.** Foes get a front and back row too: archers and casters stand behind; a Ranger, a Volley, a
  spell or Shield Bash's knockback reaches them. Makes the corridor rule ("two can reach you") two-sided.
- **Intent for the big ones.** Guardians telegraph their every-third-turn move a round ahead ("The Forge-Warden
  raises the hammer...") so Defend and positioning matter.
- **Combos between callings.** Small, legible pairings: Frost then Shield Bash shatters (double); a Mocked foe takes
  more from the Rogue; Entangle + Fireball burns the vines; Bless + Smite. Listed on the sheet once discovered.
- **More monster verbs:** heal an ally, shield an ally, split when struck, flee to fetch help, steal an item and run.
- **Status icons on the foe cards** (held, asleep, burning, marked, mocked) with turns left.

---

## Phase 3 - The hoard, deeper

- **Affixes.** Prefixes and suffixes on found gear ("Keen", "of the Bear", "of Warding") drawn from a table by band;
  identifying reveals them. Rarity colours: common, fine, rare, relic.
- **One unique per band**, guarded by the band's set piece, each with a line of lore and a mechanic of its own
  (e.g. the Drowned Town's *Tidecaller* - frost spells also put a foe to sleep).
- **Relic sets.** The nine guardian relics already exist; wearing two/three from adjacent bands wakes a set bonus.
- **Alchemy at the camp.** Ingredients from the Deep's bands (spore caps, crystal dust, foundry slag, grave salt)
  plus potions -> stronger potions, oils (a weapon's element for one fight), bombs. Gives the Deep's floors loot
  identity.
- **The smith, extended:** re-roll one affix (gem + gold), salvage gear into scrap for enchanting.

---

## Phase 4 - The party, wider

- **Three new callings,** unlocked by achievements so the title's eight stay the start:
  - **Monk** - unarmed, fast, dodges; "Flurry". Unlock: *Unfallen*.
  - **Necromancer** - raises a fallen foe to fight one fight; curses. Unlock: slay the Bone Patriarch.
  - **Artificer** - places a turret/ward that acts each round; repairs gear. Unlock: slay the Foundry Master.
  Each with two paths at 5/10, like the eight.
- **A third path tier at level 15** for every calling (one capstone trait per path) - the Deep's levels currently
  have nothing new to give.
- **Party bonds.** Heroes who've fought together long enough get a pairing trait (the Knight guards the Mage
  without being asked; two who've both fallen and risen share Second Wind). A few lines of banter in the log at camp.
- **Memorial.** A hero who falls for good is written into the Hall of Fame by name; their heirloom can be left in the
  vault automatically.

---

## Phase 5 - The dungeon, stranger

- **Choice events** on the floor (a shrine that wants blood, a chained prisoner who might be a monster, a gamble
  table, a cursed fountain that grants a boon) - small risk/reward dialogs, a dozen to start, data in `CM.EVENTS`.
- **Band hazards in the Deep:** the Drowned Town's tides (some squares flood and drain on a step count), the Fungal
  Deep's spore clouds (poison while standing in them), the Crystal Caverns' mirror walls (bolts bounce), the
  Foundry's vents (fire on a beat), the Ossuary's bone piles that stand up, the Root's shifting walls.
- **Multi-floor puzzles:** a key on floor N for a vault on N+2; a lever that drains the floor below.
- **A wandering merchant** (rare, any floor) with one odd item, and a **rival party** - another band of
  adventurers, sometimes helpful, sometimes after the same relic.
- **More set pieces and lair layouts** in `CM.TEMPLATES` - the generator already takes them as data.

---

## Phase 6 - The look, and the sound

- **Lit stone.** Use the normal and roughness maps already kept from ambientCG in the Stone theme: per-pixel
  torchlight, wet sheen in the Vaults. Pack size goes up - pack at 256 px and measure the built file.
- **Render scale** setting (and auto: drop scale if frame time > 20 ms); the view is soft at 1280x800 today.
- **Monster idle frames** in the Drawn theme (breathing, a twitch of the tail) and a short entrance for each
  guardian (a slow camera push and a title card).
- **Music:** a stinger when a leader or elite appears; the band's tune gains a layer the deeper into the band you go.
- **Spatial sound:** pan monster calls by direction, not only by distance.

---

## Phase 7 - Everyone can play - DONE in v1.1 (gamepad remapping: A/B swap only)

- Settings: **text size** (3 steps), **reduced motion** (no shake, no flashes, no colour washes; respect
  `prefers-reduced-motion` by default), **high-contrast** UI, status shown by icon *and* letter, not colour alone.
- The log as an ARIA live region; every dialog reachable and closable by keyboard and pad (mostly true - audit it).
- **Layout for small screens:** the view on top, party as a 2x2, log collapsible, buttons as a thumb bar. Today there
  is one `@media` query.
- **Gamepad remapping** alongside the key remapping.

---

## Phase 8 - Around the game

- **Share a run:** the summary card gets a short code (seed + mode + difficulty + party) that "Play this seed"
  accepts from the clipboard.
- **Weekly challenge:** a fixed seed, party and mutators for the week (from the date, like Today's), its own board.
  With Phase 0's seeded fights it's genuinely the same run for everyone.
- **New mutators:** Glass Cannon (double damage both ways), Pacifist-ish (no XP from kills, XP from exploring),
  One Hero (a party of one, scaled), Famine (no camps but the guardians').
- **Ghosts of past parties:** a party that fell on floor N in an earlier run may be found there in a later run on
  that seed - their bones, one of their items, a line from the Hall of Fame.
- **Backup:** Export also offers a file download; Import reads a dropped file.

---

## Order, and what each costs

| Phase | Size | Depends on | Notes |
|-------|------|------------|-------|
| 0 Foundations | M | - | Do first. Fixes a real save-loss risk. |
| 1 Quality of life | S-M | 0 (notes go in the delta) | Biggest felt improvement per line. |
| 2 The fight | L | 0 (sim, split) | Re-balance with the sim; expect two passes. |
| 3 The hoard | M | 2 (resistance table) | |
| 4 The party | L | 2, 3 | Three callings is the single biggest content add. |
| 5 The dungeon | M | 0 | Independent of 2-4; can run in parallel. |
| 6 Look and sound | M | - | Watch the built file's size (1.8 MB today). |
| 7 Accessibility | S | - | Could ship alongside Phase 1. |
| 8 Around the game | S-M | 0 (seeded fights) | |

Suggested sequence: **0 -> 1 + 7 -> 2 -> 3 -> 5 -> 4 -> 6 -> 8**, bumping `VERSION` to 1.1 after Phase 0 and to 2.0
when Phase 4 lands.

## Risks

- **Save compatibility.** Every phase adds to the save. Phase 0's migration chain and the per-phase fixture saves
  in CI are the guard.
- **File size.** Normal maps and more tiles grow the one file. Budget: under 4 MB built; `build.py` should print a
  warning above it.
- **Balance drift.** New callings, affixes and combos compound. Nothing merges without a sim run on all three
  difficulties.
- **Determinism.** Seeded fights mean any change to combat order changes every seed's outcome - fine, but the daily
  and weekly boards should record the build they were played on.
