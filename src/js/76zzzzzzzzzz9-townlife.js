"use strict";
// The living town, the window's side (v61.0, UPGRADE_PLAN_56.md): hens pecking about the yards behind the houses by
// day; a cat on a fence, a hedge or the well's kerb, moving by the hour, and by the tavern's door at night (its eyes
// catching the light) and in the wet; pigeons on the wall's walk and the roof ridges that take wing when the party
// comes near and settle again after. Their pictures are painted here; where they are is 69zzk-townlife.js's.
{ const P = 64, cv = () => { const c = document.createElement("canvas"); c.width = c.height = P; return c; };
  const E = (p, x, y, rx, ry, col, rot = 0) => { p.fillStyle = col; p.beginPath(); p.ellipse(x, y, rx, ry, rot, 0, Math.PI * 2); p.fill(); };
  const hen = (p, peck) => { const hy = peck ? 44 : 22, hx = peck ? 50 : 46;
    p.strokeStyle = "#C8902A"; p.lineWidth = 3; for (const lx of [26, 36]) { p.beginPath(); p.moveTo(lx, 50); p.lineTo(lx, 60); p.lineTo(lx + 5, 60); p.stroke(); }   // legs
    E(p, 30, 38, 19, 13, "#8A5A32"); E(p, 26, 36, 12, 8, "#A87846", -0.3);                                                                      // body, wing
    p.fillStyle = "#4A3020"; p.beginPath(); p.moveTo(12, 34); p.lineTo(4, 22); p.lineTo(10, 24); p.lineTo(8, 16); p.lineTo(16, 28); p.fill();     // tail
    if (!peck) { p.strokeStyle = "#8A5A32"; p.lineWidth = 7; p.beginPath(); p.moveTo(42, 32); p.lineTo(hx, hy + 4); p.stroke(); }                 // neck
    E(p, hx, hy, 7, 6, "#8A5A32"); p.fillStyle = "#D83A2A"; p.beginPath(); p.arc(hx - 1, hy - 6, 3.5, 0, Math.PI * 2); p.fill(); p.fillRect(hx + 2, hy + 2, 3, 5);   // head, comb, wattle
    p.fillStyle = "#E8B030"; p.beginPath(); p.moveTo(hx + 6, hy - 1); p.lineTo(hx + 13, hy + 1); p.lineTo(hx + 6, hy + 3); p.fill(); p.fillStyle = "#1A1008"; p.fillRect(hx + 1, hy - 2, 2, 2); };   // beak, eye
  const cat = (p, eyes) => { const body = eyes ? "#1E1C22" : "#5A5A62", pale = eyes ? "#28262C" : "#8A8A92";
    p.strokeStyle = body; p.lineWidth = 5; p.lineCap = "round"; p.beginPath(); p.moveTo(18, 54); p.quadraticCurveTo(4, 52, 8, 36); p.stroke();   // tail
    E(p, 34, 44, 16, 14, body); E(p, 36, 48, 9, 8, pale); E(p, 40, 22, 11, 10, body);                                                            // body, chest, head
    p.fillStyle = body; p.beginPath(); p.moveTo(31, 16); p.lineTo(29, 4); p.lineTo(37, 12); p.fill(); p.beginPath(); p.moveTo(49, 16); p.lineTo(51, 4); p.lineTo(43, 12); p.fill();   // ears
    p.fillStyle = eyes ? "#F0E060" : "#D8C050"; for (const ex of [36, 45]) { p.beginPath(); p.ellipse(ex, 22, eyes ? 3 : 2.4, eyes ? 2.6 : 2.2, 0, 0, Math.PI * 2); p.fill(); }
    if (!eyes) { p.fillStyle = "#1A1A1E"; for (const ex of [36, 45]) p.fillRect(ex - 0.6, 20, 1.2, 4); } p.fillStyle = eyes ? "#403040" : "#C87878"; p.fillRect(39.5, 26, 2, 1.6);
    p.strokeStyle = body; p.lineWidth = 4; p.beginPath(); p.moveTo(28, 52); p.lineTo(28, 58); p.moveTo(40, 52); p.lineTo(40, 58); p.stroke(); };                 // forelegs
  const pigeon = (p, fly) => { if (fly) { p.fillStyle = "#6A6E80"; p.beginPath(); p.moveTo(32, 36); p.lineTo(2, 22); p.lineTo(10, 36); p.lineTo(30, 42); p.fill(); p.beginPath(); p.moveTo(32, 36); p.lineTo(62, 22); p.lineTo(54, 36); p.lineTo(34, 42); p.fill(); }   // wings out
    E(p, 32, fly ? 40 : 40, 15, 10, "#7A7E90"); E(p, 44, fly ? 32 : 30, 6, 5.5, "#6A6E80"); E(p, 40, 36, 6, 4, "#4A8A60", 0.5);                // body, head, the neck's green
    p.fillStyle = "#2A2A30"; p.fillRect(49, 30, 4, 2); p.fillRect(45, 29, 1.5, 1.5); p.fillStyle = "#3A3A44"; p.beginPath(); p.moveTo(18, 40); p.lineTo(6, 46); p.lineTo(18, 46); p.fill();   // beak, eye, tail
    if (!fly) { p.strokeStyle = "#C86060"; p.lineWidth = 2; for (const lx of [28, 36]) { p.beginPath(); p.moveTo(lx, 48); p.lineTo(lx, 55); p.stroke(); } } };
  const PAINT = { "life:hen": (p) => hen(p, false), "life:hen:peck": (p) => hen(p, true), "life:cat": (p) => cat(p, false), "life:cat:eyes": (p) => cat(p, true), "life:pigeon": (p) => pigeon(p, false), "life:pigeon:fly": (p) => pigeon(p, true) };
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); for (const [k, f] of Object.entries(PAINT)) { if (set.index[k] !== undefined) continue; const c = cv(); f(c.getContext("2d")); set.index[k] = set.layers.length; set.layers.push(c); } return set; }; }
  { const s0 = CM.art.isSurfaceLayer; CM.art.isSurfaceLayer = (name) => name in PAINT || s0(name); }
  const cache = new WeakMap(), of = (fl) => { let c = cache.get(fl); if (!c) { c = { flocks: CM.chickensOf(fl), roosts: CM.roostsOf(fl), state: new Map() }; cache.set(fl, c); } return c; };
  const at = (x, z, more) => Object.assign({ x: Math.floor(x), y: Math.floor(z), dx: x - Math.floor(x) - 0.5, dz: z - Math.floor(z) - 0.5 }, more);
  { const ls0 = CM.lifeSprites; CM.lifeSprites = (game, fl, now) => { const out = ls0 ? ls0(game, fl, now) : []; const r = CM.renderer;
      if (!fl || fl.number !== 0 || game.mode === "title" || !r || !r.index || r.index["life:hen"] === undefined) return out;
      const t = now / 1000, [px, py] = fl.pos, C = of(fl), shadow = r.index.shadow !== undefined, near = (x, z, n = 14) => Math.abs(x - px - 0.5) + Math.abs(z - py - 0.5) <= n;
      if (CM.chickensOut(game)) for (const f of C.flocks) { const [hx, hy] = f.squares[0]; if (!near(hx + 0.5, hy + 0.5, 16)) continue;
        for (let i = 0; i < f.n; i++) { const q = CM.chickenPose(f, i, t); if (!near(q.x, q.y)) continue;
          out.push(at(q.x, q.y, { layer: q.peck ? "life:hen:peck" : "life:hen", w: 0.26, h: 0.24, mirror: q.mirror, lift: q.moving && !CM.reducedMotion ? Math.abs(Math.sin(t * 9 + i)) * 0.015 : 0 }));
          if (shadow) out.push(at(q.x, q.y, { layer: "shadow", flat: true, w: 0.2, alpha: 0.6 })); } }
      const c = CM.catNow(game, fl); if (c && near(c.x + 0.5, c.y + 0.5)) { out.push({ x: c.x, y: c.y, dx: c.dx || 0, dz: c.dz || 0, layer: c.night ? "life:cat:eyes" : "life:cat", w: 0.34, h: 0.3, lift: c.h, glow: c.night ? 1 : 0, mirror: (c.x + c.y) % 2 === 1 }); if (shadow && c.h === 0) out.push({ x: c.x, y: c.y, dx: c.dx || 0, dz: c.dz || 0, layer: "shadow", flat: true, w: 0.26, alpha: 0.6 }); }
      C.roosts.forEach((ro, i) => { if (!near(ro.x, ro.z, 16)) return; const d = Math.abs(ro.x - px - 0.5) + Math.abs(ro.z - py - 0.5); let st = C.state.get(i);
        if (!st && d < 2.6) { st = { flewAt: t }; C.state.set(i, st); }
        if (st) { const a = t - st.flewAt;
          if (a < 2.5 && !CM.reducedMotion) { const away = Math.sign(ro.x - px - 0.5) || 1, awayZ = Math.sign(ro.z - py - 0.5) || 1, k = a / 2.5;   // up and away from the party, flapping
            out.push(at(ro.x + away * a * 1.1, ro.z + awayZ * a * 0.6, { layer: "life:pigeon:fly", w: 0.34 + 0.08 * Math.sin(t * 22), h: 0.2, lift: ro.y + a * 1.3, alpha: 1 - k * k, mirror: away < 0 })); return; }
          if (a < 28 || d < 2.6) { if (d < 2.6) st.flewAt = Math.min(st.flewAt, t - 2.5); return; }   // (gone a while; while the party stands near it keeps away)
          C.state.delete(i); }
        out.push(at(ro.x, ro.z, { layer: "life:pigeon", w: 0.2, h: 0.18, lift: ro.y, mirror: i % 2 === 0, dz: ro.z - Math.floor(ro.z) - 0.5 })); });
      return out; }; }
}
