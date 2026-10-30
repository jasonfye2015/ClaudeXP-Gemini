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
CM.GEN = 2;                                         // the generator a new run gets (CM.generators); a run keeps the one it began with
CM.SCHEMA = 3;                                      // the run's save format (1: whole floors, before v1.1; 2: floor deltas; 3: items with a base and a finding)

// the parts of a floor that never change once it is made (everything else is diffed against the fresh floor)
CM.FLOOR_FIXED = ["number", "grid", "dark", "rooms", "decor", "special", "hazard", "kinds", "ground", "canopy", "solidDefault", "glades", "ford"];

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
CM.restoreFloor = function (d, seed, gen, awakened) {
  const fl = CM.makeFloor(d.n, seed, gen || 1);
  if (awakened) CM.mirrorFloor(fl);
  const base = CM.snapshot(fl);
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
      floors[fl.number] = CM.floorDelta(fl, CM.snapshot(CM.makeFloor(fl.number, seed, 1)));
    }
    data.floors = floors;
    data.gen = 1;
    return data;
  },
  // 2 -> 3: every item carries its base id and where it was found (unknown, for the old ones)
  3(data) {
    for (const h of data.party || []) for (const slot of CM.SLOTS) if (h && h[slot]) CM.normalizeItem(h[slot]);
    for (const it of data.bag || []) CM.normalizeItem(it);
    return data;
  },
};
CM.migrateRun = function (data) {
  if (!data || typeof data !== "object") return data;
  let schema = data.schema || 1;
  while (schema < CM.SCHEMA) { schema += 1; if (CM.MIGRATIONS[schema]) CM.MIGRATIONS[schema](data); data.schema = schema; }
  return data;
};
CM.runFloor = (run) => { if (!run) return null; const n = typeof run.floor === "object" && run.floor ? run.floor.number : run.floor; return typeof n === "number" ? n : null; };   // the floor a saved run is on, in either format (0 is the town; null is no run)

// how much of the browser's keeping the game uses (bytes, as the browser counts them: two a character)
CM.store.used = function () {
  let n = 0;
  try { for (let i = 0; i < localStorage.length; i++) { const k = localStorage.key(i); if (k.startsWith("claudemagic.")) n += (k.length + (localStorage.getItem(k) || "").length) * 2; } } catch (e) { /* no storage */ }
  return n;
};

// the log, packed for the save: the common lines are one character each (a step, a turn, a tick), runs of the same
// character are counted, and anything else is JSON between bars
const SHORT = { "move,0": "f", "move,2": "b", "move,1": "r", "move,3": "l", "turn,1": ">", "turn,-1": "<", tick: ".", use: "u", travelStep: "s", autoTurn: "a", stopTravel: "x", closeBag: "c" };
const LONG = Object.fromEntries(Object.entries(SHORT).map(([k, v]) => [v, k.split(",").map((x, i) => (i ? Number(x) : x))]));
CM.packLog = function (log) {
  let out = "", last = "", run = 0;
  const flush = () => { if (run) out += run > 2 ? `${run}${last}` : last.repeat(run); run = 0; last = ""; };
  for (const line of log || []) {
    const c = SHORT[line.join(",")];
    if (c) { if (c === last) run++; else { flush(); last = c; run = 1; } }
    else { flush(); out += "|" + JSON.stringify(line) + "|"; }
  }
  flush();
  return out;
};
CM.unpackLog = function (text) {
  if (Array.isArray(text)) return text;
  const out = [];
  let i = 0, n = 0;
  while (i < (text || "").length) {
    const ch = text[i];
    if (ch === "|") { const j = text.indexOf("|", i + 1); out.push(JSON.parse(text.slice(i + 1, j))); i = j + 1; n = 0; }
    else if (ch >= "0" && ch <= "9") { n = n * 10 + Number(ch); i++; }
    else { const line = LONG[ch]; for (let k = 0; k < Math.max(1, n); k++) out.push(line.slice()); n = 0; i++; }
  }
  return out;
};

// ---- a run played again from its seed and its log: the same floors, the same dice, the same choices ----
// spec: {seed, gen, party, kit, difficulty, mutators, mode, log} (game.replaySpec()). Returns the game at the log's
// end. `upTo` stops after that many lines (the viewer scrubs with it).
CM.replayRun = function (spec, upTo) {
  const game = new CM.Game();
  game.replaying = 1;                                                  // (nothing is logged while it plays itself back)
  const gen = CM.GEN;
  CM.GEN = spec.gen || 1;
  const maxWas = CM.store.get("ascension", 0);
  if ((spec.ascension || 0) > (maxWas || 0)) CM.store.set("ascension", spec.ascension);   // (a replay may be from a higher rung than this browser has reached)
  try { game.newGame(spec.seed, spec.party || null, spec.kit, spec.difficulty, spec.mutators, spec.mode, { ascension: spec.ascension || 0, iron: spec.iron, town: Boolean(spec.town) }); } finally { CM.GEN = gen; CM.store.set("ascension", maxWas || 0); }
  game.gen = spec.gen || 1;
  const lines = upTo === undefined ? spec.log : spec.log.slice(0, upTo);
  for (const line of lines) {
    CM.replayStep(game, line);
    if (game.mode === "title") break;
  }
  game.replaying = 0;
  return game;
};

// one line of a log, played on a game
CM.replayStep = function (game, line) {
  {
    const [name, ...args] = line;
    switch (name) {
      case "tick": game.wanderMonsters(); break;
      case "act": game.act(args[0], args[1] === null ? undefined : args[1]); break;
      case "travelStep": game.travelStep(); break;
      case "offerBoons": game.offerBoons(game.party[args[0]]); break;
      case "chooseBoon": game.chooseBoon(game.party[args[0]], args[1]); break;
      case "choosePath": game.choosePath(game.party[args[0]], args[1]); break;
      case "setRow": game.setRow(game.party[args[0]], args[1]); break;
      case "equip": game.equip(game.party[args[0]], args[1]); break;
      case "chooseFamiliar": game.chooseFamiliar(game.party[args[0]], args[1]); break;
      case "secondCalling": game.secondCalling(args[0], args[1]); break;
      case "talk": { const t = game.floor.things[args[0]]; if (t) game.talk(t, args[0]); break; }
      case "drink": { const f = game.floor.features[CM.keyOf(...game.floor.pos)]; if (f) game.drink(f); break; }
      case "kneel": { const f = game.floor.features[CM.keyOf(...game.floor.pos)]; if (f) game.kneel(f); break; }
      case "openBag": game.openBag(Boolean(args[0])); break;
      case "autoFight": game.autoFight(Boolean(args[0])); break;
      case "travelTo": game.travelTo(args[0], args[1], Boolean(args[2])); break;
      case "hire": game.hire(args[0], args[1] === null ? undefined : args[1]); break;
      case "castOutside": game.castOutside(args[0], args[1], args[2] === null ? undefined : args[2]); break;
      default: if (typeof game[name] === "function") game[name](...args); break;
    }
  }
};

// a film: a run's spec with its packed log, as a code to hand on ("CM2:" and JSON); CM.parseFilm reads one back
CM.filmCode = function (spec) { return "CM2:" + JSON.stringify(Object.assign({}, spec, { log: CM.packLog(spec.log) })); };
CM.parseFilm = function (text) {
  const t = String(text || "").trim();
  if (!t.startsWith("CM2:")) return null;
  try { const spec = JSON.parse(t.slice(4)); if (!spec.seed || spec.log === undefined) return null; spec.log = CM.unpackLog(spec.log); return spec; } catch (e) { return null; }
};

// ---- a save, or a film, as a link: the text deflated and written base64url after #save= (or #film=) - nothing is
// stored anywhere but the link. Browsers without CompressionStream write it plain, under a different first letter. ----
CM.b64url = function (bytes) {
  let s = "";
  for (let i = 0; i < bytes.length; i += 8192) s += String.fromCharCode.apply(null, bytes.subarray(i, i + 8192));
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
};
CM.unb64url = function (text) {
  const s = atob(text.replace(/-/g, "+").replace(/_/g, "/") + "===".slice((text.length + 3) % 4));
  const out = new Uint8Array(s.length);
  for (let i = 0; i < s.length; i++) out[i] = s.charCodeAt(i);
  return out;
};
CM.toLink = async function (text) {
  const bytes = new TextEncoder().encode(text);
  if (typeof CompressionStream === "function") {
    try { const packed = new Uint8Array(await new Response(new Blob([bytes]).stream().pipeThrough(new CompressionStream("deflate-raw"))).arrayBuffer()); return "1" + CM.b64url(packed); } catch (e) { /* plain, below */ }
  }
  return "0" + CM.b64url(bytes);
};
CM.fromLink = async function (code) {
  code = String(code || "");
  const bytes = CM.unb64url(code.slice(1));
  if (code[0] === "0") return new TextDecoder().decode(bytes);
  if (code[0] !== "1" || typeof DecompressionStream !== "function") return null;
  try { return await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream("deflate-raw"))).text(); } catch (e) { return null; }
};
// what a page's #fragment carries: {kind: "save" | "film", code} or null
CM.linkPayload = function (hash) {
  const m = /^#(save|film)=([A-Za-z0-9_-]+)$/.exec(String(hash || "").trim());
  return m ? { kind: m[1], code: m[2] } : null;
};
