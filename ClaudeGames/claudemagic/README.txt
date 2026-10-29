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

The game is one HTML file
  game\Claude and Magic v<version>.html is the whole game: open it in a browser (Chrome, Edge, Firefox) and play.
  It draws with WebGL 2 and makes its sounds with Web Audio, in code - there are no pictures or sound files to
  ship. Your runs, the Hall of Fame and your settings are kept in that browser (localStorage); Export / Import on
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
    30-art.js     every picture, painted in code: the stone of each depth, chests, hatches, monsters, portraits
    40-render.js  the WebGL 2 view: the floor's mesh, billboards, torchlight and fog, smooth steps and turns
    50-audio.js   the sounds and the dungeon's ambience, synthesised
    60-game.js    the rules: moving, fighting, loot, the camp, saving, the Hall of Fame - no screen in it
    70-ui.js      the title, the party and log, the automap, the bag and merchant, the dialogs
    80-main.js    wiring, keys, the frame loop
  python build.py writes game\Claude and Magic v<VERSION>.html from them (and removes an older version's file);
  python build.py --check says whether the built file is current. Bump VERSION in build.py for a new file name.
  Tests\test_claudemagic.py drives the built game in Qt WebEngine offscreen (on a scratch profile).

Keys
  W/Up forward, S/Down back, A/Left and D/Right turn, Q/E sidestep, Space use (a chest, the ladder or stairs, a
  fountain, an altar, a lever or carving on the wall you face - or search that wall), I inventory, Tab the automap
  large, Esc the menu. In a fight: F fight, C cast, P potion, R run. F3 shows frames per second.
