"use strict";
// One name across the world (v18.7): the renown level. Renown was the village's money, earned by the dungeon's runs; now
// every part of the world adds to it - the Mage Tower's floors, the Fortress's, Claudeita's cave, Leshy's tables,
// Haven's depths, the pipe, the island and the Joker (its standing is one strand of this) - and all the renown ever
// earned makes one level, 1 to 30, whose perks reach everywhere: the fights, the solo runs, Haven, the pipe, the Joker.
// What an area adds is counted from its best ever, so nothing is paid twice. (Spending renown on the village never
// lowers the level: it counts what was earned.) The window's side is 76zzzh-renownlv.js.
{ const RL = CM.RENOWNLV = { max: 30, cur: 0 };
  RL.need = (n) => 15 * n * (n - 1);                       // renown earned for level n (2 at 30, 10 at 1,350, 20 at 5,700, 30 at 13,050)
  RL.levelOf = (earned) => { let n = 1; while (n < RL.max && earned >= RL.need(n + 1)) n++; return n; };
  // what each area has done, in renown
  RL.AREAS = [
    ["tower", "The Mage Tower", "3 a floor cleared", (g) => 3 * ((g.tower && g.tower.cleared) || 0)],
    ["fortress", "The Fortress", "5 a floor cleared", (g) => 5 * ((g.fort && g.fort.cleared) || 0)],
    ["cave", "Claudeita's cave", "2 a depth, 15 a boss, 25 a win", (g) => { const K = (g.village || {}).cave || {}; return 2 * (K.deepest || 0) + 15 * (K.bosses || 0) + 25 * (K.wins || 0); }],
    ["cabin", "Leshy's table", "12 a game won", (g) => 12 * Object.keys(((g.village || {}).cards || {}).beaten || {}).length],
    ["haven", "Haven", "3 a level reached", (g) => 3 * Math.max(0, ...Object.values(((g.village || {}).ablo || {}).heroes || {}).map((p) => p.maxDepth || 0))],
    ["pipe", "The pipe", "10 a level", (g) => 10 * ((g.tally && g.tally.brosBest) || 0)],
    ["island", "The island", "2 a visit, to 40", (g) => 2 * Math.min(20, (((g.village || {}).craft || {}).visits) || 0)],
    ["joker", "The Joker", "3 a Joker level", (g) => { try { return g.jkInfo ? 3 * Math.max(0, g.jkInfo().level - 1) : 0; } catch (e) { return 0; } }],
  ];
  // the perks: [level, words, kind, amount]
  RL.PERKS = [
    [2, "+3% experience from fights, everywhere", "xpBonus", 0.03], [4, "+15 Life in Haven", "havenLife", 15], [6, "+1 Luck to every hero", "stat", { luck: 1 }],
    [8, "+10% prize tickets at the Joker", "tickets", 0.1], [10, "+3% weak spots, everywhere (alone too)", "crit", 0.03], [12, "Knocks down the pipe hurt 10% less", "pipe", 0.9],
    [14, "+1 health from each kill", "killHeal", 1], [16, "+1 to every stat", "stat", { str: 1, dex: 1, con: 1, int: 1, wis: 1, luck: 1 }], [18, "+2% gold from kills for each hero", "killGold", 0.02],
    [20, "+1 attack and +1 defence", "arms", 1], [25, "+5% experience from fights", "xpBonus", 0.05], [30, "+1 to every stat, and the name's known in every hall", "stat", { str: 1, dex: 1, con: 1, int: 1, wis: 1, luck: 1 }],
  ];
  RL.perks = (lvl) => RL.PERKS.filter((p) => p[0] <= lvl);
  RL.sumOf = (lvl, kind) => RL.perks(lvl).filter((p) => p[2] === kind).reduce((n, p) => n + p[3], 0);
  RL.statOf = (lvl, s) => RL.perks(lvl).filter((p) => p[2] === "stat").reduce((n, p) => n + (p[3][s] || 0), 0);
  const lvlOf = (g) => { const L = RL.levelOf(((g && g.village) || {}).renown || 0); RL.cur = L; return L; };
  // ---- into the reckonings: the game's own (with the level fresh from the village), and the hero-only ones (from the last seen) ----
  const G = CM.Game.prototype, stat0 = G.stat, eff0 = G.effective;
  G.stat = function (h, s) { return stat0.call(this, h, s) + RL.statOf(lvlOf(this), s); };
  G.effective = function (h) { const e = eff0.call(this, h), a = RL.sumOf(lvlOf(this), "arms"); if (a) { e.atk += a; e.df += a; } return e; };
  { const gp0 = CM.gearProp; CM.gearProp = (h, prop) => { const v = gp0(h, prop); if (!RL.cur) return v; const k = { xpBonus: "xpBonus", crit: "crit", killHeal: "killHeal", killGold: "killGold" }[prop]; return k ? v + RL.sumOf(RL.cur, k) : v; }; }
  { const SE = CM.SOLOEDGE; if (SE) { const ab0 = SE.ablo, bs0 = SE.brosShield; SE.ablo = (h) => { const A = ab0(h), n = RL.sumOf(RL.cur, "havenLife"); if (n) A.life = (A.life || 0) + n; return A; };
    SE.brosShield = (h) => { const p = RL.perks(RL.cur).filter((x) => x[2] === "pipe"); return Math.max(SE.brosFloor * 0.9, bs0(h) * p.reduce((m, x) => m * x[3], 1)); }; } }
  { const tk0 = G.tkAdd; if (tk0) G.tkAdd = function (n, why) { const k = tk0.call(this, n, why), b = RL.sumOf(lvlOf(this), "tickets"); if (k > 0 && b && !this.cgPractice && why !== "renown") { const T = this.tkStore(); T.rlFrac = (T.rlFrac || 0) + k * b; const x = Math.floor(T.rlFrac); T.rlFrac -= x; if (x) tk0.call(this, x, "renown"); } return k; }; }
  // ---- the deeds counted in, and the level announced ----
  const save0 = G.saveVillage; const enter0 = G.enterFloor;
  Object.assign(G, {
    rlStore() { this.village = this.village || {}; const R = this.village.rl = this.village.rl || {}; R.cred = R.cred || {}; R.seen = R.seen || 0; return R; },
    rlDeeds() { const out = {}; for (const [id, , , f] of RL.AREAS) { let v = 0; try { v = Math.max(0, Math.floor(f(this) || 0)); } catch (e) { v = 0; } out[id] = v; } return out; },
    // what's new since last counted goes into renown; returns the renown added
    rlSync() { if (this.rlSyncing) return 0; this.rlSyncing = true; try { const R = this.rlStore(), D = this.rlDeeds(); let add = 0;
        for (const [id, v] of Object.entries(D)) { const c = R.cred[id] || 0; if (v > c) { add += v - c; R.cred[id] = v; } }
        if (add) this.village.renown = (this.village.renown || 0) + add; const L = lvlOf(this);
        const seen0 = R.seen; if (!R.seen) R.seen = L; else if (L > R.seen) { const P = RL.PERKS.filter((p) => p[0] > R.seen && p[0] <= L); this.say(`Renown level ${L}! Your name is known further.${P.length ? ` ${P.map((p) => p[1]).join("; ")}.` : ""}`); this.emit && this.emit("renownlevel", L); R.seen = L; }
        if (add || R.seen !== seen0) save0.call(this); return add; } finally { this.rlSyncing = false; } },
    enterFloor(...a) { const out = enter0.apply(this, a); if (this.village && !this.replaying) this.rlSync(); return out; },
    saveVillage() { const out = save0.call(this); if (!this.rlSyncing) this.rlSync(); return out; },
    rlInfo() { const v = this.village || {}, earned = v.renown || 0, L = lvlOf(this), next = L < RL.max ? RL.need(L + 1) : null, from = RL.need(L), R = this.rlStore();
      return { level: L, earned, next, from, toNext: next === null ? 0 : next - earned, areas: RL.AREAS.map(([id, name, how]) => ({ id, name, how, renown: R.cred[id] || 0 })), perks: RL.PERKS.map(([n, w]) => ({ level: n, words: w, have: n <= L })) }; },
  });
  // the goals page knows it
  { const goals0 = G.wmGoals; if (goals0) G.wmGoals = function () { const out = goals0.call(this), I = this.rlInfo(), P = RL.PERKS.find((p) => p[0] > I.level);
    out.unshift({ area: "Renown", text: I.next === null ? `Renown level ${I.level}, the highest.` : `Renown level ${I.level}: ${I.toNext} more renown to level ${I.level + 1}${P ? ` (at ${P[0]}: ${P[1]})` : ""}. Every part of the world adds to it.`, go: "guildhall" }); return out; }; }
}
