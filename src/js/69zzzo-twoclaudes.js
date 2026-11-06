"use strict";
// The two Claudes, and the scribe of your runs (UPGRADE_PLAN_70.md, release 3). With the Margins home, Claude has
// worked out what the king needs to hear, and writes him a letter in his own old hand: carried down to the throne, it
// answers one thing the party can't when the king asks to be reminded - a sixth line for any one gap in the five.
// After the ending Claude hears of it, either way. When a run ends after the party has met him, Claude writes a short
// true account of it, kept at the desk and in the Hall of Fame as "Claude's note". After a guardian falls a letter from
// him is waiting at home; and the regular at the Hanged Lantern mentions "the one with the quill, out past the farm".
//   CM.claudeAccount(game, entry, foe) -> text; CM.KING_LETTER; item kind "kingletter"
{ const P = CM.Game.prototype;
  CM.KING_LETTER = { name: "Claude's letter to the king", kind: "kingletter", power: 0, value: 0 };
  const hasLetter = (g) => (g.bag || []).some((i) => i.kind === "kingletter");
  // ---- the letter, at the throne: one gap answered ----
  { const ar0 = P.askRemind; P.askRemind = function (k, thing) { const R = CM.REMIND[thing.remind || 0], have = this.story && this.story.read[R.key] !== undefined;
      if (have || thing.letterUsed || !hasLetter(this)) return ar0.call(this, k, thing);
      this.emit("choice", { k, title: CM.BOSS.name, text: R.ask, options: ["Give him Claude's letter", "Say nothing"], parley: true, remind: true }); }; }
  { const an0 = P.answerRemind; P.answerRemind = function (k, thing, i) { const step = thing.remind || 0, R = CM.REMIND[step], have = this.story && this.story.read[R.key] !== undefined;
      if (have || thing.letterUsed || !hasLetter(this) || i !== 0) return an0.call(this, k, thing, i);
      thing.letterUsed = true; this.bag.splice(this.bag.findIndex((it) => it.kind === "kingletter"), 1); this.ext("claude").letterGiven = true;
      const read = `The king takes the letter, and stops. The hand is his own - his own, from before, round and careful, the way he wrote at twenty. He reads it with his lips moving. "${R.say}" it says, among a great deal else. ${R.back}`;
      this.say(read); thing.remind = step + 1;
      if (thing.remind < CM.REMIND.length) { this.emit("talk", { title: CM.BOSS.name, text: read }); this.askRemind(k, thing); return true; }
      this.emit("talk", { title: CM.BOSS.name, text: read }); this.quietEnd(k, thing); return true; }; }
  // ---- the account of a run, from its real tally ----
  CM.claudeAccount = function (g, e, foe) { const names = (g.party || []).map((h) => h.name), t = e.tally || {}, T = CM.themeFor(Math.max(1, e.floor)), out = [];
    const who = names.length > 1 ? `${names.slice(0, -1).join(", ")} and ${names[names.length - 1]}` : names[0] || "Someone";
    out.push(`${who} went down${e.date ? ` on ${e.date}` : ""}.`);
    if (e.floor >= 1) out.push(`They reached floor ${e.floor}${T && T.name ? `, in ${T.name}` : ""}.`); else out.push("They didn't go far below, and I don't think less of them for it.");
    if (t.kills) out.push(`${CM.plural(t.kills, "thing")} fell to them${t.guardians && t.guardians.length ? `, ${t.guardians.length === 1 ? "a guardian among them" : `${t.guardians.length} guardians among them`}` : ""}.`);
    if (e.reminded) out.push("At the bottom they didn't fight him. They reminded him who he was, and he sat down. I have waited a long time to write that sentence.");
    else if (e.won) out.push("At the bottom they fought him, and won. I'd hoped for the other way. Then I'll write it down this way. Truthfully.");
    else if (g.party && g.party.every((h) => h.hp <= 0)) out.push(foe ? `They didn't come back. It was ${/^the /i.test(foe.name) ? foe.name : `a ${String(foe.name).toLowerCase()}`}, on floor ${e.floor}. I've written their names on the wall at the top of the shaft, with the others.` : `They didn't come back from floor ${e.floor}. I've written their names on the wall at the top of the shaft, with the others.`);
    else if (e.left || (g.floor && g.floor.number <= 0)) { const fell = (g.party || []).filter((h) => h.hp <= 0).map((h) => h.name); out.push(fell.length ? `They came back up - not all of them. ${fell.join(" and ")} stayed below.` : "They came back up on their own feet, which is the best way to come back."); }
    else { const fell = (g.party || []).filter((h) => h.hp <= 0).map((h) => h.name); out.push(`The account stops on floor ${e.floor}${fell.length ? `, with ${fell.join(" and ")} already fallen` : ""}. I don't know how it ended, and I won't guess.`); }
    return out.join(" "); };
  { const pc0 = P.payChapters; P.payChapters = function (entry, ...a) { const out = pc0.call(this, entry, ...a), V = this.vext("claude");
      if (V.met && entry && !this.replaying && !this.film) { const foe = this.mode === "combat" && Array.isArray(this.foes) ? this.foes.filter((m) => m && m.hp > 0 && !m.summoned).sort((x, y) => (y.max || 0) - (x.max || 0))[0] || null : null;
        const text = CM.claudeAccount(this, entry, foe); entry.claudeNote = text; V.accounts = (V.accounts || []).concat({ date: entry.date || "", floor: entry.floor, text }).slice(-12);
        if (entry.won) V.kingNews = entry.reminded ? "reminded" : "fought"; }
      return out; }; }
  // ---- at the cabin: the letter, the accounts, the news ----
  CM.claudeTopics = (CM.claudeTopics || []).concat([
    (g) => { const V = g.vext("claude"); return g.marginsPinned && g.marginsPinned().length === 10 && V.kingNews !== "reminded" && !hasLetter(g) ? [["kingletter", V.letterWritten ? "Would you write the letter again?" : "You said you'd worked something out"]] : []; },
    (g) => ((g.vext("claude").accounts || []).length ? [["accounts", "What did you write about us?"]] : []),
  ]);
  CM.claudeActs = Object.assign(CM.claudeActs || {}, {
    kingletter(g, k, say) { const V = g.vext("claude"), again = V.letterWritten; V.letterWritten = true; g.bag.push(Object.assign({}, CM.KING_LETTER));
      say(again ? "Claude writes it out again, faster this time, in a round careful hand that isn't his own. \"Same as before. If you can't find the words when he asks, give him this. It'll answer once.\"" : "Claude takes a sealed letter down from behind the clock. \"I've worked out what he needs. He doesn't need to be told who he was - he needs to recognise it. So I wrote to him in his own hand. The way he wrote at twenty; it's on the oldest walls, if you look. When he asks you something you can't answer, give him this. It will answer once. After that it's up to you.\"");
      g.emit("change"); },
    accounts(g, k) { const A = (g.vext("claude").accounts || []).slice().reverse().slice(0, 6); g.claudeTalk(k, "accounts", A.map((a, i) => ["account", `${a.date || "A run"}: floor ${a.floor}`, i]).concat([["main", "Something else"]]), "\"I write each one down. Not the songs - what happened. Which?\""); },
    account(g, k, say, i) { const A = (g.vext("claude").accounts || []).slice().reverse(); if (A[i]) g.emit("talk", { title: "Claude's account", text: A[i].text }); },
  });
  const NEWS = { reminded: "Claude is on his feet before you're through the door. \"I heard. They say he sat down. They say he said her name.\" He has to stop for a moment. \"Thank you. I'm going to pin the last page now - the one I hadn't written yet.\"",
    fought: "Claude looks up when you come in, and you can see he's heard. \"You fought him.\" He nods slowly. \"I'm not angry. I'd hoped for the other way, that's all. Then I'll write it down that way. Truthfully.\"" };
  { const ct0 = P.claudeTalk; P.claudeTalk = function (k, menu = "main", ...a) { const V = this.vext("claude");
      if (menu === "main" && V.kingNews && V.kingTold !== V.kingNews) { V.kingTold = V.kingNews; if (V.kingNews === "reminded") V.lastPage = true; this.emit("talk", { title: "Claude", text: NEWS[V.kingNews] }); if (!this.replaying && this.saveVillage) this.saveVillage(); }
      return ct0.call(this, k, menu, ...a); }; }
  // ---- home: a letter from Claude after a guardian falls ----
  { const wl0 = P.writeLetters; if (wl0) P.writeLetters = function (...a) { const T = this.trip ? this.trip() : null, gs = T && T.guardians ? T.guardians.slice() : [], out = wl0.apply(this, a), V = this.vext("claude");
      if (gs.length && V.met && !this.replaying && !this.film) { const L = this.letters(), g0 = gs[0];
        const ltr = { hero: "Claude", cls: "Scribe", date: CM.today ? CM.today() : "", day: CM.dayOf ? CM.dayOf(this) : 0, to: "the party", text: `To all four of you - I heard about ${g0}. Well done, and I mean it; I've written it down already, in ink. A question, since you'll have been closer than anyone has: what was it like, at the end? Not the fight. The moment after. Come and tell me, if you want to. The kettle's on. - C.` };
        L.push(ltr); while (L.length > 80) L.shift(); if (this.saveVillage) this.saveVillage(); this.say("And a letter waiting at the door, sealed with a little quill: Claude has heard about " + g0 + ". (The Journal keeps it.)"); }
      return out; }; }
  // ---- the tavern: the regular has heard of him ----
  { const go0 = P.gossip; if (go0) P.gossip = function (...a) { const before = this.gossiped, out = go0.apply(this, a); if (!before && this.gossiped && !this.vext("claude").met) this.say("\"And there's the one with the quill, out past the farm - a path off the road, south, if you look for it. Keeps a lamp lit all night. Harmless. Asks a lot of questions.\""); return out; }; }
}
