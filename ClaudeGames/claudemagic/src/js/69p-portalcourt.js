"use strict";
// The Portal Court (v21.0, UPGRADE_PLAN_16.md): the Keep-yard's walls pushed out to make room, and its portals laid
// round the shaft by kind - the Wood's portals on the north and south walls, the world gates (one hero, another world)
// on the east - with the middle rows clear from the opening on Shaft Lane to the shaft and to every portal. Each portal
// has a name stone at its foot, a brazier either side burning in its colour and a ring of runes on the floor before it
// (drawn by 76zzzq-portalcourt.js). The postern moves to the new north-east corner.
{ const PC = CM.PORTALCOURT = {};
  CM.TOWN_YARD = [32, 15, 40, 25];
  CM.TOWN_POSTERN = [39, 16];
  // [key in CM.PORTAL_YARD, the square, the name on its stone, its colour, "wood" or "world"]
  PC.PORTALS = [
    ["tower", [34, 16], "The Mage Tower", "#A070FF", "wood"], ["cabin", [36, 16], "Leshy's Cabin", "#60C060", "wood"], ["claudeita", [38, 16], "Claudeita's Cave", "#E0B060", "wood"],
    ["fortress", [34, 24], "The Fortress", "#9098A8", "wood"], ["glyph", [36, 24], "The Glyph Deep", "#40F070", "wood"],
    ["ablo", [39, 18], "Haven (Claudeablo)", "#F04040", "world"], ["gate", [39, 22], "The Neather Gate", "#9060E0", "world"],
  ];
  PC.byKey = Object.fromEntries(PC.PORTALS.map((p) => [p[0], p]));
  PC.TO = { tower: "magetower", cabin: "cabin", claudeita: "claudeita", fortress: "fortress", glyph: "glyph", ablo: "claudeablo", gate: "claudecraft" };
  PC.keyOfTo = Object.fromEntries(Object.entries(PC.TO).map(([k, v]) => [v, k]));
  for (const [k, at] of PC.PORTALS) CM.PORTAL_YARD[k] = at.slice();
  CM.PORTAL_YARD.plinths = [];
  // the court's other things (the waystone, the noticeboard and the warden come in later updates, but have their places)
  PC.WAYSTONE = [33, 18]; PC.BOARD = [33, 23]; PC.WARDEN = [37, 20];
  // the court laid on the town: the old yard's portals and plinths cleared, every portal in its place
  CM.layPortalYard = function (fl) { const key = (x, y) => `${x},${y}`, [x0, y0, x1, y1] = CM.TOWN_YARD;
    for (const [k, t] of Object.entries(fl.things)) { const [x, y] = k.split(",").map(Number); if (x > x0 && x < x1 && y > y0 && y < y1 && (t.type === "portal" || t.type === "plinth")) delete fl.things[k]; }
    for (const [k, at] of PC.PORTALS) fl.things[key(...at)] = { type: "portal", to: PC.TO[k] };
    return fl; };
  // the court by name, and the portal a square belongs to
  PC.portalAt = (x, y) => PC.PORTALS.find(([, at]) => at[0] === x && at[1] === y) || null;
  { const tp0 = CM.townPlace; CM.townPlace = function (fl, x, y) { const out = tp0.call(this, fl, x, y), P = fl && fl.number === 0 && PC.portalAt(x, y); return P ? `the Portal Court - ${P[2]}` : out; }; }
  // home from a portal in the Wood: to its own twin in the court (the old rule found the cabin's, the cave's and the
  // Fortress's by their squares; the Mage Tower's and the Glyph Deep's are found the same way)
  { const G = CM.Game.prototype, up0 = G.usePortal; G.usePortal = function (t) { const fl = this.floor;
      if (t && t.to === "town" && fl && fl.number === -1) { const near = (q) => q && Math.abs(fl.pos[0] - q[0]) + Math.abs(fl.pos[1] - q[1]) <= 1;
        const from = near(CM.CABIN && CM.CABIN.portal) ? "cabin" : near(CM.CLAUDEITA && CM.CLAUDEITA.portal) ? "claudeita" : near(CM.FORTRESS && CM.FORTRESS.portal) ? "fortress" : near(CM.GLYPH_PORTAL) ? "glyph" : "tower";
        this.sound && this.sound("spell"); this.enterFloor(0, "rope", CM.PORTAL_YARD[from].slice()); this.floor.facing = 2; this.say(`Light, and the Portal Court: ${PC.byKey[from][2]}'s portal, by the shaft.`); this.emit && this.emit("portalfx", from); return true; }
      return up0.call(this, t); }; }
}
