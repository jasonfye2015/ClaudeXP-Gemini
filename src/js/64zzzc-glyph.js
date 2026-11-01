"use strict";
// The Glyph Deep (v20.0, UPGRADE_PLAN_15.md): the game inside the arcade cabinet by the Wood's road - a roguelike in
// letters, turn by turn, twenty levels of rooms and corridors for one hero. This file is the game: the levels, the
// monsters (the main game's numbers under the deep's own names and letters), the things, the hero's turn and the
// monsters'. The cabinet, the rewards and the way home are 69o-glyphdeep.js; the screen is 76zzzp-glyph.js.
//
//   new CM.GlyphRun(game, heroIndex, level)  -> a run on that level
//   run.act(cmd, arg)                        -> the hero's turn ("move" [dx,dy], "pick", "quaff" i, "read" i, "wield" i,
//                                               "wear" i, "eat" i, "drop" i, "wait"); then the monsters'. Returns the
//                                               messages; run.over is "dead" when the hero falls.
//   run.atDown() / run.atUp()                -> standing on the stairs
{ const GD = CM.GLYPH = { W: 80, H: 21, levels: 20, xpShare: 0.6, regenEvery: 9 };
  // the tuning (tools/glyphbot.js measured it): a monster's level by the level, how many, the Unwritten's level and health
  GD.TRAPS = ["dart", "pit", "teleport", "gong"];
  Object.assign(GD, { monLevel: (L) => Math.max(1, Math.round(L * 0.85)), monCount: (L) => 3 + Math.floor(L / 3), bossLevel: 21, bossHp: 3.2, bossAtk: 0.75, bossWrites: 6, lastCrowd: 4, minionLevel: 10 });
  // the deep's monsters: [letter, name, colour, the main game's kind for its numbers, speed, first level, last level, ways]
  GD.MONSTERS = [
    ["r", "cellar rat", "#B08A60", "Giant Rat", 1, 1, 6, ""], ["b", "cave bat", "#A080C0", "Giant Rat", 2, 1, 7, "erratic"], ["j", "grey ooze", "#90B090", "Sporeling", 0.5, 1, 8, ""],
    ["g", "goblin", "#70B040", "Goblin", 1, 2, 9, ""], ["k", "knocker", "#C0A060", "Kobold", 1, 2, 8, ""], ["s", "web-spinner", "#C0C0C0", "Cellar Spider", 1, 4, 11, ""],
    ["Z", "skeleton", "#E8E8D8", "Skeleton", 1, 4, 12, ""], ["w", "grey wolf", "#A0A0A8", "Wolf", 1.5, 5, 12, ""], ["o", "orc", "#C05040", "Orc", 1, 6, 13, ""],
    ["z", "ghoul", "#7A9A6A", "Ghoul", 1, 7, 14, ""], ["i", "ember imp", "#F07040", "Foundry Imp", 1.5, 8, 15, ""], ["m", "mimic", "#F0C040", "Mimic", 1, 8, 18, "mimic"],
    ["T", "troll", "#50A050", "Troll", 1, 9, 17, "regen"], ["W", "wraith", "#9090E0", "Wraith", 1, 10, 18, "drain"], ["O", "ogre", "#D09050", "Ogre", 1, 12, 19, ""],
    ["h", "charnel hound", "#C06060", "Charnel Hound", 2, 12, 20, ""], ["G", "glass golem", "#A0E8F8", "Crystal Golem", 0.5, 13, 20, ""], ["V", "vampire", "#E03050", "Vampire", 1, 15, 20, "drain"],
    ["D", "red drake", "#F05020", "Wyvern", 1, 16, 20, "breath"],
  ];
  GD.BOSS = ["&", "the Unwritten", "#FF60FF", "Demon", 1, 20, 20, "boss"];
  GD.MINION = ["?", "loose glyph", "#E0A0FF", "Giant Rat", 2, 20, 20, ""];
  // what a thing looks like on the floor
  GD.glyphOf = (it) => ({ weapon: ")", armor: "[", shield: "[", helm: "[", ring: "=", amulet: "\"", heal: "!", mana: "!", ration: "%", seed: ",", gscroll: "?", gcard: "~", gtickets: "*", ggold: "$" })[it.kind] || "(";
  GD.colourOf = (it) => ({ weapon: "#C0C8D0", armor: "#B09070", shield: "#B09070", helm: "#B09070", ring: "#F0D040", amulet: "#F0A040", heal: "#F06060", mana: "#6080FF", ration: "#C08040", seed: "#80D060", gscroll: "#F0F0C0", gcard: "#E080E0", gtickets: "#F0C040", ggold: "#F0D040" })[it.kind] || "#FFFFFF";
  GD.SCROLLS = { mapping: "magic mapping", teleport: "teleportation", fire: "fire", enchantWeapon: "enchant weapon", enchantArmour: "enchant armour" };
  GD.scroll = (sub) => ({ name: `Scroll of ${GD.SCROLLS[sub]}`, kind: "gscroll", sub, power: 0, value: 15 });
  GD.depthOf = (L) => Math.max(1, Math.min(CM.BOTTOM || 50, Math.round(L * 2.4)));
  const DIRS8 = [[0, -1], [1, 0], [0, 1], [-1, 0], [1, -1], [1, 1], [-1, 1], [-1, -1]];
  const key = (x, y) => `${x},${y}`;

  CM.GlyphRun = class {
    constructor(game, heroIndex, level, carry) {
      this.game = game; this.heroIndex = heroIndex; this.hero = game.party[heroIndex]; this.L = level; this.turn = 0; this.msgs = []; this.over = null;
      this.rnd = new CM.Random(CM.hashSeed(`${game.seed}:glyph:${level}:${(game.village && game.village.glyph && game.village.glyph.runs) || 0}`));
      Object.assign(this, { pack: [], gold: 0, levelGold: 0, xp: 0, kills: 0, wield: null, wear: null }, carry || {});
      this.hp = Math.max(1, this.hero.hp); this.max = this.hero.max;
      this.make();
    }
    // ---- the level ----
    make() { const W = GD.W, H = GD.H, R = this.rnd, g = this.grid = Array.from({ length: H }, () => Array(W).fill(" "));
      const cw = Math.floor(W / 3), ch = Math.floor(H / 3), rooms = [];
      for (let cy = 0; cy < 3; cy++) for (let cx = 0; cx < 3; cx++) { const bx = cx * cw, by = cy * ch;
        if (R.chance(0.82) || this.L === GD.levels && cx === 1 && cy === 1) { const big = this.L === GD.levels && cx === 1 && cy === 1, w = big ? cw - 4 : R.int(4, cw - 6), h = big ? ch - 2 : R.int(2, ch - 3), x0 = bx + R.int(2, Math.max(2, cw - w - 3)), y0 = by + R.int(1, Math.max(1, ch - h - 2));
          rooms.push({ cx, cy, x0, y0, x1: x0 + w - 1, y1: y0 + h - 1, room: true }); }
        else { const x = bx + R.int(3, cw - 4), y = by + R.int(2, ch - 3); rooms.push({ cx, cy, x0: x, y0: y, x1: x, y1: y, room: false }); } }
      for (const r of rooms) if (r.room) { for (let y = r.y0 - 1; y <= r.y1 + 1; y++) for (let x = r.x0 - 1; x <= r.x1 + 1; x++) g[y][x] = y === r.y0 - 1 || y === r.y1 + 1 ? "-" : x === r.x0 - 1 || x === r.x1 + 1 ? "|" : "."; }
        else g[r.y0][r.x0] = "#";
      this.rooms = rooms; const at = (cx, cy) => rooms.find((r) => r.cx === cx && r.cy === cy);
      // a tree over the 3x3, and a couple more joins
      const edges = []; for (let cy = 0; cy < 3; cy++) for (let cx = 0; cx < 3; cx++) { if (cx < 2) edges.push([at(cx, cy), at(cx + 1, cy)]); if (cy < 2) edges.push([at(cx, cy), at(cx, cy + 1)]); }
      R.shuffle(edges); const set = new Map(rooms.map((r) => [r, r])), find = (r) => { while (set.get(r) !== r) r = set.get(r); return r; }; let extra = 2;
      for (const [a, b] of edges) { const fa = find(a), fb = find(b); if (fa !== fb) { set.set(fa, fb); this.join(a, b); } else if (extra > 0 && R.chance(0.4)) { extra--; this.join(a, b); } }
      // the stairs: up in one room, down in the one farthest from it
      const real = rooms.filter((r) => r.room), start = this.L === GD.levels ? real.find((r) => !(r.cx === 1 && r.cy === 1)) || real[0] : R.pick(real); this.up = this.spot(start);
      g[this.up[1]][this.up[0]] = "<"; this.x = this.up[0]; this.y = this.up[1];
      const dist = this.distances(this.x, this.y); let far = null;
      if (this.L === GD.levels) { const B = at(1, 1); far = [Math.floor((B.x0 + B.x1) / 2), Math.floor((B.y0 + B.y1) / 2) + 1]; }
      else for (const r of real) if (r !== start) for (let y = r.y0; y <= r.y1; y++) for (let x = r.x0; x <= r.x1; x++) { const d = dist.get(key(x, y)); if (d !== undefined && (!far || d > far[2])) far = [x, y, d]; }
      if (!far) far = this.spot(start); this.down = [far[0], far[1]]; g[this.down[1]][this.down[0]] = ">";
      this.seen = new Set(); this.things = new Map(); this.mons = [];
      this.stock(start); this.layTraps(); this.see(); }
    // traps (v20.1): hidden in the floor until stepped on - a dart, a pit, a teleport, a gong that wakes the level
    layTraps() { const R = this.rnd; this.traps = new Map(); const n = 1 + Math.floor(this.L / 4);
      for (let i = 0; i < n; i++) { const r = R.pick(this.rooms.filter((q) => q.room)), [x, y] = this.spot(r); if ((x === this.x && y === this.y) || this.tile(x, y) !== ".") continue; this.traps.set(key(x, y), { kind: R.pick(GD.TRAPS), found: false }); } }
    spring(x, y) { const T = this.traps && this.traps.get(key(x, y)); if (!T) return; T.found = true; const R = this.rnd, L = this.L;
      this.killer = `a ${T.kind} trap`; if (T.kind === "dart") this.hurt(R.int(2, 5) + L * 2, "A little dart shoots out at you!");
      else if (T.kind === "pit") { this.stuck = 2; this.hurt(R.int(3, 6) + L, "You fall into a pit!"); }
      else if (T.kind === "teleport") { const r = R.pick(this.rooms.filter((q) => q.room)), [nx, ny] = this.spot(r); this.x = nx; this.y = ny; this.say("A trap door of light: you are somewhere else."); }
      else { for (const m of this.mons) m.asleep = false; this.say("A gong sounds deep in the floor. Everything on the level wakes."); } }
    join(a, b) { const g = this.grid, R = this.rnd; let p, q;
      if (a.cy === b.cy) { const [l, r] = a.cx < b.cx ? [a, b] : [b, a]; p = l.room ? [l.x1 + 1, R.int(l.y0, l.y1)] : [l.x0, l.y0]; q = r.room ? [r.x0 - 1, R.int(r.y0, r.y1)] : [r.x0, r.y0];
        if (l.room) g[p[1]][p[0]] = "+"; if (r.room) g[q[1]][q[0]] = "+"; const mx = R.int(Math.min(p[0] + 1, q[0] - 1), Math.max(p[0] + 1, q[0] - 1));
        this.dig(p[0] + (l.room ? 1 : 0), p[1], mx, p[1]); this.dig(mx, p[1], mx, q[1]); this.dig(mx, q[1], q[0] - (r.room ? 1 : 0), q[1]); }
      else { const [t, d] = a.cy < b.cy ? [a, b] : [b, a]; p = t.room ? [R.int(t.x0, t.x1), t.y1 + 1] : [t.x0, t.y0]; q = d.room ? [R.int(d.x0, d.x1), d.y0 - 1] : [d.x0, d.y0];
        if (t.room) g[p[1]][p[0]] = "+"; if (d.room) g[q[1]][q[0]] = "+"; const my = R.int(Math.min(p[1] + 1, q[1] - 1), Math.max(p[1] + 1, q[1] - 1));
        this.dig(p[0], p[1] + (t.room ? 1 : 0), p[0], my); this.dig(p[0], my, q[0], my); this.dig(q[0], my, q[0], q[1] - (d.room ? 1 : 0)); } }
    dig(x0, y0, x1, y1) { const g = this.grid; for (let x = Math.min(x0, x1); x <= Math.max(x0, x1); x++) for (let y = Math.min(y0, y1); y <= Math.max(y0, y1); y++) if (g[y][x] === " ") g[y][x] = "#"; }
    spot(r) { for (let t = 0; t < 80; t++) { const x = this.rnd.int(r.x0, r.x1), y = this.rnd.int(r.y0, r.y1); if (this.grid[y][x] === "." && !this.thingAt(x, y) && !(this.mons || []).some((m) => m.x === x && m.y === y)) return [x, y]; } return [r.x0, r.y0]; }
    // what's put about: the monsters, the gold, the things
    stock(start) { const R = this.rnd, L = this.L, real = this.rooms.filter((r) => r.room), others = real.filter((r) => r !== start);
      const kinds = GD.MONSTERS.filter((m) => L >= m[5] && L <= m[6]); const n = L === GD.levels ? GD.lastCrowd : GD.monCount(L) + R.int(0, 2);
      for (let i = 0; i < n && kinds.length; i++) { const r = R.pick(others.length ? others : real), [x, y] = this.spot(r); if (x === this.x && y === this.y) continue; this.addMon(R.pick(kinds), x, y, R.chance(0.45)); }
      if (L === GD.levels) { const B = this.rooms.find((r) => r.cx === 1 && r.cy === 1); this.addMon(GD.BOSS, Math.floor((B.x0 + B.x1) / 2), Math.floor((B.y0 + B.y1) / 2), false); for (let k = 0; k < 2; k++) { const [x, y] = this.spot(B); this.put(x, y, { name: "Healing Potion", kind: "heal", power: 20 + L * 4, value: 20 + L }); } }
      for (let i = 0, k = R.int(3, 5); i < k; i++) { const [x, y] = this.spot(R.pick(real)); this.put(x, y, { kind: "ggold", n: R.int(4, 10) + L * R.int(3, 7), name: "gold" }); }
      for (let i = 0, k = R.int(3, 5) + Math.floor(L / 5); i < k; i++) { const [x, y] = this.spot(R.pick(real)); this.put(x, y, this.makeThing()); } }
    makeThing() { const R = this.rnd, L = this.L, d = GD.depthOf(L), roll = R.next();
      if (roll < 0.2) return R.chance(0.7) ? { name: "Healing Potion", kind: "heal", power: 20 + L * 4, value: 20 + L } : { name: "Mana Potion", kind: "mana", power: 12 + L * 2, value: 25 };
      if (roll < 0.34) return GD.scroll(R.pick(Object.keys(GD.SCROLLS)));
      if (roll < 0.5) { const it = CM.makeItem(d, R, R.pick(["weapon", "armor", "shield", "helm"])); if (it && CM.affix && R.chance(0.15 + L * 0.02)) return CM.affix(it, d + 2, R); return it || CM.ration(); }
      if (roll < 0.56) { const it = CM.makeItem(d, R, R.chance(0.6) ? "ring" : "amulet"); return it || CM.ration(); }
      if (roll < 0.66) return CM.ration();
      if (roll < 0.78) { const FS = CM.FIELDSEEDS, common = Object.keys(CM.CROPS).filter((c) => CM.CROPS[c].seedPrice), pool = L >= 14 && FS && R.chance(0.3) ? Object.keys(FS.CHARMED) : L >= 7 && FS && R.chance(0.5) ? FS.RARE : common; return CM.seed(R.pick(pool)); }
      if (roll < 0.86) return { name: L >= 12 && R.chance(0.35) ? "a rare inscription card" : "an inscription card", kind: "gcard", rare: L >= 12 && R.chance(0.35), power: 0, value: 30 };
      return { name: "a roll of prize tickets", kind: "gtickets", n: 5 + L * 2 + R.int(0, L), power: 0, value: 0 }; }
    put(x, y, it) { const k = key(x, y); if (!this.things.has(k)) this.things.set(k, []); this.things.get(k).push(it); }
    thingAt(x, y) { const t = this.things && this.things.get(key(x, y)); return t && t.length ? t[t.length - 1] : null; }
    addMon(def, x, y, asleep) { const [ch, name, col, kind, speed, , , ways] = def, K = CM.monsterKind(kind) || CM.monsterKind("Goblin"), lvl = def === GD.BOSS ? GD.bossLevel : def === GD.MINION ? GD.minionLevel : GD.monLevel(this.L);
      const M = CM.makeMonster(K, lvl, this.rnd); if (def === GD.BOSS) { M.max = M.hp = Math.round(M.max * GD.bossHp); M.atk = Math.round(M.atk * GD.bossAtk); }
      const m = { ch, name, col, x, y, hp: M.hp, max: M.max, atk: M.atk, df: M.df, xp: M.xp, level: lvl, speed, energy: 0, asleep, ways, boss: def === GD.BOSS, cool: 0 }; if (ways === "mimic") m.hidden = true; this.mons.push(m); return m; }
    // ---- the map's rules ----
    tile(x, y) { return y >= 0 && y < GD.H && x >= 0 && x < GD.W ? this.grid[y][x] : " "; }
    open(x, y) { return [".", "#", "+", "<", ">"].includes(this.tile(x, y)); }
    monAt(x, y) { return this.mons.find((m) => m.hp > 0 && m.x === x && m.y === y); }
    // no slipping diagonally through a doorway
    canStep(x, y, dx, dy) { const nx = x + dx, ny = y + dy; if (!this.open(nx, ny)) return false; if (dx && dy && (this.tile(x, y) === "+" || this.tile(nx, ny) === "+")) return false; return true; }
    roomOf(x, y) { return this.rooms.find((r) => r.room && x >= r.x0 - 1 && x <= r.x1 + 1 && y >= r.y0 - 1 && y <= r.y1 + 1); }
    distances(x, y) { const out = new Map([[key(x, y), 0]]), q = [[x, y]]; while (q.length) { const [cx, cy] = q.shift(), d = out.get(key(cx, cy));
      for (const [dx, dy] of DIRS8) { const nx = cx + dx, ny = cy + dy, k = key(nx, ny); if (!out.has(k) && this.canStep(cx, cy, dx, dy)) { out.set(k, d + 1); q.push([nx, ny]); } } } return out; }
    // what the hero sees: the whole of a lit room they stand in, and a step around them
    see() { this.vis = new Set(); const r = this.roomOf(this.x, this.y); if (r && this.tile(this.x, this.y) !== "+") for (let y = r.y0 - 1; y <= r.y1 + 1; y++) for (let x = r.x0 - 1; x <= r.x1 + 1; x++) this.vis.add(key(x, y));
      for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) this.vis.add(key(this.x + dx, this.y + dy)); for (const k of this.vis) this.seen.add(k); }
    visible(x, y) { return this.vis.has(key(x, y)); }
    say(t) { this.msgs.push(t); }
    atDown() { return this.x === this.down[0] && this.y === this.down[1]; }
    atUp() { return this.x === this.up[0] && this.y === this.up[1]; }
    bossDown() { return !this.mons.some((m) => m.boss && m.hp > 0); }
    // ---- the hero's numbers: the game's own, with what's held in here ----
    heroAtk() { const g = this.game, eff = g.effective(this.hero); return { atk: eff.atk, power: this.wield ? this.wield.power || 1 : (this.hero.weapon ? this.hero.weapon.power || 1 : 1) }; }
    heroDf() { const g = this.game, h = this.hero; return g.effective(h).df + (CM.gearDefence ? CM.gearDefence(h) : 0) + (this.wear ? this.wear.power || 0 : 0); }
    // ---- a turn ----
    act(cmd, arg) { if (this.over) return []; this.msgs = []; const took = this.heroTurn(cmd, arg); if (took) { this.turn++; this.monsTurn(); if (this.turn % GD.regenEvery === 0 && this.hp < this.max) this.hp++; this.see(); } return this.msgs; }
    heroTurn(cmd, arg) { const R = this.rnd;
      if (cmd === "move") { const [dx, dy] = arg, nx = this.x + dx, ny = this.y + dy, m = this.monAt(nx, ny);
        if (m && !(m.ways === "mimic" && m.hidden)) { this.strike(m); return true; }
        if (m && m.ways === "mimic") { m.hidden = false; this.say("The gold grows teeth! It was a mimic."); return true; }
        if (!this.canStep(this.x, this.y, dx, dy)) { if (dx && dy && this.open(nx, ny)) this.say("You can't squeeze diagonally through a doorway."); return false; }
        if (this.stuck) { this.stuck--; this.say("You are still climbing out of the pit."); return true; }
        this.x = nx; this.y = ny; this.spring(nx, ny); if (this.over) return true; const t = this.thingAt(nx, ny); if (t) { const all = this.things.get(key(nx, ny)); this.say(all.length > 1 ? `There are ${all.length} things here.` : `You see here ${t.kind === "ggold" ? `${t.n} gold` : t.name}.`); }
        if (this.atDown()) this.say(this.L === GD.levels && !this.bossDown() ? "The way down is sealed while the Unwritten stands." : "There is a staircase down here. (>)"); return true; }
      if (cmd === "wait") return true;
      if (cmd === "pick") { const all = this.things.get(key(this.x, this.y)); if (!all || !all.length) { this.say("There is nothing here to pick up."); return false; }
        for (const it of all.splice(0)) { if (it.kind === "ggold") { this.gold += it.n; this.levelGold += it.n; this.say(`${it.n} gold.`); continue; }
          if (this.pack.length >= 26) { this.say("Your pack is full."); all.push(it); continue; } it.gfound = this.L; it.gsecure = false; this.pack.push(it); this.say(`${String.fromCharCode(97 + this.pack.length - 1)} - ${it.name}.`); } return true; }
      const it = this.pack[arg]; if (["quaff", "read", "wield", "wear", "eat", "drop"].includes(cmd) && !it) { this.say("You don't have that."); return false; }
      if (cmd === "quaff") { if (it.kind !== "heal" && it.kind !== "mana") { this.say("That isn't something to drink."); return false; } this.pack.splice(arg, 1);
        if (it.kind === "heal") { const n = Math.min(this.max - this.hp, it.power); this.hp += n; this.say(`You feel better (${n}).`); } else { const h = this.hero; if (h.maxmp) h.mp = Math.min(h.maxmp, h.mp + it.power); this.say("Your mind clears."); } return true; }
      if (cmd === "eat") { if (it.kind !== "ration") { this.say("That isn't food."); return false; } this.pack.splice(arg, 1); const n = Math.min(this.max - this.hp, Math.round(this.max * 0.2)); this.hp += n; this.say(`That hit the spot (${n}).`); return true; }
      if (cmd === "read") { if (it.kind !== "gscroll") { this.say("There's nothing to read on that."); return false; } this.pack.splice(arg, 1); this.readScroll(it.sub); return true; }
      if (cmd === "wield") { if (it.kind !== "weapon") { this.say("You can't wield that."); return false; } this.wield = it; this.say(`You wield ${it.name}.`); return true; }
      if (cmd === "wear") { if (!["armor", "shield", "helm"].includes(it.kind)) { this.say("You can't wear that."); return false; } this.wear = it; this.say(`You put on ${it.name}.`); return true; }
      if (cmd === "drop") { this.pack.splice(arg, 1); if (this.wield === it) this.wield = null; if (this.wear === it) this.wear = null; this.put(this.x, this.y, it); this.say(`You drop ${it.name}.`); return true; }
      return false; }
    readScroll(sub) { const R = this.rnd;
      if (sub === "mapping") { for (let y = 0; y < GD.H; y++) for (let x = 0; x < GD.W; x++) if (this.tile(x, y) !== " ") this.seen.add(key(x, y)); this.say("A map forms in your mind."); }
      else if (sub === "teleport") { const r = R.pick(this.rooms.filter((q) => q.room)), [x, y] = this.spot(r); this.x = x; this.y = y; this.say("You feel a wrenching sensation."); }
      else if (sub === "fire") { let n = 0; for (const m of this.mons) if (m.hp > 0 && Math.abs(m.x - this.x) <= 2 && Math.abs(m.y - this.y) <= 2) { const d = R.int(8, 14) + this.L * 2; m.hp -= d; m.asleep = false; m.hidden = false; n++; if (m.hp <= 0) this.fall(m); } this.say(n ? "The scroll bursts into a ball of flame!" : "The scroll flares and burns away, harming nothing."); }
      else if (sub === "enchantWeapon") { const w = this.wield || this.hero.weapon; if (w) { w.power = (w.power || 0) + 1; this.say(`Your ${w.name} glows blue for a moment.`); } else this.say("Your hands twitch."); }
      else if (sub === "enchantArmour") { const a = this.wear || this.hero.armor; if (a) { a.power = (a.power || 0) + 1; if (!this.wear) CM.recompute(this.hero); this.say(`Your ${a.name} glows silver for a moment.`); } else this.say("Your skin itches."); } }
    strike(m) { const g = this.game, R = this.rnd, h = this.hero, { atk, power } = this.heroAtk(); m.asleep = false;
      if (!R.chance(CM.clamp(g.hitChance(h) - m.level * 0.004, 0.35, 0.97))) { this.say(`You miss the ${m.name}.`); return; }
      let dmg = Math.max(1, atk + power + R.int(0, Math.max(1, Math.floor((atk + power) / 2))) - Math.floor(m.df / 2)); const crit = R.chance(g.critChance(h)); if (crit) dmg *= 2;
      m.hp -= dmg; this.say(`You ${crit ? "smite" : "hit"} the ${m.name}${crit ? "!" : "."}`); if (m.hp <= 0) this.fall(m); }
    fall(m) { m.hp = 0; this.kills++; this.xp += m.xp; this.say(m.boss ? "The Unwritten comes apart into loose letters, and they blow away." : `You kill the ${m.name}!`);
      if (!m.boss && this.rnd.chance(0.25)) this.put(m.x, m.y, this.rnd.chance(0.5) ? { kind: "ggold", n: 3 + this.L * 3, name: "gold" } : this.makeThing()); }
    // ---- the monsters' turn ----
    monsTurn() { const R = this.rnd, hd = this.distances(this.x, this.y);
      for (const m of this.mons) { if (m.hp <= 0) continue;
        if (m.ways === "regen" && m.hp < m.max) m.hp = Math.min(m.max, m.hp + 2);
        if (m.asleep) { if (this.visible(m.x, m.y) && Math.max(Math.abs(m.x - this.x), Math.abs(m.y - this.y)) <= 6 && R.chance(0.35)) m.asleep = false; continue; }
        if (m.hidden && Math.max(Math.abs(m.x - this.x), Math.abs(m.y - this.y)) > 1) continue;
        m.energy += m.speed; while (m.energy >= 1 && m.hp > 0 && !this.over) { m.energy -= 1; this.monAct(m, hd); } } }
    monAct(m, hd) { const R = this.rnd, near = Math.max(Math.abs(m.x - this.x), Math.abs(m.y - this.y));
      if (m.boss) { m.cool = Math.max(0, m.cool - 1); if (m.cool === 0 && near <= 8 && this.mons.filter((q) => q.hp > 0 && q.ch === "?").length < 4) { m.cool = GD.bossWrites; let n = 0; for (const [dx, dy] of DIRS8) { if (n >= 1) break; const x = m.x + dx, y = m.y + dy; if (this.open(x, y) && !this.monAt(x, y) && !(x === this.x && y === this.y)) { this.addMon(GD.MINION, x, y, false); n++; } } if (n) this.say("The Unwritten writes, and loose glyphs crawl off its page."); }
        if (!m.blinked && m.hp < m.max / 2) { m.blinked = true; const r = this.roomOf(m.x, m.y); if (r) { const [x, y] = this.spot(r); m.x = x; m.y = y; this.say("The Unwritten smears itself across the room."); return; } } }
      if (near <= 1 && this.canStep(m.x, m.y, this.x - m.x, this.y - m.y)) { this.bite(m); return; }
      if (m.ways === "breath" && m.cool-- <= 0 && near <= 6 && (m.x === this.x || m.y === this.y || Math.abs(m.x - this.x) === Math.abs(m.y - this.y)) && this.visible(m.x, m.y)) { m.cool = 4; const d = Math.max(1, Math.round(m.atk * 0.8) - Math.floor(this.heroDf() / 3)); this.killer = `a ${m.name}'s fire`; this.hurt(d, `The ${m.name} breathes fire! (${d})`); return; }
      const sees = this.visible(m.x, m.y) || near <= 2; if (sees) m.hunting = 12; else if (m.hunting) m.hunting--;
      if (m.ways === "erratic" && R.chance(0.4) || !m.hunting) { const [dx, dy] = R.pick(DIRS8); if (this.canStep(m.x, m.y, dx, dy) && !this.monAt(m.x + dx, m.y + dy) && !(m.x + dx === this.x && m.y + dy === this.y)) { m.x += dx; m.y += dy; } return; }
      let best = null; for (const [dx, dy] of DIRS8) { const nx = m.x + dx, ny = m.y + dy; if (!this.canStep(m.x, m.y, dx, dy) || this.monAt(nx, ny) || (nx === this.x && ny === this.y)) continue; const d = hd.get(key(nx, ny)); if (d !== undefined && (!best || d < best[2])) best = [nx, ny, d]; }
      if (best) { m.x = best[0]; m.y = best[1]; } }
    bite(m) { const R = this.rnd, h = this.hero; if (!R.chance(CM.clamp(0.62 + (m.level - h.level) * 0.03, 0.25, 0.92))) { this.say(`The ${m.name} misses.`); return; }
      const d = Math.max(1, m.atk + R.int(0, Math.max(1, Math.floor(m.atk / 2))) - Math.floor(this.heroDf() / 2)); if (m.ways === "drain") m.hp = Math.min(m.max, m.hp + Math.ceil(d / 2));
      this.killer = m.boss ? "the Unwritten" : `a ${m.name}`; this.hurt(d, `The ${m.name} ${m.boss ? "writes on you" : "hits"}! (${d})`); }
    hurt(d, words) { this.hp -= d; this.say(words); if (this.hp <= 0) { this.hp = 0; this.over = "dead"; this.say("You die..."); } }
  };
}
