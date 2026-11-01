# Upgrade plan 14: the South Fields (v19.0 - v19.5)

Approved 2026-11-01. The open bowl in the south of the town (rows 32-36 of the 45x45 town) becomes farmland the
party works by hand and, later, by the village's own hands. The Glade farm (69c-farm.js) and the alchemist's beds
(69b-square.js) stay as they are; the fields share their seeds and crops (CM.CROPS, CM.FOODS) so a seed is a seed
anywhere.

Art: [LPC] Crops (bluecarrot16 et al., CC-BY-SA 3.0+ / GPL 3.0+; 67 crops, four growth stages and an after-harvest
cell, 32x64) for the plants; josehzz's Farming Crops 16x16 (CC0) for the crops LPC lacks (wheat, rice, sunflower,
roses, tulips); Kenney's Tiny Farm (CC0) for small window icons. The whole sets are kept in
`Local Storage\Farm - Sprites`; `tools/cropsheet.py --gather` copies the chosen cells into `src/art/crops.png` and
writes `src/js/35b-croppack.js`. Credits in `src/art/CREDITS.txt`.

## Phase 0 - v19.0 the land and the loop
- The South Fields as a village building (CM.VILLAGE.fields): four levels, 24 / 48 / 72 / 100 plots, the later ones
  wanting island timber and stone (CM.VILLAGE_MATS).
- Plots on the town floor (things of type "plot"); tilled ground; the crops drawn from the crop atlas, two plants a
  plot, by stage.
- Till, sow, water, harvest - by Space on the plot underfoot or ahead, or from the fields' window (a top-down grid).
- Growth by the dawns the party sees, like the Glade farm: a stage a day only when watered (rain waters everything);
  winter grows only the winter crops. Some crops regrow after picking.
- The seed shed at the fields' east end: seeds in season, a watering can (ten waterings; refilled at the trough).
- About thirty crops, the six old ones among them, each with its seasons, days, yield and value.

## Phase 1 - v19.1 water and quality
- Dry days: two stall, four wilt. Quality one to five stars from the watering streak, compost and the soil's rest.
- Compost (trimmings in, compost out), giant crops (a 3x3 of ripe of one kind, now and then), pests and weeds.

## Phase 2 - v19.2 the village's hands
- Sprinklers from the island's bars (copper a cross, iron a square, star-iron a big square).
- The field crew (the farmhand grown up): a plan per row (what to keep sown), sowing, watering, harvesting into the
  silo; the party's Automatic does the rounds. A greenhouse corner that ignores winter. A seed-maker.

## Phase 3 - v19.3 seeds and trimmings from everywhere
- Rare seeds by place: the dungeon by depth, the Wood's forage, Leshy (for cards), the Mage Tower, Haven, the island,
  the cave, the Fortress, the pipe, the Joker's counter and jackpots. Cuttings carry a crop's quality.

## Phase 4 - v19.4 what the fields are for
- The market stall in the Square, the Harvest Fair's biggest-crop contest, crops on the request board, the alchemist's
  herb potions, brewing, crop cards for Claudescryption, renown for the fields.

## Phase 5 - v19.5 the fields, finished
- Seasons on the field (frost, blossom), sounds, residents at work in the rows, the last balance pass, docs.
