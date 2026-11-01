"use strict";
// Four more arcade cabinets on the common works (v15.9), and a free puzzle:
// - Gryphon Joust (CM.GJ): a rider on a gryphon over a lava pit - flap (Space) and steer; meeting a rival knight, the
//   higher lance wins; a fallen knight leaves an egg to catch before it hatches. A wave cleared clears the level.
// - The Courier's Round (CM.CO): a courier rides up the market street throwing scrolls into the letter-boxes of the lit
//   houses; dogs, carts and puddles to dodge; deliver enough of the round to clear the street.
// - The Undercroft Sprint (CM.US): an endless run down the old tunnels - jump the pits and spikes, slide under the beams,
//   duck the bats, gather the coins; each stretch reached clears a level, and the run grows quicker.
// - The Rune Bastion (CM.RBT): tower defence - goblins march the winding road toward the gate; set fire, frost and
//   arcane runes beside it with the mana their deaths bring; each wave held clears a level. Leaks cost the gate's hearts.
// - The Vault Runes (CM.VR): a rune-lock - a grid of runes where touching one turns it and its neighbours; light them all
//   to open the vault. Free; each vault opened the first time pays gold and, every third, a card; tickets each time.
// The windows are 76zzb-joust.js, 76zzc-courier.js, 76zzd-sprint.js, 76zze-bastion.js and 76zzf-vault.js.
{ const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  // ---- Gryphon Joust ----
  const GJ = CM.GJ = { W: 480, H: 380, lava: 340, lives: 3, PLAT: [[0, 270, 110], [370, 270, 110], [150, 200, 180], [20, 120, 120], [340, 120, 120], [180, 60, 120]] };
  GJ.Level = class {
    constructor(n, seed, keep) { this.rnd = new CM.Random(seed); this.n = n; this.t = 0; this.events = []; this.stage = "play"; Object.assign(this, keep || { score: 0, lives: GJ.lives, extraGiven: false }); this.foes = []; this.eggs = []; this.spawnQ = Math.min(8, 2 + n); this.spawnT = 1; this.spawn(); }
    spawn() { this.p = { x: GJ.W / 2, y: GJ.PLAT[2][1] - 14, vx: 0, vy: 0, face: 1, dead: 0, guard: 1.5, flapT: 0 }; this.ctl = 0; }
    input(mx) { this.ctl = mx; }
    flap() { const P = this.p; if (P.dead) return; P.vy = Math.max(-260, P.vy - 190); P.flapT = 0.2; this.events.push({ kind: "flap" }); }
    rider(o, dt, ax) { o.vx = clamp(o.vx + ax * 420 * dt, -170, 170); o.vx *= 1 - 0.6 * dt; o.vy += 360 * dt; o.x += o.vx * dt; o.y += o.vy * dt; if (o.x < -10) o.x += GJ.W + 20; if (o.x > GJ.W + 10) o.x -= GJ.W + 20; if (o.y < 10) { o.y = 10; o.vy = Math.abs(o.vy) * 0.5; }
      for (const [px, py, pw] of GJ.PLAT) if (o.vy > 0 && o.x > px - 6 && o.x < px + pw + 6 && o.y + 14 >= py && o.y + 14 - o.vy * dt <= py + 2) { o.y = py - 14; o.vy = 0; o.vx *= 1 - 4 * dt; } if (ax) o.face = Math.sign(ax); }
    update(dt) {
      if (this.stage !== "play") return; this.t += dt; const P = this.p;
      if (P.dead) { P.dead -= dt; if (P.dead <= 0) { P.dead = 0; if (this.lives <= 0) { this.stage = "over"; this.events.push({ kind: "over" }); return; } this.spawn(); } }
      else { this.rider(P, dt, this.ctl); P.flapT -= dt; if (P.guard > 0) P.guard -= dt; if (P.y > GJ.lava) this.lose(); }
      if (this.spawnQ > 0 && (this.spawnT -= dt) <= 0) { this.spawnT = 1.6; this.spawnQ--; const [px, py, pw] = this.rnd.pick(GJ.PLAT.slice(0, 5)); this.foes.push({ x: px + pw / 2, y: py - 14, vx: 0, vy: -100, face: this.rnd.chance(0.5) ? 1 : -1, ai: 0, kind: this.n >= 4 && this.rnd.chance(0.3) ? "shadow" : this.n >= 2 && this.rnd.chance(0.4) ? "hunter" : "bounder" }); this.events.push({ kind: "arrive" }); }
      for (const F of this.foes) { F.ai -= dt; const sp = { bounder: 0.6, hunter: 0.85, shadow: 1.1 }[F.kind] * (1 + 0.05 * this.n); if (F.ai <= 0) { F.ai = 0.25 + this.rnd.next() * 0.35; const wantY = P.dead ? 150 : P.y - 30 * sp; if (F.y > wantY || F.y > GJ.lava - 60) { F.vy = Math.max(-240, F.vy - 170 * sp); this.events.push({ kind: "foeflap" }); } F.dir = P.dead ? F.face : Math.sign(((P.x - F.x + GJ.W * 1.5) % GJ.W) - GJ.W / 2) || 1; } this.rider(F, dt, F.dir * sp); if (F.y > GJ.lava) F.gone = true; }
      // the meeting of lances
      if (!P.dead && P.guard <= 0) for (const F of this.foes) { if (F.gone || Math.abs(F.x - P.x) > 22 || Math.abs(F.y - P.y) > 20) continue;
        if (P.y < F.y - 4) { F.gone = true; const pts = { bounder: 500, hunter: 750, shadow: 1500 }[F.kind]; this.score += pts; this.eggs.push({ x: F.x, y: F.y, vy: -60, t: 6, kind: F.kind }); this.events.push({ kind: "unhorse", x: F.x, y: F.y, pts }); P.vy = -120; }
        else if (F.y < P.y - 4) { this.lose(); break; } else { const d = Math.sign(P.x - F.x) || 1; P.vx = d * 160; F.vx = -d * 160; this.events.push({ kind: "clash" }); } }
      this.foes = this.foes.filter((F) => !F.gone);
      for (const E of this.eggs) { E.vy += 360 * dt; E.y += E.vy * dt; for (const [px, py, pw] of GJ.PLAT) if (E.vy > 0 && E.x > px && E.x < px + pw && E.y + 6 >= py && E.y - E.vy * dt + 6 <= py + 2) { E.y = py - 6; E.vy = 0; } if (E.y > GJ.lava) E.gone = true; E.t -= dt;
        if (!P.dead && E.t < 5.6 && Math.abs(E.x - P.x) < 18 && Math.abs(E.y - P.y) < 22) { E.gone = true; this.score += 250; this.events.push({ kind: "egg", x: E.x, y: E.y, pts: 250 }); }
        else if (E.t <= 0) { E.gone = true; this.foes.push({ x: E.x, y: E.y - 8, vx: 0, vy: -140, face: 1, ai: 0, kind: E.kind === "bounder" ? "hunter" : "shadow" }); this.events.push({ kind: "hatch" }); } }
      this.eggs = this.eggs.filter((E) => !E.gone);
      if (!this.extraGiven && this.score >= 15000) { this.extraGiven = true; this.lives += 1; this.events.push({ kind: "extra" }); }
      if (!this.spawnQ && !this.foes.length && !this.eggs.length && !P.dead) { this.stage = "clear"; this.events.push({ kind: "clear" }); }
    }
    lose() { const P = this.p; if (P.dead) return; this.lives -= 1; P.dead = 1.8; this.events.push({ kind: "die", x: P.x, y: P.y }); }
  };
  CM.ARC.add("joust", { name: "Gryphon Joust", Level: GJ.Level, marks: [2, 4, 6] });

  // ---- the Courier's Round ----
  const CO = CM.CO = { W: 400, H: 460, lives: 3, houseGap: 150 };
  CO.Level = class {
    constructor(n, seed, keep) { const R = this.rnd = new CM.Random(seed); this.n = n; this.t = 0; this.events = []; this.stage = "play"; Object.assign(this, keep || { score: 0, lives: CO.lives });
      this.houses = []; for (let k = 0; k < 10; k++) this.houses.push({ y: -k * CO.houseGap - 200, sub: R.chance(0.6) || k % 3 === 0, done: false, tint: R.int(0, 4) }); this.need = Math.ceil(this.houses.filter((h) => h.sub).length * 0.6); this.dist = 10 * CO.houseGap + 260 + CO.H; this.reset(); }
    reset() { this.p = { x: 250, dead: 0, guard: 1 }; this.scroll = 0; this.scrolls = 12; this.flying = []; this.obs = []; this.obsT = 1; this.got = 0; this.houses.forEach((h) => { h.done = false; }); this.ctl = 0; }
    input(mx) { this.ctl = mx; }
    throwIt() { if (this.p.dead || this.scrolls <= 0) return; this.scrolls -= 1; this.flying.push({ x: this.p.x - 10, y: CO.H - 80, vx: -260, vy: -40, t: 0 }); this.events.push({ kind: "throw" }); }
    update(dt) {
      if (this.stage !== "play") return; this.t += dt; const P = this.p;
      if (P.dead) { P.dead -= dt; if (P.dead <= 0) { P.dead = 0; if (this.lives <= 0) { this.stage = "over"; this.events.push({ kind: "over" }); } else this.reset(); } return; }
      const sp = 70 + 8 * this.n; this.scroll += sp * dt; P.x = clamp(P.x + this.ctl * 170 * dt, 190, 370); if (P.guard > 0) P.guard -= dt;
      if ((this.obsT -= dt) <= 0) { this.obsT = Math.max(0.6, 1.8 - 0.1 * this.n) * (0.6 + this.rnd.next() * 0.8); const kind = this.rnd.pick(["dog", "cart", "puddle", "barrel"]); this.obs.push({ kind, x: 200 + this.rnd.next() * 165, y: -this.scroll - 40, vx: kind === "dog" ? (this.rnd.chance(0.5) ? 70 : -70) : 0 }); }
      for (const O of this.obs) { O.x += O.vx * dt; if (O.x < 195 || O.x > 370) O.vx = -O.vx; const sy = O.y + this.scroll; if (P.guard <= 0 && Math.abs(sy - (CO.H - 70)) < 18 && Math.abs(O.x - P.x) < 18) { if (O.kind === "puddle") { P.x = clamp(P.x + (this.rnd.chance(0.5) ? 40 : -40), 190, 370); O.hit = true; this.events.push({ kind: "splash" }); } else { this.lives -= 1; P.dead = 1.6; this.events.push({ kind: "die", x: P.x, why: O.kind }); return; } } }
      this.obs = this.obs.filter((O) => !O.hit && O.y + this.scroll < CO.H + 40);
      for (const F of this.flying) { F.t += dt; F.x += F.vx * dt; F.y += F.vy * dt; F.vy += 60 * dt;
        for (const h of this.houses) { const hy = h.y + this.scroll; if (h.sub && !h.done && F.x < 175 && F.x > 120 && Math.abs(F.y - (hy + 50)) < 26) { h.done = true; F.gone = true; this.got += 1; const pts = 100 + Math.round(80 * (1 - Math.abs(F.y - (hy + 50)) / 26)); this.score += pts; this.events.push({ kind: "deliver", x: 150, y: hy + 50, pts }); } }
        if (F.x < 60 || F.t > 1.4) F.gone = true; }
      this.flying = this.flying.filter((F) => !F.gone);
      if (this.scroll >= this.dist) { if (this.got >= this.need) { this.score += this.scrolls * 25; this.stage = "clear"; this.events.push({ kind: "clear", got: this.got }); } else { this.lives -= 1; P.dead = 1.6; this.events.push({ kind: "short", got: this.got, need: this.need }); } }
      // a bundle of scrolls by the road now and then
      if (this.scrolls < 4 && !this.bundle && this.rnd.chance(dt * 0.4)) this.bundle = { x: 220 + this.rnd.next() * 130, y: -this.scroll - 30 };
      if (this.bundle) { const sy = this.bundle.y + this.scroll; if (Math.abs(sy - (CO.H - 70)) < 18 && Math.abs(this.bundle.x - P.x) < 20) { this.scrolls += 8; this.bundle = null; this.events.push({ kind: "bundle" }); } else if (sy > CO.H + 20) this.bundle = null; }
    }
  };
  CM.ARC.add("courier", { name: "The Courier's Round", Level: CO.Level, marks: [2, 4, 6] });

  // ---- the Undercroft Sprint ----
  const US = CM.US = { W: 520, H: 300, ground: 240, lives: 3, px: 110 };
  US.Level = class {
    constructor(n, seed, keep) { this.rnd = new CM.Random(seed); this.n = n; this.t = 0; this.events = []; this.stage = "play"; Object.assign(this, keep || { score: 0, lives: US.lives }); this.len = 3600 + 400 * n; this.speed = 230 + 18 * n; this.x = 0; this.things = []; this.nextAt = 500; this.p = { y: 0, vy: 0, slide: 0, guard: 0, onGround: true }; this.coins = 0; }
    jump() { const P = this.p; if (P.onGround) { P.vy = -470; P.onGround = false; P.slide = 0; this.events.push({ kind: "jump" }); } }
    slide() { const P = this.p; if (P.onGround) { P.slide = 0.6; this.events.push({ kind: "slide" }); } else P.vy = Math.max(P.vy, 300); }
    gen() { const R = this.rnd, k = R.pick(this.n >= 2 ? ["pit", "spikes", "beam", "bat", "pit", "spikes"] : ["pit", "spikes", "beam", "spikes"]); const t = { kind: k, x: this.nextAt, w: k === "pit" ? 60 + R.int(0, 30) + this.n * 3 : 26 };
      this.things.push(t); if (R.chance(0.7)) for (let c = 0; c < 4; c++) this.things.push({ kind: "coin", x: this.nextAt - 120 + c * 30, y: k === "beam" ? 18 : R.chance(0.5) ? 70 : 20 }); this.nextAt += Math.max(170, 320 - 10 * this.n) + R.int(0, 160); }
    update(dt) {
      if (this.stage !== "play") return; this.t += dt; const P = this.p, sp = this.speed * (1 + Math.min(0.3, this.x / this.len * 0.3)); this.x += sp * dt; while (this.nextAt < this.x + US.W + 100 && this.nextAt < this.len - 200) this.gen();
      P.vy += 1300 * dt; P.y += P.vy * dt; const wx = this.x + US.px, pit = this.things.find((t) => t.kind === "pit" && wx > t.x + 8 && wx < t.x + t.w - 8);
      if (P.y >= 0 && !pit) { P.y = 0; P.vy = 0; P.onGround = true; } else P.onGround = false; if (P.slide > 0) P.slide -= dt; if (P.guard > 0) P.guard -= dt;
      if (P.y > 120) { this.hurt("pit"); P.y = 0; P.vy = 0; P.guard = 1.5; this.x += 140; }
      const h = P.slide > 0 ? 18 : 40;
      for (const t of this.things) { if (t.done) continue; const dx = t.x + (t.w || 0) / 2 - wx;
        if (t.kind === "coin") { if (Math.abs(t.x - wx) < 14 && Math.abs(-P.y + 10 - t.y) < 26) { t.done = true; this.coins += 1; this.score += 10; this.events.push({ kind: "coin" }); } continue; }
        if (P.guard > 0 || Math.abs(dx) > (t.w || 20) / 2 + 8) continue;
        if (t.kind === "spikes" && P.y > -18) this.hurt("spikes", t); else if (t.kind === "beam" && h > 24) this.hurt("beam", t); else if (t.kind === "bat" && !(P.slide > 0) && P.y > -50) this.hurt("bat", t); }
      this.score += Math.round(sp * dt * 0.1);
      if (this.x >= this.len) { this.stage = "clear"; this.events.push({ kind: "clear" }); }
    }
    hurt(why, t) { if (this.p.guard > 0) return; this.lives -= 1; this.p.guard = 1.5; if (t) t.done = true; this.events.push({ kind: "hurt", why }); if (this.lives <= 0) { this.stage = "over"; this.events.push({ kind: "over" }); } }
  };
  CM.ARC.add("sprint", { name: "The Undercroft Sprint", Level: US.Level, marks: [2, 4, 6] });

  // ---- the Rune Bastion ----
  const RBT = CM.RBT = { C: 32, W: 16, H: 11, hearts: 15,
    PATH: [[0, 2], [5, 2], [5, 8], [2, 8], [2, 5], [10, 5], [10, 1], [13, 1], [13, 8], [8, 8], [8, 10]],
    TOWERS: { fire: { cost: 30, range: 2.3, rate: 1.1, dmg: 26, splash: 0.9, col: "#F06030" }, frost: { cost: 25, range: 2.0, rate: 0.9, dmg: 7, slow: 0.5, col: "#60C0F0" }, arcane: { cost: 45, range: 3.6, rate: 0.75, dmg: 20, col: "#B070F0" } },
    FOES: { goblin: { hp: 34, sp: 1.6, mana: 6, pts: 20 }, wolf: { hp: 26, sp: 2.8, mana: 7, pts: 30 }, ogre: { hp: 130, sp: 0.95, mana: 20, pts: 80 } } };
  RBT.cells = (() => { const out = []; for (let i = 0; i < RBT.PATH.length - 1; i++) { const [x0, y0] = RBT.PATH[i], [x1, y1] = RBT.PATH[i + 1]; const dx = Math.sign(x1 - x0), dy = Math.sign(y1 - y0); let x = x0, y = y0; while (x !== x1 || y !== y1) { out.push([x, y]); x += dx; y += dy; } } out.push(RBT.PATH[RBT.PATH.length - 1]); return out; })();
  RBT.onPath = new Set(RBT.cells.map(([x, y]) => `${x},${y}`));
  RBT.Level = class {
    constructor(n, seed, keep) { this.rnd = new CM.Random(seed); this.n = n; this.t = 0; this.events = []; this.stage = "play"; Object.assign(this, keep || { score: 0, lives: RBT.hearts, mana: 80, towers: [] }); this.towers = (this.towers || []).map((t) => ({ ...t, cd: 0 }));
      const R = this.rnd; this.queue = []; const count = 8 + 3 * n; for (let k = 0; k < count; k++) this.queue.push(n >= 5 && k % 6 === 5 ? "ogre" : n >= 3 && R.chance(0.3) ? "wolf" : n >= 2 && k === count - 1 ? "ogre" : "goblin");
      this.foes = []; this.shots = []; this.sendT = 5; this.hpMul = 1 + 0.18 * (n - 1); this.started = false; }
    canBuild(x, y) { return x >= 0 && y >= 0 && x < RBT.W && y < RBT.H && !RBT.onPath.has(`${x},${y}`) && !this.towers.some((t) => t.x === x && t.y === y); }
    build(kind, x, y) { const T = RBT.TOWERS[kind]; if (!T || !this.canBuild(x, y)) return "Not there."; if (this.mana < T.cost) return `That rune takes ${T.cost} mana.`; this.mana -= T.cost; this.towers.push({ kind, x, y, lvl: 1, cd: 0 }); this.events.push({ kind: "build", x, y, what: kind }); return ""; }
    upgrade(x, y) { const t = this.towers.find((q) => q.x === x && q.y === y); if (!t || t.lvl >= 3) return "It is as strong as it gets."; const cost = Math.round(RBT.TOWERS[t.kind].cost * 0.8 * t.lvl); if (this.mana < cost) return `Strengthening takes ${cost} mana.`; this.mana -= cost; t.lvl += 1; this.events.push({ kind: "upgrade", x, y }); return ""; }
    update(dt) {
      if (this.stage !== "play") return; this.t += dt;
      if (this.queue.length && (this.sendT -= dt) <= 0) { this.sendT = Math.max(0.45, 1.1 - 0.04 * this.n); const kind = this.queue.shift(), F = RBT.FOES[kind]; this.foes.push({ kind, d: 0, hp: F.hp * this.hpMul, max: F.hp * this.hpMul, slow: 0, id: this.t }); }
      for (const f of this.foes) { const F = RBT.FOES[f.kind]; f.d += F.sp * (f.slow > 0 ? 0.5 : 1) * dt; if (f.slow > 0) f.slow -= dt; if (f.d >= RBT.cells.length - 1) { f.gone = true; this.lives -= f.kind === "ogre" ? 3 : 1; this.events.push({ kind: "leak" }); } }
      const pos = (f) => { const i = Math.min(RBT.cells.length - 2, Math.floor(f.d)), k = f.d - i, [x0, y0] = RBT.cells[i], [x1, y1] = RBT.cells[i + 1]; return [x0 + (x1 - x0) * k + 0.5, y0 + (y1 - y0) * k + 0.5]; };
      for (const t of this.towers) { const T = RBT.TOWERS[t.kind]; t.cd -= dt; if (t.cd > 0) continue; let best = null; for (const f of this.foes) { if (f.gone) continue; const [fx, fy] = pos(f); if (Math.hypot(fx - t.x - 0.5, fy - t.y - 0.5) <= T.range + 0.3 * (t.lvl - 1) && (!best || f.d > best.d)) best = f; }
        if (!best) continue; t.cd = 1 / (T.rate * (1 + 0.25 * (t.lvl - 1))); const [fx, fy] = pos(best), dmg = T.dmg * (1 + 0.6 * (t.lvl - 1)); this.shots.push({ kind: t.kind, x0: t.x + 0.5, y0: t.y + 0.5, x1: fx, y1: fy, at: this.t });
        const hit = (f, d) => { f.hp -= d; if (T.slow) f.slow = 1.2; if (f.hp <= 0 && !f.gone) { f.gone = true; const F = RBT.FOES[f.kind]; this.mana += F.mana; this.score += F.pts; const [x, y] = pos(f); this.events.push({ kind: "fall", x, y, pts: F.pts }); } };
        if (T.splash) { for (const f of this.foes) { const [x, y] = pos(f); if (Math.hypot(x - fx, y - fy) < T.splash) hit(f, dmg); } } else hit(best, dmg); this.events.push({ kind: "shot", what: t.kind }); }
      this.foes = this.foes.filter((f) => !f.gone); this.shots = this.shots.filter((s) => this.t - s.at < 0.25);
      if (this.lives <= 0) { this.stage = "over"; this.events.push({ kind: "over" }); return; }
      if (!this.queue.length && !this.foes.length) { const bonus = 25 + 5 * this.n; this.mana += bonus; this.score += this.lives * 10; this.stage = "clear"; this.events.push({ kind: "held", bonus }); }
    }
    pos(f) { const i = Math.min(RBT.cells.length - 2, Math.floor(f.d)), k = f.d - i, [x0, y0] = RBT.cells[i], [x1, y1] = RBT.cells[i + 1]; return [x0 + (x1 - x0) * k + 0.5, y0 + (y1 - y0) * k + 0.5]; }
  };
  CM.ARC.add("bastion", { name: "The Rune Bastion", Level: RBT.Level, keep: (L) => ({ score: L.score, lives: L.lives, mana: L.mana, towers: L.towers.map(({ kind, x, y, lvl }) => ({ kind, x, y, lvl })) }), marks: [3, 5, 8] });

  // ---- the Vault Runes ----
  const VR = CM.VR = { gold: (n) => 10 + 6 * n, tickets: (n) => 2 + Math.floor(n / 2) };
  VR.size = (n) => (n <= 3 ? [3, 3] : n <= 6 ? [4, 4] : n <= 10 ? [5, 5] : n <= 15 ? [6, 5] : [6, 6]);
  // a lock: from all lit, a few touches undone; the same each time for a level
  VR.Lock = class {
    constructor(n, seed) { const [w, h] = VR.size(n), R = new CM.Random(seed); this.n = n; this.w = w; this.h = h; this.cross = n >= 8; this.on = Array.from({ length: h }, () => Array(w).fill(true)); this.moves = 0; this.par = 0;
      const k = Math.min(w * h - 2, 3 + Math.floor(n * 0.8)), used = new Set(); while (used.size < k) { const x = R.int(0, w - 1), y = R.int(0, h - 1); if (used.has(`${x},${y}`)) continue; used.add(`${x},${y}`); this.flip(x, y, true); } this.par = k; if (this.solved()) this.flip(0, 0, true); }
    nb(x, y) { const o = [[x, y], [x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1]]; if (this.cross) o.push([x + 1, y + 1], [x - 1, y - 1], [x + 1, y - 1], [x - 1, y + 1]); return o.filter(([a, b]) => a >= 0 && b >= 0 && a < this.w && b < this.h); }
    flip(x, y, quiet) { for (const [a, b] of this.nb(x, y)) this.on[b][a] = !this.on[b][a]; if (!quiet) this.moves += 1; }
    solved() { return this.on.every((r) => r.every(Boolean)); }
  };
  Object.assign(CM.Game.prototype, {
    vrStore() { const F = this.cgStore(); F.vr = F.vr || { done: {}, best: {}, opened: 0 }; return F.vr; },
    vrNew(n) { const S = this.vrStore(); n = Math.max(1, Math.min(n, (Object.keys(S.done).length || 0) + 1)); this.vrLive = new VR.Lock(n, CM.hashSeed(`${this.seed}:vault:${n}`)); if (this.cgStamp) this.cgStamp("vault"); return this.vrLive; },
    vrTouch(x, y) { const L = this.vrLive; if (!L || L.open) return null; L.flip(x, y); if (!L.solved()) return { moved: true };
      L.open = true; const S = this.vrStore(), n = L.n, first = !S.done[n], out = { open: true, n, moves: L.moves, par: L.par, first }; S.opened += 1; S.best[n] = Math.min(S.best[n] || 1e9, L.moves); const tk = VR.tickets(n) + (L.moves <= L.par ? 2 : 0); if (this.tkAdd) this.tkAdd(tk, "vault"); out.tickets = tk;
      if (first) { S.done[n] = true; out.gold = VR.gold(n); this.cgPay("vault", out.gold); if (n % 3 === 0) out.card = this.cgTierCard(CM.cardTierFor(n), `The Vault Runes: vault ${n} opened!`, new CM.Random(CM.hashSeed(`${this.seed}:vault:card:${n}`))); }
      this.saveCasino && this.saveCasino(); this.emit("change"); return out; },
  });
}
