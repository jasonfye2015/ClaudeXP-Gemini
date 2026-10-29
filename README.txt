Claude and Magic - twenty floors down, the Lich King waits
==========================================================

A first-person dungeon crawler ("blobber", after Wizardry, Might and Magic and Eye of the Beholder): a party of four
moves as one through twenty floors of stone, a square and a quarter-turn at a time, smoothly, in 3D. Chests and
fallen monsters give gear and gold; a merchant's camp waits below floors 5, 10 and 15; the Lich King is on floor 20.
When the whole party falls the run is over - the deepest runs go in the Hall of Fame.

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
  W/Up forward, S/Down back, A/Left and D/Right turn, Q/E sidestep, Space use (a chest, the ladder), I inventory,
  Tab the automap large, Esc the menu. In a fight: F fight, C cast, P potion, R run. F3 shows frames per second.
