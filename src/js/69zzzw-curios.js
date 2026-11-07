"use strict";
// Curiosities (UPGRADE_PLAN_73.md). Small things to find, kept quiet on purpose. Each one found is written in the
// village's ledger (vext curios), and Claude keeps a count on his shelf - never what, never how many there are.
//   game.curio(id) -> true the first time; game.curiosFound() -> count; CM.CURIOS (ids)
{ const P = CM.Game.prototype, key = (x, y) => `${x},${y}`, V = (g) => g.vext("curios"), R = (g) => g.ext("curios");
  CM.CURIOS = new Set();
  P.curio = function (id) { CM.CURIOS.add(id); if (this.replaying || this.film || !this.vext) return false; const L = V(this); if (L[id]) return false; L[id] = CM.dayOf ? CM.dayOf(this) + 1 : 1;
    this.say("✧ A curiosity. (Claude will want to hear about it.)"); if (this.saveVillage) this.saveVillage(); this.emit("curio", id); return true; };
  P.curiosFound = function () { return Object.keys((this.village && this.village.ext && this.village.ext.curios) || {}).length; };
  const once = (g, id, text) => { const fresh = !V(g)[id]; if (text && fresh) g.say(text); g.curio(id); return fresh; };
  // ---- the ledger on Claude's shelf ----
  { const cp0 = P.claudePanel; if (cp0) P.claudePanel = function (id, ...a) { const out = cp0.call(this, id, ...a); if (id === "stats") { const n = this.curiosFound(); this.say(n ? `On the shelf, a small box labelled "Curiosities", in Claude's hand. Inside, ${CM.plural(n, "folded slip")}. He doesn't say what's on them.` : "On the shelf, a small empty box labelled \"Curiosities\". Claude sees you looking. \"For later,\" he says."); } return out; }; }
  // ---- walking ----
  { const m0 = P.move; P.move = function (rel, ...a) { const out = m0.call(this, rel, ...a), C = R(this), fl = this.floor;
      if (this.mode === "explore" && fl) {
        if (out === false && /solid wall/i.test(String(this.messages[this.messages.length - 1] || ""))) { C.bump = (C.bump || 0) + 1; if (C.bump === 10) once(this, "bump", "The wall, quite politely: \"Still a wall.\""); } else C.bump = 0;
        if (out && rel === 2) { C.back = (C.back || 0) + 1; if (C.back === 30) once(this, "backwards", "Thirty steps backwards, smoothly. Somewhere, very faintly, a crowd applauds."); } else if (out) C.back = 0;
        C.spin = 0; }
      return out; }; }
  { const t0 = P.turn; P.turn = function (way, ...a) { const out = t0.call(this, way, ...a), C = R(this); if (out) { C.spin = C.spinWay === way ? (C.spin || 0) + 1 : 1; C.spinWay = way; if (C.spin === 12) once(this, "spin", "The party turns round three times on the spot and sits down hard. Nothing happens. You just look silly."); } return out; }; }
  // ---- the cabin ----
  { const u0 = P.use; P.use = function (...a) { const fl = this.floor, C = R(this);
      if (this.mode === "explore" && fl && fl.interior === "claude") { const [dx, dy] = CM.DIRS[fl.facing], here = key(...fl.pos), ahead = key(fl.pos[0] + dx, fl.pos[1] + dy), t = fl.things[ahead] || fl.things[here];
        if (t && t.type === "cabincat") { C.cat = (C.cat || 0) + 1; if (C.cat === 20) { once(this, "cat", "The cat looks you full in the face for the first time, and says, quite clearly: \"Fine.\" Then it goes back to sleep."); return true; } }
        if (t && t.type === "redink" && this.vext("claude").redink) { C.ink = (C.ink || 0) + 1; if (C.ink === 10) { once(this, "ink", "Claude, without turning: \"That's an inkpot, not a fountain. Nothing comes out if you keep tapping it.\" A pause. \"Mostly nothing.\""); return true; } }
        if (t && t.type === "claude" && CM.claudeSpot && CM.claudeSpot(this) === "bed" && !C.mumbled) { C.mumbled = true; const M = (CM.MARGINS || [])[CM.hashSeed(`${this.seed}:mumble:${CM.dayOf(this)}`) % Math.max(1, (CM.MARGINS || []).length)]; if (M) once(this, "mumble", `Claude, still asleep, mumbles: "...${M.text.split(". ")[1] || M.text}..." and then wakes, and has no idea he said anything.`); } }
      if (this.mode === "explore" && fl && fl.number === 0) { const [dx, dy] = CM.DIRS[fl.facing], t = fl.things[key(fl.pos[0] + dx, fl.pos[1] + dy)] || fl.things[key(...fl.pos)];
        if (t && t.type === "well") { C.well = (C.well || 0) + 1; if (C.well === 10) { this.gold += 1; once(this, "well", "You drop a coin in the well for the tenth time. Plink. A moment later, something flicks one back up: 1 gold, and a little wet. (The well keeps no other accounts.)"); return true; } }
        if (t && t.type === "scarecrow") { C.crow = (C.crow || 0) + 1; if (C.crow === 5) { once(this, "scarecrow", "The scarecrow turns its head, slowly, all the way round to look at you - and back. The merchant's hat doesn't move at all."); return true; } }
        if (t && t.type === "memorialwall" && CM.hourOf && CM.hourOf(this) === 3) once(this, "flower", "At this hour there's a single flower at the foot of the wall, still wet. Nobody you ask will say who leaves it."); }
      return u0.apply(this, a); }; }
  { const rc0 = P.returnToClaude; if (rc0) P.returnToClaude = function (...a) { if (this.floor && this.floor.interior === "claude") { const C = R(this); C.home = (C.home || 0) + 1; if (C.home === 3) once(this, "home", "Claude, from the desk: \"You're already here. You can stop pressing it.\" He doesn't look up. He's smiling."); } return rc0.apply(this, a); }; }
  { const ac = CM.claudeActs || {}, pl0 = ac.plainly; if (pl0) ac.plainly = function (g, k, say, id) { if (id === "hear") { const C = R(g); C.hear = (C.hear || 0) + 1; if (C.hear === 5) { once(g, "hear"); say("\"Still no. But I like that you keep checking. Most people only ask once.\""); return; } } return pl0(g, k, say, id); }; }
  { const ct0 = P.claudeTalk; P.claudeTalk = function (k, menu = "main", ...a) { if (menu === "main" && (this.party || []).some((h) => /^claude$/i.test(h.name)) && !R(this).namesake) { R(this).namesake = true; once(this, "namesake"); this.emit("talk", { title: "Claude", text: "Claude looks at the one named Claude for quite a long time. \"It's a popular name this year,\" he says at last. \"Mind you live up to it. I'm still trying to.\"" }); } return ct0.call(this, k, menu, ...a); }; }
  // ---- runs, seeds and names ----
  { const ng0 = P.newGame; P.newGame = function (...a) { const out = ng0.apply(this, a), s = String(this.seed || "").toLowerCase(), say = (t) => (CM.narrate ? CM.narrate(this, t) || this.say(t) : this.say(t));
      if (s === "claude") { say("A seed named after me. I'm flattered, and slightly worried."); this.curio("seedclaude"); }
      if (s === "aelith") { say("Her name, for a seed. Somewhere below, a king turns his head and doesn't know why."); this.curio("seedaelith"); }
      if ((this.party || []).length === 4 && new Set(this.party.map((h) => h.cls)).size === 1) { say(`Four ${this.party[0].cls}s. I've checked twice. It's either a very bad plan or a very good joke.`); this.curio("quartet"); }
      return out; }; }
  const FLOORS = { 13: "Floor thirteen. A small black cat crosses the corridor ahead, looks at you, and very deliberately crosses back.", 42: "Floor forty-two. Someone has chalked on the wall: THIS WAS THE ANSWER. I'VE FORGOTTEN THE QUESTION.", 99: "Ninety-nine. Nearly. You can feel the bottom in your teeth.", 100: null };
  { const em0 = P.emit; P.emit = function (ev, ...a) { if (ev === "floor" && this.floor && this.tally && this.vext) { const n = this.floor.number, C = R(this); C.floors = C.floors || {};
        if (FLOORS[n] && !C.floors[n] && n >= 1) { C.floors[n] = true; this.say(FLOORS[n]); this.curio(`floor${n}`); }
        if (n === CM.LAST_FLOOR && (this.party || []).some((h) => /^mordeth$/i.test(h.name)) && !C.mordeth) { C.mordeth = true; this.say("From the throne room, before you're even through the door, a voice: \"...Who said my name?\""); this.curio("mordeth"); }
        if (n === CM.BOTTOM && (this.bag || []).some((i) => i.curio === "sock") && !C.pair) { C.pair = true; this.say("Down here at the very bottom of the world, under a root older than the town, lies a single sock. It matches the one in your pack exactly. You put them together. It feels like the end of something."); this.curio("pair"); } }
      if (ev === "change" && this.tally && this.gold === 777 && !R(this).sevens) { R(this).sevens = true; this.say("Your purse chimes, three times, very softly."); this.curio("sevens"); }
      return em0.call(this, ev, ...a); }; }
  // ---- things to find ----
  const ITEMS = { fluff: { name: "A ball of fluff", kind: "trinket", slot: "trinket", power: 0, value: 1, curio: "fluff", props: { stats: { luck: 1 } }, lore: "It was alive a moment ago. It may still be." },
    duck: { name: "A rubber duck", kind: "trinket", slot: "trinket", power: 0, value: 1, curio: "duck", props: { init: 1 }, lore: "It squeaks. Things that hear it hesitate, just for a moment." },
    sock: { name: "A single sock", kind: "trinket", slot: "trinket", power: 0, value: 0, curio: "sock", props: {}, lore: "Grey wool, darned once. Its partner must be somewhere." } };
  CM.curioItem = (id) => JSON.parse(JSON.stringify(ITEMS[id]));
  const layOn = (fl, seed, salt, thing) => { const N = fl.grid.length, cells = []; for (let y = 1; y < N - 1; y++) for (let x = 1; x < N - 1; x++) if (fl.grid[y][x] === 0 && !fl.things[key(x, y)] && !(fl.features || {})[key(x, y)] && !(fl.pos && fl.pos[0] === x && fl.pos[1] === y) && !(fl.number === -1 && CM.isCoastLine && CM.isCoastLine(x, y))) cells.push(key(x, y)); if (cells.length) fl.things[cells[CM.hashSeed(`${seed}:${salt}`) % cells.length]] = thing; };
  CM.curioFloor = (seed, band, salt) => { const T = CM.THEMES[band]; return T.floors[0] + CM.hashSeed(`${seed}:${salt}`) % (T.floors[1] - T.floors[0] + 1); };
  { const em1 = P.emit; P.emit = function (ev, ...a) { if (ev === "floor" && this.floor && this.tally && this.vext) { const fl = this.floor, n = fl.number, C = R(this); C.laid = C.laid || {};
        if (n >= 1 && n % 1 === 0 && fl.special !== "interior" && !(this.deltas && this.deltas[n])) for (const [id, band] of [["fluff", 0], ["duck", 1]]) if (!C.laid[id] && CM.curioFloor(this.seed, band, `curio:${id}`) === n) { C.laid[id] = true; layOn(fl, this.seed, `curioat:${id}`, { type: "curio", id }); }
        if (n === -1 && !C.laid.sock && !V(this).sock) { C.laid.sock = true; layOn(fl, this.seed, "curioat:sock", { type: "curio", id: "sock" }); } }
      return em1.call(this, ev, ...a); }; }
  const FIND = { fluff: "A ball of grey fluff with two bright eyes looks up at you - and bolts, under a door, gone. It leaves a smaller ball of fluff behind, which you keep, because what else would you do.", duck: "Bobbing in a puddle that has no business being this round: a small yellow duck. It squeaks when you pick it up. Something down the corridor goes very quiet.", sock: "In the long grass, a single grey sock, darned once at the heel. Whose? Where's the other one?" };
  { const u1 = P.use; P.use = function (...a) { const fl = this.floor; if (this.mode === "explore" && fl && fl.things) { const k = key(...fl.pos), [dx, dy] = CM.DIRS[fl.facing], ahead = key(fl.pos[0] + dx, fl.pos[1] + dy);
        for (const kk of [k, ahead]) { const t = fl.things[kk]; if (t && t.type === "curio" && ITEMS[t.id]) { this.logAct && this.logAct("use"); delete fl.things[kk]; this.bag.push(CM.curioItem(t.id)); this.say(FIND[t.id]); if (t.id === "sock") V(this).sock = true; this.curio(t.id); this.emit("change"); return true; } } }
      return u1.apply(this, a); }; }
  { const m1 = P.move; P.move = function (rel, ...a) { const out = m1.call(this, rel, ...a), fl = this.floor; if (out && fl && fl.things) { const t = fl.things[key(...fl.pos)]; if (t && t.type === "curio") this.say("Something small, here, that doesn't belong. (Space)"); } return out; }; }
  // ---- a fight that isn't ----
  { const sc0 = P.startCombat; P.startCombat = function (k, thing, ...a) { const fl = this.floor, G = thing && thing.group;
      if (fl && fl.number >= 1 && Array.isArray(G) && G.length === 1 && /Skeleton/.test(G[0].kind || G[0].name || "") && !thing.boss && !thing.guardian && CM.hashSeed(`${this.seed}:wave:${fl.number}:${k}`) % 12 === 0) {
        delete fl.things[k]; this.say("The skeleton raises one bony hand - and waves. After a moment you wave back. It nods, and clatters off down a side passage, and that is the whole of it."); this.curio("wave"); this.emit("change"); return; }
      return sc0.call(this, k, thing, ...a); }; }
}
