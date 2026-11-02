"use strict";
// Building the town (v36.3, UPGRADE_PLAN_31.md): four works the village raises with gold and the island's timber and
// stone (the request board's materials, 69e-requests.js), each changing the map and each a small good, kept in the
// village. The old wall repaired: banners along it, and every run sets out in better heart. A stone bridge for the
// plank one in the Wood: flagstones across the river, and the Wood walked a tenth quicker. A bathhouse on the south
// lane: a hot bath once a day - everyone mended, the small ailments washed off, the heart lifted. A watchtower on the
// south green: from its top the whole Deep Wood is seen, the dens and caves with it.
//   CM.WORKS; game.works(); game.raiseWork(id); game.bathe(); game.climbWatch()
{ const W = CM.WORKS = {
    wall: { name: "The old wall repaired", gold: 300, mats: [["stone", 48]], what: "banners on the walls, and every run sets out in better heart (+6)" },
    bridge: { name: "A stone bridge in the Wood", gold: 250, mats: [["stone", 32], ["timber", 16]], what: "flagstones over the river, and the Wood walked a tenth quicker" },
    bath: { name: "The bathhouse", gold: 400, mats: [["timber", 40], ["stone", 24]], at: [14, 33], what: "a hot bath once a day: mended, washed of small ailments, in better heart" },
    watch: { name: "The watchtower", gold: 350, mats: [["timber", 32], ["stone", 32]], at: [30, 30], what: "from its top the whole Deep Wood is seen, and its dens and caves" },
  };
  const G = CM.Game.prototype, key = (x, y) => `${x},${y}`, RQ = () => CM.TOWNREQ && CM.TOWNREQ.byId;
  Object.assign(G, {
    works() { return this.vext("works"); },
    worksDone(id) { return Boolean(this.works()[id]); },
    workWhy(id) { const Wk = W[id]; if (!Wk) return "No such work."; if (!this.inTown || !this.inTown()) return "The village's works are raised from town."; if (this.worksDone(id)) return "It's done.";
      if (this.gold < Wk.gold) return `${Wk.gold} gold.`; const R = RQ(); if (R && CM.matsOn !== false) { const short = Wk.mats.filter(([k, n]) => R[k] && R[k].have(this) < n); if (short.length) return `It wants ${short.map(([k, n]) => `${R[k].what(n)} (${R[k].have(this)} in hand)`).join(" and ")}.`; } return ""; },
    raiseWork(id) { const why = this.workWhy(id); if (why) return why; this.logAct && this.logAct("raiseWork", id); const Wk = W[id], R = RQ(); this.gold -= Wk.gold; if (R && CM.matsOn !== false) for (const [k, n] of Wk.mats) if (R[k]) R[k].take(this, n);
      this.works()[id] = { day: CM.today ? CM.today() : "" }; this.saveVillage && this.saveVillage(); layWorks(this); this.sound && this.sound("level"); this.say(`${Wk.name}: done, and the town turns out to see it. ${Wk.what[0].toUpperCase() + Wk.what.slice(1)}.`);
      if (Object.keys(W).every((k) => this.worksDone(k)) && this.achieve) this.achieve("builder"); this.saveRun && this.saveRun(); this.emit("change"); return ""; },
    batheWhy() { if (!this.worksDone("bath")) return "There's no bathhouse yet."; const fl = this.floor; if (!fl || fl.number !== 0 || Math.abs(fl.pos[0] - W.bath.at[0]) + Math.abs(fl.pos[1] - W.bath.at[1]) > 1) return "The bathhouse is on the south lane.";
      if (this.vext("bath").day === `${this.seed}:${CM.dayOf(this)}`) return "Once a day: the water's still heating."; return ""; },
    bathe() { const why = this.batheWhy(); if (why) return why; this.logAct && this.logAct("bathe"); this.vext("bath").day = `${this.seed}:${CM.dayOf(this)}`;
      for (const h of this.alive()) { h.hp = h.max; h.mp = h.maxmp; if (this.cure && CM.CURABLE) this.cure(h, CM.CURABLE); } this.cheer && this.cheer(8); this.sound && this.sound("heal");
      this.say("Hot water, steam, and someone singing badly in the next tub. Everyone comes out mended and pink, and in better heart."); this.saveRun && this.saveRun(); this.emit("change"); return ""; },
    climbWatch() { if (!this.worksDone("watch")) return "There's no watchtower yet."; const fl = this.floor; if (!fl || fl.number !== 0 || Math.abs(fl.pos[0] - W.watch.at[0]) + Math.abs(fl.pos[1] - W.watch.at[1]) > 1) return "The watchtower is on the south green.";
      this.logAct && this.logAct("climbWatch"); const wood = this.floorAt ? this.floorAt(-1) : null; if (wood) { const seen = new Set(wood.seen.map(([x, y]) => key(x, y))); for (let y = 0; y < wood.grid.length; y++) for (let x = 0; x < wood.grid.length; x++) if (!seen.has(key(x, y))) wood.seen.push([x, y]); }
      const dens = this.dens ? this.dens().filter((d) => !d.cleared).length : 0; this.say(`From the top of the watchtower the whole of the Deep Wood lies open: the river, the glades, the three cave mouths${dens ? `, and ${dens === 1 ? "a den" : `${dens} dens`} under the roots` : ""}. It's on the map now.`);
      this.saveRun && this.saveRun(); this.emit("change"); return ""; },
  });
  CM.ACHIEVEMENTS.builder = { name: "The Town Rebuilt", what: "Raise all four of the village's works", title: "the Builder" };
  // the map: the bathhouse and the watchtower on the town's floor, the bridge's flagstones in the Wood
  const layWorks = (g) => { const fl = g.floor; if (!fl) return; if (fl.number === 0) for (const id of ["bath", "watch"]) { if (!g.worksDone(id)) continue; const k = key(...W[id].at); if (fl.grid[W[id].at[1]][W[id].at[0]] === 0 && !fl.things[k]) fl.things[k] = { type: "work", id }; }
    if (fl.number === -1 && g.worksDone("bridge") && fl.bridge) { const [bx, by] = fl.bridge; for (let x = bx - 1; x <= bx + 1; x++) if (fl.ground && fl.ground[key(x, by)] === "planks") fl.ground[key(x, by)] = "flags"; } };
  const em0 = G.emit; G.emit = function (ev, ...a) { if (ev === "floor") layWorks(this); return em0.call(this, ev, ...a); };
  const use0 = G.use; G.use = function (...a) { const fl = this.floor; if (this.mode === "explore" && fl && fl.number === 0) { const t = fl.things[key(fl.pos[0], fl.pos[1])]; if (t && t.type === "work") { this.logAct && this.logAct("use"); const r = t.id === "bath" ? this.bathe() : this.climbWatch(); if (r) this.say(r); return; } } return use0.apply(this, a); };
  const wp0 = G.walkPace; G.walkPace = function (...a) { const p = wp0.apply(this, a); return this.floor && this.floor.number === -1 && this.worksDone("bridge") ? p * 0.9 : p; };
  const ng0 = G.newGame; G.newGame = function (...a) { const out = ng0.apply(this, a); if (this.worksDone && this.worksDone("wall") && !this.replaying) this.morale = Math.min(100, (this.morale === undefined ? CM.MORALE.start : this.morale) + 6); return out; };
}
