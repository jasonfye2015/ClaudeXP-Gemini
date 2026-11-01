"use strict";
// The Barrow Crawler (v15.6): a centipede game in an old barrow. A long crawler of segments winds down through a field of
// toadstools, turning down a row and back each time it meets one or the wall; at the bottom it climbs and falls inside
// the gnome's patch. The gnome slides about that patch and fires one wand-spark at a time: a segment hit becomes a
// toadstool and the crawler splits in two, the one behind it gaining a head. Toadstools take three sparks. From the
// second level a spider bounds about the gnome's patch. Clear every segment to clear the level; each level a longer,
// quicker crawler and more toadstools. Three lives. Window: 76zk-crawler.js.
CM.BC = { W: 25, H: 30, zone: 24, lives: 3 };
{ const BC = CM.BC;
  BC.Level = class {
    constructor(n, seed, keep) {
      this.rnd = new CM.Random(seed); this.n = n; this.t = 0; this.events = []; this.stage = "play"; Object.assign(this, keep || { score: 0, lives: BC.lives, extraGiven: false });
      this.mush = new Map(); const R = this.rnd; for (let k = 0; k < 34 + 3 * n; k++) { const x = R.int(0, BC.W - 1), y = R.int(1, BC.H - 4); this.mush.set(`${x},${y}`, 3); }
      this.period = Math.max(0.035, 0.09 - 0.005 * n); this.segs = []; const len = Math.min(16, 9 + n);
      for (let i = 0; i < len; i++) this.segs.push({ x: 12 - i < 0 ? 0 : 12 - i, y: 0, dir: 1, vdir: 1, head: i === 0, fx: 12 - i, fy: 0, id: i });
      this.segs.forEach((s, i) => { s.x = 12 + i; s.fx = s.x; s.dir = -1; }); this.acc = 0; this.ids = len; this.spawn();
    }
    spawn() { this.p = { x: BC.W / 2, y: BC.H - 1.5, dead: 0 }; this.bolt = null; this.spider = null; this.spiderT = 4 + this.rnd.next() * 4; this.move = [0, 0]; }
    input(mx, my) { this.move = [mx, my]; }
    fire() { if (!this.bolt && !this.p.dead) { this.bolt = { x: this.p.x, y: this.p.y - 0.6 }; this.events.push({ kind: "fire" }); } }
    stepSegs() {
      for (const s of this.segs) {
        const nx = s.x + s.dir, blocked = nx < 0 || nx >= BC.W || this.mush.has(`${nx},${s.y}`);
        if (!blocked) { s.x = nx; continue; }
        let ny = s.y + s.vdir; if (ny >= BC.H) { s.vdir = -1; ny = s.y - 1; } else if (s.vdir < 0 && ny < BC.zone) { s.vdir = 1; ny = s.y + 1; }
        s.y = ny; s.dir = -s.dir;
      }
    }
    lose() { if (this.p.dead) return; this.lives -= 1; this.p.dead = 1.6; this.events.push({ kind: "die", x: this.p.x, y: this.p.y }); }
    update(dt) {
      if (this.stage !== "play") return; this.t += dt; const P = this.p;
      if (P.dead) { P.dead -= dt; if (P.dead <= 0) { P.dead = 0; if (this.lives <= 0) { this.stage = "over"; this.events.push({ kind: "over" }); return; } this.spawn(); for (const s of this.segs) if (s.y >= BC.zone - 2) { s.y = 0; s.vdir = 1; } } return; }
      // the gnome
      P.x = CM.ARC.clamp(P.x + this.move[0] * 14 * dt, 0.5, BC.W - 0.5); P.y = CM.ARC.clamp(P.y + this.move[1] * 12 * dt, BC.zone, BC.H - 0.5);
      // the spark
      if (this.bolt) { const B = this.bolt; B.y -= 42 * dt; const cx = Math.floor(B.x), cy = Math.floor(B.y);
        if (B.y < 0) this.bolt = null;
        else if (this.mush.has(`${cx},${cy}`)) { const h = this.mush.get(`${cx},${cy}`) - 1; if (h <= 0) { this.mush.delete(`${cx},${cy}`); this.score += 1; this.events.push({ kind: "pop", x: cx, y: cy }); } else this.mush.set(`${cx},${cy}`, h); this.events.push({ kind: "chip" }); this.bolt = null; }
        else { const i = this.segs.findIndex((s) => Math.abs(s.fx + 0.5 - B.x) < 0.7 && Math.abs(s.fy + 0.5 - B.y) < 0.7);
          if (i >= 0) { const s = this.segs[i], pts = s.head ? 100 : 10; this.score += pts; this.events.push({ kind: "hit", x: s.fx, y: s.fy, pts, head: s.head }); this.mush.set(`${s.x},${s.y}`, 3); const after = this.segs[i + 1]; if (after && !after.head) after.head = true; this.segs.splice(i, 1); this.bolt = null; if (!this.segs.length) { this.stage = "clear"; this.events.push({ kind: "clear" }); return; } }
          else if (this.spider && Math.abs(this.spider.x - B.x) < 0.9 && Math.abs(this.spider.y - B.y) < 0.8) { const d = Math.abs(this.spider.y - P.y), pts = d < 2 ? 900 : d < 4 ? 600 : 300; this.score += pts; this.events.push({ kind: "spider", x: this.spider.x, y: this.spider.y, pts }); this.spider = null; this.bolt = null; } } }
      // the crawler, a cell at a time, slid between
      this.acc += dt; while (this.acc >= this.period) { this.acc -= this.period; this.stepSegs(); }
      for (const s of this.segs) { const k = Math.min(1, dt / this.period * 1.2); s.fx += (s.x - s.fx) * Math.min(1, k * 2.2); s.fy += (s.y - s.fy) * Math.min(1, k * 2.2); if (Math.abs(s.x - s.fx) > 2) s.fx = s.x; }
      // the spider
      if (this.n >= 2) { if (!this.spider && (this.spiderT -= dt) <= 0) { const L = this.rnd.chance(0.5); this.spider = { x: L ? -1 : BC.W + 1, y: BC.zone + 1, vx: (L ? 1 : -1) * (5 + this.n * 0.3), vy: 6, t: 0 }; this.events.push({ kind: "spidercome" }); }
        if (this.spider) { const S = this.spider; S.x += S.vx * dt; S.y += S.vy * dt; S.t += dt; if (S.y > BC.H - 0.5 || S.y < BC.zone - 2) S.vy = -S.vy; if (this.rnd.chance(dt * 1.5)) S.vy = (this.rnd.chance(0.5) ? 1 : -1) * (4 + this.rnd.next() * 5);
          const k = `${Math.floor(S.x)},${Math.floor(S.y)}`; if (this.mush.has(k) && this.rnd.chance(dt * 3)) this.mush.delete(k);
          if (S.x < -2 || S.x > BC.W + 2) { this.spider = null; this.spiderT = 5 + this.rnd.next() * 5; } else if (Math.abs(S.x - P.x) < 0.9 && Math.abs(S.y - P.y) < 0.9) this.lose(); } }
      for (const s of this.segs) if (Math.abs(s.fx + 0.5 - P.x) < 0.9 && Math.abs(s.fy + 0.5 - P.y) < 0.9) { this.lose(); break; }
      if (!this.extraGiven && this.score >= 12000) { this.extraGiven = true; this.lives += 1; this.events.push({ kind: "extra" }); }
    }
  };
  CM.ARC.add("crawler", { name: "The Barrow Crawler", Level: BC.Level, marks: [2, 4, 6] });
}
