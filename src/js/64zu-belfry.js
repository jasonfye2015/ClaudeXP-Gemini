"use strict";
// The Belfry Climb (v15.6): a climbing game up the Joker's bell tower. A troll squats at the top and sends kegs rolling
// down six sloping beams, each falling from the open end to the beam below, now and then dropping down a ladder; at the
// bottom they roll into the brazier. The climber walks, climbs the ladders and jumps (Space) - a keg jumped is 100 -
// and rings the bell at the top to clear the level, with what is left of the bonus. Each level the kegs come quicker
// and faster, and from the third level a will-o'-wisp drifts out of the brazier now and then and wanders the beams. A
// keg or a wisp costs a life. Three lives. Window: 76zl-belfry.js.
CM.BF = { W: 28, H: 32, lives: 3, jump: 0.55, jumpH: 1.7 };
{ const BF = CM.BF;
  // the beams, top to bottom: y at the left end, slope, the range walkable, which way kegs roll
  BF.BEAMS = [{ y0: 6, s: 0, x0: 2, x1: 15, dir: 1 }, { y0: 10, s: 0.06, x0: 1, x1: 25, dir: 1 }, { y0: 16.6, s: -0.06, x0: 3, x1: 27, dir: -1 }, { y0: 20, s: 0.06, x0: 1, x1: 25, dir: 1 }, { y0: 26.6, s: -0.06, x0: 3, x1: 27, dir: -1 }, { y0: 30, s: 0, x0: 0, x1: 28, dir: -1 }];
  BF.yAt = (i, x) => BF.BEAMS[i].y0 + BF.BEAMS[i].s * x;
  // ladders: [x, upper beam, lower beam]
  BF.LADDERS = [[10, 0, 1], [4, 1, 2], [15, 1, 2], [12, 2, 3], [21, 2, 3], [6, 3, 4], [17, 3, 4], [23, 4, 5], [11, 4, 5]];
  BF.Level = class {
    constructor(n, seed, keep) {
      this.rnd = new CM.Random(seed); this.n = n; this.t = 0; this.events = []; this.stage = "play"; Object.assign(this, keep || { score: 0, lives: BF.lives, extraGiven: false });
      this.mul = 1 + Math.min(0.7, (n - 1) * 0.08); this.spawn();
    }
    spawn() { this.p = { x: 5, beam: 5, y: BF.yAt(5, 5), lad: null, jumpT: 0, h: 0, face: 1, dead: 0, walk: 0 }; this.kegs = []; this.wisps = []; this.kegT = 1; this.bonus = 5000; this.ctl = { x: 0, y: 0 }; }
    input(x, y) { this.ctl.x = x; this.ctl.y = y; }
    jump() { const P = this.p; if (!P.lad && !P.jumpT && !P.dead) { P.jumpT = BF.jump; P.jumped = new Set(); this.events.push({ kind: "jump" }); } }
    ladderAt(x, beam, up) { return BF.LADDERS.find(([lx, a, b]) => Math.abs(lx - x) < 0.45 && (up ? b === beam : a === beam)); }
    lose(why) { const P = this.p; if (P.dead) return; this.lives -= 1; P.dead = 1.8; this.events.push({ kind: "die", why, x: P.x, y: P.y }); }
    update(dt) {
      if (this.stage !== "play") return; this.t += dt; const P = this.p;
      if (P.dead) { P.dead -= dt; if (P.dead <= 0) { P.dead = 0; if (this.lives <= 0) { this.stage = "over"; this.events.push({ kind: "over" }); return; } this.spawn(); } return; }
      this.bonus = Math.max(0, this.bonus - dt * 50);
      // the climber
      if (P.lad) { const [lx, a, b] = P.lad, top = BF.yAt(a, lx), bot = BF.yAt(b, lx); P.y += this.ctl.y * 4.5 * dt; P.walk += Math.abs(this.ctl.y) * dt;
        if (P.y <= top) { P.y = top; P.beam = a; P.lad = null; if (a === 0) { this.stage = "clear"; const b2 = Math.round(this.bonus / 100) * 100; this.score += b2; this.events.push({ kind: "bell", bonus: b2 }); return; } } else if (P.y >= bot) { P.y = bot; P.beam = b; P.lad = null; } }
      else {
        if (!P.jumpT && this.ctl.y) { const L2 = this.ladderAt(P.x, P.beam, this.ctl.y < 0); if (L2) { P.lad = L2; P.x = L2[0]; } }
        if (!P.lad) { const Bm = BF.BEAMS[P.beam]; if (this.ctl.x) P.face = this.ctl.x; P.x = CM.ARC.clamp(P.x + this.ctl.x * 5.5 * dt, Bm.x0 + 0.4, Bm.x1 - 0.4); P.walk += Math.abs(this.ctl.x) * dt; P.y = BF.yAt(P.beam, P.x);
          if (P.jumpT) { P.jumpT = Math.max(0, P.jumpT - dt); P.h = Math.sin((1 - P.jumpT / BF.jump) * Math.PI) * BF.jumpH; } else P.h = 0; }
      }
      // kegs: thrown, rolled, dropped, sometimes down a ladder
      if ((this.kegT -= dt) <= 0) { this.kegT = Math.max(1.1, 3 - 0.18 * this.n) * (0.7 + this.rnd.next() * 0.6); this.kegs.push({ x: 4, beam: 1, y: BF.yAt(1, 4), fall: 0, lad: null, rot: 0, id: this.t }); this.events.push({ kind: "throw" }); }
      const sp = 5.5 * this.mul;
      for (const k of this.kegs) {
        if (k.fall) { k.y += 14 * dt; const Bt = BF.yAt(k.fall, k.x); if (k.y >= Bt) { k.y = Bt; k.beam = k.fall; k.fall = 0; this.events.push({ kind: "thud" }); } continue; }
        if (k.lad) { k.y += sp * 0.8 * dt; const bot = BF.yAt(k.lad[2], k.lad[0]); if (k.y >= bot) { k.y = bot; k.beam = k.lad[2]; k.lad = null; } continue; }
        const Bm = BF.BEAMS[k.beam]; k.x += Bm.dir * sp * dt; k.rot += Bm.dir * sp * dt * 2; k.y = BF.yAt(k.beam, k.x);
        const L2 = this.ladderAt(k.x, k.beam, false); if (L2 && k.lastLad !== L2 && k.beam < 5) { k.lastLad = L2; if (this.rnd.chance(0.25 + 0.02 * this.n)) { k.lad = L2; k.x = L2[0]; continue; } }
        if (k.beam === 5 && k.x < 1.2) { k.gone = true; if (this.n >= 3 && this.wisps.length < Math.min(3, this.n - 2) && this.rnd.chance(0.35)) { this.wisps.push({ x: 1.5, beam: 5, y: BF.yAt(5, 1.5), dir: 1, t: 0 }); this.events.push({ kind: "wisp" }); } continue; }
        if (k.x > Bm.x1 || k.x < Bm.x0) { k.fall = k.beam + 1; }
      }
      this.kegs = this.kegs.filter((k) => !k.gone);
      // the wisps: wander along their beam, and up or down ladders now and then
      for (const w of this.wisps) { w.t += dt; if (w.lad) { w.y += w.vy * 2.5 * dt; const [lx, a, b] = w.lad, top = BF.yAt(a, lx), bot = BF.yAt(b, lx); if (w.y <= top) { w.y = top; w.beam = a; w.lad = null; } else if (w.y >= bot) { w.y = bot; w.beam = b; w.lad = null; } continue; }
        const Bm = BF.BEAMS[w.beam]; w.x += w.dir * 2.4 * this.mul * dt; if (w.x > Bm.x1 - 0.5 || w.x < Bm.x0 + 0.5) w.dir = -w.dir; w.y = BF.yAt(w.beam, w.x);
        const up = this.ladderAt(w.x, w.beam, true); if (up && w.beam > 1 && this.rnd.chance(dt * 1.2)) { w.lad = up; w.x = up[0]; w.vy = -1; } }
      // touching
      if (!P.dead) {
        for (const k of this.kegs) { if (k.fall) continue; const dx = Math.abs(k.x - P.x), dy = Math.abs(k.y - (P.y - P.h)); if (dx < 0.8 && dy < 0.9) { this.lose("keg"); break; }
          if (P.jumpT && P.jumped && !P.jumped.has(k.id) && dx < 0.8 && Math.abs(k.y - P.y) < 0.6 && P.h >= 0.9) { P.jumped.add(k.id); this.score += 100; this.events.push({ kind: "leap", x: P.x, y: P.y, pts: 100 }); } }
        for (const w of this.wisps) if (Math.abs(w.x - P.x) < 0.8 && Math.abs(w.y - (P.y - P.h)) < 0.9) { this.lose("wisp"); break; }
      }
      if (!this.extraGiven && this.score >= 10000) { this.extraGiven = true; this.lives += 1; this.events.push({ kind: "extra" }); }
    }
  };
  CM.ARC.add("belfry", { name: "The Belfry Climb", Level: BF.Level, marks: [2, 3, 5] });
}
