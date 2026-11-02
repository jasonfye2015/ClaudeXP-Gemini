"use strict";
// Monsters closer up (v39.0, UPGRADE_PLAN_34.md): every monster picture gets a detail pass over what 30-art.js paints -
// fur strokes on beasts, scales on the scaled, rivets and plate seams on the armoured and the wide, rag folds on the dead,
// a rim of torchlight down its right side and a soft shadow in its folds, and a dark ink line round it - and a painted
// recoil frame (":hurt": thrown back, eyes screwed shut) shown in the instant it is struck (the hit's flash).
{ const scaled = /Wyvern|Wyrm|Eel|Drake|Dragon|Lizard|Serpent/, armoured = /Knight|Golem|Sentinel|Colossus|Iron|Gargoyle|Sellsword|Marshal|Warden/;
  const detail = (c, m) => { const p = c.getContext("2d"), S = c.width; let d; try { d = p.getImageData(0, 0, S, S); } catch (e) { return c; } const A = d.data, solid = (x, y) => x >= 0 && y >= 0 && x < S && y < S && A[(y * S + x) * 4 + 3] > 128;
    let x0 = S, x1 = 0, y0 = S, y1 = 0; for (let y = 0; y < S; y += 2) for (let x = 0; x < S; x += 2) if (solid(x, y)) { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; } if (x1 <= x0) return c;
    const r = new CM.Random(CM.hashSeed(`detail:${m.name}`)), w = x1 - x0, h = y1 - y0;
    p.save(); p.globalCompositeOperation = "source-atop";
    if (m.body === "beast" || /Wolf|Bear|Rat|Hound|Boar/.test(m.name)) { p.strokeStyle = "rgba(0,0,0,0.22)"; p.lineWidth = 1.5; for (let i = 0; i < 260; i++) { const x = x0 + r.next() * w, y = y0 + r.next() * h; p.beginPath(); p.moveTo(x, y); p.lineTo(x + 3 + r.next() * 3, y + 5 + r.next() * 4); p.stroke(); }
      p.strokeStyle = "rgba(255,255,255,0.12)"; for (let i = 0; i < 120; i++) { const x = x0 + r.next() * w, y = y0 + r.next() * h * 0.6; p.beginPath(); p.moveTo(x, y); p.lineTo(x + 2, y + 5); p.stroke(); } }
    if (scaled.test(m.name)) { p.strokeStyle = "rgba(0,0,0,0.25)"; p.lineWidth = 1.2; for (let y = y0; y < y1; y += 7) for (let x = x0 + ((y / 7) % 2) * 4; x < x1; x += 8) { p.beginPath(); p.arc(x, y, 4, 0, Math.PI); p.stroke(); } }
    if (armoured.test(m.name) || m.body === "wide") { p.fillStyle = "rgba(255,255,230,0.35)"; for (let i = 0; i < 26; i++) { p.beginPath(); p.arc(x0 + r.next() * w, y0 + h * 0.2 + r.next() * h * 0.7, 1.6, 0, Math.PI * 2); p.fill(); }
      p.strokeStyle = "rgba(0,0,0,0.25)"; p.lineWidth = 2; for (let i = 0; i < 4; i++) { const y = y0 + h * (0.35 + i * 0.13); p.beginPath(); p.moveTo(x0, y); p.quadraticCurveTo(x0 + w / 2, y + 5, x1, y); p.stroke(); } }
    if (m.undead) { p.strokeStyle = "rgba(20,20,10,0.3)"; p.lineWidth = 2; for (let i = 0; i < 16; i++) { const x = x0 + r.next() * w, y = y0 + h * 0.4 + r.next() * h * 0.55; p.beginPath(); p.moveTo(x, y); p.quadraticCurveTo(x + 4, y + 8, x - 2, y + 16); p.stroke(); } }
    const rim = p.createLinearGradient(x0, 0, x1, 0); rim.addColorStop(0, "rgba(0,0,0,0.22)"); rim.addColorStop(0.55, "rgba(0,0,0,0)"); rim.addColorStop(0.85, "rgba(255,210,150,0)"); rim.addColorStop(1, "rgba(255,210,150,0.35)"); p.fillStyle = rim; p.fillRect(x0, y0, w + 1, h + 1);
    const ao = p.createLinearGradient(0, y0, 0, y1); ao.addColorStop(0, "rgba(255,255,255,0.06)"); ao.addColorStop(0.7, "rgba(0,0,0,0)"); ao.addColorStop(1, "rgba(0,0,0,0.25)"); p.fillStyle = ao; p.fillRect(x0, y0, w + 1, h + 1);
    p.restore();
    const mk = document.createElement("canvas"); mk.width = mk.height = S; const mp = mk.getContext("2d"), md = mp.createImageData(S, S);   /* (v42.0: the ink line from the solid shape only - a soft aura or shadow in the picture stamped dark came out a black blot) */
    for (let i = 0; i < A.length; i += 4) { md.data[i] = 10; md.data[i + 1] = 6; md.data[i + 2] = 4; md.data[i + 3] = A[i + 3] > 128 ? 230 : 0; } mp.putImageData(md, 0, 0);
    p.save(); p.globalCompositeOperation = "destination-over";
    for (const [dx, dy] of [[-1.5, 0], [1.5, 0], [0, -1.5], [0, 1.5]]) p.drawImage(mk, dx, dy);   /* (the ink line: the shape, stamped dark a pixel and a half each way behind itself) */
    p.restore(); return c; };
  const m0 = CM.art.monster; CM.art.monster = function (m, big, pose) {
    if (pose === "hurt") { const c = m0.call(this, m, big, "idle"), S = c.width, o = document.createElement("canvas"); o.width = o.height = S; const p = o.getContext("2d"); p.translate(S / 2, S - 14); p.transform(0.96, 0, -0.16, 0.98, 0, -2); p.rotate(-0.06); p.translate(-S / 2, -(S - 14)); p.drawImage(c, 0, 0);
      p.setTransform(1, 0, 0, 1, 0, 0); p.globalCompositeOperation = "source-atop"; p.fillStyle = "rgba(255,240,230,0.25)"; p.fillRect(0, 0, S, S); return detail(o, m); }
    return detail(m0.call(this, m, big, pose), m); };
  // the recoil frame, for every kind (the drawn pictures; a pack's look keeps its own)
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); if (set.index[`monster:${CM.MONSTERS[0].name}:hurt`] !== undefined) return set;
      for (const m of CM.MONSTERS) if (set.index[`monster:${m.name}`] !== undefined) { set.index[`monster:${m.name}:hurt`] = set.layers.length; set.layers.push(CM.art.monster(m, false, "hurt")); } return set; }; }
  // in the instant of a hit (its flash), the recoil frame
  CM.hurtFrames = true;
  const prep = (r) => { const ss0 = r.setSprites; r.setSprites = function (list) { if (CM.hurtFrames && !CM.reducedMotion) for (const s of list) if (s.flash > 0.25 && typeof s.layer === "string" && s.layer.startsWith("monster:") && !/:attack|:hurt/.test(s.layer)) { const base = s.layer.replace(/:idle2$/, ""); if (this.index[`${base}:hurt`] !== undefined) s.layer = `${base}:hurt`; } return ss0.call(this, list); }; r.hurtWrapped = true; };
  if (typeof self !== "undefined" && self.CM_WORKER) { /* (the art worker: no renderer) */ } else { const t = setInterval(() => { if (CM.renderer && !CM.renderer.hurtWrapped) { prep(CM.renderer); clearInterval(t); } }, 200); }
}
