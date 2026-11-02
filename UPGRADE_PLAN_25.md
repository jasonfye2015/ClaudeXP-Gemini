# Upgrade plan 25: the world, sharper (v30.0 - v30.9)

Asked for 2026-11-02: all of set 9 of the new list (items 39-48). Everything here is the picture's: the rules don't
change. Each phase is its own window file (76zzzzza-... on), with the renderer (40-render.js) given what it needs, and
one hook in 80-main.js (CM.beforeFrame, called just before the frame is drawn) that they all share.

## v30.0 - wet surfaces (39)
- Rain darkens stone and cobbles and puts a sheen on them; puddles lie in the low places (by a noise of the ground),
  mirror the sky and the lamps, and ring with the rain.
- A wet morning after a day of rain: the sheen dries in the first hour of sun, the puddles shrink till noon.

## v30.1 - marks that stay (40)
- Scorch where fire spells land, blood where foes fall, footprints in snow and mud (the party's trail): lying flat,
  fading with the game's clock (footprints in an hour, blood and scorch in a day). Kept per floor, not saved.

## v30.2 - the sky (41)
- Clouds drift with the wind and their shadows cross the ground; stars at night; the moon's face waxes and wanes by its
  phase; an aurora on clear winter nights; lightning flashes (and thunder) on some rainy evenings.

## v30.3 - soft corners (42)
- Ambient occlusion: the floor darkens softly along the walls (a map of the walls, read by the shader), the foot and
  the head of each wall darken too.

## v30.4 - heat and cold (43)
- The air shimmers above braziers, the forge and fire (a screen pass that bends what is behind); the party's breath
  shows on winter days and in the cold deep; ice and crystal walls glint as the eye moves.

## v30.5 - smoke and chimneys (44)
- The town's chimneys smoke (thicker in the evening and in winter), the wind takes it; the wall torches' smoke rises
  and runs along the ceiling; braziers and the camp's fire smoke.

## v30.6 - grass that moves aside (45)
- Tall grass, reeds, crops and ferns bend away from the party as it walks through, and spring back behind it.

## v30.7 - the deeper, the older (46)
- The walls age with the depth: clean dressed stone in the first floors, then cracks and roots, then fungus that
  glows, then strange veined stone in the deepest.

## v30.8 - water you can see into (47)
- Shallows show a bed of pebbles and weed, and now and then a fish; foam where the river meets its banks and rocks;
  rings where the party, its followers and the beasts wade.

## v30.9 - better far distance (48)
- Far billboards (trees, props) fade in instead of appearing; the far land takes the colour of the air (bluer, paler)
  the further it is.
