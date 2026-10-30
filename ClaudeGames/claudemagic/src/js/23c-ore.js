"use strict";
// Mining: five ores in veins (things on the floor beside the rock, placed by hash last of all in CM.furnish, so no
// older hash's cell moves and no fingerprint changes), picks that mine by their grade and wear a point a swing (reset
// at the forge), chunks that are heavy, and the smelter at the forge in town: three chunks and a charcoal make a bar,
// two bars of a kind and one of the kind above an alloy bar. Charcoal is the Wood's burner's: deadwood in, charcoal
// out, or a coin. The dwarves' pick is a pick that is kept now (an iron one), and opens a hidden door for ten points.
CM.ORES = {
  copper: { name: "copper", floors: [1, 10], cave: 0, value: 8, colour: "#C07040" },
  iron: { name: "iron", floors: [6, 20], cave: 1, value: 14, colour: "#8A8A90" },
  silver: { name: "silver", floors: [11, 25], value: 26, colour: "#D8DCE8" },
  gold: { name: "gold", floors: [21, 40], cave: 2, value: 50, colour: "#E8C040" },
  stariron: { name: "star-iron", floors: [36, 50], value: 90, colour: "#8090D0" },
};
CM.ORE_ORDER = ["copper", "iron", "silver", "gold", "stariron"];
CM.ALLOYS = { bronze: { name: "bronze", of: ["copper", "iron"], value: 60 }, steel: { name: "steel", of: ["iron", "silver"], value: 110 }, electrum: { name: "electrum", of: ["silver", "gold"], value: 220 }, starsteel: { name: "star-steel", of: ["gold", "stariron"], value: 420 } };
CM.PICKS = { copper: { name: "Copper Pick", mines: ["copper", "iron"], points: 30, value: 80 }, iron: { name: "Iron Pick", mines: ["copper", "iron", "silver"], points: 50, value: 200 }, steel: { name: "Steel Pick", mines: CM.ORE_ORDER.slice(), points: 80, value: 500 } };
CM.VEIN_SWINGS = 3;
CM.SWING_MINUTES = 5;
CM.SECRET_POINTS = 10;
CM.SMELT_CHUNKS = 3;
CM.CHARCOAL_PRICE = 15;
CM.oreChunk = (ore, n = 1) => ({ name: `${CM.ORES[ore].name.charAt(0).toUpperCase() + CM.ORES[ore].name.slice(1)} ore`, kind: "ore", ore, power: n, value: CM.ORES[ore].value });
CM.metalBar = (kind) => { const A = CM.ALLOYS[kind], O = CM.ORES[kind]; const name = (A ? A.name : O.name); return { name: `${name.charAt(0).toUpperCase() + name.slice(1)} bar`, kind: "bar", bar: kind, power: 0, value: A ? A.value : O.value * 3 + 20 }; };
CM.charcoal = () => ({ name: "Charcoal", kind: "charcoal", power: 0, value: CM.CHARCOAL_PRICE });
CM.pick = (grade) => ({ name: CM.PICKS[grade].name, kind: "pick", pick: grade, points: CM.PICKS[grade].points, power: 0, value: CM.PICKS[grade].value });
CM.dwarfPick = () => Object.assign(CM.pick("iron"), { name: "Dwarven Pick" });
for (const [id, O] of Object.entries(CM.ORES)) { CM.BASES[CM.oreChunk(id).name] = { id: CM.oreChunk(id).name, kind: "ore", slot: null, tier: CM.ORE_ORDER.indexOf(id), group: "ingredient" }; CM.BASES[CM.metalBar(id).name] = { id: CM.metalBar(id).name, kind: "bar", slot: null, tier: CM.ORE_ORDER.indexOf(id), group: "stuff" }; void O; }
for (const id of Object.keys(CM.ALLOYS)) CM.BASES[CM.metalBar(id).name] = { id: CM.metalBar(id).name, kind: "bar", slot: null, tier: 5 + Object.keys(CM.ALLOYS).indexOf(id), group: "stuff" };
for (const id of Object.keys(CM.PICKS)) CM.BASES[CM.PICKS[id].name] = { id: CM.PICKS[id].name, kind: "pick", slot: null, tier: Object.keys(CM.PICKS).indexOf(id), group: "stuff" };
CM.BASES.Charcoal = { id: "Charcoal", kind: "charcoal", slot: null, tier: 0, group: "stuff" };
Object.assign(CM.WEIGHTS, { ore: 2, bar: 3, charcoal: 1, pick: 3 });
// which ores a floor has veins of, and how many: by the ore's floors (the Dwarven Halls' silver gives two a swing)
CM.veinsFor = (number) => { const out = []; for (const [id, O] of Object.entries(CM.ORES)) if (number >= O.floors[0] && number <= O.floors[1]) out.push(id); return out; };
CM.bestPick = (bag, ore) => { let best = -1; bag.forEach((it, i) => { if (it.kind === "pick" && (it.points || 0) > 0 && CM.PICKS[it.pick] && CM.PICKS[it.pick].mines.includes(ore) && (best < 0 || CM.PICKS[it.pick].points > CM.PICKS[bag[best].pick].points)) best = i; }); return best; };
