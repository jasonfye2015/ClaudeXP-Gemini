"use strict";
// Weather that matters (v27.0, UPGRADE_PLAN_22.md): the day's weather is felt, not only seen. Rain, outdoors after dark,
// burns a torch twice as fast, and now and then a gust and the rain put it out for a few steps (a lantern, shut in its
// glass, cares for neither). Mist on the surface shortens the party's sight: two squares ahead, not four, on the map
// and in the view. Snow lying in the Wood slows the party: every step is two minutes, and the walk is heavier.
{ const WX = CM.WEATHERPLAY = { gustEvery: 70, gutterSteps: 3, mistSight: 2, snowFrom: 0.3 };
  const day = (game) => (CM.dayOf ? Math.max(0, CM.dayOf(game)) : 0);
  // how deep the snow lies, 0 to 1: it builds over the days it falls and melts on the days it doesn't (v24.2)
  CM.snowDepth = (game) => {
    if (CM.season(game) !== "winter" || !game || game.seed === undefined) return 0;
    if (CM.seasonOff) return CM.snowLying(game) ? 1 : 0;
    const d = day(game), of = (n) => CM.weatherOf(game.seed, n, "winter") === "snow", frac = ((CM.minuteOf ? CM.minuteOf(game) : 720) % 1440) / 1440;
    let depth = 0; for (let n = Math.max(0, d - 5); n < d; n++) depth = Math.min(1, Math.max(0, depth + (of(n) ? 0.45 : -0.22)));
    depth = Math.min(1, Math.max(0, depth + (CM.weather(game) === "snow" ? 0.45 : -0.22) * frac));
    return Math.round(depth * 20) / 20;
  };
  const outside = (g) => g.floor && (g.floor.number === 0 || g.floor.number === -1);
  const P = CM.Game.prototype;
  // rain on a torch
  const burn0 = P.burn;
  P.burn = function (...a) {
    const g = this, fl = g.floor;
    if (fl && fl.number === -1 && CM.snowDepth && CM.snowDepth(g) >= WX.snowFrom) g.clock = (g.clock || 0) + 1;   // (snow underfoot: the step takes two minutes)
    if (g.gutter > 0) { g.gutter -= 1; if (g.gutter === 0) g.say("The torch is lit again, a hand cupped round it."); return; }   // (out: it doesn't burn while out)
    const out = burn0.apply(this, a);
    if (outside(g) && fl.number === -1 && CM.isNight(g) && CM.weather(g) === "rain" && g.light && g.light.kind === "torch" && !g.lightOut) {
      g.light.left -= 1;                                                   // (the rain on it: twice the burn)
      if (CM.hashSeed(`${g.seed}:gust:${g.clock}`) % WX.gustEvery === 0) { g.gutter = WX.gutterSteps; g.say("A gust and the rain put the torch out. It takes a few steps to light it again."); g.emit && g.emit("change"); }
    }
    return out;
  };
  const lf0 = P.lightFactor; P.lightFactor = function (...a) { if (this.gutter > 0) return this.floor && this.floor.number === -1 ? 0.3 : 0.22; return lf0.apply(this, a); };
  const hl0 = P.hasLight; P.hasLight = function (...a) { if (this.gutter > 0 && !(this.spellLight > 0)) return false; return hl0.apply(this, a); };
  // mist: the party sees less far
  const look0 = P.look;
  P.look = function (...a) {
    const fl = this.floor; if (!fl || !outside(this) || CM.weather(this) !== "mist") return look0.apply(this, a);
    const had = new Set(fl.seen.map(([x, y]) => `${x},${y}`)), out = look0.apply(this, a), [px, py] = fl.pos;
    fl.seen = fl.seen.filter(([x, y]) => had.has(`${x},${y}`) || Math.max(Math.abs(x - px), Math.abs(y - py)) <= ((CM.mistSightNow && CM.mistSightNow(this)) || WX.mistSight));   // (what the mist hid stays unseen; v73.0: one square in a dense mist)
    return out;
  };
  // snow: the walk is heavier in the Wood
  const wp0 = P.walkPace; P.walkPace = function (...a) { const p = wp0.apply(this, a); return this.floor && this.floor.number === -1 && CM.snowDepth && CM.snowDepth(this) >= WX.snowFrom ? p * 1.5 : p; };
}
