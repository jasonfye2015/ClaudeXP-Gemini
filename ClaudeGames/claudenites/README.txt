Claudenites 3-D
===============

A first-person roguelike in the Deep under Thornwick: the story of Claude before Claude and Magic, when he was an
apprentice with a birch wand. A hundred floors, ten bands of ten, a guardian at every tenth, and at the bottom the
thing the town is built over.

Playing
  WASD move, Shift run (a running jump goes higher and further), mouse look (click to take the mouse, Esc gives it back), left button cast, Space jump,
  F talk / use (the vendors, the stairs, the Deep's mouth, the cabin, the bed, the hearth, the chest, the farm sign), Q health potion, E mana potion, T Scroll of Return,
  1-4 or the wheel: change wand, Tab the pack, M the big map, K the Calendar, P auto-play on/off, Esc the menu.

  Thornwick is home: four vendors round the square - Hesper the Apothecary (potions, Scrolls of Return), Old Tamsin
  the Wandwright (wands and wand parts), Bramwell the Outfitter (hats, robes, gloves, boots, rings, amulets) and
  Mother Wren the Sage (the three skill trees) - and the Deep's mouth in the middle. At the stairs on every floor,
  go deeper or go home; the way down waits at the floor reached. A Scroll of Return brings him home from anywhere.

  The forest: Thornwick's clearing sits in a great wood, and trails wind out from its four ways to the glades - the
  Mossy Pond, the Old Shrine, the Woodcutter's Camp (Rook, who talks), the Fairy Ring, the Hollow Oak, the Wolf
  Hollow, the Bandits' Camp and the Stream. Its creatures (deer that run, boar, wolves, bears, bandits) are as strong
  as Claude is, come back each time he comes home, and never come into the town. Falling in the forest costs nothing
  but pride: he wakes in the clearing and the Deep is as he left it.

  If Claude falls in the Deep he wakes in Thornwick with everything: his gold, his pack, his gear, his levels and his skills.
  Only the run is lost - the Deep starts again at floor 1, and its floors are new.

  Wands: a body (its shots a second, bolt speed, base damage, mana a shot and how many slots) and the parts set in
  its slots: a Core (Fire, Frost, Storm or Venom - the bolt's element), a Lens (damage), a Splitting Prism (more
  bolts, wider), a Focusing Ring (tighter, faster), a Quickening Rune (faster casting), a Seeker's Eye (homing),
  a Rebounding Band (bounces) and a Piercing Thorn (passes through). Fire burns, Frost slows, Storm leaps to the
  next foe, Venom stacks; Arcane hits harder. Four wands ready at once.

  Barrels, crates, weapon racks, shelves, tables, benches, egg sacs, cocoons and fungus break under his bolts -
  splinters everywhere, and now and then a little gold or a potion inside.

  The music is ClaudeRPG's: its own engine (engine/music.py, carried over from its SND), every note made as it plays
  - a drone, a bass, a lead from the place's scale, bells, an echo - in its worlds' styles: the town and the title in
  its own, the forest in its Crystal Grotto's, and each band of the Deep in one of its worlds' (the Undercroft, the
  Sunken Halls, the Frozen Caverns, the Clockwork City's waltz, the Burning Heart's drums), turning to its battle
  music when a guardian wakes. Options on the title: music on/off and volume, sound, the townsfolk's voices, the mouse.

  The sky is Claude and Magic's (game/sky.py, engine/atmosphere.py, engine/weatherfx.py, ui/dial.py): a day of
  twenty-four hours (a minute of it a second of play; the stairs take an hour), the real season with its daylight,
  a twenty-nine day moon, and the weather as live events - clear, cloud, rain, storm, mist, wind, snow, heat, an
  aurora, a tornado - two to six hours each, coming in and going out. Over Thornwick and the wood: the sky of the
  hour, the sun and the moon in its phase, clouds, stars, the aurora, a rainbow in a sun-shower, lightning; rain,
  snow and leaves falling; snow lying and frost on the ground; mist closing in; a twister crossing the wood. In
  play: rain dulls fire and feeds storm, snow feeds frost and slows him, heat feeds fire, mist hides him, a storm's
  lightning strikes in the wood, the wood is fiercer at night, and a tornado flings everything. Below, on the first
  floors: rain drips from the ceilings, a storm pours through the grates and floods the sunken rooms of floors 1-3
  (draining over a day), its lightning flickers down and its thunder rolls. The dial under the map shows the hour,
  the day, the season, the weather (above, in the Deep) and the moon; K opens the Calendar.

  The ground blends as Claude and Magic's does (engine/groundmap.py and the level shader): grass, earth, cobbles,
  flags, needles, moss and litter don't meet in straight lines - each square's neighbour fades into it along a
  ragged edge - and big soft patches, lighter and darker, greener and yellower, hide the tiling. The ways people walk
  between the stalls, the Deep's mouth and the cabin are worn to earth in patches; under close trees the grass gives
  way to moss and leaf litter; the pond and the stream have dark wet banks; the sun comes through the leaves in
  dappled patches that drift in the breeze; in autumn the leaves drift against the walls; after rain the earth is
  muddy. (Options: Ground blending, on/off.)

  The title: a title card - the name over Thornwick at dusk, the camera circling the Deep's mouth - and then one page
  with Play (the three slots as cards), Records, Options, Keys and Credits.

  What the dead drop is seen: each thing - its gold, a potion, a scroll, a robe, a wand, a wand part - pops out of the
  body as its own picture, bounces, glints (gold for the rare), and flies to Claude as it goes into the pack. Chests
  and broken barrels too.

  The dead flip over: a thing that stood falls flat on its back, a beast or a blob rolls belly-up.

  The floors are big - sixteen to thirty-six rooms - and climb: each room at its own height, a step or two from the
  ones it joins, the corridors rising and falling between them in gentle steps; L-shaped rooms, rooms round a block
  of rock, split and stepped rooms, winding corridors, loops, and dead-end alcoves with a chest or a find at the end.
  Gold, potions, scrolls and things that glint lie about, taken as he walks over them; more chests, more barrels.

  The Deep is dressed as Claude and Magic's is: pipe mouths that drip, barred grates and drain ports, webs in the
  corners, moss, roots, chains, sconces and banners, beams and hanging roots overhead, stalagmites, and each band's
  own things - glowcaps, crystals, braziers, sarcophagi, candles. Most floors hold one of Claude and Magic's sixty
  set pieces (the Bone Room, the Chapel of Candles, the Cold Store, the Wolf Den, the Fallen Star...), which says its
  line when he steps in. Chests open with F (some are guarded) and stand in the round - Kenney's chest, its lid swinging back on its hinge. A
  bolt breaks them too: shot before it's opened, a chest gives its things all the same (its guards wake), and an
  emptied one shot only breaks. Water slows him.

  Home: Claude's cabin stands west of the square, between the Wandwright and the Outfitter (F at its door). Inside:
  the bed (sleep until six in the morning - the night passes, the crops grow, and he wakes with full life and mana),
  the hearth with its cauldron (cooking), and his chest (whatever is put in it stays there, whatever the Deep does).
  North of the cabin is the farm: eight plots of tilled earth to start, twenty in the end. The sign at its foot runs
  it - choose a seed and a plot (or Plant all), Water all, Harvest all, and the automation: a Sprinkler (waters
  every plot each morning), a Farmhand (harvests what's ripe into a basket, and plants again from the seeds in the
  cabin's chest), and More plots. A crop grows only on a day it's been watered (by him, the sprinkler or the rain),
  through four stages in one and a half to five days: radish, carrot, onion, potato, cabbage, tomato, strawberry,
  pepper, corn, eggplant, cauliflower, squash, pumpkin and watermelon. A harvest sometimes gives seed back.
  Seeds drop from monsters (more in the forest) and lie in chests; Hesper sells some each visit.

  Food: beasts leave meat, water-things fish, the fungal ones mushrooms, the wasps honey. Anything raw can be eaten
  as it is (a little life and mana). At the hearth, a known recipe cooks with one button; or put up to three raw
  things in the pot - if they make a dish, it's cooked and goes into the cookbook (if not, nothing's lost). Twenty-four
  dishes, from Roast Haunch to Dragonfire Chili and the Feast of the Deep; each one eaten is a buff for one to five
  real hours - spell damage, crits, move or casting speed, life, mana, armour, mana a second, gold found, life
  leech, an element's damage - three at most at once (the oldest goes), shown under the place's name with the time
  left. The cookbook (from the hearth or the pack's Cooked tab) shows what's been found and how many are left.

  The pack has tabs: Armor (the gear not worn), Wands (wands and wand parts), Seeds, Raw, Cooked and Misc (potions
  and the scroll); food stacks with its count, and Eat it / Drink it act on it there.

  The Deep's detail (game/detail.py): the corridors are dark - a fifth of a room's light, and Claude's own glow
  dimmer in them - with a torch now and then on a long one; the torches burn bright and reach far. Timber holds the
  place up: frames of posts and a lintel down the corridors, skirting boards and ceiling beams in the rooms (most in
  the Cellars and the Foundry). The floors are stained in blotches, the walls streaked with old water and grimed at
  their feet; puddles lie under the drips and in the low places and catch the torchlight. Bones, empty potion
  bottles, vines down the walls and hanging from the roof - and here and there a grate in a ceiling with the light
  of the day above falling through it (the moon's at night, less under cloud), dust turning in the beam.

  Strange floors (game/features.py): about one floor in five, never the first nor a guardian's, is more than it
  seems, and says so on its card -
    the Dreaming   the lights red, green and blue and turning, the colours washing over the eyes, the view
                   breathing; half the creatures real, and ghosts drifting among them - they can't be hurt, and
                   they don't hurt, but try telling your nerves that
    a Hoard        gold heaped in every room and spilled across the floors, the torches burning gold, more chests,
                   and some of them guarded
    a Den          one kind of creature, and lots of it, with its nests
    Drowned        the rooms flooded to the knee (it slows him), pipes in the walls pouring water into them
  Locked doors: on about half the floors, a dead-end room is shut by a red, blue, green or gold door; its key lies
  somewhere on the floor that can be reached without it (it glows in its colour). F at the door with the key opens
  it on the vault: rich chests, gold and finds. The keys held show under the place's name.
  Puzzles: a door sealed with runes and no key - find and pull every lever on the floor (two or three, glowing red
  until pulled) and it grinds open; and a room of cold braziers - shoot one to light it and the trial begins: light
  them all within twelve seconds (the time shows) and a chest rises from the floor, or they all go out to try again.

  Auto-play (the button over the life orb, or P): Claude plays himself (game/autoplay.py). On a floor he fights
  whatever he sees (backing off from biters, potions when he needs them), takes everything lying about, opens every
  chest, unlocks the doors he has keys for, pulls the levers, runs the brazier trial, breaks the cracked walls he's
  found, hunts down every monster left and walks every square - then takes the stairs home (eight minutes on a
  floor, and he heads for the stairs whatever's left). In Thornwick he sees to his things: buys from Old Tamsin and
  Bramwell whatever beats what he has, builds the best two wands he can from every body and part, wears the best
  gear, spends his skill points, harvests and waters and plants the farm, cooks, eats the best meals, sells
  everything left over (never the chest at home) and stocks up on potions and scrolls - then goes down again to
  where the run has got to. If he falls, he gets up and starts again. Past the hundredth floor it goes on: endless.
  Endless: once the Unmade King falls, the Deep goes on past the hundredth floor - the bands come round again, their
  guardians with them, everything harder each time.

  The Gauntlet: once a guardian has fallen, a strange floor may be a boss rush - the guardians of the bands already
  passed (up to four, the newest last), waiting in the stairs' hall. Step in and they come one at a time, each
  announced; the stairs stay sealed until the last falls, and then a chest of the old champions' hoard, with a
  Legendary in it, stands in the hall.
  Traps, from the second floor (two to eight a floor, more the deeper): spike plates (an iron plate pierced with
  holes - step on it and the spikes spring), dart plates (a rune-cut flagstone; a hole in the wall beside it spits a
  poisoned dart), and fire vents (a grate over a red throat that breathes flame on a beat - embers warn of the next
  burst, and monsters burn in it too). None in the first room, by the stairs, by a door or in water.
  Cracked walls: now and then a wall has a crack in it. Shoot it.
  And there are secrets - some down in the Deep, some not. Nobody's going to tell you where.

  Rarity: everything found - gear, wands and wand parts - is Common, Uncommon (green), Rare (blue), Epic (purple)
  or Legendary (orange), likelier the deeper and with luck. A wand's rarity adds damage (to +65%) and casting speed
  (to +18%), and an Epic or Legendary wand has a slot more; a part's rarity strengthens its effects (to x1.75) and
  a Legendary one adds another bolt, bounce or pierce; gear gets an affix more each step, an Epic its main stat half
  again, a Legendary its main stat doubled and the rest a fifth more. The colours show everywhere: the pack's tiles
  (Rare and up breathe, Epic and up shine, Legendary turns its rays), the names, the wand slots, what drops - Rare
  and up stand in a pillar of their light, a Legendary in a ring - and a find Rare or better is announced (a
  Legendary with a banner). Guardians drop Rare or better. Older saves' things keep their rarity (their Legendary
  stays Legendary).

  The townsfolk speak: with a language model in the Timeline's Local Storage\LLM Models (llama.cpp, through the
  Timeline's own engine - Qwen3 4B Instruct when it's there), Hesper, Old Tamsin, Bramwell and Mother Wren greet
  Claude in their own voices, knowing how deep he's been, how often he's fallen and what he's killed, and answer
  whatever he says to them at their stalls. Without one they have their own lines. (Menu: the townsfolk speak, on/off.)

  The pack: choose a wand, then a wand slot (1-4), to ready it there (or its Ready-in-slot buttons); a ready wand,
  then another slot, to swap them; a part, then a socket; gear, then its slot. Where a chosen thing can go lights up.

  The look (ui/theme.py): dark leather and old gold - painted panels with a double gold rim and filigree corners,
  fading in over a darkening vignette; bronze buttons; glass orbs with moving liquid; a gold-rimmed plate for the
  wands and potions; a shimmering experience bar; ribbons for the news; a title card for each floor and a banner
  for each level.

  Three save slots. Saves live in the Timeline's ClaudeGames/Saves/claudenites/ (slot1.json .. slot3.json).

How it's made
  Python, PySide6 (the window, the menus) and OpenGL 3.3 through PyOpenGL (the view), with numpy.
    game/     the rules, with no Qt and no GL: levels (the floors and the town), world (the running game), player,
              items (wands, parts, gear, loot), skills, shop, saves, data (the tables)
    engine/   gl (programs, meshes, textures), render (the frame), levelmesh, figures (Claude and Magic's figures and
              plants, read with numpy and skinned on the card), sound (made at start), speech (the townsfolk's voices, through
              claudecore.ai.llm_server)
    ui/       shell (the window's content), view (the loop, the input, the HUD), panels, icons, skills_panel
    assets/   imported from Claude and Magic by tools/import_cm.py (figures, plants, stone) and tools/export_cm_art.py
              (assets/cm: its painted art and its set pieces, exported from the running game; see CREDITS.txt)
    tests/    python tests/run.py - the rules, played headless (no Qt needed)

  python tools/play.py        play this copy on its own (with the Timeline's Python)
  python tools/import_cm.py      bring Claude and Magic's figures, plants and stone across again
  python tools/export_cm_art.py  export its painted art and set pieces again (runs it in Qt WebEngine)
  python tools/bake_chest.py     the 3D chest again (Kenney's Pirate Kit, CC0)
  python tools/import_icons.py   the item pictures again (Dungeon Crawl's tiles and 7Soul1's icons, both CC0)

In the Timeline it's ClaudeGames/claudenites (a subtree of this repo): in the launcher's Apps, and in each
computer's Games.

The plan: PLAN.md.
