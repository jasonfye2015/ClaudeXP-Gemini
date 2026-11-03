"use strict";
// Seen from three sides (v50.0, UPGRADE_PLAN_45.md): a monster seen from behind is its back now - no face, no eyes, no
// teeth, the head and shoulders in its own body's colour, turned away - and from the side it is lit along its leading
// edge and falls into shadow behind (76zzzzv-facing.js says which side the party sees; it no longer only darkens the
// front's picture). Made from each kind's drawn picture when the set is built.
{ const sideOf = (src, back) => { const S = src.width, c = document.createElement("canvas"); c.width = c.height = S; const p = c.getContext("2d"); if (back) { p.translate(S, 0); p.scale(-1, 1); } p.drawImage(src, 0, 0); p.setTransform(1, 0, 0, 1, 0, 0);
    let d; try { d = p.getImageData(0, 0, S, S); } catch (e) { return c; } const A = d.data; let x0 = S, x1 = 0, y0 = S, y1 = 0;
    for (let y = 0; y < S; y++) for (let x = 0; x < S; x++) if (A[(y * S + x) * 4 + 3] > 128) { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; } if (x1 <= x0) return c;
    if (back) { const top = y0 + (y1 - y0) * 0.5; let r = 0, g = 0, b = 0, n = 0;   // the body's own colour: the ordinary pixels of the upper half
      for (let y = y0; y < top; y++) for (let x = x0; x <= x1; x++) { const i = (y * S + x) * 4; if (A[i + 3] < 128) continue; const l = (A[i] * 0.3 + A[i + 1] * 0.59 + A[i + 2] * 0.11) / 255; if (l > 0.12 && l < 0.6) { r += A[i]; g += A[i + 1]; b += A[i + 2]; n++; } }
      if (n) { r /= n; g /= n; b /= n; for (let y = y0; y < top; y++) for (let x = x0; x <= x1; x++) { const i = (y * S + x) * 4; if (A[i + 3] < 128) continue; const l = (A[i] * 0.3 + A[i + 1] * 0.59 + A[i + 2] * 0.11) / 255, mx = Math.max(A[i], A[i + 1], A[i + 2]), mn = Math.min(A[i], A[i + 1], A[i + 2]);
          if (l > 0.55 || (mx - mn > 90 && l > 0.35)) { A[i] = r * 0.9; A[i + 1] = g * 0.9; A[i + 2] = b * 0.9; } }
        const hy0 = y0, hy1 = y0 + (y1 - y0) * 0.38;   // (the head from behind: its middle filled in the body's colour, the edge kept - no brows, no mouth, no lines of a face)
        for (let y = Math.floor(hy0); y < hy1; y++) { let a0 = -1, a1 = -1; for (let x = x0; x <= x1; x++) if (A[(y * S + x) * 4 + 3] > 128) { if (a0 < 0) a0 = x; a1 = x; } if (a0 < 0) continue; const m = Math.max(2, Math.round((a1 - a0) * 0.12));
          for (let x = a0 + m; x <= a1 - m; x++) { const i = (y * S + x) * 4; if (A[i + 3] < 128) continue; const sh = 0.82 + 0.18 * (1 - Math.abs((x - (a0 + a1) / 2) / ((a1 - a0) / 2 + 1))); A[i] = r * sh; A[i + 1] = g * sh; A[i + 2] = b * sh; } } }   // (the face gone)
      for (let i = 0; i < A.length; i += 4) { A[i] *= 0.82; A[i + 1] *= 0.82; A[i + 2] *= 0.82; } }
    else for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) { const i = (y * S + x) * 4; if (A[i + 3] < 128) continue; const k = 1.15 - 0.55 * (x - x0) / Math.max(1, x1 - x0); A[i] = Math.min(255, A[i] * k); A[i + 1] = Math.min(255, A[i + 1] * k); A[i + 2] = Math.min(255, A[i + 2] * k); }   // (lit along the leading edge)
    p.putImageData(d, 0, 0); return c; };
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); if (!CM.MONSTERS || set.index[`monster:${CM.MONSTERS[0].name}:back`] !== undefined) return set;
      for (const m of CM.MONSTERS) { const at = set.index[`monster:${m.name}`]; if (at === undefined) continue; const src = set.layers[at]; if (!src || !src.getContext) continue;
        set.index[`monster:${m.name}:back`] = set.layers.length; set.layers.push(sideOf(src, true)); set.index[`monster:${m.name}:side`] = set.layers.length; set.layers.push(sideOf(src, false)); }
      return set; }; }
  const prep = (r) => { const ss0 = r.setSprites; r.setSprites = function (list) { for (const s of list) { if ((s.view !== "back" && s.view !== "side") || typeof s.layer !== "string" || !s.layer.startsWith("monster:") || /:attack|:hurt/.test(s.layer)) continue;
        const base = s.layer.replace(/:idle2$/, ""), L = `${base}:${s.view}`; if (this.index[L] !== undefined) { s.layer = L; if (s.view === "back") { s.view = "backdrawn"; s.mirror = false; } } }
      return ss0.call(this, list); }; r.sidesWrapped = true; };
  const t = typeof self !== "undefined" && self.CM_WORKER ? null : setInterval(() => { if (CM.renderer && !CM.renderer.sidesWrapped) { prep(CM.renderer); clearInterval(t); } }, 150);
}
