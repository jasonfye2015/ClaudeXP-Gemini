"use strict";
// The portals' own looks (v21.2): each court portal and its twin in the Wood drawn as its own place - the Mage Tower's
// rune-cut violet stone, Leshy's roots and antlers, Claudeita's rough rock with sand running down it, the Fortress's
// black stone bound in iron, Haven's red gothic arch, the Glyph Deep's green letters falling (the Neather Gate keeps its
// basalt) - with a glimpse of the far side in the swirl, by day or by night, and a badge over the arch: one figure for
// one hero, four for the party. Standing at one, the hint line names it and what's waiting. Stepping through: a swirl
// of its colour and a fade, and each portal its own note; and near one, its hum. The rules are 69r-portallooks.js.
{ const PC = CM.PORTALCOURT, PL = CM.PORTALLOOKS, KEYS = ["tower", "cabin", "claudeita", "fortress", "ablo", "glyph"];
  const NOTE = { tower: 1.25, cabin: 0.85, claudeita: 0.95, fortress: 0.7, ablo: 0.8, glyph: 1.5, gate: 0.6, waystone: 1.1 };
  // the far side, small, in the middle of the swirl
  const glimpse = (p, k, cx, cy, r, night) => { p.save(); p.beginPath(); p.ellipse(cx, cy, r * 0.62, r * 0.9, 0, 0, Math.PI * 2); p.clip();
    const sky = p.createLinearGradient(0, cy - r, 0, cy + r); sky.addColorStop(0, night ? "#0A1030" : "#90B8E8"); sky.addColorStop(1, night ? "#203050" : "#D8E8F0"); p.fillStyle = sky; p.fillRect(cx - r, cy - r, 2 * r, 2 * r);
    const ground = k === "claudeita" ? "#8A7A5A" : k === "ablo" ? "#3A2A2A" : k === "glyph" ? "#203020" : "#3A6A30", gy = cy + r * 0.35; p.fillStyle = night ? "#1A2418" : ground; p.fillRect(cx - r, gy, 2 * r, r);
    const s = r / 40; p.fillStyle = night ? "#101018" : "#3A3A48";
    if (k === "tower") { p.fillRect(cx - 5 * s, gy - 34 * s, 10 * s, 34 * s); p.beginPath(); p.moveTo(cx - 8 * s, gy - 34 * s); p.lineTo(cx, gy - 46 * s); p.lineTo(cx + 8 * s, gy - 34 * s); p.fill(); p.fillStyle = "#C0A0FF"; p.fillRect(cx - 1.5 * s, gy - 26 * s, 3 * s, 4 * s); }
    else if (k === "cabin") { p.fillStyle = night ? "#20140C" : "#5A3A20"; p.fillRect(cx - 12 * s, gy - 12 * s, 24 * s, 12 * s); p.beginPath(); p.moveTo(cx - 15 * s, gy - 12 * s); p.lineTo(cx, gy - 24 * s); p.lineTo(cx + 15 * s, gy - 12 * s); p.fill(); p.fillStyle = "#FFD070"; p.fillRect(cx - 3 * s, gy - 8 * s, 5 * s, 4 * s); }
    else if (k === "claudeita") { p.fillStyle = night ? "#2A2420" : "#7A6A58"; p.beginPath(); p.moveTo(cx - 20 * s, gy); p.lineTo(cx - 6 * s, gy - 24 * s); p.lineTo(cx + 8 * s, gy - 18 * s); p.lineTo(cx + 20 * s, gy); p.fill(); p.fillStyle = "#100808"; p.beginPath(); p.arc(cx, gy, 6 * s, Math.PI, 0); p.fill(); }
    else if (k === "fortress") { p.fillRect(cx - 18 * s, gy - 16 * s, 36 * s, 16 * s); for (const dx of [-18, 12]) p.fillRect(cx + dx * s, gy - 24 * s, 6 * s, 24 * s); p.fillStyle = "#4A2A18"; p.fillRect(cx - 4 * s, gy - 9 * s, 8 * s, 9 * s); }
    else if (k === "ablo") { p.fillStyle = night ? "#1A0808" : "#5A2020"; p.fillRect(cx - 10 * s, gy - 22 * s, 20 * s, 22 * s); p.beginPath(); p.moveTo(cx - 10 * s, gy - 22 * s); p.lineTo(cx, gy - 38 * s); p.lineTo(cx + 10 * s, gy - 22 * s); p.fill(); p.fillStyle = "#FF6040"; p.fillRect(cx - 2 * s, gy - 16 * s, 4 * s, 7 * s); }
    else if (k === "glyph") { p.fillStyle = "#000"; p.fillRect(cx - r, cy - r, 2 * r, 2 * r); p.fillStyle = "#40F070"; p.font = `${7 * s}px monospace`; p.textAlign = "center"; const L = "@.#>$g!?"; for (let i = 0; i < 18; i++) p.fillText(L[i % L.length], cx + (((i * 37) % 50) - 25) * s, cy + (((i * 23) % 70) - 35) * s); }
    p.restore(); };
  // the frame: its own stone, wood or iron, and the badge over it
  CM.art.portalFor = function (size, k, night) { const c = document.createElement("canvas"); c.width = c.height = size; const p = c.getContext("2d"), u = size / 64, col = PC.byKey[k][3];
    const arch = (w, top, fill, stroke) => { p.fillStyle = fill; p.beginPath(); p.moveTo((32 - w) * u, 64 * u); p.lineTo((32 - w) * u, top * u); p.quadraticCurveTo(32 * u, (top - w * 1.25) * u, (32 + w) * u, top * u); p.lineTo((32 + w) * u, 64 * u); p.closePath(); p.fill(); if (stroke) { p.strokeStyle = stroke; p.lineWidth = 1.2 * u; p.stroke(); } };
    if (k === "tower") { arch(22, 26, "#4A3A6A", "#2A1A4A"); p.fillStyle = "#C0A0FF"; p.font = `${4 * u}px serif`; p.textAlign = "center"; for (let i = 0; i < 6; i++) { p.fillText("ᚱᚾᛟᛞᛗᛉ"[i], 13 * u, (30 + i * 5.5) * u); p.fillText("ᛞᛉᚱᛟᛗᚾ"[i], 51 * u, (30 + i * 5.5) * u); } }
    else if (k === "cabin") { arch(22, 26, "#5A3A20", null); p.strokeStyle = "#3A2410"; p.lineWidth = 2.5 * u; for (const sx of [-1, 1]) { p.beginPath(); p.moveTo((32 + sx * 20) * u, 64 * u); p.bezierCurveTo((32 + sx * 26) * u, 40 * u, (32 + sx * 14) * u, 20 * u, (32 + sx * 6) * u, 8 * u); p.stroke(); }
      p.strokeStyle = "#D8C8A0"; p.lineWidth = 1.6 * u; for (const sx of [-1, 1]) { p.beginPath(); p.moveTo((32 + sx * 4) * u, 9 * u); p.lineTo((32 + sx * 14) * u, 2 * u); p.moveTo((32 + sx * 9) * u, 5.5 * u); p.lineTo((32 + sx * 9) * u, 1 * u); p.stroke(); } }
    else if (k === "claudeita") { p.fillStyle = "#7A6A58"; p.beginPath(); p.moveTo(8 * u, 64 * u); p.lineTo(10 * u, 30 * u); p.lineTo(18 * u, 14 * u); p.lineTo(30 * u, 8 * u); p.lineTo(44 * u, 12 * u); p.lineTo(54 * u, 28 * u); p.lineTo(56 * u, 64 * u); p.closePath(); p.fill();
      p.fillStyle = "#E0C080"; for (let i = 0; i < 14; i++) p.fillRect((12 + ((i * 7) % 40)) * u, (20 + ((i * 11) % 40)) * u, 0.9 * u, 3 * u); }
    else if (k === "fortress") { arch(22, 24, "#1E1E24", null); p.fillStyle = "#6A6A74"; for (const y of [30, 44, 58]) p.fillRect(9 * u, y * u, 46 * u, 2.2 * u); for (const x of [10, 52]) for (const y of [31, 45, 59]) { p.beginPath(); p.arc(x * u, y * u, 1.2 * u, 0, Math.PI * 2); p.fill(); } }
    else if (k === "ablo") { arch(22, 30, "#6A1A1A", "#3A0A0A"); p.fillStyle = "#4A1010"; p.beginPath(); p.moveTo(18 * u, 30 * u); p.lineTo(32 * u, 4 * u); p.lineTo(46 * u, 30 * u); p.closePath(); p.fill(); p.strokeStyle = "#C04030"; p.lineWidth = u; p.stroke(); }
    else if (k === "glyph") { arch(22, 26, "#0A140C", "#40F070"); p.fillStyle = "#40F070"; p.font = `${3.6 * u}px monospace`; p.textAlign = "center"; for (let i = 0; i < 16; i++) p.fillText("@#.>$!?g"[i % 8], (i % 2 ? 51 : 13) * u, (28 + Math.floor(i / 2) * 4.5) * u); }
    // the swirl, its colour, with the far side in it
    const cx = 32 * u, cy = 42 * u, r = 15 * u; const g = p.createRadialGradient(cx, cy, 2, cx, cy, r * 1.15); g.addColorStop(0, "rgba(255,255,255,0.9)"); g.addColorStop(0.5, col); g.addColorStop(1, "rgba(0,0,0,0.6)");
    p.fillStyle = g; p.beginPath(); p.ellipse(cx, cy, r * 0.82, r * 1.15, 0, 0, Math.PI * 2); p.fill(); glimpse(p, k, cx, cy, r, night);
    p.strokeStyle = "rgba(255,255,255,0.45)"; p.lineWidth = u; for (let i = 0; i < 3; i++) { p.beginPath(); p.ellipse(cx, cy, r * (0.55 + i * 0.12), r * (0.8 + i * 0.13), 0, i, i + 4); p.stroke(); }
    // the badge: one figure, or four
    const solo = PL.WHO[k][0], fig = (x) => { p.beginPath(); p.arc(x * u, 3.5 * u, 1.3 * u, 0, Math.PI * 2); p.fill(); p.fillRect((x - 1.1) * u, 5 * u, 2.2 * u, 3 * u); };
    p.fillStyle = "rgba(20,16,10,0.85)"; p.fillRect((solo ? 28 : 22) * u, 0.5 * u, (solo ? 8 : 20) * u, 9 * u); p.fillStyle = "#F0D070"; if (solo) fig(32); else for (const x of [25, 29.7, 34.3, 39]) fig(x); return c; };
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); for (const k of KEYS) for (const n of [0, 1]) { set.index[`portal:${k}:${n}`] = set.layers.length; set.layers.push(CM.art.portalFor(set.size, k, n)); } return set; }; }
  // which picture a portal thing wears
  CM.portalLook = (game, key, thing) => { if (!thing || thing.type !== "portal") return null; const fl = game.floor, [x, y] = key.split(",").map(Number); let k = null;
    if (fl.number === 0) { const P = PC.portalAt(x, y); k = P && P[0]; } else if (fl.number === -1 && thing.to === "town") k = PL.twinAt(x, y);
    if (!k || !KEYS.includes(k)) return null; return `portal:${k}:${CM.isNight && CM.isNight(game) ? 1 : 0}`; };
  // the hint line, at a portal
  { const rf0 = CM.UI.prototype.refresh; CM.UI.prototype.refresh = function (...a) { const out = rf0.apply(this, a), g = this.game, fl = g && g.floor; if (fl && g.mode === "explore" && !g.travel) { const w = PL.words(g, fl.pos[0], fl.pos[1]), hint = this.$("#view .hint"); if (w && hint) hint.textContent = w; } return out; }; }
  // the crossing: a swirl of the portal's colour over the view, and its note; near a portal, its hum
  const flash = (ui, k) => { const col = (PC.byKey[k] || [, , , "#80C0FF"])[3], v = ui.$("#view"); if (!v) return; const d = document.createElement("div"); d.className = "portalfx"; d.style.setProperty("--pc", col); v.appendChild(d); setTimeout(() => d.remove(), 1100);
    try { CM.audio.play("teleport", 0.5, 0, NOTE[k] || 1); } catch (e) { /* quiet */ } };
  CM.UI.prototype.portalFx = function (k) { flash(this, k); };
  { const rf0 = CM.UI.prototype.refresh; let lastHum = ""; CM.UI.prototype.refresh = function (...a) { const out = rf0.apply(this, a), g = this.game, fl = g && g.floor; if (!fl || g.mode !== "explore") return out;
      const near = [[0, 0], [0, -1], [1, 0], [0, 1], [-1, 0]].map(([dx, dy]) => [fl.pos[0] + dx, fl.pos[1] + dy]).map(([x, y]) => (fl.number === 0 ? (PC.portalAt(x, y) || [])[0] : fl.number === -1 ? PL.twinAt(x, y) : null)).find(Boolean);
      const key = near ? `${fl.number}:${fl.pos.join(",")}:${near}` : ""; if (near && key !== lastHum) { try { CM.audio.play("spell", 0.12, 0, (NOTE[near] || 1) * 0.6); } catch (e) { /* quiet */ } } lastHum = key; return out; }; }
}
