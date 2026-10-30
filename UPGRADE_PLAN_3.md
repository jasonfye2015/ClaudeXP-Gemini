# Claude and Magic - the fifth big update: lore and story

Where the game stands (v3.0, after the fourth big update): fifty floors in ten bands with wings off them, eleven
callings with second callings, a village on the surface, magic with decisions in it, fights with ground under them,
a difficulty ladder, replays and films, a statistics ledger, an app that installs. ~14,000 lines of JS. Every seed
makes the same floors in every version; every fight's dice are the seed's.

The fourth update was about **systems**. This one is about **the story those systems happen inside**: who Caer Duin
was, what the king did, what the Root dreamed, and what the player's own parties leave behind. Same shape as before:
phases, each shippable, each with tests, each a version (v3.1 ... v3.9, and v4.0 when the endings land). Phase 0
again pays for the rest.

A word budget first, because story work sprawls: the game holds about **6,000 words of lore** today (fifty carvings,
eight odd ones, eight endless ones, nine guardian lines, six ghosts, three requests, a hermit, twelve events). This
plan adds roughly **25,000** - a short novella, spread thin over fifty floors and a village, never more than a
screen at a time. The voice stays the game's: dry, short, a knife in the last clause.

---

## What is already there (and must not be broken)

The story as the carvings tell it, top to bottom:

| Band | Floors | What the walls say | Who guards the way down |
|------|--------|--------------------|-------------------------|
| The Catacombs | 1-5 | Caer Duin's first dead; the plague in King Mordeth's twelfth year; the queen dies; the bells come down | the Rat King |
| The Flooded Vaults | 6-10 | the lower town drowns in a night; a stranger from the east leaves a box; the king stops sleeping | the Drowned Knight (the captain of the watch) |
| The Dwarven Halls | 11-15 | the dwarves' cold coin; orders in a hand not quite his; the physician's page: *the heart may be kept apart* | the Forge-Warden |
| The Lich King's Palace | 16-20 | built in a year by hands that did not tire; the court that does not breathe; the heart is not in his chest | the Lich King (and his phylactery) |
| The Drowned Town | 21-25 | *the water was let in*; the queen's barge; who held her under | the Drowned Queen |
| The Fungal Deep | 26-30 | the dead put down a shaft; something grew on them and learned | the Mind |
| The Crystal Caverns | 31-35 | the crystal that mines the miners; *it has my face now* | the Tyrant |
| The Foundry | 36-40 | the box was made here; the man from the east was from here | the Forge Master |
| The Ossuary | 41-45 | the Patriarch kept the dead before there was a king; he did it first | the Patriarch |
| The Root of the World | 46-50 | everything above is its dream; wake it and end it, or leave it to dream | the Root |

Named people, so far: King Mordeth; the queen (unnamed); the court physician (unnamed); the captain of the lower
watch; the stranger from the east who was not; Hal, Ysolde the cook, Brother Cael, Tamsin who kept the tally, Aldous
the Lesser, Mother Ennis (the six ghosts); the child who wrote MOTHER SAYS NOT TO LOOK AT HIM.

Devices already in play, worth more use than they get:
- **The upper carvings lie and the lower ones correct them** (the queen "died of the plague"; the water "rose" - it
  was let in). The story has an unreliable narrator built in.
- **Ghosts with requests** (bones, vengeance, a story read to them) and **the hermit who is paid in stories**: the
  journal is already currency.
- **Awakened** runs mirror every floor: "the Root remembers you". Nothing in the text changes yet.
- **The memorial and the fallen**: your own dead have names, callings, floors and dates, and a later run on the
  seed finds their remains. They say nothing yet.
- **Bonds and banter**, four lines of it.
- **The village**: four buildings and no one in them.

What the story cannot do today: it cannot be read in order (the journal is a flat list); it never speaks (no one
says a word before a guardian fight, and the Lich King says one line); it has one ending for the crown and one for
the bottom; it does not know the player's own history; it is the same fifty lines on every run.

---

## What v3.0 invites

| # | Observation | Where | What it means for this plan |
|---|-------------|-------|-----------------------------|
| 1 | **Lore is scattered** across `CM.LORE`, `CM.LORE_EXTRA`, `CM.LORE_ENDLESS`, guardian `lore:` fields, `CM.GHOSTS`, `CM.REQUESTS`, `CM.HERMIT`, `CM.EVENTS`. No index, no order, no canon. | `10-data.js`, `20-world.js` | Phase 0: one file (`13-lore.js`), keyed, with chapters; a canon document for the writing; a codex screen. |
| 2 | **Floors are frozen, text is not.** A carving's *text* is a feature value; `CM.furnish` already adds things by hash without moving a floor. | `25-saves.js`, `CM.furnish` | New carvings, speakers and scenes can go on old floors by hash. Variant tellings per seed are free. |
| 3 | **Everything is logged and replayable.** A story choice is one more `logAct` line. | `game.logAct`, `CM.replayStep` | Branching is cheap, and films carry the branches. |
| 4 | **The journal is a list.** Read once, kept, paid to the hermit. | `game.journal`, J | A codex: chapters, blanks for the unread, the lies struck through when the truth is found. |
| 5 | **Guardians warn and change form, but never speak.** | `CM.GUARDIANS` `warn`, `form2` | A parley before each lair, with a lore-gated way through for those who read the walls. |
| 6 | **The Lich King has one line and one ending.** The heart hunt is a box on a floor. | `62-combat.js`, `phylactery` | The court as people; clues to the heart; *remind him* as a second ending. |
| 7 | **The Root offers a choice the game doesn't take.** "Wake it, or leave it to dream." | the last carving, `endRun` | Three endings at the bottom, and Awakened becomes the consequence of one of them. |
| 8 | **The village has no villagers.** | `65-village.js`, `76-camp.js` | A chronicler, a priest, a keeper: the story's surface, where the codex lives and rumours seed the next run. |
| 9 | **Your dead are data.** Memorial names, the fallen's floors, the ledger, the Hall of Fame's legends. | `memorial`, `fallen`, `ledger`, `fame` | Carvings about *your* parties; ghosts who were your heroes; a Book of Caer Duin that your runs write into. |
| 10 | **Heroes have names, stats and quirks, not pasts.** | `72-create.js`, `CM.QUIRKS` | Origins, with a line to say at the right wall; epitaphs; last words. |
| 11 | **The bot reads nothing.** | `tools/bot.js` | Every phase adds the bot's use of its story mechanic, or the sim measures nothing. |

---

## Phase 0 - The spine (do first) - v3.1 - DONE

The writing needs a canon and the code needs a shelf.

- **`LORE.md`**: the canon. A timeline of Caer Duin (the founding; the Patriarch's order; Mordeth's reign year by
  year to the twelfth; the plague; the queen; the box; the drowning; the dwarves; the palace; now), the dramatis
  personae with what each knows and what each lies about, the truth of each band, and the Root's dream stated
  plainly once so every phase writes from the same facts. Not shipped in the game; the writer's bible.
- **`src/js/13-lore.js`**: every string of story moves here, keyed - `CM.LORE_TEXT["carving.catacombs.1"]` - with a
  `chapter` and an `order` on each. `CM.LORE`, `CM.LORE_EXTRA`, `CM.LORE_ENDLESS` and the guardians' `lore:` become
  views over it so nothing that reads them changes. Carvings keep their indices (saves hold `text: 7`); the index
  resolves through the table.
- **Chapters**: ten, one a band, plus *Odd carvings*, *The endless dark*, *The people* (ghosts) and *The village*.
  `CM.CHAPTERS` names them and gives each an epigraph.
- **The codex** (J, a second tab beside the journal): the chapters, each line in its place, the unread as a blank
  ruled line with the floor it is on; a line that has been corrected by a deeper one shows the lie struck through
  with the truth under it (`contradicts: "carving.catacombs.3"` on the deeper entry). Completion counts a chapter.
- **Variant tellings**: each carving slot gets two or three tellings of the same fact in different hands (a
  priest's, a child's, a dwarf's); `CM.furnish` picks by `hash(seed:telling:floor)`. Same facts, so the codex counts
  the slot read whichever telling was found. The journal keeps the one the party read.
- **Tests**: every chapter's lines are reachable on their floors for fifty seeds (a carving on a square `CM.solvable`
  reaches); every `contradicts` names a real key; no key is unused; the word count is printed (the budget above).
- **Bot**: the bot reads every carving it passes and talks to every ghost (it already walks to them).

Size: M. Nothing the player sees changes except the codex; everything after depends on it.

## Phase 1 - The people of Caer Duin - v3.2 - DONE

The six ghosts become characters with arcs across the dungeon.

- **Recurring ghosts**: each of the six has three appearances at three depths (Hal at 3, 9 and 23; Brother Cael at
  2, 17 and 41 ...), placed by hash on floors without a guardian. Each appearance is a scene: what they say depends
  on what the party has read (`game.story`: a set of keys, saved) and on whether they met before this run. The
  third meeting of each is a request (the three kinds exist; add **bell** - ring the last bell, a thing found on
  floor 4 - and **witness** - tell the ghost what a deeper carving says about them).
- **Six more ghosts** for the Deep, named in the carvings already: the fishwife who saw the sluices; the dwarf who
  wrote GO ROUND; the smith who would not stop; a courtier who still sits; the physician himself (floor 19, who
  burned his own notes); the stranger who was not a stranger (floor 38).
- **Your own dead**: on a seed where a party fell before, the remains already lie there. Now the fallen hero with
  the most levels stands as a ghost beside them, with the memorial's name and calling, and says one of a dozen
  lines written for a hero who died here ("I had the stairs in sight.") plus the epitaph the player gave them
  (Phase 6). Their request is always *bones*: lay them to rest, and a candle is lit for free at the shrine.
- **The hermit, chronicler**: paid in stories still, but now he *tells them back*: give him a full chapter and he
  reads its epigraph and the truth under it (a long scene, skippable), and he marks the chapter complete in the
  codex even if one telling was missed. He also sells a direction to the floor's carving if none is found.
- **The lost adventurer** gets a name from the memorial when one fits (a hero of yours who fell on a shallower
  floor of any seed, "found alive after all"), else a generated one; they carry one line of what they saw below.
- **Tests**: each ghost's three floors are distinct and in order; a ghost's second meeting knows the first (story
  flags round-trip through a save and a replay); the bot completes a *bell* request.

Size: L (mostly writing: ~6,000 words).

## Phase 2 - The guardians speak - v3.3 - DONE

A parley before every lair, and a way through for those who read.

- **The approach**: entering a lair's set piece plays a scene (title card and two or three lines) and the guardian
  speaks first. Three choices, logged: **Fight**; **Speak** (a line of dialogue each, three exchanges, which can
  end in a fight on better terms - the guardian's first form skipped, or an escort gone - or in a worse one if the
  party says the wrong thing); and a **lore-gated** option that appears only if `game.story` holds the key the
  guardian needs. The Drowned Knight: tell him the water was let in, and by whom (a Drowned Town carving) - he
  kneels, and the way down opens without a fight, and his shield is on the floor. The Forge-Warden: the dwarves'
  word for the door (a Dwarven Halls carving). The Queen: the fishwife's testimony. The Mind: the dwarf's warning,
  sung back. The Tyrant: GO ROUND. The Forge Master: the smith's name. The Patriarch: a holy thing, or nothing. The
  Rat King wants only food. The Root wants nothing you have, yet.
- A guardian passed by speech is **not slain**: no trophy, no XP, half the gold, no achievement - but a line in the
  codex and a title, *the Soft-Spoken*, for passing three. Renown counts it as a guardian met.
- **After**: the lair changes once the guardian is gone (the water drains from the Drowned Hall, the embers go out
  in the Forge, the Queen's court sits down): `changeBehind` already does this for secret stairs. The guardian's
  own carving (the `g:` lines) rewrites to the past tense.
- **Death speeches**: a line each at the second form's end; a different line if the party spoke first.
- **The Lich King's warning** on floor 20 grows to a scene; the fight itself waits for Phase 3.
- **Tests**: each gate's key is a real lore key on a shallower floor than the lair (so a first run can meet it,
  not just an Awakened one, except where the canon says otherwise - the Queen's key is below her, by design: she
  can be spoken to only by a party that has been to the bottom and come back); the bot speaks when it holds the
  key and the sim reports crowns with and without.

Size: M (writing: ~4,000 words; code: the parley dialog reuses the event dialog).

## Phase 3 - The court of the Lich King - v3.4 - DONE

Floors 16-20 become a place with people in it, and the heart becomes a hunt.

- **The court**: seated dead on the palace floors (a new thing, `courtier`, placed by hash in rooms: the throne
  template gets two), who speak if the party stands before them and uses: the chancellor, the master mason, a
  lady-in-waiting, the physician (also a ghost in Phase 1: here he is a body, and knows less), the captain's
  widow. Each knows one true thing about where the heart is kept.
- **The heart hunt**: the phylactery sits where it sat (saves hold it), but three **clues** on floors 16-19 point at
  it - a courtier's line, a carving, a page of the physician's notes in a chest - and finding all three marks it
  on the automap of floor 20 and adds a line to the journal. Without them, as now, the party searches.
- **The king's memory**: Mordeth remembers being Mordeth. If the party enters his throne room with the *Palace*
  chapter complete and the heart smashed, a fourth choice appears: **Remind him**. A scene of five exchanges - the
  queen's name, the bells, the twelfth year, the box, the heart - each needing a key the party has read, and
  failing on any gap into the ordinary fight. Succeed, and he ends himself: **the quiet ending**. The crown is
  taken; the Hall of Fame marks it (`entry.reminded`); the title is *the Merciful*; the sim counts it a crown. The
  Deep is still open below.
- **His court falls** either way: the courtiers' lines on the way back up (the party climbs through 19-16 to the
  surface in the ending's text, not in play) are written for the ending card.
- **Tests**: the three clues sit on three different floors and are reachable; `reminded` needs every key and fails
  on one missing; a replay reproduces the quiet ending; a v3.x save on floor 20 still has its phylactery.

Size: M.

## Phase 4 - The Root, and the three endings - v4.0

The bottom of the world becomes a choice, and Awakened becomes a consequence.

- **The approach to the Root** (floors 46-49): the carvings here are the Root's own voice, and it knows the party.
  It uses their names (the first time the game does), their dead ("you left one in the Ossuary"), their origins
  (Phase 6), their ledger ("this is your ninth descent"). The Awakened mode's own lines live here too.
- **Three endings at 50**, chosen after the Root's fight is won (or in place of it - see the third):
  1. **Wake it and end it** - what happens now. "Nothing is dreaming the king now."
  2. **Leave it to dream** - walk away with the crown. The village prospers (a renown bonus, and the merchant's
     prices fall for good), but the next run on any seed finds the king back on his throne, and the codex gains a
     chapter, *The dream, again*. This is what the Awakened mode has been: name it, and let it be chosen.
  3. **Give it the crown** - possible only with the *Root* chapter complete and the quiet ending (Phase 3) earned
     on some run before. The party does not fight it. The crown goes into the red stone, the Root dreams a
     different dream, and the ending card is a page of what Caer Duin might have been. The Hall of Fame marks
     `entry.dreamed`; the title is *the Dreamer*; a new mode opens, **the Other Dream**: the dungeon with the bands'
     names and carvings changed (the Drowned Town is a market; the Palace a hall with bells) and the guardians as
     they were in life - the same floors, re-skinned by a second lore table and the themes' colours. The monsters
     and the numbers are the Awakened ones; the writing is new.
- **Endless** gets the Root's voice too: beyond 50 the carvings count the party's own descents and name their dead.
- **Tests**: each ending logs and replays; the fame sorts the three equally (bottom is bottom); an Other Dream run
  is `floorPrint`-identical to its seed's ordinary run (only text and colour differ); a v3 save at floor 50 gets
  ending 1 by default.

Size: L (the Other Dream's table is ~4,000 words; the endings ~1,500). This is the phase that earns 4.0.

## Phase 5 - The village has people - v3.5 - DONE

The story's surface: where the codex lives, and where the next run is seeded.

- **Three villagers**, each in a building the player already has, each with a line a visit and a longer one when
  something has changed: the **chronicler** at the library (shows the codex; pays renown once for each chapter
  completed - 20, 40 for the Deep's; sells a *rumour* for the next run); the **priest** at the shrine (reads the
  memorial's names aloud, three a visit, with the epitaphs; lights the candles; tells the Patriarch's history in
  five parts as the shrine is built); the **keeper** at the guildhall (the trainers' stories; the retired heroes
  speak, one line each, written by calling and by how they came home).
- **Rumours**: a rumour is a hash-seeded promise for the next run on a chosen seed - "a ghost on the seventh floor
  wants its bones", "the sixth floor's carving is a child's" - which `furnish` honours by forcing the telling or
  the ghost. Costs renown; the bot buys one when it can.
- **The Book of Caer Duin**: the chronicler's second page is the player's own history - every crowned party in the
  Hall of Fame written as a chronicle entry in the carvings' voice ("In the year of the ninth descent, Elwyn the
  Knight and three came down and the king did not rise again"), generated from the ledger and the fame. And the
  dungeon writes it back: on floors 1-3 of any later run, by hash, a carving about a party of yours ("Here [name]
  the [calling] slew the Rat King with a chair" - the Aldous device, for your own).
- **The village's own lore**: a chapter, told by the buildings' levels - what the village was before the shaft
  (the Patriarch's order's first house), unlocked as renown is spent.
- **Tests**: a rumour forces the telling; the Book has one entry per crowned run and none for a fall; the shrine
  reads your names.

Size: M (writing: ~3,000 words).

## Phase 6 - Heroes with pasts - v3.6 - DONE

- **Origins** at creation (six: *of Caer Duin*, *dwarf-friend*, *from the east*, *of the Patriarch's order*, *of the
  lower town*, *nobody from nowhere*): one small mechanical touch each (a dwarf-friend reads the dwarves' marks as
  a direction; one of Caer Duin starts with a chapter's first line known; the order's are not cursed by the
  Patriarch's touch) and, more to the point, **lines**: an origin speaks at four or five walls that concern it ("My
  grandmother said the bells were taken down. She didn't say they were still here."), and the Root uses it.
- **Banter by situation**: `CM.BANTER` grows from four lines to forty, keyed by where (camp, after a guardian, at a
  carving, on a flooded floor, with a hero down) and by quirk pair; the bond's third tier gives two heroes a
  running joke that recurs. Still short: one line, at the camp or after a fight, never in one.
- **Epitaphs and last words**: a hero who falls for good says one line (by calling, origin and the floor's band);
  the memorial dialog asks the player for an epitaph (optional, 60 characters) that the ghost of Phase 1 and the
  priest of Phase 5 repeat.
- **The retired speak**: a trainer's line to every new hero of their calling, from how their own run ended.
- **Tests**: every origin has its lines on floors that exist; last words never repeat in one run; an epitaph
  round-trips through export and the ghost.

Size: M (writing: ~3,500 words).

## Phase 7 - The telling - v3.7

How the story is shown; no new words.

- **Reading a wall**: a reading view (the carving large, in the hand that wrote it - four hands as fonts drawn by
  code over the existing stone texture, a child's chalk, a dwarf's chisel, a priest's uncial, a scratch), revealed
  line by line at reading speed, Space to finish. Reduce motion shows it at once.
- **Chapter cards**: the band's title card gains the chapter's epigraph on the first floor of the band, and on the
  last the line that the next band will contradict.
- **The camp fire tells the day**: at every camp the heroes talk over what was read that band (two lines from the
  journal, in two voices, with the banter of Phase 6), so the codex is heard as well as read.
- **The ending as a page**: the ending card becomes an illuminated page: the chapters the party completed are its
  paragraphs, in order; the ones it missed are blank lines; the party's fate is the last paragraph. Saved as a PNG
  like the summary card.
- **Leitmotifs**: three short musical phrases (the bell, the queen's song, the Root's one note) that the music
  plays when their subject is read, spoken or approached - the queen's lair tune is her song; "do not let her sing"
  becomes something you hear.
- **Tests**: the reading view's hands render for every carving (a smoke test draws ten); the ending page lists
  exactly the chapters completed.

Size: M.

## Phase 8 - Around the story - v3.8 (and v4.0's wrap)

- **Achievements and titles**: *the Chronicler* (every chapter), *the Soft-Spoken* (three guardians passed by
  speech), *the Merciful*, *the Dreamer*, *the Witness* (every ghost's third meeting), *Bell-ringer*; a kit, *the
  Scholar's*, that starts with a chapter known and a tome.
- **Contracts** with story in them (ring the bell on Grim; pass the Drowned Knight by speech; lay your own dead to
  rest), from the week's seed.
- **The sim reads**: `tools/sim.js --story` reports chapters completed, guardians spoken past, endings reached, by
  difficulty - so the story's gates are measured like the fights are.
- **Text as data, finished for the story**: every word the player reads from 13-lore.js and 12-text.js; a
  `tools/words.js` prints the budget by chapter and finds strings still in the code.
- **Films** show the story choices as they were made (the film bar names the scene).
- README section, plan status, and the version.

Size: S-M.

---

## Order, size and dependencies

| Phase | Version | Size | Depends on | Notes |
|-------|---------|------|------------|-------|
| 0 The spine | 3.1 | M | - | Canon, the lore file, chapters, codex, variant tellings. Do first. |
| 1 The people | 3.2 | L | 0 | Ghost arcs, your own dead, the hermit's tellings. |
| 2 The guardians speak | 3.3 | M | 0, 1 (keys are read lines) | Parleys and lore gates. |
| 3 The court | 3.4 | M | 2 (the parley dialog) | The heart hunt; the quiet ending. |
| 5 The village has people | 3.5 | M | 0 | The codex's home; rumours; the Book. Can run before 3. |
| 6 Heroes with pasts | 3.6 | M | 1 (ghosts repeat epitaphs) | Origins, banter, last words. |
| 7 The telling | 3.7 | M | 0, 6 | Presentation only. |
| 8 Around the story | 3.8 | S-M | all | Titles, contracts, the sim, words as data. |
| 4 The Root and the endings | **4.0** | L | 3 (the quiet ending gates the third), 6 (the Root uses origins) | Last, so the Root knows everything the party is. |

Suggested sequence: **0 -> 1 -> 2 -> 3 -> 5 -> 6 -> 7 -> 8 -> 4**. The endings go last on purpose: the Root's
voice should be able to use every fact the earlier phases give it, and the Other Dream's table is the largest
single piece of writing, best done when the voice is settled.

## Risks

- **Consistency.** Eleven thousand words by nine phases will contradict themselves without the canon. `LORE.md` is
  written in Phase 0 and every later phase's text is checked against it before it ships (a reviewer's pass, not a
  test).
- **Volume on screen.** The game's strength is terseness. Rule: no scene over five exchanges, no line over two
  sentences, Space always skips, and the codex is where the long reading happens - by choice.
- **The frozen floors.** Every new thing on a floor goes through `CM.furnish` by hash, never through the
  generator; a test keeps the gen 1 and gen 2 fixtures byte-identical.
- **Saves and replays.** `game.story` (the keys read, the choices made) is new save state: schema 3, with a
  migration that derives it from the journal. Every choice is logged; the replay test suite gains a story run.
- **Endings and the Hall of Fame.** Three bottoms sort equal; `entry.reminded`, `entry.dreamed` are flags, not
  ranks. The Other Dream is a mode like Awakened, not a fourth difficulty.
- **The bot.** Each phase gives the bot its mechanic (read, speak, buy a rumour, choose an ending by a flag), or the
  sim's numbers quietly stop meaning anything.
- **Gates that lock out a first run.** Every lore gate's key must be readable above its lair except where the canon
  wants a return (the Queen). A test checks the depth of every key against its gate.

## Not in this plan, and why

- **Voice acting or recorded narration.** The game ships no sound files; the leitmotifs are code, like the rest.
- **A translation.** The door (12-text.js, 13-lore.js) is open after Phase 8; the words are English until someone
  walks through it.
- **New art for the court or the villagers.** Faces are drawn by code like the portraits; the Pixel theme's full tile
  set is on another machine and stays there.
- **A tenth band under the Root.** The Root is the bottom. The Other Dream re-reads the fifty floors instead.
