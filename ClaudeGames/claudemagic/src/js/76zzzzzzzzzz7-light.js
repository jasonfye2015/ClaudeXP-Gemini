"use strict";
// The light of the hour, the window's side (v59.0, UPGRADE_PLAN_54.md): the sun's colour falls on what faces it - gold
// at dawn and dusk on the sunward walls and the ground, white at noon, silver-blue under the moon - and the sky warms
// about the sun when it is low and cools on the far side (40-render.js: uSunCol). Mist lies on the water and its banks
// at dawn and on autumn evenings (uWaterMist). At night the lamps and the lit windows wear a halo in the damp air -
// wide and soft in mist and rain, a faint one on a clear night (the "halo" sprites). By 24c-light.js.
{ const P = 64, PAINT = {
    halo: (p) => { const g = p.createRadialGradient(P / 2, P / 2, 0, P / 2, P / 2, P / 2); g.addColorStop(0, "rgba(255,225,170,0.75)"); g.addColorStop(0.3, "rgba(255,205,140,0.34)"); g.addColorStop(0.65, "rgba(255,190,120,0.1)"); g.addColorStop(1, "rgba(255,180,110,0)"); p.fillStyle = g; p.fillRect(0, 0, P, P); },
    "halo:cool": (p) => { const g = p.createRadialGradient(P / 2, P / 2, 0, P / 2, P / 2, P / 2); g.addColorStop(0, "rgba(190,215,255,0.75)"); g.addColorStop(0.3, "rgba(170,200,255,0.34)"); g.addColorStop(0.65, "rgba(150,190,255,0.1)"); g.addColorStop(1, "rgba(140,180,255,0)"); p.fillStyle = g; p.fillRect(0, 0, P, P); } };
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); for (const [k, f] of Object.entries(PAINT)) { if (set.index[k] !== undefined) continue; const c = document.createElement("canvas"); c.width = c.height = P; f(c.getContext("2d")); set.index[k] = set.layers.length; set.layers.push(c); } return set; }; }
  { const s0 = CM.art.isSurfaceLayer; CM.art.isSurfaceLayer = (name) => name in PAINT || s0(name); }
  { const bf0 = CM.beforeFrame; CM.beforeFrame = (game, r, dt, now) => { if (bf0) bf0(game, r, dt, now); const fl = game && game.floor;
      if (!fl || !r.sky || game.mode === "title") { r.sunCol = null; r.waterMist = 0; r.haloAir = 0; return; }
      const S = CM.sunColour(game); r.sunCol = [S.col[0], S.col[1], S.col[2], S.glow]; r.waterMist = CM.waterMist(game); r.haloAir = CM.haloAir(game); }; }
  // the halos: one soft disc at each light within reach, sized by the light's reach, cool for a blue light
  { const ls0 = CM.lifeSprites; CM.lifeSprites = (game, fl, now) => { const out = ls0 ? ls0(game, fl, now) : []; const r = CM.renderer;
      if (!r || !r.sky || !(r.haloAir > 0) || !r.index || r.index.halo === undefined || (game.settings && game.settings.detail === "low")) return out;
      for (const l of r.lights || []) { if (!l || l.reach === undefined) continue; const [px, py] = fl.pos; if (Math.abs(l.x - 0.5 - px) + Math.abs(l.z - 0.5 - py) > 11) continue;
        const cool = l.colour && l.colour[2] > l.colour[0] * 1.15, s = 0.5 + l.reach * 0.3, x = Math.floor(l.x - 0.5), y = Math.floor(l.z - 0.5);
        out.push({ x, y, dx: l.x - x - 0.5, dz: l.z - y - 0.5, layer: cool ? "halo:cool" : "halo", w: s, h: s, lift: l.y - s / 2, glow: 1.3, alpha: Math.min(0.9, 0.35 + 0.55 * r.haloAir) * r.haloAir, shade: 1 }); }
      return out; }; }
}
