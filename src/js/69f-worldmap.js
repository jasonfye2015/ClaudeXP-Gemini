"use strict";
// The world, on one page (v18.5): every place the party can go - the town's doors, the Keep-yard's portals and the
// shaft, the pipe, the Joker, and out in the Wood the farm, the cabin, the Mage Tower, the Fortress and Claudeita's
// crag - with fast travel between them from anywhere above ground (the town or the Wood), and what's waiting at each:
// requests at the well, rewards at the Joker, a hero with a boon or skill points to spend, a build the village can
// afford. And the goals, gathered: for every part of the game, what's next. The window is 76zzzg-worldmap.js.
{ const WM = CM.WORLDMAP = {};
  // [id, name, floor, cell, what, open it on arrival]
  WM.PLACES = [
    ["home", "Your house", 0, () => CM.TOWN_AT.home, "rest, the hearth, the larder", true], ["well", "The well and the request board", 0, () => CM.TOWN_AT.well, "the village's requests", false],
    ["tavern", "The Hanged Lantern", 0, () => CM.TOWN_AT.tavern, "a round, the regular's gossip", true], ["merchant", "The Merchant's House", 0, () => CM.TOWN_AT.merchant, "buy, sell, commissions", true],
    ["smith", "The Smith's forge", 0, () => CM.TOWN_AT.smith, "enchanting, tempering, the smelter", true], ["temple", "The temple", 0, () => CM.TOWN_AT.temple, "healing, candles, the vigil", true],
    ["library", "The library", 0, () => CM.TOWN_AT.library, "tomes and lost pages", true], ["guildhall", "The guildhall", 0, () => CM.TOWN_AT.guildhall, "trainers, contracts, the roster", true],
    ["casino", "The Gilded Joker", 0, () => CM.TOWN_AT.casino, "the casino, the arcade, the fair", true], ["pipe", "The pipe in the Square", 0, () => CM.TOWN_PIPE, "Super Claude Bros", false],
    ["shaft", "The shaft", 0, () => CM.TOWN_AT.shaft, "down into the dungeon", false], ["haven", "The red portal", 0, () => CM.PORTAL_YARD.ablo, "Claudeablo's Haven", false],
    ["gate", "The Neather Gate", 0, () => CM.PORTAL_YARD.gate, "the island (Claudecraft)", false], ["yard", "The Keep-yard's portals", 0, () => CM.PORTAL_YARD.tower, "the Mage Tower, the cabin, the cave, the Fortress", false],
    ["farm", "The farm", -1, () => CM.FARM_AT, "the fields", false], ["cabin", "Leshy's cabin", -1, () => CM.CABIN && CM.CABIN.front, "the card table", false],
    ["fortress", "The Fortress", -1, () => CM.FORTRESS && CM.FORTRESS.front, "real-time siege", false], ["crag", "Claudeita's crag", -1, () => CM.CLAUDEITA && CM.CLAUDEITA.front, "the cave of wands", false],
    ["woodgate", "The Deep Wood", -1, () => CM.WOOD_GATE, "the land west of the town", false],
  ];
  WM.byId = Object.fromEntries(WM.PLACES.map((p) => [p[0], p]));
  Object.assign(CM.Game.prototype, {
    wmCanTravel() { if (this.mode !== "explore" || !this.floor) return "Fast travel goes from the town or the Wood."; if (this.floor.number !== 0 && this.floor.number !== -1 && !(CM.isJokerFloor && CM.isJokerFloor(this.floor.number))) return "Fast travel goes from the town or the Wood - the shaft and the portals bring you back up."; return ""; },
    // there in a step: onto the place's square, facing a way out; a door that opens, opened
    wmTravel(id) { const P = WM.byId[id]; if (!P) return "No such place."; const why = this.wmCanTravel(); if (why) return why; const at = P[3](); if (!at) return "That place isn't there.";
      if (this.floor.special === "joker" && this.jfLeave) this.jfLeave();
      this.logAct && this.logAct("wmTravel", id); this.stopTravel && this.travel && this.stopTravel(); this.enterFloor(P[2], "rope", at.slice()); const fl = this.floor; fl.pos = at.slice();
      const open = CM.openNeighbours ? CM.openNeighbours(fl, at[0], at[1]) : []; if (open.length && CM.DIRS.indexOf(open[0]) >= 0) fl.facing = CM.DIRS.indexOf(open[0]);
      this.look && this.look(); this.emit("moved", at[0], at[1]); this.emit("floor", fl); this.emit("change"); this.say(`To ${P[1].replace(/^The /, "the ")}.`);
      if (P[5] && fl.things[`${at[0]},${at[1]}`]) this.use(); return ""; },
    // what's waiting where, for the map's marks
    wmMarks() { const m = {}, add = (id, n, what) => { (m[id] = m[id] || []).push(what); };
      try { const L = this.rqList(); const ready = L.filter((q) => !q.done && this.rqProgress(q) >= q.n).length, open = L.filter((q) => !q.done).length; if (ready) add("well", ready, `${ready} request${ready > 1 ? "s" : ""} ready to hand in`); else if (open) add("well", open, `${open} request${open > 1 ? "s" : ""} posted`); } catch (e) { /* */ }
      try { if (this.alInfo && this.alInfo().waiting.length) add("casino", 1, "Almanac steps to collect"); if (this.jkWaiting && (this.jkWaiting().levels.length || this.jkWaiting().tickets)) add("casino", 1, "Joker level rewards"); if (this.flQuests && this.flQuests().some((q) => q.got >= q.n)) add("casino", 1, "a casino quest done"); } catch (e) { /* */ }
      if (this.party.some((h) => h.pending)) add("home", 1, "a boon to choose"); if (this.party.some((h) => CM.SKILLTREE && CM.SKILLTREE.points(h) > CM.SKILLTREE.spent(h))) add("home", 1, "skill points to spend"); if (this.party.some((h) => CM.needsPath && CM.needsPath(h))) add("home", 1, "a path to choose");
      const afford = Object.entries(CM.VILLAGE || {}).filter(([id, V]) => { const lvl = this.villageLevel(id); return lvl < V.costs.length && this.renown() >= V.costs[lvl] && (CM.villageNeeds ? CM.villageNeeds(id, lvl) : []).every(([k, n]) => CM.TOWNREQ.byId[k].have(this) >= n); }).map(([, V]) => V.name);
      if (afford.length) add("guildhall", 1, `can be built: ${afford.join(", ")}`); return m; },
    // every part of the game, and what's next in it
    wmGoals() { const out = [], row = (area, text, go) => out.push({ area, text, go }), deepest = Math.max(0, ...((this.fame || []).map((e) => e.floor || 0)), ...((this.trail || []).map(([n]) => n)));
      try { const L = this.rqList(); for (const q of L) if (!q.done) row("The town", `${q.giver.charAt(0).toUpperCase() + q.giver.slice(1)} wants ${this.rqWords(q)} (${Math.min(q.n, this.rqProgress(q))} of ${q.n})`, "well"); } catch (e) { /* */ }
      { const next = Object.entries(CM.VILLAGE || {}).map(([id, V]) => [id, V, this.villageLevel(id)]).filter(([, V, l]) => l < V.costs.length).sort((a, b) => a[1].costs[a[2]] - b[1].costs[b[2]])[0]; if (next) row("The town", `Next build: ${next[1].name} to level ${next[2] + 1} - ${next[1].costs[next[2]]} renown (you have ${this.renown()})${CM.matsNote ? CM.matsNote(this, next[0], next[2]) : ""}`, "guildhall"); }
      for (const h of this.party) { if (h.pending) row("The heroes", `${h.name} has a boon to choose`, "home"); if (CM.needsPath && CM.needsPath(h)) row("The heroes", `${h.name} can choose a path`, "home"); const sp = CM.SKILLTREE ? CM.SKILLTREE.points(h) - CM.SKILLTREE.spent(h) : 0; if (sp > 0) row("The heroes", `${h.name} has ${sp} skill point${sp > 1 ? "s" : ""} to spend`, "home"); }
      row("The dungeon", deepest ? `Deepest so far: floor ${deepest}. ${(this.tally.guardians || []).length} of the guardians slain this run.` : "Down the shaft: the first floor waits.", "shaft");
      try { const K = this.cards(), T = (CM.CARD_TABLES || []).find((t) => !K.beaten[t.id] && this.cardTableOpen(t)); row("Leshy's cabin", T ? `Next at the table: ${T.name} (${T.gold} gold, a ${T.pick} card)` : "Every game at the table won.", "cabin"); } catch (e) { /* */ }
      try { const A = this.abloStore(); row("Haven", `Through the red portal: ${A.visits || 0} visit${A.visits === 1 ? "" : "s"} so far${this.tally.abloDeepest ? `, deepest ${this.tally.abloDeepest}` : ""}. What's found there comes home.`, "haven"); } catch (e) { /* */ }
      try { const K = this.craftStore(); row("The island", `Through the Neather Gate: ${K.visits || 0} visit${K.visits === 1 ? "" : "s"}. Its ore, bars and gems feed the smith; its timber and stone the builders.`, "gate"); } catch (e) { /* */ }
      row("The pipe", this.tally.brosBest ? `Best so far: level 1-${this.tally.brosBest}.` : "Down the pipe in the Square: four levels and a Brass Warden.", "pipe");
      try { if (this.cgStore) { const J = this.jkInfo(), A = this.alInfo(), W = this.wkInfo(); row("The Joker", `Joker level ${J.level}; the Almanac at step ${A.reached} of 30${A.waiting.length ? ` (${A.waiting.length} to collect)` : ""}; the week's game is ${((CM.CG_TABLES || []).find(([k]) => k === W.id) || [])[1] || W.id}${this.stFinalReady && this.stFinalReady() ? "; the Final Night is ready" : ""}.`, "casino"); } } catch (e) { /* */ }
      return out; },
  });
}
