"use strict";
// Footsteps by the ground (v28.3, UPGRADE_PLAN_23.md): a step sounds like what is underfoot - a sharp click on the
// town's cobbles and flagstones, a soft brush through grass and moss, a dull fall on earth, a hollow knock on boards
// (the bridge, the houses' rooms), a splash in water and a crunch in snow lying; below ground, each depth's own as
// before, and a splash in its puddles.
{ const A = CM.audio;
  const cook0 = A._cook;
  A._cook = function (...a) { const out = cook0.apply(this, a), N = (len, vol, smooth, seed) => this._noise(len, vol, smooth, seed);
    const R = { step_stone: () => this._mix(N(0.035, 0.32, 0.015, 21), this._tones([[210, 0.025]], "square", 0.05)),
      step_grass: () => this._mix(N(0.13, 0.11, 0.004, 23), this._after(0.04, N(0.08, 0.06, 0.004, 24))),
      step_wood: () => this._mix(this._tones([[150, 0.06]], "sine", 0.26), this._tones([[300, 0.03]], "sine", 0.06), N(0.05, 0.1, 0.3, 25)),
      step_snow: () => this._mix(N(0.03, 0.2, 0.05, 27), this._after(0.035, N(0.03, 0.18, 0.05, 29)), this._after(0.075, N(0.04, 0.14, 0.05, 31)), this._after(0.11, N(0.03, 0.08, 0.05, 33))) };
    for (const [name, make] of Object.entries(R)) Object.defineProperty(this.buffers, name, { configurable: true, enumerable: true,
      get: () => { const b = this._buffer(make()); Object.defineProperty(this.buffers, name, { value: b, writable: true, configurable: true, enumerable: true }); return b; } });
    return out; };
  // what is underfoot
  CM.stepSound = (game, fallback) => { const fl = game.floor; if (!fl) return fallback; const n = fl.number, [x, y] = fl.pos;
    if (CM.waterHere && CM.waterHere(x, y)) return "step_water";
    if (fl.special === "interior") return ["smith", "temple"].includes(fl.interior) ? "step_stone" : "step_wood";
    if (n === 0 || n === -1) { if (CM.snowDepth && CM.snowDepth(game) >= 0.3) return "step_snow"; const gr = CM.groundAt(fl, x, y);
      return gr === "cobbles" || gr === "flags" ? "step_stone" : gr === "planks" ? "step_wood" : gr === "grass" || gr === "moss" || gr === "needles" || gr === "litter" ? "step_grass" : "step"; }
    return fallback; };
}
