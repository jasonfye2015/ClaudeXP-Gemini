"use strict";
// Emberreach and the Ember Halls (UPGRADE_PLAN_81.md, v136.0): a mountain in the sea to the south-east that smokes on
// still days - black sand, steam out of cracks in the rock, hot springs, and high on its flank a mouth in the stone with
// a red light in it. Under the mountain, forty floors: the Ash Tunnels; the Lost World, a jungle grown up in a cavern
// lit by the magma, where beasts the rest of the world forgot still walk; the Forge-temple of the lizard-priests and
// their demons; and the Molten Heart. Imps, hounds and magma blobs; raptors, horned and plated and long-necked beasts;
// drakelings, demons and the priests; the Cinder Prince, the Tyrant, the Forge-Priest, and the Ember Dragon.
{ const key = (x, y) => `${x},${y}`, KIT = CM.ISLE_KIT, I = { id: "ember", base: -300, name: "Emberreach", deep: "The Ember Halls", levels: [14, 30] };
  const K = (...a) => KIT.kind("ember", ...a);
  K("Cinder Imp", "#C04020", "biped", "round", "#FFE060", [], 15, { shape: [0.8, 1.1, 0.7], touch: { status: "blind", chance: 0.15 } });
  K("Ember Hound", "#3A2A24", "beast", "snout", "#FF6020", ["tail"], 16, { shape: [1.0, 1.2, 0.8], ability: "savage" });
  K("Magma Blob", "#E07030", "beast", "round", "#FFFF80", [], 8, { shape: [1.4, 1.0, 1.1], touch: { status: "blind", chance: 0.2 } });
  K("Ash Goleling", "#4A4440", "wide", "round", "#FF8040", [], 7, { shape: [1.5, 1.2, 1.6] });
  K("Raptor", "#6A8A4A", "beast", "snout", "#FFE040", ["tail"], 18, { shape: [1.0, 1.3, 0.8], ability: "savage" });
  K("Crestback", "#8A9A5A", "beast", "snout", "#101010", ["tail"], 12, { shape: [1.3, 1.0, 1.0], ability: "howl" });
  K("Platehide", "#7A8A5A", "wide", "snout", "#101010", ["tail"], 8, { shape: [1.6, 1.2, 1.7] });
  K("Hornface", "#8A6A4A", "wide", "snout", "#101010", ["tail"], 10, { shape: [1.6, 1.3, 1.5], ability: "charge" });
  K("Longneck", "#7A9A6A", "wide", "snout", "#101010", ["tail"], 7, { shape: [2.0, 1.1, 1.2], ability: "stun" });
  K("Lizard Priest", "#5A8A6A", "biped", "snout", "#FFD040", [], 11, { shape: [1.2, 1.2, 1.0], ability: "ranged" });
  K("Blue Demon", "#3A4AA0", "biped", "horns", "#FFFFFF", ["claws"], 12, { shape: [1.4, 1.4, 1.1], touch: { status: "curse", chance: 0.15 } });
  K("Drakeling", "#C04A2A", "beast", "snout", "#FFE060", ["tail"], 16, { shape: [1.1, 1.2, 0.9], ability: "ranged", touch: { status: "blind", chance: 0.2 } });
  K("Ember Drake", "#A02A1A", "beast", "snout", "#FFE060", ["tail"], 15, { shape: [1.5, 1.4, 1.2], ability: "ranged", touch: { status: "blind", chance: 0.25 } });
  K("Magma Goleling", "#7A3A20", "wide", "round", "#FFC040", [], 7, { shape: [1.9, 1.4, 1.8], touch: { status: "blind", chance: 0.2 } });
  K("Pit Fiend", "#8A1A1A", "biped", "horns", "#FFE040", ["claws"], 12, { shape: [1.6, 1.5, 1.2], ability: "howl", touch: { status: "curse", chance: 0.2 } });
  const theme = (name, like, o) => KIT.theme(I, name, like, o);
  I.bands = [
    { name: "The Ash Tunnels", wet: 0, words: "Black stone, warm to the touch, ash drifting down from cracks in the roof, and somewhere far below a sound like breathing.", kinds: ["Cinder Imp", "Ember Hound", "Magma Blob", "Ash Goleling"],
      theme: theme("The Ash Tunnels", 7, { stone: [62, 54, 50], mortar: [24, 18, 16], floor: [48, 40, 36], ceiling: [34, 28, 24], moss: [200, 90, 40], fog: [0.04, 0.025, 0.02], torch: [1.0, 0.72, 0.45], reach: 5.0, bones: 0.1, photos: "t2", grade: [1.06, 0.97, 0.9] }) },
    { name: "The Lost World", wet: 6, words: "The tunnel opens on a jungle: ferns taller than a man, hot wet air, red light from the magma under the floor - and tracks in the mud as big as shields.", kinds: ["Raptor", "Crestback", "Platehide", "Hornface", "Longneck"],
      theme: theme("The Lost World", 5, { stone: [70, 84, 54], mortar: [28, 36, 20], floor: [56, 66, 40], ceiling: [40, 48, 28], moss: [140, 210, 80], fog: [0.035, 0.04, 0.02], torch: [1.0, 0.85, 0.6], reach: 5.5, bones: 0.15, photos: "t1", grade: [1.03, 1.04, 0.9] }) },
    { name: "The Forge-temple", wet: 0, words: "Carved halls, gold leaf blackened by heat, altars where something was beaten out on anvils for gods who liked the smell of it.", kinds: ["Lizard Priest", "Blue Demon", "Drakeling", "Cinder Imp"],
      theme: theme("The Forge-temple", 7, { stone: [104, 80, 56], mortar: [44, 32, 20], floor: [80, 62, 42], ceiling: [56, 42, 28], moss: [230, 160, 60], fog: [0.035, 0.025, 0.015], torch: [1.0, 0.78, 0.45], reach: 5.5, bones: 0.1, photos: "t2", grade: [1.07, 0.98, 0.86] }) },
    { name: "The Molten Heart", wet: 0, words: "Bridges of black rock over rivers of light. The air shakes with heat, and every breath tastes of iron.", kinds: ["Ember Drake", "Magma Goleling", "Pit Fiend", "Platehide"],
      theme: theme("The Molten Heart", 9, { stone: [80, 34, 24], mortar: [34, 12, 8], floor: [62, 26, 18], ceiling: [44, 18, 12], moss: [255, 110, 30], fog: [0.05, 0.02, 0.01], torch: [1.0, 0.6, 0.35], reach: 4.5, bones: 0.2, photos: "t0", grade: [1.12, 0.92, 0.82] }) } ];
  const G = (id, name, colour, body, level, k, depth, o) => KIT.guardian(I, id, name, colour, body, level, k, depth, o);
  G("cinderprince", "The Cinder Prince", "#B03020", "biped", 18, 1.0, 10, { escorts: ["Cinder Imp", "Cinder Imp"], touch: { status: "blind", chance: 0.25 }, resist: "fire",
    intro: "At the end of the tunnels a prince of the imps lounges on a heap of cinders like a throne, a crown of red iron on his head, and grins with every tooth he has.", fall: "The Cinder Prince crumbles into the heap he sat on, and the heap goes cold.",
    take: "His crown is still hot enough to hiss in water.", relic: { name: "The Cinder Crown", kind: "helm", slot: "helm", power: 9, value: 1700, props: { relic: true, element: "fire" } },
    power: { id: "reforge", name: "Heat the steel", where: "both", what: "the wearer's weapon takes an edge for the floor (+2)" }, phase: { text: "The Cinder Prince claps his hands, and the cinders round him stand up as imps.", summon: ["Cinder Imp", 2] } });
  G("rextyrant", "The Tyrant", "#5A6A3A", "beast", 22, 1.1, 20, { escorts: ["Raptor", "Raptor"], size: 1.4,
    intro: "The ferns part, and the ground shakes, and shakes again. The king of the lost world bends its head down to look at you with one small, very old eye, and opens its jaws.", fall: "The Tyrant goes down like a tree falling, and the whole jungle goes quiet.",
    take: "One of its teeth, as long as a dagger and sharper.", relic: { name: "The Tyrant's Tooth", kind: "weapon", slot: "weapon", power: 11, value: 2100, props: { relic: true } },
    power: { id: "break", name: "Bite through", where: "fight", what: "the chosen foe's defence is halved" }, phase: { text: "The Tyrant roars, and the raptors in the ferns answer it.", summon: ["Raptor", 2] } });
  G("forgepriest", "The Forge-Priest", "#C0A040", "biped", 26, 1.1, 30, { escorts: ["Lizard Priest", "Blue Demon"], resist: "fire", touch: { status: "blind", chance: 0.2 },
    intro: "Before the great anvil a demon in a priest's gold stands with a hammer as big as a man, and strikes it once on the anvil: the whole temple rings.", fall: "The Forge-Priest falls across his anvil, and the hammer drops from his hand.",
    take: "The hammer is too heavy to carry. The tongs that hung beside it are not, and they were never meant for iron.", relic: { name: "The Priest's Tongs", kind: "shield", slot: "offhand", power: 10, value: 2300, props: { relic: true } },
    power: { id: "prism", name: "Hold the fire", where: "fight", what: "the next blow on each hero does half" }, phase: { text: "The Forge-Priest strikes the anvil again, and he burns white.", atk: 1.4 } });
  G("emberdragon", "The Ember Dragon", "#C02010", "beast", 30, 1.7, 40, { escorts: ["Ember Drake", "Magma Goleling"], size: 1.6, resist: "fire", touch: { status: "blind", chance: 0.3 },
    intro: "In the Molten Heart, on a hoard of melted gold, the Ember Dragon uncoils. Its scales glow at the edges like coals, and when it breathes in, all the light in the room goes into it.",
    fall: "The Ember Dragon falls into its own hoard, and the gold closes over it, and the mountain above stops smoking.", take: "In the hardening gold, a scale from its breast, still glowing.",
    relic: { name: "The Ember Scale", kind: "armor", slot: "armor", power: 13, value: 3000, props: { relic: true, element: "fire" } },
    power: { id: "tide", name: "Breathe out", where: "fight", what: "the hall fills with steam: every foe scalded and slowed" }, phase: { text: "The Ember Dragon breathes in, and in, and its drakes come down out of the dark to it.", atk: 1.3, summon: ["Ember Drake", 1] } });
  I.guardians = ["cinderprince", "rextyrant", "forgepriest", "emberdragon"];
  // the landing: black sand, the mountain's flank, steam, a hot spring, the mouth with a red light in it
  const SIZE = 29, JETTY = [14, 25], MOUTH = [14, 8];
  I.landingTheme = Object.assign({}, CM.WOOD_THEME, { name: "Emberreach", floors: [I.base, I.base], tree: false, sky: true, isleLanding: "ember", fog: [0.02, 0.016, 0.014] });
  I.makeLanding = (n) => { const grid = [], kinds = {}, ground = {}, things = {}, features = {}, decor = [], seen = [];
    for (let y = 0; y < SIZE; y++) { grid.push(new Array(SIZE).fill(1)); for (let x = 0; x < SIZE; x++) kinds[key(x, y)] = "sea"; }
    const open = (x, y, g) => { grid[y][x] = 0; delete kinds[key(x, y)]; ground[key(x, y)] = g; }, solid = (x, y, kind) => { grid[y][x] = 1; kinds[key(x, y)] = kind; delete ground[key(x, y)]; };
    for (let y = 1; y < SIZE - 1; y++) for (let x = 1; x < SIZE - 1; x++) { const h = (CM.hashSeed(`ember:${x},${y}`) % 1000) / 1000, r = ((x - 14) / 11) ** 2 + ((y - 13) / 10) ** 2 + (h - 0.5) * 0.15;
      if (r <= 1) { if (y <= 7 && r > 0.05) solid(x, y, h < 0.35 ? "denrocktall" : "cliff"); else open(x, y, y >= 18 ? "rock" : h < 0.15 ? "dirt" : "rock"); } }
    for (const [x, y] of [[13, 7], [15, 7], [13, 8], [15, 8]]) solid(x, y, "cliff"); solid(MOUTH[0], 7, "cavemouth"); open(...MOUTH, "dirt"); things[key(...MOUTH)] = { type: "islemouth" };
    for (let y = MOUTH[1] + 1; y <= 18; y++) if (grid[y][MOUTH[0]] !== 0) open(MOUTH[0], y, "dirt"); else ground[key(MOUTH[0], y)] = "dirt";
    for (const [x, y] of [[8, 14], [9, 14], [8, 15]]) { open(x, y, "rock"); decor.push({ kind: "water", x, y }); features[key(x, y)] = { type: "river" }; }   // (a hot spring)
    for (let y = 19; y <= JETTY[1]; y++) open(JETTY[0], y, "planks");
    things[key(JETTY[0] - 1, 20)] = { type: "signpost", text: "EMBERREACH. Up the black path: the mouth in the mountain. Mind the cracks where the steam comes out, and don't drink from the spring: it's hot enough to cook in." };
    for (let y = 0; y < SIZE; y++) for (let x = 0; x < SIZE; x++) if (grid[y][x] === 0) seen.push([x, y]);
    return { number: n, grid, pos: JETTY.slice(), facing: 0, things, features, dark: [], seen, decor, special: "landing", isle: "ember", solidDefault: "sea", kinds, ground, rooms: [{ x0: 0, y0: 0, x1: SIZE - 1, y1: SIZE - 1, name: "Emberreach" }] }; };
  Object.assign(I, { mouthFront: MOUTH.slice(), jetty: JETTY.slice(), ship: [JETTY[0] + 2.45, JETTY[1] - 0.5], shipYaw: Math.PI, atBerth: ([x, y]) => x === JETTY[0] && y >= JETTY[1] - 2 && y <= JETTY[1],
    arrive: "The Wren comes in through water that's warm to the hand and smells of eggs, under a mountain with a plume of smoke leaning off its top, and ties up at a jetty on black sand. Emberreach.",
    mouthWords: "A mouth in the mountainside, square-cut once, and through it a red light and a breath of hot air that smells of iron. Steps, worn hollow by feet with claws on them, go down." });
  CM.ISLES.ember = I; if (!CM.SEA_OPEN.includes("ember")) CM.SEA_OPEN.push("ember");
}
