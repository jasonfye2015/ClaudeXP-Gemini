"use strict";
// Which way it faces (v29.1, UPGRADE_PLAN_24.md): a monster on the floor faces the way it last moved (one that has not
// moved, a way of its own, by its square); from the party's side of it, it is seen from the front, from the side (its
// picture narrowed, its far side in shadow, turned the way it faces) or from behind (its picture in shadow, turned
// away). In a fight they all face the party. The facing is the picture's only: the rules don't know it.
{ const faces = new WeakMap(), DIRS = [[0, -1], [1, 0], [0, 1], [-1, 0]];
  CM.monsterView = (thing, x, y, eye) => {
    let f = faces.get(thing);
    if (thing.anim && thing.anim.from) { const dx = Math.sign(x - thing.anim.from[0]), dy = Math.sign(y - thing.anim.from[1]); if (dx || dy) { f = [dx, dy]; faces.set(thing, f); } }
    if (!f) { f = DIRS[CM.hashSeed(`face:${x},${y}`) % 4]; faces.set(thing, f); }
    if (!eye) return null; const vx = eye[0] - (x + 0.5), vz = eye[2] - (y + 0.5), d = Math.hypot(vx, vz) || 1, dot = (f[0] * vx + f[1] * vz) / d, cross = f[0] * vz - f[1] * vx;
    if (dot > 0.45) return { view: "front", mirror: false };
    return { view: dot < -0.45 ? "back" : "side", mirror: cross > 0 };
  };
}
