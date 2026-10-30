# Claude and Magic - the ninth big update: the surface, under the sky

A plan for v7.1 to v8.0. The town and the Wood exist (the seventh and eighth updates) but they are drawn as dungeon
floors: every cell that is not a lane is a wall a man high, a stone ceiling closes over the street, the torch's fog
hides anything nine squares off, and a house is a picture pinned to a wall. So the town feels like a crypt with doors,
and the Wood like a brick maze with green bricks. This update gives the surface a sky, open ground, buildings with
walls and roofs of their own, a town shaped like a town, a forest that is trees, and ways to find your way; the
mechanics behind every door stay as they are.

The shape in one line: **the party steps out of its door onto a hill town under a real sky, walks a crooked street
to the square and the shaft, or out of the gate past the fields into a forest that closes overhead.**

## What is, and what will be

| Today | After |
|---|---|
| A stone ceiling over every open cell, a torch's reach of nine | On the surface: no ceiling; a sky by the clock (dawn, day, dusk, night, the moon's phase), daylight that reaches to the horizon, a leaf canopy only under thick trees |
| Every cell that isn't open is "wall", one texture per floor | Solid cells have kinds: house wall, door front, shop front, town wall, hedge, fence, cliff, water's edge, tree - each with its own face and height |
| A 19 x 19 cross of lanes, nine doors as billboards | A 45 x 45 walled hill town: an irregular ring wall, a west gate and an east postern, a crooked main street, the square with its well and market cross, the keep-yard with the shaft's mouth, side lanes, yards and gardens; buildings are blocks of 2 x 2 to 3 x 3 cells with real walls, a door face on the street and a sign |
| The Wood: glades carved out of green brick, through a gate at the lane's end | The land: outside the west gate, the road through fields and the farm, the river with a ford and a plank bridge, then the forest - trees as trees, glades with sky, paths under canopy, the hut, the shrine, the burner and the caves where they were |
| Finding a door means reading the automap | Signposts at the junctions (Use reads them), signs over doors, named streets on the compass, and a "Where to?" list that walks the party to any door it knows |
| Three looks: drawn in code, Crawl's pixel tiles, photographed stone | Two: Pixel and Stone, each with an outdoor set; the drawn painters stay in the file as what the other two fall back on, but the Drawn look is no longer offered |

## Phase 0 - The sky, and solid kinds - v7.1 - DONE

Built as planned, with these differences: the mesh is worked out in a new `26-surface.js` (`CM.floorMesh`, pure
arithmetic the Node tests run) and the renderer only uploads it; the grid stays 0/1 and a floor carries `kinds`,
`ground` and `canopy` maps beside it (remade from the seed, listed in `CM.FLOOR_FIXED`, never saved); trees are two
crossed pictures in the static mesh, the first rank and the one behind it; the sky is a dome of four far quads the
shader colours from the horizon to the zenith (`CM.sky(game)`: night, dawn, day, dusk by the season's daylight, the
moon's phase lightening the night, rain, mist and snow greying the day), with the sun and the moon as far sprites on
an arc a third of the way up the sky; the old town and Wood were dressed (`CM.dressTown`: the ring wall at the edge, a
house with its door's face behind every plot, hedges between; the Wood: trees, grass, mud in the river's bed, canopy
over the close paths). The Pixel look takes Crawl's grass, dirt and grey brick; its trees and canopy are the drawn ones
made of pixels (Crawl's tree tiles are mostly black outline at this size). Pixel is the default look. pack.py finds the
Timeline's Local Storage from the game's own repo (the sibling folder, or CLAUDE_TIMELINE).

The renderer (`40-render.js`) learns two things, and nothing else in the game needs to know:

- **No ceiling on the surface.** A theme with `sky: true` gets no ceiling quads; the clear colour is the sky's by the
  clock (`CM.skyColour(game)`: night blue to dawn rose to day to dusk amber, the moon's phase lightening the night),
  with a horizon band of haze. Fog goes to the sky colour, not black; `reach` is 60 by day, 14 by night (a torch's reach
  again, plus the moon). `uAmbient` is daylight by day. Under canopy (a cell with `canopy` in the grid) the ceiling is
  leaves, drawn, lit from above.
- **Solid kinds.** The grid stops being 0/1: a solid cell holds a small integer kind (`CM.SOLID`: 1 wall, 2 house,
  3 door, 4 shop, 5 townwall, 6 hedge, 7 fence, 8 cliff, 9 tree, 10 water-edge, 11 roof). Each kind has a face
  (a layer name), a height (hedges and fences 0.5, houses 1.6, the town wall 1.3, cliffs 2) and whether the party can
  see over it (hedges, fences, water). The mesh builder draws a wall quad to the kind's height, a top quad on low
  kinds, and a roof slab on house blocks (a flat dark slab at 1.6 is enough from eye height; a pitch is a stretch
  goal). **Trees** are not walls: a tree cell blocks movement but is drawn as a trunk billboard and a crown billboard
  above it, swaying a little, with the cells around it under canopy if three or more trees are near.
- **Ground kinds.** The floor layer per cell comes from a `ground` map when the floor has one (grass, dirt road,
  cobbles, flagstones, planks, water, tilled earth), falling back to the theme's floor.
- Everything that reads the grid as "0 is open" keeps working: `CM.isOpen`, `passable`, `distances`, the automap
  (which gets a colour per kind), saves (the town and the Wood are remade from the seed, so a save never carries a
  grid).
- **Tests** (Node, no screen): a sky theme's mesh has no ceiling triangles; kinds, heights and faces resolve for every
  kind; a tree cell blocks and is a sprite; the automap knows every kind. The smoke test screenshots the town by day
  and by night.

## Phase 1 - The town, shaped like a town - v7.2

`23-town.js` lays a new Caer Duin, still by hand (no generator; the same for every seed, so saves never drift), 45 x 45:

- **The hill**: the town sits inside an irregular ring wall (an oval, bulging east around the keep), with the **west
  gate** onto the land and a small **east postern** that is barred until the party has the Lich King's crown (a
  short cut back from the shaft's other mouth, later). Outside the wall on the north and south: cliffs and the
  hill's slope (cliff kinds the player cannot pass; the sky is seen over them).
- **The streets**: *Lantern Street* from the west gate, bending twice, to **the Square** (7 x 7, cobbled, the well,
  a market cross, the peddler's pitch on market day); *Shaft Lane* from the square east to **the Keep-yard**, a
  walled yard where the shaft's mouth is (the old keep's stones around it); *Temple Row* north from the square;
  *Smiths' Lane* south. Lanes between the houses' backs: yards, a few gardens behind hedges, a midden.
- **The buildings**: the nine plots become blocks with walls of their own: the party's house (2 x 2, at the west end
  of Lantern Street, the first thing inside the gate), the Hanged Lantern (3 x 2 on the square, the sign out
  front), the Merchant's House (3 x 2, square), the Smith's forge (2 x 2 with an open front and the anvil visible,
  Smiths' Lane), the Alchemist's Garden (2 x 2 house with a hedged garden beside it), the Library (2 x 3, Temple
  Row), the Temple (3 x 3 with a porch, the end of Temple Row), the Guildhall (3 x 2, Smiths' Lane), the Chronicler's
  House (2 x 2, by the keep). Each has one **door cell** on its street (the `building` thing, as now: walk up, Space
  opens the same screens), a sign layer by kind (the shop fronts), and lit windows at night. A building's level still
  shows: a foundation is a low fenced plot with posts; a frame is open walls; a house has its roof; a lit window at
  the top. Eight more **houses of the townsfolk** fill the blocks (no doors to open; the three villagers walk outside
  their own).
- **The mechanics do not move**: `CM.TOWN_PLOTS` and every screen behind a door are untouched; `CM.TOWN_AT` gives the
  new door cells (the tests and the bot read it by name); `CM.TOWN_AT.shaft`, `well`, `woodgate` likewise. A saved
  run standing on floor 0 at a cell that is not open in the new town is put at its own door.
- **Tests**: every door, the well, the shaft and the gate stand on open ground and can be walked to from the party's
  door; the town is the same twice; the old test of the town passes as before; a saved position off the new streets
  is moved home.

## Phase 2 - The land, and the forest - v7.3

`23b-wood.js` becomes the land (`CM.makeLand`): floor -1 is everything outside the wall, 61 x 61, by the seed:

- **Outside the gate**: the road west through **the fields** - the farm's rows and its gate where the road bends
  (the farm moves here from the Wood's first glade; its mechanics are the same, `CM.FARM_AT` moves), a few hedged
  pastures, a scarecrow - to **the river**, which crosses the land north to south: a ford where the road meets it
  (knee-deep, as the flooded floors) and a plank bridge a little north, found by walking. Over the river the forest
  begins.
- **The forest**: trees as tree cells, thick at the edges and thin along the paths, **glades** under open sky (the
  first glade just over the bridge is safe at any hour, as now), paths under canopy between them, the hermit's hut,
  the ruined shrine, the charcoal burner's clearing and the three cave mouths in the deep forest, far from the road,
  where the seed puts them. The forest's edge is the map's edge: trees all the way, with the hill's cliffs behind
  the town.
- **Day and night** on the land as now (foraging and deer by day, wolves and bandits by night), but the night is dark
  without a torch, the canopy darker, and the glades show the moon.
- **Tests**: the land is the seed's and the same twice; the road reaches the farm, the ford and the first glade; the
  hut, the shrine, the burner and the caves are reachable and far from the gate; a cave is a floor as before; the
  Wood's tests pass against the land (the glades, the ford, the night's bands).

## Phase 3 - Finding the way - v7.4

- **Signposts**: a thing at the gate, the square's corners and the forest's path forks; Use reads it ("Temple Row -
  the Temple, the Library"; "West: the farm, the river, the Deep Wood").
- **Signs over doors**: a sprite of the building's kind hung over the door cell (a lantern, a bale, an anvil, a
  mortar, a book, a sun, a crossed pair of swords, a quill), visible from down the street.
- **The compass names the street** the party stands on ("Lantern Street", "the Square", "the Keep-yard", "the road",
  "the fields", "the ford", "the Deep Wood"), and the title card says where the party is when it changes.
- **Where to?** (the camp menu's "Town" button grows into it, and a key): a list of every door, the gate, the shaft,
  the farm, the ford, the first glade and any cave found, with the walk's length; choosing one walks the party there
  with `travelTo` through what it knows, stopping for anything that happens on the way. Automatic uses the same list.
- **Tests**: every signpost names what its roads reach; the street name at every street cell; Where to? reaches every
  door from the party's door and stops for a villager.

## Phase 4 - The look of the surface - v7.5

- **The Stone look**'s outdoor set (ambientCG, CC0, kept whole in Local Storage as the others): grass, a dirt road,
  cobblestones (the square), flagstones (the yard), timber planks (bridge, frames), lime plaster and half-timber (the
  houses), roof tiles, bark (the trunks), a hedge, a dry-stone wall (the town wall), cliff rock, and leaves (canopy).
- **The Pixel look**'s outdoor set (Crawl, CC0, from the kept set): the grass and dirt floors (with their flowers),
  the trees (`dungeon/trees`, three kinds, as trunk and crown), the shop fronts as signs, stone walls for the town
  wall, the statues for the market cross.
- **Drawn things the sets lack** (the sign sprites, the scarecrow, the market cross, the plank bridge, the ford's
  posts, the canopy's dapples) are painted in code and pixelated or photo-shaded as the looks already do for monsters
  without a tile.
- **The Drawn look is retired** as a choice: `CM.LOOKS` offers Pixel and Stone; a save that says "drawn" opens in
  Pixel. The painters stay (`30-art.js`): everything either set lacks is drawn from them, as now.
- **Tests**: both sets build the town theme and the land theme with every outdoor layer present; `pack.py --check`;
  the settings' look list has two.

## Phase 5 - Around the surface - v8.0

- **Automatic** walks the new town (its errands by Where to?) and the land (the farm, the forage, the open cave).
- **The bot and the simulator** (`tools/sim.js --town`) cross the new town and the road; their numbers in the plan.
- **Films** replay the walk through the new town.
- **The Timeline's host** (`__init__.py`): nothing changes; the Timeline's screenshots in the Manual are retaken.
- **Words as data**: the streets', signposts' and signs' lines through `12-text.js`.
- **Docs**: README (the surface's section rewritten), LORE.md (the town's shape in the hill's chapter), the Timeline's
  Help and Support entry and Manual ch. 6 and 15 (which still describe v1.0).
- **Tests**: everything above; `npm test`; the Timeline's five.

## Order, sizes and what depends on what

| Phase | Version | Size | Depends on | Why in this order |
|---|---|---|---|---|
| 0 The sky, and solid kinds | 7.1 | M | - | The renderer first; the old town looks better at once and nothing else can be seen without it |
| 1 The town | 7.2 | L | 0 | The thing asked for |
| 2 The land and the forest | 7.3 | L | 0 | Needs tree cells and canopy from 0; moves the farm |
| 3 Finding the way | 7.4 | M | 1, 2 | Signposts need the streets to name |
| 4 The look | 7.5 | M | 0-2 | The sets are chosen for the shapes that exist by then; Drawn retired here |
| 5 Around the surface | 8.0 | S | all | Bot, sim, films, docs, screenshots |

## What stays as it is

- Every screen behind every door, the hearth, the stash, the forge, the farm's rows, the caves, the clock, the
  calendar, renown and the buildings' levels: the data and the rules are untouched; only where things stand and how
  they are drawn changes.
- The dungeon's floors: not a cell. The renderer's new kinds are only ever used by surface floors.
- Saves: the town and the land are remade from the seed, so an old save loses nothing but its position on floor 0 or
  -1, which is moved to the party's door or the gate.

## Risks

- **Performance**: an open 61 x 61 land with daylight reach is many more quads in view than a corridor. The mesh is
  built once a floor; the draw is one call. Trees as billboards are the cost: they are culled by distance as sprites
  are now, and the canopy caps what is seen. Measured in the smoke test (frames per second on the land by day).
- **The file's size**: a dozen photo textures at 512 add about a megabyte to the one file (2.6 MB today). Acceptable;
  the Stone set's new textures are resized as the old ones are.
- **The Drawn look's retirement** removes a choice a player may have liked; the painters stay, so bringing it back is
  one line in `CM.LOOKS`.
