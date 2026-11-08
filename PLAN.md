# The Hollow Oak - build plan

The design document (Claude Docs): https://claude.ai/artifact/JtQZ3J468Lqh9E8QqoVXfS

## Phase 1 - the tree - done

- game/tree.py: the hollow's shape (a fluted, narrowing ring wall, root buttresses, chambers bulging into the wood at
  the landings, knot-holes), the ledge spiralling from the floor to the crown (rising stretches and flat landings:
  gallery, larder, high hollow, crown), the root tunnel in, and walking it (floor_at, ceiling_at, can_stand).
- game/night.py: Claude walking it (slowly; Shift hurries), falling off the ledge's edge, the clock (dusk to dawn in
  about 2.75 real hours), places named the first time he enters them, and her eyes watching from high perches.
- engine/treemesh.py + engine/render.py: the meshes from the same functions; normal-mapped bark and earth, the lantern,
  glowing fungus with its light, moonbeams with dust, the sky through the crown, fog pooled low.
- ui/: the title over the slow look up the hollow, the pause, the view; in the Timeline (Apps, every computer's Games).

## Phase 1b - the fog - done

- engine/fogfx.py: low layers of ground fog over the hollow's floor, thinning upward, and wisps of mist hanging in the
  air (most low, a few far up), turning slowly on air that barely moves; a little along the root tunnel. Drawn with a
  drifting noise, thinning at the wall and when seen edge-on, fading near the eye and into the far dark, lit warm by
  the lantern near him and pale by the moon toward the crown.

## Phase 1c - the dark roots, the night sky - done

- The root tunnel far darker (its wood and earth shaded down), and his lantern's throw short and dim there
  (night.lantern_reach: about 2.2 units at a third of its strength deep in the roots, opening out to 6.5 in the hollow).
- The sky darker, the stars twinkling, and a faint aurora: two wavering curtains strung across the sky, each in layers
  (green low, violet high) with rays shimmering along them, slowly breathing - seen through the crown.

## Phase 1d - the den dressed - done

- game/den.py: water dripping from the ledge's edge and the knot-holes into puddles; vines hanging down the wall from
  under the ledge and from the crown; roots snaking from the wall's foot, knotted, half buried; leaf litter on the
  floor, the ledge and the tunnel; low dark places where small eyes watch.
- The world shader: damp earth in patches, puddles (dark, flat, catching the lantern, the fungus and the moon) pooled
  in the bowl and under every drip; the wall damp at its foot. Drips falling and ringing where they land.
- night.py: six sets of small eyes in the dark near the ground, blinking; gone when he comes near or his lantern
  reaches them, turning up somewhere else in a while.

## Phase 1e - the lantern in his hand; darker - done

- game/lantern.py: an old lantern low on oil - always flickering, sputtering every few seconds, guttering out every
  minute or two (the first time within the first minute); a shake (E, or L) brings it back about two times in three.
- engine/held.py: the lantern drawn in his hand at the lower right - iron posts, a brass foot and cap, a ring - bobbing
  and swinging as he walks, thrown about by a shake; the light comes from its flame, as bright as the lamp allows.
- Everything about a third darker or more: the lantern's light (and its reach, more so in the roots), the ambient,
  the fungus's light, the moon.

## Phase 1f - the wand, the dark, the breathing fungus - done

The lantern hangs by its ring from the crook of Claude's wand (KayKit's, CC0 - copied once into assets by
tools/export_wand.py), held out low from the right and swinging as he walks, thrown about by a shake. When it goes out
the den goes darker still (the faint bounce of its light goes with it; only an ember is left). Each patch of glowing
fungus breathes on its own slow cycle (6 to 15 seconds), fading almost out and growing back, and its light with it.

## Phase 2 - webs and movement - done

game/web.py: three strands across the hollow, each from one turn of the ledge to a higher one (four cables woven
together, sagging; walkable only out over the hollow, so the ledge stays the ledge); her loom across the hollow at 4.5,
meeting the ledge where it passes; the crown web at the crown landing. His weight dips whatever he stands on. The
dressing: webs over three knot-holes, tangles under the ledge and at the chambers' backs, low sheets among the roots,
threads hanging into the dark, the first strands in the root tunnel.

game/night.py: the floor is the tree's or the silk's, whichever is higher. On a strand he goes along it only, and sways
- a lean sprung back by his balance, pushed by the strand's bounce (more when hurrying or turning hard); A and D lean
against it; past the limit he slips off the side and falls (into the loom, if it's below). The silk sense:
night.silk (gentle and hurried distance, slips, falls into the web), night.tremor (how hard it shakes now) and
night.manner() (-1 prey to 1 careful) - for her moods in phase 3. A hard shake brings her eyes sooner.

game/brood.py: 24 of her small ones on the wall, the floor, the loom and crown web and the strands, resting and
scurrying, bolting from him (sooner when he hurries, or his lantern finds them); strays turn up again about him.
Drawn from Quaternius's Spider, baked to frames (tools/export_spider.py -> assets/spider.npz).

engine/silkmesh.py + render.py: silk as camera-facing ribbons (never thinner than a pixel - fainter instead), lit as
threads (bright only where a light glints along them; silver under the moon at the crown), shivering with the tremor,
dipping under him; the view leans with his sway. engine/sound.py + ui/audio.py: wind, the silk's hum, creaks, the
catch, skittering, the lantern's rattle and puff, a thud - synthesized, following the computer's mute.

Tests: test_web.py (strands, loom, a gentle crossing, hurrying and leaning, what she feels), test_brood.py.

Phase 2b - across his eyes (done): game/crawlers.py - every 20 to 30 seconds a small spider (3 to 8.5% of the
screen's height) runs across the view itself in 0.55 to 1 second, in just off one edge and out just off another, on a
slight curve; three times in ten, two at once by different ways. Drawn flat over everything (Quaternius's spider, seen
from above, its legs going), lit by the lantern - a dark shape when it's out - with a skitter close by.

Phase 2c - her babies, close (done): game/babies.py. Danglers: every 25 to 45 seconds one drops on a single thread a
little before him (from the dark overhead, or the tunnel's roof) and stops at the height of his face, bobbing and
turning; walk into it and the thread is gone and it runs off across his eyes (crawlers.scurry); left alone, it climbs
back up. The swarm: with the lantern out, one comes up the wand and onto the lantern after 2-4 seconds, then another
every 10-20, to 5-7 in all, crawling all over it; a shake that lights it and they all let go, each hanging from it on
a thread of white silk, swinging, for 1.5-4 seconds before falling away; a shake that fails throws one or two off.

## Phase 3 - Ysmeine

Her figure (Quaternius's Spider, scaled), her moods, the language model's voice with its guardrails and memory, the
visual-novel scenes; a scripted fallback.

## Phase 4 - the night

The six acts, the clock, offerings, venom, saves; the six endings (each closing "Ending n of 6: <name>").

## Phase 5 - music, sound, polish

A new style on the ClaudeRPG-style sound engine; the den's sounds; text only for her voice (unless a fitting local
text-to-speech turns up).
