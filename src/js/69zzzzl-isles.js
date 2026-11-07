"use strict";
// The island dungeons (UPGRADE_PLAN_81.md), the engine every island shares. An island is a landing - a small place in
// the open air where the Wren puts in, with the dungeon's mouth on it - and forty floors below, in four bands of ten,
// each band its own look and its own creatures. The floors are carved by the shaft's own generator from keys of their
// own (no floor of the shaft moves) and made the island's: its stairs, its creatures, standing water where the band is
// wet; a guardian before the stair down on every tenth floor, the island's master on the fortieth; and at the head of
// each band below the first a stone that carries the party back up to the landing, after which the mouth can take
// them straight down to that band again. Saved under numbers of their own: an island's landing at its base (Gull Rock
// -100), its floors below that (-101 to -140). The islands themselves are in their own files (69zzzzm-gullrock.js ...).
//   CM.ISLES; CM.isleOf(n) -> { isle, depth }; CM.isIsleFloor(n); CM.isIsleLanding(n); CM.isleFloorName(n)
//   an island: { id, base, name, deep, levels: [first, last], bands: [{ name, theme, kinds, wet }], guardians: [g10, g20, g30, master],
//                landingTheme, makeLanding(n, seed), mouth: [x, y], jetty: [x, y], arrive, words }
{ const P = CM.Game.prototype, key = (x, y) => `${x},${y}`;
  CM.ISLES = CM.ISLES || {}; CM.ISLE_DEPTH = 40;
  CM.isleOf = (n) => { if (typeof n !== "number" || n % 1 !== 0 || n > -100) return null; for (const I of Object.values(CM.ISLES)) { const d = I.base - n; if (d >= 0 && d <= CM.ISLE_DEPTH) return { isle: I, depth: d }; } return null; };
  CM.isIsleFloor = (n) => { const o = CM.isleOf(n); return Boolean(o && o.depth >= 1); };
  CM.isIsleLanding = (n) => { const o = CM.isleOf(n); return Boolean(o && o.depth === 0); };
  CM.isleBand = (I, d) => I.bands[Math.min(I.bands.length - 1, Math.floor((Math.max(1, d) - 1) / 10))];
  CM.isleLevel = (I, d) => Math.round(I.levels[0] + (I.levels[1] - I.levels[0]) * (Math.max(1, d) - 1) / (CM.ISLE_DEPTH - 1));
  CM.isleFloorName = (n) => { const o = CM.isleOf(n); if (!o) return null; if (!o.depth) return o.isle.name; return `${o.isle.deep}, ${CM.isleBand(o.isle, o.depth).name.replace(/^The /, "the ")} - floor ${o.depth}`; };
  // the looks: a band's theme below, the landing's in the open air; the band a main band's look is borrowed from
  { const tf0 = CM.themeFor; CM.themeFor = (n) => { const o = CM.isleOf(n); if (!o) return tf0(n); return o.depth ? CM.isleBand(o.isle, o.depth).theme : o.isle.landingTheme; }; }
  { const ti0 = CM.themeIndex; CM.themeIndex = (n) => { const o = CM.isleOf(n); if (o && o.depth) { const T = CM.isleBand(o.isle, o.depth).theme; return T.like === undefined ? 0 : T.like; } return ti0(n); }; }
  { const d0 = CM.isDeep; CM.isDeep = (n) => CM.isIsleFloor(n) || d0(n); }
  // the floors
  const NONKEY = []; for (let r = 2; r < CM.LAST_FLOOR; r++) if (!CM.isKeyFloor(r) && !(CM.CAMP_FLOORS || []).includes(r)) NONKEY.push(r);
  const KEEP = ["chest", "key", "strongbox", "boxkey", "node", "vein", "breakable", "monsters"];
  CM.isleGroup = (I, d, rnd, n) => { const band = CM.isleBand(I, d), level = CM.isleLevel(I, d), kinds = band.kinds.map((k) => CM.monsterKind(k)).filter(Boolean), kind = rnd.pick(kinds), group = [];
    const count = Math.max(1, Math.min(5, n || rnd.int(1, 2 + Math.floor(d / 12)))); for (let j = 0; j < count; j++) group.push(CM.makeMonster(kind, level, rnd));
    if (count >= 2 && kinds.length > 1 && rnd.chance(0.35)) { const other = rnd.pick(kinds.filter((k) => k !== kind)); for (let j = Math.floor(count / 2); j < count; j++) group[j] = CM.makeMonster(other, level, rnd); }
    if (rnd.chance(0.12) && CM.makeElite) CM.makeElite(group, rnd, 2); return group; };
  CM.isleGuardianGroup = (I, id, d, rnd) => { const G = CM.GUARDIANS[id], level = CM.isleLevel(I, d), group = [CM.guardianMonster(id, 0)]; for (const name of G.escorts || []) group.push(CM.makeMonster(CM.monsterKind(name), level, rnd)); return group; };
  CM.makeIsleFloor = function (n, seed) { const { isle: I, depth: d } = CM.isleOf(n), band = CM.isleBand(I, d), L = NONKEY[Math.min(NONKEY.length - 1, Math.floor((d - 1) * NONKEY.length / CM.ISLE_DEPTH))];
    const fl = CM.makeFloor(L, `${seed}:isle:${I.id}:${d}`, 2), rnd = new CM.Random(CM.hashSeed(`${seed}:islegroups:${I.id}:${d}`));
    fl.number = n; fl.special = "isle"; fl.isle = I.id; fl.hazard = null; delete fl.wing; delete fl.landmark; delete fl.raised;
    for (const [k, t] of Object.entries(fl.things)) { if (t.type === "stairs_up") fl.things[k] = { type: "isleup" }; else if (["ladder", "boss", "guardian"].includes(t.type)) fl.things[k] = { type: "isledown" }; else if (!KEEP.includes(t.type)) delete fl.things[k]; }
    for (const [k, f] of Object.entries(fl.features)) if (["teleporter", "spinner", "trapdoor", "pit", "carving"].includes(f.type)) delete fl.features[k];
    if (!Object.values(fl.things).some((t) => t.type === "isleup")) fl.things[key(...fl.pos)] = { type: "isleup" };
    if (!Object.values(fl.things).some((t) => t.type === "isledown")) { const far = CM.distances(fl.grid, fl.pos, (x, y) => CM.isOpen(fl, x, y)); const best = [...far.entries()].filter(([k]) => !fl.things[k] && !fl.features[k]).sort((a, b) => b[1] - a[1])[0]; if (best) fl.things[best[0]] = { type: "isledown" }; }
    for (const k of Object.keys(fl.things).sort()) { const t = fl.things[k]; if (t.type !== "monsters") continue; fl.things[k] = { type: "monsters", group: CM.isleGroup(I, d, rnd, Array.isArray(t.group) ? t.group.length : 0), asleep: t.asleep }; }
    if (band.wet) { const cells = []; for (let y = 1; y < fl.grid.length - 1; y++) for (let x = 1; x < fl.grid.length - 1; x++) { const k = key(x, y); if (fl.grid[y][x] === 0 && !fl.things[k] && !fl.features[k] && CM.hashSeed(`${seed}:islewet:${I.id}:${d}:${k}`) % 100 < band.wet) cells.push({ kind: "water", x, y }); } fl.decor = (fl.decor || []).concat(cells); }
    const down = Object.keys(fl.things).find((k) => fl.things[k].type === "isledown"), [dx, dy] = down.split(",").map(Number);
    if (d % 10 === 0) { const id = I.guardians[d / 10 - 1], G = CM.GUARDIANS[id];
      if (d === CM.ISLE_DEPTH) { fl.things[down] = { type: "guardian", group: CM.isleGuardianGroup(I, id, d, rnd) }; }
      else { const near = CM.distances(fl.grid, [dx, dy], (x, y) => CM.isOpen(fl, x, y)), spot = [...near.entries()].filter(([k, dd]) => dd >= 1 && dd <= 3 && !fl.things[k] && !fl.features[k]).sort((a, b) => a[1] - b[1] || (a[0] < b[0] ? -1 : 1))[0];
        if (spot && G) fl.things[spot[0]] = { type: "guardian", group: CM.isleGuardianGroup(I, id, d, rnd) }; } }
    if (d % 10 === 1 && d > 1) { const up = Object.keys(fl.things).find((k) => fl.things[k].type === "isleup"), [ux, uy] = up.split(",").map(Number); const spot = CM.DIRS.map(([ax, ay]) => [ux + ax, uy + ay]).find(([x, y]) => CM.isOpen(fl, x, y) && !fl.things[key(x, y)] && !fl.features[key(x, y)]); if (spot) fl.things[key(...spot)] = { type: "islestone" }; }
    if (d === CM.ISLE_DEPTH) { const spot = CM.DIRS.map(([ax, ay]) => [dx + ax, dy + ay]).find(([x, y]) => CM.isOpen(fl, x, y) && !fl.things[key(x, y)] && !fl.features[key(x, y)]); if (spot) fl.things[key(...spot)] = { type: "islestone" }; }
    return fl; };
  { const mf0 = CM.makeFloor; CM.makeFloor = function (n, seed, gen) { const o = CM.isleOf(n); if (!o) return mf0.call(this, n, seed, gen); return o.depth ? CM.makeIsleFloor(n, seed) : o.isle.makeLanding(n, seed); }; }
  // the ways: down, up, the stones, the mouth
  const cellOf = (fl, type) => { const k = Object.keys(fl.things).find((kk) => fl.things[kk].type === type); return k ? k.split(",").map(Number) : null; };
  const R = (g, I) => { const E = g.ext("isles"); return (E[I.id] = E[I.id] || { bands: [1], deepest: 0 }); };
  P.isleGo = function (n, at, words) { const fl = this.floorAt(n); let pos = Array.isArray(at) ? at : cellOf(fl, at) || fl.pos; this.enterFloor(n, "rope", pos.slice()); const o = CM.isleOf(n);
    if (o && o.depth) { const r = R(this, o.isle); r.deepest = Math.max(r.deepest, o.depth); const V = this.vext("isles"); V[o.isle.id] = Math.max(V[o.isle.id] || 0, o.depth); }
    if (words) this.say(words); this.emit("change"); return true; };
  P.isleWay = function (t) { const fl = this.floor, o = CM.isleOf(fl.number); if (!o) return false; const I = o.isle, d = o.depth;
    if (t.type === "isledown") { const band = CM.isleBand(I, d + 1); return this.isleGo(fl.number - 1, "isleup", d % 10 === 0 ? `Down, into ${band.name.replace(/^The /, "the ")}. ${band.words || ""}`.trim() : `Down: floor ${d + 1}.`); }
    if (t.type === "isleup") return d === 1 ? this.isleGo(I.base, I.mouthFront, `Up the stair and out into the air: ${I.name}.`) : this.isleGo(fl.number + 1, "isledown", `Up: floor ${d - 1}.`);
    if (t.type === "islestone") { const r = R(this, I), start = d === CM.ISLE_DEPTH ? 31 : d; if (!r.bands.includes(start)) r.bands.push(start); r.bands.sort((a, b) => a - b);
      return this.isleGo(I.base, I.mouthFront, `You lay a hand on the stone, and the dark folds: you stand at the mouth again, in the open air of ${I.name}. The way down to ${CM.isleBand(I, start).name.replace(/^The /, "the ")} will open for you here.`); }
    if (t.type === "islemouth") { const r = R(this, I), opts = r.bands.map((b) => ["isleband", b === 1 ? `Down the stair (${CM.isleBand(I, 1).name})` : `Down to ${CM.isleBand(I, b).name} (floor ${b})`, b]).concat([["isleback", "Not yet"]]);
      this.isleMenu = opts; this.emit("choice", { k: key(...fl.pos), title: I.deep, text: I.mouthWords || "The mouth of the dungeon. Where to?", options: opts.map((x) => x[1]) }); return true; }
    return false; };
  { const ch0 = P.choose; P.choose = function (k, i) { const fl = this.floor, t = fl && fl.things[k]; if (!t || t.type !== "islemouth" || !this.isleMenu) return ch0.call(this, k, i); const opt = this.isleMenu[i]; this.isleMenu = null; if (!opt || opt[0] === "isleback") return true;
      const I = CM.isleOf(fl.number).isle, b = opt[2]; this.logAct && this.logAct("choose", k, i); return this.isleGo(I.base - b, "isleup", b === 1 ? `Down the stair into ${I.deep}.` : `Down, by the way the stone showed you, to ${CM.isleBand(I, b).name.replace(/^The /, "the ")}.`); }; }
  { const u0 = P.use; P.use = function (...a) { const fl = this.floor; if (this.mode === "explore" && fl && CM.isleOf(fl.number) && !this.perch) { const [dx, dy] = CM.DIRS[fl.facing];
      for (const k of [key(...fl.pos), key(fl.pos[0] + dx, fl.pos[1] + dy)]) { const t = fl.things[k]; if (t && ["isledown", "isleup", "islestone", "islemouth"].includes(t.type)) return this.isleWay(t); } } return u0.apply(this, a); }; }
  { const l0 = P.look; P.look = function (...a) { const out = l0.apply(this, a), fl = this.floor; if (this.mode === "explore" && fl && CM.isleOf(fl.number)) { const t = fl.things[key(...fl.pos)];
      if (t) { const w = { isledown: "A stair going down into the dark. (Space)", isleup: "The stair back up. (Space)", islestone: "A standing stone, worn smooth by hands, cold as the sea. (Space: back to the open air)", islemouth: "The dungeon's mouth. (Space)" }[t.type]; if (w) this.say(w); } } return out; }; }
  // (v135.0) the kit each island is made with: a band's theme, a kind, a guardian (its strength by its level), its relic's power, its turn at half health
  CM.ISLE_KIT = {
    theme: (I, name, like, o) => Object.assign({}, CM.THEMES[like], { name, like, floors: [I.base - CM.ISLE_DEPTH, I.base - 1] }, o),
    kind: (isle, name, colour, body, head, eyes, extras, speed, o) => { const k = Object.assign({ name, colour, body, head, eyes, extras, speed, isle }, o); if (!CM.MONSTERS.some((m) => m.name === name)) CM.MONSTERS.push(k); return k; },
    guardian: (I, id, name, colour, body, level, k, depth, o) => { CM.GUARDIANS[id] = Object.assign({ floor: I.base - depth, name, colour, body, head: "round", eyes: "#FFF0A0", extras: [], speed: 10, size: 1.0, isle: I.id,
        hp: Math.round(44 * level * k), atk: Math.round(2.6 * level * Math.sqrt(k)), df: Math.round(1.1 * level), xp: Math.round(220 * level * k), gold: Math.round(110 * level * k), abilities: [],
        lair: { name: `${I.name}, floor ${depth}`, rows: ["#########", "#.......#", "#...B...#", "#.......#", "####D####"] } }, o);
      if (o.relic) CM.BASES[o.relic.name] = Object.assign({}, CM.BASES["Rat King's Crown"] || {}, { id: o.relic.name, kind: o.relic.kind, slot: o.relic.slot, tier: Math.min(9, Math.round(level / 2)), group: "relic" });
      if (o.power && o.relic) CM.RELIC_POWERS[o.relic.name] = o.power; if (o.phase && CM.BOSS_PHASES) CM.BOSS_PHASES[id] = o.phase; },
  };
  // the sea: an island's landing is where the Wren puts in, and where she waits
  CM.SEA_OPEN = CM.SEA_OPEN || [];
  { const sa0 = CM.seaArrive; CM.seaArrive = (g, id) => { const I = CM.ISLES[id]; if (!I) return sa0 ? sa0(g, id) : null; g.isleGo(I.base, I.jetty, I.arrive || `${CM.SHIP.name} ties up at ${I.name}.`); return { id }; }; }
}
