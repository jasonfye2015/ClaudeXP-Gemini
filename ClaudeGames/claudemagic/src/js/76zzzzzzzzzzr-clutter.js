"use strict";
// The clutter below ground - the window's side (UPGRADE_PLAN_63.md set 4, release 1): the stalagmites and the
// stalactites go into the plants' models as they load (69zzt-clutter.js makes them) and are drawn by the plants'
// instanced path; the wall decals - drainage ports and grates, pipe mouths, spiderwebs - are pictures made here and
// laid on the walls as decals (CM.lifeSprites); a pipe mouth drips; bugs crawl on the floor about the party and
// scatter from its feet; and a few rats sit at the corridors' edges and scurry off two squares when the party comes
// within two, never fought, never in the way.
{ const r = Math.random, S = 64;
  // the cones ride with the plants
  { const p0 = CM.Plants.parse; CM.Plants.parse = (bytes, manifest) => { const out = p0(bytes, manifest); if (CM.clutterModels) Object.assign(out.models, CM.clutterModels()); return out; }; }
  // the pictures
  const PICS = {
    "clut:port": (p) => { p.fillStyle = "#3A3632"; p.beginPath(); p.arc(S / 2, S / 2, S * 0.4, 0, Math.PI * 2); p.fill(); p.fillStyle = "#141210"; p.beginPath(); p.arc(S / 2, S / 2, S * 0.3, 0, Math.PI * 2); p.fill(); p.strokeStyle = "#5A544C"; p.lineWidth = 3; p.beginPath(); p.arc(S / 2, S / 2, S * 0.38, 0, Math.PI * 2); p.stroke(); p.fillStyle = "rgba(60,80,70,0.5)"; p.fillRect(S * 0.42, S * 0.72, S * 0.16, S * 0.28); },
    "clut:grate": (p) => { p.fillStyle = "#1A1816"; p.fillRect(S * 0.08, S * 0.2, S * 0.84, S * 0.6); p.strokeStyle = "#4A4640"; p.lineWidth = 4; p.strokeRect(S * 0.08, S * 0.2, S * 0.84, S * 0.6); for (let i = 1; i < 6; i++) { p.beginPath(); p.moveTo(S * (0.08 + 0.84 * i / 6), S * 0.2); p.lineTo(S * (0.08 + 0.84 * i / 6), S * 0.8); p.stroke(); } p.fillStyle = "rgba(40,60,50,0.5)"; p.fillRect(S * 0.3, S * 0.8, S * 0.4, S * 0.2); },
    "clut:pipe": (p) => { p.fillStyle = "#4A4034"; p.beginPath(); p.arc(S / 2, S * 0.45, S * 0.3, 0, Math.PI * 2); p.fill(); p.fillStyle = "#100E0C"; p.beginPath(); p.arc(S / 2, S * 0.45, S * 0.2, 0, Math.PI * 2); p.fill(); p.strokeStyle = "#6A5C48"; p.lineWidth = 3; p.beginPath(); p.arc(S / 2, S * 0.45, S * 0.28, 0, Math.PI * 2); p.stroke(); p.fillStyle = "rgba(80,110,100,0.55)"; p.fillRect(S * 0.44, S * 0.62, S * 0.12, S * 0.38); },
    "clut:web": (p) => { p.strokeStyle = "rgba(230,230,235,0.75)"; p.lineWidth = 1.2; const cx = S * 0.06, cy = S * 0.06; for (let i = 0; i <= 5; i++) { const a = i / 5 * Math.PI / 2; p.beginPath(); p.moveTo(cx, cy); p.lineTo(cx + Math.cos(a) * S * 0.92, cy + Math.sin(a) * S * 0.92); p.stroke(); } for (let k = 1; k <= 5; k++) { const rr = S * 0.18 * k; p.beginPath(); for (let i = 0; i <= 10; i++) { const a = i / 10 * Math.PI / 2, sag = 1 - 0.06 * Math.sin(i / 10 * Math.PI * 5); const X = cx + Math.cos(a) * rr * sag, Y = cy + Math.sin(a) * rr * sag; if (i === 0) p.moveTo(X, Y); else p.lineTo(X, Y); } p.stroke(); } },
    "air:bug": (p) => { p.fillStyle = "#1A1612"; p.beginPath(); p.ellipse(S / 2, S / 2, S * 0.16, S * 0.22, 0, 0, Math.PI * 2); p.fill(); p.strokeStyle = "#2A2420"; p.lineWidth = 3; for (const s of [-1, 1]) for (let i = 0; i < 3; i++) { p.beginPath(); p.moveTo(S / 2, S * (0.4 + i * 0.1)); p.lineTo(S / 2 + s * S * 0.3, S * (0.3 + i * 0.14)); p.stroke(); } } };
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); for (const name of Object.keys(PICS)) { if (name.startsWith("air:") || set.index[name] !== undefined) continue; const c = document.createElement("canvas"); c.width = c.height = S; PICS[name](c.getContext("2d")); set.index[name] = set.layers.length; set.layers.push(c); } return set; }; }
  { CM.art.AIR = CM.art.AIR || []; if (!CM.art.AIR.includes("bug")) CM.art.AIR.push("bug"); const ap0 = CM.art.airPicture; CM.art.airPicture = function (id) { if (id !== "bug") return ap0.call(this, id); const c = document.createElement("canvas"); c.width = c.height = S; PICS["air:bug"](c.getContext("2d")); return c; }; }
  // the decals and the rats, as life sprites
  const rats = new Map();   // id -> { x, z, hx, hz, tx, tz, t }
  const ratStep = (game, fl, R0, now) => { const out = [], [px, py] = fl.pos, open = (x, y) => fl.grid[y] && fl.grid[y][x] === 0;
    for (const home of CM.clutterRats(fl)) { if (Math.abs(home.x - px) + Math.abs(home.y - py) > 12) continue; let st = rats.get(home.id); if (!st) { st = { x: home.x + 0.5, z: home.y + 0.5, hx: home.x + 0.5, hz: home.y + 0.5, tx: null, tz: null, t: 0, yaw: 0 }; rats.set(home.id, st); }
      const d = Math.abs(st.x - px - 0.5) + Math.abs(st.z - py - 0.5);
      if (st.tx === null && d <= 2.2) {   // scurry: two squares along the corridor, away from the party
        const away = CM.DIRS.map(([dx, dy]) => [dx, dy]).filter(([dx, dy]) => open(Math.floor(st.x) + dx, Math.floor(st.z) + dy) && open(Math.floor(st.x) + dx * 2, Math.floor(st.z) + dy * 2)).sort((a, b) => (Math.abs(st.x + b[0] * 2 - px - 0.5) + Math.abs(st.z + b[1] * 2 - py - 0.5)) - (Math.abs(st.x + a[0] * 2 - px - 0.5) + Math.abs(st.z + a[1] * 2 - py - 0.5)))[0];
        if (away) { st.tx = st.x + away[0] * 2; st.tz = st.z + away[1] * 2; st.squeak = now; } }
      if (st.tx !== null) { const dx = st.tx - st.x, dz = st.tz - st.z, len = Math.hypot(dx, dz), step = 3.2 * 0.016; if (len < step) { st.x = st.tx; st.z = st.tz; st.tx = null; } else { st.x += dx / len * step; st.z += dz / len * step; } st.yaw = Math.atan2(dx, dz); }
      else if (d > 6 && (Math.abs(st.x - st.hx) > 0.1 || Math.abs(st.z - st.hz) > 0.1)) { st.x = st.hx; st.z = st.hz; }   // (home again when the party is far)
      const cx = Math.floor(st.x), cz = Math.floor(st.z); out.push({ x: cx, y: cz, dx: st.x - cx - 0.5, dz: st.z - cz - 0.5, layer: "monster:Giant Rat", w: 0.3, h: 0.26, id: home.id, walking: st.tx !== null, shade: 0.8 }); }
    return out; };
  { const ls0 = CM.lifeSprites; CM.lifeSprites = (game, fl, now) => { const out = ls0 ? ls0(game, fl, now) : []; if (!fl || !(fl.number >= 1) || !CM.clutterDecals || game.mode === "title") return out; const R0 = CM.renderer; if (!R0 || R0.index["clut:port"] === undefined) return out;
      for (const d of CM.clutterDecals(fl, fl.pos, 10)) out.push({ x: d.x, y: d.y, face: d.face, layer: `clut:${d.kind}`, w: d.w, h: d.h, lift: d.lift, mirror: d.along === -1, shade: d.kind === "web" ? 1.1 : 0.9, alpha: d.kind === "web" ? 0.85 : 1 });
      if (CM.figures && !CM.ratsOff) for (const s of ratStep(game, fl, R0, now)) out.push(s); return out; }; }
  // the bugs on the floor, and the pipes' drips
  { const k0 = CM.airKinds; CM.airKinds = function (env) { const out = k0.call(this, env); const g = CM.game, fl = g && g.floor; if (env.surface || !fl || !(fl.number >= 1) || g.mode === "title") return out; const band = CM.themeIndex(fl.number);
      const bugs = { 0: 5, 5: 7, 8: 6, 1: 3, 9: 4 }[band]; if (bugs) out.push({ id: "bug", rate: bugs });
      const pipes = CM.clutterDecals ? CM.clutterDecals(fl, fl.pos, 8).filter((d) => d.kind === "pipe").length : 0; if (pipes) out.push({ id: "pipedrip", rate: 1.2 * pipes }); return out; }; }
  { const sp0 = CM.Air.prototype.spawn; CM.Air.prototype.spawn = function (k, eye, R, env) { const g = CM.game;
      if (k.id === "bug") { const a = r() * Math.PI * 2, d = 1 + r() * 4, x = eye[0] + Math.cos(a) * d, z = eye[2] + Math.sin(a) * d; if (env.open && !env.open(Math.floor(x), Math.floor(z))) return null; const va = r() * Math.PI * 2;
        return { kind: "bug", age: 0.4, seed: r() * 10, sway: 0, swayAmp: 0, windy: 0, vx: Math.cos(va) * 0.12, vy: 0, vz: Math.sin(va) * 0.12, life: 6 + r() * 6, size: 0.035 + r() * 0.015, glow: 0, alpha: 1, x, z, y: 0.012, top: 0.5, layer: "air:bug", bug: true }; }
      if (k.id === "pipedrip") { const fl = g.floor, P = CM.clutterDecals(fl, fl.pos, 8).filter((d) => d.kind === "pipe"); if (!P.length) return null; const d = P[Math.floor(r() * P.length)], [dx, dy] = CM.DIRS[d.face];
        return { kind: "pipedrip", age: 0.4, seed: r() * 10, sway: 0, swayAmp: 0, windy: 0, vx: 0, vy: -1.6, vz: 0, life: 1.0, size: 0.025, h: 0.07, glow: 1.3, alpha: 0.8, x: d.x + 0.5 + dx * 0.42, z: d.y + 0.5 + dy * 0.42, y: 0.5 + d.lift - 0.08, top: 1.2, layer: "air:drip" }; }
      return sp0.call(this, k, eye, R, env); }; }
  { const st0 = CM.Air.prototype.step; CM.Air.prototype.step = function (dt, env) { const out = st0.call(this, dt, env); const eye = env.eye;
      for (const p of this.parts) { if (!p.bug) continue; const dx = p.x - eye[0], dz = p.z - eye[2], d = Math.hypot(dx, dz); if (d < 1.3 && d > 0.001) { p.vx = dx / d * 0.9; p.vz = dz / d * 0.9; } else if (r() < dt * 0.8) { const a = r() * Math.PI * 2; p.vx = Math.cos(a) * 0.12; p.vz = Math.sin(a) * 0.12; }
        if (env.open && !env.open(Math.floor(p.x), Math.floor(p.z))) { p.vx = -p.vx; p.vz = -p.vz; p.x += p.vx * 2 * dt; p.z += p.vz * 2 * dt; } } return out; }; }
}
