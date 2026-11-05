"use strict";
// Day reaching in (v49.4, UPGRADE_PLAN_44.md): on the first three floors, by day, the town's grates let it down - an iron
// grate here and there in a corridor's ceiling, a shaft of daylight under it and the grate's shadow laid in a bright
// lattice on the floor - and the foot of the shaft on the first floor stands in the daylight from above. Brightest on
// the first floor and fainter each floor down, by the hour, and greyer under cloud or rain.
{ const S = 128;
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); if (set.index["dl:grate"] !== undefined) return set;
      const g = document.createElement("canvas"); g.width = g.height = S; const p = g.getContext("2d"); p.fillStyle = "#2A2A30"; p.fillRect(0, 0, S, S); p.clearRect(14, 14, 100, 100); p.fillStyle = "#3A3A42"; for (let i = 0; i < 5; i++) { p.fillRect(14 + i * 22, 14, 8, 100); p.fillRect(14, 14 + i * 22, 100, 8); }
      const l = document.createElement("canvas"); l.width = l.height = S; const q = l.getContext("2d"); q.fillStyle = "#FFF6DC"; for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) q.fillRect(16 + i * 25, 16 + j * 25, 17, 17);
      set.index["dl:grate"] = set.layers.length; set.layers.push(g); set.index["dl:lattice"] = set.layers.length; set.layers.push(l); return set; }; }
  const DEPTH = { 1: 1, 2: 0.6, 3: 0.32 };
  const dayK = (game) => { if (CM.isNight && CM.isNight(game)) return 0; const h = CM.hourOf ? CM.hourOf(game) : 12, w = CM.weather ? CM.weather(game) : "clear"; return Math.max(0, Math.sin(Math.PI * (h - 5) / 16)) * (w === "rain" || w === "snow" ? 0.55 : w === "mist" ? 0.7 : 1); };
  const grates = new WeakMap(), gratesOf = (fl) => { let G = grates.get(fl); if (G) return G; G = []; const N = fl.grid.length, inRoom = new Set(); for (const r of fl.rooms || []) for (let y = r.y0; y <= r.y1; y++) for (let x = r.x0; x <= r.x1; x++) inRoom.add(`${x},${y}`);
    const rnd = new CM.Random(CM.hashSeed(`grates:${fl.number}`)); for (let y = 1; y < N - 1; y++) for (let x = 1; x < N - 1; x++) { if (fl.grid[y][x] !== 0 || inRoom.has(`${x},${y}`) || fl.things[`${x},${y}`] || CM.ceilAt(fl, x, y) !== 1) continue; if (rnd.next() < 0.035) G.push([x, y]); }
    const shaft = Object.entries(fl.things).find(([, t]) => t.type === "ladder"); if (fl.number === 1 && shaft) G.push([...shaft[0].split(",").map(Number), true]); grates.set(fl, G); return G; }; CM.gratesOf = gratesOf;   // (v78.0: the waterfalls and the lightning use them - 76zzzzzzzzzzn-below.js)
  const live = (game, fl) => fl && DEPTH[fl.number] && game.mode !== "title" ? DEPTH[fl.number] * dayK(game) : 0;
  { const ls0 = CM.lifeSprites; CM.lifeSprites = (game, fl, now) => { const out = ls0 ? ls0(game, fl, now) : []; if (!fl || !DEPTH[fl.number] || !CM.renderer || CM.renderer.index["dl:grate"] === undefined) return out; const k = live(game, fl);
      for (const [x, y, isShaft] of gratesOf(fl)) { if (Math.abs(x - fl.pos[0]) + Math.abs(y - fl.pos[1]) > 10) continue; const c = CM.ceilAt(fl, x, y), f = CM.floorAt(fl, x, y);
        if (!isShaft) out.push({ x, y, layer: "dl:grate", flat: true, w: 0.7, base: c - 0.012, glow: 0.25 + k * 1.2 });
        if (k > 0.03) { out.push({ x, y, layer: isShaft ? "ce:patch" : "dl:lattice", flat: true, w: isShaft ? 0.9 : 0.7, base: f, glow: 2, alpha: 0.2 + 0.4 * k, spin: 0.15 });
          if (CM.renderer.index["ce:shaft"] !== undefined) out.push({ x, y, layer: "ce:shaft", w: isShaft ? 0.75 : 0.55, h: c - f, base: f, glow: 2, alpha: 0.1 + 0.12 * k }); } }
      return out; }; }
  { const xl0 = CM.extraLights; CM.extraLights = (game, fl, out, renderer) => { if (xl0) xl0(game, fl, out, renderer); const k = live(game, fl); if (k < 0.03) return;
      for (const [x, y, isShaft] of gratesOf(fl)) { const d = Math.abs(x - fl.pos[0]) + Math.abs(y - fl.pos[1]); if (d > 9) continue; out.push({ x: x + 0.5, y: CM.ceilAt(fl, x, y) - 0.1, z: y + 0.5, reach: isShaft ? 3.6 : 2.6, colour: [0.58 * k, 0.6 * k, 0.66 * k], flicker: false, d }); } }; }
}
