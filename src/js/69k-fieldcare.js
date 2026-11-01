"use strict";
// The South Fields, water and quality (v19.1, UPGRADE_PLAN_14.md phase 1).
// - Thirst: a crop not watered stalls; four dry dawns in a row and it withers (the plot keeps its turned earth).
// - Weeds: turned earth left bare three dawns grows weeds, and a growing plot catches them now and then; a weedy plot
//   doesn't grow until they're pulled (Space, or a click, pulls them first). Pulled weeds are trimmings.
// - Crows: a ripe plot left standing may be taken in the night, unless the fields have a scarecrow (the shed's).
// - Quality, one to five stars, set when a crop is picked: two to start; one more if it was never dry, one if the plot
//   was composted for it, one if the plot grew something else last (the soil rested), and now and then one for luck.
//   A star is a quarter more on the price; the stars are in the produce's name.
// - Trimmings and compost: every picking, pulled weed and withered plant leaves trimmings; five in the bin make a load
//   of compost three dawns on. With "compost when sowing" on, each sowing takes a load if there is one.
// - Giants: when a 3x3 of one giant kind (pumpkin, watermelon, melon, cabbage, cauliflower) stands ripe together at
//   dawn, now and then it grows into one giant: picked, it gives fifteen to twenty, at its stars.
// The window's side: 76zzzk-fieldcare.js.
{ const FD = CM.SOUTHFIELDS, FC = CM.FIELDCARE = { wiltAfter: 4, weedAfter: 3, weedChance: 0.04, crowChance: 0.12, scarecrowGold: 60, binFor: 5, binDays: 3, giantChance: 0.3, giantKinds: ["pumpkin", "watermelon", "melon", "cabbage", "cauliflower"], bin: [11, 33], scarecrow: [33, 32] };
  const G = CM.Game.prototype, keyOf = (x, y) => `${x},${y}`;
  FC.roll = (g, what) => (CM.hashSeed(`${g.seed}:fieldcare:${what}:${g.fields().days}`) % 10000) / 10000;
  FC.produce = (crop, q) => { const it = FD.produce(crop); if (q) { it.q = q; it.name = `${it.name} ${CM.stars ? CM.stars(q) : "*".repeat(q)}`; it.value = Math.round((it.value || 8) * (1 + 0.25 * (q - 1))); } return it; };
  // the stars a plot would give if picked now
  FC.quality = (g, key) => { const P = g.fields().plots[key]; if (!P || !P.crop) return 0; let q = 2; if (!P.everDry) q++; if (P.comp) q++; if (P.rested) q++; if (P.lucky) q++; return Math.max(1, Math.min(5, q)); };
  const dawn0 = G.fieldsDawn, sow0 = G._fieldSow, tend0 = G._fieldTend, next0 = G.fieldNext, stage0 = G.plotStage, till0 = G._fieldTill;
  Object.assign(G, {
    fieldsDawn(day) { const held = Object.values(this.fields().plots).filter((P) => P.weed && P.crop && !P.ripe).map((P) => [P, P.g, P.ripe]);   // (a weedy plot doesn't grow)
      dawn0.call(this, day); for (const [P, g, r] of held) { P.g = g; P.ripe = r; } const F = this.fields(); F.trim = F.trim || 0; F.bin = F.bin || []; const notes = [];
      for (const [k, P] of Object.entries(F.plots)) { if (!P.t) continue;
        if (P.crop && !P.ripe && (P.dry || 0) > 0) P.everDry = true;
        if (P.crop && !P.ripe && (P.dry || 0) >= FC.wiltAfter) { notes.push(`the ${CM.CROPS[P.crop].name.toLowerCase()} withered`); P.last = P.crop; P.crop = null; P.g = 0; P.giant = null; P.withered = true; F.trim += 1; continue; }
        if (!P.crop) { P.bare = (P.bare || 0) + 1; if (P.bare >= FC.weedAfter) P.weed = true; }
        else if (!P.ripe && FC.roll(this, `weed:${k}`) < FC.weedChance) P.weed = true;
        if (P.ripe) { P.standing = (P.standing || 0) + 1; if (P.standing >= 2 && !F.scarecrow && !P.giant && FC.roll(this, `crow:${k}`) < FC.crowChance) { notes.push(`crows had the ${CM.CROPS[P.crop].name.toLowerCase()}`); P.last = P.crop; P.crop = null; P.ripe = false; P.g = 0; P.standing = 0; } } }
      // the bin
      while (F.trim >= FC.binFor) { F.trim -= FC.binFor; F.bin.push(F.days + FC.binDays); } const ready = F.bin.filter((d) => d <= F.days).length; if (ready) { F.compost = (F.compost || 0) + ready; F.bin = F.bin.filter((d) => d > F.days); }
      // giants: a 3x3 of one giant kind, all ripe
      for (const [k, P] of Object.entries(F.plots)) { if (!P.ripe || P.giant || !FC.giantKinds.includes(P.crop)) continue; const [x, y] = k.split(",").map(Number), block = [];
        for (let dy = 0; dy < 3; dy++) for (let dx = 0; dx < 3; dx++) { const Q = F.plots[keyOf(x + dx, y + dy)]; if (Q && Q.ripe && Q.crop === P.crop && !Q.giant && this.isPlot(keyOf(x + dx, y + dy))) block.push(keyOf(x + dx, y + dy)); }
        if (block.length === 9 && FC.roll(this, `giant:${k}`) < FC.giantChance) { const mid = keyOf(x + 1, y + 1); for (const b of block) F.plots[b].giant = mid; notes.push(`a giant ${CM.CROPS[P.crop].name.toLowerCase()} has grown`); } }
      if (notes.length) this.say(`In the South Fields: ${notes.join("; ")}.`); },
    _fieldTill(key) { const out = till0.call(this, key), P = this.fields().plots[key]; if (P) { P.bare = 0; P.weed = false; } return out; },
    _fieldSow(key, crop, i) { const F = this.fields(), P = F.plots[key], rested = Boolean(P.last && P.last !== crop); const out = sow0.call(this, key, crop, i);
      Object.assign(P, { everDry: false, rested, comp: false, lucky: FC.roll(this, `luck:${key}:${crop}`) < 0.15, bare: 0, standing: 0, giant: null, withered: false });
      if (F.autoCompost && (F.compost || 0) > 0) { F.compost -= 1; P.comp = true; } return out; },
    fieldNext(key) { const P = this.fields().plots[key]; if (P && P.t && P.weed) return "weed"; return next0.call(this, key); },
    plotStage(key) { const P = this.fields().plots[key]; if (P && P.t && !P.crop && P.withered) return "withered"; return stage0.call(this, key); },
    _fieldWeed(key) { const F = this.fields(), P = F.plots[key]; P.weed = false; P.bare = 0; F.trim = (F.trim || 0) + 1; this.sound && this.sound("step"); this.emit && this.emit("change"); this.saveVillage && this.saveVillage(); return ""; },
    fieldWeed(key) { const why = this.fieldWhy(key); if (why) return why; const P = this.fields().plots[key]; if (!P || !P.weed) return "No weeds there."; this.logAct && this.logAct("fieldWeed", key); return this._fieldWeed(key); },
    _fieldTend(key) { const P = this.fields().plots[key]; if (!this.fieldWhy(key) && P && P.t && P.weed) return this._fieldWeed(key); return tend0.call(this, key); },
    // picking: the stars, the trimmings, the giant
    _fieldPick(key) { const F = this.fields(), P = F.plots[key], K = CM.CROPS[P.crop], q = FC.quality(this, key), got = [];
      if (P.giant) { const mid = P.giant, n = 15 + (CM.hashSeed(`${this.seed}:giant:${mid}:${F.days}`) % 6); for (let i = 0; i < n; i++) got.push(FC.produce(P.crop, q));
        for (const [k, Q] of Object.entries(F.plots)) if (Q.giant === mid) { Q.last = Q.crop; Q.crop = null; Q.ripe = false; Q.g = 0; Q.giant = null; Q.picks = 0; Q.standing = 0; }
        F.trim = (F.trim || 0) + 4; F.giants = (F.giants || 0) + 1; this.gain(got, "fields"); F.picked += 1; this.say(`The giant ${K.name.toLowerCase()} comes in on a barrow: ${n} of them, ${CM.stars ? CM.stars(q) : q}.`); this.sound && this.sound("coin"); this.emit && this.emit("change"); this.saveVillage && this.saveVillage(); return ""; }
      for (let n = 0; n < (K.yields || 1); n++) got.push(FC.produce(P.crop, q));
      if (CM.hashSeed(`${this.seed}:fieldseed:${key}:${F.days}:${F.picked}`) % 4 === 0) got.push(CM.seed(P.crop));
      this.gain(got, "fields"); F.picked += 1; F.trim = (F.trim || 0) + 1; this.tally.fieldPicks = (this.tally.fieldPicks || 0) + 1; F.best = Math.max(F.best || 0, q);
      if (K.regrow) { P.ripe = false; P.g = 0; P.need = K.regrow; P.picks = (P.picks || 0) + 1; P.standing = 0; P.everDry = false; } else { P.last = P.crop; P.crop = null; P.ripe = false; P.g = 0; P.picks = 0; P.standing = 0; P.comp = false; P.bare = 0; }
      this.say(`${CM.plural(K.yields || 1, K.name)} from the field, ${CM.stars ? CM.stars(q) : q}${K.regrow ? `; it will fruit again in ${K.regrow} days` : ""}.`); this.sound && this.sound("coin"); this.emit && this.emit("change"); this.saveVillage && this.saveVillage(); return ""; },
    fieldCompost(key) { const why = this.fieldWhy(key); if (why) return why; const F = this.fields(), P = F.plots[key]; if (!P || !P.crop || P.ripe) return "Compost goes on a growing crop."; if (P.comp) return "Composted already."; if (!(F.compost > 0)) return "No compost in the bin yet.";
      this.logAct && this.logAct("fieldCompost", key); F.compost -= 1; P.comp = true; this.saveVillage && this.saveVillage(); this.emit && this.emit("change"); return ""; },
    fieldAutoCompost(on) { this.logAct && this.logAct("fieldAutoCompost", Boolean(on)); this.fields().autoCompost = Boolean(on); this.saveVillage && this.saveVillage(); return ""; },
    fieldBuyScarecrow() { if (!this.atFields()) return "The shed is at the fields."; const F = this.fields(); if (F.scarecrow) return "The fields have their scarecrow."; if (this.gold < FC.scarecrowGold) return `A scarecrow is ${FC.scarecrowGold} gold.`;
      this.logAct && this.logAct("fieldBuyScarecrow"); this.gold -= FC.scarecrowGold; F.scarecrow = true; this.fieldsApply(); this.emit && this.emit("floor", this.floor); this.saveVillage && this.saveVillage(); this.emit && this.emit("change"); return ""; },
  });
  // the bin and the scarecrow on the floor
  { const ap0 = G.fieldsApply; G.fieldsApply = function (fl) { ap0.call(this, fl); fl = fl || this.floor; if (!fl || fl.number !== 0 || this.fieldsLevel() < 1) return; fl.things[keyOf(...FC.bin)] = { type: "compostbin" }; if (this.fields().scarecrow) fl.things[keyOf(...FC.scarecrow)] = { type: "scarecrow" }; }; }
  // Space at the bin: what's in it
  { const use0 = G.use; G.use = function (...a) { const fl = this.floor, t = fl && this.mode === "explore" && fl.things[keyOf(fl.pos[0], fl.pos[1])];
      if (t && fl.number === 0 && t.type === "compostbin") { this.logAct && this.logAct("use"); const F = this.fields(); this.say(`The compost bin: ${F.trim || 0} of ${FC.binFor} trimmings toward the next load, ${(F.bin || []).length} load${(F.bin || []).length === 1 ? "" : "s"} rotting down, ${F.compost || 0} ready.`); this.emit("fields", null); return; }
      if (t && fl.number === 0 && t.type === "scarecrow") { this.logAct && this.logAct("use"); this.say("The scarecrow wears the merchant's old hat and looks pleased with itself. Nothing with wings comes near."); return; }
      return use0.apply(this, a); }; }
}
