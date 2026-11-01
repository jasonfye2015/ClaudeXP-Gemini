"use strict";
// The South Fields, the village's hands (v19.2, UPGRADE_PLAN_14.md phase 2).
// - Sprinklers, made at the shed from a bar and gold and set on a plot (which then grows nothing itself): copper waters
//   the four plots beside it, iron the eight round it, star-iron the twenty-four of a 5x5. They water at every dawn.
// - Cloches: a glass bell over one plot, so it grows in any season and can be sown with anything (a cloche, 30 gold and
//   two island stones from the pack or the satchel's count as the builders take it).
// - The plan: a crop marked for a plot; the crew keeps it sown.
// - The field crew, hired at the shed (one to three hands, a wage each dawn from the crew's purse - what the party puts
//   in it): every dawn each hand does up to fourteen jobs - pull weeds, pick the ripe into the silo, turn and sow the
//   planned plots (with seed from the silo's seed box, or bought from the shed out of the purse), and water what's
//   thirsty. The silo keeps what they pick (up to 600 things) until the party takes it.
// - The seed-maker: one of a crop, as picked, gives two of its seeds.
// - Tend everything: the party's own round in one go - weeds, the ripe, the plan sown from the pack, the can as far as
//   it goes. The window's side: 76zzzl-fieldhands.js.
{ const FD = CM.SOUTHFIELDS, FC = CM.FIELDCARE, FH = CM.FIELDHANDS = { hands: 3, wage: 6, jobs: 14, silo: 600, clocheGold: 30, clocheStone: 2, silo_at: [33, 33],
    SPRINKLERS: { copper: { name: "Copper sprinkler", gold: 30, bars: ["copper", "tin", "bronze"], reach: [[1, 0], [-1, 0], [0, 1], [0, -1]] },
      iron: { name: "Iron sprinkler", gold: 60, bars: ["iron", "steel"], reach: [] }, star: { name: "Star-iron sprinkler", gold: 150, bars: ["stariron"], reach: [] } } };
  for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) if (dx || dy) FH.SPRINKLERS.iron.reach.push([dx, dy]);
  for (let dy = -2; dy <= 2; dy++) for (let dx = -2; dx <= 2; dx++) if (dx || dy) FH.SPRINKLERS.star.reach.push([dx, dy]);
  const G = CM.Game.prototype, keyOf = (x, y) => `${x},${y}`, stone = () => CM.TOWNREQ && CM.TOWNREQ.byId && CM.TOWNREQ.byId.stone;
  FH.covered = (F) => { const out = new Set(); for (const [k, P] of Object.entries(F.plots)) { if (!P.spr) continue; const [x, y] = k.split(",").map(Number); for (const [dx, dy] of FH.SPRINKLERS[P.spr].reach) out.add(keyOf(x + dx, y + dy)); } return out; };
  const dawn0 = G.fieldsDawn, sow0 = G.fieldSow, stage0 = G.plotStage, next0 = G.fieldNext;
  Object.assign(G, {
    // the sprinklers water before the night's growing; the crew work after it
    fieldsDawn(day) { const F = this.fields(); for (const k of FH.covered(F)) { const P = F.plots[k]; if (P && P.crop) P.w = true; }
      dawn0.call(this, day); this.fieldsCrew(); },
    fieldsCrew() { const F = this.fields(), n = Math.min(FH.hands, F.crew || 0); if (!n) return; const pay = n * FH.wage; if ((F.purse || 0) < pay) { if (!F.unpaid) this.say("The field crew stood idle: their purse is empty."); F.unpaid = true; return; } F.purse -= pay; F.unpaid = false;
      let jobs = n * FH.jobs; const done = { weeds: 0, picked: 0, sown: 0, watered: 0 }; F.silo = F.silo || []; F.seedBox = F.seedBox || {}; const season = CM.season(this), wet = FH.covered(F);
      const cells = CM.fieldCells(this.fieldsLevel()).map(([x, y]) => keyOf(x, y));
      for (const k of cells) { if (jobs <= 0) break; const P = F.plots[k]; if (P && P.weed) { P.weed = false; P.bare = 0; F.trim = (F.trim || 0) + 1; jobs--; done.weeds++; } }
      for (const k of cells) { if (jobs <= 0) break; const P = F.plots[k]; if (P && P.ripe && F.silo.length < FH.silo) { const got = this._fieldPickQuiet(k); F.silo.push(...got.filter((i) => i.kind !== "seed")); for (const s of got.filter((i) => i.kind === "seed")) F.seedBox[s.crop] = (F.seedBox[s.crop] || 0) + 1; jobs--; done.picked++; } }
      for (const k of cells) { if (jobs <= 0) break; const P = F.plots[k] = F.plots[k] || {}; const want = P.plan; if (!want || P.crop || P.spr || P.weed) continue; const K = CM.CROPS[want]; if (!K || !(K.sow.includes(season) || P.cloche)) continue;
        if (!(F.seedBox[want] > 0)) { const cost = this.seedPrice(want); if (!K.seedPrice || (F.purse || 0) < cost) continue; F.purse -= cost; F.seedBox[want] = (F.seedBox[want] || 0) + 1; }
        if (!P.t) { P.t = 1; P.bare = 0; jobs--; if (jobs <= 0) break; } F.seedBox[want] -= 1; this.bag.push(CM.seed(want)); this._fieldSowQuiet(k, want, this.bag.length - 1); jobs--; done.sown++; }
      for (const k of cells) { if (jobs <= 0) break; const P = F.plots[k]; if (P && P.crop && !P.ripe && !P.w && !wet.has(k)) { P.w = true; jobs--; done.watered++; } }
      const bits = [done.picked && `picked ${done.picked}`, done.sown && `sowed ${done.sown}`, done.watered && `watered ${done.watered}`, done.weeds && `weeded ${done.weeds}`].filter(Boolean);
      if (bits.length) this.fieldsNote = `The crew ${bits.join(", ")} (${pay} gold in wages).`; },
    // the quiet versions the crew uses: no words, no sounds
    _fieldPickQuiet(k) { const say0 = this.say, sound0 = this.sound, gain0 = this.gain, got = []; this.say = () => {}; this.sound = () => {}; this.gain = (items) => { got.push(...items); return items; }; try { this._fieldPick(k); return got; } finally { this.say = say0; this.sound = sound0; this.gain = gain0; } },
    _fieldSowQuiet(k, crop, i) { const sound0 = this.sound, season0 = this.season, P = this.fields().plots[k]; this.sound = () => {}; if (P && P.cloche && !CM.CROPS[crop].sow.includes(CM.season(this))) this.season = CM.CROPS[crop].sow[0]; try { return this._fieldSow(k, crop, i); } finally { this.sound = sound0; this.season = season0; } },
    // under glass, any season: sowing and growing
    fieldSow(key, crop) { const P = this.fields().plots[key]; if (P && P.spr) return "A sprinkler stands there."; if (P && P.cloche && CM.CROPS[crop] && !CM.CROPS[crop].sow.includes(CM.season(this))) { const s0 = this.season; this.season = CM.CROPS[crop].sow[0]; try { return sow0.call(this, key, crop); } finally { this.season = s0; } } return sow0.call(this, key, crop); },
    plotStage(key) { const P = this.fields().plots[key]; if (P && P.spr) return "sprinkler"; return stage0.call(this, key); },
    fieldNext(key) { const P = this.fields().plots[key]; if (P && P.spr) return "wait"; if (P && !P.crop && P.plan && P.t && !P.weed) return "sow"; return next0.call(this, key); },
    // sprinklers, cloches and the plan
    fieldMakeSprinkler(kind) { if (!this.atFields()) return "The shed is at the fields."; const S = FH.SPRINKLERS[kind]; if (!S) return "No such sprinkler."; const i = this.bag.findIndex((it) => it.kind === "bar" && S.bars.includes(it.bar));
      if (i < 0) return `${S.name}: it wants a ${S.bars[0] === "stariron" ? "star-iron" : S.bars[0]} bar (the island, or the smelter).`; if (this.gold < S.gold) return `${S.name}: ${S.gold} gold for the work.`;
      this.logAct && this.logAct("fieldMakeSprinkler", kind); this.bag.splice(i, 1); this.gold -= S.gold; const F = this.fields(); F.sprinklers = F.sprinklers || {}; F.sprinklers[kind] = (F.sprinklers[kind] || 0) + 1; this.saveVillage && this.saveVillage(); this.emit && this.emit("change"); return ""; },
    fieldSetSprinkler(key, kind) { const why = this.fieldWhy(key); if (why) return why; const F = this.fields(), P = F.plots[key] = F.plots[key] || {}; if (P.spr) return "A sprinkler stands there already."; if (P.crop) return "Something's growing there."; if (!((F.sprinklers || {})[kind] > 0)) return "None of those made yet (the shed).";
      this.logAct && this.logAct("fieldSetSprinkler", key, kind); F.sprinklers[kind] -= 1; P.spr = kind; P.t = 1; P.weed = false; P.plan = null; this.saveVillage && this.saveVillage(); this.emit && this.emit("change"); return ""; },
    fieldLiftSprinkler(key) { const why = this.fieldWhy(key); if (why) return why; const F = this.fields(), P = F.plots[key]; if (!P || !P.spr) return "No sprinkler there."; this.logAct && this.logAct("fieldLiftSprinkler", key);
      F.sprinklers = F.sprinklers || {}; F.sprinklers[P.spr] = (F.sprinklers[P.spr] || 0) + 1; P.spr = null; this.saveVillage && this.saveVillage(); this.emit && this.emit("change"); return ""; },
    fieldCloche(key) { const why = this.fieldWhy(key); if (why) return why; const F = this.fields(), P = F.plots[key] = F.plots[key] || {}; if (P.cloche) return "Under glass already."; if (P.spr) return "A sprinkler stands there.";
      const S = stone(), have = S ? S.have(this) : 0; if (have < FH.clocheStone) return `A cloche wants ${FH.clocheStone} island stones for its rim.`; if (this.gold < FH.clocheGold) return `A cloche is ${FH.clocheGold} gold.`;
      this.logAct && this.logAct("fieldCloche", key); S.take(this, FH.clocheStone); this.gold -= FH.clocheGold; P.cloche = true; this.saveVillage && this.saveVillage(); this.emit && this.emit("change"); return ""; },
    fieldPlan(key, crop) { const why = this.fieldWhy(key); if (why) return why; if (crop && !CM.CROPS[crop]) return "No such crop."; const F = this.fields(), P = F.plots[key] = F.plots[key] || {}; if (P.spr) return "A sprinkler stands there.";
      this.logAct && this.logAct("fieldPlan", key, crop || null); P.plan = crop || null; this.saveVillage && this.saveVillage(); return ""; },
    // the crew, their purse, the silo
    fieldHire(n) { if (!this.atFields()) return "The shed is at the fields."; n = Math.max(0, Math.min(FH.hands, n | 0)); this.logAct && this.logAct("fieldHire", n); this.fields().crew = n; this.saveVillage && this.saveVillage(); this.emit && this.emit("change"); return ""; },
    fieldPurse(gold) { if (!this.atFields()) return "The shed is at the fields."; gold = Math.floor(gold); const F = this.fields(); if (gold > 0 && this.gold < gold) return `You have ${this.gold} gold.`; if (gold < 0 && (F.purse || 0) < -gold) return "The purse hasn't that much.";
      this.logAct && this.logAct("fieldPurse", gold); this.gold -= gold; F.purse = (F.purse || 0) + gold; this.saveVillage && this.saveVillage(); this.emit && this.emit("change"); return ""; },
    fieldTakeSilo() { if (!this.atFields()) return "The silo is at the fields."; const F = this.fields(); if (!(F.silo || []).length) return "The silo is empty."; this.logAct && this.logAct("fieldTakeSilo"); const got = F.silo.splice(0); this.gain(got, "fields"); this.saveVillage && this.saveVillage(); this.emit && this.emit("change"); return ""; },
    fieldSeedMaker(crop) { if (!this.atFields()) return "The seed-maker is in the shed."; const i = this.bag.findIndex((it) => it.kind === "ingredient" && it.ingredient === crop); if (i < 0 || !CM.CROPS[crop]) return "It wants one of the crop, picked."; this.logAct && this.logAct("fieldSeedMaker", crop);
      this.bag.splice(i, 1); this.gain([CM.seed(crop), CM.seed(crop)], "fields"); this.saveVillage && this.saveVillage(); this.emit && this.emit("change"); return ""; },
    // the party's own round
    fieldTendAll() { if (!this.atFields()) return "You need to be at the fields."; this.logAct && this.logAct("fieldTendAll"); const F = this.fields(), n = { weeds: 0, picked: 0, sown: 0, watered: 0 }, cells = CM.fieldCells(this.fieldsLevel()).map(([x, y]) => keyOf(x, y));
      const quiet = (fn) => { const s0 = this.say, so = this.sound; this.say = () => {}; this.sound = () => {}; try { return fn(); } finally { this.say = s0; this.sound = so; } };
      quiet(() => { for (const k of cells) { const P = F.plots[k]; if (!P) continue; if (P.weed) { this._fieldWeed(k); n.weeds++; } if (P.ripe) { this._fieldPick(k); n.picked++; } }
        for (const k of cells) { const P = F.plots[k]; if (!P || P.crop || P.spr || !P.plan) continue; const K = CM.CROPS[P.plan], i = this.bag.findIndex((it) => it.kind === "seed" && it.crop === P.plan); if (i < 0 || !K || !(K.sow.includes(CM.season(this)) || P.cloche)) continue; if (!P.t) this._fieldTill(k); this._fieldSow(k, P.plan, i); n.sown++; }
        for (const k of cells) { const P = F.plots[k]; if (P && P.crop && !P.ripe && !P.w && F.can && F.water > 0) { this._fieldWater(k); n.watered++; } } });
      const bits = [n.picked && `picked ${n.picked}`, n.sown && `sowed ${n.sown}`, n.watered && `watered ${n.watered}`, n.weeds && `weeded ${n.weeds}`].filter(Boolean);
      this.say(bits.length ? `A round of the fields: ${bits.join(", ")}.` : "A round of the fields: nothing wanted doing."); this.saveVillage && this.saveVillage(); this.emit && this.emit("change"); return ""; },
  });
  // the silo on the floor
  { const ap0 = G.fieldsApply; G.fieldsApply = function (fl) { ap0.call(this, fl); fl = fl || this.floor; if (!fl || fl.number !== 0 || this.fieldsLevel() < 1) return; if ((this.fields().crew || 0) > 0 || (this.fields().silo || []).length) fl.things[keyOf(...FH.silo_at)] = { type: "silo" }; }; }
  { const use0 = G.use; G.use = function (...a) { const fl = this.floor, t = fl && this.mode === "explore" && fl.things[keyOf(fl.pos[0], fl.pos[1])];
      if (t && fl.number === 0 && t.type === "silo") { this.logAct && this.logAct("use"); const F = this.fields(); this.say(`The silo: ${(F.silo || []).length} things in it, the crew's purse ${F.purse || 0} gold.`); this.emit("fields", null); return; }
      return use0.apply(this, a); }; }
}
