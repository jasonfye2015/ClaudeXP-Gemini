"use strict";
// Puzzle rooms - the window's side (v37.1): the altar, the statues (a stone figure, and a worn arrow on the floor before
// it showing where it looks), the shaft of daylight, the mirrors (on their pins, tilted as they are), the sun-plate; and
// the beam itself, a bar of light along the floor from the shaft to wherever it stops now. Rules: 69zx-puzzles.js.
{ const S = 256, cv = () => { const c = document.createElement("canvas"); c.width = c.height = S; return c; };
  const PAINT = {
    "pz:altar": (p) => { p.fillStyle = "rgba(0,0,0,0.3)"; p.beginPath(); p.ellipse(128, 246, 100, 8, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = "#8A8478"; p.fillRect(40, 130, 176, 116); p.fillStyle = "#A8A296"; p.fillRect(28, 110, 200, 26); p.fillStyle = "#6A645A"; p.fillRect(60, 160, 136, 6); p.fillStyle = "#E8D070"; p.beginPath(); p.arc(128, 96, 12, 0, Math.PI * 2); p.fill(); },
    "pz:statue": (p) => { p.fillStyle = "rgba(0,0,0,0.3)"; p.beginPath(); p.ellipse(128, 248, 70, 7, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = "#8C8880"; p.fillRect(78, 210, 100, 38); p.fillStyle = "#A09C92";
      p.beginPath(); p.moveTo(98, 210); p.lineTo(92, 120); p.quadraticCurveTo(128, 96, 164, 120); p.lineTo(158, 210); p.fill(); p.beginPath(); p.arc(128, 78, 30, 0, Math.PI * 2); p.fill(); p.fillStyle = "#6A665E"; p.fillRect(114, 72, 6, 6); p.fillRect(136, 72, 6, 6); },
    "pz:arrow": (p) => { p.fillStyle = "rgba(200,180,120,0.55)"; p.beginPath(); p.moveTo(128, 20); p.lineTo(200, 120); p.lineTo(150, 120); p.lineTo(150, 230); p.lineTo(106, 230); p.lineTo(106, 120); p.lineTo(56, 120); p.closePath(); p.fill(); },
    "pz:shaft": (p) => { const g = p.createLinearGradient(0, 0, 0, 256); g.addColorStop(0, "rgba(255,250,220,0.9)"); g.addColorStop(1, "rgba(255,230,160,0.25)"); p.fillStyle = g; p.beginPath(); p.moveTo(100, 0); p.lineTo(156, 0); p.lineTo(200, 256); p.lineTo(56, 256); p.closePath(); p.fill();
      p.fillStyle = "rgba(255,255,240,0.8)"; for (let i = 0; i < 20; i++) p.fillRect(80 + ((i * 37) % 100), (i * 53) % 250, 2, 2); },
    "pz:mirror": (p) => { p.fillStyle = "rgba(0,0,0,0.3)"; p.beginPath(); p.ellipse(128, 248, 60, 6, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = "#5A4A3A"; p.fillRect(120, 150, 16, 98); p.fillRect(90, 236, 76, 12);
      p.fillStyle = "#B8963A"; p.beginPath(); p.ellipse(128, 100, 62, 82, 0, 0, Math.PI * 2); p.fill(); const g = p.createLinearGradient(80, 30, 180, 170); g.addColorStop(0, "#E8F0F8"); g.addColorStop(0.5, "#8AA0B8"); g.addColorStop(1, "#D8E4F0"); p.fillStyle = g; p.beginPath(); p.ellipse(128, 100, 52, 72, 0, 0, Math.PI * 2); p.fill(); },
    "pz:plate": (p) => { const g = p.createRadialGradient(128, 128, 10, 128, 128, 110); g.addColorStop(0, "#F0D070"); g.addColorStop(1, "#8A6A20"); p.fillStyle = g; p.beginPath(); p.arc(128, 128, 104, 0, Math.PI * 2); p.fill(); p.strokeStyle = "#6A4A10"; p.lineWidth = 6;
      for (let i = 0; i < 12; i++) { const a = i * Math.PI / 6; p.beginPath(); p.moveTo(128 + Math.cos(a) * 50, 128 + Math.sin(a) * 50); p.lineTo(128 + Math.cos(a) * 92, 128 + Math.sin(a) * 92); p.stroke(); } p.beginPath(); p.arc(128, 128, 40, 0, Math.PI * 2); p.stroke(); },
    "pz:beam": (p) => { const g = p.createLinearGradient(0, 0, 256, 0); g.addColorStop(0, "rgba(255,240,180,0)"); g.addColorStop(0.35, "rgba(255,245,200,0.85)"); g.addColorStop(0.5, "rgba(255,255,235,1)"); g.addColorStop(0.65, "rgba(255,245,200,0.85)"); g.addColorStop(1, "rgba(255,240,180,0)"); p.fillStyle = g; p.fillRect(0, 0, 256, 256); },
  };
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); for (const [n, f] of Object.entries(PAINT)) { const c = cv(); f(c.getContext("2d")); set.index[n] = set.layers.length; set.layers.push(c); } return set; }; }
  const rot = (f) => [Math.PI, -Math.PI / 2, 0, Math.PI / 2][f];   // (a flat sprite's spin: its picture's top toward the facing)
  CM.thingSprites = Object.assign(CM.thingSprites || {}, {
    altar: (t, x, y) => [{ x, y, layer: "pz:altar", w: 0.8, h: 0.6 }],
    statue: (t, x, y) => [{ x, y, layer: "pz:statue", w: 0.6, h: 0.95 }, { x, y, layer: "pz:arrow", w: 0.6, flat: true, spin: rot(t.face), glow: 0.001 }],
    sunshaft: (t, x, y) => [{ x, y, layer: "pz:shaft", w: 0.7, h: 1.0, glow: 1.5, alpha: 0.8 }],
    mirror: (t, x, y) => [{ x, y, layer: "pz:mirror", w: 0.55, h: 0.8, mirror: t.tilt === "\\" }],
    sunplate: (t, x, y) => [{ x, y, layer: "pz:plate", w: 0.7, flat: true, glow: 0.4 }],
  });
  { const ls0 = CM.lifeSprites; CM.lifeSprites = (game, fl, now) => { const out = ls0 ? ls0(game, fl, now) : []; if (!fl || !fl.puzzle || fl.puzzle.kind !== "beam" || !CM.renderer || CM.renderer.index["pz:beam"] === undefined) return out;
      for (const [x, y, d] of CM.beamOf(fl).cells) out.push({ x, y, layer: "pz:beam", w: 1.0, flat: true, spin: d === 0 || d === 2 ? Math.PI / 2 : 0, glow: 1.2, alpha: 0.6 + 0.15 * Math.sin(now / 300) }); return out; }; }
  { const xl0 = CM.extraLights; CM.extraLights = (game, fl, out, r) => { if (xl0) xl0(game, fl, out, r); if (!fl || !fl.puzzle || fl.puzzle.kind !== "beam") return; const B = CM.beamOf(fl).cells, end = B[B.length - 1];
      for (const [k, t] of Object.entries(fl.things)) if (t.type === "sunshaft") { const [x, y] = k.split(",").map(Number); out.push({ x: x + 0.5, y: 0.9, z: y + 0.5, reach: 3, colour: [1.0, 0.95, 0.75], flicker: false, d: Math.abs(x - fl.pos[0]) + Math.abs(y - fl.pos[1]) }); }
      if (end) out.push({ x: end[0] + 0.5, y: 0.3, z: end[1] + 0.5, reach: 2, colour: [0.9, 0.85, 0.6], flicker: false, d: Math.abs(end[0] - fl.pos[0]) + Math.abs(end[1] - fl.pos[1]) }); }; }
}
