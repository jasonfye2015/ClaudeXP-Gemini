# The fourteenth and fifteenth big updates: the Fortress, and Claudeatro's house

## v11.4: the Fortress (DONE)
Asked for: a Fortress in the Wood with large dark brown doors, a portal from town like the others, for melee
characters as the Mage Tower is for casters; Gauntlet-style play - keys that open sections of wall, large maze floors,
finding the stairs down, potions, gold and experience on the way; twenty floors of varied monsters to an end boss;
death returns the fighter to the party outside with 10% health and none of the gold or things, keeping experience;
between floors they may leave and come back to resume.
- src/js/61h-fortress.js: the keep north of Leshy's clearing (black walls, four corner towers and two flanking the
  doors, the great arched doors of dark wood and iron), the path down, the portal home; a third portal in the yard.
  Fighters: Knight, Paladin, Rogue, Monk (and a Ranger with a blade). The rules: what a floor gives is carried; out by
  the stairs, all of it is the party's; out mid-floor, that floor's finds are lost; a death loses everything carried
  and leaves a tenth of the fighter's health; experience always. Progress is kept: in again at the next floor.
- src/js/64j-fortress.js: the floors (a maze of two-wide halls opened into rooms, doors across the way down with a key
  for each before it, treasure closets behind doors of their own, lairs that send monsters until broken, draughts,
  gold, fire flasks, chests), the run in real time (move, swing in an arc, knock back, keys open whole doors), the
  Wardens on floors 5, 10 and 15 and the Iron Marshal on 20 (charges, slams, calls help at half).
- src/js/76d-fortress.js: the floor seen from above, the monsters in the game's own pictures, the fighter's token.
- tools/fortbot.js measures it.

## v11.5: Claudeatro's house
Asked for: a building in town, a little richer than the rest (a casino), hosting Claudeatro from the Games folder;
wager gold and earn gold back for each round; keep the game's unlocks; play for nothing, for fun and unlocks.
