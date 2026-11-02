"use strict";
// Sound in its place (v28.0, UPGRADE_PLAN_23.md): monsters are heard from where they are - to the left or right, louder
// the nearer, and dull and low behind a wall - and every sound takes the room it is made in: a hall or a cave rings, a
// corridor is dry, the open air hardly answers. The sounds go through a send to a reverb whose size and share follow
// the party's place, worked out a few times a second.
{ const A = CM.audio;
  // the graph: every sound to the master as before, and a share of it to the room
  const ir = (secs, decay) => { const ctx = A.ctx, n = Math.floor(ctx.sampleRate * secs), b = ctx.createBuffer(2, n, ctx.sampleRate), R = new CM.Random(91);
    for (let c = 0; c < 2; c++) { const d = b.getChannelData(c); for (let i = 0; i < n; i++) d[i] = (R.next() * 2 - 1) * Math.pow(1 - i / n, decay); } return b; };
  A.room = () => { if (!A.ctx) return null; if (A._room) return A._room; const ctx = A.ctx, send = ctx.createGain(), conv = ctx.createConvolver(), back = ctx.createGain();
    send.gain.value = 0.1; back.gain.value = 0.9; conv.buffer = ir(1.2, 3); send.connect(conv); conv.connect(back); back.connect(A.master); A._room = { send, conv, size: "mid" }; return A._room; };
  const SIZES = { small: [0.6, 4], mid: [1.2, 3], large: [2.2, 2.4], cave: [3.0, 2.0] };
  A.setSpace = (wet, size) => { const R = A.room(); if (!R) return; R.send.gain.setTargetAtTime(wet, A.ctx.currentTime, 0.3); if (size !== R.size && SIZES[size]) { R.size = size; R.conv.buffer = ir(...SIZES[size]); } };
  // a sound from a place: its side, its distance, and (behind a wall) muffled
  A.play3d = function (name, volume, pan, muffle) {
    if (!this.ctx || !this.enabled || !this.buffers[name]) return;
    const ctx = this.ctx, src = ctx.createBufferSource(), g = ctx.createGain(); src.buffer = this.buffers[name]; g.gain.value = CM.clamp(volume, 0, 1);
    let node = src; if (muffle) { const f = ctx.createBiquadFilter(); f.type = "lowpass"; f.frequency.value = 520; src.connect(f); node = f; }
    node.connect(g); let out = g; if (ctx.createStereoPanner) { const p = ctx.createStereoPanner(); p.pan.value = CM.clamp(pan, -1, 1); g.connect(p); out = p; }
    out.connect(this.master); const R = this.room(); if (R) out.connect(R.send); src.start();
  };
  { const play0 = A.play; A.play = function (name, volume = 1, pan = 0, rate = 1) {   // (the ordinary sounds take the room too)
      if (!this.ctx || !this.enabled || !this.buffers[name]) return; const R = this.room();
      if (!R) return play0.call(this, name, volume, pan, rate);
      const src = this.ctx.createBufferSource(), g = this.ctx.createGain(); src.buffer = this.buffers[name]; if (rate !== 1) src.playbackRate.value = rate; g.gain.value = CM.clamp(volume, 0, 1); src.connect(g);
      let out = g; if (pan && this.ctx.createStereoPanner) { const p = this.ctx.createStereoPanner(); p.pan.value = CM.clamp(pan, -1, 1); g.connect(p); out = p; }
      out.connect(this.master); out.connect(R.send); src.start(); }; }
  // the place's acoustics
  CM.acoustics = (game) => { const fl = game.floor; if (!fl) return [0.05, "small"]; const n = fl.number, [x, y] = fl.pos;
    if (fl.special === "interior") return [0.16, "small"]; if (fl.special === "joker") return [0.22, "large"];
    if (n === 0) return [0.06, "mid"]; if (n === -1) return [0.03, "mid"];
    if (CM.isUndercroft && CM.isUndercroft(n)) return [0.4, "cave"]; if (n % 1 !== 0 && n < 0) return [0.42, "cave"];
    const open = CM.openNeighbours(fl, x, y).length, room = (fl.rooms || []).find((r) => x >= r.x0 && x <= r.x1 && y >= r.y0 && y <= r.y1);
    const band = CM.themeIndex(Math.max(1, n)), hall = band === 2 || band === 3;
    if (!room && open <= 2) return [0.07, "small"];
    const area = room ? (room.x1 - room.x0 + 1) * (room.y1 - room.y0 + 1) : 9;
    return area >= 40 || hall ? [0.32, "large"] : [0.2, "mid"]; };
  // a straight way between two squares, or a wall between them
  const clear = (fl, ax, ay, bx, by) => { const steps = Math.max(Math.abs(bx - ax), Math.abs(by - ay)); for (let i = 1; i < steps; i++) { const x = Math.round(ax + (bx - ax) * i / steps), y = Math.round(ay + (by - ay) * i / steps); if (!CM.isOpen(fl, x, y)) return false; } return true; };
  // the monsters about: now and then one is heard, from where it is
  let nextGrowl = 0, spaceAt = 0;
  const tick = () => { const g = CM.game, r = CM.renderer; if (!g || !g.floor || !A.ctx || !r) return; const now = performance.now();
    if (now > spaceAt) { spaceAt = now + 250; const [wet, size] = CM.acoustics(g); A.setSpace(wet, size); }
    if (g.mode !== "explore" || now < nextGrowl || !CM.isDeep(g.floor.number)) return; nextGrowl = now + 3500 + Math.random() * 4500;
    const fl = g.floor, [px, py] = fl.pos; let best = null, bd = 99;
    for (const [k, t] of Object.entries(fl.things)) { if (!(t.type === "monsters" || t.type === "boss" || t.type === "guardian") || t.asleep) continue; const [x, y] = k.split(",").map(Number), d = Math.hypot(x - px, y - py); if (d < bd && d <= 9) { bd = d; best = [x, y, t]; } }
    if (!best) return; const [x, y, t] = best, ang = Math.atan2(x - px, -(y - py)) - r.yaw, pan = Math.sin(ang), behind = Math.cos(ang) < -0.3, wall = !clear(fl, px, py, x, y);
    const m = (t.group && t.group[0]) || {}; A.play3d(CM.roarFor(m.kind || m.name), 0.32 / (1 + bd * 0.35) * (wall ? 0.7 : 1), pan * (behind ? 0.8 : 1), wall || behind);
  };
  setInterval(tick, 200);
}
