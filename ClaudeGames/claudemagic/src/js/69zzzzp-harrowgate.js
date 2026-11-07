"use strict";
// Harrowgate and its Undercity (UPGRADE_PLAN_81.md, v137.0): the port on the Mainland's coast where the Wren was built
// - stone quays, warehouses, the harbour wall, a whole continent going away inland behind it - and under the old town,
// older towns: the Undercity. Forty floors: the Sewers, the Thieves' Warrens, the Old Empire that was here before the
// port, and at the bottom the Hollow Throne, where something sits that came from very far away and wears the empire's
// crown. Rats and grublings, sludge and orc raiders; shadow blades, cutpurses and hedge mages; the empire's legion
// still in its bones, its tomb mages and the yetis of its menagerie; and star-things, void blobs, hollow knights and
// moon hares. The Sewer King, the Night Mistress, the Last Legate, and the Hollow King.
{ const key = (x, y) => `${x},${y}`, KIT = CM.ISLE_KIT, I = { id: "main", base: -400, name: "Harrowgate", deep: "The Undercity", levels: [20, 35] };
  const K = (...a) => KIT.kind("main", ...a);
  K("Sewer Rat", "#5A4A3A", "beast", "snout", "#FF4040", ["tail"], 15, { shape: [0.9, 1.0, 0.7], touch: { status: "poison", chance: 0.2 } });
  K("Grubling", "#6A8A4A", "biped", "ears", "#FFE040", [], 12, { shape: [0.9, 1.0, 0.8] });
  K("Sludge", "#5A4A2A", "beast", "round", "#C0FF40", [], 7, { shape: [1.6, 1.0, 1.0], touch: { status: "poison", chance: 0.25 } });
  K("Orc Raider", "#4A6A3A", "biped", "tusks", "#FF4040", [], 11, { shape: [1.3, 1.3, 1.0], ability: "charge" });
  K("Shadow Blade", "#2A2430", "biped", "hood", "#FFFFFF", [], 18, { shape: [1.0, 1.4, 0.8], ability: "savage" });
  K("Cutpurse", "#3A3440", "biped", "hood", "#FFE060", [], 17, { shape: [0.8, 1.0, 0.7], ability: "coward", flees: true });
  K("Hedge Mage", "#4A3A7A", "biped", "hood", "#80C0FF", [], 10, { shape: [0.9, 1.3, 0.7], ability: "ranged", touch: { status: "curse", chance: 0.15 } });
  K("Legion Bones", "#D8D0C0", "biped", "skull", "#80E0FF", [], 9, { undead: true, shape: [1.2, 1.2, 1.3], weak: "holy" });
  K("Tomb Mage", "#C8C0B0", "biped", "skull", "#C080FF", ["torn"], 10, { undead: true, shape: [1.0, 1.4, 0.9], ability: "ranged", touch: { status: "curse", chance: 0.2 } });
  K("Menagerie Yeti", "#D8E0E8", "wide", "round", "#4080FF", ["claws"], 10, { shape: [1.7, 1.4, 1.1], ability: "stun" });
  K("Skull Orc", "#3A5A2A", "biped", "skull", "#FF4040", [], 11, { shape: [1.5, 1.4, 1.2], ability: "howl" });
  K("Star-thing", "#6A5AA0", "biped", "round", "#40FFC0", [], 13, { shape: [1.3, 1.5, 1.0], ability: "ranged", touch: { status: "paralysis", chance: 0.15 } });
  K("Void Blob", "#3A2A5A", "beast", "round", "#C080FF", [], 9, { shape: [1.6, 1.2, 1.2], touch: { status: "blind", chance: 0.2 } });
  K("Hollow Knight", "#2A2A34", "biped", "helm", "#A0A0FF", [], 10, { undead: true, shape: [1.6, 1.5, 1.6] });
  K("Moon Hare", "#E8E4F0", "beast", "ears", "#FF2020", [], 19, { shape: [1.2, 1.6, 0.9], ability: "savage" });
  const theme = (name, like, o) => KIT.theme(I, name, like, o);
  I.bands = [
    { name: "The Sewers", wet: 26, words: "Brick tunnels and the stink of the whole port running through them. Something big moves in the water ahead, and then something bigger.", kinds: ["Sewer Rat", "Grubling", "Sludge", "Orc Raider"],
      theme: theme("The Sewers", 1, { stone: [92, 70, 58], mortar: [40, 30, 24], floor: [70, 58, 46], ceiling: [50, 40, 32], moss: [110, 120, 60], fog: [0.04, 0.035, 0.025], torch: [1.0, 0.86, 0.6], reach: 5.0, bones: 0.15, photos: "t1", grade: [1.02, 0.99, 0.92] }) },
    { name: "The Thieves' Warrens", wet: 4, words: "Cellars knocked through into cellars: a whole hidden town of passages, chalk marks on the walls, tripwires, and people who don't want to be found.", kinds: ["Shadow Blade", "Cutpurse", "Hedge Mage", "Orc Raider"],
      theme: theme("The Thieves' Warrens", 2, { stone: [82, 76, 70], mortar: [34, 30, 28], floor: [62, 56, 50], ceiling: [42, 38, 34], moss: [90, 90, 80], fog: [0.03, 0.03, 0.03], torch: [0.95, 0.85, 0.65], reach: 4.5, bones: 0.08, photos: "t2", grade: [0.98, 0.97, 0.98] }) },
    { name: "The Old Empire", wet: 0, words: "Marble, under it all: the city that was here before the port, its streets and colonnades buried and kept. Its legion never stood down.", kinds: ["Legion Bones", "Tomb Mage", "Menagerie Yeti", "Skull Orc"],
      theme: theme("The Old Empire", 3, { stone: [150, 144, 132], mortar: [70, 66, 58], floor: [120, 114, 104], ceiling: [84, 80, 72], moss: [180, 170, 140], fog: [0.025, 0.025, 0.03], torch: [0.9, 0.9, 1.0], reach: 6.0, bones: 0.4, photos: "t0", grade: [1.0, 1.0, 1.04] }) },
    { name: "The Hollow Throne", wet: 0, words: "The deepest hall of the empire, and the empire never built it: the stone is wrong, the angles are wrong, and the stars show through the floor.", kinds: ["Star-thing", "Void Blob", "Hollow Knight", "Moon Hare"],
      theme: theme("The Hollow Throne", 6, { stone: [60, 50, 90], mortar: [24, 18, 40], floor: [44, 36, 70], ceiling: [30, 24, 50], moss: [160, 120, 255], fog: [0.02, 0.015, 0.045], torch: [0.75, 0.75, 1.0], reach: 5.0, bones: 0.1, photos: "t3", grade: [0.92, 0.9, 1.1] }) } ];
  const G = (id, name, colour, body, level, k, depth, o) => KIT.guardian(I, id, name, colour, body, level, k, depth, o);
  G("sewerking", "The Sewer King", "#4A6A3A", "wide", 24, 1.0, 10, { escorts: ["Orc Raider", "Sewer Rat"], touch: { status: "poison", chance: 0.2 },
    intro: "Where all the sewers of the port come together, on a throne of drift and broken barrels, an orc as broad as a cart wears a crown made of a chamber pot, and is not joking.", fall: "The Sewer King topples off his throne into the water, crown and all.",
    take: "His crown is a chamber pot. His sceptre is a ship's belaying pin wrapped in gold leaf, and heavier than it looks.", relic: { name: "The Sewer King's Pin", kind: "weapon", slot: "weapon", power: 11, value: 2200, props: { relic: true } },
    power: { id: "swarm", name: "Call the rats", where: "fight", what: "the sewer's rats pour out for you: every foe bitten" }, phase: { text: "The Sewer King bangs his pin on his throne, and the rats come.", summon: ["Sewer Rat", 2] } });
  G("nightmistress", "The Night Mistress", "#4A2A5A", "biped", 28, 1.0, 20, { escorts: ["Shadow Blade", "Cutpurse"], touch: { status: "blind", chance: 0.2 },
    intro: "She is sitting on the edge of a table in the guild's last cellar, a knife in each hand and a mask on her face, and she was expecting you. \"You've cost me a lot of good people,\" she says.", fall: "The Night Mistress steps back into the dark - and doesn't come out of it. Her mask is left on the floor.",
    take: "Her mask, black silk on a frame of silver wire. Through it the dark looks thinner.", relic: { name: "The Night Mistress's Mask", kind: "helm", slot: "helm", power: 11, value: 2400, props: { relic: true } },
    power: { id: "still", name: "Look through it", where: "fight", what: "the chosen foe is held two turns" }, phase: { text: "The Night Mistress whistles, and her blades come out of the walls.", summon: ["Shadow Blade", 2] } });
  G("lastlegate", "The Last Legate", "#D8D0B8", "tall", 32, 1.05, 30, { escorts: ["Legion Bones", "Legion Bones"], undead: true, weak: "holy",
    intro: "On the steps of the buried senate a legate of the old empire stands in bronze and bone, holding the standard of a legion that marched out of the world a thousand years ago. \"Who commands here?\" he asks. \"Report.\"", fall: "The Last Legate goes down on one knee, and lays the standard on the steps, and is still.",
    take: "The standard's eagle, gilt bronze, and on its base a word in the empire's tongue that means both 'faithful' and 'stubborn'.", relic: { name: "The Legion's Eagle", kind: "amulet", slot: "amulet", power: 12, value: 2800, props: { relic: true } },
    power: { id: "prism", name: "Close ranks", where: "fight", what: "the next blow on each hero does half" }, phase: { text: "The Last Legate raises the standard, and the legion stands up out of the floor.", summon: ["Legion Bones", 2], df: 4 } });
  G("hollowking", "The Hollow King", "#3A2A6A", "tall", 35, 1.7, 40, { escorts: ["Star-thing", "Hollow Knight"], size: 1.6, touch: { status: "paralysis", chance: 0.25 },
    intro: "On the Hollow Throne sits a thing from very far away, in the empire's crown. It has been waiting for the empire to come back for a long time. It is not disappointed to see you instead.",
    fall: "The Hollow King folds up into the throne like a coat falling off a chair, and the stars in the floor go out one by one.", take: "The empire's crown, which it wore, rolls to your feet. Inside its rim, scratched by a nail, a map of the stars that's wrong in every particular.",
    relic: { name: "The Crown of the Empire", kind: "helm", slot: "helm", power: 14, value: 3500, props: { relic: true } },
    power: { id: "ring", name: "Speak in the crown's voice", where: "fight", what: "every foe that can be shaken loses its next turn, and the weak run" }, phase: { text: "The Hollow King stands, and the angles of the room go wrong, and its knights step out of them.", atk: 1.3, summon: ["Hollow Knight", 1] } });
  I.guardians = ["sewerking", "nightmistress", "lastlegate", "hollowking"];
  // the landing: the quay, the warehouses, the harbour wall and the old arch into the undercity
  const SIZE = 31, JETTY = [15, 26], MOUTH = [15, 9];
  I.landingTheme = Object.assign({}, CM.WOOD_THEME, { name: "Harrowgate", floors: [I.base, I.base], tree: false, sky: true, isleLanding: "main" });
  I.makeLanding = (n) => { const grid = [], kinds = {}, ground = {}, things = {}, seen = [];
    for (let y = 0; y < SIZE; y++) { grid.push(new Array(SIZE).fill(1)); for (let x = 0; x < SIZE; x++) kinds[key(x, y)] = "sea"; }
    const open = (x, y, g) => { grid[y][x] = 0; delete kinds[key(x, y)]; ground[key(x, y)] = g; }, solid = (x, y, kind) => { grid[y][x] = 1; kinds[key(x, y)] = kind; delete ground[key(x, y)]; };
    for (let y = 0; y <= 20; y++) for (let x = 0; x < SIZE; x++) solid(x, y, "house");   // (the town, going away inland)
    for (let y = 10; y <= 20; y++) for (let x = 2; x <= SIZE - 3; x++) open(x, y, y >= 18 ? "flags" : "cobbles");   // (the quay and the street behind it)
    for (const [x0, x1] of [[3, 7], [10, 12], [18, 20], [23, 27]]) for (let x = x0; x <= x1; x++) for (let y = 11; y <= 13; y++) solid(x, y, y === 13 && x === Math.floor((x0 + x1) / 2) ? "door" : "house");   // (warehouses)
    for (let x = 0; x < SIZE; x++) if (x < 13 || x > 17) solid(x, 9, "townwall"); for (let x = 13; x <= 17; x++) solid(x, 8, "townwall");
    solid(MOUTH[0], 8, "cavemouth"); open(...MOUTH, "flags"); open(MOUTH[0] - 1, 9, "flags"); open(MOUTH[0] + 1, 9, "flags"); things[key(...MOUTH)] = { type: "islemouth" };
    for (let y = 21; y <= JETTY[1]; y++) open(JETTY[0], y, "planks");
    things[key(JETTY[0] + 1, 19)] = { type: "signpost", text: "HARROWGATE, THE OLD QUAY. The town is shut to strangers this season (sickness, says the harbourmaster). The old arch under the wall goes down to the Undercity: at your own risk, by order." };
    for (let y = 0; y < SIZE; y++) for (let x = 0; x < SIZE; x++) if (grid[y][x] === 0) seen.push([x, y]);
    return { number: n, grid, pos: JETTY.slice(), facing: 0, things, features: {}, dark: [], seen, decor: [], special: "landing", isle: "main", solidDefault: "sea", kinds, ground, rooms: [{ x0: 0, y0: 0, x1: SIZE - 1, y1: SIZE - 1, name: "Harrowgate" }] }; };
  Object.assign(I, { mouthFront: MOUTH.slice(), jetty: JETTY.slice(), ship: [JETTY[0] + 2.45, JETTY[1] - 0.5], shipYaw: Math.PI, atBerth: ([x, y]) => x === JETTY[0] && y >= JETTY[1] - 2 && y <= JETTY[1],
    arrive: "Two days out of sight of land, and then the Mainland: a coast going away north and south as far as you can see, and Harrowgate on it, roofs climbing up from a harbour full of masts. The Wren ties up at the old quay. Somewhere behind all those roofs is a whole continent.",
    mouthWords: "An arch in the old harbour wall, older than the wall, with steps going down. The port's sewers run into it - and so do older things than sewers." });
  CM.ISLES.main = I; if (!CM.SEA_OPEN.includes("main")) CM.SEA_OPEN.push("main");
}
