"use strict";
// Spell shapes (v39.2, UPGRADE_PLAN_34.md): each school's own mark where it lands, over the flight and flash it had
// (76zzzy-spells.js): fire swirls up in a coil and leaves embers drifting; frost grows crystals in the air that hang and
// shatter; lightning branches - a bolt jumping from one foe to the next; holy light falls in rays from above; arcane
// force rings out in violet; the necromancer's and the hexer's arts curl in dark smoke.
{ const S = 128, cv = () => { const c = document.createElement("canvas"); c.width = c.height = S; return c; };
  const PAINT = {
    "sp:crystal": (p) => { const g = p.createLinearGradient(40, 0, 90, 128); g.addColorStop(0, "#F0FAFF"); g.addColorStop(1, "#7AB8E8"); p.fillStyle = g; p.beginPath(); p.moveTo(64, 4); p.lineTo(92, 50); p.lineTo(64, 124); p.lineTo(36, 50); p.closePath(); p.fill(); p.strokeStyle = "rgba(255,255,255,0.8)"; p.lineWidth = 2; p.beginPath(); p.moveTo(64, 4); p.lineTo(64, 124); p.stroke(); },
    "sp:ray": (p) => { const g = p.createLinearGradient(0, 0, 0, 128); g.addColorStop(0, "rgba(255,250,210,0)"); g.addColorStop(0.5, "rgba(255,245,190,0.85)"); g.addColorStop(1, "rgba(255,240,170,0.2)"); p.fillStyle = g; p.beginPath(); p.moveTo(48, 0); p.lineTo(80, 0); p.lineTo(100, 128); p.lineTo(28, 128); p.closePath(); p.fill(); },
    "sp:smoke": (p) => { for (let i = 0; i < 6; i++) { const g = p.createRadialGradient(40 + i * 10, 40 + (i % 3) * 20, 4, 40 + i * 10, 40 + (i % 3) * 20, 40); g.addColorStop(0, "rgba(60,20,80,0.75)"); g.addColorStop(1, "rgba(30,10,40,0)"); p.fillStyle = g; p.fillRect(0, 0, S, S); } },
    "sp:ember": (p) => { const g = p.createRadialGradient(64, 64, 2, 64, 64, 40); g.addColorStop(0, "#FFF0A0"); g.addColorStop(0.4, "#FF8A20"); g.addColorStop(1, "rgba(255,60,0,0)"); p.fillStyle = g; p.fillRect(0, 0, S, S); },
  };
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); for (const [n, f] of Object.entries(PAINT)) { const c = cv(); f(c.getContext("2d")); set.index[n] = set.layers.length; set.layers.push(c); } return set; }; }
  const SCHOOL = { firebolt: "fire", fireball: "fire", fire: "fire", firework: "fire", oilgears: "fire", frost: "frost", lightning: "storm", calllightning: "storm", smite: "holy", turn: "holy", heal: "holy", lay: "holy", bless: "holy",
    missile: "force", blink: "force", drain: "dark", hex: "dark", thrall: "dark", deathpact: "dark", sleep: "force", entangle: "growth", thorns: "growth", regrowth: "growth" };
  const shape = (K, school, foes, fx) => { const at = (m, h) => K.atFoe && K.atFoe(m, h); const list = (fx.foe ? [fx.foe] : []).concat((foes || []).filter((m) => m !== fx.foe)).filter((m) => m && m.hp > -999).slice(0, 5);
    for (const [i, m] of list.entries()) { const p = at(m, 0.4); if (!p) continue; const later = (ms, f) => setTimeout(f, ms + i * 60);
      if (school === "fire") later(380, () => { for (let k = 0; k < 6; k++) setTimeout(() => K.fxs.flare({ at: [p[0] + Math.cos(k) * 0.15, 0.15 + k * 0.12, p[2] + Math.sin(k) * 0.15], layer: "sp:ember", size: 0.18, ms: 700, rise: 0.4, grow: -0.1 }), k * 50); K.fxs.burst({ at: p, layer: "sp:ember", n: 10, size: 0.05, speed: 0.4, up: 0.8, gravity: -0.6, ms: 1600 }); });
      if (school === "frost") later(320, () => { for (let k = 0; k < 5; k++) K.fxs.flare({ at: [p[0] + (k - 2) * 0.09, 0.3 + (k % 2) * 0.2, p[2]], layer: "sp:crystal", size: 0.16 + (k % 3) * 0.05, ms: 900, rise: 0, grow: 0.05, glow: 0.6 }); setTimeout(() => K.fxs.burst({ at: p, layer: "sp:crystal", n: 8, size: 0.05, speed: 1.4, up: 1, gravity: 4, ms: 500 }), 900); });
      if (school === "holy") later(150, () => { K.fxs.flare({ at: [p[0], 0.9, p[2]], layer: "sp:ray", size: 0.9, ms: 800, rise: -0.2, grow: 0.1 }); });
      if (school === "dark") later(200, () => { K.fxs.flare({ at: [p[0], 0.45, p[2]], layer: "sp:smoke", size: 0.7, ms: 1000, rise: 0.25, grow: 0.4, glow: 0 }); });
      if (school === "force") later(260, () => K.fxs.ring({ at: [p[0], 0.02, p[2]], to: 1.1, ms: 500 }));
      if (school === "growth") later(200, () => K.fxs.burst({ at: [p[0], 0.05, p[2]], layer: "hit:tuft", n: 8, size: 0.08, speed: 0.3, up: 1.2, gravity: 1, ms: 900 })); }
    if (school === "storm" && list.length) { const pts = list.map((m) => at(m, 0.55)).filter(Boolean); pts.forEach((pt, i) => setTimeout(() => { K.fxs.flare({ at: pt, layer: "fx:bolt", size: 0.8, ms: 220, grow: 0.1 }); if (i + 1 < pts.length) { const q = pts[i + 1]; for (let k = 1; k < 5; k++) K.fxs.flare({ at: [pt[0] + (q[0] - pt[0]) * k / 5, pt[1] + Math.sin(k * 2.3) * 0.12, pt[2] + (q[2] - pt[2]) * k / 5], layer: "fx:bolt", size: 0.3, ms: 180 }); } }, 200 + i * 110)); } };
  const bind = () => { const g = CM.game, K = CM.fxKit; if (!g || !g.on || !K) return false; g.on("fx", (fx) => { if (!fx || fx.kind !== "cast" || CM.reducedMotion) return; const sc = SCHOOL[fx.id]; if (sc) shape(K, sc, fx.foes, fx); }); return true; };
  const t = typeof self !== "undefined" && self.CM_WORKER ? null : setInterval(() => { if (bind()) clearInterval(t); }, 300);
}
