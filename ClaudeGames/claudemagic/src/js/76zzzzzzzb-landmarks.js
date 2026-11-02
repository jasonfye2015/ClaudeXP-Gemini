"use strict";
// Band landmarks, drawn (v40.0, UPGRADE_PLAN_35.md; the rooms are chosen by 69zzg-landmarks.js): each band's set-piece
// in its room - a centrepiece at the room's heart and its accents in the corners - with its own light: the crypt's altar
// and candle stubs, the nave's black water and drowned saint, the Forge-Hall's anvil and the hammer working on it,
// the throne and its banners, the drowned bell swinging, the fairy ring and its great cap, the crystals, the crucible
// pouring, the skull heap, the Heart-Root beating.
{ const S = 128, cv = () => { const c = document.createElement("canvas"); c.width = c.height = S; return c; };
  const PAINT = {
    "lm:altar": (p) => { p.fillStyle = "#7A6E60"; p.fillRect(14, 70, 100, 58); p.fillStyle = "#958878"; p.fillRect(8, 62, 112, 12); p.fillStyle = "#5A5046"; p.fillRect(28, 84, 72, 30);
      for (let i = 0; i < 7; i++) { const x = 16 + i * 16, h = 14 + (i * 7) % 18; p.fillStyle = "#EDE3C8"; p.fillRect(x, 62 - h, 8, h); p.fillStyle = "#FFC040"; p.beginPath(); p.ellipse(x + 4, 56 - h, 4, 7, 0, 0, Math.PI * 2); p.fill(); } },
    "lm:candles": (p) => { for (const [x, h] of [[30, 50], [54, 34], [76, 62], [96, 28]]) { p.fillStyle = "#E6DCC0"; p.fillRect(x, 128 - h, 12, h); p.fillStyle = "#FFB830"; p.beginPath(); p.ellipse(x + 6, 118 - h, 6, 11, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = "#FFF0A0"; p.beginPath(); p.ellipse(x + 6, 121 - h, 3, 5, 0, 0, Math.PI * 2); p.fill(); } },
    "lm:water": (p) => { p.fillStyle = "#1C3038"; p.fillRect(0, 0, S, S); p.strokeStyle = "#3C6070"; p.lineWidth = 3; for (let i = 0; i < 6; i++) { p.beginPath(); p.moveTo(10 + i * 9, 20 + i * 18); p.quadraticCurveTo(64, 10 + i * 18, 118 - i * 7, 24 + i * 18); p.stroke(); } },
    "lm:saint": (p) => { p.fillStyle = "#8C948E"; p.beginPath(); p.moveTo(44, 128); p.lineTo(50, 40); p.lineTo(78, 40); p.lineTo(84, 128); p.fill(); p.beginPath(); p.arc(64, 28, 14, 0, Math.PI * 2); p.fill();
      p.fillRect(18, 52, 32, 10); p.fillRect(78, 52, 32, 10); p.fillStyle = "#A8B0AA"; p.fillRect(56, 44, 6, 84); p.fillStyle = "#4A6A5A"; p.fillRect(46, 96, 36, 6); },
    "lm:anvil": (p) => { p.fillStyle = "#3A3A40"; p.beginPath(); p.moveTo(10, 50); p.lineTo(118, 50); p.lineTo(104, 72); p.lineTo(84, 72); p.lineTo(84, 104); p.lineTo(104, 128); p.lineTo(24, 128); p.lineTo(44, 104); p.lineTo(44, 72); p.lineTo(28, 72); p.closePath(); p.fill(); p.fillStyle = "#6A6A74"; p.fillRect(14, 50, 100, 6); p.fillStyle = "#FF8A30"; p.fillRect(56, 44, 26, 8); },
    "lm:hammer": (p) => { p.fillStyle = "#6A4A2A"; p.fillRect(58, 30, 12, 98); p.fillStyle = "#4A4A52"; p.fillRect(26, 6, 76, 34); p.fillStyle = "#7A7A84"; p.fillRect(26, 6, 76, 6); },
    "lm:throne": (p) => { p.fillStyle = "#3A3050"; p.fillRect(24, 8, 80, 86); p.fillStyle = "#C8A040"; p.fillRect(20, 4, 88, 8); for (const x of [24, 56, 88]) { p.beginPath(); p.moveTo(x, 6); p.lineTo(x + 8, 0); p.lineTo(x + 16, 6); p.fill(); }
      p.fillStyle = "#6A2030"; p.fillRect(36, 20, 56, 64); p.fillStyle = "#3A3050"; p.fillRect(16, 70, 96, 22); p.fillRect(16, 92, 14, 36); p.fillRect(98, 92, 14, 36); p.fillStyle = "#8A3040"; p.fillRect(30, 72, 68, 12); },
    "lm:banner": (p) => { p.fillStyle = "#5A4030"; p.fillRect(14, 4, 100, 8); p.fillStyle = "#7A1828"; p.beginPath(); p.moveTo(24, 12); p.lineTo(104, 12); p.lineTo(104, 112); p.lineTo(64, 92); p.lineTo(24, 112); p.closePath(); p.fill(); p.fillStyle = "#C8A040"; p.beginPath(); p.arc(64, 50, 16, 0, Math.PI * 2); p.fill(); p.fillStyle = "#7A1828"; p.beginPath(); p.arc(64, 50, 8, 0, Math.PI * 2); p.fill(); },
    "lm:bell": (p) => { p.fillStyle = "#4A3A2A"; p.fillRect(8, 0, 12, 128); p.fillRect(108, 0, 12, 128); p.fillRect(8, 0, 112, 12); p.fillStyle = "#5A7A6A"; p.beginPath(); p.moveTo(64, 14); p.bezierCurveTo(30, 16, 40, 70, 24, 96); p.lineTo(104, 96); p.bezierCurveTo(88, 70, 98, 16, 64, 14); p.fill(); p.fillStyle = "#7A9A88"; p.fillRect(22, 92, 84, 8); p.fillStyle = "#3A4A40"; p.beginPath(); p.arc(64, 104, 8, 0, Math.PI * 2); p.fill(); },
    "lm:cap": (p) => { p.fillStyle = "#D8D0B8"; p.fillRect(52, 54, 24, 74); p.fillStyle = "#6AC07A"; p.beginPath(); p.ellipse(64, 50, 60, 34, 0, Math.PI, 0); p.fill(); p.fillRect(4, 48, 120, 8); p.fillStyle = "#B8F0A8"; for (const [x, y, r] of [[40, 34, 8], [72, 26, 6], [94, 40, 7], [58, 44, 5]]) { p.beginPath(); p.arc(x, y, r, 0, Math.PI * 2); p.fill(); } },
    "lm:caps": (p) => { for (const [x, s] of [[24, 1], [60, 0.7], [96, 0.9]]) { p.fillStyle = "#D8D0B8"; p.fillRect(x - 4 * s, 128 - 40 * s, 8 * s, 40 * s); p.fillStyle = "#9AE890"; p.beginPath(); p.ellipse(x, 128 - 40 * s, 20 * s, 14 * s, 0, Math.PI, 0); p.fill(); } },
    "lm:crystal": (p) => { for (const [x, w, h, c] of [[64, 26, 124, "#C8A0FF"], [34, 18, 80, "#A070E8"], [94, 20, 92, "#B088F0"], [16, 12, 50, "#9060D8"], [114, 12, 56, "#9A6AE0"]]) { p.fillStyle = c; p.beginPath(); p.moveTo(x, 128 - h); p.lineTo(x + w / 2, 128 - h * 0.8); p.lineTo(x + w / 2, 128); p.lineTo(x - w / 2, 128); p.lineTo(x - w / 2, 128 - h * 0.8); p.closePath(); p.fill();
      p.fillStyle = "#F0E0FF"; p.fillRect(x - 2, 128 - h * 0.8, 3, h * 0.7); } },
    "lm:crucible": (p) => { p.fillStyle = "#3A2A22"; p.beginPath(); p.moveTo(10, 60); p.lineTo(118, 60); p.lineTo(100, 128); p.lineTo(28, 128); p.closePath(); p.fill(); p.fillStyle = "#FF7A20"; p.beginPath(); p.ellipse(64, 62, 52, 10, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = "#FFD060"; p.beginPath(); p.ellipse(64, 62, 32, 6, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = "#5A4234"; p.fillRect(10, 76, 108, 8); },
    "lm:pour": (p) => { p.fillStyle = "#FF8A20"; p.fillRect(48, 0, 32, 128); p.fillStyle = "#FFE080"; p.fillRect(58, 0, 12, 128); },
    "lm:skulls": (p) => { const sk = (x, y, r) => { p.fillStyle = "#E8DEC4"; p.beginPath(); p.arc(x, y, r, 0, Math.PI * 2); p.fill(); p.fillRect(x - r * 0.6, y + r * 0.5, r * 1.2, r * 0.6); p.fillStyle = "#2A2220"; p.beginPath(); p.arc(x - r * 0.38, y, r * 0.26, 0, Math.PI * 2); p.arc(x + r * 0.38, y, r * 0.26, 0, Math.PI * 2); p.fill(); };
      for (let row = 0; row < 5; row++) for (let i = 0; i <= 4 - row; i++) sk(16 + row * 12 + i * 24, 116 - row * 22, 11); },
    "lm:root": (p) => { p.fillStyle = "#6A1A1A"; p.beginPath(); p.ellipse(64, 80, 56, 46, 0, 0, Math.PI * 2); p.fill(); p.strokeStyle = "#9A2A28"; p.lineWidth = 10; p.lineCap = "round"; for (let i = 0; i < 6; i++) { p.beginPath(); p.moveTo(64, 80); p.quadraticCurveTo(64 + Math.cos(i) * 70, 40 + Math.sin(i * 2) * 30, 64 + Math.cos(i * 1.7) * 60, 128); p.stroke(); }
      p.fillStyle = "#C83838"; p.beginPath(); p.ellipse(64, 72, 22, 18, 0, 0, Math.PI * 2); p.fill(); },
    "lm:mote": (p) => { p.fillStyle = "#FFD070"; p.beginPath(); p.arc(64, 64, 40, 0, Math.PI * 2); p.fill(); },
  };
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); for (const [n, f] of Object.entries(PAINT)) { const c = cv(); f(c.getContext("2d")); set.index[n] = set.layers.length; set.layers.push(c); } return set; }; }
  const put = (out, fx, fz, layer, w, h, o = {}) => { const x = Math.floor(fx), y = Math.floor(fz); out.push(Object.assign({ x, y, dx: fx - x - 0.5, dz: fz - y - 0.5, layer, w, h, lift: 0 }, o)); };
  // band -> [centrepiece, its width, its height, the corner accent, its size, light colour or null]
  const SET = [["lm:altar", 0.7, 0.55, "lm:candles", 0.35, [1.0, 0.75, 0.4]], ["lm:saint", 0.55, 0.95, null, 0, [0.5, 0.7, 0.9]], ["lm:anvil", 0.6, 0.45, null, 0, [1.0, 0.55, 0.2]], ["lm:throne", 0.65, 0.85, "lm:banner", 0.45, null], ["lm:bell", 0.7, 0.8, null, 0, [0.5, 0.8, 0.9]],
    ["lm:cap", 0.95, 0.9, "lm:caps", 0.4, [0.5, 1.0, 0.55]], ["lm:crystal", 0.75, 0.95, "lm:crystal", 0.45, [0.75, 0.55, 1.0]], ["lm:crucible", 0.75, 0.6, null, 0, [1.0, 0.5, 0.15]], ["lm:skulls", 0.75, 0.6, "lm:candles", 0.35, [1.0, 0.8, 0.5]], ["lm:root", 1.0, 0.9, null, 0, [1.0, 0.25, 0.2]]];
  const near = (fl, x, y) => Math.abs(x - fl.pos[0]) + Math.abs(y - fl.pos[1]) <= 12;
  { const ls0 = CM.lifeSprites; CM.lifeSprites = (game, fl, now) => { const out = ls0 ? ls0(game, fl, now) : []; const M = fl && fl.landmark; if (!M || !CM.renderer || CM.renderer.index["lm:altar"] === undefined || !near(fl, M.at[0], M.at[1])) return out;
      const [lay, w, h, acc, aw] = SET[M.band] || SET[0], t = now / 1000, still = CM.reducedMotion, cx = M.at[0] + 0.5, cz = M.at[1] + 0.5;
      if (M.band === 1 || M.band === 4) for (let y = M.y0; y <= M.y1; y++) for (let x = M.x0; x <= M.x1; x++) if (fl.grid[y][x] === 0) put(out, x + 0.5, y + 0.5, "lm:water", 1.0, 1.0, { flat: true, lift: 0.015, glow: 0.3, alpha: 0.85, spin: 0 });
      if (M.band === 4) put(out, cx, cz, lay, w, h, { tilt: still ? 0 : Math.sin(t * 0.9) * 0.06 });
      else if (M.band === 9) { const beat = still ? 1 : 1 + 0.05 * Math.max(0, Math.sin(t * 2.4)) ** 6; put(out, cx, cz, lay, w * beat, h * beat, { glow: 1.1 }); }
      else put(out, cx, cz, lay, w, h, { glow: M.band === 6 ? 1.3 : M.band === 7 ? 0.8 : 0.2 });
      if (M.band === 2) { const k = still ? 0.5 : Math.abs(Math.sin(t * 2.2)); put(out, cx + 0.05, cz, "lm:hammer", 0.3, 0.38, { lift: 0.42 + k * 0.3, tilt: -0.3 + k * 0.4 }); if (!still && k < 0.12) for (let i = 0; i < 4; i++) put(out, cx + Math.cos(t * 40 + i) * 0.15, cz + Math.sin(t * 31 + i) * 0.1, "lm:mote", 0.04, 0.04, { lift: 0.47 + i * 0.05, glow: 2 }); }
      if (M.band === 7) put(out, cx, cz, "lm:pour", 0.12, 1.2 + (still ? 0 : Math.sin(t * 7) * 0.03), { lift: 0.45, glow: 2 });
      if (acc) for (const [x, y, sx, sz] of [[M.x0, M.y0, -1, -1], [M.x1, M.y0, 1, -1], [M.x0, M.y1, -1, 1], [M.x1, M.y1, 1, 1]]) { if (fl.grid[y][x] !== 0 || fl.things[`${x},${y}`]) continue;
        put(out, x + 0.5 + sx * 0.28, y + 0.5 + sz * 0.28, acc, aw, M.band === 3 ? aw * 1.5 : aw, { glow: M.band === 3 ? 0.1 : 1.0, lift: M.band === 3 ? 0.35 : 0 }); }
      if (M.band === 5 && !still) for (let i = 0; i < 5; i++) { const ph = (t * 0.3 + i / 5) % 1; put(out, cx + Math.cos(i * 2.2) * 0.8, cz + Math.sin(i * 2.2) * 0.8, "lm:mote", 0.03, 0.03, { lift: 0.1 + ph * 1.0, glow: 2, alpha: 1 - ph }); }
      return out; }; }
  { const xl0 = CM.extraLights; CM.extraLights = (game, fl, out, renderer) => { if (xl0) xl0(game, fl, out, renderer); const M = fl && fl.landmark; if (!M || !near(fl, M.at[0], M.at[1])) return; const c = (SET[M.band] || SET[0])[5]; if (!c) return;
      const pulse = M.band === 9 && !CM.reducedMotion ? 0.7 + 0.3 * Math.max(0, Math.sin(performance.now() / 1000 * 2.4)) ** 6 : 1;
      out.push({ x: M.at[0] + 0.5, y: 0.6, z: M.at[1] + 0.5, reach: M.band === 7 ? 4.5 : 3.4, colour: c.map((v) => v * pulse), flicker: [0, 2, 7, 8].includes(M.band), d: Math.abs(M.at[0] - fl.pos[0]) + Math.abs(M.at[1] - fl.pos[1]) }); }; }
}
