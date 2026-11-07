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

## Phase 2 - webs and movement

Walkable silk strands across the hollow (balance, vibration, sound), silk sense, her small ones scurrying.

## Phase 3 - Ysmeine

Her figure (Quaternius's Spider, scaled), her moods, the language model's voice with its guardrails and memory, the
visual-novel scenes; a scripted fallback.

## Phase 4 - the night

The six acts, the clock, offerings, venom, saves; the six endings (each closing "Ending n of 6: <name>").

## Phase 5 - music, sound, polish

A new style on the ClaudeRPG-style sound engine; the den's sounds; text only for her voice (unless a fitting local
text-to-speech turns up).
