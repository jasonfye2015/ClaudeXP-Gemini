"use strict";
// Wear (v50.2, UPGRADE_PLAN_45.md): a monster shows what the fight has done to it - below two-thirds of its life it is
// marked (cracks across plate and shell and bone, rents in hide, cuts in flesh, by what it is made of), and below a
// third it is badly so (more of them, deeper, and a darkening as of blood or soot), painted over its own picture where
// the picture is. Only its plain pictures take it (not the lunge or the recoil, which are quick).
{ const S = 128;
  const wear = (src, kind, deep) => { const c = document.createElement("canvas"); c.width = c.height = S; const p = c.getContext("2d"); p.drawImage(src, 0, 0, S, S); let d; try { d = p.getImageData(0, 0, S, S); } catch (e) { return c; }
    const A = d.data; let x0 = S, x1 = 0, y0 = S, y1 = 0; for (let y = 0; y < S; y++) for (let x = 0; x < S; x++) if (A[(y * S + x) * 4 + 3] > 128) { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; } if (x1 <= x0) return c;
    const r = new CM.Random(CM.hashSeed(`wear:${src.width}:${x0},${y0}:${kind}:${deep}`)), w = x1 - x0, h = y1 - y0;
    p.save(); p.globalCompositeOperation = "source-atop"; const n = deep ? 9 : 4;
    for (let i = 0; i < n; i++) { const x = x0 + w * (0.15 + 0.7 * r.next()), y = y0 + h * (0.2 + 0.65 * r.next());
      if (kind === "plate" || kind === "shell" || kind === "bone") { p.strokeStyle = "rgba(15,10,8,0.85)"; p.lineWidth = deep ? 2 : 1.5; p.beginPath(); p.moveTo(x, y); let cx = x, cy = y; for (let k = 0; k < 4; k++) { cx += (r.next() - 0.5) * 14; cy += 3 + r.next() * 7; p.lineTo(cx, cy); } p.stroke();
        p.strokeStyle = "rgba(255,255,255,0.25)"; p.lineWidth = 1; p.beginPath(); p.moveTo(x + 1, y); p.lineTo(x + 4, y + 6); p.stroke(); }
      else if (kind === "hide") { p.fillStyle = "rgba(60,20,15,0.85)"; p.beginPath(); p.ellipse(x, y, 2.5 + r.next() * 3, 7 + r.next() * 6, (r.next() - 0.5) * 1.4, 0, Math.PI * 2); p.fill(); p.fillStyle = "rgba(150,40,30,0.7)"; p.beginPath(); p.ellipse(x, y, 1.2, 5, 0.3, 0, Math.PI * 2); p.fill(); }
      else if (kind !== "none") { p.strokeStyle = "rgba(120,15,15,0.9)"; p.lineWidth = deep ? 2.5 : 2; p.beginPath(); p.moveTo(x - 6, y - 3); p.lineTo(x + 6, y + 3); p.stroke(); if (deep) { p.fillStyle = "rgba(110,10,10,0.7)"; p.fillRect(x - 1, y + 2, 2, 6 + r.next() * 8); } } }
    if (deep) { p.fillStyle = kind === "none" ? "rgba(200,220,255,0.15)" : "rgba(40,10,5,0.22)"; p.fillRect(0, 0, S, S); }
    p.restore(); return c; };
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); if (!CM.MONSTERS || set.index[`monster:${CM.MONSTERS[0].name}:worn1`] !== undefined) return set;
      for (const m of CM.MONSTERS) { const at = set.index[`monster:${m.name}`], src = at !== undefined && set.layers[at]; if (!src || !src.getContext) continue; const kind = CM.hideOf ? CM.hideOf(m) : "flesh";
        for (const lv of [1, 2]) { set.index[`monster:${m.name}:worn${lv}`] = set.layers.length; set.layers.push(wear(src, kind, lv === 2)); } }
      return set; }; }
  const prep = (r) => { const ss0 = r.setSprites; r.setSprites = function (list) { const g = CM.game; if (g && g.mode === "combat") { const L = (g.foes || []).filter((m) => m.hp > 0);
        for (const s of list) { if (typeof s.layer !== "string" || !/^monster:[^:]+(:idle2)?$/.test(s.layer)) continue; const name = s.layer.split(":")[1], m = L.find((f) => (f.kind || f.name) === name || f.name === name); if (!m || !m.max) continue;
          const k = m.hp / m.max, lv = k < 1 / 3 ? 2 : k < 2 / 3 ? 1 : 0; if (lv && this.index[`monster:${name}:worn${lv}`] !== undefined) s.layer = `monster:${name}:worn${lv}`; } }
      return ss0.call(this, list); }; r.wearWrapped = true; };
  const t = typeof self !== "undefined" && self.CM_WORKER ? null : setInterval(() => { if (CM.renderer && !CM.renderer.wearWrapped) { prep(CM.renderer); clearInterval(t); } }, 150);
}
