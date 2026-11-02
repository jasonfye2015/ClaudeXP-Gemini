"use strict";
// The kennel and the stable (v35.4, UPGRADE_PLAN_30.md): in town, in the corner south-east of the Keep-yard, a kennel
// and a stable where the party's animals live while it is in town - seen there through the gate. Standing at its gate:
// feed them (a few coins, once a day: the party's heart lifts), name them again, and teach and fit them as at the farm.
//   CM.KENNEL_AT; game.atKennel(); game.feedPets(); game.renamePet(kind, name)
{ CM.KENNEL_AT = [40, 26]; CM.KENNEL_FEED = 5;
  const G = CM.Game.prototype, key = (x, y) => `${x},${y}`;
  const mt0 = CM.makeTown; CM.makeTown = function (...a) { const fl = mt0.apply(this, a), [x, y] = CM.KENNEL_AT; if (fl.grid[y] && fl.grid[y][x] === 0 && !fl.things[key(x, y)]) fl.things[key(x, y)] = { type: "kennel" }; return fl; };
  Object.assign(G, {
    atKennel() { const fl = this.floor; return Boolean(fl && fl.number === 0 && Math.abs(fl.pos[0] - CM.KENNEL_AT[0]) + Math.abs(fl.pos[1] - CM.KENNEL_AT[1]) <= 1); },
    feedWhy() { if (!this.atKennel()) return "The animals are at the kennel, by the Keep-yard."; if (!this.petName("dog") && !this.petName("pony")) return "The kennel is empty."; const day = CM.dayOf ? CM.dayOf(this) : 0;
      if (this.vext("kennel").fed === `${this.seed}:${day}`) return "They've been fed today."; if (this.gold < CM.KENNEL_FEED) return `${CM.KENNEL_FEED} gold.`; return ""; },
    feedPets() { const why = this.feedWhy(); if (why) return why; this.logAct && this.logAct("feedPets"); this.gold -= CM.KENNEL_FEED; this.vext("kennel").fed = `${this.seed}:${CM.dayOf ? CM.dayOf(this) : 0}`; this.cheer && this.cheer(5);
      const names = [this.petName("dog"), this.petName("pony")].filter(Boolean); this.say(`${names.join(" and ")} ${names.length === 1 ? "eats" : "eat"} out of your hands, and the party feels the better for it.`); this.saveVillage && this.saveVillage(); this.emit("change"); return ""; },
    renamePet(kind, name) { const p = this.pets()[kind]; if (!p) return "No such animal."; if (!this.atKennel()) return "Names are given at the kennel."; const n = String(name || "").replace(/[<>&"]/g, "").trim().slice(0, 16); if (!n) return "A name, please.";
      this.logAct && this.logAct("renamePet", kind, n); const was = p.name; p.name = n; this.saveVillage && this.saveVillage(); this.say(`${was} is ${n} now, and doesn't seem to mind.`); this.emit("change"); return ""; },
  });
  const use0 = G.use; G.use = function (...a) { const fl = this.floor; if (this.mode === "explore" && fl && fl.number === 0) { const t = fl.things[key(fl.pos[0], fl.pos[1])]; if (t && t.type === "kennel") { this.logAct && this.logAct("use"); this.emit("kennel"); return; } } return use0.apply(this, a); };
}
