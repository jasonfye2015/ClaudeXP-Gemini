"use strict";
// Glimmerpop (v15.6): a bubble shooter in an alchemist's still. Coloured glimmer-bubbles hang from the ceiling in offset
// rows; a little launcher at the bottom shoots one at a time (the next one waits beside it), bouncing off the walls; it
// sticks where it touches, and three or more of one colour joined together pop - and anything left hanging by them falls
// for a bonus. Every few shots the ceiling comes down a row. Clear every bubble to clear the level; if they reach the
// line by the launcher, a life is lost and the level starts again. Each level more rows and, from the fourth and the
// seventh, another colour. Three lives. Window: 76zo-glimmerpop.js.
CM.GP = { COLS: 9, ROWS: 14, R: 16, lives: 3, speed: 620 };
{ const GP = CM.GP, W = GP.COLS * GP.R * 2 + GP.R;
  GP.W = W; GP.H = (GP.ROWS + 2) * GP.R * 1.74 + 40; GP.line = GP.ROWS * GP.R * 1.74 + GP.R;
  GP.pos = (r, c, top) => [GP.R + c * GP.R * 2 + (r % 2 ? GP.R : 0), top + GP.R + r * GP.R * 1.74];
  GP.Level = class {
    constructor(n, seed, keep) {
      const R = this.rnd = new CM.Random(seed); this.n = n; this.t = 0; this.events = []; this.stage = "play"; Object.assign(this, keep || { score: 0, lives: GP.lives });
      this.colours = Math.min(7, 4 + (n >= 4 ? 1 : 0) + (n >= 7 ? 1 : 0) + (n >= 10 ? 1 : 0)); this.start = Math.min(9, 4 + Math.floor(n / 2)); this.every = Math.max(4, 9 - Math.floor(n / 2)); this.reset();
    }
    reset() { const R = this.rnd; this.top = 0; this.grid = Array.from({ length: GP.ROWS }, () => Array(GP.COLS).fill(-1)); for (let r = 0; r < this.start; r++) for (let c = 0; c < this.cols(r); c++) this.grid[r][c] = R.int(0, this.colours - 1);
      this.shots = 0; this.ball = null; this.cur = this.pick(); this.next = this.pick(); this.aim = -Math.PI / 2; this.falling = []; this.dead = 0; }
    cols(r) { return r % 2 ? GP.COLS - 1 : GP.COLS; }
    present() { const s = new Set(); for (const row of this.grid) for (const v of row) if (v >= 0) s.add(v); return [...s]; }
    pick() { const pr = this.present(); return pr.length ? this.rnd.pick(pr) : this.rnd.int(0, this.colours - 1); }
    setAim(a) { this.aim = CM.ARC.clamp(a, -Math.PI + 0.12, -0.12); }
    shoot() { if (this.ball || this.dead || this.stage !== "play") return; this.ball = { x: GP.W / 2, y: GP.H - 30, vx: Math.cos(this.aim) * GP.speed, vy: Math.sin(this.aim) * GP.speed, k: this.cur }; this.cur = this.next; this.next = this.pick(); this.events.push({ kind: "shoot" }); }
    nbrs(r, c) { const o = r % 2 ? [[-1, 0], [-1, 1], [0, -1], [0, 1], [1, 0], [1, 1]] : [[-1, -1], [-1, 0], [0, -1], [0, 1], [1, -1], [1, 0]]; return o.map(([dr, dc]) => [r + dr, c + dc]).filter(([a, b]) => a >= 0 && a < GP.ROWS && b >= 0 && b < this.cols(a)); }
    snap(x, y) { let best = null, bd = 1e9; for (let r = 0; r < GP.ROWS; r++) for (let c = 0; c < this.cols(r); c++) { if (this.grid[r][c] >= 0) continue; const [px, py] = GP.pos(r, c, this.top), d = Math.hypot(px - x, py - y); if (d < bd) { bd = d; best = [r, c]; } } return best; }
    land(b) {
      const at = this.snap(b.x, b.y); if (!at) return; const [r, c] = at; this.grid[r][c] = b.k; this.shots += 1;
      // the same colour joined
      const seen = new Set([`${r},${c}`]), q = [[r, c]]; while (q.length) { const [a, d] = q.shift(); for (const [e, f] of this.nbrs(a, d)) if (!seen.has(`${e},${f}`) && this.grid[e][f] === b.k) { seen.add(`${e},${f}`); q.push([e, f]); } }
      let popped = 0, dropped = 0;
      if (seen.size >= 3) { for (const k of seen) { const [a, d] = k.split(",").map(Number), [x, y] = GP.pos(a, d, this.top); this.events.push({ kind: "pop", x, y, k: b.k }); this.grid[a][d] = -1; popped++; }
        // what hangs from nothing falls
        const held = new Set(), q2 = []; for (let cc = 0; cc < this.cols(0); cc++) if (this.grid[0][cc] >= 0) { held.add(`0,${cc}`); q2.push([0, cc]); }
        while (q2.length) { const [a, d] = q2.shift(); for (const [e, f] of this.nbrs(a, d)) if (!held.has(`${e},${f}`) && this.grid[e][f] >= 0) { held.add(`${e},${f}`); q2.push([e, f]); } }
        for (let a = 0; a < GP.ROWS; a++) for (let d = 0; d < this.cols(a); d++) if (this.grid[a][d] >= 0 && !held.has(`${a},${d}`)) { const [x, y] = GP.pos(a, d, this.top); this.falling.push({ x, y, vy: 0, k: this.grid[a][d] }); this.grid[a][d] = -1; dropped++; } }
      if (popped) { const pts = popped * 10 * this.n + (dropped ? 20 * Math.pow(2, Math.min(dropped, 10)) : 0); this.score += pts; this.events.push({ kind: "score", x: b.x, y: b.y, pts, dropped }); } else this.events.push({ kind: "stick" });
      if (!this.present().length) { this.stage = "clear"; this.events.push({ kind: "clear" }); return; }
      if (this.shots % this.every === 0) { this.top += GP.R * 1.74; this.events.push({ kind: "lower" }); }
      if (!this.present().includes(this.cur)) this.cur = this.pick(); if (!this.present().includes(this.next)) this.next = this.pick();
      for (let a = 0; a < GP.ROWS; a++) for (let d = 0; d < this.cols(a); d++) if (this.grid[a][d] >= 0 && GP.pos(a, d, this.top)[1] + GP.R > GP.line) { this.lives -= 1; this.dead = 1.6; this.events.push({ kind: "die" }); return; }
    }
    update(dt) {
      if (this.stage !== "play") return; this.t += dt;
      for (const f of this.falling) { f.vy += 900 * dt; f.y += f.vy * dt; } this.falling = this.falling.filter((f) => f.y < GP.H + 40);
      if (this.dead) { this.dead -= dt; if (this.dead <= 0) { this.dead = 0; if (this.lives <= 0) { this.stage = "over"; this.events.push({ kind: "over" }); } else this.reset(); } return; }
      const b = this.ball; if (!b) return; const steps = Math.ceil(GP.speed * dt / 6);
      for (let s = 0; s < steps && this.ball; s++) { b.x += b.vx * dt / steps; b.y += b.vy * dt / steps;
        if (b.x < GP.R) { b.x = GP.R; b.vx = Math.abs(b.vx); this.events.push({ kind: "wall" }); } if (b.x > GP.W - GP.R) { b.x = GP.W - GP.R; b.vx = -Math.abs(b.vx); this.events.push({ kind: "wall" }); }
        let hit = b.y - GP.R <= this.top; if (!hit) for (let r = 0; r < GP.ROWS && !hit; r++) for (let c = 0; c < this.cols(r); c++) { if (this.grid[r][c] < 0) continue; const [px, py] = GP.pos(r, c, this.top); if (Math.hypot(px - b.x, py - b.y) < GP.R * 1.8) { hit = true; break; } }
        if (hit) { this.ball = null; this.land(b); } }
    }
  };
  CM.ARC.add("glimmerpop", { name: "Glimmerpop", Level: GP.Level, marks: [3, 5, 7] });
}
