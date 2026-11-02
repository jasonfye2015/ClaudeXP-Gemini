"use strict";
// Status seen (v39.3, UPGRADE_PLAN_34.md): what ails a monster shows on it in a fight - bleeding or poisoned, a green
// tinge and drips falling; asleep, Zs drifting up; held, vines round its legs; blinded, a dark band and it sways
// groping; chilled, frost creeping up it; burning, flames licking; marked, a red sigil over it. Drawn at the monster's
// place in the fight (CM.fxKit.atFoe), each frame.
{ const S = 128, cv = () => { const c = document.createElement("canvas"); c.width = c.height = S; return c; };
  const PAINT = {
    "st:drip": (p) => { p.fillStyle = "#6AD040"; p.beginPath(); p.moveTo(64, 10); p.quadraticCurveTo(100, 80, 64, 118); p.quadraticCurveTo(28, 80, 64, 10); p.fill(); },
    "st:z": (p) => { p.fillStyle = "#D8E8FF"; p.font = "bold 96px Georgia"; p.textAlign = "center"; p.fillText("z", 64, 100); },
    "st:vines": (p) => { p.strokeStyle = "#3A7A2A"; p.lineWidth = 9; p.lineCap = "round"; for (let i = 0; i < 4; i++) { p.beginPath(); p.moveTo(10 + i * 30, 128); p.bezierCurveTo(40 + i * 10, 90, 0 + i * 30, 60, 60 + i * 15, 20); p.stroke(); } p.fillStyle = "#5AA03A"; for (let i = 0; i < 10; i++) { p.beginPath(); p.ellipse(20 + i * 10, 30 + (i % 4) * 22, 8, 4, i, 0, Math.PI * 2); p.fill(); } },
    "st:blind": (p) => { p.fillStyle = "rgba(20,15,10,0.9)"; p.fillRect(0, 48, 128, 32); p.fillStyle = "rgba(60,50,40,0.9)"; p.fillRect(0, 50, 128, 4); },
    "st:frost": (p) => { p.fillStyle = "#D8EEFF"; p.strokeStyle = "#7AB0E0"; p.lineWidth = 2; for (let i = 0; i < 9; i++) { const x = 8 + i * 14, h = 30 + ((i * 37) % 50); p.beginPath(); p.moveTo(x - 7, 128); p.lineTo(x, 128 - h); p.lineTo(x + 7, 128); p.closePath(); p.fill(); p.stroke(); } },
    "st:flame": (p) => { for (const [c, k] of [["#E8401A", 1], ["#FF9A2A", 0.7], ["#FFF0A0", 0.4]]) { p.fillStyle = c; for (let i = 0; i < 3; i++) { const x = 30 + i * 34, h = 110 * k * (0.8 + (i % 2) * 0.3); p.beginPath(); p.moveTo(x - 18 * k, 128); p.quadraticCurveTo(x - 14 * k, 128 - h * 0.6, x, 128 - h); p.quadraticCurveTo(x + 14 * k, 128 - h * 0.6, x + 18 * k, 128); p.fill(); } } },
    "st:mark": (p) => { p.strokeStyle = "#E83020"; p.lineWidth = 8; p.beginPath(); p.arc(64, 64, 44, 0, Math.PI * 2); p.moveTo(64, 10); p.lineTo(64, 118); p.moveTo(10, 64); p.lineTo(118, 64); p.stroke(); },
  };
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); for (const [n, f] of Object.entries(PAINT)) { const c = cv(); f(c.getContext("2d")); set.index[n] = set.layers.length; set.layers.push(c); } return set; }; }
  const put = (out, at, layer, w, h, lift, o = {}) => { const x = Math.floor(at[0]), y = Math.floor(at[2]); out.push(Object.assign({ x, y, dx: at[0] - x - 0.5, dz: at[2] - y - 0.5, layer, w, h, lift }, o)); };
  { const ls0 = CM.lifeSprites; CM.lifeSprites = (game, fl, now) => { const out = ls0 ? ls0(game, fl, now) : []; const K = CM.fxKit; if (!fl || game.mode !== "combat" || !K || !K.atFoe || !CM.renderer || CM.renderer.index["st:z"] === undefined) return out;
      const t = now / 1000, still = CM.reducedMotion;
      for (const m of game.foes || []) { if (!(m.hp > 0) || m.hidden) continue; const base = K.atFoe(m, 0); if (!base) continue; const H = m.boss ? 0.95 : m.guardian ? 0.85 : 0.75;
        if (m.bleeding > 0) for (let i = 0; i < 2; i++) { const ph = ((t * 0.8 + i * 0.5) % 1); put(out, [base[0] + (i - 0.5) * 0.15, 0, base[2]], "st:drip", 0.05, 0.07, H * 0.6 * (1 - ph), { glow: 0.3, alpha: 1 - ph }); }
        if (m.asleep > 0) for (let i = 0; i < 3; i++) { const ph = (t * 0.35 + i / 3) % 1; put(out, [base[0] + 0.1 + ph * 0.15, 0, base[2]], "st:z", 0.08 + ph * 0.08, 0.08 + ph * 0.08, H + ph * 0.35, { glow: 0.8, alpha: 1 - ph }); }
        if (m.held > 0) put(out, base, "st:vines", 0.55, 0.35, 0, { glow: 0.1 });
        if (m.blind > 0) put(out, [base[0] + (still ? 0 : Math.sin(t * 2) * 0.03), 0, base[2]], "st:blind", 0.3, 0.08, H * 0.82);
        if (m.chilled > 0) put(out, base, "st:frost", 0.6, 0.22, 0, { glow: 0.4 });
        if (m.burning > 0) put(out, base, "st:flame", 0.5, 0.35 + (still ? 0 : Math.sin(t * 9) * 0.04), 0, { glow: 1.2 });
        if (m.marked) put(out, base, "st:mark", 0.16, 0.16, H * 0.9, { glow: 1, alpha: 0.6 + 0.3 * Math.sin(t * 4) }); }
      return out; }; }
}
