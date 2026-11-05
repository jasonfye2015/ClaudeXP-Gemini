"use strict";
// The figures' reader (v65.0, UPGRADE_PLAN_60.md phase 0): parses the binary tools/models.py bakes into 35c-figures.js
// (CM.figuresPack: manifest, figures, data as deflated base64) into typed arrays, and poses a skeleton from a clip.
// No DOM, no WebGL here: the Node tests read it as the game does. Inflating is the caller's (the window inflates with
// DecompressionStream in 76zzzzzzzzzzd-figures.js; Node with zlib.inflateRawSync).
//   CM.Figures.parse(bytes, manifest) -> { models: { name: model }, clips: [clip] }
//     model: { verts, tris, box [lo, hi], textured, pos Int16Array(3n), uv Uint16Array(2n), col Uint8Array(3n),
//              joints Uint8Array(4n), weights Uint8Array(4n), index Uint16Array|Uint32Array, texture Uint8Array|null,
//              skeleton: { n, parent Int16Array, rest Float32Array(10n: t3 r4 s3), invBind Float32Array(16n) },
//              clips: { alias: clip } }
//     clip:  { frames, fps, joints, rot Int16Array(4*frames*joints), trans Float32Array(3*frames*joints) }
//   CM.Figures.pose(model, clip, t, out?) -> Float32Array(16n): each joint's skinning matrix (world * invBind) at t
//     seconds into the clip, looping; (model, null, 0) gives the rest pose
//   CM.Figures.figureOf(key) -> the mapping for "npc:x" / "pet:x" / "monster:Name" ({ model, scale, tint, wear }),
//     "painted", or null when unmapped
{ const half = (h) => { const s = (h & 0x8000) ? -1 : 1, e = (h >> 10) & 0x1f, f = h & 0x3ff;   // IEEE half to float
      return e === 0 ? s * f * Math.pow(2, -24) : e === 31 ? (f ? NaN : s * Infinity) : s * (1 + f / 1024) * Math.pow(2, e - 15); };
  const parseClip = (dv, o) => { const frames = dv.getUint16(o, true), fps = dv.getUint8(o + 2), joints = dv.getUint16(o + 3, true); o += 5;
      const rot = new Int16Array(frames * joints * 4), trans = new Float32Array(frames * joints * 3);
      for (let i = 0; i < frames * joints; i++) { for (let k = 0; k < 4; k++) rot[i * 4 + k] = dv.getInt16(o, true), o += 2; for (let k = 0; k < 3; k++) trans[i * 3 + k] = half(dv.getUint16(o, true)), o += 2; }
      return { frames, fps, joints, rot, trans, end: o }; };
  const parseModel = (bytes, dv, base, len, clipsTable, meta) => { let o = base; const verts = dv.getUint32(o, true), nIdx = dv.getUint32(o + 4, true); o += 8;
      const pos = new Int16Array(bytes.slice(o, o + verts * 6).buffer); o += verts * 6;   // (sliced: a copy, so the view is aligned whatever the offset)
      const uv = new Uint16Array(bytes.slice(o, o + verts * 4).buffer); o += verts * 4;
      const col = new Uint8Array(bytes.buffer, bytes.byteOffset + o, verts * 3); o += verts * 3;
      const joints = new Uint8Array(bytes.buffer, bytes.byteOffset + o, verts * 4); o += verts * 4;
      const weights = new Uint8Array(bytes.buffer, bytes.byteOffset + o, verts * 4); o += verts * 4;
      const big = verts > 65535, index = big ? new Uint32Array(bytes.slice(o, o + nIdx * 4).buffer) : new Uint16Array(bytes.slice(o, o + nIdx * 2).buffer); o += nIdx * (big ? 4 : 2);
      const n = dv.getUint32(o, true); o += 4; const parent = new Int16Array(n), rest = new Float32Array(n * 10), invBind = new Float32Array(n * 16);
      for (let k = 0; k < n; k++) { parent[k] = dv.getInt16(o, true); o += 2; for (let i = 0; i < 10; i++) rest[k * 10 + i] = dv.getFloat32(o, true), o += 4; for (let i = 0; i < 16; i++) invBind[k * 16 + i] = dv.getFloat32(o, true), o += 4; }
      const nClips = dv.getUint32(o, true); o += 4; const clips = {};
      for (let c = 0; c < nClips; c++) { const ln = dv.getUint8(o); o += 1; let name = ""; for (let i = 0; i < ln; i++) name += String.fromCharCode(bytes[o + i]); o += ln; clips[name] = clipsTable[dv.getUint32(o, true)]; o += 4; }
      const tl = dv.getUint32(o, true); o += 4; const texture = tl ? bytes.subarray(o, o + tl) : null; o += tl;
      if (o - base !== len) throw new Error(`figure ${meta && meta.pack}: read ${o - base} of ${len} bytes`);
      return { verts, tris: nIdx / 3, box: meta.box, textured: Boolean(texture), pos, uv, col, joints, weights, index, texture, skeleton: { n, parent, rest, invBind }, clips, scale: meta.scale || 1 }; };
  CM.Figures = {
    parse(bytes, manifest) { const dv = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength), T = manifest.clips, clips = [];
      let o = T.offset; const count = dv.getUint32(o, true); o += 4;
      for (let i = 0; i < count; i++) { const ln = dv.getUint32(o, true); o += 4; const c = parseClip(dv, o); if (c.end !== o + ln) throw new Error(`clip ${i}: ${c.end - o} of ${ln}`); delete c.end; clips.push(c); o += ln; }
      const models = {}; for (const [name, m] of Object.entries(manifest.models)) models[name] = parseModel(bytes, dv, m.offset, m.length, clips, m);
      return { models, clips }; },
    // the pose: local TRS from the clip (or the rest), chained up the parents, times the inverse bind
    pose(model, clip, t = 0, out = null) { const S = model.skeleton, n = S.n, M = out || new Float32Array(n * 16), W = new Float32Array(n * 16), q = [0, 0, 0, 1], tr = [0, 0, 0], L = new Float32Array(16);
      let fa = 0, fb = 0, k = 0; if (clip) { const T = clip.frames / clip.fps, tt = ((t % T) + T) % T, f = tt * clip.fps; fa = Math.min(clip.frames - 1, Math.floor(f)); fb = Math.min(clip.frames - 1, fa + 1); k = f - fa; }
      for (let j = 0; j < n; j++) { const r = S.rest.subarray(j * 10, j * 10 + 10);
        if (clip) { const a = (fa * clip.joints + j) * 4, b = (fb * clip.joints + j) * 4; let d = 0; for (let i = 0; i < 4; i++) d += clip.rot[a + i] * clip.rot[b + i]; const sg = d < 0 ? -1 : 1; let ln = 0;
          for (let i = 0; i < 4; i++) { q[i] = clip.rot[a + i] / 32767 + (sg * clip.rot[b + i] / 32767 - clip.rot[a + i] / 32767) * k; ln += q[i] * q[i]; } ln = Math.sqrt(ln) || 1; for (let i = 0; i < 4; i++) q[i] /= ln;
          const ta = (fa * clip.joints + j) * 3, tb = (fb * clip.joints + j) * 3; for (let i = 0; i < 3; i++) tr[i] = clip.trans[ta + i] + (clip.trans[tb + i] - clip.trans[ta + i]) * k; }
        else { for (let i = 0; i < 4; i++) q[i] = r[3 + i]; for (let i = 0; i < 3; i++) tr[i] = r[i]; }
        CM.Figures.trs(L, tr, q, r.subarray(7, 10)); const p = S.parent[j];
        if (p >= 0) CM.Figures.mul(W.subarray(j * 16, j * 16 + 16), W.subarray(p * 16, p * 16 + 16), L); else W.set(L, j * 16);
        CM.Figures.mul(M.subarray(j * 16, j * 16 + 16), W.subarray(j * 16, j * 16 + 16), S.invBind.subarray(j * 16, j * 16 + 16)); }
      return M; },
    trs(m, t, q, s) { const [x, y, z, w] = q, xx = x * x, yy = y * y, zz = z * z, xy = x * y, xz = x * z, yz = y * z, wx = w * x, wy = w * y, wz = w * z;
      m[0] = (1 - 2 * (yy + zz)) * s[0]; m[1] = 2 * (xy + wz) * s[0]; m[2] = 2 * (xz - wy) * s[0]; m[3] = 0;
      m[4] = 2 * (xy - wz) * s[1]; m[5] = (1 - 2 * (xx + zz)) * s[1]; m[6] = 2 * (yz + wx) * s[1]; m[7] = 0;
      m[8] = 2 * (xz + wy) * s[2]; m[9] = 2 * (yz - wx) * s[2]; m[10] = (1 - 2 * (xx + yy)) * s[2]; m[11] = 0; m[12] = t[0]; m[13] = t[1]; m[14] = t[2]; m[15] = 1; return m; },
    mul(out, a, b) { for (let c = 0; c < 4; c++) for (let r = 0; r < 4; r++) { let s = 0; for (let k = 0; k < 4; k++) s += a[k * 4 + r] * b[c * 4 + k]; out[c * 4 + r] = s; } return out; },
    // a vertex of the model skinned by the pose, in model units (for the tests, and the impostors)
    skinVertex(model, M, i, out = [0, 0, 0]) { const lo = model.box[0], hi = model.box[1], P = model.pos, v = [0, 1, 2].map((k) => lo[k] + (P[i * 3 + k] + 32767) / 65534 * (hi[k] - lo[k])); out[0] = out[1] = out[2] = 0;
      for (let k = 0; k < 4; k++) { const w = model.weights[i * 4 + k] / 255; if (!w) continue; const m = model.joints[i * 4 + k] * 16; for (let r = 0; r < 3; r++) out[r] += w * (M[m + r] * v[0] + M[m + 4 + r] * v[1] + M[m + 8 + r] * v[2] + M[m + 12 + r]); }
      return out; },
    figureOf(key) { const F = CM.figuresPack && CM.figuresPack.figures; if (!F || !(key in F)) return null; return F[key]; },
    // (v66.0) the figure behind a sprite's layer: "monster:Goblin:idle2" -> "monster:Goblin", "npc:res_smith" -> itself; else null
    keyOf(layer) { if (typeof layer !== "string") return null; const p = layer.split(":"); if (p.length < 2 || !["monster", "npc", "pet"].includes(p[0])) return null; return `${p[0]}:${p[1]}`; },
    // the model's size at rest, posed (the stored box is the raw mesh's: Quaternius' is tiny before its armature's scale): { lo, hi, height, foot }
    measure(model) { if (model.measured) return model.measured; const M = CM.Figures.pose(model, null, 0), lo = [1e9, 1e9, 1e9], hi = [-1e9, -1e9, -1e9], v = [0, 0, 0], step = model.verts > 3000 ? 2 : 1;
      for (let i = 0; i < model.verts; i += step) { CM.Figures.skinVertex(model, M, i, v); for (let k = 0; k < 3; k++) { if (v[k] < lo[k]) lo[k] = v[k]; if (v[k] > hi[k]) hi[k] = v[k]; } }
      return (model.measured = { lo, hi, height: Math.max(1e-3, hi[1] - lo[1]), width: Math.max(1e-3, hi[0] - lo[0], hi[2] - lo[2]), foot: lo[1], centre: [(lo[0] + hi[0]) / 2, (lo[2] + hi[2]) / 2] }); },
    // the uniform scale that stands a model within its billboard - its height (in squares) and its width, whichever binds: a rat is long, not tall - times the figure's own scale
    fit(figure, model, spriteH, spriteW) { const m = CM.Figures.measure(model), k = (figure && figure.scale) || 1; return Math.min((spriteH || 0.8) * k / m.height, (spriteW || spriteH || 0.8) * k / m.width); },
    // a palette for an untextured model: its colours as cells of a square grid, and the uv of each vertex at its cell's centre
    palette(model) { const cols = [], at = new Map(), uv = new Float32Array(model.verts * 2); for (let i = 0; i < model.verts; i++) { const k = (model.col[i * 3] << 16) | (model.col[i * 3 + 1] << 8) | model.col[i * 3 + 2]; let c = at.get(k);
        if (c === undefined) { c = cols.length; cols.push([model.col[i * 3], model.col[i * 3 + 1], model.col[i * 3 + 2]]); at.set(k, c); } uv[i * 2] = c; }
      const n = Math.max(1, Math.ceil(Math.sqrt(cols.length))); for (let i = 0; i < model.verts; i++) { const c = uv[i * 2]; uv[i * 2] = ((c % n) + 0.5) / n; uv[i * 2 + 1] = (Math.floor(c / n) + 0.5) / n; }
      return { colours: cols, n, uv }; },
    // (v67.0) the clip player: what a figure plays now, from its cues. st is the figure's own state (an empty object to
    // begin with); cues: { moving, attack (true while the strike's pose holds), attackClip ("attack" or "cast"), hit (this
    // frame), dead, speed }; now in seconds. Returns { clip, t, from, fromT, k }: the clip and the time into it, and while a
    // change blends (BLEND seconds), the clip it came from, the time it was at, and how far the blend has gone (k 0..1).
    // A strike, a hit and a death play once; a death holds its last frame; walking and idling loop at the figure's speed.
    step(model, st, cues, now) { const C = model.clips, has = (n) => Boolean(C[n]), len = (n) => C[n].frames / C[n].fps, BLEND = 0.15, speed = cues.speed || 1;
      const timeIn = () => (st.clip ? (now - st.since) * (st.once ? 1 : speed) : 0);
      const start = (n, once) => { if (!has(n) || n === st.clip) return; st.from = st.clip; st.fromT = Math.min(timeIn(), st.clip && st.once ? len(st.clip) - 1e-3 : timeIn()); st.clip = n; st.since = now; st.once = once; st.done = false; };
      const done = () => st.clip && st.once && (now - st.since) >= len(st.clip);
      if (cues.dead) { if (st.clip !== "die") { if (has("die")) start("die", true); else if (!st.clip) start("idle", false); } }
      else if (cues.hit && st.clip !== "hit" && !st.hitHeld && has("hit")) { start("hit", true); st.hitHeld = true; }
      else { if (!cues.hit) st.hitHeld = false;
        const atk = cues.attackClip && has(cues.attackClip) ? cues.attackClip : "attack";
        if (cues.attack && !st.attackHeld && has(atk)) { start(atk, true); st.attackHeld = true; } else if (!cues.attack) st.attackHeld = false;
        const rest = cues.act && has(cues.act) ? cues.act : "idle";   // (v68.0: standing at work - the forge, a stall - or sitting, the loop is that instead of the idle)
        if (!st.clip || (st.once && done()) || (!st.once && st.clip !== (cues.moving ? "walk" : rest))) { if (!(st.once && !done())) start(cues.moving && has("walk") ? "walk" : rest, false); } }
      if (!st.clip) return null;
      const L = len(st.clip); let t = timeIn(); if (st.once && t >= L) t = L - 1e-3;
      const k = st.from && (now - st.since) < BLEND ? (now - st.since) / BLEND : 1; if (k >= 1) st.from = null;
      return { clip: st.clip, t, from: st.from, fromT: st.fromT || 0, k }; },
    // (v69.0) the gear a foe carries, as the model to put in its hand, from the weapon's name: a sword, an axe, a knife, a staff, a crossbow - or none
    gearFor(name) { const n = String(name || "").toLowerCase(); if (!n) return null;
      if (/great ?sword|claymore|two-hand/.test(n)) return "greatsword"; if (/great ?axe|battle ?axe/.test(n)) return "greataxe"; if (/sword|blade|sabre|rapier|scimitar/.test(n)) return "sword";
      if (/axe|hatchet|cleaver/.test(n)) return "axe"; if (/dagger|knife|dirk|shiv/.test(n)) return "knife"; if (/staff|rod|wand/.test(n)) return "staff"; if (/bow|crossbow/.test(n)) return "crossbow"; return null; },
    // the model matrix: scaled, turned about y by yaw, then stood at (x, y, z); column-major
    modelMatrix(out, x, y, z, yaw, s) { const c = Math.cos(yaw) * s, sn = Math.sin(yaw) * s; out[0] = c; out[1] = 0; out[2] = -sn; out[3] = 0; out[4] = 0; out[5] = s; out[6] = 0; out[7] = 0; out[8] = sn; out[9] = 0; out[10] = c; out[11] = 0; out[12] = x; out[13] = y; out[14] = z; out[15] = 1; return out; },
  };
}
