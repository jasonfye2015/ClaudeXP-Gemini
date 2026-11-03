"use strict";
// Wall variety (v48.2, UPGRADE_PLAN_43.md): the photographed walls no longer repeat square after square - each wall
// square is mirrored or not by a hash and a little lighter or darker (26-surface.js) - and two marks more are laid
// over them in every band: a patched stone, a newer block mortared in paler than the rest, and a stain, a dark run down
// from above where water or worse has come through. With the cracks, the moss, the damp and the soot as before.
{ const S = 128, cv = () => { const c = document.createElement("canvas"); c.width = c.height = S; return c; };
  const PAINT = {
    "decal:patch": (p) => { p.fillStyle = "#B8AC94"; p.fillRect(30, 46, 52, 30); p.fillStyle = "#C8BCA4"; p.fillRect(30, 46, 52, 5); p.strokeStyle = "#5A5040"; p.lineWidth = 4; p.strokeRect(30, 46, 52, 30); p.fillStyle = "#A89C84"; p.fillRect(82, 52, 22, 24); p.strokeRect(82, 52, 22, 24); },
    "decal:stain": (p) => { p.fillStyle = "#2A2418"; p.beginPath(); p.moveTo(44, 0); p.lineTo(84, 0); p.bezierCurveTo(80, 40, 74, 70, 70, 110); p.quadraticCurveTo(64, 126, 58, 110); p.bezierCurveTo(54, 70, 48, 40, 44, 0); p.fill(); p.fillStyle = "#3A3222"; p.fillRect(56, 0, 14, 60); } };
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); for (const [n, f] of Object.entries(PAINT)) { if (set.index[n] !== undefined) continue; const c = cv(); f(c.getContext("2d")); set.index[n] = set.layers.length; set.layers.push(c); } return set; }; }
  // laid after each band's own (their thresholds run on: a band's marks first, these in the next tenth)
  for (const [band, list] of Object.entries(CM.WALL_DECALS || {})) { const top = list.length ? list[list.length - 1][1] : 0; if (!list.some(([id]) => id === "patch")) list.push(["patch", top + 0.05], ["stain", top + 0.1]); void band; }
}
