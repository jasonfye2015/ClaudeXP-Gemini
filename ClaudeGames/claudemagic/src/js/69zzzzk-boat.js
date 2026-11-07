"use strict";
// The boat (UPGRADE_PLAN_80.md, v133.0), the rules' side. A ship lies at the dock's south face - the Wren, Captain
// Morra Vane's - and anyone on the dock's edge can go aboard: the captain unrolls her sea chart, and the party picks
// where to go. To begin with that's home and a sail round the island - out along the south coast, up the west and
// along the north under the cliffs, and back to the harbour; the islands she knows of and the mainland's port are on
// the chart, and the passages open as each is charted (the places themselves: v134.0 and on). The fare is paid as
// you sail; a crossing takes hours of the clock; and she won't put out at night unless the lighthouse is lit.
//   CM.SEA_PLACES; game.boardShip(); game.seaWhyNot(id); game.sail(id) -> the voyage, for the window to show
{ const H = CM.HARBOUR, P = CM.Game.prototype;
  CM.SHIP = { name: "the Wren", captain: "Captain Morra Vane", at: [H.pier[0] + 0.5, H.head[3] + 2.6], scale: 0.55 };
  CM.SEA_PLACES = [
    { id: "home", name: "Caer Duin's island", chart: [420, 250], what: "Home: the Wood and the river, the Scarp and its falls, the town on its hill, the harbour and its light.", open: true, fare: 0, hours: 4 },
    { id: "round", name: "Round the island", chart: [420, 250], what: "A sail along the coast and home again: the Strand, the west shore, the north coast under the trees. Two hours, and the wind in your face.", open: true, trip: true, fare: 6, hours: 2 },
    { id: "gull", name: "Gull Rock", chart: [190, 110], what: "A tooth of rock to the north-west where the seabirds nest in their thousands. Someone keeps a light there too, the captain says - or did.", fare: 20, hours: 4 },
    { id: "fen", name: "The Fenholm", chart: [160, 390], what: "Low green islands to the south-west, more water than land: reeds, eels, and people who live on stilts and don't care for visitors.", fare: 25, hours: 5 },
    { id: "ember", name: "Emberreach", chart: [660, 400], what: "A mountain in the sea to the south-east that smokes on still days. Black sand, hot springs, and things that like the heat.", fare: 35, hours: 6 },
    { id: "main", name: "Harrowgate, on the Mainland", chart: [690, 90], what: "The mainland: a whole continent, the captain says, roads and rivers and kingdoms, and Harrowgate the port where her ship was built.", fare: 40, hours: 8 } ];
  CM.seaPlace = (id) => CM.SEA_PLACES.find((p) => p.id === id);
  CM.seaOpen = (g, id) => { const p = CM.seaPlace(id); return Boolean(p && (p.open || (CM.SEA_OPEN && CM.SEA_OPEN.includes(id)))); };   // (CM.SEA_OPEN: the places charted since - each adds itself)
  const atBerth = (fl) => fl && ((fl.number === -1 && fl.pos[1] === H.head[3] && fl.pos[0] >= H.head[0] && fl.pos[0] <= H.head[2] && (!CM.LIGHTHOUSE || fl.pos[0] !== CM.LIGHTHOUSE.door[0]))
    || (CM.isIsleLanding && CM.isIsleLanding(fl.number) && CM.isleOf(fl.number).isle.atBerth(fl.pos)));   // (v134.0: and at every island's jetty)
  CM.seaHere = (g) => { const fl = g && g.floor; if (!fl) return null; if (fl.number === -1) return "home"; const o = CM.isleOf && CM.isleOf(fl.number); return o ? o.isle.id : null; };
  CM.atBerth = (g) => Boolean(g && atBerth(g.floor));
  P.boardShip = function () { if (!atBerth(this.floor) || this.mode !== "explore") return false; this.say(`Up the gangplank onto ${CM.SHIP.name}. ${CM.SHIP.captain} looks up from coiling a rope. "Going somewhere?" She unrolls a chart across the hatch cover.`); this.emit("seachart"); return true; };
  P.seaWhyNot = function (id) { const p = CM.seaPlace(id); if (!p) return "Nowhere on the chart by that name.";
    if (id === CM.seaHere(this) || (p.trip && CM.seaHere(this) !== "home")) return id === CM.seaHere(this) ? "That's where you are." : `"That's a sail for home waters. We're a long way from them."`; if (!CM.seaOpen(this, id)) return `"Not there - not yet. My charts for those waters are old and wrong, and I won't sail on a wrong chart."`;
    if (CM.seaHere(this) === "home" && CM.isNight && CM.isNight(this) && !(CM.lighthouseLit && CM.lighthouseLit(this))) return `"Not in the dark with the light out. Light the lamp and I'll take her out."`;
    if ((this.gold || 0) < (p.fare || 0)) return `"The fare's ${p.fare} gold. I've a crew to feed."`; return ""; };
  P.sail = function (id) { const why = this.seaWhyNot(id); if (why) { this.say(why); return null; } const p = CM.seaPlace(id); this.logAct && this.logAct("sail", id);
    this.gold -= p.fare || 0; if (this.spend) this.spend("passage", p.fare || 0); this.clock = (this.clock || 0) + (p.hours || 1) * 60; const T = this.tally || (this.tally = {}); T.voyages = (T.voyages || 0) + 1; this.vext("sea").sailed = (this.vext("sea").sailed || 0) + 1;
    if (p.trip) { this.say(`${CM.SHIP.captain} casts off, and ${CM.SHIP.name} goes out past the lighthouse into the open sea, along the coast and round, and home to the dock ${p.hours} hours later.`); this.emit("voyage", { id, home: true }); this.emit("change"); return { id, home: true }; }
    const out = id === "home" ? (this.enterFloor(-1, "rope", [H.pier[0], H.head[3]]), this.floor.facing = 0, this.say(`${CM.SHIP.name} comes in past the lighthouse and ties up at the dock. Home.`), { id }) : CM.seaArrive ? CM.seaArrive(this, id) : null; this.emit("voyage", { id, home: false }); this.emit("change"); return out || { id }; };
  // the dock: Space on its south edge goes aboard
  { const u0 = P.use; P.use = function (...a) { if (this.mode === "explore" && atBerth(this.floor) && !this.perch) return this.boardShip(); return u0.apply(this, a); }; }
  CM.dockWords = () => `The dock. ${CM.SHIP.name} lies along its south face, her sails furled, ${CM.SHIP.captain} somewhere aboard. (Space on the dock's edge: go aboard)`;
}
