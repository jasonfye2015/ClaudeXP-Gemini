"use strict";
// The water basins - the window's side (UPGRADE_PLAN_63.md set 1.1, release 2): the spiked grating is drawn on its
// square (the barred-grate picture, flat, with spikes when dry and a dark shape under the water when flooded); a
// sunk chest lies in a stone basin; the waist-deep water sounds deeper under the step and the look line names the
// depth; and standing in deep water the view sits a little lower.
{ const look = (game) => { const fl = game.floor; if (!fl || !fl.pos) return null; const d = CM.floodDepth(game, fl, fl.pos[0], fl.pos[1]); return d === 2 ? "waist-deep" : d === 1 ? "knee-deep" : null; };
  { const ls0 = CM.lifeSprites; CM.lifeSprites = (game, fl, now) => { const out = ls0 ? ls0(game, fl, now) : []; if (!fl || !(fl.number >= 1) || !CM.basinsOf || game.mode === "title") return out; const R0 = CM.renderer; if (!R0 || R0.index["clut:grate"] === undefined) return out; const Bs = CM.basinsOf(fl);
      for (const k of Bs.grates) { const [x, y] = k.split(",").map(Number); if (Math.abs(x - fl.pos[0]) + Math.abs(y - fl.pos[1]) > 12) continue; const d = CM.floodDepth(game, fl, x, y); out.push({ x, y, layer: "clut:grate", flat: true, w: 0.82, base: CM.floorAt(fl, x, y) + 0.004, shade: d ? 0.55 : 0.95, alpha: d ? 0.7 : 1 }); }
      for (const k of Bs.chests) { const [x, y] = k.split(",").map(Number); if (Math.abs(x - fl.pos[0]) + Math.abs(y - fl.pos[1]) > 12) continue; out.push({ x, y, layer: "clut:port", flat: true, w: 0.9, base: CM.floorAt(fl, x, y) + 0.003, shade: 0.8 }); }   // (the basin the chest sits in)
      return out; }; }
  // the step's splash, deeper; the view lower
  const bf0 = CM.beforeFrame; CM.beforeFrame = (game, r, dt, now) => { if (bf0) bf0(game, r, dt, now); if (!game || !game.floor || !game.ext) return; void r;
    if (game.on && !game._basinHooked) { game._basinHooked = true; game.on("moved", () => { if (CM.floodDepthHere(game) === 2 && CM.wadeSound) CM.wadeSound(true); }); } };
  // the look line names the water
  { const d0 = CM.UI.prototype.drawSky; if (d0) CM.UI.prototype.drawSky = function (...a) { const out = d0.apply(this, a); try { const g = this.game, w = g && look(g); const el = this.$ && this.$("#view .sky .wxtext"); if (el && w && !el.textContent.includes(w)) el.textContent += ` - ${w} in water`; } catch (e) { /* (quiet) */ } return out; }; }
}
