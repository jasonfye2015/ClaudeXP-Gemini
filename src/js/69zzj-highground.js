"use strict";
// High ground (v47.4, UPGRADE_PLAN_42.md): in a fight where the party stands higher than its foes by a step or more
// (a dais, a gallery, a stair, the raised room - 69zzi-levels.js), its blows land more often (a tenth more) and the
// foes' less; standing lower, the other way about; and a Ranger shooting down from above has a little more still. The
// fight's first line says who holds it. By the floor's levels alone, so a film plays back the same.
//   CM.HIGH_GROUND = { hit, ranger, step }; Game.highGround() -> 1 (the party above), -1 (below), 0
{ CM.HIGH_GROUND = { hit: 0.1, ranger: 0.05, step: 0.15 };
  const G = CM.Game.prototype;
  G.highGround = function () { const fl = this.floor; if (!fl || !fl.levels || !this.foeKey || !CM.floorAt) return 0; const [fx, fy] = String(this.foeKey).split(",").map(Number); if (!(fx >= 0)) return 0;
    const d = CM.floorAt(fl, fl.pos[0], fl.pos[1]) - CM.floorAt(fl, fx, fy); return d >= CM.HIGH_GROUND.step - 1e-9 ? 1 : d <= -CM.HIGH_GROUND.step + 1e-9 ? -1 : 0; };
  const hit0 = G.hitChance; G.hitChance = function (h) { const base = hit0.call(this, h); if (this.mode !== "combat") return base; const e = this.highGround(); if (!e) return base;
    return CM.clamp(base + e * CM.HIGH_GROUND.hit + (e > 0 && h && h.cls === "Ranger" ? CM.HIGH_GROUND.ranger : 0), 0.05, 0.98); };
  const dodge0 = G.dodgeOf; G.dodgeOf = function (h) { const base = dodge0.call(this, h); if (this.mode !== "combat") return base; const e = this.highGround(); return e ? base * (1 - e * CM.HIGH_GROUND.hit) : base; };
  const sc0 = G.startCombat; G.startCombat = function (...a) { const out = sc0.apply(this, a); if (this.mode === "combat") { const e = this.highGround(); if (e > 0) this.say("You hold the high ground: your blows come down on them."); else if (e < 0) this.say("They have the high ground, and the party fights uphill."); } return out; };
}
