# UPGRADE_PLAN_66 - The deeper shaft: the Lich King on 70, the bottom on 100

Asked for: the Lich King moved from floor 20 to floor 70; the Deep from 71 to 100, the bottom of the world; Endless
below that with the dark deepening every ten floors; the Endless achievements at 110 and 150 (were 60 and 100).

## 1. The design: story floors and real floors

Everything the game knows about depth is written in the old fifty floors - the ten bands of five, the guardians on
5, 10 ... 50, the fifty carved chapters, the camps below 5, 10, 15, 25 ..., the uniques, the wings, the kits and the
achievements, the loot's tiers and the monsters' levels. Rewriting every table for a hundred floors would be a year
of retuning. Instead the shaft is **stretched**: the old numbering becomes the **story floor** (`CM.storyOf(n)`,
1-50) and the real floor count goes to 100:

- real 1-70 -> story 1-20: `storyOf(n) = ceil(n * 20 / 70)` - three or four real floors to a story floor;
- real 71-100 -> story 21-50: `storyOf(n) = n - 50` - the Deep, one to one;
- below 100: Endless, as before (`storyOf(n) = n - 50` still; the bands come round five floors at a time).

`CM.realOf(s)` goes the other way (the **key floor** of a story floor: the last real floor that maps to it: 3, 7,
10, 14, 17 ... 70, then 71 ... 100), and `CM.isKeyFloor(n)` says whether a real floor is one. The guardians, the
merchants' camps and the Lich King stand on key floors only; the other real floors are ordinary floors with the
band's look, its monsters, its loot - and room for the set pieces (plans 64 and 65).

| | before | after |
|---|---|---|
| the Catacombs | 1-5 | 1-17 (the Rat King on 17) |
| the Flooded Vaults | 6-10 | 18-35 (the Drowned Knight on 35) |
| the Dwarven Halls | 11-15 | 36-52 (the Forge-Warden on 52) |
| the Lich King's Palace | 16-20 | 53-70 (the Lich King on 70) |
| the Drowned Town | 21-25 | 71-75 |
| the Fungal Deep | 26-30 | 76-80 |
| the Crystal Caverns | 31-35 | 81-85 |
| the Foundry | 36-40 | 86-90 |
| the Ossuary | 41-45 | 91-95 |
| the Root of the World | 46-50 | 96-100 |
| Endless deepens | 61, 71 ... | 111, 121 ... (echo guardians on 110, 120 ...) |
| Without End / Beyond the Dream | 60 / 100 | 110 / 150 |

The upper bands are long and the Deep's are short because the asking was "the Lich King on 70, the Deep to 100";
the table is data (`CM.THEMES[].floors`, computed from the story floors) and can be re-split later.

## 2. What reads depth, and how it changes

- **Themes, guardians, camps, uniques, wings, the Bag of Holding, the Lost Page, the heart**: by story floor and key
  floor. `CM.THEMES[].floors` and `CM.ORES[].floors` become real ranges at load; `band * 5 + 1 .. + 5` arithmetic
  (uniques, wings, the palace's shops) reads the band's real floors; `CM.CAMP_AFTER` stays in story floors and
  `CM.CAMP_FLOORS` is its real list.
- **Difficulty and loot**: `CM.monsterLevel(real)` = the old curve on the story floor (level 20 at the Lich King,
  35 at the bottom, half a level a floor below it). Loot keeps its old units: every `makeItem` / `affix` /
  `makeMonster` / `makeRecruit` call that passed a real floor now passes `CM.storyOf(fl.number)`. The depth clamps
  of the tower, the Fortress, the glyphs, the cascade, the spoils and the crafts (`CM.BOTTOM || 50`) read
  `CM.STORY_BOTTOM` (50): they were story depths already.
- **Experience**: three and a half times the fights to the Lich King would carry the party far past the old level
  twenty; fights above the palace's floor give 0.45 of their experience (`CM.xpScale`), so a party reaches the
  Lich King a little stronger than before (about level 23) and the Deep's climb is as it was.
- **Lore**: the carvings read the story floor's chapter (`text: storyOf(n) - 1`; the Dream's fifty too), so three
  or four floors share a chapter; the ghosts' and people's floors go through `realOf`.
- **Kits and achievements** in real floors: Veteran 17, Scholar 28, Delver 35, Heir 52, Abyss 80; Delver 17, Of
  the Vaults 35, Of the Day 35, Of the Halls 52, Of the Palace 70, Of the Foundry 90, Of the Deep 80, To the Bottom
  100, Without End 110, Beyond the Dream 150; the Legend's kit wants the crown (`need: -1`).
- **Set pieces**: a template's `min` / `max` are story floors (`CM.storyOf(number) >= r.min`).
- **Texts**: the tagline, the README, the over-screen's "of 70 / of 100", the Endless line "below the hundredth
  floor", the Timeline's help guide.
- **Not changed**: the Mage Tower (forty floors of its own), the Fortress (twenty), the Undercroft, the Joker's floor,
  the Wood, the town.

## 3. Old seeds and saves

The first generator's frozen fingerprints (tests/fixtures/gen1.json) are regenerated: the world below floor 3 is
not the world it was (guardians and camps moved, bands stretched), and a run saved mid-way carries on at its floor
number in the new band. The Hall of Fame's old entries keep their floor numbers; "floor 20, crowned" reads as it did.

## 4. Progress

- v90.0 - the stretched shaft (this plan, one release): `CM.storyOf`, `CM.realOf`, `CM.isKeyFloor`,
  `CM.STORY_LAST`, `CM.STORY_BOTTOM`, `CM.CAMP_FLOORS`, `CM.xpScale`; the constants; every site above; the test
  "the shaft is a hundred floors deep".
