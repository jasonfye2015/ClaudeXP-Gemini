"use strict";
// Enchanting at the Mage Tower (v32.1, UPGRADE_PLAN_27.md): relic shards - three from a guardian, five from the Lich
// King, one now and then from a champion (one in four), five from a relic broken at the Tower - and the Tower's
// enchanter at its doors. For shards and gold she gives a thing a word it lacks (a prefix or a suffix: one of three
// offered, the player's pick) or raises one of its words a tier (to the third). It may not take: the more a thing has
// had, the less likely; when it fails the shards are spent and the gold kept, and once in a while (one in six) the
// thing cracks - one of its words lost. The smith's own enchanting is as it was.
//   game.shards() -> count in the pack;  game.towerOffers(row) -> {add: [[where, word]...], raise: [word...]}
//   game.towerChance(row, how) -> 0..1;  game.towerEnchant(row, how, word) -> "" or why not;  game.breakRelic(row)
{ const TC = CM.TOWERCRAFT = { add: { shards: 3, gold: 120 }, raise: { shards: 4, gold: 180 }, crack: 1 / 6, guardian: 3, lich: 5, champion: 0.25, relic: 5 };
  CM.shard = () => ({ name: "Relic Shard", kind: "shard", power: 0, value: 40 });
  CM.BASES["Relic Shard"] = { id: "Relic Shard", kind: "shard", slot: null, tier: 0, group: "stuff" };
  const G = CM.Game.prototype, gearOk = (it) => it && it.slot && !["ring", "amulet"].includes(it.kind) && (it.kind === "weapon" || it.kind === "armor" || it.kind === "shield" || it.kind === "helm" || it.kind === "boots" || it.kind === "cloak");
  const tableFor = (it, where) => (where === "prefix" ? CM.AFFIXES.prefix[it.kind === "weapon" ? "weapon" : "armor"] : CM.AFFIXES.suffix);
  const wordsOf = (it) => ((it.props || {}).affixes || []).slice(), whereOf = (w) => (w.startsWith("of ") ? "suffix" : "prefix");
  const tierOf = (it, w) => (((it.props || {}).wordTiers || {})[w] || (it.props || {}).tier || 1);
  const negate = (a) => { const o = {}; for (const [k, v] of Object.entries(a)) { if (k === "stats") { o.stats = {}; for (const [s, d] of Object.entries(v)) o.stats[s] = -d; } else if (typeof v === "number" && !["vsUndead", "vsHide"].includes(k)) o[k] = -v; } return o; };
  const strip = (props) => { for (const [k, v] of Object.entries(props)) { if (k === "stats") { for (const s of Object.keys(v)) if (!props.stats[s]) delete props.stats[s]; } else if (v === 0) delete props[k]; } };
  const rename = (it) => { const p = it.props || {}, w = p.affixes || [], pre = w.find((x) => !x.startsWith("of ")), suf = w.find((x) => x.startsWith("of "));
    it.name = `${pre ? pre + " " : ""}${p.element && CM.ELEMENTS[p.element] ? CM.ELEMENTS[p.element].prefix + " " : ""}${it.base || CM.baseName(it)}${suf ? " " + suf : ""}${p.bonus ? ` +${p.bonus}` : ""}`;
    p.rarity = p.cursed ? "cursed" : p.unique ? p.rarity : w.length >= 2 ? "rare" : w.length ? "fine" : p.rarity; };
  Object.assign(G, {
    deepestReached() { const ns = Object.keys(this.deltas || {}).concat(Object.keys(this.floors || {})).map(Number).filter((n) => n > 0 && n < 1000); if (this.floor && this.floor.number > 0 && this.floor.number < 1000) ns.push(this.floor.number); return ns.length ? Math.max(...ns) : 0; },
    shards() { return this.bag.filter((i) => i.kind === "shard").length; },
    takeShards(n) { for (let i = this.bag.length - 1; i >= 0 && n > 0; i--) if (this.bag[i].kind === "shard") { this.bag.splice(i, 1); n--; } },
    giveShards(n, why) { if (n <= 0) return; const its = []; for (let i = 0; i < n; i++) its.push(CM.shard()); this.gain(its, "relic"); if (why) this.say(`${why}: ${CM.plural(n, "relic shard")}.`); },
    atTowerDoor() { const fl = this.floor; return Boolean(fl && fl.number === -1 && CM.MAGE_DOOR && Math.abs(fl.pos[0] - CM.MAGE_DOOR[0]) + Math.abs(fl.pos[1] - CM.MAGE_DOOR[1]) <= 1); },
    towerOffers(row) { const it = this.bag[row]; if (!gearOk(it) || (it.props || {}).unique || (it.props || {}).relic) return { add: [], raise: [] };
      const p = it.props || {}, words = wordsOf(it), deep = this.deepestReached() > CM.LAST_FLOOR, add = [];
      for (const where of ["prefix", "suffix"]) { if (words.some((w) => whereOf(w) === where)) continue;
        const pool = Object.entries(tableFor(it, where)).filter(([, a]) => (!a.deep || deep) && (!a.weapon || it.kind === "weapon") && !(a.element && p.element));
        const h = CM.hashSeed(`${this.seed}:tower:${it.name}:${where}:${p.towerTries || 0}`); for (let k = 0; k < 3 && pool.length; k++) { const [w] = pool.splice((h >> (k * 3)) % pool.length, 1)[0]; add.push([where, w]); } }
      return { add, raise: words.filter((w) => tierOf(it, w) < 3 && !p.cursed) }; },
    towerChance(row, how) { const it = this.bag[row]; if (!it) return 0; const p = it.props || {}, n = wordsOf(it).length;
      return Math.max(0.3, (how === "raise" ? 0.7 : 0.85) - 0.1 * n - 0.1 * (p.towerDone || 0)); },
    towerWhy(row, how, word) { if (!this.atTowerDoor()) return "The enchanter keeps the Mage Tower's doors, in the Wood."; const it = this.bag[row]; if (!gearOk(it)) return "She works on gear that is worn: weapons, armour, shields, helms, boots, cloaks.";
      const O = this.towerOffers(row), C = TC[how]; if (!C) return "Add a word, or raise one.";
      if (how === "add" && !O.add.some(([, w]) => w === word)) return "That word isn't one she offers for it."; if (how === "raise" && !O.raise.includes(word)) return "That word can't be raised.";
      if (this.shards() < C.shards) return `She wants ${CM.plural(C.shards, "relic shard")}; the pack has ${this.shards()}.`; const gold = C.gold * (how === "raise" ? tierOf(it, word) : 1); if (this.gold < gold) return `And ${gold} gold.`; return ""; },
    towerEnchant(row, how, word) { const why = this.towerWhy(row, how, word); if (why) return why; this.logAct && this.logAct("towerEnchant", row, how, word);
      const it = this.bag[row], p = it.props = it.props || {}, C = TC[how], gold = C.gold * (how === "raise" ? tierOf(it, word) : 1), chance = this.towerChance(row, how);
      this.takeShards(C.shards); this.gold -= gold; this.spend && this.spend("tower", gold); p.towerTries = (p.towerTries || 0) + 1;
      const roll = (CM.hashSeed(`${this.seed}:towerroll:${it.name}:${p.towerTries}:${this.clock || 0}`) % 1000) / 1000;
      if (roll < chance) {
        const where = how === "add" ? whereOf(word) : null, base = tableFor(it, whereOf(word))[word];
        if (how === "add") { const tier = CM.affixTier(Math.max(1, this.deepestReached())); CM.applyProps(it, CM.scaledAffix(base, tier)); p.affixes = wordsOf(it).concat(word); (p.wordTiers = p.wordTiers || {})[word] = tier; it.value += (where === "prefix" ? 60 : 90) * tier; }
        else { const t0 = tierOf(it, word), t1 = t0 + 1; CM.applyProps(it, negate(CM.scaledAffix(base, t0))); CM.applyProps(it, CM.scaledAffix(base, t1)); strip(p); (p.wordTiers = p.wordTiers || {})[word] = t1; it.value += 60; }
        p.towerDone = (p.towerDone || 0) + 1; rename(it); this.sound("spell"); this.tally.enchanted = (this.tally.enchanted || 0) + 1;
        this.say(`The enchanter's hands go still over it, and the light in the shards goes into the ${CM.baseName(it).toLowerCase()}: ${it.name}.`);
        if (this.achieve) this.achieve("towercraft");
      } else {
        let cracked = ""; if ((CM.hashSeed(`${this.seed}:towercrack:${p.towerTries}:${it.name}`) % 1000) / 1000 < TC.crack && wordsOf(it).length) { const w = wordsOf(it)[0], base = tableFor(it, whereOf(w))[w];
          if (base) { CM.applyProps(it, negate(CM.scaledAffix(base, tierOf(it, w)))); strip(p); } p.affixes = wordsOf(it).filter((x) => x !== w); if (p.wordTiers) delete p.wordTiers[w]; rename(it); cracked = ` A hairline runs through it: "${w}" is gone from it.`; }
        this.sound("miss"); this.say(`The shards flare and go grey. It didn't take.${cracked}`);
      }
      this.saveRun(); this.emit("change"); return ""; },
    breakRelic(row) { if (!this.atTowerDoor()) return "Relics are broken at the Mage Tower, where it is safe to."; const it = this.bag[row]; if (!it || !(it.props || {}).relic) return "Only a guardian's relic breaks into shards.";
      this.logAct && this.logAct("breakRelic", row); this.bag.splice(row, 1); this.sound("slam"); this.giveShards(TC.relic, `${it.name} breaks along its old seams`); this.saveRun(); this.emit("change"); return ""; },
  });
  CM.ACHIEVEMENTS.towercraft = { name: "Words of Power", what: "Have the Mage Tower's enchanter put a word on a thing", title: "the Inscribed" };
  const sg0 = G.slayGuardian; G.slayGuardian = function (m) { const out = sg0.call(this, m); if (m && !m.echo) this.giveShards(TC.guardian, "In what it left"); return out; };
  const em0 = G.emit; G.emit = function (ev, ...a) { if (ev === "crowned") this.giveShards(TC.lich, "Where the crown fell"); return em0.call(this, ev, ...a); };
  const wf0 = G.wonFight; G.wonFight = function (...a) { const before = (this.tally && this.tally.champions) || 0, out = wf0.apply(this, a), after = (this.tally && this.tally.champions) || 0;
    for (let k = before + 1; k <= after; k++) if ((CM.hashSeed(`${this.seed}:champshard:${k}`) % 100) / 100 < TC.champion) this.giveShards(1, "On the champion"); return out; };
}
