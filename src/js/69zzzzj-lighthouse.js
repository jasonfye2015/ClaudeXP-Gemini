"use strict";
// The lighthouse (UPGRADE_PLAN_80.md, v132.0), the rules' side. Its door on the rock by the dock opens on a stair up
// to the gallery: by day, the whole island and the sea round it (the island found, if it wasn't); by night, the lamp.
// The lamp is the party's to light - nobody else keeps it - and once lit it burns and turns till dawn, its beam
// going round over the water; the town pays the keeper's wage for every night it's kept, out of a box by the lamp.
// A lit light is what a boat will want, coming in at night (the boat: v133.0).
//   CM.lighthouseLit(game); game.climbLighthouse(); CM.LIGHTHOUSE_WAGE
{ const L = CM.LIGHTHOUSE, P = CM.Game.prototype, key = (x, y) => `${x},${y}`;
  CM.SOLID.lighthouse = { face: "solid:lighthouse", h: L.h, tower: true };   // (built by the window: 77w-lighthouse.js)
  if (CM.SOLID_COLOURS) CM.SOLID_COLOURS.lighthouse = "#E8E4DC";
  CM.LIGHTHOUSE_WAGE = 12; const EYE_ABOVE = -0.12;   // (the gallery's floor is the tower's top; the eye a little over it)
  const nightOf = (g) => { const h = CM.hourOf ? CM.hourOf(g) : 12, d = CM.dayOf ? CM.dayOf(g) : 0; return h < 12 ? d - 1 : d; };   // (a night belongs to the day it began on)
  CM.lighthouseLit = (g) => Boolean(g && g.ext && CM.isNight && CM.isNight(g) && g.ext("lighthouse").lit === nightOf(g));
  P.climbLighthouse = function () { const fl = this.floor; if (!fl || fl.number !== -1 || this.perch) return false; const R = this.ext("lighthouse"), V = this.vext("lighthouse");
    this.perch = { tower: [L.at[0] - 0.55, L.at[1]], from: key(...L.door), h: L.h - EYE_ABOVE, lighthouse: true };   // (out on the gallery, the dock's side) this.clock = (this.clock || 0) + 6; this.sound && this.sound("wind");
    if (CM.isNight && CM.isNight(this)) {
      if (R.lit === nightOf(this)) this.say("Up the turning stair to the lamp room. The great lamp burns steady behind its lenses and the clockwork turns it, slow and certain; the beam goes round over the water, and round again.");
      else { R.lit = nightOf(this); V.nights = (V.nights || 0) + 1; this.gold += CM.LIGHTHOUSE_WAGE; this.tally = this.tally || {}; this.tally.lighthouse = (this.tally.lighthouse || 0) + 1;
        this.say(`Up the turning stair to the lamp room, dark and smelling of oil. The wick takes the flame; the lenses catch it; you wind the clockwork and the whole lamp begins to turn, and the beam goes out over the sea. ${V.nights === 1 ? "Whoever kept this light before, it's yours to keep now. " : ""}In the keeper's box by the lamp, the town's wage for a night's keeping: ${CM.LIGHTHOUSE_WAGE} gold. The book beside it has ${V.nights} night${V.nights === 1 ? "" : "s"} in your hand.`); } }
    else { this.say("Up the turning stair and out onto the gallery, the wind pulling at you: the dock below, the pier running back to the sand, the Strand, the Scarp, the Wood, the town on its hill - and the sea all round, every way you look. The lamp behind you waits for night.");
      const Ld = this.vext("land"); if (!Ld.island) { Ld.island = (CM.dayOf ? CM.dayOf(this) : 0) + 1; this.say("It is an island. The whole of the world you know is an island."); this.emit("island"); } }
    this.emit("change"); return true; };
  { const cd0 = P.climbDown; P.climbDown = function () { if (this.perch && this.perch.lighthouse) { this.perch = null; this.clock = (this.clock || 0) + 6; this.say("Down the turning stair, and out onto the rock by the dock."); this.emit("change"); return true; } return cd0.call(this); }; }
  { const u0 = P.use; P.use = function (...a) { const fl = this.floor; if (this.mode === "explore" && fl && fl.number === -1 && !this.perch) { const [dx, dy] = CM.DIRS[fl.facing], ahead = [fl.pos[0] + dx, fl.pos[1] + dy];
      const atDoor = (fl.pos[0] === L.door[0] && fl.pos[1] === L.door[1]) || (ahead[0] === L.at[0] && ahead[1] === L.at[1]); if (atDoor) return this.climbLighthouse(); } return u0.apply(this, a); }; }
  { const l0 = P.look; P.look = function (...a) { const out = l0.apply(this, a), fl = this.floor; if (this.mode === "explore" && fl && fl.number === -1 && fl.pos[0] === L.door[0] && fl.pos[1] === L.door[1]) this.say(CM.lighthouseLit(this) ? "The lighthouse door. High overhead the lamp is burning, its beam going round. (Space: up the stair)" : CM.isNight && CM.isNight(this) ? "The lighthouse door, and over it the tower dark against the stars: the lamp's unlit. (Space: up the stair to light it)" : "The lighthouse: a tower banded red and white, a gallery round its top. The door's on the latch. (Space: up the stair)"); return out; }; }
  // names
  { const wp0 = CM.woodPlace; CM.woodPlace = function (fl, x, y) { if (fl && fl.number === -1 && CM.isLighthouseRock(x, y) && fl.grid.length > L.rock[3]) return "the lighthouse rock"; return wp0.call(this, fl, x, y); }; }
  { const ws0 = CM.woodSafe; CM.woodSafe = function (fl, x, y) { return (fl && fl.number === -1 && CM.isLighthouseRock(x, y)) || ws0.call(this, fl, x, y); }; }
  { const wy0 = CM.wayPlaces; CM.wayPlaces = function (game) { const out = wy0(game), fl = game.floor; if (!fl || fl.number !== -1 || fl.grid.length <= L.rock[3]) return out; const at = L.door;
      if ((fl.seen || []).some(([x, y]) => x === at[0] && y === at[1]) && !(fl.pos[0] === at[0] && fl.pos[1] === at[1])) { const p = game.pathTo(...at); out.push({ name: "The lighthouse", x: at[0], y: at[1], steps: p ? p.length : null }); } return out; }; }
}
