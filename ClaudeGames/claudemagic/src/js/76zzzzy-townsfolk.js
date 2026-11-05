"use strict";
// Townsfolk with routines (v29.4, UPGRADE_PLAN_24.md): the town's six residents keep hours. By day the smith is at the
// forge's door, the merchant at the market, the priest at the temple, the librarian at the library, the landlady and
// the farmer about the market and the well; in the evening most of them make for the tavern; at night they are home,
// out of sight. When the hour moves them they walk there along the streets, and in the rain they keep under the eaves.
// They are the picture's: the rules don't know them.
{ const H = (a, b) => [a, b];
  const ROUTINE = {   // [from hour, to hour, where]: where is a building's door, the market, the well or the gate
    smith: [[H(7, 18), "smith"], [H(18, 21), "tavern"]],
    merchant: [[H(7, 9), "well"], [H(9, 17), "market"], [H(17, 19), "well"], [H(19, 22), "tavern"]],
    library: [[H(8, 17), "library"], [H(17, 19), "well"], [H(19, 21), "market"]],
    priest: [[H(6, 12), "temple"], [H(12, 14), "market"], [H(14, 20), "temple"]],
    farm: [[H(6, 10), "market"], [H(10, 16), "woodgate"], [H(16, 19), "well"], [H(19, 22), "tavern"]],
    tavern: [[H(9, 11), "market"], [H(11, 14), "well"], [H(14, 24), "tavern"]],
  };
  const WHO = Object.keys(ROUTINE), SPEED = 1.6;
  const placeOf = (fl, where, i) => { const A = CM.TOWN_AT || {}, B = (CM.TOWN_BLOCKS || {})[where];
    let at = B ? B.door : where === "market" ? A.market : where === "well" ? A.well : where === "woodgate" ? A.woodgate : null; if (!at) return null;
    // a square beside it, each of them their own
    const cand = []; for (let r = 1; r <= 3 && cand.length < 8; r++) for (let dy = -r; dy <= r; dy++) for (let dx = -r; dx <= r; dx++) { const x = at[0] + dx, y = at[1] + dy; if (Math.max(Math.abs(dx), Math.abs(dy)) === r && CM.passable(fl, x, y) && !fl.things[`${x},${y}`]) cand.push([x, y]); }
    return cand.length ? cand[i % cand.length] : at; };
  const eaveNear = (fl, at) => { for (let r = 0; r <= 4; r++) for (let dy = -r; dy <= r; dy++) for (let dx = -r; dx <= r; dx++) { const x = at[0] + dx, y = at[1] + dy; if (!CM.passable(fl, x, y) || fl.things[`${x},${y}`]) continue;
        if (CM.DIRS.some(([a, b]) => CM.isBuilding && CM.isBuilding(fl, x + a, y + b))) return [x, y]; } return at; };
  const path = (fl, a, b) => { const size = fl.grid.length, key = (x, y) => y * size + x, prev = new Map([[key(a[0], a[1]), -1]]), q = [a];
    while (q.length) { const [x, y] = q.shift(); if (x === b[0] && y === b[1]) break; for (const [dx, dy] of CM.DIRS) { const nx = x + dx, ny = y + dy; if (nx < 0 || ny < 0 || nx >= size || ny >= size || !CM.passable(fl, nx, ny) || prev.has(key(nx, ny))) continue; prev.set(key(nx, ny), key(x, y)); q.push([nx, ny]); } }
    if (!prev.has(key(b[0], b[1]))) return [a, b]; const out = []; for (let k = key(b[0], b[1]); k !== -1; k = prev.get(k)) out.push([k % size, Math.floor(k / size)]); return out.reverse(); };
  const folk = {};   // who -> { at, to, path, t0 }
  CM.townsfolkNow = (game, fl) => { const h = CM.hourOf(game) % 24, rain = CM.weather(game) === "rain", out = [];
    WHO.forEach((who, i) => { const slot = ROUTINE[who].find(([[a, b]]) => h >= a && h < b); if (!slot) { delete folk[who]; return; }
      let target = placeOf(fl, slot[1], i); if (!target) return; if (rain) target = eaveNear(fl, target);
      out.push([who, target, slot[1]]); });
    return out; };
  { const ls0 = CM.lifeSprites; CM.lifeSprites = (game, fl, now) => { const out = ls0 ? ls0(game, fl, now) : []; if (!fl || fl.number !== 0 || !CM.renderer || game.mode === "title") return out;
      for (const [who, target, where] of CM.townsfolkNow(game, fl)) { let F = folk[who];
        if (!F) F = folk[who] = { at: target.slice(), to: target.slice(), path: [target], t0: now };
        if (F.to[0] !== target[0] || F.to[1] !== target[1]) { const here = F.cur || F.at; F.path = path(fl, [Math.round(here[0]), Math.round(here[1])], target); F.to = target.slice(); F.t0 = now; }
        const P = F.path, f = Math.min(P.length - 1, ((now - F.t0) / 1000) * SPEED), j = Math.floor(f), u = f - j, a = P[j], b = P[Math.min(P.length - 1, j + 1)];
        const x = a[0] + (b[0] - a[0]) * u, y = a[1] + (b[1] - a[1]) * u; F.cur = [x, y]; const walking = f < P.length - 1, cx = Math.floor(x + 0.5), cy = Math.floor(y + 0.5);
        if (cx === fl.pos[0] && cy === fl.pos[1]) continue;   // (out of the party's way: not drawn on its square)
        const L = `npc:res_${who === "priest" ? "priest" : who}`; if (CM.renderer.index[L] === undefined && !(CM.figures && CM.Figures && CM.Figures.figureOf(L))) continue;   // (v68.0: a resident with a body but no picture is drawn as the body)
        out.push({ id: `res:${who}`, walking, act: walking ? null : ({ smith: "work", market: "work", library: "work", temple: "work" }[where] || null), x: cx, y: cy, dx: x - cx, dz: y - cy, layer: L, w: 0.62, h: 0.82, lift: walking ? Math.abs(Math.sin(now / 160 + x)) * 0.025 : 0,
          bend: CM.monsterBend ? CM.monsterBend(walking ? "walk" : "idle", now, x * 3 + y, null) : null }); }
      return out; }; }
}
