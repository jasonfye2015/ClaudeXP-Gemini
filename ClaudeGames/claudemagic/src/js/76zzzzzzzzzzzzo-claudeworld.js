"use strict";
// The world around Claude - the window's side (UPGRADE_PLAN_72.md, release 2): the memorial wall at the shaft's head, a
// grey slab cut with rows of small names; the note on his desk when he's out; and at a festival something of it by the
// cabin's door - a wreath of greenery, a string of lanterns, a candle. Rules: 69zzzv-claudeworld.js.
{ const S = 256, mk = (f) => { const c = document.createElement("canvas"); c.width = c.height = S; f(c.getContext("2d")); return c; };
  const wall = (p) => { p.fillStyle = "rgba(0,0,0,0.3)"; p.beginPath(); p.ellipse(128, 246, 110, 10, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = "#6E6A64"; p.beginPath(); p.moveTo(28, 246); p.lineTo(34, 40); p.quadraticCurveTo(128, 6, 222, 40); p.lineTo(228, 246); p.closePath(); p.fill();
    p.fillStyle = "#86827A"; p.fillRect(40, 50, 8, 190); p.fillStyle = "rgba(30,28,26,0.75)"; for (let r = 0; r < 14; r++) for (let c = 0; c < 3; c++) { const w = 30 + ((r * 7 + c * 13) % 22); p.fillRect(56 + c * 56, 62 + r * 12, w, 3); }
    p.fillStyle = "#4A4640"; p.fillRect(20, 236, 216, 12); };
  const note = (p) => { p.save(); p.translate(128, 200); p.rotate(-0.12); p.fillStyle = "rgba(0,0,0,0.25)"; p.fillRect(-58, -38, 120, 84); p.fillStyle = "#EDE4CC"; p.fillRect(-62, -44, 120, 84); p.fillStyle = "rgba(50,34,20,0.7)"; for (let i = 0; i < 7; i++) p.fillRect(-52, -32 + i * 10, i === 6 ? 30 : 96, 2); p.restore();
    p.fillStyle = "#1A1A2A"; p.beginPath(); p.arc(186, 160, 16, 0, Math.PI * 2); p.fill(); };
  const deco = (p) => { p.strokeStyle = "#3A6A2E"; p.lineWidth = 16; p.beginPath(); p.arc(128, 120, 64, 0, Math.PI * 2); p.stroke(); p.fillStyle = "#B0302A"; for (let i = 0; i < 8; i++) { const a = i * Math.PI / 4; p.beginPath(); p.arc(128 + Math.cos(a) * 64, 120 + Math.sin(a) * 64, 7, 0, Math.PI * 2); p.fill(); }
    p.fillStyle = "#E8D8A0"; p.fillRect(118, 200, 20, 40); const g = p.createRadialGradient(128, 194, 1, 128, 194, 30); g.addColorStop(0, "rgba(255,210,120,0.9)"); g.addColorStop(1, "rgba(255,160,60,0)"); p.fillStyle = g; p.fillRect(96, 164, 64, 60); };
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); for (const [n, f] of [["claude:memwall", wall], ["claude:note", note], ["claude:deco", deco]]) { set.index[n] = set.layers.length; set.layers.push(mk(f)); } return set; }; }
  CM.thingSprites = Object.assign(CM.thingSprites || {}, {
    memorialwall: (t, x, y) => [{ x, y, layer: "claude:memwall", w: 0.95, h: 1.1 }],
    claudenote: (t, x, y) => [{ x, y, layer: "claude:note", w: 0.4, h: 0.3, dz: -0.55, lift: 0.42 }],
    festdeco: (t, x, y, now) => [{ x, y, layer: "claude:deco", w: 0.5, h: 0.55, glow: 0.2 + 0.08 * Math.sin(now / 500) }],
  });
}
