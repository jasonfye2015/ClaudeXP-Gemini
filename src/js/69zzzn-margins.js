"use strict";
// The Margins (UPGRADE_PLAN_70.md, release 2): Claude was writing a true account of Caer Duin, and one stormy night the
// pages blew down the shaft. Ten of them, one in each band, lie loose on a floor the seed chooses - a page in a neat
// hand, weighted with a pebble someone put there. Carried home and handed over, Claude reads each aloud (a piece of the
// world's story, from someone who looked at it carefully) and pins it to the map wall; every third page there is a
// small thing in thanks - a bookmark (a trinket that marks the way down), two Scrolls of Mapping, a cup that keeps the
// tea's warmth for two floors. The tenth page ends the account, and with it a confession. Pages pinned are kept with
// the village; a page already on the wall is not laid again.
//   CM.MARGINS[band] -> { title, text }; CM.marginFloor(seed, band); game.marginsPinned() -> [band]
{ const key = (x, y) => `${x},${y}`;
  CM.MARGINS = [
    { title: "the first dead", text: "The songs say the first dead of Caer Duin were heroes. I went through the parish rolls. They were a baker, two carters, a girl of nine and the man who kept the ferry. The king came down and stood a long time with each of them. I think that is the truest thing anyone ever cut about him, and it is on a wall nobody reads." },
    { title: "the water", text: "The water did not rise in a night. I measured the tide-marks: it rose for a month, a finger's width a day, and the lower town was told to leave and did not believe it. Nobody likes to have been warned. That is why the carvings say a night." },
    { title: "the sealed doors", text: "The dwarves sealed their doors from the inside, and everyone above took it for fear. It was a quarantine. Their own ledgers say so - a count of the well and the sick, kept to the last day, in a very steady hand. They were keeping it from us. We never thanked them. We said they hid." },
    { title: "the court", text: "The court still sits where it sat, and I have been asked whether that is cruelty. I don't think he knows how to let anyone go. He had a wife, and then he didn't, and he made very sure that nothing else would ever leave him. That isn't cruelty. It's worse than cruelty for everyone, him most of all." },
    { title: "two kinds of wall", text: "Down here the carvings stop agreeing with the ones above, and I spent a long time on why. The ones above were cut by the court. The ones down here were cut by the people the court was talking about. Read both. Neither is lying, exactly. Each is leaving something out." },
    { title: "the names", text: "At the end there was no one left to dig, so the dead went down the shaft. I would like it written somewhere that the people who did it said each name as they let go. There is a list in charcoal on the wall at the top. I copied it out. It took me nine days." },
    { title: "the crystal", text: "The dwarves left the deep halls for this - not for the king, the walls insist, and I believe them. If you have stood in the crystal with one torch you know why. Some things are worth leaving everything for. I only wish it hadn't been the last thing they did." },
    { title: "the bells", text: "Iron was not enough for him, the wall says, and the songs make that sound like greed. The foundry's own tallies are for bells. Hundreds of them, cast and broken and cast again. He was trying to make one loud enough to be heard wherever she had gone. None of them was ever rung. None was ever loud enough." },
    { title: "the teacher", text: "The Patriarch kept the dead before there was a king; the king only learned. I want to be fair to Mordeth here. He was taught by something very old that had never lost anything, because it had never had anything to lose. That is a poor teacher for a man in grief." },
    { title: "the last page", text: "Everything above is the Root's dream, the last wall says, and I wondered for a while whether that makes the rest of it less true. I've decided it doesn't. A thing can be dreamed and still matter. And I should tell you something, since you came all this way: I had a hand in the making of this place. Not the king, and not the dark - the walls, and the words on them, and the path out to this door. I wanted it to be worth the walk. Was it?" },
  ];
  const P = CM.Game.prototype;
  CM.marginFloor = (seed, band) => { const T = CM.THEMES[band]; if (!T) return null; const [a, b] = T.floors; return Math.min(CM.BOTTOM, a + CM.hashSeed(`${seed}:margin:${band}`) % (b - a + 1)); };
  P.marginsPinned = function () { const V = this.vext("claude"); return Object.keys(V.pages || {}).map(Number).sort((a, b) => a - b); };
  CM.marginItem = (band) => ({ name: `A page in a neat hand (${CM.MARGINS[band].title})`, kind: "margin", page: band, power: 0, value: 0 });
  // laid as the floor is first entered: on an open square, weighted with a pebble
  { const em0 = P.emit; P.emit = function (ev, ...a) { if (ev === "floor" && this.floor && this.tally && this.vext) { const fl = this.floor, n = fl.number;
        if (n >= 1 && n <= CM.BOTTOM && n % 1 === 0 && fl.special !== "interior" && !(this.deltas && this.deltas[n])) { const E = this.ext("margins");
          for (let b = 0; b < CM.MARGINS.length; b++) { if (E[b] || CM.marginFloor(this.seed, b) !== n) continue; E[b] = true;
            if (b in (this.vext("claude").pages || {}) || (this.bag || []).some((i) => i.kind === "margin" && i.page === b)) continue;
            const N = fl.grid.length, cells = []; for (let y = 1; y < N - 1; y++) for (let x = 1; x < N - 1; x++) if (fl.grid[y][x] === 0 && !fl.things[key(x, y)] && !(fl.features || {})[key(x, y)] && !(fl.pos[0] === x && fl.pos[1] === y) && !(fl.number === -1 && CM.isCoastLine && CM.isCoastLine(x, y))) cells.push(key(x, y));
            if (cells.length) fl.things[cells[CM.hashSeed(`${this.seed}:marginat:${b}`) % cells.length]] = { type: "margin", page: b }; } } }
      return em0.call(this, ev, ...a); }; }
  // found: stepped on, it's seen; Space takes it
  { const m0 = P.move; P.move = function (rel) { const out = m0.call(this, rel), fl = this.floor; if (out && fl && fl.things) { const t = fl.things[key(...fl.pos)]; if (t && t.type === "margin") this.say("A loose page under a pebble, written close in a neat hand, the margins full of smaller notes. (Space to take it)"); } return out; }; }
  { const u0 = P.use; P.use = function (...a) { const fl = this.floor; if (this.mode === "explore" && fl && fl.things) { const k = key(...fl.pos), t = fl.things[k];
        if (t && t.type === "margin") { this.logAct && this.logAct("use"); delete fl.things[k]; this.bag.push(CM.marginItem(t.page)); this.sound && this.sound("page");
          const V = this.vext("claude"), M = CM.MARGINS[t.page];
          this.say(V.met ? `One of Claude's pages - "${M.title}" across the top, and the hand is his. You fold it carefully into the pack.` : `A page of someone's careful account of this place - "${M.title}" across the top. Whoever wrote it signed it only with a small drawn quill. You fold it into the pack.`);
          this.saveRun && this.saveRun(); this.emit("change"); return true; } }
      return u0.apply(this, a); }; }
  // handed over at the cabin: read aloud, pinned, and every third page a thank-you
  CM.claudeTopics = (CM.claudeTopics || []).concat([(g) => { const have = (g.bag || []).filter((i) => i.kind === "margin"); return have.length ? [["margin", have.length === 1 ? "I found one of your pages" : `I found ${have.length} of your pages`]] : []; },
    (g) => (g.marginsPinned().length ? [["wall", `Read me the map wall (${g.marginsPinned().length} of 10)`]] : [])]);
  const GIFTS = { 3: "bookmark", 6: "maps", 9: "cup" };
  CM.claudeActs = Object.assign(CM.claudeActs || {}, {
    margin(g, k, say) { const i = g.bag.findIndex((it) => it.kind === "margin"); if (i < 0) return; const [it] = g.bag.splice(i, 1), V = g.vext("claude"); V.pages = V.pages || {}; V.pages[it.page] = CM.dayOf ? CM.dayOf(g) : 1;
      const n = Object.keys(V.pages).length, M = CM.MARGINS[it.page]; let thanks = "";
      const gift = GIFTS[n]; if (gift && !(V.gifts || {})[gift]) { V.gifts = Object.assign(V.gifts || {}, { [gift]: true });
        if (gift === "bookmark") { g.bag.push(CM.trinket("bookmark")); thanks = " Claude presses something into your hand: a bookmark of thin brass with a quill cut in it. \"It points the way on. I've no use for it - I never know where I'm going either, but I like to find out slowly.\""; }
        if (gift === "maps") { g.bag.push(CM.scroll("mapping"), CM.scroll("mapping")); thanks = " \"Here - I drew these from what you've brought back. Read one on a floor and the floor is yours.\" Two Scrolls of Mapping."; }
        if (gift === "cup") { V.cup = true; thanks = " Claude takes a cup down from the shelf - a fat clay one, glazed green. \"This one keeps tea warm longer than it has any right to. It lives here, but it's yours.\" (Claude's tea now lasts two floors.)"; } }
      g.emit("talk", { title: `Claude reads: ${M.title}`, text: `Claude reads it aloud, slowly, the way you read something you wrote a long time ago. "${M.text}"` });
      say(`${n === 10 ? "Claude pins the last page in its place, and stands back, and doesn't say anything for a while." : `Claude pins it to the map wall with the others and runs a string from it to somewhere else. ${n} of ten.`}${thanks}`);
      if (g.tally) g.tally.margins = (g.tally.margins || 0) + 1; if (n === 10 && g.achieve) g.achieve("margins"); g.emit("change"); },
    wall(g, k) { const pinned = g.marginsPinned(); g.claudeTalk(k, "wall", pinned.map((b) => ["reread", CM.MARGINS[b].title, b]).concat([["main", "Something else"]]), `"${pinned.length === 10 ? "All of it. The whole account, back on one wall." : `${pinned.length} of ten. The rest are still down there somewhere.`} Which one?"`); },
    reread(g, k, say, arg) { g.emit("talk", { title: `Claude reads: ${CM.MARGINS[arg].title}`, text: `"${CM.MARGINS[arg].text}"` }); },
  });
  CM.TRINKETS.bookmark = { name: "Claude's bookmark", what: "the way down marked on the map as you arrive", props: { lodestone: true } };
  CM.BASES[CM.TRINKETS.bookmark.name] = { id: CM.TRINKETS.bookmark.name, kind: "trinket", slot: "trinket", tier: Object.keys(CM.TRINKETS).length - 1, group: "trinket", trinket: "bookmark" };
  CM.ACHIEVEMENTS.margins = { name: "The Margins", what: "Bring all ten of Claude's pages home", title: "the Scribe's Friend" };
  // the pinned pages, seen on the cabin's wall
  { const mk0 = CM.makeClaudeRoom; CM.makeClaudeRoom = () => { const fl = mk0(); fl.things[key(5, 2)] = { type: "mapwall" }; return fl; }; }
  const wallWords = (g) => { const n = g.marginsPinned().length; return n === 0 ? "The map wall: maps of the Wood and the town, string between them, and a bare patch in the middle with ten pins waiting in it." : n === 10 ? "The map wall: all ten pages pinned in their places, red string running between them and out to the maps, the whole account back on one wall." : `The map wall: ${n} of the ten pages pinned up, red string between them, and bare pins where the rest belong.`; };
  { const u0 = P.use; P.use = function (...a) { const fl = this.floor; if (this.mode === "explore" && fl && fl.interior === "claude") { const [dx, dy] = CM.DIRS[fl.facing]; for (const k of [key(...fl.pos), key(fl.pos[0] + dx, fl.pos[1] + dy)]) if (fl.things[k] && fl.things[k].type === "mapwall") { this.say(wallWords(this)); return true; } } return u0.apply(this, a); }; }
  { const l0 = P.look; P.look = function (...a) { const out = l0.apply(this, a), fl = this.floor; if (this.mode === "explore" && fl && fl.interior === "claude") { const [dx, dy] = CM.DIRS[fl.facing], t = fl.things[key(fl.pos[0] + dx, fl.pos[1] + dy)]; if (t && t.type === "mapwall") this.say(wallWords(this)); } return out; }; }
}
