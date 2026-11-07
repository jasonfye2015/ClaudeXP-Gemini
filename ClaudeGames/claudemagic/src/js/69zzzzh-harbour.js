"use strict";
// The harbour (UPGRADE_PLAN_80.md, v130.0), the rules' side: the pier, the dock and the Harbour Road by name, safe to
// walk at any hour, on the Where-to list once seen; and the portal pair - one on the dock, one in the town's Square -
// each taking the party to the other. The land of it is 23g-harbour.js's, the sight of it 77u-harbour.js's.
//   CM.TOWN_DOCK_PORTAL
{ const H = CM.HARBOUR, P = CM.Game.prototype, key = (x, y) => `${x},${y}`;
  CM.TOWN_DOCK_PORTAL = [17, 23];   // (a corner of the Square, off every way through it)
  { const mt0 = CM.makeTown; CM.makeTown = function (...a) { const fl = mt0.apply(this, a); if (fl && fl.grid[CM.TOWN_DOCK_PORTAL[1]][CM.TOWN_DOCK_PORTAL[0]] === 0 && !fl.things[key(...CM.TOWN_DOCK_PORTAL)]) fl.things[key(...CM.TOWN_DOCK_PORTAL)] = { type: "portal", to: "dock" }; return fl; }; }
  const onDock = (fl) => fl && fl.number === -1 && Math.abs(fl.pos[0] - H.portal[0]) + Math.abs(fl.pos[1] - H.portal[1]) <= 1;
  { const up0 = P.usePortal; P.usePortal = function (t) {
      if (t && t.to === "dock") { this.sound && this.sound("spell"); this.enterFloor(-1, "rope", [H.portal[0] + 1, H.portal[1]]); this.floor.facing = 2; this.say("Sea-green light, and the smell of salt: the dock at the end of the pier, gulls on the piles, and the sea all round."); this.emit && this.emit("portalfx", "dock"); return true; }
      if (t && t.to === "town" && onDock(this.floor)) { this.sound && this.sound("spell"); this.enterFloor(0, "rope", [CM.TOWN_DOCK_PORTAL[0] + 1, CM.TOWN_DOCK_PORTAL[1]]); this.floor.facing = 3; this.say("Light, and the Square: the well, the market, the town about you, and the sea's portal at your back."); this.emit && this.emit("portalfx", "dock"); return true; }
      return up0.call(this, t); }; }
  // names
  const place = (fl, x, y) => { if (!fl || fl.number !== -1 || fl.grid.length <= H.head[3]) return null; const [x0, y0, x1, y1] = H.head;
    if (x >= x0 && x <= x1 && y >= y0 && y <= y1) return "the dock"; if (CM.isPier(x, y)) return "the pier"; if (x === H.road.x && y === H.bridge[1]) return "the stream bridge"; return null; };
  { const wp0 = CM.woodPlace; CM.woodPlace = function (fl, x, y) { const own = place(fl, x, y); if (own) return own; const was = wp0.call(this, fl, x, y);
    return fl && fl.number === -1 && x === H.road.x && y >= H.road.from && y <= H.road.to && ["the Deep Wood", "the river's bank", "The Fields"].includes(was) ? "the Harbour Road" : was; }; }   // (the road's name where nothing else is named)
  { const ws0 = CM.woodSafe; CM.woodSafe = function (fl, x, y) { return ["the dock", "the pier"].includes(place(fl, x, y)) || ws0.call(this, fl, x, y); }; }
  { const wy0 = CM.wayPlaces; CM.wayPlaces = function (game) { const out = wy0(game), fl = game.floor; if (!fl || fl.number > 0) return out;
      if (fl.number === 0) { if (!(fl.pos[0] === CM.TOWN_DOCK_PORTAL[0] + 1 && fl.pos[1] === CM.TOWN_DOCK_PORTAL[1])) { const at = [CM.TOWN_DOCK_PORTAL[0] + 1, CM.TOWN_DOCK_PORTAL[1]], p = game.pathTo(...at); out.push({ name: "The sea's portal", x: at[0], y: at[1], steps: p ? p.length : null }); } return out; }
      if (fl.number !== -1 || fl.grid.length <= H.head[3]) return out; const at = [H.portal[0] + 1, H.portal[1]];
      if ((fl.seen || []).some(([x, y]) => x === at[0] && y === at[1]) && !(fl.pos[0] === at[0] && fl.pos[1] === at[1])) { const p = game.pathTo(...at); out.push({ name: "The dock", x: at[0], y: at[1], steps: p ? p.length : null }); }
      return out; }; }
  // what the dock and the pier say
  const DOCK = ["The dock: broad planks, bleached and salt-stiff, iron rings for mooring along its edge, and the sea slapping under it. No boat lies here yet.", "Gulls on the piles, a coil of old rope, a bollard worn smooth. Somebody built this dock for ships that never came - or haven't come yet."];
  { const u0 = P.use; P.use = function (...a) { const fl = this.floor; if (this.mode === "explore" && fl && fl.number === -1 && place(fl, ...fl.pos) === "the dock" && !fl.things[key(...fl.pos)]) { this.say(CM.dockWords ? CM.dockWords(this) : DOCK[(CM.dayOf ? CM.dayOf(this) : 0) % DOCK.length]); return true; } return u0.apply(this, a); }; }
}
