"use strict";
// The Wyrm's Feast (v15.6): a snake game in the Joker's garden. A young wyrm slides square by square round a walled bed,
// turning as it is told (never straight back on itself), eating glimmer berries - each makes it a segment longer. Eat
// the level's share and the level is cleared; each level the wyrm is quicker and asks more, and from the third, old
// standing stones dot the bed. A golden berry shows now and then for a while. Running into a wall, a stone or itself
// costs a life, and the level starts over with what was eaten kept. Three lives. Window: 76zj-wyrm.js.
CM.WY = { W: 24, H: 20, lives: 3 };
{ const WY = CM.WY;
  WY.Level = class {
    constructor(n, seed, keep) {
      this.rnd = new CM.Random(seed); this.n = n; this.t = 0; this.events = []; this.stage = "play"; Object.assign(this, keep || { score: 0, lives: WY.lives });
      this.need = 8 + 3 * n; this.eaten = 0; this.tick = Math.max(0.05, 0.15 - 0.012 * n); this.stones = new Set();
      if (n >= 3) for (let k = 0; k < Math.min(22, 4 + 2 * n); k++) { const x = this.rnd.int(2, WY.W - 3), y = this.rnd.int(2, WY.H - 3); if (Math.abs(y - WY.H / 2) > 1 || x > 8) this.stones.add(`${x},${y}`); }
      this.spawn();
    }
    spawn() { const y = Math.floor(WY.H / 2); this.body = [[6, y], [5, y], [4, y], [3, y]]; this.dir = [1, 0]; this.queue = []; this.acc = 0; this.dead = 0; this.berry = this.place(); this.gold = null; this.goldT = 6 + this.rnd.next() * 6; }
    free(x, y) { return x >= 0 && y >= 0 && x < WY.W && y < WY.H && !this.stones.has(`${x},${y}`) && !this.body.some(([a, b]) => a === x && b === y); }
    place() { for (let k = 0; k < 400; k++) { const x = this.rnd.int(1, WY.W - 2), y = this.rnd.int(1, WY.H - 2); if (this.free(x, y) && !(this.berry && this.berry[0] === x && this.berry[1] === y)) return [x, y]; } return [1, 1]; }
    turn(dx, dy) { const last = this.queue.length ? this.queue[this.queue.length - 1] : this.dir; if ((dx === -last[0] && dy === -last[1]) || (dx === last[0] && dy === last[1])) return; if (this.queue.length < 3) this.queue.push([dx, dy]); }
    step() {
      if (this.queue.length) this.dir = this.queue.shift(); const [hx, hy] = this.body[0], nx = hx + this.dir[0], ny = hy + this.dir[1];
      const tail = this.body[this.body.length - 1], eats = this.berry[0] === nx && this.berry[1] === ny, eatsG = this.gold && this.gold.x === nx && this.gold.y === ny;
      const hitSelf = this.body.some(([a, b], i) => a === nx && b === ny && !(i === this.body.length - 1 && !eats && !eatsG));
      if (nx < 0 || ny < 0 || nx >= WY.W || ny >= WY.H || this.stones.has(`${nx},${ny}`) || hitSelf) { this.lives -= 1; this.dead = 1.2; this.events.push({ kind: "die", x: hx, y: hy }); return; }
      this.body.unshift([nx, ny]); if (!eats && !eatsG) this.body.pop(); void tail;
      if (eats) { this.eaten += 1; const pts = 10 * this.n; this.score += pts; this.events.push({ kind: "eat", x: nx, y: ny, pts }); if (this.eaten >= this.need) { this.stage = "clear"; this.events.push({ kind: "clear" }); return; } this.berry = this.place(); }
      if (eatsG) { const pts = 50 * this.n; this.score += pts; this.events.push({ kind: "gold", x: nx, y: ny, pts }); this.gold = null; }
    }
    update(dt) {
      if (this.stage !== "play") return; this.t += dt;
      if (this.dead) { this.dead -= dt; if (this.dead <= 0) { this.dead = 0; if (this.lives <= 0) { this.stage = "over"; this.events.push({ kind: "over" }); } else this.spawn(); } return; }
      if (this.gold) { this.gold.t -= dt; if (this.gold.t <= 0) this.gold = null; } else if ((this.goldT -= dt) <= 0) { const [x, y] = this.place(); this.gold = { x, y, t: 6 }; this.goldT = 10 + this.rnd.next() * 8; this.events.push({ kind: "goldshow" }); }
      this.acc += dt; while (this.acc >= this.tick && this.stage === "play" && !this.dead) { this.acc -= this.tick; this.step(); }
    }
  };
  CM.ARC.add("wyrm", { name: "The Wyrm's Feast", Level: WY.Level, marks: [3, 5, 7] });
}
