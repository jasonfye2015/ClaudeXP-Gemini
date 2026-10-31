"use strict";
// Wyrmhold Pinball (the thirty-seventh big update - v14.7): a pinball table on the Gilded Joker's floor, painted with
// the dungeon. A launch lane on the right (hold to draw the plunger back, let go to fire); a curved top; three rune
// bumpers that kick; two slingshots over the inlanes; a bank of five drop targets (R U N E S) that raise the bonus
// multiplier when all are down; three stars to roll over (all three lit doubles the bumpers for the ball and lights
// the kickback again - the kickback in the left outlane, lit for each new ball, fires a draining ball back up); the Hoard
// Hole, a saucer that holds the ball, pays and kicks it out; and the dragon at the top, who takes hits until slain -
// and then two more balls come down for a multiball, and every second dragon gives an extra ball. A ball lost in its
// first seconds is given back. Three balls. One stake a game: every mark the score passes pays gold, more for each
// mark, every game; and a Claudescryption card the first time ever each mark is passed (common to the fourth, a
// stronger common to the ninth, rare from the tenth). The physics are plain: a ball, segments, circles and two
// flippers, stepped finely. The window: 76zd-pinball.js.
CM.PB = {
  W: 20, H: 36, step: 1 / 600, g: 26, r: 0.42, e: 0.45, maxV: 48, balls: 3, save: 6,
  flip: { len: 3.6, rBase: 0.5, rTip: 0.24, upSpeed: 30, downSpeed: 16 },
  MARKS: [3000, 8000, 15000, 25000, 40000, 60000, 90000, 130000, 180000, 250000, 350000, 500000],
  pay: (i) => 0.1 + 0.06 * i,
  PTS: { bumper: 100, sling: 10, target: 500, bank: 5000, star: 250, stars: 2000, hoard: 5000, dragonHit: 1000, dragon: 25000, lane: 50 },
};
const PB = CM.PB;
// the table, built once: walls (segments), round things (circles), things to roll over (sensors) and the flippers
PB.table = () => {
  const segs = [], circles = [], sensors = [], S = (a, b, o = {}) => segs.push({ a, b, e: PB.e, ...o }), mirror = (p) => [18.9 - p[0], p[1]];
  // the curved top
  const cx = 10, cy = 10, R = 9.5; let prev = [cx - R, cy]; for (let k = 1; k <= 18; k++) { const a = Math.PI + (Math.PI * k) / 18, p = [cx + R * Math.cos(a), cy + R * Math.sin(a)]; S(prev, p); prev = p; }
  S([0.5, 10], [0.5, 36.5]); S([1.8, 26.9], [5.2, 30.48]); S([1.8, 26.9], [1.8, 29.5]);       // the left wall, the outlane beside it, and the inlane's guide to the flipper
  S([19.5, 10], [19.5, 34.6]); S([18.4, 34.6], [18.4, 12.4]); S([18.4, 34.6], [19.5, 34.6], { kind: "plunger" });   // the lane
  S([18.4, 12.4], [19.5, 11.0], { oneWay: [-0.79, -0.62] });                                  // the lane's gate: the ball goes up and out, not back down
  S([18.4, 12.4], [18.4, 34.6]); S([17.1, 26.9], [13.7, 30.48]); S([17.1, 26.9], [17.1, 29.5]); // the right side, its outlane and guide
  S([0.5, 11.2], [2.6, 15.6], { kind: "rubber", e: 0.6 });                                    // the deflector that turns the orbit into the table
  // the slingshots: a kicking face toward the middle, and their backs
  for (const m of [(p) => p, mirror]) { const A = m([2.0, 22.8]), B = m([2.0, 26.0]), C = m([4.3, 27.6]); S(A, C, { kind: "sling", kick: 9 }); S(A, B); S(B, C); }
  // the drop targets, R U N E S, across the left-middle
  for (let k = 0; k < 5; k++) S([1.7 + k * 0.95, 18.6], [2.45 + k * 0.95, 18.6], { kind: "target", id: k });
  circles.push({ x: 9.45, y: 6.6, r: 1.45, kind: "dragon", kick: 7 });
  for (const [x, y] of [[6.1, 11.4], [12.8, 11.4], [9.45, 14.9]]) circles.push({ x, y, r: 1.0, kind: "bumper", kick: 14 });
  circles.push({ x: 1.8, y: 26.65, r: 0.3, kind: "post" }, { x: 17.1, y: 26.65, r: 0.3, kind: "post" });
  sensors.push({ x: 15.6, y: 18.6, r: 0.62, kind: "hoard" }, { x: 1.15, y: 31.5, r: 0.7, kind: "kickback" });
  for (const [x, y] of [[3.4, 13.4], [15.5, 13.4], [9.45, 21.5]]) sensors.push({ x, y, r: 0.55, kind: "star", id: sensors.filter((s) => s.kind === "star").length });
  for (const s of segs) { const dx = s.b[0] - s.a[0], dy = s.b[1] - s.a[1], L = Math.hypot(dx, dy); s.len = L; s.d = [dx / L, dy / L]; }
  const flippers = [{ side: "left", px: 5.6, py: 31.0, rest: 0.52, up: -0.44 }, { side: "right", px: 13.3, py: 31.0, rest: Math.PI - 0.52, up: Math.PI + 0.44 }];
  return { segs, circles, sensors, flippers };
};
PB.Game = class {
  constructor(seed) {
    this.rnd = new CM.Random(seed); this.T = PB.table(); this.t = 0; this.events = []; this.stage = "play"; this.score = 0; this.ballNo = 1; this.extra = 0; this.mult = 1;
    this.targets = [true, true, true, true, true]; this.stars = [false, false, false]; this.dragon = { hp: 4, level: 1, slain: 0 }; this.marks = 0; this.bumperX = 1;
    this.flips = this.T.flippers.map((f) => ({ ...f, a: f.rest, w: 0, held: false })); this.balls = []; this.pull = 0; this.pulling = false; this.serve();
  }
  serve(again) { this.balls = [{ x: 18.95, y: 34.6 - PB.r - 0.01, vx: 0, vy: 0, inLane: true, hold: 0 }]; this.saveT = 0; this.saveUsed = !!again; this.kickback = true; this.ballBonus = 0; this.stars = [false, false, false]; this.bumperX = 1; }
  input(left, right, plunger) { this.flips[0].held = !!left; this.flips[1].held = !!right; if (plunger) { this.pulling = true; } else if (this.pulling) { this.pulling = false; this.launch(); } }
  launch() { const b = this.balls.find((q) => q.inLane && Math.abs(q.vy) < 0.5 && q.y > 32); if (b) { b.vy = -(16 + 30 * this.pull); this.saveT = this.saveUsed ? 0 : PB.save; this.events.push({ kind: "launch", pull: this.pull }); } this.pull = 0; }
  // a flipper's segment and its thickness at a point along it
  flipSeg(f) { const L = PB.flip.len; return { a: [f.px, f.py], b: [f.px + Math.cos(f.a) * L, f.py + Math.sin(f.a) * L] }; }
  collideSeg(b, a, c, rad, e, surf) {
    const dx = c[0] - a[0], dy = c[1] - a[1], L2 = dx * dx + dy * dy, t = Math.max(0, Math.min(1, ((b.x - a[0]) * dx + (b.y - a[1]) * dy) / L2)), px = a[0] + dx * t, py = a[1] + dy * t;
    let nx = b.x - px, ny = b.y - py; const d = Math.hypot(nx, ny), R = PB.r + (typeof rad === "function" ? rad(t) : rad); if (d >= R || d < 1e-9) return null; nx /= d; ny /= d;
    b.x += nx * (R - d); b.y += ny * (R - d); const [sx, sy] = surf ? surf(px, py) : [0, 0], rvx = b.vx - sx, rvy = b.vy - sy, vn = rvx * nx + rvy * ny;
    if (vn < 0) { b.vx = sx + rvx - (1 + e) * vn * nx; b.vy = sy + rvy - (1 + e) * vn * ny; } return { nx, ny, vn, t };
  }
  stepBall(b, dt) {
    if (b.hold > 0) { b.hold -= dt; if (b.hold <= 0) { b.vx = -9 + this.rnd.next() * 3; b.vy = 5 + this.rnd.next() * 2; b.y += 0.9; this.events.push({ kind: "kickout" }); } return; }
    b.vy += PB.g * dt; const sp = Math.hypot(b.vx, b.vy); if (sp > PB.maxV) { b.vx *= PB.maxV / sp; b.vy *= PB.maxV / sp; } b.x += b.vx * dt; b.y += b.vy * dt;
    if (b.inLane && b.y < 12) b.inLane = false; if (!b.inLane && b.x > 18.4 && b.y > 12.5) b.inLane = true;
    for (const s of this.T.segs) {
      if (s.kind === "target" && !this.targets[s.id]) continue; if (s.kind === "plunger" && this.pulling && b.inLane) { /* the plunger drawn back: the ball rests lower */ }
      if (s.oneWay && b.vx * s.oneWay[0] + b.vy * s.oneWay[1] > 0) continue;
      const h = this.collideSeg(b, s.a, s.b, 0, s.e); if (!h) continue;
      if (s.kind === "sling" && h.vn < -3) { b.vx += h.nx * s.kick; b.vy += h.ny * s.kick; this.add(PB.PTS.sling); this.events.push({ kind: "sling", x: s.a[0] }); }
      else if (s.kind === "target" && h.vn < -2) { this.targets[s.id] = false; this.add(PB.PTS.target); this.events.push({ kind: "target", id: s.id }); if (this.targets.every((x) => !x)) { this.add(PB.PTS.bank * this.mult); this.mult = Math.min(6, this.mult + 1); this.targets = [true, true, true, true, true]; this.events.push({ kind: "bank", mult: this.mult }); } }
      else if (h.vn < -6) this.events.push({ kind: "wall", v: -h.vn });
    }
    for (const c of this.T.circles) {
      let nx = b.x - c.x, ny = b.y - c.y; const d = Math.hypot(nx, ny), R = PB.r + c.r; if (d >= R || d < 1e-9) continue; nx /= d; ny /= d; b.x = c.x + nx * R; b.y = c.y + ny * R; const vn = b.vx * nx + b.vy * ny;
      if (vn < 0) { b.vx -= (1 + PB.e) * vn * nx; b.vy -= (1 + PB.e) * vn * ny; }
      if (c.kick && vn < -1) { const out = b.vx * nx + b.vy * ny; if (out < c.kick) { b.vx += nx * (c.kick - out); b.vy += ny * (c.kick - out); } }
      if (c.kind === "bumper" && vn < -1) { this.add(PB.PTS.bumper * this.bumperX); this.ballBonus += 10; this.events.push({ kind: "bumper", x: c.x, y: c.y }); }
      else if (c.kind === "dragon" && vn < -2) this.hitDragon();
    }
    // the flippers: thick at the pivot, thin at the tip, moving
    for (const f of this.flips) { const { a, b: tip } = this.flipSeg(f), w = f.w; this.collideSeg(b, a, tip, (t) => PB.flip.rBase + (PB.flip.rTip - PB.flip.rBase) * t, 0.3, (px, py) => [-w * (py - f.py), w * (px - f.px)]); }
    for (const s of this.T.sensors) { const d = Math.hypot(b.x - s.x, b.y - s.y); if (d > s.r) { if (s.kind === "star") b["in" + s.id] = false; continue; }
      if (s.kind === "kickback" && this.kickback && b.vy > 0) { this.kickback = false; b.vy = -30; b.vx = 0.6; this.events.push({ kind: "kickback" }); }
      if (s.kind === "hoard" && !b.hold && Math.hypot(b.vx, b.vy) < 30) { b.x = s.x; b.y = s.y; b.vx = b.vy = 0; b.hold = 1.0; this.add(PB.PTS.hoard); this.events.push({ kind: "hoard" }); }
      if (s.kind === "star" && !b["in" + s.id]) { b["in" + s.id] = true; this.add(PB.PTS.star); if (!this.stars[s.id]) { this.stars[s.id] = true; this.events.push({ kind: "star", id: s.id }); if (this.stars.every(Boolean)) { this.add(PB.PTS.stars); this.bumperX = 2; this.kickback = true; this.events.push({ kind: "stars" }); } } } }
  }
  hitDragon() {
    const D = this.dragon; D.hp -= 1; this.add(PB.PTS.dragonHit); this.events.push({ kind: "dragonhit", hp: D.hp });
    if (D.hp <= 0) { D.slain += 1; this.add(PB.PTS.dragon * D.level); this.ballBonus += 2000 * D.level; this.events.push({ kind: "dragon", level: D.level }); D.level += 1; D.hp = 3 + D.level; if (D.slain % 2 === 0) { this.extra += 1; this.events.push({ kind: "extraball" }); }
      for (let k = 0; k < 2; k++) this.balls.push({ x: 9.45 + (k ? 3 : -3), y: 2.5, vx: (k ? 4 : -4) + this.rnd.next(), vy: 2, inLane: false, hold: 0 }); this.events.push({ kind: "multiball" }); }
  }
  add(n) { this.score += n; while (this.marks < PB.MARKS.length && this.score >= PB.MARKS[this.marks]) { this.marks += 1; this.events.push({ kind: "mark", i: this.marks }); } }
  tick(dt) {
    if (this.stage !== "play") return; this.t += dt; if (this.saveT > 0) this.saveT -= dt;
    if (this.pulling) this.pull = Math.min(1, this.pull + dt / 1.1);
    for (const f of this.flips) { const target = f.held ? f.up : f.rest, sp = (f.held ? PB.flip.upSpeed : PB.flip.downSpeed) * dt, d = target - f.a, m = Math.max(-sp, Math.min(sp, d)); if (f.held && !f.was) this.events.push({ kind: "flip", side: f.side }); f.was = f.held; f.a += m; f.w = m / dt; }
    for (const b of this.balls) this.stepBall(b, dt);
    const lost = this.balls.filter((b) => b.y > PB.H + 1); if (!lost.length) return; this.lastLostX = lost[0].x;
    this.balls = this.balls.filter((b) => b.y <= PB.H + 1);
    if (this.balls.length) return;  // a ball of a multiball gone; play on
    if (this.saveT > 0) { const keep = this.ballBonus; this.serve(true); this.ballBonus = keep; this.events.push({ kind: "saved" }); return; }
    const bonus = this.ballBonus * this.mult; this.add(bonus); this.events.push({ kind: "drain", bonus, mult: this.mult });
    if (this.extra > 0) { this.extra -= 1; this.events.push({ kind: "shootagain" }); this.serve(); return; }
    if (this.ballNo >= PB.balls) { this.stage = "over"; this.events.push({ kind: "over" }); return; }
    this.ballNo += 1; this.mult = 1; this.serve();
  }
  update(dt) { for (let s = 0; s < dt / PB.step - 1e-9; s++) this.tick(PB.step); }
};
Object.assign(CM.Game.prototype, {
  pbState() { return this.cgStore().pb || null; },
  pbClaimed() { const F = this.cgStore(); F.pbCards = F.pbCards || {}; return F.pbCards; },
  pbGame() { const S = this.pbState(); if (!S || S.stage !== "play") return null; if (!this.pbLive || this.pbLive.key !== S.seed) { S.stage = "done"; S.last = S.last || { score: 0, won: S.won, cards: S.cards || [], lost: true }; this.saveCasino && this.saveCasino(); return null; } return this.pbLive; },
  pbStart(bet) {
    if (this.pbGame()) return { error: "A game is on." };
    const why = this.cgStake("pinball", bet); if (why) return { error: why };
    const F = this.cgStore(); F.n += 1; F.pb = { stage: "play", bet: Math.floor(bet), seed: `${this.seed}:pinball:${F.n}`, won: 0, paid: 0, cards: [] };
    this.pbLive = new PB.Game(CM.hashSeed(F.pb.seed)); this.pbLive.key = F.pb.seed; this.saveCasino && this.saveCasino(); return F.pb;
  },
  // each mark passed: its gold (every game), its card (the first time ever); the game's end
  pbCheck() {
    const S = this.pbState(), G = this.pbLive; if (!S || !G || S.stage !== "play") return null; const out = { marks: [] };
    while ((S.paid || 0) < G.marks) { const i = (S.paid || 0) + 1, pay = Math.round(S.bet * PB.pay(i)), C = this.pbClaimed(); let card = null;
      if (!C[i]) { card = this.cgTierCard(CM.cardTierFor(i), `Wyrmhold Pinball: ${PB.MARKS[i - 1].toLocaleString("en")} points!`, new CM.Random(CM.hashSeed(`${this.seed}:pinball:card:${i}`))); C[i] = card || true; if (card) S.cards.push(card); }
      this.cgPay("pinball", pay); S.won += pay; S.paid = i; out.marks.push({ i, pay, card }); }
    if (G.stage === "over") { S.stage = "done"; S.last = { score: G.score, won: S.won, cards: S.cards.slice(), marks: G.marks }; const F = this.cgStore(); F.pbBest = Math.max(F.pbBest || 0, G.score); this.pbLive = null; out.over = true; }
    if (out.marks.length || out.over) { this.saveCasino && this.saveCasino(); this.emit("change"); }
    return out.marks.length || out.over ? out : null;
  },
});
