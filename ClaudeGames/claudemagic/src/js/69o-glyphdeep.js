"use strict";
// The Glyph Deep, the cabinet's side (v20.0, UPGRADE_PLAN_15.md): a lone arcade cabinet under a lean-to in a small
// clearing north of the Wood's road, west of the fields. One hero plays (any of the party still standing), starting on
// any level reached so far. The game is 64zzzc-glyph.js; the screen 76zzzp-glyph.js.
//   At the down stairs: down to the next level with everything, or home with it all. The first time each level's
//   stairs are reached, tickets, gold and a thing go straight to the party (once a level, ever).
//   Level 20: the Unwritten seals the way down; beaten, and the stairs reached, the deep's great prize (once).
//   The up stairs: home, without what this level gave. Death: home with a tenth of their health, without what this
//   level gave (what the levels before gave is kept). Experience always.
//   What comes home is the main game's own: weapons, armour, rings, amulets, potions, rations and seeds as they are;
//   the inscription cards as Claudescryption cards; the tickets as the Joker's; unread scrolls sold back for gold.
{ const GD = CM.GLYPH; CM.GLYPH_AT = [28, 28]; GD.clearing = [26, 27, 30, 29];
  // (v20.3) a green portal on the Keep-yard's south row (off the walk to the shaft), and its twin in the cabinet's clearing
  CM.PORTAL_YARD.glyph = [36, 22]; CM.GLYPH_PORTAL = [26, 28];
  GD.reward = (L) => ({ tickets: 10 + 4 * L, gold: 20 * L });
  GD.PRIZE = { tickets: 500, gold: 3000, items: 3, cards: 2, seeds: 3 };
  // the cabinet laid on the Wood
  { const mw = CM.makeWood; CM.makeWood = function (seed) { const fl = mw(seed), [x0, y0, x1, y1] = GD.clearing, k = (x, y) => `${x},${y}`;
      for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) { fl.grid[y][x] = 0; if (fl.kinds) delete fl.kinds[k(x, y)]; (fl.ground = fl.ground || {})[k(x, y)] = (x + y) % 3 ? "dirt" : "grass"; delete fl.things[k(x, y)]; }
      fl.things[k(...CM.GLYPH_AT)] = { type: "glyphcab" }; fl.things[k(...CM.GLYPH_PORTAL)] = { type: "portal", to: "town" }; fl.decor = (fl.decor || []).filter((d) => !(d.x >= x0 && d.x <= x1 && d.y >= y0 && d.y <= y1));
      fl.rooms = (fl.rooms || []).concat({ x0, y0, x1, y1, name: "the arcade cabinet" }); return fl; }; }
  const G = CM.Game.prototype;
  Object.assign(G, {
    glyphStore() { this.village = this.village || {}; const S = this.village.glyph = this.village.glyph || {}; S.best = S.best || 0; S.paid = S.paid || {}; S.runs = S.runs || 0; S.deaths = S.deaths || 0; return S; },
    glyphChoices() { return this.party.map((h, i) => ({ i, name: h.name, cls: h.cls, level: h.level, why: h.hp <= 0 ? `${h.name} has fallen.` : "" })); },
    glyphLevels() { return Math.min(GD.levels, this.glyphStore().best + 1); },
    atGlyphCab() { const fl = this.floor; return Boolean(fl && fl.number === -1 && fl.pos[0] === CM.GLYPH_AT[0] && fl.pos[1] === CM.GLYPH_AT[1]); },
    enterGlyph(i, level = 1) { const h = this.party[i]; if (!h || h.hp <= 0) return h ? `${h.name} has fallen.` : "No one."; if (this.mode !== "explore" || !this.atGlyphCab()) return "The cabinet is in the Wood, by the road.";
      level = Math.max(1, Math.min(this.glyphLevels(), level | 0)); this.logAct && this.logAct("enterGlyph", i, level); const S = this.glyphStore(); S.runs++;
      this.glyphRun = new CM.GlyphRun(this, i, level); S.best = Math.max(S.best, level); this.say(`${h.name} drops a coin in the slot. The screen goes black, and then: THE GLYPH DEEP - level ${level}.`);
      this.setMode("glyph"); this.emit("glyph", this.glyphRun); this.saveVillage && this.saveVillage(); return ""; },
    glyphAct(cmd, arg) { const r = this.glyphRun; if (!r || this.mode !== "glyph") return []; this.logAct && this.logAct("glyphAct", cmd, arg === undefined ? null : arg); const msgs = r.act(cmd, arg);
      if (r.over === "dead") this.leaveGlyph("dead"); this.emit("change"); return msgs; },
    // the stairs: the level's reward the first time, then down or home
    glyphStairs(down = true) { const r = this.glyphRun; if (!r || !r.atDown()) return "The stairs down are somewhere else on this level."; if (r.L === GD.levels && !r.bossDown()) return "The way down is sealed while the Unwritten stands.";
      this.logAct && this.logAct("glyphStairs", Boolean(down)); this.glyphPay(r.L); const S = this.glyphStore();
      if (r.L >= GD.levels) { if (!S.boss) this.glyphPrize(); S.boss = true; return this.leaveGlyph("won"); }
      if (!down) return this.leaveGlyph("out");
      for (const it of r.pack) it.gsecure = true; const next = new CM.GlyphRun(this, r.heroIndex, r.L + 1, { pack: r.pack, gold: r.gold, levelGold: 0, xp: r.xp, kills: r.kills, wield: r.wield, wear: r.wear });
      next.hp = r.hp; this.glyphRun = next; S.best = Math.max(S.best, next.L); this.saveVillage && this.saveVillage(); this.emit("glyph", next); this.emit("change"); return ""; },
    glyphUp() { const r = this.glyphRun; if (!r || !r.atUp()) return "The stairs up are where you came in."; this.logAct && this.logAct("glyphUp"); return this.leaveGlyph("fled"); },
    // the first time a level's stairs are reached: tickets, gold and a thing, to the party at once
    glyphPay(L) { const S = this.glyphStore(); if (S.paid[L]) return null; S.paid[L] = true; const P = GD.reward(L), R = new CM.Random(CM.hashSeed(`${this.seed}:glyphpay:${L}`)), d = GD.depthOf(L) + 2;
      let it = CM.makeItem(d, R, R.pick(["weapon", "armor", "shield", "helm", "ring", "amulet"])); if (it && CM.affix && L % 5 === 0) it = CM.affix(it, d + 4, R); if (it) it.unknown = false;
      const things = [it].filter(Boolean); if (L === 15 && CM.FIELDSEEDS) things.push(CM.seed(R.pick(Object.keys(CM.FIELDSEEDS.CHARMED))));
      this.gold += P.gold; if (this.tkAdd) this.tkAdd(P.tickets, "glyph"); if (things.length) this.gain(things, "glyph"); if (L === 10 && this.cgCard) this.cgCard(true, "Won in the Glyph Deep (level 10).", R);
      this.say(`Level ${L} cleared for the first time: ${P.tickets} tickets, ${P.gold} gold${things.length ? ` and ${things.map((t) => t.name).join(", ")}` : ""}${L === 10 ? ", and a rare card" : ""} - sent to the party.`); this.saveVillage && this.saveVillage(); return P; },
    // the deep's great prize, once
    glyphPrize() { const P = GD.PRIZE, R = new CM.Random(CM.hashSeed(`${this.seed}:glyphprize`)), things = [];
      for (let k = 0; k < P.items; k++) { let it = CM.makeItem(48, R, ["weapon", "armor", "amulet"][k]); if (it && CM.affix) it = CM.affix(CM.affix(it, 52, R), 54, R); if (it) { it.unknown = false; things.push(it); } }
      if (CM.FIELDSEEDS) for (let k = 0; k < P.seeds; k++) things.push(CM.seed(R.pick(Object.keys(CM.FIELDSEEDS.CHARMED))));
      this.gold += P.gold; if (this.tkAdd) this.tkAdd(P.tickets, "glyph"); this.gain(things, "glyph"); if (this.cgCard) for (let k = 0; k < P.cards; k++) this.cgCard(true, "The Glyph Deep's great prize.", R);
      this.achieve && this.achieve("unwritten"); this.say(`THE GLYPH DEEP - YOU WIN. The cabinet rattles and pays out: ${P.tickets} tickets, ${P.gold} gold, ${things.filter((t) => t.kind !== "seed").map((t) => t.name).join(", ")}, ${P.seeds} charmed seeds and ${P.cards} rare cards.`); },
    // home from the cabinet: "out"/"won" with everything, "fled" or "dead" without this level's finds
    leaveGlyph(how) { const r = this.glyphRun; if (!r) return null; const h = r.hero, S = this.glyphStore(), xp = Math.round(r.xp * GD.xpShare); if (xp) { h.xp += xp; this.checkLevels && this.checkLevels(); }
      let keep = r.pack, gold = r.gold; if (how === "dead" || how === "fled") { keep = r.pack.filter((it) => it.gsecure); gold = r.gold - r.levelGold; }
      const bank = [], words = []; let tickets = 0, cards = 0, scrolls = 0;
      for (const it of keep) { if (it.kind === "gtickets") tickets += it.n; else if (it.kind === "gcard") { cards++; if (this.cgCard) this.cgCard(Boolean(it.rare), "Found in the Glyph Deep.", r.rnd); } else if (it.kind === "gscroll") scrolls += it.value || 15; else { delete it.gfound; delete it.gsecure; bank.push(it); } }
      this.gold += gold + scrolls; if (tickets && this.tkAdd) this.tkAdd(tickets, "glyph"); if (bank.length) this.gain(bank, "glyph");
      if (how === "dead") { h.hp = Math.max(1, Math.round(h.max * 0.1)); S.deaths++; } else h.hp = Math.max(1, Math.min(h.max, r.hp));
      this.say(how === "dead" ? `${h.name} slumps back from the cabinet, shaking. GAME OVER on level ${r.L}; what that level gave is gone.` : how === "fled" ? `${h.name} climbs back up the stairs and steps away from the cabinet, without what level ${r.L} gave.` : how === "won" ? `${h.name} steps back from the cabinet a hero of the Glyph Deep.` : `${h.name} steps away from the cabinet at the stairs of level ${r.L}, carrying everything.`);
      if (xp) words.push(`${xp} experience`); if (gold + scrolls) words.push(`${gold + scrolls} gold`); if (tickets) words.push(`${tickets} tickets`); if (cards) words.push(`${cards} card${cards > 1 ? "s" : ""}`); if (bank.length) words.push(bank.map((t) => t.name).join(", "));
      if (words.length) this.say(`From the Glyph Deep: ${words.join("; ")}.`);
      this.glyphRun = null; this.setMode("explore"); if (this.floor && this.floor.number === -1) { this.floor.pos = CM.GLYPH_AT.slice(); }
      this.saveVillage && this.saveVillage(); this.saveRun && this.saveRun(); this.emit("change");
      this.emit && this.emit("glyphend", { how, name: h.name, cls: h.cls, level: r.L, turns: r.turn, kills: r.kills, words, cause: how === "dead" ? (r.killer || "something in the dark") : null });
      return ""; },
  });
  CM.ACHIEVEMENTS.unwritten = { name: "Unwritten", what: "Beat the Unwritten on the twentieth level of the Glyph Deep", title: "of the Glyph Deep" };
  // the portals: the yard's to the cabinet, the clearing's home to the yard
  { const ly0 = CM.layPortalYard; CM.layPortalYard = function (fl) { const out = ly0.call(this, fl), P = CM.PORTAL_YARD.glyph, k = `${P[0]},${P[1]}`; if (!fl.things[k] || fl.things[k].to !== "glyph") fl.things[k] = { type: "portal", to: "glyph" }; return out; }; }
  { const up0 = G.usePortal; G.usePortal = function (t) {
      if (t && t.to === "glyph") { this.sound && this.sound("spell"); this.enterFloor(-1, "rope", [CM.GLYPH_AT[0], CM.GLYPH_AT[1] + 1]); this.floor.facing = 0; this.say("The green portal sets you down in a little clearing by the road. An arcade cabinet hums under its roof of planks, letters crawling on its screen."); return true; }
      const fl = this.floor; if (t && t.to === "town" && fl && fl.number === -1 && Math.abs(fl.pos[0] - CM.GLYPH_PORTAL[0]) + Math.abs(fl.pos[1] - CM.GLYPH_PORTAL[1]) <= 1) { this.sound && this.sound("spell"); this.enterFloor(0, "rope", CM.PORTAL_YARD.glyph.slice()); this.say("Green light, and the Keep-yard: the portal yard by the shaft."); return true; }
      return up0.call(this, t); }; }
  // Space at the cabinet
  { const use0 = G.use; G.use = function (...a) { const fl = this.floor, t = fl && this.mode === "explore" && fl.things[`${fl.pos[0]},${fl.pos[1]}`];
      if (t && t.type === "glyphcab") { this.logAct && this.logAct("use"); this.say("An arcade cabinet stands under a little roof of planks, humming. Green letters crawl across its screen: THE GLYPH DEEP - INSERT COIN."); this.emit("glyphcab"); return; }
      return use0.apply(this, a); }; }
  // on the map, on the goals page, toward the renown level
  if (CM.WORLDMAP) { CM.WORLDMAP.PLACES.push(["glyph", "The Glyph Deep (an arcade cabinet)", -1, () => CM.GLYPH_AT, "a roguelike in letters, twenty levels", true]); CM.WORLDMAP.byId.glyph = CM.WORLDMAP.PLACES[CM.WORLDMAP.PLACES.length - 1]; }
  { const goals0 = G.wmGoals; if (goals0) G.wmGoals = function () { const out = goals0.call(this), S = this.glyphStore(); out.push({ area: "The Glyph Deep", text: S.boss ? "The Unwritten is beaten. The cabinet still plays, for the love of it." : S.best ? `Deepest so far: level ${S.best} of ${GD.levels}. The next level's stairs pay ${GD.reward(Math.min(GD.levels, S.best)).tickets} tickets the first time.` : "An arcade cabinet by the Wood's road: twenty levels of letters.", go: "glyph" }); return out; }; }
  if (CM.RENOWNLV) CM.RENOWNLV.AREAS.push(["glyph", "The Glyph Deep", "4 a level's stairs, 100 for the Unwritten", (g) => { const S = (g.village || {}).glyph || {}; return 4 * Object.keys(S.paid || {}).length + (S.boss ? 100 : 0); }]);
}
