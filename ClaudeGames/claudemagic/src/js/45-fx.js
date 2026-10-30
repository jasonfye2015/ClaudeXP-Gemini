"use strict";
// Motion and spectacle: what flies, bursts, rings, rains and hangs in the air of the view. CM.Effects keeps a list of
// short-lived effects; each frame the window asks it for their sprites (lit by their own glow, 40-render.js) and the
// expired fall off. A projectile can carry a `then` - its burst, its flash - for the moment it lands, and while one is
// in flight the window holds the damage it will do until it gets there (holdUntil). The recipes - which effect each
// event of the game gets - are in 80-main.js, where the camera and the foes' places are known.
CM.fxSpeed = 1;                                   // Settings > Combat speed: 1, 2 (fast) or 6 (as good as instant) - every effect's ms is divided by it
CM.reducedMotion = false;                         // Settings > Reduce motion: no shaking, no flashes, no washes of colour
CM.Effects = class {
  constructor() { this.list = []; this.holdUntil = 0; }
  get count() { return this.list.length; }
  clear() { this.list = []; this.holdUntil = 0; }
  now() { return performance.now(); }

  // a thing flying from one point to another (world x, height, z) over `ms`, trailing sparks; `then` runs when it lands
  projectile(o) {
    const e = Object.assign({ type: "projectile", t0: this.now(), ms: 320, size: 0.22, layer: "fx:fire", trail: "fx:spark", arc: 0.12, glow: 1 }, o);
    e.ms /= CM.fxSpeed || 1;
    this.list.push(e);
    this.holdUntil = Math.max(this.holdUntil, e.t0 + e.ms);
    return e.ms;
  }
  // sparks or shards from a point: n of them flung out, falling under gravity, fading
  burst(o) {
    const e = Object.assign({ type: "burst", t0: this.now(), ms: 650, n: 14, speed: 1.4, up: 1.6, gravity: 3.2, size: 0.07, layer: "fx:spark", glow: 1, seed: 1 }, o);
    e.ms /= CM.fxSpeed || 1;
    const rnd = new CM.Random(e.seed + Math.floor(e.t0 % 1000));
    e.parts = [];
    for (let i = 0; i < e.n; i++) {
      const a = rnd.next() * Math.PI * 2, s = e.speed * (0.4 + rnd.next() * 0.8);
      e.parts.push({ x: e.at[0], y: e.at[1], z: e.at[2], vx: Math.cos(a) * s, vz: Math.sin(a) * s, vy: e.up * (0.3 + rnd.next() * 0.9), size: e.size * (0.6 + rnd.next() * 0.8) });
    }
    e.last = e.t0;
    this.list.push(e);
  }
  // a ring on the floor, spreading out from a point
  ring(o) { const e = Object.assign({ type: "ring", t0: this.now(), ms: 800, at: [0, 0, 0], to: 2.4, layer: "fx:ring", glow: 1 }, o); e.ms /= CM.fxSpeed || 1; this.list.push(e); }
  // something hanging in the air for a moment (lightning over a foe, a holy light): a billboard that grows and fades
  flare(o) { const e = Object.assign({ type: "flare", t0: this.now(), ms: 260, size: 0.6, layer: "fx:bolt", glow: 1, rise: 0, grow: 0.3 }, o); e.ms /= CM.fxSpeed || 1; this.list.push(e); }
  // things falling onto a point from above (shards of ice)
  rain(o) {
    const e = Object.assign({ type: "rain", t0: this.now(), ms: 520, n: 8, layer: "fx:frost", size: 0.12, glow: 1, spread: 0.4, seed: 2 }, o);
    e.ms /= CM.fxSpeed || 1;
    const rnd = new CM.Random(e.seed + Math.floor(e.t0 % 1000));
    e.parts = [];
    for (let i = 0; i < e.n; i++) e.parts.push({ dx: (rnd.next() - 0.5) * e.spread, dz: (rnd.next() - 0.5) * e.spread, delay: rnd.next() * 0.4, size: e.size * (0.7 + rnd.next() * 0.6) });
    this.list.push(e);
  }
  // motes drifting up from a point (sleep, a blessing)
  drift(o) {
    const e = Object.assign({ type: "drift", t0: this.now(), ms: 900, n: 6, layer: "fx:spark", size: 0.06, glow: 1, spread: 0.5, rise: 0.5, seed: 3 }, o);
    e.ms /= CM.fxSpeed || 1;
    const rnd = new CM.Random(e.seed + Math.floor(e.t0 % 1000));
    e.parts = [];
    for (let i = 0; i < e.n; i++) e.parts.push({ dx: (rnd.next() - 0.5) * e.spread, dz: (rnd.next() - 0.5) * e.spread, delay: rnd.next() * 0.5, size: e.size * (0.6 + rnd.next() * 0.8) });
    this.list.push(e);
  }

  // the sprites of everything in flight right now; the expired fall off the list (a landing projectile runs its then)
  sprites(now = this.now()) {
    const out = [], keep = [], spawn = [];
    const put = (e, x, y, z, size, layer, alpha = 1) => out.push({ x: x - 0.5, y: z - 0.5, lift: Math.max(0, y - size / 2), w: size, h: size, layer, alpha, glow: e.glow });
    for (const e of this.list) {
      const k = (now - e.t0) / e.ms;
      if (k >= 1) { if (e.type === "projectile" && e.then) { const then = e.then; e.then = null; then(); } continue; }
      keep.push(e);
      if (e.type === "projectile") {
        const kk = CM.ease(k), x = CM.lerp(e.from[0], e.to[0], kk), z = CM.lerp(e.from[2], e.to[2], kk), y = CM.lerp(e.from[1], e.to[1], kk) + Math.sin(Math.PI * kk) * e.arc;
        put(e, x, y, z, e.size, e.layer);
        if (e.trail && now - (e.lastTrail || 0) > 28) { e.lastTrail = now; spawn.push({ type: "mote", t0: now, ms: 220, at: [x, y, z], size: e.size * 0.3, layer: e.trail, glow: 1 }); }
      } else if (e.type === "mote") {
        put(e, e.at[0], e.at[1], e.at[2], e.size * (1 - k * 0.5), e.layer, 1 - k);
      } else if (e.type === "burst") {
        const dt = Math.min(0.05, (now - e.last) / 1000);
        e.last = now;
        for (const p of e.parts) {
          p.x += p.vx * dt; p.z += p.vz * dt; p.y += p.vy * dt; p.vy -= e.gravity * dt;
          if (p.y < 0.02) { p.y = 0.02; p.vy *= -0.3; p.vx *= 0.6; p.vz *= 0.6; }
          put(e, p.x, p.y, p.z, p.size, e.layer, 1 - k * k);
        }
      } else if (e.type === "ring") {
        out.push({ x: e.at[0] - 0.5, y: e.at[2] - 0.5, flat: true, w: Math.max(0.05, e.to * CM.ease(k)), layer: e.layer, alpha: 1 - k, glow: 1 });
      } else if (e.type === "flare") {
        put(e, e.at[0], e.at[1] + e.rise * k, e.at[2], e.size * (1 + k * e.grow), e.layer, k < 0.3 ? 1 : 1 - (k - 0.3) / 0.7);
      } else if (e.type === "rain") {
        for (const p of e.parts) {
          const kk = (k - p.delay) / (1 - p.delay);
          if (kk < 0 || kk > 1) continue;
          put(e, e.at[0] + p.dx, CM.lerp(1.15, 0.06, kk), e.at[2] + p.dz, p.size, e.layer, kk > 0.8 ? 1 - (kk - 0.8) / 0.2 : 1);
        }
      } else if (e.type === "drift") {
        for (const p of e.parts) {
          const kk = (k - p.delay) / (1 - p.delay);
          if (kk < 0 || kk > 1) continue;
          put(e, e.at[0] + p.dx, e.at[1] + e.rise * kk, e.at[2] + p.dz, p.size, e.layer, Math.sin(Math.PI * kk));
        }
      }
    }
    this.list = keep.concat(spawn);
    return out;
  }
};
