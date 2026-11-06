# UPGRADE_PLAN_68 - The title card as a weather show

Asked for: a title card that shows off the weather and the plants - over "Claude" a meteor strikes and leaves its ore
lying just above the word; over "and" heavy rain and thunder; over "Magic" a tornado, nearly still, swirling; and
lower, behind the drifting lines of what the game holds, a dense line of trees.

## 0. What exists

- The card (77-splash.js) is a DOM layer over everything: a warm dark hall, the emblem striking a stone in sparks, the
  name forged letter by letter, a CSS sky that keeps the real hour and season (sun or moon in its phase, leaves, snow,
  petals or fireflies), the eleven callings, three marquee lines, the version. It is up within the first second.
- The game already has every effect asked for, in 3D: the meteor (69zzn / 76zzzzzzzzzzk: a streak, a flash, a crack
  and a rumble, a crater, Meteor Iron to pick up), the storm (76zzzzzzzzzzh: lightning at any hour, rain by strength,
  the thunder), the tornado (76zzzzzzzzzzi: a funnel of dark whirling air), and the Quaternius mesh trees in their
  seasons (35d-plants, 37b, 76zzzzzzzzzzq).
- But the 3D packs are not ready when the card appears: the dolls decode at about 1.4 s, the plants at several
  seconds, the figures later still. And the card's three words have to be hit exactly, which a 3D camera can't
  promise across window sizes.
- The card's words are out of date: "Fifty floors in ten bands", "the Lich King on floor 20", "Fifty floors down"
  (and the launcher's description says "Twenty floors down"). They should say seventy and a hundred.

## 1. The design: three acts over the three words, a forest below

The name stays the centre. Each word gets its own weather, anchored to the word's box (measured after layout, so it
holds at any window size), and the three run on one loop so the card is never all noise at once.

| beat | over "Claude" | over "and" | over "Magic" | below |
|---|---|---|---|---|
| 0.0-1.2 s | (the name is forged, as now) | clouds gather | the air begins to turn | the tree line fades up out of the dark |
| 1.2 s | a pinprick high in the sky, then a streak, burning, at a steep angle | rain begins, light | dust lifts into a slow spiral | the trees take the wind |
| 1.9 s | **impact** just above the word: a white flash, the letters lit from above, the card shakes, sparks and rock thrown out, a ring of dust | rain heavy | the funnel forms: a tapering column of dark air, debris circling it | the wind leans the trees toward the funnel |
| 2.4 s on | the crater glows and cools; a chunk of **meteor iron** sits on its lip just above the "C" - black, with a hot grain that pulses down from orange to a dull red over 20 s, steam curling off it | every 6-11 s: a **lightning** fork from the cloud to just above the word, the whole card lit blue-white for a frame, the word's letters flashing, thunder a beat later (louder the closer the fork) | the funnel holds nearly still, swaying, swirling; leaves and grit lift from the ground under it and are flung out of the top | the trees bend and recover in gusts; under the storm the nearest are wet and dark, a few leaves torn off and blown toward the funnel |
| loop | a new star every ~45 s (a smaller one, far off) | the storm comes and goes in strength | the funnel wanders a few pixels and back, never leaves its word | the marquee lines drift past in front of the trunks |

The sky behind keeps the real hour (the sun or the moon) as now, and the season dresses the trees: green, autumn
gold, bare with snow on the boughs, blossom in spring. At night the lightning is the brightest thing on the card.

## 2. How it is drawn

Option A - **a 2D stage painted in code** (recommended). One canvas layer under the card's text: its own small particle
engine (rain streaks, sparks, dust, leaves, steam), the meteor's streak and flash, lightning as a jagged branching
path drawn once and faded, the funnel as stacked rotating ellipses of soft dark noise with debris on orbits, and the
tree line from the game's own pictures. Up in the first second, aligned to the words exactly, cheap (it can run at 60
fps on the slowest machine the game supports), and it stops the moment the card is left.

Option B - **the live 3D scene behind the card**. The game's renderer draws a staged view of the Wood's edge with the
real mesh trees and the real weather systems, and the card becomes partly transparent over it. The most "real" -
it *is* the game's weather - but it can only start once the plants are decoded (several seconds of an empty card),
the camera can't be made to put a funnel exactly over "Magic" at every window size, and it costs the GPU while the
game is still loading behind the card.

Option C - **A now, B's trees later**. A from the first frame; when the plant meshes are ready, the renderer draws the
tree line once into an image (an offscreen render of the real Quaternius trees in the season, a long row at dusk
light) and the card cross-fades its painted trees to that. The words' weather stays 2D and exact; the forest becomes
the game's own meshes. The best look of the three for a little more work; recommended as release 2 of A.

Either way:
- **Sound**: the strike's crack and rumble, the rain's hiss, the thunder, the wind's roar under the funnel - the
  game's own sounds, but only after the first click or key (browsers forbid sound before a gesture; the Timeline's
  window allows it at once, so there it plays from the start). The thunder is delayed by the fork's distance.
- **Reduced motion**: a still card - the crater and its ore, the storm cloud with rain frozen mid-fall, the funnel
  drawn still, the trees upright - no flash, no shake.
- **Weight**: no new assets; the 2D stage is about 400 lines in a window file of its own (77b-splashwx.js), the card
  keeps its emblem, name, callings and marquee on top.
- **The words fixed**: the tag and the marquee lines say seventy floors to the Lich King and a hundred to the bottom,
  the sixty curated rooms, the stage pieces; the launcher's description too.

## 3. Order

1. Release 1 (Option A): the stage layer anchored to the three words, the meteor and its ore, the storm with
   lightning and thunder, the tornado, the painted tree line by season, the sound after a gesture, reduced motion,
   and the card's words brought up to date. Checked by screenshots at three window sizes and at night and by day.
2. Release 2 (Option C): the real mesh trees rendered once into the tree line when the plants are ready, cross-faded in.
