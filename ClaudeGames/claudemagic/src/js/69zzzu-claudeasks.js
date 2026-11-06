"use strict";
// Claude asks, and remembers (UPGRADE_PLAN_72.md, release 1). He's curious first: at the cabin he has a question for
// the party now and then - which of them it trusts most, why it goes down, what it's afraid of, what it'll do if it
// wins - and he keeps the answers with the village and uses them: the opening of the next run, his account of each
// run (shown now on the ending's own screen as well as in the Hall of Fame), a line in the margin when what you feared
// comes. In the second edition the king's court remembers the party that brought the Last Page about. And the last of
// red ink: every village building opened too, and no "Ascension is open" on a red-ink win.
//   CM.CLAUDE_QUESTIONS; game.claudeAnswers() -> { id: answer }
{ const P = CM.Game.prototype;
  const V = (g) => g.vext("claude");
  P.claudeAnswers = function () { const W = V(this); W.answers = W.answers || {}; return W.answers; };
  CM.CLAUDE_QUESTIONS = [
    { id: "trust", ask: "Claude turns his cup round in his hands. \"Can I ask you something? Which of them do you trust most? You don't have to say why.\"", opts: (g) => (g.party || []).map((h) => h.name), thanks: (a) => `"${a}." He writes it down, small, in the margin. "I'll watch for that."` },
    { id: "why", ask: "\"Why do you go down? Honestly. I won't write down a better reason than the real one.\"", opts: () => ["For the gold", "To end the king", "To see what's there", "Because someone has to"], thanks: (a) => (a === "For the gold" ? "\"Good. An honest reason. Most people say something nobler and then count the coins on the stairs.\"" : a === "To end the king" ? "\"Then I hope you find out what that means, when you get there. It may not mean what you think.\"" : a === "To see what's there" ? "\"That's my reason too. It's the best one. It's also the one that gets people killed.\"" : "\"Someone always says that, and it's always true, and it's never quite the whole of it.\"") },
    { id: "fear", ask: "\"What are you most afraid of, down there?\"", opts: () => ["The dark", "The king", "Losing one of them", "Nothing, yet"], thanks: (a) => (a === "Nothing, yet" ? "\"Yet. I'll write the 'yet' in, if you don't mind.\"" : "\"Thank you for telling me. I'll remember it - not to frighten you with. Just to be fair to you, in the account, when it comes.\"") },
    { id: "hope", ask: "\"And if you win - if you take the crown off him, one way or the other - what then?\"", opts: () => ["Home, and a long sleep", "Further down", "I don't know yet"], thanks: (a) => (a === "I don't know yet" ? "\"That's the answer I'd give. Let's find out.\"" : a === "Further down" ? "\"Of course it is.\" He smiles. \"There's always a further down.\"" : "\"A long sleep. I'll write that you earned it.\"") },
  ];
  const next = (g) => CM.CLAUDE_QUESTIONS.find((Q) => g.claudeAnswers()[Q.id] === undefined && Q.opts(g).length);
  CM.claudeTopics = (CM.claudeTopics || []).concat([(g) => { const E = g.ext("claude"); return next(g) && !E.askedThisVisit ? [["question", "Claude has a question for you"]] : []; }]);
  { const ce0 = P.claudeEnter; P.claudeEnter = function (...a) { const out = ce0.apply(this, a); if (out) delete this.ext("claude").askedThisVisit; return out; }; }
  CM.claudeActs = Object.assign(CM.claudeActs || {}, {
    question(g, k) { const Q = next(g); if (!Q) return; g.claudeTalk(k, "question", Q.opts(g).map((o) => ["answer", o, `${Q.id}|${o}`]).concat([["unasked", "I'd rather not say"]]), Q.ask); },
    answer(g, k, say, arg) { const [id, ...rest] = String(arg).split("|"), a = rest.join("|"), Q = CM.CLAUDE_QUESTIONS.find((q) => q.id === id); if (!Q) return; g.claudeAnswers()[id] = a; g.ext("claude").askedThisVisit = true; say(Q.thanks(a)); },
    unasked(g, k, say) { g.ext("claude").askedThisVisit = true; say("\"That's all right. I'll ask again some other time - or I won't. Either's fine.\""); },
  });
  // used: the opening of a run
  const WHY = { "For the gold": "for the gold", "To end the king": "to end the king", "To see what's there": "to see what's there", "Because someone has to": "because someone has to" };
  { const ng0 = P.newGame; P.newGame = function (...a) { const out = ng0.apply(this, a), A = (this.village && V(this).answers) || {}; if (A.why && CM.narrate && this.party && this.party.length) CM.narrate(this, `They told me they go down ${WHY[A.why] || A.why.toLowerCase()}. I've written that in, as they said it.`); return out; }; }
  // used: the account
  { const ca0 = CM.claudeAccount; CM.claudeAccount = function (g, e, foe) { let text = ca0(g, e, foe); const A = V(g).answers || {}, h = A.trust && (g.party || []).find((x) => x.name === A.trust);
      if (h) text += ` ${h.name}, the one you told me you trust most, ${h.hp > 0 ? (e.won || e.left || (g.floor && g.floor.number <= 0) ? "came home" : "was still standing at the end") : "didn't come back"}.`;
      if (e.won && A.hope) text += ` You told me that if you won, it would be ${A.hope === "Further down" ? "further down" : A.hope === "I don't know yet" ? "something you'd find out" : "home, and a long sleep"}. I hope it is.`;
      return text; }; }
  // used: what you feared, when it comes
  { const em0 = P.emit; P.emit = function (ev, ...a) { if (this.tally && this.village && CM.narrate) { const A = V(this).answers || {}, N = this.ext("narr"), fl = this.floor;
        if (ev === "change" && A.fear === "Losing one of them" && this.mode === "combat" && this.party && fl) { N.fell = N.fell || []; for (const h of this.party) if (h.hp <= 0 && !N.fell.includes(h.name) && this.party.some((o) => o.hp > 0) && N.aside !== fl.number) { N.fell.push(h.name); N.aside = fl.number; CM.narrate(this, `${h.name} falls. This is the thing you told me you were afraid of. I'm sorry. I'm writing it down anyway, because you'd want it true.`); } }
        if (ev === "floor" && fl && fl.number === CM.LAST_FLOOR && A.fear === "The king" && !N.kingFear) { N.kingFear = true; CM.narrate(this, "You told me you were afraid of him. You came anyway. I've written that down first, before anything else that happens here."); } }
      return em0.call(this, ev, ...a); }; }
  // the second edition: the court remembers
  const COURT2 = ["The Chancellor's eyes open. \"You. You were here at the end, with the scribe. No petitions from you - you've done enough.\" Then, as before:",
    "The Master Mason lifts the plumb line an inch, a salute. \"The floor rang true, the last time. You saw to that.\" Then, as before:",
    "The Captain's Widow looks at you a long moment. \"You heard him say her name. Aelith. Thank you.\" Then, as before:",
    "The Lady-in-Waiting almost smiles. \"He sat down, they say. With a man with ink on his fingers. I'd have liked to see it.\" Then, as before:",
    "Hollis turns his head. \"The scribe. You brought the scribe down. Even I didn't think of that.\" Then, as before:"];
  { const tg0 = P.talkGhost; P.talkGhost = function (thing, k, ...a) { if (!thing || thing.courtier === undefined || V(this).edition !== 2 || !CM.COURT[thing.courtier]) return tg0.call(this, thing, k, ...a);
      const C = CM.COURT[thing.courtier], was = C.line; C.line = `${COURT2[thing.courtier] || "The courtier remembers you."} ${was}`; try { return tg0.call(this, thing, k, ...a); } finally { C.line = was; } }; }
  // red ink: every village building too
  { const d0 = P.redInkDo; if (d0) P.redInkDo = function (id, ...a) { const out = d0.call(this, id, ...a); if (id === "open" && this.village) { this.village.levels = this.village.levels || {}; for (const [bid, B] of Object.entries(CM.VILLAGE)) if (B && Array.isArray(B.costs)) this.village.levels[bid] = Math.max(this.village.levels[bid] || 0, B.costs.length); if (this.saveVillage) this.saveVillage(); } return out; }; }
  if (CM.REDINK && CM.REDINK.open) CM.REDINK.open.name = "Open every calling, kit and village building (for the village)";
  // red ink: no word of a rung that isn't given
  { const e0 = P.endRun; P.endRun = function (...a) { if (!(this.redInk && this.ext && this.tally && this.redInk().used)) return e0.apply(this, a); const s0 = this.say; this.say = function (text, ...b) { if (/^Ascension \d+ is open/.test(String(text))) return; return s0.call(this, text, ...b); }; try { return e0.apply(this, a); } finally { delete this.say; if (this.say !== P.say && Object.prototype.hasOwnProperty.call(this, "say")) delete this.say; } }; }
}
