"use strict";
// Buildings with depth, painted (v53.0 on, UPGRADE_PLAN_48.md): the pictures 26b-buildings.js builds the town's windows,
// doors and timbers from - weathered timber with its grain.
{ const S = 128;
  const PAINT = {
    "solid:sill": (p) => { p.fillStyle = "#8C8272"; p.fillRect(0, 0, S, S); const r = new CM.Random(31); for (let i = 0; i < 300; i++) { const g = Math.floor(r.next() * 40) - 20; p.fillStyle = `rgba(${140 + g},${132 + g},${118 + g},0.5)`; p.fillRect(r.next() * S, r.next() * S, 2, 2); } p.fillStyle = "rgba(255,250,235,0.12)"; p.fillRect(0, 0, S, 10); },
    "solid:timber": (p) => { p.fillStyle = "#5A4028"; p.fillRect(0, 0, S, S); const r = new CM.Random(77); for (let i = 0; i < 40; i++) { p.fillStyle = r.next() < 0.5 ? "rgba(30,20,10,0.35)" : "rgba(140,105,70,0.25)"; p.fillRect(0, r.next() * S, S, 1 + r.next() * 2); }
      p.fillStyle = "rgba(255,230,190,0.08)"; p.fillRect(0, 0, S, 6); } };
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); for (const [n, f] of Object.entries(PAINT)) { if (set.index[n] !== undefined) continue; const c = document.createElement("canvas"); c.width = c.height = S; f(c.getContext("2d")); set.index[n] = set.layers.length; set.layers.push(c); } return set; }; }
  CM.BUILDING_PAINT = PAINT;
}
