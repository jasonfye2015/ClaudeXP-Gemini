# Upgrade plan 60: figures - the monsters, the townsfolk and the pets as rigged, animated bodies

Asked for 2026-11-05: "a comprehensive plan to replace and upgrade enemies and NPCs - perhaps full mesh bodies -
and explore open-source materials to source them". This is the plan; nothing in it is built yet.

## 1. Where things stand

- **What is drawn.** 52 monster kinds, 10 guardians and the Lich King (10-data.js), each painted at load by
  30-art.js from seven body shapes (beast 13, wide 13, small 7, tall 7, ghost 5, thin 4, biped 3) in the kind's
  colour, with idle2/attack poses. 11 townsfolk pictures (`npc:*`), two pets (`pet:dog`, `pet:pony`), the walkers
  and the traders. All are billboards: a quad facing the eye, with the later layers on top - strips that bend
  (v29.0), front/side/back frames (v50.0), feet and contact shadows (v50.1), wear frames (v50.2), tall guardians
  (v50.3), idle life (v50.4), hit reactions (v39.1), deaths by kind (v29.2), statuses and elite auras (v39.3-4).
- **The renderer.** Our own WebGL2 (40-render.js): one static mesh for the floor (pos, uv+layer, shade, fx) and
  one instanced billboard buffer. No skinning, no normals (lighting takes the facing from screen derivatives). The
  fragment shader does everything else - sun colour, lamps, fog, wet, snow, moss, the grade - and would light a
  real mesh the same way.
- **How art ships.** One HTML file (8.3 MB today). pack.py bakes src/art/ into 35-packs.js as base64; src/art is
  77 MB of sources. The game already carries third-party CC0 art with credit (Dungeon Crawl Stone Soup tiles,
  ambientCG textures: src/art/CREDITS.txt), so CC0 models with the same credit line keep to the house rule of
  original content - nothing is copied from a particular game, and the licence allows it outright.
- **Budget.** The Timeline's software-drawn test loads the file in ~40 s; every megabyte added to the HTML costs
  load time everywhere. A whole-roster mesh set must stay small: the target below is +3.5 MB, quantised.

## 2. Sources (all checked 2026-11-05; verify the licence file inside each download and keep a copy in src/models)

| Source | What | Licence | Formats | Notes |
|---|---|---|---|---|
| **KayKit - Character Animations** (Kay Lousberg, itch.io) | 161 humanoid clips on two rigs, Rig_Medium and Rig_Large: idle, hit, death, spawn, walk/run/sneak/dodge, one-hand/two-hand/unarmed/dual/block, bow, spellcasting, sit/wave/cheer, tool work; a Special set for skeletons | CC0 | FBX, glTF | 14 MB free. Fits every KayKit humanoid. |
| **KayKit - Adventurers** | 5 free rigged fantasy characters (8 with the Extra tier), 25+ weapons and accessories as separate meshes | CC0 | FBX, glTF | 12-18 MB. The townsfolk, traders, followers, bandits, the rival band. |
| **KayKit - Skeletons** (and the legacy Skeleton pack) | rigged skeleton warriors/mages/archers, same rig family | CC0 | FBX, glTF | Skeletons, revenants, bone kinds; the Special animations. |
| **KayKit - Dungeon Remastered / Halloween Bits** | props, a few creatures (ghosts, pumpkins, spiders) | CC0 | FBX, glTF | Ghost kinds, decor if wanted. |
| **Quaternius - Ultimate Monsters** | 50 animated monsters (attack, death, walk, run and more) | CC0 on the pack page ("free in personal and commercial projects") | glTF, FBX, OBJ, Blend | The beasts, the wide and tall kinds. A third-party guide says Quaternius now publishes a "Quaternius Asset Licence" for new packs - read the licence file in the download before relying on CC0. |
| **Quaternius - Universal Animation Library** | locomotion, death, sit, swim, crawl clips | CC0 | glTF, FBX, OBJ | Spare clips for Quaternius rigs. |
| **Kenney - Animated Characters 1-3, Mini Characters** | small rigged humans (Mini Characters: 12 characters; OpenGameArt lists 32 clips each, another guide says unanimated - check) | CC0 | FBX, glTF | Crowd variety if KayKit runs short. |
| Sketchfab (CC0 filter), Poly Pizza, OpenGameArt | single models to fill gaps (a dark elf, a mimic, a wyrm) | per model - take CC0 only | glTF | One at a time, with its licence saved. |
| Mixamo (Adobe) | thousands of clips, auto-rigging | games allowed, **raw files may not be redistributed** | FBX | Not for this repo (the Timeline is on GitHub). Mesh2Motion (CC0 clips from Quaternius) is the open stand-in. |

Rule: CC0 only, one `src/models/CREDITS.txt` line per pack as with the tiles and textures, licence files kept
beside the sources, nothing from Mixamo or CC-BY-SA packs.

## 3. Three routes, and the recommendation

- **A. Better pictures only.** Swap the painted billboards for CC0 sprite sheets. Cheapest, but the good 2D sets
  (LPC, DCSS) are CC-BY-SA or already used, and it changes nothing about how figures move. Not recommended.
- **B. Impostors from meshes.** Load the CC0 models in a build step, render each kind's idle/walk/attack/hit/die
  frames from 8 directions into sprite sheets, and feed those into the existing billboard pipeline (which already
  has frames, sides, bending and wear). A third of the engine work of C, visible in two or three releases, and
  every later system keeps working untouched. Costs texture memory (8 dirs x ~6 clips x ~6 frames per kind).
- **C. Full rigged meshes in the renderer.** Skinned meshes drawn in place of the billboards, animated at run
  time, lit by the same shader, turned to face where they look. The real upgrade: smooth motion, true sides,
  gear on the hands, scale and tint per kind. More engine work (phases 1-2 below).

**Recommendation: C, built through B.** Phase 0's pipeline and Phase 1's loader are needed either way; B's
sprite sheets come out of Phase 0 for free and become C's distance LOD and the bestiary's plates, so the painted
fallback is never needed again. Order the work so the town's people land first (few kinds, the most seen).

## 4. Phases (each a release or two; versions follow the order done)

### Phase 0 - the pipeline (no change to the game yet)
Done 2026-11-05 as v65.0 (the first release of it): tools/models.py, src/models/figures.json and CREDITS.txt,
src/js/35c-figures.js (generated), 37-figures.js (the reader and the pose), 76zzzzzzzzzzd-figures.js (the loader).
Twenty-five models - the five adventurers, four skeletons, ten pieces of gear, wolf, husky, horse, deer, rat and
spider - bake to 1.59 MB of base64 (3.48 MB raw; 81 clips shared). The Ultimate Monsters pack (Google Drive/itch
download, no direct file) is not fetched yet; the beasts came from the Animal and Easy Enemy packs via the
showcase mirror. Sizes in model units: the KayKit bodies stand 2.4-2.6 tall, the animals 2-5; the renderer will
scale each figure to its target height. Decided: the impostors will be rendered at load on the GPU by the
renderer itself (idle from eight sides, into a texture) rather than baked to sheet files, so they cost no file size
and always match the models - they move to Phase 1/5, and Phase 0 is complete with this release.
- `src/models/<pack>/` with the glTF sources and licence files; `tools/models.py` converts each chosen model
  to a compact binary: positions as int16 over the bounds, normals oct-encoded, uv as uint16, joints (uint8 x4)
  and weights (uint8 x4), an index buffer; clips sampled at 20 fps as per-joint quaternion + translation tracks in
  float16, keyed by name (idle, walk, attack, hit, die, cast, spawn); textures to 256 px atlases (most of these
  packs use one tiny palette texture - cheaper still).
- A model is picked by a mapping file `src/models/figures.json`: monster kind -> pack, model, scale, tint
  (the kind's colour, by how much), gear attachments (which weapon mesh on which bone), clip aliases.
- Budget test: the baked set <= 3.5 MB base64 in the HTML, <= 60 KB a figure including clips; the loader parses
  every entry; every kind and NPC has a mapping or is marked "painted".
- The impostor step: render each model's clips from 8 directions to sprite sheets (Node + headless WebGL or the
  browser harness), written to src/art like the other sheets. This is route B, and C's LOD.

### Phase 1 - the renderer (40-render.js)
Done 2026-11-05 as v66.0: the skinning path (aJoints/aWeights in slots 8 and 9; uJoints an RGBA32F texture, four
texels a joint; uModel; uFigFx), the figures' texture array (uFig, layers 3000 and up: a model's PNG or a palette
of its colours at 256), uTint, and drawFigures between the floor's meshes and the sprites. 37-figures.js measures
each model posed at rest (Quaternius' raw boxes are tiny before the armature's scale) and fits it to its billboard
by height or width, whichever binds (a rat is long); the body is centred on its square with its feet at the floor.
76zzzzzzzzzze-figures2.js takes the mapped sprites out of the list within fourteen squares and draws them in their
idle, facing the party; Settings > Figures: Modelled / Painted. Seen in the Square, the yards (hound, pony) and a
fight (a rat ahead, torch-lit). Impostors for the far ones still to come (Phase 5).
- A skinned program: attributes pos/normal/uv/joints/weights; per-instance model matrix (yaw, scale, position),
  tint, flash, alpha, glow; joint matrices through a float texture so a rig can have more than 64 bones; the same
  fragment lighting as the floor but with the vertex normal (sun colour, lamps and their wall shadows, fog, mist,
  snow on upward faces off, moss off).
- Drawn between the floor and the billboards with the depth buffer, so a figure stands in a doorway properly.
- Reach: meshes within 14 squares; beyond, the impostor billboard from Phase 0; at Low detail, impostors only.
- A Settings line: Figures - Painted / Modelled (Modelled the default where WebGL allows it).

### Phase 2 - animation and the systems that already move things
Done 2026-11-05 as v67.0: CM.Figures.step is the clip player (idle and walk looping at the kind's speed; attack or
cast, hit and die once, die holding its last frame; 0.15 s blends between poses). A figure's state is kept by its id
(the fight's foe object, the floor's thing key, a walker's number, the lamplighter, the kennel's pets); its cues
come from what already happens - position change for walking (not for a fight's foe, which sways and recoils in
place), the layer's :attack pose for the lunge, the picture's flash rising for the hit, hp <= 0 for the death - and
the fight's foes square up to the party while the rest face where they went. A worn-down foe is darker. Casters
(wizards, priests, the Bone Patriarch, the Lich King) cast instead of striking. Not yet: the blow's effect timed to
the clip's hit frame, the death held on the floor past the fight's end (the sprite goes when the foe does), and the
acting foe's half-step forward - these fold into Phase 4's batches as the kinds come.
- A clip player with blending (idle <-> walk <-> attack/hit/die/cast), speed from the kind's `speed`, a phase
  offset per figure so a pack is never in lockstep, and events (the blow's effect fires at the attack clip's hit
  time, ~0.3 s in, instead of at once).
- Map the old systems onto it: idle life -> idle clip + breath; facing (v29.1) -> the model's yaw; three sides ->
  real; hit reactions -> hit clip + the flinch; deaths by kind -> die clip, then the existing crumble/ash/bone
  effects; wear -> darker tint and the second idle; feet and contact shadows -> unchanged; statuses, auras and
  floating numbers -> anchored at the model's bounds (head height per kind); tall guardians -> scale 1.6-2.2.
- The fight screen's turn: the acting monster steps half a square forward while its attack plays (the turn-order
  strip already names it).

### Phase 3 - the town's people and the pets first
Done 2026-11-05 as v68.0: all six residents have bodies (the merchant, the priest and the tavern-keeper had no
picture and were never drawn on their rounds before; the townsfolk file now draws a resident with a body but no
picture), and stand at their work (cues.act: the work loop) at the forge, the stalls, the Library and the Temple;
the traders at their stalls likewise. Gear in hand: each gear:* model is a mesh bound to the shared rig's hand and
drawn with the body's own joint texture - the smith's axe, the tavern-keeper's mug, the books, the hermit's staff,
the lamplighter's pole (the mage's staff stands in; a lantern pole would need a model of its own), the knight's sword
and shield. The crowds, the followers behind the party and the kennel's pets were already bodies from phases 1-2.
Not done: sitting at the tavern's benches (the residents stand at its door; no bench positions exist), Legends' Row
and the rival band (no figures of their own on the floor), the farm's litter (a window, not the floor).
- KayKit Adventurers for the six residents, the traders, the crowds, the lamplighter (with the pole as gear),
  porters, torchbearers, followers seen behind the party, the rival band, Legends' Row; Quaternius animals for
  the hound and the pony (the kennel, the farm, the followers).
- Idle and walk clips on the routines and crowds (they walk now with a bob); sit at the tavern's benches, work at
  the forge and the stalls with the tool clips.
- The heroes stay first-person (portraits and the hand); nothing changes there.

### Phase 4 - the monsters, in batches by body shape
Done 2026-11-05 as v69.0, in one batch rather than four, since the packs in hand set the limit: 54 kinds have
bodies (the KayKit adventurers and skeletons tinted and scaled for the small folk, the big, the dead, the drowned,
the golems and the guardians; Quaternius' bull, fox, stag, snake and frog fetched for boar, bear, wyvern, eel, root
wyrm and the marsh's frogs), and nine stay painted - the plants, the fungus, the mimic, the Mycelial Mind and the
Root of the World - because no body fits them. A foe's weapon names the gear in its hand (CM.Figures.gearFor); a
striker steps in and back with its blow. The bake is 2.0 MB. When the Ultimate Monsters pack is fetched (it is
Drive/itch-only), the big kinds and the painted nine can be given their own shapes in a second batch.
- beast (13): rat, wolf, spider, bear, boar... from Ultimate Monsters' quadrupeds; small (7): goblin, kobold,
  imp - KayKit skeletons at 0.8 scale and Quaternius smalls; thin (4) and biped (3): skeleton, zombie, ghoul -
  KayKit skeletons/zombies with the Special clips; wide (13): orc, troll, ogre - Quaternius brutes; tall (7):
  dark elf, knight, wraith - Adventurers in dark tints with the two-hand clips; ghost (5): Halloween Bits ghosts
  with alpha and glow, drifting. Each kind: tint by its colour, scale by its shape, its gear.weapon on the hand.
- Guardians and the Lich King last: bespoke picks on Rig_Large, scaled, with the aura ring at the feet and the
  entrance stage (v23.2) playing the spawn clip.
- Any kind without a good match stays on its impostor (never the hand painting) and is listed in figures.json as
  such, so the test knows.

### Phase 5 - polish and holding it
- LOD and budget: a frame-time test of 30 figures skinning under 2 ms on the harness; impostors beyond 14
  squares; a per-floor cap.
- The bestiary's plates and the fight list's portraits drawn from the models' impostor sheets, so every picture of
  a kind agrees.
- Tests: the loader parses every baked model; every kind maps; every clip alias resolves; sizes within budget;
  the three-sides/feet/wear tests re-pointed at the new frames. A screenshot pass of every place with figures.
- Credits in the game's About and src/models/CREDITS.txt.

## 5. Risks and how they are met
- **Size.** Quantised buffers and 20 fps clips; shared textures; the impostor fallback means a kind can be left
  out without a hole. Measure in Phase 0 before anything else is built.
- **Licence drift.** Quaternius may have moved newer packs to its own licence; CC0 is checked per download and the
  file kept. Mixamo is out.
- **Style.** Flat-shaded low-poly figures against the Stone look's photographed walls: the same lighting helps
  most; a cel-shade option (two-band light) and tints from the kind's colour pull them together; the painted set
  stays available under Figures - Painted until the user is happy.
- **Rigs don't match across packs.** Each pack's clips stay with its own rig; the clip aliases hide the names.
- **The replay films and tests.** Figures are the window's side only; nothing here touches the rules, so
  determinism is unaffected.

## 6. Order and size
Phase 0 (two releases: pipeline, impostors), Phase 1 (two), Phase 2 (two), Phase 3 (two), Phase 4 (three or four,
a batch each), Phase 5 (two): about fourteen releases, v65.0 onward. Phase 0's first release answers the
one open question - whether fifty-odd figures fit the file - before the renderer work begins.
