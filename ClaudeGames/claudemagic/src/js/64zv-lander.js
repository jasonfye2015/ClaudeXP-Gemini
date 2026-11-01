"use strict";
// The Skyreach Landing (v15.6): a landing game over the floating isles. A sky-skiff falls in from the top, pulled down,
// with a little fuel to spend: Up fires its burner, Left and Right turn it. Land it on one of the lit pads - gently
// (slow down and across) and upright - to clear the level; the narrower pads score more. Touching the rocks, or a pad too
// hard or askew, wrecks it - a life gone, the level tried again. Each level the pull is stronger, the fuel less and a
// wind blows harder from the fourth on. Three lives. Window: 76zm-lander.js.
CM.LD = { W: 60, H: 40, lives: 3, safeV: 2.4, safeH: 1.6, safeA: 0.28 };
{ const LD = CM.LD;
  LD.Level = class {
    constructor(n, seed, keep) {
      const R = this.rnd = new CM.Random(seed); this.n = n; this.t = 0; this.events = []; this.stage = "play"; Object.assign(this, keep || { score: 0, lives: LD.lives });
      this.g = 1.6 + 0.12 * n; this.fuel0 = Math.max(45, 100 - 5 * n); this.wind = n >= 4 ? (R.chance(0.5) ? 1 : -1) * Math.min(1.2, 0.25 * (n - 3)) : 0;
      // the ground: a jagged line with flat pads cut in
      const pts = []; let y = 30; for (let x = 0; x <= LD.W; x += 2) { y = CM.ARC.clamp(y + (R.next() - 0.5) * 6, 20, 37); pts.push([x, y]); }
      this.pads = []; const widths = [[3, 2], [2, 3], [1, 5]]; const used = [];
      for (const [w, m] of widths) { for (let k = 0; k < 50; k++) { const i = R.int(2, pts.length - 2 - w); const x0 = pts[i][0]; if (used.some((u) => Math.abs(u - x0) < 10)) continue; used.push(x0); const py = pts[i][1]; for (let j = i; j <= i + w; j++) pts[j][1] = py; this.pads.push({ x0, x1: x0 + w * 2, y: py, m }); break; } }
      this.ground = pts; this.stars = Array.from({ length: 50 }, () => [R.next() * LD.W, R.next() * 20, R.next()]); this.spawn();
    }
    spawn() { this.s = { x: 8 + this.rnd.next() * 10, y: 3, vx: 3 + this.rnd.next() * 2, vy: 0, a: 0, fuel: this.fuel0, burn: false, dead: 0, landed: 0 }; this.ctl = { turn: 0, burn: false }; }
    input(turn, burn) { this.ctl.turn = turn; this.ctl.burn = !!burn; }
    groundAt(x) { const G = this.ground; const i = CM.ARC.clamp(Math.floor(x / 2), 0, G.length - 2), [x0, y0] = G[i], [x1, y1] = G[i + 1]; return y0 + (y1 - y0) * ((x - x0) / (x1 - x0)); }
    update(dt) {
      if (this.stage !== "play") return; this.t += dt; const S = this.s;
      if (S.dead) { S.dead -= dt; if (S.dead <= 0) { if (this.lives <= 0) { this.stage = "over"; this.events.push({ kind: "over" }); return; } this.spawn(); } return; }
      if (S.landed) { S.landed -= dt; if (S.landed <= 0) { this.stage = "clear"; this.events.push({ kind: "clear" }); } return; }
      S.a += this.ctl.turn * 2.4 * dt; S.a = CM.ARC.clamp(S.a, -1.6, 1.6); S.burn = this.ctl.burn && S.fuel > 0;
      if (S.burn) { S.fuel = Math.max(0, S.fuel - 10 * dt); S.vx += Math.sin(S.a) * 5.2 * dt; S.vy -= Math.cos(S.a) * 5.2 * dt; }
      S.vy += this.g * dt; S.vx += this.wind * dt * 0.6; S.x += S.vx * dt; S.y += S.vy * dt;
      if (S.x < 0) { S.x = 0; S.vx = Math.abs(S.vx) * 0.3; } if (S.x > LD.W) { S.x = LD.W; S.vx = -Math.abs(S.vx) * 0.3; }
      if (S.y < 0) { S.y = 0; S.vy = Math.max(0, S.vy); }
      // the feet touch
      const gy = this.groundAt(S.x); if (S.y + 0.9 >= gy) {
        const pad = this.pads.find((P) => S.x - 0.6 >= P.x0 && S.x + 0.6 <= P.x1), soft = S.vy <= LD.safeV && Math.abs(S.vx) <= LD.safeH && Math.abs(S.a) <= LD.safeA;
        if (pad && soft) { S.y = gy - 0.9; S.landed = 1.4; const pts = Math.round((50 + S.fuel * 2) * pad.m * (1 + (LD.safeV - S.vy) / LD.safeV)); this.score += pts; this.events.push({ kind: "land", x: S.x, y: S.y, pts, m: pad.m }); }
        else { this.lives -= 1; S.dead = 1.8; S.y = gy - 0.9; this.events.push({ kind: "crash", x: S.x, y: S.y, why: pad ? (S.vy > LD.safeV ? "too fast" : Math.abs(S.a) > LD.safeA ? "askew" : "sliding") : "rocks" }); }
      }
    }
  };
  CM.ARC.add("lander", { name: "The Skyreach Landing", Level: LD.Level, marks: [2, 4, 6] });
}
