"use strict";
// The Scarp (UPGRADE_PLAN_79.md), the rules' side: its ground and its tors, its names, its places on the Where-to list,
// and what the spring, the Lookout's cairn and the falls say. The land of it is 23e-scarp.js's; the sight and the sound
// of it the window's (77s-scarp.js).
CM.GROUNDS.push(...["heath", "rock", "sand"].filter((g) => !CM.GROUNDS.includes(g)));   // (the heath's heather and its bare rock; the sand is the shore's)
CM.SOLID.scarp = { face: "solid:scarp", h: CM.SCARP.h, top: "ground:heath" };                 // the rock round the heath: layered stone, the heather at its lip
CM.SOLID.tor = { face: "solid:crag", h: CM.SCARP.h + 1.15, top: "ground:grass" };      // a tor standing on the heath: its foot is under the heath, its head well over it
if (CM.SOLID_COLOURS) { CM.SOLID_COLOURS.tor = "#7A7468"; CM.SOLID_COLOURS.scarp = "#8A8272"; }
// the Scarp, the stair and the falls by name; the falls and the Lookout on the Where-to list once seen
{ const mw0 = CM.makeWood; CM.makeWood = function (seed) { const fl = mw0.call(this, seed), S = CM.SCARP; if (fl && fl.levels && !fl.rooms.some((r) => r.name === "The Scarp"))
    fl.rooms = [{ x0: S.pool[0] - 3, y0: S.pool[1] - 1, x1: S.pool[2], y1: S.pool[3] + 1, name: "The Falls" }, { x0: S.x0, y0: S.y0, x1: S.x1, y1: S.y1, name: "The Scarp" }].concat(fl.rooms); return fl; }; }
{ const wp0 = CM.woodPlace; CM.woodPlace = function (fl, x, y) { if (fl && fl.number === -1 && fl.levels) { const S = CM.SCARP;
      if (y === S.stair.y && x >= S.stair.x0 && x <= S.stair.x1) return "the Scarp stair"; if (x === S.lookout[0] && y === S.lookout[1]) return "the Lookout"; if (x === S.foot[0] && (y === S.foot[1] || y === S.foot[1] + 1)) return "the foot of the Scarp"; }
    return wp0.call(this, fl, x, y); }; }
{ const wy0 = CM.wayPlaces; CM.wayPlaces = function (game) { const out = wy0(game), fl = game.floor; if (!fl || fl.number !== -1 || !fl.levels) return out; const S = CM.SCARP, seen = new Set((fl.seen || []).map(([x, y]) => `${x},${y}`));
    for (const [name, at] of [["The Scarp stair", S.foot], ["The falls", S.bank[1]], ["The Lookout", S.lookout], ["The spring on the heath", [S.spring[0], S.spring[1] - 1]]]) if (seen.has(at.join()) && !(fl.pos[0] === at[0] && fl.pos[1] === at[1])) { const p = game.pathTo(...at); out.push({ name, x: at[0], y: at[1], steps: p ? p.length : null }); }
    return out; }; }
// what is there: the spring, the Lookout's cairn, and the falls from the pool's edge
{ const P = CM.Game.prototype, key = (x, y) => `${x},${y}`;
  const SPRING = "A spring comes up out of the heath under a lip of rock, so cold it aches, so clear the stones at the bottom look close enough to pick up. It fills the tarn, and the tarn spills south.";
  const LOOKOUT = "A cairn of grey stones at the heath's south edge, built up by many hands. From here you look out over the tops of the Wood.";
  const FALLS = "The stream comes off the top of the rock in one white rope and drops into a pool among the trees. The noise of it fills the air, and the spray is cold on your face.";
  const words = (g, t) => (t.type === "scarpspring" ? SPRING : t.type === "lookout" ? (CM.lookoutWords ? CM.lookoutWords(g) : LOOKOUT) : null);
  const here = (g) => { const fl = g.floor; if (g.mode !== "explore" || !fl || fl.number !== -1) return null; const [dx, dy] = CM.DIRS[fl.facing];
    for (const k of [key(...fl.pos), key(fl.pos[0] + dx, fl.pos[1] + dy)]) { const t = fl.things[k]; if (t && (t.type === "scarpspring" || t.type === "lookout")) return t; } return null; };
  CM.SCARP_WORDS = { SPRING, LOOKOUT, FALLS };
  const u0 = P.use; P.use = function (...a) { const t = here(this); if (t) { this.say(words(this, t)); if (t.type === "scarpspring" && CM.scarpDrink) CM.scarpDrink(this); return true; }
    const fl = this.floor, S = CM.SCARP; if (this.mode === "explore" && fl && fl.number === -1 && fl.levels && CM.woodPlace(fl, fl.pos[0], fl.pos[1]) === "The Falls") { this.say(FALLS); return true; }
    return u0.apply(this, a); };
  const l0 = P.look; P.look = function (...a) { const out = l0.apply(this, a), t = here(this); if (t) this.say(`${words(this, t)} (Space)`); return out; }; }
// the fall is never a way up or down, frozen or not
{ const p0 = CM.passable; CM.passable = function (floor, x, y) { if (floor && floor.number === -1 && floor.levels && x === CM.SCARP.falls[0] && y === CM.SCARP.falls[1]) return false; return p0.call(this, floor, x, y); }; }
