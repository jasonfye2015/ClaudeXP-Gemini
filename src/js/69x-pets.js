"use strict";
// A dog and a pony (v27.2, UPGRADE_PLAN_22.md): animals of the party's own, kept in the village between runs and
// bought at the farm in the Wood - not hired help, so they take no follower's place.
// - The hound goes everywhere the party goes. It growls at a trap two squares off (marked on the map) and scratches at
//   the wall where a hidden door is; on the land by day it digs now and then and brings up something small - a few
//   coins, a herb, a seed.
// - The pony carries thirty more on the surface, walks the land quicker (every other step on the Wood's roads and
//   tracks costs no time), and waits at the shaft's head: it does not go below.
{ const PT = CM.PETS = { dog: { price: 60, names: ["Bramble", "Soot", "Nell", "Tolly", "Wisp", "Corrie"] }, pony: { price: 220, names: ["Dapple", "Turnip", "Old Moss", "Clover"] }, digEvery: 45, ponyCarry: 30 };
  const P = CM.Game.prototype;
  Object.assign(P, {
    pets() { this.village = this.village || {}; return (this.village.pets = this.village.pets || { dog: null, pony: null }); },
    petName(kind) { const p = this.pets()[kind]; return p ? p.name : null; },
    buyPet(kind) { const K = PT[kind]; if (!K) return "No such animal."; if (!this.atFarm || !this.atFarm()) return "The animals are at the farm, in the Wood."; if (this.pets()[kind]) return `${this.petName(kind)} is yours already.`;
      if (this.gold < K.price) return `${K.price} gold, and you have ${this.gold}.`; this.logAct && this.logAct("buyPet", kind); this.gold -= K.price;
      const name = K.names[CM.hashSeed(`${this.seed}:${kind}:${this.clock || 0}`) % K.names.length]; this.pets()[kind] = { name, since: CM.dayOf ? CM.dayOf(this) : 0 };
      this.say(kind === "dog" ? `A pup from the farm's litter, nearly grown: ${name}. It has decided you are its people.` : `${name}, the farm's pony: sure-footed, patient, and fond of apples.`);
      this.saveVillage && this.saveVillage(); this.emit("change"); return ""; },
  });
  // the hound's nose: traps two squares off, a hidden door beside the party
  const look0 = P.look;
  P.look = function (...a) { const out = look0.apply(this, a), dog = this.petName("dog"), fl = this.floor; if (!dog || !fl || !CM.isDeep(fl.number)) return out;
    const [x, y] = fl.pos;
    for (const [k, f] of Object.entries(fl.features)) { const [tx, ty] = k.split(",").map(Number), d = Math.abs(tx - x) + Math.abs(ty - y); if (d > 2) continue;
      if ((f.type === "trapdoor" && !f.known) || (f.type === "plate" && f.trap && !f.known && !f.spent)) { f.known = true; this.say(`${dog} growls low at the floor ahead: a trap, there.`); }
      if (d === 1 && f.type === "secret" && !f.found && !f.sniffed) { f.sniffed = true; const way = tx > x ? "east" : tx < x ? "west" : ty > y ? "south" : "north"; this.say(`${dog} scratches at the ${way} wall and whines. There is something behind it.`); } }
    return out; };
  // the hound digs on the land; the pony's quick feet
  const burn0 = P.burn;
  P.burn = function (...a) { const out = burn0.apply(this, a), fl = this.floor; if (!fl || fl.number !== -1) return out;
    const dog = this.petName("dog");
    if (dog && !CM.isNight(this) && CM.hashSeed(`${this.seed}:dig:${this.clock || 0}`) % PT.digEvery === 0) { const r = CM.hashSeed(`${this.seed}:digwhat:${this.clock || 0}`) % 10;
      if (r < 5) { const g = 3 + (r * 2); this.gold += g; this.say(`${dog} digs at the roots and brings up an old purse: ${g} gold.`); }
      else if (r < 8 && CM.INGREDIENTS) { const ids = Object.keys(CM.INGREDIENTS), id = ids[r % ids.length]; this.gain([CM.ingredient(id)], "dug"); this.say(`${dog} noses out ${CM.INGREDIENTS[id].name.toLowerCase()} under the leaves.`); }
      else if (CM.CROPS && CM.seed) { const crops = Object.keys(CM.CROPS).filter((c) => !CM.CROPS[c].rare), c = crops[r % crops.length]; this.gain([CM.seed(c)], "dug"); this.say(`${dog} digs up a buried seed: ${CM.CROPS[c].name}.`); } }
    if (this.petName("pony") && (this.steps || 0) % 2 === 0) this.clock = Math.max(0, (this.clock || 0) - 1);   // (on the pony: every other step costs no time)
    return out; };
  const ow0 = P.overweight; P.overweight = function (...a) { const o = ow0.apply(this, a); if (!this.petName("pony") || !this.floor || !(this.floor.number === 0 || this.floor.number === -1)) return o;
    const cap = CM.carryCap(this.party) + (this.followerCarry ? this.followerCarry() : 0); return CM.bagWeight(this.bag) / (cap + PT.ponyCarry); };
  const wp0 = P.walkPace; P.walkPace = function (...a) { const p = wp0.apply(this, a); return this.petName("pony") && this.floor && this.floor.number === -1 ? p * 0.75 : p; };
  // the pony stays above
  const ef0 = P.enterFloor; P.enterFloor = function (number, how, at) { const from = this.floor ? this.floor.number : null, out = ef0.call(this, number, how, at);
    if (this.petName("pony") && from === 0 && CM.isDeep(number)) this.say(`${this.petName("pony")} is left tethered at the shaft's head, with a nosebag.`); return out; };
}
