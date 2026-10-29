"use strict";
// The game's rules in Node, with no screen: 00-util, 10-data, 20-world, 25-saves and 60-64 loaded into a fresh
// context with a window and a localStorage of its own. The tests and the simulator drive CM.Game straight.
//
//   const { load } = require("./tools/headless");
//   const CM = load();                 // a fresh game world; CM.storage is its localStorage (a Map behind it)
//   const game = new CM.Game();
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const SRC = path.join(__dirname, "..", "src", "js");
const RULES = ["00-util.js", "10-data.js", "20-world.js", "25-saves.js", "60-game.js", "61-explore.js", "62-combat.js", "63-camp.js", "64-meta.js"];

// a localStorage: quota is how many characters it holds before it throws, the way a full browser does
function makeStorage(quota = Infinity) {
  const map = new Map();
  const size = () => { let n = 0; for (const [k, v] of map) n += k.length + v.length; return n; };
  return {
    map,
    getItem(k) { return map.has(k) ? map.get(k) : null; },
    setItem(k, v) {
      v = String(v);
      const was = map.has(k) ? map.get(k).length : 0;
      if (size() - was + k.length + v.length > quota) { const e = new Error("QuotaExceededError"); e.name = "QuotaExceededError"; throw e; }
      map.set(k, v);
    },
    removeItem(k) { map.delete(k); },
    key(i) { return [...map.keys()][i] === undefined ? null : [...map.keys()][i]; },
    get length() { return map.size; },
    clear() { map.clear(); },
  };
}

function load(opts = {}) {
  const storage = opts.storage || makeStorage(opts.quota);
  const ctx = { console, performance, localStorage: storage, btoa, atob, setTimeout, clearTimeout, Math, Date, JSON };
  ctx.window = ctx;
  vm.createContext(ctx);
  for (const f of RULES) vm.runInContext(fs.readFileSync(path.join(SRC, f), "utf8"), ctx, { filename: f });
  const CM = ctx.CM;
  CM.LOOKS = CM.LOOKS || { drawn: {} };                                 // (the themes live with the art, which isn't loaded here)
  CM.storage = storage;
  return CM;
}

// the classic four with the dice taken out of them: the same party every time, so two runs of a seed can be compared
function fixedParty(CM, seed = "party") {
  const rnd = new CM.Random(CM.hashSeed(seed));
  return CM.CLASSIC.map((cls) => ({ cls, name: CM.randomName(rnd), stats: CM.rollStats(cls, rnd), row: CM.CLASSES[cls].row }));
}

// a party that gets on with it: fights, heals under a third, casts at a crowd - the simulator's and the smoke test's hands
function autoplayFight(CM, game, limit = 400) {
  let guard = 0;
  while (game.mode === "combat" && game.combat && guard++ < limit) {
    const h = game.combat.waiting;
    if (!h) { game.advance(); continue; }
    const hurt = game.alive().filter((p) => p.hp < p.max / 3);
    const foes = game.living();
    const can = CM.abilitiesFor(h).filter((id) => CM.ABILITIES[id].mp <= h.mp && !(CM.ABILITIES[id].once && h.used && h.used[id]));
    let done = false;
    if (hurt.length && can.includes("heal")) done = game.act("cast", { id: "heal", target: game.party.indexOf(hurt[0]) });
    else if (hurt.length && can.includes("lay")) done = game.act("cast", { id: "lay", target: game.party.indexOf(hurt[0]) });
    else if (hurt.length && hurt.includes(h) && game.bag.some((i) => i.kind === "heal")) done = game.act("item", null);
    else if (foes.length >= 3 && can.includes("fireball")) done = game.act("cast", { id: "fireball" });
    else if (foes.length >= 2 && can.includes("thorns")) done = game.act("cast", { id: "thorns" });
    else if (can.includes("song") && !game.song) done = game.act("cast", { id: "song" });
    else if (can.includes("volley")) done = game.act("cast", { id: "volley" });
    if (!done) {
      const weakest = foes.reduce((a, b) => (a.hp <= b.hp ? a : b), foes[0]);
      done = game.act("fight", weakest);
    }
    if (!done) game.act("defend");
  }
}
module.exports = { load, makeStorage, autoplayFight, fixedParty, RULES };
