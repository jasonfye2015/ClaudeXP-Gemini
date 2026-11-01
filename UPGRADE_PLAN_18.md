# Upgrade plan 18: fights worth watching (v23.0 - v23.4)

Asked for 2026-11-01: items 14-19 of the graphics list - the whole "combat presentation" set. What was there to
build on: CM.Effects (45-fx.js: projectiles with a landing, bursts, rings, flares, rain, drift), the recipes in
80-main.js (castFx, spectacle), monsters' poses (28-motion.js: a lunge, a flinch, a fall, a flight, a rise), the
damage numbers (floatAt), the camera's shake and punch, the title card, and Settings > Combat speed (normal, fast,
as good as instant) dividing every effect's time.

## v23.0 - spells that travel (14)
- Every spell aimed at foes leaves its caster's hand - the hero's own side of the view - and travels: Magic Missile
  three darts, Frost a shard to each foe, Lightning a crack from the hand, Call Lightning and Smite from above, Sleep
  and Lullaby a drift of motes, Turn Undead a wave of light rolling out, Drain a red stream coming back.
- Each lands with an impact - a ring on the floor, a burst, a flare of its light on the walls.
- Some leave something on the ground for a while: fire burning, frost glittering, holy light, thorns and roots.
- Spells on the party rise about the caster's side of the view instead.

## v23.1 - blows that land (15, 16)
- A critical hit is marked by the rules (a weak spot, a knife from behind): a white flash, a bigger gold number with
  a "!", a hit-stop - the effects hold still for a moment - and the camera nudged toward the blow.
- Recoil by the weight of the blow: a big hit knocks a foe further back and rocks it; a monster's lunge winds up first
  (it draws back, then comes), and a heavy one's lunge is bigger.

## v23.2 - entrances (17)
- A boss or guardian enters on a stage: black bars close in, the camera holds on it while it rises, a banner with its
  name and where it rules, a sting of music. Any key or click skips it; the fight waits until it is done. (The title
  card had stopped showing: the recipe had two cases for "intro" and only the first ran.)

## v23.3 - who's next (18)
- A strip across the top of the view in a fight: this round's order, heroes and foes, the one acting lit, the fallen
  struck through; it moves on as each acts and is dealt again each round.

## v23.4 - the pace (19)
- Settings > Combat speed: Quick, Normal or Cinematic (and As good as instant). Cinematic slows the effects a little,
  holds the hit-stops and the entrance longer, and pushes the camera in on crits and kills; Quick trims the pauses.
