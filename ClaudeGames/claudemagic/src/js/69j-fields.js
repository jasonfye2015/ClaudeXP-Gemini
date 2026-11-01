"use strict";
// The South Fields (v19.0, UPGRADE_PLAN_14.md phase 0): the open bowl at the bottom of the town, under the south wall,
// made farmland. A village building (four levels: 24, 48, 72 and 100 plots); a plot is tilled with the shed's hoe, sown
// with a seed from the pack, watered from the can (ten waterings, filled at the trough), and picked when ripe. A crop
// grows a day for every dawn the party sees after a day it was watered (rain waters every plot); in winter only the
// winter crops grow. Some crops stand and fruit again after picking. The seed shed sells the season's seeds and the can.
// The crops are the Glade farm's own and more (CM.CROPS, CM.FOODS), so a seed is a seed anywhere.
//
//   CM.SOUTHFIELDS, CM.fieldCells(level)        -> the plots for a level of the building, as [x, y] on the town floor
//   game.fields() / fieldsDawns()          -> the state (village.fields); the dawns since the last look, applied
//   game.fieldTill/Sow/Water/Pick(key)     -> the work, one plot at a time ("" or why not); fieldTend(key) the next job
//   game.fieldFill(), fieldBuy(crop, n), fieldBuyCan()   -> the trough and the shed
// The window and the pictures: 76zzzj-fields.js, 36c-cropart.js.
{ const FD = CM.SOUTHFIELDS = { shed: [33, 35], trough: [11, 35], can: 10, canGold: 25, hoeMinutes: 6,
    rects: [null, [16, 33, 27, 34], [14, 33, 29, 35], [13, 32, 30, 35], [12, 32, 31, 36]],   // [x0, y0, x1, y1] by level
    area: [10, 31, 35, 37] };                                               // (the fields and their edges: where "at the fields" holds)
  CM.fieldCells = (level) => { const R = FD.rects[Math.max(0, Math.min(4, level || 0))]; if (!R) return []; const out = []; for (let y = R[1]; y <= R[3]; y++) for (let x = R[0]; x <= R[2]; x++) out.push([x, y]); return out; };
  CM.VILLAGE.fields = { name: "The South Fields", costs: [40, 100, 180, 260], levels: [
    "Twenty-four plots in the bowl under the south wall, a seed shed and a trough",
    "Forty-eight plots, fenced (island timber)", "Seventy-two plots, the paths laid in stone", "A hundred plots: the whole bowl, and a bar of iron for the shed's tools"] };
  if (CM.VILLAGE_MATS) CM.VILLAGE_MATS.fields = { 2: [["timber", 24]], 3: [["stone", 32], ["timber", 16]], 4: [["stone", 48], ["bars", 2]] };
  // the crops: the Glade farm's six, given days and prices, and the fields' own. [id, name, sow seasons, days, yield, regrows (days), price, seed price]
  const C = [
    ["wheat", "Wheat", ["spring"], 4, 3, 0, 6, 8], ["barley", "Barley", ["spring"], 4, 3, 0, 6, 8], ["beans", "Beans", ["spring", "autumn"], 4, 4, 2, 6, 10], ["cabbage", "Cabbage", ["spring", "autumn"], 4, 2, 0, 12, 10],
    ["turnip", "Turnip", ["spring", "summer", "autumn"], 4, 3, 0, 7, 8], ["hops", "Hops", ["summer"], 4, 2, 3, 14, 12],
    ["potato", "Potato", ["spring"], 5, 3, 0, 9, 10], ["carrot", "Carrot", ["spring", "autumn"], 4, 3, 0, 8, 8], ["radish", "Radish", ["spring", "autumn"], 3, 2, 0, 7, 6], ["lettuce", "Lettuce", ["spring", "autumn"], 3, 2, 0, 8, 6],
    ["peas", "Peas", ["spring"], 5, 3, 2, 7, 10], ["strawberry", "Strawberry", ["spring"], 6, 2, 3, 16, 20], ["onion", "Onion", ["spring"], 5, 3, 0, 8, 8], ["beet", "Beet", ["spring", "autumn"], 4, 2, 0, 9, 8],
    ["parsnip", "Parsnip", ["spring"], 4, 2, 0, 10, 8], ["cauliflower", "Cauliflower", ["spring"], 6, 1, 0, 34, 24], ["tulip", "Tulip", ["spring"], 4, 1, 0, 22, 14], ["rose", "Rose", ["spring", "summer"], 5, 1, 4, 26, 18],
    ["tomato", "Tomato", ["summer"], 6, 3, 3, 10, 16], ["pepper", "Pepper", ["summer"], 6, 2, 3, 13, 16], ["chili", "Chili", ["summer"], 5, 3, 3, 9, 14], ["corn", "Corn", ["summer"], 7, 2, 4, 11, 16],
    ["watermelon", "Watermelon", ["summer"], 8, 1, 0, 48, 30], ["melon", "Melon", ["summer"], 7, 1, 0, 40, 26], ["cucumber", "Cucumber", ["summer"], 5, 3, 2, 8, 12], ["eggplant", "Eggplant", ["summer"], 6, 2, 3, 12, 14],
    ["zucchini", "Zucchini", ["summer"], 5, 3, 2, 7, 10], ["sunflower", "Sunflower", ["summer"], 6, 2, 0, 15, 12], ["blueberry", "Blueberries", ["summer"], 7, 4, 3, 8, 24], ["sweetpotato", "Sweet potato", ["summer"], 6, 3, 0, 10, 12],
    ["pumpkin", "Pumpkin", ["autumn"], 8, 1, 0, 52, 30], ["squash", "Squash", ["autumn"], 6, 2, 0, 16, 14], ["broccoli", "Broccoli", ["autumn"], 5, 2, 0, 14, 12], ["redcabbage", "Red cabbage", ["autumn"], 5, 2, 0, 15, 12],
    ["grapes", "Grapes", ["autumn"], 7, 3, 3, 14, 24], ["celery", "Celery", ["autumn"], 5, 2, 0, 11, 10],
    ["leek", "Leek", ["autumn", "winter"], 6, 2, 0, 14, 12], ["garlic", "Garlic", ["autumn", "winter"], 6, 3, 0, 12, 12], ["kale", "Kale", ["autumn", "winter"], 4, 2, 3, 10, 10],
  ];
  for (const [id, name, sow, days, yields, regrow, price, seed] of C) {
    CM.CROPS[id] = Object.assign(CM.CROPS[id] || {}, { name, sow, yields, days, regrow, price, seedPrice: seed, winter: sow.includes("winter") });
    if (!CM.FOODS[id]) { CM.FOODS[id] = { name }; CM.INGREDIENTS[id] = { name, band: -1, food: true }; CM.BASES[name] = { id: name, kind: "ingredient", slot: null, tier: 0, group: "ingredient" }; }
    const sn = `${name} seed`; if (!CM.BASES[sn]) CM.BASES[sn] = { id: sn, kind: "seed", slot: null, tier: 0, group: "stuff" };
  }
  FD.produce = (crop) => { const it = CM.food(crop); it.value = CM.CROPS[crop].price || 8; return it; };
  const keyOf = (x, y) => `${x},${y}`;
  Object.assign(CM.Game.prototype, {
    fields() { this.village = this.village || {}; const F = this.village.fields = this.village.fields || { plots: {}, water: 0, can: false, days: 0, picked: 0, pick: null }; F.plots = F.plots || {}; return F; },
    fieldsLevel() { return this.villageLevel("fields"); },
    isPlot(key) { const [x, y] = String(key).split(",").map(Number); return CM.fieldCells(this.fieldsLevel()).some(([a, b]) => a === x && b === y); },
    atFields() { const fl = this.floor; if (!fl || fl.number !== 0 || this.fieldsLevel() < 1) return false; const [x, y] = fl.pos, A = FD.area; return x >= A[0] && x <= A[2] && y >= A[1] && y <= A[3]; },
    // the town floor wears the fields: a plot on every cell of the level, the earth turned where tilled, the shed and the trough
    fieldsApply(fl) { fl = fl || this.floor; if (!fl || fl.number !== 0) return; const L = this.fieldsLevel(), F = this.fields(); if (L < 1) return;
      for (const [x, y] of CM.fieldCells(L)) { const k = keyOf(x, y), t = fl.things[k]; if (!t || t.type === "plot") fl.things[k] = { type: "plot" }; CM.setGround && CM.setGround(fl, x, y, F.plots[k] && F.plots[k].t ? "tilled" : "dirt"); }
      fl.things[keyOf(...FD.shed)] = { type: "fieldshed" }; fl.things[keyOf(...FD.trough)] = { type: "trough" }; },
    // the dawns since the last look
    fieldsDawns() { if (this.fieldsLevel() < 1) return 0; const day = CM.dayOf(this), n = day - (this.fieldsDay === undefined ? day : this.fieldsDay); this.fieldsDay = day; if (n <= 0) return 0;
      for (let i = 0; i < Math.min(n, 60); i++) this.fieldsDawn(day - n + i + 1); this.saveVillage && this.saveVillage(); return n; },
    fieldsDawn(day) { const F = this.fields(), season = CM.season(this), rain = CM.weatherOf(this.seed, day, season) === "rain"; F.days += 1; let ripe = 0;
      for (const P of Object.values(F.plots)) { if (!P.crop) { P.w = false; continue; } const K = CM.CROPS[P.crop]; if (!K) { P.crop = null; continue; }
        const can = season !== "winter" || K.winter; if ((P.w || rain) && can && !P.ripe) { P.g = (P.g || 0) + 1; P.dry = 0; if (P.g >= (P.need || K.days || 4)) { P.ripe = true; ripe++; } } else if (!P.ripe) P.dry = (P.dry || 0) + 1; P.w = false; }
      if (rain) this.fieldsNote = "Rain in the night: the fields are watered."; if (ripe) this.say(`${ripe === 1 ? "A plot" : `${ripe} plots`} in the South Fields ${ripe === 1 ? "is" : "are"} ripe.`); },
    // what stage a plot shows: "bare", "tilled", "sown", 1-3 growing, "ripe", "after" (picked, fruiting again)
    plotStage(key) { const P = this.fields().plots[key]; if (!P || !P.t) return "bare"; if (!P.crop) return "tilled"; if (P.ripe) return "ripe"; const K = CM.CROPS[P.crop], need = P.need || K.days || 4, g = P.g || 0;
      if (P.picks && g === 0) return "after"; if (g === 0) return "sown"; return Math.min(3, 1 + Math.floor((g / need) * 3)); },
    fieldWhy(key) { if (this.fieldsLevel() < 1) return "The South Fields aren't laid out yet (the village's window)."; if (!this.floor || this.floor.number !== 0) return "The fields are in town."; if (!this.isPlot(key)) return "That isn't one of the plots."; if (!this.atFields()) return "You need to be at the fields."; return ""; },
    fieldTill(key) { const why = this.fieldWhy(key); if (why) return why; const F = this.fields(), P = F.plots[key] = F.plots[key] || {}; if (P.t) return "Already turned."; this.logAct && this.logAct("fieldTill", key); return this._fieldTill(key); },
    _fieldTill(key) { const F = this.fields(), P = F.plots[key] = F.plots[key] || {}; P.t = 1; this.clock = (this.clock || 0) + FD.hoeMinutes; const [x, y] = key.split(",").map(Number); if (this.floor && CM.setGround) CM.setGround(this.floor, x, y, "tilled"); this.sound && this.sound("dig"); this.emit && this.emit("floor", this.floor); return ""; },
    fieldSow(key, crop) { const why = this.fieldWhy(key); if (why) return why; const P = this.fields().plots[key]; if (!P || !P.t) return "Turn the earth first."; if (P.crop) return "Something's growing there.";
      const K = CM.CROPS[crop]; if (!K) return "No such seed."; const i = this.bag.findIndex((it) => it.kind === "seed" && it.crop === crop); if (i < 0) return `No ${K.name.toLowerCase()} seed in the pack (the shed sells them).`;
      if (!K.sow.includes(CM.season(this))) return `${K.name} is sown in ${K.sow.join(" or ")}.`; this.logAct && this.logAct("fieldSow", key, crop); return this._fieldSow(key, crop, i); },
    _fieldSow(key, crop, i) { const P = this.fields().plots[key]; this.bag.splice(i, 1); Object.assign(P, { crop, g: 0, ripe: false, picks: 0, w: false, dry: 0, need: CM.CROPS[crop].days || 4 }); this.fields().pick = crop; this.sound && this.sound("step"); this.emit && this.emit("change"); return ""; },
    fieldWater(key) { const why = this.fieldWhy(key); if (why) return why; const F = this.fields(), P = F.plots[key]; if (!P || !P.crop) return "Nothing sown there to water."; if (P.ripe) return "It's ripe: pick it."; if (P.w) return "Watered already today.";
      if (!F.can) return `There's no can: the shed sells one (${FD.canGold} gold).`; if (F.water <= 0) return "The can is empty: fill it at the trough."; this.logAct && this.logAct("fieldWater", key); return this._fieldWater(key); },
    _fieldWater(key) { const F = this.fields(); F.plots[key].w = true; F.water -= 1; this.sound && this.sound("splash"); this.emit && this.emit("change"); return ""; },
    fieldPick(key) { const why = this.fieldWhy(key); if (why) return why; const P = this.fields().plots[key]; if (!P || !P.crop) return "Nothing growing there."; if (!P.ripe) return "Not ripe yet."; this.logAct && this.logAct("fieldPick", key); return this._fieldPick(key); },
    _fieldPick(key) { const F = this.fields(), P = F.plots[key], K = CM.CROPS[P.crop], got = []; for (let n = 0; n < (K.yields || 1); n++) got.push(FD.produce(P.crop));
      if (CM.hashSeed(`${this.seed}:fieldseed:${key}:${F.days}:${F.picked}`) % 4 === 0) got.push(CM.seed(P.crop));   // (now and then a head goes to seed: one back)
      this.gain(got, "fields"); F.picked += 1; this.tally.fieldPicks = (this.tally.fieldPicks || 0) + 1; const name = K.name;
      if (K.regrow) { P.ripe = false; P.g = 0; P.need = K.regrow; P.picks = (P.picks || 0) + 1; } else { P.crop = null; P.ripe = false; P.g = 0; P.picks = 0; }
      this.say(`${CM.plural(K.yields || 1, name)} from the field${K.regrow ? `; it will fruit again in ${K.regrow} days` : ""}.`); this.sound && this.sound("coin"); this.emit && this.emit("change"); return ""; },
    fieldClear(key) { const why = this.fieldWhy(key); if (why) return why; const P = this.fields().plots[key]; if (!P || !P.crop) return "Nothing to pull up."; this.logAct && this.logAct("fieldClear", key); P.crop = null; P.ripe = false; P.g = 0; P.picks = 0; this.emit && this.emit("change"); return ""; },
    // Space on a plot: whatever it wants next (sowing the last seed sown, or the one chosen in the window)
    fieldNext(key) { const P = this.fields().plots[key]; if (!P || !P.t) return "till"; if (!P.crop) return "sow"; if (P.ripe) return "pick"; if (!P.w) return "water"; return "wait"; },
    _fieldTend(key) { const why = this.fieldWhy(key); if (why) return why; const job = this.fieldNext(key), F = this.fields();
      if (job === "till") return this._fieldTill(key);
      if (job === "sow") { const crop = F.pick, i = crop ? this.bag.findIndex((it) => it.kind === "seed" && it.crop === crop) : -1; if (i < 0 || !CM.CROPS[crop].sow.includes(CM.season(this))) return "pick"; return this._fieldSow(key, crop, i); }
      if (job === "pick") return this._fieldPick(key);
      if (job === "water") { if (!F.can) return `There's no can: the shed sells one (${FD.canGold} gold).`; if (F.water <= 0) return "The can is empty: fill it at the trough."; return this._fieldWater(key); }
      return "It's watered for today."; },
    fieldTend(key) { this.logAct && this.logAct("fieldTend", key); return this._fieldTend(key); },
    // the trough and the shed
    fieldFill() { if (!this.atFields()) return "The trough is at the fields."; const F = this.fields(); if (!F.can) return `There's no can: the shed sells one (${FD.canGold} gold).`; if (F.water >= FD.can) return "The can is full.";
      this.logAct && this.logAct("fieldFill"); F.water = FD.can; this.sound && this.sound("splash"); this.emit && this.emit("change"); return ""; },
    fieldBuyCan() { if (!this.atFields()) return "The shed is at the fields."; const F = this.fields(); if (F.can) return "You have a can."; if (this.gold < FD.canGold) return `A can is ${FD.canGold} gold.`;
      this.logAct && this.logAct("fieldBuyCan"); this.gold -= FD.canGold; F.can = true; F.water = FD.can; this.sound && this.sound("coin"); this.emit && this.emit("change"); return ""; },
    seedPrice(crop) { const K = CM.CROPS[crop]; return Math.max(1, Math.round((K.seedPrice || 10) * (CM.festivalIs && CM.festivalIs(this, "sowing") ? 0.5 : 1))); },
    shedSeeds() { const s = CM.season(this); return Object.keys(CM.CROPS).filter((c) => CM.CROPS[c].sow.includes(s) && CM.CROPS[c].seedPrice); },
    fieldBuy(crop, n = 1) { if (!this.atFields()) return "The shed is at the fields."; if (!this.shedSeeds().includes(crop)) return "The shed hasn't that seed this season."; const cost = this.seedPrice(crop) * n; if (this.gold < cost) return `${n} seed${n > 1 ? "s" : ""} would be ${cost} gold.`;
      this.logAct && this.logAct("fieldBuy", crop, n); this.gold -= cost; const got = []; for (let k = 0; k < n; k++) got.push(CM.seed(crop)); this.gain(got, "fields"); this.fields().pick = crop; this.emit && this.emit("change"); return ""; },
  });
  // every piece of work is kept with the village at once
  for (const m of ["_fieldTill", "_fieldSow", "_fieldWater", "_fieldPick", "fieldClear", "fieldFill", "fieldBuyCan", "fieldBuy"]) { const f0 = CM.Game.prototype[m]; CM.Game.prototype[m] = function (...a) { const out = f0.apply(this, a); if (!out && this.saveVillage) this.saveVillage(); return out; }; }
  // into the town: the floor wears the fields; the dawns are counted on the way in
  { const G = CM.Game.prototype, enter0 = G.enterFloor, use0 = G.use, build0 = G.build;
    G.enterFloor = function (...a) { const out = enter0.apply(this, a); if (this.floor && this.floor.number === 0) { this.fieldsApply(); this.fieldsDawns(); } return out; };
    G.build = function (id, ...a) { const out = build0.call(this, id, ...a); if (id === "fields" && !out && this.floor && this.floor.number === 0) { this.fieldsApply(); this.emit && this.emit("floor", this.floor); } return out; };
    // Space: on a plot, its next job (or the window, to choose a seed); at the trough, the can filled; at the shed, the window
    G.use = function (...a) { const fl = this.floor, t = fl && this.mode === "explore" && fl.things[keyOf(fl.pos[0], fl.pos[1])];
      if (t && fl.number === 0 && (t.type === "plot" || t.type === "trough" || t.type === "fieldshed")) { this.logAct && this.logAct("use"); const k = keyOf(fl.pos[0], fl.pos[1]);
        if (t.type === "plot") { const r = this._fieldTend(k); if (r === "pick") this.emit("fields", k); else if (r) this.say(r); return; }
        if (t.type === "trough") { const F = this.fields(); if (F.can && F.water < FD.can) { F.water = FD.can; this.saveVillage && this.saveVillage(); this.sound && this.sound("splash"); this.say("The can, filled at the trough."); this.emit("change"); } else this.emit("fields", null); return; }
        this.say("The seed shed: seeds for the season on the shelves, a hoe on its nail, and the smell of earth."); this.emit("fields", null); return; }
      return use0.apply(this, a); }; }
  // the bowl is named, once it's farmland
  { const tp0 = CM.townPlace; CM.townPlace = function (fl, x, y) { const out = tp0.call(this, fl, x, y), A = FD.area; if (out === "the yards" && fl && fl.things && fl.things[FD.shed.join(",")] && x >= A[0] && x <= A[2] && y >= A[1] && y <= A[3]) return "the South Fields"; return out; }; }
  // a place on the world map, and a line on the goals page
  if (CM.WORLDMAP) { CM.WORLDMAP.PLACES.push(["fields", "The South Fields", 0, () => FD.shed, "seeds, the can, the plots", false]); CM.WORLDMAP.byId.fields = CM.WORLDMAP.PLACES[CM.WORLDMAP.PLACES.length - 1]; }
}
