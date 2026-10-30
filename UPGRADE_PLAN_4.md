# Claude and Magic - the sixth big update: items and mechanics

Where the game stands (v4.0, after the fifth big update): fifty floors in ten bands, fourteen callings, a village,
magic with decisions in it, a story that speaks, three endings. The *things* in it, though, are much as v1.1 left
them: a weapon is a number, armour is a bigger number, a potion is one of five, and the camp's merchant takes
nine-tenths of every coin the party ever spends. This update is about **what the party carries and what it does
with it** - and about the rules that the carrying touches: locks, traps, light, hunger, wounds, gold.

Same shape as before: phases, each shippable with tests and a simulator run, each a version (v4.1 ... v4.9, and
v5.0 when the balance pass lands). Phase 0 again pays for the rest: nothing below can be measured until the bot
uses the bag.

---

## What is already there (and what it is made of)

| System | What exists | Where |
|--------|-------------|-------|
| Gear | 8 slots. 12 weapons, 5 bows, 12 armours, 6 shields, 6 helms, 6 rings, 6 amulets, 7 boots, 7 cloaks - each a *tier list*: a name and a number. Two-handed, bows, armour weight by tier, who may bear what. | `CM.WEAPONS` ... `CM.CLOAKS`, `CM.makeGear` |
| Affixes | 8 weapon prefixes, 6 armour prefixes, 14 suffixes; some only below the palace. Rarity by count (fine, rare). | `CM.AFFIXES`, `CM.affix` |
| The special | 10 uniques (one a band), 9 relics (one a guardian) with a set bonus, 4 gems, a smith who enchants to +3 or sets a gem. | `CM.UNIQUES`, `CM.relic`, `CM.SMITH` |
| Consumables | 5 potions, 6 scrolls, 4 wands, 3 oils, firepots, rations, torches and one lantern, rope, two elixirs. | `CM.SCROLLS`, `CM.WANDS`, `CM.RECIPES` |
| Alchemy | 10 ingredients (one a band, dropped by its monsters), 9 recipes, brewed at a camp. | `CM.INGREDIENTS`, `game.brew` |
| Identification | Half of found gear is `unknown` until worn, scrolled or shown to the scribe. | `item.unknown` |
| Containers | Chests (two things and gold; four traps), strongboxes two floors below their key, the peddler, the rivals' purse, the remains. | the generators, `CM.furnish` |
| Between runs | The vault (one, three or five heirlooms), salvage, the shrine's buried things. | `game.vaults` |
| The body | 6 statuses, hunger (rations), morale, light (steps), 3 elements, terrain and formations. | `CM.STATUSES`, `CM.HUNGER`, `CM.MORALE` |
| Money | 30 gold at the stair; chests, fights, selling. Spent at the merchant, the smith, the temple, the alchemist, the tavern, the bed. | `game.spend` |

Two numbers from the simulator that frame everything below (`node tools/sim.js --seeds 6 --to 25 --difficulty
fair`): **the merchant takes 92% of the gold spent**, and **the bot never uses forty-three of the abilities, nor a
scroll, a wand, an oil or a bomb**. The first says the economy has one sink. The second says the simulator cannot
yet tell us what a consumable is worth - which is the first thing to fix.

---

## What v4.0 invites

| # | Observation | Where | What it means for this plan |
|---|-------------|-------|-----------------------------|
| 1 | **A weapon is a number.** A mace and a sword of the same tier are the same thing with different names. Nothing in the fight reads *what* you swing. | `CM.makeGear`, `strike` | Weapon classes with one rule each; monster armour kinds that care. The fight gains a decision at the chest, not just at the smith. |
| 2 | **Gear has no provenance and no identity.** An item is `{name, kind, power, value, props}`; two Long Swords +1 are the same object twice. The save holds names, so a renamed base breaks old saves. | `CM.makeGear`, `25-saves.js` | Phase 0: a `base` id on every item, names derived; a history on the ones worth it; a compendium of every base seen. |
| 3 | **Affixes stop at two words and never scale.** "Keen" is the same crit at floor 3 and floor 43. Deep affixes are a flag, not a tier. | `CM.AFFIXES` | Affix tiers by depth; new families (on-hit, on-kill, conditional, party-wide); cursed affixes; sets. |
| 4 | **The bag is a list; a potion in a fight costs the turn.** No belt, no throwables, nothing used without opening the pack. | `75-bag.js`, `useMagicInBattle` | A belt of four, free once a round; flasks to throw; potion tiers; wands that recharge. |
| 5 | **Alchemy is ten drops and nine recipes, at the camp.** Nothing is gathered; nothing is brewed on the floor. | `CM.INGREDIENTS` | Gathering nodes placed by hash, a field kit, twenty recipes, poisons, cooking. |
| 6 | **Relics and uniques are passive.** Nine guardians' things and ten uniques, and none of them *does* anything you choose. | `CM.UNIQUES`, `CM.RELIC_SET` | Charged powers on relics; a trinket slot; weapons that grow and can be named. |
| 7 | **Locks are a key or a Rogue; traps are four messages; doors are open or shut.** | `61-explore.js` | Picks, trap kits, re-arming traps against monsters, barring doors, bait. The Artificer finally has a trade. |
| 8 | **Monsters carry nothing and have no bodies.** An elite is a multiplier. Three elements; every undead fears holiness the same way. | `CM.MONSTERS`, `CM.ELITES` | Loadouts on elites you can take; six elements with a matrix; parts that break off. |
| 9 | **Falling to zero costs nothing.** A Phoenix Feather and the hero is whole. Hunger and morale are the only lasting marks of a hard floor. | `62-combat.js`, `raiseDead` | Wounds: a lasting mark until the temple, and scars that become traits. Weight, so a pack is a choice. |
| 10 | **Gold has one door.** 92% to the merchant; the temple and the bed are rounding errors; nothing is scarce after floor 20. | the simulator | Sinks with decisions in them: orders, insurance, bounties, the fence, prices by depth; the merchant's stock rotates. |
| 11 | **The bot carries, and never uses.** | `tools/bot.js` | Phase 0: the bot equips upgrades, drinks, reads, waves and throws. Then every phase is measured. |

---

## Phase 0 - The ledger of things (do first) - v4.1 - DONE

- **Item identity**: every item gets `base` (an id into a new `CM.BASES` table that holds the old lists' names,
  tiers and kinds) and `mods` (the affix ids, the enchant, the gem, the element); `name` is derived by
  `CM.itemName(item)` and stored only for display. A migration (`CM.SCHEMA = 3`) reads `base` back from old
  names. Nothing a player owns changes.
- **Provenance**: `item.found = {floor, how}` (a chest, a strongbox, a foe, the peddler, the vault) and, on the
  things that will grow in Phase 5, `item.history = []`. The item card shows it: "found on floor 7, in the
  Drowned Hall".
- **The compendium**: a third journal page - every base ever found, by slot and tier, with the ones not yet seen
  as outlines (like the bestiary). Completion is a title, *the Collector*.
- **The bag, better**: sort by slot/tier/value, a filter row (gear / drink / read / stuff), *compare* on hover
  against what the hero wears for every hero (the arrows exist; make them stay), a "take all" at a chest.
- **The bot's bag**: it equips an upgrade when one is found (by `CM.compare`), drinks when a hero is under a
  third, reads a Scroll of Fire on three foes or more, waves a wand at an elite, throws what it can throw. The
  simulator gains `--loot`: gold found and spent by band, items found by rarity, floors to the first upgrade of
  each slot, consumables used and wasted.
- **Tests**: every old item name resolves to a base; a v4.0 save's party loads with the same stats; the bot's
  consumable use is non-zero on every band of ten seeds.

Size: M. The measuring stick for everything after.

## Phase 1 - Weapons and armour with character - v4.2 - DONE

- **Weapon classes**, one rule each, read in `strike`: *blade* (as now: the standard), *blunt* (ignores a third
  of armoured and undead defence; no crit), *axe* (cleaves: a second foe in the same row takes half), *polearm*
  (strikes from the back row; cannot be used in the front), *dagger* (strikes first in the round, crits double,
  two-thirds damage), *bow* (as now, plus: never blocked by a shield), *staff* (+1 spell power a tier, half
  damage), *fist* (the Monk's, as now). The old lists sort into classes: Mace and War Hammer are blunt, Battle
  Axe and Flamberge axes; three new bases join (a Spear and a Glaive for polearms, an Ashwood Staff).
- **Proficiency**: each calling is *at home* with two or three classes and *clumsy* with the rest (-15% to hit,
  no class rule). A second calling adds its classes. Shown on the card.
- **Shields block**: a shield has a block chance (a tenth a tier) that turns a blow to half; a tower shield blocks
  for the hero behind as well. Two-handers and bows cannot be blocked... they can, by a tower shield only.
- **Armour weight means something**: heavy armour -1 initiative and louder (the party is surprised more often
  unless a Quiet hero stands); light armour +1 initiative. Mithril is heavy armour at medium weight: that is why
  it was mithril.
- **Dual wield** for the Rogue and the Ranger: a dagger in the off hand, a second strike at half; no shield.
- **Monster armour kinds**: *flesh*, *hide*, *shell*, *bone*, *plate*, *none* on every kind (`CM.MONSTERS`), read by
  the weapon rules (blunt against shell and bone; blades against flesh; axes against hide).
- **Tests**: each class rule in a fixed fight; proficiency changes hit rate; the sim's time-to-first-upgrade does
  not lengthen (the chests now hold choices, not only numbers).

Size: L. The biggest change to the fight since terrain.

## Phase 2 - Affixes that grow, sets, curses, and the smith's second trade - v4.3 - DONE

- **Tiers**: every affix has three tiers (I at floor 3, II at 16, III at 31); the word stays, the number grows
  ("Keen" is 10%, 15%, 20%). Deep affixes become tier III of their family.
- **New families**: *on-hit* (bleed, chill, blind, a chance each), *on-kill* (gold, a sip of health, a point of
  mana to the party's casters), *conditional* (double against undead; against beasts; while under half health),
  *aura* (the whole party +1 defence while worn; the party's torch burns slower). About twenty words more.
- **Implicits**: every base has one small property of its own (a dagger's crit, a tower shield's block, Marsh
  Boots' dry feet - already there, now a rule, not a flag) so two bases of a tier differ before any affix.
- **Cursed gear**: a fourth rarity. A cursed item has a tier-III affix *and* a cost (a stat down, hunger faster,
  the torch burns twice as fast, a curse on the wearer each floor) and cannot be taken off until the temple lifts
  it (the service exists). Unknown gear is where curses hide: identification becomes a decision.
- **Sets**: three sets of three pieces (the Watch's - Captain Aldred's; the Masons'; the Order's), scattered as
  rare drops in their bands, each piece fine alone and the three together a real thing (the Watch's: the party
  wades dry and the wearer's blows chill).
- **The smith reforges**: a suffix rerolled for a gem and an ingredient; a prefix *moved* from one piece to
  another of the same slot (the old piece is scrap); salvage returns *essence* by rarity, and essence buys the
  reforge when the party has no gem. Enchant stays at +3; a tier-III affix is the new ceiling.
- **Tests**: tiers by floor over a thousand drops; a cursed item cannot be removed and the temple lifts it; a set
  bonus turns on with the third piece; reforge never produces a duplicate element.

Size: M.

## Phase 3 - The belt, and things to drink, read and throw - v4.4

- **The belt**: four slots beside the party, filled from the bag at any time; in a fight the first belt use a
  round is free (the hero's turn is not spent), the second costs the turn as now. Keys 5-8 on the keyboard, the
  d-pad with a shoulder held on a pad.
- **Throwables**: *flasks* - oil (fire on a foe's square and the one behind; on water, it spreads), acid (armour
  down for the fight), holy water (undead, with a chance to turn), smoke (the party flees for certain, once),
  and *the firepot* joins them. Thrown from any row.
- **Potion tiers** by depth: lesser / healing / greater / full; mana likewise; the merchant's stock follows the
  band. The Phoenix Feather gets a lesser cousin (half health, once a floor) so the full one is a decision.
- **Elixirs with duration**: stoneskin (a floor), haste (a fight), owl's eyes (the next three floors seen a step
  further), the night's draught (no sleep, no surprise, a floor). Brewed, bought at the peddler, found.
- **Scrolls** gain six: *recall* (to the last camp, and back by the same scroll), *knowledge* (this floor's
  carving read from where you stand), *banish* (one summoned thing gone), *sharpen* (a weapon +2 for a floor),
  *silence* (no spells on either side for the fight), *the lost page* (a random tome's spell, once).
- **Wands recharge** at the smith (a gem's worth a charge) and *break* on the last charge one time in four; the
  Artificer never breaks one.
- **Light as a thing**: torches as now; the lantern needs *oil* (a flask every two floors) but burns twice as
  long and a step further; *glow stones* from the Crystal Caverns never go out and light one square.
- **Tests**: a belt use is free once a round and not twice; a flask on water spreads; recall and back; the bot
  throws when three or more stand.

Size: M.

## Phase 4 - Gathering, the field kit and the kitchen - v4.5

- **Gathering nodes**: a thing placed by hash on ordinary floors (like a peddler): a moss bed, a weed pool, a vein
  of ore, a fungus shelf, a crystal growth, a bone pile - three or four a band, each yielding its band's
  ingredient and, one time in five, something rarer (`CM.INGREDIENTS` grows from 10 to 18: rarer things with no
  monster to drop them). The Druid and the Ranger see nodes a step further; the Artificer gets ore twice.
- **The field kit**: bought at the alchemist's (300 gold) or found in the Fungal Deep; with it, brewing on any
  floor at the camp's prices plus a fifth. Without it, the camp, as now.
- **Twenty recipes**: poisons for weapons (the Rogue's: three fights, a status a kind), the elixirs of Phase 3,
  flasks, a *salve* that heals over a floor, *dwarven bread* (a ration that also mends), the *liniment* that
  lifts a wound (Phase 8), the alchemist's four *transmutations* (three ingredients of a band into one of the
  next), and an *essence* draught for the smith.
- **The kitchen**: monsters of the right kinds drop *meat* (not the undead, not the crystal); at a camp or with a
  fire-flask on the floor the party *cooks*: a meal feeds the party and gives a small bonus to the next floor
  (boar: +1 Strength; cave fish: the torch lasts; wyvern: fire resisted). Hunger gets a reason to be more than a
  ration.
- **The alchemist's requests**: she wants three of something this run; bring it and the next brew is free.
- **Tests**: nodes by hash never move; the kit brews on the floor; a poison applies a status by kind; the sim's
  `--loot` shows ingredients gathered as well as dropped.

Size: M.

## Phase 5 - Living items: charged relics, trinkets, and weapons that grow - v4.6

- **Charged powers on the relics**: each guardian's relic gains a power, once a floor (the Rat King's Crown calls
  the swarm *for* you; the Shield of the Drowned raises the water; the Forge-Warden's Hammer breaks a foe's armour;
  the Queen's Ring lulls the room; the Mind's cap thinks a foe still; the Tyrant's shard reflects a spell; the
  Master's hammer reforges on the spot; the Reliquary Key opens a locked door; First Root regrows a fallen hero to
  one health). Used from the belt.
- **The trinket slot**: a ninth slot for small strange things with one passive oddity each - twenty trinkets: a
  rat's tooth (never ambushed by rats), a bell's tongue (the last bell's motif when a guardian telegraphs), a
  cook's spoon (rations feed one more step), a tally stick (+1 experience a kill), a child's chalk (the floor's
  carving marked on the map)... Found in strongboxes, from ghosts, bought from the peddler. The story's objects
  (the bell, the page) are trinkets when kept.
- **Weapons that grow**: a weapon that slays a guardian, or a hundred of anything, gains a *mark* (+1, and a line
  of history); at three marks the player may **name** it, and a named weapon is kept in the compendium with its
  story, carried to the vault for free, and found by a later party as a legend (the Aldous device, for steel).
- **Heirlooms with memory**: a vault item remembers its bearers; the third bearer of a thing wears it as a relic
  (the set bonus counts it).
- **Tests**: a power once a floor and not twice; a trinket's oddity in a fixed situation; a weapon's marks and
  naming survive save, vault and a new run.

Size: M.

## Phase 6 - Tools, traps, locks and doors - v4.7

- **Locks**: a *lockpick* (consumable; anyone may try at a third of the Rogue's chance, and a pick breaks on a
  miss); locks gain *grades* (a common lock, an iron lock a Rogue of level 4, a dwarven lock the Key or a master
  pick); the *Reliquary Key* and the Master's hammer open anything. Strongboxes get grades too.
- **Traps as tools**: a *trap kit* (the Artificer's trade): disarm a plate for its parts, and *set* a trap on a
  square behind the party - a monster group walking onto it takes the trap. Chest traps become six (a dart
  volley, a floor that gives way).
- **Doors you can bar**: a *bar* (a thing from a smashed chest or the smith) holds a door against wandering
  monsters for a floor; the party can rest at a barred door for a third of the camp's rest (once a floor, costs
  a ration each). Monsters *break* doors in three turns if hungry (the hordes mutator).
- **Bait**: a ration dropped on a square draws the nearest wanderers to it for ten steps; a poisoned ration does
  what it says.
- **Climbing gear and digging**: a *grapnel* takes the party up a pit it fell down; a *pick* (the dwarves') opens
  one secret stair's wall a band without searching, and breaks.
- **Tests**: a set trap fires on a group; a barred door holds and is broken; a lockpick's chance by calling; the
  bot picks, bars and baits where it should.

Size: M.

## Phase 7 - Monsters' things, and six elements - v4.8

- **Loadouts**: elites and the rivals' people carry gear (a Hulking Orc its axe, a Sellsword its sword and
  shield) that the fight reads (its weapon class, its shield's block) and that drops when it falls - the first
  loot that is *seen before it is won*.
- **Six elements**: fire, frost, holy, and now *storm* (named already in `CM.ELEMENT_NAMES`), *venom*, *shadow*,
  with a weakness/resistance matrix on every kind (`CM.MONSTERS.el`) and on the party's gear. Storm chains to a
  second foe in water; venom is the poison status with teeth; shadow blinds and is the Necromancer's.
- **Parts that break**: a dozen kinds have a *part* (the Hydra's heads, the Wyvern's wing, the Golem's arm, the
  Lich King's staff) with its own health; break it and the kind loses an ability for the fight and drops the
  part as an ingredient or a trinket.
- **Monster abilities** gain eight: *shield-wall* (a line of them: the back row cannot be reached), *howl* (morale
  down), *steal* (a thing from the bag, and it runs), *web*, *burrow*, *split*, *mimic* (a chest that isn't),
  *carry off* (a hero dragged a square: the formation breaks).
- **Tests**: a loadout's weapon class applies to the monster's blow; the matrix is symmetric where it should be;
  a part breaks and the ability goes; the mimic is a chest until it isn't.

Size: L.

## Phase 8 - Wounds, weight and the economy - v4.9

- **Wounds**: a hero who falls to zero rises (a Feather, the fight's end) with a *wound*: one stat down by one
  until the temple's new service or the liniment; a second wound before the first heals is a *grave wound* (two
  stats). Three wounds healed become a *scar*: a trait with a touch of good in it (the limp that never trips on
  a plate; the burned hand that fears no fire). The memorial keeps the scars.
- **Weight**: the bag has a weight, by strength summed (heavy armour and two-handers weigh most; potions nothing);
  over it, every step burns the torch faster and hunger comes sooner; far over it, no running. A *pack mule*
  is not in the plan; a *bag of holding* unique is.
- **The economy, rebalanced with the sim in hand**: prices rise a tenth a band; the merchant's stock *rotates*
  by the seed and the camp (no more everything everywhere); *orders* (pay now for a thing from the merchant's
  list, delivered at the next camp, a tenth over); *insurance* (a tenth of a thing's value at a camp: if the
  party falls, it goes to the vault); *bounties* at every camp (three of a kind, gold and renown); *the fence* at
  the tavern buys unknowns at half and cursed things at nothing, and sells rumours of strongboxes; a *tithe* at
  the temple (a tenth of the purse for a blessing on the band). The target: the merchant under 60% of spending,
  and gold that is a decision past floor 20.
- **Tests**: a wound and its healing; weight slows and the bag of holding doesn't; insurance pays out; the sim's
  `--loot` report shows the spending spread and the bot buying insurance when it can.

Size: M.

## Phase 9 - Around the things - v5.0

- **The balance pass**: fifty seeds a difficulty with `--loot`; the numbers in the README; the ladder re-measured
  (the rungs that touch gold and potions - *costly temple*, *poor veins*, *no greater potions* - re-tuned).
- **The item card** everywhere one is named: in the log, the chest, the shop, the vault, the compendium - with
  provenance, class, implicits, tiers, the set and the history.
- **Accessibility**: the belt and the compare arrows on a pad and a touch screen; colour-blind marks for rarity
  (shapes, not only colours).
- **Films** show the belt used and the thing thrown.
- **Text as data**: every new word through 12-text.js; `tools/words.js` counts the items' words too.
- README, plan status, the version.

Size: S-M.

---

## Order, size and dependencies

| Phase | Version | Size | Depends on | Notes |
|-------|---------|------|------------|-------|
| 0 The ledger of things | 4.1 | M | - | Item identity, provenance, the compendium, the bot's bag, `sim --loot`. Do first. |
| 1 Weapons and armour | 4.2 | L | 0 (bases) | Classes, proficiency, block, weight, dual wield, monster armour kinds. |
| 2 Affixes, sets, curses, reforge | 4.3 | M | 0, 1 | Tiers, families, implicits, cursed, three sets, the smith's second trade. |
| 3 The belt and consumables | 4.4 | M | 0 | Belt, flasks, potion tiers, elixirs, six scrolls, wands, light. |
| 4 Gathering and the kitchen | 4.5 | M | 3 (flasks, elixirs) | Nodes, the field kit, twenty recipes, cooking. |
| 5 Living items | 4.6 | M | 0, 2, 3 (the belt uses powers) | Charged relics, trinkets, named weapons, heirlooms' memory. |
| 6 Tools, traps, locks | 4.7 | M | 3 | Picks, trap kits, bars, bait, grapnel, the dwarves' pick. |
| 7 Monsters' things | 4.8 | L | 1 (classes, armour kinds) | Loadouts, six elements, parts, eight abilities. |
| 8 Wounds, weight, economy | 4.9 | M | 0 (`--loot`), 4 (liniment) | The sinks and the body; measured against the merchant's 92%. |
| 9 Around the things | **5.0** | S-M | all | The balance pass; cards; accessibility; films; words; docs. |

Suggested sequence: **0 -> 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8 -> 9**. Phases 3 and 6 could swap with 1 and 2 if the
fight's rewrite wants more room; nothing after 0 waits on anything but what the table says.

## Risks

- **Saves.** Every item in every save and vault is renamed by Phase 0's identity change. The migration is tested
  against a v4.0 export with gear of every slot, affixed, enchanted, gemmed, unknown and relic, before anything
  else ships; `CM.itemName` must reproduce every old name exactly.
- **The fight's rewrite.** Weapon classes touch `strike`, the most-read function in the game. Each rule lands
  behind its own test with a fixed fight, and the sim's crown rate on Fair is held within five points of v4.0
  until Phase 9 tunes it on purpose.
- **Power creep.** Tiers, sets, charged relics and trinkets all add; the ceiling is set once in Phase 2 (a
  tier-III affix) and nothing after it stacks past that - a named weapon's marks cap at three, a set's bonus is a
  rule not a number.
- **Weight and wounds can be chores.** Both have an off switch in the difficulty table (Gentle has neither;
  Grim has both) and both are measured: if the bot's floor-median drops more than two floors from them alone,
  they are tuned down before shipping.
- **The bot.** Every phase gives the bot its thing - equip, drink, throw, gather, pick, bar, buy insurance - or
  `--loot` measures nothing. Phase 0's bot work is the gate for the rest.
- **The frozen floors.** Nodes, loadouts and set drops go on by hash through `CM.furnish` and the fight, never
  through the generators; the gen fixtures stay byte-identical.

## Not in this plan, and why

- **A crafting tree with its own screen.** The smith, the alchemist and the kitchen are three short lists at
  the camp; a tree would want a screen the game's size doesn't have.
- **Durability.** Repair is a chore without a decision in it. Wands break; blades do not.
- **A pack mule or a shared stash across runs beyond the vault.** The vault growing with the guildhall is the
  shape; a stash would make every run the last run's shopping trip.
- **Charisma, or haggling.** A seventh stat touches every hero in every save; the Bard's price touch (Phase 8's
  fence) is enough.
- **Mounts, ranged aiming, a grid in the fight.** The fight is rows and reach, and stays so.
