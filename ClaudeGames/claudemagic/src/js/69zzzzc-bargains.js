"use strict";
// The king's bargains (UPGRADE_PLAN_75.md, release 3). Three times a run the Lich King makes an offer - a letter
// sealed with a black crown, waiting the first time the party reaches the floor - each a real gain with a real cost,
// both said plainly before anything is taken: the Short Stair on floor 18 (five floors down at once; every torch burns
// half again as fast for the rest of the run), Strength from the Throne on floor 36 (a level for every hero standing;
// every hero's greatest health a tenth less for the rest of the run), and the King's Answer on floor 53 (one thing the
// king will ask, answered for you; but Claude will not walk down with a party that has bargained, so no Last Page).
// Refusing is always there, and the party's heart lifts a little for it. Claude writes every bargain into his account.
//   CM.BARGAINS; game.bargains() -> { id: "taken" | "refused" }; game.bargain(id, take)
{ const P = CM.Game.prototype;
  CM.BARGAINS = {
    stair: { floor: 18, name: "the Short Stair", gain: "five floors down, now", cost: "every torch burns half again as fast for the rest of the run" },
    strength: { floor: 36, name: "Strength from the Throne", gain: "a level for every hero standing", cost: "every hero's greatest health a tenth less for the rest of the run" },
    answer: { floor: 53, name: "the King's Answer", gain: "one thing the king will ask you at the end, answered for you", cost: "Claude will not walk down with a party that has bargained - no Last Page this run" },
  };
  P.bargains = function () { return this.ext("bargains"); };
  const any = (g) => Object.values(g.bargains()).includes("taken");
  P.bargain = function (id, take) { const B = CM.BARGAINS[id], E = this.bargains(); if (!B || E[id]) return false; this.logAct && this.logAct("bargain", id, take); E[id] = take ? "taken" : "refused";
    if (!take) { if (this.cheer) this.cheer(8, "the king refused"); this.say(`You put the letter in the brazier. The black wax spits once. ${B.name}, refused.`); if (CM.narrate) CM.narrate(this, `They said no to ${B.name}. I like this party.`); this.emit("change"); return true; }
    if (id === "stair") { const n = Math.min(CM.LAST_FLOOR - 1, (this.floor ? this.floor.number : B.floor) + 5); this.say("The letter crumbles, and the floor tilts, and you are standing five floors lower than you were, a little sick."); this.enterFloor(n, "down"); }
    if (id === "strength") { for (const h of this.party) if (h.hp > 0) h.xp = Math.max(h.xp || 0, CM.xpForLevel(h.level + 1)); if (this.checkLevels) this.checkLevels(); for (const h of this.party) { h.max = Math.max(1, Math.floor(h.max * 0.9)); h.hp = Math.min(h.hp, h.max); } this.say("Something cold goes into each of them, and each is stronger for it, and a little less of each comes back."); }
    if (id === "answer") { const R = (CM.REMIND || []).find((r) => !(this.story && this.story.read[r.key] !== undefined)); if (R && this.markRead) this.markRead(R.key); this.say(R ? "The letter holds a single line, in the king's own old hand, and you understand that you will know what to say when he asks it." : "The letter is blank. You already knew everything he would have told you."); }
    if (CM.narrate) CM.narrate(this, `They took ${B.name}. I've written down the price as well as the gift; the king never does.`);
    this.emit("change"); return true; };
  // the offer, the first time the floor is reached
  { const em0 = P.emit; P.emit = function (ev, ...a) { if (ev === "floor" && this.floor && this.tally && this.mode !== "title") { const n = this.floor.number, E = this.bargains();
        for (const [id, B] of Object.entries(CM.BARGAINS)) if (n === B.floor && !E[id] && !E[`offered:${id}`] && !(this.autoOn && this.autoOn())) { E[`offered:${id}`] = true;
          this.emit("choice", { k: `bargain:${id}`, title: "A letter, sealed with a black crown", text: `Waiting on the stair, a letter in a hand that was once a king's: "${B.name.charAt(0).toUpperCase() + B.name.slice(1)}. ${B.gain.charAt(0).toUpperCase() + B.gain.slice(1)}." Under it, smaller, in Claude's hand on a slip pinned to it: "The price: ${B.cost}."`, options: [`Take it: ${B.gain}; the price, ${B.cost}`, "Burn it"] }); } }
      return em0.call(this, ev, ...a); }; }
  { const ch0 = P.choose; P.choose = function (k, i) { if (typeof k === "string" && k.startsWith("bargain:")) return this.bargain(k.slice(8), i === 0); return ch0.call(this, k, i); }; }
  // the prices
  { const b0 = P.burn; P.burn = function (...a) { const L = this.light, before = L && L.kind === "torch" ? L.left : null, out = b0.apply(this, a); if (before !== null && this.light === L && this.bargains().stair === "taken" && L.left < before) { const E = this.bargains(); E.ember = (E.ember || 0) + (before - L.left) * 0.5; while (E.ember >= 1 && L.left > 0) { L.left -= 1; E.ember -= 1; } } return out; }; }
  { const wk0 = CM.claudeActs && CM.claudeActs.walk; if (wk0) CM.claudeActs.walk = function (g, k, say, ...a) { if (any(g)) { say("Claude looks at you for a long moment, and doesn't reach for his coat. \"You've had a letter from him. I can smell the wax. I'm sorry - I can't walk down beside that. Not this time.\""); return; } return wk0(g, k, say, ...a); }; }
  { const qe0 = P.quietEnd; if (qe0) P.quietEnd = function (...a) { if (any(this) && this.ext("claude").walking) this.ext("claude").walking = false; return qe0.apply(this, a); }; }
  { const ca0 = CM.claudeAccount; if (ca0) CM.claudeAccount = function (g, e, foe) { let t = ca0(g, e, foe); const E = g.bargains ? g.bargains() : {}, took = Object.keys(CM.BARGAINS).filter((id) => E[id] === "taken").map((id) => CM.BARGAINS[id].name), refused = Object.keys(CM.BARGAINS).filter((id) => E[id] === "refused").map((id) => CM.BARGAINS[id].name);
      if (took.length || refused.length) t += ` The king's letters: ${[took.length ? `took ${took.join(", ")}` : "", refused.length ? `burned ${refused.join(", ")}` : ""].filter(Boolean).join("; ")}.`; return t; }; }
}
