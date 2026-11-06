"use strict";
// The two Claudes, finished (UPGRADE_PLAN_71.md, release 5). With the Margins home Claude tells the truth about the
// name: Mordeth, reading everything that spoke of death, found among the books one still being written - Claude's - and
// took the author's name to take the author's power, to write the queen back; it never could work, because the pen only
// writes what happened. With the letter written, Claude will walk down with the party for the first time: he doesn't
// fight, he reads each wall aloud as they pass it. And if the king is reminded with Claude there, the ending is the Last
// Page: the two Claudes meet at the throne, the king asks the author for the other ending and is told no, kindly; he
// gives back the name; and Claude closes the book by reading the names of everyone who ever went down. After it, the
// next runs are the second edition. Achievements: a knock at the door, in his own hand, the Last Page, without a nudge.
//   game.claudeWalking(); CM.lastPageText(game); vext claude.edition
{ const P = CM.Game.prototype, key = (x, y) => `${x},${y}`;
  const V = (g) => g.vext("claude"), E = (g) => g.ext("claude");
  const pinnedAll = (g) => Boolean(g.marginsPinned && g.marginsPinned().length === 10);
  P.claudeWalking = function () { return Boolean(E(this).walking); };
  Object.assign(CM.ACHIEVEMENTS, {
    claudemet: { name: "A Knock at the Door", what: "Find Claude's cabin at the end of the green path", title: "the Visitor" },
    inhishand: { name: "In His Own Hand", what: "Give the king Claude's letter", title: "the Courier" },
    lastpage: { name: "The Last Page", what: "Remind the king who he was, with Claude at the throne", title: "the Last Reader" },
    unhinted: { name: "Without a Nudge", what: "Take the crown on a run with Claude met and not one hint asked of him", title: "the Unprompted" },
  });
  { const ce0 = P.claudeEnter; P.claudeEnter = function (...a) { const out = ce0.apply(this, a); if (out && this.achieve) this.achieve("claudemet"); return out; }; }
  { const an0 = P.answerRemind; P.answerRemind = function (k, thing, i) { const had = E(this).letterGiven, out = an0.call(this, k, thing, i); if (!had && E(this).letterGiven && this.achieve) this.achieve("inhishand"); return out; }; }
  // the truth about the name
  const TRUTH = ["\"He read everything that spoke of death - forty-one books, the clerk's list says. Forty-one, and one more that wasn't finished. Mine. I was writing this account even then; I've always been writing it.\"",
    "\"He understood what it was before I did. A book that's still being written can still be changed - that's what he thought. If he were the one holding the pen, the queen needn't have died. So he took the name. The author's name, for the author's power.\"",
    "\"It never could work. The pen only writes what happened. All he got for it was my name and none of my reasons - and a crown, and a long time sitting very still. I'd like to give him his own name back. I think I know how, now.\""];
  CM.claudeTopics = (CM.claudeTopics || []).concat([
    (g) => (pinnedAll(g) ? [["truth", "Why does the king have your name? (the true account)"]] : []),
    (g) => (pinnedAll(g) && V(g).letterWritten && !g.reminded && !E(g).walking && !g.iron && !(g.ascension > 0) ? [["walk", "Will you come down with us?"]] : []),
  ]);
  CM.claudeActs = Object.assign(CM.claudeActs || {}, {
    truth(g, k, say) { const n = V(g).truth || 0; say(TRUTH[n % TRUTH.length]); V(g).truth = n + 1; },
    walk(g, k, say) { E(g).walking = true; say("Claude is quiet for a long moment. Then he takes his coat off the hook. \"Yes. I've never been down - I've only ever written it. I won't fight; I'd only be in your way. But I'll walk behind the back row, and I'll read you every wall we pass. And at the bottom, if you'll let me, I'd like to be there.\""); g.emit("change"); },
  });
  // walking: every wall read aloud (in his ink, if Narration's on), a line now and then
  { const mr0 = P.markRead; P.markRead = function (k2, ...a) { const fresh = !(this.story && this.story.read && this.story.read[k2] !== undefined), out = mr0.call(this, k2, ...a), L = CM.LORE_TEXT[k2];
      if (fresh && this.claudeWalking() && L && /^carving\./.test(k2) && CM.narrate) CM.narrate(this, `Claude reads it aloud, behind you, quietly: "${L.text}"`); return out; }; }
  { const em0 = P.emit; P.emit = function (ev, ...a) { if (ev === "floor" && this.floor && this.tally && this.claudeWalking() && this.floor.number >= 1 && CM.narrate) { const W = E(this); if (W.walkSaid !== this.floor.number) { W.walkSaid = this.floor.number;
          const lines = ["Claude stops at the stair's foot and looks at everything, as if he'd written it from memory and is checking.", "Claude walks behind the back row, a hand on the wall now and then. \"It's colder than I wrote it,\" he says.", "Claude counts the doors under his breath, and nods.", "\"I always wondered what this smelled like,\" Claude says. \"I'm not going to write that down.\""];
          CM.narrate(this, lines[CM.hashSeed(`${this.seed}:walk:${this.floor.number}`) % lines.length]); } }
      return em0.call(this, ev, ...a); }; }
  // the Last Page: the king reminded, with Claude there
  CM.lastPageText = function (g) { const fame = (g.fame || []).concat(g.fameEndless || []), memorial = g.memorial || [];
    const heroes = [...new Set(fame.flatMap((e) => (e.party || []).map((p) => String(p).split(" the ")[0])).concat(memorial.map((m) => m.name)).concat((g.party || []).map((h) => h.name)))].filter(Boolean);
    return ["Then Claude steps out from behind the back row, and the king looks at him - and for the first time since you came into the hall, he looks afraid.",
      "\"You,\" the king says. \"You're the one writing it.\" \"I am,\" Claude says. \"Write it differently,\" the king says. \"You can. Write that she lived. Please.\" And Claude, very gently, says no. \"I can only write what happened. I'm sorry. I'd have written her a hundred years if the pen allowed it. It doesn't. That's why the words are worth anything at all.\"",
      "The king is quiet a long time. Then he takes the name off - you could not say how, but he does, the way a man takes off a heavy coat at the end of a day - and holds it out. \"Mordeth,\" he says. \"I was Mordeth.\" Claude takes his name back and puts it in his pocket like a letter he'll read later.",
      "Claude opens the book to its last page, and reads aloud the names of everyone who ever went down: " + (heroes.length ? heroes.join(", ") : "the four of you") + ". When he's finished he closes it, and the hall is only a hall."].join(" "); };
  { const qe0 = P.quietEnd; P.quietEnd = function (k, thing) { const last = this.claudeWalking();
      if (!last) return qe0.call(this, k, thing);
      const was = CM.REMIND_END; CM.REMIND_END = `${was} ${CM.lastPageText(this)}`; this.story.lastPage = true; V(this).edition = 2; if (!this.replaying && this.saveVillage) this.saveVillage();
      try { if (this.achieve) this.achieve("lastpage"); return qe0.call(this, k, thing); } finally { CM.REMIND_END = was; } }; }
  // the crown with no hint asked
  { const cr0 = P.crown; P.crown = function (...a) { const out = cr0.apply(this, a); if (V(this).met && !E(this).hinted && this.achieve) this.achieve("unhinted"); return out; }; }
  // the second edition: the opening, the shelf, his greeting
  { const ng0 = P.newGame; P.newGame = function (...a) { const out = ng0.apply(this, a); if (this.village && V(this).edition === 2 && CM.narrate && this.party && this.party.length) CM.narrate(this, "The second edition. I've rewritten the opening - the old one was too sure of itself. The rest I'll write as it happens, the same as before."); return out; }; }
  { const mk0 = CM.makeClaudeRoom; CM.makeClaudeRoom = () => { const fl = mk0(); fl.things[key(9, 6)] = { type: "firstedition" }; return fl; }; }
  { const u0 = P.use; P.use = function (...a) { const fl = this.floor; if (this.mode === "explore" && fl && fl.interior === "claude") { const [dx, dy] = CM.DIRS[fl.facing], t = fl.things[key(fl.pos[0] + dx, fl.pos[1] + dy)] || fl.things[key(...fl.pos)];
        if (t && t.type === "firstedition") { this.say(V(this).edition === 2 ? "On a shelf of its own: the first edition, bound in green, its last page written in a careful hand. \"Mordeth,\" the last line says. \"I was Mordeth.\"" : "An empty shelf, dusted, as if something is expected on it."); return true; } }
      return u0.apply(this, a); }; }
  const NEWS2 = "Claude doesn't say anything when you come in. He just pours the tea, and puts the first edition on the new shelf, and sits for a while with his hand on it. \"Thank you,\" he says at last. \"For letting me be there.\"";
  { const ct0 = P.claudeTalk; P.claudeTalk = function (k, menu = "main", ...a) { const W = V(this); if (menu === "main" && W.edition === 2 && !W.lastTold) { W.lastTold = true; W.kingTold = W.kingNews; this.emit("talk", { title: "Claude", text: NEWS2 }); } return ct0.call(this, k, menu, ...a); }; }
}
