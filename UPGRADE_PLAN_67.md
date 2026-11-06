# UPGRADE_PLAN_67 - Being engaged: facing the attacker, the flourish, and the lock

The complaint: a wandering group comes up from the side or behind and the fight begins, and at that moment the
motion keys stop answering. The lock is right (the fight is turn by turn, and the ways out of it - flee, parley, a
Scroll of Teleport, the last foe down - all exist), but the first second of it feels like the controls broke, and
when the attacker came from behind the party cannot even see what is hitting it: the foes are drawn on their own
square, which is behind the camera.

## 0. What exists

- `wanderMonsters` (61-explore.js) walks a group toward the party and, on an adjacent square from any of the four
  directions, calls `startCombat(k, thing, true)` (`theyCame`). Nothing turns the party; `fl.facing` is never
  touched by a fight.
- `startCombat` (62-combat.js) rolls surprise: "They're on you before you can draw!" (their free round), "You have
  the drop on them" (ours), the dog's growl that forbids an ambush, heavy armour that invites one. The only sound is
  the dog's bark; the only sign is a line in the log and the party bar's action buttons changing.
- The window places the foes on `game.foeKey` (80-main.js `foePlace`), fanned out left to right across the camera's
  yaw. From the side or behind, that square is off screen.
- Fleeing (`flee`) goes "back the way you came": the square behind the facing. If the attacker stands there, the way
  is not clear and the flee fails - the one case where the lock really bites.
- The renderer already has the pieces for a flourish: `shake(strength)`, `punch()`, `rollTo`, the screen effects
  (focus, swirl, lens) and the music engine's leitmotifs (55-music.js); the UI listens to `game.on("mode")`.

## 1. Turning to face the attacker (the rules' side)

Option A - **snap and settle** (recommended). When a fight begins and the foes' square is not the one the party
faces, `startCombat` sets `fl.facing` to the attacker's direction before the first round. The window animates the
turn (the same yaw easing the Turn keys use, a touch quicker), so the attacker swings into view as the fight opens.
Fleeing then goes away from the attacker, which is what "back the way you came" meant.

Option B - **snap only for ambushes**. Turn only when "They're on you before you can draw" - the party caught
napping spins round; a group that walks up in plain sight, from the side, is met as the party stands. Cheaper on
surprise, but it leaves the side-attack case with an off-screen foe, which is the complaint.

Option C - **free turning in the fight**. The Turn keys keep working in combat as a free action (no turn spent):
look around, and the foes stay on their square - turn your back and they are behind you. Fleeing goes the way you
face. Honest and flexible, but it makes it possible to lose sight of the fight and confuses "which way is out";
better as a later setting than the default.

**The several-directions rule** (all options): a fight is one group, so there is one square to face. If a second
group reaches the party while the first is still standing, it waits (it does today - the engaged group's fight is
the only one) and the party keeps facing the first. When the first fight ends and the second group engages, the
party turns to it then. The facing changes only at a fight's start, never between rounds: no bouncing. The same
holds for a group that flees and another that steps in. (The "hordes" mutator's extra foe joins the first group's
square, so it changes nothing.)

Edge cases: the facing change is written before the fight's dice are rolled, so replays agree; a fight begun by
the party walking into a group (`theyCame` false) already faces it; set-piece fights made by `groupAt` put the
group on the square ahead, so they face it too; the Mage Tower's and the Fortress's own fights have no facing and
are untouched. A setting "Turn to face attackers" (on by default) for players who prefer the old way, and reduced
motion makes the turn instant.

## 2. The flourish (the window's side)

Three tiers, by how the fight began, each with a look and a sound:

| began | look | sound |
|---|---|---|
| ambush ("They're on you") | a red glow at the view's border that blooms and fades over a second, a short camera shake, the party bar flashing once | a sharp stinger: a drum hit and a low brass swell, and the music drops to its fight bed |
| met ("The party meets them" - plain) | an amber border glow, no shake | a shorter stinger, two notes |
| the drop ("You have the drop on them") | a gold border glow and a slow punch-in | a bright stinger, rising |

- The glow is a DOM overlay on `#view` (a box-shadow inset animated by a CSS class the UI adds on `game.on("mode")`
  and a new `game.on("engaged", { how, from })` event), so it costs the renderer nothing and works with every look.
- The stinger is synthesised in 50-audio.js like the other sounds (a "stinger" with three variants), so there is
  no new asset; with the music engine, the fight bed (a sparser, lower take of the floor's leitmotif) comes in
  under it and the exploring bed returns on the fight's end. (The boss music already does this for guardians and
  the king; the ordinary fights get a lighter version.)
- A line in the view, not only the log: "FROM BEHIND" / "FROM THE LEFT" for a second when the party turns, so the
  turn reads as the party's reaction and not a camera glitch.

## 3. The lock, made legible

- The moment the fight begins, the party bar's action buttons light up and the Turn/Forward/Back buttons dim with
  a tooltip ("in a fight: Flee (R) to run"), so the lock is seen, not discovered by a key that does nothing.
- A key pressed on a dimmed button during the first second says, once a fight, "They're on you - fight, or flee."
- Flee stays as it is (the square behind the new facing, which is now the square away from the attacker), and the
  Scroll of Teleport's sure flee is unchanged.

## 4. Order

1. Release 1: the facing (Option A with the setting), the "engaged" event with its `how` and `from`, the camera's
   turn, and the tests: engaged from each side, the facing afterwards; two groups adjacent - the second waits and
   is faced only when its fight begins; the replay agrees; `groupAt` fights unchanged.
2. Release 2: the flourish - the border glow and the direction word, the three stingers, the fight bed in the
   music, the dimmed movement buttons with their tooltip and the once-a-fight line.
3. Later, if wanted: Option C as a setting ("Turn freely in a fight").
