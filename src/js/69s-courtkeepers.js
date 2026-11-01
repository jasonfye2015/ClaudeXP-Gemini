"use strict";
// The court's keepers (v21.3, UPGRADE_PLAN_16.md): the noticeboard in the court's south-east corner (every place
// beyond the portals, its next step and what's waiting), the Portal-warden by the east wall (who may go where, what each
// place is, and a word on what to do next), and the shaft's lift (any merchant's camp reached, or the first floor).
// The windows: 76zzzt-courtkeepers.js.
{ const PC = CM.PORTALCOURT, PL = CM.PORTALLOOKS, CK = CM.COURTKEEPERS = {};
  // the board: a row for every place beyond the court, and the shaft
  CK.board = (g) => { const rows = PC.PORTALS.map(([k, , name, col, kind]) => ({ key: k, name, col, kind, status: PL.status(g, k), who: PL.WHO[k][1] }));
    const deepest = Math.max(0, ...((g.trail || []).map(([n]) => n || 0))), camps = (g.camps || []).slice().sort((a, b) => a - b);
    rows.unshift({ key: "shaft", name: "The shaft", col: "#C0A060", kind: "shaft", status: deepest ? `this run's deepest: floor ${deepest}${camps.length ? `; camps below ${camps.join(", ")}` : ""}` : "the first floor waits", who: "the whole party" });
    const W = g.wsKnown ? g.wsKnown().length : 0; rows.push({ key: "wayfarer", name: "The Wayfarer's Stone", col: "#80C0FF", kind: "stone", status: `${W} of ${CM.WAYSTONE ? CM.WAYSTONE.PLACES.length : 0} places in the Wood known`, who: "the whole party" });
    return rows; };
  // the warden's words: who they are, the court, and the next thing worth doing (the goals page's first open row)
  CK.LINES = [
    "\"I keep the court. Somebody has to sweep the runes.\"",
    "\"The portals on the north and south walls go into the Wood - the Tower, Leshy's, the cave, the Fortress, the cabinet by the road. The two on the east wall go somewhere else entirely, and only one of you at a time.\"",
    "\"The stone in the corner knows every place in the Wood you've walked to. Lay a hand on it.\"",
    "\"The badge over an arch tells you: one figure, one of you alone; four, all of you.\"",
    "\"The winch on the shaft will lower you to any camp you've reached. Mind your fingers.\"",
  ];
  CK.advice = (g) => { let goals = []; try { goals = g.wmGoals ? g.wmGoals() : []; } catch (e) { goals = []; } const G = goals.find((x) => x.go && !/beaten|undone|won|highest|quiet|rung/i.test(x.text)); return G ? `"If you're asking me - ${G.area}: ${G.text.charAt(0).toLowerCase()}${G.text.slice(1)}"` : "\"You've done more than I'd have thought. Go and sit in the sun.\""; };
  const G = CM.Game.prototype;
  Object.assign(G, {
    talkWarden() { const k = (this.wardenTalks = (this.wardenTalks || 0) + 1); this.emit && this.emit("talk", { title: "The Portal-warden", text: CK.LINES[(k - 1) % CK.LINES.length], lines: [CK.advice(this)] }); return ""; },
    // the lift: to a camp reached (the merchant's lantern below that floor), or 0 for the first floor by the ladder
    shaftLiftWhy(n) { const fl = this.floor; if (this.mode !== "explore" || !fl || fl.number !== 0) return "The lift is at the shaft, in town."; const t = fl.things[`${fl.pos[0]},${fl.pos[1]}`]; if (!t || t.type !== "ladder") return "Stand at the shaft.";
      if (n && !(this.camps || []).includes(n)) return "The lift only goes to camps you've reached."; return ""; },
    shaftLift(n) { const why = this.shaftLiftWhy(n); if (why) return why; this.logAct && this.logAct("shaftLift", n); this.sound && this.sound("stairs");
      if (!n) { this.enterFloor(1, "down"); this.say("The winch lowers you hand over hand to the first floor."); return ""; }
      const below = this.floorAt(n); this.leaveFloor(); this.floor = below; this.stock = null; this.recruits = null; const ladder = this.cellOf(below, "ladder"); if (ladder) below.pos = ladder.slice();
      this.setMode("camp"); this.emit("floor", below); this.say(`The winch creaks and lowers the whole party past the floors you know, to the merchant's lantern beneath floor ${n}.`); this.saveRun(); this.emit("change"); return ""; },
  });
  // the board and the warden in the court
  { const ly0 = CM.layPortalYard; CM.layPortalYard = function (fl) { const out = ly0.call(this, fl); fl.things[PC.BOARD.join(",")] = { type: "courtboard" }; fl.things[PC.WARDEN.join(",")] = { type: "warden" }; return out; }; }
  { const use0 = G.use; G.use = function (...a) { const fl = this.floor, t = fl && this.mode === "explore" && fl.number === 0 && fl.things[`${fl.pos[0]},${fl.pos[1]}`];
      if (t && t.type === "courtboard") { this.logAct && this.logAct("use"); this.say("The court's noticeboard: every place beyond the portals, chalked up and rubbed out and chalked up again."); this.emit("courtboard"); return; }
      if (t && t.type === "warden") { this.logAct && this.logAct("use"); this.talkWarden(); return; }
      return use0.apply(this, a); }; }
}
