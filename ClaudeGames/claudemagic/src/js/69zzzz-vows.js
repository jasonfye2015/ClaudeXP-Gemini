"use strict";
// Vows (UPGRADE_PLAN_75.md, release 1). At Claude's desk the party may swear up to three vows for the run, each held to
// the end of the next band below the deepest floor it has reached: Dry Throat (no healing draughts), No Retreat (no
// stair back up, no Return to Claude), Unbought (nothing bought), Four Together (no hero falls), Unrested (no rest at a
// camp). Reaching the vow's floor with it kept: a ring named for it, with a small gift that fits it, and Claude writes
// it into his account. Breaking it: a bad omen - the party's heart sinks - and that goes into the account too. The
// game asks once before a vow is broken by a choice (the second time, it's broken); the Automatic hand never breaks
// one; red ink voids them all. A vow sworn is a vow the run remembers: one of each kind a run.
//   CM.VOWS; game.vows() -> [{ id, to, kept, broken }]; game.swearVow(id); game.vowActive(id)
{ const P = CM.Game.prototype;
  CM.VOWS = {
    dry: { name: "Dry Throat", what: "no healing draughts", ring: { name: "Ring of the Dry Throat", props: { regen: 1 }, gift: "mends 1 a round in fights" } },
    forward: { name: "No Retreat", what: "no stair back up, no Return to Claude", ring: { name: "Band of the Forward Stair", props: { init: 1 }, gift: "+1 to the round's order" } },
    unbought: { name: "Unbought", what: "nothing bought, anywhere", ring: { name: "Ring of the Empty Purse", props: { killGold: 0.1 }, gift: "10% more gold from a fight" } },
    together: { name: "Four Together", what: "no hero falls", ring: { name: "Ring of the Four", props: { auraDf: 1 }, gift: "the whole party +1 defence" } },
    unrested: { name: "Unrested", what: "no rest at a camp", ring: { name: "Ring of the Long Watch", props: { hitBonus: 0.05 }, gift: "blows land 5% more" } },
  };
  P.vows = function () { const E = this.ext("vows"); E.list = E.list || []; return E.list; };
  const deepestOf = (g) => Math.max(0, ...((g.trail || []).map((t) => t[0] || 0)), g.floor && g.floor.number >= 1 ? g.floor.number : 0);
  CM.vowTarget = (g) => { const d = deepestOf(g), b = d < 1 ? 0 : Math.min(CM.THEMES.length - 1, CM.themeIndex(d) + 1); return CM.THEMES[b].floors[1]; };
  P.vowActive = function (id) { return this.vows().some((v) => v.id === id && !v.kept && !v.broken); };
  P.swearVow = function (id) { const V = CM.VOWS[id]; if (!V) return "No such vow."; const L = this.vows();
    if (this.redInk && this.ext && this.tally && this.redInk().used) return "\"Not on a run in red ink. A vow has to cost something, or it isn't one.\"";
    if (L.some((v) => v.id === id)) return "\"You've sworn that one already this run.\"";
    if (L.filter((v) => !v.kept && !v.broken).length >= 3) return "\"Three at once is plenty. Keep those first.\"";
    this.logAct && this.logAct("swearVow", id); const to = CM.vowTarget(this); L.push({ id, to, at: deepestOf(this) });
    if (CM.narrate) CM.narrate(this, `They swore ${V.name} - ${V.what} - to floor ${to}. I've written the vow down before anything else, so it's there whatever happens.`);
    this.emit("change"); return ""; };
  const breakVow = (g, id, why) => { const v = g.vows().find((x) => x.id === id && !x.kept && !x.broken); if (!v) return; v.broken = why || true; if (g.cheer) g.cheer(-20, "a vow broken");
    g.say(`The vow is broken: ${CM.VOWS[id].name}. The party feels it, the way you feel a step that isn't there.`); if (CM.narrate) CM.narrate(g, `${CM.VOWS[id].name}, broken${typeof why === "string" ? ` - ${why}` : ""}. I write it as plainly as the swearing.`); g.emit("change"); };
  // asked once, broken the second time
  const guard = (g, id, what) => { if (!g.vowActive(id)) return ""; if (g.autoOn && g.autoOn()) return `(The Automatic hand keeps your vow: ${CM.VOWS[id].name}.)`;
    const E = g.ext("vows"); if (E.warned !== id) { E.warned = id; return `You swore ${CM.VOWS[id].name} - ${CM.VOWS[id].what}. Do that again to break the vow.`; } delete E.warned; breakVow(g, id, what); return ""; };
  // the vows at work
  { const gv0 = P.give; P.give = function (row, n, ...a) { const it = (this.bag || [])[row]; if (it && (it.kind === "heal" || it.kind === "greaterheal")) { const note = guard(this, "dry", "a draught drunk"); if (note) return note; } return gv0.call(this, row, n, ...a); }; }
  { const b0 = P.buy; P.buy = function (row, ...a) { if (typeof row === "number") { const note = guard(this, "unbought", "something bought"); if (note) return note; } return b0.call(this, row, ...a); }; }
  { const r0 = P.rest; P.rest = function (...a) { const note = guard(this, "unrested", "a night's rest taken"); if (note) { this.say(note); return note; } return r0.apply(this, a); }; }
  { const rc0 = P.returnToClaude; if (rc0) P.returnToClaude = function (...a) { if (this.floor && this.floor.number >= 1) { const note = guard(this, "forward", "a page turned home"); if (note) { this.say(note); this.emit("change"); return false; } } return rc0.apply(this, a); }; }
  { const ef0 = P.enterFloor; P.enterFloor = function (number, how, ...a) { const from = this.floor ? this.floor.number : null;
      if (how === "up" && from !== null && from >= 1 && this.vowActive("forward") && !(this.autoOn && this.autoOn())) breakVow(this, "forward", "a stair climbed back up");
      const out = ef0.call(this, number, how, ...a);
      if (this.floor && this.floor.number >= 1 && this.tally) for (const v of this.vows()) if (!v.kept && !v.broken && this.floor.number >= v.to) { v.kept = this.floor.number; const R = CM.VOWS[v.id].ring;
        this.bag.push({ name: R.name, kind: "trinket", slot: "trinket", power: 0, value: 120, vow: v.id, props: Object.assign({ rarity: "fine" }, JSON.parse(JSON.stringify(R.props))), lore: `Kept: ${CM.VOWS[v.id].name}, to floor ${v.to}. ${R.gift.charAt(0).toUpperCase() + R.gift.slice(1)}.` });
        this.say(`The vow is kept: ${CM.VOWS[v.id].name}, all the way to floor ${v.to}. In the pack, where nothing was a moment ago: the ${R.name}.`); if (CM.narrate) CM.narrate(this, `${CM.VOWS[v.id].name}, kept. I've underlined it.`);
        const VV = this.vext("vows"); VV.kept = (VV.kept || 0) + 1; if (this.saveVillage && !this.replaying) this.saveVillage(); }
      return out; }; }
  { const em0 = P.emit; P.emit = function (ev, ...a) { if (ev === "change" && this.party && this.tally && this.vowActive && this.vowActive("together") && this.party.some((h) => h.hp <= 0)) { const h = this.party.find((x) => x.hp <= 0); breakVow(this, "together", `${h.name} fell`); }
      return em0.call(this, ev, ...a); }; }
  // red ink voids them
  { const ri0 = P.redInkDo; if (ri0) P.redInkDo = function (...a) { const out = ri0.apply(this, a); for (const v of this.vows()) if (!v.kept && !v.broken) v.broken = "red ink"; return out; }; }
  // in Claude's account
  { const ca0 = CM.claudeAccount; if (ca0) CM.claudeAccount = function (g, e, foe) { let t = ca0(g, e, foe); const L = g.vows ? g.vows() : []; if (L.length) { const kept = L.filter((v) => v.kept).map((v) => CM.VOWS[v.id].name), broke = L.filter((v) => v.broken).map((v) => CM.VOWS[v.id].name), open = L.filter((v) => !v.kept && !v.broken).map((v) => CM.VOWS[v.id].name);
        t += ` Vows: ${[kept.length ? `kept ${kept.join(", ")}` : "", broke.length ? `broken ${broke.join(", ")}` : "", open.length ? `still held ${open.join(", ")} when it ended` : ""].filter(Boolean).join("; ")}.`; } return t; }; }
  // at the desk
  CM.claudeTopics = (CM.claudeTopics || []).concat([(g) => [["vows", g.vows().some((v) => !v.kept && !v.broken) ? `Vows (${g.vows().filter((v) => !v.kept && !v.broken).length} held)` : "Swear a vow for this run"]]]);
  CM.claudeActs = Object.assign(CM.claudeActs || {}, {
    vows(g, k) { const to = CM.vowTarget(g), L = g.vows(); const opts = Object.entries(CM.VOWS).filter(([id]) => !L.some((v) => v.id === id)).map(([id, V]) => ["swear", `${V.name}: ${V.what} (to floor ${to}) - kept, the ${V.ring.name}: ${V.ring.gift}`, id]);
      const held = L.filter((v) => !v.kept && !v.broken).map((v) => `${CM.VOWS[v.id].name} to floor ${v.to}`);
      g.claudeTalk(k, "vows", opts.concat([["main", "Not today"]]), `Claude opens the account to a clean page. "${held.length ? `You hold ${held.join(", ")}. ` : ""}A vow is a thing you choose to make harder. Keep it to the floor, and I'll have something for you. Break it, and I'll write that too. Which?"`); },
    swear(g, k, say, id) { const note = g.swearVow(id); say(note || `"${CM.VOWS[id].name}. Written." He blots the page. "Go carefully - or don't. That's rather the point."`); },
  });
}
