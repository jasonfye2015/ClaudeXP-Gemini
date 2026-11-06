# Upgrade plan 62: mesh trees and a world painted with plants

Asked for 2026-11-05: mesh trees of a few kinds that take snow, and the whole game painted much more densely with
plants of every sort - bushes, shrubs, plants, weeds, flowers - above ground and below.

## 1. The source

The **Quaternius Ultimate Nature Pack** (CC0; quaternius.com/packs/ultimatenature.html), fetched as GLB from the
showcase mirror github.com/trebeljahr/quaternius-showcase (public/glb/nature_pack, 150 files, 38 MB) into
`Local Storage\Claude and Magic models\quaternius-nature` (never committed; only the baked file is). It holds:

| Kind | Shapes | States |
|---|---|---|
| CommonTree, BirchTree | 5 each | green, Autumn, Dead, Snow, Dead_Snow |
| PineTree | 5 | green, Autumn, Snow |
| Willow | 5 | green, Dead, Snow, Dead_Snow |
| Bush, BushBerries, Bush_Snow | 2 each | |
| Plant 1-5, Grass, Grass_2, Grass_Short, Flowers, Lilypad, Corn 1-2, Wheat | | |
| Rock 1-7 and Rock_Snow, TreeStump (+Moss, +Snow), WoodLog (+Moss, +Snow) | | |
| Cactus, CactusFlowers, PalmTree | not used | |

The models are untextured, flat-shaded and vertex-coloured (a tree ~1,900-2,900 triangles, a bush ~360, a plant
~300, grass ~190). The figures' pipeline (plan 60) bakes skinned bodies; these are static, so they get a pipeline of
their own that is smaller and simpler.

## 2. The architecture

- **Baking** (`tools/plants.py` -> `src/js/35d-plants.js`, `CM.plantsPack`): positions as int16 over the model's
  box, one colour index a vertex into the model's own palette (the palettes ride in the manifest), uint16 indices,
  deflated and base64'd like the figures. `src/models/plants.json` maps names to files and holds the budget.
- **Reading** (`37b-plants.js`, rules-side, no DOM): `CM.Plants.parse`, `measure` (height, radius, foot), and the
  palette atlas: every model's colours packed into one picture layer ("pal:plants", a surface-and-shared layer),
  so a vertex's colour is a texture lookup and the ordinary fragment shader lights it (facing from dFdx, the
  snow's whitening of up-facing faces, the mist, the fog, the torch) with nothing new in the fragment.
- **Drawing** (40-render.js, `76zzzzzzzzzzq-plants.js`): a static instanced path - one vertex buffer a model, an
  instance buffer a model a floor (x, y, z, yaw | scale, sway, reach, 0 | tint rgb, shade), `drawElementsInstanced`
  after the figures and before the billboards; the vertex shader's new branch (uStatic) places, turns, scales, sways
  (the existing gust) and parts (uPush) each instance, and hides instances beyond their reach. Instances are
  rebuilt when the floor's key changes and when the party has walked four squares (the reach cull).
- **The painted trees stay as the far ones**: a tree square's crossed pictures are flagged hidden-within-reach
  (aFx.x <= -10 in the vertex shader, the mirror of the details' shown-within-reach), so beyond the mesh reach the
  old pictures stand and within it the meshes do.
- **Where plants go** (`69zzs-plants.js`, rules, deterministic by hash like CM.scatter): by ground, by what is
  near (trees, water, walls, buildings), by band below ground, by the Detail setting's density. Never on a thing, a
  feature, a door or the party's square. Plants are a sight, not a solid: nothing blocks a step that was open.
- **Seasons and weather**: autumn shapes in autumn (by the turn, as the pictures turn), the Dead shapes for the
  charred and the fallen trees' stumps and logs, the Snow shapes when the lying snow is deep (uSnow whitens the
  crowns before that), the bare Dead shapes in winter for the common trees. Saplings are the green shape, small.

## 3. Phases (each a release)

0. The pipeline: the bake, the reader, the loader, the palette atlas, the Node test that parses the pack.
1. The renderer path: uStatic, the instance buffers, drawStatics, the hidden-within-reach flag; one tree kind on
   the Wood's squares to prove it, the far pictures beyond.
2. The trees: every tree square by kind (the Wood's three by the old variant hash - common, pine, birch; willows by
   the water; the town's yard trees), the seasons, the states (fallen -> a log, charred -> a dead shape dark, a
   sapling small), the snow shapes by depth.
3. The plants above ground: grass tufts and tall grass, flowers, plants, bushes and berry bushes, stumps, logs and
   rocks, corn and wheat on the farm's rows, lilypads on the river's still water - dense by Detail, swaying, parted
   by the party.
4. The plants below ground: moss and pale fungus (the plant and grass shapes tinted by band) in the corners and
   along the walls, thick in the Fungal Deep, lilypads and reeds on the flooded squares, roots at the Root of the
   World, berry bushes and grass in the daylit squares under the grates.
5. The look and the cost: the snow and the frost on the meshes checked in every season, the reach by Detail, the
   harness's frame time on the Wood at high Detail, the far pictures matched to the meshes' colours.

## 3a. Progress

- v80.0 - phases 0, 1 and 2: tools/plants.py and src/models/plants.json (47 models, 620 KB of base64),
  35d-plants.js, 37b-plants.js (parse, vertex, measure, atlas), 76zzzzzzzzzzq-plants.js (the loader, the
  "pal:plants" shared layer, plantBuffers, plantInstances, drawStatics, renderer.plantReach by Detail),
  40-render.js (uStatic's instanced branch with the reach cull, the sway and the parting; the hidden-within-reach
  quads aFx.x <= -10; uTint on the plants; the floor key and floorMesh's meshReach), 26-surface.js (the tree
  pictures flagged far-only), 69zzs-plants.js (CM.plantInstancesOf: every tree square on the surface floors by
  kind - common, pine, birch by the old variant, a willow by water - the autumn shapes as the leaves turn, bare
  broadleaves in winter, the snow shapes when the snow lies, a log for a fallen tree, a dark dead shape for a
  charred one, a small sapling).
- v81.0 - phases 3 and 4: 69zzs-plants.js places the plants above ground by the ground and what is near (grass
  tufts on the grass, fewer under the canopy; flowers on the open grass in spring and summer, fewer in autumn,
  none in winter; plants under the trees, on the litter and the moss and beside the water; bushes beside the trees
  and along the walls, berries in summer and autumn, snow bushes under snow; stumps, logs and rocks on the Wood's
  floor, sparse; corn and wheat on the tilled rows; lilypads on the still water - the river keeps them though it
  is a feature) and below ground by the band (moss in the Catacombs, weeds in the Flooded and the Salt Vaults with
  lilypads on their water, fungus thick in the Fungal Deep, roots at the Root of the World; nothing in the other
  bands), tinted a draw a model (CM.plantTintOf -> uTint), toward a wall when there is one, never on a solid
  square, a thing, a feature, in a cave, a house or the Joker's hall. The small plants' reach is eleven squares;
  the density scales with Detail. Not done: the daylit squares under the grates (the grates are the window's).
- Phase 5, checked after v81.0 in the harness: the Wood in summer, autumn, winter and under snow reads right (green
  crowns, orange, bare broadleaves with the pines green, the snow shapes with the ground whitened); 434 instances
  drawn at high Detail with a tree in reach; the frame rate with the plants against without differed by under a
  frame a second (45.5 against 46.1 in the harness, which is CPU-bound). Nothing more was changed for it. Open: the
  far pictures' colours against the meshes' (the painted far trees stay green in winter beyond sixteen squares),
  and the daylit grates' grass.

## 4. Budget

The baked pack is held under 1.2 MB of base64 (the HTML is 10.2 MB). A tree kind in three states and two shapes is
about 150 KB deflated; the plants are small. The reach is 16 squares above ground and 12 below at high Detail,
12 and 9 at medium, and at low Detail the meshes are off and the pictures stand as before.
