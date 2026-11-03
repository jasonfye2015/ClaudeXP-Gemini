"use strict";
// Trim (v48.3, UPGRADE_PLAN_43.md): the dungeon's walls stand on a course of dressed skirting stones, a hand's height,
// set a little proud of the wall so the torch catches their top; and every doorway and gate has a stone lintel across
// its head under the ceiling (26-surface.js lays them; this paints their stone).
{ const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); if (set.index["trim:stone"] !== undefined) return set; const c = document.createElement("canvas"); c.width = c.height = 128; const p = c.getContext("2d");
    p.fillStyle = "#7A6E5E"; p.fillRect(0, 0, 128, 128); p.fillStyle = "#8C806E"; for (let y = 0; y < 128; y += 32) for (let x = (y / 32) % 2 ? -24 : 0; x < 128; x += 48) p.fillRect(x + 2, y + 2, 44, 28);
    p.fillStyle = "rgba(0,0,0,0.18)"; for (let y = 0; y < 128; y += 32) p.fillRect(0, y + 26, 128, 6); p.fillStyle = "rgba(255,255,255,0.08)"; for (let y = 0; y < 128; y += 32) p.fillRect(0, y + 2, 128, 4);
    set.index["trim:stone"] = set.layers.length; set.layers.push(c); return set; }; }
