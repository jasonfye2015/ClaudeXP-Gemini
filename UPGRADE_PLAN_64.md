# Upgrade plan 64: set-piece rooms - a curated list for the dungeon's generation

Asked for 2026-11-05: curated rooms the generators can drop in - an oasis with trees and a pond, a room of bones, a
long hallway of doors most of which lead nowhere, a flooded room with fish. This is the list, with what each room
needs from the generator and what already exists to draw it. Nothing here is built yet.

## 0. What exists

- **Set pieces by template** (20-world.js `CM.TEMPLATES`, 10-data.js `CM.TEMPLATES2`): ASCII rows with the ring
  wall included; on the ring D door, L locked door, G gate, S secret door (at odd positions, so the maze comes up to
  them); inside C chest, M monsters that stay, F fountain, A altar, P pit, K key, X dark floor, W a carved wall.
  Generator 1 places one or two a floor (two from the sixth), the guardian's lair first; a flood flag floods one.
  Twelve exist: Treasure Vault, Shrine, Fountain Hall, Den, Library, Crypt, Pit Room, Keep, Great Hall, Drowned
  Chapel, Charnel Pit, Crystal Gallery.
- **Landmarks**, one a band (69zzg-landmarks.js: the Bell Square, the Candle Crypt, the Crystal Hall, the Empty
  Throne, the Fairy Ring, the Flooded Nave, the Forge-Hall, the Great Crucible, the Heart-Root, the Skull Wall) and
  the **vaults** (69zza-vaults.js: the Counting-House, the Drowned Chapel, the Sealed Library) with their puzzles.
- **Drawing that is ready to use below ground**: water decor on squares (the flooded mood's water, rings, glints,
  the wading sounds), the sunken and raised rooms (69zzi-levels.js), the plants' meshes on any floor - trees, bushes,
  grass, lilypads, fungus, roots - and the clutter (plans 62 and 63), the glowcaps' green light (plan 63),
  the figures (the rat, the wolves, the deer), the air (motes, spores, drips, fireflies, fog), the wall decals,
  the pet fish's shallows sound, the lit grates' daylight.

## 1. New letters the templates need (one small generator change)

| Letter | Means | Drawn by |
|---|---|---|
| `T` | a tree square (solid, see-through, like the Wood's) | the plants' meshes; the canopy's dapple |
| `~` | still water (open, the flooded mood's water, wadable) | the water decor; lilypads; fish (new, an air kind on the water) |
| `B` | a heap of bones (open, a thing that is looked at, not taken) | the bones picture and the skull decals |
| `H` | a false door on the ring (a door picture on the wall; opens on a niche one square deep, or does not open) | a `door` feature marked `blind` |
| `R` | a raised square (a step up, the dais) | 69zzi-levels' dais |
| `V` | a sunken square (a step down) | 69zzi-levels' pit level |
| `G`-inside | a glowcap cluster (light) | plan 63's glowcaps |
| `*` | a brazier or a standing candle (light, warmth) | the breakables' brazier |
| `=` | a bridge plank over water | the Wood's planks ground |

Everything else is placement: the room's name on the look line, its line of lore when first entered (the landmark
system's), its mood, and a thing or two of its own.

## 2. The rooms

Each: size (interior), band or depth, what is in it, the reward, the danger, and the soft-lock note (plan 63's rules:
a way always stands, every block clears, no hazard unseen or unbounded).

### Quiet and strange (any band)

1. **The Oasis** - 10 x 10. A ring of `T` trees round a `~` pond three squares wide with lilypads and fireflies; a
   chest on the far bank behind the trees, a second treasure (a relic-grade item or a gem) in the pond, dived for
   (plan 63's dive). Daylight from a grate above the pond. Birds. Danger: none by day; by night a wolf pack drinks
   there (figures, the Wood's wolves at the floor's level). The trees are see-through and the pond wadable: nothing
   blocks.
2. **The Bone Room** - 8 x 8. `B` heaps along every wall and the floor `X` dark; a Bone Colossus' bones in the
   middle too big to be a heap (a thing to look at: "it is not all here"); a chest under the heaps found by
   looking at the right one (a hint on the look line). Danger: the heaps stir - one group of skeletons at the floor's
   level when the chest is taken. The Catacombs and the bone halls.
3. **The Hall of Doors** - 3 x 15. Fourteen `H` doors down both long walls; two are real (`D`, to the maze), two
   open on a niche with a thing in it (a key, a chest, a carving), the rest are painted or nailed shut. The look line
   says "a door" for all; opening a false one says what it is. Danger: one niche holds a mimic. Soft-lock: the two
   real doors are the ring's entrances; the niches never deeper than one square.
4. **The Fish Pool** - 7 x 7. All `~` but a `=` plank walk across it; fish (an air kind, small dark shapes under
   the water with a flick and a ring, the shallows' sound); a chest on an island square in the middle. Fishing: with
   a rod in the bag (new, sold in town), a few minutes' standing on the plank gives a cave fish (the Drowned's catch:
   a meal). Danger: a Drowned rises from the pool when the chest is opened (the Flooded Vaults' level).
5. **The Garden Gone Wild** - 9 x 9. A town garden's plan - beds in rows, a well in the middle, a bench - swallowed
   by plants: bushes, ferns, flowers, glowcaps for light; the beds `R` raised. A gardener's grave (a carving) and
   the gardener's shears (a weapon, keen, cheap). A hive (the Wood's honey). The overgrown mood.
6. **The Mirror Hall** - 5 x 11. Two rows of pillars; at the far end a mirror (a wall picture that shows the party's
   figures reflected - the figures drawn again, flipped); a shard of it is a trinket that shows a foe's weakness
   once. Danger: the reflections step out of the mirror as Shades (the party's own classes at the floor's level) if
   the mirror is struck. The Lich King's palace and the Crystal Caverns.
7. **The Cold Store** - 6 x 6. The frozen mood in any band: frost on every wall, meat hanging (the cook's meals, a
   few, free), the party's breath; a Wraith asleep in the ice at the back, woken only by taking the last meal.
8. **The Chapel of Candles** - 7 x 9. Rows of `*` candles, all lit, a `A` altar; an offering (any gold) lights the
   altar's lamp for the floor (the room is a safe light); a hymn (the music's leitmotif) when the party enters.
   Danger: none - a rest without a camp (a short heal, once).
9. **The Map Room** - 7 x 7. A table in the middle with the floor's map carved in it (the floor is mapped when read,
   as the scroll does) and the next floor's stairs marked; a chest with a Scroll of Mapping.
10. **The Rookery** - 6 x 10, tall (the ceiling raised). Bats (an air kind, a cloud that wheels and settles) and
    guano (a dark floor); the bats scatter when the torch comes in; a nest high up with a trinket, reached by a
    `R` ledge. Danger: a Gargoyle among the bats.

### Water and weather (plans 61 and 63 drive them)

11. **The Cistern** - 9 x 9. `V` sunken the whole way, the storm's floodwater standing waist-deep for a day after a
    heavy rain above and dry otherwise; the drainage grates in every wall (the clutter's); a chest sunk in the
    middle (a dive). The flood's leeches. On a dry day a drowned treasure is just a walk.
12. **The Dripping Gallery** - 3 x 12. A corridor room under the town's street: grates every third square, the
    drips and the waterfalls in rain, puddles, the moss thick; a Drowned's hand in a puddle holding a key.
13. **The Storm Drain** - 5 x 5 with a `~` channel through it and `=` planks; after a storm above the channel runs
    (the air's rain kind along it, the wading sounds), and the planks are slick (the walk pace); a sluice gate (`G`)
    that opens from the other side.
14. **The Steam Room** - 6 x 6, the fire bands only. Hot stone, a `~` pool that steams (plan 63's steam screen):
    ranged foes cannot see through it; a Foundry Imp nest; the hot stone dries the party's wet (the damp uniform
    off for an hour).
15. **The Lightning Rod** - 5 x 5 under a grate on the first floor: an iron rod from grate to floor; in a storm
    above it crackles (plan 61's storm light through the grate) and a lightning spell cast in the room chains to
    every foe; a Shard Wisp hums round it.

### Trials (the rooms with a rule)

16. **The Tilting Floor** - 7 x 7. Plates (`plate`) in a ring; stepping on one tilts the floor (the view leans a
    moment) and opens a pit on the opposite side for a turn; the chest in the middle is reached by stepping the
    plates in the carved order. Soft-lock: the pits close again; the room's door is always open.
17. **The Echo Chamber** - 9 x 5. Every step is heard twice (the foley's echo); monsters here are deaf (they never
    ambush) but a bell on the floor summons them all when rung - and the floor's guardian's key is tied to the
    bell's rope.
18. **The Gauntlet** - 3 x 13. Vents (`vents` features) every other square down the length, firing in sequence
    (the Furnace's timing); a dash through at the right beat takes no burns; the far end a chest and a second door.
    Soft-lock: the near door is the way in and out; the burns are bounded (a point a vent).
19. **The Weighing Room** - 5 x 5. A scale `A` in the middle: the party's gold on one pan, a relic on the other;
    leave the relic's weight in gold to take it, or take it and be cursed for the floor (the curse status). The
    Counting-House's cousin.
20. **The Puzzle of Lamps** - 5 x 7. Five lamps (breakables' braziers), a carving with the pattern; light them in
    the pattern (Space lights, Space again douses) and the far wall's secret door opens; wrong, and the lamps go out
    and the room's cold wakes a Wraith.

### Lairs and dens (fights with a shape)

21. **The Spider Hollow** - 8 x 8. Webs on every corner (the clutter's, thick), cocoons (`B`-like things) with a
    hero-shaped one holding a bound adventurer (the existing one) and spider egg sacs that hatch when a cocoon is cut;
    the Giant Spider figure in the rafters (a `R` ledge). The Fungal Deep.
22. **The Kennel** - 6 x 8. Iron cages (the kennel's picture) along the walls, Iron Hounds in them; a lever opens
    all cages at once (a fight of three groups, or leave it); the kennel-master's whistle (a trinket that calls the
    party's dog from anywhere) on a hook. The Foundry.
23. **The Barrow** - 5 x 9, the Catacombs. A long mound with `R` steps up to a sarcophagus (`A`); grave goods in two
    chests; the lid is the floor's carved story; opening the lid for the third chest wakes the barrow's king (an
    elite of the floor's level).
24. **The Wolf Den** - 7 x 7 with `T` trees at the corners (the roots come down through the roof). Wolves (figures)
    asleep in a ring round a kill; sneak past (the Rogue's shadowstep, or Boots of Silence) or fight; the kill is a
    deer (meat for the cook).
25. **The Troll Bridge** - 3 x 9 across a `~` chasm (the water a long way down: a dark floor with a drop's sound).
    A Troll under the bridge demands a toll (gold, or a riddle, or a fight); paying is remembered (he waves the party
    through next time).

### Memory and story (the chronicle's rooms)

26. **The Hall of Fame Annex** - 7 x 7. The Hall's dead (the remains system) laid out here with their names on
    plaques; a bell to ring for them (a line of lore each); their best piece of gear in a chest the plaques open.
27. **The Painter's Room** - 5 x 5. An easel with the party's portrait being painted (the portraits' pictures),
    unfinished; the painter is a ghost who finishes it if the party stands still a minute (a trinket: the painted
    likeness, +1 Luck). The Lich King's palace.
28. **The Orrery** - 9 x 9, raised in rings (`R`). A model of the sky: the sun's and the moon's places move with
    the clock (plan 61's sky bar in brass), the planets' spheres on arms; reading it tells the next three days'
    weather and the next meteor's night. The Crystal Caverns.
29. **The Lich's Study** - 7 x 7, the last floors. His desk, his letters (the letters system), the first page of
    the box's making (the lore), and a trap: the chair.
30. **The Kitchen** - 6 x 8, any band. Ysolde the king's cook's kitchen (her tale is in the lore): an oven that
    still works (a camp's cooking without a camp), knives (a weapon), the bread recipe on the wall, rats in the
    flour (the scurrying rats, many).

## 3. Mechanics to add once, shared by the rooms

- **Rooms with water inside** (`~`): the water decor, a wadable square; fish as an air kind on the water (a dark
  flick, a ring, the shallows' sound), lilypads from the plants; the dive for things under it (plan 63).
- **Trees inside** (`T`): a solid see-through square as the Wood's, the plants' tree meshes, dapple from the grate
  above when there is one; the canopy set so the air's leaves fall.
- **False doors** (`H`): a `door` feature with `blind: true` on the ring - the door picture on the wall, "a door"
  on the look line, a niche one square deep behind it when `niche: true`, or nothing ("painted on the stone",
  "nailed shut").
- **Raised and sunken squares inside a template** (`R`, `V`): fed to 69zzi-levels' per-square levels.
- **A room's own lore line and name**: the landmark system's, generalised to every template (name, line, mood).
- **A room's own things**: bones heaps (looked at), cages, candles, the easel, the scale, the orrery - each a
  thing type with a look line and a Space action, the pattern of the breakables.
- **The soft-lock test**: every template's ring has at least one plain `D` on it; every inside square is reachable
  from every entrance with the `T`, `~` (when not wadable) and `B` squares counted as they are; the generator's
  reach check after placement (the one that exists) stays the last word.

## 3a. Progress

- v86.0 - release 1 (with plan 63's release 7): 69zzz-setpieces.js - CM.SETPIECES (the Oasis, the Bone Room, the
  Hall of Doors, the Fish Pool as templates with their own dice), CM.planFloor wrapped so one floor in three from
  the third takes one, chosen by a hash of its own (22-gen2.js places an ownDice template with its own Random, so
  the floor's other rooms stand where they stood and generator 1's frozen floors are untouched); the letters read
  after the making (dress): T a tree square on open stone that bars the walk (CM.isOpen wrapped; the plants stand
  a mesh tree there - 69zzs-plants.js), ~ water decor with fish, B and b bone heaps (a chest under one, the
  skeletons' stir), H/h/m false doors, niche doors and a mimic's door as "falsedoor" features, R/V the levels, *
  a brazier, G a glowcap that never fades (69zzw-blooms.js), c a chest with a guard and a note, the pond's sunk
  chest dived for (69zzu-basins.js); the room's line said on the first step in. 76zzzzzzzzzzw-setpieces.js draws the
  heaps, the false doors on the walls, the fish and the chests' notes. Not done: the plank bridge picture, the
  fishing rod, the daylight grate over the Oasis, the rooms' own names on the look line.
- v87.0 - release 2, the second nine: 69zzza-rooms2.js - the Garden Gone Wild (raised beds, the well, glowcaps,
  the Gardener's Shears in a chest, the plants grown thick by a garden flag in 69zzs-plants.js), the Chapel of
  Candles (braziers in rows, the altar), the Map Room (a table that maps the floor once, a Scroll of Mapping in
  the chest), the Rookery (a dark floor, a nest on a ledge with a trinket, a still group, bats that wheel under the
  roof and scatter - the window's), the Cistern (a sunken hall in the damp bands of the first four floors, a sunk
  chest in the middle that floods with the storm), the Dripping Gallery (floors 1-3, puddles, a key under one),
  the Storm Drain (a channel and a gate), the Steam Room (the Foundry and the Root only, a pool that steams under a
  cold sky, a still group), the Lightning Rod (floors 1-3, a rod that makes a lightning spell leap to every foe for
  half, a still group). 69zzz-setpieces.js takes a template's bands and max and a CM.SETPIECE_LETTERS registry,
  and a chest's fixed item (CM.setPieceItem) and sunk flag. The Cistern's floodwater is plan 63's. Not done: the
  Mirror Hall and the Cold Store (rooms 6 and 7: the mirror's shades and the hanging meat want pictures of their
  own).
- v88.0 - release 3, the third ten: 69zzzb-rooms3.js - the Echo Chamber (a bell that calls the floor's two nearest
  wandering groups to one fight), the Gauntlet (vents every other flag, a chest at the end), the Weighing Room (a
  relic of the band on a scale: paid by weight, or taken and cursed), the Barrow (steps up to a sarcophagus:
  opened, a third chest and the barrow's king - a Wraith and two Skeletons), the Wolf Den (trees, three wolves
  asleep - struck before they wake, or walked round - and the venison of their kill), the Troll Bridge (a troll
  who bars the bridge till his toll is paid or he is fought), the Painter's Room (a ghost painter: stand a while for
  a painted likeness, a new trinket, +1 Luck), the Orrery (the next three days' weather and the next star's night),
  the Lich's Study (a trap chair, a bounded shock once; a desk with his letter), the Kitchen (the cook's knives, a
  cold oven, rats in the flour - the clutter's rats, 69zzt-clutter.js). 69zzz-setpieces.js makes a chest of any
  letter a room names. Not done from the list: the Tilting Floor, the Puzzle of Lamps, the Spider Hollow, the
  Kennel, the Mirror Hall, the Cold Store, the Hall of Fame Annex (each wants a mechanic of its own - plates that
  tilt, lamps in order, cocoons, cages, reflections, hanging meat, plaques).

## 4. Order (when asked)

1. The letters and the shared mechanics (`T`, `~`, `B`, `H`, `R`/`V`, the room's name and lore line) - one release.
2. The four asked for: the Oasis, the Bone Room, the Hall of Doors, the Fish Pool.
3. The water and weather rooms (11-15), riding on plans 61 and 63.
4. The trials (16-20), one or two a release, each with its soft-lock test.
5. The lairs (21-25) and the memory rooms (26-30).
