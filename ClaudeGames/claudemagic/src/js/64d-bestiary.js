"use strict";
// Ten more kinds for the Deep (the eleventh update, phase 7): two for each of the five bands below the Drowned Town
// that had only two of their own. They join their band's groups by `deep` (CM.deepGroup picks among a band's kinds with
// the same one die as before, so no floor's walls or count of dice move; which kind is picked may). Two new ways:
// "spawns" (the Spore Mother: every third turn a Sporeling bursts from her, two at most) and "astray" (the Grave
// Lantern: its touch leads a hero a step the wrong way, and the hero loses the moment). A Sporeling is only ever
// spawned.
CM.DEEP_MORE = [
  { name: "Spore Mother", colour: "#9A8A4A", body: "wide", head: "round", eyes: "#E0FF80", extras: ["torn"], speed: 7, ability: "spawns", touch: { status: "poison", chance: 0.2 }, deep: 5, shape: [1.3, 0.9, 0.8] },
  { name: "Mycelid Crawler", colour: "#6A7A3A", body: "beast", head: "round", eyes: "#C0FF60", extras: ["claws"], speed: 12, ability: "web", touch: { status: "poison", chance: 0.15 }, deep: 5, shape: [0.9, 1.0, 0.7] },
  { name: "Glass Hound", colour: "#A8D8E8", body: "beast", head: "snout", eyes: "#FFFFFF", extras: ["tail"], speed: 16, ability: "charge", deep: 6, shape: [0.9, 1.1, 0.9] },
  { name: "Prism Sentinel", colour: "#C0A8E8", body: "tall", head: "helm", eyes: "#FFF0FF", extras: ["shield"], speed: 7, ability: "warder", deep: 6, shape: [1.2, 0.9, 1.3] },
  { name: "Bellows Imp", colour: "#C85A2A", body: "small", head: "ears", eyes: "#FFE040", extras: ["tail"], speed: 14, ability: "breath", deep: 7, shape: [0.7, 1.0, 0.6] },
  { name: "Slag Golem", colour: "#5A4A42", body: "wide", head: "round", eyes: "#FF8030", extras: [], speed: 5, ability: "stun", deep: 7, shape: [1.5, 1.2, 1.4] },
  { name: "Grave Lantern", colour: "#D8E8A0", body: "ghost", head: "pale", eyes: "#FFFFC0", extras: [], speed: 13, undead: true, ability: "astray", deep: 8, shape: [0.7, 0.9, 0.4] },
  { name: "Charnel Hound", colour: "#7A6A5A", body: "beast", head: "skull", eyes: "#FF5040", extras: ["tail", "torn"], speed: 15, undead: true, ability: "savage", deep: 8, shape: [0.9, 1.1, 0.7] },
  { name: "Thorn Lotus", colour: "#8A4A6A", body: "small", head: "round", eyes: "#FF60A0", extras: ["claws"], speed: 9, ability: "ranged", touch: { status: "poison", chance: 0.2 }, deep: 9, row: "back", shape: [0.8, 1.0, 0.6] },
  { name: "Root Wyrm", colour: "#5A4030", body: "beast", head: "snout", eyes: "#FFB040", extras: ["tail"], speed: 10, ability: "buffet", deep: 9, shape: [1.4, 1.2, 1.0] },
  { name: "Sporeling", colour: "#B8C870", body: "small", head: "round", eyes: "#FFFFA0", extras: [], speed: 11, touch: { status: "poison", chance: 0.1 }, spawned: true, shape: [0.4, 0.5, 0.2] },
];
for (const k of CM.DEEP_MORE) { k.since = 10; if (!CM.MONSTERS.some((m) => m.name === k.name)) CM.MONSTERS.push(k); }   // (since v10: generator 1's floors never meet them, so its frozen floors stay as they were)
CM.SPAWN = { every: 3, most: 2 };

Object.assign(CM.Game.prototype, {
  // the Spore Mother's turn: every third, a Sporeling bursts from her (two at most) instead of a blow
  spawnTurn(m) {
    m.spawnT = (m.spawnT || 0) + 1;
    if (m.spawnT % CM.SPAWN.every !== 1) return false;
    const up = this.foes.filter((f) => f.summoned && f.hp > 0 && !f.fled && f.kind === "Sporeling").length;
    if (up >= CM.SPAWN.most) return false;
    this.summonFor(m, { what: "Sporeling", text: `${CM.The(m)} splits, and {n} bursts out of her, wet and hungry.`, plural: "a Sporeling", level: "deep" }, 1);
    this.emit("fx", { kind: "summon", layer: "fx:leaf" });
    return true;
  },
  // the Grave Lantern's touch: the hero follows the light a step the wrong way, and loses the moment
  leadAstray(m, target) {
    if (target.hp <= 0 || target.thrall || (target.status || {}).paralysis || !this.rnd.chance(0.3)) return false;
    target.status = target.status || {}; target.status.paralysis = 1;
    this.say(`${target.name} follows ${CM.the(m)}'s light a step the wrong way, and loses the moment.`);
    return true;
  },
});
