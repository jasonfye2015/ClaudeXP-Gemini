# The canon of Caer Duin

The writer's bible for Claude and Magic. Not shipped in the game. Every line of story in `src/js/13-lore.js` is
written from these facts, and a line that contradicts them is a bug, unless it is one of the lies listed below -
and then it is a lie on purpose, with the truth marked deeper down.

The voice: dry, short, a knife in the last clause. Nothing is explained twice. The walls were carved by people who
had little time and less stone; the ghosts have had a long time to think and say less than they know.

---

## The shape of it

Caer Duin was a river city built on a hill over a shaft the hill was never asked about. The shaft is the Root's.
Everything that happened to the city happened because the Root dreams, and what it dreams it wants fed. The king
heard it and called it a stranger's box. The Patriarch heard it a thousand years before and called it a god. The
dwarves heard it and called it the note the world made when it was struck, and left.

The player goes down through the city's history in reverse: the recent dead on top, the oldest thing at the bottom.
The upper carvings were cut by people who believed what they were told; the lower ones by people who saw. So the
upper carvings **lie** - not from malice, from distance - and the lower ones correct them. The codex shows the lie
struck through once the truth is read.

## The Deep Wood

West of the town, through the gate at the end of the main lane, the Wood is the land the city never cleared: glades
joined by paths under the trees, a river crossed at one ford (frozen and crossed anywhere in snow), the hermit's hut
(a leatherworker by day, a shut door by night), the charcoal burner's clearing, a ruined shrine of the Order with one
standing wall - THE ORDER KEPT THE DEAD IN THE TREES BEFORE IT KEPT THEM IN THE HILL - and three cave mouths, one open a
day, each a short floor of the first bands' kinds with ore in the rock, and the Troll under the Hill beneath the third.
The farm stands in the First Glade. By day the Wood is foraging and the deer and boar that run; by night the wolves,
the bear and the bandits come to the party, and under a full moon a wolf that is more. The Wood gives no renown: hides,
meat, honey, deadwood and the night's danger. It is the Root's land as much as the hill is; the shrine says so.

## The calendar

The town keeps a year of twelve festivals, one a month, in the week around the fifteenth (the game reads the real
date, or a season pinned in Settings; `CM.FESTIVALS` in `src/js/24b-calendar.js`). Four are the hill's own; the
rest the city's, kept after the city. Each has its line, said at the well.

| Month | Season | Festival | What it does | The line |
|-------|--------|----------|--------------|----------|
| January | winter | Midwinter | the hearth gives two rests; the king's court sits a floor higher | The longest night. The king's court sat late, they say, and sits later. |
| February | winter | the Sexton's Day | a candle at the memorial costs no renown | The sexton buried the city's dead for forty years and asked no coin of the poor. |
| March | spring | the Sowing | seed at half price | What goes into the ground in the Sowing comes up. |
| April | spring | the Dwarves' Letter | picks whetted free, and sold at half | "We are well. Do not come." The town keeps the day it came. |
| May | spring | the Greening (the hill's) | the Wood's nodes give one more | The first week the Wood is green to the top. |
| June | summer | Midsummer | the round free; the townsfolk out at night | The shortest night, and nobody sleeps through it. |
| July | summer | the Forge Fire (the hill's) | the smith's gold at half | The week the forge is never let go out. |
| August | summer | the Reaping (the hill's) | the farm grows two stages a dawn | Everyone cuts, even the chronicler. |
| September | autumn | the Harvest Fair | market day all week; the farm yields double | The fair came up from the lower town once a year, and stayed. |
| October | autumn | the Feast of the Dead | the names read at the well; a candle free; the priests gentle | The names are read at the well, oldest first. |
| November | autumn | the Night of Bells | the boy hears one; gossip free; locks a tenth easier | One night a year the whole town listens anyway. |
| December | winter | the Wassail (the hill's) | the round sets the heart to full, with beer | The year goes out singing. |

The seasons set the day's length (summer's night falls at ten, winter's at six), the weather's odds (spring rain,
autumn mist, winter snow), the Wood's gifts (summer's honey and berries), the farm (nothing grows in winter) and the
dungeon's edges (autumn's quick tide in the Drowned Town; winter's frost a tenth harder near the surface; winter
dailies carry Gloom more often, summer dailies Swift).

## The timeline

| When | What | Who knows |
|------|------|-----------|
| long ago | The Patriarch's order keeps the dead of the hill people in the Ossuary, "before there was a king". The Patriarch learns from the red stone below how a heart may be kept apart, and does it to himself. He is the first lich. | the Ossuary carvings; the Patriarch himself |
| long ago | The dwarves dig down from the Dwarven Halls into the Crystal Caverns and the Foundry below, find the Root at the bottom, name the place *the root* in their oldest word, and seal what they find. Later the crystal begins to mine them. They abandon the deep halls for that, not for the king - and never tell him why. | the dwarves' marks (floors 11-15, 31-35) |
| year 0 | Mordeth is crowned king of Caer Duin. A good king, by the carvings; the catacombs say he wept for each of the first dead. | floor 1 |
| year 11 | The queen (**Aelith**, named only below) is drowned in her barge on the lower town's water. The carvings above say she died of the plague. She was held under; the Root's voice through Mordeth's own hands, though he does not know it yet. Mordeth shuts the gates and has the bells taken down. | floors 3, 24; Brother Cael; Mother Ennis |
| year 12 | The plague comes up the river. The priests say it will pass. It does not. The king sends for every book on death and every man who claims to have come back from it. He stops eating. | floors 2, 4; Ysolde |
| year 12 | A man of Caer Duin, a foundryman named **Orrin Vale**, comes to the king with a box. The carvings call him a stranger from the east. The box was made in the Foundry of a metal that can hold a heart apart; it is empty; the king keeps it by his bed and listens to it. What he hears is the Root. | floors 6, 18, 36-40; the stranger's ghost |
| year 12 | The king stops sleeping and says he no longer needs to. The court physician, **Master Hollis**, writes it down and begins to believe him. | floor 7; the physician |
| year 13 | The lower town drowns in a night, doors still barred. The carvings say the water rose. It was let in: the sluices were opened on the king's order, to feed the shaft. A fishwife, **Marguerite**, saw who opened them. The captain of the lower watch, **Captain Aldred**, stands in the water to the chest and will not leave his post. | floors 5, 22, 23; Hal; the Drowned Knight |
| year 13 | The dwarves' last letter asks why the king's coin is cold. They seal their doors from the inside. The seals hold a year. | floors 8, 11 |
| year 14 | Hollis's notes are burned, by him. One page survives: *the heart may be kept apart, and the body need not know.* He learned the way of it from what the Patriarch did first. | floors 10, 43 |
| year 14 | The king's orders come in a hand not quite his. The guard turns back at the palace gate. | floor 9 |
| year 15 | The dwarves' doors open and nothing comes out. The deep halls are empty - of dwarves. The Forge-Warden they left at their door still keeps it. | floor 11; the Forge-Warden |
| year 15 | The palace is built in a year by hands that do not tire. The masons' graves are its foundations. The forges of the deep halls are relit for one work: the box. The smiths who did the work are the Foundry's floor. | floors 16, 36-38 |
| year 16 | The king's heart is put in the box, in the Foundry, and the box is carried up by Orrin Vale. The king keeps the court. They sit where they sat. He asks for the last captain of the guard by name. | floors 14, 17, 18, 40 |
| year 16 | The child's letters: MOTHER SAYS THE KING IS STILL OUR KING. MOTHER SAYS NOT TO LOOK AT HIM. Mother Ennis looked. | floor 12; Mother Ennis |
| year 16 | Tamsin stops counting. | floor 2 (the tally marks); Tamsin |
| since | The thing that wears the crown remembers being Mordeth. That is the worst of it. He has waited so long he has forgotten what for. | floors 15, 20 |
| now | The player's parties come down. Each is a year, in the Root's reckoning. | the ledger |

## The people

| Name | Who | What they know | What they lie about or don't say |
|------|-----|----------------|----------------------------------|
| **King Mordeth** | the Lich King | everything, and remembers being a man | that it was his hands on the sluice and on the queen |
| **Queen Aelith** | the Drowned Queen | who held her under | nothing: she sings it, and the drowned stand when she stands |
| **Master Hollis** | the court physician; a body in the court (19) and a ghost | the heart kept apart; that he burned his own notes | that he kept one page on purpose, for whoever came |
| **Captain Aldred** | the Drowned Knight; captain of the lower watch | that the water was let in | he does not know by whom; tell him, and he kneels |
| **Orrin Vale** | the "stranger from the east"; a foundryman | the box; that the Root spoke through it | that he is from Caer Duin; his ghost on 38 says so at last |
| **Marguerite** | fishwife of the lower town | WE SAW WHO OPENED THEM | - |
| **The Patriarch** | the first lich; keeper of the Ossuary | how a heart is kept apart; that the Root taught him | that he taught the king on purpose, by letting Hollis find his chapel |
| **The Forge-Warden** | the dwarves' door-keeper | the dwarves' word for the door | that the dwarves are not coming back |
| **The Mind** | what grew on the dead in the shaft | what it was fed | - |
| **The Tyrant** | the crystal that took the dwarves' shapes | the one note | - |
| **The Forge Master** | the master of the relit forges; did not stop when the smiths died | the box's making | it is not clear it noticed anything |
| **The Root** | the dreamer at the bottom | all of it; it dreamed it | - |
| Hal | of the lower watch | the captain stood in the water | that they left him |
| Ysolde | the king's cook | the king stopped eating in the twelfth year | - |
| Brother Cael | a priest | rang the last bell himself, the night the queen died | - |
| Tamsin | kept the tally | counted the dead for the king | - |
| Aldous the Lesser | slew a troll with a chair | the troll was already wounded | - |
| Mother Ennis | the child's mother | looked at the king | what she saw |
| the child | wrote on floor 12 | - | - |

## The lies, and where the truth is

| The lie (upper) | Floor | The truth (lower) | Floor |
|-----------------|-------|-------------------|-------|
| When the queen died (of the plague, by implication) | 3 | She did not die of the plague. The water knows who held her under. | 24 |
| The water rose and never fell | 5 | The water was let in. | 22 |
| A stranger came from the east with a box | 6 | He was not a stranger from the east. He was from here. | 40 |
| The physician's page: the heart may be kept apart (his discovery) | 10 | He showed the king. He had done it first, long ago. | 43 |
| The deep halls: *they did not leave them* (the king's doing, by implication) | 13 | The deep halls were abandoned for the crystal, not for the king. | 32 |
| The king listened to a stranger's box | 18 | He listened to this. | 48 |

## The bands, and what each is for

1. **The Catacombs** (1-5): the good king and the first dead; the plague; the queen; the bells. Grief.
2. **The Flooded Vaults** (6-10): the drowning; the box; the king stops sleeping; the physician's page. Dread.
3. **The Dwarven Halls** (11-15): the dwarves seal their doors; the child's letters; the last captain; *remembers being Mordeth*. Horror, quietly.
4. **The Lich King's Palace** (16-20): the court that does not breathe; the box now empty; the heart apart. The confrontation.
5. **The Drowned Town** (21-25): the water was let in; who opened the sluices; the queen's barge; the queen. The first truth.
6. **The Fungal Deep** (26-30): the dead put down a shaft; something learned on them. What the city fed.
7. **The Crystal Caverns** (31-35): why the dwarves really left. The hill's own hunger, before the king.
8. **The Foundry** (36-40): the box made; the smiths; the stranger who was from here. The mechanism.
9. **The Ossuary** (41-45): the Patriarch did it first. The precedent.
10. **The Root of the World** (46-50): it dreamed it all. The cause.

The Deep says the truth plainly because no one down there had anyone left to protect.

## The Root

It is not evil. It is hungry, and it dreams, and what it dreams happens above it, slowly, over centuries. It dreamed
a king who would feed it, and the king fed it: the lower town, the dwarves, the court. It knows the player's parties
by their descents and counts them as years. It can be woken and ended (the stone goes still; nothing dreams the
king); it can be left to dream (the king returns - this is the Awakened mode: *the Root remembers you*); and, in the
fifth update's last phase, it can be given the crown and dream otherwise (*the Other Dream*: the Caer Duin that
might have been).

## Rules for writing more

- Facts come from the tables above. New facts are added here first.
- An upper lie is only a lie if a lower line corrects it, and the deeper line carries `contradicts`.
- Two tellings of a slot say the same fact in a different hand: a priest's, a child's, a dwarf's, a soldier's, a
  scratch. The riddles ask about the facts, so a telling never drops the fact the riddle needs.
- Names appear below the floor where the person is first mentioned without one. Aelith is named on 24, not 3.
- Nothing the Root says above floor 46 is in its own voice. Below 46 everything is.
- No line over two sentences. No scene over five exchanges. Space always skips.
