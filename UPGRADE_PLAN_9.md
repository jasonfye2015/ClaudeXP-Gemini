# Claude and Magic - the eleventh big update: a world that moves

A plan for v9.3 to v10.0, proposed at the player's word on 30 October 2026, after the tenth update filled the view
and rebuilt the town's buildings. Ten updates have given the game a town, a land, a sky, a clock, a dungeon fifty
floors deep with things lying in it and light on its walls. What it does not yet have is *motion in the world
itself*: a monster is a picture that slides a square, a door is a picture that is replaced by an open one, a river is
a flat blue square, a tree is the same picture in winter as in June, and everything the party meets on a floor is
awake and waiting for it. This update is in three strands, braided so that no three phases in a row are all of one
kind: **graphics** (what moves and what the seasons do), **mechanics** (a dungeon that sleeps, hunts and hides, and
company for the party), and **content** (a second way down, more monsters, more of the town's people and their
errands).

The shape in one line: **a dungeon that sleeps until you wake it and hunts you when you do, monsters that lunge and
fall, doors that swing and water that moves, a winter that is white and an autumn that is red, a wall you can walk,
a hireling at your back, and a second, older way into the dark.**

---

## Principles (every phase keeps these)

- **No rule changes behind the player's back.** A graphics phase changes nothing the rules can see; the Node suite
  is the proof (its numbers do not move). A mechanics phase changes rules in the open, with a line in the log and a
  line in the README, and the balance simulator (`tools/sim.js`) is run before and after.
- **The seed still decides everything.** Lairs, sleepers, champions, the Undercroft's floors, the errands: all from
  the seed. Two runs on one seed meet the same world. Films still play back (anything the clock or the dice decide
  is written to the film as the fights already are).
- **Saves migrate, and old saves still open.** New fields have defaults; the schema's version rises once (to 7) in
  Phase 1 and the migration is tested against the fixtures (`tests/fixtures/run-v1.0.json`, `export-v1.0.json`) and
  a v9.2 export taken before Phase 1 ships.
- **Both looks, and Low.** Every moving thing degrades: at Low detail the animations are the slide and the swap
  they are today; under reduced motion nothing lunges, swings or shimmers.
- **Automatic plays it all.** Each mechanics phase gives the bot the new thing (sneak, wake, hire, take an errand,
  go down the other way) or the simulator measures nothing. Phase 7 ties them together.
- **The lore bible rules.** New people, monsters and places are written to `LORE.md`'s rules (the lies, the truth,
  the bands' purposes) and added to it.

## What is there now, and what each phase turns it into

| Today | After |
|---|---|
| A monster is one picture that slides a square | It breathes where it stands, lunges when it strikes, flinches when struck, falls when it dies; packs move out of step |
| Every monster on a floor is awake and waiting | Most sleep in lairs; the party's light and noise wake them; a woken pack hunts; a party in the dark, led by a Rogue, can pass |
| An elite is a bigger number with a name | Champions lead packs, with a word that says what they do (Warded, Frenzied, Shrieking, Shadowed, Stonehide) |
| A door is swapped for an open door; a chest for an open chest | Doors swing, portcullises lift, lids open, levers throw, over a third of a second |
| Water is a blue square; torches are a still picture | Water moves and shows the sky; puddles shine in rain; flames flicker; windows light at night |
| The trees are June all year; snow is a word in the HUD | Autumn colour, bare winter crowns, blossom in spring; snow on the ground, the roofs and the crowns; the river frozen; the ground wet in rain |
| The town wall is a wall | The gate tower's stair climbs to the wall-walk; the land seen from above; the east postern and the cliff path |
| Four heroes, always four | A fifth place behind them for a hireling, a rescued adventurer or a dog, with a trade and a few words |
| The townsfolk have one line each | Six of them have errands: short chains of things to find or do below, with a reward, a line of story and a change in the town |
| One way down: the shaft | The Undercroft under the third cave: three floors of its own, a tenth guardian, and a door into the Flooded Vaults from below |
| 35 monsters | 50: fifteen more, each band's own and the Undercroft's, with new abilities and new calls |

---

## Phase 0 - Monsters that move - v9.3 (graphics; small to medium; first because every fight shows it) - DONE

As built: `28-motion.js` (`CM.motion`, `CM.facesMirror`) gives the pose; the renderer's billboards take `tilt`,
`skew`, `scale` and `mirror`. Crawl's set has no second frames (only old and new drawings of a kind), so the Pixel look's
idle2 and attack frames are the same tile leaned about its foot, pixels kept square. The lunge reaches a quarter of a
square (a third filled the view at arm's length); a fallen monster topples away from the pack's middle. Sleepers and
champions are drawn from here too (Phase 1 sets the flags).

- **A monster's picture has a state**: idle (a slow breath - the sprite's height scales by two percent on a sine of
  its own phase, so a pack is never in step), lunge (toward the party by a third of a square over 120 ms, then back
  over 200 ms, on its blow), flinch (back by a sixth of a square and a white flash for 90 ms, on being struck),
  fall (a tilt of 80 degrees about its foot over 400 ms, then a fade over 300 ms; the dying map in `80-main.js`
  already knows when). Fleeing monsters turn and shrink along the corridor; a cowardly Kobold's run is seen.
- **Facing**: a monster's picture is mirrored by which side of the party's line it is on, so a pack looks at the
  party, not all one way.
- **Crawl's second frames**: where the Pixel pack has a second tile for a kind (the pack has them for a dozen),
  it is the lunge frame; `pack.py` gathers them as `mon.<kind>.2`. Drawn monsters lunge as one picture.
- **Bosses and guardians**: the Lich King's robe stirs (a slow horizontal sine on the lower half, two quads);
  the guardians' intro push-in already exists, and now they *rise* into it from the floor over a second.
- **Sprites in the mesh**: the renderer's sprite path (`setSprites`) takes `scaleY`, `tilt`, `flash`, `mirror`
  per sprite; the fight (`74-fight.js`) and the exploration loop set them from events already emitted (`fx`
  `hit`, `blow`, `fall`, `flee`). Nothing in `62-combat.js` changes.
- **Tests**: the sprite state machine is a pure function of (event, time since) in `27-props.js`'s neighbour
  `28-motion.js`, so the Node suite drives it: a lunge returns to rest; a fall ends faded; a flinch during a
  lunge cancels the lunge; reduced motion gives the slide only.

## Phase 1 - The living dungeon: lairs, sleepers, light, noise and stealth - v9.4 (mechanics; large) - DONE

As built: `61b-lairs.js`. `CM.makeLairs` runs over every dungeon floor and wing as it is made, by a hash of its own, so
no floor's walls, chests or way down move and the fingerprints and fixtures hold. The save's schema rose to 4 (the
shaded light and the noise; a follower and errands will use the same migration). Differences: the save keeps the
sleepers in the floor deltas it already had; Stonehide turns the *first* blow a round (three of four would have made it
a wall); plain elites stay as the generator made them (changing their odds would have moved the dice of every floor), so
champions are added on top, on packs with no elite; and a sleeper killed asleep keeps its hoard and its experience - the
reason to sneak is the free round that always lands. The step's noise: two, heavy armour two more, a walk by itself
one more; shaded, half; a Rogue, Ranger or Monk in front, half again; a door four, a chest four, a fight nine, a spell
four, mining eight; a shut door costs four squares of it. The action bar is now redrawn when the floor's kind, the light
or Automatic change (it was cached by the mode alone, and showed Where to? below ground).

Measured (`tools/sim.js`, 20 seeds, Fair, to floor 20): v9.3 15 crowned, 3 fell, median 127 fights; v9.4 15 crowned,
3 fell, median 126 fights. The classic four lead with the Knight, so the simulator's party never shades its light: the
lairs are met with the torch lit, woken or struck asleep.

- **Lairs.** `CM.makeFloor` already places monster groups; now three in five are placed *in a lair* - a dead-end,
  a room's far corner, a wing's end - and begin **asleep** (`group.asleep = true`). A sleeping pack is drawn lying
  (the fall pose at rest, no breath) with a snore in the soundscape when near. The others wander as today.
- **What wakes them**: the party's **light** (a torch is seen from eight squares down a straight corridor, a lantern
  from ten, a glow stone from five, no light from nothing) and the party's **noise** - a number the rules keep:
  armour's weight (plate rings, leather does not), a run (Explore, a walk by map), a fight (the existing
  `noise()` grows into this), a door kicked, a chest's lid, a spell. Noise carries through open squares and halves
  at a door. A sleeping pack within the noise's reach rolls to wake each step; a woken pack **hunts**: it walks
  toward where the noise was, then toward the light, and a pack that reaches the party from behind gets the
  ambush round the game already has.
- **Sneaking.** Without a light (or with it doused - a new action on the torch's line, `Use` on the light, and a
  key) the party sees two squares and makes half the noise; a Rogue or Ranger in front halves it again; the Monk's
  path too. Passing a sleeping pack gives nothing but the way past - and a party that *strikes* a sleeping pack
  gets a free round with every blow a hit (the surprise mechanic exists; this is its reverse). A sleeping pack
  killed outright drops no renown for the kill but keeps its hoard: the dungeon's answer to the question "why sneak".
- **Champions.** One pack in four above floor 5 is led by a champion: the group's leader with a word from a
  table of eight (**Warded** - a shield that takes the first spell; **Frenzied** - two blows a round under half
  health; **Shrieking** - wakes every lair on the floor on its first turn; **Shadowed** - unseen until it strikes
  (the Rogue sees it); **Stonehide** - the first three blows a round bounce; **Vampiric** - heals by its blows;
  **Hoarder** - carries a chest's worth; **Fleet** - acts twice in the order). The word is in its name
  ("a Frenzied Orc Chieftain"), its picture wears a mark (Phase 0's `flash` colour, standing), and it drops a
  champion's trophy for the Hall of Fame card.
- **Elites' loot** moves to the champions; plain elites become rarer. The simulator's crown rate on Fair stays
  within five points of v9.2's; the lairs' sleepers are the lever (three in five, tuned by the sim).
- **Automatic**: douses the torch in the Catacombs and the Vaults when a Rogue or Ranger leads, wakes nothing it
  can pass, strikes sleepers when the party is whole and the pack is small.
- **Saves**: `group.asleep`, `group.champion`, `game.noise`, `game.lightOut` - schema 7, with the migration and
  the fixture test.
- **Tests**: a lair's pack sleeps until the light reaches it and not before; noise through a shut door is halved;
  a sneaking party passes a sleeper on a fixed seed and a lit one does not; each champion's word does what it says
  in a fixed fight; the film replays a hunt the same; the sim's crown rate; Automatic's douse and strike.

## Phase 2 - Things that move: doors, chests, levers, water, fire and windows - v9.5 (graphics; medium) - DONE

As built: `CM.swing` (28-motion.js) eases a thing between two states; the frame remembers when each door, portcullis
and lever was seen to change (a thing first seen is as it was found). A door is its closed picture swung a quarter
turn on its hinge, away from whoever opened it (a corridor is one square wide: a quarter turn lays it along the wall);
a portcullis lifts into the lintel; a lever's two pictures cross over. An emptied chest leaves an open chest standing as
a trace (saved with the floor, like the bottles). Water is drawn by the shader's own branch (glow 4): ripples from the
time, the sky (or below, the torch) in it by the angle, a glint of the sun, a dark green-blue body; the sky dome's
branch had been catching it and was narrowed. In rain the surface's ground darkens and shows the sky low down, and
puddles lie on the roads and paths by the day's hash. The town's windows are lit at night: a glowing quad over seven
windows in ten, the floor's mesh made again at dusk and dawn (twice a day; a bug that rebuilt a dungeon floor with the
town's theme was caught in the screenshots and fixed). Fire needed nothing: the torches already flicker at eight frames
a second and their lights waver.

- **Doors swing**: a door is two quads hinged on the frame's post that rotate 100 degrees over 350 ms when opened,
  and swing back when barred; the Pixel door tile is split in two. **Portcullises lift** (the gate's picture rises
  into the lintel over 600 ms, the chain's rattle with it). **Chest lids open** (the lid's third of the picture
  tilts back) and stay open - an opened chest is seen open from across the room. **Levers throw** (the handle's
  quad rotates). All of it is in the mesh's *dynamic* part, rebuilt per frame only for the few things in motion
  (`renderer.setMoving(list)`), never the floor.
- **Water that moves**: the river, the ford, the Flooded Vaults' pools, the Drowned Town's streets and the
  dungeon's puddles are drawn with a water shader branch (a vertex flag): two scrolling normal-ish ripples from a
  small tiling picture, a reflection of the sky's zenith colour by the view angle, and a shine from the sun's
  direction by day. Below ground the torch's light rides on it. In rain the ground's quads near the party get a
  wet sheen (a `wet` uniform that the sky passes) and the puddles multiply (the scatter's puddle prop at a higher
  rate for the day).
- **Fire**: the wall torches and the campfire are two-frame sprites flickering at eight a second, and their lights
  (Phase 6 of the tenth update) waver by five percent with them. The Foundry's vents breathe on their beat.
- **Windows light at night**: the house facade has a `night` variant with the window glowing (painted once; in
  Stone the plaster photo under it), swapped by `CM.sky(game).night` as the lanterns already are; the tavern's
  windows glow warmest. From the wall-walk (Phase 4) the town at night is a hundred lit windows.
- **Tests**: a door's angle is a function of (opened at, now) and ends at 100 degrees; a barred door is shut; a
  lid stays open after a save; the water flag is on exactly the water cells; the night facade is used only at
  night; the moving list is empty when nothing moves (so the floor is never rebuilt for it).

## Phase 3 - The seasons seen - v9.6 (graphics; medium) - deferred from the ninth update's Phase 2 - DONE

As built: `CM.CROWNS` / `CM.crownOf` (26-surface.js) say what each of the three trees wears in each season and
`CM.CANOPIES` the canopy over the paths; the painters read them (`CM.art.tree(variant, bark, season)`, `CM.art.canopy`)
and the town's and the land's sets are built for the run's season (the set's key has the season in it). Winter oaks and
birches are bare branches, firs carry snow on each tier, spring oaks blossom, autumn oaks redden. `CM.snowLying` (24b):
winter, on a day of snow and the day after; the shader whitens what faces up (roofs, the ground, the wall's walk, the
hedges' tops - a level top from either side, since the eye can stand at a hedge's height). The river is ice on a day of
snow (as the rules already have it: crossed anywhere). Mist lies low on the land (a fog term by height). The orchard's
blossom became the oaks' (the farm has no fruit trees); fallen leaves under the broadleaves were already the ground's
litter. The free camera now sees from its own eye, which the shader needs to tell which way a surface faces.

- **The trees by season**: the three tree kinds get a crown per season (the oak green, deep green, red-brown,
  bare; the fir the same fir with snow on its tiers in winter; the birch green, green, its autumn gold as today,
  bare white), chosen by `CM.season(game)` when the floor's textures are set - the same layer slot, a different
  picture, so the mesh is untouched. The canopy's picture follows. In Stone the leaf photos are recoloured with a
  hue shift at upload (the ambientCG leaf sets are green; autumn is a shift, winter is the bark alone).
- **Snow**: when the season is winter and the weather is snow or the day after it, a `snow` uniform whitens the
  tops of things - the ground, the roofs, the hedges' tops, the crowns, the wall's walk, the signposts' caps - by
  their upward facing (the shader has the facing from `dFdx`/`dFdy` already). The river is a sheet of ice (the
  water branch off, a white-blue plane with cracks) and crossed anywhere, as the rules already say. The scatter's
  grass and flowers are not placed in winter; stones and logs keep a cap of snow (a second prop picture).
- **Blossom and the seasons' props**: spring's fruit trees in the farm's orchard blossom (a pink crown); the
  autumn scatter adds fallen leaves under the broadleaves as a ground decal rather than a prop; summer's tall
  grass as today.
- **Wet ground**: rain darkens the ground's grades (a `wet` uniform, from Phase 2) and the roads shine; mist is a
  fog band at ground level on the land (the renderer's fog with a height term, the dungeon's fog untouched).
- **Tests**: the tree layer chosen is the season's; the snow uniform is on only in winter with snow; the winter
  scatter has no flowers; the ice is where the water was; the land's mesh is the same count in every season (the
  change is in the textures and the uniforms, never the geometry).

## Phase 4 - The wall-walk, the gate towers and the east postern - v9.7 (content and graphics; medium to large) - DONE (the towers' fallback)

As built (`61c-tower.js`): the plan's own fallback for height. The ring wall steps round the hill in diagonals and
runs into the hedges by the gate and the Temple's back, so it is not a walk a party can take a square at a time without
rebuilding the town's wall; that waits for a later update. What shipped: the two towers that flank the West Gate,
drawn as octagons of stone with a merlon on each face (a `tower` kind: the town's grid and fingerprint are as they
were); a stair at each one's foot inside the wall; up it (six minutes) the party stands among the merlons with the
town below, turns to look, and hears the watchman's word on tomorrow's weather; any step, Space or a walk brings it
down; the top is never saved. At sunset from the top: an achievement. The east postern stands in the Keep-yard's
north-east corner, shut until the party has been to floor five (in this run or any - kept in the village store), and
opens onto a cliff path cut along the foot of the cliffs to the fields (laid after everything else on the land, so no
seed's land moved); both ends are on the Where to? list once it is open, and the path is safe at night.

- **Height for the first time**: a surface floor gets `fl.height` {key: 0 | 1.3} for cells on the wall-walk;
  the renderer's eye stands at the cell's height plus the eye height, the mesh lays the walk's floor at 1.3 (the
  town wall's top already is), and a step between heights is a stair cell (the gate towers' spiral stairs, as
  two cells: `stair:up`, `stair:down`, drawn as a stepped quad run) that costs the stair's hour's tenth - six
  minutes. Falling is impossible: the walk's outer edge is the wall's parapet (a low top face), its inner edge a
  rail. Monsters never come up (nothing hunts in the town).
- **The wall-walk**: the ring wall's top from the West Gate's towers round to the Keep-yard's corner on each side,
  with a lookout's hut at the two corners (a bench; a townsperson who looks west and says what the weather will
  be tomorrow, the Calendar's "ahead" made a person). From the walk: the land laid out below, the Wood's glades,
  the river, the farm's rows, the night's lit windows and the chimneys' smoke; at the sunset hour, a line in the
  log the first time, and an achievement ("the view from the wall").
- **The gate towers**: the West Gate's two flanking towers are built as buildings of their own kind (`tower`:
  round in the mesh's eye - an octagon of eight faces - with a conical roof, the stair inside drawn as a dark
  doorway), the portcullis of Phase 2 under the arch between them.
- **The east postern**: a small door in the ring wall at the Keep-yard's north-east corner, locked until the party
  has reached floor 5 (the chronicler mentions it; the key is at the guildhall for 50 gold once renown allows),
  opening onto a **cliff path** cut along the north cliffs' foot - a second surface strip, part of floor -1's map,
  nine squares long from the postern down to the road's bend at the farm. It saves the walk through the whole
  town from the shaft to the land: the "short cut back from the shaft's other mouth" the seventh plan deferred.
- **Tests**: the height map is only on the walk and the stairs; the eye's height follows it; a stair costs six
  minutes; no monster path ever enters a cell with height; the postern is locked before floor 5 and the path's
  length is nine; the land's places list (Where to?) knows the postern once it is opened.

## Phase 5 - The people's part: a fifth place, and the townsfolk's errands - v9.8 (mechanics and content; large)

- **A fifth place.** Behind the four heroes stands at most one **follower** (`game.follower`), not a hero: no
  level, no gear slots, no turn in the fight. Each has a trade that acts by itself:
  - the **porter** (the tavern, 30 gold a run): carries 40 weight - the pack's limit rises by it;
  - the **torchbearer** (the tavern, 20 gold): the party's light burns at half rate and he holds the light high -
    seen from one square further (Phase 1's light); he can be told to douse it;
  - the **dog** (the farm, once the farm has a cow; one gold a day in scraps): smells an ambush a room away (the
    log says "the dog growls" and the ambush round is lost to the monsters), and finds the buried things the Wood's
    cairns hide; it will not go below floor 10;
  - the **hedge-wizard** (the library, when renown allows): one Light a floor and one Mend between fights;
  - the **rescued adventurer** (the one bound in the dungeon, whom `Use` cuts loose): asks to come; a rogue by
    trade, picks the first lock of each floor, and has a story told in three pieces over three floors, after which
    she leaves at the next camp with a gift, and the chronicler's book has her.
  A follower can **die**: a blow that would miss the back row by one point strikes the follower instead (they are
  behind, and not quick); a dead follower is a trace on the floor, a line in the log, a candle at the memorial,
  and the tavern will not hire to this party for a run. Automatic hires the porter when the pack is heavy and the
  torchbearer when a Rogue does not lead; it takes the adventurer always.
- **Errands.** Six townsfolk (the tavern-keeper, the merchant, the smith, the librarian, the priest, the farmer's
  hand) each have an **errand** - a chain of two or three things below, from the seed, told in their own words:
  "my brother's ring is on floor 7, where the Drowned took him" (a thing placed on that floor's seed), "bring me
  three Foundry slag-bars and I'll make something of them", "read what is written on the Palace's fourth carving
  and tell me", "the fungal deep has a mushroom the cook wants", "find who sells the Guildhall's stolen seal" (a
  champion's trophy, Phase 1). Errands are taken by speaking (a line in the dialog), tracked in the Journal's new
  page, and paid in the giver's coin: a discount that lasts, a recipe, a title, a thing, a line of story that
  moves the town's telling (the fifth update's spine has a hook for each). Three errands at a time; one of each
  giver a season. The bot takes an errand when it passes the giver's door and does it if it lies on its way.
- **Saves**: `game.follower`, `village.errands` (schema 7's second half, in the same migration test).
- **Tests**: each follower's trade in a fixed situation; the follower takes the blow that misses by one and no
  other; the dog refuses floor 11; the adventurer's three pieces come on three floors and she leaves; an errand's
  thing is on its floor for its seed and nowhere else; an errand done pays once; the tavern refuses after a death;
  Automatic hires and takes.

## Phase 6 - The Undercroft: a second way down - v9.9 (content; large)

- **Where**: the third cave in the Wood (the one the seed puts deepest) has, past its ore, a stair of old stone
  that the party finds only with a light (Phase 1's light reach: it is dark) - **the Undercroft**, the lower town
  that "went under" in the Harvest Fair's lore, three floors (-2, -3, -4 in the save's numbering; "the Undercroft,
  first vault" in words) of its own theme: river stone, roots through the vaulting, standing water (Phase 2's
  water), drowned houses' fronts as wall decals (the facade painter, mossed), the air heavy with drips and motes.
  Generator 2 makes them with a new fixture set (`CM.UNDERCROFT`): small rooms off a flooded street, a market
  square with a cross like the town's, a chapel.
- **What is there**: its own five monsters (the Drowned Townsfolk - zombies in the town's clothes; the Eel; the
  Marsh Light that leads the party astray - a thing that moves away as it is approached; the Cellar Spider; the
  Bell-Ringer, a champion always); the **tenth guardian** on its third floor - the Bell-Founder's Boy, grown old
  and dead and still ringing a bell nobody hears (the Night of Bells' lore made a fight: his bell wakes every lair,
  so Phase 1 is in play; the relic is the Bell's Tongue, a mace that shrieks - Phase 1's Shrieking as a weapon
  affix, which wakes and frightens); and at the bottom **a door into the Flooded Vaults** - floor 6's wing stair
  from below. Opened once, it is a way down to floor 6 that skips the Catacombs, for parties that have cleared them
  before (renown says), and a way up from the Vaults that comes out in the Wood rather than the town.
- **The telling**: the chronicler has the lower town's story (three carvings in the Undercroft, the spine's rule:
  the walls tell the truth that the town has forgotten); the librarian's errand (Phase 5) sends the party there;
  the Night of Bells changes (the bell is heard in the Undercroft that week, and the boy is easier).
- **Tests**: the stair is in the deepest cave and found only lit; three floors, their numbers, their theme and
  monsters; the guardian is on the third and his bell wakes; the door opens onto floor 6's wing and is remembered
  in the village store; a run that goes down by the Undercroft has the Catacombs' floors untouched; the sim runs
  the route; the films play it.

## Phase 7 - Around the world that moves - v10.0 (small to medium)

- **Fifteen monsters in all** across the bands (the Undercroft's five in Phase 6; ten here: two for each of five
  bands that are thin - the Fungal Deep's Spore Mother, the Crystal Caverns' Glass Hound, the Foundry's Bellows
  Imp, the Palace's Courtier, the Root's Rootling and so on), each with a part set for the drawn painter, a Crawl
  tile where one fits, a call, an ability from the existing table or one new (the Marsh Light's "leads astray" and
  the Spore Mother's "spawns" are the two new ones), and a bestiary line.
- **Balance**: the simulator on all difficulties with lairs, champions, followers and the Undercroft route; the
  crown rate on Fair within five points of v9.2; the sleepers' share and the champions' rate are the levers.
- **Sound**: each new monster's call; the snore; the door's hinge, the portcullis's chain, the lid, the lever;
  water's lap on the surface and the drip in the Undercroft; the wind on the wall-walk; the dog; the bell.
- **Performance**: `tools/perf.js` gets a fourth scene (the wall-walk at night: the whole town's windows and
  smoke in view) and the numbers go here; the moving list and the water branch are measured; Low has none of it.
- **Docs**: the README's section; `LORE.md` grows the Undercroft, the followers and the errand-givers; the
  Timeline's Help and Manual; the plan marked.
- **Tests**: `npm test`; the Timeline's five; the fixture migration from v9.2's export.

## Order, sizes and what depends on what

| Phase | Version | Strand | Size | Depends on | Why in this order |
|---|---|---|---|---|---|
| 0 Monsters that move | 9.3 | graphics | S-M | - | Seen in every fight; teaches the sprite states Phase 1 draws sleepers with |
| 1 The living dungeon | 9.4 | mechanics | L | 0 (the poses) | The biggest change of feel; early, so every later phase is tuned with it |
| 2 Things that move | 9.5 | graphics | M | - | Independent; the water branch is wanted by 3 and 6 |
| 3 The seasons seen | 9.6 | graphics | M | 2 (wet, water) | Closes the ninth update's deferral |
| 4 The wall-walk and the postern | 9.7 | content + graphics | M-L | 2 (the portcullis, the windows) | Height is new ground; after the shader work settles |
| 5 The people's part | 9.8 | mechanics + content | L | 1 (light and noise for the torchbearer and the dog) | Followers want the dungeon's new senses to act on |
| 6 The Undercroft | 9.9 | content | L | 1 (the bell wakes), 2 (water), 5 (the errand that sends you) | Last of the big ones: it uses everything |
| 7 Around | 10.0 | all | S-M | all | Monsters, balance, sound, perf, docs |

Suggested sequence: **0 -> 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7**. A graphics phase follows each mechanics phase so
the suite's numbers can settle between.

## Risks

- **A dungeon that sleeps is a dungeon that is quieter.** Fewer fights per floor means less renown and gold per
  run unless the lairs' hoards and the champions make it up; the sim decides the share of sleepers (three in five
  is the opening bid) and the champions' drops. If the feel is wrong, the lever is one number.
- **Stealth can become the only way to play.** It is kept narrow: the dark is two squares of sight, traps are not
  seen in it, the Mage's and Cleric's spells still make noise, and only the lairs sleep - the wanderers do not.
- **Height is a first.** Every path-finder, the automap, the sprites' projection and the ambush rules assume one
  level. The walk is kept to the town (no monsters, no traps, no fights), the height map is on its cells alone,
  and `pathTo` treats a height change as a stair cell. If it bites, the walk ships as a view from the towers only
  (the stair's top is a lookout) and the ring is a later phase.
- **A follower is a fifth thing to balance.** Followers never attack and never scale; their worth is in weight,
  light, smell and locks - conveniences the party could buy otherwise. The adventurer leaves by design.
- **Three more floors and a tenth guardian** are the content a cloud session could write in a day; the risk is the
  door into floor 6 making the Catacombs skippable. It is gated on renown that proves the Catacombs were cleared
  before, and the daily and weekly dungeons do not have the Undercroft at all.
- **The moving mesh and the water branch** cost on the integrated graphics the step-down is tuned for. Both are
  Detail-scaled (Medium: doors and water, no flicker; Low: none) and `tools/perf.js` measures them in Phase 7.
- **Saves.** One schema rise, one migration, tested against the fixtures and a fresh v9.2 export.

## Not in this plan, and why

- **Interiors you walk through.** The buildings' screens are the buildings; a drawn room behind each dialog was
  weighed and left: it is a picture the player reads for one second on the way to the counter.
- **Hands and weapons in the view.** Not this game's lineage (Wizardry, Eye of the Beholder show the party as
  portraits), and it would hide the floor's new life.
- **A second town, a world map, mounts, fishing with a reel, a market that moves with the seasons.** As the eighth
  plan said: one town, one wood, one shaft - and now one old way under it.
- **Multiplayer or a shared world.** The game is one file in one browser by design.
- **Voice.** The monsters call; the people have their lines in text; the bell rings.
