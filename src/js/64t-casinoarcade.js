"use strict";
// The Gilded Joker's arcade (the twenty-first big update - v13.1): two games of skill on the floor, played for gold.
//
// Runefall (CM.PG): a board of rune-stones under a wizard's staff. Aim, and the staff looses an orb that falls and
// bounces through the runes, lighting what it strikes; lit runes crumble when the orb is gone. Clear every ember rune
// (orange) before the ten orbs are spent. A mana rune (green) makes the next orb a fireball that burns through; the
// gold rune (purple, a new one each shot) pays a bonus; the Well that slides along the bottom gives a caught orb back.
// Five boards in a run, by the dungeon's bands; the stake is paid once, and each board cleared pays a share of it back
// (more for each), and cards from the second, fourth and fifth. A board lost ends the run, and the ember runes
// already broken earn a little back.
//
// Lantern Lane Dash (CM.CR): a cabinet of the old sort. Hop the hero across lanes - grass with lamp-posts in the way,
// roads of carts, rivers of floating logs, the mine-cart rail with its bell - to the gate at the top. Each level
// cleared climbs the ladder of what the stake would pay; collect, or press on and risk it. Cards at levels 3 and 5.
//
// Both step on a fixed clock from the seed and the house's count, so the same inputs play the same game. The window
// is 76j-casinoarcade.js.
CM.PG = {
  W: 600, H: 720, gravity: 640, orbR: 7, pegR: 9, bounce: 0.72, speed: 520, orbs: 10, step: 1 / 240, launcher: [300, 40],
  BOARDS: [["The Cellar", "#4A4038"], ["The Goblin Warrens", "#3A4A2A"], ["The Drowned Halls", "#203A4A"], ["The Foundry", "#4A2A1A"], ["The Lich's Throne", "#2A1E3A"]],
  PAY: [0.6, 0.8, 1.0, 1.4, 2.4],                                          // (a share of the stake back for each board cleared: 6.2 times it for a whole run)
  CARD: { 2: "common", 4: "common", 5: "rare" }, EMBERS: 0.22, consolation: 0.35, SCORE: { blue: 10, ember: 100, mana: 10, gold: 500 },
};
const PG = CM.PG;
// the boards' runes: a pattern for each band, the embers and the mana runes picked by the seed
PG.layout = (n, rnd) => {
  const pegs = [], W = PG.W, add = (x, y) => { if (x > 24 && x < W - 24 && y > 130 && y < 640 && !pegs.some((p) => Math.hypot(p.x - x, p.y - y) < 24)) pegs.push({ x: Math.round(x), y: Math.round(y), kind: "blue", hit: false, gone: false }); };
  if (n === 1) for (let r = 0; r < 9; r++) for (let c = 0; c < 11; c++) add(52 + c * 50 + (r % 2 ? 25 : 0), 170 + r * 52);
  else if (n === 2) for (let k = 0; k < 4; k++) for (let a = 0; a < 18; a++) { const t = Math.PI * (0.08 + 0.84 * a / 17); add(300 - Math.cos(t) * (120 + k * 60), 220 + Math.sin(t) * (120 + k * 60) * 0.85); }
  else if (n === 3) for (let r = 0; r < 8; r++) for (let c = 0; c < 13; c++) add(40 + c * 44, 180 + r * 58 + Math.sin(c * 0.8 + r) * 22);
  else if (n === 4) { for (const [cx, cy, rr] of [[160, 300, 70], [440, 300, 70], [300, 470, 90], [140, 560, 50], [460, 560, 50]]) for (let a = 0; a < 14; a++) add(cx + Math.cos(a / 14 * Math.PI * 2) * rr, cy + Math.sin(a / 14 * Math.PI * 2) * rr); for (let c = 0; c < 9; c++) add(80 + c * 55, 190); }
  else { for (let a = 0; a < 90; a++) { const t = a * 0.32, rr = 30 + a * 2.6; add(300 + Math.cos(t) * rr, 400 + Math.sin(t) * rr * 0.85); } }
  const order = pegs.map((_, i) => i); for (let i = order.length - 1; i > 0; i--) { const j = rnd.int(0, i); [order[i], order[j]] = [order[j], order[i]]; }
  const embers = Math.max(10, Math.round(pegs.length * PG.EMBERS)); order.slice(0, embers).forEach((i) => { pegs[i].kind = "ember"; }); order.slice(embers, embers + 2).forEach((i) => { pegs[i].kind = "mana"; });
  return pegs;
};
PG.Board = class {
  constructor(n, seed) {
    this.n = n; this.rnd = new CM.Random(seed); this.pegs = PG.layout(n, this.rnd); this.orbs = PG.orbs; this.score = 0; this.ball = null; this.stage = "aim"; this.fire = 0; this.events = [];
    this.well = { x: PG.W / 2, w: 90, dir: 1, speed: 110 }; this.shotHits = 0; this.t = 0; this.pickGold();
  }
  embersLeft() { return this.pegs.filter((p) => p.kind === "ember" && !p.gone).length; }
  embersTotal() { return this.pegs.filter((p) => p.kind === "ember").length; }
  pickGold() { for (const p of this.pegs) if (p.kind === "gold") p.kind = "blue"; const blues = this.pegs.filter((p) => p.kind === "blue" && !p.gone); if (blues.length) blues[this.rnd.int(0, blues.length - 1)].kind = "gold"; }
  // the score's multiplier: up as the embers fall
  mult() { const f = 1 - this.embersLeft() / Math.max(1, this.embersTotal()); return f >= 0.9 ? 5 : f >= 0.7 ? 3 : f >= 0.4 ? 2 : 1; }
  shoot(angle) {
    if (this.stage !== "aim" || this.orbs <= 0) return false; this.orbs -= 1; const [x, y] = PG.launcher;
    this.ball = { x, y, vx: Math.sin(angle) * PG.speed, vy: Math.cos(angle) * PG.speed, still: 0, lastY: y, fire: this.fire > 0 }; if (this.fire > 0) this.fire -= 1;
    this.stage = "flying"; this.shotHits = 0; this.events.push({ kind: "shoot" }); return true;
  }
  // the orb's path as the guide shows it (a quarter of a second, the first bounce)
  guide(angle, seconds = 0.45) { const pts = [], [x0, y0] = PG.launcher; let x = x0, y = y0, vx = Math.sin(angle) * PG.speed, vy = Math.cos(angle) * PG.speed; for (let t = 0; t < seconds; t += 1 / 60) { vy += PG.gravity / 60; x += vx / 60; y += vy / 60; if (x < PG.orbR || x > PG.W - PG.orbR) vx = -vx; pts.push([x, y]); if (this.pegs.some((p) => !p.gone && Math.hypot(p.x - x, p.y - y) < PG.pegR + PG.orbR)) break; } return pts; }
  update(dt) {
    this.t += dt; const wl = this.well; wl.x += wl.dir * wl.speed * dt; if (wl.x < wl.w / 2 + 10 || wl.x > PG.W - wl.w / 2 - 10) { wl.dir *= -1; wl.x = Math.max(wl.w / 2 + 10, Math.min(PG.W - wl.w / 2 - 10, wl.x)); }
    if (this.stage !== "flying") return;
    for (let s = 0; s < dt / PG.step - 1e-9 && this.ball; s++) this.stepBall(PG.step);
  }
  stepBall(dt) {
    const b = this.ball, R = PG.orbR + PG.pegR; b.vy += PG.gravity * dt; b.x += b.vx * dt; b.y += b.vy * dt;
    if (b.x < PG.orbR) { b.x = PG.orbR; b.vx = Math.abs(b.vx) * PG.bounce; this.events.push({ kind: "wall" }); } if (b.x > PG.W - PG.orbR) { b.x = PG.W - PG.orbR; b.vx = -Math.abs(b.vx) * PG.bounce; this.events.push({ kind: "wall" }); }
    if (b.y < PG.orbR) { b.y = PG.orbR; b.vy = Math.abs(b.vy); }
    for (const p of this.pegs) {
      if (p.gone) continue; const dx = b.x - p.x, dy = b.y - p.y, d = Math.hypot(dx, dy); if (d >= R || d === 0) continue;
      if (!p.hit) { p.hit = true; this.shotHits += 1; this.score += PG.SCORE[p.kind] * this.mult(); this.events.push({ kind: "hit", peg: p, n: this.shotHits }); if (p.kind === "mana") { this.fire += 1; this.events.push({ kind: "mana" }); } }
      if (b.fire) continue;                                                // (a fireball burns through)
      const nx = dx / d, ny = dy / d, vn = b.vx * nx + b.vy * ny; b.x = p.x + nx * R; b.y = p.y + ny * R; if (vn < 0) { b.vx -= (1 + PG.bounce) * vn * nx; b.vy -= (1 + PG.bounce) * vn * ny; }
    }
    // stuck on runes: the lit ones nearest crumble early
    if (Math.abs(b.y - b.lastY) < 0.5) b.still += dt; else { b.still = 0; b.lastY = b.y; }
    if (b.still > 2.5) { const lit = this.pegs.filter((p) => p.hit && !p.gone).sort((a, c) => Math.hypot(a.x - b.x, a.y - b.y) - Math.hypot(c.x - b.x, c.y - b.y)); if (lit[0]) lit[0].gone = true; b.still = 0; }
    if (b.y > PG.H - 34 && Math.abs(b.x - this.well.x) < this.well.w / 2 && b.vy > 0) { this.orbs += 1; this.events.push({ kind: "well" }); this.endShot(); return; }
    if (b.y > PG.H + PG.orbR) this.endShot();
  }
  endShot() {
    this.ball = null; let broke = 0; for (const p of this.pegs) if (p.hit && !p.gone) { p.gone = true; broke++; } this.events.push({ kind: "crumble", n: broke });
    if (!this.embersLeft()) { this.stage = "won"; this.score += this.orbs * 1000; this.events.push({ kind: "cleared" }); return; }
    if (this.orbs <= 0) { this.stage = "lost"; this.events.push({ kind: "lost" }); return; }
    this.stage = "aim"; this.pickGold();
  }
};
// ---- Lantern Lane Dash ----
CM.CR = {
  COLS: 9, step: 1 / 60, idle: 12, LADDER: [1.2, 1.7, 2.6, 4.0, 6.5], CARD: { 3: "common", 5: "rare" }, levels: 5,
  rowsFor: (n) => 12 + n * 4,
};
const CR = CM.CR;
CR.Level = class {
  constructor(n, seed) {
    this.n = n; this.rnd = new CM.Random(seed); const R = this.rnd, rows = CR.rowsFor(n); this.rows = [{ kind: "grass", posts: [] }];
    for (let y = 1; y < rows; y++) {
      const roll = R.next(), prev = this.rows[y - 1].kind, kind = prev !== "grass" && R.chance(0.3) ? "grass" : roll < 0.38 ? "road" : roll < 0.66 ? "river" : roll < 0.78 + n * 0.02 ? "rail" : "grass";
      const dir = R.chance(0.5) ? 1 : -1, speed = (kind === "river" ? 1.2 + R.next() * 0.8 : 1.6 + R.next() * 1.4) * (1 + n * 0.12);
      const row = { kind, dir, speed, things: [], posts: [] };
      if (kind === "grass") { for (let c = 0; c < CR.COLS; c++) if (c !== 4 && R.chance(0.22)) row.posts.push(c); }
      if (kind === "road") { let x = R.next() * 3; while (x < CR.COLS + 4) { const len = R.chance(0.3) ? 2 : 1; row.things.push({ x, len }); x += len + 2 + R.next() * 3.5; } }
      if (kind === "river") { let x = R.next() * 2; while (x < CR.COLS + 5) { const len = 2 + R.int(0, 2); row.things.push({ x, len }); x += len + 1.2 + R.next() * 1.6; } }
      if (kind === "rail") { row.train = { x: -30, t: 2 + R.next() * 4, every: 5 + R.next() * 3, len: 6, speed: 18 }; }
      this.rows.push(row);
    }
    this.rows.push({ kind: "gate", posts: [] }); this.hero = { c: 4, y: 0, fx: 4 }; this.stage = "play"; this.t = 0; this.idleT = 0; this.events = []; this.best = 0; this.span = CR.COLS + 6;
  }
  rowAt(y) { return this.rows[y]; }
  hop(dir) {
    if (this.stage !== "play") return false; const h = this.hero, [dx, dy] = { up: [0, 1], down: [0, -1], left: [-1, 0], right: [1, 0] }[dir] || [0, 0];
    const c = Math.round(h.fx) + dx, y = h.y + dy; if (c < 0 || c >= CR.COLS || y < 0 || y >= this.rows.length) return false;
    const R = this.rows[y]; if (R.posts && R.posts.includes(c)) return false;
    h.c = c; h.fx = c; h.y = y; this.events.push({ kind: "hop" }); if (y > this.best) { this.best = y; this.idleT = 0; }
    if (R.kind === "gate") { this.stage = "won"; this.events.push({ kind: "cleared" }); }
    this.check(); return true;
  }
  update(dt) { for (let s = 0; s < dt / CR.step - 1e-9; s++) this.tick(CR.step); }
  tick(dt) {
    if (this.stage !== "play") return; this.t += dt; this.idleT += dt; const span = this.span;
    for (const R of this.rows) {
      if (R.kind === "road" || R.kind === "river") for (const o of R.things) { o.x += R.dir * R.speed * dt; if (R.dir > 0 && o.x > CR.COLS + 2) o.x -= span; if (R.dir < 0 && o.x + o.len < -2) o.x += span; }
      if (R.kind === "rail") { const T = R.train; if (T.x > -20 && T.x < CR.COLS + 2) { T.x += T.speed * dt; if (T.x >= CR.COLS + 2) { T.x = -30; T.t = T.every; } } else { T.t -= dt; if (T.t <= 1.2 && !T.warned) { T.warned = true; this.events.push({ kind: "bell" }); } if (T.t <= 0) { T.x = -T.len - 1; T.warned = false; } } }
    }
    const h = this.hero, R = this.rows[h.y];
    if (R.kind === "river") { const log = R.things.find((o) => h.fx + 0.5 > o.x && h.fx + 0.5 < o.x + o.len); if (log) { h.fx += R.dir * R.speed * dt; if (h.fx < -0.4 || h.fx > CR.COLS - 0.6) return this.die("swept"); } }
    if (this.idleT > CR.idle) return this.die("watch");
    this.check();
  }
  check() {
    const h = this.hero, R = this.rows[h.y], x = h.fx + 0.5; if (this.stage !== "play") return;
    if (R.kind === "road" && R.things.some((o) => x > o.x - 0.15 && x < o.x + o.len + 0.15)) return this.die("cart");
    if (R.kind === "river" && !R.things.some((o) => x > o.x && x < o.x + o.len)) return this.die("water");
    if (R.kind === "rail" && R.train.x > -R.train.len - 1 && x > R.train.x - 0.2 && x < R.train.x + R.train.len + 0.2) return this.die("train");
  }
  die(why) { this.stage = "lost"; this.why = why; this.events.push({ kind: "die", why }); }
};

Object.assign(CM.Game.prototype, {
  // ---- Runefall: a run of five boards for one stake ----
  pgState() { return this.cgStore().pg || null; },
  pgBoard() { const S = this.pgState(); if (!S || S.stage !== "board") return null; if (!this.pgLive || this.pgLive.key !== `${S.seed}:${S.n}`) { this.pgLive = new PG.Board(S.n, CM.hashSeed(`${S.seed}:${S.n}`)); this.pgLive.key = `${S.seed}:${S.n}`; } return this.pgLive; },
  pgStart(bet) {
    const S0 = this.pgState(); if (S0 && S0.stage === "board") return { error: "A board is on the table." };
    const why = this.cgStake("runefall", bet); if (why) return { error: why };
    const F = this.cgStore(); F.n += 1; this.cgStore().pg = { stage: "board", n: 1, bet: Math.floor(bet), won: 0, cards: [], seed: `${this.seed}:runefall:${F.n}` }; this.pgLive = null;
    this.saveCasino && this.saveCasino(); return this.pgState();
  },
  // a board finished (the window calls this when the board says won or lost): the share of the stake, the cards, the next
  pgSettle() {
    const S = this.pgState(), B = this.pgLive; if (!S || !B || (B.stage !== "won" && B.stage !== "lost")) return null;
    let pay = 0, card = null;
    if (B.stage === "won") {
      pay = Math.round(S.bet * PG.PAY[S.n - 1]); const kind = PG.CARD[S.n];
      if (kind) card = this.cgCard(kind === "rare", `Runefall, board ${S.n} cleared!`, new CM.Random(CM.hashSeed(`${S.seed}:card:${S.n}`)));
      if (card) S.cards.push(card); S.last = { n: S.n, won: true, pay, card, score: B.score };
      if (S.n >= PG.BOARDS.length) { S.stage = "done"; S.cleared = true; } else { S.n += 1; this.pgLive = null; }
    } else {
      const broke = B.embersTotal() - B.embersLeft(); pay = Math.round(S.bet * PG.consolation * broke / B.embersTotal()); S.last = { n: S.n, won: false, pay, score: B.score }; S.stage = "done";
    }
    this.cgPay("runefall", pay); S.won += pay; this.saveCasino && this.saveCasino(); this.emit("change"); return S.last;
  },
  // ---- Lantern Lane Dash: press on, or collect ----
  crState() { return this.cgStore().cr || null; },
  crLevel() { const S = this.crState(); if (!S || S.stage !== "run") return null; if (!this.crLive || this.crLive.key !== `${S.seed}:${S.n}`) { this.crLive = new CR.Level(S.n, CM.hashSeed(`${S.seed}:${S.n}`)); this.crLive.key = `${S.seed}:${S.n}`; } return this.crLive; },
  crStart(bet) {
    const S0 = this.crState(); if (S0 && (S0.stage === "run" || S0.stage === "between")) return { error: "A game is in the cabinet." };
    const why = this.cgStake("dash", bet); if (why) return { error: why };
    const F = this.cgStore(); F.n += 1; F.cr = { stage: "run", n: 1, bet: Math.floor(bet), pot: 0, cards: [], seed: `${this.seed}:dash:${F.n}` }; this.crLive = null;
    this.saveCasino && this.saveCasino(); return F.cr;
  },
  // a level ended: cleared - the pot climbs the ladder (and a card at 3 and 5), then collect or press on; lost - the pot is gone
  crSettle() {
    const S = this.crState(), L = this.crLive; if (!S || !L || L.stage === "play") return null;
    if (L.stage === "won") {
      S.pot = Math.round(S.bet * CR.LADDER[S.n - 1]); const kind = CR.CARD[S.n]; let card = null;
      if (kind) { card = this.cgCard(kind === "rare", `Lantern Lane Dash, level ${S.n}!`, new CM.Random(CM.hashSeed(`${S.seed}:card:${S.n}`))); if (card) S.cards.push(card); }
      S.last = { n: S.n, won: true, pot: S.pot, card }; this.crLive = null;
      if (S.n >= CR.levels) { this.cgPay("dash", S.pot); S.paid = S.pot; S.stage = "done"; } else S.stage = "between";
    } else { S.last = { n: S.n, won: false, why: L.why, lost: S.pot }; S.pot = 0; S.paid = 0; S.stage = "done"; this.crLive = null; }
    this.saveCasino && this.saveCasino(); this.emit("change"); return S.last;
  },
  crCollect() { const S = this.crState(); if (!S || S.stage !== "between") return 0; this.cgPay("dash", S.pot); S.paid = S.pot; S.stage = "done"; this.saveCasino && this.saveCasino(); this.emit("change"); return S.pot; },
  crOn() { const S = this.crState(); if (!S || S.stage !== "between") return false; S.n += 1; S.stage = "run"; this.crLive = null; this.saveCasino && this.saveCasino(); return true; },
});
