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

The guardians (the second big update, phase 3)
  The shaft down to each camp is held. On the floor above every camp something has made its lair over the ladder,
  and the party must go through it: it stands on the shaft, so there is no way round - though there is a way back
  (run, and it mends a quarter and keeps its lair). Each has a set piece of its own with a carving of its story, two
  ways of fighting, a weakness and a thing it shrugs off, and a relic it leaves when it falls:
    The Rat King        floor 5, in a nest of bones and rags heaped over the shaft, with two rats. Every third turn
                        the swarm pours out of the refuse (four at most); its bite poisons more often than not, for
                        longer, and bites a poisoned hero half again as hard. Fire bites deep. Leaves the Rat King's
                        Crown: a helm, proof against poison, +3 Luck.
    The Drowned Knight  floor 10, in a sunken hall of pillars and water, his throne behind him. Every third turn he
                        drags one of the party under (half again the blow, and a round lost gasping); killed, the
                        water lifts him up again, once, at a third of his strength. Undead: holy bites deep, frost
                        does little. Leaves the Shield of the Drowned: proof against paralysis, warding +2.
    The Forge-Warden    floor 15, in the dwarves' forge - anvils, embers in the floor, pillars. Every third turn the
                        hammer comes down on the whole front row and may knock someone flat; every blow struck on it
                        sears the striker (arrows don't). Fire does it little, frost bites deep. Leaves the
                        Forge-Warden's Hammer: two-handed, flaming, and a blow may leave the foe reeling.
  None of them sleeps, is held or is routed, any more than the Lich King is. A guardian's fight has a heavier tune
  of its own (the Lich King's too); its fall tolls, and washes the view in its colour. The Hall of Fame's details
  name the guardians a run slew, and the title's Trophies keep every guardian ever slain (the Lich King among them)
  between runs and through Export / Import. CM.GUARDIANS in 10-data.js holds all of it - the lair's rows (B the
  guardian over the shaft, # a pillar, n t v e the furniture, W the carving, flood for water on every floor), the
  numbers, the words and the relic - so a deeper dungeon can add more.

The dungeon's people and its puzzles (the second big update, phase 4)
  The dungeon is not empty of the living, or of the dead who still have something to say. Now and then a floor has
  someone on it - stand where they are and press Space:
    A ghost        with a request: bring it the bones that lie somewhere on its floor; kill the thing that killed it
                   (a leader among the floor's monsters, marked for it); or read the floor's carving and tell it what
                   it says. Done, the ghost rests, leaves a ring or an amulet (known already) and experience, and
                   tells its tale - which goes in the journal.
    A hermit       who names any unknown thing in the pack, for a story: each carving read and each tale heard pays
                   for one. With nothing unknown to name, he points the way down instead.
    A lost adventurer, bound, from a party that didn't come back. Cut loose, they take the place of a hero who has
                   fallen or turned to stone - or, if the party is whole, give you a rope and their map of the floor
                   and make for the camp, where the tavern lists them first, and free.
  The journal (J, or the Journal button) keeps everything read and heard: the carvings by floor, what the dead
  said, the riddles answered. It is saved with the run.
  Puzzles, from the third and fourth floors down:
    Riddle doors   some doors are written over with runes and ask a question when you walk into them - about the
                   carvings on the floors above (the answer is always one you could have read, and the journal
                   remembers it). The right answer opens the door and teaches the party something; a wrong one burns
                   everyone a little, and the door asks again.
    Pressure plates  some gates have no lever: a plate in the floor sinks under your boot and the iron grinds up.
                   Other plates are traps - a needle, gas, a blade, an alarm - sprung once, then known.
    Rope           sold at the camp, or a rescued adventurer's gift. With a rope in the pack, a pit is no fall: the
                   party lowers itself to the floor below without a scratch, and the rope stays tied - a way back up
                   (Space on it) and down again, for the rest of the run.
  Special floors - one or two in a run, by the seed, never on a guardian's floor:
    a flooded floor   (in the Vaults) the whole floor is under water: torches burn twice as fast in the damp.
    a dark floor      a magical dark lies over every square: the automap only learns where you have stood, unless a
                      Light is up - the Mage's or Cleric's spell cuts through it.
    a labyrinth       (in the Halls) no rooms, no doors, every dead end kept - and the Minotaur of the Labyrinth,
                      which knows where you are from anywhere on the floor and comes.
  In code: CM.RIDDLES, CM.GHOSTS, CM.REQUESTS, CM.HERMIT and CM.ADVENTURER (10-data.js); CM.specialFor, CM.rope,
  CM.bones and the placing at the end of makeFloor (20-world.js), so the floors of a seed stay as they were; the
  game's remember/talk/answerRiddle/ropeDown and the plates in arrive (60-game.js); the talk, riddle and journal
  dialogs (70-ui.js). Pixel theme: Crawl's ghost, Crazy Yiuf, a slave for the adventurer, its pressure plate and
  sealed door.

Growth and craft (the second big update, phase 5)
  A path for each calling. At level 5 a hero's sheet (1-4) offers two paths, and the one chosen gives its first
  trait at once and its second at level 10:
    Knight    Bulwark   +3 defence; a blow the Knight steps in front of does half.
              Champion  +3 attack; every Fight is two blows, the second at half.
    Paladin   Crusader  every blow bites deep into the undead; Smite falls on every undead foe.
              Shepherd  Lay on Hands mends half again and lifts the small ailments; it can call a fallen hero back, once a fight.
    Rogue     Assassin  a weak spot does triple; the first blow of every fight finds one.
              Trickster Dirty Trick also holds the foe; running always works (not from the Lich King), and no surprises.
    Ranger    Sharpshooter  arrows never miss; Volley looses three.
              Warden    trapdoors and trap plates two steps off are seen and a hidden door beside you found; torches burn half as fast.
    Cleric    Priest    Heal mends half again; Raise Dead brings a hero back whole.
              Exorcist  Turn Undead scorches the living too; Bless also lays Protection.
    Mage      Pyromancer  fire spells do half again; Fireball leaves every foe burning two rounds.
              Archmage  every spell costs one less; two magic back each round of a fight.
    Druid     Grove     Thorns mends the party three times as much; the party mends 3 every round.
              Storm     Call Lightning strikes every foe; lightning may leave a foe reeling.
    Bard      Skald     Song gives +4 attack and 2 off every blow; Song lasts the whole floor.
              Jester    Mockery half-blinds the foe; Lullaby never fails.
  Tomes. Some chests deeper down hold a tome (Tome of Frost, of Mending, of Blessing, of Storms...). Read by a caster
  (Paladin, Cleric, Mage, Druid, Bard - Read it to them from the pack), it teaches the spell for good, at its usual
  cost - a Cleric who throws frost, a Bard who blesses. A tome of a spell the reader knows is refused.
  The smith. A dwarf of the deep halls works a forge by the camp (Smith, at the camp). Gems turn up in chests from the
  third floor down: a diamond and 80 gold (160 the second time, 240 the third) put +1 on a weapon, armour, a shield or
  a helm, three times at most; a ruby, a sapphire or a sunstone and 120 gold set fire, frost or holiness into a weapon.
  The vault. The merchant keeps one thing in an iron box for whoever comes after (Vault, at the camp): leave an
  heirloom and it waits, through the end of the run and the start of the next, until a party at a camp takes it up.
  It travels with Export / Import. The ending screen says what waits there.
  In code: CM.PATHS / CM.PATH_AT / CM.trait(hero, id) / CM.needsPath, CM.TOMES, CM.GEMS, CM.SMITH (10-data.js); the
  traits bite in strike, hurt, effective, useAbility/doAbility, endRound, flee, burn and look (60-game.js), the paths'
  flat bonuses in CM.recompute; readTome, smith, leaveHeirloom/takeHeirloom; the chests' gems and tomes come by the seed
  at the end of makeFloor, so the floors stay as they were. The sheet offers the path; the Smith and Vault dialogs are
  the camp's.

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
    10-data.js    the classes, gear, monsters (and how each is painted), the guardians, the riddles and the people, the paths, tomes and gems, the depths
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
