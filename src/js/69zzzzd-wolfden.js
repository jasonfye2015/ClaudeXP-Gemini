"use strict";
// The wolf den (UPGRADE_PLAN_77.md). West of the river, south of the west glade, a low crag of grey rock rises out of
// the trees with a real cave in its face - an open, dark mouth, no door - and a small trodden clearing before it, reached
// on foot from the glade. A pack lives there: two alphas, five grown wolves, four pups, in coats of grey, black, brown,
// tawny and pale. By day they range through the forest round the den - between the trees, not on the paths - and at
// dusk they go home and in, one after another, to sleep. They are wild, not hostile: wary of people, they keep their
// distance (the Wood's own wolves by night are another matter). The pack itself is the window's (77q-wolfpack.js);
// here are the den, its name, and its place on the map.
//   CM.WOLF_DEN; CM.layWolfDen(fl); CM.WOLF_PACK (the eleven: role, size, coat)
{ const D = CM.WOLF_DEN = { crag: [4, 46, 8, 48], mouth: [6, 46], front: [6, 45], clearing: [1, 41, 11, 45], centre: [6, 44], range: 15 };
  const key = (x, y) => `${x},${y}`;
  CM.isDenCell = (x, y) => x >= D.crag[0] && x <= D.crag[2] && y >= D.crag[1] && y <= D.crag[3];
  CM.WOLF_PACK = [
    { role: "alpha", size: 1.18, coat: "grey" }, { role: "alpha", size: 1.14, coat: "black" },
    { role: "adult", size: 0.95, coat: "brown" }, { role: "adult", size: 0.92, coat: "grey" }, { role: "adult", size: 0.93, coat: "tawny" }, { role: "adult", size: 0.9, coat: "pale" }, { role: "adult", size: 0.94, coat: "black" },
    { role: "pup", size: 0.5, coat: "grey" }, { role: "pup", size: 0.48, coat: "tawny" }, { role: "pup", size: 0.5, coat: "black" }, { role: "pup", size: 0.47, coat: "pale" } ];
  // its own rock: rounded boulders and moss, not the layered crag; and a mouth with no light in it (the window paints them)
  Object.assign(CM.SOLID, { denrock: { face: "solid:denrock", h: 1.75, top: "ground:grass" }, denrocktall: { face: "solid:denrock", h: 2.35, top: "ground:grass" }, denrocklow: { face: "solid:denrock", h: 1.05, top: "ground:grass" }, denmouth: { face: "solid:denmouth", h: 1.75, top: "ground:grass" } });
  if (CM.SOLID_COLOURS) Object.assign(CM.SOLID_COLOURS, { denrock: "#6A6660", denrocktall: "#6A6660", denrocklow: "#6A6660", denmouth: "#1A1612" });
  // natural rocks about the crag - along its front, at its ends, over its top - so it reads as an outcrop, not a block
  { const pi0 = CM.plantInstancesOf; if (pi0) CM.plantInstancesOf = (game, fl, at, reach, density) => { const out = pi0(game, fl, at, reach, density); if (!fl || fl.number !== -1 || !(density > 0)) return out;
      const M = (CM.plantsPack && CM.plantsPack.manifest && CM.plantsPack.manifest.models) || {}, [ax, ay] = at || fl.pos; if (Math.abs(ax - D.mouth[0]) + Math.abs(ay - D.mouth[1]) > (reach || 12) + 4) return out;
      const put = (name, x, z, y, size, salt) => { const m = M[name]; if (!m) return; const lo = m.box[0], hi = m.box[1], w = Math.max(1e-3, hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]), sc = size * 0.62 / w, hh = CM.hashSeed(`den:${salt}`);
        out.push({ model: name, x: x - (lo[0] + hi[0]) / 2 * sc, y: y - lo[1] * sc, z: z - (lo[2] + hi[2]) / 2 * sc, yaw: (hh % 360) * Math.PI / 180, scale: sc, sway: 0, height: (hi[1] - lo[1]) * sc, shade: 0.62, kind: "rock" }); };
      const H = (x) => (x === D.crag[0] || x === D.crag[2] ? 1.05 : Math.abs(x - D.mouth[0]) <= 1 ? 2.35 : 1.75), [x0, y0, x1, y1] = D.crag;
      for (let x = x0; x <= x1; x++) { if (x !== D.mouth[0]) put(x % 2 ? "rock1" : "rock2", x + 0.5, y0 + 0.08, 0, 0.95 + (x % 3) * 0.12, `front${x}`); put(x % 2 ? "rock2" : "rock1", x + 0.5, y0 + 0.55, H(x) - 0.18, 0.9, `top${x}`); put("rock1", x + 0.5, y0 + 1.6, H(x) - 0.12, 1.1, `back${x}`); }
      for (const [x, s] of [[x0 - 0.15, 1.1], [x1 + 1.15, 1.0]]) for (let y = y0; y <= y1; y++) put("rock2", x, y + 0.5, 0, s, `end${x}:${y}`);
      put("rock1", D.mouth[0] - 0.05, y0 + 0.1, 1.55, 0.7, "lintel"); put("rock2", D.mouth[0] + 1.05, y0 + 1.1, 2.2, 0.8, "crown");
      return out; }; }
  CM.layWolfDen = function (fl) { const [x0, y0, x1, y1] = D.clearing, [cx, cy] = D.centre;
    const open = (x, y, g) => { if (!fl.grid[y] || x < 0 || x >= fl.grid.length) return; fl.grid[y][x] = 0; if (fl.kinds) delete fl.kinds[key(x, y)]; (fl.ground = fl.ground || {})[key(x, y)] = g; };
    for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) if (((x - cx) / 5.2) ** 2 + ((y - cy) / 2.6) ** 2 <= 1 && !CM.isDenCell(x, y) && !fl.things[key(x, y)]) open(x, y, (x * 7 + y * 3) % 5 ? "litter" : "dirt");
    for (const [x, y] of [[4, 42], [5, 42], [6, 42], [6, 43]]) if (!fl.things[key(x, y)]) open(x, y, "dirt");   // (the way in from the glade: trodden earth)
    for (let y = D.crag[1]; y <= D.crag[3]; y++) for (let x = D.crag[0]; x <= D.crag[2]; x++) { fl.grid[y][x] = 1; (fl.kinds = fl.kinds || {})[key(x, y)] = x === D.mouth[0] && y === D.mouth[1] ? "denmouth" : x === D.crag[0] || x === D.crag[2] ? "denrocklow" : y > D.crag[1] && Math.abs(x - D.mouth[0]) <= 1 ? "denrocktall" : "denrock"; if (fl.ground) delete fl.ground[key(x, y)]; delete fl.things[key(x, y)]; }
    fl.decor = (fl.decor || []).filter((d) => !(d.x >= x0 && d.x <= x1 && d.y >= y0 && d.y <= y1));
    fl.rooms = (fl.rooms || []).concat({ x0, y0, x1, y1, name: "The wolf den" });
    fl.things[key(...D.front)] = fl.things[key(...D.front)] || { type: "wolfden" };
    return fl; };
  { const lc0 = CM.layCabin; CM.layCabin = function (fl) { const out = lc0 ? lc0.call(this, fl) : fl; return CM.layWolfDen(out || fl); }; }
  { const wp0 = CM.woodPlace; CM.woodPlace = function (fl, x, y) { if (fl && fl.number === -1) { const [x0, y0, x1, y1] = D.clearing; if (x >= x0 && x <= x1 && y >= y0 && y <= y1 && fl.grid[y] && fl.grid[y][x] === 0) return "the wolf den"; } return wp0.call(this, fl, x, y); }; }
  { const wy0 = CM.wayPlaces; CM.wayPlaces = function (game) { const out = wy0(game), fl = game.floor; if (fl && fl.number === -1 && (fl.seen || []).some(([x, y]) => x === D.front[0] && y === D.front[1]) && !(fl.pos[0] === D.front[0] && fl.pos[1] === D.front[1])) { const p = game.pathTo(...D.front); out.push({ name: "The wolf den", x: D.front[0], y: D.front[1], steps: p ? p.length : null }); } return out; }; }
  // what you see and hear at the mouth
  const P = CM.Game.prototype;
  const words = (g) => { const h = CM.hourOf ? CM.hourOf(g) : 12; return h >= 20 || h < 6 ? "The cave's mouth is dark and very still. From somewhere inside comes slow breathing - a lot of it - and once, a pup's small whine, hushed." : h < 8 ? "The den's mouth, and a smell of wolf. Paw-prints going out, fresh, all over the trodden earth." : h >= 18 ? "The den's mouth. The prints in the earth are coming home." : "A low crag with a dark cave in its face, the earth before it trodden bare. Bones, a little fur on the rock. The den is empty by day: the pack is out in the forest."; };
  { const u0 = P.use; P.use = function (...a) { const fl = this.floor; if (this.mode === "explore" && fl && fl.number === -1) { const [dx, dy] = CM.DIRS[fl.facing]; for (const k of [key(...fl.pos), key(fl.pos[0] + dx, fl.pos[1] + dy)]) if (fl.things[k] && fl.things[k].type === "wolfden") { this.say(words(this)); return true; } } return u0.apply(this, a); }; }
  { const l0 = P.look; P.look = function (...a) { const out = l0.apply(this, a), fl = this.floor; if (this.mode === "explore" && fl && fl.number === -1) { const [dx, dy] = CM.DIRS[fl.facing], t = fl.things[key(fl.pos[0] + dx, fl.pos[1] + dy)] || fl.things[key(...fl.pos)]; if (t && t.type === "wolfden") this.say(`${words(this)} (Space)`); } return out; }; }
}
