"use strict";
// Things that break, the window's side (v27.1): the crates, barrels and urns as they stand, a brazier burning on its
// tripod (or on its side), the burning floor - coals and flames, and their light - and a burst of splinters when one
// breaks. The rules are 69w-breakables.js.
{ const S = 256, cv = () => { const c = document.createElement("canvas"); c.width = c.height = S; return c; };
  const PAINT = {
    urn: (p) => { p.fillStyle = "rgba(0,0,0,0.3)"; p.beginPath(); p.ellipse(128, 246, 60, 10, 0, 0, Math.PI * 2); p.fill(); const g = p.createLinearGradient(70, 0, 186, 0); g.addColorStop(0, "#6A4A30"); g.addColorStop(0.45, "#B07A4A"); g.addColorStop(1, "#5A3A24"); p.fillStyle = g;
      p.beginPath(); p.moveTo(104, 70); p.quadraticCurveTo(60, 120, 80, 200); p.quadraticCurveTo(96, 244, 128, 244); p.quadraticCurveTo(160, 244, 176, 200); p.quadraticCurveTo(196, 120, 152, 70); p.closePath(); p.fill();
      p.fillStyle = "#4A3020"; p.fillRect(100, 56, 56, 16); p.strokeStyle = "rgba(40,24,12,0.6)"; p.lineWidth = 4; for (const y of [120, 170]) { p.beginPath(); p.moveTo(76, y); p.quadraticCurveTo(128, y + 12, 180, y); p.stroke(); } },
    brazier: (p, lit) => { p.fillStyle = "rgba(0,0,0,0.3)"; p.beginPath(); p.ellipse(128, 246, 70, 10, 0, 0, Math.PI * 2); p.fill(); p.strokeStyle = "#2E2A28"; p.lineWidth = 9;
      if (lit) { for (const [x0, x1] of [[90, 108], [166, 148], [128, 128]]) { p.beginPath(); p.moveTo(x0, 244); p.lineTo(x1, 150); p.stroke(); } p.fillStyle = "#3A3430"; p.beginPath(); p.moveTo(64, 130); p.lineTo(192, 130); p.lineTo(170, 168); p.lineTo(86, 168); p.closePath(); p.fill();
        const g = p.createRadialGradient(128, 110, 4, 128, 110, 70); g.addColorStop(0, "#FFF2A0"); g.addColorStop(0.35, "#FFA030"); g.addColorStop(0.75, "rgba(220,70,20,0.85)"); g.addColorStop(1, "rgba(160,30,10,0)"); p.fillStyle = g;
        p.beginPath(); p.moveTo(70, 132); p.quadraticCurveTo(90, 60, 112, 90); p.quadraticCurveTo(128, 20, 146, 86); p.quadraticCurveTo(170, 56, 186, 132); p.closePath(); p.fill(); }
      else { p.save(); p.translate(128, 210); p.rotate(1.25); p.fillStyle = "#3A3430"; p.beginPath(); p.moveTo(-64, -40); p.lineTo(64, -40); p.lineTo(42, 0); p.lineTo(-42, 0); p.closePath(); p.fill(); p.restore(); p.lineWidth = 9; p.beginPath(); p.moveTo(40, 240); p.lineTo(150, 210); p.stroke();
        for (let i = 0; i < 18; i++) { p.fillStyle = i % 3 ? "#C8401A" : "#FFB040"; p.beginPath(); p.arc(150 + Math.cos(i * 2.4) * (20 + i * 3), 236 + Math.sin(i * 1.7) * 6, 4 + (i % 3), 0, Math.PI * 2); p.fill(); } } },
  };
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look), add = (n, f) => { const c = cv(); f(c.getContext("2d")); set.index[n] = set.layers.length; set.layers.push(c); };
      add("brk:urn", (p) => PAINT.urn(p)); add("brazier", (p) => PAINT.brazier(p, true)); add("brazier_down", (p) => PAINT.brazier(p, false)); return set; }; }
  const has = (L) => CM.renderer && CM.renderer.index && CM.renderer.index[L] !== undefined;
  CM.thingSprites = Object.assign(CM.thingSprites || {}, {
    breakable: (t, x, y) => { const L = t.kind === "urn" ? "brk:urn" : has(`prop:${t.kind}`) ? `prop:${t.kind}` : "chest", dx = ((x * 37 + y * 11) % 30 - 15) / 100, dz = ((x * 13 + y * 29) % 30 - 15) / 100;
      return [{ x, y, dx, dz, layer: L, w: t.kind === "barrel" ? 0.42 : t.kind === "urn" ? 0.4 : 0.46, h: t.kind === "barrel" ? 0.55 : t.kind === "urn" ? 0.45 : 0.44 }]; },
    brazier: (t, x, y, now) => [{ x, y, layer: t.lit ? "brazier" : "brazier_down", w: 0.7, h: 0.75, glow: t.lit ? 0.35 + 0.1 * Math.sin(now / 90 + x) : 0.15 }],
  });
  // the burning floor: coals lying flat, flames standing, flickering, and their light
  { const ls0 = CM.lifeSprites; CM.lifeSprites = (game, fl, now) => { const out = ls0 ? ls0(game, fl, now) : []; const B = fl && fl.burning; if (!B || !game.burningAt) return out;
      if ((game.clock || 0) >= B.until) return out; const left = Math.min(1, (B.until - (game.clock || 0)) / 10);
      for (const k of B.cells) { const [x, y] = k.split(",").map(Number), ph = (x * 7 + y * 3) % 10;
        out.push({ x, y, flat: true, w: 0.95, layer: "fx:fire", alpha: 0.55 * left, glow: 1 });
        for (let i = 0; i < 2; i++) out.push({ x, y, dx: (i ? 0.2 : -0.18), dz: (i ? -0.15 : 0.12), layer: "fx:fire", w: 0.32 * left, h: (0.4 + 0.12 * Math.sin(now / 120 + ph + i)) * left, glow: 1, alpha: 0.9 }); }
      return out; }; }
  { const xl0 = CM.extraLights; CM.extraLights = (game, fl, out, renderer) => { if (xl0) xl0(game, fl, out, renderer); if (!fl) return;
      for (const [k, t] of Object.entries(fl.things)) if (t.type === "brazier" && t.lit) { const [x, y] = k.split(",").map(Number); if (Math.abs(x - fl.pos[0]) + Math.abs(y - fl.pos[1]) <= 10) out.push({ x: x + 0.5, y: 0.7, z: y + 0.5, reach: 3.4, colour: [1.0, 0.55, 0.2], flicker: true, d: Math.abs(x - fl.pos[0]) + Math.abs(y - fl.pos[1]) }); }
      const B = fl.burning; if (B && (game.clock || 0) < B.until) { const [x, y] = B.cells[Math.floor(B.cells.length / 2)].split(",").map(Number); out.push({ x: x + 0.5, y: 0.3, z: y + 0.5, reach: 4.0, colour: [1.0, 0.5, 0.15], flicker: true, d: 0 }); } }; }
  // a crate's splinters, a brazier's coals scattered
  { const bind = CM.UI.prototype.refresh; CM.UI.prototype.refresh = function (...a) { if (!this.brkBound && this.game && this.game.on && CM.fxKit) { this.brkBound = true; this.game.on("fx", (e) => { const K = CM.fxKit; if (!e || !K || !K.renderer || !K.renderer.ok || !e.at) return;
        const at = [e.at[0] + 0.5, 0.25, e.at[1] + 0.5];
        if (e.kind === "smash") { K.fxs.burst({ at, layer: "fx:shard", n: 14, size: 0.06, speed: 1.4, up: 1.6, ms: 600 }); K.renderer.shake(0.15); }
        if (e.kind === "brazier") { K.fxs.burst({ at, layer: "fx:fire", n: 22, size: 0.08, speed: 1.8, up: 1.4, ms: 800 }); K.fxs.ring({ at: [at[0], 0, at[2]], to: 2.6, ms: 600 }); K.ui.tint("rgba(255,120,30,0.35)", 400); if (CM.lightFlare) CM.lightFlare(K.renderer, "fireball", e.at); } }); }
      return bind.apply(this, a); }; }
}
