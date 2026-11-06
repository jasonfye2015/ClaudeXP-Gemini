"use strict";
// Steam, the dry roots and the fog pools (UPGRADE_PLAN_63.md sets 1.3 and 3.2, release 5). Steam: in the fire bands
// (the Foundry, the Root of the World) when water meets the heat - floodwater underfoot, or rain above dripping on
// the first floors - under a cold sky (winter, or snow falling), the square is a steam screen: the fight's terrain
// carries "steam", a bow lands at three quarters (the foes' archers too, by the party's dodge), and the sight is a
// square. The dry roots: in a heat event above, the roots of the Root of the World are dry (CM.rootsDry): a fire
// spell in a fight there bites a quarter harder and sets the hall's roots alight for the fight's length - a sight,
// never a harm to the party (the standing rule). The fog pools: a magical fog lies thick in a sunken room (its
// strength 1, the sight a square, said when entered) and thin in a raised one (half).
//   CM.steamHere(game) -> boolean;  CM.rootsDry(game) -> boolean;  CM.rootsBurning(game, fl) -> minutes left | 0
{ const skyOn = (game) => Boolean(game && game.tally && game.tally.ext && game.tally.ext.wx && game.tally.ext.wx.cur);   // (the sky is read only once the clock has made it: a fight's rules must not roll the weather's dice, or a run and its replay part)
  const S = CM.STEAM = { hot: ["The Foundry", "The Root of the World"], bowHit: 0.75, dodgeK: 0.75, rootsBite: 1.25, rootsBurnMinutes: 15, poolDeep: 1, poolHigh: 0.5 };
  const hot = (fl) => Boolean(fl && S.hot.includes((CM.themeFor(fl.number) || {}).name));
  const coldSky = (game) => { const season = CM.season ? CM.season(game) : "summer", W = CM.aboveNow ? CM.aboveNow(game) : { kind: "clear" }; return season === "winter" || W.kind === "snow"; };
  CM.steamHere = (game) => { const fl = game && game.floor; if (!fl || !(fl.number >= 1) || !hot(fl) || !game.ext || !skyOn(game)) return false; const W = CM.aboveNow(game), rainy = (W.kind === "rain" || W.kind === "storm") && fl.number <= 3; const wet = (CM.floodedHere && CM.floodedHere(game)) || rainy; return Boolean(wet && coldSky(game)); };
  const P = CM.Game.prototype;
  { const t0 = P.terrain; P.terrain = function () { const out = t0.call(this); if (CM.steamHere(this) && !out.includes("steam")) out.push("steam"); return out; }; }
  { const hc0 = P.hitChance; P.hitChance = function (h, ...rest) { const c = hc0.call(this, h, ...rest); return h && h.weapon && h.weapon.props && h.weapon.props.bow && CM.steamHere(this) ? Math.max(0.05, c * S.bowHit) : c; }; }
  { const d0 = P.dodgeOf; if (d0) P.dodgeOf = function (...a) { const d = d0.apply(this, a); return CM.steamHere(this) && this.combat && this.combat.shooter ? d * S.dodgeK : d; }; }   // (the foes' archers: the fight marks who shoots - 62-combat sets combat.shooter for a ranged blow where it can; else the party's own quarter is the rule)
  { const m0 = CM.mistSightNow; CM.mistSightNow = (game) => { const v = m0 ? m0(game) : null; if (CM.steamHere(game)) return 1; const Fg = CM.fogNow && game && game.floor && game.floor.pos ? CM.fogNow(game) : null; if (Fg && CM.floorAt(game.floor, game.floor.pos[0], game.floor.pos[1]) < 0) return 1; return v; }; }
  // the dry roots, and the fire that takes them
  CM.rootsDry = (game) => { const fl = game && game.floor; if (!fl || !game.ext || !skyOn(game) || (CM.themeFor(fl.number) || {}).name !== "The Root of the World") return false; const W = CM.aboveNow(game); return W.kind === "heat" && W.strength > 0.2; };
  CM.rootsBurning = (game, fl) => { if (!game || !game.ext || !fl) return 0; const E = game.ext("roots"), until = E[fl.number]; return until ? Math.max(0, until - CM.clockOf(game)) : 0; };
  { const sh0 = P.spellHit; P.spellHit = function (foe, dmg, what, element, chained, ...rest) { if (element === "fire" && !chained && CM.rootsDry(this)) { dmg = Math.max(1, Math.ceil(dmg * S.rootsBite)); if (what) what += " - the dry roots catch"; const E = this.ext("roots"), fl = this.floor; if (!E[fl.number] || E[fl.number] < CM.clockOf(this)) { E[fl.number] = CM.clockOf(this) + S.rootsBurnMinutes; this.say("The roots along the walls are tinder-dry in the heat from above: they take the fire with a roar, and the hall burns about the fight. (The flames keep to the roots.)"); this.emit("rootsfire", { floor: fl.number }); } else E[fl.number] = CM.clockOf(this) + S.rootsBurnMinutes; }
      return sh0.call(this, foe, dmg, what, element, chained, ...rest); }; }
  // the fog pools: thick in a sunken room, thin in a raised one
  { const f0 = CM.fogNow; if (f0) CM.fogNow = (game) => { if (!skyOn(game)) return null; const F = f0(game); if (!F || !game.floor || !game.floor.pos || !(game.floor.number >= 1)) return F; const lv = CM.floorAt(game.floor, game.floor.pos[0], game.floor.pos[1]); if (lv < 0) return Object.assign({}, F, { strength: Math.max(F.strength, S.poolDeep), pool: "deep" }); if (lv > 0) return Object.assign({}, F, { strength: F.strength * S.poolHigh, pool: "high" }); return F; }; }
  { const mv0 = P.move; P.move = function (rel) { const fl = this.floor, was = fl && fl.pos ? CM.floorAt(fl, fl.pos[0], fl.pos[1]) : 0, out = mv0.call(this, rel); if (!out || !fl || this.floor !== fl) return out; const now = CM.floorAt(fl, fl.pos[0], fl.pos[1]); if (now < 0 && was >= 0 && CM.fogNow) { const F = CM.fogNow(this); if (F) this.say(`${F.name[0].toUpperCase() + F.name.slice(1)} lies thick in this low hall, pooled to the walls.`); } return out; }; }
}
