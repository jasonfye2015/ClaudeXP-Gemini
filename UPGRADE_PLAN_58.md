# Upgrade plan 58: the interface (v63.0)

Asked for 2026-11-05: the fifth of six sets. The party's cards with their bars and ailments, the turn-order strip,
tooltips that compare, the living minimap, the parchment map that remembers, the Stone interface and the place
transitions were already in the game (plans 18, 20, 26, 37, 47), so this plan is what still felt plain.

## v63.0 - closer to hand (64zzzd-foemarks.js, 76zzzzzzzzzzb-gui.js, 74-fight.js, style.css)
- In a fight each foe's row has a health bar (its part's too) and its marks - asleep, held, marked, blinded,
  burning, chilled, warded, a broken part, what it carries, under the floor - as small tags with tooltips, in place
  of the run-on line of words (CM.foeMarks, for the tests).
- In the pack a thing can be dragged onto a hero's card to give it; at the merchant's, onto the wares to sell it, or
  a ware onto the pack to buy it. The clicks work as before.
- A short fade into and out of the real-time places (the Mage Tower, the cave, the Fortress, Claudeablo, Claudebros,
  Claudecraft) in place of the cut.
