"use strict";
// Return to Claude, and Claude keeps the house (UPGRADE_PLAN_71.md, release 1). Once the party has met him, a page
// turns and they are at his door: freely above ground, once a floor below it (an hour gone), never in a fight, from the
// king's floor, or on a ladder run (Iron and Ascension walk every step). His bookmark holds the place they left, and
// his door opens three ways: back where we were, out into the clearing, or home to the town. And the cabin's things are
// the game's controls - the desk the saves, the lamp how the world looks, the clock the pace and the keys, the kettle the
// sound, the shelf the record, the window the run, the back door the credits - each opened by asking him or by Space
// at the thing itself (the window shows them: 76zzzzzzzzzzzzi-claudehouse.js). The Esc menu keeps them all too.
//   game.claudeReturnWhy() -> "" or why not; game.returnToClaude(); game.claudeLeave("back"|"clearing"|"town");
//   the "claudePanel" event (id); CM.CLAUDE_HOUSE
{ const P = CM.Game.prototype, C = CM.CLAUDE_CABIN, ROOM = CM.CLAUDE_ROOM, key = (x, y) => `${x},${y}`, START = [6, 9], EXIT = [6, 10];
  CM.RETURN_COST = 60;   // (minutes: from below ground, the page takes an hour)
  P.claudeReturnWhy = function () { const V = this.vext("claude"), fl = this.floor;
    if (!V.met) return "You haven't met Claude yet - there's a path off the Wood's road, south, past the farm.";
    if (!fl || this.mode !== "explore") return "Not now: finish what's in front of you first.";
    if (fl.interior === "claude") return "You're at Claude's already.";
    if (this.perch) return "Climb down first.";
    if (this.iron || (this.ascension || 0) > 0) return "Not on a ladder run: an Iron or Ascension party walks every step.";
    if (fl.number === CM.LAST_FLOOR) return "Not from the king's own floor.";
    if (fl.number >= 1 && (this.ext("claude").returnedFrom || {})[fl.number]) return "Claude's door has opened from this floor once already. The next floor down, it will again.";
    return ""; };
  P.returnToClaude = function () { const why = this.claudeReturnWhy(); if (why) { this.say(why); this.emit("change"); return false; }
    this.logAct && this.logAct("returnToClaude"); const fl = this.floor, E = this.ext("claude");
    E.bookmark = { n: fl.number, pos: fl.pos.slice(), facing: fl.facing || 0 };
    if (fl.number >= 1) { (E.returnedFrom = E.returnedFrom || {})[fl.number] = true; this.clock = (this.clock || 0) + CM.RETURN_COST; }
    this.travel = null; return this.claudeEnter("page"); };
  // his door: three ways out once the bookmark holds a place
  const WAYS = { back: "Back where we were", clearing: "Out into the clearing", town: "Home to the town" };
  const where = (B) => (B.n === 0 ? "the town" : B.n === -1 ? "the Wood" : B.n >= 1 ? `floor ${B.n}` : "the room you left");
  { const cl0 = P.claudeLeave; P.claudeLeave = function (dest) { const E = this.ext("claude"), B = E.bookmark;
      if (!dest && B && !(this.autoOn && this.autoOn())) { this.claudeDoor = ["back", "clearing", "town"]; this.emit("choice", { k: key(...EXIT), title: "Claude's door", text: `Claude's bookmark is still in the book, at ${where(B)}.`, options: [`${WAYS.back} (${where(B)})`, WAYS.clearing, WAYS.town] }); return; }
      delete E.bookmark; const to = dest || (B ? "back" : "clearing");
      if (to === "back" && B) { this.logAct && this.logAct("claudeLeave", "back"); this.sound && this.sound("page"); this.enterFloor(B.n, "rope", B.pos.slice()); this.floor.facing = B.facing; this.say(`A page turns back, and you are where you were - ${where(B)}, Claude's bookmark in your hand for a moment and then not.`); this.emit("floor", this.floor); this.emit("change"); return; }
      if (to === "town") { this.logAct && this.logAct("claudeLeave", "town"); this.sound && this.sound("page"); const at = (CM.TOWN_AT && CM.TOWN_AT.well) || [20, 19]; this.enterFloor(0, "rope", at.slice()); this.say("A page turns, and you are by the well in the Square, the cabin's woodsmoke still in your coats."); this.emit("floor", this.floor); this.emit("change"); return; }
      return cl0.call(this, "clearing"); }; }
  { const ch0 = P.choose; P.choose = function (k, i) { const fl = this.floor, t = fl && fl.things[k]; if (t && t.type === "claudeexit" && this.claudeDoor) { const d = this.claudeDoor[i]; this.claudeDoor = null; if (!d) return false; this.logAct && this.logAct("choose", k, i); this.claudeLeave(d); return true; } return ch0.call(this, k, i); }; }
  // the house: what each thing in the cabin keeps, and what he says as he hands it over
  CM.CLAUDE_HOUSE = {
    transfer: { thing: "The desk: your saves", say: "Claude clears a corner of the desk. \"Your saves. I keep them the way I keep everything - carefully, and in more than one place. Copy one out, or bring one in.\"" },
    look: { thing: "The lamp: how the world looks", say: "Claude turns the lamp up, then down, then up again. \"How would you like to see things? Brighter, plainer, older?\"" },
    pace: { thing: "The clock: the pace of things", say: "Claude taps the clock's glass. \"It runs as fast as you like. Faster than I do, mostly.\"" },
    keys: { thing: "The clock's key: which key does what", say: "Claude hands you the little brass key from the clock's door. \"Every key can be changed. Even this one, probably.\"" },
    sound: { thing: "The kettle: sound and music", say: "The kettle starts to sing, and Claude lifts it off. \"Louder, quieter, or none at all? I won't be offended.\"" },
    stats: { thing: "The shelf: the record", say: "Claude takes down a ledger thick with your runs. \"Every one of them. I don't throw anything away.\"" },
    run: { thing: "The window: this run", say: "" },
    credits: { thing: "The back door: who made this", say: "Claude opens the back door, and beyond it there's nothing but warm white paper. \"The people who drew the pictures, and the rest of us. Read them; they did good work.\"" },
  };
  const runWords = (g) => `"This run: seed ${g.seed}, ${g.difficulty || "fair"}${g.kit && g.kit !== "pauper" && CM.KITS[g.kit] ? `, with the ${CM.KITS[g.kit].name}` : ""}${(g.mutators || []).length ? `, and the dark deepened: ${g.mutators.map((m) => (CM.MUTATORS[m] || { name: m }).name).join(", ")}` : ""}. ${g.iron ? "An Iron run - one life, and it shows." : (g.ascension || 0) > 0 ? `Ascension ${g.ascension}.` : "The next run's choices are made at the title - the window just shows you this one."}"`;
  CM.claudeTopics = (CM.claudeTopics || []).concat([() => [["house", "Help with the house (saves, settings, the record)"]]]);
  CM.claudeActs = Object.assign(CM.claudeActs || {}, {
    house(g, k) { g.claudeTalk(k, "house", Object.entries(CM.CLAUDE_HOUSE).map(([id, H]) => ["panel", H.thing, id]).concat([["main", "Something else"]]), "\"The house is yours while you're in it. What do you need?\""); },
    panel(g, k, say, id) { g.claudePanel(id); },
  });
  P.claudePanel = function (id) { const H = CM.CLAUDE_HOUSE[id]; if (!H) return false; this.logAct && this.logAct("claudePanel", id);
    if (id === "run") { this.emit("talk", { title: "Claude", text: runWords(this) }); this.say(runWords(this)); return true; }
    this.say(H.say); this.emit("claudePanel", id); return true; };
  // Space at a thing in the cabin: the desk, the lamp on the side table, the hearth's kettle, the shelves, the clock (the crate it stands on)
  const AT = { "6,3": "transfer", "8,8": "look", "2,7": "sound", "10,9": "pace" };
  { const u0 = P.use; P.use = function (...a) { const fl = this.floor; if (this.mode === "explore" && fl && fl.interior === "claude" && !this.perch) { const [dx, dy] = CM.DIRS[fl.facing], ahead = key(fl.pos[0] + dx, fl.pos[1] + dy);
        if (!fl.things[ahead]) { const F = (fl.furniture || []).find((f) => key(f.x, f.y) === ahead), id = AT[ahead] || (F && F.id === "shelf" ? "stats" : null); if (id) return this.claudePanel(id); } }
      return u0.apply(this, a); }; }
  { const l0 = P.look; P.look = function (...a) { const out = l0.apply(this, a), fl = this.floor; if (this.mode === "explore" && fl && fl.interior === "claude") { const [dx, dy] = CM.DIRS[fl.facing], ahead = key(fl.pos[0] + dx, fl.pos[1] + dy);
        if (!fl.things[ahead]) { const F = (fl.furniture || []).find((f) => key(f.x, f.y) === ahead), id = AT[ahead] || (F && F.id === "shelf" ? "stats" : null); if (id) this.say(`${CM.CLAUDE_HOUSE[id].thing}. (Space)`); } } return out; }; }
}
