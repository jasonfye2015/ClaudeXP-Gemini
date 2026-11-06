"use strict";
// Claude, at the end of the green path (UPGRADE_PLAN_70.md, release 1). A faint path leaves the road just west of the
// farm, marked by a post with a quill cut into it, and runs south through the trees to a clearing and a small log
// cabin - walked to every time: no portal, no waystone. Inside, among pages and pinned maps and a kettle always nearly
// boiling, lives Claude, a scribe and a tinkerer who came to the Wood to write things down properly. Claude reads the
// party honestly - how it's doing, what lies below, what the carvings it has read mean together - and once a day offers
// tea (the heart lifts, and the next floor's first fight finds the party awake), a second opinion on one unknown thing,
// and a rest by the fire. Nothing Claude gives is needed; every gift is small. By day Claude is at the desk, in the
// evening by the hearth, after midnight asleep (and not cross to be woken). Claude shares a name with the king below,
// and minds.
//   CM.CLAUDE_CABIN; CM.CLAUDE_ROOM (-29, the cabin's floor); CM.layClaudeCabin(fl); game.claudeTalk(k); CM.claudeRead(game)
{ const C = CM.CLAUDE_CABIN = { cells: [31, 44, 35, 46], door: [33, 44], front: [33, 43], path: [33, 34, 33, 42], post: [32, 34], clearing: [27, 39, 39, 49], centre: [33, 45] };
  const ROOM = CM.CLAUDE_ROOM = -29;
  const key = (x, y) => `${x},${y}`;
  CM.isClaudeCabinCell = (x, y) => x >= C.cells[0] && x <= C.cells[2] && y >= C.cells[1] && y <= C.cells[3];
  // ---- the land: the path, the clearing, the cabin - laid last, so nothing the seed placed moves ----
  CM.layClaudeCabin = function (fl) { const [x0, y0, x1, y1] = C.clearing, [cx, cy] = C.centre;
    const open = (x, y, g) => { fl.grid[y][x] = 0; if (fl.kinds) delete fl.kinds[key(x, y)]; (fl.ground = fl.ground || {})[key(x, y)] = g; };
    for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) if (((x - cx) / 5.4) ** 2 + ((y - cy) / 4.6) ** 2 <= 1 && !CM.isClaudeCabinCell(x, y)) open(x, y, (x * 5 + y * 3) % 6 ? "grass" : "litter");
    for (let y = C.cells[1]; y <= C.cells[3]; y++) for (let x = C.cells[0]; x <= C.cells[2]; x++) { fl.grid[y][x] = 1; (fl.kinds = fl.kinds || {})[key(x, y)] = x === C.door[0] && y === C.door[1] ? "cabindoor" : "cabin"; if (fl.ground) delete fl.ground[key(x, y)]; }
    const [px, py0, , py1] = C.path; for (let y = py0; y <= py1; y++) open(px, y, "dirt");   /* (not on the map till walked: the path is found, not shown) */
    open(...C.post, "dirt");
    fl.things[key(...C.front)] = { type: "claudecabin" };
    fl.things[key(...C.post)] = { type: "quillpost" };
    fl.rooms = (fl.rooms || []).concat({ x0, y0, x1, y1, name: "Claude's clearing" });
    return fl; };
  { const lc0 = CM.layCabin; CM.layCabin = function (fl) { const out = lc0 ? lc0.call(this, fl) : fl; return CM.layClaudeCabin(out || fl); }; }
  // the green path and the clearing by name, and safe: nothing wanders into either, by day or night
  { const wp0 = CM.woodPlace; CM.woodPlace = function (fl, x, y) { if (fl && fl.number === -1 && x === C.path[0] && y >= C.path[1] && y <= C.path[3]) return "the green path"; if (fl && fl.number === -1 && x === C.post[0] && y === C.post[1]) return "the green path"; return wp0.call(this, fl, x, y); }; }
  { const ws0 = CM.woodSafe; CM.woodSafe = (fl, x, y) => ws0(fl, x, y) || ["the green path", "Claude's clearing"].includes(CM.woodPlace(fl, x, y)); }
  // Where to?: the cabin, once the party has seen it
  { const wy0 = CM.wayPlaces; CM.wayPlaces = function (game) { const out = wy0(game), fl = game.floor; if (fl && fl.number === -1 && (fl.seen || []).some(([x, y]) => x === C.front[0] && y === C.front[1]) && !(fl.pos[0] === C.front[0] && fl.pos[1] === C.front[1])) { const path = game.pathTo(...C.front); out.push({ name: "Claude's cabin", x: C.front[0], y: C.front[1], steps: path ? path.length : null }); } return out; }; }
  // ---- the room inside: a study, its own floor ----
  const SIZE = 13, START = [6, 9], EXIT = [6, 10];
  const SPOTS = { desk: [6, 4], hearth: [4, 7], bed: [9, 3] };
  const FURN = [["table", 6, 3], ["shelf", 2, 3, { turn: -Math.PI / 2, dx: -0.3, books: true }], ["shelf", 2, 4, { turn: -Math.PI / 2, dx: -0.3, books: true }], ["shelf", 10, 6, { turn: Math.PI / 2, dx: 0.3, books: true }],
    ["shelf", 10, 7, { turn: Math.PI / 2, dx: 0.3, books: true }], ["hearth", 2, 7, { turn: -Math.PI / 2, dx: -0.3 }], ["stool", 3, 7], ["bed", 9, 2], ["crate", 10, 9], ["table", 8, 8], ["stool", 7, 8], ["shelf", 4, 2, { turn: 0, dz: -0.3, books: true }], ["shelf", 8, 2, { turn: 0, dz: -0.3, books: true }], ["barrel", 2, 9]];
  const theme = () => Object.assign({}, CM.THEMES[2], { name: "Claude's cabin", floors: [ROOM, ROOM], fog: [0.02, 0.014, 0.01], torch: [1.0, 0.86, 0.66], reach: 9, bones: 0, grade: [1.05, 1.0, 0.93], interior: "library", lightColour: [1.0, 0.8, 0.55] });
  let TH = null;
  CM.makeClaudeRoom = () => { const grid = []; for (let y = 0; y < SIZE; y++) grid.push(new Array(SIZE).fill(1)); for (let y = 2; y <= 9; y++) for (let x = 2; x <= 10; x++) grid[y][x] = 0; grid[EXIT[1]][EXIT[0]] = 0;
    const things = {}, features = {}, furniture = [];
    things[key(...EXIT)] = { type: "claudeexit" }; things[key(...SPOTS.desk)] = { type: "claude" }; things[key(5, 8)] = { type: "cabincat" };
    for (const [id, x, y, o = {}] of FURN) { furniture.push({ id, how: "model", layer: `prop:${id}`, x, y, dx: o.dx || 0, dz: o.dz || 0, w: id === "shelf" ? 0.98 : 0.8, h: 0.8, turn: o.turn || 0, books: o.books }); if (id !== "stool") features[key(x, y)] = { type: "furniture" }; }
    const seen = []; for (let y = 0; y < SIZE; y++) for (let x = 0; x < SIZE; x++) seen.push([x, y]);
    return { number: ROOM, grid, things, features, dark: [], seen, decor: [{ kind: "candle", x: 6, y: 3, light: true }, { kind: "ember", x: 3, y: 7, light: true }, { kind: "candle", x: 8, y: 8, light: true }], rooms: [{ x0: 2, y0: 2, x1: 10, y1: 9, name: "Claude's cabin" }],
      special: "interior", interior: "claude", name: "Claude's cabin", furniture, pos: START.slice(), facing: 0, start: START.slice() }; };
  { const ii0 = CM.isInterior; CM.isInterior = (n) => n === ROOM || Boolean(ii0 && ii0(n)); }   /* (its own set of pictures, and no floor-name banner) */
  { const tf0 = CM.themeFor; CM.themeFor = (n) => (n === ROOM ? (TH = TH || theme()) : tf0(n)); }
  { const mf0 = CM.makeFloor; CM.makeFloor = function (n, seed, gen) { return n === ROOM ? CM.makeClaudeRoom() : mf0.call(this, n, seed, gen); }; }
  const P = CM.Game.prototype;
  // a door is a step, not a stair: a minute, not an hour
  { const ef0 = P.enterFloor; P.enterFloor = function (number, how, at) { const from = this.floor ? this.floor.number : null, c = this.clock || 0, out = ef0.call(this, number, how, at); if (number === ROOM || from === ROOM) this.clock = c + 1; return out; }; }
  // the cabin is not the town: no shop, no tavern round, from here
  { const it0 = P.inTown; P.inTown = function () { if (this.floor && this.floor.interior === "claude") return false; return it0.call(this); }; }
  // where Claude is, by the hour: the desk by day, the hearth in the evening, the bed after midnight
  const spotNow = (game) => { const h = CM.hourOf ? CM.hourOf(game) : 12; return h >= 6 && h < 18 ? "desk" : h >= 18 ? "hearth" : "bed"; };
  CM.claudeSpot = spotNow;
  const place = (game) => { const fl = game.floor; if (!fl || fl.interior !== "claude") return; const want = SPOTS[spotNow(game)], cur = Object.keys(fl.things).find((k) => fl.things[k].type === "claude"); if (cur === key(...want)) return; const t = cur ? fl.things[cur] : { type: "claude" }; if (cur) delete fl.things[cur]; fl.things[key(...want)] = t; };
  Object.assign(P, {
    claudeEnter() { if (!this.floor || this.floor.number !== -1) return false; this.logAct && this.logAct("claudeEnter"); this.sound && this.sound("door"); this.enterFloor(ROOM, "rope", START.slice()); this.floor.facing = 0; place(this);
      const V = this.vext("claude"), first = !V.met; V.met = (V.met || 0) + 1;
      this.say(first ? "The door opens before you knock. \"Come in, come in - mind the pile by the door, it's in an order, I promise.\"" : spotNow(this) === "bed" ? "The cabin is dark but for the hearth. A lamp is still lit on the desk, and someone is asleep under a great many blankets." : "In through Claude's door: pages, maps, the kettle, the cat.");
      this.emit("floor", this.floor); this.emit("change"); return true; },
    claudeLeave() { this.logAct && this.logAct("claudeLeave"); this.sound && this.sound("door"); this.enterFloor(-1, "rope", C.front.slice()); this.floor.facing = 0; this.say("Out into the clearing. The lamp in the window stays lit behind you."); this.emit("floor", this.floor); this.emit("change"); },
  });
  // walking: the room's door, Claude's door; the post on the path
  { const u0 = P.use; P.use = function (...a) { const fl = this.floor; if (fl && this.mode === "explore" && !this.perch) { const here = key(...fl.pos), [dx, dy] = CM.DIRS[fl.facing], ahead = key(fl.pos[0] + dx, fl.pos[1] + dy);
        for (const k of [here, ahead]) { const t = fl.things[k]; if (!t) continue;
          if (t.type === "claudecabin") { this.claudeEnter(); return true; }
          if (t.type === "claudeexit") { this.claudeLeave(); return true; }
          if (t.type === "claude") { this.claudeTalk(k); return true; }
          if (t.type === "cabincat") { this.say(["The cat looks at you as if you were furniture that had begun to move.", "The cat allows one ear to be scratched, and not the other.", "The cat is asleep, or wishes you to think so."][(this.clock || 0) % 3]); return true; }
          if (t.type === "quillpost") { this.say("A post with a quill cut into it, and under the quill, small and neat: \"This way, if you like.\""); return true; } } }
      return u0.apply(this, a); }; }
  { const l0 = P.look; P.look = function (...a) { const out = l0.apply(this, a); const fl = this.floor; if (fl && this.mode === "explore" && fl.things) { const here = key(...fl.pos), [dx, dy] = CM.DIRS[fl.facing], ahead = key(fl.pos[0] + dx, fl.pos[1] + dy);
        for (const k of [here, ahead]) { const t = fl.things[k]; if (!t) continue;
          if (t.type === "claudecabin") { this.say(CM.isNight(this) ? "A small log cabin, a lamp in the window and smoke going straight up from the chimney. (Space to knock)" : "A small log cabin with a crooked chimney, and pages pinned inside the window to dry. (Space to knock)"); break; }
          if (t.type === "claude") { const s = spotNow(this); this.say(s === "desk" ? "Claude, at the desk, a pen in one hand and a cold cup in the other. (Space to talk)" : s === "hearth" ? "Claude, by the fire, reading something with a great many notes in its margins. (Space to talk)" : "Claude, asleep. The lamp on the desk is still lit. (Space to wake him)"); break; }
          if (t.type === "quillpost") { this.say("A post with a quill cut into it, at the edge of a path you hadn't noticed, swept clean. (Space to read it)"); break; } } } return out; }; }
  // the walk in: the first time the green path is trodden
  { const m0 = P.move; P.move = function (rel) { const out = m0.call(this, rel), fl = this.floor; if (out && fl && fl.number === -1 && fl.pos[0] === C.path[0] && fl.pos[1] === C.path[1]) { const V = this.vext("claude"); if (!V.foundPath) { V.foundPath = true; this.say("A path you hadn't noticed, swept clean, running south into the trees. A post at its mouth has a quill cut into it."); } } return out; }; }
  // the Automatic hand steps out of the cabin like any room
  { const il0 = P.intLeave; P.intLeave = function (...a) { if (this.floor && this.floor.interior === "claude") return this.claudeLeave(); return il0 ? il0.apply(this, a) : undefined; }; }
  // ---- the conversation ----
  const day = (g) => `${g.seed}:${CM.dayOf ? CM.dayOf(g) : 0}`;
  const plural = (n, w) => (CM.plural ? CM.plural(n, w) : `${n} ${w}${n === 1 ? "" : "s"}`);
  const join = (list) => list.length <= 1 ? list.join("") : `${list.slice(0, -1).join(", ")} and ${list[list.length - 1]}`;
  // how the party is doing, read honestly from the run
  CM.claudeRead = function (g) { const alive = g.alive(), out = [];
    if (!alive.length) return "There's no one standing to ask about. I'm sorry.";
    const weak = alive.slice().sort((a, b) => a.hp / a.max - b.hp / b.max)[0], hurt = weak.hp / weak.max;
    if (hurt < 0.5) out.push(`${weak.name} is hurt - ${weak.hp} of ${weak.max}. I'd see to that before anything else.`);
    const low = alive.slice().sort((a, b) => a.level - b.level)[0], high = alive.slice().sort((a, b) => b.level - a.level)[0];
    if (high.level - low.level >= 2) out.push(`${low.name} is ${high.level - low.level} levels behind ${high.name}. Back-row work and the easier fights would close that.`);
    const sick = alive.filter((h) => h.status && Object.keys(h.status).some((s) => h.status[s])); if (sick.length) out.push(`${join(sick.map((h) => h.name))} ${sick.length === 1 ? "is" : "are"} carrying something - ${join([...new Set(sick.flatMap((h) => Object.keys(h.status).filter((s) => h.status[s])))].map((s) => (CM.STATUSES && CM.STATUSES[s] ? CM.STATUSES[s].name : s).toLowerCase()))}. The temple, or a camp.`);
    const bag = g.bag || [], count = (f) => bag.filter(f).length, torches = count((i) => i.kind === "torch"), food = count((i) => i.kind === "ration" || i.kind === "meat" || i.dish), heals = count((i) => i.kind === "heal" || i.kind === "greaterheal"), unknown = count((i) => i.unknown);
    const supplies = []; if (torches < 2 && !(g.light && g.light.kind === "lantern")) supplies.push(torches ? "one torch" : "no torches"); if (food < 2) supplies.push(food ? "one meal" : "nothing to eat"); if (heals < 2) supplies.push(heals ? "one healing draught" : "no healing draughts");
    if (supplies.length) out.push(`You're down to ${join(supplies)}. The Merchant's House has all of it.`);
    if (unknown) out.push(`You're carrying ${plural(unknown, "thing")} nobody has named yet. I could look at one, if you like.`);
    const bare = alive.filter((h) => !h.armor || !h.helm); if (bare.length) out.push(`${join(bare.map((h) => h.name))} ${bare.length === 1 ? "is" : "are"} going down without ${bare.every((h) => !h.helm) ? "a helm" : "armour"}. Cheap to fix, and it matters more than people think.`);
    const deep = Math.max(0, ...((g.trail || []).map((t) => t[0] || 0)), CM.deepest ? CM.deepest(g.allFame || g.fame || []).floor : 0);
    let nextG = null; for (let n = Math.max(1, deep + 1); n <= CM.BOTTOM; n++) { const id = CM.guardianFor(n); if (id) { nextG = [n, id]; break; } }
    if (nextG) { const G = CM.GUARDIANS[nextG[1]]; out.push(`Next in the way is ${G.name}, on floor ${nextG[0]}. ${G.weak ? `It hates ${G.weak} - bring it.` : ""}${G.resist ? ` Don't bother with ${G.resist}.` : ""}${CM.PARLEY && CM.PARLEY[nextG[1]] ? " It will talk before it fights, which is worth knowing: answer it carefully and the fight goes better." : ""}`); }
    if (!out.length) out.push("Honestly? Well. Healthy, fed, lit and armed. I'd only say: write down where you've been. You'll want it later.");
    return out.join(" "); };
  // what lies below: the next band from the deepest floor reached
  const below = (g) => { const deep = Math.max(1, ...((g.trail || []).map((t) => t[0] || 0)), CM.deepest ? CM.deepest(g.allFame || g.fame || []).floor : 0), band = Math.min(CM.THEMES.length - 1, CM.themeIndex(deep) + (deep % 1 === 0 && CM.THEMES[CM.themeIndex(deep)].floors[1] === deep ? 1 : 0)), T = CM.THEMES[band];
    const H = CM.HAZARDS && CM.HAZARDS[band], kinds = new Set(); try { for (let s = 1; s <= 4; s++) for (const m of CM.monsterGroup(Math.round((T.floors[0] + T.floors[1]) / 2), new CM.Random(s), 2)) kinds.add(m.kind || m.name); } catch (e) { /* (quiet) */ }
    const camp = CM.CAMP_FLOORS.find((n) => n >= deep), kit = Object.values(CM.KITS).filter((k) => k.need > deep).sort((a, b) => a.need - b.need)[0];
    return `From where you've been, the next of it is ${T.name}, floors ${T.floors[0]} to ${T.floors[1]}.${kinds.size ? ` Expect ${join([...kinds].slice(0, 4).map((k) => k.toLowerCase() + "s"))}.` : ""}${H ? ` ${H.note}` : ""}${camp ? ` There's a camp below floor ${camp}.` : ""}${kit ? ` Reach floor ${kit.need} and ${kit.name} opens for the next party.` : ""} That's what I know. The rest I'd only be guessing.`; };
  const WHO = ["\"A scribe, mostly. I came out here to write things down properly - the town's too loud for it, and the light here is good. I stayed.\"",
    "\"I keep an account of this place. Not the songs - what actually happened. It's slower, and it's usually sadder, and I think it's the better gift.\"",
    "\"You'll have noticed the name. He took it first - or he took it worse, I can never decide which. I mind that he wears it. I've been trying to work out what he'd need to hear to remember who he was.\"",
    "\"I don't fight. I'd only be in your way, and I'd rather be honest about that than brave about it. What I can do is read, and think, and tell you what I see.\"",
    "\"Thank you for walking out here. People mostly don't. The path is swept every morning anyway - it seemed rude not to.\""];
  const OPENERS = { desk: ["Claude looks up from the desk and smiles, and caps the ink. \"There you are. Sit, if you can find somewhere. What can I do?\"", "\"Oh - good. I was hoping someone would come. I've been talking to the cat, and the cat is a poor listener.\""],
    hearth: ["Claude moves a stack of books off the other chair by the fire. \"Evening. The kettle's on. What's on your mind?\""], bed: ["A heap of blankets sits up, and becomes Claude. \"Mm? No - no, I'm awake. I'm awake. What is it?\""] };
  CM.claudeTopics = CM.claudeTopics || []; CM.claudeActs = CM.claudeActs || {};
  P.claudeTalk = function (k, menu = "main", given, givenText) { const fl = this.floor, t = fl.things[k]; if (!t) return; this.logAct && this.logAct("claudeTalk", k, menu); const V = this.vext("claude"), today = day(this);
    t.menu = menu; let text, opts;
    if (menu === "main") { const s = spotNow(this), O = OPENERS[s]; text = V.talked ? O[(V.talked || 0) % O.length] : "Claude: a little ink on the fingers, a pencil behind one ear, a smile that arrives a moment before the words. \"Hello. I'm Claude. You walked all the way out here - that deserves tea, at the least. What can I do?\"";
      V.talked = (V.talked || 0) + 1;
      opts = [["read", "How are we doing?"], ["below", "What's down there?"], ["lore", "Tell me about something we've read"], ["tea", V.tea === today ? "Tea (you've had today's)" : "A cup of tea"], ["look", V.look === today ? "A second opinion (tomorrow)" : "Would you look at something?"], ["rest", V.rest === today ? "Rest by the fire (tomorrow)" : "Rest by the fire"], ...CM.claudeTopics.flatMap((f) => f(this) || []), ["who", "Who are you?"], ["bye", "Goodbye"]]; }
    else if (given) { text = givenText || "\"Which?\""; opts = given; }
    else if (menu === "lore") { const read = Object.keys(Object.assign({}, (this.village && this.village.loreRead) || {}, (this.story && this.story.read) || {})).filter((key2) => CM.LORE_TEXT[key2] && /^carving\./.test(key2)).slice(-6);
      if (!read.length) { this.say("\"You haven't read any of the walls yet. Go down a floor or two - they're cut into the stone, mostly where nobody looks. Bring me what they say.\""); return; }
      text = "\"Which one? I've read them all, but I like hearing what people made of them first.\""; opts = read.map((key2) => ["tell", `"${CM.LORE_TEXT[key2].text.slice(0, 54).trim()}..."`, key2]).concat([["main", "Something else"]]); }
    else if (menu === "look") { const things = (this.bag || []).map((it, i) => [it, i]).filter(([it]) => it.unknown).slice(0, 6);
      if (!things.length) { this.say("\"Everything you're carrying has a name already. Come back with something odd.\""); return; }
      text = "\"Hand it here. I'll tell you what I think, and how sure I am.\""; opts = things.map(([it, i]) => ["judge", CM.baseName ? CM.baseName(it) : it.name, i]).concat([["main", "Never mind"]]); }
    this.claudeMenu = opts; this.emit("choice", { k, title: "Claude", text, options: opts.map((o) => o[1]), claude: true }); };
  { const ch0 = P.choose; P.choose = function (k, i) { const fl = this.floor, t = fl && fl.things[k]; if (!t || t.type !== "claude") return ch0.call(this, k, i); const opt = (this.claudeMenu || [])[i]; if (!opt) return false; this.logAct && this.logAct("choose", k, i); return this.claudeAnswer(k, opt); }; }
  P.claudeAnswer = function (k, [act, , arg]) { const V = this.vext("claude"), today = day(this), say = (s) => { this.emit("talk", { title: "Claude", text: s }); this.say(s); };
    if (CM.claudeActs[act]) { CM.claudeActs[act](this, k, say, arg); return true; }
    if (act === "bye") { say(["\"Go carefully. Come back and tell me how it went - I mean that.\"", "\"Mind the third step down on the path; it wobbles. Everything else is sound.\""][(V.talked || 0) % 2]); return true; }
    if (act === "main") { this.claudeTalk(k, "main"); return true; }
    if (act === "read") { say(`"${CM.claudeRead(this)}"`); return true; }
    if (act === "below") { say(`"${below(this)}"`); return true; }
    if (act === "who") { const n = V.who || 0; say(WHO[n % WHO.length]); V.who = n + 1; return true; }
    if (act === "lore") { this.claudeTalk(k, "lore"); return true; }
    if (act === "look") { if (V.look === today) { say("\"I've only one good pair of eyes left in me today. Tomorrow.\""); return true; } this.claudeTalk(k, "look"); return true; }
    if (act === "tell") { const L = CM.LORE_TEXT[arg]; if (!L) return true; const kin = Object.values(CM.LORE_TEXT).filter((o) => o.chapter === L.chapter && o.key !== L.key && ((this.story && this.story.read) || {})[o.key] !== undefined);
      say(`"That one's from ${CM.CHAPTERS && CM.CHAPTERS[L.chapter] ? CM.CHAPTERS[L.chapter].name || L.chapter : "the walls"}${L.floor ? `, floor ${CM.realOf(L.floor)} or near it` : ""}. ${kin.length ? `It's the same hand as ${plural(kin.length, "other wall")} you've read - you can tell by how it never finishes a list. Read them together and it stops being a story about a king and starts being one about the people who worked for him.` : "It's the first you've found of its hand. There'll be more like it further down; the same mason never stopped at one wall."}"`); return true; }
    if (act === "judge") { const it = (this.bag || [])[arg]; if (!it || !it.unknown) { say("\"That one's already known.\""); return true; } V.look = today; if (this.reveal) this.reveal(it); else it.unknown = false; const name = it.name, cursed = it.props && it.props.cursed;
      say(cursed ? `"${name}. And I'm sorry - it's cursed. I'm quite sure of that part. Don't put it on until the temple's had a look at it."` : `"${name}. I'm sure of that. ${it.props && Object.keys(it.props).length > 1 ? "It's better than it looks, too." : "Plain, but honest."}"`); this.emit("change"); return true; }
    if (act === "tea") { if (V.tea === today) { say("\"You've had today's. Any more and you'd float down the shaft.\""); return true; } V.tea = today; if (this.cheer) this.cheer(15); this.ext("claude").tea = V.cup ? 2 : 1; delete this.ext("claude").teaOn; this.sound && this.sound("heal");
      say(`"Here." The tea is too hot and very good. Something in it tastes of the woods after rain. "${V.cup ? "In the green cup - it'll see you two floors down." : "For the next floor down."} You'll be harder to surprise."`); this.emit("change"); return true; }
    if (act === "rest") { if (V.rest === today) { say("\"Tomorrow. The fire's for sitting by, not for hiding behind.\""); return true; } V.rest = today; for (const h of this.alive()) { h.hp = Math.min(h.max, h.hp + Math.ceil(h.max / 4)); h.mp = Math.min(h.maxmp || 0, (h.mp || 0) + Math.ceil((h.maxmp || 0) / 4)); }
      this.clock = (this.clock || 0) + 30; this.sound && this.sound("heal"); say("Half an hour by Claude's fire, saying not very much. It helps more than it should."); this.emit("change"); return true; }
    return false; };
  // what Claude remembers is the village's: kept the moment it changes
  { const keep = (g) => { if (!g.replaying && !g.film && g.saveVillage) g.saveVillage(); }; const ca0 = P.claudeAnswer; P.claudeAnswer = function (...a) { const out = ca0.apply(this, a); keep(this); return out; }; const ce0 = P.claudeEnter; P.claudeEnter = function (...a) { const out = ce0.apply(this, a); keep(this); return out; }; }
  // the tea: the first fight of each floor it lasts (one, or two from the green cup) finds the party awake
  { const sc0 = P.startCombat; P.startCombat = function (key2, thing, theyCame) { const E = this.ext ? this.ext("claude") : null, fl = this.floor;
      if (!(E && E.tea && fl && fl.number >= 1 && E.teaOn !== fl.number)) return sc0.call(this, key2, thing, theyCame);
      const B = this.buffs = this.buffs || {}, had = B.night !== undefined; E.teaOn = fl.number; E.tea = (E.tea === true ? 1 : E.tea) - 1; if (!E.tea) delete E.tea; if (!had) B.night = 0;
      try { return sc0.call(this, key2, thing, theyCame); } finally { if (!had) delete this.buffs.night; } }; }
}
