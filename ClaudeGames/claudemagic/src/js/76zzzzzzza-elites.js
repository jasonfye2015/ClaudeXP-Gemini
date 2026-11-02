"use strict";
// Elite looks (v39.4, UPGRADE_PLAN_34.md): champions, guardians and the Lich King stand in an aura - a ring of light on the
// floor about them in the colour of what they are (a champion's word, a guardian's own, the king's cold blue) with motes
// rising out of it - and the great ones' tread ripples the floor now and then in a fight. In a fight and on the floor.
{ const S = 128, cv = () => { const c = document.createElement("canvas"); c.width = c.height = S; return c; };
  const ring = (col) => (p) => { p.strokeStyle = col; p.lineWidth = 10; p.beginPath(); p.arc(64, 64, 52, 0, Math.PI * 2); p.stroke(); p.lineWidth = 4; p.beginPath(); p.arc(64, 64, 40, 0, Math.PI * 2); p.stroke();
    for (let i = 0; i < 12; i++) { const a = i * Math.PI / 6; p.beginPath(); p.moveTo(64 + Math.cos(a) * 40, 64 + Math.sin(a) * 40); p.lineTo(64 + Math.cos(a) * 52, 64 + Math.sin(a) * 52); p.stroke(); } };
  const COL = { gold: "#F0C040", red: "#E04030", blue: "#70B0FF", green: "#60D060", violet: "#B070F0" };
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); for (const [n, c] of Object.entries(COL)) { const k = cv(); ring(c)(k.getContext("2d")); set.index[`el:${n}`] = set.layers.length; set.layers.push(k);
      const m = cv(), q = m.getContext("2d"); q.fillStyle = c; q.beginPath(); q.arc(64, 64, 40, 0, Math.PI * 2); q.fill(); q.fillStyle = "#FFFFFF"; q.beginPath(); q.arc(64, 64, 16, 0, Math.PI * 2); q.fill(); set.index[`elm:${n}`] = set.layers.length; set.layers.push(m); } return set; }; }
  const colourOf = (m) => (m.boss ? "blue" : m.guardian ? ({ rat: "green", knight: "blue", forge: "red", queen: "blue", mind: "green", tyrant: "violet", master: "red", patriarch: "gold", root: "red" }[m.guardian] || "gold") : m.champion ? ({ vampiric: "red", warded: "violet", shadowed: "violet", hoarder: "gold" }[m.champion] || "gold") : null);
  const aura = (out, x, z, col, big, now, i) => { const cx = Math.floor(x), cz = Math.floor(z), t = now / 1000, still = CM.reducedMotion;
    out.push({ x: cx, y: cz, dx: x - cx - 0.5, dz: z - cz - 0.5, layer: `el:${col}`, w: 0.5 * big, flat: true, spin: still ? 0 : t * 0.6 + i, glow: 1.4, alpha: 0.75 + 0.2 * Math.sin(t * 2 + i) });
    if (!still) for (let k = 0; k < 4; k++) { const ph = (t * 0.5 + k / 4 + i * 0.13) % 1, a = k * 1.7 + i; out.push({ x: cx, y: cz, dx: x - cx - 0.5 + Math.cos(a) * 0.25 * big, dz: z - cz - 0.5 + Math.sin(a) * 0.25 * big, layer: `elm:${col}`, w: 0.04, h: 0.04, lift: ph * 0.9 * big, glow: 2, alpha: 1 - ph }); } };
  let lastTread = 0;
  { const ls0 = CM.lifeSprites; CM.lifeSprites = (game, fl, now) => { const out = ls0 ? ls0(game, fl, now) : []; if (!fl || !CM.renderer || CM.renderer.index["el:gold"] === undefined) return out;
      if (game.mode === "combat" && CM.fxKit && CM.fxKit.atFoe) { let big = null; (game.foes || []).forEach((m, i) => { if (!(m.hp > 0) || m.hidden) return; const col = colourOf(m); if (!col) return; const at = CM.fxKit.atFoe(m, 0); if (!at) return; const B = m.boss ? 1.5 : m.guardian ? 1.3 : 1; aura(out, at[0], at[2], col, B, now, i); if (B > 1) big = at; });
        if (big && !CM.reducedMotion && now - lastTread > 2600) { lastTread = now; CM.fxKit.fxs.ring({ at: [big[0], 0.01, big[2]], to: 1.6, ms: 700 }); if (CM.renderer.shake) CM.renderer.shake(0.08); } }
      else if (game.mode === "explore") { const [px, py] = fl.pos; let i = 0; for (const [k, t] of Object.entries(fl.things)) { if (!["monsters", "guardian", "boss"].includes(t.type)) continue; const [x, y] = k.split(",").map(Number); if (Math.abs(x - px) + Math.abs(y - py) > 8) continue;
          const lead = (t.group || []).find((m) => colourOf(m)) || (t.type !== "monsters" ? { guardian: t.guardian || "x", boss: t.type === "boss" } : null); if (!lead) continue; aura(out, x + 0.5, y + 0.5, colourOf(lead) || "gold", lead.boss ? 1.5 : lead.guardian ? 1.3 : 1, now, i++); } }
      return out; }; }
}
