# Claude and Magic - the tenth big update: a world with things in it

A plan for v8.1 to v9.0. The ninth update gave the surface a sky, a town and a forest; this one fills the view. Today
every square is bare: the dungeon is clean stone with a chest or a monster on it, the land is flat grass between
trees, and under the trees there is no ground at all - the mesh only lays ground on open squares, so between and
beneath the trunks you see the sky. This update lays ground everywhere, scatters the small things that make a place
look lived in or died in - grass and shrubs, rocks and rubble, bones, cobwebs, empty bottles - lets the floor remember
what the party did on it, varies the stone, lights the dark with the torches that are already on the walls, and puts
weather and motes in the air. No rule of the game changes: every prop is for the eye only.

The shape in one line: **look down any corridor or path and see a place, not a grid: ground under every tree, grass
and stones along the road, bones and rubble in the corners, the bottle you drank from where you dropped it, torchlight
on the walls and dust in the light.**

## Principles (every phase keeps these)

- **Props are for the eye only.** Nothing scattered blocks a step, hides a thing, or changes a fight. The party walks
  through a tuft of grass and over a bone.
- **Made from the seed, never saved.** Scattered props come from a hash of the seed, the floor and the square, the same
  every visit, and are never part of a save or a floor's fingerprint (`CM.floorPrint`), so no seed's floors move and
  no save grows. The one exception is Phase 4's traces, which are the party's own doing and saved as a short list.
- **Batched, not per frame.** The thousands of small things go into the floor's static mesh when it is built, like the
  walls; only what moves (grass that sways near the party, particles) is rebuilt per frame, and only near the party.
- **A Detail setting** (Low / Medium / High, Medium by default, and the automatic step-down when frames come late)
  scales how many props, lights and particles there are. Low is today's look plus ground under the trees.
- **Both looks.** Every prop has a drawn painter (as the surface's houses and trees do). Pixel shows it in pixels or
  uses a Crawl tile where one exists; Stone uses a photograph where one fits (a rock cut from the rock texture, a
  leaf from a leaf atlas) and the drawn one shaded otherwise.

## What is, and what will be

| Today | After |
|---|---|
| No ground under trees, hedges and fences; the map's edge is sky at ground level | Ground under every square; past the map's edge a skirt of ground and a ring of far tree-line and hills |
| A tree is two crossed pictures standing on nothing | A tree stands in a patch of roots, needles or leaf litter, with a soft shadow at its foot |
| Open ground is one texture repeated | Tufts of grass, flowers by the season, shrubs, ferns, stones, fallen logs, stumps, reeds by the water |
| The town's streets are bare | Barrels, crates, a cart, flower boxes, lamp posts lit at night, market stalls on market day, smoke from chimneys |
| A dungeon floor is clean stone | Each band's own debris: bones and skulls, rubble, cobwebs in the corners, puddles, slag, shards, roots |
| A floor forgets the party | The fallen leave remains, a drunk potion leaves its bottle, a fireball leaves a scorch, a spent torch its stub |
| Every wall and floor square looks the same | Tile variants and turns, cracks and moss, darker corners and wall feet, beams and stalactites overhead |
| One light: the party's torch | The wall torches light their walls; embers, crystals and fungus glow on what is near them; soft shadows under things |
| The air is empty | Dust in the torchlight, drips, rising embers, drifting spores, falling leaves, fireflies, rain, snow, morning mist, clouds |

## Phase 0 - Ground everywhere, and a horizon - v8.1 (small; the fix first)

- **Ground under solid surface squares.** `CM.floorMesh` lays a ground quad under every tree, hedge, fence, frame and
  town-wall square, and on cliff tops, wearing the ground the square would have had (grass in the forest, the field's
  grass by the hedges). Dungeon floors are untouched: their solid squares are rock.
- **Under the trees.** A tree's square gets its own ground: leaf litter under a broadleaf, needles under a fir, with a
  dark soft disc at the trunk's foot (a flat sprite in the static mesh) so a tree stands on the ground instead of
  floating over it.
- **The edge of the world.** Past the map's edge on surface floors, a skirt of ground runs out sixty squares (a few
  large quads, fogged), and a ring of far silhouettes stands on it: a tree-line round the land, the town's hill and its
  wall seen from the land, the land's forest seen over the town wall. Drawn once, coloured by the sky.
- **Tests**: no surface floor's mesh has a square without ground; the skirt meets the map's edge; a dungeon floor's
  mesh is byte-for-byte what it was.

## Phase 1 - The scatter engine - v8.2 (medium; everything after stands on it)

- **`CM.PROPS`**, a table in a new `27-props.js`: each prop is `{ id, layer, how: "stand" | "flat" | "cross" | "wall",
  size: [min, max], tint }`, and `CM.SCATTER`, the rules that place them: `{ prop, where: { floors | bands | special |
  ground | canopy | near: "wall" | "corner" | "water" | "road" }, per: chance per square, most: per square }`.
- **`CM.scatter(fl, seed, detail)`** works out, square by square, what lies there: up to four props a square at
  offsets and turns inside it, by `hashSeed(seed:floor:x:y:i)`, never on a square with a thing (a chest, a door, a
  stair, a person), never on a feature (a pit, a plate, a lever's wall), and never on the party's start square.
- **Into the mesh.** The props go into the static mesh with the walls (standing pictures face the camera's
  quarter-turn: four orientations baked, the right one chosen per square at build time, or crossed pairs for
  plants, which read from any side). A short list of swaying things near the party is rebuilt per frame.
- **Small things share layers.** Props are small: four to a texture layer (each a quadrant), so a hundred props cost
  twenty-five layers, not a hundred. The sprite and mesh code learn a sub-rectangle of a layer.
- **The Detail setting** in Settings and on the title (Low / Medium / High) and in `CM.scatter`'s density; the
  automatic step-down drops it one before it drops the render scale.
- **Tests**: the scatter is the same twice and differs by seed; never on a thing, a feature or the start; a floor's
  fingerprint is the same with props as without; Low places none; a hundred floors build their meshes under a time
  budget.

## Phase 2 - The surface's life - v8.3 (large)

- **The land**: grass tufts and wild flowers on open grass (spring's flowers, summer's tall grass, autumn's seed heads
  and fallen leaves, winter's snow lying on the ground, the crowns and the roofs - the season already in `CM.season`);
  shrubs and bushes at the forest's edge and the field's hedges; ferns, mushrooms, moss and fallen leaves under the
  canopy; fallen logs and stumps in the forest; stones and boulders along the road and the river; reeds, rushes and
  lily pads by the water; stepping stones in the ford; hay bales and a cart in the fields; the farm's rows showing what
  grows in them, by the farm's own state (sown, sprouting, ripe, rotten).
- **The town**: barrels and crates by the tavern and the merchant, a handcart, a water trough, flower boxes under
  windows, a woodpile by the smith, lamp posts along Lantern Street and in the Square that light at dusk, warm windows
  at night, smoke rising from the chimneys of houses whose hearth is lit, stalls round the market cross on market day,
  banners and garlands in festival weeks (the calendar's).
- **Assets**: ambientCG (CC0) Foliage001 and Foliage006 (grass and strands with cut-out), a LeafSet or two (broadleaf,
  autumn maple), ScatteredLeaves001 and Ground077 (forest floor), downloaded and kept whole in the Timeline's Local
  Storage like the others; Crawl's grass-with-flowers floors, bushes and plants for Pixel; barrels, crates, carts,
  stalls, lamps, logs and stones drawn in code.
- **Tests**: the props of the land and the town follow the season and the hour; nothing on the road blocks the way
  (props never block, but the road stays readable: no shrub on a road square); market-day stalls only on market day.

## Phase 3 - The dungeon's debris - v8.4 (large)

Each band has its own palette, placed by the rules - corners and wall feet first, corridors sparser than rooms:

| Band | Debris |
|---|---|
| Catacombs (1-5) | bones and skulls, a broken coffin lid, cobwebs in the upper corners, dust drifts, a fallen candle |
| Flooded Vaults (6-10) | puddles, drips from the ceiling, green slime on the wall feet, rotted crates, a waterlogged sack |
| Dwarven Halls (11-15) | rubble and fallen stones, a broken pick, mine-cart rails, rusted armour pieces, an overturned barrel |
| Lich King's Palace (16-20) | torn banners, shattered glass, guttered candelabra, a toppled urn, frost on the stone |
| Drowned Town (21-25) | weed, shells, a rotted oar, silt drifts |
| Fungal Deep (26-30) | mushroom clumps, spore puffs, slime trails |
| Crystal Caverns (31-35) | shards, crystal growths at the wall feet, glittering dust |
| Foundry (36-40) | slag heaps, chains, cogs, ingot moulds, soot |
| Ossuary (41-45) | bone heaps, skull niches in the walls, grave dust |
| Root of the World (46-50) | roots through the floor and the walls, earth spills, pale growths |

And by room: a vault's spilled coins, a library's fallen books and loose scrolls, a crypt's sarcophagi and urns, a
den's straw and gnawed bones, a shrine's candles, a fountain hall's wet stones. The guardians' lairs already have
furniture; they get debris that agrees with it.

- **Assets**: Crawl's bone floors, moss, blood, the boulder, the skeleton vault tiles and the item tiles (bones,
  potions, books, coins) for Pixel; drawn painters for the rest (cobwebs, rubble, shards, slag, chains), shaded with
  the band's own stone photograph for Stone.
- **Tests**: each band's palette appears on its floors and not on others; nothing in a doorway or on a lever's wall;
  cobwebs only in corners; the dungeon's fingerprints unchanged for every seed the tests walk.

## Phase 4 - Traces: the floor remembers - v8.5 (medium)

- **What a fight leaves**: where a monster fell, remains by its kind - bones for the dead, a slime puddle, a pile of
  ash for the burned, scales and feathers - and a dark stain; where a hero fell and was raised, a scuff and a dropped
  strap.
- **What the party leaves**: a drunk potion leaves its empty bottle (the potion's own colour, tipped on its side) on the
  square it was drunk on; a spent torch leaves its stub; a fireball leaves a scorch on the floor and the walls near it;
  a Ranger's fights leave broken arrows; a picked lock leaves a bent pin; a smashed phylactery its shards.
- **Saved, and small**: traces are the one saved kind of prop - a short list on the floor's delta, `{ id, x, y, turn }`,
  at most forty a floor, the oldest fading first. A film replays them as they happen.
- **Tests**: a potion drunk leaves a bottle where it was drunk; a fight leaves remains by the kind; traces survive a save
  and come back; the forty-first trace drops the first; a save's size grows by no more than a set amount per floor.

## Phase 5 - Walls, floors and ceilings with variation - v8.6 (medium)

- **Tile variants**: each band's floor and wall get two or three variants (the sets have them: Crawl's numbered tiles,
  a photograph cropped three ways) and a turn per square by hash, so no two neighbours repeat.
- **Corners and wall feet**: a baked darkening where the floor meets a wall and in corners (a per-vertex shade in the
  mesh: ambient occlusion without a pass), and a strip of grime or moss at the wall foot by band.
- **On the walls**: cracks, creeping moss and roots, chains, rings, banners, empty sconces and candle niches, by band
  and by room; in the Stone look, ambientCG's Leaking decals for wet stains in the Flooded Vaults and the Drowned Town.
- **Overhead**: beams in the Dwarven Halls, stalactites in the caves and the Root, vaulting in the Palace.
- **Doorways**: lintels and posts drawn round a door's opening instead of a door picture alone.
- **Tests**: the variant and the turn of a square are the seed's; the darkening is only where a wall is; decals never on
  a secret door's wall (they would give it away), nor on a lever's or a carving's.

## Phase 6 - Light and shadow - v8.7 (medium to large)

- **The wall torches light**: the nearest eight torches on the floor become point lights in the shader, each lighting
  the walls and floor about it with its own flicker; the party's torch stays the strongest. Glowing things (embers,
  crystals, fungus, a teleporter, lava vents) light what is near them in their own colour.
- **Soft shadows**: a dark disc under every monster, person, chest and standing prop; under trees on the surface, a
  dappled shade.
- **The sun on the surface**: walls facing the sun's direction (by the hour) are lit, walls facing away are in shade;
  at dusk the light goes gold, at night the moon's blue; lamps and windows glow.
- **A colour grade per band** (a little warmer in the Foundry, colder in the Palace, greener in the Fungal Deep), kept
  subtle.
- **Tests**: the light count stays within the shader's limit; a floor with no torches renders as today; the sun's
  direction follows the clock.

## Phase 7 - Air and weather - v8.8 (medium)

- **In the dungeon**: dust motes in the torchlight, drips from wet ceilings (Flooded Vaults, caves), embers rising in
  the Foundry, spores drifting in the Fungal Deep, glitter in the Crystal Caverns, cold breath in the Palace.
- **On the surface**: leaves falling under the trees (autumn most), fireflies on summer nights, birds crossing the sky
  by day, clouds drifting across the dome, low mist on the land at dawn, rain streaks and splashes when the weather is
  rain, snow falling and settling in winter, smoke from the chimneys.
- All of it from the existing effects system (`45-fx.js`), as a steady stream near the party, scaled by Detail and
  stopped under reduced motion (`CM.reducedMotion`).
- **Tests**: weather particles only in the weather; nothing under reduced motion; the particle count stays within
  Detail's budget.

## Phase 8 - Around the update - v9.0 (small)

- **Performance**: the smoke test measures frames per second on the land by day at High, on a dungeon floor with ten
  torches in view, and in a fight with a fireball; the numbers go in this plan, and the automatic step-down is tuned so
  a modest laptop holds thirty frames at Medium.
- **The file's size**: the new photographs and atlases are budgeted (about 1.5 MB more); props share layers.
- **Docs**: the README's section, the Timeline's Help and Manual, the Manual's screenshots retaken.
- **Tests**: all of the above; `npm test`; the Timeline's five.

## Order, sizes and what depends on what

| Phase | Version | Size | Depends on | Why in this order |
|---|---|---|---|---|
| 0 Ground everywhere, a horizon | 8.1 | S | - | The visible fault, fixed first |
| 1 The scatter engine | 8.2 | M | - | Everything scattered stands on it; the Detail setting with it |
| 2 The surface's life | 8.3 | L | 0, 1 | The land and town are the newest and the barest |
| 3 The dungeon's debris | 8.4 | L | 1 | Most of the game is spent below |
| 4 Traces | 8.5 | M | 1 | Needs the props' painters; the only saved kind |
| 5 Walls, floors, ceilings | 8.6 | M | - | Independent; could go earlier if the repetition grates |
| 6 Light and shadow | 8.7 | M-L | 3, 5 | Lights look best on stone that has something on it |
| 7 Air and weather | 8.8 | M | - | Independent; the effects system exists |
| 8 Around | 9.0 | S | all | Performance, size, docs |

## Downloads (CC0, kept whole in the Timeline's Local Storage, asked for at the phase that needs them)

| Phase | ambientCG sets | For |
|---|---|---|
| 0 | Ground077, ScatteredLeaves001 | needles and leaf litter under the trees |
| 2 | Foliage001, Foliage006, LeafSet027, LeafSet024 | grass tufts, strands, autumn and green leaves for shrubs and crowns |
| 5 | three or four Leaking decals, a moss material | wet stains and creeping moss in the Stone look |

Everything else comes from the kept Dungeon Crawl set (bones, moss, blood, boulder, bushes, plants, potions, books,
coins, flowered grass) or is drawn in code.

## Risks

- **Frames**: hundreds of props per view. They are batched into the static mesh and shared layers, culled by Detail,
  and measured in the smoke test; the step-down drops Detail before resolution.
- **Clutter hiding the game**: a chest, a key or a lever must never be lost in debris. Props keep off things and
  features, stay low and dim beside them, and the automap is unchanged.
- **Texture memory**: the Stone look's layers are 512 a side; props at four to a layer keep the count down, and the
  art cache already holds only three depths at a time.
- **Seeds and saves**: props are by hash after generation and outside the fingerprint; the only saved props are the
  party's traces, capped. The Node tests walk the seeds they walk today and compare fingerprints.
