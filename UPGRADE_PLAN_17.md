# Upgrade plan 17: light and air (v22.0 - v22.5)

Asked for 2026-11-01: items 1-7 of the graphics list, everywhere - the town, the Wood and every floor below (one
renderer draws them all). What was there to build on: twelve coloured point lights (wall torches, decor, glowing
props), the party's torch at the eye, the sun's direction on the surface, a grade per band, low mist, rain and snow on
the ground, blob shadows. Each phase is measured against the start-up and frame figures of v21.4.

## v22.0 - light (1)
- Up to 24 lights a frame, each with its own flicker; more things give light: the court's braziers and portals, the
  Glyph Deep's cabinet, the Wayfarer's Stone, the town's lit windows after dark, lanterns, campfires; spells and
  blasts flare for a moment where they strike.
- The party's torch held a little to the side and above, so surfaces it lights have a facing.

## v22.1 - surfaces (2)
- Walls, floors and the ground take relief from their own pictures (a height read off the picture's light and dark,
  turned into a normal per pixel), so every light - the torch, a brazier, the sun - rakes across stone and brick. In all
  three looks, stronger in Stone. Wet ground and polished stone get a highlight.

## v22.2 - shadows (3)
- Figures, props and trees cast shadows away from the strongest light near them (the sun by day, a torch below),
  stretched by the light's angle - long at dawn and dusk.

## v22.3 - air (4)
- Fog with body: drifting, thicker low, by place (the Drowned Town and the Undercroft thick, the Foundry hazy, the
  Wood's hollows misty at dawn). Light shafts: sunbeams through the Wood's canopy and the town's lanes, dust in them;
  below, a haze in the torchlight.

## v22.4 - grade and hour (5, 6)
- Each band its own grade (lift, contrast, saturation), not only a tint. The surface by the hour: gold at dawn and
  dusk, blue after, the colours drained at night. Frost on walls on winter mornings; the wet ground's sheen.

## v22.5 - glow (7)
- Bloom: what's bright - magic, portals, lanterns, gold, the sun - softly haloed. A setting, and off at the lowest
  Detail. The whole set measured again.
