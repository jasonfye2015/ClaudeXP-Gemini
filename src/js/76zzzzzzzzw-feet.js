"use strict";
// Feet on the stone (v50.1, UPGRADE_PLAN_45.md): a monster stands on the floor rather than floating over it - a small,
// dark contact shadow right under its feet (under the long one the light casts), tighter and darker for the heavy and
// wider for the big ones, in a fight as on the floor; and since its square's floor is its own (69zzi-levels.js), on a
// dais or a stair or down in a pit it stands on that. Ghosts and wisps float, and keep only a faint one.
{ const W = { wide: 0.62, beast: 0.58, tall: 0.42, thin: 0.36, small: 0.34, biped: 0.42, ghost: 0.4 };
  const contact = (out, x, z, m) => { const k = CM.monsterKind(m.kind || m.name) || {}, body = k.body || m.body || "biped", ghost = body === "ghost", big = m.boss ? 1.4 : m.guardian ? 1.25 : 1, cx = Math.floor(x), cz = Math.floor(z);
    out.push({ x: cx, y: cz, dx: x - cx - 0.5, dz: z - cz - 0.5, layer: "shadow", flat: true, w: (W[body] || 0.42) * big, alpha: ghost ? 0.25 : body === "wide" ? 0.95 : 0.85 }); };
  { const ls0 = CM.lifeSprites; CM.lifeSprites = (game, fl, now) => { const out = ls0 ? ls0(game, fl, now) : []; if (!fl || !CM.renderer || CM.renderer.index.shadow === undefined) return out;
      if (game.mode === "combat" && CM.fxKit && CM.fxKit.atFoe) { for (const m of game.foes || []) { if (!(m.hp > 0) || m.hidden) continue; const at = CM.fxKit.atFoe(m, 0); if (at) contact(out, at[0], at[2], m); } }
      else for (const [k, t] of Object.entries(fl.things)) { if (!["monsters", "boss", "guardian"].includes(t.type) || !t.group || t.anim) continue; const [x, y] = k.split(",").map(Number); if (Math.abs(x - fl.pos[0]) + Math.abs(y - fl.pos[1]) > 10) continue;
        const m = t.group.find((f) => f.hp > 0 && !f.fled) || t.group[0]; if (m) contact(out, x + 0.5, y + 0.5, m); }
      return out; }; }
}
