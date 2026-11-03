"use strict";
// Glints (v49.3, UPGRADE_PLAN_44.md): metal, gold and gems catch the light as the party passes - a small star flashing
// on a chest's bands, a strongbox, a key, the coins in a vault, and in a fight on a foe in plate or crystal - each
// glint at its own angle, so it comes and goes as the eye moves or turns, the way a real one does. Not with reduced
// motion asked for.
{ const S = 128; let made = false;
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); if (set.index["gl:star"] !== undefined) return set; const c = document.createElement("canvas"); c.width = c.height = S; const p = c.getContext("2d");
      p.fillStyle = "#FFFFFF"; p.beginPath(); for (let i = 0; i < 8; i++) { const a = i * Math.PI / 4, r = i % 2 ? 10 : 60; p.lineTo(64 + Math.cos(a) * r, 64 + Math.sin(a) * r); } p.closePath(); p.fill(); p.beginPath(); p.arc(64, 64, 14, 0, Math.PI * 2); p.fill();
      set.index["gl:star"] = set.layers.length; set.layers.push(c); made = true; return set; }; }
  const KIND = { chest: [0.35, 0.3], strongbox: [0.3, 0.32], key: [0.15, 0.12], boxkey: [0.15, 0.12] };
  const twinkle = (eye, yaw, x, z, seed) => { const ph = Math.sin(seed * 12.9898) * 43758.5453, a = Math.sin(eye[0] * 2.7 + eye[2] * 3.1 + yaw * 5.0 + ph); return Math.pow(Math.max(0, a), 18); };
  { const ls0 = CM.lifeSprites; CM.lifeSprites = (game, fl, now) => { const out = ls0 ? ls0(game, fl, now) : []; const r = CM.renderer; if (!fl || !r || r.index["gl:star"] === undefined || CM.reducedMotion) return out;
      const eye = r.eye || [fl.pos[0] + 0.5, 0.5, fl.pos[1] + 0.5], yaw = r.yaw || 0, t = now / 1000, put = (x, y, dx, dz, lift, k, w) => { if (k < 0.05) return; out.push({ x, y, dx, dz, layer: "gl:star", w: w * (0.6 + 0.4 * k), h: w * (0.6 + 0.4 * k), lift, glow: 2, alpha: Math.min(1, k * 1.4) }); };
      if (game.mode === "explore") for (const [key, th] of Object.entries(fl.things)) { const K = KIND[th.type]; if (!K) continue; const [x, y] = key.split(",").map(Number); if (Math.abs(x - fl.pos[0]) + Math.abs(y - fl.pos[1]) > 7) continue;
        for (let i = 0; i < 2; i++) { const s = x * 31 + y * 17 + i * 7; put(x, y, Math.sin(s) * 0.18, Math.cos(s * 1.3) * 0.12, K[0] * (0.6 + 0.6 * ((s * 0.37) % 1)), twinkle(eye, yaw, x, y, s) + 0.25 * Math.pow(Math.max(0, Math.sin(t * 1.3 + s)), 30), K[1] * 0.85); } }
      if (game.mode === "combat" && CM.fxKit && CM.fxKit.atFoe) (game.foes || []).forEach((m, i) => { if (!(m.hp > 0)) return; const hide = CM.hideOf ? CM.hideOf(m) : ""; if (hide !== "plate" && hide !== "shell") return; const at = CM.fxKit.atFoe(m, 0); if (!at) return; const x = Math.floor(at[0]), y = Math.floor(at[2]);
        put(x, y, at[0] - x - 0.5 + Math.sin(i * 3) * 0.1, at[2] - y - 0.5, 0.45 + (i % 3) * 0.1, twinkle(eye, yaw + t * 0.4, x, y, i * 13 + 5), 0.16); });
      return out; }; }
  void made;
}
