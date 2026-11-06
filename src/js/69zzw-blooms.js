"use strict";
// The blooms and the drafts (UPGRADE_PLAN_63.md sets 2.2 and 3.1, release 4). The blooms: rain above over the last
// day (CM.bloomNow, 0..1) makes the damp bands' growth thick - the moss, the weeds and the fungus meshes denser by
// it - and, when it stands at half or more, puts out things of its own on the party's floor, once a bloom: glowcaps
// (a lit mushroom cluster on a wall-side square: a light the party can see by, pale green, two squares), spore
// patches (a pale patch on a square: a point of poison to each hero stepping through, never below one, said on the
// look line - never on the stairs, a doorway, a thing or a feature, never in a corridor one square wide, and only
// where every square reachable from the stairs stays reachable with the patch counted as a wall), both gone after
// a day. The drafts: a gale or a tornado above sends a draft down the shaft and along the corridors (CM.draftPath,
// the squares within twenty-five of the shaft by the walk): on them the torch may be snuffed for three steps (the
// gust's own guttering, 69v-weather.js - never the spell light), and the spore patches are blown one square along
// the draft every ten minutes, never onto the stairs, a thing, a feature or a dead end's last square.
//   CM.bloomNow(game) -> 0..1;  CM.bloomStep(game, minutes)  (wrapped into CM.tickClock)
//   CM.bloomsOf(fl) -> { glowcaps: ["x,y"], spores: ["x,y"] };  CM.glowcapNear(game) -> boolean
//   CM.draftNow(game) -> 0..1 on floors 1-4;  CM.draftPath(fl) -> Map "x,y" -> distance from the shaft
{ const skyOn = (game) => Boolean(game && game.tally && game.tally.ext && game.tally.ext.wx && game.tally.ext.wx.cur);   // (the sky is read only once the clock has made it: a fight's rules must not roll the weather's dice, or a run and its replay part)
  const B = CM.BLOOM = { bands: [0, 1, 4, 5, 9], from: 0.5, dayMinutes: 24 * 60, glowPer: 0.05, sporePer: 0.04, most: 10, bite: 1, lifeMinutes: 24 * 60, draftFloors: [1, 2, 3, 4], draftFrom: 0.7, draftReach: 25, snuffPerStep: 0.08, blowEvery: 10 };
  const rnd = () => (CM.wxRandom ? CM.wxRandom() : Math.random());
  const rain = (e) => e && (e.kind === "rain" || e.kind === "storm");
  CM.bloomNow = (game) => { if (!game || !game.ext || !skyOn(game)) return 0; const W = CM.weatherStep(game); if (!W || !W.cur) return 0; const t = CM.clockOf(game), now = CM.weatherNow(game); let b = rain(W.cur) ? Math.min(1, 0.5 + 0.5 * now.strength) : 0;
    if (W.prev && rain(W.prev)) b = Math.max(b, Math.min(1, W.prev.strength) * Math.max(0, 1 - (t - W.prev.until) / B.dayMinutes)); return Math.round(b * 100) / 100; };
  CM.bloomsOf = (fl) => { const out = { glowcaps: [], spores: [] }; for (const [k, t] of Object.entries((fl && fl.things) || {})) { if (t.type === "glowcap") out.glowcaps.push(k); else if (t.type === "spores") out.spores.push(k); } return out; };
  const stairsOf = (fl) => { for (const [k, t] of Object.entries(fl.things)) if (t.type === "ladder" || t.type === "stairs_up") return k.split(",").map(Number); return fl.pos; };
  const inRoom = (fl, x, y) => (fl.rooms || []).some((r) => x >= r.x0 && x <= r.x1 && y >= r.y0 && y <= r.y1);
  const wayHolds = (fl, key) => { const S = stairsOf(fl), before = CM.distances(fl.grid, S, (x, y) => CM.passable(fl, x, y)), after = CM.distances(fl.grid, S, (x, y) => CM.passable(fl, x, y) && `${x},${y}` !== key); for (const k of before.keys()) if (k !== key && !after.has(k)) return false; return true; };
  const okFloor = (fl) => fl && fl.number >= 1 && fl.grid && !["joker", "interior", "cave"].includes(fl.special) && B.bands.includes(CM.themeIndex(fl.number));
  const sprout = (game, fl) => { const N = fl.grid.length, open = (x, y) => x >= 0 && y >= 0 && x < N && y < N && fl.grid[y][x] === 0, S = stairsOf(fl); let glow = 0, spores = 0;
    for (let y = 1; y < N - 1; y++) for (let x = 1; x < N - 1; x++) { if (!open(x, y)) continue; const k = `${x},${y}`; if (fl.things[k] || (fl.features || {})[k] || (Math.abs(x - fl.pos[0]) + Math.abs(y - fl.pos[1]) <= 1) || (Math.abs(x - S[0]) + Math.abs(y - S[1]) <= 1)) continue;
      const walls = CM.DIRS.filter(([dx, dy]) => !open(x + dx, y + dy)).length, narrow = (!open(x - 1, y) && !open(x + 1, y)) || (!open(x, y - 1) && !open(x, y + 1)), h = CM.hashSeed(`${game.seed}:bloom:${fl.number}:${k}:${CM.dayOf(game)}`) >>> 0;
      if (walls && glow < B.most && (h % 1000) / 1000 < B.glowPer) { fl.things[k] = { type: "glowcap", at: CM.clockOf(game) }; glow++; continue; }
      if (!narrow && !inRoom(fl, x, y) === false && spores < B.most && ((h >> 10) % 1000) / 1000 < B.sporePer && wayHolds(fl, k)) { fl.things[k] = { type: "spores", at: CM.clockOf(game) }; spores++; } }
    return { glow, spores }; };
  CM.bloomStep = (game, minutes = 1) => { if (!game || !game.ext || !game.floor || !(minutes > 0)) return; const fl = game.floor, t = CM.clockOf(game), E = game.ext("bloom"), b = CM.bloomNow(game), q = Math.round(b * 4);
    if (E.q !== q) { E.q = q; game.plantsVersion = (game.plantsVersion || 0) + 1; }   // (the meshes' density follows the bloom)
    for (const [k, th] of Object.entries(fl.things)) if ((th.type === "glowcap" || th.type === "spores") && t - (th.at || 0) >= B.lifeMinutes) { delete fl.things[k]; game.plantsVersion = (game.plantsVersion || 0) + 1; }
    if (okFloor(fl) && b >= B.from) { const key = `${fl.number}:${CM.dayOf(game)}`; if (E.last !== key) { E.last = key; const n = sprout(game, fl); if (n.glow || n.spores) game.say(`The damp has brought the walls out in growth: ${n.glow ? "glowcaps, pale green in the dark" : ""}${n.glow && n.spores ? ", and " : ""}${n.spores ? "patches of spore that are best walked round" : ""}.`); } }
    // the draft: the spore patches blown along it
    const d = CM.draftNow(game); if (d > 0) { E.blow = (E.blow || 0) + minutes; while (E.blow >= B.blowEvery) { E.blow -= B.blowEvery; const path = CM.draftPath(fl), S = stairsOf(fl), open = (x, y) => fl.grid[y] && fl.grid[y][x] === 0;
        for (const k of CM.bloomsOf(fl).spores) { const [x, y] = k.split(",").map(Number); if (!path.has(k)) continue; const here = path.get(k); const next = CM.DIRS.map(([dx, dy]) => [x + dx, y + dy]).filter(([nx, ny]) => open(nx, ny) && path.has(`${nx},${ny}`) && path.get(`${nx},${ny}`) > here && !fl.things[`${nx},${ny}`] && !(fl.features || {})[`${nx},${ny}`] && !(nx === S[0] && ny === S[1]) && CM.DIRS.filter(([ddx, ddy]) => open(nx + ddx, ny + ddy)).length > 1)[0];
          if (next) { fl.things[`${next[0]},${next[1]}`] = fl.things[k]; delete fl.things[k]; game.plantsVersion = (game.plantsVersion || 0) + 1; } } } } };
  { const t0 = CM.tickClock; CM.tickClock = (game, minutes) => { t0(game, minutes); if (game && game.ext) CM.bloomStep(game, minutes); }; }
  CM.glowcapNear = (game) => { const fl = game && game.floor; if (!fl || !fl.pos) return false; for (const k of CM.bloomsOf(fl).glowcaps) { const [x, y] = k.split(",").map(Number); if (Math.abs(x - fl.pos[0]) + Math.abs(y - fl.pos[1]) <= 1) return true; } return false; };
  const P = CM.Game.prototype;
  { const h0 = P.hasLight; P.hasLight = function (...a) { return h0.apply(this, a) || CM.glowcapNear(this); }; }   // (a glowcap beside the party is light to see by)
  { const ar0 = P.arrive; P.arrive = function (f, k) { return ar0.call(this, f, k); }; }
  // the spores underfoot: the step's own look (the move's thing branch has no words for them: they come here)
  { const mv0 = P.move; P.move = function (rel) { const fl = this.floor, before = fl && fl.pos ? fl.pos.slice() : null; let out; const say0 = this.say; this.say = function (t) { if (t !== undefined) return say0.call(this, t); }; try { out = mv0.call(this, rel); } finally { delete this.say; }
      if (!fl || !fl.pos || this.floor !== fl || !before || (before[0] === fl.pos[0] && before[1] === fl.pos[1])) return out; const k = `${fl.pos[0]},${fl.pos[1]}`, th = fl.things[k];
      if (th && th.type === "spores") { let bit = 0; for (const h of this.alive()) if (h.hp > 1) { h.hp = Math.max(1, h.hp - B.bite); bit++; } this.sound("trap"); this.say(bit ? `Spores rise about the party's knees in a pale cloud: a point of sickness each (-${B.bite}).` : "Spores rise in a pale cloud, and find nothing left to sicken."); }
      else if (th && th.type === "glowcap") this.say("A cluster of glowcaps grows from the wall's foot, pale green: light enough to see by.");
      return out; }; }
  // the draft
  CM.draftNow = (game) => { const fl = game && game.floor; if (!fl || !B.draftFloors.includes(fl.number) || !game.ext || !skyOn(game)) return 0; const W = CM.aboveNow(game); return Math.max(0, Math.min(1, (W.wind.speed - B.draftFrom) / (1 - B.draftFrom))) * ({ 1: 1, 2: 0.8, 3: 0.55, 4: 0.3 }[fl.number] || 0); };
  const paths = new WeakMap();
  CM.draftPath = (fl) => { let M = paths.get(fl); if (M) return M; const S = stairsOf(fl), D = CM.distances(fl.grid, S, (x, y) => fl.grid[y] && fl.grid[y][x] === 0); M = new Map(); for (const [k, d] of D) { const [x, y] = k.split(",").map(Number); if (d <= B.draftReach && !inRoom(fl, x, y)) M.set(k, d); } paths.set(fl, M); return M; };
  { const b0 = P.burn; P.burn = function (...a) { const fl = this.floor; if (fl && this.mode === "explore" && !(this.gutter > 0) && !(this.spellLight > 0) && this.light && this.light.kind === "torch" && !this.lightOut) { const d = CM.draftNow(this); if (d > 0 && CM.draftPath(fl).has(`${fl.pos[0]},${fl.pos[1]}`) && rnd() < B.snuffPerStep * d) { this.gutter = (CM.WEATHERPLAY && CM.WEATHERPLAY.gutterSteps) || 3; this.say("A draft comes howling down the corridor and the torch goes out. A few steps, a hand cupped round it, and it will light again."); } }
      return b0.apply(this, a); }; }
}
