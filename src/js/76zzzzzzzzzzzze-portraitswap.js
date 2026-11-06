"use strict";
// The sprite portraits, wherever they were handed out early (v99.1): a portrait made before the heroes' dolls were
// decoded (the title card, the Hall of Fame, the legends, a saved run's cards - anything drawn in the first moment) is
// the drawn stand-in. Each such canvas is remembered, and when the dolls arrive it is drawn over in place from them, so
// no screen has to know to redraw itself. Loaded after every other portrait wrapper (the gear, the scars), so the whole
// picture is redrawn.
{ const P = CM.UI.prototype, base = P.portrait, early = [];
  P.portrait = function (who, size) {
    const c = base.call(this, who, size);
    if (!(CM.art.hasDolls && CM.art.hasDolls()) && c && c.getContext) early.push({ c, who, size });
    return c;
  };
  CM.swapEarlyPortraits = function (ui) {
    if (!(CM.art.hasDolls && CM.art.hasDolls()) || !early.length) return 0;
    let n = 0; for (const e of early.splice(0)) { try { const fresh = base.call(ui, e.who, e.size); const p = e.c.getContext("2d"); p.clearRect(0, 0, e.c.width, e.c.height); p.drawImage(fresh, 0, 0, e.c.width, e.c.height); n++; } catch (err) { /* (a screen gone: nothing to draw on) */ } }
    return n;
  };
  { const r0 = P.restyle; P.restyle = function (...a) { const out = r0 ? r0.apply(this, a) : undefined; CM.swapEarlyPortraits(this); return out; }; }
  // and if the dolls arrive without a restyle (the look already right), swap all the same
  if (CM.art.load) { const t = setInterval(() => { if (CM.art.hasDolls && CM.art.hasDolls()) { clearInterval(t); if (CM.ui) CM.swapEarlyPortraits(CM.ui); } }, 250); setTimeout(() => clearInterval(t), 60000); }
}
