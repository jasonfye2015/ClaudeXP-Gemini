"use strict";
// Bonds and rivals (v34.1, UPGRADE_PLAN_29.md): old friends (CM.BOND_FIGHTS fights together, 62-combat.js) now cover
// each other - a blow meant for a friend at under a third of their health is, two times in five, taken by the other
// (on their feet and able to act) instead. And rivals: who lands the killing blow is counted for every hero; two who
// have fought twenty-five fights together, each with fifteen kills or more and their counts within a sixth of each
// other, become rivals (a hero has one rival, and no rival who is a friend) - each strikes a weak spot a twentieth
// more often while the other stands, and they keep score out loud at the fire (69zh-fireside.js).
//   game.rivals -> [[a, b]];  game.heroKills -> {name: n};  game.rivalOf(h)
{ CM.RIVAL = { fights: 25, kills: 15, close: 1 / 6, crit: 0.05 }; CM.COVER = { below: 1 / 3, chance: 0.4 };
  const G = CM.Game.prototype, R = CM.RIVAL;
  Object.defineProperty(G, "rivals", { configurable: true, get() { return this.tally ? (this.ext("rival").list = this.ext("rival").list || []) : []; } });
  Object.defineProperty(G, "heroKills", { configurable: true, get() { return this.tally ? (this.ext("rival").kills = this.ext("rival").kills || {}) : {}; } });
  G.rivalOf = function (h) { for (const [a, b] of this.rivals) { if (a === h.name) return this.party.find((p) => p.name === b) || null; if (b === h.name) return this.party.find((p) => p.name === a) || null; } return null; };
  const st0 = G.strike; G.strike = function (hero, target, ...a) { const was = target && target.hp > 0, out = st0.call(this, hero, target, ...a);
    if (was && target && target.hp <= 0 && hero && hero.name && !target.creditedTo) { target.creditedTo = hero.name; this.heroKills[hero.name] = (this.heroKills[hero.name] || 0) + 1; } return out; };
  const ft0 = G.foughtTogether; G.foughtTogether = function (...a) { const out = ft0.apply(this, a), up = this.alive(), K = this.heroKills;
    for (let i = 0; i < up.length; i++) for (let j = i + 1; j < up.length; j++) { const A = up[i], B = up[j], k = [A.name, B.name].sort().join("|");
      if ((this.pairFights || {})[k] < R.fights || this.rivalOf(A) || this.rivalOf(B) || (this.bondOf && this.bondOf(A) === B)) continue;
      const ka = K[A.name] || 0, kb = K[B.name] || 0; if (ka < R.kills || kb < R.kills || Math.abs(ka - kb) > Math.max(ka, kb) * R.close) continue;
      this.rivals.push(k.split("|")); this.say(`${A.name} and ${B.name} have been keeping score - ${ka} to ${kb}. Rivals now: each strikes truer with the other watching.`); this.sound && this.sound("level"); if (this.achieve) this.achieve("rivalry"); }
    return out; };
  CM.ACHIEVEMENTS.rivalry = { name: "Keeping Score", what: "Have two heroes become rivals", title: "the Competitive" };
  const cc0 = G.critChance; G.critChance = function (h) { const r = this.rivalOf ? this.rivalOf(h) : null; return Math.min(0.7, cc0.call(this, h) + (r && r.hp > 0 ? R.crit : 0)); };
  const pt0 = G.pickTarget; G.pickTarget = function (m) { const t = pt0.call(this, m); if (!t || !this.bondOf || t.thrall) return t; const f = this.bondOf(t);
    if (f && f !== t && f.hp > 0 && t.hp / Math.max(1, t.max) < CM.COVER.below && this.canAct(f) && this.rnd.chance(CM.COVER.chance)) { this.say(`${f.name} steps in front of ${t.name} and takes it instead.`); this.tally.covers = (this.tally.covers || 0) + 1; return f; }
    return t; };
}
