# Upgrade plan 15: The Glyph Deep (v20.0 - v20.2)

Asked for 2026-11-01: a full-sized arcade game in the forest - a roguelike drawn in ASCII, the classic way (rooms,
corridors, letters for monsters, symbols for things) - that one hero enters alone. It is our own game in that style:
its own monsters, things, levels and last boss, not a copy of any existing roguelike.

## The cabinet
- A lone arcade cabinet under a lean-to by the Wood's road (a small clearing north of the road, west of the fields),
  green letters on its screen. Use: who plays, and from which level (any level reached so far: levels can be replayed).

## The game
- Twenty levels, 80x21 each: rooms and corridors, doors, the up stairs where you start and the down stairs somewhere
  far off. Lit rooms seen whole; corridors a step around you; what's been seen remembered.
- Turn by turn: arrows / numpad / hjklyubn to move and attack, g to pick up, q quaff, r read, w wield, W wear, e eat,
  d drop, . wait, > at the stairs. Mouse too: click a square to step toward it, click a thing in the pack for its uses.
- The hero is the party member chosen, with their real health, attack, defence, weapon and skill tree; monsters use
  the main game's own numbers (CM.makeMonster) under the deep's own names and letters, by depth.
- Things: $ gold, ! potions, ? scrolls (mapping, teleport, fire, enchant weapon, enchant armour), ) weapons, [ armour,
  = rings, " amulets, % rations, , seeds for the South Fields, ~ inscription cards (Claudescryption), * prize tickets.
  Weapons, armour, rings, amulets, potions, rations and seeds are the main game's own things, made for the depth, so
  what comes out is worn and used in the overworld; a weapon or armour wielded/worn inside counts inside.

## The rules asked for
- At the down stairs: go down, or go back to the party with everything carried.
- The first time each level's stairs are reached: tickets, gold and a thing, paid at once to the party (once only).
- Level 20: the Unwritten, the deep's last boss, holds the way; beaten, several high-end prizes and many tickets.
- Death: back with the party at a tenth of their health, without the gold and things found on that level (what was
  found on the levels before is kept). Experience always.

## Phases
- v20.0: the cabinet, the game whole (levels, monsters, things, the rules above), its window, tests.
- v20.1: the deep's life - traps, a mimic or two, monsters with ways (fast, slow, regenerating, draining, breathing),
  the boss's fight, sounds; a bot that plays it to measure the levels; tuning.
- v20.2: polish - the cabinet's attract screen, the world map, the goals page, renown, docs and lore.
