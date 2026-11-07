"use strict";
// Gull Rock and the Drowned Light (UPGRADE_PLAN_81.md, v134.0): a tooth of rock in the sea north-west of home, white
// with gulls, a jetty on its south side and the stump of an old light on its shoulder. The light's last keeper went
// down into the sea caves under it, after a sound he heard in the rock at night; the stair he went down is still open.
// Under it, forty floors: the Sea Caves, the Wreck Galleries, the Pearl Deeps and the Leviathan's Throat - crabs and
// glubs and the drowned; wreckers and salt wights among the ships the rock has eaten; sharks and mantas in the flooded
// halls; and at the bottom, in the dark, the Old Leviathan, which has been dreaming down there longer than the sea.
//   CM.ISLES.gull; its kinds (the Quaternius creatures, 77y-isles.js maps them), its four guardians
{ const key = (x, y) => `${x},${y}`;
  const theme = (name, like, o) => Object.assign({}, CM.THEMES[like], { name, like, floors: [-140, -101] }, o);
  const BANDS = [
    { name: "The Sea Caves", wet: 14, words: "The sea's own caves: the stone wet and green, the floors standing in water, and the boom of the waves somewhere through the rock.", kinds: ["Rock Crab", "Glub", "Squidle", "Drowned Sailor"],
      theme: theme("The Sea Caves", 1, { stone: [84, 98, 94], mortar: [32, 42, 40], floor: [60, 74, 70], ceiling: [42, 52, 52], moss: [60, 140, 120], fog: [0.02, 0.035, 0.04], torch: [0.88, 0.92, 1.0], reach: 5.0, bones: 0.05, photos: "t1", grade: [0.93, 1.0, 1.02] }) },
    { name: "The Wreck Galleries", wet: 6, words: "Ships' timbers in the rock: ribs and keels and a figurehead staring out of a wall. The rock has been eating ships for a long time.", kinds: ["Wrecker", "Drowned Sailor", "Salt Wight", "Rock Crab"],
      theme: theme("The Wreck Galleries", 2, { stone: [98, 80, 62], mortar: [40, 30, 22], floor: [76, 60, 46], ceiling: [52, 40, 30], moss: [110, 100, 60], fog: [0.03, 0.028, 0.022], torch: [1.0, 0.8, 0.55], reach: 5.5, bones: 0.3, photos: "t2", grade: [1.04, 0.98, 0.92] }) },
    { name: "The Pearl Deeps", wet: 24, words: "Blue halls, half under water, the walls nacre-pale and shining. Things swim through the flooded rooms.", kinds: ["Reef Shark", "Manta", "Pearl Glub", "Sea Wind", "Fishfolk"],
      theme: theme("The Pearl Deeps", 6, { stone: [72, 92, 122], mortar: [30, 40, 56], floor: [56, 74, 98], ceiling: [40, 52, 72], moss: [150, 200, 235], fog: [0.015, 0.03, 0.05], torch: [0.8, 0.9, 1.0], reach: 6.0, bones: 0.02, photos: "t3", grade: [0.92, 0.98, 1.08] }) },
    { name: "The Leviathan's Throat", wet: 10, words: "The rock goes dark and red and soft-looking, ridged like the roof of a mouth. Everything down here is very quiet, as if listening.", kinds: ["Fishfolk", "Salt Wight", "Deep Squidle", "Abyssal Glub", "Reef Shark"],
      theme: theme("The Leviathan's Throat", 9, { stone: [74, 40, 48], mortar: [30, 14, 18], floor: [58, 30, 36], ceiling: [40, 20, 24], moss: [170, 60, 80], fog: [0.04, 0.015, 0.02], torch: [1.0, 0.7, 0.65], reach: 4.2, bones: 0.4, photos: "t0", grade: [1.06, 0.94, 0.96] }) } ];
  // the kinds (the window gives each its Quaternius figure; these are their pictures where the figures are off)
  const K = (name, colour, body, head, eyes, extras, speed, o) => Object.assign({ name, colour, body, head, eyes, extras, speed, isle: "gull" }, o);
  const KINDS = [
    K("Rock Crab", "#C0604A", "beast", "round", "#101010", ["claws"], 9, { shape: [1.0, 0.9, 1.3] }),
    K("Glub", "#5AA0C0", "beast", "round", "#FFFFFF", [], 13, { shape: [0.8, 0.8, 0.6], touch: { status: "sleep", chance: 0.1 } }),
    K("Squidle", "#C080C0", "beast", "round", "#FFE060", ["tail"], 12, { shape: [0.9, 1.0, 0.7], ability: "web" }),
    K("Drowned Sailor", "#6A8A88", "ghost", "pale", "#D0F0E8", ["torn"], 8, { undead: true, shape: [1.0, 1.0, 0.8], touch: { status: "sleep", chance: 0.12 } }),
    K("Wrecker", "#8A6A4A", "biped", "hood", "#FFD080", [], 11, { shape: [1.1, 1.15, 0.9], ability: "charge" }),
    K("Salt Wight", "#D8D4C8", "ghost", "skull", "#80E0FF", ["torn"], 10, { undead: true, shape: [1.0, 1.2, 0.9], ability: "howl", touch: { status: "paralysis", chance: 0.12 } }),
    K("Reef Shark", "#5A6A78", "beast", "snout", "#101010", ["tail"], 16, { shape: [1.2, 1.3, 0.8], ability: "savage" }),
    K("Manta", "#3A4A5A", "wide", "round", "#E0E0FF", ["tail"], 14, { shape: [1.2, 0.9, 0.9], ability: "ranged" }),
    K("Pearl Glub", "#E0E0F0", "beast", "round", "#40A0FF", [], 13, { shape: [1.0, 1.0, 1.0], touch: { status: "sleep", chance: 0.15 } }),
    K("Sea Wind", "#A0D8E0", "ghost", "pale", "#FFFFFF", [], 17, { shape: [0.8, 1.0, 0.6], ability: "coward", flees: true }),
    K("Fishfolk", "#4A8A7A", "biped", "snout", "#FFE060", [], 11, { shape: [1.2, 1.2, 1.1], ability: "ranged" }),
    K("Deep Squidle", "#6A3060", "beast", "round", "#FF6060", ["tail"], 13, { shape: [1.2, 1.2, 0.9], ability: "web", touch: { status: "poison", chance: 0.2 } }),
    K("Abyssal Glub", "#203048", "beast", "round", "#FF4040", [], 13, { shape: [1.3, 1.2, 1.1], touch: { status: "sleep", chance: 0.2 } }) ];
  for (const k of KINDS) if (!CM.MONSTERS.some((m) => m.name === k.name)) CM.MONSTERS.push(k);
  // the guardians: a level's worth of strength each (the bands' levels: 3 to 16)
  const G = (id, name, colour, body, level, k, o) => { CM.GUARDIANS[id] = Object.assign({ floor: null, name, colour, body, head: "round", eyes: "#FFF0A0", extras: [], speed: 10, size: 1.0, isle: "gull",
      hp: Math.round(44 * level * k), atk: Math.round(2.6 * level * Math.sqrt(k)), df: Math.round(1.1 * level), xp: Math.round(220 * level * k), gold: Math.round(110 * level * k), abilities: [],
      lair: { name: `Gull Rock, floor ${-100 - o.floor}`, rows: ["#########", "#.......#", "#...B...#", "#.......#", "####D####"] } }, o);
    if (o.relic) CM.BASES[o.relic.name] = Object.assign({}, CM.BASES["Rat King's Crown"] || {}, { id: o.relic.name, kind: o.relic.kind, slot: o.relic.slot, tier: Math.min(9, Math.round(level / 2)), group: "relic" }); };
  G("crabqueen", "The Crab Queen", "#D0503A", "beast", 6, 1.0, { floor: -110, escorts: ["Rock Crab", "Rock Crab"], touch: { status: "paralysis", chance: 0.15 },
    intro: "The floor of the cave moves: a crab the size of a cart, her shell crusted white with barnacles, her claws open. Her children scuttle out from under her.", fall: "The Crab Queen goes over on her back, legs folding, and is still.",
    take: "Among the shells under her: a pearl as big as an eye, and a claw-tip sharp as glass.", relic: { name: "The Queen's Claw", kind: "weapon", slot: "weapon", power: 7, value: 600, props: { relic: true } } });
  G("saltbones", "Captain Saltbones", "#E0DCD0", "tall", 10, 1.0, { floor: -120, escorts: ["Wrecker", "Drowned Sailor"], undead: true, weak: "holy", touch: { status: "sleep", chance: 0.15 },
    intro: "At the end of the gallery, at the wheel of a ship the rock has half swallowed, a captain in a salt-stiff coat turns his skull to look at you. \"Boarders,\" he says, \"at last.\"", fall: "Captain Saltbones falls to pieces across his deck, and his crew stop where they stand.",
    take: "His coat is rotten, but his compass still points - not north. Down.", relic: { name: "Saltbones's Compass", kind: "amulet", slot: "amulet", power: 6, value: 900, props: { relic: true } } });
  G("pearlwarden", "The Pearl Warden", "#C8D0E8", "wide", 13, 1.05, { floor: -130, escorts: ["Reef Shark", "Manta"], resist: "frost",
    intro: "Something vast and pale lifts off the floor of the flooded hall and turns in the water, wings slow as breath: a manta the size of a house, pearls set in the skin of its back like stars.", fall: "The Pearl Warden settles to the floor and goes dull, and the pearls on its back go out one by one.",
    take: "One pearl stays lit.", relic: { name: "The Warden's Pearl", kind: "amulet", slot: "amulet", power: 8, value: 1300, props: { relic: true } } });
  G("leviathan", "The Old Leviathan", "#304050", "wide", 16, 1.7, { floor: -140, escorts: ["Abyssal Glub", "Deep Squidle"], size: 1.6, resist: "frost", touch: { status: "sleep", chance: 0.25 },
    intro: "The dark at the bottom of the Throat is not empty. It is an eye, closing and opening, as big as a door. The Old Leviathan has been dreaming down here longer than the sea has had a name, and you have woken it.",
    fall: "The Leviathan's eye closes, and the whole rock sighs, and the sea outside goes calm as glass.", take: "Where it lay, a tooth, and in the tooth's root, cold light: the thing the old keeper heard at night.",
    relic: { name: "The Leviathan's Tooth", kind: "weapon", slot: "weapon", power: 12, value: 2400, props: { relic: true, element: "frost" } } });
  // their relics' powers (the powers the rules know, under the relics' own names), and the turn each takes at half its health
  Object.assign(CM.RELIC_POWERS, { "The Queen's Claw": { id: "break", name: "Prise the shell", where: "fight", what: "the chosen foe's defence is halved" },
    "Saltbones's Compass": { id: "unlock", name: "Follow the needle", where: "floor", what: "the needle swings to the nearest locked door on the floor, and it opens" },
    "The Warden's Pearl": { id: "lull", name: "The deep's quiet", where: "fight", what: "half the room sleeps" },
    "The Leviathan's Tooth": { id: "tide", name: "Raise the sea", where: "fight", what: "the hall floods: water underfoot, and every foe chilled" } });
  if (CM.BOSS_PHASES) Object.assign(CM.BOSS_PHASES, { crabqueen: { text: "The Crab Queen rears up and clacks her claws, and the floor boils with her brood.", summon: ["Rock Crab", 2] },
    saltbones: { text: "Captain Saltbones blows a cracked whistle, and his drowned crew climb up over the rail to him.", summon: ["Drowned Sailor", 2] },
    pearlwarden: { text: "The Pearl Warden folds its wings over itself, and the pearls on its back burn white, and close its wounds.", heal: 0.25 },
    leviathan: { text: "The Old Leviathan comes fully awake. The water round it heaves, and the glubs of the abyss come up in it.", atk: 1.3, summon: ["Abyssal Glub", 1] } });
  // the landing
  const SIZE = 29, C = [14, 12], JETTY = [14, 25], MOUTH = [9, 7], LIGHT = [19, 6];
  const landingTheme = Object.assign({}, CM.WOOD_THEME, { name: "Gull Rock", floors: [-100, -100], stone: [96, 100, 104], mortar: [40, 42, 44], floor: [110, 110, 104], tree: false, sky: true, isleLanding: "gull" });
  const makeLanding = (n, seed) => { const grid = [], kinds = {}, ground = {}, things = {}, rooms = [], seen = [];
    for (let y = 0; y < SIZE; y++) { grid.push(new Array(SIZE).fill(1)); for (let x = 0; x < SIZE; x++) kinds[key(x, y)] = "sea"; }
    const open = (x, y, g) => { grid[y][x] = 0; delete kinds[key(x, y)]; ground[key(x, y)] = g; }, solid = (x, y, kind) => { grid[y][x] = 1; kinds[key(x, y)] = kind; delete ground[key(x, y)]; };
    for (let y = 1; y < SIZE - 1; y++) for (let x = 1; x < SIZE - 1; x++) { const h = (CM.hashSeed(`gull:${x},${y}`) % 1000) / 1000, r = ((x - C[0]) / 10) ** 2 + ((y - C[1]) / 9) ** 2 + (h - 0.5) * 0.18;
      if (r <= 1) open(x, y, y >= 17 && Math.abs(x - JETTY[0]) <= 5 ? "sand" : r < 0.55 && h < 0.3 ? "grass" : "rock"); }
    for (let y = 2; y <= 6; y++) for (let x = 3; x <= 25; x++) if (grid[y][x] === 0 && ((x - C[0]) / 10) ** 2 + ((y - C[1]) / 9) ** 2 > 0.5) solid(x, y, (x + y) % 3 ? "scarp" : "denrocktall");   // (the north shoulder: bare rock)
    for (const [x, y] of [[8, 6], [10, 6], [8, 7], [10, 7]]) solid(x, y, "denrock"); solid(MOUTH[0], MOUTH[1], "cavemouth"); solid(MOUTH[0], MOUTH[1] - 1, "cragtall");
    open(MOUTH[0], MOUTH[1] + 1, "rock"); things[key(MOUTH[0], MOUTH[1] + 1)] = { type: "islemouth" };
    solid(LIGHT[0], LIGHT[1], "tower"); for (const [x, y] of [[LIGHT[0], LIGHT[1] + 1], [LIGHT[0] - 1, LIGHT[1] + 1]]) open(x, y, "rock");
    for (let y = 18; y <= JETTY[1]; y++) open(JETTY[0], y, "planks");
    things[key(JETTY[0] - 1, 19)] = { type: "signpost", text: "GULL ROCK. Up the rock: the old light, and the stair the keeper went down. The Wren waits at the jetty's end." };
    for (let y = 0; y < SIZE; y++) for (let x = 0; x < SIZE; x++) if (grid[y][x] === 0) seen.push([x, y]);
    rooms.push({ x0: 0, y0: 0, x1: SIZE - 1, y1: SIZE - 1, name: "Gull Rock" });
    return { number: n, grid, pos: JETTY.slice(), facing: 0, things, features: {}, dark: [], seen, decor: [], special: "landing", isle: "gull", solidDefault: "sea", kinds, ground, rooms }; };
  CM.ISLES.gull = { id: "gull", base: -100, name: "Gull Rock", deep: "The Drowned Light", levels: [3, 16], bands: BANDS, guardians: ["crabqueen", "saltbones", "pearlwarden", "leviathan"], landingTheme, makeLanding,
    mouthFront: [MOUTH[0], MOUTH[1] + 1], jetty: JETTY.slice(), light: LIGHT, ship: [JETTY[0] + 2.45, JETTY[1] - 0.5], shipYaw: Math.PI,
    atBerth: ([x, y]) => x === JETTY[0] && y >= JETTY[1] - 2 && y <= JETTY[1],
    arrive: "The Wren comes in under the rock with a thousand gulls screaming over her, and ties up at the jetty. Gull Rock: bare stone, white with birds, and on its shoulder the stump of an old light.",
    mouthWords: "The keeper's stair: steps cut down into the rock, wet, going round and down into the sound of the sea. Somewhere below, the keeper's lantern is still lying where he dropped it." };
  if (!CM.SEA_OPEN.includes("gull")) CM.SEA_OPEN.push("gull");
}
