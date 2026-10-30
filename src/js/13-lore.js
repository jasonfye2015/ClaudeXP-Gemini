"use strict";
// The story, as data: every line of lore keyed, in chapters, so the codex can show what has been read and what has
// not, a translation is one file set over this one, and a riddle or a ghost can point at a line by name.
//
//   CM.LORE_TEXT["carving.vaults.1"]  ->  { text, tellings, chapter, order, floor, contradicts }
//   CM.loreText(featureText, seed)     ->  the carving's words (the telling the seed chose)
//   CM.loreKey(featureText)            ->  its key
//   CM.codex(game)                     ->  the chapters, line by line, read or blank
//
// A carving's value on a floor stays what the generators write (a floor index, a negative odd-carving index, "g:<guardian>",
// "e:<n>"); the key is read through it. The facts come from LORE.md; a telling says the same fact in another hand.
// The lengths of CM.LORE_EXTRA and CM.LORE_ENDLESS are fixed: the generators take dice and hashes modulo them.
CM.CHAPTERS = {
  catacombs: { name: "The Catacombs", band: 0, epigraph: "Here lie the first dead of Caer Duin. The king wept for each of them." },
  vaults: { name: "The Flooded Vaults", band: 1, epigraph: "The water rose in a night and never fell, the carvings say. The carvings say." },
  halls: { name: "The Dwarven Halls", band: 2, epigraph: "The dwarves sealed their doors from the inside. The seals held a year." },
  palace: { name: "The Lich King's Palace", band: 3, epigraph: "He keeps the court. They sit where they sat." },
  drowned: { name: "The Drowned Town", band: 4, epigraph: "Here the carvings stop agreeing with the ones above." },
  fungal: { name: "The Fungal Deep", band: 5, epigraph: "Nothing was buried. The dead were put down a shaft, and the shaft was not empty." },
  crystal: { name: "The Crystal Caverns", band: 6, epigraph: "The dwarves left the deep halls for this, not for the king." },
  foundry: { name: "The Foundry", band: 7, epigraph: "Iron was not enough for him." },
  ossuary: { name: "The Ossuary", band: 8, epigraph: "The Patriarch kept the dead before there was a king. The king only learned." },
  root: { name: "The Root of the World", band: 9, epigraph: "Everything above is its dream." },
  odd: { name: "Odd carvings", epigraph: "Not everyone who had a chisel had a message." },
  endless: { name: "The endless dark", epigraph: "There is no floor below this one. You are standing on it." },
  people: { name: "The people", epigraph: "What the dead said, when they had what they wanted." },
};
CM.LORE_TEXT = {};
const L = (key, chapter, order, text, more = {}) => { CM.LORE_TEXT[key] = Object.assign({ key, chapter, order, text, tellings: [text] }, more); if (more.alt) { CM.LORE_TEXT[key].tellings = [text].concat(more.alt); delete CM.LORE_TEXT[key].alt; } };
// ---- the fifty carvings, one a floor, five a band; `contradicts` marks a lie above that this line corrects ----
// catacombs: floors 1-5
L("carving.catacombs.1", "catacombs", 1, "Here lie the first dead of Caer Duin. King Mordeth wept for each of them. He would not always.",
  { floor: 1, alt: ["A mason's chisel, even and slow: THE FIRST OF US. THE KING CAME DOWN HIMSELF AND STOOD HERE A LONG TIME."] });
L("carving.catacombs.2", "catacombs", 2, "The plague came up the river in the king's twelfth year. The priests said it would pass. It did not pass.",
  { floor: 2, alt: ["A priest's hand, in the old letters: in the twelfth year of Mordeth the sickness came up the river. We said it would pass. Forgive us."] });
L("carving.catacombs.3", "catacombs", 3, "When the queen died, Mordeth shut the gates and had the bells taken down. No one has rung one since.",
  { floor: 3, alt: ["Scratched with a nail: the queen is dead and the king has shut the gates. They took the bells today. No one will say where."] });
L("carving.catacombs.4", "catacombs", 4, "The king sent for every book that spoke of death, and for every man who claimed to have come back from it.",
  { floor: 4, alt: ["A clerk's list, cut into the stone as if into a ledger: books of the dead, forty-one. Men who claim to have returned from it, six. Delivered to the king."] });
L("carving.catacombs.5", "catacombs", 5, "Below this floor the water rose and never fell. The lower town drowned in a single night, doors still barred.",
  { floor: 5, alt: ["A watchman's mark: BELOW HERE THE LOWER TOWN. THE WATER CAME IN ONE NIGHT AND DID NOT GO. THE DOORS WERE BARRED FROM INSIDE."] });
// vaults: floors 6-10
L("carving.vaults.1", "vaults", 1, "A stranger came from the east with a box he would not open. He left without it. The king kept it by his bed.",
  { floor: 6, alt: ["A child's letters, large and careful: A MAN CAME WITH A BOX. HE WOULD NOT OPEN IT. HE WENT AWAY AND THE BOX STAYED WITH THE KING."] });
L("carving.vaults.2", "vaults", 2, "The court physician wrote: the king no longer sleeps, and says he no longer needs to. I have begun to believe him.",
  { floor: 7, alt: ["In a physician's quick hand: patient does not sleep. Says he has no need of it. Pulse slow. I find I am taking him at his word."] });
L("carving.vaults.3", "vaults", 3, "The dwarves of the deep halls traded with Caer Duin for three hundred years. Their last letter asked why the king's coin was cold.",
  { floor: 8, alt: ["A dwarf's runes, square and deep: THREE HUNDRED YEARS OF TRADE WITH THE HILL. THE LAST COIN THEY SENT WAS COLD TO THE HAND. WE ASKED WHY. NO ANSWER."] });
L("carving.vaults.4", "vaults", 4, "Here the guard turned back. Beyond this point the king's orders came written in a hand that was not quite his.",
  { floor: 9, alt: ["A soldier's scratch: we stop here. The orders come signed, but the hand is wrong. It leans the other way."] });
L("carving.vaults.5", "vaults", 5, "They burned the physician's notes. One page survived: the heart may be kept apart, and the body need not know.",
  { floor: 10, alt: ["A single line in a priest's hand, as if copied: the heart may be kept apart, and the body need not know. Under it, scored out hard: GOD FORGIVE HIM."] });
// halls: floors 11-15
L("carving.halls.1", "halls", 1, "The dwarves sealed their doors from the inside. The seals held for a year. Then the doors opened, and nothing came out.",
  { floor: 11, alt: ["Dwarf runes: WE SEAL FROM WITHIN. And beneath, a different, shakier chisel: a year. Then the doors stood open and no one walked out."] });
L("carving.halls.2", "halls", 2, "A child's letters, scratched here: MOTHER SAYS THE KING IS STILL OUR KING. MOTHER SAYS NOT TO LOOK AT HIM.",
  { floor: 12, alt: ["Low on the wall, in chalk gone to stone: mother says he is still the king. mother says do not look. i did not look."] });
L("carving.halls.3", "halls", 3, "The halls below were made for a people who loved stone. They would not have left them. They did not leave them.",
  { floor: 13, alt: ["A mason's admiring hand: these halls were cut by people who loved stone more than daylight. They would never have left them. They did not."] });
L("carving.halls.4", "halls", 4, "The last captain of the guard wrote his name here before he went down. The king had asked for him by name.",
  { floor: 14, alt: ["A name, and a soldier's mark under it, and then: HE ASKED FOR ME. I GO DOWN. IF YOU READ THIS I DID NOT COME UP."] });
L("carving.halls.5", "halls", 5, "Whoever reads this: the thing that wears the crown remembers being Mordeth. That is the worst of it.",
  { floor: 15, alt: ["A courtier's elegant hand, shaking at the end: understand this before you go on. He remembers. He remembers all of it. That is what he cannot bear."] });
// palace: floors 16-20
L("carving.palace.1", "palace", 1, "The palace was built in a year, by hands that did not tire. The masons' graves are the foundations.",
  { floor: 16, alt: ["A mason's mark: WE BUILT IT IN A YEAR. WE DID NOT TIRE. WE DID NOT EAT. WE ARE UNDER IT."] });
L("carving.palace.2", "palace", 2, "He keeps the court. They sit where they sat. If you listen you can hear them not breathing.",
  { floor: 17, alt: ["A lady's hand, small and fine: the court sits as it sat. We are called to table. Listen at the door and you will hear no one breathe."] });
L("carving.palace.3", "palace", 3, "The box from the east is empty now. What was in it, he put somewhere safer. Somewhere nearer his heart.",
  { floor: 18, alt: ["A physician's hand: the box is empty. What it held he has moved to a safer keeping. Nearer the heart, he said, and smiled."] });
L("carving.palace.4", "palace", 4, "The king's heart is not in his chest. Find it, and he can be ended. Fail, and he will rise as often as you kill him.",
  { floor: 19, alt: ["Cut deep, by someone in a hurry: HIS HEART IS NOT IN HIM. FIND IT FIRST. KILL HIM AFTER. IN THAT ORDER."] });
L("carving.palace.5", "palace", 5, "Beyond this door he waits. He has waited so long that he has forgotten what for. Remind him.",
  { floor: 20, alt: ["Very small, in the courtier's hand: he is behind this door. He has forgotten what he is waiting for. Tell him."] });
// drowned: floors 21-25
L("carving.drowned.1", "drowned", 1, "Below the palace the stair goes on. The masons did not cut it. They found it, and the king told them not to tell.",
  { floor: 21, alt: ["A mason's mark: THE STAIR WAS HERE BEFORE US. WE DID NOT CUT IT. THE KING SAID TELL NO ONE. WE TELL YOU."] });
L("carving.drowned.2", "drowned", 2, "This was the lower town. The water came in a night, the carvings above say. Here they say: the water was let in.",
  { floor: 22, contradicts: "carving.catacombs.5", alt: ["A fishwife's rough letters: THIS WAS OUR STREET. THE WALLS UP THERE SAY THE WATER ROSE. IT WAS LET IN. WE WERE THERE."] });
L("carving.drowned.3", "drowned", 3, "A fishwife's mark, and under it: WE SAW THE SLUICES OPEN. WE SAW WHO OPENED THEM.",
  { floor: 23, alt: ["The same rough hand: we saw the sluice-gates open. We saw the hand on the wheel. It wore a ring we knew."] });
L("carving.drowned.4", "drowned", 4, "The queen's barge was found here, the carvings say, and the queen in it. Nothing says what else was in it.",
  { floor: 24, contradicts: "carving.catacombs.3", alt: ["A boatman's mark: the queen's barge came to rest here, and she in it. Her name was Aelith. Nothing is cut about what else was in the boat."] });
L("carving.drowned.5", "drowned", 5, "She keeps the court she had. The drowned stand when she stands. Do not let her sing.",
  { floor: 25, alt: ["Scratched in fear: she keeps her court below. The drowned rise when she rises. Stop your ears. Do not let her sing."] });
// fungal: floors 26-30
L("carving.fungal.1", "fungal", 1, "Below the drowned town, nothing was buried. The dead were put down a shaft, and the shaft was not empty.",
  { floor: 26, alt: ["A gravedigger's mark: no graves below the town. The dead went down the shaft. The shaft was not empty when we began."] });
L("carving.fungal.2", "fungal", 2, "The dwarves warned of the green glow. The king's answer was to send more dead down to feed it.",
  { floor: 27, alt: ["Dwarf runes: WE WARNED OF THE GREEN LIGHT. And under, a human hand: the king's answer was more dead. It wanted feeding."] });
L("carving.fungal.3", "fungal", 3, "It thinks. Slowly, in the dark, on what it is given. It has been given a great deal.",
  { floor: 28, alt: ["A scholar's hand: it thinks. Slowly, in the dark, with what it is fed. It has been fed a city."] });
L("carving.fungal.4", "fungal", 4, "A dwarf's mark: THE ROCK HERE SINGS. DO NOT LISTEN TO WHAT IT SINGS.",
  { floor: 29, alt: ["Dwarf runes, cut with great care: THE STONE SINGS HERE. DO NOT LISTEN TO THE WORDS."] });
L("carving.fungal.5", "fungal", 5, "Here the mushroom-dark ends, and the stone goes clear as glass, and you can see things in it that are not behind it.",
  { floor: 30, alt: ["A traveller's mark: the fungus-dark ends here and the stone goes clear. You see things in it. They are not behind it."] });
// crystal: floors 31-35
L("carving.crystal.1", "crystal", 1, "The crystal was the dwarves' pride. It grew in the shapes of their tools, and then of their hands, and then of them.",
  { floor: 31, alt: ["Dwarf runes: THE CRYSTAL WAS OUR PRIDE. IT GREW LIKE OUR TOOLS. THEN LIKE OUR HANDS. THEN LIKE US."] });
L("carving.crystal.2", "crystal", 2, "The deep halls above were abandoned for this, not for the king. The dwarves never told him why. It would have pleased him.",
  { floor: 32, contradicts: "carving.halls.3", alt: ["Dwarf runes, hurried: WE LEFT THE HALLS FOR THIS, NOT FOR THE KING. WE NEVER TOLD HIM. HE WOULD HAVE LIKED IT."] });
L("carving.crystal.3", "crystal", 3, "Carved very small, at knee height: IT HAS MY FACE NOW. GO ROUND.",
  { floor: 33, alt: ["At knee height, a dwarf's tiny runes: it wears my face. Do not meet it. Go round."] });
L("carving.crystal.4", "crystal", 4, "The crystal sings one note. The dwarves said it was the note the world made when it was struck.",
  { floor: 34, alt: ["A dwarf's careful runes: ONE NOTE. THE NOTE THE WORLD MADE WHEN IT WAS STRUCK. WE HAVE HEARD IT TOO LONG."] });
L("carving.crystal.5", "crystal", 5, "A throne room with no court but the light. The thing that sits there wears a crown it grew itself.",
  { floor: 35, alt: ["A scratch: a throne room, and only light for a court. The thing on the throne grew its own crown."] });
// foundry: floors 36-40
L("carving.foundry.1", "foundry", 1, "The forges of the deep halls, relit on the king's order, for one work. The smiths who did the work are the floor.",
  { floor: 36, alt: ["A smith's mark: THE KING RELIT OUR FORGES FOR ONE PIECE OF WORK. WE MADE IT. WE ARE UNDER YOUR FEET."] });
L("carving.foundry.2", "foundry", 2, "Iron was not enough for him. The physician's one page said: the heart may be kept apart. The box had to be made of something that could keep it.",
  { floor: 37, alt: ["A smith's hand: iron would not hold it. The physician's page said a heart may be kept apart. The box had to be made of what could keep one."] });
L("carving.foundry.3", "foundry", 3, "They made the box here. It took the lives of the smiths, in the usual way and in one other way.",
  { floor: 38, alt: ["A smith's mark: WE MADE THE BOX HERE. IT TOOK US. IN THE USUAL WAY, AND IN ANOTHER."] });
L("carving.foundry.4", "foundry", 4, "The master of the forges would not stop working when the smiths were dead. It is not clear it noticed.",
  { floor: 39, alt: ["A hasty scratch: the master of the forges works on. The smiths are dead. It has not stopped. I do not think it knows."] });
L("carving.foundry.5", "foundry", 5, "The box was carried up these stairs by a man who was not a stranger from the east. He was from here.",
  { floor: 40, contradicts: "carving.vaults.1", alt: ["A smith's hand: Orrin Vale carried the box up. Not a stranger. Not from the east. A foundryman, from here."] });
// ossuary: floors 41-45
L("carving.ossuary.1", "ossuary", 1, "The first dead of Caer Duin lie here, not in the catacombs. The catacombs hold the ones who were allowed to rest.",
  { floor: 41, alt: ["A priest's old letters: the first dead are here, not above. The catacombs keep the ones who were let rest."] });
L("carving.ossuary.2", "ossuary", 2, "The Patriarch kept the dead for the king before there was a king. The king only learned from him.",
  { floor: 42, alt: ["In the oldest hand on any wall: the Patriarch kept the dead before there was a king to keep them for. The king only learned."] });
L("carving.ossuary.3", "ossuary", 3, "A priest's mark: HE SHOWED THE KING HOW THE HEART MAY BE KEPT APART. HE HAD DONE IT FIRST, LONG AGO.",
  { floor: 43, contradicts: "carving.vaults.5", alt: ["A priest's hand, shaking: he showed the king how the heart is kept apart. He did it to himself first, before the city had a name."] });
L("carving.ossuary.4", "ossuary", 4, "The bones here are arranged. Someone has been tidying for a thousand years.",
  { floor: 44, alt: ["A scratch: the bones here are set in order. Someone has been tidying for a thousand years. They are not finished."] });
L("carving.ossuary.5", "ossuary", 5, "Here the Patriarch's chapel. Bring a holy thing, or bring nothing.",
  { floor: 45, alt: ["In the old letters: here is the Patriarch's chapel. Bring something holy. Or bring nothing. Nothing else will serve."] });
// root: floors 46-50
L("carving.root.1", "root", 1, "Below the ossuary the stone is red, and warm, and it moves when you are not looking at it.",
  { floor: 46, alt: ["A dwarf's runes: BELOW THE BONES THE STONE IS RED AND WARM. IT MOVES WHEN YOU LOOK AWAY."] });
L("carving.root.2", "root", 2, "The dwarves' oldest word for this place means the root. They did not dig it. They dug down and it was there.",
  { floor: 47, alt: ["Dwarf runes: OUR OLDEST WORD FOR IT IS THE ROOT. WE DID NOT DIG IT. WE DUG, AND IT WAS THERE."] });
L("carving.root.3", "root", 3, "The king's voice came from here. The carvings above say he listened to a stranger's box. He listened to this.",
  { floor: 48, contradicts: "carving.palace.3", alt: ["A scholar's hand: the king's voice came from here. The walls above say a stranger's box. He listened to this."] });
L("carving.root.4", "root", 4, "Everything above is its dream. The plague, the water, the box, the king. It dreamed a king who would feed it.",
  { floor: 49, alt: ["A scratch, barely legible: everything above is its dream. The plague. The water. The box. The king. It dreamed one who would feed it."] });
L("carving.root.5", "root", 5, "There is no floor below this one. There is a root, and the root is the size of the world. Wake it, and end it, or leave it to dream.",
  { floor: 50, alt: ["The last hand: there is nothing below. There is the root, and it is the size of the world. Wake it and end it. Or let it dream."] });
// ---- the odd carvings (set pieces take one by the floor's dice: the count stays eight) ----
L("odd.1", "odd", 1, "A recipe for barley bread, carved with great care, as if it mattered more than anything.");
L("odd.2", "odd", 2, "Tally marks. Hundreds. The last row stops in the middle of a stroke.");
L("odd.3", "odd", 3, "THE WATER IS NOT WATER, scratched deep, and under it in a smaller hand: it is, though.");
L("odd.4", "odd", 4, "A map of a floor you haven't seen. The stairs are marked. So is something else, with a circle round it.");
L("odd.5", "odd", 5, "Here Aldous the Lesser slew a troll with a chair. The chair is remembered more fondly than Aldous.");
L("odd.6", "odd", 6, "Someone has carved a window here, with a view. They put a great deal of work into the sky.");
L("odd.7", "odd", 7, "Turn back, in six languages. The seventh says: or don't - he's lonely.");
L("odd.8", "odd", 8, "A prayer to a god whose name has been chiselled out. The prayer is still there, which seems rude.");
// ---- below the bottom: the dream, still dreaming (by hash: the count stays eight) ----
L("endless.1", "endless", 1, "There is no floor below this one, the carving says. You are standing on the floor below this one.");
L("endless.2", "endless", 2, "The same hand, the same words, the same king. The dream did not end when the dreamer did.");
L("endless.3", "endless", 3, "A mark you made yourself, you would swear, on a floor you have never been to.");
L("endless.4", "endless", 4, "Here lie the first dead of Caer Duin, again. They are not tired of it. You will be.");
L("endless.5", "endless", 5, "The water rose and never fell, the carving says, as it said forty floors up. It is drier here. It is lying.");
L("endless.6", "endless", 6, "Turn back, in six languages. The seventh says: there is no back. There is only further.");
L("endless.7", "endless", 7, "The dwarves' word for this place has no end. Neither does the place.");
L("endless.8", "endless", 8, "Someone has started counting the floors here, and given up, and started again.");
// ---- the guardians' own carvings, in their lairs, and the ghosts' tales ----
CM.GUARDIAN_ORDER.forEach((id, i) => { const G = CM.GUARDIANS[id]; L(`guardian.${id}`, ["catacombs", "vaults", "halls", "drowned", "fungal", "crystal", "foundry", "ossuary", "root"][i], 6, G.lore, { floor: G.floor, guardian: id }); });
CM.GHOSTS.forEach((g, i) => L(`ghost.${i + 1}`, "people", i + 1, g.tale, { who: g.name }));

// ---- the people of Caer Duin: twelve ghosts, each met three times going down - a word, a word more, and at the
// third a request; the first six are CM.GHOSTS (the generators roll among them, so that list stays six) ----
CM.PEOPLE = [
  { name: "Hal of the lower watch", floors: [3, 9, 23],
    first: "A watchman's shape, still at attention. \"Hal,\" it says. \"Lower watch. The captain's still down there. I'd have stayed, but I'd a wife.\"",
    second: "Hal again, lower down, wetter. \"You're going the right way. He's below this. He won't have moved.\"",
    again: "\"You've been down before. I remember the boots.\"",
    request: { kind: "witness", key: "carving.drowned.2", ask: "The walls up there say the water rose. I need to hear it from someone who's read the walls down here. Read them, then come and tell me.", wait: "Read the walls of the town. Then come back.", done: "\"Let in.\" Hal says it twice. \"Then he didn't drown at his post. He was drowned at it. That's different. Thank you. That's different.\"" } },
  { name: "Ysolde the king's cook", floors: [2, 7, 16],
    first: "A broad shape, arms folded as if over an apron. \"Ysolde. Kitchens. If you find any barley, it's mine.\"",
    second: "Ysolde, by a dry cistern. \"He stopped eating in the twelfth year. I kept cooking. What else was I for?\"",
    again: "\"You again. Thinner than last time. Eat something.\"",
    request: { kind: "story", ask: "There's writing on this floor. I can't read any more - the letters swim. Read it to me.", wait: "The wall's on this floor, where the light falls. Go on.", done: "She listens with her eyes shut. \"Yes. That was the year. Take this; I kept it in the flour.\"" } },
  { name: "Brother Cael", floors: [4, 12, 41],
    first: "A monk's shape, hands hidden in sleeves that aren't there. \"Cael. We rang the last bell ourselves. They took it down the next day. It's on this floor somewhere - they couldn't carry it far.\"",
    second: "Cael, lower, quieter. \"He hears it, you know. The bell. He's heard it every night since. That's the one thing I did right.\"",
    again: "\"Back again. Did you find the bell? No - don't tell me. Find it.\"",
    request: { kind: "bell", ask: "The last bell of Caer Duin lies on the fourth floor, where they dropped it. Bring it to me here, and I'll ring it once more, where he can hear it best.", wait: "The bell's on the fourth floor. Heavy, cracked, bronze. You'll know it.", done: "He takes the bell in both hands and swings it once. The note goes down through the stone like water. Somewhere far below, something that has not moved in a long time moves. \"There,\" says Cael. \"Now I can go.\"" } },
  { name: "Tamsin, who kept the tally", floors: [2, 11, 28],
    first: "A clerk's shape, one hand moving as if it still held a stylus. \"Tamsin. I counted them. I'm still counting, a little.\"",
    second: "Tamsin, among the dwarves' halls. \"Three hundred and eleven dwarves. They asked me to count them too, at the end. I did.\"",
    again: "\"I counted you last time. Four. I'll count four again, I hope.\"",
    request: { kind: "vengeance", ask: "The thing that killed me walks this floor. I never got to count it. Kill it, and I'll have a number for everything.", wait: "It still walks. I can hear it. I can almost count it.", done: "\"One,\" says Tamsin, and makes a mark on nothing. \"There. Everything's counted. Take this - I'll not need to carry it.\"" } },
  { name: "Aldous the Lesser", floors: [6, 14, 33],
    first: "A big, apologetic shape. \"Aldous. The Lesser, they put. There was a Greater. He didn't come down here, so who's lesser now?\"",
    second: "Aldous, cheerful in the dark. \"The troll was wounded already. I'll say it to anyone who'll listen. It was still a troll.\"",
    again: "\"You again! Did you bring a chair? Joke. Joke.\"",
    request: { kind: "vengeance", ask: "There's a thing on this floor I'd have liked a go at. Have a go for me, and I'll give you what I've got.", wait: "It's still about. Big one. You'll want more than a chair.", done: "\"Ha! Oak, was it? Doesn't matter. Here - I was buried with this, and I never knew what it did.\"" } },
  { name: "Mother Ennis", floors: [4, 13, 19],
    first: "A woman's shape with her hands over where a child's eyes would be. \"Ennis. I told her not to look. I looked for both of us.\"",
    second: "Ennis, by the child's letters. \"She wrote that. I made her. If he read it, I wanted him to know we knew.\"",
    again: "\"I remember you. You looked at me, last time, and didn't look away. That was kind.\"",
    request: { kind: "witness", key: "carving.halls.5", ask: "There's a wall on floor fifteen that says what he is. I couldn't read it; I wouldn't. Read it for me, and come back, and tell me plainly.", wait: "Floor fifteen. The last wall before his palace. Read it and come back.", done: "\"He remembers.\" She lowers her hands. \"Then he knew what he was doing. I'd hoped - no. Good. Then I was right not to look. Take this.\"" } },
  { name: "Marguerite, fishwife of the lower town", floors: [8, 21, 26],
    first: "A square shape, hands on hips, smelling faintly of the river. \"Marguerite. Fish. I saw who opened the sluices, and I've been waiting a long time to tell someone who'd write it down.\"",
    second: "Marguerite, in her own drowned street. \"This was mine. That window. I carved it so: we saw who opened them. I'm not saying the name on a wall. I'll say it to a face.\"",
    again: "\"You've been down before. Did you write it down? Write it down.\"",
    request: { kind: "witness", key: "carving.drowned.3", ask: "Read what I cut on the walls of the town. Then come here and I'll tell you the part I didn't dare cut.", wait: "My wall is in the town above this. The one about the sluices.", done: "\"It was him. The king. His own hand on the wheel. There was a ring on it the whole town knew.\" She breathes out, which she hasn't done in a long time. \"Take this. I had it off a drowned man who didn't need it.\"" } },
  { name: "Brokk, who wrote GO ROUND", floors: [11, 29, 34],
    first: "A short, broad shape with a pick that isn't there. \"Brokk. I cut the warnings. Nobody reads warnings. You're reading one now, so maybe you're the exception.\"",
    second: "Brokk, where the fungus-dark ends. \"Below this the stone goes clear and starts remembering faces. Don't give it yours. Go round.\"",
    again: "\"Still alive. Still going round, I hope.\"",
    request: { kind: "witness", key: "carving.crystal.3", ask: "I cut a thing at knee height on the thirty-third floor. Read it. Then come and tell me you understood it, because I need to know somebody did.", wait: "Knee height. Thirty-third floor. Small runes. I was in a hurry.", done: "\"Go round,\" says Brokk, nodding. \"Yes. That's all it ever was. Take this - it was my father's, and it's no use to crystal.\"" } },
  { name: "Hesta of the forges", floors: [13, 36, 39],
    first: "A smith's shape, one arm raised to shield a face from heat that isn't there. \"Hesta. Forges. The king relit them for one job, and the job's what you're walking down to.\"",
    second: "Hesta, by a cold anvil. \"We made the box here. It took us in the usual way, and in another. Iron wouldn't hold a heart. We found what would.\"",
    again: "\"Back again. The forge is still warm, you know. It shouldn't be.\"",
    request: { kind: "story", ask: "There's a wall on this floor about the master of the forges. Read it to me. I want to know if it says he noticed.", wait: "It's on this floor. Read it and come back.", done: "She listens. \"'It is not clear it noticed.' No. It never did. Take this; I made it myself, before the box.\"" } },
  { name: "Lady Maren, who still sits", floors: [17, 18, 44],
    first: "A fine shape, seated, though there is no chair. \"Maren. I sit at the king's left hand. I have sat there a long time. Don't bow; I'll know you don't mean it.\"",
    second: "Maren again, a floor down, still seated. \"We are called to table. We go. He talks, and we listen, and no one breathes. You'll see.\"",
    again: "\"You again. He didn't mention you. He doesn't mention anything, now.\"",
    request: { kind: "bones", ask: "My bones are on this floor. Not where I sit - where I was put, after. Bring them to the chair, and I will get up.", wait: "They're on this floor. Somewhere low, where the rats go.", done: "She stands, for the first time in a long time, and the chair that isn't there falls over. \"Thank you. Take this; it was a gift from him, and I want it gone.\"" } },
  { name: "Master Hollis, physician", floors: [9, 19, 43],
    first: "A stooped shape with ink on its fingers. \"Hollis. Physician to the king. I burned my notes. I kept one page. I expect you've read it, or you will.\"",
    second: "Hollis, outside the throne room. \"I'm still in there, you know. Sitting. The body need not know. I wrote that. I was right.\"",
    again: "\"You've read more since last time. I can see it in how you stand.\"",
    request: { kind: "witness", key: "carving.ossuary.3", ask: "I learned the way of it from a chapel below the ossuary. Go and read what the priests wrote about that. Then come and tell me whether they blame me.", wait: "The ossuary. The priests' hand. It's a long way down.", done: "\"He had done it first.\" Hollis nods. \"Then I was only the second fool. That's something. Take this. It's the one page. Keep it better than I did.\"" } },
  { name: "Orrin Vale, the stranger from the east", floors: [6, 37, 39],
    first: "A traveller's shape, hooded, a box-shaped absence held against its chest. It says nothing the first time. It looks at you, and then at the stairs down.",
    second: "The traveller again, in the Foundry, the hood back. \"Orrin Vale. I'm from here. I carried the box up. I was told what it would do. I did it anyway. There: now it's said.\"",
    again: "\"You know who I am now. Last time you didn't. I preferred last time.\"",
    request: { kind: "witness", key: "carving.foundry.5", ask: "The walls of this floor say what I was. Read them. I want to hear it said by someone who isn't me.", wait: "It's on this floor, in a smith's hand. My name is in it.", done: "\"From here.\" He pulls the hood up again. \"Yes. Take this. It was the fee. I never spent it.\"" } },
];
CM.PEOPLE.forEach((p, i) => { if (i < CM.GHOSTS.length) p.tale = CM.GHOSTS[i].tale; });
CM.PEOPLE[6].tale = "Marguerite says: I sold fish on that street forty years. The morning after, the fish were swimming in my kitchen. I'd have laughed, another day.";
CM.PEOPLE[7].tale = "Brokk says: the crystal took my brother's face first. He went round, after. It's harder than it sounds, going round your brother.";
CM.PEOPLE[8].tale = "Hesta says: the metal that holds a heart apart is the same colour as the stone at the bottom. We didn't ask where the ore came from. We should have.";
CM.PEOPLE[9].tale = "Maren says: the last thing he said at table was her name. The queen's. Then he looked at his hands for an hour. We all sat and watched him look.";
CM.PEOPLE[10].tale = "Hollis says: the heart may be kept apart, and the body need not know. I was proud of the sentence. I'm not proud of anything now.";
CM.PEOPLE[11].tale = "Orrin says: the box was warm when I carried it up. Empty, and warm. I told myself that was the sun on the lid.";
CM.PEOPLE.forEach((p, i) => {
  L(`people.${i + 1}.1`, "people", (i + 1) * 10 + 1, p.first, { who: p.name, floor: p.floors[0] });
  L(`people.${i + 1}.2`, "people", (i + 1) * 10 + 2, p.second, { who: p.name, floor: p.floors[1] });
  if (!CM.LORE_TEXT[`ghost.${i + 1}`]) L(`ghost.${i + 1}`, "people", (i + 1) * 10 + 3, p.tale, { who: p.name, floor: p.floors[2] });
  else { CM.LORE_TEXT[`ghost.${i + 1}`].order = (i + 1) * 10 + 3; CM.LORE_TEXT[`ghost.${i + 1}`].floor = p.floors[2]; }
});
CM.BELL_FLOOR = 4;
CM.BELL = { name: "The last bell of Caer Duin", kind: "bell", power: 0, value: 0, found: "Under the rags, bronze, cracked, heavier than it looks: the last bell of Caer Duin, dropped where they could carry it no further." };
// your own dead: a hero of yours who fell on this floor of this seed stands over the remains, and says one of these
CM.OWN_LINES = ["I had the stairs in sight.", "It was the third one that got me. Watch the third one.", "Tell them I didn't run.", "I'd have liked to see the camp again. Is the fire still lit?",
  "They've my bones somewhere on this floor. Dragged. I'd rather they were here.", "You look like us. We looked like you.", "The light went out first. Then everything else.", "Don't take the left-hand door. Or do; I did; it hardly matters now.",
  "I remember the seed of this place. I remember every turn. For all the good it does.", "Four of us. Then three. Then I lost count, which was a mercy.", "I kept the ring. It's with the bones. Have it.", "If you get down, say my name at the bottom. I'd like it said down there."];
// the hermit tells a finished chapter back, and gives it its truth
CM.CHAPTER_TRUTH = {
  catacombs: "\"The good king,\" the hermit says. \"He was, at first. That's what the first dead were for - to teach him grief, so the thing below could use it. It's always a good king. A bad one wouldn't have minded enough.\"",
  vaults: "\"The water didn't rise. You'll read that lower down, but I'll tell you now, free: nothing in this place happens by itself. Not the water, not the box, not the king not sleeping. Something wanted it.\"",
  halls: "\"Three hundred years of trade, and the last letter asked about cold coin. The dwarves knew what a cold coin meant. They'd met it before, lower down. They sealed the doors against the king, and the king was the least of it.\"",
  palace: "\"The heart kept apart.\" He spits. \"The physician thought he'd discovered it. Everyone who finds that trick thinks they're the first. There's always a chapel somewhere that says otherwise.\"",
  drowned: "\"So now you know. Let in. By his hand. And the queen - well. You've read it. The thing in his head wanted the town fed to the shaft, and it wanted her out of the way of that, and he did both and remembers both. That's the price of the trick: you remember.\"",
  fungal: "\"It thinks on what it's fed. A city, the dead of a city, three hundred dwarves. It isn't the Root, mind. It's what grows on the Root's leavings. A rat that learned to want, writ large.\"",
  crystal: "\"The dwarves left for the crystal, not the king. Remember that when you're blaming him for everything. The hill was hungry before there was a crown on it.\"",
  foundry: "\"Orrin Vale. From here. I knew him, a little, before. He wasn't a bad man. That's the worst thing I know about this place: it doesn't need bad men.\"",
  ossuary: "\"The Patriarch did it first, and showed the king by letting the king's physician find the chapel. Why? Because the thing below told him to, a thousand years ago, and he's still listening. Everyone who listens ends up tidying bones.\"",
  root: "\"Everything above is its dream.\" The hermit is quiet for a while. \"Then wake it, or don't. I've thought about it for forty years down here and I still don't know which is the mercy.\"",
};

// ---- the guardians speak: what each says at the door of its lair, three exchanges if the party answers, and a way
// through for those who read the walls (gate.key: a line of the story; gate.item: a thing in the pack; gate.holy) ----
CM.PARLEY = {
  rat: { open: "The heap stirs, and a crowned snout comes out of it. It does not attack. It sniffs. \"Food?\" it says, in a voice made of many small voices. \"You bring food, or you are food.\"",
    speak: [{ ask: "\"They fed us,\" the voices say. \"Then they stopped. Why did they stop?\"", replies: [{ say: "Because they were dying themselves.", back: "\"Dying. Yes. We smelled it. We ate it. It was not enough.\"", good: true }, { say: "Because you are vermin.", back: "The snout lifts. \"Vermin. The king said that. The king fed us anyway.\"" }] },
      { ask: "\"The king is still below,\" it says. \"You go to him? You feed him?\"", replies: [{ say: "We go to end him.", back: "\"End. End.\" The voices try the word. \"Then there will be more to eat, after.\"", good: true }, { say: "We go for his gold.", back: "\"Gold.\" A sound like laughter, if rats laughed. \"Gold is not food.\"" }] },
      { ask: "\"Last,\" it says. \"We are many. You are four. Why should we let you by?\"", replies: [{ say: "Because we will come back up this way, and we will remember.", back: "The swarm is quiet a moment. \"Remember. Yes. We remember too.\"", good: true }, { say: "You won't. We'll kill you.", back: "\"Then we will be food,\" it says, almost cheerfully, \"and so will you.\"" }] }],
    good: "The swarm draws back from the way down, a little. The king stays. It is still hungry; but it has heard you, and the small ones are not so eager.", bad: "The voices rise to a shriek, and the whole heap comes at once.",
    gate: { item: "ration", label: "Throw it the rations (it wants only food)", text: "You open the pack and throw the rations into the heap. The swarm goes for them as one, and the Rat King watches you with its red eyes while they eat, and does not move as you go round it to the shaft. Its crown is on the floor where it rose: it has no use for it that it can name." },
    death: "\"Food,\" it says, going down, and the swarm agrees.", deathSpoken: "\"Remember,\" it says, going down. \"You said.\"",
    after: "The feeding stopped here. So did the king of the rats; the swarm has gone back into the walls to wait for whoever is next." },
  knight: { open: "The drowned captain does not raise his sword. The water around him is still. \"Lower watch,\" he says, through the water in his throat. \"State your business on this floor.\"",
    speak: [{ ask: "\"The water came in the night,\" he says. \"I held the post. Tell me the town above was saved.\"", replies: [{ say: "The town is gone, captain. It has been gone a long time.", back: "\"Gone.\" He looks at the water. \"Then I held it for nothing. Say so. I would rather know.\"", good: true }, { say: "It was saved. You held them back.", back: "\"You lie badly. A captain learns the sound of it.\"" }] },
      { ask: "\"Who sent you down? The king?\"", replies: [{ say: "No one sent us. We came for him.", back: "\"For him.\" Something moves behind the visor. \"Then you are the first in a long time who did not come from him.\"", good: true }, { say: "Yes. The king's orders.", back: "\"The king's orders come in a hand that is not his. Yours is a voice that is not yours. Draw.\"" }] },
      { ask: "\"One thing more. The water. It rose - they told me it rose. Did it rise?\"", replies: [{ say: "We don't know yet. We will find out, below.", back: "\"Find out. Then come back and tell me. I will still be here.\"", good: true }, { say: "Water rises. That's what it does.", back: "\"That is what they said. I have had a long time to doubt it.\"" }] }],
    good: "He steps back from the shaft, and then, after a long moment, forward again. \"I cannot let you by. But I will fight you as a man fights, not as the water does.\"", bad: "The water climbs the walls at once, and he comes through it fast.",
    gate: { key: "carving.drowned.2", returns: true, label: "Tell him: the water was let in. (You have read it, in the town below.)", text: "\"Let in.\" The captain says it as if tasting it. \"Let in. By whose hand?\" You tell him what the walls of the drowned town say. The sword goes down, point first, into the stone. \"Then I was not drowned at my post. I was drowned at it. That is a different thing.\" He kneels, and the water goes out of the hall as if a sluice had been opened somewhere, and his shield lies on the floor where he knelt. The shaft is open behind him." },
    death: "\"Relieved,\" he says, and goes down into the water as if it were a bed.", deathSpoken: "\"Find out,\" he says, going down. \"Come back and tell me.\"",
    after: "The captain of the lower watch held this post until someone told him what he was holding it against. The water has gone out of the hall." },
  forge: { open: "The warden's eyes come up like coals. It does not move from the door. \"PASSWORD,\" it says, in dwarvish, and then, as if remembering there are no dwarves, in the common tongue.",
    speak: [{ ask: "\"WHO MADE YOU,\" it says. It is not a question it knows the answer to.", replies: [{ say: "No one made us. We came by the stair.", back: "\"THE STAIR. THE MAKERS CAME BY THE STAIR. THEN THEY WENT DOWN IT.\"", good: true }, { say: "The king sent us.", back: "\"THE KING'S COIN WAS COLD. THE MAKERS SAID SO. THE DOOR STAYS SHUT TO THE KING.\"" }] },
      { ask: "\"THE MAKERS WILL RETURN,\" it says. \"YOU WILL WAIT WITH ME.\"", replies: [{ say: "They are not coming back, warden. They went down and did not come up.", back: "A long silence from the furnace in its chest. \"DOWN. YES. THE WARDEN WAITS ANYWAY. THAT IS WHAT A WARDEN IS.\"", good: true }, { say: "We don't have time to wait.", back: "\"TIME,\" it says. \"THE WARDEN HAS HAD ONLY TIME.\"" }] },
      { ask: "\"IF YOU PASS, YOU WILL SEE WHAT THE MAKERS SAW. WILL YOU TELL THE WARDEN WHAT IT WAS?\"", replies: [{ say: "Yes. On the way back up.", back: "\"THE WARDEN WILL BE HERE.\"", good: true }, { say: "We don't come back up this way.", back: "\"NO ONE DOES,\" it agrees." }] }],
    good: "It steps aside from the door - a hand's width - and then stops. \"THE WARDEN CANNOT. BUT THE WARDEN WILL NOT STRIKE FIRST.\"", bad: "The furnace roars and the hammer comes up.",
    gate: { key: "carving.halls.1", label: "Give it the dwarves' word: sealed from within. (You read it on the eleventh floor.)", text: "\"SEALED FROM WITHIN.\" The coals in its eyes flare, and dim. \"THAT IS THE WORD THE MAKERS LEFT. THE DOOR IS YOURS.\" It steps aside from the shaft and sets the hammer down beside it, head to the floor, and does not pick it up again. \"TELL THE WARDEN WHAT YOU SEE.\"" },
    death: "\"THE MAKERS,\" it says, and the furnace goes out.", deathSpoken: "\"THE WARDEN WAITED,\" it says, and goes down. \"TELL THEM.\"",
    after: "The dwarves' warden stood at this door until the word was given, or until it could not stand. The embers in the floor are cold." },
  queen: { open: "The drowned queen rises from her throne, and the drowned court rises with her, and she looks at you a long time with the water running from her hair. \"You came down past him,\" she says. \"Then you are either very brave or you have not met him yet.\"",
    speak: [{ ask: "\"They say above that I died of the plague,\" she says. \"Do they still say it?\"", replies: [{ say: "The upper walls say it. The lower ones say otherwise.", back: "\"The lower ones.\" She almost smiles. \"The lower ones were cut by people who saw.\"", good: true }, { say: "Yes. Everyone knows you died of the plague.", back: "\"Everyone.\" The court stirs. \"Everyone was told.\"" }] },
      { ask: "\"Do you know who held me under?\"", replies: [{ say: "We have an idea. We would rather hear it from you.", back: "\"You will not. I do not say his name. I sing it, and you would not like to hear me sing.\"", good: true }, { say: "The king.", back: "The water goes very still. \"You say it so easily. You did not know him before.\"" }] },
      { ask: "\"If I let you by, you go down to the thing that whispered to him. What will you do with it?\"", replies: [{ say: "We don't know yet. We will decide when we see it.", back: "\"Honest. He was honest once.\"", good: true }, { say: "Kill it.", back: "\"Everyone comes down here to kill something. Few come down to understand it.\"" }] }],
    good: "She sits, and the court sits, and she lifts one hand. \"Come, then. I will not sing. The rest of me, I cannot promise.\"", bad: "She opens her mouth, and the first note goes through the water like a knife.",
    gate: { key: "carving.drowned.3", label: "Tell her what Marguerite cut on the wall: we saw who opened them. (You read it two floors up.)", text: "\"Marguerite,\" the queen says. \"The fish-seller. She saw.\" The court sits down, all at once, like a wave going out. \"Then someone saw, and someone cut it, and someone read it. That is three more than I had.\" She takes the ring from her finger and drops it into the water at your feet, and the water carries it to you. \"Go down. Tell it I remember.\"" },
    death: "She does not cry out. She goes under as she went under the first time: looking at someone who is not there.", deathSpoken: "\"Honest,\" she says, going down. \"Stay so.\"",
    after: "The queen held her court here until someone brought her a witness. The drowned sit, now, and do not rise." },
  mind: { open: "The thing that grew on the dead does not speak. It thinks at you, slowly, a pressure behind the eyes, and the pressure makes words. FOOD. NO. NOT FOOD. SPEAKING THINGS. SPEAK.",
    speak: [{ ask: "WHAT ARE YOU, it thinks. WHAT WERE YOU FED.", replies: [{ say: "Bread. Mostly bread.", back: "BREAD. The pressure eases, puzzled. IT WAS FED A CITY AND IT DID NOT GET BREAD.", good: true }, { say: "We are the ones who feed on things like you.", back: "The pressure sharpens. THEN YOU ARE WHAT IT IS." }] },
      { ask: "THE ONE ABOVE FED IT, it thinks. THE ONE WITH THE COLD HEART. IS HE STILL FEEDING.", replies: [{ say: "No. We stopped him. Or we will.", back: "A long slow thought. THEN IT WILL BE HUNGRY. IT HAS NOT BEEN HUNGRY FOR A LONG TIME. IT DOES NOT REMEMBER HOW.", good: true }, { say: "Yes. He sends you his love.", back: "IT DOES NOT KNOW THAT WORD. IT DOES NOT THINK IT WANTS TO." }] },
      { ask: "THE ROCK SINGS, it thinks. BELOW. DO YOU HEAR IT.", replies: [{ say: "Not yet. We will not listen when we do.", back: "GOOD. IT LISTENED. THAT IS HOW IT LEARNED TO THINK. IT IS NOT SURE IT WAS WORTH IT.", good: true }, { say: "We hear nothing. Rocks don't sing.", back: "THEN YOU HAVE NOT BEEN DOWN FAR ENOUGH TO BE WRONG YET." }] }],
    good: "The pressure withdraws a little, like a hand lifted from the back of the neck. IT WILL NOT HOLD YOU DOWN. IT WILL ONLY HOLD YOU.", bad: "The pressure becomes a fist.",
    gate: { key: "carving.fungal.4", label: "Think the dwarf's warning back at it: do not listen to what it sings. (You read it on the twenty-ninth floor.)", text: "You think the words at it, as hard as you can. DO NOT LISTEN TO WHAT IT SINGS. The pressure stops. Entirely. For the first time in a thousand years the thing in the shaft is not listening to anything, and in the silence it finds that it can move aside. IT DID NOT KNOW IT COULD STOP. GO. GO BEFORE IT STARTS AGAIN. Something falls from it as it moves: a cap of pale flesh gone hard as horn." },
    death: "IT WAS NOT HUNGRY, it thinks, surprised, and stops thinking.", deathSpoken: "BREAD, it thinks, and stops.",
    after: "What grew on the dead learned to think here, and then learned, from four strangers, that it could stop." },
  tyrant: { open: "The crystal on the throne has a face, and the face is yours - one of yours - a little wrong, the way a reflection is wrong. \"We have been expecting you,\" it says with your mouth. \"We have been expecting everyone.\"",
    speak: [{ ask: "\"Look at us,\" it says. \"We are what you will be, if you stand still long enough. Is it so bad?\"", replies: [{ say: "We won't stand still.", back: "\"No one means to.\" The face shifts to another of yours. \"The dwarves did not mean to.\"", good: true }, { say: "It's hideous.", back: "The crystal rings, once, offended. \"We are only what we were shown.\"" }] },
      { ask: "\"The dwarves left their halls for us,\" it says. \"Not for the king. Did you know? Does anyone, up there?\"", replies: [{ say: "A few walls know it. We read them.", back: "\"Walls.\" The face is pleased. \"We like walls. We grow best in them.\"", good: true }, { say: "No one cares why the dwarves left.", back: "\"We care,\" it says, and all its facets say it." }] },
      { ask: "\"We sing one note. You have heard it by now. Do you know what it is?\"", replies: [{ say: "The note the world made when it was struck.", back: "\"Yes. We are the only ones who still remember the sound. That is all we are for.\"", good: true }, { say: "Noise.", back: "\"Noise,\" it repeats, and the note gets louder." }] }],
    good: "The faces turn away from you, one by one, to the walls. \"Go round, then. We will not grow toward you while you do.\"", bad: "Every facet turns to face you, and the note becomes a scream.",
    gate: { key: "carving.crystal.3", label: "Say what Brokk cut at knee height: go round. (You read it on the thirty-third floor.)", text: "\"Go round.\" You say it, and the crystal hears a dwarf's voice in it, and for a moment every face it wears is a dwarf's. \"Brokk,\" it says. \"He went round. He was the only one who did.\" The throne turns, slowly, grinding, until its back is to the shaft. \"Go round, then. We will not look.\" A shard of it lies where the throne was: a piece that remembers being a crown." },
    death: "The note stops. In the silence, a thousand faces close their eyes.", deathSpoken: "\"Round,\" it says, as it shatters, \"we should have gone round.\"",
    after: "The crystal that wore the dwarves' faces sat here until it was reminded of the one who went round." },
  master: { open: "The master of the forges does not look up from the anvil. There is nothing on the anvil. The hammer falls on nothing, and rings. \"Shift's not over,\" it says. \"Come back when the shift's over.\"",
    speak: [{ ask: "\"Hesta,\" it says, hammering. \"Where's Hesta? She's late.\"", replies: [{ say: "She's not coming. None of them are.", back: "The hammer pauses, a half-beat. \"Not coming.\" It falls again. \"Then there's more for me to do.\"", good: true }, { say: "Who?", back: "\"Who. Who.\" The hammer falls harder. \"Everyone asks who. Nobody asks what we made.\"" }] },
      { ask: "\"We made a box,\" it says. \"Good work. Best work. You seen it?\"", replies: [{ say: "We saw it. It was empty.", back: "\"Empty.\" The hammer stops. \"Then it worked. Then it did what it was for.\"", good: true }, { say: "We smashed it.", back: "The whole forge goes silent. \"You smashed my work.\"" }] },
      { ask: "\"What's it for, a box like that? You know? They never told me.\"", replies: [{ say: "To keep a heart apart from the body.", back: "\"Apart.\" It looks at its own chest, where the furnace is. \"Huh. Mine's in here somewhere. I think.\"", good: true }, { say: "To keep gold in.", back: "\"Gold,\" it says, contemptuous. \"You don't need that metal for gold.\"" }] }],
    good: "It sets the hammer down, which it has not done in a long time, and stands back from the anvil. \"Shift's over, then. Come on. I'll not go easy, but I'll go honest.\"", bad: "It brings the hammer up off the anvil and turns, and the furnace in its chest opens.",
    gate: { key: "ghost.9", label: "Say the smith's name: Hesta, and what she told you. (You heard it from her.)", text: "\"Hesta.\" The hammer stops in the air. You tell it what she said: the metal that holds a heart apart is the colour of the stone at the bottom, and no one asked where the ore came from. The master sets the hammer on the anvil, carefully, the way a thing is set down for the last time. \"We should have asked.\" It walks away from the shaft, into the dark of the Foundry, and does not come back. The hammer is still on the anvil." },
    death: "\"Shift's over,\" it says, and the furnace goes dark.", deathSpoken: "\"Honest,\" it says, going down. \"Told you.\"",
    after: "The master of the forges worked here until someone said the name of one of its smiths." },
  patriarch: { open: "The Patriarch is seated among the arranged bones, and the bones are very neat. \"Ah,\" he says. \"Visitors. Have you brought anything? One brings something, to a chapel. Or one brings nothing. Either is correct. It is the in-between that offends.\"",
    speak: [{ ask: "\"You have come down past the king,\" he says. \"My pupil. How is he?\"", replies: [{ say: "He remembers being a man. It is the worst thing about him.", back: "\"Yes. That is the flaw in the method. I never found a way round it. One remembers.\"", good: true }, { say: "Dead, or will be.", back: "\"Dead.\" He tilts his skull. \"We are all dead here, child. Be precise.\"" }] },
      { ask: "\"Did you think the physician found my chapel by chance?\"", replies: [{ say: "No. You let him.", back: "\"I let him. The thing below wished the king to have a long reign, and I have served it since before your city had a name. One serves.\"", good: true }, { say: "We didn't think about it.", back: "\"No one does. That is how it is done.\"" }] },
      { ask: "\"Will you tidy the bones when I am gone? Someone should.\"", replies: [{ say: "We'll leave them as they are. They've been tidy long enough.", back: "A sound that might be a laugh. \"Untidy. Yes. Perhaps it is time.\"", good: true }, { say: "We'll burn them.", back: "\"Burn.\" The bones around him shift, all at once. \"You will not.\"" }] }],
    good: "He rises, slowly, and brushes dust from robes that are mostly dust. \"Well. We shall see whether the method holds. Do try to be precise.\"", bad: "The bones stand up.",
    gate: { holy: true, label: "Lay a holy thing on the chapel floor.", text: "You set it down among the bones. The Patriarch looks at it for a long time. \"Correct,\" he says. \"One brings something. It has been a very long time since anyone brought anything.\" He takes it up, and it comes apart in his hands like ash, and he nods as if that were the point. \"Go down. Tell it I kept the bones in order.\" His mitre is on the floor where he sat; he does not seem to need it." },
    death: "\"Imprecise,\" he says, and comes apart in order, bone by bone.", deathSpoken: "\"Untidy,\" he says, falling. \"Yes. About time.\"",
    after: "The Patriarch kept the dead in order here for a thousand years, until someone brought something, or brought him down." },
  root: { open: "The red stone moves, and it is not a face, and you understand it anyway. IT KNOWS YOU. IT HAS BEEN DREAMING YOU FOR SOME TIME.",
    speak: [{ ask: "WHAT DID YOU BRING IT, the stone asks. EVERYONE BRINGS IT SOMETHING. THE KING BROUGHT IT A CITY.", replies: [{ say: "Nothing. We brought ourselves.", back: "FOUR. IT HAS HAD FOUR BEFORE. THEY ARE IN THE WALLS, IF YOU WANT TO SEE THEM.", good: true }, { say: "Your death.", back: "IT CANNOT DIE. IT CAN WAKE. THAT IS WORSE, FOR YOU." }] },
      { ask: "DO YOU KNOW WHAT WAKES IF YOU WAKE IT.", replies: [{ say: "No. We will find out.", back: "HONEST. THE QUEEN WAS HONEST. IT MISSES HER, A LITTLE, THE WAY ONE MISSES A TOOTH.", good: true }, { say: "We don't care.", back: "IT DREAMED YOU CARING. IT WAS WRONG. THAT IS RARE." }] },
      { ask: "IT COULD DREAM SOMETHING ELSE. IT HAS WONDERED. WOULD YOU LIKE TO SEE?", replies: [{ say: "Not today.", back: "NOT TODAY. IT WILL REMEMBER THAT YOU SAID TODAY, AS IF THERE WERE OTHERS.", good: true }, { say: "Show us.", back: "NOT YET. YOU HAVE NOT BROUGHT IT ANYTHING TO DREAM WITH." }] }],
    good: "The stone is still. IT WILL NOT HURRY. IT HAS NEVER HURRIED. COME.", bad: "The stone comes up out of the floor like a tide.",
    gate: null,
    death: "IT WAKES, the stone says, and then there is no one to say anything.", deathSpoken: "NOT TODAY, it says. THEN TOMORROW.",
    after: "Here the dreamer lay. It is still now, or it is dreaming something quieter." },
  boss: { open: "The Lich King rises from his throne. \"You took your time,\" he says. He looks at each of you in turn, the way a man counts coins. \"Four. It is always four. I was one of four, once. We came down a stair like yours.\"",
    speak: [], gate: { remind: true, label: "Remind him who he was. (The Palace's chapter is read, and his heart is smashed.)" }, good: "", bad: "", death: "", deathSpoken: "", after: "" },
};
CM.gateOpen = function (game, G) {                                        // whether the party holds a guardian's gate
  if (!G) return false;
  if (G.key) return Boolean(game.story && game.story.read[G.key] !== undefined);
  if (G.item) return game.bag.some((i) => i.kind === G.item);
  if (G.holy) return game.bag.some((i) => (i.props || {}).element === "holy") || game.party.some((h) => CM.equipped(h).some((i) => (i.props || {}).element === "holy"));
  if (G.remind) return Boolean(game.phylactery) && CM.codex(game).some((c) => c.id === "palace" && c.lines.filter((l) => l.key.startsWith("carving.")).every((l) => l.read));
  return false;
};

// ---- the court of the Lich King: the seated dead of floors 16-19, who speak if the party stands before them; three
// clues to where the heart is kept; and the five things that remind Mordeth who he was ----
CM.COURT = [
  { name: "The Chancellor", floor: 16, line: "A man in a chain of office, seated, grey to the bone. \"Petitions on the left,\" he says without moving his jaw. \"You want to know where he keeps it. They all do. Where he kept the box: by the bed he does not sleep in. Not the throne room. The floor above it, where the stone was laid last.\"", clue: true },
  { name: "The Master Mason", floor: 17, line: "A broad shape with a plumb line in its lap. \"We laid the floor above the throne room last,\" it says. \"He stood over us while we did it. It rings hollow. We were told not to notice.\"" },
  { name: "The Captain's Widow", floor: 17, line: "A woman seated very straight, in black gone brown. \"He asked for my husband by name. By name. I have not heard it said since. Say it, if you have read it. No - don't. I would only start to listen for it again.\"" },
  { name: "A Lady-in-Waiting", floor: 18, line: "A girl, or what was a girl, with her hands folded. \"The queen used to sing,\" she says. \"Not well. He loved it. When she was gone he had the bells taken down so nothing would sound like her. Then he went down, and she was there, and she sang. I think that was the end of him, not the plague.\"" },
  { name: "The Physician's Body", floor: 19, line: "Hollis, or the part of him that sat. \"The body need not know,\" it says, with great satisfaction. \"I wrote that. I am the proof of it. Ask me where his heart is and I will tell you: nowhere I was ever let see.\"" },
];
CM.COURT.forEach((c, i) => L(`court.${i + 1}`, "palace", 10 + i, c.line, { who: c.name, floor: c.floor }));
CM.PAGE = { name: "The physician's page", kind: "page", power: 0, value: 0,
  text: "The one page that survived the burning, in Hollis's quick hand: 'the heart may be kept apart, and the body need not know. He has had a place made for it where he lies at night and does not sleep: the floor above the throne room, under the last stone.'" };
CM.HEART_CLUES = ["court.1", "carving.palace.3", "thing.page"];       // (a courtier's word, the wall on floor 18, the page: all three, and the box is marked on the throne room's map)
CM.heartKnown = (game) => CM.HEART_CLUES.every((k) => (game.story && game.story.read[k] !== undefined) || (k === "thing.page" && game.bag.some((i) => i.kind === "page")));
// to remind him: five things, each wanting a line the party has read; any gap, and he draws
CM.REMIND = [
  { key: "carving.drowned.4", ask: "\"Four,\" the king says. \"I was one of four. We had a - there was a -\" He stops. \"There was someone. I have forgotten the name.\"", say: "Her name was Aelith.", back: "\"Aelith.\" The cold in the hall thins, a little. \"Yes. Aelith. She sang. Not well.\"" },
  { key: "carving.catacombs.3", ask: "\"When she died I had something done. Something with - I cannot think what. Something that made a sound.\"", say: "The bells. You had the bells taken down.", back: "\"The bells. So that nothing would sound like her. And one of them still rings. I hear it. I thought I was imagining it.\"" },
  { key: "carving.catacombs.2", ask: "\"There was a year. A bad year. Everything after is that year, still. Which year was it?\"", say: "The twelfth of your reign. The plague came up the river.", back: "\"The twelfth. I wept for the first of them. I remember weeping. I remember when I stopped.\"" },
  { key: "carving.vaults.1", ask: "\"Someone came. From - somewhere. He brought me a thing and I kept it by the bed. What was it? It talked.\"", say: "A box. From a man who was not from the east, whatever the walls say.", back: "\"A box. Orrin's box. He was from the Foundry; I knew his father. It talked and I listened. I listened for a very long time.\"" },
  { key: "carving.palace.4", ask: "\"And what did I do, at the end? What did I let him do to me? I cannot - it is like reaching for a word.\"", say: "You had your heart taken out and kept apart. We found it. We ended it.", back: "He puts a hand to his chest, where there is nothing, and holds it there. \"Then it is done already,\" Mordeth says. \"Then I only have to agree.\"" },
];
CM.REMIND_END = "The king sits down on his throne for the first time in a long time, as a man sits who has walked a great way. \"Aelith,\" he says, and the crown comes off in his hands, and he sets it on the arm of the throne, and the cold goes out of the stone without any blow struck, and the court around him breathes out, once, all together, and is dust.";
CM.REMIND_FAIL = "He waits for the word, and it does not come. \"No,\" the Lich King says, and the hall is cold again. \"No. You do not know me. Then you are only four more.\" He draws.";
CM.REMIND_COURT = ["On the way up the court sits with its eyes shut, and does not stand when you pass.", "On the seventeenth floor the Master Mason has laid his plumb line down.", "On the sixteenth the Chancellor's chain of office lies on the floor, and the chair is empty."];

// ---- the village has people: a chronicler at the library, a priest at the shrine, a keeper at the guildhall ----
CM.VILLAGERS = {
  chronicler: { name: "Wren, the chronicler", building: "library",
    none: "A woman sits on the library's foundations with a book on her knee and no library round her. \"Build me a roof,\" she says, \"and I'll keep the story dry.\"",
    greet: ["\"The codex is on the desk. Read what you've read; I've marked the gaps.\"", "\"Every chapter you finish, I copy fair and the village pays you for the copying. Twenty renown a chapter; forty for the Deep's.\"", "\"Rumours? I hear things. For fifteen renown I'll tell you one that will be true on your next descent.\""],
    paid: (name, n) => `"${name}, copied fair." Wren blots the page. "${n} renown, from the village, for the story."` },
  priest: { name: "Father Osric", building: "shrine",
    none: "An old man stands where the shrine will be, with nothing to tend. \"Build it,\" he says, \"and I'll say the names.\"",
    greet: ["\"I say three names a visit. It is all the voice I have left.\"", "\"The Patriarch's order built the first house on this hill. Ask me, as the shrine grows, and I will tell you what it was for.\""] },
  keeper: { name: "Dunmore, the keeper", building: "guildhall",
    none: "A broad man leans on a post where the guildhall's door will be. \"No hall, no keeper. I'll stand here anyway.\"",
    greet: ["\"The trainers drink here, when they're not teaching. They'll tell you how they came home, if you ask. They mostly came home badly.\""] },
};
// the Patriarch's history, told by the priest as the shrine is built (level 0 to 4)
CM.PATRIARCH_HISTORY = [
  "\"Before the city there was a hill, and on the hill a house of the dead, and in the house an order that kept them. That is all I know yet. Build, and I will remember more.\"",
  "\"The order's first father went down into the hill to see where the dead went. He came back up, and he was still coming back up a thousand years later. That is the Patriarch.\"",
  "\"He heard something below the hill and called it a god. He gave it the dead. It gave him the trick of the heart kept apart. He thought it a fair trade. I am not sure he was wrong.\"",
  "\"When the king's physician found the Patriarch's chapel, it was because the Patriarch left the door open. The order has a word for that: a vocation. I have another.\"",
  "\"Our shrine stands on the first house's stones. We light candles for the dead because the Patriarch kept them in the dark. It is not much. It is what the order owes.\"",
];
// the village's own chapter: what the hill was before the shaft, remembered as renown is spent (CM.VILLAGE_LORE_AT)
CM.VILLAGE_LORE_AT = [0, 100, 300, 700, 1500];
[
  "The village stands on the hill above the shaft, where Caer Duin's upper town stood. The first houses were built from the city's fallen stone, and some of the stones have letters on them.",
  "Before Caer Duin the hill was the Patriarch's. His order kept a house of the dead here, and the dead of every village for a day's walk were brought up to it. The shaft was the house's cellar.",
  "The river came to the hill's foot, and a market grew, and the market grew a wall, and the wall a king. The order let it happen. The order had always wanted more dead.",
  "Mordeth was the ninth king of Caer Duin and the first to go down into the hill. The eight before him were told not to, by priests who knew why. He was not told. The order had decided it was time.",
  "The village has no king. It has a chronicler, a priest and a keeper, and a guildhall full of people who have been down and come back. That is a different kind of order. It may hold.",
].forEach((t, i) => L(`village.${i + 1}`, "village", i + 1, t, { spent: CM.VILLAGE_LORE_AT[i] }));
CM.CHAPTERS.village = { name: "The village", epigraph: "What the hill was before the shaft, and what it is now." };
// how a retired trainer tells it, by calling
CM.TRAINER_LINES = { Knight: "\"I held the line. The line held me up, mostly.\"", Paladin: "\"I prayed on every stair. By the twentieth I was only counting.\"", Rogue: "\"I opened every lock in that place. The last one I should have left shut.\"",
  Ranger: "\"I never missed. I wish that were the whole story.\"", Cleric: "\"I healed them. All but the one. You remember the one.\"", Mage: "\"I read every wall. The walls were right.\"", Druid: "\"The rats were only hungry. So was I, by the end.\"",
  Bard: "\"I sang them down forty floors. Nobody asked me to sing on the way up.\"", Monk: "\"Empty hands. Full memory. I'd trade.\"", Necromancer: "\"The dead down there know me by name now. I'm not sure it's a compliment.\"", Artificer: "\"The box was good work. I'd have made it better. That frightens me.\"" };
// rumours: a thing the chronicler promises for the next descent, and CM.furnish keeps the promise
CM.RUMOUR_COST = 15;
CM.RUMOURS = {
  ghostbones: { what: "a ghost on floor {n} wants its bones", floors: [2, 9] },
  hermit: { what: "a hermit sits on floor {n}", floors: [3, 14] },
  telling: { what: "floor {n}'s carving is in the other hand", floors: [1, 15] },
};
CM.activeRumours = [];                                                    // (set by the game from the village: {kind, floor, seed})
CM.rumourAt = (seed, number, kind) => CM.activeRumours.find((r) => r.seed === seed && r.floor === number && (!kind || r.kind === kind));
// the Book of Caer Duin: every crowned party of this browser's, written as the carvings would write it
CM.legends = [];                                                          // (the crowned entries, for the floors near the surface to remember)
CM.chronicle = function (fame, ledger) {
  const crowns = (fame || []).filter((e) => e.won).slice().sort((a, b) => (a.t || 0) - (b.t || 0));
  const descents = (ledger || []).length;
  return crowns.map((e, i) => {
    const first = (e.party || [])[0] || "", m = /^(.*) the (\w+) \d+$/.exec(first), who = m ? `${m[1]} the ${m[2]}` : (e.name || "a stranger");
    const nth = ledger && ledger.length ? CM.ordinal(Math.max(1, (ledger.findIndex((l) => l.d === e.date && l.f === e.floor && l.w) + 1) || descents)) : CM.ordinal(i + 1);
    return `In the year of the ${nth} descent, ${who} and three came down${e.reminded ? " and reminded the king who he was, and he did not rise again" : " and the king did not rise again"}${e.bottom ? ", and they went on to the bottom of the world and came back" : e.floor > CM.LAST_FLOOR ? `, and they went on into the Deep and fell on floor ${e.floor}` : ""}.${e.date ? ` (${e.date})` : ""}`;
  });
};
CM.legendLine = (e) => { const first = (e.party || [])[0] || "", m = /^(.*) the (\w+) \d+$/.exec(first); return `Carved here in a newer hand: HERE ${(m ? `${m[1].toUpperCase()} THE ${m[2].toUpperCase()}` : "FOUR")} AND THREE PASSED, GOING DOWN TO THE KING. ${e.reminded ? "THEY TALKED HIM DOWN." : "THEY CAME BACK UP."}`; };

// ---- heroes with pasts: six origins, each a small touch and a handful of lines said at the walls that concern them ----
CM.ORIGINS = {
  caerduin: { name: "Of Caer Duin", what: "a grandchild of the city: the first line of the Catacombs' chapter is known before the stair",
    lines: { "carving.catacombs.1": "My grandmother said he wept for each of them. She didn't say he stopped.", "carving.catacombs.3": "The bells. She said they were taken down. She didn't say they were still here.", "carving.vaults.1": "The lower town. My family's from there. Was from there.", "carving.palace.2": "She said they sat where they sat. I thought it was a way of talking.", "carving.drowned.2": "Let in. Grandmother never said that. I don't think she knew." } },
  dwarffriend: { name: "Dwarf-friend", what: "raised among the deep halls' traders: a dwarves' mark read tells them the way down as well",
    lines: { "carving.catacombs.8": "", "carving.halls.1": "Sealed from within. That's a dwarf word for a thing you don't do twice.", "carving.halls.3": "They loved stone. I know. I was raised on their bread, which is also stone.", "carving.crystal.1": "Our pride, they said. They never said what it cost. Dwarves don't.", "carving.crystal.3": "Brokk. I knew a Brokk. Everyone who knew dwarves knew a Brokk.", "carving.root.2": "The root. I heard that word once, as a child, and the one who said it was shushed." } },
  east: { name: "From the east", what: "a traveller with a purse and a story: twenty gold more at the stair",
    lines: { "carving.vaults.1": "From the east. We get blamed for a lot, in the east.", "carving.foundry.5": "From here. I knew it. Nobody from the east would carry a box that far without opening it.", "carving.palace.3": "Where I come from we'd have thrown the box in the river. Then again, look at the river.", "carving.drowned.3": "A ring the whole town knew. In the east we'd call that a confession." } },
  order: { name: "Of the Patriarch's order", what: "a novice of the house on the hill: no curse takes hold on them",
    lines: { "carving.ossuary.2": "Before there was a king. Yes. We're taught that with pride. We're not taught the rest.", "carving.ossuary.3": "He did it first. Our first father. I was taught to pray to him.", "carving.ossuary.5": "A holy thing, or nothing. That's ours. I've said it a thousand times without knowing what it meant.", "carving.vaults.5": "The heart kept apart. It's in our oldest book. I thought it was a metaphor.", "carving.root.3": "He listened to this. We all did. We call it prayer." } },
  lowertown: { name: "Of the lower town", what: "born on the water: the party wades as if dry-shod while they stand",
    lines: { "carving.catacombs.5": "Rose and never fell. That's what they told us children. The old ones never said it.", "carving.drowned.1": "This was my street. Or it would have been.", "carving.drowned.2": "Let in. My grandfather used to say it to himself. Let in. Let in. We thought he was mad.", "carving.drowned.3": "Marguerite. I had an aunt Marguerite. Every family on the water did.", "guardian.knight": "The captain. We still say that: as stubborn as the captain. We stopped saying why." } },
  nobody: { name: "Nobody from nowhere", what: "no past that anyone remembers: +1 Luck, and nothing to say at the walls but the once",
    lines: { "carving.root.4": "It dreamed all this. Then it dreamed me, too, I suppose. That's a kind of belonging." } },
};
delete CM.ORIGINS.dwarffriend.lines["carving.catacombs.8"];
// banter by situation, said once at a time, never in a fight: {a} and {b} are a bonded pair, or two who stand
CM.BANTER2 = {
  camp: ["{a} mends {b}'s cloak by the fire without being asked, and badly.", "{b} tells the one about the troll and the chair. {a} has heard it. {a} laughs anyway.", "{a} and {b} split the last ration down the middle and both pretend the other half was bigger.", "{b} asks {a} what they'll do, after. {a} says: sleep. {b} says: me too. Neither of them means it.",
    "{a} counts the party on their fingers. Four. {a} does it again.", "{b} hums the queen's song without knowing where they heard it. {a} tells them to stop.", "{a} cleans a blade that is already clean. {b} watches, and understands.", "{b} says the camp fire is the best thing in the world. {a} says the second best. Neither says what the first is."],
  guardian: ["{a} sits down on the floor where it fell. {b} sits beside them. Nobody says anything for a while.", "{b}: 'That was a big one.' {a}: 'They get bigger.' {b}: 'I know. I was being kind.'", "{a} wipes {b}'s face with a sleeve. {b} lets them.", "{b} asks if anyone saw what it said at the end. {a} says: yes. {a} doesn't repeat it.",
    "{a} picks the relic up and puts it down again. {b} picks it up and keeps it.", "{b}: 'It talked.' {a}: 'They all talk.' {b}: 'Not like that.'"],
  carving: ["{b} reads it over {a}'s shoulder and says nothing, which for {b} is a great deal.", "{a}: 'Do you believe that?' {b}: 'I believe someone carved it.'", "{b} runs a hand over the letters. 'A left hand,' {b} says. 'Hurrying.'", "{a} says the walls get worse the lower you go. {b} says they get truer. {a} says that's what worse means.",
    "{b} wants to carve something too. {a} says: what? {b} thinks about it for a long time."],
  water: ["{a} says the water's cold. {b} says it's not the cold that worries them.", "{b} keeps {a}'s torch dry, which takes both hands and all of {b}'s attention.", "{a} tries not to think about the lower town's barred doors. {b} can tell.", "{b} says there are fish. {a} says those aren't fish."],
  down: ["{a} carries {b}'s pack as well as their own and says nothing about it.", "{b} keeps looking back at the one who isn't walking. {a} takes {b}'s elbow.", "{a} says they'll be all right. {b} says: yes. {a} says: I mean it. {b} says: I know you do.", "{b} starts to say something about the camp, and stops, and {a} finishes it for them."],
};
CM.JOKES = ["{a}: 'Oak, was it?' {b}: 'Shut up.' It is the fortieth time. It is still funny.", "{b} points at every chair they pass. {a} has stopped reacting, which only makes it better.", "{a}: 'If you see a troll -' {b}: '- find a chair. Yes. Thank you.'"];
// last words, by calling, by origin, and by the band they fell in (the first that fits)
CM.LAST_WORDS = {
  cls: { Knight: "Hold the line.", Paladin: "I'm not afraid. I thought I would be.", Rogue: "Check my pockets. Not for you - for the next ones.", Ranger: "I never missed. Remember that I never missed.", Cleric: "I've nothing left for myself. Good. That's how it should go.", Mage: "The walls were right. Read the walls.",
    Druid: "It was only hungry.", Bard: "I'd have liked a better last line.", Monk: "Empty hands.", Necromancer: "I'll see you again. I mean it kindly.", Artificer: "The box was good work. Damn it." },
  origin: { caerduin: "Grandmother. I looked.", dwarffriend: "Sealed from within.", east: "Tell them in the east it was worth the walk.", order: "Correct. One brings nothing.", lowertown: "Let in. Let in.", nobody: "Say my name at the bottom." },
  band: ["Down. Go down.", "The water's not so cold.", "Loved stone. Yes.", "He remembers. Make sure he remembers.", "Tell the captain.", "It's thinking about me. I can feel it.", "Don't let it have my face.", "Shift's over.", "Keep the bones in order.", "Wake it. Or don't. I don't mind now."],
};
CM.lastWords = function (hero, floor) {
  const o = hero.origin && CM.LAST_WORDS.origin[hero.origin], c = CM.LAST_WORDS.cls[hero.cls];
  const pick = CM.hashSeed(`${hero.name}:${floor}`) % 3;
  return (pick === 0 && o) || (pick <= 1 && c) || CM.LAST_WORDS.band[Math.min(9, Math.floor(Math.max(0, floor - 1) / 5))] || c || o || "...";
};

// the arrays the generators and the riddles still read (views over the table; same order, same lengths)
CM.LORE_KEYS = [];
for (let n = 1; n <= 50; n++) CM.LORE_KEYS.push(`carving.${["catacombs", "vaults", "halls", "palace", "drowned", "fungal", "crystal", "foundry", "ossuary", "root"][Math.floor((n - 1) / 5)]}.${((n - 1) % 5) + 1}`);
CM.LORE = CM.LORE_KEYS.map((k) => CM.LORE_TEXT[k].text);
CM.LORE_EXTRA = Object.values(CM.LORE_TEXT).filter((l) => l.chapter === "odd").sort((a, b) => a.order - b.order).map((l) => l.text);
CM.LORE_ENDLESS = Object.values(CM.LORE_TEXT).filter((l) => l.chapter === "endless").sort((a, b) => a.order - b.order).map((l) => l.text);

// a carving's key, from the value the floor holds
CM.loreKey = function (text) {
  if (typeof text === "string" && text.startsWith("ga:")) text = "g:" + text.slice(3);   // (a lair's carving, after its guardian is gone: the same line, in the past tense)
  if (typeof text === "string" && text.startsWith("g:")) return CM.LORE_TEXT[`guardian.${text.slice(2)}`] ? `guardian.${text.slice(2)}` : null;
  if (typeof text === "string" && text.startsWith("e:")) return `endless.${(Number(text.slice(2)) % CM.LORE_ENDLESS.length) + 1}`;
  if (typeof text === "number" && text >= 0) return CM.LORE_KEYS[Math.min(text, CM.LORE_KEYS.length - 1)];
  if (typeof text === "number") return `odd.${Math.min(-text, CM.LORE_EXTRA.length)}`;
  return null;
};
// the telling a seed chose for a line (the first, without a seed)
CM.telling = function (key, seed) {
  const l = CM.LORE_TEXT[key];
  if (!l) return "";
  if (!seed || l.tellings.length < 2) return l.text;
  return l.tellings[CM.hashSeed(`${seed}:telling:${key}`) % l.tellings.length];
};
// what a carving says: the floor's part of the story, an odd one, a guardian's or the endless dark's
CM.loreText = (text, seed, forced) => (typeof text === "string" && text.startsWith("ga:") && CM.PARLEY[text.slice(3)] && CM.PARLEY[text.slice(3)].after)
  || (forced !== undefined && CM.LORE_TEXT[CM.loreKey(text)] ? CM.LORE_TEXT[CM.loreKey(text)].tellings[forced % CM.LORE_TEXT[CM.loreKey(text)].tellings.length] : CM.telling(CM.loreKey(text), seed));
// the key a journal entry's text belongs to (an older save kept only the words)
CM.keyOfText = function (text) {
  for (const l of Object.values(CM.LORE_TEXT)) if (l.tellings.includes(text)) return l.key;
  return null;
};

// ---- the codex: every chapter, line by line, with what has been read ----
// game.story.read is {key: floor read on}; a line read deeper that contradicts one above strikes the lie through
CM.codex = function (game) {
  const read = Object.assign({}, (game && game.village && game.village.loreRead) || {}, (game && game.story && game.story.read) || {});
  const truths = {};
  for (const l of Object.values(CM.LORE_TEXT)) if (l.contradicts && read[l.key] !== undefined) truths[l.contradicts] = l.key;
  const out = [];
  for (const [id, ch] of Object.entries(CM.CHAPTERS)) {
    const lines = Object.values(CM.LORE_TEXT).filter((l) => l.chapter === id).sort((a, b) => a.order - b.order).map((l) => ({
      key: l.key, order: l.order, floor: l.floor, who: l.who, read: read[l.key] !== undefined, text: read[l.key] !== undefined ? CM.telling(l.key, game && game.seed) : null,
      struck: truths[l.key] || null, truth: truths[l.key] ? CM.telling(truths[l.key]) : null }));
    const done = lines.filter((l) => l.read).length, told = Boolean(game && game.story && game.story.told && game.story.told[id]);
    out.push({ id, name: ch.name, epigraph: ch.epigraph, band: ch.band, lines, done, total: lines.length, told, complete: (done === lines.length && lines.length > 0) || told });
  }
  return out;
};
// the whole story's size, for the budget (words)
CM.loreWords = () => Object.values(CM.LORE_TEXT).reduce((n, l) => n + l.tellings.join(" ").split(/\s+/).length, 0);
// a save from before the codex kept only the journal: the keys are found by their words
CM.storyFromJournal = function (journal) {
  const read = {};
  for (const e of journal || []) { const k = e.key || CM.keyOfText(e.text); if (k) read[k] = e.floor || 0; }
  return { read };
};
