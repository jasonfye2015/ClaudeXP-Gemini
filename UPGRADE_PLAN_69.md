# UPGRADE_PLAN_69 - The title screen on one page

Asked for: the screen after the title card has grown to about four screens of scrolling (3,087 px of content in an
800 px window). Redo it with buttons and pages so that everything fits on a single screen.

## 0. What is on it today

One tall sheet in two columns that scrolls as a whole:

- **Left column, "Expedition"**: the three save slots, Continue and its note, New Expedition, the seed box with the dice,
  Today's and This week's buttons, two paragraphs explaining run codes and seeds; then "The callings" - all eleven
  with their portraits and a paragraph each (the tallest block); then a long paragraph on how a run goes.
- **Right column, "Hall of Fame"**: the three boards (the dungeon, Endless, this week); Unlocks (the kits, with their
  conditions); Trophies (fourteen guardians); In memoriam (the fallen heroes); Achievements (the daily table and all
  ninety-three achievements, done and not done) - the longest block on the page.
- **At the very bottom**, below everything: the look picker and The Village, Settings, Keys, Export / Import,
  Statistics, Credits, Install. They are the most-used buttons, and the hardest to reach.

## 1. The design: a hub and pages

The screen becomes a fixed frame that never scrolls, with three parts:

```
+-----------------------------------------------------------------------------+
|  [emblem] Claude and Magic      Adventurer of the Deep - 13 of 93           |  header, one line
+-----------------------------------------------------------------------------+
|  [ Play ] [ Callings ] [ Hall of Fame ] [ Progress ] [ Memorial ]           |  the pages, as tabs
+-----------------------------------------------------------------------------+
|                                                                             |
|                     the page: always fits, never scrolls                    |
|                                                                             |
+-----------------------------------------------------------------------------+
|  Village   Settings   Keys   Export/Import   Statistics   Credits   Install |  the toolbar, always there
+-----------------------------------------------------------------------------+
```

**Play** (the page it opens on). This is everything needed to start, at a glance:
- The three slots as three cards side by side: the place, the floor, the gold, the party's four portraits and the date
  saved. A click selects one, and Continue is the big button under the selected card. An empty slot's card reads "New".
- New Expedition, with the seed box, the dice, Today's and This week's in one row beneath it.
- The two explanation paragraphs fold into a "?" button beside the seed box: a short popover, closed by default.
- If the party has a festival, a weekly challenge or a daily record, a single line under the slots says so.

**Callings**. A grid of the eleven portraits (sprites, as now), one row of six and one of five. Clicking one shows its
paragraph, role and paths in a detail panel beside the grid. The first is shown until another is clicked. The run
paragraph moves to the bottom of this page as a single line, with "more" opening the rest.

**Hall of Fame**. The three boards as sub-tabs (the dungeon, Endless, this week), ten rows a page with arrows and
"1 / 3".

**Progress**. Unlocks, Trophies and Achievements as sub-tabs:
- Unlocks: the seven kits as cards, done or with how far there is to go.
- Trophies: the fourteen guardians as a grid of badges, greyed until beaten, with their floor on hover.
- Achievements: a grid of badges, as many as fit the space and paged after that, with a filter (all, done, to do)
  and the daily table as its own small panel.

**Memorial**. The fallen heroes as cards (portrait, calling, level, floor, date, epitaph), paged.

## 2. How it fits every window

- **Paging by measure, not by count.** Each list measures its panel's height and puts on a page only what fits; the
  arrows and "1 / n" appear only when there is more than one page. A tall window shows more per page, a short window
  shows fewer, and nothing ever scrolls.
- **Narrow windows** (under about 900 px): the tabs become a row of icons with their names under them, the Play page's
  slot cards stack two-up, and the toolbar folds into a "More" menu.
- **The keyboard and the pad.** Keys 1-5 or Q/E switch pages, the arrow keys page a list, and Enter is Continue on the
  Play page. The pad's shoulder buttons switch pages. Focus outlines are visible.
- **It remembers** the page last open, per browser (a convenience: the game opens on Play if it's missing).
- **Reduced motion**: pages switch without a slide.

## 3. What stays the same

- Every element id the code already uses (btn-continue, btn-new, seed, btn-daily, btn-weekly, classes, fame, unlocks,
  trophies, memorial, achievements, the toolbar's buttons) is kept and moved into its page. The functions that fill
  them keep working, and the Timeline's tests (which drive the game through CM.game) don't notice.
- The New Expedition screen (the party's creation) is not part of this. It could get the same treatment later if it
  has grown too.
- The look of the game: the same dark panels, gold headings, fonts and frames.

## 4. Order

1. Release 1: the frame, the tabs, the toolbar always visible, the Play page with slot cards, and the other pages
   holding today's content as-is (each in its own panel, with measured paging for the lists). This alone ends the
   scrolling.
2. Release 2: the polished pages - the Callings grid with its detail panel, the trophy and achievement badges with the
   filter, the memorial cards, the narrow-window layout, and the keyboard and pad.
3. Checked by screenshots at 1280 x 720, 1180 x 800, 1920 x 1080 and 900 x 600, plus a test that no page's content is
   taller than its panel at those sizes.

## 5. Progress

- v102.0 - both releases in one (77d-titlepages.js): the frame, the tabs and the toolbar; the Play page with slot cards
  and a row at a glance (best runs, deepest and the next kit, who fell lately and the nemesis); the Callings grid with
  a detail panel (role, stats, starting gear, the two paths); the boards, unlocks, trophies, achievements (filtered)
  and memorial paging by measure; keys 1-5, Q/E, Tab and the arrows; the last page remembered; compact rules under
  900 px wide or 700 px tall. Measured in the window at 1180x800, 1280x720, 1920x1080 and 900x600: nothing scrolls,
  no row spills.
- Decisions taken: the narrow-window toolbar wraps to two lines rather than folding into a "More" menu (it fits);
  the pad's shoulder buttons arrive as Tab, which switches pages; the run-code and seed paragraphs sit behind "?".
