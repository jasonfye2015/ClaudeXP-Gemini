"use strict";
// The Margins - the window's side (UPGRADE_PLAN_70.md, release 2): a loose page on the dungeon floor, a pebble on it;
// the map wall in Claude's cabin, a board that fills with pinned pages and the red string between them as they come
// home; a page in the pack drawn as a scroll. Rules: 69zzzn-margins.js.
{ const S = 256;
  const page = (p, x, y, w, h, tilt) => { p.save(); p.translate(x, y); p.rotate(tilt); p.fillStyle = "#E8DFC8"; p.fillRect(-w / 2, -h / 2, w, h); p.fillStyle = "rgba(60,40,20,0.55)";
    for (let i = 0; i < Math.floor(h / 7) - 1; i++) p.fillRect(-w / 2 + 4, -h / 2 + 5 + i * 7, w * (i % 3 === 2 ? 0.5 : 0.8), 1.5); p.restore(); };
  const loose = (p) => { p.fillStyle = "rgba(0,0,0,0.25)"; p.beginPath(); p.ellipse(128, 140, 92, 70, 0, 0, Math.PI * 2); p.fill(); page(p, 128, 128, 150, 190, 0.2);
    p.fillStyle = "#7A746C"; p.beginPath(); p.ellipse(150, 96, 22, 16, 0.3, 0, Math.PI * 2); p.fill(); p.fillStyle = "#9A948A"; p.beginPath(); p.ellipse(146, 91, 12, 7, 0.3, 0, Math.PI * 2); p.fill(); };
  const wall = (n) => (p) => { p.fillStyle = "#6A4A2C"; p.fillRect(14, 30, 228, 190); p.fillStyle = "#B89870"; p.fillRect(22, 38, 212, 174); p.fillStyle = "rgba(90,60,30,0.35)"; for (let i = 0; i < 40; i++) p.fillRect((i * 47) % 200 + 24, (i * 29) % 160 + 40, 3, 3);
    const spots = [[52, 70], [110, 62], [176, 74], [70, 130], [134, 118], [200, 130], [46, 182], [104, 180], [160, 176], [212, 186]], at = spots.slice(0, n);
    p.strokeStyle = "#B0302A"; p.lineWidth = 2; p.beginPath(); at.forEach(([x, y], i) => (i ? p.lineTo(x, y) : p.moveTo(x, y))); p.stroke();
    at.forEach(([x, y], i) => { page(p, x, y, 36, 44, ((i * 37) % 9 - 4) * 0.04); p.fillStyle = "#C03028"; p.beginPath(); p.arc(x, y - 18, 3.5, 0, Math.PI * 2); p.fill(); });
    p.fillStyle = "#4A3220"; p.fillRect(118, 214, 20, 36); };
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look), add = (name, f) => { const cv = document.createElement("canvas"); cv.width = cv.height = S; f(cv.getContext("2d")); set.index[name] = set.layers.length; set.layers.push(cv); };
      add("margin:page", loose); for (let n = 0; n <= 10; n++) add(`margin:wall${n}`, wall(n)); return set; }; }
  CM.thingSprites = Object.assign(CM.thingSprites || {}, {
    margin: (t, x, y) => [{ x, y, layer: "margin:page", w: 0.42, flat: true, shade: 0.9 }],
    mapwall: (t, x, y) => { const g = CM.game, n = g && g.marginsPinned ? g.marginsPinned().length : 0; return [{ x, y, layer: `margin:wall${n}`, face: 0, w: 0.95, h: 0.95, dz: -0.42, lift: 0.25 }]; },
  });
  { const ik0 = CM.art.itemKey; CM.art.itemKey = function (item) { return item && item.kind === "margin" ? "i.scroll" : ik0.call(this, item); }; }
}
