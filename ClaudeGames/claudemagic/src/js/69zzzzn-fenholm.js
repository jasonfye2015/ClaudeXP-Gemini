"use strict";
// The Fenholm and the Sunken Barrow (UPGRADE_PLAN_81.md, v135.0): low green islands to the south-west, more water than
// land, joined by plank walks on stilts; the fen-folk's huts stand shut on their poles, and nobody comes out. On the
// biggest island, a long barrow of grey stones grown over with moss, and in its end a door that was sealed once and has
// been opened from the inside. Under it, forty floors: the Reedways, the Eel Warrens, the Barrow-halls and the Mire
// Heart - frogs as big as dogs, mushnubs and blobs, bees and wasps of the fen, golelings of the bog, barrow wights; the
// Mushroom King, Old Gulp, the Barrow-King, and at the bottom the Mire Mother, from whom the whole fen grows.
{ const key = (x, y) => `${x},${y}`, KIT = CM.ISLE_KIT, I = { id: "fen", base: -200, name: "The Fenholm", deep: "The Sunken Barrow", levels: [8, 22] };
  const K = (...a) => KIT.kind("fen", ...a);
  K("Bog Frog", "#5A8A3A", "beast", "round", "#FFE040", [], 12, { shape: [1.1, 1.0, 0.8], touch: { status: "poison", chance: 0.15 } });
  K("Green Blob", "#6AB050", "beast", "round", "#101010", [], 8, { shape: [1.2, 0.8, 0.6] });
  K("Fen Adder", "#4A6A30", "beast", "snout", "#FF4040", ["tail"], 15, { shape: [0.8, 1.1, 0.6], touch: { status: "poison", chance: 0.3 } });
  K("Marsh Wasp", "#C8A030", "beast", "round", "#101010", [], 17, { shape: [0.7, 1.0, 0.5], touch: { status: "poison", chance: 0.2 } });
  K("Mushnub", "#C06A4A", "beast", "round", "#FFFFFF", [], 9, { shape: [1.0, 0.9, 0.9], touch: { status: "sleep", chance: 0.15 } });
  K("Armabee", "#D0A040", "beast", "round", "#101010", [], 15, { shape: [0.9, 1.0, 1.2] });
  K("Bramble Blob", "#4A8A3A", "beast", "round", "#FFFFFF", ["claws"], 8, { shape: [1.3, 1.0, 1.0], ability: "web" });
  K("Barrow Wight", "#A0B898", "ghost", "pale", "#C0FF80", ["torn"], 10, { undead: true, shape: [1.0, 1.1, 0.9], ability: "howl", touch: { status: "paralysis", chance: 0.12 } });
  K("Mushnub Elder", "#A04A3A", "beast", "round", "#FFFF80", [], 9, { shape: [1.4, 1.1, 1.1], touch: { status: "sleep", chance: 0.25 } });
  K("Bog Goleling", "#6A7A50", "wide", "round", "#80FF80", [], 7, { shape: [1.5, 1.2, 1.5] });
  K("Thornback", "#7AA050", "biped", "round", "#FFFF60", ["claws"], 10, { shape: [1.2, 1.2, 1.2], ability: "charge" });
  K("Pink Blob", "#E080A0", "beast", "round", "#101010", [], 9, { shape: [1.5, 1.0, 0.9], touch: { status: "sleep", chance: 0.2 } });
  K("Armoured Bee", "#E0B040", "beast", "round", "#FF4040", [], 15, { shape: [1.1, 1.3, 1.4] });
  K("Elder Goleling", "#4A5A3A", "wide", "round", "#C0FF60", [], 7, { shape: [1.8, 1.4, 1.7] });
  K("Bog Troll", "#5A6A40", "biped", "snout", "#FFE040", [], 9, { shape: [1.6, 1.4, 1.0], ability: "stun" });
  const theme = (name, like, o) => KIT.theme(I, name, like, o);
  I.bands = [
    { name: "The Reedways", wet: 22, words: "Low tunnels through peat and root, the floors standing in brown water, reeds growing in the dark where no reed should.", kinds: ["Bog Frog", "Green Blob", "Fen Adder", "Marsh Wasp"],
      theme: theme("The Reedways", 5, { stone: [74, 80, 54], mortar: [32, 34, 20], floor: [56, 60, 38], ceiling: [40, 44, 28], moss: [110, 160, 60], fog: [0.03, 0.04, 0.02], torch: [0.92, 1.0, 0.75], reach: 5.0, bones: 0.04, photos: "t1", grade: [0.98, 1.03, 0.92] }) },
    { name: "The Eel Warrens", wet: 12, words: "Burrows in the clay, round and slick, and the smell of eels. Things hum in the walls.", kinds: ["Mushnub", "Armabee", "Bramble Blob", "Bog Frog", "Eel"],
      theme: theme("The Eel Warrens", 1, { stone: [92, 78, 60], mortar: [40, 32, 22], floor: [70, 58, 42], ceiling: [50, 42, 30], moss: [120, 120, 60], fog: [0.035, 0.03, 0.02], torch: [1.0, 0.86, 0.6], reach: 5.0, bones: 0.08, photos: "t1", grade: [1.03, 1.0, 0.92] }) },
    { name: "The Barrow-halls", wet: 3, words: "Dressed stone, very old: the barrow's own halls, the dead of the fen laid in niches along them. Not all of them are lying down.", kinds: ["Barrow Wight", "Mushnub Elder", "Bog Goleling", "Thornback"],
      theme: theme("The Barrow-halls", 8, { stone: [104, 108, 96], mortar: [46, 48, 40], floor: [80, 84, 72], ceiling: [56, 58, 50], moss: [120, 150, 100], fog: [0.03, 0.035, 0.03], torch: [0.9, 1.0, 0.85], reach: 5.0, bones: 0.6, photos: "t0", grade: [0.97, 1.02, 0.97] }) },
    { name: "The Mire Heart", wet: 30, words: "The barrow gives way to the fen's own heart: soft walls that breathe, green light, water everywhere, and a slow pulse in the floor.", kinds: ["Pink Blob", "Armoured Bee", "Elder Goleling", "Bog Troll"],
      theme: theme("The Mire Heart", 5, { stone: [60, 92, 50], mortar: [24, 40, 20], floor: [44, 70, 36], ceiling: [30, 50, 24], moss: [150, 230, 90], fog: [0.025, 0.05, 0.02], torch: [0.85, 1.0, 0.65], reach: 4.5, bones: 0.1, photos: "t1", grade: [0.94, 1.06, 0.9] }) } ];
  const G = (id, name, colour, body, level, k, depth, o) => KIT.guardian(I, id, name, colour, body, level, k, depth, o);
  G("mushking", "The Mushroom King", "#C04030", "biped", 11, 1.0, 10, { escorts: ["Mushnub", "Mushnub"], touch: { status: "sleep", chance: 0.2 },
    intro: "In a hall of pale stalks a king sits on a throne of shelf-fungus, his cap a crown, his court of mushnubs swaying round him. He stands, and spores go up like smoke.", fall: "The Mushroom King folds up on his throne and goes to dust, and his court stops swaying.",
    take: "His cap is soft rot already; but the crown-ring under it is gold.", relic: { name: "The Spore-King's Ring", kind: "ring", slot: "ring", power: 7, value: 1100, props: { relic: true } },
    power: { id: "still", name: "Breathe the spores", where: "fight", what: "the chosen foe is held two turns" }, phase: { text: "The Mushroom King shakes his cap, and the spores fall like snow on the front row.", sleepFront: true } });
  G("oldgulp", "Old Gulp", "#4A7A2A", "beast", 15, 1.0, 20, { escorts: ["Bog Frog", "Fen Adder"], touch: { status: "poison", chance: 0.25 },
    intro: "The pool in the middle of the warren isn't a pool. It opens two yellow eyes and a mouth as wide as a door, and a frog older than the fen-folk heaves itself out of the water at you.", fall: "Old Gulp sinks back into his pool, and the water closes over him.",
    take: "On the bottom of his pool, where he's sat for a hundred years: a golden bell off a fen-folk boat, and a tongue-ring of bronze.", relic: { name: "Old Gulp's Bell", kind: "amulet", slot: "amulet", power: 8, value: 1400, props: { relic: true } },
    power: { id: "swarm", name: "Ring for the fen", where: "fight", what: "the frogs of the fen answer: every foe bitten" }, phase: { text: "Old Gulp croaks, and the walls croak back: his children come up out of the water.", summon: ["Bog Frog", 2] } });
  G("barrowking", "The Barrow-King", "#B8C0A8", "tall", 19, 1.05, 30, { escorts: ["Barrow Wight", "Barrow Wight"], undead: true, weak: "holy", touch: { status: "paralysis", chance: 0.15 },
    intro: "At the barrow's heart, on a bier of green stone, the first king of the fen sits up in his mask of bone and reaches for the sword laid on his chest.", fall: "The Barrow-King lies down again on his bier, and folds his hands, and is quiet.",
    take: "The sword he reached for: bronze, green as the fen, and still sharp.", relic: { name: "The Barrow-King's Blade", kind: "weapon", slot: "weapon", power: 11, value: 2000, props: { relic: true } },
    power: { id: "unlock", name: "The king's key", where: "floor", what: "the nearest locked door on the floor opens for its old king" }, phase: { text: "The Barrow-King raises his blade, and every wight in the barrow stands up in its niche.", summon: ["Barrow Wight", 2] } });
  G("miremother", "The Mire Mother", "#2A5A2A", "wide", 22, 1.7, 40, { escorts: ["Elder Goleling", "Pink Blob"], size: 1.6, touch: { status: "poison", chance: 0.25 }, resist: "poison",
    intro: "The Mire Heart's last chamber is all one living thing: green, spined, vast, breathing. The Mire Mother, from whom the whole fen grows, opens and looks at you with every part of herself at once.",
    fall: "The Mire Mother shrinks in on herself and goes still and grey, and far above, out on the Fenholm, every reed in the fen bows at once.", take: "In what's left of her, a seed the size of a fist, warm, and beating very slowly.",
    relic: { name: "The Mire Seed", kind: "amulet", slot: "amulet", power: 12, value: 2600, props: { relic: true } },
    power: { id: "regrow", name: "Plant it", where: "both", what: "a fallen hero rises, to one health" }, phase: { text: "The Mire Mother splits along her spines and breathes out the fen: everything in the room is wet and green and growing, and her children come.", heal: 0.2, summon: ["Pink Blob", 1] } });
  I.guardians = ["mushking", "oldgulp", "barrowking", "miremother"];
  // the landing: islands in the water, plank walks on stilts, the fen-folk's huts, the barrow
  const SIZE = 31, JETTY = [15, 27], MOUTH = [9, 8];
  I.landingTheme = Object.assign({}, CM.WOOD_THEME, { name: "The Fenholm", floors: [I.base, I.base], tree: false, sky: true, isleLanding: "fen" });
  I.makeLanding = (n) => { const grid = [], kinds = {}, ground = {}, things = {}, features = {}, decor = [], seen = [];
    for (let y = 0; y < SIZE; y++) { grid.push(new Array(SIZE).fill(1)); for (let x = 0; x < SIZE; x++) kinds[key(x, y)] = "sea"; }
    const open = (x, y, g) => { grid[y][x] = 0; delete kinds[key(x, y)]; ground[key(x, y)] = g; }, solid = (x, y, kind) => { grid[y][x] = 1; kinds[key(x, y)] = kind; delete ground[key(x, y)]; };
    const fen = (x, y) => { open(x, y, "moss"); decor.push({ kind: "water", x, y }); features[key(x, y)] = { type: "river" }; };
    const isles = [[10, 9, 6, 4], [21, 11, 4, 3], [15, 19, 5, 3], [24, 21, 3, 2]];
    for (let y = 2; y < SIZE - 2; y++) for (let x = 2; x < SIZE - 2; x++) { const h = (CM.hashSeed(`fen:${x},${y}`) % 1000) / 1000, inIsle = isles.some(([cx, cy, rx, ry]) => ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 + (h - 0.5) * 0.2 <= 1), nearIsle = isles.some(([cx, cy, rx, ry]) => ((x - cx) / (rx + 3)) ** 2 + ((y - cy) / (ry + 3)) ** 2 <= 1);
      if (inIsle) open(x, y, h < 0.75 ? "grass" : "moss"); else if (nearIsle) fen(x, y); }
    const walk = (a, b) => { let [x, y] = a; while (x !== b[0] || y !== b[1]) { if (x !== b[0]) x += Math.sign(b[0] - x); else y += Math.sign(b[1] - y); if (grid[y][x] !== 0 || features[key(x, y)]) { open(x, y, "planks"); delete features[key(x, y)]; for (let i = decor.length - 1; i >= 0; i--) if (decor[i].x === x && decor[i].y === y) decor.splice(i, 1); } } };
    walk([JETTY[0], JETTY[1]], [15, 19]); walk([15, 19], [10, 12]); walk([15, 19], [21, 13]); walk([18, 19], [24, 21]);
    for (let y = 22; y <= JETTY[1]; y++) { open(JETTY[0], y, "planks"); delete features[key(JETTY[0], y)]; for (let i = decor.length - 1; i >= 0; i--) if (decor[i].x === JETTY[0] && decor[i].y === y) decor.splice(i, 1); }
    for (let x = 6; x <= 12; x++) for (let y = 6; y <= 7; y++) solid(x, y, (x + y) % 2 ? "denrocklow" : "denrock"); solid(MOUTH[0], MOUTH[1] - 1, "denrocktall"); solid(MOUTH[0], 7, "cavemouth"); open(MOUTH[0], MOUTH[1], "dirt"); things[key(...MOUTH)] = { type: "islemouth" };
    for (const [x, y] of [[21, 10], [22, 10]]) solid(x, y, "cabin"); solid(21, 11, "cabindoor"); for (const [x, y] of [[14, 18], [16, 18]]) solid(x, y, "cabin");
    things[key(JETTY[0], 21)] = { type: "signpost", text: "THE FENHOLM. North by the walks: the barrow. The fen-folk's huts are shut, and will stay shut. Keep to the planks." };
    for (let y = 0; y < SIZE; y++) for (let x = 0; x < SIZE; x++) if (grid[y][x] === 0) seen.push([x, y]);
    return { number: n, grid, pos: JETTY.slice(), facing: 0, things, features, dark: [], seen, decor, special: "landing", isle: "fen", solidDefault: "sea", kinds, ground, rooms: [{ x0: 0, y0: 0, x1: SIZE - 1, y1: SIZE - 1, name: "The Fenholm" }] }; };
  Object.assign(I, { mouthFront: MOUTH.slice(), jetty: JETTY.slice(), ship: [JETTY[0] + 2.45, JETTY[1] - 0.5], shipYaw: Math.PI, atBerth: ([x, y]) => x === JETTY[0] && y >= JETTY[1] - 2 && y <= JETTY[1],
    arrive: "The Wren feels her way in between the islands with a man in the bows sounding the depth, and ties up at a jetty of black poles. The Fenholm: reeds, still water, huts on stilts with their shutters closed, and a long barrow of grey stones on the largest island.",
    mouthWords: "The barrow's end: a door of one great slab, sealed with clay once - and the clay is broken outward. Steps go down into the peat, and there's water on every one." });
  CM.ISLES.fen = I; if (!CM.SEA_OPEN.includes("fen")) CM.SEA_OPEN.push("fen");
}
