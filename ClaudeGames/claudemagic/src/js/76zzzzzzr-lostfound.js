"use strict";
// Lost and found - the window's side (v37.3): the lost party's pack drawn where it lies - a dusty pack, a sword-hilt and
// a helm beside it. Rules: 69zz-lostfound.js.
{ const S = 256;
  const paint = (p) => { p.fillStyle = "rgba(0,0,0,0.3)"; p.beginPath(); p.ellipse(128, 240, 100, 12, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = "#6A5A40"; p.beginPath(); p.ellipse(110, 190, 70, 52, -0.2, 0, Math.PI * 2); p.fill(); p.fillStyle = "#4A3A26"; p.fillRect(80, 160, 60, 10); p.fillStyle = "#C8A040"; p.fillRect(102, 156, 14, 18);
    p.fillStyle = "#9AA0A8"; p.beginPath(); p.arc(196, 200, 30, Math.PI, 0); p.fill(); p.fillRect(166, 198, 60, 8); p.strokeStyle = "#7A7A80"; p.lineWidth = 8; p.beginPath(); p.moveTo(40, 230); p.lineTo(200, 120); p.stroke(); p.fillStyle = "#5A3A1E"; p.fillRect(196, 104, 20, 20);
    p.fillStyle = "rgba(200,190,170,0.35)"; for (let i = 0; i < 40; i++) p.fillRect((i * 53) % 220 + 18, (i * 37) % 110 + 130, 3, 3); };
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look), cv = document.createElement("canvas"); cv.width = cv.height = S; paint(cv.getContext("2d")); set.index["lost:pack"] = set.layers.length; set.layers.push(cv); return set; }; }
  CM.thingSprites = Object.assign(CM.thingSprites || {}, { lostpack: (t, x, y) => [{ x, y, layer: "lost:pack", w: 0.75, h: 0.5 }] });
}
