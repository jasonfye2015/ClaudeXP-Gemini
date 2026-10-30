"use strict";
// The alchemist's garden (beds planted between runs, grown a little every run that ends, and the brewing bench at
// town prices), the chronicler's house (the films, the statistics, the ledger, the Hall of Fame and the memorial's
// book, under one roof) and the square's life: the well (a drink, the notice board, a coin thrown for the town),
// market day on the week's seed (a peddler's cloth in the square), three townsfolk on the lanes with a line a day
// each from the hill's own story, and the lanterns lit when a run begins late.
CM.VILLAGE.garden = { name: "The Alchemist's Garden", costs: [30, 80, 160], levels: [
  "One bed (three of an ingredient, grown one more every run that ends, up to five) and the brewing bench at town prices", "Two beds", "Three beds, and the alchemist's request may be delivered here"] };
CM.VILLAGE.chronicler = { name: "The Chronicler's House", costs: [120], levels: ["Wren's house: the films, the statistics, the ledger, the Hall of Fame and the memorial's book, under one roof"] };
CM.TOWN_PLOTS.garden.village = "garden"; CM.TOWN_PLOTS.chronicler.village = "chronicler";
CM.BED_MAX = 5;
CM.TOWNSFOLK = [
  { name: "Marget's granddaughter", who: "a fishwife with a basket and no fish", lines: ["\"My grandmother saw who opened the sluices. She told my mother, and my mother told the water. I tell the well.\"", "\"The lower town is under the river still. On a quiet night you can hear a door that never unbarred.\"", "\"Fish? There are no fish. The river remembers what was put in it.\"", "\"You are going down. Everyone goes down. Some come up, and they don't eat fish either.\""] },
  { name: "the bell-founder's boy", who: "an old man they still call the boy", lines: ["\"My father cast the last bell. The king had it taken down the week the queen drowned. It is in the river with her.\"", "\"They say Brother Cael rang it once more, alone, the night she died. I believe it. Bells want ringing.\"", "\"A bell's tongue is a trinket now, the pedlars say. It was a voice.\"", "\"If you hear a bell down there, it is not mine. Mine is under the water.\"", ] },
  { name: "the sexton's widow", who: "a woman in black who sweeps the square", lines: ["\"My husband buried a thousand and was buried by none. His helm is down there in a chest, they tell me, and no one brings it up.\"", "\"The well was dry the morning the shaft was dug. The old ones say it runs again when a crown comes up. I sweep, and I wait.\"", "\"The dwarves' coin was cold. My mother kept one in a box. It is still cold.\"", "\"The Patriarch's order built the first house on this hill. The temple stands on its stones. Mind where you step.\""] },
];
CM.clockHour = () => new Date().getHours();
CM.townNight = (hour) => { const h = hour === undefined ? CM.clockHour() : hour; return h >= 21 || h < 6; };
Object.assign(CM.Game.prototype, {
  // ---- the garden ----
  garden() { this.village = this.village || {}; const G = this.village.garden = this.village.garden || { beds: [] }; G.beds = G.beds || []; return G; },
  bedsOf() { return this.villageLevel("garden"); },
  plant(row) {
    if (!this.inTown()) return "The beds are in the garden, in town.";
    if (this.villageLevel("garden") < 1) return "The garden has no beds yet.";
    const item = this.bag[row]; if (!item || item.kind !== "ingredient") return "The beds take an ingredient.";
    const G = this.garden(); if (G.beds.length >= this.bedsOf()) return `Every bed is planted (${this.bedsOf()}). Harvest one first.`;
    this.logAct("plant", row);
    this.bag.splice(row, 1); G.beds.push({ ingredient: item.ingredient, n: 1 }); this.saveVillage();
    this.say(`${CM.INGREDIENTS[item.ingredient].name} goes into a bed. It grows a little with every run that ends.`);
    this.saveRun(); this.emit("change");
    return "";
  },
  harvest(i) {
    if (!this.inTown()) return "The beds are in the garden, in town.";
    const G = this.garden(), bed = G.beds[i]; if (!bed) return "No such bed.";
    this.logAct("harvest", i);
    const n = bed.n; G.beds.splice(i, 1); this.saveVillage();
    const got = []; for (let k = 0; k < n; k++) got.push(CM.ingredient(bed.ingredient)); this.gain(got, "garden");
    this.say(`${CM.plural(n, CM.INGREDIENTS[bed.ingredient].name)} from the bed, and the bed turned over.`);
    this.saveRun(); this.emit("change");
    return "";
  },
  growBeds() { const G = this.garden(); for (const b of G.beds) b.n = Math.min(CM.BED_MAX, (b.n || 1) + 1); if (G.beds.length) this.saveVillage(); },
  // ---- the square ----
  well() {
    const fl = this.floor, won = (this.fame || []).some((e) => e.won);
    const lines = [won ? `The well runs clear since the crown came up. The party drinks, and is ${this.moraleWord().toLowerCase()}.` : "The well is dry, and has been since the shaft was dug. The old ones say it runs again when a crown comes up."];
    lines.push(`The notice board: the week's seed is ${CM.weeklySeed()}; the day's is daily-${CM.today()}.${String(this.seed).startsWith("weekly-") ? " Market day: a peddler's cloth is out in the square." : ""}`);
    const stones = this.wellStones(); if (stones.length) lines.push(`Carved on the well's stones, in an old hand: ${stones.join(" ")}`);
    if (!fl.wished && this.gold >= 1) { this.logAct("wish"); fl.wished = true; this.gold -= 1; this.village = this.village || {}; this.village.renown = (this.village.renown || 0) + 1; this.saveVillage(); lines.push("A coin goes down the well for the town: one renown."); }
    this.say(lines.join(" "));
    this.emit("talk", { title: "The square", text: lines.join(" ") });
  },
  // the hill's own chapter, carved on the well's stones as renown is spent on the town (CM.VILLAGE_LORE_AT): read in order
  wellStones() {
    const spent = (this.village || {}).spent || 0, out = [];
    CM.VILLAGE_LORE_AT.forEach((at, i) => { const L = CM.LORE_TEXT[`village.${i + 1}`]; if (spent >= at && L) out.push(L.tellings[0]); });
    return out;
  },
  townsfolkLine(who) { const T = CM.TOWNSFOLK[who % CM.TOWNSFOLK.length]; const day = CM.hashSeed(CM.today()) % T.lines.length; return T.lines[(day + who) % T.lines.length]; },
  talkTownsfolk(thing) { const T = CM.TOWNSFOLK[thing.who % CM.TOWNSFOLK.length]; this.emit("talk", { title: T.name, text: this.townsfolkLine(thing.who) }); this.say(`${T.name.charAt(0).toUpperCase() + T.name.slice(1)}: ${this.townsfolkLine(thing.who)}`); },
});
