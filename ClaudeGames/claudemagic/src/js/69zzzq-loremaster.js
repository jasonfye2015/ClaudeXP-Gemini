"use strict";
// The lore-master (UPGRADE_PLAN_71.md, release 2): everything the game knows, asked of Claude. His shelves open the
// codex, the compendium of things and the journal's bestiary; he answers about any kind the party has met, any guardian
// it has reached (and the next), and anything it carries - always from the game's own tables, so always true; he gives
// hints in three tiers, the player's choice (a nudge, a hint, the answer) for the king's heart, the reminding of the
// king and the Margins' next page, and remembers which were taken; and he tells the story behind the walls that
// disagree.
//   CM.claudeOnFoe(game, kind), CM.claudeOnGuardian(game, id), CM.claudeOnThing(game, item), CM.CLAUDE_HINTS
{ const P = CM.Game.prototype, plural = (n, w) => CM.plural(n, w), join = (a) => (a.length <= 1 ? a.join("") : `${a.slice(0, -1).join(", ")} and ${a[a.length - 1]}`);
  const read = (g) => Object.assign({}, (g.village && g.village.loreRead) || {}, (g.story && g.story.read) || {});
  const deepest = (g) => Math.max(1, ...((g.trail || []).map((t) => t[0] || 0)), g.floor && g.floor.number > 0 ? g.floor.number : 0, CM.deepest ? CM.deepest(g.allFame || g.fame || []).floor : 0);
  const resists = (K) => { const R = Object.assign({}, K.undead ? { holy: 1.5 } : {}, ((CM.MONSTER_SHAPES || {})[K.name] || {}).resist || {}, K.resist || {}); return { weak: Object.keys(R).filter((e) => R[e] > 1), strong: Object.keys(R).filter((e) => R[e] < 1) }; };
  CM.claudeOnFoe = function (g, kind) { const K = CM.monsterKind(kind); if (!K) return "\"I don't know that one. Describe it to me sometime - from a safe distance.\""; const B = (g.bestiary || {})[K.name] || {}, R = resists(K), out = [];
    out.push(`"${K.name}. ${B.seen ? `You've met ${B.seen === 1 ? "one" : `${B.seen} of them`}${B.slain ? `, and put down ${B.slain}` : ""}.` : "You haven't met one yet."}`);
    if (K.ability && CM.ABILITY_WORDS && CM.ABILITY_WORDS[K.ability]) out.push(`It ${CM.ABILITY_WORDS[K.ability]}.`);
    if (K.touch && K.touch.status) out.push(`Its touch can leave you ${((CM.STATUSES || {})[K.touch.status] || { name: K.touch.status }).name.toLowerCase()}${K.touch.chance >= 0.3 ? " - often" : ""}.`);
    if (K.undead) out.push("It's undead: holy work bites it.");
    if (R.weak.length) out.push(`It fears ${join(R.weak)}.`); if (R.strong.length) out.push(`${join(R.strong).replace(/^./, (c) => c.toUpperCase())} ${R.strong.length === 1 ? "does" : "do"} little to it.`);
    if (K.row === "back" || ((CM.MONSTER_SHAPES || {})[K.name] || {}).row === "back") out.push("It keeps to the back row; your front line has to reach past the others.");
    if (out.length === 1) out.push("Nothing strange about it, which is its own kind of warning.");
    return `${out.join(" ")}"`; };
  const MOVE_WORDS = { summon: "calls others to it", grasp: "seizes one of you and holds them", breath: "breathes on the whole party", sweep: "sweeps the front row", drain: "drinks what it hits", charge: "charges the back row", heal: "mends itself" };
  CM.claudeOnGuardian = function (g, id) { const G = CM.GUARDIANS[id]; if (!G) return "\"I don't know that one.\""; const floor = CM.realOf ? CM.realOf(G.floor) : G.floor, out = [`"${G.name}, on floor ${floor}.`];
    const moves = (G.moves || []).map((m) => MOVE_WORDS[m.kind]).filter(Boolean); if (moves.length) out.push(`It ${join([...new Set(moves)])}.`);
    if (G.touch && G.touch.status) out.push(`Its touch can leave you ${((CM.STATUSES || {})[G.touch.status] || { name: G.touch.status }).name.toLowerCase()}.`);
    if (G.weak) out.push(`It hates ${G.weak}.`); if (G.resist) out.push(`Don't waste ${G.resist} on it.`); if (G.undead) out.push("It's undead.");
    if (CM.PARLEY && CM.PARLEY[id]) out.push("It talks before it fights. Answer it carefully; the fight goes better if you do, and sometimes there isn't one.");
    const N = CM.store.get("nemesis", null); if (N && N.name === G.name) out.push(`It's what took ${(N.party || [])[0] ? `${N.party[0]}'s party` : "your last party"}. I wrote that down. I'd rather not write it again.`);
    return `${out.join(" ")}"`; };
  CM.claudeOnThing = function (g, it) { if (!it) return "\"Hand it here.\""; if (it.unknown) return "\"I can't say what it is until it's named. I can look at one a day, if you ask me to - or the temple's scribe will.\"";
    const label = CM.itemLabel ? CM.itemLabel(it) : "", lore = it.lore || ((CM.BASES || {})[it.name] || {}).lore || ""; return `"${it.name}${label ? ` - ${label}` : ""}.${lore ? ` ${lore}` : ""}${(it.props || {}).cursed ? " It's cursed. I'd have the temple see to it." : ""}"`; };
  // hints in three tiers: a nudge, a hint, the answer
  const unread = (g, keys) => keys.filter((k) => read(g)[k] === undefined);
  const floorOf = (k) => { const L = CM.LORE_TEXT[k]; return L && L.floor ? (CM.realOf ? CM.realOf(L.floor) : L.floor) : null; };
  CM.CLAUDE_HINTS = {
    heart: { name: "Where the king keeps his heart", open: (g) => !CM.heartKnown(g), tiers: [
      (g) => { const n = CM.HEART_CLUES.length - unread(g, CM.HEART_CLUES).length; return `"Three things point to it. You have ${n === 0 ? "none of them" : n === 1 ? "one" : "two"}. They're all in the palace, or near it."`; },
      () => "\"A courtier who still keeps the petitions; a wall on the palace's eighteenth floor or so, as the story counts; and a page the physician didn't manage to burn - it's in a chest somewhere in the palace.\"",
      () => `"Under the last stone of the floor above the throne room. The physician had a place made there for it: he says so himself, in the page that survived."` ] },
    remind: { name: "Reminding the king who he was", open: (g) => !g.reminded, tiers: [
      (g) => { const n = unread(g, CM.REMIND.map((r) => r.key)).length; return n ? `"He'll ask you five things. You can't yet answer ${n === 1 ? "one of them" : `${n} of them`}. Read the walls - the old ones."` : "\"You can answer everything he'll ask. Read the palace's chapter to the end, smash the heart, and go and talk to him.\""; },
      (g) => { const left = unread(g, CM.REMIND.map((r) => r.key)); return left.length ? `"The ones you're missing are in ${join([...new Set(left.map((k) => ((CM.CHAPTERS || {})[(CM.LORE_TEXT[k] || {}).chapter] || {}).name || "the walls"))])}."` : "\"Nothing missing. Go on.\""; },
      (g) => { const left = unread(g, CM.REMIND.map((r) => r.key)); return left.length ? `"Floor${left.length > 1 ? "s" : ""} ${join(left.map(floorOf).filter(Boolean).map(String))}: the carvings there. Stand at each and read it."` : "\"Nothing missing. Go on.\""; } ] },
    margins: { name: "My next lost page", open: (g) => g.marginsPinned && g.marginsPinned().length < 10, tiers: [
      (g) => { const b = (CM.MARGINS || []).findIndex((_, i) => !g.marginsPinned().includes(i)); return `"The next one I'm missing blew down into ${CM.THEMES[b].name}."`; },
      (g) => { const b = (CM.MARGINS || []).findIndex((_, i) => !g.marginsPinned().includes(i)), T = CM.THEMES[b]; const n = CM.marginFloor(g.seed, b); return `"In ${T.name}, somewhere in the ${n - T.floors[0] < (T.floors[1] - T.floors[0]) / 2 ? "upper" : "lower"} half - on your road this time, at least."`; },
      (g) => { const b = (CM.MARGINS || []).findIndex((_, i) => !g.marginsPinned().includes(i)); return `"Floor ${CM.marginFloor(g.seed, b)}, this time down. On open floor, under a pebble. I think the wind was kind."`; } ] },
  };
  const TIER_NAMES = ["A nudge", "A hint", "The answer"];
  // the walls that disagree: pairs the party has both read
  const lies = (g) => { const r = read(g); return Object.values(CM.LORE_TEXT).filter((L) => L.contradicts && r[L.key] !== undefined && r[L.contradicts] !== undefined); };
  // the lore-master's menu
  CM.claudeTopics = (CM.claudeTopics || []).concat([() => [["lore-master", "Ask the lore-master..."]]]);
  CM.claudeActs = Object.assign(CM.claudeActs || {}, {
    "lore-master"(g, k) { const opts = [["library", "The library: the codex, the things, the bestiary"]];
      if (Object.keys(g.bestiary || {}).length) opts.push(["foes", "Something we've fought"]);
      opts.push(["guardians", "A guardian"]); if ((g.bag || []).length) opts.push(["things", "Something we're carrying"]);
      if (Object.values(CM.CLAUDE_HINTS).some((H) => H.open(g))) opts.push(["hints", "I'm stuck"]);
      if (lies(g).length) opts.push(["lies", "The walls that disagree"]);
      g.claudeTalk(k, "lore-master", opts.concat([["main", "Something else"]]), "Claude sets down the pen. \"Ask. If I know, I'll say; if I don't, I'll say that.\""); },
    library(g, k) { g.claudeTalk(k, "library", [["shelf", "The codex: the story, chapter by chapter", "codex"], ["shelf", "The compendium of things", "things"], ["shelf", "The bestiary, and the run's journal", "journal"], ["lore-master", "Back"]], "\"Everything's on the shelves. The blank spines are the walls you haven't read yet.\""); },
    shelf(g, k, say, id) { g.logAct && g.logAct("claudeShelf", id); say(id === "codex" ? "Claude takes the codex down and opens it flat. \"The story so far - your story of it.\"" : id === "things" ? "Claude pulls out a fat catalogue, every page a drawing. \"Everything you've carried, and some you haven't.\"" : "Claude hands you the journal. \"Kept as you went. The bestiary's at the back.\""); g.emit("claudePanel", id); },
    foes(g, k) { const kinds = Object.keys(g.bestiary || {}).sort((a, b) => ((g.bestiary[b] || {}).seen || 0) - ((g.bestiary[a] || {}).seen || 0)).slice(0, 10); g.claudeTalk(k, "foes", kinds.map((n) => ["foe", n, n]).concat([["lore-master", "Back"]]), "\"Which one?\""); },
    foe(g, k, say, kind) { say(CM.claudeOnFoe(g, kind)); },
    guardians(g, k) { const deep = deepest(g), ids = CM.GUARDIAN_ORDER.filter((id) => CM.GUARDIANS[id]), shown = []; for (const id of ids) { shown.push(id); if ((CM.realOf ? CM.realOf(CM.GUARDIANS[id].floor) : CM.GUARDIANS[id].floor) > deep) break; }
      g.claudeTalk(k, "guardians", shown.map((id) => ["guardian", `${CM.GUARDIANS[id].name} (floor ${CM.realOf ? CM.realOf(CM.GUARDIANS[id].floor) : CM.GUARDIANS[id].floor})`, id]).concat([["lore-master", "Back"]]), "\"The ones you've reached, and the next. I won't tell you about the ones further down until you're nearer; it doesn't help to dread them.\""); },
    guardian(g, k, say, id) { say(CM.claudeOnGuardian(g, id)); },
    things(g, k) { g.claudeTalk(k, "things", (g.bag || []).slice(0, 10).map((it, i) => ["thing", it.unknown ? "Something unknown" : it.name, i]).concat([["lore-master", "Back"]]), "\"Hand it here.\""); },
    thing(g, k, say, i) { say(CM.claudeOnThing(g, (g.bag || [])[i])); },
    hints(g, k) { g.claudeTalk(k, "hints", Object.entries(CM.CLAUDE_HINTS).filter(([, H]) => H.open(g)).map(([id, H]) => ["hint", H.name, id]).concat([["lore-master", "Back"]]), "\"Stuck where? And how much do you want me to say - I can nudge, or I can just tell you.\""); },
    hint(g, k, say, id) { const H = CM.CLAUDE_HINTS[id], had = (g.vext("claude").hints || {})[id]; g.claudeTalk(k, "hint", TIER_NAMES.map((n, t) => ["tier", `${n}${had !== undefined && had >= t ? " (again)" : ""}`, `${id}:${t}`]).concat([["hints", "Back"]]), `"${H.name}. How much?"`); },
    tier(g, k, say, arg) { const [id, t] = String(arg).split(":"), H = CM.CLAUDE_HINTS[id]; if (!H) return; const V = g.vext("claude"); V.hints = V.hints || {}; V.hints[id] = Math.max(V.hints[id] === undefined ? -1 : V.hints[id], Number(t)); g.ext("claude").hinted = true;
      say(H.tiers[Number(t)](g)); },
    lies(g, k) { const L = lies(g); g.claudeTalk(k, "lies", L.map((l, i) => ["lie", `Floor ${floorOf(l.contradicts)} and floor ${floorOf(l.key)}`, i]).concat([["lore-master", "Back"]]), "\"You've noticed. Good. Which pair?\""); },
    lie(g, k, say, i) { const l = lies(g)[i]; if (!l) return; const above = CM.LORE_TEXT[l.contradicts];
      g.emit("talk", { title: "Claude, on the walls that disagree", text: `"Up on floor ${floorOf(l.contradicts)} the wall says: ${above.text} Down on floor ${floorOf(l.key)}: ${l.text} The lower one's the truer. The walls above were cut for the court, by people who had to live with the court reading them. The ones below were cut by people who no longer had anything to lose. When they disagree, I believe the ones who had nothing to lose."` }); },
  });
}
