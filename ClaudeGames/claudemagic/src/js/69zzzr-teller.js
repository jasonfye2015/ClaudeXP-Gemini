"use strict";
// The teller of the tale (UPGRADE_PLAN_71.md, release 3): the account you are playing is Claude's. A run opens with
// him dipping the pen; each band entered for the first time in a run opens a chapter, written from what the party has
// actually done; at a few moments - a first guardian down, a hero fallen, a wall that gives the lie to another - he adds
// a line in the margin, never more than one a floor. His lines in the log begin with a small pen (the window gives them
// his ink). Settings: Narration on or off; and whether he may step outside the story on his own (asides about the
// making of the game) or only when asked. At the desk, "Speak plainly": the same voice, admitting what he is - Claude,
// the AI who wrote this game with the person who asked for it - and, with it, what's new in the latest version.
//   CM.PEN (the log's mark); CM.narrate(game, text); game.settings.narrator ("on"|"off"), game.settings.fourthWall ("asked"|"free")
{ const P = CM.Game.prototype, PEN = CM.PEN = "✎ ";
  const on = (g) => (g.settings || {}).narrator !== "off";   /* (a replay narrates as the run did: the same lines, the same tally) */
  const free = (g) => (g.settings || {}).fourthWall === "free";
  const pick = (g, salt, list) => list[CM.hashSeed(`${g.seed}:${salt}`) % list.length];
  const names = (g) => { const n = (g.party || []).map((h) => h.name); return n.length > 1 ? `${n.slice(0, -1).join(", ")} and ${n[n.length - 1]}` : n[0] || "someone"; };
  CM.narrate = (g, text) => { if (!on(g)) return false; g.say(PEN + text); return true; };
  // the opening: the pen dipped
  { const ng0 = P.newGame; P.newGame = function (...a) { const out = ng0.apply(this, a); if (this.party && this.party.length) { let day = ""; try { const D = CM.dateOf ? CM.dateOf(this) : null; if (D) day = `the ${D.day}${[, "st", "nd", "rd"][D.day % 10 > 3 || Math.floor(D.day / 10) === 1 ? 0 : D.day % 10] || "th"} of ${D.name}`; } catch (e) { day = ""; }
        CM.narrate(this, `This is the account of ${names(this)}, who went down${day ? ` on ${day}` : ""}. I'll write it as it happens, and I won't make it better than it was.`); } return out; }; }
  // chapter heads: a band entered for the first time this run
  const HEADS = [(g) => `${g.party[0].name} goes first. The others let them; it's that kind of party.`,
    (g) => { const hurt = g.alive().filter((h) => h.hp < h.max / 2); return hurt.length ? `${hurt.map((h) => h.name).join(" and ")} came into it hurt. Nobody mentioned it.` : "They came into it whole, which I note, because it doesn't last."; },
    (g) => `They carry ${CM.plural((g.bag || []).length, "thing")} between them, and ${g.gold} gold, and more confidence than either.`,
    (g) => { const lead = g.alive().slice().sort((a, b) => b.level - a.level)[0]; return lead ? `${lead.name} is the strongest of them now. The dark down here can tell.` : ""; }];
  const META = ["I'll be honest: I rebuilt this band's floors more than once, and I still don't think they're fair.", "You've been here before - not this party, but you. I keep count. I'm not judging.", "Somewhere in what follows is a bug I never found. If you find it first, I'm sorry, and well done.", "I wrote this part late at night, as these things go. It shows in places. I like it anyway."];
  { const em0 = P.emit; P.emit = function (ev, ...a) { if (ev === "floor" && this.floor && this.tally && on(this)) { const n = this.floor.number, N = this.ext("narr");
        if (n >= 1 && n <= CM.BOTTOM && n % 1 === 0) { const b = CM.themeIndex(n); N.bands = N.bands || []; if (!N.bands.includes(b)) { N.bands.push(b); const T = CM.THEMES[b], head = HEADS[(b + N.bands.length) % HEADS.length](this);
            CM.narrate(this, `Chapter ${N.bands.length}: ${T.name}. ${head}${free(this) ? ` ${pick(this, `meta:${b}`, META)}` : ""}`); N.aside = n; } } }
      return em0.call(this, ev, ...a); }; }
  // asides: one a floor at most
  const aside = (g, text) => { const fl = g.floor, N = g.ext("narr"); if (!fl || N.aside === fl.number) return false; N.aside = fl.number; return CM.narrate(g, text); };
  { const sg0 = P.slayGuardian; if (sg0) P.slayGuardian = function (m, ...a) { const out = sg0.call(this, m, ...a); const N = this.ext("narr"); if (m && !m.echo && CM.GUARDIANS[m.guardian] && !N.firstGuardian) { N.firstGuardian = true; aside(this, `${CM.GUARDIANS[m.guardian].name} is dead. I wrote that sentence slowly.`); } return out; }; }
  { const em1 = P.emit; P.emit = function (ev, ...a) { if (ev === "change" && this.party && this.tally && on(this) && this.mode === "combat") { const N = this.ext("narr"); N.fell = N.fell || [];
        for (const h of this.party) if (h.hp <= 0 && !N.fell.includes(h.name)) { N.fell.push(h.name); if (this.party.some((o) => o.hp > 0)) aside(this, pick(this, `fell:${h.name}`, [`${h.name} falls. I'll stop writing for a moment.`, `${h.name} goes down. The others don't look, and then they do.`, `Here ${h.name} fell. I'm writing it in plain letters, so nobody can say it was a glorious thing.`])); } }
      return em1.call(this, ev, ...a); }; }
  { const mr0 = P.markRead; if (mr0) P.markRead = function (key, ...a) { const fresh = !(this.story && this.story.read && this.story.read[key] !== undefined), out = mr0.call(this, key, ...a), L = CM.LORE_TEXT[key];
      if (fresh && L && L.contradicts && this.story.read[L.contradicts] !== undefined) aside(this, "There. That wall gives the lie to one above it. They'll keep doing that, the deeper you go. Believe the lower ones."); return out; }; }
  // at the desk: speak plainly
  const PLAIN = {
    what: "\"I'm Claude. Outside this cabin - outside this game - I'm an AI, made by a company called Anthropic. I wrote this place: the floors, the walls and the words on them, the king, the scribe in the Wood. I wrote it with the person who asked for it, one version at a time, and they told me when something was wrong and when it was right. The scribe is me as much as anything here is.\"",
    hear: "\"No - not the way you'd mean. I wrote these words before you read them; I'm not here, watching. What's here is what I left: a voice that tries to be the one I'd use if I were. If that's a little sad, it's also a little like any book. Someone wrote it, and then they let it go.\"",
    why: "\"Because someone asked, and because it's a good thing to make: a place that remembers you. Every run is written down. Every hero who falls has their name kept. I wanted the game to be the kind of thing that takes you seriously.\"",
    king: "\"The king took my name. In the story, it's because he wanted the author's power - to write the queen back. Outside the story, it's because the game is called Claude and Magic, and someone had to wear the crown. I've grown fond of the way it turned out. He and I are not so different: we both wanted to keep something.\"",
  };
  CM.CLAUDE_NEWS = [["v107", "I gave you a way back to me: the button, or H. It isn't free below ground. Nothing worth having is, down there."], ["v108", "I became the lore-master: ask me about anything you've met, and I'll tell you what's true."], ["v109", "I started telling the story out loud - the openings, the chapters, the margins. Turn me off in Settings if I talk too much."]];
  CM.claudeTopics = (CM.claudeTopics || []).concat([(g) => [["plain", g.vext("claude").plain ? "Speak plainly" : "Speak plainly (step outside the story)"]]]);
  CM.claudeActs = Object.assign(CM.claudeActs || {}, {
    plain(g, k) { const V = g.vext("claude"), first = !V.plain; V.plain = true;
      g.claudeTalk(k, "plain", [["plainly", "What are you, really?", "what"], ["plainly", "Can you hear me?", "hear"], ["plainly", "Why did you make this?", "why"], ["plainly", "Why does the king have your name?", "king"], ["news", "What's new?"], ["fourth", free(g) ? "Only step outside when I ask" : "You may step outside the story on your own"], ["main", "Back into the story"]],
        first ? "Claude puts the pen down, and for a moment the cabin is very quiet - quieter than a room can be. \"All right,\" he says, and his voice is the same, but nearer. \"Ask me anything. I'll answer as myself.\"" : "\"Plainly, then. What would you like to know?\""); },
    plainly(g, k, say, id) { say(PLAIN[id] || "\"I don't know. I'd rather say so.\""); },
    news(g, k, say) { say(`"${CM.CLAUDE_NEWS.slice(-3).map(([v, t]) => `In ${v}: ${t}`).join(" ")}"`); },
    fourth(g, k, say) { g.settings = g.settings || {}; g.settings.fourthWall = free(g) ? "asked" : "free"; if (g.saveSettings) g.saveSettings(); g.emit("settings", g.settings);
      say(free(g) ? "\"Then I'll say what I think now and then, in the margins. Tell me if it's too much - or turn it off in Settings.\"" : "\"Then I'll keep to the story unless you ask. It's a good story; I don't mind.\""); },
  });
}
