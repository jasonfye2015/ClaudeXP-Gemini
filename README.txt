Claude and Magic - twenty floors down, the Lich King waits
==========================================================

A first-person dungeon crawler ("blobber", after Wizardry, Might and Magic and Eye of the Beholder): a party of four
moves as one through twenty floors of stone, a square and a quarter-turn at a time, smoothly, in 3D. Chests and
fallen monsters give gear and gold; a merchant's camp waits below floors 5, 10 and 15; the Lich King is on floor 20.
When the whole party falls the run is over - the deepest runs go in the Hall of Fame. Below the Lich King, the Deep goes
down to the Root of the World on floor 50; an Endless expedition goes on below that, with no bottom.

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
    20-world.js   items, a floor's maze with its chests, monsters and ladder, monster groups, a new party
    25-saves.js   a floor as what changed since the seed made it, the save's schema and its migrations
    30-art.js     every picture of the Drawn theme, painted in code: stone, chests, hatches, monsters, portraits
    35-packs.js   GENERATED by pack.py from src\art: the Pixel theme's atlas and the Stone theme's textures
    36-looks.js   the three themes: each one's set for a depth, the paper-doll portraits, the item and spell icons
    40-render.js  the WebGL 2 view: the floor's mesh, billboards, torchlight and fog, smooth steps and turns, shakes
    45-fx.js      what flies, bursts, rings and rains: the effects, advanced each frame into sprites
    50-audio.js   the sounds, each depth's ambience and the monsters' calls, synthesised
    55-music.js   the music, written from a seed and played as it goes
    60-game.js    the rules, with no screen in them: the class, its events, saving and loading, the stairs
    61-explore.js moving, looking, using: doors, traps, fountains, the monsters moving about the floor; walking by itself
    62-combat.js  the fight: turns, blows, spells, the monsters' ways, the Lich King and the guardians; Auto, the odds
    63-camp.js    the bag, the merchant, the temple, the tavern, the smith, the vault, the waystones
    64-meta.js    the dungeon's people, riddles, paths and boons, achievements, the Hall of Fame, Export / Import
    70-ui.js      the title, the party and log, the automap, the bag and merchant, the dialogs
    80-main.js    wiring, keys, the frame loop
  src\art\pixel\*.png and src\art\stone\*.jpg are the chosen tiles and textures (pack.py --gather puts them there).
  python build.py writes game\Claude and Magic v<VERSION>.html from them (and removes an older version's file);
  python build.py --check says whether the built file is current. Bump VERSION in build.py for a new file name.
  tests/run.js and tests/smoke.js are the tests (npm test); tools/sim.js the balance simulator; tools/headless.js loads
  the rules into Node for both. Tests\test_claudemagic.py, in the Timeline, drives the built game in Qt WebEngine.

Keys
  W/Up forward, S/Down back, A/Left and D/Right turn, Q/E sidestep, Space use (a chest, the ladder or stairs, a
  fountain, an altar, a lever or carving on the wall you face - or search that wall), C cast between fights, I
  inventory, 1-4 a hero's sheet, Tab the automap large (click a square to walk there, right-click for a note), X explore,
  Esc the menu. In a fight: F fight the chosen foe, C cast or a skill, P an item, D defend, R run, A auto, Tab or 1-9
  or a click to choose the foe, Esc back. Enter or Space closes the ending. F3 shows frames per second.
