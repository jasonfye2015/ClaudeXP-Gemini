"use strict";
// The Bard's Stage (v15.7): a rhythm game on the tavern stage. Each level is a tune - its notes falling down four lanes
// to the strike line, to be struck as they cross it (D F J K, or the arrows). Struck on the beat is Perfect, near it
// Good, missed is a Miss; a run of strikes builds a combo that multiplies the score. The crowd's cheer is a bar: misses
// drain it, strikes fill it; play the tune through with any cheer left to clear the level - empty it and the bard is
// booed off (a life). Each level a quicker tempo, more notes, and from the fourth, chords. Three lives. The tune itself
// is made from the level's seed, and plays as it is struck. Window: 76zs-bard.js.
CM.BD = { lanes: 4, perfect: 0.05, good: 0.11, late: 0.16, lives: 3, lead: 1.6 };
{ const BD = CM.BD;
  BD.Level = class {
    constructor(n, seed, keep) {
      const R = this.rnd = new CM.Random(seed); this.n = n; this.events = []; this.stage = "play"; Object.assign(this, keep || { score: 0, lives: BD.lives });
      this.bpm = Math.min(168, 92 + 7 * n); this.beat = 60 / this.bpm; this.len = Math.min(52, 30 + 2 * n); this.key = R.int(0, 6); this.reset();
    }
    reset() {
      const R = new CM.Random(CM.hashSeed(`${this.key}:${this.bpm}:${this.n}`)), notes = [], dens = Math.min(0.85, 0.42 + 0.05 * this.n), half = this.beat / 2; let lane = 1, deg = 0;
      for (let t = 2; t < this.len; t += half) { const onBeat = Math.abs((t - 2) / this.beat - Math.round((t - 2) / this.beat)) < 0.01; if (!(onBeat ? R.chance(Math.min(0.95, dens + 0.25)) : R.chance(dens * 0.55))) continue;
        lane = CM.ARC.clamp(lane + R.int(-1, 1) * (R.chance(0.3) ? 2 : 1), 0, 3); deg = CM.ARC.clamp(deg + R.int(-2, 2), -3, 9); notes.push({ t, lane, deg, hit: null });
        if (this.n >= 4 && onBeat && R.chance(0.12 + 0.02 * this.n)) notes.push({ t, lane: (lane + 2) % 4, deg: deg + 4, hit: null }); }
      this.notes = notes; this.t = -BD.lead; this.cheer = 60; this.combo = 0; this.best = 0; this.counts = { perfect: 0, good: 0, miss: 0 }; this.dead = 0;
    }
    strike(lane) {
      if (this.stage !== "play" || this.dead) return; let best = null, bd = 9; for (const N of this.notes) { if (N.hit || N.lane !== lane) continue; const d = Math.abs(N.t - this.t); if (d < bd) { bd = d; best = N; } if (N.t - this.t > BD.late) break; }
      if (!best || bd > BD.late) { this.events.push({ kind: "empty", lane }); return; }
      if (bd <= BD.good) { const perf = bd <= BD.perfect; best.hit = perf ? "perfect" : "good"; this.counts[best.hit] += 1; this.combo += 1; this.best = Math.max(this.best, this.combo); const pts = (perf ? 300 : 100) * (1 + Math.min(3, Math.floor(this.combo / 10))); this.score += pts; this.cheer = Math.min(100, this.cheer + (perf ? 3 : 1.5)); this.events.push({ kind: "hit", lane, how: best.hit, deg: best.deg, pts }); }
      else { best.hit = "miss"; this.miss(best); }
    }
    miss(N) { this.counts.miss += 1; this.combo = 0; this.cheer -= 7 + this.n * 0.6; this.events.push({ kind: "miss", lane: N.lane }); if (this.cheer <= 0) { this.lives -= 1; this.dead = 1.8; this.events.push({ kind: "boo" }); } }
    update(dt) {
      if (this.stage !== "play") return;
      if (this.dead) { this.dead -= dt; if (this.dead <= 0) { this.dead = 0; if (this.lives <= 0) { this.stage = "over"; this.events.push({ kind: "over" }); } else this.reset(); } return; }
      const was = this.t; this.t += dt; if (Math.floor((was + 1e3) / this.beat) !== Math.floor((this.t + 1e3) / this.beat) && this.t > 0) this.events.push({ kind: "beat", n: Math.floor(this.t / this.beat) });
      for (const N of this.notes) { if (N.hit) continue; if (this.t - N.t > BD.late) { N.hit = "miss"; this.miss(N); if (this.dead) return; } else if (N.t > this.t) break; }
      if (this.t > this.len + 1) { const tot = this.notes.length || 1, acc = (this.counts.perfect + this.counts.good * 0.5) / tot, bonus = Math.round(acc * 2000 * this.n); this.score += bonus; this.stage = "clear"; this.events.push({ kind: "done", acc, bonus }); }
    }
  };
  CM.ARC.add("bard", { name: "The Bard's Stage", Level: BD.Level, marks: [2, 4, 6] });
}
