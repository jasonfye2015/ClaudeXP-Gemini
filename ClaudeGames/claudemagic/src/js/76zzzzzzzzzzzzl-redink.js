"use strict";
// Red ink - the window's side (UPGRADE_PLAN_71.md, release 4): the little pot under the desk's edge, a red gleam in
// it; and a red-ink run's row in the Hall of Fame marked in red. Rules: 69zzzs-redink.js.
{ const S = 128;
  const pot = (p) => { p.fillStyle = "rgba(0,0,0,0.3)"; p.beginPath(); p.ellipse(64, 118, 30, 6, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = "#3A2A22"; p.beginPath(); p.moveTo(38, 116); p.lineTo(42, 76); p.lineTo(86, 76); p.lineTo(90, 116); p.closePath(); p.fill();
    p.fillStyle = "#5A4234"; p.fillRect(40, 70, 48, 8); p.fillStyle = "#8A1414"; p.beginPath(); p.ellipse(64, 72, 20, 4, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = "rgba(255,120,120,0.7)"; p.fillRect(56, 70, 6, 2);
    p.strokeStyle = "#D8D0C0"; p.lineWidth = 2; p.beginPath(); p.moveTo(70, 72); p.lineTo(98, 18); p.stroke(); p.fillStyle = "#E8E0D0"; p.beginPath(); p.ellipse(96, 26, 5, 16, 0.5, 0, Math.PI * 2); p.fill(); };
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look), cv = document.createElement("canvas"); cv.width = cv.height = S; pot(cv.getContext("2d")); set.index["redink:pot"] = set.layers.length; set.layers.push(cv); return set; }; }
  CM.thingSprites = Object.assign(CM.thingSprites || {}, { redink: (t, x, y) => [{ x, y, layer: "redink:pot", w: 0.26, h: 0.26, dz: -0.3 }] });
}
