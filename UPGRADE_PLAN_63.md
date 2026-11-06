# Upgrade plan 63: the sky in the deep - water, rockfalls, steam and fire, the beasts that move, the drafts and the clutter

Asked for 2026-11-05 as four sets of upgrades, with the standing rule that none of them may soft-lock a run. This
plan says what each set becomes in this game, what already exists to build on, where each could trap the party and
how that is ruled out, and the order of work. Nothing here is built yet.

## 0. What is already there (plans 61 and 62)

- The sky reaches below: `CM.aboveNow` (any floor), the flood of the sunken rooms of floors 1-3 after a heavy storm
  (`CM.floodNow`, `floodedAt`, knee-deep water drawn, a minute more a step, lightning chains through it), the drips
  and the grates' waterfalls, the draft that gutters the torches, the lightning through the grates, the steam in the
  fire bands (76zzzzzzzzzzn-below.js, 69zzq-below.js).
- The four magical fogs on every floor with their statuses (69zzo-fogs.js).
- The meteor's shock felt below (69zzn-meteors.js), the trees' fire above (69zzm-trees.js).
- The plants below ground by band - moss, weeds, fungus, roots - as instanced meshes (69zzs-plants.js); the rat has
  a body (plan 60); drips, dust, haze, the flooded and haunted moods, the sunken rooms (69zzi-levels.js).
- The torch gutters in a gust and relights after three steps (69v-weather.js); a doused light is dark but the party
  always has the spell light and the floor's own lit rooms.

## 1. The soft-lock rules (every feature below is checked against them)

| Rule | What it means in code |
|---|---|
| **A way always stands** | Nothing solid is ever added on the only path between the party, the stairs down, the way up, the camp and every key, boss and chest. Before a block is placed, `CM.distances` from the stairs is run with the block in; if any of those squares falls out of reach, the block is not placed there. |
| **Every block clears** | Debris is cleared by standing before it and pressing Space - a few minutes of the clock and some torch, never an item - and clears itself after a day of the clock whatever the party does. |
| **No hazard is unseen and unavoidable** | A hazard is drawn, named on the look line, costs at most a few points a step, never kills (never below one hit point), and never covers the only path (the same reach check). |
| **Never dark for good** | A draft that blows the torch out relights it in three steps as the gust does; the spell light and the lit rooms are untouched; a floor's lamps and braziers are never all out at once. |
| **Fights stay winnable** | A migrated or stirred monster group is drawn from the floor's own level band (the tables by floor), never from deeper, and never more than the floor's largest group; nothing spawns on the party's square or between it and the way up on the first floor. |
| **The clock, not the step** | Every event here runs on the clock (`CM.tickClock`) like the weather, so standing still never freezes a hazard in place, and every state lives in `game.ext` and saves. |
| **Off switches** | Each system has a Settings toggle beside the weather's, and the harness has a force hook, so a run in trouble can be stepped out of and a bug found. |

## 2. Set 1 - structural and environmental infiltration

### 2.1 Water basins and currents
- **What exists**: the sunken rooms of floors 1-3 flood knee-deep after a heavy storm and drain over a day.
- **Build**: a second depth. At `floodNow` 1 the sunken rooms are waist-deep (`CM.floodDepth(game, fl, x, y)` 0 /
  1 / 2): waist-deep water slows two minutes a step and the walk pace x2; fire spells cast from it or at a foe in
  it sputter (the water terrain's half already does this); the "water" terrain tag lets lightning chain. Submerged
  hazards: on a flooded square a **spike grate** (a feature the generator places in a few sunken rooms, harmless
  when dry: a drawn grating) bites a point a step while flooded, said on the look line ("the water hides a
  grating: a point a step"); **leech mobs** are a monster group that forms only on flooded squares (Giant Leech,
  the floor's level, two or three) and is gone when the water is; **sunk chests** are an ordinary chest the flood
  reveals (drawn as a basin, opened when the water is below knee-deep - or dived for at the cost of a few minutes).
- **Soft-lock checks**: the flood never adds a solid square (rule A holds by construction); the spike grate is
  placed only in a sunken room with two doors so the room can be crossed on the dry side (rule C), and never on the
  stairs' square; a sunk chest is reward, not a block.

### 2.2 Ceiling collapses and rockfalls
- **Build**: `CM.rockfallStep(game, minutes)` on the clock: the chance a minute rises with the rain's strength over
  the last hours (`CM.mudNow` is that number) on floors 1-4, with a gale above, and for an hour after a meteor's
  shock; it picks a **corridor square** (not a room, not a door, not a feature) of the party's floor within twenty
  squares, runs the reach check with it blocked, and places a **debris** thing on it: drawn as a heap of rock
  (meshes from the pack's rocks, several), the ceiling above it broken, dust falling, a crack and a rumble heard
  (the weatherscape's). Walking into it: "A fall of rock. (Space to clear it)"; clearing takes 20 minutes of the
  clock and a torch step or two, the heap gone, the square open (a pickaxe in the bag halves it, never needed).
  It clears itself after a day. Never two falls within six squares of each other, never more than three a floor.
- **Soft-lock checks**: rule A by the reach check from the stairs (and the way up, the camp, every key and chest
  and the boss' room) with the fall in; rule B by the clearing and the day's limit; never on the first floor's way
  up within six squares of the shaft.

### 2.3 Steam and the dry roots
- **Steam** (exists as a sight in the fire bands when wading or dripping): build the fight's side - a **steam
  terrain tag** on a square where the Foundry's or the Furnace's heat meets water or a drip under a cold sky
  (winter, snow, or a cold band above): ranged attacks (the party's bows and the foes' "ranged" ability) hit at
  three quarters; the "ambush" sight rule (the mist's) reads it as a dense mist, one square. Drawn as the steam
  puffs thickened to a white screen on those squares.
- **Dry roots** (the Root of the World, and the root-walled squares plants placed): in a **heat** event above, the
  roots are dry (`CM.rootsDry(game)`): a fire spell in a fight on a root square sets the **walls alight** for the
  fight - the fire's damage x1.25 to every foe (the room burns), the roots drawn burning (the tree-fire layer along
  the wall), smoke, and the root plants on those squares charred for the day. Never a harm to the party (the
  standing rule: fire is a sight to the party).
- **Soft-lock checks**: both are modifiers, never blocks; steam never covers the stairs' square.

## 3. Set 2 - the ecology and the beasts

### 3.1 Weather-driven migrations
- **Build**: `CM.migrationNow(game)` from the sky: in a storm or a tornado above, the first two floors' wandering
  groups (the "monsters" things not yet fought, within reach of the party, not a boss' or a guardian's) are
  **reseeded from the surface's beasts** for the event's length - wolves, bats, foxes, the Wood's goblins - at the
  floor's level, the same group size; said once ("Wet fur and wild eyes: the storm has driven the beasts in off the
  land."). When the sky clears they go back to the floor's own kinds (groups already met stay as fought).
- **The deep stirs**: on a flooded floor (floods, or the Flooded Vaults in rain above) the water's own kinds -
  the Drowned, slimes, a new **Mud Elemental** (a Rootling variant, mud-brown, the slow strike) - are **active**:
  their groups wake a square sooner (the ambush rule's reach +1), strike first more often (the sure first round at
  a third), and one group in three has a leech or two added. Never a kind from a deeper band.
- **Soft-lock checks**: rule E by the tables (the surface's beasts at the floor's level are weaker than the floor's
  own worst); a group never reseeds while the party stands beside it; a fight in progress is never changed.

### 3.2 Fungal and flora blooms
- **Build** on 69zzs-plants.js: a **bloom** state per band from the rain above (`CM.bloomNow(game)` 0..1 over the
  last day of rain): the fungus and moss meshes' density x(1 + bloom), and three new things of the bloom -
  **glowcaps** (a lit mushroom cluster: an extra light, pale green, reach 2, on a few wall-side squares - a light
  source the party can read by, drawn as the plant mesh with glow), **spore patches** (a drawn pale patch on a
  square; a step through it: a point of poison to each hero, never below one, said on the look line; it dies in a
  day), and **moss carpets** (cosmetic, the moss plants thick, the footsteps softer). The blooms fade over the day
  after the rain.
- **Soft-lock checks**: spore patches are placed only on squares with an open neighbour on the same path (the reach
  check with the patch counted as a wall must still reach everything), never on the stairs, never in a corridor one
  square wide; a point a step, bounded (rule C).

## 4. Set 3 - pressure, drafts and the fogs

### 4.1 Drafts, the torch and the gas
- **What exists**: a gale above gutters the lights below (v78); the torch goes out in a gust above for three steps.
- **Build**: in a tornado or a gale above, the **draft** has a way through the floor (from the shaft's square along
  the corridors: `CM.draftPath(fl)`): on those squares the haze streams (the air parts drift fast), the smoke runs,
  and the party's torch has a chance a step of going out for three steps (the existing gutter, never longer, never
  the spell light); **spore gas** (the bloom's patches, if any) is **blown** a square along the draft each ten
  minutes, never onto the stairs or into a dead end's last square.
- **Soft-lock checks**: rule D (three steps, the spell light untouched, the lit rooms untouched); the gas moves but
  never multiplies and always leaves the square it was on.

### 4.2 Magical fog seepage
- **What exists**: every fog is on every floor with its status.
- **Build**: the fog **pools**: in a sunken room (floor level below zero) the fog's strength is 1 and its picture
  thick (the billows dense, the sight one square for the ambush rule); in a raised room it is half. The statuses
  follow the strength as they do above. A fog pool in a sunken room is said when entered ("The violet fog lies
  thick in this low hall.").
- **Soft-lock checks**: none added - the fogs already have none (statuses are bounded, the green's poison never
  below one).

## 5. Set 4 - the clutter

- **Stalagmites and stalactites** (meshes, three sizes each, made in the pack's style - no source has them, so they
  are modelled in code: a cone of eight sides, the palette's stone greys): stalagmites on open squares' edges and
  corners (never the middle of a corridor one wide), stalactites on the ceiling over them, dripping; in the Crystal
  Caverns crystal-coloured.
- **Water**: leaks running down the walls in streaks (the rain's streaks already in the shader, keyed to the damp),
  drips with rings where they land (the drip kind's splash), a trickle along a corridor's gutter (a thin water
  decor strip on the floor's edge in the damp bands), drainage **pipes, ports and grates** in the walls' feet
  (decals: a round port, a barred grate, a pipe's mouth with a drip), and a hose or chain hanging from a ceiling
  ring here and there.
- **Rocks and rubble** along the walls (the pack's rocks small, from 69zzs-plants.js's placer), **spiderwebs** in
  the corners (a decal on the two walls of a corner, more in the Catacombs and the Crypt), **bugs** (an air kind
  of tiny dark parts that crawl on the floor and walls near the party and scatter from it, non-combatant), and
  **rats that scurry** (the rat figure, small, at the corridors' edges, running off two squares when the party
  comes within two, never fought, never in the way - the pet system's follower logic in reverse).
- **Soft-lock checks**: all cosmetic; rule A holds because none is solid. Density by the Detail setting and the
  plants' reach.

## 6. Order of work (each a release)

1. Set 4's clutter (stalagmites, drips and pipes, webs, bugs, rats): all sight, no rules, the quickest win and the
   base for the rest's drawing.
2. Set 1.1 the water basins (the second depth, the spike grates, the leeches, the sunk chests) with the reach checks.
3. Set 1.2 the rockfalls with the clearing, the day's limit and the reach check from every square that matters.
4. Set 2.2 the blooms (glowcaps, spore patches, moss carpets) and Set 3.1 the drafts and the blown gas together.
5. Set 1.3 steam and the dry roots; Set 3.2 the fog pools.
6. Set 2.1 the migrations and the stirred deep.
7. The pass: every system under every sky in the harness, the Settings toggles, the soft-lock test (a run of fifty
   floors under forced storms, floods, rockfalls and blooms, with the reach from the stairs asserted every floor).

## 6a. Progress

- v82.0 - release 1, the clutter: 69zzt-clutter.js (CM.clutterModels - stalagmite and stalactite cones of three
  sizes in the plants' model shape; CM.clutterOf at the walls' feet and corners, off the middle of a narrow way,
  stalactites at the ceiling's height; CM.clutterDecals by band - ports, grates, pipes, webs in corners;
  CM.clutterRats' corridor homes), merged by 69zzs-plants.js into the plants' instances with the stone tinted grey
  (blue in the Crystal Caverns); 76zzzzzzzzzzr-clutter.js (the cones ride with the plants through CM.Plants.parse,
  the decal pictures, the pipes' drips, the bugs that scatter from the party's feet, the rats that scurry two
  squares off along the corridor and go home when the party is far). Fixed on the way: a set painted ahead in the
  art worker now goes through the window files' build hooks (CM.art._prebuilt, 36-looks.js and 80-main.js), and
  CM.rebuildArt makes the floor's set again when the plants' pack arrives after it. Not done: the water leaks and
  trickles (the walls' streaks need the surface's wet uniform; a later look).
- v83.0 - release 2, the water basins: 69zzu-basins.js (CM.floodDepth 0/1/2 by CM.floodNow against
  BASINS.waistFrom; burn and walkPace wrapped for the deep water - two minutes a step, the pace doubled; the
  grating and the sunk chest furnished on a floor's first visit, not at its making, so the generator's fingerprints
  and the save's deltas hold: a "grate" feature two squares in from a sunken room's edge of five squares' width or
  more, a sunken room's chest marked sunk one room in three; arrive wrapped for the grating's bite, a point each
  when flooded, never below one, harmless and said when dry; CM.leechStep on the clock while wading waist-deep -
  a poison of four, cleared by any healing; use wrapped for the dive, a quarter hour while the water stands).
  76zzzzzzzzzzs-basins.js draws the grating flat (dark and dim under water), the chest's basin, splashes the deep
  step and names the depth on the sky bar. The test asserts every square still reachable from the stairs with the
  grating counted as a wall.
- v84.0 - release 3, the rockfalls: 69zzv-rockfalls.js (CM.ROCKFALL; CM.isOpen wrapped so a "debris" thing is a
  wall for the walk, the pathing and the monsters but not the map; CM.rockfallAt with every refusal - a room, a
  thing, a feature, the party's square or its neighbour, six of the way up on the first floor, six of another
  fall, three a floor, and wayHolds(): every square reachable from the stairs before must be reachable with the
  fall counted as a wall; CM.rockfallStep on the clock by the mud's number, a gale above and the hour after a
  meteor's shock, said near or far, clearing itself after a day; move wrapped to say the block, use wrapped to
  clear it - twenty minutes and two torch steps, a pick named if carried but never needed). 69zzs-plants.js heaps
  four of the pack's rocks on a fall. 76zzzzzzzzzzt-rockfalls.js: the shake, the crack, the dust burst and the dust
  sifting from the broken roof over it, the look line's "a rockfall ahead (Space to clear)".
- v85.0 - release 4, the blooms and the drafts: 69zzw-blooms.js (CM.bloomNow from the rain over the last day;
  CM.bloomStep on the clock - the density quartile, the sprouting once a floor a day with wayHolds for the spore
  patches, the day's life, the blown spores along CM.draftPath; CM.glowcapNear into hasLight; the spores' bite in
  move; CM.draftNow by the wind above and the depth; the torch snuffed with the gust's own gutter, never the spell
  light). 69zzs-plants.js's dungeon density follows the bloom. 76zzzzzzzzzzu-blooms.js draws the glowcaps (a wall
  decal with a green light), the spore patches (a flat picture, spores drifting), the draft's wind and haze and
  the look lines.

## 7. Decisions taken (2026-11-05, on the plan's own suggestions)

1. Rockfalls block corridors only, never a doorway or a room.
2. The spike grate bites a point a step, no wound.
3. Leeches are a status: standing in waist-deep water a while, a hero may be found with a leech (a bleed of a point
   a round in the next fight until pulled off at the camp or by any healing) - no new monster.
4. The migrations touch the first two floors.
5. The scurrying rats are the rat figure, small and grey.

## 7a. Decisions to take (as asked)

1. Should rockfalls block only corridors, or rooms' doorways too (never, by this plan)?
2. The spike grate's bite: a point a step, or a point a step and a chance of a wound?
3. Leeches: a monster group, or a status (bleeding) from standing in the water a while (cheaper to build)?
4. The migrations: the first two floors, or every floor with a grate (the daylit ones)?
5. Rats that scurry: the pet-rat picture, or a smaller grey rat of its own?
