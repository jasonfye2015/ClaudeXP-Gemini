"use strict";
// Lost and found (v37.3, UPGRADE_PLAN_32.md): when an expedition ends in the dark, the best of what its heroes wore -
// four things at most - stays on the floor where they fell, kept in the store ("lostGear", twelve at most) for any later
// expedition, whatever its seed: the first to come onto that floor finds it, a pack with their names scratched on the
// buckle, and takes it home. (The same seed's remains and their ghost, 61-explore.js, are as they were.)
//   game.lostGear(); a floor's "lostpack" thing
{ const G = CM.Game.prototype, key = (x, y) => `${x},${y}`;
  G.lostGear = function () { return CM.store.get("lostGear", []) || []; };
  const end0 = G.endRun; G.endRun = function (won) { const lost = !(won || this.crowned) && !this.replaying && !this.film, fl = this.floor;
    if (lost && fl && fl.number >= 1 && fl.number < 1000 && fl.number % 1 === 0) { const worn = []; for (const h of this.party || []) for (const it of CM.equipped(h)) if (!(it.props || {}).cursed && !(it.props || {}).relic && !(it.props || {}).againHeirloom) worn.push(JSON.parse(JSON.stringify(it)));
      worn.sort((a, b) => (b.value || 0) - (a.value || 0)); if (worn.length) { const L = this.lostGear().filter((r) => !r.taken); L.push({ id: `${this.seed}:${fl.number}:${Date.now()}`, run: `${this.seed}:${this.startedAt || ""}`, floor: fl.number, names: (this.party || []).map((h) => h.name), items: worn.slice(0, 4), date: CM.today ? CM.today() : "" }); CM.store.set("lostGear", L.slice(-12)); } }
    return end0.call(this, won); };
  const em0 = G.emit; G.emit = function (ev, ...a) { if (ev === "floor" && this.floor && this.tally) {   /* (a replay lays it as the run did: the store is read, not changed) */ const fl = this.floor, n = fl.number, E = this.ext("lostfound");
      if (n >= 1 && n < 1000 && !E[n] && !(this.deltas && this.deltas[n])) { E[n] = true; const L = this.lostGear(), here = L.find((r) => r.floor === n && !r.run.startsWith(`${this.seed}:`) && (!r.taken || r.taken === this.seed));
        if (here) { const N = fl.grid.length, cells = []; for (let y = 1; y < N - 1; y++) for (let x = 1; x < N - 1; x++) if (fl.grid[y][x] === 0 && !fl.things[key(x, y)] && !(fl.features || {})[key(x, y)] && !(fl.pos[0] === x && fl.pos[1] === y)) cells.push(key(x, y));
          if (cells.length) fl.things[cells[CM.hashSeed(`${this.seed}:lostat:${here.id}`) % cells.length]] = { type: "lostpack", id: here.id, names: here.names, items: here.items, date: here.date }; } } }
    return em0.call(this, ev, ...a); };
  const use0 = G.use; G.use = function (...a) { const fl = this.floor; if (this.mode === "explore" && fl) { const k = key(fl.pos[0], fl.pos[1]), t = fl.things[k];
      if (t && t.type === "lostpack") { this.logAct && this.logAct("use"); delete fl.things[k]; if (!this.replaying && !this.film) { const L = this.lostGear(), R = L.find((r) => r.id === t.id); if (R) { R.taken = this.seed; CM.store.set("lostGear", L); } }   /* (marked, not struck off: a replay of this run finds it the same) */ this.gain(t.items, "remains");
        this.say(`A pack, half under the dust, and scratched into its buckle: ${t.names.join(", ")}${t.date ? `, ${t.date}` : ""}. An expedition that didn't come back. You carry what they wore up to the light: ${t.items.map((i) => i.name).join(", ")}.`);
        this.tally.lostFound = (this.tally.lostFound || 0) + 1; if (this.achieve) this.achieve("lostfound"); this.saveRun(); this.emit("change"); return; } }
    return use0.apply(this, a); };
  CM.ACHIEVEMENTS.lostfound = { name: "Lost and Found", what: "Bring home the gear an earlier expedition lost", title: "the Finder" };
}
