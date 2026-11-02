"use strict";
// Stained glass (v41.1, UPGRADE_PLAN_36.md): the Temple's walls have windows - three tall lancets down each side and a
// rose over the altar - and by day the sun comes through them: the glass glows, and pools of coloured light lie on the
// floor and over the pews from whichever side the sun is on (the east windows in the morning, the west in the
// afternoon), sliding as it goes over; at night the glass is dark and only the candles light the room.
{ const S = 128, cv = () => { const c = document.createElement("canvas"); c.width = c.height = S; return c; };
  const GLASS = ["#C82838", "#2850B8", "#E8B020", "#2A8A48", "#8A38A8", "#E86A20"];
  const PAINT = {
    "sg:lancet": (p) => { p.fillStyle = "#3A3028"; p.beginPath(); p.moveTo(28, 128); p.lineTo(28, 40); p.quadraticCurveTo(64, -20, 100, 40); p.lineTo(100, 128); p.closePath(); p.fill();
      for (let r = 0; r < 7; r++) for (let c = 0; c < 3; c++) { p.fillStyle = GLASS[(r * 2 + c) % GLASS.length]; const x = 34 + c * 21, y = 34 + r * 13; p.fillRect(x, y, 18, 10); }
      p.fillStyle = GLASS[2]; p.beginPath(); p.moveTo(34, 32); p.quadraticCurveTo(64, -6, 94, 32); p.closePath(); p.fill(); p.fillStyle = "#3A3028"; p.fillRect(62, 8, 4, 120); },
    "sg:rose": (p) => { p.fillStyle = "#3A3028"; p.beginPath(); p.arc(64, 64, 62, 0, Math.PI * 2); p.fill(); for (let i = 0; i < 12; i++) { p.fillStyle = GLASS[i % GLASS.length]; p.beginPath(); p.moveTo(64, 64); p.arc(64, 64, 56, i * Math.PI / 6 + 0.05, (i + 1) * Math.PI / 6 - 0.05); p.closePath(); p.fill(); }
      p.fillStyle = "#3A3028"; p.beginPath(); p.arc(64, 64, 22, 0, Math.PI * 2); p.fill(); p.fillStyle = GLASS[2]; p.beginPath(); p.arc(64, 64, 17, 0, Math.PI * 2); p.fill(); },
    "sg:pool": (p) => { for (let r = 0; r < 4; r++) for (let c = 0; c < 3; c++) { p.fillStyle = GLASS[(r + c * 2) % GLASS.length]; p.fillRect(8 + c * 38, 6 + r * 30, 34, 26); } },
  };
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); for (const [n, f] of Object.entries(PAINT)) { const c = cv(); f(c.getContext("2d")); set.index[n] = set.layers.length; set.layers.push(c); } return set; }; }
  const ROWS = [4, 6, 8], sunNow = (game) => { const sky = CM.renderer && CM.renderer.sky; if (CM.isNight && CM.isNight(game)) return null; if (sky && sky.sun !== null && sky.sun !== undefined) return sky.sun; const h = CM.hourOf ? CM.hourOf(game) : 12; return h >= 6 && h <= 20 ? (h - 6) / 14 : null; };
  { const ls0 = CM.lifeSprites; CM.lifeSprites = (game, fl, now) => { const out = ls0 ? ls0(game, fl, now) : []; if (!fl || fl.interior !== "temple" || !CM.renderer || CM.renderer.index["sg:lancet"] === undefined) return out;
      const sun = sunNow(game), lit = sun !== null ? Math.max(0.2, Math.sin(Math.PI * sun)) : 0;
      for (const y of ROWS) { out.push({ x: 2, y, layer: "sg:lancet", face: 3, w: 0.5, h: 0.74, lift: 0.12, glow: 0.3 + lit * 1.4 }); out.push({ x: 10, y, layer: "sg:lancet", face: 1, w: 0.5, h: 0.74, lift: 0.12, glow: 0.3 + lit * 1.4 }); }
      out.push({ x: 6, y: 2, layer: "sg:rose", face: 0, w: 0.66, h: 0.66, lift: 0.16, glow: 0.3 + lit * 1.5 });
      if (sun !== null) { const east = sun < 0.5, reach = 1.2 + Math.abs(sun - 0.5) * 4, a = 0.38 + lit * 0.35;   /* (low sun, long pools) */
        for (const y of ROWS) { const fx = east ? 10.5 - reach : 2.5 + reach, x = Math.floor(fx); out.push({ x, y, dx: fx - x - 0.5, dz: 0.05, layer: "sg:pool", flat: true, w: 0.75, len: 1 + Math.abs(sun - 0.5) * 2, rot: east ? Math.PI : 0, glow: 2, alpha: a }); }
        out.push({ x: 6, y: 4, dz: -0.2, layer: "sg:pool", flat: true, w: 0.6, glow: 2, alpha: a * 0.8 }); }
      return out; }; }
  { const xl0 = CM.extraLights; CM.extraLights = (game, fl, out, renderer) => { if (xl0) xl0(game, fl, out, renderer); if (!fl || fl.interior !== "temple") return; const sun = sunNow(game); if (sun === null) return; const lit = Math.max(0.2, Math.sin(Math.PI * sun)), east = sun < 0.5;
      out.push({ x: east ? 9.2 : 3.8, y: 0.8, z: 6.5, reach: 4.5, colour: [0.55 * lit, 0.45 * lit, 0.75 * lit], flicker: false, d: 2 }); out.push({ x: 6.5, y: 0.9, z: 3.0, reach: 3, colour: [0.6 * lit, 0.35 * lit, 0.4 * lit], flicker: false, d: 3 }); }; }
}
