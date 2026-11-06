"use strict";
// The Last Page - the window's side (UPGRADE_PLAN_71.md, release 5): the new shelf in Claude's cabin, empty and dusted
// until the first edition stands on it, bound in green. Rules: 69zzzt-lastpage.js.
{ const S = 128;
  const shelf = (full) => (p) => { p.fillStyle = "#4A3220"; p.fillRect(14, 96, 100, 8); p.fillStyle = "#3A2414"; p.fillRect(20, 104, 6, 18); p.fillRect(102, 104, 6, 18);
    if (full) { p.fillStyle = "#2E5A34"; p.fillRect(46, 50, 30, 46); p.fillStyle = "#3E7444"; p.fillRect(46, 50, 5, 46); p.fillStyle = "#D8B860"; p.fillRect(54, 60, 16, 2); p.fillRect(54, 84, 16, 2); p.fillStyle = "#E8DFC8"; p.fillRect(76, 54, 3, 40); } };
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); for (const [n, f] of [["edition:empty", shelf(false)], ["edition:full", shelf(true)]]) { const cv = document.createElement("canvas"); cv.width = cv.height = S; f(cv.getContext("2d")); set.index[n] = set.layers.length; set.layers.push(cv); } return set; }; }
  CM.thingSprites = Object.assign(CM.thingSprites || {}, { firstedition: (t, x, y) => { const g = CM.game, full = Boolean(g && g.village && g.village.ext && g.village.ext.claude && g.village.ext.claude.edition === 2); return [{ x, y, layer: full ? "edition:full" : "edition:empty", w: 0.5, h: 0.5, lift: 0.35, dx: 0.4 }]; } });
}
