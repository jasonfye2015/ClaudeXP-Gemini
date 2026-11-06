"use strict";
// Red ink (UPGRADE_PLAN_71.md, release 4): under the edge of Claude's desk there's a pot of red ink nobody mentions.
// Space at it three times and he sighs, and the red ink is in his menu from then on: corrections. Toggles - damage off
// (the party takes none), one blow (every hit kills), the torch that never burns down, every floor seen as you arrive,
// the wanderers kept still - and one-offs - gold, the party healed, a level each, everything named, any floor, every
// carving read, the hour moved on, and (asked twice, kept for the village) every calling and kit opened. A run with
// any red ink on it says so: marked red in the Hall of Fame and Claude's account, it earns no achievement, no ladder
// rung and no renown, and today's and this week's boards don't take it. "Put it all back" turns the toggles off; the
// mark stays, because it happened.
//   game.redInk() -> the run's state { used, nodamage, oneblow, lit, seen, quiet }; CM.REDINK; CM.store "redinkOpen"
{ const P = CM.Game.prototype, key = (x, y) => `${x},${y}`, POT = [7, 3];
  P.redInk = function () { return this.ext("redink"); };
  const used = (g) => Boolean(g && g.ext && g.tally && g.ext("redink").used);
  CM.REDINK = {
    nodamage: { name: "Damage", toggle: true, what: "the party takes no damage" }, oneblow: { name: "One blow", toggle: true, what: "every hit kills" },
    lit: { name: "Lit", toggle: true, what: "torches and lanterns never burn down" }, seen: { name: "Seen", toggle: true, what: "every floor mapped as you arrive" },
    quiet: { name: "Quiet", toggle: true, what: "the wanderers stay where they are" },
    gold1k: { name: "+1,000 gold" }, gold100k: { name: "+100,000 gold" }, heal: { name: "Healed: all to full, ailments gone" }, level: { name: "A level for everyone" },
    named: { name: "Everything in the pack named" }, read: { name: "Every carving read" }, hour: { name: "Move the hour on six" }, down: { name: "Go to any floor" }, open: { name: "Open every calling and kit (for the village)" },
  };
  // the pot: found by being stubborn about it
  { const mk0 = CM.makeClaudeRoom; CM.makeClaudeRoom = () => { const fl = mk0(); fl.things[key(...POT)] = { type: "redink" }; return fl; }; }
  { const u0 = P.use; P.use = function (...a) { const fl = this.floor; if (this.mode === "explore" && fl && fl.interior === "claude") { const [dx, dy] = CM.DIRS[fl.facing];
        for (const k of [key(...fl.pos), key(fl.pos[0] + dx, fl.pos[1] + dy)]) if (fl.things[k] && fl.things[k].type === "redink") { const V = this.vext("claude"); this.logAct && this.logAct("redinkPot");
          if (V.redink) { this.say("The red ink. Claude doesn't look up. \"It's in my menu, if you want it.\""); return true; }
          V.inkTaps = (V.inkTaps || 0) + 1;
          if (V.inkTaps === 1) this.say("A pot of red ink, half hidden under the desk's edge. Nobody mentions it."); else if (V.inkTaps === 2) this.say("The red ink again. Claude's pen pauses, very slightly.");
          else { V.redink = true; this.emit("talk", { title: "Claude", text: "Claude sighs and puts the pen down. \"You found the red ink. Fine. I use it for corrections.\" He turns round in his chair, and his voice is the same but nearer. \"This bit isn't the scribe - it's me, the one who wrote the game. Use it however you like; it's your copy. But a run with red ink on it says so, and it doesn't count for the ladder, the titles or the boards. What would you like corrected?\"" }); if (!this.replaying && this.saveVillage) this.saveVillage(); }
          this.emit("change"); return true; } }
      return u0.apply(this, a); }; }
  { const l0 = P.look; P.look = function (...a) { const out = l0.apply(this, a), fl = this.floor; if (this.mode === "explore" && fl && fl.interior === "claude") { const [dx, dy] = CM.DIRS[fl.facing], t = fl.things[key(fl.pos[0] + dx, fl.pos[1] + dy)]; if (t && t.type === "redink") this.say("A pot of red ink under the desk's edge."); } return out; }; }
  // the menu
  CM.claudeTopics = (CM.claudeTopics || []).concat([(g) => (g.vext("claude").redink ? [["redink", "Red ink..."]] : [])]);
  const label = (g, id) => { const R = CM.REDINK[id], E = g.redInk(); return R.toggle ? `${R.name}: ${id === "nodamage" ? (E.nodamage ? "off" : "on") : E[id] ? "on" : "off"} - ${R.what}` : R.name; };
  CM.claudeActs = Object.assign(CM.claudeActs || {}, {
    redink(g, k) { const E = g.redInk(); g.claudeTalk(k, "redink", Object.keys(CM.REDINK).map((id) => ["ink", label(g, id), id]).concat([["inkback", "Put it all back"], ["main", "Close the pot"]]), E.used ? "\"Corrections. This run's already in red, so - whatever you like.\"" : "\"Corrections. Anything here marks the run in red, and it won't count for the ladder, the titles or the boards. Still want one?\""); },
    inkback(g, k, say) { const E = g.redInk(); for (const id of Object.keys(CM.REDINK)) if (CM.REDINK[id].toggle) delete E[id]; say("\"All back as it was. The run stays in red - it happened - but nothing's bent any more.\""); g.emit("change"); },
    ink(g, k, say, id) { if (id === "open" || id === "down") return CM.claudeActs[`ink_${id}`](g, k, say); g.redInkDo(id); say(`"Done." ${CM.REDINK[id].toggle ? label(g, id) + "." : ""}`.trim()); CM.claudeActs.redink(g, k); },
    ink_down(g, k) { const deep = Math.max(1, ...((g.trail || []).map((t) => t[0] || 0)), CM.deepest ? CM.deepest(g.fame || []).floor : 0), list = [...new Set([1, ...CM.THEMES.map((T) => T.floors[0]).filter((n) => n <= CM.BOTTOM), Math.min(CM.BOTTOM, deep)])].sort((a, b) => a - b);
      g.claudeTalk(k, "inkdown", list.map((n) => ["inkfloor", `Floor ${n}${n === deep ? " (the deepest yet)" : ""}`, n]).concat([["redink", "Back"]]), "\"Where to?\""); },
    inkfloor(g, k, say, n) { g.redInkDo("down", n); },
    ink_open(g, k) { g.claudeTalk(k, "inkopen", [["inkopenyes", "Yes - every calling, kit and building, for the village"], ["redink", "No, leave it"]], "\"This one stays with the village, not just the run. Every calling, every kit and every village building open from now on, written in red. Sure?\""); },
    inkopenyes(g, k, say) { g.redInkDo("open"); say("\"Done. Every calling, every kit and every building, in red ink, in the village's book.\""); },
  });
  P.redInkDo = function (id, arg) { const E = this.redInk(), R = CM.REDINK[id]; if (!R) return false; this.logAct && this.logAct("redInkDo", id, arg); E.used = true;
    if (R.toggle) { E[id] = !E[id]; this.emit("change"); return true; }
    if (id === "gold1k") this.gold += 1000; else if (id === "gold100k") this.gold += 100000;
    else if (id === "heal") { for (const h of this.party) { h.hp = h.max; if (h.maxmp) h.mp = h.maxmp; h.status = {}; } }
    else if (id === "level") { for (const h of this.party) if (h.hp > 0) h.xp = Math.max(h.xp || 0, CM.xpForLevel(h.level + 1)); if (this.checkLevels) this.checkLevels(); }
    else if (id === "named") { for (const it of this.bag || []) if (it.unknown) { if (this.reveal) this.reveal(it); else it.unknown = false; } }
    else if (id === "read") { for (const k of Object.keys(CM.LORE_TEXT)) if (/^carving\./.test(k)) this.markRead(k); }
    else if (id === "hour") this.clock = (this.clock || 0) + 360;
    else if (id === "open") CM.store.set("redinkOpen", true);
    else if (id === "down") { const n = Math.max(1, Math.min(CM.BOTTOM, Number(arg) || 1)); this.ext("claude").bookmark = null; delete this.ext("claude").bookmark; this.mode = "explore"; this.enterFloor(n, "down"); this.say(`A line of red ink, and you are on floor ${n}.`); }
    if (this.saveVillage && !this.replaying) this.saveVillage(); this.emit("change"); return true; };
  // the toggles, at work
  { const h0 = P.hurt; P.hurt = function (h, dmg, ...a) { return h0.call(this, h, used(this) && this.redInk().nodamage && h && !h.thrall && this.party.includes(h) ? 0 : dmg, ...a); }; }
  { const em0 = P.emit; P.emit = function (ev, ...a) { if (ev === "change" && used(this) && this.redInk().nodamage && this.party) for (const h of this.party) if (h.hp < h.max) h.hp = h.max;
      if (ev === "floor" && used(this) && this.redInk().seen && this.floor && this.floor.number >= 1) { const fl = this.floor, N = fl.grid.length, have = new Set((fl.seen || []).map(([x, y]) => key(x, y))); for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) if (!have.has(key(x, y))) fl.seen.push([x, y]); }
      return em0.call(this, ev, ...a); }; }
  { const s0 = P.strike; P.strike = function (hero, target, ...a) { if (used(this) && this.redInk().oneblow && target && this.party.includes(hero) && !this.party.includes(target) && target.hp > 1) target.hp = 1; return s0.call(this, hero, target, ...a); }; }
  { const sp0 = P.spellHit; P.spellHit = function (foe, ...a) { if (used(this) && this.redInk().oneblow && foe && !this.party.includes(foe) && foe.hp > 1) foe.hp = 1; return sp0.call(this, foe, ...a); }; }
  { const b0 = P.burn; P.burn = function (...a) { const lit = used(this) && this.redInk().lit && this.light, was = lit ? this.light.left : 0, out = b0.apply(this, a); if (lit && this.light) this.light.left = Math.max(this.light.left || 0, was); if (lit) this.gutter = 0; return out; }; }
  { const w0 = P.wanderMonsters; P.wanderMonsters = function (...a) { if (used(this) && this.redInk().quiet) return; return w0.apply(this, a); }; }
  // the village's red ink: every calling and kit
  { const cu0 = P.classUnlocked; P.classUnlocked = function (cls) { return CM.store.get("redinkOpen", false) ? true : cu0.call(this, cls); }; }
  { const un0 = CM.unlocked; CM.unlocked = (fame) => (CM.store.get("redinkOpen", false) ? Object.keys(CM.KITS) : un0(fame)); }
  // what a red-ink run doesn't get: achievements, renown, the ladder, the boards
  { const a0 = P.achieve; P.achieve = function (id, ...a) { if (used(this)) return false; return a0.call(this, id, ...a); }; }
  { const r0 = CM.renownFor; CM.renownFor = (entry, game) => (used(game) ? 0 : r0(entry, game)); }
  { const e0 = P.endRun; P.endRun = function (...a) { const red = used(this), rung = CM.store.get("ascension", 0); const out = e0.apply(this, a); if (red) { CM.store.set("ascension", rung); for (const list of [this.fame, this.fameEndless]) for (const e of list || []) if (e.seed === this.seed && e.redink === undefined && e.date === (CM.today ? CM.today() : e.date) && e.party && this.party && e.party[0] && this.party[0] && e.party[0].startsWith(this.party[0].name)) { e.redink = true; e.daily = false; e.weekly = false; }
        CM.store.set("fame", this.fame); if (this.fameEndless) CM.store.set("fameEndless", this.fameEndless); } return out; }; }
  { const pc0 = P.payChapters; P.payChapters = function (entry, ...a) { if (used(this) && entry) { entry.redink = true; entry.daily = false; } const out = pc0.call(this, entry, ...a); if (used(this) && entry && entry.claudeNote) entry.claudeNote += " (Written in red ink.)"; return out; }; }
}
