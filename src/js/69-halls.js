"use strict";
// The library, the temple and the guildhall, under their roofs in town (the village's three buildings become doors):
// the library's reading desk (the journal's boards), Wren's copying, a tome borrowed for a run and returned when the
// party comes home, the lost pages shelved as they are found, and at the fifth level the gazetteer (the first five
// floors' walls on the map before the party is on them); the temple at town prices (a tenth less), the candles, the
// Patriarch's history, the tithe and a vigil (a scar kept or let fade, once a hero); the guildhall's trainers, the
// second calling, the contracts, and the roster: every party this browser set out with, kept as a preset, and a
// muster that makes the next run's party from the last that came home.
CM.VILLAGE.library.costs.push(300); CM.VILLAGE.library.levels.push("The gazetteer: a new run has the first five floors' walls on its map before the party is on them");
CM.VILLAGE.shrine.costs.push(250); CM.VILLAGE.shrine.levels.push("The vigil: a hero's scar may be kept or let fade, once a hero");
CM.TOWN_PRICE = 0.9;
CM.ROSTER_MAX = 12;
CM.GAZETTEER_FLOORS = 5;
Object.assign(CM.Game.prototype, {
  libraryState() { this.village = this.village || {}; const L = this.village.library = this.village.library || { lent: null, pages: 0 }; return L; },
  // a tome borrowed for the run: one at a time; back on the shelf when the run ends (read or not)
  borrowTome(id) {
    if (!this.inTown()) return "The tomes are at the library, in town.";
    if (this.villageLevel("library") < 1) return "The library has no roof yet.";
    const L = this.libraryState(); if (L.lent) return `${CM.TOMES[L.lent.tome] || "A tome"} is out already, with this party.`;
    if (!CM.TOMES[id]) return "No such tome on the shelves.";
    this.logAct("borrowTome", id);
    const tome = CM.tome(id); tome.borrowed = true; tome.value = 0;
    L.lent = { tome: id, seed: this.seed }; this.saveVillage();
    this.gain([tome], "library");
    this.say(`Wren writes it in the ledger: ${tome.name}, lent to this party until it comes home.`);
    this.saveRun(); this.emit("change");
    return "";
  },
  returnTomes() {                                                        // (at a run's end: what was borrowed goes back on the shelf)
    const L = this.libraryState(); if (!L.lent) return;
    for (let i = this.bag.length - 1; i >= 0; i--) if (this.bag[i].borrowed) this.bag.splice(i, 1);
    L.lent = null; this.saveVillage();
  },
  shelvePage() { const L = this.libraryState(); L.pages = (L.pages || 0) + 1; this.saveVillage(); },
  // the temple at town prices, and the vigil
  townPrice(cost) { return this.inTown() ? Math.ceil(cost * CM.TOWN_PRICE) : cost; },
  vigil(heroIndex, scarId, keep) {
    if (!this.inTown()) return "The vigil is kept at the temple, in town.";
    if (this.villageLevel("shrine") < 5) return "Father Osric keeps no vigil yet: the shrine wants its fifth level.";
    const h = this.party[heroIndex]; if (!h || h.hp <= 0) return "Only a hero on their feet.";
    if (!(h.scars || []).includes(scarId)) return `${h.name} has no such scar.`;
    if (h.vigil) return `${h.name} has kept the vigil already.`;
    this.logAct("vigil", heroIndex, scarId, keep ? 1 : 0);
    h.vigil = true;
    if (!keep) { h.scars = h.scars.filter((s) => s !== scarId); this.say(`A night on the temple's stones, and in the morning ${h.name}'s ${CM.SCARS[scarId].name} is a story and not a mark.`); }
    else this.say(`${h.name} keeps the vigil and keeps the ${CM.SCARS[scarId].name}: it is theirs, and they say so.`);
    this.saveRun(); this.emit("change");
    return "";
  },
  // the roster: the parties this browser set out with, as presets; the muster, from the last party that came home
  roster() { this.village = this.village || {}; return this.village.roster || []; },
  noteRoster(entry) {
    const party = (this.startParty || []).map((p) => ({ cls: p.cls, name: p.name, stats: Object.assign({}, p.stats || {}), row: p.row, quirk: p.quirk || null, origin: p.origin || null }));
    if (party.length !== 4) return;
    const key = party.map((p) => `${p.name}:${p.cls}`).join("|");
    this.village = this.village || {};
    const roster = (this.village.roster || []).filter((r) => r.key !== key);
    roster.unshift({ key, party, date: CM.today(), floor: entry.floor, won: Boolean(entry.won), home: Boolean(entry.won || entry.left || entry.bottom), seed: this.seed });
    this.village.roster = roster.slice(0, CM.ROSTER_MAX);
  },
  muster() { return this.roster().find((r) => r.home) || null; },
});
