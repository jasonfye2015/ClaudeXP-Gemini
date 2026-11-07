"use strict";
// The island, seen (UPGRADE_PLAN_79.md, v129.0; the rules 69zzzzg-island.js, the shore 23f-shore.js): past the land's
// edge on the north, the west and the south, the sea - the water's own shader, rippling, carrying the sky, glinting -
// to the edge of seeing; a strip of grey shingle between the last trees and the water; the hill's cliffs closed where
// they meet the sea; surf running up the sand and back along the Strand; and on the world map, once the island is
// known, the sea round the land.
{ const H = CM.SHORE;
  // past the edge: the sea, the shingle, the hill's ends
  { const fv0 = CM.farViews; CM.farViews = (fl, size, index, night, put) => { const n = fv0 ? fv0(fl, size, index, night, put) : 0; if (!fl || fl.number !== -1 || !CM.LAND_ISLE || fl.grid.length <= H.sea) return n;
      const water = index.water0, shingle = index["ground:rock"], cliff = index["solid:cliff"], R = 230, y = -0.04;
      if (water !== undefined) put([-R, y, size + R], [size + R, y, size + R], [size + R, y, -R], [-R, y, -R], water, 0.92, 4);   // (the sea: under all the land, and out to the haze)
      if (shingle !== undefined) { const B = 1.6, E = CM.WOOD_EAST, band = (x0, z0, x1, z1) => { for (let z = z0; z < z1; z += 4) for (let x = x0; x < x1; x += 4) { const xe = Math.min(x + 4, x1), ze = Math.min(z + 4, z1); put([x, 0, ze], [xe, 0, ze], [xe, 0, z], [x, 0, z], shingle, 0.78, 0); } };
        band(-B, -B, E, 0); band(-B, 0, 0, H.strand[0]); }   // (grey shingle between the last trees and the water)
      if (cliff !== undefined) { const E = CM.WOOD_EAST; for (let x = E; x < size; x += 2) put([Math.min(x + 2, size), y, 0], [x, y, 0], [x, 2.2, 0], [Math.min(x + 2, size), 2.2, 0], cliff, 0.7, 0);   // (the hill falls to the sea: its north face, and its east end)
        for (let z = 0; z < H.strand[0]; z += 2) put([size, y, z], [size, y, Math.min(z + 2, H.strand[0])], [size, 2.2, Math.min(z + 2, H.strand[0])], [size, 2.2, z], cliff, 0.62, 0); }
      return n + 1; }; }
  // the surf: up the sand and back, along the water's edge near the party
  { const ls0 = CM.lifeSprites; CM.lifeSprites = (game, fl, now) => { const out = ls0 ? ls0(game, fl, now) : []; if (!fl || fl.number !== -1 || game.mode === "title" || fl.grid.length <= H.sea || Math.abs(fl.pos[1] - H.sea) > 14) return out;
      const t = CM.reducedMotion ? 0 : now / 1000, ice = fl.frozen;
      for (let x = Math.max(1, fl.pos[0] - 14); x <= Math.min(fl.grid.length - 2, fl.pos[0] + 14); x++) { const ph = t * 0.32 + Math.sin(x * 0.7) * 0.4 + x * 0.05, k = (Math.sin(ph * Math.PI * 2) + 1) / 2;
        if (!ice) out.push({ x, y: H.sea, dz: -0.42 - k * 0.28, flat: true, layer: `fx:foam${(x + Math.floor(t * 3)) % 3}`, w: 1.15, alpha: 0.25 + 0.4 * (1 - k) }); }
      return out; }; }
  // the lapping of the waves, along the shore (76zzzzs-placeamb.js plays it)
  CM.shoreNear = (fl) => (fl && fl.number === -1 && fl.grid.length > H.sea ? Math.abs(fl.pos[1] - H.sea) : 99);
}
