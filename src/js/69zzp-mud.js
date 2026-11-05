"use strict";
// Mud (v77.0, UPGRADE_PLAN_61.md part 7): the rain's strength over the last hours makes mud of the earth squares
// above ground - the dirt, the tilled rows and the Wood's litter - and a step on it costs an extra minute at half
// mud or more, the walk heavier with it (as snow does in the Wood, 69v-weather.js). The window darkens the earth by
// it. State is the weather's own (24f-events.js): nothing new is kept.
//   CM.mudNow(game) -> 0..1      CM.mudHere(game) -> 0..1 on the party's square (0 off the earth)
{ const M = CM.MUD = { hours: 3, from: 0.5, earth: ["dirt", "tilled", "litter"] };
  CM.mudNow = (game) => { if (!game || !game.ext) return 0; const W = CM.weatherStep(game); if (!W || !W.cur) return 0; const now = CM.weatherNow(game), t = CM.clockOf(game), rain = (e) => e && (e.kind === "rain" || e.kind === "storm");
    let m = 0; if (rain(W.cur)) m = Math.min(1, 0.35 + 0.65 * now.strength * (W.cur.kind === "storm" ? 1.2 : 1));
    if (W.prev && rain(W.prev)) { const since = t - W.prev.until, k = Math.max(0, 1 - since / (M.hours * 60)) * Math.min(1, W.prev.strength + (W.prev.kind === "storm" ? 0.3 : 0)); m = Math.max(m, k); }
    return Math.round(m * 100) / 100; };
  CM.mudHere = (game) => { const fl = game && game.floor; if (!fl || !(fl.number === 0 || fl.number === -1) || !fl.pos) return 0; const g = CM.groundAt(fl, fl.pos[0], fl.pos[1]) || (fl.number === -1 ? "litter" : "grass"); return M.earth.includes(g) ? CM.mudNow(game) : 0; };
  const P = CM.Game.prototype, burn0 = P.burn; P.burn = function (...a) { if (CM.mudHere(this) >= M.from) this.clock = (this.clock || 0) + 1; return burn0.apply(this, a); };   // (mud underfoot: the step takes two minutes)
  const wp0 = P.walkPace; P.walkPace = function (...a) { const p = wp0.apply(this, a), m = CM.mudHere(this); return m > 0.3 ? p * (1 + 0.5 * m) : p; };
}
