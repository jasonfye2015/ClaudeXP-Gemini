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

// the arrays the generators and the riddles still read (views over the table; same order, same lengths)
CM.LORE_KEYS = [];
for (let n = 1; n <= 50; n++) CM.LORE_KEYS.push(`carving.${["catacombs", "vaults", "halls", "palace", "drowned", "fungal", "crystal", "foundry", "ossuary", "root"][Math.floor((n - 1) / 5)]}.${((n - 1) % 5) + 1}`);
CM.LORE = CM.LORE_KEYS.map((k) => CM.LORE_TEXT[k].text);
CM.LORE_EXTRA = Object.values(CM.LORE_TEXT).filter((l) => l.chapter === "odd").sort((a, b) => a.order - b.order).map((l) => l.text);
CM.LORE_ENDLESS = Object.values(CM.LORE_TEXT).filter((l) => l.chapter === "endless").sort((a, b) => a.order - b.order).map((l) => l.text);

// a carving's key, from the value the floor holds
CM.loreKey = function (text) {
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
CM.loreText = (text, seed) => CM.telling(CM.loreKey(text), seed);
// the key a journal entry's text belongs to (an older save kept only the words)
CM.keyOfText = function (text) {
  for (const l of Object.values(CM.LORE_TEXT)) if (l.tellings.includes(text)) return l.key;
  return null;
};

// ---- the codex: every chapter, line by line, with what has been read ----
// game.story.read is {key: floor read on}; a line read deeper that contradicts one above strikes the lie through
CM.codex = function (game) {
  const read = (game && game.story && game.story.read) || {};
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
