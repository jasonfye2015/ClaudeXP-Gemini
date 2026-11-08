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

Her hand (done): the user picked Italianno from ten free calligraphy fonts - fancy, elegant, readable
(assets/fonts, SIL OFL). ui/fonts.py: her words in it, larger; his in a plain serif; both sized in Options (60-160%).
Used now for her murmurs and the F4 stand-in; her scene window (3d) next.

Phase 3d - her scenes (done). game/scene.py + ui/scene.py: the first time he steps onto her loom, the audience
(F4 starts it any time, for building the game). The frame letterboxes; the view goes dark a moment while she's set
down before him on the loom, facing him; then a composed camera - low, to the hollow's side of him, looking up at her,
drifting - holds on her. The night goes on (her hunger too), but nothing small drops onto him; between her lines her
breathing, a leg shifting, her small ones crossing her back, and his breathing in the sound. Her window: low across
the frame, growing to fit, dark, dressed with old branches and oak leaves along its top, a cobweb in its corner,
glowing mushrooms at its feet; "Ysmeine" in gold at its head; her words in Italianno, written out as she speaks them
(a click shows them whole); his last words above in his own hand; below, his answer - typed (a model) or chosen (the
script) - and "Go on" at the end. Then the dark again, she's gone to the wall, the frame opens; night.met records how
it ended. Her eyes, close: deep glossy red, with a glint of whatever light there is. (The F4 stand-in is gone.)

Phase 3e - the letter, the notebook, unlocks (done; the user's next round). ui/pages.py: Begin the night shows her
letter first - silk (pale, fibrous, a sheen, frayed, threads trailing), in her hand; on its back the way to the oak, her
mark, "Bring no fire" - beside what it means to him: why he goes anyway, and that the silk is soaked in her venom and
something meant for him that makes it impossible to refuse. Go to the oak, or not tonight. Esc in the night now offers
Go on, View letter (front and back), Notes, Unlocks, Back to the title. Notes (game/notes.py; kept in records.json
across nights and deaths): a notebook flipped through - The invitation, Her (name, what she hides, what she is, how old,
what she wants, what she fears), Her ways (her silk sense, the edge of the light, the dark, the three tells in the
fungus, her small ones, her bite, her hunting), Her guests (seven suitors: Orrin Vale, Ser Aldric, Wick, Maudren Hale,
Brother Fennick, Isolde of the Marr, and the one she won't speak of) - each page written when he learns it (her
words, the script's lines, what she does, her moods seen in the light), with a word low on the screen. Unlocks: endings,
guests found, pages written by section, anything else.

Time and weather (done; the user's next round). game/sky.py: a magical forest - in real time the night lasts an hour,
the day ten minutes, dusk and dawn two minutes each (a night begins at dusk, 7 pm, Saturday the 31st of October). The
den is no brighter by day, but light comes down from the crown and through the knot-holes in shafts - golden by day,
orange at dusk, rose at dawn, moonlight by night. The weather: clear (by night the aurora - and only then), overcast
(grey; no stars), rain, thunderstorms (lightning lights the den, thunder rolls), snow; it turns every 7-20 minutes.
Rain and snow fall through the hollow; puddles grow on the floor and ledges, snow settles white, and dry or melt after;
she shines wet in the rain. The rain hisses down the trunk. ui/dial.py: the clock, top right, as the other games show
theirs - the sky of the hour with the sun or moon on its arc, the moon's face, the time and part of the day, the date,
the weather and its strength. (Weather may open other endings, later.)

Her guests (done): game/cocoons.py + engine/cocoonmesh.py - seven suitors wrapped in silk where she hung them: four
against the wall of the hollow's floor (Orrin Vale and his broken lute, Ser Aldric and his sword, Wick and his picks,
Isolde of the Marr and her fire-tipped arrows), two in the gallery's chamber (Maudren Hale and her book, Brother
Fennick and his beads), and one high by the crown with nothing beneath it. Close, and looking: "F - look closer". The
silk splits - torn strands drifting - and her small ones pour out of him every way across the floor (and some onto
his face); his sanity and heart take it; she feels it (suspicion, and much more for the one by the crown). He learns
who it was: a page of his notes.

Still to come in phase 3: her voice (3c - the local model, a persona, guardrails, memory; a scripted
fallback), the scenes (3d - letterbox, her own font, larger than his; a text window dressed with webs, branches,
leaves and mushrooms, like Before the night).

## Phase 4 - the night

Sub-phases: 4a the acts (done) - 4b offerings (done) - 4c spells (done) (Warmth: the road to Fire) - 4d venom (and the antidote) (done) -
4e saving (done) - 4f the rest of the endings (The hidden, Fire) and each ending's own scene (done). Phase 4 done.

Phase 4a - the acts (done). game/acts.py: threshold (in, to her loom) -> audience (her loom) -> gallery (her guests;
sent up to look at them) -> supper (her larder; she calls him down at midnight, or sooner once he's looked at three of
her guests; entering the larder begins it) -> crown (she goes up to her web under the moon and calls him at 3 am;
stepping onto it begins it) -> dawn. She calls when he's late (her calls: in her words, aloud). What she's asked shows
in the pause and as a word when it changes. Supper's script ends as her moods decide - guest, or meal (her bite: the
first is venom; the second is Supper). The crown's script: what he wants of her - to know (and ask for her bite's
gift), to stay (and mean it), her true name (not tonight), to go home alive. With a model: each scene its own opening
and closing; the judge hears "stay". After the crown, T waits with her for the light. Dawn decides: bitten and little
thought of - Cast out; held dear and staying - Bound; held dear, still fascinating, never caught lying, never bitten -
The gift; otherwise Dawn. game/ending.py: the dawn light down into the den, her last words (her hand, her voice), the
dark, the line, "Ending n of 7: ..." (Supper 1, Cast out 2, Dawn 3, Bound 4, The gift 5, The hidden 6, Fire 7).

Phase 4b - offerings (done). game/offerings.py: a silver ring in the mud of the root tunnel, a live mouse scurrying
where the roots open into the hollow, moths about the low fungus, a comb of honey on her larder wall (her own), Orrin's
lute string and Maudren's journal under them once opened (the journal: a page of his notes - a clue to her true name).
F takes; he carries them (shown low left); in her scenes "Offer her something..." opens his pack. Worth to her by her
mood and the hour: moths delight early, are only kind late, insult her starving; a mouse delights her hungry, insults
her fed ("I am not a cat"); the ring delights if she thinks well of him, else reads as a bribe; Orrin's string touches
her fascinated, else he's a thief like Wick; the journal softens her doubt; her own honey amuses her fascinated, else
he stole it. Script: her answer for that gift and worth, and the talk goes on; a model: told how it lands.

Phase 4c - spells (done). game/spells.py: 1 Light, 2 Warmth, 3 Illusion, 4 Memory, each with a short rest between
casts (shown low in the middle). In the den: Light hangs a hard white orb before him a few seconds - the den lit, her
small ones scattering, three old marks cut in the wood that only it shows (notches in the roots, names behind her
guests, a word burnt under the crown: a new "Old marks" section of his notes); near her it hurts her eyes (she pulls
back; doubt up, patience down). Warmth: a small flame in his palm - a comfort (sanity up, stupor down); she likes it at
a distance, distrusts it close; cast on her silk, the silk smoulders (an ember, the oak shaking, her terrified -
flagged "smouldered": the road to Fire, 4f). Illusion: her small ones lose him for 15 s. Memory: steadies him. In her
scenes "Cast a spell..." makes them gestures: Light insults her; Warmth from off her silk pleases her a little, on it
enrages her; Illusion dazzles her or she sees through it (more likely the more she doubts him: suspicion jumps);
Memory - one of three true memories of his own (his mother's hands, his first candle, the night Thornwick threw him
out), each once a night - his most intimate gift: she keeps what she sees (into her memory of him), and answers it.

Phase 4d - venom (done). game/venom.py: her first bite leaves her venom in him for the rest of the night (his poison
never wears below 20): the edges of his sight darken and pulse (Options can still it); his hands shake - a spell
comes apart three times in ten, in the den or before her; what he types to her comes out slurred (a letter lost, a
sound dragged out, a word stumbled on, two swapped); her silk's hum bends and wavers. A second bite while it's in him
is Supper (once it's out of him, a bite is the first again). Now and then (40 s after the bite, then every two or
three minutes) he sees through her eyes for seven seconds, standing still: her larder and the phial hidden behind her
stores; himself, far below, watched; the oak long ago, and someone with hands cutting a word into its heart (notes:
The phial, Through her eyes, Before it was hollow). The antidote: a stoppered phial on her larder floor, seen once the
vision shows it (or by Light); F takes it, Q drinks it - if she sees, she knows it was stolen. Or, in her scenes,
"Ask her to take her venom out of you" (once a night): she gives it if she thinks well enough of him and doesn't
doubt him too much; else he wears her bite till dawn. A model is told he's envenomed, or cured, and how.

Phase 4e - saving (done). game/saving.py: the night saves as each act begins (night_act.json, in the saves folder),
and a quick save (night_quick.json) with F5 or "Save here" in the pause - not while she's talking to him, not through
her eyes, not falling or swaying, not with her coming for him. Kept: where he is, the clock and the weather, her
moods (and her bites), how he's holding up, the act and its outcomes, what he's found, carries and given, her guests
opened, what he's chosen, her venom and the visions seen, the memories given her, the places seen, and what she
remembers of him tonight (and his lies). The den's live things - her small ones, the lantern, she herself - start
fresh about him. The title: "Go on from a save" lists them (newest first). Begin clears them (a new night); an ending
leaves them, to go on from. A night gone on with is the same night: its time counts, not as another night or meeting.

Phase 4f - the rest of the endings (done). Fire: Warmth on her silk a second time, in the den or before her, and it
catches - no more night: flames up from below, sparks, the den lit orange, the roar of it, her last words, the dark.
The hidden: a secret for the player to find - how it's reached is in game/hidden.py and nowhere else, on purpose. And
each ending its own scene (game/ending.py LOOK): she's before him, framed, for Dawn, Bound, The gift and The hidden
(game/scene.py's placing and camera); Dawn in warm light, Cast out grey and alone, Bound with the silk closing over his
sight, The gift with her venom glowing green about him, The hidden in gold, Fire in fire.

## Phase 5 - music, sound, polish (done)

The score (engine/music.py: the game's own, made as it plays, mixed into the den's sound under her voice): exploring - a
low drone (D and A), harp and bell plucks falling like drips down D minor, long silences; her scenes - a slow waltz in
three (an original eight-bar tune over Dm-Bb-Gm-A), each beat a little out of true; the crown - the waltz opened out,
strings over the drone, the melody on bells; each ending its own short coda (Supper: silence). Her moods move it:
hunger past 45 brings a heartbeat under the drone, quickening; patience under 55 drops melody notes; suspicion over 55
adds a second voice a semitone wrong and a moment late; fascination warms and slows the bells and steadies the waltz;
venom bends and wavers the pitch. Notes are made once and kept; the waltz's made ahead (no stall at the crown). Options:
a Music level.
Supper's last moments: as he's hung she comes down to him, close, and he looks at her - and she speaks (in her hand,
aloud): one quiet line, without cruelty, from what she made of him - held dear; lied to; met before; walked her silk
with care; bitten - or, with a model speaking for her, its own words if they come in time.
Polish: Options for how fast her words come and for steadier light (the lantern's flicker smoothed, the lightning only
a glow); the Saved nights page lists the night's saves to go on from; the README tells the whole night.

## Phase 6 - in his hands

Phase 6a - the satchel (done). game/satchel.py: four places, and what's in them doesn't keep - the mouse kicks for three
and a half minutes, then it's still (and a still mouse is worth less: she likes them kicking); the moths get out one
by one (two or three left are hardly a gift); the honey drips, and her small ones follow it onto his face. A full
satchel takes nothing more. The mouse wheel puts one thing in his left hand (engine/itemmesh.py: held low on the left,
cupped, palm up - the mouse kicking, the moths beating about his fingers, the phial glowing green on him); G puts it
down at his feet (a live mouse or the moths are simply gone; the rest lie where he left them, to take again). Tab opens
the satchel over the den - leather, stitched, the night going on behind it (he can't walk with his hands in it): each
thing drawn as itself on the cloth, where he found it, how it is now, and what she made of it other times he gave it
her - written there once he's seen it (records.learned, kept across nights). In her scenes, what's in his hand is
held out first; the rest are offered as cards with what he's learned. Picked up, a thing flies into its place on the
strip low on the left. A model is told what he's holding. Saved with the night: the satchel, his hand, what's put down.

Phase 6b - the notebook in his hands (done). ui/journal.py: Esc - the view tilts down and his notebook lifts into it, the
night going on around him (he stands still while he reads; a small one on his face, a dangler, a bite, her strike:
it's knocked from his hands). The left page its contents; the right what he's turned to, a page turning between:
Notes on her (written first, three to a page, back and on), Her letter (in her hand), What's been found, Options
(drawn in ink: sliders to drag, boxes to tick), Save here, Back to the title (Leave / Stay). The true pause is P, or
the window losing the computer's attention - "The night waits"; in her scenes Esc still pauses.

## Phase 7 - led by her letter (done)

game/autoplay.py: Nav - where he is (the root tunnel, the floor, a turn of the ledge, her silk) and a way from there to
anywhere through the oak (out of the tunnel, up the ledge from its foot, onto her loom where the ledge meets it, into
the chambers, onto the crown web); a step that never comes closer in 3.5 s sets him on past it. Director - the night,
act by act: Light at the old marks, the ring and the mouse, onto her loom; her guests (keepsakes taken, room made in a
full satchel), the moths, the gallery; down to supper when she calls; the crown's mark and her web; T. Her scenes:
his lines chosen as her moods would score them (never a lie, never to stay), the best gift held out, a memory shown
her at the crown; with a model speaking for her, his lines typed. A ghost of a cursor (ui/ghost.py: large, brown,
dripping her venom) glides to each choice, rests, and presses it; the scene window grows taller, the small things he
can do in a row under his lines. Paced for reading: every word new on the screen holds him (a second, and a third of
one a word) - place names, whispers, her murmurs, visions, her lines; a page newly written lifts his notebook to it;
F10 hurries the rest (x2, x4, x8, more again with nothing to do). The game's pause when the window's left skips the
letter's nights (they're for watching). Spellbound (Let the letter lead you): led from the first step to the last,
he's kept from giving out and she doesn't hunt him; any move key wakes him (the night his, no longer Spellbound); F9
hands any night to the letter or takes it back. Ending 8 of 8: Spellbound - she carries him home asleep; his notebook
full, in his hand but slower, as if guided. Its own coda, and a dream drifting over the den. (Her guests looked at now
count, too: three of them, and she calls him to supper from twenty past ten.)
game/tutorial.py - The first night (Learn the oak; offered the first time): eighteen lessons in the night's own order
- walking, the lantern, Light and the marks, taking, the satchel, the orbs, her small ones, her loom, her words, her
guests, the notebook, a strand, Warmth, saving, supper, her venom (one bite, safe), the phial, the crown - each a note
in his own hand, then his to do (watched for: he walks, shakes, casts, takes, opens...); the letter leads him between
them. Gentler: kept from giving out, not hunted; she calls him to supper once the lessons before it are done.

## Phase 8 - what the night does to him (done)

game/afflictions.py: each of the four at 75, 50 and 25 (health and sanity falling to them; poison and stupor rising),
each starting at its line and ending five past it. Health: panting, his heart's rest up 14, she hears him; a red tint
and blood from his eyes at the sides of his sight, beating with his heart; at 25, blood down the wand onto the lantern
(the light red), drops behind him, her hunger quickened by the smell. Poison: sick at once and every five to ten
minutes - a puddle (five at most), poison eased by six; a green tint, foam and drips at the bottom, a cough, his heart
skipping beats; at 75, oftener and green over the wand and lantern (the light green; E flings a third of it off; it
wears off in minutes). Sanity: his sight breathing, swimming, doubled a little (a post-process pass in
engine/render.py), false eyes in the fungus; at 50, down on his hands and knees for ten to fifteen minutes, up for five
to seven (slower, no jumping; on her silk the sway halved, and she reads him as wounded prey - hunger and
fascination); at 25, once a night, his left eye - the hand to it, the dark down that side of his sight, the hand away
red, and looking down, it in his palm, looking up at him (his own eye: into the satchel, room made; offered her, it
delights her fascinated, insults her otherwise). Stupor: a heat shimmer, sounds dulled; at 50, bouts of "No" (his head
shaking, nothing obeyed); at 75, falls (down, a while, dragging himself up) and moments lost (dark, the clock on six
minutes). Nothing that takes him from himself starts on a strand or in her scenes. Each writes a page in "What the
night does to me"; she remarks on the panting, the blood, the crawling, the sickness, the eye (once each a night).
Sounds: retching, coughing, a hummed "No," a stifled scream, scraping, his hearing dulled. Options: all of it, each of
the four, blood and vomit, the eye, the swaying sight, what takes him from himself - before the night and in his
notebook. Retuned: poison lingers (0.06 a second) and eats at health a little less. The letter keeps him above thirty
(never the worst); the first night is never the worst either, and has a lesson on it. The letter waits out what's
done to him, shakes the lantern clean, and steadies his mind with Light (her far off) or Memory.

## Phase 9 - polish, one at a time

9a - sound from where it is (done). The den's sound is stereo now (engine/sound.py: render -> (n, 2); the audio sink two
channels). Her rustle, her strike, the web creaking under her, her voice outside her scenes: from where she is
(heard_pan: left to right of him, a little less behind). Small ones bolting, a guest's silk tearing, thunder, the
crawlers across his face: each from its side; the lantern a little to his right. Wind and rain different in each ear.
And the space he's in: a reverb (four combs an ear) - long and dark in the hollow, close in the root tunnel, thinner in
the chambers and under the open crown.

9b - the lantern's shadows (done). engine/render.py: each frame the den is drawn once more from the lantern's flame
(SHADOW_VS/FS: how far each surface is from it, into a 1024 square), looking where he looks, 128 degrees wide - the
wood, the dressing, her guests, her small ones near him, and her. Every surface lit by the lantern asks it (shadowAt in
the shared lighting: nine samples, a soft edge, never quite black), and her chitin's shine too. The shadows swing as
the lantern swings. Options: "The lantern's shadows" (off, for a slower computer).

9c - her, between her scenes (done). game/sightings.py, every minute or two (oftener the more she's taken with him,
or hungry; never in her scenes, while she hunts, or in the first minute): across the wall above him, fast (when he's
near enough the wall for the lantern to catch her: Mother's "cross"); legs at the edge of the light, drawn back quick
(a glimpse cut short). And when he turns round fast (2.2 radians in 0.7 s), now and then - at most every two and a half
minutes - she's there, close, facing him (staged on the floor before him), his heart leaping; the lantern stutters, and
she isn't. While she moves near him her web thrums: the silk shivers, a low hum. Two pages: "Above me", "Behind me".

9d - before the dark (done). ui/pages.py Brightness: the first time Begin is pressed, a black screen with three small
spiders at the den's own darks (about 4, 9 and 20 of 255, as made) and a slider: until the middle is barely there.
The setting (0..100, 50 as made) is the den's exposure before its gamma (engine/render.py exposure: every 25 steps
twice or half the light). Also in Options and the notebook's Options.

9e - her body when she talks (done). Before him (her scenes, her endings) her fangs open and close with her voice
(engine/sound.py speech_level - or, unvoiced, while her words are coming), and her palps never quite still
(engine/render.py _mouth: built under her eyes on the spider's own axes, twice life size to be seen). Her head
breathes and turns a little, and tilts as she weighs what he's just said (Mother.judge), coming back. The scene's
camera looks a little lower, so her mouth is in the frame.

9f - silence, when she's close (done). Within four and a half of him, outside her scenes (and when she's there behind
him), the music falls away, and most of the wind - fast going, slow coming back - and what's left is his breathing and
his heart, loud (engine/sound.py duck; ui/audio.py).

9g - Supper, from her side (done). After the dark comes down on him, three lines in her hand on the black, a line at
a time (and in her voice), before the card: what she did with him and what she thinks of it, by what she made of him
- held dear (hung highest, by the moon; not eaten for a long time), lied to (kept low by the roots), met before, his
careful steps, or plain (game/death.py her_side).

9h - the walk to the oak (done). A new night begins out in a glade at dusk, twenty-one strides from the roots, her
letter in his left hand (game/tree.py outside: the glade beyond the tunnel's far end, now open - its floor, its
trees to walk round; game/night.py begin_outside). engine/treemesh.py _outside: the leaf-litter floor; the mound of
roots arched over the tunnel, and its mouth; the oak's own trunk going up into the sky (its broken top capped to the
crown's rim), a gap at its foot where the roots run in; a dozen trees in the glade and a wall of them round it. Out
there the dusk sky lights everything (the shared lighting's outsideK) and the mist between the trees is thicker; the
sky itself deepens to dusk while he's under it. Into the roots, he folds the letter away. Nothing small drops on him
under the sky. The letter leads from out there, too (Nav: outside -> the mouth -> the tunnel).

9i - how hard the night is (done). Four levels (game/condition.py LEVELS; Options, before the night and in his
notebook; saved with the night): Easy - as it was made; Normal (the new default) - hurts 2.2x, bites 2.6x, the mind's
losses 2x and its mending 0.6x, poison wearing off at 0.45x and eating at health 2x, health mending 0.5x, stupor in 2x
and out 0.5x, her hunger 1.25x; Hard and Nightmare further still (Nightmare: hurts 5x, bites 6x, the mind 4.5x,
poison wearing off at a fifth). Her own bite a little more. Led by the letter, still kept above thirty.
And in her scenes his orbs and his heart are no longer hidden: they sit just above her words.

