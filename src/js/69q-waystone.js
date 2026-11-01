"use strict";
// The Wayfarer's Stone (v21.1, UPGRADE_PLAN_16.md; "the Waystone" in the plan, named apart from the dungeon camps' waystones): a tall stone on a dais by the Portal Court's opening, and its twin by the
// Wood's road. Touched, it takes the party to any place in the Wood they have already walked to - and the Wood's stone
// back to the court. A place is found by coming within two steps of it on foot (or, for a party that had been there
// before the stones were raised, by what the village already remembers of it). New places join by being found.
// The window: 76zzzr-waystone.js.
{ const WS = CM.WAYSTONE = { court: [33, 24], courtLand: [34, 22], wood: [55, 29], near: 2 };   // (the court's stone in its south-west corner, off every walk)
  // [id, name, the place (found within two steps), where the party lands, facing (0 N, 1 E, 2 S, 3 W), what it is]
  WS.PLACES = [
    ["woodgate", "The Wood gate", () => CM.WOOD_GATE, [58, 30], 3, "the road home, the land's east edge"],
    ["glade", "The First Glade", () => [18, 33], [18, 33], 1, "the glade nearest the river"],
    ["farm", "The farm", () => CM.FARM_AT, [45, 31], 1, "the fields by the road's bend"],
    ["glyph", "The Glyph Deep's cabinet", () => CM.GLYPH_AT, [28, 29], 0, "the arcade cabinet by the road"],
    ["tower", "The Mage Tower", () => CM.MAGE_DOOR, [47, 15], 0, "the tower's clearing"],
    ["cabin", "Leshy's cabin", () => CM.CABIN.front, [32, 18], 0, "the card table"],
    ["crag", "Claudeita's crag", () => CM.CLAUDEITA.front, [48, 44], 2, "the cave of wands"],
    ["fortress", "The Fortress", () => CM.FORTRESS.front, [35, 5], 0, "the black keep's doors"],
  ];
  WS.byId = Object.fromEntries(WS.PLACES.map((p) => [p[0], p]));
  const G = CM.Game.prototype;
  Object.assign(G, {
    wsStore() { this.village = this.village || {}; const S = this.village.waystone = this.village.waystone || {}; S.known = S.known || {}; return S; },
    // what the village remembers already: the gate and the glade from the first walk, the rest by their own records
    wsKnown() { const K = this.wsStore().known, v = this.village || {}; const was = { woodgate: true, glade: true, farm: this.villageLevel && this.villageLevel("farm") > 0, glyph: v.glyph && v.glyph.runs > 0,
        tower: this.tower && (this.tower.cleared > 0 || this.tower.best > 0), cabin: v.cards && v.cards.games > 0, crag: v.cave && v.cave.runs > 0, fortress: this.fort && this.fort.best > 0 };
      return WS.PLACES.filter(([id]) => K[id] || was[id]).map(([id]) => id); },
    wsFind() { const fl = this.floor; if (!fl || fl.number !== -1) return []; const K = this.wsStore().known, got = [];
      for (const [id, name, at] of WS.PLACES) { if (K[id]) continue; const c = at(); if (c && Math.abs(fl.pos[0] - c[0]) <= WS.near && Math.abs(fl.pos[1] - c[1]) <= WS.near) { K[id] = true; got.push(name); } }
      if (got.length) { this.say(`The Wayfarer's Stone will know it now: ${got.join(", ")}.`); this.saveVillage && this.saveVillage(); } return got; },
    wsWhy() { if (this.mode !== "explore" || !this.floor) return "Not now."; const fl = this.floor, at = fl.number === 0 ? WS.court : fl.number === -1 ? WS.wood : null; if (!at || fl.pos[0] !== at[0] || fl.pos[1] !== at[1]) return "The Wayfarer's Stone answers a hand laid on it."; return ""; },
    wsTravel(id) { const why = this.wsWhy(); if (why) return why;
      if (id === "court") { if (this.floor.number === 0) return "You're in the court."; this.logAct && this.logAct("wsTravel", id); this.sound && this.sound("teleport"); this.enterFloor(0, "rope", WS.courtLand.slice()); this.floor.facing = 1; this.say("The stone hums, the trees go thin as smoke, and you're standing by the Wayfarer's Stone in the Portal Court."); this.emit && this.emit("portalfx", "waystone"); return ""; }
      const P = WS.byId[id]; if (!P) return "No such place."; if (!this.wsKnown().includes(id)) return `The stone doesn't know ${P[1]} yet: walk there once.`;
      this.logAct && this.logAct("wsTravel", id); this.sound && this.sound("teleport"); this.enterFloor(-1, "rope", P[3].slice()); this.floor.facing = P[4];
      this.say(`The stone hums, the court goes thin as smoke, and you're standing at ${P[1].replace(/^The /, "the ")}.`); this.emit && this.emit("portalfx", "waystone"); return ""; },
  });
  // the stones on the floors
  { const ly0 = CM.layPortalYard; CM.layPortalYard = function (fl) { const out = ly0.call(this, fl); fl.things[WS.court.join(",")] = { type: "wayfarer" }; return out; }; }
  { const mw = CM.makeWood; CM.makeWood = function (seed) { const fl = mw(seed); fl.things[WS.wood.join(",")] = { type: "wayfarer" }; return fl; }; }
  // found on foot: after every step in the Wood
  { const look0 = G.look; G.look = function (...a) { const out = look0.apply(this, a); if (this.floor && this.floor.number === -1 && this.village && !this.replaying) this.wsFind(); return out; }; }
  // Space at a stone
  { const use0 = G.use; G.use = function (...a) { const fl = this.floor, t = fl && this.mode === "explore" && fl.things[`${fl.pos[0]},${fl.pos[1]}`];
      if (t && t.type === "wayfarer") { this.logAct && this.logAct("use"); this.say("The Wayfarer's Stone, taller than a man, cut with every place in the Wood it knows. It hums under your hand."); this.emit("wayfarer"); return; }
      return use0.apply(this, a); }; }
}
