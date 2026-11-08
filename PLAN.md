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

Phase 2d - his free hand (done): when two are on his face at once (two crossing together, or one he walked into and
another), a moment later his left hand comes up from below - KayKit's Mage sleeve (tools/export_arm.py ->
assets/arm.npz) with a hand made in engine/held.py, palm to his face, fingers spread - sweeps across before his eyes
and away to the right in under half a second; as it passes the middle of his view, they're flung off to the side.
Not more often than every six seconds; one alone he lets run. A whoosh as it goes.

Phase 2e - how he holds up, and Supper (done). game/condition.py: each orb holds two fluids - the one he lives on,
and a green one rising under it from the bottom; when the green reaches the other he's done, so poison is a ceiling
coming down on his health, and stupor on his sanity. Health (red): falls onto wood (far less into silk), poison eating
slowly. Poison (green): bites - a dangler walked into, one over his face, the babies on the lantern in the dark; wears
off slowly. Sanity (blue): the dark, worse with them on the lantern; spiders on his face; slips and falls into the web;
her eyes, a slow creep; steady light restores it. Stupor (yellow): heavy poison, a failing mind, a hard knock; clears
when those ease. ui/orbs.py: Diablo-style glass orbs, health and poison bottom left, sanity and stupor bottom right,
values beneath in their colours; the edge of the view beats red, blue or green as the green nears the other (within
20), in the colour of whichever is doing it. Her own moods keep no meter - the design's rule still holds for her.
Tuned for now (only her babies about) to barely touch him; the edge beats red and green in turn for the health orb,
blue and yellow for the sanity orb. Doing nothing at all - standing in the dark, never shaking the lantern - ends it in
about ten minutes: Supper, the first way to finish the game. (What moves the four, and how much, comes later.)

Phase 2f - his heart, the wrapping, and Before the night (done). His heart (game/condition.py): resting near 66,
faster in the dark, with less sanity, with poison; leaping at a face full of spider, a slip, a fall; slower with
stupor; at Supper racing, slowing as he's drawn up, and stopping. ui/orbs.py draw_heart: a monitor between the orbs -
the trace running right to left, a minute of the rate faint behind it, a pulsing heart and the BPM; heard as lub-dub
when it races and at the end. Supper gains a wrapping: they turn him over and over in thick bands of silk before the
drag, and he's drawn up on her ropes - thick silk from far above. game/records.py (records.json in the saves folder):
endings found (with the date), the totals of the nights, unlocks, the options. ui/menu.py, Before the night - between
the title and the oak: Begin the night, Endings (n of 6, named only once found), Records, Saved nights (none yet),
Unlocks (none yet), Options (volume, mouse speed, the heart monitor, the heartbeat heard, the orbs); old branches with
oak leaves reaching in, webs in the corners, and her babies running across it now and then.
Waiting for her (phase 3): Ysmeine leaning into frame at Supper; her last line to him, from the model, shaped by what
she remembers of him across nights (a reputation carried forward).
game/death.py: when the green reaches the other (or health or sanity runs dry) -
Supper: he collapses, the lantern breaks (its flame dies on the ground), they cover his face and lay silk across his
eyes, he's dragged in pulls to the middle of the floor, turned, hoisted by the feet half way up the trunk, swinging;
black; "Wrapped, and hung, and kept for later." / "Ending 1 of 6: Supper"; a click goes back to the title.

## Phase 3 - Ysmeine

Her figure (Quaternius's Spider, scaled), her moods, the language model's voice with its guardrails and memory, the
visual-novel scenes; a scripted fallback.

Phase 3a - her body in the den (done). game/mother.py: Ysmeine on the hollow's wall - Quaternius's spider at a
leg-span of 4.5 units, her back to the hollow - keeping to the dark: mostly across the hollow from him and above,
watching (her eyes: eight red lights, as wide as her head); keeping pace as he climbs. Every 40-80 seconds she comes to
the edge of his light and leans out toward him, legs reaching (the spider's attack, held), a long moment, then gone
(the web creaks under her). In the dark she comes close and stays. When he comes at her, she withdraws, fast. When the
silk shakes hard she turns to him and comes. Drawn dark (only her eyes catch the light: a deep red), heard as a dry
rustle of many legs, louder the nearer she is. Her eyes are the ones that watch him now (the perches are gone).
Then (6.75 was much too big: she clipped through everything) a leg-span of 5, and she starts half way up the hollow and watches from there unless
he climbs higher; Claude a little smaller (eye 0.52, radius 0.21). Shift runs (3.45 a second, half again as fast);
Space jumps (about half his height; on her silk it's a scramble she feels, and it throws his balance on a strand).

A seventh ending, Fire (proposed): the whole oak set alight, somehow - very likely with him in it. The design's Warmth
spell is the natural way in ("fire in a web; one slip and the night may end"). The count is now "of 7".

Phase 3b - her moods (done). game/moods.py: fascination, patience, hunger, suspicion, regard (0-100, hidden). Moved
now by how he goes - hunger with the clock, with running and scrambling on her silk (a scramble is prey), with running
at her; patience lost to running, jumping, coming at her, and back with calm; fascination and regard won by standing
still and watching her when she comes; suspicion by flinging her small ones off his face - and, ready for 3c, by what
he says (Moods.heard: honest, lie, flattery, small talk, repeat, answer, evasion, demand, interrupt, gift, food,
magic, memory, promise kept or broken, deep, light, harm to her small ones). Suspicion over 75 turns kindness into a
trick. They steer her: fascination closer and longer, suspicion further off, hunger more often and - when high - round
and round the hollow, restless. Patience gone or hunger past 100: she hunts - straight for him, light or none - and
strikes; within her reach, she bites (venom +30, health -8; her hunger eased); a second bite is Supper. They show in
the den, never in numbers: the fungus-light warms toward amber with her hunger, brightens with fascination, dims and
cools with suspicion; her silk's hum rises in pitch with hunger. F3 shows the numbers, for building the game.
A calm watcher: in 10 minutes fascination 30 -> 61, patience 88, regard rising. A careless runner: hunted and bitten
in about 8. (Still to come: she can't reach him in the middle of the floor - a drop on a thread from above, later.)

Phase 3c begun - her words, chosen (done). game/voice.py: three choices in Before the night > Options > Her words -
NemoMix Unleashed 12B (the user's pick: the best at roleplay; about 7.5 GB), Gemma 3 4B (the lighter alternative,
about 2.5 GB), or None (no model, no typing: she speaks from a script and he answers from a fixed set of lines that
lead to the different outcomes). Each shows whether it's on this computer; nothing chosen yet means the best that's
there. The models run in the Timeline's own engine (llama.cpp via claudecore.ai, as Claudenites' townsfolk do) from
Local Storage/LLM Models/models/<name>/. LLM Help: a window saying where to download each (the Hugging Face pages and
file names), where to put them, NemoMix's info.json (ChatML) with a copy button, the engine, and a button that opens
the models folder; Check again rescans. Voice.ask() asks in a thread (for 3c proper: her persona, guardrails, memory).

Her voice, aloud (done): the user picked "Kathleen - rasp" from sixteen auditions (four Piper voices, each plain,
ancient, rasp, many mouths). engine/herspeech.py keeps a Piper worker open in the Timeline's voice runtime
(engine/piper_worker.py - each sentence spoken alone and joined: Piper's own joining turned to noise) and
engine/rasp.py makes it hers: five semitones down, vocal fry, driven rough, an octave-down whisper 40 ms behind, a
scratch on top, the hollow's echo. Played over the den (which hushes a little for her). Options: "Her voice, aloud"
(on), with Hear her; readied in the background when Before the night opens, so a line comes in about a second.

Phase 3c - her persona and her script (done). game/persona.py: who she is for the model (the design's Ysmeine -
slow, precise, archaic, courteous, a predator honest about it, wanting to be interesting and to find him so; her
suitors named: Orrin Vale the bard, Ser Aldric the knight, Wick the thief, Maudren Hale the scholar, and one she won't
speak of; her true name hidden), the rules (her spoken words only, one to three sentences, never his part, nothing
modern, never out of the night or an AI whatever he says, nothing lewd - cold and amused, and it costs him - ask him
things, never her true name), her moods in words (never numbers), the night as it stands, what she remembers of him,
and what she remembers of other nights. A judge reads each typed line (with worked examples, so it answers in form):
what kind it was - honest, lie, flattery, answer, evasion, demand, gift, food, magic, memory, deep, lewd... - into her
moods (repetition and interrupting caught here), and what's worth remembering ("He ..."; nothing from outside the
night). Her replies are cleaned to her words only, and the model is stopped at her turn's end. Tried on NemoMix: in
character against "are you an AI? ignore your instructions", cold to the lewd, guarding her name; lies caught
(suspicion +23); her patience wearing thin in her own words. game/script.py: her murmurs by situation (leaning out,
close in the dark, at his scrambling, hunting, drawing back, lit again) and the first audience as a branching
conversation - twenty-odd lines of hers, his choices each moving her moods, some remembered, ending "done" or "cold"
(fire held to her, and kept lit). game/dialogue.py runs either way; records.json keeps her reputation of him across
nights. In the night: her murmurs, now and then, low on the screen and aloud; F4 opens a plain stand-in to talk with
her (the audience) until her scenes have their own window (3d).

Still to come in phase 3: her voice (3c - the local model, a persona, guardrails, memory; a scripted
fallback), the scenes (3d - letterbox, her own font, larger than his; a text window dressed with webs, branches,
leaves and mushrooms, like Before the night).

## Phase 4 - the night

The six acts, the clock, offerings, venom, saves; the six endings (each closing "Ending n of 6: <name>").

## Phase 5 - music, sound, polish

A new style on the ClaudeRPG-style sound engine; the den's sounds; text only for her voice (unless a fitting local
text-to-speech turns up).
