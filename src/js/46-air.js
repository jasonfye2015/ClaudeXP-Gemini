"use strict";
// The air: what drifts, falls and rises about the party, drawn as small billboards rebuilt each frame. CM.airKinds
// (27-props.js) says what belongs where and how many; CM.Air keeps the motes alive, spawns them in a box about the
// eye and moves them; the frame loop hands their sprites to the renderer with the rest. Far things - clouds, birds and
// chimney smoke - are spawned where they belong (the sky, the roofs). Nothing here touches the rules.
CM.Air = class {
  constructor() { this.parts = []; this.env = null; this.acc = {}; this.t = 0; }
  // env: { kinds (CM.airKinds), eye [x, y, z], budget, chimneys [[x, z]], wind [x, z] }
  step(dt, env) {
    this.t += dt;
    const eye = env.eye, R = 7;
    for (const k of env.kinds) {                                        // spawn: each kind at its rate, while there is room in the budget
      this.acc[k.id] = (this.acc[k.id] || 0) + dt * k.rate;
      while (this.acc[k.id] >= 1) {
        this.acc[k.id] -= 1;
        if (this.parts.length >= env.budget) continue;
        let p = null;
        for (let tries = 0; tries < 4 && !p; tries++) { p = this.spawn(k, eye, R, env); if (p && !p.far && env.open && !env.open(Math.floor(p.x), Math.floor(p.z))) p = null; }   // (below ground: only in the open, where it can be seen)
        if (p) this.parts.push(p);
      }
    }
    const w = env.wind || [0, 0];
    for (const p of this.parts) {                                        // move: their own drift, the wind, a sway
      p.age += dt;
      p.x += (p.vx + w[0] * p.windy) * dt + Math.sin(this.t * p.sway + p.seed) * p.swayAmp * dt;
      p.y += p.vy * dt;
      p.z += (p.vz + w[1] * p.windy) * dt + Math.cos(this.t * p.sway * 0.8 + p.seed) * p.swayAmp * dt;
      if (p.grow) p.size += p.grow * dt;
    }
    this.parts = this.parts.filter((p) => p.age < p.life && p.y > -0.05 && p.y < (p.top || 3) && Math.abs(p.x - eye[0]) < (p.far ? 120 : R + 2) && Math.abs(p.z - eye[2]) < (p.far ? 120 : R + 2));
  }
  spawn(k, eye, R, env) {
    const r = Math.random, near = ["rain", "snow", "mote", "drip", "glitter"].includes(k.id) ? 3.5 : R, around = () => { for (;;) { const x = eye[0] + (r() * 2 - 1) * near, z = eye[2] + (r() * 2 - 1) * near; if (Math.hypot(x - eye[0], z - eye[2]) > 0.8) return [x, z]; } };   // (what falls thick is spawned close, but never in the party's face)
    const base = { kind: k.id, age: 0, seed: r() * 10, sway: 0.6 + r(), swayAmp: 0, windy: 0, vx: 0, vy: 0, vz: 0, life: 6, size: 0.04, glow: 0, alpha: 1, layer: `air:${k.id}` };
    switch (k.id) {
      case "mote": { const [x, z] = around(); return Object.assign(base, { x, z, y: 0.15 + r() * 0.75, vy: (r() - 0.5) * 0.02, swayAmp: 0.05, life: 5 + r() * 5, size: 0.025 + r() * 0.025, glow: 2, alpha: 0.75 }); }
      case "drip": { const [x, z] = around(); return Object.assign(base, { x, z, y: 0.98, vy: -2.2, life: 0.8, size: 0.03, h: 0.07, glow: 2 }); }
      case "ember": { const [x, z] = around(); return Object.assign(base, { x, z, y: 0.02, vy: 0.25 + r() * 0.2, swayAmp: 0.15, life: 3 + r() * 2, size: 0.04 + r() * 0.04, glow: 2, top: 1.1 }); }
      case "spore": { const [x, z] = around(); return Object.assign(base, { x, z, y: 0.1 + r() * 0.6, vy: 0.04 + r() * 0.04, swayAmp: 0.12, life: 6 + r() * 4, size: 0.045 + r() * 0.04, glow: 2 }); }
      case "glitter": { const [x, z] = around(); return Object.assign(base, { x, z, y: 0.1 + r() * 0.8, vy: -0.02, life: 1 + r() * 1.5, size: 0.035 + r() * 0.03, glow: 2 }); }
      case "leaf": { const [x, z] = around(); return Object.assign(base, { x, z, y: 2.2 + r() * 0.5, vy: -0.35 - r() * 0.2, swayAmp: 0.5, windy: 0.6, life: 9, size: 0.14 + r() * 0.08, top: 3.2 }); }
      case "firefly": { const [x, z] = around(); return Object.assign(base, { x, z, y: 0.2 + r() * 1.0, vx: (r() - 0.5) * 0.15, vz: (r() - 0.5) * 0.15, swayAmp: 0.3, life: 4 + r() * 4, size: 0.055, glow: 2 }); }
      case "rain": { const [x, z] = around(); return Object.assign(base, { x, z, y: 3.0, y: 2.2 + r() * 0.8, vy: -7 - r() * 2, windy: 0.4, life: 0.6, size: 0.03, h: 0.55, glow: 2, alpha: 0.85, top: 3.2 }); }
      case "snow": { const [x, z] = around(); return Object.assign(base, { x, z, y: 2.8, y: 1.2 + r() * 1.6, vy: -0.5 - r() * 0.3, swayAmp: 0.35, windy: 0.5, life: 7, size: 0.05 + r() * 0.05, glow: 2, top: 3.2 }); }
      case "cloud": { const a = r() * Math.PI * 2, d = 40 + r() * 30; return Object.assign(base, { x: eye[0] + Math.cos(a) * d, z: eye[2] + Math.sin(a) * d, y: 22 + r() * 10, vx: 0.6, life: 160, size: 9 + r() * 7, h: 0.45, alpha: 0.85, glow: 2, far: true, top: 60 }); }
      case "bird": { const a = r() * Math.PI * 2, d = 35 + r() * 20, s = 3 + r() * 2; return Object.assign(base, { x: eye[0] + Math.cos(a) * d, z: eye[2] + Math.sin(a) * d, y: 12 + r() * 8, vx: -Math.sin(a) * s, vz: Math.cos(a) * s, life: 25, size: 0.7, far: true, top: 40, flap: true }); }
      case "smoke": { const ch = (env.chimneys || [])[Math.floor(r() * (env.chimneys || []).length)]; if (!ch) return null; return Object.assign(base, { x: ch[0] + (r() - 0.5) * 0.1, z: ch[1] + (r() - 0.5) * 0.1, y: 2.05, vy: 0.35, windy: 0.4, swayAmp: 0.1, life: 6, size: 0.3, grow: 0.18, alpha: 0.8, top: 6 }); }
      default: return null;
    }
  }
  // the motes as the renderer's sprites: a cell and an offset in it, a lift, a size
  sprites(t) {
    const out = [];
    for (const p of this.parts) {
      const x = Math.floor(p.x), y = Math.floor(p.z), fade = Math.min(1, p.age / 0.4, (p.life - p.age) / 0.6);
      let w = p.size, h = p.h ? p.h : p.size;
      if (p.flap) h = p.size * (0.5 + 0.3 * Math.abs(Math.sin(t * 6 + p.seed)));
      out.push({ x, y, dx: p.x - x - 0.5, dz: p.z - y - 0.5, lift: p.y - h / 2, layer: p.layer, w, h, glow: p.glow, alpha: p.alpha * Math.max(0, fade), air: true });
    }
    return out;
  }
};

// the motes' pictures: small, plain, painted once
CM.art.airPicture = function (id) {
  const S = 64, c = document.createElement("canvas"); c.width = c.height = S;
  const p = c.getContext("2d"), dot = (col, r = S * 0.32) => { p.fillStyle = col; p.beginPath(); p.arc(S / 2, S / 2, r, 0, Math.PI * 2); p.fill(); };
  switch (id) {
    case "mote": dot("#E8DCC0", S * 0.3); break;
    case "drip": p.fillStyle = "#9CC8E8"; p.beginPath(); p.moveTo(S / 2, 4); p.quadraticCurveTo(S * 0.82, S * 0.7, S / 2, S - 4); p.quadraticCurveTo(S * 0.18, S * 0.7, S / 2, 4); p.fill(); break;
    case "ember": dot("#FFB040"); p.fillStyle = "#FFF0B0"; p.beginPath(); p.arc(S / 2, S / 2, S * 0.14, 0, Math.PI * 2); p.fill(); break;
    case "spore": dot("#A8F0A0"); break;
    case "glitter": p.fillStyle = "#E8F8FF"; p.beginPath(); p.moveTo(S / 2, 0); p.lineTo(S * 0.6, S * 0.4); p.lineTo(S, S / 2); p.lineTo(S * 0.6, S * 0.6); p.lineTo(S / 2, S); p.lineTo(S * 0.4, S * 0.6); p.lineTo(0, S / 2); p.lineTo(S * 0.4, S * 0.4); p.closePath(); p.fill(); break;
    case "leaf": p.fillStyle = "#C8742C"; p.beginPath(); p.ellipse(S / 2, S / 2, S * 0.42, S * 0.22, 0.6, 0, Math.PI * 2); p.fill(); p.strokeStyle = "#7A4418"; p.lineWidth = 3; p.beginPath(); p.moveTo(S * 0.2, S * 0.75); p.lineTo(S * 0.8, S * 0.25); p.stroke(); break;
    case "firefly": dot("#E8FF9A", S * 0.3); p.fillStyle = "#FFFFE0"; p.beginPath(); p.arc(S / 2, S / 2, S * 0.14, 0, Math.PI * 2); p.fill(); break;
    case "rain": p.fillStyle = "#DCE6F4"; p.fillRect(S * 0.4, 0, S * 0.2, S); break;
    case "snow": dot("#FFFFFF", S * 0.34); break;
    case "cloud": { p.fillStyle = "#F2F4F8"; for (const [x, y, r] of [[0.3, 0.6, 0.22], [0.5, 0.45, 0.28], [0.7, 0.6, 0.22], [0.5, 0.68, 0.24], [0.18, 0.7, 0.14], [0.84, 0.7, 0.14]]) { p.beginPath(); p.arc(S * x, S * y, S * r, 0, Math.PI * 2); p.fill(); } p.fillStyle = "rgba(170,180,200,1)"; p.fillRect(S * 0.08, S * 0.78, S * 0.84, S * 0.06); break; }
    case "bird": p.strokeStyle = "#2A2A30"; p.lineWidth = 6; p.lineCap = "round"; p.beginPath(); p.moveTo(S * 0.08, S * 0.35); p.quadraticCurveTo(S * 0.3, S * 0.2, S / 2, S * 0.55); p.quadraticCurveTo(S * 0.7, S * 0.2, S * 0.92, S * 0.35); p.stroke(); break;
    case "smoke": { const rnd = new CM.Random(5), img = p.createImageData(S, S); for (let y = 0; y < S; y++) for (let x = 0; x < S; x++) { const d = Math.hypot(x - S / 2, y - S / 2) / (S / 2), k = Math.max(0, 1 - d), i = (y * S + x) * 4; img.data[i] = 150; img.data[i + 1] = 150; img.data[i + 2] = 156; img.data[i + 3] = k > 0.45 || rnd.next() < k * 2.2 ? 255 : 0; } p.putImageData(img, 0, 0); break; }
    default: break;
  }
  return c;
};
CM.art.AIR = ["mote", "drip", "ember", "spore", "glitter", "leaf", "firefly", "rain", "snow", "cloud", "bird", "smoke"];
