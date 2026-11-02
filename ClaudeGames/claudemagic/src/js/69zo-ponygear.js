"use strict";
// The pony's gear (v35.2, UPGRADE_PLAN_30.md): bought at the farm (or the kennel and stable), kept with the pony in the
// village. Saddlebags: twenty more carried on the land, besides the pony's thirty. A blanket: the snow no longer slows the
// party on the Wood's ways - the extra minute a step and the slower walk are gone. A cart: the fields' produce rides to
// the Square's stall in it, and sells a tenth higher; and the silo can be sold from the fields themselves.
//   CM.PONY_GEAR; game.ponyGear(); game.buyPonyGear(id)
{ CM.PONY_GEAR = { saddlebags: { name: "Saddlebags", gold: 90, what: "twenty more carried on the land" }, blanket: { name: "A blanket", gold: 70, what: "the snow no longer slows the party in the Wood" },
    cart: { name: "A cart", gold: 200, what: "the fields' produce sells a tenth higher, and the silo can be sold from the fields" } };
  const G = CM.Game.prototype, PG = CM.PONY_GEAR;
  Object.assign(G, {
    ponyGear() { const p = this.pets().pony; if (!p) return {}; return (p.gear = p.gear || {}); },
    hasPonyGear(id) { return Boolean(this.petName("pony") && this.ponyGear()[id]); },
    buyPonyGearWhy(id) { const T = PG[id]; if (!T) return "No such thing."; if (!this.petName("pony")) return "There's no pony to fit it to."; if (!((this.atFarm && this.atFarm()) || (this.atKennel && this.atKennel()))) return "The pony's gear is fitted at the farm (or the stable, once there is one).";
      if (this.ponyGear()[id]) return "It has one."; if (this.gold < T.gold) return `${T.gold} gold.`; return ""; },
    buyPonyGear(id) { const why = this.buyPonyGearWhy(id); if (why) return why; this.logAct && this.logAct("buyPonyGear", id); this.gold -= PG[id].gold; this.ponyGear()[id] = true; this.saveVillage && this.saveVillage();
      this.say(`${PG[id].name} for ${this.petName("pony")}: ${PG[id].what}.`); this.saveRun && this.saveRun(); this.emit("change"); return ""; },
  });
  const snowy = (g) => g.floor && g.floor.number === -1 && CM.snowDepth && CM.snowDepth(g) >= (CM.WEATHERPLAY ? CM.WEATHERPLAY.snowFrom : 0.3);
  const ow0 = G.overweight; G.overweight = function (...a) { const o = ow0.apply(this, a); if (!this.hasPonyGear("saddlebags") || !this.floor || !(this.floor.number === 0 || this.floor.number === -1)) return o;
    const cap = CM.carryCap(this.party) + (this.followerCarry ? this.followerCarry() : 0) + CM.PETS.ponyCarry + 20; return CM.bagWeight(this.bag) / cap; };
  const wp0 = G.walkPace; G.walkPace = function (...a) { const p = wp0.apply(this, a); return this.hasPonyGear("blanket") && snowy(this) ? p / 1.5 : p; };
  const burn0 = G.burn; G.burn = function (...a) { const c0 = this.clock || 0, out = burn0.apply(this, a); if (this.hasPonyGear("blanket") && snowy(this) && (this.clock || 0) > c0) this.clock -= 1; return out; };
  const ms0 = G.marketSell; if (ms0) G.marketSell = function (from = "pack") { const cart = this.hasPonyGear("cart"), fieldsHere = cart && from === "silo" && this.atFields && this.atFields(), fl = this.floor, n0 = fl ? fl.number : null;
    if (fieldsHere && fl) fl.number = 0; let r; try { r = ms0.call(this, from); } finally { if (fieldsHere && fl) fl.number = n0; }
    if (cart && r && !r.error && r.gold > 0) { const more = Math.round(r.gold / 10); this.gold += more; r.gold += more; this.say(`${this.petName("pony")} hauled it in the cart, fresh: ${more} gold more.`); }
    return r; };
}
