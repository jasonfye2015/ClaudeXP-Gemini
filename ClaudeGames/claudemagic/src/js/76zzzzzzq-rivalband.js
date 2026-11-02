"use strict";
// The rival party - the window's side (v37.2): the band's chalk on a wall, the thing they dropped (a small bundle), one
// of theirs fallen (bones in a coat of the band's colour); and the band named in the side panel once met or marked.
// Rules: 69zy-rivalband.js.
{ const S = 256, cv = () => { const c = document.createElement("canvas"); c.width = c.height = S; return c; };
  const PAINT = {
    "rb:chalk": (p) => { p.strokeStyle = "rgba(240,240,230,0.85)"; p.lineWidth = 6; p.lineCap = "round"; p.beginPath(); p.moveTo(40, 120); p.lineTo(200, 120); p.lineTo(170, 90); p.moveTo(200, 120); p.lineTo(170, 150); p.stroke();
      p.lineWidth = 4; for (let i = 0; i < 7; i++) { p.beginPath(); p.moveTo(50 + i * 22, 170); p.lineTo(56 + i * 22, 210); p.stroke(); } p.beginPath(); p.moveTo(46, 196); p.lineTo(200, 182); p.stroke(); p.beginPath(); p.arc(120, 56, 26, 0, Math.PI * 2); p.moveTo(102, 38); p.lineTo(138, 74); p.moveTo(138, 38); p.lineTo(102, 74); p.stroke(); },   /* (the band's sign: a crossed ring) */
    "rb:bundle": (p) => { p.fillStyle = "rgba(0,0,0,0.3)"; p.beginPath(); p.ellipse(128, 240, 70, 10, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = "#8A6A40"; p.beginPath(); p.ellipse(128, 190, 70, 50, 0, 0, Math.PI * 2); p.fill(); p.strokeStyle = "#5A3A1E"; p.lineWidth = 6; p.beginPath(); p.moveTo(128, 140); p.lineTo(128, 240); p.moveTo(60, 190); p.lineTo(196, 190); p.stroke(); },
    "rb:dead": (p) => { p.fillStyle = "#7A2A20"; p.beginPath(); p.ellipse(128, 150, 90, 50, 0.2, 0, Math.PI * 2); p.fill(); p.fillStyle = "#E8DCC0"; p.beginPath(); p.arc(60, 110, 26, 0, Math.PI * 2); p.fill(); p.fillStyle = "#3A2A1A"; p.fillRect(48, 102, 8, 8); p.fillRect(64, 102, 8, 8);
      p.strokeStyle = "#E8DCC0"; p.lineWidth = 9; p.lineCap = "round"; for (const [x1, y1, x2, y2] of [[170, 120, 220, 90], [180, 170, 230, 200], [90, 190, 60, 230]]) { p.beginPath(); p.moveTo(x1, y1); p.lineTo(x2, y2); p.stroke(); } },
  };
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); for (const [n, f] of Object.entries(PAINT)) { const c = cv(); f(c.getContext("2d")); set.index[n] = set.layers.length; set.layers.push(c); } return set; }; }
  CM.thingSprites = Object.assign(CM.thingSprites || {}, { chalk: (t, x, y) => [{ x, y, face: t.face, layer: "rb:chalk", w: 0.8, h: 0.8, lift: 0.1 }], dropped: (t, x, y) => [{ x, y, layer: "rb:bundle", w: 0.45, h: 0.35 }], rivaldead: (t, x, y) => [{ x, y, layer: "rb:dead", w: 0.9, flat: true }] });
}
