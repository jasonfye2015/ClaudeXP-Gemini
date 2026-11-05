# Upgrade plan 54: light and sky (v59.0)

Asked for 2026-11-05: the first of six sets ("create and complete every suggestion you have put forth"). Much of
the set as first suggested was already in the game (the sky and its stars, storms, the lamps and the lit windows as
lights, the hour's grade), so this plan is what was missing from it.

## v59.0 - the light of the hour (24c-light.js, 76zzzzzzzzzz7-light.js, 40-render.js)
- The sun's colour on what faces it: gold at dawn and dusk on the sunward walls and the ground, white at noon,
  silver-blue under the moon; the sky warms about the low sun and cools on the far side; the water's glint in the
  sun's colour.
- Mist on the water and its banks at dawn (thickest in autumn and spring, less in summer) and on autumn and spring
  evenings; none in rain or snow, none below ground.
- Halos about the lamps and the lit windows in the damp night air - wide in mist and rain, faint on a clear night
  (a soft sprite: a glow of 1.3 keeps its faint edge instead of the usual alpha cut).
- Fixed: moss grew on the barrels and the well again when they stood against a wall - it keeps to squarely-set
  wall faces at a square's edge now.
