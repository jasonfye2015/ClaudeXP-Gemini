"use strict";
// The Portal Court, drawn (v21.0): for every portal a name stone at its foot (its name cut and gilded), a brazier
// either side burning in the portal's colour (two frames, flickering), and a ring of runes on the flagstones before it
// in the same colour, breathing. The rules are 69p-portalcourt.js.
{ const PC = CM.PORTALCOURT;
  const hex = (c, a) => { const n = parseInt(c.slice(1), 16); return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`; };
  CM.art.nameStone = function (size, name, col) { const c = document.createElement("canvas"); c.width = c.height = size; const p = c.getContext("2d"), u = size / 64;
    p.fillStyle = "#6A6A72"; p.beginPath(); p.moveTo(4 * u, 62 * u); p.lineTo(6 * u, 26 * u); p.quadraticCurveTo(32 * u, 18 * u, 58 * u, 26 * u); p.lineTo(60 * u, 62 * u); p.closePath(); p.fill();
    p.fillStyle = "#585860"; p.fillRect(4 * u, 54 * u, 56 * u, 8 * u); p.strokeStyle = "#45454C"; p.lineWidth = u; p.stroke();
    p.fillStyle = "#2A2A30"; p.fillRect(9 * u, 33 * u, 46 * u, 15 * u); p.fillStyle = "#F0D070"; p.textAlign = "center"; p.textBaseline = "middle";
    const words = name.toUpperCase(); let fs = 7.5; p.font = `bold ${fs * u}px Georgia`; while (p.measureText(words).width > 44 * u && fs > 3.2) { fs -= 0.3; p.font = `bold ${fs * u}px Georgia`; } p.fillText(words, 32 * u, 40.5 * u);
    p.fillStyle = col; p.fillRect(14 * u, 49 * u, 36 * u, 1.5 * u); return c; };
  CM.art.brazier = function (size, col, frame) { const c = document.createElement("canvas"); c.width = c.height = size; const p = c.getContext("2d"), u = size / 64;
    p.fillStyle = "#3A3A40"; p.fillRect(30 * u, 40 * u, 4 * u, 22 * u); p.fillRect(22 * u, 60 * u, 20 * u, 3 * u); p.fillStyle = "#5A5048"; p.beginPath(); p.moveTo(18 * u, 36 * u); p.lineTo(46 * u, 36 * u); p.lineTo(40 * u, 44 * u); p.lineTo(24 * u, 44 * u); p.closePath(); p.fill();
    const g = p.createRadialGradient(32 * u, 28 * u, 1, 32 * u, 28 * u, 16 * u); g.addColorStop(0, "rgba(255,255,240,0.95)"); g.addColorStop(0.35, hex(col, 0.9)); g.addColorStop(1, hex(col, 0));
    p.fillStyle = g; p.beginPath(); const s = frame ? 1 : -1; p.moveTo(20 * u, 37 * u); p.quadraticCurveTo((26 + 3 * s) * u, 22 * u, (32 + 2 * s) * u, (8 + frame * 3) * u); p.quadraticCurveTo((38 - 2 * s) * u, 22 * u, 44 * u, 37 * u); p.closePath(); p.fill(); return c; };
  CM.art.runeRing = function (size, col) { const c = document.createElement("canvas"); c.width = c.height = size; const p = c.getContext("2d"), u = size / 64; p.strokeStyle = hex(col, 0.85); p.lineWidth = 1.6 * u;
    p.beginPath(); p.arc(32 * u, 32 * u, 25 * u, 0, Math.PI * 2); p.stroke(); p.beginPath(); p.arc(32 * u, 32 * u, 18 * u, 0, Math.PI * 2); p.stroke(); p.fillStyle = hex(col, 0.9); p.font = `${5 * u}px serif`; p.textAlign = "center"; p.textBaseline = "middle";
    const R = "ᚠᚢᚦᚨᚱᚲᚷᚹᚺᚾᛁᛃ"; for (let i = 0; i < 12; i++) { const a = (i / 12) * Math.PI * 2; p.save(); p.translate((32 + Math.cos(a) * 21.5) * u, (32 + Math.sin(a) * 21.5) * u); p.rotate(a + Math.PI / 2); p.fillText(R[i], 0, 0); p.restore(); } return c; };
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look), add = (n, c) => { set.index[n] = set.layers.length; set.layers.push(c); };
      for (const [k, , name, col] of PC.PORTALS) { add(`court:stone:${k}`, CM.art.nameStone(set.size, name, col)); add(`court:fire:${k}:0`, CM.art.brazier(set.size, col, 0)); add(`court:fire:${k}:1`, CM.art.brazier(set.size, col, 1)); add(`court:runes:${k}`, CM.art.runeRing(set.size, col)); }
      return set; }; }
  // what stands with each portal: the stone in front, a brazier either side, the runes on the square before it
  CM.courtExtras = (game, key, x, y, thing, now) => { if (!thing || thing.type !== "portal") return []; const P = PC.portalAt(x, y); if (!P) return []; const k = P[0], east = x === CM.TOWN_YARD[2] - 1, south = y === CM.TOWN_YARD[3] - 1;
      const f = Math.floor((now || 0) / 180 + x) % 2, out = [], front = east ? [-1, 0] : south ? [0, -1] : [0, 1];
      out.push({ x, y, dx: front[0] * 0.44, dz: front[1] * 0.44, layer: `court:stone:${k}`, w: 0.46, h: 0.34 });
      for (const s of [-1, 1]) out.push({ x, y, dx: east ? -0.25 : s * 0.47, dz: east ? s * 0.47 : (south ? -0.25 : 0.25), layer: `court:fire:${k}:${(f + (s > 0 ? 1 : 0)) % 2}`, w: 0.3, h: 0.42, glow: 0.7 });
      out.push({ x: x + front[0], y: y + front[1], layer: `court:runes:${k}`, flat: true, w: 0.92, glow: 0.35 + 0.15 * Math.sin((now || 0) / 600 + x + y), alpha: 0.85 });
      return out; };
}
