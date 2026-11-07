"use strict";
// The island (UPGRADE_PLAN_79.md, v129.0), the rules' side. The sea is a solid nothing is drawn on - the sea's own
// surface lies there (77t-island.js); the Strand and the river's mouth are named; and the land is found to be an island - first the sea
// itself from the sand, then the whole of it from the Lookout on the Scarp: water every way you turn but east, where
// the hill and the town stand, and past the hill, from that height, the sea again. Kept with the village (vext land):
// a later run knows it, the world map shows it, Claude has something to say about it.
//   CM.islandKnown(game); CM.lookoutWords(game); game.vext("land") = { sea, island }
{ const H = CM.SHORE, S = CM.SCARP, P = CM.Game.prototype, key = (x, y) => `${x},${y}`;
  CM.SOLID.sea = { face: "ground:sand", h: 0.001, see: true, sea: true };   // (no wall to see, no ground: the sea itself lies there, under the land and out past it - 77t-island.js)
  if (CM.SOLID_COLOURS) CM.SOLID_COLOURS.sea = "#4A7A9A";
  CM.seaGirt = (fl) => Boolean(fl && fl.grid && ((fl.number === -1 && CM.LAND_ISLE && fl.grid.length > H.sea) || (CM.isIsleLanding && CM.isIsleLanding(fl.number))));   // (v134.0: the home island, and every island's landing)
  CM.seaCells = (fl) => (fl && CM.seaGirt(fl) && fl.kinds ? Object.keys(fl.kinds).filter((k) => fl.kinds[k] === "sea").map((k) => k.split(",").map(Number)) : []);   // (v130.0: for the renderer's map - the sea is water)
  CM.islandKnown = (g) => Boolean(g && g.vext && g.vext("land").island);
  // names
  { const mw0 = CM.makeWood; CM.makeWood = function (seed) { const fl = mw0.call(this, seed); if (fl && fl.grid.length > H.sea && !fl.rooms.some((r) => r.name === "The Strand")) fl.rooms = [{ x0: 0, y0: H.fringe, x1: fl.grid.length - 1, y1: fl.grid.length - 1, name: "The Strand" }].concat(fl.rooms); return fl; }; }
  { const wp0 = CM.woodPlace; CM.woodPlace = function (fl, x, y) { if (fl && fl.number === -1 && fl.grid.length > H.sea && y >= H.strand[0]) { if (x === CM.riverX(y)) return "the river's mouth"; if (y >= H.strand[0]) return "The Strand"; } return wp0.call(this, fl, x, y); }; }
  { const wy0 = CM.wayPlaces; CM.wayPlaces = function (game) { const out = wy0(game), fl = game.floor; if (!fl || fl.number !== -1 || fl.grid.length <= H.sea) return out; const at = H.shore;
      if ((fl.seen || []).some(([x, y]) => x === at[0] && y === at[1]) && !(fl.pos[0] === at[0] && fl.pos[1] === at[1])) { const p = game.pathTo(...at); out.push({ name: "The Strand", x: at[0], y: at[1], steps: p ? p.length : null }); } return out; }; }
  // the words: the sea from the sand; the island from the cairn
  const SEA_FIRST = "The trees end, and there is sand, and past the sand there is the sea - grey-green, wrinkled, going on and on until it is the sky. Nobody in Caer Duin ever said there was a sea. The waves come up the sand a little way, and go back, and come up again.";
  const SEA_AGAIN = ["The sea, the same as ever and never the same: the waves come up the sand and go back.", "Salt on the wind, gulls over the water, and nothing on the horizon at all.", "The tide has left a line of weed and shells along the sand, and the sea is a little further off than it was."];
  const ISLAND_FIRST = "From the cairn you can see all of it at once: the Wood, the river winding through it to the sand, the fields, the farm, the hill with Caer Duin on its top - and all round it, every way you turn, the sea. South and west and north, the sea; and east, past the town's hill, from up here, the sea again. It is an island. The whole of the world you know is an island, and the water goes on past the edge of seeing.";
  CM.lookoutWords = (g) => (CM.islandKnown(g) ? "From the cairn: the Wood, the river, the fields and the town on its hill - and the sea all round it, as far as there is anything to see. An island, and you on it." : CM.SCARP_WORDS.LOOKOUT);
  CM.ISLAND_WORDS = { SEA_FIRST, SEA_AGAIN, ISLAND_FIRST };
  const atSea = (fl) => fl.grid.length > H.sea && fl.pos[1] >= H.strand[0];
  const atLookout = (fl) => fl.levels && fl.pos[0] === S.lookout[0] && fl.pos[1] === S.lookout[1];
  const notice = (g) => { const fl = g.floor; if (!fl || fl.number !== -1 || g.mode !== "explore") return; const L = g.vext("land"), R = g.ext ? g.ext("land") : {}, day = CM.dayOf ? CM.dayOf(g) : 0;
    if (atSea(fl) && !R.sea) { R.sea = true; const first = !L.sea; if (first) L.sea = day + 1; g.say(first ? SEA_FIRST : SEA_AGAIN[day % SEA_AGAIN.length]); }
    if (atLookout(fl) && fl.grid.length > H.sea && !L.island) { L.island = day + 1; R.island = true; g.say(ISLAND_FIRST); g.emit("island"); } };
  { const em0 = P.emit; P.emit = function (ev, ...a) { const out = em0.call(this, ev, ...a); if (ev === "moved") notice(this); return out; }; }
  // at the water's edge
  { const u0 = P.use; P.use = function (...a) { const fl = this.floor; if (this.mode === "explore" && fl && fl.number === -1 && atSea(fl) && fl.pos[1] === H.strand[1]) { const day = CM.dayOf ? CM.dayOf(this) : 0; this.say(SEA_AGAIN[(day + fl.pos[0]) % SEA_AGAIN.length]); return true; } return u0.apply(this, a); }; }
  // Claude, once he hears
  const CLAUDE_TOLD = "Claude sets his cup down very carefully. \"An island.\" He looks at the window for a long time. \"I'd wondered. The way the wind comes, the gulls in a hard winter. Nobody ever went to look - why would they? Everything anyone needed was here.\" A small laugh. \"I'm going to have to redraw every map I own. Thank you. Really. That's the best thing anyone's brought me in years.\"";
  const CLAUDE_AGAIN = ["\"Do you think anyone's ever sailed off it? There's no boat in the town's records. No word for one, even. I checked.\"", "\"I went down to the sand yesterday and stood with my feet in it. It's cold. Colder than the river. It tastes of salt - don't tell anyone I tasted it.\"", "\"Somewhere out there there's another shore, I suppose. Or there isn't. I can't decide which I'd rather.\""];
  CM.claudeTopics = (CM.claudeTopics || []).concat([(g) => { if (!CM.islandKnown(g)) return []; const V = g.vext("claude"); return [["island", V.island ? "About the sea" : "We saw the sea from the Scarp - all round us"]]; }]);
  CM.claudeActs = Object.assign(CM.claudeActs || {}, { island: (g, k, say) => { const V = g.vext("claude"); if (!V.island) { V.island = 1; say(CLAUDE_TOLD); } else { say(CLAUDE_AGAIN[V.island % CLAUDE_AGAIN.length]); V.island += 1; } g.emit("change"); } });
}
