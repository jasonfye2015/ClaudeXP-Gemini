Claudenites 3-D
===============

A first-person roguelike in the Deep under Thornwick: the story of Claude before Claude and Magic, when he was an
apprentice with a birch wand. A hundred floors, ten bands of ten, a guardian at every tenth, and at the bottom the
thing the town is built over.

Playing
  WASD move, mouse look (click to take the mouse, Esc gives it back), left button cast, Space jump,
  F talk / use (the vendors, the stairs, the Deep's mouth), Q health potion, E mana potion, T Scroll of Return,
  1-4 or the wheel: change wand, Tab the pack, M the big map, Esc the menu.

  Thornwick is home: four vendors round the square - Hesper the Apothecary (potions, Scrolls of Return), Old Tamsin
  the Wandwright (wands and wand parts), Bramwell the Outfitter (hats, robes, gloves, boots, rings, amulets) and
  Mother Wren the Sage (the three skill trees) - and the Deep's mouth in the middle. At the stairs on every floor,
  go deeper or go home; the way down waits at the floor reached. A Scroll of Return brings him home from anywhere.

  If Claude falls he wakes in Thornwick with everything: his gold, his pack, his gear, his levels and his skills.
  Only the run is lost - the Deep starts again at floor 1, and its floors are new.

  Wands: a body (its shots a second, bolt speed, base damage, mana a shot and how many slots) and the parts set in
  its slots: a Core (Fire, Frost, Storm or Venom - the bolt's element), a Lens (damage), a Splitting Prism (more
  bolts, wider), a Focusing Ring (tighter, faster), a Quickening Rune (faster casting), a Seeker's Eye (homing),
  a Rebounding Band (bounces) and a Piercing Thorn (passes through). Fire burns, Frost slows, Storm leaps to the
  next foe, Venom stacks; Arcane hits harder. Four wands ready at once.

  Three save slots. Saves live in the Timeline's ClaudeGames/Saves/claudenites/ (slot1.json .. slot3.json).

How it's made
  Python, PySide6 (the window, the menus) and OpenGL 3.3 through PyOpenGL (the view), with numpy.
    game/     the rules, with no Qt and no GL: levels (the floors and the town), world (the running game), player,
              items (wands, parts, gear, loot), skills, shop, saves, data (the tables)
    engine/   gl (programs, meshes, textures), render (the frame), levelmesh, figures (Claude and Magic's figures and
              plants, read with numpy and skinned on the card), sound (made at start)
    ui/       shell (the window's content), view (the loop, the input, the HUD), panels, icons, skills_panel
    assets/   imported from Claude and Magic by tools/import_cm.py (see CREDITS.txt)
    tests/    python tests/run.py - the rules, played headless (no Qt needed)

  python tools/play.py        play this copy on its own (with the Timeline's Python)
  python tools/import_cm.py   bring Claude and Magic's art across again

In the Timeline it's ClaudeGames/claudenites (a subtree of this repo): in the launcher's Apps, and in each
computer's Games.

The plan: PLAN.md.
