"use strict";
// The tree goes with them (v18.6): what a hero has learned - and the weak spots, mending and spoils their gear gives -
// now counts when they go somewhere alone, so the hero in the Fortress or the Tower is the same hero.
// - The Mage Tower, the Fortress and the island: weak spots (critical blows, double), health and mana from each kill,
//   more gold and experience from each kill. (Attack, defence and health already came through the rules' own sums.)
// - Claudeita's cave: the casting stat is the hero's whole stat (the tree's included), and weak spots raise the wands.
// - Claudeablo: the tree's stats become Haven's (Strength and attack to Strength, Dexterity to Dexterity, Intelligence
//   and Wisdom to Magic, Constitution to Vitality), its health to Life, its mana to Mana, its aim to To Hit.
// - The pipe: the tree's defence takes the sting out of a knock, 4% a point (to half at most).
// The tree's window says so (76zzzd-skilltree.js reads CM.SOLOEDGE.lines).
{ const SE = CM.SOLOEDGE = { critMult: 2, brosPerDf: 0.04, brosFloor: 0.5 };
  SE.of = (h) => { const p = (k) => (CM.gearProp ? CM.gearProp(h, k) : 0) || 0; return { crit: p("crit"), killHeal: p("killHeal"), killMana: p("killMana"), killGold: p("killGold"), xpBonus: p("xpBonus"), hit: p("hitBonus") }; };
  SE.tree = (h) => (CM.SKILLTREE && CM.SKILLTREE.sum(h)) || { stat: {}, prop: {}, atk: 0, df: 0, hp: 0, mp: 0, traits: [] };
  // Haven's stats from the tree
  SE.ablo = (h) => { const S = SE.tree(h), st = S.stat || {}; return { str: (st.str || 0) + (S.atk || 0), dex: st.dex || 0, mag: (st.int || 0) + (st.wis || 0), vit: st.con || 0, life: S.hp || 0, mana: S.mp || 0, to_hit: Math.round(((S.prop || {}).hitBonus || 0) * 100) }; };
  SE.brosShield = (h) => Math.max(SE.brosFloor, 1 - SE.brosPerDf * (SE.tree(h).df || 0));
  // what it comes to for one hero, in words (for the tree's window)
  SE.lines = (h) => { const E = SE.of(h), A = SE.ablo(h), out = [], pc = (x) => `${Math.round(x * 100)}%`;
    if (E.crit) out.push(`Weak spots ${pc(E.crit)} in the Tower, the Fortress and on the island; the cave's wands ${pc(E.crit)} stronger`);
    if (E.killHeal || E.killMana) out.push(`From each kill alone: ${[E.killHeal ? `${E.killHeal} health` : "", E.killMana ? `${E.killMana} mana` : ""].filter(Boolean).join(" and ")}`);
    if (E.killGold || E.xpBonus) out.push(`Kills alone pay ${[E.killGold ? `${pc(E.killGold)} more gold` : "", E.xpBonus ? `${pc(E.xpBonus)} more experience` : ""].filter(Boolean).join(" and ")}`);
    const ab = [["str", "Strength"], ["dex", "Dexterity"], ["mag", "Magic"], ["vit", "Vitality"], ["life", "Life"], ["mana", "Mana"], ["to_hit", "To Hit"]].filter(([k]) => A[k]).map(([k, n]) => `+${A[k]} ${n}`);
    if (ab.length) out.push(`In Haven: ${ab.join(", ")}`); const sh = SE.brosShield(h); if (sh < 1) out.push(`Down the pipe: knocks hurt ${pc(1 - sh)} less`); return out; };
  const edgeRnd = (run, tag) => run.edgeRnd || (run.edgeRnd = new CM.Random(CM.hashSeed(`${run.game ? run.game.seed : ""}:edge:${tag}:${run.n || 0}`)));
  // a kill's spoils, for the runs that keep xp and gold on themselves
  const spoils = (run, h, o, goldShare) => { const E = SE.of(h); if (E.killHeal) h.hp = Math.min(h.max, h.hp + E.killHeal); if (E.killMana && h.maxmp) h.mp = Math.min(h.maxmp, h.mp + E.killMana);
    if (E.xpBonus) run.xp += Math.round((o.m.xp || 0) * E.xpBonus); if (E.killGold) { const more = Math.round((o.m.gold || 0) * goldShare * E.killGold); run.gold += more; if ("floorGold" in run) run.floorGold += more; } };
  // the Mage Tower
  { const T = CM.TowerRun.prototype, strike0 = T.strike, fall0 = T.fall;
    T.strike = function (o, b) { const c = SE.of(this.hero).crit; if (c > 0 && edgeRnd(this, "tower").chance(c)) { b = Object.assign({}, b, { mult: (b.mult || 1) * SE.critMult }); this.events.push({ kind: "crit", at: [o.x, 0.9, o.z] }); } return strike0.call(this, o, b); };
    T.fall = function (o) { const out = fall0.call(this, o); spoils(this, this.hero, o, 1); return out; }; }
  // the Fortress
  { const F = CM.FortRun.prototype, crit0 = F.critMult, fall0 = F.fall;
    F.critMult = function () { const m = crit0.call(this); if (m > 1) return m; const c = SE.of(this.hero).crit; return c > 0 && edgeRnd(this, "fort").chance(c) ? SE.critMult : 1; };
    F.fall = function (o) { const out = fall0.call(this, o); spoils(this, this.hero, o, 0.5); return out; }; }
  // the island
  { const G = CM.Game.prototype, crit0 = G.craftCritMult, fell0 = G.craftFell;
    G.craftCritMult = function () { const m = crit0.call(this); if (m > 1) return m; const c = SE.of(this.craft.hero).crit; return c > 0 && this.craftLife().rnd.chance(c) ? SE.critMult : 1; };
    G.craftFell = function (o) { const out = fell0.call(this, o), h = this.craft && this.craft.hero, L = this.craftLife(); if (!h) return out; const E = SE.of(h);
      if (E.killHeal) h.hp = Math.min(h.max, h.hp + E.killHeal); if (E.killMana && h.maxmp) h.mp = Math.min(h.maxmp, h.mp + E.killMana);
      if (E.xpBonus) { const xp = Math.round((o.m.xp || 0) * CM.CL.xpShare * E.xpBonus); if (xp) { h.xp += xp; L.xp += xp; this.checkLevels && this.checkLevels(); } }
      if (E.killGold && CM.CL.GOLD.includes(o.kind)) L.gold += Math.round((o.m.gold || 0) * CM.CL.goldShare * E.killGold); return out; }; }
  // Claudeablo: the tree's stats ride on Haven's own affix sums, set on the way in and gone on the way out (never saved)
  { const AP = CM.AB.Player.prototype, affix0 = AP.affix; AP.affix = function (name) { return affix0.call(this, name) + ((this.edge && this.edge[name]) || 0); };
    const G = CM.Game.prototype, enter0 = G.enterClaudeablo, leave0 = G.leaveClaudeablo;
    G.enterClaudeablo = function (i) { const why = enter0.call(this, i); if (why) return why; const w = this.abloWorld, pl = w && w.player; if (pl) { const ratio = pl.maxhp ? pl.hp / pl.maxhp : 1; pl.edge = SE.ablo(this.party[i]); pl.recalc(); pl.hp = Math.max(1, Math.round(pl.maxhp * ratio)); } return why; };
    G.leaveClaudeablo = function (...a) { const pl = this.abloWorld && this.abloWorld.player; if (pl && pl.edge) { pl.edge = null; pl.recalc(); pl.hp = Math.min(pl.hp, pl.maxhp); pl.mana = Math.min(pl.mana, pl.maxmana); } return leave0.apply(this, a); }; }
  // the pipe
  { const B = CM.BrosRun.prototype, hurt0 = B.hurt; B.hurt = function (frac, ...a) { return hurt0.call(this, frac * SE.brosShield(this.hero), ...a); }; }
}
