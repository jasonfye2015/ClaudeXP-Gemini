# UPGRADE_PLAN_65 - Stage pieces and dressed rooms, the second thirty

A list to choose from, in the shape of plan 64's: curated rooms placed by `CM.planFloor`'s wrap (one set piece a
floor in three, its own dice), each a template with a letter or two of its own, a line of lore on entering, a thing
with a Space action, and a bounded danger. Plan 64's thirty are done (v86-v89); this list is what comes after it, and
it leans harder on the systems the game already has - the weather and the calendar, the meteors, the floods and
rockfalls, the plants and the figures, the ledger, the memorial, the pets, the town - and on **stage pieces**: rooms
whose point is a sight built from several squares (meshes made in code, as the clutter's cones are), not only a thing
on one square.

## 0. The rules every room keeps (plan 64's, kept)

- Every ring has a plain `D` on an odd square; nothing inside is solid but what the plan says (trees, a troll); every
  hazard is bounded (never a floor lost, never below one hit point, every pit closes, every sleeper can be walked
  round); every fight is chosen, never stumbled into; the generator's reach check stays the last word.
- Rooms keep `{x0, y0, x1, y1, name}` only; everything else is rebuilt from the template (`CM.fillOf`) and dressed
  on `makeFloor` (`CM.dressSetPieces`) through `CM.SETPIECE_LETTERS`. Things that need the game (the memorial, the
  pets, the ledger) read it at use time, not at dress time.
- A thing type needs a `CM.thingSprites` entry or it is invisible: every room ships with its pictures (the lesson of
  v87-v89).

## 1. Stage pieces (the sight is the room)

1. **The Giant's Ribcage** - 7 x 13. A colossus fell here: ribs arch over the whole room (cones and arcs made in
   code, in the plants' mesh shape, like the clutter's stalagmites), a skull at the far end the size of a cart with
   a chest between its teeth. Bats. The Ossuary and the Catacombs. Danger: the Bone Colossus kind stirs if the chest
   is taken at night (a sight by day).
2. **The Shipwreck** - 9 x 9. The Drowned Town: a hull broken through the vault's roof, its ribs and mast across the
   room, water (`~`) round it, fish, the captain's cabin a niche with a strongbox and a chart (a scroll of mapping
   for the floor below). The Drowned stand on the deck, still, and come down only if the bell on the mast is rung.
3. **The Fallen Star** - 9 x 9. A crater in the floor (`V` ring, the meteors' crater picture from plan 61), the star
   itself in the middle: a lump of star-iron hot to look at. Pick it with the miner's pick (plan 42's ore): star
   iron, an ore of its own for a weapon that never dulls. The floor's air shimmers (the heat-far shader). Any band
   from the twelfth floor.
4. **The Petrified Wood** - 9 x 9. Trees turned to stone (the plants' tree meshes, grey, no sway, no leaves), a
   stone deer among them, a stone adventurer with a stone hand out. A basilisk's work: the room's Stone status is
   bounded to one hero for one fight, cured at the fountain in the middle. The Crystal Caverns and the Root.
5. **The Rope Bridge** - 3 x 15. A chasm across the room (a sunken band of `V` three deep, dark), one rope bridge over
   it that sways as the party walks (the camera's roll, the Tilting Floor's hook) and creaks. Nothing falls; a chest
   hangs under the far end on a rope, pulled up with Space. Wyverns pass under the bridge now and then (air parts).
6. **The Waterfall Hall** - 7 x 9. The aquifer comes through the wall and down into a pool (`~`), spray in the air
   (plan 61's steam and drips, loud), lilypads, a cave behind the fall with a chest (walk through the curtain:
   wet, torches out for a turn). The Flooded Vaults and the Drowned Town; the storm above makes it roar.
7. **The Great Mushroom** - 9 x 9. One cap the size of the room on a stalk in the middle (a raised `R` disc you climb
   by steps), glowcaps round the foot, spores thick (the blooms' spore cloud, bounded). Sporelings under the cap.
   The Fungal Deep. Standing on top: the floor's map for twelve squares round.
8. **The Lantern Shaft** - 5 x 5, tall. A shaft up through every floor above (a lit grate chain: daylight comes down
   it, the weather too - rain falls in the middle of the dungeon). A rope ladder up it to a ledge with a chest; at
   night the moon lights the square. Floors 2-8.
9. **The Sunken Chapel** - 7 x 9. Plan 64's Drowned Chapel vault's cousin: half flooded, pews under water, a bell
   under the water that rings when dived for (plan 63's dive) - and rings the floor's drowned to the chapel, or, on
   a holy day (the calendar's festivals), blesses the party instead.
10. **The Throne of the Hollow One** - 7 x 11. The Root of the World: a throne grown from roots, the Hollow One kind
    on it asleep, roots across the floor (the dry roots that burn, plan 63). A crown on its head: take it (a relic
    of the band) and it wakes; burn the roots first and it cannot rise for three turns.

## 2. Trials (a rule to learn)

11. **The Hourglass Room** - 7 x 7. A great glass in the middle, turned by Space: sand runs for twelve turns of the
    clock and three chests round the room open only while it runs. Nothing closes on the party: the chests seal
    again, and the glass turns again (once a day).
12. **The Riddle Gallery** - 5 x 9. Three statues, each asks one of the game's riddles (the riddle doors' list) when
    passed; three right and the far chest opens; a wrong answer wakes the statue (a Gargoyle, bounded to one).
13. **The Pendulum Hall** - 3 x 13. Blades swing across the hall on a beat (the foley's beat, drawn): step on the
    off-beat (Space to wait a beat) and pass; step on the beat and take a bounded cut (-3) and be thrown back a
    square. The chest at the end is worth the timing.
14. **The Dark Room** - 9 x 9. Every torch goes out at the door (the drafts' snuff) and will not light; only a
    light spell or a glowcap carried shows the walls. The exit is on the far side; the floor is plain. A
    Shadow-kind group hunts by sound: stand still a turn and it loses you.
15. **The Frozen Pond** - 9 x 9. Ice over water: a step keeps going till a wall or a thing stops it (the spinner's
    cousin, drawn as a slide). Chests on islands of stone reached by sliding right; the ice never breaks.
16. **The Wind Tunnel** - 3 x 15. A draft that roars (plan 63's drafts, strongest): torches out, the party pushed a
    square back every third step unless it carries a lantern or walks along the wall (the side squares). A chest in
    the eye of the wind at the far end.
17. **The Counting Room** - 7 x 7. Gold on every square of the floor (a sight: coins drawn), take what you like - but
    the door's gate closes behind the party at a weight (the pony's carry rule) and opens only when enough is put
    back on the altar. Never a lock: the altar always takes.
18. **The Crawlway** - 9 x 9. The levels' crawl height over the whole room (plan 60's crawl), pillars, a low chest,
    and Giant Rats that fight at a crouch (the party's shields do nothing here, its daggers double).
19. **The Weighing of Deeds** - 7 x 7. A cousin of the Weighing Room: the scale weighs the ledger - the party's deeds
    this run (fights fled, chests opened, hermits helped, from `game.tally` and `CM.chronicle`) - and the relic goes to
    a party whose good outweighs; otherwise a curse-free "not yet" and the scale waits.
20. **The Dice Room** - 5 x 5. The Joker's: a stone die the size of a stool, thrown with Space for a stake of gold:
    six and the stake is tripled and a chest opens; one and a Mimic hatches from the die's box. Once a day.

## 3. Lairs and dens

21. **The Rat King's Nest** - 7 x 7. Rats on every square (the clutter's rats, many, scurrying), a nest of rags in
    the middle and the Rat King on it (an elite Giant Rat with a crown: the fled foes' trinkets in the nest -
    plan 30's fetch pile). The Catacombs and the Kitchen's cousin.
22. **The Hatchery** - 7 x 9. Wyvern eggs on warm sand (the steam's heat), six; take one (an egg to sell, or to
    hatch at the farm in forty days: a wyvern figure that follows, a pet) and the mother comes down the shaft.
    The Foundry and the Caverns.
23. **The Bandit Camp** - 9 x 9. A fire in the middle, Sellswords and a Hedge Wizard round it, a loot pile: the
    rivals' parley (plan 24) - pass the fire with a toll, trade, or fight; they remember.
24. **The Vampire's Parlour** - 7 x 7. The Lich King's palace: a parlour with a coffin, a table set for guests, a
    mirror that shows no one. Sit (Space at the table) and a Vampire wakes and offers a bargain: blood for a relic
    (-5 max hp on one hero for the run, a relic of the band); refuse and fight.
25. **The Golem Forge** - 9 x 9. The Foundry: a Crystal Golem half made on a slab, the furnace's vents, a lever
    that finishes it - and it fights for the party for one floor (a follower that leaves at the stair), or, if the
    lever is thrown twice, against it.
26. **The Drowned Shrine** - 7 x 7. The Drowned Town: the Drowned kneeling round a sea-stone, still; a pearl on the
    stone (the Cave Pearl ingredient, a rare one). Take it and they rise; put a fish on the stone first (the Fish
    Pool's, the kitchen's) and they let it go.

## 4. Memory, story and the town (the chronicle's rooms)

27. **The Chronicle Wall** - 7 x 9. Murals of the party's own runs (the ledger, `CM.chronicle`): one panel a run,
    the deepest floor painted, the way it ended. A rubbing of a panel is a trinket that gives +1 to the stat that run
    lacked. Floors 6 and down.
28. **The Old Camp** - 7 x 7. A camp of the party's own from an earlier run on this seed (the `camps` record): the
    cold fire, a tent, what they left - a potion, a note in their hand (the memorial's epitaph), and the camp works
    as a camp again (a rest, once). Any band.
29. **The Festival Hall** - 9 x 9. Dressed for the calendar's nearest festival (plan 38's): lanterns at Lantern
    Night, green boughs at Thaw, skulls at the Hallows - a different room each month, and on the festival's own day a
    gift on the table and the leitmotif played. Floors 3-10.
30. **The Smuggler's Drop** - 5 x 7. A cache of town goods (the market's stock) behind a false door, with a mark on
    the chest: sold at the market they fetch double, and the trader asks no questions - but the Guild's man in the
    Square asks one, and the answer costs a day's standing.

## 5. Mechanics to add once

- **Meshes made in code** for the stage pieces (ribs, a hull, a mast, a stalk and cap, a rope bridge): the
  clutter's `cone` pattern generalised to arcs and planks, baked into the plants' model table at load.
- **A room's own weather**: rain, moonlight or daylight on the room's squares through a shaft (the lit grates'
  daylight, widened to a room), the Lantern Shaft's and the Fallen Star's.
- **A slide**: a step that continues (the Frozen Pond) - one move loop with the renderer's slide of the camera.
- **A follower for a floor** (the Golem Forge): the recruits' follower slot, leaving at the stair.
- **The beat** (the Pendulum Hall): a clock on the foley's tempo that the rules can read (`CM.beatOf(game)`).
- **The ledger read in a room** (the Weighing of Deeds, the Chronicle Wall): `CM.chronicle` and `game.tally`, read
  at use time.

## 5a. Progress

- v91.0 - release 1, the stage pieces with meshes in code: 69zzzd-stage.js - a small mesh kit (tubes along a path,
  boxes, domes, arcs; packed the plants' way and added to the model table at parse by 76zzzzzzzzzzy-stage.js, drawn
  untinted) and four rooms: the Giant's Ribcage (ribs every other square arching the hall, bats, a skull with a
  chest between its teeth - taken by day it is only a chest, by night the Bone Colossus kind stirs), the Shipwreck
  (the Drowned Town: a hull and a mast in a ring of water with fish, a raised deck, the captain's chart - a scroll
  of mapping - in the cabin's chest, a bell at the mast's foot that calls three Drowned down), the Rope Bridge (a
  chasm either side, solid and deep - never walked into - planks with their ropes, the view swaying at every step on
  the bridge, wyverns passing under it, a chest hauled up at the far end), the Great Mushroom (the Fungal Deep: a
  stalk and a cap on a raised disc with steps, glowcaps at the foot, Sporelings asleep under it; the cap's top shows
  the floor for twelve squares round). Letters 0 8 M A _ =.
- v92.0 - release 2, the weather-and-water stage pieces and two more: 69zzze-stage2.js - the Fallen Star (a sunk
  ring and the star, a vein of star-iron the pick mines), the Waterfall Hall (a curtain of water into a pool, the
  torch guttering a step through it, a niche with a chest behind), the Lantern Shaft (a grate feature for the
  daylight, a rope ladder, a chest on the ledge), the Sunken Chapel (pews under the water, a bell dived for: a
  blessing on a holy day, the Drowned otherwise), the Petrified Wood (stone trees and figures - the room's plant
  instances stand still and grey - a fountain, and a chest whose Gargoyle guard carries a basilisk's gaze: one hero
  stone for two turns, the fountain undoes it), the Throne of the Hollow One (the crown is the band's relic; held
  three turns when the roots burn). Letters + | @ ^ & % ! F Y.
- v93.0 - release 3, the trials 11-15: 69zzzf-trials.js - the Hourglass Room (the glass turned once a day, four
  sealed chests open for twelve steps), the Riddle Gallery (three riddle doors across the hall with statues in them,
  a wrong answer wakes a Gargoyle once each), the Pendulum Hall (one flag wide between two pits, blades on a beat,
  a bounded cut and a square back on the beat, Space waits a beat), the Dark Room (the torch guts inside it; shadows
  asleep; the far door the way on), the Frozen Pond (ice slides the party till a wall, a thing or dry stone; the
  slide's own steps unlogged so a replay slides again). Letters I ? J Z O. The riddles' experience follows the story
  floor now.
- v94.0 - release 4, the trials 16-20: 69zzzg-trials2.js - the Wind Tunnel (the torch out and a square back every
  third step on the middle way, a lantern stands, the walls' squares are still), the Counting Room (coins on every
  square taken by walking; past eight the inner gate drops; the altar takes a square's worth back at a time and
  lifts it), the Crawlway (crawl height end to end, rats asleep, a low chest), the Weighing of Deeds (the run's deeds
  against its flights: the relic, or "not yet" and no curse), the Dice Room (a stake of fifty on a stone die: six
  opens the chest, one is a Mimic, once a day). Letters E $ N U Q K and "," (the die: X is the old templates' dark
  floor).
- v95.0 - release 5, the lairs 21-26: 69zzzh-lairs.js - the Rat King's Nest (the clutter's rats, a crowned elite
  rat on a nest with a chest under it), the Hatchery (eggs worth selling; the first taken brings a Wyvern down, once),
  the Bandit Camp (a rivals thing at a fire: the rivals' own parley, with their pile a guarded chest), the Vampire's
  Parlour (Space twice: five of a hero's health for the run, the band's relic; the candlesticks a Vampire-guarded
  chest), the Golem Forge (the lever finishes the golem and it fights), the Drowned Shrine (flesh on the stone buys
  the pearl; bare, the Drowned rise). Letters P ( ) < > {.
- Decisions taken (release 5): the egg is a thing of value, not a pet (the farm's pets are a plan of their own); the
  golem never fights for the party (no follower slot for a golem); the vampire's bargain is two presses of Space,
  not a choice dialog.
- v96.0 - release 6, the memory rooms 27-30: 69zzzi-memory.js - the Chronicle Wall (ten panels reading the
  ledger's runs; a rubbing is a new trinket, +1 to the party's least stat, once a floor), the Old Camp (a dead
  hero's note from the memorial, an hour at the fire mends 30%, once), the Festival Hall (dressed on entering by
  CM.MEMORY_ROOMS.festivalOf - the run's festival, else the real month's - and the chest opens on the festival's own
  day), the Smuggler's Drop (a false-door niche with three things worth double). Letters [ ] : ;. Plan 65 complete:
  sixty curated rooms with plan 64's.
- Decisions taken (release 6): the smugglers' goods are gear with doubled worth, with no question asked in the
  Square; the old camp is this house's memorial, not a camps record by seed (none is kept).
- Decisions taken (release 1): the chasm is solid, not a fall (the soft-lock rule); the bridge sways in the view,
  the planks never give; the ship's Drowned come down only at the bell; the mushroom's cap is a dome round the
  party's feet on the raised disc, not a climb through the mesh.

## 6. Order (when asked)

1. The stage pieces with meshes in code (1, 2, 5, 7): one release for the mesh tools and four rooms.
2. The weather-and-water stage pieces (3, 6, 8, 9) and the Petrified Wood and the Throne (4, 10).
3. The trials (11-20), two releases.
4. The lairs (21-26) and the memory rooms (27-30).
