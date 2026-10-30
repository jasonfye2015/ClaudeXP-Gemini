"use strict";
// Saving, the small way: a floor is CM.makeFloor(number, seed) plus what the party did to it. The run keeps only
// that - the doors opened, the chests taken, the monsters moved or slain, the squares seen - and the floor is made
// again from the seed and the changes laid back over it. A hundred floors fit where one used to.
//
// This asks one thing of the generator: a seed must make the same floor in every version of the game. New things
// a later version puts on a floor take their dice from a hash of their own (`${seed}:craft:${number}:${k}`, as the
// gems, the riddles and the plates do), never from the floor's own random, so the floors already laid out stay as
// they were. CM.GEN says which generator wrote a save; a floor whose fingerprint has changed is still loaded, with
// a word in the log.
CM.GEN = 1;
CM.SCHEMA = 2;                                      // the run's save format (1: whole floors, before v1.1)

// the parts of a floor that never change once it is made (everything else is diffed against the fresh floor)
CM.FLOOR_FIXED = ["number", "grid", "dark", "rooms", "decor", "special", "hazard"];

// a seen-list ([x, y] pairs) as a bitset, base64 - and back
CM.packSeen = function (seen, size) {
  const bytes = new Uint8Array(Math.ceil((size * size) / 8));
  for (const [x, y] of seen) { if (x >= 0 && y >= 0 && x < size && y < size) { const i = y * size + x; bytes[i >> 3] |= 1 << (i & 7); } }
  let s = "";
  for (const b of bytes) s += String.fromCharCode(b);
  return btoa(s);
};
CM.unpackSeen = function (text, size) {
  const out = [];
  if (!text) return out;
  const s = atob(text);
  for (let i = 0; i < size * size; i++) if (s.charCodeAt(i >> 3) & (1 << (i & 7))) out.push([i % size, Math.floor(i / size)]);
  return out;
};

// a floor's things and features, each as text, to tell later what changed
const stripAnim = (t) => { if (t && t.anim) { const c = Object.assign({}, t); delete c.anim; return c; } return t; };
const textOf = (map) => { const out = {}; for (const k of Object.keys(map || {})) out[k] = JSON.stringify(stripAnim(map[k])); return out; };
CM.snapshot = function (fl) {
  return { things: textOf(fl.things), features: textOf(fl.features), grid: fl.grid.map((row) => row.join("")), fp: CM.floorPrint(fl) };
};
// the fresh floor's fingerprint: the walls, the furniture and the way down - not the chests and the monsters, which a
// later version may add to by its own hashes without the floor having moved
CM.floorPrint = function (fl) {
  const fixed = Object.keys(fl.things).filter((k) => ["ladder", "stairs_up", "boss", "guardian", "phylactery"].includes(fl.things[k].type)).sort();
  return CM.hashSeed(fl.grid.map((r) => r.join("")).join("|") + "#" + fixed.join(",") + "#" + Object.keys(fl.features).sort().join(","));
};

// what the party did to a floor, against the snapshot of the fresh one
CM.floorDelta = function (fl, base) {
  const d = { n: fl.number, pos: fl.pos.slice(), facing: fl.facing, seen: CM.packSeen(fl.seen || [], fl.grid.length), fp: base.fp, things: {}, features: {}, grid: [] };
  const now = { things: textOf(fl.things), features: textOf(fl.features) };
  for (const part of ["things", "features"]) {
    for (const k of Object.keys(now[part])) if (now[part][k] !== base[part][k]) d[part][k] = JSON.parse(now[part][k]);
    for (const k of Object.keys(base[part])) if (!(k in now[part])) d[part][k] = null;
  }
  for (let y = 0; y < fl.grid.length; y++) {
    const row = fl.grid[y].join("");
    if (row === base.grid[y]) continue;
    for (let x = 0; x < row.length; x++) if (row[x] !== base.grid[y][x]) d.grid.push([x, y, fl.grid[y][x]]);
  }
  for (const k of Object.keys(fl)) if (!CM.FLOOR_FIXED.includes(k) && !["pos", "facing", "seen", "things", "features"].includes(k)) (d.x = d.x || {})[k] = fl[k];
  return d;
};

// the floor again, from the seed and the changes; returns {floor, base, drifted}
CM.restoreFloor = function (d, seed) {
  const fl = CM.makeFloor(d.n, seed), base = CM.snapshot(fl);
  const drifted = d.fp !== undefined && d.fp !== base.fp;
  for (const part of ["things", "features"]) for (const [k, v] of Object.entries(d[part] || {})) { if (v === null) delete fl[part][k]; else fl[part][k] = v; }
  for (const [x, y, v] of d.grid || []) if (fl.grid[y] && x < fl.grid[y].length) fl.grid[y][x] = v;
  fl.seen = CM.unpackSeen(d.seen, fl.grid.length);
  fl.facing = d.facing === undefined ? fl.facing : d.facing;
  if (d.pos && CM.passable(fl, d.pos[0], d.pos[1])) fl.pos = d.pos.slice();
  Object.assign(fl, d.x || {});
  return { floor: fl, base, drifted };
};

// ---- the run's save, version by version: each step lifts a save one schema ----
CM.MIGRATIONS = {
  // 1 -> 2: whole floors become deltas; the floor the party stands on becomes its number
  2(data) {
    const seed = data.seed || "";
    const whole = Object.assign({}, data.floors || {});
    if (data.floor && typeof data.floor === "object") { whole[data.floor.number] = data.floor; data.floor = data.floor.number; }
    const floors = {};
    for (const fl of Object.values(whole)) {
      if (!fl || !fl.grid) continue;
      CM.upgradeFloor(fl);
      for (const t of Object.values(fl.things)) if (t.group) t.group.forEach(CM.upgradeMonster);
      floors[fl.number] = CM.floorDelta(fl, CM.snapshot(CM.makeFloor(fl.number, seed)));
    }
    data.floors = floors;
    data.gen = CM.GEN;
    return data;
  },
};
CM.migrateRun = function (data) {
  if (!data || typeof data !== "object") return data;
  let schema = data.schema || 1;
  while (schema < CM.SCHEMA) { schema += 1; if (CM.MIGRATIONS[schema]) CM.MIGRATIONS[schema](data); data.schema = schema; }
  return data;
};
CM.runFloor = (run) => (run ? (typeof run.floor === "object" ? run.floor.number : run.floor) : 0);   // the floor a saved run is on, in either format

// how much of the browser's keeping the game uses (bytes, as the browser counts them: two a character)
CM.store.used = function () {
  let n = 0;
  try { for (let i = 0; i < localStorage.length; i++) { const k = localStorage.key(i); if (k.startsWith("claudemagic.")) n += (k.length + (localStorage.getItem(k) || "").length) * 2; } } catch (e) { /* no storage */ }
  return n;
};
