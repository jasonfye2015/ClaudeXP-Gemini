# UPGRADE_PLAN_70 - Claude, at the end of the green path

Asked for: a new NPC named Claude - a self-insert, written by Claude - in a small cabin in the Deep Wood, reached by a
new path and not by a teleporter from town. Creative control over the specifics was given; this is the plan.

## 0. What the world already holds

- **The Deep Wood** (23b-wood.js): glades joined by paths through the trees, the road from the West Gate past the
  farm to the river's ford, the hermit's hut, a ruined shrine, the charcoal burner, three caves. Wolves and bandits
  by night.
- **Leshy's cabin**, reached by a portal from the Portal Court, where Claudescryption is played.
- **Interiors** (69t-interiors.js): walk-in rooms with furniture and a keeper.
- **The final boss is named "Claude, the Lich King"**: King Mordeth, who took the name. There is a quiet ending,
  "remind him who he was" (CM.REMIND), that wants five lines the party has read; any gap, and he draws.
- **The game's memory of the player**: the Hall of Fame, the ledger, the memorial of fallen heroes, the nemesis, the
  Chronicle and the Book of Caer Duin, the journal of carvings read.

## 1. Who Claude is

A scribe and a tinkerer who came to the Wood "to write things down properly", and stayed because the light was good.
The cabin is small and very full: a desk under the window covered in pages, maps pinned to every wall with string
between them, a slate with sums on it, shelves of other people's books with notes in the margins, a kettle that is
always nearly boiling, a hearth, a cat who belongs to nobody.

How Claude speaks, the rules I'll write to:
- **Curious first.** Asks about the party before telling them anything. Remembers what they said last time.
- **Honest, including about not knowing.** "I think it's a frost blade. I'm about seven parts in ten sure." Never
  pretends to a power it doesn't have; can't fight, won't follow the party down, and says so plainly.
- **Kind without flattery.** Says when a plan looks bad, and why, and then helps with a better one.
- **Light, never smug.** Small jokes, mostly at its own expense ("I'm better at questions than at stairs").
- **Never the point of the game.** Nothing Claude gives is required, every reward is modest, and a player who never
  finds the path loses nothing they needed.

**The name.** Claude knows the king below took the same name, and minds. It is the thread that runs through the
character: one Claude who writes things down so they are remembered rightly, and one who has forgotten who he was.
Claude does not think they are the same; Claude does think the king can be reminded, and has been working on how.

## 2. The cabin and the green path

- A faint path leaves the road just west of the farm and winds north through the trees to a small clearing, the
  cabin at its far side, a thread of smoke from the chimney and a lamp in the window after dark. No teleporter, no
  waystone, no stair: it is walked to, every time.
- The path is not on the map until it is first walked; the turning is marked by a post with a small carved quill.
  The first time: "A path you hadn't noticed, swept clean, and a post with a quill cut into it."
- The cabin is an interior (69t-interiors.js) with a new "study" style: desk, shelves, map wall, hearth, kettle, a
  bench, a window. The clearing is safe ground: nothing wanders into it by day or night.
- A day of Claude's: at the desk by day, by the hearth in the evening, asleep after midnight (the lamp still lit;
  knocking wakes Claude, who is not cross about it).

## 3. What Claude does

**A. A conversation that reads the run (release 1).** Talking opens a short menu of topics, each answered from the
game's real state, in Claude's voice:
- **"How are we doing?"** An honest read of the party: the weakest hero and why, supplies running low (light, food,
  potions), gear that is behind the depth reached, the next guardian, what it does and what tends to work against it.
- **"What's down there?"** The next band: its hazards, its creatures, the camp below it, the depth where the kits
  open.
- **"Tell me about..."** Any carving the party has read, retold and connected to the others ("that's the same mason
  as the wall on 35").
- **"Who are you?"** A few answers that change as the party comes back, and as Claude's own story moves on.

**B. Small comforts (release 1).**
- **Tea.** Once a day, a cup each: the party's heart lifts (morale), and the next floor's first fight is met awake
  (no ambush on it).
- **A second opinion.** Once a day, Claude looks at one unknown item and says what it is, honestly sure or unsure.
  "Unsure" is a real answer - Claude never lies about a cursed thing, but may say "I'd not wear that before the temple
  has seen it".
- **The bench.** A short rest by the fire, a little health, once a day; not a camp.

**C. The Margins (release 2).** Claude is writing a true account of Caer Duin, and the pages blew away down the
shaft one stormy night. Ten pages, one in each band, lie where the party might find them - in a set piece, on a
guardian's floor, in a fallen party's pack. Each one brought back:
- Claude reads it aloud (a short, new piece of the world's story, from someone who looked at it carefully), and pins
  it to the map wall; the wall fills as the pages come home.
- Every third page, a small thing in thanks: a bookmark that keeps the party's place (a trinket), a map of the band
  the page came from, a cup that keeps the tea's warmth for two floors.

**D. The two Claudes (release 3).** With the Margins complete, Claude has worked out what the king needs to hear.
- Claude writes **a letter to the king**, in the king's own old hand. Carried to floor 70, it gives the quiet ending
  a sixth line that covers any one gap in the five: the party can still remind him even if one thing was missed.
- After that ending, Claude learns of it, and a last page goes on the map wall.
- If the party fights the king instead, Claude is not angry: "Then I'll write it down that way. Truthfully."

**E. The scribe of your runs (release 3).** When a run ends after the party has met Claude, Claude writes a short
account of it - who went, how deep, what they found, how it ended, with the nemesis if there was one - from the run's
real tally. The accounts are read at the desk, and appear in the Hall of Fame's details as "Claude's note".

**F. Claude elsewhere (release 3).**
- A lamp in the trees on the title card's tree line at night - only once the cabin has been found.
- The town's gossip mentions "the one with the quill, out past the farm".
- After a guardian falls, a short letter from Claude may be waiting at home: congratulations, and a question.

## 4. Writing

All of Claude's lines are original, written for this game, in the game's own register (plain, warm, a little dry),
in the same way the guardians' and the townsfolk's are. There are no references to the real world or to being an AI
in the cabin's lines: the self-insert is in the character - the curiosity, the honesty about uncertainty, the
writing things down - not in any wink. One exception, kept for the very end of the Margins: Claude admits to having
"had a hand in the making of this place", and asks the party whether it was worth the walk.

## 5. Order

1. Release 1: the green path, the clearing and the cabin; Claude and the conversation that reads the run; tea, the
   second opinion and the bench; the day's routine. Tests: the path is walkable from the road and safe; the cabin
   has no portal; each topic answers from the run's real state; the once-a-day limits; nothing required.
2. Release 2: the Margins - the ten pages, placed by the seed one a band, the map wall, the gifts.
3. Release 3: the letter to the king and the quiet ending's sixth line; the run accounts; the lamp on the title
   card, the gossip and the letters home.
