# Upgrade plan 61: weather, the clock, the fogs and the soundscape - architecture and logic

Asked for 2026-11-05 as a specification in eight parts (time and calendar; the weather engine; magical fogs; the
world's persistence and reactions; lighting; the dungeon coupling; combat synergies; the audio engine), with the
instruction to lay out the architecture and the logic before any code. This is that layout. Nothing here is built.

## 0. What the game already has (so the plan builds on it, not beside it)

| Spec part | Already in the game | Where |
|---|---|---|
| Clock, day/night, dawn/dusk | The game's own clock (a step a minute, a stair an hour, a rest to dawn); dawn and dusk hours by season; the sky's colours blend across the hour before and after; sun and moon on their arc; moon phases | 24-clock.js, 24b-calendar.js, 26-surface.js (CM.sky) |
| Calendar | Four seasons by the real date or pinned; a 29-day moon; twelve festivals, one a month; weather by the seed and the day | 24b-calendar.js, 69ze-seasons.js |
| HUD | The dial with sun/moon, hour, day, season, the weather with five days ahead, the Calendar (K) | 73b-clock.js |
| Weather kinds | clear, rain, mist, wind, snow - one a day, by season's odds | 24b-calendar.js CM.WEATHER_ODDS |
| Sky | Clouds drifting with the wind and their shadows; stars twinkling; an aurora on some clear winter nights; lightning and thunder on some rainy evenings; sun colour by the hour; a rainbow in the sun-shower hours | 76zzzzzc-sky.js, 24c-light.js, 24d-weather.js, 40-render.js |
| Rain on the world | Wet ground with the sky in it, rain streaks down walls, puddles that linger, eave drips, drops on the lens, rings on the water | 76zzzzza-wet.js, 76zzzzzzzzz2-puddles.js, 76zzzzzzzzz4-wetsurfaces.js, 76zzzzzr-lens.js |
| Snow and cold | Snow building over days and melting, lying on roofs and up-facing faces, icicles, drifts; frost on walls and the ground at dawn; the party's breath on a cold day | 69v-weather.js (snowDepth), 76zzzzzzzf-townseason.js, 76zzzzzd-heatcold.js |
| Wind | A direction and strength a day; trees, grass, reeds, crops, washing and banners sway to it; the air's drift | 76zzzzc-wind.js, 26-surface CM.SWAY |
| Birds, fireflies, bats | Birds in the sky by day; fireflies on summer nights; moths, bats and an owl | 46-air.js, 76zzzzf-nightlife.js |
| God rays, haze, heat | Sun shafts through the Wood's canopy and the grates; the air's body; heat shimmer over flames | 76zzzw-air.js (uShaft, uHaze), 76zzzzzd-heatcold.js |
| Lightning in the dungeon | A storm's flash lights the first floors through the grates; day reaches in by the grates | 76zzzzzzzj-stormlight.js, 76zzzzzzzzu-daylight.js |
| Dungeon water | Flooded vaults and the drowned floors as moods; wading sounds by depth; low fog; damp stone | 76zzzzzzo-moods.js, 76zzzzzzzzm-dampdust.js, 76zzzzzzzzs-lowfog.js |
| Weather felt | Rain burns the torch and gusts put it out; mist halves sight; lying snow slows the party; mist makes an ambush likelier | 69v-weather.js, 62-combat.js |
| Torches and lamps | The lamplighter lights the lamps at dusk and snuffs them at dawn; lit windows by the hour | 76zzzzf-nightlife.js |
| Sound | Rain as a hiss and patter, wind gusts by strength, snow's hush; wading; thunder with distance; the mixer, headphones' spatial sound, dynamic quiet | 76zzzzzzzzc-weathersound.js, 76zzzzzzzzf-mixer.js, 76zzzzzzzzg-spatial.js, 76zzzzzzzzj-quiet.js |
| Music | Tunes by place and hour, mood layers, a filter and reverb in the synth | 55-music.js, 76zzzzr-musicmood.js, 76zzzzzzzx-townmusic.js |

So of the eight parts, the sky, the rain, the snow, the wind, the god rays, the dungeon's lightning and the weather's
sounds exist in some form; what is new is the **event engine** (weather as timed events within a day rather than one
weather a day), the **four magical fogs** with their statuses, the **destruction cycle**, the **tactical synergies**,
the **calendar's naming**, the **HUD's predictor**, the **dungeon coupling beyond lightning**, and the **fog sound
pads and adaptive music**.

## 1. The two decisions the specification forces

**1a. Real time or game time.** The spec asks for a 30-minute day and 30-minute night of real time. The game's clock
is the game's: a step is a minute, so the day passes as the party acts, a rest skips to dawn, and - this is the
constraint that matters - the clock is saved with the run and **replays and films play back the same** (every rule
that says lines or starts fights must be a function of the game's state, never the wall's). A real-time clock breaks
replays, makes a long think in a menu turn day to night, and fights the camp's "rest till dawn".

*Recommendation:* keep the game's clock as the one that counts, and give it an **idle tick**: while the party stands
still above ground with no dialog open, the clock advances one game minute every N real seconds (N = 60 real min /
(24 h x 60 min) = 2.5 s for a 24-hour day in 60 real minutes, matching the spec's 30 + 30). Stepping still costs a
minute, so the day moves at the spec's pace when the party watches and faster when it walks. Replays record the
idle ticks as actions (they already record the clock). Below ground the idle tick stops (the dungeon keeps its
hours by steps), unless the user wants the dungeon's time to run too - a setting. Every "real-world minute" in the
spec becomes **24 game minutes** at that pace (a 5-15 minute event = 2-6 game hours).

**1b. One weather a day, or events.** Today the day's weather is one word from the seed. The spec wants events of
5-15 minutes between clear spells, at night leaning clear. These can coexist: the day's word stays the **day's
leaning** (a rainy day has more and longer rain events; a clear day a few clouds), and a seeded **event schedule**
is laid out for each day - a list of [from minute, to minute, kind, strength] - from the seed and the day, so a replay
gets the same storms. `CM.weather(game)` keeps answering the day's word (everything that reads it today keeps
working); a new `CM.weatherNow(game)` answers the event in force this minute, and the systems are moved to it one
by one.

## 2. Architecture

```
rules (tested in Node, deterministic)               window (draws, sounds; wraps the rules' hooks)
----------------------------------------------      ---------------------------------------------------
24e-calendar2.js  year/month/day naming             73c-weatherhud.js  bigger sun/moon, stars overlay, the predictor bar
24f-events.js     the day's event schedule          76...-skyevents.js  tornado funnel, dense fog, dramatic sunsets, meteor
                  CM.weatherNow, CM.windNow,        76...-fogs.js       the fog particle layer and tint, above and below
                  CM.nextWeather (the predictor)    76...-fallen.js     fallen trees, saplings growing
69zzm-fogs.js     the four fogs' statuses           76...-flood.js      knee-high water, waterfalls at the grates, steam
69zzn-trees.js    felled trees, saplings, regrowth  76...-synergy.js    chain lightning's arcs, damped fire
69zzo-synergy.js  spell and arrow modifiers         76...-audio2.js     rain layers, wind, fog pads, dungeon echoes
69zzp-idle.js     the idle tick                     76...-music2.js     crossfades and the low-pass under storms
```
The rules never read the wall clock. Each window file wraps `CM.beforeFrame` (as the weather files do now) to
read `CM.weatherNow(game)` and set renderer fields; the renderer takes new uniforms the way uRainbow and uWaterMist
were added. The audio side builds on 50-audio.js's AudioContext and the mixer's buses.

## 3. Logic, part by part

### 3.1 Time and calendar
- `CM.calendarOf(game)` -> { year, month (1-12), day (1-30), name } from the run's day count, starting Year 500,
  Month 1, Day 1; the seasons stay as they are (three months each), the festivals keep their months.
- The idle tick (1a): `game.idleTick()` called by the frame loop every N real seconds when `game.mode === "explore"`,
  no dialog open, the floor above ground (or the setting allows below); it is an action in the replay stream.
- Dawn and dusk: the sky already blends over an hour each side of them; at the spec's pace an hour is 2.5 real
  minutes, so the 5-minute transition is two game hours: widen CM.sky's blends from 1 to 2 hours. Shadows (the sun's
  direction) follow the same arc already.
- HUD: the dial's sun and moon drawn larger (the moon's face already is); a star field laid over the dial at night
  by the sky's `stars`; the **predictor bar**: a strip under the dial showing the next six game hours as coloured
  segments from the day's schedule, the next change named ("rain in 40 min"), and the full date and time.

### 3.2 The weather engine
- `CM.weatherSchedule(seed, day, season, leaning)` -> events: a seeded random walk over the day: clear gaps of 1-6
  hours, events of 2-6 hours (the spec's 5-15 real minutes at the pace above), kinds weighted by the season and the
  day's leaning; at night the odds of starting an event fall to a fifth, a running event may carry over. Kinds:
  rain (light, heavy, storm), mist (dense), wind (gale), snow, aurora (clear winter nights), tornado (rare, on gale
  days in autumn), heat (summer afternoons), and the four fogs (rare; see 3.3). A strength 0-1 per event, rising
  over its first ten minutes and falling over its last.
- `CM.weatherNow(game)` -> { kind, strength, since, until, wind: { dir, speed } }; `CM.nextWeather(game)` -> the
  next event and when. Both pure functions of the game's seed and clock.
- The window reads them each frame and sets what exists today (rain rate, wet, puddles, snow, wind, mist, cloud
  cover, lightning) by strength instead of by the day's word, and adds: the dense fog (uMist deeper, sight to one
  square), the gale (wind k 1.0, the air's debris, the lamps guttering), the tornado (a funnel of rotating particles
  on the horizon that crosses the land, drawn in the sky dome and as air, with its sound), dramatic dawns and dusks
  (the sun colour's glow widened on clear evenings after rain), heat (uHeatAll over the horizon by the afternoon's
  heat).

### 3.3 The magical fogs
- Four events, each 15 real minutes = 6 game hours, rare (a few a season), scheduled like the weather; they **do not
  stop at the shaft**: `CM.fogNow(game)` answers the same below ground.
- Statuses as a party-wide field `game.fog = { kind, until }` read by the rules: orange - spells cost half again as
  much and deal a fifth less (62-combat's cost and damage hooks); green - a point of poison to each hero every ten
  game minutes (the camp's and the step's tick); brown - strength x0.8 in the stat hook; purple - each cast has a
  tenth chance of wild magic (a random spell of the same tier) and a status may shift at the round's end.
- The window: a coloured particle layer (the "fog" air kind tinted, denser) and a tint on uFog/uHaze, above and
  below; the HUD names the storm and its time left; the sound pads (3.8).

### 3.4 The world's persistence and reactions
- Torches and lamps: the lamplighter's round already follows dusk and dawn; add `CM.lampsOut(game)`: in a gale or a
  storm each lamp has a chance per hour of going out (a seeded roll), to be relit by the lamplighter's next pass;
  the dungeon's wall torches gutter in a draft (3.6).
- Mud: rain's strength over the last hours -> `CM.mudNow` 0-1 on earth squares; a step on mud costs an extra
  minute at full mud (as lying snow does); the ground shader darkens and glosses earth by it (uWet already does the
  gloss; mud adds the darkening on dirt).
- Snow on foliage: the snow uniform already whitens up-facing faces including the crowns; extend the canopy
  layers' tops. Breath puffs: 76zzzzzd's breath on the party extends to the figures (a puff particle at the head
  joint of each body when cold).
- Felled trees: `CM.fellTrees(game, event)` on a tornado or gale picks a few interior trees (never the ring that
  bounds the map, never a landmark) by seed and marks them in `game.ext("fallen")` with the day; the floor's grid
  treats a fallen square as open with a log prop lying across it; after three days the log goes and a sapling
  stands (a small tree picture, impassable again); after seven more it is a tree. The mesh rebuilds when the set
  changes (the floor key already includes the season).
- Wind on everything: exists; add the figures' capes and the banners' sway driven by the event's wind speed.
- Birds scatter: `CM.nextWeather` gives the warning: thirty real seconds = 12 game minutes before a storm or
  tornado the air spawns a burst of birds from the nearest crowns, flying away from the wind.
- Fireflies on warm clear summer nights: exists; tie to the heat and the event (none in rain).

### 3.5 Lighting
- God rays after rain: uShaft already gives sun shafts under the canopy and at the grates; add the shafts over
  the land for the hour after a rain event ends when the sun is low (cloud gaps), strength by the event's tail.
- Lightning shadows: the flash already whitens; add a one-frame directional shadow pass: during a flash the sun
  direction is set to the bolt's direction and uSunK to 1.5 for the frame, so the walls' facing and the contact
  shadows jump; the town's shadow caster (76zzzv-shadows) takes the bolt as the light for that frame.
- Long sunset shadows: the shadow caster stretches shadows by the sun's elevation already; lengthen the cap.
- Heat haze: uHeatAll exists for the furnace bands; drive it by the heat event over the far land only (a horizon
  band in the fragment shader).

### 3.6 Dungeon coupling
- `CM.aboveNow(game)` answers the surface's event from below ground, by the same schedule.
- Fogs: 3.3, fully active below.
- Dripping and waterfalls: rain above -> the "drip" air kind on the first floors at the ceiling at a rate by
  strength, and the damp uniform rises; a storm -> a waterfall at each grate square (a column of the "rain" kind
  falling from the ceiling with a splash ring on the floor, and the floor wet around it).
- Flooding: a flood event (the heaviest rain, rare) -> `fl.floodedBy(game)` marks the lowest hallways (the pits
  and sunk halls from 69zzi-levels) knee-deep: drawn as the flooded mood's water on those squares, wading sounds,
  the party slowed a minute a step; it drains over the next day.
- Drafts: a gale above -> the dungeon's haze drifts faster, the torches' flicker doubles and leans, the howl is
  heard muffled (3.8).
- Seismic shocks: a meteor event (rare; "a star falls", scheduled like a tornado) -> a screen shake and a rumble
  above and below, a crater prop where it fell on the land; lightning through grates and high windows exists -
  extend the lit rooms to those with the daylight grates.
- Steam: standing in floodwater or under a drip in a fire band (Foundry, the Furnace) -> steam puffs (the smoke
  kind, pale) that raise the haze in that room, shortening sight for the ambush rule.

### 3.7 Combat synergies
- `CM.weatherMods(game, spell|arrow, target)` in 69zzo-synergy.js, read by 62-combat's damage and range hooks:
  electric spells in a storm, or on a target standing in water (the flooded squares, the river's ford, floodwater),
  deal +25% and chain to one adjacent foe for half; fire spells in rain deal -25% and lose their spread; arrows and
  bolts against a headwind lose a square of range, with a tailwind gain one (the wind's direction against the
  facing).
- The window draws the chain's arc (the spell-light system) and the damped fire's smaller burst.

### 3.8 The audio engine
- `CM.Weatherscape` in a new window file over 50-audio.js: a set of procedural loops, each a node graph on the
  mixer's ambience bus, with a target gain set each frame from `CM.weatherNow` and eased:
  - rain: three layers (filtered noise: patter = band-passed bursts, downpour = broad noise, roof = short clicks)
    mixed by strength; thunder = a noise burst through a long convolver-less feedback delay, panned by the bolt's
    bearing (the spatial system's panner when headphones are on);
  - wind: noise through a resonant low-pass whose cutoff and gain follow the gust envelope (76zzzzc's gusts);
  - the fogs: orange - a crackling static (sparse impulse noise through a high-pass) over a 55 Hz hum; green - a
    soft bubbling hiss (band-passed noise with slow random dips); brown - a 40 Hz drone pulsing every two seconds;
    purple - a crystalline arpeggio of sine partials with slow random detune;
  - the dungeon: the same loops through a low-pass at 600 Hz, a third the gain and a short reverb tail (the
    synth's reverb), plus drips (the existing drip clicks at the rain's rate) and the drafts' howl;
  - effects: a tree's crack (a sawtooth snap into noise) on a felling, the meteor's rumble (sub-bass noise swell)
    with the shake, splashing footsteps (the wading sounds, already by depth) on flooded roads and corridors.
- Adaptive music: 55-music's output through a master low-pass; under a storm or a fog the music's gain eases down
  by a third and the cutoff from 20 kHz to 1.2 kHz over four seconds, and back when it clears; the mixer's sliders
  still apply.

## 4. Order of work (each a release; versions follow the order done)
1. The clock's pace and the calendar (3.1 without the HUD): the idle tick as a replay action, the calendar naming,
   the wider dawn and dusk; tests for determinism and the replay.
2. The event engine and the predictor HUD (3.2, the HUD of 3.1): the schedule, CM.weatherNow, the systems that
   exist moved to it by strength, the predictor bar; tests for the schedule's shape and night's leaning.
3. The new sky and air (3.2's dense fog, gale, tornado, heat, dramatic dusks).
4. The magical fogs (3.3) above and below, with their statuses and the HUD.
5. The world's reactions (3.4): lamps out, mud, breath on the figures, felled trees and saplings, the birds'
   warning.
6. Lighting (3.5).
7. The dungeon coupling (3.6): drips, waterfalls, floods, drafts, steam, the meteor.
8. Combat synergies (3.7).
9. The soundscape (3.8): the loops, the fog pads, the dungeon's echo, the effects.
10. Adaptive music, then a screenshot and listening pass of every place in every event.

## 5. Tests, determinism and risks
- Every rules function above is a function of (seed, clock, state): the schedule, the fogs' statuses, the felled
  trees, the synergy modifiers. Tests pin them; a replay test runs a recorded day with idle ticks and storms and
  checks the same lines and fights.
- The frame budget: the fog particles, the waterfalls and the tornado are air kinds under the Detail budget; the
  loops are a dozen nodes.
- The spec's "real-world minutes" are read at the pace of 1a; if the user wants the wall clock instead, the idle
  tick's rate becomes a setting and the replay records the ticks either way.
- Felled trees change passability: the test for every place reachable (the world map's) runs with trees felled.
- The fogs' statuses touch the rules' balance: the numbers above are starting points, held in BALANCE.md.

## 6. The decisions, as given (2026-11-05), and what they change above
- **The films and replays are gone** (v71.0): no replay determinism to keep. The weather, the fellings, the meteors
  and the fogs roll their own dice at the moment they happen (seeded by nothing but the moment); the rules stay
  pure functions of the game's state for the tests, but nothing need play back the same. Section 1a's idle tick is
  replaced by **the clock that runs**: a game minute every 2.5 real seconds on the floor, in a fight or at camp,
  above and below ground alike, whether the party moves or not (a day an hour); a step still costs its minute.
  Settings > Clock: Runs / By steps only. Done in v71.0.
- **Weather as events, free, more and stronger**: not a static script - 3.2's schedule becomes a live engine that
  rolls the next event when the current one ends (kind and length by season and hour, night leaning clear), with
  stronger looks and effects than the day's-word systems have; the day's word keeps answering `CM.weather` for the
  old readers until each is moved to `CM.weatherNow`.
- **Twelve named months, numbered beside the name** (v71.0): Thawlight, Sowmoon, Greening (spring); Highsun,
  Hayfall, Emberwane (summer); Harvestmoon, **Claudetober**, Lanternfall (autumn); Frostbell, Deepsnow, Longnight
  (winter). Thirty days each, from Year 500; a run begins on its season's first month. **The Lich King is Claude,
  the Lich King** (v71.0).
- **Any tree may fall** - to a gale or a tornado, or burned - and the square stays solid while it lies and while
  the sapling grows, so nothing opens a way out of the map: a fallen or charred tree is a different picture on the
  same solid square, not an open one (this is simpler and safer than 3.4's open-square log; section 3.4 is amended
  to it). A tornado touches only trees, in its wake.
- **Meteors a couple of times a week at least**, landing where the party can walk (an open square reachable from
  the party's floor, never a building), leaving a **meteorite ore chunk** to pick up (an ingredient that sells, and
  a smith's material: a meteor-iron edge, to be given a recipe), and sometimes starting a fire.
- **Fire**: a burning tree burns a while, then falls charred; charred trees go after a few days and a sapling
  takes their place as after a gale. Fire spreads tree to tree (a chance per minute per burning neighbour, less in
  rain, none in snow, out in a downpour), never to buildings, fences or the party: it is a sight, not a harm - the
  glow, the smoke, the crackle, the embers in the air, the blackened ground after.

## 6a. The order, revised
1. v71.0 - the clock that runs, the calendar, the films out, the Lich King named. **Done.**
2. The event engine, live: `CM.weatherNow`, the next event rolled on the fly, the predictor bar and the big sun
   and moon and stars on the dial; the existing rain/snow/wind/mist/cloud/lightning driven by the event's strength.
3. The stronger sky and air: dense fog, gale, tornado, heat, dramatic dawns and dusks.
4. Trees: felled, burning, charred, the sapling and the regrowth; the tornado's wake; fire's spread; the lamps out.
5. Meteors and the ore: the strike, the crater, the chunk, the fire it starts, the shake and the rumble above and
   below, the birds' warning.
6. The magical fogs, above and below, with their statuses and the HUD.
7. Lighting; mud; breath on the figures.
8. The dungeon coupling: drips, waterfalls, floods, drafts, steam.
9. Combat synergies.
10. The soundscape and the adaptive music; then the pass over every place in every event.
1. The clock: the idle tick at the spec's pace (24 game minutes a real minute while standing) - yes, or the wall
   clock outright (replays then record the ticks as they happened)?
2. Does the dungeon's time run while the party stands still below, or only by steps (today's way)?
3. The calendar's month names: twelve of the game's own (the plan will name them by the seasons' lore), or plain
   "Month 1-12"?
4. Felled trees: allowed in the Deep Wood only, or in the town's trees too (the yards' trees shade the houses)?
5. The meteor: in the plan as a rare event with a crater, or left out?
