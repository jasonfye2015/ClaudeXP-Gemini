# Claude and Magic - the twelfth big update: the Mage Tower

A plan for v10.1 to v11.0, from the player's description of 31 October 2026. In the Deep Wood stands a tower of
black and grey stone, many stories tall, with two great dark-brown doors, fog lying round its foot and dark shrubs
crowding it. One hero goes in alone - a caster for choice, or anyone with a bow or a crossbow - and inside, the game
changes: no squares and turns, but a close, quick first-person fight in the manner of Wolfenstein, through larger
rooms and wider halls, floor after floor. Each floor's ladder up is guarded by a floor boss: a monster of the floor,
made more, and seen to be more. Forty floors; on the fortieth, in one great hall broken only by pillars to hide
behind, the King of the Tower, a caster who walks, casts and every few seconds is somewhere else. Between floors the
hero may leave, sell, mend and come back to the floor after the last one cleared. In the town, beside the shaft, a
portal yard holds the tower's portal and room for more such challenges later.

The shape in one line: **one hero, a staff or a bow, forty floors of a tower that fights back in real time, and a
king who will not stand still.**

---

## Principles

- **The tower is its own place, with its own pace.** Nothing in the shaft, the town or the land changes its rules
  for it. Inside, time runs: the frame's clock drives the tower (a fixed step, so the Node tests can drive it the same
  way). Outside, the game is turn by turn as ever.
- **One hero, the party's own.** The hero who goes in is a hero of the party, with their level, gear, health and
  magic; what they win (experience, gold, things) is the party's. The others wait at the tower's foot.
- **The seed makes the tower.** Each run's tower is made from its seed: the same forty floors for the same seed, so a
  run can be talked about and a film can follow it.
- **Leave and come back.** Progress is the run's: the last floor cleared is kept, and the tower is entered again at
  the floor after it. A hero who falls inside is carried out by the tower itself, at one health, and the floor they
  fell on is not counted.
- **Both looks, Low detail, reduced motion, a pad.** As everywhere else.
- **Automatic does not climb the tower.** It is the player's challenge; Automatic stops at the door.

## Phase 0 - The portal yard and the tower in the Wood - v10.1 (content and graphics; medium) - DONE

As built (`61d-magetower.js`): the portal yard in the Keep-yard's free corners (the lit portal north-west, the
two plinths south); the tower in a clearing north of the fields, laid after everything else on the land, nine squares
of a `magetower` kind drawn as one octagon of black stone, seven stories with darker bands and narrow violet windows,
a slate cone and two iron-banded doors facing the path south; dark shrubs at the clearing's edge, fog drifting at any
hour and mist lying in the clearing. The doors' dialog lists each hero, who may go in and why not; going in is phase 2.

- **The portal yard**, in the Keep-yard beside the shaft: a ring of standing stones with a paved floor, and in it one
  lit portal (an arch of stone with a turning light in it) and three dark plinths for challenges to come. Space at the
  lit portal: the party steps out at the tower's front in the Wood. A matching portal stands by the tower's door for
  the way back.
- **The tower**, in a clearing of the Deep Wood that the seed places away from the glades and the caves, reached by a
  path: drawn as a great octagon of black and grey stone (the town's tower kind, larger: three cells across and many
  times as tall), with windows lit faintly at each story, a conical slate roof, and two dark-brown doors on the
  front. Round its foot: dark shrubs (a scatter of their own, near-black green), and fog - low mist in its clearing at
  any hour, and wisps drifting off it.
- **The door**: Space at the doors opens the choice of hero. Those who may go in: Mage, Necromancer, Druid, Cleric,
  Bard, Artificer (the casters) - and any hero with a bow or a crossbow in hand (a Ranger, most often). The list says
  why a hero cannot (a sword is no use in there).
- **Tests**: the portal yard is in the Keep-yard and the portal takes the party to the tower's front and back; the
  tower's clearing is the seed's and is reachable; the choice lists exactly the heroes who may go.

## Phase 1 - The tower's floors - v10.2 (content; medium to large)

- **A generator of its own** (`CM.makeTowerFloor(n, seed)`): a square floor, larger than the shaft's (33 to 41 cells
  across), of big rooms (5 to 11 cells a side) joined by halls two and three cells wide, Wolfenstein's way: doors
  between rooms, side rooms, a few long galleries. The start at one end, the ladder at the far end in a boss room.
- **Its own theme**: black and grey stone, arcane light (purple-white torches in sconces), a colder fog; the Pixel
  look from Crawl's stone tiles in its own colours; the Stone look's darkest photographs.
- **Floor 40**: one nearly open hall, pillars set through it to hide behind, the throne at the far end.
- **Floors as numbers**: tower floors are `1001` to `1040` in the save, never among the shaft's; their names are
  "the Mage Tower, floor n".
- **Tests**: every floor is connected; the ladder is reachable; the boss room holds the ladder; halls are at least two
  wide; floor 40 is open with pillars; the seed's floors are the same twice.

## Phase 2 - Moving and shooting in real time - v10.3 (mechanics; large)

- **The tower's loop** (`CM.TowerRun`, a class with a fixed step): the hero's position and facing are continuous; the
  frame loop steps it by the frame's time. Keys: W/S forward and back, A/D (or Q/E) sidestep, the arrows and the mouse
  (when the view is clicked: pointer lock) turn. Movement slides along walls; doors open as the hero walks into them.
- **Shooting**: the left button (or Space, or F) fires the hero's bolt: a caster's own (Magic Missile's violet, a
  Cleric's holy light, a Druid's thorn, a Necromancer's shadow), an archer's arrow. Bolts fly at a speed, strike the
  first monster in their path or the wall. A caster's bolt costs magic, a little; magic comes back slowly. An archer's
  arrows are counted (the quiver from the pack; ten found on each floor). The right button (or 2) is the hero's
  great spell, if they have one: Fireball (a burst), Frost (a cone that slows), Lightning (a line), Smite (the
  strongest single blow) - dear in magic.
- **The HUD**: a crosshair, health and magic bars, the quiver, the floor, the boss's bar when it is in sight, a small
  automap.
- **Damage** from the rules the game has: the hero's level, their weapon or the spell's power, the key stat.
- **Tests**: the step moves and slides; walls stop; a bolt flies and strikes the first thing; magic is spent and comes
  back; arrows are counted; the same inputs at the same step give the same run.

## Phase 3 - Monsters in real time, and the floor bosses - v10.4 (mechanics; large)

- **The tower's own monsters**, from the game's kinds by the floor (the first bands' low, the Deep's high), at a level
  from the hero's and the floor's. Each has a state: idle (it stands, or walks a short beat), alert (it has seen the
  hero - a line of sight within its eyes' reach, or heard a shot), chase (it walks the shortest way), attack (a blow
  within reach, on a cooldown; a ranged kind shoots its own bolt; a caster casts). They take the motion of the
  eleventh update: breath, lunge, flinch, fall.
- **The floor boss**: one of the floor's kinds, made more: half again as large on screen, a coloured aura, a champion's
  word (the eleventh update's eight), twice the health and more; it stands in the boss room by the ladder and does
  not leave it until the hero is in it. Its bar is on the HUD while it is in sight. Its drop: a thing of the floor's
  worth, and gold.
- **Tests**: a monster sees the hero only with a clear line; chases by the shortest way; strikes on its cooldown;
  ranged kinds shoot; the boss is larger, has its word, keeps its room, and drops its things.

## Phase 4 - The ladder, leaving and coming back - v10.5 (mechanics; medium)

- **The ladder**: once the boss has fallen, Space at the ladder offers "Climb to floor n+1" or "Leave the tower". The
  floor is counted cleared either way.
- **Leaving**: the hero comes out of the doors to the party; experience, gold and things are the party's; the
  party can go home (the portal), sell, mend, and come back. **Coming back**: in at the doors, at the floor after the
  last cleared, fresh (its monsters back, the hero's health and magic as they are outside).
- **Falling**: the tower carries the hero out at one health; the floor is not counted.
- **Saved** with the run (`game.tower = { cleared, hero }`), and in the Hall of Fame card ("Mage Tower: floor n").
- **Tests**: clearing counts; leaving keeps it; coming back starts at the next floor; a fall counts nothing and
  carries the hero out; the save keeps it.

## Phase 5 - The King of the Tower - v10.6 (content and mechanics; medium)

- **Floor 40's hall**: pillars to hide behind; the King on his dais. He walks, casts (a bolt of his own, a ring of
  fire that grows from him, a summoning of two of the tower's monsters, a curse that slows), and every 1 to 15 seconds
  - the dice say - he is gone in a burst of light and stands somewhere else in the hall, never within three cells of
  the hero. At half health he speaks, and his casting quickens.
- **His fall**: the tower is quiet; a relic of his (the King's Circlet: magic comes back twice as fast, everywhere), a
  title, an achievement, and a line in the codex.
- **Tests**: the teleport's wait is always 1 to 15 seconds; he never lands within three cells or in a wall; each spell
  does what it says; the second phase at half; the relic.

## Phase 6 - Around the tower - v11.0 (small to medium)

- **Balance**: a headless climb by a simple tower bot (aim, shoot, back off) measures how far heroes of each level and
  calling get; the floors' monster levels are set from it.
- **Sound**: the doors, the portal's hum, bolts and their strikes, the King's teleport, the boss's call.
- **Performance**: `tools/perf.js` gets a fifth scene, a tower floor with eight monsters in view and bolts in the air.
- **Docs**: the README, `LORE.md` (who the King was, and why the tower stands in the Wood), the Timeline's Help and
  Manual; the plan marked.

## Order

| Phase | Version | Size | Depends on |
|---|---|---|---|
| 0 The portal yard and the tower | 10.1 | M | - |
| 1 The tower's floors | 10.2 | M-L | 0 |
| 2 Moving and shooting | 10.3 | L | 1 |
| 3 Monsters and bosses | 10.4 | L | 2 |
| 4 The ladder, leaving and coming back | 10.5 | M | 3 |
| 5 The King of the Tower | 10.6 | M | 3, 4 |
| 6 Around | 11.0 | S-M | all |

## Risks

- **Real time in a turn-based game.** The tower's loop is apart from the rules' clock: the run's clock moves only
  when the hero comes out (an hour a floor climbed). The loop has a fixed step so it can be tested and filmed; films
  record the tower's inputs a step at a time, or the tower is left out of films (decided in Phase 2).
- **The renderer was made for squares.** It already draws the eye anywhere and billboards anywhere; free movement
  needs only the camera driven by the loop and collision against the grid.
- **One hero against a room.** The tower's monsters are fewer and slower to see than the shaft's packs, and the boss
  waits in its room; the balance bot sets the numbers.
- **Mouse look in the Timeline's window and in browsers**: pointer lock on a click into the view, Esc releases it; the
  keys alone always suffice.
