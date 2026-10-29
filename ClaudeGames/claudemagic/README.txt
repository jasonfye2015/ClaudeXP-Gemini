Claude and Magic - twenty floors down, the Lich King waits
==========================================================

A first-person dungeon crawler ("blobber", after Wizardry, Might and Magic and Eye of the Beholder): a party of four
moves as one through twenty floors of stone, a square and a quarter-turn at a time, smoothly, in 3D. Chests and
fallen monsters give gear and gold; a merchant's camp waits below floors 5, 10 and 15; the Lich King is on floor 20.
When the whole party falls the run is over - the deepest runs go in the Hall of Fame.

The dungeon (phase 2 of the big update)
  Each floor is rooms joined by corridors, with a set-piece room or two dropped in (a treasure vault behind a locked
  door, a shrine, a fountain hall, a den, a library, a crypt in magical dark, a pit room, a keep behind a portcullis).
  Doors open when walked into; a locked one wants a key found somewhere before it. Secret doors hide on the
  shortcuts - search a wall (Space) and a hairline in the stone gives one away. Pits and hidden trapdoors drop the
  party a floor, bruised. Teleporters move them, spinners turn them. A fountain heals, restores magic or poisons,
  once; an altar heals a little, once. A lever raises its gate. A carving on each floor tells the Lich King's story.
  Stairs lead back up, and floors are kept as you left them. Torches burn down (400 steps; fresh ones light
  themselves from the pack; the merchant sells torches and a lantern that never runs out); in the dark the automap
  stops filling, and in a magical dark even a torch sees only a step. Monsters that see you come for you.
  CM.solvable (20-world.js) proves every generated floor can be finished, and the generator checks each piece of
  furniture against it as it goes.

The party (phase 3)
  New Expedition opens the creation screen: four heroes, each named (or given a name by the dice), with one of
  eight callings - Knight, Paladin, Rogue, Ranger, Cleric, Mage, Druid, Bard - six stats rolled on three dice plus
  what the calling brings (Strength, Dexterity, Constitution, Intelligence, Wisdom, Luck; each calling has the stat
  that matters most to it), and a row. Advice on the right says what the party lacks (no one up front, no healer,
  nothing that hits every foe, a low stat worth a reroll); Suggest a party fills in the classic four.
  Rows: the front row takes most of the blows (the Knight most of all); the back row is reached only when it must
  be, and hits for half - except the Rogue (a knife from behind: double) and the Ranger (arrows). Cast is each
  calling's own: Fireball, Heal, Lay on Hands, Volley (two arrows), Thorns (every foe hurt, some held), Song (the
  party hits harder for the fight).
  Ailments: poison (bites each round and every few steps), paralysis, sleep (a blow wakes), blindness, a curse
  (weaker until lifted), stone (out of it until restored). Monsters leave them with a touch (rats and wyverns
  poison, ghouls paralyse, wraiths curse, gargoyles turn to stone...); Luck and Wisdom shrug them off. Cures: an
  antidote, a rest at the camp, the camp's temple (cure, lift a curse, stone to flesh, raise the fallen), a fountain,
  an altar (curses).
  A level earned is a boon chosen: three offered (the calling's own stat always among them) - +2 to a stat, Iron
  Skin, Second Wind, Keen Eye, Thick Blood, Scavenger, War Cry. Press 1-4 (or click a card) for a hero's sheet: stats,
  rows, ailments, boons, and the choice when one is due.

The fight (phase 4)
  Turn by turn, in order of speed (Dexterity and the dice; monsters have a speed of their own): when a hero's turn
  comes the bar under the view is theirs - Fight (F) the chosen foe (Tab, a number, or a click on a foe chooses),
  Cast / Skill (C) from their book, Item (P), Defend (D: half the blows until their next turn), Run (R: more than
  half the time, a Rogue helps, never from the Lich King; the party steps back a square). Surprise goes both ways:
  monsters that come at you out of the dark may strike first; a party with a Rogue or Ranger often gets a free
  round. In a corridor only two foes can reach you at once.
  Books and skills come with the levels (CM.ABILITIES in 10-data.js): the Mage's Magic Missile, Fire Bolt, Light,
  Sleep, Frost, Fireball, Blink, Lightning; the Cleric's Heal, Cure, Bless, Turn Undead, Protection, Lift,
  Sanctuary, Raise Dead; the Paladin's Lay on Hands, Smite, Bless; the Druid's Thorns, Mend, Entangle, Regrowth,
  Call Lightning; the Bard's Song, Mockery, Lullaby, Rally; the Ranger's Volley, Aimed Shot, Mark; the Knight's
  Guard, Taunt, Shield Bash; the Rogue's Dirty Trick - and Pick Lock, which works on its own (walk into a locked
  door without a key). Healing, cures and Light can be cast between fights (C on the way).
  Monsters have ways of their own: goblins and dark elves shoot over the front row, kobolds bolt with a purse when
  hurt, orcs land savage blows, trolls knit each round, wraiths drain experience, ogres knock flat, minotaurs
  charge, vampires feed on every blow, demons breathe fire on everyone, wyverns strike two at once. Deeper down,
  groups mix two kinds, and one in eight has a leader: Hulking, Swift, Venomous, Ancient, Cunning or Ravenous.
  The Lich King: hurt past half, he calls skeletons up out of the floor; near his end, a deathly cold on everyone;
  and killed, he rises again at two fifths of his strength - as often as you kill him - unless his phylactery, a
  cold box on floor 19, has been smashed (Space). The carvings say so.

The hoard (phase 5)
  Six slots a hero: weapon, off hand (a shield), armour, helm, ring, amulet. Armour has a weight - Mages wear light,
  Knights and Paladins anything; only a Ranger draws a bow; a two-handed weapon leaves no hand for a shield. Rings
  add to a stat; amulets turn one ailment aside (poison, curses, stone, blindness, sleep) or ward; a Flaming, Frost
  or Blessed weapon bites deep into what fears it (trolls and the rotting, demons, the undead). Found gear from the
  second floor down may be unknown - a bare name until it's worn (which names it, and may find a curse that clings
  until the temple lifts it), read with a Scroll of Identify, or shown to the camp's scribe (25 gold for the lot).
  Scrolls (Identify, Mapping, Teleport between fights; Fire, Frost, Protection in them) and wands (Fire, Frost,
  Sleep; Healing, anywhere) with a few charges - anyone can use them, from the pack (Item in a fight).
  From the second floor down a chest may be trapped: a Rogue sees to it, or it springs - a poisoned needle, choking
  gas, a blade, an alarm that brings a fight. The camp has a Tavern: three recruits a step behind the party's level,
  one to take the place of a hero who has fallen (what they wore besides weapon and armour stays with the party).
  Unlocks between runs (the title's Hall of Fame card lists them; the creation screen's Kit picks one): the deepest
  run so far earns the Veteran's kit at floor 5, the Delver's at 10, the Heir's at 15, the Legend's for slaying the
  Lich King. Today's (beside the seed) gives today's dungeon - the same one for everyone, marked with a sun in the
  Hall of Fame; a run's seed and party are kept there too (hover a row).

Sound and polish (phase 6)
  Music, made as it plays (55-music.js): a tune for each depth (the Catacombs in a slow Dorian, the Flooded Vaults
  Phrygian, the Dwarven Halls a plucked Mixolydian, the Palace in harmonic minor), a battle theme with drums, a lute
  by the camp fire, the title's own, and one each for victory and the fall. Each is written once from a seed - four
  chords and sixty-four steps of melody, A A B A - and played on oscillators through a filter and a little
  stone-hall reverb; one tune fades into the next as the mode and the depth change. Settings has Music and its
  volume beside Sound and its volume.
  Each depth has its own ambience (dripping; running water; wind and far-off iron; a cold hum and whispers; the
  camp fire crackles) and its own footfall. New sounds in their places: a door's creak, a key or a pick in the lock,
  the secret door grinding, the lever, a trapped lid, the teleporter, a fall, a miss, a hero falling, an ailment,
  the phylactery shattering, the Lich King rising. Every kind of monster has a call - small things chitter, the
  undead rattle, beasts and brutes roar - heard when a fight starts and, softer, when something is coming down the
  corridor towards you (louder the nearer it is).
  The monsters are finished: a sheen where the torch catches them, fur on the rat, scales on the wyvern, belts and
  seams on whatever carries a weapon, cracked stone on the gargoyle, warts on the troll, rot on the zombie, brows
  drawn down and grim mouths with teeth or fangs; they sway where they stand, shudder when struck, and sink into
  the floor when they fall (a wraith rises). The title wears an emblem: the Lich King's crown on his skull, over a
  crossed sword and staff. A run ends on a screen of its own - what happened, who came home and who fell, and the
  tally (floors, gold, monsters slain, chests opened, steps walked, fights and flights, kit, seed, the place in the
  Hall of Fame); Enter or Space closes it. The Hall of Fame keeps that tally: click a row for the party, the seed
  (Play this seed sets it), the kit and the numbers.

The look: three themes (the second big update, phase 1)
  Theme - on the title's foot and in Settings - changes the look of everything at once, at any time: on the
  title (the corridor behind it changes too), in a corridor, in the middle of a fight.
    Drawn        the game's own art, painted in code (30-art.js), as it has always been.
    Pixel tiles  Dungeon Crawl Stone Soup's 32-pixel tiles (CC0, by the Crawl Stone Soup team and the RLTiles
                 project): the stone of each depth, every door, chest, fountain, altar and trap, all seventeen
                 monsters, the things in the pack (as icons in the pack, on the merchant's table and on a hero's
                 sheet), the spells (as icons in the casting menus) and the heroes as paper dolls. Crisp and
                 chunky, the way a crawler of the time was.
    Stone        photographed stone (ambientCG, CC0) on the walls, floors and ceilings of each depth - old bricks
                 and cobbles in the Catacombs, wet rock in the Vaults, sandstone blocks under oak beams in the
                 Halls, black marble over a chequered floor in the Palace - with the drawn furniture and monsters.
  The packs ride inside the one file. pack.py --gather copies the chosen tiles and textures from the whole sets
  (kept in Local Storage\Dungeon Crawl - Sprites and Local Storage\ambientCG - Textures, every tile and every
  map, for the updates to come) into src\art\ (committed, with CREDITS.txt); pack.py writes src\js\35-packs.js
  from them - one atlas of the tiles and the twelve textures, as text - and build.py inlines it like any other
  module; pack.py --check says whether it is current (the tests ask). 36-looks.js builds each theme's set and
  picks portraits and icons by the theme. Credits, on the title, names both sources.

Motion and spectacle (the second big update, phase 2)
  A fight moves. A monster lunges when it strikes; a goblin's or a dark elf's arrow and a demon's fire come down
  the corridor at you; the party leans into each blow it lands (a Ranger's arrow flies); a heavy blow shakes the
  view and jolts the hero's card. Spells fly: a bolt of force, a fire bolt, a fireball that bursts over every foe,
  frost that falls on them, lightning that cracks the air white, holy light over the undead, thorns up from the
  floor, the Ranger's volley - each with its own wash of colour over the view, and a blow waits for its bolt to
  land. Sparks fly from every hit; a fallen monster bursts into sparks, the undead into bone; the Lich King's
  skeletons claw up in a spray of bone, and when he rises a ring of cold light spreads across the floor and the
  hall shakes. A mending glows green on the hero's card, a blessing gold, a ward blue; a trap's gas fills the view
  green, its blade red. The dungeon lives too: torches burn on some walls of every depth (never over a lever or a
  carving) and the floors of the Flooded Vaults stand in water that shimmers. All of it in the three themes - the
  Pixel theme draws the effects, the torches and the water with Crawl's own tiles. Monsters wait while the pack,
  a sheet, the map or a menu is open.
  45-fx.js is CM.Effects - projectiles, bursts, rings, flares, rain, drift - a list the frame loop turns into
  sprites lit by their own glow; the recipes (which event gets which effect) are in 80-main.js, where the camera
  and the foes' places are known; the renderer shakes and punches the camera; the window washes the view with
  colour and jolts or glows the cards.

The game is one HTML file
  game\Claude and Magic v<version>.html is the whole game: open it in a browser (Chrome, Edge, Firefox) and play.
  It draws with WebGL 2 and makes its sounds and music with Web Audio, in code; the two art packs ride inside it
  as text - there are no pictures or sound files to ship. Your runs, the Hall of Fame and your settings are kept in that browser (localStorage); Export / Import on
  the title screen carries them, as text, to another browser or back.

In the Timeline
  __init__.py is a thin host: the newest "Claude and Magic v*.html" in game\ opens in a Qt WebEngine window of the
  computer's style, on one permanent browser profile in ClaudeGames\Saves\claudemagic (storage\, cache\) shared by
  all three computers and by the launcher's APPS copy - so a run begun on XP is there on Windows 11. Sound follows
  the computer's mute. The first time, the host hands the page the old Python version's run.json and
  hall_of_fame.json from that Saves folder (then keeps them as *.imported.json).
  It's in Start > Games, the desktop's Games folder, and - this game alone among the games - loose on the desktop of
  all three computers; and in the launcher's APPS, where it runs on its own without a computer around it.

The source
  src\index.html, src\style.css and src\js\*.js (read in name order):
    00-util.js    CM, the version, a seeded random (the same seed, the same dungeon), saving in the browser
    10-data.js    the classes, gear, monsters (and how each is painted), the depths and their colours, the keys
    20-world.js   items, a floor's maze with its chests, monsters and ladder, monster groups, a new party
    30-art.js     every picture of the Drawn theme, painted in code: stone, chests, hatches, monsters, portraits
    35-packs.js   GENERATED by pack.py from src\art: the Pixel theme's atlas and the Stone theme's textures
    36-looks.js   the three themes: each one's set for a depth, the paper-doll portraits, the item and spell icons
    40-render.js  the WebGL 2 view: the floor's mesh, billboards, torchlight and fog, smooth steps and turns, shakes
    45-fx.js      what flies, bursts, rings and rains: the effects, advanced each frame into sprites
    50-audio.js   the sounds, each depth's ambience and the monsters' calls, synthesised
    55-music.js   the music, written from a seed and played as it goes
    60-game.js    the rules: moving, fighting, loot, the camp, saving, the Hall of Fame - no screen in it
    70-ui.js      the title, the party and log, the automap, the bag and merchant, the dialogs
    80-main.js    wiring, keys, the frame loop
  src\art\pixel\*.png and src\art\stone\*.jpg are the chosen tiles and textures (pack.py --gather puts them there).
  python build.py writes game\Claude and Magic v<VERSION>.html from them (and removes an older version's file);
  python build.py --check says whether the built file is current. Bump VERSION in build.py for a new file name.
  Tests\test_claudemagic.py drives the built game in Qt WebEngine offscreen (on a scratch profile).

Keys
  W/Up forward, S/Down back, A/Left and D/Right turn, Q/E sidestep, Space use (a chest, the ladder or stairs, a
  fountain, an altar, a lever or carving on the wall you face - or search that wall), C cast between fights, I
  inventory, 1-4 a hero's sheet, Tab the automap large, Esc the menu. In a fight: F fight the chosen foe, C cast or
  a skill, P an item, D defend, R run, Tab or 1-9 or a click to choose the foe, Esc back. Enter or Space closes the
  ending. F3 shows frames per second.
