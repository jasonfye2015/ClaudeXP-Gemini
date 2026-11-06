"use strict";
// Presentation, fourth pass (UPGRADE_PLAN_74.md, release 4): enemy silhouettes. Many kinds share a handful of bodies
// (the rogue's, the barbarian's, the knight's) told apart by colour and size alone, so a kobold could read as a
// person in a hood. Now each family stands its own way: its proportions (an ogre broad, a troll tall and stooped, a
// kobold squat, a dark elf slender) and its carriage (a zombie or a ghoul hunched forward, a gargoyle crouched, a
// demon upright). The body's own joints, its gear and its animations go with it; only how the figure is set on the
// square changes, and only in the figures' own pass (not the far impostors, which keep the painted look).
//   CM.SILHOUETTES[kind] -> { sx, sy, sz, lean } (widths, height, depth, and the forward lean in radians)
{ CM.SILHOUETTES = {
    Kobold: { sx: 1.16, sy: 0.84, sz: 1.12, lean: 0.12 }, Goblin: { sx: 1.08, sy: 0.88, sz: 1.04, lean: 0.16 }, Zombie: { sx: 1.02, sy: 0.95, sz: 1.0, lean: 0.3 },
    Ghoul: { sx: 0.9, sy: 0.98, sz: 0.95, lean: 0.34 }, Orc: { sx: 1.16, sy: 1.0, sz: 1.12, lean: 0.06 }, Troll: { sx: 0.9, sy: 1.18, sz: 0.95, lean: 0.2 },
    Ogre: { sx: 1.3, sy: 0.94, sz: 1.24, lean: 0.08 }, Minotaur: { sx: 1.2, sy: 1.08, sz: 1.1, lean: 0.12 }, Demon: { sx: 1.1, sy: 1.1, sz: 1.05, lean: -0.05 },
    "Dark Elf": { sx: 0.88, sy: 1.08, sz: 0.9, lean: 0 }, Wraith: { sx: 0.85, sy: 1.15, sz: 0.85, lean: 0.1 }, Vampire: { sx: 0.92, sy: 1.06, sz: 0.94, lean: -0.03 },
    Drowned: { sx: 0.96, sy: 1.0, sz: 0.96, lean: 0.16 }, "Weed Hag": { sx: 1.0, sy: 0.9, sz: 1.0, lean: 0.3 }, "Crystal Golem": { sx: 1.26, sy: 1.05, sz: 1.2, lean: 0.04 },
    "Slag Golem": { sx: 1.3, sy: 0.95, sz: 1.25, lean: 0.06 }, Gargoyle: { sx: 1.2, sy: 0.86, sz: 1.1, lean: 0.24 }, "Foundry Imp": { sx: 1.12, sy: 0.84, sz: 1.06, lean: 0.12 },
    "Bellows Imp": { sx: 1.12, sy: 0.84, sz: 1.06, lean: 0.12 }, "Grave Priest": { sx: 0.96, sy: 1.04, sz: 0.96, lean: 0.12 }, "Hollow One": { sx: 0.86, sy: 1.12, sz: 0.86, lean: 0.04 },
    "Prism Sentinel": { sx: 1.1, sy: 1.1, sz: 1.06, lean: 0 }, "Drowned Townsfolk": { sx: 0.96, sy: 0.98, sz: 0.96, lean: 0.14 }, "Shard Wisp": { sx: 0.9, sy: 1.0, sz: 0.9, lean: 0.06 },
    "Bone Colossus": { sx: 1.15, sy: 1.0, sz: 1.1, lean: 0.08 }, "Grave Lantern": { sx: 0.9, sy: 1.05, sz: 0.9, lean: 0.08 } };
  const F = CM.Figures; if (F && F.modelMatrix && CM.Renderer) {
  const L = new Float32Array(16), T = new Float32Array(16);
  const shapeOf = (f) => { const layer = (f && f.s && f.s.layer) || "", parts = layer.split(":"); if (parts[0] !== "monster") return null; const K = CM.monsterKind ? CM.monsterKind(parts[1]) : null; return CM.SILHOUETTES[parts[1]] || (K && CM.SILHOUETTES[K.name]) || null; };
  let queue = null;
  const mm0 = F.modelMatrix; F.modelMatrix = function (out, ...a) { const res = mm0.call(this, out, ...a); if (!queue) return res; const S = queue.list[queue.i++]; if (!S || CM.silhouettesOff) return res;
    const c = Math.cos(S.lean || 0), s = Math.sin(S.lean || 0);   // (local: the lean about the feet, then the proportions - Rx(lean) * diag(sx, sy, sz), column-major)
    L.fill(0); L[0] = S.sx; L[5] = c * S.sy; L[6] = s * S.sy; L[9] = -s * S.sz; L[10] = c * S.sz; L[15] = 1; T.set(res); F.mul(res, T, L); return res; };
  const df0 = CM.Renderer.prototype.drawFigures; CM.Renderer.prototype.drawFigures = function (...a) { queue = { list: (this.figList || []).map(shapeOf), i: 0 }; try { return df0.apply(this, a); } finally { queue = null; } };
  }
}
