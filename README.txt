Claude and Magic - seventy floors down, the Lich King waits
===========================================================

A first-person dungeon crawler ("blobber", after Wizardry, Might and Magic and Eye of the Beholder): a party of four
moves as one through seventy floors of stone, a square and a quarter-turn at a time, smoothly, in 3D. Chests and
fallen monsters give gear and gold; a merchant's camp waits below floors 17, 35 and 52; the Lich King is on floor 70.
When the whole party falls the run is over - the deepest runs go in the Hall of Fame. Below the Lich King, the Deep goes
down to the Root of the World on floor 100; an Endless expedition goes on below that, with no bottom.

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
  eight callings (eleven, with the three earned - see The party, wider) - Knight, Paladin, Rogue, Ranger, Cleric, Mage, Druid, Bard - six stats rolled on three dice plus
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

Ways to play (the second big update, phase 6)
  Difficulty, chosen when the party sets out: Gentle (monsters a quarter weaker, more gold), Fair (the dungeon as it
  is) or Grim (monsters a third tougher and harder-hitting, a little less gold; the Hall of Fame marks the run). The
  weight is put on each monster as its fight begins, so the floors of a seed are the same at every difficulty.
  Today's dungeon comes with two mutators from the date, named on the creation screen and in the log: Hordes (every
  band one more), Brittle (half the health, half again the blows), Rich veins (chests hold twice the gold), Swift
  (monsters move faster), Drought (every fountain dry), Gloom (torches burn twice as fast), Lean (no potions, 100 gold
  more). The Hall of Fame remembers which.
  Achievements, earned once and kept between runs (and through Export / Import): Crownbreaker, Unfallen, Grim, Swift,
  Of the Halls, Minotaur's Bane, Unbowed, Of the Vaults, Of the Day, Tempered, Rich, Learned, Kind, Gentle, Delver. The
  title's Achievements block lists them; the first earned in that order is the title the player wears under the
  tagline ("Jason the Unbowed"), and a run's entry in the Hall of Fame notes what it earned.
  Three expedition slots, on the title: each keeps a run of its own; New Expedition starts in the chosen slot (and
  warns if a run waits there), Continue carries on the chosen one, and a run's end clears only its own slot. Export
  carries all three.
  Keys (the title's Keys button): every key can be set - Change, then press the key you want; one key, one action;
  Reset puts them back. The arrows always move and turn, and Esc always steps back.
  A gamepad works as it is: the pad or stick moves, A uses, talks or picks, B steps back, X opens the pack, Y casts,
  the shoulders sidestep (in a fight, pick the next foe), Start pauses, Select opens the map; in a fight A fights, B
  defends, X an item, Y a spell; in any list or dialog the pad moves a highlight along the buttons and A presses.
  On a touch screen (or with the mouse), tap the view: the left and right thirds turn, the top walks, the bottom
  steps back; Settings can turn that off. The action buttons under the log were always there to tap.
  The summary card: a run's end (and every Hall of Fame entry's details) offers one - the emblem, who went, how it
  ended, the tally, the guardians and what was earned - to copy as text or save as a PNG.
  In code: CM.DIFFICULTIES, CM.MUTATORS / mutatorsFor, CM.ACHIEVEMENTS / titleFor, CM.DEFAULT_KEYS / KEY_ACTIONS,
  CM.summaryText (10-data.js); game.tune/has/achieve/setSlot, lastRun as the slot's run, runs saved as run / run2 /
  run3 (60-game.js); renderKeys/rebind/resetKeys, openCard, padTargets/padFocus/padPress, tapView (70-ui.js); the
  keys as set, the gamepad polled each frame as synthetic key presses, the tap on the view (80-main.js);
  CM.art.summaryCard (30-art.js).

The Deep (phase 7)
  The Lich King's fall no longer ends the run unless you want it to. When he falls, the crown is yours and the
  Hall of Fame will say so - and behind the throne the floor has split: a shaft goes down into thirty floors the
  carvings never spoke of. The victory screen offers the choice: Into the daylight (the run ends there, a victory),
  or Into the Deep. A party that goes down and falls is still a crowned party in the Hall of Fame ("SLEW THE LICH
  KING, floor 34"); a party that reaches the bottom ranks above everything ("TO THE BOTTOM").
  Six bands of five floors, each with its own stone (and in the Pixel theme Crawl's own walls and floors; in the
  Stone theme a band above's photographs in the band's own colour), its own tune, its own monsters that never climb
  above floor 20, and its own carvings - the story under the story: who let the water in, what the dead were fed to,
  what the dwarves really fled, what the box was made of and by whom, who taught the king, and what dreamed him.
    21-25  The Drowned Town      the Drowned and the Weed Hags; the Drowned Queen over the shaft on 25 (her Lament puts
                                 the party to sleep, her court climbs out of the water to her, and she rises once).
                                 Relic: the Queen's Ring.
    26-30  The Fungal Deep       Fungal Horrors and Spore Beasts; the Mycelial Mind on 30 (spores that poison, spore
                                 beasts that tear loose, flesh that regrows every round). Relic: the Sporecap Helm.
    31-35  The Crystal Caverns   Crystal Golems and Shard Wisps; the Crystal Tyrant on 35 (shards that fly and blind;
                                 every blow struck on it cuts the striker). Relic: the Prism Amulet.
    36-40  The Foundry           Iron Hounds and Foundry Imps; the Foundry Master on 40 (a furnace breath over everyone,
                                 the hammer on the front line, the forge's heat). Relic: the Ember Mail.
    41-45  The Ossuary           Bone Colossi and Grave Priests; the Bone Patriarch on 45 (skeletons raised from the
                                 heaps, a curse spoken on the party, blows that drain experience). Relic: the
                                 Patriarch's Reliquary.
    46-50  The Root of the World Rootlings and Hollow Ones; the Root of the World on 50 (the quake under everyone,
                                 rootlings torn from its bark, sap that regrows, and once, it knits). No relic: there is
                                 nothing below. Its fall is the run's end, in triumph.
  A camp waits below every fifth floor of the Deep (25, 30, 35, 40, 45), with the smith and the vault. The Deep has
  its own special floors (a flooded street, a labyrinth of the forges, the ossuary's dark). The monsters' level climbs
  more slowly than the floors (floor 50 fights at level 35), the bands are two to five strong and a leader comes one
  time in five. Two achievements more: Of the Deep (floor 30) and To the Bottom. One kit more: the Abyss kit, for
  reaching floor 30 (every hero at level 3 with a boon, 150 gold more, a rope, a diamond, a Scroll of Mapping).
  In code: CM.BOTTOM, CM.CAMP_AFTER, CM.THEMES (ten bands, the Deep's with `photos`), CM.MONSTERS (the Deep's kinds carry
  `deep`: their band), CM.SHALLOW and CM.monsterLevel, CM.GUARDIANS as data (moves: summon / grasp / slam / breath /
  ailment; passives: plague / rise / heat / glass / regrow / drain; `final` for the Root), CM.AMBIENCE_OF (10-data.js);
  CM.LORE to fifty, CM.deepGroup / makeElite, the Deep's special floors (20-world.js); game.crown() and the "crowned"
  event, guardianMove / summonFor, bottom, the Hall of Fame's order (60-game.js); the crowning dialog (70-ui.js);
  depth4-9 tunes (55-music.js); fungus, crystal and root furniture (30-art.js).

Endless (phase 8)
  An Expedition choice on the creation screen, beside the difficulty: The dungeon (as ever: fifty floors, the Lich
  King on 20, the Root of the World and the bottom on 50) or Endless. An Endless expedition is the same fifty floors
  and the same king - and then no bottom. The Root's fall opens a shaft like any guardian's, a camp waits below the
  fiftieth floor and below every fifth floor after it, and below the Root the stair goes on:
    The bands come round again, five floors each, in order: the Catacombs on 51-55, the Flooded Vaults on 56-60, and
    so on to the Root of the World on 96-100, and the Catacombs again on 101 - with their own stone, tunes and
    monsters (the first four bands' kinds come back at the depth's level: floor 61 fights the Dwarven Halls' ogres
    and trolls at level 40). The monsters' level keeps climbing (half a level a floor), the bands are a monster
    larger and a leader comes three times in ten; the special floors (flooded, dark, labyrinth) come round where the
    first fifty had them, of whatever kind the dark dreams.
    The guardians return as echoes, every tenth floor, in the order they were met: the Rat King's Echo on 60, the
    Drowned Knight's on 70 ... the Root's on 140, the Rat King's again on 150. An echo is the guardian grown to the
    depth (its strength scaled by this floor's monster level against its own floor's), drawn a little through, in
    its own lair with its own moves; it leaves no relic and is no trophy - "the echo fades, and leaves nothing but
    the shaft it stood over".
    The dark deepens: on floors 61, 71, 81 ... one of the daily dungeon's mutators the run doesn't have yet is added
    - Hordes, Brittle, Swift, Gloom or Drought, chosen by the seed - and stays.
    The carvings are not the story any more: eight sayings of the dream still dreaming, by the seed.
  Endless runs go on a board of their own - the Hall of Fame has two now, The dungeon and Endless, a button each -
  ranked by depth with the crown noted ("floor 64 - crowned"); the ending says "Floor N of the endless dark", the
  summary card and the continue note say Endless, and Export carries the board. Both boards unlock the kits. Two
  achievements more: Without End (floor 60) and Beyond the Dream (floor 100; its title ranks above To the Bottom).
  An Endless party that takes the daylight on floor 20 is a victory like any, on the Endless board.
  In code: CM.themeFor wraps below CM.BOTTOM, CM.GUARDIAN_ORDER / CM.echoOf / CM.guardianFor, CM.LORE_ENDLESS and
  loreText("e:<n>"), CM.DEEPENING, CM.endlessFall, the achievements (10-data.js); CM.guardianMonster(id, floor) and
  guardianGroup, the carvings, specialFor and deepGroup below the bottom (20-world.js); game.endless, campBelow,
  deepen / deepened, fameEndless / sortFameEndless / allFame, endRun's board, slayGuardian's echo (60-game.js); the
  Expedition select, the two boards, the ending (70-ui.js); echoes drawn through (80-main.js); the card (30-art.js).

Foundations (the third big update, phase 0)
  The save is small. A floor was kept whole - every wall of every floor walked - and a deep run could outgrow what a
  browser keeps (about 5 MB for everything) without a word. Now a floor is saved as what the party did to it: the doors
  opened, the chests taken, the monsters moved or slain, the squares seen (as a bitset), and the floor is made again
  from the seed and the changes laid back over it (25-saves.js: CM.snapshot, CM.floorDelta, CM.restoreFloor). A run
  a hundred floors deep is a few hundred kilobytes where it was megabytes. Saves carry a schema number (CM.SCHEMA)
  and a chain of migrations (CM.MIGRATIONS) lifts an older one: a v1.0 save, whole floors and all, loads as it was.
  If the browser will not keep a save, the game says so in the log, once, and Settings shows how much is saved there.
  This asks one thing of the generator, kept from here on: a seed makes the same floor in every version. Anything a
  later version adds to a floor takes its dice from a hash of its own (as the gems, riddles and plates already do),
  never from the floor's own random. A floor whose fingerprint has changed still loads, with a note in the log.
  The dice are the seed's. A run's random is seeded from the seed, saved with the run, and reseeded at the start of
  every fight from the seed, the floor, the fight's number and the step: the same fight, fought the same way, goes the
  same way - so Today's dungeon is the same dungeon for everyone all the way down, and a reload never re-rolls a fight.
  (Heroes made on the creation screen still roll their stats on real dice.)
  The rules are five files instead of one: 60-game.js keeps the class, the events, saving and the stairs; 61-explore.js
  moving, looking and using; 62-combat.js the fight; 63-camp.js the bag and the camp; 64-meta.js the dungeon's people,
  growth, achievements, the Hall of Fame and Export / Import. Each adds its methods to CM.Game.prototype.
  Tests, in the repository: tools/headless.js loads the rules into Node with no screen; tests/run.js checks the build
  is current, that every floor of many seeds can be finished (to 100, Endless), that a floor and a run survive save
  and load, that the v1.0 fixtures in tests/fixtures still load, that a full browser is noticed, and that the dice are
  the seed's; tests/smoke.js opens the built file in Playwright's Chromium, plays, reloads and continues. `npm test`
  runs both; .github/workflows/test.yml runs them on every push. pack.py --check compares the atlas pixel by pixel
  now (Pillow's PNG encoder differs between versions).
  The balance simulator: tools/bot.js is a party that plays by itself - the chests on the way, the key before the
  door, the lever before the gate, fountains when hurt, fights (healing under a third, casting at a crowd), the
  class's own stat at every level, the camp's rest and potions, the phylactery on 19 - and tools/sim.js sends it
  down many seeds at every difficulty and reports where parties fall, how far they get and their level at each camp
  (node tools/sim.js --seeds 30 --to 50). The fight and the hoard don't change without a look at it.
  F3 and Settings name the build (CM.built, the day build.py ran); Export carries it.

Quality of life (the third big update, phase 1)
  The party walks by itself. Click a square on the automap (the small one, or the large one on Tab) and the party
  walks there over the squares it knows, opening doors on the way, and stops when a band of monsters is three steps
  off, when something is underfoot (a chest, a fountain, a lever, someone to talk to), when something new comes into
  view, or when the light fails. Explore (X) walks to the nearest square with an unknown one beside it, and on to the
  next, until the floor is known as far as the light has reached. Any key or click stops a walk. It never walks into
  a pit, a known trap or a riddle door by itself.
  Notes: right-click a square on the automap for a word or two ("key?", "come back") - a flag and the words on the
  map, kept with the floor.
  A fight, faster: Auto (A) has the party fight on by itself - healing under a third, a fireball for a crowd, the
  weakest foe for the blows - until the fight ends or someone drops below half; any key takes the reins back. Under
  each foe, the odds: how likely the hero whose turn it is is to hit, and the range of the blow; in the casting menu,
  what each spell is likely to do. Settings has a Combat speed: the bolts and sparks fly at normal speed, fast, or as
  good as instantly.
  The pack: pick a thing, and each hero's button says what it would change against what they wear (+2, -1, same,
  can't - with the reason); Sort the pack puts weapons first, then armour, shields, helms, rings and amulets, the best
  of each first, and the rest after.
  Waystones: every camp reached is marked, and from any camp the Waystone leads to another the party has reached -
  back up to the temple and the smith from deep down, and down again. The floors between stay as they were.
  In code: pathTo / travelTo / travelStep / explore / frontier / setNote (61-explore.js), autoFight / autoTurn /
  strikeEstimate / spellEstimate (62-combat.js), reachCamp / waystone / compare / sortBag (63-camp.js); the window
  steps a walk each frame the view is still and takes an Auto turn each time the bolts have landed (80-main.js);
  CM.fxSpeed (45-fx.js). The simulator's party fights with the game's own Auto hand now.

Everyone can play (the third big update, phase 7)
  Settings: Text size (normal, large, larger), Reduce motion (no shaking, no flashes, no washes of colour; on by
  default where the browser asks for it), High contrast (brighter text, sharper edges, a clear focus ring), and
  Gamepad: swap A and B. The log is a live region for a screen reader; every button shows its focus. On a phone, the
  view sits on top, the party two by two, the log short and the buttons as a thumb bar (style.css, the 640px rule).
  An ailment is always its mark and its name, never a colour alone.

The fight, deeper (the third big update, phase 2)
  Monsters have a shape. Every kind's health, blows and armour are its own share of the straight line of its level
  (CM.MONSTER_SHAPES, 10-data.js): a rat is frail and quick, a troll a wall of meat, a gargoyle all armour, an ogre
  hits like a falling roof. Every kind fears something and shrugs something off - fire for trolls, zombies, the fungal
  and the rooted; frost for demons, wyverns and the foundry's imps; lightning for the crystal, the iron and the dark
  elves; holiness for the undead (a vampire doubly) - and some do little from what they are made of (fire does little
  to a demon or an iron hound, frost to crystal and the drowned). CM.resistance(foe, element) says, for monsters and
  guardians alike; a flaming, frost or blessed blade reads the same table. Lightning is an element now (storm).
  The monsters have rows too. Goblins, dark elves, weed hags, shard wisps, foundry imps and grave priests keep to the
  back row, where a blow from the front must reach past their fellows for half - as the party's own back row does;
  a Ranger's arrows and every spell reach them whole. The target buttons say who is behind.
  The guardians show their hand. The turn before one of its great moves, a guardian telegraphs it - the Forge-Warden
  lifts the hammer, the Drowned Knight's gauntlet opens, the Tyrant begins to ring - in the log and on its target
  button, so the party can Defend, guard, or strike first.
  Combos: two things done in order that come to more than their sum, found by doing them and kept in the journal
  (CM.COMBOS): Shatter (frost on a foe, then Shield Bash: double), Twist the knife (a Rogue's blow on a mocked or
  marked foe: half again), Kindling (fire on a foe held by thorns or roots: half again), Consecrated strike (Smite
  under a Blessing: half again), Thunderclap (lightning on a chilled foe: double). Frost leaves a foe chilled two rounds.
  More ways for the monsters: the Weed Hag mends the most hurt of her fellows; the Crystal Golem wards one (the next
  blows do half); the Spore Beast tears in two when badly hurt; the Foundry Imp snatches a potion, a scroll or a gem
  from the pack and bolts with it. Each foe's statuses are on its button with the turns left (asleep 2, held 1, chilled,
  warded, burning, blinded).
  The bestiary, in the journal: every kind met and slain, what it does, and what it has been seen to fear or shrug off
  - learned by hitting it with the element - kept between runs and carried by Export / Import (CM.store "bestiary").
  The level curve is measured now. The old curve (60 * (L-1)^1.6) was the twenty-floor game's: with fifty floors it
  ran to level 100 and more by the bottom, and the simulator's parties reached the Root at level 120 without trying.
  The new one (20 * (L-1) + 8 * (L-1)^2.6) is fitted to the experience a party actually earns fighting its way down:
  about level 20 on floor 20 and the middle thirties at the bottom - the monsters' own level. Heroes already past that
  keep their levels.

The hoard, deeper (the third big update, phase 3)
  Affixes. A found weapon or piece of armour may be fine (one affix, green) or rare (two, blue), from the third and
  eighth floors down: a prefix - Keen, Heavy, Vicious, Swift, Jolting on a weapon; Sturdy, Warding, Spiked, Quiet on
  armour - and a suffix: of the Bear, the Fox, the Oak, the Owl, the Saint, of Fortune (+2 to a stat), of Mending
  (a health a round), of Warding, of Embers, of Rime; below the Lich King the deeper pools open (Thirsting, Lulling,
  Cruel, Hallowed, Barbed; of the Deep, of the Root, of the Dreamer, of the Dark). An unknown thing shows only its base
  name until it is known. The affixes come from a hash of the seed, the floor and the chest (CM.affix), so the floors
  already laid out stay as they were.
  One unique in every band of five floors, in a chest on one of them (the seed says which), orange, each with a line
  of its story: Gravewarden, Tidecaller (whatever it cuts sleeps), Anvilheart, the Courtier's Mask, the Queen's Grief,
  the Sporemother's Finger (it feeds you), Prismshard, the Foundry Master's Gauntlet, the Reliquary Key, First Root.
  CM.UNIQUES; they are made of the same props as the affixes - crit, stats, regen, lifesteal, sleep, thorns, element.
  Relic sets: two of the guardians' relics worn by one hero give +2 attack and +2 defence; three or more, and they mend
  2 a round (CM.RELIC_SET; the sheet says so).
  The alchemist, at the camp. The monsters of each depth now and then drop something she wants - Grave Moss, Drowned
  Weed, Forge Soot, Bone Dust, Salt Weed, Spore Cap, Crystal Dust, Foundry Slag, Grave Salt, Root Sap (CM.INGREDIENTS)
  - and she makes things of it for gold (CM.RECIPES): a Greater Healing Potion (twice the merchant's), Oils of Fire,
  Rime and Saints (rubbed on a hero's weapon from the pack: the element for three fights), a Firepot (thrown in a fight
  - Item - fire on every foe), two Antidotes, and the Elixirs of Vigour and Fortune: +1 Constitution or Luck for good,
  to whoever has least (the Distilled achievement).
  The smith, extended: Salvage puts a weapon or piece of armour from the pack into the fire for scrap (two from a rare
  one), and five pieces of scrap stand in for a diamond; Rework the suffix strikes a piece of gear's suffix off and
  works another in, for a gem of any kind and 100 gold.
  In code: CM.affix, CM.makeUnique, CM.rarityOf, CM.heroStat (props.stats), CM.gearProp, CM.relicsWorn (20-world.js);
  the hooks in critChance, endRound, hurt (thorns), strike (an oil, the blade that drinks, the blow that lulls),
  useItemInBattle (the firepot), wonFight (the band's ingredient, the oil wearing) (62-combat.js); recipeLacks / brew,
  salvage, smith("reroll"), give (an oil) (63-camp.js); the Alchemist dialog, the smith's new rows, the rarity colours
  (70-ui.js); the new glyphs (36-looks.js).

The dungeon, stranger (the third big update, phase 5)
  Choices on the floor. A third of the floors have something to decide on (CM.EVENTS, placed by the seed): a shrine
  that wants blood (+1 Strength for a fifth of the front hero's health), someone in chains (a rescued adventurer, or a
  ghoul), a dice table, a fountain that runs black (+2 to a stat, and a curse), an old camp fire (a third of everyone's
  health, and perhaps company), a dead merchant (his purse, or his burial), a whispering box (the whole floor, perhaps
  a curse), a rats' nest (burn it with a torch, or rummage), a statue (a blessing on the next fight, or its hand - a
  boon, or the stone's gaze), a dropped pack (something fine, or a trap), a still pool (every ailment washed off; the
  Deep's pools have something in them), a hermit's grave (a tome, or the hermit). Space asks; 1-3 answer.
  The Deep's bands have their hazards (CM.HAZARDS): the Drowned Town's tide turns every thirty steps - at high tide
  torches burn double and the Drowned are quick; spore clouds in the Fungal Deep's ways poison the front row as often
  as not; in the Crystal Caverns the mirror walls throw a Magic Missile, a fire bolt or lightning onto a second foe
  for half; the Foundry's vents breathe fire on every third step; the Ossuary's bone piles stand up as you pass. A
  hazard is named when its band is first entered, and drawn on the automap once met; the party walking by itself
  goes round the known ones.
  Strongboxes: a heavy key on one floor (stamped with a number) opens an iron strongbox bolted to the floor two floors
  down - its gold and a rare thing (the Keyholder achievement). The box never lacks its key, nor the key its box.
  A peddler, now and then, on a floor: Space, and he lays out a cloth - a rare weapon or armour, a Greater Healing
  Potion, an oil, a Scroll of Mapping, an ingredient - at a peddler's prices. What you buy stays bought.
  A rival party, now and then: trade for their map of the floor (40 gold), challenge them for the floor (two
  Sellswords and a Hedge Wizard, at the depth's level; win, and their purse and their best thing are yours - the
  Unrivalled achievement), or let them be (they may leave a potion for the road).
  In code: the placing at the end of makeFloor by hashes of the seed (20-world.js); askEvent / choose, openStrongbox,
  peddle, meetRivals / chooseRivals, the hazards in arrive and the tide in move (61-explore.js); rebound, the blessing
  prayed for, the rivals' purse (62-combat.js); the choice dialog (70-ui.js). The floor's fingerprint (CM.floorPrint)
  no longer counts the chests and monsters, so a later version may add to a floor by its own hashes without a saved
  run noticing. New set pieces are left for a generator version: they would move the floors already laid out.

The party, wider (the third big update, phase 4)
  Three callings more, earned (the title's list shows them greyed with what earns them; the creation screen offers
  them once they are; the recruits and the rescued are still the eight):
    Monk         earned by Unfallen (the Lich King slain with no hero ever fallen). Fights with bare hands that grow
                 with every level (a Monk wears no weapon and no shield), is quick, and hard to hit. Flurry of Blows
                 (two blows at three fifths), Iron Palm (a blow that may leave the foe reeling), Still Mind (a quarter
                 of their health back and the small ailments gone, once a fight). Paths: Drunken Master (Sway, Counter,
                 Untouchable) and Iron Body (Iron Body, Iron Fists, Diamond Body).
    Necromancer  earned by slaying the Bone Patriarch. Drain (the life pulled out of a foe, half of it kept), Hex
                 (marked and half-blind), Raise Thrall (the last thing slain stands up on your side: it takes three
                 blows in four meant for the party and claws back each round), Death Pact (every foe withers, the
                 Necromancer bleeds). Paths: Lich-touched (Deep Drain, Thrall Unbound, Undying) and Hexer (Binding Hex,
                 Open Wound, Contagion).
    Artificer    earned by slaying the Foundry Master. Clockwork Turret (shoots a foe every round, once a fight), Ward
                 Engine (Protection), Oil the Gears (+3 speed for everyone), Firework (fire on every foe). Paths:
                 Siege Engineer (Scattershot, Twin Barrels, Bombard) and Tinkerer (Bulwark Engine, Medic Engine,
                 Overclock).
  The third tier: every path has a capstone at level 15 (CM.PATH_AT = [5, 10, 15]). Immovable, Executioner, Avenger,
  Sanctified, Shadowstep, Light Fingers, Piercing, Foresight, Benediction, Holy Fire, Immolation, Mana Well, Old Growth,
  Hurricane, Anthem, Last Laugh - and the new callings' own. The sheet says what each is and when it comes.
  Bonds: two heroes who have won forty fights side by side (CM.BOND_FIGHTS) are old friends: +1 attack and +1 defence
  each, heals between them a quarter kinder, and when one falls the other's next blow is doubled. One bond a hero;
  the sheet names it; the Old Friends achievement. At the camp's fire, old friends have a word for each other now and
  then (CM.BANTER). A bond ends at the grave.
  The memorial: a hero laid to rest at a camp fire (the tavern's recruit, or a rescued adventurer, taking their place)
  is written into the title's In memoriam - name, calling, level, floor, seed, date - kept between runs and carried by
  Export / Import (CM.store "memorial").
  In code: CM.CLASSES (three more), CM.ALL_CLASSES / CM.NEW_CLASSES / CM.CLASS_UNLOCK, the abilities, the paths and
  every t3 (10-data.js); game.classUnlocked / classesAvailable / remember2 (60-game.js); dodgeOf, enginesAct (the
  turret and the thrall at the round's end), bondOf / foughtTogether / applyBonds and the capstones' hooks through
  the fight (62-combat.js); the fists in CM.recompute and CM.cantWear (20-world.js); the portraits and paper dolls
  (30-art.js, 36-looks.js).

The look, and the sound (the third big update, phase 6)
  Render scale, in Settings: Full, Three quarters, Half - or Auto, which steps down a notch when frames have come late
  for two seconds and back up when they have come quick for ten (renderer.scale, 40-render.js; autoScale, 80-main.js).
  The monsters breathe where they stand, on the floor and in a fight (not with Reduce motion on). A guardian rises
  under its name: a title card across the view - the Forge-Warden, in The Forge - with a push of the camera. A leader
  among a band of monsters gets a stinger as the fight begins (the "elite" sound). The depth's tune gains a voice past
  the middle of its band - an echo an octave up - and a fifth under the melody on the band's last floor
  (CM.music.setDepth). A monster's call comes from the side it is on: the game says which way, and the sound is panned
  (StereoPanner, 50-audio.js).
  Left for a generator version: per-pixel lit stone wants ambientCG's normal and roughness maps, and only the colour
  maps were gathered into src/art - pack.py --gather on the machine with the full sets is the first step.

Around the game (the third big update, phase 8)
  Run codes: a run's end writes a code - CM1:seed:difficulty:expedition:kit:party - into its Hall of Fame entry and
  onto the summary card. Paste one into the seed box and New Expedition sets out with that seed, that party (names,
  stats and rows), that difficulty and that kit; Play this run, in a Hall of Fame entry's details, does the same.
  This week's challenge: the button beside Today's sets this week's seed (weekly-YYYY-WW, by the ISO week): one seed
  for everyone all week, three mutators from it, and a party the seed rolls - the creation screen locks the four. The
  Hall of Fame has a This week board: every run on the week's seed, from both boards.
  Three mutators more: Glass Cannon (every blow does double, theirs and yours), Pilgrim (no experience from fights;
  every floor first set foot on gives 60 experience a floor), Hunted (every band of monsters knows where you are).
  The remains of a fallen party: when a party falls, where it fell on which floor of which seed is kept (CM.store
  "fallen", through Export / Import); a later run on that seed finds their bones there - the names, the date, and one
  thing they carried, to take up. The dungeon remembers.
  Backup: Export / Import has Download (the export as a .json file) and takes a dropped file.

Balance, as measured (tools/sim.js, 20 seeds a difficulty, the classic four, the Pauper's kit, the bot's hand)
  Gentle: 17 of 20 parties reach the bottom; Fair: half the parties take the crown, 4 of 20 reach the bottom, most
  of the rest fall in the Palace (floors 16-20: the demons' breath) or the Ossuary; Grim: no party past floor 20 -
  the Lich King ends them all. Party level at the camps tracks the floor (6 at 5, 11 at 10, 25 at 25, 38 at 45).
  Run it after any change to the fight or the hoard.

A generator that can grow (the fourth big update, phase 0 - v2.1)
  Generator versions. The floors of every run begun before v2.1 come from generator 1 (21-gen1.js), frozen: the file
  is never edited again, and tests/fixtures/gen1.json holds the fingerprints of twenty-eight seeds' floors for the
  tests to check. New runs come from generator 2 (22-gen2.js), which carves as the first did but decides what a floor
  holds first, as a plan (CM.planFloor: the set pieces and their order, the plain rooms to try) - the door for new
  rooms and wings. A run keeps the generator it began with (run.gen; CM.makeFloor(number, seed, gen)); what every
  generator's floor gets afterwards, by hashes - gems, affixes, uniques, events, strongboxes, the peddler, rivals,
  hazards - is CM.furnish, shared.
  The log. Every choice the player makes - a step, a turn, Space, a fight's command, a purchase, a brew, an answer -
  goes down as a line (game.logAct), with the moments the monsters move (a tick), and is saved with the run packed
  (CM.packLog: a character a step). CM.replayRun(spec) plays a run again from its seed and its log and comes out the
  same, step for step; the tests prove it on the bot's runs. The viewer that watches one is phase 7's.
  The window is seven files now: 70-ui.js (the frame, the dialogs, the sheet), 71-title.js, 72-create.js,
  73-play.js, 74-fight.js, 75-bag.js, 76-camp.js, each adding to CM.UI.prototype.
  The bot plays the whole game: the safe answer at every event, strongboxes with their keys, the peddler, the
  alchemist's oils and greater potions, oils on the front line before a guardian. The simulator reports where the
  gold went and which spells the bot never used (a mechanic nobody uses is a mechanic to cut or fix); the tally
  counts both (tally.spent, tally.abilities).

The eleven finished, and the ground of a fight (the fourth big update, phase 1 - v2.2)
  The three earned callings, native: a fists icon for the Monk; the Heir's kit and the smith's work count double on
  the fists; tomes of Hexes and of Engines for any caster; the tavern's recruits may be of an earned calling; the
  advice knows an Artificer or a Necromancer hits every foe. (Pixel dolls of their own want the full Crawl set:
  pack.py --gather on the machine with it.)
  The ground of a fight (CM.TERRAIN; a line under the round counter says which): knee-deep in water (the Vaults' and
  the Drowned Town's floors, a flooded floor, high tide, the Drowned Hall) frost holds every foe it touches and fire
  does half; over a vent the heat sears the back row every round; among a lair's pillars only two foes can come at
  you at once; in a magical dark every blow, theirs and yours, may go wide.
  Formations (CM.FORMATIONS; on any hero's sheet, out of a fight): Line, as ever; Wedge - one hero at the point takes
  every blow that isn't a shot, with +2 defence, and everyone else hits for full from wherever they stand; Loose - a
  breath, a slam or a cold on everyone does half, blows do a little less, spells cost one more. Saved with the run.
  Second forms for the shallow guardians, at a third of their strength (form2 in CM.GUARDIANS): the Rat King hides in
  the heap and the swarm is the fight until it thins; the Drowned Knight floods the whole hall (water underfoot for
  the rest of the fight) and comes every other turn; the Forge-Warden's hammer breaks, its heat doubles and so does
  its fury. (An echo of a guardian has no second form.)
  Leaders with affixes of their own, for runs begun from v2.2 (CM.ELITES_MORE, generator 2 only): Shielded (warded
  every round), Mirrored (a spell on it does half, and a quarter comes back on the caster), Spectral (half of every
  blow passes through it).

Magic with decisions in it (the fourth big update, phase 2 - v2.3)
  Overcasting: every spell on the casting menu has x2 and x3 beside it - twice the cost for half again the effect,
  three times for double, and a triple cast may bite back (the caster burns a tenth of their health, one time in
  two). CM.OVERCAST; act("cast", {id, target, power}).
  Weaving (CM.WEAVES; the journal keeps them): two casters in one round make one spell. Fire Bolt and Frost are
  Steam (every foe blinded and scalded); Fireball and Lightning a Firestorm (the fire through every foe again, and
  they burn); Heal and Bless a Sanctuary (every foe held a round, the party mended); Sleep and Hex a Nightmare (every
  sleeping foe torn by its dream); two Magic Missiles a Barrage; Thorns and Entangle a Bramble (every foe held two
  rounds). The first holds, the second matches, either order; the Weaver achievement.
  Reagents (CM.REAGENTS): the alchemist's ingredients have a second use, one with a spell, from the pack - a spore
  cap with Sleep lasts the fight, crystal dust splits a Magic Missile onto a second foe, grave salt with Turn Undead
  routs them all, soot or slag puts half again into fire, weed into Frost holds every foe, bone dust doubles a Smite,
  grave moss puts half again into a mending, root sap doubles the party's mending from Thorns or Regrowth. The
  casting menu shows "+ reagent" when one is in the pack.
  Spell levels: a tome of a spell the reader already knows is not refused - it raises the spell a level (a quarter
  more, one less to cast), to three (CM.SPELL_LEVELS). The sheet lists the spells deepened.
  Familiars (CM.FAMILIARS): at level 6 a Mage's sheet offers a cat (finds a hidden door beside you as you pass), an
  owl (sees in a magical dark) or a toad (eats one ailment off the party on every new floor); a Necromancer's skull
  comes by itself and bites a foe at the start of every round.

The surface (the fourth big update, phase 3 - v2.4)
  Renown. Every run brings some home - its floors (to fifty), five a guardian, fifty for the crown, a hundred for the
  bottom, twenty a title earned, thirty on the week's seed; half again on Grim, a little less on Gentle (CM.renownFor;
  the ending says). Renown never buys a blow in the dungeon.
  The Village (the title's button): four buildings, four levels each, bought with renown (CM.VILLAGE, 65-village.js):
    The Guildhall       a hero who comes home may retire at the run's end as a trainer (one a calling, one a run): every
                        new hero of that calling sets out with the trainer's first boon. Level 2: the vault holds three;
                        3: the tavern's third recruit is someone the party rescued in a run before; 4: the vault holds five.
    The Merchant's House  the camps' merchant stocks Greater Healing Potions; 2: an oil of each kind; 3: one rare
                        thing a camp; 4: everything a fifth cheaper.
    The Library         scholarship: every kind fully learned (met and slain three times, a weakness found) takes 1%
                        more from every blow, then 2%, then 3%; 4: the library knows every kind's weakness the moment it
                        is met.
    The Shrine of the Fallen  light a candle for a hero on the memorial (10 renown; 5 at level 2): what they were
                        buried with - the better of their weapon and armour - comes up to the vault; 3: the memorial
                        keeps sixty names; 4: a hero remembered may come back to the tavern as a recruit, once, free.
  Contracts: three a week from the week's seed (CM.CONTRACTS), checked at a run's end, renown each: steel alone (the
  Forge-Warden with no healer), the grim dozen, the alchemist's errand, no time to lose, dry, unbroken, the hoard, old
  friends deep down, three weaves, empty hands.
  The vault is slots now (game.vaults; an old single vault carries over): leave more than it holds and the oldest
  comes back to the pack.

The difficulty ladder (the fourth big update, phase 5 - v2.5)
  Hard, between Fair and Grim: monsters a sixth tougher and a little harder-hitting. On Grim the Lich King's deathly
  cold comes every third turn, not every second: a wall with a door in it.
  Ascension. Slay the Lich King on Fair or above and the next run may carry one rule more; each crown opens the next
  rung, to fifteen (CM.ASCENSION; the creation screen's Ascension select; the run's start and its Hall of Fame row
  name the rung): Lean camps (a bedroll costs 40), Dry fountains (half are dry), Hardened (+5% health), Leaders
  (every band from the third floor down has one), Hungry dark (torches half again as fast), Costly temple (prices
  doubled), Poor veins (a fifth less gold), Deeper hurts (poison bites double), No greater potions, Watchful (the
  party never has the drop on them), Keen blades (+10% attack), No mercy (the guardians' second forms from the first
  blow), Thick skins (+10% health again), The king's guard (the Lich King begins with two skeletons up), Ironbound
  (a fallen hero rises only at the temple). A run code carries the rung (:A7). The Ascended achievement at rung 5.
  Iron: a run saved only at the camps (and at the top of the stair) - a closed window between them loses the floors
  since. The Hall of Fame marks it; the Iron Will achievement for a crown on Iron. A run code carries it (:A0i).
  The simulator's ladder report: node tools/sim.js --difficulty fair --ascension 0,5,10,15 runs each rung and reports
  survival by it, so each rung is a measured step and not a cliff.

The dungeon, branched (the fourth big update, phase 4 - v2.6; generator 2, so runs begun from v2.1)
  Wings. One floor a band has a second stair, narrower, into a short floor of the band's own (CM.WINGS): the Sewers
  under the Catacombs, the Cistern, the Mines, the Crypts, the Drowned Market, the Spore Cellars, the Crystal Seam,
  the Slag Pits, the Charnel Pit, the Root Cellar - a smell at the top of the stair says which. A wing has its own
  hazard, chests a third richer, no people and no way on but its last stair, which comes out on the main stair a
  floor below; the wing stair goes back up. Floors are numbered beside their floor (7.5) and saved like any.
  Secret stairs. Once a band, a wall beside a corridor hides a stair (search it: Space before the wall) to a hidden
  floor, richer still - the Sexton's Cellar, the Dwarves' Vault, the Lich King's Wine Cellar, the Dreamer's Bed...:
  one band of monsters, every chest two and a half times the gold and a rare thing in each. Two achievements.
  New set pieces, through the planner (CM.TEMPLATES2): a Great Hall with pillars and a band that waits, a Drowned
  Chapel, a Charnel Pit of pits and dark, a Crystal Gallery behind a secret door. Generator 1's floors are untouched.
  The dungeon changes behind you: every hundred and fifty steps, now and then, a door you left shut on a floor
  above swings open - or, once a run, a peddler sets up by a fountain there. The log says so.
  Awakened. Once the bottom has been reached, the creation screen's Expedition offers an Awakened run on any seed:
  every floor is the mirror of itself (CM.mirrorFloor), the monsters a band deeper (CM.AWAKENED), the uniques awake
  (a second power in each: ", Awake"). The Hall of Fame marks it; the Awakened achievement for its crown. The tenth
  band under the Root is left for a later version: a band is a band's worth of art and lore.

Expanded systems in play (the fourth big update, phase 6 - v2.7)
  Morale: the party's temper, from 0 to 100, said as a word under the automap (CM.MORALE: Broken, Shaken, Uneasy,
  Steady, High). High, blows land a little more often; Shaken or Broken, a hero may freeze a turn. A victory lifts it
  (a guardian's more), a bond, the camp fire, a Bard's song, a chest; a hero falling, a flight, a curse and hunger
  wear it down. Saved with the run.
  Two slots more: boots (speed in the fight's order; some are silent - the party is never surprised - or keep dry feet
  in the water) and cloaks (warding; some hooded against the dark's surprises). Generator 2's chests hold them. The
  sheet has the slots.
  Quirks at creation (CM.QUIRKS; a select under each hero's calling): Nightsighted, Greedy, Pious, Stubborn, Lucky,
  Sickly, Hardy, Quiet - a small, honest trade-off each, carried in run codes. The week's party has none.
  Hunger, lightly (CM.HUNGER): three hundred steps without a ration and the party is hungry (morale wears), six
  hundred and Weary (every blow does less). Rations: the merchant sells them, the alchemist makes three of moss, weed
  or sap; the camp fire feeds everyone; any hero eats from the pack for all. No one starves.
  A second calling: with a guildhall of the second level, a hero at level twenty takes a second calling at a camp
  (Guild, at the camp) for 200 renown: its first two spells or skills are theirs for good, and a little magic with
  them if the calling casts. The sheet names it.
  The ladder, measured (10 seeds, Fair, the bot): A0 and A5 much alike (half the parties take the crown), A10 a wall at
  the Lich King - so the rungs were reordered: the costly temple and deeper hurts come before keen blades and the
  guardians' second forms, which now sit at 11 and 12.

Replays, ghosts and the film of a run (the fourth big update, phase 7 - v2.8)
  Films. Every run's end keeps its film - the seed, the party, the rung and the log - the last six (CM.store "films").
  Films, on the title, lists them: Watch plays one in the real view, on the game itself - the walk, the fights, the
  choices - with a bar over the view: Pause, 1x / 4x / 16x, Next fight, Next floor, Stop (Esc; Space pauses). Nothing
  of a film is saved; the player's own runs are where they were when it stops. A Hall of Fame entry's details offer
  Watch the film while the film is kept.
  Share a run as a film code: CM2: and the run (Copy the code, in Films; the summary card carries it too). Paste one
  into Films and Watch plays anyone's run - the same dungeon, the same dice, the same choices (CM.filmCode,
  CM.parseFilm; the log packed, a character a step).
  Racing a ghost: a run leaves a trail - each floor and the step it was first set foot on - in its Hall of Fame entry.
  A later run on the same seed hears, at every stair, when the best run on that seed took it, and whether it is ahead
  or behind. The weekly's seed is everyone's, so the week's board is a race.
  Clips: Record a clip, in the pause menu, saves ten seconds of the view as a .webm, where the browser can (the
  canvas's stream and MediaRecorder).

Sound and sight, again (the fourth big update, phase 8 - v2.9)
  Two frames more for every monster of the Drawn theme, painted in code from the same picture under a different hand
  (CM.art.monster(m, big, pose)): the weight on the other foot as it breathes, and a lean-in as it strikes. The Pixel
  theme's tiles stand still, as tiles do.
  The battle tune in layers, by danger (CM.music.setDanger): drums and the pad while the party is whole, the lead
  joins when someone is under half, the pad drops out when a hero has fallen; a guardian's second form shifts the
  tune up three semitones (CM.music.shift) until the fight ends.
  Barks (CM.audio.bark): a monster's call, short and high when it is struck, low and slow when it dies.
  A camera pass (40-render.js: zoomTo, rollTo): a push-in when a guardian telegraphs its move, a pull-back on the
  crown, a slow tilt on the ending when the party has fallen. Not with Reduce motion on.
  Lit stone is deferred again: ambientCG's normal and roughness maps are not in src/art (pack.py --gather on the
  machine with the full sets is the first step).
  The ladder, measured again at ten seeds a rung (Fair): too few seeds to rank the middle rungs - the dice of every
  run change with any rule, and five crowns against three is noise - but Ascension 15 is plainly the hardest (one
  crown in ten). Thirty seeds a rung is the number to decide by; node tools/sim.js --seeds 30 --ascension 0,5,10,15.

Around the game, again (the fourth big update, phase 9 - v3.0)
  Install as an app: build.py writes manifest.webmanifest, sw.js and icon.svg beside the game's file. Served by any
  web server (python -m http.server in game\ will do), the page offers Install on the title's foot; installed, it
  opens from its own icon and plays without the network (the worker keeps the file). Opened from disk nothing of
  this is asked for; the file alone is still the whole game.
  A save as a link (Export / Import > Link; Films > Link): the export deflated and written after #save= (a film
  after #film=), stored nowhere but in the link. Opening such a link asks before importing or watching
  (CM.toLink, CM.fromLink, CM.linkPayload).
  The gamepad, remappable (Keys > Gamepad): every button but the d-pad and the stick can be set, the way the keys
  are (settings.pad, CM.DEFAULT_PAD, CM.PAD_ACTIONS); Swap A and B still works on top. A handheld layout (Settings;
  Auto picks it on a Steam Deck's shape, 1280 by 800 with a touch screen): thumb-sized buttons and larger text.
  Statistics (the title's foot): every expedition that ended is one short line in a ledger (CM.ledgerLine, up to
  600; the runs from before are read back from the Hall of Fame, without their numbers) and CM.statistics sums
  them - where parties fell by band, the callings and how they fared, gold and where it went, by difficulty. The
  ledger rides in Export / Import and merges without doubling.
  Text as data, begun: 12-text.js holds CM.TEXT and CM.t(key, vars); the new screens are written through it. The
  older strings move as they are touched; no translation is shipped.

The spine of the story (the fifth big update, phase 0 - v3.1)
  LORE.md is the canon: the timeline of Caer Duin, its people, the lies the upper carvings tell and where the
  truth is cut. 13-lore.js holds every line of story keyed and in chapters (CM.LORE_TEXT, CM.CHAPTERS); the old
  arrays are views over it, so the generators and the riddles read what they read. Each of the fifty carvings has
  two tellings - the same fact in another hand - and a seed picks one (CM.telling). A run keeps what it has read by
  key (game.story, saved; an older save is read back from its journal), and the journal's second page is the codex:
  chapter by chapter, the unread as blank lines, a lie struck through once the deeper line that corrects it is read.
  The bot reads the walls it passes. Reading every band's chapter in one run is the Chronicler.

The people of Caer Duin (the fifth big update, phase 1 - v3.2)
  Twelve ghosts (CM.PEOPLE: the six, and Marguerite the fishwife, Brokk who wrote GO ROUND, Hesta of the forges,
  Lady Maren who still sits, Master Hollis the physician, Orrin Vale who was not from the east), each met three
  times going down - a word, a word more, and at the third a request: bones, vengeance, a story read to them, the
  bell (dropped on the fourth floor; Brother Cael rings it on the forty-first, and something far below moves), or a
  witness (read the deeper wall that concerns them and come back). Met in an earlier run, they remember. Placed by
  hash on their floors (never a guardian's), last in CM.furnish so nothing older moves.
  Your own dead: on a seed where a party of yours fell, the hero with the most levels stands over the remains, says
  one of a dozen lines, and wants their bones; laid to rest, a candle burns for them at the shrine for nothing.
  The hermit tells a chapter back once all but one of its lines is read - the epigraph, then the truth under it
  (CM.CHAPTER_TRUTH) - and the codex counts the chapter whole; with nothing to name, he points at the unread wall.
  The lost adventurer may be a hero of yours who fell shallower on any seed, found alive after all (the name only).
  Talk dialogs can run to a second line (More). Titles: Bell-ringer, the Witness, the Faithful.

The guardians speak (the fifth big update, phase 2 - v3.3)
  Every guardian speaks first at the door of its lair (CM.PARLEY): Fight; Speak - three exchanges, two answers each,
  and the fight comes on the party's terms (all three right: its company goes and it is shaken; none: enraged); or,
  when the party holds what it wants, a way through without a blow - rations for the Rat King, the dwarves' word
  for the Forge-Warden, Marguerite's testimony for the Queen, the dwarf's warning for the Mind, GO ROUND for the
  Tyrant, Hesta's name for the Forge Master, a holy thing for the Patriarch, and for the Drowned Knight the truth
  from the town below him (a return). The Root wants nothing you have, yet. Passed by speech a guardian is not
  slain: no trophy, no experience, half the gold, but its relic is left behind and the shaft is open; three of them
  make the Soft-Spoken, and renown counts them. A death speech each, another if it was spoken to. The lair after:
  the water drains, the embers go out, and its carving speaks in the past tense (ga:<id>). Every word is logged
  (game.parley), so films carry the talk. The bot takes an open gate, else it fights. game.mapAll is a second
  logged cheat for the tests, beside warp.

The court of the Lich King (the fifth big update, phase 3 - v3.4)
  The seated dead of floors 16-19 (CM.COURT: the Chancellor, the Master Mason, the Captain's Widow, a Lady-in-
  Waiting, the Physician's Body) speak when stood before; each is a line of the Palace's chapter. The heart hunt:
  the Chancellor's word, the wall on the eighteenth floor and the physician's page (in one of the palace's chests;
  read it from the pack) together mark the phylactery on the map of the floor above the throne room before it is
  seen (CM.HEART_CLUES).
  The quiet ending: with the Palace's five carvings read and the heart smashed, the king's door offers Remind him -
  five things he has forgotten (CM.REMIND: her name, the bells, the twelfth year, the box, the heart), each wanting
  a line the party has read; any gap and he draws. All five, and Mordeth sets the crown down himself: crowned
  without a blow, the Merciful, and the Deep still open below (entry.reminded; the ending and the summary say so).

The village has people (the fifth big update, phase 5 - v3.5)
  Three villagers (CM.VILLAGERS), each in a building once it stands: Wren the chronicler at the library shows the
  codex, pays renown at a run's end for every chapter completed - twenty, forty for the Deep's, once each - and
  sells rumours (CM.RUMOURS, 15 renown) that bind to the next seed begun and that CM.furnish keeps: a ghost who
  wants its bones, a hermit, the other telling of a floor's carving. Father Osric at the shrine says three names
  of the memorial a visit, with their epitaphs, and tells the Patriarch's history in five parts as the shrine is
  built. Dunmore the keeper's trainers say how they came home, one line a calling.
  The Book of Caer Duin (CM.chronicle): every crowned party of this browser's as a chronicle entry, in the
  carvings' voice; and the dungeon writes it back - near the surface, a legend of one of your own parties, carved
  in a newer hand (CM.legends). The village's own chapter of the codex opens a line at a time as renown is spent.

Heroes with pasts (the fifth big update, phase 6 - v3.6)
  Six origins at creation (CM.ORIGINS): of Caer Duin (the Catacombs' first line known at the stair), dwarf-friend
  (a dwarves' mark read gives the way down too), from the east (twenty gold), of the Patriarch's order (no curse
  takes hold), of the lower town (the party wades dry-shod), nobody from nowhere (+1 Luck). Each speaks at the
  walls that concern it, once a run, and the word goes in the journal (game.originLines).
  Banter by situation (CM.BANTER2, forty lines: the camp, after a guardian, at a carving, on a flooded floor, with
  a hero down), for the bonded pair or two who stand, never in a fight; a long bond's running joke (CM.JOKES).
  Last words (CM.lastWords: by origin, by calling, by the band) for every hero laid to rest when the party falls -
  they all are, now, so the memorial and your own dead agree; an epitaph (the shrine, sixty characters) that the
  priest and the hero's ghost repeat. A trainer's word to every new hero of their calling at the stair.

The telling (the fifth big update, phase 7 - v3.7)
  A wall read opens a reading view: the carving large, in the hand that cut it (CM.handOf: a chisel, dwarf runes,
  a child's chalk, a priest's small capitals, a scratch - four hands and the plain one, as CSS), a word at a time
  at reading speed; Space shows it all; Reduce motion (or instant combat speed) shows it at once. Chapter cards:
  the band's epigraph on its first floor, and on its last a word that the walls below will differ. The camp fire
  tells the day: at a rest one hero tells a wall read this band and another answers (game.campTale). The ending as
  a page: the chapters the party completed are its paragraphs, the rest blank lines, under the ending's text,
  and Save the page (PNG) draws it (CM.endingPage). Three leitmotifs in code (CM.music.motif): the bell, the
  queen's song, the Root's one note, played when a line that concerns them is read or heard (CM.MOTIFS).

Around the story (the fifth big update, phase 8 - v3.8)
  The Scholar's kit (floor 8 reached): the Catacombs' chapter known at the stair and a tome in the pack. Four
  contracts with story in them (the bell on Grim, the Drowned Knight passed by speech, one of your own laid to
  rest, three chapters in a run). The titles of the update, together: the Chronicler, the Soft-Spoken, the
  Merciful, the Witness, Bell-ringer, the Faithful. node tools/sim.js --story reports lines read a run, chapters
  completed, guardians spoken past, the bell rung and the king reminded, by difficulty; node tools/words.js prints
  the story's budget by chapter and counts the long strings still in the code. The film bar names the scene
  (a parley, a word with someone, a choice).
  Measured (six seeds, Fair, to floor 25, --story): the bot reads about fifty lines a run, completes the Catacombs
  and the Vaults every time and the Halls most times, and passes the Forge-Warden by the dwarves' word in five of
  six runs - the gates are open to a party that reads, as meant; it never rings the bell (it does not carry one
  thing forty floors for a ghost), so that gate is a player's.

The Root, and the three endings (the fifth big update, phase 4 - v4.0)
  Below the Ossuary the carvings are the Root's own voice, and it knows the party: a line is added to each from the
  names, the dead, the origins and the ledger (CM.rootAddress; the journal keeps the wall's own words). An
  Awakened party hears one thing more.
  Three endings at the bottom. The Root beaten, the party chooses (logged: game.ending): wake it and end it - what
  always happened; or leave it to dream - the village prospers (100 renown, the merchants a fifth cheaper for
  good), the codex gains a chapter (The dream, again), and the king is on his throne when the next party comes:
  this is what Awakened was, named and chosen. The third is at the Root's door, not after a fight: with the crown,
  the Root's five carvings read and the Merciful earned on some run before, give it the crown - and the Other
  Dream opens. The Hall of Fame marks all three as the bottom (entry.left, entry.dreamed); the titles are the
  Forbearing and the Dreamer; a window closed over the beaten Root asks again when the run is continued.
  The Other Dream (a mode, once the Dreamer is earned): the same seed and the same floors, not mirrored, with the
  Awakened numbers - and the walls say what Caer Duin might have been (CM.DREAM: fifty lines, ten band names, the
  guardians as they were in life: Captain Aldred, Queen Aelith, the First Father), in warmer stone.

The ledger of things (the sixth big update, phase 0 - v4.1)
  14-items.js: every base a thing can be, by id (CM.BASES - the old lists' names, which were already ids), and a
  name derived from what a thing is made of (CM.itemName: prefix, element, base, suffix, plus; the smith's work
  keeps the affix words now). Saves are schema 3: every item carries its base and where it was found
  (item.found: the floor and how - a chest, a slain foe, a strongbox, a ghost, the vault, the merchant...), and
  the bag's card says so (CM.itemCard). The journal's third page is the compendium: every kind of thing, by group,
  the unseen as outlines; an unknown thing counts once it is named; all of them is the Collector. The bag has
  filters (All, Gear, Drink, Read, Stuff). The game's own Auto - and so the bot - uses the pack in a fight: a
  firepot or a scroll of fire on a crowd, a wand of fire on a leader, a wand of sleep on three; the bot equips the
  better thing as it is found. node tools/sim.js --loot reports gold found and spent, things by rarity, what was
  used and the floors to the first upgrade of each slot. Measured (four seeds, Fair, to floor 20): about 60,000
  gold found a run and 9,000 spent; 260 common things found, 15 fine, 3 rare; the first better weapon by floor 2,
  armour by 4, a shield by 12; wands and scrolls now used in every run. The numbers Phase 8 will be judged against.

Weapons and armour with character (the sixth big update, phase 1 - v4.2)
  Every weapon has a class with one rule (CM.WEAPON_CLASSES, read in strike): blades a sixth more against flesh;
  blunt arms ignore a third of bone, shell, plate and the undead's defence and never find a weak spot; axes cleave
  into a second foe of the row for half, and bite hide; polearms strike at full from the back row and are cramped
  in the front; daggers are two steps quicker, find weak spots a tenth more and strike them for three times, at
  two thirds of a blow; staves are half a blow and +1 to every spell (one more every four tiers); bows and fists as
  they were. Eleven arms more (a Stiletto, a Spear, a Maul, a Halberd...) come up a third of the time, by the
  draws the generators already made, so no floor moved. Every calling is at home with two or three classes
  (CM.ARMS_AT_HOME; a second calling adds its own) and clumsy with the rest: blows land 15% less often and the
  class's trick is lost; the bag says so. Shields block (CM.blockChance: 8% a buckler to 38% mithril) for half,
  and a tower shield in the front row takes some of the back row's blows. Heavy armour is a step late in the
  round and loud (surprised 65% not 50%); light a step early; mithril plate neither. The Rogue and the Ranger may
  put a second dagger in the off hand (the bag's "or the other hand"): another blow at half, every blow. Every
  monster is made of something (CM.HIDE: flesh, hide, bone, shell, plate, none) that the rules read.
  Measured on twenty seeds, Fair, to floor 25, v4.1 against v4.2 side by side: 18 crowns against 19 - within the
  five points the plan allows before Phase 9 tunes on purpose (six seeds swung from two to six crowns between
  tweaks: the reseeded dice make six seeds noise). The flesh and hide bonuses were trimmed from a quarter to a
  sixth on the way.

Affixes that grow, sets, curses, and the smith's second trade (the sixth big update, phase 2 - v4.3)
  Every affix has three tiers (CM.affixTier: I from floor 3, II from 16, III from 31): the word stays, the number
  grows by half and then double (CM.scaledAffix; item.props.tier). Seventeen words more: on a hit (Bleeding,
  Chilling, Blinding), on a kill (of Plunder, of the Leech, of the Font), by the foe (Undead-bane, Hunting,
  Desperate), for the party (of the Hearth, Sheltering: +1 defence to everyone while worn; of the Lantern: every
  third step free of the torch), and the small ones (Sure, Weighted, Steadfast, Fleet, of Haste, of Stone, of the
  Scholar). Implicits (CM.IMPLICITS): a base's own small property before any word - a Dagger's edge, a Buckler's
  quickness, the Dragon Scale's proof against fire; older things learn theirs when they are named. Cursed gear is
  a fourth rarity: hidden among the unknown, a tier-III word and a cost (CM.CURSES: hungering, dark, weakening,
  haunted) that will not come off until the temple lifts it - the cost goes, the word stays. Three sets of three
  (CM.SETS: the Watch's, the Masons', the Order's), dropped in their bands by hash, fine alone and a rule together.
  The smith's second trade: a prefix moved from a worded thing in the pack to the worn one (150 gold; the pack's
  thing is scrap), and essence from the fire (salvage: one from a fine thing, two from a rare or a cursed one;
  three essence stand in for a gem at the rework). Enchantment stays at +3; a tier-III word is the ceiling.

The belt, and things to drink, read and throw (the sixth big update, phase 3 - v4.4)
  The belt: four slots under the automap (keys 5 to 8; the bag's "To the belt"), and in a fight the first thing
  used from it in a round costs no turn (game.toBelt, useBelt; act("item", {belt})). Flasks, thrown from any row
  (CM.FLASKS): oil (fire on a foe and the one behind; on water it spreads to every foe for half), acid (three off
  a foe's defence), holy water (the undead burn, some cower), smoke (away, for certain) - brewed by the alchemist,
  sold at the camps. Potions by depth (CM.healPotion: lesser, healing, greater, full; mana likewise) and a Lesser
  Phoenix Feather (half health, once a floor), so the full one is a decision. Elixirs with a time to them
  (CM.ELIXIRS): stoneskin (three off every blow, the floor), haste (first in every round of the next fight), owl's
  eyes (no dark, three floors), the night's draught (no sleep, no surprise, the floor). Six scrolls more: recall
  (to the last camp, and back to the square by the same scroll), knowledge (the floor's carving from here),
  banishing (a called thing sent back), sharpening (+2 for the floor), silence (no spell, no breath, the fight),
  the lost page (fire, frost or lightning on every foe, once). Wands are spent, not crumbled, on their last charge
  (one in four breaks; never with an Artificer standing) and the smith charges them (a gem and 60 gold for three).
  Light as a thing: the lantern wants oil (CM.LANTERN_OIL steps, burned one in two; lamp oil from the merchant,
  poured by hand or from the pack as it gutters; an older save's lantern gets a flask), and glow stones from the
  Crystal Caverns' chests never go out and do not reach far.

Gathering, the field kit and the kitchen (the sixth big update, phase 4 - v4.5)
  Gathering nodes (CM.NODES: a moss bed, a weed pool, a vein of ore, a fungus shelf, a crystal growth, a bone pile,
  a root knot...), two or three on every ordinary floor by hash - placed last of all in CM.furnish, so no older
  hash's cell moves - give the band's ingredient and, one time in five, its rarer one (ten rarer things:
  CM.INGREDIENTS with rare: a grave lily, a cave pearl, silver vein, ghost cap, prism dust, foundry gold, a saint's
  bone, heartwood...). The Druid and the Ranger take two; the Artificer two of ore. The field kit (the merchant's,
  from the third camp, or the bag's own button) brews anywhere at a fifth over the camp's price. Twenty-two
  recipes now: salve (the party mends as it walks, the floor), dwarven bread (a ration that mends twenty),
  liniment (a wound closed, the small ailments with it), blade poison (a weapon's wounds fester, three fights),
  transmutation (three of one band's ingredient into one of the band below's). The kitchen: the kinds that have
  meat drop it (CM.MEALS); cooked at a camp, or on the floor for a torch, a meal feeds the party and lasts the next
  floor (+1 attack, +1 defence, the torch slower, mending in fights, +1 Luck). The alchemist asks for three of the
  band's ingredient at every camp: bring them, and the next brew is free. The bot gathers what it passes.

Living items: charged relics, trinkets, and weapons that grow (the sixth big update, phase 5 - v4.6)
  Every guardian's relic, and First Root, has a power spent once a floor (CM.RELIC_POWERS, CM.powerOf): the Rat
  King's Crown calls the swarm for you; the Shield of the Drowned floods the hall and chills every foe; the
  Forge-Warden's Hammer halves the chosen foe's defence; the Queen's Ring puts half the room to sleep; the Sporecap
  Helm holds a foe two turns; the Prism Amulet halves the next blow on each hero; Ember Mail reforges the wearer's
  weapon (+2, the floor); the Patriarch's Reliquary opens the nearest lock on the floor; First Root regrows a fallen
  hero to one health. In a fight it is the Relic button (L), on the floor the hero's sheet; a film replays it.
  A ninth slot, the trinket (CM.TRINKETS: twenty, one passive oddity each): a rat's tooth (never ambushed by rats),
  the bell's tongue (the last bell's note when a guardian gathers itself), a cook's spoon, Tamsin's tally stick,
  a child's chalk (the floor's carving on the map as you arrive), a lodestone (the way down), a dowsing twig (the
  gathering), knucklebones, a cracked hourglass, a mirror shard, a thimble (a chest's trap never springs on the
  wearer), a whetstone, a lucky bootlace, an ember stone, a cold coin, a sewing kit, a steady-hand charm, a hearth
  stone, a long wick, a hawk's eye. Found in strongboxes (two in five), from grateful ghosts, and on the peddler's
  cloth. (A flag on worn gear now counts as one through CM.gearProp, so the oddities are read everywhere.)
  Weapons that grow: the weapon that struck a foe last remembers it (lastWeapon); a hundred slain is a mark, a
  guardian slain is a mark (+1 to the weapon and a line of history); at three marks the sheet offers a name
  (nameWeapon, 24 letters). A named weapon is the name everywhere (CM.itemName), is kept in the compendium's Named
  list with its story, takes no slot in the vault and is never the thing the merchant hands back, and may be found
  again by a later party of this browser: on floors 4 and below, one chest in eight carries a named weapon of the
  compendium made again (CM.legendWeapon: its base, its marks, its story so far, and a line about who lost it).
  Heirlooms with memory: a thing taken from the vault remembers its bearers; the third wears it as a relic
  (props.heirloom), and CM.relicsWorn counts it for the relic set.
  Test: "living items" - every power once a floor and not twice, the swarm bites all, the hammer halves one, the
  prism halves the next blow, the reliquary opens the nearest lock, the root regrows; the chalk and the lodestone
  mark the map on arrival; the hundredth kill and the Rat King mark a sword, its third mark names it, and the name
  survives save, the vault's one slot, and turns up in a later seed's chest with its story; a ring's third bearer.

Tools, traps, locks and doors (the sixth big update, phase 6 - v4.7)
  Locks have grades (CM.LOCKS, by the seed and the door: common above floor 6; iron two in five below; dwarven one
  in four from the palace down). A key opens any; a Rogue picks a lock of her level (2 for common, 4 for iron); a
  Lockpick lets anyone try at a third of the Rogue's chance, and breaks on a miss; a Master Pick tries at the full
  chance and is the only pick for a dwarven lock; the Patriarch's Reliquary or the Forge-Warden's Hammer, worn,
  opens anything (CM.OPENS_ANYTHING). A strongbox without its key is picked the same way (tryLock). The merchant
  sells two picks a camp, a master pick from depth 14.
  Traps as tools: six traps now (a volley of darts, a floor that gives way). A Trap Kit (the Artificer starts with
  one; the merchant sells one from depth 7) takes a found plate apart for its parts - the Artificer never fails, a
  Rogue or a steady hand may, and a failure springs it - and Trap Parts are set on the square behind the party; a
  band of monsters that walks onto a set plate takes the trap (trapGroup: darts a quarter of each, gas a fifth,
  the blade half of the first, the needle bleeding, the alarm makes them hunters, the floor takes them down a level;
  a band finished by a trap is a kill).
  A Door Bar (merchant, and one chest in ten from floor 3) shuts and holds the open door beside the party for the
  floor; walking into it lifts the bar. Used again at a barred door the party rests there: a third of the camp's
  rest, once a floor, for a ration. With the Hordes mutator a band beside a barred door breaks it in three turns.
  Bait (a ration, dropped where the party stands) draws the nearest wanderers for ten steps instead of the party;
  a band that reaches it stops to eat for ten steps; Poisoned Bait (a new recipe: a ration, a ghost cap or spore
  cap, 10 gold) takes two fifths of each and leaves them bleeding. Bait goes stale after ten steps.
  A Grapnel (kept; merchant from depth 6) climbs the party back up the pit it fell down, to the floor and square it
  fell from (fellFrom, saved). A Dwarven Pick (in the dwarves' halls' chests, one floor in three) opens the nearest
  hidden door or stair on the floor without searching, and breaks.
  The bot: walks through locks with a pick in the pack, sets a trap when it has parts and a kit, disarms a found
  plate, and bars a door and rests at it when the party is worn; playRun returns what it did (tools).
  Test: "tools, traps, locks and doors".

Monsters' things, and six elements (the sixth big update, phase 7 - v4.8)
  Six elements: fire, frost, holiness, and now storm, venom and shadow (CM.ELEMENTS, CM.ELEMENT_NAMES), on gear
  (Storm, Venomed, Shadowed prefixes), on oils (Oil of Storms, of Venom, of Shadow) and on every kind: CM.ELEMENT_MORE
  lays venom and shadow over CM.MONSTER_SHAPES' table, and CM.elementMatrix() reads the whole thing out. The undead
  shrug venom off and fear holiness; the fleshy fear venom; the things of the dark shrug shadow. Storm leaps to a
  second foe for half when the party fights in water; venom is the poison with teeth (the number, and a four-round
  bleed); shadow blinds one time in three, and is the Necromancer's (Drain and Death Pact carry it).
  Loadouts: an elite leader and a rival's people come armed (CM.LOADOUTS, CM.armMonster - by a hash of the monster,
  so no dice of the floor's move): the fight says what they carry, and reads it - a maul cares little for armour,
  an axe bites one time in seven, a knife finds a gap, a spear reaches the back row, a shield takes one blow in
  four for half - and what they carried drops when they fall: the first loot seen before it is won.
  Parts that break (CM.PARTS): a dozen kinds and the Lich King carry a part with its own health (a share of the
  whole: the Troll's arm, the Wyvern's wing, the Golem's arm, the Priest's staff, the King's staff); every blow on
  the kind wears it too; broken, the kind loses the ability named for the fight (the mending, the breath, the cold)
  and the part drops as the band's ingredient or a trinket. The fight screen shows the part's health.
  Eight monster abilities: shieldwall (Skeletons: two or more in front and their back row can't be reached), howl
  (the party's morale falls six), web (a blow that holds), burrow (under the floor every third turn, up hard),
  mimic (a chest that isn't: one chest in twelve on generator 2's floors from 4 down, with the hoard in it),
  carryoff (a hero dragged into the front row until the fight ends) - with thief and splitter from the Deep making
  the eight. Four new elite kinds carry the new ones (Howling, Web-spinning, Burrowing, Dragging).
  Test: "monsters' things, and six elements".

Wounds, weight and the economy (the sixth big update, phase 8 - v4.9)
  Wounds: a hero who falls and rises (a feather, the lesser feather, the temple, First Root) carries a wound - one
  stat down by one (CM.heroStat reads it) until the temple's new service (40 gold a hero) or a liniment; a second
  wound before the first heals is a grave wound (two stats). The third wound healed leaves a scar (CM.SCARS): a
  limp (leading, never trips a plate one time in two), a burned hand (fire does half), a hard head (shrugs a stun
  or a sleep one time in two), a thick skin (+1 defence). The memorial keeps the scars.
  Weight: the pack has a weight (CM.weightOf: heavy armour 8, a two-hander 5, a shield 4, potions nothing) against
  the party's strength summed (CM.carryCap). Over the line the torch burns and hunger comes half again as fast and
  the HUD says Heavy-laden; half again over it there is no travel (Overloaded). The Bag of Holding, a unique in a
  palace chest by the seed, worn in the trinket slot, doubles the line. The bag screen shows weight against the line.
  The economy: prices climb a tenth a band (CM.priceAt); the merchant's stock rotates - a third of the things
  beyond the staples are not on the table at a given camp, by the seed; orders (a thing from CM.ORDERABLE paid now
  at a tenth over, delivered at the next camp, saved); insurance (a tenth of a thing's value, for a bag row or a
  hero's worn thing: if the party falls, it goes to the vault for the next - payInsurance); a bounty board at every
  camp (three of the band's kind, 60 gold + 40 a floor, and a renown for the village; counted against the bestiary);
  the fence at the tavern (buys unknowns at half, takes cursed things for nothing, sells a rumour of the next
  strongbox within six floors for 30 gold - it is marked on the map on arrival); a tithe at the temple (a tenth of
  the purse: +1 defence and blows land a twentieth surer for five floors). The sim's --loot report shows the spread:
  with the bot, the merchant's share of spending fell from 92% to 62-69% (tithe 16-22%, alchemist 8%, insurance 6%).
  The bot closes wounds, takes and claims bounties, tithes, insures its best worn things, orders what the stock
  lacks, sells heavy things when over the line, and fences unknowns and curses.
  Test: "wounds, weight and the economy".

Around the things (the sixth big update, phase 9 - v5.0)
  The balance pass, with the bot (node tools/sim.js --seeds 20 --to 20 --difficulty <d> --loot), twenty seeds a
  difficulty to floor 20:
    Gentle: median floor 21, 16 of 20 crowned, 3 fell (all in the palace, 16-20)
    Fair:   median floor 21, 15 of 20 crowned, 3 fell; the merchant 66% of spending, tithe 19%, alchemist 8%,
            insurance 6%, peddler 1%; 55,500 gold found a run and 11,400 spent; wands used 44 times a run, brews
            27, rations 5, scrolls 4; the first weapon upgrade by floor 1.4, armour 1.9, helm 5.6, off hand 9.5
    Hard:   median floor 21, 15 of 20 crowned, 3 fell; merchant 63%, tithe 21%
    Grim:   median floor 21, 15 of 20 crowned, 4 fell; merchant 64%, tithe 20%
  The crown rate on Fair with the bot is 75% (it was about 90% at v4.1, before the wounds, the weight, the
  loadouts and the eight abilities): the median floor is unchanged and every fall is in the palace, so nothing
  was tuned down for v5.0; the ladder's gold rungs were re-read (costly temple now doubles the wounds' price
  too; poor veins and no greater potions stand as they were).
  The item card (CM.itemCard) is on every row that names a thing - the pack and the merchant's wares, the smith's
  and the vault's lists, the hero's sheet (hover for it) - and the chest's line carries each thing's label.
  Rarity is marked by a shape before the name as well as a colour (a diamond for fine, a star for rare, a
  four-point star for a relic, a flower for a unique, a skull for the cursed), for eyes that don't tell the greens
  from the blues. The gamepad has a belt button (LT by default: the first thing on the belt; rebind it in the
  Gamepad settings), and the belt's buttons in the HUD take a tap. The belt's use, and a flask thrown from it in
  a fight, are logged and play back in a film. The HUD's and the camps' new words (Heavy-laden, Overloaded,
  blessed, the bag's weight and gold, insurance, orders, the bounty board, the fence) go through 12-text.js, and
  tools/words.js counts the things' words too (the bases, affixes, trinkets, powers, scars, recipes, leaders and
  uniques: about two thousand words beside the story's).
  Test: "around the things". The sixth big update is complete: nine phases, v4.1 to v5.0, and 75 tests.

Automatic (v5.1)
  A toggle that plays the game for you: Z, or the Automatic button in the explore and camp menus. On, the party
  walks a step a tick (slower at the camp, so the business can be read): it opens the chests on the way, gathers,
  finds the key before the locked door and the lever before the gate, reads the walls and listens to the dead,
  answers riddles and the strangers' choices the careful way, drinks from fountains when hurt, sets traps and bars
  doors when it has them, and fights what it walks into with the fight's own Auto hand. It wears what compares
  better as it comes (every slot, the trinket too), drinks a potion under two fifths, eats when hungry, takes an
  antidote when ailing, and at the camp rests, raises and heals, brews, buys potions and torches, closes wounds,
  takes and claims bounties, tithes, insures its best worn things, orders what the stock lacks, sells heavy things
  when over the line, fences unknowns and curses, and buys a weapon upgrade with the gold left - then goes deeper.
  The HUD says "automatic" while it is on. Any move or fight key, or Z again, takes the reins back (the fight's
  Auto too). It pauses while a dialog is open (Escape), and stops by itself, saying why, when it is lost on a floor
  or when the choice is yours (the bottom of the world). Everything it does goes through the game's own logged
  acts, so a film of an automatic run plays back the same, and the run saves as any other.
  Under the hood it is CM.Autopilot (src/js/66-auto.js): the simulator's bot (tools/bot.js) is now the same class,
  driven in one loop with warping past a lost floor and the waking of the Root allowed, so the bot and the toggle
  can never drift apart. Test: "automatic".

The ground of the town (the seventh big update, phase 0 - v5.2)
  Floor 0 is the town above, Caer Duin: hand-laid in src/js/23-town.js (CM.makeTown - no generator, so nothing
  frozen moves), a nineteen-square map with a square and a well, a main lane from the party's own door at the
  west end to the shaft's mouth at the east, a north and a south lane, and nine plots on them (your house, the
  Hanged Lantern, the Merchant's House, the Smith's forge, the Alchemist's Garden, the Library, the Temple, the
  Guildhall, the Chronicler's House - CM.TOWN_PLOTS, CM.TOWN_AT). A plot is a door: walk up to it and Space opens
  the building's screen - in this phase, the plot's name, what stands there, the levels the village has raised
  and the village's own Build button; a plot the village does not raise yet is a foundation with two posts.
  The town is a floor to the engine: drawn by the renderer in its own daylight theme (CM.TOWN_THEME: limewash,
  a sky-coloured ceiling, a long reach), saved and restored as a delta like any floor, on the automap in full
  from the first step, with its own title card, compass word and arrival line. Nothing wanders it, no torch burns
  on it, no one grows hungry on it (a Rogue of the party may still pick nothing: there is nothing to pick).
  A new run begins at the party's door facing down the lane (Settings: Skip the walk puts the party at the shaft
  instead; the tests and the simulator start at the shaft, and node tools/sim.js --town starts at home). From any
  camp, Back to town climbs to the shaft's mouth; from the town the shaft goes down to the deepest camp the run has
  reached, so the town is never a trap, and to floor 1 before any camp. Saves on floor 0 continue (a run on floor
  0 was "no run" to the old save check), a film of a run that began at home begins at home, and an old film
  begins at the shaft as it did. Automatic and the bot walk the lane to the shaft and go down.
  Test: "the town above".

The home (the seventh big update, phase 1 - v5.3)
  Your house, at the west end of the main lane, is raised like any building (CM.VILLAGE.home: 50, 150, 400, 800,
  1500 renown) and opens from its door into its rooms (src/js/67-home.js; the village store keeps village.home):
  - The hearth (level 1): once a visit to the town the party rests for nothing - health, magic, the small
    ailments, hunger - and goes down rested: +5% to hit on floors 1 to 5 (buffs.rested, gone at six).
  - The stash (6 things at level 1; 12 at 2; 20 at 3; 40 at 5): the party's own storage between runs, apart
    from the camps' vault. Anything but a floor's key may be left; taking is free; nothing in it is ever bumped
    or insured, and a fallen party's pack does not come to it - only what the party walked home is there.
  - The trophy wall (level 2): the guardians' trophies, the named weapons, the uniques found, the crowns and the
    stones from the bottom of the world.
  - The kitchen (level 3): meat brought home is cooked for a meal that lasts the first two floors; the larder
    keeps three rations from run to run.
  - The door-plate (level 4): the memorial's names on the door, with their scars; a candle lit at home (the
    shrine's price) sends what they were buried with to the stash instead of the vault.
  - The study (level 5): a hero retires home (home for good, without teaching), and a will may be written: one
    thing from the stash, copied into the pack of every later run from this house (no relics or uniques).
  Everything the house does is a logged act, so a run that rested and stashed replays the same.
  Test: "the home".

The tavern, the merchant and the smith (the seventh big update, phase 2 - v5.4)
  Three doors in town open onto the camps' benches with more behind them (src/js/68-shops.js). The Hanged Lantern:
  the recruits, the fence and the rumour of a strongbox (the fence drinks in town now, not at the camps), the board
  (the camps' bounty and the week's contracts), a round for the party (5 gold: morale 90 for the road, once a
  visit) and the regular's gossip (10 gold, once a run: where the sexton's helm and the Bag of Holding lie on this
  seed). The Merchant's House: the whole stock, nothing rotated, at the party's level; orders and insurance as at
  the camps, delivered at the first camp; and at the house's third level a commission - a weapon, armour, a shield
  or a helm of any base at the party's level, affixed as the floor would, paid now at half again over, waiting at
  the first camp (CM.gearOfBase). The Smith's forge: everything the camps' smith does, and the forge's own work -
  a base reforged (a Long Sword into a Bastard Sword: every word, mark, name and history kept, for an essence and
  100 gold a tier), a second gem set in a relic (the wearer proof against its element, +1), and the apprentice who
  buys scrap at three quarters. A merchant's table belongs to where it stands: it is fresh on every floor.
  Test: "the tavern, the merchant and the smith in town".

The library, the temple and the guildhall (the seventh big update, phase 3 - v5.5)
  The village's three buildings are doors in town (src/js/69-halls.js). The Library: a reading desk with the
  journal's boards (the codex, the compendium of things, the run's journal, bestiary and combos), Wren and the
  Book of Caer Duin, the tomes - one borrowed a run for nothing, back on the shelf when the run ends, read or not -
  the shelf where every Lost Page found is copied, and at a new fifth level (1500 renown) the gazetteer: a new
  run has the first five floors' walls on its map before the party is on them (the walls, not the things). The
  Temple: the camps' temple at a tenth less (cure, a curse lifted, stone to flesh, the raising of the fallen, the
  wounds closed, the scribe), Father Osric's candles and the Patriarch's history, the tithe, and at a new fifth
  level the vigil: a hero's scar kept or let fade, once a hero. The Guildhall: Dunmore and the trainers (a hero
  retires there), the guild's letter (the second calling, read in town as at a camp), the week's contracts, and
  the roster - every party this browser set out with, kept as a preset (twelve, newest first; the same four under
  the same names are one line), each with "Set out again as them", and a muster that fills the creation screen
  with the last party that came home.
  Test: "the library, the temple and the guildhall".

The garden, the chronicler and the square (the seventh big update, phase 4 - v5.6)
  The Alchemist's Garden (CM.VILLAGE.garden: 100, 300, 700 renown): one, two, three beds - an ingredient from the
  pack planted in a bed grows one more every run that ends, up to five, and is harvested whole - the alchemist's
  brewing bench at the camp's price (no field kit's fifth in town), and at three beds the alchemist's request may
  be delivered here. The Chronicler's House (100 renown): the films, the statistics, the Hall of Fame, the ledger
  and the memorial's book under Wren's roof; the title keeps its boards too. The square: the well, with the notice
  board beside it (the week's seed, the day's, and market day), a drink when it runs (after the first crown), and
  a coin thrown for the town once a visit (1 gold, 1 renown); market day on the week's seed, a peddler's cloth in
  the square; three townsfolk on the lanes, where the seed puts them, each with a line a day from the hill's own
  story (Marget's granddaughter, the bell-founder's boy, the sexton's widow: CM.TOWNSFOLK); and the lanterns lit
  when the clock says night (CM.clockHour: the town is dimmer, and the title card says so). Everything in the
  square is a thing on the floor, so the town's fingerprint never changes and a save of it never drifts.
  Test: "the garden, the chronicler and the square".

Growth, and the town as a thing that remembers (the seventh big update, phase 5 - v5.7)
  A building is drawn by its level (CM.houseStage): a foundation with two posts, then a frame, a roofed house, a
  house with its sign, a house with a lit window - the stage is the level against the building's most, so the
  square fills in over many runs. Every building is raised at its own door (a Raise line at the foot of its screen;
  the title's village dialog still works). Nine buildings now, the tavern and the smith with levels of their own
  (a better cellar: the round fills the heart and the gossip is free; a better bench: the recruits a level higher;
  the apprentice pays scrap in full; a reforging at half), and renown re-tuned for nine: the town costs about
  3,800 renown in all (the home first at 15, the chronicler's house late at 120), and a run brings three renown for
  every door opened before the descent, up to nine. Measured with the bot: a run brings about 85 renown on average
  to floor 20 (about 110 with every door opened), so a careful player raises the whole town over some thirty-five
  runs, the first buildings in the first three or four. What the runs brought back is on the walls: the trophies
  at home, the first named weapon on the smith's sign, the best run painted on the tavern's wall, the chapters
  copied and the lost pages on the library's shelf, the names on the door. The hill's own chapter (the village's
  lore, unlocked as renown is spent) is carved on the well's stones and read there, in order.
  Test: "growth".

Around the town (the seventh big update, phase 6 - v6.0)
  Automatic in town runs the errands at their doors in a sensible order - home (the hearth, rations from the
  larder), the Merchant's House (the shopping the camps know), the Temple when someone is wounded or fallen or the
  purse is heavy (the raising, the wounds, the tithe), the Hanged Lantern when there is gold for a round (the round,
  the board) - each door opened and counted, then the shaft; node tools/sim.js --town measures a run that walks the
  town, and the bot's crown rate on Fair is the same from home as from the shaft (14 and 13 of 20, within noise).
  The gamepad walks the lanes with the stick and opens a door with Use, and every building's screen takes the pad's
  list focus like any dialog. A film of a run that began at home begins at home (spec.town). The town's words go
  through 12-text.js (the title card, the arrival and opening lines, the compass, Back to town, a foundation, a
  door), and tools/words.js counts the town's words (the plots, the townsfolk, the buildings' levels: about eight
  hundred). The balance pass: the rested buff, the gazetteer, the will and the commission are all the village's
  (a bot with no village feels none), and the sims to floor 20 on Fair hold the crown rate where v5.0 left it.
  Test: "around the town". The seventh big update is complete: seven phases, v5.2 to v6.0, and 83 tests.

The clock, the sun and the moon (the eighth big update, phase 0 - v6.1)
  The clock is the game's, not the wall's (src/js/24-clock.js): a step is a minute, a stair an hour, a round of a
  fight a minute, and a rest - the camp's or the hearth's - sleeps until the next dawn (a whole day if it is dawn
  already). A run begins at six in the morning; the hour is saved with the run and a film keeps it. CM.hourOf,
  CM.isNight (nine to five), CM.hourWord (dawn, morning, noon, afternoon, dusk, evening, night, the small hours),
  CM.dayOf, and a twenty-nine day moon (CM.moonPhase: new at the first day, full at the fifteenth; CM.moonWord).
  The HUD has a sky bar over the view's corner: the sun and the moon on their arc by the hour, the moon drawn in its
  phase, the hour in words beneath (and "above" when the party is below ground, where no sky changes anything); a
  tap says the hour, the day of the run and the moon. What the clock does: the town's lanterns and the townsfolk
  (indoors by night) go by it now; a new moon makes a lock a tenth easier and a night ambush on the first five floors
  a little likelier; a full moon makes the undead a tenth tougher on floors 1 to 5 - and nothing below the fifth
  floor sees the moon. The wall clock keeps only the title screen.
  Test: "the clock".

Scrolls of Homecoming (the eighth big update, phase 1 - v6.2)
  A Scroll of Homecoming (CM.SCROLLS.homecoming) read on any floor below - not in a fight - brings the party to its
  own door; the climb is the night, so it arrives at dawn and the clock says so, and the floors behind it move on
  while it is away (the drifting that a hundred steps would bring). The scroll remembers the square it was read on:
  read again in town it takes the party back to that very square, and crumbles. One chest in twenty from floor 3
  carries one (by the seed), the dead drop one in forty and an elite one in ten, and the Merchant's House sells one
  at a price that climbs with the deepest floor the run has reached (60, and 10 a floor; never the camps, whose
  merchant sells Recall). A hero who was fallen stays fallen until the temple. Automatic reads it when the party is
  out of potions below floor 10 with gold in the purse, runs its errands, and reads it again to go back; the sim
  counts the trips, and the crown rate on Fair with the scroll in play is 16 of 20, where v6.0 left it.
  Test: "scrolls of Homecoming".

The Deep Wood (the eighth big update, phase 2 - v6.3)
  A west gate at the end of the town's main lane opens on floor -1, the Deep Wood (src/js/23b-wood.js, CM.makeWood):
  a thirty-one-square forest made by the seed from the forest's own rules - never the dungeon's generators, whose
  fifty floors do not change by a cell - with glades joined by winding paths through the trees (a tree is a wall
  the renderer draws as a trunk and a crown: CM.art.treeWall, the Wood's own theme of green, grass and sky), a river
  crossed at one ford (a fight there is a fight in water), a hermit's hut, a ruined shrine whose wall carries the
  hill's older page into the journal, a charcoal burner's mound, eight foraging nodes (Wood Mushrooms, Bramble
  Berries, Wild Herbs, Deadwood and, one time in five, Wild Honey: the kitchen's and the forge's things to come) and
  three cave mouths. The first glade, just inside the gate, is safe at any hour.
  By day the Wood is lit by the sky, no torch burns, and deer and boar run from the party (hunted by walking into
  them: meat four times in five, and hides); by night the torch burns, the dark has eyes, and wolves, a bear or
  bandits hunt the party - under a full moon the Great Wolf among them - while the hermit's door and the burner's
  eyes are shut. The beasts change at dusk, dawn and every new day, by the seed. They give no renown and a quarter
  of the gold: hides, meat and the night's danger. The trek makes the party hungry as any floor does.
  The caves (one open a day, by the day of the run) are short floors of the first bands' kinds, carved as any floor
  of their own key and made caves of: the way out where the stair was, no stair down, nothing to fall through, and
  under the third the Troll under the Hill, whose hide is worth a cloak. A Scroll of Homecoming works from the Wood
  and its caves. The floors behind the party are never the town's or the Wood's.
  Test: "the Deep Wood".

Mining and the ore (the eighth big update, phase 3 - v6.4)
  Five ores (CM.ORES: copper on floors 1-10, iron 6-20, silver 11-25, gold 21-40, star-iron 36-50) lie in veins
  beside the rock - things placed last of all in CM.furnish by hash, so no older cell moves and no fingerprint
  changes; the gen-1 fixtures stand - and in the Wood's caves (copper in the first, iron in the second, gold at the
  deepest). A pick mines a vein with Space: a chunk a swing, three swings a vein and it is worked out for the run;
  silver in the Dwarven Halls gives two a swing and the Artificer one more; a swing is five minutes, and it is loud:
  the nearest band comes a square closer. Picks have grades (CM.PICKS: a copper pick mines copper and iron, an iron
  pick silver too, a steel pick everything), wear a point a swing, and are whetted at the forge for 20 gold; the
  dwarves' pick is an iron pick that is kept now, and opens a hidden door for ten points. The Merchant's House sells
  a copper pick, and an iron one once the forge has its second level. Chunks weigh 2 and bars 3: a mining trip is a
  choice about what to carry back. The smelter at the forge (the smith's second level) makes a bar of three chunks
  and a charcoal; two bars of a kind and one of the kind above make an alloy (bronze, steel, electrum, star-steel:
  the upgrading's coin, next phase); the apprentice buys bars at their worth. Charcoal is the Wood's burner's, by
  day: deadwood in, two charcoal out, or one for 15 gold. The bot mines a vein it has a pick for, on its way.
  Test: "mining".

Upgrading and tempering (the eighth big update, phase 5 - v6.5; shipped before the farm)
  Every weapon, armour, shield and helm has a grade (item.grade, 0 to 5), written as stars in the name's tail ("Long
  Sword ★★★") and never in the base id. The forge in town raises a grade for bars of the base's metal (CM.GRADE_METAL:
  copper for tiers 0-2, bronze 3-4, iron 5-6, steel 7-8, electrum above, and star-steel for the fourth and fifth grade
  of the highest tiers), one bar a grade and 60 gold a grade; each grade is +1 power, and at the third and fifth the
  metal remembers it (+1 to blows on a weapon, +1 warding on the rest). The grade is kept through reforging, the vault
  and a replay; a relic and a unique thing are what they are. The ceiling: a thing may not be both of the fifth grade
  and enchanted +3 - the smith says why, either way round. Tempering is the smith's third level (CM.VILLAGE.smith has
  three now: 60, 140, 260 renown): one word from the land worked in for 40 gold, kept for the run and gone at its end
  (never into the stash or the vault) - oak from deadwood (weighs one less), beeswax from wild honey (the water costs
  the torch nothing), wolf-fat from a Wolf hide (the party is not surprised), bear's bile from a Bear hide (a blow in
  four bleeds; blades only), star-dust from a star-iron chunk (+1 to blows); one temper on a thing at a time. The
  hermit of the Deep Wood is a leatherworker by day (CM.TANNING, 20 gold a piece): two hides make a Travel Cloak or
  Soft Boots, three a Buckler or a Quiver (a bow shoots a second arrow from it once a fight), a Bear hide a Hooded
  Cloak, the Troll's hide a Cloak of Wards. The item card shows the grade and the temper; "Five Stars" is an
  achievement. Test: "upgrading and tempering".

The farm (the eighth big update, phase 4 - v6.6)
  A farm stands in the Deep Wood's First Glade, just inside the gate (a thing placed last, by no die, so the Wood
  stands as it was), raised at the town's board with renown like a building (CM.VILLAGE.farm, five levels: a field of
  four rows, an orchard, a mill and a farmhand, hens and two more rows, a cow and a byre) and kept in the village
  store (village.farm) from run to run. The town's beds stay the alchemist's. Six crops (CM.CROPS: wheat and barley
  in spring, beans and cabbage in spring and autumn, turnip in any season but winter, hops in summer) are sown from
  seed - the Merchant's House sells the season's packets once the farm has a field, and every cut gives one back -
  and a row grows a stage every dawn the party sees (the run's clock: a run that sleeps at the camps grows the field,
  a Homecoming and a night at the hearth grow it too; a stair is an hour; the farm sees the run's last dawns when it
  ends), is cut at the fourth stage for the crop's yield, and rots three dawns past ripe. Nothing grows in winter.
  Crows take a ripe row in ten (by the seed and the day) unless a scarecrow stands: a deadwood and an old tunic (any
  light armour). The orchard drops apples and pears on autumn dawns; the mill grinds a sack of wheat or barley in the
  store into flour or malt a dawn; the hens lay an egg a dawn each (three); the cow gives milk a dawn for a week on a
  cabbage; the byre gives two of venison every forty-five dawns. The store holds it all until the party takes it, and
  the farm's food is ingredients (CM.FOODS) - eggs and milk keep a week, in the store or the pack, and then go off;
  grain, flour and malt keep. The farmhand (the mill's level, 30 gold a season) cuts what ripens into the store and
  sows what he is told from the seed chest, so a deep run comes home to a harvest. The season is pinned to the run
  from the real date (CM.season; the calendar's phase makes more of it). Automatic walks out to the farm by day when
  there is something to cut, take or sow, and comes back by the gate. Test: "the farm:".

Cooking as a trade (the eighth big update, phase 6 - v6.7)
  CM.DISHES is thirty-two dishes from the farm's, the Wood's and the beasts' things (src/js/69d-cook.js): bread,
  porridge, an omelette, stew, meat pie, apple cake, roast venison, honey cakes, posset, beer, cheese, the hunter's
  breakfast, the miner's pasty, the fisherman's soup (a new river node in the Wood gives fish), the dwarves' bread
  remade, the Queen's cake, and the dungeon's own - rat on a stick, kobold stew, spore-cap fry, troll's heart - among
  others. A dish is made at the home's kitchen (its third level), at a camp's fire, or on the floor by a cook of the
  third level for a torch, from things in the pack (CM.canCook names the rows), and it travels: a thing in the pack
  that keeps two days (stale ones are thrown out at a fresh floor), eaten by anyone from the bag ("Eat, served by").
  Eating feeds the party and does the dish's thing for its floors - +1 or +2 to attack or defence, blows that land
  more often, mending a round, a stat raised one, Luck, the torch burning slower, the heart lifted, an ailment that
  finds no purchase, a second wind (at a quarter health a hero mends a quarter, once a fight) - the better dishes two
  things; one dish at a time, and eating another replaces it (the old meat meals go through the same door:
  CM.mealOf). A hero may take the apron (h.cook): a level every five dishes made, up to five; a cook's dishes last a
  floor longer a level; "The Apron" is an achievement. Every class and origin has a favourite (CM.FAVOURITES): eating
  it lifts the heart two more and the hero says a line. The tavern's round now feeds the party and comes with bean
  pottage for the first floor; the Merchant's House in town sells bread and porridge. Automatic eats a dish it
  carries when hungry, or at a floor's start with no meal on. Test: "cooking as a trade".

The calendar, the seasons and the festivals (the eighth big update, phase 7 - v6.8)
  Four seasons by the real date (CM.seasonOfDate), or one pinned in Settings for every new run, written into the run
  at its start and kept through a save (src/js/24b-calendar.js). The season sets the day's length (CM.DAYLIGHT:
  summer's night falls at ten and dawn is at four, winter's night at six and dawn at seven), the Wood's gifts
  (summer's hive and brambles give one more), the farm (nothing grows in winter; the seasons' sowing rule), the
  Drowned Town's tide (quicker in autumn's mist), frost near the surface (a tenth harder in winter) and the daily
  dungeon's colour (a winter daily carries Gloom more often, a summer one Swift). The weather is by the seed, the
  day of the run and the season (CM.weatherOf: clear, rain, mist, wind, snow - snow only in winter) and holds a day:
  rain wets the party at the Wood's ford and gives the farm a stage more that dawn; mist hides the Wood's hunters and
  the party from each other (no surprise either way, and the light reaches less); wind takes the party's smell from
  the deer and boar, which do not run; snow freezes the river (crossed anywhere) and the town's well. Twelve
  festivals, one a month in the week around the fifteenth (CM.FESTIVALS; the lore bible's calendar table has them
  all): Midwinter (the hearth gives two rests; the Lich King's court a tenth tougher), the Sexton's Day (a candle for
  nothing), the Sowing (seed at half), the Dwarves' Letter (picks whetted free and sold at half), the Greening (the
  Wood's nodes give one more), Midsummer (the round free; the townsfolk out at night), the Forge Fire (the smith's
  gold at half: an enchantment, a grade, a tempering), the Reaping (the farm grows two stages a dawn), the Harvest
  Fair (a peddler's cloth in the square all week; the farm's yield doubled), the Feast of the Dead (the memorial's
  names read at the well; a candle free; the Ossuary's priests a tenth gentler), the Night of Bells (the
  bell-founder's boy hears one; the regular's gossip free; locks a tenth easier), the Wassail (the round sets the
  heart to full and comes with beer). The sky bar says the season, the festival and the weather under the hour; the
  well's board says the day; the chronicler's house keeps the year's calendar with the runs marked on it.
  Test: "the calendar:".

Around the land (the eighth big update, phase 8 - v7.0)
  The update closes with the land in the loop. Automatic takes a day in the land in the game (a Settings checkbox,
  on by default; the simulator with --land): out by the west gate by day, the Wood's nodes foraged, the open cave gone down with a pick and its
  veins mined, the farm tended when it wants it, then home by the gate; at the door the kitchen makes what the pack's
  things will (up to six dishes), at the forge the bars grade the worn things and the scrap is sold; and in the small
  hours below, with the pack heavy or the party worn, a Scroll of Homecoming brings it home to sleep and back down by
  the same scroll. The simulator prints a line for the land (foraged, mined, farm visits, cooked, dishes eaten,
  grades, nights home). tools/words.js counts the land's words (the Wood's lines, the ores, the crops and foods, the
  dishes, the tempers, the hermit's patterns, the festivals and the favourites' lines), and the farm's and the hut's
  headers go through CM.t. The lore bible gains the Wood's page beside the calendar's table. The gamepad walks the new
  dialogs' buttons as it walks the old; the sky bar's tap tells the hour and the date; a film turns the sky as the run
  did. The balance pass is written up in UPGRADE_PLAN_6.md. Test: "around the land".

The surface, under the sky (the ninth big update - v7.1 to v8.0)
  The town and the land stop being drawn as dungeon floors. (The sections above on the town and the Deep Wood tell how
  they began; the shapes and the look below replace theirs. Every screen behind every door is as it was.)
  The sky (v7.1): on the surface there is no ceiling. A dome over the view takes its colours from the game's clock -
  night, dawn, day and dusk by the season's daylight hours (CM.sky in src/js/26-surface.js) - with the sun and the moon
  on an arc over the south, a full moon lightening the night, and rain, mist and snow greying the day. Daylight reaches
  to the horizon; at night the torch and the moon do what they can. Solid cells have kinds with their own faces and
  heights (CM.SOLID: house, door, shop, frame, town wall, hedge, fence, cliff, tree): houses wear plaster and timber
  under a roof's eaves, the face with a door in it or a shop's board over it; hedges and fences are seen over; trees
  are a trunk and a crown, two crossed pictures, and a leaf canopy closes over a path with trees on most sides. The
  ground wears grass, dirt, cobbles, flags, planks or tilled earth (CM.GROUNDS). A floor's kinds, ground and canopy
  are made with it from the seed and never saved (CM.FLOOR_FIXED). The mesh is plain arithmetic (CM.floorMesh), so the
  Node tests can count a surface floor's ceilings (none) and a dungeon floor's (one over every open square).
  The town (v7.2): Caer Duin on its hill, 45 squares a side, inside a ring wall, with the forest down the slope and
  cliffs north and south. The West Gate opens on Gate Lane, which bends south to Lantern Street; the party's house is the
  first inside the gate. Lantern Street runs east between the townsfolk's houses to the Square (cobbles, the well, the
  market cross, the peddler's pitch on market day), with the Hanged Lantern and the Merchant's House on its north side
  and the Smith's forge and the Guildhall on its south. Temple Row runs north past the Library to the Temple's porch;
  Smiths' Lane south; Shaft Lane east past the Chronicler's House to the Keep-yard, a walled yard of flagstones with the
  shaft's mouth in it. The plots are blocks of house with a doorway cut into the street side; the layout is data in
  src/js/23-town.js (CM.TOWN_BLOCKS, CM.TOWN_HOUSES, CM.TOWN_STREETS, CM.TOWN_SQUARE, CM.TOWN_YARD) and the doors are
  found by name (CM.TOWN_AT). The townsfolk keep to the side streets.
  The land (v7.3): floor -1 is everything west of the wall, 61 squares a side (CM.makeWood, also CM.makeLand). The gate
  opens in the cliffs at the hill's foot onto the road, which runs west through the fields - hedged pastures, copses,
  the farm's rows in their fence where the road bends (the farm moved here from the first glade) - to the river,
  crossed at the ford where the road meets it or by a plank bridge a little north. Over the river is the forest: the
  first glade just past the ford, safe at any hour, seven more joined by paths under the leaves, and deep among the
  trees the hermit's hut, the ruined shrine, the charcoal burner and the three cave mouths, where the seed puts them.
  The night's beasts keep off the road, the fields, the ford, the bridge and the first glade (CM.woodSafe).
  Finding the way (v7.4): signposts stand at the town's junctions, along the road and in the first glade (Space reads
  one); a sign hangs over every finished door (a lantern, a bale, an anvil, a mortar, a book, a sun, crossed swords, a
  quill, a key); the compass and the side panel name the place under the party's feet (CM.placeOf). Where to? (G, or
  the button on the surface) lists the doors and places the party knows with the walk's length, and walks it there,
  stopping for whatever it meets (CM.wayPlaces). The road, the fields and the near bank are on the map from the gate;
  the forest's places join the list once seen. A walk goes round a well, a signpost or a cave mouth unless that is
  where it is going.
  The look (v7.5): two looks now, Pixel (the one to start with) and Stone; the Drawn look is no longer offered, and a
  save that says Drawn opens in Pixel. Its painters stay in the file as what the other two fall back on. Pixel takes
  Crawl's grass, dirt and grey brick for the surface, with the drawn trees, houses and signs made of pixels. Stone takes
  eight more ambientCG sets (CC0; Grass001, Grass005, Ground110, Ground103, Plaster001, RoofingTiles013A, Bark007,
  Bricks097, kept whole in the Timeline's Local Storage like the others) for the grass, the road, tilled earth, the
  hedges, the plaster under the drawn timbers, the roofs, the bark on the trunks and the town wall.
  Around the surface (v8.0): Automatic walks the new town's errands and takes its day on the land as before (the
  simulator's land line is unchanged from v7.0's); UPGRADE_PLAN_7.md says what each phase did and what waits (the east
  postern). Tests: "the surface", "finding the way", and the town's and the Wood's tests on the new ground.

A world with things in it (the tenth big update - v8.1 to v9.0)
  The view fills up. No rule changes: everything below is for the eye only, made from the seed and never saved, except
  the traces, which are the party's own doing. UPGRADE_PLAN_8.md says what each phase did.
  Ground everywhere (v8.1): ground under every tree, hedge and fence (needles under a fir, leaf litter under a
  broadleaf), and past the map's edge a skirt of ground and a far ring of tree-line and hills instead of sky.
  The scatter (v8.2): CM.PROPS and CM.scatter in src/js/27-props.js say what small things lie on each square, by a hash
  of the seed, the floor and the square - the same every visit, never on a thing, a door or the start. They go into
  the floor's mesh with the walls. The Detail setting (Low, Medium, High; Settings and the title) scales how many.
  The surface's life (v8.3): grass tufts, flowers by the season, shrubs, ferns, stones, logs, stumps and reeds on the
  land; barrels, crates, a cart, a trough, flower boxes and lamp posts in the town, stalls on market day.
  The dungeon's debris (v8.4): each band its own - bones and skulls, rubble, cobwebs in the corners, puddles, slag,
  shards and roots.
  Traces (v8.5): the floor remembers. A fallen monster leaves remains by its kind, a drunk potion its empty bottle, a
  fireball a scorch, a spent torch its stub. These are saved, at most forty a floor.
  Walls, floors and ceilings (v8.6): variants and turns of each tile, darker corners and wall feet, cracks, moss,
  chains, banners and niches on the walls, beams and stalactites overhead, lintels round the doors.
  Light and shadow (v8.7): the wall torches light their walls (up to twelve lights near the party), embers, crystals
  and fungus glow, soft shadows lie under things, the sun lights the walls that face it, and each band has its own
  colour grade. The pictures every band shares are uploaded once, so going down a band no longer halts the view.
  Air and weather (v8.8): CM.airKinds says what drifts where and CM.Air (src/js/46-air.js) keeps it moving about the
  party - dust in every open room, drips in the wet bands, embers in the Foundry, spores in the Fungal Deep, glitter
  in the Crystal Caverns; on the surface rain, snow, falling leaves (autumn most), fireflies on summer nights, birds,
  clouds and smoke from the town's chimneys, blown by the wind. None at Low, or with reduced motion.
  Around the update (v9.0): the frame's cost, measured. tools/perf.js times three heavy scenes - the land by day, a
  room of torches, a fight with fireballs - and the smoke test runs it in both looks. On a desktop graphics card every
  scene holds 60 frames a second at High and at Medium, the game's own script taking under 2 ms a frame. When frames
  come late for two seconds the Detail steps down first, then the render scale; quick frames for ten seconds step
  back up. The file grew from 3.8 MB to 4.7 MB (within the plan's budget of 1.5 MB): the photographs and the atlas are
  3.1 MB of it, and the small props share texture layers four to one.

The second five trials (v94.0, UPGRADE_PLAN_65.md release 4)
  (src/js/69zzzg-trials2.js, src/js/76zzzzzzzzzzzb-trials2.js, UPGRADE_PLAN_65.md)
  - The trials, the second five (plan 65, release 4): the Wind Tunnel, a draught down the middle of a long hall
    that puts the torch out and shoves the party a square back every third step - a lantern stands in it, and the
    squares along the walls are out of it; the Counting Room, gold on every flag of the floor, taken by walking,
    and past eight squares' worth the gate behind the party drops - a square's worth back on the altar at a time
    lifts it, and the altar always takes; the Crawlway, a room crossed bent double with rats asleep in it and a
    chest under the crawl's roof; the Weighing of Deeds, two stone hands with the band's relic between them that
    weigh what the run has done - foes slain, guardians spoken with, the dead laid to rest, chests opened - against
    fights fled, and give or say not yet, and never curse; and the Dice Room, a stone die the size of a stool for a
    stake of fifty - a six triples it and opens the chest, a one opens the box the die sits in, which is a mouth.
    Fifty rooms now.

The first five trials (v93.0, UPGRADE_PLAN_65.md release 3)
  (src/js/69zzzf-trials.js, src/js/76zzzzzzzzzzza-trials.js, src/js/64-meta.js, UPGRADE_PLAN_65.md)
  - The trials, the first five (plan 65, release 3): the Hourglass Room, where turning the glass lifts the bars on
    four chests for twelve steps and no more, once a day; the Riddle Gallery, three statues standing in three doors,
    each with one of the carvings' own riddles - a wrong answer wakes the statue; the Pendulum Hall, one flag wide
    between two pits with blades sweeping it on a beat - cross on the off-beat, or take a cut and a square back, and
    Space waits a beat; the Dark Room, where no torch will burn and only a light of the party's own making shows the
    walls, with shadows asleep in the middle of it and the way on at the far wall; and the Frozen Pond, ice wall to
    wall and a step that keeps going till a wall, a chest or dry stone stops it. The riddles' reward of experience
    now follows the story floor, as the rest of the loot does. Forty-five rooms now.

Six more stage pieces (v92.0, UPGRADE_PLAN_65.md release 2)
  (src/js/69zzze-stage2.js, src/js/76zzzzzzzzzzz-stage2.js, UPGRADE_PLAN_65.md)
  - Six more stage pieces (plan 65, release 2): the Fallen Star, a crater in the floor and the star itself, a lump of
    star-iron a pick will have; the Waterfall Hall, the aquifer through the wall in a sheet into a pool - walk through
    it and the torch gutters a step, and behind it a niche with a chest; the Lantern Shaft, a small hall with a grate
    in its roof and daylight and weather down it, and a rope ladder up to a ledge with a chest; the Sunken Chapel,
    half under black water with the pews still standing in it and a bell under the water - dive and ring it on a
    holy day for a blessing, on any other day for the drowned; the Petrified Wood, trees stone to the last leaf, a
    stone deer and a stone traveller, a fountain, and a chest under a basilisk's eye - its gaze turns one hero to
    stone for two turns and the fountain undoes it; and the Throne of the Hollow One, a crown on a sleeper's head -
    take it and it wakes, and if the hall's roots are burning it cannot rise for three turns. Forty rooms now.

Four stage pieces (v91.0, UPGRADE_PLAN_65.md release 1)
  (src/js/69zzzd-stage.js, src/js/76zzzzzzzzzzy-stage.js, UPGRADE_PLAN_65.md)
  - Four stage pieces (plan 65, release 1), rooms whose point is a sight built from several squares, their meshes
    made in code: the Giant's Ribcage, ribs arching the whole hall in two rows and a skull the size of a cart at the
    far end with a chest between its teeth - by day only a chest, by night the thing the bones belonged to stirs;
    the Shipwreck, a hull and a mast broken through the Drowned Town's vault into a ring of black water with fish in
    it, a deck to walk, the captain's chart in the cabin, and a green bell at the mast's foot that brings the
    Drowned down off the deck together; the Rope Bridge, one bridge of planks and rope over a dark that goes down
    farther than any light, swaying at every step, wyverns passing under it, a chest hauled up at the far end - and
    the chasm itself never walked into; and the Great Mushroom, one cap as wide as the hall on a stalk with steps cut
    in it, glowcaps burning at its foot and Sporelings asleep under the cap, and from the top the whole floor round
    it seen at once. Thirty-four curated rooms now.

The deeper shaft (v90.0, UPGRADE_PLAN_66.md)
  (src/js/10-data.js, src/js/20-world.js, src/js/21-gen1.js, src/js/22-gen2.js, src/js/62-combat.js, src/js/61-explore.js, src/js/13-lore.js, src/js/14-items.js, src/js/23c-ore.js, src/js/60-game.js, src/js/64-meta.js, src/js/68-shops.js, src/js/70-ui.js, src/js/71-title.js, the set-piece and room files, tests/fixtures/gen1.json, UPGRADE_PLAN_66.md)
  - The deeper shaft (plan 66): a hundred floors. The old fifty are the story floors now, and the real shaft is
    stretched over them - three or four floors to a story floor above the Lich King, so the Catacombs run 1-17, the
    Flooded Vaults 18-35, the Dwarven Halls 36-52 and the palace 53-70, with the Lich King on 70; and one to one
    below him, the Drowned Town from 71 to the Root of the World on 100. The guardians and the merchants' camps
    stand on the story floors' key floors (the Rat King on 17, the Drowned Knight on 35, the Forge-Warden on 52, the
    Deep's on 75, 80 ... 100); the other floors are ordinary floors of their band, with room for the set pieces. The
    monsters' levels and the loot keep the old curve by story floor, fights above the palace's floor give less
    experience so the party reaches the king a little stronger than before, the carvings read the story floor's
    chapter, and the kits and achievements ask their real floors (Delver 17, the Vaults 35, the Halls 52, the Palace
    70, the Deep 80, the Bottom 100, Without End 110, Beyond the Dream 150). Endless deepens every ten floors below
    the hundredth. The first generator's frozen fingerprints are regenerated: the world below the third floor is
    not the world it was.

The last seven rooms (v89.0, UPGRADE_PLAN_64.md release 4)
  (src/js/69zzzc-rooms4.js, src/js/76zzzzzzzzzzx-rooms4.js, UPGRADE_PLAN_64.md)
  - The last seven rooms (plan 64, release 4): the Mirror Hall, where the party's own faces look back a half-breath
    late and step out of the glass as shades when it is struck, a shard of it to keep; the Cold Store, meat on
    hooks and frost on the walls, and in the ice at the back something that wakes when the larder is empty; the
    Tilting Floor, four plates about a barred chest - step them in the carving's order and the bar draws back,
    step them wrong and the floor leans and a pit opens across the room for a turn; the Puzzle of Lamps, five lamps
    to light in the carving's pattern for a door that was not there, and a cold that comes in if they are lit
    wrong; the Spider Hollow, cocoons from the roof with someone alive in one, egg sacs that split when it is cut,
    and the spider on its ledge that never comes down; the Kennel, iron hounds in every other cage, a lever that
    looses them all at once, and the kennel-master's whistle on a hook; and the Hall of Fame Annex, plaques with
    your own dead's names on them, a bell rung once for each, and a chest the bell opens. Every room thing now has
    a picture, the earlier rooms' included; the view leans when a plate tilts. Thirty rooms: plan 64 is complete.

Ten more rooms (v88.0, UPGRADE_PLAN_64.md release 3)
  (src/js/69zzzb-rooms3.js, src/js/69zzz-setpieces.js, src/js/69zzt-clutter.js)
  - Ten more rooms (plan 64, release 3): the Echo Chamber, where a bell on a frayed rope brings the floor's
    nearest two bands of foes to one fight; the Gauntlet, a long run of vents that breathe in turn, a chest at the
    far end; the Weighing Room, a relic of the band on a brass scale - count out its weight in gold, or take it and
    carry a curse till it is lifted; the Barrow, steps up a mound to a stone coffin whose lid opens on grave goods
    and the one buried with them; the Wolf Den, trees come down through the roof and a ring of wolves asleep round
    their kill - strike them before they wake, or walk round; the Troll Bridge, one narrow way over black water and
    a troll halfway who takes a toll in gold or a fight, and remembers; the Painter's Room, where a ghost finishes
    the party's portrait if they stand still a while - a painted likeness to carry, a little luck in it; the
    Orrery, brass rings that turn with the sky and tell the next three days' weather and the next falling star;
    the Lich's Study on the last floors, his desk, his letter, and a chair that was never meant for visitors; and
    the Kitchen, the cook's knives on the wall and rats in the flour. Twenty-three rooms now, one floor in three.

Nine more rooms (v87.0, UPGRADE_PLAN_64.md release 2)
  (src/js/69zzza-rooms2.js, src/js/69zzz-setpieces.js, src/js/69zzs-plants.js, src/js/76zzzzzzzzzzw-setpieces.js)
  - Nine more rooms (plan 64, release 2): the Garden Gone Wild - raised beds, a well, glowcaps, the plants grown
    thick, and the gardener's shears in a chest under the brambles; the Chapel of Candles - rows of them lit, and an
    altar at the end; the Map Room - a stone table with the floor cut in its top, which maps the whole floor when
    read, and a scroll of mapping in the chest; the Rookery - a dark floor under a high roof, bats that wheel and
    scatter from the torch, a nest on a ledge with a trinket in it, and something worse among the bats; the Cistern
    - a sunken hall of the first floors' damp bands with a chest in its middle, a walk when dry and a dive after a
    storm; the Dripping Gallery under the street, puddles on the floor and a key under one; the Storm Drain, a
    channel through the room and a gate; the Steam Room of the Foundry and the Root, whose pool is a white blindness
    under a winter sky; and the Lightning Rod on the first floors, an iron rod from roof to floor that makes any
    lightning cast in that room leap to every foe. One floor in three from the third carries one of the thirteen
    rooms now, each where it belongs.

The set-piece rooms, and the soft-lock pass (v86.0, UPGRADE_PLAN_64.md release 1, UPGRADE_PLAN_63.md release 7)
  (src/js/69zzz-setpieces.js, src/js/76zzzzzzzzzzw-setpieces.js, src/js/22-gen2.js, src/js/69zzs-plants.js, src/js/69zzv-rockfalls.js, src/js/69zzw-blooms.js, src/js/69zzu-basins.js)
  - Set-piece rooms (plan 64, release 1): one floor in three from the third holds a curated room of its own. The
    Oasis: a ring of trees about a pool with lilypads, a chest on the far bank that the wolves who drink there
    guard, and a second chest under the water to dive for. The Bone Room: heaps to the walls, the floor black, a
    chest under one heap - turn the right bones over and the bones stand up. The Hall of Doors: a long hall of
    doors down both walls, two real, two opening on a niche with a key or a chest, one with teeth, the rest painted,
    nailed or bricked. The Fish Pool: water wall to wall with fish flicking under it, a plank walk to a stone and a
    chest the Drowned rise for. Each room says its line on the first step in. The rooms roll their own dice, so
    every other room on every floor stands where it stood.
  - The soft-lock pass (plan 63, release 7): a test storms three runs through their first eight floors with the
    flood, the blooms, the beasts and every rockfall the dice allow, and proves the whole map's reach holds, every
    fall clears, no hazard lies in a narrow way or by the stairs, and no hero drops below one. It found that the
    reach checks judged the way by passable squares and so missed a locked door's far side and the key beyond it;
    they judge the map's shape now.

The blooms, the drafts, the steam and the beasts (v85.0, UPGRADE_PLAN_63.md releases 4-6)
  (src/js/69zzw-blooms.js, src/js/76zzzzzzzzzzu-blooms.js, src/js/69zzx-steam.js, src/js/76zzzzzzzzzzv-steam.js, src/js/69zzy-migrate.js, src/js/69zzs-plants.js)
  - The blooms (plan 63, release 4): rain above over the last day is a bloom below. The damp bands' moss, weeds and
    fungus grow thick by it, and at half or more a floor sprouts, once a day, glowcaps - pale green clusters at the
    walls' feet that throw a green light, light enough to see by - and spore patches, pale on the floor, a point of
    sickness to each hero who steps through, never below one, named on the look line and never laid on the stairs,
    a doorway, a narrow corridor or anywhere that would close a way. Both go after a day.
  - The drafts: a gale or a tornado above sends a draft down the shaft and along the corridors of the first four
    floors - the haze and the smoke stream along it - and there the torch may be snuffed a few steps as a gust does
    above, never the spell light; the spore patches are blown a square along the draft every ten minutes, never
    onto the stairs or into a dead end.
  - Steam and the dry roots (release 5): in the Foundry and at the Root of the World, water on the hot stone -
    floodwater underfoot, or rain dripping down - under a cold sky is a screen of steam: the sight a square, a bow
    at three quarters. In a heat event above, the Root of the World's roots are tinder-dry: a fire spell in a fight
    there bites a quarter harder and sets the hall's roots alight for a quarter hour, flames and smoke along the
    walls and an orange light - a sight, never a harm to the party.
  - The fog pools: a magical fog lies at its full strength in a sunken hall, the sight a square and said as the
    party steps down into it, and at half in a raised one.
  - The beasts (release 6): under a storm or a tornado above, the first two floors' wandering groups not yet met
    are the land's own for the event - wolves, a boar, a bear, the bandits - at the floor's level and the group's
    own size, never a group beside the party, never a still one or a boss', and the floor's own again when the sky
    clears. On a flooded floor, or in the Flooded Vaults under rain, the water's kinds come up fast: one fight in
    three with the Drowned, the Weed Hag or the Rootling opens with their strike sure.

The rockfalls (v84.0, UPGRADE_PLAN_63.md release 3)
  (src/js/69zzv-rockfalls.js, src/js/76zzzzzzzzzzt-rockfalls.js, src/js/69zzs-plants.js)
  - The rockfalls (plan 63, release 3): the first four floors' roofs are not to be trusted when the ground above
    is sodden with rain, when a gale blows above, or in the hour after a meteor's shock. Now and then a fall of rock
    comes down on a corridor square - a crack and a roar, the view shaken, dust bursting and sifting from the broken
    roof - and blocks it: a heap of rock, named on the look line. It never falls in a room or a doorway, on a thing
    or a feature, on the party or beside it, near the way up on the first floor, near another fall, or more than
    three to a floor; and it never falls where it would cut off any square from the stairs - the whole floor's
    reach is checked before each one. Stand before it and press Space: twenty minutes with hands and shoulders
    (and the pick, if one is carried, but none is needed) and the way is open. Left alone, a fall settles and
    clears itself after a day.

The water basins (v83.0, UPGRADE_PLAN_63.md release 2)
  (src/js/69zzu-basins.js, src/js/76zzzzzzzzzzs-basins.js)
  - The water basins (plan 63, release 2): the flood has two depths. While a heavy storm's water stands the sunken
    halls are waist-deep - two minutes more a step, the walk at twice the pace, the step a deep splash, the sky bar
    naming the depth - and knee-deep as it drains over the day after. The water hides things. A spiked grating set
    in the floor of a wide sunken hall is harmless and plain when dry, a point a step to each hero when flooded,
    never below one, and never on a doorway: a hall is always crossed another way. A leech may fasten on a hero
    wading waist-deep a while - a bite that festers like a poison, pulled off by any healing or the camp. One chest
    in three of the sunken halls is sunk: while the water stands it is dived for, a quarter hour of the clock.

The clutter below ground (v82.0, UPGRADE_PLAN_63.md release 1)
  (src/js/69zzt-clutter.js, src/js/76zzzzzzzzzzr-clutter.js, src/js/69zzs-plants.js, src/js/36-looks.js, src/js/80-main.js, src/js/76zzzzzzzzzzq-plants.js)
  - The clutter below ground (plan 63, release 1): the dungeon is a lived-in place. Stalagmites stand at the walls'
    feet and in the corners, three sizes, and stalactites hang from the ceilings over them - stone grey, crystal
    blue in the Crystal Caverns, never in the middle of a narrow way. By band the walls carry drainage ports and
    barred grates at their feet (the damp halls), pipe mouths that drip (the Foundry and the damp halls), and
    spiderwebs in the corners (most in the Catacombs and the bone halls). Bugs crawl on the floor about the party and
    scatter from its feet. A few rats sit at the corridors' edges and scurry off two squares as the party comes
    within two, never fought, never in the way, home again when the party is far. All of it a sight: nothing is
    solid, nothing stands on the stairs, a thing or a feature; the Detail setting sets how much.
  - Under the hood: a set of pictures painted ahead in the art worker now passes through the window's own
    additions, so no floor painted ahead lacks the twister's, the fogs', the plants' or the clutter's pictures; and
    the floor's pictures are made again if the plants' pack arrives after them.

The plants (v81.0, UPGRADE_PLAN_62.md phases 3-4)
  (src/js/69zzs-plants.js, src/js/76zzzzzzzzzzq-plants.js)
  - The plants (plan 62, phases 3-4): the world is painted with them, as meshes from the same CC0 pack as the
    trees. On the grass, tufts and flowers; under the trees and on the forest floor, plants and ferns; beside the
    trees and along the walls, bushes - berried in summer and autumn, snowy under snow; here and there on the
    Wood's floor a stump, a log, a rock; corn and wheat on the farm's tilled rows; lilypads on the river's still
    water. The flowers go in winter and the grass is short; every plant sways in the wind, parts for the party and
    whitens under snow. Below ground each band has its own growth: moss in the Catacombs, pale weeds in the Flooded
    and the Salt Vaults with lilypads on their water, fungus thick in the Fungal Deep, roots at the Root of the
    World - in the corners and along the walls, never in the way. The Detail setting sets how dense; at low Detail
    the pictures stand alone.

Mesh trees (v80.0, UPGRADE_PLAN_62.md phases 0-2)
  (tools/plants.py, src/models/plants.json, src/js/35d-plants.js, src/js/37b-plants.js, src/js/69zzs-plants.js, src/js/76zzzzzzzzzzq-plants.js, src/js/40-render.js, src/js/26-surface.js)
  - Mesh trees (plan 62, phases 0-2): the trees have bodies. Within sixteen squares (twelve at medium Detail; at low
    Detail the pictures stand as before) every tree square carries a low-poly mesh from the CC0 Quaternius Ultimate
    Nature Pack - common trees, pines and birches by the square's old variant, willows by the water - each turned
    and sized a little differently, swaying in the wind and whitening under snow as the ground does. In autumn the
    broadleaves turn shape by shape as the leaves turn; in winter they stand bare and the pines stay green; when the
    snow lies deep every tree wears its snow shape. A felled tree lies as a log, a burned one stands as a black
    dead shape, a sapling is the green shape small. Beyond the reach the painted trees stand as they always did.
  - The pipeline: the pack is baked by tools/plants.py (47 models, 620 KB) into one deflated file, read by
    37b-plants.js in the game and the tests, coloured by one palette picture, and drawn instanced - one draw a
    kind - after the figures. The plants, the bushes, the flowers and the crops are the next phases.

The combat synergies and the soundscape (v79.0, UPGRADE_PLAN_61.md parts 9 and 10)
  (src/js/69zzr-synergy.js, src/js/76zzzzzzzzzzo-synergy.js, src/js/76zzzzzzzzzzp-soundscape.js)
  - The combat synergies (plan 61, part 9): the weather is in the fight on the surface. Under a storm a lightning
    spell bites a quarter harder and the storm's own bolt leaps on to a second foe for half, with a flash and a
    thunderclap. In rain or a storm a fire spell bites a quarter less and leaves no burning behind. Floodwater
    underfoot is water for the fight, so lightning chains through it as it does in the drowned halls. An arrow or a
    bolt shot into a headwind lands less often and falls a point short; on a tailwind it lands more often and flies
    a point long - the wind against the facing, said once a fight.
  - The soundscape (plan 61, part 10): the weather's beds follow the live event's strength - the downpour's roar
    and the roofs' patter rising with a heavy rain, the gale's howl leaning with the gusts - and each magical fog has
    a pad of its own: the orange fog a crackling static over a low hum, the green a soft bubbling hiss, the brown a
    slow pulsing drone, the violet a crystalline chord that drifts. Below ground the same beds are heard muffled
    through the stone, by the floor's depth. A tree felled within hearing cracks and falls. Under a storm or a fog
    the music draws back - softer and muffled - and comes back when it clears.

The dungeon coupling (v78.0, UPGRADE_PLAN_61.md part 8)
  (src/js/69zzq-below.js, src/js/76zzzzzzzzzzn-below.js, src/js/76zzzzzzzzu-daylight.js)
  - The dungeon coupling (plan 61, part 8): what the sky does reaches down the shaft. Rain above drips from the
    ceilings of the first three floors and the damp rises; a storm pours a waterfall through each grate, with its
    splash, and its lightning comes down through the grates as well as the shaft. A heavy storm floods the sunken
    rooms of those floors knee-deep - the flooded mood's black water on their squares, a splash to every step, a
    minute more a step and the walk heavier - and the water drains away over the day after. A gale above makes a
    draft below: the torches gutter and lean, the smoke drifts. In the Foundry and the Root of the World the
    floodwater and the drips steam, and the haze thickens.

The light, the mud and the breath (v77.0, UPGRADE_PLAN_61.md part 7)
  (src/js/69zzp-mud.js, src/js/76zzzzzzzzzzm-light.js, src/js/40-render.js, src/js/76zzzzzzzzzzi-wxair.js, src/js/76zzzv-shadows.js)
  - The light, the mud and the breath (plan 61, part 7): rain makes mud of the earth above ground - the dirt
    roads, the tilled rows and the Wood's litter darken in patches and gloss, a storm most, drying over three
    hours - and a step on muddy earth takes a minute more, the walk heavier. In the hour after a rain, with the sun
    low, god rays stand over the land. A lightning flash lights the land from the bolt's side for its frames, so the
    walls' facing and the cast shadows jump. The sunset's shadows run longer. The heat's shimmer lies along the
    horizon over the far land rather than over the whole view. In the cold, every figure's breath shows: a pale
    puff from each mouth now and then.

The magical fogs (v76.0, UPGRADE_PLAN_61.md part 6)
  (src/js/69zzo-fogs.js, src/js/76zzzzzzzzzzl-fogs.js, src/js/73c-wxhud.js)
  - The magical fogs (plan 61, part 6): four fogs among the weather's events, rarer than rain, six hours long, and
    they do not stop at the shaft - the same fog hangs on every floor below. Each is a status on the whole party
    while it lasts, said when it comes and when it goes, and named with its effect on the sky bar: the orange ember
    fog (spells cost half again as much and bite a fifth less), the green rot fog (a point of poison to each hero
    every ten minutes, never below one), the brown dun fog (strength a fifth down), the violet wild fog (one cast in
    ten twists into another spell of the same kind).
  - Above ground a fog is a coloured low veil of drifting billows, the sky, the clouds and the far land drawn to its
    colour; below, the torches and lamps burn in its colour, the haze thickens and the billows drift through the
    halls.

Meteors and the ore (v75.0, UPGRADE_PLAN_61.md part 5)
  (src/js/69zzn-meteors.js, src/js/76zzzzzzzzzzk-meteors.js, src/js/26-surface.js, src/js/40-render.js)
  - Meteors and the ore (plan 61, part 5): a star falls every day and a half to three and a half (the first within
    a day or so), by night more often than not. In the minutes before, the birds go up from every tree at once
    (by night the crickets and owls go quiet and the town's dogs howl). It streaks down the sky with a whistle to
    an open square the party can walk to, never under them, never on a building, a fence or a tree: a flash, a
    crack, a rumble, the ground shaken, a burst of dust, stones and embers, and an orange glow in the crater that
    fades over the minutes. Trees in its reach may catch, on a dry night. Below ground it is a shock through the
    stone and a dust-fall, and the chunk waits on the town's or the Wood's floor.
  - The crater: a scorched square with a raised rim, healing over ten days. In it a chunk of the fallen star - step
    onto it to take it: Meteor Iron, an ingredient worth 60, which anyone buys and which the smith takes in a
    diamond's place when he works a weapon or a piece of armour.

Trees that fall, burn and grow again (v74.0, UPGRADE_PLAN_61.md part 4)
  (src/js/69zzm-trees.js, src/js/76zzzzzzzzzzj-trees.js, src/js/26-surface.js, src/js/40-render.js, src/js/76zzzzzzzzzzi-wxair.js)
  - Trees that fall, burn and grow again (plan 61, part 4): a gale fells a tree now and then and a tornado fells
    what stands in its wake; lightning in a storm sets one alight, and fire spreads tree to tree - less in rain,
    not through snow, out in a downpour - but never to a building, a fence or the party: flames and smoke and an
    orange light, a sight and not a harm. A burning tree burns forty minutes and falls charred; a fallen or charred
    tree lies three days as a log (a black one over ash), then a sapling stands in its place, a tree again seven days
    on. The square stays solid the whole way, so nothing opens a way off the map.
  - In a storm or a gale a town lamp may blow out, and stays dark till the lamplighter's round.
  - The twister is fuller: more than twice the whirling parts, the air's budget raised while it crosses.

The stronger sky and air (v73.0, UPGRADE_PLAN_61.md part 3)
  (src/js/24f-events.js, src/js/76zzzzzzzzzzi-wxair.js, src/js/69v-weather.js)
  - The stronger sky and air (plan 61, part 3): a tornado - an hour or two, by day in summer and autumn - is a
    funnel of dark whirling air that comes in from the wind's side and crosses the land at half a square a minute,
    dust and debris flung up round it, the sky black over it; in a gale the air fills with flying leaves, twigs and
    dust streaking downwind, and the lamps and torches gutter in the gusts.
  - A dense mist closes the party's sight to a single square (a light one to two), the air thick with it; a heat
    event on a summer afternoon shimmers the air over the ground.
  - After rain, with the sun low, the dawn or the dusk is dramatic: the sun's glow doubled and the clouds lit in
    its colour, fading over the hour and a half after.

The weather, live (v72.0, UPGRADE_PLAN_61.md part 2)
  (src/js/24f-events.js, src/js/76zzzzzzzzzzh-wxlive.js, src/js/73c-wxhud.js, src/js/70-ui.js, src/js/73b-clock.js)
  - The weather is live (plan 61, part 2): rain, a storm, mist, wind, snow, cloud, heat or an aurora comes as an
    event of two to six hours, rolled when the last one ends by the season, the hour and the day's leaning, with
    clear spells of one to six hours between (longer at night, which leans clear); it comes in and goes out over
    twenty minutes, and everything that watched the day's word - the rain's fall and the ground's wet, the cloud,
    the mist's depth, the wind on all that sways, the lightning, the sounds - follows the event and its strength.
  - The dial: a bar of the next six hours under the clock, each event in its colour, and the words - "rain (heavy)
    - clearing in 1 h 20" - with the full date and time on hover; the sun and the moon drawn half again as large,
    and the stars thicker on a clear night.

The clock that runs (v71.0, UPGRADE_PLAN_61.md part 1)
  (src/js/24e-calendar2.js, src/js/76zzzzzzzzzzg-clockrun.js, src/js/73b-clock.js, src/js/26-surface.js, src/js/70-ui.js, src/js/71-title.js, src/js/64-meta.js)
  - The clock runs (plan 61, part 1): on the floor, in a fight or at camp a game minute passes every two and a half
    seconds whether the party moves or not - a day in an hour, a night the same - and a step still costs its minute.
    Settings > Clock: Runs, or By steps only, as it was.
  - The calendar: the run's days count into years of twelve months of thirty days from Year 500, each month named
    for what the land does - Thawlight, Sowmoon, Greening, Highsun, Hayfall, Emberwane, Harvestmoon, Claudetober,
    Lanternfall, Frostbell, Deepsnow, Longnight - with its number beside the name on the dial. A run begins on the
    first day of its season's first month.
  - Dawn and dusk take two hours each side now (five minutes at the clock's pace) instead of one.
  - The Lich King has a name: Claude, the Lich King.
  - The films and replays are gone - the title's Films, the film bar, the film codes, the film kept at a run's end;
    nothing need play back the same now, so the weather and the world may roll their own dice from here on.

The figures, finished (v70.0, UPGRADE_PLAN_60.md phase 5)
  (src/js/76zzzzzzzzzzf-figures3.js, src/js/76zzzzzzzzzze-figures2.js)
  - The figures, finished (plan 60, phase 5): at load each body is drawn once, flat-lit from the front, into an
    impostor picture; beyond the fourteen squares the bodies are drawn in, a kind wears its impostor in place of the
    old painting, so it looks the same near and far - and the bestiary's plates and the monsters' pictures are the
    impostors too where a kind has a body.
  - No more than forty bodies are drawn a frame, the nearest; the rest wear impostors. A test holds thirty figures'
    posing to the frame's budget.
  - Credits: KayKit (Kay Lousberg) and Quaternius, CC0, join the game's credits. Plan 60 is complete.

The monsters in batches (v69.0, UPGRADE_PLAN_60.md phase 4)
  (src/models/figures.json, src/js/37-figures.js, src/js/76zzzzzzzzzze-figures2.js)
  - The monsters in batches (plan 60, phase 4): fifty-four kinds have bodies now - the small folk (kobold, goblin,
    the imps), the big (orc, troll, ogre, minotaur, demon), the dead (zombie, ghoul, wraith, the hollow), the
    drowned and their knight and queen, the golems and the gargoyle, the beasts (boar, bear, stag-wyvern, eel,
    root wyrm, the frogs of the marsh), the guardians and the Lich King - each in its own colour and size. The
    plants, the fungus and the mimic keep their painted pictures: no body fits them.
  - What a foe carries is in its hand - a sword, an axe, a knife, a staff, a crossbow, by the weapon's name - and
    a striker steps in and back with its blow.
  - Five more CC0 animals from Quaternius (bull, fox, stag, snake, frog); the bake is 2.0 MB.

The town's people (v68.0, UPGRADE_PLAN_60.md phase 3)
  (src/js/37-figures.js, src/js/76zzzzzzzzzze-figures2.js, src/js/76zzzzy-townsfolk.js, src/js/76zzzzzzj-market.js, src/models/figures.json)
  - The town's people (plan 60, phase 3): all six residents have bodies now - the merchant, the priest and the
    tavern-keeper had no picture before and were never seen walking their rounds - and at the forge, the stalls, the
    Library and the Temple they stand at their work rather than idling; the traders at their stalls likewise.
  - What they carry is in their hands: the smith's axe, the tavern-keeper's mug, the priest's and the librarian's
    books, the hermit's staff, the lamplighter's pole, the knight's sword and shield - each a mesh bound to the hand
    of the same rig, moving with the body.

The figures' own motion (v67.0, UPGRADE_PLAN_60.md phase 2)
  (src/js/37-figures.js, src/js/76zzzzzzzzzze-figures2.js, src/js/80-main.js, src/js/76zzzzzzzzz3-crowds.js, src/js/76zzzzf-nightlife.js, src/js/76zzzzzzi-kennel.js, src/models/figures.json)
  - The figures' own motion (plan 60, phase 2): a body walks its walk when it moves and turns the way it goes -
    the crowds on their rounds, the lamplighter, a monster prowling the floor, the hound at heel - and idles when it
    stands; in a fight it strikes on its lunge (the wizards and priests cast instead), flinches when a blow lands,
    falls when it dies and lies where it fell; a foe worn down is darker. Each change blends over a few frames.
  - The fight's foes square up to the party; the rest face where they last went.

The figures, drawn (v66.0, UPGRADE_PLAN_60.md phase 1)
  (src/js/40-render.js, src/js/37-figures.js, src/js/76zzzzzzzzzze-figures2.js)
  - The figures are drawn (plan 60, phase 1): the townsfolk, the hound and the pony, and the monster kinds with
    a body in the mapping - rats, skeletons, wolves, spiders and more - stand as modelled bodies in their idle,
    skinned by the renderer, stood their picture's height (a rat its length), turned to face the party, tinted as
    the mapping says, and lit by the same light as everything else; within fourteen squares, farther off their
    pictures stand as before.
  - Settings > Figures: Modelled (the bodies) or Painted (the pictures as they were); Low detail keeps the pictures.
  - The shadows, the marks, the statuses and the fight's strip are untouched; the bodies' own motion - walking,
    striking, falling - is the next phase.

The figures' pipeline (v65.0, UPGRADE_PLAN_60.md phase 0)
  (tools/models.py, src/models/figures.json, src/js/35c-figures.js, src/js/37-figures.js, src/js/76zzzzzzzzzzd-figures.js)
  - The figures' pipeline (the first step of plan 60): twenty-five rigged, animated low-poly bodies from the CC0
    KayKit (adventurers, skeletons) and Quaternius (animals, rat, spider) packs, baked by tools/models.py into one
    deflated binary of 1.6 MB inside the file - meshes quantised, the clips sampled at 15 a second and shared
    between the figures that use the same library, and read back by 37-figures.js in the game and the tests.
  - src/models/figures.json says which body stands for each townsperson, pet and monster kind, at what size and
    tint, with what in hand; thirty-odd are mapped so far, the rest marked painted. The sources stay in Local
    Storage with their licences; credits in src/models/CREDITS.txt.
  - Nothing is drawn from the figures yet: the game loads and parses them at start, off the main path, ready for
    the renderer's turn (phase 1). Everything looks as it did.

The places' look (v64.0, UPGRADE_PLAN_59.md)
  (src/js/64zzze-placelook.js, src/js/76zzzzzzzzzzc-places.js)
  - The Fortress: the torch's light breathes and warms what is near it, dust drifts in it, and the view's corners
    fall into the dark.
  - Claudeita's cave: water drips from the roof about the hero and splashes where it lands, and the deep has a cold
    blue glow at its edge the farther down it goes.
  - Claudebros: the hour lies over the sky by the game's own clock - warm at dusk and dawn, a deep blue with stars at
    night - and clouds cross every kind of level.

Closer to hand (v63.0, UPGRADE_PLAN_58.md)
  (src/js/64zzzd-foemarks.js, src/js/76zzzzzzzzzzb-gui.js, src/js/74-fight.js, src/style.css)
  - In a fight each foe's row has a health bar (and its part's, below it) and its marks - asleep, held, marked,
    blinded, burning, chilled, warded, a broken part, what it carries, under the floor - as small tags with tooltips,
    in place of the run-on line of words.
  - In the pack a thing can be dragged onto a hero's card to give it; at the merchant's, onto the wares to sell it,
    or a ware onto the pack to buy it. The clicks work as they did.
  - A short fade into and out of the Mage Tower, the cave, the Fortress, Claudeablo, Claudebros and Claudecraft, in
    place of the cut.

The river's life (v62.0, UPGRADE_PLAN_57.md)
  (src/js/69zzl-waterlife.js, src/js/76zzzzzzzzzza-waterlife.js, src/js/40-render.js)
  - The banks in the water: where the Wood's trees or a wall stand over it, the river mirrors them - darker and
    greener under the trees - instead of the open sky.
  - Lily pads and duckweed lie in the slack water along the banks in the warm months: full in summer, some in spring
    and autumn, none in winter.
  - Dragonflies dart over the river on a summer's day; a pair of ducks on each of two slow stretches drifts down and
    paddles back up, dipping now and then - out by day, gone when the river is frozen.

Small life (v61.0, UPGRADE_PLAN_56.md)
  (src/js/69zzk-townlife.js, src/js/26k-washing.js, src/js/76zzzzzzzzzz9-townlife.js, src/js/26-surface.js, src/js/40-render.js)
  - Hens in the yards behind the townsfolk's houses: a few flocks wandering their yard and pecking by day, in from
    the rain and at night.
  - A cat on a fence top, a hedge or the well's kerb, a different perch every couple of hours; by the tavern's door at
    night, its eyes catching the light, and in the wet.
  - Pigeons roosting on the ring wall's walk and the roof ridges; they take wing when the party comes near and settle
    back a while after.
  - Washing hung out behind about half the houses - a line from the wall to a post in the yard, three or four cloths
    pegged along it - built into the town; none in winter.

Weather in the small things (v60.0, UPGRADE_PLAN_55.md)
  (src/js/24d-weather.js, src/js/76zzzzzzzzzz8-weather2.js, src/js/40-render.js)
  - A rainbow: on a rainy day, in the second hour after dawn and in the late afternoon, the cloud thins, the rain
    eases and a bow stands opposite the low sun, a fainter second bow outside it with its colours reversed.
  - Hoar frost whitens the ground on a clear or windy morning in winter or autumn, from an hour before dawn and gone
    two hours after it, glinting in the first sun; none under lying snow.
  - In the rain, drops run off the eaves of the town's houses.

The light of the hour (v59.0, UPGRADE_PLAN_54.md)
  (src/js/24c-light.js, src/js/76zzzzzzzzzz7-light.js, src/js/40-render.js)
  - The sun's light has a colour now: gold on the sunward walls and the ground at dawn and dusk, white at noon,
    silver-blue under the moon; the sky warms about the low sun and cools on the far side of it.
  - Mist lies on the water and its banks at dawn - thickest in autumn and spring, little in summer - and off the
    water again on autumn and spring evenings; none in rain or snow.
  - At night the lamps and the lit windows wear halos in the damp air: wide and soft in mist and rain, a faint one
    on a clear night.
  - Fixed: moss grew on a barrel or the well standing against a wall; it keeps to the walls themselves now.

Built in time (v58.4, UPGRADE_PLAN_53.md phase 3)
  (tests/run.js)
  - A test now holds the town and the Deep Wood to their time and size: each built whole at High detail in well under
    a second and a half, and under 300,000 vertices, so a change that makes them heavier is caught.
  - A look round every place after the visual updates - the Square by day and night, the West Gate, the Keep-yard, the
    Wood and its river, the dungeon, the yards at dusk - found nothing more to put right.

Detail governs the details (v58.3, UPGRADE_PLAN_53.md phase 2)
  (src/js/40-render.js, src/js/26e-wooddetail.js, src/js/26i-wall.js, src/js/26-surface.js)
  - Settings > Detail now governs the built details as well as the scattered ones - it never reached them before.
    Low leaves out the window sills and lintels, the rooflines, the kerbs, the stains and ivy, and the Wood's roots,
    stumps and rocks; Medium has fewer roots, stumps and rocks and no ivy on the town wall; High has everything. The
    fences, the well, the lamps, the battlements, the gate and the shaft head stand at every setting.

Automatic and the badly hurt (v58.2, fix (asked 2026-11-05))
  (src/js/62-combat.js)
  - Fixed: playing on Automatic, a fight could stick for good once anyone fell below half their health - the log
    filling with "The party fights on by itself" and "Someone is badly hurt: Auto stops, and waits for orders" by
    turns, and no one acting. The fight's Auto stopped to wait for you, and Automatic turned it straight back on.
    While Automatic plays, Auto plays on (it heals anyone under a third and drinks what it needs); pressing A
    yourself, Auto still stops for you when someone is badly hurt.

Details within reach (v58.1, UPGRADE_PLAN_53.md phase 1)
  (src/js/26-surface.js, src/js/40-render.js)
  - The small built details are drawn only as near as they can be seen: the trees' roots, the stumps and the rocks
    within 12 squares, lamp posts within 16, the windows' sills and lintels, the doors' frames and the raised
    timbers within 18, the fences within 28. Farther off the painted walls carry them, and there's less to draw.
  - Fixed: the moss of v57.4 greened the feet of everyone in town, the well and the barrels - it keeps to the walls now.

Lighter meshes (v58.0, UPGRADE_PLAN_53.md phase 0)
  (src/js/26e-wooddetail.js)
  - The town and the Deep Wood are lighter to draw: the trees' roots are built only on the trees beside an open
    square - the ones you can walk up to - and not deep in the forest where their feet are never seen. The Wood has
    40% less to draw, the town 18%, and both are built a quarter faster.

Weathering (v57.4, UPGRADE_PLAN_52.md phase 4)
  (src/js/76zzzzzzzzzz6-weather.js, src/js/40-render.js, src/js/26b-buildings.js, src/js/26-surface.js, src/js/26i-wall.js, src/js/76zzzzzzzzzz-buildings.js)
  - The town has weathered: moss creeps up the feet of its walls in patches (more in a wet spring or autumn, less in
    a dry summer), stains have run down the plaster from under the window sills, and ivy climbs some house walls and
    stretches of the town wall, thick at the foot and thinning as it climbs.

The shaft head (v57.3, UPGRADE_PLAN_52.md phase 3)
  (src/js/26j-shaft.js, src/js/26-surface.js)
  - The shaft in the Keep-yard is built up now: a low kerb of dressed stone round the hole, and over it a winch -
    two timber A-frames, the windlass drum on its axle between them with a crank, and the rope wound on it running
    down into the dark. Step onto the square to climb down as before.

The West Gate (v57.2, UPGRADE_PLAN_52.md phase 2)
  (src/js/26i-wall.js, src/js/26-surface.js)
  - The West Gate is an archway now, not a gap between the towers: two thick jambs, a round arch over the road with
    its stone soffit, the stonework above it to a capped top and three merlons - and the portcullis hanging under it.

Buttresses and arrow slits (v57.1, UPGRADE_PLAN_52.md phase 1)
  (src/js/26i-wall.js, src/js/26-surface.js)
  - Buttresses lean against the town wall's inner side, one square in three: stone piers with their tops sloping
    down and away from the wall.
  - The gate towers have arrow slits: one in each of their eight faces, high and low by turns, a dark slot in a
    dressed stone surround.

Battlements (v57.0, UPGRADE_PLAN_52.md phase 0)
  (src/js/26i-wall.js, src/js/26-surface.js)
  - The town wall is battlemented now: along both edges of its walk a low parapet, and on it two merlons a square
    with the crenels between to see through, capped in the walk's stone and turning the corners where the wall
    does - seen from the streets as well as from outside.

Hanging signs (v56.4, UPGRADE_PLAN_51.md phase 4)
  (src/js/76zzzzzzzzzz5-signs.js, src/js/40-render.js, src/js/80-main.js)
  - Each building's sign hangs out from the wall now instead of lying flat on it: two short iron arms, a rod between
    them, and the board facing the street - still easy to read - swinging out and back on the rod in the wind (still,
    with reduced motion asked for).

Lamp posts (v56.3, UPGRADE_PLAN_51.md phase 3)
  (src/js/26h-lamps.js, src/js/76zzzzzzzzzz4-lamps.js, src/js/26-surface.js, src/js/80-main.js)
  - The town's lamps are built now: a stone plinth, a tapering iron post with its collars, and a lantern's cage with
    corner bars, a little roof and a finial. The glass glows warm, and a soft pool of light spreads on the ground
    beneath, once the lamplighter has been round to light that lamp - and goes dark again when he snuffs it at dawn.

Fences and hedges (v56.2, UPGRADE_PLAN_51.md phase 2)
  (src/js/26g-fences.js, src/js/26-surface.js, src/js/76zzzzzzzzzz-buildings.js)
  - The town's fences are built now instead of painted round their squares: a post in each, two rails running on to
    the next, and pointed pickets with their own thickness, so a run of fence reads as one fence along its line.
  - The hedges have rounded, uneven crowns instead of flat lids. Both still stand in the way as before.

The well, built (v56.1, UPGRADE_PLAN_51.md phase 1)
  (src/js/26f-well.js, src/js/26-surface.js, src/js/40-render.js, src/js/80-main.js)
  - The Square's well is built now instead of painted: a round wall of dressed stone with a capstone rim, dark water
    down inside that ripples like the river, two posts carrying a little shingled roof, the windlass across them
    with its crank, and a bucket on its rope. Step onto its square to draw water as before; while you stand there it
    folds out of the way.

The market's furniture (v56.0, UPGRADE_PLAN_51.md phase 0)
  (src/js/76zzzzzzzzzz3-furniture.js)
  - The town's furniture is made the way it would be: a crate has corner posts, rims and a brace across each side,
    and now and then another crate on it; a barrel has four hoops and its lid set in the rim, and some stand open
    with apples or cabbages in them.
  - A cart has spoked wheels - a rim, a hub and six spokes, standing the right way at last - and a load of sacks or
    hay. A market stall has a scalloped edge hanging from its awning, a back shelf, and baskets of apples, cabbages,
    bread or folded cloth on the counter.

Dappled light (v55.5, UPGRADE_PLAN_50.md phase 4)
  (src/js/40-render.js, src/js/76zzzzzzzzzz2-dapple.js)
  - In the Deep Wood by day the sun comes through the leaves in soft patches of light and shade on the forest floor,
    drifting slowly as the breeze moves the crowns - most under and beside the trees. Full on a clear day, softer
    under cloud, faint in the rain, none at night or at Low detail.

River banks (v55.4, UPGRADE_PLAN_50.md phase 3)
  (src/js/40-render.js, src/js/27-props.js)
  - The river in the Deep Wood has banks: dark wet mud from the water's edge, fading into the grass or the forest
    floor in a ragged line, and a thicker fringe of reeds along it.
  - Fixed: the grounds' blending (v54.0) painted the grass beside the river onto the water itself.

Roots, stumps and rocks (v55.3, UPGRADE_PLAN_50.md phase 2)
  (src/js/26e-wooddetail.js, src/js/26-surface.js, src/js/76zzzzzzzzzz-buildings.js)
  - The trees of the Deep Wood stand in the ground: four to six roots spread from the foot of every trunk, each its
    own length and way, paler under the birches.
  - The forest floor has things in it: here and there beside the trees a low stump, its cut top showing the rings,
    and rocks half sunk in the moss and the litter - never on a path, a door or anything to use.

The Mage Tower in focus (v55.2, fix (asked 2026-11-03))
  (src/js/80-main.js)
  - Fixed: the Mage Tower was out of focus the whole way up. The soft blur behind the Tower's doors window, the
    Wood's weather on the lens and its fires' shimmer froze on the view as the hero went in, because the Tower's
    frames don't run the step that fades them. They are cleared now on going into the Tower - and into the caves,
    the Fortress, Claudeablo, Super Claude Bros and Claudecraft, which had the same fault.

Tracks (v55.1, UPGRADE_PLAN_50.md phase 1)
  (src/js/40-render.js)
  - The narrow earth paths of the land are tracks now: two ruts worn into them where the wheels and feet go, a ridge
    of grass down the middle, and the edges grown over with whatever lies beside them - grass, moss or leaf litter.

The forest floor (v55.0, UPGRADE_PLAN_50.md phase 0)
  (src/js/26d-forestfloor.js, src/js/26-surface.js, src/js/40-render.js)
  - In the Deep Wood the grass gives way under the trees: deep among them the floor is leaf litter, or needles among
    the pines; at the trees' edge it is moss; and the open grass begins only where they fall back, each blending into
    the next. Only the picture: the ground underfoot is as it was.

The season on the ground (v54.4, UPGRADE_PLAN_49.md phase 4)
  (src/js/40-render.js, src/js/76zzzzzzzzzz1-groundseason.js)
  - In autumn the fallen leaves drift against the walls and the kerbs, more of them as the season turns.
  - In winter the snow settles along the walls and the edges first, filling the open ground last.
  - While it rains, and the morning after, the earth of the paths and the worn grass go to mud.

Grounds that vary (v54.3, UPGRADE_PLAN_49.md phase 3)
  (src/js/40-render.js)
  - The town's and the land's grounds no longer show their tiling over distance: large soft patches lie over them,
    lighter and darker, and the grass is greener or yellower in places.

Edging (v54.2, UPGRADE_PLAN_49.md phase 2)
  (src/js/26-surface.js, src/js/27-props.js)
  - Where the town's cobbles and flags meet grass or earth, a low kerb of dressed stone runs along the edge of the
    paving, and pebbles kicked off it lie in the grass along the seam.

Worn ground (v54.1, UPGRADE_PLAN_49.md phase 1)
  (src/js/26c-wear.js, src/js/40-render.js)
  - The grass of the town and the land is worn to earth where feet go: in patches along the ways people walk between
    the doors, at the doors themselves, round the well and the market, and by the Wood's gate, hut, farm and caves.

Grounds that blend (v54.0, UPGRADE_PLAN_49.md phase 0)
  (src/js/40-render.js, src/js/76zzzzzzzzzz0-groundblend.js)
  - In the town and the land the grounds no longer meet in hard straight lines: near the edge of a square its
    neighbour's ground fades in, half and half at the line, the edge wandering with the noise - grass running into
    the dirt of a path, cobbles into flags, moss into litter. Off at Low detail.

Rooflines (v53.6, UPGRADE_PLAN_48.md phase 4)
  (src/js/26b-buildings.js, src/js/26-surface.js)
  - The town's roofs: under the eaves a shadowed underside with the rafters' ends showing; on a roof three squares
    long or more a dormer on each side, with its window and its own little roof; and on about half the buildings a
    gutter along the eaves and a downpipe down a corner.

Timbers that stand out (v53.5, UPGRADE_PLAN_48.md phase 3)
  (src/js/26b-buildings.js)
  - The half-timbering of the town's houses stands out from the plaster now: the posts at each wall's ends, the
    middle post of a house wall and the beam under the eaves are timbers proud of the wall, their edges catching
    the light.

Doors in their frames (v53.4, UPGRADE_PLAN_48.md phase 2)
  (src/js/26b-buildings.js)
  - Every door in the town stands in its frame now: a stone step before it, and the jambs and the lintel of its frame
    standing out from the wall, catching the light - on the houses and the shops alike.

Claudecraft's picks (v53.3, fix (asked 2026-11-03))
  (src/js/64n-claudecraft.js, src/js/61k-gate.js)
  - Claudecraft's picks are a tier stronger, as in Minecraft: a stone pick takes copper and iron, a copper pick silver
    as well, an iron pick gold too.
  - Fixed: striking ore your pick could not take said bare hands would not break it, though a pick was in your hand.
    It says now which pick you have and which it wants - Silver ore: your stone pick will not bite it - it wants a
    copper pick, made at a workbench.

Shutters (v53.2, UPGRADE_PLAN_48.md phase 1)
  (src/js/26b-buildings.js, src/js/76zzzzzzzzzz-buildings.js)
  - The town's windows have shutters: a pair of boarded shutters with a Z brace, folded back against the wall
    beside each window, in the house's own colour - green, blue or red - and on about one window in six, closed.

Claudecraft's controls (v53.1, fix (asked 2026-11-03))
  (__init__.py, src/js/80-main.js, src/js/64n-claudecraft.js)
  - Fixed: in the desktop window blocks could not be broken and the mouse would not look about - the window refused
    the mouse capture Claudecraft asks for. It grants that now (and nothing else); and if the mouse still cannot be
    captured, a click digs and places all the same and dragging looks.
  - Fixed: a swimmer could not get out of the water - at the surface Space only bobbed them up and down. Space at the
    surface, or against a bank, now lifts them clear onto it, even a bank a block above the water.

Windows set into the wall (v53.0, UPGRADE_PLAN_48.md phase 0)
  (src/js/26b-buildings.js, src/js/76zzzzzzzzzz-buildings.js, src/js/26-surface.js)
  - The town's windows are no longer flat on their walls: each is set in - a stone sill standing proud below it, a
    timber lintel over it, and the reveals of its frame standing out at each side, catching the light - on every
    house, door and shop.

Brightness and contrast (v52.4, UPGRADE_PLAN_47.md phase 4)
  (src/js/76zzzzzzzzz9-picture.js)
  - Settings has two sliders for the picture of the world itself: its brightness (60% to 160% - the dark floors
    lighter on a dim screen, or darker in a bright room) and its contrast (70% to 140%), beside the text size and the
    high contrast that were there. Only the view changes; the windows and the words are left as they are.

Photo mode (v52.3, UPGRADE_PLAN_47.md phase 3)
  (src/js/76zzzzzzzzz8-photo.js)
  - From the pause menu, or Shift+P on the floor, the interface goes away and the camera is freed a little: the arrow
    keys turn it and lean it about the party's square, A and D step it aside, Q and E raise and lower it, and Space
    or Enter saves the picture as a .png named for the place. Escape puts everything back. The game stands still.

Depth of field, deeper (v52.2, UPGRADE_PLAN_47.md phase 2)
  (src/js/76zzzzzzzzz7-dof.js)
  - The view behind an open window, soft since v31.3, now goes fully out of focus and draws back into shadow at its
    edges, so the window stands clearly in front of the world; it comes back sharp as the window closes.

Going down (v52.1, UPGRADE_PLAN_47.md phase 1)
  (src/js/76zzzzzzzzz6-descent.js)
  - A change of floor is no longer a cut: going down, the view sinks and dims to black and the new floor rises up
    into it out of the dark; going up, the other way; through a door into the town or a house, a short fade. With
    reduced motion, only a fade.

A Stone interface (v52.0, UPGRADE_PLAN_47.md phase 0)
  (src/js/76zzzzzzzzz5-stoneui.js)
  - The windows, the buttons and the panels are dressed to match the look: dark carved stone, framed in iron with a
    rivet at each corner of a window, and the buttons set into it like stone blocks that take a warm edge of
    torchlight when the pointer is on them. The colours of the words are as they were.

Weather on the surfaces (v51.4, UPGRADE_PLAN_46.md phase 4)
  (src/js/40-render.js, src/js/76zzzzzzzzz4-wetsurfaces.js)
  - While it rains, the rain is seen running down the town's walls in streaks.
  - The morning after a rainy day the cobbles and the walls are still wet - darker, shining a little - drying as the
    day warms, dry by early afternoon, with the puddles.

Crowds that move (v51.3, UPGRADE_PLAN_46.md phase 3)
  (src/js/76zzzzzzzzz3-crowds.js)
  - By day Caer Duin's streets have people going about them: a handful of townsfolk walking from one door to another
    - the tavern, the merchant's, the smith's, the Library, the Temple, the Guildhall, the Square - pausing at each,
    then setting off again; more at midday, fewer at dusk, none in the small hours.
  - Only seen: they are not in the way, and the ones to talk to stand where they always did.

Water to see (v51.2, UPGRADE_PLAN_46.md phase 2)
  (src/js/76zzzzzzzzz2-puddles.js)
  - The puddles of a rainy day no longer vanish when it stops: the next morning they still lie in the roads and
    paths of the town and the land - the same ones, holding the sky - and dry away, shrinking, as the day goes on,
    gone by early afternoon.

Real distance (v51.1, UPGRADE_PLAN_46.md phase 1)
  (src/js/76zzzzzzzzz1-farhills.js, src/js/26-surface.js)
  - Beyond the treeline round the town and the land stand two rings of hills more, a near range and a far one,
    paler for the air between, so the world goes back in layers to the edge of seeing.
  - Fixed: the distant views of v24.4 - the town on its hill seen from the land, the Mage Tower seen from the town -
    were never drawn: a name in the far ring's code hid the picture of them. They stand on the skyline now.

Building variety (v51.0, UPGRADE_PLAN_46.md phase 0)
  (src/js/26-surface.js)
  - Caer Duin's houses are no longer all one wash: each building has its own, a little lighter or darker than its
    neighbours, so a street reads as houses and not one long wall. (The trades already hang their signs at their
    doors.)

Idle life (v50.4, UPGRADE_PLAN_45.md phase 4)
  (src/js/76zzzzzzzzz-idlelife.js)
  - A monster at rest is never quite still: it breathes, a slow rise and settle; shifts its weight from one foot to
    the other every few seconds; and now and then looks round - toward the party when a hero acts in a fight, or
    after the party's own noise on the floor. Not with reduced motion asked for.

The great ones, tall (v50.3, UPGRADE_PLAN_45.md phase 3)
  (src/js/76zzzzzzzzy-tallguardians.js)
  - A guardian or the Lich King stands as tall as the room lets it - its head near the ceiling, taller still in a
    tall hall, and broader with it - so it looms over the party where before it stood little higher than an orc.

Wear (v50.2, UPGRADE_PLAN_45.md phase 2)
  (src/js/76zzzzzzzzx-wear.js)
  - A monster shows what the fight has done to it: below two-thirds of its life it is marked - cracks across plate,
    shell and bone, rents in hide, cuts in flesh, by what it is made of - and below a third badly so, more of them
    and deeper, darkened as with blood or soot.

Feet on the stone (v50.1, UPGRADE_PLAN_45.md phase 1)
  (src/js/76zzzzzzzzw-feet.js)
  - A monster stands on the floor rather than floating over it: a small, dark contact shadow right under its feet,
    under the long one the light casts - tighter and darker for the heavy, wider for the big - in a fight as on the
    floor. On a dais, a stair or down in a pit it stands on that. Ghosts and wisps float, and keep only a faint one.

Seen from three sides (v50.0, UPGRADE_PLAN_45.md phase 0)
  (src/js/76zzzzzzzzv-threesides.js)
  - A monster seen from behind is its back now - no face, no eyes, no teeth, the head and shoulders in its own body's
    colour, turned away - and from the side it is lit along its leading edge and falls into shadow behind, where
    before the front picture was only darkened.

Day reaching in (v49.4, UPGRADE_PLAN_44.md phase 4)
  (src/js/76zzzzzzzzu-daylight.js, tests/smoke.js)
  - On the first three floors, by day, the town's grates let the day down: an iron grate here and there in a
    corridor's ceiling, a shaft of daylight under it and the grate's shadow laid in a bright lattice on the floor -
    and the foot of the shaft on the first floor stands in the light from above.
  - Brightest on the first floor and fainter each floor down, by the hour, and greyer under cloud or rain.
  - The browser test waits for the title card to go rather than a fixed moment (a slow machine is busy building the
    art for its first seconds).

Glints (v49.3, UPGRADE_PLAN_44.md phase 3)
  (src/js/76zzzzzzzzt-glints.js)
  - Metal, gold and gems catch the light as the party passes: a small star flashing on a chest's bands, a strongbox,
    a key, and in a fight on a foe in plate or crystal - each glint at its own angle, so it comes and goes as the eye
    moves or turns, the way a real one does. Not with reduced motion asked for.

Low fog (v49.2, UPGRADE_PLAN_44.md phase 2)
  (src/js/40-render.js, src/js/76zzzzzzzzs-lowfog.js)
  - Mist lies low below ground: a thin skin over every floor, deeper where the floor goes down, so the pits and the
    sunk halls fill with it - thicker in the dank bands (the Flooded Vaults, the Drowned Town, the Fungal Deep, the
    Ossuary, the Root). It drifts slowly, stirs as the party moves through it, and takes the torch's light.

Bounced light (v49.1, UPGRADE_PLAN_44.md phase 1)
  (src/js/40-render.js, src/js/76zzzzzzzzr-bounce.js)
  - What the torch lights on the floor it throws back up: the foot of the walls takes a warmth in the floor's own
    colour, fading as they rise, and the ceiling a little of it - a red floor reddening the stone, a pale one
    lightening it. Below ground only.

Shadows from the walls (v49.0, UPGRADE_PLAN_44.md phase 0)
  (src/js/40-render.js, src/js/76zzzzzzzzq-lightshadow.js)
  - The lamps, wall torches, braziers and spell-lights no longer shine through stone: where a wall stands between a
    light and what it would light, its light stops, softly at the edge, so a torch round a corner lights only its own
    side of it. The eight nearest lights are traced; the party's own torch sees what the party sees. Off at Low detail.

Floor detail (v48.4, UPGRADE_PLAN_43.md phase 4)
  (src/js/40-render.js, src/js/76zzzzzzzzp-worn.js)
  - Below ground the floor shows how it has been walked on: a path worn paler and smoother down the middle of every
    corridor and room, away from the walls where feet don't go.
  - And the joints of its flags, two to a square and staggered, faint in the stone. Not in the town or the Wood.

Trim (v48.3, UPGRADE_PLAN_43.md phase 3)
  (src/js/26-surface.js, src/js/76zzzzzzzzo-trim.js)
  - The dungeon's walls stand on a course of dressed skirting stones, a hand's height, set a little proud of the wall
    so the torch catches their top.
  - Every doorway and gate has a stone lintel across its head under the ceiling.

Wall variety (v48.2, UPGRADE_PLAN_43.md phase 2)
  (src/js/26-surface.js, src/js/76zzzzzzzzn-wallvariety.js)
  - The photographed walls no longer repeat square after square: each wall square is mirrored or not, and a little
    lighter or darker, by a hash of where it is.
  - Two marks more in every band, with the cracks, the moss, the damp and the soot: a patched stone - a newer block
    mortared in, paler than the rest - and a stain, a dark run down from above where water or worse has come through.

Wet stone and dry dust (v48.1, UPGRADE_PLAN_43.md phase 1)
  (src/js/40-render.js, src/js/76zzzzzzzzm-dampdust.js)
  - The Flooded Vaults and the Drowned Town are damp: their stone darker, streaked where the water runs down the
    walls, and shining broadly where the torch catches it - and so is any floor the party wades.
  - The Ossuary is dry: a pale dust lies on its floors and on all that faces up, and nothing in it shines.

Relief on the walls (v48.0, UPGRADE_PLAN_43.md phase 0)
  (src/js/40-render.js, src/js/76zzzzzzzzl-relief.js)
  - The Stone look's photographs take their relief a third more strongly - each stone standing a little further out of
    the wall for the torch to catch - and their cavities, the mortar between the stones and the pits in them, are
    shaded from what is round them in the picture itself, so the joints read as sunk and the faces as standing proud.

High ground (v47.4, UPGRADE_PLAN_42.md phase 4)
  (src/js/69zzj-highground.js)
  - In a fight where the party stands a step or more above its foes - a dais, a gallery, a stair, the raised room -
    its blows land a tenth more often and the foes' a tenth less; standing below them, the other way about.
  - A Ranger shooting down from above has a little more still, and the fight's first line says who holds the high
    ground.

Galleries (v47.3, UPGRADE_PLAN_42.md phase 3)
  (src/js/69zzi-levels.js, src/js/76zzzzzzzzk-levels.js)
  - About half the tall halls five squares or more a side are galleries now: the edge a walk at the corridors' level
    behind a stone balustrade, open at the middle of each side, and the hall below it stepping down in tiers to a
    floor well under the party's feet - to be looked down into from the walk.

Tall halls and crawlways (v47.2, UPGRADE_PLAN_42.md phase 2)
  (src/js/69zzi-levels.js, src/js/26-surface.js, src/js/76zzzzzzze-ceilings.js)
  - The great rooms - twenty squares or more - stand tall now, under a ceiling half as high again, their ribs, beams,
    chains and cobwebs up under it.
  - On about a floor in three a short run of corridor is a crawlway, its ceiling low over the party's heads, stepping
    down to it and up again.

Stairs (v47.1, UPGRADE_PLAN_42.md phase 1)
  (src/js/69zzi-levels.js)
  - On about half the floors one room stands raised, its ceiling raised with it, and every corridor into it climbs
    to it as a flight of stone steps, a step a square - the eye going up them and down them as the party walks.

Daises and pits (v47.0, UPGRADE_PLAN_42.md phase 0)
  (src/js/69zzi-levels.js, src/js/76zzzzzzzzk-levels.js, src/js/26-surface.js, src/js/40-render.js)
  - The dungeon has height now. About one plain room in five has a raised dais in its middle and about one in nine a
    sunken pit, with stone step faces between the levels; a band's landmark stands its centrepiece on a dais.
  - The room's edge stays at the corridors' level, so every way in meets it; what stands on a dais stands on it and
    what is in a pit is down in it; the eye climbs the step and goes down into the pit as the party walks.
  - On the map a dais is lighter and a pit darker. Each square has one floor and one ceiling - no room over another -
    and the moves and the saves are as they were.

Dynamic quiet (v46.4, UPGRADE_PLAN_41.md phase 4)
  (src/js/76zzzzzzzzj-quiet.js)
  - While the party creeps through the dungeon with its light shaded (Douse), the music falls away to almost nothing
    over a few seconds and the dungeon's own sounds are left.
  - When a fight starts out of that quiet - found - a sting strikes, a drum and a brass chord rising, and the music
    swells back up. Lighting up again brings it back gently.

Interface sounds (v46.3, UPGRADE_PLAN_41.md phase 3)
  (src/js/76zzzzzzzzi-uisounds.js)
  - A soft click under every button; a page turned when a book-like window opens or one of its pages is chosen (the
    Journal, the codex, the plates, the lore, the library); a soft thump for the other windows; the map unrolling and
    rolled up again; and coins clinking when gold changes hands in a window.
  - At the Interface slider's level in Settings.

Sound cues (v46.2, UPGRADE_PLAN_41.md phase 2)
  (src/js/76zzzzzzzzh-cues.js)
  - Two new settings for those who play by ear. Sound cues gives three tones of their own: a falling warning when a
    trap the party knows of is close ahead, a rising chime when a chest, a key or a find comes within a few steps,
    and a slow pulse when a hero falls below a quarter of their health.
  - Say the cues aloud speaks them too - Trap ahead, A chest nearby, Mira is badly hurt - in the computer's own voice.

Spatial sound (v46.1, UPGRADE_PLAN_41.md phase 1)
  (src/js/76zzzzzzzzg-spatial.js, src/js/76zzzzq-sound3d.js, src/js/76zzzzzzzzd-distant.js)
  - With Headphones ticked in Settings, the sounds that come from a place are placed around the head instead of only
    left and right: a monster heard behind is behind, and the distant sounds come from all round, from above (drips,
    chimes) and from below (the Root's groan, grinding stone).

A mixer (v46.0, UPGRADE_PLAN_41.md phase 0)
  (src/js/76zzzzzzzzf-mixer.js, src/js/76zzzzzzzzc-weathersound.js, src/js/76zzzzzzzzd-distant.js, src/js/76zzzzzzzze-firesound.js)
  - Settings has a slider for each kind of sound under the sound's own volume and the music's: Voices (the heroes,
    the monsters, the town, the ghosts, those who come along), Ambience (the dungeon's air, the weather, the distant
    sounds, the fire) and Interface (the windows' own sounds). Kept with the other settings.

Fire (v45.4, UPGRADE_PLAN_40.md phase 4)
  (src/js/76zzzzzzzze-firesound.js)
  - The party's torch crackles - quietly while it is new, louder and more fitfully in its last forty steps, and not
    at all when it is doused or a lantern is carried.
  - A lit brazier roars as the party comes near it; the Foundry's vents, and anything burning, bubble and pop like
    lava.

Distant sounds (v45.3, UPGRADE_PLAN_40.md phase 3)
  (src/js/76zzzzzzzzd-distant.js)
  - Below ground the dungeon is heard from beyond the walls every ten seconds or so, from a side of its own, muffled
    and echoing: water dripping into pools, a roar far off, stone grinding somewhere.
  - And each band's own: the Flooded Vaults dripping more, hammers far away in the Dwarven Halls and the Foundry,
    the Crystal Caverns chiming, the Ossuary's bones clattering, the Root groaning deep down.

Water and weather (v45.2, UPGRADE_PLAN_40.md phase 2)
  (src/js/76zzzzzzzzc-weathersound.js)
  - Above ground the weather is heard: rain as a hiss, pattering on the roofs near the houses and dripping fat from
    the leaves under the trees; the wind in gusts as strong as it is; and snow hushing everything, the ambience let
    down while it falls.
  - Below, wading is heard by its depth - a light splash in a puddle, a slosh to the knee on a flooded floor or in
    the tide - and standing in water, it laps.

Doors, locks and traps (v45.1, UPGRADE_PLAN_40.md phase 1)
  (src/js/76zzzzzzzzb-foley.js)
  - Each has its own made sound now, laid over the old one: a door's creak and its latch, a key turning and a bolt
    drawn, a chest's lid on its hinge, a lever's ratchet and clunk, a portcullis's chain running up, a slam, stone
    grinding, a trap's spring and snap.
  - The big ones echo - longer in the great halls (the Dwarven Halls, the Palace, the Foundry, the Joker's) and
    shorter in caves and the houses.

Materials (v45.0, UPGRADE_PLAN_40.md phase 0)
  (src/js/76zzzzzzzza-materials.js)
  - A blow sounds like what it lands on, under the hit's own sound: a blade rings on plate, cracks on shell and
    crystal, crunches on bone, thuds into hide and slaps into flesh, and only whistles through the bodiless.
  - An arrow lands with a wooden thunk before it; a weak spot struck is louder and brighter; crates and barrels
    knock like wood. Each from the side the foe stands on.

Stone, the one look (v44.6, fix (asked 2026-11-02))
  (src/js/36-looks.js, src/js/60-game.js, src/js/70-ui.js, src/js/80-main.js, src/js/76zzza-walk.js, pack.py, src/js/35-packs.js)
  - Stone is the only look now, and the default. Pixel built its own set of pictures and kept missing ones added
    later - the Gilded Joker's tables and counters were not drawn in it at all - so it is gone, and a save that chose
    Pixel (or the old Drawn) opens in Stone. With one look there is nothing to choose: the Theme pickers on the title
    and in Settings are put away.
  - The Pixel tiles are left out of the built file (it is smaller by about 350 KB); they stay in src/art/pixel.
  - The Joker's tables are added to any set of pictures, whatever builds it.

The Joker's hall, full (v44.5, fix (asked 2026-11-02))
  (src/js/80-main.js, src/js/76zzzzzzzz0-jokerlight.js)
  - Fixed: the Gilded Joker's hall looked nearly empty from its door - things on a floor were drawn only within twelve
    steps of the party, and the hall is one great room, so most of its fifty-five tables and seventeen counters were
    left out. On the Joker's floor the whole hall is drawn now.
  - Chandeliers hang over the hall in rows, each a warm light, so the far tables are not lost in the dark.

A music room (v44.4, UPGRADE_PLAN_39.md phase 4)
  (src/js/76zzzzzzzz-musicroom.js)
  - The party's house has a music room from its first level: every tune ever heard, on any run, kept by name and
    played there on asking - the bands' themes, the guardians' and the Lich King's, the fight, the camp, the town by
    the hour, the Joker's lounge, the title, the end, and the motifs.
  - What was playing comes back when the room is left.

Leitmotifs (v44.3, UPGRADE_PLAN_39.md phase 3)
  (src/js/76zzzzzzzy-leitmotifs.js)
  - Three themes come back when they matter, over whatever is playing: the party's - four notes rising, a horn's
    call - on going down into a new band and when a guardian falls; the Lich King's - a falling minor line with a
    tritone in it - on first coming into his Palace, woven quietly into the Palace's own tune now and then, and
    turned to the major when he falls; and the Joker's - a chromatic little waltz - on coming onto his floor.

Town music by the hour (v44.2, UPGRADE_PLAN_39.md phase 2)
  (src/js/76zzzzzzzx-townmusic.js)
  - Caer Duin has tunes of its own now, by the clock: a flute over the rooftops in the morning, a busy lute and a
    tambourine through the middle of the day, the tavern's fiddle over a drone from dusk to late, and in the small
    hours only a few soft notes, far apart. Inside the Hanged Lantern it is always the fiddle.
  - The tune changes as the hour turns, the old fading under the new. (The town had been playing the Catacombs' tune.)

Boss themes (v44.1, UPGRADE_PLAN_39.md phase 1)
  (src/js/76zzzzzzzw-bossmusic.js)
  - Each guardian and the Lich King has a battle theme of its own in place of the one shared boss tune: the Rat King's
    scurrying chromatic run, the Drowned Knight's slow march, the Drowned Queen's waltz, the Crystal Tyrant's bright
    cruel Lydian, the Bone Patriarch's dirge, the Lich King's own, and the rest - its band's instrument doubling the
    lead once the fight turns hard.
  - When it turns at half its life the theme turns with it: faster, a step higher, a double kick on the drums.

A theme for every band (v44.0, UPGRADE_PLAN_39.md phase 0)
  (src/js/76zzzzzzzv-bandmusic.js)
  - Each band's tune is played on its own consort now: the Catacombs by a low choir with a bell at each change of
    chord; the Flooded Vaults on a glass harmonica, water dripping; the Dwarven Halls on a hammered dulcimer over a
    horn, an anvil keeping time; the Palace on a harpsichord over an organ; the Drowned Town on a music box out of
    tune, a bell far off; the Fungal Deep on a marimba with a hand drum; the Crystal Caverns on glass bells; the
    Foundry in brass with the anvils; the Ossuary on a bone xylophone over the choir; the Root in a throat's drone
    and a heartbeat.

Hireling chatter (v43.4, UPGRADE_PLAN_38.md phase 4)
  (src/js/76zzzzzzzu-chatter.js)
  - Those who come along make themselves heard now and then on the walk: the porter grunts under the pack, the
    torchbearer coughs in the smoke, a dog barks or whuffs, the wizard mutters to himself, the cut-loose adventurer
    hums, and the pony on the lead snorts. About one sound every half a minute, from behind the party.

Ghost whispers (v43.3, UPGRADE_PLAN_38.md phase 3)
  (src/js/76zzzzzzzt-whispers.js)
  - When the dead speak - a ghost on the floor, a vault's keeper telling its story - their words come with a whisper
    under them: breath shaped into syllables with no voice behind it, drifting from one side to the other and
    echoing a little, over a thin cold tone, as long as the words are.

Townsfolk murmur (v43.2, UPGRADE_PLAN_38.md phase 2)
  (src/js/76zzzzzzzs-murmur.js)
  - By day the Square talks: a low murmur of voices, a syllable here and a laugh there, from the side each comes
    from, louder the more townsfolk are about and the nearer the party is to the middle of it. At night it falls quiet.
  - Whoever the party speaks to in town says hello first: a two-note greeting in the speaker's own voice.

Monster voices (v43.1, UPGRADE_PLAN_38.md phase 1)
  (src/js/76zzzzzzzr-monvoices.js, src/js/76zzzzzzzq-voices.js)
  - Every kind has its own made voice in place of the few shared roars: the beasts growl, the small things shriek,
    the bones rattle, the serpents and the plants hiss, the walking dead moan, the big ones roar, the golems grind,
    and the people cry out like people - each kind pitched a little its own way.
  - Short and sharp when struck, long and falling at its death; the guardians deeper and longer. The Lich King keeps
    his own.

Hero barks (v43.0, UPGRADE_PLAN_38.md phase 0)
  (src/js/76zzzzzzzq-voices.js)
  - The heroes have voices now - no words, a throat: a grunt when a blow lands on them, a shout on a weak spot struck,
    a long cry as one falls, a whoop at a new level.
  - Each hero's voice is pitched by calling (a Knight's low, a Mage's light) and a little by name, so the four sound
    like four, and each comes from its own side of the party.

Ending scenes (v42.4, UPGRADE_PLAN_37.md phase 4)
  (src/js/76zzzzzzzp-endcard.js, src/js/76zzzzzzzm-titletown.js)
  - A run's end opens on a painted card of how it ended: the place, in its band's own stone, seen down a corridor;
    the party along the front, those who stand standing and the fallen laid down and greyed; and what ended it at
    the back - the foe still standing, or for a won run the crown in a gold light - with a line saying where and by
    what.
  - The town behind the title (v42.1) now waits until the title has stood clear of its card for a moment before it
    builds, so the first key and a slow machine's start are not held up by it.

A map that remembers (v42.3, UPGRADE_PLAN_37.md phase 3)
  (src/js/76zzzzzzzo-mapmemory.js)
  - The parchment keeps the expedition's story in little ink sketches in the corner of each square it happened on:
    crossed swords where a fight was fought, an open box where a chest was emptied, a grave-cross where a hero fell,
    a tent and its fire where the party made camp.
  - Kept with the run, floor by floor (the newest sixty a floor), on the minimap and the big map alike.

Painted headers (v42.2, UPGRADE_PLAN_37.md phase 2)
  (src/js/76zzzzzzzn-headers.js)
  - Each of the town's windows opens under a painted strip of the place: the Tavern's hearth and mugs, the Smith's
    anvil throwing sparks, the Temple's altar under its rose window, the Alchemist's bottles and a flask bubbling,
    the Vault's coin-stacks and strongbox, the Library's shelves, the Guild's banners and notice board, the
    Chronicler's desk and quill, and the party's own hearth.

An animated title (v42.1, UPGRADE_PLAN_37.md phase 1)
  (src/js/76zzzzzzzm-titletown.js)
  - Behind the title the view is no longer a corridor turning on the spot: it drifts slowly up and down Caer Duin's
    longest street at the real hour, in the real season and under the day's own weather - the sky, the light, rain on
    the ground, snow - with the street's props standing about.
  - Leaving the title gives the renderer back the corridor's pictures, so whatever comes next finds things as it was.
    Reduced motion: the view stands still.

An illustrated bestiary (v42.0, UPGRADE_PLAN_37.md phase 0)
  (src/js/76zzzzzzzl-bestiary.js, src/js/76zzzzzzw-mondetail.js)
  - A new page of the Journal, Plates: every kind the party has met painted large on its own parchment plate, named
    in a fair hand, with the margins written up from what has been learned of it - where it lives, how many met and
    slain, what it fears and shrugs off, what it does, and its way once known.
  - A kind met but never slain is only sketched, in faded outline.
  - Fixed: the ink line round the Lich King's and the guardians' pictures (v39.0) turned the soft parts of them into
    black blots; it is drawn from the solid shape only now.

The dark that moves (v41.4, UPGRADE_PLAN_36.md phase 4)
  (src/js/76zzzzzzzk-creepingdark.js)
  - Where a floor's dark is magical it is not still: wisps of it stand at the edge of the party's light and lean in,
    creeping nearer and drawing back, and pools of it spread across the flags toward the torch.
  - A spell's light drives it back a way, a lantern holds it further off than a torch, and owl's eyes see it from
    further still.

Storm light (v41.3, UPGRADE_PLAN_36.md phase 3)
  (src/js/76zzzzzzzj-stormlight.js)
  - When a storm is over Caer Duin its lightning reaches down the shaft to the first floors: a cold flash whitening
    the stone, brightest by the shaft's foot and fainter each floor down - the third sees only a glimmer.
  - A while after each flash comes the thunder, muffled by the earth. Reduced motion keeps the flashes out.

Eyes in the dark (v41.2, UPGRADE_PLAN_36.md phase 2)
  (src/js/76zzzzzzzi-eyes.js)
  - A waking pack out past the torch's reach is a darkness with eyes in it: a pair for each that stands, at its head's
    height, in its kind's colour - cold blue for the dead, amber for beasts, red for the fiery and the demonic, green
    for the rest - blinking now and then.
  - The sleeping keep theirs shut and one that has turned its back shows none; as the party comes nearer the torch
    finds the rest of it.

Stained glass (v41.1, UPGRADE_PLAN_36.md phase 1)
  (src/js/76zzzzzzzh-stainedglass.js)
  - The Temple has windows now: three tall lancets down each side and a rose over the altar.
  - By day the glass glows and pools of coloured light lie on the floor and over the pews from whichever side the
    sun is on - the east windows in the morning, the west in the afternoon - sliding as it goes over. At night the
    glass is dark and only the candles light the room.

Moving shadows (v41.0, UPGRADE_PLAN_36.md phase 0)
  (src/js/76zzzzzzzg-torchshadows.js)
  - Below ground a shadow cast by a flame - the party's torch, a brazier, a wall torch - sways and breathes with it,
    turning a little this way and that and lengthening as the flame dips. The sun's shadows above stay still.
  - Pillars and the ends of walls now cast their own long shadows away from the party's torch, swaying the same.
    Reduced motion keeps them steady.

The town by season (v40.4, UPGRADE_PLAN_35.md phase 4)
  (src/js/76zzzzzzzf-townseason.js)
  - In winter snow lies on Caer Duin's roofs, icicles hang from the eaves and drifts bank against the walls.
  - In spring the window boxes are pink and white and blossom drifts down from the trees; in summer the boxes are red
    with geraniums; in autumn sheaves of the harvest lean by the walls, with pumpkins beside them.

Ceilings (v40.3, UPGRADE_PLAN_35.md phase 3)
  (src/js/76zzzzzzze-ceilings.js)
  - Stone ribs spring across the bays of halls and of any room of twenty squares or more; timber beams cross the
    cellar rooms and corridors of the Catacombs and the Dwarven Halls.
  - Chains hang from the dark in the Lich King's Palace, the Foundry and the Ossuary, swaying a little.
  - In the first two bands, by day, light falls through a broken place in the roof: a shaft of it, dust turning in
    it, and a pale patch on the floor.

Furniture by purpose (v40.2, UPGRADE_PLAN_35.md phase 2)
  (src/js/76zzzzzzzd-furniture.js)
  - A plain room below ground is now and then something: a library (shelves of books along its walls and a reading
    table), a guardroom (weapon racks, a table and a bench), a tomb (sarcophagi laid in a row) or a hall (banners on
    the walls and a long table down the middle). About four rooms in seven; the rest stay bare.
  - The furniture keeps off things, features and doorways and out of a band's landmark room, and never moves: it is
    chosen by the floor and the room.

Doors and gates that work (v40.1, UPGRADE_PLAN_35.md phase 1)
  (src/js/76zzzzzzzc-doors.js)
  - A found secret wall no longer just vanishes: the block grinds down into the floor over a second, dust bursting
    out at its foot.
  - A portcullis judders up its chains a notch at a time, grit sifting from the lintel while it moves; a door swings
    past and settles back on its hinge, with a puff of dust from under it as it gives. Reduced motion keeps them still.

Band landmarks (v40.0, UPGRADE_PLAN_35.md phase 0)
  (src/js/69zzg-landmarks.js, src/js/76zzzzzzzb-landmarks.js)
  - On the third floor of each band, the largest plain room is the band's landmark, told once when the party first
    steps in: the Candle Crypt, the Flooded Nave, the Forge-Hall, the Empty Throne, the Bell Square, the Fairy Ring,
    the Crystal Hall, the Great Crucible, the Skull Wall and the Heart-Root.
  - Each is drawn with a centrepiece and its own light: an altar banked with candles, a drowned saint in black water,
    a hammer working an anvil by itself, a throne between banners, a bell swinging in its frame, a great glowing cap
    in a ring, crystals lit from inside, a crucible pouring iron, a heap of skulls, a red root that beats.

Elite looks (v39.4, UPGRADE_PLAN_34.md phase 4)
  (src/js/76zzzzzzza-elites.js)
  - Champions, guardians and the Lich King stand in a ring of light on the floor, in the colour of what they are (a
    vampiric champion red, a warded one violet, a guardian its own, the king a cold blue), with motes rising from it.
  - In a fight the great ones' tread ripples the floor every few seconds, with a small shake; the auras show on the
    floor too, on bands within sight. Reduced motion keeps the ring and drops the motes and the ripple.

Status seen (v39.3, UPGRADE_PLAN_34.md phase 3)
  (src/js/76zzzzzzz-statuses.js)
  - In a fight, what ails a monster shows on it: bleeding or poisoned, green drips falling; asleep, Zs drifting up;
    held, vines round its legs; blinded, a dark band and a groping sway; chilled, frost spikes about its feet; burning,
    flames licking up; marked, a red sigil over it.

Spell shapes (v39.2, UPGRADE_PLAN_34.md phase 2)
  (src/js/76zzzzzzy-spellshapes.js)
  - Where a spell lands it leaves its school's mark, over its flight and flash: fire swirls up in a coil and leaves
    embers drifting; frost grows crystals in the air that hang and shatter; lightning branches from one foe to the
    next; holy light falls in rays from above; force rings out; the dark arts curl in smoke; growing things sprout.

Hit reactions (v39.1, UPGRADE_PLAN_34.md phase 1)
  (src/js/76zzzzzzx-hitreact.js)
  - A struck monster flinches away from the blow; a weak spot staggers it further back and tips it.
  - What the blow knocks off flies by what the monster is: sparks from plate, chips from shell and crystal, splinters of
    bone, tufts of hide, a spray of blood from flesh, cold motes from the bodiless. Not with Reduce motion.

Monsters, closer up (v39.0, UPGRADE_PLAN_34.md phase 0)
  (src/js/76zzzzzzw-mondetail.js (a detail pass over every monster picture, and its recoil frame))
  - Every monster picture gets a detail pass: fur strokes on beasts, scales on the scaled, rivets and plate seams on the
    armoured and the big, rags on the dead, a rim of torchlight down one side, a soft shadow below, and a dark ink line.
  - A painted recoil frame (thrown back, washed pale) shows in the instant a monster is struck.

Boss phases (v38.4, UPGRADE_PLAN_33.md phase 4)
  (src/js/69zzf-phases.js; 76zzzzzzv-phases.js (the card, the sting, the music held high))
  - At half its health each guardian without a second form, and the Lich King, changes once: the Drowned Queen calls her
    court, the Mycelial Mind puts the front row to sleep, the Crystal Tyrant grows a thicker carapace, the Foundry
    Master burns white (blows half again), the Bone Patriarch pulls himself together, the Root of the World puts out
    new shoots and hardens, the Bell-Founder's Boy rings the bell, and the Lich King's crown blazes - the dead rise round
    him and his blows grow harder. The three shallow guardians keep their own second forms.
  - Every change, theirs included, shows a card with the boss's name, sounds the entrance's sting, shakes the view, and
    holds the fight's music at its height to the end. This finishes plan 33 (set 5).

Surrender and parley (v38.3, UPGRADE_PLAN_33.md phase 3)
  (src/js/69zze-surrender.js; 76zzzzzzu-surrender.js (the choice answered; quarter given under Automatic))
  - Foes who can speak (kobolds, goblins, orcs, trolls, ogres, dark elves, imps, sellswords, hedge-wizards, hags,
    minotaurs, demons), all at a quarter of their health or less with the party mostly standing, now and then throw
    down their weapons, once a fight: "Quarter?" Spare them - they go, leaving their purse (no experience), and the
    heart lifts - or finish them, and they fight on the harder. Under Automatic the party gives quarter.
  - Kept between runs: how many of each kind were spared. A kind spared five times remembers - once a run, on a floor
    where they are, one of them slips the party the floor's map.

Monster habits (v38.2, UPGRADE_PLAN_33.md phase 2)
  (src/js/69zzd-habits.js; 76zzzzzzt-habits.js (the bestiary writes each kind's way))
  - Every kind has a habit, read from what it is - who it goes for, when it runs, what it does first ("it stands off and
    shoots at whoever is easiest to see - rush it", "it keeps the others standing - kill it first").
  - Once a party has slain five of a kind in an expedition it has their measure: the habit is told then and when a
    fight with them begins, and every blow and spell on that kind is a tenth harder. The Bestiary writes the habit for
    good once read.

Combos, more (v38.1, UPGRADE_PLAN_33.md phase 1)
  (src/js/69zzc-combos.js)
  - Four more combos, each from two blows one after the other on the same foe in a round, named the first time and kept
    with the rest in the Journal: the feint (a blow, then the Rogue's - as much again), the volley (a shot, then
    another's - half again), smite and sear (holy light, then fire - half again), hammer and anvil (the Knight's shield
    bash, then another's blow - a third again).

Positioning (v38.0, UPGRADE_PLAN_33.md phase 0)
  (src/js/69zzb-position.js)
  - A weapon with the reach word strikes from the back row at full, as a polearm in practised hands does.
  - A shield turns some of the blows aimed at the hero beside its bearer in the same row (a third of its own chance,
    for half).
  - Two heroes of the front row who strike the same foe in one round flank it: the second blow a fifth harder.

Scars kept apart (v37.5, UPGRADE_PLAN_29.md (a fix to phase 2))
  (src/js/69zj-scars.js, 76zzzzzzd-scars.js)
  - The game already had scars - the trait left by a third healed wound at the camp, kept as a list of names the temple's
    vigil reads. v34.2's near-death scars had been put in the same list, which could break the vigil and the sheet; they
    keep their own list now (a hero from those versions is sorted out when the run is loaded), and the sheet's Scars
    shows both kinds.

Secret floors (v37.4, UPGRADE_PLAN_32.md phase 4)
  (src/js/69zza-vaults.js; 76zzzzzzs-vaults.js (the stair, the keeper ghost, the vault named))
  - About one floor in nine from the fourth hides a stair under a flagstone in a quiet corner, found by searching the
    square (Space on it), by the hound within two squares, or by a Rogue passing beside it.
  - It leads down to a small hand-made vault - the Drowned Chapel, the Counting-House or the Sealed Library - its ghost
    keeper telling the story in three parts, one each time spoken to; heard out, the prize is given (the Bell-Rope
    Charm; the Ledger Ring and a hoard; the Reader's Circlet and two tomes). Once a run each. This finishes plan 32 (set 4).

Lost and found (v37.3, UPGRADE_PLAN_32.md phase 3)
  (src/js/69zz-lostfound.js; 76zzzzzzr-lostfound.js (the lost party's pack))
  - When an expedition ends in the dark, the best of what its heroes wore - four things at most, never cursed or a
    relic - stays where they fell, kept between runs (twelve at most). The first later expedition, on another seed, to
    come onto that floor finds it: a dusty pack with their names scratched on the buckle, and takes it home. Bringing
    lost gear home is a feat. (The same seed's remains and their ghost are as they were.)

The rival party (v37.2, UPGRADE_PLAN_32.md phase 2)
  (src/js/69zy-rivalband.js; 76zzzzzzq-rivalband.js (their chalk, a dropped bundle, one of theirs fallen))
  - Every run has its rivals, a named band of four going down ahead: their chalk on the walls one floor in three (Space
    reads it - their name and floor, their arguments, their tallies), something dropped in a hurry one floor in six,
    and from the fifth floor now and then one of their own, fallen, with what they carried (never the leader).
  - The rival parties met on a floor are this band now, named, with whoever of them still stands.

Puzzle rooms (v37.1, UPGRADE_PLAN_32.md phase 1)
  (src/js/69zx-puzzles.js; 76zzzzzzp-puzzles.js (the altar, statues, shaft, mirrors, plate and the beam drawn))
  - About one floor in five from the second holds a puzzle made fresh for it (always solvable). The statues: an altar
    and three stone figures about it, each turned a quarter at a time with Space (a worn arrow on the floor shows where
    each looks); when all three face the altar a chest rises beside it. The sunbeam: daylight down a crack in the roof,
    two mirrors on pins (Space tilts one the other way) and a sun-plate; the beam is drawn along the floor as it goes,
    and when it falls on the plate a chest rises there - better than the floor's own.

Floor moods (v37.0, UPGRADE_PLAN_32.md phase 0)
  (src/js/69zw-moods.js; 76zzzzzzo-moods.js (each mood's look); tests/run.js (the nodes test knows an overgrown floor grows two more))
  - About one floor in seven from the third down (by the run's seed; never a guardian's, a camp's or a special floor)
    has a mood, named as the party comes onto it and in the side panel. Flooded: water stands in a third of the halls,
    and the torch burns half again as fast. Overgrown: roots and vines on the walls, a green cast, and two more things
    growing to gather. Frozen: frost over everything, breath showing, glints - and the cold numbs the monsters' blows.
    Haunted: a pale fog, drained colour and wandering wisps; the dead are a sixth harder to put down, and the heart sinks.

The news board (v36.4, UPGRADE_PLAN_31.md phase 4)
  (src/js/69zv-crier.js; 76zzzzzzn-crier.js ("The Crier" in town, and on the court's noticeboard))
  - The Caer Duin Crier, a sheet a week: the week's expeditions and the deepest reached, the fallen remembered, a
    record broken, the South Fields' ribbons and takings, the Gilded Joker's wagered and paid, new legends on the Row,
    new plaques in the hall of feats, the town's works raised - or a quiet week, said so.
  - "The Crier" among the town's actions, and pinned to the court's noticeboard; the last eight weeks turned with the
    arrows. This finishes plan 31 (set 3).

Building the town (v36.3, UPGRADE_PLAN_31.md phase 3)
  (src/js/69zu-works.js; 76zzzzzzm-works.js ("Town works", the bathhouse, the watchtower and the banners drawn))
  - "Town works" among the town's actions: four works raised with gold and the island's timber and stone. The old wall
    repaired (banners along it, and every run sets out in better heart); a stone bridge for the Wood's plank one
    (flagstones over the river, the Wood walked a tenth quicker); a bathhouse on the south lane (a hot bath once a day -
    everyone mended, small ailments washed off, the heart lifted); a watchtower on the south green (from its top the
    whole Deep Wood goes on the map, its dens and caves with it). All four is a feat.

Townsfolk who remember (v36.2, UPGRADE_PLAN_31.md phase 2)
  (src/js/69zt-remember.js; 76zzzzzzl-remember.js (a greeting when the party steps beside a resident))
  - Stepping beside one of the six residents walking the town, they greet the party by its deeds - this run's depth
    and guardians, the last expedition's end, the best ever, the trophies on the wall, a legend on Legends' Row, the
    feats - once a day each.
  - One time in three a lead comes with it: a den the hound could find (or a hound that could learn to track), the
    trader due tomorrow, the season's trial still open, the still's pages lying about below, the festival games.

Festivals, kept (v36.1, UPGRADE_PLAN_31.md phase 1)
  (src/js/69zs-festgames.js; 76zzzzzzk-festival.js (the Square dressed, the jig, the games' window))
  - In a festival's week the Square is dressed: strings of bunting across it and paper lanterns, lit and glowing from
    dusk; a jig plays coming into town.
  - "Festival games" among the town's actions: the tug and the stone (Strength), the butts (Dexterity) and the
    riddle-tent (Intelligence), once each a festival - the best hero's stat and a throw against the mark. Each won pays
    gold and a little renown; all three take the festival's favour (a charm of every stat), once a year.

Market days (v36.0, UPGRADE_PLAN_31.md phase 0)
  (src/js/69zr-market.js; 76zzzzzzj-market.js (the stalls in the Square, the side panel's line))
  - Traders from away come to the Square, each on a fixed day of the run's week: Hrodna of the Deep Halls (fine arms
    and armour), Saffi from the East (rare herbs, rare seeds and spice), old Mott the tinker (wands, lamps, rings and
    amulets) - and on the seventh day, market day, all three and a bookseller with tomes, under striped awnings.
  - Their stock is the week's, dearer than the town's own, and bought through the shop as the peddler's is; the side
    panel says who is in the Square today.

The kennel and the stable (v35.4, UPGRADE_PLAN_30.md phase 4)
  (src/js/69zq-kennel.js; 76zzzzzzi-kennel.js (the kennel drawn, the animals in it, its window))
  - In town, in the corner south-east of the Keep-yard: a kennel and a stable, and the party's hound and pony in it
    while the party is in town (they don't follow it about the streets; the side panel says so).
  - Space at its gate: feed them (five gold, once a day: the party's heart lifts), give them new names, and teach the
    hound's tricks and fit the pony's gear, as at the farm. This finishes plan 30 (set 2).

A follower's fear (v35.3, UPGRADE_PLAN_30.md phase 3)
  (src/js/69zp-fear.js)
  - Coming to a new floor that is dark - the Lich King's palace and below, or with the light shaded - a hired follower
    (porter, torchbearer, hedge-wizard) may lose their nerve and bolt up the stair for good, if the party's heart is
    below Steady: likelier the lower it is, half as likely seasoned, a quarter as likely a veteran. When they are close
    to it they go quiet and keep near the light. The farm's dog never runs, nor the one you cut loose.

The pony's gear (v35.2, UPGRADE_PLAN_30.md phase 2)
  (src/js/69zo-ponygear.js; 76zzzzzzh-ponygear.js (the farm's window fits it))
  - Fitted at the farm: Saddlebags (twenty more carried on the land, besides the pony's thirty), a blanket (the snow no
    longer slows the party in the Wood - neither the extra minute a step nor the slower walk), and a cart (the fields'
    produce sells a tenth higher at the stall, and the silo can be sold from the fields themselves).

The hound's tricks (v35.1, UPGRADE_PLAN_30.md phase 1)
  (src/js/69zn-tricks.js; 76zzzzzzg-tricks.js (the farm's tricks, the den's mouth and way out))
  - Three tricks taught at the farm for gold: Fetch (after a fight some fled from, the hound brings back their coins and
    now and then a thing), Guard (no one catches the party napping, and a better night's rest at a camp) and Track.
  - Track: when a foe flees, the hound takes the scent to its lair - a den under the roots of the Deep Wood, up to three
    at once, each its own cave of that kind with the fled beast leading them and a hoard; cleared, it is gone.

Followers who level (v35.0, UPGRADE_PLAN_30.md phase 0)
  (src/js/69zm-followranks.js)
  - A follower who comes through five new floors is seasoned, through ten a veteran: four more health a rank, and
    better at their trade - the porter carries ten more a rank; the torchbearer cups the flame against a gust, then
    spots a trap a square off; the hedge-wizard mends twice a floor, then keeps her light half again as long; the
    farm's dog goes five floors deeper a rank. The rank is in their name on the side panel.

Retirement to Legends' Row (v34.4, UPGRADE_PLAN_29.md phase 4)
  (src/js/69zl-legends.js; 76zzzzzzf-legends.js (Legends' Row among the town's actions); 76zzzzzzb-fireside.js (an action button shown only while it applies))
  - A hero who reaches level fifty is offered it: to retire from the party to a house of their own on Legends' Row in
    town (six houses; the oldest legend moves on to make room). The guildhall's trainers and the house's study stay.
  - In town, Legends' Row among the actions: each legend's house, and a hero of the party sent in for a lesson, once a
    run - +1 to the legend's calling's own stat for good, and a hero of the same calling their first boon besides.
    This finishes plan 29 (set 1).

Letters home (v34.3, UPGRADE_PLAN_29.md phase 3)
  (src/js/69zk-letters.js; 76zzzzzze-letters.js (the Journal's Letters page))
  - A trip down is kept - the deepest floor, the slain, the guardians, the finds, who fell, the scars taken - and when
    the party comes up into the town, every hero standing writes a short letter home: to whom by where they come from,
    what they saw in their own calling's way, the new scar, the one lost, the friend still beside them.
  - The Journal's Letters page keeps them, the last eighty, each on its own sheet.

Scars and stories (v34.2, UPGRADE_PLAN_29.md phase 2)
  (src/js/69zj-scars.js; 76zzzzzzd-scars.js (scars on the portraits and in the sheet); 69za-enchant.js and 76zzzzzb-marks.js (a hash read signed, read whole))
  - A hero brought to a tenth of their health or less in a fight that is won keeps a scar - three at most: drawn on
    the portrait (a burn from fire), and written in the sheet with where it is, what gave it and on which floor.
  - Each scar is a small trait for good: Hardened, Watchful, Lucky to be Alive, or the double-edged Grim, Shaken and
    Slow to Heal. A fight fled leaves none. Three scars on one hero is a feat.
  - (A hash read as a signed number could leave a scar's place unnamed, the enchanter's offers lopsided and a mark
    off its square; read whole now.)

Bonds and rivals (v34.1, UPGRADE_PLAN_29.md phase 1)
  (src/js/69zi-rivals.js; 76zzzzzzc-sheetx.js (the sheet's rival, and CM.sheetExtra))
  - Old friends (forty fights side by side) now cover each other: a blow meant for a friend under a third of their
    health is, two times in five, taken by the other instead, if they're on their feet.
  - Rivals: killing blows are counted for every hero; two who have fought twenty-five fights together with fifteen
    kills or more each, and their counts close, become rivals - each finds a weak spot a twentieth more often while the
    other stands, the sheet keeps the score, and they argue it out at the fire.

Camp scenes (v34.0, UPGRADE_PLAN_29.md phase 0)
  (src/js/69zh-fireside.js; 76zzzzzzb-fireside.js (the fire, and CM.addAction for the actions row))
  - Coming into a camp, the four sit round the fire - painted, the fire alive, each in its light, the fallen's place
    left empty - and talk over what happened since the last camp: who is hurt, what was found, a guardian slain, how
    many fell to them, who fell, the purse, the torch. The lines are theirs, by who they are and what happened.
  - Once a camp (not under Automatic or a film); the camp's "Round the fire" button brings it back.

The daily challenge, scored (v33.3, UPGRADE_PLAN_28.md phase 3)
  (src/js/69zg-daily.js; 76zzzzzza-daily.js (the day's party on the new party's screen; the days on the title screen))
  - Today's dungeon keeps its seed and two mutators, and now sets the rest for everyone: the day's party (the classic
    four, named and rolled by the date), the pauper's kit, Fair, no ascension and no again.
  - Its end is scored (floors, the fallen, guardians, gold and chests, a crown or the bottom, less a little for steps),
    and each day played is kept with its best score, deepest floor and tries, listed on the title screen. A score of
    3,000 is a feat. This finishes plan 28 (set 8).

New Game+ (v33.2, UPGRADE_PLAN_28.md phase 2)
  (src/js/69zf-again.js; 76zzzzzz-again.js (Again and Carry on the new party's screen))
  - When the Lich King falls, the way opens to set out again: the new party's screen has "Again" (up to the highest
    won plus one, to ten) and "Carry" - one of the things the crowning party wore, carried down as an heirloom.
  - Each time again its monsters are a quarter tougher and an eighth harder-hitting; its fights pay a quarter more
    gold a time, and now and then leave a thing from two floors deeper a time. Winning again is a feat.

Seasons of the year (v33.1, UPGRADE_PLAN_28.md phase 1)
  (src/js/69ze-seasons.js; 76zzzzzy-seasons.js (the Calendar's trial))
  - Each season (the real date's, or the one pinned in the Settings) has its trial, done once a season: spring's Thaw
    (the tenth floor within three days), summer's Long Day (a guardian slain on the first day, while the sun is up),
    autumn's Wild Hunt (forty beasts in one expedition), winter's Long Hunger (the fifteenth floor with nothing eaten).
  - Each pays its own: the Thaw-water Charm, the Ring of the Long Day, the Huntsman's Ring, the Rime-hunger Torc. The
    Calendar (K) tells the season's trial and how far the run has come; all four are a feat.

The hall of feats (v33.0, UPGRADE_PLAN_28.md phase 0)
  (src/js/69zd-feats.js; 76zzzzzx-feats.js (the hall, from the Mage Tower's doors))
  - Twenty feats more, kept with the achievements (and so titles too): a run's ten dishes, three feasts, fifty chests,
    three hundred slain, ten thousand steps, three, six and all nine guardians, ten champions, 10,000 gold, floors 20
    and 40, twenty shards held, three words from the Tower, five things from the still, four trophies mounted, every
    hero in rare gear, a hero at level twenty, a party of veterans.
  - The hall of feats, a room at the Mage Tower's foot (from its doors): a brass plaque for every feat earned, with
    who and when, and dark stone with the words for the rest; and the title worn.

The house furnished (v32.3, UPGRADE_PLAN_27.md phase 3)
  (src/js/69zc-furnish.js; 76zzzzzw-furnish.js (two more rooms in the house's window))
  - Eight furnishings for the party's house, bought with gold in town - a hearth rug, a pantry shelf, a brass lamp, a
    strongbox, a bookcase, a shrine nook, a weapon rack, an armour stand - each a small good that every run setting out
    from the house carries (good heart, rations, a trimmed torch, gold, or +1 to a stat for every hero).
  - The guardians' trophies mounted on the trophy wall, two a level of the house past the first: each gives every hero
    who sets out +1 to its guardian's own stat. This finishes plan 27 (set 7).

Brewing at the still (v32.2, UPGRADE_PLAN_27.md phase 2)
  (src/js/69zb-stillbook.js; 76zzzzzv-stillbook.js (the still's book in the fields and a Journal page))
  - Recipe pages lie in the dungeon - one chest in eight from the second floor down, a fallen party's remains one time
    in three - each a still recipe of a South Fields crop and a band's ingredient, written into the village's book.
  - At the still in the fields' shed a known recipe makes healing or mana potions, antidotes, oils, holy water, a
    firepot or an elixir from its two, for no gold. Twelve pages in all; the Journal's Still book page lists them.
  - (v32.1's commit took in this release's files too soon and its checks failed; this one makes them right.)

Enchanting at the Mage Tower (v32.1, UPGRADE_PLAN_27.md phase 1)
  (src/js/69za-enchant.js; 76zzzzzu-enchant.js (the enchanter's corner of the Tower's doors))
  - Relic shards: three from every guardian, five where the Lich King's crown falls, one now and then from a champion,
    and five from a guardian's relic broken at the Tower.
  - The enchanter at the Mage Tower's doors gives worn gear a word it lacks (three offered for each empty place, the
    player's pick) or raises one of its words a tier, for shards and gold. The more a thing has had done, the less
    likely it takes; a failure spends the shards, and one time in six cracks the thing and takes a word from it.

Cooking, wider (v32.0, UPGRADE_PLAN_27.md phase 0)
  (src/js/69y-ext.js, 69z-cooking2.js; 76zzzzzs-pages.js (a Journal page for the later updates), 76zzzzzt-cooking2.js)
  - Fifteen new dishes from the South Fields' crops (potato, leek, carrot, tomato, pumpkin, corn, chili, garlic,
    strawberries, grapes...) and the deep's edible finds (salt weed, spore caps, root sap, ghost caps).
  - A feast: at a camp's fire or the home's table, two or three different dishes eaten together - all their good at
    once, for as long as the shortest lasts (a new feat for three).
  - The Journal's Recipes page: every dish, those made written in with what they need and do, the rest a blank with a
    hint. The book is kept in the village, from run to run.

Weather on the lens (v31.9, UPGRADE_PLAN_26.md phase 9)
  (src/js/76zzzzzr-lens.js; 40-render.js (the screen pass's drops, snow and mist))
  - Out in the rain drops gather on the view - beads that sit and runners that slide down - bending what is behind
    them; in falling snow it gathers at the edges; in mist and the damp bands below (the Flooded Vaults, the Drowned
    Town) fine beads cloud it a little. Each comes and goes slowly; not indoors or in a fight.
  - Settings > Weather on the view: On or Off. This finishes plan 26 (set 10 of the list).

The map as an object (v31.8, UPGRADE_PLAN_26.md phase 8)
  (src/js/76zzzzzq-parchment.js (the big map's drawing, wrapped))
  - The big map (Tab) is on parchment: old paper, blotched and darker at its edges; the walls inked with a hand's
    wobble; each newly seen square inked in with a spreading blot; the party's route on the floor in pencil. Its marks,
    icons and notes are all kept. Settings > The big map: Parchment or Graph paper; the side map is as it was.

3-D items (v31.7, UPGRADE_PLAN_26.md phase 7)
  (src/js/76zzzzzp-solids.js (CM.solidOf: an icon given depth, layer on layer))
  - Hover a thing's icon in the pack, a shop, a chest or the stash and it turns where it lies, a small solid thing:
    its picture laid layer on layer, the outer ones lit and the inner ones darker.
  - Its tooltip card carries a larger one turning slowly. With Reduce motion it stands still, turned so its depth shows.

Scene transitions (v31.6, UPGRADE_PLAN_26.md phase 6)
  (src/js/76zzzzzo-transitions.js; 40-render.js (the screen pass's swirl))
  - Down or up the shaft the view goes to black and comes back; through a portal or a waystone it swirls in violet;
    after a night's camp the dawn brightens slowly out of a warm dark; any other new floor fades in.
  - The swirl is left out with Reduce motion (the fades stay).

Screen styles (v31.5, UPGRADE_PLAN_26.md phase 5)
  (src/js/76zzzzzn-styles.js; 40-render.js (the screen pass's styles))
  - Settings > Screen style: Clean (as it was), Old monitor (a curved tube, scanlines, colour fringes), Watercolour
    (soft washes that bleed, pigment pooled at the edges, the paper's grain), Ink and parchment (sepia shades and
    inked lines on old paper), Crisp (sharpened). The game underneath is the same.

Spell colours in the room (v31.4, UPGRADE_PLAN_26.md phase 4)
  (src/js/76zzzzzm-spelllight.js; 40-render.js (a room's flash below ground))
  - A bolt in flight carries its light along the walls: a fireball orange, frost blue, force violet, holy gold, poison
    and acid green, shadow purple (where it lands it already flared).
  - Lightning flashes the whole room white, below ground as under the sky (not with Reduce motion).

Focus (v31.3, UPGRADE_PLAN_26.md phase 3)
  (src/js/76zzzzzl-focus.js; 40-render.js (the screen pass softens the frame, holding the eye on a spot))
  - While a dialog is open the view behind it goes soft, and comes back sharp when it closes.
  - When a boss or a guardian makes its entrance, all but it goes soft and the room comes back into focus as the
    entrance ends (not with Reduce motion).

Living portraits (v31.2, UPGRADE_PLAN_26.md phase 2)
  (src/js/76zzzzzk-portraits.js (the party's cards, redrawn from their own pictures))
  - The heroes on the party's cards blink now and then and glance aside (a helmed face that shows no eyes doesn't).
  - Hurt, a hero bruises; badly hurt, goes pale with a cut. Weary with hunger or in the heat of the deep, they sweat;
    in the snow and the cold bands their faces frost at the edges. The fallen are left as they are.

Camera feel (v31.1, UPGRADE_PLAN_26.md phase 1)
  (src/js/76zzzzzj-camera.js (and CM.addSetting, a Settings row for the window files); 40-render.js (renderer.camOff))
  - Settings > Camera motion: Gentle (the default), Full or Off. The walk bobs and sways from foot to foot, the view
    leans into a turn, a blow of a quarter of a hero's health or more makes it stumble, and a guardian's, a boss's or a
    giant's arrival shakes it. Off is a steady camera (no bob at all); Reduce motion is always Off.

A hand and a torch (v31.0, UPGRADE_PLAN_26.md phase 0)
  (src/js/76zzzzzi-hand.js (its own canvas over the view, under the HUD))
  - The front hero's hand at the foot of the view holds the torch or the lantern up: it sways with the walk and lags
    a turn; the flame leans and gutters in the wind and burns smaller as the torch burns down.
  - Shaded (T), the light is held low and covered. Not by daylight, not in a fight, not with no light; no sway with
    Reduce motion.

Better far distance (v30.9, UPGRADE_PLAN_25.md phase 9)
  (40-render.js (billboards fade in; the air's colour on the far land))
  - What stands on the ground far off (props, beasts, people) comes into view softly over the last two or three
    squares instead of appearing all at once.
  - Outdoors the far land takes the colour of the air - paler and bluer by day - before the fog, so the distance
    reads as distance. This finishes plan 25 (set 9 of the list).

Water you can see into (v30.8, UPGRADE_PLAN_25.md phase 8)
  (src/js/76zzzzzh-water2.js; 40-render.js (shallows, fish, foam); 80-main.js (CM.waterCells))
  - The shallows near the banks show their bed through the ripples - pebbles and swaying weed; now and then a fish
    turns in the water; foam gathers right along the banks, more where the river runs.
  - Rings spread where followers, townsfolk and beasts stand or wade in water, as they did for the party. The floor's
    water goes to the shader in the floor's map (CM.waterCells).

The deeper, the older (v30.7, UPGRADE_PLAN_25.md phase 7)
  (src/js/76zzzzzg-age.js; 40-render.js (cracks, roots, fungus and veins on the walls))
  - The first floors are clean dressed stone; cracks come in from the sixth floor; roots hang from the ceiling from
    the eighth, thickest about the twentieth; fungus that glows grows low on the walls from the eighteenth.
  - From the thirtieth the stone is strange, veined in colours that shift as the eye moves. Endless goes on ageing.

Grass that moves aside (v30.6, UPGRADE_PLAN_25.md phase 6)
  (40-render.js (the vertex shader: what grows bends away from the party))
  - What grows tall - grass, reeds, crops, ferns, flowers - bends away from where the party stands, more the closer
    it is, and springs back as the party walks on. Trees and hedges stand firm. Off with Reduce motion.

Smoke and chimneys (v30.5, UPGRADE_PLAN_25.md phase 5)
  (src/js/76zzzzze-smoke.js (the air's motes: torch and fire smoke))
  - The wall torches' smoke rises and, under a ceiling, gathers and runs along it; braziers, the camp's fire and fire
    on the floor send up a thicker plume that the wind takes outdoors.
  - The town's chimneys smoke more at supper-time, on top of the night and the cold months.

Heat and cold (v30.4, UPGRADE_PLAN_25.md phase 4)
  (src/js/76zzzzzd-heatcold.js; 40-render.js (the screen pass made general: heat and breath; glints))
  - The air shimmers above braziers, the forge, fire on the floor and (a little) the wall lamps, and all through the
    Foundry and the Root of the World. The glow's screen pass now runs for these even with Glow off.
  - The party's breath shows on a winter's day outdoors and in the cold bands below (the Lich King's Palace, the
    Drowned Town, the Crystal Caverns); crystal and frosted walls glint as the eye moves, and snow glints in the sun.

Soft corners (v30.3, UPGRADE_PLAN_25.md phase 3)
  (40-render.js (the floor's map as a texture; the shading's soft corners))
  - Ambient occlusion: the floor's walls go to the shader as a small map, and the floor (and the ceiling, below) darken
    softly near them - most in the corners - while the walls darken at their foot and, under a ceiling, at their head.
  - Rooms read as solid stone rather than flat paint; in the town the cobbles shade along the house fronts.

The sky (v30.2, UPGRADE_PLAN_25.md phase 2)
  (src/js/76zzzzzc-sky.js; 40-render.js (the sky dome's clouds, stars and aurora; cloud shadows; the flash))
  - Clouds drift with the wind, as many as the weather brings (a few on a clear day, a deck in the rain), and their
    shadows cross the sunlit ground. Stars come out on clear nights and twinkle.
  - On some clear winter nights an aurora hangs in the north; on some rainy evenings lightning whitens the land and
    the thunder follows a moment later (no flash with Reduce motion). The moon's face already waxed and waned.

Marks that stay (v30.1, UPGRADE_PLAN_25.md phase 1)
  (src/js/76zzzzzb-marks.js; 40-render.js (a flat mark turned by its spin, not snowed over))
  - Fire that lands leaves a scorch; a foe that falls leaves blood (or ash, bone dust, or glittering shards, by how
    it died; nothing for those that sink or fade); the party leaves footprints in lying snow and on wet ground.
  - They lie flat and fade with the game's clock - footprints in an hour, ash and bone dust in half a day, the rest in a
    day - and are kept for each floor while the game is open (not saved).

Wet surfaces (v30.0, UPGRADE_PLAN_25.md phase 0)
  (src/js/76zzzzza-wet.js; 40-render.js, 80-main.js (CM.beforeFrame))
  - In the rain the stone and cobbles darken and shine, the walls darken at their foot, and puddles lie in the low
    places: they mirror the sky and the lamps and ring with the falling rain.
  - The morning after a day of rain the sheen dries in the first hour of sun and the puddles shrink till noon (not on
    lying snow). 80-main.js gained CM.beforeFrame, the picture's last word before a frame, for the window files.

Followers seen (v29.5, UPGRADE_PLAN_24.md phase 5)
  (src/js/76zzzzz-followers.js)
  - Who comes along walks behind the party, where a look back finds them: the porter under a great pack, the
    torchbearer with the torch held high (and its light about him), the hedge-wizard, the one you cut loose, Grip,
    and the party's own hound at heel to one side and the pony on the lead to the other (the pony only in the Wood).
  - They keep to the party's trail a step or two behind and close up as it walks; on a new floor they come in at its
    back. They are the picture's: the rules don't know where they stand.

Townsfolk with routines (v29.4, UPGRADE_PLAN_24.md phase 4)
  (src/js/76zzzzy-townsfolk.js)
  - The town's six residents keep hours: by day the smith at the forge's door, the merchant at the market, the priest
    at the temple, the librarian at the library, the landlady and the farmer about the market, the well and the West
    Gate; in the evening most of them make for the tavern; at night they are home, out of sight.
  - When the hour moves them they walk there along the streets, bobbing as they go; in the rain they keep under the
    eaves near where they'd be. They step out of the party's way. They are the picture's: the rules don't know them.

The heroes' gear seen (v29.3, UPGRADE_PLAN_24.md phase 3)
  (src/js/76zzzzx-herogear.js; 70-ui.js, 73-play.js)
  - A hero's portrait - on the party's cards (and so the level-up card's), the sheet, the camp's and the end's lists -
    shows what they carry: the weapon in hand at its lower right, the helm at its upper left, the armour at its lower
    left, each drawn in the look of the day with a dark rim. Change what they wear and the portrait follows.

Deaths of their own (v29.2, UPGRADE_PLAN_24.md phase 2)
  (src/js/76zzzzw-deaths.js; 80-main.js)
  - A monster dies as what it is: the bones crumble where they stand, their pieces falling; the demons, the burning
    things and the undead flesh go to ash, darkening and blowing away in embers; the crystal ones shatter in a flash of
    shards and light; the drowned - and anything that falls in water - sink with a splash and its rings; the ghosts
    rise away and the rest topple and fade, as they did. Reduced motion: they only fade.

Which way it faces (v29.1, UPGRADE_PLAN_24.md phase 1)
  (src/js/76zzzzv-facing.js; 40-render.js, 80-main.js)
  - A monster on the floor faces the way it last moved (one that hasn't moved, a way of its own). From the party's
    side of it, it is seen from the front, from the side - narrowed, its far side in shadow, turned the way it faces -
    or from behind, its picture in shadow and turned away. One coming for the party comes face first. In a fight they
    all face you. The facing is the picture's only; the rules don't know it.

Monsters that move (the ninety-fifth big update - v29.0, UPGRADE_PLAN_24.md phase 0)
  (src/js/76zzzzu-animate.js; 40-render.js, 80-main.js)
  - A monster's picture is drawn in strips that bend, so it moves as a body: at rest it sways a little from the hips;
    on the move it bobs and its feet step; in a fight it draws itself down for the blow, stretches into the strike and
    is crushed back by a hard one taken. (The packs have no frames to play: the motion is the game's own.)

Footsteps by the ground (v28.3, UPGRADE_PLAN_23.md phase 3 - the sound plan done)
  (src/js/76zzzzt-footsteps.js; 80-main.js)
  - A step sounds like what is underfoot: a sharp click on the town's cobbles and flagstones, a soft brush through
    grass, moss and the leaf litter, a dull fall on earth and the roads, a hollow knock on boards (the bridge, the
    houses' rooms - the forge and the temple are stone), a splash in water, a crunch in snow lying. Below ground, each
    depth's own footfall as before, and a splash in its puddles.

The place's own sound (v28.2, UPGRADE_PLAN_23.md phase 2)
  (src/js/76zzzzs-placeamb.js)
  - Over the depth's ambience, loops of the place itself, made by the game when first wanted, each as loud as the
    party is near it and heard from its side: birds by day (fewer in rain and winter) and crickets on summer nights in
    the Wood, and the river beside it; in the town the market's murmur about the Square and hammering at the forge by
    day, birds overhead; in the houses' rooms, the tavern's talk and the forge's anvil.
  - Below, each band its own: water lapping in the Flooded Vaults, the Undercroft and the Drowned Town, bubbling in the
    Fungal Deep, chimes in the Crystal Caverns, the Foundry's hammers and hiss, a slow beat at the Root of the World.

Music that follows (v28.1, UPGRADE_PLAN_23.md phase 1)
  (src/js/76zzzzr-musicmood.js)
  - Below ground, as monsters awake come within seven squares, a layer of tension rises in the depth's tune - a low
    pulse on the chord's root, brighter the nearer they are, a heartbeat under it, and close by a sharp note a half
    step off - and it falls away as they are left behind. In a fight the tune's own danger takes over, as before.
  - In safe places - the town by day, a house's room, a camp - the tune drops to its quiet self: softer, and three
    notes in four of its melody left out, the pad carrying it.

Sound in its place (the ninety-fourth big update - v28.0, UPGRADE_PLAN_23.md phase 0)
  (src/js/76zzzzq-sound3d.js)
  - Monsters are heard from where they are: now and then the nearest one awake within nine squares calls - from the
    side it stands on, louder the nearer it is, and dull and low when a wall stands between, or it is behind you.
  - Every sound takes the room it is made in: a large room or the Dwarven Halls and the Lich King's Palace ring, a
    cave rings longest, a corridor is dry, the town and the Wood hardly answer, a house's room is close and warm.

A dog and a pony (v27.2, UPGRADE_PLAN_22.md phase 2 - the gameplay plan done)
  (src/js/69x-pets.js, 76zzzzp-pets.js)
  - Animals of the party's own, bought at the farm in the Wood and kept in the village between runs - not hired help,
    so they take no follower's place (the farm's dog Grip can still be hired besides).
  - The hound goes everywhere: it growls at a trap two squares off (marked on the map) and scratches at the wall where
    a hidden door is; on the land by day it digs now and then - an old purse, a herb, a seed. 60 gold.
  - The pony carries thirty more on the surface, walks the land quicker - every other step on the Wood's roads and
    tracks costs no time - and waits tethered at the shaft's head; it does not go below. 220 gold.
  - The side panel says who is along.

Things that break (v27.1, UPGRADE_PLAN_22.md phase 1 - below ground only)
  (src/js/69w-breakables.js, 76zzzzo-breakables.js; 61-explore.js, 80-main.js)
  - Crates, barrels and urns stand about the dungeon's rooms (urns in the Catacombs and the Ossuary). Walk through one
    and it breaks underfoot - the step goes on: often only splinters, a few coins, a dry torch, a healing potion, a
    reagent, and now and then a nest of rats that bites.
  - Some halls have a brazier. Space, standing at it, knocks it over: the squares about it burn for half an hour - a
    fight in the fire burns every foe each round (fire's resistances count) and singes the front row; walking through
    the coals burns the party a little. The flames light the room.
  - Placed by dice of their own, so the floors already laid out stay as they were; none above ground.

Weather that matters (the ninety-third big update - v27.0, UPGRADE_PLAN_22.md phase 0)
  (src/js/69v-weather.js; 40-render.js, 76zzzze-seasons.js)
  - Rain, after dark in the Wood, burns a torch twice as fast, and now and then a gust and the rain put it out for a
    few steps - dark until it is lit again. A lantern, shut in its glass, minds neither.
  - Mist on the surface shortens the party's sight: two squares ahead, not four, on the map, and the view closes in.
  - Snow lying in the Wood slows the party: every step there takes two minutes, and the walk is heavier.

Faster loading (v26.4, UPGRADE_PLAN_21.md phase 4 - the performance plan done)
  (src/js/50-audio.js, 40-render.js, 79-artworker.js, 76zzzzk-livemap.js, 80-main.js, 00-util.js)
  - The game's own start - from its code running to the title - went from 647 ms to 426 ms of the page's time: the 56
    sounds are made when each is first wanted (and the rest in the idle moments after), not all at once at the start,
    which was 272 ms; the shaders are compiled by the graphics driver beside the start (where the browser can) rather
    than in its way. The page is ready about 150 ms sooner.
  - The worker paints in software and only six seconds after the party arrives somewhere, so its paintings coming back
    no longer stall a frame (in v26.3 they could, by 270 to 400 ms, just after a new game).
  - The side map is drawn again only when something on it changes; between, only what pulses and glows is drawn over a
    picture of it - a tenth of the work it was.
  - Tried and left out: keeping the built sets between visits in the browser's store. Measured here, reading two sets
    back took 3.1 seconds where painting them takes a quarter of one, so painting stays.
  - CM.startLog notes the start's moments (the packs in, each look's pictures first up, the worker ready).

Painting off the main thread (v26.3, UPGRADE_PLAN_21.md phase 3)
  (src/js/79-artworker.js; 40-render.js, 80-main.js)
  - The sets of pictures are painted in a worker - the game's own code, run beside the page with a few stand-ins for
    it, given the looks' packs as bitmaps - so painting a set no longer stops the screen. While the party plays, the
    sets it will want next are painted there ahead: the next band's from its last floor, the town's and the Wood's
    from below. They come back as raw pixels at the size each texture takes (the small sprites as bitmaps), the
    pictures the graphics card already holds left out, and go straight up.
  - Measured, going down into a band not yet seen: Pixel 662 to 242 ms, Stone 594 to 191 ms (what is left is the
    floor's own making and the mipmaps). The worker's sets are the page's, layer for layer.
  - Where the browser has no worker that can paint, or a set wasn't painted ahead, it is painted the old way.

Instanced drawing (v26.2, UPGRADE_PLAN_21.md phase 2)
  (src/js/40-render.js)
  - Every plain billboard - the standing props, the townsfolk and the monsters standing, the crops, the motes and the
    sparks - is drawn as an instance of one quad: sixteen numbers each sent to the graphics card, stood up to face the
    camera (and bent by the wind) in the vertex shader, instead of sixty worked out in the page every frame. What lies
    flat, hangs on a wall, swings on a hinge, topples or ripples is drawn as before.
  - Measured: the frame's sprite work halved as things are (0.76 to 0.36 ms); with three thousand billboards in view, 21.6
    ms a frame (39 frames a second) became 4.7 ms (60) - room for far more grass, props and crops at the same speed.

Partial rebuilds (v26.1, UPGRADE_PLAN_21.md phase 1)
  (src/js/40-render.js, 26-surface.js)
  - The floor's mesh is kept in three parts, each made again only when what it is made of changes: the floor itself
    (walls, ground, roofs, trees, props - the long one), the traces the party has left, and the lit windows with the
    far town's lights.
  - A fight starting or ending, a mode changing, the Detail asked again: nothing is made again unless something in it
    changed - in the town or the Wood that was a 90 to 110 ms stall every time, now about 2 ms.
  - A trace left: 3 ms, not 84; the windows lighting or going dark: 16 ms, not 84. A secret door found, a building
    raised, the trees turning still make the floor again, as they must.

Smaller textures (the ninety-second big update - v26.0, UPGRADE_PLAN_21.md phase 0)
  (src/js/40-render.js, 36-looks.js)
  - The pictures go up to the graphics card at the size they need: the Pixel look's (pixel art) at 128 rather than
    256; the Stone look's photographs at 512 and nothing else; the outdoors' drawn pictures (the crops, the court's
    stones and portals, the far views, the moons, the townsfolk) in a third texture of their own at 256, not blown up
    to 512 beside the photographs; and the small sprites - motes, sparks, signs, moons, keys - four to a layer.
  - The town's textures, measured: Pixel 165 MB to 38 MB, Stone 348 MB to 221 MB, Drawn 178 MB to 163 MB; a band's
    below ground about a tenth less again. Nothing on screen changes.

The tray (v25.3, UPGRADE_PLAN_20.md phase 3 - the interface and feel plan done)
  (src/js/76zzzzm-tray.js; style.css)
  - What matters and passes comes up as a small toast in the lower corner of the view, as well as in the log: a hero
    gaining a level, a town request ready to hand in and its reward when it is, seeds found, a rare (or better) find,
    a card for the deck, the party's renown level rising.
  - Each has its own mark and colour; four at most stack up; they fade after a few seconds, and a pointer over one
    holds it. A click opens its page: the hero's sheet, the requests, the pack, the village.
  - Not while a film plays.

Tooltips that compare (v25.2, UPGRADE_PLAN_20.md phase 2)
  (src/js/69u-compare.js, 76zzzzl-tips.js; style.css)
  - Hovering a thing anywhere it is listed - the pack, a shop, a chest, the belt, the stash - brings up a tooltip of
    its own: the name in its rarity's colour, what it is and where it was found.
  - For gear, the hero it suits best and every number that would move if they wore it in place of what they wear -
    attack, the weapon's blow, armour, health, magic, the six stats, to hit, crits, blocking and the gear score - green
    for up, red for down; and a line for the rest of the party. What one can't wear says why; the unknown, that it is.
  - It is worked out by trying the thing on and taking it off again: nothing about the hero changes.

A living minimap (v25.1, UPGRADE_PLAN_20.md phase 1)
  (src/js/76zzzzk-livemap.js; 70-ui.js, style.css)
  - The side map moves with the place: monsters within seven squares pulse red; the portals glow in their own
    colours, and the Wayfarer's Stones and the Glyph Deep's cabinet with them; the party's last forty steps on a floor
    fade out behind it.
  - It zooms in on the party - the + and - in its corner, or the mouse wheel - four steps, kept between visits;
    clicking a square to walk there and right-clicking for a note still work zoomed. The big map is as it was.

Windows that move (the ninety-first big update - v25.0, UPGRADE_PLAN_20.md phase 0)
  (src/js/76zzzzj-feel.js; style.css)
  - A window rises and fades in when it opens and fades away when it closes; buttons press in when clicked.
  - The purse counts up (or down) to the new gold, with a flash of gold (or red) as it goes.
  - What the party picks up flies from the view to the Inventory button, which bumps as it lands.
  - Reduced motion keeps all of it still.

Interiors (v24.6, UPGRADE_PLAN_19.md phase 6 - the world plan done)
  (src/js/69t-interiors.js, 76zzzzi-interiors.js; 61-explore.js, 63-camp.js, 69f-worldmap.js, 73-play.js, 76zzzzh-models.js, 80-main.js)
  - The town's houses can be walked into. Through the door of the Hanged Lantern, the Merchant's House, the Smith's
    forge, the Library, the Temple, the Guildhall, the Chronicler's House or your own house, the party steps into a
    furnished room of its own: the tavern's bar and kegs, tables, stools and hearth; the merchant's shelves, crates and
    barrels; the forge's fires, anvils and racks; the library's and the chronicler's walls of books and reading
    tables; the temple's altar, pews and candles; the guildhall's long tables; at home the hearth, a table and a bed.
  - The furniture is solid - built, not pictured - and stands in the way; the rooms are lit by their own candles,
    lamps and fires, and have their own walls, floors and ceilings: plaster and timber, stone, panelling, pale stone.
  - Space at the keeper (at home, the hearth) opens the same window the door used to; every service works inside as
    it did at the door. The door in the south wall goes back out onto the doorstep. Fast travel leaves the room first.
  - A house not yet raised still opens its window at the door. Going in or out is a step, a minute on the clock.
  - Automatic and the films keep to the door's window, as before; Automatic steps out of a room before it goes on.

Real 3-D props (v24.5, UPGRADE_PLAN_19.md phase 5)
  (src/js/76zzzzh-models.js; 26-surface.js)
  - Barrels, crates, carts, the market's stalls, fallen logs and stumps are built as small solid models in the floor's
    mesh - boxes and many-sided cylinders - instead of pictures that turn to face the party: a barrel with its iron
    hoops and its bulge, a cart on its wheels with its shafts, a stall with posts, a counter of goods and a striped
    awning.
  - They stand in the light like the walls - the torch, the lamps, the sun and the relief all fall on them - and look
    right from every side. Their wood, end grain, iron, bark and awning are painted once a set.

Distant views (v24.4, UPGRADE_PLAN_19.md phase 4)
  (src/js/76zzzzg-farviews.js; 26-surface.js)
  - From the land, the town stands on its hill to the east, where it really is - past the cliffs and the West Gate:
    its ring wall, the roofs and chimneys within, the keep and the temple's spire. After dark its windows shine out
    over the Wood (they glow through the night air and catch the Glow setting).
  - From the town, the Mage Tower rises on the skyline to the north-west, over the Wood's treeline, at its own place
    in the land; its high window is lit at night.
  - The land's eastern horizon no longer repeats a small picture of a walled hill all along it.

Day and night life (v24.3, UPGRADE_PLAN_19.md phase 3)
  (src/js/76zzzzf-nightlife.js; 26-surface.js, 40-render.js, 80-main.js)
  - The town keeps hours: its windows light from half past six in the evening, most are lit by eight, and they go dark
    one by one from ten as the town goes to bed; a few come back before dawn for the early risers.
  - A lamplighter walks the streets from seven, from the lamp nearest the Square to the next, lighting each with the
    flame on his pole; by nine they are all lit. At five he goes round again and puts them out. (The clock is the
    game's - a step a minute - so the lamps come on as the party walks the evening.)
  - Moths gather about the lit lamps; bats flit over the roofs and the trees at dusk; in the Wood at night an owl
    calls and passes over. The leaves, the snow and the rest of the air now drift with the day's wind.

Seasons that turn (v24.2, UPGRADE_PLAN_19.md phase 2)
  (src/js/76zzzze-seasons.js; 26-surface.js, 30-art.js, 36-looks.js, 40-render.js, 80-main.js)
  - A run's season comes in over its first days instead of all at once: on the first day only a third of the trees
    have turned - the rest still wear last season's crowns (green in autumn, gold in winter, bare in spring) - and a
    few more turn each day until all have by the fourth.
  - Through autumn the leaves come down and gather on the open ground, more each day.
  - In winter the snow builds over the days it falls - in patches at first, then whole - and melts back the same way
    on the days it doesn't.

Living water (v24.1, UPGRADE_PLAN_19.md phase 1)
  (src/js/76zzzzd-water.js; 40-render.js, 45-fx.js, 80-main.js)
  - The Wood's river runs: its ripples are carried downstream with the current.
  - Still water - the flooded vaults, the Undercroft, the puddles on the roads - lies calm and mirrors the sky more
    clearly; rain stirs it and rings every pool and puddle, each drop in its own time.
  - Rings spread, and a few drops fly, where the party wades in.

Wind (the ninetieth big update - v24.0, UPGRADE_PLAN_19.md phase 0)
  (src/js/76zzzzc-wind.js; 26-surface.js, 40-render.js, 80-main.js)
  - On the surface the wind blows from a way of its own each day, in gusts that roll across the land: the trees, the
    grass, the reeds, the flowers and the crops in the fields all give to it together, and the scarecrow's coat flaps.
  - Rain brings it up, snow a little, mist lays it down; below ground there is none. Reduced motion stills it.

The pace (v23.4, UPGRADE_PLAN_18.md phase 4 - the fights worth watching plan done)
  (src/js/70-ui.js, 80-main.js, 76zzzz-blows.js, 76zzzza-stage.js)
  - Settings > Combat speed: Cinematic, Normal, Quick or As good as instant.
  - Cinematic slows the effects a little, holds crits and entrances longer, pushes the camera in on a crit, and holds
    a beat on a kill with the camera leaning in (further for a guardian or the Lich King).
  - Quick halves the effects and trims the hit-stops and the entrance; the automatic hand moves on sooner.
  - As good as instant: no holds and the entrance's banner only.

Who's next (v23.3, UPGRADE_PLAN_18.md phase 3)
  (src/js/76zzzzb-order.js; style.css)
  - In a fight, a strip along the foot of the view shows the round's order as the dice and everyone's speed set it:
    heroes in blue, foes in red and numbered as the tags over their heads, the one acting lit gold, those done dimmed,
    the fallen and the fled struck through, a hidden foe a "?". It moves on as each acts and is dealt again each round.

Entrances (v23.2, UPGRADE_PLAN_18.md phase 2)
  (src/js/76zzzza-stage.js; 80-main.js, style.css)
  - A guardian or the Lich King enters on a stage: black bars close in from above and below, the clock and the name
    tags step aside, the camera leans in while it rises from the floor, its name comes up in a large banner with where
    it rules, and a sting of music sounds - a low drum and a rising minor chord.
  - Any key or a click skips it; the fight (and the automatic hand) waits until it is done.
  - The title card had stopped showing at all: the recipe had two cases for the entrance and only the first ever ran.
  - Reduced motion or As good as instant: the banner and the sting only.

Blows that land (v23.1, UPGRADE_PLAN_18.md phase 1)
  (src/js/76zzzz-blows.js; 62-combat.js, 28-motion.js, 45-fx.js, 40-render.js, 80-main.js, style.css)
  - A critical hit (a weak spot found, a knife from behind) is shown as one: the foe flashes white and everything in
    the air holds still for a moment (a hit-stop), the view leans toward the blow, sparks fly, and the number comes
    big and gold with a "!".
  - Every blow has weight: a heavy one knocks its foe further back, for longer, and rocks it; a light one only makes
    it flinch. A big blow taken by the party pushes the view back.
  - A monster's lunge winds up first - it draws back, then comes - and a boss's or guardian's reaches further.
  - Reduced motion keeps only the flash and the number; As good as instant skips the hold.

Spells that travel (the eighty-ninth big update - v23.0, UPGRADE_PLAN_18.md phase 0)
  (src/js/76zzzy-spells.js; 45-fx.js, 80-main.js)
  - Every spell aimed at foes leaves its caster's hand - the hero's own side of the view - and travels: Magic Missile
    three darts, Frost a shard to each foe, Lightning a crack from the hand, Call Lightning and Smite from above, Sleep
    and Lullaby a drift of motes, Turn Undead a wave of light rolling out, Drain a red stream coming back to the caster,
    a Firework's sparks arcing over.
  - Each lands with an impact: a ring on the floor, a burst, a flare of its light on the walls.
  - Some leave something on the ground a while: a fireball's fire burning under each foe, frost glittering, holy light,
    thorns and roots, a sanctuary's ring. (Not with Reduced motion.)
  - Spells on the party - healing, blessing, protection - rise about the caster's side of the view.

Glow (v22.5, UPGRADE_PLAN_17.md phase 5 - the light and air plan done)
  (src/js/40-render.js, 70-ui.js, 80-main.js)
  - What is bright is softly haloed: torch flames, lamps and braziers, the portals and their runes, spells, gold, the
    sun. The frame is drawn off screen (still smoothed at the edges), its bright part taken out at a quarter size,
    blurred and laid back over it. By day only the brightest glows, so the sky does not.
  - Settings > Glow: Soft (the default), Strong or Off; always off at Low detail, so a slow machine that steps its
    Detail down sheds it first.

Grade and hour (v22.4, UPGRADE_PLAN_17.md phase 4)
  (src/js/76zzzx-grade.js; 40-render.js, 80-main.js)
  - Each band its own grade - a lift in the shadows, a contrast, a saturation - not only a tint: the Lich King's
    Palace cold and hard, the Drowned Town soft and blue, the Ossuary drained, the Crystal Caverns vivid, the Foundry
    and the Root of the World hot.
  - On the surface the hour colours everything: gold at dawn and dusk, blue in the hour after sunset and before dawn,
    the colours drained at night.
  - Winter mornings frost the walls, thickest low and in patches, gone by mid-morning.

Air (v22.3, UPGRADE_PLAN_17.md phase 3)
  (src/js/76zzzw-air.js; 40-render.js, 80-main.js)
  - The air below has a body, each band its own: the Drowned Town and the Undercroft thick and drifting, the Foundry
    smoky, the Fungal Deep full of spores, the Flooded Vaults damp, the Catacombs only a little. It lies thicker low
    and drifts slowly; the party's torch and every lamp and brazier glow in it.
  - Above, the Wood's hollows and the town's lanes lie misty at dawn and a little hazy at night.
  - By day, looking toward the sun, bars of light stand in the air with dust drifting in them - strongest in the Wood,
    fainter in the town's lanes; none in the rain. Nothing moves with Reduced motion on.

Shadows (v22.2, UPGRADE_PLAN_17.md phase 2)
  (src/js/76zzzv-shadows.js; 40-render.js, 80-main.js)
  - Whatever stands on the ground - people, monsters, chests, props, trees - casts a shadow away from the light that
    rules where it stands: by day on the surface, the sun, long to the west in the morning, short at noon and long to
    the east at dusk; at night and below, the strongest lamp, torch or brazier near it, or else the party's own torch.
  - A small soft shadow stays under each foot, so nothing floats.

Surfaces (v22.1, UPGRADE_PLAN_17.md phase 1)
  (src/js/40-render.js)
  - Walls, floors and the ground take relief from their own pictures: a height is read off each picture's light and
    dark and turned into a facing per pixel, so the torch, a brazier or the sun rakes across stone, brick and earth -
    the mortar and the cracks fall back, the faces of the stones catch the light.
  - Deepest in the Stone look, gentler in Drawn, light in Pixel (the tiles stay crisp). Stone keeps a faint sheen and
    wet ground a stronger one. Figures, props and the sky are left flat.

Light (the eighty-eighth big update - v22.0, UPGRADE_PLAN_17.md phase 0)
  (src/js/76zzzu-light.js; 40-render.js, 26-surface.js, 80-main.js)
  - Up to twenty-four lights a frame (from twelve), in the town, the Wood and every floor below.
  - More things give light: the Portal Court's portals and braziers in their own colours, the Wayfarer's Stones, the
    Glyph Deep's cabinet; after dark, the town's lit windows spill warm light onto the street.
  - Spells and blasts flare where they land and die away: fire orange, frost blue, lightning white, holy light gold,
    a blink violet, a summoning purple.
  - The party's torch is held in the right hand, a little up, not worn at the eye: what faces it is lit more, so
    corners and wall faces read in the torchlight.

A smoother start (v21.4)
  (src/js/40-render.js, 80-main.js, 36-looks.js)
  Measured in the browser the Timeline uses (QtWebEngine, Chromium 140) on the same machine, before and after:
  the page ready in 3.5 s (it was 6.7), a new game started in 0.4 s (it was a 1.4 s freeze), and the town's first
  seconds with one long frame (there were seven, up to 130 ms).
  - The textures go to the graphics card as their pixels, read off each picture, not as the picture itself - in this
    browser several times quicker (the town's set: 0.6 s, from 2 s at worst).
  - At the start one set is built and sent, not two: a look still decoding is waited for behind the title card.
  - Behind the title the sets go up a slice a frame, and the town's set (a new expedition's first) is made ready there,
    so starting a game swaps it in at once.
  - The fields', the court's and the cabinet's pictures count as the surface's, so they are never sent below ground.
  - A floor's mesh is made once on arriving (the mode changing inside the arrival made it twice), and the traces a fight
    leaves (remains, scorch, arrows) make it again once, on the next frame - not once each, there and then.
  - The automatic Detail no longer counts a loading pause as the machine being slow, waits three seconds on a new floor
    before judging, and needs thirty quick seconds, not ten, to step back up - no more stepping down and up at the start.

The court's keepers (the eighty-seventh big update - v21.3, UPGRADE_PLAN_16.md phase 3 - the plan complete)
  (src/js/69s-courtkeepers.js, 76zzzt-courtkeepers.js)
  - The noticeboard in the court's south-east corner: every place beyond the court in its own colour - the shaft, the
    seven portals, the Wayfarer's Stone - with its next step and who may go.
  - The Portal-warden by the east wall, a keeper in a grey-blue coat with a lantern on a staff: talk to them for how
    the court works (the walls by kind, the badges, the stone, the winch), and a word on something worth doing next.
  - The shaft's lift: at the shaft, with camps reached, Space offers the winch - the first floor, or the merchant's
    camp beneath any floor reached - instead of the old straight drop to the deepest camp.

The portals' own looks (the eighty-sixth big update - v21.2, UPGRADE_PLAN_16.md phase 2)
  (src/js/69r-portallooks.js, 76zzzs-portallooks.js)
  - Every portal drawn as its own place: the Mage Tower's rune-cut violet stone, Leshy's roots and antlers, Claudeita's
    rough rock with sand running down it, the Fortress's black stone bound in iron, Haven's red gothic arch, the Glyph
    Deep's green letters falling (the Neather Gate keeps its basalt) - and in each swirl a glimpse of the far side,
    by day or by night: the tower's lit window, the cabin's, the crag's mouth, the keep, the cathedral, the letters.
  - The twins in the Wood wear the same faces, so each pair is plain to see.
  - A badge over each arch: one figure for one hero, four for the whole party. Standing at a portal, the hint line
    names it, what's waiting there (the next floor, the next table, the levels paid) and who may pass.
  - Crossing: a swirl in the portal's colour over the view and a fade, and each portal its own note; near one, its hum.

The Wayfarer's Stone (the eighty-fifth big update - v21.1, UPGRADE_PLAN_16.md phase 1)
  (src/js/69q-waystone.js, 76zzzr-waystone.js; named apart from the dungeon camps' waystones)
  - A tall rune-cut stone on a dais in the Portal Court's south-west corner, and its twin by the Wood's road east of the fields.
    A hand on it takes the party to any place in the Wood it knows - the Wood gate, the First Glade, the farm, the
    Glyph Deep's cabinet, the Mage Tower, Leshy's cabin, Claudeita's crag, the Fortress - and the Wood's stone back to
    the court. It knows the gate and the glade from the start; every other place once the party has walked within two
    steps of it (and whatever the village already remembers from before the stone was raised). New places in the Wood
    join the stone, not the court, so the court never fills up again.

The Portal Court (the eighty-fourth big update - v21.0, UPGRADE_PLAN_16.md phase 0)
  (src/js/69p-portalcourt.js, 76zzzq-portalcourt.js)
  - The Keep-yard's walls pushed out to make a Portal Court, 7x9 inside (it was 5x5), still open to Shaft Lane.
  - The shaft in the middle; the Wood's portals on the north wall (the Mage Tower, Leshy's cabin, Claudeita's cave)
    and the south wall (the Fortress, the Glyph Deep); the world gates - one hero into another game - on the east
    (Haven's red portal, the Neather Gate). Every portal and the shaft can be walked to from the opening without
    stepping on another; the old dark plinths are gone, the postern is in the new north-east corner.
  - Each portal has a name stone at its foot, cut and gilded, a brazier either side burning in its own colour, and a
    ring of runes on the flagstones before it. Standing on one, the place is named for it.
  - Home through any Wood portal lands on its own twin in the court.

The Glyph Deep's portals (v20.3)
  (src/js/69o-glyphdeep.js; the green picture in 76zzzp-glyph.js)
  - A green portal on the Keep-yard's south row (between the Fortress's portal and Claudeita's) sets the party down by
    the cabinet; its twin in the cabinet's clearing takes them back to the yard.

The Glyph Deep, finished (the eighty-third big update - v20.2, UPGRADE_PLAN_15.md phase 2 - the plan complete)
  (src/js/76zzzp-glyph.js, 69o-glyphdeep.js)
  - The end of a game on the cabinet's screen: a tombstone with the hero's name, the level and what killed them; a
    trophy for the Unwritten undone; a tally for coming home; and what came home with them.
  - ? shows how to play, P the messages so far; > away from the stairs walks you to them once they've been seen,
    stopping when something shows itself or hurts you.
  - LORE.md has the cabinet's story.

The Glyph Deep, measured (the eighty-second big update - v20.1, UPGRADE_PLAN_15.md phase 1)
  (tools/glyphbot.js; the tuning at the top of src/js/64zzzc-glyph.js)
  - Traps, hidden in the floor until stepped on and shown (^) after: a dart, a pit that holds you a turn or two, a
    teleport, and a gong that wakes the whole level. One, and one more every four levels.
  - The deep's own player (tools/glyphbot.js) plays it to measure it: it found levels past 8 far too hard and the
    Unwritten unbeatable. Now monsters are a little under the level's number and fewer, the last level is the
    Unwritten's alone (four others, two healing potions in its room), it writes one glyph at a time and only when
    you're near, and hits a little softer. A hero of the level's own number reaches the stairs about 75 to 100% of
    the time with a couple of potions; the Unwritten falls to about half the level-20 heroes and nearly all at 23.

The Glyph Deep (the eighty-first big update - v20.0, UPGRADE_PLAN_15.md phase 0)
  (src/js/64zzzc-glyph.js the game, 69o-glyphdeep.js the cabinet's rules, 76zzzp-glyph.js the screen)
  - An arcade cabinet under a lean-to in a clearing north of the Wood's road: Space at it, choose who plays (one of the
    party, alone, with their real health, arms, armour and skill tree) and from which level (any reached so far).
  - Inside, a roguelike in letters, our own: twenty levels of rooms, doors and corridors, lit rooms seen whole, what's
    been seen remembered; turn by turn, moving into a monster fights it (the main game's hit, weak-spot and damage
    rules); nineteen monsters by depth with their own ways (fast, erratic, slow, regenerating trolls, draining wraiths
    and vampires, fire-breathing drakes, mimics that look like gold) and, on level 20, the Unwritten, who writes loose
    glyphs into the fight and smears across its room when hurt.
  - Things: $ gold, ! potions, ? scrolls (mapping, teleport, fire, enchant weapon, enchant armour), ) [ weapons and
    armour (wield and wear them inside), = " rings and amulets, % rations, , seeds for the South Fields, ~ inscription
    cards, * prize tickets. Keys: arrows / number pad / hjklyubn, g pick up, q r w W e d, . wait, > and <, i the pack;
    or click: a square to step toward it, a thing in the pack to use it.
  - At the stairs down: down to the next level with everything, or home with it all. The first time each level's
    stairs are reached, tickets, gold and a thing (better every fifth level; a rare card at 10, a charmed seed at 15)
    go straight to the party - once a level, ever. Beating the Unwritten and taking the last stairs pays the great
    prize once: 500 tickets, 3,000 gold, three high-end enchanted pieces, two rare cards and three charmed seeds.
  - Death: home with a tenth of their health and without what that level gave (the levels before are kept); the
    stairs up or walking away the same. Experience always.
  - What comes home is the game's own: the weapons, armour, jewellery, potions, rations and seeds go in the pack to
    use and wear; cards to the Claudescryption collection; tickets to the Joker; unread scrolls sold back for gold.
  - On the world map and the Goals page; toward the renown level (4 a level's stairs, 100 for the Unwritten).

The South Fields, finished (the eightieth big update - v19.5, UPGRADE_PLAN_14.md phase 5 - the plan complete)
  (src/js/76zzzo-fieldlife.js; the hands painted in 36c-cropart.js; tools/fieldbot.js and FIELDS.md)
  - The field through the year: frost on bare turned plots in winter, blossom along the rows in spring, fallen leaves
    in autumn.
  - The crew at work: the hands hired stand among the crops in straw hats - one with a hoe, one a watering can, one a
    basket - somewhere new every hour, and go home at night.
  - The books: tools/fieldbot.js works out what a plot makes a day for every crop over a season and writes FIELDS.md.
    It found the crops that fruit again earning five times the one-harvest crops; the prices were evened out (the
    regrowers a little down, the one-harvest crops up, the big ones' seed cheaper): the shed's crops now make about
    4.6 to 10.3 gold a plot a day at two stars, the found ones more.
  - LORE.md has the fields' history.

What the fields are for (the seventy-ninth big update - v19.4, UPGRADE_PLAN_14.md phase 4)
  (src/js/69n-fielduse.js, 76zzzn-fielduse.js)
  - The market stall in the Square: the fields' produce sells at its full worth, stars and all, and three crops a day
    are in demand at half as much again - from the pack or straight out of the silo, anywhere in town.
  - The Harvest Fair's contest (September's fair week): one entry a fair, scored on its stars and its kind against
    three of the village's; first, second and third pay renown and gold, and first a blue ribbon (an achievement).
  - The still in the shed: mana-blossom to a mana potion, two frost-berries to a healing potion, moon-melon to wine,
    coin-bean pods cracked for gold, and the Joker's roses traded to the Joker for tickets.
  - The request board asks for the fields too (a crop of three stars or more, a charmed crop), once they're laid out.
  - The fields count toward the renown level: a picking of ten, a giant, a fair won, every 200 gold sold.
  - (Three sounds named in earlier updates that the game didn't have - the anvil, turning earth - now use real ones.)

Seeds from everywhere (the seventy-eighth big update - v19.3, UPGRADE_PLAN_14.md phase 3)
  (src/js/69m-fieldseeds.js, 76zzzm-fieldseeds.js)
  - Eight rare crops (rhubarb, asparagus, artichoke, blackberries, raspberries, coffee, pineapple, kiwi) and six
    charmed ones that glow in the field and fetch a high price (mana-blossom, frost-berries, ember pepper, moon-melon,
    coin-bean, the Joker's rose). None is on the shed's shelf or the merchant's: each place has its own -
    the dungeon's spoils by depth, the Wood's forage nodes (berry canes), a game won at Leshy's (kiwi or another),
    the Mage Tower (mana-blossom for floors climbed), Haven's cold gardens (frost-berries), the island's warm side
    (coffee, pineapple, kiwi), Claudeita's cave (moon-melon), the Fortress (ember peppers), the pipe (a coin-bean for
    every level cleared), and "A rare seed" at the Joker's prize counter (60 tickets).
  - Cuttings: a crop picked at three stars or better sometimes gives a cutting - a seed that remembers its stars, so
    the plot sown from it never picks worse.

The village's hands (the seventy-seventh big update - v19.2, UPGRADE_PLAN_14.md phase 2)
  (src/js/69l-fieldhands.js, 76zzzl-fieldhands.js; the kit painted in 36c-cropart.js)
  - Sprinklers, made at the shed's workbench from a bar and gold and set on a plot: copper waters the four plots
    beside it (a copper, tin or bronze bar, 30 gold), iron the eight round it (iron or steel, 60), star-iron a 5x5
    (150). They water at every dawn; lifted, they go back on the shelf.
  - Cloches: a glass bell over one plot (30 gold and two island stones) - it can be sown with any crop in any season
    and grows through the winter.
  - The plan: mark the crop a plot should keep (the board's Plan mode); "Tend everything" sows the plan from the
    pack, pulls the weeds, picks what's ripe and waters as far as the can goes, in one go.
  - The field crew: hire one to three hands (6 gold a dawn each, from a purse the party fills). Every dawn each does
    fourteen jobs: weeds, picking into the silo (up to 600 things, with a seed box for the seeds that come back),
    turning and sowing the plan (buying seed out of the purse when the box is out), and watering. Unpaid, they stand idle.
  - The seed-maker: one of a crop, picked, makes two of its seeds.

Water and quality (the seventy-sixth big update - v19.1, UPGRADE_PLAN_14.md phase 1)
  (src/js/69k-fieldcare.js, 76zzzk-fieldcare.js)
  - Thirst: an unwatered crop stalls, and four dry dawns in a row wither it.
  - Weeds on bare turned earth after three dawns, and now and then among the crops; a weedy plot doesn't grow until
    they're pulled (Space or a click pulls them first).
  - Crows take a ripe plot left standing two dawns, unless the fields have a scarecrow (60 gold at the shed).
  - Stars, one to five, set at picking: two to start, one if never dry, one if composted, one if the plot grew
    something else last, and sometimes one for luck. A star is a quarter more on the price, and shows in the name.
  - Trimmings (pickings, pulled weeds, withered plants) go in the compost bin; five make a load, ready three dawns on.
    Compost a growing crop by hand, or turn on "compost when sowing".
  - Giants: a ripe 3x3 of pumpkin, watermelon, melon, cabbage or cauliflower may become one giant crop overnight,
    drawn over all nine plots; picked, it gives fifteen to twenty at its stars.

The South Fields (the seventy-fifth big update - v19.0, UPGRADE_PLAN_14.md phase 0)
  (src/js/69j-fields.js, 76zzzj-fields.js, 36c-cropart.js; the crops' pictures in 35b-croppack.js from tools/cropsheet.py)
  - The open bowl under the town's south wall becomes farmland: a new village building with four levels (24, 48, 72
    and 100 plots), the later ones wanting island timber and stone. A seed shed at its east end, a trough at its west.
  - Turn a plot, sow it from a seed in the pack, water it from the can (ten waterings, filled at the trough), pick it
    when it's ripe. Space on a plot does its next job; the fields' window (the shed, or "The fields" in the menu) is
    the whole board at once, with "Water what the can will" and "Pick everything ripe".
  - A crop grows a day for every dawn the party sees after a day it was watered, and rain waters every plot. In winter
    only kale, leeks and garlic grow. Peas, beans, tomatoes, peppers, corn, berries, grapes and others stand and fruit
    again after picking. A picked plant sometimes goes to seed and gives one back.
  - Thirty-nine crops (the Glade farm's six among them, and its seeds are the same seeds), each with its seasons, days,
    yield and price; the shed sells the season's seeds (half price at the Sowing).
  - The plants are real pixel art: [LPC] Crops (CC-BY-SA 3.0+ / GPL 3.0+, src/art/CREDITS-crops.txt) and josehzz's
    Farming Crops (CC0), four growth stages each, two plants a plot in the 3-D view and on the window's board.

The tongue of the last bell (the seventy-fourth big update - v18.8)
  (src/js/69i-thread.js, 76zzzi-thread.js; the canon in LORE.md)
  One story through every part of the world, in a new Journal page, "The last bell". In the Undercroft's bell-yard the
  Bell-Founder's Boy swings a bell with no tongue. The portals round the shaft open on what the Root dreams, and it
  dreams in the city's stuff, so the tongue's ten makings are out there: the bell-yard itself, the dungeon's bell-rope
  grooves (past floor 15, or Brother Cael's bell), the Mage Tower's tenth floor, Haven's eighth level, the island (a
  homestead or the Hollow Mason), a boss of Claudeita's cave, the Fortress's fifth floor, the Brass Warden down the
  pipe, three games won at Leshy's table, and Joker level 10. Each is found by doing the deed (and whatever a party
  has already done counts), with its own page. All ten and a metal bar go to the smith (200 gold) to be cast; the
  tongue, taken down to the bell-yard, answers him (150 renown, the title "who Answered the Bell"). After that the
  Lich King rises a fifth short, every time. The Goals page shows the next step, with Go.

One name across the world (the seventy-third big update - v18.7)
  (src/js/69h-renownlv.js, 76zzzh-renownlv.js)
  - Every part of the world now earns renown, counted from its best ever so nothing pays twice: the Mage Tower (3 a
    floor), the Fortress (5 a floor), Claudeita's cave (2 a depth, 15 a boss, 25 a win), Leshy's table (12 a game won),
    Haven (3 a level reached), the pipe (10 a level), the island (2 a visit, to 40) and the Joker (3 a Joker level).
    What a party had already done is counted in the first time.
  - All the renown ever earned makes one renown level, 1 to 30 (spending it on the village never lowers it), shown in
    the village's window with where it came from, and first on the Journal's Goals page.
  - Its perks reach everywhere: more experience and weak spots in every fight (the solo runs too), Luck and then
    every stat, Life in Haven, more Joker tickets, softer knocks down the pipe, health from each kill, gold from
    kills, and +1 attack and defence. A level gained plays the level-up jingle.

The tree goes with them (the seventy-second big update - v18.6)
  (src/js/69g-soloedge.js; small hooks in 64j-fortress.js, 64o-craftlife.js, 61g-cavemouth.js)
  What a hero has learned in the skill tree - and the weak spots, mending and spoils of their gear - now counts when
  they go somewhere alone:
  - the Mage Tower, the Fortress and the island: weak spots (double blows), health and mana from each kill, more gold
    and experience from each kill (attack, defence and health already came through);
  - Claudeita's cave: the casting stat is the whole stat, tree included, and weak spots make the wands stronger;
  - Claudeablo: the tree's stats become Haven's (Strength and attack, Dexterity, Intelligence and Wisdom as Magic,
    Constitution as Vitality, health as Life, mana, aim as To Hit) while the hero is there - never saved into Haven;
  - the pipe: the tree's defence takes 4% a point off every knock, to half at most.
  The skill tree's window lists what it comes to for the hero, under "When alone".

The world on one page (the seventy-first big update - v18.5)
  (src/js/69f-worldmap.js, 76zzzg-worldmap.js)
  - The world map (the World map button): a painted map of Caer Duin on its hill and the Keep-yard, the Deep Wood with
    the farm, the cabin, the Mage Tower, the Fortress and Claudeita's crag. Every place is a pin; pointed at, it says
    what's there, and a gold mark with a count shows where something waits - requests at the well, rewards at the
    Joker, a boon or skill points at home, a building the village can now afford at the guildhall.
  - Fast travel: clicking a pin takes the party there from anywhere in the town or the Wood (not from below - the
    shaft and the portals bring you back up), facing the way in; a door that opens is opened.
  - Goals, a new first page in the Journal: every part of the game and what's next in it - the town's requests and
    next build, the heroes' choices, the dungeon, Leshy's table, Haven, the island, the pipe and the Joker - each with
    a Go button to the place.

The town's asking (the seventieth big update - v18.4)
  (src/js/69e-requests.js, 76zzzf-requests.js)
  - The request board at the well (the town's Requests button): three notes a day from the residents, each wanting
    something from a different part of the world - island timber, stone or bars, a gem or an essence from the dungeon,
    meat or food, something from Haven, Joker tickets - or a deed done since it was posted: a floor reached, fights won,
    Claudescryption hands, a trip down the pipe or into Haven, fish from the Pond, a night at the Joker. Done, a note
    pays renown and gold; one left undone stays on the board the next day.
  - Village upgrades want other places' things: the later levels of the smith, library, shrine, home, tavern,
    merchant, guildhall, garden and farm ask for island bars and stone, gems and essences, Haven's finds or meat as
    well as renown, shown beside the cost and taken when the building goes up. Early levels are as they were.

The ways between (the sixty-ninth big update - v18.3)
  (src/js/64zzza-links.js, 76zzze-links.js)
  - Haven's potions come home: potions a hero found in Claudeablo (beyond those they went in with, which stay there as
    the gold does) become the party's own - healing, mana, and the full ones as strong healing.
  - The party's relics go in: a relic, unique or heirloom a hero wears through the red portal is echoed in Haven - a
    rare piece of the same kind, made for their level, bearing the relic's name - once for each relic.
  - The pipe's coins pay tickets at the Joker too: one for every five coins carried out (the gold as before).
  - Island tempering at the smith: a metal bar (the island's, or the smelter's) and an essence (the dungeon's) put +1
    on a worn weapon or armour, once a piece, for 40 gold.

Skill trees (the sixty-eighth big update - v18.2)
  (src/js/64zzz-skilltree.js, 76zzzd-skilltree.js)
  Every calling has a tree of three branches, each its own names (the Knight's Blade, Shield and Banner; the Mage's
  Flame, Ward-runes and Library; ...), five tiers and fifteen ranks a branch. A skill point comes with every level
  gained (heroes already levelled have theirs waiting); a tier opens with two more points spent in its branch, the
  capstones at level 15. The first branch is blows for the warriors (their key stat, attack, weak spots, to hit) and
  spells for the casters (their key stat, spell power, magic, magic from each kill); the second standing up to it
  (Constitution, defence, health, mending each round); the third luck and the spoils (Luck, experience, gold,
  quickness). Two capstones teach the traits of the path the hero didn't choose at level 5; the third steadies the
  whole party (+1 defence) and adds 1 to every stat. Every rank works through the game's own reckonings, the same as a
  ring or a blade. "Skill tree" on a hero's sheet opens it; the party card says "Skill!" while points wait; a tree is
  unlearned for nothing in town.

Gear score and auto-manage (the sixty-seventh big update - v18.1)
  (src/js/64zzy-automanage.js; the pack's button and figures in 70-ui.js and 75-bag.js)
  - Gear score: each thing worn scores by its power (weighted by slot: the weapon most, then armour, off hand, helm,
    then boots, cloak, rings, amulets, trinkets), its worth and its rarity (cursed much less; a weapon a hero isn't at
    home with counts for less in their hands). Each hero's is the sum of what they wear - on their sheet - and the
    party's the sum of all four, shown in the pack with a bar for each hero.
  - "Auto-manage: Y/N" in the pack (kept in the settings): when Y, known gear coming into the pack (loot, chests, the
    casino's spoils) - and everything there when it's switched on - goes to the first hero, left to right, whom it
    betters by gear score; what they took off returns to the pack and may suit the next hero along. Unknown and cursed
    things are left alone, nothing moves in a fight, and a film plays the changes back as they were made.

A level gained (the sixty-sixth big update - v18.0)
  (src/js/76zzzc-levelup.js; 62-combat.js and 64-meta.js mark a real level gained, 64l-claudeablo.js calls it too)
  Every level gained - in a fight, at camp, home from the Mage Tower, the cave or the Fortress, at the Joker's tables,
  or in Claudeablo - has its own seven-tone jingle (G C E G, E G, a high C held with a shimmer, on a bell voice) and
  its own fireworks on the hero's card: small rockets behind it in gold and the hero's colour, sparks off its edges, the
  border running with light, and "Level N!" rising off it. No window to close. Heroes levelling together take turns
  under one jingle; when the party bar isn't showing, the burst goes up at the top of the view. Reduced motion: the
  border glows only.

The floor's spoils (the sixty-fifth big update - v17.9)
  (src/js/64zzx-spoils.js; shown on the result card, 76zzp-controls.js)
  Time at the tables now counts like time in the dungeon. Every play (worth two tickets) and every ticket won by
  playing gives every hero standing experience (0.4 + 0.35 x the party's highest level, per ticket), and every fifty
  turn up a piece of gear to wear - weapon, armour, shield, helm, ring, amulet, boots or cloak - made for the depth of
  the party's highest level, sometimes enchanted, into the pack. Tickets handed over (the Almanac, the visit card, the
  Joker's bank, the books, quests, the story, the daily wheel) and practice don't count. The pace is held to a
  dungeon's whatever the stakes: at most 25 tickets' worth a real minute, banked up to six minutes' worth.

The Joker's story (the sixty-fourth big update - v17.8)
  (src/js/64zzw-story.js, 76zzzb-story.js)
  - Five chapters told by the Joker himself - in his alcove at the end of the foyer on his floor, or from the story's
    door on the club strip - opened at Joker levels 3, 7, 12, 17 and 22: the card that floated when the lower town
    drowned, the girl who picked him up, the house she built on a laugh, why the floor goes back so far, and what he
    wants from the party.
  - The Final Night (Joker level 25, every chapter heard): the Joker plays the party at five of his games in turn -
    three alike within 15 pulls at the reels, three blackjack hands won before three lost, more than 600 at the Tavern
    Board, 8 times the chip or better on the high Drop Board within 12 drops, two pair or better twice in 6 deals at
    Jacks or Better. A round lost starts over; practice doesn't count. Winning all five ends the story: 5,000 gold,
    1,000 tickets, a rare card, the charm the Joker's Own (3% hits, 3% criticals, 5% gold and experience from fights)
    and the golden crown for his card.

Into the Joker (the sixty-third big update - v17.7)
  (src/js/64zzv-jokerfloor.js, 76zzza-walk.js; hooks in 60-game.js, 61-explore.js, 70-ui.js, 73-play.js, 80-main.js)
  - The street door now asks: "Enter the Joker" or "See the games" (the gallery, as it was).
  - Entering walks the party into the Gilded Joker as a place - floor -9, the same for every seed, its own set of
    surfaces (red carpet with a gold figure, damask walls over a gilt rail and panelling, a coffered ceiling), its own
    music and murmur, and no torch burning. A foyer from the street door, and the great hall: every table on the floor
    in rows by kind (the fairground to the west, the card tables, wheels and machines, the arcade wing to the east),
    each drawn as what it is (a reel cabinet, a round card table under its lamp, a wheel on its stand, an arcade
    cabinet, a striped fairground booth, the pond's tub), and the house's seventeen counters along the north wall, each
    with its sign. The six residents stand by their favourite tables.
  - Step onto a table and press Space to sit down (its window opens there); a counter opens its page; a resident has
    a word; the street door goes back out into the town beside the casino's door.

The Joker's charms (the sixty-second big update - v17.6)
  (src/js/64zzu-charms.js, 76zzz-charms.js; 62-combat.js asks chPhoenix when a hero would fall)
  Eleven charms, kept with the floor's books and worn into the world - one at a time, two from Joker level 20, three
  from 40 - from the Charms door on the club strip.
  - Earned, the floor's capstones: the Loaded Die (level 10 at five cabinets: 5% more hits), the Joker's Wink (900 at
    the Tavern Board: 5% more criticals), the Phoenix Card (the residents' table cleared at a 500-gold buy-in: once an
    expedition a falling hero stands at 1), the Cartographer's Ace (three collection books full: each new dungeon
    floor's walls mapped on arrival), the Night Owl (the golden carp and the whole creel book: 10% more experience from
    fights), the Gambler's Purse (the progressive jackpot won: 10% more gold from fights) and the Crown of the Week
    (first in a Joker's Week: 2% hits, 2% criticals, 3% gold).
  - Bought with tickets: the Lucky Coin (1,500: once a floor a sprung trap fails), the Rabbit's Foot (2,000: once a
    floor a flight can't fail), the Wanderer's Token (1,200: a camp rest mends a quarter more) and the Golden Ticket
    (2,500: 15% more tickets on the Joker's floor).

The Almanac and the visit calendar (the sixty-first big update - v17.5)
  (src/js/64zzt-almanac.js, 76zzy-almanac.js)
  - The Joker's Almanac: thirty steps a real month, named for the month's festival, turned by the JXP earned anywhere on
    the floor (fifty a step; the week's game counts double; nothing in practice). Every step pays - tickets, gold, a
    potion, a card at every fifth - the tenth, twentieth and thirtieth more, and the thirtieth leaves the month's
    keepsake in the cabinet. Steps not collected wait a month.
  - The visit calendar: a card of 28 stamps, one for each real day the party comes in (a missed day costs nothing),
    stamped at the door on the first visit of the day; each stamp pays, the 7th, 14th, 21st and 28th more.

Your history (the sixtieth big update - v17.4)
  (src/js/64zzs-history.js, 76zzx-history.js)
  Each visit with anything in it is written into the floor's books when the party leaves (the last 200 kept): when,
  how long, gold laid and paid back, up or down, tickets, the tables, the best moment, the Joker level. "Your history"
  on the club strip shows the record: five figures (visits, time on the floor, up or down in all, tickets won, the
  Joker level), each visit's up or down as a bar, the running total, the most played tables, tickets by month and the
  Joker level over the visits - point at a mark for its figures, or show it all as a table.

Life on the floor (the fifty-ninth big update - v17.3)
  (src/js/64zzr-week.js, 76zzw-floorlife.js)
  - The residents are about: over the gallery a band of the floor at night where the six residents and a few
    visitors stroll between the tables and talk - about the floor, the party's big wins, the week's board and who the
    party has just gone past on it. At a table, now and then one of them drops by and watches, and has a word when the
    party wins big.
  - The Joker's Week: each real week (Monday to Sunday) one game of skill - a cabinet (furthest level) or the
    fairground or the pond (best score) - is the week's game, posted on a banner over the gallery with the party's
    place. The residents and visitors put their bests on the week's board day by day; the party earns double JXP at
    the week's game. When the week is out it pays by place (first 1,500 gold, 300 tickets and a rare card; second 800,
    200 and a stronger card; third 400, 150 and a card; fourth to tenth 60 tickets), collected on the week's page any
    time in the next four weeks.
  - From the sweep (tools/sweep.py, run again): the tables' bar, grown with the new buttons, takes a second line on a
    narrow window; the reels no longer trip if the party leaves while they turn. No script errors, nothing left running.

The wardrobe and the books (the fifty-eighth big update - v17.2)
  (src/js/64zzq-wardrobe.js, 76zzv-wardrobe.js)
  - The Wardrobe (a door on the club strip): looks opened by the Joker level - six table felts (green, royal blue at 3,
    crimson 7, midnight violet 12, onyx 18, gold leaf 30), five chip sets (classic, jade 5, obsidian 11, pearl 16,
    gilded 25), six card backs (ruby, sapphire 4, forest 9, the Joker's own 14, starfield 22, gilded 35), five cabinet
    trims (oak, brass 6, silver 13, neon 20, gold 28) and six hats for the Joker's card (the jester's cap, a crown at
    10, a wizard's hat 17, a top hat 24, a laurel 40, the golden crown 50). What's worn is worn across the floor: the
    felt behind every table, the chips in the bet rows, the card backs at blackjack, hold'em and patience, a trim round
    the screens.
  - The Collections (a door on the club strip): seven books filled from play - the reels' nine lines, video poker's
    paying hands, the Joker's Wheel's seven slots, every number won straight up at roulette, the high Drop Board's
    thirteen bins, the hands won at the residents' table, the Bell Hall's patterns - with the pond's creel book beside
    them. Each new entry is told on the table's note; a full page pays 100 tickets, 150 JXP and a card (rare for the
    long pages). Nothing is noted in practice.

Fast and auto (the fifty-seventh big update - v17.1)
  (src/js/76zzu-speed.js)
  - Fast: at the tables where the waiting is only watching (the reels, roulette, blackjack, video poker, the dice, the
    wheels, the slips, the Pin Garden, the Drop Board, the lottery's draw, bingo, hold'em, the Hexed Wand, the Pit,
    Claudeatro, the coin pusher), "Fast" on the bar runs the window's animations and pauses 2.5 times quicker. The
    results and pays are the same; it's remembered; it isn't offered where timing is the game.
  - Auto: at the reels, roulette, the Joker's Wheel, the Drop Board and the slips, "Auto" plays 10, 25, 50 or 100 in a
    row with the bet on the board, stopping on a big win (10 times the stake, if asked), when the purse runs short, on
    any key or click, or on leaving the table.

How to play, and practice (the fifty-sixth big update - v17.0)
  (src/js/64zzp-practice.js, 76zzt-howto.js)
  - Every one of the 55 tables has a How to play card: its picture large, what it's for, three or four steps, its keys
    and how it pays. It opens by itself the first time the party sits down, and again from the "?" on the table's bar.
  - Every table that takes a stake can be practised (the Practice switch on its bar, or "Try it in practice" on the
    card): nothing is laid or won - no gold, tickets, cards, JXP or board places - and when practice ends (switched off,
    or leaving the table or the Joker) the purse and the floor's whole books are put back exactly as they were, so
    nothing bought in practice (bait, balls, a seat) can be kept. The free tables, the daily wheel, the lottery and
    the idle works don't offer it.

The house's books (the fifty-fifth big update - v16.9)
  tools/balance.js plays every game of chance many thousands of times (a plain, sensible way of playing each) and
  reads the games of skill from their pay tables; it writes BALANCE.md and the figures for the House odds page
  (src/js/64zzo-odds.js, read by 76zzs-odds.js) - a new door on the club strip, with each game's return, tickets and
  JXP for every 100 gold, the party's own return beside it, and each table's Figures page showing the house's figure.
  Exact figures are worked out where the odds are known (roulette, the Joker's Wheel, the Drop Board, the pass line).
  What the books found, and the changes made:
  - The Tavern Board paid a perfectly steady hand 108%: its top pays are trimmed (85% at 800, 98% at 900) and the
    fairground's pays now round down.
  - The fairground and the arcade cabinets paid the same tickets on a 1-gold stake as on a 5-gold one: full tickets
    now need a 5-gold stake (less in proportion below).
  - The Bell Hall paid 3 tickets on every win whatever the room: its tickets now come by the gold won (one per 25).
  - Small stakes counted a whole JXP each: a part of a JXP now carries, so they add up instead; bingo's balls and the
    fairground's hundreds no longer count as levels for JXP.

Joker standing (the fifty-fourth big update - v16.8)
  The party's standing with the Joker (src/js/64zzn-joker.js, 76zzr-joker.js; fights read it in 62-combat.js):
  - JXP (Joker experience) from play anywhere on the floor: 1 for every 10 gold laid (small stakes add up; up to 50 a stake), 1 for every
    4 tickets won, 3 for each level reached at a cabinet, 10 for a place on a board and 25 more for a record, 40 for a
    quest, 30 for a tournament night (60 in the top three), 80 for beating a high-roller.
  - The Joker level, 1 to 50, kept with the floor's books so it carries from expedition to expedition. Each level owes
    20 gold for each level number, and a card at every fifth (stronger from 15, rare from 25), collected on the Joker
    standing page with the bonus tickets the level has banked.
  - What the level gives: 1% more tickets for each level past the first (to 30%, banked); 2% more off the prize
    counter at every sixth level (to 10%); out in the world, 1% more gold from fights for each level past the fourth
    (to 20%), 5% more experience from fights at 10 (10% at 20, 15% at 30, 20% at 40), and a Joker's Cordial in the
    pack at the start of every expedition from level 8 (two from 18, three from 28).
  - The Joker standing page (the first door on the club strip, or the level on any table's bar): the Joker's card,
    the bar to the next level, what's waiting, the bonuses now, the perks and where the JXP came from.

The Joker's own air (the fifty-third big update - v16.7)
  Sound and season on the floor (src/js/76zzq-atmos.js):
  - The Joker's music: a lounge tune in the music engine (Mixolydian, 104 to the minute) with a walking bass and swung
    brushes, while the party is inside; the tune it came in with comes back when it leaves.
  - The floor's air: a crowd's murmur (shaped noise, rising and falling), full in the gallery and softer at a table,
    and now and then a bell from the reels, coins in a tray, chips clacking or a cheer.
  - The season, from the game's calendar: a painted banner over the gallery (spring's blossom and lanterns,
    Midsummer's lanterns and maypole, the Harvest Fair's striped stalls with pumpkins, apples and sheaves, the midwinter
    Joker in his fur-trimmed cap with holly and candles), the season's colour on the window's frame, and its weather
    drifting over the floor (petals, fireflies, leaves, snow - still with reduced motion). The week's festival, if one
    is on, is named on the banner.

One way to play (the fifty-second big update - v16.6)
  The same controls and the same result at every table (src/js/64zzm-result.js, 76zzp-controls.js):
  - Keys everywhere on the floor: Space or Enter does the table's main action (the arcade cabinets keep their own
    keys), Esc goes back to the gallery (and from the gallery, out of the door), [ and ] step to the table before or
    after. The keys are written on every table's bar.
  - Whatever a play wins - gold, tickets, a card - comes up on one card at the foot of the window when the play is
    done, counting up; wins close together add up on the same card. A stake's tickets and Hold'em cash-outs aren't
    counted as wins.

Finding your way round (the fifty-first big update - v16.5)
  The gallery and the door (src/js/64zzl-lobby.js, 76zzo-lobby.js; the gallery's own changes in 76ze-gallery.js):
  - A search box (names and descriptions), a sort (as on the floor, most played, most tickets won, A to Z), a
    Favourites tab with a star on every card and on every table's bar, a "Recently played" row of the last eight
    tables opened, and a green "New" ribbon on every table the party has never tried.
  - Figures for every table (the "i" on its card, or Figures on its bar): times played, gold laid and paid back, the
    return so far with a break-even bar, up or down, tickets won there, the best score, first and last played.
  - The reckoning at the door: leaving after a visit with anything in it shows the evening's bill - time on the floor,
    the tables played, gold laid and paid back, the purse before and after, tickets, the best moment and the cards -
    with Leave the Joker or Back to the floor.

The sweep (the fiftieth big update - v16.4)
  tools/sweep.py opens all 55 tables in a real browser engine at a normal and a narrow window, plays a few rounds with
  clicks and keys, and reports script errors, loops or timers left running after leaving, and anything that runs off
  the edge. Its first run found no errors and no leaks; sixteen tables' side panels ran off a narrow window, and now
  drop under their pictures instead.

The floor's big nights (the forty-ninth big update - v16.3)
  Four things across the Gilded Joker (src/js/64zzk-floor2.js, 76zzn-floor2.js):
  - The progressive jackpot: a marquee over the gallery (and a ticker on every table's bar). It starts at 1,000 gold,
    takes 2% of every stake on the floor and a little each real hour, and must go by 4,000 - at a point the house
    picks in secret. Once past it, the next stake at a jackpot table (the reels, video poker, the Joker's Wheel,
    roulette, the Pin Garden, the Drop Board, Fortune Slips) wins the lot, with 150 tickets, a rare card and fireworks.
  - Happy hour: each real day one ticket-paying game has an hour between noon and eleven at night when its tickets are
    doubled; posted on the gallery all day, flashing while it's on, with a ribbon on the game's card.
  - High-roller challenges: each real day one of the six residents brings a wager (200 to 1,000 gold, over the house
    limit) - heads-up hold'em (first to take all the chips) or a score to beat at the Tavern Board, Rune-Roll or
    Hoop-la. Take it or let it go; a win pays double, with tickets and a card the first time you beat each resident.
  - The Ticket Exchange: sell tickets for gold or buy them with gold at rates that drift day to day (buying always
    costs well over selling pays), with a chart of the last fortnight; daily limits.

The town's draws (the forty-eighth big update - v16.2)
  Three new games and a celebration (src/js/64zzj-draws.js; 76zzj-fireworks.js, 76zzk-lottery.js, 76zzl-plinko.js, 76zzm-pond.js):
  - Fireworks: a big win - ten or twenty-five times the stake, a great deal of gold at once, a rare card, a hundred
    tickets or more - sends rockets up over the window when the table shows its result: peonies, rings, gold willows,
    palms, crossettes and hearts, with a whistle, a boom and a crackle, and a banner (BIG WIN, HUGE WIN, JACKPOT - a
    finale with a rain of gold). Cash-outs are not wins. With reduced motion asked for, only the banner.
  - The Town Lottery: slips at 2 gold, six numbers from thirty (or quick picks), up to 25 a draw; the draw is at eight
    each evening, real time. Watch it: the drum turns and six balls ride the chute, lighting your numbers. Three matched
    pay 8 gold, four 60, five 1,200 and a rare card, six the town jackpot (from 5,000, growing every night, now and
    then won by someone in the village).
  - The Drop Board: plinko - a big chip down twelve rows of pegs into thirteen bins; low, middle and high risk boards
    (0.2 to 120 times the stake), each about 96% back; ten times or better pays tickets, the high corner a card once.
  - The Fishing Pond: bait at the shed, then cast (hold and let go), strike when the float goes under, and play the fish
    in against the line's tension. Ten kinds (eels and catfish only after dark, real time; the golden carp rare); the
    fishmonger pays by weight, every fish pays tickets, and the creel book keeps the best of each (a card when full).

The floor's evenings (the forty-seventh big update - v16.1)
  Four things across the whole Gilded Joker floor (src/js/64zzi-floor.js, 76zzi-floor.js), on the gallery's club strip:
  - The prize counter grows with the tickets spent - glass cases, the velvet shelf, the Gilded Vault - each step 5%
    more off every price and another of the day's specials: rotating stock that changes each real day (deep-delve
    gear, crates of potions, card packs, phoenix feathers, gilded relics, rare packs, the Joker's box), a few of each.
    One everyday prize is the day's bargain at a quarter off.
  - Tournament night: each day one arcade cabinet hosts a tournament against fifteen villagers and visitors; 25 gold
    enters for three games, the best level reached counts (score breaks ties); settle up for the purse (first, second
    and third in gold, fourth to eighth in tickets, and a rare card the first time you win each cabinet's).
  - Quests: three requests from the residents at a time - try so many tables, lay or win so much, reach a level at a
    cabinet, make a board, play a table so often - paying gold, tickets and sometimes a card. Swap one for 10 tickets.
  - The VIP room: for Platinum members, or with a pass from the counter (3,000 tickets). Raise the limits to 5,000 gold
    a bet (a 1,000 chip, and 1,000 and 2,500 buy-ins at the Residents' Game), a daily drink and 20 tickets on the house,
    and the tournament leader's level shown.

The residents' table and the Bell Hall (the forty-sixth big update - v16.0)
  Two social games on the Gilded Joker's floor (src/js/64zzg-holdem.js, 64zzh-bingo.js; 76zzg-76zzh):
  - The Residents' Game: fixed-limit Texas hold'em against four of the village's six residents - the tavern-keeper
    (calls anything), the merchant (counts the odds), the smith (plays few, plays hard), the librarian (a careful
    rock), the priest (steady, a little hopeful) and the farmer's hand (wild and fearless) - each judging their cards
    by a quick count of a hundred deals against the pot's price, bent by their nature. Buy in for 50 to 500 gold, play
    as many hands as you like, cash out between hands; side pots handled. Tickets for strong winning hands and for each
    resident sent home; a royal flush brings a rare card, clearing the table a card the first time at each buy-in.
  - The Bell Hall: 75-ball bingo in the old chapel - up to four cards in the Copper, Silver or Gold Room (2, 10 or 50
    gold a card), a pattern each game in turn (any line, corners, the X, the frame, coverall), daubing by hand or by the
    hall's dauber, "Bingo!" to call; every finished card shares 85% of what the hall took. Tickets on a win; a card for
    the first coverall.

Four cabinets and a vault (the forty-fifth big update - v15.9)
  Four more arcade cabinets on the common works and a free puzzle (src/js/64zzf-arc2.js; 76zzb-76zzf):
  - Gryphon Joust: gryphon riders over a lava lake - flap and steer; the higher lance unhorses, the lower falls; catch
    the egg a fallen rider leaves before it hatches something worse. A wave cleared is a level.
  - The Courier's Round: ride up Market Row throwing scrolls into the lit houses' letter-boxes, dodging dogs, carts and
    barrels; deliver to most of the street's subscribers to clear it.
  - The Undercroft Sprint: an endless run through the tunnels - jump pits and spikes, slide under beams, duck bats,
    gather coins; each stretch reached clears a level and the pace rises.
  - The Rune Bastion: tower defence - set fire (bursts), frost (slows) and arcane (long reach) runes by the goblins'
    road with the mana the fallen drop, strengthen them to three pips; runes and mana carry from wave to wave.
  - The Vault Runes: a free rune-lock puzzle (lights-out) - touch a rune to turn it and its neighbours, light them all;
    tickets each vault, gold the first time, a card every third vault; corners join in from vault 8.

The luck and the fair (the forty-fourth big update - v15.8)
  A new Luck shelf and two more fairground stalls (src/js/64zzd-luck.js, 64zze-fair2.js; 76zv-76zza):
  - The Pin Garden: pachinko - balls a gold apiece, shot with a handle through brass pins into start pockets, windmill
    cups and a tulip that spins three drums (three alike: Fever, 60 balls and a card); balls exchanged any time at 85
    gold a hundred and a ticket a ten. The handle has its sweet spots.
  - The Joker's Wheel: a big wheel of 54 slots paying 1 to 40 to 1; the Joker brings a rare card.
  - Fortune Slips: copper, silver and gold scratch cards scratched with the mouse; three alike wins, three cards a card.
  - The Prize Wheel: a free spin each real day for tickets, gold, a potion or a card.
  - Hoop-la: ten rings at a table of bottles (green 1, blue 2, gold 5, the red one 10); gold by points, a ticket a point.
  - The Crossbow Range: a shooting gallery on the arcade works - ducks, dragons, stars and the keeper's lantern on
    three rails, bullseyes double, a mark to make each round.

Six more tables (the forty-third big update - v15.7)
  - Bones (64zy-craps.js; 76zp): craps at the true odds - Pass and Don't Pass, the Odds behind (2:1, 3:2, 6:5), the
    Field, Place 6 and 8 at 7:6 and Any Seven at 4:1; tumbling dice; a card for a shooter who makes four points.
  - The Tavern Board and Rune-Roll (64zz-fair.js; 76zq, 76zr), under a new Fairground shelf: darts (eight rounds of
    three with a wavering hand) and skee-ball (nine balls, aim and power) - a stake a game, gold by the score, a ticket
    a 20 (darts) or a 10 (skee), a card the first time each high mark is passed, high-score boards.
  - The Bard's Stage (64zza-bard.js; 76zs): a rhythm game - strike notes on four lanes to a tune made from the level's
    seed and played with Web Audio; a combo multiplier and a crowd's cheer; chords from level 4.
  - The Patience Table (64zzb-patience.js; 76zt): Klondike and FreeCell, free - drag or click, double-click home,
    moves taken back, safe cards put up, the bouncing-cards finish; gold and tickets a win, cards at the 1st, 5th,
    15th and 40th.
  - The Trapfinder's Grid (64zzc-traps.js; 76zu): minesweeper on a trapped flagstone floor, free - the Cellar, the
    Crypt and the Catacomb, pennants, lifting round a number, a lantern; gold, tickets and a card the first time each.

Six new arcade cabinets (the forty-second big update - v15.6)
  A common works for level-by-level cabinets (src/js/64zr-arcfw.js; 76zi-arcfw.js) - one stake a game, gold for every
  level cleared every game, prize tickets by the level's number, a card every third level the first time, a high-score
  board and a daily-challenge place for each - and six cabinets built on it:
  - The Wyrm's Feast (64zs/76zj): a snake game - a wyrm eating glimmer berries in a walled garden bed, stones from level 3.
  - The Barrow Crawler (64zt/76zk): a centipede game - a gnome against a long crawler winding down through toadstools,
    and a spider from level 2.
  - The Belfry Climb (64zu/76zl): a climbing game - up the bell tower's sloping beams and ladders while a troll rolls
    kegs (jump them for 100), wisps from level 3; ring the bell.
  - The Skyreach Landing (64zv/76zm): a landing game - set a sky-skiff down softly and upright on ×2, ×3 or ×5 pads among
    floating isles; stronger pull and less fuel each level, wind from level 4.
  - The Rampart Battery (64zw/76zn): a defence game - burst falling embers with bolts from three mana wells before they
    reach six cottages; splitting embers from wave 3, a fire-drake from wave 5.
  - Glimmerpop (64zx/76zo): a bubble shooter - pop three of a colour in an alchemist's still, drop what hangs; the
    ceiling comes down every few shots.

The Prize Counter (the forty-first big update - v15.4)
  Every table on the casino floor now hands out prize tickets (src/js/64zq-prizes.js; 76zh-prizes.js): one for each 30
  gold staked at any table, one for each 50 gold a free table pays (the Mint, the Shelter, the Lexicon Engine, the
  Conduit), 2 for each blind beaten at Claudeatro (5 for a boss), 3 for a place on a high-score board and 10 for a new
  record; odd gold carries over. The Prize Counter, reached from the gallery's strip, trades them for pouches of gold,
  torches, antidotes, healing and mana potions, phoenix feathers, mystery parcels, weapons, armour, shields, helms, an
  enchanted piece (all made for the deepest floor reached) and common, stronger and rare Claudescryption cards. Gold
  is the poorest buy on purpose - a ticket is worth at most an eighth of a gold - so no table can be played at a profit
  for its tickets. The ticket count shows in every table's bar, a ticket hopping up as they come.

The polish pass (v15.1 onward)
  Going through the casino's tables one by one for their looks: more polish and more animation, the games as they
  were.
  - v15.3, the last seven - Shatterpane to Claudeatro:
    Shatterpane's window under a stone arch, its coloured light falling faintly to the floor. Starstone Drift
    with a second nebula and a ringed planet far off. Moatleap: lily pads and reeds on the moat, sunlight
    glinting on the water, banners on the wall. Runestep Pyramid under stars and a slow aurora. Wyrmhold
    Pinball: lamps round the dragon that light as it weakens, a chrome glint along the rails, the ball's shadow
    and trail. The Wishing Claw: a spotlight on the pit and reflections drifting over the glass. Claudeatro's
    lobby on a gilt-edged felt, with pill-shaped wagers that lift and the chosen deck glowing. No more than
    three of the floor's notices at once.
  - v15.2, sixteen tables more, from Runefall to the Hexmarch:
    Runefall lit by two flickering torches, its embers smouldering, a ring where each rune is struck, the
    Well's water moving and the slate's edges in shadow. Lantern Lane Dash at night: pools of lamplight round
    the posts, the carts' lamps and the hero's own lantern, dust on each hop, a splash or a crash when caught.
    The Gemcutter's Tray: stones that cast shadows and catch the lamp in glints, the chosen one breathing, a
    ring where stones are cut, a nap to the velvet. The Tilewright's Table lacquered red with a gilt border and
    clouds, the tiles rounded ivory on jade with soft shadows, and the free tile under the mouse lifted.
    The Hexed Wand: dust drifting in the lamp's beam, a grained wooden rim with a brass edge, the felt lit from
    above. The Gilded Pit's screen given a glass sheen and its winning lines pulsing. Runestack: light rippling on
    the water's surface, bubbles rising, the column under the falling stone lit, a streak where a stone is
    slammed down. The Gilded Cascade: a shimmer across the glass, light running along the pusher, the tray
    glowing as coins land. The Lexicon Engine's screen flickers now and then, a scan band rolls down it and a
    lamp breathes on the case. The Mana Conduit's slate grained and chipped, brass rivets at its corners, the
    font's light cast about it, sparks along the wet pipe. The Gilded Mint's coin with a passing gleam, its star
    turning, a gilt rim. Mana Shelter under a sky with drifting clouds, the earth banded, with stones, roots and
    deep crystals. Mana-Mine's sky with a sun and drifting clouds, grass along the top, tunnels with shadowed
    edges and dust where the miner digs. The Glimmer Maze's motes twinkle, the hedges flower and the slime
    leaves a faint trail. The Gloomwing Swarm's sky has nebulae, a crescent moon and rushing near stars, and a
    flash at the mast when it fires. The Hexmarch's cellar lit by two torches, a glow along the floor and a
    flash at the cannon's mouth.
  - v15.1, the Gilded Reels, Roulette, Blackjack and Jacks or Better:
    The Gilded Reels in a red-and-gilt cabinet with a neon marquee, chasing bulbs and a lever that swings;
    the reels blur as they spin, winning symbols pulse on a glowing payline, and the joker is drawn in
    place of a missing emoji. Roulette's wheel shaded, with frets, brass diamonds on the track, a ball with a
    shadow and a trail, and a marker set on the winning number. Blackjack's felt printed, the bet in chips
    on its circle and a banner for the outcome. Jacks or Better in a glass-and-brass cabinet with an LED
    line, the paytable lighting the hand as dealt and the held cards glowing. The floor's notices moved to
    the lower corner.

The Daily Challenge (the fortieth big update - v15.0)
  Each real day the Gilded Joker chalks up one challenge (src/js/64zp-daily.js; 76zg-daily.js), the same for every
  party that day: one of the ten scoring tables, picked by the date, with a bronze, a silver and a gold mark - the
  level to reach (or, at the pinball table, the score marks to pass), a little higher at the weekend. Any game of that
  table finished that day counts. Each mark pays once when collected: 150 gold; 400 gold and a common card; 900 gold
  and a stronger card. Days in a row with at least bronze make a streak - a tenth more gold for each day, up to double
  - and every seventh day of a streak brings a rare card. A mark not collected by midnight waits for the next day; the
  last fortnight is kept on the "Past days" page. Today's challenge heads the gallery, and the slim bar of that table
  shows how near it is.

The Joker's Club (the thirty-ninth big update - v14.9)
  Three things that tie the casino floor together (src/js/64zo-floorclub.js; 76zf-floorclub.js), reached from a strip
  under the gallery's head:
  - The Hall of Champions: a high-score board for each of the ten scoring tables (Runestack, Mana-Mine, the Glimmer
    Maze, the Gloomwing Swarm, the Hexmarch, Shatterpane, Starstone Drift, Moatleap, Runestep Pyramid, Wyrmhold
    Pinball) - the ten best games, how far each went, the day and who played; beating your own best is a record.
  - The loyalty card: a stamp for each different table played (a stake laid, or gold from a free table); eight fill a
    card, which pays gold and a Claudescryption card when collected, and full cards raise the membership - Bronze (1),
    Silver (3), Gold (6), Platinum (10) - and with it the reward.
  - Achievements: twenty-six, bronze (100 gold), silver (400 gold and a common card) and gold (1,500 gold and a rare
    card), from the first chip to every table, the jackpot, the claw, the boards, the arcade and Platinum
    membership - each paid once, when collected.
  Stamps, places on boards, records and achievements show for a moment in the corner as they happen.

The Gilded Joker's gallery (the thirty-eighth big update - v14.8)
  The casino floor opens on a gallery now (src/js/76ze-gallery.js) instead of a wall of buttons: a page of twelve
  cards, each with a little painted picture of its table, its name and a line on what it is; filters for cards and
  tables, arcade, puzzles, idle and builders, and prizes; pages turned with the arrows or the ← and → keys. Inside a
  table, a slim bar takes the place of the old rows - back to all the games, the tables either side, the table's name
  and the party's gold - so each table has more of the window.

Wyrmhold Pinball (the thirty-seventh big update - v14.7)
  A pinball table on the Gilded Joker's floor (src/js/64zn-pinball.js; 76zd-pinball.js), painted with the dungeon:
  a plunger lane, a curved top with a deflector, three rune bumpers, two slingshots, inlanes and outlanes (a kickback in
  the left one), the R U N E S drop targets that raise the bonus multiplier, three stars (all lit doubles the bumpers
  and relights the kickback), the Hoard Hole saucer, and the dragon at the top - slay it for a three-ball multiball,
  and every second dragon gives an extra ball. Ball save once per ball; three balls; a bonus times the multiplier at
  the end of each. Its own physics: a ball against segments, circles and two flippers, stepped 600 times a second.
  One stake a game: every score mark passed (3,000 up to 500,000) pays gold, more for each, every game; and a
  Claudescryption card the first time ever each mark is passed (common, a stronger common, rare).

The Wishing Claw (the thirty-sixth big update - v14.6)
  Three claw machines on the Gilded Joker's floor (src/js/64zm-claw.js; 76zc-claw.js) - the Copper Claw (25 gold a
  try), the Silver Claw (120, from floor 4) and the Gold Claw (400, from floor 10) - each with its own pit of prizes kept
  between visits: gold pouches and hoards, card capsules, mystery eggs, weapons, armour, shields and helms. Hold to
  slide the claw right, let go; hold to send it back, let go, and it drops (its shadow on the floor shows where). It
  grips the nearest prize, more surely over the middle and the lighter the prize, and may lose it on the way to the
  chute - though a slip over the chute still wins. Gold is paid out; a card capsule gives a Claudescryption card (common,
  a stronger common, or rare by the machine); gear is real gear for the party's pack, made for floor 3, 9 or 18 by the
  machine, the dearer ones more often enchanted.

Runestep Pyramid (the thirty-fifth big update - v14.5)
  A hopping game on the Gilded Joker's floor (src/js/64zl-runestep.js; 76zb-runestep.js): a pyramid of twenty-eight
  rune-cubes seen from the corner, and a glimmerkin hopping diagonally to light every cube's top - one hop each on
  levels 1-2, two from 3, and from 6 a hop on a finished cube turns it back. Ember-balls roll down; a violet egg hatches
  at the bottom into the Sigil Serpent, who hops after you; the Smudge (from 3) undoes cubes unless caught; a frost orb
  freezes them all. Wind-wisps off the sides carry you to the top, and a serpent close behind follows you off the edge.
  Three lives, one more at 8,000. One stake a play: each level cleared pays gold, more each level, every play; and a
  Claudescryption card the first time ever each third level is cleared (3 common, 6 and 9 a stronger common, rare from
  12).

Moatleap (the thirty-fourth big update - v14.4)
  A crossing game on the Gilded Joker's floor (src/js/64zk-moat.js; 76za-moat.js): a toad hops square by square across
  five lanes of market road - handcarts, hay wagons, galloping riders, ox-trains - to the verge, then across five
  lanes of castle moat on drifting logs and lily-turtles (from level 2 some dive) to the five lily-bays under the wall.
  Fill all five for the next level; thirty seconds a toad; a firefly in a bay for a bonus, from level 3 a pike lurking
  in one. Three lives, one more at 10,000. One stake a play: each level cleared pays gold, more each level, every play;
  and a Claudescryption card the first time ever each third level is cleared (3 common, 6 and 9 a stronger common, rare
  from 12).

Starstone Drift (the thirty-third big update - v14.3)
  A drifter on the Gilded Joker's floor (src/js/64zj-drift.js; 76z-drift.js): through a scrying glass a wand-ship
  floats in a void whose edges fold round. It turns, thrusts and drifts on, fires sparks (four at once) and blinks to
  a random spot. Struck starstones split - great into two middling, middling into two small, small ones gone - and
  wraith-lanterns cross now and then, firing back (a small one that aims, from wave 4). Each wave brings more and
  quicker stones. Three lives, one more every 10,000. One stake a play: each wave cleared pays gold, more each wave,
  every play; and a Claudescryption card the first time ever each third wave is cleared (3 common, 6 and 9 a stronger
  common, rare from 12).

Shatterpane (the thirty-second big update - v14.2)
  A breaker on the Gilded Joker's floor (src/js/64zi-pane.js; 76y-pane.js): a ruined chapel's stained-glass windows,
  a new design each level, broken pane by pane with a mana orb kept in play by a glass-slipper paddle (the mouse or
  the keys; where the orb strikes sets its angle). Tinted panes take two hits, the darkest three; lead frames from
  level 5 never break - though if nothing breaks for a while a guiding light bends the rising orb toward a pane, and
  later the lead crumbles. Charms fall from broken panes: a wider slipper, two more orbs, a slower orb, a sticky
  slipper, a life. Three lives. One stake a play: each level cleared pays gold, more each level, every play; and a
  Claudescryption card the first time ever each third level is cleared (3 common, 6 and 9 a stronger common, rare
  from 12).

The Hexmarch (the thirty-first big update - v14.1)
  A shooter in the Gilded Joker's cellar range (src/js/64zh-hexmarch.js; 76x-hexmarch.js): fifty-five hexlings in five
  ranks - Grubs, Wisps and Imps - march from side to side and step down at each wall, quicker as they thin, dropping
  hexes. A rune-cannon behind four warding stones fires one bolt at a time; both sides chip the stones away. A comet
  crosses the top for a mystery score. If the march reaches the floor the game is over. Each level starts lower and
  shoots back harder. Three lives, one more at 1,500. One stake a play: each level cleared pays gold, more each level,
  every play; and a Claudescryption card the first time ever each third level is cleared (3 common, 6 and 9 a stronger
  common, rare from 12).

The Gloomwing Swarm (the thirtieth big update - v14.0)
  A shooter on the Gilded Joker's roof (src/js/64zg-swarm.js; 76w-swarm.js): a lantern-skiff slides along the bottom
  of the night sky firing mana bolts (two in the air at once) while thirty-two Gloomwings swoop in on curving paths and
  settle into a breathing formation - Mites, Moths and four armoured Wardens that take two hits - then peel off to dive,
  dropping embers. A Warden that hovers low lowers a binding beam that carries the skiff off (a life); shoot that Warden
  out of formation to free it and fly two skiffs side by side. Every fourth stage is a Bonus Flight: forty fly past,
  100 each, 10,000 for all. Three lives, more at 20,000 and 70,000. One stake a play: each stage cleared pays gold,
  more each stage, every play; and a Claudescryption card the first time ever each of stages 2, 4, 6, 8, 10, 12, 15
  and 20 is cleared (common, a stronger common from 6, rare from 10).

The Glimmer Maze (the twenty-ninth big update - v13.9)
  A maze-chase on the Gilded Joker's floor (src/js/64zf-glimmer.js; 76v-glimmer.js): a glimmerslime eats its way round
  a hedge maze of glimmer motes while four Lantern Haunts hunt it, each its own way - Ember straight at it, Bramble at
  where it is going, Frost from the far side of Ember, Moth close and then shy - drifting off to their corners now and
  then. The four Hex Runes turn them pale and slow: eat them for 200, 400, 800 and 1600 and they go home as a pair of
  eyes. Tunnels wrap at the sides; a lucky chip shows twice a level. Three lives, one more at 10,000; each level the
  haunts are quicker and the runes shorter. One stake a play: each level cleared pays gold, more each level, every
  play; and a card the first time each level is ever cleared (common to 4, a stronger common to 9, rare from 10).

Mana-Mine (the twenty-eighth big update - v13.8)
  An arcade game under the Gilded Joker (src/js/64ze-manamine.js; 76u-manamine.js): a miner with a lamp-helmet digs
  down through four bands of earth. Mudlings wait in their hollows and drift through the earth as a pair of eyes when
  they cannot reach her; Ember Newts draw a breath and spit fire along their row. Her mana-tether latches onto a
  creature along the tunnel and each pump swells it until it bursts (left alone it shrinks back). Boulders wobble and
  fall when the earth under them is dug away, crushing what is below; two down and a mana crystal shows for a while.
  Clear every creature for the next level - more of them, quicker. Three lives, one stake a play: each level cleared
  pays gold back, more each level, every play; and a card the first time each level is ever cleared (common to 4, a
  stronger common to 9, rare from 10). Arrows or W A S D, Space to shoot and pump, P to pause.

The Gilded Mint and Mana Shelter (the twenty-seventh big update - v13.7)
  Two free games on the Gilded Joker's floor that go on in real time, even while you are away:
  - The Gilded Mint (src/js/64zc-mint.js; 76s-mint.js), an idle game: strike the great coin press for gold dust; buy
    apprentices, bellows, coin presses, alchemists, kilns, golems, star-forges and a dragon's hoard to mint it for you
    (a seventh dearer each), double each kind at 10, 25, 50 and 100 owned, buy better hammers; catch the lucky coin when
    it glints (seven times everything for half a minute, or a lump); melt the mint down at a million for Gilded Seals,
    a twentieth more for good. Away it mints at half pace for up to eight hours. Gold and a Claudescryption card the first
    time the dust minted in all passes a hundred, a thousand ... a trillion (common, then stronger, then rare).
  - Mana Shelter (64zd-shelter.js; 76t-shelter.js): a warren dug under the Joker, in cross-section - a stair down one
    side and rooms on each floor: Mana Wells (whose mana runs the rest), Kitchens, Springs, Living Quarters (two who
    share them raise a child), Storerooms, Beacons that draw wanderers, Training Halls. Residents have Might, Grace and
    Wit, and work faster at the rooms that want them; a room's work waits in a bubble to be gathered, which fills the
    stores and pays marks to build, dig and improve with. Everyone eats and drinks; with bread or water gone work goes
    at half pace. Away it runs on for up to four hours. Gold and a card the first time the warren houses 6, 10, 15, 20,
    25, 30, 40 and 50.

The Lexicon Engine and the Mana Conduit (the twenty-sixth big update - v13.6)
  Two free games of skill on the Gilded Joker's floor, ten levels each; each level pays gold and a Claudescryption card
  the first time it is done (common to level four, a stronger common to nine, rare at ten), and never again:
  - The Lexicon Engine (src/js/64za-lexicon.js; 76q-lexicon.js): an artificer's terminal with a green glass screen -
    glow, scanlines, a rolling band, flicker, the header typed out. Its memory is rows of symbols with words hidden in
    them; choose one and the engine answers its likeness to the password (letters in the same places). Four tries
    (three from level seven); a pair of brackets with only symbols between them takes out a dud or gives the tries
    back. The words grow from five letters to ten, and from eight to twenty of them.
  - The Mana Conduit (64zb-conduit.js; 76r-conduit.js): a slate with a font of mana and a rack of brass conduit -
    straights, bends and crossings - laid by clicking before the font opens (a dry piece can be swapped); then the mana
    runs, glowing, through each piece and must pass as many as the level asks before it spills from an open end. A
    crossing run both ways counts twice; from level six a drain to finish in pays a fifth more. Each level gives less
    time, faster mana, a longer run and more rubble.

Runestack, the Gilded Cascade, and the Hexed Wand's new shots (the twenty-fifth big update - v13.5)
  - Runestack (src/js/64y-runestack.js; the window 76o-runestack.js): rune-stones of seven shapes sink through a glass
    case of black water; move, turn (the stones kick off the walls), sink and drop them so rows fill - a full row
    flashes and bursts into chips - with a ghost where the stone will land and the next three shown. Ten rows a level,
    faster each level. One stake a play: every level cleared pays gold back, more for each (a fifth of the stake and a
    tenth more each level: level three cleared and the stake is back), every play; and a Claudescryption card for each
    level the first time it is ever cleared - a common card for levels one to four, a stronger common for five to
    nine, a rare one from ten on. Arrows or W A S D, Up/X/Z to turn, Space to drop, P to pause.
  - The Gilded Cascade (64z-cascade.js; 76p-cascade.js): a coin pusher in a glass-and-brass cabinet with chasing
    lamps. Buy a cup of twenty coins (1, 5 or 25 gold each), click over the shelf to drop one where you choose (hold to
    keep dropping); the brass pusher shoves the bed, and what goes over the front edge tumbles into your tray at its
    worth - what slips into the side gutters is the house's. Now and then a prize comes down with a coin: a gold nugget
    (ten coins), a Claudescryption card token, or a sealed item token (a real piece of gear by the party's depth). The
    shelf is kept between visits; the cup can be cashed in. About nine in ten comes back over the edge, more with the
    prizes and a good eye for where to drop.
  - The Hexed Wand looks the part now: the wand rises from the table into the shooter's hand and comes closer to its
    mark - across to the dealer, or turned back toward the player - its tip gathering light; a live hex is a blast (a
    white flash, a forked red bolt, rings and sparks, the table shaking), a dud a fizzle (the tip sputters, a few sparks
    drop, a curl of grey smoke, "fzzt..."), each with its own sounds.

The Hexed Wand and the Gilded Pit (the twenty-fourth big update - v13.4)
  Two more of the Gilded Joker's games (src/js/64w-hexwand.js and 64x-gildedpit.js; the windows 76m-hexwand.js and
  76n-gildedpit.js):
  - The Hexed Wand: a duel across a round table with the house's hooded dealer. A wand of black wood is loaded with
    live hexes and duds - the counts shown, then turned face down. On your turn point it at the dealer or at yourself:
    a live hex cracks across in red and snuffs one of the target's candles; a dud only puffs - and if you aimed it at
    yourself, the turn stays yours. Charms are dealt with each loading: a seeing-glass (the next charge), an unloading
    (throw the next one out), a whetstone (the next hex snuffs two), tallow (a candle lit again) and a binding cord
    (the other side loses a turn). The dealer plays fair - only the counts and its own glass. Three rounds, of two,
    four and five candles; the stake climbs a ladder (1.75, 3.6 and 8.8 times) - collect between rounds, or play on and
    risk the pot - with a common Claudescryption card for the second round and a rare one for the third. Set from
    thousands of measured duels so a careful player comes out about even.
  - The Gilded Pit: one hero of the party goes down a stair behind the bar into a locked room under the Joker, drawn
    in 3D - green papered walls, a bare bulb flickering on its cord, the Old Lucky (a five-reel slot machine) on the far
    wall with its lever, the house's deposit box and a chalk board of what is owed on the left, a black telephone on
    the right, the door behind, and a trapdoor under the stool. Drag to look about; click the lever, the box, the
    telephone, the door. The stake goes down as coins; five deadlines, each a debt to pay into the box within seven
    spins. The reels pay for rows of three, four and five, columns, diagonals and ten times a full grid; three of the
    Pit's eyes spoil a spin. Pay early for more tickets, and the telephone rings with lucky charms to buy (a horseshoe,
    a four-leaf clover, a pocket watch, a lodestone, a hand mirror, a piggy bank...); then step out with the coins, or
    stay for a bigger debt. Miss a deadline and the floor drops away: the hero comes back up to the party with a tenth
    of their health, and the coins stay below. Eight more charms unlock for good as deeper deadlines are reached;
    Claudescryption cards at the third and fifth deadlines and for a full grid. Measured, it returns about what is put
    in, at a deeper risk the longer one stays.

The Tilewright's Table (the twenty-third big update - v13.3)
  Tile-matching solitaire on the Gilded Joker's floor (src/js/64v-mahjong.js; the window 76l-mahjong.js), with
  ivory tiles of the game's own: three suits of nine - Coins, Runes and Blades - the four winds of the compass, the
  three elements (Fire, Frost, Holy), four potions and the four seasons, a hundred and forty-four in all, stacked in
  the Keep or the Tower. Take away pairs of matching free tiles (any potion with any potion, any season with any
  season) - a tile is free when nothing lies on it and its left or right side is open; the free tiles show bright, a
  picked one lifts in gold, a taken pair flies together and is gone in a glint. Every deal is built backwards from a
  way to clear it, so every table can be cleared; a hint shows an open pair, and three shuffles deal the tiles left
  again (still clearable) when no pair is open. One stake a table: cleared without a shuffle it pays 1.6 times the
  stake (the Tower, an easier stack, 1.4) and a rare Claudescryption card; with one shuffle 0.9 (0.8) and a common
  card; with two 0.5; with three 0.3; a table given up or stuck pays back a little by how much was cleared. Measured,
  a player who takes open pairs at random comes out about even, and a careful one ahead. A table left mid-way waits.

The Gemcutter's Tray (the twenty-second big update - v13.2)
  A third game of skill on the Gilded Joker's floor (src/js/64u-gemtray.js; the window 76k-gemtray.js): an eight by
  eight tray of cut stones under a jeweller's lamp - rubies, sapphires, sunstones and diamonds (the game's own gems),
  with jade, amethyst and pearl. Swap two neighbours to make a line of three or more of a kind: they flash and burst
  into sparks, the stones above fall into place and new ones drop in, and whatever lines up as they settle goes too,
  the cascade called out as it climbs (each step rings a little higher). Four in a line, or an L or a T, leaves a
  rune-stone ringed in gold that bursts its square of nine when it goes; five in a line leaves a star-stone that,
  swapped with any stone, takes every one of that kind. A tray with no move left is shaken up; a hint is a click away.
  Five trays a run for one stake, each with a mark to reach in its moves (2,000 in 22 up to 6,200 in 26); each tray
  done pays 0.6, 0.8, 1.0, 1.4 and 2.4 of the stake, with a common Claudescryption card from trays 2 and 4 and a rare
  one from 5; a tray left short pays back a little for the score made. Measured with a greedy hand, the trays are
  done 98%, 78%, 60%, 35% and 15% of the time.

The Gilded Joker's arcade (the twenty-first big update - v13.1)
  Two games of skill join the floor (src/js/64t-casinoarcade.js; the window 76j-casinoarcade.js):
  - Runefall: a slate board of rune-stones under a wizard's staff. Aim with the mouse (a guide shows the first of the
    path) and loose an orb; it falls and bounces, ringing higher with every rune it strikes, and the lit runes crumble
    to dust when it is gone. Break every ember rune (orange) before ten orbs are spent; a mana rune (green) makes the
    next orb a fireball that burns straight through; the purple rune pays a bonus; the Well sliding along the bottom
    gives a caught orb back. Five boards in a run, by the dungeon's bands - the Cellar, the Goblin Warrens, the
    Drowned Halls, the Foundry, the Lich's Throne - for one stake: each board cleared pays 0.6, 0.8, 1.0, 1.4 and 2.4
    of it (6.2 for a whole run), with a common Claudescryption card from boards 2 and 4 and a rare one from 5; a lost
    board pays back a little for the ember runes broken.
  - Lantern Lane Dash: a cabinet of the old sort - a pixel lane under scanlines, a lit marquee and red readouts. Hop
    the hero (arrow keys, W A S D or the pad) across grass with lamp-posts in the way, roads of carts, rivers of
    floating logs and the mine-cart rail (its bell rings before the train), to the gate at the top; dawdle and the
    Night Watch's crow comes. Each level cleared raises the pot up a ladder - 1.2, 1.7, 2.6, 4 and 6.5 times the stake
    - and you collect it or press on and risk it; a common card at level 3 and a rare one at level 5.
  Measured with bots, a careful player comes out about even on both and a good one ahead.

The Gilded Joker's floor (the twentieth big update - v13.0)
  The Gilded Joker now has a floor beside its Claudeatro table: a row of tables across the top of its dialog, four
  of a casino's own games played for the party's gold, at fair odds - the house keeps a little and no more, and the
  tests check each game's return (src/js/64s-casinogames.js; the window 76i-casinofloor.js):
  - The Gilded Reels: three reels and one line, 97.1% back; three Jokers pay a thousand times the bet and a rare
    Claudescryption card. The reels spin and stop one by one with a ticking and a clunk, coins fall for a win and the
    machine flashes for a jackpot.
  - Roulette: a single zero and the usual payouts (35 to 1 down to even money), 97.3% back; chips are laid on a board
    and the walnut wheel turns against its ball, which clicks over the pockets and drops; a straight bet of five or
    more that wins on the zero brings a common card besides.
  - Blackjack: six decks in a shoe, a natural pays 3 to 2, the dealer peeks and stands on soft 17, double any two,
    split a pair once - about 99.5% back with good play; the cards slide out of the shoe and the hole card turns. A
    natural of the Ace and Jack of Spades - the black jack - brings a common card.
  - Jacks or Better: the full 9/6 pay table, 99.5% back with good play; hold what you like and draw once; a royal
    flush pays 800 times the bet and a rare card.
  Chips of 1, 5, 25, 100 and 500 gold make the bet (500 a hand, 2,000 on a roulette spin); a hand left on the table
  waits for you; each table keeps what you have wagered and what it has paid back, and the cards go to Leshy's box.

Claudecraft phase 8, v12.8: measured, tuned and told - the island plan complete
  tools/craftbot.js sends a simple hand through the gate for an hour of the island in real time (a staircase down, a
  tunnel along, every ore and gem beside it, fighting what comes, a potion when hurt) and sets it beside an hour in the
  shaft (the balance simulator's run, at 1800 steps an hour, one hero's share). Tuned from it: monster levels now
  follow the hero's (a little under up top, level in the caves, two over in the deep, a night counted for every two,
  inside each band's bounds), a hero mends while calm (as in the Mage Tower), Kobolds and Goblins drop a little more,
  island shots strike harder, and bundles are capped at twelve. As measured over three seeds: a fighter's hour pays
  about what the shaft's does in experience at level 5 (530-870 against 530) and two thirds of it at level 12
  (1320-1600 against 2270), with less coin and more ore; a caster fares worse with the simple hand (400-880),
  as in the Fortress against the Tower. The island makes in about a third of a second and keeps its save small
  (edits only). The nineteenth big update (UPGRADE_PLAN_13.md) is complete.

Claudecraft phase 7, v12.7: the vault under the island, and errands
  Under the island's highest hill (the map of four scraps marks it) lies a sealed vault of rune-cut stone, reached
  only by digging down; its stone wants a pick that would take silver, and breaks into rune-cut stone. Three rooms in a
  row: spikes underfoot, two lairs, and the hall of its guardian - the Hollow Mason, a golem of the island's own
  blocks that wakes when a hero enters its hall and tears stones from the walls to mend itself. Its fall leaves a
  relic, the Mason's Plumb (an amulet), and a title. Four new errands in town want the island's things: the Smith
  six iron (a bar counts two), the tavern's cook three cuts of deer or boar, the Library a piece of the vault's
  rune-cut stone, the Guildhall's builders 128 island stone in the satchels. Three achievements: the first star-iron,
  the Mason's fall, a homestead.

Claudecraft phase 6, v12.6: a home on the island
  A bedroll (leaves and poles, at a workbench) laid in a room the hero has walled all round and roofed over - a door,
  two high, opened and shut with the right button, counts as wall when shut - makes a camp. Sleeping there at night
  (the right button on the bedroll) passes the night to the dawn and mends the hero fully, and from then on a fatal
  fall wakes them on that bedroll rather than by the gate. A camp with a chest, a workbench and a kiln within reach of
  the bed is a homestead: word of it reaches Caer Duin (+40 renown, once), and its chest can be opened from the
  island's gate (the right button on the gate's stone). Signposts (planks and a pole) are named when placed and show
  on the compass. All of it helps; none of it is needed.

Claudecraft phase 5, v12.5: finds and places to go
  The island now hides things, the seed's: gems on the deep caverns' walls - the main game's own rubies, sapphires,
  sunstones and the odd diamond, which want a pick that would take silver; four old chests sunk in the sea and a few
  ruins on the hills, each with an old chest (a right click opens it: gold and a thing by its depth, and a scrap of
  map); and three lairs in the deepest caverns that send out the deep's monsters while the hero is near, until they are
  broken - and then leave an old chest of their own. Four scraps make a map, and a compass above the hotbar marks the
  place under the island's highest hill where the vault lies (the gate is always on it). At the Smith, three like gems
  are set in a ring or an amulet.

Claudecraft phase 4, v12.4: the way home, and what comes with it
  Out through the gate, what has a meaning at home comes home as the main game's own: ore chunks, bars and charcoal
  into the bag (for the Smith), deer and boar meat (for the cook), the island's gold into the purse and its finds into
  the bag. What is the island's stays in the satchel for the next visit: blocks, the island's tools, torches. Building
  stuff has a use at home too: the merchant buys island timber and stone at a gold the stack of sixteen (a button at
  any shop), and the Guildhall's builders take blocks a hundred at a time for ten renown off the village's next build
  (the village builds with renown). Into the island the bag goes with the hero: picks and lantern work there, Q drinks
  a healing potion (the smallest that will do; a mana potion for a caster who is not hurt), G eats a ration or a bit
  of the island's meat for a little mending.

Claudecraft phase 3, v12.3: day, night, and the island's creatures
  The island keeps the game's own clock while a hero is there, a minute a second: day, a gold dusk, night (dark but
  for a little moonlight), dawn; the sun and moon cross the sky. A torch's light is not dimmed by the night. By day deer
  and boar graze the grass (meat for the cook; a boar struck turns on you). In the dark - at night up top, at any hour
  in the caves, and never by a torch or in the hero's own light - the game's own monsters come, in their own pictures:
  Giant Rats and Kobolds up top, Skeletons and Goblins in the caves, Wraiths and Gargoyles in the deep, their level by
  the depth and the nights counted. Fight in real time: the left button strikes what is in reach (the hero's weapon by
  the main game's sums, an island sword adding), F shoots with a bow or a caster's bolt. Every kill pays a third of its
  experience at once; Kobolds and Goblins drop gold; now and then a thing. A fall leaves the gold and finds in the
  bundle with the satchel; out through the gate they come home, with the meat.

Claudecraft phase 2, v12.2: crafting
  Crafting, from the satchel's window (I): by hand, at a workbench or at a kiln within reach (a right click on one opens
  it). Planks and poles from wood; a workbench; torches (a pole and charcoal) that light the dark round them; at the
  workbench a kiln, chests, ladders, and the island's own tools - stone, copper and iron picks, axes and swords, which
  speed breaking by tier (an island pick also mines ore of its grade), wear with use and stay on the island; at the
  kiln glass, bricks, and bars from three chunks and a charcoal - the Smith's own sum - which go home lighter than ore.
  A chest keeps what is put in it safe on the island, through any fall; ladders are climbed with Space or forward.

Claudecraft phase 1, v12.1: ore, caves, and the pick from home
  Under the island's hills now wind caves, with a few large caverns deep down (never under the sea, now and then
  opening on a hillside). Underground it is dark but for the light the party carries: a little of the hero's own, more
  with a torch, most with a lantern. In the stone are veins of ore by depth - copper high, iron below, silver deeper,
  gold deep, star-iron in seams just over the bedrock - and charstone near the top. Ore breaks only with a pick from
  the bag that mines it (CM.PICKS: a copper pick takes copper and iron, an iron pick silver too, steel all of them), a
  point of wear a block; a better pick breaks stone and ore faster. Ore drops the main game's own ore chunks (two from
  star-iron) and charstone drops charcoal, both heavy: past twice what the hero can carry, they slow down. Out through
  the gate the chunks and charcoal go into the party's bag, ready for the Smith's smelter (three chunks and a charcoal
  make a bar).

Claudecraft made a place (the nineteenth big update, UPGRADE_PLAN_13.md) - phase 0, v12.0: one hero and a satchel
  The Neather Gate now asks who steps through: one hero goes, the rest wait in the Keep-yard. On the island the HUD
  shows their portrait, health, magic and the game's clock. Breaking a block takes time - hold the left button and a
  crack grows over it (leaves fast, dirt quick, wood slower, stone slow by hand and quicker with a pick from the bag);
  the block goes into the hero's own satchel (27 slots, stacks of 64; grass gives dirt, stone gives cobblestone), and
  the right button places from the hotbar, which is the satchel's first row (I opens the satchel to move stacks).
  No more flying, and a fall of more than four blocks hurts; a fall that would kill wakes the hero by the island's gate
  with a tenth of their health, and what they carried is left in a glowing gold bundle where they fell, kept until they
  walk into it. Each hero's satchel, place and bundles are kept with the village.

The Neather Gate: Claudecraft (the eighteenth big update - v11.9), a tech demo for now
  On the Keep-yard's east side stands a gate of dark basalt blocks, violet runes cut into them, a slow violet shimmer
  inside. The whole party steps through onto the Timeline's Claudecraft island (src/js/64n-claudecraft.js, with its own
  WebGL in src/js/76h-claudecraft.js): 160 by 160 blocks and 64 high, hills, beaches, a sea, snow on the peaks and
  trees, drawn a chunk at a time with fog and an outline round the block under the eye. Walk, look, jump, swim, fly
  (Space twice), break blocks and trees with the left button, place blocks from the hotbar with the right (1-9 or the
  wheel). Bedrock and the gate's stone do not break. Every change is kept with the village (src/js/61k-gate.js), and
  the same gate stands on the island near the spawn: walk into its light to come home.

The pipe in the Square: Super Claude Bros (the seventeenth big update - v11.7), for fun
  A great bronze pipe, green with age, stands up out of the cobbles at the Square's east corner. Any one of the party
  climbs in and comes out in a side-on world of four levels (src/js/64m-claudebros.js; the window's side
  src/js/76g-claudebros.js): 1-1 the Meadow Road, 1-2 Under the Hill, 1-3 the Treetops, and 1-4 the Brass Keep, where
  the Brass Warden charges and leaps. Run and jump to the banner pole at the end of each. Land on foes, or use what you
  carry - a blade for the fighters, bolts for the casters, arrows for a bow. Coins in the air and in crates knocked
  from below are gold (two each), every foe is experience, and a few draughts mend; there is no gear to find. A fall
  (or a pit, or the lava) brings the hero back up the pipe with a tenth of their health, but the coins and the
  experience come too (src/js/61j-pipe.js). A D or the arrows run (Shift faster), Space, W or Up jump (held: higher),
  J, F or the mouse uses the weapon. The levels, foes and pictures are this game's own.

The red portal: Claudeablo (the sixteenth big update - v11.6)
  A red portal on the Keep-yard's north side leads to Haven, a village of thatch and timber under a dark cathedral:
  the Timeline's Claudeablo, ported whole (src/js/64l-claudeablo.js; the window's side src/js/76f-claudeablo.js) and
  drawn at an angle as it is there. Any one of the party steps through, as a warrior, rogue or sorcerer by their
  calling, as strong as they are here the first time; that character is kept with the village, one for each hero.
  Haven has its smith, witch, healer and elder, a waystone, and the way down: fifty levels from the Cathedral through
  the Catacombs, the Caves, Hell and the Abyss to Vorthak the Undying in the Undying Sanctum, with loot white, blue and
  gold, shrines, chests, barrels, bosses every ten levels and champions between. Left-click to walk, fight, take and
  talk (hold to keep walking), right-click casts, Shift-click attacks on the spot, 1-4 the belt, I inventory,
  C character, S spells, Tab map, Alt the names of things on the floor, HOME walks to the portal. Haven's own red
  portal, south of the well, brings the hero home with a share of the experience, the gold found, and every piece of
  gear in the pack as a thing of the party's own (what is worn, and the potions, scrolls and books, stay there for
  next time). A death there wakes the hero in Haven with half the gold, as Claudeablo does. (The original game's
  characters borrowed from another game's names have names of their own here: Vorthak the Undying, the Flesher,
  Brannoc, Isolde, Tobin and Aldous.)

The Gilded Joker (the fifteenth big update - v11.5)
  East of Temple Row, up Gilded Row from Shaft Lane, stands the richest house in Caer Duin: red plaster between gilt
  pilasters, tall arched windows lit gold, gilded doors under a fanlight, a copper roof, a sign of three cards. Inside,
  the Timeline's Claudeatro, its rules ported whole (src/js/64k-claudeatro.js; the table src/js/76e-casino.js): poker
  hands scored as chips times mult, Jokers, Tarot and Planet cards, enhancements and editions, the blinds and their
  bosses, tags, vouchers, packs and the shop, eight decks, and endless play past Ante 8. Wager 0 to 500 gold at the
  table: every blind beaten pays back 40%, 60% or 100% of it (small, big, boss), a quarter more for each ante, and
  beating Ante 8 pays five wagers more. Play for nothing and nothing is paid, but the house's book still fills: 25
  Jokers to start and one more for every blind ever beaten, and the decks by milestones (a boss beaten, Ante 3, Ante 4,
  six bosses, a Straight Flush, Ante 6, a won run). The book and any game left on the table are kept with the village.
  Every step of a hand's score is shown on its card or Joker as the chips and the mult count up, each with its sound.

  The cards in motion (v11.8): a deck pile and a discard pile either side of the hand. Cards are dealt from the deck,
  turning over as they fly into the hand; discarded cards spin away onto the discard pile and the new ones are dealt
  in their place; played cards travel from the hand up to the table, and the ones that do not score sink back; a
  sort slides every card to its new place; a card a Tarot changes turns edge-on in a flash of gold and back; a new
  Joker springs into its row. The cards themselves are finer: pips for the numbers, a crowned court for J, Q and K,
  a great suit for the ace, a stone for Stone Cards, a label for each enhancement, and each enhancement its own life -
  Bonus and Mult cards glow, Glass and Gold catch the light, Steel is brushed, Wild cards shift colour, Lucky ones
  twinkle - over the editions' foil, holographic and polychrome.

The Fortress (the fourteenth big update - v11.4)
  UPGRADE_PLAN_12.md says what it does. North of Leshy's clearing stands a black keep with four corner towers and two
  great arched doors of dark wood bound in iron; a third portal in the portal yard goes there, and one by the doors
  comes back. One fighter goes in (Knight, Paladin, Rogue, Monk, or a Ranger with a blade) and the game becomes a
  gauntlet seen from above, in real time (src/js/64j-fortress.js; the window's side src/js/76d-fortress.js): twenty
  floors of maze, keys that open whole doors across the way, treasure closets behind doors of their own, lairs that
  keep sending their monsters until they are broken, draughts, gold, fire flasks and chests, and the stairs down
  somewhere far off. A Warden guards the stairs on floors 5, 10 and 15; the Iron Marshal holds the way out of the
  twentieth (he charges, slams the floor, and calls help when hurt). W A S D move, Space, J or the mouse strikes (the
  mouse aims), Q throws a flask, E at the stairs goes down and L comes out with everything carried. Out mid-floor, that
  floor's finds are lost; a death loses everything carried and leaves the fighter a tenth of their health; experience
  is always kept, and the next time in is the floor after the last one counted (src/js/61h-fortress.js).
  tools/fortbot.js measures it: a careless Knight gets 2 to 4 floors at level 1, 7 to 9 at level 10, 13 to 17 at 20.

Claudeita's cave (the thirteenth big update - v11.3)
  UPGRADE_PLAN_11.md says what it does. South of the fields, up a path from them, a crag of grey rock has a low dark
  mouth with a forge-glow far down in it; the second plinth in the portal yard by the shaft is lit for it, and a portal
  by the crag goes back. One caster goes in alone (Mage, Necromancer, Druid, Cleric, Bard or Artificer) and the game
  becomes the Timeline's Claudeita, ported whole (src/js/64i-claudeita.js; the window's side src/js/76c-cave.js): a
  side-on world of falling sand, flowing water, lava and acid, and fire, made a few rows at a time as you descend; five
  biomes (the Mines, the Frozen Depths, the Fungal Caverns, the Magma Vault, the Hollow Heart), each ending in a boss's
  arena - Gravelmaw, Rimecaller, Mother Spore, the Cinder Colossus, the Unmaker - and, under the first four, a sanctuary
  with a fountain and a shop. Wands are rows of spells cast in order (projectiles, modifiers, multicasts); the
  Apprentice's Wand and the Miner's Rod are given at the mouth, more are found deeper, and Tab is the wand editor.
  A D move, W or Space jump (held: levitate), the mouse aims and casts, 1-4 or the wheel change wands, E takes or buys.
  The hero's health in the cave follows theirs; their level and wisdom or intellect add to the spells' damage.
  Dying puts the hero back with the party at the mouth with a tenth of their health, and the run's gold, things and
  wands are lost. Undoing the Unmaker - or climbing a sanctuary's rope back to the daylight, which is the Wood's own
  addition - keeps them all: the gold, a thing of the party's own from every boss, and the wands and spells, which go
  to the rack at the mouth (up to two of them may be taken in on a later run, and come back whatever happens).
  Experience is always kept. Turning back from the actions panel keeps only the experience. The Unmaker's fall is an
  achievement. Sounds made in code for the wands' bolts, blasts, digging and splashes.

Leshy's cabin: Claudescryption in the Wood (v11.1)
  In a clearing between the river and the fields, up a path from the road, stands a log cabin with smoke from its
  chimney and a candle in its window; the second portal in the portal yard by the shaft goes there, and one by its door
  comes back. Inside, Leshy deals Claudescryption - the Timeline's own card game, its rules ported whole into
  src/js/64h-cards.js: four lanes, blood paid by sacrificing your creatures, bones from your dead, the bell, the scale
  tipped five teeth to win. Seven games at his table, each opened by winning the one before: the Woodlands, the
  Wetlands and the Snow Line, then Leshy in the Prospector's, the Angler's and the Trapper's masks, then Leshy himself
  and the Moon. A win pays gold (doubled the first time), a card of three to choose, and against a mask a thing besides;
  a loss costs nothing. Your collection and your deck are kept between runs (src/js/61f-cabin.js): a starter deck of
  six, changed between games at the table (four to twenty cards; squirrels are always to hand). Cards turn up in about
  one chest in twenty-two, on a champion one time in four and a tower boss one in three; every guardian, the Lich King
  and the tower's tenth floors give a rare one. Beating Leshy and the Moon is an achievement.

  The table moves (v11.2): Leshy's eyes glint between two flickering candles, and the board shows what happens.
  A card drawn slides in from the pile, a card laid is dealt into its lane from your hand, Leshy's cards drop onto
  his row and his waiting cards flip up behind it, a card moving from the back row slides forward, and the dead
  redden and fall away. When the bell rings each step comes a beat apart: the attacker lunges at the lane it
  strikes, the creature struck shakes and its damage rises off it in red, a blow to a player rises off the scale,
  and the scale's beam tips toward whoever is winning. Banners say whose turn it is and when a mask plays a trick.
  Each has its sound, made in code: cards drawn and laid, a sacrifice's knife and its bones, the blows, a death,
  the bell, the scale, a win and a loss. Reduced motion shortens the beats and the movements.

The Mage Tower (the twelfth big update - v10.1 to v11.0)
  UPGRADE_PLAN_10.md says what each phase does.
  The portal yard and the tower (v10.1): in the Keep-yard by the shaft, a portal yard - a lit portal to the Mage Tower,
  and two dark plinths waiting for challenges to come. The tower stands in a clearing north of the fields: black and
  grey stone, seven stories, narrow violet windows, a slate cone, and two great dark doors, with dark shrubs and fog
  about its foot (src/js/61d-magetower.js). A portal by its door goes home. At the doors the party chooses who goes in
  alone: a caster (Mage, Necromancer, Druid, Cleric, Bard, Artificer) or anyone with a bow or a crossbow.

  The tower's floors (v10.2): forty floors made from the run's seed (src/js/61e-towerfloor.js) - large rooms and halls
  two and three wide, the start in one corner and the ladder up in the farthest room, where the floor's boss waits;
  the fortieth is the King's hall, open, with pillars to hide behind. Dark stone and violet torchlight.

  Inside, in real time (v10.3): the hero walks the tower's floors freely (src/js/64e-towerrun.js) - W A S D or the arrows,
  Q to turn, the mouse after a click into the view; click, Space or F shoots the calling's bolt (an archer's arrow,
  forty to start, quivers on the floors); right-click, R or 2 casts its great spell (Fireball, Smite, Drain, Thorns,
  Lullaby, Firework, or the archer's Volley) for magic that comes back slowly. Draughts on the floors mend. The HUD has
  a crosshair, the hero's bars and the floor's name; "Leave the tower" gives up the floor, and what was won is kept.

  Monsters and bosses (v10.4): the tower's monsters stand until they see the hero or hear a shot, then hunt by the
  shortest way and strike when close; some shoot from a distance (src/js/64f-towerfoes.js). Each floor's ladder is
  guarded by its boss - one of the floor's kinds, larger, glowing, with a champion's word and far more health - which
  waits in its room. Its fall frees the ladder and leaves something good.

  The ladder, out and back (v10.5): when the boss falls, E at the ladder climbs to the next floor and L goes out of the
  doors with the floor counted; each floor's experience, gold and things go to the party as it is cleared. Out of the
  tower the party can go home by the portal, sell, rest, and come back: the doors take the hero to the floor after the
  last one cleared. A fall puts the hero outside at one health, and the floor is lost.

  The King of the Tower (v10.6): on the fortieth floor, in a hall of pillars, the King keeps his distance and casts -
  bolts, a ring of fire that grows out from him (a pillar between you and it is safety), two of the tower's monsters
  summoned at his side, a curse that slows - and every 1 to 15 seconds he is somewhere else in the hall, never close
  (src/js/64g-towerking.js). At half his health he speaks and casts faster. His fall leaves the King's Circlet and a
  title, and the dais takes the hero out.

  Around the tower (v11.0): tools/towerbot.js climbs it and measures how far heroes get (a Mage starting at level 20
  clears about sixteen floors in a row, at level 40 about thirty-three); the tower's numbers are set from it. Close
  fighters rush the last stretch, a hero out of the fight a few seconds gets breath back, and the tower's experience is
  a third of a fight's (one hero takes every kill). LORE.md says who the King was.

A world that moves (the eleventh big update - v9.3 to v10.0)
  UPGRADE_PLAN_9.md says what each phase does.
  Monsters that move (v9.3): a monster's pose is worked out from what happened to it and when (CM.motion in
  src/js/28-motion.js): it breathes in its own time, lunges a quarter of a square at the party when it strikes,
  flinches back white when struck (a blow mid-lunge breaks the lunge off), topples away from the pack and fades when it
  dies (a ghost rises away), runs and shrinks down the corridor when it flees; a guardian rises from the floor into its
  title, and the Lich King's robe stirs. Pictures face the party from either side. Under reduced motion only the flash
  and the fade are left.

  The living dungeon (v9.4): three packs in five sleep, most of them in a dead end near where the seed put them
  (CM.makeLairs in src/js/61b-lairs.js; the floors themselves never move). A sleeper lies on its side and does not
  wander. The party's light wakes it if it lies on the same row or column within the light's reach (a torch eight
  squares, a lantern ten, a glow stone five, a conjured light eight) with nothing shut between; the party's noise may
  wake it each turn if it lies within the noise's reach (squares of open floor; a shut door costs four). A step makes
  two, heavy armour two more, walking by itself one more; a door or a chest four, a fight nine, a spell four, mining
  eight. A woken pack hunts the party from anywhere on the floor. T shades the light below ground (the Douse button):
  no light to be seen by, half the noise, two squares of sight, and the torch does not burn down; a Rogue, Ranger or
  Monk in front halves the noise again. Walk into a sleeping pack and the party has a free round in which every blow
  lands. Champions lead a quarter of the packs from floor six, each with a word: Warded (its ward drinks the first
  spell), Frenzied (twice a round under half), Shrieking (its cry wakes every lair on the floor), Shadowed (unseen
  until it strikes; a Rogue sees it), Stonehide (the first blow a round glances off), Vampiric (its blows feed it),
  Hoarder (carries a chest's worth), Fleet (twice a round). A champion is tougher, worth twice the experience, and
  drops a thing of its own; five in a run is an achievement. Automatic shades the light near a sleeper when a quiet
  one leads, and lights it again past it.

  Things that move (v9.5): a door swings open on its hinge, away from whoever opened it; a portcullis lifts into its
  lintel; a lever is thrown (CM.swing in src/js/28-motion.js). A chest the party empties stays standing open where it
  was. Water - the river, the ford, the Flooded Vaults' pools - ripples, shows the sky (or below ground the torch) by
  the angle you see it at, and glints in the sun. In rain the ground darkens and shines, and puddles lie on the roads.
  At night seven windows in ten are lit in the town.

  The seasons seen (v9.6): the trees wear the run's season - blossom on the oaks in spring, deep green in summer, red
  oaks and gold birches in autumn, bare branches and snow-laden firs in winter - and the leaves over the paths turn with
  them (CM.CROWNS in src/js/26-surface.js). Snow lies in winter on a day of snow and the day after (CM.snowLying): the
  roofs, the ground, the wall's walk and the hedges go white, and the river freezes. Mist lies low on the land.

  The gate towers and the postern (v9.7): two round towers of stone flank the West Gate (src/js/61c-tower.js). Space
  at the stair at a tower's foot climbs it: the party stands among the merlons with the town below, can turn to look
  round, and the watchman says what tomorrow's weather will be; any step comes down. Watch the sun go down from there for
  an achievement. Once a party has been to floor five, the postern - a small iron door in the Keep-yard's north-east
  corner - opens onto a path down the cliffs' foot to the fields: the short way from the shaft to the land, and back.

  The people's part (v9.8): one follower walks behind the party (src/js/64b-people.js) - a porter (the tavern, 30 gold:
  carries forty more), a torchbearer (the tavern, 20 gold: the torch burns at half the rate and is seen a square
  further), the farm's dog (once there's a cow: smells an ambush, won't go below the tenth floor), a hedge-wizard (the
  library at level three, 40 gold: a Light on each new floor, a Mend after a fight once a floor), or the adventurer you
  cut loose (picks the first lock of each floor, tells her story over three floors, and goes her way at a camp with a
  gift). A blow that misses a hero in the back row may catch the follower; one that falls is on the memorial, and the
  tavern won't hire to the party again that run. Six of the townsfolk have errands (the Journal's Errands page, in
  the town): a ring, a crate and a sickle to find on their floors, a carving to read, a champion to slay, iron ore to
  bring; three at a time, one from each a season, each paid in gold, renown, a thing or a favour that lasts.

  The Undercroft (v9.9): in the Wood's third cave, a stair of old stone that only a light finds goes down to the lower
  town that went under (src/js/64c-undercroft.js): three floors of standing water and drowned streets, five kinds of
  their own (Drowned Townsfolk, Eels, Marsh Lights that run from you, Cellar Spiders, and a Bell-Ringer leading a pack on
  each floor), and a carving on each that tells what the town forgot. In the bell-yard below the third stands the tenth
  guardian, the Bell-Founder's Boy, whose bell wakes everything on the floor; his relic is the Bell's Tongue. Past him a
  black door - once he has fallen and a party has been to floor six - opens onto the Flooded Vaults: a way to floor six
  that skips the Catacombs, and from floor six a flooded stair back down to the bell-yard.

  Around the world that moves (v10.0): ten more kinds for the Deep, two for each band below the Drowned Town
  (src/js/64d-bestiary.js) - the Spore Mother (a Sporeling bursts from her every third turn) and the Mycelid Crawler;
  the Glass Hound and the Prism Sentinel; the Bellows Imp and the Slag Golem; the Grave Lantern (its touch leads a hero
  astray, and the hero loses the moment) and the Charnel Hound; the Thorn Lotus and the Root Wyrm - each with a Crawl
  tile and a call. Runs that began on generator 1 never meet them, so their floors stay as they were. New sounds,
  cooked in code like the rest: a sleeper's snore, a door's hinge, a portcullis's chain, water lapping, the wind on a
  tower, the dog, the cracked bell. tools/perf.js measures a fourth scene, the town at night from a tower's top.
  Measured (tools/sim.js, Fair, 12 seeds to floor 50): v9.2 - 9 to the bottom, 2 fell; v10.0 - 10 to the bottom, 2 fell,
  both on floors 16 to 20, the party a little higher at each camp; with the town (10 seeds to floor 20), 6 crowned.

The town's buildings, rebuilt (v9.2)
  The houses were walls only where a street faced them, under a fringe of half-square slopes: the sky showed through the
  middle of every block, and a house beside a hedge, a fence or a tree was open on that side. Now CM.buildingsOf
  (src/js/26-surface.js) cuts the house cells into rectangles, the largest first, and each is built whole: plaster
  and timber on every outside face whatever stands beside it, a course of stone at the foot, and one gabled roof - two
  slopes from overhanging eaves to a ridge along the longer side, a darker ridge cap, and gable ends in plaster and
  timber up to the ridge. A wider house has a higher roof. A door or a shop shows its face once, toward its street.
  Most buildings carry a stone chimney through the roof (CM.chimneysOf), and the town's smoke rises from their tops.

The clock made visible (v9.1)
  A dial in the view's top-right corner shows the game's clock at a glance: the sky in the hour's colour (day, dawn,
  dusk, a starry night), the sun and the moon on their arc over a strip of ground - up from the season's dawn to its
  dusk, the moon opposite - and beside it the hour in figures and words, the day of the run and the season in its
  colour, the weather with the next three days' as small icons, a festival in its week, and the moon's face in its
  phase (glowing when full, ringed when new). Below ground it stays as clear, says "above", and its ground turns to
  stone. A click on the dial, or K, opens the Calendar: the moon's month as eight faces with tonight's marked, the
  next full and new moons and what they do, a week of weather ahead (the seed decides it, so it is shown), the four
  seasons' daylight hours, and the year's twelve festivals with this week's marked. The numbers are CM.dialOf,
  CM.nextMoon and CM.comingWeather in src/js/24b-calendar.js; the drawing is src/js/73b-clock.js.

The pack's weight, and selling in bulk (v8.7.2)
  Over the line of what the party can carry, the party only walks slower - up to three times as slow at twice the
  line and beyond - and never stops: Explore, Where to?, a click on the map and Automatic all walk at that pace. The
  torch and hunger cost nothing more for it. Once each time the pack goes over, the log says so and names the way out:
  a merchant at a camp or the Merchant's House, and a Scroll of Homecoming if the pack holds one. At a merchant's
  table two buttons sell in bulk - "Sell all shown" (everything the bag's filter shows) and "Sell spare gear" (worn by
  nobody, known, not cursed); the first click says how many things and for how much, the second sells. Keys, bones,
  pages, the field kit, relics and a Homecoming scroll that remembers a square below are never sold. Automatic, with
  the pack over the line below ground and a Scroll of Homecoming, reads it, sells at the Merchant's House (the spare
  gear first, then the heaviest of the rest) and comes back to the square it left by the same scroll. And a torch
  found after the last one went out is lit as soon as the party walks in the dark.

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
    10-data.js    the classes, gear, monsters (the Deep's too), the nine guardians, riddles and people, paths, tomes and gems, difficulties, mutators, achievements, keys, the ten depths
    20-world.js   items, CM.furnish and CM.makeFloor, monster groups, a new party
    21-gen1.js    generator 1: the floors of runs begun before v2.1 - frozen
    22-gen2.js    generator 2: the plan, then the carving - where new rooms go
    23-town.js    the town above, laid from data: the wall, the streets, the blocks, the signposts; townPlace
    23b-wood.js   the land west of the town: the road, the fields, the river, the forest, the caves; woodPlace, wayPlaces
    25-saves.js   a floor as what changed since the seed made it, the save's schema and its migrations
    26-surface.js the solid kinds and the ground, the sky by the clock, and every floor's mesh as arithmetic
    30-art.js     everything painted in code: stone, chests, monsters, portraits, the surface's houses, trees and signs
    35-packs.js   GENERATED by pack.py from src\art: the Pixel theme's atlas and the Stone theme's textures
    36-looks.js   the two looks (Pixel, Stone): each one's set for a depth and the surface, the dolls, the icons
    27-props.js   the props: what the scatter lays on each square, the traces, the wall decals, what drifts in the air
    40-render.js  the WebGL 2 view: the mesh, the sky, billboards, torchlight and fog, smooth steps and turns, shakes
    45-fx.js      what flies, bursts, rings and rains: the effects, advanced each frame into sprites
    64d-bestiary.js the Deep's ten more kinds, the Spore Mother's spawning and the Grave Lantern's light
    64c-undercroft.js the Undercroft: its floors, kinds, carvings, the Bell-Founder's Boy and the black door
    64b-people.js the followers and the townsfolk's errands
    64g-towerking.js the King of the Tower
    64f-towerfoes.js the Mage Tower's monsters in real time, and the floor bosses
    64e-towerrun.js the Mage Tower inside: the real-time hero, bolts, spells, monsters and bosses
    61f-cabin.js  Leshy's cabin in the Wood, the card collection and deck, his games and their winnings
    64h-cards.js  Claudescryption's rules: the cards, the sigils, the battle
    76b-cabin.js  Leshy's table: the games, the deck, the board
    61e-towerfloor.js the Mage Tower's forty floors
    61d-magetower.js the Mage Tower outside: the portal yard, the tower in the Wood, who may go in
    61c-tower.js  the gate towers and their lookout, the east postern and the cliff path
    61b-lairs.js  the lairs and sleepers, the light's reach and the noise, shading the torch, the champions
    46-air.js     the air: dust, drips, embers, spores, rain, snow, leaves, birds, clouds and smoke about the party
    50-audio.js   the sounds, each depth's ambience and the monsters' calls, synthesised
    55-music.js   the music, written from a seed and played as it goes
    60-game.js    the rules, with no screen in them: the class, its events, saving and loading, the stairs
    61-explore.js moving, looking, using: doors, traps, fountains, the monsters moving about the floor; walking by itself
    62-combat.js  the fight: turns, blows, spells, the monsters' ways, the Lich King and the guardians; Auto, the odds
    63-camp.js    the bag, the merchant, the temple, the tavern, the smith, the vault, the waystones
    64-meta.js    the dungeon's people, riddles, paths and boons, achievements, the Hall of Fame, Export / Import
    65-village.js the surface: renown, the buildings, trainers, candles, contracts
    70-ui.js      the window's frame, the dialogs, a hero's sheet, the ending
    73b-clock.js  the dial in the view's corner and the Calendar
    71-76         the title, the creation screen, the dungeon screen, the fight, the bag, the camp's doors
    80-main.js    wiring, keys, the frame loop
  src\art\pixel\*.png and src\art\stone\*.jpg are the chosen tiles and textures (pack.py --gather puts them there).
  python build.py writes game\Claude and Magic v<VERSION>.html from them (and removes an older version's file);
  python build.py --check says whether the built file is current. Bump VERSION in build.py for a new file name.
  tests/run.js and tests/smoke.js are the tests (npm test); tools/sim.js the balance simulator; tools/perf.js the frame's cost; tools/towerbot.js the Mage Tower's climb; tools/headless.js loads
  the rules into Node for both. Tests\test_claudemagic.py, in the Timeline, drives the built game in Qt WebEngine.

Keys
  W/Up forward, S/Down back, A/Left and D/Right turn, Q/E sidestep, Space use (a chest, the ladder or stairs, a
  fountain, an altar, a lever or carving on the wall you face - or search that wall), C cast between fights, I
  inventory, 1-4 a hero's sheet, Tab the automap large (click a square to walk there, right-click for a note), X explore, G
  Where to? on the surface, K the calendar, T shade or light the torch below ground; in the Mage Tower W A S D and the mouse, click or Space to shoot, right-click or R to cast, E at the ladder,
  Esc the menu. In a fight: F fight the chosen foe, C cast or a skill, P an item, D defend, R run, A auto, Tab or 1-9
  or a click to choose the foe, Esc back. Enter or Space closes the ending. F3 shows frames per second.
