"use strict";
// Ceilings (v40.3, UPGRADE_PLAN_35.md): the dungeon's roof gets something to it - stone ribs springing across a hall's
// bays (the halls of 76zzzzzzzd-furniture.js, and any room of twenty squares or more), timber beams across the cellar
// rooms and corridors of the Catacombs and the Dwarven Halls, chains hanging from the dark in the Palace, the Foundry and
// the Ossuary, and - in the first two bands, by day - light falling through a broken place in the roof, a shaft of it
// and a pale patch on the floor. Chosen by the floor's number and drawn only.
{ const S = 128, cv = () => { const c = document.createElement("canvas"); c.width = c.height = S; return c; };
  const PAINT = {
    "ce:beam": (p) => { p.fillStyle = "#4A3220"; p.fillRect(0, 110, 128, 18); p.fillStyle = "#5E4230"; p.fillRect(0, 110, 128, 4); p.fillStyle = "#3A2616"; for (let x = 6; x < 128; x += 22) p.fillRect(x, 116, 12, 2); },
    "ce:rib": (p) => { p.save(); p.beginPath(); p.rect(0, 0, 128, 52); p.clip(); p.strokeStyle = "#8A8070"; p.lineWidth = 9; p.beginPath(); p.ellipse(64, 60, 66, 58, 0, Math.PI, 0); p.stroke(); p.strokeStyle = "#A69C8A"; p.lineWidth = 3; p.beginPath(); p.ellipse(64, 60, 62, 54, 0, Math.PI, 0); p.stroke(); p.restore(); },
    "ce:chain": (p) => { p.strokeStyle = "#9A9AA4"; p.lineWidth = 7; for (let y = 0; y < 112; y += 14) { p.beginPath(); p.ellipse(64, y + 7, (y / 14) % 2 ? 4 : 9, 8, 0, 0, Math.PI * 2); p.stroke(); } p.beginPath(); p.arc(64, 116, 10, 0, Math.PI); p.stroke(); },
    "ce:shaft": (p) => { p.fillStyle = "#FFF2C4"; p.beginPath(); p.moveTo(40, 0); p.lineTo(88, 0); p.lineTo(118, 128); p.lineTo(10, 128); p.closePath(); p.fill(); },
    "ce:patch": (p) => { p.fillStyle = "#FFF0C0"; p.beginPath(); p.ellipse(64, 64, 60, 50, 0, 0, Math.PI * 2); p.fill(); },
  };
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); for (const [n, f] of Object.entries(PAINT)) { const c = cv(); f(c.getContext("2d")); set.index[n] = set.layers.length; set.layers.push(c); } return set; }; }
  const plan = (fl) => { const out = [], shafts = [], band = CM.themeIndex(fl.number), rnd = new CM.Random(CM.hashSeed(`ceiling:${fl.number}`)), open = (x, y) => fl.grid[y] && fl.grid[y][x] === 0, key = (x, y) => `${x},${y}`;
    const inRoom = new Set(); for (const r of fl.rooms || []) for (let y = r.y0; y <= r.y1; y++) for (let x = r.x0; x <= r.x1; x++) inRoom.add(key(x, y));
    for (const r of fl.rooms || []) { const W = r.x1 - r.x0 + 1, H = r.y1 - r.y0 + 1, wide = W >= H; if (W < 2 || H < 2) continue;
      if ((CM.roomPurpose && CM.roomPurpose(fl, r) === "hall") || W * H >= 20) { for (let y = r.y0; y <= r.y1; y++) for (let x = r.x0; x <= r.x1; x++) if (open(x, y) && (wide ? (x - r.x0) % 2 === 1 : (y - r.y0) % 2 === 1)) out.push({ x, y, layer: "ce:rib", axis: wide ? "ew" : "ns", lift: 0 }); }
      else if (band === 0 || band === 2) { for (let y = r.y0; y <= r.y1; y++) for (let x = r.x0; x <= r.x1; x++) if (open(x, y) && (wide ? (x - r.x0) % 2 === 0 : (y - r.y0) % 2 === 0)) out.push({ x, y, layer: "ce:beam", axis: wide ? "ew" : "ns", lift: 0.9 }); } }
    const N = fl.grid.length;
    if (band === 0 || band === 2) for (let y = 1; y < N - 1; y++) for (let x = 1; x < N - 1; x++) { if (!open(x, y) || inRoom.has(key(x, y)) || (x * 7 + y * 3) % 4 !== 0) continue; const ns = open(x, y - 1) && open(x, y + 1), ew = open(x - 1, y) && open(x + 1, y); if (ns === ew) continue; out.push({ x, y, layer: "ce:beam", axis: ns ? "ns" : "ew", lift: 0.9 }); }   /* (a corridor's beam runs across it) */
    if ([3, 7, 8].includes(band)) for (let y = 1; y < N - 1; y++) for (let x = 1; x < N - 1; x++) if (open(x, y) && !fl.things[key(x, y)] && rnd.next() < 0.08) out.push({ x, y, layer: "ce:chain", glow: 0.35, w: 0.09, h: 0.25 + rnd.next() * 0.35, dx: (rnd.next() - 0.5) * 0.6, dz: (rnd.next() - 0.5) * 0.6, chain: true });
    if (band <= 1 && fl.number >= 1) { const rooms = (fl.rooms || []).filter((r) => !r.name); for (let i = 0; i < Math.min(2, rooms.length); i++) { const r = rooms[Math.floor(rnd.next() * rooms.length)], x = r.x0 + Math.floor(rnd.next() * (r.x1 - r.x0 + 1)), y = r.y0 + Math.floor(rnd.next() * (r.y1 - r.y0 + 1)); if (open(x, y)) shafts.push([x, y]); } }
    return { out, shafts }; };
  const cache = new WeakMap(), get = (fl) => { let c = cache.get(fl); if (!c) { c = plan(fl); cache.set(fl, c); } return c; };
  const day = (game) => !(CM.isNight && CM.isNight(game));
  { const ls0 = CM.lifeSprites; CM.lifeSprites = (game, fl, now) => { const out = ls0 ? ls0(game, fl, now) : []; if (!fl || !fl.rooms || !(fl.number >= 1) || fl.number % 1 !== 0 || fl.special === "vault" || !CM.renderer || CM.renderer.index["ce:beam"] === undefined) return out;
      const c = get(fl), t = now / 1000, still = CM.reducedMotion, near = (x, y) => Math.abs(x - fl.pos[0]) + Math.abs(y - fl.pos[1]) <= 9;
      for (const s of c.out) if (near(s.x, s.y)) { const o = Object.assign({}, s), hi = CM.ceilAt ? CM.ceilAt(fl, s.x, s.y) - CM.floorAt(fl, s.x, s.y) - 1 : 0; o.lift = (o.lift || 0) + hi; if (s.chain) { o.lift = 1 - s.h + hi; if (!still) o.dx += Math.sin(t * 0.8 + s.x * 3 + s.y) * 0.015; } out.push(o); }
      if (day(game)) for (const [x, y] of c.shafts) if (near(x, y)) { out.push({ x, y, layer: "ce:shaft", w: 0.55, h: 1.0, glow: 2, alpha: 0.16 }); out.push({ x, y, layer: "ce:patch", flat: true, w: 0.8, glow: 1.6, alpha: 0.32 });
        if (!still) for (let i = 0; i < 4; i++) { const ph = (t * 0.08 + i / 4) % 1; out.push({ x, y, layer: "ce:patch", w: 0.015, h: 0.015, dx: Math.sin(t * 0.5 + i * 2) * 0.15, dz: Math.cos(t * 0.4 + i) * 0.15, lift: 0.95 - ph * 0.9, glow: 2, alpha: 0.8 }); } }
      return out; }; }
  { const xl0 = CM.extraLights; CM.extraLights = (game, fl, out, renderer) => { if (xl0) xl0(game, fl, out, renderer); if (!fl || !fl.rooms || !(fl.number >= 1) || fl.number % 1 !== 0 || fl.special === "vault" || !day(game)) return;
      for (const [x, y] of get(fl).shafts) { const d = Math.abs(x - fl.pos[0]) + Math.abs(y - fl.pos[1]); if (d <= 9) out.push({ x: x + 0.5, y: 0.95, z: y + 0.5, reach: 2.6, colour: [0.9, 0.85, 0.7], flicker: false, d }); } }; }
}
