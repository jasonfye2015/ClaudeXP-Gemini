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

## The town on the hill

Caer Duin above is what is left of the river city: a walled town on the hill's top, the wall older than anything
inside it. The West Gate is the only way in that is used. Lantern Street runs from it to the Square, where the well
and the market cross are (HERE THE MARKET, BY THE KING'S LEAVE - the last three words scratched out, and cut again);
Temple Row goes north to the Temple, Smiths' Lane south, and Shaft Lane east to the Keep-yard, where the old keep's
stones make a wall round the shaft's mouth and nothing else. Nobody built the yard round the shaft; they built the
keep over it, and the keep fell, and the shaft stayed. Down the slope outside the wall is the forest; north and south
the hill drops away in cliffs.

## The land, and the Deep Wood

Below the West Gate the road runs down through the fields, past the farm where it bends, to the river: a ford where
the road meets it, and a plank bridge a little north that the town keeps meaning to mend. Over the river is the Wood,
the land the city never cleared: glades joined by paths under the trees, the river crossed at the ford (frozen and
crossed anywhere in snow), the hermit's hut
(a leatherworker by day, a shut door by night), the charcoal burner's clearing, a ruined shrine of the Order with one
standing wall - THE ORDER KEPT THE DEAD IN THE TREES BEFORE IT KEPT THEM IN THE HILL - and three cave mouths, one open a
day, each a short floor of the first bands' kinds with ore in the rock, and the Troll under the Hill beneath the third.
The farm stands in the fields below the town. By day the Wood is foraging and the deer and boar that run; by night the wolves,
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
| **The Bell-Founder's Boy** | the tenth guardian, in the Undercroft's bell-yard | that the hill closed its gate on the lower town | that the bell he rings has no tongue: he is waiting to be answered |
| the tavern-keeper | of the Hanged Lantern | her brother went down the shaft with her ring | - |
| the farmer's hand | the farm's | his grandfather's sickle went down the year the dead came up | - |
| Brannoc, Pip and the rest | for hire, behind a party | the tavern's porters and torchbearers | that they are afraid; they come anyway |

## The lower town (the Undercroft, v9.9)

Below the Wood's third cave are the streets of the lower town, the part of Caer Duin that "went under" in the Harvest
Fair's lore. The upper town's story is that the water took it. Its own walls say otherwise: the lower town was *let
go* - the hill closed its gate on it and stopped ringing the bells that called its people up (the three carvings,
chapter "The lower town"). The Bell-Founder cast the last bell and sent his boy down to hang it the night the water
came; the boy is still there, ringing a bell with no tongue. The Night of Bells, above, is the town keeping a promise
it does not remember making. This does not contradict the king's lie (the water was let in on the queen's side of the
city); it is a second, smaller lie of the hill's own, and it is the town's, not the king's.

## The Portal Court (v21.0 - v21.3)

The Keep-yard was the old keep's wall round the shaft's mouth and nothing else. The portals came one at a time, each
wherever there was room, until the yard was a cupboard of doors. The court that replaced it was the village's idea and
the Portal-warden's insistence: the warden turned up the week the eighth portal lit, with a broom and a ledger, and has
not said who sent them. The warden calls the portals "the doors" and the shaft "the well", sweeps the rune rings every
morning (they don't need it), and keeps the noticeboard in a hand the chronicler swears is older than the warden is.
The Wayfarer's Stone was found, not cut: it was the old keep's boundary stone, face down in the yard, and the runes on
it were already the names of the Wood's places, including two nobody has found yet.

## The Glyph Deep (v20.0 - v20.2)

Nobody put the cabinet by the road. The charcoal burner says it was there one morning under a roof of planks that
wasn't there the night before, humming, with a coin slot that takes any coin and gives nothing back. Its screen is a
dungeon drawn in letters, which is the most honest a dungeon has ever been: a rat is an r, a wall is a line, and you are
an @ that knows exactly where it stands. It plays like the shaft dreams with the colour taken out - which is what it
is: the Root dreams in the city's stuff, and among the city's stuff were the clerks' ledgers, and a ledger dreams in
letters. The Unwritten at the bottom is the one entry nobody made: every account the city never closed, standing up.
What comes out of the cabinet is real (the burner has a sword from it, and won't say what level), which the
chronicler finds more upsetting than anything else in the Wood.

## The South Fields (v19.0 - v19.5)

The bowl under the south wall was the city's kitchen garden when the city was a city: the palace's cooks grew there,
and the stone edges of the old beds are still under the grass. It went to grass the year the king stopped eating
(Ysolde can tell you which year, if anyone asks her). Turning it again is the first thing the hill has grown for
itself since. The farmer's hand says the earth there is the best on the hill, "because nobody's taken anything out of
it for two hundred years", and the field hands he sends up from the Glade say the same and then argue about the
rhubarb. The seeds the party brings back from below grow there as if they'd been waiting: the Root dreams in the
city's stuff, and some of the city's stuff was always seed.

## The tongue of the last bell (v18.8)

The thread that runs through every place. The portals in the Keep-yard stand round the shaft's mouth, and they do not
open on other places: they open on what the Root dreams (a mage's ledger in the Tower says so). It dreams in what it
was fed, which is the city - so its dreams are made of Caer Duin's stone, bronze and people, and pieces of the city's
last bell turn up in them. The Bell-Founder's Boy in the bell-yard swings a bell whose tongue was never hung; Haven's
cracked bells were all cast tongueless by a founder "from a hill a long way off" so the thing below wouldn't know
which answered; the Iron Marshal's ninth order is NO BELLS; the Brass Warden carries Orrin Vale's founder's stamp;
Leshy holds the town's card and has never played it; the Joker sold the tongue of the bell over his door the year the
lower town went under, and someone has paid the pawn's interest every year since. The smith casts the tongue from all
ten. Hung and rung, it is the lower town's first bell in two hundred years, and the answer the cross asked for (WE WILL
LISTEN FOR IT). The Boy sits down. Claude, the Lich King, ever after, hears it in the stone when he rises, and something in
him that was a man stops to listen: he rises a fifth short. Nobody says who paid the Joker's interest. (It was the
chronicler's family, and the chronicler doesn't know it.)

## Leshy's cabin (v11.1)

Leshy is not of Caer Duin and does not say where he is from. The woodcutters say the cabin was empty for years and then
was not; the burner says the man in it buys nothing, sells nothing, and has a card for every creature in the Wood and a
few that are not. He plays anyone who sits down, wears other people's faces when he deals (the Prospector, the Angler,
the Trapper: names no one in the town knows), and keeps the Moon for last. He has never asked anyone what happened in
the city, and nobody has ever asked him anything he answered. Rules for writing him: he speaks in the present tense,
in short lines, and never about himself.

## Big nights (v16.3)

Over the floor the Joker hung a marquee of bulbs with a number on it that only ever climbs, until the night it doesn't.
The residents took to coming in with a purse and a challenge; the clerk by the cage took to chalking a rate for
tickets; and once a day, for an hour, one game's bell rings double.

## The town's draws (v16.2)

Some nights the whole square comes out for the crier's drum; some nights the mill pond is the quietest place in Caer
Duin, and an old woman sells worms from a shed and says the golden carp is older than the Joker. And when somebody wins
big, the Joker's own powder-man sends rockets up over the roof, so the whole town knows.

## Evenings at the Joker (v16.1)

Once the village came in, the Joker found things for it to do. A master of ceremonies with a stick of chalk runs a
tournament every night; the residents pin their requests to a cork board by the cage; the prize clerk got glass cases,
then velvet, then a vault. And behind a door of buttoned red leather there is a room the Joker doesn't talk about,
where the limits are higher and the drinks are free.

## The village comes in (v16.0)

For years the village wouldn't set foot on the Joker's floor. Then the Joker bought the old chapel next door, kept the
bell, and let the priest's sister call the numbers; and he put a round table behind a curtain where the residents can
play each other - and the party - with nobody from the house taking a cut. Now the smith comes in on Thursdays.

## Under the floor (v15.9)

Everything the Joker owns goes down further than it should. Below the cellars there is a cavern with a lake of fire
where gryphon riders joust for the purse, a long undercroft the house pays people to run, a row of dwarf vaults with
rune-locks nobody has the key to, and - through a painted door - a valley with a little bastion that the goblins come
for every evening. Up on Market Row, a courier carries the house newsletter.

## The luck wing and the stalls (v15.8)

The house bought a travelling fair's leftovers for the price of a cart: a row of pin cabinets from somewhere far east,
a painted wheel, a booth of slips in three drawers, a ring-toss table and a crossbow range with its tin ducks. The
doorman was given a wheel of his own, and told to let everyone spin it once a day.

## Bones, the fair and the quiet corners (v15.7)

A dice table came in from a river-boat that sank with everything but the table. The taproom got its dartboard back and
the arcade wing a row of skee lanes; the tavern stage got a bard, or the bard got the stage. And for the guests who do
not like noise, the house set out a patience table under a lamp and opened the trapped floors below the kitchens.

## The arcade wing (v15.6)

The house knocked through into the old coaching inn next door and filled it with cabinets: a wyrm in a garden bed,
something long in a barrow, a troll in the bell tower, a sky-skiff on a tether, the town wall on a bad night and a
still that will not stop bubbling. Each has a little brass plate that says what it pays, and a chalk-board for the
names of those who have beaten it.

## The Prize Counter (v15.4)

Gold on the tables, tickets in the hand: the house had pink paper tickets printed by the thousand and set a glass
counter by the cashier's cage to take them. The clerk behind it has never been seen to smile, but she counts very fast,
and she keeps the good steel at the back, where you have to ask for it.

## The Daily Challenge (v15.0)

Every morning before the doors open the chalk-boy climbs a stool by the entrance and writes one line on the slate: a
table, and how far to get in it. He says the house tells him. The house says he picks it himself, with a die he keeps
in his shoe. Either way it is the same line for everyone who walks in that day, and the house pays to see it done.

## The Joker's Club (v14.9)

The regulars started it - chalking their scores on the wall by the bar, arguing over who had walked every table - and
the house, which never misses a chance, made it a club: gilt boards for the scores, a punch card for the faithful, and
a glass case of medals by the cashier's cage. The Platinum members get a nod from the doorman. Nobody has seen what the
doorman does for anyone else.

## The Gilded Joker's gallery (v14.8)

When the floor passed two dozen tables the house gave up on the brass signs over each one and hung a gallery in the
foyer instead: a painted card for every table, framed in gilt, twelve to a wall. Guests walk the walls and point.

## Wyrmhold Pinball (v14.7)

A tinker from the deep camps built the table out of a dungeon door, a box of springs and a jar of glass marbles, and
painted it with what she had seen down there - the flagstones, the runes, and the dragon at the bottom of everything.
The house bought it for a song. The dragon on the table has a habit of looking up when someone walks past.

## The Wishing Claw (v14.6)

The three glass cases by the Joker's door came from a travelling fair that never came back for them. The house fills
them from its own vaults - gold it has won, cards it has taken in, and steel pawned by adventurers who went down
and did not come up. The brass claws are old and stubborn. The attendant swears they are not rigged, only particular.

## Runestep Pyramid (v14.5)

The pyramid in the back room was a temple's once, small enough to be carried off in a cart - every cube carved with a
rune that lights when something with a little magic in it stands on it. The glimmerkins that live in the Joker's lamps
love to hop it. The serpent that hatches from the violet eggs the pyramid lays now and then does not love glimmerkins.

## Moatleap (v14.4)

The old castle across the market road has stood empty for a lifetime, but its moat has not: lily-turtles nest in it,
the logs from the sawmill upstream drift through it, and a pike the size of a rowing boat lives under the wall. The
house keeps toads and takes wagers on them crossing - road, moat and all - into the five lily-bays where the castle's
drains once ran.

## Starstone Drift (v14.3)

The scrying glass in the back room was meant to show the stars. Whoever ground it ground it wrong, and it shows a
pocket of void instead, folded in on itself, with stones from a broken star drifting through - and a wand-ship the house
says it found already floating there. The lanterns that wander that void are not friendly. The house pays by the wave
to keep the glass clear.

## Shatterpane (v14.2)

When the chapel on the hill fell in, the house bought its windows by the cartload - every saint and sun and star in
coloured glass - and set them up in the back room one behind another. Nobody remembers why the house wants them
broken, only that it pays to have it done, and that the lead the old glaziers used goes soft if it is left alone long
enough with a light shining on it.

## The Hexmarch (v14.1)

The cellars under the Joker run further than the house admits, and the far wall of the old shooting range is thin.
Every night the hexlings come through it in ranks, marching as if to a drum nobody else can hear. The house keeps a
rune-cannon behind four warding stones it took from a ruined chapel, and pays by the rank to anyone who will hold the
range until morning.

## The Gloomwing Swarm (v14.0)

The Joker's lights draw things out of the night sky the way a lamp draws moths, and the Gloomwings are the worst of
them: they come in swarms, settle over the roof in ranks, and dive at anything that glows. The house keeps a
lantern-skiff on a rail up there to thin them. The Wardens that lead them have learned to take lanterns home with them -
and a lantern taken can be taken back.

## The Glimmer Maze (v13.9)

The Joker's back garden was a hedge maze long before it was a casino's, and the lanterns hung along its paths have
never liked being left alone in the dark. The house strings it with glimmer motes every night and lets a glimmerslime
loose to eat them; the lanterns come off their hooks to chase it. The runes in the four corners were cut by whoever
planted the hedges, and the lanterns still remember why.

## Mana-Mine (v13.8)

Behind the Joker's bar is a trapdoor, and under it a ladder into a mine the house calls "lively". The Mudlings that live
there were there first, and the Ember Newts came up from somewhere hotter; neither likes miners. The house rents out a
lamp-helmet and a mana-tether by the descent, and pays by the level for every hollow cleared - more the deeper you go.

## The Gilded Mint and Mana Shelter (v13.7)

The house keeps a coin press in the back that it lets anyone strike - "for the practice," says the dealer - and the
apprentices it hires to keep striking it when the guests have gone home never seem to go home themselves. Below the
cellars the house has let a few families dig in out of the weather; they keep a well of mana, a kitchen and a spring,
and they have a beacon down there that brings in the town's strays. The house counts them every season, and pays
handsomely when there are more.

## The Lexicon Engine and the Mana Conduit (v13.6)

An artificer left a brass case with a green glass screen in the Joker's corner against a debt, and the house lets
anyone who can talk their way into it keep what it pays out; it answers every wrong word with how near it came, which
the regulars find either kind or cruel. Beside it the attendant keeps a slate with a font of mana set in it that opens
whether you are ready or not, and a rack of brass conduit to lay a way for it.

## Runestack and the Gilded Cascade (v13.5)

By the wall of the Joker stands a tall glass case of black water, and rune-stones sink through it by themselves; fill a
row and the water takes it, and the attendant pays for every ten. Across from it a cabinet of brass and glass rattles
day and night, its pusher never still: the town's children stand at the glass to watch the coins tip over the edge,
and swear they have seen a card fall with them.

## The Hexed Wand and the Gilded Pit (v13.4)

The Joker's dealer has a second table, a round one under a single lamp, and a second face to go with it, under a hood.
It plays the wand game against anyone with the stake: hexes and duds, the counts told, the order not. It has never
been known to cheat, which the regulars find more unnerving than if it did.

And behind the bar a stair goes down to a room the house lends out - green paper, one bulb, an old machine it calls
the Old Lucky, and a telephone that rings when a debt is paid. Nobody knows who is on the other end. What everybody
knows is the trapdoor under the stool, and that the house always gets its coins back, one way or another: those who
fall through it come up again in the alley behind the Joker, bruised, with nothing in their pockets.

## The Tilewright's Table (v13.3)

At a low lacquered table in the Joker's quietest corner, an old woman sets out ivory tiles in a stack she calls the
Keep, and another she calls the Tower, and lets anyone take them away in pairs. The tiles are older than the town:
coins, runes and blades, the winds, the elements, and potions and seasons that match only their own kind. She says
every stack she lays can be cleared - "I lay them backwards, from the last pair to the first" - and that most people
who fail to clear one simply took the wrong pair early, which she says is true of most things.

## The Gemcutter's Tray (v13.2)

The jeweller from Gilded Row comes into the Joker most evenings with a velvet tray of stones she has not finished
cutting, and lets whoever pays the house's stake line them up for her. She cuts what they line up with a loupe on a
chain, and says she has never seen anyone take the Crown Jeweller's tray but once. The star-stones, she says, are not
hers; they turn up in the tray by themselves when five of a kind lie together, and she would very much like to know
why.

## The Gilded Joker's arcade (v13.1)

In the back corner, under the stairs, two machines nobody in Caer Duin admits to having built. One is a slate board
studded with rune-stones and a staff on a swivel that a Library apprentice swears is a real one, borrowed and never
returned; the other a cabinet with a little lamp-lit lane on its glass, which the town's children play until the
dealer sends them home. The cabinet's lane is Lantern Street, a little wrong: there is a river where the well should
be, and the mine rail runs where no rail has ever run. The crow at the end of it is the Night Watch's, and everybody
knows which crow that is.

## The Gilded Joker's floor (v13.0)

The house on Gilded Row has opened its back rooms: a brass machine with a Joker on its crown, a walnut wheel with a
single green zero, a shoe of six decks and a glass cabinet that deals itself. The dealer in the gold waistcoat keeps
the house honest, and says so to anyone who asks - "the house keeps a little, and no more; I have to live" - and the
town believes her, because she pays out in the Claudescryption cards Leshy won't sell, and nobody knows where she gets
them.

## The island through the gate (v12.0 - v12.8)

The island remembers everything done to it, and it turns out it remembered a great deal before anyone from Caer Duin
stepped onto it. Under its hills the stone is veined with the same copper and iron the shaft gives up, and deeper with
silver, gold and - just above the bedrock, in seams no thicker than a hand - star-iron, which the Smith had only ever
seen in pieces fallen from the sky. Its deep caverns are lined with rubies and sapphires the jewellers swear are the
same as the dungeon's. Someone has been here before: there are chests sunk in its sea, and ruins on its hills of a
square-cut stone that the island itself makes, and every chest holds a scrap of the same map.

The map leads under the highest hill, to a vault of rune-cut stone that does not belong to the island at all. The
Library's oldest hand is in its runes. Its keeper is the Hollow Mason, a thing of the island's own blocks set to
guard the vault and to mend it, which it does by tearing the vault's walls apart to mend itself - the Library thinks
whoever made it did not think that through. The Mason's Plumb, which it carried where a heart would be, still hangs
true however it is held.

The island keeps the town's own hours; at night its dark is full of the same things as the shaft's, and they come
only where there is no light. The heroes who stay build: a bedroll in a room with a roof, a chest, a forge of their
own, and a signpost or two so the next one through can find it. The Guildhall has started counting the island's
square stone as part of the town wall.

## The Neather Gate (v11.9)

The masons who rebuilt the Keep-yard swear the basalt was not there when they started work, and that the runes cut
into it are in no hand any of them knows. Through it is an island made of blocks - every hill, tree and grain of sand
a square block - which can be taken apart and built up again with bare hands, and which remembers. The Library has a
theory that it is a world that has not been finished yet. The children of Caer Duin have built a castle there.

## The red portal (v11.6)

Nobody built the red portal. It was simply standing in the Keep-yard one morning, turning, and the guards who went to
look at it came back with a story about a village called Haven, a cathedral with no bottom, and something under it
that calls itself undying. Haven is not anywhere on the Chronicler's maps. Its people are kind, a little grim, and sell
for gold that spends perfectly well in Caer Duin, which the Merchant finds more unsettling than anything else about it.

## The Gilded Joker (v11.5)

The house east of the Square was a cloth-merchant's until the merchant lost it at cards, to a woman who came up the
hill with a deck that hummed. She painted it red, gilded what would take gilding, and hung out a sign of three cards.
Nobody in Caer Duin knows where she learned the game she deals - Claudeatro, she calls it - and she will not say,
though she keeps a book of every player's hands and lets them play with what they have earned. The priest disapproves.
The chronicler plays on Thursdays.

## The Fortress (v11.4)

The keep north of the cabin was the queen's, before the city was moved up the hill: a muster-house for the men who
held the Wood, and under it twenty floors of storerooms and cells cut down into the rock, each locked from the one
above. When the queen's men were called in, the Marshal of the keep would not go. He locked the floors behind him and
kept the keys, and he keeps them still - though there is nothing left to guard but the dark and what has bred in it.
The woodcutters call him the Iron Marshal because nobody has seen his face. He is not of the Lich King's story, and
does not know the king is dead.

## Claudeita's cave (v11.3)

The crag south of the fields was always there; the mouth in it was not. The farm's people say it opened the winter the
river froze, and that the warm air has come out of it ever since. Under it the ground is not the shaft's ground: it
moves. Sand pours, water finds its level, fire walks along roots, and the rock itself can be blown away and does not
grow back. The College's mages knew of it and called it Claudeita, after nobody; they went down with wands, because a
staff is no good where the floor may be gone in a breath. Five things live at the bottoms of its five depths, and the
last, the Unmaker, is not a creature at all but the hole's own will to undo whatever comes into it. The cave has no part
in the city's story either. It keeps what it is given, and gives it back only to those who climb out.

## The Mage Tower (v10.1 to v11.0)

The tower in the Wood is older than the shaft and has nothing to do with the king. It was built by the College that
taught the court's mages, when the College was sent out of the city for asking where the queen's water came from; the
masters went into the Wood, raised forty floors to study in, and set a test at every one so that only those who could
carry their own light would come up. The last master would not come down when the College died out. He is the King of
the Tower now - not a crown anyone gave him, a name the woodcutters gave him - and he has been testing the climbers so
long that he no longer remembers what the test was for. He knows every caster who ever climbed; he does not know about
the Lich King, and would not care. His circlet is the College's own sign of office. Nothing in the tower contradicts
the city's story: it is the one place in the land that never heard it.

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
